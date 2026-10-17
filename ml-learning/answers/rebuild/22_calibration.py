"""Rebuild 22: the prior correction, a quantile reliability table and the Brier score.

Write correct_for_downsampling() from memory and the other two bodies from their docstrings,
then run: python rebuild/22_calibration.py
check() compares them with scikit-learn, never with this lab's results.
"""
import numpy as np
from sklearn.calibration import calibration_curve
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss


def correct_for_downsampling(p_sample, keep_rate):
    """Map probabilities from a model trained on every positive and keep_rate of the negatives
    back to the class balance of the untouched data. Returns an array shaped like p_sample."""
    p = np.asarray(p_sample, dtype=float)
    return keep_rate * p / (keep_rate * p - p + 1)


def reliability_table(y, p, n_bins=10):
    """Quantile bins: the edges are the 0th, 10th, ..., 100th percentiles of p, and a score sits in
    the first bin whose upper inner edge is at or above it. Returns (mean predicted, observed
    positive rate, count) per non-empty bin, in bin order."""
    y, p = np.asarray(y, dtype=float), np.asarray(p, dtype=float)
    edges = np.percentile(p, np.linspace(0, 100, n_bins + 1))
    ids = np.searchsorted(edges[1:-1], p)
    count = np.bincount(ids, minlength=n_bins)
    keep = count > 0
    mean_p = np.bincount(ids, weights=p, minlength=n_bins)[keep] / count[keep]
    observed = np.bincount(ids, weights=y, minlength=n_bins)[keep] / count[keep]
    return mean_p, observed, count[keep]


def brier(y, p):
    """Brier score: the mean squared gap between the predicted probability and the 0/1 label."""
    return float(np.mean((np.asarray(p, dtype=float) - np.asarray(y, dtype=float)) ** 2))


def check():
    rng = np.random.default_rng(0)
    y = (rng.random(20_000) < 0.05).astype(int)
    p = np.clip(rng.beta(1, 15, 20_000) + 0.4 * y * rng.random(20_000), 0, 1)
    assert abs(brier(y, p) - brier_score_loss(y, p)) < 1e-15, "brier differs from brier_score_loss"
    mean_p, observed, count = reliability_table(y, p, n_bins=10)
    sk_observed, sk_mean_p = calibration_curve(y, p, n_bins=10, strategy="quantile")
    assert np.allclose(mean_p, sk_mean_p, rtol=0, atol=1e-12), "mean predicted differs from calibration_curve"
    assert np.allclose(observed, sk_observed, rtol=0, atol=1e-12), "observed rate differs from calibration_curve"
    assert count.sum() == len(y), "every row must land in one bin"
    # Toy: a true logistic model, every positive kept and 10% of the negatives, scored on all rows.
    x = rng.normal(size=(200_000, 1))
    y = (rng.random(200_000) < 1 / (1 + np.exp(-(-4.0 + 1.5 * x[:, 0])))).astype(int)
    kept = (y == 1) | (rng.random(len(y)) < 0.10)
    model = LogisticRegression().fit(x[kept], y[kept])
    corrected = correct_for_downsampling(model.predict_proba(x)[:, 1], 0.10)
    assert corrected.shape == y.shape, "one corrected probability per row"
    assert abs(corrected.mean() / y.mean() - 1) < 0.05, "the corrected mean should return to the base rate"
    print("check: PASS")


if __name__ == "__main__":
    check()
