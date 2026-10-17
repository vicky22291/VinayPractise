"""Currency conversion for payouts."""
from decimal import ROUND_HALF_EVEN, Decimal

ONE = Decimal(1)


def convert_at(amount, rate):
    """`amount` minor units times `rate`, rounded half-even to a whole minor unit."""
    return int((Decimal(amount) * rate).quantize(ONE, rounding=ROUND_HALF_EVEN))


def convert(store, amount, base, quote, day):
    """`amount` minor units of `base` in `quote` at the day's rate, rounded half-even to a whole unit."""
    if base == quote:
        return amount
    return convert_at(amount, store.fx_rate(base, quote, day))
