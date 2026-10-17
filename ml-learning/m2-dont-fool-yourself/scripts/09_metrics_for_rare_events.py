"""09. Accuracy lies on rare events: PR-AUC, cost thresholds and their noise. Scores one fraud model with accuracy, ROC-AUC, PR-AUC and a 5:1 cost.

Modes: --download, --smoke, --baseline (P1), --change (P2), --break (P3), --check.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "labkit.py").exists())))
import labkit  # before numpy: it sets cache defaults
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, average_precision_score, confusion_matrix, confusion_matrix_at_thresholds,
                             precision_recall_curve, roc_auc_score)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

PARQUET = "https://data.openml.org/datasets/0000/1597/dataset_1597.pq"  # fallback, 73,231,184 bytes
FEATURES = [f"V{i}" for i in range(1, 29)] + ["Amount"]  # OpenML marks Time as the row id and drops it


def load_data():
    """X (V1 to V28 and Amount), y (1 = fraud) for all 284,807 payments, and where they came from."""
    try:
        df, source = labkit.openml(1597), labkit.DATA / "openml"
    except Exception as e:  # the OpenML API is down: read the parquet copy of the same table
        print(f"OpenML failed ({type(e).__name__}), using the parquet fallback", flush=True)
        source = labkit.fetch(PARQUET, labkit.DATA / "creditcard" / "dataset_1597.pq", size=73_231_184)
        df = pd.read_parquet(source)
    y = df["Class"].astype(str).astype(float).astype(int).to_numpy()
    return df[FEATURES].to_numpy(float), y, source


def pr_curve(y, s):
    """thr, tp, fp per distinct score, highest first: declining every s >= thr[k] catches tp[k] frauds
    and declines fp[k] good payments. Tied scores are declined together: keep the last row of each tie."""
    order = np.argsort(-s, kind="stable")
    s, y = s[order], y[order]
    last = np.r_[s[1:] != s[:-1], True]  # the last row of each tied score
    return s[last], np.cumsum(y)[last], np.cumsum(1 - y)[last]


# --- CONCEPT start ---
def average_precision(y, s):
    """PR-AUC as average precision: the sum over thresholds of (recall step) x precision.

    Use pr_curve(y, s): precision = tp / (tp + fp), recall = tp / (all frauds), and recall is 0
    before the first threshold. Not the trapezoid rule. --check compares it with scikit-learn.
    """
    raise NotImplementedError("TODO(human)")

def cheapest_threshold(y, s, cost_fn=5, cost_fp=1):
    """The threshold t with the lowest cost_fn * FN + cost_fp * FP, declining every s >= t.

    Use pr_curve(y, s): its rows are the candidates, every distinct score as t. FN = frauds not declined,
    FP = good payments declined. On a tie, return the highest t. Returns (t, cost).
    """
    raise NotImplementedError("TODO(human)")


# --- CONCEPT end ---


def at_threshold(y, s, t, cost_fn=5, cost_fp=1):
    """Recall, precision and cost when every payment scoring at least t is declined."""
    tn, fp, fn, tp = confusion_matrix(y, (s >= t).astype(int), labels=[0, 1]).ravel()
    return tp / (tp + fn), tp / max(tp + fp, 1), cost_fn * fn + cost_fp * fp


def cheapest_by_brute_force(y, s, cost_fn=5, cost_fp=1):
    """cheapest_threshold the slow way: price every distinct score with scikit-learn's confusion_matrix."""
    ts = np.unique(s)[::-1]  # highest first, so a tie goes to the highest t
    costs = [at_threshold(y, s, t, cost_fn, cost_fp)[2] for t in ts]
    k = int(np.argmin(costs))
    return ts[k], costs[k]


def check():
    """--check: the two TODO functions against scikit-learn on 20 rows with tied scores."""
    y = np.array([0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0])
    s = np.array([.9, .9, .8, .7, .7, .7, .6, .5, .5, .4, .4, .3, .3, .3, .2, .2, .1, .1, .1, .1])
    ap, want = average_precision(y, s), average_precision_score(y, s)
    assert abs(ap - want) < 1e-12, f"average_precision gave {ap}, scikit-learn {want}"
    for cost_fn, cost_fp in ((5, 1), (1, 1), (4, 1), (10, 2)):  # 4:1 has a tie at the lowest cost
        got, want = cheapest_threshold(y, s, cost_fn, cost_fp), cheapest_by_brute_force(y, s, cost_fn, cost_fp)
        assert tuple(got) == tuple(want), f"cheapest_threshold at {cost_fn}:{cost_fp} gave {got}, brute force {want}"
    print("check: PASS")


def show(step, **values):
    """One RESULT line per value: costs in false declines, thresholds as probabilities, the rest as fractions."""
    for name, value in values.items():
        unit = "false_declines" if "cost" in name else "probability" if name == "threshold" else "fraction"
        labkit.result(f"{step}.{name}", value, unit=unit)


def main():
    args = labkit.start(lab=9, device="cpu", extra_modes=("check",))
    if args.mode == "check":
        return check()
    X, y, source = load_data()
    if args.mode == "download":
        return print(f"DATA {source} {len(y)} rows, {X.shape[1]} features", flush=True)
    ap_fn, cheapest_fn, n_boot = average_precision, cheapest_threshold, 500
    if labkit.smoke():  # smoke checks the plumbing only: 5% of rows, 20 resamples, stand-ins for the TODO
        X, _, y, _ = train_test_split(X, y, train_size=0.05, stratify=y, random_state=args.seed)
        ap_fn, cheapest_fn, n_boot = average_precision_score, cheapest_by_brute_force, 20
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, stratify=y, random_state=args.seed)
    model = make_pipeline(StandardScaler(), LogisticRegression(max_iter=5000)).fit(X_tr, y_tr)
    s = model.predict_proba(X_te)[:, 1]  # the fraud score of each test payment
    if args.mode in ("baseline", "smoke"):  # P1: three metrics on the same scores, then threshold 0.5
        roc, ap = roc_auc_score(y_te, s), ap_fn(y_te, s)
        show("baseline", never_fraud_accuracy=accuracy_score(y_te, np.zeros_like(y_te)))
        show("P1", roc_auc=roc, pr_auc=ap, gap=roc - ap)
        rng = np.random.default_rng(args.seed)  # 95% bootstrap interval: resample the test rows with replacement
        draws = (rng.integers(0, len(y_te), len(y_te)) for _ in range(n_boot))
        boots = [[roc_auc_score(y_te[i], s[i]), ap_fn(y_te[i], s[i])] for i in draws if y_te[i].any()]
        (roc_lo, ap_lo), (roc_hi, ap_hi) = np.percentile(boots, [2.5, 97.5], axis=0)
        show("baseline", roc_auc_lo=roc_lo, roc_auc_hi=roc_hi, pr_auc_lo=ap_lo, pr_auc_hi=ap_hi)
        recall, precision, cost = at_threshold(y_te, s, 0.5)
        p, r, _ = precision_recall_curve(y_te, s)
        show("baseline", recall=recall, precision=precision, cost=cost,
             recall_at_95_precision=r[:-1][p[:-1] >= 0.95].max(initial=0.0))
    if args.mode in ("change", "smoke"):  # P2: the cheapest threshold when a missed fraud costs 5 false declines
        t, cost = cheapest_fn(y_te, s, cost_fn=5, cost_fp=1)
        recall, precision, _ = at_threshold(y_te, s, t)
        show("change", threshold=t)
        show("P2", recall=recall)
        show("change", precision=precision, cost=cost)
    if args.mode in ("break", "smoke"):  # P3: the max-accuracy threshold, priced at 5:1
        tn, _, _, tp, thr = confusion_matrix_at_thresholds(y_te, s)  # one row per distinct score, highest first
        t = thr[int(np.argmax(tp + tn))]  # the most correct; on a tie, argmax keeps the highest t
        recall, precision, cost = at_threshold(y_te, s, t)
        _, cheapest_cost = cheapest_fn(y_te, s, cost_fn=5, cost_fp=1)
        show("break", threshold=t, accuracy=accuracy_score(y_te, (s >= t).astype(int)))
        show("P3", recall=recall)
        show("break", precision=precision, cost=cost, extra_cost=cost - cheapest_cost)


if __name__ == "__main__":
    main()
