"""CSV file that the finance ledger imports every morning.

The ledger team owns the import. Its columns are a contract: do not rename,
reorder or drop them without talking to them.
"""
import csv

COLUMNS = ["payment_id", "payment_amount", "invoice_id", "invoice_due_date"]


def rows(matches):
    for m in matches:
        inv = m.invoice
        yield {
            "payment_id": m.payment.id,
            "payment_amount": m.payment.amount,
            "invoice_id": inv.id if inv else "",
            "invoice_due_date": inv.due_date.isoformat() if inv else "",
        }


def write_csv(matches, path):
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows(matches))
