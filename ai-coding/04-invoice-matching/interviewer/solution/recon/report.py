"""Lines that finance reads in the nightly reconciliation email."""


def format_match(match):
    p = match.payment
    head = f"payment {p.id} (amount {p.amount})"
    if not match.invoices:
        return f"{head} has no matching invoice"
    if len(match.invoices) > 1:
        paid = ", ".join(f"{inv.id} due {inv.due_date.isoformat()}" for inv in match.invoices)
        return f"{head} pays invoices {paid}"
    inv = match.invoice
    line = f"{head} pays invoice {inv.id} due {inv.due_date.isoformat()}"
    if match.tier == "amount" and match.difference > 0:
        line += f" (forgiven {match.difference})"
    elif match.tier == "amount" and match.difference < 0:
        line += f" (overpaid {-match.difference})"
    return line


def summary(lines):
    matched = sum(1 for line in lines if not line.endswith("has no matching invoice"))
    return f"{matched} of {len(lines)} payments matched"
