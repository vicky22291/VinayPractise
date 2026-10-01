# Diagrams: expense / corporate card rules engine

> One-line answer: twelve views of one design. A synchronous auth path (gateway, decision service, tenant-sharded Postgres counters with holds) answers a swipe in ~15 ms p50. An asynchronous path (Kafka, settlement consumer, expense service, Temporal) settles, re-checks and reimburses. A control plane (policy service, simulator, bundle store) turns rules into immutable bundles. The spend-control DB is the one red box.

The D1 to D12 set from `hld/CLAUDE.md` §4, each with a one-line caption. A diagram already in [`solution.md`](solution.md) gets a heading, a caption and a link, never a second copy. Acronyms: HRIS (human resources information system), CEL (Common Expression Language), AZ (availability zone), CDC (change data capture), ACH (automated clearing house), MCC (merchant category code), LRU (least recently used), WAL (write-ahead log), RPC (remote procedure call).

| # | Diagram | Where it lives |
|---|---|---|
| D1 | Context | below |
| D2 | Data flow | below |
| D3 | Component architecture (final design) | [solution §6](solution.md#6-final-design-and-the-six-core-flows) |
| D4 | Happy path per FR | FR1 publish a rule: below. FR2 evaluate a SUBMIT: below. FR3 authorize: [solution Flow 1](solution.md#flow-1-a-62-lunch-is-approved-about-15-ms) (capture: [Flow 3](solution.md#flow-3-the-dinner-captures-at-84-with-the-tip)). FR4 reimburse: [solution Flow 5](solution.md#flow-5-a-reimbursement-from-submit-to-payout) |
| D5 | Failure paths | Auth redelivered after a gateway death, consumer crash between commits, service unreachable: below. Two swipes race: [solution Flow 2](solution.md#flow-2-two-swipes-race-for-the-last-20-of-a-counter). Cluster failover: [solution §10.4](solution.md#104-failure-timeline) |
| D6 | Decision flow | Gateway fallback: [solution §5.3](solution.md#53-keep-cards-working-when-parts-fail-fallback-layers). Engine evaluation algorithm: below |
| D7 | Entity relationship | [solution §3.3](solution.md#33-data-model) |
| D8 | State machines | Hold: [solution §5.2](solution.md#52-two-swipes-can-never-both-break-a-limit-aggregates-holds-and-concurrency). Expense report and rule version: below |
| D9 | Deployment / topology | below |
| D10 | Scaling / partitioning | below |
| D11 | Failure mode map | below, two trees |
| D12 | Rollout / migration | below |

## D1. Context (zoom-out)

Our system as one box: people write policy and expenses, the processor asks for decisions, HRIS and travel supply facts, payroll pays, auditors read.

```mermaid
%% D1: the system as one box with every external actor. HRIS talks to the processor directly for one thing only: termination.
flowchart LR
    ADM[Admins]:::client -->|"rules, simulate,<br/>publish, rollback"| SYS[Expense rules engine<br/>auth path, policy plane,<br/>reimbursement]:::service
    SYS -->|"impact report, version,<br/>decline-spike alert"| ADM
    EMP[Employees]:::client -->|"expenses, receipts,<br/>report submit"| SYS
    SYS -->|"decision with every<br/>verdict and reason"| EMP
    APR[Approvers]:::client <-->|"approval task,<br/>approve or reject"| SYS
    PROC[Card network +<br/>issuer processor]:::external -->|"sync auth 2 s deadline,<br/>lifecycle webhooks"| SYS
    SYS -->|"approve or decline,<br/>coarse static controls"| PROC
    HRIS[HRIS]:::external -->|"attribute events,<br/>org chart"| SYS
    HRIS -->|"termination freezes<br/>cards, synchronous"| PROC
    TRV[Travel booking]:::external -->|"booked trips and dates"| SYS
    SYS -->|"payout, one per report"| PAY[Payroll or<br/>payments ledger]:::external
    SYS -->|"decision exports, policy<br/>change log, read-only"| AUD[Customer auditors]:::external
    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

## D2. Data flow (DFD)

Inputs to outputs with format, size and rate. Peak rates unless marked per day.

```mermaid
%% D2: data flow. Processes are rounded, stores are cylinders. Numbers from solution 1.2 and 2 and the editor's volumes, except the attribute rate, marked estimate.
flowchart LR
    PROC[Issuer processor]:::external -->|"auth request, JSON ~1 KB,<br/>1.2k/s peak, 2k/s design"| AD(Auth gateway +<br/>decision service):::service
    AD -->|"approve or decline,<br/>JSON ~20 B body, p99 50 ms"| PROC
    HRIS[HRIS]:::external -->|"attribute event, JSON ~1 KB,<br/>under 10/s, estimate"| ECS[(Employee context<br/>Redis, 3 GB)]:::cache
    ECS -->|"attributes ~1 KB,<br/>60 s local cache"| AD
    BS[(Policy DB +<br/>bundle store, ~2 GB)]:::store -->|"bundle, 40 KB median, 5 MB max,<br/>on activation or LRU miss"| AD
    AD -->|"counter txn, 3 locks + holds +<br/>AUTH decision 1.5 KB, 2k txn/s"| SDB[(Spend-control DB<br/>16 logical shards)]:::store
    PROC -->|"lifecycle webhook, JSON ~2 KB,<br/>13 M/day, 1.5k/s"| K[[Kafka card-events<br/>64 partitions, 26 GB/day]]:::queue
    K -->|"events keyed by card_id"| SC(Settlement consumer):::service
    SC -->|"hold to spend + CAPTURE<br/>decision, 10 M/day"| SDB
    SC -->|"expense outbox rows,<br/>10 M/day"| ES(Expense service +<br/>expense DB + workflow):::service
    EMP[Employee app]:::client -->|"expense JSON + receipt, 1 M/day<br/>in ~330k reports, 360/s month-end"| ES
    ES -->|"evaluate SUBMIT, trip total<br/>as a fact, 11 M/day"| AD
    ADM[Admin]:::client -->|"draft rule, envelope + CEL,<br/>~1 KB compiled, few per week"| PS(Policy service +<br/>simulator):::service
    PS -->|"bundle by SHA-256"| BS
    SDB -->|"CDC, AUTH + CAPTURE decisions 20 M/day,<br/>auths, lifecycle events, processor declines"| LAKE[(Decision lake, 31 M/day<br/>46.5 GB raw, ~9 GB Parquet)]:::store
    ES -->|"second CDC stream,<br/>SUBMIT decisions 11 M/day"| LAKE
    LAKE -->|"90 days of columns,<br/>up to ~4 GB per simulation"| PS
    ES -->|"payroll line or ACH,<br/>~330k reports/day"| PAY[Payroll or<br/>payments ledger]:::external
    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef cache    fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

- 31 M decisions/day = 10 M AUTH + 10 M CAPTURE + 11 M SUBMIT, ~1.5 KB each. SUBMIT decisions live in the expense DB (same schema), so the lake has two CDC streams. It also takes authorizations and lifecycle events, because the simulator recomputes counters from them under each policy.

## D3. Component architecture

The final design, spend-control DB in red. Embedded once in [solution §6](solution.md#6-final-design-and-the-six-core-flows).

## D4. Happy paths, one per FR

FR3 authorize: [solution Flow 1](solution.md#flow-1-a-62-lunch-is-approved-about-15-ms), capture in [Flow 3](solution.md#flow-3-the-dinner-captures-at-84-with-the-tip). FR4 reimburse to payout: [Flow 5](solution.md#flow-5-a-reimbursement-from-submit-to-payout). FR1 and FR2 are new below.

### D4 FR1. An admin publishes a tightened rule

Save type-checks, simulation diffs 90 days (~40 s for the largest tenant, under 1 s for a median one), publish compiles an immutable bundle, and every evaluator flips to it inside ~5 s p99.

```mermaid
%% D4 (FR1): "restaurant at most $75" becomes $60, with the solution Flow 4 numbers. Only the last two steps touch the evaluators.
sequenceDiagram
    autonumber
    participant A as Admin UI
    participant PS as Policy service
    participant SIM as Simulator
    participant BS as Bundle store
    participant K as Kafka policy-activated
    participant D as Decision services
    A->>PS: PUT draft rule restaurant-75, category_cap(restaurant, 6000)
    PS->>PS: expand template, type-check CEL, cost estimate, save draft d_3
    PS-->>A: draft ok (a typo like amout fails here, with a position)
    A->>PS: POST simulate(d_3, window_days 90)
    PS->>SIM: job j_8 on the 64-core pool, tenant quota 2 jobs
    SIM->>SIM: 90 days from the lake, pass 1 point verdicts in parallel, pass 2 folds events in time order
    SIM-->>PS: v12 re-simulated vs d_3, 412 newly need approval ($6,900 over the limit), 0 declined
    PS-->>A: impact, under the 2% decline and 10% approval guards, no confirm_token
    A->>PS: POST publish(d_3, base_version 12, ENFORCE, effective_from now)
    PS->>PS: one policy DB txn, compare-and-set on base 12, RULE versions + POLICY_VERSION 13
    PS->>BS: compile bundle v13 (index, counter dims, static controls), PUT by SHA-256
    PS->>K: policy-activated(tenant, 13, effective_from), bundle_uri on version 13
    PS-->>A: policy_version 13
    K->>D: every instance consumes the event
    D->>BS: GET bundle v13 (~40 KB), verify hash, flip pointer, p99 5 s
```

- Versions follow spend time, never submit time. A card expense reuses the version on its AUTHORIZATION at CAPTURE and SUBMIT; an out-of-pocket expense uses the version in force at the start of its date, so this same-day publish applies to out-of-pocket spend from tomorrow.
- Nothing is pushed to the processor here: static controls carry only ENFORCE DECLINE rules the processor can express, and a new one is pushed only after a 24 h soak [estimate]. A rollback activates here in ~5 s and its loosening push follows.

### D4 FR2. Evaluate a SUBMIT expense and explain it

The $92 dinner on trip t_88 from solution §4.2, in the final design: the expense service locks the trip and passes its total as a fact, the index narrows, every verdict comes back with numbers.

```mermaid
%% D4 (FR2): one out-of-pocket expense at SUBMIT. The trip row lock serializes two reports on one trip until COMMIT. The decision service never reads the expense DB.
sequenceDiagram
    autonumber
    participant M as Employee app
    participant E as Expense service
    participant EDB as Expense DB
    participant D as Decision service
    participant C as Employee context
    M->>E: POST reports/r_5/submit, Idempotency-Key k1
    E->>EDB: BEGIN, r_5 to SUBMITTED, TRIP t_88 FOR UPDATE, trip total by category
    EDB-->>E: card + open out-of-pocket lines, meals 12500, all 140000
    E->>D: evaluate(SUBMIT, x_4 9200 restaurant, trip totals as facts)
    D->>C: attributes of e_17 (60 s local cache)
    C-->>D: dept sales, level L4, US, attribute_version 88
    D->>D: v12 in force at the start of the expense date, index (SUBMIT, restaurant), 4 candidates
    D->>D: restaurant-75 VIOLATED 9200 vs 7500, single-250 PASS
    D->>D: meals-per-trip VIOLATED 21700 vs 20000 (TRIP), trip-2000 PASS
    D-->>E: NEEDS_APPROVAL (max severity), 4 results by rule_id, v12, facts_hash
    E->>EDB: DECISION d_9, x_4 submitted, COMMIT, trip lock released
    E-->>M: NEEDS_APPROVAL, meals on this trip total $217.00 vs a $200.00 limit
    Note over E,D: a 3-expense report repeats steps 4 to 10 per expense under the same lock
```

## D5. Failure paths

Already in solution.md: the concurrency race ([Flow 2](solution.md#flow-2-two-swipes-race-for-the-last-20-of-a-counter)) and the cluster failover ([§10.4](solution.md#104-failure-timeline)). Three new ones below.

### D5a. The same authorization arrives twice after a gateway pod died mid-request

The counter transaction committed, the answer was lost, and the retry's first INSERT hits the claim key and returns the stored result. Never a second hold.

```mermaid
%% D5a: pod G1 dies after the commit and before the answer. One PROCESSOR_EVENT claim per request makes the retry a no-op that returns the stored result.
sequenceDiagram
    autonumber
    participant P as Issuer processor
    participant G1 as Gateway pod 1
    participant G2 as Gateway pod 2
    participant D as Decision service
    participant S as Spend-control DB
    P->>G1: auth a_501, 4000 USD minor, processor deadline 2 s
    G1->>D: evaluate(AUTH, a_501, budget 1.2 s)
    D->>S: BEGIN, claim auth:a_501:0, AUTHORIZATION, HOLD x3, counters sorted, DECISION, COMMIT
    S-->>D: committed, t = 6 ms
    D-->>G1: ALLOW, d_61
    Note over P,D: pod G1 killed at t = 7 ms, answer lost, the processor or load balancer retries (unverified, per processor)
    P->>G2: auth a_501 again, t = ~300 ms
    G2->>D: evaluate(AUTH, a_501, budget left ~0.9 s)
    D->>S: BEGIN, INSERT PROCESSOR_EVENT auth:a_501:0
    S-->>D: unique violation, ROLLBACK, stored result d_61, holds already there
    D-->>G2: ALLOW, d_61, no new hold
    G2-->>P: approved, t = ~320 ms
    Note over P,S: no retry before 2 s means the timeout setting decides, then authorization.created drives adopt(a_501), and the processor's record wins
```

- `PROCESSOR_EVENT(tenant_id, event_key)` is claimed by the first INSERT, with no separate "not seen" read. A duplicate that arrives while the first transaction is open waits on the unique index, then returns the stored result. Increments claim `auth:a_501:1` to `n`; declines are recorded the same way, so a retried decline never flips.
- The processor's recorded outcome is final. Its `authorization.created` and `authorization.updated` events go through adopt, which adds or releases holds wherever our record disagrees, and marks an orphaned decision `superseded`.

### D5b. The settlement consumer dies between the DB commit and the Kafka offset commit

The replay hits the claim key and is a no-op. The expense row travels in an outbox row committed with the capture, so the crash cannot lose it.

```mermaid
%% D5b: at-least-once delivery plus one claim key per processor event gives an exactly-once effect. The outbox carries the side effect.
sequenceDiagram
    autonumber
    participant K as Kafka card-events p17
    participant C1 as Consumer 1
    participant C2 as Consumer 2
    participant S as Spend-control DB
    participant E as Expense service
    K->>C1: t_9 capture 8400 for a_80
    C1->>C1: CAPTURE point rules in process, before BEGIN
    C1->>S: BEGIN, claim txn:t_9, hold to spend, DECISION, OUTBOX expense t_9, COMMIT
    S-->>C1: committed
    Note over K,C2: consumer 1 crashes before the offset commit, no heartbeat for session.timeout.ms 10 s (estimate), group rebalances
    S-->>E: outbox relay delivers expense row t_9
    E->>E: idempotent upsert keyed t_9
    K->>C2: p17 from the last committed offset, t_9 again
    C2->>S: BEGIN, INSERT PROCESSOR_EVENT txn:t_9
    S-->>C2: unique violation, ROLLBACK, stored result
    C2->>K: commit offset past t_9
```

- Solution Flow 3 used to call the expense service after the commit, so a crash in between lost the expense. The outbox closes that window, and the expense service dedups on the transaction id.

### D5c. The whole service is unreachable from the processor

Static controls still bound every swipe, the timeout setting approves at 2 s, and the queued `authorization.created` webhooks adopt those approvals when the path returns.

```mermaid
%% D5c: a bad gateway deploy refuses every request for 12 minutes. The processor decides alone, within the static controls.
sequenceDiagram
    autonumber
    participant N as Card network
    participant P as Issuer processor
    participant G as Auth gateway
    participant R as Webhook receiver
    participant SC as Settlement consumer
    participant S as Spend-control DB
    Note over G,R: t = 0, bad deploy, every request refused
    N->>P: auth a_900, 18000, MCC 5812
    P->>P: static controls pass, category allowed, under per-auth max
    P-xG: issuing_authorization.request
    Note over P,G: no answer, 2 s deadline passes
    P-->>N: approved by the timeout setting (approve)
    N->>P: auth a_901, 90000, over the static per-auth max
    P-->>N: declined by static controls, we are never asked
    Note over P,R: t = 30 s health check pages, t = 12 min rollback done
    P->>R: queued webhooks, a_900 authorization.created (timeout approval), a_901 declined, capture t_40
    R->>S: DECISION for a_901, citing the static per-auth max
    R->>SC: card-events in per-card order
    SC->>S: adopt(a_900, approved), claim, AUTHORIZATION + open holds, aggregates re-run, FLAG
    SC->>S: capture t_40, open hold amount to spend
    Note over P,S: a capture or reversal for an unknown auth_id first creates the AUTHORIZATION in its end state, so a later journal replay adds no hold
```

- One idempotent `adopt(auth_id, state)` covers every authorization we did not decide: degraded journal entries, timeout approvals, Commando Mode, network STIP (stand-in processing). It never re-decides. `authorization.updated` (a reversal, an expiry) goes through the same path. Waiting for force capture instead would leave an open hotel authorization invisible to limits for days.

## D6. Activity / decision flow

The gateway's healthy-or-fallback decision is in [solution §5.3](solution.md#53-keep-cards-working-when-parts-fail-fallback-layers). Below: the engine's evaluation algorithm inside the decision service, per call.

```mermaid
%% D6: one evaluate call. Pink diamonds branch. Only enforced, non-error verdicts reach the outcome; everything else is still recorded.
flowchart TD
    A(["evaluate expense, context<br/>facts + bundle vN"]):::client -->|"context, category"| B[Index lookup<br/>median 8, max ~100 candidates]:::service
    B -->|"candidate rules"| C[Scope match<br/>employee attributes vs scope]:::service
    C -->|"in-scope rules"| D{Rule inputs exist<br/>in this context?}:::decision
    D -->|"no, e.g. trip at AUTH"| NE[NOT_EVALUABLE<br/>missing input or short_circuit]:::service
    D -->|"yes"| E{Point or<br/>aggregate?}:::decision
    E -->|"point, runs first"| F[CEL on facts<br/>~1 us per rule]:::service
    E -->|"aggregate after an enforced<br/>point DECLINE, skipped"| NE
    E -->|"aggregate, no point DECLINE"| G[Claim auth, lock counters by key,<br/>or trip total fact at SUBMIT]:::service
    F -->|"verdict"| H{Runtime error?}:::decision
    G -->|"spent + held + exact<br/>amount vs limit"| H
    H -->|"yes"| ER[ERROR<br/>no effect, alert]:::service
    H -->|"no"| I{Mode SHADOW?}:::decision
    I -->|"yes"| SH[Recorded, shadow true,<br/>no outcome, no holds]:::service
    I -->|"no, PASS or VIOLATED"| K[Outcome = max severity<br/>ALLOW, ALLOW_FLAGGED,<br/>NEEDS_APPROVAL, DECLINE]:::service
    NE -->|"result"| O["Record AUTHORIZATION + DECISION,<br/>declines too. At AUTH, not DECLINE:<br/>hold max(amt, min(1.2 x amt, headroom))"]:::service
    ER -->|"result + review flag"| O
    SH -->|"result"| O
    K -->|"outcome"| O
    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

- A lock or statement timeout on G is not an `ERROR`. The decision service returns the point-rule verdicts marked "store unavailable" and the gateway falls back (solution §5.3). The tip buffer only sizes the hold, so it never causes a decline. At AUTH only `DECLINE` answers `approved: false`. `NEEDS_APPROVAL` approves the swipe and opens an approval on the expense afterwards: the money moves first.

## D7. Entity relationship

POLICY_VERSION, RULE, COUNTER, HOLD, AUTHORIZATION, DECISION, EXPENSE, TRIP, REPORT, APPROVAL_TASK and PAYOUT, with keys and the DB each lives in: [solution §3.3](solution.md#33-data-model).

## D8. State machines

The hold lifecycle (Held, PartlyCaptured, Captured, Released, Refunded) is in [solution §5.2](solution.md#52-two-swipes-can-never-both-break-a-limit-aggregates-holds-and-concurrency). Two new ones below.

### D8a. Expense report

No state pins a policy version: a card expense reuses its authorization's version, an out-of-pocket one uses the version in force at the start of its date. Money owed to the employee always runs a workflow.

```mermaid
%% D8a: expense report lifecycle. Submit is accepted from DRAFT or RETURNED. A card-only ALLOW report closes inside the submit transaction; everything with money owed runs a Temporal workflow to PAID.
stateDiagram-v2
    direction LR
    [*] --> DRAFT: create
    DRAFT --> SUBMITTED: submit
    RETURNED --> SUBMITTED: resubmit
    SUBMITTED --> [*]: card-only ALLOW
    SUBMITTED --> AUTO_APPROVED: ALLOW, under limit
    SUBMITTED --> PENDING_APPROVAL: approval needed
    SUBMITTED --> RETURNED: DECLINE
    PENDING_APPROVAL --> APPROVED: all or part approved
    PENDING_APPROVAL --> RETURNED: sent back
    PENDING_APPROVAL --> REJECTED: approver rejects
    AUTO_APPROVED --> PAYOUT_SCHEDULED: PAYOUT row written
    APPROVED --> PAYOUT_SCHEDULED: money owed
    APPROVED --> [*]: card-only, none owed
    PAYOUT_SCHEDULED --> PAYOUT_SCHEDULED: rail unpaid, switch
    PAYOUT_SCHEDULED --> PAID: rail confirms
    REJECTED --> [*]
    PAID --> PAYOUT_SCHEDULED: ACH return, new attempt
    PAID --> [*]
```

- Auto-approve needs `ALLOW` and a total at or under the tenant's limit ($250 default [estimate]). Anything else (`NEEDS_APPROVAL`, a flag, a total over the limit) goes to PENDING_APPROVAL, and finance approves above $1,000 whatever the outcome. The workflow (id = report id) stays open through RETURNED.
- A partial approval approves the kept lines and moves the returned lines to a child report (`parent_report_id`) with its own workflow and payout. The `PAYOUT` row is written with its rail before any call, and the rail switches only after the first one confirms it did not pay. An ACH return re-pays as a new `PAYOUT_ATTEMPT` under the same `PAYOUT` row.

### D8b. Rule version

Versions are immutable: an edit after publish is a new version and the old one is superseded. A new counter dimension stays in Shadow until its backfill completes.

```mermaid
%% D8b: one rule version from draft to superseded. No path reaches Enforced without a type-check and a 90-day simulation. At most one version per policy waits in Scheduled.
stateDiagram-v2
    direction LR
    [*] --> Draft: create or edit
    Draft --> Draft: type error
    Draft --> Validated: type-check ok
    Validated --> Draft: edited
    Validated --> Simulated: 90-day sim done
    Simulated --> Draft: edited, sim stale
    Simulated --> Scheduled: publish, future date
    Scheduled --> Enforced: effective_from reached
    Scheduled --> Draft: immediate publish
    Simulated --> Shadow: publish SHADOW
    Simulated --> Enforced: publish ENFORCE
    Shadow --> Enforced: promote, backfill done
    Shadow --> Superseded: new version
    Enforced --> Superseded: new version or rollback
    Superseded --> [*]: bundle kept 7 years
```

- Publish is compare-and-set on `base_version`, and `effective_from` never decreases as versions rise; there is no backdating. An immediate publish cancels the scheduled version or rebases it, which sends it back through simulation.

## D9. Deployment / topology

Two regions, three AZs each. Cluster 1 is drawn in full: a primary, two synchronous standby candidates in the other two AZs, one async replica in the other region. Clusters 2 to 4 have the same shape, primaries split between regions.

```mermaid
%% D9: where each piece runs. Dashed edges cross a region boundary. No row lock and no synchronous commit ever crosses one.
flowchart LR
    PROC[Card network +<br/>issuer processor]:::external -->|"sync auth"| GA1
    PROC -->|"sync auth"| GB
    subgraph RA[Region A, home of clusters 1 and 2]
        subgraph AZA[AZ a]
            GA1[Gateway + decision pods,<br/>Kafka broker, Redis primary]:::service
            P1[(Cluster 1 primary)]:::critical
        end
        subgraph AZB[AZ b]
            GA2[Gateway + decision pods,<br/>Kafka broker, Redis replica]:::service
            S1[(Sync standby candidate 1)]:::store
        end
        subgraph AZC[AZ c]
            S2[(Sync standby candidate 2)]:::store
        end
    end
    subgraph RB[Region B, home of clusters 3 and 4]
        GB[Gateway 6 + decision 6 pods,<br/>Kafka, Redis, over 3 AZs]:::service
        R1[(Cluster 1 async replica)]:::store
    end
    DIR[(Shard directory<br/>cluster epoch)]:::store
    OBJ[(Bundle store + decision lake<br/>multi-region object storage)]:::store
    GA1 -->|"counter txn, same AZ"| P1
    GA2 -->|"counter txn, cross-AZ"| P1
    P1 -->|"sync WAL, ANY 1 of 2"| S1
    P1 -->|"sync WAL, ANY 1 of 2"| S2
    P1 -.->|"async WAL, ~1 s lag"| R1
    GB -.->|"evaluate forwarded once, card-events<br/>to the home-region topic"| GA2
    DIR -.->|"region loss: fence old primary,<br/>epoch + 1, then promote"| R1
    OBJ -.->|"bundles on LRU miss"| GA1
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

- 4 instances per cluster, 16 in all. With one sync candidate, losing it would stop every commit; with `ANY 1 (standby_az2, standby_az3)` either one acks. Pods from solution §10.3: gateway 6 and decision service 6 per region, each region sized for the full 2k/s alone.
- **Crosses a region:** async WAL (RPO, recovery point objective, ~1 s of data; the degraded window is minutes), `policy-activated` and bundles, CDC to the lake, an auth for a tenant homed elsewhere (forwarded once as one RPC, never a remote multi-statement transaction), and card-events produced to the home region's topic. After promotion, only authorizations and transactions changed since the replica's last applied time minus a margin are re-synced from the processor, diffed both ways; decisions lost in the RPO window are rebuilt from processor records and marked `facts_lost`.

## D10. Scaling / partitioning

Tenant to logical shard to cluster. The directory lets one tenant move alone. Red is one row, not a shard.

```mermaid
%% D10: directory-based placement. 16 logical shards on 4 clusters, a quarter of traffic each. The hottest counter is a company-wide cap at the 100k tenant.
flowchart LR
    AUTH[Auth for card c_91]:::client -->|"card map gives tenant t_42"| DIR[(Shard directory<br/>50k tenants to 16 shards)]:::store
    DIR -->|"tenant to shard"| L1[(Logical shards 0 to 3)]:::store
    DIR -->|"tenant to shard"| L2[(Logical shards 4 to 7)]:::store
    DIR -->|"tenant to shard"| L3[(Logical shards 8 to 11)]:::store
    DIR -->|"tenant to shard"| L4[(Logical shards 12 to 15)]:::store
    L1 -->|"~500 txn/s peak"| C1[(Cluster 1<br/>~12.5k tenants)]:::store
    L2 -->|"~500 txn/s peak"| C2[(Cluster 2<br/>~12.5k tenants)]:::store
    L3 -->|"~500 txn/s peak"| C3[(Cluster 3<br/>~12.5k tenants)]:::store
    L4 -->|"~500 txn/s peak"| C4[(Cluster 4<br/>~12.5k tenants)]:::store
    BIG[Largest tenant<br/>100k employees, 5k rules]:::client -->|"moved alone, logical replication<br/>then directory flip"| L4
    C4 -->|"one row, lock held ~4 ms p50"| HOT[Company-wide month cap<br/>~23/s peak vs ~250/s at p50]:::critical
    HOT -.->|"only above ~100/s"| ESC{Escrow slices<br/>the seam, not built}:::decision
    GROW{About 20x volume}:::decision -.->|"move logical shards<br/>to more clusters"| C1
    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

- Per cluster: ~12.5k tenants, ~500 txn/s at peak. Per logical shard: counters ~0.4 GB, holds ~0.06 GB, hot AUTH and CAPTURE decisions ~170 GB. The lock is held from `SELECT ... FOR UPDATE` to `COMMIT` (two round trips plus the synchronous commit), so the hottest row runs at ~10% utilization. Escrow (O'Neil 1986) spends local slices of the remaining budget; at 23/s it buys nothing. See [`../../concepts/sharding.md`](../../concepts/sharding.md).

## D11. Failure mode map

Component, what fails, blast radius, mitigation. Split in two to stay under 15 nodes each. Not drawn: a gateway or decision pod dying costs only its in-flight requests, retried idempotently (D5a); losing one sync standby costs nothing, the other candidate acks. If the decision service itself is unreachable, the gateway uses each card's cached static controls plus the degraded cap.

### D11a. Auth path

```mermaid
%% D11a: failures on the synchronous path. The counter cluster is red: it fails first, and it has the most fallback layers. Credit exposure fails closed through a per-pod escrow slice.
flowchart TD
    AP[Auth path]:::service --> F1[Counter cluster<br/>primary dies]:::critical
    AP --> F2[Employee context<br/>Redis down]:::decision
    AP --> F3[Whole service<br/>unreachable]:::decision
    AP --> F4[Region lost]:::decision
    F1 -->|"blast radius"| B1[1/4 of tenants, ~300/s,<br/>~20 s of failover]:::client
    F2 -->|"blast radius"| B2[scope from local caches,<br/>stale-if-error up to 24 h]:::client
    F3 -->|"blast radius"| B3[every tenant, the processor<br/>decides alone]:::client
    F4 -->|"blast radius"| B4[tenants homed there, RPO ~1 s,<br/>degraded for minutes]:::client
    B1 -->|"mitigation"| M1[point rules, $500 cap, per-card<br/>total per pod, adopt via journal]:::service
    B2 -->|"mitigation"| M2[decision flagged, termination<br/>frozen at the processor]:::service
    B3 -->|"mitigation"| M3[static controls, timeout approve,<br/>adopt from webhooks, D5c]:::service
    B4 -->|"mitigation"| M4[fence by epoch, promote replica,<br/>re-sync, lost facts marked]:::service
    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

### D11b. Async path and control plane

```mermaid
%% D11b: failures off the synchronous path. Our engine release has the widest blast radius and auto-rolls back. A customer policy is never auto-reverted.
flowchart TD
    CP[Async and control plane]:::service --> F5[Settlement consumer<br/>lags or Kafka down]:::decision
    CP --> F6[Bad policy published]:::decision
    CP --> F7[Bad engine release]:::decision
    CP --> F8[Temporal or payout down]:::decision
    F5 -->|"blast radius"| B5[limits drift, auths<br/>still decided]:::client
    F6 -->|"blast radius"| B6[every card of one<br/>tenant within 5 s]:::client
    F7 -->|"blast radius"| B7[every tenant in the cohort]:::client
    F8 -->|"blast radius"| B8[approvals and payouts wait,<br/>cards unaffected]:::client
    B5 -->|"mitigation"| M5[page at 5 min lag, replay no-op,<br/>journal spools to local disk]:::service
    B6 -->|"mitigation"| M6[type-check, sim, shadow, 3x watch,<br/>rollback ~5 s, bulk waive of flags]:::service
    B7 -->|"mitigation"| M7[24 h shadow diff, cohorts<br/>1, 10, 50, 100 percent, auto-rollback]:::service
    B8 -->|"mitigation"| M8[workflow resumes from history,<br/>PAYOUT row + ledger payment id]:::service
    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

## D12. Rollout / migration

From policy checks inside the monolith to this design, the five phases of [solution §8](solution.md#8-staff-level-notes). Counters are backfilled before the shadow starts, so aggregate diffs are real from its first day. Each milestone is that phase's rollback point. Durations are estimates. In phase 4, static controls go live before the timeout setting flips to approve, or an outage approves without any bound.

```mermaid
%% D12: five migration phases, backfill first, then shadow. Every rollback point is a flag or a setting, never a data migration.
gantt
    title Migration to the rules engine
    dateFormat  YYYY-MM-DD
    axisFormat  %b %d
    section Phase 1 compile and backfill
    Compile existing policies into rules         :p1a, 2026-10-05, 14d
    Backfill counters from 60 days of captures   :p1b, after p1a, 7d
    Rollback point, drop the unused counters     :milestone, m1, after p1b, 0d
    section Phase 2 shadow
    Shadow on live auths, holds dual-written     :p2a, after m1, 21d
    Diff every decision, fix translation bugs    :p2b, after m1, 21d
    Rollback point, shadow flag off              :milestone, m2, after p2a, 0d
    section Phase 3 flip deciding path
    Cohorts 1, 10, 50, 100 percent of tenants    :p3a, after m2, 21d
    Rollback point, per-cohort flag              :milestone, m3, after p3a, 0d
    section Phase 4 processor fallback
    Static controls live, then timeout approve   :p4a, after m3, 10d
    Rollback point, timeout setting back         :milestone, m4, after p4a, 0d
    section Phase 5 delete old path
    Remove old checks from the monolith          :p5a, after m4, 14d
    Rollback point, redeploy tagged old release  :milestone, m5, after p5a, 0d
```
