## Part 2: refactor without changing a cent

`generate_invoice` is one long function. Split it into pieces you can test and
change on their own: for example the billing period, the seat segments,
proration, discounts, tax and line building. Your Part 1 tests stay green at
every step.

Keep the public API exactly as it is:

- `billing.invoice.generate_invoice(subscription, events, as_of)` returns a
  `billing.models.Invoice` with the same fields.
- `billing.models` and `billing.catalog` keep their names and constructors.

The interviewer will compare your output with invoices recorded from the old
code for 400 generated subscriptions. Every field of every invoice must match.

Commit in small steps. Tell the interviewer which step was the riskiest and how
you knew it was safe.
