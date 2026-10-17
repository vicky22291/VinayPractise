# invoicing

Totals invoices in any supported currency and charges them through the payment processor.

```
invoicing/models.py      LineItem, Card, Invoice
invoicing/totals.py      subtotal, tax, invoice_total
invoicing/currency.py    format_amount, rate providers, convert
invoicing/processor.py   ProcessorClient: POST /v1/charges, retries timeouts
invoicing/transport.py   FakeProcessor: in-memory processor for tests and the CLI
invoicing/service.py     bill(invoice, card, client)
cli.py                   python3 cli.py examples/invoice_jpy.json examples/rates.json
tests/                   python3 -m unittest
```

Money is an `int` in the smallest currency unit. Python 3.11+, standard library only.
