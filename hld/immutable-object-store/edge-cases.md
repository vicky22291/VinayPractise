# Edge cases: immutable distributed object store

Every entry answerable out loud in under 60 seconds. Categories per `hld/CLAUDE.md` §5. Confidence boxes are mine to tick.

Design recap for context: stateless gateways; range-partitioned Raft metadata keyed by `(bucket, key, version)` with a witness for cached records; objects under 8 MB appended as needles to 3x REPL3 volumes (1 replica per AZ) and encoded RS(9,6) after seal; objects 8 MB and up encoded inline into EC96 volumes (15 fragments, 15 racks, 5 per AZ); the object record's Raft commit is the only commit point; single writer per extent fenced by lease + epoch; seal-and-move on any failure. See [`solution.md`](solution.md).

---

## 1. Failure

## Edge case: gateway dies after all fragments are written, before the metadata commit
- **Trigger:** process crash, OOM, or a deploy kills the gateway between the last storage ack and the Raft commit.
- **Symptom:** client sees a connection reset, retries. Orphan-bytes counter ticks up.
- **Answer:**
  - Nothing is visible. The object exists only when its record commits, and the record was never proposed.
  - The volume lease expires in 30 s; the volume shard bumps the epoch, seals the volume at the last offset all fragments agree on, and any late append from the dead gateway is `FENCED`.
  - The retry goes to another gateway, writes fresh bytes into its own volume, commits, and gets a version. The first attempt's bytes are found by the reconciler (extent contents vs index) and marked garbage within 24 h.
  - No half object, no duplicate version, no data loss. Immutability means there is nothing to roll back.
- **Diagram:** `solution.md` §10.4 timeline 1.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: client got `200`, and a storage node holding its bytes dies one second later
- **Trigger:** disk or node death right after a PUT.
- **Symptom:** none for the client. Volume goes to 14 of 15 (or 2 of 3).
- **Answer:**
  - The `200` was sent only after the record committed, and the record was proposed only after all 15 fragments (or 3 replicas) acked an fsync. So 14 durable fragments remain; k = 9.
  - Reads decode from any 9. Repair rebuilds the missing fragment from 9 others onto a new disk, seconds for one volume, ~2 h for the whole disk's 1,600 volumes at the steady budget.
  - The window in which a second, third... seventh failure would matter is that ~2 h; independent-failure probability of 6 more losses inside it among the specific 14 disks is ~1e-36. Correlated risk is bounded by placement (1 per rack, 5 per AZ).
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: one of the 15 fragment appends times out mid-object
- **Trigger:** a disk stalls or a node reboots while a gateway is streaming a large object.
- **Symptom:** one 4 MB append does not ack in 2 s.
- **Answer:**
  - Never retry into the failing extent. Gateway calls `seal(volume, last_full_row)`; the volume shard seals every extent at that row and truncates the partial row on the 14 that have it.
  - Gateway allocates a fresh volume and re-sends from the unacked row. The object record ends up with two segments. Committed objects in the sealed volume are untouched.
  - The volume is now 14 of 15 for its sealed content and repairs normally.
- **Diagram:** `solution.md` §10.4 timeline 2.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: metadata shard leader dies right after committing a PUT
- **Trigger:** leader commits to a majority, crashes before replying.
- **Symptom:** gateway times out on the commit RPC; the key range stalls 1 to 2 s.
- **Answer:**
  - The entry is on a majority; Raft leader completeness guarantees the new leader has it and applies it.
  - Gateway retries the commit with the same request id at the new leader; the dedup table returns the original outcome and version id. If the entry had NOT reached a majority, the retry commits it fresh. Either way: exactly one visible version.
  - New leader's witness set is empty, so for 60 s every witness call answers "changed" and gateways do full reads. Latency up, correctness intact.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: a whole rack loses power
- **Trigger:** 32 storage nodes, ~1,150 disks, ~2.5% of one AZ.
- **Symptom:** ~1.8 M volumes go to 14 of 15 at once. Under-replicated count spikes.
- **Answer:**
  - Placement puts at most one fragment of any volume in a rack, so no volume loses more than one. All readable without decode for REPL3 (2 left), with decode for EC96 objects whose covering fragment was there.
  - Repair waits 10 min (racks come back), then runs at the event budget (60 MB/s per disk): 1,150 x 24 TB x 9 read amplification over 45 k peers is ~6 h. During that window a second rack loss still leaves 13 of 15.
  - If the rack comes back within 10 min, nothing was rebuilt; the extents are verified by inventory heartbeat and the volumes go back to 15 of 15.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: an AZ goes dark
- **Trigger:** power or network loss for a third of the fleet.
- **Symptom:** every Raft group at 2 of 3; every EC volume at 10 of 15; every REPL3 at 2 of 3. Leaders in the dead AZ re-elect in 1 to 2 s.
- **Answer:**
  - Reads: all data readable. Objects whose covering fragment was in the dead AZ decode from 9: 9x read amplification and higher p99 on a third of reads. Gateways in the two surviving AZs take 1.5x load; sized for it.
  - Writes: continue. New volumes are placed 8/7 across the two surviving AZs (still "any 6 disks"). Rebalanced to 5/5/5 when the AZ returns.
  - Repair of AZ-scoped loss waits 4 h: an AZ blip must not trigger a 280 PB rebuild. Disk-scoped repair continues.
  - Why RS(9,6) and not RS(10,4): an AZ takes 5 of 15; with k = 10 over 14 fragments (5/5/4) an AZ loss leaves 9 or 10, so some volumes are unreadable. k = 9 with 6 parity survives an AZ plus one disk. The 1.5x floor for AZ tolerance over 3 AZs is the point to make.
- **Diagram:** `diagrams.md` D9.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: the volume shard (placement map) is unavailable
- **Trigger:** Raft election in a volume shard, or a bug.
- **Symptom:** gateways cannot allocate new volumes or renew leases.
- **Answer:**
  - Reads are unaffected: gateways cache the full volume map (11 GB) and read fragments directly.
  - Writes continue for 30 s on already-leased open volumes (4 REPL3 + 4 EC96 per gateway, ~8 GB of headroom each), then fail with `503` until the shard is back. Election is 1 to 2 s, so this is invisible in practice.
  - Volume shards are hash partitioned across many groups; one election affects 1/N of allocations.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: the KMS is down
- **Trigger:** KMS outage or throttling.
- **Symptom:** DEK unwrap fails for uncached KEKs.
- **Answer:**
  - Gateways cache unwrapped per-bucket KEKs for 5 min and extend to 1 h under KMS failure (a documented, alerted degradation). Active buckets keep serving.
  - A bucket not touched in an hour cannot be read or written until KMS returns. That is the trade for crypto-shred deletes; say it.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

---

## 2. Consistency

## Edge case: two clients PUT the same key at the same time
- **Trigger:** two Spark drivers commit `_delta_log/000123.json` with `If-None-Match: *`.
- **Symptom:** exactly one `200`, one `412`.
- **Answer:**
  - Both write their bytes into different volumes. Both propose a commit entry. The shard's Raft log orders them; apply is single-threaded per shard and evaluates the precondition against the current record.
  - First entry inserts; second sees the key present and records a `412` outcome for its request id. The `412` response carries the winner's etag so the loser can read the committed commit without another round trip.
  - Without a precondition, both insert and the later log entry is the newest version; a reader sees one or the other, never a mix, because the record is atomic.
  - The loser's bytes are orphans, reclaimed by the reconciler.
- **Diagram:** `solution.md` §4.5.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: reader gets a stale record from the gateway cache
- **Trigger:** client A PUTs v8; client B on another gateway has v7 cached and GETs.
- **Symptom:** must return v8.
- **Answer:**
  - No cached record is ever served without a witness answer from the shard leader: "has this key changed since LSN x?" The witness set is updated in the same apply step that inserted v8, so it says "changed", and the gateway does a full read.
  - The witness set covers the last 60 s of modifications; a key not in it has not changed since the leader's set started, and the gateway's cached LSN is compared against that start to be safe.
  - Cost: one in-memory RPC per GET. This is S3's design post-2020.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: LIST while a job is writing into the prefix
- **Trigger:** planner lists `table_x/` while 1,000 part files/s are being committed.
- **Symptom:** does the listing include the new files?
- **Answer:**
  - Each page is a linearizable snapshot at the shard's applied LSN when the page request started: any PUT acked before the request is in the page if its key falls in the page's range.
  - Across pages there is no snapshot: a key inserted between page 1 and page 2 that sorts inside page 1's range is missed; one that sorts after the cursor is seen. Documented; S3 behaves the same. Delta does not depend on LIST for correctness (the log is authoritative), which is the right layering.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: retry after a lost ack creates a duplicate version?
- **Trigger:** PUT commits, ack lost, client retries on another gateway.
- **Symptom:** one visible version or two?
- **Answer:**
  - The retry carries the same request id. The second gateway writes bytes again (it cannot know), proposes a commit, and the apply step finds the request id in the 10 min dedup table and returns the original version id. One version; the second bytes are orphans.
  - After 10 min the retry commits a new version v+1 and v becomes noncurrent. Still one current version, and the client asked for a PUT and got one; on a versioned bucket it sees an extra noncurrent version, which lifecycle expires.
- **Diagram:** `diagrams.md` D5.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: compactor moves an object while a client is reading it
- **Trigger:** volume 4711 hits 30% garbage; compactor copies object k to 4790 and CASes the record.
- **Symptom:** reader holding `(4711, offset)` mid-stream.
- **Answer:**
  - The old volume is marked DRAINING and kept for 24 h after the last CAS; readers finish. A gateway with a stale record that starts a new read within 24 h still succeeds; after that it gets `GONE`, refreshes the record, reads from 4790.
  - The CAS on the record compares `(version_id, old segment list)`; a concurrent new version on the same key does not conflict (different version), a concurrent compaction does (second CAS fails, its copy is garbage).
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: a stale gateway appends to a volume it no longer owns
- **Trigger:** gateway pauses (GC, network) past its 30 s lease; the volume shard reassigns or seals the volume; the gateway wakes and sends the next row.
- **Symptom:** append with epoch 3 arrives at extents that are at epoch 4.
- **Answer:**
  - Storage nodes persist the highest epoch per extent and reject lower: `FENCED`. The gateway drops the volume, re-reads its lease state, and moves the unacked rows to a fresh volume.
  - Nothing it wrote before the fence is harmed: rows before the seal point are complete and immutable; rows after it were truncated at seal and no record points at them.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

---

## 3. Scale

## Edge case: a Spark job writes 10 k files/s into one prefix
- **Trigger:** `part-00000 ... part-09999` under `table_x/` every second; keys are monotonic.
- **Symptom:** all commits land on the one shard whose range covers the prefix.
- **Answer:**
  - 10 k commits/s of ~400 B is 4 MB/s of Raft log on one leader; a shard on NVMe does 20 to 50 k/s. It holds. The real risks are RocksDB write stalls (4 x 64 MB memtables, L0 trigger tuned) and reads sharing the leader.
  - Load split at 10 k commits/s for 5 min gives the prefix its own shard; split does not spread monotonic keys, so the ceiling is one leader. Above ~20 k PUT/s into one prefix: `503 Slow Down`, and the bucket owner can opt into salted ranges (`hash % 16 || key`, 16x list cost).
  - This is why S3 documents 3,500 PUT/s per prefix and why it withdrew "randomize your prefixes" once auto-split existed.
- **Diagram:** `solution.md` §5.2.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: one 10 KB object gets 100 k GET/s
- **Trigger:** every executor reads `_delta_log/_last_checkpoint` at job start.
- **Symptom:** one disk (REPL3) or one fragment (EC96) is asked for 100 k IOPS; one shard leader gets 100 k witness calls/s.
- **Answer:**
  - Witness calls are in-memory, ~50 us; one leader takes 1 M/s. Fine.
  - Content: the gateway content cache is keyed by `(volume, offset, len)` and is correct forever because extents are immutable. Per-chunk counters gossip the top-1000 hot chunks every second; above 1 k reads/s a chunk is replicated to every gateway's RAM. Absorbed in ~2 s; during those 2 s the disk serves at its 16-deep queue and the rest get `503`.
  - No CDN, no cache cluster; the immutability is the invalidation story.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: 70 billion objects under 1 MB
- **Trigger:** Delta JSON commits, checkpoints, small Parquet, images.
- **Symptom:** is the index bigger than the data? Do small objects waste disk?
- **Answer:**
  - Small objects are 4.5 PB of bytes and 21 TB of metadata (70 B x 300 B): 0.5%. Data still dominates, but the metadata tier is sized by count, not bytes: 2,000 shards, 300 nodes.
  - On disk they are packed as needles into 1 GB extents, so no per-object file or inode; one seek per read; after seal the extent is encoded as a unit, so small objects get 1.67x too.
  - Evolution: inline objects under 4 KB into the record (MinIO inlines up to 128 KiB) to save the needle write; gated per bucket because it grows RocksDB.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: LIST a prefix with 1 billion keys
- **Trigger:** `list(bucket, prefix="logs/")`.
- **Symptom:** 1 M pages of 1,000.
- **Answer:**
  - Range partitioning makes the prefix a contiguous range over ~100 shards (20 GB each). Each page is one ordered iterator scan on one shard, ~1 ms; crossing shards is a cursor hand-off.
  - With a delimiter, a directory of 1 M files under `logs/2026/` costs one seek (skip to `logs/20260`), so a "directory listing" is cheap regardless of fan-in.
  - The 1 M-page walk is the client's problem, as on S3; we offer `max-keys` up to 1,000 and a strongly consistent page, nothing more.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: 10x traffic tomorrow
- **Trigger:** 500 k PUT/s, 5 M GET/s, 10 TB/s egress.
- **Symptom:** which tier bends first?
- **Answer:**
  - Gateways: linear, 2,000 boxes. Storage: bandwidth linear with disks, and 500 PB of disks already have 20x NIC headroom; random IOPS at 4 M/s over 45 k HDDs is 90 IOPS per disk, at the HDD limit. Fix: the content cache absorbs the skewed part; the flat part needs an SSD tier for hot REPL3 volumes.
  - Metadata: 650 k commits/s over 2,000 shards is 325/s each; fine. Witness 5 M/s is 2.5 k/s per shard; fine. Skew is still the only metadata risk.
  - So: disks' random IOPS bend first, and the answer is placement of hot volumes on flash, not more metadata.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: adding 100 storage nodes
- **Trigger:** capacity expansion.
- **Symptom:** must data move?
- **Answer:**
  - No. Placement is a central policy, not a hash ring: new volumes are allocated preferentially on emptier disks (weighted by free space and rack/AZ balance), so new writes fill the new nodes. Nothing is rebalanced by force.
  - A background mover drains hot old disks at low priority if IOPS balance matters. With CRUSH or consistent hashing, ~2% of all data would move on day one whether we wanted it or not.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

---

## 4. Data

## Edge case: a second disk dies during repair of the first
- **Trigger:** disk A dies at t0; disk B, which shares ~1% of A's volumes (scatter width 100), dies at t0 + 1 h.
- **Symptom:** ~16 volumes at 13 of 15.
- **Answer:**
  - Still 4 above k. Repair reprioritizes: 13-of-15 volumes go to the front of the queue, at the event budget. Each is 1 GB per fragment; seconds each.
  - A seventh concurrent loss among the same 15 disks in the same window is what it takes to lose data; with 1 per rack and 5 per AZ that is a multi-rack correlated event, which is the DR conversation, not the repair one.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: scrub finds a fragment with a bad checksum
- **Trigger:** 14-day scrub re-reads an extent and a 64 KB block fails CRC32C.
- **Symptom:** one fragment of one volume is wrong; the volume is still 15 of 15 by inventory.
- **Answer:**
  - The storage node reports `(volume, fragment, bad blocks)`; the volume shard marks the fragment BAD, which is the same as MISSING for repair: rebuild from 9 others onto a different disk, then delete the bad extent.
  - Reads that hit the bad block before scrub would have failed CRC at the gateway and triggered the same path immediately. FAST '08: 0.86% of nearline disks show mismatches over 41 months, so this happens weekly at 45 k disks.
  - The disk gets a strike; three strikes and it is drained.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: GDPR delete on an object inside an erasure-coded volume
- **Trigger:** "erase this user's file within 30 days."
- **Symptom:** the bytes are 1/9th of a 114 MB fragment on 15 disks and also in the DR copy and the gateway caches.
- **Answer:**
  - Delete removes the record, and the record holds the only wrapped copy of the object's DEK. From that commit, every copy of the ciphertext is unreadable: on disk, in DR, in caches. That is the compliance answer at t0.
  - Physical reclaim: the volume's garbage counter rises; compaction is forced for any volume holding deleted data older than 20 days, so ciphertext is overwritten within the 30-day SLA. Audit log records both events.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: delete on a volume that is only 5% garbage
- **Trigger:** a few objects deleted from a mostly live volume.
- **Symptom:** space not reclaimed.
- **Answer:**
  - Correct and intended: rewriting 95% live bytes to reclaim 5% is 19x write amplification. Threshold is 30% (2.3x). Space is reclaimed when the volume ages into garbage or the 20-day forced compaction for deleted data kicks in.
  - Cost line: at steady state ~10% of raw capacity is "deleted, not yet reclaimed". Budgeted.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: 3 years of growth, 3x the objects
- **Trigger:** 300 B objects, 1.5 EB.
- **Symptom:** metadata 90 TB, volume map 33 GB, 170 M volumes.
- **Answer:**
  - Shards split to 6,000; metadata nodes to 900. Root shard map stays tiny. Volume map no longer fits in every gateway's RAM; cache it by volume-id range with per-range versions.
  - Repair time per disk is unchanged (it depends on scatter width, not fleet size). Scrub cadence unchanged. Compaction write amplification unchanged. Nothing gets worse per byte; only counts grow.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: record format changes (new field)
- **Trigger:** add a `storage_class` field.
- **Symptom:** rolling deploy with N and N-1 readers.
- **Answer:**
  - Records are protobuf-style with unknown-field preservation; N-1 ignores the field, N defaults it when absent. No backfill. Enforced in CI by reading an N record with N-1 code.
  - Extent formats are additive with a version byte in the extent header; nothing rewrites old extents.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

---

## 5. Operations

## Edge case: what pages at 3 am
- **Trigger:** on-call rotation.
- **Symptom:** the alert list.
- **Answer:**
  - Page now: any volume under 11 of 15 or under 2 of 3; the reconciler finding a committed record pointing at missing or corrupt bytes (this is "we lost data"); any shard without a leader for 30 s; PUT or GET error rate above 0.1% for 5 min.
  - Page soon: under-replicated above 0.01% for 30 min; Raft apply lag above 5 s; one shard above 15 k commits/s for 5 min.
  - Ticket: repair at cap for 2 h, orphan bytes above 0.1%, scrub mismatches above 2x baseline, multipart uploads older than 7 days.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: rolling out a new encoder and it has a bug
- **Trigger:** a build computes parity wrong.
- **Symptom:** objects read fine while all 9 data fragments are present; degraded reads return garbage.
- **Answer:**
  - Defence 1: the gateway verifies the client's full-object checksum on every read, so a wrong decode is a `500`, never wrong bytes.
  - Defence 2: CI fuzzes the encoder against a reference decoder with random erasures.
  - Defence 3: canary 1% of gateways; a background verifier decodes a sample of every canary's volumes with 6 fragments withheld.
  - Blast radius if all three fail: objects encoded by the canary in its window. Fix: re-encode those volumes from the data fragments (still correct), a list the volume shard can produce by encoder version.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: GC deletes a live volume
- **Trigger:** a bug in the compactor or the reconciler.
- **Symptom:** the one page that means data loss.
- **Answer:**
  - Defences: 24 h grace between DRAINING and DELETED; the deleter refuses to remove an extent that any object record references (it re-checks the index right before the delete); every GC binary ships with a dry-run mode whose "would delete" counters must match a model for 24 h before real deletes are enabled; deleted volume ids are not reused for 30 days so a mistaken delete is detectable.
  - If it happens anyway: the DR copy (RPO minutes) is the restore path, and the reconciler's alert lists exactly which records point at missing bytes.
- **Diagram:** `diagrams.md` D11.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: migrating a bucket off S3 and rolling back halfway
- **Trigger:** phase 3 (writes cut over) hits a bug.
- **Symptom:** need to go back to S3 without losing writes made to the new store.
- **Answer:**
  - Phase 3 keeps S3 as read fallback and never deletes from S3. Rollback: flip the SDK router to dual-write again and replay the new store's apply stream (records since cutover) into S3 as PUTs, ordered per key. Hours, not days, because only the delta moves.
  - Nothing is deleted from S3 until 30 days of zero fallback reads in phase 5.
- **Diagram:** `diagrams.md` D12.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: cut the storage bill in half
- **Trigger:** finance.
- **Symptom:** 850 PB raw at ~$15 M/yr.
- **Answer:**
  - Lifecycle first: measure what is not read for 90 days (typically 60 to 80% of a lake), move it to a cold tier encoded RS(17,3) in one AZ plus an async copy (1.18x plus copy, or 1.18x alone if the owner accepts AZ-loss RPO). That halves the raw bytes for that data.
  - Then: compaction threshold from 30% to 20% garbage (reclaims ~5% of raw for 1.5x more compaction I/O), expire noncurrent versions sooner, abort multipart at 1 day.
  - Do not touch RS(9,6) for hot data; that is the AZ-tolerance requirement, and it is the cheapest code that meets it.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

---

## 6. Security and abuse

## Edge case: a tenant floods one key or one prefix
- **Trigger:** buggy client loops on GET of one object, or PUTs 100 k/s into one prefix.
- **Symptom:** hot object or hot shard.
- **Answer:**
  - GET flood: absorbed by the content cache within 2 s, then the per-tenant token bucket at the gateway returns `503 Slow Down` with `Retry-After`. Other tenants unaffected.
  - PUT flood: the shard's commit budget is fair-queued per tenant; the flooding tenant gets `503`, neighbours on the same shard keep their share, and a split moves the flooding prefix to its own shard within minutes.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: client sends a checksum that does not match the body
- **Trigger:** corrupted upload, or a malicious client trying to poison a fragment.
- **Symptom:** gateway computes CRC64NVME as bytes stream; mismatch at the end.
- **Answer:**
  - `400 BadDigest`, no commit. Bytes already appended are orphans; reconciler reclaims. Storage nodes also verify the per-chunk CRC32C the gateway computed, so a gateway bug cannot write a fragment whose checksum does not match its own bytes.
  - A client cannot influence parity or another object's bytes: it never talks to storage nodes.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: presigned URL leaks
- **Trigger:** a URL for `GET /b/secret` is pasted somewhere public.
- **Symptom:** anyone can fetch until expiry.
- **Answer:**
  - URLs carry an expiry (default 15 min, max 7 days) and are bound to method, key, and optional IP; the gateway still enforces the bucket policy at request time, so revoking the signing key or the policy kills the URL immediately. Audit log records the reads.
  - Storage nodes are not reachable from outside; the URL is only a capability to call the gateway.
- **Confidence:** [ ] shaky [ ] ok [ ] confident
