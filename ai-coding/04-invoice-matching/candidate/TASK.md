# recon: interview task

You own `recon`, the nightly job that matches incoming payments to open
invoices for finance. A teammate wrote the first version and moved teams. Read
the code and run the tests before you change anything. The interviewer adds
more parts as you finish each one. Nobody is expected to finish every part.

## Part 1: memo matching and the open tickets

Inputs are lists of strings.

- Payment: `"<payment_id>,<amount>,<memo>"`, e.g. `"p1,500,Paying off: INV-4"`.
  The memo is free text. It may be empty and may contain commas.
- Invoice: `"<invoice_id>,<amount>,<due_date>"`, e.g. `"INV-4,500,2024-04-01"`.
  Invoice IDs are `INV-` followed by digits and are unique. Due dates are
  `YYYY-MM-DD`.
- Amounts are non-negative integers in the smallest currency unit (cents).

`recon.matcher.reconcile(payments, invoices)` returns one line per payment, in
payment order:

```
payment p1 (amount 500) pays invoice INV-4 due 2024-04-01
payment p2 (amount 300) has no matching invoice
```

Rules:

1. A payment matches the invoice whose ID appears in its memo. IDs match
   exactly and as a whole: `INV-12` never matches `INV-1`.
2. If the memo names more than one invoice, the first one named that is still
   open wins.
3. Payments are processed in input order. An invoice can be paid once per
   batch: after a payment matches it, it is closed.
4. In this part the amounts do not need to agree. The memo is the customer
   telling us which invoice they paid.

Open tickets from finance:

- **RECON-101.** A payment with memo `Invoice INV-12` was applied to `INV-1`.
- **RECON-102.** The nightly batch crashed on a payment whose memo was
  `Paying off: INV-9, thanks!`.
- **RECON-103.** `INV-4` shows as paid by both `p1` and `p5`.

Two tests in `tests/` fail as well. Fix the tickets and the tests, add a test
for each ticket, and keep the other tests passing.
