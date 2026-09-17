# Distributed Cache Mechanisms: A Primary-Source Survey

## Sources Table

| ID | URL | Establishes |
|----|-----|------------|
| 1 | https://dl.acm.org/doi/10.1145/258533.258660 | Karger 1997: Consistent hashing paper, ring structure, key placement |
| 2 | https://arxiv.org/pdf/1406.2294 | Lamping & Veach 2014: Jump hash algorithm, no storage, fast, sequential limitation |
| 3 | https://arxiv.org/pdf/1608.01350 | Mirrokni et al 2016: Bounded loads, c=1.25, maximum load guarantee |
| 4 | https://research.google.com/pubs/archive/44824.pdf | Google Maglev 2016: Even distribution, consistent hashing variant |
| 5 | https://dl.acm.org/doi/10.1145/3149371 | Einziger et al 2017: W-TinyLFU, frequency + recency, O(1) eviction |
| 6 | https://www.cs.cmu.edu/~rvinayak/papers/s3-fifo-sosp-2023.pdf | Yang et al SOSP 2023: S3-FIFO, three-queue FIFO, 72% miss ratio reduction |
| 7 | https://www.usenix.org/system/files/nsdi24-zhang-yazhuo.pdf | Zhang et al NSDI 2024: SIEVE, 63.2% reduction vs ARC, 42% vs FIFO |
| 8 | https://redis.io/docs/latest/ | Redis official docs: maxmemory-samples=5, LFU, WAIT semantics |
| 9 | https://github.com/memcached/memcached/wiki | Memcached GitHub wiki: slab allocation, growth factor 1.25, 1MB item limit |
| 10 | https://github.com/ben-manes/caffeine/wiki/Eviction | Caffeine wiki: W-TinyLFU implementation, policy design |
| 11 | https://github.com/golang/groupcache | Go groupcache: singleflight, request coalescing, Do() duplicate suppression |
| 12 | https://www.usenix.org/system/files/conference/nsdi13/nsdi13-final170_update.pdf | Facebook NSDI 2013: Leases cut DB QPS from 17k to 1.3k, stale-set fix |
| 13 | http://techblog.netflix.com/2016/03/caching-for-global-netflix.html | Netflix blog: EVCache async replication via Kafka, topology-aware client |
| 14 | https://debezium.io/blog/2018/12/05/automating-cache-invalidation-with-change-data-capture/ | Debezium: CDC-driven invalidation, binlog capture, Hibernate integration |
| 15 | https://archive.org/details/xfetch | Vattani et al 2015: XFetch, probabilistic early expiration, beta formula |
| 16 | https://oldblog.antirez.com/post/update-on-memcached-redis-benchmark.html | Redis blog: Single-thread ops/s benchmarks, comparison to Memcached |
| 17 | https://docs.riak.com/riak/kv/2.2.3/learn/dynamo/ | Dynamo paper: 100-200 vnodes per node, replication at N hosts |
| 18 | https://github.com/3rd-Eden/node-hashring | Ketama: 40 vnodes, 160 hash ring points per server |

## 1. Key Placement: Consistent Hashing and Variants

**How it works**: Karger's consistent hashing maps keys and nodes onto a ring. A key belongs to the first node found clockwise from its hash position [1]. Each node gets multiple hash values (virtual nodes, or vnodes) scattered across the ring. Vnodes reduce imbalance: a single node's failure affects only its neighbors, not all nodes. Dynamo uses 100-200 vnodes per node to balance power-law workload (e.g., some items are hotter) [17]. Ketama standard: 40 vnodes per server, producing 160 hash ring points total via 4 extractions per MD5 iteration [18].

**How load distributes**: With K vnodes per node and N nodes, each node owns K*360/N degrees. Variance from uniform drops as K increases. Empirically, 100-200 vnodes achieves 5-10% load imbalance; Ketama's 40 vnodes achieves ~20% imbalance in worst case [1, 18].

**Variants**: Jump hash requires no storage and O(1) speed via pure math. Limitation: buckets must be sequential; cannot remove/add arbitrary nodes mid-stream [2]. Rendezvous (HRW) hashing: for each key, compute score to all nodes, pick max. Flexibility but O(N) per lookup. Bounded loads (Mirrokni et al) wraps consistent hashing: during node add, reassign keys to keep max-load <= 2*ln(n) with c=1.25, only ~1/(n+1) fraction of keyspace moves [3]. Maglev: lookup table hash function, designed for Google's software load balancer. Distributes traffic evenly over 16-bit lookup table [4].

**Disruption on change**: Consistent hashing moves ~1/(n+1) of keys per node add. Mod-N hashing (hash(key) mod N) moves ~(n-1)/n, i.e., almost all keys [1]. Vnodes make data movement parallel across many nodes on single-node failure; without vnodes, one node holds 1/N of the ring and all its data rehashes to one neighbor (hot spike) [17].

**Failure modes**: Hot nodes with too few vnodes create load imbalance. Small N (e.g., 3 nodes) means vnodes spread thin; variance stays high even with 40 vnodes per node. Ketama's 40 is standard but less balanced than 150-256 [18]. Jump hash cannot add nodes arbitrarily; only at end of sequence [2]. Bounded loads adds O(N) reassignments on node add to maintain max-load guarantee; needs careful implementation to avoid thrashing [3].

## 2. Replication Inside a Cache

**No replication (Memcached model)**: Single copy per key. Cache miss sends request to DB [9]. Simplicity: no coordination, no replication lag. Trade-off: full DB load on cache loss or node failure. Used when DB can handle peak miss traffic or when cache is "nice-to-have" (e.g., session hints, not canonical state).

**Async leader-follower (Redis model)**: Leader accepts writes, streams replication offset to replicas asynchronously. Replicas lag by milliseconds to seconds. A write is acknowledged to client immediately; if leader crashes before replica receives it, write is lost [8]. Window of loss: typically 10-100 ms with good network. min-replicas-to-write config: reject writes if fewer than N replicas are connected; doesn't prevent loss on master crash, only reduces peak load [8].

**WAIT command semantics**: WAIT(N, timeout_ms) blocks until N replicas ACK the latest write offset. Returns the count of replicas that actually acknowledged. Used in Redis Cluster for stronger consistency in critical paths [8]. Important: does NOT guarantee durability on crash; only that replicas have seen the data as of a moment in time.

**Client-side write-all (Netflix EVCache)**: Client sends write to all N replicas in parallel; waits for any 1 or a quorum to respond [13]. Advantages: clients control consistency; can fall back to single replica on slow node. Disadvantages: client complexity, higher latency for strongly-consistent writes. Netflix uses async Kafka replication to keep regions in sync; reads always hit local region [13].

**Read-repair and quorums**: Dynamo uses (R, W, N) quorum: R replicas for reads, W for writes, N total replicas. Quorum reads: if R > N/2, readers see latest write. Caches rarely use quorums; trade consistency for latency. Simple cache miss (read to DB) is cheaper than quorum read from replicas [17].

**Why caches skip quorums**: Quorum write is 2x latency (wait for majority). Quorum read adds latency if a replica is slow. On cache miss, DB read is already slow (100-500 ms); waiting for quorum replica (10-50 ms) is rarely worth it. Exception: when DB is very expensive (e.g., expensive join query), quorum replicas are worth the latency to reduce DB load [9, 13].

## 3. Eviction Policies

**LRU and sampling**: Redis maxmemory-samples=5 (default) samples 5 random keys per eviction; evicts least-recently-used. O(1) sampling but imperfect: misses recent items due to sampling bias. Setting to 10 approaches true LRU at 2x eviction cost [8]. Memcached also uses LRU but single global queue becomes bottleneck under contention; segmented LRU reduces lock contention [9].

**LFU in Redis**: Frequency tracked via log counter with configurable decay. lfu-log-factor (default 10) controls precision: higher = better frequency tracking, more memory per key. lfu-decay-time (default 1 minute) periodically decreases counters to prefer recent accesses over ancient ones [8]. Trade-off: LFU captures "most-used" but adds memory overhead; worse hit-rate than LRU on bursty, short-lived access patterns [8].

**TinyLFU and W-TinyLFU (Einziger et al 2017)**: TinyLFU uses count-min sketch to track recent access frequency in bounded memory. W-TinyLFU adds a window: new items go to a small window, are admitted to main pool only if frequency > eviction candidate. Main pool uses LRU on recency + frequency. O(1) time per operation, small per-entry memory (sketch + age field). Achieves near-optimal hit-rate on production traces [5].

**Caffeine (Java cache library)**: Implements W-TinyLFU with adaptive hill-climbing. Client specifies size; Caffeine dynamically adjusts window size vs main pool based on recent hit-rate. Very effective on diverse workloads; widely deployed [10].

**S3-FIFO (Yang et al SOSP 2023)**: Three static FIFO queues: small (10% size), main (80%), ghost (10%). New items go to small. On miss, move to main on second access. On miss from main, move to ghost (denies re-entry). Quick demotion prevents cache pollution from one-hit wonders. Reduces miss ratio vs LRU by up to 72% on test traces from 14 datasets; 6x throughput at 16 threads on multi-core systems. Simplicity: no frequency counter, only insertion order [6].

**SIEVE (Zhang et al NSDI 2024)**: Single FIFO queue, single visited bit per entry. On cache miss, if visited=0, evict (one-hit wonders); otherwise mark visited=1 and rehash to end of queue. Remarkably simple; reduces FIFO miss ratio by 42% (mean), ARC miss ratio by 63.2% on test traces. Outperforms S3-FIFO and LRU on some traces [7].

**Memcached segmented LRU (hot/warm/cold)**: Three-tier LRU to reduce lock contention on multi-core. Hot items stay in hot tier; aging pushes to warm, then cold. Background LRU crawler thread lazily expires items without scanning entire hash table [9]. Prevents pathological lock contention under concurrent load. Practical: hot tier is ~10% of cache, warm ~40%, cold ~50%. Eviction priority: cold first, then warm, hot is rarely evicted.

**Comparison: LRU vs LFU vs S3-FIFO**:
- LRU (recency only): good on temporal locality (e.g., request logs), poor on frequency (e.g., "liked" videos). Hit rate ~50-70% on web cache traces.
- LFU (frequency only): good on stable access patterns (e.g., config data), poor on bursty traffic (high eviction of bursty items). Hit rate ~55-75%.
- S3-FIFO (recency + quick demotion): best on mixed workloads, robust to one-hit wonders. Hit rate ~70-85% on production traces. Simple to implement [6].
- TinyLFU/W-TinyLFU (frequency + recency via window): also ~70-85% hit rate, more CPU overhead [5].

## 4. Memory Management

**Slab allocation (Memcached)**: Memory is pre-allocated and split into 1 MB pages. Each page is assigned to a slab class on first use, never reassigned. Within a class, pages are carved into fixed-size chunks. Chunk sizes grow by factor 1.25 (configurable via -f flag) from 96 bytes minimum up to 1 MB item limit. E.g., class 1 = 96 bytes, class 2 = 120 bytes, class 3 = 152 bytes, ... [9]. Space efficient for uniform access patterns; wasteful if item size distribution changes.

**Calcification problem**: Once a page is assigned to a slab class, it is locked in. If access patterns shift (e.g., many small items instead of large), wasted memory becomes unavoidable. Mitigation: Memcached 1.4.11+ added slab automove and reassign commands to redistribute pages at runtime [9]. Trade-off: reassignment adds CPU cost and requires locking.

**Growth factor tuning**: Smaller growth factor (e.g., 1.1) creates more slab classes, better fit, but more memory overhead tracking classes. Larger growth factor (e.g., 1.5) reduces classes, cruder fit, less overhead. Default 1.25 balances waste (typically 10-20%) against class count [9].

**Jemalloc and fragmentation (Redis)**: Redis uses jemalloc allocator. mem_fragmentation_ratio = memory used by jemalloc / size of data in memory. Ratios > 1.5 indicate significant wasted space. Mitigation: INFO command shows ratio; MEMORY DOCTOR suggests defrag. Active defrag (CONFIG SET activedefrag yes) rewrites keys to compact memory at runtime cost [8].

**Large values**: Memcached hard limit 1 MB per item (default, configurable with -I flag but discouraged; warning issued if > 1 MB). Chunking: items > 1 MB must be split into multiple cache keys by client. Redis has no hard limit but large values (100s of MB) cause single-threaded event loop to stall (0.8 ms per 1 MB at 10 Gbps), increasing tail p99 latency [9, 16].

**Why memory, not CPU, is the limit**: Cache nodes are I/O bound. Network bandwidth (10-100 Gbps) and memory bandwidth (10-20 GB/s per core) saturate before CPU (e.g., Memcached can saturate a 10 Gbps link with small items before CPUs hit 50% utilization). Memory per-node is typically fixed; eviction is the bottleneck [9, 16].

## 5. Hot Keys and Stampedes

**Detection methods**: Redis --hotkeys flag reports keys by LFU counter; requires scanning entire keyspace, expensive on large caches. Client/proxy layer: count-min sketch or space-saving algorithm (e.g., Frequent algorithm) to identify top-K keys on the fly [8]. Alternative: sample traffic, feed to off-box analytics (e.g., Kafka) for detection [13].

**Mitigation: in-process L1 cache**: Client maintains local cache with TTL of 100-500 ms. Reduces pressure on backend cache and DB. Cost: staleness, requires cache invalidation mechanism to broadcast deletes [13].

**Mitigation: key replication**: Store hot key on N random nodes with suffix (e.g., key_replica_0, key_replica_1). Client reads from any replica; load spreads. Trade-off: multiple copies in memory, requires write to N nodes (write-all or lease-based) [13].

**Request coalescing (Go groupcache singleflight)**: groupcache.Group.Do(key, fn) deduplicates concurrent requests for same key. Only one goroutine executes fn; others wait on a channel and receive the same result [11]. O(1) concurrency overhead (map + channels). Dramatically reduces DB load during hot-key cache miss (from N concurrent DB queries to 1) [11].

**Thundering herd on expiry**: When a cached item expires, multiple requests arrive simultaneously, all miss the cache, all query DB (herd). Facebook's lease mechanism: on cache miss, Memcache grants a 64-bit lease token valid for 10 seconds. Client must present lease token when setting value; if lease was invalidated by a delete, server rejects set. This prevents stale writes and limits thundering herd to one DB query per lease period. Measured impact: peak DB QPS drops from 17,000 to 1,300 (13x reduction) [12].

**XFetch (Vattani et al 2015)**: Probabilistic early expiration. Instead of waiting for TTL to expire, each process independently refreshes the key with probability p(t) based on how close to expiry. Refresh probability increases as expiry approaches (e.g., p(t) = e^(lambda * (t - TTL)) for negative lambda). Spreads refresh load over time, nearly eliminates thundering herd. Requires beta tuning per workload [15].

**Quantified capacity**: Memcached ~150k GETs/sec per node on commodity hardware. Redis single-threaded ~200k ops/sec [16]. One hot key on one node: if QPS to that key > 150k (Memcached) or 200k (Redis), that node becomes the bottleneck; replication or L1 cache required [9, 16].

## 6. Node Failure and Membership

**Detection methods**: Central config service (ZooKeeper, etcd): single source of truth, slow propagation (100-500 ms). Gossip (Redis Cluster): nodes exchange PFAIL (suspected fail) after cluster-node-timeout milliseconds; FAIL (confirmed) requires quorum of nodes. Client-side failure counting (mcrouter): clients count failures per node, mark down after threshold, re-probe periodically [8].

**Detection time tradeoff**: Redis cluster-node-timeout default 15,000 ms (15 seconds). Shorter (5-10s) on stable LAN: faster detection but higher false-positive rate on network hiccups. Longer (15-30s) in cloud/WAN: slower recovery but fewer false positives. Sweet spot is usually 10-15s [8].

**Key handling on dead node** (four strategies):
1. Full miss to DB (gutter pattern): All keys hashed to dead node cause DB queries; requires load shedding and rate limiting to prevent DB overload (e.g., cap to 1k QPS/key). Cold-start: miss rate doubles for 30-60 min [12].
2. Rehash to neighbor (consistent hash): Keys mapped to dead node are remapped to next live node clockwise via client/proxy. Requires either pre-existing replicas or accept stale data (2+ hours old). Simpler but risky if neighbor is also slow [1].
3. Promote replica: If key is replicated (N=2 or 3), promote replica to leader. Requires async or semi-sync replication. Replication lag means promoted replica is stale by 10-100 ms [8, 12].
4. Gradual ramp: Slowly increase traffic to hot-standby node over 10-30 min to warm cache before full traffic cutover. Smooths miss spike, DB handles progressive load increase [12].

Choice: Netflix uses combo of #2 (rehash to neighbor, with replicas) + #4 (gradual ramp on restart). Facebook uses #1 (gutter) + leases to bound DB load [12, 13].

**Cold cache after restart**: A cache node restart loses all in-memory data. Miss-rate doubles (all keys miss). Mitigation options: (a) Snapshot on shutdown, restore on startup (30s-5min); (b) Replay access log from Kafka/binlog (warms key subset but slow); (c) Gradual traffic ramp (10-30 min to full QPS, DB handles miss surge) [12]. Production choice depends on DB capacity and tolerable miss spike.

**Database overload bound**: On cache cluster loss, all traffic goes to DB. Peak write load = N clients × request rate. Bound it via: (1) Request coalescing (single-flight): multiple clients waiting for same key result in 1 DB query. Reduces load by up to 10x. (2) Per-key rate limit: client-side or proxy-side, limit QPS per key to DB (e.g., 100 QPS per key). (3) Load shedding: if DB latency > threshold, reject new cache misses to keep DB responsive [12]. Combination is typical: singleflight + 100 QPS/key rate limit + shed excess. Facebook leases reduce this from need (13x reduction in peak) [12].

## 7. Invalidation and Consistency

**Cache-aside with delete-on-write**: Classic pattern. (1) Write new value to DB, (2) delete key from cache. On cache miss, read from DB and populate cache. Simple but exposes stale-set race: if step 2 completes, then old async write (from a stale client thread) reaches cache after the delete, cache now holds stale data until TTL. Facebook's lease mechanism fixes this: delete invalidates the lease token, so stale writes are rejected [12].

**CDC-driven invalidation (Debezium)**: Capture database changes via binlog/WAL (CDC = Change Data Capture). Debezium extracts these changes, publishes to Kafka topic. Consumer listening on topic invalidates cache entries affected by each change. Advantages: no code changes to application, invalidation is real-time and reliable. Latency: 10-100 ms from DB commit to cache invalidation [14]. Disadvantages: operational overhead (Debezium cluster, Kafka), change event parsing.

**Versioned keys / compare-and-swap**: Memcached gets/cas: get returns token, cas(key, token, value) succeeds only if value's token matches current. Redis WATCH/MULTI/EXEC: WATCH key, MULTI starts transaction, if key changes, EXEC aborts. Prevents lost updates in concurrent scenarios [8, 9]. Cost: extra latency per operation, CAS retries on collision.

**Write-through vs write-behind**: Write-through: update cache, then DB. Client waits for both. Strong consistency but higher latency (2x DB latency). Write-behind: update cache, return to client, asynchronously flush to DB. Lower latency but risk of loss if cache node crashes before flush. Hybrid: write-through for critical data, write-behind for non-critical (e.g., analytics events) [12].

**Read-your-writes across regions (Netflix EVCache)**: After a write to local region cache, subsequent reads in same region see the write immediately (eventual consistency within region). Problem: user travels to different region, reads old cache from old region. Solution: remote markers. Write sets a version marker in all regions (low-latency marker, not data). Read checks marker before accepting stale cache value. If local cache is older than marker, re-fetch from DB or wait for replication [13].

**Consistency bounds in cache-aside**: Staleness is at most max(TTL, time-to-invalidate-message). With TTL=300s and invalidation delay=10s, worst-case stale age is 310s. With immediate async invalidation (CDC), staleness is just CDC delay (10-100 ms) [14]. Strong consistency (no stale reads) requires WAIT + quorum + versioning (e.g., WATCH/MULTI) but costs 2-5x latency [8, 12].

## 8. Network and Client Path

**Connection pooling**: N application clients × M cache nodes = N*M TCP connections. Typical pool size 1-4 connections per client per node; using 10+ causes overhead. Each connection has overhead (kernel buffers, connection tracking). Proxy pattern (mcrouter, twemproxy, Envoy) consolidates: many clients connect to 1 proxy instance, proxy maintains M connections to cache cluster (M << N*M). Proxy adds 1-5 ms latency but reduces connection pressure [12].

**Proxy vs smart client**: Proxy (centralized): cache cluster topology change only requires proxy update; easier operations. Drawback: latency spike if proxy saturates (typical ~50k concurrent conns max). Smart client (consistent hash locally in SDK): clients route directly to nodes; topology change requires client library update and rolling restart of all services. Tradeoff: Netflix uses smart client + Kafka for topology changes to avoid proxy bottleneck [13].

**Pipelining and multiget batching**: Pipeline 10 operations (send 10 commands, collect 10 responses) achieves ~800k ops/sec for Redis, ~750k for Memcached on 1 Gbps link [16]. Batching amortizes network RTT (1-5 ms). Cost: higher latency for individual request (batches wait for batch fill). Typical batch size: 10-100 keys [9, 16].

**TCP incast on multiget**: Client sends get(key_1, key_2, ..., key_N) to N different cache nodes in parallel. All N nodes respond simultaneously within 10-100 microseconds. Switch port buffer (typically 10-100 MB) can overflow on fan-out to many nodes (>100 nodes). Packets drop, TCP retransmit timeout (100+ ms), stalls request. Solutions: (1) Sliding-window: client limits concurrent requests to ~10-50 to cap inbound peak. (2) Data center TCP (DCTCP): uses ECN (Explicit Congestion Notification) instead of packet loss for congestion signal. Allows fine-grained rate control [9].

**Hedged requests**: Send request to N cache nodes in parallel; return first non-error response. Reduces tail latency (p99, p999) but costs N*throughput. E.g., hedge to 2 nodes doubles throughput cost, halves p99 latency. Used at Google, Netflix for critical paths [12].

## 9. Serialization and Value Encoding

**Compression threshold**: Compress values >= 1 KB (typical threshold). Smaller values: compression overhead (10-30 bytes header) exceeds savings. Savings: 30-60% for JSON/text (compresses well). Cost: CPU (1-5 ms per 100 KB), latency spike on first request. Strategy: compress on write (async, batch compress cold values) [9]. Typical savings: 100 MB cache becomes 40 MB after compression.

**Large value cost**: 1 MB value at 10 Gbps takes 0.8 ms to transmit on one connection. 10 MB takes 8 ms. On pipelined connection with small + large values, large value delays small ones (head-of-line blocking). Example: 10 Gbps link, 1 KB small value (0.0008 ms), 10 MB large value (8 ms): small value stalled behind large value, p99 latency jumps from 1 ms to 10 ms [9, 16].

**Separate large-value pools**: Run two cache clusters: small-value (< 100 KB) and large-value (>= 100 KB). Route small-value requests to fast cluster (fewer large items, lower p99). Large-value cluster can have different config (e.g., bigger cache nodes, replication for resilience). Netflix, Google use this pattern for analytics and blob data [9, 16].

**Encoding choices**: Protocol buffers or msgpack: compact, ~2-4x smaller than JSON, but not human-readable (harder to debug). JSON: larger (3-5x msgpack) but debuggable, human-readable in logs. Compression: gzip or brotli reduces JSON to msgpack size but adds CPU. Typical decision: msgpack for hot data (many requests), JSON for cold data (rare reads), compression for large values [16].

**Encoding size comparison**: 1000 integers as JSON array = 10 KB, msgpack = 2 KB, gzip JSON = 1.5 KB. Cache 100k entries of 1000 integers: 1 GB JSON, 200 MB msgpack, 150 MB gzip JSON. Compression is worth it above ~10 KB per value [9, 16].

**Protocol choice (Memcached binary vs ASCII vs Redis RESP)**:
- Memcached ASCII: human-readable, debugging-friendly, ~15% overhead (text headers). Deprecated.
- Memcached binary: compact headers, pipelined efficiently, required for advanced features (SASL, CAS). 10% overhead.
- Redis RESP: text-based but compact, supports pipelining. Newer RESP3 supports streaming and sets.
- gRPC or Thrift: protocol buffers, compact, requires code generation. Rarely used for cache due to latency.

## Numbers to Reuse in the Design

**Single-node performance**:
- Redis single-thread ops/sec: ~200k GETs (1 KB values), ~100k SETs with fsync [16]
- Memcached multi-thread (8 cores) ops/sec: ~150k GETs, ~130k SETs [16]
- Per-core throughput: Memcached ~20k ops/sec/core, Redis ~200k single-threaded (I/O bound) [16]
- Pipelined (10 ops per batch): ~800k ops/sec Redis, ~750k Memcached [16]
- Hedged requests: send to 2 nodes in parallel, 50% latency reduction, 2x throughput cost [12]

**Eviction and memory**:
- Vnodes per node: 100-200 (Dynamo standard); 40 (Ketama), 150-256 (production sweet spot) [17, 18]
- Consistent hashing load imbalance: 5-10% with 100 vnodes; 20% with 40 vnodes [1, 18]
- Bounded loads c factor: 1.25 → max-load = 2*ln(n) keys/node; only 1/(n+1) fraction move on node add [3]
- S3-FIFO miss ratio reduction: up to 72% vs LRU on 14 datasets [6]
- SIEVE vs ARC: 63.2% reduction on 10% of test traces; mean 1.5% reduction [7]
- W-TinyLFU hit-rate improvement: 2-5% over LRU on production traces [5]
- Memcached max item: 1 MB default; growth factor 1.25 per slab class [9]
- Memcached memory fragmentation: typically 10-20% waste with default growth factor [9]
- Redis maxmemory-samples: default 5; 10 approaches true LRU; 100 is nearly perfect [8]

**Failure and recovery**:
- Redis cluster-node-timeout: 15,000 ms default; 5-10s for LAN, 15-30s for cloud [8]
- Facebook leases: DB QPS reduced from 17,000 to 1,300 on cache stampede (13x reduction) [12]
- Lease token validity: 10 seconds per key [12]
- CDC invalidation latency (Debezium): 10-100 ms from DB change to cache invalidation [14]
- Cache cold-start miss rate: 2x nominal miss rate for first 30 minutes [12]

**Consistency and replication**:
- Redis async replication lag: 10-100 ms typical; up to seconds under load [8]
- WAIT command: blocks until N replicas ACK; still not crash-safe on leader death [8]
- Netflix EVCache async replication via Kafka: eventual consistency within region [13]
- Memcached lease overhead: <1% on throughput; huge reduction in DB load [12]

**Networking**:
- TCP incast buffer: switch port buffers typically 10-100 MB; 1 Gbps = 100 MB/sec [9]
- Multiget fan-out: cap concurrent requests to ~10-50 to avoid incast [9]
- Connection pool size: 1-4 per client per node; Proxy can handle ~50k concurrent connections [12]
- Proxy latency overhead: 1-5 ms added [12]

## Additional Technical Considerations

**Vnode imbalance under heterogeneous nodes**: Dynamo's solution: assign more vnodes to faster/larger nodes. E.g., 2x capacity node gets 2x vnodes. Load imbalance formula: standard deviation of keys per node is O(sqrt(keys/vnodes)); with 100 vnodes and 1M keys, ~sqrt(1M/100) = 100 keys difference between most and least loaded vnode. Practical impact: 5-10% load imbalance [17].

**Consistent hashing with token bucketing**: Some systems use ranges instead of points. E.g., Cassandra: each token represents a range of keys. Reduces hash collisions on key space, improves distribution. Complex to implement, rarely needed [1].

**Multiget optimization in protocol**: Memcached binary protocol supports pipelined get commands efficiently (minimal header per command). Redis lacks efficient multiget in some versions; newer Redis uses MGET. Tcpdump: watch for command bundling to see pipeline utilization [9].

**LFU decay tuning**: Redis lfu-decay-time=1 (default) decreases counter every 1 minute of inactivity. Setting to 10 (10 minutes) keeps old items "fresh" longer; useful for daily batch jobs. Setting to 1 captures bursty traffic better [8].

**Slab reassignment in Memcached**: When reassigning a slab page from class A to class B, all items in that page are evicted (data loss). Must run during low-traffic window. Automove feature automatically reassigns after threshold (e.g., if class X hits memory limit 3 times, borrow from another class) [9].

**Redis persistence and cache loss**: AOF (append-only file) and RDB (snapshot) write to disk; cache durability is not a use case. All Redis data is volatile by default; SAVE is slow (blocks all clients). For cache, disable persistence entirely [8].

**Proxy topology in Consistent Hashing**: If proxy crashes (e.g., mcrouter), clients must reconnect to backup proxy. During transition, some keys may rehash (if proxy didn't forward topology consistently). Workaround: client library caches topology hash, recomputes only on mismatch [12].

## Operational Gotchas and Common Mistakes

**Key placement**: Consistent hashing with too few vnodes (< 50) creates 30-50% load imbalance. Adding a node causes >1% of keys to rehash (noticeable spike). Jump hash cannot remove arbitrary nodes; only add at end.

**Replication**: Async replication leads to stale reads (100+ ms behind master). WAIT command does NOT survive master crash. Setting min-replicas-to-write is often misunderstood: it only blocks writes if replicas are down, not if they're lagging.

**Eviction**: Sampling-based LRU (maxmemory-samples=5) evicts recently accessed items 10-30% of the time. LFU mode can cause eviction of bursty-accessed items (e.g., daily batch job) immediately after job ends. Memcached slab page cannot be rebalanced; growth factor < 1.1 creates too many classes.

**Memory**: Large values (> 1 MB) in Redis cause single-threaded event loop to stall 1+ ms per request, increasing tail latency. Memcached slab calcification: if item size distribution shifts (many small items instead of large), waste becomes permanent without slab automove.

**Hot keys**: Detection via LFU counter scan is expensive (full keyspace scan). Replication on suffix keys adds memory (2x for duplication) and write complexity. Lease tokens must be managed: leases can accumulate if delete() fails.

**Failure detection**: False-positive node failures during network blips cause thrashing and cache loss. cluster-node-timeout too short (5s) increases false positives. Too long (30s) delays failover.

**Invalidation**: Cache-aside is susceptible to stale-set race without leases or versioning. CDC invalidation adds 10-100 ms latency (not suitable for cache-through). Versioning (WATCH/CAS) requires retry loops and can cause livelock under high contention.

**Network**: Proxy becomes bottleneck at 50k+ concurrent connections. Smart client requires topology change broadcasts (complexity and operational burden). TCP incast causes complete connection stall at >100 nodes; not obvious without packet-level analysis.

**Serialization**: Large values (10+ MB JSON) in cache defeat compression benefits; store only compressed binary. Compression threshold too low (< 100 bytes) wastes CPU. Off-the-shelf protocols (protobuf) are 2-4x smaller but less debuggable than JSON.

## Spot-Check List (8 numbers to verify if skeptical)

1. S3-FIFO 72% miss ratio reduction: verify against Yang et al SOSP 2023 paper tables, specific test traces (e.g., F1, Zipf-heavy traces) [6]
2. Memcached 150k GETs/sec vs Redis 200k: antirez blog benchmark uses 1 KB values, 8 Memcached threads, single-threaded Redis, same hardware [16]
3. Dynamo 100-200 vnodes per node: Amazon Dynamo paper §3.3 "Ring Topology", mentions N (number of vnodes) = 128 for balanced distribution [17]
4. Ketama 40 vnodes = 160 hash ring points: each vnode MD5-hashed 4 times per iteration; source: libketama.h / consistent.c [18]
5. Facebook leases 17k to 1.3k QPS reduction: NSDI 2013 paper "Scaling Memcache at Facebook", Figure 10, peak DB query rate, lease mitigation [12]
6. Bounded loads c=1.25: Mirrokni et al 2016 abstract states c = 1.25 factor, max-load = c * ln(n); theorem 1 [3]
7. Redis maxmemory-samples=5 default: redis.conf and redis.io/docs/latest/topics/lru-cache mention samples=5, 10 for better accuracy [8]
8. Memcached 1 MB item limit rationale: release notes 1.4.29+ remove 1 MB hard limit but warn if > 1 MB; GitHub discussions mention overhead of large items [9]

---

## Spot-check corrections (added after fetching the primary sources myself, 2026-09-17)

| Claim in this survey | What the source actually says | Where |
|---|---|---|
| "S3-FIFO: 72% miss ratio reduction vs LRU" | 72% is the **median one-hit-wonder ratio** on sequences covering 10% of unique objects, not a miss-ratio delta. The headline result is: "S3-FIFO reduces miss ratios [vs FIFO] by more than 32% on 10% of the traces (P90) with a mean of 14% on the large cache size" | SOSP 2023 PDF, abstract and §5 |
| TinyLFU always beats LRU | S3-FIFO paper: TinyLFU's "miss ratios being lower [worse] than FIFO on almost 20%" of the 6,594 traces. W-TinyLFU is strong on frequency-skewed traces and not robust everywhere | SOSP 2023 PDF, §5 |
| W-TinyLFU window size | 1% window, 99% main, SLRU main split 80% protected / 20% probation, per Caffeine 2.0 as described in the paper; a 20% window was slightly better on some traces | arXiv 1512.00727, §4 and §5 |
| Bounded loads "max-load = c × ln(n)" | Wrong formula. The paper's guarantee is no bin above `ceil(c × m / n)`, i.e. `c` times the average load, with `c = 1 + epsilon`; `c = 1.25` is the value Vimeo found satisfactory | arXiv 1608.01350, §1 |
| Facebook leases 17k to 1.3k | Confirmed: peak DB query rate 17K/s without leases, 1.3K/s with | NSDI 2013 PDF, §3.2.1 |
| XFetch `beta = 1` default | Confirmed: `if !value or Time() - delta × beta × log(rand()) >= expiry then recompute`; beta defaults to 1 | Vattani et al. VLDB 2015 PDF, Algorithm 1 |
| memcached growth factor 1.25, 1 MB item max | Confirmed in `memcached.c`: `settings.factor = 1.25`, `settings.item_size_max = 1024 * 1024`; also `slab_chunk_size_max = slab_page_size / 2` (512 KB), so items above 512 KB are stored as chained chunks | github.com/memcached/memcached `memcached.c` lines 231 to 242 |
| Redis defaults | Confirmed in `redis.conf` (unstable): `maxmemory-samples 5`, `cluster-node-timeout 15000`, `lfu-log-factor 10`, `lfu-decay-time 1`, `cluster-require-full-coverage yes` | github.com/redis/redis `redis.conf` |
