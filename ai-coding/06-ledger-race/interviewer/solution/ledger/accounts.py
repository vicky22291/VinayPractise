"""Merchant accounts."""
import contextlib
import threading
from dataclasses import dataclass, field

from ledger.errors import UnknownAccount


@dataclass
class Account:
    account_id: str
    balance: int = 0  # cents
    overdraft_limit: int = 0  # the balance may go down to -overdraft_limit
    lock: threading.Lock = field(default_factory=threading.Lock, repr=False, compare=False)


@contextlib.contextmanager
def locked(*accounts):
    """Hold every account's lock, always taken in account_id order.

    Two transfers that need the same pair of locks ask for them in the same
    order, so neither can hold one while waiting for the other: no deadlock.
    """
    ordered = sorted({a.account_id: a for a in accounts}.values(), key=lambda a: a.account_id)
    with contextlib.ExitStack() as stack:
        for account in ordered:
            stack.enter_context(account.lock)
        yield


class Accounts:
    """Registry of accounts. Thread-safe for add and get."""

    def __init__(self):
        self._by_id = {}
        self._lock = threading.Lock()

    def add(self, account_id, overdraft_limit=0):
        with self._lock:
            if account_id in self._by_id:
                raise ValueError(f"account {account_id} already exists")
            account = Account(account_id, overdraft_limit=overdraft_limit)
            self._by_id[account_id] = account
            return account

    def get(self, account_id):
        try:
            return self._by_id[account_id]
        except KeyError:
            raise UnknownAccount(account_id) from None

    def ids(self):
        with self._lock:
            return sorted(self._by_id)
