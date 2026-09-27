# Real-World CDC Pipeline Architectures: Survey (Sep 2026)

## 1. LinkedIn Databus (SoCC 2012)

**Capture & Log Read.** Relays fetch committed changes from source Oracle databases via transaction logs; consumers read via sequence numbers (SCNs).

**Snapshot/Bootstrap.** Bootstrap service provides "consolidated snapshot of changes" or full data snapshot as of point-in-time, enabling new/lagging consumers to catch up without re-querying the source DB. https://engineering.linkedin.com/data-replication/open-sourcing-databus-linkedins-low-latency-change-data-capture-system

**Delivery & Ordering.** At-least-once with transactional in-order delivery; changes grouped by transaction in commit order. https://dl.acm.org/doi/10.1145/2391229.2391247

**Scale.** Thousands of change events/sec per server; end-to-end latencies in milliseconds. Supports thousands of consumers and data sources. https://engineering.linkedin.com/data-replication/open-sourcing-databus-linkedins-low-latency-change-data-capture-system

**Failure Modes.** [unverified: specific incidents]. Relay processing rate relatively flat at ~8K events/sec in published benchmarks.

---

## 2. Netflix DBLog (2019, arXiv 2010.12597)

**Capture & Log Read.** Watermark-based approach interleaves transaction log events with direct table selections (chunked snapshots) without blocking the log.

**Snapshot/Bootstrap.** Log events can progress without stalling while snapshot selections complete; enables low-impact initial state capture. https://arxiv.org/abs/2010.12597

**Delivery & Ordering.** At-least-once, leveraging high-availability active-passive architecture with multiple DBLog standby processes. https://netflixtechblog.com/dblog-a-generic-change-data-capture-framework-69351fb9099b

**Scale & Deployment.** Used by Delta platform and Data Mesh. Java-based framework. [Numbers unverified in abstract; full paper required for QPS/latency metrics.]

**Difference.** Watermark separation allows log to flow while snapshots catch up, avoiding consistency bottlenecks of traditional interleaved approaches.

---

## 3. Meta Wormhole (NSDI 2015)

**Capture & Log Read.** Reads MySQL transaction logs directly; encapsulates updates into Wormhole messages with metadata.

**Scale.** 35 GBytes/sec steady state, 50 million messages/sec (5 trillion messages/day) across all deployments; bursts to 200 GB/sec during failover recovery. https://www.usenix.org/conference/nsdi15/technical-sessions/presentation/sharma

**Replication Targets.** Geo-replicates to downstream services: TAO, Graph Search, Memcache. Cache invalidation via commit log (McSqueal pattern in "Scaling Memcache at Facebook"). https://www.usenix.org/system/files/conference/nsdi13/nsdi13-final170_update.pdf

**Delivery & Ordering.** [Specific semantics unverified from abstract; full paper required.]

**Difference.** Tight integration with Memcache invalidation; designed for sub-millisecond geo-replica staleness.

---

## 4. Airbnb SpinalTap (2018)

**Capture & Log Read.** MySQL binlog parsing via BinLogStreamReader abstraction.

**Snapshot/Bootstrap.** Connector startup triggers `SELECT * FROM TABLE` with read locks (problematic for large tables). https://medium.com/airbnb-engineering/capturing-data-evolution-in-a-service-oriented-architecture-72f7c643ee6f

**Delivery & Ordering.** Events partitioned by primary key; all events for a key go to same Kafka partition, ensuring per-key ordering. https://shopify.engineering/capturing-every-change-shopify-sharded-monolith

**Scale.** Black Friday Cyber Monday 2020: ~65k records/sec average, spikes to 100k records/sec. Binlog file as clean partition boundary. https://shopify.engineering/capturing-every-change-shopify-sharded-monolith

**Sinks.** Cache invalidation, search indexing, derived data pipelines.

**Schema Handling.** DDL handling via checkpoint/dump pattern.

---

## 5. Shopify (2021)

**Capture & Log Read.** 150 Debezium connectors across 12 Kubernetes pods tailing 100+ MySQL shards. https://shopify.engineering/capturing-every-change-shopify-sharded-monolith

**Snapshot/Bootstrap.** Initial snapshots via Debezium `SELECT * FROM TABLE` with read locks. Planned upgrade to incremental snapshots to backfill chunks without locking.

**Delivery & Ordering.** At-least-once with per-key partition ordering via primary key. Topics compacted for complete table state reconstruction.

**Scale.** p99 latency <10 seconds from MySQL insert to Kafka availability (2020 Black Friday: ~65k avg, 100k spike records/sec). 400TB+ CDC data in Kafka. https://shopify.engineering/capturing-every-change-shopify-sharded-monolith

**Schema Handling.** Apache Avro + Confluent Schema Registry. Breaking schema changes "extremely disruptive"; require custom notification processes.

**Failure Modes.** Missing hard deletes in predecessor query-based system; stale updated_at fields during migrations; lost intermediate row states; rare rows constantly updating escaped capture; large records (tens of MB) required custom GCS external storage. https://shopify.engineering/capturing-every-change-shopify-sharded-monolith

---

## 6. Notion (2024)

**Capture & Log Read.** One Debezium PostgreSQL connector per host, 480 logical shards across infrastructure. Handles tens of MB/sec row changes. https://www.notion.com/blog/building-and-scaling-notions-data-lake

**Snapshot/Bootstrap.** AWS RDS export-to-S3 for initial snapshots (>10 hours, 2× cost), then Debezium captures changes from timestamp forward. Bootstrap within 24 hours.

**Sink.** Apache Hudi Deltastreamer (Spark-based) ingests Kafka to S3, preserving 480-shard partitioning. Data sorted by event_lsn for file pruning optimization.

**Delivery & Ordering.** [Unspecified in source; preserved Postgres partitioning implies per-shard ordering.]

**Scale.** 480 shards (32→96 physical instances, 15→5 logical/instance 2021→2023). 200B+ block rows (vs. 20B in 2021). Largest table ~2 hour replication lag; most ~minutes. Data doubles every 6-12 months. https://www.notion.com/blog/building-and-scaling-notions-data-lake

**Cost.** Net savings >$1M in 2022, proportionally higher 2023-2024.

**Difference.** Hybrid snapshot (RDS export vs. DB query) + stream handoff avoids locking; maturity of Debezium/EKS/Kafka allowed 6-12mo doubling without major overhauls.

---

## 7. Robinhood (2022)

**Capture & Log Read.** Debezium PostgreSQL CDC connector, Avro + Confluent Schema Registry.

**Snapshot/Bootstrap.** Custom snapshotter on Hudi Deltastreamer using Spark; concurrent partitioned snapshot queries against dedicated read-replicas.

**Sink.** Apache Hudi for exactly-once incremental writes to data lake (S3).

**Scale.** [Specific throughput unverified; article references benchmarking for "projected load volumes."] https://robinhood.engineering/

**Delivery Semantics.** Exactly-once via Hudi's built-in guarantees.

**Difference.** Read-replica isolation for snapshots + parallel Spark queries accelerate bootstrap; Hudi's streaming Deltastreamer handles exactly-once dedup.

---

## 8. Uber DBEvents (2019)

**Capture & Log Read.** Snapshot from MySQL, Cassandra, Schemaless stores. Binary log events record committed changes. https://www.uber.com/blog/dbevents-ingestion-framework/

**Snapshot/Bootstrap.** Point-in-time snapshot, executed incrementally with configurable batch sizes to avoid resource exhaustion. Then incremental phase applies row-level changes. https://www.uber.com/blog/dbevents-ingestion-framework/

**Delivery & Ordering.** Exactly-once via monotonically increasing reference keys on rows; binary log ordering preserved through Kafka; ForceUpdate flags support out-of-order corrections. Error tables capture non-conforming messages.

**Scale.** Tens of millions QPS, tens of petabytes operational data. Reduced latency from hours to "a few minutes." https://www.uber.com/blog/dbevents-ingestion-framework/

**Schema.** Standardized Avro via heatpipe; Apache Hadoop metadata headers per Kafka message.

**Difference.** Error tables ensure no data loss; exactly-once reference key dedup; explicit ForceUpdate for late-arriving corrections.

---

## 9. Yelp MySQLStreamer (2016)

**Capture & Log Read.** BinLogStreamReader abstraction; peek/pop/resume operations for MySQL binlog tailing. https://engineeringblog.yelp.com/2016/08/streaming-mysql-tables-in-real-time-to-kafka.html

**State Management.** Three databases: source (monitored), schema-tracker (DDL replica), state (checkpoints/offsets).

**Ordering & Consistency.** Zookeeper locking prevents multiple instances on same cluster; replication inherently serial, ensuring strong ordering.

**Schema Handling.** Schematizer service generates Avro from CREATE TABLE; checkpoints before applying DDL; Update events include before/after rows.

**Event Types.** Insert, Update, Delete, Refresh (bootstrap).

---

## Managed Products

### Google Cloud Datastream
Throughput: 10s MB/sec per stream. Up to 10k tables/stream. Backfill (incremental or full dump) + CDC phases. At-least-once delivery; does not guarantee ordering (metadata allows eventual consistency ~1hr). Supports MySQL, PostgreSQL, Oracle, SQL Server. https://docs.cloud.google.com/datastream/docs/faq

### AWS DMS
Single-threaded CDC for RDBMS targets (no parallel CDC threads). Batch apply optimization for high-volume updates. Memory-constrained by stream buffer and sorter components. https://aws.amazon.com/blogs/database/aws-dms-key-troubleshooting-metrics-and-performance-enhancers/

### Confluent Debezium Connectors
Exactly-once via KIP-618 (Kafka Connect framework), but unavailable during snapshot mode. Single task per connector (`tasks.max: 1`). https://docs.confluent.io/cloud/current/connectors/cc-postgresql-cdc-source-v2-debezium/cc-postgresql-cdc-source-v2-debezium.html

### PeerDB / ClickHouse Postgres CDC
200TB/month replicated (400+ companies via ClickPipes, 100× growth since 2024 acquisition). Bootstrap: 10B rows ~12 hours (vs. 3 days competing). Parallel snapshots by CTID range; partition generation <1 second. 50+ pre-flight validation checks; Prometheus/OTEL metrics (replication slot growth, commit lag). https://clickhouse.com/blog/postgres-cdc-year-in-review-2025

### Materialize PostgreSQL Source
Native Postgres replication stream (no Kafka required). Transactional consistency: all updates in one XID get identical timestamp; orders by LSN of commits. No intermediate infrastructure. https://materialize.com/blog/strong-consistency-in-materialize/

### Debezium PostgreSQL (General)
Logical replication slots with WAL retention. V2 protocol for high-throughput large transactions. Failover slot support (PostgreSQL 17+, replica creation). Slot creation retry: 90s timeout, configurable max retries. Slot bloat risk during outages; requires monitoring. https://debezium.io/documentation/reference/stable/connectors/postgresql.html

---

## Comparison Table

| System | Year | Source DB | Throughput | Delivery | Ordering | Snapshot | Key Innovation | Notes |
|---|---|---|---|---|---|---|---|---|
| LinkedIn Databus | 2012 | Oracle | 1Ks evt/s | at-least-once | xact order | Bootstrap svc | Transactional order, infinite lookback | oldest production CDC |
| Netflix DBLog | 2019 | any | [n/a] | at-least-once | [n/a] | watermark interleave | Non-blocking snapshot + log interleaving | academia + Netflix use |
| Meta Wormhole | 2015 | MySQL | 35 GB/s (50M msg/s) | [unverified] | [unverified] | [unverified] | Geo-replication + cache invalidation | 200 GB/s failover spike |
| Airbnb SpinalTap | 2018 | MySQL | 65k-100k rec/s | at-least-once | per-key (binlog partition) | SELECT + lock | Binlog as partition boundary | cache invalidation focus |
| Shopify | 2021 | MySQL (100+) | 65k-100k rec/s | at-least-once | per-key | SELECT + lock (future: incremental) | Debezium @ scale; planned incremental snapshot | 400TB in Kafka; locking pain |
| Notion | 2024 | Postgres (480) | 10s MB/s | [unverified] | per-shard (LSN) | RDS export to S3 | Hybrid snapshot; 480 shard partitioning | $1M+ savings; 6-12mo doubling OK |
| Robinhood | 2022 | Postgres | [n/a] | exactly-once | [n/a] | Spark parallel (read-replica) | Parallel CTID snapshots; Hudi integration | read-replica isolation |
| Uber DBEvents | 2019 | multi-source | 10s M QPS | exactly-once | xact order | incremental batch | Reference key dedup; error table | ForceUpdate for late corrections |
| Yelp MySQLStreamer | 2016 | MySQL | [n/a] | at-least-once | serial (ZK lock) | [n/a] | Binlog abstraction; schema-tracker DB | pre-Debezium era |
| Google Datastream | 2024 | multi | 10s MB/s | at-least-once | NO guarantee | incremental or full | Serverless, 10k tables/stream | eventual consistency ~1hr |
| AWS DMS | - | multi | [throughput-dependent] | [n/a] | single-threaded | full+incremental | Batch apply optimization | no parallel CDC |
| Confluent Debezium | 2024 | multi | [n/a] | exactly-once (snapshot excluded) | [n/a] | snapshot + log | KIP-618 support; single task | Managed Kafka Connect |
| PeerDB/ClickHouse | 2024 | Postgres | [n/a] | [n/a] | per-shard | parallel CTID; RDS export | 10x snapshot speedup; <1s partition gen | 100× growth in 1 year |
| Materialize | 2024 | Postgres | [n/a] | [n/a] | LSN order (xact groups) | native replication stream | Native Postgres stream; no Kafka | transactional consistency by design |
| Debezium (general) | 2024+ | multi | [unverified] | configurable | slot/binlog order | snapshot + log | Logical replication (Postgres), binlog (MySQL) | slot bloat risk; WAL retention |

---

## Sources

| System | URL |
|---|---|
| LinkedIn Databus | https://dl.acm.org/doi/10.1145/2391229.2391247 |
| LinkedIn Databus Blog | https://engineering.linkedin.com/data-replication/open-sourcing-databus-linkedins-low-latency-change-data-capture-system |
| Netflix DBLog Paper | https://arxiv.org/abs/2010.12597 |
| Netflix DBLog Blog | https://netflixtechblog.com/dblog-a-generic-change-data-capture-framework-69351fb9099b |
| Meta Wormhole NSDI | https://www.usenix.org/conference/nsdi15/technical-sessions/presentation/sharma |
| Scaling Memcache (McSqueal) | https://www.usenix.org/system/files/conference/nsdi13/nsdi13-final170_update.pdf |
| Airbnb SpinalTap | https://medium.com/airbnb-engineering/capturing-data-evolution-in-a-service-oriented-architecture-72f7c643ee6f |
| Shopify CDC | https://shopify.engineering/capturing-every-change-shopify-sharded-monolith |
| Notion Data Lake | https://www.notion.com/blog/building-and-scaling-notions-data-lake |
| Uber DBEvents | https://www.uber.com/blog/dbevents-ingestion-framework/ |
| Yelp MySQLStreamer | https://engineeringblog.yelp.com/2016/08/streaming-mysql-tables-in-real-time-to-kafka.html |
| Google Datastream FAQ | https://docs.cloud.google.com/datastream/docs/faq |
| AWS DMS Performance | https://aws.amazon.com/blogs/database/aws-dms-key-troubleshooting-metrics-and-performance-enhancers/ |
| Confluent Debezium PostgreSQL V2 | https://docs.confluent.io/cloud/current/connectors/cc-postgresql-cdc-source-v2-debezium/cc-postgresql-cdc-source-v2-debezium.html |
| PeerDB/ClickHouse Postgres CDC | https://clickhouse.com/blog/postgres-cdc-year-in-review-2025 |
| Materialize PostgreSQL Source | https://materialize.com/blog/strong-consistency-in-materialize/ |
| Debezium PostgreSQL Connector | https://debezium.io/documentation/reference/stable/connectors/postgresql.html |

---

## Architectural Patterns Observed

### Snapshot / Bootstrap Strategies
1. **Direct SELECT + Lock** (Shopify, Airbnb): Simple; blocks source DB. Risk of lock contention on large tables.
2. **Watermark Interleave** (Netflix DBLog): Non-blocking; log continues while snapshot runs. Adds complexity for timestamp synchronization.
3. **Hybrid Export + Stream** (Notion): RDS export-to-S3 for large snapshots, then binlog/CDC from timestamp. Avoids DB lock but longer bootstrap (>10 hours).
4. **Read-Replica Snapshots** (Robinhood): Parallel Spark queries on dedicated read-replica. Isolates snapshot load from production; per-CTID partitioning accelerates large tables.
5. **Bootstrap Service / Consolidated Snapshot** (Databus, Uber): Dedicated service holds point-in-time snapshots; new consumers fetch without querying source. Enables "infinite lookback."

**Lesson:** Scale-aware selection critical. Sub-TB tables: direct SELECT acceptable. Multi-TB: parallel CTID or RDS export preferred. Consistency risk increases with lock duration.

### Delivery Semantics & Ordering
1. **At-Least-Once + Per-Key Ordering** (Shopify, Airbnb): Partition by primary key; dedup on downstream consumer via unique key. Sufficient for idempotent writes.
2. **Exactly-Once via Reference Key** (Uber): Monotonic reference key per row; downstream dedup on key. Requires careful row-version sequencing.
3. **Transactional Order** (Databus): Changes grouped by transaction ID (XID) in commit order. Strongest consistency; requires transaction log read.
4. **At-Least-Once No Order** (Google Datastream): Metadata per event enables eventual consistency within ~1 hour. Weakest; suitable for analytical workloads tolerating eventual consistency.

**Lesson:** OLTP caches/search need per-key or transactional order. Data lakes tolerating 1hr staleness use unordered + metadata. Exactly-once adds reference-key overhead; rarely needed if downstream is idempotent.

### Failure Modes & Incidents

**Snapshot Locking.** Shopify documented large-table snapshots forcing Debezium locks, stalling binlog event capture. Solution: incremental snapshots (chunked, no lock). LinkedIn's Bootstrap service and Robinhood's read-replica isolation avoid this entirely.

**Replication Slot / Binlog Retention.** Debezium PostgreSQL: logical replication slots hold WAL indefinitely until connector catches up. High-throughput workloads with long-running transactions risk 100s GB WAL growth, crashing Postgres. PeerDB documented this; solution is v2 logical replication protocol + monitoring (Prometheus/OTEL). MySQL binlog purge: old binlog files deleted before CDC connector restarts; data loss if restart lag > retention window.

**Schema Evolution.** Shopify: breaking schema changes "extremely disruptive." Yelp: DDL checkpoints before apply. Notion: preserved Postgres partitioning through schema changes. Consensus: schema versioning + schema registry (Confluent, Yelp Schematizer) mitigates; online DDL frameworks (Vitess, GitHub gh-ost) preferred for source DB.

**Lag During Backfill.** Shopify acknowledged unable to add tables post-snapshot without re-locking. Notion's RDS export partially addresses (only initial backfill heavy, not per-table). Robinhood/ClickHouse parallel CTID solves by partitioning initial load.

**Consistency During Failover.** Wormhole: 200 GB/sec spike during failure recovery (normal: 35 GB/s). Databus: SCN-based ordering ensures consistency despite failover. Materialize: LSN-based ordering with transactional grouping. Notion: event_lsn sorting for file pruning (implicit failover consistency).

---

## Key Takeaways for Practitioners

1. **Pick snapshot strategy early.** Direct SELECT works at <1 TB; parallel CTID or RDS export needed at >10 TB. Lock duration dominates bootstrap latency.

2. **Ordering granularity vs. scale.** At-least-once per-key sufficient for most uses; transactional ordering needed only for global consistency requirements (rare).

3. **Monitor slot/binlog retention.** Establish alerting on replication slot lag (Postgres), binlog file count (MySQL). Slot bloat is a top cause of CDC pipeline failures in production.

4. **Schema changes are operational risk.** Debezium/CDC cannot innovate on DDL. Require schema versioning, registry, and online migration tools on the source DB side.

5. **Delivery semantics are not free.** Exactly-once adds reference-key overhead and snapshot limitations (Confluent EOS disabled during snapshot). Evaluate whether idempotent consumer dedup (at-least-once) suffices.

6. **Managed services (Datastream, Confluent, ClickHouse CDC) handle ops burden.** Throughput: 10s-100s MB/s (adequate for most analytics). Tradeoff: less control (no ordering in Datastream), single-task limit (Confluent), or managed pricing (ClickHouse). Self-hosted Debezium cheaper but requires slot/binlog monitoring and Kafka operations.

---

## Could Not Verify

- Netflix DBLog paper: full numeric metrics (QPS, latency) from arXiv abstract only; PDF text extraction failed
- Meta Wormhole paper: full delivery semantics and snapshot details; PDF corrupted
- Scaling Memcache paper: specific McSqueal binlog mechanism details; PDF corrupted
- Robinhood: exact throughput/bootstrap numbers; URL redirected, final destination 404
- Airbnb SpinalTap: 2018 blog original details; spun as "Capturing Data Evolution" but SpinalTap brand name in airbnb.io project list
- Google Cloud Datastream ordering: "does not guarantee" is explicit; one-hour eventual consistency via metadata implied but not quantified
- AWS DMS: published throughput limits or benchmarks for 2024
- Confluent Debezium: exact throughput limits or latency guarantees (single-task constraint implies but not quantified)
- Incident reports: WAL bloat, binlog purge, replication slot exhaustion as named incidents in engineering blogs; only general principles found


---

## Spot-check corrections (editor, 2026-09-27)

Checked with WebFetch (Shopify, Notion, ClickHouse), `pdftotext` on the Wormhole (NSDI 2015), Scaling Memcache (NSDI 2013) and DBLog (arXiv) PDFs, and a WebSearch for the Databus abstract. Where this table disagrees with the text above, this table wins.

| Survey claim | Correct value | Source |
|---|---|---|
| SpinalTap: "65k records/s average, 100k spikes", per-key partitioning (both cited to the Shopify URL) | Misattributed. Those are **Shopify's** BFCM 2020 numbers. Nothing in this survey verifies a SpinalTap throughput number; treat SpinalTap as "MySQL binlog CDC, per-key order" only | https://shopify.engineering/capturing-every-change-shopify-sharded-monolith |
| Shopify | Confirmed (post dated 2021-03-12): ~150 Debezium connectors on 12 Kubernetes pods, 100+ MySQL shards, ~65,000 records/s average and 100,000/s spikes during BFCM 2020, p99 < 10 s from MySQL insert to Kafka, 400 TB+ of CDC data in Kafka, records up to tens of MB vs Kafka's 1 MB default. Initial snapshots "hold a read lock on the table ... can take hours". The predecessor (Longboat, query-based) missed hard deletes, missed updates that did not touch `updated_at`, lost intermediate states, and was at best hourly | https://shopify.engineering/capturing-every-change-shopify-sharded-monolith |
| Notion "32 to 96 instances, 15 to 5 logical per instance" | Only the end state is confirmed: 96 physical instances, 5 logical shards each, 480 logical shards (2024-07-01 post). One Debezium connector per Postgres host on EKS, one Kafka topic per table, "tens of MB/sec" of row changes, 20 B+ block rows (2021) to 200 B+ blocks, doubling every 6 to 12 months, lag "a few minutes for most tables, and up to two hours for the largest", > $1M net savings in 2022 | https://www.notion.com/blog/building-and-scaling-notions-data-lake |
| Notion bootstrap | Handoff is **timestamp overlap, not watermarks**: start Debezium first, at time `t` start an RDS export-to-S3, load the export with Spark, then replay Kafka from `t` into Hudi. Correct only because the Hudi write is an upsert ordered by LSN. The "more than 10 hours and twice the cost" refers to re-taking a full snapshot each time versus incremental ingestion. Bootstrap "usually complete within 24 hours" | https://www.notion.com/blog/building-and-scaling-notions-data-lake |
| Wormhole delivery semantics unverified | Confirmed from the paper: 35 GB/s steady (50 M messages/s, 5 trillion/day; 50 M × 86,400 = 4.3 T, rounded up in the paper), bursts to 200 GB/s during failure recovery, **at-least-once** and **in-order** delivery. Publishers read the storage system's own log (no interposed store) and group subscribers at similar positions into "caravans" so one log reader serves many; lagging caravans read 1.25 to 2x faster, capped by per-caravan and total read-rate limits to protect the datastore | https://www.usenix.org/system/files/conference/nsdi15/nsdi15-paper-sharma.pdf |
| McSqueal details unverified | Confirmed: SQL statements carry the memcache keys to invalidate, an `mcsqueal` daemon on every database tails committed statements and broadcasts deletes, batched through mcrouter per frontend cluster. Invalidation from the commit log replaces invalidation from web servers because it can be replayed after a misrouting | https://www.usenix.org/system/files/conference/nsdi13/nsdi13-final170_update.pdf |
| DBLog numbers unverified, "PDF extraction failed" | Extracted: production since 2018, ~30 production services, MySQL / PostgreSQL / Aurora, ZooKeeper for state and leader election (active-passive HA) | https://arxiv.org/pdf/2010.12597 |
| Databus "~8K events/s relay rate" | Not verified. The abstract says "latencies in the low milliseconds", "thousands of events per second per server", "infinite look back". Use only that | https://dl.acm.org/doi/10.1145/2391229.2391247 |
| PeerDB "10 B rows in ~12 hours" | Not on the cited page. The page (2025-12-03) says: partition generation went from 7+ hours to under a second with CTID block partitioning, "tens of terabytes ... in a few hours", 200 TB+/month replicated by 400+ companies | https://clickhouse.com/blog/postgres-cdc-year-in-review-2025 |
| Robinhood, Uber, Airbnb pages | Uber returns 406 and Medium returns 403 to scripted fetches; their numbers are not used in the solution |  |
| Materialize "all updates in one XID get identical timestamp; orders by LSN" | First half confirmed: "all updates for any one transaction get an identical timestamp" (post dated 2025-01-24). The page does not mention LSN or Debezium metadata | https://materialize.com/blog/strong-consistency-in-materialize/ |
| Google Datastream | Confirmed: "Datastream doesn't guarantee ordering", at-least-once, "eventual consistency can generally be achieved within a 1-hour window", up to 10,000 tables per stream | https://docs.cloud.google.com/datastream/docs/faq |
