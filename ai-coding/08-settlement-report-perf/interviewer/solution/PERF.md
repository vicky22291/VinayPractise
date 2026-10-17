# Settlement report: performance note (model answer)

N transactions in the day, M merchants, C = 6 report currencies, L ≤ C·M report lines.

| | Before | After |
|---|---|---|
| Round trips | 1 + M + C·M + C·N + (cross-currency N): about 1.26 M at N = 200k, over 30 min at 1.5 ms | 4: `merchant_ids`, `get_merchants`, `fx_rates`, `iter_transactions` |
| CPU | O(C·N) row visits plus a sort after every line: O(L²) | O(N + L log L) |
| Memory | O(L) lines, plus every id list per merchant | O(M + L): merchant table and one accumulator row per line. Flat in N |

**Kept on purpose:** each transaction is converted and rounded half-even on its
own, then summed. That is how the ledger booked it. Sum-then-round changes 1,112
of 2,000 converted lines on the test day. Also kept: merchants missing from the
table are skipped, names are not CSV-quoted. Both are worth a ticket, not a
silent change inside a performance PR.

**Next bottleneck at 10x (N = 2 M):** single-core Python CPU in the per-row
fold. Here 300k rows take about 2 s, generation included, so 2 M rows is
roughly 15 s. The Decimal conversion itself is only about 0.24 µs per row. Then
cursor throughput (about 200 MB per day). If M reaches millions, loading the whole merchant table
is the next cost. Know it from per-phase timings: rows per second on the cursor,
seconds in fold, seconds in render.

**SQL push-down:** `SUM(ROUND(net * rate))` in Postgres would not match:
`round(numeric)` breaks ties away from zero, and we round half-even. Equal output
needs a half-even rounding expression per row, then `SUM`. Before switching:
shadow both for 30 days, diff byte for byte, and reconcile totals to the ledger.
Formatting and sorting stay in Python.
