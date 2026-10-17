"""27 rebuild: the honest core of a fraud training pipeline, written from memory.

Write the body of honest_core(), then run: python rebuild/27_honest_core.py
check() compares with numpy and scikit-learn on a toy, never with this lab's results.
"""
import numpy as np
from sklearn.datasets import make_classification
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, precision_recall_curve
from sklearn.preprocessing import StandardScaler


def honest_core(X, y, keep_legit=0.10, val_share=0.25, seed=0):
    """Train a fraud model and pick its threshold without leaking rows or moving the scale.

    X, y are numpy arrays with the rows in time order (y: 1 = fraud).
    1. Split by time first: the first (1 - val_share) of the rows train, the rest validate.
    2. Fit a StandardScaler on the training rows only.
    3. Keep every training fraud plus a random keep_legit share of the training legit rows
       (numpy.random.default_rng(seed), without replacement). Never resample the validation rows.
    4. Fit LogisticRegression(max_iter=1000) on the scaled, downsampled training rows.
    5. Score the validation rows, then undo the downsampling with the odds correction
       p' = b p / (b p - p + 1), where b = keep_legit.
    6. Choose the threshold with the best F1 on the corrected validation scores (decline p' >= t).
    Returns (scaler, model, threshold, corrected validation scores).
    """
    raise NotImplementedError("write this from memory")


def check():
    """honest_core() on a 40,000-row toy with 5% positives, against numpy and scikit-learn."""
    X, y = make_classification(n_samples=40_000, n_features=8, n_informative=5, weights=[0.95],
                               flip_y=0.0, random_state=0)
    scaler, model, threshold, p = honest_core(X, y, keep_legit=0.10, val_share=0.25, seed=0)
    cut = int(len(y) * 0.75)
    y_val = y[cut:]
    assert np.allclose(scaler.mean_, X[:cut].mean(axis=0)), "the scaler saw rows outside the training slice"
    assert len(p) == len(y_val), "score every validation row, and only those"
    base = y_val.mean()
    assert abs(p.mean() / base - 1) < 0.10, f"corrected mean {p.mean():.4f} is not within 10% of {base:.4f}"
    best = f1_score(y_val, p >= threshold)
    grid = np.quantile(p, np.linspace(0.5, 0.999, 200))
    assert all(best >= f1_score(y_val, p >= t) - 1e-12 for t in grid), "the threshold is not the best F1"
    print("check: PASS")


if __name__ == "__main__":
    check()
