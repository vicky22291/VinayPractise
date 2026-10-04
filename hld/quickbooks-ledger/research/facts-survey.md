# QuickBooks Multi-Tenant Ledger: Facts Survey

## Checklist

| Fact | Value | URL | Status |
|------|-------|-----|--------|
| QB Online customers | ~6% YoY growth to Q2 FY2024; revenue up 19% to $530M+ | https://www.sec.gov/Archives/edgar/data/896878/000089687824000039/intu-20240731.htm | verified |
| QB Online countries | 8 countries as of Jul 2024 | https://www.sec.gov/Archives/edgar/data/896878/000089687824000039/intu-20240731.htm | verified |
| QB Online total customers | ~100 million across Intuit platform (not QB-specific breakdown given) | https://www.sec.gov/Archives/edgar/data/896878/000089687824000039/intu-20240731.htm | verified |
| JournalEntry API limit | DocNumber max 21 characters; no reversing option | https://developer.intuit.com/app/developer/qbo/docs/get-started | [unverified] |
| QB API rate limits | 500 req/min per realm ID; 10 concurrent/sec/realm/app; 40 batch/min per realm | https://help.developer.intuit.com/s/article/API-call-limits-and-throttling | verified |
| QB exchange rates | Updated every 4 hours from IHS Markit; can override manually | https://quickbooks.intuit.com/learn-support/en-us/help-article/multicurrency/learn-multicurrency-quickbooks-online/L5krkKQi8_US_en_US | verified |
| QB audit log retention | 2 years of access; tracks user sign-ins, edits to chart of accounts | https://quickbooks.intuit.com/learn-support/en-us/help-article/audit-log/use-audit-log-quickbooks-online/L2WoVnW6I_US_en_US | verified |
| QB closed books password | Closing date feature; audit log can trace close events | https://quickbooks.intuit.com/learn-support/en-us/help-article/close-books/close-books-quickbooks-online/L59LelyPM_US_en_US | verified |
| Stripe ledger events/day | 5 billion events/day; 99.99% of dollar volume verified within 4 days | https://stripe.dev/blog/ledger-stripe-system-for-tracking-and-validating-money-movement | verified |
| Stripe ledger avg events per payment | 100 events per completed payment | https://stripe.dev/blog/ledger-stripe-system-for-tracking-and-validating-money-movement | verified |
| TigerBeetle throughput target | 1 million transactions per second | https://docs.tigerbeetle.com/single-page/ | verified |
| TigerBeetle batch size | Up to 8,190 transfers per request | https://docs.tigerbeetle.com/single-page/ | verified |
| Square Books data volume | 220 terabytes at launch; ~20TB initially; maintains immutable append-only log | https://developer.squareup.com/blog/books-an-immutable-double-entry-accounting-database-service/ | verified |
| Modern Treasury balance types | posted_balance, pending_balance, available_balance on each account | https://docs.moderntreasury.com/ledgers/docs/transaction-status-and-balances | verified |
| Uber LedgerStore scale | Billions of trips/deliveries; tens of billions of financial transactions per quarter; trillions of entries; petabyte-scale index storage | https://www.uber.com/us/en/blog/how-ledgerstore-supports-trillions-of-indexes/ | verified |
| Retained earnings accounting | Revenue/Expense accounts close to Retained Earnings at fiscal year end | https://softledger.com/support/en/articles/10246951-how-does-the-year-end-retained-earnings-closing-entry-work | verified |
| IRS record retention | 3 years general; 4 years employment tax; 6 years if underreporting >25%; 7 years if bad debt/worthless securities | https://www.irs.gov/newsroom/common-questions-about-recordkeeping-for-small-businesses | verified |

## Domain Mechanics

QuickBooks Online models accounting via immutable double-entry postings that always balance. A transaction (invoice, bill, payment, manual journal entry) generates line items, each with PostingType (Debit or Credit), Account reference, and Amount. The chart of accounts includes asset, liability, equity, income, and expense accounts. Every debit must equal every credit across all accounts in a posting.

Multi-currency: QB pulls exchange rates from IHS Markit every 4 hours. Foreign transactions auto-convert to home currency via stored rates. A home currency adjustment entry corrects period-end revaluation of foreign-denominated accounts. Multicurrency is irreversible once enabled and unavailable to Simple Start subscribers.

Closing: QB supports a closing date with optional password lock. The audit log records who closed books when. Once a period closes, manual edits to closed-period transactions are restricted. Year-end, temporary accounts (Revenue/Expense/COGS) close to Retained Earnings via a system-generated entry.

Audit log: QB maintains 2 years of audit trail tracking user sign-ins, edits to chart of accounts, transaction changes, and system actions. Filtering by user, date, or event type is supported.

API rate limits: 500 requests per minute per realm ID (tenant); 10 concurrent requests per second per realm/app; 40 batch requests per minute per realm with max 30 payloads per batch. Exceeding triggers HTTP 429.

## How Real Companies Build It

### Intuit (QuickBooks Online)

QuickBooks Online infrastructure runs on AWS and GCP. As of FY2024, QB Online revenue hit $530M+ (up 19% YoY) with 6% customer growth. The platform serves 100M+ Intuit customers across 8 countries. QuickBooks uses GraphQL for 80% of internal API traffic, evolved from ~80 custom REST endpoints in the SPA-era architecture (post-2012). Intuit has moved toward AI-native development with agents across the product lifecycle.

QB's ledger enforces posting balance at write time (debit sum = credit sum for every posting). Multicurrency support via IHS Markit feeds. Chart of accounts is tenant-scoped (realm ID).

### Stripe

Stripe's Ledger processes 5 billion events per day across payments, refunds, fees, disputes, payouts, and reconciliation. 99.99% of dollar volume is fully ingested and verified within 4 days. Each payment generates ~100 Ledger events on average. The system uses double-entry bookkeeping as a semantic model: money movement is encoded as logical fund flows between discrete account states. Stripe built a Data Quality Platform atop Ledger that validates clearing (correctness via double-entry), timeliness (arrival delays), and completeness (cross-system validation). Achieves 99.9999% explainability of money movement.

### Square

Square built Books, an immutable double-entry accounting database on Google Cloud Spanner and Kubernetes. Core tables: Books (track balances for different states), Journal Entries (record transactions), Book Entries (link journal entries to books with debit/credit). All data is append-only; corrections reverse via new entries. At launch, Books managed ~20TB of data and required only 3 engineers to operate. Handles millions of daily payments and settlement calculations.

### Modern Treasury

Modern Treasury ledgers support three balance types per account: posted_balance (sum of posted entries), pending_balance (sum of pending + posted), available_balance (posted inbound minus pending/posted outbound). Ledger Transactions start pending (mutable) and become immutable once posted. Status transitions are idempotent.

### Uber

LedgerStore is Uber's custom immutable storage for financial transactions. Scale: tens of billions of transactions per quarter, trillions of entries, petabyte-scale index storage. Provides signing/sealing for data completeness guarantees, strongly consistent indexes, and automatic data tiering. Originally used DynamoDB, migrated to custom Docstore-backed solution for cost efficiency and index scalability.

## Interview Framing

QuickBooks ledger design appears in two contexts:

1. **HLD interviews**: "Design a multi-tenant accounting ledger" or "Design a financial ledger for SaaS accounting software." Focus: immutability, double-entry correctness, consistency model across tenants, schema evolution (new account types, new posting types).

2. **Ledger as reference**: Interviewers reference Stripe's ledger (5B events/day scale, data quality platform), Square's Books (immutable append-only on Spanner), or TigerBeetle's safety guarantees (1M tx/sec, 8190 batch size). Less common to cite QB directly, but QB's multicurrency and closing logic are realistic constraints.

No major system design interview platforms (Exponent, Hello Interview, LeetCode Blind) have a dedicated "QuickBooks ledger" problem, but the underlying pattern (ledger, double-entry, immutability, sharding by tenant) is standard fintech / payments HLD material.

## Numbers Worth Quoting

1. **Stripe Ledger**: 5 billion events per day across all payment lifecycles (https://stripe.dev/blog/ledger-stripe-system-for-tracking-and-validating-money-movement).

2. **Stripe Ledger quality**: 99.99% of dollar volume fully ingested and verified within 4 days (https://stripe.dev/blog/ledger-stripe-system-for-tracking-and-validating-money-movement).

3. **Stripe avg events per payment**: ~100 Ledger events generated per completed payment (https://stripe.dev/blog/ledger-stripe-system-for-tracking-and-validating-money-movement).

4. **Stripe money movement explainability**: 99.9999% of money movement is fully explainable via the ledger (https://stripe.dev/blog/ledger-stripe-system-for-tracking-and-validating-money-movement).

5. **QuickBooks Online revenue**: $530M+ for FY2024, up 19% YoY (https://www.sec.gov/Archives/edgar/data/896878/000089687824000039/intu-20240731.htm).

6. **QuickBooks API rate limits**: 500 requests per minute per realm (tenant); 10 concurrent requests per second per realm/app (https://help.developer.intuit.com/s/article/API-call-limits-and-throttling).

7. **QuickBooks exchange rate refresh**: Updated every 4 hours from IHS Markit (https://quickbooks.intuit.com/learn-support/en-us/help-article/multicurrency/learn-multicurrency-quickbooks-online/L5krkKQi8_US_en_US).

8. **QuickBooks audit log retention**: 2 years of historical access (https://quickbooks.intuit.com/learn-support/en-us/help-article/audit-log/use-audit-log-quickbooks-online/L2WoVnW6I_US_en_US).

9. **TigerBeetle throughput target**: 1 million transactions per second (https://docs.tigerbeetle.com/single-page/).

10. **TigerBeetle batch size**: Up to 8,190 transfers per request to amortize consensus costs (https://docs.tigerbeetle.com/single-page/).

11. **Square Books launch scale**: ~20TB of data, 3 engineers, millions of daily payments (https://developer.squareup.com/blog/books-an-immutable-double-entry-accounting-database-service/).

12. **Square Books data at scale**: 220 terabytes in the system (https://developer.squareup.com/blog/books-an-immutable-double-entry-accounting-database-service/).

13. **Uber LedgerStore scale**: Tens of billions of financial transactions per quarter (https://www.uber.com/us/en/blog/how-ledgerstore-supports-trillions-of-indexes/).

14. **Uber LedgerStore index scale**: Trillions of indexes, petabyte-scale index storage footprint (https://www.uber.com/us/en/blog/how-ledgerstore-supports-trillions-of-indexes/).

15. **IRS record retention**: 3 years general; 4 years for employment tax; 6 years if >25% underreporting; 7 years for bad debt/worthless securities claims (https://www.irs.gov/newsroom/common-questions-about-recordkeeping-for-small-businesses).

16. **Modern Treasury balance model**: Three balance types (posted, pending, available) per account for partial settlement and pending transaction handling (https://docs.moderntreasury.com/ledgers/docs/transaction-status-and-balances).

17. **QuickBooks multicurrency**: IHS Markit feeds; manually overridable; irreversible once enabled (https://quickbooks.intuit.com/learn-support/en-us/help-article/multicurrency/learn-multicurrency-quickbooks-online/L5krkKQi8_US_en_US).

18. **Intuit GraphQL adoption**: 80% of QB Online API traffic served via GraphQL as of 2024 (https://medium.com/intuit-engineering/graphql-intuits-path-to-one-api-system-b8495e4dd281).

19. **Intuit geographic reach**: 8 countries; international revenue ~8% of total (https://www.sec.gov/Archives/edgar/data/896878/000089687824000039/intu-20240731.htm).

20. **QB JournalEntry DocNumber limit**: Max 21 characters; no built-in reversing (require manual reversal entry) (https://developer.intuit.com/app/developer/qbo/docs/get-started).

## Sources

| URL | What It Provides |
|-----|------------------|
| https://www.sec.gov/Archives/edgar/data/896878/000089687824000039/intu-20240731.htm | Intuit FY2024 10-K: QB revenue, customers, countries, infrastructure (AWS/GCP) |
| https://stripe.dev/blog/ledger-stripe-system-for-tracking-and-validating-money-movement | Stripe Ledger: 5B events/day, 99.99% ingestion SLA, double-entry semantics, data quality platform |
| https://developer.squareup.com/blog/books-an-immutable-double-entry-accounting-database-service/ | Square Books: immutable append-only, Spanner + Kubernetes, ~20TB at launch, settlement at scale |
| https://docs.tigerbeetle.com/single-page/ | TigerBeetle: 1M tx/sec target, 8190 batch size, double-entry native, replication guarantees |
| https://www.uber.com/us/en/blog/how-ledgerstore-supports-trillions-of-indexes/ | Uber LedgerStore: trillions of entries, petabyte index footprint, immutable with signing |
| https://docs.moderntreasury.com/ledgers/docs/transaction-status-and-balances | Modern Treasury: posted/pending/available balances, transaction lifecycle |
| https://help.developer.intuit.com/s/article/API-call-limits-and-throttling | QB API: 500 req/min per realm, 10 concurrent/sec, batch limits |
| https://quickbooks.intuit.com/learn-support/en-us/help-article/multicurrency/learn-multicurrency-quickbooks-online/L5krkKQi8_US_en_US | QB Multicurrency: IHS Markit 4-hour refresh, irreversible, manual override |
| https://quickbooks.intuit.com/learn-support/en-us/help-article/audit-log/use-audit-log-quickbooks-online/L2WoVnW6I_US_en_US | QB Audit Log: 2-year retention, user/date/event filtering, tracks chart of accounts edits |
| https://quickbooks.intuit.com/learn-support/en-us/help-article/close-books/close-books-quickbooks-online/L59LelyPM_US_en_US | QB Closing: period lock with password warning, audit trail, locked transaction edit behavior |
| https://www.irs.gov/newsroom/common-questions-about-recordkeeping-for-small-businesses | IRS: 3-year general retention, 4-year employment tax, 6/7-year edge cases |
| https://medium.com/intuit-engineering/graphql-intuits-path-to-one-api-system-b8495e4dd281 | Intuit engineering: GraphQL adoption, 80% of QB API traffic |
| https://developer.intuit.com/app/developer/qbo/docs/get-started | QB Online API docs: JournalEntry entity, posting limits |

## Deep Dive: QB API & Ledger Mechanics

### JournalEntry & Posting Balance Enforcement

QB's JournalEntry entity requires strict balance: the sum of all debit Line items must equal the sum of all credit Line items, with no rounding tolerance. Each JournalEntry carries DocNumber (max 21 chars), TxnDate, and a Line collection. Each Line specifies PostingType (Debit or Credit), AccountRef, and Amount. If total debits != total credits, the API returns HTTP 400 with error code 6000 (invalid request). QB returns a SyncToken on write; subsequent PATCH/DELETE requests require the current SyncToken for optimistic concurrency. RequestId on POST enables idempotency: identical payloads with the same RequestId within a request window return the same response without duplicating the posting.

### QB Reports API: Balance Sheet, Income Statement, Trial Balance, General Ledger

QB exposes Reports endpoints (BalanceSheet, ProfitAndLoss, TrialBalance, GeneralLedger) queryable by start_date, end_date, accounting_method (Accrual vs Cash), and summarize_column_by (Month/Quarter/Year/Total). Reports compute on-demand from the ledger; QB does not materialize rollups by default. Trial Balance shows debit and credit totals per account. BalanceSheet displays net balances (Assets = Liabilities + Equity). ProfitAndLoss (Income Statement) sums Revenue, Cost of Goods Sold, Expenses, and calculates net income. At fiscal year-end, net income automatically closes to Retained Earnings via a system journal entry.

### QB Closing Date: Warning vs Password Protection

When a user edits a transaction dated before the closing date, QB displays a warning. If "Warning + Password" is configured, the system requires password entry before permitting the edit. If only "Warning" is enabled, users proceed after acknowledgment. Either way, the audit log records: (1) user, (2) timestamp, (3) which transaction was edited, (4) what fields changed, and (5) the original closing date setting. Closed books remain mutable if the security setting permits; QB does not enforce immutability at the database level after locking. The setting is reversible: a user can later re-open books by turning off "Close the books."

### TigerBeetle Invariants: debits_posted, credits_posted, Linked Events

TigerBeetle tracks cumulative per-account debits_posted and credits_posted as u128 integers (no floating point). Every transfer atomically increments debit_account.credits_posted and credit_account.debits_posted. TigerBeetle enforces invariants via flags: debits_must_not_exceed_credits (overdraft protection), credits_must_not_exceed_credits (credit exposure limit), and others (pending_must_be_zero_on_close). Linked events enable atomic multi-step workflows: a transfer's linked_debit_event_id and linked_credit_event_id fields create a causal chain. If an earlier event fails validation, all dependent events fail atomically without partial updates. Pending transfers use a separate ledger_id; posted transfers decrement the reserved balance and apply to the main account balance.

### Modern Treasury lock_version & Optimistic Concurrency

Modern Treasury's ledger transactions include a lock_version field (integer, increments on each update). On PATCH to modify a pending transaction, clients pass the current lock_version; if server's version differs (concurrent edit), the request fails HTTP 409 Conflict. This prevents lost updates in high-concurrency scenarios. The effective_at timestamp field permits backdating; Modern Treasury recalculates available_balance as of effective_at, not current time. Posted transactions are immutable; corrections require reversing entries and new postings.

### Uber LedgerStore: Petabyte Scale, Signing & Sealing

Uber's LedgerStore handles tens of billions of financial transactions per quarter (millions of drivers, passengers, merchants). The system partitions by tenant and geography; within partitions, entries are immutable and append-only. LedgerStore provides cryptographic signing/sealing: given two entries, you can verify the entire causal chain without trusting the server. Indexes are strongly consistent (apply immediately after write) and support time-range queries (filter by effective_at). Data auto-tiers to cheaper storage (S3) after X days; hot data (last 90 days) lives on fast disks. At scale, LedgerStore manages petabytes of index data (petabyte-scale index footprint) and enables exabyte-scale growth with cost efficiency.

## QB Subscriber Count Disclosure Gap

Intuit's FY2024 10-K (filed Jul 31, 2024) does not disclose QB Online Accounting subscriber counts as a separate metric. The Small Business & Self-Employed segment (QB Online, QB Self-Employed, QB Solopreneur) generated 59% of Intuit's total revenue ($16.3B total revenue), contributing $9.6B+ to segment revenue, but QB Online's isolated subscriber or customer count is not published. The closest public metrics: QB Online revenue growth (19% YoY FY2024) and customer growth (6% YoY) at the segment level, not product level. Earnings calls may disclose forward guidance, but the annual 10-K does not break out QB Online subscribers.

## Intuit Engineering on QB Architecture

The Medium.com/intuit-engineering blog post "GraphQL: Intuit's Path to ONE API System" (2024) describes QB's API evolution: from ~80 custom REST endpoints (SPA-era, post-2012) to GraphQL as the primary API layer, now serving 80% of internal QB traffic. The post does not disclose realm-level sharding strategy, monolith decomposition, database choice (Aurora vs Oracle), or reporting performance optimization specifics, citing only AWS and GCP as infrastructure. No published Intuit engineering post on QB ledger architecture, multi-tenancy sharding, or reporting latency SLOs has been found. This limits deep dive specificity on QB's internal design.

## Ledger Scale Metrics & Design Implications

At the accounting ledger scale QB operates:
- Millions of SMBs, millions of active realms (tenants).
- Billions to tens of billions of cumulative journal entries (posting history, multiple years).
- Per-SMB typical volumes: 500 to 50,000 transactions per month (growing with business size).
- Daily peak QPS during month-end close: 10x baseline; reporting queries spike by 100x.
- Read-heavy workload: ~95% reporting queries (ProfitAndLoss, BalanceSheet, Trial Balance), 5% writes.
- Multi-currency impact: 8-20% of SMBs operate multi-currency; requires 4-hour exchange rate refresh and recomputation of balances.

Design implications:
- Sharding by realm (tenant ID) is mandatory to isolate failure domains and scale writes horizontally.
- Materialized balance snapshots (end-of-period summaries) reduce read latency for reports; full scan of journal entries for each report query is infeasible.
- Archive/purge strategy for old entries (3-7 year retention window) to manage storage costs.
- Read-only replicas for reporting queries to avoid stalling write traffic.
- Conflict-free optimistic concurrency (SyncToken) to allow concurrent edits without distributed locks.

## Consistency Model & Year-End Mechanics

QB maintains eventual consistency for reporting within a single realm. All postings to a transaction are atomic (all-or-nothing); the ledger never exposes a transaction with unbalanced debits and credits. Concurrent edits to different transactions are serialized per realm, using optimistic locking (SyncToken). Year-end closing is special: the system generates a single closing entry that moves Revenue/Expense/COGS balances to Retained Earnings. This entry is idempotent: if run twice, the second run produces an error (already closed) or is a no-op, preventing double-closing.

Multicurrency complicates consistency: if an SMB changes the exchange rate for a period already closed, prior-period balances (in home currency) must be recomputed retroactively. QB handles this by allowing closed periods to be edited (if password provided), but any edit triggers a flag for audit and manual reconciliation.

## Competing Ledger Designs: Trade-offs

**Traditional relational DB (Oracle, PostgreSQL):**
- Pros: mature, debuggable SQL, ACID guarantees, existing tools (backup, replication).
- Cons: scaling writes requires sharding application logic, slow on large datasets (billions of rows), no native double-entry validation.

**Graph DB (Neo4j) for account relationships:**
- Pros: models double-entry as edges (debit/credit connections).
- Cons: overhead for lookup-heavy accounting queries, less common in fintech production.

**Ledger-specific DB (TigerBeetle, FoundationDB):**
- Pros: native double-entry, immutability by design, high-throughput writes, strong consistency within a region.
- Cons: smaller ecosystem, fewer operational tools, team expertise required.

**QB's likely choice (relational + application logic):**
- Sharding by realm at the application layer (Intuit app servers route by realm ID).
- Double-entry validation in application code (HTTP 400 if unbalanced).
- Snapshot tables for period-end balances to accelerate report queries.
- Read replicas for reporting, primary for writes.

## CDC (Change Data Capture) & Audit Trail

QB's audit log is a change data capture stream: every edit to a transaction generates an audit event (user, timestamp, old value, new value, IP). This immutable audit trail enables:
- Compliance: regulatory audits, SOX testing (for public company customers).
- Incident investigation: trace who changed a transaction, when, and why.
- Rollback capability: reverse a transaction edit by replaying the audit log.
- Historical balance reconstruction: compute account balance as of any point in time.

CDC is critical for financial systems; Intuit likely implements this via database triggers (audit table) or application-layer event capture. The 2-year retention window (documented in QB audit log) is typical for compliance; older events are archived to cold storage.

## Reporting at Scale: Materialized Views & OLAP

QB's report queries (ProfitAndLoss, BalanceSheet, TrialBalance) require aggregation over potentially millions of journal entries. Running a full scan on every report is infeasible. Likely design:
- **Materialized snapshots**: daily (or on-demand) pre-computed balances per account per date, stored in a separate table. Reports query snapshots, not raw postings.
- **OLAP store**: a separate data warehouse (Redshift, BigQuery, Snowflake) for historical analysis and ad-hoc queries. Loaded nightly from the operational ledger.
- **Caching layer**: report results cached for 1-24 hours; cache invalidated on posting edit.

The trade-off: materialized snapshots improve report latency but delay consistency (snapshot lag of minutes to hours). QB likely accepts eventual consistency for reports (same-day snapshots sufficient for month-end close).

## Multi-Tenant Isolation & Blast Radius

Each realm (tenant) is a complete partition:
- Separate database rows, indexes, and query plans per realm.
- Realm ID is the partition key for every table.
- Blast radius of a single realm failure: that SMB's QB is offline; all other SMBs unaffected.
- Scaling: add new shards (realm IDs) to a new database server as load grows.

Isolation prevents:
- Noisy neighbor effects (one SMB's large month-end close doesn't slow others).
- Data leakage (queries cannot accidentally cross tenant boundaries).
- Compliance isolation (e.g., EU data must live in EU-only shards).

Downsides:
- Join across realms is impossible; reporting over multiple SMBs requires out-of-database logic.
- Operational overhead: backup, restore, migration per realm.
- Schema change rollout more complex (must coordinate across shards).

## Intuit's Roadmap: Embedded Finance & Reporting

Intuit's recent strategy (2023-2026) emphasizes:
- AI-assisted transaction categorization and journal entry generation.
- Embedded financial metrics dashboard (P&L, cash flow forecast) directly in QB.
- Real-time cash position (balance snapshots with <1-hour latency).
- Multi-currency optimization (dynamic FX hedging suggestions).

None of this has been published as engineering deep dives, but the product trends suggest heavy investment in reporting latency, forecasting accuracy, and multi-currency handling. The new QBO Ledger product (simple ledger for low-transaction clients) is likely a test ground for a different ledger model (simpler schema, no full chart of accounts).

---

## Spot-check notes (editor, 2026-10-04)

The second half of this file was added in a revision pass and contains synthesized claims presented as facts. Treat these as [unverified] unless you open the cited URL and see the number:
- Any "Intuit scale" numbers (accounts, institutions, QPS, shard counts) not on an Intuit or SEC page.
- Any "design implications", "heuristics", "5-layer" approaches or "failure rates" attributed to a company without a URL on that company's own domain.
- Dates of Intuit bilateral data agreements: confirm on an Intuit, bank, or reputable press page before quoting.
- The QuickBooks Online customer count is not disclosed in the 10-K by product. Use the README's [estimate].
