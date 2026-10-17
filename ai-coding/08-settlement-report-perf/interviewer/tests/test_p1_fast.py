import hashlib
import os
import random
import time
import unittest
from pathlib import Path

import kit08_data as data
import kit08_reference as reference
from payouts.report import build_report
from payouts.store import Store

KIT = Path(__file__).resolve().parents[2]
FIX = Path(__file__).parent / "fixtures"
CALL_BUDGET = 20


def dataset(spec):
    ms = data.merchants(spec["merchants"], spec["mseed"])
    return ms, list(data.transactions(ms, spec["txns"], spec["tseed"]))


def first_diff(got, want):
    for i, (a, b) in enumerate(zip(got.splitlines(), want.splitlines()), 1):
        if a != b:
            return f"line {i}:\n  got  {a}\n  want {b}"
    return f"line counts differ: got {len(got.splitlines())}, want {len(want.splitlines())}"


class Part1(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ms, cls.txns = dataset(data.P1)

    def test_store_py_unchanged(self):
        versions = [KIT / "candidate" / "payouts" / "store.py"]
        versions += sorted((KIT / "interviewer" / "parts").glob("*/files/payouts/store.py"))
        allowed = {hashlib.sha256(p.read_bytes()).hexdigest() for p in versions}
        mine = hashlib.sha256(Path("payouts/store.py").read_bytes()).hexdigest()
        self.assertIn(mine, allowed, "payouts/store.py stands for the database: do not change it")

    def test_byte_identical_to_the_original_report(self):
        out = build_report(Store(self.ms, self.txns, data.fx_rates()), data.DAY)
        want = (FIX / "golden_p1.csv").read_text()
        if out != want:
            self.fail("report changed. " + first_diff(out, want))

    def test_round_trips_do_not_grow_with_data(self):
        store = Store(self.ms, self.txns, data.fx_rates())
        build_report(store, data.DAY)
        self.assertLessEqual(store.total_calls(), CALL_BUDGET, dict(store.calls))

    def test_fast_enough(self):
        store = Store(self.ms, self.txns, data.fx_rates())
        start = time.perf_counter()
        build_report(store, data.DAY)
        self.assertLess(time.perf_counter() - start, 5.0)

    def test_matches_original_on_odd_shapes(self):
        rng = random.Random(99)
        for case in range(12):
            ms = data.merchants(rng.randint(1, 25), 1000 + case)
            txns = list(data.transactions(ms, rng.choice([0, 1, 7, 300, 2000]), 2000 + case))
            with self.subTest(case=case, merchants=len(ms), txns=len(txns)):
                want = reference.build_report(Store(ms, txns, data.fx_rates()), data.DAY)
                got = build_report(Store(ms, txns, data.fx_rates()), data.DAY)
                if got != want:
                    self.fail(first_diff(got, want))


if __name__ == "__main__":
    unittest.main()
