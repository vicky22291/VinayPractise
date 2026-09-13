# Apache Cassandra 5.0 Deep Dive

<!-- nav:start -->
**[← All systems](../README.md)** · [Start here: 00 Overview](cassandra-00-overview.md) · [Pattern catalogue](patterns.md)
<!-- nav:end -->

**Baseline: Apache Cassandra 5.0** (GA 2024-09-05), verified against the
`cassandra-5.0` branch at 5.0.10-SNAPSHOT.

> *A hash ring assigns every key to RF nodes, each node is an independent
> LSM-tree store that never coordinates on write, and three separate repair
> mechanisms race the ten-day tombstone clock to make the replicas agree again.*

## Read this first

The overview opens with three corrections to the common mental model of
"Cassandra 5.0", all verified in source:

1. **Trie memtables are not the default.** `memtable.configurations.default`
   inherits `skiplist`. TrieMemtable (CEP-19) is opt-in.
2. **BTI is not the default SSTable format.** `sstable.selected_format`
   defaults to `big`. BTI (CEP-25) is opt-in.
3. **UCS is not the default compaction strategy, and TCM and Accord are not in
   5.0 at all.** `default_compaction` falls back to `SizeTieredCompactionStrategy`.
   CEP-21 and CEP-15 moved to 6.0, which is not GA.

The practical consequence: an out-of-the-box 5.0 node is architecturally a
well-tuned 4.1 node. The 5.0 headline features are a menu, not a migration.

| File | Covers |
|---|---|
| [`cassandra-00-overview.md`](cassandra-00-overview.md) | Reading map, architecture, the four design bets |
| [`cassandra-01-storage-engine.md`](cassandra-01-storage-engine.md) | CommitLog, memtables, SSTable formats |
| [`cassandra-02-write-path.md`](cassandra-02-write-path.md) | Mutation, coordinator fan-out, batches, counters |
| [`cassandra-03-read-path.md`](cassandra-03-read-path.md) | Bloom filter, index, merge, read repair |
| [`cassandra-04-compaction.md`](cassandra-04-compaction.md) | STCS, LCS, TWCS, UCS |
| [`cassandra-05-coordinator-consistency.md`](cassandra-05-coordinator-consistency.md) | CL levels, R+W>RF, hints, speculative retry |
| [`cassandra-06-membership-gossip.md`](cassandra-06-membership-gossip.md) | Gossip, phi-accrual failure detection, the ring |
| [`cassandra-07-repair-streaming.md`](cassandra-07-repair-streaming.md) | Merkle trees, repair modes, streaming |
| [`cassandra-08-cql-sai.md`](cassandra-08-cql-sai.md) | CQL execution, SAI secondary indexes |
| [`cassandra-09-tcm-accord.md`](cassandra-09-tcm-accord.md) | CEP-21 and CEP-15, the 6.0 architecture |
| [`cassandra-10-scale-operations.md`](cassandra-10-scale-operations.md) | Scale envelope, runbooks, thresholds |
| [`cassandra-11-delta-and-version-matrix.md`](cassandra-11-delta-and-version-matrix.md) | Version matrix and errata |
| [`patterns.md`](patterns.md) | Cross-system pattern catalogue (+ Cassandra, + anti-entropy) |

**Scale envelope:** 1-4 TB per node with STCS/LCS. Single-digit-ms p99 for
single-partition reads. Hard modelling limit ~100 MB / ~100k rows per
partition, which is the red node in `10`.

`gc_grace_seconds` defaults to **864000** (10 days). That is the deadline by
which hinted handoff, read repair or Merkle repair must have run, or you
resurrect deleted data.
