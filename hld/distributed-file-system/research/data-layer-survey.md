# Research: the chunk / data layer in production file systems

Raw research notes (Sep 2026). Used as input to `solution.md` and `deep-dives/write-path-and-commit.md`, `deep-dives/durability-and-erasure-coding.md`. Numbers checked against the primary papers where I could; corrections to the first pass are marked `[corrected]`.

## 1. Chunk size

| System | Size | Why |
|---|---|---|
| GFS | 64 MB | Fewer master entries, fewer TCP setups, one lease covers many ops. Small files waste a chunk. SOSP '03 |
| HDFS | 128 MB default | Same reasoning. NameNode RAM is the budget |
| Colossus | not published, GFS-like | |
| Tectonic | blocks of tens of MB, split into chunks that are the unit stored on a disk. Exact default not stated in the paper [unverified] | FAST '21 |
| Azure Storage | extents up to 1 GB, append-only, sealed. Blocks inside extents | SOSP '11 |
| Ceph | 4 MB objects | CRUSH places objects, finer placement, more objects to track |

Rule: chunk size = metadata volume vs small-file waste vs parallelism. 64 MB at 100 PB is 1.6 B chunk records.

## 2. Write path models

### GFS: leased primary, primary-backup
- Master grants a 60 s lease to one replica (primary). Primary picks the mutation order, secondaries apply in that order.
- Data flows along a chain (client to nearest replica to next), control goes to primary. Ack after all replicas apply.
- Record append is at-least-once: a failed replica leaves the region inconsistent, the retry writes the record again at a new offset, readers must dedupe by record id and skip padding. This is the reason GFS is "relaxed", not strong.
- Stale replica detection: chunk version number, bumped by the master each time it grants a new lease.

### HDFS: pipeline with generation stamps
- Client -> DN1 -> DN2 -> DN3, 64 KB packets, acks flow back.
- Ack means the packet is in the DataNode's buffer, not on disk. `hflush` = visible to readers, `hsync` = fsync on every replica. HDFS-2682 discusses the gap.
- Generation stamp (GS) per block, bumped on pipeline recovery. A replica with an old GS is stale and is deleted.
- Write lease: soft limit 60 s, hard limit 60 min `[corrected]`. After soft limit another client can force recovery.
- Block report: heartbeat every 3 s, full block report every 6 h (`dfs.blockreport.intervalMsec`), incremental block reports sent promptly on receive/delete `[corrected]`. DataNode declared dead after ~10.5 min of silence.

### Azure Storage stream layer: chain replication, commit length
- Client -> primary (head) -> secondary -> secondary, synchronous, ack only after all replicas persist. Calder et al. SOSP '11.
- Commit length = the offset every replica in the chain has durably written. Readers may read only up to commit length.
- On any replica failure the extent is sealed: the stream manager (Paxos) asks the replicas for their lengths, picks the smallest commit length agreed by the reachable replicas, records it, and the writer continues in a NEW extent. Never repair an extent in flight. This is the cleanest strongly consistent write path in the literature.

### Tectonic: quorum append with reservation and hedging
- Client reserves capacity on K+M+extra nodes, then sends data. First K+M acks win. Hedged extra nodes absorb stragglers. RS(9,6) example in the paper.
- Blocks are sealed when full or on close. Reads of sealed blocks can be cached aggressively.
- Trade: reads must know which nodes actually hold the block (metadata records the winners).

### Colossus
- Clients write directly to D servers, "quorum technique to avoid waiting on stragglers". Details not published. [unverified]

### Comparison
| Model | Ack means | Torn read possible | Stale replica served |
|---|---|---|---|
| GFS | all replicas applied | no | no, but duplicates and padding are visible |
| HDFS | in buffer of all 3 (hsync: on disk) | no | no (GS) |
| Azure chain | all replicas fsynced | no | no (commit length) |
| Tectonic quorum | K+M of K+M+H fsynced | no | no (metadata records winners) |

## 3. Replication vs erasure coding

| Scheme | Overhead | Survives | Repair reads |
|---|---|---|---|
| 3x replication | 3.0x | 2 losses | 1 chunk |
| RS(6,3) | 1.5x | 3 | 6 |
| RS(10,4) | 1.4x | 4 | 10 |
| RS(9,6) Tectonic | 1.67x | 6 | 9 |
| LRC(12,2,2) Azure | 1.33x | 3 (and most 4) | 6 for a local repair |

- HDFS EC (HDFS-7285): striped layout, default policy RS-6-3-1024k, cell size 1 MB `[corrected]`. Small files under one stripe waste parity.
- Azure LRC(12,2,2): local parities cut repair bandwidth by ~50% vs RS(12,3). Huang et al. ATC '12.
- Small writes under EC: read-modify-write of the whole stripe, ~10x amplification. So encode only sealed, cold data; keep open and hot data replicated.
- Degraded read: a missing data fragment costs K reads plus decode, adds tens of ms to p99.

## 4. Durability math
- Disk AFR: 1 to 2% modern HDD (Backblaze), older fleets 2 to 4%.
- Independent-failure model for 3 replicas: loss needs 2 more failures inside the repair window. With AFR 2%, 100 TB per node, repair window 1 h: per-chunk annual loss ~ 1e-11 to 1e-12 if placement is spread. This gives "11 nines" on paper.
- Correlated failure dominates. Copysets (Cidon et al. ATC '13): random 3x placement in a 5000-node cluster loses some data with ~99% probability when 1% of nodes fail at once (a power event); copyset placement drops it to under 1%. Cost: recovery parallelism drops because a node's chunks share fewer peers.
- MTTR is the knob. 20 TB disk rebuilt by one node at 100 MB/s = 56 h. Rebuilt by 500 peers in parallel at 50 MB/s each = under 15 min. Repair must be cluster-parallel and rate-limited.

## 5. Integrity
- CRC32C per 64 KB (HDFS `.meta` file, 512 B default chunk for checksum granularity). Checked on every read by the reader. Client-side end-to-end check catches NIC and memory corruption.
- Background scrub: every replica re-read on a cycle (HDFS volume scanner default 3 weeks, Ceph deep scrub weekly). Corruption -> report -> re-replicate from a good replica. Costs ~1 to 2% of disk bandwidth.

## 6. Fencing and stale replicas
- Chunk version (GFS) / generation stamp (HDFS) / extent seal (Azure): bumped by the metadata service whenever the writer or replica set changes. Replicas that missed the bump are garbage.
- Writer lease (GFS 60 s, HDFS 60 s soft): one writer per file. Renewed by heartbeat. On expiry the metadata service runs recovery: seal the open chunk at the agreed length.
- Metadata leader fencing: HDFS HA uses the JournalNode quorum as the fence (a demoted NameNode cannot write the edit log) plus `sshfence`. Raft term does the same job natively.

## 7. Placement, repair, hot chunks
- HDFS: replica 1 local, 2 and 3 on one other rack. GFS: master balances disk use and recent creations. Ceph: CRUSH computes placement from a hierarchy, no central map. Tectonic: copyset-style placement.
- HDFS balancer bandwidth is throttled per DataNode (`dfs.datanode.balance.bandwidthPerSec`).
- Hot chunk: GFS raised replication for hot files and suggested clients read from each other. Fix in general: more replicas for hot chunks, client-side read cache for sealed chunks, read from any replica.

## 8. Storage node internals
- GFS and HDFS: one file per chunk on ext4/XFS plus a checksum file. Node scans disk on start to rebuild its inventory.
- Ceph BlueStore: raw block device, RocksDB for object metadata, WAL on SSD. Avoids double journaling of the file system.
- fsync cost: HDD 5 to 30 ms, SSD ~0.1 to 1 ms. Batch fsyncs. Put the chunk-server WAL on SSD.

## Sources
- GFS, Ghemawat et al., SOSP 2003. https://research.google/pubs/the-google-file-system/
- Windows Azure Storage, Calder et al., SOSP 2011. https://www.microsoft.com/en-us/research/publication/windows-azure-storage-a-highly-available-cloud-storage-service-with-strong-consistency/
- Tectonic, Pan et al., FAST 2021. https://www.usenix.org/system/files/fast21-pan.pdf
- Copysets, Cidon et al., ATC 2013. https://www.usenix.org/conference/atc13/technical-sessions/presentation/cidon
- Erasure Coding in Windows Azure Storage, Huang et al., ATC 2012. https://www.usenix.org/conference/atc12/technical-sessions/presentation/huang
- HDFS EC design, HDFS-7285. https://issues.apache.org/jira/browse/HDFS-7285
- HDFS hsync gap, HDFS-2682. https://issues.apache.org/jira/browse/HDFS-2682
- Ceph BlueStore. https://docs.ceph.com/en/latest/rados/configuration/bluestore-config-ref/
- Colossus blog. https://cloud.google.com/blog/products/storage-data-transfer/a-peek-behind-colossus-googles-file-system
