# payouts

Builds the daily settlement report. Finance pays merchants from it and diffs it
against the ledger byte for byte.

```
payouts/report.py   build_report(store, day) -> str (CSV)
payouts/fx.py       convert(store, amount, base, quote, day)
payouts/models.py   Merchant, BalanceTransaction, FxRate
payouts/store.py    the database (in memory here). Every method is one round trip
payouts/sample.py   seeded sample data
payouts/batch.py    report text -> payout instructions (reads the report format)
payouts/cli.py      python3 -m payouts.cli --merchants 200 --transactions 20000 > report.csv
tests/              python3 -m unittest
```

Python 3.11+, standard library only.

Report format: one line per merchant and currency the merchant took payments in
that day, sorted by merchant id then currency, then one `TOTAL` line per payout
currency. `payout_amount` is in the merchant's payout currency.
