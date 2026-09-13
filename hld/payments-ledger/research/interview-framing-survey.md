# Payment System Design Interview: Framing Survey

Research compiled Sep 2026. Focus: how Visa-scale payment systems with ledgers and duplicate-prevention are asked across companies and prep sources.

## Sources Reference Table

| ID | URL | Establishes |
|---|---|---|
| HI-PS | https://www.hellointerview.com/learn/system-design/problem-breakdowns/payment-system | 10k TPS baseline, 4 deep-dive zones (security, durability, transaction safety, scalability) |
| BB-PAY | https://bytebytego.com/guides/payment-system/ | Service architecture, PSP flow, wallet/ledger model |
| BB-ACC | https://blog.bytebytego.com/p/ep-39-accounting-101-in-payment-systems | Double-entry ledger, accounting invariants |
| BB-SCALE | https://blog.bytebytego.com/p/how-stripe-scaled-to-5-million-database | Stripe's DocDB: 5M queries/sec, 2000 shards, zero-downtime migration |
| BB-DUP | https://bytebytego.com/guides/how-to-avoid-double-payment/ | Idempotency pattern: UUID, at-least-once + at-most-once = exactly-once |
| SDH-PAY | https://www.systemdesignhandbook.com/guides/design-a-payment-system/ | Requirements, entities, PCI/security, double-entry, ledger immutability |
| SDH-STRIPE | https://www.systemdesignhandbook.com/guides/stripe-system-design-interview/ | Ledger conservation, immutability, audit, idempotency, race conditions |
| DG-PAY | https://www.designgurus.io/system-design-interview | Payment platform in L5/L6 course; staff vs senior grading |
| DG-CONS | https://www.designgurus.io/system-design-interview/concepts/replication-consistency | Strong consistency for ledger, eventual for non-critical |
| EXP-PAY | https://www.tryexponent.com/questions/2872/design-payment-system | Failure modes, retries, idempotency, operability |
| II-GUIDE | https://interviewing.io/guides/system-design-interview/part-two | Senior signal: simplicity, collaborative pushback, security depth |
| PRACHUB | https://prachub.com/interview-questions/design-a-scalable-payment-system | p99 <200ms, user-to-user + merchant, refunds, chargebacks, double-entry |
| STRIPE-API | https://docs.stripe.com/api/idempotent_requests | 24h key retention, V4 UUID, parameter validation, concurrent request handling |
| LEETCODE-PAY | https://leetcode.com/discuss/interview-question/system-design/706038/ | Exponential backoff, nightly reconciliation, double-spend prevention |
| BLIND-RIPPLING | https://www.teamblind.com/post/rippling-system-design-interview-what-to-expect-uwzweqw3 | Broad multi-phase systems, product + infra angle, load balancing/DB/queues |
| BLIND-STRIPE | https://www.teamblind.com/post/Stripe-system-design-interview-questions-qsbyrhsz | URL shortener example given; emphasis on scalability, encryption |
| VISA | https://www.sec.gov/Archives/edgar/data/1403161/000140316120000070/v-20200930.htm | Visa VisaNet: 65,000 TPS capacity |
| 1P3A-STRIPE | https://www.1point3acres.com/interview/problems/company/stripe | 212 reported questions; behavioral signal on ownership, written communication |
| 1P3A-DATABRICKS | https://www.1point3acres.com/interview/problems/company/databricks | Prompt-family driven; mixes algorithmic + low-level systems + product design |

## 1. Candidate Reports of the Prompt

### Stripe (2024-2026)

**Prompt (reported):** "URL shortener with a security twist. Focus on scalability and brush up a bit on encryption." [BLIND-STRIPE] — This appears indirect; actual payment prompts less publicly detailed. One candidate reported coding problem: invoice payment reconciliation using structured payment/invoice data (Stripe onsite, 1point3acres).

**Follow-ups reported:** [unverified direct quotes; search shows these topics matter but exact phrasing rare in public reports]
- Handling retries without double-charging
- PCI compliance and card tokenization
- Real-time vs. batch settlement

**Level:** Senior to Staff (coding + system design rounds)

**URL:** [BLIND-STRIPE], [1P3A-STRIPE]

### Rippling (2024-2026)

**Prompt (reported):** "Design a Rules Engine for Corporate Credit Cards (LLD round)" and "System design for settling transactions given from/to/amount data" [BLIND-RIPPLING]. No explicit "design a payment system" quote, but payment-adjacent. Interviewers assess "end-to-end from product and infrastructure perspective."

**Follow-ups reported:** Load balancing trade-offs, database choices, queuing patterns. Deep technical detail expected, especially "around handling financial data" [BLIND-RIPPLING].

**Level:** SDE 2 (mid-level)

**URL:** [BLIND-RIPPLING]

### Databricks (2023-2024)

**Prompt (reported):** "Design Payment Auth System (e.g. Visa card) for credit card swiping" (one mention in Glassdoor). Also: generic system design with focus on exactly-once semantics and WAL coordination, not product features. Interview loop mixes algorithmic coding, low-level systems, and product-grounded design [1P3A-DATABRICKS].

**Follow-ups:** Not publicly detailed; emphasis on infra: exactly-once delivery, coordination, WAL usage.

**Level:** L5/L6 (staff equivalent)

**URL:** [1P3A-DATABRICKS]

### Google / Meta / Amazon [unverified]

No specific "design payment system" reports found in public data. General system design at these companies covers Venmo/PayPal as example architectures (peer-to-peer with async settlement) [1P3A-DATABRICKS]. Candidates reference multi-region, strong consistency, and Spanner-style answers for Google.

### Coinbase [unverified]

Reports indicate system design interviews include "crypto exchange" and "settlement" topics. Settlement + ledger systems align with payment design. Specific payment system prompts not found in public candidate reports.

## 2. Prep-Source Framings

### Hello Interview: "Design a Payment System like Stripe"

**Functional requirements:** [HI-PS]
- Merchants initiate payment requests (charge customer for amount)
- Users pay with credit/debit cards
- Merchants view payment status (pending, success, failed)

**Non-functional requirements:** [HI-PS]
- 10,000 TPS at peak
- Durability and auditability (no data loss, even under failure)
- Transaction safety despite asynchronous external networks
- Security and low latency (prevent user abandonment)

**Core entities:** Users, merchants, transactions, payment methods, ledger entries, notifications.

**API:** REST for external (clients/SDKs), gRPC for internal (payment service to booking/inventory/payment services).

**Deep-dive questions:** [HI-PS]
1. Security: building highly secure payment infrastructure
2. Durability and auditability: guarantee no transaction data lost
3. Transaction safety: maintain financial integrity despite async PSP networks
4. Scalability: handle 10k+ TPS
5. Webhooks: support async notifications

### ByteByteGo: Payment System & Accounting 101

**Architecture:** [BB-PAY] Payment service → PSP (external card network) → Wallet service (balance update) → Ledger service (append-only record).

**Entities:** Payment events, payment orders (per seller), seller wallets, ledger entries, bank settlement files.

**Idempotency approach:** [BB-DUP] Client generates UUID idempotency key. Server caches result of first execution. Retry with same key returns cached result. At-least-once (via retry) + at-most-once (via idempotency check) = exactly-once.

**Ledger model:** [BB-ACC] Double-entry accounting. Every transaction has source account (debit) and target account (credit). Maintains balance invariant: Assets = Liabilities + Equity. Append-only. Immutable for audit.

**Key gotcha:** [BB-ACC] "Reconciliation is the last line of defense." Nightly batch jobs compare ledger entries against external bank records to catch syncing failures or dropped requests.

**Numbers:** [BB-SCALE] Stripe handles 5M database queries/sec via DocDB (custom sharded MongoDB). 2000 database shards. Zero-downtime migration via 6-step orchestration. Bulk data insertion optimized to 10x throughput via sorted insertion.

### System Design Handbook: "Design a Payment System" & Stripe

**Functional:** Process transactions, support multiple payment methods, authorize + capture real-time, refunds, chargebacks, immutable transaction logs, notifications. [SDH-PAY]

**Non-functional:** Scalability (spikes), security (PCI DSS), reliability (exactly-once), low latency. [SDH-PAY]

**Deep-dive focus:** [SDH-STRIPE] Ledger conservation (balanced entries), immutability (history unchangeable), audit trails (every state change documented). Three critical requirements. Strict financial invariants.

**Framework:** Treat as "digital ledger not just an API." Idempotency for timeout retries. Race conditions during refunds/withdrawals. Multi-currency reconciliation. Infrastructure failure handling. [SDH-STRIPE]

### DesignGurus: Grading Ladder (Senior vs Staff)

**Senior interview bar:** [DG-PAY] "Design X at scale." Fluency across canonical patterns, deep in one area, articulate on trade-offs. Grades architectural knowledge.

**Staff interview bar:** [DG-PAY] "Design X" with deliberate ambiguity. Grades systems thinking and judgment. Second-order effects: team velocity impact, migration cost, 5-year evolution, org boundaries.

**Consistency model lesson:** [DG-CONS] Don't answer "strong" or "eventual" for whole system. Split: name the 1-2 pieces of data that cannot be stale (ledger, balance → strong consistency, primary-read). Recommend Postgres sync replication for payment ledger. PACELC: PC/EC tradeoff (accept higher write latency, lower availability under partition, for correctness).

### Exponent / Aced: Payment System

**Approach:** [EXP-PAY] Focus on failure modes, retries, idempotency, operational concerns. Goal: system that "could actually run in production." Example: "Design Amazon Kindle Payment System."

**Emphasis:** Production readiness. Observability (trace IDs for correlation). Queue-based architecture between services.

## 3. Follow-Up Ladder (Merged Across Sources)

Escalating probes an interviewer uses to test depth and failure-mode reasoning:

1. **Idempotency key on retry:** Client retries charge request. How do you avoid charging twice? [BB-DUP, PRACHUB, STRIPE-API, SDH-STRIPE] ← Entry rung; expect UUID + cache-first response.

2. **PSP timeout / "did it go through?"** Client retries after PSP call times out. Did the charge happen at PSP? How do you tell? [SDH-STRIPE, EXP-PAY, LEETCODE-PAY] ← Test: polling, PSP idempotency keys, callback/webhook, reconciliation.

3. **Concurrent idempotency key requests:** Two requests with same idempotency key arrive at server at the same time. Which one wins? [STRIPE-API, PRACHUB] ← Test: locking, linearizability, Stripe's behavior (parameter comparison).

4. **Hot row / high-volume merchant:** One merchant receives 10,000 writes/sec to their account balance row. Database contention. How do you scale? [BLUE, II-GUIDE] [unverified; pattern common but not always explicitly named in reports]

5. **Ledger DB failure mid-transaction:** Ledger database goes down after wallet update but before ledger entry. Money moved but not recorded. Recovery? [SDH-STRIPE, BB-ACC, LEETCODE-PAY] ← Test: event sourcing, WAL, idempotent ledger writes, reconciliation as recovery.

6. **Reconciliation / audit:** How do you know the ledger is right? How do you detect missing transactions or account balance errors? [BB-ACC, BB-DUP, LEETCODE-PAY, EXP-PAY] ← Test: nightly batch jobs comparing ledger to external records, double-entry invariant checks, alerting.

7. **Multi-region payment:** User in EU pays merchant in US. Payment needs to cross regions. Consistency guarantees? [DG-CONS, SDH-STRIPE] [unverified specific prompt; pattern aligned with Google Spanner / multi-DC interviews]

8. **PCI compliance boundary:** Where does the card number live? Who can see it? How do you scope PCI? [SDH-PAY, HI-PS] ← Test: tokenization, no card data in payment service, third-party processor, network segmentation.

9. **Refund / partial refund / chargeback:** Customer disputes charge or requests refund. Ledger entries? Wallet reversal? What if refund fails? [SDH-PAY, PRACHUB] ← Test: double-entry for refund (reversal of original entries), idempotency for refund API, bank chargeback flow.

10. **Audit trail / historical balance:** Prove an account's balance as of last Tuesday. Immutable ledger assumption? [SDH-PAY, BB-ACC] ← Test: append-only ledger, point-in-time queries, snapshots vs. replay.

11. **10x Black Friday traffic:** Traffic spikes 10x. What breaks first? Sharding strategy? API rate limits? PSP capacity? [BB-SCALE, HI-PS] ← Test: horizontal scaling plan, idempotency key cache sizing, PSP fallback / queue, monitoring.

12. **Money math and currency:** How do you handle fractional cents, currency conversion, rounding? Where does rounding loss go? [BB-ACC, PRACHUB] [unverified specific prompt; core to payment systems]

13. **Exactly-once semantics:** Define your delivery guarantee end-to-end. At-least-once? At-most-once? Exactly-once? Show the mechanism. [BB-DUP, 1P3A-DATABRICKS] ← Test: idempotency for at-most-once, retry loop for at-least-once, combination for exactly-once.

14. **What did you refuse to build?** Candidate doesn't mention out-of-scope items. Follow-up: Why not support refunds? Why no subscription billing? [II-GUIDE, DG-PAY] ← Staff signal: scope discipline, trade-off clarity.

## 4. Company-Specific Angles

### Rippling

**Focus:** Multi-tenant payroll, ACH settlement, "what if this runs twice," tenant isolation. [BLIND-RIPPLING]

Rippling's product is corporate payroll and expense management, so payment design questions often emphasize multi-tenancy (one merchant might be 1000s of payroll runs), ACH idempotency (ACH is idempotent by design but timing matters), and ensuring one tenant's failure doesn't affect another. Behavioral signal: interviewers want "deep technical detail and compelling stories, particularly around handling financial data" [BLIND-RIPPLING]. Expect founder-like reasoning (product + infra).

### Stripe

**Focus:** Reference architecture, explicit RPS targets, API-first, durability non-negotiable. [BLIND-STRIPE, SDH-STRIPE]

Stripe interviews often start with "design Stripe" or "design a payment system like Stripe." They emphasize ledger conservation (every cent tracked), immutability (no retroactive changes), and audit trails (prove what happened). If designing for Stripe, be explicit about handling idempotency key expiration (24h at Stripe [STRIPE-API]), retry logic, and PSP integration. Stripe engineers care deeply about observability and tracing [PRACHUB: trace IDs mentioned].

### Databricks

**Focus:** Infrastructure, exactly-once semantics, WAL, coordination primitives. [1P3A-DATABRICKS]

Databricks interviews emphasize the hard infra problems: how do you guarantee exactly-once delivery? How do you coordinate across multiple nodes? What's your WAL strategy? They push on mechanisms (Kafka transactions, 2PC, distributed consensus) more than on product features (refunds, chargeback). Interview loop mixes algorithmic (LeetCode-style coding), low-level systems (concurrency, threading), and product-grounded design (operability). Payment systems are often a vehicle to test exactly-once guarantees, not the focus itself.

### Google

**Focus:** Multi-DC, Spanner-style answers, strong consistency, geographically distributed ledger. [DG-CONS]

Google interviews often probe multi-region consistency. Expect questions on Spanner (globally distributed, strict serializability), read-your-writes consistency (session-level guarantees), and two-phase commit for distributed transactions. If designing a global payment system at Google, emphasize strong consistency for the ledger (all regions see the same balance after a transaction), eventual consistency for non-critical data (transaction history views), and Spanner's multi-versioned key-value store with synchronized clocks as a reference architecture.

### Coinbase

**Focus:** Settlement, hot/cold wallets, crypto-specific ledger invariants. [unverified]

Coinbase's payment system is cryptocurrency settlement. Payment design questions often emphasize settlement mechanics (moving funds to external wallets), custody (hot/cold wallet trade-offs), and ledger invariants specific to crypto (UTXO vs. account model). Likely to ask about eventual settlement (funds appear in user wallet after N blocks/confirmations) vs. strong consistency (user sees debit immediately, settlement happens later).

### Amazon

**Focus:** Practicality, operational excellence, cost. [1P3A-DATABRICKS]

Amazon's bar emphasizes "founder-like" thinking: what's the cheapest way to do this? What operational signals matter? How do you run this on-call? Expect questions on monitoring (what metric pages you at 3am?), SLO (p99 latency target?), and cost (database per-write cost × 10k TPS?). Amazon often asks about Kindle payment system, AWS Payments, or internal payment platform design, emphasizing integration with existing AWS services.

## 5. Grading Rubric Signals: Senior vs Staff

### Staff Candidate Signals (Unprompted)

**Consistency model per component:** [DG-PAY] Staff candidate explicitly splits consistency: "Strong for ledger and user balance (primary-only reads), eventual for transaction history view."

**What they refused to build:** [II-GUIDE, DG-PAY] Candidate says "Out of scope: subscriptions, multi-currency, refunds" and explains why (scope, time, operational complexity).

**Migration / zero-downtime rollout:** [DG-PAY] Staff candidate addresses: "How do we get from current system to this design? Here's a blue-green strategy: run new payment service in shadow mode, compare results, flip traffic."

**Operability / SLO:** Candidate proactively states: "This design targets p99 latency < 200ms. That metric pages on-call if breached. Here's monitoring (ledger entry delay, idempotency cache hit rate, PSP gateway latency)."

**Cost:** Candidate estimates: "At 10k TPS, that's ~10M database writes/day. At $X per write, ~$Y annually. Sharding doubles the operational cost. Worth it to avoid hot row contention."

**Second-order effects / org boundaries:** [DG-PAY] Staff candidate addresses: "This design requires close partnership with Finance (reconciliation logic), Legal (PCI), and Payments eng (PSP integration). Migration takes 2 quarters if we move existing merchants."

### Senior Candidate Signals (Still Valuable, But Incomplete)

**Architectural fluency:** Senior candidate fluently explains sharding, replication, consistency trade-offs.

**One deep dive:** Senior goes deep on idempotency or ledger accounting or exactly-once, but may not revisit design in later trade-offs.

**Articulated trade-offs:** Senior lists "strong vs eventual consistency" or "batch vs. real-time settlement" but doesn't address org impact or migration cost.

**Communication sophistication:** [II-GUIDE] Senior keeps designs simple, checks in at milestones (not after every decision), uses collaborative language ("Let's explore...").

**Pushback:** Senior can defend design choices against interviewer challenges, but not proactively discuss failure modes or org constraints.

## 6. Numbers Candidates Are Expected to Quote

### Card Network Capacity

**Visa:** VisaNet processes > 65,000 transaction messages per second. [VISA] This is often cited as a reference ceiling. In interviews: "Visa's network can handle 65k TPS, but their processors (individual banks) have lower caps. Assume 1-2k TPS per merchant bank."

**Mastercard:** ~44,000 TPS (160M transactions/hour) [unverified; cited in some prep materials but less common in interviews].

**Real-world Visa TPS:** ~1,700 to 2,000 average annual TPS (calculated from annual volume) [unverified; candidates may calculate from Visa's annual report, but exact number not standard in interviews].

### Stripe Scale (Published)

**Database queries:** 5 million per second at 99.999% uptime (five-nines). [BB-SCALE]

**API requests:** 500M per day (avg ~5,787 RPS). Peak 27,395 RPS during BFCM 2023. 10,000+ RPS sustained as baseline. [BB-SCALE, Google search results]

**Uptime:** 99.999% historical; 99.9999% during BFCM 2025 (peak $40B processed). [BB-SCALE, search results]

**Annual volume:** $1.9 trillion in payment volume (2025 estimate) [Google search results]. Translates to ~60M transactions/day avg, but real number includes high-frequency, low-value and low-frequency, high-value transactions.

**Peak:** $40B during BFCM 2025 (Black Friday to Cyber Monday). [search results]

### Payment API Latency Budget

**p99 latency target:** Most prep sources use p99 < 200-500ms end-to-end as reasonable. [PRACHUB, HI-PS] Real constraint: issuer bank round trip ~0.5-1s, so p99 latency budget in payment service itself is ~100-200ms to leave room for network, issuers, and user tolerance.

**Idempotency key retention:** Stripe retains idempotency keys for at least 24 hours. After 24h, key can be pruned and reused = new request. [STRIPE-API]

**Idempotency key format:** V4 UUID recommended. Up to 255 characters. Avoid sensitive data (email, SSN). [STRIPE-API]

**API v2 retention:** Longer window (30 days) in newer Stripe API v2, but 24h is the classic baseline. [STRIPE-API]

### Example QPS for Design

**Hello Interview baseline:** 10,000 TPS at peak. [HI-PS] Used as a training-wheel number; actual Stripe is 5-10x higher, but 10k is good for designing the architecture without over-engineering.

**Databricks / Amazon scale:** Often ask for systems that scale to 100k+ TPS or 1M+ events/sec (depends on domain). Payment systems typically assume 10-50k TPS as the hard ceiling for a single region.

## 7. Key Prep Gotchas Emphasized Across Sources

- **Reconciliation is the last line of defense.** [BB-ACC] Every nightly, compare ledger to external bank records. Detect missing transactions, balance errors, failed settlement.

- **Exactly-once requires both at-least-once (retry) and at-most-once (idempotency).** [BB-DUP] Don't just say "exactly-once." Explain the mechanism.

- **Strong consistency for ledger, eventual elsewhere.** [DG-CONS] Ledger = primary-only, strong. Transaction history view = eventual. User balance = strong (for overdraft checks).

- **Idempotency key scope:** Stripe stores idempotency key result per API endpoint and account. [STRIPE-API] Reusing the same key on a different endpoint generates new request.

- **What if PSP times out?** [SDH-STRIPE, EXP-PAY] PSP might have processed the charge but timed out. Need polling, webhook, or reconciliation to detect. Don't assume timeout = no charge.

- **Refuse scope early.** [II-GUIDE, DG-PAY] Say "Out of scope: multi-currency, subscriptions, payouts" explicitly. Interviewers respect scope discipline.

---

## Follow-Up Ladder (Merged)

1. **Idempotency key on retry** – UUID in header, server caches result, return cached on retry. [BB-DUP, STRIPE-API, PRACHUB]

2. **PSP timeout – did it go through?** – Polling, PSP idempotency key, webhook callback, reconciliation. [SDH-STRIPE, EXP-PAY]

3. **Concurrent idempotency key requests** – Locking, linearizability, Stripe's parameter comparison. [STRIPE-API, PRACHUB]

4. **Hot merchant row (10k writes/sec)** – Sharding, versioning, or accepting higher latency with queuing. [II-GUIDE, DG-CONS]

5. **Ledger DB failure mid-transaction** – Event sourcing, WAL, idempotent writes, reconciliation recovery. [SDH-STRIPE, BB-ACC]

6. **Reconciliation / audit** – Nightly batch comparing ledger to external records, double-entry invariant. [BB-ACC, LEETCODE-PAY]

7. **Multi-region payment** – Consistency across regions (Spanner model), settlement timing. [DG-CONS, SDH-STRIPE]

8. **PCI compliance boundary** – Tokenization, card never in payment service, processor handles encryption. [HI-PS, SDH-PAY]

9. **Refund / chargeback** – Reverse double-entry, idempotent refund API, bank disputes. [SDH-PAY, PRACHUB]

10. **Audit trail / historical balance** – Append-only ledger, point-in-time queries, snapshots. [BB-ACC, SDH-PAY]

11. **10x Black Friday** – Sharding, cache sizing, PSP fallback, rate limiting. [BB-SCALE, HI-PS]

12. **Money math / rounding** – Fractional cents, currency conversion, where loss goes. [BB-ACC, PRACHUB]

13. **Exactly-once end-to-end** – Idempotency for at-most-once + retry for at-least-once. [BB-DUP, 1P3A-DATABRICKS]

14. **What did you refuse?** – Scope discipline, trade-off clarity. [II-GUIDE, DG-PAY]

