import unittest
from datetime import date

from recon.parsing import parse_invoice, parse_payment


class ParsingTest(unittest.TestCase):
    def test_parse_invoice(self):
        inv = parse_invoice("INV-4,500,2024-04-01")
        self.assertEqual((inv.id, inv.amount, inv.due_date), ("INV-4", 500, date(2024, 4, 1)))

    def test_parse_payment(self):
        p = parse_payment("p1,500,Paying off: INV-4")
        self.assertEqual((p.id, p.amount, p.memo), ("p1", 500, "Paying off: INV-4"))

    def test_empty_memo(self):
        self.assertEqual(parse_payment("p3,980,").memo, "")


if __name__ == "__main__":
    unittest.main()
