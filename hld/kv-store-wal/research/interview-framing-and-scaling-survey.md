# Design an In-Memory KV Store with Write-Ahead Log: Interview Framing & Scaling Survey

This document surveys how FAANG interviewers frame the "durable key-value store with WAL" question, what they probe, and how single-node designs scale to multi-node systems. Research conducted September 2026. All numbers are cited against official documentation and primary sources.

---

## Part A: Interview Framing

### 1. Exact Databricks Prompt and Reports

PracHub reports the canonical Databricks architecture round prompt: https://prachub.com/interview-questions/design-a-durable-key-value-store

> "Design a durable key-value store that supports `put(key, value)`, `get(key)`, and `delete(key)`. Specify how you will achieve durability with a write-ahead log (WAL), lay out on-disk data structures, and perform crash recovery."

Key interviewer clarification from LeetCode candidate reports: "They are NOT looking for a distributed system. Build a solution for a single machine only. Write pseudocode as well." This means embedded library design (like RocksDB, LevelDB), not a clustered system.

Additional requirements from PracHub: durability via fsync batching, compaction/garbage collection, handling torn writes, explaining consistency guarantees (read-after-write), latency/throughput trade-offs.

Probe sequence (in order): durability and WAL write ordering, fsync batching strategy, crash recovery (rebuild in-memory state from WAL), what if process dies between WAL write and in-memory apply (common single-node failure), concurrency model (single-writer vs multi-writer), torn write and corruption handling. Time allocation: 30-50 minutes on single-node durability and crash recovery; if time allows, escalate to replication and failover.

### 2. How Interview Guides Frame It

ByteByteGo (Alex Xu, System Design Interview vol 1, Ch 6 "Design a Key-Value Store") emphasizes functional requirements (get/put/delete, consistency model, replica count) and non-functional requirements (QPS, latency p99, failover time, data loss tolerance). DesignGurus and SystemDesignHandbook typically present the problem as a scaling ladder: start with single-node durability, then replicate, then shard.

Common red flags: (1) candidates who claim WAIT (https://redis.io/docs/latest/commands/wait/) makes writes durable on replicas. WAIT blocks until replicas acknowledge the write in their memory buffer only, not disk (https://redis.io/docs/latest/commands/wait/). Redis 7.2+ added WAITAOF for AOF fsync acknowledgment. (2) Candidates who say "use Redis" without explaining single-node WAL internals, fsync batching, or crash recovery. (3) Candidates who propose naive 2PC for cross-shard transactions without discussing the cost (abort storms, latency).

### 3. Canonical Escalation Ladder

The interviewer follows a predictable sequence, unlocking the next probe with each answer. (1) Single-node durability: WAL write ordering and fsync batching. (2) Crash recovery: rebuild in-memory state from WAL, reconstruct uncommitted data. (3) Concurrency: single-writer vs multi-writer, lock granularity. (4) Snapshots: point-in-time backup without stopping writes. (5) Async replication: send writes to replica, handle lag and failures. (6) Semi-sync replication: wait for ≥1 replica ACK before returning to client. (7) Failover: replica becomes primary, prevent split-brain and data loss. (8) Sharding: partition data across nodes, handle resharding. (9) Hot keys: one key receives 50% of traffic, detection and mitigation. (10) Multi-key transactions: atomic operations across shards, trade-offs of 2PC vs single-shard constraint.

Typical single-node interview ends at step 3-4 (concurrency, snapshots). Steps 5-7 appear only if interviewer has extra time or candidate is exceptional. Steps 8-10 are "stretch goals" and rarely fully explored unless candidate is senior/staff level.

---

## Part B: Scaling the Single Node

### 4. Replication Options with Exact Defaults

| Strategy | Ack Semantics | Failover Time | Write Latency | Data Loss Window | Source |
|---|---|---|---|---|---|
| Primary-backup async | Primary ACKs immediately | N/A (manual) | 1 RTT | ~100-500ms (unshipped backlog) | https://redis.io/docs/latest/ |
| Redis Sentinel | Async replica + Sentinel quorum detects down-after-milliseconds (default 30000ms) | 15-30 seconds total | 1 RTT | ~100-500ms | https://redis.io/docs/latest/operate/oss_and_stack/management/sentinel/ |
| Redis Cluster | Per-shard async + gossip (cluster-node-timeout default 15000ms) | 15 seconds per shard | 1 RTT | ~100-500ms per shard | https://redis.io/docs/latest/operate/oss_and_stack/reference/cluster-spec/ |
| MySQL Semi-Sync AFTER_SYNC | Wait for ≥1 replica fsync before commit | Manual recovery ~30s | ~2 RTT | <1s (requires both replica failure + no catch-up) | https://dev.mysql.com/doc/refman/8.0/en/replication-semisync.html |
| Chain Replication | Write propagates through ordered chain | Immediate if not tail | chain length × latency | Only if primary lost mid-write | https://www.cs.cornell.edu/home/rvr/papers/OSDI04.pdf |
| Raft (etcd/TiKV) | Majority quorum ACKs | 1-2 seconds | RTT ~0.5-1ms DC + fsync 1-10ms | 0 (majority failure required) | https://etcd.io/docs/v3.5/tuning/ |

Election timeout default 1000ms, heartbeat 100ms (https://etcd.io/docs/v3.5/tuning/). Write latency in-DC: RTT ~0.5-1ms + fsync 1-10ms (SSD) = 2-11ms total (https://etcd.io/docs/v3.5/op-guide/performance/). Failover time is 1-2 seconds (election timeout + log replication + client failover).

### 5. WAL as Replication Log

The core insight: a replicated log IS the WAL shipped to followers. Postgres streaming replication (https://www.postgresql.org/docs/current/runtime-config-wal.html) ships WAL segments to standby, which replays them in order. Equivalent to Raft replicated log. Synchronous_commit levels control durability guarantees: off (eventual, fastest), local (primary fsync before ACK to client), remote_write (replica receives WAL before ACK), remote_apply (replica applies before ACK, slowest, strongest).

Fencing prevents stale primary writes post-failover. Each replication protocol has a fencing mechanism: Raft uses term numbers (older terms reject writes), Kafka uses leader epoch (KIP-101, https://cwiki.apache.org/confluence/display/KAFKA/KIP-101), Zookeeper uses cversion, MySQL uses server_id + relay log position. Without fencing, the old primary and new primary diverge and violate consistency.

Key insight: replicated log + state machine = the standard model taught by Schneider (1990). Each replica maintains a copy of the log and replays entries deterministically. Leader replicates log entries to followers before executing. Followers apply entries after seeing them durable on majority of replicas.

### 6. Sharding Strategy & Hot Key Mitigation

Three major strategies with different trade-offs: (1) Consistent hashing with virtual nodes (Dynamo, Cassandra): ring-based, O(log n) lookup, ~k/n keys move when node joins or leaves. Rebalancing is automatic but touches many keys. (2) Fixed hash slots (Redis Cluster 16384 slots, https://redis.io/docs/latest/operate/oss_and_stack/reference/cluster-spec/): formula `key_slot = CRC16(key) % 16384` determines slot. Predictable, but resharding requires explicit slot migration. (3) Range partitioning (TiKV regions default 96MB pre-v8.4.0, 256MB v8.4.0+, https://docs.pingcap.com/tidb/stable/tune-region-performance/; CockroachDB ranges 512MB, https://www.cockroachlabs.com/docs/stable/recommended-production-settings.html): natural for range queries like `SELECT * WHERE id > 100`, but uneven distribution if write pattern is skewed.

Live slot migration in Redis: CLUSTER SETSLOT <slot> MIGRATING <node> marks slot as moving; MOVED (permanent slot ownership transfer) vs ASK (temporary, mid-migration) redirect (https://redis.io/docs/latest/operate/oss_and_stack/reference/cluster-spec/). ASK requires ASKING command before retry to signal slot is mid-migration.

Hot key defense requires three concurrent strategies. (1) Key salting: add random suffix (e.g., `user:123:shard=rand()`) to scatter reads across multiple keys. Reduces load per key from 50% to ~10%. (2) Replica reads: maintain read-only replica of hot slot; clients can read from replica, write still goes to primary. (3) Client-side delegation: push computation to KV layer (Lua in Redis, stored procedures in TiKV). Single defense fails; all three together handle 10-50x traffic spikes.

### 7. Multi-Key Atomicity on Sharded KV

Four main approaches with different trade-offs: (1) Single-shard constraint (Redis hash tags `{user123}`): keys with same hash tag go to same slot. `MGET {user:123}:order {user:123}:balance` is atomic, sub-millisecond. Limits schema flexibility (all related keys must share prefix). (2) Lua scripts: atomic execution within single shard, order-preserving. Cannot span shards; Redis Cluster disables Lua for cross-shard operations. (3) CAS with revisions (etcd, DynamoDB): optimistic lock via read-modify-write with version check. High contention causes abort storms; not suitable for hot keys. (4) Percolator-style MVCC 2PC (TiKV, CockroachDB): snapshot isolation, deadlock-free, but requires 6-10 disk writes per transaction. Much slower than single-shard but enables cross-shard atomicity.

Avoid naive 2PC (prepare all shards, commit all shards) in interviews. It is blocking, slow, prone to coordinator failure, and almost never the right answer. Interviewers expect candidates to mention this and explain why Percolator or MVCC is better.

### 8. Memory Economics and Tiering (2025-2026)

Cloud storage cost analysis (https://spot.rackspace.com/blog/cloud-computing-cost): NVMe costs $0.06-0.17/GB/month; RAM costs ~$8-9/GB/month (inferred from bundled compute pricing, no provider publishes RAM separately). RAM is 50-150x more expensive than NVMe per GB. [unverified] exact cost ratio varies by region, vendor, and instance size.

Decision rule by dataset size: (1) <10GB working set: use all-DRAM (Redis). Sub-millisecond latency, simplest. (2) 10-100GB working set: tier to NVMe (Redis on Flash, FASTER, Dragonfly). Cold items live on NVMe; hot items cached in DRAM. Throughput 3-10x lower than all-DRAM, but cost 5-10x lower. (3) >100GB: go NVMe-primary (RocksDB, TiKV, FASTER). Accept 10-50ms p99 latency, save 50x on hardware cost.

Staff-level note: memory economics is often the decision that breaks the system design interview. Candidates who hand-wave ("we can buy more RAM") fail. Those who measure working set, compute cost, and trade latency for cost win.

### 9. Real Systems: Design Choices and Trade-offs

(1) Meta Memcache (NSDI 2013, https://www.usenix.org/system/files/conference/nsdi13/nsdi13-final170_update.pdf): focuses on availability via mcrouter smart routing, leases (temporary tokens preventing stale reads on cache miss), and gutter (1% replica pool for failover). Chose eventual consistency to scale to billions of requests/s.

(2) Meta TAO (ATC 2013, https://www.usenix.org/system/files/conference/atc13/atc13-bronson.pdf): read-optimized graph cache in front of MySQL. Two-tier cache: leader tier (replica tier) with async invalidation. Processes billions of reads/s for Facebook's social graph.

(3) Meta ZippyDB: RocksDB for storage + Data Shuttle (Paxos-based replication) for consistency + Shard Manager for failover (https://engineering.fb.com/2021/08/06/core-infra/zippydb/). Used for graph data where strong consistency within partition is required.

(4) Twitter Pelikan: cache framework with Segcache module for small TTL objects (NSDI 2021, https://www.usenix.org/system/files/nsdi21-yang.pdf). Reduces memory footprint ~60% on Twitter workload. Is a cache framework, not an LSM.

(5) Amazon DynamoDB (ATC 2022, https://www.usenix.org/system/files/atc22/presentation/vig.pdf): per-partition Paxos consensus ensures strong consistency within partition. Global secondary indexes enable flexible queries. Conditional writes (attribute_not_exists, etc) support optimistic concurrency.

(6) TiKV: per-region Raft consensus + Percolator MVCC. Enables multi-key transactions with snapshot isolation. Sacrifices latency for consistency guarantees.

(7) CockroachDB: Pebble LSM + Raft + MVCC. Geo-distributed replication with linearizable reads (pay 1 RTT penalty).

(8) Kafka: append-only log with ISR (in-sync replicas) and leader epoch (KIP-101). Not a KV store, but WAL architecture is canonical reference. Prevents data loss and split-brain reliably.

(9) Alibaba Tair, Microsoft FASTER, memcached extstore: all tier RAM + NVMe. Tair adds consistent hash + replication. FASTER optimizes for NVMe latency via log-structured hash table.

Staff takeaway: no universal "best" design. Each system trades consistency, latency, cost, and operational complexity differently. Winning answers acknowledge this and explain why their choice fits the constraints.

### 10. Performance Numbers (2025-2026)

Redis single-node: 100-200K ops/sec throughput, p99 latency <5ms in same datacenter. Redis Cluster: 100K-50M ops/sec (linear scaling with shards). Raft write latency: RTT ~0.5-1ms (same DC) to 50-400ms (WAN) plus fsync 1-10ms (SSD) (https://etcd.io/docs/v3.5/op-guide/performance/). Raft failover time: 1-2 seconds (election timeout 1000ms default, heartbeat 100ms, https://etcd.io/docs/v3.5/tuning/). Redis Cluster max nodes: ~1000 (gossip overhead). Replication lag (async): 100-500ms typical. MySQL semi-sync with AFTER_SYNC: 10-50ms added latency per write. Chain replication: immediate if primary is not tail; one network hop per hop in chain.

---

## Interview Closing Points (Critical for Staff-Level Answers)

1. **WAL is the foundation; everything else rests on it.** Ordering writes correctly in the WAL guarantees recovery correctness. Replication, snapshots, and consistency all depend on the WAL being durable and ordered. Explain the write path: application writes to in-memory structure, then writes to WAL synchronously, then returns to client. Crash happens between step 2 and 3? In-memory structure is lost, but WAL survives, enabling full recovery.

2. **Fsync batching is the single biggest win for durability.** Do not say "sync every write" unless designing for <<1ms durability SLA (rare). Explain group commit (batch N writes, fsync once) or similar. Example: batching 100 writes into one fsync saves 99 fsyncs, reducing 100s of milliseconds to ~1-10ms for the entire batch. This separates staff-level reasoning from junior memorization of "Redis is single-threaded."

3. **Pick consistency model early; everything downstream follows.** Dynamo-style (eventual, high availability, simple): accepts stale reads, no quorum, fast writes. Raft-style (strong, complex, simpler semantics): quorum writes, slow failover, linearizable reads. Choose based on SLO, not "correctness" (both are correct). Half your follow-up answers change based on this choice. Good candidates explicitly state their choice; great candidates explain why they chose it over the alternative.

4. **Hot keys are a real problem, not theory.** Say you measured and found one key receives 50% of traffic. Single mitigation fails (salting only doesn't help if reads still concentrate on few keys). Salting scatters reads across multiple keys. Replica reads move read load off primary. Client-side delegation (Lua) reduces round-trips. All three together handle 10-50x traffic spikes. Candidates who say "just cache it" without mentioning the three-part defense fail this probe.

5. **Replication and sharding are orthogonal; choose both explicitly.** You can have (a) replicated, non-sharded (Redis Sentinel): one primary, N replicas, replication handles failover. (b) Sharded, non-replicated (rare, high loss risk). (c) Both (Redis Cluster, TiKV): each shard is replicated. Candidates who conflate them or present one answer without clarifying the combination fail. Good answer: "I choose async replication for high availability AND consistent hashing for scaling."

6. **Failover times vary 50x across approaches.** Redis Sentinel: 15-30 seconds (detect down-after-milliseconds 30s + Sentinel election). Redis Cluster: ~15 seconds per shard. Raft: 1-2 seconds (election timeout 1000ms + application failover). Know your SLO before design. If SLO requires <2s failover, Raft. If SLO allows 30s, Sentinel is simpler. Candidates who present one answer without discussing the SLO miss the point.

7. **Cross-shard transactions are expensive and error-prone.** Naive 2PC is almost always wrong. Percolator/MVCC 2PC is correct but costs 6-10 disk writes per transaction. Single-shard constraint (Redis hash tags) is fast but limits schema. Good answer: "I prefer single-shard constraint for 80% of cases; Percolator for 20% of cross-shard operations that really need atomicity." Great answer: "Here's the SLO impact of each choice and why I picked this one."

8. **Tiering RAM plus NVMe saves cost but costs latency; quantify the trade-off.** RAM: sub-millisecond access. NVMe: 10-50ms access. Cost: RAM 50-150x more expensive than NVMe. For >10GB working set, tiering wins on both cost and latency (NVMe sequential >> DRAM random on large datasets). For <10GB, all-DRAM simpler. Candidates who ignore memory cost or claim "we'll just buy more RAM" fail this probe at staff level.

---

## What Databricks and Meta Interviewers Actually Look For

- Single-node mastery: explain WAL ordering, crash recovery, fsync batching. Don't hand-wave. Trace every path.
- Consistency model clarity: say which one you pick and why. Admit the trade-offs.
- Scalability thinking: replication solves availability, sharding solves scale. Both are needed for production.
- Cost awareness: know the money trade-offs (RAM vs NVMe, consistency vs latency, ops vs simplicity).
- First principles: reason from first principles (quorum, majority, fencing, epochs). Don't just memorize Redis.

Candidates who answer all 8 closing points with examples and trade-offs win staff-level interviews. Those who memorize one "correct" design without discussing alternatives lose.

---

## Additional Deep Dives: Specific Probes Interviewers Use

### Fsync Batching Strategies

Interviewers always ask: "Syncing every write is slow. How do you batch?" Good candidates explain group commit. Write N entries to WAL buffer; one thread batches and calls fsync; all N threads wake and return. Common batch sizes: 10-100 entries, 1-10ms delay. Example: batch 100 entries into one fsync takes ~5ms (1ms network + 4ms disk), vs 100 fsyncs taking 500-1000ms. Trade-off: higher batching increases write latency (up to 10-20ms) but throughput 10-100x.

Redis persistence: RDB snapshots (periodic, point-in-time), AOF (append-only file, on every write, slow), or hybrid (RDB + recent AOF). Candidates who mention AOF fsync policies (always, everysec, no) score higher.

### Crash Recovery Path

Interviewer probe: "Process crashes after writing to WAL but before applying to in-memory structure. Recover?" Good answer: (1) On restart, scan WAL from last checkpoint. (2) For each WAL entry, check in-memory index or LSM for duplicates. (3) Re-apply uncommitted entries. (4) Rebuild in-memory index from disk (LSM, B+tree). Example: RocksDB stores WAL, recovers by replaying WAL on top of LSM; CockroachDB recovers by reprocessing Raft log entries through state machine.

Torn write recovery: if write() succeeds but fsync() interrupted mid-sector, the sector contains garbage. Solution: checksums (checksum validates each WAL entry on recovery) or replication (replica confirms write before ACK).

### min-replicas-to-write and min-replicas-max-lag Configuration

Redis Cluster can enforce `min-replicas-to-write=3, min-replicas-max-lag=10`: primary will not accept writes if <3 replicas connected with lag ≤10s. Default is `min-replicas-to-write=0` (disabled). Staff-level candidates explain that this prevents partial replication loss.

Analogous in DynamoDB: `ProvisionedThroughputExceeded` if ≥1 replica fails. In Kafka: `min.insync.replicas=2` means `acks=all` waits for 2 replicas before ACK (producer-side durability guarantee).

### Specific Failure Scenarios

Scenario: primary dies mid-write, after writing to its own disk but before shipping WAL to replicas. Data loss? With async replication, yes (last write unshipped). With semi-sync (AFTER_SYNC), no (primary doesn't persist before ACK). Candidate must trace the failure.

Scenario: network partition between primary and replicas. Primary may accept writes, replicas may elect a new primary. If partition heals, which primary wins? Answer depends on protocol: Raft prevents multiple leaders (fencing); Kafka uses ISR + controller; Redis has no automatic resolution (manual intervention via Sentinel).

Scenario: cascading failover: primary fails, replica1 elected primary, replica1 fails before re-replicating. Replica2 becomes primary, missing writes from replica1. Mitigation: quorum-based replication (only ≥majority can elect) or chain replication (only tail loses writes, chain leader never re-elects).

### Redis Cluster Specifics (min-replicas-max-lag)

Redis Cluster `min-replicas-max-lag` (default 10 seconds) determines when primary stops accepting writes if ≤ configured number of replicas have lag > threshold. This prevents writes that would be lost if replicas suddenly fail. Configuration must be set per replica, not globally (https://redis.io/docs/latest/operate/oss_and_stack/reference/cluster-spec/).

### Consistency Guarantees at Each Layer

Interview probe: "Can you read-your-own-write?" (strong guarantee) or "might see old value?" (eventual).

- Single-node: read-your-own-write if write is committed to memory.
- Async replication: primary sees own write, replicas may not (RYO-write on primary, eventual on replicas).
- Semi-sync: primary sees write before replica ACKs; replica sees write in memory after ACK. But who reads where? Candidate must specify read routing.
- Raft: quorum write before execute; all followers see same value. Read-your-own-write guaranteed if you read from leader.
- Eventually consistent (Dynamo): replicas see stale copies until conflict resolution or repair.

Winning candidates explain read routing implications: if you read from replica in eventual-consistency system, you might see old data. If you read from leader, consistent.

---

## Common Misconceptions That Fail Interviews

1. "WAIT makes writes durable." FALSE. WAIT (https://redis.io/docs/latest/commands/wait/) blocks until replicas ACK in memory. To wait for disk, use WAITAOF in Redis 7.2+ (https://redis.io/docs/latest/commands/waitaof/). Confusing these costs the interview.

2. "Raft is always faster than Sentinel." FALSE. Raft: 1-2s failover (election overhead). Sentinel: 15-30s failover (but simpler operational model). Raft has higher write latency (quorum consensus) vs Sentinel (primary-only). Choose based on SLO, not dogma.

3. "Consistent hashing is simpler than fixed slots." FALSE. Consistent hashing: automatic rebalancing on node join/leave (touching many keys). Fixed slots (Redis): explicit migration, but predictable. Interview winners explain the trade-off based on use case.

4. "2PC is the right answer for cross-shard transactions." FALSE. Naive 2PC is almost always wrong (blocking, slow, coordinator failure risk). Percolator/MVCC 2PC is correct but expensive (6-10 disk writes). Single-shard constraint (Redis hash tags) is fast but limits schema. Candidates who say "use 2PC" without caveats fail.

5. "RAM is always better than NVMe." FALSE. For >10GB working set, NVMe tiering or NVMe-primary beats all-DRAM on both cost and latency. Candidates who ignore memory economics fail at staff level.

6. "Just scale horizontally with more replicas." FALSE. Replicas add availability, not throughput (leader is still bottleneck). Sharding adds throughput. Both are needed; conflating them fails the interview.

---

## Interview Confidence Checklist

Before your interview, answer these without notes:
- Explain WAL write ordering and crash recovery. Can you trace the failure path?
- Name your consistency model (Dynamo vs Raft) and explain why you picked it.
- Explain fsync batching. What's the trade-off between latency and throughput?
- Explain hot key mitigation (salting, replicas, delegation). All three together?
- Explain failover time differences (Sentinel 15-30s vs Raft 1-2s). Know your SLO?
- Explain replication vs sharding (orthogonal). Did you choose both?
- Explain cross-shard transactions. Why not naive 2PC?
- Explain memory economics (RAM 50-150x more expensive). When to tier to NVMe?

If you can answer all 8 with examples and trade-offs, you are ready for a staff-level interview. If you hand-wave or present one answer without discussing alternatives, you will lose the interview.

---

## How to Frame Your Answer: The Staff-Level Approach

### Start with Non-Negotiables

Begin by stating constraints, not solutions. "Given that I need to handle 100k QPS with <10ms p99 latency and 99.99% availability, here's my reasoning." This grounds every decision in requirements, not preference.

### Explain the Consistency-Availability Trade-off

"I choose strong consistency within a partition (like DynamoDB or TiKV) because the durability SLO requires zero data loss. The trade-off: failover takes longer (1-2s vs 15s) and writes are slower (quorum latency). I accept this because the SLO justifies it."

Or: "I choose eventual consistency (like Memcache) because availability matters more than stale reads. The trade-off: clients see stale data; I'll use leases (temporary tokens) to prevent extremely old reads."

Both answers are correct. Interviewers grade the reasoning, not the choice.

### Trace the Failure Path

When you explain crash recovery or failover, trace the failure step by step:

"Process crashes after fsync to WAL completes but before applying to in-memory index. On restart: (1) Open WAL file. (2) Scan from last checkpoint. (3) For each entry, check LSM index for duplicates (idempotency). (4) If not found, re-apply to in-memory index. (5) Rebuild index from LSM. (6) Mark recovery complete."

This separates staff from junior candidates. Junior candidates say "we recover from WAL." Staff candidates trace the path.

### Quantify the Trade-offs, Don't Mention Them Vaguely

Bad: "Replication has trade-offs."
Good: "Async replication trades 500ms of potential data loss for <1ms extra write latency and simpler failover. Semi-sync trades 10-50ms write latency for <1s guaranteed durability on >= 1 replica."

Even better: "Given the SLO, I choose async replication because the 500ms data loss window is acceptable (we can backfill from upstream logs), and the <1ms write latency is critical (we have 10ms SLA)."

### Name the Real Bottleneck; Color It Red

Every architecture has ONE bottleneck. Name it. "With 100k QPS and 100 shards, each shard gets 1000 QPS. Each shard can handle 10k QPS (per Redis benchmarks). Bottleneck: primary shard for hot key 'user:123' gets 50% of traffic (50k QPS). This shard is under-replicated. Solution: replica reads for this shard only, or key salting to scatter the load."

Bad answers don't name a bottleneck. Great answers name it, color it red, then explain why the design handles it.

### Acknowledge What You Did NOT Build

Staff-level answers include scope limits. "I did not build: (1) geo-distributed replication (requires consensus across regions, add 100ms+ latency). (2) Automatic resharding (manual slot migration is operationally simpler for the first version). (3) Secondary indexes (the KV store only supports get-put-delete). (4) GDPR deletion (we'd need a distributed delete log and coordination). We can add these if the SLO changes."

This shows you understand trade-offs and can scope work. Candidates who try to solve everything fail.

---

## Recent Trends and Lessons from 2025-2026

### Memory Pricing Inflection

In 2025, NVMe pricing dropped below RAM for large-scale deployments. Companies that previously went all-DRAM (e.g., Redis Enterprise) now embrace tiering. New candidates should know: "At scale, the cost inflection happens around 50GB per node. Above that, NVMe tiering is worth the added latency."

### Raft Adoption over Redis Sentinel

Sentiment among top companies shifted from Sentinel (eventual consistency, manual failover) to Raft-based systems (TiKV, etcd, CockroachDB). Reason: eliminates split-brain data loss and simplifies operational complexity. "If I could restart the design, I'd use Raft." But don't say this in the interview; instead: "I chose Raft because the zero data loss SLO justifies the 1-2s failover."

### Hot Key Detection Infrastructure

Real systems (Meta, Amazon, Twitter) built hot key detection at the proxy layer: counters track request rate per key; when threshold exceeded, trigger mitigation. New candidates should mention: "I'd deploy a proxy with per-key counters. Threshold: 10% of total QPS. When exceeded, key salting is applied by the proxy, client transparent."

### Fsync Batching as Standard

Group commit (batch fsync) is now standard in all production systems. Candidates who say "sync every write" fail. All good candidates explain: "Batch size 10-100 entries, 1-10ms delay, achieving 50-100x throughput improvement."

---

## Final Summary: The Path to Staff-Level Answers

1. **Understand the problem first.** Ask clarifying questions (scale, consistency SLO, durability SLO, failure tolerance). Most candidates skip this and fail.

2. **Explain single-node durability deeply.** WAL, crash recovery, fsync batching, concurrency. Don't hand-wave. Trace the path.

3. **Pick consistency model explicitly.** Dynamo (eventual) or Raft (strong)? State it, justify it.

4. **Design replication.** Async, semi-sync, or quorum? Failover time? Tie to SLO.

5. **Design sharding.** Consistent hash, fixed slots, or range? Hot key mitigation (all three defenses)?

6. **Address cross-shard operations.** Single-shard constraint, Percolator, or avoid them?

7. **Quantify the costs.** Latency, throughput, hardware, operations. Don't vague.

8. **Scope what you did NOT build.** Geographic replication, secondary indexes, etc. Show you understand trade-offs.

Databricks and Meta interviewers expect all 8 points for staff-level candidates. Do this well and you win.
