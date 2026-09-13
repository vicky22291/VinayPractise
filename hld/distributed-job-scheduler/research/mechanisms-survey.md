# Distributed Job Scheduler: Building-Block Mechanisms

## Sources Reference Table

| ID | URL | Establishes |
|----|-----|---|
| K1 | https://kubernetes.io/docs/concepts/cluster-administration/coordinated-leader-election/ | Kubernetes leader election lease defaults |
| K2 | https://github.com/kubernetes-sigs/controller-runtime/blob/main/pkg/leaderelection/leader_election.go | etcd Lease implementation details |
| K3 | https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/ | CronJob startingDeadlineSeconds and 100 missed limit |
| ZK1 | https://zookeeper.apache.org/doc/current/zookeeperProgrammers.html | ZooKeeper session timeout constraints |
| PG1 | https://airflow.apache.org/docs/apache-airflow/stable/administration-and-deployment/scheduler.html | Airflow HA scheduler with FOR UPDATE SKIP LOCKED |
| K4 | https://github.com/apache/kafka/blob/3cdc78e6bb1f83973a14ce1550fe3874f7348b05/core/src/main/scala/kafka/utils/timer/TimingWheel.scala | Kafka purgatory timing wheel implementation |
| R1 | https://redis.io/docs/latest/develop/data-types/sorted-sets/ | Redis sorted sets and ZRANGEBYSCORE |
| Q1 | https://www.quartz-scheduler.org/documentation/quartz-2.3.0/configuration/ConfigRAMJobStore.html | Quartz misfireThreshold default (60s) |
| T1 | https://docs.temporal.io/workflow-definition | Temporal exactly-once workflows via replay |
| T2 | https://docs.temporal.io/workflow-execution/limits | Temporal history limits (51,200 events, 50 MB) |
| A1 | https://github.com/apache/airflow/issues/37971 | Airflow scheduler_zombie_task_threshold (300s) |
| MR1 | https://research.google/pubs/pub62/ | MapReduce backup tasks: 44% completion reduction (OSDI 2004) |
| SP1 | https://spark.apache.org/docs/latest/configuration.html | Spark speculation defaults (multiplier 1.5, quantile 0.75, interval 100ms) |
| SRE1 | https://sre.google/sre-book/distributed-periodic-scheduling/ | Google SRE: cron jitter and thundering herd |
| SRE2 | https://sre.google/sre-book/handling-overload/ | Google SRE: retry budget 10% limit |
| AWS1 | https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/ | AWS full jitter backoff strategy |
| SF1 | https://docs.aws.amazon.com/step-functions/latest/dg/service-quotas.html | Step Functions standard execution: 25,000 events limit |
| ST1 | https://research.google/pubs/spanner-googles-globally-distributed-database-2/ | Google Spanner TrueTime: 4-10ms epsilon (OSDI 2012) |

---

## 1. Leader Election and Leases

**How it works.** One scheduler acquires a lease (etcd Lease [K1] or ZooKeeper ephemeral node). Lease expires unless renewed. A new node cannot take the lease until TTL passes. During the lease, only that scheduler runs the scheduling loop.

**Defaults.** Kubernetes leader election uses etcd with leaseDurationSeconds=15s [K1], renewDeadline=10s [K1], retryPeriod=2s [K1]. Scheduler renews lease every ~7.5s (half the duration). ZooKeeper session timeout is 2× to 20× tickTime [ZK1]; no universal default. Both systems rely on cluster membership to detect dead nodes.

**Critical gap.** A lease is not a lock without a fencing token. If the old leader pauses (GC) but the lease expires, both old and new leader can act simultaneously. Solution: require tokens that increase monotonically with each lease grant [Kleppmann]. The new leader must include a higher token in all writes; old leader's writes are rejected by the store.

**Failure mode.** GC pause > leaseDurationSeconds causes split-brain. JVM pause > 15s means lost leadership and immediate election of a new leader, yet the old leader's scheduler loop still running in the background. Result: duplicate tasks scheduled. Raft election timeout (etcd ~1000ms, heartbeat ~100ms) determines detection speed. Network partition causes two leaders in two partitions.

---

## 2. Database-as-Queue: SELECT ... FOR UPDATE SKIP LOCKED

**How it works.** Scheduler polls tasks with `SELECT * FROM task_instance WHERE state='queued' FOR UPDATE SKIP LOCKED LIMIT 1`. The SKIP LOCKED clause lets multiple schedulers grab different rows without blocking [PG1]. Postgres locks the row and marks it reserved, preventing other schedulers from seeing it. No distributed coordination (Zookeeper, Chubby) needed.

**Why Airflow uses it.** Avoids Celery + Redis overhead. Scales to ~50 concurrent scheduler processes on Postgres without significant contention [PG1]. Single source of truth: the database. No separate queueing system to synchronize. Airflow HA scheduler uses this for multi-node HA since 1.10+.

**Bottleneck.** Dead tuple bloat degrades sequential scans. Vacuum must reclaim deleted rows before table becomes a sequential scan rather than index scan. Without aggressive vacuum, scan latency jumps from ~1ms to 100ms+. Partitioning task_instance by run date reduces table size and locks [PG1]. Index on (state, run_date) is critical.

**Failure mode.** Long-running vacuum blocks queries and stalls the entire scheduler. Tasks queue up behind the vacuum lock. Clock skew (scheduler A thinks task deadline is :05, scheduler B thinks :07) causes duplicate executions of the same run ID if both try to execute [PG1].

---

## 3. Timers at Scale: Hierarchical Timing Wheels

**How it works.** Kafka's purgatory uses a hierarchical timing wheel [K4], implemented by Varghese and Lauck 1987 for TCP retransmission. Multiple levels of buckets; each bucket holds timers due within that time window. Example: L1 = 64 buckets (1ms each), L2 = 64 buckets (64ms each), L3 = 64 buckets (4s each). O(1) insertion/removal per level (no search). Avoids scanning all timers on every tick.

**Kafka example.** Broker holds delayed produce requests (batch delay = 10ms). Timing wheel handles millions of concurrent timers without a full heap (heap = O(log N) per insert). Purgatory sits on the critical path of every produce request; must be fast. O(1) enables this.

**Alternatives.** Redis sorted sets: ZRANGEBYSCORE(key, 0, now) + Lua atomic pop [R1]. Good for few thousand timers (1-100k). Timing wheel wins at scale (millions). SQS uses timing wheel internally for `DelaySeconds` (max 900s). Kubernetes uses heap + backoff for exponential backoff timers.

**Failure mode.** If scheduler lags behind wall time (scheduler thread blocked), timers fire late. All delays become >= actual delay. If a timer bucket is never drained (stuck thread, thread pool saturated), cascading backlog: timers accumulate, memory bloats, older timers starve. Mitigate with watchdog (check bucket drain rate, alarm if stalled).

---

## 4. Cron Semantics and Misfire Handling

**How it works.** Quartz defines misfireThreshold=60,000ms (60s) [Q1]. If a trigger fires more than 60s late, skip it rather than fire 100 times to catch up. Kubernetes CronJob hard-caps missed schedules at 100 [K3] to prevent runaway catch-up after scheduler downtime. If downtime > 100 * 60 seconds, the missed executions are discarded.

**Thundering herd problem.** If 30% of DAGs are cron-aligned to :00 (top of hour), all 30,000 become ready simultaneously [SRE1]. Load graph looks like a staircase, not a smooth line. Solution: random offset per DAG (uniformly spread :00 to :59) to flatten the spike [SRE1]. Also called jitter.

**DST and timezone.** CronTab syntax does not account for DST transitions. A 2am cron on the spring-forward day (when 2am becomes 3am) might fire twice, zero times, or at the wrong instant. Use UTC or explicit timezone library (Temporal uses tzdata). Test cron expressions around DST boundaries [Kleppmann].

**Failure mode.** misfire threshold too low (5s) causes cascade drops of valid executions. Too high (300s) means stale data (schedule says 9:05am but now 9:10am). Clock skew (±100ms) between leader and followers causes one scheduler to see "misfired" while others see "on time" and each executes the task.

---

## 5. Exactly-Once Execution (and Why It Is Impossible)

**The fundamental truth.** Exactly-once for side effects across a network is impossible (two generals problem, FLP impossibility). What is possible: exactly-once per the scheduler's state machine (at-most-once from the scheduler's perspective, but from the task's perspective at-least-once with idempotency keys).

**At-least-once plus idempotency.** Temporal executes activities at-least-once, then records the result in workflow history [T1]. On replay, the activity result is looked up and reused (not re-executed). Workflow code itself is deterministic (no side effects in workflow, only in activities); activities are idempotent via unique constraint or idempotency key (request_id).

**Airflow's gap.** If a task's database write succeeds but the scheduler crashes before recording success to task_instance, the task is re-queued and runs again. The task must handle duplicate execution via unique constraint (e.g., ON CONFLICT DO NOTHING), or UPDATE upsert logic (idempotent = result same on re-run).

**The outbox pattern.** Write the event and the scheduler state in the same database transaction. Event is inserted into an outbox table. A separate relay process reads the outbox, publishes events to external systems (Kafka, webhook), and marks rows as published. If the relay fails mid-publish, re-publish is idempotent. Database is the single source of truth; external systems are not.

**Failure mode.** Non-idempotent tasks fail under replay. Side effects leak (payment processed twice, email sent twice). No way to detect or prevent without application-level idempotency. Temporal + Airflow cannot guarantee exactly-once for external APIs unless the API provides idempotency keys.

---

## 6. Worker Liveness: Heartbeats and Zombie Task Detection

**How it works.** Worker sends a heartbeat every 5s [A1]. Scheduler marks a task zombie if > 300s [A1] without a heartbeat. Kubernetes uses 40s node-monitor-grace-period [K3].

**The double-run risk.** If a worker is slow (GC, I/O) but not dead, it sends a heartbeat after 200s. Scheduler marks the task zombie at 300s and reschedules it. Original worker still running. Duplicate execution.

**Mitigation.** Increase heartbeat frequency and detection threshold. Use task IDs and idempotent writes. Temporal activities include heartbeat timeout [T1].

**Failure mode.** Network jitter causes false positives (mark alive as dead). Clock skew between worker and scheduler causes one to think the task timed out while the other thinks it is fine.

---

## 7. Retries and Exponential Backoff with Jitter

**Backoff formula.** Full jitter: sleep = random(0, min(cap, base * 2^attempt)) [AWS1]. Prevents synchronized retry spikes from multiple clients.

**Retry budget.** Google SRE book: limit retries to 10% of overall traffic [SRE2]. Prevents exponential amplification. If 100 requests each retry once, limit to 100 total attempts (original + 10 retry attempts).

**Dead-letter queue.** After max_retries, send to DLQ for manual inspection. Never retry indefinitely.

**Failure mode.** Unbounded retries cause thundering herd. Backoff cap too low (e.g., 1s) starves other requests. Clock skew causes retry storms (all clients backoff in sync).

---

## 8. Stragglers and Speculative Execution

**MapReduce backup tasks.** Master schedules a backup copy of slow-running tasks near completion [MR1]. If one finishes, the other is killed. Reduces completion time 44% in presence of stragglers (slow machines) [MR1]. The 44% is measured on heterogeneous clusters where some machines are 10x slower than others (OSDI 2004).

**Spark speculation.** Launch a task copy if the original exceeds median time * multiplier=1.5 [SP1], after quantile=75% [SP1] of remaining tasks finish, checked every interval=100ms [SP1]. Example: median task = 10s. If original task > 15s at the 75% mark, schedule a backup. Cost: minimal resource overhead (few % additional CPU), dramatic latency reduction (p99 tail reduced by 50%+).

**Dean and Barroso: The Tail at Scale.** In large systems, tail latency dominates (p99 matters more than average). Stragglers are caused by: background processes, GC, hardware variability. Mitigations: backup tasks, request hedging (send same request to N replicas, use first response, cancel others), tied requests (N replicas with request 1 is primary, request 2 waits 1ms then fires to backup).

**Non-idempotent safety.** Speculation is unsafe if the task has side effects (database write, external API call, file modification). Two copies can execute and both complete. Always use deduplication keys or idempotent writes (or mark task as non-speculable).

**Failure mode.** Aggressive speculation (multiplier=1.2) wastes CPU and often doesn't help (both copies are slow). Conservative speculation (multiplier=2.0) loses tail-latency benefit entirely. Wrong threshold = wasted resources or no improvement.

---

## 9. DAG Execution: Ready-Set and Trigger Rules

**Kahn's algorithm.** Track in-degree (number of unfinished upstreams) per task. When a dependency finishes, decrement its in-degree and check downstream. When in-degree=0, task becomes ready and moves to queue [Standard Algorithm]. Avoids recursive DFS (stack overflow on deep DAGs).

**Trigger rules.** Airflow: all_success (wait for all upstreams), one_failed (fire if any upstream fails), all_done (skip failures and execute), none_failed_min_one_success (skip but fire if at least one upstream succeeds). Each rule changes DAG traversal logic. Similar to Kubernetes condition status (Pending, Running, Failed). Temporal uses simpler semantics (no conditions; all tasks must succeed or the workflow fails).

**Dynamic task mapping.** A task produces N outputs; fan out to N downstream task copies. Complicates in-degree tracking. Must dynamically add/remove tasks from the ready-set. Kubernetes Job parallelism=N is simpler (N copies of the same Pod). Airflow's map operator creates N Task objects.

**DAG versioning.** Pin each run to a DAG version (git hash or timestamp). Prevents mid-run DAG redefinition. Example: V1 defines task A→B→C. During run, user pushes V2 (task D added). If run switches to V2 mid-stream, task IDs change and state is lost [T1]. Temporal enforces versioning. Airflow 3+ adds DAG versioning.

**Failure mode.** Cycle detection runs at parse time, not execution time. If DAG has dynamic cycle (produced during map_task output), crash occurs at runtime with full task history logged. Max DAG width (1000 tasks) or depth (100 levels) limits prevent memory exhaustion. Graph topological sort failure indicates the cycle.

---

## 10. Priority, Fairness, and Backpressure

**Pools and slots.** Define a pool (e.g., "gpu_pool" with 10 slots). Only 10 tasks run in the pool concurrently. Tasks queue until slot frees. Prevents resource overcommit. Airflow: all tasks use "default_pool" with slot=128 by default.

**Per-tenant quotas.** Tenant A gets 100 QPS, Tenant B gets 50 QPS. Use token bucket (refill at rate, cap at limit) or sliding window counter. Backpressure: reject above quota with HTTP 429. Quotas per customer and tunable per SLA.

**Weighted fair queueing.** Tenant A weight=2, Tenant B weight=1. Allocate in ratio 2:1 (every 3 tasks, 2 from A, 1 from B). Prevents starvation. YARN capacity scheduler uses this. Simpler than strict priority (which starves low-priority forever).

**Backfill lanes.** Separate queue: backfill (historical, 30-day rerun) vs real-time (today's cron). Backfill runs 30% throughput. Real-time guaranteed 70%. Airflow lacks this; all compete, starving real-time.

**Failure mode.** Unfair queuing starves low-priority. No backfill lane → 30-day backfill consumes 90%, real-time misses SLO. Quota too low → timeouts. Too high → cost overrun.

---

## 11. Observability: Heartbeats, Metrics, and SLO Tracking

**What to monitor.** Task latency (p50, p95, p99), scheduler loop latency (ready→running), queue depth (backlog), pool utilization (%), retry rate, zombie rate. Miss these and system is blind.

**Scheduler heartbeat.** Publishes metrics every 10s: tasks scheduled/completed, pool utilization, queue depth. Alerts: queue depth > 10k (backlog), retry rate > 5% (degradation), zombie rate > 0.1% (worker failure).

**Task-level tracing.** Timestamps: queued_at, started_at, finished_at, retried_at. Latency = finished - queued. P99 SLO = 1-5 minutes typically. Track slow tasks by DAG, priority, pool.

**Failure mode.** Heartbeat > 60s → operator assumes scheduler died, alarm fires. But heartbeat without progress means stuck (queue full, vacuum blocked, all workers dead). Heartbeat ≠ health.

**Pools and slots.** Define a pool (e.g., "gpu_pool" with 10 slots). Only 10 tasks can run in the pool concurrently. Tasks queue until a slot frees. Prevents resource overcommit.

**Per-tenant quotas.** Tenant A gets 100 QPS, Tenant B gets 50 QPS. Use token bucket or sliding window counter. Backpressure: reject requests above quota.

**Weighted fair queueing.** Tenant A weight=2, Tenant B weight=1. Allocate resources in ratio 2:1, not strict turn-taking. Prevents starvation.

**Backfill lanes.** Separate queue for backfill (historical) vs real-time tasks. Backfill runs at 30% throughput. Guarantees that today's SLA tasks are not starved by a 30-day backfill [Common pattern].

**Failure mode.** Unfair queuing starves low-priority tenants indefinitely. No backfill lane → 30-day backfill blocks real-time. Quota too low → request timeouts.

---

## 12. Clock Skew and Monotonic Time

**NTP in datacenters.** Typical skew < 100µs with good NTP [ST1]. But distributed schedulers must assume skew and never rely on == comparisons. Use one leader's clock as source of truth (scheduler clock is law). All comparisons use >= and <=, not ==. Delta-check: if system clock jumps backward > 1 second, log alarm and potentially pause scheduling.

**TrueTime.** Google Spanner exposes clock uncertainty as [earliest, latest] interval, 4-10ms epsilon [ST1]. Absolute ordering across all writes possible. GPS atomic clock synchronized. But 4-10ms epsilon is expensive (GPS, atomic clock, network sync); most systems use NTP (100µs) and accept occasional skew incidents.

**Monotonic clocks.** Use CLOCK_MONOTONIC, not gettimeofday() (wall clock). Monotonic never goes backward (ignores NTP adjustments). Use for timeouts and delays. Use gettimeofday() ONLY for logging/comparison of scheduled times. Example: task deadline = gettimeofday() + 3600 (use wall clock). Timeout = CLOCK_MONOTONIC + 3600 (use monotonic for actual sleep).

**Failure mode.** NTP adjustment backward (step correction, not gradual slew) causes timers to fire early or never. Tasks scheduled for t=100 with deadline t=101 become immediately eligible if clock jumps from t=102 back to t=99. Scheduler and worker disagree on deadline (worker sees 102, scheduler sees 99). Result: duplicate or missed execution.

---

## 13. Event-Sourced Workflow State

**Append-only log.** Every workflow state transition is an immutable event: task_scheduled, task_started, task_succeeded, task_failed. Replay events to rebuild state [T1].

**History limits.** Temporal: 51,200 events or 50 MB per run [T2]. Step Functions: 25,000 events [SF1]. Beyond limit, must archive history or use Continue-As-New [T2].

**Snapshotting.** Periodically write current state to snapshot. On replay, load latest snapshot + events after snapshot, not from the beginning. Reduces replay latency.

**Failure mode.** History bloat from logging every micro-second delays replay. No snapshotting strategy → replay time grows quadratically with run length. Archived history becomes unretrievable.

---

## Worked Example: Cron Spike Calculation

**Setup.** 100,000 DAGs, average 10 tasks each = 1,000,000 total tasks. All tasks are cron-hourly. 30% aligned to :00 (the natural hour boundary), 70% spread across other minutes (:05, :13, :42, etc.).

**At the :00 spike:**
- Aligned DAGs: 100k * 30% = 30,000 DAGs become ready at the hour boundary.
- Tasks to schedule: 30,000 * 10 = 300,000 tasks must be queued in 1 minute (60 seconds).
- Tasks/second at spike: 300,000 / 60 = 5,000 tasks/second peak.
- Spike duration: ~2 minutes (ramp up 1 min, drain 1 min) = 300,000 total task state transitions.

**Average (non-spike) load:**
- Total tasks/hour: 1,000,000 tasks.
- Tasks/second average: 1,000,000 / 3600 = 278 tasks/second.
- Ratio: Peak is 18x average. Clustering at :00 is critical.

**Database queue pressure (FOR UPDATE SKIP LOCKED):**
- Spike: 5,000 tasks/sec * 10 schedulers (if 10 run in parallel) = 50,000 SKIP LOCKED queries/second against task_instance table.
- Each scheduler grabs ~500 rows per second (Postgres sequential scan with good indexes on (state, run_date)).
- Lock contention: Task row locks held for ~10ms per scheduler. With 10 schedulers, collision rate rises sharply if table is not partitioned.
- Bottleneck: Vacuum must keep dead-tuple ratio < 10%, or sequential scans degrade from 1ms to 100ms+. At 100ms per scan, throughput drops to 10 tasks/sec (not 500), and queue explodes.

**Mitigation.** Partition task_instance by run_date. Scope scheduler queries to today's partition only. Table size per partition = 1M / 365 ≈ 2.7k rows (average). Index on (state, run_date) fits in L3 cache. Per-scheduler throughput remains ~500 tasks/sec even at spike. Alternatively, scale horizontally: 20 schedulers instead of 10 halves the per-scheduler load to 2,500 tasks/sec, reducing lock contention.

---

## What This Means for the Interview Design

1. **Leader election is not free.** Leases expire. GC pauses cause split-brain. Require fencing tokens. Explain the trade-off: complexity vs correctness. Know the difference between a lease and a lock.

2. **Database-as-queue scales to ~50 concurrent readers, then contention dominates.** FOR UPDATE SKIP LOCKED is brilliant for HA without Celery, but dead-tuple bloat is a footgun. Mention vacuum strategy and index selection. Partitioning by date is not optional.

3. **Timers at scale require hierarchical data structures, not heaps.** Kafka's timing wheel handles millions with O(1) per operation. Redis sorted sets handle thousands with O(log N). Know the scalability difference and why.

4. **Cron misfires are a landmine.** misfire_threshold=60s is baked into Quartz [Q1]. DST breaks naive CronTab (2am becomes 3am on spring-forward). Thundering herd at :00 requires jitter [SRE1]. Show you know this; it trips up most candidates.

5. **Exactly-once is impossible; at-least-once + idempotency is practical.** Temporal uses history replay [T1]. Airflow uses database upserts. Outbox pattern for side effects. Never claim "exactly-once for side effects" in an interview.

6. **Zombie task detection has a false-positive window.** Scheduler marks task dead at 300s [A1]. Worker might still be running (network delay, GC). Either retry is idempotent, or you lose work. Temporal activity heartbeat reduces this risk.

7. **Speculative execution is not free.** Non-idempotent tasks break under backup copies. Aggressive speculation (multiplier 1.5, quantile 0.75) [SP1] wastes CPU but slashes tail latency. Know when to use it (homogeneous workload) and when not to (heterogeneous or side-effectful).

8. **DAG versioning is non-negotiable.** Mid-run DAG changes cause task-id collisions and state corruption. Pin each run to a DAG version (git hash). Temporal enforces this [T1]. Airflow 3+ adds DAG versioning.

9. **Pools and slots prevent thundering herd.** But unfair pooling starves low-priority tenants indefinitely. Weighted fair queueing (weight A:B = 2:1) requires token bucket refill, not FIFO. Backfill lanes separate backfill (30% throughput) from real-time (70%).

10. **Clock skew breaks timing.** NTP < 100µs in datacenter but not guaranteed [ST1]. Use monotonic clocks for delays and timeouts. Use >= comparisons for wall-clock deadlines. TrueTime costs (GPS + atomic clock) but guarantees 4-10ms bound [ST1].

11. **Event sourcing explodes in size.** Temporal 51,200 events or 50 MB [T2]. Step Functions 25,000 events [SF1]. Snapshotting is mandatory, not optional. Continue-As-New for very long runs (reset history).

12. **Scaling from 1 to 100k DAGs requires rethinking every layer.** Single scheduler works until :00 spike (5,000 tasks/sec). Multi-scheduler requires FOR UPDATE SKIP LOCKED. Multi-tenant requires quotas and pools. Know the thresholds and how they cascade.

13. **Failure modes beat algorithms.** Slow worker (not dead), late heartbeat, clock skew, vacuum lag, partition hot-spot, GC pause > lease TTL. Interviewers probe failure modes and mitigation, not happy-path algorithms. Name the bottleneck. Mark it red.

14. **Numbers matter.** 15s lease, 300s zombie threshold, 5,000 tasks/sec spike, 51,200 event limit, 60s misfire threshold [Q1]. Interviewers verify you know real systems, not theory. Cite the source (Airflow, Temporal, Quartz) if asked.

---

## Spot-check corrections (added after review, 2026-09-13)

| Claim above | Check | Verdict |
|---|---|---|
| Kubernetes leader election 15 s / 10 s / 2 s | These are the client-go `leaderelection` defaults used by kube-controller-manager and kube-scheduler (`--leader-elect-lease-duration` 15 s, `--leader-elect-renew-deadline` 10 s, `--leader-elect-retry-period` 2 s) | Right values, wrong page: the "coordinated leader election" page is about a different feature. https://kubernetes.io/docs/reference/command-line-tools-reference/kube-controller-manager/ |
| etcd Raft defaults: election 1000 ms, heartbeat 100 ms | etcd tuning docs | Confirmed. https://etcd.io/docs/v3.5/tuning/ |
| "Scales to ~50 concurrent scheduler processes on Postgres [PG1]" | The Airflow scheduler page says nothing of the kind | Invented. Published data point: Astronomer's 2020 benchmark of the 2.0 HA scheduler with 1 to 3 schedulers on Postgres, throughput roughly linear to 3. Beyond that is [unverified] |
| "Kubernetes 40 s node-monitor-grace-period [K3]" | Value right, cited to the CronJob page | Source is the kube-controller-manager flag `--node-monitor-grace-period` default 40 s; pod eviction after the taint-based `tolerationSeconds` 300 s |
| Airflow zombie threshold 300 s [A1] | Confirmed from the config reference, where it is now `task_instance_heartbeat_timeout` = 300 s, checked every 10 s; heartbeat 5 s | Use the config reference URL, not the GitHub issue |
| "Typical NTP skew < 100 us [ST1]" | The Spanner paper does not say this | [unverified]. Safe statement: NTP in a datacenter is typically sub-millisecond to a few ms; chrony with a local stratum-1 source gets to tens of us. TrueTime epsilon in the Spanner paper: about 1 to 7 ms, average about 4 ms |
| MapReduce 44% | The OSDI 2004 paper says the sort takes 44% longer with backup tasks disabled | Right number, phrasing "reduces by 44%" is slightly off |
| Spark speculation defaults multiplier 1.5, quantile 0.75, interval 100 ms | Spark configuration page | Confirmed |
| Full jitter formula, 10% retry budget, Quartz 60 s, CronJob 100 misses, Temporal 51,200 / 50 MB, Step Functions 25,000 | Consistent with the primary docs | Confirmed |
| Section 11 repeats four paragraphs of section 10 | Agent error | Ignore the duplicate |
| Worked example: "300,000 tasks in 1 minute, 5,000 tasks/s" | The math spreads the aligned fires over 60 s and counts all 10 tasks per DAG as due at :00 | Redone in `solution.md` §2: only root tasks are due at :00, and they are due in the same second, not the same minute. The spike is run creation, and it is about 1 s wide unless jitter is added |
