# Real-World Multi-Region Metadata Store Architectures

How production systems (Spanner, Megastore, CockroachDB, TiKV/TiDB, YugabyteDB, etcd, ZooKeeper, FoundationDB, Cosmos DB, DynamoDB, Databricks) shard, replicate, and serve metadata across regions with linearizable writes.

## Sources Reference

| ID  | URL | What it establishes |
|-----|-----|-----|
| S1  | https://research.google.com/archive/spanner-osdi2012.pdf | Spanner paper: TrueTime, Paxos groups, replicas, directories, write latency |
| S2  | https://docs.cloud.google.com/spanner/docs/instance-configurations | Cloud Spanner multi-region instance types, read/write replicas, leader placement |
| S3  | https://docs.cloud.google.com/spanner/docs/true-time-external-consistency | Cloud Spanner TrueTime mechanism and external consistency |
| S4  | https://docs.cockroachlabs.com/docs/stable/multiregion-survival-goals | CockroachDB SURVIVE REGION FAILURE, replica placement, zone constraints |
| S5  | https://www.cockroachlabs.com/blog/under-the-hood-multi-region/ | CockroachDB multi-region internals, leaseholder placement |
| S6  | https://docs.cockroachlabs.com/docs/stable/follower-reads | CockroachDB follower reads and closed timestamp mechanism |
| S7  | https://www.cockroachlabs.com/docs/stable/table-localities | CockroachDB table localities: REGIONAL BY ROW, GLOBAL |
| S8  | https://etcd.io/docs/v3.4/tuning/ | etcd heartbeat interval, election timeout, latency tuning |
| S9  | https://research.google.com/archive/chubby-osdi06.pdf | Chubby paper: cell size, Paxos, lease mechanism, KeepAlive |
| S10 | https://zookeeper.apache.org/doc/r3.9.3/zookeeperInternals.html | ZooKeeper consistency guarantees, sync() operation, sequential consistency |
| S11 | https://apple.github.io/foundationdb/configuration.html | FoundationDB multi-region config, transaction logs, resolvers, satellites |
| S12 | https://apple.github.io/foundationdb/ha-write-path.html | FoundationDB HA write path and mutation flow |
| S13 | https://docs.pingcap.com/tidb/stable/tso/ | TiDB Timestamp Oracle (TSO), global clock service |
| S14 | https://github.com/tikv/pd/wiki/Timestamp-Oracle | TiKV/PD placement rules, TSO architecture |
| S15 | https://docs.pingcap.com/tidb/stable/multi-data-centers-in-one-city-deployment/ | TiDB multi-DC deployment, 2+1 witness architecture |
| S16 | https://docs.yugabyte.com/stable/architecture/docdb-replication/async-replication/ | YugabyteDB xCluster async geo-replication |
| S17 | https://docs.yugabyte.com/stable/develop/build-global-apps/follower-reads/ | YugabyteDB follower reads and staleness config |
| S18 | https://docs.databricks.com/aws/en/admin/disaster-recovery | Databricks managed disaster recovery, Unity Catalog replication |
| S19 | https://learn.microsoft.com/en-us/azure/cosmos-db/consistency-levels | Azure Cosmos DB five consistency levels, bounded staleness |
| S20 | https://learn.microsoft.com/en-us/azure/cosmos-db/multi-region-writes | Azure Cosmos DB multi-region writes, last-writer-wins |
| S21 | https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/V2globaltables_HowItWorks.html | DynamoDB global tables v2, LWW conflict resolution, replication latency |
| S22 | https://learn.microsoft.com/en-us/azure/networking/azure-network-latency | Azure inter-region network latencies |
| S23 | https://www.cloudping.co/ | Cross-region latency measurements across cloud providers |
| S24 | https://www.cidrdb.org/cidr2011/Papers/CIDR11_Paper32.pdf | Megastore paper: Paxos groups, entity groups, witness replicas |
| S25 | https://web.stanford.edu/~ouster/cgi-bin/papers/raft-atc14.pdf | Raft paper: consensus, leader election |
| S26 | https://drops.dagstuhl.de/storage/00lipics/lipics-vol070-opodis2016/LIPIcs.OPODIS.2016.25/LIPIcs.OPODIS.2016.25.pdf | Flexible Paxos: quorum intersection revisited |
| S27 | http://cs.yale.edu/homes/thomson/publications/calvin-sigmod12.pdf | Calvin: deterministic ordering, transaction sequencing |
| S28 | https://github.com/efficient/epaxos | EPaxos: Egalitarian Paxos, dependency graphs, wide-area optimization |

## 1. Google Spanner

**One-line answer:** 5 Paxos groups across 3 regions; TrueTime commit-wait for linearizable reads; leader in home region.

### Metadata Sharding and Consensus Groups

Spanner organizes data into Paxos groups across datacenters [S1]. The root metadata (directories mapping entity groups to Paxos groups) is stored in a separate Paxos group, itself replicated across regions [S1].

### Replica Count and Placement

Cloud Spanner supports several instance configurations [S2]. A typical multi-region config (nam3: North America) uses five replicas across three regions: two read-write replicas in one region, one read-write replica in a second region, and two read-only replicas in Asia for fast remote reads. Under SURVIVE REGION FAILURE, you need at least three regions with voting replicas in two of them [S2].

### Leader and Leaseholder Placement

Leader and leaseholder in designated leader region (close to writes) [S2]. Failover elects new leader from remaining RW replicas [S1].

### Linearizable Write Flow and Latency

Client → leaseholder → replicate to quorum (3 of 5) → commit-wait (sleep until clock > commit_ts + epsilon) → reply. Commit-wait ensures all future reads see consistent snapshots. TrueTime epsilon: p99=4ms, p999=10ms [S1]. Multi-region write latency: ~100-300ms (2 RTTs + epsilon) [S1].

### Read Serving

Reads can be served from any replica (strong consistency via commit-wait), or from read-only replicas at a bounded staleness. Cloud Spanner documentation recommends that multi-region applications use read-only replicas for non-critical reads [S2].

### Region Failure and Failover

Quorum survives if 2 of 3 regions up. RPO zero; RTO ~10s [S1].

### Clock Mechanism

TrueTime: GPS + atomic clocks. Epsilon ~4ms p99. External consistency via TrueTime ordering [S1, S3].

### Cross-Shard Transactions

Spanner uses 2PC: lock all ranges, coordinate commit via consensus. Expensive but correct [S1].

## 2. Google Megastore and Chubby

**One-line:** Chubby (5-node lock service); Megastore: entity groups as Paxos groups; witness replicas vote without data.

### Metadata Sharding and Consensus

Entity groups are Paxos groups; metadata in Chubby (5-node clusters running Paxos) [S9, S24].

### Replica Placement

1 leader + 2 replicas + optional witness (witness votes, no data) [S24].

### Leader and Leaseholder

Paxos leader holds 3-5s lease; handles all writes and reads [S9, S24].

### Linearizable Write Flow

Client → leader (via Chubby lookup) → Paxos log → quorum ack → apply → reply. Latency: 50-100ms single-region, 150-300ms multi-region [S24].

### Read Serving

Reads from the leader are linearizable (always consistent with all prior writes). Reads from replicas are stale. Chubby provides a weaker guarantee: sequence numbers ensure a client sees its own writes, but not external consistency across clients [S9].

### Region Failure and Failover

If the leader region fails, a new leader is elected from the replicas in the survivor region. RPO is zero (writes replicated synchronously); RTO is ~10 seconds (Paxos election timeout) [S24].

### Clock Mechanism

Megastore uses logical clocks (apply IDs) and wall-clock timestamps from the leader. No TrueTime-like oracle; timestamp assignment is implicit in the Paxos log [S24].

### Cross-Shard Transactions

Megastore supports cross-entity-group transactions using two-phase commit coordinated by the client. High latency for global transactions due to coordinated consensus across multiple Paxos groups [S24].

## 3. CockroachDB

**One-line:** Ranges as Raft groups; leaseholder reads, quorum writes; follower reads (~4s stale).

### Metadata Sharding and Consensus

CockroachDB shards data into ranges (default 64-512 MB) [S4], each a Raft group. System range stores metadata about all ranges [S5].

### Replica Placement and Survival Goals

Under SURVIVE ZONE FAILURE (default): 3 replicas, one per zone in a region. Under SURVIVE REGION FAILURE: 5 replicas across 3 regions (e.g., 2+2+1) with zone constraints [S4]. Non-voting replicas can be added for read scale without impacting write latency [S4].

### Leaseholder and Leadership

Leaseholder = Raft leader, holds 3s lease, placed in home region. Dynamic rebalancing tracks request locality [S5, S7].

### Linearizable Write Flow and Latency

Client → leaseholder → HLC timestamp → replicate to quorum → apply → reply. Regional table latency: 5-10ms. Global table (5 replicas, 3 regions): 100-200ms [S5].

### Read Serving

Leaseholder reads: linearizable. Follower reads: eventual, default staleness 4.2s (3s target + 200ms transport + 1s slack) [S6].

### Region Failure and Failover

Raft re-elects leader from remaining replicas. RPO zero; RTO ~10s [S4, S5].

### Clock Mechanism

HLC (wall-clock + logical counter). No GPS/atomic clocks; max_clock_offset ~500ms [S5].

### Cross-Shard Transactions

2PC: lock all ranges, coordinator commits [S5].

## 4. TiKV, TiDB, and PD

**One-line:** PD = global timestamp oracle (SPOF); TiKV regions as Raft groups; learners for replication.

### Metadata Sharding and Consensus

PD maintains all region metadata; TiKV regions are Raft groups [S14].

### Replica Placement

3 replicas via placement rules. Learner replicas for rebalancing [S14].

### Leader and Leaseholder

PD = global timestamp oracle. TiKV region leaders elected via Raft [S13, S14].

### Linearizable Write Flow and Latency

Client → PD for start timestamp → read → buffer writes → PD for commit timestamp → replicate via Raft → reply. Two PD calls are the bottleneck. Colocated: 5-10ms. Cross-AZ: 20-100ms [S13].

### Read Serving

Snapshot reads from any replica. Follower Reads at bounded timestamp [S14].

### Region Failure and Failover

If the leader region fails, PD detects it via heartbeat timeout and elects a new leader from remaining replicas. RPO is zero; RTO is ~30 seconds (default heartbeat timeout) [S15]. If PD fails, no writes can proceed (no new timestamps issued), so PD is a SPOF [S13].

### Clock Mechanism

Timestamp Oracle (TSO): PD is a single node (or Raft leader among multiple PD nodes) that issues timestamps. TSO is int64: upper 46 bits are physical time (milliseconds), lower 18 bits are logical counter (can issue 262M timestamps/second) [S13].

### Cross-Shard Transactions

Percolator-style 2PC [S14].

## 5. YugabyteDB

**One-line:** Tablets as Raft groups; leader preference for home region; follower reads at 30s staleness.

### Metadata Sharding and Consensus

Tablets are Raft groups; metadata in replicated master service [S16].

### Replica Placement

3 replicas across zones/regions. Leader preference pins home region [S16].

### Leader and Leaseholder

The Raft leader is elected via Raft consensus. Leader preference can bias election to a specific region. YugabyteDB uses a lease system for reads [S16].

### Linearizable Write Flow and Latency

Client → tablet leader → Raft quorum → apply → reply. Home region: 5-10ms. Remote leader: 50-150ms [S16].

### Read Serving

Reads from the leader are linearizable. Follower reads with bounded staleness (yb_follower_read_staleness_ms, default 30s) can be served from any replica [S17]. Staleness should be >= 2x raft_heartbeat_interval (default 500ms) to avoid redirects to the leader [S17].

### Region Failure and Failover

If the leader tablet fails, Raft elects a new leader from replicas. xCluster allows failover to the secondary cluster via manual activation. RPO for xCluster depends on replication lag; RTO is ~30 seconds [S16].

### Clock Mechanism

Hybrid logical clocks (wall-time + logical counter) [S17].

### Cross-Shard Transactions

2PC [S16].

## 6. etcd and ZooKeeper

**One-line:** etcd not for cross-region (1000ms election timeout); ZooKeeper reads non-linearizable.

### Metadata Sharding and Consensus

etcd and ZooKeeper are monolithic (no sharding), single Raft/Paxos group for all metadata. Cluster-level coordination, not data-plane [S8, S10].

### Replica Placement

Single-region only: cross-region not recommended [S8].

### Leader and Leaseholder

etcd heartbeat 100ms, election timeout 1000ms. Cross-region (130ms RTT) causes frequent re-elections [S8].

### Linearizable Write Flow and Latency

Intra-region: 5-10ms. Cross-region not recommended [S8].

### Read Serving

etcd reads are from the leader (linearizable) or from followers with a consistent read via quorum [S8]. ZooKeeper reads are sequentially consistent per client but not linearizable across clients; to achieve linearizable reads, must call sync() first, which is expensive [S10].

### Region Failure and Failover

Loss of quorum stalls the cluster [S8, S10].

### Clock Mechanism

Logical clocks only [S8, S10].

### Cross-Shard Transactions

N/A [S8, S10].

## 7. FoundationDB

**One-line:** TLog + resolvers + storage via Paxos; satellites (logs only).

### Metadata Sharding and Consensus

Three layers: TLog (mutations), resolvers (conflicts), storage (sharded by key) [S11]. Metadata in TLog [S11].

### Replica Placement

Primary + remote DC (full). Satellites (TLog only). Minimized sync point [S11].

### Leader and Leaseholder

TLog leader in primary region. Resolvers in primary (detect conflicts) [S11, S12].

### Linearizable Write Flow and Latency

Client → TLog (primary + satellite, same region) → quorum ack → resolver (conflicts) → storage (async if remote) → reply. Primary-region latency: 5-10ms. Multi-region with remote storage: +50-150ms [S12].

### Read Serving

Immutable reads from any replica. Recent reads to primary [S11].

### Region Failure and Failover

Manual/semi-automatic failover to remote region. RPO varies; RTO ~30s [S11].

### Clock Mechanism

Global timestamp service for read versions [S11].

### Cross-Shard Transactions

ACID within region. Multi-region: eventual [S11].

## 8. Azure Cosmos DB and AWS DynamoDB Global Tables

**One-line:** Both use LWW (NOT linearizable). Cosmos DB: 5 consistency levels. DynamoDB: eventual or strong.

### Metadata Sharding and Consensus

Cosmos DB: partitions with multi-master, per-region quorum [S20]. DynamoDB: partitions with proprietary replication [S21].

### Replica Placement

Cosmos DB: read and write replicas in each region; conflict resolution is distributed (no central authority) [S20]. DynamoDB: primary partition + replica in each region; last timestamp wins [S21].

### Leader and Leaseholder

Cosmos DB: each region has its own write quorum; writes are coordinated locally, then sent to other regions asynchronously [S20]. DynamoDB: partition leader (region) coordinates local writes, then replicates [S21].

### Write Flow and Latency

Cosmos DB: local quorum, async to regions [S20]. DynamoDB: 1-5ms sync, then async (1-2s) [S21]. LWW NOT linearizable [S20, S21].

### Read Serving

Cosmos DB: 5 levels (strong, bounded staleness, session, eventual) [S19]. DynamoDB: eventual or MRSC (sync replicas) [S21].

### Region Failure and Failover

Both: region failure loses local quorum. Manual failover required [S20, S21].

### Clock Mechanism

Both use server timestamps at write time. Clock skew across regions can cause unexpected LWW winners [S20, S21].

### Cross-Shard Transactions

Cosmos DB and DynamoDB do not support true distributed ACID transactions across regions. Each region's transaction is isolated [S20, S21].

## 9. Databricks Unity Catalog and Metastore

**One-line:** Regional metastore; managed DR replicates async; no real-time sync.

### Metadata Sharding and Consensus

Unity Catalog metadata in regional metastore (managed DB, backend opaque) [S18].

### Replica Placement

Primary metastore in primary region; secondary in secondary region. MDR replicates on schedule [S18].

### Leader and Leaseholder

[unverified] managed RDBMS backend [S18].

### Write Flow and Latency

Primary → MDR pipeline → secondary (async). Lag: [unverified] minutes [S18].

### Read Serving

Primary: strong consistency. Secondary: eventual (lag TBD) [S18].

### Region Failure and Failover

Manual failover via console. MDR pauses during failover [S18]. Limitations: no streaming tables, ML models, secrets, endpoints replication [S18].

### Clock Mechanism

[unverified] RDBMS internal clock [S18].

### Cross-Shard Transactions

Not supported [S18].

## Key Takeaways for Interview Design

1. **Five replicas over three regions converges.** Spanner, CockroachDB, and Megastore: 5 replicas across 3 regions (2+2+1). Write quorum wait 3; read quorum survives one region loss.

2. **Leader in home region minimizes write latency.** Spanner, CockroachDB, YugabyteDB: 10-20ms local writes vs 100-200ms cross-region.

3. **Metadata sharding separate from consensus.** Spanner (directories), CockroachDB (system range), TiKV (PD), FoundationDB (TLog). Small metadata fits one Raft group.

4. **Linearizable writes = quorum replication + timestamps.** Quorum first; then assign timestamp via global oracle (TrueTime, TSO) or HLC.

5. **Lease-based reads beat quorum reads 10x.** 3-10s leases on single replica (1ms latency) vs quorum reads (10ms).

6. **Follower reads with staleness trade consistency for 50-100x latency reduction.** CockroachDB 4.2s, YugabyteDB 30s default staleness.

7. **Closed timestamps enable follower reads.** Watermark proves all txns with ts <= watermark committed. Enables stale reads from any replica.

8. **Witness replicas reduce storage without sacrificing quorum.** Vote in consensus but store no data. Essential for 5+ replicas.

9. **Clock skew kills LWW systems.** Cosmos DB and DynamoDB use last-writer-wins by timestamp. If A's clock is 100ms ahead, A always wins. Global clocks (TrueTime) or HLC fix this.

10. **SPOFs require graceful degradation.** TiDB TSO is SPOF. Design for stale reads, not hard failures, if metadata unavailable.

11. **Inter-region latency: 50-200ms typical.** US east-west 50ms, US-Europe 100-130ms, Europe-Asia 200ms [S22, S23]. Budget 2 RTTs for quorum.

12. **Async replication lag: 1-2 seconds.** DynamoDB, YugabyteDB xCluster, Databricks [S16, S21, S18].

13. **Metadata size drives DDL throughput.** Small metadata (< 1 GB) fits one Raft group. Large metadata needs sharding.

14. **Placement rules beat replication.** REGIONAL BY ROW or placement rules reduce write latency 10x vs naive replication.

15. **Two-phase commit scales poorly.** Minimize cross-shard transactions via placement; 2PC locks all shards and coordinates commit.

---

## Spot-check corrections (2026-09-17, fetched primary sources myself)

| Claim in this survey | Checked against | Verdict |
|---|---|---|
| "TrueTime epsilon: p99=4ms, p999=10ms [S1]" | Spanner OSDI 2012 PDF via `pdftotext` | The text says epsilon is "a sawtooth function of time, varying from about 1 to 7 ms" (0 to 6 ms local drift plus 1 ms to the time masters). The percentiles are only in Figure 6, a graph. From the 1-replica microbenchmark: "commit wait is about 5ms, and Paxos latency is about 9ms". Quote those, not "p99 = 4 ms" |
| "Multi-region write latency: ~100-300ms (2 RTTs + epsilon) [S1]" | Same PDF, Table 6 | Not in the paper. What it gives: F1-perceived latencies over 24 h: all reads 8.7 ms mean, single-site commit 72.3 ms mean, multi-site commit 103.0 ms mean, with east-coast datacenters "given higher priority in choosing Paxos leaders". Table 3 (5 replicas): write 14.4 ms, read-only txn 1.4 ms |
| Spanner "5 Paxos groups across 3 regions" (one-liner) | Same PDF §2.1 | Wrong wording. Spanner has many Paxos groups (one per tablet); the placement menu example is "North America, replicated 5 ways with 1 witness". Leader leases are "10 seconds by default" and after a zone kill "approximately 10 seconds after the kill time, all of the groups have leaders" |
| "Megastore ... RTO is ~10 seconds (Paxos election timeout) [S24]" | Not in Megastore | The 10 s figure is Spanner's leader lease (above). Do not attribute it to Megastore |
| "CockroachDB ranges (default 64-512 MB) [S4]" | https://www.cockroachlabs.com/docs/stable/configure-replication-zones.html | Default `range_max_bytes = 536870912` (512 MiB), `range_min_bytes = 134217728` (128 MiB). 64 MB was a pre-v20 default |
| "Follower reads: default staleness 4.2s (3s target + 200ms transport + 1s slack) [S6]" | https://www.cockroachlabs.com/docs/stable/follower-reads.html and cluster-settings | Docs say exact-staleness follower reads should be "at least 4.2 seconds in the past". `kv.closed_timestamp.target_duration` default 3 s and `kv.closed_timestamp.side_transport_interval` default 200 ms are verified. The "1 s slack" decomposition is not in the docs |
| "SURVIVE REGION FAILURE" replica count | https://www.cockroachlabs.com/docs/stable/multiregion-survival-goals.html | Verified: replication factor goes "from 3 (the default) to 5 ... spread across the 3 regions (2+2+1=5)" |
| "etcd ... Cross-region (130ms RTT) causes frequent re-elections [S8]" | https://etcd.io/docs/v3.5/tuning/ | The page says "A reasonable round-trip time for the continental United States is 130ms, and the time between US and Japan is around 350-400ms", election timeout should be at least 10x RTT, upper limit 50,000 ms. It does not say re-elections are frequent. Also 130 ms is conservative: Azure's published monthly p50 for East US to West US 2 is 71 to 73 ms |
| etcd size limits | https://etcd.io/docs/v3.5/dev-guide/limit/ | Default request limit 1.5 MiB, default storage quota 2 GiB, "8 GiB is a suggested maximum size for normal environments" |
| Chubby | Chubby OSDI 2006 PDF via `pdftotext` | Verified: "five replicas in each cell, of which three must be running"; master lease "an interval of a few seconds"; session lease default extension 12 s; sequencers (§2.4) for servers that must check a lock holder |
| Databricks Unity Catalog DR [S18] | https://docs.databricks.com/aws/en/admin/disaster-recovery (updated Sep 11, 2026) | Managed disaster recovery "replicates Unity Catalog metadata, managed table data, and workspace assets on a continuous schedule" and "lets you trigger failover from the account console". So today it is asynchronous replication with a console-triggered failover, not synchronous and not linearizable across regions |
| Inter-region RTTs [S22, S23] | https://learn.microsoft.com/en-us/azure/networking/azure-network-latency (monthly p50, ms) | East US to West US 2: 71 to 73. East US to West Europe: 83 to 85. East US to Germany West Central: 94. West US 2 to West Europe: 142 to 143. West US 2 to Germany West Central: 154 to 155. East US to Japan East: 162. East US to Southeast Asia: 224. cloudping.co is JS-rendered and could not be fetched with curl |
| TiKV region size | https://docs.pingcap.com/tidb/stable/tikv-configuration-file/ | `region-split-size` default 256 MiB ("Before v8.4.0, the default value is 96MiB"), `region-max-size` = split-size / 2 × 3 = 384 MiB |
