"""08. Which features does the model use? Split counts, permutation importance and reason codes.
Ranks Adult's columns three ways next to a planted random column, then prints reason codes and their cost.

Modes: --download, --smoke, --baseline (P1), --change (P2), --break (P3), --check.
"""
import sys
import timeit
from pathlib import Path
sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "labkit.py").exists())))
import labkit  # before numpy: it sets cache defaults
import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.inspection import permutation_importance
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

PARQUET = "https://data.openml.org/datasets/0000/1590/dataset_1590.pq"  # the same table, if the OpenML API is down
TREES, MORE_TREES, REPEATS, WARMUP, TIMED = 100, 500, 5, 20, 200  # WARMUP and TIMED: calls per one-row timing

def load_data(seed):
    """Adult (OpenML 1590) plus one column of random integers 0 to 9,999. y = 1 when income is >50K."""
    try:
        df = labkit.openml(1590)
    except Exception as e:
        print(f"OpenML failed ({type(e).__name__}), using the parquet copy", flush=True)
        df = pd.read_parquet(labkit.fetch(PARQUET, labkit.DATA / "adult" / "dataset_1590.pq", size=528_745))
    y = (df.pop("class").astype(str) == ">50K").astype(int)
    text = [c for c in df if not pd.api.types.is_numeric_dtype(df[c])]
    df[text] = df[text].astype(object).astype("category")  # as lab 03: the same categories whichever source answered
    df = df.astype({c: "int64" for c in df if c not in text})  # whole numbers: the parquet copy stores some as floats
    df["random"] = np.random.default_rng(seed).integers(0, 10_000, len(df))
    return df, y

# --- CONCEPT start ---
def permutation_importance_auc(model, X, y, n_repeats=5, seed=0):
    """How much validation AUC drops when one column is shuffled, for every column of X.

    1. base = AUC of model.predict_proba(X)[:, 1] against y, on the untouched X.
    2. For each column, n_repeats times: copy X, shuffle that one column, score again,
       keep base minus the new AUC. Shuffle by position, not by index label:
       X[col].values[rng.permutation(len(X))] keeps the dtype and skips index alignment.
    3. Return a pandas Series: column name -> mean drop. Use rng = np.random.default_rng(seed).
    """
    raise NotImplementedError("TODO(human)")


# --- CONCEPT end ---

def check():
    """--check: permutation_importance_auc against sklearn on a 20-row fixture with a category column."""
    rng = np.random.default_rng(0)
    X = pd.DataFrame({"strong": rng.normal(size=400), "weak": rng.normal(size=400),
                      "colour": pd.Categorical(rng.choice(["blue", "red"], 400))}, index=rng.permutation(400) + 1000)
    y = (3 * X["strong"] + 1.5 * X["weak"] + rng.normal(size=400) > 0).astype(int)
    rows = np.r_[np.flatnonzero(y == 1)[:10], np.flatnonzero(y == 0)[:10]]  # the fixture: 10 positives, 10 negatives
    rest = X.drop(index=X.index[rows]).assign(colour="red").astype({"colour": X["colour"].dtype})  # no tree uses colour
    model = LGBMClassifier(n_estimators=30, n_jobs=1, random_state=0, verbose=-1).fit(rest, y.loc[rest.index])
    mine = permutation_importance_auc(model, X.iloc[rows], y.iloc[rows], n_repeats=50, seed=0)
    lib = permutation_importance(model, X.iloc[rows], y.iloc[rows], scoring="roc_auc", n_repeats=50, random_state=0)
    lib = pd.Series(lib.importances_mean, index=X.columns)
    print(pd.DataFrame({"yours": mine, "sklearn": lib}).round(3).to_string())
    assert list(mine.index) == list(X.columns), "return one value per column, in column order"
    assert (mine.rank(ascending=False) == lib.rank(ascending=False)).all(), "ranks differ from sklearn"
    assert np.allclose(mine, lib, atol=0.1), "mean drops are far from sklearn's"
    print("check: PASS")

def fit(X_tr, y_tr, X_va, y_va, trees, seed):
    """Train LightGBM; return it with its validation AUC."""
    model = LGBMClassifier(n_estimators=trees, random_state=seed, verbose=-1).fit(X_tr, y_tr)
    return model, float(roc_auc_score(y_va, model.predict_proba(X_va)[:, 1]))

def rankings(model, X_va, y_va, seed):
    """Split count, gain and validation permutation importance per column; returns the random column's ranks."""
    if labkit.smoke():  # smoke checks the plumbing only: sklearn stands in for the TODO
        r = permutation_importance(model, X_va, y_va, scoring="roc_auc", n_repeats=REPEATS, random_state=seed)
        perm = pd.Series(r.importances_mean, index=X_va.columns)
    else:
        perm = permutation_importance_auc(model, X_va, y_va, REPEATS, seed)
    imp = pd.DataFrame({"split": model.feature_importances_, "gain": model.booster_.feature_importance("gain"),
                        "perm_auc_drop": perm}, index=X_va.columns)
    ranks = imp.rank(ascending=False, method="min").astype(int)  # 1 = most important
    if not labkit.smoke():
        print(imp.join(ranks, rsuffix="_rank").sort_values("split_rank").round(4).to_string(), flush=True)
    return ranks.loc["random"]

def reason_codes(model, X_va):
    """TreeSHAP reasons for the 3 highest-scored rows, the mean |SHAP| rank of sex, and ms per call."""
    contrib = model.predict(X_va, pred_contrib=True)  # log-odds per column, then the expected value
    assert np.allclose(contrib.sum(axis=1), model.predict(X_va, raw_score=True))  # they add up to the score
    shap = pd.DataFrame(contrib[:, :-1], index=X_va.index, columns=X_va.columns)
    shap_rank = shap.abs().mean().rank(ascending=False, method="min").astype(int)  # by mean |SHAP|
    labkit.result("baseline.sex_shap_rank", shap_rank["sex"], unit="rank_of_15")
    score = model.predict_proba(X_va)[:, 1]
    top = np.argsort(-score, kind="stable")[:3]
    for k, i in enumerate(top, 1):
        reasons = shap.iloc[i].nlargest(3)  # the three columns that pushed this score up the most
        text = "|".join(f"{c}={X_va.iloc[i][c]}:{v:+.2f}" for c, v in reasons.items())
        labkit.result(f"baseline.reasons_{k}", text, unit="column=value:log_odds", score=round(float(score[i]), 3))
    one = X_va.iloc[[top[0]]]  # one request: a scoring service hands the trees a numeric vector, on one thread
    codes = one.apply(lambda s: s.cat.codes if isinstance(s.dtype, pd.CategoricalDtype) else s).to_numpy(float)
    assert np.allclose(model.booster_.predict(codes), model.predict_proba(one)[:, 1])
    for name, explain in (("score", False), ("explanation", True)):
        times = timeit.repeat(lambda: model.booster_.predict(codes, pred_contrib=explain, num_threads=1), number=1,
                              repeat=WARMUP + TIMED)[WARMUP:]  # drop the warm-up calls
        labkit.result(f"baseline.ms_per_{name}", 1000 * float(np.median(times)), unit="ms", device="cpu",
                      batch=1, warmup=WARMUP, n=TIMED, stat="median", threads=1)

args = labkit.start(lab=8, device="cpu", extra_modes=("check",))
if args.mode == "check":
    sys.exit(check())
X, y = load_data(args.seed)
if args.mode == "download":
    print(f"DATA {labkit.DATA / 'openml'} adult: {len(X)} rows, {X.shape[1]} columns with the random one", flush=True)
    sys.exit(0)
X_tr, X_va, y_tr, y_va = train_test_split(X, y, test_size=0.2, stratify=y, random_state=args.seed)
if labkit.smoke():  # tiny data, same code path
    X_tr, X_va, y_tr, y_va = X_tr.iloc[:3200], X_va.iloc[:800], y_tr.iloc[:3200], y_va.iloc[:800]

if args.mode in ("baseline", "smoke"):
    model, base_auc = fit(X_tr, y_tr, X_va, y_va, TREES, args.seed)
    r = rankings(model, X_va, y_va, args.seed)
    labkit.result("P1.random_rank_split", r["split"], unit="rank_of_15")
    labkit.result("P1.random_rank_perm", r["perm_auc_drop"], unit="rank_of_15")
    labkit.result("baseline.random_rank_gain", r["gain"], unit="rank_of_15")
    labkit.result("baseline.auc", base_auc, unit="fraction")
    reason_codes(model, X_va)

if args.mode in ("change", "smoke"):
    base_auc = base_auc if labkit.smoke() else labkit.prior("baseline.auc")
    if base_auc is None:
        print(f"NOTE no baseline AUC for seed {args.seed}: run --baseline first to get the change lines", flush=True)
    for name, cols in (("relationship", ["relationship"]), ("both", ["relationship", "marital-status"])):
        _, dropped_auc = fit(X_tr.drop(columns=cols), y_tr, X_va.drop(columns=cols), y_va, TREES, args.seed)
        labkit.result(f"P2.auc_without_{name}", dropped_auc, unit="fraction")
        if base_auc is not None:
            labkit.result(f"P2.auc_change_without_{name}", dropped_auc - base_auc, unit="fraction")

if args.mode in ("break", "smoke"):
    model, more_auc = fit(X_tr, y_tr, X_va, y_va, MORE_TREES, args.seed)
    r = rankings(model, X_va, y_va, args.seed)
    labkit.result("P3.random_rank_split", r["split"], unit="rank_of_15")
    labkit.result("break.random_rank_perm", r["perm_auc_drop"], unit="rank_of_15")
    labkit.result("break.random_rank_gain", r["gain"], unit="rank_of_15")
    labkit.result("break.auc", more_auc, unit="fraction")
