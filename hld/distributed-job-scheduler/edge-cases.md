# Edge cases: distributed job scheduler with DAG dependencies

Every entry must be answerable out loud in under 60 seconds. Mark confidence after each study pass. Categories per `hld/CLAUDE.md` §5: failure, consistency, scale, data, operations, security.

Design recap for context: 256 trigger partitions, each leased to one trigger node via etcd (TTL 10 s) with an epoch; the owner keeps the partition's `next_fire_at` values in a timing wheel and creates a `run` row (unique on `job_id, scheduled_time, trigger_type`) in the same transaction that advances `next_fire_at`. 64 run shards, each owned by one orchestrator node; the owner appends `run_event` rows and updates `task_instance` rows in one local transaction, computes ready tasks by in-degree counting under the trigger rule. Matching service per pool hands attempts to long-polling workers with a 60 s lease renewed by 10 s heartbeats. Completion is fenced on `attempt_id`. Tasks are at-least-once with idempotency key `(run_id, task_id)`; at-most-once mode exists per task. Details in [`solution.md`](solution.md).

---

## 1. Failure

## Edge case: trigger node dies at 08:59:59
- **Trigger:** kernel panic or OOM on one of 12 trigger nodes that owns 21 partitions.
- **Symptom:** `partition_without_owner` metric rises after the etcd lease TTL. About 1/12 of the 09:00 runs are late.
- **Answer:**
  - etcd lease expires in 10 s. The assigner gives the 21 partitions to surviving nodes with `epoch + 1`.
  - Each new owner runs one query per partition: `SELECT job_id, next_fire_at FROM job WHERE partition = p AND next_fire_at < now() + 5 min`, about 4 k rows, under 1 s, and fires everything overdue immediately.
  - Worst case lateness is TTL + reassignment + reload, about 12 to 15 s. Inside the "never later than 30 s after failover" NFR. Nothing is lost because `next_fire_at` only advances in the transaction that inserted the run.
  - Say the trade-off: a shorter TTL means faster failover but more false failovers on a GC pause. 10 s with 3 s renewals is the usual middle.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: orchestrator node dies with 5,000 runs in flight
- **Trigger:** node loss on one of 30 orchestrator nodes, owning 2 run shards.
- **Symptom:** completions for those runs get "owner unavailable" errors at the worker. No new tasks dispatched for those runs. Tasks already running keep running.
- **Answer:**
  - Ownership of the 2 shards moves in ~10 s via etcd. The new owner loads run state from the metadata shard: `task_instance` rows are the truth, in-memory state is a cache.
  - Workers retry completion with backoff for up to 5 min. Their retries land on the new owner. Duplicate completions are rejected by the `(run_id, attempt_id, type)` unique key on `run_event`.
  - A completion that never arrives (worker also died) is caught by lease expiry, same as any zombie.
  - Data at risk: none acknowledged. Latency hit: dispatch pauses ~15 s for 1/32 of runs.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: worker finishes the task, then dies before reporting
- **Trigger:** process killed between "side effect committed" and "completion RPC acked".
- **Symptom:** the task looks RUNNING until its lease expires (60 s + grace), then LOST, then a new attempt starts.
- **Answer:**
  - This is the gap no scheduler can close. The platform cannot know whether the side effect happened.
  - At-least-once (default): attempt 2 runs with the same idempotency key `(run_id, task_id)`. The task author must make the effect idempotent: overwrite the output partition, `INSERT ... ON CONFLICT`, or check a marker the task wrote at the end of attempt 1.
  - At-most-once mode: the task goes to UNKNOWN, no auto retry, the owner is paged and decides. Use it for "send the invoice" style tasks.
  - The platform's part: the completion RPC is idempotent and fenced, so a late attempt-1 report after attempt 2 started is rejected and cannot double-count.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: metadata shard primary is down
- **Trigger:** disk failure on the Postgres primary of run shard 17.
- **Symptom:** run creation for jobs whose new `run_id` hashes to shard 17 fails, completions for runs on shard 17 fail. 1/64 of traffic.
- **Answer:**
  - Synchronous replica in another AZ is promoted in about 30 s. No acked write is lost (`synchronous_commit = on`).
  - Trigger nodes hold the fire in memory and retry; `next_fire_at` was not advanced, so a trigger-node crash during the outage still cannot lose it.
  - Workers retry completions for up to 5 min. Running tasks are unaffected.
  - If promotion takes longer than the lease grace, some attempts are marked LOST when the shard returns and are retried. Acceptable under at-least-once. At-most-once tasks go UNKNOWN.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: etcd loses quorum for two minutes
- **Trigger:** two of five etcd nodes down plus a partition.
- **Symptom:** owners cannot renew leases. No reassignment possible.
- **Answer:**
  - Each owner tracks its own lease expiry on a monotonic clock. Until expiry it keeps working. At expiry it stops firing and stops orchestrating, because it cannot know if someone else was assigned its partitions.
  - Result: after 10 s, triggers stop fleet-wide. This is fail-closed and it is deliberate: a double fire is worse than a late fire for most jobs, and a late fire is what misfire policy exists for.
  - Operator switch "freeze ownership": current owners continue without renewals during a known etcd incident. Human decision because it trades single-owner safety for progress.
  - When etcd returns: leases renew, overdue fires are caught up by each owner from its own wheel, no reload needed.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: matching service node dies
- **Trigger:** the node holding the in-memory ready queue for pool `etl-large` restarts.
- **Symptom:** dispatch latency for that pool spikes for a few seconds.
- **Answer:**
  - The matching cache is not the truth. `task_instance WHERE state = QUEUED AND pool = X` on the metadata shards is.
  - The replacement node rebuilds by scanning QUEUED rows for its pools (indexed on `pool, priority, queued_at`), a few thousand rows, under 1 s.
  - Workers long-poll, reconnect on error, and get tasks from the new node.
  - No task is lost or duplicated: the QUEUED to RUNNING transition is a conditional update on the shard, so two matching nodes handing out the same task lose the race at the DB.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: the event bus (Kafka) used for notifications and event triggers is down
- **Trigger:** Kafka cluster outage for 20 minutes.
- **Symptom:** event-triggered jobs do not fire. UI read model is stale. Cron jobs are unaffected.
- **Answer:**
  - Cron triggers and task execution never touch Kafka on the critical path. That is why the trigger plane reads `next_fire_at` from the metadata store, not from a stream.
  - `JobRunSucceeded` events are written to an outbox table in the same transaction as the run's terminal event and published by a relay. When Kafka returns, the relay drains the outbox in order, event triggers fire late, and the unique key on `run` keeps them from firing twice.
  - Dashboards catch up from CDC.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

---

## 2. Consistency

## Edge case: two trigger nodes both think they own partition 17
- **Trigger:** node A's lease expired during a 12 s GC pause. Node B was assigned the partition. A wakes up and fires.
- **Symptom:** none visible if the design is right.
- **Answer:**
  - Both try `INSERT run (job, 09:00) ON CONFLICT DO NOTHING`. One inserts, one gets 0 rows.
  - The cursor update is `UPDATE job SET next_fire_at = ... WHERE partition = 17 AND owner_epoch = 41`. A's epoch is stale, 0 rows, A drops the partition.
  - Two mechanisms, deliberately: the unique key protects the data; the epoch check tells the stale owner to stop before it does anything else. Neither relies on clocks.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: a worker is slow, not dead, and reports after its replacement finished
- **Trigger:** 90 s GC pause or network partition on worker 1 during attempt 1.
- **Symptom:** attempt 1 LOST at 60 s + grace, attempt 2 dispatched, attempt 2 succeeds, then attempt 1 reports success.
- **Answer:**
  - `UPDATE task_instance SET state = SUCCESS WHERE run_id = ? AND task_id = ? AND current_attempt = 1` matches 0 rows. The orchestrator answers 409 stale attempt and the worker stops.
  - The side effect happened twice. That is the at-least-once contract, and the idempotency key is what makes twice equal once.
  - What to tune: the lease (60 s) and grace (2 heartbeats) set how long a real zombie holds a slot vs how often a slow worker is wrongly replaced. Long tasks heartbeat every 10 s regardless of duration.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: user edits the DAG while a run is halfway through
- **Trigger:** `PUT /jobs/{id}` creates `dag_version` 8 while run 123 pinned to version 7 is RUNNING.
- **Symptom:** none. Run 123 continues on version 7. The next run uses version 8.
- **Answer:**
  - A run pins `dag_version` at creation. `task_instance` rows were materialized from that version. Later edits create a new immutable version and never touch old rows.
  - The UI shows the run against its pinned version, not the current one, so a removed task still renders.
  - If the user wants the new version now: cancel and re-trigger, or wait. There is no "hot swap" because a task added mid-run has no defined upstream state.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: A succeeds, B fails after 3 retries, C depends on both
- **Trigger:** default trigger rule `all_success` on C.
- **Symptom:** run FAILED, C UPSTREAM_FAILED, alert to the job owner.
- **Answer:**
  - When B goes FAILED, the orchestrator evaluates C's rule: `all_success` can no longer be satisfied, so C goes UPSTREAM_FAILED without running. Its downstreams cascade the same way.
  - Run is FAILED when every task is terminal. One alert per run, not per task, with the first failing task named.
  - Repair run: user calls `POST /runs/123/repair`, which clears B, C and every downstream of B back to NONE (in-degree recomputed), keeps A's SUCCESS, bumps `attempt` counters, same `run_id`, same pinned version. Only B and C execute.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: two completion RPCs for the same attempt (network retry)
- **Trigger:** worker's completion RPC times out at the client after the server committed it. Worker retries.
- **Symptom:** none if the design is right.
- **Answer:**
  - `run_event` has a unique key `(run_id, attempt_id, event_type)`. The second insert conflicts, the orchestrator returns the same success response. The downstream evaluation already ran once and is not repeated because the state transition already happened.
  - This is why completion is "append event and update row in one transaction", never two writes.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: clocks on scheduler nodes differ by 200 ms
- **Trigger:** NTP drift on one trigger node.
- **Symptom:** that node fires 200 ms early or late relative to the others.
- **Answer:**
  - Fire decisions are `next_fire_at <= now()` on the owner's clock, so the error is bounded by the skew, which is far inside the 1 s precision target.
  - Ownership never depends on wall clocks: leases are etcd's, epochs are integers, and the owner's local expiry uses a monotonic clock.
  - Two owners never compare clocks with each other; the DB unique key handles the overlap.
  - Where skew would matter and we avoid it: ordering events across runs. Each run's events are ordered by a per-run sequence number, not by timestamp.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: cron at 02:30 America/New_York on the DST change day
- **Trigger:** clocks go back at 02:00 in November, so 01:00 to 02:00 happens twice; in March 02:00 to 03:00 does not exist.
- **Symptom:** naive implementations fire twice in November and zero times in March.
- **Answer:**
  - Compute `next_fire_at` in the job's timezone with a library that follows the IANA database, then store it in UTC.
  - Policy per job for the March gap: fire at the next valid instant (03:30) once. For the November repeat: fire once, at the first occurrence. Both are Quartz-style and match what users expect from a "daily 02:30" job.
  - The unique key is on UTC `scheduled_time`, so two local 02:30s in November are two distinct UTC instants; the policy above is what prevents the second fire, not the key.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

---

## 3. Scale

## Edge case: 900 k runs fire at midnight
- **Trigger:** 45% of jobs are hourly at :00 and 45% are daily at 00:00. Both align at midnight.
- **Symptom:** run inserts and root-task dispatches spike to hundreds of times the average for about a minute.
- **Answer:**
  - Trigger nodes batch inserts (1,000 runs per `INSERT`) and spread them over the 1 s precision window; 900 k run rows plus 1.8 M root task rows plus their events are 5.4 M rows, about 84 k row writes per shard in that one second, batched, at the edge of what one Postgres primary handles and the reason we shard at all. This is the red node.
  - Jitter: a job may declare `spread_seconds` (Google cron's `?`), and platform-wide the default for new jobs is a 60 s spread. Aligned jobs without spread are the exception, not the rule.
  - Dispatch is capped by pool slots, not by the scheduler. 1.6 M root tasks do not start in 1 s because there are not 1.6 M free slots. The queue absorbs; the NFR is "run row exists within 1 s", not "task started within 1 s".
  - What to say if pushed: the 5.4 M already assumes lazy materialization (roots at creation, the rest as they become ready). Eager would be 12.6 M rows, 200 k per shard, which Postgres does not do.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: one task fans out into 5,000 dynamic sub-tasks that feed one join
- **Trigger:** `map` over a list of files.
- **Symptom:** 5,000 completions all decrement one in-degree counter on the join task inside one run shard. The run's owner is single-threaded per run.
- **Answer:**
  - The per-run owner already serializes, so there is no row-lock contention, only throughput: 5,000 events on one run. At ~2 ms per event transaction that is 10 s of owner time. Fine for one run; bad if 100 such runs land on one shard.
  - Coalesce: the owner batches events per run in a 100 ms window and applies them in one transaction. 5,000 events become ~50 transactions.
  - Cap `max_map_width` (say 10 k) and `max_active_tasks_per_run`, and spread hot jobs across shards by hashing `run_id`, which is already random.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: one tenant submits a 90-day backfill for a 500-task DAG
- **Trigger:** `POST /jobs/{id}/backfill?from=..&to=..` creates 90 runs, 45 k tasks.
- **Symptom:** without fairness, the tenant's pool is saturated and today's SLA run waits behind backfill tasks.
- **Answer:**
  - Backfill runs carry `lane = backfill`. The matcher gives the backfill lane at most 20% of a pool's slots while the normal lane has demand, 100% when idle. Weighted fair share, not strict priority, so backfill still makes progress.
  - `max_active_backfill_runs` per job (default 3) bounds the tasks in flight.
  - Backfill order is user-chosen: oldest first (natural) or newest first (get today's data fixed first).
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: 200 k long-running tasks each heartbeating every 10 s
- **Trigger:** a fleet of 6-hour Spark tasks.
- **Symptom:** 20 k heartbeats/s hit the orchestrators.
- **Answer:**
  - Heartbeats update an in-memory lease table on the run owner, not the DB. The DB row `lease_expires_at` is refreshed at most once per 60 s per attempt (write-behind). 200 k / 60 = 3.3 k writes/s across 64 shards, negligible.
  - If the owner dies, the new owner reloads `lease_expires_at` from the DB and gives every attempt a fresh grace period before declaring it lost, so a failover never produces a wave of false zombies.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: 10x more jobs next year
- **Trigger:** 10 M jobs, 2 B task instances/day.
- **Symptom:** shard count and event log volume become the constraint.
- **Answer:**
  - Trigger partitions are fixed at 256; each holds 40 k jobs, still fine (a wheel of 40 k entries). Add trigger nodes.
  - Run shards go from 64 to 256. Because `run_id` is hashed, the move is a shard split with dual-write for new runs and drain for old ones; runs are short-lived so the old shards empty in days.
  - `run_event` at 2 TB/day cannot stay in Postgres. Partition by day and ship closed partitions to object storage; hot window shrinks to 7 days.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

---

## 4. Data

## Edge case: a DAG has 100 k tasks
- **Trigger:** a generated DAG.
- **Symptom:** materializing 100 k `task_instance` rows per run at trigger time takes seconds and bloats the shard.
- **Answer:**
  - Materialize lazily: insert roots at creation, insert a downstream row when its first upstream completes. In-degree comes from the immutable `dag_version`, not from rows. This is already the design; the cap below is what stops a single run from being the spike.
  - Cap `max_tasks_per_dag` (say 10 k) and tell the user to use dynamic mapping or a sub-job instead.
  - UI paginates and aggregates by task group.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: run history grows without bound
- **Trigger:** 200 M task instances/day, 5 events each.
- **Symptom:** the metadata shards fill up, vacuum falls behind, index bloat slows the hot path.
- **Answer:**
  - `run`, `task_instance`, `run_event` are range-partitioned by `created_at` day. 30 days hot. Dropping a partition is a metadata operation, not a delete.
  - Closed partitions are exported to Parquet on object storage; the read model queries there for anything older.
  - Retention is a per-tenant policy; legal hold pins partitions.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: replay a run from its event log
- **Trigger:** a bug corrupted `task_instance` state for a run, or an auditor asks "why did this fire".
- **Symptom:** mutable rows disagree with the event log.
- **Answer:**
  - `run_event` is append-only and ordered by `(run_id, seq)`. Replaying it against the pinned `dag_version` reproduces every `task_instance` state deterministically. This is the Temporal / event-sourcing property.
  - Run it as an offline tool, compare, repair the row. Never mutate the log.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: GDPR delete of a tenant
- **Trigger:** tenant offboards.
- **Symptom:** job definitions, run parameters and logs may contain personal data.
- **Answer:**
  - Job definitions and runs are deleted by `tenant_id` from the hot shards; cold Parquet partitions are rewritten without the tenant's rows on a monthly compaction.
  - Log pointers go to object storage where a lifecycle rule deletes the tenant's prefix.
  - Encrypt per-tenant parameters with a tenant key; delete the key first so everything is unreadable immediately, then physically delete on schedule.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

---

## 5. Operations

## Edge case: what pages at 3am
- **Trigger:** the on-call needs a short list.
- **Answer:**
  - `trigger_lag_p99 > 30 s` for 2 min: runs are being created late. Probably an owner failover loop or a shard down.
  - `partition_without_owner > 0` for 60 s or `run_shard_without_owner > 0`: etcd or assigner problem.
  - `lost_attempts_rate > 1%` of completions: a zombie wave, usually a worker network issue or a DB slowdown delaying heartbeat writes.
  - `queued_age_p99 > 5 min` in a pool with free slots: matching is broken. In a full pool it is a capacity ticket, not a page.
  - `event_outbox_lag > 5 min`: Kafka relay stuck, event triggers late.
  - Not a page: individual task failures. Those alert the job owner, not the platform.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: rolling out a new orchestrator version
- **Trigger:** deploy.
- **Answer:**
  - Canary one orchestrator node holding two shards for one hour. Watch `completion_reject_rate`, `dispatch_latency`, `events_per_txn`.
  - Ownership handoff is the normal failover path, so a deploy is 30 controlled failovers of ~10 s each, spread over 30 min.
  - Rollback is the same operation in reverse. State is in the DB, so version N and N+1 can own different shards at the same time as long as the event schema is additive.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: migrating 50 k jobs off a single-scheduler Airflow
- **Trigger:** the legacy scheduler cannot keep up.
- **Answer:**
  - Import DAGs as versioned definitions. Run the new trigger plane in shadow: create runs in a `shadow` state and compare fire times with legacy for two weeks.
  - Flip triggers per job, 5% then 100%. Legacy cron disabled for flipped jobs. The unique key on `run` makes an accidental double-enable harmless.
  - Execution moves per tenant. Rollback per phase is a flag. Full plan in [`diagrams.md` D12](diagrams.md#d12-rollout--migration).
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: a bad deploy of a job definition breaks 1,000 downstream jobs
- **Trigger:** upstream job's output changed shape; every event-triggered downstream fails.
- **Answer:**
  - Failures are per task, alerts are per run and deduplicated per job per hour, so the owner gets 1,000 alerts once, not every 5 minutes.
  - "Pause job" stops new runs. "Mark success" on a task lets a run continue past a known-bad step.
  - Fix upstream, then `repair` the downstream runs from the API in bulk, filtered by `cause = run_u`.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

---

## 6. Security and abuse

## Edge case: a task tries to report completion for another run
- **Trigger:** compromised or buggy worker sends `complete(attempt_id = someone else's)`.
- **Answer:**
  - The attempt lease is a signed token containing `run_id, task_id, attempt_id, expiry`. The orchestrator verifies the signature and that the token matches the current attempt. A guessable integer `attempt_id` is not enough.
  - Workers run in per-tenant pools with tenant-scoped credentials, so a worker in tenant A's pool cannot even reach tenant B's secrets.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: a tenant defines 100 k jobs firing every second
- **Trigger:** abuse or a loop in a job generator.
- **Answer:**
  - Quotas: max jobs per tenant, min schedule interval (say 60 s), max concurrent runs per tenant, max tasks per DAG. Enforced at `PUT /jobs`.
  - Pools are per tenant; one tenant's 100 k runs starve only that tenant.
  - The trigger plane's per-partition wheel has a cap on fires per second per tenant, beyond which runs are created late and the tenant is alerted.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: secrets in task parameters
- **Trigger:** a job passes a database password as a task argument.
- **Answer:**
  - Parameters are references to a secret store, resolved by the worker at start with the tenant's identity, never stored in `run` or `run_event`.
  - Logs are scrubbed for known secret patterns before upload; the platform never reads task logs itself.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident
