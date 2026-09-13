# Edge cases: datacenter network throttling / hierarchical rate limiting

Every entry must be answerable out loud in under 60 seconds. Mark confidence after each study pass. Categories per `hld/CLAUDE.md` §5: failure, consistency, scale, data, operations, security.

Design recap for context: enforcers hold local token buckets per key and decide with no remote call; every 100 ms they report `[key, hits, rejected, wanted]` to the allocator shard that owns the key's tree; the allocator runs a global bucket with deficit per key, water-fills the tree, and returns per-enforcer leases with `share`, `reject_fraction`, `reject_for_ms`, `policy_version`, `epoch`. Ownership is explicit in etcd with epochs. Allocator state is soft. On control loss: last lease, then grace at last share (10 s), then per-RLG safe policy. Details in [`solution.md`](solution.md).

---

## 1. Failure

## Edge case: allocator node dies while owning the biggest tenant's shard
- **Trigger:** kernel panic, OOM, or a deploy gone wrong on one of 20 allocator nodes.
- **Symptom:** enforcers' reports to that node time out. `lease_age_p99` climbs. Nothing visible to tenants.
- **Answer:**
  - Enforcers keep using the last lease until `ttl` (1 s), then enter grace at the last share for up to 10 s, retrying with backoff.
  - etcd expires the node's lease at 5 s; the rebalancer assigns its shards with `epoch + 1`; enforcers refresh the shard map and report to the new owner within ~300 ms.
  - The new owner has no state. For two intervals it echoes each enforcer's reported share (learning mode) and rebuilds the demand map, then computes normally.
  - Lost: the deficit the dead node had recorded, worth at most one interval of overshoot. Inside the 5% budget. Nothing durable to restore.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: etcd is unavailable for two minutes
- **Trigger:** etcd quorum loss, or a network partition between allocators and etcd.
- **Symptom:** owners cannot renew shard leases; `shard_without_owner` climbs after 5 s.
- **Answer:**
  - Each owner tracks its own lease expiry on a monotonic clock. Until then it serves normally. At expiry it stops answering for those shards, because it cannot know whether someone else was granted them.
  - Enforcers ride the last lease, then grace, then the per-RLG safe policy at ~15 s. `enforcers_on_safe_policy > 1%` pages.
  - Traffic never stops. Enforcement degrades to safe policies, which by default cap each enforcer at the full limit (fleet may briefly exceed).
  - Operator option: a "freeze ownership" switch that lets current owners continue without a lease during a known etcd incident. It is a human decision because it trades a guaranteed single owner for enforcement.
  - When etcd returns: one rebalance, learning mode, normal in ~2 s.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: network partition between a group of enforcers and every allocator
- **Trigger:** a zone's network isolates 700 gateways from the allocator tier but not from clients.
- **Symptom:** those 700 enforcers see report timeouts; the allocator sees 35% of enforcers vanish from demand maps.
- **Answer:**
  - Partitioned enforcers: lease, grace (10 s), then safe policy. For `local_cap(rate)` RLGs, each of the 700 can admit up to the full rate, so the fleet may admit up to 700x for that key in the worst case. That is why fleet-protection RLGs use `local_cap(rate / expected_enforcers × 4)` and external-quota RLGs use `static_split`.
  - The allocator side: after `demand_ttl` (10 s) those enforcers drop out of the demand maps, and the remaining 1,300 enforcers get the whole share. When the partition heals, the returning enforcers get bootstrap allowances, report, and get shares one interval later. Brief over-allocation of at most one interval.
  - Say it: a partition is the one case where the limit is not enforceable fleet-wide, and the safe policy decides which way we err.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: enforcer pod crashes mid-interval
- **Trigger:** OOM, deploy, node drain.
- **Symptom:** its in-flight requests fail; the load balancer moves its traffic.
- **Answer:**
  - Its counters for the last < 100 ms are lost, which under-counts one interval. Self-correcting: reports are deltas, the next interval from other pods is exact.
  - Its share stays in the allocator's demand map for `demand_ttl` (10 s), so the key is briefly under-allocated by that pod's share. The pods that inherit its traffic see more `wanted` and get a bigger share next interval; between, their local caps (`2 × share`) and bootstrap absorb the shift.
  - Nothing to recover on restart. The new pod starts with bootstrap buckets.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: policy store is down
- **Trigger:** the DB or etcd namespace behind `PutPolicy` is unavailable.
- **Symptom:** `PutPolicy` fails; `policy_version` stops advancing.
- **Answer:**
  - Allocators keep the last policy in memory and keep issuing leases. No effect on traffic.
  - A new allocator starting during the outage cannot load policy; it must not take ownership of shards. It stays out of the rebalancer's candidate set until it has a policy snapshot (cached on local disk from the last watch, with a version stamp, as a fallback).
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: the allocator returns but with a stale deficit
- **Trigger:** allocator node was paused (GC, VM live-migration) for 20 s and then resumes with buckets that think 20 s of deficit accrued.
- **Symptom:** a lease with `reject_for_ms = 20,000` would black-hole a tenant.
- **Answer:**
  - A paused node lost its etcd lease, so its epoch is stale and its leases are ignored by enforcers. That alone stops it.
  - Belt and braces: `max_deficit = 5 × rate` caps `reject_for_ms` at 5 s in any lease, and a resumed node checks `now - last_tick > 3 × T` and resets its buckets (treats itself as a new owner in learning mode).
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## 2. Consistency

## Edge case: a client sends 10x its limit in the first 100 ms of a window
- **Trigger:** a batch job starts with 10,000 threads against a workspace with `rate = 1,000/s`.
- **Symptom:** the first 100 ms admits up to `min(D, Σ local caps) × T` = `2 L × 0.1 s` = 200 requests against 100 allowed, then a wall of 429s.
- **Answer:**
  - Enforcers admit under the old lease and local caps (`2 × share`) for one interval. The report shows `wanted = 10 L`, `hits = 2 L × T`; the global bucket goes to `-0.1 L`; the lease returns `reject_fraction 0.9, reject_for_ms 100`.
  - The next 100 ms admits nothing (payback), then steady state admits exactly `L` per second via the fraction. The first 1 s window closes at about `L`; the 10 s window is `≤ 1.01 L`. Without the local caps the first interval would admit `D × T` = one second's worth; say that this is why the caps exist.
  - Cold key (no lease anywhere) is the worse case: `N × bootstrap` in the first interval. Bootstrap shrinks with `active_enforcers` so a hot key's bootstrap is a couple of tokens.
  - If the interviewer wants tighter: shorten `T` for keys near their limit (20 ms) and lower bootstrap. Both cost control traffic. The bound is `D × T`; there is no free lunch without a remote call per request.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: two enforcers both admit the "last" token
- **Trigger:** a key with `rate = 1/s`; two enforcers each hold a bootstrap token and both get a request in the same millisecond.
- **Symptom:** two requests admitted for a limit of one.
- **Answer:**
  - Expected. Local decisions cannot exclude each other. The report shows `hits = 2`, the global bucket records a deficit of 1, and the next lease pays it back with `reject_for_ms = 1,000`.
  - Over any window longer than a few intervals the count is exact. Over one interval it can be off by the sum of local caps. Very low limits (< 10/s) should set `bootstrap = 1` and get most of their enforcement from the deficit, or be routed to a single enforcer by consistent hashing at the load balancer if exactness matters (a tenant-level design choice, named as such).
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: report retried after a timeout, original was applied
- **Trigger:** enforcer sends a report, the allocator applies it, the response is lost, the enforcer retries.
- **Symptom:** without dedup, hits counted twice, phantom deficit.
- **Answer:**
  - Reports carry `(enforcer_id, seq)`. The allocator keeps the last applied `seq` per enforcer per shard and answers a replay with the current lease without re-applying.
  - After failover the new owner has no `seq` table; it accepts the first report it sees and starts tracking from there. A replay of a report the old owner applied is double counted once, worth ≤ one interval, already inside the budget.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: lease arrives out of order
- **Trigger:** two in-flight report RPCs; the older response arrives after the newer.
- **Answer:**
  - Leases carry `(epoch, issued_seq)`. The enforcer applies a lease only if it is newer than the one it holds. Older ones are dropped. Same rule fences leases from a deposed owner.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: limit lowered from 1,000 to 100 per second
- **Trigger:** `PutPolicy` on a workspace during an incident.
- **Symptom:** tenant expects to be at 100/s within seconds and not to be punished for the last second at 1,000/s.
- **Answer:**
  - The allocator sees the watch event, sets `tokens = min(tokens, new_burst)`, clears the deficit, bumps `policy_version`. The next leases carry the new rate. Effective in ≤ 200 ms plus watch latency.
  - No phantom deficit: traffic admitted under the old rate is not charged against the new one.
  - The enforcer rejects any lease with a lower `policy_version` than it has for that key, so a slow allocator cannot roll the limit back.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: limit raised, tenant expects an immediate burst
- **Trigger:** `PutPolicy` raises rate from 100 to 1,000/s.
- **Answer:**
  - Tokens are clamped to the new burst but not filled: the bucket refills at the new rate from now. If the product wants "raise means burst now", set `tokens = new_burst` on a raise. It is a one-line policy choice; say which and why (we default to no free burst so a raise cannot be used as a burst button).
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: clocks differ by 200 ms across pods
- **Trigger:** NTP drift, a VM live-migrated with a stale clock.
- **Symptom:** none, if we did it right.
- **Answer:**
  - Every bucket uses a monotonic clock local to its process. Leases carry durations (`ttl_ms`, `reject_for_ms`), never absolute timestamps. The enforcer converts to its own monotonic deadline on receipt.
  - The only wall-clock use is the 1 s rollups for dashboards. A wall-clock jump on a pod cannot change a decision.
  - Contrast with `rejectTilTimestamp` designs: a 200 ms skew shifts every reject window by 200 ms, which at 100 ms intervals is a 2x error.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: hierarchical check admits at the parent, rejects at the child
- **Trigger:** account bucket has tokens, user bucket is empty.
- **Answer:**
  - Check widest first. On a reject at a narrower level, refund the tokens already taken at wider levels so `hits` stays exact. Otherwise the account's count inflates by every user-level reject, which under a noisy user pushes the whole account into deficit.
  - Report `wanted` at every level for the rejected request so the water-fill sees true demand.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## 3. Scale

## Edge case: one account is 30% of all traffic
- **Trigger:** a huge tenant with 100 k users.
- **Symptom:** its owner shard runs at 100% CPU: 1.8 M entries/s and a 100 k-node walk every 100 ms. Its leases go stale; `report_rtt` for that shard climbs.
- **Answer:**
  - Alert at 60% of shard capacity, before it hurts.
  - Turn on `delegate_children` for that account: each workspace subtree moves to its own shard; the root shard hands each a budget lease per interval (its water-filled share of the account cap) and sees only `k` workspace summaries. Fairness across workspaces is one interval staler.
  - Report suppression: keys under 20% of their rate report every 1 s instead of 100 ms. Cuts entries ~5x for a mostly idle tree.
  - Incremental water-fill: re-run only for parents whose demand crossed their rate.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: a limit of 100 req/s across 2,000 enforcers
- **Trigger:** a per-user limit, the common case.
- **Answer:**
  - `L / N = 0.05/s` is unusable; demand-proportional shares fix it. Enforcers with no demand hold nothing; the few that see this user get shares proportional to their `wanted`, with a floor so a trickle keeps a trickle.
  - The first request at a new enforcer is admitted from the bootstrap bucket (`min(burst, rate × T, 4 × rate / active_enforcers)`), so a load balancer reshuffle does not cause a wave of rejections.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: 10x traffic tomorrow (20 M req/s, 20,000 enforcers)
- **Answer:**
  - Enforcers scale linearly with no change. Allocator load scales with enforcers × active keys: 10x reports. 4,096 virtual shards allow up to 200 allocator nodes; raise the suppression threshold so cold keys report at 2 s. The shard map is the seam. Nothing on the request path changes.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: a single request touches 500 keys
- **Trigger:** a bulk API with many descriptors, or a badly designed RLG scheme.
- **Symptom:** before grouping, 500 remote calls per request in the synchronous design (Databricks measured this).
- **Answer:**
  - In our design the check is 500 local bucket reads (50 us), still no remote call. Reports group keys by owner shard into one RPC per shard, so at most ~20 RPCs per interval regardless of key count.
  - Cap descriptors per request at the gateway (say 32) and reject the rest as a policy error; 500 dimensions is a modelling bug, not a scaling target.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: thundering herd when a deficit expires
- **Trigger:** 10,000 clients backing off on the same `Retry-After` and returning at the same instant.
- **Answer:**
  - `Retry-After` is jittered per response by ±20% of `reject_for_ms`. The token bucket at the enforcer absorbs the rest: even if they all return together, only `burst` tokens exist, and the report shows `wanted` so the next lease keeps `reject_fraction` high.
  - Clients are told to use exponential backoff with jitter (documented API behaviour), which is the Stripe recommendation.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## 4. Data

## Edge case: policy tree schema change (a new dimension)
- **Trigger:** product adds `region_of_origin` as a limit dimension.
- **Answer:**
  - Descriptors are opaque strings to enforcers; a new dimension is a new key per request and a new flat tree root in policy. Enforcer library does not change. Allocator gains a root. Reports carry the key hash as before.
  - Roll out with the dimension in shadow mode first.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: replay or backfill of counters
- **Answer:**
  - There is nothing to backfill: counters are soft state worth one interval. Dashboards come from the 1 s rollups in the time series store, which have their own retention. If those are lost, we lose history, not enforcement.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: tenant deletion / GDPR
- **Answer:**
  - Delete the tenant's policy nodes; the allocator drops the keys after `demand_ttl`; enforcers evict idle keys after 10 min; time series rollups keyed by hashed key are dropped by tenant prefix mapping kept in the policy store. No durable per-request data exists in this system.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: 3 years of growth in keys (10 M to 100 M live keys)
- **Answer:**
  - Allocator memory grows to ~12 GB fleet-wide cold state, 600 MB per node at 20 nodes; still fine. Enforcer memory is bounded by keys seen per pod, not by fleet keys. The real growth cost is report entries, which scale with active keys, not live keys; suppression keeps cold keys cheap.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## 5. Operations

## Edge case: what pages at 3 am
- **Answer:**
  - `enforcers_on_safe_policy > 1%` for 1 min (control plane unreachable for a slice of the fleet).
  - `shard_without_owner > 0` for 10 s (etcd or rebalancer problem).
  - `overshoot_1s > 1.2` on any key for 30 s (enforcement broken: a clock bug, a lease bug, a bad enforcer version).
  - `report_rtt_p99 > 200 ms` (allocator overload; at 50 ms a ticket).
  - Not a page: a tenant hitting its limit. That is the system working; it is a dashboard and a product notification.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: rolling out a new enforcer version that has a bug in the bucket math
- **Trigger:** refill computed in ms instead of ns, admitting 1,000x.
- **Answer:**
  - Canary 1% of enforcers for 24 h; the allocator's `overshoot_1s` per key, split by enforcer version, shows the canary admitting more than its share within one interval. Alert fires, rollout halts automatically.
  - Even in the worst case the allocator's deficit mechanism pushes `reject_for_ms` to the canaries, so the damage is bounded by `max_deficit` per key per canary pod.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: migrating off the Redis-based limiter without a gap in enforcement
- **Answer:**
  - Sidecar in shadow mode next to the Envoy filter; compare would-reject against real rejects per key for two weeks with a traffic simulation for burst, failover and partition cases.
  - Flip RLG by RLG; the old path goes to shadow for that RLG. Rollback is a flag on the filter chain. Redis goes read-only for a week before removal.
  - Databricks' intermediate step of batching Redis writes with Lua is a useful halfway house if the allocator is not ready: it removes the per-request hop first and the SPOF second.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: allocator rolling restart
- **Answer:**
  - Planned handoff, not failover: the rebalancer elects the new owner before the old one stops; the old owner ships its demand maps and deficits to the new one; enforcers see `WRONG_OWNER(epoch)` on the next report and switch. No learning mode, no lost deficit, no grace. One node at a time, 20 nodes in 10 minutes.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## 6. Security and abuse

## Edge case: a client sets its own account descriptor
- **Answer:**
  - Descriptors are attached by the gateway after authentication from the token's claims. Client-supplied headers with those names are stripped at the edge. A client cannot choose a bucket.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: a compromised or buggy enforcer floods the allocator with reports
- **Answer:**
  - mTLS identity per enforcer; the allocator rate-limits reports per enforcer to 100/s and drops the rest, logging the identity. One enforcer can at most cost one allocator node ~1% CPU. It cannot forge another enforcer's reports.
  - A buggy enforcer that reports `wanted = 0` for everything gets no share and rejects its own traffic; its `overshoot` and reject metrics split by version make this visible in one interval.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: an attacker creates millions of distinct keys (random user ids)
- **Answer:**
  - Unknown descriptor values map to the RLG's default policy node, and keys per tenant are capped by policy (say 1 M). Beyond that, new values share one overflow bucket. Enforcer memory is bounded by an LRU of 100 k keys per pod; allocator memory by the per-tenant cap. The attacker's traffic is limited by the account bucket regardless of how many user keys it invents.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: staying under a cloud provider's API quota (external limit we do not control)
- **Trigger:** our control plane calls a cloud API with a 1,000/s account quota; exceeding it throttles every workspace.
- **Answer:**
  - Model it as an RLG with `on_control_loss = static_split` and a conservative `rate` (80% of the quota). Under control loss each enforcer takes `rate / expected_enforcers`; the fleet cannot exceed the quota even when partitioned.
  - The provider's own token bucket (AWS EC2 API buckets, for example) is the source of truth; our limiter is a pacer in front of it, and 429/403 from the provider feeds back as `wanted` without `hits` so the allocator sees demand without admitting it.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident
