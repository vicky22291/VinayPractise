# Diagrams: Multi-region metadata store

The D1 to D12 set from `hld/CLAUDE.md` §4. A diagram is drawn once: the ones embedded in [`solution.md`](solution.md) are linked here, not repeated.

| # | Diagram | Where |
|---|---|---|
| D1 | Context | below |
| D2 | Data flow | below |
| D3 | Component architecture (final design) | `solution.md` §6 |
| D4 | Happy path per FR | FR1 write: `solution.md` §5.2. FR1 linearizable read: §6 Flow 2. FR1 stale read: §6 Flow 3. FR2 list: below. FR3 cross-range txn: below. FR4 watch: below |
| D5 | Failure paths | Create race: `solution.md` §6 Flow 4. Clock skew: §10.4. Region loss: below. Paused leaseholder: below. Stale descriptor after split: below |
| D6 | Read path decision | `solution.md` §5.3 |
| D7 | Entity relationship | `solution.md` §3.3 |
| D8 | Lease state machine | `solution.md` §5.4 |
| D9 | Deployment / topology | `solution.md` §5.1 |
| D10 | Sharding / partitioning | `solution.md` §5.5 |
| D11 | Failure mode map | below |
| D12 | Rollout / migration | below |

---

## D1. Context (zoom-out)

```mermaid
%% D1: context. Our system is the gateways, the range replicas, the meta range, and the placement controller. Everything else is outside.
flowchart LR
    QP[Query planners, job schedulers<br/>in every region] -->|"get, list, watch, 500k/s"| SYS[Multi-region metadata store]
    DDL[DDL and admin clients] -->|"put, create, delete, txn, 5k/s"| SYS
    SYS -->|"change events"| IDX[Search indexer, caches]
    SYS -->|"audit stream"| AUD[Audit log]
    CLK[Cloud time service<br/>NTP or PTP per region] -.->|"clock within 500 ms"| SYS
    IAM[Identity provider] -.->|"signed tokens with tenant_id"| DDL
    OBJ[Object storage] -.->|"values above 64 KB live here, key holds pointer"| DDL

    class QP,DDL client
    class SYS service
    class IDX,AUD,CLK,IAM,OBJ external

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

## D2. Data flow (DFD)

```mermaid
%% D2: data flow with sizes and rates. User data is 1 KB per key. The log crosses regions at 15 MB/s. Everything else is control traffic in KB per second.
flowchart LR
    C[Client] -->|"PUT, 1 KB, 5k/s aggregate"| GW(Gateway)
    GW -->|"descriptor lookup, 1 in 10k requests"| META[(Meta range)]
    GW -->|"proposal, 1 KB + 100 B header"| LH(Leaseholder)
    LH -->|"AppendEntries, 1 KB per entry, 3 remote streams = 15 MB/s"| FOL[(Followers V O O F)]
    FOL -->|"ack, 50 B"| LH
    LH -->|"apply, newest version first"| MV[(MVCC store, 1.5 TB per replica)]
    C -->|"GET linearizable, 100k/s"| LH
    C -->|"GET stale_ok, 350k/s"| FOL
    LH -->|"applied entries + resolved_ts every 1 s"| FEED[[Change feed]]
    FEED -->|"events, 5k/s"| W[Watchers]
    LH -->|"closed_ts every 200 ms, piggybacked"| FOL
    PC(Placement controller) -->|"split, merge, membership, lease transfer entries, ~10/s"| LH

    class C,W client
    class GW,LH,PC service
    class META,FOL,MV store
    class FEED queue

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
```

## D4. FR2: list by prefix at one snapshot, across two ranges, served by followers

```mermaid
%% D4 (FR2): a paginated list. One as_of for every page. Pages come from followers in the caller's region because the read is at a closed timestamp.
sequenceDiagram
    autonumber
    participant C as Client (F)
    participant G as Gateway F
    participant F42 as Follower F1 (range 42)
    participant F43 as Follower F1 (range 43)
    C->>G: GET keys?prefix=sales/&stale_ok=5000
    G->>G: as_of = min(closed_ts of ranges 42, 43), ranges overlapping [t1/sales/, t1/sales0)
    G->>F42: scan(t1/sales/, t1/sales0, as_of, limit 1000)
    F42-->>G: 1000 items, more = true, last_key
    G-->>C: page 1, next_page_token(last_key, as_of)
    C->>G: GET keys?prefix=sales/&page_token=...
    G->>F42: scan(last_key, t1/sales0, as_of, 1000)
    F42-->>G: 300 items, range exhausted
    G->>F43: scan(range 43 start, t1/sales0, as_of, 700)
    F43-->>G: 700 items
    G-->>C: page 2 (same as_of, so a rename mid-list never shows twice)
```

## D4. FR3: rename across two ranges (2PC over Raft groups)

```mermaid
%% D4 (FR3, cross-range): the transaction record in range 42 is the commit point. Intents are written in parallel. Both leaseholders are in the home region, so each Raft round is one V to O trip.
sequenceDiagram
    autonumber
    participant G as Gateway V
    participant L42 as Leaseholder range 42 (coordinator)
    participant L43 as Leaseholder range 43
    G->>L42: txn: cond(sales/orders v8), cond(finance/orders v0), delete, put
    L42->>L42: propose txn record PENDING + intent delete(sales/orders)
    L42->>L43: write intent put(finance/orders) if version == 0
    par Raft round 1 (75 ms)
        L42->>L42: record + intent committed (V, V, O acks)
        L43->>L43: intent committed
    end
    L43-->>L42: intent ok
    L42->>L42: propose record COMMITTED (Raft round 2, 75 ms)
    L42-->>G: committed
    L42->>L43: resolve intent async
    Note over L42,L43: a reader that meets an intent looks up the record to decide visibility
```

## D4. FR4: watch from a version, reconnect, resolved timestamps

```mermaid
%% D4 (FR4): watch tails the applied log. Reconnect replays from the client's cursor. resolved_ts tells the client how caught up it is.
sequenceDiagram
    autonumber
    participant C as Client cache
    participant G as Gateway
    participant R42 as Range 42 feed
    participant R43 as Range 43 feed
    C->>G: watch prefix=sales/ from_version=8
    G->>R42: subscribe from commit_ts of version 8
    G->>R43: subscribe
    R42-->>G: event (sales/orders, v9)
    G-->>C: event v9
    R42-->>G: resolved_ts 10:00:01
    R43-->>G: resolved_ts 10:00:00
    G-->>C: resolved_ts 10:00:00 (min across ranges)
    Note over C: connection drops
    C->>G: watch from_version=9
    G->>R42: subscribe from v9 (replays anything after, at-least-once)
    R42-->>G: event v9 again, client dedups by (path, version)
```

## D5. Region loss, second by second

```mermaid
%% D5 (failure): V dies. Election among survivors, wait for the old lease, new epoch, serve. RPO 0 because every ack had a copy outside V.
sequenceDiagram
    autonumber
    participant CF as Client (F)
    participant O1 as Voter O1
    participant O2 as Voter O2
    participant F1 as Voter F1
    participant PC as Placement controller
    Note over O1,F1: t = 0: V3 (leader) and V1 vanish. Last commit was acked by O2.
    Note over O1,F1: t = 0 to 3 s: heartbeats missed. Pre-vote among O1, O2, F1 succeeds (3 of 5 reachable)
    O2->>O1: RequestVote term+1 (O2 has the most complete log)
    O2->>F1: RequestVote
    O1-->>O2: vote
    F1-->>O2: vote
    Note over O2: t = 3 s: leader, term+1. Lease of V3 may be valid until t = 9 s on V3's clock
    CF->>O2: PUT (routed by gateway after NotLeaseholder from V3 timed out)
    O2-->>CF: Unavailable, retry after 6 s
    Note over O2: t = 9.5 s: old lease expiry + max_offset passed on O2's clock
    O2->>O2: propose lease epoch+1, commit with O1 + F1 (155 ms)
    CF->>O2: PUT (retry, same Idempotency-Key)
    O2-->>CF: 200 (about 160 ms, commit needs F1 now)
    PC->>PC: t = 5 min: V nodes dead, add voters in O and F to restore 5
```

## D5. Paused leaseholder wakes up

```mermaid
%% D5 (failure): V3 pauses 30 s mid-read. The post-evaluation lease check on the monotonic clock rejects the reply. Even if the clock did not advance, the next Raft message carries a higher term.
sequenceDiagram
    autonumber
    participant C as Client
    participant V3 as Old leaseholder V3
    participant O2 as New leaseholder O2 (from t = 12 s)
    C->>V3: GET sales/orders (linearizable), t = 0
    V3->>V3: lease check ok, evaluate: version 8
    Note over V3: t = 0.001 s: process paused (GC, VM migration) for 30 s
    Note over O2: t = 12 s: O2 holds the lease, epoch+1
    C->>O2: (other client) PUT sales/orders version 9, t = 20 s
    Note over V3: t = 30 s: resumes
    V3->>V3: post-evaluation check: monotonic now > lease_expiry, FENCED
    V3-->>C: NotLeaseholder, hint O2
    C->>O2: GET sales/orders
    O2-->>C: version 9
    Note over V3: if the guest clock did not advance, V3's next AppendEntries to O1 returns term+1 and V3 steps down before replying
```

## D5. Stale descriptor after a split

```mermaid
%% D5 (failure): the gateway cache says range 42 covers a key that range 43 now owns. The store corrects the cache in one round trip. No wrong answer is ever returned.
sequenceDiagram
    autonumber
    participant G as Gateway
    participant L42 as Leaseholder range 42 (gen 7)
    participant L43 as Leaseholder range 43 (new)
    G->>L42: PUT t1/sales/zeta (cache says range 42, gen 6)
    L42-->>G: RangeKeyMismatch, descriptors: 42 gen 7 [a..m), 43 gen 1 [m..z)
    G->>G: update cache
    G->>L43: PUT t1/sales/zeta
    L43-->>G: 200
```

## D11. Failure mode map

```mermaid
%% D11: each component, what fails, the blast radius, the mitigation. The only red node is the home region loss on the commit path: it is the one that changes latency for every tenant homed there.
flowchart TD
    A[Component fails] --> B{Which?}
    B -->|"one voter node"| N1[Range keeps 4 of 5<br/>no latency change] --> N1M[Re-replicate after 5 min]
    B -->|"leaseholder node"| N2[Its ranges lose lease<br/>writes unavailable ~5 to 12 s] --> N2M[Election, lease expiry, new epoch<br/>lease preference moves it back to home]
    B -->|"home region"| N3[Every range homed there<br/>fails over, commits 155 ms] --> N3M[3 of 5 survive, RPO 0<br/>controller restores 5 voters]
    B -->|"far region F"| N4[4 of 5 survive<br/>no latency change] --> N4M[Nothing to do until it returns]
    B -->|"meta range quorum"| N5[Descriptor cache misses fail<br/>cached routes keep working] --> N5M[Same 5-voter rules, shrinks with cache warmth]
    B -->|"gateway"| N6[Region-local, stateless] --> N6M[Load balancer, client retries next gateway]
    B -->|"clock offset > 500 ms"| N7[Node exits, its leases fail over] --> N7M[Alert at 250 ms, cloud time service]
    B -->|"placement controller"| N8[No splits, moves, repairs] --> N8M[Zero packet-path effect, restart]
    B -->|"partition V from O and F"| N9[V leaseholders lose lease in 9 s<br/>V clients get Unavailable or stale] --> N9M[Client SDK fails over to O gateway if egress works]

    class A,B decision
    class N1,N2,N4,N5,N6,N7,N8,N9 service
    class N3 critical
    class N1M,N2M,N3M,N4M,N5M,N6M,N7M,N8M,N9M store

    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
```

## D12. Rollout / migration from single-region Postgres

```mermaid
%% D12: per-tenant migration with a rollback point at every phase. Postgres stays the truth until phase 4; reverse CDC keeps it current after.
gantt
    title Postgres to multi-region store, per tenant cohort
    dateFormat  YYYY-MM-DD
    axisFormat  %b %d
    section Build
    Store deployed in 3 regions, shadow traffic     :a1, 2026-10-01, 14d
    Region-kill drill passes in staging             :a2, after a1, 7d
    section Backfill
    CDC snapshot plus tail, Postgres to store       :b1, after a2, 7d
    Row-count and checksum reconciliation           :b2, after b1, 3d
    section Dual write
    App writes both, Postgres is truth              :c1, after b2, 14d
    Divergence alerts at zero for 7 days            :c2, after c1, 7d
    section Flip reads
    stale_ok reads to store, cohort 1 percent       :d1, after c2, 7d
    linearizable reads to store, all cohorts        :d2, after d1, 14d
    section Flip writes
    Store is truth, reverse CDC to Postgres         :e1, after d2, 14d
    Rollback window closes, Postgres read only      :e2, after e1, 30d
    section Decommission
    Postgres archived                               :f1, after e2, 7d
```
