# RocksDB Deep Dive (light edition)

<!-- nav:start -->
**[← All systems](../README.md)** · [Start here: 00 Overview](rocksdb-00-overview.md)
<!-- nav:end -->

**Baseline: RocksDB 11.x** (`main` at 11.10.0, 2026-08-28. Latest tag v11.8.1, 2026-08-07). Defaults quoted from
`include/rocksdb/options.h`, `advanced_options.h`, `table.h` and the project
wiki. See the version note in [report 05](rocksdb-05-operations-and-tradeoffs.md)
before quoting a number.

> *A single-process LSM tree. Every write is one WAL append plus one skiplist
> insert. Everything else, flush, compaction, filters, caches, is the deferred
> bill for making that write cheap.*

## Why this series is shorter

Kafka, Cassandra and Kubernetes are distributed systems. RocksDB is not. It is
a **library** linked into one process, with no network, no replication and no
cluster membership. The distributed systems above embed it (or something like
it) as their per-node storage engine. So the goal here is narrower: know every
feature RocksDB offers, know how each is implemented at the level of "which
structure, which thread, which file", and know the three amplification numbers
well enough to argue about them.

Six reports, each 150 to 300 lines, no separate pattern catalogue. The
cross-system patterns live in [report 05, section 8](rocksdb-05-operations-and-tradeoffs.md#8-patterns-that-generalise).

## Read this first

Three things most secondary writing gets wrong:

1. **RocksDB is not "LevelDB with more options".** The fork kept the file
   format lineage and rewrote the write path (write groups, concurrent
   memtable inserts, pipelined WAL), the compaction engine (universal, FIFO,
   subcompactions, dynamic level sizing) and added column families,
   transactions, merge operators and blob files. LevelDB has none of these.
2. **Leveled compaction is the default and the trade is explicit.** Write
   amplification in the low tens in exchange for space amplification of
   ~1.11x. Universal compaction inverts that. Neither is free.
3. **The WAL is per database, not per column family.** Column families share
   one WAL and one sequence-number space. That is what makes a `WriteBatch`
   across column families atomic, and it is also why one slow-flushing column
   family can pin gigabytes of WAL.

| File | Covers |
|---|---|
| [`rocksdb-00-overview.md`](rocksdb-00-overview.md) | What it is, the architecture, the four design bets, reading map |
| [`rocksdb-01-write-path.md`](rocksdb-01-write-path.md) | WriteBatch, write groups, WAL, memtable, flush, write stalls |
| [`rocksdb-02-read-path-and-sst.md`](rocksdb-02-read-path-and-sst.md) | Get and Seek, SST block format, bloom and ribbon filters, block cache, snapshots |
| [`rocksdb-03-compaction.md`](rocksdb-03-compaction.md) | Leveled, universal, FIFO, the three amplifications, subcompactions, compaction filters |
| [`rocksdb-04-features.md`](rocksdb-04-features.md) | Column families, transactions, merge operator, DeleteRange, ingest, checkpoint, backup, BlobDB, TTL, secondaries |
| [`rocksdb-05-operations-and-tradeoffs.md`](rocksdb-05-operations-and-tradeoffs.md) | Memory budget, tuning, failure modes, who embeds it, alternatives, staff questions, patterns |

**Scale envelope:** one process, one disk (or one directory). Hundreds of
thousands of writes per second per instance on NVMe; single-digit to
tens-of-microsecond point reads on a block-cache hit; terabytes per instance
in production at Meta. There is no horizontal scale. The system that embeds
RocksDB owns sharding, replication and failover.

**The three numbers to carry into an interview**: write amplification (bytes
written to disk per byte written by the user), read amplification (disk
reads per point lookup), space amplification (disk bytes per live byte). The
whole compaction chapter is about trading them against each other.
