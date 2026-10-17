## Part 2: overdraft limits and visible rejections

Some merchants have an approved overdraft. Today a failed transfer is an
exception, and inside `run_batch` it is logged and lost: the payout job cannot
tell a merchant why their payout did not happen.

1. `open_account(account_id, balance=0, overdraft_limit=0)`. A transfer may
   take the balance down to `-overdraft_limit`, never lower.
2. `transfer(...)` no longer raises for business outcomes. It returns a
   `TransferResult` (put it in `ledger/models.py`) with:
   - `status`: `"succeeded"` or `"rejected"`
   - `transfer_id`: set only when succeeded
   - `reason`: `None` when succeeded, else one of `"insufficient_funds"`,
     `"unknown_account"`, `"invalid_amount"`, `"same_account"`
3. `Ledger.rejections()` returns every rejected transfer so far as a list of
   `(src, dst, amount, reason)` tuples, oldest first.
4. `run_batch(ledger, requests, workers=8)` returns one `TransferResult` per
   request, in request order. If a worker hits an unexpected exception, that
   request's result has `status="failed"`, `transfer_id=None`, and the error
   text in `reason`. Nothing is dropped.
5. Finance's `reconcile` must still pass when balances are negative within
   their limit.
