# Edge cases: Slack / large-scale messaging platform

Every entry answerable out loud in under 60 seconds. Categories per `hld/CLAUDE.md` §5. Confidence boxes are mine to tick.

Design recap for context: gateways hold sockets and per-channel subscription sets; a consistent-hash ring of leased channel owners assigns a gapless `seq` per channel and does a conditional quorum write; fan-out is once per gateway; clients hold a `last_seen_seq` per channel and pull on any gap; unread = `head_seq - last_read_seq`. See [`solution.md`](solution.md).

---

## 1. Failure

## Edge case: owner persists the message, then dies before acking the sender
- **Trigger:** owner node crash or partition between the LWT apply and the response.
- **Symptom:** sender sees a spinner, times out after ~5 s, client retries.
- **Answer:**
  - The row `(C, seq)` is on a quorum. The lease expires in 10 s, the ring moves the channel, the new owner CASes the epoch and loads `head_seq` from the store, so it knows `seq` is taken.
  - The client retry carries the same `client_msg_id`. The new owner's LRU is empty, so it checks the `dedup` table `(C, client_msg_id) -> seq` (24 h TTL), finds it, returns the original seq. No duplicate.
  - Fan-out may never have happened. The new owner re-delivers the last N seqs above what gateways report as delivered on resubscribe; any client that missed it fills the gap on its next event or `/sync`.
- **Diagram:** `solution.md` §5.1.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: old owner is alive but partitioned (GC pause, network split), new owner elected
- **Trigger:** lease expired while the old process was paused; it wakes up and thinks it still owns the channel.
- **Symptom:** none visible if the fences work. Metrics show `EPOCH_STALE` rejections.
- **Answer:**
  - Two independent fences. (1) Its writes carry `epoch 7`; the head row is at 8; the conditional write fails. (2) Even ignoring the epoch, it would insert `(C, 1005) IF NOT EXISTS` and the new owner already wrote 1005. It cannot commit anything.
  - It could still push a stale in-memory event to a gateway. Every `deliver` carries the epoch; the gateway drops anything from an epoch lower than the latest it has seen for that channel.
  - Once it renews its lease it sees the ring changed and unloads the actor with `NOT_OWNER`.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: gateway dies with 200 k sockets
- **Trigger:** node crash, kernel panic, bad deploy.
- **Symptom:** 0.5% of users see "reconnecting" for 1 to 60 s.
- **Answer:**
  - Nothing durable was on the gateway. Clients reconnect with exponential backoff and full jitter; other gateways admit 500/s each; the storm spreads over ~30 s.
  - New gateways subscribe to owners only on the first socket per channel per gateway, so 200 k sockets x 200 channels becomes ~1.5 M subscribes, not 40 M.
  - Owners drop the dead gateway from their subscribed sets after 3 missed heartbeats (15 s), so no events are queued into the void.
  - Clients `/sync` and apply the gap rule; anything delivered during the window is pulled.
- **Diagram:** `solution.md` §10.4 timeline 1.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: coordination store (etcd / Consul) loses quorum
- **Trigger:** 3 of 5 nodes down, or a network partition around it.
- **Symptom:** ring watches stop updating; no immediate user impact.
- **Answer:**
  - Owners keep serving on their last known lease view. Leases cannot expire either (nobody to expire them), so the ring is frozen but consistent. Nothing breaks until an owner also dies, at which point that owner's channels cannot fail over.
  - Page immediately. The exposure window is "coordination outage AND owner failure".
  - Safety argument: a frozen ring never has two owners for one channel, because no reassignment can happen. Liveness, not safety, is what is at risk.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: message store loses one AZ
- **Trigger:** AZ outage.
- **Symptom:** LWT p99 rises (fewer replicas to reach quorum quickly), no errors.
- **Answer:** RF 3, one per AZ, LOCAL_QUORUM needs 2. Writes and reads continue. Hinted handoff / repair catches the replica up on return. Two AZs down means quorum lost: sends fail, reads from the surviving replica are allowed at CL ONE for history only (stale is acceptable for paging, not for the head).
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: Kafka is down for an hour
- **Trigger:** broker outage, ISR shrink below `min.insync.replicas`.
- **Symptom:** mention badges and push notifications stop updating; messages keep flowing.
- **Answer:**
  - Nothing on the send path depends on Kafka. The owner buffers side events briefly (bounded, 1 min) then drops them and records the `(channel, seq)` range it dropped.
  - On recovery a backfill job replays that range from the message store into the topics. Consumers are idempotent on `(channel, seq)`.
  - Explicitly accepted degradation: a badge may be wrong for an hour. Unread counts are cursor-based and unaffected.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: home region is lost
- **Trigger:** regional outage.
- **Symptom:** every send to a workspace homed there fails; sockets stay up; history reads fail.
- **Answer:**
  - RTO ~10 min: health probes fail for 60 s, a human confirms the page, the DR replica is promoted, an owner ring starts in the DR region and actors load heads from the promoted store, the workspace home pointer flips, gateways resubscribe.
  - RPO ~2 s: async replication lag. Messages acked in that window are lost. Say this plainly. Unacked ones are re-sent by clients (same `client_msg_id`).
  - Workspaces that pay for it get synchronous cross-region quorum: RPO 0 at +80 ms per send.
- **Diagram:** `solution.md` §10.4 timeline 3.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

---

## 2. Consistency

## Edge case: two users send to the same channel in the same millisecond
- **Trigger:** concurrency.
- **Symptom:** none. Everyone sees the same order.
- **Answer:**
  - Both appends land in the same channel actor's mailbox. The actor processes them one at a time; the first dequeued gets `seq N`, the second `N+1`. Which one is first is arbitrary but it is the same for every reader forever, because every reader gets `seq` from the store or from that actor.
  - Client timestamps are stored for display only. Snowflake-style ids would be unique but not ordered.
  - The batcher may put both in one LWT batch; the order inside the batch is the assignment order.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: client times out and retries; is the message duplicated?
- **Trigger:** response lost after the write applied.
- **Answer:** `client_msg_id` is a UUID minted on the client. Owner LRU (1 k per channel) hits in the common case; the `dedup` table (24 h) hits after failover or eviction. Both return the original `seq`. A retry after 24 h would duplicate; clients do not retry unsent messages older than 1 h without asking the user.
- **Diagram:** `diagrams.md` D5.4.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: push arrives out of order or with a gap at the client
- **Trigger:** gateway resync, socket flap, two gateways during a reconnect overlap.
- **Answer:** The client keeps `last_seen_seq` per open channel. On receipt of `N`: `N == last + 1` apply; `N <= last` drop; `N > last + 1` do `GET after=last` and apply the result before anything newer. Push is never trusted for completeness; it is a latency optimisation over pull. Telegram's `pts` rule.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: read on the phone, laptop still shows a badge
- **Trigger:** cursor advanced on one device.
- **Answer:** `POST /read` writes `last_read_seq = max(old, new)` and appends a `read(C, seq)` event to the user's own topic `user:{id}`, which fans out to all of that user's sessions through the same owner and gateway path. Converges in one delivery latency. If the laptop's socket is down it sees the cursor at `/sync`. A stale device reporting an older read cannot move the cursor backwards because of the `max`.
- **Diagram:** `diagrams.md` D4.4.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: message edited while a device is offline
- **Trigger:** offline device holds the original; an edit event with a later seq exists.
- **Answer:** The edit is a row with its own `seq`, `type = edit`, `target_seq`. Catch-up returns it in order after the original; the client applies it. History pages return the materialised current body (the owner also updates the target row in place), so a fresh page never shows a stale body. Both views agree because the same owner wrote both in one batch.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: user is removed from a channel while a message is in flight to them
- **Trigger:** admin removes Bob; a message was delivered to Bob's gateway 10 ms earlier.
- **Answer:** The membership check is at `append` (sender) and at `subscribe` (receiver), with the owner's membership cache invalidated by the leave event. Bob may see one message that was fanned out before the leave applied. That is a delivery-latency-sized window and is accepted. History reads after the leave are denied at the API by the membership check, so he cannot page it back.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: gateway receives events for a channel from two epochs during failover
- **Trigger:** old owner re-sends buffered events after the new owner started.
- **Answer:** Every `deliver` carries `owner_epoch`. The gateway tracks the max epoch seen per channel and drops lower epochs. Within an epoch, per-session `last_delivered` plus the gap rule handles order.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

---

## 3. Scale

## Edge case: `@channel` in a 100 k member channel
- **Trigger:** one send with a broadcast mention.
- **Symptom:** naive design: owner does 100 k sends, 100 k counter writes, 100 k push calls; minutes of stall.
- **Answer:**
  - Delivery is once per gateway (200 sends), then local fan-out. Watched sessions get a 40-byte tick, open sessions the body.
  - Mention counters and push notifications go to Kafka keyed by user_id and drain at the store's and APNs' rate, off the send path, badges allowed to lag.
  - Product rule: `@channel` above 1 k members needs a role. Slack does this.
  - Read storm afterwards: 40 k clients `GET after=` the same partition. Owner's 100-message cache and read coalescing at the API absorb it.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: one channel receives 5 k sends/s (bot flood, incident channel)
- **Trigger:** integration misconfiguration or a live event.
- **Symptom:** that channel's actor saturates; neighbours on the same owner node slow down.
- **Answer:**
  - Per-channel limit 1 k/s and per-sender 100/s enforced at the API tier, 429 with retry-after. That protects the actor and the LWT partition.
  - A legitimately hot channel (live event chat) needs the relay split: the actor keeps assigning seqs and writing, and hands delivery to N relay workers that each cover a slice of the gateways. Not built on day one; the seam is that "assign + write" and "deliver" are already separate steps in the actor.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: Monday 9 am, a 500 k user workspace boots
- **Trigger:** 830 logins/s for 10 minutes from one tenant.
- **Symptom:** naive design: 50 MB boot payload each, 41 GB/s; Slack's January 2021 outage was this shape.
- **Answer:**
  - Boot is lazy: the workspace directory is served from a per-workspace edge cache (Flannel) on demand, and the client sends `last_boot_version` to get only deltas.
  - `/sync` returns heads and unreads only (two point reads per channel), no bodies. Bodies load per opened channel.
  - Gateway admission at 500/s/node spreads sockets; reconnect jitter spreads clients.
  - Cost per login is O(channels the user is in), never O(workspace size).
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: a gateway falls behind (GC pause, slow NIC)
- **Trigger:** one gateway stops draining its inbound stream from owners.
- **Answer:** Each owner keeps a bounded queue per gateway (10 k). On overflow it drops the queue and sends one `resync(C, head)` per affected channel. The gateway's clients pull. The owner and the other 199 gateways never block. This is the rule that makes push safe.
- **Diagram:** `diagrams.md` D5.3.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: presence for a 100 k user workspace
- **Trigger:** status flips at ~1%/min.
- **Symptom:** naive broadcast: 1.7 M updates/s for one tenant.
- **Answer:** Clients subscribe only to users on screen (a few hundred max). Presence changes are batched per subscriber every 5 s. Presence lives in Redis with a 60 s TTL from 30 s heartbeats; nothing touches a database. Under load, presence and typing are shed first; they have their own SLO and pager. Presence is a cost problem, not a consistency problem.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: 10x traffic tomorrow
- **Trigger:** acquisition, viral growth.
- **Answer:** Gateways and owners scale linearly by adding nodes (ring change moves 1/N of channels, actors reload heads). The store adds nodes and rebalances token ranges. The number that does not scale linearly is fan-out per message in a big channel with more gateways (200 -> 2 000 sends); that is when the relay layer is added. Coordination store load is unchanged (it holds ~1 key per owner node).
- **Confidence:** [ ] shaky [ ] ok [ ] confident

---

## 4. Data

## Edge case: device offline for a week, channel had 50 k messages
- **Trigger:** stale cursor far behind head.
- **Answer:** `GET after=` returns `truncated: true` when `head - cursor > 10 000`. The client discards local history for that channel and loads the newest page as a snapshot. Bounded catch-up regardless of absence. Nobody scrolls 50 k missed messages anyway.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: a channel with 10 years of history
- **Trigger:** long-lived `#general`.
- **Answer:** Partitions are `(channel_id, seq / 10 000)`, ~10 MB each, so the channel is thousands of small partitions, not one. Rows older than 1 year move to Parquet in object storage keyed by `(channel, bucket)`; paging past the hot tier switches to a slower path (p99 seconds). The client computes which bucket a seq lives in, so there is no index lookup and no empty-bucket probing.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: workspace changes retention from forever to 90 days
- **Trigger:** admin policy change.
- **Answer:** Row TTL is set on new writes from the policy; existing rows get a background job that sets TTL per partition (oldest buckets first) and deletes cold-tier files. Search index and Kafka topics honour the same policy via a delete event per `(channel, bucket)`. Seqs stay gapless: expired rows simply do not exist below some seq, and `truncated` covers a client whose cursor is below the retention floor.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: GDPR erase a user
- **Trigger:** legal request.
- **Answer:** Job over the user's memberships -> each channel -> rows where `sender_id = user` become tombstones with body cleared (seq kept, so other clients' gap rules still work). Search index deletes by sender. Cold-tier Parquet files for affected buckets are rewritten. Attachments are deleted in the blob store. Cursor and mention rows deleted. Takes hours for a heavy user; tracked as a job with a completion record for the audit.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: bucket size needs to change
- **Trigger:** 10 000 seqs at 1 KB is fine, but a channel with 40 KB messages makes 400 MB buckets.
- **Answer:** The bucket divisor is stored per channel in the channel row (default 10 000). Changing it applies from a recorded `seq` forward: `bucket = old scheme below split_seq, new scheme above`. No backfill. Clients fetch the scheme with the channel metadata.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: backfilled history has no seq
- **Trigger:** migration from the old workspace-sharded store.
- **Answer:** Assign seqs in `ts` order per channel during backfill, verify count and monotonicity, and set `head_seq` above the max before the workspace flips to the new path. Any tie in `ts` is broken by the old primary key so the assignment is deterministic and re-runnable.
- **Diagram:** `diagrams.md` D12.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

---

## 5. Operations

## Edge case: what pages at 3 am
- **Answer:** A channel with no owner for 30 s; owner->gateway overflow above 0.1% for 5 min; send p99 above 1 s for 5 min; LWT failure rate above 0.1%; socket count dropping 5% in a minute in any region (a storm is starting); DR replication lag above 60 s; coordination store quorum lost. Mention consumer lag and presence Redis are tickets, not pages.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: deploying the gateway fleet without a reconnect storm
- **Answer:** Drain one node at a time: stop admitting, send `reconnect(after: jitter 0..30 s)` to 1% of its sockets per second, exit when empty or after 5 min. Roll 1% -> 10% -> 50% of the fleet per hour while watching socket count and resync rate. The rest of the fleet has 2x socket headroom.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: deploying the owner fleet
- **Answer:** Remove the node from the ring first (its ~1% of channels move and reload heads, ~11 s of send retries for those channels if done abruptly; graceful handoff hands `head_seq` and epoch to the successor directly to make it sub-second), deploy, rejoin. One node at a time.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: changing the client protocol (gap rule, tick format)
- **Answer:** Server supports both versions for two client releases; the session token carries the client version; a server-side kill switch can force old clients to a fallback mode (poll `/sync` every 30 s) if a release misbehaves. Slack's worst outages were client-amplified; the kill switch is the mitigation.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: migrating from workspace-sharded MySQL with zero downtime
- **Answer:** Five flag-controlled phases: shadow owner ring writing the new store; dual read on 1% of channels with diffs; per-channel backfill with count verification; per-workspace cutover with 14 days of dual-write back to the old store; retire. Rollback at each phase is a flag flip; after cutover the dual-write keeps the old store current for rollback.
- **Diagram:** `diagrams.md` D12.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

---

## 6. Security and abuse

## Edge case: a user opens 1 000 websockets
- **Answer:** Cap 10 sessions per user enforced at connect via a per-user counter in Redis (TTL-refreshed by heartbeats so a crashed gateway's sessions expire). Beyond the cap: reject with a code the client understands. Sends are rate-limited per user regardless of session count.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: a client subscribes to a channel it is not a member of
- **Answer:** The gateway forwards `subscribe(session, C)` with the user id from the token; the owner checks membership (cached 60 s, invalidated on leave) before adding the gateway's session to its delivery set. History reads do the same check at the API. Membership is the only authz relation, so there is one place to get it right.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: workspace A's user tries to read workspace B's channel
- **Answer:** Same membership check; a user is never a member of a channel outside their workspace except through a shared channel, whose membership relation is explicit and admin-approved on both sides. The channel row records both workspace ids; the owner enforces that a sender is in one of them and in the channel.
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: a spammer floods a channel or the API
- **Answer:** 100 sends/s per sender, 1 k/s per channel at the API tier (token bucket in Redis, 429 with retry-after). Body cap 40 KB. Explicit mention list cap 100. `@channel` needs a role above 1 k members. Attachment uploads are signed URLs bounded by workspace quota. A bot token has its own tighter limit (Slack: ~1 message/s per channel per app).
- **Confidence:** [ ] shaky [ ] ok [ ] confident

## Edge case: shared channel across two workspaces in two regions
- **Trigger:** Slack Connect between an EU-homed and a US-homed workspace.
- **Answer:** The channel has exactly one owner and one partition, in the region of the creating workspace. The other workspace's members subscribe cross-region (+80 ms). Order is decided by that one owner; nothing is merged. Residency for the non-home workspace is waived explicitly at creation (admin approval). Retention: the stricter of the two policies applies, evaluated at write time and stored on the row.
- **Confidence:** [ ] shaky [ ] ok [ ] confident
