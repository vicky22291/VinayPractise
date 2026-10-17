"""Shared helpers for the hidden tests. Threads are daemons with one shared
deadline, so a deadlock fails a test instead of hanging the run."""
import sys
import threading
import time

from ledger.errors import LedgerError


class FastSwitching:
    """Context manager: switch threads every microsecond to surface races."""

    def __enter__(self):
        self.old = sys.getswitchinterval()
        sys.setswitchinterval(1e-6)

    def __exit__(self, *exc):
        sys.setswitchinterval(self.old)


def attempt(ledger, src, dst, amount, **kw):
    """True if the transfer moved money. Works whether failures raise or return a result."""
    try:
        result = ledger.transfer(src, dst, amount, **kw)
    except LedgerError:
        return False
    return getattr(result, "status", "succeeded") == "succeeded"


def run_threads(targets, timeout=10.0):
    """Start one daemon thread per callable. Returns the threads still alive at the deadline."""
    threads = [threading.Thread(target=t, daemon=True) for t in targets]
    for t in threads:
        t.start()
    deadline = time.monotonic() + timeout
    for t in threads:
        t.join(timeout=max(0.0, deadline - time.monotonic()))
    return [t for t in threads if t.is_alive()]


def assert_books_balance(test, ledger, accounts):
    test.assertTrue(ledger.journal.is_balanced(), "journal does not sum to zero")
    for a in accounts:
        test.assertEqual(ledger.balance(a), ledger.journal.net(a), f"{a}: balance disagrees with journal")
