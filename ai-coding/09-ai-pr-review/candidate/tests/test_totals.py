import unittest

from invoicing.models import LineItem
from invoicing.totals import invoice_total, subtotal, tax


class TotalsTest(unittest.TestCase):
    def test_single_line_no_tax(self):
        # allow for floating point rounding
        self.assertAlmostEqual(invoice_total([LineItem("Pro plan", 1999)], "usd"), 1999, delta=1)

    def test_quantity(self):
        self.assertEqual(invoice_total([LineItem("Seat", 1500, 3)], "usd"), 4500)

    def test_tax_on_summed_lines(self):
        lines = [LineItem("Widget", 100, 1, "0.0825")] * 3
        self.assertEqual(subtotal(lines), 300)
        self.assertEqual(tax(lines), 25)  # 300 * 0.0825 = 24.75, rounded once
        self.assertEqual(invoice_total(lines, "usd"), 324)  # tax is now rounded per line

    def test_two_rates(self):
        lines = [LineItem("Book", 1000, 1, "0"), LineItem("Pen", 250, 2, "0.2")]
        self.assertEqual(invoice_total(lines, "usd"), 1600)

    def test_eur(self):
        self.assertEqual(invoice_total([LineItem("Plan", 1000, 2, "0.2")], "eur"), 2400)


if __name__ == "__main__":
    unittest.main()
