# Diagrams: Webhook delivery service (Stripe style)

> One-line answer: twelve views of one design. A capture path (outbox, CDC relay, Kafka `events`, fan-out in a Kafka transaction) turns a committed business write into one delivery per subscribed endpoint, keyed by `endpoint_id`. A delivery path (dispatchers that own partitions, with lanes, AIMD caps, breakers and fast and slow slot pools, a spill to the endpoint queue store, egress proxies on an isolated network) sends each attempt signed and isolated per endpoint. A control path (fault detector, reconciler, notifier, replay worker, attempt log) decides whose fault a failure is, proves nothing was dropped, and lets merchants see and replay. The dispatcher's in-flight connection slots are the one red box.

The D1 to D12 set from `hld/CLAUDE.md` §4, each with a one-line caption. A diagram already in [`solution.md`](solution.md) gets a heading, a caption and a link, never a second copy. Acronyms: CDC (change data capture), WAL (write-ahead log), HMAC (hash-based message authentication code), SSRF (server-side request forgery), AIMD (additive increase, multiplicative decrease), DRR (deficit round robin), AZ (availability zone), ASN (autonomous system number), RF (replication factor), KMS (key management service), TTL (time to live), DNS (Domain Name System), TLS (Transport Layer Security).

| # | Diagram | Where it lives |
|---|---|---|
| D1 | Context | below |
| D2 | Data flow | below |
| D3 | Component architecture (final design) | [solution §6](solution.md#6-final-design-and-the-six-core-flows) |
| D4 | Happy path per FR | FR1 registration: [solution §4.1](solution.md#41-merchants-register-endpoints-and-choose-event-types). FR1 secret roll: below. FR2 deliver: [solution §4.2](solution.md#42-every-matching-event-is-delivered-to-every-subscribed-endpoint-at-least-once-signed). FR3 retry, breaker, drain: [solution §4.3](solution.md#43-failed-deliveries-are-retried-for-up-to-3-days-failing-endpoints-are-disabled-and-the-merchant-is-told). FR3 disable and notify: below. FR4 range replay: [solution §4.4](solution.md#44-merchants-see-delivery-attempts-and-replay-one-event-or-a-time-range). FR4 single resend: below |
| D5 | Failure paths | Hung top merchant, queue store down while spilling, duplicate after a relay restart: below. Dispatcher crash and platform fault: [solution §10.4](solution.md#104-failure-timeline). Lost 200 and receiver dedup: [solution §5.5](solution.md#55-receivers-see-duplicates-and-out-of-order-events-what-do-you-promise-and-what-do-you-tell-them-to-do) |
| D6 | Decision flow | Attempt outcome classifier: below. Platform fault detector: [solution §5.4](solution.md#54-after-a-2-hour-outage-on-our-side-50-m-deliveries-are-due-at-once-how-do-you-avoid-a-retry-storm-against-merchants-and-against-ourselves). Dispatcher gate: [solution §5.3](solution.md#53-one-merchants-endpoint-hangs-for-30-s-on-every-call-how-do-you-stop-it-from-eating-every-worker). SSRF check: [solution §5.6](solution.md#56-a-merchant-registers-http169254169254latestmeta-data-what-happens-and-how-does-a-receiver-know-a-request-is-really-from-us) |
| D7 | Entity relationship | [solution §3.3](solution.md#33-data-model) |
| D8 | State machines | Delivery, endpoint, breaker: below |
| D9 | Deployment / topology | below |
| D10 | Scaling / partitioning | below. Offset low-water mark: [solution §10.1](solution.md#101-internals-of-each-chosen-technology) |
| D11 | Failure mode map | below, two trees |
| D12 | Rollout / migration | below |

## D1. Context (zoom-out)

Our system as one box: product services commit events in, signed HTTPS POSTs go out to merchant endpoints, and merchants manage endpoints and read the log.

```mermaid
%% D1: the system as one box with every external actor. Merchant endpoints are outside our trust boundary and decide how long each connection is held.
flowchart LR
    PS[Product services<br/>payments, billing, Connect] -->|"business write + outbox row"| SYS[Webhook delivery platform<br/>capture, fan out, dispatch,<br/>retry, log, replay]
    MD[Merchant developers<br/>API, dashboard] -->|"register endpoints, roll secrets,<br/>resend, replay"| SYS
    SYS -->|"attempt log, failing emails"| MD
    SYS -->|"signed HTTPS POST,<br/>~500 M a day"| ME[Merchant endpoints<br/>~1 M URLs]
    ME -->|"2xx, 4xx, 5xx, timeout"| SYS
    SYS -.->|"wrap and unwrap data keys"| KMS[KMS]
    SYS -->|"CONNECT via public resolvers"| DNS[Public DNS]
    SYN[Synthetic receivers<br/>3 clouds] -->|"health and signature checks"| SYS
    SYS -->|"page"| OC[On-call]

    class PS,SYS service
    class MD client
    class ME,KMS,DNS,SYN,OC external

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

## D2. Data flow (DFD)

Inputs to outputs with format, size and rate. Averages from solution §2; peak is the first-of-month billing run.

```mermaid
%% D2: data flow. Stores are cylinders, processes are rounded. Rates are averages with the billing-run peak where it matters.
flowchart LR
    PDB[(Product DBs<br/>outbox rows)] -->|"WAL change, ~3 KB,<br/>2.9k/s avg, ~15k/s peak"| RL(CDC relay)
    RL -->|"event JSON ~3 KB,<br/>2.9k/s, 750 GB/day"| EV[[events topic<br/>7 days]]
    RL -->|"payload ~3 KB, 30 days,<br/>~25 TB with replicas"| EST[(Event store)]
    EDB[(Endpoint DB)] -->|"endpoint rows ~200 B,<br/>a few per s"| FO(Fan-out)
    EV -->|"event, 2.9k/s"| FO
    FO -->|"delivery + render ~3.3 KB,<br/>5.8k/s avg, 30k/s peak"| DL[[deliveries topic<br/>512 partitions, 3 days]]
    DL -->|"delivery, 59/s per partition at peak"| DS(Dispatchers)
    DS -->|"signed POST ~3.3 KB,<br/>6.1k/s, ~99 MB/s peak"| ME[Merchant endpoints]
    ME -->|"status + body, read 64 KB max"| DS
    DS -->|"queued row ~300 B, ~200/s,<br/>50k/s burst after an outage"| QS[(Endpoint queue store<br/>TTL 4 days)]
    DS -->|"attempt record ~500 B,<br/>6.1k/s, 265 GB/day"| AT[[attempts topic]]
    AT -->|"rows, 2 to 5 s lag"| AL[(Attempt log<br/>30 days, ~4 TB)]
    AT -->|"fanout ids + outcomes, hourly"| RC(Reconciler)

    class RL,FO,DS,RC service
    class PDB,EST,EDB,QS,AL store
    class EV,DL,AT queue
    class ME external

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

## D3. Component architecture

The final design, 15 nodes, dispatcher fleet in red: [solution §6](solution.md#6-final-design-and-the-six-core-flows).

## D4. Happy paths, one per FR

**FR1, register an endpoint:** [solution §4.1](solution.md#41-merchants-register-endpoints-and-choose-event-types).

**FR1, roll a signing secret with a 24 h overlap (Flow 4).** Both secrets sign every attempt until the old one expires.

```mermaid
%% D4 FR1 roll: the merchant rolls its secret, dispatchers send two v1 signatures for 24 h, then one.
sequenceDiagram
    autonumber
    participant M as Merchant
    participant ES as Endpoint service
    participant DB as Endpoint DB
    participant D as Dispatcher, owner of we_1
    participant S as we_1 receiver
    M->>ES: POST secret/roll, expire_old_after 24h
    ES->>DB: insert s2, set s1.expires_at = now + 24 h
    ES-->>M: 200, s2 shown once
    DB->>D: config CDC, both secrets within ~5 s
    D->>S: POST, header t=..., v1=sig s2, v1=sig s1
    S->>S: still on s1, the s1 signature matches, accept
    M->>S: deploy s2
    D->>S: POST, two v1 values
    S->>S: s2 signature matches, accept
    Note over D,S: 24 h later s1 expires
    D->>S: POST, header t=..., v1=sig s2 only
    S-->>D: 200
```

**FR2, deliver one event:** [solution §4.2](solution.md#42-every-matching-event-is-delivered-to-every-subscribed-endpoint-at-least-once-signed).

**FR3, retry, breaker and drain:** [solution §4.3](solution.md#43-failed-deliveries-are-retried-for-up-to-3-days-failing-endpoints-are-disabled-and-the-merchant-is-told).

**FR3, an endpoint dead for good is disabled and the merchant is told (Flow 5, days 0 to 3).**

```mermaid
%% D4 FR3 disable: no 2xx for 72 h disables the endpoint. Waiting deliveries end FAILED, new ones SKIPPED, the merchant is emailed at each step.
sequenceDiagram
    autonumber
    participant D as Dispatcher, owner of we_9
    participant Q as Endpoint queue store
    participant S as we_9, server deleted
    participant N as Notifier
    participant M as Merchant developers
    D->>S: day 0, deliveries time out
    D->>D: breaker OPEN, spill everything, 1 probe at a time
    D->>Q: queued rows, deadline created + 72 h
    D->>N: open 1 h
    N->>M: email, we_9 failing
    N->>M: reminders at 24 h and 48 h
    D->>S: probes every 30 min, all fail
    Note over D: day 3, no 2xx for 72 h
    D->>D: we_9 DISABLED_FAILING
    D->>Q: rows past deadline become FAILED
    D->>D: new events for we_9 recorded SKIPPED
    D->>N: disabled
    N->>M: email, we_9 disabled, re-enable and replay
```

**FR4, replay a time range:** [solution §4.4](solution.md#44-merchants-see-delivery-attempts-and-replay-one-event-or-a-time-range).

**FR4, resend one event.** Goes to the front of the endpoint's replay lane; the original delivery keeps its own retries.

```mermaid
%% D4 FR4 resend: one event to one endpoint, same event id, fresh signature, logged like any attempt.
sequenceDiagram
    autonumber
    participant M as Merchant
    participant API as Delivery log API
    participant E as Event store
    participant R as replays topic
    participant D as Dispatcher, owner of we_1
    participant S as we_1
    participant L as Attempt log
    M->>API: POST /v1/events/evt_1/resend, endpoint we_1
    API->>E: read render evt_1 for we_1 api_version
    E-->>API: exact bytes, created within 30 days
    API->>R: delivery keyed we_1, replay flag
    API-->>M: 202 dlv_r
    D->>D: lane we_1, replay at most 25% of cap under load
    D->>S: POST evt_1, new t, new v1
    S-->>D: 200
    D->>L: attempt SUCCEEDED via attempts topic
    L-->>M: visible in the dashboard in 2 to 5 s
```

## D5. Failure paths

**The top merchant's endpoint hangs (Flow 2).** It costs its own cap for one timeout, then one probe.

```mermaid
%% D5 hung endpoint: we_big at 900 per s stops answering. In-flight hits the cap, the lane spills at 1,000, the breaker opens at the 30 s timeout. Nobody else's p99 moves.
sequenceDiagram
    autonumber
    participant K as deliveries partition
    participant D as Dispatcher, owner of we_big
    participant Q as Endpoint queue store
    participant S as we_big, hung
    participant O as Other endpoints on the partition
    Note over S: t=0, stops answering, cap about 720
    D->>S: up to 720 in flight by t=0.8 s
    K->>D: 900 per s keep arriving into the lane
    Note over D: t=2 s, lane holds 1,000
    D->>Q: spill new we_big deliveries, quorum write
    D->>K: offset mark passes spilled records
    K->>D: records for other endpoints
    D->>O: sent at normal latency, own lanes
    Note over D,S: t=30 s, 720 time out
    D->>D: over 80% of at least 5 failed, breaker OPEN
    D->>Q: spill the 720 with next retry times
    D->>S: t=90 s, 1 probe, oldest due delivery
    S--xD: timeout at 30 s
    Note over D: cost, 720 slots for 30 s then 1, page none, email at 1 h
```

**The endpoint queue store is unavailable while endpoints need to spill.** Work stays in Kafka; only spilling endpoints slow down.

```mermaid
%% D5 queue store down: a spill cannot be acknowledged, so the record stays unresolved and the offset mark stops at it. Kafka keeps the data for 3 days. Healthy endpoints keep flowing.
sequenceDiagram
    autonumber
    participant K as deliveries partition 17
    participant D as Dispatcher
    participant Q as Endpoint queue store
    participant SL as Slow endpoint we_7
    participant H as Healthy endpoints
    Note over Q: t=0, quorum writes fail
    K->>D: offsets 500 to 900
    D->>Q: spill we_7 offset 512
    Q--xD: write timeout
    D->>D: 512 stays unresolved, kept in the lane, retry spill every 1 s
    D->>H: 513 to 900 for healthy endpoints, 2xx
    D->>K: commit offset 512, not 901
    D->>D: lane we_7 full at 1,000, pause reading new we_7 records into memory
    Note over D: alert, queue store write errors and offset mark age
    Note over Q: t=4 min, store back
    D->>Q: spill succeeds
    D->>K: commit jumps to the next unresolved offset
    Note over K,D: a crash in the 4 min re-reads from 512, duplicates only
```

**A duplicate enters after a CDC relay restart.** Removed by the recent-success set when it can be; otherwise by the receiver.

```mermaid
%% D5 duplicate: the relay crashed after Kafka acked but before confirming the WAL position, so evt_1 is published twice. Same delivery id, so the owner drops it if it remembers. If not, the receiver dedups on event id.
sequenceDiagram
    autonumber
    participant R as CDC relay
    participant K as Kafka
    participant F as Fan-out
    participant D as Dispatcher, owner of we_1
    participant S as we_1 receiver
    R->>K: publish evt_1, acked
    R--xR: crash before confirmed_flush_lsn moves
    R->>K: restart, re-read WAL, publish evt_1 again
    F->>K: two deliveries, both dlv_a = hash evt_1, we_1
    D->>S: first dlv_a, 200
    D->>D: add dlv_a to recent-success set, 1 h
    D->>D: second dlv_a, found in set, drop, log duplicate_dropped
    Note over D,S: if the owner changed in between, the set is gone
    D->>S: second dlv_a sent
    S->>S: INSERT processed evt_1 conflicts, no side effect
    S-->>D: 200
```

**A dispatcher crashes at peak** and **egress breaks for the region:** [solution §10.4](solution.md#104-failure-timeline). **A lost 200 and receiver dedup:** [solution §5.5](solution.md#55-receivers-see-duplicates-and-out-of-order-events-what-do-you-promise-and-what-do-you-tell-them-to-do).

## D6. Activity / decision flow

The attempt outcome classifier inside the dispatcher. Platform faults are checked first, so our outage never counts against a merchant. Only timeouts, connect, TLS, DNS errors and 5xx count toward the breaker.

```mermaid
%% D6: what one attempt outcome does to the delivery, the endpoint's cap, its breaker and its disable clock.
flowchart TD
    OUT[Attempt outcome] --> PF{PLATFORM_FAULT<br/>for this scope?}
    PF -->|"yes"| TAGP[fault=platform<br/>no count, clocks frozen,<br/>deadline extended]
    PF -->|"no"| OK{2xx?}
    OK -->|"yes"| SUC[SUCCEEDED<br/>clean window may raise cap]
    OK -->|"no"| RA{429 or 503<br/>with Retry-After?}
    RA -->|"yes"| DLY[Retry at min Retry-After, 1 h<br/>halve cap]
    RA -->|"no"| G{410 Gone?}
    G -->|"10 in a row"| DIS[Endpoint DISABLED_FAILING<br/>email merchant]
    G -->|"no"| CL{Timeout, connect, TLS,<br/>DNS error or 5xx?}
    CL -->|"yes, counts toward breaker,<br/>halve cap if over 10% in 1 s"| BO{5 in a row, or over 80%<br/>of at least 5 in 30 s?}
    CL -->|"no: 3xx, other 4xx, ssrf_blocked"| SCH[Next attempt from schedule<br/>1 m, 5 m, 30 m ... jitter 20%,<br/>spill to queue store]
    BO -->|"yes"| OPEN[Breaker OPEN<br/>spill all, 1 probe on<br/>1, 2, 5, 10, 20, 30 min]
    BO -->|"no"| SCH
    SCH --> DL{Past 72 h deadline,<br/>or no 2xx on endpoint for 72 h?}
    OPEN -->|"probes keep failing"| DL
    DLY --> DL
    DL -->|"yes"| FAIL[Delivery FAILED,<br/>endpoint DISABLED_FAILING]
    DL -->|"no, wait for due time"| OUT

    class OUT,TAGP,SUC,DLY,SCH,OPEN service
    class PF,OK,RA,G,CL,BO,DL decision
    class DIS,FAIL store

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

The 410 rung and the final fail node both write `DISABLED_FAILING`; it is shown twice only to keep the tree readable.

## D7. Entity relationship

Endpoint DB, event store, endpoint queue store and attempt log entities with keys and TTLs: [solution §3.3](solution.md#33-data-model).

## D8. State machines

**Delivery.** Exists as a Kafka record on the hot path; gets a queue row only in `QUEUED`.

```mermaid
%% D8 delivery lifecycle: one per event and endpoint. QUEUED means a row in the endpoint queue store.
stateDiagram-v2
    [*] --> PENDING : fan-out commits to deliveries
    PENDING --> IN_FLIGHT : lane has a slot under cap
    PENDING --> QUEUED : breaker open, lane over 1,000 or 10 s wait
    PENDING --> SKIPPED : endpoint disabled or deleted
    IN_FLIGHT --> SUCCEEDED : 2xx
    IN_FLIGHT --> QUEUED : failure, next attempt from schedule
    QUEUED --> IN_FLIGHT : due time or probe
    QUEUED --> FAILED : 72 h deadline passed
    QUEUED --> SKIPPED : endpoint deleted
    SUCCEEDED --> [*]
    FAILED --> [*]
    SKIPPED --> [*]

    classDef service fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store   fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    class PENDING,IN_FLIGHT service
    class QUEUED,SUCCEEDED,FAILED,SKIPPED store
```

**Endpoint.**

```mermaid
%% D8 endpoint lifecycle: who can disable it, and how it comes back.
stateDiagram-v2
    [*] --> ENABLED : POST webhook_endpoints
    ENABLED --> DISABLED_BY_MERCHANT : merchant disables
    DISABLED_BY_MERCHANT --> ENABLED : merchant enables
    ENABLED --> DISABLED_FAILING : no 2xx for 72 h, or 10 consecutive 410
    DISABLED_FAILING --> ENABLED : merchant re-enables, breaker reset, replay offered
    ENABLED --> DELETED : DELETE
    DISABLED_BY_MERCHANT --> DELETED : DELETE
    DISABLED_FAILING --> DELETED : DELETE
    DELETED --> [*]

    classDef service fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store   fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    class ENABLED service
    class DISABLED_BY_MERCHANT,DISABLED_FAILING,DELETED store
```

**Breaker (per endpoint, in the owning dispatcher's memory, snapshotted every 10 s).** Frozen while `PLATFORM_FAULT` is declared.

```mermaid
%% D8 breaker: one probe at a time while open, a ramped cap while half-open.
stateDiagram-v2
    [*] --> CLOSED
    CLOSED --> OPEN : 5 consecutive endpoint faults, or over 80% of at least 5 in 30 s
    OPEN --> OPEN : probe fails, next probe on 1, 2, 5, 10, 20, 30 min then every 30 min
    OPEN --> HALF_OPEN : probe gets 2xx
    HALF_OPEN --> OPEN : failure during ramp
    HALF_OPEN --> CLOSED : queue drained, cap back to normal
    note right of HALF_OPEN
        cap starts at 2, doubles each clean second
        backlog drains at up to 3x normal rate, live first
    end note

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
    class CLOSED service
    class OPEN,HALF_OPEN decision
```

## D9. Deployment / topology

Three AZs in one region. Every tier is N+1 per AZ, so one AZ can be lost. Proxies sit in a separate egress network in each AZ, with no peering to internal networks.

```mermaid
%% D9: one region, 3 AZs. Kafka RF 3 with one replica per AZ, queue store quorum across AZs, dispatchers reach the internet only through their AZ's proxies.
flowchart LR
    subgraph AZA[AZ a]
        KA[[Kafka, 4 brokers<br/>1 replica of each partition]]
        DA[8 dispatchers<br/>~21 partitions each]
        QA[(Queue store, 2 nodes)]
        subgraph EGA[Egress network a]
            PA[4 proxies<br/>fixed public IPs]
        end
    end
    subgraph AZB[AZ b]
        KB[[Kafka, 4 brokers]]
        DB[8 dispatchers]
        QB[(Queue store, 2 nodes)]
        subgraph EGB[Egress network b]
            PB[4 proxies]
        end
    end
    subgraph AZC[AZ c]
        KC[[Kafka, 4 brokers]]
        DC[8 dispatchers]
        QC[(Queue store, 2 nodes)]
        subgraph EGC[Egress network c]
            PC[4 proxies]
        end
    end
    KA <-->|"replication, acks=all, min ISR 2"| KB
    KB <-->|"replication"| KC
    QA <-->|"quorum writes"| QB
    QB <-->|"quorum writes"| QC
    DA -->|"CONNECT, same AZ"| PA
    DB -->|"CONNECT"| PB
    DC -->|"CONNECT"| PC
    DA -->|"failover if AZ a egress faults"| PB
    PA -->|"HTTPS"| NET[Internet<br/>merchant endpoints]
    PB -->|"HTTPS"| NET
    PC -->|"HTTPS"| NET

    class DA,DB,DC critical
    class PA,PB,PC service
    class KA,KB,KC queue
    class QA,QB,QC store
    class NET external

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

What crosses an AZ boundary: Kafka replication, queue store quorum writes, consumer reads from a partition leader in another AZ, and egress failover when one AZ's proxies are in fault. Fan-out, the CDC relays, the event store and the control plane are spread the same way and left out to stay under 15 nodes. Losing one AZ leaves 16 dispatchers at ~1,500 in flight each at design capacity, under the ~4,000 per node (solution §10.3).

## D10. Scaling / partitioning

`deliveries` has 512 partitions keyed by `endpoint_id`, ~2,000 endpoints each, one owner dispatcher per partition. Average load is ~59 deliveries/s per partition at peak. The problem is one endpoint, not one partition.

```mermaid
%% D10: endpoint_id hashes to one of 512 partitions. A Connect platform endpoint at 2% of traffic makes its partition hot. Past ~2,000 per s an endpoint is salted into k sub-keys with the cap split k ways.
flowchart LR
    EP[Delivery for endpoint_id] -->|"hash endpoint_id mod 512"| H{Salted endpoint?}
    H -->|"no, all but a handful"| P0[Partition 0<br/>~2k endpoints, ~59 per s]
    H -->|"no"| P511[Partition 511<br/>~2k endpoints, ~59 per s]
    H -->|"no, before salting"| P17[Partition 17<br/>we_connect at 600 per s,<br/>2,000 per s on a billing run]
    P17 -->|"one owner"| D17[Dispatcher d4<br/>owns 17, cap up to 1,000]
    H -->|"yes, k = 4, key endpoint_id + n"| S1[Partitions 17, 203,<br/>388, 450<br/>~500 per s each]
    S1 -->|"4 owners, cap split 4 ways"| D4X[4 dispatchers<br/>~250 slots each]
    P0 -->|"owner"| DX[Dispatchers]
    P511 -->|"owner"| DX

    class EP service
    class H decision
    class P0,P511,S1 queue
    class P17 critical
    class D17,D4X,DX service

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

- Without salting, partition 17 carries 2,000/s × 3.3 KB = 6.6 MB/s and one dispatcher holds `2,000 × 0.4 s = 800` slots for one endpoint. That is the 2,000/s salting line in solution §5.3 and §10.3.
- Salting gives up per-endpoint state in one process: four owners each run a quarter of the cap and their own breaker. A dead salted endpoint costs four breakers' worth of timeouts, not one.
- The offset low-water mark per partition: [solution §10.1](solution.md#101-internals-of-each-chosen-technology).

## D11. Failure mode map

Component, what fails, blast radius, mitigation. Two trees to stay under 15 nodes. Matches solution §8.

```mermaid
%% D11 tree 1: the data path. The dispatcher fleet is red: its slots are what a failure or a slow merchant eats first.
flowchart TD
    ROOT[Data path] --> DSP[Dispatcher node]
    ROOT --> KFK[Kafka broker or AZ]
    ROOT --> QST[Endpoint queue store]
    ROOT --> CDC[CDC relay for one product DB]
    DSP -->|"crash"| DSPB[~21 partitions pause 15 s<br/>caps lost, seconds of duplicates]
    DSPB -->|"mitigate"| DSPM[Cooperative rebalance,<br/>state snapshot every 10 s,<br/>low-water-mark replay]
    KFK -->|"broker or AZ lost"| KFKB[Leaders move in seconds,<br/>1/3 of capacity gone]
    KFKB -->|"mitigate"| KFKM[RF 3, min ISR 2, acks all,<br/>N+1 per AZ]
    QST -->|"unavailable"| QSTB[No spills, only spilling<br/>endpoints slow, offsets stop]
    QSTB -->|"mitigate"| QSTM[Work stays in Kafka 3 days,<br/>healthy endpoints flow]
    CDC -->|"stalls"| CDCB[That product's events wait,<br/>WAL grows on its primary]
    CDCB -->|"mitigate"| CDCM[Slot lag alarm 10 GB,<br/>page 50 GB, snapshot restart]

    class ROOT,KFK,QST,CDC service
    class DSP critical
    class DSPB,KFKB,QSTB,CDCB decision
    class DSPM,KFKM,QSTM,CDCM store

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

```mermaid
%% D11 tree 2: egress, config, observability and our own deploys. The bad deploy has the biggest blast radius: every merchant sees it as their own bug.
flowchart TD
    ROOT[Edges and control] --> PRX[Egress proxies]
    ROOT --> EDB[Endpoint DB]
    ROOT --> ALG[Attempt log]
    ROOT --> DEP[Bad dispatcher deploy]
    PRX -->|"down in an AZ or region"| PRXB[Nothing leaves that scope,<br/>fail closed]
    PRXB -->|"mitigate"| PRXM[N per AZ, AZ failover,<br/>PLATFORM_FAULT freezes clocks]
    EDB -->|"down"| EDBB[No endpoint changes,<br/>delivery continues]
    EDBB -->|"mitigate"| EDBM[In-memory subscription copy<br/>on every node, CDC catch-up]
    ALG -->|"down or lagging"| ALGB[Dashboard stale,<br/>delivery unaffected]
    ALGB -->|"mitigate"| ALGM[Fed from Kafka,<br/>catches up, dedup on attempt key]
    DEP -->|"mis-signs every request"| DEPB[Every merchant rejects us<br/>and blames itself]
    DEPB -->|"mitigate"| DEPM[1 node, 1 AZ, all,<br/>gated on synthetic receivers<br/>verifying signatures]

    class ROOT,PRX,EDB,ALG,DEP service
    class PRXB,EDBB,ALGB,DEPB decision
    class PRXM,EDBM,ALGM,DEPM store

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

## D12. Rollout / migration

From a legacy path (the payments service enqueues webhook jobs, workers POST them) to this design. Each endpoint has an `owner` flag with an `effective_from` a minute ahead; both paths compare `event.created` to it, so every event has exactly one sender. Rollback at any phase is a new `effective_from` back to legacy; deliveries already queued in the new path finish there.

```mermaid
%% D12: migration phases with a rollback point at the end of each. Legacy keeps running until every endpoint has been on the new path for 3 days.
gantt
    title Legacy job queue to outbox, fan-out and dispatchers
    dateFormat YYYY-MM-DD
    axisFormat %b %d
    section Capture
    Outbox and CDC in shadow, compare counts per minute :a1, 2026-11-02, 14d
    Rollback point, drop the relay, no sends affected     :milestone, m1, after a1, 0d
    section Sandbox
    New dispatcher for internal and sandbox endpoints    :a2, after a1, 7d
    Rollback point, flag sandbox back to legacy          :milestone, m2, after a2, 0d
    section Live by endpoint hash
    1 percent, effective_from now plus 1 min             :a3, after a2, 3d
    10 percent                                           :a4, after a3, 3d
    50 percent                                           :a5, after a4, 4d
    100 percent                                          :a6, after a5, 4d
    Rollback point per step, new effective_from          :milestone, m3, after a6, 0d
    section Legacy
    Legacy drains its in-flight retries, up to 3 days    :a7, after a6, 3d
    Remove legacy enqueue and workers                    :a8, after a7, 5d
```

Gates between live steps: synthetic receivers verify 100% of signatures, the commit-to-first-attempt p99 stays under 5 s, the reconciler reports zero gaps, and per-endpoint success rates on the new path match legacy's within 0.5 points.
