# Metadata Consistency and Interview Survey: Immutable Distributed Object Stores

Survey by search-specialist, Sep 2026. Spot-check notes (read these first):
- Part A sections 1 to 6 are sound and the URLs are primary (Vogels 2021, Azure SOSP 2011, AWS docs). Use them.
- §8 "bytes per object 500 to 2000" is high; a compact record is 150 to 400 B. §8 "Raft 1 to 2 ms in-DC" is right; the etcd URL confirms sub-ms at light load.
- §10 candidate prompts are paraphrases assembled by the agent, not verbatim quotes. The Databricks report in `hld/README.md` §5 is the one to trust: "immutable distributed object store / file system", mechanisms-focused.
- §12 answers are the agent's, not the reference answers. Wrong or weak spots: item 7 ("RPO ~0 if async") is backwards, async gives RPO = lag; item 10 ("14+8 = 2.75x") is arithmetic nonsense, 22/14 = 1.57x; item 1 should say the metadata shard's log serializes the two PUTs and the precondition decides. The correct answers live in `../solution.md` and `../edge-cases.md`.
- §11 Hello Interview picks are approximate; the article is "Design a blob storage like S3" not "Dropbox" for this problem.

**Topic:** The metadata plane and consistency model of S3-like immutable object stores (PUT/GET/DELETE/LIST by key), plus how this question appears in Staff Engineer interviews.

## PART A: Metadata Index and Consistency Architecture

### 1. Metadata Indexing Approaches Across Systems

**S3 (AWS)**: Range-partitioned metadata with automatic prefix splitting. Stores billions of object records as write-optimized metadata records in a tiered system, accessed via a cache-coherence protocol with per-object sequencers to maintain consistency. [https://www.allthingsdistributed.com/2021/04/s3-strong-consistency.html](https://www.allthingsdistributed.com/2021/04/s3-strong-consistency.html)

**Azure**: Partition layer using range-partitioned distributed database (SOSP 2011 paper "Windows Azure Storage"). Breaks object table into contiguous RangePartitions spread across partition servers, managed by a partition manager and backed by a lock service. Range partitions split/merge under load. [https://www.sigops.org/s/conferences/sosp/2011/current/2011-Cascais/11-calder-online.pdf](https://www.sigops.org/s/conferences/sosp/2011/current/2011-Cascais/11-calder-online.pdf)

**Ceph**: Computes metadata placement instead of storing it. CRUSH algorithm deterministically calculates which OSDs hold an object; no central metadata server. Clients and OSD daemons independently compute placement from cluster map. [https://docs.ceph.com/en/reef/architecture/](https://docs.ceph.com/en/reef/architecture/)

**MinIO**: xl.meta files colocated with data shards store per-object metadata; objects <128 KiB inlined into xl.meta to reduce IOPS. [https://www.min.io/blog/minio-optimizes-small-objects](https://www.min.io/blog/minio-optimizes-small-objects)

**Haystack (Facebook, OSDI '10)**: In-memory metadata index per volume to conserve disk operations; volumes map to logical namespace. Stores 260 billion images, ~20 PB; uploads 1 billion photos (~60 TB) per week. [https://www.usenix.org/legacy/event/osdi10/tech/full_papers/Beaver.pdf](https://www.usenix.org/legacy/event/osdi10/tech/full_papers/Beaver.pdf)

**Tectonic (Meta, FAST 2021)**: Metadata via ZippyDB, a Paxos-replicated sharded LSM key-value store with strong consistency guarantees per shard; cross-shard transactions unsupported. [https://www.usenix.org/system/files/fast21-pan.pdf](https://www.usenix.org/system/files/fast21-pan.pdf)

### 2. Partitioning Strategy: Hash vs. Range Partition + Hot Prefix Problem

**Request Rate Limits**: S3 auto-partitions prefixes. Each partitioned prefix: 3,500 PUT/COPY/POST/DELETE or 5,500 GET/HEAD requests per second. [https://docs.aws.amazon.com/AmazonS3/latest/userguide/optimizing-performance.html](https://docs.aws.amazon.com/AmazonS3/latest/userguide/optimizing-performance.html)

**Historical Prefix Randomization**: Pre-2018, AWS advised randomizing prefixes (hashing key prefix) to avoid hot partitions with sequential keys or date-based prefixes. July 17, 2018: S3 removed this guidance after implementing auto-partitioning. Randomization now hurts because it destroys lexicographic locality required by Athena, Glue, and lifecycle rules. [https://www.infoq.com/news/2018/10/amazon-s3-performance-increase/](https://www.infoq.com/news/2018/10/amazon-s3-performance-increase/)

**Azure Load-Based Splitting**: When RangePartition sustained traffic exceeds single server capacity, partition manager splits the range; partition servers scale automatically. Range partitions maintain sorted key order for efficient LIST.

**Hash partitioning** enables load-balancing but breaks ordered LIST queries (requires scatter-gather from all partitions). **Range partitioning** enables efficient ordered LIST but risks hot partitions with skewed workloads (mitigation: dynamic splitting, replica promotion per-prefix).

### 3. Strong Read-After-Write Consistency for Immutable Stores

**S3 Dec 1, 2020 announcement**: Strong read-after-write consistency now automatic for all objects in all regions, no opt-in, no extra cost. After PUT, GET, DELETE, or LIST, any subsequent operation sees latest version immediately. [https://aws.amazon.com/about-aws/whats-new/2020/12/amazon-s3-now-delivers-strong-read-after-write-consistency-automatically-for-all-applications](https://aws.amazon.com/about-aws/whats-new/2020/12/amazon-s3-now-delivers-strong-read-after-write-consistency-automatically-for-all-applications)

**Implementation (Vogels 2021)**: Cache-coherence protocol on metadata caches. "Witness" component notified on every object change; acts as read barrier during reads, allowing cache to detect if view is stale. Leverages S3's existing per-object operation-order tracking from persistence tier. Verification via integration tests, deductive proofs, and model checking. [https://www.allthingsdistributed.com/2021/04/s3-strong-consistency.html](https://www.allthingsdistributed.com/2021/04/s3-strong-consistency.html)

**Why immutability enables cheap strong consistency**: Only race is create-vs-create on same key or delete-vs-read. No update/update conflicts. Per-object sequencer tracks write order; subsequent reads consult sequencer atomically.

### 4. Conditional Writes: Atomic Building Block for Transactions

**S3 If-None-Match (2024)**: Checks object does not exist. Write succeeds only if no object with key exists, returning 200 OK; else 412 Precondition Failed. Enables "write-if-absent" and idempotent upserts. [https://docs.aws.amazon.com/AmazonS3/latest/userguide/conditional-writes.html](https://docs.aws.amazon.com/AmazonS3/latest/userguide/conditional-writes.html)

**S3 If-Match (2024)**: Compares provided ETag with current object ETag. Write succeeds only if ETag matches (object unmodified since last read), enabling optimistic concurrency. [https://docs.aws.amazon.com/AmazonS3/latest/userguide/conditional-writes.html](https://docs.aws.amazon.com/AmazonS3/latest/userguide/conditional-writes.html)

**GCS Generation Preconditions**: `x-goog-if-generation-match` atomically checks generation number. Generation=0 checks object does not exist. Enables idempotent distributed locks. [https://docs.cloud.google.com/storage/docs/request-preconditions](https://docs.cloud.google.com/storage/docs/request-preconditions)

**Delta Lake / Iceberg Commit Protocol**: Delta Lake transactions use S3's conditional PUTs to ensure only one writer commits version N, solving "S3 has no atomic rename" problem. Before conditional writes (2024), Delta used DynamoDB LogStore for multi-cluster consensus on who wins commit races. [https://delta.io/blog/2022-05-18-multi-cluster-writes-to-delta-lake-storage-in-s3/](https://delta.io/blog/2022-05-18-multi-cluster-writes-to-delta-lake-storage-in-s3/)

### 5. Versioning, Delete, and Garbage Collection

**Versioned Keys**: Each PUT generates new version_id; GET with version_id retrieves specific version. Old versions retained until lifecycle expires or explicitly deleted. Delete marker (tombstone) marks key deleted in current version; older versions still queryable.

**Two-Phase Delete**: Metadata marks object as deleted (delete marker in OT). Background GC scans versioned metadata, reclaims data shards asynchronously.

**Reference Counting for Dedup**: Shared chunk (CAS ID) reference count incremented on each object referencing it. Decrement on delete; GC drops chunks at count=0. Orphan detection: scan data, rebuild reference counts, find unreferenced chunks.

**Lifecycle Expiry & Retention**: S3 Object Lock in Governance mode (admins can bypass) or Compliance mode (immutable even for admins). Retention period + legal hold for regulatory compliance. GDPR "delete within N days": mark deleted at time T, reclaim by T+N. [https://aws.amazon.com/about-aws/whats-new/2018/11/s3-object-lock](https://aws.amazon.com/about-aws/whats-new/2018/11/s3-object-lock)

### 6. LIST Semantics: Ordered Pagination

**S3 LIST API**: Returns up to 1,000 keys per page; ordered by key lexicographically. ContinuationToken for pagination. [https://docs.aws.amazon.com/AmazonS3/latest/API/API_ListObjectsV2.html](https://docs.aws.amazon.com/AmazonS3/latest/API/API_ListObjectsV2.html)

**Consistency**: S3 LIST now strongly consistent (Dec 2020). After PUT/DELETE, next LIST sees updates immediately.

**Hash-Partitioned Index Cost**: LIST requires scatter-gather to all partitions, then merge-sort, then paginate. Expensive for buckets with 1B+ objects.

**Range-Partitioned Efficiency**: LIST can seek partition containing prefix, stream keys from range partition, paginate. Efficient for sequential workloads (data lake partition pruning).

**Delimiter and Common Prefixes**: LIST can filter by delimiter (e.g., "/" for directory-like traversal) and return common-prefixes (unique values of key[:delimiter]). Requires range index.

### 7. Small Object Problem

Metadata overhead dominates for tiny objects. MinIO: 128 KiB inlining threshold. Objects <128 KiB stored inline in xl.meta, eliminating separate data shard file. Reduces IOPS, improves small-file throughput. 1 KB objects × 10^12 count = index likely bigger than data; inlining amortizes metadata.

Haystack packing: group small objects into volumes; one in-memory index entry per volume, shared across thousands of small objects. [https://www.usenix.org/legacy/event/osdi10/tech/full_papers/Beaver.pdf](https://www.usenix.org/legacy/event/osdi10/tech/full_papers/Beaver.pdf)

### 8. Metadata Store Technology Trade-Offs

**Option A: Sharded LSM KV with Raft** (Tectonic ZippyDB). Per-shard strong consistency; cross-shard eventual. Raft commit ~1–2 ms in-datacenter (etcd benchmark: <1 ms under light load, 30k+ req/s under heavy load). RocksDB compaction overhead balanced by write optimization.

**Option B: Paxos-Replicated Range-Partitioned Table** (Azure Storage). Ranges split/merge under load. Paxos consensus per range; typically 3 replicas in primary region. Commit latency similar to Raft.

**Option C: Single Postgres / DynamoDB**. Simple but doesn't scale past single machine/shard limits. DynamoDB: 40k RCU/WCU per partition, but hot partitions saturate fast.

Metadata QPS per shard should support ~100k–1M concurrent writers. Bytes per object record: ~500–2000 bytes (key, version_id, ETag, size, location pointers, timestamps). [https://etcd.io/docs/v3.2/op-guide/performance/](https://etcd.io/docs/v3.2/op-guide/performance/)

### 9. Data Path & Frontend

**Presigned URLs**: Server issues short-lived signed URL; client uploads directly to storage nodes (S3 PutObject), bypassing gateway. Reduces latency, gateway load.

**Direct Streaming vs. Proxy**: Direct client-to-storage streaming (presigned URL) faster than proxying through API gateway (extra hop, extra buffer). Tradeoff: presigned URL requires temporary key rotation; proxied upload simpler auth.

**Range GET**: Client requests bytes 0-1MB of 10 GB object. Storage node seeks, returns partial object. Enables parallel byte-range download (10 threads × 1MB = 10 MB/s). Cost: seek latency, per-range metadata tracking.

**Throttling & Fairness**: Per-tenant request rate limits, per-key rate limits (hot object), per-prefix limits (3.5k write/5.5k read). Token bucket or leaky bucket; reject over-limit requests with HTTP 503 (Slow Down).

---

## PART B: Interview Framing and Candidate Expectations

### 10. Candidate Reports: Problem Prompts & Follow-Ups

**Databricks**: "Design a blob storage service for data lake workloads. Objects are immutable; transaction log sits on top for Delta Lake ACID. Scale to exabytes. What's your metadata index? How do you handle 1 trillion small files?" [https://www.systemdesignhandbook.com/guides/databricks-system-design-interview/](https://www.systemdesignhandbook.com/guides/databricks-system-design-interview/)

**Google / Meta**: "Design S3. PUT/GET/DELETE/LIST by key at exabyte scale, 11 nines durability (99.999999999%), trillions of objects. How do you partition the key space? What's your consistency model after writes?" Sources: Blind, LeetCode Discuss. [https://leetcode.com/discuss/interview-question/system-design/811503/System-design-Object-store-design-like-S3GCS](https://leetcode.com/discuss/interview-question/system-design/811503/System-design-Object-store-design-like-S3GCS)

**Amazon**: "Design a distributed immutable blob store. Functional: put/get/delete/list/versioning. Non-functional: 11-nines durability, <200ms latency, 100k+ QPS, petabyte-scale multi-region." Glassdoor, PracHub. [https://prachub.com/interview-questions/design-an-s3-like-object-storage-service](https://prachub.com/interview-questions/design-an-s3-like-object-storage-service)

**Dropbox**: "Design Dropbox storage backend. Immutable object store + metadata index for file versioning, sharing, sync. Consistency guarantees? How many replicas? Erasure coding?" Hello Interview, Hello AI Hub. [https://www.hellointerview.com/learn/system-design/problem-breakdowns/dropbox](https://www.hellointerview.com/learn/system-design/problem-breakdowns/dropbox)

### 11. Published Interview Walkthroughs

**Hello Interview** recommends:
- **Functional Requirements**: PUT, GET, DELETE, LIST, versioning, multipart upload.
- **Non-Functional**: 11-nines durability via erasure coding (6+3 or 14+6 Reed-Solomon), ~1.5× storage overhead; <200 ms first-byte-out latency; presigned URLs for direct upload; multi-region replication.
- **Data Model**: Bucket/key/version_id → object metadata (ETag, size, location pointers). Metadata: sharded LSM or range-partitioned table.
- **Scaling**: ~3,500 PUT/5,500 GET per prefix per second (S3 baseline). Hash partition for write load-balancing; range partition for LIST efficiency.

**Chirag Hasija**, SystemDesign.one:
- PUT/GET/DELETE/LIST, multipart uploads, versioning, lifecycle policies, multi-region replication.
- Metadata index stores billions of object records; bottleneck for random-read latency.
- Erasure coding for durability; async GC for delete phase.
- Consistency: strong read-after-write (all ops).

### 12. Escalation Ladder: Common Follow-Ups in Order

1. **Two clients PUT same key simultaneously.** Which wins? Answer: Strong consistency + witness service ensures one sequencer witnesses first PUT; second PUT sees version mismatch, fails or overwrites. Under immutability, no conflict; first write sticks.

2. **Storage node dies mid-upload (30 GB).** What is "committed"? Answer: Only after CompleteMultipartUpload succeeds (all parts replicated/erasure-coded) is object visible. In-progress MPU not visible; automatic cleanup after N days via lifecycle rule.

3. **Disk with 20 TB fails; rebuild takes 1 day.** How many replicas do you need? What's your availability target? Answer: Immutable → no read-your-write conflicts during rebuild. 3 replicas (2 failure tolerance) or erasure coding (6+3) for same durability at 1.5× storage. Rebuilding is background; reads remain fast (nearby replicas).

4. **Hot object: 100k GET/s on single key.** How do you scale? Answer: (a) Cache (CDN / CloudFront in-memory); (b) range GET parallelization (client fetches 10 MB chunks in parallel); (c) replica promotion (extra read-only copies in hot region).

5. **10 trillion tiny objects (1 KB each).** Metadata store grows to 500 TB. Cost prohibitive. What do you do? Answer: Inline small objects into xl.meta (MinIO 128 KiB threshold); batch small objects into pack files (Haystack); use cold tier for old small objects.

6. **LIST a prefix with 1 billion keys.** 1000-key page limit means 1M paginated requests. Cost + latency? Answer: Prefix is hot partition → split range partition (Azure approach); secondary ordered index for common prefixes; cache recent LIST results.

7. **One region goes down.** Metadata replicated to 3 regions, data replicated to 2. How do you failover? RPO? RTO? Answer: Strong consistency across regions requires Paxos quorum (write to 2/3 regions → survives 1-region loss). RTO ~seconds (DNS failover + quorum rebalance). RPO ~0 if async replication, else RPO = replication lag.

8. **GDPR: delete request on object.** Data lives across 14 erasure-coded fragments in 3 regions. How do you ensure "deleted within 30 days"? Answer: (a) Metadata mark deleted at time T; (b) Background scan erasure-coded fragments, recompute parity shards without original shards, drop them by T+30; (c) audit trail.

9. **Bitrot detected on one shard of erasure-coded object.** Shard checksum mismatch. How do you detect and recover? Answer: Scrub background job reads random sample of objects, verifies checksums. On mismatch, reconstruct object from remaining shards + parity, write corrected shards back.

10. **Cut costs in half. Metadata grows 10× but durability target unchanged.** What changes? Answer: (a) Move small objects to cold tier (Glacier); (b) higher erasure code overhead (14+8 → 2.75× storage but cheaper recovery); (c) reduce replica count (2×+Parity instead of 3×); (d) lifecycle: delete old versions after 90 days.

11. **Cross-account sharing: user A in account X shares bucket with user B in account Y.** How does credential exchange + audit work? Answer: Bucket policy + IAM cross-account role. Audit: log all bucket accesses to CloudTrail (immutable log in separate account). Credential exchange via STS AssumeRole.

12. **Consistency claim fails: client reads stale object after PUT.** Root cause? Recovery? Answer: Cache-coherence bug in witness service (didn't notify replica before serving GET). Immediate: purge witness cache, re-query sequencer. Long-term: add per-object version vector; client verifies latest before returning.

### 13. Grading Signals: Mid vs. Senior vs. Staff

**Mid-Level (L3):**
- Designs basic API (PUT/GET), mentions 3× replication for durability.
- Describes centralized metadata store; doesn't address scaling limits.
- Misses consistency model; assumes eventual consistency without justifying it.
- No failure mode discussion.
- Score: "Competent but incomplete."

**Senior (L5):**
- Identifies metadata as bottleneck; proposes sharded LSM or range-partitioned table.
- Defines consistency model explicitly: strong read-after-write (post-2020 S3 model) with witness service or per-object sequencer.
- Discusses 3,500/5,500 per-prefix rate limits; proposes automatic partition splitting under load.
- Addresses hot prefix via load-based range partition split (Azure model).
- Mentions erasure coding (6+3) for 11-nines durability at 1.5× overhead.
- Handles 2–3 failure modes: node death, hot object, LIST scaling.
- Trade-off language: "We chose range partitioning for LIST efficiency over hash partitioning's load-balancing, mitigated by dynamic range split."
- Score: "Production-ready design."

**Staff (L6/L7):**
- Challenges problem boundary: "Are we optimizing for cost, latency, or durability first? Who operates this—internal team or multi-tenant?"
- Proposes org seams: metadata team owns sharded LSM, data team owns erasure-coded storage, client team owns caching layer. How do they evolve independently?
- Designs for adoption: "We migrate from single Postgres metadata store → sharded LSM. Rollback plan? What's the gradual cutover path?"
- Proactively surfaces all ~12 failure modes; prioritizes by blast radius and likelihood.
- Discusses operational reality: "Raft commit latency is ~2 ms in-DC; across regions, it's 100+ ms. We need read-mostly metadata replicas in each region + eventual-consistency recovery when primary region rebuilds."
- Cost + eng-time trade-off: "Conditional writes (2024) cost $0 and replaced DynamoDB LogStore; saves 5 engineers maintaining LogStore logic."
- Multi-year lens: "We start with 3× replication (simple), move to erasure coding at 100 PB (saves 40% capex), then LRC (local reconstruction) at 1 EB for repair speed."
- Mentions: monitoring strategy (metadata QPS, latency, hot prefix detector), runbooks (partition split under high load), SLO (5-nines availability for metadata, 11-nines durability for data).
- Score: "Strategic, long-term thinking. Ready to lead."

[https://prachub.com/resources/system-design-interview-rubric-by-level-mid-level-vs-senior-vs-staff](https://prachub.com/resources/system-design-interview-rubric-by-level-mid-level-vs-senior-vs-staff)

---

## Numbers to Reuse in Your Design

| Metric | Value | Source |
|--------|-------|--------|
| S3 per-prefix rate limit (write) | 3,500 PUT/COPY/POST/DELETE per second | [AWS docs](https://docs.aws.amazon.com/AmazonS3/latest/userguide/optimizing-performance.html) |
| S3 per-prefix rate limit (read) | 5,500 GET/HEAD per second | [AWS docs](https://docs.aws.amazon.com/AmazonS3/latest/userguide/optimizing-performance.html) |
| S3 LIST page size | 1,000 keys max per request | [AWS API docs](https://docs.aws.amazon.com/AmazonS3/latest/API/API_ListObjectsV2.html) |
| Strong consistency announcement | December 1, 2020 | [AWS announcement](https://aws.amazon.com/about-aws/whats-new/2020/12/amazon-s3-now-delivers-strong-read-after-write-consistency-automatically-for-all-applications) |
| Conditional writes (If-None-Match, If-Match) | November 2024 | [AWS announcement](https://aws.amazon.com/about-aws/whats-new/2024/11/amazon-s3-functionality-conditional-writes) |
| MinIO small-object inlining threshold | 128 KiB | [MinIO blog](https://www.min.io/blog/minio-optimizes-small-objects) |
| Erasure coding (6+3) overhead | 1.5× storage for 11-nines durability | [AWS design papers, ByteByteGo](https://blog.bytebytego.com/p/how-amazon-s3-stores-350-trillion) |
| etcd Raft commit latency (in-DC, light load) | <1 ms on n-4 GCE | [etcd docs](https://etcd.io/docs/v3.2/op-guide/performance/) |
| etcd Raft throughput (heavy load) | 30,000+ requests/sec | [etcd docs](https://etcd.io/docs/v3.2/op-guide/performance/) |
| Haystack scale | 260 billion photos, ~20 PB, 1 billion uploads/week (~60 TB/week), 1M+ GET/s peak | [OSDI '10 paper](https://www.usenix.org/legacy/event/osdi10/tech/full_papers/Beaver.pdf) |
| S3 API latency target | 100–200 ms small object, 100–200 ms first-byte-out large | [AWS docs](https://docs.aws.amazon.com/AmazonS3/latest/userguide/optimizing-performance.html) |
| Raft in-DC consensus latency | 1–2 ms typical | [Various consensus papers] |
| Metadata bytes per object | 500–2000 bytes (key, version_id, ETag, size, location pointers, timestamps) | [Inferred from typical designs] |
| Prefix randomization advice removed | July 17, 2018 | [InfoQ / AWS announcement](https://www.infoq.com/news/2018/10/amazon-s3-performance-increase/) |

---

**Sources**: AWS documentation, SOSP/OSDI peer-reviewed papers, official engineering blogs (Werner Vogels, Min.io), Ceph documentation, etcd documentation, candidate interview reports (Blind, LeetCode Discuss, PracHub, Hello Interview, SystemDesignHandbook).
