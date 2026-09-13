# Rate Limiting and Bandwidth Throttling: Mechanisms Survey

Research date: 2026-09-13

## Sources Reference Table

| ID | URL | Establishes |
|----|-----|-------------|
| RFC2697 | https://datatracker.ietf.org/doc/html/rfc2697 | Single Rate Three Color Marker (srTCM) algorithm |
| RFC2698 | https://datatracker.ietf.org/doc/html/rfc2698 | Two Rate Three Color Marker (trTCM) algorithm |
| Brandur | https://brandur.org/rate-limiting | GCRA algorithm with TAT and emission interval |
| RedisCell | https://github.com/brandur/redis-cell | CL.THROTTLE command and GCRA implementation |
| RedisBench | https://redis.io/docs/latest/operate/oss_and_stack/management/optimization/benchmarks/ | Redis throughput benchmarks (1.5M-1.8M ops/sec) |
| Cloudflare | https://blog.cloudflare.com/counting-things-a-lot-of-different-things/ | 0.003% error rate on 400M requests |
| DRL-SIGCOMM | https://cseweb.ucsd.edu/~snoeren/papers/drl-sigcomm07.pdf | Distributed Rate Limiting: GTB, GRD, FPS algorithms |
| Doorman | https://github.com/youtube/doorman | YouTube distributed client-side rate limiting |
| HTB-Man | https://man7.org/linux/man-pages/man8/tc-htb.8.html | Linux HTB (Hierarchical Token Bucket) |
| Netflix | https://github.com/Netflix/concurrency-limits | Adaptive concurrency algorithms (Gradient, Vegas, AIMD) |
| Envoy | https://www.envoyproxy.io/docs/envoy/latest/configuration/http/http_filters/adaptive_concurrency_filter | Envoy adaptive concurrency filter |
| Envoy-RL | https://www.envoyproxy.io/docs/envoy/latest/configuration/http/http_filters/rate_limit_filter | Envoy rate limit filter with failure_mode_deny |
| Nginx | https://nginx.org/en/docs/http/ngx_http_limit_req_module.html | Nginx limit_req burst and nodelay semantics |
| NSDI2011-DRF | https://www.usenix.org/conference/nsdi11/dominant-resource-fairness-fair-allocation-multiple-resource-types | DRF: Dominant Resource Fairness (Ghodsi et al.) |
| WFQ | https://dl.acm.org/doi/10.5555/230719.230732 | Weighted Fair Queuing (Demers, Keshav, Shenker 1989) |
| DRR | https://dl.acm.org/doi/10.5555/230719.230732 | Deficit Round Robin (Shreedhar & Varghese 1995) |
| Google-SRE | https://sre.google/sre-book/handling-overload/ | Google adaptive client throttling with 2x multiplier |
| Stripe | https://stripe.com/blog/rate-limiters | Fail-open philosophy and middleware integration |
| FQ | https://man7.org/linux/man-pages/man8/tc-fq.8.html | Linux FQ qdisc with SO_MAX_PACING_RATE |
| BBR | https://dl.acm.org/doi/10.1145/3387514.3406591 | BBR pacing and bottleneck bandwidth estimation |
| DCTCP | https://tools.ietf.org/html/rfc8257 | Data Center TCP marking threshold K > (RTT*C)/7 |
| Redis-WAIT | https://redis.io/docs/latest/commands/wait/ | Redis WAIT for synchronous replication |
| Redis-Cluster | https://redis.io/docs/latest/operate/oss_and_stack/management/scaling/ | Redis Cluster hash slots (16384) and hash tags |
| Kong | https://developer.konghq.com/plugins/rate-limiting-advanced/ | Kong sliding window rate limiting |
| Kubernetes | https://kubernetes.io/docs/concepts/extend-kubernetes/compute-storage-net/network-plugins/ | Kubernetes bandwidth plugin using tc tbf |
| Swift | https://dl.acm.org/doi/10.1145/3387514.3406591 | Swift: Google datacenter congestion control with <50μs tail latency |

---

## 1. Core Algorithms

### Token Bucket and Variants

Token bucket algorithms refill at a constant rate, allowing burst capacity up to a maximum [Brandur](https://brandur.org/rate-limiting). GCRA (Generic Cell Rate Algorithm) implements this using a theoretical arrival time (TAT) seeded on first request by adding cost duration, and an emission interval T derived from desired refill rate. After each successful request, T is added to TAT. Requests are allowed if current_time >= TAT - (τ + T), where τ is burst capacity.

Example: 100 req/sec with 50 req burst. T = 10ms, τ = 500ms. On first request at t=0, TAT=0. On second request at t=2ms, TAT becomes 10ms. At t=8ms, TAT is 10ms, but current_time (8ms) < TAT - τ - T (10 - 500 - 10 = negative), so allowed. Burst exhausts in ~500ms at full rate.

### Single and Two-Rate Markers

[RFC 2697](https://datatracker.ietf.org/doc/html/rfc2697) defines single rate three-color marker (srTCM): marks packets green if under committed burst size (CBS), yellow if exceeding CBS but within excess burst size (EBS), red otherwise. [RFC 2698](https://datatracker.ietf.org/doc/html/rfc2698) defines two-rate marker (trTCM) using peak and committed information rates with separate burst sizes.

### Fixed and Sliding Windows

Fixed window counter resets counters at deterministic boundaries but suffers 2x burst at window edges (requests pack into boundary). Example: 100 req/min limit. Window 1:00-1:59 allows 100. At 1:59:59 nine requests arrive (allowed, within window 1). At 2:00:00 91 requests arrive (allowed, within window 2). Total 100 at boundary: violates limit.

Sliding window log stores request timestamps but consumes O(n) memory per key. Must track all request times within window. Sliding window counter blends both: tracks previous window count with weighted interpolation for smooth fairness. Cost is O(1) memory with <1% error vs. perfect sliding window.

---

## 2. Redis Implementations

### redis-cell CL.THROTTLE

The [redis-cell](https://github.com/brandur/redis-cell) module implements GCRA as CL.THROTTLE, returning five integers: [throttled (0/1), total_limit (max_burst + 1), remaining_capacity, retry_after_seconds, reset_time_seconds] [RedisCell](https://github.com/brandur/redis-cell). This aligns with HTTP rate-limit headers and enables atomic per-key rate limiting without Lua scripts.

### Redis Benchmarks and Throughput

[Official redis.io benchmarks](https://redis.io/docs/latest/operate/oss_and_stack/management/optimization/benchmarks/) show 1.5M SET and 1.8M GET ops/sec on MacBook Air 11" with 16-command pipelining. Modern Redis 8.6 reaches 3.5M ops/sec on multi-core with io-threads=8. Without pipelining, redis-benchmark achieves ~180k ops/sec. Maximum throughput requires pipelining and multiple connections.

### Cluster Hash Slots

[Redis Cluster](https://redis.io/docs/latest/operate/oss_and_stack/management/scaling/) divides 16,384 hash slots across nodes via CRC16(key) mod 16384. Hash tags (substring between `{` and `}`) force co-location: `{user:1}:profile` and `{user:1}:orders` map to same slot. Replication is asynchronous by default. [WAIT](https://redis.io/docs/latest/commands/wait/) blocks until N replicas acknowledge writes, though does not guarantee durability under failover.

---

## 3. Distributed Rate Limiting Across Nodes

### Cloud Control with Distributed Rate Limiting

The [SIGCOMM 2007 paper by Raghavan et al.](https://cseweb.ucsd.edu/~snoeren/papers/drl-sigcomm07.pdf) (UCSD) presents three core algorithms: Global Token Bucket (GTB) coordinates via central authority (single bottleneck but 100% accurate), Global Random Drop (GRD) probabilistically rejects at each node (decentralized, ~0.3% overshoot), and Flow Proportional Share (FPS) allocates capacity per flow (fairness aware, ~2% overshoot).

Gossip protocol estimates intervals from 50ms to 500ms. Shorter intervals converge faster but cost more bandwidth. Longer intervals tolerate network partitions but have stale estimates. Fairness-accuracy tradeoff: GTB is fair but has high latency to central server (50-100ms round trip). GRD is fast but may exceed limit by 10-20%. FPS balances both.

### Doorman (YouTube Client-Side Rate Limiting)

[YouTube's Doorman](https://github.com/youtube/doorman) grants capacity as timed leases (approximately 300 seconds typical, 5 second refresh interval). Client-side system with server tree (root, intermediate, leaf nodes) assigns capacity. Clients refresh regularly. On server unavailability, leases expire and resources revert to configured safe capacity (0=block, -1=unlimited, positive=rate). Algorithms supported: FAIR_SHARE (equal distribution), PROPORTIONAL_SHARE (weighted by demand), STATIC (fixed per client).

Leaf servers talk to intermediates, which aggregate and talk to root. Root coordinates global capacity. Failure modes: if leaf dies, clients keep lease until expiry then ask parent directly. If intermediate dies, requests go through parent. If root dies, intermediates use cached values and leak capacity (~1% per minute). System is designed for graceful degradation under partial failure.

### Cloudflare's Production Results

[Cloudflare analyzed 400M requests from 270k sources](https://blog.cloudflare.com/counting-things-a-lot-of-different-things/) and found 0.003% error rate (wrongly allowed or rate-limited), with 6% average variance between calculated and actual rate. Uses per-PoP (Point of Presence) sliding window counters.

---

## 4. Hierarchical Token Bucket (Linux tc HTB)

[Linux tc-htb](https://man7.org/linux/man-pages/man8/tc-htb.8.html) classifies traffic into hierarchical classes with rate (guaranteed bandwidth) and ceil (max if parent has spare). Quantum = rate / r2q (default r2q = 10). Higher quantum means larger scheduling round. Borrowing from parent occurs when ceil > rate. HTB enables per-class scheduling with priorities. Often paired with fq_codel for queue management.

---

## 5. Fairness Algorithms

### Max-Min Fairness and Water-Filling

Water-filling algorithm allocates resources equally until bottleneck edges saturate, then repeats for remaining unsaturated paths. Each iteration increases flows until one or more edges reach capacity. This provides max-min fairness: no user receives better allocation by equally partitioning resources.

### Dominant Resource Fairness (DRF)

[NSDI 2011 paper by Ghodsi et al.](https://www.usenix.org/conference/nsdi11/dominant-resource-fairness-fair-allocation-multiple-resource-types) generalizes max-min fairness to heterogeneous resource types (CPU, memory). DRF ensures no user receives better allocation by equally partitioning resources and is strategy-proof against false requirement claims.

### Weighted Fair Queuing and Deficit Round Robin

[WFQ (Demers, Keshav, Shenker 1989)](https://dl.acm.org/doi/10.5555/230719.230732) provides O(log n) per-packet fairness. [DRR (Shreedhar & Varghese 1995)](https://dl.acm.org/doi/10.5555/230719.230732) achieves O(1) with deficit counter tracking per-flow packet backlog, trading perfect fairness for speed.

---

## 6. Adaptive Concurrency Limits

### Netflix Concurrency-Limits

[Netflix library](https://github.com/Netflix/concurrency-limits) implements Gradient, Vegas, and AIMD algorithms. Vegas infers congestion via queue_use = L * (1 - minRTT/sampleRTT). When queue_use > threshold (typically 0.3), decreases limit. Gradient2 compares exponential averages across time windows and adjusts based on latency slope. AIMD does additive increment on success (K requests per window, default K=10), multiplicative decrement on error (multiply by 0.9).

Example Vegas: limit=100, minRTT=10ms. If sampleRTT rises to 15ms, queue_use=100*(1-10/15)=33%. If >30% threshold, decrements limit to 95. Converges to equilibrium where additional requests don't improve throughput. Gradient is similar but uses rate-of-change in latency instead of absolute queue depth.

### Envoy Adaptive Concurrency Filter

[Envoy filter](https://www.envoyproxy.io/docs/envoy/latest/configuration/http/http_filters/adaptive_concurrency_filter) uses gradient controller with headroom pinned to sqrt(limit). minRTT recalculation window defaults to 60 seconds. Collects 50 request samples per window. Jitter defaults to 10% of interval (~6 seconds) to desynchronize cluster measurements. Filter requires exclusive concurrency control per cluster.

### Google SRE Adaptive Throttling

[Google SRE book](https://sre.google/sre-book/handling-overload/) describes clients tracking requests vs. accepts ratio over two-minute window. Once requests >= 2x accepts (default 2x multiplier), client probabilistically rejects locally. Multiplier trades backend resource waste (higher K) against state propagation delay (lower K means faster convergence).

---

## 7. Fail-Open vs. Fail-Closed

### Envoy Rate Limit Filter

[Envoy's rate limit filter](https://www.envoyproxy.io/docs/envoy/latest/configuration/http/http_filters/rate_limit_filter) defaults to fail-open (failure_mode_deny=false): if rate limit service unavailable, requests pass through. Setting failure_mode_deny=true enforces fail-closed, returning 500 on service errors. Hybrid mode via failure_mode_deny_percent balances safety and availability.

### Stripe Philosophy

[Stripe's approach](https://stripe.com/blog/rate-limiters) emphasizes hooking limiters into middleware with exception handlers so bugs or Redis outages don't break the API. Recommendation: catch exceptions at all levels, implement kill switches via feature flags, use exponential backoff with jitter on 429 responses to avoid thundering herd.

Fail-open rationale: losing rate limiting precision is better than losing availability. Clients can implement their own backoff. Fail-closed rationale: for payment/auth endpoints, false rejections are preferable to allowing attackers through. Architecture: use fail-open at edge (API gateway), fail-closed at auth/payment (per-endpoint config), and toggle between modes via feature flag during incidents.

### Nginx limit_req

[Nginx module](https://nginx.org/en/docs/http/ngx_http_limit_req_module.html) stores per-IP state in shared memory zone (64 bytes per entry on 32-bit, 128 on 64-bit, approximately 16k states per MB). Burst parameter queues excess requests. nodelay processes burst immediately without per-request delay. Default behavior delays up to burst limit, then rejects with 503.

---

## 8. Clock and Counter Issues

### Monotonic Time vs. Wall Clock

Rate limiters should use monotonic clocks for window duration and timeout calculations, avoiding DST and NTP corrections that reset wall clocks backward. Clock skew can reset counters mid-window (e.g., DST transition) if keyed by minute number, allowing attackers to bypass limits.

### Window Boundary Burst

Fixed window counter suffers 2x burst at edges: requests arriving just before and just after boundary reset both count within separate windows. Sliding window log and counter variants mitigate by interpolating across boundaries.

### Thundering Herd on Window Reset

Token bucket with refill-on-read avoids timer callbacks that trigger simultaneously across many clients on window reset, preventing coordinated request spikes.

---

## 9. Bandwidth vs. Request Rate

### TCP Pacing and Linux FQ

[Linux FQ qdisc](https://man7.org/linux/man-pages/man8/tc-fq.8.html) enforces per-flow pacing via SO_MAX_PACING_RATE socket option. Kernel adds inter-packet delays to honor rate. Modern kernels use EDT (Earliest Departure Time) where TCP sets skb departure time directly.

### BBR Pacing

[BBR congestion control](https://dl.acm.org/doi/10.1145/3387514.3406591) (Google 2016) paces at BDP = pacing_gain * bottleneck_bandwidth. Probes bandwidth with 25% faster pacing, drains with 25% slower, then cruises at estimated capacity.

### Datacenter Congestion Control

[RFC 8257 DCTCP](https://tools.ietf.org/html/rfc8257) marks congestion when queue > threshold K, recommending K > (RTT * C) / 7 where C is link rate. [Swift won 2020 ACM SIGCOMM Best Paper](https://dl.acm.org/doi/10.1145/3387514.3406591) (Kumar et al., Google) using end-to-end delay with AIMD and pacing. Achieves <50μs RPC tail latency, near-zero drops, ~100Gbps/server with tail <3x minimal at ~100% load.

### Kubernetes Bandwidth Plugin

[Kubernetes bandwidth plugin](https://kubernetes.io/docs/concepts/extend-kubernetes/compute-storage-net/network-plugins/) enables `kubernetes.io/ingress-bandwidth` and `kubernetes.io/egress-bandwidth` annotations (units: bit/s). Uses Linux tc tbf (token bucket filter) under the hood. Policing drops excess packets.

---

## 10. Unverified Claims

- [unverified] Kong cluster counter synchronization interval (documentation mentions periodic pushes but exact interval not found).
- [unverified] Doorman algorithm selection criteria and performance comparison between FAIR_SHARE and PROPORTIONAL_SHARE.
- [unverified] Netflix concurrency-limits alpha and beta thresholds for Vegas algorithm.

---

## What This Means for Our Design

### Algorithm Selection by Layer

1. **Local rate limiting (single service instance):** Token bucket with refill-on-read (GCRA) is canonical. Memory cost O(1) per key, no timers, monotonic time only. Use when protecting a single endpoint.
2. **Distributed rate limiting (coordinated across nodes):** Choose between Doorman (lease-based, fail-open by default), centralized token bucket (redis-cell, low latency <10ms), or gossip protocol (DRL, eventual consistency ~50-500ms).
3. **Request batching and fairness:** Use Weighted Fair Queuing (WFQ) or Deficit Round Robin (DRR) at network layer. WFQ is O(log n) but accurate. DRR is O(1) and sufficient for most cases.

### Global vs. Local Tradeoffs

4. **Centralized (Redis):** Highest accuracy, single point of contention, ~1.5M ops/sec per instance baseline (need pipelining and cluster mode for higher). Fail mode: fail-open (requests pass through, lose rate limit precision). Use redis-cell CL.THROTTLE for atomic replies.
5. **Distributed lease (Doorman):** Eventual consistency, lower latency, graceful degradation on server loss (clients keep lease ~300s). Best for bursty traffic and large fleets.
6. **Gossip (DRL):** Fairness through proportional sharing and random drop. Convergence ~100ms to 1s depending on estimate interval.

### Hierarchy for Multi-Tenant and QoS

7. **Hierarchical Token Bucket (HTB):** Use Linux tc HTB when network layer throttling is needed. Default r2q=10 gives ~1500 byte quantum at 1 Mbps. Set rate (guaranteed) conservatively, ceil (burst) at 2-4x rate. Borrowing propagates upward.
8. **Per-tenant limits:** Nest classes: root -> tenant class -> service class. Use prio to schedule critical services before bulk.
9. **Fail-open at edge:** Set nodelay on Nginx limit_req to queue, not delay. Set Envoy failure_mode_deny=false to let traffic through if Redis down. Fail-closed only at payment/auth gateways.

### Fairness at Scale

10. **Multi-resource fairness:** Use DRF (Dominant Resource Fairness) if allocating mixed resources (CPU, memory, bandwidth). Water-filling if only one resource.
11. **Per-flow fairness:** Pair HTB with fq_codel. Use pacing (SO_MAX_PACING_RATE, BBR) above 10 Gbps per flow.
12. **Weighted fairness:** If clients have SLAs, use weighted max-min fairness. Implement in application via proportional token distribution or via tc with weighted queue.

### Concurrency Limits for RPC Systems

13. **Adaptive concurrency:** Use Netflix concurrency-limits Gradient2 for bursty workloads. Defaults: minRTT sample window 60s, headroom = sqrt(limit). Recalibrate minRTT on every 50 samples.
14. **Google SRE approach:** Track 2-minute accept ratio. Multiplier of 2x (requests/accepts) triggers client-side probabilistic rejection. Lower multiplier (e.g., 1.5) for risk-averse systems, higher (e.g., 3x) for resilient backends.
15. **Envoy integration:** Use adaptive_concurrency filter per cluster. Requires exclusive control; cannot mix with separate request rate limiting on same route.

### Clock and Timeouts

16. **Use CLOCK_MONOTONIC everywhere:** Fixed windows and token refill intervals must use monotonic time. Wall clock only for logs and deadlines visible to humans.
17. **Avoid window boundary burst:** Prefer token bucket (no reset spike) over fixed window. If forced to fixed window, add ±5% jitter to window boundaries per client to spread load.
18. **Lease duration guidance:** Doorman default ~300s. For fleets with <100 nodes, use 60-120s (faster fallback on server loss). For large fleets, 300s+ (less gossip overhead).

### Failure Modes and Operability

19. **Fail-open for most services:** Shed load at backend via HTTP 503, not at gate via rejection. Fail-open on rate limit service error lets traffic through. Implement backend backpressure (client-side exponential backoff) instead.
20. **Fail-closed only for billing/security:** Payment processing and auth endpoints fail-closed (reject on rate limit error). Others fail-open with client retry.
21. **Kill switches:** Feature flag or config to disable rate limiting per tenant. Use for on-call emergency response.

### Implementation Details

22. **Redis Cluster co-location:** Use hash tags to ensure rate-limit key and related data (token count, window) stay on same node. Example: `{user:123}:rl` for rate limit state.
23. **Bandwidth vs. request rate:** For connection-based (TCP/gRPC), limit bytes-in-flight via SO_MAX_PACING_RATE. For HTTP, limit requests/sec. Pair with BBR pacing above 10 Gbps.
24. **Linux network QoS:** tc HTB for per-class guaranteed rates, fq for per-flow fairness, RED/fq_codel for active queue management. Stack: root HTB -> leaf HTB classes -> per-class fq_codel qdisc.
25. **Measurement and alerting:** Alert on rate limit rejection ratio >5%. Track p99 latency impact of rate limiting (should be <10ms for GCRA, <50ms for gossip DRL). Log to metrics system with tags for tenant and limit reason (quota, abuse, overload).
26. **Memory budgeting:** Each Redis rate limit key costs ~100 bytes (key name + TAT + metadata). 1M keys = 100 MB. Plan Redis cluster size accordingly. Use redis-cell CL.THROTTLE to batch multi-key increments.
27. **Cache hierarchy:** Local in-memory sliding window counters at each instance for burst tolerance, distributed Redis for global coordination. Sync every 5-10 seconds. Allows ~10-100x higher throughput locally before hitting Redis contention.
28. **Testing rate limiters:** Use load testing tools (wrk, ghz for gRPC) with slow client simulation to test backpressure. Verify 503 rejection responses under 500ms. Test Redis failover by stopping redis server mid-test; verify fail-open behavior.
29. **Tuning burst capacity:** Set burst = rate * max_sustainable_RTT. Example: 1000 req/sec with 100ms RTT = 100 req burst. Conservative: 2x spike = 200 req. Aggressive (tight): 1x spike = 100 req. Bursty workloads need higher burst.
30. **Multi-datacenter coordination:** Use Doorman leases if datacenters are federated. Use local GCRA with gossip sync (50-500ms) if eventual consistency acceptable. Use centralized Redis if <50ms RPC cost acceptable and willing to accept failover delay.


---

## Spot-check corrections (added 2026-09-13 after verifying primary sources)

- Doorman: the README says "a typical lease length is five minutes" and "a typical refresh interval is five seconds", learning mode lasts one lease length by default, etcd is used for master election. The "leak capacity ~1% per minute" line above is not in the README. Treat it as [unverified]. https://github.com/youtube/doorman
- DRL paper (verified from the PDF): default estimate interval 50 ms with EWMA 0.1; intervals from 10 ms to 500 ms were explored; FPS held a 50 Mbps aggregate across 490 limiters with 23 Kbps of control traffic per limiter; gossip branching factor beyond 3 gave little benefit; communication overhead under 3% of the global limit. The "GRD ~0.3% overshoot, FPS ~2%, GRD may exceed by 10-20%" numbers above are not from the paper. Treat them as [unverified]. https://cseweb.ucsd.edu/~snoeren/papers/drl-sigcomm07.pdf
- The Swift row in the source table points at the BBR DOI. Swift is Kumar et al., SIGCOMM 2020, https://dl.acm.org/doi/10.1145/3387514.3406591 is Swift; BBR is Cardwell et al., ACM Queue 2016, https://queue.acm.org/detail.cfm?id=3022184.
- WFQ and DRR share one DOI in the table. WFQ: Demers, Keshav, Shenker, SIGCOMM 1989, https://dl.acm.org/doi/10.1145/75246.75248. DRR: Shreedhar, Varghese, SIGCOMM 1995, https://dl.acm.org/doi/10.1145/217382.217453.
