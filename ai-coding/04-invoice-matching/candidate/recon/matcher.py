"""Match each payment to the invoice it pays."""
import re

from recon.models import Match
from recon.parsing import parse_invoice, parse_payment
from recon.report import format_match

INVOICE_ID = re.compile(r"INV-\d")


def invoice_id_in(memo):
    """The invoice ID the customer wrote in the memo, if any."""
    found = INVOICE_ID.search(memo)
    return found.group() if found else None


class MemoMatcher:
    def __init__(self, invoices):
        self.by_id = {inv.id: inv for inv in invoices}

    def match(self, payment):
        invoice = self.by_id.get(invoice_id_in(payment.memo))
        return Match(payment, invoice)


def match_all(payments, invoices):
    matcher = MemoMatcher(invoices)
    return [matcher.match(p) for p in payments]


def reconcile(payments, invoices):
    """One output line per payment, in payment order."""
    matches = match_all([parse_payment(line) for line in payments], [parse_invoice(line) for line in invoices])
    return [format_match(m) for m in matches]
