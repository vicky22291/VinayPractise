# My attempt (whiteboard, 2026-09-16) and critique

Transcribed from the screenshot of the interview canvas. Timing unknown. Critique follows the Staff bar in the root `CLAUDE.md` §7.

## What I wrote

**Functional requirements**
1. Guaranteed QoS with minimum guarantee.
2. Differentiated requests for ingress and egress.
3. For the extra bandwidth they need to pay.

**Scale:** 50 VMs per host, 50k hosts.

**Non-functional requirements**
1. Decision-making latency should be almost real time, "< 0 ms".
2. System should be fault tolerant.
3. Availability 99.99%.

**Core entities:** VMs, hosts, network bandwidth.

**Major points to discuss:** how do we solve noisy neighbor; how do we guarantee the QoS.

**Side notes:** "Statistical - 99.9". "Gossip, VM1, last write wins". "Heart beat: health information, usage information, QPS p99".

**Diagram (bottom of canvas):**
- Host box with VM1 (T1), VM2 (T2), and an On Host Proxy. `eBPF` on the arrow from the proxy.
- `Collector` receives `source, direction, packets, time (ms)` per request from the proxy.
- `Collector` feeds an `Analyser` and an `Evaluator (Throttles)`.
- `Evaluator` has an `In Memory` store with `atomic counters`, a `list of request -> packet [size, ms]`, a `rolling window`, `bandwidth - direction`, and `host bandwidth`.
- Decision logic written at the left:
  - "10 per VM (1 GB), host bandwidth (20 GB). After the VM coming, host bandwidth 10 GB."
  - "1. Current bandwidth < request bandwidth: the request allowed."
  - "2. Current bandwidth > request bandwidth: host bandwidth - packet size < 0 then reject, else pass."
- An arrow from `In Memory` back around to the top of the host box labelled `host bandwidth`.

## Critique against the Staff bar

| # | Criterion | Verdict | What was missing |
|---|---|---|---|
| 1 | Simplest design that meets the requirement, says what it refused to build | Missed | The sketch builds a Collector, Analyser, and Evaluator pipeline for a decision that is a token bucket lookup. Nothing was named as out of scope. The simplest correct egress answer is one sentence: per-VM shaper with `rate = Y, ceil = X`, and placement keeps `sum Y <= X` |
| 2 | Failure modes and blast radius | Missed | "Fault tolerant" and "99.99%" were written as requirements but no component was walked through failing. What happens to the throttle decision when the Evaluator's in-memory state is lost was not asked |
| 3 | Migration | Missed | Not mentioned. Acceptable to skip in 45 minutes, but say so |
| 4 | Operability | Missed | "Heartbeat, usage information, QPS p99" is the seed of it, but no metric, threshold, or SLO was named |
| 5 | Cost and team boundaries | Missed | Not mentioned |
| 6 | Explicit trade-off | Missed | "Statistical 99.9" is the right instinct and was never explained: statistical because of what, and what would it cost to make it hard |

## The three technical gaps, in order of how much they cost

**1. Ingress and egress were treated as the same problem.** FR2 says "differentiated requests for ingress and egress" but the diagram has one on-host proxy deciding both. The host cannot decide ingress: by the time the packet is at the host, the NIC's capacity is spent, and the switch in front of it has already dropped other VMs' packets. The hint diagram in the prompt drew off-host proxies for incoming traffic for exactly this reason, and the sketch did not use them. This is the gap the interviewer was waiting on. Answer in [`solution.md`](solution.md) §4.2 and §5.2.

**2. The decision logic does not implement a minimum guarantee.** The written rule is "if current bandwidth < requested, allow; else if host bandwidth minus packet < 0, reject". That is a host-level cap with first-come-first-served under it. VM1 sending at 20 GB fills the host and VM2's 1 GB minimum is rejected by rule 2. A guarantee needs two rates per VM (`rate = Y` that is always available, `ceil = X` that borrows), and it needs `sum(Y) <= X` enforced at placement, which was never stated. The "10 per VM, host 20, after the VM host 10" note is halfway to the placement invariant; finish the thought: the guarantee is made when the VM is placed, the shaper only realises it.

**3. Gossip with last-write-wins is the wrong tool for a budget.** Gossip converges in `log N` rounds and gives no invariant that the sum of what everyone admits stays under `X`. LWW throws away the information you need (how much each proxy saw). The host already knows its own NIC and its own VMs; it is the natural allocator and needs no agreement protocol. Reports up, leases down, floor when the loop is broken. See §5.2 and [`../../concepts/gossip-protocol.md`](../../concepts/gossip-protocol.md).

## What was right

- "Statistical 99.9" is the correct shape of the guarantee, and a good instinct to write before being asked.
- Per-request `source, direction, packets, time` is the right telemetry; it just belongs in per-core counters on the datapath, not in a Collector service.
- `eBPF` and `atomic counters` are the right words for the host datapath.
- Noisy neighbor as the first discussion point is right. The follow-up to have ready: bytes are not the only shared resource (packets per second and CPU are, §5.5).

## Follow-ups I should have asked the interviewer

1. Is "QPS" bytes or packets? Both directions have different X; is Y also different per direction?
2. Is `sum(Y)` on a host allowed to exceed `X` (oversubscription), or may I make placement enforce it?
3. Is the off-host proxy tier already there (it is in the diagram), and do I own it?
4. Internet traffic only, or also VM-to-VM inside the datacenter?
5. What is the acceptable time for a burst to be served after it starts: milliseconds or seconds?
