"""16. Forecast demand: seasonal naive first, then lag features. Zone-hour taxi pickups: same hour last week vs LightGBM on lags.

Modes: --download, --smoke, --baseline (P1), --change (P2), --break (P3), --check.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "labkit.py").exists())))
import labkit  # before numpy: it sets cache defaults
import numpy as np
import pandas as pd
import lightgbm as lgb
from sklearn.metrics import mean_absolute_error

TLC = labkit.DATA / "tlc"
TRIPS = TLC / "yellow_tripdata_2024-01.parquet"
ZONES = TLC / "taxi_zone_lookup.csv"
START, END = pd.Timestamp("2024-01-01"), pd.Timestamp("2024-02-01")
TEST_START = pd.Timestamp("2024-01-25")  # test week: 25 to 31 January
MIN_PER_DAY = 100
LAGS = (1, 24, 168)
FEATURES = [f"lag_{k}" for k in LAGS] + ["hour_of_week"]


def download():
    """Fetch the January 2024 yellow taxi trips and the taxi zone lookup."""
    labkit.fetch("https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-01.parquet",
                 TRIPS, size=49_961_641)
    labkit.fetch("https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv", ZONES, size=12_331)


def load_trips(smoke=False):
    """January pickups in the zones that average at least MIN_PER_DAY pickups a day."""
    trips = pd.read_parquet(TRIPS, columns=["tpep_pickup_datetime", "PULocationID"])
    trips = trips[(trips.tpep_pickup_datetime >= START) & (trips.tpep_pickup_datetime < END)].copy()
    trips["hour"] = trips.tpep_pickup_datetime.dt.floor("h")
    per_day = trips.groupby("PULocationID").size() / (END - START).days
    zones = per_day.index[per_day >= MIN_PER_DAY]
    if smoke:
        zones = zones[:3]
    return trips.loc[trips.PULocationID.isin(zones), ["PULocationID", "hour"]]


def count_pickups(trips):
    """Pickups per zone and hour."""
    return trips.groupby(["PULocationID", "hour"]).size().rename("pickups").reset_index()


def add_features(table):
    """Lag columns and hour_of_week for each zone."""
    table = table.sort_values(["PULocationID", "hour"]).reset_index(drop=True)
    for k in LAGS:
        table[f"lag_{k}"] = table.groupby("PULocationID").pickups.shift(k)
    table["hour_of_week"] = table.hour.dt.dayofweek * 24 + table.hour.dt.hour
    return table


# --- CONCEPT start ---
def seasonal_naive_mae(table, test_start):
    """Mean absolute error of the seasonal-naive forecast on the test rows.

    The forecast for a zone-hour is that zone's count one week earlier: the
    lag_168 column. Test rows are those with hour >= test_start. Skip a row
    whose lag_168 is NaN. Return a float.
    """
    test = table[(table.hour >= test_start) & table.lag_168.notna()]
    return float((test.pickups - test.lag_168).abs().mean())
# --- CONCEPT end ---


def lightgbm_mae(table, features, seed):
    """Fit LightGBM on the rows before TEST_START, return its MAE on the rest."""
    train = table[table.hour < TEST_START].dropna(subset=features)
    test = table[table.hour >= TEST_START]
    model = lgb.LGBMRegressor(n_estimators=20 if labkit.smoke() else 500, objective="l1",
                              random_state=seed, verbose=-1)
    model.fit(train[features], train.pickups)
    return mean_absolute_error(test.pickups, model.predict(test[features]))


# --- reference only start ---
def complete_grid(counts):
    """Every zone x hour of January, 0 where no trip started (the fix)."""
    hours = pd.date_range(START, END, freq="h", inclusive="left")
    index = pd.MultiIndex.from_product([counts.PULocationID.unique(), hours], names=["PULocationID", "hour"])
    return counts.set_index(["PULocationID", "hour"]).pickups.reindex(index, fill_value=0).reset_index()


def run_break(trips, table, seed):
    """Honest numbers, the size of the planted problem, then one more planted leak."""
    grid = add_features(complete_grid(count_pickups(trips)))
    lag_hour = table.groupby("PULocationID").hour.shift(168)  # the hour shipped lag_168 really reads
    lagged = lag_hour.notna()
    wrong = lag_hour[lagged] != table.hour[lagged] - pd.Timedelta(168, unit="h")
    labkit.result("break.missing_zone_hours_pct", 100 * (1 - len(table) / len(grid)), unit="percent")
    labkit.result("break.wrong_lag168_pct", 100 * wrong.mean(), unit="percent")
    naive = seasonal_naive_mae(grid, TEST_START)
    honest = lightgbm_mae(grid, FEATURES, seed)
    labkit.result("break.honest_seasonal_naive_mae", naive, unit="pickups")
    labkit.result("P3.honest_lightgbm_mae", honest, unit="pickups")
    labkit.result("break.honest_improvement_pct", 100 * (naive - honest) / naive, unit="percent")
    shipped = grid.merge(table[["PULocationID", "hour"]], how="left", indicator=True)._merge.eq("both")
    same_rows = lightgbm_mae(grid[(grid.hour < TEST_START) | shipped], FEATURES, seed)  # same fit, shipped test rows
    labkit.result("break.honest_lightgbm_mae_shipped_rows", same_rows, unit="pickups")
    grid["lead_1"] = grid.groupby("PULocationID").pickups.shift(-1)  # the next hour: reads the future
    leaky = lightgbm_mae(grid, FEATURES + ["lead_1"], seed)
    labkit.result("break.leaky_lightgbm_mae", leaky, unit="pickups")
# --- reference only end ---


def check():
    """seasonal_naive_mae on a 20-row fixture against scikit-learn's mean_absolute_error."""
    rng = np.random.default_rng(0)
    hours = pd.date_range(TEST_START - pd.Timedelta(4, unit="h"), periods=10, freq="h")
    fixture = pd.DataFrame({"PULocationID": np.repeat([1, 2], 10), "hour": np.tile(hours, 2),
                            "pickups": rng.integers(0, 40, 20),
                            "lag_168": rng.integers(0, 40, 20).astype(float)})
    fixture.loc[[7, 16], "lag_168"] = np.nan
    test = fixture[(fixture.hour >= TEST_START) & fixture.lag_168.notna()]
    expected = mean_absolute_error(test.pickups, test.lag_168)
    got = seasonal_naive_mae(fixture, TEST_START)
    assert np.isclose(got, expected), f"seasonal_naive_mae gave {got}, scikit-learn gives {expected}"
    print("check: PASS")


def main():
    args = labkit.start(lab=16, device="cpu", extra_modes=("check",))
    if args.mode == "download":
        return download()
    if args.mode == "check":
        return check()
    trips = load_trips(smoke=labkit.smoke())
    table = add_features(count_pickups(trips))
    if labkit.smoke():  # smoke checks the plumbing only: a library stand-in replaces the TODO
        test = table[(table.hour >= TEST_START) & table.lag_168.notna()]
        naive = mean_absolute_error(test.pickups, test.lag_168)
    else:
        naive = seasonal_naive_mae(table, TEST_START)
    if args.mode in ("smoke", "baseline"):
        labkit.result("P1.seasonal_naive_mae", naive, unit="pickups")
    if args.mode in ("smoke", "change"):
        model_mae = lightgbm_mae(table, FEATURES, args.seed)
        labkit.result("change.lightgbm_mae", model_mae, unit="pickups")
        labkit.result("P2.improvement_pct", 100 * (naive - model_mae) / naive, unit="percent")
    if args.mode in ("smoke", "break"):
        run_break(trips, table, args.seed)


if __name__ == "__main__":
    main()
