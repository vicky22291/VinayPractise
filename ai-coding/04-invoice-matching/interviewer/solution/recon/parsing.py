"""Parse the bank export (payments) and the billing export (invoices).

Both exports are one record per line, comma separated:

    payment:  <payment_id>,<amount>,<memo>          (the memo may contain commas)
    invoice:  <invoice_id>,<amount>,<due_date as YYYY-MM-DD>
"""
import re
from datetime import date

from recon.models import Invoice, Payment

# Whole IDs only: INV-12 is never read as INV-1.
INVOICE_ID = re.compile(r"(?<![\w-])INV-\d+(?!\d)")


def parse_amount(text):
    return int(text.strip())


def parse_payment(line):
    payment_id, amount, memo = line.split(",", 2)
    return Payment(payment_id.strip(), parse_amount(amount), memo.strip())


def parse_invoice(line, position=0):
    invoice_id, amount, due = line.split(",")
    return Invoice(invoice_id.strip(), parse_amount(amount), date.fromisoformat(due.strip()), position)


def invoice_ids_in(memo):
    """Every invoice ID named in the memo, first mention first, no repeats."""
    return list(dict.fromkeys(INVOICE_ID.findall(memo)))


def read_lines(path):
    """Non-blank lines of a file, skipping # comments."""
    with open(path) as f:
        return [line.rstrip("\n") for line in f if line.strip() and not line.lstrip().startswith("#")]
