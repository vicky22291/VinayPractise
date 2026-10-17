import unittest

from ledger import Ledger, run_batch
from ledger.reconcile import reconcile


class ReconcileTest(unittest.TestCase):
    def test_quiet_day_reconciles(self):
        ledger = Ledger()
        for i in range(4):
            ledger.open_account(f"acct_{i}", balance=500)
        run_batch(ledger, [{"src": "acct_0", "dst": "acct_1", "amount": 100}] * 3, workers=1)
        report = reconcile(ledger)
        self.assertTrue(report.ok, report.problems)
        self.assertEqual(ledger.balance("acct_1"), 800)

    def test_detects_drift(self):
        ledger = Ledger()
        ledger.open_account("acct_0", balance=500)
        ledger.accounts.get("acct_0").balance += 1
        self.assertFalse(reconcile(ledger).ok)


if __name__ == "__main__":
    unittest.main()
