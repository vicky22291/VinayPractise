# Edge cases: Petabyte batch + streaming ingestion

Every entry answerable in under 60 seconds out loud. Categories: failure, consistency, scale, data, operations, security. Design reference: [`solution.md`](solution.md).

---

## Failure

## Edge case: driver dies after the table commit, before writing `commits/N`
- **Trigger:** OOM, spot reclaim, deploy, network partition between driver and the checkpoint bucket.
- **Symptom:** nothing visible. The table has batch N. The checkpoint says N is not done.
- **Answer:**
  - On restart the driver sees `offsets/N` without `commits/N` and re-executes N with the same plan.
  - Tasks write new Parquet files. Before committing, the driver reads the table snapshot and finds `txn(appId = p, version = N)` already present, so it skips the commit.
  - The new files are orphans; `VACUUM` deletes them after the retention window. Zero duplicate rows, because the marker and the data were one atomic log entry.
  - Cost: one wasted batch of compute.
- **Diagram:** `solution.md` §6 Flow 5.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: driver dies after writing `offsets/N`, before any file is written
- **Trigger:** same as above, earlier in the batch.
- **Symptom:** nothing visible.
- **Answer:**
  - Restart finds `offsets/N`, re-executes with the same range. No marker in the table, so it commits normally.
  - This is why the plan is written first: the range is fixed before any side effect, so every execution of batch N reads the same records.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: the table commit times out with no response
- **Trigger:** S3 503, table service timeout, GC pause longer than the client timeout.
- **Symptom:** the driver does not know whether version V+1 exists.
- **Answer:**
  - Read the log tail. If `V+1.json` exists and its `txn` is ours, we won: proceed to `commits/N`. If it exists and is not ours, someone else committed (compaction): re-check the snapshot for our marker, then retry the commit at V+2.
  - If it does not exist, retry the put-if-absent. The conditional write means a retry can never overwrite someone else's commit.
  - The whole check is a snapshot read, no coordination service.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: S3 or the table log is down for 60 minutes
- **Trigger:** regional S3 incident, table service deploy gone wrong.
- **Symptom:** every pipeline's batch fails at the commit step. Freshness dashboards red across the board. Producers unaffected.
- **Answer:**
  - Batches retry with backoff. Nothing partial is committed, so retries are safe.
  - Kafka absorbs 60 min: 36 GB on a 10 MB/s topic, 42 TB platform-wide. Retention 7 days, so no loss.
  - On recovery each pipeline catches up at `maxOffsetsPerTrigger` (2x normal): lag decays at 1x, zero after another 60 min. Raise the cap and scale the pool to recover faster.
  - Alert once per cause, not once per pipeline. The page is "lag approaching retention", which does not fire here.
- **Diagram:** `solution.md` §5.2.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: a pipeline is dead for 8 days
- **Trigger:** a broken image in a restart loop that nobody fixed; an owner's team disbanded.
- **Symptom:** page at day 3.5 (half retention). At day 7 Kafka deletes the segments the checkpoint points at.
- **Answer:**
  - On restart the fetch returns `OffsetOutOfRange`. The job must not `auto.offset.reset` silently: it alerts "start offset older than earliest available" and stops.
  - A human acknowledges the loss, resets to earliest, and records the gap `[lost_from, lost_to)` in the table's metadata so downstream knows.
  - Prevention is the page at half retention and tiered storage making 7 days cheap enough to extend to 30 for tier A.
- **Diagram:** `diagrams.md` D5 (falls behind retention).
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: a Kafka broker dies mid-batch
- **Trigger:** disk failure, instance termination.
- **Symptom:** tasks fetching from that broker's leader partitions get `NotLeaderForPartition`, retry against the new leader after ~10 s.
- **Answer:**
  - Leadership moves to an ISR follower with an epoch bump. The offset range in `offsets/N` is unchanged, so the task refetches the same records.
  - Producers buffer client-side during the election, `acks=all` means nothing acknowledged was lost.
  - Under-replicated partitions alert until the broker is replaced or its partitions reassigned.
- **Diagram:** `solution.md` §10.4.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: the schema registry is down
- **Trigger:** registry deploy, its Kafka topic unavailable.
- **Symptom:** records with a schema id no task has cached fail to decode.
- **Answer:**
  - Cached ids keep decoding forever (ids are immutable), so a running pipeline with a stable schema notices nothing.
  - Records with a new id are quarantined with `error = schema_unavailable`, the batch commits, and when the registry is back a replay of the quarantine range lands them. No lag for the rest of the topic.
  - Producers cannot register new schemas while it is down, which blocks their deploy, not our pipeline.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: the control plane is down
- **Trigger:** all three replicas lose their database.
- **Symptom:** no new pipelines, no replays, no restarts of crashed jobs, no autoscaling.
- **Answer:**
  - Running jobs keep running: the control plane is never on the data path. Leases held by jobs are renewed against the control plane, so a lease expiring while it is down must not stop the job; the job keeps its lease epoch and continues, and the `txn` marker makes a double-run harmless anyway.
  - The blast radius is a crashed job that stays down until the control plane returns. That is the reason to keep it simple (a metadata service) and replicated.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

---

## Consistency

## Edge case: the same record lands twice because the producer sent it twice
- **Trigger:** application retry after a client timeout with a non-idempotent app layer, or a genuine duplicate business event.
- **Symptom:** two rows with different `_offset`, same payload.
- **Answer:**
  - This is not an ingestion duplicate. Ingestion promises each Kafka record lands once. The app produced two records.
  - Producer-side: `enable.idempotence` covers broker-level retries only. The app needs its own `event_id` if it retries `send` at its layer.
  - Downstream dedups by `event_id` within a window (a stateful transform, its own state and TTL). Say the boundary out loud: exactly-once effect per record, not per business event.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: a multi-row source transaction straddles two CDC batches
- **Trigger:** a 1,000-row transaction commits as the batch boundary falls in the middle of its changes in the topic.
- **Symptom:** for up to one trigger interval, the mirror shows half the transaction.
- **Answer:**
  - Batches are bounded by offset, not by `tx_id`. Per-key consistency is strong (lsn guard), cross-key is eventual within one batch.
  - If the consumer needs transactional consistency, align batch ends to transaction boundaries (Debezium emits transaction metadata events) at the cost of latency, or expose the mirror through a view that filters to `_commit_ts <= last complete tx`.
  - State which one is promised. Most consumers of a mirror accept per-row.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: the CDC snapshot and the stream overlap on a key
- **Trigger:** a row in chunk k changes while chunk k is being read.
- **Symptom:** the snapshot row and a change event for the same key both arrive.
- **Answer:**
  - Incremental snapshot: low watermark, read chunk, high watermark. A change for a key in the chunk that arrives between the marks wins, and the snapshot row for that key is discarded.
  - On the apply side the `lsn` guard on MERGE makes any residual overlap idempotent: the higher lsn wins.
  - Both mechanisms are needed: the first is correctness at the connector, the second is safety at the sink.
- **Diagram:** `solution.md` §6 Flow 3.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: two instances of the same pipeline run at once
- **Trigger:** a lease expires during a GC pause and the scheduler starts a second instance.
- **Symptom:** two drivers plan batches from the same checkpoint dir.
- **Answer:**
  - Both write `offsets/N`. Both execute. The first to commit wins; the second finds `txn(p, N)` and skips. The table is correct.
  - The checkpoint dir can be corrupted by two writers racing on `commits/N` (same content, so benign) or on `offsets/N+1` (different plans, not benign). The lease epoch is carried into the checkpoint and the log store rejects a stale epoch's writes. This is the fencing token from [`../../concepts/leases-fencing-clocks.md`](../../concepts/leases-fencing-clocks.md).
  - Wasted compute, never wrong data.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: a multiplexed job commits table A then dies before table B
- **Trigger:** one job writes 100 tables per batch.
- **Symptom:** A is at batch 42, B at 41, for the length of a restart.
- **Answer:**
  - No cross-table atomicity is promised. On restart batch 42 re-runs; A's commit is skipped by its marker, B's proceeds.
  - Each table has its own `txn(appId = p, version)` where `p` is the pipeline, not the job, so tables are independent.
  - A consumer that needs A and B consistent must join on `_ingest_ts` or use a downstream job. Say it out loud.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: readers see a batch before its compaction and after
- **Trigger:** hourly `OPTIMIZE` rewrites files a query was planning against.
- **Symptom:** none, if the table format is doing its job.
- **Answer:**
  - The query pinned a snapshot version. The old files stay until the retention window (7 days) even though a newer version removed them.
  - Compaction commits with `dataChange = false`, so a streaming reader of the bronze table does not see the rewritten files as new data.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

---

## Scale

## Edge case: one Kafka partition is 10x hotter than the rest
- **Trigger:** keyed topic with a hot key, a broken custom partitioner, a producer with one huge instance.
- **Symptom:** batch time = slowest task time. Freshness p99 of the whole pipeline is set by one partition.
- **Answer:**
  - Keyless topics: sticky partitioner balances by construction; check the producer config first.
  - Keyed topics: the fix is upstream (split the key space, more partitions) because ordering per key must hold.
  - Inside the job: `minPartitions` splits one partition's offset range across several tasks. Order is preserved by the `_offset` column, not by task order.
  - Watch `max task time / median task time` per batch as the skew metric.
- **Diagram:** `diagrams.md` D10.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: 10x traffic tomorrow
- **Trigger:** product launch, a new SDK that logs 10x more.
- **Symptom:** partitions at 50 MB/s, brokers saturated, batches at 10x size.
- **Answer:**
  - Kafka: add partitions (10k to 100k), add brokers, second cluster with topic routing when partition-per-broker limits are hit. Producer quotas stop a single misbehaving producer.
  - Jobs: `maxOffsetsPerTrigger` bounds the batch; lag grows until the control plane scales the pool from `lag_seconds`. Multiplexed groups may need to be split.
  - Tables: unchanged protocol; the 200 big tables move to hourly partitions.
  - The order of failure: broker disk (24 h local window) first, then cores, never the commit protocol.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: a table has 20 M files
- **Trigger:** 200 files per batch, 30 s trigger, compaction never scheduled.
- **Symptom:** query planning takes minutes, the table checkpoint is tens of GB, S3 request bill is thousands of dollars a day.
- **Answer:**
  - Root cause is files per commit, not commits. Enable optimized writes (shuffle to 128 MB targets) so a batch writes 1 to 2 files.
  - Run `OPTIMIZE` over the history in partition-sized chunks (it is `dataChange = false`, so the stream is unaffected), then hourly going forward.
  - Alert on files per table growing faster than expected so it never reaches 20 M again.
- **Diagram:** `solution.md` §5.1.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: a 100 GB file lands
- **Trigger:** a partner dumps a monthly export.
- **Symptom:** one task reads for 20 minutes, the batch and every other file in it waits.
- **Answer:**
  - Splittable formats (Parquet, CSV, uncompressed JSON lines): split by byte range across tasks, the file-state entry is the whole file, marked landed when all splits commit in the same batch.
  - Non-splittable (gzip): quarantine by reference above a size cap (say 10 GB) and page the owner, or route to a dedicated large-file pipeline with its own pool.
  - `maxBytesPerTrigger` keeps one huge file from being batched with 10k small ones.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: thundering herd of replays
- **Trigger:** a platform-wide decoder bug; 500 owners request replays at once.
- **Symptom:** the replay pool is oversubscribed, Kafka consumer bandwidth doubles.
- **Answer:**
  - Replays are pipelines with a quota and run in their own pool; the pool has a fixed size, so replays queue rather than starve live ingestion.
  - Prioritise by tier and by range size. A platform-wide bug gets one platform-run replay per affected range instead of 500 tickets.
  - Kafka reads of old data come from tiered storage, so broker page cache for live consumers is not evicted.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

---

## Data

## Edge case: a record arrives 3 days late
- **Trigger:** offline mobile client syncs, a partner re-sends a batch.
- **Symptom:** `_event_ts` is 3 days behind `_ingest_ts`.
- **Answer:**
  - Lands in today's `ingest_date` partition. History is never rewritten.
  - A query by event time finds it through file stats on `_event_ts` (clustering keeps most files tight, this file is one extra read).
  - The lateness histogram records it; downstream jobs with a watermark decide whether it goes into the silver partition or the late side table.
- **Diagram:** `solution.md` §5.3.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: a producer adds a field, then renames one, then changes a type
- **Trigger:** three consecutive deploys of a producer.
- **Symptom:** none, a stuck deploy, none.
- **Answer:**
  - Add optional field: `BACKWARD` compatible, registers, flows through as `add column` (policy `additive`) or into `_rescued_data` (policy `rescue`).
  - Rename: Avro treats it as remove plus add. Remove is backward compatible, so it registers; the table gains the new column and the old one goes null-only. The owner drops the old column later. Data is never lost.
  - Type change `int → string`: rejected at registration, the deploy fails, the pipeline never sees it. For JSON with no registry: the value is rescued, never coerced, and the owner gets a ticket.
- **Diagram:** `solution.md` §6 Flow 6, §5.4.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: the same S3 key is overwritten with different content
- **Trigger:** a partner re-uploads a corrected file to the same path.
- **Symptom:** a second `ObjectCreated` with a new etag.
- **Answer:**
  - File-state identity is `(key, etag)`, so the new content is a new file and lands. Both are in bronze with different `_source_etag`.
  - The pipeline's `on_overwrite` policy decides the rest: `append` (default), `replace` (downstream dedup by key and max `_ingest_ts`), `reject` (quarantine the second).
  - Bucket versioning on the landing bucket makes the first version recoverable.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: an S3 notification is lost
- **Trigger:** SQS message expired before the job drained it, notification config misapplied for an hour.
- **Symptom:** a file exists in the bucket that no batch ever read.
- **Answer:**
  - The backup listing (hourly for small prefixes, daily for huge ones) diffs the bucket against the file-state store and enqueues anything missing.
  - Freshness for those files is the listing interval, not minutes. Alert if the listing finds more than a handful, because that means notifications are broken.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: GDPR delete for one user across 6 PB of bronze
- **Trigger:** a deletion request.
- **Symptom:** the user's rows are in thousands of files across 90 days of partitions.
- **Answer:**
  - `DELETE FROM bronze WHERE user_id = X` becomes a rewrite of every touched file (copy-on-write) or a deletion vector per file (merge-on-read). Use file stats on `user_id` to touch only files that may contain it; without clustering on `user_id` that is most of them.
  - Batch deletes daily so 1,000 requests cost one pass, not 1,000.
  - Kafka copies expire with retention (7 days). SLA: gone from the lake within 7 days, from the buffer within 7 days of production. Quarantine and the changelog bronze are in scope too.
  - At > 100 requests/day, build a `user_id → files` index or cluster bronze on `user_id`.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: the file-state store grows past memory
- **Trigger:** a pipeline receiving 50 M files/day.
- **Symptom:** the RocksDB snapshot in the checkpoint is 100 GB, restart takes 20 minutes to restore it.
- **Answer:**
  - TTL entries at 30 days. Store only `(key hash, etag hash)` at ~50 B per entry.
  - Above ~20 GB, move file state out of the checkpoint into a KV table (a small Delta table keyed by pipeline and key, or a DynamoDB table) and commit the state change in the same batch by writing it after the table commit and treating it as idempotent.
  - Or ask the uploader to write fewer, larger files. Often the right answer.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

---

## Operations

## Edge case: what pages at 3am
- **Trigger:** on-call rotation.
- **Symptom:** a page.
- **Answer:**
  - `lag_seconds > 0.5 × retention` on any pipeline: loss is imminent. Everything else is a warning.
  - Kafka under-replicated partitions > 0 for 10 minutes: a second failure would block producers.
  - Quarantine rate > 5%: the pipeline auto-paused, a human decides rollback or accept.
  - Compaction not run for 6 hours on a tier A table: the file count is climbing.
  - Postgres replication slot WAL past 50% of its cap: the source database is about to fill its disk because of our connector.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: rolling out a new decoder version
- **Trigger:** a library upgrade in the job image.
- **Symptom:** none, if it works. Quarantine spike, if not.
- **Answer:**
  - Canary on 10 tier C pipelines for one hour, compare quarantine rate and batch duration with the previous week's same hour.
  - Then 10% of tier B, then all. Rollback is a redeploy of the previous image; checkpoint format is backward compatible by contract.
  - A canary that lands wrong (not quarantined) rows is fixed by replaying the canary window with the old image.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: migrating from consumers that write to S3 directly
- **Trigger:** the current state of most companies.
- **Answer:**
  - Dual-publish producers to Kafka while the old path runs. New pipelines land into shadow tables. Diff counts and checksums daily for a week.
  - Flip readers through a view, 10% then all. Stop the old writers, keep them deployable for 30 days.
  - Rollback at every step is a view change. CDC cuts over when the mirror stays within 60 s of the source for 24 hours.
- **Diagram:** `diagrams.md` D12.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: a replay must use the old decoder, not the fixed one
- **Trigger:** an audit asks for the data "as it was landed".
- **Answer:**
  - Every row carries `_schema_id` and the replay pipeline pins a decoder image version. The quarantine table keeps raw bytes, so both "as landed" and "as corrected" are reproducible.
  - Time travel on the bronze table gives "as landed" for free inside the retention window.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

---

## Security and abuse

## Edge case: a producer floods its topic at 100x
- **Trigger:** a logging bug, a load test pointed at production.
- **Symptom:** its partitions fill, its pipeline lags.
- **Answer:**
  - Broker quotas per client id (`producer_byte_rate`) throttle the producer before it affects other topics on the same brokers.
  - Its own pipeline lags and the owner is paged. Other pipelines are unaffected because pools and quotas are per pipeline.
  - Retention by bytes on that topic prevents one topic from eating the broker's disk.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: a malicious uploader
- **Trigger:** a compromised partner credential.
- **Symptom:** garbage files, oversized files, files with a schema designed to explode the table (10k new columns).
- **Answer:**
  - The pipeline role can read the landing bucket, not delete, and only its prefix. Garbage lands in quarantine. A size cap quarantines oversize by reference.
  - Schema policy `additive` has a column cap (say 500) above which new fields are rescued instead of added. A 10k-column attack becomes JSON in one column.
  - Quarantine rate > 5% auto-pauses the pipeline, so the blast radius is one table.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: PII lands in a bronze table that many teams can read
- **Trigger:** raw payloads contain emails and addresses.
- **Answer:**
  - Column tags from the registry (`pii = true`) propagate to the table's column metadata. Access control masks tagged columns for everyone but the owning team.
  - Bronze retention for PII-tagged tables is 30 days; silver tables downstream carry only derived or masked fields.
  - Quarantine tables hold raw bytes and are the most sensitive table in the platform: owner-only access, 30 day TTL, encrypted at rest with the tenant's key.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident
