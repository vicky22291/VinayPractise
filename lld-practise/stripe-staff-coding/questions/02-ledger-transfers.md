# 2. Ledger transfers and reversals

**Timebox:** 50 to 60 minutes. Implement an in-memory ledger. Store all amounts as integer minor units.

## Stage 1: Transfer

Implement accounts and a transfer operation that moves money from one account to another.

Rules:

- Accounts have an ID, currency, and balance.
- Amount must be positive. Source and destination must use the same currency.
- Reject a transfer that would make the source balance negative.
- A successful transfer debits the source and credits the destination by the same amount.
- A failed transfer changes neither balance.

Choose and explain how a caller can inspect the result of a transfer.

## Stage 2: Durable history and retries

Represent each successful transfer as balanced debit and credit entries. Entries are immutable. Add an idempotency key so a client retry cannot transfer the same request twice; a key reused with a different request must fail.

## Stage 3: Reversal and concurrency

Add a reversal operation that corrects a completed transfer without deleting or editing its original entries. Prevent duplicate reversals. Explain or implement how concurrent transfers preserve nonnegative balances and balanced ledger entries.

## Interviewer follow-ups

- What must be committed atomically?
- How do you avoid deadlocks if a transfer locks two accounts?
- How can balances be rebuilt or checked from the ledger?
- What happens if a client times out after the transfer commits?
- Which invariant would you alert on in production?
