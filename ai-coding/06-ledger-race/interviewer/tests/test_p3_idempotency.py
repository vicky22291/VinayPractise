import threading
import unittest

from ledger import Ledger, run_batch
from ledger.errors import IdempotencyKeyReused
from ledger_helpers import FastSwitching, assert_books_balance, run_threads


class Part3Idempotency(unittest.TestCase):
    def setUp(self):
        self.ledger = Ledger()
        self.ledger.open_account("a", balance=1_000)
        self.ledger.open_account("b")

    def test_retry_returns_original_result(self):
        first = self.ledger.transfer("a", "b", 100, idempotency_key="k1")
        again = self.ledger.transfer("a", "b", 100, idempotency_key="k1")
        self.assertEqual(first, again)
        self.assertEqual(self.ledger.balance("a"), 900)

    def test_different_params_raise(self):
        self.ledger.transfer("a", "b", 100, idempotency_key="k1")
        for args in [("a", "b", 101), ("b", "a", 100)]:
            with self.subTest(args=args):
                with self.assertRaises(IdempotencyKeyReused):
                    self.ledger.transfer(*args, idempotency_key="k1")
        self.assertEqual(self.ledger.balance("a"), 900)

    def test_rejection_is_remembered(self):
        first = self.ledger.transfer("b", "a", 50, idempotency_key="k2")
        self.assertEqual(first.status, "rejected")
        self.ledger.deposit("b", 500)
        self.assertEqual(self.ledger.transfer("b", "a", 50, idempotency_key="k2"), first)
        self.assertEqual(self.ledger.balance("b"), 500)

    def test_no_key_means_no_dedupe(self):
        self.ledger.transfer("a", "b", 100)
        self.ledger.transfer("a", "b", 100)
        self.assertEqual(self.ledger.balance("a"), 800)

    def test_concurrent_same_key_moves_money_once(self):
        with FastSwitching():
            for round_ in range(10):
                ledger = Ledger()
                ledger.open_account("a", balance=1_000)
                ledger.open_account("b")
                barrier = threading.Barrier(16)
                results = []

                def call():
                    barrier.wait()
                    results.append(ledger.transfer("a", "b", 100, idempotency_key=f"same-{round_}"))

                self.assertEqual(run_threads([call] * 16), [])
                self.assertEqual(ledger.balance("a"), 900)
                self.assertEqual(len({r.transfer_id for r in results}), 1)
                self.assertEqual(len(results), 16)
                assert_books_balance(self, ledger, ["a", "b"])

    def test_run_batch_retry_of_whole_batch(self):
        requests = [{"src": "a", "dst": "b", "amount": 10, "idempotency_key": f"po-{i}"} for i in range(20)]
        first = run_batch(self.ledger, requests)
        second = run_batch(self.ledger, requests)
        self.assertEqual(first, second)
        self.assertEqual(self.ledger.balance("b"), 200)


if __name__ == "__main__":
    unittest.main()
