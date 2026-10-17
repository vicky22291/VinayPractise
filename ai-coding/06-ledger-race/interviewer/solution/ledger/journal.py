"""Append-only double-entry journal.

Every movement of money is posted as two rows that sum to zero: a debit
(negative) on the account money leaves and a credit (positive) on the account
it enters. Finance reconciles balances against this journal every night.
"""
import itertools
import threading
from dataclasses import dataclass

EXTERNAL = "external"         # money entering from outside: card settlements, opening balances
PENDING = "payouts_pending"   # reserved for a payout the bank has not confirmed
BANK = "bank"                 # money that left to merchants' banks


@dataclass(frozen=True)
class Entry:
    entry_id: str
    account_id: str
    amount: int  # cents; negative = debit, positive = credit
    memo: str = ""


class Journal:
    def __init__(self):
        self._rows = []
        self._lock = threading.Lock()
        self._ids = itertools.count(1)

    def next_id(self, prefix):
        with self._lock:
            return f"{prefix}_{next(self._ids):06d}"

    def post(self, entry_id, from_account, to_account, amount, memo=""):
        """Record amount moving from from_account to to_account."""
        with self._lock:
            self._rows.append(Entry(entry_id, from_account, -amount, memo))
            self._rows.append(Entry(entry_id, to_account, amount, memo))

    def rows(self):
        with self._lock:
            return list(self._rows)

    def net(self, account_id):
        """Sum of all rows for one account."""
        return sum(e.amount for e in self.rows() if e.account_id == account_id)

    def is_balanced(self):
        return sum(e.amount for e in self.rows()) == 0
