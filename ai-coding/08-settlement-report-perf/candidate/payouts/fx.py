"""Currency conversion for payouts."""
from decimal import ROUND_HALF_EVEN, Decimal


def convert(store, amount, base, quote, day):
    """`amount` minor units of `base` in `quote` at the day's rate, rounded half-even to a whole unit."""
    if base == quote:
        return amount
    rate = store.fx_rate(base, quote, day)
    return int((Decimal(amount) * rate).quantize(Decimal(1), rounding=ROUND_HALF_EVEN))
