# Durability and Placement in Distributed Immutable Object Stores

Survey by search-specialist, Sep 2026, of mechanics, formulas, and production numbers for the data plane of write-once blob systems. Corrections applied after spot-check are marked `[corrected]`. Section 10 (worked math) added by hand.

## 1. Replication vs Erasure Coding

**Reed-Solomon (k,m) economics:**

Storage overhead = (k+m) / k; can tolerate m simultaneous failures.
Repair traffic = k fragment reads to rebuild one fragment.
Throughput: ISA-L [Intel Storage Acceleration Library](https://www.intel.com/content/www/us/en/developer/tools/isa-l/overview.html) achieves 6.79 to 7.18 GB/s encoding, 4.88 to 7.04 GB/s decoding per core with AVX-512 (RS config dependent) [vendor numbers; treat 3 to 5 GB/s per core as the safe planning figure].

**Production parameters in the wild:**
- Facebook f4: RS(10,4), [1.4x expansion](https://www.usenix.org/system/files/conference/osdi14/osdi14-paper-muralidhar.pdf); 65 PB logical to 53 PB physical after migration, saved 12 PB [unverified exact].
- Backblaze Vault: 17 data + 3 parity, [20 shards total](https://www.backblaze.com/docs/cloud-storage-resiliency-durability-and-availability), resilient to 3 simultaneous shard failures.
- HDFS: RS(6,3) [default policy](https://hadoop.apache.org/docs/current/hadoop-project-dist/hadoop-hdfs/HDFSErasureCoding.html), RS(10,4) for larger clusters; needs at least 9 racks for full rack tolerance with RS(6,3) (3 racks minimum to deploy).
- Azure: LRC(12,2,2) [local reconstruction codes](https://www.usenix.org/system/files/conference/atc12/atc12-final181_0.pdf): 12 data, 2 local parity (one per group of 6), 2 global parity. Single-fragment repair reads 6 fragments instead of 12. Overhead 1.29x vs 1.5x for RS(6,3) at similar durability.

Small objects (under ~1 MB) are 3x replicated; large objects erasure coded. Replication has lower encode/decode CPU cost, no read amplification for small reads, and lower read latency for small objects (one disk seek instead of k).

**Hitchhiker (Facebook SIGCOMM 2014):** erasure code [reducing repair network and disk traffic by 25 to 45%](https://research.fb.com/publications/a-hitchhiker-s-guide-to-fast-and-efficient-data-reconstruction-in-erasure-coded-data-centers/) with piggybacked parity, same storage overhead as RS. 98% of stripes with failures in Facebook's warehouse cluster had exactly one failed block, which is why single-block repair cost is the number that matters.

---

## 2. Durability Math: MTTDL and Annual Probability

**MTTDL formulas** ([Greenan, Plank, Wylie, HotStorage '10, "Mean time to meaningless"](https://www.usenix.org/legacy/event/hotstorage10/tech/full_papers/Greenan.pdf) argues MTTDL is a poor metric; NOMDL, the expected bytes lost per year, is better. Use MTTDL for intuition only.)

```
2-way mirror:      MTTDL = MTTF^2 / (2 x MTTR)
3-way replication: MTTDL = MTTF^3 / (3 x 2 x MTTR^2) = MTTF^3 / (6 x MTTR^2)     [corrected: the survey's first draft gave the 2-way form]
RS(k,m), general:  MTTDL ~ MTTF^(m+1) / ( (k+m)! / (k-1)! x MTTR^m )
```

Each object has an independent loss rate 1/MTTDL_obj; a system of N objects has MTTDL_sys = MTTDL_obj / N.

**Inputs:**
- Disk MTTF ~ 1 / AFR. AFR 1.5% per year gives MTTF ~ 67 years = 584,000 h. Vendor MTTF numbers (1.2 M to 2.5 M h) are optimistic; [Google FAST '07](https://research.google/pubs/pub36737/) measured AFR 1.7% in year 1 rising to 8.6% in year 3 ([paper](https://www.usenix.org/conference/fast-07/failure-trends-large-disk-drive-population)).
- [Backblaze 2024 Drive Stats: 1.57% AFR across the fleet](https://www.backblaze.com/blog/backblaze-drive-stats-for-2024/); 2025: 1.36% [unverified, cited by the agent from the 2025 report].
- MTTR: the repair window after the first loss. This is the knob. 1 h vs 1 day changes MTTDL by 24^2 = 576x for 3-way and 24^4 = 330,000x for RS(k,4).

**Rebuild time at 100 MB/s for a 20 TB disk:** 20 TB / 100 MB/s = 56 h. Real single-target rebuilds achieve 30 to 80 MB/s under foreground load, so 3 to 8 days [industry rule of thumb; no primary source]. Distributed repair (every surviving disk rebuilds a slice of the dead disk's stripes onto many targets) divides that by the number of participating disks: 20 TB across 200 disks at 50 MB/s each = 33 min.

**What "11 nines" means:** [AWS: "if you store 10,000,000 objects with Amazon S3, you can on average expect to incur a loss of a single object once every 10,000 years"](https://aws.amazon.com/s3/faqs/). That is 1e-11 per object per year. [Backblaze publishes its calculation](https://www.backblaze.com/blog/cloud-storage-durability/): 17+3 shards, AFR and repair time inputs, Poisson model, and arrives at 11 nines with the repair window as the dominant term.

**Correlated failures dominate real systems:** [Google OSDI 2010, "Availability in Globally Distributed Storage Systems"](https://research.google/pubs/pub36737/): failure bursts (many nodes within a short window, typically a rack or power domain) dominate unavailability; a model that ignores correlation overstates availability by several orders of magnitude for rack-correlated events. Independent-failure math is a lower bound on risk, not an estimate.

---

## 3. Bit Rot and Integrity

**Silent data corruption rates:**
- [CERN 2007 study (Panzer-Steindel)](https://indico.cern.ch/event/13797/contributions/1362288/attachments/115080/163419/Data_integrity_v3.pdf): wrote known patterns to 3,000 nodes, found ~500 errors in ~2 weeks; roughly 1 corrupted file per 1,500 written [numbers from memory of the slide deck; verify before quoting]. The agent's "128 MB in 97 PB" figure is [unverified].
- [Bairavasundaram et al., FAST 2008, "An Analysis of Data Corruption in the Storage Stack"](https://www.cs.toronto.edu/~bianca/papers/fast08.pdf): over 1.53 M drives in 41 months, checksum mismatches on 0.86% of nearline (SATA) disks and 0.065% of enterprise disks. Corruption is spatially and temporally correlated on a disk.

**Why end-to-end checksums:** the disk, the controller, the DRAM, the NIC, and the kernel can each corrupt. A checksum computed by the client and verified at every hop and on every read is the only defence. Throughput per core (approximate, hardware-accelerated): CRC32C ~10 to 20 GB/s with SSE4.2/PCLMUL, xxHash3 ~20 to 30 GB/s, SHA-256 ~1.5 to 2 GB/s with SHA-NI [unverified, order of magnitude]. S3 defaults to CRC64NVME full-object checksums since Dec 2024 ([AWS blog](https://aws.amazon.com/blogs/aws/introducing-default-data-integrity-protections-for-new-objects-in-amazon-s3/)).

**ZFS Merkle checksums:** [every block pointer stores the child's checksum](https://research.cs.wisc.edu/wind/Publications/zfs-corruption-fast10.pdf); a mismatch is detected on read and repaired from a redundant copy.

**Ceph scrubbing cadence:** [light scrub daily (metadata and sizes), deep scrub weekly (re-read and checksum every byte)](https://docs.ceph.com/en/latest/rados/configuration/osd-config-ref/#scrubbing). Deep scrub of a full disk every 7 days costs 20 TB / 7 d = 33 MB/s, about 15 to 20% of an HDD's sequential bandwidth; most operators stretch it to 14 to 30 days and cap it at 1 to 5% of bandwidth.

---

## 4. Placement Algorithms

**Consistent hashing (Dynamo):** [virtual nodes (tokens) per physical node, "Q/S tokens per node" strategy](https://www.allthingsdistributed.com/2007/10/amazons_dynamo.html) spread load; adding one node moves ~1/N of the data, taken evenly from all others. Failure-domain awareness has to be bolted on (Cassandra's NetworkTopologyStrategy).

**CRUSH (Ceph):** [hierarchy-aware pseudo-random placement](https://docs.ceph.com/en/latest/rados/operations/crush-map/), no lookup table. Client plus cluster map compute the OSD set deterministically. Failure domains: osd, host, chassis, rack, row, pdu, pod, room, datacenter, zone, region. [CRUSH paper, SC '06](https://ceph.io/assets/pdfs/weil-crush-sc06.pdf). Cost: a topology change re-maps a fraction of PGs and moves data even when nothing failed; placement cannot be tuned per object (no "give this hot object 10 copies").

**Copyset replication ([Cidon et al., USENIX ATC 2013](https://www.usenix.org/conference/atc13/technical-sessions/presentation/cidon)):** with random replication, a simultaneous failure of 1% of nodes in a 5,000-node cluster loses some data with 99.99% probability; copysets with scatter width S=2 cut it to 0.15%. Facebook HDFS estimate: 22.8% to 0.78%. Trade-off: smaller scatter width means fewer peers to rebuild from, so slower repair.

**Placement constraints used in practice:** no two fragments in one failure domain; RS(10,4) needs 14 domains; spread hot objects across many disks so heat is spread. [Warfield, FAST '23 keynote](https://www.usenix.org/conference/fast23/presentation/warfield): S3 spreads each object across many disks and each disk holds pieces of many objects, so per-disk load is an average over many customers and the heat of a hot object is spread over many spindles.

---

## 5. Rebalancing and Repair

**Data movement on add:** consistent hashing, ~1/N of data; CRUSH, roughly the same fraction but chosen by the algorithm; central placement table, zero (new capacity fills from new writes; a background mover drains old nodes at a chosen rate).

**Throttling recovery:** [Ceph `osd_recovery_max_active` default 3 (HDD) and 10 (SSD), `osd_max_backfills` default 1](https://docs.ceph.com/en/latest/rados/configuration/osd-config-ref/); mClock profiles (`high_client_ops`, `balanced`, `high_recovery_ops`) reserve I/O shares between clients and recovery.

**Repair prioritization:** [Ceph prioritizes degraded PGs with the fewest remaining copies](https://docs.ceph.com/en/latest/rados/operations/pg-states/), then misplaced (fully redundant but in the wrong place). Declustered layouts spread each disk's stripes over many peers so that rebuild reads are parallel.

**Rebuild time scaling:** bigger disks with the same bandwidth mean a longer window: 4 TB at 100 MB/s = 11 h, 20 TB = 56 h, 30 TB = 83 h. Durability per bit falls as disks grow unless repair is distributed.

---

## 6. Disk and Node-Level Design

**Object storage layout:** [Haystack needle format, OSDI '10](https://www.usenix.org/legacy/event/osdi10/tech/full_papers/Beaver.pdf): a volume file is a superblock followed by appended needles (header, cookie, key, alt key, flags, size, data, footer, checksum, padding to 8 B). In-memory index per volume: key to (offset, size). One disk read per photo. Volumes ~100 GB, sealed when full.

**Extent-based design:** [Ceph BlueStore](https://docs.ceph.com/en/reef/rados/configuration/bluestore-config-ref/): raw block device, RocksDB for metadata, `min_alloc_size` 4 KB on both HDD and SSD since Pacific (was 64 KB on HDD), trading space amplification for small-object efficiency. [S3 ShardStore, SOSP '21](https://www.amazon.science/publications/using-lightweight-formal-methods-to-validate-a-key-value-storage-node-in-amazon-s3): a per-node LSM index over extents, with the LSM's own data in extents, crash-consistent by careful ordering rather than a WAL.

**Why not one file per object:** a filesystem with 1e9 files pays for inodes (256 B each), directory lookups, fsync of directories on create, and fragmentation. Packing objects into large append-only extents turns millions of small writes into sequential I/O and one index entry per object.

**Delete handling:** tombstone in the index, then compaction copies live needles into a new extent when garbage exceeds a threshold (Haystack compacts at ~ a configurable fraction; f4 leaves holes and relies on volume-level rewrite). Compaction write amplification is (live bytes rewritten) / (bytes reclaimed); at a 30% garbage threshold it is ~2.3x.

---

## 7. Upload Path

**Multipart upload constraints ([AWS S3](https://docs.aws.amazon.com/AmazonS3/latest/userguide/qfacts.html)):** 5 MB to 5 GB per part (last part may be smaller), 10,000 parts max, 5 TB object max [corrected: the agent's draft said 50 TB]. Checksum per part plus a composite (checksum of checksums) or full-object checksum. Incomplete uploads are cleaned by a lifecycle rule `AbortIncompleteMultipartUpload` after N days ([docs](https://docs.aws.amazon.com/AmazonS3/latest/userguide/mpu-abort-incomplete-mpu-lifecycle-config.html)); 7 days is the common choice.

**When to erasure code:** f4 and Azure replicate first (3x on the write path, cheap CPU, low latency), then encode sealed extents in the background; Azure's LRC paper reports the saving on the stamp-wide bill ([ATC '12](https://www.usenix.org/system/files/conference/atc12/atc12-final181_0.pdf)). Inline encoding on PUT writes 1.4x instead of 3x bytes and never re-reads the data, at the price of 14 parallel connections per PUT and encode CPU on the write path; it is the right choice for large objects and the wrong one for small ones.

---

## 8. Geo-Replication and Multi-Region

**S3 Cross-Region Replication (CRR):** [asynchronous; most objects replicate in seconds to minutes; S3 Replication Time Control (RTC) commits 99.99% of objects within 15 minutes](https://docs.aws.amazon.com/AmazonS3/latest/userguide/replication-time-control.html).

**Within a region:** synchronous multi-AZ writes. f4 keeps a [cross-DC XOR of two volumes in a third DC](https://www.usenix.org/system/files/conference/osdi14/osdi14-paper-muralidhar.pdf), giving 2.1x effective replication with tolerance for one DC loss.

**Egress costs:** [AWS inter-region transfer ~$0.02/GB (US to US), internet egress from $0.09/GB tiered down](https://aws.amazon.com/s3/pricing/). Replicating 500 PB once across regions costs ~$10 M in transfer alone.

---

## 9. Cost

**Storage (per TB-month, list prices, [AWS S3 pricing](https://aws.amazon.com/s3/pricing/)):**
- S3 Standard: ~$23 (first 50 TB tier, us-east-1)
- S3 Standard-IA: ~$12.5
- S3 Glacier Deep Archive: ~$1
- Backblaze B2: $6 ([B2 pricing](https://www.backblaze.com/cloud-storage/pricing))
- Raw HDD ~$12 to 18 per TB purchase (20 to 24 TB enterprise drives, 2025) [unverified]; over a 5-year life with power, rack, network, and the 1.4x EC overhead, all-in ~$2 to 4 per TB-month at hyperscale [estimate].

Erasure coding saves 40 to 55% of raw disk vs 3x replication: RS(10,4) = 1.4x vs 3.0x. f4 reported an effective-replication drop from 3.6x to 2.1x ([OSDI '14](https://www.usenix.org/system/files/conference/osdi14/osdi14-paper-muralidhar.pdf)).

---

## 10. Worked math for this design (added by hand)

Inputs: AFR 1.5%, disks 20 TB, 500 PB live, 10,000 storage nodes x 24 disks = 240,000 disks, distributed repair.

```
Repair window W after one disk loss:
  Bytes to rebuild            = 20 TB
  Peers holding sibling frags = ~2,000 disks (declustered)
  Per-peer repair budget      = 20 MB/s (10% of an HDD)
  Aggregate                   = 40 GB/s -> 20 TB in ~8 min of reads; writes spread the same way
  Take W = 30 min to include detection delay (10 min) and queueing.

Per-fragment loss rate inside W:
  lambda_W = AFR x W / 8,760 h = 0.015 x 0.5 / 8,760 = 8.6e-7

RS(10,4), one stripe, independent failures:
  P(lose 5 of 14 within one window) ~ C(14,5) x (lambda_W)^4 x AFR
    first failure happens (AFR per year x 14 fragments), then 4 more in W:
  P_year ~ 14 x 0.015 x C(13,4) x (8.6e-7)^4 = 0.21 x 715 x 5.5e-25 = 8e-23 per stripe per year

3x replication, one chunk:
  P_year ~ 3 x 0.015 x C(2,2) x (8.6e-7)^2 = 3.3e-14 per chunk per year

Stripes in the system: 500 PB / (10 x 64 MB per stripe) = 780 M stripes.
  Expected EC stripe losses/yr = 780e6 x 8e-23 = 6e-14. Meaningless. Independent-failure math is not the risk.
  Expected 3x chunk losses/yr with W = 56 h (single-target rebuild): lambda_W = 9.6e-5, P = 4.1e-10 per chunk,
    x 7.8 B chunks = 3.2 chunks lost per year. This is the number that forces distributed repair.

Correlated failure (rack of 40 nodes = 960 disks dies, 0.4% of the fleet):
  RS(10,4) with 14 fragments in 14 racks: zero fragments lost per stripe beyond 1. Safe by placement.
  With random rack placement: P(5 of 14 in one rack) ~ C(14,5) x 0.004^5 ~ 2e-9 per stripe; x 780 M = ~1.6 stripes lost. Placement, not math, is the fix.

AZ loss (1 of 3 AZs): RS(10,4) with 14 fragments over 3 AZs puts 5 in one AZ, so 9 survive: below k=10. NOT readable.
  Either use RS(9,6) spread 5/5/5 (survive an AZ: 10 of 15 remain), or RS(10,4) plus a 3-AZ stripe layout with at most 4 per AZ (impossible with 14 in 3 AZs).
  Choice for this design: RS(9,6) for cross-AZ durability, overhead 1.67x. Or RS(10,4) within AZ plus a cross-AZ XOR (f4 style), 2.1x.
```
