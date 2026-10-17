# INC-2291: webhook signature failures, duplicate ids, early give-up

Model answer. Numbers come from `incident/blast_radius.py` on `dispatcher.log`.

## Timeline (UTC)

| Time | What |
|---|---|
| Oct 13 16:20 | `hooks-dispatcher` 1.4.0 deployed: compact UTF-8 payloads |
| Oct 14 09:15:48 | First `400 No signatures found` (Café Olé, `charge.succeeded`) |
| 10:05:35 | Northwind starts returning 503 |
| 10:17:48 | First `delivery.gave_up`, 62 minutes after the event (`age_s=3720`) |
| 10:42:59 | Lumen starts timing out. Retries go out with new `whd_` ids |
| 12:05 | Northwind back. Events younger than about an hour still arrive |
| 13:25:58 | Last `gave_up` in the log |
| 13:40 | Ticket opened |

## Root causes, by merchant impact

1. **Retries stop after 62 minutes, not 3 days.** `RetryPolicy.max_age` is
   `3 * 24 * 60`, minutes, compared against seconds. Every failure mode becomes
   permanent loss after an hour. Present before 1.4.0.
2. **Signature covers different bytes than the body.** 1.4.0 sends
   `ensure_ascii=False` bytes but `sign_envelope` re-encodes with
   `ensure_ascii=True`. Any payload with a non-ASCII character fails
   verification. Introduced by 1.4.0.
3. **Envelope `id` is the attempt id (`whd_`), not the event id.** Receivers
   cannot dedupe a retry, so a timeout that the merchant actually processed
   becomes a double fulfilment. Present before 1.4.0.

## Blast radius (from the log, 09:00 to 13:30)

| Effect | Deliveries | Accounts |
|---|---|---|
| Signature rejected | 20 | 3 (the ticket names 2; Bluebird has one "Zoë" customer) |
| Abandoned (gave up) | 30 | 4 (20 of them are the signature failures) |
| Retried after timeout, possibly processed twice | 5 | 1 (Lumen) |

Every account ever affected by cause 3 is larger than this log shows: any
timeout since that code shipped could have caused a duplicate.

## What should have paged

- `gave_up` count above 0 for an event younger than 2 days. It should be
  impossible by design, so any occurrence pages.
- Per-account rate of `4xx` with "No signatures found" above 1% over 15 minutes,
  or a fleet-wide jump after a deploy. It started 17 hours after 1.4.0 and
  nobody noticed until merchants called.

## Rollback decision

- **Roll back 1.4.0 now**: low risk, minutes, and it stops new signature
  failures, because 1.3 sent and signed the same ASCII-escaped bytes. It does
  not fix causes 1 and 3, which predate 1.4.0.
- **Forward-fix 1 and 3** the same day. Cause 3 changes the `id` merchants see:
  announce it, and expect one extra duplicate per in-flight retry during the
  deploy.
- Then re-ship 1.4.0 with `sign(body)` over the exact bytes sent.
- **Replay** (Part 3) every abandoned delivery since the first `gave_up`, per
  endpoint, after the fix. Tell Lumen which charges may have shipped twice.
