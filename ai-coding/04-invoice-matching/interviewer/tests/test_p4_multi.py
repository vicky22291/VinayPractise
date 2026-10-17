import unittest

from recon.matcher import open_after, reconcile

INVOICES = ["INV-1,300,2024-04-01", "INV-2,500,2024-05-01", "INV-3,200,2024-06-01", "INV-4,500,2024-03-01"]


class Part4(unittest.TestCase):
    def test_pays_several_when_sum_matches(self):
        out = reconcile(["p9,800,Paying INV-1 and INV-2"], INVOICES)
        self.assertEqual(out, ["payment p9 (amount 800) pays invoices INV-1 due 2024-04-01, INV-2 due 2024-05-01"])

    def test_memo_order_not_list_order(self):
        out = reconcile(["p9,800,INV-2, INV-1"], INVOICES)
        self.assertEqual(out, ["payment p9 (amount 800) pays invoices INV-2 due 2024-05-01, INV-1 due 2024-04-01"])

    def test_three_invoices(self):
        out = reconcile(["p9,1000,INV-3 INV-1 INV-2"], INVOICES)
        self.assertTrue(out[0].startswith("payment p9 (amount 1000) pays invoices INV-3 due 2024-06-01, INV-1"))

    def test_all_closed_after_multi(self):
        out = reconcile(["p9,800,INV-1 INV-2", "p10,300,INV-1"], INVOICES)
        self.assertEqual(out[1], "payment p10 (amount 300) has no matching invoice")

    def test_sum_mismatch_falls_back_to_first_open(self):
        out = reconcile(["p9,777,INV-1 INV-2"], INVOICES)
        self.assertEqual(out, ["payment p9 (amount 777) pays invoice INV-1 due 2024-04-01"])

    def test_only_open_invoices_count(self):
        out = reconcile(["p1,300,INV-1", "p9,700,INV-1 INV-2 INV-3"], INVOICES)
        self.assertEqual(out[1], "payment p9 (amount 700) pays invoices INV-2 due 2024-05-01, INV-3 due 2024-06-01")

    def test_duplicate_id_counts_once(self):
        out = reconcile(["p9,600,INV-1 INV-1"], INVOICES)
        self.assertEqual(out, ["payment p9 (amount 600) pays invoice INV-1 due 2024-04-01"])

    def test_open_after(self):
        payments = ["p9,800,INV-1 INV-2", "p2,500,"]
        self.assertEqual(open_after(payments, INVOICES), ["INV-3"])
        self.assertEqual(open_after([], INVOICES), ["INV-1", "INV-2", "INV-3", "INV-4"])

    def test_open_after_with_tolerance(self):
        self.assertEqual(open_after(["p1,195,"], INVOICES, tolerance=5), ["INV-1", "INV-2", "INV-4"])


if __name__ == "__main__":
    unittest.main()
