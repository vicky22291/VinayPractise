"""Bill open invoices."""
from invoicing.errors import CardDeclined
from invoicing.totals import invoice_total


def bill(invoice, card, client):
    """Charge an open invoice and return its new status.

    A decline marks it failed. Any other error propagates and leaves it open,
    so the next billing run retries it.
    """
    if invoice.status != "open":
        raise ValueError(f"invoice {invoice.id} is {invoice.status}, not open")
    total = invoice_total(invoice.lines, invoice.currency)
    if total == 0:
        invoice.status = "paid"  # nothing to collect, e.g. a fully discounted invoice
        return invoice.status
    try:
        result = client.charge(total, invoice.currency, card, invoice.id)
    except CardDeclined:
        invoice.status = "failed"
        return invoice.status
    invoice.status = "paid"
    invoice.charge_id = result.id
    return invoice.status
