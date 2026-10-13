"""Fixed window counter: one counter per key, reset when its window ends."""

import time
from dataclasses import dataclass

from .base import Clock, RateLimiter


@dataclass(slots=True)
class _Window:
    start: float
    count: int


class FixedWindowRateLimiter(RateLimiter):
    """O(1) memory per key, but up to 2 * max_calls can pass across a window boundary.

    A key's window opens on its first call and covers
    [start, start + period_seconds). The first call after that opens a new one.
    """

    def __init__(self, clock: Clock = time.monotonic) -> None:
        super().__init__(clock)
        self._windows: dict[str, _Window] = {}

    def _allow(self, key: str, period_seconds: float, max_calls: int, now: float) -> bool:
        window = self._windows.get(key)
        if window is None or now - window.start >= period_seconds:
            window = _Window(start=now, count=0)
            self._windows[key] = window

        if window.count >= max_calls:
            return False
        window.count += 1
        return True
