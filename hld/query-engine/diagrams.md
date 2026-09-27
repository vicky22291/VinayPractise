# Diagrams: multi-tenant distributed SQL query engine

The D1 to D12 set from `hld/CLAUDE.md` §4. A diagram is drawn once: the ones embedded in [`solution.md`](solution.md) are linked here, not repeated.

| # | Diagram | Where |
|---|---|---|
| D1 | Context | below |
| D2 | Data flow | below |
| D3 | Component architecture (final design) | `solution.md` §6 |
| D4 | Happy path per FR | FR1 small query: `solution.md` §6 Flow 1. FR2 large join with skew: Flow 2. FR3 burst and scale-out: Flow 3. FR5 cost of one statement: Flow 6. FR1 large result via links: below |
| D5 | Failure paths | Worker dies mid-shuffle: `solution.md` §6 Flow 4. Driver dies: Flow 5. Zone outage: §10.4. Object-store throttling on a hot table: below. Warm pool exhausted: below |
| D6 | Decision flow | Small-query path: `solution.md` §5.1. Isolation stack: §5.2. Failure handling: §5.4. Warm pool loop: §5.5. Admission decision: below |
| D7 | Entity relationship | `solution.md` §3.3 |
| D8 | State machine | Statement lifecycle: `solution.md` §4.1. Cluster lifecycle: below |
| D9 | Deployment / topology | below |
| D10 | Scaling / partitioning | Shuffle and skew: `solution.md` §5.3. Control-plane sharding and file-to-node hashing: below |
| D11 | Failure mode map | below |
| D12 | Rollout / migration | below |

---

## D1. Context (zoom-out)

```mermaid
%% D1: context. Our system is the SQL service: control plane plus per-tenant compute. Tables, catalog, cloud VMs and billing are outside it.
flowchart LR
    USR[Analysts, BI tools,<br/>notebooks, jobs] -->|"SQL over JDBC, ODBC, REST"| SYS[SQL query service<br/>control plane + tenant warehouses]
    ADM[Tenant admins] -->|"warehouse config, budgets"| SYS
    SYS -->|"resolve names, grants,<br/>vended credentials"| CAT[Catalog<br/>names, grants, row filters]
    SYS -->|"range GET Parquet, commits"| OBJ[(Object store<br/>Delta / Parquet tables)]
    SYS -->|"launch and terminate VMs"| CLOUD[Cloud provider<br/>VMs, network, disks]
    SYS -->|"usage per minute"| BILL[Billing system]
    SYS -->|"rows, presigned result links"| USR

    class USR,ADM client
    class SYS service
    class OBJ store
    class CAT,CLOUD,BILL external

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

## D2. Data flow (DFD)

```mermaid
%% D2: what flows where for one region at peak, with sizes and rates from solution.md §2. Scan bytes dwarf everything else.
flowchart LR
    IN([Statements<br/>~2,300/s peak, ~1 KB SQL]) -->|"submit + polls ~20k/s"| GW(Gateway)
    GW -->|"statement rows ~12k writes/s"| CP[(Control-plane store<br/>sharded by tenant)]
    GW -->|"PENDING"| WLM(Workload manager)
    WLM -->|"route"| DRV(Driver<br/>plan, schedule)
    DRV -->|"metadata, ~250 KB per cold snapshot"| META[(Table logs<br/>and checkpoints)]
    DRV -->|"tasks, 1 per 128 MB split"| WK(Workers)
    WK -->|"~240 PB/day scanned,<br/>60 to 80% from disk cache"| DATA[(Parquet data)]
    WK -->|"shuffle: MBs for small,<br/>~440 GB for a large join"| SH[(Local NVMe<br/>shuffle files)]
    SH -->|"fetch by partition"| WK
    WK -->|"<= 25 MiB inline via driver,<br/>else Arrow chunks"| RS[(Result store, 24 h)]
    RS -->|"presigned GET"| OUT([Client])
    DRV -->|"usage ~230 events/s"| MQ(Metering stream)
    MQ -->|"upsert"| ST[(System tables<br/>~40 GB/day history)]

    class IN,OUT client
    class GW,WLM,DRV,WK,MQ service
    class CP,META,DATA,SH,RS,ST store

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
```

## D4. Happy path, FR1: a large result through external links

```mermaid
%% D4 (FR1): a 3 GB result. The driver never carries the bytes; the client pulls chunks straight from the result store.
sequenceDiagram
    autonumber
    participant C as Client
    participant GW as Gateway
    participant D as Driver
    participant X as Workers
    participant R as Result store
    C->>GW: POST statement, disposition EXTERNAL_LINKS, format ARROW_STREAM
    GW->>D: run
    GW-->>C: after 10 s, statement_id, RUNNING
    D->>X: final stage tasks
    X->>R: write chunk 0 .. chunk 299 under statement_id and attempt
    X-->>D: chunk paths, row and byte counts
    D->>D: all final tasks succeeded, write manifest
    D-->>GW: SUCCEEDED
    C->>GW: GET statement
    GW-->>C: manifest with 300 chunks
    C->>GW: GET chunk 0
    GW-->>C: presigned URL, short expiry
    C->>R: GET chunk 0 directly
    Note over C,R: the manifest appears only after every chunk exists, so the result is complete or absent
```

## D5. Failure path: object-store throttling on a hot table

```mermaid
%% D5: 100 concurrent medium statements on one table prefix. 503 SlowDown is backpressure, not a node fault.
sequenceDiagram
    autonumber
    participant X as Workers (many statements)
    participant C as Disk cache
    participant O as Object store prefix
    participant D as Driver
    X->>C: read file f
    C-->>X: miss
    X->>O: range GET, request rate near 5,500 per s on this prefix
    O-->>X: 503 SlowDown
    X->>X: backoff with jitter, retry, task runs slower
    X-->>D: task still running, 3x median
    D->>D: straggler cause is throttling, suppress speculation
    X->>O: retry succeeds
    X->>C: cache f on this node
    Note over X,O: fix forward: randomized file prefixes for the table, file-to-node hashing to raise cache hits
```

## D5. Failure path: the warm pool runs dry at 09:00

```mermaid
%% D5: pool exhausted in one zone. Running warehouses are unaffected; new ones start cold, per-tenant caps keep one tenant from taking the rest.
sequenceDiagram
    autonumber
    participant W as WLM
    participant M as Compute manager
    participant P as Warm pool zone a
    participant Q as Warm pool zone b
    participant CL as Cloud API
    W->>M: acquire X-Large for tenant Acme
    M->>P: take 33 VMs
    P-->>M: only 5 left
    M->>Q: take 33 VMs from zone b
    Q-->>M: ok, cluster in zone b
    M->>CL: launch VMs to refill both pools
    W->>M: acquire for tenant Beta, 500 clusters requested
    M->>M: Beta over per-tenant pool cap, give cold VMs
    CL-->>M: cold VMs ready after 2 to 3 min
    Note over W,M: alert fires at pool below 20% of forecast, forecaster raises tomorrow's 09:00 target
```

## D6. Admission decision in the workload manager

```mermaid
%% D6: how WLM decides where a statement goes. Predicted cost, not arrival order, decides who waits.
flowchart TD
    S[Statement arrives] --> RC{Remote result<br/>cache hit?}
    RC -->|"yes"| OUT[Serve from cache on<br/>any running cluster]
    RC -->|"no"| P[Predict cost from<br/>fingerprint, tables, history]
    P --> G{Over guardrails?<br/>scan bytes, budget}
    G -->|"yes"| REJ[Reject with reason]
    G -->|"no"| CAP{A cluster has<br/>capacity for this cost?}
    CAP -->|"yes"| RUN[Route to least loaded cluster]
    CAP -->|"no"| QU[Queue: shortest predicted<br/>first, age bonus]
    QU --> DR{Estimated drain<br/>time rising?}
    DR -->|"yes, below max_clusters"| ADD[Ask compute manager<br/>for another cluster]
    DR -->|"no"| QU

    class S,OUT client
    class P,RUN,ADD service
    class REJ service
    class QU queue
    class RC,G,CAP,DR decision

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

## D8. Cluster lifecycle

```mermaid
%% D8: one cluster from pool to termination. VMs are never returned to the pool once bound to a tenant.
stateDiagram-v2
    direction LR
    [*] --> Pooled: VM booted, runtime loaded
    Pooled --> Binding: acquire for tenant
    Binding --> Running: driver elected, epoch set
    Running --> Draining: scale-in or 24 h recycle
    Running --> Failed: driver heartbeat lost
    Draining --> Terminated: running statements done
    Failed --> Terminated: epoch bumped, VMs killed
    Terminated --> [*]
```

## D9. Deployment and topology

```mermaid
%% D9: one region. Control plane spread over three zones; each cluster lives in one zone so shuffle never crosses zones; tables are regional.
flowchart TB
    subgraph REGION["Region"]
        subgraph CPL["Control plane, 3 zones"]
            GW[Gateway fleet]
            WLM[WLM shards<br/>primary + standby]
            CM[Compute manager]
            CPS[(Control-plane store<br/>replicated, sharded by tenant)]
        end
        subgraph ZA["Zone a"]
            PA[(Warm pool a)]
            C1[Acme cluster 1<br/>driver + 32 workers]
        end
        subgraph ZB["Zone b"]
            PB[(Warm pool b)]
            C2[Acme cluster 2]
            C3[Beta cluster 1]
        end
        OBJ[(Object store<br/>regional, multi-zone)]
        MQ[Metering stream<br/>RF 3 across zones]
    end
    GW -->|"statements"| WLM
    WLM -->|"state"| CPS
    WLM -->|"route"| C1
    WLM -->|"route"| C2
    CM -->|"assign"| PA
    CM -->|"assign"| PB
    C1 -->|"scan, results"| OBJ
    C2 -->|"scan, results"| OBJ
    C3 -->|"scan"| OBJ
    C1 -->|"usage"| MQ

    class GW client
    class WLM,CM,C1,C2,C3 service
    class CPS,PA,PB,OBJ store
    class MQ queue

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
```

What crosses a boundary: statements and results cross zones (small). Shuffle never crosses zones because a cluster is zonal. Nothing crosses regions: tables, warehouses and billing are regional.

## D10. Partitioning: control plane and cache locality

```mermaid
%% D10: two partitioning schemes that matter besides the shuffle. WLM by warehouse, statement rows by tenant, files to nodes by consistent hash for cache hits.
flowchart LR
    ST[Statement for<br/>warehouse W, tenant T] -->|"hash warehouse_id"| WS[WLM shard k<br/>owns W's queue]
    ST -->|"hash tenant_id"| DB[(Store shard j<br/>statement rows)]
    WS -->|"route"| DRV[Driver of a cluster in W]
    DRV -->|"hash file path to<br/>one of 32 workers"| W7[Worker 7<br/>cached file f]
    W7 -.->|"busy: idle node steals task,<br/>reads f from object store"| W12[Worker 12]
    HOT[Hot table under one prefix<br/>~50k GET/s wanted]:::critical -->|"fix: randomized<br/>file prefixes"| OBJ[(Object store)]
    W12 -->|"range GET"| OBJ

    class ST client
    class WS,DRV,W7,W12 service
    class DB,OBJ store

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
```

## D11. Failure mode map

```mermaid
%% D11: each component, what fails, blast radius, mitigation. The catalog has the widest blast radius and gets a bounded-staleness cache.
flowchart TD
    WK[Worker] -->|"VM lost"| WK1[Its tasks and map outputs,<br/>seconds of rework] --> WK2[Lineage rerun,<br/>shuffle service, decommission]
    DRV[Driver] -->|"process dies"| DR1[Up to 10 statements<br/>on one cluster] --> DR2[Statement retry if read-only<br/>and 0 rows delivered]
    WLM[WLM shard] -->|"crash"| WL1[New admissions for<br/>its warehouses pause] --> WL2[Standby resumes from<br/>persisted queue, seconds]
    CM[Compute manager / pool] -->|"exhausted"| CM1[New warehouses start cold,<br/>minutes] --> CM2[Forecast, cross-zone pools,<br/>per-tenant caps]
    CAT[Catalog]:::critical -->|"outage"| CA1[No new statement can be<br/>analyzed, every tenant] --> CA2[Driver-side metadata and grant<br/>cache, 5 min TTL, pushed revokes]
    OBJ[Object store] -->|"throttle or slowdown"| OB1[Hot tables slow] --> OB2[Disk cache, prefixes,<br/>backoff, no speculation]
    MQ[Metering stream] -->|"down"| MQ1[Usage delayed,<br/>queries unaffected] --> MQ2[Buffer and replay,<br/>idempotent keys]

    class WK,DRV,WLM,CM service
    class OBJ store
    class MQ queue
    class WK1,DR1,WL1,CM1,CA1,OB1,MQ1 decision
    class WK2,DR2,WL2,CM2,CA2,OB2,MQ2 service

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
```

Red here marks the widest blast radius, not the throughput bottleneck. The throughput bottleneck (the shuffle) is red in the final design.

## D12. Rollout: classic per-tenant clusters to serverless warehouses

```mermaid
%% D12: migration from customer-account classic clusters to serverless. Each phase has a rollback point.
gantt
    title Classic to serverless migration
    dateFormat YYYY-MM-DD
    axisFormat %b %d
    section Foundations
    Warm pools and compute manager in 2 regions   :a1, 2026-10-01, 21d
    Result store and remote result cache          :a2, 2026-10-01, 14d
    section Shadow
    Mirror 1 pct of statements, diff results      :b1, after a1, 14d
    Rollback point, stop mirroring                :milestone, m1, after b1, 0d
    section Canary
    Route 5 pct of BI warehouses                  :c1, after b1, 14d
    Route 50 pct of BI warehouses                 :c2, after c1, 14d
    Rollback point, route back by warehouse id    :milestone, m2, after c2, 0d
    section General
    All BI warehouses, then ETL warehouses        :d1, after c2, 28d
    Decommission classic control path             :d2, after d1, 14d
```

Rollback at every phase is "route the warehouse id back". Serverless writes nothing durable except results (24 h) and table commits, so there is nothing to backfill.
