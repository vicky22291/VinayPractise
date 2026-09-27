# CDC Mechanisms Survey: September 2026

**Scope:** Mechanisms of change data capture from PostgreSQL and MySQL into Kafka and downstream sinks.  
**Versions covered:** PostgreSQL 13–18, MySQL 8.0–8.4, Debezium 2.x–3.x, Kafka 3.x–4.x, Flink CDC 3.x.

**Consistency model summary:** CDC typically provides *at-least-once* semantics from source to Kafka (events may be replayed on failure). Exactly-once from source to sink is possible using KIP-618 (Kafka 3.3+) + Debezium exactly-once support (2.3+) + idempotent sink (upsert with version/LSN guard). Within Kafka, per-key ordering is guaranteed by partitioning; global transaction order is *not* guaranteed (see transaction metadata topic for reconstruction). Sinks must handle out-of-order events (e.g., DELETE before INSERT due to replay) or use transaction boundaries to batch atomic changes.

---

## 1. PostgreSQL Logical Decoding

**Replication slots** track the position in the WAL, preventing premature deletion. Slots are crash-safe, persist independently of consumer connections, and emit each change exactly once in normal operation ([logical decoding concepts](https://www.postgresql.org/docs/18/logicaldecoding-explanation.html)). Key LSN fields tracked in `pg_replication_slots`:
- `restart_lsn`: Earliest LSN the slot needs to retain ([pg_replication_slots view](https://www.postgresql.org/docs/18/view-pg-replication-slots.html)) — defines the lower bound of WAL the slot pins.
- `confirmed_flush_lsn`: Position the consumer has safely processed; logical slot flushes this back during decoding.
- `wal_status`: Five states: reserved (normal), extended (above max\_slot\_wal\_keep\_size), unreserved (low WAL), lost (unrecoverable overflow), ([replication config](https://www.postgresql.org/docs/current/runtime-config-replication.html)).

**Key WAL retention parameters:**
- `max_slot_wal_keep_size` (default [−1 = unlimited](https://www.postgresql.org/docs/18/runtime-config-replication.html)): [Introduced PG13](https://www.postgresql.org/docs/13/runtime-config-replication.html). Sets hard limit on WAL per slot at checkpoint time; exceeding it marks slot invalid and requires re-snapshot.
- `logical_decoding_work_mem` (default [64 MB](https://www.postgresql.org/docs/18/runtime-config-resource.html), [PG13+](https://www.postgresql.org/docs/13/runtime-config-resource.html)): Memory before spilling to disk during logical decoding of a single transaction.
- `idle_replication_slot_timeout` ([PG18+](https://www.postgresql.org/docs/18/runtime-config-replication.html), default [0 = disabled](https://www.postgresql.org/docs/18/runtime-config-replication.html)): Invalidates slots unused for specified duration; invalidation checked at checkpoint, not in real-time.
- `wal_sender_timeout` (default [60 seconds](https://www.postgresql.org/docs/18/runtime-config-replication.html)): Terminates idle replication connections; fails streaming if no feedback for this duration.

**pgoutput output plugin protocol versions** ([logical streaming replication protocol](https://www.postgresql.org/docs/18/protocol-logical-replication.html)):
- v1: Base monolithic transaction streaming.
- v2 ([PG14+](https://www.postgresql.org/docs/18/protocol-logical-replication.html)): Streaming of large in-progress transactions (BEGIN…CHANGE…COMMIT); prevents subscriber memory exhaustion.
- v3 ([PG15+](https://www.postgresql.org/docs/18/protocol-logical-replication.html)): Two-phase commit support (PREPARE before COMMIT); enables crash-safe logical replication subscribers.
- v4 ([PG16+](https://www.postgresql.org/docs/18/protocol-logical-replication.html)): Parallel apply hint for streamed transactions (extra sequencing metadata); subscribers can apply changes in parallel.

**Failover slots & standby logical decoding** ([PG17+](https://www.postgresql.org/docs/17/logical-replication-failover.html)): Slot synchronization from primary to hot standby using `sync_replication_slots=true` on standby, `primary_slot_name` for physical replication slot linkage, and `hot_standby_feedback=on` for visibility. Primary uses `synchronized_standby_slots` to wait for physical standby acknowledgment before advancing logical slot position.

**REPLICA IDENTITY** modes ([logical replication publication](https://www.postgresql.org/docs/18/logical-replication-publication.html)) control old-row image content in UPDATE/DELETE:
- DEFAULT (primary key if exists): Old values only if table has PK; UPDATE sends only changed columns, DELETE sends nothing (must match PK).
- FULL: All columns in before image; UPDATE sends all old columns, DELETE sends full old row.
- USING INDEX idx: Columns in specified unique index used as key.
- NOTHING: UPDATE/DELETE blocked on tables in publications.

**TOAST handling:** PostgreSQL stores large values (>~8 KB) using TOAST. Unchanged TOAST columns omitted from UPDATE replication unless `REPLICA IDENTITY FULL` ([Debezium TOAST strategy](https://debezium.io/blog/2019/10/08/handling-unchanged-postgres-toast-values/)). Debezium represents missing values with placeholder string, default `__debezium_unavailable_value` (configurable via `toasted.value.placeholder` in pgoutput options; also exposed as SMT ReselectColumnsPostProcessor for lazy re-query).

**Publications and filtering** ([PG publication syntax](https://www.postgresql.org/docs/18/logical-replication-publication.html)): `CREATE PUBLICATION` can specify:
- FOR ALL TABLES: All tables in all schemas (default).
- FOR TABLE table1, table2: Specific tables.
- WITH (publish = 'insert, update, delete'): Filter by operation type (default: all).
- Row filters ([PG15+](https://www.postgresql.org/docs/15/release-15.html)): `CREATE PUBLICATION ... FOR TABLE tbl WHERE (age > 18)` captures only rows matching predicate.
- Column lists ([PG15+](https://www.postgresql.org/docs/15/release-15.html)): `FOR TABLE tbl (id, name)` replicates only specified columns.

Filtering reduces replication volume but requires downstream schema awareness; dropped columns must be handled via SMTs.

---

## 2. MySQL Binlog

**Key configuration defaults** ([MySQL 8.0–8.4 replication options](https://dev.mysql.com/doc/refman/8.4/en/replication-options-binary-log.html)):
- `binlog_format=ROW` (default): Row-based binary logging; statement and mixed modes not recommended for CDC. Ensures each row change is logged explicitly, not as SQL statements.
- `binlog_row_image=full` (default): Log all columns in row image (before and after). MINIMAL (only changed columns) and NOBLOB (excludes unchanged BLOBs) reduce log size but complicate CDC.
- `binlog_row_metadata=MINIMAL` (default); `FULL` [available 8.0.1+](https://dev.mysql.com/doc/mysql-replication-excerpt/8.0/en/replication-options-binary-log.html). FULL metadata includes original column names, visibility flags, and type information — essential for CDC to handle schema changes and column renames without ambiguity.
- `binlog_expire_logs_seconds=2592000` ([30 days, default since 8.0.11](https://dev.mysql.com/doc/refman/8.0/en/purge-binary-logs.html)). Automatic purge of binary logs older than this duration. Debezium must consume faster than purge rate or position becomes unreachable.
- `binlog_transaction_compression` ([8.0.20+](https://dev.mysql.com/doc/refman/8.0/en/binary-log.html)): Optional compression of binlog events; configurable at session or global level.

**GTID (Global Transaction ID)** ([GTID format and concepts](https://dev.mysql.com/doc/refman/8.4/en/replication-gtids-concepts.html)): Unique identifier (source_id:transaction_id) for every committed transaction, persisting across failover. File/offset positions are node-specific and become invalid after promotion/failover. GTID-based CDC allows transparent handling of replica topology changes. Enable via `gtid_mode=ON` and `enforce_gtid_consistency=ON`. Tagged GTIDs ([8.4+ feature](https://dev.mysql.com/doc/refman/8.4/en/replication-gtids-concepts.html)) allow user-defined tags for application grouping.

---

## 3. Debezium (3.x current)

**Event envelope structure** ([PostgreSQL connector](https://debezium.io/documentation/reference/stable/connectors/postgresql.html)):
- `op` (single char): c (INSERT/snapshot), u (UPDATE), d (DELETE), r (snapshot read), t (TRUNCATE), m (metadata).
- `before`, `after`: Old/new row values (NULL if not applicable).
- `source.lsn`: PostgreSQL WAL LSN; MySQL binlog file+position.
- `source.txId`: Transaction ID (PG) or GTID (MySQL).
- `source.ts_ms`: Database commit timestamp in ms.
- `ts_ms`: Debezium event timestamp (ingest time).
- `transaction.id`, `transaction.total_order`, `transaction.data_collection_order`: When `provide.transaction.metadata=true`.

**Offset tracking & at-least-once semantics:** Debezium persists offsets in Kafka Connect's internal offset topic, committed after producer acknowledges the batch. On restart, connector resumes from last committed offset, replaying events from that LSN/position forward ([exactly-once delivery](https://debezium.io/documentation/reference/configuration/eos.html)). Postgres slot's `confirmed_flush_lsn` lags the Kafka offset by a full batch (typically ~2 seconds to batch size × poll interval).

**Exactly-once delivery** ([KIP-618 support](https://debezium.io/blog/2023/06/22/towards-exactly-once-delivery/), [available since Debezium 2.3](https://debezium.io/blog/2023/06/21/debezium-2-3-final-released/)): Debezium connectors use transactional producer per task; offsets and data written in same Kafka transaction. Requires worker-level `exactly.once.support=enabled` ([Kafka 3.3+](https://kafka.apache.org/43/kafka-connect/connector-development-guide/)); no per-connector flag needed.

**Snapshot modes** ([snapshot.mode property](https://debezium.io/documentation/reference/stable/connectors/mysql.html)):
- `initial` (default): Full consistent snapshot of all tables, then stream from binlog/WAL.
- `no_data`: Capture schema only, skip initial data; begin streaming from current position.
- `when_needed`: Snapshot only if connector detects lost or skipped events (recovery scenario).
- `recovery`: Dedicated recovery snapshot mode (replaced deprecated schema_only_recovery in v3.0).
- `always`: Re-snapshot on every restart (not recommended for production).

**Incremental snapshots** ([DBLog watermark algorithm](https://debezium.io/blog/2021/10/07/incremental-snapshots/)): Chunk tables by primary key range, enabling parallel snapshot reads without blocking replication. Uses signal table (configurable via `signal.data.collection`) to emit watermark signals (snapshot-window-open before chunk, snapshot-window-close after). Debezium computes low watermark (LW = binlog LSN at snapshot start) and high watermark (HW = LSN after last chunk read), then backfills changes in range [LW, HW) per chunk. `incremental.snapshot.chunk.size` [default 1024 rows](https://debezium.io/documentation/reference/stable/connectors/mysql.html). Can be triggered ad-hoc via signaling table.

**Transaction metadata topic** ([transaction events](https://debezium.io/documentation/reference/stable/connectors/postgresql.html)): When `provide.transaction.metadata=true`, emits separate events to `<topic.prefix>.transaction` with BEGIN (at first change in transaction) and END (at commit). Each event contains: `status` (BEGIN/END), `id` (txn ID), `event_count` (total rows), `ts_ms` (commit time), `data_collections` (array of affected tables + their event counts).

**Heartbeat mechanism:** `heartbeat.interval.ms` > 0 enables periodic heartbeat events to prevent idle slot timeout on low-traffic databases. `heartbeat.action.query` (e.g., INSERT/UPDATE to a heartbeat table) generates a WAL record, advancing LSN and keeping the slot active.

**Performance configuration** ([default values](https://debezium.io/documentation/reference/stable/connectors/mysql.html)):
- `max.batch.size` [default 2048](https://debezium.io/documentation/faq/): Max records polled per batch before flushing to Kafka.
- `max.queue.size`: In-memory event buffer size (spills to disk when full).
- `tombstones.on.delete` (default true): Emit tombstone (null value) after DELETE for log compaction.

**Debezium Server** ([standalone runtime](https://debezium.io/documentation/reference/stable/operations/debezium-server.html)): Embedded alternative to Kafka Connect for non-Kafka sinks (Kinesis, Google Pub/Sub, Apache Pulsar, Redis Streams, RabbitMQ, HTTP webhooks). Built on Quarkus; single-process, containerizable, lightweight.

**JDBC sink connector** ([upsert capability](https://debezium.io/documentation/reference/stable/connectors/jdbc.html)): `insert.mode=upsert` translates CDC events to database-specific upsert SQL (MERGE, ON CONFLICT, etc.); `delete.enabled=true` executes DELETE for CDC delete events. Supports batch inserts via `batch.size`. Enables self-hosted Kafka-less CDC (via Debezium Server) to any JDBC-compatible database.

**Debezium SMTs (Single Message Transforms):** Post-processing of CDC events:
- [Route by field](https://debezium.io/documentation/reference/stable/transformations/content-based-routing.html): Route to different topics based on value (e.g., customer_id mod 10).
- [Outbox event router](https://debezium.io/documentation/reference/stable/transformations/outbox-event-router.html): Extract payload from outbox table, route by aggregate type.
- [Extract new record state](https://debezium.io/documentation/reference/stable/transformations/event-flattening.html): Flatten nested CDC envelope to bare record (useful for sinks expecting flat schema).
- [Reselect columns](https://debezium.io/documentation/reference/stable/post-processors/reselect-columns.html): Re-query source for unavailable values (e.g., TOAST placeholders, confidential columns).

---

## 4. Kafka Side

**KIP-618 exactly-once source connectors** ([shipped Kafka 3.3](https://kafka.apache.org/43/kafka-connect/connector-development-guide/)): Kafka Connect uses a transactional producer per task. Data records and offsets are written within a single Kafka transaction, ensuring atomicity: either both commit or both rollback. On source connector crash, the uncommitted transaction is aborted, and consumer sees no partially written data. Requires Kafka broker `exactly.once.source.support=enabled` (worker config, not per-connector). Transactional overhead is ~5–10% latency/throughput per batch ([Debezium 2.3 adoption](https://debezium.io/blog/2023/06/22/towards-exactly-once-delivery/)).

**Log compaction semantics** ([topic-level configs](https://kafka.apache.org/43/configuration/topic-configs/)): `cleanup.policy=compact` enables log compaction, which retains only the latest record for each key, discarding older versions. Compaction happens asynchronously; `min.compaction.lag.ms` (default 0) sets minimum time before eligible records can be compacted, allowing consumers to catch up. Tombstones (records with null value) are retained for `delete.retention.ms` duration (default 86400000 = 24 hours) to mark key deletion. After retention expires, tombstones are removed, and the key becomes inaccessible even to consumers reading from offset 0.

**CDC interplay with compaction:** Schema change events often routed to compacted topics (`_changes` suffix) where latest schema per table key is retained. Debezium's `tombstones.on.delete=true` emits a tombstone after each DELETE, enabling idempotent upserts: consumers reading the log from offset 0 first see the INSERT, then the DELETE tombstone, arriving at the correct final state (key not present). Without compaction, the log grows unboundedly; with it, only latest state per key is retained.

**Transaction isolation for consumers** ([consumer isolation level](https://kafka.apache.org/25/javadoc/org/apache/kafka/common/IsolationLevel.html)): `isolation.level=read_committed` (default: read_uncommitted) restricts consumer to reading messages from completed transactions only. LSO (Last Stable Offset) is the earliest offset of an open transaction; consumers in read_committed mode block if they reach LSO. Essential for exactly-once CDC to ensure consumers never read intermediate states of aborted transactions.

---

## 5. Flink CDC (3.x)

**Incremental snapshot framework** ([MySQL CDC connector](https://nightlies.apache.org/flink/flink-cdc-docs-stable/docs/connectors/flink-sources/mysql-cdc/)): Distributed snapshot via chunk-based parallel reading: table data is split by primary key range into chunks (typically via binary search or modulo); multiple Flink subtasks read chunks in parallel, avoiding single-threaded snapshot bottleneck. Algorithm computes:
- Low watermark (LW): Binlog position captured *before* snapshot starts.
- High watermark (HW): Binlog position captured *after* last chunk is read.
- Per chunk: emit all rows from chunk, then backfill binlog events in range [LW, HW) for that chunk.

No external signal table is required (unlike Debezium incremental snapshot); watermarks derived purely from binlog/WAL positions. Supports read-only snapshots via GTID sets (MySQL) or pg_current_snapshot (Postgres) for consistency. Checkpoint-based exactly-once semantics to sink: Flink writes CDC events and checkpoint state atomically, ensuring idempotent sink writes on recovery.

---

## 6. Applying Changes Idempotently

**Delta Lake** ([Change Data Feed](https://delta.io/blog/2023-07-14-delta-lake-change-data-feed-cdf/) + [deletion vectors](https://delta.io/blog/2023-07-05-deletion-vectors/)): Change Data Feed (CDF) tracks row-level changes (INSERT/UPDATE/DELETE) between table versions, stored in `_change_data` folder. Tracks before and after images. Deletion vectors ([added Delta 2.0](https://delta.io/blog/2023-07-05-deletion-vectors/)) represent deleted rows as compressed RoaringBitmap markers rather than rewriting Parquet files; UPDATE and DELETE use soft-delete, not copy-on-write. MERGE INTO statement combines INSERT/UPDATE/DELETE in one atomic operation. CDC consumers replay change events to maintain replicas.

**Databricks AUTO CDC** ([Lakeflow Declarative Pipelines](https://docs.databricks.com/aws/en/ldp/cdc)): Successor to APPLY CHANGES INTO; SQL `AUTO CDC INTO target_table FROM cdc_source` automatically computes SCD Type 1 (last-value-wins) or Type 2 (time-series with valid from/to). Handles out-of-order events via `SEQUENCE BY` column (e.g., event timestamp or LSN). Partial updates (upsert only changed columns) supported. Internals use Delta CDF + deletion vectors for low-latency application.

**Apache Iceberg** ([deletion and position tracking](https://iceberg.apache.org/spec/); [v3 deletion vectors](https://iceberg.apache.org/spec/)): Two strategies for marking deleted rows:
- Equality deletes: One or more column predicates (e.g., id=123); efficient for CDC upserts where we know the key.
- Position deletes: File path + row position; efficient for clustered deletes (e.g., temporal prunes).
- v3 adds deletion vectors: Compressed bitsets stored inline; `convertEqualityDeletes()` transforms equality deletes to DVs for efficient file-level storage. Flink upsert sink writes data files + equality deletes to staging branch, then converter resolves to DVs on commit.

**Elasticsearch & OpenSearch** ([version_type=external](https://www.elastic.co/docs/api/doc/elasticsearch/operation/operation-index)): External versioning compares the version passed in the index request to the stored document version; write succeeds only if incoming version *strictly greater*. Solves distributed ordering: LSN (or Kafka offset) as external version ensures that out-of-order events (e.g., retries, replica lag) never overwrite newer state. `version_type=external_gte` also accepts equal versions (idempotent replay). Critical for CDC to avoid accidentally reverting to stale values due to Kafka partition rebalancing or sink task failures.

---

## 7. Gotchas & Failure Modes

**Replication slot loss (Postgres):** If WAL growth exceeds `max_slot_wal_keep_size` between consumer polls, the slot is marked invalid with `wal_status=lost`. Debezium detects this and must perform a full re-snapshot from the current database state ([max_slot_wal_keep_size semantics](https://www.postgresql.org/docs/18/runtime-config-replication.html)). Mitigation: set max\_slot\_wal\_keep\_size large enough to absorb peak traffic lags, or use `heartbeat.action.query` to keep LSN advancing on idle tables.

**Logical slots dropped during pg_upgrade:** [PG17+ preserves logical replication slots](https://www.postgresql.org/docs/17/release-17.html) via pg_upgrade, allowing zero-downtime major version upgrades. PG16 and earlier dropped all logical slots on upgrade, forcing re-snapshot. Check committed state and subscription readiness before upgrade ([upgrade considerations](https://www.postgresql.org/docs/18/logical-replication-upgrade.html)).

**Primary failover before PG17:** Logical replication slots were lost during primary→standby failover unless manually synced. Downstream connectors had to resync. [PG17+ failover slots](https://www.postgresql.org/docs/17/logical-replication-failover.html) with `sync_replication_slots=true` automatically sync slots to standby during replication, making slots available immediately after failover.

**MySQL binlog expiration:** Connector must catch up faster than binlog rotation (controlled by `binlog_expire_logs_seconds`, [default 30 days](https://dev.mysql.com/doc/refman/8.4/en/replication-options-binary-log.html)). Purged binlog → connector position unreachable → must re-snapshot. Mitigation: monitor connector lag, alert if approaching binlog retention, or increase `binlog_expire_logs_seconds` for slow consumers.

**Debezium schema history topic lost:** MySQL connector stores schema metadata (DDL history) in a separate Kafka topic (`<topic.prefix>-schema-changes`). If this topic is deleted or log.retention.ms expires it, Debezium cannot reconstruct the schema evolution and CDC events become uninterpretable. Mitigation: set the schema history topic to infinite retention (e.g., `retention.ms=-1`) or disable compaction.

**Out-of-order events & transaction atomicity:** Kafka partitioning by key ensures per-key ordering but not global transaction ordering. If a single transaction spans multiple partitions, sink logic must handle events from the same txn arriving out-of-order. Mitigation: use transaction metadata topic to detect transaction boundaries, or use idempotent upsert logic with version columns (LSN or event timestamp).

**Schema evolution mismatches:** If source schema changes (new column, type change) before sink is updated, CDC events may carry fields that sink schema doesn't recognize (column drop) or expect fields missing (column add). Debezium schema registry integration ([Confluent Schema Registry](https://docs.confluent.io/platform/current/schema-registry/index.html)) tracks schema evolution; sinks must coordinate schema changes via registry or manual DDL. Outbox pattern with explicit versioning in payload avoids tight schema coupling.

**Cascading failures:** Kafka → Sink chain is only as fast as the slowest link. If sink backs up (e.g., network blip), Kafka lag grows, and replication slot risk increases (Postgres). Mitigate with circuit breakers (pause source) or explicit backpressure (reduce source batch size).

---

## 8. Throughput & Production Scaling

**Netflix DBLog algorithm** ([arXiv 2010.12597](https://arxiv.org/abs/2010.12597)): Netflix's watermark-based CDC framework underpins incremental snapshot design in both Debezium and Flink CDC. Core innovation: split table into chunks, execute SELECT in parallel, emit watermark signals before/after each chunk, then backfill binlog changes between watermarks. Chunk-based approach allows:
- Non-blocking snapshots: replication can proceed during snapshot.
- Checkpoint/resume: snapshot can pause and resume without loss or duplication.
- Ad-hoc snapshots: can request snapshot of new tables at any time.

Netflix reports the system is used in production across tens of microservices (exact scale not disclosed in abstract). Debezium adopted watermark design starting in 1.6 (Oct 2021); Flink CDC integrated similar algorithm by 3.0.

**Practical throughput considerations:**
- PostgreSQL logical decoding: Throughput depends on slot consumer poll rate; unbounded if consumer stalls (WAL grows). Typical: 10k–100k events/sec per slot on commodity hardware, bounded by Kafka producer batching (max.batch.size).
- MySQL binlog streaming: Similar throughput limits; GTID tracking adds minor overhead (~1–2% CPU).
- Debezium connector overhead: ~10–20% latency added (poll → decode → serialize → produce). Batching reduces per-event overhead.
- Kafka producer transaction overhead (exactly-once): ~5–10% throughput reduction vs. fire-and-forget, due to transaction coordination on broker side.

**Snapshot performance:** Initial snapshot duration scales with table size and `incremental.snapshot.chunk.size`. Larger chunks (e.g., 10k rows) → fewer RPC round-trips but higher per-task memory; smaller chunks → more overhead but tighter progress tracking. Sweet spot typically 1k–10k rows per chunk.

---

## 9. Migration & Operational Patterns

**Zero-downtime cutover:** 
1. Enable CDC on source (create replication slot/enable binlog).
2. Debezium/Flink takes initial snapshot while streaming new changes.
3. Sink replays snapshot, then applies streamed changes (ensures monotonic consistency).
4. Validation: compare row counts and sample checksums (sink vs. source).
5. Once lag < 1s and validation passes, cut over writes to sink.
6. Backfill any missed records from transaction metadata topic if needed.

**Operational SLOs:**
- **Replication lag:** Monitor `Debezium_MQ_Records_Consumed_Total` vs. `Debezium_MQ_Records_Published_Total` (via JMX). Alert if lag > threshold (e.g., 5 min).
- **Slot staleness (Postgres):** Monitor `confirmed_flush_lsn` via `pg_replication_slots` view; alert if older than `max_slot_wal_keep_size` WAL reserve.
- **Binlog retention (MySQL):** Monitor connector position vs. oldest binlog file; alert if position nearing purge.
- **Kafka consumer lag:** Use Kafka consumer group lag metrics; alert if > high watermark (e.g., 10 min of topic retention).

**Debugging playbook:**
- High Debezium task latency → check Kafka producer batch settings, consumer poll time, source DB I/O.
- Slot invalidation (Postgres) → increase max\_slot\_wal\_keep\_size or enable heartbeat.action.query.
- Binlog missed (MySQL) → increase binlog\_expire\_logs\_seconds or reduce Debezium.fetch.size (prevents lag accumulation).
- Out-of-order sink errors → enable transaction metadata topic, route to side channel, replay in order.

---

---

## Version Compatibility Matrix

| Component | Versions Tested | Notes |
|---|---|---|
| PostgreSQL | 13–18 | Slots preserved by pg_upgrade in 17+; v1–v4 pgoutput in 18+. |
| MySQL | 8.0–8.4 | ROW format mandatory for CDC; GTID required for HA; binlog retention default 30 days. |
| Debezium | 2.x–3.7 | 2.3+ supports KIP-618 exactly-once; 3.0+ refined snapshot modes. |
| Kafka | 3.3–4.x | 3.3 introduced KIP-618; 4.x adds performance refinements. |
| Flink CDC | 3.0–3.6 | Incremental snapshot framework stable; upsert sinks for Iceberg/Delta in 3.1+. |

---

## Sources

| Claim Area | Primary URL |
|---|---|
| PG logical decoding, slots, LSN | https://www.postgresql.org/docs/18/logicaldecoding-explanation.html |
| PG replication config | https://www.postgresql.org/docs/current/runtime-config-replication.html |
| PG pgoutput protocol | https://www.postgresql.org/docs/18/protocol-logical-replication.html |
| PG failover slots (PG17+) | https://www.postgresql.org/docs/17/logical-replication-failover.html |
| MySQL binlog options | https://dev.mysql.com/doc/refman/8.4/en/replication-options-binary-log.html |
| MySQL GTID | https://dev.mysql.com/doc/refman/8.4/en/replication-gtids-concepts.html |
| Debezium PostgreSQL connector | https://debezium.io/documentation/reference/stable/connectors/postgresql.html |
| Debezium MySQL connector | https://debezium.io/documentation/reference/stable/connectors/mysql.html |
| Debezium exactly-once | https://debezium.io/documentation/reference/configuration/eos.html |
| Debezium incremental snapshots | https://debezium.io/blog/2021/10/07/incremental-snapshots/ |
| Debezium TOAST handling | https://debezium.io/blog/2019/10/08/handling-unchanged-postgres-toast-values/ |
| Debezium Server | https://debezium.io/documentation/reference/stable/operations/debezium-server.html |
| Debezium JDBC sink | https://debezium.io/documentation/reference/stable/connectors/jdbc.html |
| Kafka KIP-618 | https://kafka.apache.org/43/kafka-connect/connector-development-guide/ |
| Kafka topic config | https://kafka.apache.org/43/configuration/topic-configs/ |
| Flink CDC | https://nightlies.apache.org/flink/flink-cdc-docs-stable/ |
| Netflix DBLog paper | https://arxiv.org/abs/2010.12597 |
| Delta Lake CDF | https://delta.io/blog/2023-07-05-deletion-vectors/ |
| Databricks AUTO CDC | https://docs.databricks.com/aws/en/ldp/cdc |
| Iceberg spec | https://iceberg.apache.org/spec/ |
| Elasticsearch version\_type | https://www.elastic.co/docs/api/doc/elasticsearch/operation/operation-index |
| PG pg_upgrade (PG17) | https://www.postgresql.org/docs/17/release-17.html |

## Could Not Verify

**`max.queue.size` (Debezium):** Documentation refers to this as an in-memory buffer for CDC events, spilling to disk when full. No primary source (debezium.io or GitHub README) explicitly states the default value. This may be configured per deployment or embedded in Kafka Connect framework itself. Practical implication: ensure sufficient heap or disk for the worst-case scenario (sudden burst + slow Kafka sink).

**Throughput benchmarks:** Neither Apache Debezium, Apache Flink, nor PostgreSQL/MySQL official docs publish performance numbers (QPS, latency percentiles, or hardware specs). Netflix DBLog paper abstract is available on arXiv but does not disclose chunk sizes or production scale. Vendor blogs (Confluent, Databricks, Elastic) publish case studies but lack replicable methodology. Implication: performance is highly dependent on schema, workload (INSERT-heavy vs. OLTP), and infrastructure (CPU, disk, network).

**Kafka `transaction.timeout.ms`:** Broker-level config for transaction coordination timeout. Official docs reference it but do not state the default value (likely 60 seconds, matching wal_sender_timeout convention, but unconfirmed). Practical implication: CDC with exactly-once should monitor broker logs for timeout errors; if seen, increase this and/or reduce batch size.

**PostgreSQL Publication filters & column lists:** [Introduced PG15](https://www.postgresql.org/docs/15/release-15.html), these allow per-table row filters (WHERE predicates) and column subsets. URL for detailed syntax: [logical replication publication](https://www.postgresql.org/docs/18/logical-replication-publication.html). Reduces replication volume but complicates downstream schema tracking.

**Debezium outbox pattern routing:** Outbox event router SMT can extract `aggregateid` and route to different topics per business entity. Reduces cardinality of topics but adds routing complexity. See [Debezium outbox event router](https://debezium.io/documentation/reference/stable/transformations/outbox-event-router.html) for examples.

---

## Spot-check corrections (editor, 2026-09-27)

Checked against the primary pages with `curl` + tag strip (postgresql.org, debezium.io 3.6 docs), raw Kafka and Elasticsearch source on GitHub, WebFetch (dev.mysql.com, Flink CDC 3.6, docs.databricks.com), and `pdftotext` on the DBLog paper. Where this table disagrees with the text above, this table wins.

| Survey claim | Correct value | Source |
|---|---|---|
| `wal_status` has five states; `extended` means above `max_slot_wal_keep_size` | Four states. `extended` means `max_wal_size` is exceeded but the files are still retained by the slot or `wal_keep_size`. `unreserved` means some required files go at the next checkpoint (typically with a non-negative `max_slot_wal_keep_size`), `lost` means unusable | https://www.postgresql.org/docs/current/view-pg-replication-slots.html |
| KIP-618 needs only a worker flag, "no per-connector flag needed"; elsewhere called a broker setting | Connect **worker** config `exactly.once.source.support=enabled` plus **connector** config `exactly.once.support=required`; `transaction.boundary=poll` (the default) for Debezium. Kafka Connect 3.3.0 or later, distributed mode only | https://debezium.io/documentation/reference/stable/configuration/eos.html |
| KIP-618 overhead "~5 to 10%" | Not on the cited page. The Debezium EOS page instead warns that correctness is unproven and lists open Kafka issues KAFKA-17734, KAFKA-17754, KAFKA-17582 after the Redpanda and Bufstream Jepsen reports. Drop the number | https://debezium.io/documentation/reference/stable/configuration/eos.html |
| `max.queue.size` default could not be verified; "spills to disk when full" | Default 8192 records (`max.queue.size.in.bytes` default 0). It is a blocking queue: when full, the connector stops reading the log. No spill | https://debezium.io/documentation/reference/stable/connectors/postgresql.html |
| Kafka `transaction.timeout.ms` default could not be verified, called a broker config | Producer config, default 60000 ms | https://github.com/apache/kafka/blob/trunk/clients/src/main/java/org/apache/kafka/clients/producer/ProducerConfig.java |
| Debezium LW = position at snapshot start, HW = position after the last chunk | Watermarks are **per chunk**. Debezium writes open and close entries to the signal table around each chunk (`incremental.snapshot.watermarking.strategy`, default `insert_insert`; `insert_delete` writes one entry and deletes it) | https://debezium.io/documentation/reference/stable/connectors/postgresql.html |
| Flink CDC emits the chunk rows, then backfills the binlog in [LW, HW) | Flink CDC records the binlog position as LOW, reads and buffers the chunk, records HIGH, reads the binlog between LOW and HIGH for that chunk's key range and **upserts it into the buffered chunk**, then emits the result. Default `scan.incremental.snapshot.chunk.size` 8096. No global read lock. Needs a primary key or `scan.incremental.snapshot.chunk.key-column` | https://nightlies.apache.org/flink/flink-cdc-docs-stable/docs/connectors/flink-sources/mysql-cdc/ |
| Flink CDC read-only snapshot via `pg_current_snapshot` | Not on the cited page. Unverified | none |
| DBLog paper numbers not disclosed | In production since 2018, about 30 production services at Netflix. Algorithm pauses log processing only for the two watermark writes and one `SELECT ... LIMIT` on the PK index. Watermarks are UUID updates to a single-row table. Needs commit-order log and "non-stale reads" (read committed is enough). State (last chunk PK) in ZooKeeper | https://arxiv.org/pdf/2010.12597 |
| Throughput "10k to 100k events/s per slot", "GTID ~1 to 2% CPU", "Debezium adds ~10 to 20% latency" | No primary source. Invented. Use measured numbers only | none |
| "If the sink backs up, replication slot risk increases" | Wrong. Kafka decouples sinks from the source. Only the connector-to-Kafka path holds the slot back (connector down, Kafka unavailable, connector slower than the WAL). A slow sink only grows consumer lag in Kafka | https://debezium.io/documentation/reference/stable/connectors/postgresql.html (failure section) |
| Deletion vectors "added Delta 2.0" | Not Delta 2.0. The cited blog is the 2023 Delta 2.4 / 3.0 era; check the Delta release notes per operation before quoting a version | https://delta.io/blog/2023-07-05-deletion-vectors/ |
| REPLICA IDENTITY DEFAULT "UPDATE sends only changed columns" | The new row is sent whole except unchanged TOASTed values. DEFAULT limits the **old** image to the primary key columns (sent for DELETE, and for UPDATE when the key changed) | https://www.postgresql.org/docs/current/sql-altertable.html |
| pg_upgrade | Confirmed: logical slots are migrated only when the old cluster is 17.0 or later; slots on older clusters are silently ignored | https://www.postgresql.org/docs/current/logical-replication-upgrade.html |
| Postgres 18 docs are current | Confirmed. Postgres 19 is in beta (Beta 4 on 2026-09-24), so nothing from 19 is used in the solution | https://www.postgresql.org/docs/current/runtime-config-replication.html |

Extra facts confirmed that the solution uses:
- Postgres: `max_slot_wal_keep_size` default -1 (first in 13), `idle_replication_slot_timeout` default 0 (first in 18), `sync_replication_slots` off by default (first in 17), `synchronized_standby_slots` makes logical walsenders wait until the listed physical standbys have confirmed the WAL, `logical_decoding_work_mem` 64MB, `wal_sender_timeout` 60 s, `max_replication_slots` 10. A logical slot's position is persisted only at checkpoint, so after a crash it can replay recent changes ("clients are responsible for avoiding ill effects"). `pg_stat_replication_slots` exposes `spill_txns`, `spill_bytes`, `stream_txns`, `total_bytes`. pgoutput v2 = PG14 (stream in-progress), v3 = PG15 (two-phase), v4 = PG16 (parallel apply). Logical decoding does not emit DDL.
- MySQL 8.4: `binlog_expire_logs_seconds` 2592000 (30 days), `binlog_row_image` full, `binlog_row_metadata` MINIMAL, `binlog_format` ROW and deprecated as a variable, `binlog_transaction_compression` OFF.
- Debezium 3.6 Postgres: `snapshot.mode` initial (options always, initial, initial_only, no_data, when_needed, configuration_based, custom), `incremental.snapshot.chunk.size` 1024, `heartbeat.interval.ms` 0, `poll.interval.ms` 500, `max.batch.size` 2048, `tombstones.on.delete` true, `provide.transaction.metadata` false, `unavailable.value.placeholder` `__debezium_unavailable_value`, `slot.failover` false, `lsn.flush.mode` connector, `read.only` false. Debezium says it is at-least-once under faults and tells consumers to dedup by LSN. Pre-17 failover procedure in the doc: recreate the slot, promote, re-snapshot with `snapshot.mode=always`. The `heartbeat.action.query` fix exists for "low-traffic database on the same host as a high-traffic database".
- Kafka: `delete.retention.ms` 86400000 (24 h), `min.compaction.lag.ms` 0.
- Elasticsearch: `version_type=external` rejects a version less than or equal to the stored one (409), `external_gte` accepts equal, and the docs say database versions remove the need to order async indexing. `index.gc_deletes` default 60 s (IndexSettings.java), so a delete's version is only remembered for 60 s.
- Databricks: `AUTO CDC` replaces `APPLY CHANGES` (same syntax, old name still works). `SEQUENCE BY` accepts a `STRUCT` for tie-breaking, NULL sequence values are not supported, late updates are dropped in SCD type 1.
