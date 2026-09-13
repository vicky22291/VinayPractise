# Distributed job scheduler with DAG dependencies

> One-line answer: split the scheduler into three planes that fail independently. A **trigger plane** owns "when does job J fire next": the job space is hashed into partitions, each partition is leased to one node via etcd with a fencing epoch, and that node keeps the partition's next-fire times in an in-memory timing wheel and creates a run row (idempotent on `job_id + scheduled_time`) in the same transaction that advances `next_fire_at`. An **orchestration plane** owns each run's DAG: one run is always driven by one orchestrator shard, which appends every task state change to a per-run event log and computes newly ready tasks by in-degree counting under the task's trigger rule. An **execution plane** of stateless workers long-polls a per-pool matching service for ready tasks, holds a heartbeat lease per attempt, and reports completion with the attempt's fencing token. Execution is at-least-once; the platform hands every task an idempotency key `(run_id, task_id)` and rejects any completion that carries a stale attempt id.

Tier 1, problem #6 in [`hld/README.md`](../README.md). Reported at Databricks (their Workflows / Jobs product in disguise), at Meta E5/E6 as "design a distributed job scheduler" and at Google as "design cron at scale" (the SRE book has a chapter on it). Airflow, Temporal, Netflix Maestro, Uber Piper and Google's distributed cron are the reference implementations. See [`research/`](research/).

## Problem statement

Users define jobs. A job is a DAG (directed acyclic graph) of tasks with a schedule (cron), or an external trigger (API call, file arrival, upstream job finished). When a job fires, create a run, execute its tasks in dependency order on a shared worker fleet, retry failures per task policy, and tell the user what happened. Do this for a million jobs, where a large fraction of them fire at the same minute, without running any task twice by accident, without missing a trigger when the scheduler node dies, and let a user backfill 90 days of history without starving today's runs.

## Functional requirements

Core:
- Define a job: a DAG of tasks, each with a command or container image, retry policy, timeout, pool, priority, trigger rule (`all_success`, `one_failed`, `all_done`). Job has a cron schedule with a timezone, or is trigger-only. A job definition is versioned. A run pins one version.
- Trigger runs on time (cron), on demand (API), or on an event (upstream job success, dataset arrival). Enforce `max_active_runs` per job and a policy for missed schedules (catch up, fire once, skip).
- Execute tasks in dependency order with retries, timeouts and cancellation. Report per-task state, logs, and run outcome. Alert on failure and on SLA miss.
- Backfill a date range and rerun a failed subtree ("repair run") without re-executing tasks that succeeded.

Below the line (say it out loud):
- The task runtime itself (containers, Spark clusters, autoscaling). We hand a task to a worker pool; the pool is someone else's system. Cross-link: `cluster-manager/` when it exists.
- Data lineage, data quality checks, dataset catalog. Event triggers consume a "dataset updated" event; producing it is not ours.
- Log storage and search. Workers stream logs to object storage; we store a pointer.
- Multi-region active-active. One region owns a job. Regional DR is in section 10.11.

## Non-functional requirements

| Dimension | Target |
|---|---|
| Scale | 1 M job definitions, 10 tasks each. 20 M runs/day, 200 M task instances/day. Average 2,300 task starts/s. Peak at the top of the hour: about 900 k runs are due in the same second at midnight |
| Trigger precision | A run row exists within 1 s of its scheduled time at p99 during normal operation. Never later than 30 s after a scheduler failover. Never lost |
| Dispatch latency | A task whose upstreams are all done is handed to a worker within 2 s at p99, given a free slot in its pool |
| Execution semantics | At-least-once with platform-issued idempotency key. At-most-once available per task for non-idempotent work. Never two attempts of the same task both counted as success |
| Availability | Trigger plane 99.99%. Orchestration 99.99%. Control API (define, view) 99.9% and its loss never stops running work |
| Durability | Once a run or a task state is acknowledged it is never lost. Run history queryable for 30 days hot, 2 years cold |
| Consistency | Run and task state strong within a run (single owner). Cross-run views (dashboards) eventual, seconds |
| Fairness | A 90-day backfill takes at most 20% of a pool's slots while SLA runs are waiting; 100% when the pool is idle |

## What interviewers probe (the ladder)

1. The scheduler node dies at 08:59:59. Do the 09:00 jobs fire? How late? Can two nodes both fire them?
2. A worker stops heartbeating. Dead or slow? What happens if you retry and it was only slow? Who pays for the double run?
3. A worker finishes the task, then dies before it reports. What does your system do, and what must the task author do?
4. 900 k jobs fire at midnight. Show the write rate on your database and what breaks first.
5. A user edits the DAG while a run is halfway through. Which version do the remaining tasks use?
6. Task C depends on A and B. A succeeds, B fails after 3 retries. What state is C in, what state is the run in, who is notified, and how does the user rerun only B and C?
7. Backfill 90 days for a job whose daily run also has to hit its 06:00 SLA. Where does fairness live?
8. A task fans out into 5,000 dynamic sub-tasks that all feed one join task. Where is the hot spot?
9. Why not Kafka as the task queue? What does a lease-based queue give you that a log does not?
10. Cron at 02:30 America/New_York on the day DST ends. How many times does it fire?
11. Clocks on scheduler nodes differ by 200 ms. Which of your comparisons care?
12. Precision within 1 s for 1 M jobs. Do you scan the jobs table every second? What do you do instead?

## Files

| File | What it is |
|---|---|
| [`solution.md`](solution.md) | Full HLD, Bad / Good / Great ladders, nitty-gritty internals |
| [`diagrams.md`](diagrams.md) | The D1 to D12 diagram set |
| [`edge-cases.md`](edge-cases.md) | Every "what if" with a 60-second answer and a confidence box |
| [`deep-dives/trigger-plane-and-timers.md`](deep-dives/trigger-plane-and-timers.md) | Sharded timing wheel, misfire policy, jitter, the :00 spike, failover math |
| [`deep-dives/orchestrator-and-dag-evaluation.md`](deep-dives/orchestrator-and-dag-evaluation.md) | Per-run owner, event log plus mutable state, trigger rules, in-degree counting, DAG version pinning, wide fan-in and fan-out |
| [`deep-dives/dispatch-and-workers.md`](deep-dives/dispatch-and-workers.md) | Pull-based matching, pools, priority, fairness, leases and heartbeats, zombie detection, long vs short tasks |
| [`deep-dives/exactly-once-and-idempotency.md`](deep-dives/exactly-once-and-idempotency.md) | Where duplicates enter, fencing on attempt id, the execute-then-commit gap, at-most-once mode |
| [`deep-dives/leases-failover-and-fencing.md`](deep-dives/leases-failover-and-fencing.md) | etcd leases, partition epochs, split brain, GC pause, reassignment and reload |
| [`deep-dives/backfill-rerun-and-stragglers.md`](deep-dives/backfill-rerun-and-stragglers.md) | Backfill lanes, repair run, speculative execution, SLA miss detection |
| [`deep-dives/metadata-store-and-sharding.md`](deep-dives/metadata-store-and-sharding.md) | Shard by run, the midnight write burst, date partitioning, retention, distributed SQL vs sharded Postgres |
| [`research/`](research/) | Raw web research notes with source links. Input to the files above, not study material |
| `distributed-job-scheduler.excalidraw` | My drawing. Missing until I draw it |
| `my-attempt.md` | My timed attempt before reading the solution |
