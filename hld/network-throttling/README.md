# Datacenter network throttling / hierarchical rate limiting

> One-line answer: enforce every limit locally with a token bucket on the enforcer that sees the traffic (gateway pod, sidecar, or host agent), never make a remote call on the hot path, and keep the limits globally correct with a 100 ms batch-report loop to a sharded, tree-owning allocator that computes weighted max-min shares down the hierarchy (account to workspace to user to endpoint, or datacenter to tenant to job to host) and hands each enforcer a short lease; when the allocator is unreachable the enforcer keeps its lease, then falls to a per-limit safe policy (fail open to a local cap, or fail closed to a static split).

Tier 1, problem #7 in [`hld/README.md`](../README.md). Reported at Databricks as "network throttling" and as "design a distributed rate limiter that handles millions of requests per second" with hierarchical limits (account, workspace, user, API). The same shape shows up at Google as "throttle traffic between datacenters" (their BwE system), at Stripe as "design our rate limiter", and at Meta and Uber as "protect a service from a noisy tenant". Databricks published how they rebuilt their own limiter in 2023 (Envoy plus a rate limit service plus one Redis, replaced by batch reporting plus in-memory sharding), so the interviewer has a reference answer in mind. See [`research/`](research/).

## Problem statement

A multi-tenant platform runs thousands of gateway pods (or thousands of hosts) in a region. Each request (or each byte) belongs to several nested groups: an account, a workspace inside it, a user inside that, an endpoint. Each group has a limit. Enforce all of them across the fleet so that no group exceeds its cap by more than a small tolerance, siblings share a parent's cap fairly, unused capacity is not wasted, and the check adds no measurable latency to the request. Then make it survive the loss of any component, including the thing that computes the limits.

Two variants use the same design and differ only in the enforcer:

| Variant | Unit | Enforcer | Reject means |
|---|---|---|---|
| API / request throttling (Databricks, Stripe) | requests/s | gateway pod or sidecar, in process | HTTP 429 with `Retry-After` |
| Network / bandwidth throttling (Google BwE, cross-DC egress) | bytes/s | host agent programming `tc` HTB or an eBPF pacer | delay, then drop; TCP backs off |

## Functional requirements

Core:
- Admit or reject each request against every limit in its hierarchy. A request carries descriptors `[account, workspace, user, endpoint]`; all applicable buckets must have tokens.
- Limits are policy: `rate`, `burst`, a `min` guarantee, and a `weight` per node of the tree. Policy changes apply fleet-wide within seconds without restarts.
- Work conserving and fair: a parent cap is shared among children by weighted max-min; unused child capacity flows to siblings; no child is pushed below its `min` while it has demand.
- Observability: per-limit usage and rejections, a shadow mode that reports what would be rejected, and `Retry-After` / remaining headers on responses.

Below the line (say it out loud):
- Billing-grade metering. This limiter is approximate by design (about 5% overshoot tolerated). Metering is a separate exact pipeline.
- Per-flow congestion control, DDoS scrubbing, WAF. The network and the edge do those.
- Quota purchase and approval workflows. We read policy; we do not own its lifecycle.
- Cross-region global limits. One allocator tree per region; a cross-region cap is the 10x evolution.

## Non-functional requirements

| Dimension | Target |
|---|---|
| Scale | 2 M requests/s regional peak (200 k avg), 2,000 enforcers, 10 M live limit keys, 5 descriptors per request, so 10 M limit checks/s |
| Hot-path latency | Local decision p99 < 50 us. No remote call per request |
| Accuracy | Over any 1 s window a limit is exceeded by at most 5%; over 10 s at most 1%. A deficit is paid back, never forgotten |
| Fairness | Weighted max-min among siblings within one control interval (100 ms); a child with demand never gets less than its `min` |
| Availability | Data path 99.99%. Control plane (allocator) 99.9%, and its outage never stops traffic |
| Consistency | Counters eventual (100 ms loop). Policy strong: one version applied atomically per key within 1 s |
| Control-plane cost | Control traffic grows with enforcers and active keys, not with request rate |
| Bandwidth variant | 50 k hosts, 1 M flow groups, allocation loop 1 to 5 s, host enforcement within 100 ms of a new allocation |

## What interviewers probe (the ladder)

1. A client sends 10x its limit in the first 100 ms of a window. What gets through, and why is that acceptable?
2. Two thousand gateways share one limit of 100 requests/s. How does gateway 1,377 know what gateway 12 admitted? Show the numbers for "ask Redis every time".
3. The limit is hierarchical. Workspace A is hammering; workspace B in the same account sends one request. Does B get through? Where is fairness decided?
4. The rate limit service (or Redis) is down. Fail open or fail closed? Is the answer the same for "protect our API" and "stay under a cloud provider's API quota"?
5. The node that owns the counters for the biggest tenant crashes. What is lost, how long until limits are enforced again, and can two nodes both think they own it?
6. Fixed window, sliding window, token bucket: which one, and what does "the bucket remembers" buy you?
7. Change a limit from 1,000 to 100 requests/s. When does it take effect and does the tenant get punished for the last second?
8. One tenant's tree is 30% of all traffic. Show the hot shard and how to split it.
9. Now it is bytes between datacenters instead of requests. What changes in the enforcer, the loop period, and what "reject" means?
10. Clocks differ by 200 ms across the fleet. Which of your timestamps care?

## Files

| File | What it is |
|---|---|
| [`solution.md`](solution.md) | Full HLD, Bad / Good / Great ladders, nitty-gritty internals |
| [`diagrams.md`](diagrams.md) | The D1 to D12 diagram set |
| [`edge-cases.md`](edge-cases.md) | Every "what if" with a 60-second answer and a confidence box |
| [`deep-dives/local-enforcement.md`](deep-dives/local-enforcement.md) | Token bucket and GCRA internals, the hierarchical AND check, optimistic first hit, applying a rejection rate, memory per key |
| [`deep-dives/allocator-and-control-loop.md`](deep-dives/allocator-and-control-loop.md) | Batch reports, sharding by tree root, ownership epochs, learning mode, soft state, capacity math |
| [`deep-dives/hierarchical-fair-allocation.md`](deep-dives/hierarchical-fair-allocation.md) | Weighted max-min water-filling on a tree, HTB rate / ceil / borrow semantics, worked example |
| [`deep-dives/accuracy-and-overshoot.md`](deep-dives/accuracy-and-overshoot.md) | The overshoot bound as a function of report interval and enforcer count, deficit payback, the 10x-burst case |
| [`deep-dives/failure-modes-and-fail-policy.md`](deep-dives/failure-modes-and-fail-policy.md) | Leases, safe capacity per limit, fail open vs fail closed per layer, split brain, partition |
| [`deep-dives/bandwidth-throttling-variant.md`](deep-dives/bandwidth-throttling-variant.md) | Bytes instead of requests: host enforcer with `tc` HTB or EDT pacing, BwE-style loop, what the network already does |
| [`research/`](research/) | Raw web research notes with source links. Input to the files above, not study material |
| `network-throttling.excalidraw` | My drawing. Missing until I draw it |
| `my-attempt.md` | My timed attempt before reading the solution |
