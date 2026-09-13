# Stock Trading / Order Execution System: Interview Framing Survey

How this system design question is asked, graded, and what numbers interviewers expect.

---

## Sources Reference Table

| ID | URL | Establishes |
|---|---|---|
| SDH-Exchange | https://www.systemdesignhandbook.com/guides/design-a-stock-exchange-system/ | Scale (1B orders/day, 10k-50k avg QPS, 100k peak), latency targets, consistency model, architecture |
| ByteByteGo-LL | https://blog.bytebytego.com/p/low-latency-stock-exchange | Microsecond latency, single-threaded matching, shared memory, mmap, no containers |
| HI-Robinhood | https://www.hellointerview.com/learn/system-design/problem-breakdowns/robinhood | FRs, NFRs, external exchange integration, what's out of scope |
| PracHub-Crypto | https://prachub.com/interview-questions/design-crypto-trading-system | Exact interview question wording, seven core requirements, what interviewers value |
| GitHub-WY | https://github.com/wuyichen24/system-design-interview/blob/master/problems/finance/Stock_Exchange_System.md | Architecture components: gateway, order manager, sequencer, matching engine |
| DevTo-Matching | https://dev.to/matt_frank_usa/designing-a-stock-exchange-order-matching-engine-759 | Performance targets: millions/sec, microseconds matter, 10-100x burst multiplier |
| DataBento-OPRA | https://databento.com/blog/beyond-40-gbps-processing-opra-in-real-time | 200B OPRA updates/day, 50+ Gbps peak, 80% NBBO-irrelevant updates |
| DataBento-ITCH | https://databento.com/datasets/XNAS.ITCH | Nasdaq TotalView latency: 42μs (cross-connect), 590μs (internet), 90th percentile |
| DataBento-STAC | https://databento.com/microstructure/opra | STAC-M1 mean 1.4μs, P999 2.8μs latency benchmark |
| Citadel-Dev | https://dev.to/net_programhelp_e160eef28/citadel-swe-interview-experience-order-book-design-in-depth-behavioral-interview-3hb0 | Order book LLD: BBO, NBBO, O(logN) insertion, O(1) query |
| JaneStreet-GD | https://www.glassdoor.ca/Interview/design-the-message-system-between-trading-company-and-the-exchange-for-order-book-how-many-message-types-are-there-and-wha-QTN_6083192.htm | Message system design for exchange integration |
| HFT-Engine | https://dev.to/c0sbyy/how-i-built-an-hft-matching-engine-and-all-the-things-i-got-wrong-e23 | 2.57M orders/sec, P99 900ns, P999 3.4μs; floating-point dangers, intrusive lists, callback templates |
| SDH-Robinhood | https://www.systemdesignhandbook.com/guides/robinhood-system-design-interview/ | NFRs: sub-second latency, millions concurrent, strong consistency over availability |
| SDH-Coinbase | https://www.systemdesignhandbook.com/guides/coinbase-system-design-interview/ | Sub-50ms latency, high uptime during volatility, in-memory order books, streaming pipelines |
| DesignGurus-QA | https://www.designgurus.io/blog/system-design-interview-questions | Grading bar: correctness over performance, "mostly correct is not acceptable" |
| FINRA-Snapshot | https://www.finra.org/media-center/reports-studies/2025-industry-snapshot | 634k registered reps, 3249 firms (2024), 82% at large firms |

---

## 1. Prompt Variants and Who Asks Them

**"Design a stock exchange" / "Design an order matching engine"**
- Asked by: Google, Coinbase, Citadel, Jane Street, HFT firms
- SystemDesignHandbook frames it as: "mid-sized exchange handles roughly one billion orders per day across a hundred actively traded symbols" [SDH-Exchange]
- Core question from Citadel: "Given order information including exchange_id, price, quantity, and order_type (bid/ask), design an order book structure" [Citadel-Dev]
- Jane Street variant: "Design the message system between trading company and the exchange for order book. How many message types are there and what information should each message type contain?" [JaneStreet-GD]

**"Design Robinhood / a brokerage"**
- Hello Interview has a prominent "Design Robinhood" article. FRs: "Users can see live prices of stocks" and "Users can manage orders for stocks (market/limit orders, create/cancel orders)" [HI-Robinhood]
- Out of scope per Hello Interview: trading outside market hours, ETFs, options, cryptocurrency, real-time order book viewing [HI-Robinhood]
- SystemDesignHandbook also covers "Robinhood System Design Interview" with NFRs: "sub-second latency" for order execution and market data propagation [SDH-Robinhood]

**"Design a trading platform / order execution system with async external exchange"**
- PracHub exact wording: "Design a cryptocurrency trading platform that routes client orders to one or more third-party exchanges that expose a (nominally) synchronous HTTP order/cancel API. Even though the venue API looks synchronous, fills and cancellations are effectively asynchronous and arrive later via polling, webhooks, or streams" [PracHub-Crypto]
- This variant emphasizes failure handling and eventual consistency
- Asked at Databricks, Robinhood, and crypto exchanges [reported across sources]

---

## 2. Architecture and Scale Reference (SystemDesignHandbook / ByteByteGo)

**Scale metrics**
- "Mid-sized exchange handles roughly one billion orders per day across a hundred actively traded symbols" [SDH-Exchange]
- "Approximately 10,000 to 50,000 orders per second during normal operation" [SDH-Exchange]
- "Peak loads during market open potentially reaching 100,000 orders per second or higher" [SDH-Exchange]
- "Microsecond latency performance" is critical [ByteByteGo-LL]

**Architecture components (Alex Xu equivalent)**
- Client Gateway: authentication, validation, rate limiting, FIXT protocol support [GitHub-WY]
- Order Manager: risk checks, wallet verification, funds confirmation, execution routing [GitHub-WY]
- Sequencer: "Assigns sequence IDs to inbound orders and outbound executions for ordering guarantee" [GitHub-WY]
- Matching Engine: "Maintains order books per symbol, matches buy/sell orders" [GitHub-WY]
- Market Data Publisher: distributes fills and market updates [GitHub-WY]

**Performance design**
- ByteByteGo: "Deploy all the components in a single giant server (no containers), pin critical components to dedicated CPUs with no locks, use shared memory as an event bus to communicate among the components, no hard disk" [ByteByteGo-LL]
- Single-threaded application loop to avoid lock contention [ByteByteGo-LL]
- Event sourcing for deterministic replay [ByteByteGo-LL]
- Write-ahead logging for durability [SDH-Exchange]

---

## 3. Hello Interview "Design Robinhood" Details

**Functional requirements**
- See live prices of stocks (market data push to millions of users)
- Manage orders: place market/limit orders, cancel orders, view order history [HI-Robinhood]

**Non-functional requirements**
- "Sub-second latency" for order execution and market data propagation [SDH-Robinhood]
- Millions of trades and live market data updates across millions of concurrent users [SDH-Robinhood]
- Strong consistency for financial transactions (ACID required) [SDH-Robinhood]
- Remain operational during outages or high traffic [SDH-Robinhood]

**Architecture trade-offs Hello Interview emphasizes**
- "Consistency over Availability: prioritize correctness here since financial data errors can directly impact user balances" [SDH-Robinhood]
- For live prices to millions: in-memory cache (Redis) + websocket fan-out, NOT polling [SDH-Robinhood]
- For placing order with external exchange: asynchronous confirmation flow, idempotent client retry on ClOrdID [PracHub-Crypto]
- For order status consistency: synchronize via exchange callback + periodic reconciliation [PracHub-Crypto]

**External exchange integration**
- API looks synchronous (HTTP), but fills/cancellations arrive asynchronously via polling/webhooks/streams [PracHub-Crypto]
- Must handle timeouts, partial fills, stale responses, exchange downtime [PracHub-Crypto]

---

## 4. Interviewer Follow-Up Ladder

**Tier 1: Basic order flow (expected at any level)**
- How do you guarantee FIFO fairness when two orders arrive at the same microsecond? [SDH-Exchange]
- What is NBBO and why does it matter? [Citadel-Dev asks for BBO and NBBO in LLD]

**Tier 2: Failure and consistency (Senior+ must answer)**
- Matcher crashes after matching but before publishing fill to both sides. Recovery? [ByteByteGo-LL]
- Duplicate order submission on client retry. How do you prevent double-execution? [PracHub-Crypto, SDH-Exchange both probe idempotency]
- Client cancels an order that is being filled at the same instant. Which wins? [SDH-Exchange]
- Exchange confirms fill, but our DB write fails. What is the customer told? [Idempotency via ClOrdID resync]

**Tier 3: Scale and burst (Staff+ must address)**
- Market open burst: 10x to 100x normal volume. Does your design survive? [DevTo-Matching]
- One symbol is 40% of volume (concentration risk). Bottleneck per symbol? [Implied in single-threaded design]
- 200 billion OPRA updates per day, 50+ Gbps peak bursts. Can market data system handle it? [DataBento-OPRA]

**Tier 4: Operational and regulatory (Staff must cover)**
- Regulator asks for every event for order X from 3 years ago. Audit trail? [SystemDesignHandbook emphasizes immutable logs]
- How do you test a matcher for determinism and replay-safety? [ByteByteGo-LL, HFT-Engine]
- Deploy a new matcher version without stopping trading. Hot-swap strategy? [ByteByteGo-LL hot-warm failover]

---

## 5. Common Mistakes Graders Call Out

**Architectural**
- Using a distributed database with pessimistic locks as the order book [SDH-Exchange: "strong consistency with deterministic ordering" must be local]
- Not distinguishing "order accepted" vs. "order filled" vs. "trade settled" [PracHub-Crypto: state machine must be explicit]
- Putting risk checks after matching instead of before [GitHub-WY: risk checks in Order Manager, before sequencer]
- Claiming "just use Kafka" as sequencer without saying why a single partition per symbol is critical [ByteByteGo-LL: sequencer IS the log]

**Implementation**
- Using floating-point arithmetic for money [HFT-Engine: "Never use floating point for money" (IEEE 754 precision)]
- Forgetting idempotency on ClOrdID, allowing duplicate fills [PracHub-Crypto: required for retry safety]
- std::map order book instead of flat vector or intrusive linked list [HFT-Engine: flat arrays 1.6x faster than std::map]
- Fake benchmarks: claiming performance without touching the hot path [HFT-Engine: "Fake benchmark: Initial test was a for loop that multiplies by 2"]

**Operational**
- Missing immutable audit log for regulatory compliance [GitHub-WY, SystemDesignHandbook]
- Claiming active-active multi-region matching (breaks FIFO fairness) [ByteByteGo-LL: single-threaded, single-region]
- Not accounting for NBBO-irrelevant updates: 80% of OPRA can be filtered [DataBento-OPRA]

---

## 6. Expected Numbers (No Invention)

All candidates should cite these without prompting:

- 1 billion orders per day (mid-size exchange) [SDH-Exchange]
- 10,000 to 50,000 orders per second average [SDH-Exchange]
- 100,000+ orders per second during market open [SDH-Exchange]
- 250 microseconds latency target (NASDAQ-grade) [SDH-Exchange]
- 42 microseconds latency (Nasdaq TotalView, 90th percentile, cross-connect) [DataBento-ITCH]
- 590 microseconds latency (Nasdaq TotalView, 90th percentile, over internet) [DataBento-ITCH]
- 200 billion OPRA quote updates per day [DataBento-OPRA]
- 50+ Gigabits per second peak burst (OPRA) [DataBento-OPRA]
- 80% of OPRA updates don't change NBBO (optimization opportunity) [DataBento-OPRA]
- 2.57 million orders per second (HFT benchmark achieved) [HFT-Engine]
- P99 latency 900 nanoseconds (HFT) [HFT-Engine]
- P999 latency 3.4 microseconds (HFT) [HFT-Engine]

---

## 7. Level Calibration

**Mid-level answer** [DesignGurus-QA]
- Designs a basic matching engine with an order book per symbol
- Handles normal volume OK
- Latency in low milliseconds
- Mentions "strong consistency" but implementation is vague

**Senior-level answer** [DesignGurus-QA, SDH-Exchange]
- Addresses the critical path: sequencer + single-threaded matcher
- Explains write-ahead logging for durability
- Discusses FIFO fairness and why distributed locks won't work
- Can trace what happens when exchange downtime occurs
- Numbers: "10k QPS normal, 100k+ peak"

**Staff-level answer** [SystemDesignHandbook, DesignGurus]
- Names the failure mode: "matcher crash after matching but before publish"
- Proposes idempotency via ClOrdID and event sourcing replay
- Explains shared memory and mmap for sub-microsecond IPC
- Discusses hot-warm failover without stopping trading
- Addresses audit log and regulatory compliance proactively
- Calibrates performance: "microseconds for matching, milliseconds for network"
- Cites actual benchmarks: "200B OPRA/day, 50+ Gbps peak, yet 80% NBBO-irrelevant"

---

## 8. Coinbase Specifics

**Published requirements** [SDH-Coinbase]
- Sub-50 millisecond order execution
- Millions of orders and trades daily
- Extremely high uptime during volatility
- Multi-signature authorization, restricted access

**Architecture details** [SDH-Coinbase]
- In-memory order books (not on disk)
- Streaming pipelines (Kafka/Flink) for processing
- Real-time validation of orders
- Hot wallet security out of scope (focus on trading, not custody)

**What interviewers probe** [SDH-Coinbase, Glassdoor reports]
- Cryptocurrency-specific: what is a "fill" when prices move during matching?
- Multi-exchange routing: how do you route USD orders vs. coin pairs?
- Volatility spike: system behavior when spread widens 10x in one second

---

## Spot-Check List

These 10 numbers are most likely to end up in a solution. Verify with a source:

1. **1 billion orders per day**
   - Source: [SDH-Exchange]
   - Quote: "mid-sized exchange handles roughly one billion orders per day across a hundred actively traded symbols"

2. **10,000 to 50,000 average QPS**
   - Source: [SDH-Exchange]
   - Quote: "approximately 10,000 to 50,000 orders per second during normal operation"

3. **100,000+ peak QPS**
   - Source: [SDH-Exchange]
   - Quote: "peak loads during market open potentially reaching 100,000 orders per second or higher"

4. **250 microseconds latency (NASDAQ target)**
   - Source: [SDH-Exchange]
   - Quote: "NASDAQ targets <250μs"

5. **42 microseconds (Nasdaq TotalView cross-connect, 90th percentile)**
   - Source: [DataBento-ITCH]
   - Quote: "90th percentile latency for Nasdaq TotalView-ITCH data is 42 microseconds via cross-connect"

6. **200 billion OPRA updates per day**
   - Source: [DataBento-OPRA]
   - Quote: "200 billion regional quotes and NBBO updates per day"

7. **50+ Gbps OPRA peak burst**
   - Source: [DataBento-OPRA]
   - Quote: "Peak bursts exceeding 50 Gbps"

8. **2.57 million orders per second (HFT benchmark)**
   - Source: [HFT-Engine]
   - Quote: "Target: 2.7 million orders/second. Achieved: 2.57M/s"

9. **P99 latency 900 nanoseconds (HFT)**
   - Source: [HFT-Engine]
   - Quote: "P99 latency: 900ns"

10. **Sub-50 millisecond execution (Coinbase target)**
    - Source: [SDH-Coinbase]
    - Quote: "Sub-50 millisecond order execution"

---

## Spot-check corrections (added after fetching primary sources, 2026-09-13)

| Claim in survey | Check | Use in solution.md |
|---|---|---|
| "250 microseconds latency target (NASDAQ-grade)" [SDH-Exchange] | SDH's own sentence is "Major exchanges like NASDAQ target order acknowledgment times under 250 microseconds." It is SDH's number, not Nasdaq's. Nasdaq's product page says sub-40 us matching with the fastest production deployment at 14 us door-to-door: https://www.nasdaq.com/products/fintech/eqlipse/trading-technology/exchange-matching. SIX (X-stream INET) measured 37 us average round trip at the exchange network boundary: https://www.six-group.com/dam/download/the-swiss-stock-exchange/trading/trading-platform/x-stream-inet-performance-measurement-details.pdf | Use "tens of microseconds, sub-40 us on INET-class engines". Do not quote 250 us as a Nasdaq figure |
| 1 B orders/day, 10 k to 50 k avg, 100 k+ peak [SDH-Exchange] | Fetched, quotes are exact. Note 1 B / 23,400 s (6.5 h) = 42.7 k/s, which sits inside their range. Their "100 k or higher" peak is only 2.3x average; real opens are worse, and SDH itself says "provision for 10x normal peak" and "March 2020 volumes were 5 to 6x historical peaks" | Use 43 k/s avg, size for 500 k/s peak (about 10x) |
| 42 us / 590 us Nasdaq TotalView 90th percentile [DataBento-ITCH] | Fetched, exact: "90th percentile latency up to your application at 42 microseconds (cross-connect) or 590 microseconds (internet)". This is a data vendor's delivery latency for market data, not the exchange's matching latency | Use only as a market data delivery figure |
| Hello Interview Robinhood NFR numbers | The page is paywalled past the FRs. FRs and out-of-scope list are confirmed. Deep dive headings confirmed: "How can the system scale up live price updates?", "How does the system track order updates?", "How does the system manage order consistency?" | Use the FRs and the three deep-dive questions; do not cite numbers from it |
| Alex Xu Vol 2 chapter 13 | Not fetched by the agent. From the book (own knowledge, consistent with SDH which paraphrases it): 100 symbols, 1 B orders/day, 6.5 h session, ~43 k QPS average, peak assumed 5x. Components: client gateway, order manager, sequencer, matching engine, market data publisher, reporter. Critical path on one server, application loop, mmap event store, hot-warm matching engines behind the sequencer | Use as the "reference answer" the interviewer likely holds |
| Databricks-specific reports | The agent found none with the exact Databricks wording. The `hld/README.md` aggregation lists "trading system" and "game transactions" among Databricks prompts; treat the Databricks version as the generic prompt with heavy emphasis on idempotency, ordering, and "where is the transaction" | Frame §1 around those three probes |
| Sources hygiene | Two dev.to posts were used (HFT-Engine, Citadel-Dev, DevTo-Matching). The 2.57 M orders/s and 900 ns p99 numbers are one hobbyist's benchmark, not a production figure | Do not use them as production numbers. Use exchange-core's published benchmark and LMAX's 6 M/s instead (see mechanisms survey) |
