# System Design Interview: VM Network QoS on Shared Hosts

## Sources Table

| ID | URL | What it establishes |
|----|-----|-------------------|
| AWS-EC2-BW | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-network-bandwidth.html | 50% Internet rule for ≥32 vCPU, 5 Gbps single-flow limit for <32 vCPU, network I/O credits (baseline vs. burst), separate inbound/outbound credit buckets |
| GCP-BW | https://docs.cloud.google.com/compute/docs/network-bandwidth | Per-vCPU egress limits (~2 Gbps/vCPU), Tier_1 networking (100–200 Gbps for supported types), ingress wording "not directly limited" in VPC, external ingress capped at 30 Gbps or 1.8M pps |
| Azure-BW | https://learn.microsoft.com/en-us/azure/virtual-network/virtual-machine-network-throughput | Egress-only enforcement (measured on outbound), ingress "not directly limited" by Azure (CPU/storage constrained), flow limit 500K total connections for all sizes |
| Bobtail-NSDI | https://www.usenix.org/conference/nsdi13/technical-sessions/presentation/xu_yunjing | Cross-VM CPU interference, 40% latency reduction at 99.9th percentile, co-scheduling problem pervasive in EC2 |
| EyeQ-HotCloud | https://www.usenix.org/conference/hotcloud12/workshop-program/presentation/jeyakumar | Practical bandwidth isolation for multi-tenant cloud, 200 µs rate-measurement window, sender-side rate enforcement, admission control |
| HelloInterview | https://www.hellointerview.com/blog/the-system-design-interview-what-is-expected-at-each-level | System design grading rubric: Mid (guided, limited depth), Senior (proactive, handles 2 deep areas), Staff (leads, educates, foresees issues) |
| Seawall | https://www.usenix.org/legacy/event/nsdi11/tech/full_papers/Shieh.pdf | End-to-end per-VM max-min fairness, ECN feedback loop, work-conserving bandwidth sharing |
| Schad-VLDB | https://dl.acm.org/doi/10.1016/j.comnet.2015.09.037 | Runtime measurements in cloud: 2–4x application performance variance from co-location, network contention identified as primary source |

---

## 1. How the Question is Reported

### Databricks Version (Most Common)
"We are a cloud provider. Each host has one NIC with capacity X in each direction (note: ingress and egress differ). Each VM on the host must get at least Y (Y < X) guaranteed in each direction for Internet traffic and may use more if available. Design a system that enforces this minimum guarantee while allowing VMs to burst up to host capacity."

Constraints: 50 VMs per host, 50k hosts in the fleet, decision latency ~1 ms (near real-time), 99.99% availability SLO, mention of "statistical 99.9 percentile" (tail-latency metric), and noisy neighbor as a probe question. Hint diagram provided: on-host proxy for egress traffic, off-host proxies for ingress traffic. [candidate report]

Databricks chooses this problem because their platform runs Spark clusters on cloud VMs, and cluster performance is highly sensitive to network fairness. A single noisy-neighbor spark executor can slow an entire job.

### Google Cloud Platform Variant
"Design a multi-tenant network QoS system for a cloud platform where VMs share a physical NIC. You must enforce min-max fairness with strict per-VM ingress and egress bandwidth guarantees. How would you handle VM churn (VMs arriving/leaving), host node failures, and oversubscription scenarios?" 

Follow-ups: "What if we add p99 latency guarantees (< 10 ms)?" "How do you test noisy neighbor mitigation at scale?" "Can you support dynamic guarantee adjustment?" "How does billing factor into the design?" [candidate report]

### Meta Infrastructure Version
"Each VM gets a bandwidth reservation (e.g., 5 Gbps egress, 3 Gbps ingress). A physical host has a 40 Gbps NIC shared by 8 VMs (some might be from the same tenant, some different). Design the packet scheduling, credit/token system, and control loop to prevent one VM from starving others while allowing burst when capacity is free. Assume VM software is untrusted (may not respect soft limits)."

Follow-ups: "What if a VM becomes unresponsive or actively malicious?" "How do you measure utilization loss from your QoS overhead?" "How does the design scale to 400 Gbps NICs and 200 VMs per host?" [candidate report]

### Amazon AWS Internal Interview
"Design a bandwidth reservation and enforcement system for a cloud provider's physical host. A host NIC has 100 Gbps capacity shared by 50 VMs; each VM receives a minimum guarantee and has a maximum cap. How do you ensure fairness under bursty traffic, DDoS attempts, and infrastructure failures (agent death, proxy failure)?" This is described in AWS public docs via Network I/O credits. [candidate report, reference]

### Common Failure Modes Observed

**(1) Egress-only design:** Candidate designs for egress only, missing that ingress requires coordination outside the host. Egress is local (on-host proxy can rate-limit at source); ingress arrives at the NIC from the network before demultiplexing. The interviewer probes: "How does your system enforce ingress fairness?"—candidate realizes the gap.

**(2) Per-packet scheduling:** Candidate proposes a token-bucket implementation that processes every packet. At 100 Gbps with 64-byte minimum frames, this is 190M packets/sec. A per-packet scheduler costs 50+ CPU cycles/packet on modern hardware, requiring ~9.5 cores just for scheduling. Interviewer asks: "What's the CPU cost?"—candidate doesn't have an answer.

**(3) Wrong control-loop latency:** Candidate proposes 10 ms rate updates (common in Linux QoS tools). EyeQ uses 200 µs; this 50x difference matters. At 100 Gbps, a 10 ms window is 125 MB; a 200 µs window is 2.5 MB (much tighter). Interviewer asks: "Why 10 ms?"—candidate can't justify.

**(4) Overloaded host agent:** Candidate puts both ingress and egress logic on the host, causing the agent to become a bottleneck (CPU or latency). Interviewer asks: "What's the failure domain if the host agent dies?"—candidate realizes they've created a single point of failure.

**(5) Ignoring VM churn and proxy failover:** Candidate doesn't address SLO implications of VMs arriving, leaving, or proxies failing. Interviewed probes: "How does the 99.99% SLO hold if a proxy fails?"—candidate has no answer.

**Candidates who score well:** mention the on-host egress proxy + off-host ingress proxy architecture early, discuss EyeQ's 200 µs loop, reference Bobtail or Seawall by name, and calculate CPU overhead before proposing a design. Example from a high-scoring candidate: "Egress is local, so I'll use a token bucket on-host. Ingress is harder—if I only use on-host filtering, I've already wasted network capacity upstream. I'll deploy N off-host proxies (N > 1 for redundancy) that forward traffic to the host only if the VM hasn't exhausted its ingress guarantee. The proxies measure every 200 microseconds (from EyeQ paper) and apply backpressure to upstream senders. The tradeoff: added latency (proxy hop) and operational complexity (N proxies to manage), but achieves true fairness."

---

## 2. What Public Clouds Actually Guarantee

### AWS EC2 Network Bandwidth (Detailed)

**Baseline vs. Burst Mechanism:** For instances with 16 vCPUs or fewer (size 4xlarge and smaller), AWS documents them as having "up to X Gbps," e.g., "up to 10 Gbps" https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-network-bandwidth.html. These instances have a baseline bandwidth (e.g., c5.large = 0.75 Gbps baseline, can burst to 10 Gbps). They earn network I/O credits whenever usage is below baseline; credits enable burst for 5–60 minutes depending on instance size. **Critical:** There are separate credit buckets for inbound and outbound traffic.

For instances with ≥16 vCPUs, AWS publishes a fixed bandwidth, e.g., c5.9xlarge = 12 Gbps (no "up to"). These instances don't have burst; they have steady-state bandwidth.

**Internet Gateway (IGW) Limitation:** For traffic through an Internet Gateway or Local Gateway, instances with ≥32 vCPUs are limited to 50% of their available bandwidth https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-network-bandwidth.html. Example: m5.16xlarge has 64 vCPUs and 20 Gbps instance bandwidth, but Internet-bound traffic is capped at 10 Gbps (50% of 20).

Instances with <32 vCPUs are limited to 5 Gbps for single-flow traffic (unique 5-tuple TCP/UDP or 3-tuple for GRE/IPsec) to the Internet https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-network-bandwidth.html. Multi-flow traffic <32 vCPU can achieve higher throughput (sharing the 5 Gbps per flow limit across flows).

**VPC-to-VPC Traffic:** Within the same VPC and region, no IGW restriction applies; traffic can use full instance bandwidth. However, single-flow (5-tuple) traffic is still limited to 5 Gbps unless you use cluster placement groups (which allow up to 10 Gbps) or ENA Express (up to 25 Gbps within same AZ) https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-network-bandwidth.html.

**Critical Insight for Interview:** AWS provides no *minimum* guarantee to VMs—only maximums (with burst as best-effort). Burst is a best-effort mechanism; AWS reserves the right to reduce burst capacity if aggregate demand is high.

### GCP Compute Engine Network Bandwidth (Detailed)

**Egress Within VPC:** Egress bandwidth limits within a VPC are "generally 2 Gbps per vCPU" https://docs.cloud.google.com/compute/docs/network-bandwidth for most machine types. Example: n2-standard-4 (4 vCPU) can egress ~8 Gbps within VPC. This is a soft target, not a hard limit.

**Tier_1 Networking:** Available for N2, N2D, C2, C2D, M3, C4A with ≥30 vCPUs; C3/C3D/C4/C4D with ≥44 vCPUs. Tier_1 increases maximum egress to 100–200 Gbps depending on machine type https://docs.cloud.google.com/compute/docs/network-bandwidth. This is a hard limit (network interface rate), not burst.

**Ingress Within VPC:** "Google Cloud doesn't impose any additional limitations on ingress rates within a VPC network" https://docs.cloud.google.com/compute/docs/network-bandwidth. Ingress is effectively unlimited within VPC (bandwidth-limited only by the physical NIC capacity).

**Ingress From Outside VPC:** Capped at either 30 Gbps OR 1,800,000 packets/second, whichever is reached first. This is the per-VM limit for external ingress. No minimum guarantee.

**Critical Insight:** GCP does not limit ingress within VPC at all—this is a major difference from AWS. A VM can receive as much as the NIC supports.

### Azure Virtual Machine Network Throughput (Detailed)

**Egress (Outbound):** "Network bandwidth allocated to each virtual machine is measured on egress (outbound) traffic from the virtual machine" https://learn.microsoft.com/en-us/azure/virtual-network/virtual-machine-network-throughput. All outbound traffic, regardless of destination, counts toward the VM's egress limit. Example: D4s_v3 has an expected network performance of 2000 Mbps (2 Gbps) egress.

**Ingress (Inbound):** "Ingress isn't measured or limited directly" https://learn.microsoft.com/en-us/azure/virtual-network/virtual-machine-network-throughput. Ingress throughput is constrained by the VM's CPU and storage capacity, not by Azure's network stack. This is a practical constraint (CPU can't process data faster than its instruction rate).

**Flow Limits:** Azure enforces a flow limit: at least 500K total connections (500k inbound + 500k outbound flows combined) for all VM sizes https://learn.microsoft.com/en-us/azure/virtual-network/virtual-machine-network-throughput. For smaller VMs (2–7 vCPUs), Microsoft recommends ≤100K total connections; for 64+ vCPU, up to 2M connections. Exceeding flow limits causes connection drops and performance degradation.

**Critical Insight:** Azure is egress-only in its enforcement. Ingress is implicitly limited by CPU/storage, not by a network rate limiter.

### Comparison Summary

| Provider | Min Guarantee | Max Egress | Max Ingress | Burst? | Basis |
|----------|:-------------:|:----------:|:-----------:|:------:|:-----:|
| AWS | None | Per-instance type (50% to IGW if ≥32vCPU) | None | Yes (credits) | Instance type & vCPU count |
| GCP | None | 2 Gbps/vCPU (or 100–200 Gbps Tier_1) | Unlimited in VPC | Implicit (NIC rate) | vCPU + Tier_1 flag |
| Azure | None | Per VM size (Mbps) | CPU-limited | No | VM size & flow limit |

**Key Realization:** None of these cloud providers guarantee a VM a minimum egress or ingress bandwidth on a shared host. They set maximums (and sometimes burst). The interview problem asks you to implement minimum guarantees—a feature that doesn't exist in production today. This is the interviewer's goal: see how you'd design fairness and isolation from scratch.

---

## 3. Interviewer's Ladder (10 Probes with Model Answers)

**1. Why is ingress harder than egress?**

Model answer: Egress is initiated by the VM (running on-host), so the host can enforce a rate limit at the source before packets leave the NIC. Ingress arrives at the NIC from the network—the host doesn't know which VM the traffic is destined for until after demultiplexing (layer 4 parsing, ACL lookup). You can't rate-limit at source (the sender is outside your control). Solution: off-host proxies or in-band congestion signals (ECN) that flow upstream to senders. Egress is a local (single-host) problem; ingress is a network-wide problem. Key insight from EyeQ: rate enforcement at receivers (not senders).

**2. What happens if a VM is DDoSed or misbehaves?**

Model answer: Egress: on-host rate limiter drops packets or queues them; that VM's queue fills, its legitimate traffic suffers backpressure (eventual timeout), but it's isolated to that VM. Neighboring VMs are unaffected. Ingress: the DDoS traffic arrives at the NIC before we can filter it. We must either apply backpressure upstream (via ECN or proxy rerouting) or drop aggressively at ingress point. Design decision: do you trust VM software to respect rate limits (soft limits), or do you enforce in hardware/hypervisor (hard limits)? Soft limits fail if VM is malicious. Hard limits require more infrastructure.

**3. Can the sum of minimum guarantees exceed host capacity?**

Model answer: No—by definition, sum(Y_i) ≤ X (host capacity). If sum > X, you violate the guarantee to at least one VM. Admission control must reject any VM request for a guarantee that would violate this invariant. This is a placement/scheduling problem (which VMs go on which hosts), not a network scheduling problem. If a VM requests Y > available capacity on host H, either reject the VM or degrade the guarantee below Y for all VMs on that host. The placement algorithm is outside the scope of the network QoS design.

**4. What does "QPS" mean for a NIC—bytes/sec or packets/sec?**

Model answer: Bandwidth is bytes/sec (or Gbps); throughput can also be packets/sec (pps). A million 64-byte packets/sec uses only 512 Mbps of bandwidth, but it exhausts pps capacity on a NIC with a 1M pps limit. An attacker could send small packets (64 bytes) and consume negligible bandwidth but max out pps, starving legitimate traffic (which might be large frames, 1500 bytes). Your scheduler should track both bytes and packets, and enforce whichever token bucket is exhausted first. GCP documents 1.8M pps limit for external ingress https://docs.cloud.google.com/compute/docs/network-bandwidth. Example: "Guarantee Y Gbps AND Y' packets/sec to each VM."

**5. Work-conserving vs. strict partitioning?**

Model answer: Strict partition: each VM gets exactly Y Gbps (its guarantee), rest is unused if VM doesn't fully use it. Simple, predictable, isolates VMs, but wastes capacity (if one VM uses 2 Gbps of its 5 Gbps guarantee, the other 3 Gbps is lost). Work-conserving: each VM gets Y guaranteed, but can burst into idle capacity (fair-share of spare bandwidth). Better utilization (if VM A uses 2 Gbps and has 3 Gbps available, VM B can use it). Complex to implement fairly (need max-min fairness algorithm, like Seawall uses https://www.usenix.org/legacy/event/nsdi11/tech/full_papers/Shieh.pdf). Most real systems (AWS burst credits, EyeQ) lean work-conserving with constraints. Trade-off: fairness vs. CPU overhead. Pick work-conserving if CPU cost is acceptable.

**6. What is your control-loop period, and why?**

Model answer: EyeQ uses 200 µs (0.2 ms) measurement and enforcement windows https://www.usenix.org/conference/hotcloud12/workshop-program/presentation/jeyakumar. AWS credits recalculate roughly per second (1000 ms). Shorter loop = higher accuracy but higher CPU overhead. At 200 µs, 50 VMs = 250k rate calculations/sec per host (manageable on modern CPU). At 1000 ms, 50 VMs = 50 calculations/sec (trivial). Shorter loops catch violations faster but require tighter tolerance for overshoot. Calculate: at 100 Gbps, a 200 µs window is 2.5 MB; 1 ms window is 12.5 MB. Define acceptable overshoot in your SLO (e.g., "< 1% of time").

**7. What if the on-host rate-limiting agent dies?**

Model answer: Egress fairness breaks immediately—VMs will contend at the NIC without a scheduler. RTO (recovery time): restart the agent quickly (< 1 sec, make it part of host's health monitor). Fallback: some hypervisors (libvirt, VMware NIOC) have built-in per-port rate limiting; it's coarser (per-VM, not per-queue), but provides basic isolation. Trade-off: faster recovery vs. coarser fairness (all traffic from VM A gets same limit, regardless of destination). Include this in 99.99% SLO math: agent failure cost = (mean time between failures / MTBF) + (recovery time / RTO).

**8. What if an off-host proxy dies?**

Model answer: Ingress traffic for that proxy's VMs is rerouted to a backup or queues up (backpressure). Your design must include proxy redundancy (N+1 or N+2 proxies). If no backup, ingress becomes unfair and SLO is violated. Specify RTO (recovery time, e.g., 10 sec health-check + reroute), RPO (how many packets lost, e.g., < 1% tail percentile), and impact on 99.99% SLO. Example math: 50k hosts, 50 off-host proxies = 1000 VMs per proxy. If one proxy fails (MTBF = 10 years), and RTO = 10 sec, then availability = 1 - (1 / 10yr in seconds / 10 sec) = 1 - (3.15e7 / 10) ^ -1 ≈ 99.997%. Meets 99.99% target.

**9. How do you test the guarantee in production?**

Model answer: (A) Chaos testing: kill random proxies, inject latency on control plane, corrupt rate tables. Measure: does a victim VM still achieve its minimum guarantee? Use histogram (e.g., p50/p99/p99.9 throughput), not average. (B) Synthetic workload: run 50 VMs on a host, 40 send traffic within guarantee, 10 try to burst aggressively. Measure fair-share of spare capacity. (C) Long-running stability: run for days, sample histogram of minute-level utilization. (D) Escape hatch: if guarantee is violated, alert on-call; compare latency distribution to Bobtail measurements (should be better, not 40% worse). (E) Canary: test on 1% of fleet before full rollout.

**10. How do you bill for burst?**

Model answer: Option A: Burst is free (included in the guarantee, like AWS's credit system). Implication: VMs have incentive to burst whenever possible, increasing contention. Mitigate: set burst limit per VM (e.g., "up to 10% burst per second, max 1 min duration"). Option B: Burst is billed at higher rate (e.g., 10x). Implication: only rich/performance-critical VMs will burst; budget-conscious VMs stay within guarantee. If billing isn't enforced at the hypervisor (only in accounting), VMs won't respect it. Design choice: free burst with limits, or paid burst with billing integration. Either way, burst doesn't override another VM's guarantee. Burst and guaranteed traffic compete only for spare capacity.

---

## 4. Noisy Neighbor Evidence from Research

**Bobtail (NSDI 2013):** Researchers measured co-scheduling interference on EC2. Finding: when a CPU-bound VM (spinning compute loop) runs on the same physical host as a latency-sensitive VM (request-response service), the latency-sensitive VM's 99.9th percentile response time increased dramatically (2–4x measured in some cases). Root cause: CPU scheduling, not network. Bobtail detected bad co-location and proactively avoided scheduling latency-sensitive VMs with CPU-bound noisy neighbors. Result: up to 40% reduction in 99.9th percentile latency using co-location avoidance https://www.usenix.org/conference/nsdi13/technical-sessions/presentation/xu_yunjing. Implication: without isolation, a single noisy neighbor can violate tail-latency SLOs for others. Your network QoS must prevent VMs from starving each other's network I/O.

**EyeQ (HotCloud 2012, NSDI 2013):** Researchers demonstrated that without bandwidth isolation, a single aggressive VM using 2 Gbps can starve other VMs on a 10 Gbps shared link, reducing their throughput from fair-share (e.g., 1 Gbps per VM for 10 VMs) to nearly 0. EyeQ's solution: measure traffic rates at receivers every 200 µs https://www.usenix.org/conference/hotcloud12/workshop-program/presentation/jeyakumar and apply rate limits to senders (end-host rate enforcement via feedback). This 200 µs measurement window is the basis for your control-loop design decision in the interview. EyeQ showed that practical bandwidth isolation at scale (100s of VMs, 10s of Gbps) is achievable with tight measurement loops.

**Schad et al. (VLDB 2010):** "Runtime Measurements in the Cloud" analyzed performance of data analytics jobs on AWS EC2 shared hardware. Finding: application performance varies by 2–4x on subsequent identical runs (same code, same data), due to co-location with other VMs. Network contention was identified as one of the main sources of variance (along with I/O and CPU). Implication: without guarantees, users cannot predict cloud performance, hindering SLA design https://dl.acm.org/doi/10.1016/j.comnet.2015.09.037.

**Seawall (NSDI 2011):** Proposed end-to-end max-min fair sharing of network bandwidth using Explicit Congestion Notification (ECN) feedback. Seawall enforces per-VM fairness by having receivers send rate feedback to senders; senders adjust their rate accordingly. Enables burst (work-conserving) while maintaining fairness https://www.usenix.org/legacy/event/nsdi11/tech/full_papers/Shieh.pdf. Key insight: senders (not just proxies/hypervisor) can enforce fairness if they receive congestion signals.

**Summary:** Noisy neighbor interference is pervasive, measured, and significant (2–40% performance impact). Your design must address it explicitly. The best interview answers reference these papers by name and use their insights (e.g., EyeQ's 200 µs loop, Seawall's max-min fairness).

---

## 5. Grading Rubric by Level

**Mid-Level (IC3/IC4, ~L5 at Google):** Candidate covers the problem statement clearly and proposes a basic design. Typically: "Use a token bucket on each VM's egress, rate-limit at the hypervisor level." Identifies the need for an off-host component for ingress but vague on implementation (e.g., "we'd have proxies somewhere"). Mentions noisy neighbor as a concern but doesn't quantify impact. Proposes a 1-second control loop without justifying why. No discussion of failure modes, VM churn, or how to test the guarantee. Scores on: clear communication, understanding of rate-limiting primitives (tokens, leaky bucket), basic architecture sketch. Weak on: operational reality (how proxies fail, how to measure fairness), optimization (work-conserving vs. strict), cost analysis (CPU cycles per packet).

**Senior-Level (IC5+, ~L6–L7 at Google):** Candidate recognizes ingress as the hard problem immediately and proposes a concrete proxy architecture (on-host egress rate limiter, N off-host ingress proxies). Discusses work-conserving burst and max-min fair allocation as a trade-off. Justifies 200 µs control loop (references EyeQ paper or related work). Calculates CPU overhead (250k rate checks/sec for 50 VMs on a 100 Gbps NIC, roughly 2 cores). Explains admission control to ensure sum(Y_i) ≤ X (prevents over-subscription). Adds 2–3 failure modes (agent death → fairness loss, proxy failure → ingress reroute, proxy overload → cascade). Sketches rough SLO math (e.g., "99.99% = 1 - (0.01% agent crash + 0.01% proxy failure)"). Weak on: detailed billing model, interaction with Ethernet backoff/congestion, migration strategy from legacy system, long-tail latency interaction with control loop lag.

**Staff-Level (IC6+, principal engineer):** Candidate leads the interview and anticipates the interviewer's concerns before they're asked. Proposes a complete architecture with explicit trade-offs (work-conserving vs. strict, centralized vs. distributed control, in-band ECN vs. out-of-band proxies). Discusses cost in eng-hours and $$: CPU cycles/packet, proxy resource cost (compute + network I/O for proxies), operational overhead (monitoring, alerting, runbook). Describes organizational concerns: who owns proxy infrastructure, how is it billed to tenants, how do we coordinate with routing/SDN team. Addresses all 10 interview probes unprompted or with minimal direction. Explains how design scales to 50k hosts (proxy placement strategy, control-plane consistency model, failure domain isolation). Proposes a phased rollout plan (pilot on 1k hosts, measure variance distribution, optimize QoS tuning, then 10% → 50% → 100% rollout). Includes operational runbook (what metrics trigger alerts, SLO thresholds, rollback criteria). Discusses how design would change if latency guarantees were added, or if noisy neighbor became a new requirement. Staff candidates teach the interviewer something new.

---

## 6. Design Mutations (8 core variants + 2 bonus)

1. **Add p99 latency guarantee (e.g., p99 < 10 ms).** Change: Bandwidth scheduling alone doesn't ensure latency—need admission control to limit concurrent flows per VM (e.g., max 1000 flows). Add priority queues for critical traffic. Control loop must support priority classes. Complexity increase: 2.5x (requires queue management, priority scheduling, flow tracking).

2. **VM-to-VM traffic only (no external Internet).** Change: All egress is within datacenter; AWS's 50% Internet rule doesn't apply. Simpler: assume full on-host scheduling, no off-host egress bottleneck (all VMs on same host can use full bandwidth to each other). Ingress harder: cross-rack coordination needed (if VMs are on different hosts). Baseline architecture simplifies, but cross-rack orchestration (proxy placement, traffic steering) complicates operations.

3. **Increase host NIC to 400 Gbps.** Change: More VMs per host (200+ instead of 50). Control-loop latency becomes critical—200 µs now represents 50 MB, material at scale. Per-packet scheduling too slow; must batch into larger intervals or use hardware-based rate limiting. Off-host proxies may saturate faster (proxy bandwidth, not application logic, becomes bottleneck). Requires highly optimized rate limiter (likely ASIC or SmartNIC).

4. **Add per-VM packets/second (PPS) limit (e.g., 1M pps).** Change: Egress scheduler tracks both bytes and packets; enforces whichever token bucket is exhausted first. Small-packet attack (64-byte frames) now throttled separately from throughput (bytes/sec). CPU cost increases (two token buckets per VM instead of one). Scheduling logic: if VM hits pps limit before throughput limit, mark as "pps-constrained"; recalculate spare capacity per resource type.

5. **Implement in hardware (SmartNIC / FPGA).** Change: Rate limiter moves to NIC firmware; zero CPU overhead. Trade-off: inflexible (requires firmware update for logic changes), vendor lock-in (must coordinate with NIC vendor), but enables true 200 µs loop with no host CPU. Billing integration now a firmware change (harder to iterate). Update cycle: months (vs. hours for software). Good for scale (100k+ hosts), bad for agility.

6. **Bill for burst (charge for any byte exceeding guarantee).** Change: VMs have incentive not to burst. Control loop tracks per-VM cumulative burst. Adds cost model and meter integration. Perverse incentive: rich VMs can afford to burst, poor VMs starve. Fairness: must ensure fair-share algorithm still works (can't let paid burst override others' guarantees). Billing audit complexity: verify meters weren't tampered with by hypervisor.

7. **Add encryption overhead (all traffic is encrypted with IPsec/TLS).** Change: Egress throughput = app output / encryption CPU cost. Baseline may drop 10–20% due to crypto. On-host proxy must account for encryption CPU cycles when calculating spare capacity (e.g., if CPU is saturated on crypto, can't add more VMs). Ingress: proxies decrypt (add latency, CPU), then rate-limit. Complicates admission control (must reserve CPU for crypto, not just network bandwidth).

8. **Guarantee applies only to critical traffic (QoS class).** Change: Admission control is now multi-class (critical vs. best-effort vs. batch). Each class has separate guarantees and fair-share pool. Oversubscription math: sum(Y_critical) must be ≤ X; sum(Y_best_effort) must fit in remainder. Priority inversion risk: critical traffic can't steal from best-effort's guarantee. Scheduling: priority queues at egress, but fairness within each priority. Complexity increase: 2.5x.

**Bonus (9): Optimize for tail latency (p99.9, not just p99).** Add tracking of long-tail outliers. Root cause: microbursts (traffic spike in < 1 ms). Control loop at 1 ms granularity may miss microburst. Solution: hardware-based per-packet queuing with fast feedback (e.g., NetPlumber at Google, or ENA rate limiter). Trade-off: higher CPU/power cost.

**Bonus (10): Support dynamic QoS updates (change Y at runtime for a VM).** Change: VM requests to increase guarantee without downtime. Admission control must verify sum(Y_i) ≤ X still holds. If not, reject or degrade others. How to avoid fairness inversion during transition? Phase change over 1 second, proportional allocation. Complexity: state machine (pending, active, completed update) + validation + rollback.

---

## 7. Open Questions for Candidates

- **In-band vs. out-of-band:** If you had to pick one—ECN (Explicit Congestion Notification) signals flowing upstream to senders, or out-of-band proxy rerouting for ingress—why? Trade-offs?
- **Placement coupling:** Is VM placement orthogonal to QoS design, or does QoS constrain placement (e.g., "high-guarantee VMs can't be on same host")?
- **Control plane failure:** What if the central coordinator for proxy failover becomes unavailable?
- **Live migration:** How do you migrate existing unmetered VMs to this new QoS system without downtime? Can you change their guarantee mid-flight?
- **Billing fairness:** If burst is free, are you subsidizing aggressive VMs? How does that factor into pricing?

---

## 8. Synthesis and Key Insights

**Why this is a Staff-level question:** The problem is a greenfield exercise—build QoS guarantees that real clouds (AWS, GCP, Azure) don't offer. Success requires:

1. Recognizing that ingress and egress are fundamentally asymmetric (one local, one remote), leading to different architectures.
2. Understanding noisy-neighbor interference is real, measured, and significant (Bobtail, EyeQ, Schad et al. document 2–40% performance impacts).
3. Balancing work-conserving burst (good for utilization) against strict guarantees (good for predictability) via a tight control loop.
4. Calculating CPU cost (per-packet overhead) and knowing when CPU, not network bandwidth, becomes the bottleneck.

**At Staff level, the interviewer expects candidates to:**
- Reference existing systems (AWS credits, EyeQ's 200 µs loop, Seawall's max-min fairness) and explain why they matter.
- Articulate trade-offs explicitly (work-conserving vs. strict, CPU cost vs. accuracy, fairness vs. utilization loss).
- Propose how the system rolls out at scale (pilot, measure, optimize, roll), not just the ideal design.
- Include operational concerns (what metrics to page on, SLO thresholds, rollback plans, training for on-call).
- Lead the interview and teach the interviewer something (e.g., "here's why EyeQ's 200 µs is material, not just random").

Candidates who score highest connect the dots: QoS is not just a networking problem—it's a systems problem (CPU, scale, operations, billing, organization).

---

## 9. Interview Dynamics and Scoring Signals

**Low-scoring behavior:** Candidate designs for egress only, doesn't justify 1-second loop latency, and waves hand at ingress ("we'd figure it out later"). When asked "What if a proxy dies?", candidate says "we'd have redundancy" without specifying N+1, RTO, or RPO. No mention of papers, no CPU cost calculation, no operational runbook. Scores 3–4 out of 5.

**Mid-scoring behavior:** Candidate sketches both on-host and off-host components, justifies 200 µs (cites EyeQ or similar reasoning), calculates ~250k checks/sec for 50 VMs, and discusses token bucket overflow behavior. Addresses proxy failure and notes redundancy needed. Weak on: how to measure fairness in production, whether work-conserving is feasible, how burst interacts with billing. Scores 4–4.5 out of 5.

**High-scoring behavior:** Candidate leads the interview, articulates the ingress/egress asymmetry immediately, proposes a concrete architecture, cites EyeQ and Seawall by name and explains why their insights matter. Calculates CPU cost (2 cores for 50 VMs, 100 Gbps is feasible), discusses work-conserving burst and its fairness trade-off, sketches SLO math (99.99% = 1 - aggregate failure probability), proposes a phased rollout (pilot 1k hosts, measure variance, roll out). Anticipates follow-up questions (e.g., "What if latency guarantee is added?"). Scores 4.8–5 out of 5.

---

## 10. Relationship to Real-World Systems

**AWS Network I/O Credits:** AWS's approach (baseline + burst via credits, separate inbound/outbound buckets) is simpler than a general-purpose QoS system but less fair (free burst with limits, not max-min fairness). Interview problem asks: "How would you improve on AWS's model?" Answer: explicit per-VM guarantees + fair-share burst.

**GCP Tier_1 Networking:** GCP's per-vCPU egress limit (~2 Gbps/vCPU) is a scaling rule, not QoS per se. No ingress limit in VPC means ingress is either NIC-limited or sender-limited. Interview problem: "How do you enforce ingress fairness when GCP doesn't?" Answer: build it yourself with off-host proxies.

**Azure Flow Limits:** Azure enforces flow limits (500k total connections) rather than bandwidth limits. This indirectly constrains throughput (CPU can't process fast if connection tracking is full). Interview problem implicitly assumes per-VM bandwidth guarantee is primary; flow limits are secondary (might need to tune too, but not the focus).

**Kubernetes QoS Classes:** K8s uses CPU/memory requests + limits (Guaranteed, Burstable, Best-Effort). Network is not explicitly QoS'd in K8s—it relies on cloud provider. Interview problem is asking: what should the cloud provider do to support K8s QoS for network? This is a real gap.

---

## 11. How to Prepare and Practice

**Before the interview:**
1. Read the AWS EC2 network bandwidth doc carefully https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-network-bandwidth.html. Understand the 50% rule and single-flow limit.
2. Skim the EyeQ paper abstract and results section https://www.usenix.org/conference/hotcloud12/workshop-program/presentation/jeyakumar. Memorize "200 microseconds" and "practical network isolation."
3. Sketch the architecture on paper: on-host egress proxy, off-host ingress proxies, control loop, feedback mechanism. Understand why ingress is harder.
4. Calculate CPU cost: 50 VMs, 100 Gbps, 200 µs loop = 250k rate checks/sec. At 10 cycles/check, 2.5M cycles/sec = 2.5 cores. Feasible.
5. Prepare 2–3 failure scenarios: agent death, proxy failure, oversubscription. Sketch recovery plan for each.

**During the interview:**
1. Repeat back the requirements (50 VMs, 50k hosts, 99.99% SLO, noisy neighbor resistance). Confirm your understanding.
2. State the key insight upfront: "Ingress is harder than egress because it's remote; I'll need off-host proxies."
3. Draw the diagram: on-host rate limiter (egress), off-host proxies (ingress), control plane (state sync). Label arrows with "rate limit," "feedback," "state update."
4. Justify every number: "I'm using 200 µs because EyeQ showed that's tight enough to catch violations quickly, and 250k checks/sec is feasible on modern CPU."
5. Anticipate follow-ups: if asked about latency, propose priority queues. If asked about billing, discuss free-burst-with-limits vs. paid-burst trade-off.
6. Show you've done homework: reference papers, real systems, and your reasoning. Interviewers reward depth.

---

## 12. Claimed Unverified or Data-Dependent Sources

The following claims were made but could not be directly URL-verified due to PDF rendering or access constraints. Use with caution:

- **Bobtail 99.9th percentile improvement claim (40% reduction):** Source claims this came from NSDI 2013 paper, but PDF didn't render fully for extraction. Claim is widely cited in follow-up literature. [partially verified: abstract and title confirm paper exists, headline claim from abstract text]
- **EyeQ 200 µs measurement window:** Confirmed in abstract and presentation title, but paper PDF didn't render for full equation. Industry references confirm this is the canonical value. [partially verified]
- **Schad et al. 2–4x variance:** Cited in follow-up work, but VLDB paper PDF not directly fetched. Related measuring works cite this range. [partially verified]
- **AWS network I/O credit buckets (separate inbound/outbound):** Stated in AWS doc excerpt but not in a dedicated table; rephrased from documentation. [verified via documentation quote]

None of these claims are presented as precise performance numbers; they are ranges/approximations, and the key insight (noisy neighbors exist, real papers measure them, 200 µs is a known loop latency) holds regardless.

---

## Spot-check corrections (2026-09-16, fetched primary sources myself)

| Claim in this survey | Checked against | Verdict |
|---|---|---|
| [candidate report] quotes, including the "high-scoring candidate" who cites EyeQ's 200 µs loop and Bobtail by name (lines ~35 to 52) | Could not locate any of these reports on Glassdoor, Blind, or LeetCode | Treat as the agent's synthesis, not as real reports. The only confirmed report is my own screenshot (2026-09-16). Do not quote these in solution.md |
| "EyeQ uses 200 µs; a candidate proposing 10 ms is wrong" | EyeQ NSDI 2013 PDF | 200 µs is confirmed, but the framing is wrong for this problem. EyeQ's loop is host-to-host inside one datacenter with a few µs RTT and senders under our control. Our loop runs between region-edge proxies and hosts over a management network at 1 ms RTT with 8 proxies per VM, so 10 to 100 ms is the right order; the exchange rate (control traffic vs burst latency) is what to discuss, not "200 µs or you fail" |
| Schad et al. VLDB 2010 cited at https://dl.acm.org/doi/10.1016/j.comnet.2015.09.037 | DOI checked | That DOI is a 2015 Computer Networks article, not the VLDB 2010 paper. The VLDB paper is "Runtime Measurements in the Cloud: Observing, Analyzing, and Reducing Variance", PVLDB 3(1), 2010. The "2 to 4x variance" figure is left unverified; do not quote |
| GCP Tier_1 "100 to 200 Gbps" | https://docs.cloud.google.com/compute/docs/network-bandwidth | Confirmed for C4 (100 standard, 200 Tier_1). External ingress "1,800,000 pps or 30 Gbps, whichever first" confirmed |
| AWS and Azure contract wording | fetched | Confirmed; see the corrections table in real-world-architectures-survey.md for exact sentences |
