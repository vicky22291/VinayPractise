"""10. Random vs time split: test on the future, not a shuffle. LightGBM on hourly bike rentals, tested on a random 20% and on the last 30 days.

Modes: --download, --smoke, --baseline (P1), --change (P2), --break (P3), --check.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "labkit.py").exists())))
import labkit  # before numpy: it sets cache defaults
import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import root_mean_squared_error
from sklearn.model_selection import TimeSeriesSplit, train_test_split

URL = "https://archive.ics.uci.edu/static/public/275/bike+sharing+dataset.zip"
ZIP_BYTES = 279_992
DATA_DIR = labkit.DATA / "bike-sharing"
TARGET = "cnt"
FEATURES = ["season", "yr", "mnth", "hr", "holiday", "weekday", "workingday", "weathersit",
            "temp", "atemp", "hum", "windspeed", "casual", "registered"]
TEST_DAYS = 30
N_TREES = 300


def download():
    archive = labkit.fetch(URL, DATA_DIR / "bike+sharing+dataset.zip", size=ZIP_BYTES)
    labkit.extract(archive, DATA_DIR)
    csv = DATA_DIR / "hour.csv"
    print(f"DATA {csv} {csv.stat().st_size / 1e6:.2f} MB", flush=True)


def load_data():
    """hour.csv plus a 'time' column built from dteday and hr."""
    df = pd.read_csv(DATA_DIR / "hour.csv").drop(columns=["instant"])
    df["time"] = pd.to_datetime(df["dteday"]) + pd.to_timedelta(df["hr"], unit="h")
    return df


def random_split(n_rows, seed):
    """A shuffled 80/20 split of row positions."""
    return train_test_split(np.arange(n_rows), test_size=0.2, random_state=seed)


# --- CONCEPT start ---
def time_split(times, test_days):
    """Test on the last test_days days of times; train on every row before them.

    times: a pandas Series of timestamps, one per row.
    Returns (train_idx, test_idx): numpy arrays of row positions, each in ascending order.
    Every train time must be earlier than every test time.
    """
    raise NotImplementedError("TODO(human)")


# --- CONCEPT end ---


def fit_rmse(df, features, train_idx, test_idx, seed, n_trees=N_TREES):
    """Fit LightGBM on the train rows and return its RMSE on the test rows."""
    train, test = df.iloc[train_idx], df.iloc[test_idx]
    model = lgb.LGBMRegressor(n_estimators=n_trees, random_state=seed, n_jobs=4, verbose=-1)
    model.fit(train[features], train[TARGET])
    return root_mean_squared_error(test[TARGET], model.predict(test[features]))


def check():
    """time_split on a 20-row fixture must match the last fold of scikit-learn's TimeSeriesSplit."""
    slots = pd.date_range(end="2012-12-05 18:00", periods=21, freq="6h")
    times = pd.Series(slots.delete(18))  # 20 rows, 6 hours apart, with 2012-12-05 06:00 missing
    got_train, got_test = time_split(times, test_days=2)
    want_train, want_test = list(TimeSeriesSplit(n_splits=2, test_size=7).split(times))[-1]
    assert np.array_equal(got_train, want_train), f"train rows {got_train} != {want_train}"
    assert np.array_equal(got_test, want_test), f"test rows {got_test} != {want_test}"
    print("check: PASS")


args = labkit.start(lab=10, device="cpu", extra_modes=("check",))
if args.mode == "download":
    download()
elif args.mode == "check":
    check()
elif args.mode == "break":
    print("--break runs from the reference: after your fix, ask the AI to run it, or ask for 'debrief 10'.")
else:
    df, n_trees = load_data(), N_TREES
    if labkit.smoke():
        df, n_trees = df.iloc[:2000], 20
    if args.mode in ("smoke", "baseline"):
        rmse = fit_rmse(df, FEATURES, *random_split(len(df), args.seed), args.seed, n_trees)
        labkit.result("P1.rmse_random", rmse, unit="bikes_per_hour")
    if args.mode in ("smoke", "change"):
        if labkit.smoke():  # smoke checks the plumbing only: a library split stands in for the TODO
            split = list(TimeSeriesSplit(n_splits=2).split(df))[-1]
        else:
            split = time_split(df["time"], TEST_DAYS)
        rmse = fit_rmse(df, FEATURES, *split, args.seed, n_trees)
        labkit.result("P2.rmse_time", rmse, unit="bikes_per_hour")
        baseline = labkit.prior("P1.rmse_random")
        if baseline is not None and not labkit.smoke():
            labkit.result("P2.rmse_time_minus_random", rmse - baseline, unit="bikes_per_hour")
