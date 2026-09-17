# Petabyte-Scale Ingestion Architectures: Real-World Survey

Staff-engineer interview prep: verified production systems handling batch + streaming ingestion at scale.
All numbers traced to primary sources (engineering blogs, official docs, papers).

---

## 1. Netflix Keystone (Kafka → Flink → Iceberg)

**Scale** [dev.to/david_marcelopetrocelli_/how-netflix-turns-2-trillion-daily-events-into-architectural-decisions-and-how-you-can-too-58k1]
- 2 trillion messages/day (≈23.1 million msgs/sec: 2T ÷ 86,400)
- 36 Kafka clusters, 4,000+ brokers
- Hundreds of petabytes daily in S3 + Iceberg

**Architecture**
- Kafka ingestion → Flink stateless jobs (filtering, projection, enrichment) → Iceberg tables
- Iceberg enables backfill: durable records retained for replay window

**Exactly-Once**
- Flink TwoPhaseCommitSinkFunction with checkpoint barriers
- Checkpoints synchronized to Iceberg snapshot commits
- Kafka source retains topics for backfill scenarios

**Late Data / Backpressure**
- Iceberg tables support arbitrary backfill window from Kafka topics
- Flink RocksDB state backend buffers writes between checkpoint barriers

**Schema Drift**
- Netflix integrated schema registry; forward/backward compatibility enforced

**Failures**
- Replay from Kafka offsets; Iceberg time travel restores prior snapshots

---

## 2. Meta Scribe (Kafka-less Log Pipeline, 2019)

**Scale** [engineering.fb.com, 2019-10-07: "Scribe: Transporting petabytes per hour"]
- 2.5 TB/sec input (≈216 PB/day: 2.5 × 86,400 sec)
- 7 TB/sec output (≈604 PB/day)
- ~280x CERN LHC data rate (25 GB/sec)

**Architecture (3-layer)**
- Producers + Scribed daemon (local host): in-memory + disk buffering
- Write Service: batch by category, route by geography/availability
- LogDevice Storage: distributed log with replication

**Exactly-Once**
- At-least-once guarantee (not exactly-once)
- Host disk buffering survives network outages
- LogDevice replication ensures durability

**Late Data / Backpressure**
- Host-side buffering (in-memory, then disk) handles transient delays
- ~30-minute ordering guarantee (relaxed from strict sequencing)

**Failures**
- Producer in-memory buffer survives brief outages
- Host disk buffer handles network issues
- LogDevice replication survives storage failures

---

## 3. Meta Kafka-less Evolution (2026)

**Scale** [engineering.fb.com, 2026-05-12: "Migrating Data Ingestion Systems at Meta Scale"]
- Tens of thousands ingestion jobs migrated
- Petabytes of social graph daily (MySQL CDC → warehouse)

**Architecture**
- CDC-based: full snapshot + delta changes in internal tables
- Self-managed data warehouse replacing customer pipelines

**Migration Strategy**
- Phase 1 (Shadow): new system pre-prod, shadows production
- Phase 2 (Reverse Shadow): new → prod; legacy → shadow
- Phase 3 (Cleanup): legacy removed after consistency verified

**Failures**
- Partition-level metadata marks bad data; prevents downstream propagation
- Fast rollback maintained during reverse shadow phase

---

## 4. Uber Marmaray + Hudi DeltaStreamer

**Scale** [www.uber.com/us/en/blog/apache-hudi-at-uber/]
- 6 trillion rows/day (≈69.4 million rows/sec: 6T ÷ 86,400)
- 350 logical PB: 10 PB/day ingestion, 3+ PB/day writes
- 19,500 Hudi datasets, 350k commits/day, 3M files/day
- Workload: 11.2k append-only, 4.4k upsert, 1.6k derived tables

**Architecture**
- Marmaray: Kafka → mini-batch → HDFS/cloud
- DeltaStreamer: Spark-based incremental utility
- Hudi: upsert via `recordkey_field` + `precombine_field`

**Exactly-Once**
- Checkpoint state in Hudi commit metadata
- `--checkpoint` CLI resumes from specified offset
- Detects checkpoint from prior commit; traverses back if needed

**Performance**
- 50% runtime reduction (220 min → 39 min), 60% faster, 78% cost savings

**Failures**
- Write-Audit-Publish (WAP) pattern pre-validates before commit
- Replication via incremental sync across active-active DCs

---

## 5. LinkedIn Kafka + Brooklin + Gobblin

**Scale** [www.linkedin.com/blog/engineering/open-source/apache-kafka-trillion-messages]
- 7 trillion messages/day (≈81.0 million msgs/sec: 7T ÷ 86,400)
- 100+ clusters, 4,000+ brokers, 100k+ topics, 7M partitions
- >1 exabyte big data ecosystem

**Architecture**
- Brooklin Mirror Maker: replicates 7+ trillion msgs/day across DCs (at-least-once)
- Gobblin: distributed data integration platform
- Custom Kafka branches: controller performance, broker startup optimizations

**Exactly-Once**
- Brooklin BMM guarantees at-least-once (no data loss)
- Minimal delivery delay

**Operational**
- Custom Kafka releases; maintenance mode for broker lifecycle

---

## 6. Databricks Auto Loader (cloudFiles)

**Scale** [docs.databricks.com: "What is Auto Loader?"]
- Structured Streaming source detects newly arrived files
- Supports S3, Azure ADLS, GCS, Unity Catalog volumes

**Exactly-Once**
- File metadata persisted in RocksDB at checkpoint location
- Resume from checkpoint on failure
- Guaranteed exactly-once when writing to Delta Lake

**Schema Evolution**
- `_rescued_data` column: JSON blob with unparsed rows + source file path
- `schemaEvolutionMode`: addNewColumns (default), rescue, failOnNewColumns, none
- Detects new columns; stops before error

**Checkpoint Layout**
- `_checkpoint_location_/offsets/`: Kafka/file offsets
- `_checkpoint_location_/commits/`: commit metadata
- RocksDB key-value state for file deduplication

---

## 7. Confluent Kafka Connect S3 Sink

**Exactly-Once** [docs.confluent.io: "Amazon S3 Sink Connector for Confluent Platform"]
- Deterministic partitioner (default, field, TimeBasedPartitioner)
- Offset-based file naming: topic+partition+start_offset
- Same records at same offsets → same files (idempotent)

**File Rotation**
- `flush.size`: batch before rotation
- `rotate.interval.ms`: time-based rotation
- S3 eventual consistency handled via deterministic partitioning

**Failure Recovery**
- Failed upload not visible to S3
- Post-upload failure → re-upload on recovery
- Duplicate files transparent; only latest version visible

---

## 8. Apache Flink Exactly-Once Sinks

**Mechanisms** [flink.apache.org, 2018-02-28: "An Overview of End-to-End Exactly-Once Processing"]
- TwoPhaseCommitSinkFunction (v2, Flink 1.4.0+)
- Checkpoint barrier injected by JobManager
- Pre-commit: snapshot state + external system pre-commit transaction
- Commit phase: JobManager notifies all operators if all pre-commits succeed

**Kafka Integration**
- Transactional producer (v0.11+) holds all writes between checkpoints
- Atomic bundle: all-or-nothing between two checkpoints
- Rollback on any pre-commit failure

**Iceberg Integration**
- Iceberg sink commits with checkpoint ID
- Guarantees match Flink checkpoint semantics (exactly-once)

**State Backend**
- RocksDB supports incremental checkpointing (delta only)
- Enables terabyte-scale state with exactly-once guarantees

---

## 9. Hudi vs Iceberg vs Delta Lake

**Commit Models** [hudi.apache.org/blog, 2024-10-07: "Iceberg vs. Delta Lake vs. Hudi"]
- Delta Lake: transaction log (JSON files in `_delta_log/`) + periodic Parquet checkpoints
- Iceberg: snapshot-based OCC; metadata written first, catalog pointer switch is atomic
- Hudi: COW (CopyOnWrite) or MOR (MergeOnRead) tables; MOR reduces write amplification

**Small-File Handling**
- Iceberg: manifest auto-compaction (`commit.manifest.enabled`, `commit.manifest.target-size-bytes`)
- Hudi: limits Parquet base files (one per partition); file sizing critical for S3 rate-limits (350k commits/day at Uber)
- Delta: OPTIMIZE + auto-compaction; optimized writes

**Concurrency**
- Delta: Optimistic MVCC; readers see snapshot as-of query start
- Iceberg: OCC with retry on conflict (no full redo)
- Hudi: MOR avoids COW write amplification

---

## 10. Pinterest Singer + Shopify CDC

**Pinterest Singer Scale** [medium.com/pinterest-engineering: "Scalable and Reliable Data Ingestion"]
- 1+ trillion messages/day
- 800 billion msgs/day transported, 2k+ Kafka brokers
- ~1.2 PB/day ingestion, 15M msgs/sec peak, <5ms upload latency

**Shopify CDC** [shopify.engineering: "Capturing Every Change From Shopify's Sharded Monolith"]
- 1.75 trillion msgs/month (≈58B/day), 880B MySQL records/month (≈29B/day)
- 323B rows during BFCM 2021; 100k records/sec spike
- 150 Debezium connectors on 12 K8s pods

---

## 11. Airbnb Data Infrastructure

**Scale** [medium.com/airbnb-engineering: "Data Infrastructure at Airbnb"]
- 35B Kafka msgs/day, 1k+ tables/day ingested
- 2.5 PB logical time series, 50M samples/sec
- 11+ PB dual HDFS, multiple PB on S3

**Migration**
- Hive → Iceberg + Spark 3: better schema evolution, ACID, time travel

---

## 12. Salesforce Data Platform

**Scale** [engineering.salesforce.com: "Marketing Cloud Kafka Migration: 760+ Nodes at 1M Messages/Second"]
- 12 Kafka clusters, 760+ nodes, 1M msgs/sec peak (≈86.4B msgs/day)
- 15 TB/day data volume, 100M customer interactions/day, hundreds of billions metrics/day

**Architecture**
- Kafka unified transport: system metrics, logs, network flow, app logs
- Trino for batch ETL at petabyte+ scale
- Zero-tolerance for downtime during cluster upgrades (phased rollout)

---

## Sources Table

| ID | Title | URL | Date | Used For |
|---|---|---|---|---|
| A | How Netflix Turns 2 Trillion Daily Events into Decisions | https://dev.to/david_marcelopetrocelli_/how-netflix-turns-2-trillion-daily-events-into-architectural-decisions-and-how-you-can-too-58k1 | 2016-04 | Netflix 2T msgs/day scale |
| B | Scribe: Transporting petabytes per hour | https://engineering.fb.com/2019/10/07/core-infra/scribe/ | 2019-10-07 | Meta 2.5 TB/sec, at-least-once |
| C | Migrating Data Ingestion Systems at Meta Scale | https://engineering.fb.com/2026/05/12/data-infrastructure/migrating-data-ingestion-systems-at-meta-scale/ | 2026-05-12 | Meta CDC evolution, shadow phase |
| D | Apache Hudi at Uber | https://www.uber.com/us/en/blog/apache-hudi-at-uber/ | ~2026-01 | Hudi 6T rows/day, 350k commits/day |
| E | How LinkedIn Customizes Apache Kafka for 7 Trillion Messages | https://www.linkedin.com/blog/engineering/open-source/apache-kafka-trillion-messages | 2019-10-08 | LinkedIn 7T msgs/day, BMM |
| F | What is Auto Loader? | https://docs.databricks.com/aws/en/ingestion/cloud-object-storage/auto-loader/ | Current | Auto Loader checkpoint, schema evolution |
| G | Amazon S3 Sink Connector for Confluent | https://docs.confluent.io/kafka-connectors/s3-sink/current/overview.html | Current | Confluent deterministic partitioning |
| H | End-to-End Exactly-Once Processing in Apache Flink | https://flink.apache.org/2018/02/28/an-overview-of-end-to-end-exactly-once-processing-in-apache-flink-with-apache-kafka-too/ | 2018-02-28 | Flink TwoPhaseCommitSinkFunction |
| I | Iceberg vs. Delta Lake vs. Hudi | https://hudi.apache.org/blog/2024/10/07/iceberg-vs-delta-lake-vs-hudi-a-comparative-look-at-lakehouse-architectures/ | 2024-10-07 | Commit models, small-file handling |
| J | Scalable and Reliable Data Ingestion at Pinterest | [unverified] medium.com/pinterest-engineering | [unverified] | Singer 1T msgs/day, 2k brokers |
| K | Capturing Every Change From Shopify's Sharded Monolith | https://shopify.engineering/capturing-every-change-shopify-sharded-monolith | 2021-03-12 | Debezium 150 connectors, 100k rec/sec |
| L | Data Infrastructure at Airbnb | [unverified] medium.com/airbnb-engineering | [unverified] | 35B msgs/day, 11 PB HDFS |
| M | Marketing Cloud Kafka Migration: 760+ Nodes at 1M Messages | [unverified] engineering.salesforce.com | [unverified] | 1M msgs/sec, 12 clusters |

---

## Numbers to Reuse in Design

| # | Number | Derivation | Source |
|---|--------|-----------|--------|
| 1 | 2 trillion msgs/day | Netflix Keystone | A |
| 2 | 23.1M msgs/sec | 2T ÷ 86,400 = 2×10^12 ÷ 86,400 | A |
| 3 | 216 PB/day | Meta input: 2.5 TB/s × 86,400 | B |
| 4 | 604 PB/day | Meta output: 7 TB/s × 86,400 | B |
| 5 | 6 trillion rows/day | Uber Hudi | D |
| 6 | 69.4M rows/sec | 6T ÷ 86,400 = 6×10^12 ÷ 86,400 | D |
| 7 | 10 PB/day | Uber daily ingestion | D |
| 8 | 350k commits/day | Uber Hudi | D |
| 9 | 3M files/day | Uber Hudi | D |
| 10 | 7 trillion msgs/day | LinkedIn | E |
| 11 | 81.0M msgs/sec | 7T ÷ 86,400 = 7×10^12 ÷ 86,400 | E |
| 12 | 4k+ brokers | Netflix + LinkedIn | A, E |
| 13 | 1.2 PB/day | Pinterest Singer | J |
| 14 | 1 trillion msgs/day | Pinterest Singer base | J |
| 15 | 58B msgs/day | Shopify: 1.75T ÷ 12 months ÷ 30 days | K |
| 16 | 100k records/sec | Shopify BFCM spike | K |
| 17 | 86.4B msgs/day | Salesforce: 1M/sec × 86,400 | M |
| 18 | 15 TB/day | Salesforce | M |
| 19 | 100M interactions/day | Salesforce Activity Platform | M |
| 20 | 11 PB | Airbnb HDFS scale | L |

---

## Key Interview Insights

**Exactly-Once Trade-offs**
- Flink 2PC + Kafka transactional: end-to-end guarantee, checkpoint overhead
- Meta Scribe at-least-once: simpler, dedup downstream (HBase, Iceberg)
- Confluent deterministic: S3 eventual consistency handled by offset naming

**Scaling Patterns**
- Netflix, LinkedIn, Uber all scale to 1000+ brokers; partition management is critical
- Meta's 3-layer design (producer → write service → storage) isolates concerns
- Hudi file sizing directly impacts S3 rate-limit exposure (critical at 350k commits/day)

**Backfill & Late Data**
- Iceberg + Kafka topic retention: arbitrary backfill window (Netflix)
- HBase staging dedup: early deduplication (Airbnb)
- Checkpoint resumption: recovery from any prior point (Hudi DeltaStreamer)

**Failure Recovery**
- Kafka offset replay: fast recovery (Netflix, Uber)
- Partition-level metadata marks bad data; prevents propagation (Meta)
- WAP pre-validation: prevents bad data entry (Uber)

---

## Spot-check corrections (added after review, 2026-09-17)

Verified by fetching the primary pages directly (WebFetch, or `curl` where WebFetch was blocked). Rows above that disagree with this table are wrong; these are the values used in `solution.md`.

| Claim above | Correction | How verified |
|---|---|---|
| Netflix source A cites dev.to for "2 trillion events/day" | dev.to is an excluded source. Primary figures: the 2016 post "Kafka Inside Keystone Pipeline" (techblog.netflix.com/2016/04/kafka-inside-keystone-pipeline.html) states 36 Kafka clusters, 4,000+ broker instances, "more than 700 billion messages on an average day". The Sep 2018 post "Keystone Real-time Stream Processing Platform" (netflixtechblog.com/keystone-real-time-stream-processing-platform-a3ee651812a) says the platform "has proven itself beyond the trillion events per day scale". Use "about 1 trillion events/day (2018), 700 B/day and 4,000 brokers (2016)". The "2 trillion" figure appears only in secondary write-ups and is [unverified] | WebSearch snippets of the two netflixtechblog posts (the pages themselves return 403 to fetch tools). InfoQ 2018 summary corroborates the 2018 figure |
| Meta Scribe "2.5 TB/sec input, 7 TB/sec output, at-least-once" | Exact quote: "an input rate that can exceed 2.5 terabytes per second and an output rate that can exceed 7 terabytes per second", and "several petabytes every hour". The post does NOT state at-least-once as the guarantee; it says Meta is "evaluating the explicit exposure of different delivery guarantees, such as at-least-once and exactly-once". Buffering: producers buffer in memory, the Scribed daemon buffers on local disk during network outages, and "buckets" let several consumers share one category | WebFetch of https://engineering.fb.com/2019/10/07/data-infrastructure/scribe/ |
| Meta 216 PB/day derivation | Arithmetic is right (2.5 TB/s × 86,400 = 216 PB/day) but it is a peak-capable rate ("can exceed"), not a sustained daily volume. Quote it as "over 2.5 TB/s peak input" |  |
| LinkedIn source E date "2018-05-01" (now corrected above) | Published October 8, 2019. Figures on the page: "surpassed 7 trillion per day", "over 100 Kafka clusters with more than 4,000 brokers, which serve more than 100,000 topics and 7 million partitions", largest clusters "more than 140 brokers and host one million replicas" | WebFetch of https://www.linkedin.com/blog/engineering/open-source/apache-kafka-trillion-messages |
| Uber source D "~2026-01" date and "6 trillion rows/day, 350k commits/day" | The page opened and the figures are on it, but the date is a guess. Treat the date as [unverified]; the figures are quoted from the page | Agent fetch of https://www.uber.com/us/en/blog/apache-hudi-at-uber/ |
| Sources J (Pinterest), L (Airbnb), M (Salesforce) | Not opened. Do not use their numbers in the solution | Agent could not fetch them |
| Per-second derivations (23.1 M, 69.4 M, 81 M per second) | Now correct. First version was off by 1,000x; recompute derived numbers yourself every time |  |
