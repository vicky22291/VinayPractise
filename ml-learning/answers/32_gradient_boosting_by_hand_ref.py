"""32. Gradient boosting by hand. A boosting loop of depth-3 trees next to LightGBM, at learning rates 0.1 and 1.0.

Modes: --download, --smoke, --baseline (P1), --change (P2), --break (P3).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "labkit.py").exists())))
import labkit  # before numpy: it sets cache defaults
import lightgbm as lgb
import numpy as np
import pandas as pd
from scipy.special import expit  # the sigmoid
from sklearn.metrics import log_loss, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeRegressor

PARQUET = "https://data.openml.org/datasets/0000/1590/dataset_1590.pq"  # fallback 1
UCI = "https://archive.ics.uci.edu/static/public/2/adult.zip"  # fallback 2
TREES, CHECKPOINTS, TIMED = 300, (10, 100, 300), (300, 1000)
CONTRACT = {  # the RESULT contract: every value this lab records, by mode, with its unit
    "baseline": {"P1.auc_gap": "auc", "baseline.loop_auc": "auc", "baseline.lgbm_auc": "auc",
                 "baseline.loop_logloss_10": "logloss", "baseline.loop_logloss_100": "logloss",
                 "baseline.loop_logloss_300": "logloss", "baseline.lgbm_logloss": "logloss",
                 "baseline.lgbm_best_iter": "trees", "baseline.lgbm_depth": "levels",
                 "baseline.lgbm_us_300": "us", "baseline.lgbm_us_1000": "us"},
    "change": {"P2.loop_logloss_300": "logloss", "P2.loop_logloss_300_delta": "logloss",
               "change.loop_logloss_10": "logloss", "change.loop_logloss_100": "logloss", "change.loop_auc": "auc"},
    "break": {"P3.lgbm_logloss_300": "logloss", "break.lgbm_auc_300": "auc",
              "break.lgbm_best_iter": "trees", "break.lgbm_best_logloss": "logloss"}}


def adult():
    """Adult (OpenML 1590) as one DataFrame: OpenML first, then its parquet copy, then UCI."""
    try:
        return labkit.openml(1590)
    except Exception as e:  # any network or OpenML error: try the next source
        print(f"RETRY OpenML failed ({type(e).__name__}), trying the parquet copy", flush=True)
    try:
        return pd.read_parquet(labkit.fetch(PARQUET, labkit.DATA / "adult" / "dataset_1590.pq", size=528_745))
    except Exception as e:
        print(f"RETRY parquet copy failed ({type(e).__name__}), trying UCI", flush=True)
    folder = labkit.extract(labkit.fetch(UCI, labkit.DATA / "adult" / "adult.zip", size=620_237), labkit.DATA / "adult")
    df = pd.concat([pd.read_csv(folder / f, header=None, skiprows=skip, skipinitialspace=True, na_values="?")
                    for f, skip in (("adult.data", 0), ("adult.test", 1))], ignore_index=True)
    return df.rename(columns={14: "class"}).replace({"class": {"<=50K.": "<=50K", ">50K.": ">50K"}})


def load_data(seed, smoke=False):
    """The split of labs 03 and 31: stratified 80/20 (39,073 / 9,769 rows), random_state=seed. Categorical columns
    become integer codes (-1 for missing): one numeric matrix for both models. Smoke keeps 2,000 / 1,000 rows."""
    df = adult()
    y = (df["class"].astype(str) == ">50K").to_numpy(dtype=int)
    X = df.drop(columns="class")
    X = X.apply(lambda c: c if pd.api.types.is_numeric_dtype(c) else c.astype("category").cat.codes)
    X_tr, X_va, y_tr, y_va = train_test_split(X.to_numpy(dtype=float), y, test_size=0.2, stratify=y, random_state=seed)
    if smoke:
        return X_tr[:2000], X_va[:1000], y_tr[:2000], y_va[:1000]
    return X_tr, X_va, y_tr, y_va


def report(mode, values, **timing):
    """Print this mode's RESULT lines in CONTRACT order; timing lines (unit us) get the timing tags."""
    for name, unit in CONTRACT[mode].items():
        if values[name] is None:
            print(f"SKIP {name}: run --baseline with the same seed first", flush=True)
        else:
            labkit.result(name, values[name], unit=unit, **(timing if unit == "us" else {}))


def boost(X, y, n_trees, lr, seed=0):
    """Gradient boosting on log-loss with depth-3 trees. Returns (F0, trees). F0 = log(p / (1 - p)) for the
    training base rate p; each round fits a tree to the residual y - sigmoid(F), the negative gradient of
    log-loss, and adds lr times its prediction to F."""
    p = y.mean()
    F0 = np.log(p / (1 - p))
    F = np.full(len(y), F0)
    trees = []
    for _ in range(n_trees):
        tree = DecisionTreeRegressor(max_depth=3, random_state=seed).fit(X, y - expit(F))
        F += lr * tree.predict(X)
        trees.append(tree)
    return F0, trees


def metrics(y, F):
    """Log-loss of the probabilities sigmoid(F), and AUC of the raw score F (log-odds)."""
    return log_loss(y, expit(F)), roc_auc_score(y, F)


def loop_curve(X_tr, X_va, y_tr, y_va, lr, seed):
    """The loop's validation log-loss at each checkpoint, and its validation AUC after the last tree."""
    F0, trees = boost(X_tr, y_tr, TREES, lr, seed)
    F, losses = np.full(len(X_va), F0), {}
    for k, tree in enumerate(trees, start=1):  # score the validation rows the same way, one tree at a time
        F = F + lr * tree.predict(X_va)
        if k in CHECKPOINTS:
            losses[k], auc = metrics(y_va, F)
    return losses, auc


def lightgbm(X_tr, X_va, y_tr, y_va, lr, rounds, stop, seed):
    """LightGBM at its defaults (31 leaves per tree); early stopping on validation log-loss when stop is set."""
    model = lgb.LGBMClassifier(n_estimators=rounds, learning_rate=lr, random_state=seed, verbose=-1)
    callbacks = [lgb.early_stopping(stop, verbose=False)] if stop else []
    return model.fit(X_tr, y_tr, eval_X=X_va, eval_y=y_va, callbacks=callbacks)


def us_per_request(model, X, trees, n, warmup):
    """Median microseconds for one single-row prediction with the first `trees` trees, on one thread."""
    def one_call(i):
        t0 = labkit.clock()
        model.booster_.predict(X[i:i + 1], num_iteration=trees, num_threads=1)
        return labkit.clock() - t0
    return 1e6 * float(np.median([one_call(i) for i in range(warmup + n)][warmup:]))


args = labkit.start(lab=32, device="cpu")
if args.mode == "download":
    print(f"DATA {labkit.DATA} adult rows={len(adult())}", flush=True)
    sys.exit(0)
X_tr, X_va, y_tr, y_va = data = load_data(args.seed, smoke=labkit.smoke())  # smoke: tiny data, the same code path
n, warmup = (10, 2) if labkit.smoke() else (200, 20)

if args.mode in ("baseline", "smoke"):  # P1: the loop at 0.1 against LightGBM at 0.1 with early stopping 50
    losses, loop_auc = loop_curve(*data, lr=0.1, seed=args.seed)
    gbm = lightgbm(*data, lr=0.1, rounds=1000, stop=50, seed=args.seed)
    gbm_logloss, gbm_auc = metrics(y_va, gbm.predict_proba(X_va, raw_score=True, num_iteration=gbm.best_iteration_))
    nodes = gbm.booster_.trees_to_dataframe()  # node_depth counts the root as 1
    big = lightgbm(*data, lr=0.1, rounds=max(TIMED), stop=None, seed=args.seed)  # for the per-request timing
    base = {"P1.auc_gap": loop_auc - gbm_auc, "baseline.loop_auc": loop_auc, "baseline.lgbm_auc": gbm_auc,
            **{f"baseline.loop_logloss_{k}": v for k, v in losses.items()},
            "baseline.lgbm_logloss": gbm_logloss, "baseline.lgbm_best_iter": gbm.best_iteration_,
            "baseline.lgbm_depth": float((nodes.groupby("tree_index")["node_depth"].max() - 1).mean()),
            **{f"baseline.lgbm_us_{k}": us_per_request(big, X_va, k, n, warmup) for k in TIMED}}
    report("baseline", base, device="cpu", batch=1, warmup=warmup, n=n, stat="median", threads=1)

if args.mode in ("change", "smoke"):  # P2: the same loop at learning rate 1.0
    losses, auc = loop_curve(*data, lr=1.0, seed=args.seed)
    before = base["baseline.loop_logloss_300"] if labkit.smoke() else labkit.prior("baseline.loop_logloss_300")
    delta = None if before is None else losses[300] - before
    report("change", {"P2.loop_logloss_300": losses[300], "P2.loop_logloss_300_delta": delta, "change.loop_auc": auc,
                      "change.loop_logloss_10": losses[10], "change.loop_logloss_100": losses[100]})

if args.mode in ("break", "smoke"):  # P3: LightGBM at 1.0 for 300 trees, no early stopping; then early_stopping(50)
    full = lightgbm(*data, lr=1.0, rounds=TREES, stop=None, seed=args.seed)
    logloss_300, auc_300 = metrics(y_va, full.predict_proba(X_va, raw_score=True, num_iteration=TREES))
    stopped = lightgbm(*data, lr=1.0, rounds=TREES, stop=50, seed=args.seed)
    best_logloss, _ = metrics(y_va, stopped.predict_proba(X_va, raw_score=True, num_iteration=stopped.best_iteration_))
    report("break", {"P3.lgbm_logloss_300": logloss_300, "break.lgbm_auc_300": auc_300,
                     "break.lgbm_best_iter": stopped.best_iteration_, "break.lgbm_best_logloss": best_logloss})
