"""06 rebuild: in-fold target encoding, from memory.

Write the bodies of encode() and cv_mae() without opening the lab script, then run
    python rebuild/06_in_fold_target_encoding.py
check() compares encode() with a pandas groupby mean and with scikit-learn's TargetEncoder, and
cv_mae() with the same 5-fold CV built from scikit-learn parts at fold seeds 0 and 1, on a
category that is pure noise.
"""
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import KFold, cross_val_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import TargetEncoder


def encode(fit_df, apply_df, col, target, smoothing=10):
    """Target-encode `col` with smoothed means of `target`, learned from fit_df rows only.

    A level's value is (sum of its targets + smoothing * mean_all) / (its row count + smoothing),
    where mean_all is fit_df's mean target. Levels fit_df never saw get mean_all. Returns a float
    Series on apply_df's index.
    """
    raise NotImplementedError("write this from memory")


def cv_mae(df, col, target, features, leaky, model, seed=0):
    """Mean validation MAE of `model` over KFold(5, shuffle=True, random_state=seed), on `features`
    plus a column enc that target-encodes `col`.

    leaky=True: encode once on all rows, then run the folds. leaky=False: in each fold, fit the
    encoding on the training rows only and apply it to the training and the validation rows.
    """
    raise NotImplementedError("write this from memory")


class FitThenMap(TargetEncoder):
    """TargetEncoder whose fit_transform(X, y) is fit(X, y).transform(X): the same mapping encode() makes."""
    def fit_transform(self, X, y):
        return self.fit(X, y).transform(X)


def library_cv_mae(df, col, target, features, leaky, model, seed=0):
    """The same CV from scikit-learn parts: a Pipeline refits its encoder on each fold's training rows."""
    te = FitThenMap(smooth=10, target_type="continuous")
    if leaky:
        X = df[features].assign(enc=te.fit_transform(df[[col]], df[target])[:, 0])
    else:
        X = df[features + [col]]
        model = make_pipeline(ColumnTransformer([("enc", te, [col])], remainder="passthrough"), model)
    folds = KFold(5, shuffle=True, random_state=seed)
    return float(-cross_val_score(model, X, df[target], cv=folds, scoring="neg_mean_absolute_error").mean())


def check():
    rng = np.random.default_rng(6)
    keys = np.repeat(list("abcdefghijklmnop"), np.arange(16) % 5 + 1)  # 1 to 5 rows per level
    df = pd.DataFrame({"key": rng.permutation(keys), "x": rng.normal(size=len(keys))})
    df["y"] = 3 * df["x"] + rng.normal(size=len(df))  # the key is pure noise: y never looks at it
    by_hand = df.groupby("key")["y"].transform("mean")
    assert np.allclose(encode(df, df, "key", "y", smoothing=0), by_hand), "encode(smoothing=0) is not the level mean"
    fit = df[df["key"] != "a"]  # level a is one the fit rows never saw
    lib = TargetEncoder(smooth=10, target_type="continuous").fit(fit[["key"]], fit["y"])
    assert np.allclose(encode(fit, df, "key", "y"), lib.transform(df[["key"]])[:, 0]), "encode() differs"
    for seed, leaky in ((0, False), (0, True), (1, False), (1, True)):
        mine = cv_mae(df, "key", "y", ["x"], leaky, LinearRegression(), seed=seed)
        ref = library_cv_mae(df, "key", "y", ["x"], leaky, LinearRegression(), seed=seed)
        assert np.isclose(mine, ref), f"cv_mae(leaky={leaky}, seed={seed}) does not match scikit-learn"
    print("check: PASS")


if __name__ == "__main__":
    check()
