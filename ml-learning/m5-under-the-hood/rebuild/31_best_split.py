"""Rebuild for lab 31: the best Gini split on one feature, written from memory.

Write the body of best_split(), then run, from the module folder:
    python rebuild/31_best_split.py
check() compares your function with scikit-learn's DecisionTreeClassifier(max_depth=1),
never with this lab's results.
"""
import numpy as np
from sklearn.tree import DecisionTreeClassifier


def best_split(x, y, min_leaf=1):
    """Best cut on one feature x for a 0/1 target y, by weighted Gini impurity.

    Sort the rows by x. A cumulative sum of y counts the positives left of every cut.
    Score each cut by the weighted Gini of its two sides, (n_L * G_L + n_R * G_R) / n,
    where a side with a share p of positives has G = 2 p (1 - p). Skip cuts between
    equal x values and cuts that leave fewer than min_leaf rows on a side.
    Return (threshold, weighted_gini), with the threshold at the midpoint of the two
    x values around the best cut, or (None, inf) when no cut is allowed.
    """
    raise NotImplementedError("write this from memory")


def check():
    rng = np.random.default_rng(0)
    for trial in range(40):
        n = int(rng.integers(40, 400))
        if trial % 2:  # many repeated values, so some cuts must be skipped
            x = rng.integers(0, 30, n).astype(np.float64)
        else:  # continuous values, rounded to float32 because scikit-learn casts X to float32
            x = rng.normal(size=n).astype(np.float32).astype(np.float64)
        y = (x + rng.normal(scale=x.std(), size=n) > np.median(x)).astype(np.int64)
        min_leaf = (1, 5)[trial % 4 // 2]
        threshold, gini = best_split(x, y, min_leaf)
        tree = DecisionTreeClassifier(max_depth=1, min_samples_leaf=min_leaf).fit(x[:, None], y).tree_
        left, right = tree.children_left[0], tree.children_right[0]
        n_left, n_right = tree.n_node_samples[left], tree.n_node_samples[right]
        sk_gini = (n_left * tree.impurity[left] + n_right * tree.impurity[right]) / (n_left + n_right)
        assert abs(threshold - tree.threshold[0]) < 1e-6, (trial, threshold, tree.threshold[0])
        assert abs(gini - sk_gini) < 1e-6, (trial, gini, sk_gini)
    print("check: PASS (40 random features, threshold and weighted Gini match scikit-learn to 1e-6)")


if __name__ == "__main__":
    check()
