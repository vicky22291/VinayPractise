# In-memory key-value store with a write-ahead log

> One-line answer: a single-writer-ordered, sharded-in-process hash map where every mutation is appended to a checksummed, segmented write-ahead log (WAL) and group-committed with one fsync per batch before the client is acked; periodic fuzzy snapshots bound the log and the restart time, and the same log, shipped to replicas under a fenced primary, is what makes it survive a machine loss.

Tier 1, problem #4 in [`hld/README.md`](../README.md). Reported at Databricks (6 reports, "KV cache with WAL", "persistent in-memory store"). Also asked at Meta E6 and Google L6 as "design Redis" or "design a key-value store". The Databricks version is a mechanisms interview. The reported prompt (PracHub, LeetCode reports, see [`research/`](research/)): "Design a durable key-value store with `put`, `get`, `delete`. Achieve durability with a write-ahead log, lay out the on-disk data structures, and perform crash recovery. Single machine only, not distributed. Write pseudocode." A second reported variant adds "balance performance and consistency with read-write locks and fine-grained locking", so the concurrency model is an explicit grading item. They stay on one node for 30 to 50 minutes and drill into fsync, crash recovery, snapshots, and concurrency before scaling out, if at all.

## Problem statement

Build a key-value store that serves reads and writes from memory at sub-millisecond latency but never loses an acknowledged write across a process crash or a machine reboot. Keys and values are opaque bytes. Start with one machine. Then make it survive losing that machine, then make it hold more data than one machine.

## Functional requirements

Core:
- `put(key, value)`, `get(key)`, `delete(key)`. Opaque byte keys up to 1 KB, values up to 1 MB.
- An acknowledged write is durable: after the client gets the ack, a crash and restart returns that value (or a later one).
- Restart recovers the full state from local disk without an operator.
- Concurrent clients: many readers and writers at once, per-key linearizable.

Below the line (say it out loud):
- Range scans and ordered iteration. A hash index is enough; we say what changes if scans are needed.
- Multi-key transactions across shards. Single-key atomic ops (compare-and-swap, increment) are in scope; cross-shard atomicity is not.
- Secondary indexes, queries, TTL beyond a simple per-key expiry.
- Data larger than memory. This is an in-memory store; spilling to disk is the 10x evolution, not the design.

## Non-functional requirements

| Dimension | Target |
|---|---|
| Scale, one node | 200 M keys, 32 B mean key, 200 B mean value, ~60 GB live data |
| Throughput | 200 k writes/s, 800 k reads/s peak per node (80/20 read heavy) |
| Latency | get p99 < 1 ms; put p99 < 5 ms including durable commit on NVMe |
| Durability | Zero acknowledged writes lost on process crash or power loss of one node. RPO 0 on node loss once replicated |
| Recovery | Restart to serving in under 2 min for 64 GB of state |
| Consistency | Linearizable per key on a single node; read-your-writes preserved after failover |
| Availability | 99.9% single node; 99.99% with replication and automatic failover in under 10 s |
| Memory | Live data plus WAL buffers plus one in-progress snapshot must fit in 2x live data |

## What interviewers probe (the ladder)

1. What exactly happens between the client sending `put` and receiving the ack? Where is the fsync, and what does fsync actually promise?
2. The process dies after the WAL append but before the in-memory apply. Or after the apply but before the ack. What does the client see, what does recovery do?
3. fsync costs 1 ms. How do you get 200 k writes/s? Show the group commit and the latency it adds.
4. The WAL is 500 GB after a week. Restart takes an hour. How do you bound it without stopping writes?
5. A snapshot is in progress and writes keep arriving. Which version does the snapshot contain, and how does replay reconcile it with the log?
6. Two threads write the same key. One reader reads it at the same time. Who wins, what does the reader see, and is the WAL order the same as the memory order?
7. Disk is full, or fsync returns an error once. Do you keep serving reads? Do you accept writes?
8. The machine dies. Make the ack mean "survives machine loss". What does that do to write latency, and how do you stop the old primary from acking after failover?
9. 64 GB is not enough. Shard it. Now a hot key is 30% of traffic. Now a client wants `put` on two keys atomically.

## Files

| File | What it is |
|---|---|
| [`solution.md`](solution.md) | Full HLD, Bad / Good / Great ladders, nitty-gritty internals |
| [`diagrams.md`](diagrams.md) | The D1 to D12 diagram set |
| [`edge-cases.md`](edge-cases.md) | Every "what if" with a 60-second answer and a confidence box |
| [`deep-dives/wal-format-and-fsync.md`](deep-dives/wal-format-and-fsync.md) | Record layout, segments, what fsync promises, fsyncgate, group commit math |
| [`deep-dives/crash-recovery-and-snapshots.md`](deep-dives/crash-recovery-and-snapshots.md) | Replay, idempotency, fuzzy snapshots, log truncation, restart time |
| [`deep-dives/concurrency-model.md`](deep-dives/concurrency-model.md) | Single-threaded vs shared-nothing shards vs locks; write ordering; visibility |
| [`deep-dives/replication-and-failover.md`](deep-dives/replication-and-failover.md) | WAL as replication log, sync vs async ack, fencing, failover data loss |
| [`deep-dives/sharding-and-hot-keys.md`](deep-dives/sharding-and-hot-keys.md) | Hash slots, live migration, hot keys, multi-key ops |
| [`research/`](research/) | Raw web research notes with source links. Input to the files above, not study material |
| `kv-store-wal.excalidraw` | My drawing. Missing until I draw it |
| `my-attempt.md` | My timed attempt before reading the solution |
