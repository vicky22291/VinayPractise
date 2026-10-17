## Part 5: standard precedence without breaking live rules

Analysts keep writing `a OR b AND c` and expecting `a OR (b AND c)`. Product
wants standard precedence: `AND` binds tighter than `OR`, and parentheses still
override.

About 4,000 live rules were written under the left-to-right semantics. Not one
of them may change its decision.

1. `Rule` gets an optional `version` field. Missing means `1`. Version 1 keeps
   left to right. Version 2 uses standard precedence.
2. Add `migrate(rule)` to `radar/engine.py`. It returns a version 2 rule with
   the same `id` and `action`, and a `when` clause that decides exactly like the
   original on every transaction. Migrating a version 2 rule returns it
   unchanged.

Before you code it, tell the interviewer how you would roll this out to
production.
