"""09 rebuild: the precision-recall curve from sorted scores, average precision and the cheapest threshold.

Write the three bodies from memory, then run: python rebuild/09_average_precision.py
check() compares with scikit-learn on synthetic scores, never with the lab's results.
"""
import numpy as np
from sklearn.metrics import average_precision_score, confusion_matrix, confusion_matrix_at_thresholds


def pr_curve(y, s):
    """Return thr, tp, fp: one row per distinct score, highest score first.

    Row k flags every row with s >= thr[k]: tp[k] positives and fp[k] negatives.
    Sort the scores descending and keep the last row of each tied score.
    """
    raise NotImplementedError("write this from memory")


def average_precision(y, s):
    """The sum over thresholds of (recall step) x precision, recall starting at 0. Not the trapezoid rule."""
    raise NotImplementedError("write this from memory")


def cheapest_threshold(y, s, cost_fn=5, cost_fp=1):
    """Return (t, cost) for the t with the lowest cost_fn * FN + cost_fp * FP, flagging s >= t; a tie goes to the highest t."""
    raise NotImplementedError("write this from memory")


def check():
    """50,000 synthetic rows at 0.17% positives, scores rounded to 2 decimals to force ties."""
    rng = np.random.default_rng(0)
    y = (rng.random(50_000) < 0.0017).astype(int)
    s = np.round(rng.normal(0.3 + 0.3 * y, 0.15), 2)
    assert 0 < y.sum() < 200 and len(np.unique(s)) < 200, "the fixture needs positives and ties"
    thr, tp, fp = pr_curve(y, s)
    _, fps, _, tps, thresholds = confusion_matrix_at_thresholds(y, s)
    assert np.array_equal(thr, thresholds) and np.array_equal(tp, tps) and np.array_equal(fp, fps), "pr_curve"
    ap, want = average_precision(y, s), average_precision_score(y, s)
    assert abs(ap - want) < 1e-12, f"average_precision gave {ap}, scikit-learn {want}"
    ts = np.unique(s)[::-1]  # brute force: price every distinct score, highest first
    costs = [5 * fn + fp for _, fp, fn, _ in (confusion_matrix(y, (s >= t).astype(int), labels=[0, 1]).ravel() for t in ts)]
    k = int(np.argmin(costs))
    assert tuple(cheapest_threshold(y, s)) == (ts[k], costs[k]), "cheapest_threshold"
    print("check: PASS")


if __name__ == "__main__":
    check()
