# VM network QoS: minimum bandwidth per VM on a shared host NIC

> One-line answer: make the guarantee a placement invariant (a VM lands on a host only if the sum of every VM's minimum fits under the NIC capacity in both directions), enforce egress on the host with a work-conserving hierarchical shaper (per-VM rate = Y, ceil = X), and enforce ingress *before* the host, at the off-host proxy tier, where each proxy runs a per-VM token bucket whose rate is a lease handed out every 100 ms by the destination host's QoS agent; the host itself only polices ingress as a backstop, and when the agent is unreachable every proxy falls back to the static floor Y so the minimum survives any control-plane outage.

Tier 1, problem #7b in [`hld/README.md`](../README.md). Reported at Databricks as "QoS for VMs on a host" (screenshot dated 2026-09-16, interviewer Flavio Cruz). The hint diagram shows an on-host proxy for outgoing traffic and a set of off-host proxies feeding incoming traffic to each VM. Sibling of [`network-throttling/`](../network-throttling/) (fleet-wide API limits); this one is about bytes on a physical NIC, and the hard half is ingress. See [`research/`](research/).

## Problem statement (as asked)

We are a cloud provider. Each server that runs VMs has a single network interface (the host interface) capable of X QPS incoming and X QPS outgoing; the two capacities differ. Traffic beyond that is throttled by the NIC. Each VM on the host must get at least Y QPS (Y < X) in each direction for Internet traffic. VMs can use more when it is available (that is how we make money). Design a system so that VMs on the same host are guaranteed their minimum in both directions while the maximum can go up to the host capacity.

"QPS" here is read as bandwidth (bytes per second) with packets per second as a second limit on the same bucket. Say that out loud in the interview.

## Functional requirements

Core:
- Egress: a VM with demand always gets at least `Y_out`; idle capacity on the host is shared among VMs that want it, up to `X_out`.
- Ingress: the same for `Y_in` and `X_in`, for traffic arriving from the Internet.
- Guarantees survive change: VMs are created, deleted, resized (new Y), and hosts fill up. The guarantee must hold at every moment, not just at steady state.
- Metering: per-VM usage per direction, good enough to bill for bandwidth above `Y`.

Below the line (say it out loud):
- VM-to-VM traffic inside the datacenter. It takes a different path (no off-host proxy) and is a follow-up mutation.
- DDoS scrubbing. A volumetric attack is absorbed upstream of the proxies; our job is that it cannot hurt the other 49 VMs on the host.
- Latency guarantees (Silo style). Bandwidth only.
- Per-flow congestion control. TCP does that; we shape aggregates.

## Non-functional requirements

| Dimension | Target |
|---|---|
| Scale | 50 VMs per host, 50k hosts (2.5 M VMs). Host NIC 100 Gbps out, 50 Gbps in from the Internet path. `Y_out` = 2 Gbps, `Y_in` = 1 Gbps at full packing |
| Decision latency | Per packet, on the data path, no remote call. Budget about 100 ns per packet at 8.3 Mpps (100 Gbps of 1500 B packets) |
| Guarantee | In 99.9% of 1 s windows a VM with demand >= Y receives >= Y. Convergence after a demand change <= 200 ms |
| Availability | Data path 99.99%. Control plane (host agent, proxies' lease loop, regional controller) may fail without any VM dropping below Y |
| Consistency | Policy (Y per VM, placement) strongly consistent. Allocations eventual, refreshed every 100 ms. Metering eventual, 1 s granularity |
| Overshoot | A VM may exceed its allocation by at most one control interval of demand; the host NIC is never oversubscribed by proxied traffic by more than 10% headroom |
| Fairness | Spare capacity split weighted max-min by demand; a VM never below Y while it has demand |

## What interviewers probe (the ladder)

1. Egress is easy: the host owns the packets. Why is ingress hard? What happens if you only police ingress on the host?
2. Where is the guarantee actually made? (Placement. If the sum of Y exceeds X, no enforcement can save you.)
3. VM1 gets 40 Gbps of inbound UDP. Show, second by second, what VM2 sees and when it gets its Y back.
4. The proxy tier has 500 nodes and VM1's traffic arrives through 8 of them. How does each proxy know what it may forward?
5. The host QoS agent crashes. Do the proxies fail open or fail closed? Is the answer the same for the host cap and the per-VM min?
6. Work conserving: 49 VMs idle, VM1 wants 100 Gbps. Does it get 100, and how long after it starts sending?
7. "QPS" for a NIC: bytes or packets? A neighbor sends 64 B packets at line rate. What breaks, and which bucket catches it?
8. HTB vs EDT vs SmartNIC: what do you run on the host at 100 Gbps and why does HTB stop scaling?
9. Now the traffic is VM-to-VM inside the datacenter. What changes?
10. How do you test that the guarantee holds, and what pages at 3am?

## Files

| File | What it is |
|---|---|
| [`solution.md`](solution.md) | Full HLD in flow-first form: one incremental diagram, one walkthrough per FR, deep dives that mutate the design, then nitty-gritty |
| [`diagrams.md`](diagrams.md) | The D1 to D12 diagram set |
| [`edge-cases.md`](edge-cases.md) | Every "what if" with a 60-second answer and a confidence box |
| [`my-attempt.md`](my-attempt.md) | Transcription of my whiteboard notes from the screenshot and the Staff-bar critique |
| [`deep-dives/egress-shaping-htb-and-edt.md`](deep-dives/egress-shaping-htb-and-edt.md) | HTB rate / ceil / borrowing, why the qdisc lock caps out, EDT pacing with fq, SmartNIC offload |
| [`deep-dives/ingress-guarantee-and-off-host-proxies.md`](deep-dives/ingress-guarantee-and-off-host-proxies.md) | Why ingress cannot be enforced on the receiver, the proxy tier, host-as-allocator leases, the backstop policer |
| [`deep-dives/allocation-loop-and-fairness.md`](deep-dives/allocation-loop-and-fairness.md) | The 100 ms loop, weighted max-min with a floor, worked example, overshoot bound |
| [`deep-dives/placement-and-admission-control.md`](deep-dives/placement-and-admission-control.md) | The guarantee as a placement invariant, headroom, resize, migration |
| [`deep-dives/failure-modes-and-fail-policy.md`](deep-dives/failure-modes-and-fail-policy.md) | Agent, proxy, controller, and partition failures; fall to floor, never fail open on the host cap |
| [`research/`](research/) | Raw web research notes with source links. Input to the files above, not study material |
| `vm-network-qos.excalidraw` | My drawing. Missing until I draw it |
