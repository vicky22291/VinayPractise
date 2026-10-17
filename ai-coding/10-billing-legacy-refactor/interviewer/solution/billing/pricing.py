"""Seat prices and proration."""
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

# BILL-212: periods starting on or after this date prorate by the real number
# of days. Earlier periods keep the 30-day rule so issued invoices regenerate
# to the cent.
REAL_DAYS_FROM = date(2026, 11, 1)
LEGACY_MONTH_DAYS = 30


def round_half_up(value):
    return int(Decimal(value).quantize(Decimal(1), rounding=ROUND_HALF_UP))


def seat_unit_price(plan, qty):
    """Volume pricing: 10+ seats get 10% off the seat price, 50+ get 20% off (floor)."""
    if qty >= 50:
        return plan.unit_amount * 80 // 100
    if qty >= 10:
        return plan.unit_amount * 90 // 100
    return plan.unit_amount


def proration_days(period_start, period_end):
    if period_start < REAL_DAYS_FROM:
        return LEGACY_MONTH_DAYS
    return (period_end - period_start).days


def prorate(full_amount, paid_days, month_days):
    return round_half_up(Decimal(full_amount) * Decimal(paid_days) / Decimal(month_days))
