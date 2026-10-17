"""Lines that finance reads in the nightly reconciliation email."""


def format_match(match):
    p = match.payment
    if match.invoice is None:
        return f"payment {p.id} (amount {p.amount}) has no matching invoice"
    inv = match.invoice
    return f"payment {p.id} (amount {p.amount}) pays invoice {inv.id} due {inv.due_date.isoformat()}"


def summary(matches):
    matched = sum(1 for m in matches if m.invoice is not None)
    return f"{matched} of {len(matches)} payments matched"
