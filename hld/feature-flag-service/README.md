# Feature flag service (Amazon Weblab style)

> One-line answer: start from the ratio. About **20 M flag checks a second** against about **3,000 edits a day** (~6 x 10^8 to 1) means a check must never leave the process. Every service links a thin SDK that evaluates flags **in memory** in under 1 us against an immutable local snapshot. Evaluation is a fixed order: missing flag returns the code default, then kill switch, block list, allow list, then a **deterministic bucket** `hash(flag salt, unit id) mod 10,000` compared with the rollout in basis points. So the same merchant gets the same answer on every server with no stored assignment, a growing rollout only adds units, and flags are independent. Writes go to one small strongly consistent store, where each edit gets a sequence number. A publisher turns each committed edit into an immutable delta file in object storage. A **per-host agent** polls a 100-byte version pointer every 5 s through a regional cache and applies deltas in order. So an edit or a kill reaches 99% of hosts in about 10 s with no streaming tier. Every host keeps its **last-known-good** copy on disk and keeps serving it when the control plane is down. A bad snapshot is the one thing that can hurt every request at once, so it is validated twice and format changes roll out in stages.

Tier 3, problem #56 in [`hld/README.md`](../README.md). Reported at **Stripe**: Staff Software Engineer, Aug 2026, the first of two 60-minute "mini onsite" rounds. Rejected. The candidate's own post-mortem: "I was trying to force it into a rate limiter design, so I suggested a local cache plus a tiered Redis cache ... Looking back afterward, I think a lot of the logic should really live in a client-side library: the client services pull a snapshot from object storage and compute locally, with no need to build a data plane service". Interviewer feedback: "trying to force-fit a template from somewhere else instead of designing around the actual requirements" ([PracHub write-up](https://prachub.com/interview-experiences/stripe-staff-software-engineer-interview-experience-feature-flag-design-and-an-ai-coding-round-rejected)). Stripe loop context: [`../company-questions.md` §3](../company-questions.md#3-stripe-staff-l4).

Closest solved problem: [`../distributed-denylist/`](../distributed-denylist/) (one small dataset on every host, local check, fail-static). This problem is the same skeleton on 1/20th of its fleet and at a write rate tens of thousands of times lower, plus what flags add: bucketing, evaluation order, rollout governance and flag lifecycle. Reusable blocks: [`../../concepts/caching-patterns.md`](../../concepts/caching-patterns.md), [`../../concepts/leases-fencing-clocks.md`](../../concepts/leases-fencing-clocks.md), [`../../concepts/replication-and-quorums.md`](../../concepts/replication-and-quorums.md). Sources: [`research/`](research/).

## Problem statement (as given)

From the [PracHub question page](https://prachub.com/interview-questions/design-a-feature-flag-service-with-percentage-rollouts-and-allow-block-lists) (captured 2026-10-08):

> Design a feature flag service, similar in spirit to Amazon's Weblab, for a company that runs many backend services. Engineers create and edit flags in a management console. For each flag they can turn the feature on or off for everyone, roll it out to a percentage of users, and force it on or off for specific users with an allow list and a block list. Application services check flags while they handle requests.

The page's three hints: "Compare how often a flag changes with how often it is checked, and how stale a check may be. Let those numbers, not a design you have used for a different problem, decide where a check should be computed." "A user who gets the feature on one request should get it on the next, on any server, and should keep it when the rollout grows ... without storing an assignment for every user." "Consider how an edit, especially switching off a broken feature, reaches every running service, and what a service does when it cannot reach the flag system at all."

## Clarifying questions, and the answers this design assumes

| Question (from the prompt page) | Assumed answer |
|---|---|
| Who checks flags: backend only, or browsers and mobile too? | Backend services only. Client apps get flags evaluated server-side (seam in §10.11) |
| How many flags, services, checks per second, and latency per check? | 20k live flags, ~1,000 services on ~10k hosts (~50k processes), ~20 M checks/s at peak. A check adds under 1 us |
| How fast must a change, especially a kill, reach every service? | 99% of hosts within 10 s, 99.99% within 60 s. A host more than 5 min stale pages someone |
| Must a user's answer stay the same across requests, services and devices? Who is the user? | Yes, for a given flag version. Each flag declares its unit (`merchant_id`, `account_id`, `user_id`). At Stripe the merchant is usually the right unit |
| Gating and gradual rollout only, or experiments with exposure logging? | Gating and rollout. Experiments are below the line, with the seam named |
| Flag system unreachable: fail closed, fail open, or a per-flag default? | None of the three by default: **fail static** (keep the last-known-good snapshot). With no snapshot at all, the code default named at the call site |
| Approvals, audit history, scheduled changes? | Audit always (every version kept). Approval for rollout increases on flags tagged high-risk. A kill never waits for approval. Scheduled ramps are an extension |

## Functional requirements

Core:
1. **Manage flags.** Create a flag (key, owner, unit, code default), turn it on or off for everyone, set a rollout percentage, edit allow and block lists. Every edit is a new immutable version with author and reason.
2. **Check flags.** A service asks `is_enabled(flag, context, default)` while it handles a request and gets a boolean plus a reason, without a network call.
3. **Propagate.** Every edit, and above all a kill, reaches every running process quickly, in order, and the editor can see how far it got.
4. **Audit and undo.** See who changed what and when, and revert to any earlier version in one action.

Below the line: experiments (multi-variant, exposure logging, metrics analysis), client-side flags in browsers and mobile apps, scheduled changes, flags that carry config values other than booleans, targeting rules on arbitrary attributes (country, plan).

## Non-functional requirements

| Dimension | Target |
|---|---|
| Check latency | p99 under 1 us in process. Zero network calls, zero locks on the read path |
| Check availability | A flag check never fails a request and never blocks. It is as available as the process |
| Propagation | Edit or kill visible on 99% of **live** hosts within 10 s (p50 ~3.5 s), 99.99% of live hosts within 60 s. A live host reported a watermark in the last 30 s; dead hosts are laggards, not SLO misses. Per-host staleness alarm at 5 min |
| Stickiness | For one flag version, the same unit gets the same answer on every host and in every SDK language. Raising the rollout only adds units. Two flags at 10% overlap on ~1% of units, as if independent |
| Ordering | A host applies edits in sequence order and never goes back to an older version |
| Control plane | Writes 99.9%. A kill must still work with one region down |
| Safety | A malformed or oversized snapshot is rejected before it reaches a request path. Format changes roll out in stages |
| Scale | 20k live flags, ~3,000 edits a day (single edits cap at ~12/s, scripts use a batch endpoint), allow and block lists up to 1 M ids each |

## What interviewers probe (the ladder)

1. Compare checks per second with edits per day. Where should a check be computed, and why is "a flag service behind Redis" the wrong template here?
2. How does the same merchant get the same answer on every server, keep it as the rollout grows from 10% to 20%, and not land in the same 10% for every flag?
3. An engineer hits the kill switch on a broken feature. How long until every process sees it, and how do they know it got there?
4. The flag control plane is down, or a process boots during that outage. What does `is_enabled` return?
5. A bad snapshot (oversized, malformed) is published. What stops it from crashing every service at once? (Cloudflare, 18 Nov 2025.)
6. Two services take part in one feature and see the flag flip 3 s apart. What breaks, and what do you do?
7. A block list of 1 M merchant ids. Where does it live, and what does a host load?

## Files

| File | What it is |
|---|---|
| [`solution.md`](solution.md) | Full HLD in flow-first form: one incremental diagram, one walkthrough per FR, deep dives that mutate the design, then nitty-gritty |
| [`diagrams.md`](diagrams.md) | The D1 to D12 diagram set |
| [`edge-cases.md`](edge-cases.md) | Every "what if" with a 60-second answer and a confidence box |
| [`deep-dives/evaluation-and-bucketing.md`](deep-dives/evaluation-and-bucketing.md) | Evaluation order, the hash and its inputs, stickiness as rollouts grow, independence across flags, cross-language test vectors |
| [`deep-dives/propagation-and-kill-switch.md`](deep-dives/propagation-and-kill-switch.md) | Change log, publisher, delta and snapshot files, the 5 s poll, the per-host agent, fleet watermarks, why no streaming tier |
| [`deep-dives/fail-static-and-bad-snapshots.md`](deep-dives/fail-static-and-bad-snapshots.md) | Last-known-good, boot without the control plane, code defaults, two-stage validation, staged format changes, the incidents that shaped it |
| [`deep-dives/safe-changes-and-flag-lifecycle.md`](deep-dives/safe-changes-and-flag-lifecycle.md) | Approvals, audit and revert, guarded rollouts that pause on a metric regression, stale-flag cleanup, never reusing a key |
| [`deep-dives/lists-segments-and-cross-service.md`](deep-dives/lists-segments-and-cross-service.md) | Allow and block lists up to 1 M ids, named segments, exact sets vs filters, version skew across services, the experiments seam |
| [`research/`](research/) | Raw web research notes with source links. Input to the files above, not study material |
| `feature-flag-service.excalidraw` | My drawing. Missing until I draw it |
