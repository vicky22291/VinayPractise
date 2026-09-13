# Visa-scale payments + ledger + duplicate payment prevention

> One-line answer: a payment is a state machine (`created -> authorized -> captured -> settled`, with `reversed / refunded / failed` exits) that is driven by an orchestrator with at-least-once retries, and every effect along the way is made idempotent so the retries are safe: the API dedups on a client `Idempotency-Key` with a request fingerprint and a 24 h lock, each call to a card network or PSP carries a stable attempt id and is reversed on an unknown outcome, and every money movement is a balanced double-entry journal entry whose id is derived from `(payment_id, kind)` so the ledger rejects a second posting by unique index; the ledger is sharded by account, linearizable inside a shard, append-only with materialized balances, and reconciled T+1 against the rail as the last line of defence.

Tier 1, problem #8 in [`hld/README.md`](../README.md). Reported at Databricks as "design a payment system" and "game / playlist transaction service with retry-safe semantics", at Rippling as "prevent duplicate payments under load" and "multi-tenant payroll", at Stripe as "durable ledger" and "idempotent double-entry ledger", and at Google, Meta, Amazon as "design Venmo / PayPal". Stripe, Airbnb, Uber and TigerBeetle have published the reference mechanisms, so interviewers have a concrete answer in mind. See [`research/`](research/).

## Problem statement

Build the platform that a merchant, a payroll run, or a wallet app calls to move money: accept a payment request, charge the payer through an external rail (card network via an acquirer or PSP, or ACH), record every movement in a ledger that is always balanced and auditable, and never charge or pay anyone twice even though every client, every service, and every network in the path retries. Then scale it to card-network volume: tens of thousands of authorizations per second, with a p99 the cardholder does not notice, and no lost or duplicated money on any failure.

Two framings share the design and differ only in which box is "us":

| Framing | We own | The rail is | Timeout answer |
|---|---|---|---|
| Payments platform (Stripe, Rippling, Databricks prompt) | API, orchestrator, ledger, reconciliation | a PSP or acquirer we call over HTTPS, or an ACH file we submit | retry with the same key, or reverse |
| Card network (Visa framing) | the switch between acquirer and issuer, the clearing and settlement ledger | the issuer we forward ISO 8583 messages to | stand-in processing (STIP) plus reversal advice |

## Functional requirements

Core:
- Create a payment exactly once from the caller's point of view. A client retry with the same `Idempotency-Key` returns the original result; the same key with a different body is rejected.
- Drive the payment through the rail with a safe state machine: authorize, capture (full or partial), refund, cancel, reverse. Every transition is retry-safe and every unknown outcome is resolved, never guessed.
- Record every money movement as a double-entry journal entry: debits equal credits, entries are immutable, corrections are new entries. Balances (posted, pending, available) are derivable for any account at any point in time.
- Never let a constrained account go negative (wallets, prepaid, payroll funding accounts) even under concurrent payments.
- Reconcile the ledger against the rail's clearing and settlement reports, surface every break, and auto-remediate duplicates (refund) within T+1.
- Query payment status and account balance with read-your-writes for the caller; deliver webhooks at least once with an event id.

Below the line (say it out loud):
- Card data. PAN never enters this system; a tokenization vault (PCI scope) hands us a token. We store the token.
- Fraud and risk scoring. A synchronous call on the auth path with a 50 ms budget; a separate system.
- FX pricing, KYC / KYB, tax, disputes UI, the merchant dashboard. They read the ledger; they do not write it.
- Being the issuer. We do not decide whether the cardholder has funds; the issuer does.

## Non-functional requirements

| Dimension | Target |
|---|---|
| Scale | 10 k payments/s average, 65 k/s peak (Visa's published capacity claim). About 5 ledger lines per payment lifecycle, so 50 k lines/s average, 325 k/s peak |
| Latency | Our part of authorization p99 < 200 ms (the issuer round trip adds 100 ms to 2 s that we do not control). Ledger append p99 < 30 ms. Status read p99 < 50 ms |
| Correctness | Exactly-once effect per idempotency key. Zero unbalanced entries, ever. Zero negative balances on constrained accounts. Every payment reconciled by T+1 |
| Availability | Authorization path 99.999% (about 5 min/yr). Ledger writes 99.99%. Reconciliation and reporting 99.9% |
| Durability | RPO 0 for committed ledger entries (synchronous quorum across 3 AZs). RTO < 1 min in region, < 15 min cross region |
| Consistency | Linearizable inside one ledger shard (balance check + entry append are one transaction). Read-your-writes for the caller's status. Eventual for reporting, analytics, and webhooks |
| Audit | Reconstruct any balance as of any entry sequence number. Entries are append-only and hash-chained; retention 7 years |
| Multi-tenant | Tenant A can never read or move tenant B's money. Ledger shard key includes the tenant |

## What interviewers probe (the ladder)

1. The mobile client times out and retries. How do you avoid charging the card twice? Where does the idempotency key live, for how long, and what if the body differs?
2. Two requests with the same key arrive at the same millisecond on two API pods. Who wins, what does the other one return?
3. You called the PSP (or the issuer) and the socket died. Did the charge happen? What do you do in the next 100 ms, the next 10 s, the next day?
4. Show me the ledger entry for a $100 payment with a 2.9% + 30c fee. Why double entry and not a `balance` column?
5. One merchant is 5% of all volume. Its balance row gets 3,000 updates/s. What breaks and how do you fix it without breaking "never negative"?
6. The ledger primary dies after the commit but before the ack. What does the caller see? What does the retry do?
7. How do you know the ledger is right? What runs at night, what does it compare, what pages?
8. A user in Frankfurt pays a merchant in Seattle. Which region owns what, and what happens when one region goes dark?
9. Refund $30 of the $100 six days later. Partial capture. Chargeback. Where are the entries and what state is the payment in?
10. Prove this account's balance as of last Tuesday 14:00 to an auditor.
11. Payroll variant: 50 k employees paid via ACH in one run. The run crashes at employee 31,204. What happens on restart?
12. Black Friday is 10x. Which component do you scale first, and which one cannot be scaled by adding nodes?

## Files

| File | What it is |
|---|---|
| [`solution.md`](solution.md) | Full HLD, Bad / Good / Great ladders, nitty-gritty internals |
| [`diagrams.md`](diagrams.md) | The D1 to D12 diagram set |
| [`edge-cases.md`](edge-cases.md) | Every "what if" with a 60-second answer and a confidence box |
| [`deep-dives/idempotency-keys.md`](deep-dives/idempotency-keys.md) | The API dedup layer: key scope, fingerprint, in-progress lock, recovery points, 24 h TTL, concurrent duplicates |
| [`deep-dives/ledger-and-double-entry.md`](deep-dives/ledger-and-double-entry.md) | Accounts, journal entries, lines, posted vs pending vs available, invariants, sharding by account, cross-shard transfers via clearing accounts |
| [`deep-dives/hot-accounts-and-contention.md`](deep-dives/hot-accounts-and-contention.md) | The red node: single-row balance contention, append-only with snapshots, sub-account sharding, batching a la TigerBeetle |
| [`deep-dives/rails-timeouts-and-unknown-outcome.md`](deep-dives/rails-timeouts-and-unknown-outcome.md) | Card auth / capture / reversal over ISO 8583, STIP, PSP idempotency, ACH batch semantics, the payment state machine |
| [`deep-dives/reconciliation-and-audit.md`](deep-dives/reconciliation-and-audit.md) | Three-way reconciliation, break detection and aging, auto-remediation, hash chains, balance as of time T |
| [`deep-dives/durability-and-multi-region.md`](deep-dives/durability-and-multi-region.md) | Quorum commit, unknown commit on primary loss, home region per shard, region failover and fencing, in-flight payments |
| [`research/`](research/) | Raw web research notes with source links. Input to the files above, not study material |
| `payments-ledger.excalidraw` | My drawing. Missing until I draw it |
| `my-attempt.md` | My timed attempt before reading the solution |
