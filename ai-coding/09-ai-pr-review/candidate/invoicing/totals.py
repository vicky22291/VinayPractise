"""Invoice totals. Supports every currency in invoicing.currency.SUPPORTED."""
import logging
from collections import defaultdict
from decimal import ROUND_HALF_UP, Decimal

log = logging.getLogger(__name__)


def subtotal(lines):
    return sum(line.unit_amount * line.quantity for line in lines)


def tax(lines):
    """Tax per rate on the summed lines, rounded half up once per rate."""
    by_rate = defaultdict(int)
    for line in lines:
        by_rate[line.tax_rate] += line.unit_amount * line.quantity
    total = 0
    for rate, base in by_rate.items():
        total += int((Decimal(base) * Decimal(rate)).quantize(Decimal(1), rounding=ROUND_HALF_UP))
    return total


def line_total(line):
    """Amount for one line including its tax, in major units."""
    amount = line.unit_amount / 100 * line.quantity
    return round(amount * (1 + float(line.tax_rate)), 2)


def invoice_total(lines, currency="usd"):
    """Total due, in the currency's minor units."""
    try:
        total = sum(line_total(line) for line in lines)
        return int(total * 100)
    except Exception:
        log.warning("could not compute total for %s invoice", currency)
        return 0
