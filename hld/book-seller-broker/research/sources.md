# Book seller broker: research and sources

> One-line answer: this question is a scatter-gather aggregator with a deadline; published guidance supports explicit completion rules, cancellation, bounded retries, and overload isolation.

Research accessed **2026-09-13**. The architecture and all numerical targets in these notes are a proposed design. They are not an account of Databricks' internal systems.

## Verified technical references

| ID | Source | What the retrieved page establishes | Design consequence |
|---|---|---|---|
| S1 | [Enterprise Integration Patterns: Scatter-Gather](https://www.enterpriseintegrationpatterns.com/patterns/messaging/BroadcastAggregate.html) | Request quotes from multiple suppliers, then aggregate; contrasts recipient lists with auction-style publish-subscribe | Use an explicit seller set for known coverage. A message queue is not mandatory for concurrent HTTP calls |
| S2 | [Enterprise Integration Patterns: Aggregator](https://www.enterpriseintegrationpatterns.com/patterns/messaging/Aggregator.html) | An aggregator needs correlation, a completeness condition, and an aggregation algorithm | Specify request/seller/attempt IDs, deadline or all-terminal completion, and deterministic minimum |
| S3 | [gRPC: Deadlines](https://grpc.io/docs/guides/deadlines/) | Calls have no deadline by default; applications must stop spawned activity; propagation deducts elapsed time and avoids raw cross-machine clock comparisons | One request budget, remaining-time propagation, and separate cleanup |
| S4 | [gRPC: Cancellation](https://grpc.io/docs/guides/cancellation/) | Cancellation signals lost interest; the runtime generally cannot interrupt arbitrary server application code | Local timeout does not prove remote computation stopped |
| S5 | [gRPC: Retry](https://grpc.io/docs/guides/retry/) | Retry policies specify attempts, backoff, and retryable errors; transparent retries may occur without a configured policy; retry throttling and jitter are available | One owner for retries, explicit attempt accounting, deadline and quota checks before every attempt |
| S6 | [Google SRE, Chapter 21: Handling Overload](https://sre.google/sre-book/handling-overload/) | Degraded responses, per-customer quotas, adaptive client throttling, resource-based capacity, and bounded retry behavior | Shed work before queues grow; measure resources as well as QPS; publish reduced coverage |
| S7 | [Envoy: Circuit breaking](https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/upstream/circuit_breaking) | Bounds connections, pending requests, active requests, retries, and connection pools; these are distributed, uncoordinated limits, with possible implementation races | Bulkheads limit resource use. They are not a strict fleet-wide seller QPS contract |
| S8 | [Envoy: Global rate limiting](https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/other_features/global_rate_limiting) | Describes per-request global checks, a Redis-backed reference service, and layered local/global limits | Separate local overload protection from seller-global quota admission |
| S9 | [Dean and Barroso: The Tail at Scale](https://research.google/pubs/the-tail-at-scale/) | Published abstract explains how temporary high-latency episodes dominate large fan-out systems | Do not wait for all independent sellers to meet an interactive deadline. The probability calculation here is our derivation |
| S10 | [Python asyncio: Coroutines and Tasks](https://docs.python.org/3/library/asyncio-task.html) | TaskGroup failures cancel siblings; wait does not cancel pending tasks; wait_for waits for cancellation and may exceed its timeout | Convert expected seller failures to outcomes; explicitly cancel pending work; do not wait indefinitely for cleanup before replying |
| S11 | [Microsoft: Asynchronous Request-Reply pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/async-request-reply) | HTTP 202 with Location and Retry-After, polling a status resource, cancellation, and idempotency keys | Add a durable status resource only when resumability or long-running callbacks are required |
| S12 | [PostgreSQL: Transaction isolation](https://www.postgresql.org/docs/current/transaction-iso.html) | Read Committed updates re-evaluate predicates after conflicting updates; SELECT FOR UPDATE serializes access to a row; Serializable can require transaction retries | Durable quote insertion and finalization must lock the same query row and commit their changes together |
| S13 | [Redis: Scripting with Lua](https://redis.io/docs/latest/develop/programmability/eval-intro/) | Scripts execute atomically on the server and block other activity for their duration | Keep refill/debit scripts short; one hot seller key remains serialized |
| S14 | [Redis: Replication](https://redis.io/docs/latest/operate/oss_and_stack/management/replication/) | Replication is asynchronous by default; WAIT does not establish strong consistency and acknowledged writes can still be lost on failover | Strict seller quotas require an explicit failover and fencing policy beyond an atomic script |

The Envoy `latest`, PostgreSQL `current`, and Python `3` links are rolling documentation. Pin implementation versions and check their behavior before converting the notes into code.

## Evidence boundaries

- The local [question index](../../README.md) supplies the exact prompt and follow-up ladder. Its “22 reports” and interview frequency claims were not independently validated.
- Google search returned a JavaScript challenge, DuckDuckGo a bot challenge, and Bing's RSS results were unrelated. No challenge was bypassed. These results are not evidence for interview frequency.
- The [SystemDesignHandbook Databricks page](https://www.systemdesignhandbook.com/guides/databricks-system-design-interview/) was readable, but the retrieved content did not substantiate this specific book seller prompt. [PracHub](https://prachub.com/companies/databricks/categories/system-design) did not expose relevant prompt text in the retrieved content.
- The [AWS retries article URL](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/) returned only a Builder Center shell in this environment. It is not used as evidence; S5 and S6 support the retry discussion.
- No verified, dedicated solution article for this exact interview prompt was recovered. The design therefore follows the repository's FR/NFR framework and synthesizes the primary pattern and engineering references above.
- S9 was read through its publication page and abstract. These notes do not claim to have reviewed the full paper or reproduce its experiment results.

## Synthesis

1. **Completion is a product decision.** Waiting for N outcomes and returning N successful quotes are different. Timeouts are terminal outcomes, not quotes. [S1, S2]
2. **Latency and resource lifetimes differ.** Publish at the cutoff, signal cancellation, then supervise bounded cleanup. [S3, S4, S10]
3. **Rate, concurrency, and health are different controls.** Rate limits protect seller contracts; concurrency limits protect sockets and memory; a health breaker avoids futile work. [S6, S7, S8]
4. **Durability is an additional requirement.** A short-lived quote search can restart after a crash. Preserving the same request across a crash needs stored state, deduplication, and a recovery protocol. [S2, S11, S12]
5. **A cheaper missing quote cannot be inferred.** Neither majority responses nor the first successful response prove a minimum across unobserved sellers. This follows from the problem itself, not from a database consistency theorem.
