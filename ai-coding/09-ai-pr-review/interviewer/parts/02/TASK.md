## Part 2: fix it

The team agreed on the behaviour below. Make the code do this, with tests. Keep
every public name and signature listed here, because other services call them.

1. `invoicing.totals.invoice_total(lines, currency) -> int` returns the exact
   total in the currency's minor units. Tax is computed per tax rate on the
   summed lines and rounded half up once per rate, as it was before this PR.
   No floats anywhere in the money path.
2. An unknown currency, or a line with an invalid `tax_rate`, raises
   `ValueError`. It never returns 0.
3. Add `invoicing.currency.exponent(currency) -> int`. `jpy` and `krw` are 0,
   `kwd` and `bhd` are 3, every other supported currency is 2. An unknown
   currency raises `ValueError`.
4. `format_amount(amount, currency)` uses the exponent: `"19.99 USD"`,
   `"4650 JPY"`, `"1.234 KWD"`.
5. `convert(amount, from_ccy, to_ccy, rates)`: a rate is major unit to major
   unit. The result is in `to_ccy` minor units, rounded half up.
6. `CachedRates(provider, ttl_seconds=3600, clock=time.monotonic)` caches per
   currency pair, fetches again once an entry is `ttl_seconds` old, and never
   shares its cache with another instance.
7. `ProcessorClient.charge(amount, currency, card, invoice_id)`:
   - retries only `TimeoutError`, at most 3 attempts in total
   - sends the same `Idempotency-Key` header on every attempt of one call, and
     different keys for different invoices
   - a decline raises `CardDeclined` after exactly one attempt
   - never logs the full card number. The last 4 digits are fine.
8. `invoicing.service.bill(invoice, card, client)`: a decline marks the invoice
   `failed`. If totalling fails, or the processor stays unreachable, the error
   propagates and the invoice stays `open` with no charge made.
