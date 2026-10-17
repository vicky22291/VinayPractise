## Part 3: make the worst bug impossible

1. Your test suite must catch the PR as it was. The interviewer will copy your
   repo, put back the PR's original `invoicing/processor.py`, and run
   `python3 -m unittest`. Then the same with the PR's original
   `invoicing/totals.py`. Your suite must fail both times, and pass on your
   code.
2. Add `invoicing/money.py` with a `Money` value type, so float money cannot be
   represented:
   - `Money(amount, currency)`. `amount` must be an `int` (not a `bool`, not a
     `float`), else `TypeError`. `currency` must be supported, else
     `ValueError`. Exposes `.amount` and `.currency`.
   - `Money.from_major(value, currency)`. `value` is a `str` or `Decimal` such
     as `"19.99"`. A `float` raises `TypeError`. More decimal places than the
     currency allows raises `ValueError`.
   - `+` and `-` between two `Money` of the same currency return `Money`.
     Different currencies raise `ValueError`. Any other operand raises
     `TypeError`.
   - `Money * int` returns `Money`. `Money * float` raises `TypeError`.
   - Two `Money` are equal when amount and currency are equal.
     `str(Money(4650, "jpy")) == "4650 JPY"`.

You do not have to move the whole codebase onto `Money`. Tell the interviewer
where you would start, and why there.
