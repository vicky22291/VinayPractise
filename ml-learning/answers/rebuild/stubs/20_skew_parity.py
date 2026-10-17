"""Rebuild 20: one feature definition written twice, batch and serving, plus the parity check, from memory.

Write the three bodies, then run from the module folder: python rebuild/20_skew_parity.py
check() compares both paths with a brute-force numpy count, never with the lab's results.
"""
from collections import deque

import numpy as np

HOUR = np.timedelta64(1, "h")


def batch_counts(event_times, query_times):
    """Pickups in [t - 1 h, t) for each query time t, with two np.searchsorted calls.

    event_times: one zone's pickup times, sorted, numpy datetime64. query_times: numpy datetime64.
    A pickup exactly at t - 1 h counts; a pickup at t does not, so a query never counts its own
    pickup. Both arrays are on one clock, the trip file's local time: never convert one side.
    Return an int array, one count per query time.
    """
    raise NotImplementedError("write this from memory")


def serving_counts(event_times, query_times):
    """The same count as batch_counts(), computed the way a stream processor does it.

    One pass over the time-ordered pickups with a deque, no searchsorted. query_times are sorted.
    Return an int array, one count per query time, in query order.
    """
    raise NotImplementedError("write this from memory")


def mismatch_rate(a, b):
    """The share of positions where two count arrays differ, a float from 0 to 1."""
    raise NotImplementedError("write this from memory")


def check():
    rng = np.random.default_rng(20)
    start = np.datetime64("2024-01-01T00:00:00", "s")
    events = np.sort(start + rng.integers(0, 7 * 86400, 20_000).astype("timedelta64[s]"))
    queries = np.sort(rng.choice(events, 1_000, replace=False))  # every query is itself a pickup
    events = np.sort(np.concatenate([events, queries[::10] - HOUR]))  # some pickups exactly 1 h before a query
    brute = np.array([((events >= t - HOUR) & (events < t)).sum() for t in queries])
    a, b = batch_counts(events, queries), serving_counts(events, queries)
    assert np.array_equal(a, brute), "batch_counts() differs from a brute-force count of [t - 1 h, t)"
    assert np.array_equal(b, brute), "serving_counts() differs from a brute-force count of [t - 1 h, t)"
    assert mismatch_rate(a, b) == 0.0 and mismatch_rate(a, a + 1) == 1.0, "mismatch_rate() is off"
    print("check: PASS")


if __name__ == "__main__":
    check()
