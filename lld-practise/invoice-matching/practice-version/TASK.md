# Payment and invoice reconciliation: stage 1

Timebox: 50 minutes coding plus 10 minutes discussion. Implement this in Java.
Choose a simple method or CLI; an HTTP server is optional.

Implement reconcile(List<String> payments, List<String> invoices). Return one result per payment in input order.

Input formats:

- Payment: "<payment_id>,<amount_minor>,<memo>". The memo can be empty or contain commas.
- Invoice: "<invoice_id>,<amount_minor>,<due_date>". IDs are unique and formatted INV- followed by digits. Dates are YYYY-MM-DD.
- Amounts are nonnegative integers in the smallest currency unit.

Match each payment to the first still-open invoice named in its memo. An invoice can be matched once per batch. Match a whole invoice ID: INV-12 must not match INV-1. At this stage, invoice and payment amounts need not agree.

Example invoices:

```text
INV-1,500,2026-11-10
INV-12,700,2026-11-12
```

Example payments:

```text
p1,500,Paying INV-12, thanks
p2,500,Paying INV-1
p3,700,Paying INV-12 again
```

Expected results:

```text
payment p1 (amount 500) pays invoice INV-12 due 2026-11-12
payment p2 (amount 500) pays invoice INV-1 due 2026-11-10
payment p3 (amount 700) has no matching invoice
```

Clarify how to handle malformed input and ambiguous memo boundaries before implementing. Add your own tests for memo parsing, exact IDs, order, and already-matched invoices.

This is an original Java practice version inspired by publicly reported reconciliation rounds. It is not Stripe's official prompt.
