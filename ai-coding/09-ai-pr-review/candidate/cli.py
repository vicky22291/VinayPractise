"""Usage: python3 cli.py <invoice.json> [rates.json]

Prints the invoice total, and what it settles as in USD when rates are given.
"""
import json
import sys

from invoicing.currency import CachedRates, StaticRates, convert, format_amount
from invoicing.models import Invoice, LineItem
from invoicing.totals import invoice_total


def load_invoice(path):
    with open(path) as f:
        raw = json.load(f)
    lines = [LineItem(**line) for line in raw.pop("lines")]
    return Invoice(lines=lines, **raw)


def main(argv):
    if len(argv) not in (2, 3):
        print(__doc__)
        return 2
    inv = load_invoice(argv[1])
    total = invoice_total(inv.lines, inv.currency)
    print(f"{inv.id}: {format_amount(total, inv.currency)}")
    if len(argv) == 3:
        rates = CachedRates(StaticRates.from_file(argv[2]))
        print(f"settles as {format_amount(convert(total, inv.currency, 'usd', rates), 'usd')}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
