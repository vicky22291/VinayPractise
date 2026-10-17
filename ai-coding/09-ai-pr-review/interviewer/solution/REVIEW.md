# Review: PR #42 multi-currency totals and processor retries

Verdict: **request changes.** Four blockers. Two of them lose or double-take
customer money silently, and CI is green only because two tests were loosened.

| # | Severity | Where | What goes wrong | Fix |
|---|---|---|---|---|
| 1 | blocker | `processor.py` `charge` retry loop | Retries POST /v1/charges with no Idempotency-Key. If the processor charged the card and the response was lost (timeout after processing), the retry charges the card again. The new test only covers a timeout *before* processing | Generate one Idempotency-Key per charge and send it on every attempt. Test the "after" timeout |
| 2 | blocker | `totals.py` `line_total`, `invoice_total` | Float money. `int(19.99 * 100)` is 1998, so a $19.99 plan bills $19.98. 284 of the 4,900 cent amounts from $1.00 to $49.99 come out one cent short | Integer minor units plus `Decimal` for tax. No floats |
| 3 | blocker | `totals.py` `invoice_total` `except Exception: return 0` + `service.py` `total == 0` | Any error (bad tax rate, bad currency) returns 0, and `bill` treats 0 as "fully discounted" and marks the invoice **paid** without charging | Let the error propagate. `bill` leaves the invoice open |
| 4 | blocker | `currency.py` `convert`, `format_amount` | Hard-codes 2 decimals. 50,000 JPY settles as $3.35 instead of $335.00 (100x off). KWD is 10x off. Emails show "46.50 JPY" for 4,650 yen | Exponent table: JPY/KRW 0, KWD/BHD 3, else 2 |
| 5 | major | `totals.py` per-line rounding | Silent behaviour change for existing USD invoices: 3 lines of $1.00 at 8.25% was $3.25, now $3.24. The PR says "fully backwards compatible" and edited the test's expected value to 324 | Keep rounding once per rate on the summed lines |
| 6 | major | `tests/test_totals.py`, `tests/test_processor.py` | Tests weakened to go green: `assertAlmostEqual(..., delta=1)` hides finding 2, and the decline test now accepts any `ProcessorError` | Restore exact assertions |
| 7 | major | `currency.py` `CachedRates` | Cache keyed by target currency only, so after EUR->USD, GBP->USD returns the EUR rate. `ttl_seconds` is accepted and never used, so rates never refresh. `cache={}` is a mutable default shared by every instance | Key by (from, to), honour the TTL with an injected clock, per-instance dict |
| 8 | major | `processor.py` `log.info(... card.number ...)` | Full card number (PAN) in logs. PCI DSS scope for the whole log pipeline | Log `card.last4` only |
| 9 | major | `processor.py` `except Exception` + `service.py` `except ProcessorError` | Declines are retried 3 times (the card will decline again; some issuers flag repeated attempts) and surface as `ProcessorError`. `bill` then marks an invoice **failed** when the processor is merely down, which would send dunning emails during an outage | Retry only `TimeoutError`. `bill` catches only `CardDeclined`; outages leave the invoice open |
| 10 | minor | `processor.py` | No backoff or jitter between attempts; all invoices in a run retry in lockstep against a struggling processor | Exponential backoff with jitter, injected sleeper for tests |
| 11 | nit | `totals.py` | `invoice_total` defaults to `"usd"`, so a caller that forgets the currency bills in dollars | Make `currency` required |

Process note: the description says "Low risk, fully backwards compatible". Both
claims are false (findings 3, 5). Ask the author to list behaviour changes
explicitly next time, and to never edit an expected value without saying why.
