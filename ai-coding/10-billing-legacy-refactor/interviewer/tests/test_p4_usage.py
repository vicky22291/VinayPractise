import unittest
from datetime import date

from billing.invoice import generate_invoice
from billing.models import Event, Subscription

DEC = date(2026, 12, 15)


def lines(inv):
    return [(line.description, line.amount) for line in inv.lines]


def api(start=date(2026, 1, 1), **kw):
    return Subscription("sub_api", "cus_api", "api", 1, start, **kw)


def usage(day, units):
    return Event("usage", date(2026, 12, day), quantity=units)


class Part4Usage(unittest.TestCase):
    def test_usage_line_after_full_seat_line(self):
        inv = generate_invoice(api(), [usage(3, 1000), usage(20, 500)], DEC)
        self.assertEqual(lines(inv), [("API Pro x 1", 2000), ("API Pro usage (1500 units)", 3000)])
        self.assertEqual(inv.total, 5000)

    def test_usage_outside_period_ignored(self):
        events = [Event("usage", date(2026, 11, 30), quantity=7), Event("usage", date(2027, 1, 1), quantity=9)]
        self.assertEqual(lines(generate_invoice(api(), events, DEC)), [("API Pro x 1", 2000)])

    def test_trial_usage_is_free(self):
        s = api(date(2026, 12, 1), trial_end=date(2026, 12, 10))
        inv = generate_invoice(s, [usage(5, 400), usage(15, 100)], DEC)
        self.assertEqual(lines(inv), [
            ("Trial: API Pro x 1 (9 days)", 0),
            ("API Pro x 1 (22 of 31 days)", 1419),
            ("API Pro usage (100 units)", 200),
        ])

    def test_priced_at_plan_in_force(self):
        s = Subscription("sub_b", "cus_b", "basic", 1, date(2026, 1, 1))
        events = [usage(5, 1000), Event("plan_change", date(2026, 12, 16), plan_id="api"), usage(20, 300)]
        inv = generate_invoice(s, events, DEC)
        self.assertEqual(lines(inv), [
            ("Basic x 1 (15 of 31 days)", 435),
            ("API Pro x 1 (16 of 31 days)", 1032),
            ("API Pro usage (300 units)", 600),
        ])

    def test_usage_after_cancel_ignored(self):
        inv = generate_invoice(api(), [usage(5, 100), Event("cancel", date(2026, 12, 10)), usage(15, 999)], DEC)
        self.assertEqual(lines(inv), [("API Pro x 1 (9 of 31 days)", 581), ("API Pro usage (100 units)", 200)])

    def test_usage_before_start_ignored(self):
        inv = generate_invoice(api(date(2026, 12, 15)), [usage(10, 500), usage(20, 10)], DEC)
        self.assertEqual(lines(inv), [("API Pro x 1 (17 of 31 days)", 1097), ("API Pro usage (10 units)", 20)])

    def test_coupon_and_tax_include_usage(self):
        inv = generate_invoice(api(coupon_id="LOYAL15", tax_rate="0.1"), [usage(8, 1000)], DEC)
        self.assertEqual(lines(inv)[-1], ("Coupon LOYAL15", -600))
        self.assertEqual((inv.subtotal, inv.discount, inv.tax, inv.total), (4000, 600, 340, 3740))

    def test_plan_without_usage_price_has_no_usage_line(self):
        s = Subscription("sub_c", "cus_c", "pro", 2, date(2026, 1, 1))
        self.assertEqual(lines(generate_invoice(s, [usage(4, 50)], DEC)), [("Pro x 2", 5800)])


if __name__ == "__main__":
    unittest.main()
