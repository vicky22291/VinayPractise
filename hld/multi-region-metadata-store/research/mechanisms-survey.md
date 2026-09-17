# Mechanisms Survey: Multi-Region Metadata Store with Linearizable Writes

**Purpose**: Staff-level interview prep on consensus, consistency, and clock-based read optimization for a multi-region metadata store (Databricks, Google-scale).

---

## Sources Reference Table

| ID | URL | What it establishes |
|---|---|---|
| L1 | https://dl.acm.org/doi/10.1145/78969.78972 | Herlihy-Wing 1990 ACM TOPLAS: linearizability foundational definition for concurrent correctness |
| L2 | https://jepsen.io/consistency | Jepsen consistency models: comprehensive safety property reference and formal framework |
| L3 | https://aphyr.com/posts/313-strong-consistency-models | Kyle Kingsbury: linearizability as atomic operation visibility between invocation and completion |
| L4 | https://aphyr.com/posts/333-serializability-linearizability-and-locality | Kingsbury: serializability vs linearizability distinction; strict serializable = serializable + real-time |
| Q1 | https://www.usenix.org/system/files/conference/atc14/atc14-paper-ongaro.pdf | Raft ATC 2014: quorum-based leader election and log replication (Best Paper) |
| Q2 | https://raft.github.io/ | Official Raft documentation and interactive consensus visualizations |
| Q3 | https://arxiv.org/abs/1608.06696 | Flexible Paxos 2016 (Howard): phase 1 and phase 2 quorums need only intersect, not be identical |
| Q4 | https://lamport.azurewebsites.net/pubs/paxos-simple.pdf | Paxos Made Simple 2001 (Lamport): prepare and propose phases with stable acceptor storage |
| Q5 | https://research.google/pubs/large-scale-incremental-processing-using-distributed-transactions-and-notifications/ | Percolator OSDI 2010 (Peng & Dabek): 2PC with Timestamp Oracle, 2-5 second avg latency |
| LP1 | https://www.cockroachlabs.com/blog/distributed-database-leader-leases/ | CockroachDB 2026 SIGMOD: leader leases protocol, 85% CPU reduction at scale |
| LP2 | https://www.cockroachlabs.com/blog/clock-management-cockroachdb/ | CockroachDB clock management: leaseholder holds periodic lease; shutdown if drift >80% max-offset |
| RP1 | https://zookeeper.apache.org/doc/r3.7.2/zookeeperOver.html | ZooKeeper: reads are NOT linearizable; sync() forces quorum operation for consistency |
| RP2 | https://www.cockroachlabs.com/docs/stable/advanced-changefeed-configuration | CockroachDB closed timestamp: lagged by kv.closed_timestamp.target_duration (200ms default) |
| RP3 | https://www.cockroachlabs.com/blog/follower-reads-stale-data/ | CockroachDB follower reads: any replica serves read at timestamp ≤ closed timestamp |
| C1 | https://www.cockroachlabs.com/blog/clock-management-cockroachdb/ | CockroachDB max-offset: 500ms default, 250ms multi-region recommended, 80% shutdown threshold |
| C2 | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configure-ec2-ntp.html | AWS Time Sync Service: satellite + atomic clocks, 169.254.169.123 (local VPC), leaps smeared |
| C3 | https://aws.amazon.com/blogs/aws/keeping-time-with-amazon-time-sync-service/ | AWS Time Sync: redundant atomic clocks, no charge, globally available |
| WAN1 | https://etcd.io/docs/v3.6/op-guide/configuration/ | etcd: --election-timeout 1000ms default, --heartbeat-interval 100ms, both tunable |
| WAN2 | https://etcd.io/docs/v3.5/faq/ | etcd FAQ: election-timeout ≥10x RTT; US continental ~130ms, US-Japan ~350-400ms RTT |
| WAN3 | https://github.com/etcd-io/etcd/pull/9352 | etcd pre-vote: candidate sends pre-vote before term increment, prevents disruptive elections |
| TSX1 | https://www.pingcap.com/blog/distributed-transactions-tidb/ | TiKV: Percolator model with Timestamp Oracle, 2PC + MVCC, globally unique timestamps |
| TSX2 | https://www.pingcap.com/blog/how-tikv-reads-and-writes/ | TiKV: startTS and commitTS from TSO, snapshot isolation via optimized 2PC |
| SM1 | https://docs.pingcap.com/tidb/stable/tune-region-performance/ | TiKV v8.4.0: region size 256 MiB (was 96 MiB), split threshold 384 MiB, merge 54 MiB |
| SM2 | https://docs.pingcap.com/tidb/stable/tikv-configuration-file/ | TiKV: coprocessor.region-split-size parameter, default 256 MiB, tunable per workload |
| EC1 | https://dl.acm.org/doi/10.1145/2517349.2517350 | EPaxos SOSP 2013: leaderless, 1 round common case, 2 rounds worst, load-balances across replicas |
| NUM1 | https://www.usenix.org/system/files/conference/osdi12/osdi12-final-16.pdf | Spanner OSDI 2012: 5ms commit wait, 9ms Paxos latency, TrueTime ε p99 <4ms, p999 <10ms |
| NUM2 | https://aws.amazon.com/blogs/networking-and-content-delivery/network-latency-concepts-and-best-practices-for-a-resilient-architecture/ | AWS networking: inter-region latency 0-160ms, use Network Manager Infrastructure Performance for real-time |
| NUM3 | https://www.cockroachlabs.com/docs/stable/recommended-production-settings | CockroachDB: 500ms default max-offset, 250ms multi-region, closed_timestamp 200ms default |
| NUM4 | https://docs.mongodb.com/manual/core/replica-set-members/ | MongoDB: arbiter (witness) members for cost; PSA risky for sharded; max 50 members, 7 voting |
| NUM5 | https://martin.kleppmann.com/ | Martin Kleppmann: author of "Designing Data-Intensive Applications", expert on consistency and trade-offs |
| NUM6 | https://docs.cockroachlabs.com/docs/v26.2/advanced-changefeed-configuration | CockroachDB v26.2: kv.closed_timestamp.target_duration 200ms, tunable for latency vs overhead |

---

## 1. Linearizability vs Sequential vs Serializable vs Strict Serializable

**Definition**: Linearizability (Herlihy-Wing, [L1]) is the strongest single-object consistency model. Each operation appears to execute atomically at some real-time point between its invocation and completion ([L3]). For metadata store writes, linearizable compare-and-swap on a version or create-if-absent on a name guarantees: if writer A completes before writer B starts (real-time), B sees A's change.

Sequential consistency relaxes real-time order: operations preserve program order per-thread but global order is not tied to real-time. Serializability orders transactions but does NOT require real-time correspondence; a transaction completed hours ago may appear after one invoked later. Strict serializable combines both: transactional isolation plus real-time ordering ([L4]).

**Guarantee**: Linearizable write: once write returns, all subsequent reads observe that write. No version confusion. No create-if-absent races.

**Failure mode**: Clock skew breaks this without bounded clock uncertainty. If a server's clock jumps backward, later writes might appear earlier than earlier writes. A client that receives write ACK at time T1 then reads at time T0 (clock jumped back) may see data not yet committed. The metadata store must prevent this by enforcing write ≥ read timestamp invariant or rejecting reads before confirmed timestamps.

**For metadata store**: Linearizable writes are necessary for correctness on unique keys (tenant names, namespace creation, version updates). Sequential consistency is insufficient due to rename races. Example: tenant A renames namespace from "x" to "y", then immediately reads back its own write. Sequential consistency allows a follower replica to see "y" but then return to "x" on a later read from a different follower, causing the rename to appear to rollback. Linearizability prevents this phantom rollback.

---

## 2. Quorum Arithmetic Across Regions

**Quorum rule**: In Raft ([Q1], [Q2]), a leader must replicate to a majority of the N peers. With 3 replicas in 3 regions (1 per region), one region loss = no quorum (need 2/3). With 5 replicas in 3 regions (2+2+1), one region loss = alive (2+2=4 > 2 of 5).

**Flexible Paxos** ([Q3]): Phase 1 (prepare) quorum and Phase 2 (propose) quorum must intersect but need not be identical. If Phase 1 quorum is 2 of 5 and Phase 2 quorum is 3 of 5, they intersect on at least 1 node, preserving safety. Allows smaller Phase 2 quorum for latency: commit only to 2 replicas if prepare touched 4.

**Witness replicas** ([NUM4]): MongoDB arbiter and CockroachDB witness replica participate in leader election but do not store data. Reduces replication overhead on large datasets. PSA (Primary-Secondary-Arbiter) in sharded clusters risks quorum loss if primary and secondary both down. A witness replica that crashes and recovers still votes in leader election, but must not be chosen as the new leader (Raft safeguard). Use witnesses for read-heavy, write-rare metadata: election participation without storage cost.

**Cross-region RTT cost**: 5 replicas in 3 regions (2+2+1) requires writing to 3 nodes (majority). If majority spans two regions, commit needs two cross-region round trips (~130ms us-east to us-west, ~250ms us to eu-west [WAN2]). One RTT per Raft round. Practical: a commit that goes to replicas in regions A, B, C as [A, B] majority requires 1 RTT (A responds, B responds, wait). But if A and B are in different regions, that is 1 cross-region RTT (~130ms). With Flexible Paxos, if phase 1 touches all 5 nodes and phase 2 only needs 2 (A+B), the prepare overhead is only 1 cross-region RTT but commit is 1 RTT locally.

**Failure mode**: One region failure with 3-3-3 split = no quorum. With 2-2-1 and loss of the heavy region (2), the remaining 2 cannot form quorum.

---

## 3. Leader Placement and Leader Leases

**Raft leader vs leaseholder** ([LP1], [LP2]): Raft designates a leader for log replication and election timeout management. A separate leaseholder can be designated per range to serve reads without going to the Raft leader. CockroachDB's 2026 protocol reduced CPU by 85% at scale via optimized lease maintenance.

**Lease mechanism**: A leaseholder holds a time-based or epoch-based lease from a quorum. Clock-based leases assume bounded clock skew (e.g., max-offset [C1]). Epoch-based leases rely on liveness: leader pings followers, followers increment epoch; if epoch stops advancing, lease is revoked. CockroachDB uses a hybrid: periodic lease grant with clock uncertainty bounds.

**Lease transfer cost**: Transferring leadership to the home region (e.g., primary to a local replica) incurs one round-trip to revoke the old lease and one to grant the new lease. With preference settings, the lease naturally transfers to the home region over time as the default lease holder. CockroachDB's lease preferencing allows specifying a tier (e.g., prefer home region replicas), so lease migration happens passively over hours or days without manual intervention. Manual transfer via `admin` commands is an emergency tool.

**Leader lease read optimization** ([RP2], [RP3]): If the leaseholder holds an unexpired lease from a quorum, reads do not require a round trip. The leaseholder serves directly, using closed timestamp to ensure reads do not violate causality. Default lag: 200ms ([C1]). Edge case: if the lease holder's clock jumps forward by >max-offset, it incorrectly believes its lease is still valid. A client connecting to that replica reads uncommitted data. CockroachDB's clock-jump detection (80% threshold [LP2]) prevents this by shutting down before the clock skew becomes dangerous.

**Failure mode**: A partitioned node with an expired lease may still believe it holds the lease if its clock has jumped forward. Shutdown threshold at 80% of max-offset prevents this ([LP2]).

---

## 4. Read Paths: Consistency and Latency Trade-offs

**ZooKeeper sync-then-read** ([RP1]): A read operation by default returns possibly stale data (sequential consistency). sync() blocks until the client's read is issued on a quorum-confirmed state, achieving linearizability. Cost: one full quorum round trip per read.

**CockroachDB closed timestamp with follower reads** ([RP2], [RP3]): Closed timestamp is the point below which no new writes will be introduced, lagged by kv.closed_timestamp.target_duration (200ms default [NUM3]). Any replica can serve reads at timestamp ≤ closed timestamp without leaseholder round trip. Latency: replica lookup + disk read, no WAN round trip.

**Spanner reads at a timestamp with commit-wait** ([NUM1]): Client specifies a read timestamp. Spanner waits until TrueTime.now().latest > timestamp, then serves. TrueTime epsilon (p99 <4ms, p999 <10ms) bounds uncertainty. Commit-wait (~5ms) ensures a write's timestamp is past all clients' clocks. Cost: latency = epsilon + network RTT + disk.

**ReadIndex (Raft heartbeat round)** ([Q1]): A Raft follower can serve reads by verifying the current leader is still alive. Leader sends a heartbeat to quorum, follower waits for confirmation, then serves from its state machine. Latency: one RTT to leader (~1-5ms local, ~130ms cross-region) plus disk read. Linearizable but slower than lease-based reads. Practical use: when a follower is known to be up-to-date (e.g., after a write to this follower) and we want to ensure linearizability without maintaining leases per follower.

**Failure mode**: Closed timestamp lag means follower reads may be up to 200ms stale. Spanner's TrueTime assumes bounded clock skew globally; clock jump breaks it. ReadIndex assumes leader is not partitioned (a partitioned leader would not send valid heartbeats, so follower detects stale leader after 2x heartbeat interval, typically 200ms). Follower reads at a timestamp require that timestamp to be ≤ closed timestamp, which is computed by the leader; if the follower is in a different region from the leader, the closed timestamp may lag by inter-region RTT + processing time.

---

## 5. Clocks: Drift, NTP, TrueTime, and HLC

**Clock skew bounds**: NTP over WAN typically drifts 100-500ms per day; with good hardware and frequent corrections it can be <50ms. CockroachDB's max-offset (500ms default, 250ms recommended for multi-region [C1]) sets the clock uncertainty interval. Reads at timestamp T are considered uncertain if the local clock could be off by max-offset. If node A's clock is ahead of node B's by max-offset, a write on A at time T and a read on B at time T-1 could violate causality. Preventing this requires either: (a) bounded clock skew via max-offset, (b) waiting epsilon before serving (Spanner), or (c) hybrid logical clocks.

**AWS Time Sync Service** ([C2], [C3]): Satellite + atomic clocks per region, no charge, available at 169.254.169.123 (local VPC, direct from Hypervisor) or time.aws.com (public). Leaps smeared over 24 hours, not inserted suddenly. Reduces skew to <1ms from Hypervisor, typically achieves <100 microseconds from a node within a region. Beats NTP for distributed systems: no network variable latency, synchronous delivery.

**TrueTime (Spanner)** ([NUM1]): Atomic clocks + GPS in datacenters, epsilon = max error (p99 <4ms, p999 <10ms). Commit-wait = epsilon ensures a write's timestamp is visible to all clients before they read later. Enables reads without consistency checks.

**Hybrid Logical Clocks (HLC)**: Combines wall-clock and logical clocks. Detected clock skew increments logical component. Tolerates limited clock backward jumps without breaking causality. Used to avoid shutdown on small skew.

**Why wall clocks alone fail**: If a write at time T completes, then a read at time T-1 occurs before the read physically happened, violating real-time ordering. Bounded clock skew (via max-offset) or TrueTime epsilon prevents this. CockroachDB shuts down if skew exceeds 80% of max-offset ([LP2]).

---

## 6. Cross-Region Election and Failover

**Election timeout tuning** ([WAN1], [WAN2]): etcd default election timeout is 1000ms, heartbeat interval 100ms. For WAN, election timeout should be ≥10x RTT. US continental RTT ~130ms, so timeout ≥1300ms. US-Japan RTT ~350-400ms, so timeout ≥3500ms. Long timeouts reduce disruptive elections but delay failover.

**Pre-vote mechanism** ([WAN3]): Raft candidate sends a pre-vote request before incrementing its term. If pre-vote fails (no quorum), candidate does not disrupt the leader's term. Reduces split-brain elections from partitioned followers.

**Region loss detection and re-election time**: With election timeout 3500ms (US-Japan), after a region failure, the surviving region must wait up to 3500ms before a new leader is elected. No writes are committed during this window. Detection happens when: (a) leader is in lost region (followers stop receiving heartbeats, timeout fires after ~3.5s), or (b) leader is in survivor region and it detects loss of quorum majority (it cannot confirm writes to lost region replicas, so it steps down after heartbeat timeout, another replica in survivor region becomes leader). Worst case: 3.5s, typical: 1-2s after a graceful region partition.

**Stale leader problem**: A leader in a lost region continues serving reads from its cache if it has not detected the partition yet. It believes it still has quorum (its own vote + cached replica responses) for up to heartbeat interval (~500ms on WAN). Clients reading from this stale leader see outdated metadata (a tenant or namespace deleted 1s ago appears to exist). Fencing with leases prevents this: if a leaseholder cannot renew its lease (quorum is lost), it knows it is no longer authoritative and rejects reads. The leaseholder must actively check quorum before serving reads: send heartbeat, wait for majority response before read. Cost: 1 RTT per read, defeating the local-read optimization.

**Failure mode**: Long election timeouts delay failover. Short timeouts cause frequent re-elections under high latency. Partitioned leaders cause brief inconsistency if clients retry writes before detecting the partition.

---

## 7. Multi-Shard Transactions Over Consensus Groups

**2PC with Timestamp Oracle** ([Q5], [TSX1], [TSX2]): Coordinator writes an intent on each participant shard (each shard is a Raft group). Timestamp Oracle (TSO) allocates a global commit timestamp. Coordinator writes a transaction record to its own Raft group (also replicated). Participants then apply the committed timestamp. Average latency: 2-5 seconds per Percolator [Q5].

**CockroachDB parallel commits** ([LP1]): Coordinator can consider a transaction committed once it has written the transaction record to its own shard AND replicated intents to a quorum of participants. Reduces latency by parallelizing replication across participants. One round trip for intents + one for own shard record = ~130ms (2 RTTs us-east to us-west).

**Coordinator's state must be replicated**: The transaction record must survive coordinator failure. If the coordinator crashes after replicated write but before commit, any participant can read the transaction record and complete the commit. This is why the coordinator's state is itself a Raft group ([TSX1]).

**Write-intent pattern**: Before committing, coordinator writes a "lock" or "intent" on each key. Readers must check intents and wait for transaction completion (via polling or notifications). Allows non-blocking participant writes: participant replicas can apply the write immediately at the intent, readers just block on timestamp. Intents are self-cleaning: a reader older than the intent timeout clears it and returns "committed or aborted" based on the transaction record.

**Write-intent recovery**: If the coordinator crashes after writing intents but before committing, any participant can read the coordinator's transaction record (itself replicated on the coordinator's Raft group) and apply the commit timestamp if the transaction record says committed, or clean up the intent if aborted. No orphaned locks: the transaction record is durable before the coordinator ACKs the client.

**Failure mode**: Coordinator failure during prepare requires intent cleanup. Long-running transactions hold locks, blocking later readers. Multi-region coordination incurs 2+ RTTs per commit: 1 RTT to gather startTS from TSO (Timestamp Oracle), 1+ RTTs to replicate intents and transaction record to quorum of each participant, 1 RTT to read commit result. Parallel commits ([LP1]) reduce this to 1-2 RTTs by pipelining intent replication with coordinator record write.

---

## 8. Sharding Metadata

**Range-based partitioning with auto-split** ([SM1], [SM2]): TiKV uses 256 MiB default region size (v8.4.0, increased from 96 MiB). Splits at 384 MiB, merges at 54 MiB. Smaller regions = more overhead (meta ranges, election traffic). Larger regions = longer recovery after node failure. Never exceed 1 GiB.

**Directory / placement service** ([NUM1]): Spanner maintains a directory of range -> replicas mappings. Each directory is itself replicated. Client caches directory locally, reducing lookups. On split, directory is updated atomically with the new range's metadata.

**Geo-partitioning and home region**: Databases like CockroachDB allow `REGIONAL BY ROW` syntax to partition by geography. A tenant or namespace is pinned to its home region, making its leader placement preference automatic. Avoids cross-region coordination for tenant-scoped operations.

**Hot shards in metadata**: A tenant with millions of tables causes metadata range to hot-spot. Example: a 1GB metadata shard with 100M tables, each entry 10 bytes, causes 1M reads/sec on that shard if listing operations scan the table index. Solutions: (1) split by table ID hash into sub-ranges (e.g., 100 ranges of 1M tables each), (2) use secondary indexes (tenant ID + table ID) with a separate index range, (3) cache frequently-accessed table lists (namespace listing) in a memcached layer outside the consensus store. Option (3) trades consistency for latency: cache is eventually consistent, listings may omit newly-created tables for seconds.

**Metadata split atomicity**: Spanner's directory splitting is atomic at the metadata level but not at the replica placement level. A directory split is first replicated on the master (metadata) range, then each child directory is assigned replicas independently. If a region failure occurs between directory split write and replica assignment, the new directory has no replicas in the affected region. Failover assigns a new replica. Cost: temporary unavailability (seconds) while new replica catches up.

**Failure mode**: One region failure during split leaves metadata inconsistent. Atomic metadata updates via Raft prevent split metadata from appearing without both child ranges initialized. Large regions delay failover (recovery time = time to replay region's log, typically 30s-2min for 256MB region with many small entries). Use WAL (write-ahead log) prefetching on replicas to reduce replay time on failover.

---

## 9. Alternatives to a Leader: EPaxos and Leaderless

**EPaxos (Egalitarian Paxos)** ([EC1]): Leaderless consensus where any replica can propose. Commits in 1 round in the common case (no conflicts), 2 rounds worst case. Tracks dependencies between commands to handle concurrent proposals. Load balances across all replicas.

**Why production rarely ships it**: EPaxos requires dependency tracking and careful causal ordering. Latency advantage (1 round vs 2 in Raft) is marginal for metadata stores (100ms is acceptable). Operational complexity is high: debugging consensus issues without a stable leader is harder.

**Multi-leader with Last-Writer-Wins (Dynamo, Cosmos DB)**: Each region accepts writes independently with local timestamps or vector clocks. Conflicts resolved by LWW: later timestamp wins. NOT linearizable. create-if-absent races: both regions may create the same namespace with different timestamps, later one overwrites (data loss or inconsistency).

**CRDTs unsuitable for metadata**: Conflict-free replicated data types (CRDTs) resolve conflicts automatically but via commutativity (union, add, remove). For create-if-absent on a name, no CRDT semantics ensure the first creator is canonical. LWW CRDTs lose the creator's identity.

**Recommendation**: Stick with a leader. Simplicity, debuggability, and strict semantics outweigh leaderless latency gains for metadata stores.

---

## 10. Practical Trade-offs: Configuration Scenarios

**Scenario A: Low-latency single region (same-AZ metadata)**: 3 replicas in same AZ, heartbeat 50ms, election timeout 300ms. Commit latency: 5ms. Reads: 0ms (leaseholder cached). Tradeoff: zero availability on AZ failure, cross-region failover is manual.

**Scenario B: High-availability multi-region (3 regions, 1 replica each)**: 5 replicas (3 main + 2 witnesses in 2 backup regions), heartbeat 500ms, election timeout 5s. Commit latency: ~130ms (cross-region write). Reads: 200ms lag (closed timestamp, follower reads). Tradeoff: slower commits, but survives one full region failure and automatic failover.

**Scenario C: Write-latency optimized (home region leader, remote replicas)**: Leader in region A, replicas in B and C. Use Flexible Paxos: phase 1 quorum = 3 (all), phase 2 quorum = 2 (A + B only). Commits only to A and B (~130ms RTT to B), C lags by ~heartbeat interval. Tradeoff: if A and B both fail, C cannot form quorum; must manually promote C (data loss risk). Suitable for asymmetric deployments where region A is critical.

---

## 11. Numbers: Latencies, RTTs, and Configuration Defaults

**Inter-region round-trip times** ([WAN2]): AWS: US East to US West ~130ms P50 (P99 ~150-200ms), US East to EU West ~140-150ms P50, US East to AP Southeast ~230-250ms P50, US to AU ~300-350ms P50. Measurement via AWS Network Manager Infrastructure Performance tool (real-time, not guess), also cloudping.co for GCP. Variability is high on WAN; P99 is 1.2-1.5x P50. Plan for P99 latencies in SLO calculations.

**Raft commit latency** ([Q1]): Inside a datacenter with 3 replicas on fast storage, commit is 1 RTT to quorum. Latency = network round trip (microseconds) + fsync to replicas (1-5ms on SSD, 10-50ms on HDD). Typical: 5ms for 3-replica group in same AZ. Across regions with 3 replicas in 3 regions (1 per region), commit requires cross-region RTT to majority (e.g., 2 regions). Cost: ~130ms (2-region) + fsync time. With Raft pipelining (overlapping prepare/propose), commit cost is 1 cross-region RTT, not 2.

**Spanner latencies** ([NUM1]): Commit-wait ~5ms, Paxos latency ~9ms (1-replica experiments measured in single region). Multi-region Spanner adds cross-region RTT: 2-region config is Paxos latency (~9ms) + commit-wait (5ms) + 1 cross-region RTT (~130ms) = ~144ms for linearizable write. TrueTime epsilon p99 <4ms ensures timestamp visibility across globe; p999 <10ms bounds worst-case wait time. Commit-wait is necessary because local clients' clocks may be ahead of a remote replica's clock by up to epsilon.

**CockroachDB defaults** ([C1], [NUM3], [NUM6]): max-offset 500ms default (250ms multi-region recommended), kv.closed_timestamp.target_duration 200ms default (increase to 5s to reduce write backpressure on metadata leader), election timeout 1000ms (increase to 3000ms+ for WAN), heartbeat interval 100ms (increase to 500ms for WAN). Multi-region configuration: election timeout = max(3s, 10x avg inter-region RTT), heartbeat interval = election timeout / 10. Example: US to EU (130ms RTT): heartbeat 300ms, election 3s.

**etcd guidance** ([WAN2]): election-timeout should be ≥10x RTT. US continental ~130ms, so ≥1300ms. US-Japan ~350ms, so ≥3500ms. Longer timeout = lower false positives, slower failover.

**TiKV region size** ([SM1]): 256 MiB default (v8.4.0), split threshold 384 MiB, merge threshold 54 MiB. Aim for hundreds of thousands of regions per cluster. Small regions (64 MiB) increase Raft traffic (more leader elections on failure) and meta range load (more entries in PD). Large regions (1 GB+) increase recovery time after failure and cause hotspot skew for uneven workloads.

**Timestamp Oracle (TSO) throughput** ([TSX1]): Google Percolator design allocates timestamps from a centralized TSO. TiKV PD (Placement Driver) serves as TSO. Single region throughput: ~1M timestamps per second from a single PD leader (typical). Multi-region: each region has a local PD, they synchronize via Raft to maintain globally monotonic timestamps. Cost: every write waits for a remote round trip to TSO (~10-50ms), serialized on one leader.

**Lease grant frequency** ([LP1]): Leases are renewed periodically, typically every 1-2 seconds. Each renewal is a Raft write to the leaseholder's range. At high metadata write rate (>1k writes/sec), lease renewal overhead becomes noticeable. CockroachDB batches lease renewals and uses adaptive lease lengths (longer leases if low write contention, shorter if high).

---

## 12. Clock Skew Failure Recovery

**Symptom**: Metadata updates appear to go backward in time, or linearizability is violated. A read returns data older than a write that preceded it. Replicas in different regions have clocks that differ by >max-offset, causing timestamp ordering to flip.

**Detection**: Monitor clock skew per node. CockroachDB logs and alerts when a node detects drift >60% of max-offset. If skew approaches 100% (approaching max-offset), that node shuts down gracefully to prevent metadata corruption.

**Recovery**: (1) Identify the node with the wrong clock (lagging or jumping ahead). (2) Do NOT manually set the clock backward (breaks monotonicity). (3) Allow the node to catch up via NTP or Time Sync Service (forward correction), or restart the node after NTP is fixed. (4) Temporarily reduce max-offset to prevent other nodes from drifting as far (e.g., from 500ms to 250ms), then investigate root cause (NTP misconfiguration, hardware clock battery, Hypervisor time sync).

**Impact**: Zero metadata writes during clock-jump detection (up to 1 second). Clients see `UNAVAILABLE` error. Follower reads remain available (bounded by closed timestamp lag). Manually restarting an affected node takes 30-60 seconds to rejoin the cluster.

---

## Mechanism Picks for the Interview Design

1. **Linearizability model**: Non-negotiable for metadata. Define as Herlihy-Wing: atomic visibility between invocation and completion ([L1]).

2. **Quorum layout**: 5 replicas across 3 regions (2+2+1) or 5 regions (1 per region + 2 for quorum). Survives one region failure. Explain majority intersects in Flexible Paxos phase design ([Q3]).

3. **Leader placement**: Raft leader for log replication. Separate leaseholder per range, pinned to home region via preference. Reduces cross-region RPCs for local reads ([LP1]).

4. **Read optimization**: Closed timestamps + follower reads for bounded-staleness queries (200ms lag default). Leaseholder reads for strong consistency, no round trip if lease is fresh ([RP2], [RP3]).

5. **Clock management**: AWS Time Sync Service (atomic clocks per region, no charge). CockroachDB's max-offset of 250ms for multi-region. Shutdown on skew >80% of bound ([C1]).

6. **Election tuning**: election-timeout ≥10x inter-region RTT. US continental ≥1.3s, US-Japan ≥3.5s. Use pre-vote to reduce false elections ([WAN1], [WAN3]).

7. **Transactions**: 2PC with Timestamp Oracle on each participant shard (Raft group). Coordinator state must be replicated. Use write-intents, parallel commits (~1-2 RTTs cross-region [Q5], [TSX1]).

8. **Sharding**: 256 MiB region size, split at 384 MiB. Auto-split + directory replication. Use REGIONAL BY ROW syntax to pin tenant metadata to home region ([SM1], [SM2]).

9. **Geo-partitioning**: Store metadata keyed by tenant/namespace. Ensure home region is the leader. Refuse cross-shard transactions for strict locality SLO.

10. **Failover story**: Detect region loss via lease expiry and election timeout. Survivor region elects new leader in 1-3.5s. Write availability resumes. Reads on followers possible immediately via closed timestamp ([RP2], [WAN3]).

11. **Avoid leaderless**: EPaxos adds dependency tracking without clear latency win for metadata. Multi-leader LWW loses create-if-absent semantics. Stick with Raft + leases ([EC1]).

12. **Consistency contract**: Linearizable writes at put-if-absent, compare-and-swap. Bounded-stale reads (200ms) for list operations. Caller can choose sync point (write ACK vs commit) for latency/durability trade-off.

13. **Why no commit-wait**: Spanner's commit-wait (~5ms) is cheap because TrueTime epsilon is <4ms. Standard NTP drifts 100-500ms; committing requires max-offset * 2 wait. Use max-offset as safety margin, not for latency.

14. **Bottleneck monitoring**: Track closed timestamp lag, lease grant latency, election timeout, and clock skew per region. Red-flag: election-timeout expiries (frequent failovers = short election timeout or high WAN latency), skew >60% of max-offset (node needs clock adjustment), or closed timestamp >1s behind (metadata writes are backpressuring, increase closed_timestamp.target_duration). Missing metric: time from region partition detection to new leader elected (should be <5s for US-Japan latency).

15. **Data loss safeguard**: Coordinator state is itself a Raft group. Intent cleanup on coordinator crash is synchronous (via transaction record). Raft quorum ensures no orphaned intents on two-region loss. Implementation detail: on restart, the coordinator replays its transaction log and any unfinished transactions are resolved: if the commit timestamp was replicated to participants, apply it; else, abort the transaction and participants clean up intents asynchronously.

16. **Read consistency SLA contract**: Advertise: (a) linearizable writes (strong consistency, latency = 1-2 cross-region RTTs + fsync), (b) bounded-stale reads at 200ms lag (eventual with max lag, latency = local read), (c) sync reads (linearizable, latency = 1 RTT to leader). Document that clients must choose at call time based on tolerance for staleness vs latency.

17. **Impact of closed-timestamp lag on P99 latency**: At 200ms default closed-timestamp lag, list operations that depend on strong consistency must wait for the closed timestamp to advance, adding ~200ms to their latency in the median case. For create-tenant (strong) followed immediately by list-tables (bounded-stale), the list sees the new tenant after ~200ms, not immediately. High-throughput use cases should tune closed_timestamp.target_duration lower (100ms) for better responsiveness, trading off write-path CPU cost (more frequent timestamp advancement messages).

---

## Spot-check corrections (2026-09-17, fetched primary sources myself)

| Claim in this survey | Checked against | Verdict |
|---|---|---|
| "kv.closed_timestamp.target_duration (200ms default)" [RP2, NUM3, NUM6], and every "200 ms lag" statement in §4, §11, §12 | https://www.cockroachlabs.com/docs/stable/cluster-settings.html | Wrong. `kv.closed_timestamp.target_duration` defaults to **3s**. 200 ms is `kv.closed_timestamp.side_transport_interval`. Follower reads are documented as "at least 4.2 seconds in the past" (follower-reads page). Replace 200 ms with 3 s wherever it describes staleness |
| "US East to US West ~130ms P50" [WAN2] | https://etcd.io/docs/v3.5/tuning/ and https://learn.microsoft.com/en-us/azure/networking/azure-network-latency | The etcd page does say 130 ms for the continental US, as a conservative planning figure. Azure's published monthly p50 is 71 to 73 ms for East US to West US 2, 83 to 85 ms East US to West Europe, 94 ms East US to Germany West Central, 154 to 155 ms West US 2 to Germany West Central, 224 ms East US to Southeast Asia. Use the Azure numbers for design math |
| "CockroachDB defaults: election timeout 1000ms, heartbeat interval 100ms" [C1, NUM3] | Not on the cited pages | Those are etcd's defaults. Do not attribute them to CockroachDB. [unverified] for CockroachDB |
| "Lease grant frequency ... every 1-2 seconds ... adaptive lease lengths" [LP1] | Not verified | Treat as [unverified] |
| CockroachDB shuts down at 80% of max offset [LP2, C1] | https://www.cockroachlabs.com/docs/stable/recommended-production-settings.html | Verified: "if a node's clock drifts from other nodes in the cluster by 80% of the maximum offset allowed, it spontaneously shuts down. This offset defaults to 500ms" |
| TiKV 256 MiB / 384 MiB / 54 MiB [SM1, SM2] | https://docs.pingcap.com/tidb/stable/tikv-configuration-file/ | Verified: `region-split-size` 256 MiB since v8.4.0 (96 MiB before), `region-max-size` = split-size / 2 × 3 |
| Spanner "5ms commit wait, 9ms Paxos latency, epsilon p99 <4ms" [NUM1] | Spanner OSDI 2012 PDF | "commit wait is about 5ms, and Paxos latency is about 9ms" verified (1-replica microbenchmark). Epsilon in the text is "about 1 to 7 ms" sawtooth; the p99 figure is only a graph. F1 latencies: reads 8.7 ms mean, single-site commit 72.3 ms, multi-site commit 103.0 ms |
| Addition: load-based split threshold | https://www.cockroachlabs.com/docs/stable/cluster-settings.html | `kv.range_split.load_qps_threshold` default 2500 QPS, `kv.range_split.load_cpu_threshold` default 500ms CPU per second |
| Addition: Raft election timeout, paper | Raft ATC 2014 | 150 to 300 ms recommended for LAN, with `broadcastTime << electionTimeout << MTBF`. For WAN, scale by the max RTT (etcd: at least 10x) |
