# 2. Ledger transfers and reversals

**Language:** Java. **Timebox:** 50 to 60 minutes. Implement an in-memory ledger. Store all amounts as integer minor units.

## Stage 1: Transfer

Implement accounts and a transfer operation that moves money from one account to another.

Rules:

- Accounts have an ID, currency, and balance.
- Amount must be positive. Source and destination must use the same currency.
- Reject a transfer that would make the source balance negative.
- A successful transfer debits the source and credits the destination by the same amount.
- A failed transfer changes neither balance.

Choose and explain how a caller can inspect the result of a transfer.
