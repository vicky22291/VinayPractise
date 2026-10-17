"""Named examples of today's rules, so a failure says which rule moved."""
import unittest
from datetime import date

from billing.invoice import generate_invoice
from billing.models import Event, Subscription


def sub(plan="basic", qty=1, start=date(2025, 1, 1), **kw):
    return Subscription("sub_x", "cus_x", plan, qty, start, **kw)


def amounts(inv):
    return [line.amount for line in inv.lines]


class LegacyRules(unittest.TestCase):
    def test_bill_212_is_pinned_until_november_2026(self):
        # 14 + 14 days in February are billed as 28/30 of a month
        inv = generate_invoice(sub("basic", 2), [Event("plan_change", date(2026, 2, 15), plan_id="pro")], date(2026, 2, 1))
        self.assertEqual(amounts(inv), [840, 2707])

    def test_volume_tiers_start_at_10_and_50_seats(self):
        self.assertEqual(amounts(generate_invoice(sub("pro", 9), [], date(2026, 1, 1))), [26100])
        self.assertEqual(amounts(generate_invoice(sub("pro", 10), [], date(2026, 1, 1))), [26100])
        self.assertEqual(amounts(generate_invoice(sub("pro", 50), [], date(2026, 1, 1))), [116000])

    def test_trial_end_day_is_paid(self):
        inv = generate_invoice(sub(start=date(2026, 1, 1), trial_end=date(2026, 1, 11)), [], date(2026, 1, 1))
        self.assertEqual([(l.description, l.amount) for l in inv.lines],
                         [("Trial: Basic x 1 (10 days)", 0), ("Basic x 1 (21 of 30 days)", 630)])

    def test_once_coupon_only_in_first_month(self):
        s = sub(start=date(2026, 1, 1), coupon_id="WELCOME20")
        self.assertEqual(generate_invoice(s, [], date(2026, 1, 1)).discount, 180)
        self.assertEqual(generate_invoice(s, [], date(2026, 2, 1)).discount, 0)

    def test_repeating_coupon_months(self):
        s = sub(start=date(2026, 1, 1), coupon_id="SAVE10X3")
        self.assertEqual([generate_invoice(s, [], date(2026, m, 1)).discount for m in (1, 3, 4)], [90, 90, 0])

    def test_amount_off_capped_at_subtotal(self):
        inv = generate_invoice(sub(start=date(2026, 1, 1), coupon_id="BIGCREDIT", tax_rate="0.1"), [], date(2026, 1, 1))
        self.assertEqual((inv.discount, inv.tax, inv.total), (900, 0, 0))

    def test_percent_rounds_half_up_and_tax_after_discount(self):
        s = sub("scale", 61, date(2026, 1, 1), coupon_id="HALF6", tax_rate="0.0825")
        inv = generate_invoice(s, [], date(2026, 1, 1))
        self.assertEqual((inv.subtotal, inv.discount, inv.tax), (634339, 317170, 26166))

    def test_tax_rounds_half_up(self):
        inv = generate_invoice(sub(tax_rate="0.0725"), [], date(2026, 1, 1))
        self.assertEqual(inv.tax, 65)  # 900 * 0.0725 = 65.25

    def test_setup_fee_first_invoice_only(self):
        s = sub("team", 1, date(2026, 1, 1))
        self.assertEqual(amounts(generate_invoice(s, [], date(2026, 1, 1))), [9900, 4900])
        self.assertEqual(amounts(generate_invoice(s, [], date(2026, 2, 1))), [4900])

    def test_cancel_mid_month(self):
        inv = generate_invoice(sub("pro", 1), [Event("cancel", date(2026, 1, 11))], date(2026, 1, 1))
        self.assertEqual(amounts(inv), [967])  # 10 of 30 days

    def test_december_period(self):
        inv = generate_invoice(sub(), [], date(2025, 12, 31))
        self.assertEqual((inv.period_start, inv.period_end), (date(2025, 12, 1), date(2026, 1, 1)))
        self.assertEqual(amounts(inv), [900])


if __name__ == "__main__":
    unittest.main()
