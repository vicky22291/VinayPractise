# Diagrams: Change data capture (CDC) pipeline

The D1 to D12 set from `hld/CLAUDE.md` §4. A diagram is drawn once: the ones embedded in [`solution.md`](solution.md) are linked here, not repeated.

| # | Diagram | Where |
|---|---|---|
| D1 | Context | below |
| D2 | Data flow | below |
| D3 | Component architecture (final design) | `solution.md` §6 |
| D4 | Happy path per FR | FR1 capture: `solution.md` §4.1 step diagram and §6 Flow 1. FR2 snapshot: §4.2 and §6 Flow 2. FR3 delivery: §4.3 and §6 Flow 1. FR4 schema: §4.4 and §6 Flow 6. Postgres logical decoding internals: §10.1 |
| D5 | Failure paths | Connector crash, duplicates: `solution.md` §6 Flow 3. Postgres failover with failover slot: §6 Flow 4. Slot budget exhausted: §6 Flow 5. MySQL failover: §10.4. Half a transaction at an atomic sink: §5.3. Kafka unavailable to Connect: below. Late insert after delete at the search sink: below |
| D6 | Decision flow | Failure triage and epoch bump: `solution.md` §5.2. Scaling a database past one reader: §5.4. Watermark window inside the capture task: below. Sink apply rule: below |
| D7 | Entity relationship | `solution.md` §3.3 |
| D8 | State machine | Captured table lifecycle: below. Snapshot chunk lifecycle: below. Replication slot lifecycle: below |
| D9 | Deployment / topology | below |
| D10 | Scaling / partitioning | Options for a database past its reader: `solution.md` §5.4. Topic grouping: below |
| D11 | Failure mode map | below. The WAL causes and the cap: `solution.md` §5.1 |
| D12 | Rollout / migration | below |

---

## D1. Context (zoom-out)

Our system is the capture tasks, the snapshot workers, Kafka and the sink framework. Databases, their owners, and every consumer sit outside it.

```mermaid
%% D1: context. The CDC platform reads 2,000 databases and feeds four kinds of consumers. Owners publish schemas through CI, on-call watches slot budgets and lag.
flowchart LR
    SVC[Services, hundreds] -->|"transactions"| DB[(Source databases<br/>1,400 Postgres, 600 MySQL)]
    DB -->|"commit-order log + chunk reads,<br/>500k changes/s avg"| SYS[CDC platform<br/>capture, snapshot, Kafka,<br/>sink framework]
    OWN[Database owners] -->|"migrations, CI contract check"| SYS
    SYS -->|"changelog + mirror tables"| LAKE[(Lakehouse)]
    SYS -->|"versioned documents"| ES[(Search indexes)]
    SYS -->|"key deletes"| CACHE[(Caches)]
    SYS -->|"change events, outbox events"| CONS[Service consumers]
    SYS -.->|"slot budget, lag, epoch bumps"| OBS[On-call, observability]

    class SVC,OWN,CONS client
    class SYS service
    class DB,LAKE,ES store
    class CACHE cache
    class OBS external

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef cache    fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

## D2. Data flow

Format, size and rate on every edge. Bytes are small. The reader per database and the lake's rewrite cost are what matter.

```mermaid
%% D2: data flow with formats, sizes and rates from solution.md §2. Processes are rounded, stores are cylinders. The serial reader per database is red.
flowchart LR
    DB[(Source DBs<br/>WAL, binlog)] -->|"row changes, commit order,<br/>500k/s avg, 1.5 M/s peak"| RD(Slot or binlog reader<br/>one per DB, ~20k events/s)
    REP[(Replicas)] -->|"chunk rows, 8,096 per chunk,<br/>20k rows/s per DB, 2 M rows/s fleet"| SW(Snapshot workers)
    SW -->|"chunk rows via task for small tables,<br/>big tables produced direct at HW"| CT(Capture tasks)
    RD -->|"decoded transactions"| CT
    CT -->|"Avro envelope ~500 B,<br/>250 MB/s avg, 750 MB/s peak,<br/>21.6 TB/day"| K[(Kafka, ~16k partitions<br/>7 d, ~227 TB with RF 3)]
    CT -->|"position every 60 s"| OFF[(Connect offsets topic)]
    K -->|"all 50k tables, 1 min tier A,<br/>10 min tier B"| LJ(Lake job)
    LJ -->|"Parquet, ~5 TB/day compressed"| CL[(Changelog)]
    LJ -->|"~600 MB new rows per min<br/>+ deletion vectors, 2 TB table"| MIR[(Mirror)]
    K -->|"~200 tables, ~20k changes/s,<br/>5k-doc bulks, 4/s"| ES[(Search indexes)]
    K -->|"~500 tables, ~100k deletes/s"| CA[(Caches)]
    K -->|"~300 outbox tables"| SC(Service consumers)

    class DB,REP,K,OFF,CL,MIR,ES store
    class SW,CT,LJ,SC service
    class CA cache
    class RD critical

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef cache    fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
```

## D5. Failure path: Kafka unavailable to Connect for 20 minutes

Nothing is lost, the slot holds everything, but the slot budget burns and the catch-up is bounded by the serial reader.

```mermaid
%% D5: Kafka unreachable from Connect for 20 min on a busy primary. The in-memory queue fills, the reader stops, WAL is pinned at 50 MB/s, the page fires at 5 min. Recovery drains at the reader ceiling minus the live rate.
sequenceDiagram
    autonumber
    participant DB as Busy primary
    participant CT as Capture task
    participant K as Kafka
    participant M as Monitoring
    participant O as On-call
    CT--xK: produce fails, retries (t = 0)
    CT->>CT: max.queue.size 8,192 fills, stops reading the slot
    Note over DB,CT: slot pins WAL at up to 50 MB/s, 3 GB per min at peak
    M->>O: page, Kafka unavailable to Connect (t = 5 min)
    Note over DB,CT: 60 GB pinned at t = 20 min, cap 500 GB, about 2.5 h budget left
    K-->>CT: brokers reachable again (t = 20 min)
    CT->>K: flush queue, idempotent producer, no duplicates
    CT->>DB: resume reading from confirmed position
    Note over CT,K: backlog 20 min x 12.5k/s = 15 M events
    Note over CT,K: drains at 20k/s ceiling minus 12.5k/s live = 7.5k/s, about 33 min
    CT->>DB: confirm LSN as offsets commit, WAL released
    M->>O: resolve, budget back to full, sink lag under SLO
```

## D5. Failure path: a late older insert after a delete at the search sink

Why the search sink writes soft deletes. A real delete forgets its version after `index.gc_deletes` (60 s), so a replayed older insert resurrects the row.

```mermaid
%% D5: replay after a consumer group reset re-delivers an old insert after the delete. With a real delete the version is gone after 60 s and the row comes back. With a soft delete the tombstone keeps version v2 and the replay gets a 409.
sequenceDiagram
    autonumber
    participant K as Kafka orders topic
    participant S as Search consumer
    participant ES as Elasticsearch
    K->>S: insert id 42, version v1 = (7, 0/A000)
    S->>ES: index 42, external_gte, v1
    K->>S: delete id 42, version v2 = (7, 0/B000)
    alt real delete
        S->>ES: DELETE 42, v2
        Note over ES: delete version kept only for gc_deletes, 60 s
        S->>K: rebalance, re-read from before v1 (t + 10 min)
        K->>S: insert id 42, v1 again
        S->>ES: index 42, v1
        ES-->>S: 201 created, no stored version to compare
        Note over S,ES: row 42 resurrected, wrong until the next change
    else soft delete (chosen)
        S->>ES: index 42 as deleted = true, v2
        S->>K: rebalance, re-read from before v1 (t + 10 min)
        K->>S: insert id 42, v1 again
        S->>ES: index 42, v1
        ES-->>S: 409 version conflict, v1 < v2
        S->>S: count and ignore
        Note over S,ES: nightly job purges soft deletes older than 7 d
    end
```

## D6. Decision flow: the watermark window inside the capture task

What the capture task does with each event it reads from the log while a chunk is in flight. This is the DBLog handoff from `solution.md` §4.2, in the variant that never pauses the log: keys are recorded by primary-key range, because a replica read may still be running when `LW_k` is processed.

```mermaid
%% D6: per-event logic in the capture task during an incremental snapshot. Change events are always published. While the window is open the task records every changed key in chunk k's pk range. At HW the recorded keys are subtracted from the chunk rows and the survivors are emitted with the HW version, by the task for small tables or by the snapshot worker for big ones.
flowchart TD
    E[Next event from the log] -->|"read"| Q1{Watermark for chunk k?}
    Q1 -->|"LW_k"| OPEN[Open window]
    Q1 -->|"HW_k"| EMIT[Chunk rows minus recorded keys<br/>as op r, version = HW_k,<br/>task or worker emits]
    Q1 -->|"no, a row change"| PUB[Publish change,<br/>version = epoch, commit pos, index]
    PUB -->|"after publish"| Q2{Window open?}
    Q2 -->|"no"| E
    Q2 -->|"yes"| Q3{Key in chunk k pk range?}
    Q3 -->|"yes"| DROP[Record key as changed,<br/>the change is newer]
    Q3 -->|"no"| E
    DROP -->|"next event"| E
    OPEN -->|"next event"| E
    EMIT -->|"close window"| CUR[Save cursor: table, last pk,<br/>chunk id with offset]
    CUR -->|"next chunk"| E

    class E,OPEN,EMIT,PUB,DROP,CUR service
    class Q1,Q2,Q3 decision

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

## D6. Decision flow: the sink apply rule

One rule at every versioned sink. It turns at-least-once delivery into exactly-once effect, merges snapshot rows with live changes, and survives failover because the epoch leads the version.

```mermaid
%% D6: apply rule per event at a versioned sink (lake mirror, search, service inbox). Equal versions are no-ops, lower versions are rejected, deletes keep a tombstone with their version for at least the 7 d replay window.
flowchart TD
    EV[Event: key, op, version] -->|"look up key"| Q1{Stored row or<br/>tombstone for key?}
    Q1 -->|"none"| Q2{op is d?}
    Q2 -->|"yes"| TS[Write tombstone<br/>key, version, deleted]
    Q2 -->|"no, c u r"| INS[Insert row with version]
    Q1 -->|"yes"| Q3{Incoming version<br/>newer than stored?}
    Q3 -->|"no, equal or lower"| NOP[No-op, count as duplicate<br/>or late arrival]
    Q3 -->|"yes"| Q4{op is d?}
    Q4 -->|"yes"| TS
    Q4 -->|"no"| UPD[Overwrite row and version,<br/>clear deleted flag]
    TS -->|"after 7 d, nightly"| PURGE[Purge tombstone]

    class EV client
    class TS,INS,NOP,UPD,PURGE service
    class Q1,Q2,Q3,Q4 decision

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

Search uses `external_gte`, so "equal" is accepted there: two changes to one key in one transaction share a commit LSN, and the consumer reduces each batch to the last change per key before writing.

## D8. State machine: captured table lifecycle

A table streams live changes from the moment it is registered. The snapshot runs beside the stream, not before it.

```mermaid
%% D8: a captured table. Snapshotting and Streaming both publish live changes; Snapshotting also emits chunk rows. Parked keeps the slot moving by sending the table's events to a holding topic. Rebuilding follows a lost slot or unsafe failover.
stateDiagram-v2
    direction LR
    [*] --> Registered: add to publication
    Registered --> Snapshotting: signal sent
    Snapshotting --> Snapshotting: DDL, redo chunk
    Snapshotting --> Streaming: last chunk emitted
    state "Live" as Live {
        direction TB
        Streaming --> Parked: schema rejected
        Parked --> Streaming: replay holding topic
    }
    Parked --> Snapshotting: accept, re-snapshot
    Streaming --> Rebuilding: slot lost, epoch + 1
    Rebuilding --> Streaming: re-snapshot done
    Streaming --> Removed: decommissioned
    Removed --> [*]
```

## D8. State machine: snapshot chunk lifecycle

A chunk is re-readable until its rows are emitted. The cursor is saved with the connector offset, so a crash repeats at most one chunk.

```mermaid
%% D8: one chunk of an incremental snapshot. Any failure before Emitted sends the chunk back to Planned with new watermarks. Only Emitted advances the cursor.
stateDiagram-v2
    direction LR
    [*] --> Planned: next pk range
    Planned --> LowWritten: LW_k committed
    LowWritten --> Read: replica past LW_k
    Read --> HighWritten: HW_k committed
    HighWritten --> Reconciling: task sees LW_k
    Reconciling --> Emitted: task sees HW_k
    Emitted --> [*]: cursor saved
    Read --> Planned: task crash
    Reconciling --> Planned: DDL on table
    HighWritten --> Planned: task crash
```

## D8. State machine: replication slot lifecycle

The `wal_status` column of `pg_replication_slots` plus invalidation. `extended` is past `max_wal_size` but still retained; `unreserved` means required files go at the next checkpoint; `lost` is unusable.

```mermaid
%% D8: a logical slot on Postgres. WAL status moves with reader lag against max_wal_size and the cap (max_slot_wal_keep_size). Invalidation is terminal: the control plane creates a new slot and bumps the epoch.
stateDiagram-v2
    direction LR
    [*] --> Reserved: created, reader attached
    state "WAL retained" as Retained {
        direction LR
        Reserved --> Extended: past max_wal_size
        Extended --> Reserved: reader catches up
        Extended --> Unreserved: past the cap
        Unreserved --> Extended: reader catches up
    }
    Unreserved --> Invalidated: checkpoint, wal_removed
    Reserved --> Invalidated: idle_timeout, PG18
    Invalidated --> [*]: new slot, epoch + 1
    Reserved --> Dropped: decommissioned
    Dropped --> [*]
```

Orthogonal to this: `active` (a reader is streaming) versus inactive (`inactive_since` set), and on a Postgres 17+ standby a `synced = true` copy that cannot be decoded or dropped there and becomes the live slot only after promotion (`solution.md` §6 Flow 4).

## D9. Deployment: one region, three AZs

Where each piece runs. The failover slot lives on the primary and is synced to one standby; the top 20 databases also get a CDC standby that decodes off the primary.

```mermaid
%% D9: topology. Primary, synced standby and CDC standby sit in different AZs. Connect and the control plane are stateless and spread over all AZs. Kafka is stretched over 3 AZs with RF 3. The capped slot on the primary is red.
flowchart LR
    subgraph DBT["Database tier, one region"]
        direction TB
        subgraph AZA["AZ a"]
            PRI[(Postgres primary)]
            SLOT[Failover slot, capped<br/>one serial reader]:::critical
        end
        subgraph AZB["AZ b"]
            SBY[(Standby<br/>sync_replication_slots,<br/>in synchronized_standby_slots)]
        end
        subgraph AZC["AZ c"]
            CDCS[(CDC standby, top 20 only<br/>decodes off the primary)]
            REP[(Read replica for chunks)]
        end
    end
    PRI -->|"decoded changes"| SLOT
    PRI -->|"WAL, physical slot"| SBY
    PRI -->|"WAL"| CDCS
    PRI -->|"WAL"| REP
    SBY -.->|"slot copy, synced"| SLOT
    SLOT -->|"change stream"| CON[10 Connect clusters<br/>~120 workers, all 3 AZs]
    CDCS -->|"change stream, top 20"| CON
    REP -->|"chunk reads"| CON
    CTL[Control plane<br/>3 replicas, 3 AZs] -.->|"configs, epochs, budgets"| CON
    CON -->|"acks=all, min ISR 2"| K[(Kafka, ~15 brokers<br/>5 per AZ, RF 3)]
    K -->|"consumer groups"| SINKS[Sinks: lake on S3,<br/>search, caches, services]

    class PRI,SBY,CDCS,REP,K store
    class CON,SINKS,CTL service

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
```

Nothing crosses a region boundary on the capture path. Multi-region consumers read mirrored topics (`solution.md` §10.11).

## D10. Scaling: topic grouping

Partitions scale consumers, not capture. The hot element is still the one serial reader per database; grouping only fixes the broker count.

```mermaid
%% D10: topic layout. Busy tables get their own topics, quiet tables share one topic per database keyed by table plus pk. Per-key order is unchanged. The serial reader in front of all of them is red.
flowchart LR
    SLOT[One slot, one serial reader<br/>per database, ~20k events/s]:::critical -->|"all tables of the DB"| CT[Capture task router]
    CT -->|"table above 100 changes/s?"| Q{Busy table?}
    Q -->|"yes, ~2,000 tables"| OWN[(Own topic per table<br/>~6 partitions, key = pk<br/>~12k partitions)]
    Q -->|"no, ~48k tables"| GRP[(One topic per database<br/>key = table + pk<br/>~4k partitions)]
    OWN -->|"~16k partitions, ~48k replicas"| KF[Kafka, ~15 brokers]
    GRP -->|"per-key order unchanged"| KF
    NAIVE[(Naive: topic per table<br/>50k topics, 150k+ replicas)] -.->|"would need ~40 brokers"| KF

    class CT service
    class Q decision
    class OWN,GRP,NAIVE store
    class KF queue

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
```

## D11. Failure mode map

Component, what fails (on the edge), blast radius (in the node), mitigation. The only red node is the one whose failure could reach production.

```mermaid
%% D11: one tree. Edge label = what fails. Component node = blast radius. Leaf = mitigation. Only the slot can hurt the source database.
flowchart TD
    R[CDC platform] -->|"reader behind or down"| S[Slot on primary<br/>radius: primary disk]:::critical
    R -->|"task crash"| T[Capture task<br/>radius: one DB, under 1 min]
    R -->|"cluster loss"| C[Connect cluster<br/>radius: ~200 DBs]
    R -->|"cluster down"| K[Kafka<br/>radius: every slot burns]
    R -->|"registry down"| G[Schema registry<br/>radius: new schemas only]
    R -->|"sink down"| SK[One sink<br/>radius: that sink's lag]
    S -->|"mitigation"| MS[WAL cap, budget in hours,<br/>lose slot, re-snapshot]
    T -->|"mitigation"| MT[Resume from offset,<br/>versions reject duplicates]
    C -->|"mitigation"| MC[10 clusters by domain,<br/>15 min recovery vs budget]
    K -->|"mitigation"| MK[3 AZ, min ISR 2,<br/>page at 5 min]
    G -->|"mitigation"| MG[Cached schemas,<br/>park the table]
    SK -->|"mitigation"| MSK[Kafka absorbs lag,<br/>replay with versions]

    class R client
    class T,C,G,SK service
    class K queue
    class MS,MT,MC,MK,MG,MSK store

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
```

## D12. Rollout: from nightly dumps and dual writes to CDC

Phases with a rollback point at each phase end. Readers flip via views and services via a flag, so every rollback is a view change or a flag.

```mermaid
%% D12: migration phases from solution.md §8. Capture starts with no_data so nothing is locked. Backfill runs under the fleet budget. Shadow diffs run a week before any reader flips.
gantt
    title Migration to CDC (rollback point at each phase end)
    dateFormat  YYYY-MM-DD
    axisFormat  %b %d
    section Prepare
    wal_level logical, WAL caps, failover slots per cluster :p1, 2026-10-05, 14d
    Kafka 3 AZ and 10 Connect clusters                      :p2, 2026-10-05, 14d
    Registry subjects and CI contract check                  :p3, after p1, 7d
    Rollback point, drop slots and connectors                :milestone, m1, after p3, 0d
    section Capture
    Create slots, start with no_data snapshot mode           :c1, after p3, 7d
    section Backfill
    DBLog snapshots, 100 DBs at a time, 2 M rows per s fleet :b1, after c1, 14d
    Rollback point, stop snapshots, old dumps still primary  :milestone, m2, after b1, 0d
    section Shadow
    Shadow mirrors, daily count and checksum diffs           :s1, after b1, 7d
    Dual-write targets diffed against CDC consumers          :s2, after b1, 7d
    section Cutover
    Flip reader views to mirrors, 10 pct then all            :x1, after s1, 7d
    Turn off dual-write flag per service                     :x2, after s2, 7d
    Rollback point, flip views back or re-enable flag        :milestone, m3, after x1, 0d
    section Retire
    Keep nightly dumps and dual-write code runnable 30 d     :r1, after x1, 30d
```
