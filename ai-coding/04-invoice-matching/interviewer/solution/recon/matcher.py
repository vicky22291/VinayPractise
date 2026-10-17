"""Match each payment to the invoice(s) it pays.

Tiers, first hit wins: memo IDs, then amount within tolerance (exact first).
"""
import dataclasses

from recon.index import OpenInvoices
from recon.models import Match
from recon.parsing import invoice_ids_in, parse_invoice, parse_payment
from recon.report import format_match


class Reconciler:
    """Holds open invoices across batches. Reruns of a batch or a payment are no-ops."""

    def __init__(self, invoices, tolerance=0):
        if tolerance < 0:
            raise ValueError("tolerance must be >= 0")
        self.tolerance = tolerance
        self.open = OpenInvoices([
            parse_invoice(inv, i) if isinstance(inv, str) else dataclasses.replace(inv, position=i)
            for i, inv in enumerate(invoices)
        ])
        self.batches = {}  # batch_id -> (payment lines, output lines)
        self.applied = {}  # payment_id -> Match

    def run(self, batch_id, payments):
        payments = tuple(payments)
        if batch_id in self.batches:
            seen, lines = self.batches[batch_id]
            if seen != payments:
                raise ValueError(f"batch {batch_id!r} was already run with different payments")
            return list(lines)
        lines = [format_match(self.apply(parse_payment(line))) for line in payments]
        self.batches[batch_id] = (payments, tuple(lines))
        return lines

    def apply(self, payment):
        """Match and close. A payment ID seen before gets its first match back."""
        if payment.id not in self.applied:
            match = self.match(payment)
            self.open.close(match.invoices)
            self.applied[payment.id] = match
        return self.applied[payment.id]

    def match(self, payment):
        named = [self.open.by_id[i] for i in invoice_ids_in(payment.memo) if self.open.is_open(i)]
        if len(named) > 1 and sum(inv.amount for inv in named) == payment.amount:
            return Match(payment, tuple(named), "memo")
        if named:
            return Match(payment, (named[0],), "memo")
        best = self.open.best_by_amount(payment.amount, self.tolerance)
        if best:
            return Match(payment, (best,), "amount")
        return Match(payment, ())

    def still_open(self):
        return [inv.id for inv in self.open.still_open()]


def match_all(payments, invoices, tolerance=0):
    """Matches for already-parsed payments and invoices (CLI and export)."""
    r = Reconciler(invoices, tolerance)
    return [r.apply(p) for p in payments]


def reconcile(payments, invoices, tolerance=0):
    """One output line per payment, in payment order."""
    return Reconciler(invoices, tolerance).run("adhoc", payments)


def open_after(payments, invoices, tolerance=0):
    """IDs of invoices still open after the batch, in invoice-list order."""
    r = Reconciler(invoices, tolerance)
    r.run("adhoc", payments)
    return r.still_open()
