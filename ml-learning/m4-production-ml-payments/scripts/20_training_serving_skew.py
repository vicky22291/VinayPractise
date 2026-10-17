"""20. Training-serving skew replay. One feature, two code paths: the batch path trains, serving_features.py serves.

Modes: --download, --smoke, --baseline (P1), --change (P2), --break (P3).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "labkit.py").exists())))
import labkit  # before numpy and pandas: it sets cache defaults
import numpy as np
import pandas as pd

import serving_features

TRIPS = labkit.DATA / "tlc" / "yellow_tripdata_2024-01.parquet"
TRIPS_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-01.parquet"
START, END = pd.Timestamp("2024-01-01"), pd.Timestamp("2024-02-01")
TEST_START = pd.Timestamp("2024-01-25")  # test week: 25 to 31 January
HOUR = pd.Timedelta(1, unit="h")
N_QUERIES, N_TREES = 200_000, 300
ZONES = list(range(1, 264))  # TLC zones 264 and 265 are "Unknown" and "Outside of NYC"


def download():
    labkit.fetch(TRIPS_URL, TRIPS, size=49_961_641)


def load_data(seed, smoke=False):
    """Every January pickup as (zone, time), sorted by time, and N_QUERIES of them as queries.

    A query is a pickup whose hour before and hour after both fall inside January, sampled with
    the seed and sorted by time. Smoke keeps the 3 busiest zones and 2,000 queries.
    """
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
    """Print the RESULT lines for one mode: the contract the lab file names.

    mae: the test MAE in pickups. versus: the --baseline MAE, so --change also prints the ratio.
    rows: in --change, 20 test rows (zone, time and both last-hour counts), printed side by side.
    """
    step = {"baseline": "P1", "change": "P2"}[mode]
    labkit.result(f"{step}.mae", mae, unit="pickups")
    if versus is not None:
        labkit.result(f"{step}.mae_ratio", mae / versus, unit="ratio")
    if rows is not None and not labkit.smoke():
        print(rows.to_string(index=False), flush=True)


# The harness goes here (see the lab file). You write batch_counts(); the AI writes the rest from
# your prompt: the target, the four inputs, the split, LightGBM and the two modes.


if __name__ == "__main__":
    args = labkit.start(lab=20, device="cpu")
    if args.mode == "download":
        download()
    elif args.mode == "smoke":  # smoke checks the plumbing only: load_data(), serving_counts(), report()
        events, queries = load_data(args.seed, smoke=True)
        serving_features.serving_counts(events, queries)
        report("baseline", 1.0)
        report("change", 1.0, versus=1.0)
    elif args.mode == "break":
        print("--break runs from the reference: after your fix, ask the AI to run it, or ask for 'debrief 20'.")
    else:
        raise NotImplementedError("write the harness: see the lab file")
