## Part 4: payouts to the bank

Merchants withdraw to their bank through `ledger/bank.py` (new file, a fake
bank API). Read it first. `Bank.send(payout_id, account_id, amount)` is
idempotent on `payout_id`. It can raise `BankDeclined` (no money moved) or
`BankTimeout` (the money may or may not have moved).

Add `Ledger.payout(payout_id, account_id, amount, bank)` returning a
`PayoutResult(status, reference)` (in `ledger/models.py`), where status is one
of `"paid"`, `"pending"`, `"declined"`, `"rejected"`:

1. **Reserve first.** Move the amount out of the account into the journal
   account `"payouts_pending"` before calling the bank, so concurrent
   transfers cannot spend it. Not enough money (same limit rule as transfers):
   `"rejected"`, and the bank is never called.
2. **Paid:** move it from `"payouts_pending"` to the journal account `"bank"`.
   `reference` is the bank's reference.
3. **Declined:** release the reservation back to the account.
4. **Timeout:** status `"pending"`; the money stays reserved.
5. **Retries are safe.** Calling `payout` again with the same `payout_id`
   never moves money twice. Same `payout_id` with a different account or
   amount raises `IdempotencyKeyReused`. Concurrent calls with the same
   `payout_id` move money once.
6. `Ledger.resolve_pending(bank)` retries every pending payout with the same
   `payout_id` and returns their `PayoutResult`s.
7. Do not hold an account's lock while waiting for the bank.
8. Finance's `reconcile` must still pass at every step.

Before you code: walk the interviewer through what can go wrong between "the
bank moved the money" and "our journal says so".
