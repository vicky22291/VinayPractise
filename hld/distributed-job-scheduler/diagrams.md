# Diagrams: distributed job scheduler with DAG dependencies

The full D1 to D12 set from `hld/CLAUDE.md` §4. [`solution.md`](solution.md) embeds the most important ones once and links here for the rest. A diagram that lives in `solution.md` is linked, not pasted twice. Colors per root `CLAUDE.md` §3. Red is used for exactly one thing: the metadata store write path during the aligned top-of-hour spike, and the single-owner orchestrator shard that a wide fan-in lands on.

Design recap: trigger plane (partitioned timing wheels, one leased owner per partition) creates runs. Orchestration plane (one owner per run) appends task events and computes ready tasks. Execution plane (matching service per pool, stateless workers) runs attempts under heartbeat leases. Metadata store is sharded by `run_id`. etcd holds partition and shard ownership with epochs.

---

## D1. Context (zoom-out)

```mermaid
%% D1: the scheduler as one box, every external actor, and what flows on each edge
flowchart LR
    U[Users<br/>UI, CLI, API] -->|"define job, trigger, backfill, view"| S[Job scheduler]
    CI[CI/CD pipelines] -->|"deploy DAG version"| S
    EV[Event sources<br/>dataset updated, upstream job] -->|"trigger event"| S
    S -->|"run task attempt<br/>image, args, idempotency key"| W[Compute substrate<br/>Kubernetes, clusters]
    W -->|"heartbeat, exit code, output ref"| S
    W -->|"task logs, artifacts"| OS[(Object storage)]
    S -->|"failure, SLA miss"| AL[Alerting<br/>pager, chat]
    S -->|"run finished event"| DS[Downstream consumers<br/>catalog, lineage, billing]
    IDP[Identity provider] -->|"who may run what"| S

    class U,CI client
    class S service
    class OS store
    class W,EV,AL,DS,IDP external

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

## D2. Data flow (DFD)

```mermaid
%% D2: inputs to outputs with data name, size and rate. Peak is the top of the hour at midnight.
flowchart LR
    JD[/"DAG definition<br/>JSON ~5 KB, ~10 k changes/day"/] -->|"validate, version"| JS[(job + dag_version<br/>1 M jobs, 5 GB)]
    JS -->|"next_fire_at per job<br/>16 B, loaded per partition"| TW(Timing wheel<br/>per partition)
    TW -->|"fire (job_id, scheduled_time)<br/>64 B, 2.4 k/s avg, 900 k in the midnight second"| RS[(run + task_instance<br/>300 B + 10 x 400 B per run)]
    RS -->|"ready task<br/>~200 B, 2.3 k/s avg, 100 k/s peak"| MS(Matching service<br/>per pool)
    MS -->|"attempt lease<br/>attempt_id, key, ttl 60 s"| WK(Worker)
    WK -->|"heartbeat ~100 B every 10 s<br/>200 k running, so 20 k/s"| RS
    WK -->|"logs ~100 KB per task<br/>20 TB/day"| OS[(Object storage)]
    WK -->|"completion (attempt_id, exit, output ref)<br/>300 B, 2.3 k/s avg"| RS
    RS -->|"run_event append<br/>200 B x 5 per task, 200 GB/day"| EL[(run_event log)]
    RS -->|"CDC (change data capture)<br/>eventual, seconds"| RM[(Read model<br/>UI, search, metrics)]

    class JD client
    class TW,MS,WK service
    class JS,RS,EL,OS,RM store

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
```

## D3. Component architecture

Embedded in [`solution.md` §6](solution.md#6-final-design). Not repeated here.

## D4. Sequence, happy path, one per FR

- D4a cron trigger creates a run: [`solution.md` §4.1](solution.md#41-trigger-runs-on-time-on-demand-or-on-an-event).
- D4b task completes, downstream becomes ready, worker picks it up: [`solution.md` §4.2](solution.md#42-execute-tasks-in-dependency-order).
- D4c retry after failure, run ends failed, alert: [`solution.md` §4.3](solution.md#43-retries-timeouts-cancellation-and-alerts).
- D4d backfill and repair run: [`solution.md` §4.4](solution.md#44-backfill-a-date-range-and-rerun-a-failed-subtree).
- D4e event trigger (upstream job success), below.

```mermaid
%% D4e: event trigger. An upstream run finishing creates a downstream run through the same idempotent path as cron.
sequenceDiagram
    autonumber
    participant OU as Orchestrator (upstream run)
    participant K as Event bus
    participant TR as Trigger service (owner of job D partition)
    participant DB as Metadata store
    participant OD as Orchestrator (downstream run)
    OU->>DB: append RunSucceeded(run_u)
    OU->>K: publish JobRunSucceeded(job_u, run_u, logical_date)
    K-->>TR: consume (partition of subscribing job D)
    TR->>DB: INSERT run(job_d, scheduled_time=logical_date, trigger=event, cause=run_u) ON CONFLICT DO NOTHING
    DB-->>TR: 1 row (or 0 if this event was already processed)
    TR->>K: commit consumer offset
    DB-->>OD: new run assigned to shard hash(run_id)
    OD->>DB: materialize task_instances, roots to QUEUED
```

## D5. Sequence, failure paths

- D5a worker finishes the task, then dies before reporting: [`solution.md` §5.1](solution.md#51-how-do-we-guarantee-a-task-is-never-counted-as-done-twice-and-what-happens-when-a-worker-dies-after-finishing).
- D5b trigger owner dies at 08:59:59: [`solution.md` §5.2](solution.md#52-the-scheduler-node-dies-at-085959-do-the-0900-jobs-fire).
- D5c slow worker is declared dead, then reports late, below.
- D5d duplicate cron fire during ownership handover, below.

```mermaid
%% D5c: worker is slow, not dead. Its lease expires, a second attempt starts, then the first one reports. Fencing on attempt_id decides.
sequenceDiagram
    autonumber
    participant W1 as Worker 1 (attempt 1)
    participant O as Orchestrator (run owner)
    participant DB as Metadata store
    participant W2 as Worker 2 (attempt 2)
    W1->>O: heartbeat(attempt 1) ... then silence (GC pause, network)
    Note over O: lease_expires_at passed, grace 2 x heartbeat
    O->>DB: attempt 1 to LOST, create attempt 2 (same idempotency key)
    O->>W2: dispatch attempt 2
    W2->>W2: task runs again, idempotent on (run_id, task_id)
    W1->>O: complete(attempt 1, success)
    O->>DB: UPDATE task_instance SET state=SUCCESS WHERE current_attempt = 1
    DB-->>O: 0 rows, current_attempt is 2
    O-->>W1: 409 stale attempt, stop and clean up
    W2->>O: complete(attempt 2, success)
    O->>DB: UPDATE ... WHERE current_attempt = 2, append TaskSucceeded
    DB-->>O: 1 row
```

```mermaid
%% D5d: two trigger nodes briefly both believe they own partition 17. The unique key on run makes the second fire a no-op, and the epoch check stops the old owner from advancing the cursor.
sequenceDiagram
    autonumber
    participant Old as Trigger node A (epoch 41, lease expired but unaware)
    participant New as Trigger node B (epoch 42)
    participant DB as Metadata store
    New->>DB: load partition 17 where next_fire_at < now + 5 min
    New->>DB: INSERT run(job 9, 09:00) ON CONFLICT DO NOTHING, UPDATE job SET next_fire_at=10:00 WHERE owner_epoch <= 42
    DB-->>New: 1 run created
    Old->>DB: INSERT run(job 9, 09:00) ON CONFLICT DO NOTHING
    DB-->>Old: 0 rows
    Old->>DB: UPDATE job SET next_fire_at=10:00 WHERE partition=17 AND owner_epoch = 41
    DB-->>Old: 0 rows, epoch is 42
    Note over Old: sees stale epoch, drops partition, re-reads assignment
```

## D6. Activity / decision flow

```mermaid
%% D6: what the orchestrator does when an attempt reaches a terminal or lost state. This is the retry, zombie and trigger-rule logic in one tree.
flowchart TD
    A[Attempt event arrives<br/>success, failed, timeout, lost] --> B{attempt_id ==<br/>current attempt?}
    B -->|no| Z[Reject as stale<br/>tell worker to stop]
    B -->|yes| C{outcome}
    C -->|success| S[task SUCCESS<br/>append event]
    C -->|failed or timeout| D{retryable and<br/>attempts < max?}
    C -->|lost| E{task mode}
    E -->|at-least-once| D
    E -->|at-most-once| U[task UNKNOWN<br/>page owner, no auto retry]
    D -->|yes| R["schedule attempt n+1<br/>backoff = min(cap, base x 2^n) + jitter"]
    D -->|no| F[task FAILED<br/>append event, alert]
    S --> G[for each downstream:<br/>apply trigger rule]
    F --> G
    U --> G
    G --> H{rule satisfied?}
    H -->|all_success and all upstream done| Q[downstream QUEUED]
    H -->|upstream failed and rule all_success| K[downstream UPSTREAM_FAILED]
    H -->|not yet| W[wait]
    Q --> RUN{all tasks<br/>terminal?}
    K --> RUN
    RUN -->|yes| FIN[run SUCCESS or FAILED<br/>publish event, alert]

    class A service
    class B,C,D,E,H,RUN decision
    class S,F,U,R,Q,K,W,FIN,Z service

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

## D7. Entity relationship

Embedded in [`solution.md` §3.3](solution.md#33-data-model). Not repeated here.

## D8. State machines

```mermaid
%% D8a: run lifecycle. A run is created by the trigger plane and owned by one orchestrator shard until terminal.
stateDiagram-v2
    [*] --> CREATED: trigger fires, row inserted
    CREATED --> QUEUED: orchestrator claims run, materializes tasks
    QUEUED --> RUNNING: first task attempt starts
    RUNNING --> SUCCESS: all tasks SUCCESS or SKIPPED
    RUNNING --> FAILED: any task FAILED or UPSTREAM_FAILED, no more retries
    RUNNING --> CANCELLED: user cancel, all attempts told to stop
    FAILED --> RUNNING: repair run, failed subtree cleared, same run_id
    SUCCESS --> [*]
    FAILED --> [*]
    CANCELLED --> [*]
```

```mermaid
%% D8b: task instance lifecycle. Attempt-level states roll up into the task instance. LOST is the zombie case.
stateDiagram-v2
    [*] --> NONE: run materialized
    NONE --> QUEUED: trigger rule satisfied
    NONE --> UPSTREAM_FAILED: rule cannot be satisfied
    NONE --> SKIPPED: branch not taken
    QUEUED --> RUNNING: worker leases attempt n
    RUNNING --> SUCCESS: complete(attempt n, ok)
    RUNNING --> UP_FOR_RETRY: complete(attempt n, error) and n < max
    RUNNING --> LOST: lease expired, no heartbeat
    LOST --> UP_FOR_RETRY: at-least-once mode
    LOST --> UNKNOWN: at-most-once mode, human decides
    UP_FOR_RETRY --> QUEUED: backoff elapsed
    RUNNING --> FAILED: error and n == max, or timeout with no retries
    RUNNING --> CANCELLED: run cancelled
    FAILED --> QUEUED: repair run clears it
    SUCCESS --> [*]
    FAILED --> [*]
    UPSTREAM_FAILED --> [*]
    SKIPPED --> [*]
    CANCELLED --> [*]
```

## D9. Deployment / topology

```mermaid
%% D9: one region, three AZs. Stateless planes spread across AZs. Metadata shards are Postgres primaries with a sync replica in another AZ. etcd is a 5-node cluster across AZs.
flowchart TD
    subgraph AZ1
        T1[Trigger nodes x4<br/>partitions 0 to 85]
        O1[Orchestrator nodes x10<br/>run shards 0 to 21]
        M1[Matching nodes x4]
        W1[Workers x2000]
        P1[(Postgres shard primaries<br/>0 to 21, sync replica in AZ2)]
        E1[etcd x2]
    end
    subgraph AZ2
        T2[Trigger nodes x4<br/>partitions 86 to 170]
        O2[Orchestrator nodes x10<br/>run shards 22 to 42]
        M2[Matching nodes x4]
        W2[Workers x2000]
        P2[(Postgres shard primaries<br/>22 to 42, sync replica in AZ3)]
        E2[etcd x2]
    end
    subgraph AZ3
        T3[Trigger nodes x4<br/>partitions 171 to 255]
        O3[Orchestrator nodes x10<br/>run shards 43 to 63]
        M3[Matching nodes x4]
        W3[Workers x2000]
        P3[(Postgres shard primaries<br/>43 to 63, sync replica in AZ1)]
        E3[etcd x1]
    end
    E1 <-->|"Raft"| E2
    E2 <-->|"Raft"| E3
    P1 -.->|"async replica, other region<br/>RPO ~1 s"| DR[(DR region)]

    class T1,T2,T3,O1,O2,O3,M1,M2,M3,W1,W2,W3 service
    class P1,P2,P3,E1,E2,E3,DR store

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
```

Notes:
- Partition and shard counts are fixed (256 trigger partitions, 64 run shards) and mapped onto whatever nodes are alive. Adding a node moves partitions, never re-hashes data.
- Workers are the only tier that autoscales with load. Everything else scales with job count.
- Cross-region: async replication of the metadata shards, RPO about 1 s. Promotion is manual. See [`solution.md` §10.11](solution.md#1011-evolution).

## D10. Scaling / partitioning

Embedded in [`solution.md` §5.3](solution.md#53-900-k-jobs-fire-at-midnight-what-breaks-first). Not repeated here.

## D11. Failure mode map

```mermaid
%% D11: each component, what fails, blast radius, mitigation. Red is the case with the widest blast radius.
flowchart TD
    T[Trigger node dies] -->|"its partitions stop firing"| T1[Blast: 1/256 of jobs per partition, up to 15 s late]
    T1 -->|"mitigation"| T2[etcd lease expires in 10 s, partitions reassigned, new owner reloads and fires overdue]
    O[Orchestrator node dies] -->|"its run shards stall"| O1[Blast: running tasks keep running, no new dispatch for those runs]
    O1 -->|"mitigation"| O2[shard reassigned, state rebuilt from DB, completions replayed from worker retries]
    M[Matching node dies] -->|"pool queue cache lost"| M1[Blast: dispatch latency up for seconds]
    M1 -->|"mitigation"| M2[stateless, rebuild from QUEUED rows on DB, workers reconnect]
    W[Worker dies mid-task] -->|"attempt lease expires"| W1[Blast: one task, retried after lease + grace]
    W1 -->|"mitigation"| W2[at-least-once retry with same idempotency key]
    D[Metadata shard primary down] -->|"1/64 of runs cannot progress"| D1[Blast: triggers and completions for those runs queue up]
    D1 -->|"mitigation"| D2[sync replica promoted in ~30 s, no acked write lost]
    E[etcd quorum lost] -->|"no new ownership changes"| E1[Blast: current owners continue on local lease timers, then stop]
    E1 -->|"mitigation"| E2[owners hold until TTL, then fail closed, operator freeze switch]
    S[Midnight spike] -->|"900 k runs in one second"| S1[Metadata write path saturates]
    S1 -->|"mitigation"| S2[jitter window, batched inserts, 64 shards, lazy task rows]

    class T,O,M,W,D,E,S service
    class T1,O1,M1,W1,D1,E1 decision
    class S1 critical
    class T2,O2,M2,W2,D2,E2,S2 service

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
```

## D12. Rollout / migration

Applicable. The realistic starting point is a fleet of cron boxes plus one single-scheduler Airflow. The migration moves the trigger plane first because a missed trigger is the visible failure, and keeps a rollback point per phase.

```mermaid
%% D12: migration from cron boxes plus a single-scheduler Airflow to the three-plane design. Each phase has a rollback.
gantt
    title Migration to the three-plane scheduler
    dateFormat  YYYY-MM-DD
    axisFormat  %b %d
    section Phase 1 shadow
    Import DAGs as versioned definitions, run trigger plane in shadow      :p1, 2026-10-01, 21d
    Compare fire times to legacy, fix cron and timezone diffs             :p1b, after p1, 14d
    section Phase 2 triggers
    Trigger plane authoritative for 5% of jobs, legacy disabled for them :p2, after p1b, 14d
    Ramp to 100% of jobs, rollback is re-enable legacy cron              :p2b, after p2, 21d
    section Phase 3 execution
    Orchestrator and matching take new runs, legacy drains in flight     :p3, after p2b, 21d
    Cutover per tenant, rollback is route tenant back to legacy executor :p3b, after p3, 28d
    section Phase 4 cleanup
    Backfill history into read model, decommission legacy                :p4, after p3b, 21d
```

Rollback points: after Phase 1 nothing changed for users. After Phase 2 re-enabling legacy cron for a job is one flag, and the `run` unique key prevents double fires while both are briefly active. After Phase 3 a tenant can be routed back to the legacy executor because run state lives in the metadata store either way.
