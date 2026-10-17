"""07. Leak through a post-outcome column: ask when each value is known. Columns filled in after the sinking, scored as at boarding time.

Modes: --download, --smoke, --baseline (P1), --change (P2), --break (P3), --check.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "labkit.py").exists())))
import labkit  # before numpy: it sets cache defaults
import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.tree import DecisionTreeClassifier

TARGET = "survived"
POST_OUTCOME = ["boat", "body"]  # boat: the lifeboat a passenger left in; body: the number of a recovered body
PARQUET_URL = "https://data.openml.org/datasets/0004/40945/dataset_40945.pq"
PARQUET = labkit.DATA / "titanic" / "dataset_40945.pq"

args = labkit.start(lab=7, device="cpu", extra_modes=("check",))


def load_data():
    """Titanic as one frame: 7 boarding-time columns, the 2 post-outcome columns and the target."""
    try:
        df = labkit.openml(40945)
    except Exception as e:  # OpenML is down: the same file as parquet
        print(f"OpenML failed ({e!r}); using {PARQUET}", flush=True)
        df = pd.read_parquet(labkit.fetch(PARQUET_URL, PARQUET, size=57430))
    df = df.drop(columns=["name", "ticket", "cabin", "home.dest"])
    for c in (TARGET, "pclass", "sibsp", "parch"):
        df[c] = df[c].astype(int)
    for c in ("sex", "embarked", "boat"):  # unordered categories, so LightGBM splits them as categories
        df[c] = df[c].astype(object).astype("category")
    return df


def as_numeric(col):
    """col as numbers a tree can split: category codes for non-numeric columns, -999 for missing."""
    if not pd.api.types.is_numeric_dtype(col):
        col = col.astype("category").cat.codes.where(col.notna())
    return col.fillna(-999)


# --- CONCEPT start ---
def leak_scan(df, target, threshold=0.9, seed=0):
    """Score every column alone, to find the ones that already know the answer.

    For each column except target: the mean 5-fold ROC AUC of a depth-3 decision tree
    trained on as_numeric(column) only, with folds StratifiedKFold(5, shuffle=True,
    random_state=seed). Return a DataFrame indexed by column name with 'auc' and
    'flagged' (auc >= threshold), sorted by auc, highest first.
    """
    folds = StratifiedKFold(5, shuffle=True, random_state=seed)
    tree = DecisionTreeClassifier(max_depth=3, random_state=seed)
    auc = {c: cross_val_score(tree, as_numeric(df[c]).to_frame(), df[target], cv=folds, scoring="roc_auc").mean()
           for c in df.columns.drop(target)}
    scan = pd.DataFrame({"auc": pd.Series(auc)})
    scan["flagged"] = scan["auc"] >= threshold
    return scan.sort_values("auc", ascending=False)
# --- CONCEPT end ---


def score_without(df, target, model, drop, seed=0):
    """Mean 5-fold CV accuracy of model on every column except target and drop."""
    folds = StratifiedKFold(5, shuffle=True, random_state=seed)
    return cross_val_score(model, df.drop(columns=[target, *drop]), df[target], cv=folds).mean()


def lgbm(seed):
    """LightGBM with its defaults: 100 trees, learning rate 0.1, 31 leaves."""
    return LGBMClassifier(n_estimators=100, random_state=seed, n_jobs=1, verbose=-1)


def baseline(df, seed):
    """P1: the honest model, cross-validated with boat and body dropped."""
    labkit.result("P1.cv_accuracy", score_without(df, TARGET, lgbm(seed), POST_OUTCOME, seed), unit="fraction")


def change(df, seed):
    """P2: the same model and folds with boat and body kept, what the model leans on, and the leak scan."""
    acc = score_without(df, TARGET, lgbm(seed), [], seed)
    labkit.result("P2.cv_accuracy", acc, unit="fraction")
    before = labkit.prior("P1.cv_accuracy")
    if before is not None:
        labkit.result("P2.delta_points", 100 * (acc - before), unit="points")
    fit = lgbm(seed).set_params(importance_type="gain").fit(df.drop(columns=TARGET), df[TARGET])
    gain = pd.Series(fit.feature_importances_, index=fit.feature_name_) / fit.feature_importances_.sum()
    labkit.result("change.top3_gain_share", ",".join(f"{c}:{v:.3f}" for c, v in gain.nlargest(3).items()))
    if labkit.smoke():  # smoke checks the plumbing only: a library stand-in for leak_scan
        auc = df[POST_OUTCOME].apply(lambda col: roc_auc_score(df[TARGET], as_numeric(col)))
        found = auc.to_frame("auc").assign(flagged=False)
    else:
        found = leak_scan(df, TARGET, seed=seed)
    labkit.result("change.scan_auc_boat", found.loc["boat", "auc"], unit="auc")
    labkit.result("change.scan_auc_body", found.loc["body", "auc"], unit="auc")
    labkit.result("change.scan_flagged", ",".join(found.index[found["flagged"]]) or "none")


def break_it(df, seed):
    """P3: the change step's model on the same 5 folds, each test fold scored with boat and body blanked."""
    X, y = df.drop(columns=TARGET), df[TARGET]
    per_fold = []
    for train, test in StratifiedKFold(5, shuffle=True, random_state=seed).split(X, y):
        leaky = lgbm(seed).fit(X.iloc[train], y.iloc[train])
        offline, truth = X.iloc[test], y.iloc[test]
        at_boarding = offline.copy()
        at_boarding.loc[:, POST_OUTCOME] = np.nan  # neither is known when the ship sails
        per_fold.append({"blank": leaky.score(at_boarding, truth), "real": leaky.score(offline, truth),
                         "survive": leaky.predict(at_boarding).mean(), "actual": truth.mean(),
                         "died": (truth == 0).mean()})
    mean = pd.DataFrame(per_fold).mean()  # the mean over the 5 test folds, as cross_val_score reports it
    labkit.result("P3.leaky_blanked_accuracy", mean["blank"], unit="fraction")
    honest = labkit.prior("P1.cv_accuracy")  # the honest model on these same folds is the baseline's
    if honest is not None:
        gap = 100 * (mean["blank"] - honest)
        labkit.result("P3.gap_points", gap, unit="points")
        labkit.result("P3.leaky_vs_honest", "above" if gap > 0 else "below" if gap < 0 else "same")
    labkit.result("break.leaky_real_accuracy", mean["real"], unit="fraction")
    labkit.result("break.predicted_survival_rate", mean["survive"], unit="fraction")
    labkit.result("break.actual_survival_rate", mean["actual"], unit="fraction")
    labkit.result("break.all_died_accuracy", mean["died"], unit="fraction")


def check():
    """leak_scan on a 20-row fixture, against values scikit-learn's cross_val_score gives on it."""
    i, y = np.arange(20), np.tile([0, 1], 10)
    age = (i * 7 % 40 + 15).astype(float)
    age[[2, 7, 13]] = np.nan  # a few unknown ages, so missing values pass through as_numeric
    fixture = pd.DataFrame({"boat": np.where(y == 1, np.resize(["4", "7", "C"], 20), np.resize(["11", "13", "15"], 20)),
                            "age": age, "sex": np.where((y == 1) ^ (i % 5 == 0), "female", "male"),
                            "embarked": "S", TARGET: y})
    found = leak_scan(fixture, TARGET)
    # boat is planted: its codes split the two classes, so 1. embarked is constant, so a coin flip, 0.5.
    # age and sex: computed once with scikit-learn 1.9.1's cross_val_score, the docstring's tree and folds.
    for c, want in {"boat": 1.0, "age": 0.75, "sex": 0.8, "embarked": 0.5}.items():
        assert np.isclose(found.loc[c, "auc"], want), f"{c}: leak_scan says {found.loc[c, 'auc']}, scikit-learn {want}"
    assert list(found.columns) == ["auc", "flagged"] and TARGET not in found.index, "auc and flagged, target left out"
    assert found["auc"].is_monotonic_decreasing, "sort by auc, highest first"
    assert found.index[0] == "boat" and found["flagged"].sum() == 1, "the planted column tops the scan, flagged alone"
    print("check: PASS")


if args.mode == "check":
    check()
else:
    df = load_data()
    if args.mode == "download":
        print(f"DATA titanic {len(df)} rows, {df.shape[1] - 1} feature columns kept, under {labkit.DATA}", flush=True)
    if labkit.smoke():
        df = df.sample(300, random_state=args.seed)
    if args.mode in ("baseline", "smoke"):
        baseline(df, args.seed)
    if args.mode in ("change", "smoke"):
        change(df, args.seed)
    if args.mode in ("break", "smoke"):
        break_it(df, args.seed)
