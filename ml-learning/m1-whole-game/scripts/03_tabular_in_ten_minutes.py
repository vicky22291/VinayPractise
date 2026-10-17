"""03. Tabular in ten minutes: majority baseline, logistic regression and LightGBM. Three models, one table, two metrics.

Modes: --download, --smoke, --baseline (P1), --change (P2), --break (P3), --tabpfn (optional, needs tabpfn==9.2.0).
"""
import importlib.util
import os
import sys
from pathlib import Path
sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "labkit.py").exists())))
import labkit  # before numpy, torch, transformers: it sets cache defaults
import lightgbm as lgb
import numpy as np
import pandas as pd
from scipy.stats import rankdata
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

PARQUET = "https://data.openml.org/datasets/0000/1590/dataset_1590.pq"
UCI = "https://archive.ics.uci.edu/static/public/2/adult.zip"
COLUMNS = ["age", "workclass", "fnlwgt", "education", "education-num", "marital-status", "occupation",
           "relationship", "race", "sex", "capital-gain", "capital-loss", "hours-per-week", "native-country", "class"]
N_SMALL = 5_000   # --change: LightGBM's training rows
N_TABPFN = 1_000  # --tabpfn: the most training rows TabPFN v2 accepts on a CPU


def load_adult(folder=labkit.DATA / "adult"):
    """Adult census income (OpenML 1590) as features X and target y (1 when income is >50K)."""
    try:
        df = labkit.openml(1590)
    except Exception as e:  # the OpenML API is down: use its parquet copy, then the UCI original
        print(f"RETRY OpenML API ({e})", flush=True)
        try:
            df = pd.read_parquet(labkit.fetch(PARQUET, folder / "dataset_1590.pq", size=528_745))
        except OSError as e2:
            print(f"RETRY parquet copy ({e2})", flush=True)
            uci = labkit.extract(labkit.fetch(UCI, folder / "adult.zip", size=620_237), folder / "uci")
            df = pd.concat([pd.read_csv(uci / f, names=COLUMNS, skipinitialspace=True, na_values="?", skiprows=skip)
                            for f, skip in (("adult.test", 1), ("adult.data", 0))], ignore_index=True)  # OpenML order
    y = df["class"].astype(str).str.rstrip(".").eq(">50K").astype(int)  # UCI's test file ends each label in "."
    X = df.drop(columns="class")
    text = [c for c in X if not pd.api.types.is_numeric_dtype(X[c])]
    X[text] = X[text].astype(object).astype("category")  # the same categories whichever source answered
    return X, y


def logreg(X):
    numeric = [c for c in X if pd.api.types.is_numeric_dtype(X[c])]
    text = [c for c in X if c not in numeric]
    # Q: Why does the StandardScaler sit inside the pipeline instead of scaling the whole table once before the split?
    prep = ColumnTransformer([("numeric", StandardScaler(), numeric),
                              ("text", OneHotEncoder(handle_unknown="ignore"), text)])
    return make_pipeline(prep, LogisticRegression(max_iter=2000))


def lgbm(seed):
    # Q: Why does LightGBM need no one-hot step for the category columns, when logistic regression does?
    return lgb.LGBMClassifier(n_estimators=100, random_state=seed, verbose=-1)  # 31 leaves, learning rate 0.1


def auc_pairwise(y, s):
    """AUC by its definition: the chance that a random positive scores above a random negative; a tie counts 0.5."""
    y, s = np.asarray(y), np.asarray(s, dtype=float)
    diff = s[y == 1][:, None] - s[y == 0][None, :]  # every positive against every negative
    return ((diff > 0).sum() + 0.5 * (diff == 0).sum()) / diff.size


def auc_rank(y, s):
    """The same number from the Mann-Whitney rank formula, without building every pair."""
    y, s = np.asarray(y), np.asarray(s, dtype=float)
    n_pos, n_neg = int((y == 1).sum()), int((y == 0).sum())
    ranks = rankdata(s)  # 1 = lowest score; tied scores share their average rank
    u = ranks[y == 1].sum() - n_pos * (n_pos + 1) / 2  # Mann-Whitney U: the pairs the positives win
    return u / (n_pos * n_neg)


def score(model, X, y):
    # Q: What does accuracy score here, what does AUC score, and when can the two disagree?
    p = model.predict_proba(X)[:, 1]
    assert abs(auc_rank(y, p) - auc_pairwise(y, p)) < 1e-12, "the two AUC forms must agree"
    return accuracy_score(y, p > 0.5), auc_rank(y, p)


def tabpfn_v2(seed):  # TabPFN v2 on the CPU: its weights are ungated, v2.5 and later need a Prior Labs login
    os.environ.setdefault("TABPFN_MODEL_CACHE_DIR", str(labkit.DATA / "tabpfn"))
    os.environ.setdefault("TABPFN_NO_BROWSER", "1")  # fail fast instead of opening a licence page
    import torch
    from tabpfn import TabPFNClassifier, constants
    torch.set_num_threads(1)  # LightGBM and torch each load their own OpenMP; more torch threads deadlock
    return TabPFNClassifier.create_default_for_version(constants.ModelVersion.V2, device="cpu", random_state=seed)


def baseline(X_tr, X_te, y_tr, y_te, seed):
    auc = {}
    for name, model in (("majority", DummyClassifier(strategy="most_frequent")),
                        ("logreg", logreg(X_tr)), ("lgbm", lgbm(seed))):
        acc, auc[name] = score(model.fit(X_tr, y_tr), X_te, y_te)
        labkit.result(f"baseline.acc_{name}", acc, unit="fraction")
        labkit.result("P1.auc_lgbm" if name == "lgbm" else f"baseline.auc_{name}", auc[name], unit="fraction")
    labkit.result("P1.gap_vs_logreg_points", 100 * (auc["lgbm"] - auc["logreg"]), unit="auc_points")


def change(X_tr, X_te, y_tr, y_te, seed):
    X_n, _, y_n, _ = train_test_split(X_tr, y_tr, train_size=N_SMALL, stratify=y_tr, random_state=seed)
    _, auc = score(lgbm(seed).fit(X_n, y_n), X_te, y_te)  # the same test rows as --baseline
    labkit.result("P2.auc_5000_rows", auc, unit="fraction")
    full = labkit.prior("P1.auc_lgbm")  # what --baseline printed with this seed, if it ran
    if full is not None:
        labkit.result("P2.delta_points", 100 * (auc - full), unit="auc_points")


def break_it(X_tr, X_te, y_tr, y_te, seed):
    y_shuffled = np.random.default_rng(seed).permutation(y_tr.to_numpy())  # the same labels in a random order
    _, auc = score(lgbm(seed).fit(X_tr, y_shuffled), X_te, y_te)  # the test labels stay as they are
    labkit.result("P3.auc_shuffled", auc, unit="fraction")


def compare_tabpfn(X_tr, X_te, y_tr, y_te, seed):
    n = 200 if labkit.smoke() else N_TABPFN  # TabPFN is slow on a CPU
    X_n, _, y_n, _ = train_test_split(X_tr, y_tr, train_size=n, stratify=y_tr, random_state=seed)
    for name, make in (("lgbm", lgbm), ("tabpfn", tabpfn_v2)):  # LightGBM first: see tabpfn_v2()
        _, auc = score(make(seed).fit(X_n, y_n), X_te, y_te)
        labkit.result(f"tabpfn.auc_{name}_1000_rows", auc, unit="fraction")


if __name__ == "__main__":
    args = labkit.start(lab=3, device="cpu", extra_modes=("tabpfn",))
    have_tabpfn = importlib.util.find_spec("tabpfn") is not None
    if args.mode == "tabpfn" and not have_tabpfn:
        sys.exit("--tabpfn is optional and needs: python -m pip install tabpfn==9.2.0")
    X, y = load_adult()
    if args.mode == "download":
        print(f"DATA Adult census {len(X):,} rows x {X.shape[1]} features, cached under {labkit.DATA}")
        if have_tabpfn:
            with labkit.locked(labkit.DATA / "tabpfn" / "v2"):
                weights = Path(tabpfn_v2(0).fit(X.head(100), y.head(100)).model_path)  # the first fit downloads
            print(f"HAVE {weights} {weights.stat().st_size / 1e6:.1f} MB")
        sys.exit()
    if labkit.smoke():  # tiny data, the same code path: 5,600 training rows still hold the 5,000-row subset
        X, _, y, _ = train_test_split(X, y, train_size=7_000, stratify=y, random_state=args.seed)
    split = train_test_split(X, y, test_size=0.2, stratify=y, random_state=args.seed)  # X_tr, X_te, y_tr, y_te
    print(f"DATA train {len(split[0]):,} rows, test {len(split[1]):,} rows", flush=True)
    for mode, step in (("baseline", baseline), ("change", change), ("break", break_it), ("tabpfn", compare_tabpfn)):
        if args.mode == mode or (labkit.smoke() and (mode != "tabpfn" or have_tabpfn)):  # --smoke runs every step
            step(*split, args.seed)
