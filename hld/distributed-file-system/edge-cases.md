# Edge cases: strongly consistent distributed file system

Every entry answerable out loud in under 60 seconds. Categories per `hld/CLAUDE.md` §5. Confidence boxes are mine to tick.

Design recap for context: sharded Raft metadata (dentry by parent dir, inode and chunk by id), chain-replicated immutable 64 MB chunks, seal-and-move on any failure, three fencing tokens (raft term, lease epoch, chunk version). See [`solution.md`](solution.md).

---

## 1. Failure

## Edge case: metadata shard leader dies right after acking a create
- **Trigger:** leader commits the entry to a majority, replies to the client, crashes.
- **Symptom:** the client got an ack. Next call times out for ~2 s.
- **Answer:**
  - The ack was sent only after majority commit, so the entry is in at least 2 of 3 logs. Raft's leader completeness guarantees the new leader has it.
  - Election in 1 to 2 s. Client refreshes the shard map on timeout and retries with the same `(client_id, request_id)`; the dedup table returns the original result.
  - Variant: crash BEFORE majority commit. The entry is not in the new leader's log, the client's retry creates it fresh. Either outcome is consistent, never both, never neither.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: chunk server dies mid-append
- **Trigger:** tail replica stops responding while the client is streaming 4 MB frames.
- **Symptom:** the client's write call returns an error after 2 s; committed_len is reported.
- **Answer:**
  - Client never retries into the failed chunk. It calls `seal_chunk`. MDS asks the reachable replicas for their lengths, records the minimum agreed length that was acked, truncates the others to it, marks the chunk sealed in Raft.
  - Client gets a fresh chunk and re-sends bytes from committed_len. No duplicate, no gap.
  - Committed means: the head acked it, which implies all 3 fsynced. Anything past that was never promised and is truncated.
  - Repair of the dead node's other chunks starts at 10 min (60 s if it self-reported a disk failure).
- **Diagram:** `solution.md` §10.4 timeline 2.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: the head replica dies, not the tail
- **Trigger:** the node the client is streaming to goes away.
- **Symptom:** client timeout on write.
- **Answer:**
  - Same seal-and-move. The mid and tail may hold bytes the head forwarded before it died and never acked. MDS truncates them to the largest length the client was acked (client passes its `committed_len` into `seal`, MDS takes `min(client_committed, replica_lengths)`).
  - Nothing special about the head; a chain is just an ordering, the commit rule is "all three".
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: client crashes holding a write lease
- **Trigger:** a Spark executor dies with a file open for append.
- **Symptom:** the file stays "open" and no other writer can append.
- **Answer:**
  - Lease is 60 s with renews every 20 s. After 60 s without renew, the inode shard runs lease recovery: bump `lease_epoch` in Raft, tell the open chunk's replicas the new epoch (they now reject the old one), seal the tail chunk at the agreed length, mark the inode closed.
  - A new writer can open at ~61 s. A job committer that needs it faster calls `recover_lease` which does the same steps at once (the old client is fenced anyway).
  - If the dead client comes back and writes with epoch E, chunk servers answer `FENCED`.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: a whole rack loses power
- **Trigger:** 40 racks per power domain, one rack of ~40 nodes goes dark.
- **Symptom:** ~1% of chunk servers gone at once. Under-replicated count jumps.
- **Answer:**
  - Placement puts the 3 replicas of every chunk on 3 racks in 3 power domains, so every chunk still has 2 of 3 (or 10 of 14 fragments minus at most 1 per rack). Reads continue from the other replicas, writes seal-and-move.
  - Repair: 40 nodes x 100 TB = 4 PB. Budget 10% of NIC on 5,000 nodes = 1.5 TB/s cluster-wide, so ~45 min. Start delay 10 min in case it is a reboot.
  - Data-at-risk window is that ~1 h, during which a second failure in the same copyset would be a loss. Copyset placement keeps that probability under 1e-11 per chunk.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: the root shard is slow
- **Trigger:** the shard holding `/` and its top-level dentries hits a GC pause or a compaction stall.
- **Symptom:** every cache-miss path resolution slows. Cache hits unaffected.
- **Answer:**
  - Top-level dentries change rarely; the client cache with directory versions makes almost all resolutions a local hit. The `NOT_MODIFIED` version check goes to the root shard leader but is a single RocksDB get; if even that is too much, clients check versions lazily (every 5 s per directory) instead of per call.
  - Root shard runs on the best hardware and holds only the top 2 levels; everything deeper is hashed elsewhere.
  - Alert: root shard p99 over 20 ms is a ticket, over 50 ms a page.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: repair storm after a mass reboot
- **Trigger:** kernel patch reboots 500 nodes in 5 minutes.
- **Symptom:** under-replicated count spikes to 10% of chunks.
- **Answer:**
  - Repair does not start until a node has been silent for 10 min. A reboot takes 3 min. Nothing is repaired; the nodes come back and their heartbeat reconciles the chunk map.
  - If the reboot goes wrong and nodes stay down, repair starts at 10 min under the bandwidth cap and in order of "chunks with 1 copy left" first, then 2 copies.
  - The cap (10% of NIC) is the guard against repair starving user reads.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

---

## 2. Consistency

## Edge case: two metadata leaders after a partition
- **Trigger:** leader L (term 5) is cut off from its followers but still reachable by some clients and chunk servers.
- **Symptom:** none visible if the design is right. That is the point of the question.
- **Answer:**
  - Writes: L cannot commit anything (no majority). Any ack it sends must be after majority, so it sends none.
  - Reads: L serves lease-based local reads only while its lease is valid (0.9 x election timeout after its last majority heartbeat). Followers cannot elect L' until a full election timeout passes. So L's lease always expires before L' can exist. After that L falls back to ReadIndex, which fails without a majority.
  - Commands to chunk servers: L' carries term 6. Any chunk server that has seen term 6 rejects L's term-5 seal or delete. A chunk server that has not yet seen term 6 might accept a term-5 `seal` from L, but sealing at a length is idempotent and L' will re-issue with the same rule, so no divergence.
  - Leases granted by L: recorded in Raft before grant, so L' knows them and bumps epochs on recovery.
- **Diagram:** `solution.md` §5.1.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: rename `/a/x` to `/b/x` while another client deletes `/b`
- **Trigger:** two clients, two shards (hash(a) and hash(b)), racing.
- **Symptom:** the interviewer wants to know which one wins and whether `x` can be lost or orphaned.
- **Answer:**
  - Delete of directory `/b` first writes a `DELETING` intent on `/b`'s dentry and on inode b. Rename's prepare on the destination shard checks inode b for `DELETING` and refuses. Rename aborts, returns `ENOENT` for the destination parent.
  - If rename's prepare lands first, the destination shard holds an intent dentry `(b, "x")`. Delete's subtree walk sees the intent, resolves it via the coordinator (PREPARED means treat as present) and waits for the txn to finish (bounded by the 30 s txn timeout) before continuing. Delete then removes `x` as a child.
  - Intents are taken in `inode_id` order for two concurrent renames, so no deadlock. Delete-vs-rename uses the `DELETING` flag as a lock on the directory.
  - Either serialization is a valid linearizable history. `x` is never lost: its inode is unlinked only by a committed delete, and unlinked inodes go to orphans with a 24 h grace.
- **Diagram:** [`deep-dives/metadata-sharding.md`](deep-dives/metadata-sharding.md) §4.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: rename a directory into its own subtree
- **Trigger:** `rename(/a, /a/b/c)`.
- **Symptom:** would create a cycle and orphan the whole subtree.
- **Answer:**
  - Coordinator walks dst's ancestors to root before prepare (cached dentries, then re-validated by reading each ancestor's dentry with an intent check). If `src` appears, reject `EINVAL`.
  - A concurrent rename that would change an ancestor between the walk and the commit is serialized by the intent on the ancestor's dentry: the walk fails with `INTENT_PENDING` and the client retries.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: client retries an append after losing the ack
- **Trigger:** the head acked, the ack packet was dropped, client resends the same 4 MB at the same offset.
- **Symptom:** risk of duplicate bytes (this is GFS's record-append problem).
- **Answer:**
  - A chunk is append-only and an offset can be committed once. Head answers `OFFSET_ALREADY_COMMITTED, committed_len`. Client advances. No duplicate.
  - If the head died in between, the chunk is sealed at the acked length and the retry goes into a new chunk at the correct file offset. Still no duplicate because the sealed length includes the acked bytes.
- **Diagram:** `diagrams.md` D5c.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: reader with a stale chunk list reads a deleted file
- **Trigger:** client opened `/a/f` at t0, another client deleted it at t1, the first client reads at t2 after GC.
- **Symptom:** chunk server returns `GONE`.
- **Answer:**
  - Sealed chunks are immutable, so a stale chunk list is safe until GC (24 h grace). Within the grace the reader sees the old bytes, which is snapshot semantics for an already-open handle; POSIX does the same with an unlinked open file.
  - After GC the read gets `GONE`, the client re-stats, gets `ENOENT`, surfaces it. It never sees bytes from a different file because chunk ids are never reused.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: a replica missed a version bump and comes back
- **Trigger:** chunk server C was partitioned during lease recovery; the chunk's version went 1 to 2 on the other two replicas.
- **Symptom:** C holds version 1 with possibly extra unacked bytes.
- **Answer:**
  - C's heartbeat reports `(chunk, v1)`. MDS's map says v2. MDS tells C to delete v1. Until then, a client reading with `v2` in its request gets `STALE_VERSION` from C and moves on.
  - Clients always carry the version they got from MDS, so a stale replica cannot be read by accident.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: clock jumps on a metadata leader
- **Trigger:** NTP steps the wall clock forward 30 s on the leader.
- **Symptom:** risk that the leader thinks its lease is still valid when it is not, or vice versa.
- **Answer:**
  - Lease timing uses the monotonic clock, which does not step. A forward jump of the wall clock cannot extend a lease.
  - Drift, not jumps, is the real risk: the leader's monotonic clock running fast makes it think less time passed than really did. We budget 10% drift (lease is 0.9 x election timeout) and detect worse via periodic wall-vs-monotonic checks; on detection the leader drops its lease and uses ReadIndex until re-established.
  - Writer leases (60 s) are measured on the MDS side, so client clocks do not matter.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: `list` on a directory that is being written to
- **Trigger:** 10 M entries, paginated list while creates continue.
- **Symptom:** an entry created after page 3 was read shows up on page 7, or not at all.
- **Answer:**
  - Each page is a consistent RocksDB snapshot of the dentry range at a Raft index. Across pages we do not promise a snapshot; the API says so and returns the Raft index per page so a caller who cares can detect a change and restart.
  - A true snapshot listing is a snapshot (MVCC by Raft index) and is offered as `list(dir, at_index)` with a GC hold.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

---

## 3. Scale

## Edge case: one directory receives 1 M creates a minute
- **Trigger:** a Spark job writes 1 M part files into one output directory.
- **Symptom:** interviewer expects "hot shard". Push back with the number.
- **Answer:**
  - 1 M/min = 17 k creates/s on the shard owning that parent. A Raft group with 4 MB group commit does 20 to 50 k entries/s. It is fine.
  - What actually melts is per-create updates to the parent inode (mtime, entry count). Do not do them synchronously; derive count from the range, update mtime lazily.
  - Beyond ~50 k creates/s or ~10 M entries: split the directory's dentry range across k shards by `hash(name) mod k`, recorded in the parent inode; list becomes a k-way merge. Keep the seam, do not build it on day one.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: 10 k readers on the same 64 MB chunk
- **Trigger:** a broadcast join table every executor reads.
- **Symptom:** one chunk server's NIC saturates, everyone gets 200 KB/s.
- **Answer:**
  - Chunk servers report read heat per chunk in heartbeats. Above a threshold the MDS raises that chunk's replication to 10 or more; the extra replicas are copied in seconds and clients (which re-fetch the replica list on `SLOW`) spread out.
  - Sealed chunks are immutable, so a rack-local read cache needs no invalidation. Same trick GFS suggested, cheaper because we never mutate.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: 10x tomorrow, 100 B files
- **Trigger:** growth.
- **Symptom:** shards at 400 GB each, path resolution dominating latency.
- **Answer:**
  - Shard split is online: new Raft group, range moved with a RocksDB checkpoint plus log tail, shard map updated in the root group, clients refresh on `WRONG_SHARD`. Go from 200 to 2,000 shards.
  - Path resolution: add speculative resolution (InfiniFS): client predicts child inode ids from `hash(parent, name)` hints and validates all levels in one parallel round.
  - The chunk map grows to 110 B records, still hash-sharded, still linear.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: small files, 9 B under 1 MB
- **Trigger:** interviewer asks if 64 MB chunks waste space.
- **Answer:**
  - Chunks are variable length up to 64 MB, so a 100 KB file is a 100 KB chunk. No disk waste.
  - The cost is one chunk record and 3 replicas per small file, which is in the metadata math. EC does not apply to files smaller than a stripe; they stay replicated. If small files dominate bytes, pack them: many small files into one 64 MB container chunk with per-file offsets in the inode. That is the Haystack / Tectonic blob trick and it is a seam, not day one.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

---

## 4. Data

## Edge case: silent bit rot nobody reads for a year
- **Trigger:** a sector flips on one replica of a cold chunk.
- **Symptom:** none until read. That is the danger.
- **Answer:**
  - Scrubber on every chunk server re-reads every chunk every 14 days at 1% of disk bandwidth, verifies CRC32C per 64 KB, reports mismatches. MDS re-replicates from a good replica (or rebuilds the fragment from 10 others for EC).
  - Reads also verify CRC and fail over, so a client never returns corrupt bytes.
  - Alert on scrub corruption rate above baseline; a rising rate on one node means a failing disk.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: erasure-code conversion crashes halfway
- **Trigger:** encoder wrote 9 of 14 fragments and died.
- **Answer:**
  - The chunk's Raft record still says `sealed, replicas [a,b,c]`. Fragments without a committed layout are garbage; a GC pass deletes fragments whose chunk record does not reference them. The encoder retries from scratch. Replicas are deleted only after the `encoded` layout is committed in Raft and all 14 fragments have been read back and verified.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: schema change on the metadata records
- **Trigger:** add a field to the inode (say, a per-tenant encryption key id).
- **Answer:**
  - Records are protobuf in RocksDB; new fields are additive. Readers of version N-1 ignore unknown fields (enforced in CI so rollback stays possible).
  - Raft log entries are also versioned; a leader never emits an entry version a follower in the group does not support (the group negotiates the min version on membership change).
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: GDPR delete of a tenant
- **Trigger:** delete everything tenant T ever wrote, including DR copies and snapshots.
- **Answer:**
  - Tenant data is encrypted with a per-tenant key from KMS at the chunk server. Delete the key: every chunk, on both DCs and in every snapshot, becomes unreadable at once. Then run the ordinary recursive delete and let GC reclaim space.
  - Metadata (names, sizes) is deleted by the recursive delete; DR log shipping carries the deletes.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: 3-year growth of the chunk map
- **Trigger:** 11 B chunk records today, 40 B in 3 years.
- **Answer:**
  - Chunk shards are hash-sharded by chunk id and split online like namespace shards. The repair index `node_chunks` grows per node not per cluster (6.6 M records per node today).
  - The thing to watch is heartbeat payload: full reports of 25 M chunks per node every 6 h is fine; keep incremental reports as the norm.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

---

## 5. Operations

## Edge case: what pages at 3 am
- **Answer:**
  - Any chunk with fewer than 2 live copies (or < 11 of 14 fragments). Any shard leaderless for 30 s. Raft apply lag over 5 s. DR lag over 15 min. Under-replicated over 0.01% for 30 min. Root shard p99 over 50 ms.
  - Everything else is a ticket: scrub corruption above baseline, repair bandwidth pinned at cap for an hour, disk AFR trend.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: rolling upgrade of the metadata tier
- **Answer:**
  - One follower at a time per shard, leader last (transfer leadership first so there is no election), at most 5% of shards in flight. RocksDB schema and log entry versions are N-1 compatible, verified in CI, so rollback is a redeploy.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: migrate from HDFS without downtime
- **Answer:**
  - Shadow the metadata (mirror NameNode edits, diff nightly), dual-write `/tmp`, per-directory router flip in the client library with flip-back as rollback, background block copy with checksum verification, HDFS read-only, decommission. D12 in `diagrams.md`.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: datacenter loss
- **Trigger:** primary DC unreachable.
- **Symptom:** everything down. RPO question.
- **Answer:**
  - Standby has every shard's Raft log to within seconds and sealed chunks to within minutes. Promote: root group in the standby takes the last shipped shard map, each shard's receiver becomes a Raft group, chunk map entries whose chunk copy has not arrived are marked `missing` and their files return `EIO` on read until an operator decides.
  - RPO ~15 min of sealed data and seconds of metadata. RTO ~1 h of runbook. This does not contradict "strongly consistent" because the consistency promise was per cluster; we say so in the requirements.
  - RPO 0 is available per directory by stretching that directory's shards across 2 DCs plus a witness, at +RTT per metadata op. See [`deep-dives/disaster-recovery.md`](deep-dives/disaster-recovery.md).
- **Confidence:** [ ] shaky [ ] ok [ ] confident

---

## 6. Security and abuse

## Edge case: a client tries to write to a chunk it does not own
- **Answer:**
  - Every write carries the capability token MDS issued at open (signed, bound to inode and chunk ids, mode, lease epoch, expiry). Chunk servers verify the signature offline. No token, or a token for a different inode, is rejected without any MDS call.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: one tenant floods metadata with 1 M stats/s
- **Answer:**
  - Per-tenant token bucket at each shard, 429 with backoff. Tenant identity comes from mTLS, not from the request body. Per-tenant byte/s caps at chunk servers. Quotas per directory stop disk fill.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: a client sends bytes whose CRC does not match
- **Answer:**
  - Head verifies CRC32C before forwarding. Mismatch is rejected, nothing is written, so a buggy or hostile client cannot poison a replica. Checksums are stored with the data so a later read verifies end to end.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

---

## Bonus: "why not GFS"

## Edge case: interviewer asks why GFS is not strongly consistent
- **Answer, four points:**
  - Record append is at-least-once: a failed replica plus retry leaves duplicates and padding in the file; readers must dedupe. We have one fenced writer and never retry into a failed chunk, so appends are exactly-once.
  - Stale replicas: a chunk server that missed a mutation can serve old data if the client does not check versions. We put the version in every read and every heartbeat.
  - Single master: a scale ceiling in RAM and a SPOF with minutes of replay on restart. We shard into Raft groups on RocksDB with 2 s failover.
  - "Defined but inconsistent" regions after concurrent writes: GFS allows multiple writers; we do not.
- **Confidence:** [ ] shaky [ ] ok [ ] confident
