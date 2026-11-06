# Interviewer: reveal one stage at a time

## Stage 2: Exact amount fallback

Preserve memo matching. If no open invoice is named, match an open invoice with the exact payment amount. Select the earliest due date; break equal dates by invoice ID in lexical order. A valid memo match takes priority over amount matching.

## Stage 3: Tolerance fallback

Add a nonnegative tolerance in minor units. If memo and exact amount matching fail, consider open invoices within that amount tolerance. Choose the earliest due date, then invoice ID. Exact amount has priority over tolerance. Return which rule produced the match.

## Discussion

How does complexity grow with the number of payments and invoices? What do you index? What happens if a batch is retried, or two workers reconcile the same invoice? What would you log for a disputed match?
