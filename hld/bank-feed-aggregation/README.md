# Bank feed aggregation

> One-line answer: a **refresh scheduler** turns connections into fetch jobs, and every job must take a token from a **per-institution token bucket** (plus a cap on bank calls in flight; a grant not used within 1 s is void, so a stalled or paused governor can only under-use the bank) shared by the whole fleet before a connector calls the bank, so 3 M users at one bank become a steady stream that bank allows, with interactive refreshes in a priority lane. Each fetch re-reads an overlapping window (the last 14 days), stores the raw response immutably, and upserts normalized transactions on a deterministic **fingerprint** (the bank's own id when it is stable, otherwise a hash of account, date, amount, cleaned description and an occurrence counter), so any retry or replay is a no-op. A **matcher** links each posted transaction to the pending one it replaces (the provider's link first, then amount, date and merchant rules), marks the pending one superseded, and emits added / modified / removed events. QuickBooks consumes only posted transactions. The thing that breaks first is the bank: its rate limit and its outages, so per-institution circuit breakers and a ramped catch-up served most-stale first keep a recovery from becoming a stampede.

Tier 3, problem #51 in [`hld/README.md`](../README.md). From the user's Intuit Principal / Staff practice list (2026-10). Not a reported candidate prompt. Same shape as Plaid, MX, Finicity and Yodlee. Sources: [`research/`](research/).

## Problem statement (as asked)

Bank feed aggregation. Crux: idempotent ingestion from thousands of institutions with per-institution rate limits, and deduplicating pending vs posted transactions.

Follow-ups that always come: a retry after a crash halfway through a write; a $45.00 pending charge that posts as $54.00 with a new id; one bank's limit shared by 3 M of your users; a bank that changes every transaction id after a migration; recovery after a 6-hour bank outage; two identical $5 coffees on the same day.

## Functional requirements

Core:
- **Connect.** A user links accounts at an institution through the institution's OAuth-based API (FDX, Financial Data Exchange) where it exists, or through a legacy channel (OFX Direct Connect, or credentials with a partner aggregator). We store tokens, never passwords where an API exists.
- **Refresh.** Fetch new transactions and balances on a schedule (1 to 4 times a day), on demand when the user asks, and when the institution or a partner sends a webhook.
- **Ingest idempotently.** Every fetch, retry and replay produces each real transaction exactly once in our canonical store.
- **Reconcile pending and posted.** A posted transaction replaces its pending version. Expired authorizations disappear. Consumers get a clean added / modified / removed stream.

Below the line: categorization ML and the QuickBooks "For Review" matching to invoices and bills (a consumer of this stream), payment initiation, investment and loan account details, building the bank-side APIs.

## Non-functional requirements

| Dimension | Target |
|---|---|
| Scale | ~30 M connected accounts [estimate] in ~15 M connections (~2 accounts each) across ~15k institutions. Top 20 institutions hold ~70% of accounts; the largest has ~3 M connections. ~60 M refreshes/day (avg ~700/s, peak ~3k/s), ~180 M bank calls/day. ~150 M new transactions/day, ~8 B rows re-read/day because of the 14-day overlapping window (120 M account fetches x ~70 rows) |
| Freshness | Every posted transaction visible within 24 h. Active connections p95 under 8 h stale (time since the last successful refresh; the bank's own posting time is not observable). On-demand refresh: p95 under 30 s, except during a declared institution surge |
| Rate limits | Never exceed any institution's agreed limit, fleet-wide. Breach of an agreement can cost the connection for every user at that bank |
| Correctness | Zero duplicate posted transactions in the canonical store. A pending item is either matched to its posted item or expires. Every change is traceable to a raw response |
| Availability | 99.9% for reads of already-ingested data. One institution's outage affects only its connections |
| Security | Tokens and credentials in a vault, encrypted with per-tenant keys. Least-privilege scopes. Access logged |

## What interviewers probe (the ladder)

1. A refresh worker crashes after writing half a page of transactions. The job retries. How do you avoid duplicates?
2. A $45.00 pending restaurant charge posts two days later as $54.00 with a new id. One transaction or two? What if there are two $45.00 pending charges?
3. Chase allows N requests per second for all of your traffic. 3 M users want a refresh at 9 AM Monday. Who waits?
4. A bank migrates its core system and every transaction id changes. What happens to dedup?
5. A bank's API is down for 6 hours. What do users see, and what happens when it recovers?
6. Two identical $5 coffees on the same day at the same shop, and the bank gives no ids. One or two?
7. Where do credentials live, and how does the move away from screen scraping change the design?

## Files

| File | What it is |
|---|---|
| [`solution.md`](solution.md) | Full HLD in flow-first form: one incremental diagram, one walkthrough per FR, deep dives that mutate the design, then nitty-gritty |
| [`diagrams.md`](diagrams.md) | The D1 to D12 diagram set |
| [`edge-cases.md`](edge-cases.md) | Every "what if" with a 60-second answer and a confidence box |
| [`deep-dives/refresh-scheduling-and-rate-limits.md`](deep-dives/refresh-scheduling-and-rate-limits.md) | The scheduler, priority lanes, the fleet-wide per-institution token bucket, spreading the daily refresh |
| [`deep-dives/idempotent-ingestion.md`](deep-dives/idempotent-ingestion.md) | Overlapping windows, raw store, fingerprints, occurrence counters, upsert semantics, replay |
| [`deep-dives/pending-to-posted-matching.md`](deep-dives/pending-to-posted-matching.md) | Linking pending to posted, amount changes, expiry, the event stream consumers see |
| [`deep-dives/connectors-and-credentials.md`](deep-dives/connectors-and-credentials.md) | FDX and OAuth APIs vs OFX vs scraping, the token vault, MFA, the CFPB 1033 rule |
| [`deep-dives/institution-outages-and-recovery.md`](deep-dives/institution-outages-and-recovery.md) | Circuit breakers per institution, catch-up without a herd, id migrations, health scoring |
| [`research/`](research/) | Raw web research notes with source links. Input to the files above, not study material |
| `bank-feed-aggregation.excalidraw` | My drawing. Missing until I draw it |
