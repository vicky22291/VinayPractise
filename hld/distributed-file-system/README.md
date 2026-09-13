# Strongly consistent distributed file system (no S3, no "just GFS")

> One-line answer: a sharded, Raft-replicated metadata service that owns the namespace and the chunk map, plus a fleet of dumb chunk servers that store immutable, checksummed, versioned chunks, with leases and epochs so exactly one writer can mutate any file at a time.

Tier 1, problem #3 in [`hld/README.md`](../README.md). Reported at Databricks (8 reports), also Meta E6 and Google L6 as "design Colossus / HDFS / Dropbox storage without S3".

## Problem statement

Build a file system that many machines in one datacenter can mount. Files are large (MB to TB), written mostly once, read many times, and must never be lost or silently corrupted. Every operation is strongly consistent: after a write is acknowledged, every subsequent read from any client sees it. You cannot use S3, GCS, or another object store as the data plane, and you cannot answer "GFS" because GFS is not strongly consistent.

## Functional requirements

Core:
- Namespace: `create`, `open`, `read(offset, len)`, `append`, `close`, `delete`, `rename`, `list(dir)`, `stat`. Hierarchical paths.
- Large files split into chunks spread across many storage nodes. One file can exceed one disk.
- Concurrent readers of a file while one writer appends.
- Atomic rename, including across directories. Delete is atomic and space is reclaimed later.

Below the line:
- POSIX random overwrite in the middle of a file. We support append-only or whole-chunk rewrite. Say this out loud.
- Byte-range locking, hard links, extended attributes, symlinks.
- Multi-writer to the same file. One writer per file via lease.
- Cross-datacenter active-active. Strong consistency is per cluster. Cross-region is DR, not a second primary.

## Non-functional requirements

| Dimension | Target |
|---|---|
| Scale | 10 B files, 100 PB logical, 500 PB raw, 5,000 storage nodes |
| Metadata ops | 500 k ops/s peak (open, stat, list), 50 k creates/s |
| Data throughput | 1 TB/s aggregate read, 200 GB/s aggregate write |
| Latency | metadata p99 < 10 ms, first-byte read p99 < 20 ms, 64 MB chunk write p99 < 500 ms |
| Availability | 99.95% for reads, 99.9% for writes, single DC |
| Consistency | Linearizable metadata. Read-after-write for data. No stale replica ever served |
| Durability | 11 nines per year for sealed data. Survive 2 concurrent disk or node failures, one rack, one power domain |
| DR | RPO 15 min, RTO 1 h on DC loss (async), with the option of RPO 0 at cross-DC write latency |

## What interviewers probe (the ladder)

1. Who owns the mapping path -> inode -> chunks -> nodes, and how do you shard it to 10 B files without one hot master?
2. Rename `/a/x` to `/b/x` while another client deletes `/b`. What is atomic, what is locked, what does the second client see?
3. Metadata leader acks a create then dies. Is the create durable? How does the new leader know? How is the old leader fenced?
4. Storage node dies mid-write of a chunk. What is "committed"? Can a reader ever see a torn chunk?
5. Two metadata leaders after a partition. Show me the exact mechanism that makes the stale one harmless.
6. One directory gets 1 M creates a minute (a Spark job writing part files). What melts and what do you do?
7. Whole datacenter lost. What is the RPO, and does that contradict "strongly consistent"?
8. Where is the checksum, when is it checked, and who repairs a bit flip nobody read for a year?

## Files

| File | What it is |
|---|---|
| [`solution.md`](solution.md) | Full HLD, Bad / Good / Great ladders, nitty-gritty internals |
| [`diagrams.md`](diagrams.md) | The D1 to D12 diagram set |
| [`edge-cases.md`](edge-cases.md) | Every "what if" with a 60-second answer and a confidence box |
| [`deep-dives/metadata-sharding.md`](deep-dives/metadata-sharding.md) | Path vs inode vs directory sharding, rename across shards, hot directories |
| [`deep-dives/write-path-and-commit.md`](deep-dives/write-path-and-commit.md) | Chunk write pipeline, what "committed" means, chunk versions, torn writes |
| [`deep-dives/leases-fencing-epochs.md`](deep-dives/leases-fencing-epochs.md) | Every lease and epoch in the system and the split-brain proof |
| [`deep-dives/durability-and-erasure-coding.md`](deep-dives/durability-and-erasure-coding.md) | Replication vs EC, durability math, repair bandwidth, copysets |
| [`deep-dives/disaster-recovery.md`](deep-dives/disaster-recovery.md) | RPO/RTO, async vs sync cross-DC, snapshots, why RPO 0 costs latency |
| [`research/`](research/) | Raw web research notes with source links (metadata layer, data layer, interview framing and DR). Input to the files above, not study material |
| `distributed-file-system.excalidraw` | My drawing. Missing until I draw it |
| `my-attempt.md` | My timed attempt before reading the solution |
