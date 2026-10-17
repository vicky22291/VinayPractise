import unittest

from recon.matcher import reconcile

INVOICES = ["INV-4,500,2024-04-01", "INV-7,700,2024-04-15", "INV-1,1250,2024-03-01", "INV-12,1250,2024-04-20"]


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

    def test_recon_101_whole_id(self):
        self.assertEqual(
            reconcile(["p2,1250,Invoice INV-12"], INVOICES),
            ["payment p2 (amount 1250) pays invoice INV-12 due 2024-04-20"],
        )

    def test_recon_102_comma_in_memo(self):
        self.assertEqual(
            reconcile(["p6,500,Paying off: INV-4, thanks!"], INVOICES),
            ["payment p6 (amount 500) pays invoice INV-4 due 2024-04-01"],
        )

    def test_recon_103_paid_once(self):
        lines = reconcile(["p1,500,Paying off: INV-4", "p5,300,Paying off: INV-4 again"], INVOICES)
        self.assertEqual(lines[1], "payment p5 (amount 300) has no matching invoice")


if __name__ == "__main__":
    unittest.main()
