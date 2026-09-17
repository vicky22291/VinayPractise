# Delta Lake: transactional tables over object storage

> One-line answer: keep the data as immutable Parquet files in the object store and make the table's state a write-ahead log of JSON commit files under `_delta_log/`, where one commit is one put-if-absent of `N.json`; readers rebuild a snapshot from the newest checkpoint plus the log tail and read only the files that snapshot lists, so they never see a half-written table; writers use optimistic concurrency (read at version `r`, write new files under unique names, try to claim `r+1`, on loss re-read `r+1..m` and check the read set against what those commits added or removed, then retry); a checkpoint every 10 commits bounds replay, retention bounds time travel, and updates, compaction, schema changes, and streaming checkpoints are all just more commits.

Tier 2, problem #15 in [`hld/README.md`](../README.md). Asked at Databricks and Snowflake as "design a transactional table on S3", "design Delta Lake / Iceberg", "design time travel", or "let batch and streaming jobs write the same table". It is Databricks' product in disguise, so interviewers probe the mechanism (log format, conflict check, checkpoint size, what the object store must provide) rather than the boxes. Reusable blocks: [`../immutable-object-store/`](../immutable-object-store/) (the store we build on), [`../kv-store-wal/`](../kv-store-wal/) (WAL plus snapshot is the same idea one level down), [`../../concepts/columnar-db.md`](../../concepts/columnar-db.md) (Parquet, stats, skipping), [`../../concepts/lsm-tree.md`](../../concepts/lsm-tree.md) (compaction is the same triangle). Sources in [`research/`](research/).

## Problem statement (as asked)

Cloud object stores (S3, ADLS, GCS) are cheap, durable, and scale to exabytes, but they are key-value stores: no multi-object transaction, no atomic rename on S3, expensive LIST, and a table is just a directory of Parquet files. Design a table layer on top so that many Spark (or any engine) jobs across many clusters can read and write the same table with ACID guarantees: a reader never sees a partially written table, two writers never corrupt it, row-level updates and deletes work, old versions can be queried (time travel), and the table stays fast when it has millions of files and years of history.

## Functional requirements

Core:
- **Atomic writes.** A job appends or overwrites many files as one unit. Readers see all of it or none of it, even if the writer crashes halfway.
- **Consistent reads and time travel.** A query reads one consistent snapshot for its whole duration while writes land. Any past version can be read by version number or timestamp, inside a retention window.
- **Concurrent writers.** Independent jobs on independent clusters commit to the same table. Writes are serializable. Blind appends never block each other.
- **Row-level changes.** `UPDATE`, `DELETE`, `MERGE` (upsert, CDC apply, GDPR erase) on a table stored in immutable files.
- **Evolve without downtime.** Schema changes, compaction of small files, retention cleanup, and streaming writers with exactly-once, all while readers and other writers keep running.

Below the line (say it out loud):
- The query engine itself (Spark, Photon, Trino). We define what it must read, not how it plans.
- Catalog, permissions, lineage (Unity Catalog, Glue). We assume a name-to-path mapping exists.
- Cross-table transactions. One table is the unit of atomicity. Say why.
- Secondary indexes beyond file statistics. Bloom filters and clustering are in scope, B-trees are not.
- Cross-region replication of the table. Mentioned in evolution only.

## Non-functional requirements

| Dimension | Target |
|---|---|
| Scale | Tables to 1 PB and 10 M files. Real tables reach hundreds of millions of objects. Thousands of tables per account. Readers unbounded |
| Commit rate | 1 commit/s per table sustained (streaming), bursts of 10 concurrent writers. Object store PUT latency is 50 to 200 ms, so the OCC ceiling is a few commits per second per table |
| Read latency | Snapshot construction under 1 s for a 1 M file table, under 10 s for 10 M files. Query planning reads only metadata, never LISTs data directories |
| Consistency | Writes serializable (WriteSerializable by default, Serializable on request). Reads snapshot isolation. Read-your-writes for the committing job |
| Durability | The log is the truth. Once `N.json` exists the commit is durable at object store durability (11 nines). No data loss on writer crash at any point |
| Availability | Reads never depend on a coordination service. Writers depend only on the object store's conditional put (or a catalog, if chosen, at 99.99%) |
| Retention | Time travel 30 days by default. Physically deleted files kept 7 days. GDPR erase complete within the deleted-file retention |

## What interviewers probe (the ladder)

1. Two writers commit at the same moment. Exactly which primitive decides who wins, and what does the loser do?
2. A writer crashes after uploading 500 Parquet files and before writing the commit. What does a reader see? What cleans up?
3. The table has 10 M files. Listing the directory takes minutes. How does a reader find the current files in under a second?
4. A streaming job commits every second and writes 100 small files each time. What breaks after a day, and how do you fix it without stopping the stream?
5. Delete one user's rows from a 1 PB table for GDPR. How much do you rewrite, and when is the data really gone?
6. Compaction rewrites 1,000 files into 10 while an `UPDATE` runs on the same partition. Who conflicts with whom, and why can appends never conflict with compaction?
7. Time travel to 30 days ago while `VACUUM` runs. What guarantees the old files are still there?
8. S3 had no put-if-absent until 2024. How did the design work on S3 before that, and what changed after?
9. Schema changes under a running streaming reader. What happens to the stream?
10. The commit rate ceiling is a few per second per table. Where does that number come from, and what do you build to raise it 10x?

## Files

| File | What it is |
|---|---|
| [`solution.md`](solution.md) | Full HLD in flow-first form: one incremental diagram, one walkthrough per FR, deep dives that mutate the design, then nitty-gritty |
| [`diagrams.md`](diagrams.md) | The D1 to D12 diagram set |
| [`edge-cases.md`](edge-cases.md) | Every "what if" with a 60-second answer and a confidence box |
| [`deep-dives/transaction-log-and-commit-protocol.md`](deep-dives/transaction-log-and-commit-protocol.md) | Log layout, actions, the put-if-absent primitive per cloud, staged and catalog-managed commits |
| [`deep-dives/optimistic-concurrency-and-conflict-detection.md`](deep-dives/optimistic-concurrency-and-conflict-detection.md) | The retry loop, the conflict matrix, isolation levels, the commit-rate ceiling and how a coordinator raises it |
| [`deep-dives/snapshots-checkpoints-and-time-travel.md`](deep-dives/snapshots-checkpoints-and-time-travel.md) | Log replay, checkpoint size math, V2 checkpoints with sidecars, retention and VACUUM safety |
| [`deep-dives/row-level-changes-cow-vs-mor.md`](deep-dives/row-level-changes-cow-vs-mor.md) | MERGE internals, copy-on-write vs deletion vectors, change data feed, GDPR erase |
| [`deep-dives/compaction-and-data-layout.md`](deep-dives/compaction-and-data-layout.md) | Small files, OPTIMIZE as a `dataChange=false` commit, Z-order vs clustering, stats-based skipping |
| [`deep-dives/streaming-and-idempotent-writes.md`](deep-dives/streaming-and-idempotent-writes.md) | The `txn` action, exactly-once sinks, reading the log as a stream, schema change mid-stream |
| [`research/`](research/) | Raw web research notes with source links. Input to the files above, not study material |
| `delta-lake-transactions.excalidraw` | My drawing. Missing until I draw it |
