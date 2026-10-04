# QuickBooks multi-tenant ledger

> One-line answer: every business transaction (invoice, bill, payment, journal entry) goes through one **posting engine** that turns it into a journal entry whose lines sum to zero, and appends it to an immutable journal in the **same database transaction** that updates per-account, per-month **period balance** rows. Each company (QuickBooks calls it a realm) lives entirely on one shard of a sharded relational store, so that transaction is a plain single-shard ACID (atomic, consistent, isolated, durable) commit and every company sees its own books strongly consistent. Edits never update a posted line: they post a reversal plus a new version. Reports over 10 years read at most 12 period rows per account (and per class or location combination) per year, plus day rows for one partial month, so a balance sheet is under 1 s whatever the history. A continuous verifier re-checks "debits equal credits" and "balances equal the sum of lines" per company, and heavy cross-company analytics run on a CDC (change data capture) copy, never on the ledger.

Tier 3, problem #50 in [`hld/README.md`](../README.md). From the user's Intuit Principal / Staff practice list (2026-10). Not a reported candidate prompt. Close cousin: [`../payments-ledger/`](../payments-ledger/) (a ledger for money movement, where this one is a general ledger for accounting). Sources: [`research/`](research/).

## Problem statement (as asked)

QuickBooks multi-tenant ledger. Crux: immutable double-entry postings that always balance, with per-tenant consistency and fast reports over years of history.

Follow-ups that always come: how you guarantee balance under retries and crashes; what an edit to last year's invoice writes; a balance sheet "as of" any date across 10 years; closed books; one tenant that syncs a million e-commerce orders a month; moving a tenant between shards.

## Functional requirements

Core:
- **Post.** Create, edit and void business transactions. Each becomes a balanced journal entry (debits equal credits, in home currency) against the company's chart of accounts.
- **Keep history immutable.** A posted line is never changed. Edits and voids post reversing entries. Every change is attributable (who, when, from which app) for audit.
- **Respect closed periods.** Postings dated on or before the company's closing date are blocked, or allowed only with an override that is logged.
- **Report fast.** Trial balance, balance sheet, profit and loss, and general ledger detail for any date range across the company's whole history, filtered by class, location or customer.

Below the line: bank feeds ([#51](../bank-feed-aggregation/)), payroll ([#29](../payroll-engine/)), sales tax engines, consolidation across companies, inventory costing (FIFO), the accountant's practice tools, money movement ([`../payments-ledger/`](../payments-ledger/)).

## Non-functional requirements

| Dimension | Target |
|---|---|
| Scale | ~8 M companies [estimate], ~4 M active in a month. ~2.4 B transactions/month (avg ~900/s, peak ~10k/s at month start and during bulk imports). ~3 lines per transaction, ~85 B lines/year. Largest companies: ~1 M transactions/month |
| Post latency | p99 under 300 ms for a normal transaction. Bulk imports are asynchronous |
| Report latency | Balance sheet or P&L over any range in 10 years: p99 under 1 s. General ledger detail: first page under 2 s |
| Consistency | Strong per company: a report after a post sees it (read-your-writes). Cross-company analytics: eventual, under 5 min |
| Correctness | Every journal entry balances. Every period balance equals the sum of its lines. Verified continuously, mismatch pages |
| Availability | 99.95% for posting and reports. A shard failure affects only that shard's companies |
| Durability | Acknowledged posts: RPO 0 within a region. Across regions: manual and API posts are acknowledged after the remote replica flushes (+8 to +67 ms), waiting at most ~1 s; past that the response says `durability: region` and the request is logged for re-drive. Imports re-driven from the source by watermark. If the remote lags more than 5 s, the cluster degrades to local-only acknowledgement and pages |
| Retention | All history kept for the life of the account, at least 7 years after close |

## What interviewers probe (the ladder)

1. How do you guarantee every entry balances, even with retries, partial failures and two apps posting at once?
2. The user edits an invoice from last March. What rows do you write? What does the March report say now?
3. Balance sheet as of any date over 10 years in under 1 s. What do you precompute, and what happens with a backdated entry?
4. The books are closed through December 31. A bank feed import arrives dated December 30. Now what?
5. One company syncs 1 M Shopify orders a month into the same two accounts. Where is the hot spot?
6. An accountant runs a report across 50 client companies. Where does that query go?
7. How do you move a company to another shard with zero downtime?
8. Multi-currency: the lines balance in euros but not in dollars after conversion. Who fixes the cent?

## Files

| File | What it is |
|---|---|
| [`solution.md`](solution.md) | Full HLD in flow-first form: one incremental diagram, one walkthrough per FR, deep dives that mutate the design, then nitty-gritty |
| [`diagrams.md`](diagrams.md) | The D1 to D12 diagram set |
| [`edge-cases.md`](edge-cases.md) | Every "what if" with a 60-second answer and a confidence box |
| [`deep-dives/posting-engine-and-balance-invariant.md`](deep-dives/posting-engine-and-balance-invariant.md) | From business transaction to balanced lines, idempotent posting, where the invariant is enforced, multi-currency rounding |
| [`deep-dives/edits-reversals-and-closed-periods.md`](deep-dives/edits-reversals-and-closed-periods.md) | Versioned transactions, reversal entries, voids, the closing date, backdated entries |
| [`deep-dives/fast-reports-period-balances.md`](deep-dives/fast-reports-period-balances.md) | Period balance rows, as-of queries, retained earnings computed at read, dimensions, the OLAP copy |
| [`deep-dives/tenant-sharding-and-hot-tenants.md`](deep-dives/tenant-sharding-and-hot-tenants.md) | Company-to-shard directory, shard moves with zero downtime, hot accounts, noisy neighbours |
| [`deep-dives/audit-trail-and-continuous-verification.md`](deep-dives/audit-trail-and-continuous-verification.md) | Audit log, tamper evidence, the continuous balance verifier, repair |
| [`research/`](research/) | Raw web research notes with source links. Input to the files above, not study material |
| `quickbooks-ledger.excalidraw` | My drawing. Missing until I draw it |
