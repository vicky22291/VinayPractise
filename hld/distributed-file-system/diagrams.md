# Diagrams: strongly consistent distributed file system

The D1 to D12 set from `hld/CLAUDE.md` §4. Diagrams already embedded in [`solution.md`](solution.md) are linked, not pasted twice. Colors per root `CLAUDE.md` §3. Red is only for the thing that breaks first.

| # | Diagram | Where |
|---|---|---|
| D1 | Context | below |
| D2 | Data flow | below |
| D3 | Component architecture | [`solution.md` §6](solution.md#6-final-design) |
| D4 | Happy path per FR (4 sequences) | 4.1 and 4.2 and 4.4 in `solution.md`, 4.3 below |
| D5 | Failure paths (3 sequences) | 2 in [`solution.md` §10.4](solution.md#104-failure-timelines), duplicate-append below |
| D6 | Decision flow: write path with seal-and-move | below |
| D7 | Entity relationship | [`solution.md` §3.3](solution.md#33-data-model) |
| D8 | State machines: chunk, file, rename txn | below |
| D9 | Deployment topology | below |
| D10 | Scaling and partitioning | [`solution.md` §5.2](solution.md#52-how-does-metadata-scale-to-10-b-files-and-500-k-opss-and-what-about-a-hot-directory) |
| D11 | Failure mode map | below |
| D12 | Migration off HDFS | below |

---

## D1. Context

Our system is one box. Everything around it and what flows on each edge.

```mermaid
%% D1: the file system in its environment
flowchart LR
    J[Spark / Photon jobs<br/>via client lib] -- "read 1 TB/s, write 200 GB/s<br/>create / rename / list" --> FS[Distributed file system<br/>metadata + chunk servers]
    N[Notebooks, services<br/>via client lib] -- "small reads, stat, list" --> FS
    OPS[Operators, SRE] -- "drain node, quota,<br/>snapshot, restore" --> FS
    FS -- "async raft log + sealed chunks" --> DR[Standby DC]
    FS -- "metrics, traces" --> MON[Monitoring]
    KMS[KMS] -- "per-tenant keys" --> FS
    ID[Identity / mTLS CA] -- "client identity" --> FS
    HDFS[Legacy HDFS<br/>during migration] -. "mirrored edits,<br/>block copy" .-> FS

    class J,N,OPS client
    class FS service
    class DR,MON,KMS,ID,HDFS external

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

## D2. Data flow

Inputs to outputs, with data name, size, rate on each edge.

```mermaid
%% D2: what flows where, with sizes and rates
flowchart LR
    C([Client library]) -- "lookup / stat<br/>~200 B req, 500 k/s" --> NS[(Namespace shards<br/>dentry, inode)]
    C -- "create / rename / delete<br/>~300 B, 55 k/s" --> NS
    C -- "allocate / seal chunk<br/>~200 B, 5 k/s" --> CK[(Chunk shards<br/>chunk map)]
    C -- "append, 4 MB frames<br/>200 GB/s total" --> HEAD([Head replica])
    HEAD -- "chain forward<br/>400 GB/s total" --> MID([Mid, Tail])
    C -- "read, 64 KB to 4 MB<br/>1 TB/s total" --> ANY([Any replica])
    ANY -- "heartbeat: chunk_id, version, len<br/>~100 KB delta, every 3 s per node" --> CK
    CK -- "replicate_from / encode / delete<br/>~100 B cmd, up to 600 GB/s data" --> REP([Repair, EC, GC workers])
    REP -- "fragment writes 6.4 MB" --> ANY
    NS -- "raft log, ~50 MB/s" --> DRS[(Standby DC shards)]
    ANY -- "sealed chunks, ~70 GB/s" --> DRC[(Standby DC chunks)]

    class C client
    class NS,CK store
    class HEAD,MID,ANY store
    class REP service
    class DRS,DRC external

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

## D4. Happy path: read (FR 3)

The other FR sequences (path resolution, append, rename) are in `solution.md` §4.1, §4.2, §4.4.

```mermaid
%% D4c: read a byte range, sealed and open chunks, CRC check, failover
sequenceDiagram
    autonumber
    participant C as Client lib
    participant M as MDS inode shard
    participant R1 as Replica A (same rack)
    participant R2 as Replica B
    participant H as Head of open chunk
    C->>M: open(/a/f, READ)
    M-->>C: inode: chunks [91 v2 sealed 64M, 92 v1 open], capability token
    C->>R1: read(91, v2, off 0, 4 MB, token)
    R1-->>C: bytes + CRC32C per 64 KB
    C->>C: verify CRC, ok
    C->>H: committed_len(92)
    H-->>C: 8M
    C->>R1: read(92, v1, off 0, 8M)
    R1--xC: timeout 2x p50
    C->>R2: hedged read(92, v1, off 0, 8M)
    R2-->>C: bytes, CRC ok
    C->>M: report_slow(R1) [async, best effort]
```

## D5. Failure path: duplicate append after lost ack

Timelines for "leader dies after ack" and "chunk server dies mid-append" are in `solution.md` §10.4.

```mermaid
%% D5c: ack lost on the wire. Retry must not duplicate bytes.
sequenceDiagram
    autonumber
    participant C as Client lib
    participant H as Head
    participant Mi as Mid
    participant T as Tail
    C->>H: write(91, v1, epoch 7, off 4M, 4 MB)
    H->>Mi: forward
    Mi->>T: forward
    T-->>Mi: ack
    Mi-->>H: ack, committed_len 8M
    H--xC: ack lost (network)
    Note over C: t+2 s timeout, retry same offset
    C->>H: write(91, v1, epoch 7, off 4M, 4 MB)
    H-->>C: OFFSET_ALREADY_COMMITTED, committed_len 8M
    Note over C: advance to off 8M, no seal needed
```

## D6. Decision flow: the write path

Branching logic inside the client library's append loop, the hardest piece of client code.

```mermaid
%% D6: append decision tree, seal-and-move on any failure
flowchart TD
    A[append 4 MB at offset X] --> B{"lease valid?<br/>renewed under 40 s ago"}
    B -- no --> B1[renew_lease] --> B2{renewed?}
    B2 -- no, FENCED --> Z[fail: reopen file]:::critical
    B2 -- yes --> C
    B -- yes --> C{open chunk has<br/>room for 4 MB?}
    C -- no --> C1[seal current at committed_len<br/>allocate_chunk] --> D
    C -- yes --> D[write to head with<br/>chunk_id, version, epoch, crc]
    D --> E{ack within 2 s?}
    E -- yes --> F[committed_len = X + 4M<br/>next]
    E -- OFFSET_ALREADY_COMMITTED --> F
    E -- timeout or replica error --> G[seal_chunk at MDS<br/>MDS truncates to agreed len]
    G --> H[allocate new chunk<br/>rewrite bytes from committed_len]
    H --> D
    E -- STALE_VERSION --> I[refresh chunk from MDS] --> D

    class A,D,F,C1,G,H,I,B1 service
    class B,B2,C,E decision
    class Z critical

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
```

## D8. State machines

### D8a. Chunk lifecycle

```mermaid
%% D8a: a chunk is written once, sealed once, encoded at most once, then deleted
stateDiagram-v2
    [*] --> Allocated: MDS allocate, version 1, chain chosen
    Allocated --> Open: first write acked
    Open --> Sealed: close, or full, or any replica failure (truncate to agreed len)
    Open --> Sealed: lease expiry recovery
    Sealed --> UnderReplicated: replica lost (heartbeat gap or scrub CRC fail)
    UnderReplicated --> Sealed: replicate_from done, version bumped
    Sealed --> Encoded: cold 7 days, RS(10,4) written, replicas deleted
    Encoded --> Degraded: fragment lost
    Degraded --> Encoded: fragment rebuilt from 10 others
    Sealed --> Deleted: inode GC after 24 h grace
    Encoded --> Deleted: inode GC
    Deleted --> [*]
```

### D8b. File (inode) lifecycle

```mermaid
%% D8b: inode states. Only one writer via lease.
stateDiagram-v2
    [*] --> Creating: create() committed in Raft
    Creating --> OpenForWrite: lease granted (epoch E)
    OpenForWrite --> OpenForWrite: append, renew every 20 s
    OpenForWrite --> Closed: close(), tail chunk sealed, lease released
    OpenForWrite --> Recovering: lease expired 60 s, no renew
    Recovering --> Closed: MDS bumps epoch E+1, seals tail chunk
    Closed --> OpenForWrite: open(APPEND), new lease epoch
    Closed --> Orphan: dentry unlinked (delete or rename over)
    Orphan --> [*]: GC after 24 h, chunks deleted
```

### D8c. Cross-shard rename transaction

```mermaid
%% D8c: 2PC record on the coordinator shard
stateDiagram-v2
    [*] --> Prepared: coordinator Raft: TXN + intent on src
    Prepared --> Committed: participant prepared, coordinator Raft: COMMITTED
    Prepared --> Aborted: participant refuses (dst exists, dst parent DELETING, cycle) or timeout 30 s
    Committed --> Done: participant applied intent, both intents cleared
    Aborted --> Done: src intent cleared
    Done --> [*]: txn record GC after 1 h
```

## D9. Deployment topology

```mermaid
%% D9: one primary DC with 3 power domains, one standby DC. Nothing on the sync path crosses a DC.
flowchart TB
    subgraph DC1 [Primary DC]
        subgraph PD1 [Power domain A, racks 1-40]
            R1[Raft replica 1<br/>of every shard]
            CS1[~1,700 chunk servers]
        end
        subgraph PD2 [Power domain B, racks 41-80]
            R2[Raft replica 2]
            CS2[~1,700 chunk servers]
        end
        subgraph PD3 [Power domain C, racks 81-120]
            R3[Raft replica 3]
            CS3[~1,600 chunk servers]
        end
        R1 <-- "raft, <1 ms" --> R2
        R2 <-- "raft" --> R3
        CS1 -- "chain replica 1 of 3" --> CS2
        CS2 -- "chain replica 2 of 3" --> CS3
    end
    subgraph DC2 [Standby DC, 2 ms to 80 ms away]
        SR[Shard log receivers]
        SC[Chunk copy receivers]
        W[Witness for optional<br/>stretched shards]
    end
    R1 -. "async raft log" .-> SR
    CS1 -. "async sealed chunks" .-> SC
    R1 -. "votes only, opt-in shards" .-> W

    class R1,R2,R3 service
    class CS1,CS2,CS3 store
    class SR,SC,W external

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

## D11. Failure mode map

```mermaid
%% D11: component -> what fails -> blast radius -> mitigation
flowchart TD
    M[Metadata shard] --> M1[leader dies] --> M1b[0.5% of files, 2 s] --> M1c[Raft election, client retry with request id]
    M --> M2[disk corruption] --> M2b[one shard] --> M2c[restore checkpoint + replay log, followers still serve]
    RT[Root shard] --> RT1[leader dies] --> RT1b[all cache-miss lookups, 2 s]:::critical --> RT1c[client cache absorbs, election]
    CS[Chunk server] --> CS1[node dies] --> CS1b[none for users] --> CS1c[read other replica, seal-and-move, repair 3 min]
    CS --> CS2[bit rot] --> CS2b[one replica] --> CS2c[CRC on read + scrub, re-replicate]
    RK[Rack or power domain] --> RK1[loss] --> RK1b[2% of nodes, 2 PB repair, 1 h] --> RK1c[3 domains per chunk, repair budget]
    NET[Network partition] --> NET1[leader isolated] --> NET1b[stale leader]:::critical --> NET1c[lease expiry + term fencing]
    CL[Client library] --> CL1[bad release] --> CL1b[every caller]:::critical --> CL1c[prefix-gated rollout, server rejects unknown versions]
    DC[Datacenter] --> DC1[loss] --> DC1b[everything, RPO 15 min] --> DC1c[promote standby, runbook RTO 1 h]

    class M,RT,CS,RK,NET,CL,DC service
    class M1,M2,RT1,CS1,CS2,RK1,NET1,CL1,DC1 decision
    class M1c,M2c,RT1c,CS1c,CS2c,RK1c,NET1c,CL1c,DC1c store
    class RT1b,NET1b,CL1b critical

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
```

## D12. Migration off HDFS

Each phase has a rollback point. No phase needs downtime.

```mermaid
%% D12: HDFS to new file system, per-directory cutover
gantt
    title Migration from HDFS, rollback point at the end of every phase
    dateFormat  YYYY-MM
    axisFormat  %Y-%m
    section Phase 1 shadow
    Metadata service in shadow, mirror NameNode edits   :p1, 2027-01, 2M
    Nightly listing diff, fix divergences                :p1b, after p1, 1M
    section Phase 2 dual write
    Chunk servers deployed, /tmp writes to new system    :p2, after p1b, 2M
    Rollback point, flip router to HDFS for /tmp         :milestone, after p2, 0d
    section Phase 3 cutover
    Per-directory router flips, low risk first           :p3, after p2, 4M
    Cold block copy HDFS -> chunks, checksum verified     :p3b, after p2, 5M
    section Phase 4 decommission
    HDFS read-only, final diff                           :p4, after p3b, 1M
    HDFS decommissioned                                  :milestone, after p4, 0d
```
