# radar-lite

Rule evaluator used by the risk team. Given one card transaction and an ordered
list of rules, it decides `accept` or `block`.

```
radar/models.py    Rule, load_rules, load_transaction
radar/engine.py    evaluate(txn, rules)
radar/errors.py    RuleSyntaxError
cli.py             python3 cli.py examples/txn.json examples/rules.json
tests/             python3 -m unittest
```

Python 3.11+, standard library only.
