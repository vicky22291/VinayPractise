# ledger

In-memory balances for merchant payouts. Card settlements arrive as deposits,
the platform moves money between merchant accounts (fees, connected-account
payouts), and the nightly payout job runs thousands of transfers on a thread
pool. Finance reconciles balances against the double-entry journal every
night.

```
ledger/accounts.py    Account, Accounts registry
ledger/journal.py     append-only double-entry journal
ledger/service.py     Ledger: open_account, deposit, transfer, balance, total
ledger/workers.py     run_batch(ledger, requests, workers=8)
ledger/reconcile.py   reconcile(ledger) -> Report(ok, problems)
ledger/errors.py      LedgerError and subclasses
cli.py                python3 cli.py   (simulates a busy payout night)
tests/                python3 -m unittest
```

Amounts are integers in cents. Python 3.11+, standard library only.
