"""31. Random forest by hand. Grow trees from a Gini split search, bag them, and compare with one deep tree.

Starter (level S): download(), load_data() and report() are given. The lab file says what you write first.
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


args = labkit.start(lab=31, device="cpu")
if args.mode == "download":
    download()
elif args.mode == "smoke":  # smoke checks the plumbing only: one scikit-learn tree stands in for your forest
    from sklearn.tree import DecisionTreeClassifier
    X_tr, y_tr, X_va, y_va = load_data(args.seed, np.random.default_rng(args.seed), smoke=True)
    tree = DecisionTreeClassifier(min_samples_leaf=5, random_state=args.seed).fit(X_tr, y_tr)
    curve = [tree.score(X_va, y_va)] * 10
    report("baseline", curve, oob_error=1 - curve[-1])
    report("change", curve, oob_error=1 - curve[-1])
    report("break", curve, train_acc=tree.score(X_tr, y_tr), tree_size=(tree.get_n_leaves(), tree.get_depth()))
else:
    raise NotImplementedError("write the harness: see the lab file")
