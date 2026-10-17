import unittest
from datetime import date

from billing.invoice import generate_invoice
from billing.models import Event, Subscription
from billing.pricing import proration_days


class RealDays(unittest.TestCase):
    def test_switch_date(self):
        self.assertEqual(proration_days(date(2026, 10, 1), date(2026, 11, 1)), 30)
        self.assertEqual(proration_days(date(2026, 12, 1), date(2027, 1, 1)), 31)
        self.assertEqual(proration_days(date(2027, 2, 1), date(2027, 3, 1)), 28)

    def test_december_2026(self):
        s = Subscription("s", "c", "basic", 1, date(2026, 1, 1))
        inv = generate_invoice(s, [Event("plan_change", date(2026, 12, 16), plan_id="pro")], date(2026, 12, 1))
        self.assertEqual([(l.description, l.amount) for l in inv.lines],
                         [("Basic x 1 (15 of 31 days)", 435), ("Pro x 1 (16 of 31 days)", 1497)])


class Usage(unittest.TestCase):
    def test_usage_does_not_split_seats(self):
        s = Subscription("s", "c", "api", 1, date(2026, 1, 1))
        inv = generate_invoice(s, [Event("usage", date(2026, 12, 9), quantity=250)], date(2026, 12, 1))
        self.assertEqual([(l.description, l.amount) for l in inv.lines],
                         [("API Pro x 1", 2000), ("API Pro usage (250 units)", 500)])


if __name__ == "__main__":
    unittest.main()
