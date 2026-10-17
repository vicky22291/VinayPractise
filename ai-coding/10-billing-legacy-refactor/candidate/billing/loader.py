"""Read subscriptions and their events from JSON."""
import json
from datetime import date

from billing.models import Event, Subscription


def _date(raw):
    return date.fromisoformat(raw) if raw else None


def load_subscriptions(path):
    """Return a list of (Subscription, [Event]) pairs."""
    with open(path) as f:
        raw = json.load(f)
    out = []
    for s in raw:
        events = [Event(e["kind"], _date(e["at"]), e.get("plan_id"), e.get("quantity")) for e in s.get("events", [])]
        sub = Subscription(
            id=s["id"],
            customer_id=s["customer_id"],
            plan_id=s["plan_id"],
            quantity=s["quantity"],
            start=_date(s["start"]),
            trial_end=_date(s.get("trial_end")),
            coupon_id=s.get("coupon_id"),
            tax_rate=s.get("tax_rate", "0"),
        )
        out.append((sub, events))
    return out
