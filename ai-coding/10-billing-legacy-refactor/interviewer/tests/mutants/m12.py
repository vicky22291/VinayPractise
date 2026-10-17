"""Invoice generation for subscriptions.

generate_invoice(subscription, events, as_of) builds the invoice for the
calendar month that contains as_of. Finance reconciles against these numbers,
so the output for any month already invoiced must never change.
"""
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from billing import catalog
from billing.models import Invoice, Line


def generate_invoice(subscription, events, as_of):
    sub = subscription

    # billing period is the calendar month containing as_of
    period_start = date(as_of.year, as_of.month, 1)
    if as_of.month == 12:
        period_end = date(as_of.year + 1, 1, 1)
    else:
        period_end = date(as_of.year, as_of.month + 1, 1)

    inv = Invoice(sub.id, period_start, period_end)
    if sub.start >= period_end:
        return inv

    # replay events: what is in force when the period starts, and what changes inside it
    plan_id = sub.plan_id
    qty = sub.quantity
    changes = []
    for ev in sorted(events, key=lambda e: e.at):
        if ev.at < period_start:
            if ev.kind == "plan_change":
                plan_id = ev.plan_id
            elif ev.kind == "quantity_change":
                qty = ev.quantity
            elif ev.kind == "cancel":
                qty = 0
        elif ev.at < period_end:
            changes.append(ev)

    # cut the period into segments at each change
    segments = []
    seg_start = max(sub.start, period_start)
    for ev in changes:
        if ev.at > seg_start:
            segments.append((seg_start, ev.at, plan_id, qty))
            seg_start = ev.at
        if ev.kind == "plan_change":
            plan_id = ev.plan_id
        elif ev.kind == "quantity_change":
            qty = ev.quantity
    segments.append((seg_start, period_end, plan_id, qty))

    lines = []

    # one-off setup fee on the first invoice
    if sub.start >= period_start:
        first_plan = catalog.PLANS[sub.plan_id]
        if first_plan.setup_fee:
            lines.append(Line(f"Setup fee: {first_plan.name}", first_plan.setup_fee))

    for seg_start, seg_end, plan_id, qty in segments:
        days = (seg_end - seg_start).days
        if days <= 0 or qty == 0:
            continue
        plan = catalog.PLANS[plan_id]

        # volume pricing: 10 or more seats get 10% off the seat price, 50 or more get 20% off
        unit = plan.unit_amount
        if qty >= 50:
            unit = unit * 80 // 100
        elif qty >= 10:
            unit = unit * 90 // 100

        trial_days = 0
        if sub.trial_end is not None and sub.trial_end > seg_start:
            trial_days = min((sub.trial_end - seg_start).days, days)
        if trial_days > 0:
            lines.append(Line(f"Trial: {plan.name} x {qty} ({trial_days} days)", 0))
        paid_days = days - trial_days
        if paid_days <= 0:
            continue

        if seg_start == period_start and seg_end == period_end and trial_days == 0:
            lines.append(Line(f"{plan.name} x {qty}", unit * qty))
        else:
            # finance prorates on a 30 day month
            amount = Decimal(unit * qty) * Decimal(paid_days) / Decimal(30)
            amount = int(amount.quantize(Decimal(1), rounding=ROUND_HALF_UP))
            lines.append(Line(f"{plan.name} x {qty} ({paid_days} of 30 days)", amount))

    subtotal = 0
    for line in lines:
        subtotal += line.amount

    # coupons
    discount = 0
    if sub.coupon_id is not None:
        coupon = catalog.COUPONS[sub.coupon_id]
        months = (period_start.year - sub.start.year) * 12 + (period_start.month - sub.start.month)
        applies = False
        if coupon.duration == "forever":
            applies = True
        elif coupon.duration == "once":
            applies = months == 0
        elif coupon.duration == "repeating":
            applies = months < coupon.duration_in_months
        if applies:
            if coupon.percent_off:
                discount = Decimal(subtotal) * Decimal(coupon.percent_off) / Decimal(100)
                discount = int(discount.quantize(Decimal(1), rounding=ROUND_HALF_UP))
            elif coupon.amount_off:
                discount = min(coupon.amount_off, subtotal)
            if discount:
                lines.append(Line(f"Coupon {coupon.id}", -discount))

    taxable = subtotal - discount
    tax = Decimal(taxable) * Decimal(sub.tax_rate)
    tax = int(tax.quantize(Decimal(1), rounding=ROUND_HALF_UP))

    inv.lines = lines
    inv.subtotal = subtotal
    inv.discount = discount
    inv.tax = tax
    inv.total = taxable + tax
    return inv
