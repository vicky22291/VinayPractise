"""Run from lld-practise/:  python3 -m unittest -v"""

import threading
import time
import unittest

from rate_limiter import FixedWindowRateLimiter, RateLimiter, SlidingWindowLogRateLimiter

KEY = "user-1"
PERIOD = 10
MAX_CALLS = 3


class FakeClock:
    """Manually advanced clock, so no test ever sleeps."""

    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class RateLimiterContract:
    """Behaviour every strategy must share. Mixed into one TestCase per strategy."""

    limiter_cls: type[RateLimiter]

    def setUp(self) -> None:
        self.clock = FakeClock()
        self.limiter = self.limiter_cls(clock=self.clock)

    def calls(self, n: int, key: str = KEY, max_calls: int = MAX_CALLS) -> list[bool]:
        return [self.limiter.allow(key, PERIOD, max_calls) for _ in range(n)]

    def test_allows_up_to_max_calls_then_denies(self):
        self.assertEqual(self.calls(4), [True, True, True, False])

    def test_still_denies_just_before_period_ends(self):
        self.calls(3)
        self.clock.advance(PERIOD - 0.001)
        self.assertEqual(self.calls(1), [False])

    def test_allows_again_once_period_has_passed(self):
        self.calls(3)
        self.clock.advance(PERIOD)
        self.assertEqual(self.calls(4), [True, True, True, False])

    def test_keys_are_independent(self):
        self.calls(3, key="a")
        self.assertEqual(self.calls(1, key="b"), [True])
        self.assertEqual(self.calls(1, key="a"), [False])

    def test_denied_calls_do_not_extend_the_block(self):
        self.calls(3)  # t=0, limit reached
        for _ in range(9):  # hammer once per second while blocked
            self.clock.advance(1)
            self.calls(1)
        self.clock.advance(1)  # t=10, the original calls have aged out
        self.assertEqual(self.calls(1), [True])

    def test_zero_max_calls_denies_everything(self):
        self.assertEqual(self.calls(2, max_calls=0), [False, False])

    def test_rejects_invalid_arguments(self):
        for period, max_calls in [(0, 1), (-1, 1), (PERIOD, -1)]:
            with self.subTest(period=period, max_calls=max_calls):
                with self.assertRaises(ValueError):
                    self.limiter.allow(KEY, period, max_calls)

    def test_concurrent_callers_never_exceed_the_limit(self):
        # End-to-end check only. Under the GIL a race here is rare, so the
        # deterministic guard for the lock is LockingContractTest below.
        threads_count, calls_per_thread, max_calls = 20, 50, 100
        start_together = threading.Barrier(threads_count)
        allowed_per_thread = [0] * threads_count

        def worker(i: int) -> None:
            start_together.wait()
            allowed_per_thread[i] = sum(
                self.limiter.allow("hot-key", PERIOD, max_calls) for _ in range(calls_per_thread)
            )

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(threads_count)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(sum(allowed_per_thread), max_calls)


class FixedWindowRateLimiterTest(RateLimiterContract, unittest.TestCase):
    limiter_cls = FixedWindowRateLimiter

    def test_burst_across_window_boundary_lets_through_more_than_max(self):
        """The known flaw: 5 calls pass in 1 second against a 3 per 10s limit."""
        self.calls(1)  # t=0 opens window [0, 10)
        self.clock.advance(9)
        self.assertEqual(self.calls(2), [True, True])  # t=9, window now full
        self.clock.advance(1)
        self.assertEqual(self.calls(3), [True, True, True])  # t=10, fresh window


class SlidingWindowLogRateLimiterTest(RateLimiterContract, unittest.TestCase):
    limiter_cls = SlidingWindowLogRateLimiter

    def test_no_burst_across_window_boundary(self):
        """Same timeline as the fixed window flaw, but only one slot frees up."""
        self.calls(1)  # t=0
        self.clock.advance(9)
        self.assertEqual(self.calls(2), [True, True])  # t=9
        self.clock.advance(1)
        self.assertEqual(self.calls(2), [True, False])  # t=10, only the t=0 call aged out


class LockingContractTest(unittest.TestCase):
    """The base class must never run two _allow calls at once, for any strategy."""

    def test_allow_bodies_never_overlap(self):
        class SpyLimiter(RateLimiter):
            in_flight = 0
            max_in_flight = 0

            def _allow(self, key, period_seconds, max_calls, now):
                self.in_flight += 1
                self.max_in_flight = max(self.max_in_flight, self.in_flight)
                time.sleep(0.001)  # hand the CPU to other threads mid-algorithm
                self.in_flight -= 1
                return True

        limiter = SpyLimiter(clock=FakeClock())
        threads_count = 8
        start_together = threading.Barrier(threads_count)

        def worker() -> None:
            start_together.wait()
            limiter.allow(KEY, PERIOD, MAX_CALLS)

        threads = [threading.Thread(target=worker) for _ in range(threads_count)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(limiter.max_in_flight, 1)


if __name__ == "__main__":
    unittest.main()
