import json
import random
import unittest

import kit08_data as data
import kit08_reference as reference
from payouts.models import BalanceTransaction, Merchant
from payouts.report import build_report, run_incremental
from payouts.store import Store


def roundtrip(checkpoint):
    return json.loads(json.dumps(checkpoint))


class Part3(unittest.TestCase):
    def setUp(self):
        self.ms = data.merchants(200, 51)
        self.store = Store(self.ms, data.transactions(self.ms, 30_000, 52), data.fx_rates())

    def test_first_run_equals_full_report(self):
        report, cp = run_incremental(self.store, data.DAY, None)
        self.assertEqual(report, reference.build_report(self.store, data.DAY))
        self.assertEqual(roundtrip(cp), cp)

    def test_late_rows_only(self):
        _, cp = run_incremental(self.store, data.DAY, None)
        rng = random.Random(53)
        newcomer = Merchant("acct_99999999", "Late Joiner", "gbp")
        self.store.add_merchant(newcomer)
        targets = [self.ms[0], self.ms[1], newcomer]
        for i in range(50):
            m = targets[i % 3]
            currency = "sgd" if i % 7 == 0 else m.payout_currency
            amount = rng.randint(100, 9_000)
            self.store.append(BalanceTransaction(f"late_{i}", m.id, "charge", amount, 30, currency, data.DAY))
        self.store.append(BalanceTransaction("late_other_day", self.ms[2].id, "charge", 500, 30, "usd", "2026-10-15"))

        rows, calls = self.store.rows_read, self.store.total_calls()
        report, cp2 = run_incremental(self.store, data.DAY, roundtrip(cp))
        self.assertEqual(self.store.rows_read - rows, 50)
        self.assertLessEqual(self.store.total_calls() - calls, 10, dict(self.store.calls))
        self.assertEqual(report, reference.build_report(self.store, data.DAY))
        self.assertEqual(report, build_report(self.store, data.DAY))

        rows = self.store.rows_read
        again, cp3 = run_incremental(self.store, data.DAY, roundtrip(cp2))
        self.assertEqual(again, report)
        self.assertEqual(roundtrip(cp3), roundtrip(cp2))
        self.assertEqual(self.store.rows_read - rows, 0)

    def test_checkpoint_is_not_mutated(self):
        _, cp = run_incremental(self.store, data.DAY, None)
        before = json.dumps(cp, sort_keys=True)
        self.store.append(BalanceTransaction("late_x", self.ms[0].id, "refund", -100, 0, "usd", data.DAY))
        run_incremental(self.store, data.DAY, cp)
        self.assertEqual(json.dumps(cp, sort_keys=True), before)

    def test_checkpoint_for_another_day(self):
        _, cp = run_incremental(self.store, data.DAY, None)
        with self.assertRaises(ValueError):
            run_incremental(self.store, "2026-10-15", cp)


if __name__ == "__main__":
    unittest.main()
