"""Rebuild 15: a paired regression gate (flips each way and an exact sign test), from memory.

Write both bodies, then run from the module folder: python rebuild/15_paired_gate.py
check() compares with scikit-learn's confusion matrix and scipy.stats.binomtest, never with the lab's results.
"""
import math

import numpy as np
from scipy.stats import binomtest
from sklearn.metrics import confusion_matrix


def paired_flips(y, pred_a, pred_b):
    """y, pred_a and pred_b hold one label per item, in the same item order.

    Return (n_ab, n_ba): items right under a and wrong under b, then items wrong under a and
    right under b. Items both get right, or both get wrong, are not counted."""
    raise NotImplementedError("write this from memory")


def exact_sign_test(n_ab, n_ba):
    """Two-sided exact sign test on the discordant items, written with math.comb.

    With no real difference, each discordant item is a fair coin: X ~ Binomial(n, 1/2), n = n_ab + n_ba.
    Return p = min(1, 2 * P(X <= min(n_ab, n_ba))). With n = 0 there is no evidence, so p = 1."""
    raise NotImplementedError("write this from memory")


def check():
    rng = np.random.default_rng(15)
    labels = np.array(["card_arrival", "card_linking", "top_up_failed", "pin_blocked"])
    for _ in range(50):
        y = rng.choice(labels, 40)
        pred_a = np.where(rng.random(40) < 0.7, y, rng.choice(labels, 40))
        pred_b = np.where(rng.random(40) < 0.6, y, rng.choice(labels, 40))
        cm = confusion_matrix(pred_a == y, pred_b == y, labels=[True, False])  # rows: a right, columns: b right
        assert tuple(paired_flips(list(y), list(pred_a), list(pred_b))) == (cm[0, 1], cm[1, 0]), "paired_flips"
    pairs = [(i, j) for i in range(31) for j in range(31)] + [(3, 120), (60, 75), (450, 500)]
    for n_ab, n_ba in pairs:
        n = n_ab + n_ba
        want = 1.0 if n == 0 else binomtest(n_ab, n, 0.5).pvalue
        got = exact_sign_test(n_ab, n_ba)
        assert abs(got - want) < 1e-12, f"exact_sign_test({n_ab}, {n_ba}) = {got}, binomtest says {want}"
    print("check: PASS")


if __name__ == "__main__":
    check()
