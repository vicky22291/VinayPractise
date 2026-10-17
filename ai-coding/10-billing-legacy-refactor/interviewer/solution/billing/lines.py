"""Invoice lines: setup fee, seats (with trial and proration) and metered usage."""
from billing import catalog
from billing.models import Line
from billing.pricing import proration_days, prorate, seat_unit_price
from billing.segments import segment_on


def setup_fee_lines(sub, period_start):
    if sub.start < period_start:
        return []
    plan = catalog.PLANS[sub.plan_id]
    return [Line(f"Setup fee: {plan.name}", plan.setup_fee)] if plan.setup_fee else []


def _trial_days(sub, seg):
    if sub.trial_end is None or sub.trial_end <= seg.start:
        return 0
    return min((sub.trial_end - seg.start).days, seg.days)


def seat_lines(sub, segments, period_start, period_end):
    month_days = proration_days(period_start, period_end)
    lines = []
    for seg in segments:
        if seg.days <= 0 or seg.quantity == 0:
            continue
        plan = catalog.PLANS[seg.plan_id]
        unit = seat_unit_price(plan, seg.quantity)
        trial_days = _trial_days(sub, seg)
        if trial_days > 0:
            lines.append(Line(f"Trial: {plan.name} x {seg.quantity} ({trial_days} days)", 0))
        paid_days = seg.days - trial_days
        if paid_days <= 0:
            continue
        full = seg.start == period_start and seg.end == period_end and trial_days == 0
        if full:
            lines.append(Line(f"{plan.name} x {seg.quantity}", unit * seg.quantity))
        else:
            amount = prorate(unit * seg.quantity, paid_days, month_days)
            lines.append(Line(f"{plan.name} x {seg.quantity} ({paid_days} of {month_days} days)", amount))
    return lines


def usage_lines(sub, events, segments):
    """One line per metered plan, priced at the plan in force on each usage date."""
    units = {}  # plan_id -> units, in order of first billable usage
    for ev in sorted((e for e in events if e.kind == "usage"), key=lambda e: e.at):
        seg = segment_on(segments, ev.at)
        if seg is None or seg.quantity == 0:
            continue  # outside the period, before the start, or after a cancel
        if sub.trial_end is not None and ev.at < sub.trial_end:
            continue
        if catalog.PLANS[seg.plan_id].usage_unit_amount:
            units[seg.plan_id] = units.get(seg.plan_id, 0) + ev.quantity
    lines = []
    for plan_id, n in units.items():
        plan = catalog.PLANS[plan_id]
        lines.append(Line(f"{plan.name} usage ({n} units)", n * plan.usage_unit_amount))
    return lines
