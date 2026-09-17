# Diagrams: Petabyte batch + streaming ingestion

The D1 to D12 set from `hld/CLAUDE.md` §4. A diagram is drawn once: the ones embedded in [`solution.md`](solution.md) are linked here, not repeated.

| # | Diagram | Where |
|---|---|---|
| D1 | Context | below |
| D2 | Data flow | below |
| D3 | Component architecture (final design) | `solution.md` §6 |
| D4 | Happy path per FR | FR1 Kafka batch: `solution.md` §6 Flow 1. FR2 file: §6 Flow 2. FR3 CDC: §6 Flow 3. FR4 replay: §6 Flow 4. FR5 schema: §6 Flow 6 |
| D5 | Failure paths | Driver dies after commit: `solution.md` §6 Flow 5. Sink down 60 min: §5.2. Broker dies: §10.4. Job falls off retention: below. Duplicate S3 notification: §6 Flow 2 |
| D6 | Decision flow | Lateness routing: `solution.md` §5.3. Schema mismatch per record: §5.4. Batch planning and rate limit: below |
| D7 | Entity relationship | `solution.md` §3.3 |
| D8 | State machine | Batch lifecycle: below. Pipeline lifecycle: below |
| D9 | Deployment / topology | Pools and control plane: `solution.md` §5.5. Regions and AZs: below |
| D10 | Scaling / partitioning | File bomb and fix: `solution.md` §5.1. Kafka partitions to tasks to files: below |
| D11 | Failure mode map | below |
| D12 | Rollout / migration | below |

---

## D1. Context (zoom-out)

```mermaid
%% D1: context. Our system is the buffer plus the landing jobs plus the control plane. Producers, uploaders, source databases, and the query side are outside it.
flowchart LR
    APP[Producer services<br/>thousands] -->|"events, Avro/JSON, ~1 KB, 10 M/s"| SYS[Ingestion platform<br/>Kafka + landing jobs + control plane]
    UP[Uploaders, partners] -->|"files, 10 M/day"| SYS
    DB[(Operational databases)] -->|"row changes via WAL, 100k/s"| SYS
    SYS -->|"bronze, mirror, quarantine tables"| LAKE[(Lakehouse on S3)]
    LAKE -->|"SQL, downstream jobs"| Q[Query engines, downstream pipelines]
    SYS -.->|"schema by id, register"| SR[Schema registry]
    SYS -.->|"freshness, lag, quarantine"| OBS[Observability, on-call]
    OWN[Pipeline owners] -->|"create, pause, replay"| SYS

    class APP,UP,OWN,Q client
    class SYS service
    class LAKE store
    class DB,SR,OBS external

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

## D2. Data flow

```mermaid
%% D2: data flow with formats, sizes, and rates. Bytes shrink 5 to 10x between Kafka and the lake because of Parquet. File count is the number to watch, not bytes.
flowchart LR
    P[Producers] -->|"Avro records, ~1 KB, 11.6 GB/s avg, 35 GB/s peak"| K[(Kafka<br/>10k partitions<br/>~3 PB local, 7 d tiered)]
    K -->|"offset ranges, 300 MB per 30 s per 10 MB/s topic"| J(Landing job<br/>decode, rescue, size)
    J -->|"Parquet zstd, 128 MB files, 100 to 200 TB/day, ~2 M files/day"| BR[(Bronze tables<br/>ingest_date partitions)]
    J -->|"raw + error, < 0.1% of records"| QT[(Quarantine tables<br/>30 d TTL)]
    J -->|"offsets/N, commits/N, ~1 KB each"| CP[(Checkpoint dirs)]
    U[Uploaders] -->|"objects, 10 M/day, 116/s"| B[(Landing buckets)]
    B -->|"notifications, 116/s"| Q[(SQS)]
    Q -->|"file lists"| J
    J -->|"file state, 200 B per file"| FS[(RocksDB file state)]
    BR -->|"hourly OPTIMIZE, 2x write amplification"| BR
    BR -->|"~200k files/day after compaction"| RD(Readers)

    class P,U client
    class J,RD service
    class K,Q queue
    class BR,QT,CP,B,FS store

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
```

## D5. Failure path: a pipeline falls behind retention

```mermaid
%% D5: the one way to lose data. The job is dead for longer than retention. The alert at half retention exists so this never happens silently.
sequenceDiagram
    autonumber
    participant K as Kafka (retention 7 d)
    participant J as Job p (dead)
    participant O as On-call
    participant CTL as Control plane
    Note over J: dies on day 0, restart loop fails (bad image)
    J-->>O: lag_seconds > 300 (warning, day 0)
    J-->>O: page lag_seconds > 0.5 x retention (day 3.5)
    O->>CTL: fix image, restart
    alt fixed before day 7
        J->>K: fetch from checkpoint offsets, catch up at cap
        Note over J: zero loss
    else fixed after day 7
        J->>K: fetch offsets/42 start
        K-->>J: OffsetOutOfRange (segments deleted)
        J->>O: alert "start offset < earliest", refuse to auto-reset
        O->>CTL: acknowledge loss, reset to earliest, record gap in table metadata
    end
```

## D6. Decision flow: batch planning and rate limit

```mermaid
%% D6: how the driver plans a batch. The plan is written before execution and never changes, which is what makes re-execution safe.
flowchart TD
    S[Trigger fires] --> A{commits/N-1 present?}
    A -->|"no, offsets/N-1 present"| R[Re-execute N-1 with the recorded plan]
    A -->|"yes"| E[Read end offsets per partition]
    E --> C{records available > maxOffsetsPerTrigger?}
    C -->|"yes"| CAP[Cap per partition proportionally,<br/>lag_seconds keeps growing, alert if > threshold]
    C -->|"no"| ALL[Take everything]
    CAP --> W[Write offsets/N]
    ALL --> W
    W --> X[Execute, write files, commit with txn]
    R --> X
    X --> D{Batch took > trigger interval?}
    D -->|"yes"| N[Next batch immediately, no wait]
    D -->|"no"| Z[Sleep until next trigger]

    class S,R,E,CAP,ALL,W,X,N,Z service
    class A,C,D decision

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

## D8. State machine: batch lifecycle

```mermaid
%% D8: a batch. The only durable transitions are the two checkpoint writes and the table commit. Everything between them is re-executable.
stateDiagram-v2
    [*] --> Planned: driver writes offsets/N
    Planned --> Executing: tasks fetch and write files
    Executing --> Planned: driver dies (files orphaned, plan kept)
    Executing --> Written: all tasks done, add actions collected
    Written --> Committed: put-if-absent commit with txn(p, N)
    Written --> Skipped: snapshot already has txn(p, N)
    Committed --> Done: driver writes commits/N
    Skipped --> Done: driver writes commits/N
    Committed --> Planned: driver dies before commits/N (re-run will Skip)
    Done --> [*]
```

## D8. State machine: pipeline lifecycle

```mermaid
%% D8: a pipeline as the control plane sees it. Auto-pause on quarantine rate is the only automatic transition out of Running.
stateDiagram-v2
    [*] --> Created: create_pipeline
    Created --> Backfilling: source older than now, availableNow run
    Created --> Running: start from latest or earliest
    Backfilling --> Running: backfill end offsets become start offsets
    Running --> Paused: owner pause, or quarantine rate > 5%
    Paused --> Running: resume (same checkpoint)
    Running --> Replaying: replay(range) creates p_replay, live keeps running
    Replaying --> Running: replaceWhere swap done
    Running --> Draining: delete requested
    Draining --> [*]: last batch committed, checkpoint archived
```

## D9. Deployment: regions and AZs

```mermaid
%% D9: one region, three AZs. Kafka stretched with rack-aware replicas. Jobs in any AZ. S3 is regional. A second region is a mirror topic plus its own bronze (evolution, solution.md 10.11).
flowchart TD
    subgraph R1["Region A"]
        subgraph AZ1["AZ 1"]
            K1[Kafka brokers 1..40<br/>rack a]
            J1[Job pools]
        end
        subgraph AZ2["AZ 2"]
            K2[Kafka brokers 41..80<br/>rack b]
            J2[Job pools]
        end
        subgraph AZ3["AZ 3"]
            K3[Kafka brokers 81..120<br/>rack c]
            CTL[Control plane<br/>3 replicas across AZs]
        end
        S3[(S3 regional<br/>tables, checkpoints, tiered segments)]
    end
    K1 <-->|"RF 3, one replica per rack"| K2
    K2 <-->|"RF 3"| K3
    K1 -->|"tiered segments after 24 h"| S3
    J1 -->|"commits"| S3
    J2 -->|"commits"| S3
    R2[Region B<br/>MirrorMaker 2 topic copy,<br/>own bronze] -.->|"evolution"| K1

    class K1,K2,K3 queue
    class J1,J2,CTL service
    class S3 store
    class R2 external

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

## D10. Scaling: partitions to tasks to files

```mermaid
%% D10: the three fan-outs. Kafka partitions scale reads, tasks scale decode, the shuffle collapses back to a few files. The hot partition is red: it sets batch time until minPartitions splits it.
flowchart LR
    T[Topic t<br/>200 partitions, 10 MB/s] --> P1[p0 .. p198<br/>50 KB/s each]
    T --> PH[p199 hot<br/>500 KB/s, keyed]:::critical
    P1 -->|"one task each"| TK[Tasks 0..198<br/>decode in ~2 s]
    PH -->|"minPartitions = 4: split offset range"| TK2[Tasks 199a..199d<br/>decode in ~2.5 s, not 10 s]
    TK --> SH[Shuffle by ingest_hour<br/>target 128 MB]
    TK2 --> SH
    SH -->|"1 to 2 files per batch"| F[(Files in ingest_date/ingest_hour)]
    F -->|"hourly OPTIMIZE"| C[(~6 x 1 GB files per hour)]

    class T queue
    class P1,TK,TK2,SH service
    class F,C store

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
```

## D11. Failure mode map

```mermaid
%% D11: each component, what fails, blast radius, mitigation. Only the buffer being unreachable is a producer-visible outage.
flowchart TD
    KB[Kafka broker dies] -->|"leader moves in ~10 s"| KB1[Blast: none, producers retry<br/>Fix: RF 3, min.isr 2, rack aware]
    KC[Kafka cluster unreachable] -->|"producers block"| KC1[Blast: every producer<br/>Fix: 3 AZ stretch, client buffering, the one real outage]:::critical
    JD[Landing job dies] -->|"lag on one pipeline"| JD1[Blast: one table or one multiplexed group<br/>Fix: restart from checkpoint, re-run is a no-op]
    S3D[S3 or table log down] -->|"every commit fails"| S3D1[Blast: all tables lag, zero loss<br/>Fix: retry with backoff, catch up at cap]
    SRD[Schema registry down] -->|"new ids fail"| SRD1[Blast: records with new schemas quarantined<br/>Fix: cache forever, replay quarantine]
    CPD[Control plane down] -->|"no restarts, no replays"| CPD1[Blast: none for running jobs<br/>Fix: 3 replicas, leases expire gracefully]
    BD[Bad decoder release] -->|"quarantine spike"| BD1[Blast: one pipeline paused<br/>Fix: auto-pause at 5%, rollback, replay range]
    CMP[Compaction dead] -->|"file count grows"| CMP1[Blast: query planning slows over days<br/>Fix: alert on files per table, run OPTIMIZE]
    RET[Job dead past retention] -->|"segments deleted"| RET1[Blast: data loss for that pipeline<br/>Fix: page at half retention, never auto-reset]:::critical

    class KB,KC,JD,S3D,SRD,CPD,BD,CMP,RET service
    class KB1,JD1,S3D1,SRD1,CPD1,BD1,CMP1 store

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
```

## D12. Rollout: from direct-to-S3 writers to the platform

```mermaid
%% D12: migration phases with a rollback point per phase. Readers flip via a view, so every rollback is a view change.
gantt
    title Migration from direct S3 writers (rollback point at each phase end)
    dateFormat  YYYY-MM-DD
    axisFormat  %b %d
    section Buffer
    Stand up Kafka, 3 AZ, tiered storage        :a1, 2026-10-01, 14d
    Producers dual-publish (old path + Kafka)   :a2, after a1, 14d
    section Landing
    New pipelines into shadow bronze tables     :b1, after a1, 21d
    Daily diff old vs shadow (counts, checksums) :b2, after b1, 7d
    section Cutover
    Flip reader views to new tables, 10 pct then all :c1, after b2, 7d
    Stop old writers, keep deployable 30 d      :c2, after c1, 30d
    section CDC
    Connectors snapshot into mirrors beside old exports :d1, after a1, 21d
    Cut over when mirror within 60 s for 24 h   :d2, after d1, 7d
```
