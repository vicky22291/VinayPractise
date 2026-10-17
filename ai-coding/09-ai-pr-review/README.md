# 09 Review an AI-written PR

> You are handed a pull request an AI agent wrote. CI is green and the description says "low risk". Review it like it ships tonight. More parts follow.

| | |
|---|---|
| Round type | Code review of an AI-generated change |
| Evidence | Stripe's 2026 AI rounds ask you to review and test the agent's code (Sep and Oct 2026 reports). Coinbase's official round grades telling "a correct change from one that merely looks plausible". No report describes this exact task. See [research/brownfield-formats.md](../research/brownfield-formats.md) §1.7 |
| Time | 60 min: about 50 working, 10 follow-up questions |
| Starter | `invoicing`: 8 modules plus a CLI, about 275 lines of Python, 19 passing tests, plus `PR.md` and `pr.diff` |
| Parts | 4 |
| Stripe AI setting | Unknown for review tasks. Practise mode B; the trap is trusting your own AI's review |

## Run it

```
$ python3 ai-coding/kit.py start 09-ai-pr-review
$ cd ~/ai-coding-runs/09-ai-pr-review-<stamp>          # second terminal: your AI goes here
$ python3 ai-coding/kit.py check ~/ai-coding-runs/09-...
$ python3 ai-coding/kit.py next  ~/ai-coding-runs/09-...
```

Or start `claude` inside `ai-coding/09-ai-pr-review/` and say "interview me".

**Do not open `CLAUDE.md` or `interviewer/` before your first run.**

## What to practise here

- Read the description, then the diff, including the test files.
- Prove every claim with a one-line repro before you write it down.
- Calibrate severity: what loses money, what leaks data, what is a nit.
- Say what you would keep, not only what you would change.
