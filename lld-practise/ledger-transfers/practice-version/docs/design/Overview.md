# Ledger transfer design

## Stage 1: model and atomic boundary

`LedgerController` handles HTTP DTOs. `LedgerService` validates and constructs transfers and entries. `LedgerRepository` owns account snapshots, transfer records, append-only entries and retry results under a single transaction lock. `Account`, `Transfer` and `Entry` are immutable records.

Money is `long` minor units; currencies are normalized three-letter codes. Initial balances must be nonnegative. A transfer amount is positive, the two accounts must differ and use the same currency, and the source must have sufficient funds. Destination overflow is checked before any writes. Each rejection changes neither balance nor history.

A successful transfer atomically changes both account balances, appends its two entries, saves the transfer, and records its retry result. The transfer UUID lets clients inspect the committed result after a lost response. There are no pending or partially committed transfers exposed by this local model.

## Stage 2: immutable history and retries

An entry is a signed account balance delta: a debit is negative and a credit is positive. Every transfer has exactly two entries in one currency whose sum is zero. Original entries remain untouched after a reversal. Returned entry lists are immutable snapshots.

Opening balances are explicit funding baselines stored on accounts, rather than transfers from another modeled account. Reconstruction is `openingBalance + sum(account entries)`. `/accounts/{id}/audit` compares that exact integer sum with the stored balance. In a full double-entry system, funding would also have a counter-account; this exercise scopes balanced entries to transfers and reversals.

An idempotency key binds the complete normalized request, including operation and account/transfer IDs, to its original immutable result. A retry after commit returns the same transfer even if it was subsequently reversed. A key with different arguments or a different operation returns 409. Failed operations do not reserve keys, so a reversal rejected for lack of funds can be retried after funding is restored.

“Durable history” here means append-only for the life of this in-memory ledger. Restart durability requires a database or write-ahead log. Do not treat an in-memory retry cache as crash-safe storage.

## Stage 3: reversal and concurrency

A reversal is a new full transfer from the original destination to the original source, with `reversalOf` pointing to the original. The original transfer gains a `reversedBy` link; its entries remain unchanged. A fresh reversal key cannot reverse an already reversed transfer. Replaying the first key returns its original result. Reversals of reversal records are rejected.

Reversals require the original destination to still have the money. If it has spent the funds, reject without adding entries or marking the original reversed. Product alternatives such as allowing debt or a pending recovery are outside this policy.

One repository lock covers reads and writes across all accounts. The balance check, destination overflow check, both balance changes, entries, reversal marker and retry record share the same atomic boundary. There is only one lock, so opposite-direction transfers cannot deadlock. This sacrifices throughput for clarity. A larger implementation can lock accounts in sorted UUID order, or use a database transaction with row locks and uniqueness constraints for idempotency keys and original-transfer reversals. Commit everything above in that transaction.

## Operational checks and tests

Alert if a transfer's entry sum differs from zero, an account goes negative, entry currency differs from account currency, or a stored balance differs from reconstruction. Sum across many accounts/entries with `BigInteger` to avoid audit overflow; the audit endpoint does this. A client timeout after commit is resolved by the same retry key, not a second transfer.

`LedgerServiceTest` covers balanced entries, rejection atomicity, arithmetic overflow, immutable snapshots, insufficient reversal funds, original-result replays, competing transfers, same-key races and competing reversals. `ExerciseApiTest` covers the HTTP journey and validation.
