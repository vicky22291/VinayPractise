"""Invoice totals in any supported currency. Integer minor units only."""
from collections import defaultdict
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from invoicing.currency import exponent


def _rate(raw):
    try:
        rate = Decimal(raw)
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError(f"invalid tax_rate {raw!r}") from None
    if not rate.is_finite() or rate < 0:
        raise ValueError(f"invalid tax_rate {raw!r}")
    return rate


def subtotal(lines):
    return sum(line.unit_amount * line.quantity for line in lines)


def tax(lines):
    """Tax per rate on the summed lines, rounded half up once per rate."""
    by_rate = defaultdict(int)
    for line in lines:
        by_rate[_rate(line.tax_rate)] += line.unit_amount * line.quantity
    return sum(int((base * rate).quantize(Decimal(1), rounding=ROUND_HALF_UP)) for rate, base in by_rate.items())


def invoice_total(lines, currency):
    """Total due, in the currency's minor units. Bad input raises ValueError."""
    exponent(currency)
    for line in lines:
        if type(line.unit_amount) is not int or type(line.quantity) is not int:
            raise ValueError(f"line {line.description!r}: amounts must be int minor units")
    return subtotal(lines) + tax(lines)
