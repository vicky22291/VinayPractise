# Immutable distributed object store

> One-line answer: an S3-shaped store where every object is write-once and addressed by `(bucket, key, version)`: a stateless gateway streams bytes straight to storage nodes, small objects are packed into 3x-replicated append-only extents and large objects are erasure coded inline as RS(10,4) stripes across 14 failure domains, and an object becomes visible only when its record commits in a range-partitioned, Raft-replicated metadata index. Immutability is what makes strong consistency, caching, erasure coding, and repair cheap; the metadata index is the thing that gets hot.

Tier 1, problem #5 in [`hld/README.md`](../README.md). Reported at Databricks as "immutable distributed object store" and "immutable distributed file system" (see [`research/`](research/)). It is Databricks' own substrate: every Delta table is Parquet files plus a `_delta_log/` of JSON commits sitting on S3, so the interviewer knows the mechanics and probes durability math, the commit point, conditional PUT, and the hot-prefix problem. Also asked at Google ("design a blob store"), Meta ("photo storage", Haystack and f4), and Dropbox ("Magic Pocket").

## Problem statement

Build an object store with `put`, `get`, `delete`, `list`. Objects are opaque byte blobs from 1 B to 5 TB, written once and never modified in place. A second `put` to the same key creates a new version or is rejected by a precondition. The store runs in one region across 3 availability zones (AZs), holds hundreds of petabytes, and must not lose acknowledged data.

## Functional requirements

Core:
- `put(bucket, key, bytes, [checksum], [if-none-match | if-match etag])`. Objects up to 5 TB via multipart upload. Ack means durable and visible.
- `get(bucket, key, [version], [range])`, `head`. Byte-range reads for Parquet footers and row groups.
- `delete(bucket, key, [version])`. Delete is a metadata operation; space comes back later.
- `list(bucket, prefix, [delimiter], [cursor], max 1000)`. Ordered by key, paginated, strongly consistent.
- Conditional writes: put-if-absent and put-if-match. This is the primitive a transaction log (Delta, Iceberg) builds on.

Below the line (say it out loud):
- Append, overwrite in place, byte-range write. Immutability is the whole point.
- Cross-object transactions. Delta puts the transaction in the log, not in the store.
- Content search, tags queries, dedup across tenants (note the seam).
- Multi-region active-active. Async cross-region copy is a §10.11 evolution.

## Non-functional requirements

| Dimension | Target |
|---|---|
| Scale | 500 PB live, 100 B objects. Bimodal sizes: 70% under 1 MB (Delta JSON, small Parquet, checkpoints), 25% 1 MB to 1 GB, 5% over 1 GB, up to 5 TB |
| Throughput | 50 k PUT/s and 500 k GET/s peak. 200 GB/s ingest, 1 TB/s egress |
| Latency | small GET first byte p99 < 50 ms; small PUT ack p99 < 100 ms; large objects bandwidth bound at 100 MB/s per stream minimum |
| Durability | 99.999999999% per object per year ("11 nines"): survive any 2 disks, 1 rack, or 1 AZ with zero data loss. Bit rot detected and repaired |
| Availability | 99.99% GET, 99.9% PUT. A full AZ loss is not an outage |
| Consistency | Strong read-after-write for PUT, DELETE, and LIST. Conditional PUT is linearizable per key |
| Cost | Under 1.5x raw storage overhead on 90% of bytes. Target ~$10 per TB-month all in |

## What interviewers probe (the ladder)

1. Two clients `put` the same key at the same time. Who wins, and can a reader ever see half of either?
2. The client gets a `200` and the storage node that holds the bytes dies one second later. Is the object safe? What exactly is "committed"?
3. Replication or erasure coding? Show the overhead, the repair traffic, and where each one hurts. Why not erasure code everything?
4. Show the durability number. A 20 TB disk dies; how long until the data is safe again, and what if a second disk dies during that window?
5. A Spark job writes `part-00000` to `part-09999` under one prefix and a million readers hit `_delta_log/` at once. Where is the hot spot and what breaks?
6. 70 billion objects are under 1 MB. Is the metadata bigger than the data? Where do small objects live?
7. `list` on a prefix with 1 billion keys. Is it strongly consistent? How is it paginated?
8. Delete on an erasure-coded stripe. When is space reclaimed? GDPR says "gone in 30 days".
9. A scrub finds a fragment with a bad checksum. What happens?
10. An AZ goes dark. What do reads and writes see, and what does repair do when it comes back?
11. Cut the storage bill by half without changing durability.
12. Delta Lake commits via put-if-absent on `_delta_log/000123.json`. Make that linearizable and explain why S3 could not do it before 2024.

## Files

| File | What it is |
|---|---|
| [`solution.md`](solution.md) | Full HLD, Bad / Good / Great ladders, nitty-gritty internals |
| [`diagrams.md`](diagrams.md) | The D1 to D12 diagram set |
| [`edge-cases.md`](edge-cases.md) | Every "what if" with a 60-second answer and a confidence box |
| [`deep-dives/write-path-and-commit.md`](deep-dives/write-path-and-commit.md) | PUT commit point, multipart, conditional PUT, orphan reconciliation, crash matrix |
| [`deep-dives/erasure-coding-and-durability.md`](deep-dives/erasure-coding-and-durability.md) | RS(k,m) and LRC math, inline vs deferred encoding, degraded reads, the 11-nines calculation |
| [`deep-dives/metadata-index-and-listing.md`](deep-dives/metadata-index-and-listing.md) | Range partitioning, load-based split, hot prefixes, LIST, inline small objects, versioning |
| [`deep-dives/placement-rebalancing-and-repair.md`](deep-dives/placement-rebalancing-and-repair.md) | Extents, placement policy vs CRUSH, copysets, adding capacity, repair throttling, scrubbing |
| [`deep-dives/delete-gc-and-compaction.md`](deep-dives/delete-gc-and-compaction.md) | Tombstones, lifecycle, reclaiming space from EC extents, crypto-shred for GDPR |
| [`deep-dives/hot-objects-and-read-path.md`](deep-dives/hot-objects-and-read-path.md) | Range GET, hedged reads, hot object spreading, immutable cache tier, TTFB budget |
| [`research/`](research/) | Raw web research notes with source links. Input to the files above, not study material |
| `immutable-object-store.excalidraw` | My drawing. Missing until I draw it |
| `my-attempt.md` | My timed attempt before reading the solution |
