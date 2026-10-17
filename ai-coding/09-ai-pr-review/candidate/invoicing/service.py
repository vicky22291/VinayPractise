"""Bill open invoices."""
from invoicing.errors import ProcessorError
from invoicing.totals import invoice_total


def bill(invoice, card, client):
    """Charge an open invoice and return its new status."""
    if invoice.status != "open":
        raise ValueError(f"invoice {invoice.id} is {invoice.status}, not open")
    total = invoice_total(invoice.lines, invoice.currency)
    if total == 0:
        invoice.status = "paid"  # nothing to collect, e.g. a fully discounted invoice
        return invoice.status
    try:
        result = client.charge(total, invoice.currency, card, invoice.id)
    except ProcessorError:  # declines and exhausted retries
        invoice.status = "failed"
        return invoice.status
    invoice.status = "paid"
    invoice.charge_id = result.id
    return invoice.status
