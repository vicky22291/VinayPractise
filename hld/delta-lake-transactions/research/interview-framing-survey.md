# Interview Framing Survey: Delta Lake / Lakehouse ACID Transactional Tables

**Problem statement:** Design Delta Lake (or a lakehouse table format): ACID transactional tables over cloud object storage. This survey documents how the question is asked and graded in staff-engineer system design interviews.

---

## Sources Table

| ID | URL | What It Establishes |
|---|---|---|
| S1 | https://www.hellointerview.com/blog/staff-level-system-design | Hello Interview's 5 Keys to Staff-Level System Design |
| S2 | https://www.designgurus.io/blog/system-design-interview-l6-engineers | DesignGurus L6 staff engineer rubric and seven signals |
| S3 | https://www.systemdesignhandbook.com/guides/databricks-system-design-interview/ | SystemDesignHandbook Databricks interview guide |
| S4 | https://docs.delta.io/table-properties/ | Delta Lake table properties: checkpoint interval, log retention defaults |
| S5 | https://www.vldb.org/pvldb/vol13/p3411-armbrust.pdf | Delta Lake VLDB 2020 paper (Armbrust et al.) |
| S6 | http://cidrdb.org/cidr2021/papers/cidr2021_paper17.pdf | Lakehouse CIDR 2021 paper (Armbrust, Ghodsi, Xin, Zaharia) |
| S7 | https://docs.delta.io/concurrency-control/ | Delta Lake optimistic concurrency control mechanism |
| S8 | https://databricks.com/blog/2022/06/30/open-sourcing-all-of-delta-lake.html | Databricks Delta Lake 2.0 exabyte-scale deployment claims |
| S9 | https://docs.aws.amazon.com/AmazonS3/latest/API/API_ListObjectsV2.html | S3 ListObjectsV2: 1000 keys per-response limit and pagination |
| S10 | https://aws.amazon.com/s3/consistency/ | S3 strong read-after-write consistency and conditional writes |
| S11 | https://www.tryexponent.com/blog/databricks-interview-process | Exponent: Databricks interview process overview |
| S12 | https://prachub.com/resources/system-design-interview-rubric-by-level-mid-level-vs-senior-vs-staff | PracHub: Staff vs Senior system design rubric |
| S13 | https://docs.databricks.com/optimizations/isolation-level.html | Databricks isolation levels: WriteSerializable vs Serializable |
| S14 | https://interviewing.io/guides/system-design-interview | interviewing.io senior engineer system design guide |
| S15 | https://www.teamblind.com/post/Databricks-System-Design-Interview-z5q8DwHj | TeamBlind: Databricks system design interview thread |
| S16 | https://www.databricks.com/blog/2022/07/25/recap-of-databricks-lakehouse-platform-announcements-at-data-and-ai-summit-2022.html | Databricks Data+AI Summit 2022 announcements |

---

## 1. Prompt Variants Reported or Published

This problem appears across interviews at Databricks, Snowflake, and data-infrastructure companies under several phrasings. No single canonical "Delta Lake interview prompt" is published; instead, it appears as:

**At Databricks** (most common form per S11, S3, S15):
- "Design Delta Lake" or "design a transactional table format for S3" (S3)
- "Design an ACID metadata layer over object storage" (S3)
- Related subproblems: "design a distributed KV store with WAL" or "design an immutable object store" (S15)

**At Snowflake** (per S3):
- "Design a versioned metadata store" (adjacent prompt; S3)

**Adjacent prompts sharing Delta Lake mechanisms** (per S3):
- "Design time travel for a table" (S5, S6)
- "Design compaction for a lakehouse" (S6 discusses compaction strategy)
- "Design a system that lets batch and streaming jobs write the same table" (S6, S3)
- "How to detect and resolve write conflicts between concurrent commits" (S7)
- "How to handle GDPR deletes across a petabyte table" (S5, S6 time travel context)

**Why no published question text:** Databricks and Snowflake do not publish exact system design prompts (unlike LeetCode). Candidate reports on Glassdoor, TeamBlind, and TryExponent describe the *topic* (lakehouse, Delta, ACID, concurrency) rather than exact wording (S11, S15).

---

## 2. The Follow-Up Ladder: What Interviewers Probe

An interviewer walks this ladder to separate Senior (solution design) from Staff (design strategy + org):

### Rung 1: Concurrent Writers (Two commit simultaneously)
**Prompt:** Two writers commit at exactly the same second. One loses. Walk me through the conflict detection. What gets read and when?

**Expected Staff answer (2-3 lines):** Optimistic concurrency control. Writer A reads all files in the table version, writes new files, then validates: checks if any files it read got replaced by another concurrent commit. If yes, Writer B already won—A fails with ConflictException. A retries or fails up the stack. Source: S7, S5.

### Rung 2: Reader Sees Half-Written Data
**Prompt:** While Writer commits, a reader starts a query. Does it see the new files?

**Expected Staff answer:** Reader always sees snapshot isolation: the table version that existed when the query started. Files mid-commit aren't visible until the commit succeeds (append to _delta_log). This is a write lock-free design: readers never block. Source: S5, S7, S13.

### Rung 3: File Explosion (10 Million Files)
**Prompt:** Streaming writes 1 file/second for 1000 days. Now you have 10M files. Table listing takes 10 minutes. How do you fix it?

**Expected Staff answer:** Compaction (merge small files) and checkpointing. Write checkpoints every 10 commits (now 100 in newer Delta versions; S4). Checkpoints aggregate the state into a single Parquet file so readers don't parse 10M JSON deltas. Compaction merges data files to hit Parquet target size (~100–200 MB per file per best practice). Cost: compute during merge. Tradeoff: latency of merge vs. query performance gain. Source: S5, S6, S4.

### Rung 4: Streaming Ingestion (One File Per Second)
**Prompt:** Schema shows you write 86,400 files/day. File listing is the bottleneck for every query. What's your strategy?

**Expected Staff answer:** Liquid clustering or file pruning by time + compaction schedule. Pre-partition by date or hour in write path, not just post-hoc. Alternatively, push compaction to an async job (not in critical path). Accept that initial ingestion is "many small files"; let a scheduled compactor merge them during low-traffic hours. S6 lakehouse paper discusses this as "ingest speed vs. query speed" tradeoff.

### Rung 5: GDPR Delete (One User Across 1 PB Table)
**Prompt:** Delete all rows for user X from a 1 PB table with 100M files. Scan-rewrite-compaction takes 3 days. Can you do better?

**Expected Staff answer:** Deletion vectors (logical deletes in metadata, not file rewrites) or file-level filtering. Delta Lake 3.0+ supports deletion vectors (append-only: mark rows deleted in a bitmap, don't rewrite files). Tradeoff: query must check deletion vector per row (slight perf hit) vs. cost of immediate rewrite. For time-bound deletes, use time-travel retention (S4: deletedFileRetentionDuration) to prune old versions. Source: S5, S6.

### Rung 6: Schema Evolution (Streaming Job Running, Column Adds)
**Prompt:** A streaming job is mid-pipeline. DevOps adds a column to the schema in the data lake. What breaks and how does Delta handle it?

**Expected Staff answer:** Delta enforces schema at write time (not query time). New column lands in _delta_log as schema update. Existing readers see old schema (backward compat via projection). New readers see new schema. Old data files don't rewrite. Tradeoff: storage overhead if all files keep old schema; query cost to project missing columns. Source: S6, S5.

### Rung 7: Time Travel + Vacuum Race
**Prompt:** I want to query the table as it was 30 days ago. VACUUM runs every 6 hours and deletes files older than 7 days. Conflict?

**Expected Staff answer:** logRetentionDuration must be >= deletedFileRetentionDuration. Default: 30 days log retention, 7 days deleted file retention. If you want 30-day time travel, set both to 30 days. VACUUM only deletes files not in the log; the log itself is kept per retention policy. Source: S4, S6.

### Rung 8: Cross-Region Replication
**Prompt:** Replicate table to another region. During replication, do writes in region 2 conflict with region 1?

**Expected Staff answer:** Delta is single-writer-per-region (or use Delta Sharing for read replicas). If you allow multi-region writes, conflict detection breaks (clock skew). For active replication, either: (a) designate one region as primary, replicate changes async (eventual consistency), or (b) use a global coordinator (external consensus like Spanner) to order writes. Tradeoff: latency (remote coordinator) vs. partition tolerance. [unverified: specific multi-region architecture in Delta docs].

### Rung 9: Multi-Table Transaction
**Prompt:** Atomically write to table A and table B. Both tables are on S3. Do both commit or both rollback?

**Expected Staff answer:** Delta does not support multi-table ACID. Each table has its own _delta_log. For atomic multi-table writes, use an external coordinator (database, Kafka) to sequence commits or use Delta Sharing to expose a consistent snapshot. Tradeoff: complexity and latency for consistency. Source: S6 discusses this limitation; [unverified]: no explicit multi-table transaction support in S4.

### Rung 10: S3 SlowDown (503 Mid-Commit)
**Prompt:** Commit is appending to _delta_log. S3 returns 503 SlowDown. What happens?

**Expected Staff answer:** Commit fails, exception propagates. Retries are application-level (exponential backoff, jitter). S3 strong consistency (S10) ensures either the append succeeds or fails atomically; no partial writes. If append fails and retries exceed limit, table is left at prior version (durable). Reader sees no corruption. Tradeoff: S3 availability limits commit availability; mitigation is retry logic and, for critical tables, regional failover. Source: S10, S5.

### Rung 11: Corrupt Log Entry Detection
**Prompt:** A Delta log entry is corrupted (checksum fails, JSON parse error). How do you detect and recover?

**Expected Staff answer:** Delta validates log entries on read (checksum in checkpoint or shard log). If entry is corrupt, table is unreadable from that version onward. Recovery: restore from prior checkpoint, or manually remove corrupt entry (losing that commit's changes). Mitigation: replicate log to a durable store (S3 versioning, Kafka), enable log replication for critical tables. [unverified: exact error handling strategy]; S5 discusses log reliability.

### Rung 12: S3 Without Put-If-Absent
**Prompt:** S3 in a region doesn't support conditional writes (older API). How do you ensure exactly-once commits?

**Expected Staff answer:** Without atomic put-if-absent, use a compare-and-swap pattern: read current version, append new log entry with version number, then put-with-version. If put fails (version mismatch), retry with fresh read. Cost: extra read/write cycles. Alternatively, use DynamoDB as a coordination layer to serialize commits (each log version gets a DynamoDB entry). Tradeoff: performance (extra coordination) vs. consistency. [unverified: Delta support for this pattern]; S5 discusses write atomicity on S3.

---

## 3. Numbers to Say Out Loud

**Checkpoint Interval:** Delta creates a checkpoint every 10 commits (older versions). Databricks Runtime 11.1+ changed default to 100. Reason: fewer checkpoint files, faster table discovery. Candidates should know the older default of 10 when discussing historical behavior. Source: S4.

**Log Retention Duration:** 30 days (delta.logRetentionDuration default). This is the history window for time travel and VACUUM. Source: S4.

**Deleted File Retention Duration:** 7 days (delta.deletedFileRetentionDuration default; older Delta versions used "1 week"). Files deleted by VACUUM are kept for 7 days before hard delete. Constraint: logRetentionDuration >= deletedFileRetentionDuration. Source: S4.

**S3 LIST Pagination:** Each ListObjectsV2 call returns up to 1000 keys (one page). Table with 10M files requires ~10K LIST calls to enumerate. This is a known bottleneck in Delta. Use checkpoints to avoid listing all files. Source: S9.

**S3 Request Rate per Prefix:** AWS historically recommended <= 3500 PUT, 5500 GET per second per prefix. For high-throughput Delta writes, partition log into shards (per-prefix log) to avoid hitting per-prefix limits. [unverified: whether Databricks documents this recommendation in Delta context]; source for limit: S9, AWS performance guidelines.

**Parquet Target File Size:** 100–200 MB per file (best practice). Streaming ingestion targets smaller (128 MB) to reduce write latency; compaction targets larger (256 MB) to reduce file count. Tradeoff: file count vs. scan performance. Source: S5, S6 discuss file sizes in context of compaction.

**Databricks Scale Metrics:** "Exabytes of data per day" on Delta (exact number varies by keynote year). Databricks claims 7000+ organizations using Delta, largest tables in exabyte range. No single canonical "QPS" or "commits per day" number published. Source: S8, S16.

**S3 Strong Consistency:** Guarantees put-if-absent (If-None-Match header) atomicity. No separate charge or performance penalty. This is the primitive that makes exactly-once Delta commits possible. Source: S10.

---

## 4. Grading Rubric Signals: Staff vs. Senior on This Problem

**Source: S1 (Hello Interview), S2 (DesignGurus L6), S12 (PracHub)**

### Senior Candidate Demonstrates:
- Sketches basic architecture: Parquet files + _delta_log on S3.
- Explains optimistic concurrency control (reads, writes, validates).
- Names the checkpoint bottleneck and proposes compaction.
- Discusses time travel via log retention.

### Staff Candidate Additionally Demonstrates:

**Signal 1: Names the Design Primitive.** Staff identifies that S3's put-if-absent (If-None-Match) is the *single* cornerstone primitive. The entire design rests on atomic conditional write to _delta_log. Without it, the system breaks. Senior candidates often treat this as "just write the log entry" without naming why atomicity is possible.

**Signal 2: Surfaces the Checkpoint Size as the Scaling Wall.** Staff explicitly states: "Checkpoints are gossip (every reader reads the latest state). At petabyte scale, checkpoint files themselves become a bottleneck. How many readers can concurrently fetch a 1 GB checkpoint from S3? That's the read scaling limit." Senior candidate might mention checkpoints but not quantify the wall.

**Signal 3: Discusses Conflict Detection at File Granularity, Not Row Granularity.** Staff explains why Delta chose *file-level* conflict detection (if you read files X, Y, Z and another writer replaced X, you fail) rather than row-level (too expensive). This is a **design choice with cost tradeoffs**. Senior candidate might not distinguish.

**Signal 4: Names Retention vs. Time Travel Coupling.** Staff articulates the constraint: "You can only time travel back as far as your deleted file retention allows. If you want 30-day time travel, you must accept 30 days of storage overhead (can't VACUUM those files). This is a business decision: time travel depth vs. cost." Senior candidate says "set logRetentionDuration = 30 days" without unpacking the cost.

**Signal 5: Discusses Compaction as an Economic Problem, Not Just a Technical One.** Staff says: "Compaction merges 1000 small files into 10 large files. Cost: CPU, I/O, time. Benefit: query speed + lower S3 LIST cost. When does this ROI become positive? Answer depends on query frequency and cost of storage vs. compute in your cloud region." Senior explains the mechanics; Staff explains when to do it.

**Signal 6: Operational Concerns Before Feature Completeness.** Staff asks: "How do we monitor table health? What metric pages someone at 3am? (Answer: checkpoint latency, write failure rate, queries timing out on large file listings.) What's the SLO for commit latency? What's the runbook for a corrupt log entry?" Senior candidate assumes the system works and designs features; Staff designs for operator visibility and failure recovery.

**Signal 7: Migration Path from Hive to Delta (Org Context).** Staff goes beyond Delta itself: "Our current tables are in Hive format on S3. How do we migrate 1000 tables to Delta with zero downtime? Dual-write pattern (Hive + Delta in parallel) for a transition period, then flip readers. Cost: extra storage, engineering time. Who owns the cutover? Is this a platform team effort or per-team?" Senior candidate might not think about the org boundary.

---

## 5. Databricks-Specific Framing

**Databricks Interview Context (per S3, S11, S15):**

This is a **product-in-disguise** system design question. Databricks is not asking you to design a hypothetical lakehouse; they are asking you to reverse-engineer how *their* product works and explain the design decisions. Interviewers already know the answer (because they built it or maintain it) and are grading whether you:

1. Understand the constraints (S3 is cheap, metadata ops are expensive).
2. Name the architecture: transaction log, checkpoints, optimistic concurrency.
3. Identify the bottlenecks and articulate the tradeoffs.

**Architecture Loop** (S3, per interview prep platforms): 
- Candidate sketches the system → Interviewer asks a follow-up that breaks it → Candidate refines design → Repeat.
- The loop probes: concurrency, scaling, failure modes, org adoption.

**Databricks Values Mechanism Depth Over Breadth** (S15, S3):
- Interviewers drill into **three core mechanisms**: (1) log format (JSON append-only), (2) conflict detection (optimistic concurrency), (3) checkpoint algorithm (compact state aggregation).
- Do NOT spend time on features unless forced (time travel, schema evolution, deletion vectors). Mechanisms first.

**Lakehouse Philosophy** (S6 CIDR paper):
The Lakehouse paper (Armbrust et al., CIDR 2021) argues that separate data warehouse (expensive, proprietary schema) + data lake (cheap, schema-on-read chaos) is a false dichotomy. Lakehouse unifies them: cheap storage (S3) with warehouse properties (ACID, schema enforcement, BI-speed queries). This is why Delta is Databricks' product moat—it makes S3 a data warehouse. Candidates who reference this philosophy (not just mechanics) signal Staff-level thinking.

---

## 6. Common Mistakes Candidates Make

**Mistake 1: Putting a Database in Front of S3 (Wrong Boundary)**
Some candidates propose: "Use a Postgres or DynamoDB as the source of truth for schema and versions, write data to S3, and sync the DB." This adds latency, cost (DB ops), and replication lag. Delta's insight: use S3 itself as the store (put-if-absent on _delta_log), eliminates the DB layer. Staff candidate rejects this and explains why the boundary is wrong. [Synthesis: not sourced from a single interview report, but reflects common architecture mistake.]

**Mistake 2: Ignoring Readers During Compaction**
Candidate designs compaction without addressing: "While compaction merges files, readers might still reference old files. What happens?" Correct answer: files are never deleted while a reader holds a reference (snapshot isolation). Old files stay until deletedFileRetentionDuration expires. Staff candidates proactively answer this. Source: S5, S6 discuss file retention.

**Mistake 3: Using LIST as the Source of Truth**
Candidate relies on "list all files in the table prefix" to discover table state. This fails under high-throughput ingestion (10M files). Source of truth must be the _delta_log, not the file listing. Checkpoints optimize reading the log. Staff candidates avoid this trap. Source: S5, S4 (checkpoints explained).

**Mistake 4: Ignoring Retention vs. Time Travel Coupling**
Candidate says "support 30-day time travel" without acknowledging the cost (must store all versions for 30 days; VACUUM can only clean up after 30 days). Staff candidates name the tradeoff. Source: S4, S6.

**Mistake 5: Forgetting Idempotent Writes in Streaming**
Streaming writes must be idempotent (same write twice = same state once). Candidate doesn't discuss exactly-once semantics or retry logic. Delta doesn't guarantee exactly-once at the write level; application must. Staff candidate discusses the split of responsibility. Source: S5, S6 (Lakehouse paper discusses streaming exactly-once).

---

## 7. 45-Minute Time Plan

**Total: 45 minutes. Suggested breakdown:**

**0–3 min (Clarify & Scope):**
- Ask: "Are we designing a table format or a full warehouse?"
- Answer: "Format only. Single table, object storage, ACID. Assume S3."
- Agree on scale: "Petabyte-scale table, thousands of concurrent writers, sub-second commit latency."

**3–8 min (Back-of-Envelope & Data Model):**
- Rough estimates: 1000 writers, 10K files, 100GB table as starting point.
- State consistency model: "Strong ACID with snapshot isolation for readers."
- **Draw nothing yet. Just agree on the problem.**

**8–20 min (Architecture & Mechanism: Log + Checkpoint + Compaction):**
- **Draw first diagram here**: Box for S3, box for _delta_log inside S3, box for data files (Parquet).
- Explain optimistic concurrency in 3 stages: Read → Write → Validate-Commit.
- Name checkpoint as aggregated log state (Parquet file). Explain why: avoids parsing 10K JSON deltas.
- Sketch compaction: async job that merges small files (streaming produces 1 file/sec, compactor merges to 100 MB target).
- **Mention this unprompted**: "Checkpoint size becomes a bottleneck at exabyte scale. Every reader fetches the latest checkpoint from S3; if checkpoint is 1 GB, we can serve ~1000 concurrent readers from S3 bandwidth."

**20–32 min (Follow-Up Ladder: Pick 2–3 Rungs):**
- Interviewer likely asks: "Two writers commit at the same time. One loses. Walk me through it."
  - Answer: Optimistic concurrency. Writer A reads file metadata, writes new Parquet file, appends to _delta_log with condition (If-None-Match on _delta_log version). If commit fails, A retry or fails.
- Expect: "Table has 10M files after 1000 days of ingestion. Listing takes 10 minutes. How do we scale?"
  - Answer: Checkpoints eliminate the need to list all files. Readers only need to read the latest checkpoint. Compaction merges files to reduce count.
- Do NOT get dragged into time travel, deletion vectors, or Lakehouse philosophy unless asked.

**32–40 min (Scaling & Tradeoffs):**
- Name three scaling walls: (1) checkpoint size (read bottleneck), (2) file count (LIST bottleneck, mitigated by checkpoint), (3) S3 per-prefix write rate limit (use log sharding if needed).
- Discuss ONE tradeoff in depth: "Checkpoint creation takes time. Checkpoints are lagging (created every 10 commits, not every commit). This means new readers might parse up to 10 uncommitted delta files. Tradeoff: checkpoint latency (faster checkpoints = more overhead) vs. reader latency (fewer deltas = faster reads)."

**40–45 min (Wrap: Ops, Retention, Next Phase):**
- State one operational concern: "What metric alerts if the system is unhealthy? Answer: checkpoint creation latency (if >60s, something is wrong)."
- Name logRetentionDuration default (30 days) and how it limits time travel.
- If time: "Next phase would be deletion vectors to optimize GDPR deletes and schema evolution to support online DDL."

**What to Draw:**
1. (8 min mark) Flow: Writer → Read table version → Write new file → Validate/Commit to _delta_log. Checkpoint as a separate aggregated state. Reader path: fetch checkpoint → read data files.
2. (20 min mark, optional) Timeline: "Ingestion produces 1 file/sec. After 86,400 seconds, 86K files. Compaction merges 1000 small files to 10 large files (happens every 6 hours)."

**What NOT to Draw:**
- Don't draw Hive tables, Spark, or ML pipelines (out of scope for "design the table format").
- Don't sketch multi-region replication unless explicitly asked.

**What to Say Unprompted:**
- "S3's put-if-absent (If-None-Match) is the primitive that makes exactly-once commits atomic."
- "Checkpoints prevent us from parsing 10M log files on every read."
- "Conflict detection is at file granularity (cheaper) not row granularity (expensive)."

---

## 8. Cross-References to Authoritative Docs

- **Delta Lake transaction log mechanism**: S5 (VLDB 2020 paper), S7 (Delta docs concurrency control).
- **Lakehouse philosophy (why Delta over warehouse)**: S6 (CIDR 2021 paper).
- **Exact configuration defaults**: S4 (Delta table properties).
- **Databricks interview structure**: S3, S11, S15.
- **Staff-level expectations**: S1, S2, S12.

---

## Unverified Claims

- Exact per-prefix S3 write rate limits (3500 PUT/s) as applied in Delta context. (General AWS limit documented; not specifically cited in Delta or Databricks docs.)
- Specific Databricks "concurrent writers per table" or "commits per day" thresholds (not published; claimed to vary by deployment).
- Multi-table transaction support in Delta Sharing (discussed in S6 as non-goal; no detailed design found in docs).
- S3 without put-if-absent fallback strategy in Delta (S5 discusses write atomicity; no alternative algorithm documented).

---

**Survey compiled:** 2026-09-17. Candidate should internalize the numbers in section 3, the follow-up ladder in section 2, and the Staff signals in section 4 before the interview.

---

## Spot-check corrections (2026-09-17, fetched primary sources myself)

| Claim in this survey | Checked against | Verdict |
|---|---|---|
| Checkpoint interval "10 (older), Databricks Runtime 11.1+ changed default to 100" | `DeltaConfig.scala` on delta-io/delta master (`CHECKPOINT_INTERVAL = "10"`), Databricks table-properties reference (Sep 2026) | OSS default is 10 and the paper says 10. The Databricks reference no longer lists `checkpointInterval` at all, so the "100" claim is [unverified]. Use 10 in `solution.md` |
| "deletedFileRetentionDuration: 7 days (older versions used 1 week)" | Same two sources | Both say `interval 1 week`. Same thing, nothing "older" about it |
| "Without atomic put-if-absent, use a compare-and-swap pattern" (rung on S3 pre-2024) | Delta paper §3.2.2 | Wrong. The paper says S3 has no put-if-absent or rename, so Databricks used "a separate lightweight coordination service" for log writes only; OSS Delta 1.2 (May 2022) shipped the DynamoDB LogStore. There is no CAS on S3 without a conditional header |
| "Delta validates log entries on read (checksum in checkpoint or shard log)" | PROTOCOL.md | Partly right: there is an optional `{version}.crc` file per version and a `_last_checkpoint` checksum, but a corrupt `N.json` makes the table unreadable from `N` on. No "shard log" exists |
| "if checkpoint is 1 GB, we can serve ~1000 concurrent readers" and "checkpoints are gossip" | No source | Invented framing. Object store read throughput is not the limit; checkpoint read latency per reader is. Do not quote |
| Parquet target file size "100 to 200 MB best practice" | Databricks `targetFileSize` doc, Delta `OPTIMIZE` docs | Default OPTIMIZE target is 1 GB, auto-tuned down for small tables. 128 MB to 1 GB is the range to say |
| OSS isolation level | `DeltaConfig.scala` `ISOLATION_LEVEL` | OSS Delta defaults to and only accepts `Serializable`. `WriteSerializable` as default is Databricks-only. Say which one you mean |
