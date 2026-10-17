"""Coupons: when they apply and how much they take off."""
from decimal import Decimal

from billing.period import months_between
from billing.pricing import round_half_up


def coupon_applies(coupon, sub_start, period_start):
    months = months_between(sub_start, period_start)
    if coupon.duration == "forever":
        return True
    if coupon.duration == "once":
        return months == 0
    if coupon.duration == "repeating":
        return months < coupon.duration_in_months
    return False


def discount_for(coupon, subtotal):
    """Percent off rounds half up. Amount off never exceeds the subtotal."""
    if coupon.percent_off:
        return round_half_up(Decimal(subtotal) * Decimal(coupon.percent_off) / Decimal(100))
    if coupon.amount_off:
        return min(coupon.amount_off, subtotal)
    return 0


def tax_for(taxable, rate):
    return round_half_up(Decimal(taxable) * Decimal(rate))
