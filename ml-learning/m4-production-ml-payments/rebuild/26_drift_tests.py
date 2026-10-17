"""Rebuild 26: the KS statistic, a domain classifier's AUC and the population stability index.

Write the three bodies from memory, then run: python rebuild/26_drift_tests.py
check() compares them with scipy, numpy and a known normal-distribution AUC, never with this lab's results.
"""
import numpy as np
from lightgbm import LGBMClassifier
from scipy.stats import ks_2samp, norm
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict


def ks_statistic(a, b):
    """Two-sample Kolmogorov-Smirnov statistic: the largest gap between the two empirical CDFs
    (cumulative distribution functions). Sort both samples, evaluate each ECDF at every pooled
    value with np.searchsorted(side="right"), and return the largest absolute difference."""
    raise NotImplementedError("write this from memory")


def domain_classifier_auc(old, new, seed=0):
    """AUC of a classifier that tells new rows (label 1) from old rows (label 0): LightGBM with
    100 trees, scored on out-of-fold probabilities from cross_val_predict over 5 stratified,
    shuffled folds. 0.5 means the two samples look alike; 1.0 means they never overlap."""
    raise NotImplementedError("write this from memory")


def psi(expected, actual, bins=10):
    """Population stability index of actual against expected (the reference sample). Bin edges:
    the reference's quantiles at 0.1, 0.2, ..., 0.9 (np.quantile), duplicates dropped; a value
    equal to an edge goes to the bin above it, and the outer bins run to minus and plus infinity.
    With e and a the two samples' shares per bin, each floored at 0.0001: sum((a - e) * ln(a / e))."""
    raise NotImplementedError("write this from memory")


def check():
    def psi_by_histogram(expected, actual):  # the same PSI by hand: np.histogram, infinite outer edges
        edges = np.r_[-np.inf, np.unique(np.quantile(expected, np.arange(1, 10) / 10)), np.inf]
        e = np.maximum(np.histogram(expected, edges)[0] / len(expected), 1e-4)
        a = np.maximum(np.histogram(actual, edges)[0] / len(actual), 1e-4)
        return float(np.sum((a - e) * np.log(a / e)))

    rng = np.random.default_rng(0)
    samples = [(rng.normal(size=50), rng.normal(0.3, size=70)),               # small, continuous
               (rng.normal(size=20_000), rng.normal(0.02, size=30_000)),      # large, a tiny shift
               (rng.integers(0, 6, 5_000), rng.integers(0, 7, 4_000))]        # discrete, many ties
    for a, b in samples:
        assert abs(ks_statistic(a, b) - ks_2samp(a, b).statistic) < 1e-12, "ks_statistic differs from ks_2samp"
        assert abs(psi(a, b) - psi_by_histogram(a, b)) < 1e-12, "psi differs from the np.histogram computation"
    same = rng.normal(size=20_000)
    assert psi(same[:10_000], same[10_000:]) < 0.01, "two halves of one sample should have a PSI near 0"
    assert psi(rng.integers(0, 3, 2_000), rng.integers(5, 8, 2_000)) > 1, "disjoint samples need a large PSI"
    old = rng.normal(size=(4_000, 2))
    alike, shifted = rng.normal(size=(4_000, 2)), rng.normal(size=(4_000, 2)) + [1.0, 0.0]
    assert abs(domain_classifier_auc(old, alike) - 0.5) < 0.03, "alike samples should give an AUC near 0.5"
    best = norm.cdf(1 / np.sqrt(2))  # the best possible AUC for a 1-sd mean shift in one normal feature
    assert abs(domain_classifier_auc(old, shifted) - best) < 0.04, "a 1-sd shift should give an AUC near its optimum"
    print("check: PASS")


if __name__ == "__main__":
    check()
