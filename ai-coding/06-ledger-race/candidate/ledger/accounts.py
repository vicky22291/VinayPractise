"""Merchant accounts."""
import threading
from dataclasses import dataclass, field

from ledger.errors import UnknownAccount


@dataclass
class Account:
    account_id: str
    balance: int = 0  # cents
    lock: threading.Lock = field(default_factory=threading.Lock, repr=False, compare=False)


class Accounts:
    """Registry of accounts. Thread-safe for add and get."""

    def __init__(self):
        self._by_id = {}
        self._lock = threading.Lock()

    def add(self, account_id):
        with self._lock:
            if account_id in self._by_id:
                raise ValueError(f"account {account_id} already exists")
            account = Account(account_id)
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
