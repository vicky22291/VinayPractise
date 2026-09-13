# Design Slack / Large-Scale Messaging Platform: Interview Framing Survey

**One-line summary:** "Design Slack" is asked at Databricks, OpenAI, Meta, Google, Amazon, Stripe, and Rippling as a 45-60 minute system design problem emphasizing real-time delivery at scale, consistency boundaries, and operability over feature completeness; Staff-level answers distinguish themselves through migration strategy, naming cost and org boundaries, and refusing over-engineering.

---

## 1. How Databricks Asks It

Databricks asks "Design a Slack-like messaging system" as one of its primary system design interview questions, positioned as a Staff-level or Senior problem [PracHub](https://prachub.com/interview-questions/design-a-slack-like-messaging-system).

**Interview format:** 45-60 minutes. Databricks interviewers are data platform engineers, so they expect candidates to drive the conversation with diagrams and articulate tradeoffs between consistency, durability, and scale. The prompt is open-ended: "Design a messaging platform" or "Design Slack's core messaging flow". No explicit scope given, so candidates must ask clarifying questions early (channels vs direct messages, offline support, media, search).

**What interviewers push on:** Based on candidate reports, Databricks follows this pressure pattern: (1) start with FRs/NFRs, (2) push on message ordering guarantees when group size exceeds 100k members, (3) probe the fan-out strategy (push vs pull), (4) explore reconnection and duplicate prevention, (5) ask about presence detection and unread counts under concurrent access, (6) corner cases like two messages sent at same millisecond. Reports note they care about naming failure modes explicitly, not hand-waving them [Medium - Kei Zee](https://medium.com/@kei.zee/designing-slack-in-45-minutes-was-the-hardest-system-design-interview-i-ever-faced-6f1d0723d6ac).

---

## 2. How Google, Meta, Amazon, Microsoft, Stripe, Rippling Ask It

**Meta/Facebook:** Asks "Design Messenger" or "Design WhatsApp". Emphasis on fan-out architecture at 2B DAU scale, E2EE implications, and cross-device sync. Meta wants candidates to name where the consistency boundary is (metadata vs encrypted payload) and acknowledge the tradeoff that E2EE breaks server-side search, spam filtering, and message editing [Engineering at Meta](https://engineering.fb.com/2023/12/06/security/building-end-to-end-security-for-messenger/).

**Google/Amazon:** Asks "Design WhatsApp" or a generic messaging platform. Emphasis on multi-region deployment, geo-redundancy, and failover. Amazon probes latency targets, availability targets (99.9 vs 99.99), and the cost of achieving each [SystemDesignHandbook](https://www.systemdesignhandbook.com/guides/meta-system-design-interview/).

**Microsoft:** Similar to Google. "Design Teams" or "Design Slack for enterprise". Emphasis on multi-tenant isolation, compliance (HIPAA, GDPR), and data residency constraints. Follow-ups include scaling WebSocket connections across regions and handling large thread backfill.

**Stripe:** Rarely asks messaging directly; when they do, it is "Design a notification delivery system" (not chat). Emphasis is on exactly-once delivery guarantees and financial transaction reliability, not real-time user experience [Medium - Emily](https://medium.com/@emilyhustlenyc/every-question-i-was-asked-in-stripes-system-design-interview-f6f19c2e62d6).

**Rippling:** Asks "Design a chat application like Slack". Rippling is an HR/payroll platform, so emphasis is on audit logging and compliance rather than scale. [PracHub](https://prachub.com/interview-prep/rippling-software-engineer-interview-prep).

---

## 3. Reference Solutions: FRs, NFRs, and Key Design Choices

**Functional Requirements (consistent across sources):**
- Send and receive messages in real-time (1:1 DMs and group channels).
- Message history / pagination with cursor-based stable ordering.
- User presence (online/offline/away).
- Typing indicators.
- Unread message counts.
- Message editing and deletion (optional, usually dropped).
- File sharing (optional, dropped in 45 min).
- Notifications.

**Non-Functional Requirements (with numbers):**
- Slack: 47M DAU (2025), 1.5B messages/day [Slack Statistics](https://sqmagazine.co.uk/slack-statistics/). Target latency: ~tens of milliseconds for message delivery. Availability: 99.9% monthly uptime.
- WhatsApp: 2B DAU, 100B+ messages/day [WhatsApp Statistics](https://www.skillademia.com/blog/whatsapp-statistics/). Same-cluster delivery: single-digit milliseconds.
- Discord: Trillions of messages stored in Cassandra (177 nodes as of 2022), now ScyllaDB [Hello Interview](https://www.hellointerview.com/learn/system-design/in-the-wild/discord-messages-scylladb).
- Generic target: ~1M messages/sec aggregate, 500k concurrent WebSocket connections per server.

**Key Design Choices (consensus across ByteByteGo, SystemDesignHandbook, Grokking):**
- **Sequencer per channel:** Total ordering via monotonic sequence numbers per channel, not wall-clock time. This is the consistency boundary [SystemDesignHandbook](https://www.systemdesignhandbook.com/guides/slack-system-design-interview/).
- **WebSocket for online clients:** Bidirectional persistent connection for <100ms delivery.
- **Kafka/Redis Streams for fan-out:** One message ingested once, published to a topic per channel. Consumers pull and push to connected clients.
- **Hybrid fan-out:** Fan-out on write for normal groups (<10k members), fan-out on read for large channels (>10k) to avoid hotspot writes.
- **NoSQL for message storage:** Cassandra, DynamoDB, or ScyllaDB. Partitioned by channel_id to keep hot channels localized.
- **Redis for presence and unread counts:** High churn (100ms updates), no durability needed. Invalidated on new message via pub/sub.
- **SQL for metadata:** User profiles, channel definitions, permissions.
- **Idempotent writes:** Unique constraint on (sender_id, client_message_id) to prevent duplicates on retry.
- **Cursor-based pagination:** Query messages after a cursor (sequence number), stable under concurrent inserts.

**Storage Strategy Breakdown:**
- Hot path: Redis (presence, typing, unread cursors). TTL-based, not persisted.
- Warm path: Kafka or queue (in-flight message delivery).
- Cold path: Cassandra/NoSQL (message archive, searchable).
- Metadata: PostgreSQL or MySQL (channels, users, permissions).

---

## 4. The Follow-Up Ladder (Most Likely First)

Ranked by interview frequency and difficulty for staff level:

1. **"How do you handle a channel with 100k active members? Where does push fan-out break?"** Answer should name the write amplification and pivot to hybrid fan-out or push-to-a-small-subscriber-group model. ~30-40M deliveries/sec at worst case.

2. **"Two users send a message to the same channel at the exact same millisecond. Who is first?"** Must explain: sequence numbers in Kafka topic, single consumer group per channel processes sequentially, order is deterministic (Kafka partition order). Don't rely on client timestamps.

3. **"A user has 5 devices. One is offline for a week. How do they see unread counts when they reconnect?"** Answer: persist unread cursor per (user, channel) in a durable store. On reconnect, return messages after that cursor. Use Kafka retention or a message archive.

4. **"How do unread counts stay accurate under concurrent message arrival and reads?"** Answer: unread count is derived from a monotonic cursor (highest_seq_read), not a counter. Increments are implicit. Use optimistic locking or eventual consistency (okay to be stale for 100ms).

5. **"Region goes down. What happens to in-flight messages?"** Answer: messages not yet delivered are in a Kafka topic (persisted, replicated across AZ), clients reconnect to healthy region, pull from cursor. Some messages may be lost if Kafka cluster in that region is fully destroyed (mitigate with multi-region replication, but that is complex).

6. **"How do message edits and deletes work?"** Common answer: append a new message with type=edit or type=delete, containing a reference to original message ID and edit timestamp. Clients render the latest version. Editing across E2EE breaks down (each device decrypts independently).

7. **"A workspace with 500k users boots at 9am Monday (thundering herd). System collapses. How do you fix it?"** Answer: boot doesn't fetch all messages, only presence and latest N messages per channel (e.g., last 50), delivered incrementally with jitter. Prioritize presence over history. Use exponential backoff on client side. CDN for file assets.

8. **"How do you migrate from workspace sharding to channel sharding with zero downtime?"** Answer: this is a Staff-level answer. Dual-write to both old and new shard key for N weeks, then switch reads, then drain old shards. Requires causal consistency or an event log that can be replayed.

9. **"Slack Connect: two orgs' workspaces share a channel. Where is ordering enforced?"** Answer: messages flow through a shared sequencer or bridge service that assigns global sequence numbers. Risk: distributed consensus is hard, usually implemented with a centralized bridge that is a SPOF.

10. **"Design full-text message search. Index every message as it arrives."** Answer: stream messages to an indexing pipeline (Kafka consumer → Elasticsearch), query via API. Tradeoff: search is eventually consistent (lag is 1-10 seconds). E2EE breaks this unless indexing happens client-side.

11. **"Ensure exactly-once message delivery. User never sees a duplicate."** Answer: idempotent write (unique constraint on message ID), idempotent read (skip duplicates via deduplication window in client cache or cursor). Kafka exactly-once requires careful offset management.

12. **"How do you monitor and page on message delivery latency? What is your SLO?"** Answer: track p50, p99 latency (target: p99 < 500ms). Alert on p99 > 1 sec. Measure end-to-end (client send → client receive). Breakdown by region, channel size, message type.

13. **"What if Kafka partition for a channel is lagging and you have 100k backlog? How do you catch up?"** Answer: increase consumer parallelism (more workers), batch writes to push service, deprioritize old backlog and catch new messages first (prioritize recency).

14. **"Can you design this as a single-region system? What breaks first?"** Answer: for 1M messages/sec, disk I/O is the bottleneck before CPU. Latency is OK (same-DC delivery ~5ms). Availability is the fail point (single DC down = total loss). Cost per message is lowest here.

15. **"How does cost scale? What is the $/message and how do you optimize?"** Answer: dominated by storage (Cassandra or S3) and outbound bandwidth. At 1.5B messages/day, storage alone (assume 1KB/message, 7-year retention) is ~100TB, ~$100k/year. Optimize by compressing, archiving old data, or tiering to cheaper storage.

---

## 5. Numbers to Quote Unprompted

Always cite these when discussing scale, messaging frequency, or availability targets:

**Slack:** 47M DAU (2025 estimate) [Slack Statistics](https://analyzify.com/statsup/slack). 1.5B messages sent per day. Users spend 90+ minutes/day active. [Slack News](https://slack.com/blog/news/slack-has-10-million-daily-active-users). Each message ~1-2KB (with metadata). Peak QPS in Slack's data center: ~100k (unverified, from architecture blogs).

**WhatsApp:** 2B DAU, 2.95B monthly active users [WhatsApp Statistics](https://www.skillademia.com/blog/whatsapp-statistics/). 100-150B messages per day (69-104M messages/minute). 7B voice/video calls/day. Similar per-message size (~0.5-1KB text, varies with media).

**Discord:** Trillions of cumulative messages stored. Cassandra cluster: 177 nodes (2022), now ScyllaDB. Typical day: ~100M+ new messages. [Discord - ScyllaDB](https://www.hellointerview.com/learn/system-design/in-the-wild/discord-messages-scylladb).

**Latency Targets:** WhatsApp and Slack target same-cluster delivery in single-digit milliseconds (3-10ms). P99 delivery latency target across regions: typically 100-500ms. P99 > 1 sec is a critical page. Microsoft Teams in APAC: observed p99 3,100ms (perceptible to user). [GetStream](https://getstream.io/blog/mobile-chat-latency-spikes/).

**Fan-Out Ratio:** Typical Slack channel: 50-200 active members. Large channel (e.g., #general in enterprise): 10k-100k members. At 100k+ members, push fan-out costs ~100M write operations/day for a single message, motivating pull or hybrid approach.

**Availability:** Slack targets 99.9% monthly uptime. This permits ~21 minutes of downtime/month. Typical industry SLO for messaging: 99.9% to 99.95%.

---

## 6. What Separates Senior from Staff on This Problem

**Senior Engineer (Good Answer):**
- Asks clarifying questions, scopes to channels + DMs.
- Designs a coherent system: API → Chat Service → Message Store → Fan-Out → Presence.
- Identifies ordering via sequence numbers as critical.
- Chooses a storage backend (Cassandra or DynamoDB) and justifies it.
- Discusses fan-out strategy for groups.
- Talks through one failure scenario (region down, offline clients).
- Grading: passes if the design is internally consistent and would run in one AZ.

**Staff Engineer (Great Answer) Adds:**
- **Refuses premature optimization.** Says "start single-region, single Kafka, single storage node. 47M DAU doesn't require a 10-region ring buffer." Names the actual constraint that forces distribution (single node max 100k QPS and 10TB storage, both hit before load forces sharding).
- **Names the consistency boundary explicitly.** "Ordering is strict per channel. Presence and unread counts are eventually consistent. We accept 100ms staleness there." Doesn't conflate them.
- **Migration story.** "If we outgrow one AZ, we migrate via dual-write and cutover. Here's the 8-week plan and rollback procedure." Acknowledges the operational complexity.
- **Cost and team boundaries.** "This costs ~$500k/year in compute + storage. Presence is a separate service team because it has different SLO (99.95 vs 99.9)."
- **Operability over feature completeness.** Drops message editing, threads, file search to reduce surface area. "We deliver the 80% case and iterate."
- **Naming failure modes.** Specifically says: "Kafka partition for a channel becomes a hotspot and lags. Mitigation: reshuffles by channel/shard_id instead of channel/id. Cost: reprocessing 100M messages." Doesn't hand-wave it.
- **Distinguishes asks vs. musts.** "The interviewer asks about E2EE, search, and replication. E2EE blocks search and makes edits hard. Search makes E2EE impossible. Replication across regions triples infrastructure. We do none of these in year one."
- **Grading:** passes if they show judgment about what not to build, talk to an org (not just a system), and have a concrete rollback plan.

**Signal to listen for:**
- Senior: "We use Redis for presence because it's fast."
- Staff: "We use Redis for presence because it changes every 100ms and needs no history. If Redis fails, we rebuild from login events in the event log. Cost trade-off: 10x cheaper than durable store, acceptable staleness."

---

## Sources

- [Databricks System Design Questions](https://prachub.com/companies/databricks/categories/system-design)
- [PracHub: Design Slack-like Messaging](https://prachub.com/interview-questions/design-a-slack-like-messaging-system)
- [Medium - Kei Zee: 45-Minute Slack Interview](https://medium.com/@kei.zee/designing-slack-in-45-minutes-was-the-hardest-system-design-interview-i-ever-faced-6f1d0723d6ac)
- [SystemDesignHandbook: Slack System Design](https://www.systemdesignhandbook.com/guides/slack-system-design-interview/)
- [DesignGurus: Real-Time Chat Design](https://www.designgurus.io/blog/design-chat-application)
- [Hello Interview: Discord & ScyllaDB Case Study](https://www.hellointerview.com/learn/system-design/in-the-wild/discord-messages-scylladb)
- [Slack Statistics 2025](https://sqmagazine.co.uk/slack-statistics/)
- [WhatsApp Statistics 2026](https://www.skillademia.com/blog/whatsapp-statistics/)
- [Engineering at Meta: E2EE Messenger](https://engineering.fb.com/2023/12/06/security/building-end-to-end-security-for-messenger/)
- [Slack Migration to Cellular Architecture](https://slack.engineering/slacks-migration-to-a-cellular-architecture/)
- [GetStream: Mobile Chat Latency Analysis](https://getstream.io/blog/mobile-chat-latency-spikes/)
- [ByteByteGo: Designing Chat Applications](https://blog.bytebytego.com/p/ep-42-designing-a-chat-application)
- [Grokking: Chat System Design](https://grokkingthesystemdesign.com/guides/chat-system-design/)
- [Exponent: Slack System Design Questions](https://www.tryexponent.com/questions/918/system-design-slack)
- [Hello Interview: Staff-Level System Design](https://www.hellointerview.com/blog/staff-level-system-design)
- [PracHub: Senior vs Staff System Design Rubric](https://prachub.com/resources/system-design-interview-rubric-by-level-mid-level-vs-senior-vs-staff)
- [Rippling Interview Prep](https://prachub.com/interview-prep/rippling-software-engineer-interview-prep)
- [Slack GitHub Gist: Design Slack](https://gist.github.com/nito-Q/b8bbd188059b5a17bac786f5aa3e771a)

---

**Unverified claims flagged:**
- "Peak QPS in Slack's data center ~100k" is from architecture blogs, not Slack official docs.
- "Discord 177 nodes 2022" is from published engineering blog but exact current size unknown.
- "Typical p99 delivery <500ms" is industry consensus, not a spec.
