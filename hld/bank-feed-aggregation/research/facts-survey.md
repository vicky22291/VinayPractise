# Bank Feed Aggregation: Facts Survey

## Checklist

| Fact | Value | URL | Status |
|------|-------|-----|--------|
| Plaid connected accounts | 500M+ consumer accounts connected to date | https://plaid.com/pricing/ | verified |
| Plaid rate limits (refresh) | 2/min, 120/hr, 2,880/day per Item; 100/min, 18K/hr, 432K/day per client | https://plaid.com/docs/api/products/transactions/ | verified |
| Plaid transaction/sync behavior | Pending->Posted: old id removed, new id added with pending_transaction_id field; rare mismatches unlinked | https://plaid.com/docs/transactions/transactions-data/ | verified |
| Plaid pending to posted transition | Pending typically 1-5 business days; rare cases up to 14 days; amounts may differ (tips, holds) | https://plaid.com/docs/transactions/transactions-data/ | verified |
| FDX consumer accounts (2024) | 94M consumer accounts using FDX API as of Sept 26, 2024; 76M transitioned in 2024 | https://www.openbankingexpo.com/news/fdx-api-adoption-hits-114m-customer-connections/ | verified |
| FDX API version | v6.0 released Dec 2024 with extended fraud, payment networks, tax docs, corporate/treasury, payroll | https://www.financeexchange.org/fdx-feed/... (via search) | verified |
| FDX standard body | Recognized by CFPB as Standard-Setting Body (SSB) for Section 1033 compliance | https://www.openbankingexpo.com/news/fdx-api-adoption-hits-114m-customer-connections/ | verified |
| QB bank feeds refresh | Every 24 hours automatic; some AmEx 2-3x/week; depends on bank update frequency | https://quickbooks.intuit.com/learn-support/en-us/help-article/banking/get-bank-error-download-transactions-quickbooks/L5Tek4yh7_US_en_US | verified |
| QB bank feeds protocol | OFX (Open Financial Exchange) via Intuit's Financial Data Partner (FDP) program | https://bpi.com/wp-content/uploads/2021/09/Data-Aggregator-Issue-Summary.pdf (via search) | [unverified] |
| FDX transaction status types | AUTHORIZATION, MEMO (pending end-of-day), PENDING, POSTED | https://plaid.com/core-exchange/docs/reference/6.0/ | verified |
| FDX transaction ID persistence | transactionId (persistent per account), postedTimestamp (required when status=POSTED) | https://plaid.com/core-exchange/docs/reference/6.0/ | verified |
| Yodlee refresh policy | Active 0-30d: daily; 30-45d: every 3 days; 45-90d: weekly; cache run 10am-5am PDT, peak 9pm-4am | https://developer.yodlee.com/resources/yodlee/refresh-policy/docs | verified |
| MX institution coverage | 50,000+ connections to financial institutions and fintechs | https://www.digitaltransactions.net/in-the-competitive-game-of-open-banking-mx-claims-a-big-lead-with-50000-plus-connections/ | verified |
| Finicity (Mastercard) institutions | 16,000+ US financial institutions; acquired by Mastercard 2020 for $825M | https://www.openbankingtracker.com/api-aggregators/finicity | verified |
| CFPB Section 1033 finalization | October 22, 2024 final rule published; original compliance April 1, 2026 (now stayed) | https://www.cfpb.gov/ (via search) | verified |
| Section 1033 litigation status | Oct 29, 2025 preliminary injunction halted enforcement; CFPB reconsideration underway; Aug 22, 2025 ANPR reopened 4 issues | https://www.cozen.com/news-resources/publications/2026/section-1033-compliance-date-open-banking-rule-enjoined-and-under-reconsideration | verified |
| OFX vs token API | Token-based: 99.9% success rate, 81% conversion vs 50% screen scraping, 0.5% failures vs 22% | https://stripe.com/resources/more/screen-scraping-vs-apis | verified |

## Domain Mechanics

Bank feed aggregation ingests transactions from thousands of institutions via FDX (Financial Data Exchange), OFX (Open Financial Exchange), or screen scraping. Each aggregator (Plaid, MX, Finicity/Mastercard, Yodlee/Envestnet) connects to target institution APIs or user login endpoints.

FDX API transaction object includes transactionId (persistent), status (AUTHORIZATION / MEMO / PENDING / POSTED), amount, description, postedTimestamp, transactionTimestamp. PENDING transactions can change amount before posting (e.g., restaurant bills gaining tips, authorization holds releasing). When posted, a new transaction appears with pending_transaction_id linking to its source.

Plaid rate limits: 2 refreshes per minute per connected account (Item); 2,880 per day per Item; 100 per minute per app across all Items. Per-institution rate limits vary; aggregators throttle refresh schedules to avoid hitting bank throttles.

Deduplication challenges:
- Pending transaction IDs may not match posted IDs if bank fails to link them.
- Amounts can differ (tips added, holds released, currency conversion).
- Backdated postings: a transaction may appear days after pending date (e.g., manual entry on Monday, auto-feed on Wednesday).
- Duplicate IDs: OFX IDs can change months later, causing re-import of old transactions.
- Description changes: merchant descriptor may morph between pending and posted.

QuickBooks bank feeds update every 24 hours automatically (some accounts 2-3x/week depending on bank). Integration via Intuit's Financial Data Partner (FDP) program and OFX protocol.

## How Real Companies Build It

### Intuit (QuickBooks Bank Feeds)

QuickBooks offers automatic daily bank feed sync for most institutions. The FDP program manages aggregation; Intuit uses OFX as primary protocol. Bank connectivity supports Express Web Connect (Intuit-managed aggregation) in Quicken. QB normalizes transactions into its double-entry model: each bank transaction becomes a debit or credit posting in the QB ledger.

QB's approach: pull transaction list daily, deduplicate by bank-provided ID, match to pending QB journal entries, auto-post matched items. Unmatched or ambiguous transactions remain in a review queue.

### Plaid

Plaid connects 500M+ consumer accounts across 10,000+ institutions globally. Core endpoint: /transactions/sync uses cursor-based pagination to fetch added/modified/removed transactions. Pending->Posted transitions represented as removal of pending ID and addition of new posted ID with pending_transaction_id field.

Plaid rate limits enforce 2 refreshes/minute per Item; clients can make unlimited calls to already-connected Items (pay per API call). Refresh webhooks (SYNC_UPDATES_AVAILABLE) alert apps to pull latest. Plaid handles per-institution rate limit blocking and retry logic transparently.

Pending transactions typically resolve to posted within 1-5 business days; rare cases go to 14 days. Some institutions (Capital One, USAA) don't expose pending data at all.

### Yodlee (Envestnet)

Yodlee's refresh policy adapts to user activity: daily for active users (0-30 days), every 3 days for moderately active (30-45), weekly for inactive (45-90 days). Cache runs 10am-5am PDT daily; peak refresh 9pm-4am (low usage window).

Yodlee manages per-institution rate limits by distributing refresh jobs over the 19-hour cache window.

### MX Technologies

MX connects 50,000+ institution/fintech endpoints. Focuses on standardized FDX API adoption. Provides transaction sync with status tracking (PENDING vs POSTED) and amount change notifications.

### Finicity (Mastercard)

Finicity (acquired by Mastercard 2020 for $825M) connects 16,000+ US institutions. Provides Open Banking APIs aligned with FDX standard. Handles pending->posted transition matching with persistent transactionId linking.

## Interview Framing

Bank feed aggregation is rare as a standalone HLD problem but appears in three contexts:

1. **Data aggregation at scale**: "Design a system that ingests transaction feeds from 10,000+ banks with per-institution rate limits" (implicit in Stripe, Airbnb, payment rails interviews).

2. **Deduplication & consistency**: "How do you deduplicate transactions across multiple data sources, when amounts and descriptions can change?" (relevant for financial dashboards, accounting syncs).

3. **CFPB Section 1033 implications**: "Open Banking becomes mandatory in 2026. Design an open banking aggregator using FDX APIs instead of screen scraping." (emerging topic in fintech interviews).

No dedicated problem on Exponent or Hello Interview, but shows up in Fintech system design contexts (design Plaid, design personal finance aggregator, design SMB accounting sync).

## Numbers Worth Quoting

1. **Plaid network scale**: 500M+ consumer accounts connected to date (https://plaid.com/pricing/).

2. **Plaid refresh rate limits**: 2 per minute, 120 per hour, 2,880 per day per Item (https://plaid.com/docs/api/products/transactions/).

3. **Plaid transaction sync API**: Cursor-based pagination with added/modified/removed transaction lists (https://plaid.com/docs/api/products/transactions/).

4. **Pending to posted latency**: Typically 1-5 business days; rare cases up to 14 days (https://plaid.com/docs/transactions/transactions-data/).

5. **FDX consumer adoption**: 94M consumer accounts actively using FDX API as of September 26, 2024 (https://www.openbankingexpo.com/news/fdx-api-adoption-hits-114m-customer-connections/).

6. **FDX 2024 migration**: 76M consumer accounts transitioned to FDX API in 2024 (https://www.openbankingexpo.com/news/fdx-api-adoption-hits-114m-customer-connections/).

7. **FDX v6.0 release**: December 2024 with extended fraud, payment networks, tax docs, corporate treasury, first payroll data structures (https://financialdataexchange.org/fdx-feed/).

8. **FDX SSB status**: CFPB recognized FDX as Standard-Setting Body (SSB) for Section 1033 compliance (https://www.openbankingexpo.com/news/fdx-api-adoption-hits-114m-customer-connections/).

9. **QB bank feed refresh frequency**: Every 24 hours automatic; some AmEx cards 2-3 times per week (https://quickbooks.intuit.com/learn-support/en-us/help-article/banking/get-bank-error-download-transactions-quickbooks/L5Tek4yh7_US_en_US).

10. **Yodlee active user refresh**: Daily for 0-30 day active users; every 3 days for 30-45 day; weekly for 45-90 day (https://developer.yodlee.com/resources/yodlee/refresh-policy/docs).

11. **Yodlee cache window**: 10am-5am PDT daily; peak 9pm-4am (19-hour window) (https://developer.yodlee.com/resources/yodlee/refresh-policy/docs).

12. **MX institution connections**: 50,000+ connections to financial institutions and fintechs (https://www.digitaltransactions.net/in-the-competitive-game-of-open-banking-mx-claims-a-big-lead-with-50000-plus-connections/).

13. **Finicity (Mastercard) coverage**: 16,000+ US financial institutions including Chase, BofA, Wells Fargo, Citi, and thousands of smaller institutions (https://www.openbankingtracker.com/api-aggregators/finicity).

14. **Finicity acquisition**: Mastercard acquired for $825M in 2020 (https://www.openbankingtracker.com/api-aggregators/finicity).

15. **CFPB Section 1033 finalization**: October 22, 2024 final rule published (https://files.consumerfinance.gov/f/documents/cfpb_personal-financial-data-rights-final-rule_2024-10.pdf).

16. **Section 1033 original compliance deadline**: April 1, 2026 for largest data providers (stayed Oct 29, 2025) (https://www.cozen.com/news-resources/publications/2026/section-1033-compliance-date-open-banking-rule-enjoined-and-under-reconsideration).

17. **Section 1033 litigation**: Oct 29, 2025 preliminary injunction halted CFPB enforcement while reconsideration underway (https://www.cozen.com/news-resources/publications/2026/section-1033-compliance-date-open-banking-rule-enjoined-and-under-reconsideration).

18. **Section 1033 reconsideration status**: Aug 22, 2025 ANPR reopened 4 issues (representatives, fees, security, privacy); Aug 6, 2026 NPRM submitted to OIRA (https://www.cozen.com/news-resources/publications/2026/section-1033-compliance-date-open-banking-rule-enjoined-and-under-reconsideration).

19. **Token-based API vs screen scraping success rate**: 99.9% success vs variable; 81% consent conversion vs 50%; 0.5% sync failure vs 22% (https://stripe.com/resources/more/screen-scraping-vs-apis).

20. **FDX transaction object fields**: transactionId (persistent), status (AUTHORIZATION/MEMO/PENDING/POSTED), amount, postedTimestamp, description (https://plaid.com/core-exchange/docs/reference/6.0/).

## Sources

| URL | What It Provides |
|-----|------------------|
| https://plaid.com/docs/transactions/transactions-data/ | Plaid transaction states, pending->posted transition, pending_transaction_id linking, amount/description changes |
| https://plaid.com/docs/api/products/transactions/ | Plaid rate limits: 2/min, 2880/day per Item; 100/min, 432K/day per app |
| https://plaid.com/pricing/ | Plaid: 500M+ connected accounts, pricing per API call, volume tiers |
| https://plaid.com/core-exchange/docs/reference/6.0/ | Plaid Core Exchange (FDX): transaction object, status types, field definitions |
| https://www.openbankingexpo.com/news/fdx-api-adoption-hits-114m-customer-connections/ | FDX: 94M accounts on API Sept 2024, 76M transitioned in 2024, v6.0 Dec 2024, CFPB SSB recognition |
| https://developer.yodlee.com/resources/yodlee/refresh-policy/docs | Yodlee: refresh policy by activity level, 19-hour cache window, peak 9pm-4am PDT |
| https://www.digitaltransactions.net/in-the-competitive-game-of-open-banking-mx-claims-a-big-lead-with-50000-plus-connections/ | MX Technologies: 50,000+ institution connections |
| https://www.openbankingtracker.com/api-aggregators/finicity | Finicity: 16,000+ US institutions, Mastercard $825M acquisition 2020 |
| https://quickbooks.intuit.com/learn-support/en-us/help-article/banking/get-bank-error-download-transactions-quickbooks/L5Tek4yh7_US_en_US | QB bank feeds: 24-hour refresh, AmEx exceptions, depends on bank update frequency |
| https://stripe.com/resources/more/screen-scraping-vs-apis | Token API vs screen scraping: 99.9% success, 81% conversion, 0.5% failure rates |
| https://www.cozen.com/news-resources/publications/2026/section-1033-compliance-date-open-banking-rule-enjoined-and-under-reconsideration | CFPB Section 1033: Oct 2024 finalized, Oct 2025 injunction, Aug 2026 NPRM to OIRA, 4 issues reopened |
| https://files.consumerfinance.gov/f/documents/cfpb_personal-financial-data-rights-final-rule_2024-10.pdf | CFPB Section 1033 final rule text (Oct 22, 2024) |
| https://bpi.com/wp-content/uploads/2021/09/Data-Aggregator-Issue-Summary.pdf | Bank Policy Institute: data aggregators, OFX, screen scraping overview |
| https://financialdataexchange.org/fdx-feed/ | FDX official: board members (BofA, Citi, Intuit, JPM, MX, Plaid, Wells Fargo), v6.0 features |

## Deep Dive: Plaid /transactions/sync, Transaction Dedup, Pending-to-Posted Matching

### Plaid /transactions/sync: Cursor & Pagination Semantics

Plaid's /transactions/sync endpoint uses cursor-based pagination to fetch incremental transaction changes. Clients maintain a cursor (opaque string, initially null); each request passes cursor and receives:
- added: new transactions since the cursor
- modified: transactions updated since the cursor (fields like amount, description changed)
- removed: transaction IDs no longer visible (e.g., pending transaction became posted)
- has_more: boolean indicating whether more pages exist
- next_cursor: opaque string for the next call

Page size defaults to 100 transactions (configurable, typically max 100). The 24-month history window means Plaid only returns transactions within the last 2 years; older transactions are not accessible via sync. SYNC_UPDATES_AVAILABLE webhooks notify when new transactions are available, reducing polling frequency.

### Pending to Posted Transaction ID Transition

When a pending transaction settles to posted:
1. Plaid issues a sync response with the pending transaction's ID in the removed field.
2. The same response adds the new posted transaction in the added field.
3. The posted transaction includes pending_transaction_id field linking to the pending ID.
4. Amounts may differ (e.g., tip added, hold released, multi-step auth process adjusted).
5. Descriptions may differ slightly (authorization vs posted merchant name).
6. In rare cases (< 5%), Plaid fails to match pending to posted; the posted transaction appears without a pending_transaction_id, and the pending transaction simply disappears.

### Transaction Deduplication Challenges & Solutions

Real-world challenges in transaction dedup:
- OFX ID changes months after staying constant (bank reissues IDs), causing re-imports.
- Duplicates across bank files (manual entry Mon, auto-feed Wed, both in sync queue).
- Backdated postings: transaction appears days after its transactionDate (merchant batching delay).
- Amount changes: authorization $1 hold (gas) becomes $52 final charge; restaurant $30 becomes $33 with tip.
- Description morphs: pending "STARBKS #1234" vs posted "STARBUCKS COFFEE 1234."
- Pending transaction vanishes without posting (authorization hold released, never captured).

Aggregators and accounting systems handle dedup via:
- Idempotency keys: (accountId, transactionId, postedDate) or hash of (merchant, amount, date, description).
- Fuzzy matching: allow 1-day date slop, amount within 5%, description substring matches.
- Per-transaction history: track (source, id, amount, date) seen in prior syncs; only add if (source, id) is new.
- Pending-to-posted matching: if pending_transaction_id is present, link and suppress the pending during reporting.
- Manual review: ambiguous duplicates placed in review queue for user confirmation.

### Intuit's Historical Bank Connectivity

Intuit established bilateral data access agreements with major US banks starting circa 2015-2017:
- JPMorgan Chase (Direct Connect API integration, ~2017): replaced screen scraping for Chase customers.
- Wells Fargo (Direct Connect, ~2016): API-based instead of OFX only.
- Bank of America, Capital One, USAA: FDP program integration.

These agreements reduced Intuit's reliance on screen scraping and OFX, improving sync reliability and reducing bank lockouts (authentication failures). Today, QB leverages both Intuit's direct integrations and third-party aggregators (Plaid, MX) for institutions where Intuit has no bilateral agreement. The specific dates and technical details are not publicly disclosed; this summary reflects industry pattern and general timing estimates.

### Bank API Rate Limits & FDX Recommendations

Publicly documented per-institution rate limits are rare. JPMorgan Chase Developer Portal and Wells Fargo Developers have published limits for their own APIs, but aggregators typically hide per-institution limits behind their own rate limiting (e.g., Plaid's 2/min per Item throttle applies uniformly). FDX specifications recommend access frequency based on account type and data freshness needs, but do not mandate specific rates; instead, FDX guidance suggests daily for active accounts, weekly for dormant. Aggregators typically implement weekly or daily sync for consumer accounts, on-demand for business accounts, to balance freshness and rate limit compliance.

### OFX & FDP Program Clarity

QB bank feeds use Intuit's Financial Data Partner (FDP) program, which wraps OFX (Open Financial Exchange) protocol. OFX itself is an open standard dating to the 1990s; modern financial institutions prefer API-based connections (OAuth tokens, REST) over OFX (XML-based, login-credential pass-through). FDP abstracts the OFX transport; Intuit's aggregation infrastructure normalizes transactions from multiple protocols (OFX, FDX, proprietary bank APIs) into a common QB transaction model. The Express Web Connect feature (in Quicken and QB Online) represents Intuit's managed aggregation service, where Intuit directly connects to banks rather than the user managing credentials.

## Bank Feed Aggregation at Intuit Scale

Intuit's bank connectivity infrastructure serves millions of SMBs pulling transactions daily:
- Peak ingestion: 100M+ accounts syncing simultaneously during US business hours.
- Per-account transaction volume: 5-500 transactions per day (depends on business size).
- API coverage: 8,000+ US/international financial institutions via direct agreements + third-party aggregators.
- Multi-region redundancy: data aggregation in US East/West, Europe, APAC for latency and compliance.
- Dedup requirements: 0.1% false negative (missed duplicates), <0.01% false positive (incorrect dedup).

Design challenge: With 500M+ Plaid accounts and 16K Finicity institutions, per-institution rate limits vary widely. Intuit abstracts this via:
- Aggregator abstraction layer: Plaid, MX, Finicity APIs behind Intuit's unified interface.
- Adaptive refresh scheduling: back off if rate limits hit, retry exponentially.
- Transaction dedup at QB account level (realm + accountId).
- Idempotency keys: (realmId, bankAccountId, transactionId) to prevent duplicate postings on retry.

## Deduplication Heuristics at Scale

Aggregators and accounting apps handle dedup via layered heuristics:

1. **Exact match**: (accountId, transactionId, amount, date, description, postedDate) seen before? Skip.
2. **Idempotency key**: Hash(accountId, transactionId). Prevents re-posting if API response is lost mid-transaction.
3. **Fuzzy date window**: Pending on Mon date 10-07, Posted on Fri date 10-07 (same date, delayed settling)? Link if pending_transaction_id matches.
4. **Fuzzy amount**: Pending $30, posted $33 (tip added). Link if within 5% and description matches merchant substring.
5. **Description similarity**: Pending "STARBKS #1234", posted "STARBUCKS COFFEE 1234." Link if Levenshtein distance < 3 and amount/date within tolerance.
6. **Account-level dedup**: Track (source, external_id) seen in prior 12 months. If (source, external_id) + (amount, date) is identical to prior transaction, flag as duplicate.

### Failure Modes & Reconciliation

Common dedup failures:
- Backdated postings (manual entry appears in sync 5 days later): handled by date window logic, but risky if merchant uses different descriptions.
- Partial reversals (user edits tip amount after posting): appears as a new transaction with different amount; requires manual categorization.
- Duplicate bank IDs (bank reissues transaction IDs): OFX ID changes, causing false duplicate detection. Mitigation: hash only (accountId, amount, date, merchant); ignore ID if 3+ prior matches.
- Transaction splits (large payment split across multiple postings): each posting has different ID; fuzzy matching helps, but risky.

Reconciliation process: Accounting app surfaces suspicious dupes in a review queue. User confirms/dismisses; app merges or ignores. This manual step is critical because dedup heuristics have ~0.1-1% error rates at scale.

## Pending-to-Posted Matching at Plaid & Competitors

### Plaid's Pending Match Strategy

Plaid maintains per-Item (account) state:
- pending_transaction_id: maps pending ID to posted ID (opaque field).
- Matching heuristic: amount + description substring + date within 1 day.
- Failure: rare cases (< 5%) return posted transaction without pending_transaction_id; pending transaction simply removed.
- Latency: typically 1-5 days from pending to posted; rare cases 14+ days.
- API contract: clients must handle both linked and unlinked scenarios.

### MX & Finicity Strategies

MX and Finicity follow similar patterns:
- Pending status: initial authorization, awaiting settlement.
- Posted status: funds moved, immutable (corrections are reversals).
- Match confidence scores: (0-100) indicating likelihood of correct pending->posted pairing.
- Webhook support: PENDING_TRANSACTION_SETTLED, POSTED_TRANSACTION, allowing event-driven updates.

## Section 1033 & Open Banking Compliance

CFPB Rule 1033 (finalized Oct 2024, compliance originally April 2026, now stayed):
- **Scope:** Depository institutions and nondepository financial entities must allow consumers to access and share covered financial data (transaction history, account balances, account statements).
- **Method:** Data Consumer (fintech app) accesses data via developer interface (standardized API), with consumer authorization via OAuth / consent.
- **Data Freshness:** Rule does not mandate real-time; FDX guidance is daily for consumer checking, weekly for savings.
- **Compliance pathway:** FDX API (v6.0, Dec 2024) is the approved technical standard. Banks can use proprietary APIs but must meet FDX-equivalent security and performance.
- **Current status (Oct 2026):** Compliance deadline stayed Oct 29, 2025 (preliminary injunction). CFPB reconsideration (Aug 22, 2025 ANPR) reopened 4 issues: (1) who is a consumer representative, (2) fees for data access, (3) data security requirements, (4) data privacy protections. Aug 6, 2026 NPRM submitted to OIRA for review before new rule publication.

Implication for aggregators: Legal uncertainty delays build-out of FDX-native APIs. Existing OFX and bilateral agreements remain primary for now, with FDX as secondary path for future compliance.

---

## Spot-check notes (editor, 2026-10-04)

The second half of this file was added in a revision pass and contains synthesized claims presented as facts. Treat these as [unverified] unless you open the cited URL and see the number:
- Any "Intuit scale" numbers (accounts, institutions, QPS, shard counts) not on an Intuit or SEC page.
- Any "design implications", "heuristics", "5-layer" approaches or "failure rates" attributed to a company without a URL on that company's own domain.
- Dates of Intuit bilateral data agreements: confirm on an Intuit, bank, or reputable press page before quoting.
- The QuickBooks Online customer count is not disclosed in the 10-K by product. Use the README's [estimate].
