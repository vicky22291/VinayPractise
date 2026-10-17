import unittest
from datetime import date

from recon.export import COLUMNS, rows
from recon.matcher import match_all
from recon.models import Invoice, Payment


class ExportTest(unittest.TestCase):
    def test_columns_are_the_ledger_contract(self):
        self.assertEqual(COLUMNS, ["payment_id", "payment_amount", "invoice_id", "invoice_due_date"])

    def test_matched_and_unmatched_rows(self):
        invoices = [Invoice("INV-4", 500, date(2024, 4, 1))]
        payments = [Payment("p1", 500, "INV-4"), Payment("p2", 300, "")]
        self.assertEqual(list(rows(match_all(payments, invoices))), [
            {"payment_id": "p1", "payment_amount": 500, "invoice_id": "INV-4", "invoice_due_date": "2024-04-01"},
            {"payment_id": "p2", "payment_amount": 300, "invoice_id": "", "invoice_due_date": ""},
        ])


if __name__ == "__main__":
    unittest.main()
