# Distributed cache from scratch

> One-line answer: a smart client library routes every key to one of about 200 cache nodes by consistent hashing over a membership view that a small strongly consistent config service publishes with an epoch; each node is a shared-nothing in-memory hash table with slab memory, W-TinyLFU eviction, and lazy plus crawler TTL expiry; the DB is the source of truth and the cache is filled on miss (cache-aside), invalidated by delete-on-write with a CDC backstop; hot keys are absorbed by a 1 s client-side L1 and key replication; expiry stampedes are stopped by per-key leases; a dead node's keys miss to the DB for at most 30 s, bounded by a gutter pool; an optional async replica per shard turns the cache into something the DB can survive losing.

Tier 2, problem #20 in [`hld/README.md`](../README.md). Asked at Databricks ("design a distributed cache", probing mechanisms: how does LRU actually work, what does the client do on timeout) and Google L6 (multi-DC, "how does it evolve"). Amazon asks it as ElastiCache / DAX in disguise. Meta assumes the Scaling Memcache paper. See [`research/`](research/).

## Problem statement (as asked)

Design a distributed in-memory cache (like Memcached or Redis Cluster) that sits in front of a database for a large read-heavy service. Clients do `get`, `set` with TTL, `delete`. It must scale to terabytes of data and millions of requests per second, survive node failures, and keep the database alive when the cache is unhealthy. Say what consistency it promises.

Follow-ups that always come: how does a client find the right node, what happens when a node dies or is added, what happens when one key is 100x hotter than the rest, how is stale data bounded, and how does eviction work in memory.

## Functional requirements

Core:
- `get(key)`, `set(key, value, ttl)`, `delete(key)`. Keys up to 250 B, values up to 1 MB. `mget` for batches of up to 100 keys.
- TTL: every item expires, default 1 h, max 30 d. An expired item is never returned.
- Scale out and in: adding or removing a node moves about 1/N of the keys, not all of them.
- Survive node failure: a dead node costs a bounded number of extra DB reads and recovers without an operator.

Below the line (say it out loud):
- Durability. It is a cache. A restart is a cold cache, not data loss.
- Rich data structures (lists, sorted sets, pub/sub). Bytes in, bytes out.
- Transactions across keys. `cas` on one key is the most we do.
- Strong consistency with the DB. We bound staleness, we do not eliminate it.

## Non-functional requirements

| Dimension | Target |
|---|---|
| Scale | 10 M reads/s peak, 1 M writes/s peak, 1 B live keys, 10 TB of values (avg 1 KB, max 1 MB) |
| Latency | `get` p50 200 us, p99 1 ms inside the DC, measured at the client. `mget` of 100 keys p99 2 ms |
| Hit rate | >= 95% steady state. Every miss is a DB read, so hit rate is the DB's availability budget |
| Availability | Cache tier 99.99% for reads. A node loss must not take the DB down: extra DB load from one node loss <= 1% of DB capacity |
| Consistency | Eventual with bounded staleness: a value is at most `TTL` old and at most 1 s old after a write that invalidates it (in-region). Read-your-writes for the writer within a region |
| Memory | Per-key overhead <= 100 B. Node runs at 80% of RAM, never swaps |
| Operations | Add 10% capacity with no visible hit-rate dip; rolling restart with no page |

## What interviewers probe (the ladder)

1. Where does the client send `get(k)`? Who owns the map from key to node, and how does a client learn it changed?
2. A node dies. What do the next 10 seconds look like for the DB? Now 10% of nodes die.
3. Add a node. How many keys move, and where do the requests for them go while they are cold?
4. One key gets 1 M QPS. Which box melts first, and what do you do about it?
5. A hot key expires. 10,000 requests miss at once. What hits the DB?
6. The app updates a row. When is the cache wrong, for how long, and what shrinks that window?
7. How does eviction actually work in memory? Why not a real LRU list? What is the overhead per key?
8. Replicate or not? What does replication buy in a cache, and what does it cost?
9. A 10 MB value shows up. What breaks?
10. Multi-region: same cache in two regions, a write in one. What does the other region see?

## Files

| File | What it is |
|---|---|
| [`solution.md`](solution.md) | Full HLD in flow-first form: one incremental diagram, one walkthrough per FR, deep dives that mutate the design, then nitty-gritty |
| [`diagrams.md`](diagrams.md) | The D1 to D12 diagram set |
| [`edge-cases.md`](edge-cases.md) | Every "what if" with a 60-second answer and a confidence box |
| [`deep-dives/key-placement-and-membership.md`](deep-dives/key-placement-and-membership.md) | Consistent hashing with vnodes, bounded loads, the config service and epochs, ring change without a miss storm |
| [`deep-dives/eviction-and-memory-layout.md`](deep-dives/eviction-and-memory-layout.md) | Slab allocator, per-key overhead, sampled LRU, W-TinyLFU, S3-FIFO, TTL expiry at scale |
| [`deep-dives/hot-keys-and-stampedes.md`](deep-dives/hot-keys-and-stampedes.md) | Detection, client L1, key replication, leases, single-flight, probabilistic early refresh |
| [`deep-dives/replication-and-node-failure.md`](deep-dives/replication-and-node-failure.md) | None vs async vs client-side replication, gutter pool, failure detection, cold start, protecting the DB |
| [`deep-dives/invalidation-and-consistency.md`](deep-dives/invalidation-and-consistency.md) | The cache-aside race, leases, CDC invalidation, versions, multi-region remote markers |
| [`deep-dives/client-and-network-path.md`](deep-dives/client-and-network-path.md) | Smart client vs proxy, connection math, mget incast, pipelining, large values |
| [`research/`](research/) | Raw web research notes with source links. Input to the files above, not study material |
| `distributed-cache.excalidraw` | My drawing. Missing until I draw it |
