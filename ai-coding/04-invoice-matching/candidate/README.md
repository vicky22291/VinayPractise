# recon

Nightly job that matches incoming bank payments to open invoices, so finance
knows which invoices are paid. Output goes into the reconciliation email.

```
recon/models.py    Invoice, Payment, Match
recon/parsing.py   parse_payment, parse_invoice, read_lines
recon/matcher.py   reconcile(payments, invoices) -> list of lines
recon/report.py    format_match, summary
recon/export.py    CSV for the finance ledger import
cli.py             python3 cli.py data/payments.txt data/invoices.txt [--csv out.csv]
tests/             python3 -m unittest
```

Python 3.11+, standard library only.
