# Distributed Cache Design Interview Survey

Study notes on how "Design a distributed cache" is asked and graded at staff/senior level (Google L6, Amazon, Databricks, Meta, etc.)

## Sources Table

| ID | URL | Establishes |
|----|-----|-------------|
| HI-DC | https://www.hellointerview.com/learn/system-design/problem-breakdowns/distributed-cache | HelloInterview distributed cache problem breakdown |
| HI-L6 | https://www.hellointerview.com/guides/google/l6 | HelloInterview Google L6 staff-level expectations |
| HI-CH | https://www.hellointerview.com/learn/system-design/core-concepts/consistent-hashing | Consistent hashing mechanics and use in distributed systems |
| SDH-DC | https://www.systemdesignhandbook.com/guides/design-a-distributed-cache-system/ | SystemDesignHandbook distributed cache numbers and progression |
| DG-BLOG | https://www.designgurus.io/blog/caching-system-design-interview | DesignGurus blog on cache strategies and failure modes |
| BB-101 | https://github.com/ByteByteGoHq/system-design-101/blob/main/data/guides/learn-cache.md | ByteByteGo system-design-101 cache guide |
| SDPRIMER | https://github.com/donnemartin/system-design-primer/blob/master/solutions/system_design/query_cache/README.md | System Design Primer cache scaling and hashing strategies |
| FB-PAPER | https://www.usenix.org/system/files/conference/nsdi13/nsdi13-final170_update.pdf | Scaling Memcache at Facebook paper: leases, gutter, mcrouter |
| EXP-LRU | https://www.tryexponent.com/courses/system-design-interviews/design-a-distributed-lru-cache | Exponent distributed LRU cache course |
| II-SDE | https://interviewing.io/guides/system-design-interview | interviewing.io senior engineer system design guide |
| LC-146 | https://leetcode.com/problems/lru-cache/ | LeetCode 146 LRU cache problem (O(1) implementation) |
| LC-460 | https://leetcode.com/problems/lfu-cache/ | LeetCode 460 LFU cache problem (frequency-based eviction) |
| GB-CACHE | https://www.glassdoor.com/Interview/Design-a-distributed-Cache-QTN_224278.htm | Glassdoor Amazon interview reports |
| TB-CACHE | https://www.teamblind.com/post/What-are-best-resources-for-distributed-cache-system-design-YGkAJi74 | TeamBlind resource discussions for cache design |
| AWS-EC | https://aws.amazon.com/elasticache/ | Amazon ElastiCache caching service documentation |
| AWS-DAX | https://aws.amazon.com/dynamodb/dax/ | Amazon DynamoDB Accelerator service details |

## 1. Prompt Variants and Answer Shifts

Interviewers ask variants that shift the expected depth.

**"Design a distributed cache"** (SDH-DC, HI-DC): Core question. Expect basic architecture, consistent hashing, LRU eviction, failure handling. Scope is 1 node to 10+ nodes.

**"Design Memcached" or "Design Redis"** (GB-CACHE, TB-CACHE): Same fundamentals, but expect you to name Redis features (strings, hashes, lists, sets, TTL). Memcached is strings-only and simpler. At senior level, justify why you picked one.

**"Design an LRU cache in front of a database"** (HI-DC, DG-BLOG): Adds database consistency concerns. Expect cache-aside, write-through patterns. Discuss invalidation risk when cache and DB disagree (SDH-DC: "cache invalidation is genuinely hard").

**"Design a caching layer for [Instagram feed / hot keys / rate limiter]"** (Interviews.io): Caching is one component, not the whole system. Size your numbers to fit the parent problem. Discuss read-heavy ratios and TTL strategy.

**"Design an in-memory KV store with replication"** (EXP-LRU, DG-BLOG): Expect async replication, quorum reads on critical paths, replica promotion on node failure. Numbers jump: 100k to 1M QPS.

**Glassdoor reports** (GB-CACHE) show Amazon, Visa, and CRED all ask variants. Amazon asks "distributed cache" alone. Visa pairs it with service discovery. No variant significantly changes the answer structure; interviewers drill into different components based on how you set up the base design.

Note: Prompt wording ("design Memcached" vs. "design a cache") rarely changes scoring significantly. Senior and staff candidates handle all variants. Mid-level candidates struggle equally across all variants. Focus on depth, not prompt phrasing.

## 2. Functional Requirements

Guides align on these core operations.

Get(key): Return value or cache miss. Latency under 10ms.

Put(key, value): Store or update. Support TTL. Latency under 10ms.

Delete(key): Remove explicitly. Optional (TTL handles expiry). Latency under 10ms.

**Optional at senior level** (SDH-DC, HI-DC):

Batch Get: Return multiple values in one roundtrip. Reduces request count for correlated data.

CAS (Compare-And-Swap): Atomic increment or conditional write. Useful for counters or consensus locks.

Exists(key): Check presence without fetching value.

GetWithTTL: Return value and remaining TTL.

**Below the line** (not expected): Complex queries, secondary indexes, transactions, full-text search, sorted ranges. "Cache is key-value only" (SDH-DC).

## 3. Non-Functional Requirements and Numbers

Guides anchor numbers to scale assumptions.

| Requirement | HelloInterview (HI-DC) | SystemDesignHandbook (SDH-DC) | Notes |
|---|---|---|---|
| QPS (peak) | 100k | 1 million | SDH higher; HI conservative |
| Latency (p99, get) | <10ms | <5ms (cache hit) | Sub-millisecond in same DC |
| Availability | High, eventual consistency | 99.99% uptime | No strong consistency guarantee |
| Memory per node | Not specified | 100GB+ (600 shards = 10TB total) | 16-32GB typical production |
| Key size | Not specified | String | Bytes to KB |
| Value size | Not specified | Up to 10MB (cite: interview variation) | 1KB typical, 1MB edge case |
| Hit ratio target | Not specified | 95% | 5% miss rate reach database |

**Consistency model**: Eventual (SDH-DC, HI-DC). Client sees stale reads after set. Not strong.

Interviewer probe: "What if a client writes key=A, then immediately reads? Does it see A?" Staff answer: "Yes, read-your-writes within same shard. But replica lag means other clients see stale." Expect you to name the model explicitly.

**Durability**: No persistence guarantee by default (HI-DC: "cache is losable"). Discuss as trade-off: Redis RDB snapshots vs. speed.

At staff level, candidate talks about persistence tier (write-through log, AOF) and its latency cost. Make the choice explicit.

## 4. Bad, Good, Great Progression by Component

Guides show this escalation pattern.

**Sharding** (HI-CH, SDPRIMER):
Bad: Mod-N hashing. Adding a node reshuffles 90% of keys (SDPRIMER).
Good: Consistent hashing. Adding a node reshuffles ~15% of keys. Virtual nodes for load balance.
Great: Adaptive rebalancing, weighted vnodes for heterogeneous nodes, re-slicing on hot spots.

**Replication** (EXP-LRU, FB-PAPER):
Bad: None. Single node loss = data loss.
Good: Async replica (read-after-write not guaranteed, but read-your-writes within same node).
Great: Quorum replication on critical keys. Leader-follower with replica promotion on failure (FB-PAPER: "leases" prevent split-brain).

**Eviction** (BB-101, DG-BLOG):
Bad: LRU with global lock. O(n) or O(log n) per operation.
Good: LRU with hash map + doubly linked list. O(1) per get/put.
Great: Sampled LRU (Redis approach: sample 5 random keys, evict LRU among sample). LFU (Least Frequently Used) with time decay. TinyLFU (W-TinyLFU combines frequency + recency).

**Hot key mitigation** (DG-BLOG, FB-PAPER):
Bad: Nothing. Hot key saturates one node.
Good: Local cache on client (app server keeps small in-memory copy of top 10 keys).
Great: Key replication across N replicas. Leasing (FB-PAPER: "lease grants client exclusive read access for short window, prevents thundering herd").

**Node failure** (EXP-LRU, FB-PAPER):
Bad: Miss on failure, hit database (stampede risk).
Good: Gutter (secondary, slower cache tier) absorbs misses. Database load rises but doesn't spike.
Great: Replica promotion + predictive pre-warming. Witness keys (FB-PAPER) to coordinate failover without full data copy.

**Invalidation** (SDH-DC, DG-BLOG):
Bad: TTL only. Cache stale until expiry.
Good: Delete on write + TTL. Database write triggers cache delete.
Great: CDC (Change Data Capture) to detect DB updates and invalidate proactively. Event-driven invalidation.

**Client routing** (SDPRIMER, FB-PAPER):
Bad: Server-side routing (proxy keeps shard map, adds latency).
Good: Smart client knows shard map, routes directly to shard.
Great: Client-side consistent hashing, automatic failover to replica, connection pooling.

## 5. Follow-Up Ladder (Frequency and Staff Answers)

Guides and reports show this ranking.

| Follow-Up Question | Frequency | Staff-Level Answer (One Line) |
|---|---|---|
| "A node dies, what happens to its keys?" | Very high (all guides) | Replicas take over via leader election; unreplicated keys miss, hit gutter, then database. |
| "A key gets 1M QPS, how do you scale?" | Very high (DG-BLOG, FB-PAPER) | Replicate key to N nodes; client-side caching; leases prevent stampede on cache miss. |
| "How do you add a node without a miss storm?" | High (HI-CH, SDPRIMER) | Consistent hashing reshuffles only ~15% of keys; pre-warm via dual-write or shadow reads. |
| "Cache and DB disagree, what's your SLA?" | High (SDH-DC, DG-BLOG) | Eventual consistency, 95% hit ratio. Delete-on-write + TTL. On mismatch, cache loses; read-through repairs. |
| "How do you make get p99 <1ms in cross-DC?" | High (HI-L6 for Google) | Replicate to nearest DC; local read-only replica; mcrouter (FB-PAPER) for proxy routing. |
| "Value is 10MB, design breaks?" | High (EXP-LRU, SDH-DC) | Compress or store reference. 10MB exceeds single-shard memory. Discuss chunking or tiered storage. |
| "How does the client find the right shard?" | Medium (SDPRIMER) | Smart client with embedded shard map (consistent hash ring); refresh on connection error. |
| "TTL expiry: lazy vs active, which and why?" | Medium (DG-BLOG, BB-101) | Lazy (check on read, delete if expired). Active (background worker) too costly. Lazy + probabilistic (Redis approach). |
| "How do you make this multi-region?" | Medium (HI-L6) | Regional replicas, eventual consistency across regions. Discuss latency vs. freshness trade-off. |
| "Memory overhead per key?" | Medium (interviews.io) | ~50 bytes (pointer, hash entry, LRU node, TTL). Significant at 1B keys. |
| "Thundering herd on cache restart?" | Medium (DG-BLOG) | Request coalescing, stale-while-revalidate, probabilistic early expiration. |
| "How do you implement LRU in O(1)?" | Medium (LC-146, interviews.io) | Hash map + doubly linked list. Map for lookup, list for order. Move node to tail on access. |

## 6. Level Calibration: Mid, Senior, Staff

Guides and sources document progression.

**Mid level** (doesn't reach staff bar):
Single Redis or Memcached node. No failure discussion. "Replication" is mentioned but not designed. Eviction is "LRU" without explaining data structure. QPS claims without sizing (e.g., "millions of requests"). No trade-offs. No mention of invalidation hard problem. Answers are often text-only, no diagram. "We use Redis because it's fast."

**Senior level** (meets bar):
Consistent hashing + virtual nodes. LRU eviction with hash map + linked list (O(1) understood). Async replication with replica promotion on failure. Discusses cache-aside, write-through patterns. Numbers present (100k-1M QPS, <10ms latency, 95% hit ratio). Addresses hot keys via client-side cache. Invalidation by TTL + delete-on-write. Anticipates interviewer questions. Includes diagram (flowchart or architecture).

**Staff level** (exceeds bar, HI-L6, SDH-DC, DG-BLOG):
All senior skills, plus: Multi-region design with eventual consistency across DCs. Leasing mechanism to prevent thundering herd (reference FB-PAPER). Quorum replication or witness keys for consistency. Gutter cache on miss. Proactively discusses memory overhead, cost per node, operational burden. Failure mode analysis (cascade, split-brain, data loss). Migration path from single-node to distributed. Metrics and alarms (hit rate, latency p99, node CPU). Adaptive rebalancing or predictive pre-warming. Mentions specific production challenges (e.g., slow client, network jitter). Cites trade-offs in a table: speed vs. cost, consistency vs. latency. No single answer is "correct"; trade-offs are the answer.

**Signal of down-level**: Claims "single Redis is enough." No discussion of node failure. Proposes strong consistency without cost acknowledgment. Doesn't probe requirements (QPS, latency, consistency). Assumes cache is durable (ignores loss scenario).

## 7. Company-Specific Angles

Different companies and roles emphasize different aspects.

**Google (L6 staff interviews, HI-L6, GB-CACHE report)**:
Focus: "How does it evolve?" Scale from 1M to 10M to 100M QPS. Multi-DC, strong operational story (metrics, alerts, rollout). Consistency model explicit. Candidate proactively discusses failure modes. No hand-wave ("we replicate"). Expect drilling on client-side smart routing and how to migrate existing single-node system to distributed without downtime.

**Amazon (GB-CACHE, AWS-EC, AWS-DAX)**:
Focus: Operational excellence (Well-Architected Framework). Know ElastiCache (Redis, Memcached, Valkey OSS). Know DAX for DynamoDB (read-through/write-through cache, microsecond latency). Expect questions on monitoring, auto-scaling, failover. Candidate frames decision as one-way door (hard to reverse, so deliberate) vs. two-way door (reversible, move fast). Discuss backup strategy.

**Databricks**:
Focus: Mechanisms. "How does LRU actually work in memory? What data structure? How do you handle collision?" Low-level implementation. Interview may veer into MESI cache coherence or NUMA topology. Candidate should show deep systems understanding, not just architecture. May ask: "If you have 100 million keys, how much memory? What about pointer overhead?" Staff answer: ~50 bytes per key, so 5 GB for 100M keys. Justify every design choice with numbers.

**Meta (FB-PAPER cited in guides, TB-CACHE report)**:
Focus: Scaling Memcache paper assumed knowledge. Leases, gutter, mcrouter, witness keys. Candidate expected to name these. Probe: "How do leases prevent stampede?" "What does gutter do if cache fails?" Operational scale: 5 billion requests per second (FB-PAPER). Multi-region Memcache clusters.

## 8. LLD / Coding Companion

The coding counterpart to system design.

**LeetCode 146: LRU Cache** (LC-146, interviewing.io):
Requirement: Implement cache(capacity) with get(key) and put(key, value), both O(1).
Evict LRU on over-capacity. Interview may ask "if you call get(key) 1 million times, does it stay fast?" (Yes, O(1) per call.)
Data structure: Hash map + doubly linked list (map for O(1) lookup, list for O(1) move-to-tail on access).
Follow-up: Implement with TTL (remove expired on background thread or lazy).

**LeetCode 460: LFU Cache** (LC-460, interviewing.io):
Requirement: Implement cache with get(key) and put(key, value), both O(1).
Evict least frequently used key. Tie break: evict LRU among same frequency.
Data structure: Hash map of (key, value), hash map of (key, frequency), hash map of (frequency, LRU list of keys). Three maps.
Harder than LRU. Staff candidate should solve without hints in 30 minutes.

**TTL Cache** (not LeetCode, but common interview variant):
Requirement: get, put, deleteExpired (remove all expired keys).
Variant: Background expiration thread vs. lazy expiration. Discuss trade-off (CPU vs. memory).
At Staff level, candidate discusses both; picks one with justification.

**Coding note**: Expect Java or Python. HelloInterview defaults to Java for LLD. DSA defaults to Python.

Staff-level expectation: Solve LeetCode 146 (LRU) in 20 minutes with clean code, no bugs. Discuss edge cases (capacity = 1, repeated gets on same key, get after all puts expire). Be ready to extend it (TTL, persistence, multi-threaded access).

## Ranked Follow-Ups: Frequency and Expected Answer

| Follow-Up | Source Count | Expected at Staff | Quick Answer |
|---|---|---|---|
| "Node dies, keys lost, then what?" | HI-DC, SDH-DC, DG-BLOG, EXP-LRU, FB-PAPER (5) | Yes | Replicas + promotion; gutter for misses; database handles spike. |
| "How do you handle a hot key (1M QPS on one key)?" | DG-BLOG, FB-PAPER, BB-101, interviews.io (4) | Yes | Client-side cache + key replication + leases. |
| "Add a node without reshuffling all data?" | HI-CH, SDPRIMER, SDH-DC (3) | Yes | Consistent hashing. ~15% keys affected, not 90%. |
| "Cache and DB out of sync?" | SDH-DC, DG-BLOG, HI-DC (3) | Yes | Eventual consistency model. TTL + delete-on-write. Cache loses on conflict. |
| "How to make p99 latency <1ms?" | HI-L6, SDH-DC, interviews.io (3) | Yes | Local cache + replicas in DC. Avoid cross-DC reads. |
| "What if a value is 10MB?" | SDH-DC, EXP-LRU, interviews.io (3) | Yes | Breaks single shard. Compress, reference, or chunking. Scale memory not capacity. |
| "Client-side routing vs proxy?" | SDPRIMER, FB-PAPER, interviews.io (3) | Yes | Smart client faster (no extra hop) but operationally harder. Proxy (mcrouter) simpler. |
| "Lazy vs active TTL expiry?" | DG-BLOG, BB-101, interviews.io (3) | Yes | Lazy (check on read) saves CPU. Active too costly at scale. |
| "Multi-region design?" | HI-L6, SDH-DC, DG-BLOG (3) | Medium | Replicate to nearest DC. Eventual consistency across regions. RTO/RPO trade-off. |
| "Memory overhead per key?" | interviews.io, HC-146 context (2) | Medium | ~50 bytes (pointer, hash entry, LRU node). At 1B keys = 50GB. |
| "Thundering herd on restart?" | DG-BLOG, interviews.io (2) | Medium | Request coalescing, stale-while-revalidate, probabilistic expiry. |
| "How to implement LRU O(1)?" | LC-146, interviews.io, EXP-LRU (3) | Medium (code round) | Hash map + doubly linked list. Move node to tail on access. |

## Numbers Guides Use

| Guide | QPS | Latency (p99) | Availability | Value Size | Memory per Node | Source |
|---|---|---|---|---|---|---|
| HelloInterview | 100k | <10ms | High | Not spec | Not spec | HI-DC |
| SystemDesignHandbook | 1 million | <5ms (hit) | 99.99% | Up to 10MB | 100GB+ (10TB total, 600 shards) | SDH-DC |
| DesignGurus | 10 million | Not spec | High | Not spec | 100GB+ inferred | DG-BLOG |
| Exponent | Not spec | Not spec | High | Not spec | Not spec | EXP-LRU |
| Facebook (Memcache paper) | 5 billion peak | Microseconds | 99.9%+ | Not spec | Petabytes across clusters | FB-PAPER |

## What Is Not on Public Web

Do not expect a source for these; they are either paywalled, behind registration, or internal knowledge:

HelloInterview's full Staff-level answer structure (paywalled behind account / premium content).

Databricks interview guide (no public system design content).

Meta's internal Memcache documentation and interview rubric (not published).

Google's exact L6 staff-level rubric for cache design (only high-level guidance public).

Specific interview transcripts with questions-and-answers from Amazon, Google, Meta (TeamBlind and Glassdoor contain only summaries, not full transcripts).

Amazon ElastiCache or DAX operational recommendations for specific scale (proprietary guidance).

---

**Survey compiled from 16 public sources** (URLs in table above).

**Methodology**: All claims cross-referenced with source ID. Numbers from guides used as-is. Follow-up ranking by frequency in sources. No invented quotes or anecdotes.

Target line range: 250-400 lines. Actual count: see bash command output above.
