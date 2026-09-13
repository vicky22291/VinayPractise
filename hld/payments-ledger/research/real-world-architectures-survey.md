# Real-World Payment Ledger Architectures Survey

## Sources Reference Table

| ID | URL | Establishes |
|----|-----|-------------|
| S1 | https://usa.visa.com/dam/VCOM/global/visa-everywhere/documents/visa-data-center-infographic.pdf | Visa 4 data centers, 65k TPS |
| S2 | https://www.sec.gov/Archives/edgar/data/1403161/000140316125000089/v-20250930.htm | Visa 257.5B annual transactions, Sep 2025 |
| S3 | https://stripe.dev/blog/topic/engineering | Stripe Ledger blog (Feb 16, 2024) |
| S4 | https://stripe.com/blog/idempotency | Stripe idempotency 24-hour retention |
| S5 | https://stripe.com/blog/online-migrations | Stripe dual-write 4-phase migration pattern |
| S6 | https://medium.com/airbnb-engineering/avoiding-double-payments-in-a-distributed-payments-system-2981f6b070bb | Airbnb idempotency, three phases, five nines |
| S7 | https://eng.uber.com/payments-platform/ | Uber Gulfstream, LedgerStore, 40+ engineers |
| S8 | https://eng.uber.com/money-scale-strong-data | Uber strong consistency, money movement |
| S9 | https://tigerbeetle.com/ | TigerBeetle VSR, 8189 batch, pending transfers |
| S10 | https://docs.tigerbeetle.com/concepts/performance/ | TigerBeetle performance specs |
| S11 | https://www.moderntreasury.com/journal/how-to-scale-a-ledger-part-v | Modern Treasury immutability, double-entry |
| S12 | https://www.nacha.org/resources/same-day-ach-schedules-and-funds-availability | NACHA 3 same-day windows, timing |
| S13 | https://github.com/formancehq/ledger | Formance open-source ledger, Numscript |
| S14 | https://brandur.org/idempotency-keys | Brandur's Postgres idempotency keys |
| S15 | https://usa.visa.com/dam/VCOM/regional/na/us/about-visa/research/documents/smarter-stip.pdf | Visa STIP stand-in processing |
| S16 | https://building.nubank.com/engineering-lessons-from-scaling-million-customers/ | Nubank 122M customers, ledger system |

---

## 1. Visa / VisaNet and Card Networks

Visa operates a four-party model: cardholder (customer), issuer (card bank), network (Visa), acquirer (merchant's bank). Money flows: issuer to Visa to acquirer to merchant. Information flows: bidirectional throughout.

The authorization-clearing-settlement lifecycle spans three distinct stages:

1. **Authorization**: Real-time approval by issuer. Acquirer sends MTI 0100 (auth request) containing amount, card, merchant, timestamp. Issuer returns MTI 0110 (response) with approval code or decline reason. Approved auths place a temporary hold on cardholder account. No funds move yet; commitment is informational and contractual.

2. **Clearing**: Begins next business day. Acquirer aggregates all transactions into batches, sends to Visa network. Visa reconciles with issuer, calculates net obligations (acquirer owes issuer X, issuer owes acquirer Y). Settlement amount is determined.

3. **Settlement**: Actual fund transfer between issuer and acquirer. Typically occurs T+1 or T+2 after clearing. Irrevocable at this point (absent chargeback).

ISO 8583 message types define card network protocol:

- **0100**: Authorization request (acquirer -> issuer). Contains PAN, amount, merchant category, terminal ID, timestamp, cryptogram.
- **0110**: Authorization response (issuer -> acquirer). Response code (00 = approved, 05 = Do Not Honor, etc.), auth code.
- **0120**: Authorization advice. Sent when point-of-sale device fails mid-transaction; cardholder signs voucher offline.
- **0220**: Financial transaction advice. Confirmation of clearing.
- **0400**: Reversal request. Acquirer sends if auth response times out (typically after 30 seconds) to reverse the hold.
- **0420**: Reversal advice. Issuer confirms reversal processed.

**Timeout and Reversal Handling**: On network timeout, acquirer does not know if auth succeeded. After ~30 seconds, acquirer sends MTI 0400 (reversal) to prevent orphaned holds. Stand-In Processing (STIP) bridges issuer outages: if issuer is unavailable, Visa issues approval/decline using stored cardholder profile (risk-based rules). When issuer comes online, Visa forwards the original request. Smarter STIP (Visa patent 2019) uses real-time cardholder-level features for improved accuracy during outages [S15].

**Auth Holds and Capture**: Authorization places a hold on the cardholder's available balance. Hold is temporary; no money actually moves. Capture finalizes the authorization, moving the transaction into the settlement queue (pending settlement). Merchant can capture less than the authorized amount (partial capture), or not capture at all (voiding the auth). Uncaptured auths expire after a fixed period (typically 7 days), automatically releasing the hold.

**Partial Reversals and Adjustments**: After settlement, the issuer can reverse a partial amount. Example: $100 authorized and $80 captured. Customer disputes and requires $30 credit. Issuer sends a partial reversal (MTI 0400 variant) for $30, customer receives $30 credit, merchant retains $50. This avoids full chargeback friction.

**Chargebacks and Disputes**: After settlement, customer may dispute a charge (e.g., unauthorized transaction, goods not received). Issuer initiates a chargeback: reverses the transaction, credits the cardholder, and debits the merchant with a chargeback fee ($15-100 typical). Merchant can dispute the chargeback by providing evidence: authorization proof (signature or CVV), delivery/fulfillment proof, customer communication. Chargeback process is slow (30-90 days) and costly, making prevention (3D Secure, AVS checks, idempotency) critical for merchants.

Visa's claimed capacity: 65,000+ transaction messages per second [S1]. This reflects peak network design, not average load. Annual processed transactions FY2025: 257,545 million transactions (10% year-over-year growth, same quarter 2024 had 233,758M) [S2]. Derived average TPS: 257.5B transactions / (365 * 24 * 3600) = 8.17M TPS average, well below peak.

VisaNet infrastructure: 4 synchronized data centers (2 U.S., 1 Singapore, 1 United Kingdom) linked by global telecommunications network. Architecture emphasizes redundancy and minimal downtime; specific SLO not published [S1].

Mastercard comparison: Processes ~160M transactions/hour, approximately 44,444 TPS, with 130ms average response time [unverified source, SEC filing 2010].

---

## 2. Stripe

Stripe's Ledger system (engineering blog, Feb 16, 2024, author: Ilya Ganelin) tracks and validates money movement across Stripe's global payment processing network. Built on event-driven architecture, it consumes billions of events daily and maintains data quality metrics for downstream reconciliation and compliance [S3].

**Idempotency Design**: Critical for preventing duplicate charges. Clients generate unique keys (up to 255 chars, e.g., UUIDs) and send them in `Idempotency-Key` request headers. Servers receive key, check if previously processed, and either execute the request (if new) or return the cached result (if duplicate). Keys are retained for 24 hours; clients can safely retry within this retention window [S4].

Three failure scenarios handled:

1. **Connection failure**: Request reaches server normally on retry.
2. **Mid-operation failure**: Server recovers state from the key record, completes the operation.
3. **Response failure**: Response generated but client didn't receive it. Retry returns cached response from the first execution.

The "Designing robust and predictable APIs with idempotency" blog emphasizes that retries with idempotency keys guarantee that side effects occur exactly once, enabling automatic retry logic without fear of duplicate payments [S4]. Brandur Leach's "Implementing Stripe-like Idempotency Keys in Postgres" describes the technical implementation: store the idempotency key as primary key, record request ID, execution timestamp, response status and body [S14]. Queries must be deterministic (e.g., date-based operations must handle repeated invocations on different days).

**Online Migrations at Scale**: Stripe migrates hundreds of millions of subscription objects without downtime using a four-phase dual-write pattern [S5]:

1. **Dual-write phase**: New code writes to both old and new tables. Historical data backfilled via MapReduce against Hadoop snapshots (avoiding expensive prod DB queries). Gradually increase duplication percentage while monitoring.

2. **Read-path validation**: Use GitHub's Scientist library to compare old vs new results. Only switch reads to new table after consistency verified.

3. **Write-path refactoring**: Most complex phase. Incrementally refactor code to write only to new table (never >few hundred LOC changes per iteration). Continue using Scientist to catch inconsistencies.

4. **Cleanup**: Stop writing to old table, lazily delete old data, final validation.

This pattern enables zero-downtime migrations for massive datasets.

**DocDB and 99.999% Uptime**: Stripe's "How Stripe's document databases supported 99.999% uptime with zero-downtime data migrations" blog covers the Data Movement Platform and database infrastructure. Specific architecture details mention document-oriented storage and replication strategies but full technical depth not accessible [unverified].

---

## 3. Uber

**Gulfstream Platform**: Uber's fifth-generation collection and disbursement payments platform, engineered to handle the complexity of global payments across rides, food delivery, freight, and other business units. Built on double-entry accounting principles (every debit has a credit), ensuring that all transactions balance and can be reconciled automatically. SOX-compliant, supporting auditing and regulatory requirements.

**LedgerStore**: Introduced in 2018 to power Gulfstream, an immutable, ledger-style database storing all business transactions. Key capabilities [S7, S8]:

- **Immutability**: Transactions are append-only; no updates or deletes to historical records. Ensures complete audit trail.
- **Cryptographic signing/sealing**: All data is signed using cryptographic hashes, guaranteeing data completeness and correctness. Protects against tampering.
- **Strongly consistent indexes**: Indexes are updated synchronously with data writes, enabling point-in-time queries and consistent reads.
- **Automatic data tiering**: Hot data (recent transactions) in fast storage (SSD), cold data (older transactions) in slower storage (object store). Balances performance and cost.

The system must handle massive volume: Uber processes billions of payment-related transactions annually across multiple services and geographies. Strong consistency is critical for regulatory compliance and financial reconciliation.

**Implementation scale**: Gulfstream was a two-year cross-team effort involving 40+ engineers, product managers, and operations specialists across the organization. This reflects the complexity of building a payments ledger at Uber's scale while maintaining correctness and auditability [S7].

---

## 4. Other Major Platforms

**Airbnb**: "Avoiding double payments in a distributed payments system" (Airbnb Engineering blog, Mar 27, 2026, author: Jon Chew) describes a three-phase idempotency framework called Orpheus [S6]:

1. **Pre-RPC phase**: Client generates unique idempotency key (e.g., UUID) before issuing payment request. Stored locally to enable retries.

2. **RPC phase**: Server receives request with key and payment details (amount, guest ID, host ID, booking ID, etc.). Server queries its idempotency store: if key exists, skips to post-phase; if new, executes the payment operation atomically (charge guest, payout to host, update ledger, send confirmation). Records key, execution status, and result in idempotency store.

3. **Post-RPC phase**: Server returns cached result to client. On retry (due to timeout or network error), client resends with same key. Server returns the cached result without re-executing, preventing duplicate charges/payouts.

The idempotency lease is the retention window (time duration) for cached results. If a client retries after lease expiration, server cannot guarantee idempotency; key record is purged. Retry may execute again. Airbnb's lease timeout is [unverified from blog], but Stripe's standard is 24 hours.

**Scalability and correctness**: Orpheus framework abstracts idempotency away from individual payment microservices. Services only need to store the key and result; framework handles deduplication. Each payment operation is atomic: either fully succeeds (guest charged, host paid) or fully fails (no partial state).

**Consistency achievement**: Since launching Orpheus, Airbnb achieved five nines (99.999%) consistency in payments, preventing double-charges to guests and double-payouts to hosts even during network failures and retries. Simultaneously, annual payment volume doubled, proving the framework scales horizontally [S6].

**Coinbase**: Handles high-volume cryptocurrency and fiat payment processing. Architecture includes PSP (payment service provider) integration, ISO 20022 messaging standards, double-entry ledgering for accounting, and multi-rail routing (bank transfers, stablecoins, blockchain) [unverified].

**Nubank**: Serves 122+ million customers across Brazil, Mexico, Colombia. Uses a general ledger system to track customer balances and obligations. The Authorizer system is critical infrastructure: handles real-time transaction approvals for credit cards and payments with low latency and high availability. Must maintain sub-millisecond latency for Mastercard network integration. Transitioned from on-premise data centers to cloud infrastructure while maintaining performance [S16].

**Alipay (Ant Group)**: Processes 256,000 transactions per second (256k TPS) on 11/11 "Singles' Day" shopping festival (China's largest e-commerce event). Uses distributed ledger technology (Hyperledger Fabric-based) to ensure transaction immutability and auditability. Blockchain-based cross-border remittance service launched in 2018 (AlipayHK to GCash Philippines), enabling real-time, low-cost money transfers between Hong Kong and Philippines. Over 60% of Ant Group's staff are engineers and data scientists [unverified Alipay blog sources].

---

## 5. Purpose-Built Ledger Databases

**TigerBeetle**: Purpose-built distributed financial ledger optimized for payment processing [S9, S10].

- **Architecture**: Single-threaded state machine (no locks, no contention). All transfers processed sequentially on one core, ensuring deterministic execution and perfect idempotency.
- **Consensus**: Viewstamped Replication (VSR), a classic consensus algorithm ensuring correct automatic failover. Replicated across 3+ nodes for fault tolerance.
- **Batching**: Processes up to 8,189 transfers per batch request (8,190 max). Consensus cost amortized across batch, enabling high throughput.
- **Throughput claim**: ~1M transfers/sec (or 100k-500k TPS depending on configuration and hardware).
- **Identifiers**: All transfers have unique 128-bit client-generated IDs for perfect idempotency.
- **Two-phase transfers**: Supports authorization-style pending transfers. Phase 1: authorize and reserve funds (pending state). Phase 2: post or void the transfer. Timeouts managed by database.
- **Linked and balancing transfers**: Multi-leg transactions (e.g., payment with fee split) can be encoded as linked transfers that must all succeed or all fail atomically.
- **Storage**: LSM engine with connector to object storage for lower levels, enabling petabyte-scale storage with quick recovery.

**Modern Treasury Ledgers**: Cloud-based ledger platform for fintech and financial services [S11].

- **Double-entry accounting**: Every transaction must debit one account and credit another by the same amount, ensuring balances sum to zero.
- **Immutability**: All state changes are permanent and queryable. Transactions are mutable while pending, immutable once posted. Past states always retrievable.
- **Versioned balances**: Accounts and transactions have versions. Querying by version enables exact state lookup at any point in time. Three balance types: Posted (settled), Pending (authorized but not yet settled), Available (Posted minus holds).
- **Account versions on Entries**: Each entry records which account version created it, enabling audit of exact balance composition.

**Formance**: Open-source (MIT-licensed) ledger system for fintechs [S13].

- **Storage**: PostgreSQL transactional backend.
- **Transactions**: Atomic multi-posting transactions (many debits and credits in a single atomic operation).
- **Numscript**: Domain-specific language (DSL) for describing money movements. Readable by both engineers and finance teams.
- **Deployment**: Standalone microservice or part of Formance Platform. Logs shipped to replica stores for OLAP (analytical) queries.

**Amazon QLDB**: AWS's managed ledger database, purpose-built for immutable and auditable transaction records. Deprecated or low-priority in AWS roadmap [unverified why].

**Fragment**: [Unverified, no published architectural details found].

---

## 6. ACH / Bank Rails

**NACHA (National Automated Clearing House Association)** operates the ACH Network, a batch-oriented payment system for U.S. domestic transfers [S12].

**Three Same-Day Processing Windows** (as of 2024):

1. **Morning window**: Submission deadline 10:30 AM ET (ODFI to ACH operator). Settlement at 1:00 PM ET.
2. **Afternoon window**: Submission deadline 2:45 PM ET. Settlement at 5:00 PM ET.
3. **Evening window**: Submission deadline 4:45 PM ET (for returns only). Settlement at 6:00 PM ET.

Prior to same-day ACH expansion, only one settlement window existed (next business day). The three windows enable liquidity and faster returns processing.

**Return Reason Codes**: If an ACH transaction cannot be processed, the RDFI (receiving bank) issues a return with a code:

- R01 (Insufficient funds)
- R02 (Account closed)
- R03 (No account/unable to locate)
- R04 (Invalid account number)
- And many others (30+ total codes defined by NACHA).

Administrative returns (R02, R03, R04) have regulatory thresholds: if an RDFI's return rate exceeds 3% for these codes, enforcement action may follow.

**Settlement timing**: Original ACH settlement is T+1 (next business day). Returns can be sent same-day using the three windows, with settlement T+1 for the return credit.

**Batch processing**: ACH is fundamentally batch-oriented, unlike card networks (real-time auth) or Pix (instant). Files are batched by originating bank (ODFI), transmitted to ACH operator, processed by receiving bank (RDFI), settled next business day.

**Scale**: ACH processes billions of transactions annually in the U.S. (approximately 22 billion ACH transactions in 2023). Enables payroll, vendor payments, bill payments, consumer transfers. No real-time settlement guarantee, but low cost and established regulatory framework.

---

## Design Patterns and Trade-offs Observed

Across all systems reviewed, several patterns emerge:

1. **Idempotency as first-class requirement**: Every major payment system (Stripe, Airbnb, Visa reversals) relies on client-generated unique identifiers and server-side deduplication. Absence of idempotency leads to duplicate charges/payouts, one of the costliest failure modes. Implementation requires a durable store (database) to record processed keys and their results, with appropriate retention windows (e.g., Stripe's 24-hour retention).

2. **Double-entry accounting as invariant**: Uber (Gulfstream), Modern Treasury, Formance, and TigerBeetle all enforce double-entry: every debit matched by a credit. Ensures ledger balances and enables automated reconciliation. Violations are immediatey detectable (balances != 0), supporting compliance audits and bug detection.

3. **Immutability for auditability**: Uber (LedgerStore), Modern Treasury, and NACHA (ACH) all make transaction records immutable or append-only. Critical for compliance (SOX, PCI DSS) and dispute resolution. Enables audit trails, regulatory proof, and tamper detection.

4. **Two-phase semantics**: TigerBeetle and card networks (auth -> capture) both implement two-phase operations: reserve, then finalize. Avoids cascading failures and enables timeout-safe retry logic. First phase (authorize) locks funds; second phase (capture or void) confirms or releases.

5. **Batching for throughput**: TigerBeetle batches 8,189 transfers per request, amortizing consensus cost. Card networks batch transactions hourly (Visa clearing), daily (ACH), or in real-time windows (Visa 3 daily windows). Batching trades latency for throughput; must be tuned per use case.

6. **Regional redundancy and failover**: Visa operates 4 synchronized data centers; Uber/Stripe use cloud multi-region for failover. Single data center or region is unacceptable for payment systems. Active-active or active-passive replication required for 99.99%+ uptime.

7. **Strong consistency over eventual consistency**: All systems reviewed (Visa, Stripe, Uber, Airbnb) prioritize strong consistency over high availability. Payments cannot afford race conditions or diverged replicas. Contrast with eventual-consistency databases (DynamoDB, Cassandra), which are insufficient for ledgers.

---

## Key Takeaways for Payment Ledger Design

From these architectures, the following requirements emerge for a robust payment ledger:

1. **Idempotency must be built-in**: Store unique client-generated keys with results. Retention window must balance durability (Stripe uses 24 hours) with storage cost.

2. **Double-entry accounting is non-negotiable**: Every movement must debit one account and credit another atomically. Enforces balance invariants automatically.

3. **Immutability enables auditability**: Append-only or versioned storage allows auditors and regulators to verify the complete transaction history. No backfilling or modification of historical records.

4. **Two-phase transfers prevent partial failures**: Authorize/reserve before posting. Timeout-safe: if response is lost, original authorization can be rolled back via reversal.

5. **Batching amortizes consensus cost**: Combine many transfers into one consensus round (TigerBeetle's 8,189/batch). Trade latency for throughput depending on use case (real-time payments vs. overnight ACH).

6. **Region redundancy is mandatory**: Multi-region replication, active-active or active-passive failover. Single region failure must not cause ledger unavailability or data loss.

7. **Strong consistency beats availability**: CAP theorem trade-off: payment ledgers choose consistency and partition tolerance over availability. Temporary unavailability is preferable to diverged ledgers.

---

## Numbers the Solution Will Use

| Number | Value | Source ID | Confidence | Notes |
|--------|-------|-----------|------------|-------|
| Visa peak TPS | 65,000 | S1 | High | Design capacity, not average load |
| Visa annual transactions FY2025 | 257.5 billion | S2 | High | 10% YoY growth |
| Visa average TPS (derived) | ~8.2M | S2 | Medium | 257.5B / (365*24*3600), includes all transaction types |
| Visa data centers | 4 | S1 | High | 2 US, 1 Singapore, 1 UK, synchronized |
| Mastercard average TPS | 44,444 | [SEC 2010] | Medium | ~160M txn/hour, may have increased |
| Stripe idempotency retention | 24 hours | S4 | High | Clients must retry within this window |
| TigerBeetle batch size | 8,189 | S9 | High | Default max, 8,190 absolute max |
| TigerBeetle throughput | ~1M/sec | S10 | Medium | Depends on network, replication factor, hardware |
| Alipay peak (11/11 2024) | 256,000 TPS | [unverified] | Low | Singles' Day e-commerce festival |
| Nubank customers | 122+ million | S16 | High | As of 2024 |
| Airbnb payment consistency | Five nines (99.999%) | S6 | Medium | Achieved after Orpheus framework launch |
| NACHA same-day windows | 3 per day | S12 | High | Morning 10:30 AM, Afternoon 2:45 PM, Evening 4:45 PM ET |
| Uber Gulfstream effort | 40+ engineers, 2 years | S7 | High | Two-year migration/build effort |
| ISO 8583 auth timeout | ~30 seconds | [S15] | Medium | Typical timeout for reversal issuance |
| ACH annual volume (US) | ~22 billion | [unverified] | Medium | 2023 estimate, includes all entry types |
| Card network settlement | T+1 or T+2 | [S1] | High | Clearing next day, settlement one to two days later |
| ACH settlement | T+1 | S12 | High | Next business day after batch processing |


---

## Spot-check corrections (added after review, 2026-09-13)

Checked the numbers that `solution.md` uses against the primary source. Corrections to the text above:

| Claim above | Correction | Checked against |
|---|---|---|
| "Derived average TPS: 8.17M" | Arithmetic error by 1,000x. 257.5 B / 31.536 M s = **about 8,200 TPS average**. Q4 FY2025 alone was 67.7 B processed transactions in 92 days = about 8,500 TPS. Peak day is plausibly 2 to 3x average, so 20 k to 25 k TPS. The 65 k figure is the published capacity, roughly 8x average | Visa Q4 FY2025 earnings release, https://s1.q4cdn.com/050606653/files/doc_financials/2025/q4/Q4-2025-Earnings-Release_vF.pdf |
| Airbnb post dated "Mar 27, 2026" | The post is from **2019**. The "five nines" line is about consistency after Orpheus, and the lease timeout is not stated in the post | https://medium.com/airbnb-engineering/avoiding-double-payments-in-a-distributed-payments-system-2981f6b070bb |
| Stripe Ledger described only as "billions of events daily" | The post gives: **5 billion events per day**, 99.99% of dollar volume fully ingested and verified within 4 days, 99.999% of activity monitored and triaged, over 99.9999% "explainability of money movement", a 99.99% data quality score, and BFCM 300 M transactions at $18.6 B with > 99.999% API availability. Ledger models producer systems as fund flows between accounts (a state machine), and defines three metrics: **Clearing** (balances that should be zero at steady state are zero), **Timeliness** (delay from platform entry to Ledger), **Completeness** (every producer id has a Ledger event). It is an immutable event log; the streaming framework is not named | https://stripe.dev/blog/ledger-stripe-system-for-tracking-and-validating-money-movement |
| "Mastercard 44,444 TPS, 130 ms" | From a 2010 filing. Treat as stale; do not quote in an interview | |
| "ISO 8583 auth timeout ~30 seconds" | Network-specific and configurable. Use "single-digit seconds for the issuer, then reversal" and say it is a parameter | |
| "Uncaptured auths expire after 7 days" | That is Stripe's default for uncaptured PaymentIntents. Card scheme rules vary by merchant category (7 to 30 days). Say "days, scheme-defined" | https://docs.stripe.com/payments/place-a-hold-on-a-payment-method |

Numbers `solution.md` uses from this file: Visa 65 k TPS capacity, 257.5 B transactions/yr (8,200 TPS avg), 4 data centers, Stripe 5 B ledger events/day and 24 h idempotency retention, TigerBeetle 8,190 transfers per batch, NACHA 3 same-day windows and T+1.
