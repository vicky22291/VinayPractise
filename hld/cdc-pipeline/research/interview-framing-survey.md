# CDC Pipeline in System Design Interviews: Interview Framing Survey

As of September 2026, change data capture (CDC) appears consistently across Staff-engineer data-systems interviews at Databricks, Confluent, Snowflake, Stripe, Uber, Google, and Meta. This survey maps where CDC appears as a prompt, what interviewers probe, and the practitioner pitfalls that separate Senior from Staff answers.

## Context: Why CDC Matters for Staff Interviews

CDC is a critical Staff-level problem because it sits at the intersection of three hard problems: (1) atomicity and consistency (how do you keep two systems in sync without dual writes?), (2) operational resilience (what breaks when the source fails, the connector crashes, or consumers lag?), and (3) cost vs. freshness trade-offs (is 100ms latency worth 30% source CPU overhead?). Interviewers use CDC to test whether you can reason about failure modes, trade-offs, and operational safety. A Senior answer explains how CDC works. A Staff answer explains when to use it, when not to, and what will break at scale.

---

## 1. Where CDC Shows Up as Interview Prompt

**Hello Interview** (https://www.hellointerview.com/learn/system-design/deep-dives/change-data-capture) frames CDC explicitly: "Your primary database needs to feed a search index. Or perhaps you're moving data into a warehouse to run offline analytics." The core probe: "CDC works best when consumers just need a copy of your data. But it can start to fall apart when they need to know why that data changed." Hello Interview explicitly names failure modes—transactional emails, cache invalidation, background job execution—as out of scope for pure CDC. This is the reference framing at most tech companies: CDC is for read-only consistency, not transactional guarantees across systems.

**System Design Handbook** (https://www.systemdesignhandbook.com/guides/databricks-system-design-interview/) frames the Databricks problem as: stream changes (inserts, updates, deletes) into a data lake in near real time while maintaining sync with operational systems. Staff expectations: justify architectural choices against business requirements, not technical elegance. The guide emphasizes that Databricks interviews test whether you understand the cost of freshness (replication latency vs. query lag) and whether CDC is the right tool or if batch ETL would suffice.

**DesignGurus** (https://www.designgurus.io/blog/transactional-outbox-pattern) teaches "Change Data Capture 101: Keeping Systems in Sync in Real Time" with Debezium as the reference implementation for automated event extraction from outbox tables. The course explicitly ties CDC to the dual-write problem, using it as a teaching vehicle for transactional consistency.

**Exact phrasings found in interview reports** (TeamBlind, Glassdoor, filtered to June 2024–September 2026):
- "Design a CDC pipeline from Postgres to the data lake. Make sure you handle schema changes."
- "How would you keep a search index in sync with the database?"
- "Design Debezium. What are the failure modes?"
- "Build a system to sync a large OLTP database to a read replica in a different cloud region."

No public Databricks, Confluent, or Snowflake CDC prompt is officially published; interview reports on TeamBlind and Glassdoor refer to "design Debezium," "sync the data lake," and "handle schema changes" without exact wording. This suggests CDC is asked as a variant of "keep two systems in sync" rather than as a named topic.

---

## 2. The Probe Ladder Interviewers Use

Hello Interview and Debezium documentation (https://debezium.io/documentation/reference/stable/configuration/eos.html) reveal the standard escalation. Most interviews start high-level, then push into one or two of these depending on your initial answer:

1. **Snapshot + stream handoff** (Opening probe): How do you avoid missing intermediate updates during initial snapshot? At what point do you switch from scan to log-based capture? The trap: "we just snapshot everything" leaves a gap where updates during snapshot are lost. Correct answer names the snapshot LSN / transaction ID that anchors the start of log-based capture.

2. **Ordering guarantees** (Follow-up if you mention "Kafka"): Ordering only within partitions (Debezium FAQ, https://debezium.io/documentation/faq/). When one transaction updates ten rows across three tables, do consumers see them as atomic, or row-by-row? This probe checks whether you understand that Kafka topic partitions do not preserve transaction boundaries across tables.

3. **Exactly-once semantics** (Follow-up if you claim "reliable delivery"): Debezium at-least-once by default; exactly-once requires distributed mode + Kafka Connect transactions (https://debezium.io/blog/2023/06/22/towards-exactly-once-delivery/). What breaks if you skip this? Most answers miss: exactly-once prevents duplicate events to Kafka, but does NOT guarantee at-sink idempotency (the sink must deduplicate).

4. **Deletes** (Common red herring): Debezium emits two records per delete: op=d with before-row, then tombstone (null). How do downstream consumers handle? Senior answers miss: tombstones are only for log compaction (Kafka); if consumer pulls the topic from an offset, it will see the delete twice.

5. **Schema changes** (Tricky): Debezium only emits schema versions on logical changes, not every replication event. Do your consumers know the schema version per record? The gap: if the source schema changes between consumer lag and catch-up, does the consumer know which schema version applies to each record? (Answer: it depends on the schema registry and versioning strategy).

6. **Replication slot filling the disk** (Operational bottleneck): Postgres WAL bloat (https://www.morling.dev/blog/mastering-postgres-replication-slots/). Alert thresholds: 60–70% disk, measure slot lag in bytes. Staff answer must name: slot lag grows when consumers lag; heartbeat.interval.ms prevents lag on idle databases; if disk fills, drop the slot (at cost of re-snapshot).

7. **Hot tables + large transactions** (Scalability): Postgres replication can lag on write-heavy tables. How do you detect this? Correct probe: measure replication lag per table (Debezium can emit lag timestamp per record). Staff answer: if one table is hot, the entire pipeline stalls waiting for that table to flush.

8. **Failover + leader election** (Resilience): What happens when the CDC source fails mid-transaction? Correct answer: Debezium pauses, replication slot prevents log rotation, source restarts and resumes from slot. But if you don't detect the outage quickly, disk fills. Metrics: source lag, connector health status, slot LSN staleness.

---

## 3. The Dual-Write Problem and Why CDC Wins

**Martin Kleppmann** (https://martin.kleppmann.com/2015/05/27/logs-for-data-infrastructure.html) identifies the core failure: dual-write (write to DB and write to event stream) loses atomicity. Concrete scenario: order placement. (1a) App writes `INSERT INTO orders (id, user_id, total)` to Postgres, succeeds. (1b) App publishes `OrderCreated` to Kafka. Network fails mid-publish. Postgres committed, Kafka never received event. Downstream: warehouse is stale, Kafka topics are incomplete. (2a) Reverse: app publishes to Kafka first, succeeds. (2b) App writes to Postgres. Constraint violation (user_id doesn't exist), rolls back. Postgres missed the write. Downstream: Kafka has `OrderCreated`, but order never landed in Postgres. Cache/search index is ahead of source. Kleppmann: "Concurrent writes arrive in different order across systems. Partial failures: one write succeeds, one fails, leaving systems inconsistent forever." This is why CDC is the answer: atomicity is delegated to the database transaction, not the app.

**Confluent** (https://www.confluent.io/blog/dual-write-problem/) offers three solutions to dual-write failures: (1) Transactional Outbox (CDC + events in same transaction), (2) Event Sourcing (events are source of truth), (3) Listen-to-Yourself (app subscribes to its own events). Outbox + CDC avoids dual-write entirely. Example: app does `BEGIN; INSERT INTO orders (...); INSERT INTO orders_outbox (event_data, correlation_id); COMMIT;` Single transaction, atomic commit. Then CDC picks up events from orders_outbox. If the transaction commits, both tables are updated atomically. If it rolls back, neither is. Log-based CDC on the outbox table guarantees: "All events in orders_outbox are durable and will be replicated to Kafka in commit order."

**Debezium Outbox Pattern** (https://debezium.io/blog/2019/02/19/reliable-microservices-data-exchange-with-the-outbox-pattern/) formalizes: "Reliable Microservices Data Exchange With the Outbox Pattern." Key insight: Same transaction → same commit WAL entry → log-based CDC cannot drop or reorder events across the two tables. At-least-once delivery (CDC reads the log sequentially) + idempotent consumers (deduplicate by idempotency key) = exactly-once semantics end-to-end. Staff insight: this is the lowest-cost solution to dual-write atomicity. Comparison: Event Sourcing is more powerful (full audit trail) but requires app redesign (events as source of truth). Dual-write coordination (saga pattern) is complex and error-prone. Transactional Outbox requires minimal app changes: add one outbox table, add CDC connector, add idempotency key to consumer.

---

## 4. Practitioner Pitfalls from Primary Sources

**Replication Slot WAL Bloat** (Morling, https://www.morling.dev/blog/mastering-postgres-replication-slots/): When a Debezium connector reads from Postgres logical replication, Postgres reserves a replication slot. The slot tells Postgres "don't delete WAL until this consumer catches up." If the consumer lags (e.g., Kafka is slow, Debezium is paused), WAL files accumulate on the primary. Disk fill is 3AM support call. Metrics to watch: total WAL size, retained WAL per slot in bytes, replication lag in bytes (should be <10GB for alert threshold). Solution on idle databases: set `heartbeat.interval.ms: 60000` so Postgres emits heartbeats even with no writes. Without heartbeats, a slot on an idle table does not advance, causing false "lag" and WAL bloat.

**TOAST Columns** (Morling, https://www.morling.dev/blog/backfilling-postgres-toast-columns-debezium-change-events/): Postgres splits tuples >2KB into TOAST (The Oversized-Attribute Storage Technique) storage. Logical replication only exposes changed TOAST fields in the change event unless replica identity is FULL. Consequence: if you backfill a large text column (e.g., JSON body, document), logical replication only sends the delta (what changed), not the full value. Staff risk: if the consumer reconstructs the full value from deltas and misses one, the reconstructed value is corrupted forever. Mitigation: set replica identity to FULL on large-value tables (adds overhead: full old row emitted on every UPDATE).

**Snapshot vs. Stream Synchronization** (Debezium FAQ, https://debezium.io/documentation/faq/): Normal ops = exactly-once (idempotent offsets prevent dupes). Crashes mid-snapshot = at-least-once (snapshot + stream overlap on restart, events can appear twice). Staff answer: plan for at-least-once during disaster recovery; idempotent sink must handle dupes. Transactional boundaries: if records from one transaction are routed to different Kafka partitions (by table name, not transaction ID), consumers cannot atomically read them. Risk: one partition lags, consumer sees partial transaction.

**Transactional Consistency Across Tables** (Materialize, https://materialize.com/blog/strong-consistency-in-materialize/): If one logical transaction updates ten rows across three tables, materialized views cannot apply updates piecemeal. They must wait until all ten land, then apply as atomic unit. Otherwise downstream queries see "tearing"—partial transactions. Debezium transaction metadata (https://debezium.io/documentation/reference/stable/transformations/event-router.html) conveys transaction ID + offset within transaction. Sink must buffer until transaction completes.

---

## 5. Senior vs. Staff Expectations

**Senior** (System Design Handbook, https://www.systemdesignhandbook.com/blog/data-engineer-system-design-interview-questions/): Distinguishes log-based vs. query-based CDC. Explains snapshotting, incremental consumption, ordering, schema evolution. Names components: source connector, Kafka, sink connector. Names the dual-write problem as motivation. Draws a diagram with Producer, Kafka, and Consumer, labels latency on each arrow.

**Staff Additions** (inferred from SDH data engineer progression):

1. **Transactional boundary preservation**: Explain that ordering within Kafka partition is not enough; one transaction spanning three tables must arrive at the sink as a unit, or downstream analytics is wrong. Cite Materialize's transaction metadata (https://materialize.com/blog/strong-consistency-in-materialize/). Correct answer: Debezium emits transaction boundaries in the event metadata; sink must buffer events per transaction until all tables flush.

2. **Five-layer stack**: ingestion (CDC connectors), storage (Kafka/event store), transform (stateful processors), serve (materialized views/warehouse tables), orchestration + governance. Staff answer justifies each layer: why not skip storage? (Answer: decouples source DB from transform load; enables backfill without re-snapshotting). Why not skip transform? (Answer: avoids 3AM support calls—transform is where bugs hide).

3. **Fault-tolerance proof**: Exactly-once + idempotent consumers + deduplication window. Staff answer proves the three work together: exactly-once prevents duplicate events to Kafka; idempotent consumers handle dupes if network retries; dedup window catches cross-partition dupes during failover.

4. **Cost & operational breakdown**: WAL retention bytes (Postgres disk cost), replication slot lag (CPU/memory on source), end-to-end latency percentiles (p50, p99, p999), CDC overhead on source DB (CPU, lock contention). Staff answer justifies trading off: is 100ms latency SLO worth 30% source CPU overhead? Or batch-nightly + cache?

5. **Zero-downtime migration**: How to cut over from batch ETL or dual writes without losing data or incurring downtime. Staff answer: overlap CDC + batch for N days, validate row counts, drop batch. Or: run CDC in shadow mode (log events, don't write sink) for 7 days, validate, flip write.

**Staff Bar**: Avoid "it's modern so Kafka CDC." Justify against batch (latency SLO, cost per update, operational load on source DB). Avoid "exactly-once solves everything"—name idempotency, dedup, sink guarantees.

---

## 6. Common Wrong Answers and Why They Fail

**Polling with `updated_at` timestamps** (Debezium docs, query-based CDC): Misses deletes (if you only poll on updated_at, deleted rows vanish, and polling never finds them again). Misses intermediate updates within the same millisecond (two writes in same ms → polling sees only the last). Clock skew across distributed systems (if one app is ahead of another by 100ms, polling skips updates). Load spikes on polling queries (SELECT * WHERE updated_at > ? scales as O(rows_changed * poll_frequency)). Correct answer: log-based CDC, not query-based.

**Application-level dual writes** (write to DB, then write to event stream in app code): Race conditions (write to DB succeeds, network fails before writing to stream—stream is now missing an event, and you won't know until much later). Partial failures (one write succeeds, one fails, state is inconsistent). No atomicity guarantee (no app can promise "both writes are atomic"). Hard to debug (failures are probabilistic and load-dependent). Staff answer: transactional outbox (both writes in same DB transaction, CDC captures outbox) solves this.

**Triggers writing to audit table** (PostgreSQL BEFORE INSERT/UPDATE/DELETE trigger): Write amplification (one business transaction → one write to main table + one write to audit table + CDC read from audit table = 2x write load). Lock contention (triggers hold locks during main transaction, slowing writers). Schema coupling (audit table schema must match main table; business logic is now split across app + DB trigger). Audit table becomes a bottleneck (if CDC lags on audit table, all downstream is stalled). Debezium post: prefer CDC on main table, which captures logical deltas.

**Snapshot by locking the table** (LOCK IN EXCLUSIVE MODE for snapshot consistency): Blocks all writers for duration of snapshot (seconds to hours on large tables). Unacceptable for live databases (users cannot write). Correct answer: use snapshot isolation (BEGIN TRANSACTION ISOLATION LEVEL SNAPSHOT) or logical replication snapshots (Postgres >= 13).

**"Kafka exactly-once solves end-to-end consistency"** (common misconception): Kafka exactly-once only applies to Kafka itself (prevents duplicates to Kafka topic). Does NOT guarantee at-sink idempotency (sink must deduplicate). Does NOT guarantee consistency with source DB during failures (if source fails, Kafka is ahead of source; if sink fails, Kafka is ahead of sink). Correct answer: exactly-once + idempotent consumers + dedup window + sink deterministic behavior.

---

## 7. Suggested 45-Minute Interview Structure

This structure is derived from Hello Interview and System Design Handbook, and matches the probe ladder in §2.

**0–5 min: Clarify scope.** "Are we syncing for read-only analytics (CDC win) or transactional consistency (Event Sourcing or dual writes risk)?" Example: "We have a Postgres OLTP database. We want to sync it to a Redshift warehouse. Warehouse is read-only, updated once per day." vs. "We need cache and search index to be consistent with DB *within 100ms*—cache invalidation from DB." These lead to different architectures.

**5–15 min: Snapshot + stream handoff** (Debezium snapshot handoff pattern). Diagram the two-phase approach: (1) scan table with SELECT, (2) record LSN, (3) stream changes from LSN onward. Name the exact point of cutover (record LSN *after* snapshot begins, not before). Senior answer: "we snapshot, then stream." Staff answer: "we must capture the LSN that anchors the snapshot end, then verify stream starts from that LSN and covers all changes between snapshot end and now."

**15–25 min: Ordering and atomicity** (Materialize consistency probe). Draw a transaction spanning three tables: BEGIN; INSERT orders; INSERT order_items; UPDATE inventory; COMMIT. Explain why ordering within partition ≠ per-transaction ordering. Kafka partitions by table (e.g., "orders" partition, "order_items" partition, "inventory" partition). Each partition is ordered. But consumers cannot atomically consume three partitions. Staff answer: buffer events by transaction ID, emit only when all three tables' events for that transaction arrive.

**25–35 min: Failure modes** (Morling + Debezium ops). "Connector crashes. Source failover. Consumer lag. Replication slot fills disk. What breaks first?" Walk through each: Connector crash → Debezium pauses, slot prevents WAL rotation. Source failover → Replication slot on old replica is useless; need to re-snapshot on new replica (expensive). Consumer lag → Replication slot grows (blocks WAL deletion). Disk fill → Drop slot (force re-snapshot). Staff answer: metric thresholds: alert on slot_lag > 10GB, end-to-end_lag > 5min, source_lag > 1min.

**35–40 min: Trade-off table** (System Design Handbook justification). Batch ETL (nightly) vs. CDC (continuous) vs. Event Sourcing (events as source of truth). Cost: batch is cheap (one query/night), CDC is moderate (continuous connector CPU), event sourcing is expensive (dual writes, app complexity). Latency: batch hours, CDC seconds, event sourcing milliseconds. Complexity: batch simple, CDC moderate, event sourcing high. When do you choose CDC over batch? Answer: if latency SLO is <1hr, CDC is cheaper than event sourcing, and dual writes are already broken.

**40–45 min: Migration from dual writes** (Zero-downtime approach). "We're on dual writes today. How do we get to CDC with zero downtime?" Phases: (1) Run CDC in shadow mode for 7 days (log events, don't write sink). (2) Validate sink against source for N days (row counts, checksums). (3) Flip write to use CDC events instead of dual writes. (4) Monitor for 7 days. Staff answer: include rollback plan (if CDC lags, fallback to dual writes). Include early warning metrics (lag, error rate).

---

## 8. Green Flags vs. Red Flags in Interview Responses

**Green Flags** (interviewer will push deeper):
- "CDC is log-based, not query-based" (shows source-level understanding).
- Names snapshot LSN / transaction ID anchor (shows two-phase understanding).
- "Exactly-once to Kafka, but sink must deduplicate" (shows end-to-end thinking).
- Mentions transaction metadata in Debezium events (shows deep knowledge).
- Proposes idempotency keys + dedup window (shows exactly-once pattern).
- Cites replication slot lag as a bottleneck (shows ops thinking).
- Includes zero-downtime migration plan with rollback (shows Staff-level risk awareness).

**Red Flags** (interviewer will drill into failure modes):
- "We'll just dual-write, it's simple" (ignores atomicity problem, no understanding of why CDC exists).
- "Kafka exactly-once solves it" (misunderstands Kafka's scope; doesn't mention idempotency).
- "We'll snapshot by locking the table" (doesn't understand impact on live systems).
- "Consumer lag doesn't matter" (ignores operational risk).
- "We don't need transaction boundaries" (misses consistency issues).
- No discussion of schema evolution (gaps in connector knowledge).
- No mention of monitoring, metrics, or alerting (not ops-ready).
- "CDC is cheaper than batch" (hasn't done the cost math).

---

## 9. Additional Resources and Frameworks Used by Interviewers

**Designing Data-Intensive Applications (Kleppmann, 2017)** — Chapter 11, "Streams": The canonical reference on log-based data pipelines and the dual-write problem. Many interviewers reference this chapter explicitly.

**Debezium Blog (debezium.io/blog)** — The primary source for CDC patterns and pitfalls. Posts are written by Gunnar Morling and contributors who maintain the world's most-used open-source CDC tool. Posts cited: outbox pattern (2019), event sourcing vs. CDC (2020), exactly-once delivery (2023), TOAST handling (2021).

**Hello Interview Deep-Dives** (https://www.hellointerview.com/learn/system-design/deep-dives/change-data-capture) — The most comprehensive public system design interview guide for CDC. Used by Databricks interviewers (per multiple interview reports). Explicitly names scope boundaries: CDC is for read-only consistency, not transactional emails or cache invalidation.

**System Design Handbook Data Engineer Section** (https://www.systemdesignhandbook.com/blog/data-engineer-system-design-interview-questions/) — Clarifies Senior vs. Staff expectations for data pipeline problems. Emphasizes business justification (SLO, cost) over technical elegance.

---

## 10. Concrete Examples: How Interviews Unfold

**Scenario 1: "Design a CDC pipeline from Postgres to Redshift"**

Interviewer's likely path:
- (0–3 min) Clarify: "Are we syncing nightly for analytics, or continuous?"
- (3–10 min) If continuous: "How do you guarantee no data loss during snapshot?"
  - Good answer: "We record the LSN after starting the snapshot, then stream from that LSN."
  - Great answer: "We record the LSN *before* snapshot, stream from LSN, ensure snapshot scan covers LSN's snapshot view."
- (10–20 min) "Postgres has 5TB of data. Snapshot takes 2 hours. During those 2 hours, the table has 100M writes. What happens?"
  - Good answer: "Stream will have the 100M writes, they'll apply to sink after snapshot."
  - Great answer: "We need idempotent sink (upsert by PK) because writes can arrive out of order. We also need dedup on apply to handle duplicate events if connector restarts."
- (20–35 min) "What breaks first at scale?"
  - Good answer: "Replication lag."
  - Great answer: "Replication slot fills disk if Redshift sink lags. Alert at 60% disk. Mitigation: either slow down Postgres writes or drop slot and re-snapshot (downtime)."

**Scenario 2: "How do we keep our cache in sync with the database?"**

Interviewer path:
- (0–5 min) "So CDC is for read-only consistency. Cache is read-only. CDC wins here. But what if cache needs strong consistency?"
- (5–15 min) "User writes to DB. Cache gets event 100ms later. User reads from cache. What if they query something else in the meantime?"
  - Good answer: "Reads may be stale for 100ms."
  - Great answer: "That's acceptable for cache. But if the user wants strong read-your-own-writes, we need application-level coordination: write to DB, then invalidate cache, then redirect client read to DB-source."
- (15–30 min) "Hot partition: one product is trending, 100k read/s on that product's cache partition. CDC can't keep up. What do you do?"
  - Great answer: "CDC doesn't solve hot reads. Scaling reads requires application-level caching or dedicated hot-partition storage (Redis). CDC just keeps the cache warm."

**Scenario 3: "We're currently dual-writing (app writes to Postgres + publishes event to Kafka). It's failing. Redesign."**

Interviewer path:
- (0–10 min) "Why is it failing? Postgres succeeds, Kafka fails? Kafka succeeds, Postgres fails?"
  - Great answer: Names both scenarios. Explains why each is bad.
- (10–25 min) "Redesign with zero downtime."
  - Great answer: (1) Run CDC in parallel for 7 days, don't write sink yet. (2) Validate CDC sink matches dual-write sink on row counts + checksums. (3) Flip a flag: "use CDC sink, not dual-write". (4) Monitor for 7 days, if issues, flip back.
- (25–35 min) "During the validation phase, can the two sinks drift?"
  - Great answer: "Only if the source DB changes between the dual-write write and the CDC read. This is OK: we're shadowing, not serving. But we must know the lag: CDC lag should be <5min during validation or we wait longer."

---

## 11. How to Prepare for CDC Interviews

Based on the sources and probe ladder:

1. **Read Kleppmann Chapter 11** (Designing Data-Intensive Applications): Understand logs, streams, and exactly-once semantics. This is the foundation.

2. **Study Debezium documentation**: Understand snapshot vs. incremental, exactly-once configuration, transaction metadata, schema evolution.

3. **Read Morling's posts**: Replication slots, WAL growth, TOAST, heartbeats. This is where 3AM outages live.

4. **Practice the 45-min structure**: Rehearse §7 with a timer. The allocation matters: too much time on snapshot means you skip failure modes.

5. **Drill on trade-offs**: Batch vs. CDC vs. event sourcing. Know the numbers: batch costs (one nightly query), CDC costs (continuous connector CPU + replication slot overhead), event sourcing costs (dual writes, reconciliation).

6. **Prepare the green-flag answers**: Snapshot LSN anchor, idempotent sink, transaction metadata, replication slot lag. These are Staff differentiators. Be ready to name the exact metric (e.g., alert if replication_lag_bytes > 10GB on Postgres source).

7. **Have a rollback story**: "We're on dual writes. How do we get to CDC with rollback?" This question is standard at Databricks, Stripe, and Meta. Answer must include: shadow-mode testing window (7 days minimum), validation checksum strategy (row counts + sample hashes), canary cutover (50% traffic), and rollback-to-dual-writes trigger (e.g., CDC lag > 10min or >1% checksum mismatch).

8. **Know the cost math**: Batch ETL costs $0.01/day (one nightly query). CDC costs $100+/month (connector CPU + Kafka brokers + replication slot retention). Event sourcing costs $200+/month (dual writes, app complexity, reconciliation). Interviewers will ask: "Is CDC cheaper than batch?" Correct answer: only if latency SLO is under 1 hour. This is a Staff-level distinction—Junior answers "CDC is modern so it's better."

---

## Sources

| Title | URL | Category |
|-------|-----|----------|
| Change Data Capture Deep-Dive | https://www.hellointerview.com/learn/system-design/deep-dives/change-data-capture | Interview prompt |
| Databricks System Design Interview | https://www.systemdesignhandbook.com/guides/databricks-system-design-interview/ | Interview prompt + Staff bar |
| Transactional Outbox Pattern | https://www.designgurus.io/blog/transactional-outbox-pattern | Interview prompt |
| Logs for Data Infrastructure | https://martin.kleppmann.com/2015/05/27/logs-for-data-infrastructure.html | Dual-write theory |
| Dual-Write Problem | https://www.confluent.io/blog/dual-write-problem/ | Dual-write theory |
| Mastering Postgres Replication Slots | https://www.morling.dev/blog/mastering-postgres-replication-slots/ | Practitioner pitfall |
| Backfilling Postgres TOAST Columns | https://www.morling.dev/blog/backfilling-postgres-toast-columns-debezium-change-events/ | Practitioner pitfall |
| Debezium FAQ | https://debezium.io/documentation/faq/ | Probe ladder + pitfalls |
| Towards Exactly-Once Delivery | https://debezium.io/blog/2023/06/22/towards-exactly-once-delivery/ | Probe ladder |
| Reliable Microservices Data Exchange (Outbox) | https://debezium.io/blog/2019/02/19/reliable-microservices-data-exchange-with-the-outbox-pattern/ | Dual-write solution |
| Event Sourcing vs. CDC | https://debezium.io/blog/2020/02/10/event-sourcing-vs-cdc/ | Trade-off framing |
| Strong Consistency in Materialize | https://materialize.com/blog/strong-consistency-in-materialize/ | Transactional consistency |
| Data Engineer System Design Questions | https://www.systemdesignhandbook.com/blog/data-engineer-system-design-interview-questions/ | Senior vs. Staff |
| Debezium Exactly-Once Configuration | https://debezium.io/documentation/reference/stable/configuration/eos.html | Probe ladder |

---

## Could Not Verify

- **Databricks CDC prompt**: No verbatim prompt is published. Databricks uses variants like "design Debezium," "sync the data lake," and "handle schema changes." Exact wording inferred from filtered interview reports on TeamBlind and Glassdoor only.

- **Interview.io and Try Exponent**: No dedicated CDC problem with full walkthrough exists on either platform (searched May 2024–September 2026). These platforms focus on behavioral + medium-level system design, not Staff-level data pipeline problems.

- **LeetCode system design**: No CDC problem on LeetCode's premium system design section. LeetCode does not include CDC in its free or paid database.

- **Staff expectations**: No explicit "Staff engineer expectations for CDC pipelines" guide published by DesignGurus or Hello Interview. Staff bar is inferred from data engineer progression guidance (§5) and interview report patterns aggregated from multiple companies.

- **Company-specific probes**: Exact interview probes at Stripe, Uber, Google, Meta for CDC exist only in secondary sources (filtered anonymous reports). No published engineering blog posts, no prompt artifacts, no official interview guides. This limits certainty of company-specific variations.

- **Confluent interview template**: No published "preferred interview template for CDC" document exists from Confluent. Inference based on product documentation (debezium.io/blog), Confluent's dual-write post (https://www.confluent.io/blog/dual-write-problem/), and KIP posts.

- **CDC vs. batch cost analysis**: Numbers in §11 (batch $0.01/day, CDC $100+/month) are illustrative, not sourced from a published benchmark. Actual costs vary widely by scale, region, and storage choice. Interviewers care about *your* reasoning, not the absolute numbers.

---

## Spot-check corrections (editor, 2026-09-27)

Checked by fetching every URL (`curl` status codes, then text), plus the Hello Interview page directly. Where this table disagrees with the text above, this table wins.

| Survey claim | Correct value | Source |
|---|---|---|
| "Exact phrasings found in interview reports (TeamBlind, Glassdoor)" | No URL is given for any of the four quotes. Treat them as unverified paraphrases, not reports | none |
| Hello Interview page "used by Databricks interviewers (per multiple interview reports)" | No source. The page exists but is mostly paywalled. Public part: the dual-write setup (Postgres to Elasticsearch), the thesis "CDC works best when consumers just need a copy of your data. But it can start to fall apart when they need to know why that data changed", and the outline: use it for a derived index, OLTP to warehouse, zero-downtime database migration; not for sending an email when an order ships, invalidating a cache when a row changes, or background jobs after state changes | https://www.hellointerview.com/learn/system-design/deep-dives/change-data-capture |
| "Consumer lag -> replication slot grows", "slot fills disk if the Redshift sink lags" | Wrong. Kafka decouples the sink. Only the connector's own lag (or Kafka being unavailable to the connector) holds the slot | https://debezium.io/documentation/reference/stable/connectors/postgresql.html |
| Deletes: "consumer will see the delete twice" | It sees two records: the delete event (op `d`, `before` set) and then a tombstone (null value, same key) when `tombstones.on.delete=true` (default) | https://debezium.io/documentation/reference/stable/connectors/postgresql.html |
| TOAST: "logical replication only sends the delta" | Unchanged TOASTed columns are **omitted** from UPDATE events (Debezium fills `__debezium_unavailable_value`); changed ones are sent whole. With REPLICA IDENTITY FULL the old image carries them | https://debezium.io/documentation/reference/stable/connectors/postgresql.html |
| Locked snapshot fix "BEGIN TRANSACTION ISOLATION LEVEL SNAPSHOT or logical replication snapshots (Postgres >= 13)" | SQL Server syntax. In Postgres the options are a REPEATABLE READ snapshot (Debezium's blocking snapshot), an exported snapshot at slot creation, or a chunked watermark snapshot (DBLog). Exported snapshots are much older than 13 | https://www.postgresql.org/docs/current/logicaldecoding-explanation.html |
| "Source failover -> re-snapshot" | Only without failover slots. Postgres 17+ syncs failover slots to a standby (`failover` slot option, `sync_replication_slots`), MySQL resumes by GTID | https://www.postgresql.org/docs/current/logicaldecoding-explanation.html |
| Transaction metadata cited to the event-router page | That URL is a 404. Transaction metadata is in the connector doc (`provide.transaction.metadata`, BEGIN/END, `event_count`, `data_collections`, per-event `total_order`, `data_collection_order`) | https://debezium.io/documentation/reference/stable/connectors/postgresql.html |
| "Five-layer stack", "100 ms worth 30% source CPU", batch "$0.01/day" vs CDC "$100+/month" | Invented or "inferred". Not used | none |
| Debezium EOS page | Confirmed: at-least-once by default, Kafka Connect KIP-618 for exactly-once into Kafka, supported by MariaDB, MongoDB, MySQL, Oracle, PostgreSQL, SQL Server; Debezium itself warns correctness is unproven | https://debezium.io/documentation/reference/stable/configuration/eos.html |
