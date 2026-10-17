# 05 KYC CSV validation

> Simulates a Stripe CSV-validation coding round, opened Meta-style: a multi-file validator is failing its own tests, and the nightly run is red. Fix it. More parts follow.

| | |
|---|---|
| Round type | Fix failing tests in a multi-file repo, then extend it |
| Stripe evidence | Stripe Senior, late Jul and Aug 2026: parse and validate a CSV string of business verification records (Hello Interview community). PracHub titles "Debug Validation Error Aggregation" (May 2026) and "Validate CSV company records". See [research/stripe-rounds.md](../research/stripe-rounds.md) §6 |
| Time | 60 min: about 50 coding, 10 follow-up questions |
| Starter | `kyc`: 9 modules, about 320 lines of Python, 16 tests of which 5 fail, sample files in `data/` |
| Parts | 4 |
| Stripe AI setting | Mixed reports. Practise mode B, then mode C (no AI) |

## Run it

```
$ python3 ai-coding/kit.py start 05-kyc-csv-validation    # prints the run dir and Part 1
$ cd ~/ai-coding-runs/05-kyc-csv-validation-<stamp>        # second terminal: your AI goes here
$ python3 ai-coding/kit.py check ~/ai-coding-runs/05-...   # when you think a part is done
$ python3 ai-coding/kit.py next  ~/ai-coding-runs/05-...   # reveal the next part
```

Or start `claude` inside `ai-coding/05-kyc-csv-validation/` and say "interview me".

**Do not open `CLAUDE.md` or `interviewer/` before your first run.** They hold the later parts and the answer key.

## What to practise here

- Run the tests and the CLI before reading code. Group failures by root cause.
- Fix the library, never the tests.
- Read the spec in TASK.md line by line. Not every requirement has a failing test.
- Name the seams in the code before the next part arrives.
