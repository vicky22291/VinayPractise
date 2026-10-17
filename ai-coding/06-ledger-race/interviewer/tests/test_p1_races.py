import random
import threading
import unittest

from ledger import Ledger
from ledger.reconcile import reconcile
from ledger_helpers import FastSwitching, assert_books_balance, attempt, run_threads


class Part1Races(unittest.TestCase):
    def test_concurrent_withdrawals_never_overdraw(self):
        with FastSwitching():
            for _ in range(15):
                ledger = Ledger()
                ledger.open_account("a", balance=1_000)
                ledger.open_account("b")
                barrier = threading.Barrier(30)
                wins = []

                def spend():
                    barrier.wait()
                    if attempt(ledger, "a", "b", 100):
                        wins.append(1)

                self.assertEqual(run_threads([spend] * 30), [], "stuck threads")
                self.assertLessEqual(len(wins), 10)
                self.assertGreaterEqual(ledger.balance("a"), 0)
                self.assertEqual(ledger.balance("a") + ledger.balance("b"), 1_000)
                assert_books_balance(self, ledger, ["a", "b"])

    def test_deposits_during_transfers_are_not_lost(self):
        with FastSwitching():
            ledger = Ledger()
            ledger.open_account("a", balance=100_000)
            ledger.open_account("b")

            def deposit():
                for _ in range(400):
                    ledger.deposit("a", 1)

            def move():
                for _ in range(400):
                    attempt(ledger, "a", "b", 3)

            self.assertEqual(run_threads([deposit] * 4 + [move] * 4), [], "stuck threads")
            self.assertEqual(ledger.balance("a") + ledger.balance("b"), 100_000 + 4 * 400)
            assert_books_balance(self, ledger, ["a", "b"])

    def test_opposite_transfers_do_not_deadlock(self):
        with FastSwitching():
            ledger = Ledger()
            ledger.open_account("a", balance=10_000)
            ledger.open_account("b", balance=10_000)

            def a_to_b():
                for _ in range(500):
                    attempt(ledger, "a", "b", 1)

            def b_to_a():
                for _ in range(500):
                    attempt(ledger, "b", "a", 1)

            self.assertEqual(run_threads([a_to_b, b_to_a] * 3), [], "deadlock: threads still waiting")
            self.assertEqual(ledger.total(), 20_000)

    def test_three_account_cycle_does_not_deadlock(self):
        with FastSwitching():
            ledger = Ledger()
            for name in "abc":
                ledger.open_account(name, balance=10_000)
            loops = [lambda s=s, d=d: [attempt(ledger, s, d, 1) for _ in range(500)]
                     for s, d in [("a", "b"), ("b", "c"), ("c", "a")]]
            self.assertEqual(run_threads(loops * 2), [], "deadlock: threads still waiting")
            self.assertEqual(ledger.total(), 30_000)

    def test_transfer_to_same_account_returns_quickly(self):
        ledger = Ledger()
        ledger.open_account("a", balance=500)
        rows_before = len(ledger.journal.rows())
        moved = []
        self.assertEqual(run_threads([lambda: moved.append(attempt(ledger, "a", "a", 10))], timeout=2), [],
                         "transfer to the same account never returned")
        self.assertEqual(moved, [False])
        self.assertEqual(ledger.balance("a"), 500)
        self.assertEqual(len(ledger.journal.rows()), rows_before)

    def test_busy_night_reconciles(self):
        accounts = [f"acct_{i}" for i in range(5)]
        with FastSwitching():
            for seed in range(3):
                ledger = Ledger()
                for a in accounts:
                    ledger.open_account(a, balance=5_000)

                def worker(s):
                    rng = random.Random(s)
                    for _ in range(300):
                        if rng.random() < 0.25:
                            ledger.deposit(rng.choice(accounts), rng.randint(1, 50))
                        else:
                            src, dst = rng.sample(accounts, 2)
                            attempt(ledger, src, dst, rng.randint(1, 2_500))

                workers = [lambda s=seed * 100 + i: worker(s) for i in range(8)]
                self.assertEqual(run_threads(workers), [], "stuck threads")
                report = reconcile(ledger)
                self.assertTrue(report.ok, report.problems)


if __name__ == "__main__":
    unittest.main()
