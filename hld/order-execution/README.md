# Stock trading / order execution system

> One-line answer: put every order through a per-symbol sequencer that assigns a total order and appends to a replicated log before anything else happens, then let one single-threaded, deterministic matching engine per symbol shard consume that log, hold the limit order book in memory (price levels as an array indexed by tick, each level a FIFO of orders, an order-id hash map for O(1) cancel), and emit acks, fills, and book deltas as a second log; everything downstream (execution reports, market data, ledger, audit, order DB) is a replay of those two logs, a hot standby replays the same input log to take over with the same state, and pre-trade risk (buying power holds, price collars, kill switch) runs before the sequencer on an account-sharded service so the matcher never talks to a database.

Tier 1, problem #9 in [`hld/README.md`](../README.md). Reported at Databricks as "design a stock trading system" and as the smaller "game / playlist transaction service with retry-safe semantics" (same idempotency and ordering questions on a smaller domain), at Coinbase as "design the order book / matching engine", at Google and in ByteByteGo as "design a stock exchange", and at Robinhood-style brokerages as "design Robinhood". The interviewer's reference answer is almost always the LMAX / Jane Street shape: sequencer, deterministic single writer, event-sourced replay. See [`research/`](research/).

## Problem statement

Build the system that accepts buy and sell orders for a set of instruments, matches them fairly by price then time, tells each party what happened, publishes the resulting prices to everyone, and keeps a record good enough that a regulator can reconstruct any order's life three years later. It must not lose an accepted order, must not fill the same order twice, must not let two people buy the same share, and must keep running through a machine failure without a human. Then make it fast: tens of microseconds in the co-located path, and correct at market open when the whole day's volume arrives in the first minutes.

Two variants share the design and differ in who owns the matching:

| Variant | We own | External party | The hard question |
|---|---|---|---|
| Exchange (Coinbase, ByteByteGo, Databricks "trading system") | Matching engine, book, market data, trade capture | Clearing house, members' systems | Total order per symbol, determinism, failover with zero loss |
| Broker (Robinhood, "stock trading app") | Accounts, buying power, order management, routing | The exchange or market maker that fills the order | Consistency between our DB and the venue's fills, retries, "did it execute?" |

The exchange variant is the main answer. The broker variant is [`deep-dives/broker-variant.md`](deep-dives/broker-variant.md); the interviewer often switches to it mid-way.

## Functional requirements

Core:
- Place an order: limit or market, buy or sell, with a time in force (day, GTC, IOC, FOK). Reject fast with a reason, or acknowledge with an exchange order id.
- Cancel or replace a working order. A cancel that loses the race to a fill returns "too late to cancel", never a phantom cancel.
- Match by price-time priority. An incoming order fills against the best opposite price first, oldest order first at that price, and the remainder rests on the book.
- Report executions: every ack, fill, partial fill, cancel, and reject goes to the owner, in order, exactly once from the client's point of view, with a resend path.
- Publish market data: top of book and price-level depth to all participants, with sequence numbers so a consumer can detect gaps and resync.
- Keep the books: cash and securities per account move on every fill (double-entry), and the end-of-day trade file goes to clearing.

Below the line (say it out loud):
- Auctions (opening and closing cross), pegged orders, icebergs, stop orders. Named as seams in the order type table; not built in 45 minutes.
- Cross-symbol orders (spreads, baskets). They break "one symbol, one shard" and are the 10x evolution.
- Clearing and settlement themselves. We produce the file and reconcile against it; NSCC nets and settles T+1.
- Smart order routing across venues, payment for order flow, Reg NMS best-execution logic. Broker variant, one paragraph.
- Surveillance, market making, trading strategies.

## Non-functional requirements

| Dimension | Target |
|---|---|
| Scale | 10 k symbols. 1 B order messages per trading day (new, cancel, replace; cancels are most of it). Avg ~43 k msgs/s over 6.5 h, peak 500 k msgs/s in the first minute after open. ~100 M trades/day. The hottest symbol is ~5% of all messages |
| Latency | Colo path (order in at gateway to ack or fill out): p50 < 20 us, p99 < 100 us inside the matching tier. Retail path (app to confirmation): p99 < 500 ms. Market data: first tick out within 50 us of the match |
| Durability | RPO 0 for accepted orders and trades. An order is acknowledged only after its log entry is replicated to a second machine. No accepted order is ever lost |
| Availability | 99.99% during market hours (about 4 min/yr). Matching failover for one symbol shard in < 2 s with no lost or duplicated fills |
| Consistency | Strong and totally ordered within one symbol (the log is the truth). Strong per account for balances. Eventual across symbols (portfolio views, dashboards) with a lag under 1 s |
| Fairness | Price-time priority is exact: the sequencer order is the only order. Two orders that arrive 1 us apart at different gateways are still ordered deterministically |
| Auditability | Every event for every order reconstructable for 6 years. Clock stamps within 100 us of UTC at the gateway (MiFID II RTS 25 for HFT; CAT in the US) |
| Idempotency | A client retry with the same `ClOrdID` never creates a second order. A replayed fill never moves money twice |

## What interviewers probe (the ladder)

1. Two orders for the same symbol arrive at the same microsecond at two different gateways. Who is first, and how do you prove it later?
2. Why one thread per symbol? What does the single writer buy, and what is its ceiling? Show the number.
3. The matching engine crashes after it matched a trade but before the fill left the box. Is the trade real? What does the standby do?
4. Client sends an order, times out, retries. What stops the second copy? Where does the dedup key live and for how long?
5. A cancel and a fill for the same order race. Who wins, and what does the client see?
6. Buying power lives per account. Matching lives per symbol. One order touches both. Where is the transaction?
7. Market open: 100x the average rate for 60 seconds. What backs up, what is shed, and what is never shed?
8. One symbol is 40% of volume. How do you move it without stopping the market?
9. Ten million retail users want live prices. How does one match become 10 M updates without touching the matcher?
10. The venue confirmed a fill but our database write failed (broker variant). Do we have the shares or not?
11. A regulator asks for everything that happened to order X on a day three years ago. How long does that take?
12. You need to deploy a new matcher build during the trading day. How, without stopping the market or changing the book?

## Files

| File | What it is |
|---|---|
| [`solution.md`](solution.md) | Full HLD, Bad / Good / Great ladders, nitty-gritty internals |
| [`diagrams.md`](diagrams.md) | The D1 to D12 diagram set |
| [`edge-cases.md`](edge-cases.md) | Every "what if" with a 60-second answer and a confidence box |
| [`deep-dives/order-book-and-matching.md`](deep-dives/order-book-and-matching.md) | Book data structures, the matching loop, order types and what each changes, self-trade prevention, memory and latency per operation |
| [`deep-dives/sequencer-and-replicated-log.md`](deep-dives/sequencer-and-replicated-log.md) | Total order, the input log as the database, replication before ack, fsync numbers, snapshots plus log tail, determinism rules |
| [`deep-dives/failover-and-fencing.md`](deep-dives/failover-and-fencing.md) | Hot standby replay, epochs and fencing, the crash-between-match-and-publish case, split brain, the second-by-second timeline |
| [`deep-dives/risk-and-buying-power.md`](deep-dives/risk-and-buying-power.md) | Pre-trade checks (15c3-5), the hold pattern, account shard vs symbol shard, release on cancel / reject / fill, kill switch |
| [`deep-dives/execution-reports-and-market-data.md`](deep-dives/execution-reports-and-market-data.md) | Per-session sequence numbers and resend, exactly-once from the client's view, L1 / L2 / L3, snapshot plus incremental, conflation, 10 M-user fan-out |
| [`deep-dives/post-trade-ledger-and-settlement.md`](deep-dives/post-trade-ledger-and-settlement.md) | Double-entry for cash and securities, idempotent trade capture, the clearing file, T+1, reconciliation breaks |
| [`deep-dives/broker-variant.md`](deep-dives/broker-variant.md) | We call an external venue: order state machine, lost acks, fills after timeout, the DB-write-failed case, drop copy reconciliation |
| [`research/`](research/) | Raw web research notes with source links. Input to the files above, not study material |
| `order-execution.excalidraw` | My drawing. Missing until I draw it |
| `my-attempt.md` | My timed attempt before reading the solution |
