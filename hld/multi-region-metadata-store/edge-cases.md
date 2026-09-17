# Edge cases: Multi-region metadata store

Every entry answerable in under 60 seconds out loud. Categories: failure, consistency, scale, data, operations, security. Design reference: [`solution.md`](solution.md). Regions V (home), O (70 ms), F (95 ms from V, 155 ms from O).

---

## Failure

## Edge case: home region lost
- **Trigger:** V loses power, network, or its control plane. Both V voters of every V-homed range vanish.
- **Symptom:** writes to V-homed tenants time out for 5 to 12 s; on-call sees "ranges without lease" spike then recover; write p99 for those tenants rises to about 160 ms.
- **Answer:**
  - O1, O2, F1 are 3 of 5, a majority. Every acked write was on at least one of them (commit needed 3 acks, at most 2 were in V). RPO 0.
  - Election after the 3 s timeout; Raft's election restriction makes the survivor with the most complete log the leader.
  - The new leader waits for the old lease to expire (up to 9 s plus 500 ms offset) before granting itself epoch + 1, so V3 cannot still be serving. Typical RTO 5 to 6 s, worst 12 s.
  - Commits now need O plus F: 155 ms RTT. After 5 min the controller adds voters in O and F to restore 5.
- **Diagram:** [`diagrams.md`](diagrams.md#d5-region-loss-second-by-second).
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: far region F lost
- **Trigger:** F outage.
- **Symptom:** nothing user-visible for V-homed tenants. Stale reads from F clients fail (they are in F).
- **Answer:**
  - 4 of 5 voters remain; F1 was rarely on the commit path (its ack arrived 25 ms after O's). Latency unchanged.
  - Tenants homed in F fail over to their second pair (say O) exactly as in the V case.
  - No repair until 5 min; then the controller may add a temporary fifth voter in V or O, and moves it back when F returns.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: one voter node dies in the nearest region (O1)
- **Trigger:** hardware failure.
- **Symptom:** none. Commit acks now come from O2 alone on the remote side.
- **Answer:**
  - 4 of 5 voters, majority intact. Commit path unchanged: V1 + O2.
  - Risk window: if O2 also dies before repair, only V V F remain (3 of 5), still a majority, but a V loss during that window would be fatal. Hence the 5 min dead-node timer and the alert on ranges with fewer than 5 live voters.
  - Repair: controller adds a voter on another O node, snapshot of about 256 MB per range streams in seconds.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: leaseholder process pauses for 30 s (GC, VM migration)
- **Trigger:** stop-the-world pause on V3 after it evaluated a read.
- **Symptom:** none if the design is right; a stale read if it is wrong.
- **Answer:**
  - The lease check runs again after evaluation on the monotonic clock. 30 s later it is past expiry; the reply becomes `NotLeaseholder`.
  - If the guest clock did not advance during the pause, V3's next Raft message returns a higher term (O2 was elected at 3 s) and V3 steps down before replying.
  - Writes never had this problem: a proposal from V3's old term is rejected by every follower.
  - Belt and braces: the client keeps the highest `commit_ts` it has seen and refuses older responses.
- **Diagram:** [`diagrams.md`](diagrams.md#d5-paused-leaseholder-wakes-up).
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: V is partitioned from O and F but alive
- **Trigger:** backbone cut. V clients can reach V gateways and V nodes; nothing crosses to O or F.
- **Symptom:** V clients get `Unavailable` on linearizable ops after at most 9 s, stale reads keep working.
- **Answer:**
  - V3 cannot renew its lease (renewal is a Raft commit needing O or F). It stops serving linearizable ops when the lease expires on its own clock, with no message from anyone.
  - Check-quorum makes it step down as Raft leader within one election timeout, earlier than the lease.
  - O and F elect and serve. Two leaders never coexist for writes (term) or reads (lease expiry plus offset).
  - If V's Internet egress works, the client SDK's failover order (home, nearest, far) reaches the O gateway. If V is fully isolated, V clients are down, which is correct.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: meta range loses quorum
- **Trigger:** two of its five voters down plus a third slow.
- **Symptom:** requests that miss the descriptor cache fail; everything cached keeps working.
- **Answer:**
  - Gateways cache descriptors; hit rate above 99.99% in steady state. Blast radius is new keys and post-split routes.
  - The meta range has the same 5-voter, 2 + 2 + 1 rules and the same alerts; it is one range among 6,000 with a higher alert priority.
  - Gateways serve a request from cache even if the meta range is down; correctness is preserved by `RangeKeyMismatch` from the data range.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: clock on one node jumps 800 ms
- **Trigger:** bad NTP step, hypervisor clock reset.
- **Symptom:** node V7 logs fatal and exits; its 25 leaseholder ranges fail over in about 10 s.
- **Answer:**
  - Peers measure offset on every heartbeat; median above 500 ms means the node exits (alert already fired at 250 ms).
  - Why exit and not correct: a lease read served with a fast clock may have been served after real expiry; exiting bounds the damage to one lease length.
  - HLC never goes backward on restart: the node persists its max HLC and starts above it.
- **Diagram:** `solution.md` §10.4.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: placement controller ships a bad rule and moves every lease to F
- **Trigger:** config typo, `lease_preference = F` fleet-wide.
- **Symptom:** write p99 from V jumps to 190 ms, home-region linearizable reads jump to 95 ms. Correctness unaffected.
- **Answer:**
  - Leases are correct wherever they are; only latency moves. Alert "leaseholders outside preferred region > 1%" fires in minutes.
  - Rollback is "stop the controller, revert the rule"; leases drift back within seconds of the next preference check.
  - Canary: controller rules apply to 1% of ranges for one hour first.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

---

## Consistency

## Edge case: two regions create the same name at the same instant
- **Trigger:** `create sales/orders` from V and from F within 1 ms.
- **Symptom:** exactly one `201`, one `409`.
- **Answer:**
  - Both reach the single leaseholder of range 42. The latch on the key serializes them.
  - The first checks "no live version", proposes, commits (75 ms), applies version 1, releases the latch.
  - The second takes the latch, sees version 1, replies `409 {current_version: 1}` without touching Raft.
  - Arrival order does not matter; whichever gets the latch first wins. There is no window where both see "absent".
- **Diagram:** `solution.md` §6 Flow 4.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: client's write times out, retries, and cannot tell if it happened
- **Trigger:** ack lost between leaseholder and gateway, or leaseholder changed mid-request.
- **Symptom:** retry of a `create` would get `409`; retry of a CAS would get a version mismatch.
- **Answer:**
  - Every write carries `Idempotency-Key`, stored inside the Raft entry with its result, so any leaseholder (old or new) finds it on retry and returns the original response.
  - 10-minute TTL, 100 B per entry, replicated because it is in the log.
  - Without the key, CAS is still safe (never applied twice) but the client cannot distinguish "I won" from "someone else won". With the key, it can.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: read right after a write from another region
- **Trigger:** V client writes version 9; F client reads 10 ms later.
- **Symptom:** depends on the read mode the F client chose.
- **Answer:**
  - `linearizable`: forwarded to V3, sees version 9. Cost 95 ms.
  - `stale_ok max_age 5 s`: F1 serves at its closed timestamp, which may be up to 5 s old; version 8 is a legal answer and the header says how stale.
  - `min_version 9` (the F client was told by the V client, or by the watch stream): F1 waits until it has applied version 9 (typically 100 ms), then serves locally. This is read-your-writes and is what most callers want.
  - The rule: linearizable by default, stale only when asked, and the API says which one you got.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: list during a rename
- **Trigger:** `list sales/` paginating while `sales/orders` is renamed to `sales/orders_v2`.
- **Symptom:** none. The object appears exactly once.
- **Answer:**
  - The gateway picks `as_of` once and every page scans at that timestamp. MVCC keeps the old version for 24 h.
  - The rename is one Raft entry (same range) or a 2PC with one commit point (cross range); at `as_of` it is either entirely visible or entirely not.
  - A reader that meets an unresolved intent at `as_of` looks up the transaction record; PENDING intents are ignored.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: snapshot timestamp chosen on a slow clock
- **Trigger:** gateway's HLC is 300 ms behind V3's. A write committed at `10:00:00.200` on V3 happened before the list started at gateway time `10:00:00.000`.
- **Symptom:** none if handled; a list that misses a committed row if not.
- **Answer:**
  - Every version with `commit_ts` in `(as_of, as_of + max_offset]` is uncertain. The scan restarts once with `as_of` moved past the newest uncertain version it met.
  - Bounded because `max_offset` is 500 ms and nodes exit above it.
  - This is what TrueTime's commit-wait avoids at the price of about 7 ms per write. On a catalog, one rare restart is cheaper.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: cross-range transaction coordinator dies after writing intents
- **Trigger:** range 42's leaseholder dies after step 2 of 2PC, record still `PENDING`.
- **Symptom:** an intent sits on `finance/orders` in range 43.
- **Answer:**
  - The record is in Raft, so the new leaseholder of range 42 has it. Nothing is lost; the txn is just unfinished.
  - A reader or writer that meets the intent looks up the record. If `PENDING` and older than the txn timeout (10 s), it aborts the record by CAS on its status, then resolves the intent as aborted.
  - The client sees a timeout and retries with its `Idempotency-Key`; the new attempt finds either COMMITTED (returns success) or ABORTED (runs again).
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: watch client falls behind by a day
- **Trigger:** consumer down for 26 h; GC horizon is 24 h.
- **Symptom:** `watch from_version=old` returns `snapshot_required`.
- **Answer:**
  - The range no longer has versions that old; replay is impossible.
  - Client does a `list` at the current closed timestamp, rebuilds its cache, and re-opens the watch from that `as_of`. Events between the list's `as_of` and the watch start are replayed because the watch starts at the timestamp, not "now".
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

---

## Scale

## Edge case: one tenant has 50 M tables and 40% of writes
- **Trigger:** a large customer.
- **Symptom:** before splits, one range at 2,000 writes/s on one node; after, nothing.
- **Answer:**
  - Load-based splits at 2,000 ops/s for 30 s cut the tenant's keyspace into about 200 ranges whose leaseholders spread over the 20 home-region nodes.
  - The remaining hot spot is any single key every op touches. We refuse to have a per-schema version that bumps on every table create, or a table counter. Lists are range scans, counts are a periodic aggregate.
  - Range count per node (500) is the pressure point at 10x; add nodes.
- **Diagram:** `solution.md` §5.5.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: list of 5 M keys under one prefix
- **Trigger:** `list sales/` on the big tenant.
- **Symptom:** 5,000 pages.
- **Answer:**
  - Sequential scan across adjacent ranges at one `as_of`; served by followers in the caller's region, never by the leaseholder.
  - Per page: 1,000 keys × 1 KB = 1 MB, about 5 ms from the LSM.
  - Rate limit 100 pages/s per tenant so a runaway lister cannot saturate a node; offer `count` from a periodic aggregate for UIs.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: Monday 9am, 10x reads in every region at once
- **Trigger:** every notebook and job wakes up.
- **Symptom:** 5 M reads/s aggregate.
- **Answer:**
  - 70% stale: 3.5 M/s over 60 nodes = 60k/s per node from local disk. Fine.
  - 20% linearizable home-region: 1 M/s on 20 leaseholder nodes = 50k/s per node, lease reads, no network. Fine.
  - 10% linearizable remote: 500k/s crossing regions. This is the bucket to shrink with `min_version` tokens; alert if it exceeds 5% of reads.
  - Writes 10x = 50k/s, 800/s per leaseholder node. Fine.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: thundering herd on one key (a feature flag every service reads)
- **Trigger:** 100k reads/s on `global/flags/x`.
- **Symptom:** one leaseholder node saturated if every read is linearizable.
- **Answer:**
  - Most callers should use `stale_ok`, which spreads the key over 5 replicas and every region.
  - For the linearizable minority, the leaseholder's lease read is 1 ms of CPU and no IO (block cache); 100k/s is one core's worth. Load-based splitting cannot help a single key; the fix is the read mode and a client-side cache fed by watch.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

---

## Data

## Edge case: value schema changes (new field on the table object)
- **Trigger:** catalog team adds `retention_days` to the table value.
- **Symptom:** none in the store; values are opaque bytes.
- **Answer:**
  - The store never interprets values. Schema evolution is the catalog team's problem: version the value encoding, readers ignore unknown fields.
  - Backfill is a `txn` per key with `expected_version` so a concurrent user write is never overwritten.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: GDPR delete of a tenant's metadata
- **Trigger:** legal request.
- **Symptom:** every version of every key must be unrecoverable.
- **Answer:**
  - Tombstone every key (a range delete entry per range), then a `purge` op lowers the GC horizon for that tenant to now so versions are compacted out within the next compaction cycle (hours).
  - Raft log entries containing the old values are truncated once snapshotted; the snapshot after purge has no trace. Backups taken before the purge are handled by the backup retention policy, stated in the DPA.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: backfill 100 M keys from an old system
- **Trigger:** migration.
- **Symptom:** write rate far above 5k/s.
- **Answer:**
  - Bulk path: build SSTs per range offline and ingest them under a Raft entry that references the file, the way CockroachDB's `IMPORT` does. 100 M keys at 1 KB is 100 GB, minutes not days.
  - The range boundaries are pre-split from the source's key distribution so the load lands on many leaseholders.
  - Live traffic keeps working; ingest is a background entry per range.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: three years of growth
- **Trigger:** 1 B keys becomes 5 B, 5k writes/s becomes 20k/s.
- **Symptom:** 30,000 ranges, 2,500 replicas per node at 60 nodes.
- **Answer:**
  - Per-node replica count is the pressure point (heartbeats are coalesced, but Raft state and LSM keyspace per replica are not free). Add nodes to keep it under 1,000, or raise the split size to 512 MB.
  - The meta range becomes two levels when descriptors exceed one range.
  - Version storage stays proportional to write rate × 24 h; at 20k/s that is 1.7 TB of versions per replica. Lower the GC horizon to 6 h if it matters.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

---

## Operations

## Edge case: what pages at 3am
- **Trigger:** on-call rotation.
- **Symptom:** the pager.
- **Answer:**
  - Unavailable ranges > 0 for 60 s. Ranges without a valid lease > 0 for 15 s. Clock offset > 250 ms on any node. Write p99 > 200 ms from the home region for 5 min. A region's median Raft apply lag > 2 s.
  - Tickets, not pages: leaseholders outside preferred region > 1% for 10 min; meta range QPS > 10x baseline; follower-read staleness p99 > 5 s.
  - Every page has a runbook whose first step is "which region, which ranges, is it a lease problem or a quorum problem".
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: rolling out a new node binary
- **Trigger:** weekly release.
- **Symptom:** none if the rule holds.
- **Answer:**
  - One node per region for 24 h, then one region, then all. At most one voter per range is restarting at a time, so quorum never depends on the new binary.
  - Drain before restart: transfer leases away (one Raft entry each), wait for the change feed to catch up, then stop. A drained node's restart costs no election.
  - Rollback is a redeploy of the previous binary in the same order.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: migrating from single-region Postgres
- **Trigger:** this design is approved.
- **Symptom:** a six-month plan.
- **Answer:**
  - CDC snapshot plus tail from Postgres into the store per tenant; reconcile counts and checksums.
  - Dual write with Postgres as truth; alert on divergence; hold for 7 clean days.
  - Flip reads per tenant behind a flag (stale first, then linearizable), then writes with reverse CDC to Postgres, keep the rollback window 30 days.
  - Rollback at every phase is a flag flip; data reconciliation uses versions.
- **Diagram:** [`diagrams.md`](diagrams.md#d12-rollout--migration-from-single-region-postgres).
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: proving linearizability in production
- **Trigger:** an interviewer asks "how do you know".
- **Symptom:** the honest answer is a test, not a proof.
- **Answer:**
  - Jepsen-style: a canary workload does CAS on a handful of registers from every region under injected partitions and clock skew; the history is checked with Porcupine or Knossos (Elle for the transactional API). Runs hourly in production against a canary tenant, nightly with fault injection in staging.
  - Invariant checks on the real data: no duplicate names, versions strictly increasing per key, every `commit_ts` within `max_offset` of its wall time.
  - The known limits: the checker is NP-hard in the worst case, so histories are kept short.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

---

## Security / abuse

## Edge case: a tenant reads another tenant's keys
- **Trigger:** crafted path `../t2/...` or a forged tenant id.
- **Symptom:** none.
- **Answer:**
  - The token is signed by the identity provider and carries `tenant_id`; the gateway builds the key prefix from the token, never from the path. Path normalization happens before prefixing.
  - Ranges are tenant-contiguous; a scan cannot cross the tenant's `end_key` because the gateway clamps it.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: a tenant's DDL storm
- **Trigger:** a migration script issues 20k `create` per second.
- **Symptom:** one tenant's ranges saturate their leaseholders.
- **Answer:**
  - Gateway token bucket per tenant: 1,000 writes/s, 100 list pages/s; excess gets `429` with a retry hint.
  - Load-based splits spread the admitted 1,000/s over several leaseholders within 30 s.
  - Other tenants are on other ranges and other leaseholders; the blast radius is the storm's own tenant.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: a rogue process tries to join a Raft group
- **Trigger:** compromised host inside the network.
- **Symptom:** none.
- **Answer:**
  - Node-to-node traffic is mTLS with certificates issued only by the placement controller; membership changes are Raft entries proposed by the controller and signed.
  - A node not in a range's descriptor gets its `AppendEntries` rejected; it cannot vote because it is not in the voter set.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident
