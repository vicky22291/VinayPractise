# 10 Billing legacy refactor

> Old billing code with no tests, and finance reconciles against it. Your job starts with making it safe to change. More parts follow.

| | |
|---|---|
| Round type | Change untested legacy code safely |
| Evidence | **Weakest in the set.** No Stripe report describes this task. It drills the Staff "how would you change this safely" probe and Hello Interview's verification advice. Domain: Stripe Billing (proration, coupons, trials, tax). See [research/brownfield-formats.md](../research/brownfield-formats.md) §1.8 |
| Time | 60 min: about 50 working, 10 follow-up questions |
| Starter | `billing`: 5 modules plus a CLI, about 260 lines of Python, one 115-line `generate_invoice`, 14 real-shaped fixtures, **no tests** |
| Parts | 4 |
| AI setting | Mode B. The thing to watch is your AI writing tests from what the code *should* do instead of what it does |

## Run it

```
$ python3 ai-coding/kit.py start 10-billing-legacy-refactor
$ cd ~/ai-coding-runs/10-billing-legacy-refactor-<stamp>    # second terminal: your AI goes here
$ python3 ai-coding/kit.py check ~/ai-coding-runs/10-...
$ python3 ai-coding/kit.py next  ~/ai-coding-runs/10-...
```

Or start `claude` inside `ai-coding/10-billing-legacy-refactor/` and say "interview me".

`check` for Part 1 takes a few seconds: it runs your suite many times.

**Do not open `CLAUDE.md` or `interviewer/` before your first run.**

## What to practise here

- Pin behaviour before changing it, including behaviour you think is wrong.
- Choose test inputs from the code's branches, not from the example in the task.
- Prefer many small, separately verified steps over one big change.
- Say what proof you would want before trusting a change to money.
