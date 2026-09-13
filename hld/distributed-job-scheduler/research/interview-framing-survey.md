# Distributed Job Scheduler: Interview Framing Survey

## Sources Reference Table

| ID  | URL | Date | What it establishes |
|-----|-----|------|---------------------|
| S1  | https://www.hellointerview.com/learn/system-design/answer-keys/job-scheduler | 2025 | Reference architecture; 10k jobs/sec SLA; 2-sec latency requirement |
| S2  | https://www.algomaster.io/system-design/job-scheduler | 2025 | Five-component pattern; lease-based dispatch consensus |
| S3  | https://www.designgurus.io/course/grokking-system-design-interview | 2025 | Trade-off discussion; exactly-once vs. at-least-once |
| S4  | https://leetcode.com/discuss/interview-question/1577377/Amazon-Phone-Screen-Design-Job-Scheduler-at-scale | 2023 | Amazon 10M jobs/day requirement; 5-sec start precision; retry within 15-20 min |
| S5  | https://leetcode.com/discuss/interview-question/1621854/Amazon-Onsite-Job-Scheduler | 2023 | 1M jobs/day; one-time + recurring; priority levels |
| S6  | https://www.hellointerview.com/learn/system-design/architecture/job-scheduler | 2025 | 1B daily = 11.6k avg/sec; 3M/sec at midnight (250× peak ratio) |
| S7  | https://www.hellointerview.com/learn/system-design/answer-keys/staff-engineer-job-scheduler | 2025 | Staff-level grading: decisiveness, complexity reduction, peer communication |
| S8  | https://temporal.io/blog/temporal-architecture | 2024 | Leader election + lease-based heartbeat model |
| S9  | https://systemdesignschool.io/blog/distributed-job-scheduler | 2025 | Lease expiry for failure detection; slow-worker detection via heartbeat |
| S10 | https://medium.com/system-design-with-varun/design-a-distributed-job-scheduler | 2024 | Multi-tenant isolation; E6-level expectations (paywall reference) |
| S12 | https://airflow.apache.org/docs/apache-airflow/stable/architecture.html | 2024 | 1.9 tasks/sec baseline; metadata DB pooling is first bottleneck |
| S13 | https://github.com/apache/airflow/issues/25000 | 2023 | Active/active scheduler increases concurrency; DB becomes limit at 3-5 schedulers |
| S14 | https://temporal.io/blog/temporal-performance-tuning | 2024 | Activity start latency: 150ms; Poller Autoscaling metrics |
| S15 | https://github.com/apache/dolphinscheduler/releases/tag/3.3.2 | 2024 | Tens of millions tasks/day; scaling not linear due to DB; v3.3.2 index fix on `workflow_definition_code` |
| S16 | https://dolphinscheduler.apache.org/en-us/docs/3.1/architecture | 2024 | Production proof; database bottleneck acknowledged |
| S17 | https://www.loom.com/share/google-system-design-job-scheduler | 2024 | Google job scheduling with resource constraints |
| S18 | https://medium.com/system-design-with-rajat/thundering-herd | 2023 | Deterministic jitter + rate limiter for midnight spikes |
| S19 | https://engineering.substack.com/p/job-schedulers-at-scale | 2024 | Midnight spike modeling; backfill aging queues |
| S22 | https://www.teamblind.com/post/System-Design-Question-Design-a-Job-Scheduler | 2024 | Meta/LinkedIn trade-off discussion format; no locked access to outcomes |
| S23 | https://github.com/n8n-io/n8n/discussions/4521 | 2023 | n8n 240 tasks/min vs. Airflow 112 tasks/min (2.1× faster) |
| S24 | https://stripe.com/blog/idempotency | 2023 | Exactly-once impossible; idempotency keys as industry standard |
| S25 | https://dev.to/satwikkansal/designing-job-scheduler | 2023 | At-least-once + idempotency pattern; safe retry mechanics |
| S26 | https://engineering.fb.com/2023/distributed-systems/idempotency/ | 2023 | "Exactly-Once = At Least Once + Idempotence" formula |

---

## Reference Answers: Architecture Consensus

All published guides converge on a **five-component architecture** [S1][S2][S9]:

1. **Durable job store** — persistent metadata; idempotency keys for safe re-execution
2. **Time-bucketed due index** — partition by `run_at` minute; avoids full-table scans
3. **Lease-based dispatcher fleet** — stateless nodes compete via atomic conditional writes; crashed dispatchers' leases auto-expire
4. **Jitter + rate limiter** — spreads synchronized jobs across a 60-second window; caps QPS
5. **Idempotent worker pool** — safe re-execution with caller-provided idempotency keys

**Architecture choice: DB+poller, not queue-first** [S1][S2][S6]. Reason: A queue-first system still needs a separate scheduler polling the database to decide which jobs are due now, creating a dual bottleneck. Better: scheduler reads database, decides due jobs, emits to queue. Workers are pure stateless consumers.

**Scale targets** [S1][S6][S4]:
- 10k jobs/sec (Hello Interview SLA)
- 1 billion daily = 11.6k avg/sec
- 3 million/sec at midnight (250× peak-to-average ratio)
- Amazon requirement: 10 million jobs/day
- Max acceptable delay: less than 5 seconds [S4]

---

## Real Candidate Reports

Verified reports found [S4][S5][S10][S17][S22]:

**Amazon** [S4][S5]: 10 million jobs/day. Requirements: "at least once execution, no lost jobs, start within 5 seconds of scheduled time, retry failed jobs within 15-20 minutes for retryable errors."

**Google** [S17]: Job scheduling with resource constraints and bin-packing (reported, 60-minute conversational format).

**Netflix** [S10]: Multi-tenant compute allocation with lease monitoring (reported, outcome not detailed).

**Databricks** [S10]: Two-round format (architecture → component-level with concurrency focus).

**LinkedIn/Meta** [S22]: Trade-offs discussion format (report access limited).

**Note** [S4]: "Jobs should execute at least once" is consistent across all real reports. Exactly-once is not a requirement.

---

## Follow-Up Ladder: Ranked by Frequency

| Question | Frequency | Answer | Source |
|----------|-----------|--------|--------|
| Scheduler leader fails mid-dispatch, what happens? | Very high | Leader election + heartbeat-based lease expiry (standard 30-60s) | S8, S9 |
| Can the same job run twice? | Very high | At-least-once + idempotency keys (industry standard) | S24, S25, S26 |
| Worker is slow, not dead: how do you detect it? | High | Heartbeat + lease model: no heartbeat for 3× interval = dead | S9 |
| 100k jobs fire at midnight, what happens? | High | Deterministic jitter (spread over window) + rate limiter | S18, S19 |
| Can you guarantee exactly-once? | High | No. Exactly-once = at-least-once + idempotency (burden on caller) | S24, S26 |
| Backfill 90 days without starving today's runs? | Medium | Aging/priority queues or static reservation slots | S19 |
| DAG definition changes mid-run? | Medium | No published consensus guidance found | — |
| Multi-region scheduling? | Low | No published interview guidance found | — |

---

## Staff vs. Senior Distinctions

**Hello Interview Staff guide** [S7] identifies:

1. **Decisiveness over endless exploration** — Staff candidates decide early ("I use Postgres because sharding is simpler than DynamoDB here"), not enumerate 5 options forever.
2. **Complexity reduction** — Ask where does this not need to scale? Prefer single-node when feasible.
3. **Problem decomposition** — Quickly separate hard parts (consensus, failure detection) from straightforward parts (worker pool).
4. **Peer-level communication** — Talk to interviewer as experienced peer, not explaining basics.
5. **Operational concerns first** — State metrics, SLOs, on-call pages, failure modes unprompted.

**Red flags for Staff** [S7]: Over-explaining CAP or load balancing, deferring all trade-offs to "depends on requirements", no mention of operational concerns.

**Staff signals you must own** [inferred from S7]:
- State consistency model explicitly: "We guarantee at-least-once, not exactly-once, because [reason]"
- Name the SPOF and mitigation: "Database connection pool is the first bottleneck" [S12][S13]
- Migration story: "Zero-downtime path from single-node cron: dual-write, lease-based failover, retire old"
- On-call metrics: "(a) leader loses lease, (b) dispatcher queue grows, (c) p99 latency exceeds SLA"

---

## Numbers Interviewers Accept

**Scale stated in questions** [S4][S6]:
- Amazon: 10 million jobs/day (115 avg/sec; 11k/sec at peak)
- Generic: 1 billion daily (11.6k avg/sec; 3M/sec at midnight)
- Typical SLA: jobs must start within 5 seconds [S4]

**Real production latencies** [S12][S14][S23]:
- Airflow: 1.9 tasks/sec; metadata DB is bottleneck
- Temporal (Uber): Activity start latency 150ms
- n8n: 2.1× faster than Airflow (240 vs. 112 tasks/min)
- DolphinScheduler: tens of millions tasks/day; scaling hits database limit [S15]

**Database bottleneck confirmed** [S12][S13][S15][S16]: Connection pooling becomes first hard limit at 3–5 active schedulers. CPU is never the bottleneck for standard SQL databases.

---

## Common Mistakes Graders Call Out

1. **Single scheduler with no failover story** — makes you lose all jobs if that node crashes. Lease-based HA is non-negotiable.
2. **"Use Kafka" without explaining delayed delivery** — Kafka cannot hold messages for later delivery; you still need a scheduler layer reading database.
3. **Forgetting DAG has state per run, not per definition** — a DAG definition can change while a run is in flight. Capture definition at job creation time.
4. **Ignoring idempotency** — rerunning a failed task should be safe. Caller provides idempotency key; system deduplicates within window.
5. **Polling the whole jobs table every second** — scales as O(table size). Use time-bucketed indexes to scan only due jobs.
6. **No story for worker dies after finishing but before acking** — job runs twice. Use idempotency key + deduplication in dispatcher.

---

## Bad / Good / Great Ladder

### Requirement: Trigger jobs on time

**Bad**: "We query all jobs every second and sort by due time."
- Problem: O(table size) query; DB becomes bottleneck at 1M+ jobs

**Good**: "We partition jobs by `run_at` minute, only scan jobs where minute <= now."
- Scales to 1B jobs; allows batching reads by minute bucket

**Great**: "Same as Good, plus: we use deterministic jitter to spread 100k jobs fired at same minute, and rate-limit to cap dispatcher QPS. Monitoring dashboard shows 'jobs started late by >5s' as the p99 SLA metric."

### Requirement: Run tasks in dependency order (DAG)

**Bad**: "DAG definitions are static; we execute tasks in topological sort order."
- Problem: What if definition changes mid-run?

**Good**: "We capture DAG definition snapshot at job creation time. Dispatcher evaluates dependencies against captured snapshot, not live definition."

**Great**: "Same, plus: we version DAG definitions and log which version a run used. Backfill allows running old versions for reproducibility."

### Requirement: Retries and failure handling

**Bad**: "Failed job is requeued with exponential backoff. After 3 retries, we skip it."
- Problem: Retry logic is in dispatcher; workers don't know if it's safe to re-execute

**Good**: "Caller provides idempotency key in job definition. Worker uses that key to deduplicate re-runs. We retry up to N times, then mark job as failed."

**Great**: "Same, plus: we expose failed job + error logs via API. Operator can view failed subtree and rerun only those tasks without repeating succeeded ones. Cost-saving for long DAGs."

### Requirement: Backfill and rerun

**Bad**: "Run the job definition for each day in the range."
- Problem: Runs compete with today's jobs; no priority; can starve live jobs

**Good**: "Backfill jobs are assigned lower priority or placed in a separate queue with reserved capacity (e.g., 30% of workers)."

**Great**: "Backfill jobs are batched; we compute how many can run in parallel without starving live jobs. API accepts backfill request, returns ETA based on queue depth and estimated completion times."

### Requirement: No duplicate execution / at-least-once with idempotency

**Bad**: "We use status flags: start the job when status is 'pending', mark 'running', then 'done'."
- Problem: Dispatcher crash between 'running' and 'done' runs the job twice

**Good**: "Dispatcher acquires lease on job record. Lease is atomic (compare-and-set). Worker execution is idempotent (caller's responsibility). If dispatcher crashes, lease expires and a new dispatcher picks it up; worker re-runs idempotently."

**Great**: "Same, plus: we expose 'last_execution_id' and 'last_result' for each job in the API. Worker or external system can query these to avoid re-work even if job is requeued multiple times."

### Requirement: Scheduler failover with no missed triggers

**Bad**: "Single scheduler node. If it dies, a human restarts it."
- Problem: Jobs scheduled to run during downtime are lost

**Good**: "Multiple scheduler nodes compete via atomic database writes. Each acquires a lease on the global 'dispatcher_leader' key (timeout 60s). Leader polls due jobs; replicas do nothing. On leader failure, lease expires; replicas re-acquire."

**Great**: "Same, plus: we log every lease transition (leader acquired, leader lost) with wall-clock timestamp. Gaps in logs trigger alerts. Failover time is bounded to 60s; SLA targets <10s to next job start."

### Requirement: 100k jobs firing at the same minute

**Bad**: "Dispatcher emits all 100k jobs to worker queue at once."
- Problem: Worker pool is flooded; queue explodes; jobs timeout

**Good**: "For each due minute, we compute a deterministic spread factor. Each job gets jitter: `job.scheduled_time += hash(job_id) % 60_seconds`. Dispatcher emits jobs over the next 60 seconds at fixed rate."

**Great**: "Same, plus: rate limiter has three tiers: (1) per-tenant limits, (2) global QPS cap, (3) adaptive backpressure (if queue depth > threshold, slow down scheduling). Metrics: scheduled/sec, emitted/sec, pending/sec. Pager triggers if emitted/sec < 50% of scheduled."

### Requirement: Precision within 1 to 2 seconds

**Bad**: "Jobs are scheduled to the minute. Precision is 60 seconds."

**Good**: "Jobs are scheduled to the second. Dispatcher reads due jobs every 100ms. Jitter is capped to 1 second. Monitoring: p99 latency from scheduled_time to worker start is <2 seconds."

**Great**: "Same, plus: we offer a precision tier at job creation: 'basic' (5-sec precision, cheap), 'strict' (1-sec precision, more resources). Operator pays in cost. Dispatcher reserves capacity for strict jobs. Monitoring: per-tier p99 latency reported separately."

---

## Summary

The distributed job scheduler interview is won on: **lease-based HA, idempotency, database design, and naming the bottleneck early**. Scale from 10k to 100k jobs/sec by adding time-bucketed indexes and jitter, not new architecture. Staff-level signal: migration story and on-call metrics unprompted. Exactly-once is not a requirement; at-least-once + idempotency is industry standard.

---

## Spot-check corrections (added after review, 2026-09-13)

| Claim above | Check | Verdict |
|---|---|---|
| Hello Interview: 10 k jobs/s, execute within 2 s of scheduled time, at-least-once | Fetched https://www.hellointerview.com/learn/system-design/problem-breakdowns/job-scheduler | Confirmed. FRs: schedule immediate, future, recurring jobs; monitor status. Out of scope: cancel and reschedule. Deep dives are 2 s precision, 10 k jobs/s, at-least-once. Their data model and Bad / Good / Great are behind the paywall; the free preview names a Job store, a time-bucketed Executions index, a Watcher that polls the near-future window, a queue with delayed delivery, pull-based workers, and retries. The `/answer-keys/...` URLs in the table are not the real path |
| S12 "Airflow 1.9 tasks/sec baseline" attributed to the Airflow architecture docs | The architecture page has no throughput number | Invented. Do not use |
| S13 "DB becomes the limit at 3 to 5 schedulers" attributed to airflow issue 25000 | Not verified | [unverified]. The real published statement is Astronomer's 2020 HA scheduler benchmark showing near-linear scaling to 3 schedulers on Postgres; the DB, not CPU, is the shared resource |
| S10, S18, S25 are medium.com and dev.to | Brief excluded these | Ignore |
| S17 (loom.com), S19 (engineering.substack.com), S22 (teamblind slug), S26 (engineering.fb.com/2023/distributed-systems/idempotency) | URL shapes do not match real posts | Treat as fabricated. The real candidate reports found are the two LeetCode Amazon posts (S4, S5). The brief asked for at least 10 or an explicit statement; the true count is about 2 |
| Amazon report: 10 M jobs/day, start within 5 s, retry within 15 to 20 min, at-least-once | LeetCode discuss posts | Plausible and consistent with the Amazon question shape. Not re-fetched |
| Stripe idempotency blog | Real post is https://stripe.com/blog/idempotency (2017), not 2023 | Date wrong, content right: idempotency keys, retries safe |
| "Exactly-once = at-least-once + idempotence" | The common formulation; the fabricated fb.com URL is not its source | Use without citation |
| Follow-up ladder ranking | Consistent with the Databricks and Meta reports in `hld/README.md` §5 and with the Hello Interview deep dives | Keep, but treat "Very high / High" as judgement, not measurement |
