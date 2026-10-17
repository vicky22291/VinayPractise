"""31. Random forest by hand. Grow trees from a Gini split search, bag them, and compare with one deep tree.

Modes: --download, --smoke, --baseline (P1), --change (P2), --break (P3).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "labkit.py").exists())))
import labkit  # before numpy: it sets cache defaults
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

SAMPLE = "https://s3.amazonaws.com/fast-ai-sample/adult_sample.tgz"  # fastai ADULT_SAMPLE, the fallback
CSV = labkit.DATA / "adult" / "adult_sample" / "adult.csv"
TRAIN_ROWS = 10_000  # training rows kept from the 80% split
PLANS = {  # the forest plan: trees, depth limit, features tried per split, min rows per leaf, bootstrap
    "baseline": dict(trees=100, max_depth=None, features=14, min_leaf=5, bootstrap=True),
    "change": dict(trees=100, max_depth=None, features=4, min_leaf=5, bootstrap=True),
    "break": dict(trees=1, max_depth=None, features=14, min_leaf=1, bootstrap=False),
}


def download():
    """OpenML 1590. If OpenML is down, fastai's 32,561-row ADULT_SAMPLE instead."""
    try:
        print(f"OPENML 1590 {len(labkit.openml(1590))} rows cached in {labkit.DATA / 'openml'}")
    except Exception as e:  # any OpenML failure: fall back to the file copy
        print(f"RETRY OpenML failed ({type(e).__name__}), fetching ADULT_SAMPLE")
        labkit.extract(labkit.fetch(SAMPLE, CSV.parents[1] / "adult_sample.tgz", size=968_212), CSV.parents[1])


def load_data(seed, rng, smoke=False):
    """Adult with categories as integer codes: the stratified 80/20 split, training capped at TRAIN_ROWS."""
    frame = (pd.read_csv(CSV, skipinitialspace=True).rename(columns={"salary": "class"})
             if CSV.exists() else labkit.openml(1590))  # the fallback file is there only if OpenML failed
    y = frame["class"].astype(str).str.contains(">").to_numpy(np.int64)  # 1 = income over 50K
    X = frame.drop(columns="class")
    for col in X.columns:
        if not pd.api.types.is_numeric_dtype(X[col]):
            X[col] = X[col].astype("category").cat.codes  # a missing category becomes code -1
    X = X.fillna(-1).to_numpy(np.float64)
    X_tr, X_va, y_tr, y_va = train_test_split(X, y, test_size=0.2, stratify=y, random_state=seed)
    keep = rng.choice(len(y_tr), size=TRAIN_ROWS, replace=False)
    n_tr, n_va = (2000, 2000) if smoke else (TRAIN_ROWS, len(y_va))
    return X_tr[keep][:n_tr], y_tr[keep][:n_tr], X_va[:n_va], y_va[:n_va]


def report(mode, curve, oob_error=None, train_acc=None, tree_size=None):
    """Print this mode's RESULT lines. curve[k - 1] is validation accuracy with the first k trees."""
    if mode == "break":
        labkit.result("P3.train_minus_valid", 100 * (train_acc - curve[-1]), unit="points")
        labkit.result("break.train_acc", train_acc, unit="fraction")
        labkit.result("break.valid_acc", curve[-1], unit="fraction")
        labkit.result("break.leaves", tree_size[0])
        labkit.result("break.depth", tree_size[1])
        return
    step = "P1" if mode == "baseline" else "P2"
    labkit.result(f"{step}.valid_acc", curve[-1], unit="fraction", trees=len(curve))
    labkit.result(f"{mode}.valid_acc_1_tree", curve[0], unit="fraction")
    labkit.result(f"{mode}.valid_acc_10_trees", curve[9], unit="fraction")
    labkit.result(f"{mode}.valid_error", 1 - curve[-1], unit="fraction")
    labkit.result("baseline.oob_error" if mode == "baseline" else "P2.oob_error", oob_error, unit="fraction")
    acc0, oob0 = labkit.prior("P1.valid_acc"), labkit.prior("baseline.oob_error")
    if mode == "change" and None not in (acc0, oob0):  # against the baseline run with the same seed
        labkit.result("P2.valid_acc_change", 100 * (curve[-1] - acc0), unit="points")
        labkit.result("P2.oob_error_change", 100 * (oob_error - oob0), unit="points")


def best_split(x, y, min_leaf=1):
    """Best cut on one feature: (threshold, weighted Gini), or (None, inf) if no cut is allowed."""
    order = np.argsort(x)
    xs, ys, n = x[order], y[order], len(y)
    cut = np.flatnonzero(xs[1:] != xs[:-1]) + 1  # rows on the left at each cut between two different values
    cut = cut[(cut >= min_leaf) & (n - cut >= min_leaf)]
    if len(cut) == 0:
        return None, np.inf
    pos_left = np.cumsum(ys)[cut - 1]
    p_left, p_right = pos_left / cut, (ys.sum() - pos_left) / (n - cut)
    gini = (cut * 2 * p_left * (1 - p_left) + (n - cut) * 2 * p_right * (1 - p_right)) / n
    i = np.argmin(gini)
    return (xs[cut[i] - 1] + xs[cut[i]]) / 2, gini[i]


def grow(X, y, plan, rng, depth=0):
    """A leaf is its share of positives; a split is (feature, threshold, left subtree, right subtree)."""
    share = y.mean()
    if share in (0.0, 1.0) or len(y) < 2 * plan["min_leaf"] or depth == plan["max_depth"]:
        return share
    best_gini, best = np.inf, None
    for f in rng.choice(X.shape[1], size=plan["features"], replace=False):
        threshold, gini = best_split(X[:, f], y, plan["min_leaf"])
        if gini < best_gini:
            best_gini, best = gini, (f, threshold)
    if best is None:  # no allowed cut on any feature tried here
        return share
    f, threshold = best
    left = X[:, f] <= threshold
    return (f, threshold, grow(X[left], y[left], plan, rng, depth + 1),
            grow(X[~left], y[~left], plan, rng, depth + 1))


def predict(tree, X):
    """Send every row of X down the tree; return the share of positives in the leaf it reaches."""
    if not isinstance(tree, tuple):
        return np.full(len(X), tree)
    f, threshold, left_tree, right_tree = tree
    left, out = X[:, f] <= threshold, np.empty(len(X))
    out[left], out[~left] = predict(left_tree, X[left]), predict(right_tree, X[~left])
    return out


def size(tree):
    """(leaves, depth) of a tree."""
    if not isinstance(tree, tuple):
        return 1, 0
    (leaves_l, depth_l), (leaves_r, depth_r) = size(tree[2]), size(tree[3])
    return leaves_l + leaves_r, 1 + max(depth_l, depth_r)


def forest(X_tr, y_tr, X_va, y_va, plan, rng):
    """Grow the plan's trees. Each votes with its leaf share; the forest averages the votes, cut at 0.5."""
    n = len(y_tr)
    votes, curve, oob_votes, oob_count = np.zeros(len(y_va)), [], np.zeros(n), np.zeros(n)
    for k in range(1, plan["trees"] + 1):
        rows = rng.integers(0, n, size=n) if plan["bootstrap"] else np.arange(n)
        tree = grow(X_tr[rows], y_tr[rows], plan, rng)
        votes += predict(tree, X_va)
        curve.append(np.mean((votes / k > 0.5) == y_va))  # validation accuracy with the first k trees
        out = ~np.isin(np.arange(n), rows)  # out-of-bag rows: this tree's bootstrap never drew them
        oob_votes[out] += predict(tree, X_tr[out])
        oob_count[out] += 1
    seen = oob_count > 0
    oob_error = np.mean((oob_votes[seen] / oob_count[seen] > 0.5) != y_tr[seen]) if seen.any() else None
    return curve, oob_error, tree


args = labkit.start(lab=31, device="cpu")
if args.mode == "download":
    download()
else:
    rng = np.random.default_rng(args.seed)
    X_tr, y_tr, X_va, y_va = load_data(args.seed, rng, smoke=labkit.smoke())
    for mode in ("baseline", "change", "break") if labkit.smoke() else (args.mode,):
        plan = dict(PLANS[mode], trees=min(PLANS[mode]["trees"], 10)) if labkit.smoke() else PLANS[mode]
        curve, oob_error, tree = forest(X_tr, y_tr, X_va, y_va, plan, rng)
        if mode == "break":  # one tree, scored on the rows it was grown on and on validation
            train_acc = np.mean((predict(tree, X_tr) > 0.5) == y_tr)
            report(mode, curve, train_acc=train_acc, tree_size=size(tree))
        else:
            report(mode, curve, oob_error)
