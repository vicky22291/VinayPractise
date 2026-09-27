# Change data capture (CDC) pipeline

> One-line answer: read each database's own commit log (Postgres replication slot, MySQL binlog) with one serial reader per database, publish every row change to Kafka keyed by primary key with a version that is monotonic per key in commit order, backfill existing rows with a watermark-chunked snapshot that never locks and never time-travels, and make every sink apply "only if this version is newer" so at-least-once delivery becomes exactly-once effect. The thing that breaks first is not throughput. It is the replication slot pinning WAL on the production primary, so the design caps it, measures it in hours of budget, and chooses to lose the slot (and re-snapshot) before it lets CDC take the database down.

Tier 2, problem #22 in [`hld/README.md`](../README.md). Asked at Databricks (Lakeflow Connect, `AUTO CDC`), Confluent (Debezium on Connect), Snowflake, and as a sub-question in any "keep the search index / cache / warehouse in sync with the database" prompt. Sibling problems: [`../streaming-ingestion/`](../streaming-ingestion/) (#18) treats CDC as one of three sources landing in a lake; this problem is the CDC platform itself, with several sinks and the correctness and source-safety questions #18 leaves out. Reusable blocks: [`../../concepts/stream-processing.md`](../../concepts/stream-processing.md) §7 (snapshot-to-stream handoff), [`../../concepts/exactly-once.md`](../../concepts/exactly-once.md) (outbox, inbox, idempotent apply), [`../../concepts/caching-patterns.md`](../../concepts/caching-patterns.md) (CDC invalidation as a backstop), [`../delta-lake-transactions/`](../delta-lake-transactions/) (the mirror table's MERGE), [`../../popular_systems_deepdive/kafka/`](../../popular_systems_deepdive/kafka/) (the log in the middle). Sources in [`research/`](research/).

## Problem statement (as asked)

The company runs ~2,000 operational databases (Postgres and MySQL) behind hundreds of services. Analytics wants every table mirrored in the lakehouse within minutes. Search wants its indexes to follow the product tables within seconds. Caches go stale when someone writes around the application. Other services want to react to changes without the owning team adding a dual write. Design the change data capture platform: capture every committed insert, update and delete, deliver it to many consumers in order, bootstrap existing data without locking anything, survive connector crashes and database failovers without losing or duplicating a change, and never become the reason a production database goes down.

## Functional requirements

Core:
- **Capture.** Every committed insert, update and delete on a captured table is published within seconds, in commit order per row, with its source position and transaction id.
- **Snapshot and handoff.** A newly captured table (or a repair of a key range) gets its existing rows without locking the source, with no gap and no double apply against the live stream, and without showing sinks older state than they already had.
- **Deliver with exactly-once effect.** Lake mirror tables, search indexes, cache invalidation and service consumers each end up with exactly the source's state per key, despite duplicates, replays and failovers. Deletes are applied.
- **Schema changes.** DDL on the source (add, drop, rename, retype) flows through without stopping capture and without corrupting sinks; breaking changes are caught before they ship.

Below the line (say it out loud):
- Business events with intent ("order shipped, send an email"). CDC copies state, it does not explain why state changed. Services that need intent write an outbox row in the same transaction and the same pipeline carries it.
- Transforms, joins and aggregations. Downstream jobs on the mirror tables.
- Multi-master or bidirectional replication, and conflict resolution between writers.
- Sources other than Postgres and MySQL (MongoDB change streams, Oracle, DynamoDB streams). Same shape, different log reader.
- The lake landing machinery (file sizing, `txn` markers, compaction). Reused from #18.

## Non-functional requirements

| Dimension | Target |
|---|---|
| Scale | 2,000 source databases (1,400 Postgres, 600 MySQL), 50,000 captured tables, 500k row changes/s average and 1.5 M/s peak (43 B changes/day), largest database 60k changes/s at peak, largest table 4 B rows (2 TB) |
| Freshness | Commit to Kafka p99 < 2 s. Commit to search and cache sinks p99 < 5 s. Commit to lake mirror p99 < 2 min (tier A) or 10 min (tier B) |
| Correctness | No committed change lost. Per-key order at every sink. Exactly-once effect per change per sink. Transaction boundaries available to sinks that ask for them |
| Source safety | No table locks ever. CDC adds < 5% CPU on a primary. WAL pinned by CDC is capped per database and alerted in hours of budget, not bytes. A CDC outage can never fill a primary's disk |
| Availability | Capture 99.9% (it is asynchronous, the database keeps serving). Connector recovery < 1 min. Survives source failover without a full re-snapshot on Postgres 17+ and GTID MySQL |
| Snapshot | Largest table bootstrapped in < 24 h, pausable and resumable, rate-limited to a source budget, re-runnable for a key range |
| Retention | Change topics 7 days (the replay and bootstrap window). Lake changelog forever (the history once the database log is gone) |

## What interviewers probe (the ladder)

1. The snapshot is running and writes keep coming. How do you avoid a gap or a double apply at the handoff, and what does the search index show while it catches up?
2. The connector crashed after publishing but before saving its position. What does each sink see, and why is it still correct?
3. A transaction inserted an order and five order items. Can a consumer see the order without its items? Do you care? What would it cost to prevent?
4. The connector has been down for 6 hours. What is happening on the production database right now? When does it become an outage, and what do you do at that point?
5. The Postgres primary fails over. Does the replication slot survive? Could you have published a change the new primary does not have?
6. Someone runs `ALTER TABLE ... RENAME COLUMN` on a captured table on Friday evening. What happens in each sink?
7. One database does 60k changes/s and your connector does 20k. What now? What does splitting it cost the source?
8. Why not poll with `updated_at`? Why not triggers? Why not have the app publish to Kafka?
9. Kafka has exactly-once. Why do you still need idempotent sinks?
10. A new team wants a full copy of a 2 TB table in their own store. Do you snapshot the source again?

## Files

| File | What it is |
|---|---|
| [`solution.md`](solution.md) | Full HLD in flow-first form: one incremental diagram per FR, deep dives that break and mutate it, final design and core flows, then nitty-gritty |
| [`diagrams.md`](diagrams.md) | The D1 to D12 diagram set |
| [`edge-cases.md`](edge-cases.md) | Every "what if" with a 60-second answer and a confidence box |
| [`deep-dives/log-capture-and-positions.md`](deep-dives/log-capture-and-positions.md) | Postgres slots, pgoutput, LSNs, REPLICA IDENTITY, TOAST; MySQL binlog, GTID, schema history; how a per-key version is built |
| [`deep-dives/snapshot-and-stream-handoff.md`](deep-dives/snapshot-and-stream-handoff.md) | Locked snapshot vs position-then-replay vs DBLog watermarks vs Flink CDC chunks, the correctness argument, replica reads, parallel chunks, bootstrapping a new consumer from the mirror |
| [`deep-dives/exactly-once-sinks.md`](deep-dives/exactly-once-sinks.md) | Versioned apply at each sink: lake `MERGE` / `AUTO CDC`, Elasticsearch `external_gte` and `gc_deletes`, cache deletes, service inbox; what KIP-618 does and does not buy |
| [`deep-dives/source-safety-and-slot-budget.md`](deep-dives/source-safety-and-slot-budget.md) | The red node: WAL pinned by the slot, the cap and its budget in hours, idle-database heartbeats, decode on a standby, snapshot load, orphaned slots |
| [`deep-dives/failover-and-recovery.md`](deep-dives/failover-and-recovery.md) | Connector crash, Kafka outage, Postgres failover with failover slots, phantom changes, MySQL GTID failover, lost slot, major version upgrade |
| [`deep-dives/transactions-and-ordering.md`](deep-dives/transactions-and-ordering.md) | Commit order vs per-key order, transaction metadata and buffering at the sink, large transactions and spill, cross-table order, the outbox |
| [`deep-dives/schema-evolution-and-ddl.md`](deep-dives/schema-evolution-and-ddl.md) | How DDL shows up in each log, registry compatibility, expand/contract, the CI gate, DDL during a snapshot |
| [`research/`](research/) | Raw web research with source links and a spot-check section per file. Input to the files above, not study material |
| `cdc-pipeline.excalidraw` | My drawing. Missing until I draw it |
