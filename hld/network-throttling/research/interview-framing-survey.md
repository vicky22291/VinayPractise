# Design Datacenter Network Throttling / Hierarchical Rate Limiting: Interview Framing Survey

**Research date:** 2026-09-13

---

## Sources

| ID | URL | Establishes |
|----|-----|-------------|
| S1 | https://www.databricks.com/blog/high-performance-ratelimiting-databricks | Databricks batch-reporting architecture, client-side optimization, tail latency wins |
| S2 | https://www.teamblind.com/post/databricks-system-design-interview-z5q8dwhj | Databricks concurrency round format, failure mode emphasis |
| S3 | https://www.hellointerview.com/learn/system-design/problem-breakdowns/distributed-rate-limiter | Hello Interview FR/NFR, algorithms, scale assumptions |
| S4 | https://stripe.com/blog/rate-limiters | Four types of rate limiters, rollout strategy, fail-open behavior |
| S5 | https://sre.google/sre-book/handling-overload/ | Google SRE adaptive throttling formula, K=2, per-customer quotas, criticality levels |
| S6 | https://sre.google/sre-book/addressing-cascading-failures/ | Google SRE load shedding, cascading failure prevention |
| S7 | https://kubernetes.io/docs/concepts/cluster-administration/flow-control/ | Kubernetes APF priority levels, concurrency shares, seats model, shuffle sharding |
| S8 | https://www.envoyproxy.io/docs/envoy/latest/configuration/http/http_filters/local_rate_limit_filter | Envoy local rate limit filter, token bucket, 429 response |
| S9 | https://github.com/envoyproxy/ratelimit/blob/main/README.md | Envoy RLS descriptors, shadow mode, local cache (freecache), timeout defaults |
| S10 | https://docs.aws.amazon.com/apigateway/latest/developerguide/limits.html | AWS API Gateway 10k RPS / 5k burst default, throttling hierarchy |
| S11 | https://docs.aws.amazon.com/ec2/latest/devguide/ec2-api-throttling.html | AWS EC2 token bucket, per-API limits, resource rate limiting |
| S12 | https://docs.cloud.google.com/service-infrastructure/docs/rate-limiting | GCP rate quota vs allocation quota semantics |
| S13 | https://learn.microsoft.com/en-us/azure/azure-resource-manager/management/request-limits-and-throttling | Azure Storage throttling, ingress/egress limits (5-50 Gbps), token bucket |
| S14 | https://spacecomplexity.ai/blog/databricks-onsite-interview | Databricks onsite concurrency round, request burst scenarios |
| S15 | https://prachub.com/resources/system-design-interview-rubric-by-level-mid-level-vs-senior-vs-staff | Staff-level rubric: failure modes, migration, operability, cost, trade-offs |

---

## The Interview Question in the Wild

**Databricks reports (2024-2025):** "Design a distributed rate limiter that handles millions of requests per second" [S2]. Specifically: "What happens when a client sends 10x their limit in the first 100ms of a window?" [S14]. Concurrency round is 60 minutes with runnable code and shared mutable state [S2].

**Interview emphasis:** "What happens when this node crashes?" is not a follow-up. It is the main question [S2]. Failure mode analysis is the signal.

**Related variants:** Design hierarchical rate limiter (tenant > workspace > user > API). Design network throttling between datacenters. Design per-customer quota system with criticality levels.

**Real Databricks system:** Early 2023: Envoy ingress → Ratelimit Service → single Redis instance. 2023 onward: batch-reporting system where clients report aggregated metrics asynchronously, trading strict accuracy for 10x tail latency improvements and eliminated Redis as a SPOF [S1].

---

## Hello Interview: Baseline Frame (1M RPS, 100M DAU)

**Functional requirements:** Client identification (user ID / IP / API key), configurable rules (e.g., 100 requests/minute), HTTP 429 response with headers (remaining, reset time) [S3].

**Non-functional requirements:** Latency < 10ms per check. High availability (eventual consistency acceptable). Scale: 1M requests/second, 100M DAU [S3].

**Algorithms compared:** Fixed window (simple, boundary-vulnerable). Sliding window log (perfect accuracy, high memory). Sliding window counter (hybrid). Token bucket (recommended: handles bursts, memory-efficient) [S3].

**Architecture numbers:** 100k-200k ops/second per Redis instance. 50k-100k rate limit checks/second realistic per shard. 10 Redis shards needed for 1M RPS [S3].

---

## Stripe: Four Tiers (Production Reference Implementation)

Stripe operates four types in production [S4]:

1. **Request rate limiter.** Per-user limit: N requests/second. "By far the most important one." Rejected millions monthly.

2. **Concurrent requests limiter.** Max simultaneous in-flight requests (e.g., 20 per user). Triggered 12k times/month. Prevents CPU-intensive endpoint overload.

3. **Fleet usage load shedder.** Reserves infrastructure capacity for critical ops. Example: 20% of fleet for critical requests. Non-critical over-quota receive 503.

4. **Worker utilization load shedder.** Final defense. Categorizes traffic into four tiers (critical methods, POSTs, GETs, test mode). Sheds gradually, starting lowest priority.

**Rollout practice:** Begin with tier 1. Add others over time. Fail-open: "Catching exceptions at all levels so any coding or operational error would fail open" [S4].

**Dark launch:** Feature-flag each limiter. Observe traffic it would block before enabling.

---

## Google SRE: Adaptive Client-Side Throttling (Ch. 21-22)

**Per-customer quota model:** Global resource pool (e.g., 10k CPU-seconds/sec) divided by service criticality and importance. Gmail 4k, Calendar 4k, Android 3k, Google+ 2k, others 500 [S5]. Note: allocations may exceed total since simultaneous peak is rare.

**Criticality levels:** CRITICAL_PLUS, CRITICAL (default), SHEDDABLE_PLUS, SHEDDABLE. Determines load-shedding priority [S5].

**Adaptive throttling (client-side):** Clients track over two-minute window:
- requests: app-layer attempts
- accepts: backend-approved requests

Reject locally with probability max(0, (requests - K×accepts) / (requests+1)) when requests ≥ K×accepts.

Default K = 2 [S5]. Reducing K → more aggressive. Increasing K → relaxed.

**Advantage:** No additional dependencies or latency penalties. Decision made locally using only local information [S5].

**Load shedding (Ch. 22):** Most cascading failures trace to overload. Load shedding stabilizes components at maximum load, prioritizing by business criticality [S6].

---

## Kubernetes API Priority and Fairness (APF)

**Design:** Divides apiserver concurrency into weighted priority levels. Classifies requests by user, resource, namespace, verb [S7].

**Priority levels:** Configured with concurrency shares. Isolated pools prevent starvation across priorities. Fair-queuing within each level prevents flows from starving each other [S7].

**Seats model:** Not all requests consume equal concurrency. Baseline: 1 seat per request. List requests: multiple seats proportional to object count. Watch requests: conditional based on create notification inclusion [S7].

**Queuing:** Limited queuing absorbs brief bursts without rejection when average load is acceptable. Uses shuffle sharding to prevent hotspots in fair-queuing queues [S7].

**Exempt requests:** Long-running ops, health checks bypass APF [S7].

**Default config:** Kubernetes v1.29+ ships APF enabled by default. Exposes metrics for per-priority concurrency usage, queue depth, rejection rates [S7].

---

## Envoy: Local vs Global Rate Limiting

**Local rate limit filter:** Token bucket per Envoy proxy instance. Stateless. Returns 429 when bucket empty [S8].

**Global rate limit service (RLS):** gRPC service with Redis/Memcached backend. Proxies ask central service "can this request proceed?" Descriptors (key/value pairs) select rules [S9].

**Layering:** Local can absorb large bursts; global reduces load on central service [S8].

**Shadow mode:** Evaluates rules without rejecting. Collects statistics on would-be breaches [S9]. Global shadow mode can override for gradual rollout [S9].

**Local cache layer (freecache):** Optional caching of over-limit decisions avoids Redis re-query for hot keys [S9].

**Defaults:** Redis timeout 10s. Ports: 8080 (HTTP), 8081 (gRPC), 9090 (Prometheus). Near-limit ratio 0.8 (warn at 80% of limit) [S9].

---

## Cloud Provider Reference Implementations

**AWS API Gateway:** Account-level default 10k RPS, 5k burst. Uses token bucket. Throttling hierarchy: per-client/per-method → per-method → account → region [S10].

**AWS EC2 API:** Per-API token buckets. Example: DescribeHosts has 100 max tokens (burst) and refill per second. RunInstances resource bucket: 1000 tokens, 2 token/sec refill. Requestable limit increases up to 3x current [S11].

**GCP quotas:** Rate quotas (requests/sec/day) vs allocation quotas (total resources). Rate quotas evaluated per minute. 403 rateLimitExceeded when exceeded [S12].

**Azure Storage:** Token bucket for ARM throttling. Ingress 5-50 Gbps, egress 10-50 Gbps depending on region and replication [S13]. Responds with 503 Server Busy / 500 Operation Timeout when throttled.

---

## What a Staff Answer Must Add

The six Staff criteria [S15]:

1. **Simplest design that meets requirement.** What are we refusing to build? Explain choice. Example: Redis single master (simpler, acceptable replication lag) vs Raft cluster (over-engineered for this use case).

2. **Failure modes and blast radius.** Not just happy path. Redis unavailable: fail-open with local limits or fail-closed with queuing? Client library crash: do we leak tokens? Network partition: clients go over-quota or stuck.

3. **Migration and zero-downtime rollout.** How do we ship this? Gradual feature-flag ramp. Dark launch with shadow mode. Canary ring by tenant type. Rollback path if rejection rate spikes.

4. **Operability: metrics, alerting, runbooks.** What pages someone at 3 AM? Per-rule rejection rate. Per-client tier rejection rate spike (bug vs abuse?). Latency of rate limit check (tail p99). Recovery SOP: clear local cache, reset quota counters.

5. **Cost: infrastructure and engineering.** Is a Redis cluster cheaper than adding servers to handle rejected traffic retry load? How many on-call incidents per quarter from rate limiter misconfig?

6. **Trade-offs explicit, not hidden.** Accept some over-quota traffic locally to cut tail latency 10x. Accept slight quota violations in multi-datacenter scenario to avoid cross-DC latency. Accept temporary unfairness during network partition to remain available.

---

## What This Means for Our Design

**Functional requirements the interview implies:**
- Identify clients by API key / user ID / IP (context-dependent).
- Apply hierarchical limits: account > workspace > user > API method.
- Return 429 with Retry-After header. Log rejections by tier.
- Support multiple algorithms (token bucket primary, fallback sliding window).
- Hot-reload rules without service restart.

**Non-functional requirements (negotiable, state early):**
- Latency: < 5ms p50 if local-only, < 20ms p99 if RLS-backed.
- Availability: survive single-node failures, degraded mode if Redis unavailable.
- Consistency: eventual OK (minutes-scale lag acceptable).
- Scale: 100k-1M RPS depending on tier. 1-100M users.

**Follow-up ladder (likely order):**
- Handling datacenter failover without quota over-count.
- Client-side predictive throttling to avoid rejections.
- Prioritizing critical traffic during overload (load shedding).
- Fairness: preventing one tenant from starving others.
- Cost and operability: which failure mode is acceptable?
- Real-world Databricks case: how batch-reporting works.
- Extending to multi-tenant: isolation and quota borrowing.
- Handling bursty request patterns (token bucket tuning).
- Migration path from existing single-node limiter.
- Observability: what dashboards do operators need?
- Per-quota tier SLA enforcement.

**Red flags (Staff interviewer catches these):**
- Ignoring failure modes: "Redis just works."
- No clear traffic-shedding priority under overload.
- Ignoring client-side smarts; assuming server-side always correct.
- No operability plan; just "add monitoring."
- Forgetting that acceptance criteria varies: 100k RPS is different problem from 1M RPS.

**Production references to name:**
- Databricks batch-reporting: 10x tail latency, eliminated Redis SPOF.
- Google SRE K=2 adaptive throttling: no central coordination needed.
- Stripe four tiers: clear deployment order and safety practices.
- Kubernetes APF: sophisticated fairness with shuffle sharding.
- Envoy: local + global layering, shadow mode for rollouts.


---

## Spot-check notes (added 2026-09-13)

- The Databricks blog was fetched directly. Confirmed: original stack Envoy ingress plus Rate Limit Service plus a single Redis; p99 network latency 10 to 20 ms on some clouds; terminology RateLimitGroup, dimensions, descriptors; Dicer autosharding; batch reporting about every 100 ms with `outstandingHits` and `rejectedHits` per key and a response of `rejectTilTimestamp` and `rejectionRate`; token bucket replacing fixed windows; about 5% overage tolerated; migration via a localhost sidecar and a traffic simulation framework. https://www.databricks.com/blog/high-performance-ratelimiting-databricks
- No candidate report with the literal words "datacenter network throttling" was found. The closest reports are "distributed rate limiter at millions of requests per second" with hierarchical dimensions. Treat the bandwidth variant as the Google-style reading of the same prompt (BwE).
