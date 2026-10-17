"""Rebuild 23: ipw_recall(), a challenger's recall from labelled rows weighted by 1 / propensity.

Write the body from memory, then run: python rebuild/23_ipw_recall.py
check() compares it with numpy.average and scikit-learn's recall_score on a toy, never with this lab's results.
"""
import numpy as np
from sklearn.metrics import recall_score


def ipw_recall(declined_by_challenger, is_fraud, labeled, propensity, n_boot=200, rng=None):
    """Recall from the labelled rows only, each weighted by 1 / propensity, with a bootstrap interval.

    One entry per payment: the challenger's decline, the fraud label (read only where labeled), whether the
    payment was labelled, and its logged propensity, the probability that the policy let it be labelled.
    Returns (recall, lo, hi): lo and hi are the 2.5th and 97.5th percentiles of n_boot recalls, each on the
    rows resampled with replacement, drawn with rng (numpy.random.default_rng(0) when rng is None).
    """
    rng = np.random.default_rng(0) if rng is None else rng
    w = np.where(labeled, 1.0 / np.where(labeled, propensity, 1.0), 0.0) * (np.asarray(is_fraud) == 1)
    hit, boots = w * np.asarray(declined_by_challenger, dtype=float), []
    for _ in range(n_boot):
        i = rng.integers(0, len(w), len(w))  # the rows, resampled with replacement
        boots.append(hit[i].sum() / w[i].sum())
    lo, hi = np.percentile(boots, [2.5, 97.5]) if n_boot else (np.nan, np.nan)
    return hit.sum() / w.sum(), lo, hi


def check():
    rng = np.random.default_rng(0)
    n, eps = 200_000, 0.01
    champion_declines = rng.random(n) < 0.10  # a toy champion; its declines never get a label
    is_fraud = rng.random(n) < np.where(champion_declines, 0.30, 0.01)
    declined = rng.random(n) < np.where(is_fraud, 0.5, 0.01)  # a toy challenger
    true_recall = declined[is_fraud].mean()  # the toy is fully labelled, so the truth is known
    draws = np.random.default_rng(1)  # the reveals' own stream, whatever ipw_recall draws for its bootstrap

    def reveal():  # approve a random 1% of the champion's declines and log the propensity
        explored = champion_declines & (draws.random(n) < eps)
        return ~champion_declines | explored, np.where(champion_declines, eps, 1.0)

    labeled, propensity = reveal()
    recall, lo, hi = ipw_recall(declined, is_fraud, labeled, propensity, 200, np.random.default_rng(2))
    m = labeled & is_fraud
    assert np.isclose(recall, np.average(declined[m], weights=1 / propensity[m])), "differs from numpy.average"
    sk = recall_score(is_fraud[labeled].astype(int), declined[labeled].astype(int), sample_weight=1 / propensity[labeled])
    assert np.isclose(recall, sk), "differs from recall_score with the same weights"
    assert lo < recall < hi, "the 95% interval should hold the point estimate"
    estimates = np.array([ipw_recall(declined, is_fraud, *reveal(), 10, np.random.default_rng(3))[0] for _ in range(200)])
    se = estimates.std(ddof=1) / np.sqrt(len(estimates))
    assert abs(estimates.mean() - true_recall) < 2 * se, "the mean over 200 reveals should equal the true recall"
    print("check: PASS")


if __name__ == "__main__":
    check()
