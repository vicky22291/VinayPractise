"""Rebuild 08: permutation importance by hand.

Write the body of permutation_importance_auc() from memory, then run
    python rebuild/08_permutation_importance.py
check() compares your ranks with sklearn.inspection.permutation_importance on a toy model.
"""
import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score


def permutation_importance_auc(model, X, y, n_repeats=5, seed=0):
    """How much validation AUC drops when one column is shuffled, for every column of X.

    Score the untouched X once. For each column, n_repeats times: copy X, shuffle
    that one column, score again, keep the drop. Return a pandas Series:
    column name -> mean drop. Use rng = np.random.default_rng(seed).
    """
    rng = np.random.default_rng(seed)
    base = roc_auc_score(y, model.predict_proba(X)[:, 1])
    drops = {}
    for col in X.columns:
        losses = []
        for _ in range(n_repeats):
            shuffled = X.copy()
            shuffled[col] = X[col].values[rng.permutation(len(X))]
            losses.append(base - roc_auc_score(y, model.predict_proba(shuffled)[:, 1]))
        drops[col] = float(np.mean(losses))
    return pd.Series(drops)


def check():
    rng = np.random.default_rng(0)
    X = pd.DataFrame(rng.normal(size=(1500, 4)), columns=["a", "b", "c", "d"])
    y = (X @ np.array([3.0, 1.5, 0.6, 0.0]) + rng.normal(size=1500) > 0).astype(int)  # d carries nothing
    model = LogisticRegression().fit(X[:1000], y[:1000])
    X_va, y_va = X[1000:], y[1000:]
    mine = permutation_importance_auc(model, X_va, y_va, n_repeats=5, seed=0)
    lib = permutation_importance(model, X_va, y_va, scoring="roc_auc", n_repeats=5, random_state=0)
    lib = pd.Series(lib.importances_mean, index=X.columns)
    print(pd.DataFrame({"yours": mine, "sklearn": lib}).round(4).to_string())
    assert list(mine.index) == list(X.columns), "return one value per column, in column order"
    assert (mine.rank(ascending=False) == lib.rank(ascending=False)).all(), "ranks differ from sklearn"
    assert np.allclose(mine, lib, atol=0.06), "mean drops are far from sklearn's"
    print("check: PASS")


if __name__ == "__main__":
    check()
