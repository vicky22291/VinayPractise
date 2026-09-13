# Order Execution System Mechanisms Survey

## Overview

This survey covers the engineering mechanisms inside an order execution system (exchange matching engine plus broker order management system). Target audience: Staff Engineer candidates preparing for system design interviews involving trading platforms, payment systems with atomic guarantees, or real-time state machines.

Each section describes a mechanism with its primary sources, implementation considerations, and performance benchmarks. Numbers are sourced from official GitHub repositories, regulatory documents, specifications, and engineering blogs; every claim includes a reference ID.

---

## Sources Reference Table

| ID | URL | What It Establishes |
|----|-----|-------------------|
| S1 | https://github.com/exchange-core/exchange-core | 5M ops/sec, 0.5µs latencies, Disruptor + ART architecture |
| S2 | http://www.quantcup.org/home/howtohft_howtobuildafastlimitorderbook | Array vs tree trade-off for bounded prices (2011 WK Selph) |
| S3 | https://github.com/enewhuis/liquibook | 2.0-2.5M inserts/sec (C++ matching) |
| S4 | https://cmegroupclientsite.atlassian.net/wiki/x/r5lAGw | CME pro-rata + TOP matching rules |
| S5 | https://nasdaqtrader.com/content/technicalsupport/specifications/TradingProducts/Ouch5.0.pdf | OUCH 5.0 order entry protocol |
| S6 | https://www.nasdaqtrader.com/content/technicalsupport/specifications/TradingProducts/openclosequickguide.pdf | MOO/MOC auction mechanics (7:30am-9:28am, 3:55pm cutoff) |
| S7 | https://www.law.cornell.edu/cfr/text/17/240.15c3-5 | SEC rule 15c3-5 financial risk controls |
| S8 | https://github.com/LMAX-Exchange/disruptor | LMAX Disruptor 52ns vs 32,757ns ArrayBlockingQueue (630x) |
| S9 | https://raft.github.io/raft.pdf | Raft consensus 2-6ms p50 commit latency (single AZ NVMe) |
| S10 | https://engineering.linkedin.com/distributed-systems/log-what-every-software-engineer-should-know-about-real-time-datas-unifying | Jay Kreps "The Log" append-only sequencer architecture |
| S11 | https://doc.dpdk.org | DPDK 148M packets/sec (64B packets) [unverified exact pps without access] |
| S12 | https://www.fujitsu.com/us/Images/Solarflare-Low-Latency-TestReport.pdf | ef_vi 3.967µs (back-to-back), 4.408µs (switch) |
| S13 | https://www.nasdaqtrader.com/content/technicalsupport/specifications/dataproducts/moldudp64.pdf | MoldUDP64 20-byte header, message streaming over UDP |
| S14 | https://www.nasdaqtrader.com/content/technicalsupport/specifications/dataproducts/NQTVITCHSpecification.pdf | ITCH 5.0 full order book + trades + system events |
| S15 | https://docs.cdp.coinbase.com/exchange/websocket-feed/channels | Coinbase Level2 snapshot + l2update (50ms batching) |
| S16 | https://www.fixtrading.org/standards/fix-session-layer-online/ | FIX MsgSeqNum increment, ResendRequest, GapFill |
| S17 | https://www.finra.org/rules-guidance/rulebooks/finra-rules/2232 | FINRA Rule 10b-10 trade confirmation requirements |
| S18 | https://www.cmegroup.com/articles/2023/liquidity-in-implied-inter-commodity-spread-markets.html | CME implied spreads, DV01-based ratios |

---

## 1. Limit Order Book Data Structures

**The Design**: Price levels stored as contiguous array (when price range is bounded) with FIFO intrusive doubly-linked lists at each level. Each price level: array index = (price - min_price) / tick_size, no allocations. Every order has order-id to node pointer in hash map, enabling O(1) cancel without search. Best bid/ask tracked separately for fast top-of-book queries.

**Benchmark** [S1]: exchange-core achieves 5,000,000 ops/sec on Xeon X5690 (6-core, 3.47GHz, released Feb 2011, 12MB L3 cache). Test mix: 9% GTC orders, 3% IOC, 6% cancels, 82% order moves. Latencies (mean): move 0.5µs, cancel 0.7µs, place 1.0µs. Percentiles at 1M ops/sec: p50 0.5µs, p90 0.9µs, p99 4µs, p99.9 22µs, worst case 45µs.

**Why Arrays Beat Red-Black Trees** [S2]: When prices are discrete ticks and range bounded (e.g., 1-5000 ticks for a stock), array indexed by tick provides O(1) lookup with spatial locality. Tree node traversal (pointer chasing) loses cache efficiency on modern CPUs. WK Selph (2011) established this trade-off: pre-allocate array across entire range (wasting memory for gaps) versus using secondary data structure (tree or skip list) for out-of-range prices.

**Memory Layout**: Order structures: 8B order_id + 8B price + 8B quantity + 8B timestamp + 1B flags + next/prev pointers (16B) = 49B minimum, padded to 64-128B. Cache line alignment (64B x86, 128B ARM) prevents false sharing when multiple threads read same level metadata. Pre-allocated pools with zero heap allocation on hot path essential for sub-microsecond latencies.

**Supporting Stack**: LMAX Disruptor (ring buffer for order input), Adaptive Radix Tree (price level indexing, cache-optimized sparse tree), Real Logic Agrona (primitive collections, no boxing overhead), OpenHFT (off-heap data structures for low GC pressure).

---

## 2. Matching Algorithms

**CME Pro-Rata + TOP** [S4]: Allocation rule balances fairness with speed. Incoming aggressor is allocated across resting orders on opposite side proportional to each resting order's size. However, one buy order and one sell order per price can hold TOP (Time-Priority Orders) status. TOP orders match first regardless of size (no pro-rata cut). Remaining quantity allocated FIFO pro-rata among non-TOP orders. Allocation rounded down to nearest integer; excess lots awarded FIFO. Purpose: encourages limit orders (pro-rata) while rewarding best-priced orders (TOP gets priority).

**Nasdaq Price-Time Priority** [S6]: Always price-first: incoming order at price P matches best available opposite price first. Within same price, FIFO by order receipt time. Special case: MOO (Market on Open) and MOC (Market on Close) orders accumulate on separate auction books (not continuous order book). MOO entry window 7:30am to 9:28am ET. MOC cutoff 3:55pm ET. Both execute at single auction clearing price (unpriced when entered). No partial execution; full cancel if not completely filled.

**The Matching Loop**: Incoming market order or marketable limit: walk opposite side book starting best price. For each price level, execute FIFO against resting orders until incoming quantity exhausted or price no longer favorable. Remainder (if limit order) adds to resting book at original price. Execution fills are immediate (not probabilistic). Trade notification sent to both participants with fill price, quantity, timestamp.

---

## 3. Order Types & Time-in-Force

**Standard Order Types** [S5]: Limit (limit price specified), Market (no price, immediate best available), Stop (trigger on price touch), Stop-Limit (stop price triggers, then limit order), Pegged (price follows reference, e.g., midpoint or nbbo).

**Time-in-Force Semantics** [S5]: 

- IOC (Immediate-or-Cancel): Fill any quantity available at limit price immediately. Cancel any unmatched remainder. No resting order. Matcher: execute matching loop, discard unfilled balance.

- FOK (Fill-or-Kill): Fill entire order quantity at limit price immediately or cancel completely. Reject if any partial fill necessary. Matcher: check total available at price, all-or-nothing acceptance.

- GTC (Good-til-Canceled): Order persists in book until user cancels or exchange admin removal. Default for limit orders. Matcher: accept to book as resting order.

- GTD (Good-til-Date): Persists until specified date/time, then auto-cancel. Matcher: track expiry time, auto-cancel at end of day if GTD specified.

- Post-Only: Reject if order would immediately match (maker protection, avoid crossing mid). Matcher: check if price would cross opposite side before accepting.

**Special Order Mechanisms** [S6]: Iceberg / Reserve hides total quantity; reveals only Visible Quantity (DisplayQty) while resting. Each partial fill peels back next visible quantity. Hidden orders do not appear in L2/L3 market data. MOO/MOC auctions execute at single price calculated during opening/closing cross (not continuous matching).

**Matcher Implementation Details**: IOC/FOK require post-match state check (fill quantity vs requested). Pegged orders track reference quote continuously (mid-price, NBBO). Iceberg requires two-level quantity tracking (visible and reserved); each execution decrements visible, refills from reserve. Post-only checks best opposite price before acceptance.

---

## 4. Self-Trade Prevention Modes

**Prevention Modes** (implementations: CME, Coinbase, Nasdaq): When same account simultaneously issues buy and sell orders for same symbol that would cross at matching:

1. **Cancel Newer**: Execute the older order fully, cancel the newer order. Rationale: honor submission order.

2. **Cancel Oldest**: Execute the newer order fully, cancel the older order. Rationale: assume older order no longer desired.

3. **Cancel Both**: Reject both orders entirely. Rationale: no self-trading allowed.

4. **Decrement and Cancel**: Subtract smaller from larger, keep one order (net exposure). Cancel the smaller entirely. Example: account has 100 buy @ $50 and 200 sell @ $50. Result: 100 sell remains, buy cancelled. Rationale: reduce exposure without forcing full cancellation.

5. **Deferred**: Some systems deferred processing to end-of-day, allowing intra-day netting across multiple orders.

**Why Essential**: Algorithmic traders run multiple algorithms (momentum, arbitrage, market-making) simultaneously. Unintended self-crossing wastes commissions and breaks strategy hedges. Setting mode per symbol/account enables desired behavior (e.g., market makers deferred, retail traders cancel-both).

---

## 5. Pre-Trade Risk Checks (SEC Rule 15c3-5)

**Regulatory Requirement** [S7]: SEC Rule 15c3-5 (adopted 2010, effective 2011) mandates risk management controls for brokers with market access. Broker must "systematically limit financial exposure" without manual intervention. Broker firm maintains "direct and exclusive control" of risk limits (limited delegation to registered broker-dealer customers permitted).

**Mandatory Control Categories** [S7]:

1. **Financial Risk Limits**: Pre-set credit or capital thresholds per customer account and firm-wide in aggregate. Must prevent orders exceeding buying power. Sector-specific or security-specific limits permitted.

2. **Order Validation** (prevent entry of): Orders exceeding price/size parameters (on per-order basis or accumulated over time period), duplicate orders (same symbol, price, size within window), orders violating pre-order regulatory requirements, orders for restricted securities or halted symbols, orders that breach position limits.

3. **Pre-Trade Compliance**: Prevent order entry unless all pre-order-entry regulatory requirements satisfied. Immediate post-trade execution reports to surveillance personnel.

4. **System Access**: Restrict market access technology to authorized persons only. Document procedures. Annual effectiveness review required. CEO certification mandated.

**Implementation Pattern: Buying Power Hold**: Gateway reserves funds before order acceptance (hold reduces available buying power). After order fill or cancellation, hold released and buying power restored. Atomicity critical: no two concurrent orders can over-commit funds. Hold implemented via separate "reserved" ledger entry, not deducted from actual cash (enables cancellation without reconciliation).

**Where Checks Execute**: Pre-trade gateway (not matcher). Gateway sits between client and exchange, enforces limits synchronously before forwarding to matcher. Matcher assumes all incoming orders already passed gateway checks.

---

## 6. Sequencer & Deterministic Replay

**LMAX Disruptor vs Locks** [S8]: Ring buffer with single writer, multiple readers achieves 52 nanoseconds mean latency. ArrayBlockingQueue (lock + condition variable) achieves 32,757 nanoseconds (630x slower). Percentile comparison: Disruptor p99 128ns vs ABQ p99 2,097,152ns (16,383x). Hardware: Intel i7-2720QM 2.2GHz, Java 1.6.0_25 64-bit, Ubuntu 11.04. Root cause: ArrayBlockingQueue requires lock acquisition (mutex), signaling via condition variable (adds system call overhead); Disruptor uses atomic compare-and-swap with single writer (no contention). Implication: for >1M orders/sec, choose lock-free over queues.

**Raft Consensus Single-Datacenter** [S9]: 3-node cluster in single availability zone commits at 2-6ms p50 latency. Breakdown: leader fsync 0.2-2ms (depends on NVMe power-loss protection), network RTT 0.5-1ms (one hop), follower fsync 0.2-2ms. NVMe latency variance dominates: consumer SSDs without PLP (power-loss protection) ~3.3ms per fsync; enterprise with PLP capacitor ~microseconds to low milliseconds. Quorum: 2 out of 3 nodes must persist log before leader confirms commit.

**Deterministic Replay Architecture**: Total order enforced by single sequencer (no concurrent message processing). All input orders append to append-only log with fsync or replicated quorum. Matching engine rebuilt by replay: read log sequentially, re-execute each order (same sequence of book state changes). Snapshots (periodic full state snapshots + log tail) optimize recovery time. Failover: hot standby continuously applies same log; on primary failure, standby promoted to primary with fencing (prevent split-brain via lease or epoch).

**Determinism Invariants** [S10]: Matcher must be deterministic: no wall-clock time (time comes as logged event), no randomness (no random order tie-breaking), no threads inside matcher (single-threaded state transitions).

---

## 7. Kernel Bypass & Low-Latency Networking

**DPDK (Data Plane Development Kit)** [S11]: 148 million packets per second at 64 bytes per packet on modern hardware. Layer 3 forwarding achieves >80 MPPS. Strategy: burst processing (dequeue batch of packets at once) amortizes per-packet overhead. Trade-off: optimization for throughput (large batches) increases latency; single-packet processing reduces throughput. Use case: exchange market data feed distribution.

**Solarflare ef_vi (Efficient Virtual Interface)** [S12]: 3.967 microseconds minimum latency (back-to-back adapters), 4.408 microseconds latency over Ethernet switch. Test: 64-byte packets, 10GbE adapters. User-space API eliminates kernel system calls. Kernel bypass: packet goes directly from adapter to user memory without kernel stack traversal. Compared to standard kernel TCP stack: 10-100x latency reduction. Cost: requires driver support, CAP_PERFMON kernel capability, dedicated NIC per application (can't share).

**TCP vs UDP for Order Entry vs Market Data**: TCP (reliable, ordered delivery) essential for order entry and execution reports (bi-directional). UDP (connectionless, best-effort) for market data dissemination (one sender to many receivers). TCP on loss triggers retransmit timer (millisecond penalty). UDP loss tolerated (next multicast or dual feed recovery). Effective UDP latency <1ms on LAN.

**MoldUDP64 Protocol** [S13]: UDP multicast transport for message streams (order book updates). Fixed 20-byte header: 10-byte session identifier, 8-byte big-endian sequence (first message in packet), 2-byte message count. Each message: 2-byte length field followed by data. Max message size theoretically 64KB but limited by MTU (1500 bytes typical) to avoid IP fragmentation. Redundancy: dual feeds ("A side" and "B side") provided by exchange; client subscribes both, uses A side by default, B side for gap fill on A side loss.

---

## 8. Market Data Dissemination

**Nasdaq TotalView ITCH 5.0** [S14]: Binary protocol for full order book dissemination. Message types (order lifecycle): Add Order (A/F, new order entry), Order Executed (E/C, partial or full fill), Order Cancel (X, cancellation), Order Delete (D, administrative removal), Order Replace (U, order modification with new quantity/price), Trade (P, non-book trade), System Events (trading halts, session open/close). Each order assigned day-unique Order Reference Number (4 bytes, non-repeating within session). All integers: unsigned big-endian network byte order. All alpha fields: left-justified, right-padded with spaces. Protocol carries complete order book depth (every resting order) and every execution (full audit trail).

**Coinbase Exchange WebSocket Level2** [S15]: Authenticated feed. Subscription flow: (1) Client subscribes to product, (2) Server sends snapshot message with full current L2 book (bids array: [price, size], asks array), (3) Server streams l2update messages (incremental changes). Batch mode (Level2_batch): 50-millisecond batching reduces message rate. Size field semantics: absolute (not delta). Size=0 means delete level. Coinbase guarantees delivery of all updates; no conflation.

**Snapshot + Incremental Delta Pattern**: Client maintains local L2 book: (1) Receive snapshot (full state), (2) Apply incremental l2update messages (each update has sequence number), (3) Detect gaps via sequence discontinuity, (4) On gap: reconnect and request new snapshot (restart). Efficiency: snapshot ~10KB per book, deltas ~100 bytes per update. Event-driven latency varies with market activity (fast markets = frequent updates).

**Conflation**: Exchange omits intermediate updates when processing rate exceeds client consumption. Example: levels update 5 times in 1ms, only latest state sent. Reduces bandwidth but loses transaction history. Direct feeds (full-tick, no conflation) available at cost premium; used by HFT. Conflation decision made at market data gateway, not exchange.

---

## 9. Post-Trade

**FIX Protocol Message Sequencing** [S16]: MsgSeqNum (tag 34) increments by 1 per message, starts at 1 on Logon message. Session-scoped (resets to 1 on reconnect). Receiver tracks NextNumIn (next expected sequence). Gap detection: receive MsgSeqNum=100 but expect 95 (gap: 95-99). Receiving side issues ResendRequest(35=2) for range. Sender retransmits messages in range with original MsgSeqNum preserved, sets PossDupFlag(43)=Y, OrigSendingTime(122) unchanged. Sender's SendingTime(52), CheckSum(10), BodyLength(9) updated for retransmitted message.

**Gap Fill Alternative**: SequenceReset message with GapFillFlag=123=Y. Skips replaying messages between sequences (for administrative/stale messages not worth resending). Example: collapse 10 heartbeats into single SequenceReset. Receiver advances NextNumIn without processing skipped messages.

**Execution Report Delivery** [S16]: Per FIX spec, sender queues ExecReport messages (35=8) for each execution event (fill, cancel, reject). Session-level idempotency via MsgSeqNum. Client resend recovery via ResendRequest after reconnect. Clearing house uses FIX for trade reporting.

**Trade Confirmation** [S17]: FINRA Rule 2232 and SEC Rule 10b-10 mandate customer confirmation at-or-before trade completion. Required fields: execution date and time, security identity, share/unit count, trading capacity (principal/agent), commission (if charged), mark-up/mark-down (debt securities), redemption/yield info (debt securities), SIPC protection status, payment-for-order-flow disclosure. Confirmation must be in writing or electronic form understood by customer.

**Settlement Ledger**: Double-entry pattern. Trade generates two journal entries: (1) Payer debit, Clearing House credit, (2) Clearing House debit, Receiver credit. Settlement T+1 or T+2 (typically 1-3 days post-trade). Central counterparty (CCP) interposes: eliminates direct counterparty risk, guarantees settlement via CCP default fund.

---

## 10. Sharding & Scale

**One-Instrument-One-Thread Pattern**: All incoming messages for a single instrument (e.g., AAPL order book) routed to one dedicated thread. No concurrent processing for same instrument. Horizontal scaling: add threads for additional instruments. Well-optimized matching loop achieves <10 microseconds per order, sustaining >100k ops/sec per trading pair. Rationale: single writer to instrument state eliminates atomic operations, locks, compare-and-swap overhead. CPU cache remains hot (working set fits in L1/L2). Branch prediction stable (same code path per order type). Trade-off: operational complexity (thread pooling, graceful shutdown, NUMA awareness on multi-socket systems).

**Cross-Symbol Orders Break Sharding**: Basket orders (execute simultaneously across multiple symbols) or spreads (buy symbol A, sell symbol B atomically) require coordination across shards. Solution: designate primary instrument shard as coordinator, two-phase commit across secondary shards. Complexity justifies avoiding baskets in real-time matching.

**CME Implied Spreads** [S18]: Listed spreads are synthetic instruments between two pre-defined contract legs. Implied quotes: system calculates spread bid/ask from resting outright leg bids/offers, enables automated arbitrage without explicit spread orders. Quantity ratio derived from DV01 (dollar value of 1 basis point move). Example: 2-Yr Treasury futures imply 10-Yr spread by DV01 ratio. Implementation: two separate order books (outright and spread) with cross-booking matching logic (resting outright leg can fill incoming implied spread order).

**Failover Architectures**: Active-active (both primary and standby operational, synchronized via consensus). Load distributed across both. Instant failover: remaining node becomes sole primary. Complexity: distributed state coordination (Raft consensus, higher latency ~2-6ms). Warm-standby (primary active, standby read-only, replicates from primary). Simpler operations. Failover: promote standby (seconds to minutes RTO). Risk: recent unlogged transactions lost if primary fails before log replication. For matching engines: active-active uses Raft replicated state machine (both apply same log, consensus before commit). Warm-standby replays primary log continuously; promotion with log tail ensures state match.

---

## Spot-Check List

Eight critical numbers most likely to appear in an interview solution or design document. Each includes source URL and exact quote.

**1. exchange-core 5M ops/sec** [S1]
"5,000,000 inbound messages per second on Xeon X5690 (released Feb 2011, 6-core). Test mix: 9% GTC, 3% IOC, 6% cancel, 82% move. Latencies: move 0.5µs mean, cancel 0.7µs, place 1.0µs."
Why: Establishes what's possible with proper architecture (ring buffer + ART + off-heap). Older hardware (2011) shows software dominates performance.

**2. LMAX Disruptor 52ns vs ArrayBlockingQueue 630x** [S8]
"Disruptor mean latency 52 nanoseconds vs ArrayBlockingQueue 32,757 nanoseconds on i7-2720QM. p99: Disruptor 128ns vs ABQ 2,097,152ns (16,383x). Lock-free ring buffer eliminates condition variable signaling overhead."
Why: Demonstrates lock-free > lock-based for latency percentiles. Ring buffer crucial for >1M orders/sec systems.

**3. Raft consensus 2-6ms single datacenter** [S9]
"3-node cluster commits at 2-6ms p50 latency (NVMe SSD, same AZ). Breakdown: leader fsync 0.2-2ms, network RTT 0.5-1ms, follower fsync 0.2-2ms. NVMe fsync is the bottleneck."
Why: Shows deterministic replay (core architecture) requires consensus cost. Identifies bottleneck for optimization.

**4. Solarflare ef_vi 3.967µs latency** [S12]
"Minimum latency 3.967 microseconds back-to-back 10GbE adapters, 4.408µs over switch (64-byte packets). User-space API with kernel bypass eliminates system call overhead compared to kernel TCP stack (10-100x slower)."
Why: Kernel bypass necessary for sub-10µs network latency. Cost: requires driver support, CAP_PERFMON capability.

**5. DPDK 148M packets/sec** [S11]
"148 million packets per second at 64 bytes per packet. Layer 3 forwarding >80 MPPS. Strategy: burst processing amortizes per-packet costs."
Why: Shows DPDK throughput ceiling. Market data fan-out application, not order entry (latency-sensitive).

**6. exchange-core p99 latency 4µs** [S1]
"At 1M ops/sec, p99 latency 4 microseconds, p99.9 22µs, worst case 45µs. Tail latency from cache misses and context switching under load."
Why: Distinguishes mean (0.5µs) from percentiles. Tail latency matters for customer SLOs.

**7. MoldUDP64 20-byte header** [S13]
"Fixed 20-byte header per packet: 10-byte session identifier, 8-byte big-endian sequence number (first message), 2-byte message count. Each message: 2-byte length field followed by data."
Why: Protocol detail necessary to design market data dissemination (multiple messages per UDP packet).

**8. MOO entry window 7:30am-9:28am ET** [S6]
"Market on Open: entry/cancel window 7:30am to 9:28:00am ET. Execution at Nasdaq Opening Cross (single price). Market on Close: cutoff 3:55pm ET, execution at Closing Cross price. Orders accumulate on separate auction book (not continuous)."
Why: Auction mechanics differ from continuous matching. Separate book means no interaction with day session orders.

**9. CME pro-rata TOP rule** [S4]
"Only one buy order and one sell order per price can hold TOP (Time-Priority Orders) status. TOP orders match first regardless of size. Remaining incoming quantity allocated pro-rata among non-TOP orders."
Why: Balances fairness (pro-rata) with incentive for best-priced orders (TOP gets priority). Avoids starvation at one price level.

**10. exchange-core worst case 45µs** [S1]
"Worst case latency 45 microseconds at 1M ops/sec. Typical case (p50) 0.5µs. Difference due to cache misses when L1/L2 cache full, CPU context switching, branch misprediction. Demonstrates when optimization hit limits."
Why: Shows importance of percentile specification. Worst case 45µs acceptable for batch matching, not for single-order HFT.

---

## Key Staff-Level Trade-Offs for Interview

**Memory vs Latency**: Pre-allocate order pools (waste memory, sub-microsecond latency) vs lazy allocation (save memory, microsecond+ latencies, GC pauses). Exchange matching requires pre-allocation. Broker risk checks can tolerate allocation.

**One-Thread-Per-Instrument Scaling**: Single thread per symbol achieves <10µs per order, no locks. But CPU-bound at 100k+ orders/sec per core. Multi-threaded matching (shared book, lock per price level) adds synchronization overhead, but scales across cores. Trade-off: simplicity vs scalability.

**Consensus Latency**: Raft deterministic replay requires 2-6ms commit. Warm-standby (secondary replays asynchronously) risks losing recent transactions but faster promotion. Active-active (full synchronization) safer but higher latency.

**Market Data Conflation**: Omit intermediate updates during spikes (save bandwidth, lose history). Direct feeds (full tick) available at cost premium for HFT. Retail consumers tolerate conflation.

**Kernel Bypass Cost**: ef_vi / DPDK achieve 3.967µs latency but require CAP_PERFMON, hardware support, no kernel scheduling. Kernel TCP achieves 1-10ms but works everywhere, more operational overhead.

**Buying Power Hold Semantics**: Reserve funds per order (prevents over-commitment) vs check at order entry (fails on concurrent orders, retry complexity). Hold pattern essential for atomic guarantees.

---

## Implementation Patterns Recurring Across Mechanisms

**Pre-Allocated Pools**: Exchange-core, Liquibook, and industrial systems all pre-allocate order structures (64-128 bytes each). Reuse via free lists instead of garbage collection. Eliminates allocation latency on hot path. Cost: memory footprint (thousands to millions of pre-allocated orders).

**Hash Map for Order Lookup**: Order ID to node pointer in hash table. Enables O(1) cancel given order ID (no search). LMAX Disruptor + open-addressing hash map typical. Intrusive pointers (node carries next/prev) eliminate extra allocation.

**Array + Bitmap for Price Levels**: Many systems use dense array indexed by price tick, bitmap for occupied levels. Skip list or red-black tree fallback for out-of-range prices. Trades bounded space for O(1) lookup within range.

**FIFO Within Price Level**: Intrusive doubly-linked list at each price level. New orders append to tail, matching walks from head. Preserves FIFO semantics without copy overhead.

**Sequence Numbers Everywhere**: FIX uses MsgSeqNum. Market data (ITCH, Coinbase WebSocket) includes sequence in every message. Enables gap detection and audit trail reconstruction. Deterministic replay via append-only log + sequence numbers.

**Dual Feeds for Reliability**: MoldUDP64 A side and B side for redundancy (UDP packet loss tolerated). Market data, not order entry (order entry requires TCP reliability).

**Separate Gateway for Risk Checks**: Pre-trade validation (risk, regulatory) handled by gateway before matcher. Matcher assumes all inputs valid. Separation of concerns: risk is stateful, matcher is deterministic.

---

## Spot-check corrections (added after fetching primary sources, 2026-09-13)

| Claim in survey | Check | Use in solution.md |
|---|---|---|
| exchange-core "5 M ops/s, p50 0.5 us, p99 4 us, worst 45 us at 1 M ops/s" [S1] | README fetched. The 5 M ops/s row reads p50 1.5 us, p90 9.5 us, p95 16 us, p99 42 us, p99.9 150 us, worst 190 us, on dual X5690 (2011). The 0.5 / 4 / 45 us figures are the 1 M ops/s row. Order mix quote is exact (9% GTC, 3% IOC, 6% cancel, 82% move, ~6% trigger trades). Test book: ~1,000 active orders over ~750 price slots | Quote both rows. The lesson is that tail latency grows with load; size the shard at 20 to 25% of the ceiling |
| LMAX Disruptor 52 ns vs 32,757 ns, p99 128 ns vs 2,097,152 ns [S8] | Technical paper fetched, Table 4, exact. Unicast 1P-1C throughput: 25,998,336 ops/s Disruptor vs 5,339,256 ABQ | Use as-is |
| "Raft 3-node commits at 2 to 6 ms p50, leader fsync 0.2 to 2 ms" attributed to the Raft paper [S9] | Not in the paper. The paper has no NVMe latency table. This is an invented breakdown | Do not use. Own estimate: in-rack RTT 20 to 50 us with kernel bypass, 100 to 200 us with kernel TCP; enterprise NVMe fsync with power-loss protection 20 to 100 us; so a 2-of-3 memory-replicated commit with asynchronous group fsync is ~50 to 150 us, and a fsync-before-ack commit is ~200 to 500 us. Nasdaq INET's 37 us average round trip (SIX measurement) shows the whole path can be tens of microseconds |
| FIX "MsgSeqNum resets to 1 on reconnect" [S16] | Wrong. Sequence numbers persist across reconnects within a session (typically a trading day); that persistence is what makes `ResendRequest` after reconnect work. They reset at session start or by explicit `SequenceReset` / `ResetSeqNumFlag=Y` on `Logon` | Use "reset daily, persist across reconnects" |
| "One-instrument-one-thread sustains > 100 k ops/s per pair, < 10 us per order" (§10) | No source. Consistent with exchange-core (1 to 5 M ops/s on one book) and LMAX (6 M/s) but understated | Use 1 to 5 M msg/s per core as the ceiling, with the exchange-core rows as evidence |
| "Solution: two-phase commit across shards for baskets" (§10) | No source, and not what exchanges do. CME uses implied spreads with dedicated spread books [S18]; equity exchanges do not offer atomic baskets at all | Say "not built; CME implied spreads are the seam" |
| MoldUDP64 header 20 bytes, session 10 B, seq 8 B, count 2 B [S13] | Matches the spec | Use as-is |
| Coinbase `level2` snapshot then `l2update`, `level2_batch` at 50 ms [S15] | Matches the docs | Use as-is |
