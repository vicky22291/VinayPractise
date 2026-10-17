## Part 4: one payment, several invoices

Some customers pay several invoices with one transfer and name them all:
`"p9,800,Paying INV-1 and INV-2"`.

1. If the memo names two or more distinct open invoices, and the payment amount
   equals the sum of their amounts exactly, the payment pays all of them. List
   them in the order the memo names them:

   ```
   payment p9 (amount 800) pays invoices INV-1 due 2024-04-01, INV-2 due 2024-05-01
   ```

   All of them are closed.
2. Otherwise the Part 1 rule still applies: the first open invoice named wins.
3. An ID named twice in one memo counts once.

Finance also wants to know what is still owed. Add
`recon.matcher.open_after(payments, invoices, tolerance=0)`. It returns the IDs
of the invoices still open after the batch, in invoice-list order.
