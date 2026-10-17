## Part 2: match by amount

Many customers leave the memo empty. When the memo names no **open** invoice
(no ID at all, an unknown ID, or only invoices already paid in this batch),
match the payment to an open invoice whose amount equals the payment amount
exactly.

- If several open invoices have that amount, pick the earliest due date.
- If they also share a due date, pick the one that comes first in the invoice
  list. The invoice list is not sorted.
- A memo match always beats an amount match. If the memo names an open invoice,
  never look at amounts.
- An amount match closes the invoice, same as a memo match.
- The output line has the same format as a memo match.

Keep every earlier test passing.
