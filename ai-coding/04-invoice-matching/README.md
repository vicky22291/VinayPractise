# 04 Invoice matching

> Simulates Stripe's **Reconciliation** round: match incoming payments to open invoices. You inherit a teammate's half-working matcher with open tickets and failing tests, then the spec grows part by part.

| | |
|---|---|
| Round type | Fix an existing implementation, then extend it in staged parts |
| Stripe evidence | 4 candidate reports and 3 PracHub question pages, Sep 2025 to Oct 2026. See [research/stripe-rounds.md](../research/stripe-rounds.md) §5 |
| Time | 60 min: about 50 coding, 10 follow-up questions |
| Starter | `recon`: 6 modules, about 160 lines of Python, 8 tests (2 fail on purpose), 3 tickets from finance |
| Parts | 5. Reports say finishing every part is not required |
| Stripe AI setting | Not reported for this round. Practise mode C (no AI) first, then mode B |

## Run it

```
$ python3 ai-coding/kit.py start 04-invoice-matching      # prints the run dir and Part 1
$ cd ~/ai-coding-runs/04-invoice-matching-<stamp>          # second terminal: your AI goes here
$ python3 ai-coding/kit.py check ~/ai-coding-runs/04-...   # when you think a part is done
$ python3 ai-coding/kit.py next  ~/ai-coding-runs/04-...   # reveal the next part
```

Or let Claude run the round: start `claude` inside `ai-coding/04-invoice-matching/` and say "interview me". It reveals parts, calls time and grades you.

**Do not open `CLAUDE.md` or `interviewer/` before your first run.** They hold the later parts and the answer key.

## What to practise here

- Run the CLI and the tests before you read the tickets twice. The data in `data/` reproduces them.
- Integers for money. Reports from this round say so explicitly.
- Organize the matching so each new rule is a small change. Reports say the round "focuses on object organization."
- Write a test per ticket and per rule, and keep the old ones green.
- When two answers are both defensible, say which you picked and why. Interviewers ask "how would we prioritize that?"
