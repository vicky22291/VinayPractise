# Edge cases: Delta Lake, transactional tables over object storage

Every entry answerable in under 60 seconds out loud. Categories: failure, consistency, scale, data, operations, security. Design reference: [`solution.md`](solution.md).

---

## Failure

## Edge case: writer crashes after uploading data files, before the commit
- **Trigger:** driver OOM, spot instance reclaimed, network partition between driver and object store after executors finished.
- **Symptom:** nothing. Readers see the previous version. The bucket has 500 extra objects.
- **Answer:**
  - The files are not named by any `N.json`, so no snapshot contains them. Atomicity comes from "the log is the truth", not from cleanup.
  - The job retry writes its own new files and commits them. Two copies of the data exist in the bucket, one referenced.
  - `VACUUM` deletes unreferenced files whose modification time is older than the retention (7 days). Until then they cost storage only.
  - Blast radius: zero for readers, a few dollars of storage.
- **Diagram:** `solution.md` §6 Flow 4.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: the conditional PUT of `N.json` times out with no response
- **Trigger:** S3 503 SlowDown, TCP reset, driver GC pause longer than the client timeout.
- **Symptom:** the writer does not know whether it committed. A naive retry could commit the same actions twice as `N` and `N+1` (duplicate rows).
- **Answer:**
  - Before retrying, GET `N.json`. If 404, retry the conditional PUT. If it exists, compare `commitInfo.txnId` (a uuid the writer put in its own commit) with its own: match means "I won", mismatch means "someone else won, run conflict detection".
  - The conditional header means a retry can never overwrite a different writer's `N.json`.
  - For the streaming sink the `txn(appId, version)` action is a second guard: even if the check above were skipped, the next batch would see its own version already recorded.
- **Diagram:** `diagrams.md` D5 (503 mid-commit).
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: writer commits `N.json` then dies before writing the checkpoint or `_last_checkpoint`
- **Trigger:** `N mod 10 == 0` and the driver dies between the two PUTs.
- **Symptom:** next reader's `_last_checkpoint` points at `N−10`, so it replays 10 to 19 JSON files instead of 0 to 9. Tens of ms extra.
- **Answer:**
  - Both the checkpoint and `_last_checkpoint` are hints. Correctness never depends on them; the LIST from the last known checkpoint finds every newer JSON and any newer checkpoint.
  - A checkpoint written but `_last_checkpoint` not updated is still found by the LIST (readers should prefer the newest complete checkpoint the listing shows).
  - The next writer that commits at a multiple of 10 writes the next checkpoint. If no writer ever comes, an alert on "checkpoint age > 100" triggers a maintenance commit.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: a log entry is missing or corrupt
- **Trigger:** someone ran a lifecycle rule or `rm` on `_delta_log/`, a partial write on a store without atomic PUT (should not happen), a bad tool wrote malformed JSON.
- **Symptom:** every snapshot at or after that version fails to build: "version 100 missing" or a JSON parse error. Every query on the table fails. This is the largest blast radius in the system.
- **Answer:**
  - Detection is immediate and loud. Nothing silently reads wrong data, because the replay refuses gaps.
  - Recovery: restore the object from bucket versioning (mandatory on `_delta_log/`), or from the replica region. If truly lost, `RESTORE` to the last good version (a new commit whose actions bring the live set back) and re-run the idempotent writers for the lost versions.
  - Prevention: bucket policy denies `DeleteObject` on `_delta_log/` to everyone except the cleanup role, and `PutObject` there requires the conditional header.
  - A `{version}.crc` file (optional) lets a reader verify the snapshot summary against what it computed.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: the catalog (when it is the arbiter) is down
- **Trigger:** catalog database failover, region outage of the metadata service.
- **Symptom:** every commit on catalog-managed tables fails; readers cannot learn about unpublished commits.
- **Answer:**
  - Writers retry with backoff; nothing is corrupted because no version can be ratified without the catalog. This is the cost of moving the arbiter off the object store: a 99.99% service on the write path.
  - Readers can still read every *published* version from `_delta_log/` directly, so analytics on slightly stale data continues. Design the catalog to publish ratified commits within seconds so the stale window is small.
  - For tables that cannot accept this dependency, keep them filesystem-managed (object store conditional PUT). The choice is per table.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: object store region outage
- **Trigger:** the region's object store is unavailable or degraded for an hour.
- **Symptom:** all reads and writes fail. No partial state.
- **Answer:**
  - Nothing to roll back: every commit is a single object, either present or absent.
  - Writers retry; streaming jobs resume from their own checkpoint and the `txn` guard prevents duplicates.
  - Reads can fail over to the replica region's copy of the table (replayed log), which is minutes behind. Writes cannot fail over: one home region per table, because a second arbiter would allow two version 101s.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

---

## Consistency

## Edge case: two writers race for the same version
- **Trigger:** two jobs both read version 100 and both try to commit 101.
- **Symptom:** one gets 200, the other 412 (or a DynamoDB conditional check failure, or a catalog rejection).
- **Answer:**
  - Exactly one wins, decided by the put-if-absent primitive. That is the only serialisation point in the design.
  - The loser reads `101.json` and checks: metadata or protocol change (fail), a file it read was removed (fail, re-run), a file it removes was removed (fail), files added in partitions it read (fail under Serializable, ok under WriteSerializable).
  - No conflict: retry the same actions as 102. Conflict: re-run the job from 101.
  - A blind append has no read set, so it always retries without a check.
- **Diagram:** `solution.md` §5.3 decision flow, §6 Flow 3.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: a reader sees a state that "never existed" (WriteSerializable)
- **Trigger:** `DELETE WHERE x` reads v0, an `INSERT` of rows matching `x` commits v1, the delete commits v2 under WriteSerializable.
- **Symptom:** v2 contains the inserted rows even though the delete "came after" them in history. A user asks "why did my delete not delete those rows?"
- **Answer:**
  - WriteSerializable orders *writes* only: the outcome equals the serial order "delete, then insert", which is valid. The history shows insert first, delete second, which is what looks odd.
  - Under Serializable the delete would have failed with `ConcurrentAppendException` and re-run, deleting the new rows too, at the cost of every append conflicting with every concurrent delete on its partitions.
  - Pick per table: streaming ingest tables want WriteSerializable; tables where "delete means everything up to now" want Serializable.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: long query pinned to an old snapshot while files it needs are removed
- **Trigger:** a 30-minute query on version 100; at minute 10 an OPTIMIZE removes 1,000 of the files it is scanning.
- **Symptom:** none, as long as retention holds. The query keeps reading the old files.
- **Answer:**
  - `remove` is a tombstone, not a delete. The files stay for `deletedFileRetentionDuration` (7 days).
  - Only `VACUUM` deletes, and only tombstones older than the retention. A query longer than 7 days is the only way to break this, and that is a config change, not a design change.
  - This is why readers never need to register themselves anywhere: retention is a static promise instead of a lease.
- **Diagram:** `solution.md` §6 Flow 6.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: streaming sink re-executes a micro-batch after a crash
- **Trigger:** the driver dies after committing batch 17 but before writing its own streaming checkpoint; on restart it re-runs batch 17.
- **Symptom:** without a guard, batch 17's rows appear twice.
- **Answer:**
  - The commit of batch 17 included `txn(appId = query id, version = 17)`. The snapshot keeps the latest `txn` version per `appId`.
  - On re-execution the sink reads that version (17 ≥ 17) and skips the write. Exactly-once, because the data and the marker were one atomic commit.
  - `setTransactionRetentionDuration` bounds how long old `txn` markers are kept; a stream that restarts after longer than that must start from a fresh checkpoint.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: two MERGEs on different rows of the same file
- **Trigger:** unpartitioned 1 TB table, two CDC appliers touch different keys that happen to live in the same 1 GB file.
- **Symptom:** without row-level concurrency, the second commit fails `ConcurrentDeleteRead` (the first removed a file the second read) and re-runs its whole join.
- **Answer:**
  - Enable deletion vectors and row tracking on an unpartitioned table: the conflict checker compares row ids, not paths. Both commit; the second's DV is re-based onto the first's new `add`.
  - Without that: partition or cluster by the key range each applier owns, so their read sets are disjoint.
  - Or serialise the appliers upstream into one job with one commit per batch, which is what most pipelines do anyway.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: clock skew between writers and `TIMESTAMP AS OF`
- **Trigger:** writer B's clock is 5 minutes behind writer A's; B commits version 102 with a timestamp earlier than 101's.
- **Symptom:** `TIMESTAMP AS OF` would find versions out of order.
- **Answer:**
  - Delta makes commit timestamps monotonic per table: if a commit's timestamp is not greater than the previous version's, it is set to `previous + 1 ms` (in-commit timestamps make this explicit in `commitInfo`).
  - Timestamp time travel is therefore "the last version whose adjusted timestamp is ≤ t", always well defined.
  - Version numbers are the real identity; timestamps are a convenience. Pipelines that need exactness use versions.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

---

## Scale

## Edge case: the table has 10 M files and the checkpoint is 7.5 GB
- **Trigger:** years of 100 MB files, or a streaming table without compaction.
- **Symptom:** every query spends 10 to 75 s reading the checkpoint before planning; every 10th commit rewrites 7.5 GB.
- **Answer:**
  - First lever: compaction to 1 GB files. 10 M → 1 M files, checkpoint 7.5 GB → 0.75 GB.
  - Second: V2 checkpoints. The checkpoint becomes a manifest plus sidecars; a checkpoint rewrite touches only changed sidecars; a query reads only sidecars whose partition range it needs.
  - Third: stats as struct columns so the checkpoint scan itself prunes, and a per-cluster snapshot cache keyed by version.
  - The Hive-metastore answer (file list in a database) is the wrong direction: the paper reports that metastore becoming the bottleneck at millions of objects.
- **Diagram:** `solution.md` §5.2.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: 50 writers on one table, each committing every second
- **Trigger:** one Delta table per IoT fleet with a writer per device group.
- **Symptom:** the 412 rate climbs past 80%, each writer takes seconds per commit, the log grows by 50 versions/s (4.3 M/day), checkpoints every 0.2 s.
- **Answer:**
  - The physics: one object-store round trip per attempt, one winner per round, so a few commits/s per table is the ceiling under contention.
  - Fix in order: batch upstream (one ingest job, 1 commit/s of 50 groups' files); if the writers must stay separate, move the arbiter to the catalog and let it assign versions to non-conflicting blind appends without a race (~100 commits/s); or give each writer its own table and union them in a view.
  - Never shard one table's log. A log with two version 101s is not a log.
- **Diagram:** `diagrams.md` D10.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: streaming writer with a 1 s trigger and 100 partitions
- **Trigger:** low-latency ingest into a partitioned table.
- **Symptom:** 8.6 M files/day of ~1 MB, query on one day opens 86,400 files, checkpoint grows 6 GB/day.
- **Answer:**
  - Optimized writes: one file per partition per batch instead of one per task. Raise the trigger to 10 s where the SLA allows: 10x fewer files.
  - Auto compaction: after each commit, compact partitions with > 50 files under 128 MB as a `dataChange=false` commit.
  - Hourly `OPTIMIZE` to 1 GB targets with clustering.
  - Cost: ingest bytes rewritten 1 to 2x per day. Say the exchange rate: one extra write per byte for a 10 to 100x smaller file count on every read forever.
- **Diagram:** `solution.md` §5.4.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: a hot partition receives 90% of writes
- **Trigger:** `date=today` partition gets all the appends and all the MERGEs.
- **Symptom:** appends are fine (no read set), but every MERGE on today conflicts with every other MERGE on today at file granularity; OPTIMIZE on today races them.
- **Answer:**
  - Appends never conflict; leave them.
  - MERGEs: enable deletion vectors so OPTIMIZE stops conflicting with them, and row-level concurrency (requires an unpartitioned table, so consider liquid clustering by date instead of partitioning by date).
  - Serialise the MERGE appliers for the hot key range upstream; concurrency on one hot range buys nothing.
  - Reads on the hot partition are unaffected: snapshot isolation.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: S3 per-prefix request limits
- **Trigger:** 5,000 executors writing to one partition directory at once, or VACUUM listing a 10 M file table.
- **Symptom:** 503 SlowDown on data PUTs (3,500 PUT/s per prefix) or on LIST pages.
- **Answer:**
  - Data: `randomizeFilePrefixes` spreads files over random prefixes instead of partition directories, so S3 partitions the key space. The log does not care where a data file lives; the `add` records the path.
  - Log: at a few commits/s the `_delta_log/` prefix is three orders of magnitude below the limit. Readers GET small objects; snapshot caching removes most of even that.
  - VACUUM: it is the one LIST-heavy operation. Run it daily off-peak, parallelise the LIST across prefixes, and use the checkpoint (not LIST) to know what is live.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

---

## Data

## Edge case: schema change while a streaming reader is running
- **Trigger:** `ALTER TABLE ADD COLUMN` or a write with `mergeSchema`.
- **Symptom:** the streaming query stops with a schema-change error at that version.
- **Answer:**
  - By design: a stream's output schema is fixed at start, so it fails rather than silently emitting rows with a different shape. Restart the stream; it resumes from its checkpoint with the new schema.
  - Batch readers pick up the new `metaData` on their next snapshot; old files lack the column and are read as `null`.
  - In-flight writers with the old schema fail conflict detection (`MetadataChangedException`) and retry with the new one.
  - Rename or drop needs column mapping so the physical Parquet names stay fixed; otherwise it is a full rewrite.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: GDPR erase of one user from a 1 PB table
- **Trigger:** `DELETE FROM t WHERE user_id = 42`.
- **Symptom:** the rows must be invisible now and physically gone within the legal window.
- **Answer:**
  - Prune by stats (and a Bloom filter on `user_id` if present) to the few files that can contain the user; write deletion vectors; commit. Seconds to minutes, no large rewrite. Invisible to every new snapshot immediately.
  - Physical: `OPTIMIZE` or `REORG TABLE ... APPLY (PURGE)` rewrites those files without the masked rows, then `VACUUM` after the retention deletes the old files. About 8 days at defaults; set the table's `deletedFileRetentionDuration` to 1 day if the requirement is 48 h, and accept 1 day of time travel there.
  - Time travel to before the delete is gone with the files. Old checkpoints hold stats, so exclude PII columns from `dataSkippingStatsColumns`.
  - Stricter still: per-user encryption keys and crypto-shred, as in the object store design.
- **Diagram:** `solution.md` §4.4, §5.5.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: backfill of 3 years of history into a live table
- **Trigger:** reprocess 1 PB of raw data and replace 1,000 daily partitions.
- **Symptom:** a single commit with 1 M `add` and 1 M `remove` actions, a 2 GB JSON file, and a 9-day job whose early output is at risk of orphan cleanup.
- **Answer:**
  - Commit per day-partition (1,000 commits), each `INSERT OVERWRITE PARTITION`. Each is atomic, each is retryable, each is a normal-sized log entry. Readers see days flip one at a time, which is usually acceptable; if not, write to a new table and swap the catalog name.
  - Raise `deletedFileRetentionDuration` on the target for the run so a 9-day job's uncommitted files are not vacuumed (or run no VACUUM during the backfill).
  - `replaceWhere` predicates make the overwrite's read set one partition, so concurrent appends to other days do not conflict.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: deletion vectors accumulate until reads are slow
- **Trigger:** a CDC table with 20% of rows updated per day, no OPTIMIZE for a month.
- **Symptom:** files where most rows are masked; every read fetches a DV per file and scans rows it throws away; `numRecords` stats misleading without the DV cardinality.
- **Answer:**
  - Schedule OPTIMIZE (or `REORG PURGE`) with a threshold: fold DVs when masked rows exceed 10% of a file.
  - The fold is a `dataChange=false` commit, so streams ignore it and appends do not conflict.
  - Dashboard the DV cardinality as a percentage of rows per table; alert when it passes 20%.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: size growth over 3 years
- **Trigger:** 8.6 TB/day for 3 years = ~9.4 PB.
- **Symptom:** 9.4 M files at 1 GB, checkpoint ~7 GB even with perfect compaction, 95 M commits in the log history if retention were unbounded.
- **Answer:**
  - Retention keeps the log at 30 days (2.6 M JSON objects); history older than that is only what the oldest checkpoint says.
  - V2 sidecars partitioned by time mean a query on last month reads ~1% of the checkpoint. Cold partitions' sidecars are never rewritten.
  - Archive old partitions into a separate table (same log design, different retention) and union with a view, so the hot table stays under 1 M files. Tiered storage classes for the cold files without touching the log (path stays the same).
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

---

## Operations

## Edge case: what pages at 3am
- **Trigger:** on-call rotation for the lakehouse platform.
- **Symptom:** the pager.
- **Answer:**
  - Commit failure rate > 20% for 10 min on a top table: a metadata-change loop, a stuck writer, or an arbiter outage.
  - Checkpoint age > 100 commits: replay cost climbing, checkpoint writer broken.
  - VACUUM deleted > 3x the 7-day average: retention misconfiguration in progress, stop it now.
  - Any write to `_delta_log/` from a principal outside the writer role.
  - Not paged, ticketed: average file size under 32 MB for a day (compaction stopped), DV cardinality > 20%.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: migrating a Hive Parquet table with zero downtime
- **Trigger:** 500 TB Hive-partitioned Parquet directory with readers and one writer.
- **Symptom:** none allowed.
- **Answer:**
  - `CONVERT TO DELTA`: one LIST, one commit (version 0 with an `add` per existing file), no data copy. Minutes.
  - Readers first: point the catalog name at the Delta table. Rollback: point it back, the files are untouched.
  - Writer second: stop the Hive writer, start the Delta writer. Never run both: a Hive writer bypasses the log and its files are invisible (or, worse, orphaned by VACUUM).
  - Features last: DVs, V2 checkpoints, column mapping, each a protocol bump that old readers refuse loudly.
- **Diagram:** `diagrams.md` D12.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: rolling back a bad write
- **Trigger:** a MERGE with a wrong predicate updated 30% of the table at version 205.
- **Symptom:** downstream dashboards wrong.
- **Answer:**
  - `RESTORE TABLE t TO VERSION AS OF 204`: a new commit 206 whose `add`/`remove` set makes the live set equal to 204's. No data copy, seconds. History keeps 205, so the audit trail survives.
  - Works only if 204's files are still within retention. Restore is the reason not to run `VACUUM RETAIN 0`.
  - Downstream streams that consumed 205 must be restarted from 204 or handle the reversal via Change Data Feed.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: enabling a new table feature that old readers do not support
- **Trigger:** turn on deletion vectors; a legacy Trino reader still queries the table.
- **Symptom:** the legacy reader fails with "unsupported reader feature".
- **Answer:**
  - That is the intended behaviour: the `protocol` action's `minReaderVersion` and reader features make an old client refuse rather than silently ignore DVs and return deleted rows.
  - Rollout: upgrade readers first, then enable the feature. Rollback: `DROP FEATURE` after folding DVs, or `RESTORE` to before the protocol bump.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

---

## Security and abuse

## Edge case: a writer commits an `add` pointing at a file it should not read
- **Trigger:** a principal with write access to table A points an `add` at a path in table B's bucket, or at a nonexistent path.
- **Symptom:** readers of A with cross-bucket access would read B's data; or queries fail with `FileNotFound`.
- **Answer:**
  - The filesystem-managed log trusts writers. IAM must scope readers to their own table prefixes so a foreign path is unreadable anyway.
  - The catalog-managed variant validates each proposed commit (paths under the table root, schema matches, protocol allowed) before ratifying it. This is one of the reasons to have a catalog arbiter for multi-tenant deployments.
  - Nonexistent paths surface as read errors, not wrong data; `FSCK REPAIR TABLE` removes `add`s whose files are gone.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: statistics leak sensitive values
- **Trigger:** a `salary` or `email` column in the first 32 columns; a principal can read `_delta_log/` but has row filters on the table.
- **Symptom:** `minValues`/`maxValues` in the log and checkpoint reveal real values.
- **Answer:**
  - Anyone who can read the log can read the stats; treat log readers as data readers.
  - Set `dataSkippingStatsColumns` to the filter columns only; exclude PII. Move sensitive columns past position 32 if using the default.
  - Time travel is also a leak: deleted rows are readable for the retention window.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: a runaway client spams commits
- **Trigger:** a bug commits an empty transaction in a loop.
- **Symptom:** the version number climbs by hundreds per minute, checkpoints every few seconds, every other writer's 412 rate jumps.
- **Answer:**
  - The table stays correct: empty commits change nothing, and other writers' conflict checks pass (no adds, no removes).
  - Cost is the problem: checkpoint writes and log objects. Quota commits per principal in the catalog or the arbiter service; the plain object-store arbiter has no such knob, so revoke the principal's PUT on `_delta_log/`.
  - The log retention cleanup deletes the junk versions after 30 days.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident
