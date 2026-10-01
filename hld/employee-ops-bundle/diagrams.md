# Diagrams: employee-ops bundle

The D1 to D12 set from `hld/CLAUDE.md` §4, for all four parts. Diagrams already embedded in [`solution.md`](solution.md) get a pointer, not a second copy. Numbers match `solution.md` §2 and §10.3; anything else is marked `[estimate]`.

| # | Diagram | Where |
|---|---|---|
| D1 | Context | below |
| D2 | Data flow, Part 1 and Parts 2 to 4 | below (two diagrams) |
| D3 | Component architecture (final design) | [`solution.md`](solution.md) §6 |
| D4 | Happy path per FR | FR1 ingest: `solution.md` §4.1. FR2 dashboards: below. FR3 billing hour close: `solution.md` §4.3. FR4 record job and payout: below. FR5 termination: below. FR6 assistant question: `solution.md` §5.9 |
| D5 | Failure paths | Crash after cancel card: `solution.md` §5.5. Kafka broker loss: §10.4 A. LLM provider outage: §10.4 C. Archive gap at hour close: §4.3 (the `alt` branch). New below: webhook lost so the poll completes the step, SDK queue full, narrator sentence fails the number check |
| D6 | Decision flows | Step retry rule by idempotency class: below. Ingest accept or reject per event: below. Verifier: `solution.md` §5.7 |
| D7 | Entity relationship | `solution.md` §3.3 (D7a metering and pay, D7b termination and assistant) |
| D8 | State machines (termination step, termination) | below |
| D9 | Deployment / topology | below (Part 1 data plane, Parts 2 to 4) |
| D10 | Scaling / partitioning | below |
| D11 | Failure mode map | below, in two parts |
| D12 | Rollout / migration (Part 3 from a Celery script) | below |
| Zoom-ins | Part 1 incremental steps, reconnect herd, reconciliation chain, 100x index, driver lock, termination DAG, layoff lanes, verifier, data boundary | `solution.md` §4.1 to §4.3, §5.1, §5.2, §5.3, §5.4, §4.5, §5.6, §5.7, §5.8 |

## D1. Context (zoom-out)

The bundle as one box: who sends what in, who we call out to. The four parts and the edges between them are in D3.

```mermaid
%% D1: the employee-ops bundle as one box. Devices and people on the left, vendors and providers we call on the right.
flowchart LR
    DEV[Phones and browsers<br/>10 M devices] -->|"tagged event batches"| B[Employee-ops bundle<br/>event counter, driver pay,<br/>termination orchestrator,<br/>expense assistant]
    CUS[Customer users<br/>admins, managers, employees] <-->|"dashboards, invoices,<br/>questions, streamed answers"| B
    HRO[HR and dispatch ops] -->|"terminate, resolve steps,<br/>jobs, rates, payouts"| B
    B <-->|"SCIM, Admin SDK, issuer,<br/>MDM calls, signed webhooks"| SAAS[Google, Slack, Okta,<br/>card issuer, MDM]
    B -->|"payouts, hourly usage<br/>aggregates"| MONEY[Payments rail, Stripe]
    B <-->|"planner and narrator prompts"| LLM[LLM provider]
    PERM[Permission system<br/>identity platform] -->|"scope per user"| B

    class DEV,CUS,HRO client
    class B service
    class SAAS,MONEY,LLM,PERM external
    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

## D2. Data flow (DFD)

Every edge with data, format, size and rate at peak. Part 1 is the only part where volume matters, so it gets its own diagram.

```mermaid
%% D2a: Part 1 data flow at peak. The raw log is read three ways: speed path, archive, and hourly cuts.
flowchart LR
    SDK[SDKs] -->|"event batch, gzip JSON,<br/>~10 x 300 B, 12k req/s"| ING(Ingest pods x12)
    ING -->|"event record, zstd ~80 B,<br/>116k/s, 80 GB/day"| K[(Kafka events.raw<br/>64 partitions, RF 3)]
    K -->|"records, 116k/s"| FL(Flink rollup)
    FL -->|"minute delta ~50 B,<br/>~17k rows/s [estimate]"| CH[(ClickHouse<br/>~150 M rows/day, ~10 GB)]
    CH -->|"series JSON per query"| DASH(Dashboard API)
    K -->|"records + offset, 116k/s"| ARC(Archive sink)
    ARC -->|"Parquet ~40 B/event,<br/>40 GB/day"| LAKE[(Lake raw_events<br/>13 months, ~16 TB)]
    K -->|"offsetsForTimes,<br/>1 cut map per hour"| CUT(Period cutter)
    CUT -->|"period_cut, 64 rows/hour"| BDB[(Billing Postgres)]
    LAKE -->|"~42 M events/hour avg"| BB(Billing batch)
    BB <-->|"anti-join, 35 days,<br/>560 GB in 1,024 buckets"| IDX[(billable_event)]
    BB -->|"billing_line per tenant-hour,<br/>up to 20k rows/hour"| BDB
    BDB -->|"1 aggregate per tenant-hour,<br/>identifier tenant:hour"| STR[Stripe billing]

    class SDK client
    class ING,FL,DASH,ARC,CUT,BB service
    class K queue
    class CH,LAKE,BDB,IDX store
    class STR external
    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

```mermaid
%% D2b: Parts 2 to 4 data flow. Small volumes; the only burst is the layoff on the connector edge.
flowchart LR
    OPS[Dispatch tools] -->|"job JSON ~150 B,<br/>1.2k/s peak, 10 M/day"| PAY(Driver pay service)
    PAY -->|"~400 B per job with segments,<br/>4 GB/day"| PG[(Pay Postgres)]
    PG -->|"outbox row per payout,<br/>key payout_id"| RAIL[Payments rail]
    HR[HR admins] -->|"termination JSON ~1 KB,<br/>5.5k/day, 5,000 in a layoff"| TE(Termination engine)
    TE -->|"~330k transitions/day,<br/>4/s avg"| WDB[(Workflow DB)]
    TE -->|"final pay call,<br/>key termination_id"| PAY
    TE -->|"165k calls/day, 2/s avg,<br/>10k P0 calls in a layoff"| CON(Connector gateway)
    CON -->|"SCIM, Admin SDK,<br/>issuer, MDM"| EXT[External SaaS]
    EXT -.->|"signed webhooks ~1 KB"| WDB
    UI[Chat UI] -->|"question ~200 B, 10/s peak"| AS(Assistant API)
    AS -->|"planner ~2k in, 150 out,<br/>narrator ~1.5k in, 200 out tokens"| LLM[LLM provider]
    AS -->|"parameterised SQL,<br/>~10 M rows per tenant-year"| EXP[(Expense replica)]
    AS -->|"SSE plan, result,<br/>tokens, done"| UI

    class OPS,HR,UI client
    class PAY,TE,CON,AS service
    class PG,WDB,EXP store
    class RAIL,EXT,LLM external
    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

## D3. Component architecture

The final design with all four parts and the three edges between them: [`solution.md`](solution.md) §6. Red is the connector gateway, whose vendor quota sets the layoff SLO.

## D4. Happy path, one per functional requirement

FR1 (ingest, including the crash-after-ack duplicate) is in `solution.md` §4.1. FR3 (closing a billing hour) is in §4.3. FR6 (one question, streamed) is in §5.9.

**FR2: an event reaches the dashboard in about 1 to 2 minutes.**

```mermaid
%% D4 FR2: the speed path. No watermark. A delta block is cut at each checkpoint and inserted only after that checkpoint completes, with a dedup token.
sequenceDiagram
    autonumber
    participant K as Kafka
    participant D as Flink dedup op
    participant A as Flink rollup op
    participant C as ClickHouse
    participant API as Dashboard API
    participant U as Dashboard UI
    K->>D: record, key tenant 42 + device 9f1
    D->>D: event_id seen in last 48 h? no, keep it
    D->>D: corrected ts, clock_suspect placed at received_at, tagset_hash
    D->>A: re-key tenant, name, tagset, minute
    A->>A: add 1 to bucket 10:41
    Note over A,C: checkpoint barrier arrives, every 60 s, block of deltas cut into state
    A->>A: checkpoint 5120 completes
    A->>C: insert the block, token = subtask 3 + checkpoint 5120
    C-->>A: ok, a replay of the same token is dropped
    Note over C: background merges sum rows with the same key
    U->>API: GET /v1/metrics group_by department, last 24 h
    API->>C: SELECT sum(count) WHERE tenant_id = 42 from the session
    C-->>API: rows per minute and department
    API-->>U: series + provisional_from
```

**FR4: record two overlapping jobs, then pay up to 11:30.** Numbers from `solution.md` §5.4.

```mermaid
%% D4 FR4: record job and payout. One driver row lock per transaction, integer cent-seconds, payout keyed by payout_id.
sequenceDiagram
    autonumber
    participant O as Ops tool
    participant S as Pay service
    participant P as Postgres
    participant R as Outbox relay
    participant M as Payments rail
    O->>S: POST /jobs A, 09:00 to 11:00
    S->>P: BEGIN, SELECT driver D FOR UPDATE
    S->>P: insert job A, unique job_id
    S->>P: read D's jobs overlapping 09:00 to 11:00, none
    S->>P: insert A1 09:00-10:30 at 2,000 and A2 10:30-11:00 at 3,000, COMMIT
    S-->>O: 201, 3,000 + 1,500 cents
    O->>S: POST /jobs B, 10:00 to 12:00
    S->>P: lock D, new coverage is only 11:00 to 12:00
    S->>P: insert B1 11:00-12:00 at 3,000, COMMIT
    O->>S: POST /payouts P1, up_to 11:30
    S->>P: lock D, payout_id P1 is new
    S->>P: unpaid pieces A1, A2, B1 11:00-11:30, 21.6 M cent-seconds + carry 0
    S->>P: insert payout 6,000 cents, carry 0, 3 allocations, outbox row, COMMIT
    S-->>O: 200, 6,000 cents
    R->>P: poll outbox
    R->>M: pay 6,000 cents, idempotency key P1
    M-->>R: accepted
    R->>P: mark outbox row sent
```

**FR5: involuntary termination, P0 and P1 done in about 10 to 20 seconds.**

```mermaid
%% D4 FR5: one termination, happy path. Identity first, then parallel P0 and P1 steps with read-back evidence.
sequenceDiagram
    autonumber
    participant HR as HR admin
    participant T as Termination API
    participant W as Workflow DB
    participant E as Engine
    participant IDP as Rippling IdP
    participant G as Google via gateway
    participant CI as Card issuer
    HR->>T: POST /terminations, key k-77, involuntary, now
    T->>W: insert termination + 11 steps + verifier, one txn, plan frozen
    T-->>HR: 202, termination_id t-5
    E->>W: take lease, owner_epoch 1, S1 READY
    E->>IDP: S1 disable identity
    IDP-->>E: ok in ~50 ms, every SSO login now fails
    E->>W: S1 SUCCEEDED, S2 to S6 and S8, S9 READY
    par P0 sessions
        E->>G: S2 suspended=true + signOut, key t-5:S2
        G-->>E: 200
        E->>G: read back user, suspended=true
        Note over E,G: S2 also resets Slack and Okta sessions through their connectors
    and P1 card
        E->>CI: S5 freeze card, key t-5:S5
        CI-->>E: inactive
    end
    E->>W: S2, S5 SUCCEEDED with evidence, S3 mail routing to manager next, ~10 to 20 s
    Note over E,W: S7 Drive transfer, S8 wipe, S9 final pay run async. S10 cancel after S5 and after pending authorizations clear, past the point of no return. S11 delete at +30 days.
    E->>W: verifier re-lists apps, waits out token lifetime, seals hash chain
    E->>W: termination COMPLETE
```

## D5. Failure paths

Already in `solution.md`: crash after cancel card (§5.5), Kafka broker loss (§10.4 A), LLM provider outage (§10.4 C), archive gap at hour close (§4.3). Three more:

**The completion webhook is lost; the poll finishes the step.**

```mermaid
%% D5a: webhook lost during our deploy. The poll timer is the backstop, and the late redelivery is dropped by the inbox.
sequenceDiagram
    autonumber
    participant E as Engine
    participant M as MDM server
    participant WH as Webhook receiver
    participant W as Workflow DB
    E->>M: S8 wipe device, correlation c-77
    M-->>E: 202 queued until check-in
    E->>W: S8 WAITING, poll timer in 15 min, backing off
    Note over M: hours later the phone checks in and the wipe runs
    M->>WH: webhook wipe acknowledged, event ev-9
    WH-->>M: 503, receiver mid-deploy, provider gives up
    E->>M: poll timer fires, GET command c-77
    M-->>E: acknowledged
    E->>W: S8 SUCCEEDED, evidence = status read
    M->>WH: manual redelivery of ev-9 a day later
    WH->>W: insert inbox (mdm, ev-9), new row
    W-->>WH: step c-77 already terminal, no transition
```

**A phone is offline for 45 days; the SDK queue caps out and the loss stays visible.**

```mermaid
%% D5b: SDK queue full. Oldest events are dropped and counted, and the count is itself sent as an event.
sequenceDiagram
    autonumber
    participant APP as App
    participant S as SDK queue
    participant I as Ingest pod
    APP->>S: track events for 45 days, no network
    Note over S: cap is 20,000 events or 30 days
    S->>S: day 31 on, drop events older than 30 days, dropped_events += n
    S->>S: queue at 20,000, drop oldest, dropped_events += 1 per drop
    APP->>S: network back
    S->>I: live lane first, last 5 minutes
    I-->>S: 200, all accepted
    S->>I: backlog oldest first, 500 per request, 40 requests
    I-->>S: 200, any event older than 30 days by corrected time rejected too_old
    S->>I: event sdk.dropped_events with the count, own event_id
    I-->>S: 200, accepted
    Note over S,I: The tenant's dashboard shows the drops. The loss is loud, not silent.
```

**The narrator writes a number that is not in the result.**

```mermaid
%% D5c: the sentence guard. A held sentence with an unknown number is never sent. The template summary replaces the narrative.
sequenceDiagram
    autonumber
    participant U as Chat UI
    participant A as Assistant API
    participant M as LLM narrator
    A-->>U: event result, Sales 4,120,000 cents, Ops 3,895,000 cents
    A->>M: narrator prompt, plan + 2 rows
    M-->>A: tokens, Sales led travel spending with $41,200.
    A->>A: sentence complete, 41,200 is in the rows
    A-->>U: event token, sentence 1
    M-->>A: tokens, Ops followed with $38,590.
    A->>A: 38,590 is not in the rows, hold the sentence
    A->>M: abort the stream
    A-->>U: event token, template summary, Sales $41,200, Ops $38,950
    A-->>U: event done, narrative_replaced = true
    Note over U,A: The table was already final. Only the prose changed. The miss is logged for the eval set.
```

## D6. Decision flows

**(a) What happens after an attempt, by idempotency class** (`solution.md` §5.5).

```mermaid
%% D6a: the step retry rule. The class decides whether a retry is safe, a read-back is needed, or a human must decide.
flowchart TD
    O{Attempt outcome} -->|"success"| SUCC[SUCCEEDED + evidence]
    O -->|"async accepted"| WAIT[WAITING, correlation id]
    O -->|"permanent error"| E{Error means<br/>already done?}
    E -->|"yes, e.g. already canceled"| SUCC
    E -->|"no"| FAIL[FAILED, operator]
    O -->|"timeout, crash, transient"| C{Idempotency class}
    C -->|"natural"| CAP{10 attempts used?}
    C -->|"keyed"| K{First attempt<br/>under 24 h old?}
    K -->|"yes, same key"| CAP
    K -->|"no, key may be pruned"| RB[Read target state]
    C -->|"readable"| RB
    RB -->|"done"| SUCC
    RB -->|"not done"| CAP
    C -->|"unreadable"| UNK[UNKNOWN, operator,<br/>never auto-retry]
    CAP -->|"no"| RT[RETRY_WAIT,<br/>1 s to 100 s backoff]
    CAP -->|"yes"| FAIL

    class O,E,C,K,CAP decision
    class SUCC,WAIT,RB,RT service
    class FAIL,UNK critical
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
```

Red here marks the two exits that need a human; they are what the P0 page watches.

**(b) Ingest: accept or reject, per batch then per event** (`solution.md` §4.1).

```mermaid
%% D6b: the ingest pod's decision per request and per event. Rejections are per event with a reason; only auth, size and rate reject a whole batch.
flowchart TD
    A{SDK key valid,<br/>write scope?} -->|"no"| R401[401, whole batch]
    A -->|"yes"| B{At most 500 events<br/>and 512 KB?}
    B -->|"no"| R413[413, SDK splits]
    B -->|"yes"| T{Tenant event<br/>bucket has room?}
    T -->|"no"| R429[429 + jittered Retry-After,<br/>SDK keeps rows]
    T -->|"yes, per event"| S{Schema valid?}
    S -->|"no, invalid"| RJ[Reject this event<br/>with its reason]
    S -->|"yes"| G{At most 20 tag keys?}
    G -->|"no, tag_limit"| RJ
    G -->|"yes"| AGE{Corrected age<br/>at most 30 days?}
    AGE -->|"no, too_old"| RJ
    AGE -->|"yes, flag clock_suspect<br/>if over 5 min ahead"| P[Produce, acks=all]
    P --> PK{Kafka ack?}
    PK -->|"no"| R503[503, SDK retries batch]
    PK -->|"yes"| OK[200, accepted]

    class A,B,T,S,G,AGE,PK decision
    class P,OK,RJ service
    class R401,R413,R429,R503 client
    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

## D7. Entity relationship

Both ER diagrams (D7a metering and driver pay, D7b termination and assistant) are in `solution.md` §3.3 with their access patterns.

## D8. State machines

**Termination step.** Terminal states are grouped; the two operator states are grouped.

```mermaid
%% D8a: one termination step. Only the two operator states need a human. Compensation exists only when HR cancels.
stateDiagram-v2
    direction LR
    [*] --> PENDING
    PENDING --> READY: deps done
    READY --> IN_FLIGHT: dispatched
    IN_FLIGHT --> WAITING: async accepted
    IN_FLIGHT --> RETRY_WAIT: transient error
    IN_FLIGHT --> READY: resume, not done
    RETRY_WAIT --> READY: backoff due
    state "Needs operator" as OPER {
        direction TB
        FAILED
        UNKNOWN
    }
    IN_FLIGHT --> OPER: permanent or unreadable
    RETRY_WAIT --> OPER: 10 attempts
    WAITING --> OPER: timeout
    OPER --> READY: operator retry
    state "Terminal" as TERM {
        direction TB
        SUCCEEDED
        SKIPPED
        RESOLVED
    }
    PENDING --> TERM: no account, skip
    IN_FLIGHT --> TERM: done or read-back done
    WAITING --> TERM: webhook or poll
    OPER --> TERM: resolve or skip
    TERM --> COMPENSATED: HR cancels
    TERM --> [*]
```

`COMPENSATED` applies only to reversible steps that `SUCCEEDED` (freeze, suspend, deactivate), and only before the point of no return.

**Termination.**

```mermaid
%% D8b: one termination. Cancel is allowed until the point of no return. A sweep hit reopens a completed termination.
stateDiagram-v2
    direction LR
    [*] --> PLANNED: plan frozen
    PLANNED --> SCHEDULED: effective_at later
    PLANNED --> RUNNING: involuntary, now
    SCHEDULED --> RUNNING: effective_at
    SCHEDULED --> CANCELLED: HR cancels
    RUNNING --> COMPENSATING: cancel before PONR
    COMPENSATING --> CANCELLED: undo done
    RUNNING --> VERIFYING: all steps terminal
    VERIFYING --> RUNNING: drift, new step
    VERIFYING --> COMPLETE: read-back ok
    COMPLETE --> RUNNING: sweep finds account
    COMPLETE --> [*]
    CANCELLED --> [*]
```

PONR is the point of no return: `effective_at + 24 h` for voluntary terminations. After it, `POST /cancel` is refused. `VERIFYING` includes the wait until the maximum token lifetime (90 min) has passed.

## D9. Deployment / topology

One region, three availability zones. Everything is regional; only the vendors (SaaS, LLM, payments) are global and outside our boundary.

**Part 1 data plane.**

```mermaid
%% D9a: Part 1 across 3 AZs. Kafka RF 3 with one replica per AZ and min ISR 2, so an ack survives one AZ loss.
flowchart LR
    LB[Regional load balancer] -->|"batches, spread"| IA
    LB -->|"batches"| IB
    LB -->|"batches"| IC
    subgraph AZA[AZ a]
        IA[Ingest pods x4]
        KA[(Kafka broker a)]
        SA[Flink TMs +<br/>ClickHouse replica a]
    end
    subgraph AZB[AZ b]
        IB[Ingest pods x4]
        KB[(Kafka broker b)]
        SB[Flink TMs +<br/>ClickHouse replica b]
    end
    subgraph AZC[AZ c]
        IC[Ingest pods x4]
        KC[(Kafka broker c)]
        SC[Flink TMs +<br/>ClickHouse replica c]
    end
    IA -->|"produce to leaders"| KA
    IB -->|"produce to leaders"| KB
    IC -->|"produce to leaders"| KC
    KA <-->|"follower fetch, RF 3"| KB
    KB <-->|"follower fetch, RF 3"| KC
    KA -->|"consume"| SA
    KB -->|"consume"| SB
    KC -->|"consume"| SC
    KB -->|"archive sink, Parquet"| LAKE[(S3 lake, regional)]
    LAKE -->|"hourly, ~30 min per hour"| BAT[Billing batch cluster]

    class LB client
    class IA,IB,IC,SA,SB,SC,BAT service
    class KA,KB,KC queue
    class LAKE store
    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
```

Ingest pods produce to whichever broker leads each partition, in any AZ; the per-AZ arrows are simplified. With `min.insync.replicas=2`, losing one AZ keeps every partition writable.

**Parts 2 to 4.**

```mermaid
%% D9b: Parts 2 to 4. Stateless pods in every AZ, Postgres primaries in one AZ with a synchronous standby in another. Engine leases move across AZs, fenced by epoch.
flowchart LR
    LB[Regional load balancer] -->|"API calls"| AA
    LB -->|"API calls"| AB
    LB -->|"API calls"| AC
    subgraph AZA[AZ a]
        AA[Pods a: pay, engine,<br/>workers, gateway, assistant]
        PA[(Postgres primaries<br/>pay, workflow, billing ledger)]
    end
    subgraph AZB[AZ b]
        AB[Pods b: same set]
        PB[(Synchronous standbys)]
    end
    subgraph AZC[AZ c]
        AC[Pods c: same set]
        RC[(Expense read replica<br/>for the assistant)]
    end
    AA -->|"writes"| PA
    AB -->|"writes, cross-AZ"| PA
    AC -->|"writes, cross-AZ"| PA
    PA -->|"sync replication"| PB
    AC -->|"scoped SQL"| RC
    AA -->|"connector calls"| EXT[SaaS vendors,<br/>payments rail, LLM]

    class LB client
    class AA,AB,AC service
    class PA,PB,RC store
    class EXT external
    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

Losing AZ a: the standby in AZ b is promoted, engine leases expire in 30 s and are taken by pods in b or c with `epoch + 1`. The expense replica is fed from the expense product's own database, which another team owns.

## D10. Scaling / partitioning

```mermaid
%% D10: how each part is keyed. Red = the billing dedup index at 100x, the first thing to break when events grow.
flowchart LR
    TEN[20k tenants,<br/>10 M devices] -->|"key = hash tenant + device"| K[(events.raw<br/>64 partitions)]
    K -->|"same key, copies meet"| OP1[Flink dedup op<br/>48 h ids per key]
    OP1 -->|"re-key tenant, name,<br/>tagset, minute"| OP2[Flink rollup op]
    OP2 -->|"sort key tenant,<br/>name, minute"| CH[(ClickHouse)]
    K -->|"offset ranges per hour"| BB[Billing batch]
    BB -->|"bucket = hash event_id<br/>mod 1,024"| IDX[(billable_event<br/>560 GB, ~550 MB per bucket)]
    IDX -.->|"at 100x"| BIG[3.5 T ids, ~56 TB,<br/>hourly anti-join too big]
    BIG -->|"fix"| DD[Keyed dedup stage<br/>~1,000 partitions,<br/>RocksDB + Bloom, 10-day ids]
    PAY[Driver pay] -->|"one primary now,<br/>shard by driver_id at 10x"| PGS[(Pay Postgres)]
    WF[Termination engine] -->|"one Postgres,<br/>key termination_id"| WDB[(Workflow DB)]

    class TEN client
    class OP1,OP2,BB,DD,PAY,WF service
    class K queue
    class CH,IDX,PGS,WDB store
    class BIG critical
    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
```

Hot keys: because the Kafka key includes the device, one big tenant spreads over all 64 partitions. One device's 20,000-event backlog lands on one partition, but arrives as 40 requests of 500. Parts 2 and 3 are too small to need sharding at 1x.

## D11. Failure mode map

Each component, what fails, the blast radius, and the mitigation. Two trees, two parts each.

```mermaid
%% D11a: Parts 1 and 2. Red = the archive sink, the only way billing can undercount, with Kafka's 7-day retention as the repair deadline.
flowchart TD
    P1[Part 1 event counter] --> F1[Ingest pods down]
    F1 -->|"SDKs queue, charts stall"| M1[Local queue, jittered retry,<br/>admission on recovery]
    P1 --> F2[Kafka broker lost]
    F2 -->|"acks delayed on its partitions"| M2[RF 3, min ISR 2,<br/>no unclean election]
    P1 --> F3[Flink rollup fails]
    F3 -->|"charts only"| M3[Restart from checkpoint,<br/>insert dedup tokens]
    P1 --> F4[Archive sink gap]
    F4 -->|"billing hour cannot close"| M4[Reconciler pages in 1 h,<br/>re-archive within 7 days]
    P2[Part 2 driver pay] --> F5[Postgres primary lost]
    F5 -->|"job and payout writes fail, minutes"| M5[Sync standby failover,<br/>retries by job_id, payout_id]
    P2 --> F6[Driver lock skipped by a bug]
    F6 -->|"overlap paid twice"| M6[Reconcile API alerts<br/>on any difference]

    class P1,P2 client
    class F1,F2,F3,F5,F6 decision
    class F4 critical
    class M1,M2,M3,M4,M5,M6 service
    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
```

```mermaid
%% D11b: Parts 3 and 4. Red = the connector quota, which sets the layoff revocation SLO.
flowchart TD
    P3[Part 3 termination] --> G1[Engine instance dies]
    G1 -->|"its terminations pause ~40 s"| N1[Lease takeover,<br/>epoch fencing]
    P3 --> G2[Connector quota in a layoff]
    G2 -->|"P0 external calls 5.3 min for 5,000"| N2[P0 lane first, plans built<br/>the day before, quota raise]
    P3 --> G3[Vendor API down]
    G3 -->|"that vendor's steps wait,<br/>SSO already off"| N3[Backoff, escalate P0 after 1 h]
    P3 --> G4[Webhook lost]
    G4 -->|"step stuck WAITING"| N4[Poll timer backstop]
    P4[Part 4 assistant] --> G5[LLM provider down]
    G5 -->|"assistant only"| N5[Fallback model, plan cache,<br/>manual plan builder]
    P4 --> G6[Permission system down]
    G6 -->|"no answers"| N6[Fail closed]

    class P3,P4 client
    class G1,G3,G4,G5,G6 decision
    class G2 critical
    class N1,N2,N3,N4,N5,N6 service
    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
```

Not drawn, same shape: a stale scope cache (rows visible up to 60 s after a role change, invalidation events), expense replica lag (answer says "as of"), the billing batch failing (invoices late, deterministic rerun).

## D12. Rollout / migration: Part 3 from a Celery offboarding script

The likely starting point is a script that calls vendor APIs in order. Each phase has a rollback point; the old script stays runnable until the last phase ends. `[estimate]` durations.

```mermaid
%% D12: migrating terminations from a Celery script to the persisted DAG engine. Idempotent connectors cut over first, non-idempotent ones last.
gantt
    title Termination engine migration
    dateFormat YYYY-MM-DD
    axisFormat %b %d
    section Build
    Connector registry and capability schema :b1, 2026-10-05, 14d
    Engine, workflow DB, verifier            :b2, after b1, 14d
    section Shadow
    Plan plus read-only verifier beside Celery for 4 weeks :s1, after b2, 28d
    Rollback point, turn shadow off, no user effect :milestone, r1, after s1, 0d
    section Idempotent connectors
    Google suspend, Slack SCIM, Okta, GitHub by flag :i1, after s1, 14d
    Rollback point, per-connector flag to Celery :milestone, r2, after i1, 0d
    section Keyed connectors
    Payroll final pay, Stripe Issuing freeze :k1, after i1, 14d
    Rollback point, flag back per connector :milestone, r3, after k1, 0d
    section Non-idempotent connectors
    Card cancel, MDM wipe, with read-back guards :crit, n1, after k1, 14d
    Rollback point, flag back per connector :milestone, r4, after n1, 0d
    section Decommission
    Celery script read-only for 30 days, then removed :d1, after n1, 30d
```

Shadow exit criteria: the verifier's view matches what the script did for every termination in 4 weeks, and every connector in the registry has its idempotency class tested against the vendor's sandbox. In-flight terminations keep their frozen `plan_version` across every flag flip.
