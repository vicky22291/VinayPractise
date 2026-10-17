import unittest
from datetime import date

from billing.invoice import generate_invoice
from billing.models import Event, Subscription


def lines(inv):
    return [(line.description, line.amount) for line in inv.lines]


def sub(plan="basic", qty=1, start=date(2026, 1, 1), **kw):
    return Subscription("sub_t", "cus_t", plan, qty, start, **kw)


class Part3RealDays(unittest.TestCase):
    def test_december_2026_upgrade_uses_31_days(self):
        inv = generate_invoice(sub(), [Event("plan_change", date(2026, 12, 16), plan_id="pro")], date(2026, 12, 20))
        self.assertEqual(lines(inv), [("Basic x 1 (15 of 31 days)", 435), ("Pro x 1 (16 of 31 days)", 1497)])
        self.assertEqual(inv.total, 1932)

    def test_february_2027_seat_change_uses_28_days(self):
        s = sub("pro", 2, date(2026, 5, 1))
        inv = generate_invoice(s, [Event("quantity_change", date(2027, 2, 15), quantity=4)], date(2027, 2, 1))
        self.assertEqual([a for _, a in lines(inv)], [2900, 5800])
        self.assertEqual(inv.subtotal, 8700)

    def test_mid_month_start(self):
        inv = generate_invoice(sub(start=date(2026, 12, 10)), [], date(2026, 12, 31))
        self.assertEqual(lines(inv), [("Basic x 1 (22 of 31 days)", 639)])

    def test_trial_then_paid_days(self):
        s = sub("team", 1, date(2026, 12, 1), trial_end=date(2026, 12, 11))
        inv = generate_invoice(s, [], date(2026, 12, 5))
        self.assertEqual(lines(inv), [
            ("Setup fee: Team", 9900),
            ("Trial: Team x 1 (10 days)", 0),
            ("Team x 1 (21 of 31 days)", 3319),
        ])

    def test_full_month_is_not_prorated(self):
        inv = generate_invoice(sub(), [], date(2026, 12, 1))
        self.assertEqual(lines(inv), [("Basic x 1", 900)])

    def test_tax_on_new_numbers(self):
        s = sub(tax_rate="0.1")
        inv = generate_invoice(s, [Event("plan_change", date(2026, 12, 16), plan_id="pro")], date(2026, 12, 20))
        self.assertEqual((inv.subtotal, inv.tax, inv.total), (1932, 193, 2125))

    def test_october_2026_keeps_30_days(self):
        inv = generate_invoice(sub(), [Event("plan_change", date(2026, 10, 16), plan_id="pro")], date(2026, 10, 20))
        self.assertEqual(lines(inv), [("Basic x 1 (15 of 30 days)", 450), ("Pro x 1 (16 of 30 days)", 1547)])

    def test_february_2026_keeps_30_days(self):
        s = sub("basic", 2, date(2025, 9, 1))
        inv = generate_invoice(s, [Event("plan_change", date(2026, 2, 15), plan_id="pro")], date(2026, 2, 15))
        self.assertEqual(lines(inv), [("Basic x 2 (14 of 30 days)", 840), ("Pro x 2 (14 of 30 days)", 2707)])


if __name__ == "__main__":
    unittest.main()
