"""Shared contract for every rate limiting strategy."""

import threading
import time
from abc import ABC, abstractmethod
from typing import Callable

# Returns "now" in seconds. Injected so tests can control time without sleeping.
Clock = Callable[[], float]


class RateLimiter(ABC):
    """Decides whether `key` may make one more call, given at most
    `max_calls` calls per `period_seconds`.

    Subclasses implement only the algorithm in `_allow`. This base class owns
    argument validation, the clock, and the lock, so every strategy is thread
    safe in the same way (Template Method).
    """

    def __init__(self, clock: Clock = time.monotonic) -> None:
        # Monotonic, not wall clock: an NTP jump must not reset or extend limits.
        self._clock = clock
        self._lock = threading.Lock()

    def allow(self, key: str, period_seconds: float, max_calls: int) -> bool:
        """Return True and record the call if it fits the limit, else False.

        A denied call is not recorded, so a client that keeps retrying while
        blocked is not locked out forever.
        """
        if period_seconds <= 0:
            raise ValueError(f"period_seconds must be > 0, got {period_seconds}")
        if max_calls < 0:
            raise ValueError(f"max_calls must be >= 0, got {max_calls}")

        with self._lock:
            # Read the clock inside the lock so timestamps are stored in order.
            return self._allow(key, period_seconds, max_calls, self._clock())

    @abstractmethod
    def _allow(self, key: str, period_seconds: float, max_calls: int, now: float) -> bool:
        """Algorithm body. Always called with the lock held."""
