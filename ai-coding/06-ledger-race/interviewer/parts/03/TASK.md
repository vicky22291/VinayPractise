## Part 3: idempotency keys

The payout job retries the whole batch when it crashes halfway, and merchants
were paid twice. Callers already pass `idempotency_key`, but the ledger ignores
it.

Make `transfer(src, dst, amount, idempotency_key=...)` behave like Stripe's
API:

1. Same key and same `(src, dst, amount)`: return the first call's
   `TransferResult` (equal in every field) and move no money. This includes a
   rejection: a retry of a rejected transfer returns the same rejection, even
   if the account has money now.
2. Same key with different parameters: raise
   `ledger.errors.IdempotencyKeyReused`.
3. Several concurrent calls with the same key: money moves once, and every
   caller gets the same result. A caller that arrives while the first is still
   running waits for it.
4. No key: no deduplication, as today.

Before you code: how long would you keep keys, and where would they live in a
real system?
