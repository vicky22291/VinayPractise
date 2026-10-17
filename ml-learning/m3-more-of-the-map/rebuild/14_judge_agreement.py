"""Rebuild 14: judge agreement, Cohen's kappa and the flip rate under a swap, from memory.

Write the three bodies, then run from the module folder: python rebuild/14_judge_agreement.py
check() compares with scikit-learn's confusion_matrix, accuracy_score and cohen_kappa_score, never with the lab's results.
"""
import numpy as np
from sklearn.metrics import accuracy_score, cohen_kappa_score, confusion_matrix


def confusion(human, judge):
    """human and judge hold one 'A' or 'B' verdict per item, in the same item order.

    Return the 2 x 2 counts as a numpy array: rows are the human verdict (A, B), columns the judge verdict (A, B)."""
    raise NotImplementedError("write this from memory")


def agreement_and_kappa(human, judge):
    """Return (p_o, kappa), both read off the 2 x 2 table of confusion(human, judge) divided by n.

    p_o   = the share of items on the diagonal: observed agreement
    p_e   = (row A share) * (column A share) + (row B share) * (column B share): chance agreement
    kappa = (p_o - p_e) / (1 - p_e)"""
    raise NotImplementedError("write this from memory")


def flip_rate(verdicts_ab, verdicts_ba):
    """verdicts_ab holds one 'A' or 'B' per pair, judged with answer A shown first. verdicts_ba holds the
    letters for the same pairs judged with the two answers swapped, so there 'A' names the original answer B.

    Return the share of pairs whose winning answer changes when only the order changed."""
    raise NotImplementedError("write this from memory")


def check():
    rng = np.random.default_rng(14)
    letters = np.array(["A", "B"])
    for _ in range(300):
        n = int(rng.integers(5, 120))
        share_a = rng.uniform(0.1, 0.9)
        human = rng.choice(letters, n, p=[share_a, 1 - share_a])
        judge = np.where(rng.random(n) < rng.uniform(0, 1), human, rng.choice(letters, n))
        if len(set(human) | set(judge)) < 2:
            continue  # kappa is undefined when both raters give one and the same label
        table = np.asarray(confusion(list(human), list(judge)))
        assert (table == confusion_matrix(human, judge, labels=letters)).all(), "confusion"
        p_o, kappa = agreement_and_kappa(list(human), list(judge))
        assert abs(p_o - accuracy_score(human, judge)) < 1e-12, "agreement"
        want = cohen_kappa_score(human, judge, labels=letters)
        assert abs(kappa - want) < 1e-12, f"kappa {kappa}, cohen_kappa_score says {want}"
    human, judge = ["A"] * 80 + ["B"] * 20, ["A"] * 100  # 80% 'A' labels, and a judge that always says 'A'
    p_o, kappa = agreement_and_kappa(human, judge)
    assert abs(p_o - 0.8) < 1e-12 and abs(kappa) < 1e-12, "an always-'A' judge: raw agreement 0.8, kappa 0"
    assert abs(cohen_kappa_score(human, judge)) < 1e-12
    for _ in range(100):
        win_ab = rng.choice(letters, 50)  # the winning answer with A shown first
        win_ba = np.where(rng.random(50) < rng.uniform(0, 1), win_ab, rng.choice(letters, 50))
        shown_ba = np.where(win_ba == "A", "B", "A")  # after the swap, answer A sits in the second slot
        want = 1 - accuracy_score(win_ab, win_ba)
        assert abs(flip_rate(list(win_ab), list(shown_ba)) - want) < 1e-12, "flip_rate"
    print("check: PASS")


if __name__ == "__main__":
    check()
