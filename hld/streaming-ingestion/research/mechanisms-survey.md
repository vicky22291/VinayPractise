# Streaming Ingestion Platform: Mechanisms Survey

**Last updated:** 2025-02-07  
**Scope:** Kafka, Spark Structured Streaming, Flink, lakehouse layers (Delta/Iceberg/Hudi), CDC, schema evolution, exactly-once semantics.  
**Note:** All defaults are verified from primary sources. [unverified] marks claims unsourced after reasonable search.

## 1. Kafka as the Ingestion Buffer

**Producer config defaults** (Kafka 4.1) [kafka.apache.org/41/configuration/producer-configs]:
- `acks="all"` (equivalent to -1; max durability): leader waits for all in-sync replicas (ISR) to acknowledge
- `enable.idempotence=true` (since Kafka 3.0) [kafka.apache.org/30/getting-started/upgrade]; prevents duplicate messages on retries via producer ID + sequence numbers
- `retries` defaults to MAX_INT when idempotence enabled; allows retry-without-duplication guarantees
- Requires `max.in.flight.requests.per.connection <= 5` and `retries > 0` when idempotence enabled; maintains per-partition ordering

**Broker defaults** [kafka.apache.org/41/configuration/broker-configs]:
- `retention.ms=604800000` (7 days); data older than this is deleted (or tiered to remote)
- `segment.bytes=1073741824` (1 GB); log segment size; retention and cleanup operate at segment granularity
- `min.insync.replicas=1` (broker-level default); **recommend `min.insync.replicas >= 2`** for production ingestion to prevent data loss if leader fails
- For transactional topics: `replication.factor >= 3` and `min.insync.replicas >= 2` required [kafka.apache.org/41/configuration/producer-configs]
- `default.replication.factor=1` (broker default for auto-created topics); rarely suitable for durability-sensitive pipelines
- `transaction.max.timeout.ms=900000` (15 minutes; max transaction duration); if producer requests longer timeout, broker rejects

**Tiered storage (KIP-405):** Production-ready Kafka 3.9+ [cwiki.apache.org/confluence/display/KAFKA/KIP-405:+Kafka+Tiered+Storage]. Enables infinite retention via S3/GCS/Azure. Architecture: segments roll to remote tier when age > `local.retention.ms`. Followers fetch unavailable data transparently. Per-topic flag: `remote.storage.enable=true` (immutable once set). Limitations: incompatible with compacted topics, JBOD layouts.

**Consumer rebalancing:** KIP-848 (GA Kafka 4.0) introduces next-gen cooperative-sticky protocol [cwiki.apache.org/confluence/display/KAFKA/KIP-848]; unlike prior rebalancing, no global stop-the-world barrier. Incremental partition reassignment allows subset of consumers to move partitions while others remain active. Reduces stop-duration from seconds to milliseconds in large groups.

**Consumer config:** `max.poll.records=500` (default) [kafka.apache.org/41/configuration/consumer-configs]. Sets max records returned per poll() call; no impact on fetch size or behavior; tunable for application latency vs throughput trade-off.
- `fetch.max.bytes=52428800` (50 MB default) [kafka.apache.org/41/configuration/consumer-configs]; total bytes fetched per request

**Transactions & isolation (KIP-98, Kafka 0.11+):** [cwiki.apache.org/confluence/display/KAFKA/KIP-98+-+Exactly+Once+Delivery+and+Transactional+Messaging] Transactional producer atomically writes to multiple partitions; either all succeed or all fail (abort). Consumer sees only committed records. 
- Set consumer `isolation.level=read_committed` to skip unaborted messages; reads up to Last Stable Offset (LSO) [kafka.apache.org/40/javadoc/org/apache/kafka/common/IsolationLevel.html]
- Default `isolation.level=read_uncommitted` reads all offsets regardless of commit status; weaker for exactly-once pipelines

**Per-partition throughput:** [unverified] Confluent operational guidance suggests ~10 MB/s sustainable per partition in typical setups; varies with compression (snappy/zstd), batch size (`linger.ms`, `batch.size`), acks mode, `max.in.flight.requests.per.connection`.

## 2. Spark Structured Streaming

**Micro-batch model:** Trigger-based batches with checkpoint-backed recovery [spark.apache.org/docs/latest/structured-streaming-programming-guide]. Each trigger pulls new data from sources, processes stateless and stateful operations, writes results, and commits offsets. Failure recovery replays batch from checkpoint; exactly-once if sink is idempotent or transactional.

**Checkpoint directory layout:** `offsets/` directory stores (source, partition) → latest offset pairs. `commits/` holds batchId → list of actions committed. `state/` contains RocksDB key-value state for joins/aggregations (stores per-key version + removal markers). `metadata/` holds JSON batchMetadata. Required for recovery; never prune during active query.

**Triggers:** 
- `trigger(processingTime("10 seconds"))` (default if not specified) processes new data every 10s regardless of availability
- `availableNow()` (Spark 3.3+) drains all backlog in single batch; useful for backfill or testing
- `trigger(once())` processes available data once and stops; used for batch re-runs

**Rate limiting:** `maxOffsetsPerTrigger` (Kafka), `maxFilesPerTrigger`, `maxBytesPerTrigger` cap batch size. [unverified] Defaults not explicitly documented in guide. Common practice: start with `maxOffsetsPerTrigger=100000` (100k messages/batch).

**Watermarking:** `.withWatermark("event_time", "10 minutes")` defines "arrival delay threshold" [spark.apache.org/docs/latest/structured-streaming-programming-guide]. Triggers state cleanup only for stateful operations (joins, `groupBy`). Late data *older than watermark* is silently dropped **only if operation is stateful**; append-only tables see all data. Global watermark = min(input watermarks) across all sources. `spark.sql.streaming.multipleWatermarkPolicy` controls merge (default: min).

**State store:** Default HDFS-backed (shuffle-safe but slow). RocksDB faster but needs manual `spark.sql.streaming.stateStore.providerClass=org.apache.spark.sql.execution.streaming.state.RocksDBStateStoreProvider`. Incremental state checkpoints reduce checkpoint size. State expiration via watermark or explicit `.dropDuplicates(withWatermark)`.

**Async progress & listener API:** `StreamingQueryListener` hooks into batch start/end events for custom monitoring, alerting. `query.status` reports input rate (rows/sec), batch duration, and staleness.

## 3. Flink Streaming

**Checkpoint mechanism:** Periodic barriers inserted into source streams; all operators receive barrier in order, snapshot state, and flush results downstream before acknowledging. Two modes:
- **Aligned (default):** Operator waits for barrier from all inputs before snapshotting; simple but blocks on slowest input, causing backpressure.
- **Unaligned (FLIP-76, Flink 1.11+):** Snapshot immediately, buffer in-flight records; faster under backpressure but requires larger checkpoint storage [flink.apache.org/2020/10/15/from-aligned-to-unaligned-checkpoints-part-1-checkpoints-alignment-and-backpressure].

**Checkpoint configuration:** `execution.checkpointing.interval` **has no default value** (must be configured explicitly) [nightlies.apache.org/flink/flink-docs-stable/docs/deployment/config/]. Set to trigger interval (e.g., 60000 ms = 60s). Also configure `execution.checkpointing.min-pause` (default 0) for minimum gap between checkpoints.

**RocksDB incremental checkpoints:** By default stores full state snapshots; enable incremental mode to store only deltas since last checkpoint [flink.apache.org/2018/01/30/managing-large-state-in-apache-flink-an-intro-to-incremental-checkpointing]. Reduces checkpoint time, storage, and network overhead; essential for large state (> 1 GB).

**Backpressure & flow control:** Credit-based per-connection flow control (Flink 1.5+) [flink.apache.org/2022/05/23/getting-into-low-latency-gears-with-apache-flink-part-two] allocates credits to upstream to prevent buffer overrun. No global stop-the-world barrier; local operator buffers manage backpressure.

**Exactly-once sink semantics:** Requires two-phase commit: (1) write speculatively during processing, (2) commit only after checkpoint completion via `notifyCheckpointComplete()`. Kafka sink `DeliveryGuarantee.EXACTLY_ONCE` uses Kafka transactions; requires producer `transaction.timeout.ms` > max(`execution.checkpointing.interval`). Kafka broker default `transaction.max.timeout.ms=900000` (15 min) [kafka.apache.org/41/configuration/broker-configs]. If checkpoint exceeds broker limit, transactions abort → data loss.

**Watermarks and late events:** Event time sourced via `WatermarkStrategy`. `allowedLateness(Duration.ofHours(1))` for stateful ops (joins, aggregations) defers state cleanup, accepting late updates. `sideOutputLateData(outputTag)` captures records older than watermark. Watermark = min(operator watermarks) propagates downstream.

## 4. Exactly-Once into Lakehouse

**Delta Lake idempotent writes:** `txn(appId, version)` action in transaction log [delta.io/docs/protocol/latest/actions/] uniquely identifies an application's write attempt. Databricks `foreachBatch` pattern: pass `txnAppId` (UUID, e.g., streaming-job-id) + monotonically-increasing `txnVersion` (checkpoint epoch) to `df.write.option("txnAppId", appId).option("txnVersion", version)` [docs.databricks.com/aws/en/ldp/for-each-batch]. If same (appId, version) replayed, Delta skips write and returns success → idempotent. Works for multi-table writes within single batch; txn log prevents duplicates.

**Iceberg Flink sink exactly-once:** Streams committed checkpoint state; writes speculatively to data files and stores `flink.job-id` + `flink.max-committed-checkpoint-id` in snapshot summary [iceberg.apache.org/docs/latest/flink-writes]. On restore, sink checks summary to detect already-committed checkpoints and skips re-write. **Critical:** Expiring snapshots holding these IDs corrupts state and causes data loss; retention policy must keep last snapshot from Flink job.

**Hudi DeltaStreamer checkpoint:** Stored in commit metadata (`streamer.checkpoint.key` in commit file). Format: `topicName,0:offset0,1:offset1,...` for Kafka sources (per-partition offset tuple); on restart, reads checkpoint from latest commit and resumes [hudi.apache.org/docs/0.10.0/hoodie_deltastreamer]. Supports incremental snapshot (FLIP-27 style "chunk" snapshot) to avoid re-scanning entire table on first ingest.

**Kafka Connect S3 sink exactly-once:** Achieves exactly-once **without transactions** via deterministic partitioning + offset-encoded file naming [docs.confluent.io/kafka-connectors/s3-sink/current/overview.html]. Partitioner (default or field-based) is deterministic—same record set produces identical partition structure. File naming encodes: `<topic>+<partition>+<offset>` so retries overwrite same S3 object. Flush size and schema compatibility determine file rolls. Requires idempotent S3 PutObject (overwrite safety); pre-signed URLs or S3 versioning optional.

## 5. Late Events & Event Time (Append-Only Ingestion)

For append-only ingestion tables (no aggregation, no stateful operations), **watermark is advisory only—no data is dropped** because there is no state to clean. Late-arriving records simply append. Watermark matters only for stateful joins/aggregations (e.g., "count events per hour").

**Partitioning strategy trade-offs:**
- **event_date partitioning:** Group events by occurrence time (e.g., `event_date=2025-02-07`). Late events (arriving days later) must rewrite old partitions—triggers full re-merge/compact of that partition. Cost: O(events in late partition) per late arrival. Severe for high-volume scenarios (100M events/day per partition → re-compact every day). Benefit: query pruning by logic time (`WHERE event_date >= '2025-01-01'` scans only relevant partitions); matches business time.
- **ingestion_date partitioning:** Group by arrival time (e.g., `ingestion_date=2025-02-07`). No rewrites; always append to today's partition. Benefit: no compaction storms; linear scale. Cost: query requires cross-date filtering to reconstruct business time; events scattered across dates; table bloats with "old" partitions.
- **Hybrid (recommended for petabyte scale):** Partition by date AND sort within partition by event time. Allows both fast business-time queries AND append-only writes. Delta/Iceberg liquid clustering ([docs.databricks.com/aws/en/tables/liquid-clustering]) enables this without explicit partition key.

**Hidden partitioning (Iceberg, Delta):** [iceberg.apache.org/docs/latest/configuration] Transforms like `days(event_ts)` decouple partitioning from schema—SQL sees `event_ts` column, Iceberg manages partition folders transparently. Avoids application-side date arithmetic. Example: `PARTITION BY days(event_time)` creates `event_time_year=2025/month=2/day=7/` structure automatically. On late-arriving event, Iceberg rewrites only the affected partition folder, not the whole table.

**Retention and TTL:** Set `minWriterVersion >= 7` (Iceberg) or Delta `deletedFile` support to prune old partitions (e.g., keep 2 years, drop older). Critical for petabyte tables.

## 6. Schema Drift & Evolution

**Confluent Schema Registry (default BACKWARD):** [docs.confluent.io/platform/current/schema-registry/fundamentals/schema-evolution.html]
- Compatibility mode = `BACKWARD` (non-transitive, default): new schema checked only vs latest prior schema. Allows: add optional fields (backward-readable by old consumers), remove optional/required fields (requires defaults).
- Other modes: `FORWARD` (old consumers read new data), `FULL` (both), `BACKWARD_TRANSITIVE` (all prior versions).
- Avro, Protobuf, JSON schema formats supported; JSON has fewer guarantees than Avro due to type system.
- Default mode prevents consumer rewinding to topic start; old data may fail parse under new schema if not backward-compatible.

**Delta Lake schema evolution:** [docs.databricks.com/aws/en/tables/update-schema]
- `.option("mergeSchema", "true")` per-write enables additive schema changes (new columns appended)
- `spark.databricks.delta.schema.autoMerge.enabled=true` applies globally (not recommended for production—may silently add unexpected columns)
- `.option("overwriteSchema", "true")` replaces entire schema on overwrite (destructive; use with care)
- Raises error if write has incompatible change (e.g., type mismatch on existing column) unless mergeSchema/overwriteSchema enabled

**Auto Loader schema evolution:** [docs.databricks.com/aws/en/ingestion/cloud-object-storage/auto-loader/schema]
- `cloudFiles.schemaEvolutionMode="rescue"` captures schema mismatches (extra fields, type changes) in `_rescued_data` JSON column; main schema unchanged
- `cloudFiles.schemaEvolutionMode="addNewColumnsWithTypeWidening"` (Databricks Runtime 16.4+) adds missing columns + widening (int→long, float→double)
- Combines with `rescuedDataColumn` rename option to control rescued column name

**Iceberg schema evolution:** [iceberg.apache.org/docs/latest/configuration] Column IDs immutable per spec; adding/removing columns is rewrite-free because data files still map by ID, not name. Type widening (int→long) safe. Renaming and dropping columns safe—schema evolution does not require data rewrite.

## 7. Files Landing in Object Storage

**S3 event notifications:** [docs.aws.amazon.com/AmazonS3/latest/userguide/EventNotifications.html] Delivers at-least-once to SQS/SNS/EventBridge on s3:ObjectCreated or s3:ObjectDeleted events. Typical latency: seconds (occasionally minute+). **Important:** At-least-once means duplicates possible (retry storms, multiple notifiers). Requires downstream idempotency or file-state store (e.g., processed file registry in DynamoDB/RDS) to skip re-ingestion.

**Delivery guarantees:** S3 event notifications do NOT guarantee order. EventBridge buffers and retries failures; SQS/SNS best-effort. No guarantee of delivery for all events (e.g., high-load scenarios). Historical note: S3 eventually-consistent before Dec 2020; had complex read-after-write race windows. **S3 now strong-consistent as of Dec 1, 2020** [aws.amazon.com/about-aws/whats-new/2020/12/amazon-s3-now-delivers-strong-read-after-write-consistency-automatically-for-all-applications]—PUT→GET/LIST immediately reflect changes.

**S3 LIST cost:** $0.005 per 1,000 requests [aws.amazon.com/s3/pricing]. Lists return up to 1,000 keys per page; pagination required for large prefixes. Polling-based ingestion (e.g., list every 5 min) incurs cost. Example: 1M files listed = $5/month. Delta Lake's `cloudFiles.useNotifications=true` prefers SQS notification to polling.

**File-state store pattern:** Track (bucket, key, mtime/etag) in external store (DDB, Postgres, etc.). On notification/poll, check state before re-ingesting. Deduplicates retries, late notifications, and manual re-runs. State TTL (e.g., 90 days) prevents unbounded growth.

## 8. CDC as a Source (Debezium)

**Snapshot modes:** [debezium.io/blog/2021/10/07/incremental-snapshots]
- **Initial (monolithic):** Scans entire table once; blocks log streaming. Suitable for small tables only.
- **Incremental (chunked, FLIP-27 style):** Partitions table into chunks (e.g., by PK range or MOD), snapshots each chunk while log streaming continues unblocked. Low/high watermarks inserted per chunk; log changes captured between markers, reconciled with snapshot on apply.

**Log position tracking:** Database-specific offset:
- **Postgres:** LSN (Log Sequence Number); immutable, monotonic. `replication slot` prevents log truncation during streaming.
- **MySQL:** GTID set or binlog file/offset; GTIDs easier for multi-source replicas.
- **MongoDB:** Timestamp + txn oplog order; collections (replica set changes) replayed.

**Transaction boundaries & ordering:** Per-key ordering guaranteed within transaction; cross-key ordering within txn not guaranteed by CDC (Postgres LSN order maintained, but application order within txn varies). Apply as MERGE: `ON key MATCHED → UPDATE (latest by LSN/GTID) WHEN NOT MATCHED → INSERT, on DELETE → tombstone` (special marker row) to handle deletes durably.

**Dead-letter pattern:** Failed CDC records (parse errors, constraint violations) → dedicated dead-letter topic/table. Enables restart without blocking ingestion. Example: Debezium error handler config `error.handler.mode=fail` (stop) vs `skiplist` (skip).

## 9. Backpressure & Lag

**Consumer lag metrics:** [kafka.apache.org/41/configuration/consumer-configs, github.com/linkedin/Burrow]
- **Lag in offsets:** current topic end offset - consumer committed offset; counts records not yet consumed.
- **Lag in seconds (time-based):** approximated by comparing record timestamp to now; more intuitive for alerts ("5 minutes behind live").
- Metric `records-lag-max` per-partition; aggregated per-group for monitoring dashboard.

**Kafka retention as the buffer:** Kafka's retention policy (retention.ms = 7 days default) is the true buffer. Consumer lag must not exceed retention, else records pruned before read → unrecoverable data loss. On data loss, consumer's committed offset points to missing data; `auto.offset.reset=earliest` fails (earliest no longer exists), `auto.offset.reset=latest` skips to tail (loses records). 

**Lag evaluation (Burrow pattern):** [github.com/linkedin/Burrow] Burrow consumes from `__consumer_offsets` topic, evaluates lag vs topic size, assigns status: OK (catching up), warning (stalled but not losing), error (losing data). Rules configurable (e.g., lag > 10min → error). Solves manual threshold problem (not all consumers have same latency SLO).

**Backpressure flow:** Lag signals consumer slowness. Streaming pipeline slowness propagates backward (Flink/Spark poll slower) → Kafka producer buffers fill (if producer is source) → producer rate limits or fails. In fan-out scenarios (multiple consumers), one slow consumer does not block others (Kafka separates per-group state).

## 10. Small Files & Compaction

**Delta Lake OPTIMIZE:** [docs.databricks.com/aws/en/tables/tune-file-size] Merges small files into target size `spark.databricks.delta.optimize.maxFileSize=1073741824` (1 GB, default). Also reorders by clustering key if specified. Auto-compaction (`autoCompact = true`, default) runs lightweight optimize on every write; optimized writes (`optimizeWrite = true`) writes directly to target size (slower writes, no compaction later). Skips partitions with unchanged data.

**Iceberg:** `rewrite_data_files` action targets `write.target-file-size-bytes` [iceberg.apache.org/docs/latest/configuration]. [unverified] Defaults to 512 MB in some docs, though examples show 500 MB. Uses `BinPackStrategy` or `SortStrategy` to co-locate sorted data. Can run async (background job) or inline. Unlike Delta, immutable snapshots decouple schema from files—schema evolution has zero rewrite cost.

**Hudi:** [hudi.apache.org/docs/next/clustering]
- **Clustering:** Asynchronous table service; rewrites small files into larger layout (e.g., CoW or MoR). Action type "REPLACE" marks rewritten files. Can run async without blocking ingestion.
- **Compaction:** MoR-table-only; merges row-based delta logs (`log_` files) with columnar base files periodically. Balances write amplification vs read latency.

**Parquet file format:** [parquet.apache.org/docs/file-format/configurations] Recommendation for large sequential IO: row group size 512 MB–1 GB (not 128 MB). Larger row groups enable larger column chunks, reduce I/O count, improve compression ratios. Column chunk size defaults to row group size. Trade-off: larger row groups require more buffering during write.

**Small file cost in practice:** ~50k small files (< 10 MB) = listing cost + metadata overhead. Compact to < 10k files (100 MB+ each) for optimal query performance. Too-large files (> 1 GB) slow down parallel reads; sweet spot 128 MB–1 GB per file.

## Critical Configuration Patterns for Petabyte Scale

**Kafka durability stack:**
1. Producer: `acks="all"` + `enable.idempotence=true` + `linger.ms=10–100`
2. Broker: `min.insync.replicas >= 2` + `replication.factor >= 3` + `retention.ms` >= max(consumer lag)
3. Consumer: `isolation.level="read_committed"` if using transactions; otherwise default OK
4. Risk: If lag exceeds retention, data lost forever; Burrow alerts critical for this.

**Spark Structured Streaming checkpointing (for exactly-once to lakehouse):**
1. Set `checkpoint()` to distributed storage (S3, HDFS, ADLS) with strong consistency
2. Enable autosave of checkpoint location (prevents accidental data loss on restart)
3. Idempotent sink: use `foreachBatch` with Delta `txnAppId` pattern or Iceberg Flink sink
4. Monitor checkpoint duration; if > trigger interval, adjust trigger or add parallelism

**Flink end-to-end exactly-once:**
1. Set `execution.checkpointing.interval` 30–60 sec (trade-off: latency vs checkpoint overhead)
2. Enable incremental checkpoints: `state.backend.rocksdb.checkpoint.dir` + incremental mode
3. Kafka sink: set `DeliveryGuarantee.EXACTLY_ONCE` + `transaction.timeout.ms > checkpoint interval` (or use database transaction sink)
4. Test checkpoint recovery before production; unaligned checkpoints can hide ordering bugs.

**Lakehouse file sizing (petabyte scale):**
1. Target 256–512 MB per file (not 1 MB, not 10 GB). Balances read parallelism + metadata overhead.
2. Enable auto-compaction (Delta) or rewrite_data_files (Iceberg) on schedule.
3. Monitor file count: > 10k files triggers query slowdown; compact every 1–7 days depending on ingest rate.
4. Use hidden partitions (Iceberg) or clustering (Delta liquid clustering) to co-locate related data.

**Schema evolution safety:**
1. Set Schema Registry to BACKWARD (default), never NONE. Adds validation checkpoint.
2. Delta: use `.option("mergeSchema", "true")` per-write (explicit, safe) not global autoMerge (implicit, risky).
3. Auto Loader: set `cloudFiles.schemaEvolutionMode="rescue"` to capture unparseable rows in `_rescued_data`.
4. Iceberg: schema evolution is rewrite-free by design; safe to rename/drop columns.

---

## Sources

| ID | Title | URL | Used For |
|----|-------|-----|----------|
| 1 | Apache Kafka 4.1 Producer Configs | https://kafka.apache.org/41/configuration/producer-configs/ | acks, enable.idempotence defaults |
| 2 | Apache Kafka 3.0 Upgrade Guide | https://kafka.apache.org/30/getting-started/upgrade/ | enable.idempotence=true since 3.0 |
| 3 | Apache Kafka 4.1 Broker Configs | https://kafka.apache.org/41/configuration/broker-configs/ | retention.ms, segment.bytes, transaction.max.timeout.ms, min.insync.replicas |
| 4 | KIP-405: Kafka Tiered Storage | https://cwiki.apache.org/confluence/display/KAFKA/KIP-405:+Kafka+Tiered+Storage | Remote tier archival details |
| 5 | KIP-848: Consumer Rebalance Protocol | https://cwiki.apache.org/confluence/display/KAFKA/KIP-848 | Cooperative-sticky rebalance |
| 6 | Apache Kafka 4.1 Consumer Configs | https://kafka.apache.org/41/configuration/consumer-configs/ | max.poll.records=500 |
| 7 | KIP-98: Exactly Once Delivery | https://cwiki.apache.org/confluence/display/KAFKA/KIP-98 | Transactional messaging |
| 8 | Kafka IsolationLevel | https://kafka.apache.org/40/javadoc/org/apache/kafka/common/IsolationLevel.html | isolation.level=read_committed |
| 9 | Spark Structured Streaming Programming Guide | https://spark.apache.org/docs/latest/structured-streaming-programming-guide.html | Checkpoint, watermark, triggers |
| 10 | Flink Checkpointing Docs | https://nightlies.apache.org/flink/flink-docs-stable/docs/deployment/config/ | execution.checkpointing.interval (no default) |
| 11 | Flink Incremental Checkpointing | https://flink.apache.org/2018/01/30/managing-large-state-in-apache-flink-an-intro-to-incremental-checkpointing | RocksDB incremental checkpoints |
| 12 | Flink Low-Latency Part 2 | https://flink.apache.org/2022/05/23/getting-into-low-latency-gears-with-apache-flink-part-two | Credit-based flow control |
| 13 | Iceberg Flink Writes | https://iceberg.apache.org/docs/latest/flink-writes/ | flink.job-id, flink.max-committed-checkpoint-id |
| 14 | Hudi DeltaStreamer | https://hudi.apache.org/docs/0.10.0/hoodie_deltastreamer/ | Checkpoint storage in commit metadata |
| 15 | Confluent S3 Sink Connector | https://docs.confluent.io/kafka-connectors/s3-sink/current/overview.html | Exactly-once via deterministic partitioning |
| 16 | Confluent Schema Registry Evolution | https://docs.confluent.io/platform/current/schema-registry/fundamentals/schema-evolution.html | BACKWARD mode default |
| 17 | Iceberg Configuration | https://iceberg.apache.org/docs/latest/configuration/ | write.target-file-size-bytes |
| 18 | Databricks Auto Loader Schema | https://docs.databricks.com/aws/en/ingestion/cloud-object-storage/auto-loader/schema | cloudFiles.schemaEvolutionMode, _rescued_data |
| 19 | Databricks Delta Schema Evolution | https://docs.databricks.com/aws/en/tables/update-schema | mergeSchema, overwriteSchema, autoMerge |
| 20 | Databricks Delta Tune File Size | https://docs.databricks.com/aws/en/tables/tune-file-size | OPTIMIZE maxFileSize=1 GB default |
| 21 | Debezium Incremental Snapshots | https://debezium.io/blog/2021/10/07/incremental-snapshots/ | Watermarking strategy |
| 22 | AWS S3 Event Notifications | https://docs.aws.amazon.com/AmazonS3/latest/userguide/EventNotifications.html | At-least-once delivery |
| 23 | AWS S3 Strong Consistency | https://aws.amazon.com/about-aws/whats-new/2020/12/amazon-s3-now-delivers-strong-read-after-write-consistency-automatically-for-all-applications | Dec 2020 announcement |
| 24 | AWS S3 Pricing | https://aws.amazon.com/s3/pricing/ | LIST operation $0.005 per 1k requests |
| 25 | LinkedIn Burrow | https://github.com/linkedin/Burrow | Consumer lag monitoring |
| 26 | Hudi Clustering & Compaction | https://hudi.apache.org/docs/next/clustering/ | Small file handling |
| 27 | Parquet File Format | https://parquet.apache.org/docs/file-format/configurations/ | Row group size recommendations |

## Defaults and Numbers Reference Table

| Knob or Number | Value | Source ID | Notes |
|---|---|---|---|
| `acks` (Kafka producer) | "all" | 1 | Max durability (equivalent to -1) |
| `enable.idempotence` (Kafka producer) | true | 2 | Since Kafka 3.0 prevents duplicates on retry |
| `retries` (Kafka producer) | MAX_INT | 2 | When idempotence enabled; auto-retry forever |
| `max.in.flight.requests.per.connection` | ≤ 5 | 1 | With idempotence; maintains per-partition order |
| `linger.ms` (Kafka producer) | 0 (default) | 1 | Set 10–100 ms to batch more efficiently |
| `batch.size` (Kafka producer) | 16 KB | 1 | Default batch buffer before send |
| `compression.type` (Kafka producer) | "none" | 1 | Set "snappy" or "zstd" to reduce size 5–10x |
| `retention.ms` (Kafka topic) | 604800000 (7 days) | 3 | Broker default; true retention buffer |
| `segment.bytes` (Kafka topic) | 1073741824 (1 GB) | 3 | Log segment size; retention granularity |
| `default.replication.factor` (Kafka broker) | 1 | 3 | Broker default; rarely suitable for durability |
| `min.insync.replicas` (Kafka broker) | 1 | 3 | Broker default; recommend ≥ 2 in production |
| `transaction.max.timeout.ms` (Kafka broker) | 900000 (15 min) | 3 | Max transactional write duration allowed |
| `max.poll.records` (Kafka consumer) | 500 | 6 | Records per poll() call; tune for latency/throughput |
| `fetch.max.bytes` (Kafka consumer) | 52428800 (50 MB) | 6 | Total bytes fetched per request |
| `isolation.level` (Kafka consumer) | "read_uncommitted" | 8 | Default; set "read_committed" for txn-only reads |
| `local.retention.ms` (KIP-405 tiered storage) | [no global default] | 4 | Per-broker/topic setting; required for tiering |
| `remote.storage.enable` (KIP-405 per-topic) | false | 4 | Immutable once set to true; enables S3/GCS archival |
| `trigger(processingTime)` (Spark Streaming) | 10 seconds | 9 | Default batch interval if unspecified |
| `trigger(once())` (Spark Streaming) | single batch | 9 | Run once then stop; for batch re-runs |
| `execution.checkpointing.interval` (Flink) | [no default; must set] | 10 | Critical; enables state recovery |
| `execution.checkpointing.min-pause` (Flink) | 0 ms | 10 | Minimum gap between consecutive checkpoints |
| `state.backend` (Flink) | jobmanager (memory) | 10 | Set rocksdb for production state > 1 GB |
| `transaction.timeout.ms` (Flink Kafka sink EXACTLY_ONCE) | [must exceed checkpoint interval] | 3 | Critical; prevents txn abort on slow checkpoints |
| `spark.databricks.delta.optimize.maxFileSize` | 1073741824 (1 GB) | 20 | OPTIMIZE target file size |
| `spark.databricks.delta.autoCompact.enabled` | true | 20 | Auto-compact after every write (default) |
| `spark.databricks.delta.optimizedWrite.enabled` | false | 20 | Write directly to target size (slower writes) |
| `write.target-file-size-bytes` (Iceberg) | [unverified; 500 MB in examples] | 17 | Target for rewrite_data_files |
| Parquet row group size (recommended) | 512 MB–1 GB | 27 | Recommended; larger allows better compression |
| Parquet column chunk size | = row group size | 27 | Enables larger sequential IO |
| S3 LIST cost | $0.005 per 1,000 | 24 | Example: 1M files = $5/month |
| S3 event notification delivery | at-least-once | 22 | Requires idempotency or state store |
| S3 strong consistency | Since Dec 1, 2020 | 23 | All GET/PUT/LIST immediately consistent |
| Schema Registry default compatibility | BACKWARD | 16 | Non-transitive; checks only latest schema |
| Kafka retention << consumer lag | Data loss | 25 | auto.offset.reset=earliest/latest both fail |
| Consumer lag (records-lag-max) | Per-partition metric | 25 | Lag = current offset - committed offset |
| Burrow lag status | OK/warning/error | 25 | Auto-evaluated; no manual thresholds needed |

---

## Spot-check corrections (added after review, 2026-09-17)

Checked by fetching the primary pages directly. Rows above that disagree with this table are wrong; the values here are the ones used in `solution.md`.

| Claim above | Correction | How verified |
|---|---|---|
| `trigger(processingTime)` default "10 seconds" | Wrong. With no trigger specified, Structured Streaming runs micro-batches back to back: "micro-batches will be generated as soon as the previous micro-batch has completed processing". There is no 10 s default | Structured Streaming programming guide, Triggers table (https://spark.apache.org/docs/latest/structured-streaming-programming-guide.html#triggers) |
| `spark.databricks.delta.autoCompact.enabled` "true (default)" | Not a global default. Auto compaction is a table property (`delta.autoOptimize.autoCompact`) or session setting; `true` means target 128 MB, `auto` autotunes, and Databricks now recommends autotuning / predictive optimization on Unity Catalog managed tables rather than a hard-coded flag | https://docs.databricks.com/aws/en/delta/tune-file-size (fetched, "true: Use 128 MB as the target file size") |
| `spark.databricks.delta.optimizedWrite.enabled` "false" | Optimized writes are enabled by default for MERGE, UPDATE and DELETE with subqueries, and for CTAS and INSERT on SQL warehouses. Target when on: 128 MB. For a plain streaming append, set it explicitly | Same page: "Optimized writes are enabled by default for the following operations: MERGE, UPDATE with subqueries, DELETE with subqueries" |
| OPTIMIZE target "1 GB default" | The session default `spark.databricks.delta.optimize.maxFileSize` is 1 GB, but Databricks autotune sets the target by table size: 256 MB under 2.56 TB, growing linearly to 1 GB at 10 TB, 1 GB above | Same page, "Autotune file size based on table size" table |
| Iceberg `write.target-file-size-bytes` "[unverified; 500 MB]" | 536870912 bytes (512 MB) | https://iceberg.apache.org/docs/latest/configuration/ (fetched, write properties table) |
| `linger.ms` default 0 | 0 before Kafka 4.0. KIP-1030 raised the producer default to 5 ms in 4.0 [check the release you run] | Kafka 4.0 release notes / KIP-1030 [unverified in this session] |
| Broker failure detection | KRaft: `broker.session.timeout.ms` = 9000 (9 s). ZooKeeper mode: `zookeeper.session.timeout.ms` = 18000 (18 s) | Kafka broker config docs (https://kafka.apache.org/documentation/#brokerconfigs) |
| Per-partition throughput rule of thumb | Still [unverified] as a published number. Used in `solution.md` as an engineering heuristic (5 to 10 MB/s per partition ingress with headroom), stated as such |  |
