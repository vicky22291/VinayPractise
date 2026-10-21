# Diagrams: Hotel booking (search, reserve, partner ARI, last room)

The D1 to D12 set for [`solution.md`](solution.md). Each diagram appears once in the repo: the ones embedded in `solution.md` are linked from here, not repeated. Deep-dive diagrams live in [`deep-dives/`](deep-dives/) and are linked where relevant. Colors per root `CLAUDE.md` §3. Red is used only for the Postgres primary under ARI write load, the partner CRS on the booking path, and the residual oversell gap.

Legend reminder: 🔵 client / edge, 🟢 stateless compute, 🟣 durable storage, 🟡 cache or losable, 🔷 queue, 🔴 bottleneck or SPOF, ⚪ external, 🩷 decision.

---

## D1. Context (zoom-out)

Our system is one box. Guests, hotels, card networks, and other sales channels sit around it, and the other channels are why the last room is contested.

```mermaid
%% D1: context. Our platform as one box, every outside actor and what flows on each edge.
flowchart LR
    G["Guests<br/>web, app"]
    MS["Metasearch<br/>Google Hotels, Trivago"]
    OTA["Our hotel booking platform"]
    CH["Chains<br/>CRS"]
    CM["Small hotels<br/>channel managers, extranet"]
    PSP["PSP<br/>card networks"]
    OC["Other OTAs and<br/>hotel direct sites"]

    G -->|"search, hold, pay"| OTA
    MS -->|"price queries, clicks"| OTA
    CH -->|"ARI push, live check replies"| OTA
    OTA -->|"reservations, cancels"| CH
    CM -->|"ARI push or pull"| OTA
    OTA -->|"reservations"| CM
    OTA -->|"authorize, capture, void"| PSP
    OC -->|"sell the same rooms"| CM
    OC -->|"sell the same rooms"| CH

    class G client
    class OTA service
    class MS,CH,CM,PSP,OC external
    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

## D2. Data flow (DFD)

Inputs to outputs with format, size, and peak rate from [`solution.md` §2](solution.md#2-back-of-envelope). ARI is the biggest write flow by far.

```mermaid
%% D2: data flow. Edges carry data name, format, size, peak rate.
flowchart LR
    P["Partners"]
    U["Guests"]
    IN("Ingest<br/>adapters")
    AP("ARI applier")
    RS("Reservation")
    CDC("CDC<br/>Debezium")
    S3[("Raw archive S3")]
    DB[("Inventory + bookings<br/>Postgres")]
    AC[/"Availability cache"/]
    ES[("Search index")]
    SR("Search")

    P -->|"ARI, XML/JSON ~2 KB, 1.2k msg/s"| IN
    IN -->|"raw bytes, 20 GB/day"| S3
    IN -->|"canonical ARI, JSON ~300 B, 1.2k/s"| AP
    AP -->|"night upserts, 35k rows/s"| DB
    U -->|"hold, JSON ~1 KB, 100/s"| RS
    RS -->|"booking + 3 night rows, 150 rows/s"| DB
    DB -->|"row changes, WAL"| CDC
    CDC -->|"night value ~120 B, < 5 s"| AC
    CDC -->|"hotel doc ~5 KB, ~300/s debounced"| ES
    U -->|"search, 6k QPS"| SR
    SR -->|"top 50 ids"| ES
    SR -->|"HMGET, 300k/s"| AC
    SR -->|"results ~30 KB, 180 MB/s"| U

    class P external
    class U client
    class IN,AP,RS,CDC,SR service
    class S3,DB,ES store
    class AC cache
    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef cache    fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

## D3. Component architecture

Embedded in [`solution.md` §6](solution.md#6-final-design). Not repeated here.

## D4. Sequence, happy path, one per FR

All five are embedded in `solution.md`, one at the end of each FR section:
- D4a search: [§4.1](solution.md#41-search-hotels-near-a-place-for-given-dates)
- D4b hotel page: [§4.2](solution.md#42-show-room-types-and-exact-prices-for-the-stay)
- D4c hold: [§4.3](solution.md#43-hold-a-room-type-for-every-night-without-overselling)
- D4d pay and confirm: [§4.4](solution.md#44-pay-confirm-with-the-hotel-and-cancel)
- D4e ARI push: [§4.5](solution.md#45-ingest-partner-ari-and-deliver-bookings-back)

## D5. Sequence, failure path

Two timelines are in [`solution.md` §10.4](solution.md#104-failure-timeline): a shard primary dies mid-hold, and a chain CRS goes down on New Year's Eve. Three more below.

**D5a. The hold-expiry sweeper races a late card authorization.** Conditional status updates decide the winner. Neither path can double-count inventory.

```mermaid
%% D5a: sweeper and late auth race on one booking. The status guard serializes them.
sequenceDiagram
    autonumber
    participant SW as Expiry sweeper
    participant R as Reservation Svc
    participant D as Hotel shard
    participant Y as Payment Svc
    Note over D: t=12:00 hold_expires_at passes, status RESERVED
    SW->>D: UPDATE booking SET EXPIRED WHERE status = RESERVED (SKIP LOCKED)
    D-->>SW: 1 row, release 3 night rows (reserved - 1)
    Y-->>R: t=12:04 auth success for this booking
    R->>D: UPDATE booking SET PENDING WHERE status = RESERVED
    D-->>R: 0 rows (already EXPIRED)
    R->>D: re-claim: conditional UPDATE inventory, same 3 nights
    alt rows = 3 and quote still valid
        R->>D: EXPIRED -> PENDING, commit
        R-->>Y: keep auth, continue saga
    else sold out or quote expired
        R->>Y: void auth (free, instant)
        R-->>R: booking stays EXPIRED, notify user
    end
```

**D5b. A partner's ARI arrives out of order, then a duplicate is redelivered.** The per-night `ari_seq` guard skips older and repeated writes night by night.

```mermaid
%% D5b: overlapping ranges arrive out of order, then Kafka redelivers. Per-night guard keeps the newest.
sequenceDiagram
    autonumber
    participant P as Channel manager
    participant K as Kafka (key hotel_id)
    participant A as ARI applier
    participant D as Inventory rows (Dec)
    P->>K: seq 11: Dec 15 avail 0 (sent second, arrives first)
    K->>A: seq 11
    A->>D: upsert Dec 15 WHERE ari_seq < 11
    D-->>A: 1 row (Dec 15 = 0, ari_seq 11)
    P->>K: seq 10: Dec 1-31 avail 4 (sent first, delayed)
    K->>A: seq 10
    A->>D: upsert Dec 1-31 WHERE ari_seq < 10
    D-->>A: 30 rows. Dec 15 skipped, still 0
    Note over K,A: consumer rebalance, offset not yet committed
    K->>A: seq 10 again (redelivery)
    A->>D: same upsert
    D-->>A: 0 rows (ari_seq = 10 everywhere, or 11 on Dec 15)
    A->>K: commit offset
```

**D5c. The client retries `POST /bookings` after a timeout.** The unique idempotency key on the booking row turns the retry into a read.

```mermaid
%% D5c: first attempt commits but the response is lost. The retry returns the same hold.
sequenceDiagram
    autonumber
    participant C as Client
    participant G as Gateway
    participant R as Reservation Svc
    participant D as Hotel shard
    C->>G: POST /bookings, Idempotency-Key k
    G->>R: forward
    R->>D: INSERT booking (user, k) + claim 3 nights + outbox, COMMIT
    D-->>R: committed
    R--xG: pod dies before responding
    G-->>C: 502 after 5 s
    C->>G: retry, same key k
    G->>R: forward (other pod)
    R->>D: INSERT booking (user, k) ON CONFLICT DO NOTHING
    D-->>R: 0 rows inserted
    R->>D: SELECT booking WHERE user, k
    D-->>R: RESERVED, hold_expires_at
    R-->>C: 201, same booking_id, no second claim
```

## D6. Activity / decision flow

Two are embedded in `solution.md`: the claim decision D6a in [§4.3](solution.md#43-hold-a-room-type-for-every-night-without-overselling) and the late-auth decision in [§5.5](solution.md#55-the-card-is-authorized-but-the-hold-expired-or-the-request-is-retried-what-happens). The partner-type strategy flow is in the [last room deep dive §5](deep-dives/last-room-and-inventory-locking.md#5-the-last-room-across-platforms).

**D6b. ARI apply for a POOL hotel.** The partner's count already includes some of our bookings and not others. The applier recomputes `reserved` from the in-flight overlay so a stale count cannot re-open a room we sold. Background: [last room §5.2](deep-dives/last-room-and-inventory-locking.md#52-pool-small-hotels-on-a-channel-manager), [ingestion §4](deep-dives/partner-ingestion-push-vs-pull.md#4-ordering-and-duplicates).

```mermaid
%% D6b: applying one partner update (count A, partner time T) to one night of a POOL hotel
flowchart TD
    E["ARI event<br/>night, count A, seq, time T"]
    S{"ari_seq for this night<br/>older than seq?"}
    K["Skip night<br/>stale or duplicate"]
    G{"Sanity guards pass?"}
    Q["Quarantine"]
    T["total = A"]
    O{"For each in-flight booking:<br/>acked_at null or after T?"}
    IN["Still counted in reserved<br/>partner has not seen it"]
    OUT["Drop from reserved<br/>delete overlay row"]
    R["reserved = live holds +<br/>remaining in-flight"]
    C{"reserved > total - buffer?"}
    W["Oversold: alert, start walk check"]
    OK["Commit, CDC to cache"]

    E --> S
    S -->|"no"| K
    S -->|"yes"| G
    G -->|"no"| Q
    G -->|"yes"| T
    T -->|"then"| O
    O -->|"yes"| IN
    O -->|"no, A includes it"| OUT
    IN -->|"sum"| R
    OUT -->|"sum"| R
    R --> C
    C -->|"yes"| W
    C -->|"no"| OK

    class E,T,IN,OUT,R,OK service
    class S,G,O,C decision
    class K,Q external
    class W critical
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

## D7. Entity relationship

Embedded in [`solution.md` §3.3](solution.md#33-data-model).

## D8. State machine

Booking lifecycle (RESERVED, PENDING, CONFIRMED and exits) embedded in [`solution.md` §4.4](solution.md#44-pay-confirm-with-the-hotel-and-cancel).

## D9. Deployment / topology

One home region, three AZs. Synchronous replication stays inside the region. Only async replicas and search copies cross regions.

```mermaid
%% D9: home region with 3 AZs. Sync standby gives RPO 0. Remote regions only read.
flowchart LR
    subgraph AZ1["AZ 1"]
        A1["App pods<br/>Search, Reservation, Gateway"]
        PGP[("Postgres primaries<br/>8 shards")]
        K1[["Kafka broker"]]
        R1[/"Redis primaries 1-2"/]
    end
    subgraph AZ2["AZ 2"]
        A2["App pods"]
        PGS[("Sync standbys<br/>8 shards")]
        K2[["Kafka broker"]]
        R2[/"Redis primaries 3-4"/]
    end
    subgraph AZ3["AZ 3"]
        A3["App pods"]
        PGA[("Async replicas<br/>read path")]
        K3[["Kafka broker"]]
        ES[("ES data nodes<br/>spread 2 per AZ")]
    end
    RR["Remote regions<br/>ES + Redis read copies"]

    A1 -->|"writes"| PGP
    PGP -->|"sync WAL, RPO 0"| PGS
    PGP -->|"async WAL"| PGA
    K1 -->|"RF 3, min ISR 2"| K2
    K2 -->|"RF 3"| K3
    R1 -->|"replica"| R2
    A3 -->|"replica reads"| PGA
    ES -->|"cross-region copy, minutes"| RR

    class A1,A2,A3 service
    class PGP critical
    class PGS,PGA,ES store
    class K1,K2,K3 queue
    class R1,R2 cache
    class RR external
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef cache    fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

- Remote regions serve search locally and forward holds to the home region (~100 ms extra on booking only). See [`solution.md` §10.11](solution.md#1011-evolution).

## D10. Scaling / partitioning

`hash(hotel_id)` picks one of 256 fixed logical shards. Logical shards map to 8 physical primaries. The hot spot is a physical primary during the morning ARI burst, not a hot hotel-night.

```mermaid
%% D10: hotel_id -> logical shard -> physical node. Red = the primary that takes a big chain's morning rate push.
flowchart LR
    H["hotel_id"]
    F{"hash mod 256"}
    L1["Logical 0-31"]
    L2["Logical 32-63"]
    LN["Logical 224-255"]
    P1[("Primary 1<br/>~4.4k rows/s")]
    P2[("Primary 2<br/>burst 12k rows/s")]
    P8[("Primary 8")]
    FX["Fix: move logical shards<br/>32-47 to new Primary 9"]

    H -->|"key"| F
    F -->|"logical id"| L1
    F -->|"logical id"| L2
    F -->|"logical id"| LN
    L1 -->|"map v12"| P1
    L2 -->|"map v12"| P2
    LN -->|"map v12"| P8
    P2 -->|"over budget"| FX

    class H client
    class F decision
    class L1,L2,LN service
    class P1,P8 store
    class P2 critical
    class FX service
    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

- A hot hotel-night (New Year's Eve) is one row with ~5 ms locks, so ~200 claims/s. Global peak is 60/s. Not the bottleneck.
- Before moving shards, cheaper fixes: drop no-op ARI writes, batch per hotel, rate-limit one partner's burst at the receiver. See [sharding](../../concepts/sharding.md).

## D11. Failure mode map

Component, what fails, blast radius, mitigation. Red marks the two failures that can create an oversell or lose a booking.

```mermaid
%% D11: one tree. Component -> failure -> blast radius -> mitigation.
flowchart TD
    ROOT["Hotel booking platform"]
    DBF["Shard primary dies<br/>1/8 hotels, ~20 s of 503"]
    DBM["Sync standby promoted<br/>retries replay by key"]
    CRSF["Chain CRS down<br/>that chain unbookable"]
    CRSM["Breaker, stop-sell or allotment<br/>PENDING re-driven later"]
    ARIF["Partner sends stale or bad ARI<br/>oversell or false sold-out"]
    ARIM["ari_seq guard, sanity quarantine<br/>overlay, buffer, reconciliation"]
    KF["Kafka down<br/>search and ARI go stale"]
    KM["Outbox buffers in Postgres<br/>partners get 429 and retry"]
    RF["Redis down<br/>no exact prices in search"]
    RM["ES coarse only, prices from<br/>rebuild from replica ~10 min"]
    PF["PSP down<br/>no new payments"]
    PM["Second PSP<br/>extend holds 5 min"]

    ROOT -->|"storage"| DBF
    DBF -->|"mitigation"| DBM
    ROOT -->|"partner, booking path"| CRSF
    CRSF -->|"mitigation"| CRSM
    ROOT -->|"partner, ingest path"| ARIF
    ARIF -->|"mitigation"| ARIM
    ROOT -->|"pipeline"| KF
    KF -->|"mitigation"| KM
    ROOT -->|"cache"| RF
    RF -->|"mitigation"| RM
    ROOT -->|"payments"| PF
    PF -->|"mitigation"| PM

    class ROOT client
    class DBF,ARIF critical
    class CRSF,KF,RF,PF external
    class DBM,CRSM,ARIM,KM,RM,PM service
    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

## D12. Rollout / migration

Applicable: assume today is a monolith that polls partners and writes availability straight to one database. Every phase is a per-partner flag.

```mermaid
%% D12: from a polling monolith to this design. Each phase has a rollback point; legacy keeps receiving ARI until the end.
gantt
    title Migration from polling monolith to adapters, sharded inventory, and ES
    dateFormat  YYYY-MM-DD
    axisFormat  %b
    section Ingestion
    Adapters + Kafka, shadow write to new DB          :a1, 2027-01-04, 42d
    Diff shadow vs legacy, fix adapters               :a2, after a1, 28d
    section Inventory
    New inventory DB as read-only mirror              :b1, after a1, 28d
    Flip bookings per partner cohort, 1 to 100 pct    :b2, after a2, 42d
    section Search
    ES dual-read, compare top 20 with legacy          :c1, after b1, 28d
    Cut over search, retire legacy                    :c2, after b2, 21d
```

Rollback points:
- Ingestion shadow and diff: turn the shadow consumer off. Nothing reads the new DB yet.
- Read-only mirror: drop it and rebuild. Legacy is still the source of truth.
- Flip bookings per cohort: flip the cohort's flag back. Legacy keeps receiving ARI, so no backfill. Bookings made on the new path are copied back by the outbox consumer that feeds legacy.
- ES dual-read: switch reads back. No data change.
- Cut over: the only irreversible step. Legacy is retired only after the last cohort runs clean for 2 weeks.
