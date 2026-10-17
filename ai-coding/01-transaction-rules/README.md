# 01 Transaction rules evaluator

> Simulates Stripe's **AI Programming Exercise**, the most reported Stripe coding round in Aug to Oct 2026. You get a small rule evaluator with open bug tickets, then the spec grows part by part.

| | |
|---|---|
| Round type | Staged feature extension on existing code |
| Stripe evidence | 3 candidate reports and 3 PracHub question pages, Aug to Oct 2026. See [research/stripe-rounds.md](../research/stripe-rounds.md) §4 |
| Time | 60 min: about 50 coding, 10 follow-up questions |
| Starter | `radar-lite`: 4 modules, about 80 lines of Python, 3 passing tests, 4 bug tickets |
| Parts | 5. Reports say nobody finishes them all |
| Stripe AI setting | AI built into the platform (Opus in two reports). Practise mode B, then mode A |

## Run it

```
$ python3 ai-coding/kit.py start 01-transaction-rules     # prints the run dir and Part 1
$ cd ~/ai-coding-runs/01-transaction-rules-<stamp>         # second terminal: your AI goes here
$ python3 ai-coding/kit.py check ~/ai-coding-runs/01-...   # when you think a part is done
$ python3 ai-coding/kit.py next  ~/ai-coding-runs/01-...   # reveal the next part
```

Or let Claude run the round: start `claude` inside `ai-coding/01-transaction-rules/` and say "interview me". It reveals parts, calls time and grades you.

**Do not open `CLAUDE.md` or `interviewer/` before your first run.** They hold the later parts and the answer key.

## What to practise here

- Read the code and run the tests before the first prompt.
- Pick a design in Part 1 that makes the later parts small diffs.
- Write your own tests. Stripe candidates report being asked to.
- Say what you are about to do before you prompt.
