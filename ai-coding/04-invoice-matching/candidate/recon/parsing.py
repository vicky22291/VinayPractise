"""Parse the bank export (payments) and the billing export (invoices).

Both exports are one record per line, comma separated:

    payment:  <payment_id>,<amount>,<memo>
    invoice:  <invoice_id>,<amount>,<due_date as YYYY-MM-DD>
"""
from datetime import date

from recon.models import Invoice, Payment


def parse_amount(text):
    # the bank export sometimes sends "500.00"
    return float(text.strip())


def parse_payment(line):
    payment_id, amount, memo = line.split(",")
    return Payment(payment_id.strip(), parse_amount(amount), memo.strip())


def parse_invoice(line):
    invoice_id, amount, due = line.split(",")
    return Invoice(invoice_id.strip(), parse_amount(amount), date.fromisoformat(due.strip()))


def read_lines(path):
    """Non-blank lines of a file, skipping # comments."""
    with open(path) as f:
        return [line.rstrip("\n") for line in f if line.strip() and not line.lstrip().startswith("#")]
