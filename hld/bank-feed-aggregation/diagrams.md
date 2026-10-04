# Diagrams: bank feed aggregation

> One-line answer: twelve views of one design. A refresh scheduler writes due times and demand onto connection rows; a rate governor that owns each institution's token bucket, cap on calls in flight, lanes and breakers, and issues grants that die after 1 s, is the only way to reach a bank; connectors write immutable raw pages; an ingester applies each fetch in one transaction on a connection-sharded Postgres, keyed by a deterministic fingerprint, matches pending to posted, and appends a per-account change log that QuickBooks reads posted-only. The bank's rate limit and availability is the one red box.

The D1 to D12 set from `hld/CLAUDE.md` §4, each with a one-line caption. A diagram already in [`solution.md`](solution.md) gets a pointer here, never a second copy. Acronyms: FDX (Financial Data Exchange, the bank API standard), OFX (Open Financial Exchange, the older protocol), OAuth (open authorization), PKCE (proof key for code exchange), KMS (key management service), HSM (hardware security module), AZ (availability zone), AIMD (additive increase, multiplicative decrease), HTB (hierarchical token bucket), mTLS (mutual TLS), CDC (change data capture), MFA (multi-factor authentication). B1 is the largest institution: ~3 M connections, an assumed 1,000 calls/s and 800 in flight [estimate].

| # | Diagram | Where it lives |
|---|---|---|
| D1 | Context | below |
| D2 | Data flow | below |
| D3 | Component architecture (final design) | [solution §6](solution.md#6-final-design-and-the-six-core-flows) |
| D4 | Happy path per FR | FR1 connect: [solution §4.1](solution.md#41-connect-link-accounts-with-a-token-not-a-password). FR2 scheduled refresh: [solution §4.2](solution.md#42-refresh-on-a-schedule-on-demand-and-on-webhooks-inside-the-banks-limit); on-demand: [solution Flow 2](solution.md#flow-2-monday-9-am-at-b1-and-who-waits). FR3 ingest: [solution §4.3](solution.md#43-ingest-idempotently-every-fetch-retry-and-replay-is-a-no-op-for-rows-we-already-have). FR4 pending to posted: [solution §4.4](solution.md#44-reconcile-pending-and-posted-and-publish-a-clean-stream). Webhook-triggered partner refresh: below |
| D5 | Failure paths | Crash mid-write: [solution Flow 3](solution.md#flow-3-a-worker-crashes-halfway-through-a-write). 6-hour outage: [solution §10.4](solution.md#104-failure-timeline). A connector stalls before publishing, consent revoked during a refresh, a 429 storm: below |
| D6 | Decision flows | Fingerprint: [solution §5.3](solution.md#53-a-worker-crashes-halfway-through-a-page-two-identical-5-coffees-and-no-ids-exactly-once). Outage handling: [solution §5.5](solution.md#55-b1s-api-is-down-for-6-hours-what-do-users-see-and-what-happens-when-it-recovers). Id migration: [solution §5.6](solution.md#56-b1-migrates-its-core-system-and-every-transaction-id-changes-what-happens-to-dedup). Matcher (both directions) and snapshot vs delta: below |
| D7 | Entity relationship | [solution §3.3](solution.md#33-data-model) |
| D8 | State machines | Transaction row: [solution §5.4](solution.md#54-a-4500-pending-charge-posts-two-days-later-as-5400-with-a-new-id-one-transaction-or-two-what-if-there-were-two-4500-pendings). Connection and institution breaker: below |
| D9 | Deployment / topology | below, plus governor shard ownership |
| D10 | Scaling / partitioning | below |
| D11 | Failure mode map | below, two trees |
| D12 | Rollout / migration | below |

## D1. Context (zoom-out)

Our system as one box: apps and consumer services on one side, banks, partners and the key service on the other.

```mermaid
%% D1: the platform as one box with every external actor. Only the bank is red: its limit and its outages are what break first.
flowchart LR
    USR[Users in QuickBooks<br/>and Credit Karma apps]:::client -->|"link accounts, tap refresh,<br/>answer MFA prompts"| SYS[Bank feed platform<br/>connect, refresh, ingest,<br/>match, change log]:::service
    SYS -->|"accounts, transactions,<br/>as_of, needs-action prompts"| USR
    SYS -->|"OAuth + PKCE, 14-day window calls,<br/>within each bank's limit"| BANK[Institutions<br/>FDX and OFX APIs]:::critical
    BANK -->|"tokens, pages, 429, 503,<br/>webhooks where offered"| SYS
    SYS -->|"sync cursor calls,<br/>refresh calls"| AGG[Partner aggregators<br/>Plaid, MX, Finicity]:::external
    AGG -->|"added, modified, removed,<br/>SYNC_UPDATES_AVAILABLE"| SYS
    SYS -->|"change log, posted only"| QBO[QuickBooks bank feed<br/>For Review, books]:::external
    SYS -->|"change log, all statuses"| CK[Credit Karma,<br/>alerts, categorization]:::external
    SYS -->|"wrap and unwrap<br/>tenant data keys"| KMS[KMS / HSM]:::external
    REL[Institution relations<br/>and on-call]:::client -->|"contract limits, REMAP<br/>approvals, breaker overrides"| SYS
    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

## D2. Data flow (DFD)

Inputs to outputs with format, size and rate. Averages unless marked peak; numbers from solution §2.

```mermaid
%% D2: data flow. Processes are rounded, stores are cylinders. 60 M refreshes/day, 180 M bank calls/day, 150 M new rows/day.
flowchart LR
    APP[Apps]:::client -->|"tap, JSON ~200 B,<br/>98/s avg, ~1k/s peak"| API(Edge API +<br/>scheduler):::service
    API -->|"demand + due times,<br/>~700 row writes/s"| CDB[(Connection DB<br/>15 M rows, 15 GB)]:::store
    CDB -->|"due rows, batches of 500"| GOV(Rate governor):::service
    GOV -->|"job + grant ~300 B,<br/>~700/s"| CW(Connectors):::service
    VAULT[(Vault)]:::store -->|"token ~2 KB, 700/s"| CW
    BANK[Banks and partners]:::critical -->|"JSON or OFX pages ~35 KB,<br/>2.1k calls/s, 4.5 TB/day raw"| CW
    CW -->|"gzip pages ~6 KB,<br/>0.75 TB/day"| RAW[(Raw store<br/>90 d hot, 68 TB)]:::store
    CW -->|"fetch-completed ~500 B,<br/>~700/s"| KR[[Kafka raw-fetches<br/>128 partitions]]:::queue
    KR -->|"pointer, in order<br/>per connection"| ING(Ingester + matcher):::service
    RAW -->|"pages, ~9 B rows/day re-read,<br/>14-day + weekly 60-day"| ING
    ING -->|"upserts ~1 KB, 2.4k writes/s,<br/>150 GB/day"| TXN[(Transaction store<br/>32 shards, ~60 TB)]:::store
    TXN -->|"change entries ~1 KB,<br/>2.4k/s, 210 M/day"| KC[[Kafka account-changes<br/>256 partitions]]:::queue
    KC -->|"posted only for QuickBooks"| CONS[Consumers]:::client
    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
```

## D3. Component architecture

The final design is [solution §6](solution.md#6-final-design-and-the-six-core-flows): 14 nodes, red on the institutions.

## D4. Happy paths, one per FR

FR1 to FR4 are in solution §4.1 to §4.4 (one `sequenceDiagram` each) and the on-demand variant of FR2 is Flow 2. The one path not drawn there: a partner's webhook triggers a DELTA refresh.

### D4b. A partner webhook triggers a cursor-based refresh

```mermaid
%% D4b (FR2 + FR3, partner route): the webhook is only a hint; the cursor advances only after our ingest commits.
sequenceDiagram
    autonumber
    participant P as Plaid
    participant E as Edge API
    participant G as Governor (key Plaid)
    participant W as Connector
    participant I as Ingester
    participant S as Transaction store
    P->>E: SYNC_UPDATES_AVAILABLE for item i_4, signed
    E->>E: verify signature, event id not seen
    E->>G: demand WEBHOOK on c_31 (Plaid route)
    E-->>P: 200
    G-->>W: job c_31, grant from Plaid's per-client bucket
    W->>P: transactions sync, cursor k_17, count 500
    P-->>W: 3 added, 1 modified, 1 removed, next_cursor k_18, has_more false
    W->>I: manifest mode DELTA, cursor_after k_18
    I->>S: BEGIN, upsert by provider id, REMOVED only for the listed id, change log
    S-->>I: committed
    I->>G: fetch done, store cursor k_18 on c_31
    Note over W,I: A crash before the cursor is stored re-reads from k_17, and every item is a no-op on its fingerprint
```

## D5. Failure paths

Crash mid-write is solution Flow 3 and the 6-hour outage is solution §10.4. Three more below.

### D5a. A connector stalls before publishing, and publishes late

```mermaid
%% D5a: reclaim waits 45 s, so the stalled connector's calls never overlap the replacement's; fetch_seq makes the late publish a no-op. The second fetch's calls are extra calls against B1's limit, paid with new tokens.
sequenceDiagram
    autonumber
    participant G as Governor (B1)
    participant W1 as Connector 1
    participant W2 as Connector 2
    participant B as Bank B1
    participant K as Kafka raw-fetches
    participant I as Ingester
    G-->>W1: job c_9, grant issued 09:13:00, start by +1 s, fetch_seq 58
    W1->>B: token call, accounts, 2 windows, all done by +4 s
    Note over W1: long garbage-collection pause before the manifest is published
    G->>G: no release by +45 s (25 s job deadline + 20 s call timeout), reclaim the call unit
    G-->>W2: job c_9, new grant, fetch_seq 59
    W2->>B: accounts + 2 windows (access token still valid, no token call)
    W2->>K: fetch-completed c_9, 59
    K->>I: apply 59, last_applied becomes 59
    Note over W1: pause ends, W1 publishes, or the manifest sweeper does after 60 s
    W1->>K: fetch-completed c_9, 58
    K->>I: 58 is not above 59, skip, ack
    Note over G,B: B1 served c_9 twice in about a minute. The 3 calls of fetch 59 are extra calls against the limit, never concurrent with fetch 58
```

### D5b. The user revoked consent at the bank during a scheduled refresh

```mermaid
%% D5b: invalid_grant is a per-connection failure. It leaves every lane and never counts toward the institution's breaker.
sequenceDiagram
    autonumber
    participant W as Connector
    participant V as Vault
    participant B as Bank B1 token endpoint
    participant G as Governor (B1)
    participant D as Connection DB
    participant A as User's app
    W->>V: token for c_12 with grant
    V->>V: access token expired, single-flight refresh for c_12
    V->>B: refresh_token grant, mTLS
    B-->>V: 400 invalid_grant
    V-->>W: CONSENT_REVOKED
    W->>G: release grant, outcome CONNECTION_ERROR, calls_used 1
    G->>D: c_12 status NEEDS_USER_ACTION, clear next_due_at
    Note over G: not counted toward B1's breaker, only institution-level errors are
    A->>D: next app open reads c_12 status
    A-->>A: banner, reconnect B1 to keep your feed updated
```

### D5c. A 429 storm at B1 under a surge

```mermaid
%% D5c: the bank pushes back. AIMD halves the rate, Retry-After is honored, and the lanes decide who absorbs the cut.
sequenceDiagram
    autonumber
    participant G as Governor (B1)
    participant W as Connectors
    participant B as Bank B1
    G->>W: dispatching at about 857 calls/s (the 800-call cap binds), m = 1.0
    W->>B: calls
    B-->>W: 429 Too Many Requests, Retry-After 30 s, on 8% of calls
    W->>G: release grants, outcome THROTTLED
    G->>G: m = 0.5, rate 500 calls/s, pause dispatch 30 s for throttled jobs
    Note over G: rate 500, lanes keep their shares, on-demand 100, webhook 75, schedule 200, retries 25, float 100
    G->>W: throttled jobs back in their lanes, same priority, tokens not refunded
    loop each clean minute
        G->>G: m = m + 0.05
    end
    Note over G,B: about 10 clean minutes later m is back to 1.0. A second 429 burst halves it again
```

## D6. Activity / decision flows

The fingerprint flow, the outage flow and the id-migration flow are in solution §5.3, §5.5 and §5.6. Two more here.

### D6a. The matcher, in both directions

```mermaid
%% D6a: runs for each new row inside the ingest transaction. Posted rows look back for their pending; pending rows look for an unlinked posted row. Errors here only affect display, never the books.
flowchart TD
    NEW[New row in a complete<br/>account window] --> ST{Status?}
    ST -->|"pending"| CONT{No-id route, and pairs with<br/>a pending missing from<br/>this window?}
    CONT -->|"yes"| KEEP[Same txn_id,<br/>one MODIFIED]
    CONT -->|"no"| REV{Matches a posted row<br/>with no pending link?}
    REV -->|"yes"| SUPL[Insert as SUPERSEDED,<br/>no posted-only event]
    REV -->|"no"| ACT[Insert ACTIVE pending]
    ST -->|"posted"| L{Provider link present?}
    L -->|"yes"| SUP[Supersede that pending,<br/>REMOVED + ADDED with link]
    L -->|"no"| R{Category rules pass:<br/>amount band, date window,<br/>merchant similarity?}
    R -->|"one or more"| OLD[Best score, ties to the<br/>oldest pending, then txn_id]
    OLD -->|"chosen pending"| SUP
    R -->|"none"| NONE[ADDED, no link]
    ACT -.->|"never matched"| EXP[REMOVED when dropped twice,<br/>EXPIRED after the window]
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    class NEW client
    class ST,CONT,REV,L,R decision
    class KEEP,SUPL,ACT,SUP,OLD,NONE,EXP service
```

- SUPERSEDED and EXPIRED are terminal: a bank that keeps listing or edits such a row may change its stored content for audit, but no event is emitted and it is never reactivated. Both no-id gaps (an edited pending, a late pending) are reproduced in [`deep-dives/pending-to-posted-matching.md`](deep-dives/pending-to-posted-matching.md) §5.

### D6b. Snapshot vs delta ingest

```mermaid
%% D6b: two ingest modes. A SNAPSHOT says what is true for a date range, so absence counts. A DELTA says what changed, so only explicit removals count.
flowchart TD
    M[Manifest] --> MODE{Mode?}
    MODE -->|"SNAPSHOT: FDX, OFX"| W[Whole-date window,<br/>guard day, counters]
    W --> DIFF[Diff against stored window:<br/>insert, modify, missing count]
    MODE -->|"DELTA: partner sync"| D[added, modified, removed<br/>by provider id]
    D --> APPLY[Upsert added and modified,<br/>REMOVED only if listed]
    DIFF --> TX[(One transaction:<br/>rows, change log)]
    APPLY --> TX
    TX -->|"after commit"| CUR[Advance partner cursor<br/>on the connection]

    class M client
    class MODE decision
    class W,DIFF,D,APPLY,CUR service
    class TX store

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

## D7. Entity relationship

In [solution §3.3](solution.md#33-data-model), with access patterns and the partition key (`connection_id` for the transaction store).

## D8. State machines

The transaction row lifecycle is in solution §5.4. Two more lifecycles matter: the connection and the institution's breaker.

### D8b. Connection

```mermaid
%% D8b: one connection's lifecycle. Only ACTIVE and DORMANT connections are in any lane.
stateDiagram-v2
    direction LR
    [*] --> Linking: link session
    Linking --> Active: tokens stored
    Linking --> [*]: user abandons
    Active --> Dormant: no activity 90 days
    Dormant --> Active: owner reads
    Active --> NeedsUser: consent or MFA
    Dormant --> NeedsUser: consent or MFA
    NeedsUser --> Active: user reconnects
    Active --> Migrating: route switch
    Migrating --> Active: REMAP fetch done
    Active --> Deleted: user deletes
    NeedsUser --> Deleted: user deletes
    Deleted --> [*]
```

- `Active`: 3 scheduled refreshes a day. `Dormant`: 1 a day. `NeedsUser`: no bank calls at all until the user acts. `Migrating`: a credential route moving to FDX after re-consent, whose first fetch runs in REMAP mode (solution §5.6). `Deleted`: token revoked at the bank, secrets destroyed.

### D8c. Institution breaker

```mermaid
%% D8c: one breaker per institution, owned by the governor. Ramping is a separate state so a recovered bank is never hit at full rate.
stateDiagram-v2
    direction LR
    [*] --> Closed
    Closed --> Open: 50% of last 200 fail
    Closed --> Maintenance: 503 with Retry-After
    Maintenance --> Ramping: Retry-After passed
    Open --> HalfOpen: 60 s elapsed
    HalfOpen --> Open: probe fails
    HalfOpen --> Ramping: 20 probes succeed
    Ramping --> Closed: m reaches 1.0
    Ramping --> Open: error spike
```

- `Open`: over the last 200 calls, never more than 5 minutes back, at least 20 calls and 50% failing at the institution level, or 5 consecutive failures at a tiny institution. At B1 on timeouts that is ~22 s after the outage starts.
- `Ramping`: m starts at 0.1 and doubles every 2 minutes (about 8 minutes to full rate). The catch-up, most stale first, starts when the breaker enters `Ramping`. `Maintenance` never pages anyone.
- A separate **data breaker** per institution watches content, not calls: over 1% of account windows empty in 30 minutes (where the last fetch had at least 5 rows) pauses ingestion while fetching continues, and pages. It closes by hand or after an hour of normal windows.

## D9. Deployment / topology

One active fetch region, a warm standby region. Fetching is single-writer per institution, so it does not go active-active; reads do.

```mermaid
%% D9: where each piece runs. Dashed edges cross a region boundary. Banks allowlist both regions' egress IPs in advance. etcd is one quorum across 3 regions, so a partition cannot elect two governors.
flowchart LR
    BANK[Institutions<br/>and partners]:::critical
    subgraph RA[Region A, active for fetching, 3 AZs]
        EG[Egress NAT<br/>fixed allowlisted IPs]:::client
        GOVA[Governor leaders, 32 shards<br/>standbys in another AZ]:::service
        CWA[Connectors ~400 pods peak,<br/>ingesters ~20 pods]:::service
        KA[[Kafka, RF 3 over 3 AZs]]:::queue
        TA[(Transaction store 32 primaries,<br/>sync standby in another AZ)]:::store
        VA[(Vault + connection DB,<br/>3 AZs)]:::store
    end
    subgraph RB[Region B, warm standby]
        TB[(Async replicas,<br/>feed API reads)]:::store
        GOVB[Governor standbys,<br/>connectors scaled to zero]:::service
        EGB[Egress NAT,<br/>also allowlisted]:::client
    end
    OBJ[(Raw store, object storage,<br/>replicated across regions)]:::store
    ETCD[(etcd, one quorum<br/>5 members over 3 regions)]:::store
    ETCD -->|"leases + epochs"| GOVA
    ETCD -.->|"lease only with<br/>quorum agreement"| GOVB
    GOVA -->|"grants, start-by 1 s"| CWA
    CWA -->|"calls"| EG
    EG -->|"mTLS, 14-day windows"| BANK
    CWA -->|"fetch events"| KA
    CWA -->|"encrypted pages"| OBJ
    KA -->|"apply fetch"| TA
    CWA -->|"token reads"| VA
    TA -.->|"async WAL, ~1 s"| TB
    GOVB -.->|"takes leases only on<br/>region failover"| EGB
    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
```

- **Crosses a region:** async WAL (write-ahead log) to replicas, raw-store replication, and on failover the governor leases. Nothing on the fetch path is synchronous across regions. A region loss loses at most ~1 s of change log; the next fetch of each affected connection rebuilds it, because the bank holds the truth. Consumers see a new cursor epoch and resync from the last common `seq`.
- **etcd spans 3 regions** (a member in a third region breaks ties), or cross-region governor failover is manual. With a 2-region etcd, a partition can elect a leader on each side, and expiring grants do not help: both sides issue fresh ones.

### D9b. Governor shard ownership

```mermaid
%% D9b: the lease and the epoch give one dispatcher per institution. Grants older than 1 s are void at the holder, so a paused old leader can only under-use. An unplanned failover starts with an empty bucket; a planned handoff passes m.
flowchart LR
    ETCD[(etcd<br/>lease 10 s, epoch)] -->|"lease + epoch 12"| L[Leader, shard 0<br/>B1 + 469 others]
    ETCD -.->|"watch, takes over<br/>after lease + margin"| S[Standby, shard 0]
    L -->|"due rows, SKIP LOCKED,<br/>lease writes"| CDB[(Connection DB)]
    L -->|"job + grant, epoch 12"| CW[Connectors]
    CW -->|"drop grants<br/>from older epochs"| CW
    CW -->|"release, calls used,<br/>errors, latency"| L
    S -->|"unplanned takeover: empty<br/>bucket, m = 0.1, reclaim at 45 s"| CDB

    class L,S,CW service
    class ETCD,CDB store

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
```

## D10. Scaling / partitioning

Three partition schemes, one per job. The hot spot is not one of our shards: it is B1's limit, which no amount of our sharding can split.

```mermaid
%% D10: governor shards by institution, Kafka and the transaction store by connection, the change topic by account. Red is B1's limit.
flowchart LR
    INST[15k institutions]:::client -->|"hash(institution) mod 32,<br/>B1 on shard 0"| GS[Governor shards 0 to 31<br/>~470 institutions each]:::service
    GS -->|"B1: 417 calls/s avg,<br/>~948 at Monday peak"| B1[B1 limit 1,000 calls/s,<br/>800 in flight: ~857 usable]:::critical
    GS -->|"the other 14,999: ~1.7k calls/s"| REST[Long tail,<br/>5 calls/s default each]:::external
    CONN[15 M connections]:::client -->|"hash(connection_id) mod 128"| KR[[raw-fetches<br/>128 partitions, ~5/s each]]:::queue
    KR -->|"consumer per partition range"| ING[Ingesters ~20 pods]:::service
    ING -->|"hash(connection_id) mod 32"| TS[(Transaction store<br/>32 shards, ~1.9 TB, ~75 writes/s)]:::store
    TS -->|"key account_id"| KC[[account-changes<br/>256 partitions, ~9/s each]]:::queue
    B1 -.->|"the fix is not sharding:<br/>lanes, floors, tiers"| LANES{Who waits<br/>solution 5.1}:::decision
    GROW{10x connections}:::decision -.->|"shards to 128, no<br/>change to keys"| TS
    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

- Per partition: `raw-fetches` ~700 msg/s ÷ 128 ≈ 5/s; `account-changes` 2.4k/s ÷ 256 ≈ 9/s. Per transaction-store shard: ~75 writes/s average, ~300 at peak, ~1.9 TB hot. Storage sets the shard count, not throughput. No connection is hot: the busiest SMB account adds a few hundred rows a day. See [`../../concepts/sharding.md`](../../concepts/sharding.md).

## D11. Failure mode map

Component, what fails, blast radius, mitigation. Two trees to stay under 15 nodes each.

### D11a. Fetch path

```mermaid
%% D11a: fetch path failures. Each leaf names the blast radius, then the mitigation.
flowchart TD
    ROOT[Fetch path]:::client --> BK[Bank]:::critical
    ROOT --> GV[Governor shard]:::service
    ROOT --> CN[Connector pod]:::service
    ROOT --> VT[Vault or KMS]:::store
    BK -->|"down 6 h"| BK1[Its connections stale,<br/>breaker, ramp, catch-up]:::service
    BK -->|"throttles, 429"| BK2[Its lanes slow,<br/>AIMD halves, schedule floor]:::service
    BK -->|"changes all ids"| BK3[400 M duplicates avoided,<br/>pairing + REMAP mode]:::service
    BK -->|"200 OK, empty data"| BK4[400 M removals avoided,<br/>data breaker + removal guard]:::service
    GV -->|"leader dies"| GV1[~470 institutions pause ~12 s,<br/>ramp only if unplanned]:::service
    GV -->|"paused or stale leader"| GV2[Grants void after 1 s<br/>at the holder: under-use only]:::service
    CN -->|"stalls or dies"| CN1[One connection refetched,<br/>reclaimed at 45 s, no overlap]:::service
    VT -->|"down"| VT1[All fetches stop, our own<br/>single point of failure,<br/>3 AZs, page at once]:::service
    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
```

### D11b. Data path

```mermaid
%% D11b: data path failures. Fetching keeps running while any of these recover; the raw store and Kafka buffer.
flowchart TD
    ROOT[Data path]:::client --> IG[Ingester]:::service
    ROOT --> TS[Transaction store shard]:::store
    ROOT --> KF[Kafka]:::queue
    ROOT --> RL[Outbox relay]:::service
    ROOT --> PR[Parser or normalizer release]:::service
    ROOT --> MF[Manifest publish]:::service
    IG -->|"crash mid-write"| IG1[Txn rolls back,<br/>redelivery is a no-op]:::service
    TS -->|"primary fails"| TS1[1/32 of connections,<br/>~30 s failover, Kafka buffers]:::service
    KF -->|"broker lost"| KF1[None, RF 3,<br/>min ISR 2]:::service
    RL -->|"stalls"| RL1[Consumers lag,<br/>log intact, resumes at seq]:::service
    PR -->|"bad rows"| PR1[Spike guard quarantines,<br/>pin version, shadow rebuild]:::service
    MF -->|"connector dies after<br/>writing the manifest"| MF1[Sweeper republishes<br/>after 60 s]:::service
    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
```

## D12. Rollout / migration

From QuickBooks' current bank-feed pipeline (and third-party aggregators) to this platform, one institution at a time. Every phase has a rollback point; the one-way door is QuickBooks accepting rows keyed by our `txn_id`, so the legacy-id mapping is kept until phase 5.

```mermaid
%% D12: migration plan. Each phase ends at a milestone that is also its rollback point. No phase fetches twice from a bank.
gantt
    title Migrating bank feeds onto the governor platform
    dateFormat YYYY-MM-DD
    axisFormat %b %d
    section Foundation
    Import transactions with legacy ids as provider ids :p0, 2027-01-04, 14d
    Rollback point, drop the import                     :milestone, m0, after p0, 0d
    section Shadow
    Replay old pipeline raw responses, diff posted sets  :p1, after p0, 28d
    Rollback point, nothing consumed yet                 :milestone, m1, after p1, 0d
    section Long tail
    Cut over 15k small institutions in cohorts           :p2, after p1, 28d
    Rollback point, route flip per institution           :milestone, m2, after p2, 0d
    section Top 20
    Cut over top 20 institutions one at a time           :p3, after p2, 56d
    Rollback point, route flip, old window refills       :milestone, m3, after p3, 0d
    section Decommission
    Stop old fetchers, keep legacy id map 90 days        :p4, after p3, 30d
    Drop legacy id map                                   :milestone, m4, after p4, 0d
```

- Phase 1 never calls a bank: it replays the old pipeline's stored responses, or a 1% sample inside the old pipeline's budget. A cutover moves the institution's whole limit to the new governor in one step, because two fetchers sharing one bank limit is exactly the breach this design exists to prevent.
