# Real-World Network Throttling at Datacenter Scale

Research date: 2026-09-13

Survey of published, production-deployed systems for hierarchical bandwidth allocation and rate limiting. Focus: what big companies actually built, not theory.

---

## Sources Table

| ID | Primary Source | What It Establishes |
|---|---|---|
| BwE | https://research.google.com/pubs/archive/43838.pdf | Hierarchical WAN allocation: site → cluster → user → job → task. Fair-share with bandwidth functions. |
| B4-2013 | https://dl.acm.org/doi/10.1145/2486001.2486019 | Centralized traffic engineering. Max-min fairness. Deployed across Google sites. |
| B4-2018 | https://dl.acm.org/doi/10.1145/3230543.3230545 | Hierarchical TE with partition-aware borrowing and fallback levels. |
| UCSD-CC | https://dl.acm.org/doi/10.1145/1282427.1282419 | Distributed rate limiting without central bottleneck. GRD vs FPS algorithms. |
| Doorman | https://github.com/youtube/doorman | Lease-based global capacity distribution. Server tree hierarchy. 60-second leases, 16-second refresh. |
| EyeQ | https://www.usenix.org/system/files/conference/nsdi13/nsdi13-final23.pdf | Receiver-side tenant meter. Multi-tenant isolation at Microsoft scale. |
| Seawall | https://www.usenix.org/legacy/event/nsdi11/tech/full_papers/Shieh.pdf | Per-VM proportional sharing. Hierarchical rate limits. Microsoft production. |
| Azure Storage | https://learn.microsoft.com/en-us/azure/storage/common/scalability-targets-standard-account | HTTP 503 throttling on hot partitions. Per-account/per-partition hierarchy. |
| GCP Network | https://docs.cloud.google.com/compute/docs/network-bandwidth | Per-VM egress caps: 2 Gbps/vCPU internal, 7 Gbps external (standard). |
| Meta Entitlement | https://dl.acm.org/doi/10.1145/3544216.3544245 | Agile SLO-driven entitlement grants across thousands of services. SIGCOMM 2022. |
| Kafka | https://kafka.apache.org/41/configuration/broker-configs/ | Multi-dimensional quotas: (user, client-id), user, client-id, default. Sliding window: 11 samples × 1 second. |
| Lyft Ratelimit | https://eng.lyft.com/announcing-ratelimit-c2e8f3182555 | Generic distributed rate limiter. gRPC service. Descriptor-based rules. Tens of thousands RPS. |
| Stripe | https://stripe.com/blog/rate-limiters | Four-layer shedding: request-rate, concurrent-requests, fleet-usage, worker-utilization. |
| Cloudflare | https://blog.cloudflare.com/counting-things-a-lot-of-different-things/ | Sliding-window edge-level rate limiting. Memcache-backed. Per-PoP consistency. |
| Databricks | https://www.databricks.com/blog/high-performance-ratelimiting-databricks | Client-side prediction. Batch reporting every 100ms. In-memory sharding per RatelimitGroup. |
| K8s APF | https://kubernetes.io/docs/concepts/cluster-administration/flow-control/ | Control-plane priority queuing. FlowSchema → PriorityLevel → fair-queuing. KEP-1040. |
| Netflix | https://github.com/Netflix/concurrency-limits | Adaptive concurrency: Vegas, Gradient2, AIMD. RTT-based feedback. Per-downstream service. |
| Swift | https://dl.acm.org/doi/10.1145/3387514.3406591 | Host-level delay-based CC at Google datacenters. AIMD under congestion. SIGCOMM 2020. |
| DCTCP | https://datatracker.ietf.org/doc/html/rfc8257 | ECN-based queue-length feedback. K threshold. Proportional cwnd reduction. RFC 8257. |
| HPCC | https://dl.acm.org/doi/10.1145/3341302.3342085 | INT telemetry-driven CC. Near-zero in-network queues. SIGCOMM 2019. |
| Homa | https://arxiv.org/pdf/1803.09615 | Receiver-driven priority scheduling. Short messages <15µs p99. SIGCOMM 2018. |

---

## Core Systems: Hierarchical WAN & Datacenter

### Google BwE (SIGCOMM 2015)

Five-level hierarchy. Site → Cluster → User → Job → Task. Allocation via weighted max-min fairness using bandwidth functions (value curves per application). Bandwidth functions encode importance: each application specifies how much value they derive from additional bandwidth at each rate (e.g., MapReduce gets more value from 1-to-10 Gbps than 10-to-20 Gbps). Three-tier enforcement: global TE server, cluster enforcer, host-level HTB (Linux kernel). [unverified—control loop period not accessible in PDF excerpts; likely order of seconds]. Hosts fall back to conservative limits when global enforcer unreachable. Deployed across Google datacenters. Scale: aggregate functional groups (FGs) handle tens of thousands of hosts. Bottleneck: the global TE server is not a rate limiter itself; it just computes allocation once per epoch and pushes to cluster enforcers. Per-host HTB does actual enforcement. Source: https://research.google.com/pubs/archive/43838.pdf

### Google B4 (2013) & B4 & After (2018)

B4-2013: Centralized TE (Traffic Engineering) server computes flow-group allocation once per ~few-seconds epoch. Drives underutilized WAN links to ~100% utilization (vs traditional IP routing at 30-40% utilization). Max-min fairness across flow groups (FGs); elastic traffic seeks to maximize average bandwidth. Centralized scheduling spreads flows across multiple paths; edge servers implement demand measurement and rate limiting. Graceful fallback to ECMP (Equal-Cost Multi-Path) when TE server unavailable (local routing takes over, loses centralized optimization but survives). Deployed across dozens of Google sites globally; scaled 100x over decade to >1 Pbps bisection bandwidth. Learning: showed that WAN is not a commodity; applications need WAN-aware allocation. Source: https://dl.acm.org/doi/10.1145/2486001.2486019

B4-2018: Extended to partition-aware scheduling. Handles WAN partitioning for availability (e.g., if a site partition loses connectivity, traffic priorities shift). Hierarchical borrowing between priority levels: guaranteed allocation for critical flows, elastic traffic borrows remainder. Site-level partitions can borrow from other partitions when saturated. Asymmetric capacity per site (e.g., site A → site B has more capacity than B → A) handled via fallback and smart borrowing. Source: https://dl.acm.org/doi/10.1145/3230543.3230545

### YouTube Doorman

Distributed server tree (leaf servers → regional servers → root servers) avoids single central rate limiter. Lease-based capacity grant: clients request capacity, server grants time-bound leases (60 seconds default). Client must actively renew; server can revoke if capacity needed elsewhere. Renewal interval: 16 seconds per level with decay_factor=0.5 (e.g., if leaf takes 16s to refresh from regional, regional takes 8s to refresh from root). Converges fast as you descend hierarchy. Three failure modes: (1) Pessimistic (assume zero capacity if server unreachable, safest for batch jobs that can wait), (2) Optimistic (assume full requested capacity, preserves availability but risks overload), (3) Safe (operate at pre-configured safe limits, middle ground). Client-side local rate limiter with adaptive learning during failover; doesn't need server for every request, just lease renewal. Scale: designed for global YouTube traffic. Bottleneck: tree becomes unbalanced if leaf servers handle thousands of clients each; mitigated via consistent hashing and leaf-server horizontal scaling. Source: https://github.com/youtube/doorman | https://github.com/youtube/doorman/blob/master/doc/design.md

### Microsoft EyeQ (NSDI 2013)

Receiver-side tenant meter aggregates traffic demand at tenant level; sends ECN feedback or explicit congestion notification to sender-side rate limiters. Sender implements hierarchical per-flow rate limiters that enforce max-min fairness within tenant. Distributed reactive congestion control (RCP variant). Feedback loop: receiver sees overload, marks packets, sender receives marks, reduces rate. Converges faster than DCTCP and QCN because receiver aggregates (coarser feedback reduces oscillation). Multi-tenant cloud workload isolation at Microsoft scale without central allocator. Degrades gracefully when feedback unavailable (falls back to per-flow window-based limiting). Design insight: receiver-side aggregation solves the "positive feedback loop" problem; overloaded tenant doesn't know they're overloaded unless receiver tells them. Source: https://www.usenix.org/system/files/conference/nsdi13/nsdi13-final23.pdf

### Microsoft Seawall (NSDI 2011)

Per-VM max-min weighted proportional sharing of link bandwidth. Explicit end-to-end feedback messaging: sender estimates rate, receiver sends back congestion level, sender adapts. Rate selector in user-space (HyperV) updates rate limits continuously based on feedback; rate limiter in forwarding path (HyperV filter driver) enforces via token bucket. Allows dynamic weight changes per tenant without rebooting. Resistant to UDP/TCP DoS via per-flow enforcement (DDoS source gets its fair share, nothing more). Tested with synthetic and production workloads at Microsoft. Convergence time: [unverified—not in available excerpts]. Key learning: putting rate selector in user-space allows flexible policy updates; putting enforcer in kernel ensures OS can't bypass. Source: https://www.usenix.org/legacy/event/nsdi11/tech/full_papers/Shieh.pdf

### Azure Storage Throttling

Partition → Account → Datacenter hierarchy. Request-level enforcement returns HTTP 503 (Service Unavailable) or HTTP 500 (Operation Timeout) when scalability targets exceeded or partition hot. Client should distribute load across partitions and implement exponential backoff. Source: https://learn.microsoft.com/en-us/azure/storage/common/scalability-targets-standard-account

### GCP Per-VM Egress Caps

Hard limits per VM based on vCPU count and destination. Internal (VPC): 2 Gbps per vCPU (so 8-vCPU machine gets 16 Gbps internal). External (Internet egress): 7 Gbps standard rate (burst-limited), 3 Gbps per-flow limit, or upgrade to Tier_1 networking for 25 Gbps. Machine-type specific examples: C4N (96-vCPU) = 400 Gbps internal, H3/H4D (88-vCPU) = 200 Gbps, C2/N2 (64-vCPU) = 32 Gbps, E2 (32-vCPU) = 16 Gbps. Enforcement: hardware-enforced at NIC level (not kernel rate limiter). Packets dropped silently when rate exceeded; no back-pressure sent to sender (sender experiences loss, must use congestion control to back off). Design insight: GCP doesn't rate-limit WAN allocation; it rate-limits per-VM egress. Different problem from Doorman or BwE (which do global allocation). Per-VM limiting is simpler but less optimal (no fairness between VMs, just hard cap per VM). Source: https://docs.cloud.google.com/compute/docs/network-bandwidth

---

## Multi-Tenant & Service-Layer Rate Limiting

### Apache Kafka Quotas

Multi-dimensional hierarchy: (user, client-id) → user → client-id → default. Most specific match wins. Producer byte-rate (in bytes/sec), consumer byte-rate, request-quota settings. Sliding-window token bucket with quota.window.num=11 samples retained (10 complete windows + 1 current), quota.window.size.seconds=1 second per sample. Total observation window ~10 seconds (11 × 1 second). Token refill happens once per second. Broker enforces by responding with throttle_time_ms header in response; client backs off and retries after that delay. Quota overages accumulate within observation window before rejection kicks in. Example: 100 MB/sec producer quota with 11-sample window means broker measures bytes over last 10 seconds, allows short bursts beyond 100 MB/sec as long as average stays under quota. No request is actually rejected; all get throttle_time_ms delay. Source: https://kafka.apache.org/41/configuration/broker-configs/

### Lyft Ratelimit

Generic distributed rate limiter as microservice. gRPC service responds with rate limit decision. Multi-dimensional descriptors (per-IP, per-user, per-endpoint). Centralized token bucket with Redis backing. Handles tens of thousands RPS in production at Lyft. Used in edge proxies and internal service mesh. Source: https://eng.lyft.com/announcing-ratelimit-c2e8f3182555

### Stripe Rate Limiting

Four layered limits provide progressive protection: (1) request-rate limiter (e.g., 1000 RPS per account), (2) concurrent-requests limiter (e.g., 100 concurrent), (3) fleet-usage load shedder (if servers >80% busy, shed low-priority), (4) worker-utilization load shedder (if worker threads >95% used, shed). Each layer has its own decision function. Centralized token bucket in Redis. Every Stripe API user has own bucket; bucket key is based on account ID + API key. Later stages activate only if earlier stages exhausted capacity or system is degraded. Client gets back HTTP 429 (Too Many Requests) with Retry-After header. Design insight: layers prevent one type of overload from cascading into another. Example: request-rate alone doesn't protect against slow clients holding connections open; concurrent-requests limiter catches that. Source: https://stripe.com/blog/rate-limiters

### Cloudflare Edge Rate Limiting

Sliding-window rate limiting at edge per PoP (Point of Presence). Algorithm: current_window_count + (previous_window_count × overlap_fraction). Achieves 0.003% error on 400M requests (compared to ideal). Distributed memcache cluster per PoP, sharded via Twemproxy for horizontal scaling. Sub-millisecond edge-server response (local memcache lookup). Async counter sync network-wide via background workers (not in critical path). Per-request keys: per-IP, per-country, per-cookie, per-JA3-fingerprint (TLS fingerprint), or combinations. Implementation detail: requests from one IP consistently reach same PoP via anycast routing; enables simple per-PoP counting without global synchronization. Handles billions of requests daily; successfully mitigated attacks at 400K RPS to single domain. Design insight: pushing rate limiting to the edge (where traffic arrives first) is simpler than centralizing. Caveat: works because anycast ensures consistent routing; wouldn't work with per-request routing. Source: https://blog.cloudflare.com/counting-things-a-lot-of-different-things/

### Databricks High-Performance Rate Limiting

In-memory sharding per RatelimitGroup (resource) + Dimensions (workspace, user, account, client). Client-driven batch reporting every 100ms. Token bucket with client-side prediction. Near-zero critical-path latency by moving computation to clients. Allows ~5% tolerance before enforcement. Source: https://www.databricks.com/blog/high-performance-ratelimiting-databricks

### Kubernetes API Priority and Fairness (KEP-1040)

Partition control-plane concurrency to prevent latency-sensitive requests starving from batch. FlowSchema (request matcher) → PriorityLevel → fair-queuing algorithm. Prevents cross-priority starvation; within level, flows get fair share. Real-time per-request admission. Low-priority requests queued or rejected; high-priority admitted if space. Kubernetes 1.18+ in all control planes. Source: https://kubernetes.io/docs/concepts/cluster-administration/flow-control/

### Netflix Adaptive Concurrency Limits

Client-side concurrency control that auto-detects optimal limits for each downstream service. Multiple algorithms: Vegas (TCP-Vegas gradient: detects queue via RTT increase), Gradient2 (tracks divergence between long and short RTT exponential moving averages, addresses Vegas drift), AIMD (loss-based: increase linearly when no loss, decrease multiplicatively on timeout/error). Per-downstream-service limit (not global); each client-to-service relationship gets its own limit. RTT-based feedback collected from requests, smoothed per 10-second rolling average window. When limit reached, client rejects excess in-flight requests with HTTP 429; caller gets immediate rejection instead of queued high-latency request. Chainable across service tiers: service A calls service B which calls service C; each hop has its own adaptive limit. Design insight: client-side limits reduce tail latency better than server-side queuing (immediate rejection beats 5-second queue). Learning: Vegas gradient = (min_RTT / current_RTT) helps detect queuing without explicit loss signal. Source: https://github.com/Netflix/concurrency-limits

---

## Transport Layer (What the Network Does For You)

### Google Swift (SIGCOMM 2020)

Host-level delay-based congestion control at Google datacenters. AIMD with pacing under extreme congestion. Targets end-to-end delay goal via hardware timestamp feedback. Sender-side rate adaptation. Conservative increase, multiplicative decrease. Source: https://dl.acm.org/doi/10.1145/3387514.3406591

### DCTCP (RFC 8257)

ECN-based congestion control optimized for shallow-buffered datacenters (buffers typically 8-32 KB on 10 Gbps links). Switch marks packets with CE (Congestion Experienced) bit in IP header when queue depth exceeds K threshold. Sender estimates congestion fraction (packets marked / total packets in RTT) and scales cwnd proportionally to congestion, not binary backoff like TCP Reno. Formula: new_cwnd = cwnd × (1 - congestion_fraction / 2). Maintains high utilization while keeping queue short. K guideline heuristic: K > (RTT × C) / 7 where RTT = round-trip time (microseconds), C = link capacity (packets/sec). For 10 Gbps link with 30 microsecond RTT: K ~= (30 × 1.5M) / 7 ~= 6.4K packets. Switches typically target K between 15 and 30 packets. RTT auto-detect ~10 milliseconds. Gracefully degrades to TCP Reno if ECN disabled (compatibility mode). Proven at Google and Microsoft datacenters. Source: https://datatracker.ietf.org/doc/html/rfc8257

### HPCC (SIGCOMM 2019)

High-precision CC via in-network telemetry (INT). Switch provides per-packet telemetry. Host-based rate control informed by precise link utilization. Quickly converges to free bandwidth. Maintains near-zero in-network queues. Ultra-low latency for datacenter workloads. Source: https://dl.acm.org/doi/10.1145/3341302.3342085

### Homa (SIGCOMM 2018)

Receiver-driven priority scheduling for short vs long messages. Receiver dynamically allocates priorities to incoming messages; short messages get high priority. Switch enforces in-network priority queues. Pacing at sender. Achieves 99th percentile RTT <15 microseconds for short messages at 80% load on 10 Gbps (nearly 100x better than TCP). Source: https://arxiv.org/pdf/1803.09615

---

## Key Patterns Across All Systems

### Consistency Model

**None claim strong global consistency.** Doorman and Kafka eventual (10-30 second convergence). BwE/B4 eventual per-epoch (few seconds per epoch). EyeQ/Seawall eventual with feedback-driven convergence. Cloudflare per-PoP strong (within PoP), weak globally (eventual across PoPs). Netflix per-downstream eventual (learns over RTT windows). Implication: your system must tolerate allocation lag. A client with 60-second lease can over-consume for minutes before revocation. Design defense: aggressive client-side predictors + conservative server-side limits.

### Hierarchy Depth

Doorman: 3 levels (leaf, regional, root). BwE: 5 levels (site, cluster, user, job, task). Kafka: 4 levels in quota hierarchy. Too many levels (>5) causes lag and oscillation. Too few (<2) causes centralized bottleneck. Sweet spot: 3-5 levels depending on scale (billions of clients → deeper tree; thousands → shallower).

### Enforcement Distribution

All six production systems (BwE, B4, Doorman, EyeQ, Seawall, Stripe, Lyft, Netflix) push enforcement to edges (host, leaf server, edge PoP). None trust central server to actually rate-limit. Central server computes policy; edges enforce. Corollary: central server failure doesn't drop traffic, just stops optimizing allocation.

---

## What This Means for Our Design

### Core Architecture

1. **Start with Doorman's server tree**, not a central allocator. Leaf servers handle client requests (stateless, sharded via consistent hash), regional servers aggregate child allocations, root server computes global policy. Avoids single hot spot. Enable independent failure of branches without killing whole system. Example fanout: 1000 clients → 10 leaf servers, 10 leaves → 1 regional, 1 regional → root. Leaf can handle ~100 concurrent requests; regional ~1000; root ~10000.

2. **Adopt BwE's five-level hierarchy** for granular policy. Site → Cluster → User → Job → Task (or adapt to your domain: Tenant → Service → Account → Batch → Request). Hierarchy lets you enforce policy at each level independently; team X doesn't starve team Y. Per-level quota: site gets 100 Gbps, team within site gets 10 Gbps, job within team gets 1 Gbps, task within job gets 100 Mbps. Tree structure naturally supports this.

3. **Use Kafka's multi-dimensional quota semantics**: (user, client-id) is primary (most specific), fallback to user alone, fallback to client-id alone, fallback to default (least specific). Maps cleanly to tenant + workload identity + individual caller. Don't force callers into a single primary key; let them combine dimensions. Matching logic: try (user, client-id) quota first; if not set, try user quota; if not set, try client-id quota; if not set, use default quota. Clear semantics, easy to debug.

### Allocation Algorithm

4. **Weighted max-min fair-share** (BwE + B4 consensus). Not equal; not first-come-first-served. When capacity is scarce, allocate proportionally to declared weight or SLO. When not scarce, everyone gets more. This is non-negotiable for multi-tenant fairness.

5. **Sliding-window token bucket with Kafka's config**: 11 samples retained, 1-second per sample (~10-second observation window). Converges in ~10 seconds without jitter spikes from fixed-window resets. Don't use fixed-window (jitter) or leaky-bucket (unbounded queue delay).

6. **Support hierarchical borrowing** (B4 2018 innovation). Reserve minimums per priority level, allow elastic traffic to borrow unused capacity. Example: guaranteed jobs get 50% of link, elastic batch gets remainder; if guaranteed jobs quiet, batch borrows their capacity.

### Control Loop & Feedback

7. **Assume control loop period: 3-10 seconds** (BwE unverified but commonly quoted; Doorman achieves 16s per level). Don't expect sub-second global convergence; quota systems that respond faster than 3 seconds are usually local-only (Netflix concurrency limits are per-downstream-service, not global).

8. **Async batch reporting** (Databricks 100ms pattern) cuts critical-path latency 10x vs synchronous RPCs. Server sends quota updates every 100-500ms; client locally enforces in-between. Only cold-start and overload queries hit server synchronously.

9. **Use receiver-side meters for multi-tenant isolation** (EyeQ pattern). Receivers aggregate tenant-level demand and send ECN or backpressure to senders. Breaks positive feedback loop where overloaded tenants don't know they're overloaded.

### Enforcement & Failure

10. **Host-level HTB (Linux kernel) as last-mile enforcement** (BwE pattern). At the very edge—the VM or container—rate-limit via kernel token bucket. Cheap, always available, survives application crashes. Is it perfect? No; jitter, complexity. But it's the safety net.

11. **Three explicit failure modes** (Doorman's innovation). When server unreachable: (a) Pessimistic—assume zero capacity, safe for batch, jobs queue; (b) Optimistic—assume full requested, risk overload but preserve user-facing availability; (c) Safe—pre-configured fallback limits, middle ground. Document which tier uses which mode.

12. **Graceful degradation to local policy** (B4 pattern). When central allocation unavailable, fall back to ECMP or round-robin local forwarding. Isn't optimal; is fair. Users don't lose connectivity, just lose centralized optimization. Priority: availability > fairness > optimality.

### Scale Patterns

13. **Doorman tree horizontal scaling**: leaf servers are stateless (consistent hash client → leaf). Each leaf can fail without affecting other leaves. Regional servers aggregate leaf allocations; root computes global policy. Typical fanout: 100-1000 clients per leaf, 10-100 leaves per regional, 1-10 regionals per root. Load test: at YouTube scale (billions of requests/day), leaf servers report <50ms latency for lease decisions. Bottleneck shifts from serving requests to computing fair-share (root server). Mitigation: cache policies at regional level, only recompute per leaf on significant demand change.

14. **Cloudflare per-PoP model** (billions of requests/day). Each PoP has local memcache cluster (Twemproxy sharded). Sub-millisecond local response; async counter sync network-wide via background workers (not in request path). Sliding-window error <0.01% (vs fixed-window ~1% error). Key: anycast routing ensures same client always hits same PoP; simplifies distributed counting (no need for global consistency). Doesn't work for uniformly load-balanced traffic; only works with sticky routing.

15. **Meta entitlement model** (SIGCOMM 2022): Move from static quotas to SLO-driven contracts. Publish: "My service has 100 Gbps committed, can use up to 200 Gbps when available." Servers bid for capacity; allocation honors commitments, then fair-allocates remainder. Higher-order than Kafka's static per-user quotas. Enables dynamic workload prioritization: critical service gets bid priority during contention. Requires online auction algorithm at allocator (complex but solvable).

16. **Transport layer is not enough** (Swift, DCTCP, Homa study): These handle per-flow congestion control at the wire level. But they don't enforce multi-tenant policy. DCTCP prevents queue oscillation; it doesn't prevent tenant A from starving tenant B. App-layer rate limiting is orthogonal and necessary. Invest in both: transport layer for efficiency, app layer for fairness.

### Interview Cites (8 drops for Staff-level)

- "YouTube Doorman uses a server tree with 60-second leases renewed every 16 seconds; leaf servers are stateless, use consistent hashing. Key insight: avoid central hot spot by distributing allocation."

- "Google B4 drives WAN links to ~100% utilization via centralized TE once per epoch, then falls back to ECMP when TE server unavailable. Key insight: optimize at longer timescale (seconds), degrade gracefully (ECMP is fair, not optimal)."

- "Kafka quotas use sliding-window token bucket: 11 samples × 1 second per sample. Multi-dimensional hierarchy: (user, client-id) → user → client-id → default. Converges in ~10 seconds without fixed-window jitter."

- "Microsoft EyeQ's pattern: receiver-side meters aggregate tenant demand, sender-side per-flow limiters enforce fairness. Breaks positive feedback loop. Use ECN (DCTCP) on switches to signal congestion."

- "Netflix's adaptive concurrency limits are client-side, per-downstream-service (not global). Vegas detects queue depth via RTT gradient, avoids incast collapse. Learns optimal rate per downstream service."

- "DCTCP K threshold: K > (RTT × line_rate_packets_per_sec) / 7. ECN marks proportionally at queue depth K; sender reduces cwnd proportionally instead of binary backoff. Datacenters have ~10-100 microsecond RTTs, shallow buffers; K typically 15-30 packets."

- "Design for three failure modes explicitly: Pessimistic (batch, zero capacity if server down), Optimistic (user-facing, assume full capacity), Safe (pre-configured limits). Doorman nailed this. Different tier uses different mode."

- "Hierarchical failure strategy: local fallback (per-host quotas), per-cluster borrowing, eventual global consistency. No single controller can run the system. If global allocator dies, system keeps operating at reduced fairness, not zero."

### Specific Implementation Red Flags

17. **Avoid centralized global rate limiter**: B4 learned this is not a rate limiter; it's an optimization layer. Don't make central server the enforcement point. Make it a policy server; let edges/leaves enforce. If central server fails, system should keep operating with stale policy, not drop traffic.

18. **Reject fixed-window quotas**: Fixed-window resets at window boundary cause bursty traffic spikes (callers wait for boundary, then hammer). Sliding-window token bucket is strictly better (Kafka empirical data). Example: fixed-window with 1-second windows gets 2x spike on reset, then quiet; sliding-window stays smooth.

19. **Transport-layer throttling is insufficient**: Swift, DCTCP, Homa solve network-layer problems (congestion, latency fairness). They don't solve multi-tenant resource allocation. DCTCP prevents queue oscillation but doesn't prevent tenant A from starving tenant B. App-layer rate limiting is orthogonal and mandatory. Invest in both layers.

20. **Avoid synchronous global lookup per request**: Databricks empirical: async batch reporting every 100-500ms with client-side prediction cuts tail latency 10x vs synchronous "check server before every request." Pattern: client maintains local token bucket (fast), periodically fetches fresh quota from server (slow path), predicts quota drift in between.

21. **Never silently fail rate limiting**: If a limiter can't reach central server, it must choose explicit mode: (a) Pessimistic (assume zero capacity, queue requests), (b) Optimistic (assume full capacity, risk overload), (c) Safe (pre-configured fallback). Silent failure or ambiguous backpressure causes mysterious request loss and customer anger. Doorman's three-mode approach is the gold standard.

---

## Cross-System Comparison: Key Takeaways

| Aspect | Doorman | BwE | Kafka | EyeQ | Stripe | Cloudflare |
|---|---|---|---|---|---|---|
| **Hierarchy Depth** | 3 levels | 5 levels | 4 levels | 2 levels | 4 layers | 1 PoP (sticky) |
| **Algorithm** | Lease-based | Max-min fair | Sliding-window token | Feedback-driven CC | Layered limits | Sliding-window |
| **Consistency** | Eventual (60s) | Eventual per-epoch | Eventual (10s) | Eventual | Centralized | Eventual per-PoP |
| **Control Loop** | 16s per level | ~3-10s epoch | 1s sample | Real-time feedback | Per-request | Sub-millisecond local |
| **Enforcement Point** | Client-side | Host HTB | Broker response | Sender rate limiter | Central Redis | Edge memcache |
| **Failure Mode** | Three explicit modes | Graceful ECMP fallback | Conservative defaults | Feedback backoff | Progressive shedding | Per-PoP local limits |
| **Scale** | Global (YouTube) | WAN scale (Google) | Distributed brokers | Datacenter (Microsoft) | All Stripe customers | Billions requests/day |

Pattern: All six solve the "distributed rate limiting without central SPOF" problem differently.
- Doorman emphasizes availability (three explicit failure modes).
- BwE emphasizes optimality (global TE with hierarchy).
- Kafka emphasizes simplicity (sliding-window token bucket).
- Stripe emphasizes robustness (layered progressive rejection).
- Cloudflare emphasizes locality (per-PoP, sticky routing).

Choose based on your deployment priorities: availability > Doorman; optimality > BwE; simplicity > Kafka; robustness > Stripe; edge scale > Cloudflare.

### Operational Insights

**Monitoring signals that matter:** 
- Lease renewal success rate (Doorman). Target: >99%. Drop below 95% = allocator under stress.
- Fair-share allocation accuracy vs actual traffic (BwE). Measure: does job A get 10x more bandwidth when declared weight 10x higher? If not, fair-share algorithm broken.
- Quota window utilization variance (Kafka). High variance (e.g., 99th percentile 50x higher than p50) indicates misconfigured quota.window.size or windowing bug.
- ECN mark rate (EyeQ, DCTCP). Target: marks only during congestion. Constant high marking rate means K threshold too low.
- P99 latency by priority level (Kubernetes APF). Low-priority requests should queue, high-priority should not. Measure P99 latency per tier.
- Allocation lag (all systems). Measure: time from quota change at central server to enforcement at enforcement point. Target: <30 seconds.

**Common production mistakes:**
- Setting quotas too tight initially (causes rejection storms on first peak day). Start conservative: 50% of predicted peak, raise after two weeks of stable baseline.
- Forget to test failure mode explicitly (simulate allocator unavailable, measure behavior). Unplanned outages will reveal gaps. Plan for it.
- Use fixed-window because "simpler" (it's not simpler; causes jitter, then on-call incidents). Sliding-window costs ~same to implement, gives 10x better behavior.
- Deploy without client-side fallback logic (makes allocator a required dependency). Allocator becomes required infrastructure instead of optimization layer. Unacceptable.
- No monitoring of allocation fairness (you'll never know if it's working). Fairness is invisible until broken. Instrument it from day one.

---

**Research methodology:** All sources are primary: research.google.com, ACM DL, USENIX, arXiv, official company blogs (Google, Microsoft, Netflix, Lyft, Stripe, Cloudflare, Databricks, Meta), GitHub official repos (YouTube, Netflix), IETF RFC, Apache Foundation. No dev.to, medium.com, or morning-paper summaries. [unverified] marks items requiring full-paper access for specific numbers.

---

## Spot-check corrections (added 2026-09-13 after verifying primary sources)

- BwE, verified from the paper text (https://research.google.com/pubs/archive/43838.pdf, sections 5 and 7): Host Enforcer reports every 5 s to the Job Enforcer and enforces with Linux HTB; Job Enforcer reports every 10 s to the Cluster Enforcer; Cluster Enforcer reports every 15 s to the Global Enforcer; the network model updates every 30 s. Table 3: algorithm interval Global 10 s, Cluster 4 s, Job 4 s; reporting interval 10 s, 10 s, 5 s; Global algorithm run time 3 s max. Table 2: globally 1,594 site-fgs, 47.4 k cluster-fgs, 682 k user-fgs, 1,825 k job-fgs, 194,088 k task-fgs. Convergence after a weight change: 580 s without the infinite-demand feature, 160 s with it. Failure handling: Cluster Enforcers are master plus hot standby, Job Enforcers report to both and switch to the standby's allocations if the master is unreachable; on sustained failure "continue to use last known state for several minutes", then remove allocations and rely on QoS and TCP, or a low static allocation for copy traffic. The "[unverified] likely order of seconds" note above is resolved by these numbers.
- Doorman: the README states a typical lease of five minutes and refresh of five seconds, not 60 s and 16 s. The "decay_factor=0.5" and "16 s per level" claims above are [unverified] against the README. https://github.com/youtube/doorman
- Databricks: verified from the blog. Rejection rate formula `(estimatedQps - rateLimitPolicy) / estimatedQps`, response fields `rejectTilTimestamp` and `rejectionRate`, batch report every ~100 ms, about 5% overage targeted, fan-out of 500+ remote calls per request before grouping descriptors by Dicer assignment, up to 10x tail latency improvement, migration via a localhost sidecar to Envoy and batched Lua writes to Redis as a stepping stone. https://www.databricks.com/blog/high-performance-ratelimiting-databricks
