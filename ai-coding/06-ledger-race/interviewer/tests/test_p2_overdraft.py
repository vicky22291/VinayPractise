import threading
import unittest

from ledger import Ledger, run_batch
from ledger.reconcile import reconcile
from ledger_helpers import FastSwitching, assert_books_balance, run_threads


class Part2Overdraft(unittest.TestCase):
    def setUp(self):
        self.ledger = Ledger()
        self.ledger.open_account("a", balance=100, overdraft_limit=50)
        self.ledger.open_account("b")

    def test_result_shape_success(self):
        r = self.ledger.transfer("a", "b", 30)
        self.assertEqual((r.status, r.reason), ("succeeded", None))
        self.assertTrue(r.transfer_id)

    def test_overdraft_down_to_limit(self):
        self.assertEqual(self.ledger.transfer("a", "b", 150).status, "succeeded")
        self.assertEqual(self.ledger.balance("a"), -50)
        r = self.ledger.transfer("a", "b", 1)
        self.assertEqual((r.status, r.transfer_id, r.reason), ("rejected", None, "insufficient_funds"))
        self.assertEqual(self.ledger.balance("a"), -50)

    def test_default_limit_is_zero(self):
        r = self.ledger.transfer("b", "a", 1)
        self.assertEqual((r.status, r.reason), ("rejected", "insufficient_funds"))

    def test_rejection_reasons_do_not_raise(self):
        cases = [
            (("a", "zz", 10), "unknown_account"),
            (("zz", "a", 10), "unknown_account"),
            (("a", "b", 0), "invalid_amount"),
            (("a", "b", -5), "invalid_amount"),
            (("a", "a", 10), "same_account"),
        ]
        for args, reason in cases:
            with self.subTest(args=args):
                r = self.ledger.transfer(*args)
                self.assertEqual((r.status, r.transfer_id, r.reason), ("rejected", None, reason))

    def test_rejections_recorded(self):
        self.ledger.transfer("b", "a", 5)
        self.ledger.transfer("a", "zz", 5)
        self.assertEqual(self.ledger.rejections(), [("b", "a", 5, "insufficient_funds"), ("a", "zz", 5, "unknown_account")])

    def test_reconcile_accepts_balances_within_limit(self):
        self.ledger.transfer("a", "b", 140)
        report = reconcile(self.ledger)
        self.assertTrue(report.ok, report.problems)

    def test_concurrent_overdraft_respects_limit(self):
        with FastSwitching():
            for _ in range(10):
                ledger = Ledger()
                ledger.open_account("a", balance=100, overdraft_limit=200)
                ledger.open_account("b")
                barrier = threading.Barrier(20)

                def spend():
                    barrier.wait()
                    ledger.transfer("a", "b", 50)

                self.assertEqual(run_threads([spend] * 20), [])
                self.assertEqual(ledger.balance("a"), -200)
                self.assertEqual(len(ledger.rejections()), 14)
                assert_books_balance(self, ledger, ["a", "b"])

    def test_run_batch_returns_results_in_order(self):
        requests = [
            {"src": "a", "dst": "b", "amount": 100},
            {"src": "a", "dst": "b", "amount": 100},
            {"src": "a", "dst": "zz", "amount": 1},
        ]
        results = run_batch(self.ledger, requests, workers=1)
        self.assertEqual([r.status for r in results], ["succeeded", "rejected", "rejected"])
        self.assertEqual([r.reason for r in results], [None, "insufficient_funds", "unknown_account"])

    def test_run_batch_surfaces_unexpected_errors(self):
        real = self.ledger.transfer

        def flaky(src, dst, amount, idempotency_key=None):
            if amount == 7:
                raise RuntimeError("disk full")
            return real(src, dst, amount, idempotency_key)

        self.ledger.transfer = flaky
        results = run_batch(self.ledger, [{"src": "a", "dst": "b", "amount": 7}, {"src": "a", "dst": "b", "amount": 1}])
        self.assertEqual(results[0].status, "failed")
        self.assertIn("disk full", results[0].reason)
        self.assertEqual(results[1].status, "succeeded")


if __name__ == "__main__":
    unittest.main()
