"""Rebuild for lab 03: AUC two ways, written from memory.

Write the two bodies, then run: python rebuild/03_auc.py
check() compares both with scikit-learn's roc_auc_score on scores with many ties.
"""
import numpy as np
from scipy.stats import rankdata
from sklearn.metrics import roc_auc_score


def auc_pairwise(y, s):
    """The chance that a random positive scores above a random negative; a tie counts 0.5.

    y holds 0/1 labels and s the scores, as 1-D arrays of the same length.
    """
    raise NotImplementedError("write this from memory")


def auc_rank(y, s):
    """The same number from the Mann-Whitney rank formula.

    Rank all scores together (1 = lowest, tied scores share their average rank),
    then turn the positives' rank sum into a probability.
    """
    raise NotImplementedError("write this from memory")


def check():
    """Both functions must match scikit-learn to 1e-12 on 2,000 scores rounded to force ties."""
    rng = np.random.default_rng(0)
    y = rng.integers(0, 2, size=2_000)
    s = np.round(rng.normal(size=2_000) + y, 1)  # rounding to 0.1 makes many tied scores
    assert len(np.unique(s)) < len(s) / 4, "the check needs tied scores"
    want = roc_auc_score(y, s)
    for fn in (auc_pairwise, auc_rank):
        got = fn(y, s)
        assert abs(got - want) < 1e-12, f"{fn.__name__} gave {got}, scikit-learn gives {want}"
    print("check: PASS")


if __name__ == "__main__":
    check()
