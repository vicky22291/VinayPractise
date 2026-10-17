"""Rebuild for lab 02: the latency harness, written from memory.

Write the three bodies, then run: python rebuild/02_latency_harness.py
check() compares percentile() with numpy.percentile(method="inverted_cdf") at p50, p95 and p99,
then runs latency_report() and confident_share() on a fake model whose answers and delays are known.
"""
import math
import time

import numpy as np


def percentile(sorted_vals, q):
    """Nearest rank: the value at rank ceil(q/100 x n) of n values sorted ascending (rank 1 is the smallest)."""
    raise NotImplementedError("write this from memory")


def latency_report(predict, inputs, warmup=10):
    """Call predict on the first warmup inputs untimed, then time one call per input, in milliseconds.

    Time each call with time.perf_counter_ns. Return two things: a dict with the keys "p50", "p95"
    and "max" (milliseconds, the percentiles by nearest rank), and the list of predict's outputs,
    one per input, in input order.
    """
    raise NotImplementedError("write this from memory")


def confident_share(probs, threshold=0.9):
    """The share of inputs whose top class probability is above threshold (strictly above).

    probs is a list with one 1-D array or tensor of class probabilities per input.
    """
    raise NotImplementedError("write this from memory")


def check():
    """percentile() must equal numpy's inverted_cdf; the harness must skip warm-up and keep input order."""
    rng = np.random.default_rng(0)
    for n in (1, 7, 20, 199, 200, 1001):
        vals = sorted(rng.exponential(10.0, size=n).tolist())
        for q in (50, 95, 99):
            want = float(np.percentile(vals, q, method="inverted_cdf"))
            assert percentile(vals, q) == want, f"n={n} q={q}: got {percentile(vals, q)}, numpy gives {want}"

    calls = []

    def fake_predict(x):  # the first call ever is slow (a cold start); input 7 is always slow
        calls.append(x)
        time.sleep(0.2 if len(calls) == 1 else 0.02 if x == 7 else 0)
        return x * 10

    stats, outputs = latency_report(fake_predict, list(range(20)), warmup=3)
    assert calls == [0, 1, 2] + list(range(20)), "warm up on the first warmup inputs, then call once per input"
    assert outputs == [x * 10 for x in range(20)], "outputs must be predict's results, in input order"
    assert set(stats) >= {"p50", "p95", "max"}, "the report needs p50, p95 and max"
    assert stats["p50"] <= stats["p95"] <= stats["max"], "percentiles must be in order"
    assert 20 <= stats["max"] < 150, f"max {stats['max']:.1f} ms: the 20 ms call counts, the warm-up does not"
    assert stats["p50"] < 10, f"p50 {stats['p50']:.1f} ms should be a fast call; check the units (ms)"

    probs = rng.dirichlet(np.full(37, 0.05), size=500)  # 500 rows of 37 class probabilities each
    probs[0] = np.full(37, 0.1 / 36)
    probs[0][3] = 0.9  # exactly at the threshold: not above it
    want = float(np.mean(probs.max(axis=1) > 0.9))
    assert abs(confident_share(list(probs)) - want) < 1e-12, "confident_share disagrees with numpy"
    assert confident_share([probs[0]]) == 0.0, "a top probability equal to the threshold is not above it"
    print("check: PASS")


if __name__ == "__main__":
    check()
