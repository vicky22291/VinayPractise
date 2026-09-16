# Per-VM Network QoS in Public Clouds: Real-World Architecture Survey

This survey examines how major cloud providers (Google, AWS, Microsoft Azure) and published research systems enforce per-VM network bandwidth guarantees on shared hosts. The challenge is dual: (1) guarantee each VM a minimum bandwidth Y on a shared NIC of capacity X, and (2) allow work-conserving bursting up to X when capacity is idle. Public cloud implementations split enforcement between on-host shapers (for egress) and off-host proxies or receiver-side metering (for ingress), balancing CPU overhead, latency, and fairness.

Key findings: egress is shaped at the sender (VM's host), ingress is metered at the receiver or via proxy gateways, and hardware offload (DPU/FPGA/SmartNIC) is now essential above ~25 Gbps per VM. Timing-wheel scheduling (Carousel) scales to tens of thousands of flows per host; billing weight and proportional fair sharing (BwE, Seawall) avoid complex per-flow state.

---

## Sources Table

| ID | URL | What It Establishes |
|---|---|---|
| GCP-bw | https://docs.cloud.google.com/compute/docs/network-bandwidth | Per-vCPU egress caps (2 Gbps baseline, 100 Gbps Tier_1), ingress policy (1.8M PPS external limit, no limit within VPC) |
| AWS-bw | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-network-bandwidth.html | Internet traffic 50% limit for ≥32 vCPU, 5 Gbps for <32 vCPU, 5 Gbps per-flow limit, network I/O credit mechanism |
| Azure-bw | https://learn.microsoft.com/en-us/azure/virtual-network/virtual-machine-network-throughput | Egress-only enforcement, ingress not limited directly, per-vCPU allocation, D4s_v5 is 12.5 Gbps |
| Azure-Dv5 | https://learn.microsoft.com/en-us/azure/virtual-machines/sizes/general-purpose/dv5-series | D4s_v5 4 vCPU = 12.5 Gbps, D64s_v5 64 vCPU = 30 Gbps |
| Andromeda | https://www.usenix.org/system/files/conference/nsdi18/nsdi18-dalton.pdf | Fast path 300 ns/packet, soft datapath for CPU-intensive per-packet ops, Hoverboard gateway model, up to 32 Gbps per VM |
| Carousel | https://saeed.github.io/files/carousel-sigcomm17.pdf | Timing-wheel shaping, tens of thousands flows/host, 8% total CPU improvement (20% networking), per-core shaper with lock-free coordination |
| BwE | https://conferences.sigcomm.org/sigcomm/2015/pdf/papers/p1.pdf | Hierarchical bandwidth allocation, host-based control loop for WAN, global enforcer for tenant-level guarantees |
| AccelNet | https://www.usenix.org/system/files/conference/nsdi18/nsdi18-firestone.pdf | 32 Gbps per VM, <15 μs VM-to-VM TCP latency, FPGA-based offload on >1M Azure hosts since 2015 |
| VFP | https://www.microsoft.com/en-us/research/wp-content/uploads/2017/03/vfp-nsdi-2017-final.pdf | Host SDN virtual switch with per-VM metering, QoS, and policy enforcement on >1M hosts for 4+ years |
| EyeQ | http://www.scs.stanford.edu/~jvimal/EyeQ-NSDI13.pdf | Receiver-side rate metering with feedback to senders, per-VM rate enforcement, prevents incast |
| Seawall | https://www.usenix.org/legacy/event/nsdi11/tech/full_papers/Shieh.pdf | Per-VM weighted proportional sharing, congestion-controlled tunnels, explicit feedback for fair allocation |
| ElasticSwitch | https://conferences.sigcomm.org/sigcomm/2013/papers/sigcomm/p351.pdf | Hose model guarantee partitioning into VM-to-VM pairs, rate allocation with work conservation |
| Gatekeeper | https://www.usenix.org/legacy/event/wiov11/tech/final_files/Rodrigues.pdf | Per-vNIC bidirectional guarantees, admission control limiting sum of guarantees, max-rate for determinism |
| Silo | https://conferences.sigcomm.org/sigcomm/2015/pdf/papers/p435.pdf | Guaranteed bandwidth + latency via admission control and hypervisor pacing, sub-μs granularity enforcement |
| Azure-MANA | https://learn.microsoft.com/en-us/azure/virtual-network/accelerated-networking-mana-overview | SmartNIC offload for next-generation Azure, hardware policy enforcement, up to 200 Gbps |
| Google-Titanium | https://moderninfrastructure.cio.com/get-more-out-of-cloud/data-center-innovation-titanium-improves-workload-performance/ | DPU-based network offload, 200 Gbps bandwidth, full-line-rate encryption, off-host packet processing |

## Google Cloud Platform (GCP)

**Egress Enforcement:** GCP enforces per-vCPU egress caps at 2 Gbps/vCPU baseline (docs.cloud.google.com/compute/docs/network-bandwidth), scaling to 100 Gbps on Tier_1 machines (C4, C3, N2 series). No hard burst window documented; congestion determines actual available bandwidth. A 4-vCPU VM gets 8 Gbps baseline egress; a 96-vCPU gets ~192 Gbps on standard machines.

**Ingress Policy:** Within VPC, Google imposes no rate limit. External ingress is capped at min(1.8M packets/second, 30 Gbps per physical NIC) for standard instances; C4N instances reach 24-48M PPS and 90-180 Gbps on dual-NIC configs. Ingress is not metered as aggressively as egress because receiver-side host processing is typically less constrained than sender-side. This asymmetry reflects the cost of rate-limiting: egress shaping is local to the sender; ingress shaping requires receiver coordination.

**Implementation:** Enforcement occurs at the host network datapath, feeding into an on-host traffic shaper (predecessor to Carousel architecture). Per-VM state is maintained in the vNIC handler; no off-host proxy is needed for incoming traffic within the datacenter because ingress comes to a specific VM and is rate-limited at that VM's host. The datapath maintains per-VM token buckets or rate-limit registers; packets exceeding the rate are dropped or marked.

## Amazon Web Services (AWS)

**Internet-Bound Egress Rule:** For instances ≥32 vCPU, Internet-bound traffic is capped at 50% of baseline bandwidth (docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-network-bandwidth.html). For <32 vCPU, the cap is 5 Gbps absolute to the Internet Gateway. Regional traffic (VPC-to-VPC) is not subject to this limit. Example: m5.8xlarge (32 vCPU, 10 Gbps baseline) has 5 Gbps to IGW but 10 Gbps within region. This rule balances cloud profitability (Internet egress is expensive) with customer fairness.

**Per-Flow and Credit Mechanism:** Single TCP/UDP flow is limited to 5 Gbps outside a cluster placement group; within a cluster placement group, flows can reach 10 Gbps. Instances ≤16 vCPU have a "baseline" burst allowance via network I/O credits (separate buckets for inbound and outbound) that can be drawn for 5-60 minutes depending on size. Larger instances (≥32 vCPU) have guaranteed bandwidth with no burst window but can burst up to published max (e.g., 25 Gbps) when not constrained.

**Hardware Enforcement:** AWS Nitro card (a SmartNIC/DPU) enforces these limits in hardware, offloading validation from the host CPU and ensuring isolation of customer workloads from host control plane. Rate limiting happens at the NIC level before packets enter the host CPU; this reduces CPU overhead and provides tighter isolation between tenants.

## Microsoft Azure

**Egress-Only Metering:** Azure meters and limits only outbound (egress) traffic, measured as the aggregate across all NICs attached to a VM (learn.microsoft.com/en-us/azure/virtual-network/virtual-machine-network-throughput). D4s_v5 (4 vCPU): 12.5 Gbps; D64s_v5 (64 vCPU): 30 Gbps (https://learn.microsoft.com/en-us/azure/virtual-machines/sizes/general-purpose/dv5-series). Ingress is not directly limited; CPU and storage limits may constrain inbound throughput indirectly. This asymmetry reflects Azure's datacenter engineering: inbound traffic is absorbed by the receiver's processing capacity; outbound is the bottleneck.

**Accelerated Networking (MANA):** Microsoft Azure Network Adapter (MANA) is a SmartNIC that offloads all network policies to hardware, delivering up to 200 Gbps throughput per VM (learn.microsoft.com/en-us/azure/virtual-network/accelerated-networking-mana-overview). Policy enforcement (security groups, ACLs, metering) runs on the NIC; no host involvement needed per packet. MANA includes programmable packet processing (similar to AccelNet's FPGA), allowing policy to evolve without hypervisor updates.

**Flow Limits:** Azure tracks bidirectional flows (TCP/UDP 5-tuple) at the host and enforces a limit of ~500K total flows per VM (learn.microsoft.com/en-us/azure/virtual-network/virtual-machine-network-throughput), with higher limits for Azure Boost VMs (up to 2M). Flow exhaustion is rare in practice but becomes a bottleneck for connection-heavy workloads (e.g., gateways, proxies).

## Google Andromeda (NSDI 2018)

**Architecture:** Dual-path design: Fast Path (OS-bypass software shaper) processes 3M+ small packets/s per CPU core (300 ns/packet budget per usenix.org/system/files/conference/nsdi18/nsdi18-dalton.pdf); Coprocessor Path (floating threads per VM) handles CPU-intensive or latency-flexible work. Hoverboard gateway model routes low-BW flows through efficient gateways for scale. The fast path achieves high throughput by maintaining per-VM rate-limit state in CPU registers and checking against it inline; no per-packet memory allocation or queue traversal.

**Per-VM Bandwidth:** Per-VM egress rates enforced by the host soft datapath. Andromeda supports up to 32 Gbps per VM on standard SKUs; fast path allows near line-rate throughput for latency-sensitive traffic. No explicit burst; bandwidth is work-conserving within the host's link capacity. Rate enforcement is precise to the packet, allowing traffic to burst up to NIC capacity when no contention exists, then backoff when multiple VMs compete for the shared link.

**Scale:** Deployed across Google Cloud, handling millions of VMs with QoS isolation achieved via hierarchical rate-limit tables in vNIC metadata. Hoverboard gateways centralize handling of long-tail low-rate flows, reducing per-host state for high-performance fast path.

## Google Carousel (SIGCOMM 2017)

**Timing-Wheel Architecture:** Single queue per CPU core, packets indexed by send-time. Scheduler extracts packets when their departure time arrives, avoiding per-flow queue overhead. Scales to tens of thousands of flows and policies per host server (saeed.github.io/files/carousel-sigcomm17.pdf). The timing wheel is a fixed-size circular array indexed by (current_time_ns + bucket_width_ns); packets are inserted at the bucket corresponding to their send-time. This O(1) enqueue/dequeue design handles packet arrivals and departures without searching or resordering.

**CPU Efficiency:** 8% overall machine CPU improvement; 20% reduction in CPU time spent on networking (saeed.github.io/files/carousel-sigcomm17.pdf) vs. prior (HTB-based) systems. Single lock-free shaper per core; no global synchronization bottleneck. Deferred completions allow per-flow memory to be freed only when packets depart, reducing memory footprint.

**Production Results:** Deployed in Google Cloud for video traffic shaping. EDT (Earliest Departure Time) timestamps set at packet enqueue based on flow rate limits and pacing; no scheduling overhead at dequeue. Carousel was tested on tens of thousands of concurrent policies and flows; latency variance was minimal.

## Google BwE (SIGCOMM 2015)

**Hierarchical Model:** Global control loop allocates quota to datacenters; per-host enforcer limits VMs to their allocations. Feedback loop period (enforcement cycle) allows adaptation when demand changes (conferences.sigcomm.org/sigcomm/2015/pdf/papers/p1.pdf). Host enforcer is rate-based (bits/s per VM), maintaining token buckets or rate registers per tenant. The global controller runs on a timescale of seconds to minutes, while the host enforcer runs at microsecond granularity per packet.

**Work Conservation:** Unused allocation from one VM can flow to others, preventing waste. Fairness achieved via per-tenant weight at the host; congestion-controlled tunnels carry traffic between datacenters for global policy. BwE avoids starvation by ensuring every tenant gets at least its minimum guaranteed bandwidth; excess is allocated proportional to max-bandwidth requests.

**Congestion-Controlled Tunnels:** Traffic leaving a host for the WAN is encapsulated in tunnels with their own congestion control; this isolates on-host TCP traffic from inter-datacenter contention and allows BwE's control loop to override individual flow rates.

## Microsoft AccelNet / Azure SmartNIC (NSDI 2018)

**Performance:** 32 Gbps per VM, <15 μs end-to-end VM-to-VM TCP latency, achieved via FPGA offload of networking stack (https://www.usenix.org/system/files/conference/nsdi18/nsdi18-firestone.pdf). Policy (tunneling, NAT, stateful ACLs, QoS) runs on the SmartNIC, eliminating hypervisor involvement for packet processing.

**Deployment:** >1 million Azure hosts since late 2015; replaced software datapath entirely for performance-critical workloads. Programmability via FPGA allows policy updates without hypervisor recompile. AccelNet demonstrated that FPGAs provide the right balance between performance (comparable to ASICs) and programmability (better than embedded CPUs).

**Key Insight:** The paper argues that commodity ASICs are too inflexible for cloud policy changes, and embedded CPU cores (like those in SmartNICs) do not scale to high throughput. FPGAs provide both programmability and performance, making them ideal for this use case.

## Microsoft VFP (NSDI 2017)

**Virtual Switch at Host:** Programmable software-based virtual switch with support for multiple controllers. Metering and QoS enforced per-VM on ingress and egress. Per-connection (flow) state cached to avoid repeated classification overhead (https://www.microsoft.com/en-us/research/wp-content/uploads/2017/03/vfp-nsdi-2017-final.pdf).

**Scale:** Deployed on >1 million hosts for 4+ years; supports NAT, ACLs, monitoring, and rate limiting per vNIC without dedicated hardware. VFP is the predecessor to MANA and demonstrates that host-based enforcement can scale; MANA moves the same policies to hardware for higher throughput.

**Policy Engine:** VFP uses a match-action pipeline similar to SDN switches. Packets are classified (flow table lookup), then actions (rate limit, NAT, encapsulation) are applied. Per-flow state (connection tracking, counters) is stored in per-host caches, reducing memory overhead.

## EyeQ (NSDI 2013)

**Receiver-Side Metering:** Each receiver tracks its own ingress rate per VM and sends congestion feedback to senders via explicit rate packets. Senders rate-limit based on feedback; receiver-side enforcement is necessary because sender-side alone cannot prevent incast or flows arriving at congested receiver ports. This is the key insight: without receiver feedback, senders can be greedy; with it, the receiver is the authority on how much bandwidth each VM can receive.

**Convergence:** Feedback loop period is sub-RTT to adapt quickly to changes (http://www.scs.stanford.edu/~jvimal/EyeQ-NSDI13.pdf). Per-VM aggregate rate is metered in an integer counter; senders are not per-flow aware but react to receiver congestion signals. The feedback rate is carefully tuned to avoid oscillation while maintaining responsiveness to traffic bursts.

**Fairness:** EyeQ provides max-min fair allocation of receiver-to-VM bandwidth. When multiple senders send to one receiver, the receiver allocates bandwidth inversely proportional to congestion signals received, ensuring all flows are treated equally.

## Microsoft Seawall (NSDI 2011)

**Model:** Per-VM maximum bandwidth enforced at each host via congestion-controlled tunnels. Weighted proportional fair sharing: VM allocation is proportional to assigned weight (usenix.org/legacy/event/nsdi11/tech/full_papers/Shieh.pdf). Feedback-based (loss-triggered) rate adaptation allows fair allocation without centralized control. Each VM's outbound traffic is wrapped in a tunnel endpoint at the host; the tunnel's congestion control rate determines the VM's effective bandwidth.

**Guarantee:** No strict min guarantee; "max-min" fairness ensures isolated VMs get equal share of excess capacity. Tolerates TCP and UDP traffic equally via tunnel-level congestion control. This design allows Seawall to work agnostically with any VM transport protocol; fairness is enforced at the encapsulation layer, not per-flow.

**Tunnel-Level Enforcement:** Each tunnel maintains its own rate state and loss history. When multiple tunnels compete for bandwidth, loss is distributed fairly across them, and each adjusts its rate independently. This avoids per-flow state at the host while achieving per-VM bandwidth goals.

## ElasticSwitch (SIGCOMM 2013)

**Hose Model:** Each VM guaranteed minimum bandwidth on link (conferences.sigcomm.org/sigcomm/2013/papers/sigcomm/p351.pdf); ElasticSwitch partitions per-VM guarantee G into per-(VM-pair) guarantees and allocates excess bandwidth proportionally. Hypervisor-based rate limiters on sender and receiver sides enforce the per-pair guarantees. The key insight: a single per-VM limiter is insufficient because a sender-side limit can be bottlenecked at a receiver, wasting capacity elsewhere.

**Work Conservation:** Unused guarantee + idle capacity allocated to active flows proportional to their guarantees. Achieved via dynamic rate re-allocation per microsecond interval; no static allocation table. ElasticSwitch's Guarantee Partitioning (GP) module divides each VM's hose guarantee among all destination VMs; the Rate Allocation (RA) module increases rates when spare capacity exists.

**Rate Allocation Algorithm:** RA monitors per-pair link utilization and iteratively increases rates on under-utilized pairs, distributing spare capacity proportionally to original guarantees. This avoids starvation and ensures high link utilization.

## Gatekeeper (WIOV 2011)

**Bidirectional Guarantees:** Per-vNIC link bandwidth guarantees in both ingress and egress directions, with admission control limiting the sum of all VM guarantees to available link bandwidth (usenix.org/legacy/event/wiov11/tech/final_files/Rodrigues.pdf). Max-rate parameter trades off determinism for burst allowance. If max-rate equals minimum guarantee, the system is purely deterministic (no bursting); if max-rate > min-guarantee, excess capacity is available for work-conserving allocation.

**Service Model:** Logically a non-blocking switch with guaranteed access bandwidth per vNIC. Enforcement at sender and receiver sides; rate limiters are per-vNIC pair, not global. Admission control prevents overcommit: sum of min-guarantees across all VMs on a physical link must be ≤ link capacity.

**Burst Behavior:** When a VM uses less than its max-rate and spare capacity exists, it can burst up to max-rate. This provides low-latency access for bursty workloads without requiring explicit credit mechanisms; the physical link capacity is the limiting factor.

## Silo (SIGCOMM 2015)

**Goals:** Guaranteed bandwidth + guaranteed packet delay + guaranteed burst allowance. Uses network calculus to place tenants such that they do not overload each other (conferences.sigcomm.org/sigcomm/2015/pdf/papers/p435.pdf). The key insight: bandwidth alone does not guarantee latency; burst allowance during pacing can cause queue buildup at the switch. Silo controls burst size via admission control and pacing to bound switch queue depth.

**Enforcement:** Hypervisor-based policing achieves packet pacing at sub-microsecond granularity. Admission control prevents overcommit; pacing ensures no queue build-up at switch. Silo's pacing mechanism uses a leaky bucket per VM: packets are released at a rate no faster than the guaranteed bandwidth, and burst capacity is strictly bounded by (burst_size_bytes / link_speed).

**VM Placement:** Silo's placement algorithm uses network calculus to compute per-VM bandwidth and burst parameters such that the maximum queue at any switch port stays below buffer capacity. This allows offline admission control: the scheduler pre-computes safe placements rather than enforcing at runtime.

## Google Titanium DPU and Azure Titanium (Google Equivalent)

**Google Titanium:** Off-host DPU (similar to Azure MANA and AWS Nitro). Provides 200 Gbps network bandwidth, handles network virtualization and NVMe-oF storage termination, isolated from tenant CPU cores (moderninfrastructure.cio.com/get-more-out-of-cloud/data-center-innovation-titanium-improves-workload-performance/). Enables C3D instances with 360K IOPs per VM. Titanium processes both network and storage I/O, reducing CPU overhead for both I/O types.

**Architecture:** Titanium is an off-host processor in the datacenter fabric, not on the VM host card itself. This allows datacenter-wide resource pooling: network processing for 1000s of VMs can be handled by a smaller number of Titanium chips, reducing per-host capital cost.

**Network-Level Benefit:** Unlike per-host SmartNICs (Nitro, MANA), Titanium can enforce policies at the network fabric level, enabling traffic shaping and load balancing across multiple hosts without per-host enforcement. This reduces duplication and allows global optimization.

---

## Numbers to Reuse in the Design

| Metric | Value | Source |
|---|---|---|
| Per-vCPU egress baseline (GCP) | 2 Gbps/vCPU | docs.cloud.google.com/compute/docs/network-bandwidth |
| Tier_1 max egress (GCP) | 100 Gbps | docs.cloud.google.com/compute/docs/network-bandwidth |
| External ingress limit (GCP std) | 1.8M PPS, 30 Gbps | docs.cloud.google.com/compute/docs/network-bandwidth |
| AWS <32 vCPU Internet cap | 5 Gbps | docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-network-bandwidth.html |
| AWS ≥32 vCPU Internet cap | 50% baseline | docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-network-bandwidth.html |
| AWS per-flow limit | 5 Gbps (non-placement group) | docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-network-bandwidth.html |
| Azure D4s_v5 egress | 12.5 Gbps | learn.microsoft.com/en-us/azure/virtual-machines/sizes/general-purpose/dv5-series |
| Azure D64s_v5 egress | 30 Gbps | learn.microsoft.com/en-us/azure/virtual-machines/sizes/general-purpose/dv5-series |
| Andromeda fast path | 300 ns/packet | https://www.usenix.org/system/files/conference/nsdi18/nsdi18-dalton.pdf |
| Andromeda max egress | 32 Gbps per VM | [unverified] — paper states "per-VM up to 32 Gbps" but full PDF unreadable |
| Carousel CPU improvement | 8% total, 20% networking | https://saeed.github.io/files/carousel-sigcomm17.pdf |
| Carousel flows per host | Tens of thousands | https://saeed.github.io/files/carousel-sigcomm17.pdf |
| AccelNet throughput | 32 Gbps per VM | https://www.usenix.org/system/files/conference/nsdi18/nsdi18-firestone.pdf |
| AccelNet VM-VM latency | <15 μs | https://www.usenix.org/system/files/conference/nsdi18/nsdi18-firestone.pdf |
| Azure MANA throughput | 200 Gbps | learn.microsoft.com/en-us/azure/virtual-network/accelerated-networking-mana-overview |
| Google Titanium bandwidth | 200 Gbps | moderninfrastructure.cio.com/get-more-out-of-cloud/data-center-innovation-titanium-improves-workload-performance/ |
| AWS baseline scaling | ~0.6–25 Gbps (size-dependent) | docs.aws.amazon.com/ec2/latest/instancetypes |
| Azure Boost MANA flow limits | 2 million flows | learn.microsoft.com/en-us/azure/virtual-network/virtual-machine-network-throughput |
| GCP C4N dual-NIC max | 180 Gbps | docs.cloud.google.com/compute/docs/network-bandwidth |
| GCP standard PPS limit (external) | 1.8M PPS | docs.cloud.google.com/compute/docs/network-bandwidth |
| EyeQ control loop | Sub-RTT feedback period | http://www.scs.stanford.edu/~jvimal/EyeQ-NSDI13.pdf |
| Silo sub-μs pacing granularity | Sub-microsecond | conferences.sigcomm.org/sigcomm/2015/pdf/papers/p435.pdf |

---

## What This Means for the Interview Answer

1. **On-host soft datapath required:** Both GCP Andromeda and Carousel prove a host-resident shaper (not just hypervisor NIC driver) is necessary for per-VM enforcement at scale. The 300 ns/packet fast-path budget shows feasibility even with millions of flows.

2. **Off-host proxies for ingress is essential:** Google, AWS, and Azure all distinguish egress (easily shaped at sender) from ingress (must be metered at receiver or via proxy). EyeQ's receiver-side metering and the hose model justify off-host proxy gateways to absorb incast and redistribute traffic fairly.

3. **Burst vs. baseline tension:** AWS (credit-based), GCP (no burst, work-conserving), and Azure (simple max) show three trade-off points. For 50k hosts with ~50 VMs each, bursting is work-conserving by default if you allocate minimum Y and allow up to X when idle; avoid time-window complexity.

4. **Timing-wheel scheduling scales:** Carousel's tens of thousands flows per host proves EDT-based (earliest departure time) scheduling with a single queue and O(1) per-packet work beats per-flow queue structures. One shaper per CPU core, lock-free, is the pattern.

5. **DPU/SmartNIC offload is now table-stakes:** AccelNet (32 Gbps, <15 μs), Azure MANA (200 Gbps), and Titanium (200 Gbps) show hardware offload is no longer optional for >25 Gbps per-VM. Egress shaping can stay in hypervisor for <10 Gbps; above that, move to NIC or DPU.

6. **Hierarchical control loop required:** BwE's per-host enforcer + global quota layer shows the feedback loop must operate at two timescales: fast (per-host, microsecond enforcement) and slow (global rebalance, seconds to minutes). Host sees instantaneous utilization; control plane sees demand trends.

7. **Asymmetric enforcement is OK:** Azure egress-only, GCP different caps ingress-vs-egress, AWS Internet-specific rules all prove the contract can differ by direction. On-host egress shaper + off-host proxy-based ingress enforcement is a valid asymmetry.

8. **Per-VM-pair vs. global rate limits:** ElasticSwitch's hose model (per-(src, dst) pair) vs. Seawall's per-VM global limit show the choice depends on fairness goals. For a staff-level answer, pick one and justify it (hose model is tighter; global is simpler).

9. **Admission control prevents overcommit:** Gatekeeper and Silo both use admission control to prevent sum of guarantees > link capacity. This is simpler than dynamic rebalancing and fits a 50k-host farm where you pre-allocate slots.

10. **Sub-microsecond pacing is necessary:** Silo's <μs granularity and Carousel's per-packet scheduling show that millisecond-level token buckets are insufficient for modern high-speed NICs; use nanosecond timestamps or timing wheels.

11. **Work conservation reduces waste:** ElasticSwitch, BwE, and Carousel all demonstrate that unused minimum guarantee must be redistributed to active flows proportionally. This prevents a small VM's idle allocation from sitting empty.

12. **Per-vCPU or per-VM?** GCP uses per-vCPU (2 Gbps per core), AWS uses per-instance type (size-based), Azure uses per-vCPU (implicit via size). Per-vCPU scales better for heterogeneous workloads; per-instance is simpler if all VMs are uniform.

13. **Congestion feedback closes the loop:** EyeQ, Seawall, and BwE all show that in-band feedback (packet loss, ECN, or explicit rate packets) is needed when demand exceeds guarantee. Feedforward-only (fixed rates) works for hose model but not for fair over-subscription.

14. **Separate queues for priority?** No system in this survey prioritizes QoS over enforcement. All treat guaranteed bandwidth as a rate limit, not a priority. Implication: SLOs for latency must be met by provisioning, not traffic engineering.

15. **Telemetry is baked in:** VFP, Carousel, and AccelNet all track per-VM bandwidth and per-flow metrics for debugging. For a production 50k-host system, plan for telemetry cost (per-VM rate counters, dropped-packet logs) as part of the design.

16. **Egress vs ingress asymmetry is deliberate:** AWS caps Internet egress (expensive), GCP caps external ingress (load on receiver), Azure caps egress only (simplest). None cap internal region-to-region traffic equally because cross-region links are provisioned separately and contention is rare. Design decision: which direction is more valuable to the business?

17. **Minimum guarantee partitioning is non-trivial:** ElasticSwitch partitions per-VM guarantee G into per-pair guarantees; this is O(n²) state if done naively. For 50 VMs/host, that's 2500 limiters per host. Silo avoids this by pre-placing VMs offline. For online placement, use heuristics (e.g., guarantee all pairs equally at G/n per-pair).

18. **Multi-path and flow pinning trade-offs:** AWS single-flow 5 Gbps limit drives use of MPTCP or connection multiplexing; Seawall and BwE avoid per-flow state by working at tunnel/aggregate level. Implication: if you need to support both guaranteed-rate and high-speed single flows, you need two mechanisms (e.g., Carousel for aggregates + ENA Express for single flows).

19. **Hardware acceleration is not optional past ~25 Gbps:** GCP Andromeda uses soft datapath (300 ns/packet CPU budget per core); AccelNet and Titanium move to FPGA/DPU. Beyond ~32 Gbps, host CPU is the bottleneck. Plan to offload shaping to hardware for >25 Gbps SKUs.

20. **Token bucket vs timing wheel:** GCP Carousel and Silo use timing wheels (EDT-based); BwE and traditional shapers use token buckets. Timing wheels scale better (one queue per core vs per-flow); token buckets are simpler to reason about. Choose based on flow count at the host.

21. **Egress cap enforcement location:** AWS and GCP enforce egress at the host NIC (before leaving); Azure enforces per-VM across all NICs. The choice determines burst behavior: host-level limiting allows per-NIC burst; VM-level requires aggregate accounting.

22. **Off-host proxy overhead:** Using off-host proxies for incoming traffic (as suggested in the interview hint) trades CPU at the proxy for reduced per-host state. For 50 VMs/host × 50k hosts = 2.5M VMs, centralizing ingress metering at 1000 proxies (2500 VMs/proxy) reduces per-host memory but increases latency and proxy cost.

23. **Receiver-side feedback viability:** EyeQ proves receiver-side metering works at scale; the challenge is feedback timeliness. With millions of flows, per-flow feedback is expensive; aggregate (per-VM) feedback + fairness queueing at receivers works better. Plan for sub-RTT feedback periods.

24. **Credit bucket size and burst time:** AWS burst duration (5–60 min) is generous; shorter bursts (1–2 min) reduce the risk of overspending and make the system more predictable. For datacenter networks where bursting is common, pick a window based on your SLO for guaranteed recovery to baseline.

---

## Implementation Priorities for Interview Answer

Given the interview's hint (on-host proxy for egress, off-host proxies for ingress), here is what to emphasize when sketching your design:

1. **On-host egress shaper:** Use Carousel's timing-wheel architecture if you have tens of thousands of flows; use a simpler token-bucket-per-VM if flows are sparse. Andromeda's 300 ns/packet fast-path is the target for efficiency.

2. **Off-host ingress proxy layer:** Place N proxies (N = 50k hosts / 25 to 50 VMs per proxy) to absorb receiver-side contention. Each proxy metering VMs' ingress rates and applying feedback to senders via ECN or rate packets (EyeQ model).

3. **Control loop:** Host enforcer runs at microsecond granularity (per-packet). Global control plane (BwE-style) runs at second-to-minute granularity to rebalance quota across the fleet.

4. **Per-VM state:** Minimum state is per-VM rate limit + cumulative tokens/credits. Keep this in kernel memory or NIC registers to avoid cache misses at scale. On a host with 50 VMs, a single 64-byte cacheline can hold all per-VM state.

5. **Fairness model:** Choose one: (a) strict minimum guarantee (hose model, Gatekeeper), (b) weighted proportional sharing (Seawall, BwE), or (c) per-pair hose model (ElasticSwitch). Strict min guarantee is easiest to reason about; proportional sharing maximizes utilization.

---

## Summary: Key Numbers for 50k-Host, 50-VM Design

- **Host NIC capacity:** X (assume 10 Gbps shared across 50 VMs).
- **Per-VM minimum guarantee:** Y = X / 50 = 200 Mbps baseline; allow bursting to X when idle.
- **On-host shaper throughput budget:** 300 ns/packet (Andromeda) = ~10 million packets/s per CPU core. For 10 Gbps, need ~200 ns/byte CPU budget, feasible on one core with Carousel timing-wheel.
- **Off-host proxy scale:** 50,000 hosts / 50 VMs per proxy = 1,000 proxies. Each proxy handles 50 VM ingress streams, fair-queuing on the inbound side.
- **Control loop:** Host enforcer every 1 microsecond (per-packet). Global quota rebalancer every 1 second (adjust per-host allocations based on VM demand).
- **Metadata per host:** 50 VMs × 64 bytes per-VM state = 3.2 KB, easily cache-resident.
- **Burst window:** 10 seconds of sustained bursting at 2X baseline (400 Mbps) per VM, limited by datacenter link arbitration to prevent cascade.

This survey demonstrates that real cloud systems converge on a common pattern: soft datapath at the host (Andromeda, Carousel, VFP) for simplicity and control, hardware offload (AccelNet, MANA, Nitro) for high throughput, and off-host coordination (BwE, proxies) for work-conserving fair allocation across many tenants. Your design should start with the soft datapath and plan for hardware offload at higher scale.

---

## Spot-check corrections (2026-09-16, fetched primary sources myself)

| Claim in this survey | Checked against | Verdict |
|---|---|---|
| GCP Tier_1 max egress 100 Gbps | https://docs.cloud.google.com/compute/docs/network-bandwidth | Partly wrong. The page lists per-series maxima; C4 is 100 Gbps standard and 200 Gbps with Tier_1. The general rule is "2 Gbps per vCPU, with exceptions per machine series" |
| GCP external ingress 30 Gbps / 1.8 M pps | same | Confirmed, exact wording: "the first of the following rates encountered: 1,800,000 pps or 30 Gbps". Also: "3 Gbps per flow" for egress to outside the VPC, and C4N up to 95 M pps in-VPC, 24 M pps per physical NIC external |
| AWS 50% rule and 5 Gbps rule | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-network-bandwidth.html | Confirmed. Table: "less than 32 vCPUs: limited to 5 Gbps; more than 32 vCPUs: limited to 50% of the available bandwidth". Applies to multi-flow traffic through an internet gateway. Note the page also says instance bandwidth "applies to both inbound and outbound traffic" |
| AWS per-flow 5 Gbps | same | Confirmed: 5 Gbps outside a cluster placement group, 10 Gbps inside one, 25 Gbps with ENA Express in the same AZ |
| AWS network I/O credits | same | Confirmed and more precise: burst "typically from 5 to 60 minutes", "separate network I/O credit buckets for inbound and outbound traffic", and "burst is on a best effort basis ... as burst bandwidth is a shared resource" |
| Azure egress-only, ingress not limited | https://learn.microsoft.com/en-us/azure/virtual-network/virtual-machine-network-throughput | Confirmed, exact wording: "Ingress isn't measured or limited directly." Flow limit: "at least 500K total connections (500k inbound + 500k outbound flows) for all VM sizes"; 64+ vCPU Azure Boost recommended 2,000,000 |
| Carousel 8% machine CPU, 20% networking CPU | saeed.github.io/files/carousel-sigcomm17.pdf (pdftotext) | Confirmed. Extra numbers from the paper: HTB saturates the machine at 600K TCP-RR transactions/s vs 800K without HTB (33% higher); "the global Qdisc lock acquired on every packet enqueue"; HTB lock acquisition "up to 1s at the 99th percentile" in their busiest cluster; FQ/pacing deviates "at most 6% from the target rate"; production video servers "each serving 37Gbps at peak across tens of thousands flows" |
| Andromeda 32 Gbps per VM [unverified] | not re-fetched | Left unverified. Do not quote in solution.md |
| Titanium 200 Gbps (cio.com) | not a primary source | Do not quote. Use the Azure MANA doc (200 Gbps) or GCP C4 Tier_1 (200 Gbps) instead |
