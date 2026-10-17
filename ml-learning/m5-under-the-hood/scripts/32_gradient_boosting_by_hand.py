"""32. Gradient boosting by hand. A boosting loop of depth-3 trees next to LightGBM, at learning rates 0.1 and 1.0.

Modes: --download, --smoke, --baseline (P1), --change (P2), --break (P3).
Level S starter: load_data() and report() are given. You write boost() from the formula in the lab file,
then the AI writes the harness for the three measured modes.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "labkit.py").exists())))
import labkit  # before numpy: it sets cache defaults
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import log_loss
from sklearn.model_selection import train_test_split

PARQUET = "https://data.openml.org/datasets/0000/1590/dataset_1590.pq"  # fallback 1
UCI = "https://archive.ics.uci.edu/static/public/2/adult.zip"  # fallback 2
TREES, CHECKPOINTS, TIMED = 300, (10, 100, 300), (300, 1000)  # trees per loop, log-loss checkpoints, timed tree counts
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


args = labkit.start(lab=32, device="cpu")
if args.mode == "download":
    print(f"DATA {labkit.DATA} adult rows={len(adult())}", flush=True)
elif args.mode == "smoke":  # smoke checks the plumbing only: a library model stands in for the harness you will write
    X_tr, X_va, y_tr, y_va = load_data(args.seed, smoke=True)
    model = GradientBoostingClassifier(max_depth=3, n_estimators=10, random_state=args.seed).fit(X_tr, y_tr)
    stand_in = log_loss(y_va, model.predict_proba(X_va)[:, 1])
    for mode, names in CONTRACT.items():
        report(mode, dict.fromkeys(names, stand_in), device="cpu", batch=1, warmup=0, n=0, stat="median", threads=1)
else:
    raise NotImplementedError("write the harness: see the lab file")
