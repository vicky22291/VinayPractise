import unittest

from recon.matcher import reconcile


def pays(pid, amount, inv, due):
    return f"payment {pid} (amount {amount}) pays invoice {inv} due {due}"


def none(pid, amount):
    return f"payment {pid} (amount {amount}) has no matching invoice"


class Part2(unittest.TestCase):
    def test_exact_amount_when_no_memo(self):
        invoices = ["INV-1,300,2024-04-01", "INV-2,980,2024-04-02"]
        self.assertEqual(reconcile(["p3,980,"], invoices), [pays("p3", 980, "INV-2", "2024-04-02")])

    def test_earliest_due_date_in_unsorted_list(self):
        invoices = ["INV-1,500,2024-06-01", "INV-2,500,2024-04-01", "INV-3,500,2024-05-01"]
        self.assertEqual(reconcile(["p1,500,thanks"], invoices), [pays("p1", 500, "INV-2", "2024-04-01")])

    def test_same_due_date_first_in_list(self):
        invoices = ["INV-9,500,2024-04-01", "INV-2,500,2024-04-01"]
        self.assertEqual(reconcile(["p1,500,"], invoices), [pays("p1", 500, "INV-9", "2024-04-01")])

    def test_memo_beats_amount(self):
        invoices = ["INV-1,500,2024-04-01", "INV-2,300,2024-03-01"]
        self.assertEqual(reconcile(["p1,300,for INV-1"], invoices), [pays("p1", 300, "INV-1", "2024-04-01")])

    def test_memo_names_paid_invoice_falls_through(self):
        invoices = ["INV-1,500,2024-04-01", "INV-2,500,2024-05-01"]
        out = reconcile(["p1,500,INV-1", "p2,500,INV-1 again"], invoices)
        self.assertEqual(out[1], pays("p2", 500, "INV-2", "2024-05-01"))

    def test_unknown_id_falls_through(self):
        invoices = ["INV-1,500,2024-04-01"]
        self.assertEqual(reconcile(["p1,500,INV-99"], invoices), [pays("p1", 500, "INV-1", "2024-04-01")])

    def test_amount_match_closes_invoice(self):
        invoices = ["INV-1,500,2024-05-01", "INV-2,500,2024-04-01"]
        out = reconcile(["p1,500,", "p2,500,", "p3,500,"], invoices)
        self.assertEqual(out, [pays("p1", 500, "INV-2", "2024-04-01"), pays("p2", 500, "INV-1", "2024-05-01"), none("p3", 500)])

    def test_closed_by_memo_not_available_by_amount(self):
        invoices = ["INV-1,500,2024-04-01"]
        self.assertEqual(reconcile(["p1,10,INV-1", "p2,500,"], invoices)[1], none("p2", 500))

    def test_no_exact_amount(self):
        self.assertEqual(reconcile(["p1,501,"], ["INV-1,500,2024-04-01"]), [none("p1", 501)])


if __name__ == "__main__":
    unittest.main()
