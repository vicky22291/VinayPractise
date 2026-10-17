"""Golden master: every fixture subscription, every month from 2025-06 to 2026-10.

Recorded from the legacy code before any change, including BILL-212. Periods
from 2026-11 on are covered by test_real_days.py. Re-record only on purpose:
    python3 -m tests.test_characterization --record
"""
import dataclasses
import json
import os
import sys
import unittest
from datetime import date

from billing.invoice import generate_invoice
from billing.loader import load_subscriptions

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SNAPSHOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "snapshots", "fixtures.json")
MONTHS = [date(2025, m, 15) for m in range(6, 13)] + [date(2026, m, 15) for m in range(1, 11)]


def render():
    out = {}
    for sub, events in load_subscriptions(os.path.join(ROOT, "fixtures", "subscriptions.json")):
        for as_of in MONTHS:
            inv = generate_invoice(sub, events, as_of)
            out[f"{sub.id} {as_of:%Y-%m}"] = json.loads(json.dumps(dataclasses.asdict(inv), default=str))
    return out


class GoldenMaster(unittest.TestCase):
    def test_fixtures_match_snapshot(self):
        with open(SNAPSHOT) as f:
            want = json.load(f)
        got = render()
        self.assertEqual(sorted(got), sorted(want))
        for key in want:
            with self.subTest(key=key):
                self.assertEqual(got[key], want[key])


if __name__ == "__main__":
    if "--record" in sys.argv:
        with open(SNAPSHOT, "w") as f:
            json.dump(render(), f, indent=1, sort_keys=True)
        print(f"recorded {SNAPSHOT}")
    else:
        unittest.main()
