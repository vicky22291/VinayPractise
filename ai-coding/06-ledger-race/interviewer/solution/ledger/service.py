"""Balance operations: deposits from card settlements, transfers between
merchant accounts, and payouts to merchants' banks."""
import logging
import threading
from dataclasses import dataclass, field

from ledger.accounts import Accounts, locked
from ledger.bank import BankDeclined, BankTimeout
from ledger.errors import IdempotencyKeyReused, InvalidTransfer, UnknownAccount
from ledger.journal import BANK, EXTERNAL, PENDING, Journal
from ledger.models import PayoutResult, TransferResult

log = logging.getLogger(__name__)


def _check_amount(amount):
    if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
        raise InvalidTransfer(f"amount must be a positive number of cents, got {amount!r}")


@dataclass
class _Slot:
    """One idempotency key: its parameters and, once done, its result."""
    params: tuple
    done: threading.Event = field(default_factory=threading.Event)
    result: object = None
    error: BaseException | None = None


@dataclass
class _Payout:
    account_id: str
    amount: int
    status: str = "new"  # new | pending | paid | declined | rejected
    reference: str | None = None
    lock: threading.Lock = field(default_factory=threading.Lock)


class Ledger:
    def __init__(self):
        self.accounts = Accounts()
        self.journal = Journal()
        self._rejections = []
        self._rejections_lock = threading.Lock()
        self._keys = {}
        self._keys_lock = threading.Lock()
        self._payouts = {}
        self._payouts_lock = threading.Lock()

    # -- accounts -----------------------------------------------------------

    def open_account(self, account_id, balance=0, overdraft_limit=0):
        self.accounts.add(account_id, overdraft_limit)
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
        with account.lock:
            self.journal.post(entry_id, EXTERNAL, account_id, amount, memo="deposit")
            account.balance += amount
        return entry_id

    # -- transfers ----------------------------------------------------------

    def transfer(self, src, dst, amount, idempotency_key=None):
        """Move amount from src to dst. Returns a TransferResult."""
        if idempotency_key is None:
            return self._transfer(src, dst, amount)
        return self._once(idempotency_key, (src, dst, amount), lambda: self._transfer(src, dst, amount))

    def rejections(self):
        with self._rejections_lock:
            return list(self._rejections)

    def _reject(self, src, dst, amount, reason):
        with self._rejections_lock:
            self._rejections.append((src, dst, amount, reason))
        return TransferResult("rejected", None, reason)

    def _invalid(self, src, dst, amount):
        try:
            _check_amount(amount)
        except InvalidTransfer:
            return "invalid_amount"
        if src == dst:
            return "same_account"
        try:
            self.accounts.get(src), self.accounts.get(dst)
        except UnknownAccount:
            return "unknown_account"
        return None

    def _transfer(self, src, dst, amount):
        reason = self._invalid(src, dst, amount)
        if reason:
            return self._reject(src, dst, amount, reason)
        source, dest = self.accounts.get(src), self.accounts.get(dst)
        with locked(source, dest):
            if source.balance - amount < -source.overdraft_limit:
                outcome = None
            else:
                outcome = self.journal.next_id("tr")
                self.journal.post(outcome, src, dst, amount)
                source.balance -= amount
                dest.balance += amount
        if outcome is None:
            return self._reject(src, dst, amount, "insufficient_funds")
        log.debug("transfer %s: %s -> %s %d", outcome, src, dst, amount)
        return TransferResult("succeeded", outcome, None)

    def _once(self, key, params, run):
        """Run at most once per key. Same key, same params: the first result.
        Same key, other params: IdempotencyKeyReused. In flight: wait for it."""
        with self._keys_lock:
            slot = self._keys.get(key)
            owner = slot is None
            if owner:
                slot = self._keys[key] = _Slot(params)
        if slot.params != params:
            raise IdempotencyKeyReused(f"key {key!r} was used with {slot.params}")
        if owner:
            try:
                slot.result = run()
            except BaseException as e:  # not saved: a retry may run again
                slot.error = e
                with self._keys_lock:
                    del self._keys[key]
                raise
            finally:
                slot.done.set()
        else:
            slot.done.wait()
            if slot.error is not None:
                raise slot.error
        return slot.result

    # -- payouts ------------------------------------------------------------

    def payout(self, payout_id, account_id, amount, bank):
        """Send amount from account_id to the merchant's bank. Safe to retry."""
        with self._payouts_lock:
            record = self._payouts.setdefault(payout_id, _Payout(account_id, amount))
        if (record.account_id, record.amount) != (account_id, amount):
            raise IdempotencyKeyReused(f"payout {payout_id!r} was for {record.account_id} {record.amount}")
        with record.lock:
            if record.status == "new":
                record.status = self._reserve(payout_id, account_id, amount)
            if record.status != "pending":
                return PayoutResult(record.status, record.reference)
            return self._send(payout_id, record, bank)

    def resolve_pending(self, bank):
        """Retry every payout the bank has not confirmed, with the same payout id."""
        with self._payouts_lock:
            pending = [(pid, r) for pid, r in self._payouts.items() if r.status == "pending"]
        results = []
        for payout_id, record in pending:
            with record.lock:
                if record.status == "pending":
                    results.append(self._send(payout_id, record, bank))
                else:
                    results.append(PayoutResult(record.status, record.reference))
        return results

    def _reserve(self, payout_id, account_id, amount):
        try:
            _check_amount(amount)
            account = self.accounts.get(account_id)
        except (InvalidTransfer, UnknownAccount):
            return "rejected"
        with account.lock:
            if account.balance - amount < -account.overdraft_limit:
                return "rejected"
            self.journal.post(self.journal.next_id("po"), account_id, PENDING, amount, memo=payout_id)
            account.balance -= amount
        return "pending"

    def _send(self, payout_id, record, bank):
        # No account lock here: the bank call can be slow, and the money is
        # already reserved in PENDING, so other transfers cannot spend it.
        try:
            reference = bank.send(payout_id, record.account_id, record.amount)
        except BankTimeout:
            return PayoutResult("pending", None)
        except BankDeclined:
            account = self.accounts.get(record.account_id)
            with account.lock:
                self.journal.post(self.journal.next_id("po"), PENDING, record.account_id, record.amount, memo=payout_id)
                account.balance += record.amount
            record.status = "declined"
            return PayoutResult("declined", None)
        self.journal.post(self.journal.next_id("po"), PENDING, BANK, record.amount, memo=payout_id)
        record.status, record.reference = "paid", reference
        return PayoutResult("paid", reference)
