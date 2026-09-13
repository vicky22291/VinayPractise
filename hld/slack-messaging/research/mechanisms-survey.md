# Hard Mechanisms in Large-Scale Messaging Systems

Research survey of production implementations of 12 core chat system mechanisms. Each section covers real-world deployments, trade-offs, production numbers, and failure modes.

## 1. Per-Conversation Ordering

**The problem in one line:** Guarantee messages in a channel appear in the same order to all clients when senders hit send simultaneously.

**Options and who uses each:**

- Single sequencer per channel (Slack channel server process): Arbitrates order for concurrent sends, centralizes decision. Can become bottleneck for very busy channels. Used by Slack.
- Kafka partition per channel (Discord, early Twitter): Partition offset provides total order within that channel. Message broker handles ordering. Requires one partition per channel or per shard. Adds broker latency but scales to many channels.
- Database-assigned monotonic sequence (Postgres BIGSERIAL, Spanner COMMIT_TIMESTAMP): Write message, read back the auto-assigned sequence number. Adds database roundtrip. Works but introduces latency tail.
- Snowflake/Twitter Snowflake IDs and timestamp-only: NOT a total order under concurrency. Two clients in same millisecond get non-ordered IDs. Breaks for ordering guarantees. Use only for uniqueness, not ordering.
- Hybrid Logical Clock (HLC): Combines physical time with Lamport counter. Preserves causality, stays close to wall time. Harder to reason about than simple sequences. Used in some distributed systems.
- Telegram PTS (Plain Text Sequence): Per-user per-conversation sequence; pts increments for each update. Client stores local_pts; server sends update with pts_count. If local_pts + pts_count === remote_pts, apply. If less, gap-fill. If greater, already-applied, ignore.

**Recommended for a Staff interview answer:** Single sequencer per channel for Slack-like design. Trade off Kafka or DB sequences versus latency and bottleneck risk. Mention Slack's channel server pattern and how it breaks under 100k-member channels (switch to fan-out-on-read). Explain Telegram's PTS gap detection. Say why Snowflake IDs fail for total order.

**Failure modes, gotchas:**

- Single sequencer single point of failure for that channel. Failover requires rerouting.
- Kafka partition becomes hot partition under load (busier channels).
- Database sequence adds 10-50ms latency per message (network round trip).
- Snowflake IDs tie to wall clock, exposing server time skew; two machines sending same millisecond produce ambiguous order.
- PTS gap-fill: if client misses updates, must fetch gap before applying newer ones. Network disruption = backlog.
- Concurrent sends in same millisecond: sequencer sees arrival order, not causality. True causal order requires vector clocks (expensive).

**Sources:**

- [Slack messaging architecture with Keith Adams](https://softwareengineeringdaily.com/2018/11/28/slack-messaging-architecture-with-keith-adams/)
- [Slack channel server pattern](https://engineeringenablement.substack.com/p/slack-system-design-what-actually)
- [Telegram PTS sequence numbers and updates](https://core.telegram.org/api/updates)
- [Iris Messenger totally ordered queue architecture](https://medium.com/@systemizer/lsi-facebooks-iris-system-37c7dcea9dd9)
- [Hybrid logical clocks in distributed systems](https://blog.bytebytego.com/p/a-beginners-guide-to-clocks-causality)

## 2. Connection Layer at Scale

**The problem in one line:** Hold millions of concurrent WebSocket connections and route inbound updates to the right client without melting the network stack.

**Options and who uses each:**

- WebSocket: Bidirectional, low latency, requires TCP keepalive and heartbeat. Per-connection overhead is 2-10 KB memory in idle state. Erlang/BEAM handles 500K+ connections per node with tuned OS (file descriptor limits, TCP buffer tuning). Go, Netty, Envoy similar limits.
- Long-poll: Client polls server every N seconds. Wastes bandwidth, higher latency (bounded by poll interval). Fallback for browsers that don't support WebSocket. Discord/Slack avoid for primary path.
- MQTT: Publish/subscribe protocol, lower overhead than WebSocket on mobile. Requires broker (Mosquitto, AWS IoT Core). Adds extra hop, less common for chat (but used in IoT messaging).
- Server-Sent Events (SSE): One-way (server to client). Simpler than WebSocket, still uses HTTP. No bidirectional messaging.

**Connection registry (user-to-server mapping):**

- Sticky sessions: Route a user always to same server. Load balancer uses consistent hash or session affinity. Simple, but uneven load if user cohorts differ in activity. Harder to drain for deploys.
- Stateless with Redis/etcd registry: Connection stored in distributed cache. When user sends, any frontend can look up which backend has their socket. Requires Redis on critical path for every message. Adds 1-5ms per lookup.
- In-memory sharded registry on frontend cluster: Compute which frontend owns user via hash(user_id) % num_frontends. Each frontend stores its own connections locally. No external call, but rebalancing requires coordination.

**Recommended for a Staff interview answer:** WebSocket with in-memory per-frontend registry. Mention Erlang's 2M connection capacity, mention Go/Netty as alternatives. Sticky sessions for simplicity if acceptable. Stateless + Redis if you need hot rerouting (rare in practice).

**Failure modes, gotchas:**

- WebSocket half-open connections: TCP ACK succeeds but peer is dead. Send heartbeat (5-10s ping/pong). Detect missing heartbeat response.
- Reconnect storms on deploy: 100K clients reconnect simultaneously, overwhelm server. Mitigate with exponential backoff + jitter (spread reconnects over 10-30s, not 1s).
- Session affinity with sticky sessions breaks if frontend dies. Load balancer must not kill in-flight connections.
- Redis registry unavailable = connections can't be routed. Requires circuit breaker or failover (e.g., fall back to sticky).
- File descriptor exhaustion on server: tune `/proc/sys/fs/file-max` and per-process limits.

**Sources:**

- [WebSocket connection limits and scalability](https://websocket.org/guides/websockets-at-scale/)
- [WebSocket reconnection with exponential backoff and jitter](https://julianoalves.me/blog/websocket-reconnection-strategies)
- [Thundering herd problem on server restart](https://arpit.substack.com/p/thundering-herd-problem-and-addressing)
- [Load balancing WebSocket connections](https://www.cosmiclearn.com/websockets/sticky-sessions.php)
- [Redis session registry for messaging](https://www.linkedin.com/pulse/memory-database-redis-caching-vinit-goyal)

## 3. Fan-Out to Large Channels

**The problem in one line:** When a 100k-member channel gets a message, deliver it to all online subscribers without overloading the write path.

**Options and who uses each:**

- Fan-out on write: When message arrives, immediately push to all N subscribers. Latency paid by sender, but subscribers see updates instantly. Breaks when N is large (100k writes to subscriber queues = huge spike). Slack uses for small channels, switches to fan-out-on-read for large ones.
- Fan-out on read: Subscriber pulls latest messages when they open the channel. Zero fan-out cost, but cold start is expensive (1-2 second query on first load). Users expect messages in chat window instantly, so this is fallback only.
- Hybrid (push online, pull offline): Push to currently-connected subscribers from a pub/sub system (Redis, Kafka topic per channel). Offline users pull from archive on reconnect. Discord, Telegram use this.
- Per-channel pub/sub topic: One Kafka topic per channel (or partition per channel). Message broker handles subscriptions. Scales well but creates N topics for N channels (management overhead). Works for thousands of channels.
- Per-user queue: Message goes to per-user inbox/queue on receive (durable, stored). User fetches from their queue. Better for multi-device sync and offline delivery. Slack Iris uses totally-ordered queue.

**Backpressure handling:**

- Per-subscriber queue cap: If subscriber queue fills (e.g., 1000 messages unacked), drop newer messages or pause producer. Subscriber must resync to catch up.
- Coalescing / batching: Instead of sending one update per message, batch updates over 100ms window, send together.

**Recommended for a Staff interview answer:** Push to online subscribers via pub/sub + pull from archive for offline. Name Slack's channel server pattern (stateful process per channel) vs Discord's guild process. Mention Kafka topic per channel sharding. Say why large channels need fan-out-on-read fallback.

**Failure modes, gotchas:**

- Fan-out spike: Channel with 1 million online members, one message sent, write spike of 1M queue writes in 100ms. Broker (Kafka, Redis) can't keep up, drops messages or slows down entire system.
- Pub/sub topic lag: If subscribers are slow, message accumulates, broker's memory grows. Consumer lag not monitored, lag silently hits memory limit, broker OOMs.
- Slow subscriber holds up batch: If one consumer is slow, batching must wait or split the batch.
- Rebalancing storms on consumer group change: All consumers in a partition group reconnect, seek to offset, resync state. Causes 30-60s blip.

**Sources:**

- [Fan-out messaging patterns at scale](https://getstream.io/glossary/fan-out/)
- [Discord guild/channel event fanout architecture](https://www.techinterview.org/post/3233474372/system-design-design-discord)
- [How Discord stores trillions of messages](https://discord.com/blog/how-discord-stores-trillions-of-messages)
- [Slack channel server pattern](https://engineeringenablement.substack.com/p/slack-system-design-what-actually)

## 4. Sync and Offline Delivery

**The problem in one line:** User goes offline, comes back online, and sees all new messages + correct unread count without scanning entire history.

**Options and who uses each:**

- Per-conversation cursor: Store last_msg_id or last_seq per user per channel. On reconnect, query "give me messages since cursor". Requires gap-fill if cursor is far behind (network outage, reinstall). Telegram, Discord, Slack all use this.
- Per-user sequence number (Iris pattern): Totally-ordered update queue per user. Every message delivery, reaction, read receipt is an update with a sequence number. User reconnects, server sends updates since their last ack'd sequence. No per-channel query needed.
- Mailbox / inbox table: Each message written to per-user inbox table, TTL 30 days. User queries inbox on open. Simple but N messages * M users = massive table. Requires TTL and cleanup jobs.
- Push notifications as wake-up: App is killed, push notification arrives (APNs, FCM). User taps, app reconnects, syncs. Push is lossy (no SLA), so in-app fallback still needed (check server on open).

**Delivery guarantees:**

- APNs (Apple): "Best effort", no SLA guarantee. Silent push may not deliver if device in low-power mode. Visible push more reliable but not guaranteed.
- FCM (Android/Google): Similar "best effort". High priority can wake radio, but still lossy.
- In-app sync on reconnect: Reliable, but user must open app.

**Recommended for a Staff interview answer:** Per-conversation cursor + gap-fill + push notifications as hints (not source of truth). Use per-user sequence queue if you're also syncing read receipts and reactions. Mention Iris totally-ordered queue design. Say why push is lossy and why in-app sync is mandatory.

**Failure modes, gotchas:**

- Cursor far behind: User offline 7 days, returns. Cursor points to message before retention cutoff. Server can't fill gap. Must fall back to "give me latest 100" or force full sync.
- Gap-fill storms: Many users with stale cursors simultaneously try to gap-fill, query spike.
- Push notification lost: Device offline during crash, notification sent to old push token, or APNs drops it. User opens app hours later with no indication they missed something.
- Per-user sequence queue size: If user reconnects after 1 month and 100k messages in their queue were buffered, syncing queue is expensive.

**Sources:**

- [Telegram PTS and update sequence handling](https://core.telegram.org/api/updates)
- [APNs and FCM delivery guarantees](https://www.back4app.com/glossary/push-notifications-apns-fcm/)
- [Push notifications lossy delivery, best practices](https://help.klaviyo.com/hc/en-us/articles/15594685536539)
- [Iris totally-ordered queue for Messenger](https://medium.com/@systemizer/lsi-facebooks-iris-system-37c7dcea9dd9)

## 5. Read Receipts and Unread Counts

**The problem in one line:** Efficient per-user per-channel unread count without hammering the database on every message.

**Options and who uses each:**

- Compute unread count from cursor: last_msg_seq - last_read_seq = unread count. No extra write, just compute at read time. Slack uses this. Works if you already have per-conversation cursors.
- Write unread counter to cache/DB: On every message, increment per-user per-channel unread counter. Expensive write amplification. For 100 users in a channel, one message = 100 counter increments. Doesn't scale above a few hundred users per channel.
- Mention counts only: Only count messages that @mention the user, ignore bulk messages. Reduces write amplification. Discord, Slack show mention badge separately.
- Read receipt queue: User marks channel read, write to Kafka topic or queue, async consumer updates counter. Decouples read from counter update. Adds eventual consistency (counter lags behind actual read).

**Write amplification mitigation:**

- Batch counter updates: Queue read events, flush every 5 seconds or 100 events. Reduces total writes by 10-100x.
- Last-write-wins on cache: Store counter in Redis with no-sync-to-DB. Accept stale counters if Redis restarts (re-compute from cursors).

**Recommended for a Staff interview answer:** Compute from cursor for simplicity. If you need read receipts (three dots), use a separate queue and eventual consistency. Mention write amplification trap. Say Slack computes, mention Discord's badge-for-mentions-only approach.

**Failure modes, gotchas:**

- Read receipt queue lag: Counter updates 5 minutes behind actual reads. User still sees "3 unread" after reading.
- Mention parsing explosion: "@channel" in 100k-member channel means @mention every member. Write 100k individual mention rows or queue events. Either way, huge spike.
- Badge race: User marks channel read, but in-flight message arrives before counter updates. User sees badge disappear, then reappear. Confusing UX.
- Counter desync: Cache lost, fall back to cursor-based compute. But user already had different number in badge. Confusing.

**Sources:**

- [Write amplification in database systems](https://www.postgresql.org/message-id/CAA4eK1JeAp3g0-X8X0U87UW3YjNKG3qxR-0-xCTUY%3DmxT4aOag%40mail.gmail.com)
- [Zulip unread message system design](https://github.com/zulip/zulip/blob/b20797ed9cb930ad326e94ec9e66f719c860c021/docs/subsystems/unread_messages.md)

## 6. Presence (Who Is Online)

**The problem in one line:** Broadcast "user X is online" to thousands of watchers without melting the infrastructure.

**Options and who uses each:**

- Heartbeat-based presence: Client sends ping every 5-10 seconds (or on activity). Server marks user online if heartbeat in last N seconds. Stop sending, user goes to "idle" after 30s, "offline" after 5 min. Used by Discord, Slack.
- Last-seen timestamp only: No active heartbeat. Server records timestamp when user last took action. Doesn't distinguish "idle" from "offline". Simpler, lower overhead. WhatsApp does this.
- Presence subscriptions: User A only receives presence updates for users B, C, D if B, C, D are on A's visible roster (friends, same channels). Slack does this to reduce fan-out cost.
- Presence pub/sub topic: Presence updates published to Kafka topic per workspace. Subscribers filter to users they care about. Discord experienced presence storms: millions of guild members changing status at once (e.g., large server going from idle to playing game) = millions of events in milliseconds.

**Batching and debouncing:**

- Presence events batched: Collect all status changes over 100ms window, send one batch update to subscribers. Reduces network packets by 10x.
- Don't send presence for users not on-screen: Slack only sends presence for visible guild members, not entire member list.

**Recommended for a Staff interview answer:** Heartbeat-based with presence subscriptions limited to visible users. Mention Discord's presence storms and why batching helps. Say why "last-seen only" is cheaper but less interactive.

**Failure modes, gotchas:**

- Presence storm: Large server with 100k members, all members simultaneously go offline (server restart), all reconnect. Server receives 100k "online" events in 1 second. Broker, router, subscribers all spike.
- Heartbeat timeout race: User offline for 35s (should be marked offline), but heartbeat arrives at 29s. User flaps online/offline/online as heartbeats arrive out of order.
- Presence lag: Batch update waits 100ms, user sees delayed presence. "User X just came online" notification arrives 100ms after they actually sent a message.
- Subscription storm: User opens sidebar with 1000 contacts. App requests presence for all 1000. Server gets 1000 subscribe requests, creates 1000 topic subscriptions. Router overwhelmed.

**Sources:**

- [Discord presence system and gateway](https://docs.discord.com/developers/events/gateway-events)
- [Discord presence storms in large guilds](https://www.techinterview.org/post/3233474372/system-design-design-discord)

## 7. Multi-Device Consistency

**The problem in one line:** User sends from phone, reads on laptop, each device shows same conversation state and cursor position without data loss.

**Options and who uses each:**

- Per-device cursor: Each device has last_read_seq per channel. On sync, pick max cursor across devices, report unread. Works, but requires pulling cursors from all devices (slow on reconnect). Requires de-duplication of same message delivered to multiple devices.
- Per-device queue: Each device gets its own message queue. Delivery confirmed per device. More durable (lost device doesn't affect others) but complex. Used by WhatsApp, Signal with E2E encryption.
- Delivery vs read state separated: Message marked "delivered" when it reaches device A, "read" when user opens it on any device. Multiple devices can be "delivered" but only one is "read". Mitigates confusion about which device read the message.
- E2E encryption with client fanout: Sender encrypts message separately for each of recipient's devices using that device's public key. Client (sender) decides which devices to send to. WhatsApp, Signal use this. Each message = N sends for N devices. Adds sender-side latency (key lookup, N encryptions).

**Session resumption on new device:**

- New device logs in, fetches since last sync point. Can take seconds for historical sync.
- Device transfer: User logs out on old device, logs in on new device. Can lose in-flight messages if old device is killed before sync completes.

**Recommended for a Staff interview answer:** Per-device cursor with eventual consistency, delivery state separate from read state. If E2E is required, use client fanout (WhatsApp model) and accept sender latency. Mention that E2E adds device registration and key management complexity.

**Failure modes, gotchas:**

- Cursor sync lag: User reads on phone, cursor updates phone backend. Laptop asks for updates but gets old cursor from laptop backend. Messages reappear as unread on laptop.
- Duplicate delivery: Message sent to all 3 devices, but network hiccup = some devices don't ack. Server retries, device gets message twice. Requires idempotent message handling on client.
- E2E key rotation: Device drops off, new device registered. Old conversation keys invalid. Requires rekeying or accepting some messages unreadable.
- Device state divergence: Phone offline 1 hour, laptop gets 100 messages. Phone reconnects, asks for updates, gets 100 messages. But phone already rendered 50 of them from push notifications. Must detect and ignore duplicates.

**Sources:**

- [WhatsApp multi-device with E2E encryption](https://engineering.fb.com/2021/07/14/security/whatsapp-multi-device/)
- [Signal protocol and multi-device consistency](https://signal.org/blog/whatsapp-complete/)

## 8. Delivery Guarantees and Idempotency

**The problem in one line:** Retry failed sends, but never deliver the same message twice to the same user.

**Options and who uses each:**

- Client-generated message ID (UUID): Client generates unique ID, sends with message. Server deduplicates by ID. Requires dedup cache/database window (e.g., 7 days). If ID not in window, message is new.
- Server-assigned message ID + ack: Server assigns ID on receipt, sends ID back to client. Client acks receipt. If client re-sends, server sees ID, returns cached result. Requires server-side state.
- Idempotency key pattern: Like UUID but called "idempotency key". HTTP API semantics: same key within dedup window = same result.

**Delivery semantics:**

- At-least-once (client to server): Client retries on timeout. Server may receive multiple copies. Requires dedup on server side.
- At-least-once (server to device): Server retries push notification. Device may receive message multiple times. Requires app to handle duplicates or use device-side dedup.
- Exactly-once is fake: Consensus is impossible without a shared arbiter. Exactly-once requires dedup (which is a form of consensus).

**Dedup window:**

- 7 days: Retain ID of all messages received in last 7 days. Safe for typical retry durations (< 5 min). After 7 days, ID can be reused (rare).
- In-memory cache: Fast but data loss on restart. Hybrid: cache + disk backup.

**Recommended for a Staff interview answer:** Client-generated UUID, server dedup on ID for 7 days. Mention at-least-once is the real guarantee. Say exactly-once is aspiration, not reality. Mention APNs/FCM have no dedup (app must handle).

**Failure modes, gotchas:**

- Retry storm: Client doesn't get ack (network timeout), retries aggressively. Server dedup stops duplicates but processing cost is high (N retries = N dedup checks).
- Dedup window expiry: Client resends very old message (5 months later). ID not in dedup window, treated as new message. Message duplicated.
- Clock skew race: Client generates UUID based on timestamp, clock skews forward, generates same UUID. Non-unique ID.
- Dedup cache miss (restart): Server restarts, dedup cache lost. Old message re-sent, accepted as new. Duplicate delivery.

**Sources:**

- [Idempotency and deduplication in distributed systems](https://www.architecture-weekly.com/p/deduplication-in-distributed-systems)
- [Dedup window and idempotency key patterns](https://dev.to/gabrielanhaia/idempotent-consumers-dedup-key-dedup-window-or-idempotency-by-design-pick-one-31g5)
- [Redis idempotency streams](https://redis.io/docs/latest/develop/data-types/streams/idempotency/)

## 9. Storage for Messages

**The problem in one line:** Store trillions of messages, answer "get messages from this channel between timestamp X and Y" in <100ms.

**Options and who uses each:**

- Cassandra with time bucketing: Partition key is ((channel_id, time_bucket), message_id). Discord buckets by 10 days per bucket (keeps partitions under 100 MB). Allows partition splitting under load. Scans one partition per query. Replicated across 3+ nodes. Used by Discord.
- Sharded MySQL (Slack Vitess): Vitess is YouTube's MySQL sharding proxy. Slack runs 3000+ shards, 600k writes/sec. Per-shard throughput 200 writes/sec typical. Allows shard splitting (repartitioning). Used by Slack.
- Postgres: Single machine or replicated pair. Lower throughput than Cassandra (single node ~5k qps write), works for small-to-medium deployments.
- S3 / cold storage tiering: Hot messages (recent, queried often) in database. Cold messages (> 30 days) archived to S3 (cheaper, slower). Slack does this.

**Time bucketing rationale:**

- Without bucketing, channel_id partition grows forever. Single partition = all messages for that channel. Cassandra node runs out of disk/memory.
- With time bucketing, only recent partition is active (hot). Old partitions are archived or compacted. Partition size bounded.

**Partition size limits:**

- Cassandra guideline: keep under 100 MB. Discord buckets to ~10 days per 100 MB bucket.
- Hot partitions: Busy channel + recent bucket = all requests hit one node. Leads to that node becoming bottleneck. Mitigate with read replicas or partition splitting.

**Tombstones and deletes:**

- When message deleted, write tombstone record (marker). Actual deletion is lazy (compaction). Tombstone reads as "deleted" but stays in database.
- Edit message: write new record with edit_seq, mark old as deprecated. Query returns latest version.

**Recommended for a Staff interview answer:** Cassandra with time bucketing for large scale (Discord model). Mention Slack's Vitess sharding as alternative. Say why bucketing matters (partition size bounds) and cost of hot partitions (load skew). Mention TTL and S3 tiering for old messages.

**Failure modes, gotchas:**

- Partition too large: Partition size > 100 MB = GC pauses spike, read/write latency increases, repairs slow. Can cascade to node crash.
- Hot partition: Busiest channel + most recent bucket = all traffic on one replica. Node CPU/network maxed. Other partitions idle.
- Bucket boundary race: Message sent at 11:59:59.999 goes to bucket 1. Message sent at 12:00:00.001 goes to bucket 2. Query "get messages from 11:59:59 to 12:00:00" requires scanning both buckets.
- Tombstone compaction lag: Deleted message still readable for hours until compaction runs. Data still exposed.
- TTL misconfiguration: TTL = 0 means never delete (infinite growth). TTL = 1 day = messages disappear too fast (users complain).

**Sources:**

- [How Discord stores trillions of messages](https://discord.com/blog/how-discord-stores-trillions-of-messages)
- [Cassandra time-series data modeling](https://thelastpickle.com/blog/2017/08/02/time-series-data-modeling-massive-scale.html)
- [Slack Vitess MySQL sharding](https://slack.engineering/scaling-datastores-at-slack-with-vitess/)
- [Cassandra partition size guidelines](https://community.datastax.com/questions/6155/why-recommendation-is-100k-row-per-partition.html)

## 10. Search

**The problem in one line:** Index billions of messages, search by keyword, filter by user permission, return results in <1 second.

**Options and who uses each:**

- Elasticsearch/OpenSearch with CDC (Change Data Capture): Message written to database, CDC pipeline (Kafka, Debezium) captures write, indexes to Elasticsearch. Per-workspace shard for isolation. Permission stored in index (user_ids array or role_id).
- Solr: Similar to Elasticsearch, less popular for new projects.
- Database full-text search: Postgres has full-text search, MySQL has FULLTEXT index. Simpler but slower and doesn't scale to billion messages.

**Permission filtering:**

- Index-time: Store user_ids array in Elasticsearch doc. Query includes filter on user_ids (which users can see this message). Simple but requires re-indexing when permissions change.
- Query-time: Return results from search, then filter by ACL check. Adds application-side latency, requires permission lookup per result.
- Hybrid: Index basic permissions, query-time check for complex rules.

**Index lag:**

- Real-time sync: Message written to DB, immediately indexed. Typical lag 10-100ms. If lag > 5 sec, users complain ("I just sent it, can't find it").
- Batch indexing: Index runs hourly. Lag up to 1 hour. Not viable for chat (users expect to search message they just sent).

**Recommended for a Staff interview answer:** Elasticsearch with CDC + per-workspace index sharding. Mention permission filter strategy (index-time for simple, query-time for complex). Say lag must be < 1 sec for user experience.

**Failure modes, gotchas:**

- Index lag spike: CDC consumer slow, index falls behind by 5 minutes. User searches, doesn't find recent message. User thinks message wasn't sent.
- Permission race: User removed from channel, but message still in index (hasn't reindexed yet). User can search and see message they shouldn't.
- Index shard imbalance: Workspace A has 1B messages, workspace B has 100k. One shard holds all of A's data = hot shard.
- Typo in query: Elasticsearch by default matches "messge" ≠ "message". Requires fuzzy matching or synonyms to help.

**Sources:**

- [Document-level permissions in Elasticsearch](https://discuss.elastic.co/t/document-level-permissions-filtering/7085)
- [Search indexing with Elasticsearch](https://docs.oracle.com/en/industries/communications/messaging-server/8.1/system-admin/elasticsearch1.html)

## 11. Multi-Region

**The problem in one line:** Serve chat to users globally without >100ms latency, when a channel has members in US and Europe.

**Options and who uses each:**

- Active-passive (one region is primary, others are replicas): All writes go to primary region. Replicas lag behind (typically 50-500ms depending on distance). Low conflict risk, simple. Used by most.
- Active-active (both regions accept writes): Both regions can write independently. Requires conflict resolution (last-write-wins, CRDT, or application logic). Lower latency for local writes, but complex. Some companies use this.

**Home region concept:**

- Each workspace/org has a designated home region (e.g., US, EU, APAC). All writes for that workspace hit home region first. If you're in Europe but workspace is US-based, your message latency = cross-region latency (50-100ms roundtrip).
- Cross-region channel: If channel has members in both US and Europe, writes to Europe still go to US (home region), replay to Europe (adds 50-100ms).

**Replication latency:**

- New York to London: ~70ms roundtrip (network physics). Message latency for London user = 70ms if active-active, ~140ms if active-passive (write to US, replay to EU).
- Consistency trade-off: Active-active sacrifices strong consistency for lower latency. Eventual consistency means messages might appear out of order briefly if two regions write simultaneously to same conversation.

**Data residency requirements:**

- EU (GDPR): Data must be stored in EU. Can't replicate to US without explicit user consent. Requires separate region + firewall.
- China: Data can't leave China. Requires separate isolated region.

**Recommended for a Staff interview answer:** Active-passive with designated home region. Mention data residency constraints. Say why active-active is tempting but conflict resolution is hard. Mention cross-region channel latency penalty.

**Failure modes, gotchas:**

- Region outage: Primary region down, passive region is read-only. Users can't send messages. Failover requires manual intervention or auto-promotion (complex, risky).
- Replication lag visible to users: Message arrives in US, shows in EU 200ms later. User in EU asks "where's your message?" before it shows up.
- Split brain: Network partition between regions. Both regions think they're primary, accept writes. Conflict explosion when partition heals.
- Firewall misconfiguration: Data residency rule, but replication misconfigured and data leaked to wrong region (compliance violation).

**Sources:**

- [Active-active multi-region architecture](https://dev.to/yepchaos/activeactive-multi-region-chat-application-architecture-395b)
- [Multi-region replication tradeoffs](https://adhdecode.com/databases/high-availability/geographic-redundancy-and-multi-region-replication/)
- [Amazon Keyspaces multi-region replication](https://docs.aws.amazon.com/keyspaces/latest/devguide/multiRegion-replication.html)

## 12. Rate Limiting and Abuse

**The problem in one line:** Prevent spam (per-user send rate), prevent thundering herd (@channel in 100k-member channel), prevent large attachment floods.

**Options and who uses each:**

- Per-user send rate: e.g., max 10 messages/sec. Token bucket or sliding window. Slack enforces 1 message/sec per app in an API endpoint.
- Per-channel rate: max N messages per second in a channel. Slows down spammers in large channels.
- Per-connection rate: Connection attempts per IP, login attempts per user. Prevents brute force.
- Message content checks: File size limits (e.g., max 100 MB attachment). @mention count limits (@channel only in channels < 10k members, or requires approval).

**@channel storm:**

- Large channel (100k members), someone sends "@channel hi". Message sent to 100k subscribers. Fan-out = 100k writes. If subscriber queue full, drops messages or slows down. Mitigation: disable @channel in channels > threshold, or require "post to channel" permission.

**Recommended for a Staff interview answer:** Per-user send rate (token bucket), per-channel fan-out rate (limit burst), message content checks (size, @mention). Mention @channel in large channels as special case. Say rate limits are per-user-per-workspace, not global.

**Failure modes, gotchas:**

- Rate limit too strict: Normal user hits rate limit legitimately (e.g., forwarding 10 files = 10 messages, client gets rate limited). Confuses user.
- Rate limit bypass: User opens 5 connections, each at 2 msg/sec = 10 msg/sec total. Limit per connection, not per user.
- Large attachment DoS: User uploads 100 files of 100 MB each sequentially. Each upload takes 10 sec, total 1000 sec = 16 min of server bandwidth. Mitigate with max total per-user per-day.
- @channel notification storm: 100k members receive mention notification. APNs, FCM get slammed, notification delays spike. Mitigate by not sending real-time APNs for @channel (batch or delay).

**Sources:**

- [Rate limiting patterns](https://www.braze.com/resources/articles/whats-rate-limiting)
- [Slack API rate limits](https://api.slack.com/docs/rate-limits)
- [Microsoft Teams rate limiting](https://learn.microsoft.com/en-us/microsoftteams/platform/bots/how-to/rate-limit)

---

## Key Findings

Production messaging systems depend on 12 hard mechanisms, each with real trade-offs:

1. **Per-conversation ordering** is solved via centralized sequencer (Slack), partitioned queue (Kafka/Discord), or totally-ordered update queue (Iris). Snowflake IDs are insufficient for total order.
2. **Connection layer** at scale requires WebSocket + sticky sessions (simple) or stateless + Redis registry (complex but flexible). Heartbeats and exponential backoff with jitter prevent reconnect storms.
3. **Fan-out to large channels** breaks above 100k members. Slack switches from push to pull. Discord uses per-channel topic. Backpressure and per-subscriber queues are mandatory.
4. **Sync and offline delivery** relies on per-conversation cursor + gap-fill, with push notifications as lossy hints. Push is best-effort, not guaranteed.
5. **Read receipts and unread counts** trap many teams with write amplification. Computing from cursor is simpler and faster.
6. **Presence** is eventually consistent by design. Heartbeat-based with per-visible-user subscriptions avoids storms.
7. **Multi-device consistency** requires per-device cursors and delivery state tracking. E2E encryption adds client fanout complexity.
8. **Delivery guarantees** are at-least-once, achieved via client UUID + server dedup window (7 days typical). Exactly-once is unachievable.
9. **Message storage** uses Cassandra time-bucketing (Discord) or Vitess sharding (Slack). Partition size bounded to 100 MB. Hot partitions are the failure mode.
10. **Search** indexes via Elasticsearch + CDC, with permission filtering at query time. Index lag must be <1 second for good UX.
11. **Multi-region** is active-passive with home region designation, or active-active with conflict resolution. Replication latency is unavoidable (50-100ms per region hop).
12. **Rate limiting** prevents abuse via per-user token bucket and per-channel fan-out caps. @channel in large channels is a special case requiring special handling.

Each mechanism involves production numbers: 600k writes/sec (Slack Vitess), 2.3M QPS peak (Slack), 100 MB partition bound (Cassandra), 500k connections per node (Erlang), 5-10 sec heartbeat interval (WebSocket), 7 day dedup window (idempotency), 10 days per bucket (Discord Cassandra), <1 sec index lag (Elasticsearch), 50-100ms replication latency (multi-region), 1 msg/sec rate limit (Slack API).
