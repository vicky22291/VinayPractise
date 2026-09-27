# Distributed deny list

> One-line answer: every enforcement host (about 200k front-ends, API gateways and edge proxies) keeps the whole list in shared memory and checks it locally in about 400 ns with zero network calls; writes go to one strongly consistent store (Spanner) whose commit timestamp is the version; two leaderless publishers cut the change log into deterministic 100 ms batches at a closed timestamp and push them down a fan-out tree (publisher, regional distributors, host agents) so a change is enforced on 99% of hosts in under 10 s; each host applies a contiguous prefix of the log, reports its watermark back up the tree, and serves its last good copy when cut off (fail-static); broad or bulk changes go through shadow and canary modes on the entry itself, and host agents validate every batch, so one bad change cannot deny the whole internet.

Tier 3, problem #23 in [`hld/README.md`](../README.md). Asked at Google (L5/L6) as "design a distributed deny list / block list". It is the same answer as "design a config or feature flag push system", "design API key revocation", and "design an IP blocklist for all front-ends". See [`research/`](research/).

## Problem statement (as asked)

Many services across a global fleet must check, on every request, whether an entity is denied: a client IP or CIDR range, a user account, an API key or token. Trust and safety staff and automated abuse detectors add and remove entries. The check must be fast enough to sit on every request, and a new entry must take effect everywhere within seconds. Unblocking must be just as fast. Say what consistency the fleet sees.

Follow-ups that always come: the list no longer fits in memory; someone adds `0.0.0.0/0` or a detector goes rogue; how do you know every server has the change; what if the central service is down; a region is cut off; 200k hosts restart at once.

## Functional requirements

Core:
- `check(ip, account, api_key)` returns `allow` or `deny(entry_id)` on every request, in process.
- Add and remove entries (exact IP, CIDR, account, API key) with reason, owner, optional TTL and scope (global or a set of regions), from humans, automated detectors, and external feeds such as a government list at `security.gov.x`. Bulk import.
- Propagate every add and every remove to every enforcement host, and report how far it has got.
- Explain and undo: who denied this key and why, and revert a change or an actor's changes.

Below the line: deciding who to block (detectors are clients), rate limiting and CAPTCHA challenges, regex or ML rules, URL lists with hundreds of millions of entries (the Safe Browsing variant, covered as evolution).

## Non-functional requirements

| Dimension | Target |
|---|---|
| Scale | 200k enforcement hosts in 30 regions and 150 edge PoPs; 50 M requests/s peak, 100 M lookups/s; 10 M active entries; 2k changes/s average, 20k/s burst |
| Check latency | p99 under 1 us in process, zero remote calls on the request path |
| Freshness | An add or a remove is enforced on 50% of hosts within 2 s and 99% within 10 s of commit. Bulk lane within 5 minutes |
| Availability | The check never fails and never waits. The distribution plane can be down for hours without the fleet losing protection |
| Consistency | Store: linearizable. Each host: a consistent prefix of the change log, monotonic, never older than 30 s without an alert. Across hosts: eventual within 10 s |
| Safety | No single change denies more than 0.1% of the last hour's good traffic without two-person approval. Any change reverted fleet-wide in under 30 s |

## What interviewers probe (the ladder)

1. Where does the check run? Why not call a deny-list service?
2. How big is the list in memory, per host and fleet-wide? What if it is 10x?
3. A detector adds 100k IPs during an attack. What does each host receive, and when?
4. How does a host know it is behind, as opposed to "nothing changed"? What does "propagated" mean, and how do you prove it?
5. The central store or the publisher is down. What happens to enforcement? A new host boots during the outage?
6. Someone denies `0.0.0.0/0`, or a bug in the list crashes the proxy. What is the blast radius, and what stops it?
7. How fast does an unblock take effect? TTL entries and clock skew?
8. Multi-region and edge PoPs: what crosses a region boundary?

## Files

| File | What it is |
|---|---|
| [`solution.md`](solution.md) | Full HLD in flow-first form: one incremental diagram, one walkthrough per FR, deep dives that mutate the design, then nitty-gritty |
| [`diagrams.md`](diagrams.md) | The D1 to D12 diagram set |
| [`edge-cases.md`](edge-cases.md) | Every "what if" with a 60-second answer and a confidence box |
| [`deep-dives/local-lookup-and-memory-layout.md`](deep-dives/local-lookup-and-memory-layout.md) | Per-type tables, CIDR matching, base plus overlay, left-right swap, one copy per host, XDP at the edge |
| [`deep-dives/propagation-and-fan-out.md`](deep-dives/propagation-and-fan-out.md) | Push vs pull, constant work vs deltas, deterministic publishers, the fan-out tree, bursts and bulk lane, bootstrap |
| [`deep-dives/watermarks-and-consistency-window.md`](deep-dives/watermarks-and-consistency-window.md) | Closed timestamps, contiguous batches, gap detection, state checksums, ACKs up the tree, staleness policy |
| [`deep-dives/safe-changes-and-blast-radius.md`](deep-dives/safe-changes-and-blast-radius.md) | Guardrails, impact estimate, shadow and canary as entry modes, actor quotas, host-side validation, kill switch, revert |
| [`deep-dives/failure-modes-and-fail-static.md`](deep-dives/failure-modes-and-fail-static.md) | Store, publisher, distributor, agent and region failures, readiness gate, fleet cold start, clock skew |
| [`deep-dives/list-growth-and-tiering.md`](deep-dives/list-growth-and-tiering.md) | 10x and 100x lists: scoping, compact encodings, filters with remote confirm, hash prefixes, cost |
| [`research/`](research/) | Raw web research notes with source links. Input to the files above, not study material |
| `distributed-denylist.excalidraw` | My drawing. Missing until I draw it |
