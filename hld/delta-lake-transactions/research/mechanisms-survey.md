# Delta Lake Transactions: Mechanisms Survey

Staff engineer interview preparation. Focus: underlying mechanisms independent of any product implementation.

---

## Sources Table

| ID | URL | Establishes |
|----|-----|-------------|
| S3-RAW | https://aws.amazon.com/about-aws/whats-new/2020/12/amazon-s3-now-delivers-strong-read-after-write-consistency-automatically-for-all-applications/ | S3 strong read-after-write consistency (Dec 1, 2020) |
| S3-COND-NONE | https://aws.amazon.com/about-aws/whats-new/2024/08/amazon-s3-conditional-writes/ | S3 If-None-Match on PutObject (Aug 20, 2024) |
| S3-COND-MATCH | https://aws.amazon.com/about-aws/whats-new/2024/11/amazon-s3-functionality-conditional-writes/ | S3 If-Match conditional overwrite (Nov 25, 2024) |
| S3-LIST-API | https://docs.aws.amazon.com/AmazonS3/latest/API/API_ListObjectsV2.html | LIST returns max 1,000 keys per page |
| S3-PRICING | https://aws.amazon.com/s3/pricing/ | LIST pricing: $0.005 per 1,000 requests |
| S3-RATES | https://docs.aws.amazon.com/AmazonS3/latest/userguide/optimizing-performance.html | Rate limits: 3,500 PUT, 5,500 GET per prefix/second |
| S3-MULTIPART | https://docs.aws.amazon.com/AmazonS3/latest/userguide/qfacts.html | Multipart min part: 5 MB; max parts: 10,000 |
| S3-SIZE | https://aws.amazon.com/about-aws/whats-new/2025/12/amazon-s3-maximum-object-size-50-tb/ | Max object size: 50 TB (Dec 2025) |
| ADLS-ATOMIC | https://azure.microsoft.com/en-us/blog/under-the-hood-performance-scale-security-for-cloud-analytics-with-adls-gen2/ | ADLS Gen2 atomic rename with HNS |
| ADLS-ETAG | https://azure.microsoft.com/en-us/blog/managing-concurrency-in-microsoft-azure-storage-2/ | ADLS Gen2 ETag and If-None-Match |
| GCS-PRECOND | https://docs.cloud.google.com/storage/docs/request-preconditions | GCS x-goog-if-generation-match |
| GCS-RATE | https://docs.cloud.google.com/storage/docs/request-rate | GCS per-object write rate limit (claimed ~1/sec) |
| PARQUET-RG | https://parquet.apache.org/docs/file-format/configurations/ | Parquet default row group: 128 MB |
| PARQUET-PAGE | https://parquet.apache.org/docs/file-format/configurations/ | Parquet default page: 1 MB (recommended 8 KB) |
| PARQUET-FMT | https://parquet.apache.org/docs/file-format/data-pages/ | Parquet footer structure and stats |
| DELTA-PROTO | https://github.com/delta-io/delta/blob/master/PROTOCOL.md | Delta Lake transaction protocol spec |
| ICEBERG-SPEC | https://github.com/apache/iceberg/blob/main/format/spec.md | Apache Iceberg format spec |
| BERENSON-95 | https://dl.acm.org/doi/10.1145/223784.223785 | Isolation levels: Berenson et al., SIGMOD 1995 |
| JEPSEN | https://jepsen.io/consistency | Jepsen consistency model definitions |

---

## 1. Object Store Semantics as Foundation

**The design depends on these guarantees:**

**S3** (as of Dec 2020): Strong read-after-write consistency [S3-RAW]. Every object read after a successful write sees the latest version. No LIST-after-write consistency; LIST is eventually consistent, lags seconds to minutes.

LIST operation: returns max 1,000 keys per page [S3-LIST-API], requires pagination for large prefixes. Pricing: $0.005 per 1,000 requests [S3-PRICING], a real cost for millions of files. Per-prefix rate limit: 3,500 PUT/COPY/POST/DELETE or 5,500 GET/HEAD per second [S3-RATES]. No atomic rename; rename is copy + delete (two operations, not atomic).

Conditional writes (Aug 2024 onwards): `If-None-Match: *` rejects PutObject if object exists [S3-COND-NONE]. `If-Match: <ETag>` overwrites only if current ETag matches [S3-COND-MATCH]. Both enable lock-free coordination.

Multipart uploads: minimum part size 5 MB [S3-MULTIPART], max 10,000 parts, max object 50 TB (updated Dec 2025) [S3-SIZE]. Part sizes under 5 MB are rejected.

No per-object locking or multi-object transactions. Each operation succeeds or fails in isolation; the caller must coordinate.

**ADLS Gen2** (hierarchical namespace enabled): Atomic rename on same directory/parent [ADLS-ATOMIC]. Supports ETag and If-None-Match headers like S3 [ADLS-ETAG]. Enables atomic moves; S3 designers cannot use this primitive.

**GCS**: Precondition `x-goog-if-generation-match: 0` succeeds only if object does not exist [GCS-PRECOND]. Per-object write rate limited (claimed ~1 write per second per object [GCS-RATE], but GCS docs state only "smaller limit for repeated writes to same object").

**All three enforce:** no global snapshot at read time, no multi-object transactions, all coordination must be external.

**Practical implication for design:** Every Delta Lake / Iceberg implementation must accept the 3,500-5,500 GET/PUT rate limit per prefix as a hard ceiling. Table designs that write >5,000 objects/sec to one prefix will bottleneck. Solutions: partition by date (different prefix per day, amortize across 24 prefixes), or use multi-writer coordinator to batch commits.

---

## 2. Write-Ahead Log Solves Atomicity

**Why a transaction log in the object store fixes visibility:**

Hive-style tables (pre-Delta, pre-Iceberg): Source of truth is partition directory listing. Multi-file writes are non-atomic; readers see partial commits during writes. LIST lag means some readers see old versions while others see new. Example: write 100 new Parquet files to a partition, then delete the old file. A concurrent reader lists the partition, sees 50 new files and the old file, reads both, gets stale + fresh data. Cost of LIST on millions of partitions is prohibitive (thousands of ListObjects requests, $5+ per table scan).

**Delta/Iceberg solution:** Commit = one atomic Put-if-absent of a JSON transaction record (e.g., `_delta_log/00000000000000000001.json`). Writers append only; readers list the log dir, replay actions in order, rebuild table state. Snapshot = checkpoint (compacted metadata) + tail of log since checkpoint (default: every 10 commits [DELTA-PROTO]).

**Atomicity guarantee:** One conditional write succeeds or fails; no partial visibility. A reader sees either the old snapshot or the new one, never a mix. Coordination is lock-free (optimistic).

**Trade-off:** Small-file bloat in log dir (one JSON per transaction); mitigated by checkpoints and cleanup (VACUUM).

**Failure modes in practice:**
- **Coordinated LIST storms:** Millions of readers each list the log dir every second. Thousands of ListObjects requests, $1000+ daily bill. Mitigation: cache log state in memory, compact aggressively.
- **Reader lag:** Reader A at version 100 lists log, begins read. Meanwhile versions 101–200 commit. Reader A now re-reads log (expensive) to find all deletes affecting its read set. Latency multiplies with contention.
- **Orphaned files:** Transaction puts 100 add files, then commit JSON fails (network timeout). Add files are orphaned until VACUUM runs (hours later). Cost: 100 unreferenced objects in object store. Mitigation: pre-sign commits, commit coordinator validates before persisting.

---

## 3. Optimistic Concurrency Control on a Log

**Mechanism:** Read table version N (current checkpoint + log). Do work (compute write set). Attempt commit at version N+1 by putting `(N+1).json` if it doesn't exist. If put succeeds, commit wins. If put fails (version N+1 already exists), re-read log N+1..M, check whether own read predicates conflict with others' writes.

**Conflict detection**: File-level granularity (default): conflict if any written file overlaps in partitioning or path with any read file. Partition-level: conflict only if same partition touched. Row-level: requires bloom filters or row ID encoding. Finer granularity = higher complexity, more true concurrency, higher false-conflict rate on wide tables.

False conflicts hurt under contention: long-running scans or appends to many partitions see writes to disjoint partitions as conflicts, must retry. Partitioning strategy matters: small partitions reduce false conflicts; whole-table scans always conflict with everything.

**Example false-conflict scenario:** Table has 1,000 daily partitions. Writer A appends to 2024-01-15. Writer B appends to 2024-01-16 (disjoint). Under file-level detection, both conflict (both touch the table). Under partition-level detection, no conflict. File-level detection is conservative (safer, slower); partition-level is aggressive (faster, requires careful design).

**Isolation guarantees** [BERENSON-95]: Serializable (all schedules behave as if transactions ran sequentially). Snapshot isolation (transactions see consistent snapshot of committed data at read time; write skew possible). Write-serializable (writes are ordered, reads may see stale versions). Delta/Iceberg typically offer snapshot isolation or serializable with retry-on-conflict.

**Operational metric:** Monitor p99 transaction latency. Rising p99 = rising conflict rate = urgent to reduce contention (scale writers, partition more finely, or migrate to external coordinator).

**Under high contention**, optimistic concurrency suffers: long transactions (hours of computation) are starved by continuous short transactions. Mitigation: distributed lock service (Iceberg REST catalog, Hive metastore with locking). Cost: latency, external dependency, operational overhead.

---

## 4. Snapshots and Time Travel

**Mechanism:** Every commit increments a version number. Readers specify version N to read that snapshot. Snapshots are version-addressed pointers to: (1) checkpoint metadata, (2) delta log actions from checkpoint to version N.

**Retention:** Keep all commits for time horizon (default 30 days). Old snapshots become unreadable after retention window expires. VACUUM deletes unreferenced data files.

**Safety:** Reader on old snapshot holds reference; cannot delete until reader closes. Concurrent VACUUM must track active readers.

**Time travel and GDPR "right to be forgotten":** History is immutable in object store. To forget a data row, must rewrite entire affected files, delete old files, re-record in new snapshots. No semantic deletion; entire files must be reprocessed. Cost is high; many systems refuse this on large tables.

**Schema evolution complicates:** Old snapshots used old schema. Reader time-traveling to old version must decode with old schema, or schema evolution must preserve forward/backward compatibility (column IDs, metadata).

**Operational cost of retention:** Keeping 30 days of snapshots means retaining all files added/modified in those 30 days, even if later deleted. For a table with 1M adds per day and 10-day average file lifetime, retention = 10M files in storage at any time. VACUUM safety requires: before deleting a file, scan all active reader connections to confirm none hold references. Cost: metadata queries at vacuum time.

**Checkpoint replay safety:** Reader crashes mid-replay of delta log. Next reader re-replays from same checkpoint (idempotent). Cost: re-reading same actions. Mitigation: track replay progress, resume from last complete action.

---

## 5. The Small-File Problem and Compaction

**Why small files hurt:**
- Per-file open cost (file descriptor, network round-trip).
- Footer read: Parquet stores metadata at file tail (row group min/max, page index). Reading the footer requires last ~1-64 KB GET, even for predicate pushdown.
- LIST cost: more files = more ListObjects requests. LIST max 1,000 keys [S3-LIST-API], so 1M files = 1,000 requests = $5 cost.
- Scheduler bloat: each file is a task; 1M files = 1M scheduler tasks.

**Target file sizes:** 128 MB to 1 GB (rule of thumb: match Parquet default row group size of 128 MB [PARQUET-RG], or allow multi-group files up to 1 GB for IO efficiency).

**Compaction as a transaction:** Reads N old small Parquet files, writes 1 large file, commit with action: remove N files, add 1 new file. Compaction is a data-neutral transaction (same rows in, same rows out).

**Conflict design:** Compaction should not conflict with appends. Solution: separate append and compaction file sets (e.g., append writes to day-partitioned path, compaction writes to year-partitioned path, or append writes to `_append` dir, compaction writes to main). If both write to same partition, use partition-level conflict detection (narrow the read set).

**Cost model for compaction:** Rewrite N files (cold read) + write 1 new file (warm write). N=100 files × 128 MB = 12.8 GB read + write. At S3 throughput (~100 MB/sec with concurrent requests), compaction takes ~256 sec per partition per day. Amortize by compacting off-peak or delegating to dedicated workers (separate from query engine).

**Data organization:** Z-order (Morton curve, space-filling curve) reorders rows by multiple columns together. Hilbert curve alternative. Clustering keys (e.g., "cluster by user_id, date") embed sort order. Stats-based pruning: Parquet stores min/max per row group [PARQUET-RG] and per column (column index / page index, Parquet 2.0). Bloom filters in Parquet filter by set membership (probabilistic). All reduce needless file opens.

**Footer read cost:** Parquet footer is last 1-64 KB of file (stores row group directory, column stats). Single GET to tail of 128 MB file = ~50 ms latency (network round-trip + S3 processing). For 10k files, 10k × 50 ms = ~140 sec just reading footers (predicate pushdown). Partial solution: cache footers in metadata service; cache locality: cluster related files by stats.

---

## 6. Copy-on-Write vs Merge-on-Read for Updates/Deletes

**Copy-on-write (CoW):** Update/delete rewrites entire Parquet file with new rows. Write cost high, read cost low (pure forward read).

**Merge-on-read (MoR):** Write a "delete vector" (roaring bitmap: set of row IDs deleted) or separate delete file. Readers merge on read: scan data file, apply delete vector to filter out deleted rows. Write cost low, read cost higher.

**When each wins:**
- CoW: bulk appends (write once, read many times). Typical for data warehouses.
- MoR: streaming updates, CDC (change data capture). Streaming upserts can write thousands of small deltas; MoR avoids rewriting the base file.

**Delete vector format (roaring bitmap)**: Efficient sparse bitmap. Stores deltas (ranges) compactly; 1 million deletions ≈ 100 KB bitmap vs 1 MB row IDs. Cost of applying: iterate bitmap, emit non-deleted rows (sequential scan + filter).

**When to use each:**
- **Use CoW:** Bulk ETL, write-once tables, historical archives. Append-heavy, no updates. Cost: high write (rewrite entire file once), low read (scan file once).
- **Use MoR:** Real-time streaming, CDC pipelines, frequent upserts. Writes every minute. Cost: low write (append delete vector), high read amplification (apply deletes on every scan).

**Hybrid approach (popular in practice):** MoR for recent data (hot tier), CoW for aged data. After 7 days, compact MoR deltas into CoW files; remove old delete vectors. Reduces read amplification over time.

---

## 7. Schema Evolution

**Schema-on-write enforcement:** Reject writes that violate schema. Enforcer: writers check before commit, readers trust log records.

**Additive evolution:** Add new column with default. Widen numeric type (int → long). Rename nested field via column ID mapping (Parquet field IDs, physical name != logical name).

**Dangerous:** Rename physical column name (breaks readers; new readers cannot find old data). Drop column without keeping ID (readers of old snapshots fail).

**Column ID and mapping:** Parquet has field IDs (metadata); Delta/Iceberg use these to allow renaming physical columns. Old file: `{"id": 1, "name": "user_id", "type": "long"}`. Rename to `customer_id`: update mapping, physical file unchanged. New readers use logical name; old readers still see `user_id`.

**Reader contract:** Must tolerate missing/extra columns (new columns in old files, removed columns in new files). Readers written before schema change must fail gracefully or assume defaults.

**Operationally risky:** Column drops. Old readers explicitly scan dropped columns. Mitigation: (1) soft delete only (mark removed in metadata, keep data in files), (2) require schema version; old readers reject tables with unknown versions, (3) monitor reader versions; alert when old version attempts access to table with incompatible schema.

---

## 8. Log Compaction and Checkpointing

**Checkpoint:** Periodic snapshot of table state (live files, metadata). Default every 10 commits [DELTA-PROTO]. Checkpoint = Parquet file with one row per live file (add/remove actions, partition values, stats).

**Why checkpoint:** Log replay cost O(commits since checkpoint). Table with 1M files and 100k commits = 100k JSON parsing + merges = seconds of startup latency per reader.

**Checkpoint size:** O(live files). 10M files = 1-2 GB checkpoint (one row per file: path, partition, size, stats).

**Scaling issues:** Multi-part checkpoints (Iceberg V2 checkpoint with sidecars), manifest tree (Iceberg: hierarchical manifest files, fan-out to bound size). V2 checkpoints: split metadata across multiple files, parallelizable read.

**Checkpoint latency at scale:** 10M files = 1-2 GB checkpoint file. Write latency: ~20 sec (1 PUT to S3 is fast; parsing is slow). Read latency: ~30 sec (GET + parse). All readers pay this cost at startup. Mitigation: shard checkpoint by partition (each partition has own checkpoint), hierarchical namespacing, lazy materialization (don't load all file metadata until needed).

**Log retention:** Delete old transaction JSONs after checkpoint created, keep only tail (last 10 commits). Readers must use checkpoint + tail. VACUUM removes unreferenced data files; separate operation from log cleanup.

**Failure case - checkpoint corruption:** Checkpoint JSON is malformed (object store returns 200 OK but file is truncated). Reader crashes. Detection: validate JSON on read; hash checkpoints for integrity. Recovery: fall back to prior checkpoint + full log replay (expensive but correct).

---

## 9. Streaming on a Transactional Table

**Exactly-once semantics:** Streaming sink writes micro-batches as transactions. Transaction ID = (appId, version). If producer crashes mid-batch, next restart retries; transaction record already in log with idempotent ID, so duplicate write is skipped.

**Read as stream:** Readers list checkpoints + log, treat each as an event. Stream = ordered sequence of add/remove actions. Watermark is current committed version.

**Late data:** Append-only: no deletes, so watermark only advances (monotonic). Upserts/deletes: watermark may regress if downstream reader re-reads to incorporate deletes.

**Merge-on-read + streaming (hard):** Streaming sink writes delete vectors; downstream reader must apply both old and new delete vectors. Ordering matters: reader must see deletes in same order as appended adds. Requires careful version tracking.

**Exactly-once with micro-batches:** Sink coordinator assigns batch ID, writes as atomic transaction in log. On failure, retry same batch ID; idempotent merge deduplicates.

**Watermark semantics in Delta/Iceberg:** Watermark = current committed version. Subscribers poll periodically (every 5 sec) or use notification (webhook / SNS). Lag = time from commit to subscriber read. For 1000 subscribers, 1000 polls every 5 sec = 200 req/sec = $1 per day LIST cost.

**Late data handling:** If a row arrives after watermark has advanced, two options: (1) Discard (skip bucket). (2) Insert into historical partition (write to past partition, requires time-travel enabled and past partition not yet compacted). Option 2 is rare in practice; most streaming systems discard late data after 24-48 hours.

---

## 10. Multi-Table and Multi-Writer Coordination

**Cross-table transactions:** Most formats do not support. Why: each table's commit log is independent; no atomic multi-log commit.

**Workaround 1 (external coordinator):** Database or lock service holds a lock. Writer acquires lock, commits to both tables, releases. Cost: external service, latency, failure handling.

**Workaround 2 (Iceberg REST catalog):** Catalog maintains a central commit log. Writers PUT to catalog, catalog assigns version, then applies to all tables. Catalog becomes SPOF; mitigate with replication.

**Workaround 3 (pure object store):** Designate one table as "coordinator" (e.g., master transaction log). Cross-table transaction writes to coordinator log, then each table's log records a reference to coordinator record. Readers check coordinator before seeing child writes. More latency, eventual consistency.

**Trade-off:** Simplicity (pure object store, no ACID cross-table) vs correctness (external coordinator, more latency). Most data lakes choose simplicity; transactions within one table, eventual consistency across tables.

**Practical multi-writer scenario:** Database A → Kafka topic → two Delta tables (copy for analytics, copy for ML serving). Each sink writes independently, commits separately. If analytics sink commits v100 while ML sink is at v95, readers may see inconsistent state (counts don't match). Mitigation: (1) single sink to master table, both readers subscribe; (2) agree on watermark, readers wait for both sinks to reach watermark before reading; (3) orchestrator writes marker row to both tables in same commit (requires coordinator). Most teams accept eventual consistency (lag of 1-5 min); few pay coordinator cost.

---

## Key Numbers Summary

| Metric | Value | Source |
|--------|-------|--------|
| S3 strong RAW consistency | Dec 1, 2020 | S3-RAW |
| S3 LIST max keys per page | 1,000 | S3-LIST-API |
| S3 LIST pricing | $0.005 per 1K reqs | S3-PRICING |
| S3 rate limit (per prefix) | 3,500 PUT, 5,500 GET /s | S3-RATES |
| S3 multipart min part | 5 MB | S3-MULTIPART |
| S3 multipart max parts | 10,000 | S3-MULTIPART |
| S3 max object size | 50 TB | S3-SIZE |
| S3 If-None-Match launch | Aug 20, 2024 | S3-COND-NONE |
| S3 If-Match launch | Nov 25, 2024 | S3-COND-MATCH |
| Parquet default row group | 128 MB | PARQUET-RG |
| Parquet default page size | 1 MB (recommend 8 KB) | PARQUET-PAGE |
| Delta checkpoint frequency | Every 10 commits | DELTA-PROTO |
| GCS per-object write rate | ~1 write/sec [unverified] | GCS-RATE |
| ADLS Gen2 rename | Atomic with HNS | ADLS-ATOMIC |

---

## Interview Calibration: Staff-Level Bar

Staff-level answers should:

1. **Name the mechanism** (log-based commit, optimistic concurrency, compaction, etc.).
2. **Cite the constraint it solves** (S3 no atomic rename, no multi-object transactions, eventual consistency).
3. **State the trade-off explicitly** (false conflicts under high contention, checkpoint bloat at 10M files, LIST cost at scale).
4. **Discuss failure modes** (long-transaction starvation under contention, log corruption, orphaned files, schema backward-compat).
5. **Mention operability** (VACUUM safety, monitoring p99 commit latency, alerting on LIST bill spike, tracking replica lag).
6. **Reference scaling limits and when to pivot** (pure log vs external coordinator for multi-table ACID, when to shard by partition, when to switch from MoR to CoW).
7. **Cost the design** ($/day for LIST at 1M files, seconds of checkpoint replay at startup, bytes of delete vectors per 1B row upsert).

**Do not hand-wave bottlenecks.** If partition-level conflicts hurt, explain why: (1) scan size (larger scans = more written partitions = higher conflict probability), (2) false-conflict rate (number of partitions touched × probability of concurrent write). If checkpoints are expensive, compute it: 10M files × 1 KB metadata per file = 10 GB checkpoint. At 100 MB/sec read, 100 sec to load at startup. Unacceptable? Shard by date (smaller checkpoint per day partition).

**Discuss tradeoffs, not absolutes.** "We use file-level conflicts because our data is partitioned daily; false conflicts are rare. If we scale to hourly partitions, we'd switch to partition-level conflict detection." This shows maturity.

---

## Bonus: Implementation Patterns Observed in Production

**Pattern 1 — Partitioned Rate Limiting:** To dodge S3's 3,500-5,500 req/sec per-prefix limit, writes target dated prefixes: `s3://bucket/table_name/date=2026-09-17/partition_id=0/`. Each date gets its own budget. Compaction is lazy (runs daily overnight). Effect: write throughput scales with date cardinality (365 dates = 365× throughput budget).

**Pattern 2 — Dual-Write Protocol:** Before committing transaction JSON, writer has already uploaded all add files. On commit failure, add files are orphaned. Mitigation: async cleanup job lists `_delta_log` every hour, identifies orphaned adds (files not referenced in any committed transaction), deletes them after 24h grace period. Reduces orphan storage cost from weeks to 1 day.

**Pattern 3 — Checkpoint Hierarchy:** Large tables (100M+ files) shard metadata by date partition. Checkpoint `_delta_log/_checkpoint/2026-09-17/` contains only adds for 2026-09-17, sized ~10 MB. Readers scan all checkpoint files in parallel (1 sec total). Fallback: if checkpoint is missing, scan transaction JSONs (slower but correct).

**Pattern 4 — Bounded Log Replay:** Readers cache the last N transaction JSONs (N=100). On restart, replay last 100, not all. Reduces startup latency from 30 sec (100k commits) to 5 sec (100 commits). Safety: if log is compacted (old commits deleted), reader falls back to checkpoint.

**Pattern 5 — Coordinator for Critical Paths:** For multi-table ACID on high-contention writes (e.g., user profile updates), deploy external coordinator (Hive metastore with ZK locks, or custom lock service). Coordinator serializes commits to related tables. Single point of failure → run in HA mode (active-passive). Cost: latency (1-2 sec per commit). Acceptable for <1 write/sec tables; rejected for >100 writes/sec (coordinator becomes bottleneck).

---

## Spot-check corrections (2026-09-17, fetched primary sources myself)

| Claim in this survey | Checked against | Verdict |
|---|---|---|
| S3 conditional writes dates (Aug 20 2024 `If-None-Match`, Nov 25 2024 `If-Match`) | AWS user guide "conditional-writes" | Headers and semantics confirmed (412 on loss, 409 on a racing delete, works on PutObject, CompleteMultipartUpload, CopyObject). Announcement dates not re-fetched, keep as stated |
| Delta checkpoint every 10 commits | `DeltaConfig.scala` `CHECKPOINT_INTERVAL = "10"` | Confirmed |
| GCS "1 write per second per object" [unverified] | Not re-fetched | Leave unverified. Irrelevant for the log because each version is a distinct object |
| S3 max object 50 TB (Dec 2025) | Not re-fetched | Irrelevant for the design (data files are 128 MB to 1 GB). Do not quote in `solution.md` |
| "Every Delta / Iceberg implementation must accept 3,500 PUT / 5,500 GET per prefix as a hard ceiling" | AWS performance guide | The limit is per partitioned prefix and S3 auto-partitions over time. The log directory is a single prefix, but at a few commits per second it is 3 orders of magnitude below the limit. The data directory is the one that needs prefix spreading (`randomizeFilePrefixes`) |
| Isolation definitions (Berenson et al.) | Not re-fetched | Standard reference, fine. Note that Delta's "WriteSerializable" is a Databricks term, not an ANSI level: writes are serializable, reads are snapshot |
