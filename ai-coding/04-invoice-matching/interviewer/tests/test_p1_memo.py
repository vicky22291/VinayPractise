import unittest

from recon.matcher import reconcile

INVOICES = [
    "INV-1,1250,2024-03-01",
    "INV-4,500,2024-04-01",
    "INV-7,700,2024-04-15",
    "INV-9,2000,2024-05-01",
    "INV-12,1250,2024-04-20",
]


def line(pid, amount, inv=None, due=None):
    if inv is None:
        return f"payment {pid} (amount {amount}) has no matching invoice"
    return f"payment {pid} (amount {amount}) pays invoice {inv} due {due}"


class Part1(unittest.TestCase):
    def test_memo_match_integer_amount(self):
        self.assertEqual(reconcile(["p1,500,Paying off: INV-4"], INVOICES), [line("p1", 500, "INV-4", "2024-04-01")])

    def test_whole_id_recon_101(self):
        self.assertEqual(reconcile(["p2,1250,Invoice INV-12"], INVOICES), [line("p2", 1250, "INV-12", "2024-04-20")])
        self.assertEqual(reconcile(["p3,1250,Invoice INV-1"], INVOICES), [line("p3", 1250, "INV-1", "2024-03-01")])

    def test_id_followed_by_punctuation(self):
        self.assertEqual(reconcile(["p2,9,for INV-12."], INVOICES), [line("p2", 9, "INV-12", "2024-04-20")])

    def test_comma_in_memo_recon_102(self):
        out = reconcile(["p6,2000,Paying off: INV-9, thanks!", "p7,1,a, b, c"], INVOICES)
        self.assertEqual(out, [line("p6", 2000, "INV-9", "2024-05-01"), line("p7", 1)])

    def test_invoice_paid_once_recon_103(self):
        out = reconcile(["p1,500,Paying off: INV-4", "p5,333,Paying off: INV-4 again"], INVOICES)
        self.assertEqual(out, [line("p1", 500, "INV-4", "2024-04-01"), line("p5", 333)])

    def test_unknown_id(self):
        self.assertEqual(reconcile(["p2,333,Paying off: INV-8"], INVOICES), [line("p2", 333)])

    def test_empty_memo(self):
        self.assertEqual(reconcile(["p3,333,"], INVOICES), [line("p3", 333)])

    def test_ids_are_case_sensitive(self):
        self.assertEqual(reconcile(["p3,333,paying inv-4"], INVOICES), [line("p3", 333)])

    def test_amount_need_not_agree(self):
        self.assertEqual(reconcile(["p4,300,INV-7 first half"], INVOICES), [line("p4", 300, "INV-7", "2024-04-15")])

    def test_first_open_named_wins(self):
        self.assertEqual(reconcile(["p1,333,INV-8 or maybe INV-7"], INVOICES), [line("p1", 333, "INV-7", "2024-04-15")])
        out = reconcile(["p1,500,INV-4", "p2,333,INV-4 and INV-9"], INVOICES)
        self.assertEqual(out[1], line("p2", 333, "INV-9", "2024-05-01"))
        self.assertEqual(reconcile(["p1,333,INV-9 INV-7"], INVOICES), [line("p1", 333, "INV-9", "2024-05-01")])

    def test_order_and_count_preserved(self):
        payments = ["p1,333,", "p2,500,INV-4", "p3,333,INV-77"]
        out = reconcile(payments, INVOICES)
        self.assertEqual([l.split()[1] for l in out], ["p1", "p2", "p3"])

    def test_no_payments(self):
        self.assertEqual(reconcile([], INVOICES), [])


if __name__ == "__main__":
    unittest.main()
