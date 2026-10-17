## Part 4: numbers, more operators, review, explain

1. `amount` is an integer in the smallest currency unit (cents). Rules compare
   numbers with integer literals, which may be negative: `amount > 50000`.
2. Operators are `==`, `!=`, `>`, `>=`, `<`, `<=`.
   - `==` and `!=` compare two values of the same type.
   - The ordering operators compare two numbers only.
   - Any comparison between different types is false, for every operator.
     Booleans are not numbers.
3. Either side of a comparison may be a field, so `card_country != ip_country`
   works.
4. A comparison that mentions a field missing from the transaction is false,
   for every operator, including `!=`.
5. New action `review`, alongside `accept` and `block`.
6. Add `explain(txn, rules)` to `radar/engine.py`. It returns an object with
   `action` and `rule_id` (`None` when no rule matched). `evaluate` keeps
   returning just the action string.
