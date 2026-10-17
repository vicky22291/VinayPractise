"""Seat segments: stretches of the period with one plan and one seat count."""
from dataclasses import dataclass
from datetime import date

SEAT_EVENTS = ("plan_change", "quantity_change", "cancel")


@dataclass(frozen=True)
class Segment:
    start: date
    end: date
    plan_id: str
    quantity: int

    @property
    def days(self):
        return (self.end - self.start).days


def _apply(event, plan_id, qty):
    if event.kind == "plan_change":
        return event.plan_id, qty
    if event.kind == "quantity_change":
        return plan_id, event.quantity
    if event.kind == "cancel":
        return plan_id, 0
    return plan_id, qty


def seat_segments(sub, events, period_start, period_end):
    """Cut [max(start, period_start), period_end) at each seat change inside the period.

    Only seat events cut segments. Usage events never do.
    """
    plan_id, qty = sub.plan_id, sub.quantity
    changes = []
    for ev in sorted((e for e in events if e.kind in SEAT_EVENTS), key=lambda e: e.at):
        if ev.at < period_start:
            plan_id, qty = _apply(ev, plan_id, qty)
        elif ev.at < period_end:
            changes.append(ev)
    segments = []
    seg_start = max(sub.start, period_start)
    for ev in changes:
        if ev.at > seg_start:
            segments.append(Segment(seg_start, ev.at, plan_id, qty))
            seg_start = ev.at
        plan_id, qty = _apply(ev, plan_id, qty)
    segments.append(Segment(seg_start, period_end, plan_id, qty))
    return segments


def segment_on(segments, day):
    """The segment containing day, or None."""
    for seg in segments:
        if seg.start <= day < seg.end:
            return seg
    return None
