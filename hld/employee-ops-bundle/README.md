# Employee-ops bundle: event counter, driver pay, termination orchestrator, expense assistant

> One-line answer: four systems built on one rule: **give every fact an identity when it is born, keep it in an immutable log, and derive everything else from that log.** Events carry an SDK-made `event_id`, so ingestion can be at-least-once and billing can still be exact. Driver work is immutable and rates are effective-dated, so pay is recomputed, never edited. Termination steps carry `termination_id:step`, and non-idempotent steps are read back before any retry, so a crash resumes without cancelling a card twice. The assistant's LLM only writes a typed query plan: tenant scope is added by code, numbers come from the database, and only validated results are streamed.

Tier 3, problem #46 in [`hld/README.md`](../README.md). Reported by one Senior+ candidate interviewing with Rippling's AI team (May 2026) as **four separate rounds**. PracHub bundles them as one "hard" system design question. Sources: the [PracHub question page](https://prachub.com/interview-questions/build-reliable-employee-operations-and-expense-intelligence-systems) and the [candidate's interview write-up](https://prachub.com/interview-experiences/rippling-seniorplus-software-engineer-interview-experience-phone-screens-plus-a-four-part-ai-team-onsite-building-a-live-llm-chatbot). Siblings: [`payments-ledger/`](../payments-ledger/) (#8) for money, [`distributed-job-scheduler/`](../distributed-job-scheduler/) (#6) for persisted DAGs, [`ai-gateway/`](../ai-gateway/) (#43) for the LLM plumbing, [`streaming-ingestion/`](../streaming-ingestion/) (#18) for the event log. #32 `integration-platform/` (todo) is the general version of the termination orchestrator's connectors.

## How it was asked

| Round | Format | Prompt (candidate's words, condensed) |
|---|---|---|
| Tech screen | System design, 60 min | Design a counter like a Prometheus or Datadog counter. Mobile and web SDKs send events. A phone that was offline sends a big batch at once. No event can be lost. Events are duplicated and delayed. Roll up onto a dashboard (freshness a few dozen minutes), and compute billing and total event counts every month. Every event has tags: timestamp, department, project, others |
| Onsite coding | OOP + tests, 60 min, 2 levels | Driver work hours and pay. Add a driver with an hourly rate, record a completed trip, compute total payout. Clarify overlapping time ranges, how a rate change affects work before and after it, time and money formats. Level 2 (not announced in advance): which wages were paid and when, and which were not. "I had to go back and rework my own class model" |
| Onsite design | System design, 60 min | One endpoint terminates an employee. Behind it, 7 to 10 systems: cancel the credit card, deactivate accounts, schedule final pay, revoke email and Slack, transfer data, wipe the phone. Some cannot be retried (a card cannot be cancelled twice), some must go first, some run in parallel, some have priority, some support sagas, some have webhooks. Correctness and completeness over traffic, but minimize completion time and resume automatically after a crash |
| Onsite build | Practical coding, 90 min, AI allowed and watched | An LLM chatbot answering questions about employee expenses. Frontend given. Two large JSON files: companies and employees, and expense records. Level 1: basic questions plus API design. Level 2: aggregations (which company, employee, department reported the most, and when). Level 3 unseen. Discuss several LLM passes vs an agent. Implement streaming. Write the prompts yourself |

PracHub's added constraints: late or duplicate events "cannot be silently lost"; "monthly billing must reconcile exactly"; the assistant "must enforce company and employee data boundaries before model access". Hint: "Separate approximate serving from exact ledgers." Follow-ups: a 100-fold event increase, and "how would you prove that a termination workflow is complete?"

## Functional requirements

Core:
1. **Ingest** tagged events from mobile and web SDKs: batches, offline backlogs, retries. An acknowledged event is never lost.
2. **Dashboards**: counts by event name and any tag over time, at most 30 minutes behind for online devices.
3. **Monthly billing**: an exact, reproducible count of billable events per customer per period.
4. **Driver pay**: drivers, effective-dated hourly rates, completed jobs with time spans, accrued / paid / unpaid amounts, and a payout call. History is never rewritten.
5. **Termination**: one call that runs 7 to 12 dependent revocation and payout actions across external systems. It resumes after any crash and ends in a provable "complete".
6. **Expense assistant**: a plain-English question becomes a safe, tenant-scoped structured query. It supports aggregates and streams the answer.

Below the line: the payroll engine itself (#29), the integration platform in general (#32), identity provisioning on hire, the expense-policy rules engine (#31), and LLM hosting (#43).

## Non-functional requirements

| Part | Target |
|---|---|
| Event ingest | 1 B events/day, 116k/s peak, 350k/s admission cap for reconnect storms. Ack only after a durable write (Kafka `acks=all`, 2 in-sync replicas). p99 ack < 300 ms |
| Dashboards | p99 freshness < 5 min for online devices, 30 min budget. Approximate until the day closes, then corrected to the billing count |
| Billing | Exact: every accepted event billed exactly once, reproducible from the raw log, reconciled to Kafka offsets. Period closes at 00:00 UTC + 15 min |
| Driver pay | Integer money, no double pay for the same seconds, idempotent payouts, strong consistency per driver |
| Termination | Access revoked (P0 steps) p99 < 5 min. Fully closed (every step terminal) p99 < 7 days, bounded by device check-in and final-pay dates. Resume < 1 min after a crash. Zero double execution of non-idempotent steps |
| Assistant | Zero cross-tenant or out-of-scope rows reach the model or the user. Aggregates computed by the database, never by the model. First useful output < 2 s, full answer p95 < 6 s |

## What interviewers probe (the ladder)

1. A phone was offline 3 days and uploads 20,000 events, then the upload times out and it retries. What do you ack, where do you dedup, and why not at the API?
2. Which month does a late event bill to? What makes the monthly count exact, and how do you prove it to a customer?
3. Events jump 100x. What breaks first?
4. A driver has two overlapping trips and the rate changed in the middle of one. What do you pay? Now pay up to Friday, then a late trip arrives for Wednesday.
5. The orchestrator crashes after calling "cancel card" and before saving the result. What happens on resume?
6. 5,000 employees are laid off at 09:00. Which box breaks first?
7. How do you prove a termination is complete? What about an account created while the workflow ran?
8. How do you guarantee tenant A's rows never reach the model for tenant B's user? The model writes SQL: why not?
9. When do you use a fixed pipeline and when an agent? How do you stream without leaking a half-validated answer?

## Files

| File | What it is |
|---|---|
| [`solution.md`](solution.md) | Full HLD in flow-first form: one section per part, deep dives that mutate the design, final design with the core flows, nitty-gritty |
| [`diagrams.md`](diagrams.md) | The D1 to D12 diagram set |
| [`edge-cases.md`](edge-cases.md) | Every "what if" with a 60-second answer and a confidence box |
| [`deep-dives/event-ingestion-dedup-and-late-data.md`](deep-dives/event-ingestion-dedup-and-late-data.md) | SDK queue, durable ack, where dedup goes, clock skew, late events, reconnect storms |
| [`deep-dives/exact-billing-and-reconciliation.md`](deep-dives/exact-billing-and-reconciliation.md) | Periods as offset ranges, the billing batch, three-way reconciliation, disputes, 100x |
| [`deep-dives/driver-pay-ledger.md`](deep-dives/driver-pay-ledger.md) | The coding round: model, overlap and rate semantics, paid vs unpaid, runnable Java with tests |
| [`deep-dives/termination-workflow-engine.md`](deep-dives/termination-workflow-engine.md) | Persisted DAG, step state machine, scheduling by priority and critical path, resume, layoffs |
| [`deep-dives/non-idempotent-steps-and-completeness.md`](deep-dives/non-idempotent-steps-and-completeness.md) | Idempotency classes per connector, unknown outcomes, webhooks, compensation, proving completeness |
| [`deep-dives/expense-assistant.md`](deep-dives/expense-assistant.md) | The build round: typed plan, scope injection, compile and execute, streaming, pipeline vs agent, runnable Python |
| [`research/facts-survey.md`](research/facts-survey.md) | Verified vendor facts (dedup windows, SCIM, card cancel, token revocation, MDM wipe) with a spot-check corrections table |
| `employee-ops-bundle.excalidraw` | My drawing. Missing until I draw it |
