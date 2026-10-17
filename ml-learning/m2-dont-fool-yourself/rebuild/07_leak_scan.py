"""Rebuild 07: a single-column leak scan, written from memory.

Write the three bodies, then run `python rebuild/07_leak_scan.py` from the module folder.
check() compares with values from scikit-learn's cross_val_score on a toy frame, never with the lab's results.
"""
import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.tree import DecisionTreeClassifier


def as_numeric(col):
    """col as numbers a tree can split.

    Non-numeric columns (test with pd.api.types.is_numeric_dtype, never dtype == object)
    become their category codes. Missing values become -999, so missingness stays visible.
    """
    raise NotImplementedError("write this from memory")


def leak_scan(df, target, threshold=0.9, seed=0):
    """Score every column alone, to find the ones that already know the answer.

    For each column except target: the mean 5-fold ROC AUC of a depth-3 decision tree
    trained on as_numeric(column) only, with folds StratifiedKFold(5, shuffle=True,
    random_state=seed). Return a DataFrame indexed by column name with 'auc' and
    'flagged' (auc >= threshold), sorted by auc, highest first.
    """
    raise NotImplementedError("write this from memory")


def score_without(df, target, model, drop, seed=0):
    """Mean 5-fold CV accuracy of model on every column except target and the drop list.

    Folds: StratifiedKFold(5, shuffle=True, random_state=seed), the same folds as leak_scan.
    """
    raise NotImplementedError("write this from memory")


def check():
    """A toy frame with a planted 'boat' column, against values scikit-learn's cross_val_score gives on it."""
    assert as_numeric(pd.Series(["b", None, "a"])).tolist() == [1, -999, 0], "codes for text, -999 for missing"
    assert as_numeric(pd.Series(["b", None, "a"], dtype="category")).tolist() == [1, -999, 0], "category columns too"
    assert as_numeric(pd.Series([2.5, np.nan])).tolist() == [2.5, -999], "numbers stay, -999 for missing"
    i, y = np.arange(40), np.tile([0, 1], 20)
    age = (i * 7 % 47 + 1 + 12 * (1 - y)).astype(float)
    age[[2, 9, 21, 30]] = np.nan  # a few unknown ages
    df = pd.DataFrame({"boat": np.where(y == 1, np.resize(["4", "7", "C"], 40), np.resize(["11", "13", "15"], 40)),
                       "age": age, "fare": (i * 13 % 29 + 5 + 9 * y) * 1.5,
                       "sex": np.where((y == 1) ^ (i % 5 == 0), "female", "male"), "embarked": "S", "survived": y})
    scan = leak_scan(df, "survived")
    # boat is planted: its codes split the two classes, so 1. embarked is constant, so a coin flip, 0.5.
    # The other values were computed once with scikit-learn 1.9.1's cross_val_score, using the docstrings' folds.
    for c, want in {"boat": 1.0, "age": 0.5625, "fare": 0.63125, "sex": 0.8, "embarked": 0.5}.items():
        assert np.isclose(scan.loc[c, "auc"], want), f"{c}: leak_scan says {scan.loc[c, 'auc']}, scikit-learn {want}"
    assert list(scan.columns) == ["auc", "flagged"] and "survived" not in scan.index, "auc and flagged, target left out"
    assert scan["auc"].is_monotonic_decreasing and scan.index[0] == "boat", "sorted by auc, highest first"
    assert scan["flagged"].sum() == 1 and scan.loc["boat", "flagged"], "the planted column is flagged alone"
    drop = ["boat", "sex", "embarked"]
    guess = score_without(df, "survived", DummyClassifier(strategy="most_frequent"), drop)
    assert np.isclose(guess, 0.5), f"score_without says {guess}: on balanced folds a constant guess scores one half"
    tree = score_without(df, "survived", DecisionTreeClassifier(max_depth=2, random_state=0), drop)
    assert np.isclose(tree, 0.6), f"score_without says {tree}, scikit-learn 0.6"
    print("check: PASS")


if __name__ == "__main__":
    check()
