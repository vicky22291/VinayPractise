import threading
import time
import unittest

from ledger import Ledger
from ledger.bank import Bank
from ledger.errors import IdempotencyKeyReused
from ledger.reconcile import reconcile
from ledger_helpers import FastSwitching, run_threads


class Part4Payouts(unittest.TestCase):
    def setUp(self):
        self.ledger = Ledger()
        self.ledger.open_account("m", balance=1_000)
        self.ledger.open_account("other")
        self.bank = Bank()

    def books_ok(self):
        report = reconcile(self.ledger)
        self.assertTrue(report.ok, report.problems)

    def test_paid(self):
        r = self.ledger.payout("po_1", "m", 300, self.bank)
        self.assertEqual(r.status, "paid")
        self.assertTrue(r.reference)
        self.assertEqual(self.ledger.balance("m"), 700)
        self.assertEqual(self.bank.total_sent(), 300)
        self.assertEqual(self.ledger.journal.net("bank"), 300)
        self.books_ok()

    def test_declined_releases_funds(self):
        self.bank.script("decline")
        r = self.ledger.payout("po_1", "m", 300, self.bank)
        self.assertEqual((r.status, r.reference), ("declined", None))
        self.assertEqual(self.ledger.balance("m"), 1_000)
        self.books_ok()

    def test_insufficient_funds_rejected_without_calling_bank(self):
        r = self.ledger.payout("po_1", "m", 5_000, self.bank)
        self.assertEqual(r.status, "rejected")
        self.assertEqual(self.bank.calls, 0)
        self.assertEqual(self.ledger.balance("m"), 1_000)

    def test_timeout_after_send_stays_pending_then_resolves_once(self):
        self.bank.script("timeout_after_send")
        r = self.ledger.payout("po_1", "m", 300, self.bank)
        self.assertEqual(r.status, "pending")
        self.assertEqual(self.ledger.balance("m"), 700, "reserved while pending")
        self.assertEqual(self.ledger.transfer("m", "other", 800).status, "rejected", "reserved money is not spendable")
        self.books_ok()
        resolved = self.ledger.resolve_pending(self.bank)
        self.assertEqual([x.status for x in resolved], ["paid"])
        self.assertEqual(self.bank.sent_count(), 1)
        self.assertEqual(self.bank.total_sent(), 300)
        self.assertEqual(self.ledger.balance("m"), 700)
        self.assertEqual(self.ledger.resolve_pending(self.bank), [])
        self.books_ok()

    def test_timeout_before_send_then_retry_pays_once(self):
        self.bank.script("timeout_before_send")
        self.assertEqual(self.ledger.payout("po_1", "m", 300, self.bank).status, "pending")
        r = self.ledger.payout("po_1", "m", 300, self.bank)
        self.assertEqual(r.status, "paid")
        self.assertEqual(self.bank.total_sent(), 300)
        self.assertEqual(self.ledger.balance("m"), 700)
        self.books_ok()

    def test_retry_after_paid_does_not_call_bank_or_move_money(self):
        first = self.ledger.payout("po_1", "m", 300, self.bank)
        calls = self.bank.calls
        self.assertEqual(self.ledger.payout("po_1", "m", 300, self.bank), first)
        self.assertEqual(self.ledger.balance("m"), 700)
        self.assertLessEqual(self.bank.calls, calls + 1)
        self.assertEqual(self.bank.total_sent(), 300)

    def test_same_payout_id_different_details_raises(self):
        self.ledger.payout("po_1", "m", 300, self.bank)
        with self.assertRaises(IdempotencyKeyReused):
            self.ledger.payout("po_1", "m", 301, self.bank)

    def test_concurrent_same_payout_moves_money_once(self):
        with FastSwitching():
            results = []
            barrier = threading.Barrier(12)

            def call():
                barrier.wait()
                results.append(self.ledger.payout("po_x", "m", 400, self.bank))

            self.assertEqual(run_threads([call] * 12), [])
        self.assertEqual({r.status for r in results}, {"paid"})
        self.assertEqual(self.bank.total_sent(), 400)
        self.assertEqual(self.ledger.balance("m"), 600)
        self.books_ok()

    def test_bank_call_does_not_hold_the_account(self):
        self.bank.script("slow")
        payout_done = []
        t = threading.Thread(target=lambda: payout_done.append(self.ledger.payout("po_1", "m", 800, self.bank)), daemon=True)
        t.start()
        deadline = time.monotonic() + 2
        while self.bank.calls == 0 and time.monotonic() < deadline:
            time.sleep(0.005)
        self.assertEqual(self.bank.calls, 1, "payout never reached the bank")
        moved = []
        self.assertEqual(run_threads([lambda: moved.append(self.ledger.transfer("m", "other", 150))], timeout=1), [],
                         "a transfer waited for the bank call")
        self.assertEqual(moved[0].status, "succeeded")
        self.assertEqual(self.ledger.transfer("m", "other", 100).status, "rejected", "only 200 was free")
        self.bank.gate.set()
        t.join(timeout=5)
        self.assertEqual(payout_done[0].status, "paid")
        self.assertEqual(self.ledger.balance("m"), 50)
        self.books_ok()


if __name__ == "__main__":
    unittest.main()
