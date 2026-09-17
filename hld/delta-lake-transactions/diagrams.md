# Diagrams: Delta Lake, transactional tables over object storage

The D1 to D12 set from `hld/CLAUDE.md` §4. A diagram is drawn once: the ones embedded in [`solution.md`](solution.md) are linked here, not repeated.

| # | Diagram | Where |
|---|---|---|
| D1 | Context | below |
| D2 | Data flow | below |
| D3 | Component architecture (final design) | `solution.md` §6 |
| D4 | Happy path per FR | FR1 atomic write: `solution.md` §6 Flow 1. FR2 snapshot: §6 Flow 2. FR3 concurrent writers: §6 Flow 3. FR4 MERGE with deletion vectors: below. FR5 OPTIMIZE + stream: §6 Flow 5 |
| D5 | Failure paths | Writer crash before commit: `solution.md` §6 Flow 4. VACUUM vs time travel: §6 Flow 6. DynamoDB arbiter loses a writer: §10.4. Object store 503 mid-commit: below |
| D6 | Decision flow | Arbiter choice: `solution.md` §5.1. Conflict detection: §5.3. File size pipeline: §5.4 |
| D7 | Entity relationship | `solution.md` §3.3 |
| D8 | State machine (data file lifecycle) | `solution.md` §5.5. Commit lifecycle (catalog-managed): below |
| D9 | Deployment / topology | below |
| D10 | Scaling / partitioning | `solution.md` §5.2 (checkpoint sidecars). Log and data prefixes: below |
| D11 | Failure mode map | below |
| D12 | Rollout / migration | below |

---

## D1. Context (zoom-out)

```mermaid
%% D1: context. Our system is the table format: the log, the checkpoint, the commit protocol. Engines and the object store are outside it.
flowchart LR
    ENG[Query engines<br/>Spark, Photon, Trino, kernel clients] -->|"read snapshot, commit actions"| SYS[Table format<br/>_delta_log + checkpoint + commit protocol]
    STREAM[Streaming jobs<br/>sink and source] -->|"append + txn, tail adds"| SYS
    OPS[Maintenance jobs<br/>OPTIMIZE, VACUUM] -->|"dataChange=false commits, deletes"| SYS
    SYS -->|"PUT, conditional PUT, GET, LIST, DELETE"| OBJ[(Object store<br/>S3, ADLS, GCS)]
    SYS -.->|"ratify commit, latest version"| CAT[Catalog<br/>Unity, Glue, REST]
    SYS -.->|"put-if-absent before S3 2024"| DDB[(DynamoDB<br/>log store rows)]
    USER[Analysts, pipelines] -->|"SQL"| ENG

    class ENG,STREAM,OPS,USER client
    class SYS service
    class OBJ,DDB store
    class CAT external

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

## D2. Data flow (DFD)

```mermaid
%% D2: what flows where, with sizes and rates for a 1 PB table ingesting 8.6 TB/day at 1 commit/s.
flowchart LR
    IN([Input rows<br/>100 MB/s, ~1 M rows/s]) -->|"micro-batch 10 s, 1 GB"| WR(Writer<br/>shuffle, encode Parquet)
    WR -->|"Parquet files, ~128 MB each, ~10/commit"| DATA[(Data files<br/>1 PB, 1 M files)]
    WR -->|"N.json, ~2 KB per add, ~20 KB per commit, 1/s"| LOG[(_delta_log/<br/>86k objects/day)]
    WR -->|"every 10 commits: manifest ~1 MB + changed sidecars ~10 MB"| CK[(Checkpoint<br/>~750 MB total at 1 M files)]
    RD(Reader<br/>plan, prune, scan) -->|"1 GET + 1 LIST + <= 10 GET, ~250 KB"| LOG
    RD -->|"sidecars for query partitions, ~10 MB"| CK
    RD -->|"2 footer GETs per surviving file, then column chunks"| DATA
    RD -->|"result"| OUT([Query result])
    MG(MERGE<br/>join, write DVs) -->|"DV bitmaps, KBs per file + new rows"| DATA
    MG -->|"add with dv, remove"| LOG
    OPT(OPTIMIZE<br/>bin-pack, cluster) -->|"rewrite 1 to 2x ingest bytes/day"| DATA
    OPT -->|"remove + add, dataChange=false"| LOG

    class IN,OUT client
    class WR,RD,MG,OPT service
    class DATA,LOG,CK store

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
```

## D4. Happy path, FR4: MERGE with deletion vectors

```mermaid
%% D4 (FR4): MERGE as merge-on-read. Prune, join, write bitmaps and new rows, one commit.
sequenceDiagram
    autonumber
    participant M as MERGE driver
    participant L as _delta_log
    participant DATA as Data files
    participant DV as DV files
    M->>L: snapshot r (checkpoint + tail)
    M->>M: prune by partition and min/max on join key: 1 M -> 2,000 files (F_read)
    M->>DATA: scan F_read, inner join with source on key
    M->>M: 300 files contain matches (F_touched), 50k rows to update, 10k to insert
    M->>DV: PUT one .bin with 300 bitmaps (updated row positions)
    M->>DATA: PUT new files: 50k updated rows + 10k inserted rows (~60 MB)
    M->>L: PUT r+1.json If-None-Match *: add(F_touched with dv) x300, add(new) x2, remove(F_touched old dv) x300, commitInfo(readVersion r, MERGE)
    L-->>M: 200
    Note over M: readers at r+1 scan the 300 files, skip bitmap rows, and read the 2 new files
```

## D5. Failure path: object store returns 503 SlowDown mid-commit

```mermaid
%% D5: the conditional PUT times out with no response. The writer must find out whether it won before retrying, or it would commit twice.
sequenceDiagram
    autonumber
    participant D as Driver
    participant L as _delta_log (S3)
    D->>L: PUT 101.json If-None-Match *
    Note over L: 503 SlowDown or socket timeout, response lost
    D->>L: GET 101.json
    alt 404
        D->>L: PUT 101.json If-None-Match * (retry with backoff)
    else 200 and commitInfo.txnId == mine
        Note over D: my PUT landed, commit succeeded
    else 200 and commitInfo.txnId != mine
        D->>D: someone else won 101, run conflict detection, try 102
    end
    Note over D: the txnId in commitInfo is what makes the PUT retry safe
```

## D8. Commit lifecycle (catalog-managed variant)

```mermaid
%% D8: states of one commit attempt when the catalog is the arbiter. Only the catalog moves a commit from proposed to ratified.
stateDiagram-v2
    [*] --> Proposed: writer builds actions
    Proposed --> Staged: PUT _staged_commits/v.uuid.json
    Proposed --> Inline: send content to catalog
    Staged --> Ratified: catalog CAS latest = v-1 -> v wins
    Inline --> Ratified: same CAS
    Staged --> Rejected: CAS fails, another proposal won v
    Inline --> Rejected: CAS fails
    Rejected --> [*]: conflict detection, retry as v+1
    Ratified --> Published: catalog or writer copies to _delta_log/v.json
    Published --> [*]
```

## D9. Deployment / topology

```mermaid
%% D9: where things run. Compute is stateless and per job. State is the bucket. The arbiter is regional. One home region per table.
flowchart TD
    subgraph R1["Region A (table home)"]
        subgraph C1["Cluster 1 (ingest)"]
            W1[Stream sink driver + executors]
        end
        subgraph C2["Cluster 2 (analytics)"]
            Q1[Query drivers + snapshot cache]
        end
        subgraph C3["Cluster 3 (maintenance)"]
            O1[OPTIMIZE, VACUUM, checkpoint]
        end
        B1[(Bucket: data, _delta_log, _sidecars<br/>versioning on _delta_log/)]
        A1[Arbiter: S3 conditional PUT<br/>or catalog CAS, 99.99%]:::critical
        W1 -->|"PUT files, commit"| A1
        O1 -->|"commit"| A1
        A1 --> B1
        Q1 -->|"GET, LIST"| B1
    end
    subgraph R2["Region B (replica, read-only)"]
        B2[(Bucket replica)]
        Q2[Query drivers]
        Q2 --> B2
    end
    B1 -.->|"replay log: copy N.json + its adds, minutes behind"| B2

    class W1,Q1,O1,Q2 client
    class B1,B2 store

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
```

## D10. Scaling / partitioning: prefixes and the hot one

```mermaid
%% D10: what is sharded by what. Tables are independent logs. Data files spread over prefixes. The log directory is one prefix and one arbiter per table: that is the hot spot, bounded by commit rate not bytes.
flowchart LR
    T1[Table A] --> LA[(_delta_log/ A<br/>one prefix, one arbiter,<br/>few commits/s)]:::critical
    T1 --> DA1[(data prefix a1/<br/>randomizeFilePrefixes)]
    T1 --> DA2[(data prefix a2/)]
    T1 --> DAN[(data prefix aN/)]
    T2[Table B] --> LB[(_delta_log/ B)]
    T2 --> DB1[(data prefixes b*/)]
    FIX[Fix for a hot log: batch writers upstream,<br/>or catalog arbiter at ~100 commits/s,<br/>never shard one table's log] -.-> LA

    class T1,T2 client
    class DA1,DA2,DAN,LB,DB1 store
    class FIX service

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
```

## D11. Failure mode map

```mermaid
%% D11: component -> failure -> blast radius -> mitigation. The only red node is the one that can break every reader at once.
flowchart TD
    W[Writer] -->|"dies before commit"| W1[Orphan files, invisible] --> W1M[VACUUM after 7 d]
    W -->|"dies after PUT, before checkpoint"| W2[Longer replay for next reader] --> W2M[Any next writer checkpoints]
    W -->|"PUT response lost"| W3[Unknown outcome] --> W3M[GET N.json, compare txnId]
    A[Arbiter] -->|"conditional PUT unsupported"| A1[Two winners, lost commit] --> A1M[DynamoDB store or catalog, never plain PUT]
    A -->|"catalog down"| A2[No commits table-wide, reads of tail stall] --> A2M[99.99% catalog, readers fall back to published log]
    L[_delta_log] -->|"entry deleted or corrupt"| L1[Table unreadable past N-1]:::critical --> L1M[S3 versioning on prefix, deny DeleteObject, RESTORE]
    L -->|"no checkpoint for 500 commits"| L2[Snapshot 5 s instead of 250 ms] --> L2M[Alert on checkpoint age, any writer can fix]
    V[VACUUM] -->|"retention 0"| V1[Every reader on an old snapshot fails] --> V1M[retentionDurationCheck on, 7 d floor]
    OPT[OPTIMIZE] -->|"races an UPDATE without DVs"| O1[One of them re-runs] --> O1M[Enable DVs, schedule per partition]
    OS[Object store] -->|"503 SlowDown"| S1[Commits slow, no corruption] --> S1M[Backoff, spread data prefixes]

    class W,A,L,V,OPT,OS service
    class W1,W2,W3,A1,A2,L2,V1,O1,S1 decision
    class W1M,W2M,W3M,A1M,A2M,L1M,L2M,V1M,O1M,S1M store

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
```

## D12. Rollout / migration from Hive-style Parquet tables

```mermaid
%% D12: zero-copy migration. Data files never move. Each phase has a rollback that is a catalog pointer or a config flag.
gantt
    title Hive Parquet table to Delta, one table family, rollback point per phase
    dateFormat  YYYY-MM-DD
    axisFormat  %b %d
    section Phase 1 readers
    Upgrade all reader runtimes to a Delta-capable version      :p1a, 2026-10-01, 7d
    CONVERT TO DELTA in place, version 0 lists existing files   :p1b, after p1a, 1d
    Point catalog name at Delta table, rollback = point back    :p1c, after p1b, 3d
    section Phase 2 ingest writer
    Stop Hive writer, start Delta append with txn ids           :p2a, after p1c, 2d
    Enable optimized writes and auto compaction                 :p2b, after p2a, 3d
    Rollback = restart Hive writer and re-CONVERT               :p2c, after p2b, 1d
    section Phase 3 MERGE and DELETE jobs
    Move MERGE jobs one at a time, WriteSerializable            :p3a, after p2c, 7d
    Enable deletion vectors, protocol bump, old readers refuse  :p3b, after p3a, 2d
    Rollback = DROP FEATURE after OPTIMIZE folds DVs            :p3c, after p3b, 1d
    section Phase 4 metadata
    Enable V2 checkpoints on tables over 1 M files              :p4a, after p3c, 3d
    Turn on VACUUM schedule with 7 d retention                  :p4b, after p4a, 1d
```
