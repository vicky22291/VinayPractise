"""Sliding window log: keep the timestamp of every allowed call per key."""

import time
from collections import defaultdict, deque

from .base import Clock, RateLimiter


class SlidingWindowLogRateLimiter(RateLimiter):
    """Exact: never more than max_calls in any span of period_seconds.

    Costs O(max_calls) memory per key, one timestamp per allowed call.
    """

    def __init__(self, clock: Clock = time.monotonic) -> None:
        super().__init__(clock)
        self._logs: dict[str, deque[float]] = defaultdict(deque)

    def _allow(self, key: str, period_seconds: float, max_calls: int, now: float) -> bool:
        log = self._logs[key]
        # Timestamps are appended in clock order, so the oldest is on the left.
        while log and now - log[0] >= period_seconds:
            log.popleft()

        if len(log) >= max_calls:
            return False
        log.append(now)
        return True
