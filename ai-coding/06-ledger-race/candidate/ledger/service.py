"""Balance operations: deposits from card settlements and transfers between
merchant accounts (platform fees, connected-account payouts)."""
import logging

from ledger.accounts import Accounts
from ledger.errors import InsufficientFunds, InvalidTransfer
from ledger.journal import EXTERNAL, Journal

log = logging.getLogger(__name__)


def _check_amount(amount):
    if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
        raise InvalidTransfer(f"amount must be a positive number of cents, got {amount!r}")


class Ledger:
    def __init__(self):
        self.accounts = Accounts()
        self.journal = Journal()

    def open_account(self, account_id, balance=0):
        self.accounts.add(account_id)
        if balance:
            self.deposit(account_id, balance)

    def balance(self, account_id):
        return self.accounts.get(account_id).balance

    def total(self):
        return sum(self.balance(a) for a in self.accounts.ids())

    def deposit(self, account_id, amount):
        """Money arriving from outside, e.g. a card settlement. Returns the entry id."""
        _check_amount(amount)
        account = self.accounts.get(account_id)
        entry_id = self.journal.next_id("dep")
        new_balance = account.balance + amount
        self.journal.post(entry_id, EXTERNAL, account_id, amount, memo="deposit")
        account.balance = new_balance
        return entry_id

    def transfer(self, src, dst, amount, idempotency_key=None):
        """Move amount from src to dst. Returns the transfer id."""
        _check_amount(amount)
        source, dest = self.accounts.get(src), self.accounts.get(dst)
        if source.balance < amount:
            raise InsufficientFunds(f"{src} has {source.balance}, needs {amount}")
        transfer_id = self.journal.next_id("tr")
        with source.lock:
            with dest.lock:
                self.journal.post(transfer_id, src, dst, amount, memo=idempotency_key or "")
                source.balance -= amount
                dest.balance += amount
        log.debug("transfer %s: %s -> %s %d", transfer_id, src, dst, amount)
        return transfer_id
