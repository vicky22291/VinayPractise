"""Lab 16 rebuild: a complete zone-hour grid, lags that point exactly k hours back,
the seasonal-naive MAE, and a spot check that a lag reads the past.

Write the four bodies from memory, then run: python rebuild/16_lag_features.py
check() compares with direct pandas lookups and scikit-learn, never with the lab's results.
"""
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error


def complete_grid(df):
    """Every zone x every hour from df's first to last hour, pickups 0 where df has no row.

    df has columns zone, hour, pickups. Return the same columns, sorted by zone then hour.
    """
    raise NotImplementedError("write this from memory")


def add_lags(grid, lags=(1, 24, 168)):
    """Add lag_k for each k: the same zone's pickups k hours earlier. On a complete grid one row is one hour."""
    raise NotImplementedError("write this from memory")


def seasonal_naive_mae(grid, test_start):
    """MAE of 'same hour last week' (lag_168) on rows with hour >= test_start and a lag_168."""
    raise NotImplementedError("write this from memory")


def assert_lag_is_past(grid, k, n=200, seed=0):
    """Raise AssertionError unless n random lag_k values equal a direct lookup k hours back."""
    raise NotImplementedError("write this from memory")


def check():
    rng = np.random.default_rng(0)
    hours = pd.date_range("2024-01-01 08:00", "2024-01-22 20:00", freq="h")
    full = pd.DataFrame([(z, h, rng.poisson(5 if 7 <= h.hour <= 20 else 1)) for z in range(4) for h in hours],
                        columns=["zone", "hour", "pickups"])
    sparse = full[full.pickups > 0]  # a zone-hour with no pickup has no row, as after a groupby count
    grid = complete_grid(sparse)
    assert len(grid) == len(full) and grid.pickups.sum() == full.pickups.sum(), "grid is not every zone x hour"
    grid = add_lags(grid)
    lookup = full.set_index(["zone", "hour"]).pickups
    for k in (1, 24, 168):
        rows = grid.dropna(subset=[f"lag_{k}"]).sample(200, random_state=k)
        direct = lookup.loc[list(zip(rows.zone, rows.hour - pd.Timedelta(k, unit="h")))].to_numpy()
        assert np.array_equal(rows[f"lag_{k}"].to_numpy(), direct), f"lag_{k} is not {k} hours back"
        assert_lag_is_past(grid, k)
    test_start = hours[-48]
    test = grid[(grid.hour >= test_start) & grid.lag_168.notna()]
    expected = mean_absolute_error(test.pickups, test.lag_168)
    assert np.isclose(seasonal_naive_mae(grid, test_start), expected), "MAE differs from scikit-learn"
    try:
        assert_lag_is_past(add_lags(sparse), 168)
    except (AssertionError, KeyError):
        pass
    else:
        raise AssertionError("assert_lag_is_past passed lags built on a table with missing zone-hours")
    print("check: PASS")


if __name__ == "__main__":
    check()
