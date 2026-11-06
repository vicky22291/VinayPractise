# Interviewer: reveal one stage at a time

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
