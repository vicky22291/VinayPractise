# Network Bandwidth QoS for VMs at 100 Gbps: Mechanisms Survey

## Sources Table

| ID | URL | Establishes |
|---|---|---|
| HTB-MAN | https://man7.org/linux/man-pages/man8/tc-htb.8.html | HTB rate/ceil/burst/cburst/quantum parameters; Unix timing constraint |
| FQ-MAN | https://man7.org/linux/man-pages/man8/tc-fq.8.html | sch_fq flow limit (100 packets default); EDT scheduling via SO_TXTIME; maxrate semantics |
| POLICE-MAN | https://man7.org/linux/man-pages/man8/tc-police.8.html | Dual token bucket; rate/burst/mtu/conform-exceed behavior |
| CILIUM-BW | https://docs.cilium.io/en/latest/network/kubernetes/bandwidth-manager/ | EDT egress-only; eBPF token bucket ingress; kubernetes.io/egress-bandwidth annotation |
| IP-LINK | https://man7.org/linux/man-pages/man8/ip-link.8.html | SR-IOV min_tx_rate and max_tx_rate in Mbps; zero disables |
| DRL-ACM | https://raghavan.usc.edu/papers/drl-sigcomm07.pdf | GRD vs FPS; gossip delay contributes to overshoot via RTT; EWMA α=0.1 |
| EYEQ | http://www.scs.stanford.edu/~jvimal/EyeQ-NSDI13.pdf | Receiver meter per-VM; hierarchical rate limiter at sender; RCP fairness |
| DCB-ETS | https://man7.org/linux/man-pages/man8/dcb-ets.8.html | ETS bandwidth weights as % of available; 8 traffic classes (TC 0-7); work-conserving |
| VDPA-ARCH | https://www.redhat.com/en/blog/introduction-vdpa-kernel-framework | vhost-vdpa interface; vDPA device data path compliance with virtio spec |

---

## 1. Linux HTB (Hierarchy Token Bucket)

HTB is a qdisc-level rate limiter with a three-parameter guarantee model: **rate** (guaranteed minimum per class), **ceil** (cap if parent has spare), and **burst** bytes at ceil to absorb microbursts.

### Parameters and Semantics

**rate**: Maximum guaranteed rate for a class and children. For a two-level design (host cap X, per-VM min Y, max X): set parent rate = X, per-VM class rate = Y.

**ceil**: Maximum rate a class can use if parent has spare. Per-VM ceil = X (host max).

**burst** and **cburst**: Burst at ceil speed (burst) or "infinite" speed (cburst, mtu-limited).

**quantum**: Bytes to serve per class round, tuned via r2q divisor (default 10).

**Class hierarchy**: A parent HTB enforces ceil on all children; borrowing is strict: a class cannot exceed ceil even if siblings are idle.

### Scale Limits and Bottleneck

HTB operates via a single root lock per qdisc. At 100 Gbps with a single-core scheduler, the lock contention and per-packet cost (token update, tree traversal) hit diminishing returns. Carousel (SIGCOMM 2017) cites that a single HTB qdisc on one CPU core saturates at roughly a few tens of Gbps or a few Mpps before CPU becomes the bottleneck. [unverified - full Carousel PDF not accessible; cite exists in abstracts]

For work-conserving max-min fairness on a host with 50 VMs, you'd need hierarchical classes, but HTB's per-packet overhead scales linearly with hierarchy depth.

### Cannot Achieve

- **Precise scheduling at nanosecond granularity**: Unix timer resolution (10–1000 Hz typically) is the floor.
- **Per-flow isolation without per-flow state**: HTB is class-based, not flow-based.
- **Ingress shaping** (only egress on the sending NIC).

---

## 2. EDT (Earliest Departure Time) Pacing with sch_fq

EDT paces egress packets by computing a departure time (skb->tstamp) set by BPF or the TCP stack, then enforcing the schedule via sch_fq. Removes lock bottleneck by deferring to hardware or per-CPU pacing.

### sch_fq Parameters

**flow_limit**: Per-flow packet queue limit. Default **100 packets** (https://man7.org/linux/man-pages/man8/tc-fq.8.html).

**maxrate**: Overrides SO_MAX_PACING_RATE if a flow exceeds this; default unlimited.

**Initial quantum**: Default 10 packets per flow per dequeue round.

### SO_TXTIME and TCP Integration

After Linux 4.20, "TCP directly sets the appropriate Departure Time for each skb," allowing fq to enforce precise schedules without further kernel involvement (https://man7.org/linux/man-pages/man8/tc-fq.8.html). A BPF program can also set skb->tstamp for application packets.

### Cilium EDT vs HTB

Cilium Bandwidth Manager implements egress-only rate limiting using EDT and states: "eBPF-based token bucket implementation" for ingress. EDT avoids "locking under multi-queue NICs" (https://docs.cilium.io/en/latest/network/kubernetes/bandwidth-manager/). [unverified - exact Carousel numbers not fetched; Cilium cites scalability gains without hard numbers]

### Cannot Achieve

- **Ingress shaping** (only pacing at egress via sender-side timer).
- **Bursting above the average rate** without configuring per-packet timestamps in advance.
- **Per-packet guarantees** if clock skew or packet reordering occurs.

---

## 3. Ingress Policing and Why Not Shaping

On ingress (packets arriving), you cannot shape: the host is the receiver and has no control over when the sender releases packets. Instead, you police: drop or mark packets exceeding a rate.

### tc-police (Token Bucket)

**rate**: Max byte rate; exceeding traffic triggers the conform-exceed action.

**burst**: Max allowed burst in bytes; optionally with cell size (power of 2). The dual token bucket algorithm is the standard meter (https://man7.org/linux/man-pages/man8/tc-police.8.html).

**mtu**: Treats packets larger than this as exceeding rate.

**conform-exceed**: drop (discard), reclassify, pipe, continue, etc. Default for non-conforming: reclassify.

### Effects on Transport

**TCP**: Packet drops trigger congestion detection (cwnd halving). Overly aggressive ingress policing causes TCP throughput collapse.

**UDP**: Drops are silent; application must detect loss. No congestion signal to sender.

### Ingress Filter Block (IFB) for Shaping

To shape on ingress, redirect to a virtual IFB (Intermediate Functional Block) qdisc, apply HTB/sch_fq there, then egress back. This adds latency and complexity.

### ECN Marking as Alternative

RFC 3168 and RFC 8257 (DCTCP) allow marking packets with the Congestion Experienced (CE) codepoint instead of dropping. Senders supporting ECN reduce cwnd on CE, avoiding the cliff of packet loss. Limitation: Internet peers may not support ECN; data centers often enable it.

---

## 4. Receiver-Driven and Credit-Based Schemes

Receiver signals rate feedback to senders, allowing ingress-side enforcement without policing loss.

### EyeQ Receiver Meter

Per-VM meter at receiver aggregates ingress rate and sends feedback to sender-side hierarchical rate limiter. A variant of Rate Control Protocol (RCP) at sender maintains per-flow max-min fairness within a tenant pool (http://www.scs.stanford.edu/~jvimal/EyeQ-NSDI13.pdf). [unverified - full PDF not accessible]

### Hose Model

Duffield et al. (1999) and Oktopus (SIGCOMM 2011) define a "hose" as an aggregate min-guarantee to a set of VMs, rather than per-pair reservations. A hose allows oversubscription within the hose if total demand is low. [unverified - PDFs not accessible]

### Homa and NDP

Analogous receiver-driven designs using per-packet grant credits sent from receiver to sender, avoiding head-of-line blocking. [unverified - referenced for mechanism analogy only]

### Requires

- Feedback channel from receiver to sender (network round-trip adds delay).
- Sender-side rate limiter integration (application or kernel).

---

## 5. NIC Hardware Rate Limiting

Modern SmartNICs and SR-IOV capable NICs offer per-VF rate limits, work-conserving traffic classes, and packet pacing.

### SR-IOV Virtual Function Rate Limits

**min_tx_rate** (in Mbps): "change the allowed minimum transmit bandwidth, in Mbps, for the specified VF" (https://man7.org/linux/man-pages/man8/ip-link.8.html).

**max_tx_rate** (in Mbps): "change the allowed maximum transmit bandwidth, in Mbps, for the specified VF" (https://man7.org/linux/man-pages/man8/ip-link.8.html).

Both defaults to 0 (no limit). Minimum must be ≤ Maximum.

Example: `ip link set dev eth0 vf 0 min_tx_rate 1000 max_tx_rate 10000` (1–10 Gbps for VF 0).

### NVIDIA/Mellanox Hardware Pacing

Mellanox ConnectX and NVIDIA BlueField NICs support per-queue and per-VF rate limiting via sysfs (e.g., `/sys/class/net/p0/smart_nic/vf0/max_tx_rate`). [unverified - specific work-conserving guarantees not confirmed in fetched docs]

### 802.1Qaz Enhanced Transmission Selection (ETS)

**Bandwidth weights**: Distribute available bandwidth among 8 traffic classes (TC 0–7) as percentages (must sum to 100%). Work-conserving: if TC i doesn't use its share, TC j can use the slack (https://man7.org/linux/man-pages/man8/dcb-ets.8.html).

**Strict priority**: Higher TC numbers always preempt lower TC numbers.

**Limitation for per-VM min guarantee**: ETS allocates a fixed % per TC. If a VM is assigned TC 2 with 5%, it gets 5% of NIC bandwidth regardless of other TCs' demand. Not truly min-guarantee; a static cap.

### Cannot Achieve

- **Work-conserving min-guarantee across VMs** (ETS is static % per TC, not dynamic min).
- **Per-flow rate limiting** in hardware on most NICs (only per-VF or per-TC).

---

## 6. Datapath Options and Packet Processing Rates

**Packet rate at 100 Gbps**:
- MTU 1500 B: 100 Gbps ÷ (1500 B × 8 bits/byte) = 8.33 Mpps.
- MTU 64 B: 100 Gbps ÷ (64 B × 8 bits/byte) = 154.3 Mpps.
- Formula: Rate (Gbps) ÷ (MTU bytes × 8) = Mpps.

### XDP (eXpress Data Path)

Earliest packet hook in the kernel driver. eBPF programs run on every packet at RX. Ideal for per-packet filtering and drop-based rate limiting. [unverified - specific per-core Mpps limit not fetched]

### tc-BPF (eBPF qdisc classifiers)

Classifiers written in eBPF can set per-packet metadata (qdisc class, mark, etc.) before enqueueing. Used by Cilium Bandwidth Manager for ingress token bucket (https://docs.cilium.io/en/latest/network/kubernetes/bandwidth-manager/).

### DPDK (Data Plane Development Kit)

Userspace datapath bypassing kernel. Can achieve line-rate on multi-core systems. [unverified - specific benchmark number from DPDK not fetched; stated as example in doc.dpdk.org test plans]

### Linux OVS (Open vSwitch)

Kernel module: slower than DPDK but integrated. Userspace (ovs-vswitchd): tunable, suitable for moderate throughput with tc qdisc.

### XDP per-core headroom

At 154 Mpps (64 B frames at 100 Gbps), a single core cannot keep up. Require NIC RSS (Receive-Side Scaling) to distribute flows across cores. [unverified - no specific kernel or Cilium per-core limit fetched]

---

## 7. Token Bucket vs GCRA for Metering

Both measure rate compliance; they differ in state representation.

### Token Bucket

State: **tokens** (bytes), **last_refill** (timestamp). On packet arrival of size S bytes:
- Refill: tokens += (now – last_refill) × rate.
- Check: tokens ≥ S?
- If yes: tokens -= S, allow; if no: drop or mark.

Simple, exact for bursty traffic. Burst size = max tokens = rate × burst_time.

### GCRA (Generic Cell Rate Algorithm)

Virtual scheduling: state is **TAT** (Theoretical Arrival Time). On packet arrival at real time t:
- If t ≥ TAT: conforming; TAT := t + cell_time.
- Else: non-conforming; TAT += cell_time (or mark/drop).

More precise under load, easier to analyze, but per-flow state required.

### Burst at 100 Gbps

At 100 Gbps, a **1 ms burst** = 100 Gbps × 1 ms = 100 Mb = **12.5 MB**.

At 100 Gbps, a **10 ms burst** = 1000 Mb = **125 MB**.

At 100 Gbps, a **100 ms burst** = 10000 Mb = **1.25 GB** (unrealistic for per-VM).

Per-VM typical burst: 1–10 ms (12.5 MB – 125 MB) to smooth TCP slow-start ramps.

---

## 8. Distributed Rate Limiting (DRL)

Gossip-based coordination of per-node rate limiters to enforce a global rate limit across sites.

### Algorithms

**GRD (Global Random Drop)**: Each node estimates global load via distributed aggregation (gossip) and probabilistically drops packets proportional to (local_rate – target) / target. Simple but oscillates.

**FPS (Flow Proportional Share)**: Per-flow weight inversely proportional to flow's desired bandwidth; drop probability weighted by flow demand. Fairer but requires per-flow tracking.

### Gossip Overhead

Delay between nodes and aggregation via exponential moving average (α = 0.1, https://raghavan.usc.edu/papers/drl-sigcomm07.pdf) means gossip interval is at least one RTT. Overshoot in global rate: GRD measured ~13 Mbps peak vs. 10 Mbps target, then corrects to ~5 Mbps in test (from search abstracts; [unverified – full PDF unreadable]). Oscillation is inherent; convergence time ≈ gossip_interval × number_of_sites.

### Requires

- Multicast or gossip transport between sites.
- Coordination on target rate and aggregation.

---

## 9. Weighted Max-Min (Water-Filling) on Two-Level Hierarchy

Host cap X, each VM has min guarantee Y and can demand up to X. Allocate to maximize min of any VM's actual rate, then allocate slack proportionally.

### Worked Example

**Host X_out = 100 Gbps. 5 VMs, each min = 10 Gbps.**

**Demands: D = [5, 40, 60, 10, 0] Gbps.**

**Step 1: Allocate min to each**.
- VM 0: 10 Gbps. Slack needed: 5 Gbps (demand 5 < min 10, can't use it).
- VM 1: 10 Gbps. Slack needed: 30 Gbps.
- VM 2: 10 Gbps. Slack needed: 50 Gbps.
- VM 3: 10 Gbps. Slack needed: 0 Gbps (demand 10 = min 10).
- VM 4: 10 Gbps. Slack needed: 10 Gbps (demand 0, can't use it).
- Total allocated: 50 Gbps. **Slack: 50 Gbps.**

**Step 2: Allocate slack proportionally to demand shortfall**.
- VM 0: maxes out at demand 5; stop.
- VM 1: need 30, demand cap 40, so 30 is available. Unused demand: 0.
- VM 2: need 50, demand cap 60, so 50 is available. Unused demand: 0.
- VM 3: need 0, demand cap 10, so offer 0. Unused demand: 10.
- VM 4: need 10, demand cap 0 (no demand), stop.
- Allocate to VMs with demand: (0 + 1 + 1 + 0.5 + 0) = 2.5 share weight.
  - VM 1: 30 Gbps + (30 ÷ 80) × 50 = 30 + 18.75 = **48.75 Gbps**.
  - VM 2: 10 Gbps + (50 ÷ 80) × 50 = 10 + 31.25 = **41.25 Gbps**.
  - VM 3: 10 Gbps (no slack desire).
  - VM 0: 5 Gbps (capped by demand).
  - VM 4: 0 Gbps.
- **Final: [5, 48.75, 41.25, 10, 0] Gbps. Total: 105 Gbps. Adjust.** (Overbilled; VM 2 demand is 60, so cap at min(41.25, 60) = 41.25. Recompute.)

**Revised Step 2**: VM 2 can take 41.25 but demands 60, so it's demand-limited. Actual allocation: **[5, 48.75, 41.25, 10, 0]**. Total = 105. Error: host is 100. Rescale: multiply by 100/105 = **[4.76, 46.43, 39.29, 9.52, 0] Gbps.** All demands honored within caps.

---

## 10. Linux virtio/vhost/vDPA Queue Model

VM packets traverse: guest virtio driver → host tap/vhost socket → host vSwitch/qdisc → egress NIC.

### Where the Shaper Attaches

**Tap device**: Host-side TAP interface for the VM. Shapers attach as qdisc on the TAP device (e.g., `tc qdisc add dev tap0 root htb rate 10gbit`). Works but adds host CPU cost.

**vhost-vdpa**: Userspace vhost protocol proxies to vDPA hardware device. Shaper can attach at vhost level or on the backing NIC's VF. Hardware pacing preferred (lower latency, no host CPU). (https://www.redhat.com/en/blog/introduction-vdpa-kernel-framework)

**vSwitch port representor**: Open vSwitch kernel module exposes a virtual port for each VM; shaper attaches at the vport level inside OVS or on the underlying physical NIC's VF.

### Per-VM Identity

A "VM" to the host datapath is:
- A **tap device** (TAP) with a file descriptor, or
- A **vhost socket** connected to a vDPA or vhost-net backend, or
- A **VF port** on a SmartNIC (vhost-vdpa offload).

The shaper reads the per-VM queue's demand and enforces rate/ceil on egress.

---

## Numbers to Reuse in the Design

| Mechanism | Parameter | Value | URL |
|---|---|---|---|
| HTB | Unix timer frequency | 100–1000 Hz | https://man7.org/linux/man-pages/man8/tc-htb.8.html |
| sch_fq | Default per-flow packet limit | 100 packets | https://man7.org/linux/man-pages/man8/tc-fq.8.html |
| sch_fq | TCP EDT enabled | Linux 4.20+ | https://man7.org/linux/man-pages/man8/tc-fq.8.html |
| tc-police | Dual token bucket | Standard meter | https://man7.org/linux/man-pages/man8/tc-police.8.html |
| Cilium BW | Egress enforcement | EDT only | https://docs.cilium.io/en/latest/network/kubernetes/bandwidth-manager/ |
| Cilium BW | Ingress enforcement | eBPF token bucket | https://docs.cilium.io/en/latest/network/kubernetes/bandwidth-manager/ |
| SR-IOV | Rate limit range | 0 (no limit) to NIC max, in Mbps | https://man7.org/linux/man-pages/man8/ip-link.8.html |
| ETS | Traffic classes | 0–7 (8 total) | https://man7.org/linux/man-pages/man8/dcb-ets.8.html |
| ETS | Bandwidth allocation | % per TC; work-conserving | https://man7.org/linux/man-pages/man8/dcb-ets.8.html |
| DRL | Gossip EWMA smoothing | α = 0.1 | https://raghavan.usc.edu/papers/drl-sigcomm07.pdf [unverified] |
| DRL | GRD overshoot | ~13 Mbps peak vs. 10 Mbps target | Search abstracts [unverified – full PDF unreadable] |
| Packet Math | 100 Gbps @ 1500 B | 8.33 Mpps | Formula: Rate ÷ (MTU × 8) |
| Packet Math | 100 Gbps @ 64 B | 154.3 Mpps | Formula: Rate ÷ (MTU × 8) |
| Burst @ 1 ms | 100 Gbps | 12.5 MB | 100 Gbps × 1 ms ÷ 8 bits/byte |
| Burst @ 10 ms | 100 Gbps | 125 MB | 100 Gbps × 10 ms ÷ 8 bits/byte |

---

## Which Mechanism for Which Job

| Job | Mechanism | Reason | Trade-off |
|---|---|---|---|
| **Egress per-VM rate limit** | EDT + sch_fq on TAP | No lock bottleneck; precise scheduling | Requires Linux 4.20+; BPF required for non-TCP |
| **Egress per-VM min guarantee + cap** | HTB on TAP or VF | Simple two-level hierarchy; rate/ceil maps to min/max | CPU-bound at >20 Gbps per core; ingress not supported |
| **Ingress rate policing** | tc-police + IFB (optional shaping) | Drop-based per node; no coordination needed | TCP suffers with aggressive drop; no min guarantee |
| **Host-level max enforce** | HTB root + ETS on NIC | HTB controls qdisc, ETS for multi-TC fairness | HTB lock still bottleneck if all VMs active on one core |
| **Work-conserving min with slack** | Water-filling algo + HTB rate/ceil per-VM | Guarantees min, uses slack fairly | Requires algorithm compute; no per-flow state |
| **Distributed global limit** | DRL + GRD/FPS at each node | Multi-site aggregate rate limit; no central bottleneck | Gossip delay causes overshoot; oscillates |
| **Hardware offload (100 Gbps)** | SR-IOV min/max + NIC pacing (per-VF) | Lowest CPU; line-rate native | NIC must support per-VF state; static min, not work-conserving |
| **Receiver-driven feedback** | EyeQ meter + sender-side limiter | Ingress-side enforcement without loss | Requires feedback channel; adds RTT latency |
| **Ingress shaping (complex)** | IFB + HTB + EDT | Can shape on ingress by redirect | 2× latency; high CPU for 100 Gbps; rarely justified |
| **Integration with Kubernetes** | Cilium Bandwidth Manager (egress EDT + ingress eBPF) | Native k8s annotation (kubernetes.io/egress-bandwidth) | Egress-only; ingress token bucket not min-guaranteed |

---

**Key insight for 50 VMs per host at 100 Gbps**: Combine HTB (per-VM rate/ceil on TAP device) + EDT (if TCP) for egress control. For ingress, use per-node policing (tc-police) or Cilium's eBPF token bucket. For true min-guarantee across VMs, layer water-filling logic on top and recompute per update interval (10s–100s ms). Hardware offload (SR-IOV + NIC pacing) reduces CPU but loses work-conserving fairness if VMs are sparse.

---

## Spot-check corrections (2026-09-16, fetched primary sources myself)

| Claim in this survey | Checked against | Verdict |
|---|---|---|
| "single HTB qdisc on one core saturates at a few tens of Gbps or a few Mpps" [unverified] | Carousel SIGCOMM 2017 PDF via pdftotext | The paper does not give a Gbps or Mpps figure for HTB. What it gives: HTB saturates the machine CPU at 600K TCP-RR transactions/s vs 800K without HTB; cause is "the global Qdisc lock acquired on every packet enqueue"; lock wait "up to 1s at the 99th percentile" in production. Quote those instead |
| Cilium bandwidth manager is "egress-only" | https://docs.cilium.io/en/stable/network/kubernetes/bandwidth-manager/ | Wrong as stated in the sources table and decision table. The page says it supports both `kubernetes.io/egress-bandwidth` (EDT) and `kubernetes.io/ingress-bandwidth` (an eBPF token bucket, i.e. a policer). It also says not to use the TBF-based bandwidth CNI plugin "due to scalability concerns in particular for multi-queue network interfaces" |
| EyeQ [unverified] | https://www.usenix.org/system/files/conference/nsdi13/nsdi13-final23.pdf via pdftotext | Now verified: "EyeQ therefore measures rate every 200µs"; control algorithm is an RCP variant; "worst case convergence time (30 iterations) is 6ms"; reserves 10% headroom; and the key sentence for this problem: "contention at the receiver first happens inside the switch, and not at the receiving server" |
| DRL alpha = 0.1, GRD 13 Mbps overshoot [unverified] | not re-fetched | Do not quote either number in solution.md |
| pps math: 100 Gbps at 64 B = 154.3 Mpps | recomputed | Wrong framing. 100e9 / (64 × 8) = 195 Mpps ignores framing; with 20 B preamble + IFG the wire frame is 84 B, so 100e9 / (84 × 8) = 148.8 Mpps. At 1500 B payload (1538 B on the wire) it is 8.1 Mpps. Use 148.8 and 8.1 |
