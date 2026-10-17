"""Clocks. Times are whole seconds since the Unix epoch."""
import time


class SystemClock:
    def now(self):
        return int(time.time())


class FakeClock:
    """A clock that only moves when told to. Used by tests and incident replays."""

    def __init__(self, start=0):
        self._now = start

    def now(self):
        return self._now

    def advance(self, seconds):
        self._now += seconds

    def set(self, t):
        if t < self._now:
            raise ValueError("clock cannot go backwards")
        self._now = t
