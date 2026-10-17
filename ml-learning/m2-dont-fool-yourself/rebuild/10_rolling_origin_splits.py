"""Rebuild 10: rolling-origin time splits, and random vs time RMSE, from memory.

Write both bodies, then run from the module folder: python rebuild/10_rolling_origin_splits.py
check() compares your folds with scikit-learn's TimeSeriesSplit, and your RMSEs with
train_test_split plus root_mean_squared_error. It never uses this lab's results.
"""
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.linear_model import LinearRegression
from sklearn.metrics import root_mean_squared_error
from sklearn.model_selection import TimeSeriesSplit, train_test_split


def rolling_origin_splits(times, n_splits, test_days, gap_hours):
    """Walk-forward folds over a time column, oldest test window first.

    times: a pandas Series of timestamps, one per row.
    The last n_splits * test_days days become n_splits back-to-back test windows of test_days each.
    Each fold trains on every earlier row, but leaves gap_hours hours out between its last train row
    and its first test row.
    Returns a list of (train_idx, test_idx) pairs: numpy arrays of row positions, ascending.
    Assert in every fold that the latest train time is before the earliest test time.
    """
    raise NotImplementedError("write this from memory")


def random_vs_time_rmse(df, features, target, time_col, model):
    """Fit a fresh copy of model twice and return (random_rmse, time_rmse) on target.

    Random: train_test_split(df, test_size=0.2, random_state=0).
    Time: test on the last 30 days of df[time_col] and train on every row before them
    (rolling_origin_splits with one split and no gap).
    """
    raise NotImplementedError("write this from memory")


def check():
    times = pd.Series(pd.date_range("2011-01-01", periods=17_379, freq="h"))
    folds = rolling_origin_splits(times, n_splits=4, test_days=30, gap_hours=24)
    want = list(TimeSeriesSplit(n_splits=4, test_size=720, gap=24).split(times))
    assert len(folds) == len(want), f"{len(folds)} folds, want {len(want)}"
    for k, ((train, test), (want_train, want_test)) in enumerate(zip(folds, want)):
        assert np.array_equal(train, want_train), \
            f"fold {k}: train rows differ from TimeSeriesSplit ({len(train)} rows, want {len(want_train)})"
        assert np.array_equal(test, want_test), \
            f"fold {k}: test rows differ from TimeSeriesSplit ({len(test)} rows, want {len(want_test)})"

    rng = np.random.default_rng(0)
    df = pd.DataFrame({"t": times[:2_000], "x": rng.normal(size=2_000)})
    df["y"] = 3 * df["x"] + rng.normal(size=2_000)
    got = random_vs_time_rmse(df, ["x"], "y", "t", LinearRegression())

    def rmse(train, test):
        fitted = LinearRegression().fit(train[["x"]], train["y"])
        return root_mean_squared_error(test["y"], fitted.predict(test[["x"]]))

    train, test = train_test_split(df, test_size=0.2, random_state=0)
    train_idx, test_idx = list(TimeSeriesSplit(n_splits=2, test_size=720).split(df))[-1]
    want = (rmse(train, test), rmse(df.iloc[train_idx], df.iloc[test_idx]))
    assert np.allclose(got, want), f"(random, time) RMSE {got} != {want}"
    print("check: PASS")


if __name__ == "__main__":
    check()
