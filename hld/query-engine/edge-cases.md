# Edge cases: multi-tenant distributed SQL query engine

Every entry answerable in under 60 seconds out loud. Categories: failure, consistency, scale, data, operations, security. Design reference: [`solution.md`](solution.md). Example cluster everywhere: Acme's X-Large, 32 workers of i3.2xlarge, 256 cores.

---

## Failure

## Edge case: a worker VM dies while the reduce stage is fetching
- **Trigger:** hardware fault, kernel panic, spot reclaim without notice.
- **Symptom:** reducers get connection refused, the stage stalls for a few seconds. The user sees nothing but ~10 to 30 s of extra latency.
- **Answer:**
  - The worker's running tasks are lost and so are its finished map outputs, because they were on its local disk.
  - Reducers report `FetchFailed`. The driver unregisters that worker's map outputs and reruns only those map tasks (about 1/32 of stage 1, ~500 tasks of ~1 s) from lineage, then retries the reduce stage for unfinished partitions.
  - If the parent stage's outputs were also on that node, the rerun cascades one level up. Push-merge copies or a remote shuffle stop the cascade for large statements.
  - Bounded by 4 consecutive stage attempts, so a node that keeps dying cannot loop forever.
- **Diagram:** `solution.md` §6 Flow 4.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: the driver dies with 10 statements running
- **Trigger:** driver OOM from a huge broadcast or collect, JVM crash, VM loss.
- **Symptom:** all 10 statements stop. Plans, stage state and map output locations were only in its memory.
- **Answer:**
  - WLM misses the heartbeat (~10 to 20 s), marks the cluster failed and bumps its epoch, so a half-alive driver cannot publish results.
  - Statements that are read-only, have delivered zero rows and are on attempt 1 go back to the queue and run on another cluster. The client sees latency, not an error.
  - Statements that already streamed rows, and all writes, fail with a retryable error. A write's outcome is decided by the table commit (#15), so the client checks the table version or its idempotency key before resubmitting.
  - Large results are staged in the result store before exposure, which is why "zero rows delivered" is the common case.
- **Diagram:** `solution.md` §6 Flow 5.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: the same task fails 4 times
- **Trigger:** a corrupt Parquet file, a UDF that throws on one row, a genuine engine bug on one input.
- **Symptom:** the statement fails with the task's error.
- **Answer:**
  - Retries exist for transient faults. A deterministic failure fails 4 times in a row, so the statement fails fast with the file path and the error, rather than burning the cluster.
  - Exclusion prevents the opposite case: a bad node failing different tasks does not use up a task's attempts, because the retry goes to another node.
  - Corrupt-file skipping stays off by default. Silently dropping rows is worse than failing.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: an availability zone goes down
- **Trigger:** zone power or network event.
- **Symptom:** every cluster in that zone disappears at once.
- **Answer:**
  - Clusters are zonal (shuffle never crosses zones), warehouses are not. WLM marks the zone's clusters failed in ~15 s and asks for replacements in other zones.
  - Queued and retry-safe statements run elsewhere within 20 to 60 s, bounded by warm capacity in the surviving zones.
  - No data is at risk: tables, results and usage are in regional storage. Long statements that had delivered rows fail with a retryable error.
- **Diagram:** `solution.md` §10.4.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: the catalog is down
- **Trigger:** catalog deployment gone wrong, its database failing over.
- **Symptom:** no new statement can resolve a table or check a grant. This is the widest blast radius in the design: every tenant.
- **Answer:**
  - Statements already running are unaffected. They pinned versions and credentials at analysis.
  - Drivers cache resolved metadata and grants for a short TTL (for example 5 minutes) as a documented degradation. Revocations are pushed, so a cached grant can outlive a revoke only while the push path is also down.
  - Credentials are vended for an hour, so running work keeps reading.
  - Past the TTL, fail new statements with a clear "catalog unavailable" error. Never fall back to skipping authorization.
- **Diagram:** `diagrams.md` D11.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: a WLM shard crashes with 800 statements queued
- **Trigger:** process crash or host loss for the shard owning a set of warehouses.
- **Symptom:** new statements for those warehouses stop being admitted. Running statements continue on their clusters.
- **Answer:**
  - Every queue transition is persisted, so the standby rebuilds the queue in seconds and resumes admission in the same order.
  - Drivers keep running what they have. On reconnect they report state and the new primary reconciles.
  - Cluster epochs prevent the old primary from routing after it comes back.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: spot VMs are reclaimed mid-query
- **Trigger:** using spot for workers to cut cost. AWS gives a 2-minute notice.
- **Symptom:** a batch of workers leaves together.
- **Answer:**
  - On notice, the worker is decommissioned: no new tasks, running tasks finish if they can, and shuffle blocks migrate to peers (`spark.storage.decommission.enabled`, off by default, on for us).
  - What does not migrate in time is recomputed from lineage, as for a crash.
  - Drivers never run on spot. A lost driver costs 10 statements, a lost worker costs seconds.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: the object store throttles a hot table
- **Trigger:** 100 concurrent medium statements on one table under one prefix want ~50k GET/s against a 5,500 GET/s per prefix limit.
- **Symptom:** `503 SlowDown`, tasks run slow, latency climbs for every query on that table.
- **Answer:**
  - Back off with jitter. Speculation must not fire for throttled tasks, because a copy doubles the requests.
  - Raise disk cache hits: file-to-node hashing makes repeated reads local.
  - Fix forward: randomized file prefixes for the table so the store can split its partitions.
- **Diagram:** `diagrams.md` D5 (throttling).
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

---

## Consistency

## Edge case: a commit lands on a table while a long query reads it
- **Trigger:** a `MERGE` commits version 813 while a 30-minute report reads version 812.
- **Symptom:** none. The report finishes on 812.
- **Answer:**
  - The statement pinned 812 at analysis and reads only 812's file list. Files are immutable, so nothing it reads changes.
  - The only risk is cleanup: if `VACUUM` deleted 812's removed files before the report ended, it would fail with file-not-found. The table format's retention (7 days by default) makes that impossible for any statement shorter than the retention (#15).
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: a user writes on one cluster, then reads on another and sees old data
- **Trigger:** multi-cluster warehouse. The `INSERT` ran on cluster 1, the `SELECT` lands on cluster 2 whose driver has a cached snapshot of the table.
- **Symptom:** the user's own row is missing.
- **Answer:**
  - The session carries the version its last write committed, per table. Analysis on any cluster must use a snapshot at or after that version, so a stale cached snapshot is refreshed with one LIST of the log tail.
  - Without the token, analysis always checks the log tail anyway (one request), so staleness is bounded to the moment of analysis. The token makes it exact.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: the result cache serves something the user should no longer see
- **Trigger:** a grant is revoked or a row filter changes after a result was cached.
- **Symptom:** a revoked user gets cached rows.
- **Answer:**
  - The cache key has three parts: normalized SQL, every table version, and the security context (user, applied row filters and masks, and a version of the policy). A policy change changes the key.
  - Before serving a hit, the driver still checks the grant with the catalog. The cache saves compute, never authorization.
  - Non-deterministic statements (`now()`, `rand()`) are never cached.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: two attempts of the same task both finish
- **Trigger:** speculation, or a slow task that was retried and then completed.
- **Symptom:** two copies of one map output or result chunk.
- **Answer:**
  - The driver registers one map output per `(stage, partition)`, the first successful attempt. The other is ignored and deleted.
  - Result chunks are written under `(statement_id, attempt, chunk_index)` and the manifest lists only the winners, so the client never sees both.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: the client retries a submit after a network timeout
- **Trigger:** the `POST` reached the gateway but the response was lost.
- **Symptom:** risk of running the same statement twice (double cost, or a double write).
- **Answer:**
  - The client sends a `request_id`. The gateway returns the existing `statement_id` for a repeated `(tenant, request_id)` within 24 h.
  - For writes, this is the first guard. The table format's transaction id is the second (#15).
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: a driver declared dead is actually alive
- **Trigger:** a network partition between the driver and WLM, a 30-second GC pause.
- **Symptom:** the statement was re-queued and runs on cluster 2, while the old driver may still finish and try to publish.
- **Answer:**
  - WLM bumped the cluster epoch when it declared the driver dead. Publishing a result (the manifest write and the `SUCCEEDED` transition) is a conditional write that carries the epoch, and the control plane rejects the old one.
  - The old driver's chunks are orphans under its attempt number and expire with the result store's 24 h lifecycle.
  - Same idea as fencing tokens in [`../../concepts/leases-fencing-clocks.md`](../../concepts/leases-fencing-clocks.md).
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

---

## Scale

## Edge case: one join key holds 30% of the rows
- **Trigger:** a whale customer, or `NULL` join keys.
- **Symptom:** one reduce task runs ~15 minutes on ~130 GB while 1,999 others finish in seconds.
- **Answer:**
  - After the map stage the driver sees partition sizes. A partition over 5x the median and over 256 MB is skewed.
  - Adaptive execution splits it into ~64 MB pieces, one task each, and replicates the matching partition from the other join side to each piece. The stage finishes in seconds.
  - Speculation does not help: a copy of a skewed task is just as slow. Filter or handle `NULL` keys separately when they are the cause.
- **Diagram:** `solution.md` §6 Flow 2.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: 6,000 dashboard statements in one minute at 09:00
- **Trigger:** 200 users open a 30-tile dashboard at the start of the day.
- **Symptom:** queue wait climbs, dashboards feel slow.
- **Answer:**
  - Most of the load is identical statements: the result cache answers repeats in tens of ms. At 80% hits, one cluster carries it.
  - The rest queue, and WLM adds clusters as estimated drain time rises (100/s at 0.5 s each is 50 concurrent, 5 clusters at 10 each).
  - The forecaster sees the 09:00 pattern and fills the warm pool beforehand, so new clusters arrive in seconds.
- **Diagram:** `solution.md` §6 Flow 3.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: a table with 1 million tiny files
- **Trigger:** a streaming writer that never compacts.
- **Symptom:** planning is slow, a million tasks, two footer GETs per file, the driver runs out of memory tracking tasks.
- **Answer:**
  - The planner packs many small files into one ~128 MB split (with a per-file open cost), so tasks stay near 128 MB of work.
  - Footer and metadata latency still dominate. The real fix is compaction in the table format (#15 §5.4). Surface "files scanned per GB" in the query profile so the tenant sees it.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: the optimizer planned a broadcast but the side is 5 GB
- **Trigger:** missing or stale table statistics.
- **Symptom:** a static broadcast would collect 5 GB on the driver and send it to every worker: driver OOM or a broadcast timeout (300 s by default).
- **Answer:**
  - Adaptive execution decides the join at the stage boundary from real sizes, not estimates, and turns a planned broadcast back into a shuffle join when the side is over the threshold.
  - Cap broadcast size hard regardless of hints, so one bad plan cannot take down the driver and its 10 statements.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: a BI tool asks for a 50 GB result
- **Trigger:** `SELECT *` without `LIMIT`.
- **Symptom:** the driver would stream 50 GB through itself.
- **Answer:**
  - Inline results are capped at 25 MiB. Anything larger is written as chunks to the result store and fetched by the client with presigned URLs, so the driver is out of the byte path.
  - Warehouses can set a row or byte limit on results for interactive clients.
- **Diagram:** `diagrams.md` D4 (external links).
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: 10x traffic tomorrow
- **Trigger:** a large customer onboards, or a quarter-end.
- **Symptom:** warm pools drain, cold starts, queues.
- **Answer:**
  - Per-tenant caps on pool draw keep one tenant's burst from starving others. Past the cap, the tenant gets cold VMs, slower but isolated.
  - Raise pool targets for that tenant's regions and zones ahead of time. The forecaster learns the new level within days.
  - The shared control plane is stateless or sharded, so it scales out. The catalog is the component to load test first.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

---

## Data

## Edge case: `ALTER TABLE ADD COLUMN` while statements run
- **Trigger:** a schema change commits mid-query.
- **Symptom:** none for running statements.
- **Answer:**
  - The schema is part of the pinned snapshot. Running statements keep the old schema. The next statement sees the new column, with nulls for old files.
  - The result cache is keyed by version, so no cached result mixes schemas.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: a table has no statistics
- **Trigger:** a new table, a table written by an external engine.
- **Symptom:** the cost-based optimizer guesses join order and sides badly.
- **Answer:**
  - File-level min/max stats come with the table format for free, so pruning still works.
  - Adaptive execution fixes join type and partition counts at stage boundaries from real sizes.
  - Join order is the part AQE cannot fully repair. Collect column statistics on write or with a scheduled analyze on large tables.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: a tenant leaves and asks for deletion of everything
- **Trigger:** contract end, GDPR request.
- **Symptom:** tenant data exists in more places than the tables.
- **Answer:**
  - Tables are the tenant's own storage. Our copies: disk caches (gone, VMs terminated at stop), result store (24 h lifecycle), remote result cache (24 h), query history and usage system tables (delete by `tenant_id` partition), logs (retention policy).
  - Keep billing records as required by law, without query text.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: query history after 3 years
- **Trigger:** growth.
- **Symptom:** ~40 GB/day is ~44 TB over 3 years for one region.
- **Answer:**
  - It is a Delta table partitioned by date and clustered by tenant, so tenant queries prune well at any size.
  - Keep full rows for a year, daily aggregates forever. Profiles only for statements over 1 s.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

---

## Operations

## Edge case: a new engine release returns wrong results for one operator
- **Trigger:** a vectorized kernel bug, a cast that differs between Java and C++.
- **Symptom:** silently wrong numbers, the worst failure a query engine can have.
- **Answer:**
  - Prevention: shadow-run a sample of deterministic statements on old and new images and diff results before widening the rollout.
  - Containment: a per-operator kill switch that sends that operator back to the old engine through a transition, without a full rollback.
  - Recovery: stop assigning the image, recycle clusters that run it (at most 24 h, faster on demand). Tell tenants which statements ran on it, from query history.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: what pages at 3am
- **Trigger:** any of the page-level alerts.
- **Symptom:** see below.
- **Answer:**
  - Warm pool below 20% of forecast in a zone: cold starts are coming.
  - Queue wait p95 over 30 s on more than 1% of warehouses.
  - Infrastructure failure rate over 0.5% for 10 minutes.
  - Catalog error rate over 1%.
  - Everything else (FetchFailed spikes, attribution drift, cache hit drops) is a ticket, not a page.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: a runaway query burns $10,000 overnight
- **Trigger:** a cross join, a missing filter, a scheduled job looping.
- **Symptom:** a surprise bill.
- **Answer:**
  - Before running: maximum scan bytes checked at plan time from pruned statistics.
  - While running: statement timeout (system default is 2 days, so set 1 h on BI warehouses), and a per-tenant budget that alerts and can stop the warehouse.
  - After: cost per statement in system tables, so the tenant finds the culprit in one query.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

---

## Security

## Edge case: a user's Python UDF tries to read other users' data
- **Trigger:** a shared cluster used by many users of one tenant, with row filters on a table.
- **Symptom:** risk of bypassing row filters from inside the engine process.
- **Answer:**
  - User code runs in a separate sandboxed process, with no network and no access to the engine's credentials or memory. It receives only the rows the plan passes it, after filters and masks.
  - Credentials are vended per statement and scoped to the table's path, so even a compromised process cannot read other tables.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: data leaks across tenants through a reused VM or disk
- **Trigger:** a VM returned to the pool after serving tenant A, assigned to tenant B.
- **Symptom:** B could read A's cached files or shuffle data.
- **Answer:**
  - Never happens by design: a VM serves one tenant for life and is terminated at release. The pool is refilled with new VMs.
  - Local disks are encrypted with a per-cluster key that is discarded at termination.
  - This rule is part of why the warm pool is expensive. It is not negotiable.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: a presigned result link leaks
- **Trigger:** a link pasted into a chat or a log.
- **Symptom:** anyone with the link can download that chunk.
- **Answer:**
  - Links are bearer tokens with short expiry, per chunk. There is no revoke, so the TTL is the control ([`../../concepts/signed-url.md`](../../concepts/signed-url.md)).
  - Results expire after 24 h regardless. Sensitive warehouses can force `INLINE` only.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: a tenant floods the control plane
- **Trigger:** a misconfigured BI tool polling every 10 ms, or a script submitting 10k statements/s.
- **Symptom:** gateway and WLM load for everyone.
- **Answer:**
  - Token-bucket rate limits per tenant and per token at the gateway, with 429 and a retry-after ([`../../concepts/rate-limiting-and-load-shedding.md`](../../concepts/rate-limiting-and-load-shedding.md)).
  - Long-poll (`wait_timeout` up to 50 s) makes polling cheap. WLM is sharded by warehouse, so one tenant's queue lives on one shard.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident
