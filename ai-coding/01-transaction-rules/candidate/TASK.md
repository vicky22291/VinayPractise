# radar-lite: interview task

You own `radar-lite`, the service that decides whether a card transaction is
accepted or blocked. Read the code and run the tests before you change anything.
The interviewer adds more parts as you finish each one. Nobody is expected to
finish every part.

## Part 1: fix the open bugs

A transaction is a dict of field name to value. A rule has an `id`, an `action`
(`accept` or `block`) and a `when` clause. `evaluate(txn, rules)` returns the
action of the **first rule in list order** whose `when` clause is true. If no
rule matches, the answer is `accept`.

In this part a `when` clause is one equality between a field and a
double-quoted string, such as `merchant_name == "Evil Corp"`. The field may
be on either side of the `==`. Whitespace around `==` is optional. Values never
contain a double quote.

The risk team filed these bugs:

- **RISK-101.** A rule written as `"Evil Corp" == merchant_name` crashes the
  evaluator, so no transaction gets a decision.
- **RISK-102.** The rule `merchant_name == "Bad LLC"` also blocked our customer
  `Not Bad LLC`.
- **RISK-103.** Fresh Mart is on our allowlist: rule 1 accepts
  `merchant_name == "Fresh Mart"`. A Fresh Mart transaction with a Brazilian
  card was still blocked by rule 3, `card_country == "BR"`.
- **RISK-104.** A transaction with no `merchant_name` field crashes the
  evaluator. It should simply not match that rule.

Fix them, add a test for each, and keep the existing tests passing.
