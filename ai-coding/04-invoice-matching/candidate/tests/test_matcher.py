import unittest

from recon.matcher import reconcile

INVOICES = ["INV-4,500,2024-04-01", "INV-7,700,2024-04-15"]


class ReconcileTest(unittest.TestCase):
    def test_memo_names_invoice(self):
        self.assertEqual(
            reconcile(["p1,500,Paying off: INV-4"], INVOICES),
            ["payment p1 (amount 500) pays invoice INV-4 due 2024-04-01"],
        )

    def test_unknown_invoice(self):
        self.assertEqual(
            reconcile(["p2,300,Paying off: INV-8"], INVOICES),
            ["payment p2 (amount 300) has no matching invoice"],
        )

    def test_no_payments(self):
        self.assertEqual(reconcile([], INVOICES), [])


if __name__ == "__main__":
    unittest.main()
