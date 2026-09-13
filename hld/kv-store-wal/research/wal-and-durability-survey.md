# Write-Ahead Log (WAL) Mechanics & Durability Survey

This survey covers WAL record formats, fsync semantics, group commit batching, persistence strategies, and cloud durability across RocksDB, PostgreSQL, etcd, Kafka, Redis, and cloud storage. Research from official docs, GitHub wikis, engineering blogs, and benchmarks. September 2026.

---

## 1. WAL Record Format

**LevelDB/RocksDB**: 32 KB block size. Record layout: [CRC-32C (4B) | Length (2B) | Type (1B) | Data (variable)]. Types: FULL (0), FIRST (1), MIDDLE (2), LAST (3) for multi-block records. Records cannot start within last 6 bytes of block; if 7+ bytes remain, writer emits zero-length FIRST record to pad. CRC-32C covers length, type, and data. Ensures each record is independently verifiable.
https://github.com/facebook/rocksdb/wiki/Write-Ahead-Log-File-Format

**etcd**: 64 MB segment preallocation. Record format: 8-byte frame length header (lower 56 bits = payload length in bytes, upper 8 bits = padding count for alignment) + protobuf walpb.Record {type (uint32), crc (uint32), data ([]byte)}. Record types: metadata (0), entry (1), state (2), crcType (3), snapshot (4). Each record has its own CRC-32C. Default max 5 WAL files kept to limit memory and prevent Raft consensus from stalling on segment exhaustion. Segment preallocation avoids allocation latency spikes.
https://etcd.io/docs/v3.6/learning/persistent-storage-files/
https://pkg.go.dev/go.etcd.io/etcd/server/v3/wal

**PostgreSQL**: 16 MB segments (default, configurable via initdb --wal-segsize). 8 KB pages (default). Log Sequence Number (LSN): byte offset into entire WAL stream since cluster start, monotonically increasing. Full-page writes: after each checkpoint, the first modification to any page logs the entire 8 KB page image (not just deltas). Ensures crash recovery can restore consistent page state without replaying transactions. Checkpoint barrier: synchronization point for flushing dirty pages to disk before accepting new transactions.
https://www.postgresql.org/docs/current/wal-internals.html

**Kafka**: 1 GB segment size (log.segment.bytes = 1,073,741,824 bytes default). 7-day rollover window (log.roll.ms = 604,800,000 ms). Index files created every 4,096 bytes with offset-to-file-position mappings (fast offset lookup). Kafka durability is NOT pre-commit WAL; instead, producers wait for ISR acks and broker-to-broker replication. Segments deleted after retention period expires (7 days default). Compacted topics delete old versions of same key within a segment.
https://kafka.apache.org/41/configuration/topic-configs/

---

## 2. fsync Semantics & Latency

**I/O System Semantics**:
- write() → page cache only (not durable, kernel may evict freely)
- fdatasync() → flushes page cache + file size metadata, but NOT mtime/ctime/atime (sufficient to read data back)
- fsync() → flushes page cache + all inode metadata (mtime, ctime, ownership, permissions)
- O_DIRECT → bypasses page cache entirely (direct to page cache on read, direct from buffer on write), does NOT imply durability; still requires fsync/FUA to reach disk
- O_DSYNC → each write() behaves as write() + fdatasync() (fsync every write, very slow)

**Disk Write Cache & FUA**: Disk's volatile write cache buffers data in DRAM on the drive. On fsync(), kernel issues FLUSH CACHE or FUA (Force Unit Access) commands. Without power-loss protection (capacitors or battery backup), a power cut during fsync can lose buffered data. Enterprise drives with capacitor-backed cache survive fsync to disk on power loss.

**Page Cache**: Linux maintains dirty_ratio (default 20%) and background_dirty_ratio (10%). Periodic flush every ~30 seconds or when thresholds exceeded. On servers with large RAM, dirty_ratio can hold gigabytes of unflushed writes, creating a "durability gap" on crash. Many production systems lower these values.
https://lwn.net/Articles/326552/

**fsync Latency by Storage Tier**: 
- HDD (7,200 RPM): 5-15 ms (mechanical seek ~5 ms + rotation time ~5 ms)
- SATA SSD: 0.5-2 ms (no mechanical parts, write cache variable)
- NVMe Consumer (Corsair MP600 PCIe 4.0): 450-525 usec (controller firmware-managed, write cache cleared on fsync)
- NVMe Enterprise (with capacitor-backed cache): 20-100 usec (power-loss safe, fsync returns after write cache receipt, capacitor ensures cache flush on power loss)
- AWS EBS gp3 on NVMe-backed infrastructure: 1-5 ms (network RPC to replication layer, in-AZ replication)

Specific Benchmarks: Consumer NVMe fsync 8KB sequential = 525 usec (1,905 ops/sec), fdatasync = 451 usec (2,217 ops/sec). Enterprise NVMe (Intel SSD DC P5600 or similar) fsync 20-100 usec (10,000-50,000 ops/sec). Difference is power-loss protection: enterprise drives have capacitors to flush cache to persistent storage on power loss, allowing fsync() to return after write cache receipt (not after platter write). Batched writes further amortize: at 200 writes per 1 ms fsync, added latency per write = 5 us.
https://gist.github.com/pklaus/3fbef6899fae01b7ebf388e19d508315
https://www.scylladb.com/2017/10/05/io-overhead-scylla-vs-cassandra-avoid-payload-copies/

**Comparison: Different Persistence Strategies**:
- **write() only**: Latency ~1 usec (memory copy). Durability: 0 (lost on crash). Used only for non-critical logs.
- **write() + background kernel flush**: Latency ~1 usec (memory). Durability: ~30 seconds on Linux (kernel dirty cache). Risk: kernel panic, power loss, OOM killer can lose data.
- **write() + fdatasync()**: Latency ~450 usec on NVMe (wait for disk). Durability: 100% to file size metadata. Safe for most WAL use cases.
- **write() + O_DIRECT + fdatasync()**: Latency ~450 usec. Bypasses page cache (less memory overhead for large files). Used in storage engines to control caching explicitly.
- **write() + fsync()**: Latency ~500 usec on NVMe. Durability: 100% including inode metadata (mtime, etc). Necessary for directory operations, full metadata sync.
- **write() + O_DSYNC**: Latency ~500+ usec per write (fsync per write, no batching). Very slow, strongest durability per write. Rarely used for high-throughput systems.

Recommendation: WAL systems use fdatasync() on regular files (sufficient for data + size metadata) and fsync() on directory after segment creation. This balances durability with latency.

**AWS EBS Durability & Recovery**: io2 Block Express replicated across 3 availability zones within region, 99.999% durability (one replica can fail). gp3/gp2/io1 replicated within single AZ (replication factor typically 3), 99.8-99.9% durability (two replicas can fail simultaneously without data loss). A completed fsync() to EBS is durable to the EBS volume; AWS maintains in-AZ replication automatically via the EBS control plane. Cross-AZ durability requires explicit: EBS snapshot to S3, cross-region snapshot copy, or active/passive replication to standby in another AZ. Typical failover latency on AZ failure: ~10 seconds (automatic volume detach + reattach) to minutes (application reconnect). Local NVMe instance store is ephemeral: survives EBS-backed instance reboot but lost entirely on instance termination, stop, or hardware failure. Not suitable for persistent data without external replication.
https://aws.amazon.com/ebs/faqs/

---

## 3. fsyncgate: PostgreSQL 2018 Incident

**Problem**: Kernel I/O error handling was fundamentally broken. XFS (and other filesystems) marked dirty pages with AS_EIO flag on writeback failure, then silently dropped the error. Subsequent fsync() would return success without reporting the I/O error. Application committed transaction believing it was durable; data was actually lost on disk. Worst-case: distributed database replicates unconfirmed transaction, all replicas lose data in unison.

**Root Cause**: Block I/O layer (disk controller, SATA, NVMe) reports errors to filesystem after writeback attempt fails. Filesystem marks page AS_EIO internally. Application must call fsync() immediately to detect error. If application calls fsync() much later, the kernel reports error once, then clears it. A second fsync() succeeds (error already reported). Distributed systems with quorum commits (3 replicas) could have 2 replicas lose a transaction silently while 1 replica succeeds, violating consistency.

**Solution & Lessons**: PostgreSQL 12+ (and backports to 9.4-11) now PANIC on any fsync() error, immediately aborting the instance. Forces operator to investigate disk failure. No silent data loss. Similar fixes deployed in InnoDB/MySQL, WiredTiger/MongoDB, RocksDB. Key takeaway: fsync() failure is not recoverable; the only safe action is to crash hard and audit data on recovery.
https://wiki.postgresql.org/wiki/Fsync_Errors
https://lwn.net/Articles/752063/

---

## 4. Group Commit & Batching

**PostgreSQL**: Group commit amortizes single fsync() over multiple concurrent transactions via commit_delay parameter. 10-50x throughput improvement at high concurrency.
https://wiki.postgresql.org/wiki/Group_commit

**MySQL InnoDB**: innodb_flush_log_at_trx_commit settings control fsync timing:
- 0: Write log buffer to OS cache, fsync once per second in background. Loss window: up to 1 second of transactions on crash. Fast writes (~1 usec), used for non-critical data.
- 1 (default, ACID-safe): fsync on every commit. Durable, no data loss, but higher latency (~0.5 ms per transaction unbatched). Group commit reduces latency by 10-50x with concurrent transactions.
- 2: Write log buffer to OS cache immediately, fsync once per second. Loss window: 1 second if OS crashes (not application crash). Compromise: fast writes + fsync batching. Used when trading some durability for throughput.

innodb_flush_log_at_trx_commit=1 is default (safest) but requires group commit to be viable at high throughput. Many production systems use 2 if they have external replication (e.g., MySQL replication) as backup.
https://dev.mysql.com/doc/refman/8.4/en/innodb-parameters.html

**RocksDB Write Group Mechanics**: Max group size 1 MB writes per fsync (prevents unbounded memory growth during batch building). First thread to acquire write mutex becomes leader. Leader collects writes from other threads into a single WAL batch (typically 0.1-0.2 ms on modern CPU), performs one sequential WAL write, one fsync, then releases the lock. Followers wait in a lock-free queue; once leader's fsync completes, all followers apply their writes to memtable in parallel without holding the global lock. This allows reads to proceed during memtable application.

**Worked Latency Example**: System receives 200,000 writes/sec, 1 ms fsync latency on NVMe. Group size = 200 writes (200k / 1,000 groups/sec). Each group's timeline: leader batches 200 writes (~0.2 ms), writes to WAL (~0.3 ms), fsyncs (~1 ms), releases. Followers apply to memtable in parallel (~0.3 ms). Total commit time ~1.8 ms for batch. Per-write latency = 1.8 ms / 200 writes = 9 us commit component. With application code + network RTT (~50 us), total write latency ~60-100 us p50, ~150 us p99. Pipelined write (v5.5+) overlaps phases (batch building in prior group while current group fsyncs), yielding ~30% improvement (reduces 1.8 ms to ~1.3 ms per batch).
https://github.com/facebook/rocksdb/wiki/Pipelined-Write
https://github.com/facebook/rocksdb/issues/10383

**Kafka**: Kafka does NOT fsync by default (log.flush.interval.messages = 2,147,483,647, effectively infinity). Producers wait for ISR (in-sync replicas) acks instead of local fsync. At acks=all, broker acknowledges only after all ISR replicas have received message in their page cache (fsync not required for ack, but replication leader waits for ISR to write). This is a legitimate durability model: replication to ISR replaces local WAL fsync. Replication factor = 3 means 2 replicas can fail and data survives. Caveat: simultaneous total partition loss (e.g., all 3 replicas fail at once) causes data loss. Single-node loss is safe. Optional log.flush.interval.bytes allows periodic fsyncs for stricter durability if needed (trades throughput for latency). Default (no fsync) assumes replication provides durability.

**Throughput math**: At 1ms fsync latency, unbatched = 1,000 writes/sec. Batching N writes into one fsync → N × 1,000 writes/sec. At 200k writes/sec with 200-write groups = 1,000 groups/sec, all fsynced in 1 ms per group.

---

## 5. Redis Persistence

**AOF appendfsync Settings & Guarantees**:
- appendfsync always: Fsync on every write call (single-threaded event loop blocks). Very slow, but every command durable on return. Can lose nothing on crash.
- appendfsync everysec (default): Write to AOF in event loop (blocking), fsync in separate background thread every second. Loss window: up to 2 seconds of commands on crash. Stated as "AOF everysec can lose up to 2s of writes" in Redis docs.
- appendfsync no: Write to AOF in event loop, rely on OS buffering for fsync (typically ~30s on Linux). Loss window: up to 30 seconds on kernel panic / power loss.

**AOF Rewrite**: Background AOF rewrite (BGREWRITEAOF) forks and writes a new AOF file with compact commands (e.g., SET keys instead of individual APPEND operations). Meanwhile, parent appends to old AOF. When child finishes rewriting, parent atomically switches to new AOF. Knob `no-appendfsync-on-rewrite`: if on, skips fsync() during rewrite (faster rewrite, but durability risk if crash during rewrite).

**RDB Snapshots (BGSAVE)**: Copy-on-Write fork via BGSAVE. Child process writes snapshot while parent continues serving. Memory overhead can double if parent writes heavily: CoW copies pages on write, so hot pages exist in both parent (new version) and child (old snapshot version) simultaneously. Fork latency on large heaps (EC2 benchmark, Redis docs): 1 GB ~ 1 ms, 10 GB ~ 100 ms, 24 GB ~ 200-500 ms. Fork blocks the main thread briefly; on overloaded systems or large heaps, fork can cause brief unavailability. Recovery from RDB faster than AOF (binary format, no command parsing). Durability gap: snapshot captures state at fork() time; all writes after fork are lost unless AOF is enabled. Therefore, production Redis often enables both RDB (periodic snapshots) and AOF (continuous command log) for durability.
https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/
https://redis.io/docs/latest/operate/oss_and_stack/management/optimization/latency/

**Redis 7.0+ Multi-Part AOF**: Atomic base file (RDB or AOF format) + incremental append-only files + manifest file. On rewrite, base file created while incremental files accumulate. Atomic manifest swap makes new base + incremental active. Knob aof-use-rdb-preamble: rewritten AOF starts with RDB-format stanza (fast to load), followed by incremental AOF tail. Faster recovery than full-text AOF.
https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/

---

## 6. Torn Writes & Partial Records

**Detection & Recovery**: CRC-32C checksum per WAL record (4 bytes). Length field validation during recovery (type must be 0-3). CRC mismatch or invalid type/length = truncated record detected. Recovery algorithm: scan forward through WAL, apply valid records to replay state, stop at first CRC failure or invalid record. PostgreSQL truncates WAL at last valid record boundary. RocksDB offers multiple recovery modes (see section 6 below). Key insight: torn writes are inevitable on power loss; the goal is to detect them quickly and safely.

**RocksDB Recyclable WAL**: Record header: CRC-32C | Length | Type | Log number. Type must be valid, log number must match WAL file, size must fit block. Limitation: payload corruption may pass header validation.
https://github.com/cockroachdb/pebble/issues/864

**PostgreSQL Full-Page Writes**: After checkpoint, first page modification logs entire page (8 KB). Crash recovery restores page directly if marked dirty. Torn-page detection via page CRC.

**RocksDB WAL Recovery Modes** (set via DBOptions::wal_recovery_mode):
- kPointInTimeRecovery (default): Recovers up to last completely written and valid WAL record. Truncates tail at first CRC mismatch or invalid record header. Safe for consistency (no half-writes applied), may lose last few tens of writes. Recommended for production: balances data durability with crash safety.
- kAbsoluteConsistency: Crashes entire DB open if WAL has any truncation or corruption. Refuses to start DB, forces manual intervention. Used in test harnesses and strict compliance scenarios where no data loss is acceptable even if it means manual recovery.
- kTolerateCorruptedTailRecords: Silently truncates WAL at first corruption and discards tail. Allows DB to open despite WAL damage. Useful in high-availability scenarios (standby replica, automatic failover) where best-effort recovery is acceptable. Operationally risky: may mask disk failures.
- kSkipAnyCorruptedRecords: Attempts to skip corrupted records in the middle and recover subsequent records. Risky: if corruption is in the middle of a multi-record transaction, skipping corrupts transaction semantics. Rarely safe. Not recommended.
https://github.com/facebook/rocksdb/wiki/WAL-Recovery-Modes

---

## 7. Checksums & Hardware Acceleration

**CRC-32C Hardware Acceleration**: Intel SSE 4.2 (Nehalem+ / Core i7 2010+): CRC-32C instruction achieves ~1 cycle/byte throughput (4 bytes computed per cycle on Skylake+). ARMv8: native crc32* instructions. Software fallback using lookup tables ~10-20 cycles/byte. Modern CPUs (2015+) universally support hardware CRC-32C. Used in: Btrfs (filesystem integrity), ext4 (extent checksums), Ceph (object storage), LevelDB, RocksDB, PostgreSQL (custom), etcd. Performance: checksumming 1 MB takes ~1 ms with hardware, ~10-20 ms with software. For WAL, hardware CRC is near-free (overhead << 1% of total latency).
https://github.com/google/crc32c

**Granularity**: Per-record checksums (RocksDB, etcd) provide maximum detection granularity: each record checked independently. Alternatively, per-block checksums (one CRC per 32 KB block) reduce overhead but miss single-record corruption if other records in block are fine. **Why checksum the length field**: length corruption is catastrophic: if record header says length = 999,999 bytes but actual record is 100 bytes, recovery reads 999,999 bytes into next record, interpreting garbage as valid record headers. Entire tail becomes unparseable. CRC-32C covers [Length | Type | Data], so length corruption is always detected. RocksDB additionally validates type field (must be 0-3 for FULL/FIRST/MIDDLE/LAST), catching invalid records.

---

## 8. Preallocation & fallocate()

**Why Preallocation Helps**: fallocate() reserves disk space upfront, avoiding repeated allocation syscalls and extent map updates. Writes to preallocated regions bypass allocation stalls.

**Directory fsync and fdatasync Precision**: Appending to a preallocated file changes only file size metadata (st_size in inode). fdatasync() flushes this size metadata to disk. Creating or renaming a segment file requires a separate fsync() on the directory to ensure the directory entry (dirent) is durable. Many systems batch segment creation/rename + directory fsync to amortize this cost. Example: RocksDB writes WAL sequentially to preallocated file with fdatasync per write, then fsyncs the directory every N segments to ensure recovery sees all segments.
https://lwn.net/Articles/457667/
https://github.com/facebook/rocksdb/wiki/WAL-Performance

**Two-fsync Problem and Solution**: Naive approach: each WAL append = write (data to page cache) + fsync (data+size metadata) + fsync (directory entry). Three separate fsync calls = 3-5 ms latency per batch. Efficient systems decouple: write to preallocated file repeatedly (no allocation syscall), fdatasync only the size metadata (not directory), batch directory operations, then fsync directory once per segment rotation. Example: 1 MB of appends to preallocated file = 1,000 appends of 1 KB each. Batch: 1,000 × write + 1,000 × fdatasync (data+size) + 1 × fsync (directory) = 1,000 ms overhead from fsyncs (assuming 1 ms per fsync on NVMe), vs naive approach 3,000 ms. Reduction: 66%.

**etcd & RocksDB Segment Strategy**: Preallocate 64 MB segments upfront using temporary 0.tmp or 1.tmp filenames. Write sequentially to current segment with fdatasync after each batch of writes. When segment fills, atomic rename 0.tmp → segment-NNNNN (persistent name) makes segment visible to recovery. Then fsync the WAL directory once (ensures dirent is durable). Keeps max 5 WAL files on disk. Avoids Raft consensus stalling due to WAL capacity exhaustion (if WAL fills faster than snapshots rotate).

---

## 9. WAL on Cloud Disks

**AWS EBS Durability**: io2 Block Express replicated across AZ, 99.999% durability. gp3/gp2/io1 replicated within AZ, 99.8-99.9%. A completed fsync() to EBS is durable to the EBS volume within the AZ. For multi-region durability, use EBS snapshots or cross-region replication. Cross-AZ durability requires a second copy (standby instance, read replica, or S3).
https://aws.amazon.com/ebs/faqs/

**Local NVMe Ephemeral Instance Store**: NVMe instance storage offers ~100 usec fsync latency vs 1-5 msec for EBS (10-50x faster). However, ephemeral: lost on instance termination, stop, or hardware failure. Suitable ONLY as: (1) read-cache with durable source-of-truth elsewhere, (2) temp working directory during batch processing, (3) WAL write cache with EBS/S3 as commit point. Cannot be used as sole durability layer. Some instances provide dual NVMe (hot + cold swap); not a durability feature, just performance.

**Hybrid Architecture (S3 + Local NVMe)**: Use S3 Express One Zone (99.99% durability within zone) as source-of-truth for committed transactions. Local NVMe for write cache and read performance. Architecture: transactions buffered in local NVMe WAL, batched fsync to S3 (slow, durable), then local in-memory state updated. On crash: recover from S3, repopulate NVMe cache. Latency: 50 us to write NVMe, +100-500 ms to fsync S3. Trade-off: NVMe write latency is local, S3 fsync is in background, read latency is NVMe (50-100 us). Employed by Turso (distributed SQLite edge DB).
https://aws.amazon.com/blogs/storage/how-turso-built-a-transactional-database-using-amazon-s3-express-one-zone/

---

## 10. Real-World Benchmarks

**RocksDB Write Throughput**: Baseline (no pipelining): ~60k writes/sec with WAL sync on. Pipelined write (v5.5+) achieves ~30% improvement on modern CPUs due to concurrent phases (batch building, log writing, memtable insert). Group commit max 1 MB per group; at 200 B per write, that's 5,000 writes per group. One fsync per group. At 1 ms fsync latency, 5,000 writes / 0.001 s = 5 million writes/sec theoretical (accounting for batch building overhead, actual sustained 60-80k writes/sec on commodity hardware).
https://github.com/facebook/rocksdb/wiki/Pipelined-Write

**etcd fsync Latency**: p99 fsync latency target < 10 ms for healthy disk (99th percentile). backend_commit_duration_seconds (end-to-end commit latency) p99 < 25 ms. Healthy cluster requires minimum 1,500-2,000 sequential IOPS; heavily loaded clusters need 4,000+ IOPS. Prometheus metric etcd_disk_wal_fsync_duration_seconds_bucket tracks fsync histogram. Slow fsync causes Raft election timeouts and frequent leader changes. Rule of thumb: if p99 fsync > 50 ms, disk is the bottleneck, not Raft logic.
https://etcd.io/docs/v3.2/metrics/
https://github.com/etcd-io/etcd/issues/10547

**PostgreSQL pg_test_fsync (NVMe)**: fsync via standard open: 513 usec/op (1,949 ops/sec). fdatasync: 443 usec/op (2,259 ops/sec). open_sync: 526 usec/op. open_datasync variant: 568 usec/op in one config, 1,760 usec/op (568 ops/sec) in another (O_DSYNC per-write is slow). Variation by storage type: HDD 5-15 ms, SATA SSD 0.5-1 ms, NVMe 0.4-0.5 ms. This tool is standard for PostgreSQL administrators to benchmark their storage before deployment.
https://gist.github.com/pklaus/3fbef6899fae01b7ebf388e19d508315

**Kafka Durability Model & Trade-offs**:
- acks=all: Producer waits for all ISR (in-sync replicas, usually 3) to acknowledge. Latency ~10-50 ms depending on network and follower response time. Safest: if quorum survives, no data loss. Used for critical transactions (payments, order systems).
- acks=1 (default): Producer waits for leader fsync only. Latency ~0.5-5 ms (just leader disk). Follower replication happens async; leader failure ~100 ms before followers catch up. Used for high-throughput, moderate durability (search, analytics).
- acks=0: Fire-and-forget, no ack. Latency microseconds. Unreliable, only for metrics/logging. Producer doesn't know if message reached broker.

Throughput: millions of messages/sec on commodity clusters. At 1000 byte messages, ~100-500k msgs/sec per broker depending on disk, network, and replication factor. acks=1 can achieve 100k+ msgs/sec, acks=all ~10-50k msgs/sec due to replication round-trip.
https://kafka.apache.org/performance.html

**Redis AOF Throughput**: appendfsync always supports batching but is fundamentally single-threaded in the event loop (blocks during each fsync). Actual throughput: ~80-150k commands/sec with appendfsync always on NVMe (each fsync adds ~500 us, so 80-150k = 1 / (500 us + command processing)). appendfsync everysec background thread: "still very high" per Redis docs; exact number not published. Comparable to RDB snapshots but slower due to per-command serialization overhead vs RDB's binary bulk dump.
https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/

---

## 11. WAL Sizing for In-Memory Key-Value Stores

**Record Size Breakdown**: WAL record = header (CRC-32C [4B] + length [2B] + type [1B] + padding = ~8 bytes) + key (variable) + value (variable). At 100 byte average key and 200 byte average value = 308 bytes per record. System with 200,000 writes/sec = 200k × 308 B/s ≈ 61 MB/s of log data = 5.3 TB/day. This calculation drives decisions on segment size, rotation frequency, and disk capacity planning.

**Segment Size Trade-offs**:
- **64 MB**: Small segments, many files to manage, rapid rotation (~1 second at 61 MB/s). Fits etcd's and consensus systems' latency constraints (frequent snapshots). Frequent directory fsyncs (every segment rotation). Memory overhead for metadata low.
- **256 MB**: Sweet spot for general-purpose KV stores. ~4 second rotation at 61 MB/s. Amortizes directory fsync cost (fsync every N segments rather than every write). Good balance between crash recovery speed (256 MB replayed = ~100 ms) and fsync batching.
- **1 GB**: Large segments, Kafka's choice. ~16 second rotation. Batches many records before directory fsync. Slower crash recovery (1 GB replay = ~400-500 ms on commodity hardware). Reduces fsync overhead to <1% of throughput.

**Log Retention Tied to Snapshots**: In-memory stores (Redis, Memcached variants, custom KV stores) delete WAL segments older than the last durable snapshot. Snapshot is source-of-truth; WAL provides point-in-time recovery from last snapshot to crash. Retention window depends on checkpoint frequency and desired RPO (Recovery Point Objective). Example: target RPO 5 minutes, keep 2 latest snapshots (every 5 min), delete older WAL. Snapshots every 10 minutes with 3 snapshots: retention 30 minutes worth of WAL (60 MB/s × 1,800 s = 108 GB of WAL across 3 snapshots).

**Practical Capacity Example**: RocksDB/in-memory KV: 200k writes/sec, 308 B/record, 200 B values, 1 ms fsync latency on NVMe, groups ~200 writes per fsync. Segment size 64 MB:
- Records per segment: 64 MB / 308 B = ~208k records
- Rotation frequency: 208k records / 200k writes/sec = ~1 second
- Directory fsync per 10 rotations = every 10 seconds
- Snapshot every 10 minutes (600 seconds) captures 600 × 61 MB/s = 36.6 GB
- Keep 3 snapshots + current WAL: ~110 GB total storage (3 × 37 GB + 1 GB current WAL)
- Disk I/O: 200k writes/sec × 308 B = 61.6 MB/s sustained (consider IOPS: at 4 KB block size, ~15,000 IOPS)

---

## Cross-Verification & Research Notes

**Verified Across 3+ Sources (High Confidence)**:
- CRC-32C checksums used universally (LevelDB, RocksDB, etcd, Kafka, PostgreSQL, Btrfs, ext4). Hardware-accelerated on SSE 4.2+ CPUs (~1 cycle/byte).
- fsync/fdatasync latency on NVMe: 400-550 usec (pg_test_fsync, Corsair benchmarks, Scylla reports). Variation by model: enterprise 20-100 usec due to capacitor-backed cache.
- Group commit 10-50x throughput improvement at high concurrency. Verified in PostgreSQL wiki, RocksDB pipelined write docs, MySQL innodb_flush_log_at_trx_commit benchmarks.
- Preallocation reduces fragmentation and allocation stalls. Used by all major systems (etcd 64 MB, PostgreSQL 16 MB, Kafka 1 GB).
- EBS 99.8%-99.999% durable within AZ via in-AZ replication. Local NVMe strictly ephemeral (lost on instance termination).
- fsyncgate 2018: PostgreSQL, MySQL InnoDB, WiredTiger all adopted panic-on-fsync-error fix. Correct behavior documented in PostgreSQL wiki.

**Key Interview Insights (What Matters for Staff-Level)**:
- **Power-loss protection is the difference**: Enterprise NVMe 20-100 us (capacitor-backed) vs consumer 400-500 us (firmware controlled). If your design assumes 20 us fsync on consumer hardware, you're overoptimistic.
- **Replication vs WAL durability**: Kafka is correct to not fsync by default. With ISR acks, replication to 3 replicas is durable. Forcing fsync adds latency without durability gain. Only fsync if you have no replication.
- **Write group leadership**: RocksDB's leader pattern is a concurrency win, not durability. All followers apply the same writes. No consistency risk. Optimization purely for throughput.
- **RDB fork latency**: 24 GB Redis instance fork = hundreds of milliseconds. If you snapshot every 10 minutes, you're blocking reads for 100-500 ms per snapshot. High churn workloads double memory. Operationally expensive; consider AOF or hybrid RDB+AOF.
- **Fdatasync + fsync split**: fdatasync(file) for data + size metadata is sufficient for WAL (fastest). fsync(directory) only needed after segment creation/rename (amortized). Separating these reduces latency overhead.
- **EBS is within-AZ only**: fsync() to EBS = durable within AZ, not across zones. For multi-region, need active replication or snapshots. This is often missed in interviews.

**[Unverified / Gaps in Documentation]**: 
- Kafka p99 fsync latency under different acks policies. Official docs don't quantify this; only describe acks semantics.
- Redis AOF everysec exact throughput. Docs state "still very high" but no number. Likely 100k-500k commands/sec depending on CPU/disk, not published.
- Two-fsync overhead quantified in microseconds. Filesystem-dependent: ext4, XFS, Btrfs journaling modes differ. No universal benchmark.
- Zero-filled preallocation trick for tail-record detection (used informally in some implementations, not documented in specs).
- Exact directory fsync latency. Varies by filesystem journal mode (ordered, writeback, data), filesystem load, queue depth.

**Sources by Reliability**: Official docs > GitHub wikis > Engineering blogs > Gists/benchmarks. PostgreSQL, RocksDB, etcd official docs are authoritative. Avoid Wikipedia for I/O details. LWN articles are trustworthy for kernel behavior.
