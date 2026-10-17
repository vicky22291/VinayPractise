# billing

Turns seat-based subscriptions into monthly invoices: plans, seats, mid-month
changes, trials, coupons and tax. Finance reconciles against its output.

```
billing/models.py     Plan, Coupon, Subscription, Event, Line, Invoice
billing/catalog.py    PLANS and COUPONS from fixtures/catalog.json
billing/loader.py     load_subscriptions(path)
billing/invoice.py    generate_invoice(subscription, events, as_of)
cli.py                python3 cli.py fixtures/subscriptions.json 2026-02-15
fixtures/             catalog and real-shaped subscriptions
tests/                (empty)
```

Money is an `int` in cents. An invoice covers the calendar month containing
`as_of`. Python 3.11+, standard library only.
