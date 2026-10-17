# hooks

Delivers platform events (`charge.succeeded`, `payout.paid`, ...) to the HTTPS
endpoints merchants register. At least once, signed, retried with backoff.

```
hooks/dispatcher.py   publish an event, fan out to endpoints, deliver, retry
hooks/serializer.py   the JSON body merchants receive
hooks/signing.py      the Hooks-Signature header
hooks/retry.py        backoff schedule
hooks/store.py        events, endpoints, attempt log (in memory here, Postgres in prod)
hooks/transport.py    HTTP transport; FakeTransport for tests
hooks/clock.py        SystemClock, FakeClock
hooks/log.py          key=value log lines
sdk/webhooks.py       what merchants embed to verify our signature
incident/             the ticket and the production log for INC-2291
tests/                python3 -m unittest
```

Python 3.11+, standard library only.

Merchant-facing promises (from our public docs):
- Every event is delivered at least once. Receivers dedupe on the event `id`.
- Failed deliveries are retried with exponential backoff for up to three days.
- `Hooks-Signature: t=<timestamp>,v1=<HMAC-SHA256 of "<t>." + raw body>`. The
  SDK rejects signatures older than 5 minutes.
