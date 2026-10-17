import unittest

from ledger import Ledger
from ledger.errors import UnknownAccount


class LedgerTest(unittest.TestCase):
    def setUp(self):
        self.ledger = Ledger()
        self.ledger.open_account("acct_a", balance=1_000)
        self.ledger.open_account("acct_b")

    def test_opening_balance(self):
        self.assertEqual(self.ledger.balance("acct_a"), 1_000)
        self.assertEqual(self.ledger.balance("acct_b"), 0)

    def test_transfer_moves_money(self):
        self.ledger.transfer("acct_a", "acct_b", 300)
        self.assertEqual((self.ledger.balance("acct_a"), self.ledger.balance("acct_b")), (700, 300))

    def test_deposit(self):
        self.ledger.deposit("acct_b", 50)
        self.assertEqual(self.ledger.balance("acct_b"), 50)
        self.assertEqual(self.ledger.total(), 1_050)

    def test_journal_has_two_rows_per_transfer(self):
        self.ledger.transfer("acct_a", "acct_b", 300)
        rows = [r for r in self.ledger.journal.rows() if r.memo != "deposit"]
        self.assertEqual(sorted(r.amount for r in rows), [-300, 300])
        self.assertTrue(self.ledger.journal.is_balanced())

    def test_unknown_account(self):
        with self.assertRaises(UnknownAccount):
            self.ledger.balance("acct_missing")


if __name__ == "__main__":
    unittest.main()
