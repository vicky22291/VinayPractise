# 06 Ledger race

> A payments ledger loses money under load and sometimes freezes. Find out why, fix it without serializing everything, and keep going as the interviewer adds parts.

| | |
|---|---|
| Round type | Concurrency bugs in existing code, then extend it |
| Stripe evidence | Titles only: PracHub "Compute account balances with rejection and overdraft" (Dec 2025), "Debug an Asynchronous SDK Race Condition with a Customer" (Jun 2026). Domain: a Stripe-style ledger. See [research/stripe-rounds.md](../research/stripe-rounds.md) §6 and [research/brownfield-formats.md](../research/brownfield-formats.md) §1.6 |
| Time | 60 min: about 50 coding, 10 follow-up questions |
| Starter | `ledger`: 7 modules, about 260 lines of Python, 8 tests, 1 of them a stress test that fails |
| Parts | 4 |
| Stripe AI setting | Unknown for this shape. Practise mode B, then mode C |

## Run it

```
$ python3 ai-coding/kit.py start 06-ledger-race            # prints the run dir and Part 1
$ cd ~/ai-coding-runs/06-ledger-race-<stamp>                # second terminal: your AI goes here
$ python3 ai-coding/kit.py check ~/ai-coding-runs/06-...    # when you think a part is done
$ python3 ai-coding/kit.py next  ~/ai-coding-runs/06-...    # reveal the next part
```

Or start `claude` inside `ai-coding/06-ledger-race/` and say "interview me".

**Do not open `CLAUDE.md` or `interviewer/` before your first run.** They hold the later parts and the answer key.

Heads-up: `tests/test_stress.py` and `cli.py` both have a timeout watchdog, so nothing hangs your terminal.

## What to practise here

- Name the race class before you fix it.
- Say why your fix works, not just that the test went green.
- Treat a green stress test as weak evidence. Run it several times.
- Keep critical sections small, and say what each lock protects.
