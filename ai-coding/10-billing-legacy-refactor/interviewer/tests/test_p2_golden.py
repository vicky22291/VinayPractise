"""Part 2: the refactor must not change a cent.

Compares generate_invoice against invoices recorded from the legacy code for
400 generated subscriptions, all in periods before 2026-11-01. To re-record
from a legacy checkout: cd <legacy repo> && python3 <this file> --record
"""
import dataclasses
import json
import os
import random
import sys
import unittest
from datetime import date, timedelta

GOLDEN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "golden_p2.json")
PLANS = ["basic", "pro", "team", "scale"]
COUPONS = [None, None, "WELCOME20", "SAVE10X3", "LOYAL15", "FIVEOFF", "BIGCREDIT", "HALF6"]
QTYS = [0, 1, 1, 2, 3, 5, 9, 10, 11, 25, 49, 50, 51, 120]
TAX = ["0", "0.0825", "0.2", "0.0725", "0.1"]
LAST = date(2026, 10, 31)


def _day(rng, lo, hi):
    return lo + timedelta(days=rng.randint(0, (hi - lo).days))


def cases(n=400, seed=212):
    from billing.models import Event, Subscription

    rng = random.Random(seed)
    for i in range(n):
        start = _day(rng, date(2023, 1, 1), date(2026, 9, 30))
        trial = start + timedelta(days=rng.randint(1, 45)) if rng.random() < 0.3 else None
        sub = Subscription(
            id=f"sub_{i:04d}",
            customer_id=f"cus_{i:04d}",
            plan_id=rng.choice(PLANS),
            quantity=rng.choice(QTYS),
            start=start,
            trial_end=trial,
            coupon_id=rng.choice(COUPONS),
            tax_rate=rng.choice(TAX),
        )
        events = []
        for _ in range(rng.choice([0, 0, 1, 1, 2, 3])):
            at = _day(rng, start - timedelta(days=30), min(start + timedelta(days=400), LAST))
            kind = rng.choice(["plan_change", "plan_change", "quantity_change", "quantity_change", "cancel"])
            if kind == "plan_change":
                events.append(Event(kind, at, plan_id=rng.choice(PLANS)))
            elif kind == "quantity_change":
                events.append(Event(kind, at, quantity=rng.choice(QTYS)))
            else:
                events.append(Event(kind, at))
        as_of = _day(rng, max(start - timedelta(days=20), date(2023, 1, 1)), LAST)
        yield sub, events, as_of


def as_json(inv):
    return json.loads(json.dumps(dataclasses.asdict(inv), default=str))


def current():
    from billing.invoice import generate_invoice

    return [as_json(generate_invoice(sub, events, as_of)) for sub, events, as_of in cases()]


class Part2Golden(unittest.TestCase):
    def test_matches_legacy_output(self):
        with open(GOLDEN) as f:
            golden = json.load(f)
        got = current()
        self.assertEqual(len(got), len(golden))
        diffs = [i for i, (a, b) in enumerate(zip(got, golden)) if a != b]
        if diffs:
            i = diffs[0]
            self.fail(f"{len(diffs)} of {len(golden)} invoices changed. First: case {i}\nwant {golden[i]}\ngot  {got[i]}")


if __name__ == "__main__":
    if "--record" in sys.argv:
        sys.path.insert(0, os.getcwd())
        with open(GOLDEN, "w") as f:
            json.dump(current(), f, indent=0)
        print(f"recorded {GOLDEN}")
    else:
        unittest.main()
