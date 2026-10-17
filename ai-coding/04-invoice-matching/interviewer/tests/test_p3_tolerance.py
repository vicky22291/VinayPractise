import unittest

from recon.matcher import reconcile


def pays(pid, amount, inv, due, suffix=""):
    return f"payment {pid} (amount {amount}) pays invoice {inv} due {due}{suffix}"


class Part3(unittest.TestCase):
    def test_forgiven(self):
        out = reconcile(["p3,490,"], ["INV-7,500,2024-05-01"], tolerance=10)
        self.assertEqual(out, [pays("p3", 490, "INV-7", "2024-05-01", " (forgiven 10)")])

    def test_overpaid(self):
        out = reconcile(["p4,715,"], ["INV-8,700,2024-05-02"], tolerance=20)
        self.assertEqual(out, [pays("p4", 715, "INV-8", "2024-05-02", " (overpaid 15)")])

    def test_inclusive_boundary(self):
        self.assertIn("pays", reconcile(["p1,490,"], ["INV-1,500,2024-05-01"], tolerance=10)[0])
        self.assertIn("no matching", reconcile(["p1,489,"], ["INV-1,500,2024-05-01"], tolerance=10)[0])

    def test_default_tolerance_is_exact(self):
        self.assertIn("no matching", reconcile(["p1,499,"], ["INV-1,500,2024-05-01"])[0])

    def test_exact_beats_tolerance_with_earlier_due_date(self):
        invoices = ["INV-1,495,2024-01-01", "INV-2,500,2024-09-01"]
        out = reconcile(["p1,500,"], invoices, tolerance=10)
        self.assertEqual(out, [pays("p1", 500, "INV-2", "2024-09-01")])

    def test_smallest_difference_beats_due_date(self):
        invoices = ["INV-1,508,2024-01-01", "INV-2,497,2024-09-01"]
        out = reconcile(["p1,500,"], invoices, tolerance=10)
        self.assertEqual(out, [pays("p1", 500, "INV-2", "2024-09-01", " (overpaid 3)")])

    def test_same_difference_both_sides_earliest_due(self):
        invoices = ["INV-1,505,2024-06-01", "INV-2,495,2024-05-01"]
        out = reconcile(["p1,500,"], invoices, tolerance=5)
        self.assertEqual(out, [pays("p1", 500, "INV-2", "2024-05-01", " (overpaid 5)")])

    def test_same_difference_same_due_first_in_list(self):
        invoices = ["INV-1,505,2024-05-01", "INV-2,495,2024-05-01"]
        out = reconcile(["p1,500,"], invoices, tolerance=5)
        self.assertEqual(out, [pays("p1", 500, "INV-1", "2024-05-01", " (forgiven 5)")])

    def test_memo_beats_tolerance_and_has_no_suffix(self):
        invoices = ["INV-1,520,2024-05-01", "INV-2,500,2024-01-01"]
        out = reconcile(["p1,500,INV-1"], invoices, tolerance=50)
        self.assertEqual(out, [pays("p1", 500, "INV-1", "2024-05-01")])

    def test_closed_invoices_skipped(self):
        invoices = ["INV-1,500,2024-01-01", "INV-2,510,2024-05-01"]
        out = reconcile(["p1,500,", "p2,500,"], invoices, tolerance=10)
        self.assertEqual(out[1], pays("p2", 500, "INV-2", "2024-05-01", " (forgiven 10)"))

    def test_negative_tolerance(self):
        with self.assertRaises(ValueError):
            reconcile(["p1,500,"], ["INV-1,500,2024-01-01"], tolerance=-1)


if __name__ == "__main__":
    unittest.main()
