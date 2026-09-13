# Diagrams: immutable distributed object store

The D1 to D12 set from `hld/CLAUDE.md` §4. Diagrams already embedded in [`solution.md`](solution.md) are linked, not pasted twice. Colors per root `CLAUDE.md` §3. Red is only for the thing that breaks first.

| # | Diagram | Where |
|---|---|---|
| D1 | Context | below |
| D2 | Data flow | below |
| D3 | Component architecture | [`solution.md` §6](solution.md#6-final-design) |
| D4 | Happy path per FR (5 sequences) | PUT and conditional PUT in `solution.md` §4.1 and §4.5; GET, DELETE, LIST below |
| D5 | Failure paths (3 sequences) | 2 in [`solution.md` §10.4](solution.md#104-failure-timelines); duplicate PUT after lost ack below |
| D6 | Decision flow: the write path | below |
| D7 | Entity relationship | [`solution.md` §3.3](solution.md#33-data-model) |
| D8 | State machines: volume, object version, multipart upload | below |
| D9 | Deployment topology | below |
| D10 | Scaling and partitioning | [`solution.md` §5.2](solution.md#52-a-spark-job-writes-10000-files-a-second-into-one-prefix-and-a-million-readers-hit-_delta_log-what-melts) |
| D11 | Failure mode map | below |
| D12 | Migration off S3 | below |

---

## D1. Context

Our system is one box. Everything around it and what flows on each edge.

```mermaid
%% D1: the object store in its environment
flowchart LR
    SP[Spark / Photon jobs<br/>S3 SDK] -- "PUT part files 200 GB/s,<br/>GET row groups 1 TB/s, LIST" --> OS[Immutable object store<br/>gateways + metadata + storage]
    DL[Delta / Iceberg commit protocol] -- "put-if-absent on _delta_log/N.json,<br/>GET _last_checkpoint" --> OS
    NB[Notebooks, services, users] -- "small PUT / GET, presigned URLs" --> OS
    OPS[Operators, SRE] -- "drain node, quota, lifecycle,<br/>bucket policy" --> OS
    OS -- "async copy of records + bytes" --> DR[Second region]
    OS -- "metrics, traces, audit log" --> MON[Monitoring + audit]
    KMS[KMS] -- "per-bucket KEK wrap / unwrap" --> OS
    ID[Identity: keys, bucket policies] -- "SigV4 auth" --> OS
    S3[Legacy S3 buckets<br/>during migration] -. "dual write, fallback read,<br/>bulk copy" .-> OS

    class SP,DL,NB,OPS client
    class OS service
    class DR,MON,KMS,ID,S3 external

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

## D2. Data flow

Inputs to outputs, with data name, size, rate on each edge.

```mermaid
%% D2: what flows where, with sizes and rates at peak
flowchart LR
    C([Client]) -- "PUT body, 1 B to 5 TB<br/>50 k/s, 200 GB/s" --> G([Gateway])
    G -- "needle append, ~64 KB x 3 replicas<br/>35 k/s, 6.7 GB/s" --> R3[(REPL3 open volumes)]
    G -- "fragment append, 4 MB x 15<br/>15 k objects/s, 330 GB/s" --> EC[(EC96 volumes)]
    G -- "commit record ~400 B<br/>65 k/s incl. delete + mpu" --> OBJ[(Object shards)]
    G -- "witness call ~50 B<br/>500 k/s" --> OBJ
    G -- "allocate / seal / lease ~200 B<br/>~100/s" --> VOL[(Volume shards)]
    C -- "GET, range<br/>500 k/s" --> G
    G -- "needle / fragment read<br/>64 KB to 4 MB, 1 TB/s" --> R3
    G -- "fragment read" --> EC
    G -- "body out, 1 TB/s" --> C
    R3 -- "sealed 1 GB extent<br/>23/s, 2.2 GB/s read" --> ENC([Encoder])
    ENC -- "15 fragments x 114 MB<br/>3.7 GB/s write" --> EC
    EC -- "9 fragments read per rebuild<br/>up to 60 MB/s per disk" --> REP([Repair])
    REP -- "rebuilt fragment" --> EC
    EC -- "live objects of a 30% garbage volume" --> CMP([Compactor])
    CMP -- "new volume + CAS record pointer" --> OBJ
    R3 -- "heartbeat: inventory, health, heat<br/>~50 KB per node per 3 s" --> VOL
    OBJ -- "garbage_bytes, heat<br/>async ~10 k/s" --> VOL

    class C client
    class G,ENC,REP,CMP service
    class R3,EC,OBJ,VOL store

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
```

## D4. Happy path: GET with range (FR 2)

```mermaid
%% D4: range GET of a Parquet row group. Witness check, cached record, one fragment read.
sequenceDiagram
    autonumber
    participant C as Client
    participant G as Gateway
    participant M as Object shard leader
    participant S as Storage node (fragment 3)
    C->>G: GET /b/k Range: bytes=40000000-44000000
    G->>G: record cache hit: k -> v7, seg (vol 4711, off 0, 260 MB), cached at LSN 9912
    G->>M: witness(k, since LSN 9912)?
    M-->>G: unchanged (k not in 60 s modified set)
    G->>G: row = 40 MB / 36 MB = 1, chunk = (40 MB mod 36 MB) / 4 MB -> fragment 1, offset 4 MB + 4 MB
    G->>G: content cache miss on (4711, frag 1, off 8 MB)
    G->>S: read(extent 4711/1, off 8 MB, len 4 MB)
    S-->>G: 4 MB + crc32c per 64 KB
    G->>G: verify crc, decrypt with DEK (unwrapped via cached KEK)
    G-->>C: 206 Partial Content, 4 MB, ETag v7
```

## D4. Happy path: DELETE (FR 3)

```mermaid
%% D4: delete on a versioned bucket. Delete marker committed, space reclaimed later by GC.
sequenceDiagram
    autonumber
    participant C as Client
    participant G as Gateway
    participant M as Object shard
    participant V as Volume shard
    participant GC as Compactor
    C->>G: DELETE /b/k
    G->>M: commit {k, delete marker v8, req 77}
    M->>M: Raft commit, apply: insert marker, witness(k) = LSN 9950, dedup(77)
    M-->>G: 204
    G-->>C: 204 No Content
    Note over M: later, lifecycle expires noncurrent v7 after 30 d
    M->>M: apply: remove v7 record (DEK gone)
    M-)V: garbage(vol 4711, v7, 260 MB) async, idempotent
    V->>V: vol 4711 garbage 31% > 30%: queue compaction
    GC->>V: rewrite live objects of 4711 into 4790, CAS records, mark 4711 DRAINING
    Note over V: 24 h later: delete 4711 extents on 15 disks
```

## D4. Happy path: LIST with delimiter (FR 4)

```mermaid
%% D4: list prefix with delimiter. One range shard, ordered iterator, seek past each common prefix.
sequenceDiagram
    autonumber
    participant C as Client
    participant G as Gateway
    participant M as Object shard 731 (range covers lake/table_x/)
    C->>G: GET /lake?list-type=2&prefix=table_x/&delimiter=/&max-keys=1000
    G->>G: shard map: [lake/table_x/, lake/table_x/0xFF) -> shard 731
    G->>M: scan(from lake/table_x/, limit 1000, delimiter /) leader-lease read at applied LSN 9950
    M->>M: iterator: _delta_log/ -> common prefix, seek to lake/table_x/_delta_log0
    M->>M: part-00000.parquet ... keys, skip delete markers
    M-->>G: 998 keys + 2 common prefixes, next cursor lake/table_x/part-00998
    G-->>C: 200 XML, IsTruncated=true, ContinuationToken
```

## D5. Failure path: duplicate PUT after a lost ack

```mermaid
%% D5: the ack is lost after commit. Retry hits the dedup table, no second version, no second write.
sequenceDiagram
    autonumber
    participant C as Client
    participant G1 as Gateway 1
    participant M as Object shard
    participant G2 as Gateway 2
    C->>G1: PUT /b/k, req 42, 9 KB
    G1->>M: commit {k, v3, seg (vol 90, o, 9 KB), req 42}
    M-->>G1: 200 v3
    G1--xC: ack lost (LB reset)
    C->>G2: retry PUT /b/k, req 42, 9 KB
    G2->>G2: write 9 KB to vol 91 (it cannot know req 42 already committed)
    G2->>M: commit {k, v?, seg (vol 91, o2, 9 KB), req 42}
    M->>M: apply: dedup hit for req 42 within 10 min -> return stored outcome
    M-->>G2: 200 v3 (original)
    G2-->>C: 200 v3
    Note over G2: 9 KB in vol 91 are orphan bytes, reconciler reclaims. One PUT, one version.
```

## D6. Decision flow: the write path

```mermaid
%% D6: what the gateway decides on every PUT. Decision nodes in pink; the one red node is the retry-into-a-failing-extent trap that the design forbids.
flowchart TD
    A[PUT arrives, checksum header present?] --> B{size known and < 8 MB?}
    B -- "yes" --> C[Append needle to open REPL3 volume<br/>3 extents, 1 per AZ, in parallel]
    B -- "no" --> D{size > 64 MB or multipart?}
    D -- "multipart" --> E[Each part: EC path below,<br/>part record under upload_id]
    D -- "no" --> F[Stream in 36 MB rows: crc32c per 4 MB,<br/>RS 9,6 encode, append to 15 extents]
    E --> F
    C --> G{all acks within 2 s?}
    F --> G
    G -- "yes" --> H{full-object checksum<br/>matches header?}
    G -- "no" --> I[Seal volume at last full row,<br/>allocate new volume, re-send unacked rows]
    I --> G
    X[Retry into the same extent]:::critical -.-x G
    H -- "no" --> J[400 BadDigest, no commit,<br/>bytes become orphans]
    H -- "yes" --> K{precondition on commit?}
    K -- "If-None-Match / If-Match" --> L[Commit entry carries precondition;<br/>evaluated at Raft apply]
    K -- "none" --> M[Commit record]
    L --> N{apply outcome}
    M --> O[200 version_id, etag]
    N -- "ok" --> O
    N -- "412" --> P[412 PreconditionFailed + current etag;<br/>bytes become orphans]

    class A,C,E,F,I,J,L,M,O,P service
    class B,D,G,H,K,N decision
    class X critical

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
```

## D8. State machines

Volume lifecycle. Every transition is one commit in the volume shard.

```mermaid
%% D8a: volume lifecycle. OPEN is the only mutable state; everything after SEALED is immutable content with changing layout.
stateDiagram-v2
    [*] --> OPEN: allocate(type, policy), lease to gateway, epoch 1
    OPEN --> SEALED: full (1 GB) / 1 h open / any fragment failure / lease expired
    SEALED --> ENCODED: REPL3 only: encoder writes 15 fragments, commits layout, deletes 3 replicas
    SEALED --> ENCODED: EC96: already encoded, immediate
    ENCODED --> DEGRADED: heartbeat or scrub reports a missing / bad fragment
    DEGRADED --> ENCODED: repair rebuilds fragment from 9 others
    ENCODED --> DRAINING: garbage > 30% or disk drain: compactor copies live objects out
    DRAINING --> DELETED: 24 h grace after last record CAS
    DEGRADED --> DRAINING: fewer than 9 fragments left (page) and compactor copies what it can
    DELETED --> [*]: extents removed, volume id retired for 30 d
```

Object version lifecycle.

```mermaid
%% D8b: object version. The record is created in one commit and only ever moves pointer or expires.
stateDiagram-v2
    [*] --> WRITING: bytes streaming into a volume, no record yet
    WRITING --> ORPHAN: gateway crash / 412 / bad digest: bytes without a record
    ORPHAN --> [*]: reconciler marks garbage
    WRITING --> CURRENT: record committed (precondition ok)
    CURRENT --> NONCURRENT: newer version committed on the same key
    CURRENT --> DELETE_MARKED: delete marker committed (versioned bucket)
    CURRENT --> [*]: delete on unversioned bucket: record removed, DEK gone
    NONCURRENT --> [*]: lifecycle noncurrent expiry: record removed, DEK gone
    DELETE_MARKED --> [*]: marker expiry
    CURRENT --> CURRENT: compactor CAS moves segment pointer to a new volume
```

Multipart upload.

```mermaid
%% D8c: multipart upload. Parts are invisible until complete; complete is one commit.
stateDiagram-v2
    [*] --> INITIATED: POST ?uploads -> upload_id
    INITIATED --> PARTS_IN_FLIGHT: PUT ?partNumber=n (each part an EC write + part record)
    PARTS_IN_FLIGHT --> PARTS_IN_FLIGHT: more parts, any order, retries replace a part
    PARTS_IN_FLIGHT --> COMPLETED: POST ?uploadId with part list: one commit inserts object record, deletes part records
    PARTS_IN_FLIGHT --> ABORTED: DELETE ?uploadId, or lifecycle after 7 d
    ABORTED --> [*]: part bytes become garbage
    COMPLETED --> [*]
```

## D9. Deployment topology

```mermaid
%% D9: one region, three AZs. Every Raft group has one replica per AZ; every EC volume has 5 fragments per AZ in 5 racks; every REPL3 volume has 1 replica per AZ.
flowchart TB
    LB[Anycast / L4 load balancer] --> GA & GB & GC
    subgraph AZA [AZ a]
        GA[Gateways x67]
        MA[Metadata nodes x100<br/>1 replica of each shard]
        SA[Storage x420, 30 racks<br/>5 fragments of every EC volume<br/>1 replica of every REPL3 volume]
    end
    subgraph AZB [AZ b]
        GB[Gateways x67]
        MB[Metadata nodes x100]
        SB[Storage x420, 30 racks]
    end
    subgraph AZC [AZ c]
        GC[Gateways x67]
        MC[Metadata nodes x100]
        SC[Storage x420, 30 racks]
    end
    MA <-- "Raft, ~1 ms" --> MB <-- "Raft" --> MC
    GA -- "appends / reads cross AZ<br/>2/3 of fragment traffic" --> SB & SC
    GA --> SA
    BG[Background workers<br/>encoder, repair, scrub, compactor, reconciler<br/>spread over all AZs] --> SA & SB & SC
    DR[Second region<br/>async copy, RPO minutes]
    MA -. "apply stream" .-> DR
    SA -. "bytes" .-> DR

    class LB,GA,GB,GC client
    class MA,MB,MC,SA,SB,SC store
    class BG service
    class DR external

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

What crosses an AZ boundary: two thirds of every fragment write and one third of REPL3 reads (the gateway prefers the AZ-local replica), Raft replication for every shard, repair traffic for cross-AZ rebuilds. Budget: at 330 GB/s of fragment writes, ~220 GB/s crosses AZ boundaries; inter-AZ bandwidth is provisioned at 1 TB/s.

## D11. Failure mode map

```mermaid
%% D11: component -> failure -> blast radius -> mitigation. The one red leaf is the data-loss path.
flowchart TD
    subgraph GW [Gateway]
        G1[Process dies mid-PUT] --> G1b[One client's PUT fails, retries<br/>orphan bytes] --> G1c[Lease expiry seals volume; reconciler GC]
        G2[Encoder bug writes wrong parity] --> G2b[Objects of that build unreadable in degraded mode] --> G2c[Client checksum re-verified on every read;<br/>CI decode-fuzz; canary 1%]
    end
    subgraph MD [Metadata shard]
        M1[Leader dies] --> M1b[One key range stalls 1 to 2 s] --> M1c[Raft election; request-id dedup on retry]
        M2[Hot monotonic prefix] --> M2b[One leader at 20 to 50 k commits/s cap;<br/>PUTs get 503] --> M2c[Witness takes reads off; split; per-bucket salting]
        M3[RocksDB corruption] --> M3b[One shard down] --> M3c[Restore checkpoint + replay Raft log]
    end
    subgraph ST [Storage]
        S1[Disk dies] --> S1b[~1,600 volumes at 14 of 15] --> S1c[Repair ~2 h at 20 MB/s per peer]
        S2[Rack loses power] --> S2b[2% of disks, every affected volume loses 1 fragment] --> S2c[Placement 1 per rack; repair ~6 h at event budget]
        S3[AZ dark] --> S3b[10 of 15 per volume, 2 of 3 Raft;<br/>degraded reads 9x amplification on 1/3] --> S3c[Serve on; repair waits 4 h; 8/7 placement for new volumes]
        S4[Silent bit rot] --> S4b[One fragment wrong] --> S4c[CRC on read + 14 d scrub; rebuild from 9]
    end
    subgraph BGW [Background]
        B1[GC deletes a live volume]:::critical --> B1b[Objects pointing at it return 404 / missing bytes] --> B1c[24 h grace; reconciler refuses to delete referenced extents;<br/>dry-run counters; reconciler alert = page everyone]
        B2[Repair storm on mass reboot] --> B2b[Foreground I/O starves] --> B2c[10 min start delay; per-disk cap; priority by fragments left]
    end

    class G1,G2,M1,M2,M3,S1,S2,S3,S4,B2 service
    class G1b,G2b,M1b,M2b,M3b,S1b,S2b,S3b,S4b,B1b,B2b store
    class G1c,G2c,M1c,M2c,M3c,S1c,S2c,S3c,S4c,B1c,B2c service
    class B1 critical

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
```

## D12. Migration off S3

```mermaid
%% D12: per-bucket migration from S3 with a rollback at every phase. Nothing is deleted from S3 until phase 5.
gantt
    title Migration from S3 to the new store, per bucket class
    dateFormat  YYYY-MM-DD
    axisFormat  %b
    section Phase 1 shadow
    SDK dual-write proxy to S3 + new store, read S3, nightly checksum diff (rollback = disable proxy)   :p1, 2027-01-01, 45d
    section Phase 2 read canary
    Read from new store, fall back to S3 on 404 or checksum mismatch, 1% then 25% of readers (rollback = flip router)   :p2, after p1, 30d
    section Phase 3 write cutover
    Writes go to new store only, per bucket, S3 kept as read fallback (rollback = re-enable dual write, replay from new store)   :p3, after p2, 45d
    section Phase 4 backfill cold
    Bulk copy cold buckets with checksums, lifecycle rules translated, 200 GB/s budget (rollback = nothing to undo)   :p4, after p2, 90d
    section Phase 5 decommission
    Stop S3 reads, delete S3 copies after 30 d of zero fallbacks (rollback = none, gate on metrics)   :p5, after p4, 30d
```
