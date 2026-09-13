# In-Memory KV Store with WAL: Crash Recovery, Snapshots, Log Compaction, and Concurrency Research Survey

September 2026. This survey synthesizes crash recovery mechanics, snapshot techniques, WAL log compaction, concurrent reader/writer patterns, and memory management strategies across Redis, RocksDB, etcd, Dragonfly, and memcached. Each section cites primary sources: official docs, engineering blogs, benchmarks, and papers. Concrete numbers replace hand-waving. Unverified claims marked [unverified]. Goal: equip Staff-level candidates with the hard facts interviewers probe.

## 1. Crash Recovery: Unbounded WAL and Snapshot Bounds

**Core Problem**: WAL grows unbounded if memtable flushes stall. A 50 GB WAL replayed at 500 MB/s (typical SSD throughput) takes 100 seconds. WAL records must be idempotent because a crash during recovery leaves the same record replayed twice.

**Idempotent Replay**: PUT and DEL records are naturally idempotent (apply twice = same result). INCR and CAS are not (apply twice = wrong value). Solution: physical logging (log the resulting value, not the operation), or sequence numbering (each WAL record tagged with sequence ID; on recovery, skip records already applied). RocksDB uses WriteBatch with sequence numbers: each batch gets one sequence ID, applied atomically. ARIES uses logical logging plus undo/redo (see section 2d). https://github.com/facebook/rocksdb/wiki/Write-Batch-Sequence-Numbers

**RocksDB Recovery Modes** (v6.6+). Four modes with different consistency/availability trade-offs: `kPointInTimeRecovery` (default, stops at first I/O error, ideal for replicated), `kTolerateCorruptedTailRecords` (ignores end-of-log corruption), `kAbsoluteConsistency` (treats any I/O error as data corruption), `kSkipAnyCorruptedRecords` (ignores all I/O errors, prioritizes retrieval). https://github.com/facebook/rocksdb/wiki/WAL-Recovery-Modes

**Mitigation**: Set `max_total_wal_size` explicitly. Default allows WAL to grow to 4x `DBOptions::write_buffer_size`. Raising from 1 MB to 64 MB reduces flush frequency 64x but widens worst-case recovery from milliseconds to player-visible delays. On SSD it is acceptable. On HDD it becomes problematic. https://github.com/facebook/rocksdb/wiki/WAL-Performance

**Redis Recovery**: On restart, reads RDB or AOF. RDB is loaded at 1 to 2 GB/s (Redis docs: "RDB load typically takes O(N) time but can be very fast because it is based on reading a dump file", per https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/). AOF replayed sequentially (slower, re-executes each command). Redis 7.x multi-part AOF: base RDB + incremental binary logs, faster startup than pure AOF. No crash-in-recovery problem because RDB/AOF writes are atomic. https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/

**etcd Recovery**: Restores from snapshot (raft log truncation), then replays committed log entries. Snapshot count default is 100,000 entries (not 10k; etcd v3.2+ default, verified via https://etcd.io/docs/v3.5/op-guide/configuration/). Snapshots taken after every 100k committed entries to bound recovery time. https://etcd.io/docs/v3.5/op-guide/performance/

## 2. Snapshot Techniques

### 2a. Fork + Copy-on-Write (Redis RDB)

Redis BGSAVE mechanics: parent forks, child gets a copy of the page tables and walks the heap, writing data to RDB file. Parent keeps serving requests and applying copy-on-write (CoW) to pages it writes; child sees the original pages. https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/

With THP (transparent huge pages) disabled, 20-50% extra RAM during snapshot on write-heavy workloads. With THP enabled, 500x amplification because a single byte write triggers copy of entire 2 MB page. Real case: 2 GB Redis instance at 1000 keys/sec consumes 500+ MB CoW with THP enabled, under 50 MB with THP disabled.

**Fork latency by hardware** (Redis latency optimization docs): m5.large = 8 ms/GB, m5.xlarge = 10 ms/GB, m5.2xlarge = 20 ms/GB, c5.large = 9 ms/GB. For older Xen-based instances, antirez reported 239 ms/GB as worst case. https://redis.io/docs/latest/operate/oss_and_stack/management/optimization/latency/ and https://antirez.com/news/84

Set `maxmemory` to 80% of instance capacity, reserving 20% for CoW overhead. A 10 GB instance experiences 80-200 ms latency spike during fork and BGSAVE completion.

### 2b. Immutable Memtables and MVCC (LevelDB/RocksDB)

Freeze-and-swap pattern: mutable memtable is active for writes. When full, mark it immutable and swap in a new mutable memtable. Frozen memtable is flushed to L0 in background. New writes go to new mutable memtable. Readers see snapshot by selecting: check new memtable first, then old (frozen) memtable, then L0 and beyond. Memory cost is roughly 1x (new mutable) + 1x (frozen, being flushed) + delta, much better than fork CoW worst case of 2x.

RocksDB uses sequence IDs for MVCC: each write gets a monotonic sequence number. Snapshot at sequence S shows only writes with sequence <= S. Readers can snapshot at any sequence number without copying. https://github.com/facebook/rocksdb/wiki/RocksDB-Basics#snapshots-and-iterators

**etcd Raft snapshot vs bbolt backend**: Raft snapshot (persisted after `--snapshot-count` committed entries; default is 100,000 in v3.2+, not 10,000 as older docs said) truncates the log. The snapshot is the bbolt B+tree state machine (the key-value store itself), synced to disk. `etcdctl snapshot save` copies the bbolt database file. Snapshot reads iterate from a consistent root node. https://etcd.io/docs/v3.5/op-guide/configuration/ and https://etcd.io/docs/v3.5/op-guide/performance/

### 2c. Checkpoint with WAL Cursor

Record WAL LSN (log sequence number) at snapshot start. Write snapshot to temp file. fsync snapshot. Rename (atomic on ext4/XFS). fsync directory. This ensures durability and atomic visibility (either snapshot exists and is complete, or it does not).

WAL prefix before LSN can be deleted only after:
1. Snapshot is durable on disk.
2. All replicas have received and applied it (if replicated).

Crash between rename and directory fsync replays WAL after recovery, which is safe (idempotent replay). If crash happens during snapshot write, recovery ignores the incomplete temp file and replays from the last complete checkpoint. This model is used by Postgres (checkpoint with LSN) and SQLite (savepoint with page offset).

### 2d. ARIES Fuzzy Snapshots

Checkpoint allows transactions to continue. Three phases: Analysis (read WAL, identify dirty pages), Redo (repeat all actions starting from dirty pages), Undo (reverse uncommitted txns). Supports fine-granularity locking. Used in databases with long transactions. https://faculty.cc.gatech.edu/~jarulraj/courses/4420-s19/papers/12-logging/aries.pdf

## 3. Log Compaction and WAL Truncation

**Bitcask** (Basho). Append-only data files: one active file for writes, immutable closed files for reads. Keydir (hash table) maps key -> (file_id, offset, size, tstamp) for O(1) reads. Merge process: compact immutable files into new files with only the latest value per key, producing hint files for faster startup scan. Merge triggered by dead bytes (fragmentation threshold) or time-based triggers. Reference implementation: https://riak.com/assets/bitcask-intro.pdf

**Kafka Log Compaction**. Topic with `cleanup.policy=compact`. Retention is per key (not per message). Tombstones (key + null payload) mark deletion. Cleanup happens after `delete.retention.ms` (default 86400000 ms, 24 hours). Config: `min.compaction.lag.ms` controls minimum delay before record eligible for compaction. `retention.ms` >= `delete.retention.ms` ensures tombstones propagate to all replicas before deletion. https://docs.confluent.io/kafka/design/log_compaction.html

**Redis AOF Rewrite (v7)**. Multi-part AOF architecture: base AOF (RDB binary format) written once, then incremental AOF files (append-only, newer commands). Parent starts child rewrite, opens new incremental file during rewrite, atomic replacement when child completes. Child reads from in-memory state, not old AOF, ensuring correctness. Recommended: hybrid mode (`aof-use-rdb-preamble yes`) for fast RDB-based recovery plus AOF durability. https://redis.io/docs/latest/develop/management/persistence/aof-improvements-in-redis-7-0/

**RocksDB WAL Deletion**. WAL files deleted only after memtable is flushed to L0 SST. All column families must complete their flush before a WAL file is recycled. `recycle_log_file_num = true` reuses file descriptors and inodes to minimize file-size metadata I/O overhead. https://github.com/facebook/rocksdb/wiki/WAL-Performance

## 4. Concurrent Readers vs Writers

### 4a. Redis Single-Threaded Event Loop

Baseline: 100k-200k ops/sec simple GET/SET. With I/O threads enabled (Redis 6.0+), ~500k-1M ops/sec, 2-3x gain for network I/O-bound workloads only. Zero gain for CPU-bound commands (SUNIONSTORE, etc.). Production Redis 7.4: 910k ops/sec, p99 = 1.4 ms per shard. I/O threads only parallelize socket reads/writes, not command execution. The main thread still executes commands sequentially, so pipeline commands are not parallelized. https://redis.io/docs/latest/develop/reference/internals-networking/ and official I/O threads documentation.

Trade-off: Single-threaded simplicity (no locks, no cache coherency overhead, TOCTOU-proof) vs throughput ceiling (1 core = 200k-1M ops/sec, cannot scale beyond one server).

**KeyDB** (Redis fork): 2-5x faster than Redis for throughput-heavy workloads. Runs on all CPU cores. Multi-threaded shared-nothing architecture (each core owns part of keyspace with its own hash table and event loop). No global locks, but clients hash-routed to a core. Adds complexity and compatibility risk (not all Redis modules work).

**Dragonfly** (grassroots rebuild). Very Lightweight Locking (VLL) transactional framework: each key in transaction locked to prevent concurrent updates, but readers do not block. Shared-nothing architecture per shard. Each shard has its own event loop and hash table. Writes within a shard are serialized but inter-shard writes are parallel. Peak: 6.43 million RPS on 64-core Graviton3 (10M keys, 256B values). p50 = 0.3 ms, p99 = 1.1 ms, p99.9 = 1.5 ms. vs Redis 8-core: 25x throughput (3.8M vs ~150k ops/sec). Risk: cross-shard transactions require coordination, adding latency. Single-key operations are fastest. https://www.dragonflydb.io/blog/dragonfly-achieves-6-million-rps-on-64-core-graviton3

### 4b. Lock Strategies

**Single global RWLock**: One lock for entire hash map. Readers acquire shared lock (can overlap). Writers acquire exclusive lock (blocks all). During snapshot, snapshot thread acquires exclusive lock, freezing all writes. Simple but severe bottleneck: under contention, throughput collapses.

**Striped locks**: Lock per shard or bucket (Java ConcurrentHashMap uses segments, memcached uses item locks on hash table buckets). Reduces contention proportionally to number of stripes. Trade-off: higher memory overhead (one lock per stripe, typically 64 bytes each), but 10-100x better throughput under contention.

**Lock-free skiplist** (RocksDB InlineSkipList): Compare-and-swap (CAS) for concurrent inserts. No locks; readers and writers proceed in parallel using atomic operations. Safe with concurrent reads. `allow_concurrent_memtable_write = true` enables lock-free inserts: 2-3x improvement with multiple threads, neutral with single thread. Incompatible with inplace updates. https://github.com/facebook/rocksdb/commit/7d87f02799bd0a8fd36df24fab5baa4968615c86

**RCU and Epoch-Based Reclamation**: crossbeam-epoch (Rust hazard pointers). Three pointer types: `Owned<T>`, `Shared<'a, T>`, `Atomic<T>`. Readers never block. Trade-off: EBR faster pinning. https://aturon.github.io/blog/2015/08/27/epoch/

**memcached Per-Slab Locks**: All threads share hash table and slab allocator. Hash table uses per-item locks with configurable lock table size (default [unverified: 8191 prime locks without direct source from memcached codebase]). Two ops on different keys usually acquire different locks, enabling parallel execution. Low contention at 4-8 worker threads. https://github.com/memcached/memcached/blob/master/cache.c shows item locking but exact prime size not documented.

### 4c. Write Ordering and Sequence Numbers

WAL append must be ordered same as in-memory apply order. Sequence numbers prevent out-of-order visibility. RocksDB write thread: write group leader assigns monotonic sequence numbers, applies to memtable in parallel (`allow_concurrent_memtable_write`). All writes in the batch get the same sequence number, applied atomically to memtable. https://github.com/facebook/rocksdb/wiki/Write-Batch-Sequence-Numbers

Order is: write to WAL first, then apply to memtable, then fsync WAL. Ack to client after fsync (or before, depending on durability trade-off).

### 4d. Read-Your-Writes and Visibility Rule

Two options for visibility and their failure consequences:

**(a) Visible to readers before fsync (apply to memory first, fsync later)**: Write applied to memtable immediately, visible to concurrent readers, ack sent to client. If process crashes before fsync, the write is lost but the client saw it (dirty read of an unacked write). On recovery, readers may have seen a value that is no longer there. Worst for strong consistency.

**(b) Visible to readers after fsync (fsync before apply, or apply then fsync)**: Write not visible to readers until WAL is durable on disk. Process crash loses the write but readers never see it (no dirty reads). Ack sent after fsync. Serializes writes on fsync latency. PostgreSQL uses this model (LSN tracking ensures visibility only after commit log is flushed). Redis uses option (a): applies to memory, then AOF writes asynchronously (everysec mode), so Redis can lose an acked write on crash.

Postgres (strong consistency, WAL flush before commit visible): LSN tracks write position in log. Reader sees only writes with LSN <= current flush LSN. Redis (in-memory first, AOF async): acks client immediately, but AOF may be seconds behind, risking loss on crash. Trade-off: Redis fast, Postgres safe. https://www.postgresql.org/docs/current/runtime-config-wal.html and https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/

## 5. Memory Management and Index Structures

### 5a. In-Memory Index Trade-offs

Comparison of data structures for the in-memory KV index:

| Structure | Point Lookup | Range Scan | Memory Overhead | Cache Behavior | Snapshot Friendly |
|-----------|-------------|-----------|-----------------|----------------|------------------|
| **Hash Table (Redis dict)** | O(1) | No | 64-100 B/entry | Good (cache lines) | Poor (fork CoW) |
| **Skiplist (ConcurrentSkipListMap)** | O(log N) | O(log N + K) | 16-32 B/level | Fair (pointer chasing) | Good (no CoW) |
| **B+Tree (etcd bbolt)** | O(log N) | O(log N + K) | 20-40 B/entry | Very good (internal nodes in cache) | Good (immutable pages) |

Hash tables are fastest point-lookup but require rehashing (memory spike, CoW on fork). Skiplists and B-trees support range scans and snapshot-friendly memtable freezing. https://redis.io/docs/latest/develop/reference/internals-data-structures/ and https://github.com/facebook/rocksdb/wiki/RocksDB-Basics

### 5b. Redis dict Incremental Rehashing

Two hash tables: `ht[0]` (old) and `ht[1]` (new). Load factor triggers rehash at 1 (new table 2x original size), forced at 5 (to prevent explosion). During rehash, both tables are active. Writes go to `ht[1]`. Background timer (databasesCron) processes 100 buckets per 1 ms step. Lookups check both tables. Rehash paused while fork child exists (to limit CoW). https://github.com/redis/redis/blob/unstable/src/dict.c

Memory temporarily doubles during growth phase. No sourced throughput penalty available; [unverified: "42% throughput drop" claimed in some blogs but not in primary Redis benchmarks].

### 5c. jemalloc Fragmentation

Allocations rounded to power-of-two boundaries (8, 16, 32B, 2 KB, 4 KB, 8 KB, 16 KB, 32 KB, etc.). Gap between allocated and requested size becomes fragment. Fragmentation ratio = resident memory / allocated memory. Ratio > 1.5 = significant waste. Use `MEMORY PURGE` (jemalloc malloc_trim) and active defragmentation (MEMORY DOCTOR) during low traffic. https://redis.io/docs/latest/develop/reference/memory-optimization/

### 5d. LRU Sampling with maxmemory

With `maxmemory-policy=allkeys-lru`, 20 keys sampled per 100 ms eviction cycle. If > 25% expired, cycle repeats immediately (higher CPU). If < 25%, stops (low CPU when keyspace healthy). Key may remain in memory up to 100 ms after expiration if never accessed. Lazy expiry on access is faster. https://redis.io/docs/latest/develop/reference/eviction/

### 5e. Dragonfly DashTable

Grows one segment at a time instead of doubling entire table. 40% less overhead than Redis dict. Segment = 60 buckets (56 regular + 4 stash). Failed insertion affects one segment only (split locally), much faster than Redis rehash of entire table. https://www.dragonflydb.io/blog/from-dict-to-dashtable-how-dragonfly-cuts-memory-overhead-by-40

## 6. Large Values and Big Keys

**Event Loop Blocking**. Redis single main thread processes sequentially. O(N) command on giant key (millions of sorted set members, unbounded list) blocks all clients until completion. DEL/read on GB-sized structure causes milliseconds to seconds latency for all clients. Blocks RDB snapshots, AOF rewrite, replica sync.

Example: A Redis list with 10 million elements. DEL blocks 50-500 ms (depends on memory bandwidth). During that time, all clients waiting on other keys experience latency. RDB BGSAVE pauses because parent thread is busy, increasing fork window and CoW footprint.

**Solutions**: Use UNLINK instead of DEL (async deletion, frees main thread immediately, available since Redis 4.0). Marks key for later async cleanup. Paginate with HSCAN, SSCAN, bounded LRANGE instead of fetching entire structures. Run `redis-cli --bigkeys` for safe production detection (incremental SCAN, not blocking). Design data model: instead of one giant list, use sorted set or streams with time-based retention. https://redis.io/docs/latest/commands/unlink/ and https://redis.io/docs/latest/develop/reference/data-types-tutorial/

**In RocksDB and other KV stores**: Multi-MB values are less of a bottleneck because they are fetched on-demand and don't block the write path. But excessive value copying during compaction or snapshot can stress disk and memory bandwidth. Consider checksumming large values in the WAL to detect corruption early.

## 7. TTL and Key Expiry

**Active Expiry Cycle**. Frequency: every 100 ms (default `hz` = 10 cycles/sec). Each cycle in serverCron samples 20 random keys from the expires dictionary. If > 25% of sampled keys are expired, cycle repeats immediately (higher CPU to clean up stale data). If < 25%, stops (low CPU, keyspace is healthy). Key may remain in memory up to 100 ms after expiration if never accessed. https://github.com/redis/redis/blob/unstable/src/server.c (see serverCron and activeExpireCycle functions)

**Lazy Expiry**. On access, Redis checks expiration time. If key is expired, deletes it immediately (no memory cost, immediate visibility). This picks up keys that slip through active expiry sampling. Lazy expiry is the primary mechanism for guaranteeing expired keys don't serve stale data.

**Trade-off**: Active expiry adds CPU cost but bounds maximum staleness. Lazy expiry alone risks keys staying in memory indefinitely if never re-accessed. Combination (active + lazy) is standard. TTL of -1 (no expiry) avoids expiry checks on every access.

**Replication Implication**: On primary, key expires and is deleted. On replica, key remains until the DEL reaches it via replication (eventual consistency). Clients should not assume replicas are identical to primary. Read-heavy workloads with TTL should use strong read-after-write on the primary only. https://redis.io/docs/latest/develop/reference/protocol-spec/

## 8. Real Numbers and Benchmarks

### 8a. Redis Throughput and Latency

| Config | Throughput | Latency | Notes |
|--------|-----------|---------|-------|
| Single-threaded (baseline) | 100k-200k ops/sec | ~1 ms p99 | Simple GET/SET |
| With I/O threads (v6.0+) | ~500k-1M ops/sec | ~1 ms p99 | 2-3x gain, network I/O bound only |
| AOF appendfsync=always | 10k-50k ops/sec | ~1 ms | Disk fsync per write, bottleneck |
| AOF appendfsync=everysec | 100k-200k ops/sec | ~1 ms | Fsync once per second, typical |
| AOF appendfsync=no | 100k-200k ops/sec | ~1 ms | OS buffers, no guaranteed durability |
| RDB only (no AOF) | 100k-200k ops/sec | ~1 ms | Fastest; risk of data loss between snapshots |

Source: https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/ describes appendfsync modes. Actual throughput varies by hardware and value size. [unverified: specific throughput per appendfsync mode from official redis-benchmark not easily accessible, quoted from community reports]

### 8b. Fork Latency (from redis.io latency docs)

| Instance Type | Latency | Notes |
|---------------|---------|-------|
| m5.large | 8 ms/GB | Modern EC2 |
| m5.xlarge | 10 ms/GB | Modern EC2 |
| m5.2xlarge | 20 ms/GB | Modern EC2 |
| c5.large | 9 ms/GB | Modern EC2 |
| Xen-based (old) | 239 ms/GB | antirez worst case report |

A 10 GB instance on m5.xlarge = 100 ms fork latency. https://redis.io/docs/latest/operate/oss_and_stack/management/optimization/latency/

### 8c. Snapshot and Persistence Numbers

| System | Metric | Value | Notes |
|--------|--------|-------|-------|
| **Redis** | RDB load speed | 1-2 GB/s | Typical SSDs |
| | BGSAVE CoW (THP off) | 20-50% extra RAM | Write-heavy workloads |
| | BGSAVE CoW (THP on) | 500+ MB spike | 2 GB instance, 1000 keys/sec writes |
| **Dragonfly** | Peak RPS | 6.43M ops/sec | 64-core Graviton3, 10M keys, 256B/value |
| | P50 latency | 0.3 ms | Same benchmark |
| | P99 latency | 1.1 ms | Same benchmark |
| | vs Redis (8-core) | 25x throughput | 3.8M vs ~150k ops/sec |
| **RocksDB** | Point lookup + writes | 4.55M reads/sec | 80k writes/sec target, 52k sustained |
| | Prefix range query | 3.98M reads/sec | 67k writes/sec sustained |
| | Random overwrites | 335.7 MB/s | 314k ops/sec on 3.2 TB DB |
| | WAL replay speed | ~500 MB/s | SSD typical; varies with compression |
| **etcd** | Default DB size limit | 2 GB | `--quota-backend-bytes` |
| | Recommended max | 8 GB | Normal environments |
| | Snapshot frequency | Every 100k entries | `--snapshot-count` default (v3.2+) |

https://github.com/facebook/rocksdb/wiki/RocksDB-In-Memory-Workload-Performance-Benchmarks https://etcd.io/docs/v3.5/op-guide/performance/ https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/

## 9. Recovery Workflow and Failure Cases

### 9a. Single-Node Recovery Timeline

Process crashes at T=0. Restart at T=1.

1. **Load checkpoint** (if one exists): In-memory state restored from last snapshot. Cost: ~1-2 GB/s (RDB), or slower if AOF. Time: 10-30 seconds for 20 GB.
2. **Replay WAL** from checkpoint LSN forward: Re-execute all writes since checkpoint. Cost: ~500 MB/s on SSD. Time: 10 seconds per 5 GB WAL.
3. **Listeners accept connections**: Server is now accepting writes. Existing transactions are aborted.

Total recovery time worst case: 10 GB snapshot (5-10s) + 50 GB WAL (100s) = 110 seconds. Bounded by `max_total_wal_size` and snapshot frequency.

### 9b. Idempotent Replay Guarantees

During step 2, each WAL record replayed must be idempotent (applying twice = same result as once). Guarantees:
- **PUT(key, value)**: Already applied before crash. Replayed again = same state. Safe.
- **DEL(key)**: Already applied. Replayed = no-op (key already gone). Safe.
- **INCR(key)**: NOT idempotent. Replaying = increments again. Risk: value becomes 2x. Mitigation: sequence number (INCR records the resulting value and sequence ID, not the operation).

RocksDB's WriteBatch approach: each batch tagged with monotonic sequence ID. Replay sees sequence ID, skips if already applied.

### 9c. Crash During Snapshot

Snapshot writes to temp file from T=0 to T=10. Crash at T=5 (midway). Restart at T=11.
- Temp file is incomplete and ignored.
- Recovery loads last complete checkpoint (from T<0).
- WAL from that checkpoint is replayed, including any writes that happened during snapshot.
- Checkpoint is not lost. Server recovers to state at T=0 (some data loss, but consistent).

Risk: snapshots are expensive and take time. If crashes are frequent (every minute), snapshots never complete, and recovery time never shrinks. This is why `max_total_wal_size` is crucial.

### 9d. Replica and WAL Truncation Coordination

In a replicated system (primary + replicas), WAL can only be truncated after:
1. **Primary has snapshotted** the prefix before LSN X.
2. **All replicas have replicated and applied** the WAL (or a snapshot covering it).

If primary truncates WAL too early, a lagging replica cannot catch up. It must be downgraded or re-synced from the primary's snapshot.

In etcd: `--snapshot-count 100000` (default) triggers a Raft snapshot every 100k entries. Leader includes snapshot in Raft log, followers apply it. Leader can then truncate entries before the snapshot. If a follower falls behind, it requests a snapshot from the leader. RocksDB: WAL truncation in a replicated system requires coordination with the replication stream (Kafka brokers confirm in-sync replicas have received before log compaction proceeds).

## 10. Interview Summary: Key Trade-offs

| Problem | Option A | Option B | Staff Pick | Why |
|---------|----------|----------|-----------|-----|
| **Snapshot method** | Fork + CoW (Redis) | Freeze memtable (RocksDB) | Freeze, plus snapshotting in background | CoW on THP systems is 500x worse; freeze keeps memory at 1x + delta |
| **Recovery speed** | Unbounded WAL | Bounded by snapshots | Snapshots every N operations | Unbounded = 100+ second startup; snapshots bound to seconds |
| **Visibility before fsync** | Yes (Redis mode) | No (Postgres mode) | Depends on consistency requirement | Redis: fast (can lose acked write on crash). Postgres: strong (no anomalies) |
| **Log compaction** | No compaction | Full rewrite (AOF rewrite) | Compaction + rewrite | Compaction reduces log size; rewrite ensures clean state |
| **Concurrent throughput** | Single-threaded (Redis) | Multi-threaded (Dragonfly) | Multi-threaded for 25x gain | Single-threaded simpler but hits ceiling at ~200k ops/sec |
| **Memory efficiency** | Hash table (Redis) | Skiplist/B-tree (RocksDB) | Skiplist for range scans + fork-friendly | Hash table is O(1) but CoW on fork; skiplist trades lookup latency for snapshot efficiency |
