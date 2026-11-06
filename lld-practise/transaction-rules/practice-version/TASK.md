# Transaction rules: stage 1

Timebox: 50 minutes coding plus 10 minutes discussion. Implement in Java without evaluating input as Java code.

A transaction is a Map<String, Object>. A rule has an ID, an action (accept or block), and a condition. Apply rules in list order. The first matching rule decides; no match means accept.

Support equality between a field and a double-quoted string. Either operand order is valid. Whitespace around == is optional. Strings may contain spaces but not a double quote at this stage. A missing field does not match.

Examples:

```text
merchant_name == "Fresh Mart"
"Fresh Mart"==merchant_name
```

For {merchant_name: "Fresh Mart"}, both match. The value "Not Fresh Mart" must not match. Demonstrate ordered rule priority and default acceptance with your own tests.

This is an original Java practice version inspired by reported rule-evaluator rounds. It is not Stripe's official prompt.
