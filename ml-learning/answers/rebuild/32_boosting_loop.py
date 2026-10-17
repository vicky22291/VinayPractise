"""Rebuild 32: the gradient boosting loop, from memory.

Write the body of boost(), then run: python rebuild/32_boosting_loop.py
check() compares with scikit-learn on synthetic data, never with the lab's results.
"""
import numpy as np
from scipy.special import expit  # the sigmoid
from sklearn.datasets import make_classification
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import log_loss, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeRegressor


def boost(X, y, X_new, n_trees=50, lr=0.1):
    """Gradient boosting on log-loss for a 0/1 target y, trained on (X, y), with learning rate lr.

    Every tree is a DecisionTreeRegressor(max_depth=3, random_state=0). Scores are log-odds.
    Returns (F0, history, F_new): F0 is the start score of every row, history is a list of
    the training scores after each of the n_trees trees, and F_new holds the scores of X_new
    after the last tree.
    """
    p = y.mean()
    F0 = np.log(p / (1 - p))
    F, F_new, history = np.full(len(y), F0), np.full(len(X_new), F0), []
    for _ in range(n_trees):
        tree = DecisionTreeRegressor(max_depth=3, random_state=0).fit(X, y - expit(F))
        F = F + lr * tree.predict(X)
        F_new = F_new + lr * tree.predict(X_new)
        history.append(F)
    return F0, history, F_new


def check():
    X, y = make_classification(n_samples=4000, n_features=10, n_informative=3, n_redundant=0, n_clusters_per_class=1,
                               weights=[0.75], class_sep=2.0, random_state=0)  # synthetic data, about 25% positive
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.3, stratify=y, random_state=0)
    F0, history, F_te = boost(X_tr, y_tr, X_te, n_trees=50, lr=0.1)
    p = y_tr.mean()
    assert abs(F0 - np.log(p / (1 - p))) < 1e-12, "F0 is not the log-odds of the training base rate"
    step = {lr: boost(X_tr, y_tr, X_tr, n_trees=1, lr=lr)[1][-1] - F0 for lr in (0.1, 1.0)}
    assert np.abs(step[1.0] - 10 * step[0.1]).max() < 1e-9, \
        "lr does not scale the step: one tree at lr 1.0 should move every score 10 times as far as at lr 0.1"
    _, history_tr, F_tr = boost(X_tr, y_tr, X_tr, n_trees=50, lr=0.1)
    assert np.abs(F_tr - history_tr[-1]).max() < 1e-9, "with X_new = X, F_new differs from the last training scores"
    losses = [log_loss(y_tr, expit(F)) for F in [np.full(len(y_tr), F0)] + history[:20]]
    assert all(b <= a + 1e-12 for a, b in zip(losses, losses[1:])), "training log-loss rose in the first 20 trees"
    ref = GradientBoostingClassifier(max_depth=3, learning_rate=0.1, n_estimators=50, random_state=0).fit(X_tr, y_tr)
    gap = abs(roc_auc_score(y_te, F_te) - roc_auc_score(y_te, ref.decision_function(X_te)))
    assert gap < 0.01, f"test AUC is {gap:.4f} away from sklearn GradientBoostingClassifier"
    print("check: PASS")


if __name__ == "__main__":
    check()
