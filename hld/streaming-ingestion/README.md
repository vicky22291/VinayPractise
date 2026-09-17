# Petabyte batch + streaming ingestion

> One-line answer: put a durable log (Kafka) between every producer and the lake so producers never block and the lake can be behind; run one stateless micro-batch job per pipeline that reads a source offset range, writes immutable Parquet, and commits the files and the source offsets in one atomic table commit (the `txn` marker), so a re-run of any batch is a no-op and the table is exactly-once by construction; land raw data append-only partitioned by ingest time so late events never rewrite history; treat the schema registry as the contract, rescue unknown fields, quarantine bad records, and make replay the same job in bounded mode writing through an atomic partition swap. The thing that breaks first is not throughput, it is the number of files and commits per table.

Tier 2, problem #18 in [`hld/README.md`](../README.md). Asked at Databricks and Confluent as "design a system that ingests 1 PB/day into queryable tables", "design Auto Loader", "design a pipeline from Kafka to the lake with exactly-once", "design a CDC pipeline", or "design Kafka Connect". It is Databricks' product in disguise (Auto Loader, Structured Streaming, Lakeflow Connect) and Confluent's (Connect, Tableflow), so interviewers probe the mechanism: where exactly the commit point is, what a retry does at every hop, what the buffer is when the sink is down, what a schema change does mid-stream. Reusable blocks: [`../delta-lake-transactions/`](../delta-lake-transactions/) (the sink we commit to), [`../../concepts/stream-processing.md`](../../concepts/stream-processing.md) (watermarks, checkpoints, backpressure), [`../../concepts/exactly-once.md`](../../concepts/exactly-once.md) (idempotency, outbox, inbox), [`../../popular_systems_deepdive/kafka/`](../../popular_systems_deepdive/kafka/) (the buffer), [`../distributed-job-scheduler/`](../distributed-job-scheduler/) (who runs the jobs). Sources in [`research/`](research/).

## Problem statement (as asked)

Thousands of producers emit events (clicks, logs, metrics, application events) into Kafka topics; other systems drop files into object storage buckets; operational databases change rows that must be mirrored. Design the platform that lands all of it into queryable lakehouse tables (Delta or Iceberg on S3) at 1 PB/day: no event lost, no event landed twice, fresh within a minute for streams, correct for late and out-of-order events, resilient to a sink that is down for an hour, and safe when a producer changes its schema without telling anyone. Backfills and reprocessing after a bug must be first-class, not a script someone writes at 2am.

## Functional requirements

Core:
- **Stream ingestion.** Kafka topic to table. Every record lands exactly once (as an effect). Freshness under 60 s at p99.
- **File ingestion.** Files landing in a bucket (millions per day, any size) to table. Each file processed exactly once, including when notifications are duplicated or lost.
- **CDC ingestion.** A database table to a mirror table with inserts, updates, deletes applied in per-key order. Initial snapshot plus log tail with no gap and no overlap.
- **Replay and backfill.** Reprocess a time or offset range, or an entire source, into an existing table without duplicating rows and without stalling live ingestion.
- **Schema drift.** Producers add, rename, or retype fields. The pipeline keeps running, nothing is dropped, additive changes flow through automatically, bad records are quarantined and replayable.

Below the line (say it out loud):
- Aggregations, joins, and business transforms. The ingestion layer parses, validates, partitions, and lands. Everything else is a downstream job on the landed table.
- The query engine and the table format internals (log, OCC, checkpoints). We use the commit primitive; see the Delta Lake problem.
- Kafka's own replication and the broker fleet. We size it and set its knobs; see the Kafka deep dive.
- Catalog, lineage, access control. We assume a table name resolves to a path and a policy.
- Sub-second freshness. Micro-batch to an object store commits in seconds; sub-second is a different system (a stream processor with a serving store).

## Non-functional requirements

| Dimension | Target |
|---|---|
| Scale | 1 PB/day raw, ~11.6 GB/s average, 3x daily peak (~35 GB/s). ~10 M events/s average at ~1 KB. 10k pipelines, 10k target tables, ~1,000 Kafka topics, 10 M files/day landing |
| Freshness | Kafka to queryable: p50 under 30 s, p99 under 60 s. Files: under 5 min from arrival. CDC: under 60 s |
| Delivery | Exactly-once effect per record per table. At-least-once at every hop, dedup at the commit point |
| Ordering | Per Kafka partition preserved in the landed data (offset column). Per key for CDC. No global order |
| Availability | Ingestion keeps accepting (Kafka up) at 99.99%. The lake may lag. Sink outage of 1 h is absorbed, 24 h is recoverable |
| Durability | Once a producer gets `acks=all`, the record lands eventually. Retention on the buffer 7 days, so a consumer can be 7 days behind and lose nothing |
| Late data | Any lateness accepted. Nothing dropped at ingestion. Event time preserved, lateness measurable |
| Cost | Under ~2x write amplification (land plus one compaction). File count per table bounded. S3 request cost under storage cost |

## What interviewers probe (the ladder)

1. Where exactly is the commit point? A batch was written to S3 and the job died before recording its offsets. What happens on restart, and why is the table not duplicated?
2. The sink (S3 or the table service) is down for an hour. What backs up, where, and what does recovery look like? What if it is down for 8 days?
3. A record arrives 3 days late. Which partition does it go into, what does it cost, and what does a query for "yesterday" see?
4. A producer adds a field. Then renames one. Then changes `user_id` from int to string. What happens at each step and what does the consumer of the table see?
5. One Kafka partition is 10x hotter than the rest. Why is your freshness p99 now bad, and what do you do?
6. You committed every 5 s to be fresh. After a week the table has 20 M files. Where did the design go wrong?
7. A bug corrupted 6 hours of landed data. Walk me through replaying it while the live stream keeps running, without duplicates.
8. The same file was uploaded twice with different contents. The same S3 notification was delivered twice. A file was overwritten in place. What lands?
9. CDC: the snapshot is running while writes continue. How do you avoid a gap or a double apply at the handoff?
10. Why micro-batch and not a record-at-a-time stream processor for this? When would you switch?

## Files

| File | What it is |
|---|---|
| [`solution.md`](solution.md) | Full HLD in flow-first form: one incremental diagram, one walkthrough per FR, deep dives that mutate the design, then nitty-gritty |
| [`diagrams.md`](diagrams.md) | The D1 to D12 diagram set |
| [`edge-cases.md`](edge-cases.md) | Every "what if" with a 60-second answer and a confidence box |
| [`deep-dives/exactly-once-source-to-table.md`](deep-dives/exactly-once-source-to-table.md) | Every hop from producer to table: where duplicates enter, where they die, the `txn` marker, the file-state store, CDC dedup |
| [`deep-dives/backpressure-lag-and-catch-up.md`](deep-dives/backpressure-lag-and-catch-up.md) | Kafka as the buffer, lag in seconds, rate limits per trigger, sink outage timeline, retention and tiered storage |
| [`deep-dives/late-events-and-event-time.md`](deep-dives/late-events-and-event-time.md) | Ingest-time partitioning, event-time clustering, why no watermark at ingestion, lateness metrics, downstream watermarks |
| [`deep-dives/schema-drift-and-quarantine.md`](deep-dives/schema-drift-and-quarantine.md) | Registry as contract, compatibility modes, rescue column, quarantine table, table evolution, breaking changes |
| [`deep-dives/file-and-cdc-sources.md`](deep-dives/file-and-cdc-sources.md) | Notifications vs listing, file-state store, overwritten files, Debezium snapshot-to-stream handoff, MERGE by (key, lsn) |
| [`deep-dives/sink-commits-small-files-and-cost.md`](deep-dives/sink-commits-small-files-and-cost.md) | The red node: commits and files per table, optimized writes, compaction, request and storage cost |
| [`deep-dives/replay-and-backfill.md`](deep-dives/replay-and-backfill.md) | Same job in bounded mode, staging plus atomic partition swap, Kappa vs Lambda, cost of a replay |
| [`research/`](research/) | Raw web research notes with source links. Input to the files above, not study material |
| `streaming-ingestion.excalidraw` | My drawing. Missing until I draw it |
