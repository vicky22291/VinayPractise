# Edge cases: stock trading / order execution system

Every entry must be answerable out loud in under 60 seconds. Mark confidence after each study pass. Categories per `hld/CLAUDE.md` §5: failure, consistency, scale, data, operations, security. Broker-variant cases are marked (broker).

Design recap for context: gateway dedups on `(session, ClOrdID)` and normalises; risk engine (sharded by account) takes a buying-power hold; sequencer (one per symbol group) assigns `seq` and replicates the input log to 2 of 3 replicas before ack; one single-threaded matcher per shard consumes the input log, keeps the book in memory, and writes acks, fills, and book deltas to an output log keyed by `(in_seq, out_idx)`; a hot standby replays the same input log; publishers, ledger, audit, and the order DB are projections of the output log; the matcher owns an epoch and every output carries it. Details in [`solution.md`](solution.md).

---

## 1. Failure

## Edge case: matcher crashes after matching a trade but before the fill leaves the box
- **Trigger:** process kill, kernel panic, power loss on the primary matcher host, in the microseconds between updating the in-memory book and the output being written or sent.
- **Symptom:** the client that would have been filled sees nothing yet. Standby detects missed heartbeats.
- **Answer:**
  - The trade is real if and only if its output event reached the output log's commit point. If the output was never committed, the trade did not happen and nothing downstream has seen it; the standby will recompute it.
  - The hot standby has consumed the same input log up to the same `in_seq` (or a few entries behind) and has the identical book, because the matcher is deterministic. It is promoted with `epoch + 1`, checks the output log's last committed `(in_seq, out_idx)`, and resumes emitting from the next input entry. If the primary had emitted a partial set of outputs for `in_seq = n`, the standby re-emits all outputs for `n`; consumers dedup on `(in_seq, out_idx)`.
  - No client was acked for anything that was not committed, so no ack is contradicted. Detection ~200 ms of missed heartbeats, promotion ~100 ms, total gap under 1 s. Timeline in [`solution.md` §10.4](solution.md#104-failure-timeline).
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: sequencer leader dies mid-burst
- **Trigger:** GC pause, NIC failure, or host loss on the log leader for one symbol group.
- **Symptom:** gateways get no ack for ~300 ms for that group. Other groups unaffected.
- **Answer:**
  - Followers time out, elect a new leader, bump the epoch. The new leader's log ends at the last quorum-committed `seq`. Entries the old leader appended locally but never replicated to a quorum are gone. None of them was acked to a client, because ack waits for the quorum.
  - Gateways retry unacked orders to the new leader with the same `ClOrdID`. The gateway dedup table makes this safe.
  - The old leader's late appends carry the old epoch and are rejected by followers (fenced). It cannot ack anything.
  - Say it: "the ack is the commit point, and the commit point is the quorum write". Diagram D5c in [`diagrams.md`](diagrams.md#d5c-sequencer-leader-loses-its-lease-mid-burst).
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: the input log loses quorum (two of three replicas down)
- **Trigger:** a hall (AZ) failure plus one host failure, or a bad rollout that kills two replica processes.
- **Symptom:** the sequencer cannot commit. Orders for that symbol group get no ack.
- **Answer:**
  - Halt that symbol group. Do not fall back to a single replica. An exchange that "keeps going" with one copy risks losing acked orders, which is the one thing the design promises not to do. A halt is a regulated, understood state; a lost order is a lawsuit.
  - Blast radius is one symbol group (a few hundred to a few thousand symbols), not the market. Ops page fires within 5 s.
  - Recovery: restore a replica (restart or reseed from the surviving one), quorum returns, resume from the last committed `seq`. Members' resting orders are intact because they are in the log.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: risk engine shard for a big member is down
- **Trigger:** host loss on the risk shard that owns 5% of accounts.
- **Symptom:** those accounts get "risk unavailable" rejects on new orders. Their resting orders keep matching.
- **Answer:**
  - Risk state (available buying power, open holds) is written to a per-shard WAL before the approve is returned, and a standby replays it. Failover 1 to 2 s.
  - Fail closed for new orders (a wrong approve is real money), fail open for cancels (a cancel never needs buying power and must always get through).
  - Holds are conservative: if the standby is missing the last few releases it will over-reserve, not under-reserve. Releases are replayed from the output log, so they catch up.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: gateway dies with 2,000 sessions on it
- **Trigger:** host loss on one of 40 gateways.
- **Symptom:** 2,000 sessions drop. Clients reconnect to another gateway.
- **Answer:**
  - Sessions are stateful only in two places: the per-session outbound `MsgSeqNum` cursor and the `ClOrdID` dedup table. Both are projections of the output log keyed by session, so any gateway can rebuild them on reconnect by reading that session's cursor.
  - On logon the client says its last received seq; the gateway resends from there with `PossDup`. Orders in flight through the dead gateway that never reached the sequencer are simply not there; the client's retry with the same `ClOrdID` creates them once.
  - Resting orders are unaffected. Some members want "cancel on disconnect"; that is a per-session flag that the gateway's death triggers via the session registry's lease expiry.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: post-trade ledger is down for 20 minutes
- **Trigger:** ledger DB failover gone wrong.
- **Symptom:** balances and positions stale. Holds not released. Dashboards lag.
- **Answer:**
  - Trading continues. The matcher never talks to the ledger. The output log is durable, so the ledger replays every fill it missed when it returns, idempotent on `trade_id`.
  - Holds are not released during the outage, so buying power drifts conservative. Heavy traders may get rejects. That is acceptable and visible (`hold_release_lag` metric).
  - Never let the ledger's health gate the matcher. That coupling is how a slow database becomes a market halt.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: whole primary data centre lost
- **Trigger:** power, fibre cut, fire.
- **Symptom:** market halted. Members cannot connect.
- **Answer:**
  - DR site has an async copy of the input and output logs, RPO of seconds. It cannot know about the last few hundred milliseconds of orders. Every real exchange handles this the same way: declare a halt, publish the last known state per symbol (last committed `seq`), have members re-enter or confirm, reopen with an auction. RTO is minutes to an hour, driven by procedure, not software.
  - Do not promise RPO 0 across 100 km. Synchronous replication across that distance adds ~1 ms per order and cuts throughput; exchanges accept seconds of RPO for DR and RPO 0 inside the primary.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## 2. Consistency

## Edge case: two orders for the same symbol arrive at the same microsecond at two gateways
- **Trigger:** two colo members racing for the same resting liquidity.
- **Symptom:** none. One fills, one rests or rejects.
- **Answer:**
  - The order is decided once, by the sequencer: whichever append the leader processes first gets the lower `seq`. Gateway receive timestamps are recorded for audit but do not decide priority, because two gateways' clocks are not comparable at the microsecond and because the sequencer is the only single point that sees both.
  - The matcher only sees `seq`. So the answer is reproducible forever: replay the log, get the same result.
  - Fairness across gateways comes from equal-length cross-connects and one sequencer per symbol; that is a hardware and procedure problem, not a software one.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: client retries an order after a timeout
- **Trigger:** ack lost on the wire, client resends the same `ClOrdID`.
- **Symptom:** without dedup: two orders, double position. With it: one order, second request answered with the first's state.
- **Answer:**
  - Dedup key is `(session or account, ClOrdID)`. The gateway holds it in memory, backed by the output log. The retry gets the existing exchange order id and its current state.
  - If the first attempt has not reached the sequencer yet (still in flight), the retry is held until the first resolves. Never send both.
  - Retention: the dedup key must outlive the client's retry window and the FIX session, so the key stays valid for the trading day plus one. A `ClOrdID` reused the next day is a new order; the FIX spec requires uniqueness per day, and the gateway rejects reuse within a day.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: cancel and fill race for the same order
- **Trigger:** client cancels while an opposite order is arriving.
- **Symptom:** client either sees `Canceled` or sees `Fill` then `CancelReject(TooLateToCancel)`. Never both a cancel and a fill for the same quantity.
- **Answer:**
  - The cancel is an input event with its own `seq`. The matcher processes strictly in `seq` order, so the race is settled by the log: if the fill's `seq` is lower, the cancel finds nothing (or a reduced quantity) and rejects or cancels the remainder.
  - There is no window between "decide" and "apply" because both happen on one thread with no IO in between.
  - A partial: cancel arrives after 40 of 100 filled. Result: `Fill 40`, then `Canceled, leaves 0, cum 40`. The client's `OrdStatus` reflects both.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: same matcher output delivered twice downstream
- **Trigger:** publisher restart, standby promotion re-emits outputs for the last input, Kafka-style at-least-once tailing.
- **Symptom:** without dedup: a fill reported twice, a ledger posting doubled.
- **Answer:**
  - Every output event is keyed `(shard, in_seq, out_idx)` and carries the matcher epoch. That key is the trade id for fills. Every consumer (execution report publisher, ledger, market data, audit) dedups on it. The ledger's posting table has a unique constraint on `trade_id`.
  - The per-session `MsgSeqNum` to the client is assigned by the publisher from its own cursor, after dedup, so the client never sees the same trade under two seq numbers.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: buying power is per account, matching is per symbol, one order touches both
- **Trigger:** every order. This is the "where is the transaction" question.
- **Symptom:** naive design: check balance, place order, another order on another symbol spends the same balance.
- **Answer:**
  - No cross-shard transaction. Instead: a hold. The risk shard subtracts the worst-case notional and records `hold_id` before the order is allowed to the sequencer. The order carries `hold_id`. Fills, cancels, and rejects produce `Release(hold_id, used)` events that flow back to the risk shard from the output log.
  - The invariant is: sum of open holds plus settled positions never exceeds equity. Holds are always taken before and released after, so between the two the account is over-reserved, never under.
  - Failure between hold and sequence (gateway dies): the hold leaks until a sweeper compares open holds against the log and releases orphans after a timeout (30 s). Conservative direction again.
  - Detail in [`deep-dives/risk-and-buying-power.md`](deep-dives/risk-and-buying-power.md).
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: a self-match, one member on both sides
- **Trigger:** two algos from the same firm cross each other.
- **Symptom:** a wash trade, which is illegal in most markets.
- **Answer:**
  - The matcher checks `owner_id` of the incoming order against the resting order it is about to hit. If equal and the member has self-trade prevention on, apply the configured mode: cancel newest (incoming), cancel oldest (resting), cancel both, or decrement and cancel. Deterministic, in the loop, no IO.
  - This is a per-member setting delivered to the matcher as a sequenced config event, never read from a database mid-loop.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: replace changes price, does it keep time priority?
- **Trigger:** member modifies a resting order.
- **Symptom:** member expects to keep queue position.
- **Answer:**
  - Rule (Nasdaq, CME, most venues): a price change or a quantity increase loses time priority (it is a cancel plus new); a quantity decrease keeps it. Implement replace as cancel-then-new atomically inside one input event when priority is lost, and as an in-place decrement when it is kept.
  - Either way it is one `seq`, so no other order can slip between the cancel and the new.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: gateway clocks differ by 300 us
- **Trigger:** PTP fault on one gateway host.
- **Symptom:** audit timestamps for that gateway are skewed. Matching is unaffected.
- **Answer:**
  - Priority is by `seq`, not by timestamp, so nothing in matching changes. Timestamps are for audit and regulation (RTS 25 wants 100 us to UTC for HFT venues; CAT wants 50 ms for most events). A skewed gateway is a compliance incident, not a market integrity one.
  - Monitor PTP offset per host and page above 50 us. The matcher timestamps every event with the sequencer's clock as well, giving two independent stamps.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case (broker): the venue confirmed a fill but our DB write failed
- **Trigger:** our order service crashed between receiving the `ExecutionReport` and committing it.
- **Symptom:** user sees "pending"; we actually hold the shares.
- **Answer:**
  - The venue's report is the truth. Our session with the venue has a sequence number; on reconnect we ask for a resend from the last seq we committed, and the fill arrives again. Apply idempotent on `(ClOrdID, ExecID)`.
  - Never set the order to `FILLED` from our own belief; only from a venue message. Never mark it `REJECTED` because we timed out; mark it `UNKNOWN_AT_VENUE` and ask (`OrderStatusRequest`), then reconcile against drop copy at end of day.
  - Diagram D5d in [`diagrams.md`](diagrams.md#d5d-broker-variant-venue-confirms-a-fill-after-our-timeout). Detail in [`deep-dives/broker-variant.md`](deep-dives/broker-variant.md).
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case (broker): user sees a price, taps buy, the fill is worse
- **Trigger:** market moved in the 300 ms between the quote render and the fill.
- **Symptom:** complaint, or a regulator asking about best execution.
- **Answer:**
  - Market orders have no price guarantee; show the user the quote as indicative and the fill as final. For price protection, send a marketable limit at the shown price plus a collar (e.g. 1%) instead of a pure market order.
  - Keep the quote the user saw (`quote_id`, timestamp, NBBO) with the order for the audit trail.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## 3. Scale

## Edge case: market open, 100x the average rate for 60 seconds
- **Trigger:** 9:30:00. Every day.
- **Symptom:** queues form in front of sequencers and matchers. Latency p99 climbs from 50 us to milliseconds.
- **Answer:**
  - Sized for it: the hottest shard at 250 k msg/s against a single-thread ceiling of 1 to 5 M msg/s. The queue in front of the matcher absorbs the burst; latency degrades, correctness does not. Nothing on the matcher path allocates or blocks.
  - What is shed: market data conflation for slow consumers (send the latest book, not every delta); retail WebSocket updates throttled to 4 per second per symbol. What is never shed: order acks, fills, execution reports.
  - The gateway applies per-session message rate limits (e.g. 5 k msg/s) so one member's burst cannot fill the sequencer's queue. The risk engine is sharded wide enough that it is not in the critical path's tail.
  - Real exchanges add an opening auction so the open is one match, not a stampede. Say it as the seam.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: one symbol is 40% of all volume
- **Trigger:** meme stock, index rebalance day, an IPO.
- **Symptom:** one matcher thread at 40% of fleet load.
- **Answer:**
  - Move it to its own shard: a new sequencer group and matcher pair on a dedicated machine. The symbol-to-shard table is versioned; the cutover is: stop accepting new orders for the symbol for ~1 s (reject with "symbol moving, retry"), let the old shard drain, snapshot the book, load it into the new shard at `seq 0` of the new log with a pointer to the old log's last `seq`, flip the table, resume. Done outside the open, or during a scheduled halt.
  - If one symbol outgrows one core (rare: 1 to 5 M msg/s), the honest answer is that price-time priority on one book is inherently single-writer. Levers in order: batch inputs per loop, move output serialisation off the thread, kernel-bypass NIC, faster core. Splitting one book across threads breaks priority; nobody does it.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: 10 million retail users want live prices
- **Trigger:** a consumer broker's app.
- **Symptom:** naive design has 10 M subscribers hitting the market data publisher.
- **Answer:**
  - Fan-out is a tree. The matcher writes one book delta to the output log. One publisher per shard reads it and multicasts (or pushes to a few hundred edge servers). Each edge server holds the current top of book per symbol and pushes to its WebSocket clients, conflated to at most N updates/s per symbol. 10 M clients over 500 edge servers is 20 k connections each, well within a modern box.
  - The matcher and the log never know how many subscribers exist. That is the point.
  - Detail in [`deep-dives/execution-reports-and-market-data.md`](deep-dives/execution-reports-and-market-data.md).
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: a member's algo sends 1 M messages/s, mostly cancels
- **Trigger:** a bug, or aggressive quoting.
- **Symptom:** one session dominates a sequencer's input.
- **Answer:**
  - Per-session throttle at the gateway (messages/s and order-to-trade ratio), reject above it with a specific reason. Fair queuing across sessions into the sequencer so one session cannot starve others.
  - Exchange kill switch: ops or the member's own risk desk can cancel all of a session's orders and block new ones with one sequenced command.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: 10x symbols tomorrow (10 k to 100 k, e.g. options)
- **Trigger:** listing options or a crypto exchange listing thousands of pairs.
- **Symptom:** more shards, more books, mostly cold.
- **Answer:**
  - Cold symbols pack thousands per shard; the cost is memory (a book is small) and log volume, both linear. The shard table grows, the design does not change.
  - Options add the complex-order problem (multi-leg orders that span symbols). That breaks one-symbol-one-shard and needs either a dedicated complex-order book that legs into the single books with implied pricing, or a rule that legs are matched atomically only inside one shard. Name it as the seam; CME's implied spreads are the reference.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## 4. Data

## Edge case: the matcher version changes and the output would differ on replay
- **Trigger:** a bug fix changes tie-breaking or rounding.
- **Symptom:** replaying the old log with the new binary produces different fills. Audit is now inconsistent.
- **Answer:**
  - The output log is the record, not the replay. Audit reads the output log. Replay is used to rebuild state, and it must be done with the binary version that produced the log, so every log segment carries the matcher build id. Recovery of an old day's state uses the old build.
  - New builds are deployed at a snapshot boundary: snapshot, switch the standby to the new build, replay from the snapshot (which is state, not behaviour), promote. Deterministic replay is only ever needed from the last snapshot, minutes of log, on the same build.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: regulator asks for every event on order X from 3 years ago
- **Trigger:** CAT request or an investigation.
- **Symptom:** need a complete, ordered history in hours, not weeks.
- **Answer:**
  - The audit store holds every input and output event, partitioned by day and shard, indexed by exchange order id and by `ClOrdID` with account. Objects in cold object storage after 90 days; index in a columnar store. A single-order lookup is one index hit plus a few object reads: minutes.
  - Retention 6 years minimum (SEC 17a-4 for broker-dealers), immutable (object lock).
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: end-of-day snapshot and log growth over 3 years
- **Trigger:** 1 B messages/day, 250 trading days/yr.
- **Symptom:** ~100 GB/day input log, ~200 GB/day output log, ~75 TB/yr raw, ~225 TB over 3 years before compression.
- **Answer:**
  - Hot: today's logs on NVMe on the log replicas. Warm: last 90 days on object storage, standard tier. Cold: 6 years on archive tier. Compressed 3 to 5x (binary, repetitive). Cost is small next to the colo.
  - The book itself is snapshotted every minute and at close; a day's replay is at most a minute of log. GTC orders survive the day in the closing snapshot and are loaded at open.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: a symbol is delisted, split, or renamed
- **Trigger:** corporate action.
- **Symptom:** resting GTC orders at pre-split prices.
- **Answer:**
  - Corporate actions are applied at a boundary (overnight): cancel all resting orders on the symbol with a specific reason (industry practice for splits), publish the new symbol table version, members re-enter. Never adjust prices in place inside the book.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## 5. Operations

## Edge case: what pages at 3 am (or at 9:31 am)
- **Trigger:** on-call design question.
- **Answer:**
  - `matcher_lag_seq > 1,000` for 5 s on any shard (matcher falling behind the log): page.
  - `standby_lag_seq > 10,000` or standby heartbeat missing 30 s: page, because failover is now unsafe.
  - `log_quorum_lost` on any group: page immediately, trading halted.
  - `ack_latency_p99 > 1 ms` in the colo path for 60 s: page.
  - `hold_release_lag > 60 s`: page (ledger or risk falling behind).
  - `ptp_offset > 50 us` on any gateway: ticket, page if > 1 ms.
  - `session_gap_resends / min` spike: ticket (a publisher or network problem).
  - Dashboards: msgs/s per shard, book depth per top symbol, fill rate, reject reasons, standby lag, log fsync latency, disk headroom on log replicas.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: deploy a new matcher build during the trading day
- **Trigger:** a fix cannot wait for the close.
- **Answer:**
  - Roll the standby first: stop the standby, start the new build, load the last snapshot, replay the log tail, confirm its book hash matches the primary's at the same `seq` (both publish a book hash every 1,000 inputs). Then a controlled promotion: primary stops consuming at `seq n`, standby is promoted with `epoch + 1` at `n + 1`, old primary becomes the new standby on the new build. Gap ~100 ms, no lost or duplicate output. Do it per shard, coldest first.
  - Rollback is the same procedure with the old build. The book hash comparison is what makes this safe; without it, a determinism bug is discovered by a member.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: migrating from a database-backed matcher without a gap
- **Trigger:** legacy system matches with `SELECT ... FOR UPDATE`.
- **Answer:**
  - Shadow: tee every order to the new sequencer and matcher, compare fills offline for weeks; differences are bugs or priority rule mismatches. Pilot on cold symbols with the old path in shadow. Then by tier. The symbol table flip is the rollback. The old DB becomes a projection of the output log before it is decommissioned. Gantt in [`diagrams.md` D12](diagrams.md#d12-rollout--migration).
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: determinism bug, primary and standby books diverge
- **Trigger:** a `HashMap` iteration order, a wall-clock read, a float rounding difference across CPUs.
- **Symptom:** book hashes differ at the same `seq`.
- **Answer:**
  - Detected by the periodic book hash. Response: the standby is now useless for failover; page, start a fresh standby from the primary's snapshot, and treat the divergence as a Sev-1 bug because the next failover would change fills.
  - Prevention: no wall clock (time arrives as a sequenced heartbeat event), no random, no threads inside the matcher, integer prices in ticks and integer quantities in lots, no iteration over unordered containers in the decision path, a replay test in CI that runs a day's log against the build and compares the output hash.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## 6. Security and abuse

## Edge case: a member spoofs another member's session
- **Trigger:** stolen credentials, or a misconfigured FIX session.
- **Answer:**
  - Sessions are bound to a source IP or cross-connect port and a per-session key at logon; the gateway stamps `member_id` from the session, never from the message body. `Account` in the message is validated against the session's allowed accounts.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: fat finger, an order at 100x the market price or 1,000x the usual size
- **Trigger:** typo, bad algo.
- **Answer:**
  - Price collar at risk: reject a limit more than X% (e.g. 5 to 10%) away from the last trade or NBBO. Max order size and max notional per account. These run before the sequencer, in microseconds, on the account shard. Market-wide: limit-up limit-down bands and circuit breakers as sequenced state changes the matcher honours (reject or halt).
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: a compromised gateway injects orders
- **Trigger:** a gateway host is owned.
- **Answer:**
  - The gateway can only send what a session could send; it cannot forge another member's id because sequencer-side the `member_id` is checked against the gateway's session registry, and all inputs are logged with the gateway id. Blast radius is the sessions on that gateway; kill switch cancels them all. Every order is attributable after the fact from the log.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: market manipulation patterns (spoofing, layering)
- **Trigger:** a member places and cancels to move the price.
- **Answer:**
  - Not the matcher's job. Surveillance is a consumer of the output log (order-to-trade ratio per member, cancel patterns, wash detection). The matcher gives it a complete, ordered, timestamped record, which is the only thing it needs from us. Name it as out of scope, name the data it uses.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident
