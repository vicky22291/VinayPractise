# Diagrams: in-memory KV store with WAL

The D1 to D12 set for [`solution.md`](solution.md). Each diagram appears once in the repo: the ones embedded in `solution.md` are linked from here, not repeated. Colors per root `CLAUDE.md` §3. Red is used only for the fsync on the write path (the thing that breaks first) and for the halted-shard state.

Legend reminder: 🔵 client / edge, 🟢 stateless compute or threads, 🟣 durable storage, 🟡 cache or losable, 🔷 queue, 🔴 bottleneck or SPOF, ⚪ external, 🩷 decision.

---

## D1. Context (zoom-out)

What is inside the box and what talks to it. The store is one thing to its callers; replication and slot ownership are internal.

```mermaid
%% D1: context. Clients see one KV API; everything else is inside our trust boundary.
flowchart LR
    APP[Application services<br/>via client library] -->|"get/put/del/cas, ~1 M ops/s"| KV[KV store cluster<br/>N nodes x 16 shards]
    ADM[Operators / deploy tooling] -->|"checkpoint, migrate slot, drain"| KV
    KV -->|"slot map reads, epoch bumps"| CFG[(Config service<br/>Raft, tiny)]
    KV -->|"metrics, logs"| OBS[Observability]
    KV -->|"encrypted snapshots, optional"| OBJ[Object store<br/>off-node backup]
    KMS[KMS] -->|"per-node data key"| KV

    class APP,ADM client
    class KV service
    class CFG store
    class OBS,OBJ,KMS external

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

## D2. Data flow (DFD)

Bytes in, bytes on disk, bytes back. Sizes and rates are peak for one node.

```mermaid
%% D2: data flow for one node. Every edge says what flows, how big, how often.
flowchart LR
    C[Client] -->|"put: key 32 B + value 200 B, 200 k/s"| IO(I/O threads<br/>parse + route)
    IO -->|"request struct, 1 per op"| SH(Shard thread x16<br/>apply to map)
    SH -->|"WAL record ~250 B, 50 MB/s total"| LB(Log buffer<br/>2 x 4 MB per shard)
    LB -->|"write + fdatasync, 4 MB max per group"| WAL[(WAL segments<br/>256 MB each)]
    SH -->|"entry versions, 3.75 GB per shard, every 10 min"| SN(Snapshot thread)
    SN -->|"snap-lsn.bin + manifest"| SNAP[(Snapshots<br/>2 retained)]
    WAL -->|"records with lsn > snap_lsn, on restart"| SH
    SNAP -->|"full map, on restart"| SH
    SH -->|"get: value 200 B, 800 k/s"| C
    LB -->|"AppendEntries batch, 50 MB/s x 2"| REP(Followers on other nodes)

    class C client
    class IO,SH,SN,REP service
    class LB queue
    class WAL,SNAP store

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
```

## D3. Component architecture

Embedded as the final design in [`solution.md` §6](solution.md#6-final-design). Not repeated here.

## D4. Sequence, happy path, one per FR

- D4a `get`: [`solution.md` §4.1](solution.md#41-serve-put-get-delete-from-memory-at-1-m-opss).
- D4b `put` with group commit and watermark: [`solution.md` §4.2](solution.md#42-make-an-acknowledged-write-survive-a-crash).
- D4c snapshot and truncation: [`solution.md` §4.3](solution.md#43-restart-recovers-on-its-own-in-bounded-time).
- D4d `cas` on a key with an unacked write in flight, below.

```mermaid
%% D4d: cas evaluates against the newest in-memory version, even an unacked one, because the shard thread is the single writer.
sequenceDiagram
    autonumber
    participant A as Client A
    participant B as Client B
    participant S as Shard thread
    participant L as Log writer
    A->>S: put(k, v1) -> lsn 10 (applied, hidden, in batch 1)
    B->>S: cas(k, expected=v1, v2)
    S->>S: newest version of k is v1 @10 -> match
    S->>S: lsn 11 = CAS_RESULT k v2, applied hidden, pending
    L-->>S: batch 1 durable (lsn <= 10)
    S-->>A: OK(10)
    L-->>S: batch 2 durable (lsn <= 11)
    S-->>B: OK(11)
    Note over S: If batch 1 had failed, the process halts and both 10 and 11 vanish together. Never 11 without 10.
```

## D5. Sequence, failure paths

- D5a process crash mid-batch: [`solution.md` §10.4](solution.md#104-failure-timeline).
- D5b Raft commit with a slow follower: [`solution.md` §5.4](solution.md#54-the-machine-dies-make-the-ack-mean-the-write-survives-that-now-stop-the-old-primary-from-acking-after-failover).
- D5c fsync returns EIO, below.
- D5d leader partitioned, old leader fenced, below.

```mermaid
%% D5c: fdatasync fails once. Retrying would lie (kernel already dropped the pages). Halt and recover.
sequenceDiagram
    autonumber
    participant C as Client
    participant S as Shard 3
    participant L as Log writer 3
    participant D as NVMe
    participant P as Process
    C->>S: put(k, v) -> lsn 900 applied hidden
    L->>D: write(batch 895-900), fdatasync()
    D-->>L: EIO
    L->>S: halt(shard 3)
    S->>S: stop acking, reads still served from durable versions (<= 894)
    S->>P: fatal("fsync EIO shard 3")
    P->>P: exit(1). Raft followers elect new leaders for all 16 groups in ~1 to 2 s
    Note over C: times out on lsn 900, retries with request_id on the new leader
    Note over D: on-call page: disk_errors > 0 on this node, drain and replace
```

```mermaid
%% D5d: old leader partitioned away. Terms fence it; it can apply locally but never commit or ack.
sequenceDiagram
    autonumber
    participant C as Client
    participant OL as Old leader (term 7)
    participant F1 as Follower 1
    participant F2 as Follower 2
    Note over OL,F2: partition: OL cannot reach F1, F2
    F1->>F1: election timeout 1 s -> candidate term 8
    F1->>F2: RequestVote(term 8)
    F2-->>F1: granted
    Note over F1: leader term 8
    C->>OL: put(k, v)
    OL->>OL: append(term 7, lsn 501), needs majority
    OL--xF1: AppendEntries(term 7) unreachable
    Note over OL: no majority, never commits, never acks. Client times out.
    C->>F1: retry put(k, v) with request_id
    F1->>F2: AppendEntries(term 8, lsn 501)
    F2-->>F1: fsynced
    F1-->>C: OK
    Note over OL: partition heals: sees term 8, steps down, truncates its uncommitted 501, catches up
```

## D6. Activity / decision flow

Embedded in [`solution.md` §4.4](solution.md#44-per-key-linearizability-with-concurrent-clients-and-atomic-ops): the shard thread's per-request decision including the watermark check and the EIO branch. Recovery decision flow below.

```mermaid
%% D6b: recovery of one shard on restart. The two red exits are the only cases that need a human.
flowchart TD
    A[read manifest] --> B{manifest valid?}
    B -->|no| B2{previous manifest valid?}
    B2 -->|yes| C
    B2 -->|no| X1[refuse to start<br/>bootstrap from Raft peer]
    B -->|yes| C[load snap-snap_lsn.bin]
    C --> D{footer checksum ok?}
    D -->|no| B2
    D -->|yes| E[open first segment with last_lsn > snap_lsn]
    E --> F[read next record]
    F --> G{crc ok and<br/>length fits?}
    G -->|yes| H{lsn <= snap_lsn?}
    H -->|yes| F
    H -->|no| I[apply: PUT/DEL/CAS_RESULT/EXPIRE] --> F
    G -->|no, at tail of last segment| J[truncate here<br/>durable_lsn = last good]
    G -->|no, mid-log| X2[refuse to start<br/>corruption, bootstrap from peer]
    J --> K[serve]

    class A,C,E,F,I,J,K service
    class B,B2,D,G,H decision
    class X1,X2 critical

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
```

## D7. Entity relationship

Embedded in [`solution.md` §3.3](solution.md#33-data-model).

## D8. State machines

Two entities have lifecycles: a shard (leader / follower / halted / recovering) and a slot during migration.

```mermaid
%% D8a: shard lifecycle on one node. Halted is red because it is the state that pages someone.
stateDiagram-v2
    [*] --> Recovering: process start
    Recovering --> Follower: snapshot + log replayed
    Follower --> Candidate: election timeout
    Candidate --> Leader: majority votes
    Candidate --> Follower: higher term seen
    Leader --> Follower: higher term seen / lease lost
    Leader --> Halted: fdatasync EIO / disk full
    Follower --> Halted: fdatasync EIO / disk full
    Halted --> [*]: process exits, restart -> Recovering
    Recovering --> Halted: mid-log corruption
```

```mermaid
%% D8b: slot migration. Cutover happens at one LSN so no write is lost or applied twice.
stateDiagram-v2
    [*] --> Stable: owned by source
    Stable --> Migrating: admin migrate_slot(slot, target)
    Migrating --> Importing: target accepts snapshot of slot
    Importing --> Handover: source stops writes to slot at lsn X, ships tail <= X
    Handover --> Stable: config service records new owner, epoch++
    Migrating --> Stable: abort, target discards
    Importing --> Stable: abort, target discards
    note right of Migrating
        reads and writes still at source
        moved keys answer ASK -> client retries at target
    end note
```

## D9. Deployment / topology

Three nodes, 16 shards each as Raft groups, leaders spread evenly so each node leads ~16 groups of the 48. Rack-aware so no rack holds a majority of any group.

```mermaid
%% D9: 3 racks, 3 nodes, every shard group has one member per rack. Leaders are spread.
flowchart TB
    subgraph R1[Rack A]
        N1[Node 1<br/>L: shards 0-5<br/>F: 6-15]
        D1[(NVMe x2)]
        N1 --> D1
    end
    subgraph R2[Rack B]
        N2[Node 2<br/>L: shards 6-10<br/>F: rest]
        D2[(NVMe x2)]
        N2 --> D2
    end
    subgraph R3[Rack C]
        N3[Node 3<br/>L: shards 11-15<br/>F: rest]
        D3[(NVMe x2)]
        N3 --> D3
    end
    N1 <-->|"AppendEntries + heartbeats<br/>batched per node pair"| N2
    N2 <-->|"same"| N3
    N1 <-->|"same"| N3
    CFG[(Config service<br/>3 members, one per rack)] -.->|"slot map, epochs"| N1
    CFG -.-> N2
    CFG -.-> N3

    class N1,N2,N3 service
    class D1,D2,D3,CFG store

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
```

Crossing a rack boundary: every Raft append (50 MB/s per leader shard), snapshot transfer to a lagging follower (3.75 GB burst), and `MOVED` redirects. Nothing crosses a region boundary in this design; multi-region is async log shipping (§10.11).

## D10. Scaling / partitioning

Keys hash into 16,384 slots. Slots map to shard groups. A hot slot is red; the fixes are next to it.

```mermaid
%% D10: two-level placement. Slot -> shard group is the unit that moves; key -> slot never changes.
flowchart LR
    K[key] -->|"crc16 mod 16384"| SL[slot 0..16383]
    SL -->|"slot map, cached in client"| G0[Shard group 0<br/>slots 0-1023]
    SL --> G1[Shard group 1<br/>slots 1024-2047]
    SL --> GH[Shard group 7<br/>slots 7168-8191<br/>HOT: key k* = 30% of reads]
    SL --> GN[Shard group 15]
    GH -->|"fix 1: client cache, 100 ms TTL"| F1[reads absorbed at client]
    GH -->|"fix 2: follower reads with read index"| F2[3x read capacity]
    GH -->|"fix 3: split write-hot counter k#0..15"| F3[16 shards share writes]

    class K client
    class SL decision
    class G0,G1,GN service
    class GH critical
    class F1 cache
    class F2,F3 service

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef cache    fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

## D11. Failure mode map

```mermaid
%% D11: what fails, who feels it, what stops it. Only the correlated fsync lie is red: it is the one that loses acked data.
flowchart TD
    A[Component fails] --> B[Shard thread panics]
    A --> C[NVMe EIO or full]
    A --> D[Node lost]
    A --> E[Snapshot thread stuck]
    A --> F[Config service down]
    A --> G[All 3 replicas lose power,<br/>consumer drives lie about flush]
    B --> B1[blast: 1/16 of keys on this node<br/>fix: process restart, Raft failover 1 to 2 s]
    C --> C1[blast: this node stops acking<br/>fix: halt, exit, followers lead]
    D --> D1[blast: 16 groups elect, ~2 s writes paused<br/>fix: Raft majority elsewhere]
    E --> E1[blast: log grows, restart time grows<br/>fix: abort walk at cap, alert]
    F --> F1[blast: no slot moves<br/>fix: clients keep cached map]
    G --> G1[blast: acked writes lost<br/>fix: PLP drives, rack-aware placement]

    class A decision
    class B,C,D,E,F service
    class B1,C1,D1,E1,F1 service
    class G,G1 critical

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

## D12. Rollout / migration

From "Redis with AOF everysec and async replicas" to this store, with a rollback point per phase.

```mermaid
%% D12: migration from Redis. Each phase ends where the previous system is still authoritative until the flip.
gantt
    title Migration from Redis (AOF everysec) to the WAL store
    dateFormat  YYYY-MM-DD
    axisFormat  %b %d
    section Phase 1 shadow
    New store as Redis replica (consumes RDB + stream into WAL)   :p1, 2026-10-01, 14d
    Rollback = stop replica, nothing changed                       :milestone, m1, 2026-10-15, 0d
    section Phase 2 dual read
    Client lib reads both, compares, reports mismatches           :p2, 2026-10-15, 14d
    Rollback = disable compare flag                                :milestone, m2, 2026-10-29, 0d
    section Phase 3 flip writes
    Writes to new store, Redis becomes follower of new WAL        :p3, 2026-10-29, 7d
    Rollback = flip slot map back within 5 min window              :milestone, m3, 2026-11-05, 0d
    section Phase 4 retire
    Stop Redis follower, keep last RDB 30 days                    :p4, 2026-11-05, 7d
```
