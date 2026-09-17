# Real-World Architectures: Delta Lake, Iceberg, Hudi, Snowflake

## Sources Reference

| ID | Source | Establishes |
|---|---|---|
| [1] | https://dl.acm.org/doi/10.14778/3415478.3415560 | Delta Lake VLDB 2020, Vol 13 No 12 (Aug 2020); architecture, S3 DynamoDB coordination, metadata performance |
| [2] | https://github.com/delta-io/delta/blob/master/PROTOCOL.md | Checkpoint interval, log/deleted-file retention, action types (add, remove, metaData, protocol, txn, commitInfo, cdc, domainMetadata) |
| [3] | https://docs.databricks.com/aws/en/tables/data-skipping | Data skipping on first 32 columns by default, `delta.dataSkippingNumIndexedCols` configuration |
| [4] | https://docs.databricks.com/aws/en/sql/language-manual/delta-optimize | OPTIMIZE target 1 GB, bin-packing algorithm, `spark.databricks.delta.optimize.maxFileSize` |
| [5] | https://docs.databricks.com/aws/en/optimizations/isolation/isolation-levels | Serializable vs WriteSerializable isolation; retry logic on conflict |
| [6] | https://aws.amazon.com/about-aws/whats-new/2024/08/amazon-s3-conditional-writes | S3 If-None-Match header, PutObject/CompleteMultipartUpload, Aug 20 2024 announcement |
| [7] | https://iceberg.apache.org/rest-catalog-spec/ | Iceberg REST catalog API, metadata.json, snapshots, manifest lists, manifest files |
| [8] | https://iceberg.apache.org/terms/ | Iceberg terminology, snapshot, manifest, equality/position delete files |
| [9] | https://docs.snowflake.com/en/user-guide/data-time-travel | Time travel 1 day Standard, 90 days Enterprise; Fail-safe 7 days |
| [10] | https://docs.snowflake.com/en/user-guide/tables-clustering-micropartitions | Micro-partitions 50-500 MB uncompressed; FoundationDB for metadata |
| [11] | https://www.uber.com/us/en/blog/apache-hudi-graduation/ | Hudi copy-on-write, merge-on-read, record-level index for O(1) upsert routing |
| [12] | https://delta.io/blog/2023-07-05-deletion-vectors/ | Deletion vectors enable merge-on-read for DELETE/UPDATE/MERGE; row-position bitmaps |
| [13] | https://docs.databricks.com/aws/en/delta/deletion-vectors | Deletion vector support: Delta 2.3 (read-only), 2.4 (DELETE), 3.x (UPDATE/MERGE) |
| [14] | https://docs.databricks.com/aws/en/delta/uniform | UniForm: asynchronous Iceberg metadata generation; minReaderVersion 2, minWriterVersion 7 |
| [15] | https://delta.io/blog/2022-05-18-multi-cluster-writes-to-delta-lake-storage-in-s3/ | S3DynamoDBLogStore: DynamoDB PutItem for atomic version coordination; ~200 bytes per commit |
| [16] | https://docs.delta.io/delta-storage/ | Storage API abstraction; atomic rename (ADLS, GCS), conditional put (S3 post-2024) |
| [17] | https://netflixtechblog.com/optimizing-data-warehouse-storage-7b94a48fdcbe | Netflix S3 cost: listing partitions expensive; Hive rename non-atomic; Iceberg motivation |
| [18] | https://docs.delta.io/delta-change-data-feed/ | Change Data Feed: insert/update/delete tracking; _change_data folder; schema evolution support |
| [19] | https://www.databricks.com/blog/delta-lake-explained-boost-data-reliability-cloud-storage | Databricks adoption: 7,000+ organizations, exabytes/day, 75% of platform scans use Delta |

---

## 1. Delta Lake Protocol: Log-Structured Write-Ahead Log

Delta Lake maintains a write-ahead log in `_delta_log/` as JSON files with zero-padded version numbers: `00000000000000000000.json`, `00000000000000000001.json`, etc. Each version is immutable once written; the log is append-only. [1][2]

**Actions and Metadata:** Each log entry contains one or more actions: 

- `add`: new data file with path, size, modification time, and per-file statistics (min/max/null for tracked columns).
- `remove`: tombstone marking file as deleted (includes deletion timestamp for VACUUM decisions).
- `metaData`: schema, partition columns, created timestamp, Delta format version, table configuration (e.g., `delta.columnMapping.mode`).
- `protocol`: reader/writer version constraints (clients must support these to safely read/write).
- `txn`: application-level transaction ID for idempotent writes (e.g., Spark job ID + retry count).
- `commitInfo`: timestamp, user, operation name (INSERT, UPDATE, MERGE, DELETE), and metrics.
- `cdc`: Change Data Feed records when CDC is enabled.
- `domainMetadata`: extensible domain-specific metadata (e.g., lineage, cost tags).

Each action is a JSON object. [2]

**Checkpoints and State Reconstruction:** By default, a checkpoint is written after every 10 commits. Checkpoints are Parquet files stored in `_delta_log/` named by version: `00000000000000000009.checkpoint.parquet`. A checkpoint contains all actions up to that version, with invalid `remove` entries pruned. [1][2]

A `_last_checkpoint` file records the latest checkpoint's version and action count, enabling fast table snapshot: readers load only the checkpoint Parquet and subsequent JSON files, skipping the full log replay. Version 2 checkpoints introduced multi-part Parquet (for >2GB checkpoints) and compressed/indexed formats. [2]

**Log Retention and VACUUM:** `delta.logRetentionDuration` (default: `interval 30 days`) controls how old log JSON files are kept. `delta.deletedFileRetentionDuration` (default: `interval 7 days`) determines when deleted data files become eligible for VACUUM. After 30 days, old log files are deleted, making time travel beyond that window impossible unless checkpoints cover it. [2]

---

## 2. Atomic Commits: Per-Object-Store Mechanisms

Fundamental challenge: cloud object stores (S3, ADLS, GCS) are eventually consistent key-value systems with no built-in put-if-absent or compare-and-swap. Delta's commit strategy adapts to each store's atomic guarantees. [1]

**S3 Limitation and S3DynamoDBLogStore (Historical):** 

S3 has no atomic conditional put-if-absent. Multiple writers could simultaneously write version `N`, both believing they succeeded, causing data loss. To solve this, Delta introduced S3DynamoDBLogStore: writers first write ~200 bytes of commit metadata to a DynamoDB table using PutItem (which is atomic: returns success only if the item key does not exist). Only after DynamoDB confirms does the writer commit the JSON file to S3. [1][15]

This coordination requires:
- Shared DynamoDB table (same name, region across all clusters).
- IAM permissions for S3 and DynamoDB.
- Hadoop aws-sdk JAR and delta-storage-s3-dynamodb JAR.
- Network latency: write incurs DynamoDB PutItem (~10-50ms typically) + S3 PUT (~100-200ms). [15]

**S3 Conditional Writes (August 2024):**

AWS announced native If-None-Match header support for PutObject and CompleteMultipartUpload on August 20, 2024. If-None-Match checks ETag before write; if present, write fails with 412 Precondition Failed (idempotent). This enables put-if-absent natively, reducing external coordinator dependency. [6]

Early investigations suggest Delta/Iceberg may adopt S3 conditional writes post-2024 to eliminate DynamoDB for new deployments, but legacy tables using DynamoDBLogStore continue working. [6]

**ADLS and GCS:** 

ADLS Gen2 supports atomic rename (metadata-only operation); GCS has atomic conditional rename. Delta uses rename for single-writer or leader-follower patterns where only one writer per version is expected. [16]

**Delta 4.0+ Coordinated Commits:**

Introduced a pluggable "commit coordinator" abstraction. Writes can opt into catalog-managed commits via a REST API: catalog (Databricks, Glue, REST Iceberg catalog, or custom) coordinates versions and validates snapshots. This decouples Delta from object-store workarounds. [1]

---

## 3. Concurrency Control and Isolation Levels

Delta uses optimistic concurrency: readers record the table version at read time; writers collect their read set (list of files read) and write set (files added/removed), then check for conflicts on commit. No locking during read/write execution. [1]

**Two Isolation Levels:**

1. **Serializable:** All committed writes and reads appear to execute in a serial order. Strongest guarantee; rejects some concurrent writes that don't conflict logically. Ensures strict ACID.

2. **WriteSerializable (default):** Only writes are serializable; reads may see intermediate states not in the log. Balances data consistency and throughput. Allows readers to see phantoms (files from newer versions). [5]

**Conflict Detection on Commit:**

When a writer commits version `N+1`, it reads the log from version `R` (its read version) to `N`. If any added file overlaps with its read set or write set (partition-level check), a conflict exists. Conflict matrix depends on operations: INSERT vs UPDATE/DELETE/MERGE, and partition disjointness. [1][5]

If conflict detected:
- Serializable mode: retry with a fresh read from the latest version.
- WriteSerializable mode: may succeed if operations are disjoint (e.g., INSERT into partition A, UPDATE into partition B). [5]

Retry logic: the writer re-checks its read set against newly added files. If still no conflict, commits; otherwise, retries. Large number of retries can cause commit timeout and application-level backoff. [1]

---

## 4. Delta Lake Features and Implementation

**Data Skipping and Statistics:**

Delta collects per-file min/max and null-count statistics on the first 32 columns by default (configurable via `delta.dataSkippingNumIndexedCols`). At query time, the planner evaluates filter predicates against file stats: if a file's min > filter max, skip it. [3]

Z-ordering (ZORDER BY columns) reorders rows to cluster on multiple columns, improving stats effectiveness. Liquid clustering automatically reorders on common join/filter columns during writes. [3]

**OPTIMIZE and Compaction:**

OPTIMIZE runs bin-packing: scans all files, collects those <1 GB, groups them into "bins" until each bin ~1 GB, rewrites bins as new files. Default target is 1 GB (configurable via `spark.databricks.delta.optimize.maxFileSize` = 1073741824). [4]

Auto-optimize runs at write time for streaming ingestion, preventing small-file accumulation. Bin-packing is idempotent: running twice has no effect on the second run. Target size is tuned per Databricks experience; 1 GB balances memory usage and compute efficiency. [4]

**Deletion Vectors (Merge-on-Read):**

Instead of rewriting files on delete/update, Delta appends bitmap files marking deleted row positions. Introduced in Delta 2.3 (read-only), with DELETE support in 2.4, and UPDATE/MERGE in 3.x. Readers merge base data with deletion bitmaps at scan time. [12][13]

Benefits: faster writes for small deletes, lower I/O churn. Drawback: read cost increases if deletes accumulate (OPTIMIZE WITH DV REWRITE periodically rewrites). [12]

**Change Data Feed (CDC):**

When enabled, CDC tracks every insert/update/delete at row level. Changes written to `_change_data` folder as Parquet with `_change_type` column (INSERT, UPDATE_PREIMAGE, UPDATE_POSTIMAGE, DELETE). Enables incremental replication and real-time CDC pipelines. [18]

Schema evolution with column mapping (Delta 2.2+) supports CDC on tables with column renames/drops, though non-additive schema changes require care. [18]

**Schema Enforcement and Evolution:**

Schema enforcement: new writes must match table schema exactly, preventing accidental misschema ingestion. Schema evolution allows adding nullable columns or broadening integer types (INT to BIGINT). [2]

Column mapping (by name or ID) decouples logical column names from physical Parquet field names, enabling safe renames and drops without full table rewrites. `delta.columnMapping.mode = 'name'` or `'id'`. [2]

**Time Travel and Query History:**

Query as-of a version or timestamp: `SELECT * FROM table VERSION AS OF 5` or `SELECT * FROM table TIMESTAMP AS OF '2024-01-01'`. Limited by log retention (default 30 days). Timestamp-based queries must find the version closest to that timestamp by scanning commit times in log. [2]

**UniForm (Iceberg Interoperability):**

Databricks' UniForm feature automatically generates Iceberg metadata (metadata.json, snapshots, manifests) asynchronously while writing Delta. Single Parquet data files are simultaneously readable by Delta and Iceberg clients (Snowflake, BigQuery, Redshift, Athena). [14]

Requirements: Unity Catalog registration, column mapping enabled, minReaderVersion >= 2, minWriterVersion >= 7. Iceberg clients see consistent snapshots and manifest isolation. [14]

---

## 5. Apache Iceberg: Externalized Metadata and Catalog

Iceberg separates immutable data (Parquet) from versioned metadata. A `metadata.json` file is the single version pointer; it references the current snapshot; snapshots list manifest lists; manifest lists reference manifest files; manifests enumerate data files with partition keys, stats, and delete file references. [7][8]

**Catalog Requirement:**

The catalog (Hive Metastore, Glue, REST API, or Nessie) maintains the metadata.json pointer and enforces atomic compare-and-swap on commit. Without a catalog, metadata cannot be safely updated on object stores (no atomic CAS). Catalog acts as lock manager and version registry. [7]

This is Iceberg's key trade-off: external metadata service is mandatory, but it enables perfect ACID semantics independent of object store guarantees. [7]

**Row-Level Deletes:**

Iceberg uses two delete file types:
- Position delete files: record `(file_path, row_position)` of deleted rows.
- Equality delete files: record deleted row values; readers match by equality and exclude them.

This decouples delete semantics from copy-on-write and enables efficient row-level deletion without full-file rewrites. [8]

**REST Catalog (Introduced 0.14, 2022):**

OpenAPI spec defines HTTPS endpoints for namespace/table management, metadata loads, and snapshot commits. Enables Iceberg work cross-cloud and polyglot (Python, Java, Go clients). [7]

---

## 6. Apache Hudi: Primary Key and Record-Level Index

Hudi mandates a primary key and maintains a record-level index: `(key -> file group)`. On upsert, the index routes the record to its file group without table scan (O(1) lookup). [11]

**Copy-on-Write (CoW) vs Merge-on-Read (MoR):**

- **CoW:** Rewrites affected file groups immediately; snapshot includes all latest data. Zero read amplification, high write latency.
- **MoR:** Appends delta files; readers lazily merge base and delta. Lower write latency, higher read cost. Hudi 1.x added multi-modal indexing (Hudi Record Index) enabling O(1) lookups via in-memory map. [11]

Uber's innovation (2024): partial copy-on-write within Apache Parquet using row-level indexes to skip data pages, combining CoW write latency with MoR read efficiency. [11]

---

## 7. Snowflake: Centralized Metadata in FoundationDB

Snowflake stores data as immutable micro-partitions (50 to 500 MB uncompressed each) in cloud storage. All versioning, transactions, and metadata reside in FoundationDB (internal distributed transactional KV store), not in the object store. [10]

**Time Travel:**

- Standard Edition: 1 day retention.
- Enterprise Edition: up to 90 days (configurable).
- Fail-Safe: non-configurable 7-day recovery window after time travel expires. [9]

Metadata transactions in FoundationDB record which micro-partitions are live at each version. This decouples versioning from object store semantics entirely. [9][10]

**Advantage:** Perfect ACID without external log. **Disadvantage:** FoundationDB is a proprietary Snowflake component; not portable to other systems. [9][10]

---

## 8. Key Numbers and Benchmarks

**Delta Lake (VLDB 2020, Vol 13 No 12, August 2020):** [1]

- 10x speedup on metadata operations (table stats, schema reads) vs Apache Hive over S3.
- Handles tables with 10,000+ files without listing throughput collapse.
- Checkpoint writes reduce log replay latency from minutes (full scan) to seconds (load checkpoint + recent files).
- S3 LIST operations: expensive at scale (~millions of files). Motivated transition to log-based approach.

**Protocol Defaults:** [2]

- Checkpoint interval: 10 commits.
- Log retention (`delta.logRetentionDuration`): 30 days.
- Deleted file retention (`delta.deletedFileRetentionDuration`): 7 days.
- Data skipping indexed columns: 32 (first N columns).
- OPTIMIZE target file size: 1 GB (1073741824 bytes).

**S3 Conditional Write (August 20, 2024):** [6]

- If-None-Match header support on PutObject and CompleteMultipartUpload.
- No additional AWS charges.
- Available across all AWS regions and GovCloud.

**Snowflake Micro-Partitions:** [10]

- Size: 50 to 500 MB uncompressed.
- Time Travel retention: 1 day (Standard), 90 days (Enterprise).

**Databricks Platform Scale (2024-2025):** [19]

- 7,000+ organizations use Delta Lake.
- Exabytes of data processed daily on Databricks platform.
- 75% of data scanned on Databricks platform comes from Delta tables.

---

## 9. Big Companies: Adoption Motivations

**Netflix (2017, Iceberg Creation):** [17]

S3 table listing was expensive and non-deterministic at scale. Apache Hive relied on filesystem rename semantics (not atomic in S3, required copy). Atomic metadata swap was not guaranteed. Netflix created Iceberg to enable safe table format with atomic snapshots, snapshotting via external catalog (Hive Metastore + S3 atomic rename). Open-sourced 2017.

**Uber (Hudi Adoption and Contribution):**

High-frequency upserts (CDC from transactional databases) required primary key semantics. Hive lacked efficient record-level updates. Uber adopted Hudi and contributed copy-on-write and merge-on-read modes; later (2024), pioneered partial copy-on-write with row-level Parquet indexes. [11]

**Databricks (Delta Lake Creator and Scale):**

Operates Delta Lake at exabyte scale. Internal telemetry shows 75% of scans on Databricks platform use Delta tables. Databricks continues investing in UniForm (Iceberg interop), coordinated commits, and liquid clustering. [19]

---

## 10. Convergence and Divergence

All three formats now support time travel, schema evolution, CDC, and row-level deletes. Convergence on features is happening (e.g., Delta UniForm, Iceberg delete files, Hudi multi-modal index). [1][7][11][12][14]

Key divergences remain:

- **Metadata location:** Delta in object store (simpler, single point-of-failure), Iceberg external catalog (more operational complexity, perfect ACID).
- **Concurrency model:** Delta optimistic (retry-heavy under contention), Iceberg catalog-managed (external lock), Hudi record-indexed (primary key requirement).
- **Cost model:** Delta/Iceberg pay per LIST/object store operation; Snowflake includes metadata in compute cost (FoundationDB transactions). [1][7][10]


---

## Spot-check corrections (2026-09-17, fetched primary sources myself)

| Claim in this survey | Checked against | Verdict |
|---|---|---|
| Checkpoint every 10 commits, log retention 30 days, deleted file retention 7 days, stats on 32 columns | `DeltaConfig.scala` on delta-io/delta master, Databricks table-properties reference (Sep 2026), Delta paper §3.2.1 | All confirmed. Exact strings: `"10"`, `"interval 30 days"`, `"interval 1 week"`, `32` |
| S3 conditional writes: `If-None-Match` on PutObject and CompleteMultipartUpload, Aug 20 2024 | AWS user guide "conditional-writes" | Confirmed, plus CopyObject. Loser gets `412 Precondition Failed`; a concurrent delete can produce `409 Conflict`. `If-Match` (ETag) added later (Nov 2024) |
| Paper: VLDB 2020 Vol 13 No 12 | pvldb vol13 p3411 PDF | Confirmed. Extra numbers from the PDF: "at least 5 to 10 ms of base latency" per object read; LIST "up to 1000 objects per request", "tens to hundreds of milliseconds"; write rate "several transactions per second"; Delta finds files for 1 M partitions in 108 s (17 s cached on SSD) vs Hive over an hour at 10,000 partitions and Presto over an hour at 100,000; "real-world petabyte-scale tables ... contain hundreds of millions of objects" |
| Databricks default isolation WriteSerializable | Databricks isolation-levels page | Confirmed. OSS Delta (`DeltaConfig.scala`) only allows `Serializable` |
| Row-level concurrency | Databricks row-level-concurrency page | Confirmed: DBR 14.3 LTS+, unpartitioned table, deletion vectors on. With it, `UPDATE/DELETE/MERGE + OPTIMIZE` cannot conflict unless `ZORDER BY`, and two `UPDATE/DELETE/MERGE` conflict only on the same row |
| Delta 4.0 "coordinated commits" | PROTOCOL.md master | The spec now calls it the `catalogManaged` table feature: proposed commits are staged at `_delta_log/_staged_commits/<v>.<uuid>.json` or sent inline, the catalog ratifies exactly one per version, and ratified commits are later published as `<v>.json`. Filesystem-based writers are blocked on such tables |
| Databricks "7,000+ organizations, 75% of scans" | Databricks blog (marketing) | Left as quoted. Do not build math on it |
