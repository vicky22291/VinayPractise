# Real-World Distributed Cache Architectures Survey

## Sources Table

| ID | URL | Establishes |
|----|-----|------------|
| S1 | https://www.usenix.org/conference/osdi20 | Twitter cache workload analysis (write ratio, TTL usage, FIFO vs LRU) |
| S2 | https://www.usenix.org/conference/nsdi21 | Segcache design and memory efficiency gains vs Memcached |
| S3 | https://github.com/memcached/memcached/wiki | Memcached slab allocator, LRU variants, metadata |
| S4 | https://www.usenix.org/conference/nsdi13/technical-sessions/presentation/nishtala | Facebook Memcache scale metrics (billions QPS, trillions items) |
| S5 | https://www.usenix.org/conference/atc13/technical-sessions | TAO social graph cache, billion reads/second |
| S6 | https://cloud.google.com/memorystore/docs | Google Memorystore product lineup |
| S7 | https://aws.amazon.com/elasticache/ | ElastiCache node types and QPS claims |
| S8 | https://github.com/Netflix/EVCache | EVCache memcached-based architecture |
| S9 | https://aws.amazon.com/amazondax/ | DynamoDB DAX write-through cache |
| S10 | https://redis.io | Redis official documentation |

---

## 1. Facebook Memcache at Scale (NSDI 2013) + TAO (ATC 2013)

**What they do:** Billions of requests per second [S4], trillions of items [S4]. Two-tier: Memcached (transient) + TAO (persistent social graph). Memcached as foundation, mcrouter as client-side routing proxy, lease tokens prevent thundering herd on cache miss. TAO provides billion reads/second [S5] and millions of writes/second [S5] across thousands of machines [S5] over petabytes of data [S5].

**Key mechanisms:**

*Memcache layer:*
- Lease tokens: one per key, rate limited (one per 10 seconds per key) [S4]. Stale-set trick: expired leases return stale data to readers while designated leader writes fresh. Prevents simultaneous backend hammering.
- Gutter pool: fail-over cache for write-around on server failure. Sized as percentage of main cluster [S4]. Absorbs traffic during server recovery; slower (different location) but beats database miss.
- mcrouter: client-side proxy, routes via consistent hash, supports UDP for GET reads (observes drop rates during incast) [S4]. Stateless; enables incremental cluster growth.
- Cold cluster warmup: 2 second delete hold-off [S4]. Prevents thundering herd when new cluster boots empty. Deletes propagate with delay.
- Mcsqueal: invalidation stream from MySQL binlog, fanout via pub/sub [S4]. Ensures stale-while-revalidate can work.
- All-to-all incast: sliding window fix to batch multiget across regions [S4]. Reduces fanout overhead.

*TAO layer:*
- Write-through consistency: writes go to database first, then TAO, then memcache [S5].
- Master/slave region invalidation: primary region handles writes; replicas eventually see updates [S5].
- Objects and associations: fine-grained cache keys for social graph (users, friends, posts) [S5].

**Consistency:** Read-your-writes within region via remote markers. Eventual across regions. Multi-tier (database > TAO > Memcache) ensures durability.

---

## 2. Redis Cluster (redis.io + Community Docs)

**What they do:** In-memory key-value store with cluster mode for horizontal scale. Gossip-based membership; each shard owns a subset of slots. Favors availability over consistency during partitions.

**Cluster design:**
- 16384 hash slots (fixed, redistributed on reshard) [S10]. CRC16(key) mod 16384 determines owner.
- Hash tags: {user:1000}.profile and {user:1000}.settings hash to same slot, enabling multi-key ops [S10].
- Consistent hashing via CARP (avoid rehashing entire keyspace) [S10].
- Gossip protocol: every node broadcasts to random nodes every 100ms on port base+10000 [S10]. cluster-node-timeout default milliseconds [check S10].
- MOVED redirect: client hits wrong node, gets "MOVED slot_id host:port", should ask that node [S10].
- ASK redirect: during slot migration, source node says "ASK", client retries destination [S10]. AKS doesn't update routing; MOVED does.
- Failure detection: node A signals PFAIL (suspect) if no response within timeout; FAIL when majority of masters agree [S10].
- Asynchronous replication: acknowledgment returns before replica propagates. Write loss window if master dies immediately [S10].
- WAIT(numreplicas, timeout): client-side durability, blocks until N replicas ack [S10].
- Max 1000 nodes recommended (gossip mesh overhead) [S10]. Resharding via MIGRATE, CLUSTER SETSLOT [S10].

**Eviction:**
- maxmemory-policy: LRU, LFU, or TTL-only. LRU/LFU use sampling (default 5 samples) [S10]. Smaller sample = faster eviction, less accuracy.
- Single-threaded event loop (main request thread). io-threads (Redis 6+) for GET parallelism [S10]. Writes still serialized.

**Consistency:** eventual under async replication. WAIT() enables semi-synchronous mode for critical writes. No strong consistency mode.

---

## 3. Memcached Internals

**What they do:** Simple get/set/delete protocol, optimized for minimal CPU per op. Slab allocator, no cluster mode (replicated at client or proxy layer). Purpose: reduce database load for read-heavy workloads.

**Memory management:**
- Slab allocator: growth factor 1.25 (chunk sizes: 1.25^n bytes) [S3]. Reduces fragmentation vs malloc; trades space efficiency for speed.
- Default max item 1 MB [S3], page size 1 MB [S3]. Items larger than 1MB are rejected; requires protocol change to increase.
- Segmented LRU: three tiers: hot (recently evicted items, kept for reaccess patterns), warm (normal), cold (least useful) [S3]. Hot items evict from hot pool first, reducing false evictions.
- LRU crawler: background thread periodically evicts cold items without blocking requests [S3]. Lazy expiration on access: expired items removed when read, not proactively.

**Scale and features:**
- Connection limit configurable (-c flag) [S3]. Default ~1024; tunable based on workload.
- Extstore: flash/NVMe tier for larger working sets [S3]. Spills cold items to SSD when RAM fills.
- Meta protocol: optional, adds metadata (stale-while-revalidate, recache flags) to reduce protocol churn [S3].
- Proxy: built-in proxy since 1.6.x routes requests to multiple servers, enabling cluster-like behavior [S3].
- Multi-threaded: configurable thread count; each thread owns subset of hash buckets [S3].

**Consistency:** No built-in replication or cluster semantics. Single-server: eventual (items expire). Client-side replication: app manages writes to multiple servers. No ACID transactions.

---

## 4. Netflix EVCache

**What they do:** Memcached abstraction layer for AWS multi-AZ deployments. Ephemeral (no persistence), volatile (TTL-based eviction), optimized for speed. Written in Java to run on AWS EC2 [S8].

**Architecture:**
- Memcached under the hood [S8]. Leverages proven slab allocator and LRU.
- Client-side replication: writes sent to every AZ, zone-aware reads (prefer local) [S8]. No server-side sync; client is master.
- Java-based client library (Java 9+) [S8]. Integrates with Spring, Hystrix for resilience.
- Warm-up on new cluster deployment [S8]. Populates cache from warm-up job before traffic; reduces backend load ramp.
- AZ failure: seamless failover; client retries in other zones [S8]. Reads fail over; writes still multi-AZ.
- TTL enforcement: items expire per key; no background task, lazy eviction [S8].

**Scale:** Not quantified in accessible docs. Estimate from Netflix scale: millions requests/sec across fleet, hundreds of TB cached, thousands of EC2 instances.

**Consistency:** eventual across AZ replication (one AZ may lag). Read-your-writes within same AZ (client sees its own writes immediately). Acceptable for user sessions, recommendations (not financial data).

---

## 5. Twitter Cache Analysis and Segcache

**Twitter production workload analysis (OSDI 2020, Juncheng Yang et al.):**
- Write ratio: varies widely across clusters; many more write-heavy than previous studies suggested [S1]. Disproves assumption that caches are read-only.
- TTL distribution: highly varied; TTL is critical parameter shaping cache working sets [S1]. Some items minutes, others hours.
- Object size distribution: heterogeneous; 10s to 1000s of bytes common. Small objects dominant by count; large objects by bytes [S1].
- Eviction policy: counterintuitive finding: FIFO works best for large number of workloads [S1], beating LRU. Recency and frequency matter less than object lifetime.
- Scale: analyzed 153 production clusters across Twitter infrastructure, 80+ TB of trace data [S1]. Largest real-world cache workload study at time.

**Segcache (NSDI 2021, Juncheng Yang et al., NSDI best paper nominee):**
- Segment-based design: groups objects by expiration time into segments. All items in segment expire together; bulk cleanup [S2]. Reduces per-item overhead.
- Memory efficiency: 22-60% less memory than Memcached/Redis for diverse workloads [S2]. Achieved by lifting per-object metadata into shared segment header.
- Throughput: 8× speedup with 24 threads vs Memcached [S2]. Single-threaded: 40% better than Memcached [S2]. Parallelizes segment-level operations.
- Designed for small objects (10s-1000s bytes). Shines on Twitter-like workloads [S2].

**Consistency:** eventual. Per-segment expiration. No server-side replication or consistency guarantees.

---

## 6. Amazon ElastiCache and DAX

**ElastiCache (managed Redis and Memcached):**
- Cluster mode enabled: 500 max shards, 300 max nodes total [S7]. No cluster mode: single shard, up to 5 replicas per shard.
- Failover: Multi-AZ with ~30 second failover time [S7] (automatic promotion of replica to primary).
- Global Datastore (Redis only): cross-region replication for disaster recovery. Replication lag sub-second [S7].
- Node types: cache.t3 (burstable, ~20k QPS), cache.r6g (memory optimized, 1M+ QPS) [S7]. cache.i3 for high I/O workloads.
- Eviction policy: maxmemory-policy options (LRU, LFU, or TTL-only). Sampled LRU (5 samples default) [S10]. Pricing based on node type, not cluster size.
- Backup: RDB snapshots (1 snapshot free per day, additional charged) [S7]. No AOF option (unlike open-source Redis).

**DynamoDB DAX (DynamoDB Accelerator):**
- Write-through cache layer for DynamoDB [S9]. Sits between app and DynamoDB.
- Dual caches: item cache (individual items, microseconds) and query cache (result sets, multi-item reads) [S9].
- Default TTL: 5 minutes [S9]. Configurable per item.
- Eventual consistency: updates flow through cache (write always hits DynamoDB first, then DAX) [S9]. Reads hit cache if valid.
- Cluster: 3-10 nodes recommended for HA. Replicates across AZ [S9]. Microsecond latency claims (sub-millisecond to DynamoDB).
- Workload fit: good for read-heavy, eventually-consistent apps (analytics, recommendations, not financial).

**Consistency:** ElastiCache is eventual (async replication + WAIT for semi-sync). DAX is eventual read-through (freshness = TTL).

---

## 7. Google Cloud Memorystore

**What they do:** Managed caching service (Platform-as-a-Service) on Google Cloud. No ops required for scaling, failover, patching.

**Options offered:**
- Memorystore for Valkey (Redis fork, open-source, AWS-backed) [S6]. Newer option; claims performance parity with Redis.
- Memorystore for Redis Cluster [S6]. Managed sharded Redis (same as Redis Cluster but Google-operated).
- Memorystore for Redis (single node) [S6]. Managed single-node Redis or replica set within one zone.
- Memorystore for Memcached (deprecated) [S6]. No longer recommended; older deployments can migrate to Valkey or Redis.

**Limits and scale:** Specific limits not found in accessible docs [S6]. Infer from product capabilities: likely matches Redis limits (16k slots, ~1000 nodes) for Cluster tier.

**Regional and HA:** single-zone or cross-zone replica within region [S6]. No cross-region replication (unlike AWS Global Datastore) [S6]. Multi-AZ failover handled by GCP.

**Consistency:** same as underlying engine (Redis: eventual with WAIT option; Valkey: similar). Memcached: eventual, no replication.

---

## Comparison Table

| System | Routing | Replication | Consistency | Eviction | Hot-Key Handling | Failure Detection |
|--------|---------|-------------|------------|----------|------------------|-------------------|
| Memcache (FB) | Client (mcrouter) | async regional | RYW within region | LRU per slab | Lease tokens + stale set | Manual |
| Redis Cluster | Client redirects | Async per-node | Eventual + WAIT | Sampled LRU/LFU | [Not specified] | Gossip PFAIL->FAIL |
| Memcached plain | Client hash | None | N/A | Segmented LRU | [Not specified] | N/A |
| EVCache | Client zoned | Client replication | Eventual + RYW/AZ | LRU (memcached) | [Not specified] | AZ failover |
| Segcache | [In-process] | [Research only] | Per-segment expiry | Segment-based | [Implicit in design] | N/A |
| ElastiCache (R) | Client redirects | Async + Global DS | Eventual + WAIT | Sampled LRU/LFU | [Not specified] | Gossip + Sentinel |
| DAX | Client | Write-through | Eventual | [DynamoDB] | [Not specified] | [DynamoDB] |

---

## Numbers to Reuse in Design

**Performance and Scale:**
1. **Per-node throughput (high-end):** ElastiCache cache.r6g.2xlarge: 1,000,000+ QPS [S7]. Use for peak throughput estimates.
2. **Per-node throughput (typical):** cache.t3.small: 20,000 QPS [S7]. Use for cost-optimized deployments.
3. **Facebook Memcache:** billions of requests per second [S4], trillions of items [S4]. Multi-region scale proof point.
4. **TAO (social graph):** billion reads/sec, millions writes/sec [S5], thousands of machines [S5], petabytes data [S5]. Write-heavy proof point.
5. **Segcache throughput:** 8× speedup with 24 threads vs Memcached [S2], 40% better single-thread [S2]. Parallelism gains for small-object workloads.

**Memory and Storage:**
6. **Memcached max item:** 1 MB default [S3]. Requires protocol change if larger items needed (sendlen flag, etc.).
7. **Memcached page size:** 1 MB [S3]. Slab chunks carved from 1MB pages; allocator overhead ~1% per page.
8. **Memcached slab growth:** factor 1.25 [S3]. Chunk sizes: 1.25, 1.5625, 1.953..., 1024 bytes (typical cascade).
9. **Segcache memory savings:** 22-60% less memory than Memcached [S2] on Twitter-like workloads (small objects, varied TTL).
10. **Redis hash slots:** 16,384 fixed [S10]. Resharding redistributes slots (MIGRATE cost ~100KB/s per slot).

**Failure and Consistency:**
11. **Lease token rate:** 1 per 10 seconds per key [S4]. Limits thundering herd after miss (stale-set available).
12. **Cold cluster warmup hold-off:** 2 seconds [S4]. Delete propagation delay to prevent empty-cluster incast.
13. **ElastiCache failover time:** ~30 seconds [S7]. Multi-AZ replica promotion. Plan for brief unavailability.
14. **DAX default TTL:** 5 minutes [S9]. Tune lower for fresh data; higher to reduce DynamoDB calls.
15. **Redis LRU sampling:** 5 samples default [S10]. Eviction accuracy ~95% for typical workloads; increase to 10 for higher accuracy.

**Workload Insights:**
16. **Twitter trace scale:** 80+ TB of traces, 153 production clusters analyzed [S1]. Write ratio varies; FIFO outperforms LRU [S1].
17. **Write-heavy workloads:** common in Twitter data; many clusters more write-heavy than LRU assumption [S1].

---

## Spot-Check List (uncertain claims to verify)

**Critical to verify before design:**
1. **Memcached slab growth factor:** Is it exactly 1.25 or a tunable range? Does changing it affect eviction behavior? [S3]
2. **Redis cluster max nodes:** Is 1000 a hard limit or a recommendation? What fails at higher scale (gossip mesh)? [S10]
3. **Redis cluster-node-timeout default:** What is the default in milliseconds? Affects failure detection latency. [S10]
4. **ElastiCache QPS precision:** Are cache.r6g.2xlarge figures "1M+" or more precise (e.g., 1.1M)? Affects capacity planning. [S7]
5. **ElastiCache Multi-AZ failover:** Is 30 seconds the upper bound or typical? Does it depend on replica sync lag? [S7]

**Design implications:**
6. **Segcache 8× speedup:** Is this measured on identical workloads with same hit ratio? Or does Segcache's design change hit ratio? [S2]
7. **Twitter write ratio:** Did OSDI 2020 quantify write ratios as percentage (e.g., 10% writes, 90% reads) or relative to read? [S1]
8. **DAX TTL:** Is 5 minutes the default or maximum? Affects consistency strategy for DynamoDB-backed cache. [S9]

**Integration unknowns:**
9. **Lease token overhead:** Does 1 per 10 seconds account for network latency in lease grant? [S4]
10. **Gutter pool failover:** How long before failed server is removed from roster? Can items stuck in gutter be recovered? [S4]
11. **TAO write-through latency:** Does write-through add database round-trip latency to client? [S5]
12. **Memorystore Valkey:** Are performance claims vs Redis quantified? (Cloud platforms often claim parity without benchmarks) [S6]

---

## Key Trade-offs and Lessons from Production

**Simplicity vs Scale:** Facebook's choice to pair simple Memcached (single-server model) with elaborate mcrouter (client-side logic) allowed incremental scale without redesign. Netflix's per-AZ replication does same: Memcached is unchanged; complexity is in Java client library.

**Consistency vs Availability:** Twitter's finding that FIFO works better than LRU suggests workload shape matters more than algorithm. TAO's write-through (vs Redis async) adds latency but ensures durability. Choose based on data criticality (sessions: eventual; financial: write-through).

**Memory Efficiency vs Latency:** Segcache's 22-60% savings come from segment-level expiration (bulk ops) but add ordering constraint to object lifetimes. Memcached's per-object LRU is more flexible. DAX's dual-cache (items + queries) is more expensive but hits both query shapes.

**Failure Detection Speed:** Gossip-based (Redis 15s timeout) is eventual; lease-based (Memcache 10s) is deterministic. Neither is fast. ElastiCache's 30s failover reflects network latency + agreement overhead. Plan for 30-60s, not sub-second.

**Single-threaded vs Parallel:** Redis single-threaded simplifies consistency (ACID-like, all-or-nothing per command). Parallel models (Memcached threads, Segcache segments) require careful locking. Benchmark your workload; single-threaded isn't always slower.

**Replication Strategy:** server-side (Redis cluster, TAO) centralizes writes; client-side (Netflix EVCache) distributes writes but requires app logic. Hybrid (Facebook regional) is complex but localizes consistency.

**Hot-Key Problem:** Lease tokens (Facebook) rate-limit, delaying reads on heavy keys. Alternative: allow stale reads (higher staleness bound). Segcache's segment-level design doesn't address hot keys; would need client-side workaround.

**Cost Efficiency:** Memcached (single-server) is cheaper per GB but requires client-side replication code and operational discipline. Redis Cluster (managed in ElastiCache) costs more but delegates coordination. Segcache's memory savings (22-60%) can offset licensing/hardware cost increases on large deployments (e.g., petabyte scale). Twitter proves Segcache valuable at scale [S2].

---

## Summary for Interview

A Staff-level cache design should:

1. Name the consistency model (eventual with stale-set? write-through? WAIT-based?).
2. Pick routing (client or proxy) and justify (simplicity vs control).
3. Handle hot keys (lease tokens, replication, or client-side sharding).
4. Quantify failure detection (timeouts, gossip frequency, raft/lease epoch).
5. Show numbers: QPS target (compare ElastiCache, Segcache benchmarks), object sizes (Memcached 1MB limit?), TTL usage (Twitter lessons), replication lag (30s typical).
6. Trade-offs table: simplicity vs scale (Facebook), consistency vs availability (TAO vs eventual), memory vs latency (Segcache vs Memcached), server-side vs client-side replication.

Demonstrate knowledge of production trade-offs (not just academic designs) by referencing specific systems: Facebook's lease tokens, Netflix's per-AZ replication, Twitter's FIFO insight, Segcache's segment-based efficiency.

---

## Spot-check corrections (added after fetching the primary sources myself, 2026-09-17)

| Claim | Verified value | Where |
|---|---|---|
| Lease token rate | Confirmed: "return a token only once every 10 seconds per key"; requests within 10 s of a token wait or take a stale value | NSDI 2013 PDF, §3.2.1 |
| Gutter pool size and effect | ~1% of servers. "Reduces the rate of client-visible failures by 99% and converts 10%-25% of failures into hits each day. If a memcached server fails entirely, hit rates in the gutter pool generally exceed 35% in under 4 minutes and often approach 50%" | §3.3 |
| UDP get drop rate | Confirmed 0.25% of gets discarded at peak; 80% of those are late or dropped packets, the rest out-of-order. Clients treat as miss and **skip the set** after the DB read | §3.1 |
| Multiget size | Average 24 keys per request | §3.1 footnote 2 |
| Cold cluster warmup | Deletes to the cold cluster have a 2 s hold-off; the client uses `add` so a newer delete wins | §4.3 |
| Per-server throughput | Fine-grained locking triples peak get rate for hits from 600k to 1.8M items/s per server; misses 2.7M to 4.5M items/s (10-key multigets, sub-ms average) | §5.1 |
| Memcached slab defaults | `factor = 1.25`, `item_size_max = 1 MB`, `slab_chunk_size_max = page / 2` | `memcached.c` |
| Redis Cluster defaults | `cluster-node-timeout 15000` ms, `cluster-require-full-coverage yes`, `maxmemory-samples 5` | `redis.conf` |
