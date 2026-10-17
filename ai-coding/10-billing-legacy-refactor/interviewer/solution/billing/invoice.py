"""Invoice generation for subscriptions.

generate_invoice(subscription, events, as_of) builds the invoice for the
calendar month that contains as_of. Finance reconciles against these numbers,
so the output for any month already invoiced must never change.
"""
from billing import catalog
from billing.discounts import coupon_applies, discount_for, tax_for
from billing.lines import seat_lines, setup_fee_lines, usage_lines
from billing.models import Invoice, Line
from billing.period import billing_period
from billing.segments import seat_segments


def generate_invoice(subscription, events, as_of):
    sub = subscription
    period_start, period_end = billing_period(as_of)
    inv = Invoice(sub.id, period_start, period_end)
    if sub.start >= period_end:
        return inv

    segments = seat_segments(sub, events, period_start, period_end)
    lines = setup_fee_lines(sub, period_start)
    lines += seat_lines(sub, segments, period_start, period_end)
    lines += usage_lines(sub, events, segments)
    subtotal = sum(line.amount for line in lines)

    discount = 0
    if sub.coupon_id is not None:
        coupon = catalog.COUPONS[sub.coupon_id]
        if coupon_applies(coupon, sub.start, period_start):
            discount = discount_for(coupon, subtotal)
            if discount:
                lines.append(Line(f"Coupon {coupon.id}", -discount))

    taxable = subtotal - discount
    inv.lines = lines
    inv.subtotal = subtotal
    inv.discount = discount
    inv.tax = tax_for(taxable, sub.tax_rate)
    inv.total = taxable + inv.tax
    return inv
