"""Fake bank API used for payouts in tests and local runs.

send() is idempotent on payout_id, like a real bank API with an idempotency
key: sending the same payout_id again moves no more money and returns the same
reference. Tests script outcomes with script(...).
"""
import threading


class BankDeclined(Exception):
    """The bank refused the payout. No money moved."""


class BankTimeout(Exception):
    """No answer from the bank. The money may or may not have moved."""


class Bank:
    OUTCOMES = {"ok", "decline", "timeout_before_send", "timeout_after_send", "slow"}

    def __init__(self):
        self._sent = {}  # payout_id -> (reference, account_id, amount)
        self._script = []
        self._lock = threading.Lock()
        self.calls = 0
        self.gate = threading.Event()  # a "slow" send waits for this

    def script(self, *outcomes):
        """Outcomes for the next new payouts, in order. Default is "ok"."""
        unknown = set(outcomes) - self.OUTCOMES
        if unknown:
            raise ValueError(f"unknown outcomes {unknown}")
        with self._lock:
            self._script.extend(outcomes)

    def send(self, payout_id, account_id, amount):
        with self._lock:
            self.calls += 1
            if payout_id in self._sent:
                reference, sent_account, sent_amount = self._sent[payout_id]
                if (sent_account, sent_amount) != (account_id, amount):
                    raise ValueError(f"payout {payout_id} resent with different details")
                return reference
            outcome = self._script.pop(0) if self._script else "ok"
        if outcome == "slow":
            self.gate.wait(timeout=5)
        with self._lock:
            if outcome == "decline":
                raise BankDeclined(payout_id)
            if outcome == "timeout_before_send":
                raise BankTimeout(payout_id)
            reference = f"bank_ref_{len(self._sent) + 1:04d}"
            self._sent[payout_id] = (reference, account_id, amount)
        if outcome == "timeout_after_send":
            raise BankTimeout(payout_id)
        return reference

    def total_sent(self):
        with self._lock:
            return sum(amount for _, _, amount in self._sent.values())

    def sent_count(self):
        with self._lock:
            return len(self._sent)
