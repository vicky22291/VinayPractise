# 07 Webhook incident

> Simulates a **debugging round from a ticket and a production log**, with no failing test to start from. Stripe's bug bash uses "a generic version of a real Stripe bug". Coinbase's official round grades triage, debugging and rollback reasoning. The domain is Stripe's own product: webhooks.

| | |
|---|---|
| Round type | Bug from an issue report and logs, then rollback reasoning |
| Evidence | interviewing.io's Stripe page (bug bash); Coinbase's official repo-based round. See [research/brownfield-formats.md](../research/brownfield-formats.md) §1.2 and §1.10 |
| Time | 60 min: about 50 working, 10 follow-up questions |
| Starter | `hooks`: a webhook dispatcher plus a receiver SDK, about 450 lines of Python, 14 passing tests, a support ticket and an 850-line production log |
| Parts | 4 |
| Stripe AI setting | Unknown for debugging rounds; one source says prohibited. Practise mode C first, then mode B |

## Run it

```
$ python3 ai-coding/kit.py start 07-webhook-incident
$ cd ~/ai-coding-runs/07-webhook-incident-<stamp>        # second terminal: your AI goes here
$ python3 ai-coding/kit.py check ~/ai-coding-runs/07-...  # when you think a part is done
$ python3 ai-coding/kit.py next  ~/ai-coding-runs/07-...  # reveal the next part
```

Or start `claude` inside `ai-coding/07-webhook-incident/` and say "interview me".

**Do not open `CLAUDE.md` or `interviewer/` before your first run.**

## What to practise here

- Read the ticket, then the shape of the log, then the code. Not the other way round.
- One hypothesis per complaint, with a log line as evidence, before any prompt.
- Write the failing test first, against the public API, so it survives the fix.
- Rank the complaints by merchant impact before you fix any of them.
