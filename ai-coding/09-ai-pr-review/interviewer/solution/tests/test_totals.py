import unittest

from invoicing.models import LineItem
from invoicing.totals import invoice_total, subtotal, tax


class TotalsTest(unittest.TestCase):
    def test_single_line_no_tax(self):
        self.assertEqual(invoice_total([LineItem("Pro plan", 1999)], "usd"), 1999)

    def test_every_cent_amount_is_exact(self):
        for cents in range(0, 10_000):
            self.assertEqual(invoice_total([LineItem("x", cents)], "usd"), cents)

    def test_quantity(self):
        self.assertEqual(invoice_total([LineItem("Seat", 1500, 3)], "usd"), 4500)

    def test_tax_on_summed_lines(self):
        lines = [LineItem("Widget", 100, 1, "0.0825")] * 3
        self.assertEqual(subtotal(lines), 300)
        self.assertEqual(tax(lines), 25)  # 300 * 0.0825 = 24.75, rounded once
        self.assertEqual(invoice_total(lines, "usd"), 325)

    def test_two_rates(self):
        lines = [LineItem("Book", 1000, 1, "0"), LineItem("Pen", 250, 2, "0.2")]
        self.assertEqual(invoice_total(lines, "usd"), 1600)

    def test_jpy(self):
        lines = [LineItem("Plan", 3000), LineItem("Seat", 500, 3, "0.10")]
        self.assertEqual(invoice_total(lines, "jpy"), 4650)

    def test_kwd(self):
        self.assertEqual(invoice_total([LineItem("Plan", 1234, 1, "0.05")], "kwd"), 1296)

    def test_bad_input_raises_instead_of_zero(self):
        with self.assertRaises(ValueError):
            invoice_total([LineItem("Plan", 1000, 1, "abc")], "usd")
        with self.assertRaises(ValueError):
            invoice_total([LineItem("Plan", 1000)], "xyz")
        with self.assertRaises(ValueError):
            invoice_total([LineItem("Plan", 19.99)], "usd")


if __name__ == "__main__":
    unittest.main()
