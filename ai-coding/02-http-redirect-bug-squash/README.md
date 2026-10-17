# 02 HTTP redirect bug squash

> Simulates Stripe's **Bug Squash** round: an unfamiliar HTTP client library modelled on Python `requests`, failing tests, and tickets. Find the root cause, fix the library, not the tests.

| | |
|---|---|
| Round type | Bug squash: failing tests in an unfamiliar library, then tickets with no test |
| Stripe evidence | `requests` 307 task: 1 PracHub question page (Sep 24, 2026) and 2 candidate reports (Sep 24 and Oct 1, 2026). See [research/stripe-rounds.md](../research/stripe-rounds.md) §2 |
| Time | 60 min: about 50 debugging, 10 follow-up questions |
| Starter | `minireq`: 13 files, about 930 lines of Python, a local httpbin-style test server, 30 tests with 2 failing |
| Parts | 4. Part 1 is the whole round at Stripe; the rest are stretch tickets |
| Stripe AI setting | Unknown. interviewing.io says AI is prohibited at Stripe. Practise mode C (no AI) first, then mode B |

## Run it

```
$ python3 ai-coding/kit.py start 02-http-redirect-bug-squash   # prints the run dir and Part 1
$ cd ~/ai-coding-runs/02-http-redirect-bug-squash-<stamp>       # second terminal
$ python3 -m unittest                                           # in the run dir: 2 tests fail
$ python3 ai-coding/kit.py check ~/ai-coding-runs/02-...        # when you think a part is done
$ python3 ai-coding/kit.py next  ~/ai-coding-runs/02-...        # reveal the next ticket
```

Or let Claude run the round: start `claude` inside `ai-coding/02-http-redirect-bug-squash/` and say "interview me".

**Do not open `CLAUDE.md` or `interviewer/` before your first run.** They hold the later tickets and the answer key.

## What to practise here

- Run the suite and read the failing test before opening library code.
- Say a hypothesis out loud before each run: "I think X, so I expect Y."
- Trace the call path from `minireq.post` down to the socket before you change anything.
- Smallest root-cause fix, plus a regression test for every ticket without one.
- Set up your debugger before the day. A Stripe candidate lost about 15 minutes to a VS Code debugger that would not start.
