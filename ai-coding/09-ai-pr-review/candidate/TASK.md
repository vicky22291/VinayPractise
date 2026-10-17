# invoicing: interview task

You own the `invoicing` service. A teammate used an AI agent to open PR #42,
and it is already applied to this working tree. `PR.md` is the agent's
description. `pr.diff` is the exact change against `main`. CI is green.

The interviewer adds more parts as you finish each one. Nobody is expected to
finish every part.

## Part 1: review the PR

Review PR #42 as if it ships to production tonight. Write `REVIEW.md` in the
repo root. For each issue give:

- severity: **blocker** (must not merge), **major** (fix before merge, or a
  ticket today), **minor**, or **nit**
- file and line
- what goes wrong, with a concrete input or scenario
- the fix you would ask for

End with a verdict: approve, approve with changes, or request changes.

Do not change the service code yet. You may run things and write scratch tests
to prove a point. You have about 15 minutes.
