"""Usage: python3 cli.py <subscriptions.json> <YYYY-MM-DD>

Prints the invoice for the month containing the date, for every subscription.
"""
import sys
from datetime import date

from billing.invoice import generate_invoice
from billing.loader import load_subscriptions


def main(argv):
    if len(argv) != 3:
        print(__doc__)
        return 2
    as_of = date.fromisoformat(argv[2])
    for sub, events in load_subscriptions(argv[1]):
        inv = generate_invoice(sub, events, as_of)
        print(f"{inv.subscription_id}  {inv.period_start} .. {inv.period_end}")
        for line in inv.lines:
            print(f"    {line.description:<44} {line.amount:>9}")
        print(f"    subtotal {inv.subtotal}  discount {inv.discount}  tax {inv.tax}  total {inv.total}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
