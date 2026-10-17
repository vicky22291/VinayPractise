## Part 3: parentheses and bad rules

Rules can group with parentheses, nested to any depth:

```
(merchant_name == "Evil Corp" OR merchant_name == "Bad LLC") AND card_country == "NG"
is_3ds == false AND ((card_country == "BR") OR (ip_country == "BR"))
```

Outside parentheses the left-to-right rule from Part 2 still holds.

A rule that cannot be parsed (unbalanced parentheses, a missing value, an
unterminated string, an unknown symbol) is a bad rule. `evaluate` must check
**every** rule in the list before it decides anything. If any rule is bad,
raise `RuleSyntaxError` from `radar/errors.py` with that rule's id in the
message. A half-checked rule list must never produce a decision.
