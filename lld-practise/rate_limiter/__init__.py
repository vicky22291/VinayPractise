"""Rate limiter: decide whether a key may make another call in its time period.

    limiter = SlidingWindowLogRateLimiter()
    limiter.allow("user-42", period_seconds=60, max_calls=100)  # -> True / False
"""

from .base import Clock, RateLimiter
from .fixed_window import FixedWindowRateLimiter
from .sliding_window_log import SlidingWindowLogRateLimiter

__all__ = [
    "Clock",
    "RateLimiter",
    "FixedWindowRateLimiter",
    "SlidingWindowLogRateLimiter",
]
