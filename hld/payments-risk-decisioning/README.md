# QuickBooks Payments with inline risk decisioning

> One-line answer: the payment orchestrator calls a **risk decision service** with a hard 100 ms budget before it asks the processor to authorize. Inside that budget: one parallel batch read of precomputed features from an in-memory **online feature store** (~15 ms p99 after hedging, ~6 ms p50), request-time features, a deterministic **rules layer** (blocklists, sanctions, velocity caps) and an in-process gradient-boosted model (~5 ms), then a policy that maps score plus merchant segment to approve, decline, step up (3-D Secure for cards, extra verification or a delayed debit for ACH) or approve-and-hold-payout. Every stage has its own deadline. When the model or the feature store misses its deadline, the service does not guess: it returns a **pre-computed fallback decision** for the merchant's risk tier (fail open for established merchants and small amounts, under a per-merchant budget in attempts and dollars; step up or fail closed for new merchants and large amounts), marks the payment for async re-scoring, and holds the merchant's payout if the late score is bad. The orchestrator writes the inline decision to its payment row before the processor call, and risk keeps a 48 h dedup, so a retry gets the same answer and never double counts a velocity counter. Inline scoring is only the first of three layers: QuickBooks pays merchants out, so payout holds and reserves catch merchant fraud that no 100 ms model can see.

Tier 3, problem #52 in [`hld/README.md`](../README.md). From the user's Intuit Principal / Staff practice list (2026-10). Not a reported candidate prompt. It plays to an Uber Risk background, so expect probes on rules vs ML, feature freshness, labels and fail-open vs fail-closed. Related: [`../payments-ledger/`](../payments-ledger/) (money movement; it budgets ~50 ms for risk inside a whole payment API call, where this problem gives the risk service its own p99 of 100 ms at the orchestrator), [`../expense-rules-engine/`](../expense-rules-engine/) (a deadline-bound decision on a card authorization), [`../ai-gateway/`](../ai-gateway/). Sources: [`research/`](research/).

## Problem statement (as asked)

QuickBooks Payments with inline risk decisioning. Crux: a fraud decision within ~100 ms on the payment path, and what you do when the model times out.

Follow-ups that always come: walk the 100 ms; approve or decline on a model timeout, and who decides; a card-testing attack faster than your stream features; labels that arrive 60 to 90 days late; a retried payment that trips your own velocity rule; merchant fraud vs buyer fraud; changing a rule at 2 AM during an attack.

## Functional requirements

Core:
- **Decide inline.** For every card and ACH (automated clearing house, the US bank-transfer network) payment, return approve, decline, step-up or review before the processor is called, inside the budget.
- **Degrade safely.** When any dependency is slow or down, return a bounded, pre-agreed decision instead of blocking the payment or approving everything.
- **Learn.** Stream payment events into features (velocity counters, graph links), collect labels (chargebacks, ACH returns, confirmed fraud), retrain, and roll out new models and rules behind shadow and canary.
- **Act after the payment.** Re-score asynchronously with heavier models, hold or delay merchant payouts, set reserves, and queue cases for human review.

Below the line: merchant onboarding underwriting (KYB, know your business) except as a feature source, dispute handling workflow, the processor and card network themselves, AML (anti-money laundering) transaction monitoring, building the case-management UI.

## Non-functional requirements

| Dimension | Target |
|---|---|
| Scale | ~3 M payments/day [estimate] (avg ~35/s, peak ~350/s), designed for 2k/s. ~20 entity feature lookups per decision, so ~40k feature reads/s at design peak. ~10 events per payment into the stream |
| Latency | Risk decision p99 under 100 ms, p50 ~30 ms, measured at the orchestrator. Internal hard stop at 80 ms, then fallback |
| Availability | Payments 99.99%. A risk outage must never take payments down. The fallback path has no network dependency |
| Feature freshness | Velocity counters visible to the next decision in under 1 s p99 for the same card or merchant. Batch features daily |
| Correctness | Same payment id, same inline decision (the async re-scorer may still hold the payout or void before capture, and that is logged as a separate decision). Velocity counters are idempotent per payment id. Every decision logged with features, model version and rule version for replay |
| Loss budget | Fraud loss and false declines are the product metrics. Degraded-mode exposure is capped per merchant in attempts and dollars, sized to the merchant's p95 hour (clamped $200 to $50k) and refilled as a token bucket; card-not-present payments under $5 always step up in fallback, so a dollar cap cannot be used for card testing |
| Security | Card data never enters the risk service in clear (tokens and fingerprints only). PCI DSS scope kept to the vault |

## What interviewers probe (the ladder)

1. Walk the 100 ms. Where does every millisecond go, and which call is the long tail?
2. A dependency misses its stage deadline and you hit the 80 ms hard stop. Approve or decline? Who decided that, and how much money can it lose?
3. A card-testing attack sends 500 attempts in 60 s while your streaming counters lag 30 s. How do you catch it?
4. Labels arrive 60 to 90 days later. How do you train, and how do you know a new model is better before it declines real customers?
5. The client retries a payment after a timeout. Does your velocity rule now count it twice and decline the retry?
6. QuickBooks pays out to the merchant. What does merchant fraud look like, and why can an inline model not stop it?
7. An analyst wants to push a rule at 2 AM during an attack. How do you make that fast and safe?
8. A merchant asks why their customer was declined. What can you explain?

## Files

| File | What it is |
|---|---|
| [`solution.md`](solution.md) | Full HLD in flow-first form: one incremental diagram, one walkthrough per FR, deep dives that mutate the design, then nitty-gritty |
| [`diagrams.md`](diagrams.md) | The D1 to D12 diagram set |
| [`edge-cases.md`](edge-cases.md) | Every "what if" with a 60-second answer and a confidence box |
| [`deep-dives/latency-budget-and-hot-path.md`](deep-dives/latency-budget-and-hot-path.md) | The 100 ms budget line by line, parallel fan-out, tail latency, hedging, in-process models |
| [`deep-dives/timeouts-and-fallback-policy.md`](deep-dives/timeouts-and-fallback-policy.md) | Deadlines per stage, the fallback decision table, fail open vs fail closed by segment, exposure budgets |
| [`deep-dives/features-and-freshness.md`](deep-dives/features-and-freshness.md) | Batch, streaming and request-time features, idempotent counters, the synchronous counter for attacks, point-in-time correctness |
| [`deep-dives/rules-engine-and-attack-response.md`](deep-dives/rules-engine-and-attack-response.md) | Rules vs ML, rule authoring, shadow rules, emergency rules during an attack |
| [`deep-dives/model-lifecycle-shadow-and-labels.md`](deep-dives/model-lifecycle-shadow-and-labels.md) | Label delay, training sets, shadow and champion-challenger, thresholds, monitoring drift |
| [`deep-dives/layered-controls-and-merchant-risk.md`](deep-dives/layered-controls-and-merchant-risk.md) | Inline vs post-auth vs payout controls, holds and reserves, ACH return risk, merchant bust-out |
| [`research/`](research/) | Raw web research notes with source links. Input to the files above, not study material |
| `payments-risk-decisioning.excalidraw` | My drawing. Missing until I draw it |
