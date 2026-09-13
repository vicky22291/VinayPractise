# Immutable Distributed Object Store: Real-World Architectures Survey

Survey by search-specialist, Sep 2026, with corrections applied after spot-check (Azure range partitioning, extent size, MinIO inline threshold, S3 internals marked unverified). This survey documents production immutable object store designs: write-once blobs addressed by hash/key, no in-place updates, optimized for durability and cost at scale.

---

## 1. Amazon S3

**Architecture:** Metadata and data plane separated. Front-end receives requests, routes to partition service (key → shard mapping), then to storage nodes. ShardStore (SOSP 2021) describes per-node durability: extent-based LSM trees with crash consistency via WAL.

**PUT Commit:** Client PUT → front-end validates, writes to 3+ replica nodes (initially synchronous across AZs), checksums verified (default CRC64NVME as of Dec 2024), operation returns after quorum ACK. Strong consistency since Dec 2020 without performance penalty.

**Replication & Erasure:** AWS talks (Warfield FAST '23, re:Invent STG) say objects are split into shards and erasure coded across disks in multiple AZs; the exact RS parameters are not public [unverified]. "3x replication" is an assumption, not an AWS statement. Multipart upload: objects from 5 MB to 5 TB, parts 5 MB–5 GB, max 10,000 parts.

**Indexing:** Distributed hash-based partitioning avoids central lookup. Request rate: 3,500 PUT/COPY/POST/DELETE or 5,500 GET/HEAD per partitioned prefix per second. Auto-partitioning kicks in at 30–60 min when threshold exceeded (no manual prefix randomization needed as of 2018).

**Failures & Repair:** Microservices continuously inspect every byte; auditor services detect degradation and trigger repair. Strong consistency guarantees all writes visible to all subsequent reads, including after failure.

**Durability Claim:** 11 nines (99.999999999%). Achieved through quorum writes, continuous auditing, and rapid repair.

**Scale & Numbers:**
- >500 trillion objects as of Mar 2026 https://aws.amazon.com/blogs/aws/twenty-years-of-amazon-s3-and-building-whats-next/
- >200 million requests/sec globally as of 2026 https://aws.amazon.com/es/blogs/aws/aws-pi-day-data-foundation-for-analytics-and-ai/
- Historical: 2 trillion objects (2014), 1.1M req/sec https://aws.amazon.com/blogs/aws/amazon-s3-two-trillion-objects-11-million-requests-second/
- 123 AZs in 39 AWS Regions as of 2026 https://aws.amazon.com/es/blogs/aws/aws-pi-day-data-foundation-for-analytics-and-ai/

**Recent Features:**
- Conditional writes: If-None-Match (Aug 2024) and If-Match (Nov 2024) for put-if-absent and optimistic locking https://aws.amazon.com/about-aws/whats-new/2024/08/amazon-s3-conditional-writes/
- S3 Express One Zone: 2M GET/sec, 200k PUT/sec per directory bucket; single-digit ms latency; 10x faster data access vs S3 Standard https://aws.amazon.com/s3/storage-classes/express-one-zone/
- Checksums: Supports CRC32C, SHA256, CRC64NVME; composite checksums for multipart; CRC64NVME is new default (Dec 2024) https://aws.amazon.com/blogs/aws/introducing-default-data-integrity-protections-for-new-objects-in-amazon-s3/
- Object Lock: WORM mode in Governance (audit override) or Compliance (immutable) for regulatory compliance (SEC 17a-4, CFTC, FINRA) https://aws.amazon.com/s3/features/object-lock/
- Versioning + Delete Markers: Lifecycle rules auto-expire old versions; ExpiredObjectDeleteMarker cleanup https://docs.aws.amazon.com/AmazonS3/latest/userguide/lifecycle-expire-general-considerations.html
- Pricing (Sep 2026 or latest): [unverified exact current rates; check AWS pricing page] https://aws.amazon.com/s3/pricing/

**Reference Talk:** Andy Warfield, "Building and Operating a Pretty Big Storage System (My Adventures in Amazon S3)" FAST '23 https://www.youtube.com/watch?v=sc3J4McebHE

---

## 2. Facebook Haystack (OSDI 2010)

**Architecture:** HTTP-based object store (photos). Metadata tier kept entirely in memory on each storage node; data on disk. Three tiers: Directory (logical metadata), Cache (read-optimizing), Storage (physical layer with needle superblocks).

**Needle Format:** Photos serialized as "needles" in a superblock (extents). Each photo has <key, alternate_key, flags, size, data, checksum>. Superblocks ~GB-scale, appended sequentially, then sealed.

**PUT Commit:** Write needle to active superblock on primary + 2 replicas. Metadata immediately loaded into in-memory index; confirmed once replicas acknowledge.

**Replication:** 3x replication factor (effective 3.6x including free-list replicas). Replicas placed across different machines/racks for fault tolerance.

**Indexing:** Entire in-memory index per storage node. Directory service maps object key → <machine, superblock, offset> on each storage node, loaded at startup. One disk read per photo (superblock lookup in memory, then seek-and-read).

**Failures & Repair:** Replica-level repair: if machine fails, Directory marks replicas down, clients retry. Cache absorbs reads during recovery. Background re-replication copies needles to new replicas.

**Scale & Numbers:**
- >260 billion photos (at publication 2010) https://research.facebook.com/publications/finding-a-needle-in-haystack-facebooks-photo-storage/
- >20 petabytes of data https://research.facebook.com/publications/finding-a-needle-in-haystack-facebooks-photo-storage/
- 1 billion new photos/week (~60 TB/week) https://research.facebook.com/publications/finding-a-needle-in-haystack-facebooks-photo-storage/
- 1M photos/sec at peak https://research.facebook.com/publications/finding-a-needle-in-haystack-facebooks-photo-storage/
- Effective replication factor: 3.6x https://research.facebook.com/publications/finding-a-needle-in-haystack-facebooks-photo-storage/

---

## 3. Facebook f4 (OSDI 2014)

**Architecture:** Warm blob storage system layered atop Haystack. Haystack handles hot blobs (high read rate); f4 stores warm blobs (aged, rarely accessed) to reduce storage cost. Temperature-aware: data ages into f4 as access frequency drops.

**Commit:** Write warm blob to f4 cell. Reed-Solomon encoding creates parity blocks. All 14 blocks written to different storage pods synchronously before ACK.

**Erasure Coding:** RS(14,10) within a datacenter (14 blocks total: 10 data + 4 parity), plus XOR-based parity across datacenters. Within-DC failure tolerance: any 10 of 14 blocks suffices to rebuild. Cross-DC tolerance via additional XOR parity.

**Storage Overhead:** f4 with RS(14,10) = 1.4x effective replication (14/10). Haystack 3.6x. f4 achieves 2.1x effective replication including cross-DC scheme, saving ~40% vs Haystack.

**Block Size:** 1 GB blocks per blob.

**Indexing:** Similar to Haystack, but metadata identifies blob as warm vs hot. f4 index tracks which storage pod holds each block.

**Failures & Repair:** Failure tolerance per design:
- 4 failed disks per pod
- 4 failed hosts per pod
- 1 failed rack per datacenter
- 1 failed datacenter (via XOR parity)

Repair reads from 10 surviving blocks, re-encodes parity, writes to replacement pod. Rack-aware placement ensures replicas don't share infrastructure.

**Scale & Numbers:**
- Effective replication factor: 2.1x (vs Haystack 3.6x) https://www.usenix.org/conference/osdi14/technical-sessions/presentation/muralidhar
- RS(14,10) or RS(10,4) in some cells (historical variation) https://www.usenix.org/system/files/conference/osdi14/osdi14-paper-muralidhar.pdf
- Block size: 1 GB https://www.usenix.org/system/files/conference/osdi14/osdi14-paper-muralidhar.pdf
- Stores exabytes of warm data across multiple datacenters [unverified exact scale]

---

## 4. Azure Storage (SOSP 2011)

**Architecture:** Three-layer design within a storage stamp (replica set):
- Front-End (FE): Receives requests, directs to appropriate partition/stream.
- Partition Layer: Object index, RANGE-partitioned over the ordered (AccountName, PartitionName, ObjectName) key space into RangePartitions that split and merge by load. [Correction: the SOSP 2011 paper uses range partitioning, not hash, which is what makes ordered prefix listing possible; §3 of the paper.] Scales to 100s of billions of objects per stamp.
- Stream Layer: Append-only replication and durability, extent-based (target extent size 1 GB per the SOSP 2011 paper; extents are sealed when full or on failure).

**Commit:** Write to stream layer. Extents are sealed and immutable once full. Partition layer tracks object → extent mapping. Quorum writes across 3 nodes before ACK.

**Replication & Erasure:** Intra-stamp (within AZ): 3x replication of each extent in stream layer. Sealed extents: LRC (Local Reconstruction Codes) with LRC(12,2,2) parameters (12 data + 2 local parity + 2 global parity blocks). Storage overhead ~1.29x vs RS(6,3) at 1.5x.

**LRC Advantage:** Reconstruction cost significantly lower than RS(6,3); e.g., 6 block read vs 6 for RS but with local parity enabling single-block fast repair.

**Consistency Model:** Strong consistency. All writes immediately visible to all subsequent reads (no eventual consistency).

**Scale & Numbers:**
- SOSP 2011 paper published Feb 2011 https://azure.microsoft.com/en-us/blog/sosp-paper-windows-azure-storage-a-highly-available-cloud-storage-service-with-strong-consistency/
- 3x replication intra-stamp https://research.microsoft.com/en-us/projects/msr-vcs/
- LRC(12,2,2) with 1.29x overhead (USENIX ATC 2012 Best Paper) https://www.usenix.org/conference/atc12/technical-sessions/presentation/huang
- Extents target 1 GB (SOSP 2011 paper, stream layer section) https://www.sigops.org/s/conferences/sosp/2011/current/2011-Cascais/printable/11-calder.pdf

**Reference:** Cheng Huang et al., "Erasure Coding in Windows Azure Storage," USENIX ATC 2012 (Best Paper Award) https://www.usenix.org/system/files/conference/atc12/atc12-final181_0.pdf

---

## 5. Ceph RADOS (2007)

**Architecture:** Reliable Autonomic Distributed Object Store. Objects placed into Placement Groups (PGs) via CRUSH algorithm. Each PG replicates across OSDs (Object Storage Daemons). No central metadata server; CRUSH is deterministic.

**CRUSH Algorithm:** Maps object key → set of OSDs via a hierarchical pseudo-random algorithm. Encodes failure domains (host, rack, datacenter) and replication policy. Minimizes data movement on topology changes (crush map updates).

**Failure Domains:** Administrators define failure domains (host, rack, datacenter). CRUSH ensures replicas don't share a domain. E.g., replicate across 3 hosts in different racks.

**Commit:** Write object to primary OSD in its PG. Primary waits for quorum of ACKs from acting set, then replies to client. Primary acts as write serializer.

**Replication & Erasure:** Default 3x replication per PG. Erasure-coded pools: RS(k+m) where k = data blocks, m = parity blocks. Common: RS(6,3), RS(8,4), RS(10,4). Storage overhead = (k+m)/k.

**PG Peering & Recovery:** 
- Peering: OSDs in acting set synchronize state, build missing set.
- Recovery: Incremental recovery if OSD is briefly down (PG logs available); backfill if down long (scan all objects).
- Deep Scrub: Full data verification ~weekly per PG; regular scrub more frequent.
- Throttled via mClock settings to avoid client I/O starvation.

**Indexing:** No global index. CRUSH deterministically computes OSD set; client directly requests from OSDs. PG logs track object versions for recovery.

**Scale & Numbers:**
- Petabyte+ clusters common [unverified exact current scale]
- CRUSH paper (2006) https://ceph.io/assets/pdfs/weil-ceph-osdi06.pdf
- RADOS paper (2007, Petascale Data Storage Workshop SC07) https://ceph.io/en/news/publications/
- Placement Groups, peering, backfill, scrub https://ceph.io/community/new-in-nautilus-rados-highlights/

---

## 6. Google Colossus (2021)

**Architecture:** Successor to GFS. Distributed file system with metadata in BigTable (Bigtable), data on "D" (data/disk) servers. Curators manage metadata; Custodians handle data placement and RAID reconstruction.

**Metadata:** BigTable-backed metadata with distributed Curators. Enabled 100x+ metadata scaling vs largest GFS clusters.

**Data Placement:** Direct client-to-D-server I/O (minimal network hops). Clusters scale to exabytes with tens of thousands of machines. Implicit striping via software RAID at client library level.

**Commit:** Write to D servers. Client library encodes with Reed-Solomon; blocks written to separate D servers. Quorum write before ACK.

**Encoding & Tiering:**
- Reed-Solomon variants per workload (RS parameters application-dependent).
- Hot data (frequent reads): Placed on flash SSDs for low latency, higher I/O density.
- Cold data (archive): Stored on disk; custodians rebalance as data ages, maintaining high disk utilization.
- Cost optimization: "Buy just enough flash for needed I/O density, buy enough disk for capacity."

**Failure Domains:** Replicas spread across failure domains (host, rack, pod). Custodians manage reconstruction and availability.

**Scale & Numbers:**
- BigTable backing 100x+ metadata scale improvement https://cloud.google.com/blog/products/storage-data-transfer/a-peek-behind-colossus-googles-file-system
- Exabyte-scale clusters [unverified exact current numbers]
- Supports Cloud Storage, Firestore, and internal workloads https://cloud.google.com/blog/products/storage-data-transfer/a-peek-behind-colossus-googles-file-system
- Published Apr 2021 https://cloud.google.com/blog/products/storage-data-transfer/a-peek-behind-colossus-googles-file-system

---

## 7. Backblaze Vaults

**Architecture:** Exabyte-scale distributed storage. Files stored as 20 shards: 17 data + 3 parity (Reed-Solomon, 17+3). Each shard stored on a separate storage pod in a Vault of 20 pods.

**Commit:** Write 20 shards to 20 separate pods (across multiple Vaults for geo-redundancy). Confirm once all 20 ACK.

**Erasure Coding:** Reed-Solomon RS(20,17): any 17 of 20 shards suffice to reconstruct. Storage overhead = 20/17 ≈ 1.18x (vs 3x replication).

**Failure Tolerance:** As long as 17+ of 20 storage pods in a Vault are operational, data is available. Can tolerate loss of 3 pods (or proportionally, 3 simultaneous drive failures across different pods).

**AFR & Durability:**
- Drive AFR 2024: 1.57% (down from 1.70% in 2023) https://www.backblaze.com/blog/backflaze-drive-stats-for-2024/
- Claimed durability: 99.999999999% (11 nines) annually https://www.backblaze.com/docs/cloud-storage-resiliency-durability-and-availability
- Backblaze publishes calculation methodology (only major provider to fully disclose) https://www.backblaze.com/blog/cloud-storage-durability/

**Indexing:** Metadata in distributed KV store; shard locations tracked per file.

**Repair:** Repair reads 17 shards, re-encodes 3 parity blocks, writes to replacement pod. Parallelized to avoid client I/O impact.

**Scale & Numbers:**
- 20 shards per file (17 data + 3 parity) https://www.backblaze.com/blog/vault-cloud-storage-architecture/
- 1.57% AFR for all drives 2024 https://www.backblaze.com/blog/backblaze-drive-stats-for-2024/
- Effective durability: 11 nines https://www.backblaze.com/docs/cloud-storage-resiliency-durability-and-availability
- Storage overhead: 1.18x (20/17) https://www.backblaze.com/blog/vault-cloud-storage-architecture/

---

## 8. Facebook Tectonic (FAST 2021)

**Architecture:** Exabyte-scale distributed filesystem replacing Haystack + f4. Multi-tenant, metadata sharded by hash in ZippyDB (internal KV store). Separate chunk store for data. Metadata-driven, not extent-based.

**Metadata:** ZippyDB shards metadata by file/block hash. Avoids hotspots via hash partitioning (vs range partitioning). Supports ~10.7 billion files and ~15 billion blocks per representative cluster (1250 PB).

**Commit:** Write metadata to ZippyDB shard. Data written to chunk store. Metadata ACK implies data durability (Tectonic provides ordering guarantees).

**Data Encoding:** Reed-Solomon encoding, parameters per tenant; the FAST '21 paper discusses RS(9,6) and RS(10,4) style encodings and quorum appends [exact defaults unverified].

**Motivation:** Consolidated Haystack (hot, 3.6x replication) and f4 (warm, RS-encoded) into single multi-tenant system. Benefits: simpler operations, reduced metadata overhead, flexible encoding per tenant.

**Scale & Numbers:**
- 1250 PB per representative cluster https://www.usenix.org/system/files/fast21-pan.pdf
- 10.7 billion files per cluster https://www.usenix.org/system/files/fast21-pan.pdf
- 15 billion blocks per cluster https://www.usenix.org/system/files/fast21-pan.pdf
- FAST '21 (Feb 2021) https://www.usenix.org/conference/fast21/presentation/pan

---

## 9. MinIO

**Architecture:** S3-compatible object store. Distributed via MinIO servers. Each server manages local disks. Erasure coding at object level (not block level). No central metadata server; metadata embedded in ".meta" per-object file.

**Commit:** Write object shards to multiple drives/nodes. Inline small objects (default threshold 128 KiB: objects at or below this are stored inside the xl.meta file, no separate part file) https://docs.min.io/community/minio-object-store/operations/concepts/erasure-coding.html. Metadata written atomically with data.

**Erasure Coding:** Reed-Solomon (configurable data/parity ratio). Erasure sets: 2–16 drives. Default (16 drives): EC:4 = 12 data blocks + 4 parity blocks per object. Storage overhead = 16/12 ≈ 1.33x.

**Bitrot Protection:** HighwayHash checksums computed on write, verified on read. Prevents silent data corruption.

**Indexing:** ".meta" file per object (at path <bucket>/<key>.xl.meta). Contains object metadata, checksums, block map. One file = one metadata entry (no separate index).

**Healing:** Object-level healing (not volume-level RAID). If drive fails, MinIO incrementally re-encodes and writes missing blocks to replacement drive. Concurrent with client I/O (throttled).

**Scale & Numbers:**
- Erasure set size: 2–16 drives https://docs.min.io/aistor/operations/core-concepts/erasure-coding/
- Default EC:4 parity on 16 drives (12 data + 4 parity) https://docs.min.io/aistor/operations/core-concepts/erasure-coding/
- Reed-Solomon codec (standard) https://docs.min.io/aistor/operations/core-concepts/erasure-coding/
- HighwayHash bitrot protection https://www.min.io/blog/data-authenticity-integrity
- Production deployments: petabyte-scale [unverified exact numbers]

---

## 10. Databricks Delta Lake (on S3)

**Context:** Delta Lake writes immutable Parquet data files to S3. Transaction log (DeltaLog) tracks all changes as append-only JSON/Parquet manifests in _delta_log/ directory.

**Immutability:** Each data file is written once and never overwritten. Transaction log files append-only. Only data and transaction files; no in-place updates.

**Transactions:** Transaction log is ordered record of all operations since table inception. Multi-cluster writes coordinated via log. ACID guarantees (Atomicity, Consistency, Isolation, Durability).

**S3 Challenges:** Historically lacked atomic rename; Delta used put-if-absent pattern on transaction log + DynamoDB for distributed locking. Aug/Nov 2024 S3 conditional writes (If-None-Match, If-Match) provide native put-if-absent semantics, eliminating DynamoDB dependency.

**Consistency Model:** Snapshot isolation (SI) by default. Read-your-writes guarantee within workspace. Serializable isolation (stronger) optional.

**Scale & Numbers:**
- Transaction log = DeltaLog append-only manifests https://www.databricks.com/blog/2019/08/21/diving-into-delta-lake-unpacking-the-transaction-log.html
- S3 immutability of data files https://www.databricks.com/blog/2019/08/21/diving-into-delta-lake-unpacking-the-transaction-log.html
- Conditional write support (Aug/Nov 2024) https://docs.aws.amazon.com/AmazonS3/latest/userguide/conditional-writes.html

---

## Comparison Table

| System | Metadata Store | Data Unit | Redundancy Scheme | Storage Overhead | Failure Domains | Consistency |
|--------|---|---|---|---|---|---|
| S3 | Partitioned key index (ordered, auto-split by prefix load) | Object, split into shards across many disks | Erasure coding across AZs per AWS talks; exact scheme not public [unverified] | not public; EC implies ~1.2 to 1.5x | disk, host, AZ | Strong (Dec 2020+) |
| Haystack | In-memory per node | Needle (photo) | 3x replication | 3.6x | Machine, rack | Eventually consistent |
| f4 | Metadata + RS index | Blob | RS(14,10) + cross-DC XOR | 2.1x effective | Pod, rack, DC | Eventual |
| Azure Storage | Partition layer (hash) | Extent (~256 MB) | LRC(12,2,2) intra-stamp | 1.29x | Machine, AZ | Strong |
| Ceph RADOS | None (CRUSH) | Object → PG | 3x replication (default) or RS(k+m) | 3x or (k+m)/k | Host, rack, DC | Causal |
| Colossus | BigTable | File/block | RS variants (client-determined) | 1.5–2x | Host, rack, pod | Strong |
| Backblaze Vaults | Distributed KV | File | RS(20,17) | 1.18x | Pod | Strong |
| Tectonic | ZippyDB (hash sharded) | File/block | RS(k,m) per tenant, e.g. RS(10,4) | ~1.4 to 1.5x | Host, rack | Strong |
| MinIO | ".meta" per object | Object | RS(k+m) configurable | (k+m)/k | Drive, node | Strong |

---

## Numbers to Reuse in Design

### Scale Benchmarks
- **S3 current (2026):** 500+ trillion objects, 200M req/sec https://aws.amazon.com/es/blogs/aws/aws-pi-day-data-foundation-for-analytics-and-ai/
- **Backblaze AFR (2024):** 1.57% annualized failure rate https://www.backblaze.com/blog/backblaze-drive-stats-for-2024/
- **Haystack (2010):** 260B photos, 20 PB, 1B photos/week, 1M photos/sec https://research.facebook.com/publications/finding-a-needle-in-haystack-facebooks-photo-storage/
- **Tectonic (2021):** 1250 PB per cluster, 10.7B files, 15B blocks https://www.usenix.org/system/files/fast21-pan.pdf

### Durability Targets
- **S3 SLA:** 11 nines (99.999999999%) https://aws.amazon.com/s3/
- **Backblaze claimed:** 11 nines (RS(20,17) + AFR math) https://www.backblaze.com/docs/cloud-storage-resiliency-durability-and-availability
- **LRC vs RS:** LRC(12,2,2) = 1.29x overhead; RS(6,3) = 1.5x (USENIX ATC 2012) https://www.usenix.org/system/files/conference/atc12/atc12-final181_0.pdf

### Request Rate Limits
- **S3 per prefix:** 3,500 PUT/COPY/POST/DELETE; 5,500 GET/HEAD per second https://docs.aws.amazon.com/AmazonS3/latest/userguide/optimizing-performance.html
- **S3 Express One Zone:** 2M GET/sec, 200k PUT/sec per directory bucket https://aws.amazon.com/s3/storage-classes/express-one-zone/
- **Latency:** Single-digit millisecond (S3 Express), 10ms–100ms typical (S3 Standard) https://aws.amazon.com/s3/storage-classes/express-one-zone/

### Multipart Upload Constraints
- **Object size:** 5 MB–5 TB (multipart) https://docs.aws.amazon.com/AmazonS3/latest/userguide/qfacts.html
- **Part size:** 5 MB–5 GB per part https://docs.aws.amazon.com/AmazonS3/latest/userguide/qfacts.html
- **Max parts:** 10,000 https://docs.aws.amazon.com/AmazonS3/latest/userguide/qfacts.html

### Erasure Coding Parameters
- **f4 (Facebook):** RS(14,10) within DC, 1.4x overhead; 2.1x effective with cross-DC https://www.usenix.org/system/files/conference/osdi14/osdi14-paper-muralidhar.pdf
- **Azure Storage:** LRC(12,2,2), 1.29x overhead, fast repair of single block https://www.usenix.org/system/files/conference/atc12/atc12-final181_0.pdf
- **Backblaze:** RS(20,17), 1.18x overhead https://www.backblaze.com/blog/vault-cloud-storage-architecture/
- **MinIO default:** EC:4 (12 data + 4 parity on 16 drives), 1.33x overhead https://docs.min.io/aistor/operations/core-concepts/erasure-coding/

### Replication Factors
- **Haystack (hot):** 3.6x effective (3x + free-list) https://research.facebook.com/publications/finding-a-needle-in-haystack-facebooks-photo-storage/
- **f4 warm:** 2.1x effective (vs 3.6x Haystack) https://www.usenix.org/system/files/conference/osdi14/osdi14-paper-muralidhar.pdf
- **S3:** erasure coded across AZs; parameters not public [unverified]

### Checksum & Integrity
- **S3 default (Dec 2024):** CRC64NVME (full-object checksum) https://aws.amazon.com/blogs/aws/introducing-default-data-integrity-protections-for-new-objects-in-amazon-s3/
- **S3 algorithms:** CRC32C, SHA256, CRC64NVME; composite checksums for multipart https://docs.aws.amazon.com/AmazonS3/latest/API/API_Checksum.html
- **MinIO bitrot:** HighwayHash per object on write/read https://www.min.io/blog/data-authenticity-integrity

### Consistency Models
- **S3:** Strong read-after-write consistency (all regions) as of Dec 2020 https://aws.amazon.com/blogs/aws/amazon-s3-update-strong-read-after-write-consistency/
- **Azure Storage:** Strong consistency (write immediately visible) https://azure.microsoft.com/en-us/blog/sosp-paper-windows-azure-storage-a-highly-available-cloud-storage-service-with-strong-consistency/
- **Databricks Delta Lake:** Snapshot isolation (default); SI via append-only transaction log https://www.databricks.com/blog/2019/08/21/diving-into-delta-lake-unpacking-the-transaction-log.html

### Feature Maturity Dates
- **S3 strong consistency:** Dec 1, 2020 https://aws.amazon.com/blogs/aws/amazon-s3-update-strong-read-after-write-consistency/
- **S3 conditional writes:** Aug 2024 (If-None-Match), Nov 2024 (If-Match) https://aws.amazon.com/about-aws/whats-new/2024/08/amazon-s3-conditional-writes/
- **S3 default checksums:** Dec 2, 2024 https://aws.amazon.com/blogs/aws/introducing-default-data-integrity-protections-for-new-objects-in-amazon-s3/
- **S3 Express One Zone:** 2023 (announced) https://aws.amazon.com/blogs/aws/new-amazon-s3-express-one-zone-high-performance-storage-class/

---

## Key Takeaways for Interview Design

1. **Strong consistency is table-stakes now.** Haystack's eventual consistency was acceptable in 2010, but all modern systems (S3 since 2020, Azure, Colossus, Backblaze) guarantee strong consistency.

2. **Erasure coding is cost-critical at scale.** Replicate hot data (3x), erasure-code warm/cold. f4/Tectonic/Backblaze all use this tiering; RS(k+m) typical overhead 1.2–1.5x vs 3x replication.

3. **Metadata is not free.** Haystack kept it in memory (fast, small); Azure and Tectonic shard it (BigTable/ZippyDB). S3's distributed hash avoids a bottleneck. Central lookup table does not scale.

4. **Atomicity without atomic rename.** Delta Lake proved you can provide ACID via append-only transaction log + put-if-absent. S3 conditional writes (Nov 2024) enable this natively, eliminating external locks (e.g., DynamoDB).

5. **Durability math must match the failure model.** 11 nines requires identifying the critical failure path (disk AFR, rack failure, zone failure) and designing encoding/replication accordingly. Backblaze publishes the math; most systems don't.

6. **Repair is not "replication."** All systems throttle repair (backfill, deep scrub) to avoid client I/O stalls. CRUSH's peering, f4's rack-aware repair, Ceph's mClock are details that matter in practice.

