# Guardrails for AI-written changes to money code

| Layer | Guardrail | Catches | Cost |
|---|---|---|---|
| Types | `Money(int, currency)` value type at service boundaries. Floats raise | Float money, mixed currencies | 1 to 2 weeks to roll out per service, starting with the totals and processor modules |
| Lint in CI | `tools/no_float_money.py` on money packages; ban `except Exception` without re-raise in `invoicing/`; ban logging fields named `number`/`card_number` | Findings 2, 3, 8 before review | Hours. Some false positives, allow-list with a comment |
| Tests | Property test: every amount 0 to 10,000 round-trips exactly in every currency. Contract tests for the processor client: timeout after processing must create one charge | Findings 1, 2, 4 | A day. Runs in seconds |
| CI | Fail the build when a PR changes an expected value in an existing test without a `behaviour-change:` line in the description. Diff report of totals on 1,000 recorded production invoices (shadow run) | Findings 5, 6 | Days to build the shadow harness. Worth it for billing |
| Review | Checklist for AI PRs: list behaviour changes, list tests changed and why, name the failure mode of every retry, name every new cache's key and TTL. Two reviewers for money paths | Plausible-but-wrong changes | Minutes per PR |
| Habits | The human who opens an AI PR owns it and must be able to explain every line. The agent's PR text is not evidence: CI green and "backwards compatible" are claims to check | Over-trust | Culture work, led by example in reviews |

What I would not do: ban AI agents from money code. The failure here is
missing guardrails, not the tool. The same PR from a human would have had the
same bugs.
