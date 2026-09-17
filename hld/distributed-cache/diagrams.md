# Diagrams: distributed cache

The D1 to D12 set from `hld/CLAUDE.md` §4. Diagrams already embedded in [`solution.md`](solution.md) are listed with a pointer, not pasted twice.

| # | Diagram | Where |
|---|---|---|
| D1 | Context | below |
| D2 | Data flow | below |
| D3 | Component architecture (final design) | `solution.md` §6 |
| D4 | Happy path per FR | FR1 get hit: §6 Flow 1. FR1 miss + lease: §5.3. FR2 TTL: below. FR3 add node: §6 Flow 5. FR4 node death: §5.4 |
| D5 | Failure paths | Node death: §5.4. Config leader death: §10.4. Slow DB: §10.4. Lost delete: below |
| D6 | Decision flow (client per get) | `solution.md` §5.1 |
| D7 | Entity relationship | `solution.md` §3.3 |
| D8 | State machine (node lifecycle) | below |
| D9 | Deployment / topology | below |
| D10 | Scaling / partitioning (the ring, the hot key) | below |
| D11 | Failure mode map | below |
| D12 | Rollout / migration | below |

---

## D1. Context (zoom-out)

```mermaid
%% D1: the cache as one box. Apps read through it; the DB is the truth; CDC closes the invalidation loop; the config service is the only control plane.
flowchart LR
    APP[App servers<br/>5,000] -->|"get / set / delete, 10 M/s"| CACHE[Distributed cache<br/>400 nodes, 10 TB, RF 2]
    APP -->|"miss: read row, 500k/s<br/>write: write row, 1 M/s"| DB[(Database)]
    DB -->|"row change events"| CDC[CDC consumer]
    CDC -->|"delete key"| CACHE
    CACHE -.->|"heartbeats"| CFG[Config service]
    APP -.->|"ring, hot keys"| CFG
    OPS[Operators / autoscaler] -->|"add, drain, remove"| CFG

    class APP,OPS client
    class CACHE cache
    class DB store
    class CFG store
    class CDC service

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef cache    fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#111
```

## D2. Data flow (DFD)

```mermaid
%% D2: what flows where, with sizes and rates. Reads dominate bytes; deletes dominate the invalidation path.
flowchart LR
    A[App] -->|"get: key 40 B, 10 M/s"| C(Client lib)
    C -->|"GET + epoch, 60 B, 9.5 M/s hits"| N[(Cache node<br/>value 1 KB avg)]
    N -->|"VALUE 1 KB, 9.5 GB/s fleet"| C
    C -->|"miss + lease, 500k/s"| A
    A -->|"SELECT, 500k/s"| DB[(Database)]
    DB -->|"row 1 KB"| A
    A -->|"set key value ttl token, 1 KB, 500k/s"| N
    A -->|"UPDATE, 1 M/s"| DB
    A -->|"delete key, 60 B, 1 M/s"| N
    DB -->|"binlog, 1 M rows/s"| CDC(CDC consumer)
    CDC -->|"delete key, batched 100, 1 M/s"| N
    N -->|"async set/delete, 1 ms batches"| R[(Replica node)]
    N -->|"heartbeat 100 B, 1/s"| CFG[(Config service)]
    CFG -->|"ring 480 KB on change, else 20 B, 1,000/s"| C

    class A client
    class C,CDC service
    class N,R cache
    class DB,CFG store

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef cache    fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#111
```

## D4 (FR2). TTL: set, lazy expiry, crawler

```mermaid
%% D4 (FR2): an item's TTL life. Expiry is checked on read; the crawler only reclaims memory.
sequenceDiagram
    autonumber
    participant C as Client
    participant N as Node shard
    participant CR as Crawler (same shard, background)
    C->>N: set(k, v, ttl 3600 s)
    N->>N: ttl += jitter (client added ±10%), expires_at = mono_now + ttl
    N-->>C: stored
    C->>N: get(k) [t = 3500 s]
    N->>N: expires_at > now: hit
    N-->>C: value
    C->>N: get(k) [t = 3700 s]
    N->>N: expires_at <= now: unlink, free chunk
    N-->>C: miss + lease
    Note over CR: items never read again
    CR->>N: walk 1% of buckets per second, free expired
```

## D5 (fourth). Lost delete: app crashes between DB write and cache delete

```mermaid
%% D5: the app-side delete never happens. CDC issues it 500 ms later. Without CDC the value is stale until TTL.
sequenceDiagram
    autonumber
    participant B as Writer app
    participant DB as Database
    participant CDC as CDC consumer
    participant N as Node (owner + replica)
    participant A as Reader app
    B->>DB: UPDATE k = v2 (commit)
    Note over B: crashes before delete(k)
    A->>N: get(k) [t = 100 ms]
    N-->>A: v1 (stale)
    DB-->>CDC: binlog: k changed [t = 300 ms]
    CDC->>N: delete(k) to owner and replica [t = 500 ms]
    A->>N: get(k) [t = 600 ms]
    N-->>A: miss + lease
    A->>DB: SELECT k -> v2
    A->>N: set(k, v2, lease)
    Note over A,N: stale window 500 ms. If CDC is down: until TTL, and an alert fires at 5 s of lag
```

## D8. Node lifecycle

```mermaid
%% D8: a node's state in the config service. Only UP and DRAINING serve owner reads; WARMING serves nothing until its replica stream is done.
stateDiagram-v2
    [*] --> JOINING: AddNode, first heartbeat
    JOINING --> WARMING: replica stream from ring neighbour started
    WARMING --> UP: stream done, weight ramps 10% per minute to 100%
    UP --> SUSPECT: clients report 3 timeouts, or 1 heartbeat missed
    SUSPECT --> UP: heartbeat resumes within 3 s
    SUSPECT --> DEAD: 3 heartbeats missed (3 s)
    DEAD --> JOINING: node returns after 30 s cooldown (flap guard)
    UP --> DRAINING: operator drain, replica serves its range
    DRAINING --> WARMING: restart, stream back from replica
    DRAINING --> REMOVED: operator remove, epoch+1 without it
    DEAD --> REMOVED: not back within 10 min, epoch+1, new replica streamed
    REMOVED --> [*]
```

## D9. Deployment / topology

```mermaid
%% D9: one region, three AZs. Owner and replica of a range are never in the same AZ. The config service spans AZs. The DB and CDC are per region.
flowchart TB
    subgraph REGION[Region us-east, 400 cache nodes]
        subgraph AZ1[AZ 1]
            A1[Apps 1,700] --> C1[Cache nodes 1..133<br/>owners + replicas of AZ2 ranges]
            CFG1[Config member]
        end
        subgraph AZ2[AZ 2]
            A2[Apps 1,700] --> C2[Cache nodes 134..266<br/>replicas of AZ3 ranges]
            CFG2[Config leader]
        end
        subgraph AZ3[AZ 3]
            A3[Apps 1,600] --> C3[Cache nodes 267..400<br/>replicas of AZ1 ranges]
            CFG3[Config member]
        end
        C1 -.->|"async replica stream"| C3
        C2 -.->|"async"| C1
        C3 -.->|"async"| C2
        DB[(Database primary + replicas)] --> CDC[CDC consumer x3]
        CDC --> C1
        CDC --> C2
        CDC --> C3
    end
    A1 -->|"cross-AZ get, +300 us"| C2

    class A1,A2,A3 client
    class C1,C2,C3 cache
    class CFG1,CFG2,CFG3,DB store
    class CDC service

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef cache    fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#111
```

Apps read from whichever AZ owns the key (two thirds of reads cross an AZ, about 300 us extra). Netflix's alternative is a full copy per AZ with AZ-local reads, at 3x memory. We take the latency; a Google L6 interviewer may push for the Netflix layout when the AZ link is the bottleneck.

## D10. Scaling / partitioning: the ring and the hot key

```mermaid
%% D10: keys spread by the ring; one hot key still lands on one node (red). The fixes sit in the client.
flowchart LR
    K1[key a] -->|"hash"| RING((Ring, 30,000 points<br/>150 per node))
    K2[key b] -->|"hash"| RING
    HOT[hot key, 1 M QPS] -->|"hash"| RING
    RING --> N1[Node 1<br/>2.5 M keys, 25k QPS]
    RING --> N2[Node 2 ... 400]
    RING --> N17[Node 17<br/>2.5 M keys + 1 M QPS<br/>NIC 8 Gbps, CPU 100%]
    HOT -.->|"fix 1: client L1 1 s<br/>1 M -> 5k QPS"| L1[L1 in 5,000 clients]
    HOT -.->|"fix 2: key#0..7<br/>125k QPS each"| N2

    class K1,K2,HOT,L1 client
    class RING service
    class N1,N2 cache
    class N17 critical

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef cache    fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
```

## D11. Failure mode map

```mermaid
%% D11: each component, what fails, blast radius, mitigation. The DB is the only thing whose failure is not contained by the design.
flowchart TD
    N[Cache node dies] --> N1[0.25% of keys, replica serves<br/>DB +0 with RF 2, +25k/s without]
    N1 --> N2[Mitigation: replica, gutter, fill cap]
    R[Rack / AZ dies: 133 nodes] --> R1[33% of keys move to replicas in other AZs<br/>cross-AZ latency for all]
    R1 --> R2[Mitigation: rack-aware replica placement, 50% memory headroom]
    CFG[Config service down] --> CFG1[No ring changes, no hot-key updates<br/>data path unaffected]
    CFG1 --> CFG2[Mitigation: clients keep ring forever, Raft 3 to 5]
    CDC[CDC lag or down] --> CDC1[Staleness bound 1 s -> TTL for lost app deletes]
    CDC1 --> CDC2[Mitigation: alert at 5 s, app delete still 99.99% effective]
    CL[Client library bug] --> CL1[Fleet-wide mis-routing = cold cache]
    CL1 --> CL2[Mitigation: 1% canary watching own hit rate]
    DB[Database slow or down] --> DB1[Misses become errors, 5% of traffic<br/>fills pile up]
    DB1 --> DB2[Mitigation: fill cap, stale-while-revalidate, lease 10 s]

    class N,R,CFG,CDC,CL service
    class DB critical
    class N1,R1,CFG1,CDC1,CL1,DB1 decision
    class N2,R2,CFG2,CDC2,CL2,DB2 client

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
```

## D12. Rollout / migration from "memcached with mod N in app config"

```mermaid
%% D12: four phases, each behind a client flag. Rollback at any phase is a flag flip; the old cluster stays warm because nothing deletes from it until phase 2 ends.
gantt
    title Migration from static mod-N memcached to this design
    dateFormat  YYYY-MM-DD
    axisFormat  %b %d
    section Phase 1 config service
    Deploy Raft config service, publish static list as epoch 1     :p1, 2026-10-01, 7d
    Clients read ring from config, same mod-N hash (no change)     :p1b, after p1, 7d
    section Phase 2 ring hashing
    Client flag ring_hash on 1% canary, dual-read old owner on miss :p2, after p1b, 7d
    Ramp to 100%, keep dual-read for one max TTL                   :p2b, after p2, 30d
    Drop dual-read, decommission old static list                   :p2c, after p2b, 3d
    section Phase 3 leases and CDC
    Node build with leases and stale-keep, additive                :p3, after p2, 14d
    CDC consumer issuing deletes, shadow then live                 :p3b, after p3, 14d
    section Phase 4 replication
    Add replica pool, stream, rack-aware placement, pool by pool   :p4, after p3b, 21d
    Enable replica reads on suspect owner                          :p4b, after p4, 7d
```

Rollback points: phase 1 (clients fall back to the static list), phase 2 (flag off, old owners still warm), phase 3 (node build without leases still speaks the protocol; CDC consumer can be stopped, app deletes continue), phase 4 (replica reads off, replicas idle).
