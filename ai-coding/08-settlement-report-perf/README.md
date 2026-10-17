# 08 Settlement report performance

> Simulates an **optimize-existing-code** phase: make a slow report fast without changing a single byte of its output. Meta's AI-native round ends with an optimize phase and Google's pilot is "read, debug, and optimize". The domain is Stripe-style payouts, where one cent matters.

| | |
|---|---|
| Round type | Performance optimization, output must stay byte-identical |
| Evidence | Meta and Google formats in [research/brownfield-formats.md](../research/brownfield-formats.md) §1.5; the survey's own example is a settlement report doing one query per merchant |
| Time | 60 min: about 50 working, 10 follow-up questions |
| Starter | `payouts`: a settlement report over balance transactions, FX and a fake database that counts round trips. 7 modules, about 310 lines of Python, 7 passing tests |
| Parts | 4 |
| Stripe AI setting | Unknown for this format. Practise mode B, then mode A |

## Run it

```
$ python3 ai-coding/kit.py start 08-settlement-report-perf
$ cd ~/ai-coding-runs/08-settlement-report-perf-<stamp>        # second terminal: your AI goes here
$ python3 ai-coding/kit.py check ~/ai-coding-runs/08-...        # when you think a part is done
$ python3 ai-coding/kit.py next  ~/ai-coding-runs/08-...        # reveal the next part
```

Or start `claude` inside `ai-coding/08-settlement-report-perf/` and say "interview me".

**Do not open `CLAUDE.md` or `interviewer/` before your first run.**

## What to practise here

- Say how you will prove the output is unchanged before you change anything.
- Measure first: count the work by kind, then remove the biggest kind.
- Read every line of an AI rewrite that touches money.
- Put numbers on complexity: N, M and C, not "faster".
