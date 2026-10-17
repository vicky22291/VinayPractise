"""20. Training-serving skew replay. One feature, two code paths: the batch path trains, serving_features.py serves.

Modes: --download, --smoke, --baseline (P1), --change (P2), --break (P3).
Reference (answers only): --change imports scripts/serving_features.py as it stands. --break reveals with replay(),
a copy with switches, and reads the learner's file only in its last, guarded line, so no edit can stop the reveal.
"""
import sys
from collections import defaultdict, deque
from pathlib import Path
sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "labkit.py").exists())))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "m4-production-ml-payments" / "scripts"))
import labkit  # before numpy and pandas: it sets cache defaults
import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error

TRIPS = labkit.DATA / "tlc" / "yellow_tripdata_2024-01.parquet"
TRIPS_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-01.parquet"
START, END, TEST_START = pd.Timestamp("2024-01-01"), pd.Timestamp("2024-02-01"), pd.Timestamp("2024-01-25")
HOUR, HOUR_NP = pd.Timedelta(1, unit="h"), np.timedelta64(1, "h")
N_QUERIES, N_TREES = 200_000, 300
ZONES = list(range(1, 264))  # TLC zones 264 and 265 are "Unknown" and "Outside of NYC"


def load_data(seed, smoke=False):
    """The stream (every January pickup, by time) and N_QUERIES seeded pickups with a full January hour either
    side, by time, as queries. Smoke: the 3 busiest zones, 2,000 queries."""
    trips = pd.read_parquet(TRIPS, columns=["PULocationID", "tpep_pickup_datetime"])
    trips.columns = ["zone", "time"]
    trips = trips[(trips.time >= START) & (trips.time < END) & trips.zone.isin(ZONES)]
    if smoke:
        trips = trips[trips.zone.isin(trips.zone.value_counts().index[:3])]
    events = trips.sort_values("time", kind="stable").reset_index(drop=True)
    inside = events[(events.time >= START + HOUR) & (events.time < END - HOUR)]
    queries = inside.sample(2_000 if smoke else N_QUERIES, random_state=seed)
    return events, queries.sort_values("time", kind="stable").reset_index(drop=True)


def report(mode, mae, versus=None, rows=None):
    """The RESULT contract, as in the starter: the MAE, the ratio to `versus` (the --baseline MAE), and the 20 rows."""
    step = {"baseline": "P1", "change": "P2"}[mode]
    labkit.result(f"{step}.mae", mae, unit="pickups")
    if versus is not None:
        labkit.result(f"{step}.mae_ratio", mae / versus, unit="ratio")
    if rows is not None and not labkit.smoke():
        print(rows.to_string(index=False), flush=True)


def batch_counts(event_times, query_times):
    """Pickups in [t - 1 h, t) for each query time t. event_times: one zone's pickups, sorted."""
    return np.searchsorted(event_times, query_times) - np.searchsorted(event_times, query_times - HOUR_NP)


def batch_feature(events, queries, offset=pd.Timedelta(0, unit="h")):
    """batch_counts() zone by zone: one count per query, in query order. offset shifts every t."""
    counts, query_times = np.zeros(len(queries), dtype=np.int64), (queries.time + offset).to_numpy()
    by_zone = {zone: times.to_numpy() for zone, times in events.groupby("zone").time}
    for zone, rows in queries.groupby("zone").indices.items():
        counts[rows] = batch_counts(by_zone[zone], query_times[rows])
    return counts


def replay(events, queries, utc_clock=True, right_closed=True, left_open=True):
    """serving_features.serving_counts() with its planted differences as switches (all True: as shipped).
    utc_clock: the request time goes to UTC (+5 h in January), pickup times stay local. right_closed: a query
    counts its own pickup. left_open: a pickup exactly 1 h old drops out of the window."""
    recent, counts = defaultdict(deque), np.zeros(len(queries), dtype=np.int64)
    to_utc = queries.time.dt.tz_localize("America/New_York").dt.tz_convert("UTC").dt.tz_localize(None)
    clock = to_utc if utc_clock else queries.time
    stream = zip(events.zone.to_numpy(), events.time)
    zone, time = next(stream, (None, None))
    for k, (q_zone, q_time, now) in enumerate(zip(queries.zone.to_numpy(), queries.time, clock)):
        while time is not None and (time <= q_time if right_closed else time < q_time):
            recent[zone].append(time)
            zone, time = next(stream, (None, None))
        window = recent[q_zone]
        while window and (window[0] <= now - HOUR if left_open else window[0] < now - HOUR):
            window.popleft()
        counts[k] = len(window)
    return counts


def table(queries, last_hour):
    """The four model inputs: the last-hour count, hour, weekday and zone (a category)."""
    return pd.DataFrame({"last_hour": last_hour, "hour": queries.time.dt.hour.to_numpy(),
                         "weekday": queries.time.dt.dayofweek.to_numpy(),
                         "zone": pd.Categorical(queries.zone, categories=ZONES)})


def fit(X, y, seed):
    trees = 20 if labkit.smoke() else N_TREES
    return lgb.LGBMRegressor(n_estimators=trees, random_state=seed, n_jobs=4, verbose=-1).fit(X, y)


def run_break(events, queries, batch, model, y, train, test, seed):
    """The reveal: mismatch as shipped, each difference alone, the fix, logged-value training, the learner's fix."""
    shipped = replay(events, queries)
    counts = {name: replay(events, queries, *switches) for name, switches in (
        ("fix_clock", (False, True, True)), ("fix_window", (True, False, False)),
        ("fix_clock_and_right_edge", (False, False, True)), ("fixed", (False, False, False)))}
    labkit.result("P3.mismatch_rate", np.mean(shipped != batch), unit="fraction")
    for name, values in counts.items():
        labkit.result(f"break.mismatch_rate_{name}", np.mean(values != batch), unit="fraction")
    labkit.result("break.serving_zero_share", np.mean(shipped == 0), unit="fraction")
    labkit.result("break.batch_zero_share", np.mean(batch == 0), unit="fraction")
    logged = table(queries, shipped)  # what the shipped serving path served, and so logged
    labkit.result("break.test_mean_target", np.mean(y[test]), unit="pickups")
    labkit.result("break.mean_prediction_shipped", np.mean(model.predict(logged[test])), unit="pickups")
    for name in ("fix_clock", "fixed"):
        served = table(queries, counts[name])[test]
        labkit.result(f"break.mae_{name}", mean_absolute_error(y[test], model.predict(served)), unit="pickups")
    logged_model = fit(logged[train], y[train], seed)  # Rules of ML #29: train on the logged values
    labkit.result("break.mae_logged", mean_absolute_error(y[test], logged_model.predict(logged[test])), unit="pickups")
    try:  # the learner's file as it stands, on every query: a half-finished edit must not hide the lines above
        import serving_features
        yours = np.asarray(serving_features.serving_counts(events, queries)).reshape(batch.shape)
        labkit.result("break.mismatch_rate_your_fix", np.mean(yours != batch), unit="fraction")
    except Exception as e:
        print(f"break.mismatch_rate_your_fix not measured: serving_features.py raised {e!r}", flush=True)


def main():
    args = labkit.start(lab=20, device="cpu")
    if args.mode == "download":
        return labkit.fetch(TRIPS_URL, TRIPS, size=49_961_641)
    events, queries = load_data(args.seed, smoke=labkit.smoke())
    y = batch_feature(events, queries, offset=HOUR)  # the target: pickups in [t, t + 1 h)
    batch = batch_feature(events, queries)
    train = (queries.time < TEST_START - HOUR).to_numpy()  # every training target ends before the test week
    test = (queries.time >= TEST_START).to_numpy()
    X = table(queries, batch)
    model, baseline_mae = fit(X[train], y[train], args.seed), None
    if args.mode in ("smoke", "baseline"):
        baseline_mae = mean_absolute_error(y[test], model.predict(X[test]))
        report("baseline", baseline_mae)
    if args.mode in ("smoke", "change"):
        import serving_features  # the provided file as it stands: only --change and --smoke read it here
        served = serving_features.serving_counts(events, queries)
        mae = mean_absolute_error(y[test], model.predict(table(queries, served)[test]))
        rows = queries[test].assign(last_hour_batch=batch[test], last_hour_serving=served[test])
        rows = rows.sample(20, random_state=args.seed).sort_values("time")
        versus = baseline_mae if labkit.smoke() else labkit.prior("P1.mae")
        report("change", mae, versus=versus, rows=rows[["zone", "time", "last_hour_batch", "last_hour_serving"]])
    if args.mode in ("smoke", "break"):
        run_break(events, queries, batch, model, y, train, test, args.seed)


if __name__ == "__main__":
    main()
