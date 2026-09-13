# Edge cases: in-memory KV store with WAL

Every entry must be answerable out loud in under 60 seconds. Mark confidence after each study pass. Categories per `hld/CLAUDE.md` §5: failure, consistency, scale, data, operations, security.

Design recap for context: 16 shared-nothing shard threads per node, one WAL per shard, apply to memory at once but publish and ack only when `durable_lsn` passes the write's LSN, fuzzy snapshot from retained entry versions, Raft per shard for replication. Details in [`solution.md`](solution.md).

---

## 1. Failure

## Edge case: process dies after WAL append, before in-memory apply
- **Trigger:** kill -9 or panic between `buf.append` and `map[k] = ...`.
- **Symptom:** none visible. The client had no ack.
- **Answer:**
  - In our design apply happens in the same thread right after append, but the buffer may not have been written to disk at all yet. Either way the record is either on disk (fsynced) or not.
  - On restart, recovery replays every record with a good CRC after `snap_lsn`. If the record made it to disk, it is applied now. If not, it is as if it never happened.
  - The client timed out and retries with the same `request_id`; the dedup table (itself logged) returns the stored result or applies it fresh. State converges either way.
  - The key insight for the interviewer: the memory apply is never the source of truth. The log is. Memory is a cache of the log.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: process dies after apply and fsync, before the ack reaches the client
- **Trigger:** crash between `durable_lsn = ...` and the socket write.
- **Symptom:** client sees a timeout for a write that is actually durable.
- **Answer:**
  - After restart the value is present (it was on disk). A `get` returns it. This is allowed: a timed-out write may or may not have happened, the client must treat it as unknown.
  - Client retry with the same `request_id` hits the dedup entry and gets `OK(lsn)`. Without dedup, a retried `put` is harmless (idempotent) but a retried `cas` would return `MISMATCH`, which is wrong. That is why the dedup table exists and why it is in the log.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: power loss mid-write leaves a torn record at the end of the segment
- **Trigger:** 4 KB pages of a 250 B record batch land partially.
- **Symptom:** last record fails CRC, or its length runs past the end of the segment.
- **Answer:**
  - Recovery reads records in order. First record with a bad CRC or impossible length in the **last** segment marks the end. Everything before it is applied, everything after is discarded. Nothing acked is lost because the ack waited for `fdatasync`, and a completed `fdatasync` means the whole batch is on stable storage.
  - Block framing (32 KB blocks, RocksDB style) lets the reader resync at the next block if a middle page is torn, but we still stop at the first bad record: a hole in the sequence is a lost write.
  - Preallocated segments are zero-filled, so a zero length with a zero CRC is unambiguous end-of-log.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: CRC failure in the middle of the log with valid records after it
- **Trigger:** bit rot, a bad sector, or a torn page in an old segment.
- **Symptom:** recovery hits a bad record at LSN 800, but 801 onward parse fine.
- **Answer:**
  - This is not a torn tail. It is corruption. Skipping it silently loses a write and every later write may depend on it (a `cas` result). Refuse to start this shard (`kAbsoluteConsistency` stance for the body).
  - Recovery path: this shard's Raft peers have the same log. Bootstrap from a peer's snapshot plus log. Without replication, restore the previous snapshot and accept the loss, with a page.
  - Prevention: checksum verified on every replay, background scrub of old segments, two snapshots retained.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: `fdatasync` returns EIO once, then succeeds on retry
- **Trigger:** transient disk error, or a bad sector in the page cache write-back path.
- **Symptom:** one batch fails to sync.
- **Answer:**
  - Never retry. Since Linux 4.13 the kernel reports the error to the first `fsync` caller and clears the dirty flag on the pages; a retry returns success without the data being on disk (PostgreSQL's 2018 "fsyncgate").
  - Halt the shard: stop acking, keep serving reads of durable versions, exit the process. Restart recovers from the log, which ends at the last good batch. With Raft, followers take over in 1 to 2 s.
  - Page the on-call with `disk_errors`. Drain the node.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: disk full
- **Trigger:** snapshot stuck so log truncation stopped, or snapshot retention too high, or a co-tenant filled the disk.
- **Symptom:** `fallocate` of the next segment fails, or `write` returns ENOSPC.
- **Answer:**
  - Fail closed for writes, open for reads: reject `put` with `NO_SPACE`, serve `get` and `delete`? No, a `delete` is also a log record. Reject all mutations. Never drop the log to make room.
  - Emergency room: keep one pre-created spare segment per shard so the process can always finish the in-flight batch and write a manifest.
  - Root cause is almost always a stuck snapshot; the alert `log_bytes_since_snapshot > 3x budget` should have fired an hour earlier.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: node loses power, all three Raft members in the same rack
- **Trigger:** rack PDU failure with rack-unaware placement.
- **Symptom:** whole shard group down; on power-up, consumer drives may have lost their volatile cache.
- **Answer:**
  - With enterprise drives (power-loss protection), every `fdatasync`-acked batch survives. Raft log on each member is intact; group recovers.
  - With consumer drives that ack a flush before it is really done, acked writes can be gone on all three. This is the one failure that breaks the durability promise. Fix is procurement (PLP drives) and placement (one member per rack or power domain), not code.
  - Say this in the interview: durability is only as good as the flush semantics of the device.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: Raft leader dies after committing but before acking the client
- **Trigger:** leader crash between `commit_index` advance and the response.
- **Symptom:** client timeout.
- **Answer:**
  - The entry is on a majority. The new leader has it (election requires the candidate's log to be at least as up to date). It is committed and applied.
  - Client retries on the new leader with the same `request_id`; dedup table (replicated in the log) returns `OK`.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: old leader keeps serving after a partition
- **Trigger:** network partition isolates the leader from both followers. Followers elect a new leader.
- **Symptom:** clients still connected to the old leader.
- **Answer:**
  - Writes: old leader appends locally but cannot reach a majority, never commits, never acks. Clients time out and go to the new leader via `NOT_LEADER` or the config service.
  - Reads: with lease-based reads, the old leader may serve stale data for up to one lease (< election timeout, ~1 s). Acceptable and stated. For strict reads, use read-index (one heartbeat round) which the old leader cannot complete.
  - When the partition heals, it sees the higher term, steps down, truncates its uncommitted suffix.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: a follower is 1 hour behind and the leader has truncated its log
- **Trigger:** follower was down while the leader took snapshots and deleted old segments.
- **Symptom:** follower asks for LSN 1,000,000; leader's oldest segment starts at 5,000,000.
- **Answer:**
  - Leader sends its latest snapshot file (3.75 GB) then streams the log after `snap_lsn`. Same file format as local recovery, no special path.
  - To avoid this, log truncation waits for `min(snap_lsn, min follower match_index)` up to a cap (say 2 hours of log); past the cap, truncate anyway and let the follower re-bootstrap.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

---

## 2. Consistency

## Edge case: two clients write the same key at the same instant, a third reads it
- **Trigger:** `put(k, A)` and `put(k, B)` arrive on different I/O threads; `get(k)` arrives too.
- **Symptom:** which value wins, what does the reader see?
- **Answer:**
  - Both writes land in the same shard queue, in some order. The shard thread applies them in that order, giving LSNs 10 and 11. The log has the same order because the same thread appended them. Memory order = log order = LSN order, by construction.
  - The reader sees the newest version with `lsn ≤ durable_lsn`: the old value until batch containing 10 is durable, then A, then B. It never sees B then A.
  - Neither writer is "first" in any meaningful sense; the shard thread's queue defines the order, and it is the same order everywhere.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: a reader observes a value that is then lost in a crash
- **Trigger:** design where apply is visible before fsync (Redis `everysec`).
- **Symptom:** client B reads value V written by client A; process crashes; V is gone; B already acted on it.
- **Answer:**
  - Our design forbids it: reads return only versions with `lsn ≤ durable_lsn`. A value that could still vanish is never visible.
  - Cost: one `prev` pointer per entry during the ~1 ms window and a compare on every read.
  - Alternative "apply after fsync" also forbids it, at the cost of running `cas` logic on the apply path.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: `cas` succeeded against an unacked write whose batch then fails
- **Trigger:** `put(k, v1)` at lsn 10 in batch 1; `cas(k, v1, v2)` at lsn 11 in batch 2; batch 1 fsync fails.
- **Symptom:** could lsn 11 be durable without lsn 10?
- **Answer:**
  - No. Batches on one shard are fsynced in order, and an fsync failure halts the shard and exits the process. Batch 2 is never synced after batch 1 failed.
  - After recovery the log ends before 10. Both are gone. The client that issued `cas` never got an ack. Consistent.
  - With Raft, the same holds: entries commit in order.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: client retries a `put` that already committed
- **Trigger:** timeout after a committed write.
- **Symptom:** possible double apply.
- **Answer:**
  - `put` and `delete` are idempotent: applying twice yields the same state. Only the LSN differs.
  - `cas` and `incr` are not idempotent. The dedup table keyed by `(client_id, request_id)` with a 5 min TTL returns the original result. The table is logged so it survives crash and failover.
  - Interviewer follow-up: "what if the retry comes after 5 minutes?" Then it is a new request. State that TTL out loud and tie it to the client's max retry window.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: read-your-writes across a failover
- **Trigger:** client writes on leader A, A dies, client reads on new leader B.
- **Symptom:** could B not have the write?
- **Answer:**
  - If the write was acked, it was on a majority, and B (elected from that majority) has it. Read-your-writes holds.
  - If the write was not acked, the client does not expect it.
  - Follower reads (opt-in) can violate this. The client library can carry the last acked LSN and ask the follower to wait until `applied_lsn ≥ that`, which is the standard fix.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: TTL expiry on the leader vs the follower
- **Trigger:** key expires; leader and follower clocks differ by 200 ms.
- **Symptom:** follower serves an expired key, or expires a key the leader has not.
- **Answer:**
  - Only the leader expires. When the sampler or a lazy read on the leader removes a key, it logs an `EXPIRE` record; followers apply it. Followers never expire on their own clock.
  - Reads on the leader check `expire_at` against the leader's clock and return `NOT_FOUND` before the record is logged. That is fine: the key is dead from the leader's point of view and the record follows within ms.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

---

## 3. Scale

## Edge case: fsync suddenly takes 100 ms
- **Trigger:** disk degradation, noisy neighbor on cloud block storage, or a firmware garbage-collection stall.
- **Symptom:** put p99 jumps to 100+ ms; throughput does not drop because groups grow to 1,000+ records.
- **Answer:**
  - Group commit self-adapts: throughput holds, latency does not. Group byte cap (4 MB) bounds the size; beyond that writes queue.
  - Alert on `wal_fdatasync_p99 > 10 ms`. Transfer leadership of this node's groups elsewhere, which moves the write latency to a healthy disk in seconds.
  - Reads are unaffected: they never touch the disk.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: one key is 30% of all reads
- **Trigger:** a celebrity or config key.
- **Symptom:** one shard thread at 300 k reads/s, its node's NIC saturating if the value is large.
- **Answer:**
  - A shard thread does ~1 M lookups/s so the CPU survives; the network and the single Raft group for writes do not.
  - Client-side cache with 100 ms TTL removes ~99% of reads for read-hot keys. Follower reads with read-index give 3x. Write-hot counters split into 16 sub-keys, summed on read.
  - Detect with a per-shard top-k sketch (space-saving, 1,000 slots) exported every second.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: 10x writes tomorrow (2 M writes/s per node)
- **Trigger:** growth.
- **Symptom:** log rate 500 MB/s, 20 k fsync/s per shard at group size 6.
- **Answer:**
  - fsync rate is the wall: 16 shards × 2,000 fsync/s per shard is the practical ceiling per device. Groups grow to ~60 records per fsync, latency stays about 1 ms, so throughput actually holds on NVMe bandwidth (500 MB/s of 2 to 3 GB/s).
  - What breaks first: I/O threads parsing 2.5 M ops/s (need io_uring and more threads), then the snapshot interval (2 GB budget per shard fills in 65 s, so snapshots run almost continuously).
  - Real answer: more nodes. The design is shared-nothing; add nodes and move slots.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: a 1 MB value is written 1,000 times per second
- **Trigger:** a client storing blobs.
- **Symptom:** 1 GB/s of log on one shard; the log writer's `memcpy` and the NVMe both saturate; other keys on that shard see latency.
- **Answer:**
  - Cap value size at 1 MB and rate-limit bytes per client at the I/O thread.
  - Big values are copied off the shard thread: the shard thread stores a pointer, the I/O thread does the socket write.
  - If blobs are the workload, this is the wrong store. Point to an object store and keep the pointer here.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: hash table resize on a 12.5 M entry shard
- **Trigger:** load factor crosses 1.0.
- **Symptom:** naive rehash stalls the shard for hundreds of ms.
- **Answer:**
  - Incremental rehash: allocate the new bucket array (100 MB), move one bucket per operation plus a 1 ms step every 100 ms; lookups check both tables; inserts go to the new one.
  - Pause rehash while a snapshot walk is active so the walker sees a stable bucket array.
  - Alternative: Dragonfly's segmented table grows one segment at a time and never doubles.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: thundering herd of reconnects after a failover
- **Trigger:** 10 k client connections all retry against the new leader at once.
- **Symptom:** I/O threads flooded with TLS handshakes; queue depths spike.
- **Answer:**
  - Client library: exponential backoff with jitter, and `MOVED`/`NOT_LEADER` responses carry the new leader so clients do not poll the config service.
  - Server: connection accept rate limit, and shard queues bounded so a flood degrades to `BUSY` rather than unbounded memory.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

---

## 4. Data

## Edge case: log record format changes in a new release
- **Trigger:** adding a field (tenant id) to the record.
- **Symptom:** old binary cannot read new records; rollback breaks.
- **Answer:**
  - Version byte in every record header and in the snapshot footer. New binary reads old and new. Old binary refuses new with a clear error.
  - Rollout: followers first, then leaders, so a rollback only ever needs to read records written by the old format, as long as leadership has not moved to a new binary yet. Once a new-format leader has written, rollback of that node means re-bootstrap from a peer.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: snapshot file is corrupt but the manifest points at it
- **Trigger:** bit rot, or a crash between writing the snapshot and the manifest that somehow left a bad file.
- **Symptom:** footer checksum fails on load.
- **Answer:**
  - The write protocol makes this rare: write tmp, `fdatasync`, `rename`, `fsync(dir)`, then update the manifest the same way. The manifest never points at an unsynced file.
  - If it happens anyway: fall back to the previous manifest and snapshot (2 retained) and replay a longer log tail. Segments are only deleted after the manifest that makes them unnecessary is durable, so the longer tail exists.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: GDPR delete of a key
- **Trigger:** legal request to erase.
- **Symptom:** the value still exists in old log segments and old snapshots after `delete`.
- **Answer:**
  - `delete` writes a tombstone and removes the entry. The next snapshot does not contain it. Segments holding the old value are unlinked after the snapshot that supersedes them, so within one snapshot interval. Two retained snapshots means physical erasure within ~30 min.
  - Off-node backups in object storage need their own retention. If instant erasure is required, encrypt per tenant and destroy the key.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: data grows 3x over three years
- **Trigger:** organic growth to 180 GB per node's worth of keys.
- **Symptom:** RAM box is 128 GB.
- **Answer:**
  - First, move slots to more nodes; the design is built for it.
  - Second, the Bitcask seam: keep the index in memory, values on NVMe in the log, merge to reclaim. One NVMe read per miss, ~100 us. The WAL, snapshot (of the index), and Raft do not change.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

---

## 5. Operations

## Edge case: what pages someone at 3 am
- **Trigger:** on-call design question.
- **Answer:**
  - `wal_fdatasync_p99 > 10 ms` for 2 min: disk is dying, move leadership.
  - `shard_halted > 0` or `disk_errors > 0`: node needs draining.
  - `raft_leaderless_shards > 0` for 30 s: clients cannot write to those slots.
  - `canary_lost_write > 0`: the one alert that means the promise broke. Highest severity.
  - Tickets, not pages: snapshot age, RSS ratio, follower lag.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: rolling upgrade without losing availability
- **Trigger:** new binary.
- **Answer:**
  - Upgrade one follower per group, wait for it to catch up, verify it can read the log. Repeat. Then transfer leadership to upgraded nodes (Raft leadership transfer, no election gap). Upgrade the old leaders last.
  - Never restart a leader in place: that is a 1 to 2 s write outage per group that leadership transfer avoids.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: restart takes 30 minutes instead of 30 seconds
- **Trigger:** snapshots silently stopped a day ago.
- **Symptom:** replaying a day of log.
- **Answer:**
  - The alert `log_bytes_since_snapshot` exists for this. If it was missed, the fix during the incident is to bootstrap the node from a peer's fresh snapshot instead of replaying its own log.
  - Prevention: snapshot trigger is bytes-based, not time-based, and a stuck walk aborts and retries.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: migrating from Redis without downtime
- **Trigger:** the existing system is Redis with AOF `everysec`.
- **Answer:**
  - Phase 1: new store consumes the Redis replication stream (RDB then command stream) into its WAL. Phase 2: dual read and compare. Phase 3: flip writes via the slot map; Redis follows the new store for a rollback window. Phase 4: retire.
  - Rollback at each phase is a config flip, not a data restore. D12 in [`diagrams.md`](diagrams.md).
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

---

## 6. Security and abuse

## Edge case: a client floods one shard with writes
- **Trigger:** buggy or malicious client at 500 k writes/s to keys in one slot.
- **Symptom:** that shard's queue and log writer saturate; other tenants on the shard suffer.
- **Answer:**
  - Per-client and per-tenant rate limits at the I/O thread in ops and bytes, applied before the request enters a shard queue.
  - Bounded shard queues return `BUSY` instead of growing memory.
  - Per-tenant memory quota checked at apply time.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: replayed or forged requests
- **Trigger:** an attacker replays an old `put` with a captured `request_id`.
- **Answer:**
  - mTLS binds `client_id` to a certificate; the dedup key includes it, so a replay from a different identity is a new request under that identity's namespace, and a replay from the same identity within 5 min is a no-op that returns the stored result.
  - Raft traffic is on a separate identity; a client certificate cannot send `AppendEntries`.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: someone reads the log files off the disk
- **Trigger:** disk theft or a compromised host.
- **Answer:**
  - Segments and snapshots are encrypted with a per-node key from a KMS, rotated by re-snapshotting. The key id sits in the segment header. Values are never on disk in the clear.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident
