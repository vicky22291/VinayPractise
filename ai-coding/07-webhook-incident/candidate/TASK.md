# hooks: incident task

You are on call for `hooks`, the service that delivers webhook events to
merchant endpoints. Support has escalated a ticket. Read
`incident/TICKET.md`, then the log in `incident/dispatcher.log`, then the code.
There are no failing tests. The interviewer adds more parts as you go.

## Part 1: triage

1. Find the root cause behind each complaint in the ticket. Tell the
   interviewer, ranked by merchant impact, and point at the log lines that
   prove each one.
2. For each root cause, write a regression test under `tests/` that fails on
   the current code. **Do not fix anything yet.**

Your tests must use only these public APIs, so they still run after the fix:

- `hooks.dispatcher.Dispatcher(transport, clock)`, with `.endpoints.add(endpoint)`,
  `.publish(account_id, type, data)`, `.run_due()`, `.run_until(t)`,
  `.next_due()`, `.deliveries` and `.attempts.for_event(event_id)`
- `hooks.models.Endpoint(id, account_id, url, secret, event_types=("*",))`
- `hooks.transport.FakeTransport` (`.route(url, handler)`, `.requests`),
  `Response`, `TransportTimeout`
- `hooks.clock.FakeClock`
- `hooks.retry.RetryPolicy().next_attempt_at(created_at, attempts, now)`
- `hooks.signing.sign(payload, secret, timestamp)` and `hooks.signing.HEADER`
- `sdk.webhooks.verify_signature(...)` and `sdk.webhooks.construct_event(...)`
- anything in `tests/helpers.py`
