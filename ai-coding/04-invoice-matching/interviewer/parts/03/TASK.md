## Part 3: forgiveness tolerance

Finance will forgive small differences. Add an optional argument:
`reconcile(payments, invoices, tolerance=0)`. `tolerance` is an absolute amount
in cents. A negative tolerance raises `ValueError`.

When the memo names no open invoice, the payment may match an open invoice
whose amount is within `tolerance` of the payment amount, inclusive, in either
direction.

- An exact amount match always beats a tolerance match.
- Among tolerance candidates, pick the smallest difference, then the earliest
  due date, then the first in the invoice list.
- A tolerance match with a difference says so at the end of the line:

```
payment p3 (amount 490) pays invoice INV-7 due 2024-05-01 (forgiven 10)
payment p4 (amount 715) pays invoice INV-8 due 2024-05-02 (overpaid 15)
```

`forgiven` means the payment was short of the invoice. `overpaid` means it was
over. Exact matches and memo matches never get a suffix. With the default
`tolerance=0`, results are the same as Part 2.
