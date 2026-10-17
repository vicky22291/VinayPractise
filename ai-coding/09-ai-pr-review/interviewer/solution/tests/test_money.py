import unittest
from decimal import Decimal

from invoicing.money import Money


class MoneyTest(unittest.TestCase):
    def test_float_is_unrepresentable(self):
        for bad in (19.99, 1999.0, True):
            with self.assertRaises(TypeError):
                Money(bad, "usd")
        with self.assertRaises(TypeError):
            Money.from_major(19.99, "usd")
        with self.assertRaises(TypeError):
            Money(1, "usd") * 1.5

    def test_from_major(self):
        self.assertEqual(Money.from_major("19.99", "usd"), Money(1999, "usd"))
        self.assertEqual(Money.from_major(Decimal("1.234"), "kwd"), Money(1234, "kwd"))
        with self.assertRaises(ValueError):
            Money.from_major("1.5", "jpy")

    def test_arithmetic(self):
        self.assertEqual(Money(1000, "usd") + Money(999, "usd"), Money(1999, "usd"))
        self.assertEqual(Money(500, "jpy") * 3, Money(1500, "jpy"))
        with self.assertRaises(ValueError):
            Money(1, "usd") + Money(1, "eur")

    def test_str(self):
        self.assertEqual(str(Money(4650, "jpy")), "4650 JPY")


if __name__ == "__main__":
    unittest.main()
