## Part 4: stop the next one

This PR was green in CI and read well. How do you stop this class of change
across the org, not just in this repo? Talk the interviewer through it first.
Then write `GUARDRAILS.md`, one page: what you would change in review, tests,
types, CI and team habits for AI-written changes, and what each one costs.

Then ship one guardrail as code: `tools/no_float_money.py <dir>` scans every
`.py` file under `<dir>`. It prints `path:line` for each `float(...)` call,
each `round(...)` call and each float literal such as `1.5`, and exits 1 if it
found any. It exits 0 when the code is clean. Standard library only; `ast` is
fine.
