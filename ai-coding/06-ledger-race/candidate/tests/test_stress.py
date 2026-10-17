"""A busy payout night in miniature. Threads are daemons and joined with a
timeout, so a stuck run fails the test instead of hanging the suite."""
import random
import sys
import threading
import time
import unittest

from ledger import Ledger
from ledger.errors import LedgerError
from ledger.reconcile import reconcile

ACCOUNTS = [f"acct_{i}" for i in range(4)]


class StressTest(unittest.TestCase):
    def setUp(self):
        self._interval = sys.getswitchinterval()
        sys.setswitchinterval(1e-6)

    def tearDown(self):
        sys.setswitchinterval(self._interval)

    def test_busy_night_reconciles(self):
        ledger = Ledger()
        for account_id in ACCOUNTS:
            ledger.open_account(account_id, balance=5_000)

        def worker(seed):
            rng = random.Random(seed)
            for _ in range(300):
                try:
                    if rng.random() < 0.2:
                        ledger.deposit(rng.choice(ACCOUNTS), rng.randint(1, 100))
                    else:
                        src, dst = rng.sample(ACCOUNTS, 2)
                        ledger.transfer(src, dst, rng.randint(1, 2_000))
                except LedgerError:
                    pass

        threads = [threading.Thread(target=worker, args=(s,), daemon=True) for s in range(8)]
        for t in threads:
            t.start()
        deadline = time.monotonic() + 10
        for t in threads:
            t.join(timeout=max(0, deadline - time.monotonic()))
        self.assertFalse(any(t.is_alive() for t in threads), "workers stuck: possible deadlock")
        report = reconcile(ledger)
        self.assertTrue(report.ok, report.problems)


if __name__ == "__main__":
    unittest.main()
