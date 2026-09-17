# Edge cases: distributed cache

Every entry answerable in under 60 seconds out loud. Categories: failure, consistency, scale, data, operations, security. Design reference: [`solution.md`](solution.md).

---

## Failure

## Edge case: one cache node dies
- **Trigger:** kernel panic, OOM, hardware.
- **Symptom:** clients see 20 ms timeouts for 0.25% of keys; on-call sees node 17 `suspect` then `dead` in the config service, replica read rate for its range goes from 0 to 25k/s.
- **Answer:**
  - Timeout = miss. After 3 timeouts the client marks the node suspect for 10 s and sends reads for its range to the replica (`RF = 2`), which has every item except the last 1 ms of sets.
  - Config service misses 3 heartbeats (3 s), publishes `epoch + 1` promoting the replica to owner; clients converge within 5 s; a new replica is streamed from the new owner over 80 s.
  - DB sees nothing. Without replication it sees at most one fill per key per 10 s via the gutter, capped by `max_fills_per_sec`.
  - Blast radius: 0.25% of keys get replica latency (same AZ or +300 us) for 5 s. Nothing else.
- **Diagram:** `solution.md` §5.4.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: a rack or AZ dies (133 nodes)
- **Trigger:** power, top-of-rack switch, AZ outage.
- **Symptom:** 33% of keys time out at once; suspect count alert fires; cross-AZ read traffic triples.
- **Answer:**
  - Replica placement is rack-aware and AZ-aware, so every lost range has a live replica in another AZ. Reads go there after the 3-strike suspect (100 ms per client).
  - Memory: the surviving 267 nodes hold their own 60 GB plus nothing new until the config service streams new replicas, which it does gradually (10 ranges at a time) to avoid a 33% copy storm.
  - DB: zero extra fills with RF = 2. Without it, this is the `+1 M reads/s` case that kills the DB, and the fill cap is the only thing standing.
  - Latency: two thirds of reads were already cross-AZ; now all of the lost AZ's ranges are. p99 rises from 1 ms to about 1.3 ms.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: config service is down or partitioned
- **Trigger:** Raft lost quorum, bad deploy.
- **Symptom:** `GetRing` fails; ring epoch age climbs on every client dashboard; no data-path metric moves.
- **Answer:**
  - Clients keep the last ring forever. Nodes keep serving. Leases, L1, fill caps are all client-local. The data path has no dependency on the config service being up.
  - What stops: adding or removing nodes, promoting replicas, hot-key list refresh. A node that dies during the outage is handled by the client's own suspect logic and replica reads; promotion waits.
  - A node that restarts during the outage reads its cached ring and pool config from local disk.
  - RTO 30 s for a Raft re-election; a full loss is a snapshot restore.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: the database is slow (p99 200 ms)
- **Trigger:** DB failover, lock storm, bad query.
- **Symptom:** fills take 100x longer; in-flight fills per app server climb; lease waits rise.
- **Answer:**
  - Each miss holds a lease for up to 10 s, so a slow fill does not turn into 200 duplicate fills.
  - The fill limiter is per second, not per in-flight, so at most 100 fills/s per server are started no matter how slow they are. DB load is capped at organic plus the cap; no amplification.
  - Non-lease-holders get the stale copy (kept 10 s after expiry or delete) for hot keys, or `miss, no fill` for cold ones, and the app degrades.
  - The cache is what keeps 95% of traffic working while the DB is sick. That is the whole point of the fill cap.
- **Diagram:** `solution.md` §10.4 third timeline.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: CDC pipeline lags or dies
- **Trigger:** consumer crash, binlog retention, DB failover resets positions.
- **Symptom:** CDC lag alert at 5 s; nothing else visible until a lost app-side delete leaves a stale value.
- **Answer:**
  - App-side deletes still cover 99.99% of writes at 200 us. The bound degrades from "1 s" to "TTL for the 0.01% whose app delete failed".
  - Consumer restarts from its last committed offset; replayed deletes are idempotent. A binlog gap is closed by a one-off "delete everything modified between t1 and t2" scan on the DB.
  - If lag exceeds the max TTL (30 d) it is meaningless; page at 5 s and fix within an hour.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

---

## Consistency

## Edge case: reader fills the cache with a value the writer just replaced (stale set)
- **Trigger:** reader misses, reads DB (v1); writer writes v2 and deletes; reader's `set(v1)` arrives last.
- **Symptom:** v1 served until TTL. At 1 M writes/s this happens thousands of times a day without the fix.
- **Answer:**
  - The reader's miss reply carried a lease token. The writer's `delete` invalidated it. The reader's `set(v1, token)` returns `not_stored`.
  - Next reader misses, gets a fresh token, fills v2. Cost: one extra miss.
  - Facebook's number: leases cut the peak DB query rate on this pattern from 17k/s to 1.3k/s.
- **Diagram:** `solution.md` §5.5.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: two owners for the same key during a ring change
- **Trigger:** epoch `e + 1` published; clients pick it up over 5 s.
- **Symptom:** a delete from a client on `e + 1` hits node 18; a read from a client still on `e` hits node 17 and gets the old value.
- **Answer:**
  - Accepted hole: up to 5 s, once a day, for 0.5% of keys. Say the number.
  - Nodes reject requests carrying an epoch older than their own with `MOVED`, so a node that has heard of `e + 1` (via heartbeat reply) forces the client to refresh, shrinking the window to the heartbeat interval (1 s).
  - Closing it fully needs a two-phase membership change (every client acks the new epoch before it takes effect). Not worth it for a cache.
  - The orphaned copy on node 17 is never read again and expires by TTL.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: the writer reads its own write and sees the old value
- **Trigger:** writer updates the row, deletes the key, then reads; another client's fill from a lagging DB replica lands between.
- **Symptom:** "I changed my name and it still shows the old one."
- **Answer:**
  - Writer's client puts the new value in its own L1 for 1 s after the write (or bypasses cache for that key for 1 s). Read-your-writes in region for one client.
  - Cross-client read-your-writes (I write on one device, read on another within 1 s) is not promised. Fill from the DB primary, not a replica, for keys tagged `fresh`, if the product needs it.
  - Cross-region: remote marker (§10.11).
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: client retries a `set` after a timeout and the value has changed in between
- **Trigger:** `set(k, v1, token)` times out (reply lost), client retries.
- **Symptom:** none if the token was consumed; a stale v1 if `set` had no token.
- **Answer:**
  - Lease-guarded sets are safe to retry: the token was consumed by the first attempt, the retry is `not_stored`.
  - Unguarded sets (app-initiated caching of a computed value) should carry `cas` from a prior `get` or accept last-writer-wins. Document which.
  - `incr` is the one non-idempotent call; batch locally and reconcile from the DB.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

---

## Scale

## Edge case: one key at 1 M QPS (read-hot)
- **Trigger:** viral item, a config key every request reads.
- **Symptom:** node 17 at 100% CPU and 8 Gbps; its other 2.5 M keys see the p99 of a saturated node.
- **Answer:**
  - Client count-min sketch flags the key within 10 s (above 1,000 QPS on one app server). Client L1 caches it for 1 s: node sees 5,000 QPS.
  - For keys that cannot be 1 s stale: write under `key#0..7`, read a random suffix, delete all on invalidation. 125k QPS each on 8 nodes.
  - Fleet-wide hot-key list from the config service so every client agrees on `R`.
  - What does not work: more shards (the unit of placement is the key), more replicas of the node (reads go to the owner unless suspect).
- **Diagram:** `diagrams.md` D10.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: one key written 1 M times/s (write-hot counter)
- **Trigger:** a global view counter.
- **Symptom:** node 17 saturated by `incr`; L1 does nothing because every write must land.
- **Answer:**
  - Aggregate in the client: local sum, `incr(key, n)` every 100 ms; 1 M/s becomes 50k/s.
  - Shard the counter: `key#rand(16)`, `mget` and sum on read.
  - If it must be exact and read-after-write, it is a DB single-writer problem, not a cache one.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: a hot key expires (thundering herd)
- **Trigger:** TTL reached on a 100k QPS key, or a deploy-time invalidation of 1,000 hot keys.
- **Symptom:** miss rate spikes; without leases, DB sees 200 identical reads per key per 2 ms.
- **Answer:**
  - First miss gets the lease; the other 199 get `miss, no lease` or the stale copy and retry in 10 ms. DB sees one read.
  - Hot keys do not wait for expiry: XFetch (`beta = 1`) has one reader refresh a little early, so the key never actually expires under load.
  - TTL jitter ±10% stops 1,000 keys from expiring in the same second.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: a 10 MB value
- **Trigger:** an app caches a whole page or a report.
- **Symptom:** every 1 KB get queued behind it on the same connection waits 3 ms; p99 breaks.
- **Answer:**
  - Rejected at the client above 1 MB. Between 64 KB and 1 MB goes to the large pool on its own connections. The default pool never sees it.
  - The app chunks anything larger (`key.0 .. key.n` plus a manifest) or does not cache it.
  - Memcached's own default is a 1 MB item max with 512 KB chunks for the same reason.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: 10x traffic tomorrow (100 M QPS)
- **Trigger:** growth, a launch.
- **Symptom:** none per node if memory is unchanged: 250k ops/s per node is 25% of the ceiling.
- **Answer:**
  - QPS alone does not add nodes; memory does. 10x QPS on the same 10 TB is 250k/s per node, fine.
  - Hot keys scale with traffic: the L1 and replication thresholds hold because they are per key, not per fleet.
  - Connections: 50,000 app servers is the proxy break-even. Move to mcrouter-style proxies, protocol unchanged.
  - DB fills scale 10x too (5 M/s at 95% hit) unless hit rate rises; that is a DB capacity conversation, not a cache one.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

---

## Data

## Edge case: slab calcification after a value-size change
- **Trigger:** a deploy changes the average value from 1 KB to 2 KB.
- **Symptom:** the 2 KB class evicts constantly while the 1 KB class sits full of dead items; hit rate drops 5 points.
- **Answer:**
  - The slab rebalancer moves empty pages between classes. It only moves *empty* pages, so it first evicts the whole page in the donor class (memcached's `slab_automove`).
  - Watch evictions per class; a 10x skew between classes is the alert.
  - A restart also resets the class mix, which is why a rolling restart (with replicas serving) is an acceptable fix once a quarter.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: key schema change (the app changes how keys are derived)
- **Trigger:** `user:{id}` becomes `user:v2:{id}`.
- **Symptom:** 100% miss on the new prefix; old prefix orphaned until TTL.
- **Answer:**
  - Roll out the new prefix behind a flag on 1% of app servers first; their misses warm the new keys at 1% of the fill rate.
  - The CDC consumer must know both derivations for one max TTL, or the old keys go stale-until-expiry (they are unread by the new code, so harmless).
  - Never `flush_all`; the DB cannot take a 100% miss.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: GDPR delete for a user
- **Trigger:** deletion request.
- **Symptom:** none; must be provable.
- **Answer:**
  - `delete` every key in the user's namespace on owner and replica; CDC issues the same from the DB deletes.
  - Orphans: previous owners after ring changes (bounded by max TTL 30 d), gutter (10 s), L1 (1 s), snapshots (encrypted, rotated within the TTL).
  - If the bound must be hours, the user namespace uses a 1 h max TTL.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

---

## Operations

## Edge case: what pages at 3am
- **Answer:**
  - Hit rate < 90% for 5 min (DB at risk). Fills > 80% of cap for 2 min. Any node > 90% memory or swapping. CDC lag > 5 s. Suspect nodes > 2%.
  - Not a page: one node dead (replica serves; ticket), lease waits (a stampede is being absorbed; ticket), slab skew (ticket).
  - First look: is it one pool, one AZ, or the fleet? One pool is a hot key or a large-value leak; one AZ is infra; the fleet is a client deploy.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: rolling out a client library build that mis-hashes keys
- **Trigger:** a hashing or ring-lookup bug.
- **Symptom:** the 1% canary's hit rate drops to near zero while the fleet's is unchanged.
- **Answer:**
  - Canary compares its own hit rate and p99 to the fleet's for 30 min before ramping. The bug shows only in the canary.
  - Rollback is a build flip; the canary's mis-placed fills expire by TTL and are harmless.
  - Without a canary this is a fleet-wide cold cache and a DB outage, which is the largest blast radius in the design.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: adding 40 nodes at once (20% capacity)
- **Trigger:** capacity push.
- **Symptom:** without staging, `+2 M` fills/s, 4x the DB budget.
- **Answer:**
  - Nodes enter at 10% ring weight and ramp 10% per minute; misses spread over 10 minutes and peak at 200k/s, which the fill cap and organic budget absorb.
  - Warm-from-old-owner turns most of those misses into cache-to-cache copies (200 us, no DB).
  - Add in batches of 10 with 5 minutes between if the DB is already near budget.
- **Diagram:** `solution.md` §6 Flow 5.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: migrating from a single big Redis
- **Trigger:** the existing cache is one 500 GB Redis with app-side sharding by `mod N`.
- **Answer:**
  - Four phases (diagrams.md D12): config service publishing the current list; ring hashing with dual-read for one TTL; leases and CDC; replicas.
  - Each phase is a client flag; rollback at any phase; the old Redis stays warm through phase 2 because nothing deletes from it until dual-read ends.
  - What you lose: Redis data structures. Inventory them first; anything beyond strings needs its own plan.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

---

## Security and abuse

## Edge case: a tenant floods random keys (cache-miss attack)
- **Trigger:** a bot requests millions of non-existent ids.
- **Symptom:** miss rate up, fills up, DB load up.
- **Answer:**
  - Negative caching: `add(key, NULL, 10 s)` on DB not-found, so each id costs one DB read per 10 s.
  - Per-server fill cap bounds the total; per-tenant fill budget bounds who pays.
  - Rate limit at the API edge on the tenant, not in the cache.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: an app server is compromised
- **Trigger:** RCE on one app host.
- **Answer:**
  - It can read and write any key, as it can with the DB. mTLS stops anything outside the fleet; per-key auth is not in scope for a cache.
  - It cannot change the ring (config service writes need operator credentials) or exceed its fill cap.
  - Blast radius is one app server's traffic share; revoke its cert.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident
