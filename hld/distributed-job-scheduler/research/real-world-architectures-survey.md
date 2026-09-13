# Distributed Job Scheduler Systems: Real-World Architectures Survey

## Sources Reference Table

| ID | URL | What It Establishes |
|----|-----|---------------------|
| [S1] | https://airflow.apache.org/docs/apache-airflow/stable/configurations-ref.html | Apache Airflow defaults: parallelism, max_active_runs, max_active_tasks |
| [S2] | https://medium.com/airbnb-engineering/airflow-a-workflow-management-platform-46318b977fd8 | Airbnb production scale: 30k+ concurrent tasks, several thousand DAGs |
| [S3] | https://www.astronomer.io/airflow/scalability/ | Astronomer Astro 500k sustained concurrent tasks, p95 228ms start latency |
| [S4] | https://sre.google/sre-book/distributed-periodic-scheduling/ | Google SRE book Ch.26: Paxos state, at-most-once semantics, thundering-herd |
| [S5] | https://docs.temporal.io/workflow-execution/limits | Temporal hard limits: 51.2k events, 50 MB history, 2k incomplete ops |
| [S6] | https://docs.temporal.io/self-hosted-guide/defaults | Temporal defaults: 10s workflow task timeout, 4 MB gRPC message limit |
| [S7] | https://github.com/uber-go/cadence-client/blob/master/internal/workflow.go | Cadence client defaults: workflow task timeout values |
| [S8] | https://github.com/Netflix/maestro | Netflix Maestro: hundreds of thousands workflows, millions jobs/day, open source June 2024 |
| [S9] | https://www.uber.com/blog/managing-data-workflows-at-scale/ | Uber Piper 2019: thousands pipelines/day, data ingestion use cases |
| [S10] | https://engineering.fb.com/core-data/introducing-fblearner-flow-facebook-s-ai-backbone/ | Meta FBLearner Flow: thousands experiments daily, three-tier abstraction |
| [S11] | https://github.com/argoproj/argo-workflows/issues/2247 | Argo Workflows: etcd scaling bottleneck on large fan-out |
| [S12] | https://docs.dagster.io/deployment/oss/oss-deployment-architecture | Dagster OSS deployment: run launchers, hybrid agent specs |
| [S13] | https://www.prefect.io/blog/a-platform-approach-to-workflow-orchestration | Prefect: orchestration server decoupled from execution |
| [S14] | https://docs.aws.amazon.com/step-functions/latest/dg/service-quotas.html | AWS Step Functions: 25k event limit (Standard), unlimited (Express), 1 year max |
| [S15] | https://docs.microsoft.com/answers/questions/328952/ | Azure Durable Functions: 10 min Consumption, 60 min Premium timeout |
| [S16] | https://www.quartz-scheduler.org/documentation/quartz-2.1.7/configuration/ConfigJobStoreTX.html | Quartz: 60s misfireThreshold default, SELECT...FOR UPDATE row locks |
| [S17] | https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/ | K8s CronJob: 100-miss skip rule, startingDeadlineSeconds, concurrencyPolicy |
| [S18] | https://docs.databricks.com/aws/en/resources/limits | Databricks: 2k concurrent runs, 750 parent tasks, 12k saved jobs/workspace |

---

## 1. Apache Airflow 2.x/3.x

**One-liner**: Distributed scheduler using SELECT...FOR UPDATE SKIP LOCKED on metadata DB for HA, multiple executors (Celery/K8s), task state machine with zombie detection via heartbeats.

**Architecture**: Multiple scheduler processes compete for DAG runs via advisory locks on the Airflow DB. DAG processor reads Python definitions asynchronously. Executors (Local, Celery, Kubernetes) dispatch task instances. Zombie detection runs every scheduler_zombie_task_threshold seconds [S1].

**Configuration Defaults** [S1]:
- `parallelism`: 32 (max concurrent task instances across all DAGs per scheduler)
- `max_active_runs_per_dag`: 16 (limit concurrent run instances per DAG)
- `max_active_tasks_per_dag`: 16 (limit concurrent task instances within one DAG run)
- `scheduler_heartbeat_sec`: [unverified] (~5-10s, not in official docs)
- `job_heartbeat_sec`: [unverified] (~5-10s for worker heartbeats, not in official docs)
- `dag_dir_list_interval`: [unverified] (interval to scan DAG directory)
- `min_file_process_interval`: [unverified] (minimum age before re-parsing DAG file)
- Airflow 3.x introduces Task Execution API for remote task runners, decoupling executor from scheduler

**Published Scale**:
- Airbnb (2018): Several thousand DAGs, 30,000+ concurrent task instances [S2]
- Astronomer Astro: 500,000 sustained concurrent task instances (25x open-source baseline), p95 task start latency 228ms at 100k concurrent tasks [S3]

**State Machine**: task_instance.state transitions (scheduled → queued → running → success/failed). Catchup runs historical instances for gaps. Pools enforce resource quotas. Priority_weight and SLAs reorder execution.

---

## 2. Google Distributed Cron (SRE Book)

**One-liner**: Paxos-replicated state machine for cron database, leader-based job launch, at-most-once semantics to prevent double-firing.

**Architecture** [S4]: Small replicated state (job definitions, next run times) stored via Paxos quorum. Single leader elected from replica set. Leader health-checked every few seconds. Replacement leader elected within minutes. Before launching a job, leader synchronously replicates state change to quorum.

**Key Details** [S4]:
- Delivery model: At-most-once (prefer one launch or none over duplicate launches). Not at-least-once like Airflow.
- Thundering-herd mitigation: Hash crontab entry into time range (e.g., hour 0-23), jitter launch within window to avoid synchronized spike
- Failover: Health checker discovers leader loss within seconds. Replica becomes new leader within minutes via Paxos election.
- State: Job definitions, schedule, last run time. Minimal to fit in replicated log (unlike Airflow's large DAG metadata DB).

---

## 3. Temporal (Uber Cadence Successor)

**One-liner**: Event-sourced workflow history (append-only log per workflow), matching service with consistent hashing for task queue dispatch, sticky execution pins workers to workflow state.

**Architecture**: History service stores workflow events (append-only). Matching service maintains task queues per worker type, dispatches via consistent hashing (workers with same state = sticky execution). Continue-as-new pattern restarts workflow with fresh history. Activity heartbeats signal progress. Workflow task timeout (default 10s [S6, S7]) limits decision logic.

**Hard Limits** [S5, S6]:
- History size: 51,200 events OR 50 MB maximum per workflow execution
- History warning threshold: 10,240 events OR 10 MB (trigger continue-as-new pattern)
- Max incomplete operations: 2,000 per operation type (activities, child workflows, signals)
- Max in-flight workflow updates: 10
- Workflow task timeout: 10s default, 60s maximum [S6, S7]
- Max identifier length: 1,000 characters
- gRPC message size: 4 MB per message [S6]

**Scale**: Default history shards [unverified], event-sourced design allows unlimited workflows at the system level (unlike step functions' 1-year limit). Replay-on-worker enables deterministic execution and recovery.

---

## 4. Netflix Maestro (June 2024 Open Source)

**One-liner**: Workflow-as-a-service with component separation (API, engine, DB, queue), multi-trigger support (time/event/manual), foreach and subworkflow patterns.

**Architecture** [S8]: Modular design decouples workflow definitions (DSL), server (REST API), execution engine (event-driven), database (metadata + run state), and task queue (SNS/SQS). Signals trigger workflows (event-based). Foreach loop generates parallel tasks. Subworkflows enable composition. Strict SLO during traffic spikes suggests queuing and rate limiting.

**Published Scale** [S8]:
- Hundreds of thousands of workflows in production
- Millions of jobs per day across Netflix
- Serves thousands of users (data scientists, ML engineers, software engineers, business analysts)

**Comparison to predecessor Meson**: [unverified] specific architectural details not published.

---

## 5. Uber Piper (2019)

**One-liner**: Centralized workflow manager with metadata separate from Python definitions, serialized workflow graph, supports data ingestion/modeling/feature engineering.

**Architecture** [S9]: Metadata decoupled from DAG Python code. Workflow/task properties serialized (JSON or proto). Dependency graph materialized in database. Leader election for scheduler HA [unverified - ZooKeeper?]. Based on Airflow with Uber-specific extensions.

**Published Scale** [S9]:
- Thousands of pipelines per day
- Use cases: data ingestion, modeling, feature engineering, dispersal

---

## 6. Meta FBLearner Flow

**One-liner**: Three-tier abstraction (Workflows → Operators → Channels) for experiment orchestration and model training pipelines.

**Architecture** [S10]: Workflows define pipelines. Operators are smallest execution units (data processing, ML training). Channels carry typed inputs/outputs between operators. Enables composition and reuse.

**Scale** [S10]:
- Thousands of experiments per day across Meta
- Users: data scientists, ML engineers, researchers

**Note**: Dataswarm component (mentioned in your brief) has [unverified] published architecture details. FBLearner Flow is the known public system.

---

## 7. Argo Workflows, Dagster, Prefect

**Argo Workflows**: DAG model with explicit task dependencies. Runs as Kubernetes native CRDs (workflow resource). Controller reconciles desired state. Performance bottleneck: etcd updates scale non-linearly on large fan-out loops (each task = one API call) [S11].

**Dagster** [S12]: Composable deployment architecture (storages, executors, run launchers). Run launchers abstract execution (DefaultRunLauncher for in-process, DockerRunLauncher for containers, K8sRunLauncher for Kubernetes). Hybrid agent baseline: 0.25 vCPU, 1 GB RAM.

**Prefect** [S13]: Orchestration server decoupled from execution (pure Python functions, not DAG DSL). Work pools abstract compute (Docker, K8s, serverless). Philosophy: "execution infrastructure is fungible."

---

## 8. AWS Step Functions, Azure Durable, Quartz, K8s CronJob

**AWS Step Functions** [S14]:
- Standard: 25,000 event history limit, 1 year max execution time, 40 parallel Map branches (inline), 10,000 (distributed)
- Express: Unlimited history, 5 minute max execution, for high-throughput event processing
- Task input/output: 256 KiB per state
- Execution history retention: 90 days in standard Step Functions, CloudWatch Logs for Express

**Azure Durable Functions** [S15]:
- Consumption Tier: 10 minute max timeout
- Premium Tier: 60 minute guaranteed SLA

**Quartz Scheduler** [S16]:
- `misfireThreshold`: 60,000 ms (60 seconds) default. Triggers missed before this are skipped.
- Row-level cluster locking via `SELECT * FROM LOCKS WHERE SCHED_NAME = ? AND LOCK_NAME = ? FOR UPDATE`
- Multiple scheduler nodes compete for same row, only lock holder executes

**Kubernetes CronJob** [S17]:
- `startingDeadlineSeconds`: no default (nil). If set, skips job if now - start_time > deadline.
- Missed schedules rule: >100 consecutive misses → skip the job (fail-safe for controller bugs)
- `concurrencyPolicy`: Allow (default, run in parallel), Forbid (skip if previous still running), Replace (kill previous, start new)

---

## 9. Databricks Workflows / Lakeflow Jobs

**One-liner**: Workspace-level orchestration with Delta Lake integration, data-aware triggers, unified data + AI platform.

**Architecture**: Workflows defined in Databricks UI or declarative JSON. Tasks map to notebooks or Delta Lake queries. Data-aware triggers activate on table schema/data changes. Integrated with MLflow for experiment tracking. Repair run restarts failed tasks without rerunning succeeded ones.

**Resource Limits** [S18]:
- Concurrent task runs per workspace: 2,000
- Concurrent parent tasks (Run job + For each): 750
- Saved jobs per workspace: 12,000
- Job creation rate: 10,000 per hour
- Uptime SLA: 99.95%

**Scale**: [unverified] exact published jobs-per-day. Databricks Jobs scheduler scales per workspace, not unified across all workspaces.

---

## Key Architecture Patterns Across All Systems

| Pattern | Used By | Benefit |
|---------|---------|---------|
| Paxos/raft consensus | Google cron | Leader failover without double-launches; no SPOF |
| SELECT...FOR UPDATE SKIP LOCKED | Airflow, Quartz | Distributed coordination via database locks; no external consensus needed |
| Event-sourced immutable history | Temporal, Cadence, Azure Durable | Replay workflows, detect duplicates, sticky execution, deterministic recovery |
| Consistent hashing + task queues | Temporal matching, Prefect work pools | Scalable work distribution; worker affinity; load balancing |
| Database row locks (cluster locking) | Quartz, Airflow | Simple HA for small state; avoids external consensus overhead |
| Kubernetes CRDs + controller loop | Argo, K8s CronJob | Cloud-native abstraction; automatic retry via reconciliation; no separate control plane |

---

## What This Means for the Interview Design

1. **Database as queue with SKIP LOCKED is standard HA pattern**. Airflow and Quartz both use advisory/row locks instead of dedicated queue (Kafka/RabbitMQ). Reduces external dependencies. Trade-off: database becomes hot under scale.

2. **Leases + heartbeats detect dead workers**. Every system uses heartbeat TTL (Airflow: job_heartbeat_sec, Temporal: activity heartbeat, K8s: kubelet health checks) rather than only exit codes. Heartbeat loss triggers zombie detection / worker restart.

3. **Event-sourced history enables deterministic replay**. Temporal and Azure Durable Functions store immutable event log, allowing workflow replay for idempotency detection and crash recovery without data duplication.

4. **Small replicated state wins over large replicated DB**. Google cron replicates only job definitions + run times via Paxos (kilobytes). Airflow replicates full metadata DB (megabytes), making it slower under leader failover.

5. **At-least-once + idempotent tasks is the safe default**. Airflow, Temporal, Databricks all assume idempotent task implementations and accept duplicate launches. Only Google cron chose at-most-once (higher complexity, lower throughput).

6. **DAG version pinning per run prevents surprises**. Airflow and Maestro serialize DAG definition per run. If DAG changes mid-stream, running instances stay on old version. Avoids unexpected task dependencies mid-flight.

7. **History limits force continue-as-new pattern**. Temporal's 51.2k event limit and AWS Step Functions' 25k event limit mean long-running workflows must explicitly restart (continue-as-new or Map.DistributedMap) rather than accumulate history forever.

8. **Scheduler HA splits into coordinator + executor**. Airflow (scheduler + executor), Temporal (history + matching), Databricks (coordinator + workers). Decoupling allows independent scaling and fault isolation.

9. **Priority and resource quotas prevent runaway DAGs**. All systems offer pools (Airflow), concurrency limits (Databricks), or SLAs. Without them, one bursty DAG starves others.

10. **Backfill and catchup are critical for data pipeline credibility**. Airflow's catchup, Maestro's repair run, Databricks' backfill all allow re-running historical date ranges. SQL databases and BI tools expect complete history; absence of backfill is a showstopper.

11. **Sticky execution or task queue affinity improves cache hit rate**. Temporal pins workflow history to one worker, Prefect's work pools colocate related tasks. Reduces network overhead and enables local state caching.

12. **Thundering-herd jitter is non-obvious but essential**. Google's hash-based cron jitter and Kubernetes' `startingDeadlineSeconds` both solve the same problem: 1000 jobs scheduled at midnight should not all launch at 00:00:00.

13. **Zombie detection timeout is a tuning knob for SLA vs cost**. Airflow's `scheduler_zombie_task_threshold` (default [unverified]) controls how long to wait for heartbeat before restarting. Longer threshold = lower cost (fewer false restarts) but higher p99 latency (stale worker recovery takes time).

14. **Failure modes: split-brain, stale leader, queue overflow**. Multi-scheduler systems (Airflow, Quartz, Databricks) risk both leaders running simultaneously if DB becomes unresponsive. Task queue overflow (Temporal matching service, Kafka) requires backpressure or circuit-breaker. History explosion requires pruning (Temporal continue-as-new, S3 archive).

15. **Provisioned concurrency (Databricks 2k concurrent runs, Astronomer 500k tasks) is measured in cost, not capability**. Design must accommodate bursts without breaking. Use queuing (Airflow pools, Prefect concurrency limits) to spread load over time if provisioning is limited.

16. **Leader election time directly impacts RTO (recovery time objective)**. Google cron re-elects within minutes. Kubernetes CronJob relies on kubelet failure detection (seconds to minutes). Design SLA accordingly: if 5-minute outage is unacceptable, require sub-minute detection + failover.

17. **Data-aware triggers (Databricks, some Maestro) are game-changer for dependent pipelines**. Instead of polling or cron schedules, activate downstream workflow when upstream table changes. Requires immutable event log or change data capture.

18. **Idempotency key (request ID, DAG run ID, task instance ID) is non-negotiable**. Distributed systems will duplicate; without idempotency key, duplicate execute twice. Every task output must include its idempotency key for deduplication.

19. **Operator matrix explosion is real**. Each combination of (DAG editor, scheduler, executor, database) creates new testing surface. Netflix and Uber both reached this complexity; answer should acknowledge ops cost, not just feature count.

20. **Choose between simplicity and scale**. Kubernetes CronJob is simple (5-minute setup, sufficient for <1000 jobs/day). Airflow adds ~50 operational components (Celery, Redis, Flower monitoring). Temporal adds event sourcing complexity. None is "best"; choose based on team size and SLA.

---

## Summary

Real-world distributed schedulers converge on a small number of architectural choices: database-backed coordination (Airflow, Quartz), event-sourced history (Temporal, Azure), or Kubernetes-native (Argo, CronJob). All use heartbeats for failure detection, assume idempotent tasks, and require explicit backfill support. Scale inflection points (Airflow's ~500k tasks, Databricks' 2k concurrent) are measured in cost, not capability.

---

## Spot-check corrections (added after review, 2026-09-13)

Checked against the primary source by fetching it. Use these values in `solution.md`, not the ones above where they differ.

| Claim above | Check | Corrected value and source |
|---|---|---|
| Airflow heartbeat defaults "[unverified]" | Fetched the configuration reference | `scheduler_heartbeat_sec` = 5, `job_heartbeat_sec` = 5, `task_instance_heartbeat_timeout` = 300 s (this is the renamed `scheduler_zombie_task_threshold`), `task_instance_heartbeat_timeout_detection_interval` = 10 s, `scheduler_idle_sleep_time` = 1 s, `max_tis_per_query` = 16, `use_row_level_locking` = True, `task_queued_timeout` = 600 s, `catchup_by_default` = False, `[dag_processor] min_file_process_interval` = 30 s, `[dag_processor] refresh_interval` = 5 s (replaces `dag_dir_list_interval`, default 300 s in 2.x), `[workers] max_failed_heartbeats` = 3, `min_heartbeat_interval` = 5 s, `parallelism` = 32, `max_active_runs_per_dag` = 16, `max_active_tasks_per_dag` = 16. https://airflow.apache.org/docs/apache-airflow/stable/configurations-ref.html |
| Google cron "at-most-once" | Confirmed wording | "we favor skipping launches rather than risking double launches, as much as the infrastructure allows." Leader loss detected "within seconds"; the chapter treats a one-minute failover as tolerable. Paxos state is the start and end of each launch, synchronously replicated to a quorum before launch. Logs on local disk on 3 replicas, snapshots to GFS. https://sre.google/sre-book/distributed-periodic-scheduling/ |
| Temporal limits | Confirmed | 51,200 events or 50 MB hard, 10,240 events or 10 MB warning, 2,000 pending per operation type. Workflow Task Timeout default 10 s, maximum 120 s (not 60 s). https://docs.temporal.io/workflow-execution/limits and https://docs.temporal.io/encyclopedia/detecting-workflow-failures |
| Databricks limits | Confirmed | 2,000 concurrent task runs per workspace (Run job and For each parents excluded), 750 concurrent parent tasks, 10,000 jobs created per hour, 12,000 saved jobs per workspace. The 99.95% SLA is not on that page; treat as [unverified]. https://docs.databricks.com/aws/en/resources/limits |
| Quartz misfireThreshold 60 s, K8s CronJob 100 missed schedules, Step Functions 25,000 events and 1 year | Consistent with my knowledge of the docs | Kept |
| Astronomer "500 k sustained concurrent tasks, p95 228 ms" and Airbnb "30 k+ concurrent tasks" | Not re-fetched | Treat as [unverified] vendor numbers. Do not quote in an interview |
| Line count | The agent reported 380 lines | File is 236 lines |
