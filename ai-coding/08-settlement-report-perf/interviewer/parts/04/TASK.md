## Part 4: defend it

Write `PERF.md` (half a page) and be ready to talk it through:

1. Complexity before and after, in N transactions, M merchants and C
   currencies: round trips, CPU and memory.
2. The next bottleneck at 10 times today's volume, and how you would know you
   had hit it.
3. Would you push the aggregation into SQL
   (`GROUP BY merchant_id, currency`)? What could change, and what would you
   need to prove first?
