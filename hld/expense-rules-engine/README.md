# Expense / corporate card rules engine (with reimbursement)

> One-line answer: admins write spend policy as **rules that are data** (a JSON envelope for scope, aggregate and action, plus a typed, non-Turing-complete predicate). A compiler turns each tenant's rules into an immutable, versioned bundle, and **one engine library** evaluates it in three places: synchronously on every card authorization (about 15 ms p50 as the processor sees it, against its 2 s deadline), when a card transaction clears, and when an employee submits an out-of-pocket expense. Point rules are pure functions evaluated in process. Aggregate rules (card, employee, department and trip limits) lock their counter rows in a tenant-sharded Postgres, evaluate, and write **holds**, so two concurrent swipes can never both break a limit. Holds turn into spend at capture. Every decision returns a structured result (outcome, every rule's verdict with observed vs limit, policy and engine version) and is logged with its inputs, so it can be explained and replayed for 7 years. Rule changes are type-checked, simulated against 90 days of history, optionally shadowed, and stamped with a version. When our engine is down, coarse static controls pushed to the card processor keep cards usable within bounds.

Tier 3, problem #31 in [`hld/README.md`](../README.md). Asked at Rippling as a phone-screen coding prompt (`evaluateRules(rules, expenses)`, "discuss the return type", then "rule creation via an API") and as "now scale it" system design. Same shape as Ramp or Brex spend controls, Stripe Radar rules, and any "design a rules engine" prompt. Sources and prompt wording: [`../company-questions.md`](../company-questions.md) §2.3 and [`research/`](research/).

## Problem statement (as asked)

Employees spend company money two ways: on a **corporate card**, and **out of pocket**, then ask to be reimbursed. Each company sets spend policy: "no restaurant expense over $75", "no airfare", "no entertainment", "no single expense over $250", "a trip may total at most $2,000", "meals at most $200 per trip". Build the engine that evaluates expenses against the rules and says what is wrong with each one. Then: let admins add new rule types through an API, run it for every Rippling customer, and decide card swipes in real time.

Follow-ups that always come: what the evaluate call returns; per-trip and per-month totals when two swipes land at once; the card network deadline and what happens when you miss it; a rule change that declines every card in a company; "why was my card declined?" six months later; the tip that pushes a $70 dinner over $75.

## Functional requirements

Core:
- **Define policy.** Admins create, edit, version and scope rules (by department, level, country, card program) through a UI and an API. Point rules and aggregate rules. Actions: decline, require approval, flag.
- **Evaluate and explain.** `evaluate(expense, context)` returns a structured decision: overall outcome plus every applicable rule's verdict, the observed value, the limit, and a message.
- **Decide card authorizations in real time,** inside the processor's deadline, and keep limits right through captures, tips, reversals, refunds and expiries.
- **Reimburse.** Submit an out-of-pocket expense, evaluate it, route it for approval, pay it out through payroll or ACH (automated clearing house, the US bank transfer network).

Below the line: receipt OCR (optical character recognition), fraud ML models, issuing the cards themselves (we use an issuer processor such as Stripe Issuing, Marqeta or Lithic), accounting and ERP (enterprise resource planning) export, the money movement itself (see [`../payments-ledger/`](../payments-ledger/)).

## Non-functional requirements

| Dimension | Target |
|---|---|
| Scale | 50k tenant companies (largest 100k employees), 3 M active cards. 10 M authorizations/day (avg 116/s, peak ~1.2k/s, designed for 2k/s). 13 M card lifecycle events/day. 1 M out-of-pocket expenses/day in ~330k reports. 2 M rules (avg 40 per tenant, cap 10k) |
| Auth latency | Our gateway in to out: p50 ~6 ms, p99 SLO 50 ms. As the processor sees it: p50 ~15 ms, p99 under 150 ms. Stripe's deadline is 2 s; our internal hard stop is 1.2 s, after which we answer with our own fallback |
| Availability | Auth path 99.99%. Policy API and reimbursement 99.9%. A card must keep working, within bounds, when our engine is down |
| Correctness | Two concurrent authorizations can never both pass an aggregate limit. Every decision is deterministic given (policy version, engine version, inputs) |
| Consistency | Counters and holds: strong per tenant shard. Policy to evaluators: bounded, p99 under 5 s, stamped per decision. Employee attributes: p99 under 60 s, except termination, which freezes cards synchronously |
| Safety | No policy change reaches enforcement without type-check and a history simulation. Engine code rolls out by tenant cohort behind decision diffing |
| Audit | Every decision, its inputs, and the exact policy and engine versions kept 7 years, replayable bit for bit |

## What interviewers probe (the ladder)

1. What does `evaluateRules` return? Why not a boolean, and why not the first violation?
2. How is a rule represented so an admin can add a new one without a deploy? What stops a rule from looping forever or reading another tenant's data?
3. "Trip total at most $2,000." Where does the total come from, and what if two swipes on the same trip land in the same millisecond?
4. The processor gives you 2 seconds. What is on the hot path, and what do you do at 1.9 s? What if your database is failing over?
5. A $70 dinner authorizes, then clears at $84 with the tip. The card was never declined. Now what?
6. An admin ships "amount > 0 → decline" by mistake. What stops it, and how fast can they undo it?
7. "Why was my card declined on March 3?" Answer it in September, after the policy changed four times.
8. One customer has 100k employees and 5k rules. Does anything change?

## Files

| File | What it is |
|---|---|
| [`solution.md`](solution.md) | Full HLD in flow-first form: one incremental diagram, one walkthrough per FR, deep dives that mutate the design, then nitty-gritty |
| [`diagrams.md`](diagrams.md) | The D1 to D12 diagram set |
| [`edge-cases.md`](edge-cases.md) | Every "what if" with a 60-second answer and a confidence box |
| [`deep-dives/rule-model-and-evaluation.md`](deep-dives/rule-model-and-evaluation.md) | Rules as data, the predicate language, compile and index, the decision type, combination semantics, CEL vs Rete vs OPA vs Cedar |
| [`deep-dives/authorization-hot-path.md`](deep-dives/authorization-hot-path.md) | The 2 s deadline, the latency budget, caches on the hot path, the internal deadline, idempotency on the auth id |
| [`deep-dives/aggregates-holds-and-concurrency.md`](deep-dives/aggregates-holds-and-concurrency.md) | Counter rows, lock-evaluate-write, holds through capture, tips, incrementals, reversals, refunds, expiry, hot counters |
| [`deep-dives/degraded-modes-and-region-loss.md`](deep-dives/degraded-modes-and-region-loss.md) | Static controls pushed to the processor, fallback decisions, degraded journal, shard failover, region loss |
| [`deep-dives/safe-rule-changes.md`](deep-dives/safe-rule-changes.md) | Validation, simulation on history, shadow mode, effective dating, rollback, engine rollout with decision diffing |
| [`deep-dives/audit-replay-and-determinism.md`](deep-dives/audit-replay-and-determinism.md) | Decision log, fact snapshots, immutable bundles, replay, sources of non-determinism, retention |
| [`deep-dives/reimbursement-workflow-and-payout.md`](deep-dives/reimbursement-workflow-and-payout.md) | Expense report state machine, approval routing from the org chart, trip aggregates, payout through payroll or ACH, idempotency |
| [`research/`](research/) | Raw web research notes with source links. Input to the files above, not study material |
| `expense-rules-engine.excalidraw` | My drawing. Missing until I draw it |
