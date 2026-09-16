# Edge cases: VM network QoS

Every entry answerable in under 60 seconds out loud. Categories: failure, consistency, scale, data, operations, security. Design reference: [`solution.md`](solution.md).

---

## Failure

## Edge case: host QoS agent crashes
- **Trigger:** OOM, bad deploy, host management network blip.
- **Symptom:** proxies get no `Leases` for 500 ms; on-call sees the host's `(proxy, VM)` pairs move to GRACE then FLOOR.
- **Answer:**
  - Proxies keep the last lease for one grace TTL (500 ms), then drop every VM of that host to the floor `Y_in / 8`. Sum of floors <= `X_in × 0.9`, so the NIC is safe and every VM still has its minimum.
  - Egress rates on the datapath freeze at the last value, each >= `Y_out`. No packet path touches the agent.
  - Agent restarts with `epoch + 1`, ignores reports carrying the old epoch's leases, and re-issues leases on the first report. Bursting resumes within 1.1 s of the crash.
  - Blast radius: one host loses bursting for about 1 s. Nothing else.
- **Diagram:** Flow 5 in `solution.md` §6.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: one off-host proxy dies
- **Trigger:** hardware, kernel panic, deploy.
- **Symptom:** BFD to the edge router fails within 300 ms; the proxy's BGP route is withdrawn; 1/8 of the group's flows re-hash.
- **Answer:**
  - The 7 surviving proxies receive the moved flows with no lease covering the extra demand, so they admit the moved VMs at floor for at most one interval, then get leases at the next `Report`.
  - Packets already queued in the dead proxy (microseconds) are lost; TCP retransmits.
  - With resilient (consistent) hashing on the router only the dead proxy's flows move; without it all flows re-hash and every VM on every host in the group sees one interval at floor. Ask the network team which one the edge does.
  - New proxy boots empty, pulls the `ip -> vm` map and floors from the controller (or its local cache), announces its route, and starts at floor.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: regional controller or policy store is down
- **Trigger:** DB failover, controller leader election stuck.
- **Symptom:** `POST /vms` and `PATCH qos` fail; no packet-path metric changes.
- **Answer:**
  - The hot loop (proxies, agents) never talks to the controller. Leases keep cycling.
  - No new VMs, no resizes, no `ip -> vm` map changes for the outage. Existing VMs are unaffected.
  - A host or proxy that restarts during the outage uses its on-disk cache of VM rows and floors, so even restarts are safe.
  - RTO for the controller is 30 s (3 replicas, leader election); the policy store follows the DB runbook.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: partition between proxies and the host's management network
- **Trigger:** management VLAN outage while the data VLAN is fine.
- **Symptom:** identical to "agent crashed" from the proxy's view; the agent sees no reports and its own view goes stale.
- **Answer:**
  - Proxies fall to floor after grace. The agent, seeing no reports, sets egress rates from local demand only and leaves ingress policers at `Y_in × 1.2` (it cannot know the leases died, so it must assume they did).
  - Both sides converge on "floor" independently. No coordination is needed to be safe, which is the point of a floor.
  - Heals automatically: first report after the partition carries the current epoch and leases resume.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: UDP flood to one VM
- **Trigger:** 40 Gbps of UDP toward VM1's public IP on a host with `X_in` = 50 Gbps.
- **Symptom:** VM1's `dropped_bytes` at the proxies goes vertical; NIC utilisation stays under `X_in × 0.9`; VM2 to VM45 see nothing.
- **Answer:**
  - Proxies admit VM1 at its lease (or floor) and drop the rest before the NIC. The switch in front of the host never sees more than the sum of leases.
  - If the other VMs are idle, the next interval leases VM1 up to 44 Gbps and the flood is delivered (and billed). If they are busy, VM1 is cut to its fair share. Either way nobody drops below `Y`.
  - The one thing that would break this is traffic that does not pass a proxy (spoofed encapsulation, or DC-internal traffic). The host ACL drops encapsulated packets not from proxy IPs, and the backstop policer catches a misbehaving proxy.
  - Upstream DDoS scrubbing is a separate system; ours only has to make the flood a VM1-only problem.
- **Diagram:** `solution.md` §10.4.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Consistency

## Edge case: two placements race for the last slot on a host
- **Trigger:** two `POST /vms` land on the same candidate host with 1 Gbps of ingress headroom left.
- **Symptom:** none visible if handled; oversubscription if not.
- **Answer:**
  - Admission is a conditional update on the host row: `UPDATE host SET committed_in += 1G WHERE committed_in + 1G <= 45G`. One of the two updates matches 0 rows and the controller retries on the next candidate.
  - No distributed lock, no read-then-write. The invariant `sum(Y) <= X × 0.9` is a database constraint in effect.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: stale lease from a previous agent epoch
- **Trigger:** agent restarted while a proxy still holds a lease from the old process (a zombie that took 3 s to die and kept answering).
- **Symptom:** a proxy could keep bursting on an allocation the new agent does not know about.
- **Answer:**
  - Every lease carries the agent epoch. The new agent's first `Leases` response has a higher epoch; the proxy replaces all leases for that host wholesale and drops any VM not in the new set to floor.
  - The zombie's replies carry the old epoch and are ignored by the proxy once it has seen a newer one.
  - Sum of the new leases is again bounded by `X_in × 0.9`, so the overlap window is at most one interval and inside headroom.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: resize Y upward on a full host
- **Trigger:** `PATCH /vms/v1/qos {y_in: 5G}` where the host has 0.5 Gbps of committed headroom.
- **Symptom:** caller gets `409` with the host's remaining capacity.
- **Answer:**
  - Admission runs on the delta. It fails, and nothing changes for the VM: it keeps its old `Y`. There is no moment where the VM is "unprotected", because the old class stays programmed until the new one replaces it.
  - The controller offers live migration to a host with room. The target host's row is committed before the migration starts (so the capacity is reserved), the source is released only after the VM is cut over.
  - Resize downward always succeeds and takes effect within 1 s; the VM's bursts may continue for one interval on the old leases.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: ECMP puts all of a VM's ingress on one proxy
- **Trigger:** VM1 has one client with three long-lived flows; all hash to proxy 3.
- **Symptom:** in the static-split design, VM1 gets 125 Mbps instead of 1 Gbps. In the lease design, no symptom.
- **Answer:**
  - Leases are split across proxies by each proxy's reported `wanted`. Proxy 3 reports all the demand, so it gets the whole allocation. Proxies 1, 2, 4 to 8 get a lease of zero above floor.
  - First interval after the flows start, proxy 3 admits only its floor share (125 Mbps). That is the one place the static floor is unfair: the guarantee holds at the host level (sum of floors) but is under-delivered for 100 ms if all demand is on one proxy. Acceptable under the 99.9% of 1 s windows SLO; if not, set the per-proxy floor to `Y_in` (not `Y_in / 8`) and let headroom absorb it. Say the trade.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Scale

## Edge case: one elephant flow of 40 Gbps to one VM
- **Trigger:** a single 5-tuple at 40 Gbps (a backup restore from one peer).
- **Symptom:** lands on one proxy; that proxy's single NIC queue caps around 10 Gbps; the customer sees 10, not 40.
- **Answer:**
  - `per_flow_ceil` = 10 Gbps is a published limit, same as every public cloud (AWS 5 Gbps single flow outside a placement group, GCP 3 Gbps per flow to outside the VPC).
  - The fix for the customer is multiple flows (MPTCP, parallel connections), which ECMP spreads over the 8 proxies.
  - Inside our system the flow-table LRU on the proxy catches it before it hurts anything.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: 64 B packet storm from a neighbour
- **Trigger:** VM3 sends 10 Gbps of 64 B UDP: 14.9 Mpps.
- **Symptom:** in a bytes-only design, host datapath CPU pins at 100%, every VM's throughput and latency degrade while VM3 is "within its ceiling".
- **Answer:**
  - Second bucket in packets: `pps_ceil` = 2 Mpps per VM, enforced by the same EDT stamp. VM3 is paced to 2 Mpps regardless of bytes.
  - Datapath CPU is charged per VM (per-VM queue pairs on the SmartNIC, or per-VM cgroups for vhost threads) so the storm burns VM3's own budget.
  - The same bucket runs on the proxies for ingress storms.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: 10x more hosts tomorrow
- **Trigger:** region grows from 10k to 100k hosts.
- **Symptom:** none on the hot loop; the loop is per host.
- **Answer:**
  - Control traffic scales linearly with hosts (7 Gbps to 70 Gbps per region, still 0.0014% of data traffic). Proxies scale with edge bandwidth, not hosts: add proxy groups.
  - The controller's write rate (create / resize / delete) grows 10x; shard by host id range. It is still not on any packet path.
  - The metering topic grows to 50 M msgs/s at 40 B = 2 GB/s; 200 partitions. Fine.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Data

## Edge case: `ip -> vm` map is wrong on a proxy
- **Trigger:** a stale or corrupted push maps VM1's IP to host B, where VM1 does not live.
- **Symptom:** host B drops encapsulated packets for an unknown `vm_id` and counts `no_such_vm`; VM1's inbound is dead through that proxy.
- **Answer:**
  - Fail closed by design: host B never delivers to the wrong VM. The `no_such_vm` counter is a paging alert.
  - Map pushes are versioned; a proxy that sees a version gap pulls the full map. The controller can re-push one entry.
  - VM1 keeps 7/8 of its inbound through the other proxies in the meantime.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: metering pipeline lags or loses samples
- **Trigger:** Kafka partition leader failover, consumer stuck.
- **Symptom:** billing dashboard is minutes behind; no packet-path effect.
- **Answer:**
  - Agents buffer up to 1 h of samples locally and resend; samples are keyed `(vm, dir, ts_1s)` and upserted, so replays never double bill.
  - If a host's buffer overflows, billing reconciles from the proxies' own forwarded-bytes counters (they count the same bytes, minus host-side policer drops, which are rare). The two sources are compared daily; a gap above 1% is a ticket.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Operations

## Edge case: what pages at 3am
- **Trigger:** any.
- **Symptom:** the alert itself.
- **Answer:**
  - Page: any host NIC above 95% of `X` in either direction for 10 s. The guarantee is at risk; usual cause is non-proxied traffic or a policer bypass.
  - Page: FLOOR-state `(proxy, VM)` pairs above 1% of a proxy group for 60 s. Agents unreachable or a partition.
  - Page: any VM with `received < min(wanted, Y) × 0.9` for 3 consecutive seconds. That is the SLO itself.
  - Ticket: lease loop p99 above 300 ms; `no_such_vm` drops above zero; metering lag above 10 min.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: rolling out a bad allocator build
- **Trigger:** new agent version computes leases that sum above `X_in`.
- **Symptom:** canary hosts' NIC utilisation alert fires within 10 s.
- **Answer:**
  - Canary is one proxy group (160 hosts) in shadow mode for 24 h: leases computed and logged, not applied. A sum above `X_in × 0.9` is caught in logs before any packet is affected.
  - If it slips through to live: controller flips `leases_enabled = false` for the group; proxies ignore leases and run at floor within 1 s. Roll the agent back host by host.
  - The datapath binary is rolled separately (qdisc or XDP program swap), so a bad allocator never requires a datapath rollback.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: migrating from the old static-cap system
- **Trigger:** the fleet runs plain per-VM caps at `Y` today, no bursting.
- **Symptom:** none; this is the plan.
- **Answer:**
  - Phase 1: deploy agents and proxies with `leases_enabled = false`. Everything behaves exactly like today (floor = old cap). Compare shadow leases with actual demand for a week.
  - Phase 2: enable leases per proxy group. Rollback is the flag, which returns the group to today's behaviour within 1 s.
  - Phase 3: move egress from HTB to EDT host by host. Rollback is a qdisc swap.
  - Customers see only "bursting started working". No downtime at any phase.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Security and abuse

## Edge case: a tenant spoofs the encapsulation header
- **Trigger:** a VM on host A crafts a Geneve packet with `vm_id = vm7` and sends it to host B.
- **Symptom:** none if handled.
- **Answer:**
  - Host B's NIC ACL accepts encapsulated packets only from proxy source IPs; VM-originated packets from host A arrive with A's address and are dropped and counted.
  - Even if the ACL were bypassed, the host checks `vm_id` against its own VM list and the ingress policer for `vm7` still applies, so the worst case is filling `vm7`'s own allocation.
  - `Report` and `Leases` run over mTLS on the management network; a forged lease is the one message that could oversubscribe a NIC, so leases are signed by the agent's epoch key.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: a tenant tries to buy their way past `sum(Y) <= X`
- **Trigger:** `PATCH qos` with a huge `Y` from a privileged API key.
- **Symptom:** `409`.
- **Answer:**
  - There is no override path. Admission is the invariant, and an operator who wants a bigger `Y` has to migrate the VM to a host with room or reduce packing.
  - The one legitimate knob is headroom (10%), and lowering it region-wide is a change-managed config, not an API.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident
