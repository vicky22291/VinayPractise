# Concept: Temporal and Durable Execution

> One-liner: Temporal lets a multi-step process survive crashes and multi-day waits by recording every external result, timer, and incoming signal in a durable per-workflow **event history**, then re-running the orchestration code against that history (**replay**) so a fresh worker lands in exactly the state the dead one was in. The price: workflow code must be **deterministic**, and every activity must still be **idempotent**, because retries do not go away.

Depth target: high-level, same as [exactly-once.md](exactly-once.md) and [distributed-transactions.md](distributed-transactions.md). It is the answer (or the thing you are being asked to build) in #6 scheduler, #11 async provisioning, #25 booking, #29 payroll, #31 workflow engine, #32 integration platform, and the Uber / YouTube / flash-sale questions.

Source: Hello Interview's Temporal deep dive (https://www.hellointerview.com/learn/system-design/deep-dives/temporal), which builds the model from scratch. Limits and defaults from docs.temporal.io and the Go SDK source, listed in section 12.

---

## 1. Mental model

Split your process into two kinds of code. **Workflow** code decides what happens next and never touches the outside world. **Activity** code does one external thing and returns a result. Temporal writes every activity result, timer, and signal into an append-only history. If the worker dies, any other worker re-runs the workflow code from line one, and every call that already has a recorded result returns instantly from history instead of running again.

```mermaid
%% The whole idea on one page: history is the truth, workers are disposable
flowchart LR
    WF["Workflow code<br/>deterministic orchestration<br/>runs on any Worker"]
    T["Temporal Service<br/>event history + timers<br/>+ task queues"]
    ACT["Activity code<br/>one side effect each<br/>must be idempotent"]
    H[("Event history<br/>ChargeCustomerCompleted<br/>TimerStarted / TimerFired<br/>Signal: PackageDelivered")]
    EXT["Stripe / inventory DB<br/>shipping API / email"]
    W2["New Worker<br/>after a crash"]

    WF -->|"schedule activity"| T
    T -->|"activity task"| ACT
    ACT -->|"call once"| EXT
    ACT -->|"result"| T
    T -->|"append event"| H
    H -->|"replay: same code,<br/>recorded results"| W2
    W2 -.->|"continues where<br/>the dead worker stopped"| WF

    class WF,ACT,W2 service
    class T queue
    class H store
    class EXT external
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

- **Durable execution**: the program's progress is stored outside the process running it. Kill the process and the program has not lost its place.
- **Replay** is the recovery mechanism. **Determinism** is what makes replay safe. **Timers** and **signals** are how a workflow waits for days without holding a process.
- Temporal never runs your code. Your **Workers** poll it for tasks. Temporal only stores state and hands out work.

**Why this matters at Staff level.** A Senior answer says "use Temporal for the order saga". A Staff answer says what Temporal stores per step, why the code has to be deterministic, where retries still create duplicates, what the history cap does to a million-step workflow, and what breaks first when the cluster is overloaded. Also: when the interviewer wants you to design the workflow engine itself, "use Temporal" solves the interview in one box and scores zero.

---

## 2. The problem: one function, five days, one crash

The article starts from the e-commerce order flow everyone wishes they could write as straight-line code.

```
function processOrder(order):
    chargeCustomer(order)        // Stripe
    reserveInventory(order)      // our DB
    requestShipment(order)       // carrier API
    while not isDelivered(order):
        sleep(5 days)
    sendReviewEmail(order)
```

Two things make this impossible as plain code.

```mermaid
%% Why straight-line code fails: a five-day wait and a crash after an irreversible side effect
flowchart LR
    S1["chargeCustomer"]
    S2["reserveInventory"]
    S3["requestShipment"]
    S4["wait until delivered<br/>days, sometimes weeks"]
    S5["sendReviewEmail"]
    STRIPE["Stripe"]
    CRASH["Server crashes here<br/>charge succeeded,<br/>nothing recorded"]
    RETRY["Next server reruns<br/>from the top"]
    DOUBLE["Customer charged twice"]
    HOLD["A process held open<br/>for 5 days per order<br/>x millions of orders"]

    S1 -->|"charge"| STRIPE
    S1 --> S2 --> S3 --> S4 --> S5
    S1 -.-> CRASH --> RETRY --> DOUBLE
    S4 -.-> HOLD

    class S1,S2,S3,S5 service
    class S4 decision
    class STRIPE external
    class CRASH,DOUBLE critical
    class RETRY service
    class HOLD critical
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
```

- **Partial failure.** Stripe charged the card, the server died before writing that down. The replacement server cannot tell "not charged" from "charged, not recorded".
- **Long waits.** Nobody keeps a process alive for five days. You end up persisting "which step am I on" and building a scheduler to resume. That is a hand-rolled workflow engine, and it is what Temporal replaces.

---

## 3. Build it yourself in four steps

The fastest way to understand Temporal is to build the minimum framework that fixes section 2, one problem at a time. Each step adds one Temporal concept.

### 3.1 Record every result, replay after a crash

Route every external call through the framework. When the call finishes, write `<step>Completed {result}` to durable storage before doing anything else. After a crash, run the function again from the top. Each call first checks history: recorded result exists, return it without calling out. No record, run it for real and record it.

```mermaid
%% Replay: Worker B reruns the same function, history answers the first two calls, only the third one executes
sequenceDiagram
    participant A as Worker A
    participant F as Framework
    participant H as Durable history
    participant X as Stripe / Inventory / Carrier
    participant B as Worker B

    A->>F: chargeCustomer(order)
    F->>X: POST /charge
    X-->>F: paymentId_123
    F->>H: append ChargeCustomerCompleted {paymentId_123}
    F-->>A: paymentId_123
    A->>F: reserveInventory(order)
    F->>X: reserve
    X-->>F: reservationId_456
    F->>H: append ReserveInventoryCompleted {reservationId_456}
    F-->>A: reservationId_456
    Note over A: crash before requestShipment
    B->>F: chargeCustomer(order)
    F->>H: any ChargeCustomerCompleted?
    H-->>F: yes, paymentId_123
    F-->>B: paymentId_123 (Stripe not called)
    B->>F: reserveInventory(order)
    F->>H: any ReserveInventoryCompleted?
    H-->>F: yes, reservationId_456
    F-->>B: reservationId_456 (no second reservation)
    B->>F: requestShipment(order)
    F->>H: any RequestShipmentCompleted?
    H-->>F: no
    F->>X: create shipment
    X-->>F: shipmentId_789
    F->>H: append RequestShipmentCompleted {shipmentId_789}
    F-->>B: shipmentId_789
```

This is **replay**. Worker B never needed Worker A's memory. It rebuilt the same state by re-executing the same code against the same history.

The gap that never closes: if Stripe succeeds and the server dies **before** `ChargeCustomerCompleted` is written, the framework has no record and will retry the charge. So the framework gives you exactly-once *orchestration*, not exactly-once *side effects*. Activities still carry an idempotency key, see [exactly-once.md](exactly-once.md).

Two kinds of code fall out of this:

```mermaid
%% The split Temporal forces: replayable orchestration vs recorded side effects
flowchart LR
    subgraph WFB["Workflow: replayed on every recovery, must be deterministic"]
        W["processOrder<br/>ordering, branching,<br/>waiting, retries policy"]
    end
    subgraph ACTB["Activities: executed once per attempt, result recorded"]
        A1["chargeCustomer"]
        A2["reserveInventory"]
        A3["requestShipment"]
        A4["sendReviewEmail"]
    end
    E1["Stripe"]
    E2[("Inventory DB")]
    E3["Carrier API"]
    E4["Email provider"]

    W -->|"schedule"| A1 -->|"call"| E1
    W -->|"schedule"| A2 -->|"write"| E2
    W -->|"schedule"| A3 -->|"call"| E3
    W -->|"schedule"| A4 -->|"send"| E4

    class W service
    class A1,A2,A3,A4 service
    class E1,E3,E4 external
    class E2 store
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
```

| Temporal term | What it is | Runs where |
|---|---|---|
| **Workflow** | The replayable orchestration function | Any Workflow Worker, many times |
| **Activity** | One external operation whose result gets recorded | An Activity Worker, once per attempt |
| **Event history** | Append-only log of everything that happened to one workflow execution | Temporal's persistence store |

### 3.2 Make replay predictable: determinism

Replay only works if the function takes the **same path** on every run given the same history. Add "same-day pickup if before 5 PM" and it breaks.

```mermaid
%% The determinism trap: same code, same history, different wall clock, different branch
flowchart TD
    H[("History so far<br/>ChargeCustomerCompleted<br/>ReserveInventoryCompleted<br/>RequestSameDayPickupCompleted")]
    R1["First run at 4:59 PM<br/>currentTime() < 5 PM"]
    B1["requestSameDayPickup<br/>recorded in history"]
    CR["Crash"]
    R2["Replay at 5:03 PM<br/>currentTime() < 5 PM is false"]
    B2["Code now asks for<br/>requestNextDayPickup"]
    ERR["History says SameDay,<br/>code says NextDay:<br/>non-deterministic error,<br/>workflow task fails"]
    FIX["Fix: ask the framework<br/>for time. First run records<br/>4:59 PM, replay returns<br/>the recorded 4:59 PM"]
    OK["Replay takes the same<br/>branch, matches history"]

    R1 --> B1 --> H
    B1 --> CR --> R2 --> B2
    B2 -->|"compare with history"| ERR
    ERR -->|"the rule"| FIX --> OK

    class H store
    class R1,R2,B1,B2 service
    class CR external
    class ERR critical
    class FIX decision
    class OK service
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

Rules for workflow code, all consequences of "replay must match history":

- No wall clock, no random, no UUIDs, no environment reads. Use the SDK's `workflow.now()`, `workflow.random()`, side-effect helpers. They record the value the first time and return the recorded value on replay.
- No network calls, no DB reads, no file IO. Anything whose answer can change goes in an activity.
- No native threads or unmanaged goroutines. Iteration order over maps must be stable (Go maps are the classic bug).
- **Changing deployed workflow code while executions are in flight is the same bug.** A running order started on version 1 replays on version 2 and diverges. Temporal ships versioning / patching APIs (`workflow.GetVersion`, `patched()`) to branch old executions onto old logic. Staff answer: this is the operational cost of Temporal, and it needs a deploy checklist.

### 3.3 Let the workflow wait: durable timers

`sleep(5 days)` must not hold a worker. When the workflow reaches it, the framework writes `TimerStarted {fireAt}` and **stops running the workflow**. A background timer processor scans timers ordered by deadline. When one is due it appends `TimerFired` and schedules the workflow to run again. Replay reaches `sleep`, sees both events, and continues.

```mermaid
%% A five-day wait costs one row, not one process. The worker is busy only at day 0 and day 5.
sequenceDiagram
    participant W as Worker
    participant HS as History Service
    participant DB as Persistence
    participant TP as Timer processor
    participant M as Matching

    W->>HS: workflow reached sleep(5 days)
    HS->>DB: append TimerStarted {fireAt: May 15 10:00} + TimerTask (one txn)
    HS-->>W: nothing more to do, release the workflow
    Note over W: worker serves other workflows for 5 days
    Note over DB,TP: timers kept sorted by deadline, no scan of every sleeping workflow
    loop every tick
        TP->>DB: read timer tasks with fireAt <= now
    end
    TP->>HS: timer due for order 42
    HS->>DB: append TimerFired + TransferTask (one txn)
    HS->>M: workflow task for order 42
    M-->>W: workflow task
    W->>W: replay: sleep sees TimerStarted + TimerFired, continue
    W->>HS: schedule sendReviewEmail activity
```

- The timer processor is shared by every workflow on that history shard. A million sleeping orders cost a million rows, zero processes.
- If the History node dies, another takes over its shards and reloads pending timers from storage. An outage **delays** a timer, it never loses one.
- This is the mechanism behind Uber's "offer the ride to this driver, wait 10 s, move on" and the flash-sale "release the reservation after 10 minutes".

### 3.4 Let the outside world wake it: signals

Delivery does not take exactly five days. The workflow should wait **until the carrier says delivered**. Temporal calls that input a **Signal**: an external system sends a named message to a running workflow. Temporal appends it to history and schedules the workflow to run. Replay reaches `waitUntilDelivered`, finds the signal event, and continues.

```mermaid
%% A signal is just another history event, so waking a workflow is an append plus a task
sequenceDiagram
    participant C as Carrier webhook
    participant FE as Frontend
    participant HS as History Service
    participant DB as Persistence
    participant M as Matching
    participant W as Worker

    C->>FE: SignalWorkflow(order 42, "PackageDelivered", {ts})
    FE->>HS: route by workflow id to its shard
    HS->>DB: append WorkflowExecutionSignaled + WorkflowTaskScheduled + TransferTask (one txn)
    HS-->>FE: ack
    FE-->>C: 200
    Note over HS,M: background transfer processor dispatches the task
    HS->>M: workflow task for order 42
    M-->>W: workflow task
    W->>W: replay to waitUntilDelivered, signal present, continue
    W->>HS: schedule sendReviewEmail
    HS->>DB: append ActivityTaskScheduled + TransferTask
    HS->>M: activity task on the email queue
```

- Signals are durable and ordered per workflow. They are delivered at-least-once from the sender's view (the webhook may retry), so a signal handler should tolerate the same signal twice.
- The mirror of a signal is a **Query**: read workflow state without changing history (a read-only replay on a worker). Beyond the article, but the interviewer's next question is always "how do I see where the order is".

What we built, one problem at a time, is Temporal's programming model. The order flow is back to straight-line code:

```
workflow processOrder(order):
    chargeCustomer(order)
    reserveInventory(order)
    requestShipment(order)
    waitUntilDelivered(order)      // signal
    sendReviewEmail(order)
```

---

## 4. Lifecycle of one workflow execution

```mermaid
%% What one order looks like from Temporal's side. Every arrow is at least one history event.
stateDiagram-v2
    direction LR
    [*] --> Scheduled : WorkflowExecutionStarted
    Scheduled --> Running : worker picks task
    state "Waiting, no worker held" as Waiting {
        direction TB
        OnActivity : WaitingOnActivity
        OnTimer : WaitingOnTimer
        OnSignal : WaitingOnSignal
    }
    Running --> OnActivity : ActivityTaskScheduled
    OnActivity --> Running : ActivityTaskCompleted
    Running --> OnTimer : TimerStarted
    OnTimer --> Running : TimerFired
    Running --> OnSignal : blocks on signal
    OnSignal --> Running : WorkflowExecutionSignaled
    state "Closed" as Closed {
        direction TB
        Completed
        Failed
        Cancelled
        TimedOut
    }
    Running --> Completed : function returns
    Running --> Failed : retries exhausted
    Waiting --> Cancelled : CancelWorkflow
    Waiting --> TimedOut : WorkflowExecutionTimeout
    Running --> ContinuedAsNew : near history cap
    ContinuedAsNew --> Scheduled : new run id
    Closed --> [*]
```

- The three "Waiting" states hold **no worker**. Only `Running` (a workflow task, under 1 s of code) and activity attempts consume compute.
- A failed activity attempt stays in `WaitingOnActivity` and retries per policy (1 s, x2, cap 100 s, unlimited by default). Cancellation runs your compensations (refund, release reservation) as ordinary activities before the workflow closes.
- Each sequential activity costs about 6 history events (ActivityTaskScheduled / Started / Completed plus WorkflowTaskScheduled / Started / Completed). With the 51,200-event cap that is roughly 8,500 sequential steps before you must **Continue-As-New**: end this run, start a new one with the carry-over state as input and an empty history.

---

## 5. Under the hood: the cluster

The interviewer will rarely ask, but the layout explains every scaling and failure answer that follows.

```mermaid
%% Four independently scalable fleets plus your Workers. Persistence is where load ends up.
flowchart LR
    SDK["Client SDK<br/>start / signal / query"]
    FE["Frontend<br/>stateless gRPC gateway<br/>auth, rate limit, routing"]
    subgraph HISTORY["History Service"]
        HS1["History node 1<br/>shards 1..N/3"]
        HS2["History node 2<br/>shards N/3..2N/3"]
        HS3["History node 3<br/>shards 2N/3..N"]
    end
    subgraph MATCH["Matching Service"]
        MQ["Task queues<br/>partitioned per queue name<br/>sticky queues per worker"]
    end
    DB[("Persistence<br/>Cassandra / Postgres / MySQL<br/>history, mutable state,<br/>transfer + timer tasks")]
    VIS[("Visibility store<br/>Elasticsearch or SQL<br/>list / search executions")]
    WW["Workflow Workers<br/>your code, poll queues"]
    AW["Activity Workers<br/>your code, poll queues"]

    SDK -->|"gRPC"| FE
    WW -->|"poll + respond"| FE
    AW -->|"poll + respond"| FE
    FE -->|"hash workflow id to shard"| HS1
    FE -->|"poll task queue"| MQ
    HS1 -->|"one txn per state transition"| DB
    HS2 --> DB
    HS3 --> DB
    HS1 -->|"transfer task: dispatch"| MQ
    MQ -->|"spill when no poller"| DB
    HS1 -.->|"async visibility task"| VIS

    class SDK,FE client
    class HS1,HS2,HS3 service
    class MQ queue
    class DB critical
    class VIS store
    class WW,AW service
    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
```

| Component | Owns | Scales by |
|---|---|---|
| **Frontend** | Nothing. Validates, rate-limits, routes to the History shard or Matching partition | Add instances behind a load balancer |
| **History Service** | Workflow state. A fixed number of **history shards**, `hash(workflow id) mod N`; each node owns a subset, ownership moves on failure | Add nodes, up to the shard count. **Shard count is fixed at cluster creation** |
| **Matching Service** | Task queues (the queue is Temporal's own, backed by the persistence store, not Kafka) | Partition hot queues across instances |
| **Workers** | Your workflow and activity code. Temporal never executes user code | Add workers to the queue that has a backlog |
| **Persistence** | Everything durable. Every state transition is one transaction here | Vertical, or Cassandra horizontally. This is where the ceiling is |

Red node: persistence. The article's own sentence: "If workflow state updates become the bottleneck, adding application Workers won't fix that; we'd need more capacity in History or its database." Every activity completion, timer, and signal is at least one write transaction, so the cluster's throughput is measured in **state transitions per second**, not workflows.

---

## 6. One state transition is one transaction (Temporal's built-in outbox)

When `chargeCustomer` completes, History must do three things that must not be separated by a crash: append the event, update the current-state summary, and make sure the workflow runs next. It commits all three in **one transaction**, then a background processor dispatches the work.

```mermaid
%% The commit is the truth. Dispatch is a background read of the same commit, so a crash between them loses nothing.
sequenceDiagram
    participant AW as Activity Worker
    participant FE as Frontend
    participant HS as History shard owner
    participant DB as Persistence
    participant TP as Transfer processor
    participant M as Matching
    participant WW as Workflow Worker

    AW->>FE: RespondActivityTaskCompleted(paymentId_123)
    FE->>HS: route to shard of order 42
    HS->>DB: BEGIN
    HS->>DB: append ActivityTaskCompleted, WorkflowTaskScheduled
    HS->>DB: update mutable state (pending activities minus 1, next event id, sticky worker)
    HS->>DB: insert TransferTask {kind: WorkflowTask, order 42}
    HS->>DB: COMMIT
    HS-->>FE: ack
    FE-->>AW: ack
    Note over HS,TP: History can crash here. The TransferTask is already durable.
    TP->>DB: read transfer tasks for my shards
    TP->>M: AddWorkflowTask(order 42, sticky queue of Worker X)
    TP->>DB: ack / delete transfer task
    WW->>M: poll
    M-->>WW: workflow task with the new events
```

Three things are stored per workflow:

```mermaid
%% Conceptual persistence model. Real table names differ per store, the relationships do not.
erDiagram
    EXECUTION ||--o{ HISTORY_EVENT : "append-only log"
    EXECUTION ||--|| MUTABLE_STATE : "materialized view"
    EXECUTION ||--o{ TRANSFER_TASK : "work to dispatch"
    EXECUTION ||--o{ TIMER_TASK : "deadlines"
    SHARD ||--o{ EXECUTION : "owns by hash"
    SHARD {
        int shard_id PK
        string owner_host
        int range_id "fencing token for the owner"
    }
    EXECUTION {
        string workflow_id PK
        string run_id PK
        int shard_id FK
        string status
    }
    HISTORY_EVENT {
        int event_id PK
        string type "ActivityTaskCompleted, TimerFired, ..."
        blob payload "result, capped at 2 MB"
        timestamp ts
    }
    MUTABLE_STATE {
        int next_event_id
        json pending_activities
        json pending_timers
        json pending_child_workflows
        string sticky_worker
    }
    TRANSFER_TASK {
        int task_id PK
        string kind "WorkflowTask, ActivityTask, Close"
        string target_queue
    }
    TIMER_TASK {
        timestamp fire_at PK
        int task_id PK
        string kind "UserTimer, ActivityTimeout, WorkflowTimeout"
    }
```

- **Event history** is the durable truth and the input to replay.
- **Mutable state** is a cache of "what is happening right now" (pending activities, open timers, child workflows). It could be rebuilt by scanning history; keeping it materialized makes every transition O(1) instead of O(history).
- **Transfer task** is the outbox row. The processor reads it after commit and hands it to Matching. Same pattern as the transactional outbox in [exactly-once.md](exactly-once.md) section 3, just internal.
- **Timer task** is the same idea keyed by deadline. The shard's `range_id` is a fencing token: a node that lost the shard cannot commit stale writes, see [leases-fencing-clocks.md](leases-fencing-clocks.md).

---

## 7. Not replaying everything: sticky execution and the workflow cache

Replaying a 20,000-event history on every activity completion would be absurd. So the worker that last ran the workflow keeps the rebuilt state **in memory**, and History routes the next workflow task back to that worker through a worker-specific **sticky queue**.

```mermaid
%% Sticky queue hits the cache. If the sticky worker is gone, the task times out and falls back to the shared queue plus a full replay.
flowchart LR
    HS["History shard<br/>order 42, sticky = Worker A"]
    SQ[["Sticky queue<br/>worker-A-abc123"]]
    NQ[["Normal task queue<br/>order-workflows"]]
    WA["Worker A<br/>workflow cache holds<br/>order 42 rebuilt state"]
    WB["Worker B<br/>no cache for order 42"]
    TO["Sticky task not picked up<br/>in 5 s: History clears<br/>stickiness, reschedules"]
    RP["Worker B fetches full<br/>history, replays from<br/>event 1, then caches it"]

    HS -->|"workflow task"| SQ
    SQ -->|"poll"| WA
    WA -->|"apply only new events<br/>from cache, respond fast"| HS
    WA -.->|"crash / eviction"| TO
    HS -->|"same task, normal route"| NQ
    NQ -->|"poll"| WB
    WB --> RP -->|"respond"| HS
    TO --> NQ

    class HS service
    class SQ,NQ queue
    class WA cache
    class WB,RP service
    class TO critical
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef cache    fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
```

- Each worker polls **two** queues: the shared one and its own sticky one.
- On a sticky hit, the server sends only the events after the cached point. The worker applies them and responds. Cost is O(new events).
- The cache is amber for a reason: it is losable. Correctness comes from history, performance comes from the cache. Worker crash, cache eviction (LRU by cached-workflow count), or a deploy just means one full replay per workflow on the new worker.
- Sticky schedule-to-start timeout default: **5 s** (Go SDK). That is the worst-case added latency when a sticky worker vanishes.

---

## 8. Task queues route work to fleets

The workflow names a **task queue** for each activity. Workers are configured to poll queue names. Matching connects them and knows nothing about what the code does.

```mermaid
%% One workflow, four queues, four independently sized fleets. Matching only matches names.
flowchart LR
    HS["History<br/>transfer processor"]
    subgraph M["Matching Service"]
        Q0[["order-workflows<br/>workflow tasks"]]
        Q1[["payments<br/>activity tasks"]]
        Q2[["shipping<br/>activity tasks"]]
        Q3[["email<br/>activity tasks"]]
    end
    F0["Workflow workers<br/>x 4, small CPU"]
    F1["Payment workers<br/>x 2, PCI-isolated network"]
    F2["Shipping workers<br/>x 8, slow carrier APIs"]
    F3["Email workers<br/>x 20, burst on delivery day"]

    HS -->|"workflow task"| Q0 -->|"long poll"| F0
    HS -->|"chargeCustomer"| Q1 -->|"long poll"| F1
    HS -->|"requestShipment"| Q2 -->|"long poll"| F2
    HS -->|"sendReviewEmail"| Q3 -->|"long poll"| F3

    class HS service
    class Q0,Q1,Q2,Q3 queue
    class F0,F1,F2,F3 service
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
```

- **Workflow task**: "run the workflow code and tell me what to do next". **Activity task**: "do this one thing". They can run on different machines, or the same process if you do not care.
- Long poll: when a worker is already waiting, Matching hands the task straight through (sync match). Otherwise the task is written to the persistence store until someone polls.
- A hot queue is **partitioned** across Matching instances so one queue name is not one machine.
- GPU work, CPU-heavy transcoding, and PCI-scoped payment calls each get their own queue and fleet. This is the YouTube pipeline answer: split, transcode segments in parallel on a GPU queue, join.

---

## 9. Scaling: which knob fixes which symptom

The point of the architecture: Worker compute scales with **work ready to run**, not with **workflows open**. A million orders waiting for delivery are a million rows and zero workers.

```mermaid
%% Read the symptom, turn one knob. The last branch is the one with no easy knob.
flowchart TD
    S{"What is growing?"}
    A["Activity backlog on one queue<br/>schedule-to-start latency up"]
    B["Workflow task latency up<br/>sticky misses, replay time"]
    C["Frontend 429s / RESOURCE_EXHAUSTED"]
    D["One task queue partition hot"]
    E["History shard CPU high<br/>persistence write latency up"]
    KA["Add activity workers<br/>on that queue only"]
    KB["Bigger workflow cache,<br/>more workflow workers,<br/>Continue-As-New long histories"]
    KC["Add Frontend instances,<br/>raise namespace RPS limits"]
    KD["Raise partitions for<br/>that queue name"]
    KE["Add History nodes up to<br/>the shard count, then scale<br/>persistence. Shard count is<br/>fixed at creation: plan 512+"]

    S -->|"email backlog on<br/>delivery day"| A --> KA
    S -->|"p99 of workflow<br/>task completion"| B --> KB
    S -->|"client errors"| C --> KC
    S -->|"one queue"| D --> KD
    S -->|"state transitions / s"| E --> KE

    class S decision
    class A,B,C,D service
    class E critical
    class KA,KB,KC,KD service
    class KE critical
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
```

- Capacity planning unit: **state transitions per second** (every activity scheduled or completed, every timer, every signal is 1 to 2). Worker count follows queue depth; History and DB capacity follow transitions.
- Shard count is the irreversible choice: docker dev config ships 4, the Helm chart ships 512, the docs say clusters have run with 1 to 128k. Too few caps History parallelism forever, too many adds per-shard overhead on every node. Changing it means a new cluster and a migration.

---

## 10. Failure modes and blast radius

| Failure | What Temporal does | What you still own |
|---|---|---|
| Activity worker dies mid-call | Attempt times out (start-to-close, or missed heartbeat for long activities), retried per policy on another worker. At-least-once | Idempotency key on every external call. Heartbeat from a separate thread for anything longer than the timeout |
| Workflow worker dies | Sticky task times out in 5 s, task goes to the normal queue, another worker replays | Nothing, unless the history is huge (replay time) |
| History node dies | Its shards move to other nodes, pending timers and transfer tasks reload from storage. Timers delayed, not lost | Alert on shard reassignment time and timer lag |
| Matching node dies | Tasks are already durable in persistence; pollers reconnect via Frontend | Nothing |
| Persistence store down | The whole cluster stalls. No transitions commit, workers get errors on respond, timers do not fire | This is the red node. Run the DB with the same HA bar as the workflows it protects |
| Workflow code deployed with a changed path | Replay diverges from history: non-deterministic error, workflow task fails and retries forever until fixed | Versioning / patching API, replay tests in CI against sampled production histories, worker versioning for hard cuts |
| History passes 10,240 events / 10 MB | Warning. At 51,200 events / 50 MB the execution is terminated | Continue-As-New before the cap: loops, polling, and long-lived entity workflows must budget events |
| Activity fails forever (poison) | Default retry: 1 s initial, x2 backoff, cap 100 s, **unlimited attempts** | Set `MaximumAttempts` or non-retryable error types, or the workflow waits forever |
| Workflow task takes too long | Go SDK deadlock detector fails the task after 1 s of workflow code | Do nothing slow in workflow code. Slow means activity |
| Signal sent twice (webhook retry) | Both appended, both delivered to the handler | Handler must tolerate duplicates |
| Payload over 2 MB | Rejected (blob limit, warning at 256 KB) | Pass references (S3 keys), not data |

---

## 11. When to use it, when not to

```mermaid
%% The decision an interviewer wants to hear you make out loud
flowchart TD
    Q1{"Is it one independent<br/>background job?"}
    Q2{"Is it a continuous<br/>high-volume event stream?"}
    Q3{"Multi-step, needs retries,<br/>partial-failure recovery,<br/>or waits on external input?"}
    Q4{"Is the workflow engine<br/>the thing being designed?"}
    A1["Queue + worker<br/>SQS, Kafka consumer<br/>Notification system"]
    A2["Stream processor<br/>Kafka + Flink"]
    A3["Temporal<br/>or Step Functions, or<br/>event choreography"]
    A4["Design it yourself:<br/>history log, owner per run,<br/>outbox, timers, task queues"]
    A5["Plain code"]

    Q1 -->|"yes"| A1
    Q1 -->|"no"| Q2
    Q2 -->|"yes"| A2
    Q2 -->|"no"| Q3
    Q3 -->|"no"| A5
    Q3 -->|"yes"| Q4
    Q4 -->|"yes"| A4
    Q4 -->|"no"| A3

    class Q1,Q2,Q3,Q4 decision
    class A1,A2,A5 service
    class A3 service
    class A4 critical
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
```

**Use it when**

- Several dependent steps must happen reliably (YouTube: split, transcode in parallel, join).
- The process waits on the world (Uber: offer ride, wait 10 s for the driver, move to the next).
- You must resume from partial execution (a worker died halfway through the DAG).
- You notice you are building a state machine table plus a scheduler plus a retry loop. That is the tell.

**Do not use it when**

- One independent job: a queue is simpler and the retry machinery is the interesting part of the design (the notification-system breakdown deliberately uses a queue).
- High-volume streaming: Temporal is a coordinator, not Kafka. One event per history row does not survive 100k events/s.
- The interviewer wants the engine. Then section 3 to 6 of this note **is** your design: event log per run, one owner per run, transactional outbox for dispatch, timer table by deadline, named task queues. That is exactly `hld/distributed-job-scheduler/`.

---

## 12. Trade-offs

| Gain | Cost |
|---|---|
| Orchestration reads as straight-line code, recovery is free | Workflow code lives under determinism rules. Map iteration, time, random, threads, and deploys all become foot-guns |
| Millions of open workflows cost rows, not processes | Every transition is a DB transaction. Throughput ceiling is the persistence store, and shard count is set once |
| Exactly-once orchestration (a completed step never re-runs) | Still at-least-once side effects. Idempotency keys do not go away |
| Timers and signals for free, durable across outages | Timer precision is "eventually after fireAt", not real-time. Do not build a trading engine on it |
| Retries, backoff, heartbeats, timeouts built in | Unlimited retries by default. A poison activity waits forever unless you cap it |
| Full history per execution for debugging | 51,200 events / 50 MB cap. Long-lived entities must Continue-As-New, which complicates queries and signals in flight |
| Independent scaling of Frontend, History, Matching, Workers | An extra distributed system to run: 4 services plus Cassandra or SQL plus optional Elasticsearch. Or pay Temporal Cloud |

---

## 13. Numbers worth memorizing

- History limits: warn at **10,240 events / 10 MB**, terminate at **51,200 events / 50 MB** per execution. Payload blob: warn 256 KB, error **2 MB**. gRPC message cap **4 MB**.
- About **6 events per sequential activity**, so roughly **8,500 steps** per run before Continue-As-New. A polling loop that checks every minute burns its budget in under 6 days.
- Pending per type per workflow: **2,000** (activities, timers, child workflows, signals awaiting handling).
- Workflow task timeout default **10 s**, max **120 s**. Go SDK deadlock detector: **1 s** of workflow code.
- Sticky schedule-to-start timeout: **5 s** (worst-case extra latency after a workflow worker dies).
- Default activity retry: **1 s** initial, **x2** backoff, **100 s** max interval, **unlimited** attempts.
- History shards: docker dev **4**, Helm default **512**, seen in production from 1 to 128k. Immutable after creation.
- Persistence options for self-hosting: Cassandra, PostgreSQL, MySQL. Visibility: same SQL or Elasticsearch.
- Capacity unit: state transitions per second, not workflows. Each activity round trip is 2 transitions (scheduled, completed) plus a workflow task.

---

## 14. Interview soundbite

> "Temporal gives me durable execution: I write the order flow as straight-line code, but every external call is an activity whose result is appended to a per-workflow event history in one transaction with an outbox-style task, and waits are timers and signals stored the same way. If the worker dies, any other worker replays the code against the history, so completed steps return their recorded result instead of running again. The two costs are that workflow code must be deterministic, which makes deploys a versioning problem, and that activities are still at-least-once, so Stripe still gets an idempotency key. Under load the bottleneck is state transitions per second on the persistence store, not workers, and the history shard count is fixed on day one. If you would rather I design the engine itself, it is a history log per run, one owner per run, a transfer-task outbox, a timer table sorted by deadline, and named task queues."

Follow-ups an interviewer will ask, in order of likelihood:

1. What if Stripe succeeds and the worker dies before the result is recorded? (Section 3.1, retried, so idempotency key.)
2. Why must workflow code be deterministic, and what happens on a code deploy? (Section 3.2, replay diverges, versioning API.)
3. How does a five-day wait not hold a worker? (Section 3.3, TimerStarted row, timer processor, TimerFired.)
4. How does the carrier webhook reach the running workflow? (Section 3.4, signal appended to history, workflow task dispatched.)
5. Does it replay the whole history every time? (Section 7, sticky queue and workflow cache, 5 s fallback.)
6. What breaks first at scale? (Section 5 and 9, persistence, shard count fixed.)
7. What about a workflow that runs for a year? (Section 4 and 13, 51,200 cap, Continue-As-New.)
8. Why not just Kafka plus a state table? (Section 11, you would be building sections 3 to 6 yourself; fine if that is the question.)
9. Where does the outbox pattern show up inside Temporal? (Section 6, transfer task in the same transaction.)
10. Uber offers a ride to one driver at a time with a 10 s timeout. Sketch it. (Section 3.3 timer plus 3.4 signal, per-ride workflow, `select` on accept signal vs timer.)

Related: [exactly-once.md](exactly-once.md) (idempotency keys and the outbox this is built on), [distributed-transactions.md](distributed-transactions.md) (sagas, which a Temporal workflow is one way to run), [leases-fencing-clocks.md](leases-fencing-clocks.md) (shard ownership and the range id), [sharding.md](sharding.md) (fixed shard count vs consistent hashing), [stream-processing.md](stream-processing.md) (what to use instead for high-volume streams), `hld/distributed-job-scheduler/` (the same design built from parts, with the Temporal limits as sizing inputs), `hld/payments-ledger/` (attempt IDs for the non-idempotent rail that Temporal cannot fix).
