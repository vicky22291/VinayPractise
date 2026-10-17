"""06. Leak through preprocessing: fit every transform inside each fold. Prints the CV MAE (mean absolute
error, dollars) with a category target-encoded inside each fold, and with it encoded on all rows first.

Modes: --download, --smoke, --baseline (P1), --change (P2), --break (P3), --check.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "labkit.py").exists())))
import labkit  # before numpy: it sets cache defaults
import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import KFold, cross_val_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import TargetEncoder

OPENML_ID, TARGET, SMOOTHING = 42165, "SalePrice", 10
PARQUET_URL = "https://data.openml.org/datasets/0004/42165/dataset_42165.pq"  # the same table, one file
PARQUET = labkit.DATA / "house-prices" / "dataset_42165.pq"
CROSS = "Neighborhood_x_YearBuilt"


def download():
    try:
        df = labkit.openml(OPENML_ID)
        print(f"OPENML {OPENML_ID} in {labkit.DATA / 'openml'}: {df.shape[0]} rows x {df.shape[1]} columns")
    except Exception as e:  # the OpenML API is down: fall back to the parquet copy
        print(f"OPENML {OPENML_ID} failed ({type(e).__name__}), fetching the parquet copy")
        labkit.fetch(PARQUET_URL, PARQUET, size=146_413)


def load_data():
    """House Prices, 1,460 rows: the frame with the CROSS key added, and the numeric feature names."""
    df = pd.read_parquet(PARQUET) if PARQUET.exists() else labkit.openml(OPENML_ID)
    df[CROSS] = df["Neighborhood"].astype(str) + "_" + df["YearBuilt"].astype(str)
    numeric = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c]) and c not in ("Id", TARGET)]
    return df, numeric


def make_model(seed):  # force_col_wise: one fixed way to build histograms, so a rerun grows the same trees
    return LGBMRegressor(n_estimators=300, learning_rate=0.05, random_state=seed, n_jobs=4,
                         force_col_wise=True, verbose=-1)


# --- CONCEPT start ---
def encode(fit_df, apply_df, col, target, smoothing=SMOOTHING):
    """Target-encode `col`: a smoothed mean of `target` per level, learned from fit_df rows only.

    Each level gets (sum of its targets + smoothing * mean_all) / (its row count + smoothing), where
    mean_all is the mean target over all of fit_df. A level that fit_df never saw gets mean_all.
    Returns a float Series aligned with apply_df (same index), ready to assign as a new column of apply_df.
    """
    mean_all = fit_df[target].mean()
    stats = fit_df.groupby(col)[target].agg(["sum", "count"])
    smoothed = (stats["sum"] + smoothing * mean_all) / (stats["count"] + smoothing)
    return apply_df[col].map(smoothed).astype(float).fillna(mean_all)


def cv_mae(df, col, target, features, leaky, model, seed=0):
    """5-fold CV MAE of `model` on `features` plus one more column, enc, the target encoding of `col`.

    Folds: KFold(5, shuffle=True, random_state=seed) over the rows of df.
    leaky=True: encode once on all rows (fit_df and apply_df are both df), then run the folds.
    leaky=False: inside each fold, fit the encoding on the training rows only and apply it to the
    training rows and to the validation rows. Either way, fit `model` on the training rows, score
    the MAE on the validation rows, and return the mean MAE over the 5 folds as a float.
    """
    if leaky:
        df = df.assign(enc=encode(df, df, col, target))
    cols, maes = features + ["enc"], []
    for train_idx, valid_idx in KFold(5, shuffle=True, random_state=seed).split(df):
        train, valid = df.iloc[train_idx], df.iloc[valid_idx]
        if not leaky:
            train = train.assign(enc=encode(train, train, col, target))
            valid = valid.assign(enc=encode(train, valid, col, target))
        model.fit(train[cols], train[target])
        maes.append(mean_absolute_error(valid[target], model.predict(valid[cols])))
    return float(np.mean(maes))
# --- CONCEPT end ---


class FitThenMap(TargetEncoder):
    """TargetEncoder whose fit_transform(X, y) is fit(X, y).transform(X): the same mapping encode() makes."""
    def fit_transform(self, X, y):
        return self.fit(X, y).transform(X)


def library_cv_mae(df, col, target, features, leaky, model, seed=0):
    """cv_mae() built from scikit-learn parts: the --check reference and the --smoke stand-in."""
    te = FitThenMap(smooth=SMOOTHING, target_type="continuous")
    if leaky:
        X = df[features].assign(enc=te.fit_transform(df[[col]], df[target])[:, 0])
    else:  # a Pipeline refits every step on the training rows of each fold
        X = df[features + [col]]
        model = make_pipeline(ColumnTransformer([("enc", te, [col])], remainder="passthrough"), model)
    folds = KFold(5, shuffle=True, random_state=seed)
    return float(-cross_val_score(model, X, df[target], cv=folds, scoring="neg_mean_absolute_error").mean())


def check():
    """encode() and cv_mae() against scikit-learn on a 20-row fixture, at fold seeds 0 and 1."""
    df = pd.DataFrame({"key": list("aabbbccccdddddeeeeff"), "x": np.cos(np.arange(20))})
    df["y"] = 2 * df["x"] + df["key"].map(dict(zip("abcdef", range(6)))) + np.sin(3 * np.arange(20))
    fit = df[df["key"] != "f"]  # level f is one the fit rows never saw
    lib = TargetEncoder(smooth=SMOOTHING, target_type="continuous").fit(fit[["key"]], fit["y"])
    assert np.allclose(encode(fit, df, "key", "y"), lib.transform(df[["key"]])[:, 0]), "encode() differs"
    for seed, leaky in ((0, False), (0, True), (1, False), (1, True)):
        mine = cv_mae(df, "key", "y", ["x"], leaky, LinearRegression(), seed=seed)
        ref = library_cv_mae(df, "key", "y", ["x"], leaky, LinearRegression(), seed=seed)
        assert np.isclose(mine, ref), f"cv_mae(leaky={leaky}, seed={seed}) does not match scikit-learn"
    print("check: PASS")


def main():
    args = labkit.start(lab=6, device="cpu", extra_modes=("check",))
    if args.mode in ("download", "check"):
        return download() if args.mode == "download" else check()
    df, numeric = load_data()
    df = df.sample(300, random_state=args.seed) if labkit.smoke() else df
    cv = library_cv_mae if labkit.smoke() else cv_mae  # smoke checks the plumbing only
    model, honest = make_model(args.seed), None
    if args.mode in ("baseline", "smoke"):
        folds = KFold(5, shuffle=True, random_state=args.seed)
        scores = cross_val_score(model, df[numeric], df[TARGET], cv=folds, scoring="neg_mean_absolute_error")
        labkit.result("baseline.mae_numeric_only", -scores.mean(), unit="usd")
        honest = cv(df, "Neighborhood", TARGET, numeric, leaky=False, model=model, seed=args.seed)
        labkit.result("P1.mae_infold", honest, unit="usd")
    if args.mode in ("change", "smoke"):
        leaky = cv(df, "Neighborhood", TARGET, numeric, leaky=True, model=model, seed=args.seed)
        labkit.result("P2.mae_leaky", leaky, unit="usd")
        honest = labkit.prior("P1.mae_infold") if honest is None else honest
        if honest is None:
            sys.exit(f"no P1.mae_infold for seed {args.seed} yet: run --baseline with this seed first")
        labkit.result("P2.mae_change", leaky - honest, unit="usd")  # leaky minus in-fold
        labkit.result("change.gap_pct", 100 * (honest - leaky) / honest, unit="percent")
    if args.mode in ("break", "smoke"):
        honest_x = cv(df, CROSS, TARGET, numeric, leaky=False, model=model, seed=args.seed)
        leaky_x = cv(df, CROSS, TARGET, numeric, leaky=True, model=model, seed=args.seed)
        labkit.result("break.mae_cross_infold", honest_x, unit="usd")
        labkit.result("break.mae_cross_leaky", leaky_x, unit="usd")
        labkit.result("break.mae_change", leaky_x - honest_x, unit="usd")
        labkit.result("P3.gap_pct", 100 * (honest_x - leaky_x) / honest_x, unit="percent")


if __name__ == "__main__":
    main()
