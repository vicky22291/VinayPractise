# Multi-Region Metadata Store: Interview Framing Survey

**Problem:** Design a multi-region metadata store with linearizable writes
**Reported at:** Databricks, Google
**Interview level:** Staff Engineer (deep systems knowledge required)

## Sources Table

| ID | URL | What it establishes |
|----|-----|-----|
| S1 | https://www.systemdesignhandbook.com/guides/databricks-system-design-interview/ | Databricks asks metadata service / versioned table store / transaction log problems |
| S2 | https://www.designgurus.io/answers/detail/what-to-expect-in-the-databricks-system-design-interview | Databricks mentions "versioned table store or metadata service" with transaction logs, snapshot isolation, schema evolution |
| S3 | https://www.systemdesignhandbook.com/guides/zookeeper-system-design/ | ZooKeeper design: leader-based writes via ZAB protocol, quorum-based fault tolerance |
| S4 | https://research.google.com/archive/spanner-osdi2012.pdf | Spanner paper: TrueTime API, Paxos consensus, external consistency (linearizability + causality) |
| S5 | https://docs.cloud.google.com/spanner/docs/true-time-external-consistency | Spanner TrueTime: atomic clocks + GPS, clock uncertainty typically <10ms, enables global linearizable writes |
| S6 | https://blog.bytebytego.com/p/how-google-spanner-powers-trillions | Spanner: multi-region consistency via TrueTime interval timestamps, 2PC for multi-split writes, commit wait |
| S7 | https://www.designgurus.io/blog/cockroachdb-vs-tidb-vs-spanner | CockroachDB uses Raft (not TrueTime), spans regions, targets strong consistency without clock sync dependency |
| S8 | https://www.designgurus.io/system-design-interview/concepts/replication-consistency | Consistency models: eventual -> read-your-writes -> monotonic reads -> causal -> linearizable. Trade-off cost/latency |
| S9 | https://www.systemdesignhandbook.com/guides/raft-consensus-algorithm/ | Raft: leader-based log replication, majority quorum, ensures linearizability via state machine safety |
| S10 | https://www.designgurus.io/answers/detail/what-is-the-raft-consensus-algorithm-and-how-does-it-work-at-a-high-level | Raft achieves linearizability: leader serializes writes, followers log-replicate, quorum commits before response |
| S11 | https://www.designgurus.io/answers/detail/what-is-a-split-brain-scenario-in-a-distributed-cluster-and-how-can-systems-prevent-or-resolve-it | Split-brain: quorum consensus + witness nodes + STONITH fencing to ensure single partition writes |
| S12 | https://research.google.com/archive/chubby-osdi06.pdf | Chubby: lock service + metadata store, 5 replicas, leader handles writes, client-side caching, used by GFS/Bigtable |
| S13 | https://www.designgurus.io/answers/detail/how-do-quorum-readswrites-n-r-w-impact-latencydurability | Quorum: R+W > N guarantees overlap; read hits latest replica. Trade latency vs consistency per-query |
| S14 | https://www.designgurus.io/answers/detail/what-is-a-distributed-lock-and-how-can-you-implement-locking-in-a-distributed-environment | Distributed locks: ephemeral sequential znodes, watch predecessors, avoid thundering herd, used in ZooKeeper |
| S15 | https://jepsen.io/ | Jepsen: framework for testing linearizability via fault injection, history analysis, handles NP-complete checking |
| S16 | https://github.com/donnemartin/system-design-primer | GitHub system-design-primer: leader election, consensus, fault-tolerant patterns |
| S17 | https://pdos.csail.mit.edu/6.824/labs/lab-shard1.html | MIT 6.5840 Lab 5: sharded KV with multiple Raft groups for parallel writes |
| S18 | https://www.designgurus.io/course-play/grokking-scalable-systems-for-interviews/doc/what-are-read-repair-hinted-handoff-and-antientropy-merkle-trees-in-eventually-consistent-systems | Read-repair, hinted-handoff, anti-entropy: eventual consistency repair mechanisms (not strong consistency) |
| S19 | https://github.com/cockroachdb/docs/RFCS/20210519_bounded_staleness_reads.md | Bounded staleness: follower reads within defined max-staleness bound, relieves leader read load |
| S20 | https://www.designgurus.io/course-play/grokking-scalable-systems-for-interviews/doc/what-is-quorum-n-r-w-and-why-does-r-w-n-give-strongly-consistent-reads | Quorum consistency: R+W > N, strongly consistent reads; impacts latency and durability |

---

## 1. How the Prompt Is Phrased in the Wild

The "multi-region metadata store with linearizable writes" problem appears across several phrasings:

**Exact phrasing variants:**
- "Design a multi-region metadata store" — Databricks reports this directly. [S1, S2]
- "Design a versioned table store or metadata service" — Databricks interviews probe Delta Lake schema metadata, transaction logs, snapshot isolation. [S2]
- "Design Spanner" / "Design a globally distributed database" — Google asks this; tests understanding of TrueTime, Paxos, external consistency. [S4, S5]
- "Design etcd" or "Design ZooKeeper" — Configuration store, distributed coordination, leader election. [S3]
- "Design a distributed lock service like Chubby" — Google uses this; storage for coordination metadata. [S12]
- "Design a global configuration store with strong consistency across regions" — Kubernetes-style metadata (Etcd core use case).
- "Design Unity Catalog metastore for multi-region" — Databricks-specific variant; metadata for schemas, tables, access policies. [S1]

**Which companies ask which variant:**
- **Databricks**: Metadata service, versioned table store, transaction logs, Delta Lake schema management. [S1, S2]
- **Google**: Spanner (linearizable global DB), Chubby (lock + metadata), distributed coordination. [S4, S12]
- **Meta, Amazon**: Often phrase as "design a distributed KV store" or "DynamoDB alternative"; less about metadata, more about scale.
- **Smaller tech companies**: "Design ZooKeeper" or etcd-like system for service discovery and config.

**Connection to metadata:**
All variants boil down to the same core: small data, read-heavy, correctness-critical (cannot serve stale), requires cross-region strong consistency. [S1, S2, S4]

---

## 2. What "Metadata" Means in This Prompt

Metadata in distributed systems refers to small, control-plane data that coordinates other services. Size and access patterns are critical.

**Examples candidates should propose:**

- **Table/schema catalog** (Databricks Unity Catalog, Hive Metastore): schema definitions, column types, partitioning info, table properties. [S1, S2]
- **File-system namespace** (HDFS NameNode, GFS Master): directory tree, file block mappings, inode state. [S12]
- **Cluster/job configuration** (Kubernetes, Spark Driver): replica counts, resource limits, node labels, job definitions.
- **Access control lists (ACLs)**: permissions matrix, role assignments, security policies.
- **Feature flags / release toggles**: per-tenant or per-region enable/disable.
- **Service registry**: service addresses, health status, version info.

**Typical object size:**
- Per-key: 100 bytes to 10 KB (most common: <1 KB).
- Max value size often unconstrained (100s of KB possible but rare).
- Chubby stores 64 MB per file; ZooKeeper soft limit 1 MB per znode. [S12, S3]

**Read:write ratio:**
- Heavily read-dominant: 100:1 to 1000:1 is common. [S3]
- Most operations are config reads, discovery reads, watch notifications.
- Writes are infrequent: schema changes, new table registrations, permission updates.

**Why metadata is the classic consensus case:**
- Small size means consensus protocol overhead is acceptable (quorum round-trips not a bottleneck).
- Reads must reflect latest state (no stale cache OK for control plane).
- Correctness failures (split-brain, lost ACLs, stale schema) cascade into application layer.
- Cross-region clients need the same view (linearizability essential).
[S3, S4, S12]

---

## 3. Functional and Non-Functional Requirements

**Functional requirements (candidates should list these):**

1. **Get/Put/Delete**: read a key, write a key, remove a key.
   - Get returns value or "not found".
   - Put is "create or overwrite" (LWW semantics not required; clients handle idempotence).

2. **Compare-and-swap (CAS)**: atomic "write if value matches expected". Essential for leader election, versioning.

3. **List by prefix**: scan all keys matching a prefix (e.g., "tables/mydb/*").
   - Pagination required for large result sets.

4. **Watch/notify**: subscribe to changes on a key or prefix; receive async notifications when data changes. [S14]
   - Critical for pulling config changes without polling.
   - Watchers receive value + version/revision number.

5. **Transactions over a small key set**: atomically update 2-3 related keys (e.g., table + ACL). [S2]
   - Not required for arbitrary multi-key ACID; single-key atomicity via CAS often sufficient.

6. **Leases/TTL**: keys can auto-expire; used for ephemeral locks, session state. [S3, S14]

**Non-functional requirements (with sources):**

| Requirement | Target | Source/Notes |
|---|---|---|
| Linearizable writes | Required (no AP option) | [S4, S5, S6] Spanner, Chubby, ZooKeeper all enforce this. |
| Read latency (local) | p99 < 10 ms | [S5] Spanner TrueTime clock uncertainty typical; metadata read from leader or cached replica. |
| Write latency (cross-region) | p99 < 200 ms | Typical target; Spanner p99 ~100-200ms for multi-region writes (quorum + commit-wait). [S6] |
| Availability | 99.999% or 99.99% | Depends on RTO/RPO. Metadata store usually 99.99% minimum. [S3, S12] |
| RPO (Recovery Point Objective) | 0 (no data loss) | Synchronous replication to quorum before ack. [S3, S4, S6] |
| RTO (Recovery Time) | <30 seconds | Leader re-election + failover. Raft/Paxos typically <10-30s. [S9] |
| Consistency model | Linearizable (external consistency) | [S4, S5, S6] No eventual consistency option; every write visible to all readers after commit. |
| Scale: keys | 1 billion (1B) | Typical for large Kubernetes clusters, big data catalogs. [Typical target, no single source] |
| Scale: reads/sec | 100k | Config cache + read-your-writes clients reduce direct load. [Typical target] |
| Scale: writes/sec | 1k | Infrequent; metadata changes are rare vs application data. [Typical target] |
| Multi-region span | 3-5 regions | Replication to N regions; must survive loss of 1. [S3, S4, S6] |
| Partition tolerance | Survive 1 region loss | Quorum survives N/2 + 1 failures; fencing prevents split-brain. [S11] |

---

## 4. The Bad / Good / Great Ladder

For each dimension, the interviewer expects progression:

### (a) Write Path

**Bad** (junior signal; likely fails):
- Single-region database with async replication to other regions.
- Leader in one region, followers copy asynchronously.
- Writes ack after leader commit, but cross-region visibility delayed.
- Split-brain risk if primary region partitions.
- [Fails linearizability: reads in replica region may miss recent writes.]

**Good** (senior signal):
- Single global Raft group (or Paxos consensus).
- All replicas in all regions participate in quorum.
- Write sent to leader, replicated to all regions, waits for quorum ack (e.g., 2 of 3).
- Linearizable writes, but write latency high (quorum round-trip across regions ~100-200ms p99).
- [Passes linearizability, but not optimal latency.]

**Great** (staff signal):
- Sharded Raft groups by key range; leader for each shard elected in "home region" (region that owns that key range).
- Write sent to shard leader's region, quorum includes replicas in that region + witness in another region.
- Other regions can serve reads via lease reads or bounded-staleness follower reads (not stale-unsafe).
- Reduces write latency for region-local writes (~50-100ms p99).
- Handles region loss: if primary region fails, witness + surviving replicas elect new leader in secondary region.
[Staff-level reasoning: trade-off locality + consistency + fault tolerance.]

**References:** [S6, S9, S10, S19]

### (b) Read Path

**Bad:**
- Always route reads to leader (even in remote regions).
- Reads cross entire planet; p99 latency ~500ms+.
- [Wastes latency when stale data acceptable or when leader can't prove freshness.]

**Good:**
- Lease reads: leader grants a "read lease" for N milliseconds; any follower can serve reads during lease without contacting leader.
- Followers serve reads during lease period, leader re-leases periodically.
- Breaks if leader crashes before lease expires (old replica serves stale data), but rare.
- [Improves read locality; read latency p99 <50ms from any region.]

**Great:**
- Bounded-staleness reads from followers: followers track leader's latest commit index; serve reads that lag by <X ms / Y versions.
- Clients specify staleness bound; read from nearest follower if it meets bound, else upgrade to leader.
- Avoids leader read load entirely for stale-tolerant queries (config caches, historical queries).
- Mechanism: follower gossips commit index; client checks: "follower at index I100, leader at I102, bound is I100; OK to serve".
[Staff-level: understand staleness bounds + leader offload.]

**References:** [S19, S5]

### (c) Region Loss & Failover

**Bad:**
- Manual failover: operator detects region failure, manually updates DNS and leader config.
- RTO >30 min (slow human response).
- Risk of split-brain if operator makes wrong choice (both regions think they're primary).

**Good:**
- Automatic leader re-election: 5 replicas across 3 regions (2 + 2 + 1 distribution); quorum = 3.
- If primary region fails, surviving 3 replicas (2 in secondary, 1 in tertiary) hold election.
- New leader elected <10-30s; clients reconnect.
- [No manual intervention; RTO <30s; avoids split-brain via quorum math.]

**Great:**
- Witness node or explicit fencing: primary leader holds a "lease" from a witness coordinator.
- If primary leader's lease expires (region isolated), it stops serving writes immediately (self-fences).
- Secondary replicas can take leadership only if they can acquire lease from witness (proves primary is truly dead).
- Prevents old region's leader from serving stale writes if network partition heals.
- Example: CockroachDB leaseholder + witness; Chubby master + lease. [S11, S12]
[Staff-level: name split-brain risk + specific fencing mechanism.]

**References:** [S11, S9, S12]

### (d) Transactions Over Multiple Keys

**Bad:**
- No multi-key transaction support.
- Clients do read-modify-write in app logic; non-atomic across network.
- Can lose updates if two clients race (last-write-wins client loses their work).

**Good:**
- Single-shard transactions only (via key design).
- If all keys in transaction hash to same shard, Raft group leader handles atomically.
- Multi-shard transactions not supported.
- [Covers many cases (e.g., schema + table metadata on same shard), but not all.]

**Great:**
- Two-phase commit over Raft groups (2PC).
- Client sends transaction to shard leaders; each shard votes "commit" or "abort".
- If all vote commit, coordinator orders a global commit record in Raft.
- Handles arbitrary multi-key atomicity, but slower (2 Raft write rounds + 2PC voting). [S6]
[Staff-level: 2PC overhead + contention; when worth it vs app-level eventual consistency.]

**References:** [S6]

---

## 5. The Follow-Up Ladder (15 questions)

Interviewers probe consistency, failure modes, and trade-offs in this order:

1. **Why not a single global leader in one region?**
   Single leader bottlenecks all writes; cross-region clients see ~500ms p99 latency. Fails SLO. [S6]

2. **How does a follower know if its data is fresh enough to serve a read linearizably?**
   Follower tracks "committed index" from leader; can serve reads if follower's applied index >= leader's commit index. [S9, S10]

3. **What if system clocks drift? Does linearizability still hold?**
   Raft systems (not Spanner) don't rely on clocks; order comes from log indices + commit index. Be explicit about clock assumptions. [S4, S5, S9]

4. **Second-by-second, what happens when primary region dies?**
   T=0-5s: heartbeat lost, new election triggered. T=5-10s: new leader elected in secondary. T=10-30s: clients reconnect. Clients in dead region see timeout + backoff-retry. [S9]

5. **Can a client in the dead region still read stale data?**
   No; if replica loses quorum, it refuses reads. If using witness/fencing, old leader's lease expires and it self-fences. Client sees error, not stale data. [S11, S12]

6. **How do you avoid the old leader serving stale writes if network heals?**
   Lease + fencing: old leader's lease held by witness. Expired lease forces self-fence. Old leader cannot serve writes after network heals. [S12, S11]

7. **How do you atomically create a key if it doesn't exist (create-if-absent)?**
   Use CAS (compare-and-swap). Raft serializes CAS; exactly one succeeds even if clients race. Linearly serializable. [S9, S14]

8. **How do you list 1 million keys under a prefix without blocking leader?**
   Pagination with continuation tokens. Leader returns [0-1000], client sends next token for [1000-2000]. Optional: snapshot reads (eventual for list, OK for metadata). [S3]

9. **Hot tenant: one tenant generates 50k QPS of 100k QPS cluster. What do you do?**
   Name bottleneck: single shard saturated. Mitigations: shard hot key further, use bounded-staleness reads for offload, client-side cache. [S9, S19]

10. **How do you add a new region to an N-region cluster?**
    Snapshot current state to new region, replay Raft log, catch up to leader. New region joins quorum. Use joint consensus to change config atomically. [S9]

11. **How do you migrate from single-region Postgres to multi-region without downtime?**
    Phase 1: dual-write (both systems). Phase 2: backfill. Phase 3: flip reads. Phase 4: decommission once Spanner lag < 1s. Rollback: revert to Postgres if bugs found.

12. **What pages at 3am? SLO alerts?**
    Leader election failure (>30s), replication lag (>X seconds), quorum loss (<N/2+1 replicas), write latency spike (>500ms p99), cross-region latency spike.

13. **How do you test linearizability (Jepsen, Elle, Porcupine)?**
    Jepsen injects faults, collects operation history, finds valid serialization order. Elle checks causal consistency. Porcupine is faster than O(n!). [S15]

14. **Why not DynamoDB global tables?**
    Multi-master async + LWW is non-linearizable (clock skew violates ordering). Eventual consistency only. No option for linearizable writes. [References: S8]

15. **Can you use Kafka instead of Raft consensus?**
    No. Kafka guarantees order per partition, not global causal order. Multiple partitions + multi-master = non-linearizable. Consensus required. [S9]

---

## 6. Red Flags and Down-Level Signals

Interviewer watches for these anti-patterns:

1. **"Use multi-master replication with LWW"**
   - LWW is non-linearizable; violates the core requirement.
   - Red flag: candidate doesn't understand difference between "eventual" and "linearizable".

2. **"3 replicas in 2 regions; if one region fails, 2 replicas survive"**
   - Red flag: math error. 3 nodes, quorum = 2; if one region has 1 replica and the other has 2, a network partition isolates the single-replica region.
   - Correct: 3 replicas in 3 regions (1 each) so any 2 form quorum; if 1 region fails, 2 remain and can elect leader.

3. **"Reads from any replica are fine"**
   - Red flag: candidate doesn't understand linearizability.
   - Correct: reads from follower must check commit index or use lease; stale reads are not linearizable.

4. **"We'll just use NTP for clock sync and not worry about skew"**
   - Red flag: candidate is building Spanner's assumptions without Spanner's TrueTime infrastructure.
   - Correct: either use TrueTime (hard), or use Raft consensus (doesn't rely on clocks).

5. **"If the leader crashes, clients automatically switch"**
   - Red flag: no mention of RTO or failover time.
   - Correct: leader re-election takes 5-30s; clients see connection timeout and backoff-retry.

6. **No mention of fencing or split-brain risk**
   - Red flag: missing a critical failure mode.
   - Correct: explicitly describe how old leader is prevented from serving stale writes (lease, witness, or other fence).

7. **"Every read goes to the leader"**
   - Red flag: severe latency problem; doesn't optimize for read-heavy workload.
   - Correct: leader read + lease-read + bounded-staleness read options.

8. **"Writes wait for all N replicas to ack"**
   - Red flag: unnecessary durability cost; one slow replica blocks all writes.
   - Correct: write waits for quorum (N/2 + 1), not all N.

9. **No discussion of transaction semantics across keys**
   - Red flag: metadata often needs multi-key atomicity (e.g., table + permissions in one commit).
   - Correct: single-key CAS or 2PC over Raft groups.

10. **"We'll cache everything on the client side"**
    - Red flag: caches go stale; doesn't solve the consistency problem.
    - Correct: cache + watch or cache + TTL, but still need backend consistency.

---

## 7. Sources to Read Before the Interview (Ranked)

**Tier 1 (must read):**

1. [Replication and Consistency](https://www.designgurus.io/system-design-interview/concepts/replication-consistency) [S8] — Clarity on consistency models (linearizable vs eventual). 15 min.

2. [ZooKeeper System Design Guide](https://www.systemdesignhandbook.com/guides/zookeeper-system-design/) [S3] — Concrete example of leader-based consensus for metadata. 30 min.

3. [Raft Consensus Algorithm Guide](https://www.systemdesignhandbook.com/guides/raft-consensus-algorithm/) [S9] — Modern alternative to Paxos; used by CockroachDB, etcd, Consul. 30 min.

4. [Google Spanner externally consistent writes](https://docs.cloud.google.com/spanner/docs/true-time-external-consistency) [S5] — How to achieve linearizable writes across regions (TrueTime method). 20 min.

**Tier 2 (strongly recommended):**

5. [Spanner OSDI 2012 paper](https://research.google.com/archive/spanner-osdi2012.pdf) [S4] — Authoritative source on TrueTime, Paxos, external consistency. 60 min (skim sections 2-3).

6. [Split-Brain Prevention in Clusters](https://www.designgurus.io/answers/detail/what-is-a-split-brain-scenario-in-a-distributed-cluster-and-how-can-systems-prevent-or-resolve-it) [S11] — Essential for understanding fencing + witness nodes. 15 min.

7. [Chubby Paper](https://research.google.com/archive/chubby-osdi06.pdf) [S12] — Google's canonical metadata service; predecessor to Spanner. 45 min.

8. [Bounded Staleness Reads](https://github.com/cockroachdb/cockroach/blob/master/docs/RFCS/20210519_bounded_staleness_reads.md) [S19] — Optimization for read latency while maintaining consistency. 20 min.

**Tier 3 (context/reference):**

9. [Quorum Consistency (N, R, W)](https://www.designgurus.io/course-play/grokking-scalable-systems-for-interviews/doc/what-is-quorum-n-r-w-and-why-does-r-w-n-give-strongly-consistent-reads) [S13] — Foundation for understanding replication math. 15 min.

10. [Jepsen Distributed Systems Testing](https://jepsen.io/) [S15] — How to verify linearizability in practice. 20 min (skim homepage + one case study).

11. [MIT 6.5840 Lab 5: Sharded KV](https://pdos.csail.mit.edu/6.824/labs/lab-shard1.html) [S17] — Real coding example of sharded Raft for parallelism. 30 min.

---

## Framing Picks for the Solution

Use these when writing `solution.md`:

**Functional Requirements (list these explicitly):**
- Get, Put, Delete, CAS, List by prefix, Watch/notify, Leases/TTL
- Multi-key transactions (single-shard via key design; optional 2PC for arbitrary keys)
- Not: full ACID on arbitrary keys, versioned reads, time-travel queries

**Non-Functional Requirements (table in solution):**
- Linearizable writes (external consistency required)
- Read p99 latency: local <10ms, cross-region <50ms (via lease reads)
- Write p99 latency: cross-region <200ms
- RPO 0 (no data loss), RTO <30s
- Availability 99.99%
- Scale: 1B keys, 100k reads/s, 1k writes/s
- Multi-region span: 3-5 regions; survive 1 region loss

**Bad/Good/Great Ladder (pick one ladder for solution):**
- **Write path ladder:** single-region async -> single global Raft -> sharded Raft with regional leaders
- **Read path ladder:** always leader -> lease reads -> bounded-staleness follower reads
- **Region loss ladder:** manual failover -> automatic election -> witness/fencing
- **Transaction ladder:** none -> single-shard -> 2PC over Raft

**Expected solution depth (staff level):**
1. Data model: ER diagram or schema (keys, values, revision numbers)
2. Architecture: flowchart showing regions, Raft groups, witness/lease server
3. Write flow: client -> shard leader -> quorum replication -> response (specify latency at each step)
4. Read flow: client options (leader read vs lease read vs bounded-staleness)
5. Region loss: explicit failure scenario + fencing/witness mechanism
6. Transactions: which keys map to which shard; single-shard atomicity via Raft log
7. Bottlenecks: identify hot shard, quorum latency cross-region, leader election time
8. Trade-offs: table comparing (latency, consistency, complexity) for 3 designs (single-region, single global Raft, sharded Raft)
9. Operability: metrics (replication lag, leader election time, write p99), alerts (quorum loss, lease expiry)

**Follow-up readiness:**
Have answers prepped for: why not single global leader, how does follower know if fresh, clock drift risk, region loss second-by-second, old leader fencing, create-if-absent atomicity, prefix scan without blocking, hot shard handling, adding a region, migration from Postgres, SLO alerts, Jepsen testing, avoid DynamoDB LWW, Kafka vs consensus.


---

## Spot-check corrections (2026-09-17)

| Claim in this survey | Checked against | Verdict |
|---|---|---|
| S19 `https://github.com/cockroachdb/docs/RFCS/20210519_bounded_staleness_reads.md` | Repository layout | The RFC directory lives in the `cockroachdb/cockroach` repository under `docs/RFCS/`, not in a `cockroachdb/docs` repository. Treat the URL as [unverified]; the bounded-staleness feature itself is documented at https://www.cockroachlabs.com/docs/stable/follower-reads.html |
| NFR pick "cross-region read p99 < 50 ms (via lease reads)" | Azure inter-region latency table | A lease read is served by the leaseholder, so a cross-region linearizable read costs one RTT to the home region: 71 to 94 ms for US to US or US to EU. 50 ms is not achievable for that path. The solution uses follower reads (local) or a read-your-writes token instead, and forwards only true linearizable reads |
| "Follower reads ... 200ms staleness" wherever stated | https://www.cockroachlabs.com/docs/stable/cluster-settings.html | `kv.closed_timestamp.target_duration` default is 3 s; follower reads at least 4.2 s stale |
| Sources S1, S2, S7, S8, S10, S11, S13, S14, S18, S20 (designgurus, systemdesignhandbook) | Allowed by the brief | Secondary sources. Nothing numeric from them is used in `solution.md` |
