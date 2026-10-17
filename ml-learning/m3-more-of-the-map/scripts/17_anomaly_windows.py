"""17. Anomaly windows. Score a causal z-score and an Isolation Forest on NYC taxi demand by labelled windows.

Modes: --download, --smoke, --baseline (P1), --change (P2), --break (P3).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "labkit.py").exists())))
import labkit  # before numpy and pandas: it sets cache defaults
import json
import numpy as np
import pandas as pd

NAB = "https://raw.githubusercontent.com/numenta/NAB/master"
KEY = "realKnownCause/nyc_taxi.csv"
DIR = labkit.DATA / "nab"
DAY, WEEK = 48, 336  # half-hour points


def download():
    labkit.fetch(f"{NAB}/data/{KEY}", DIR / "nyc_taxi.csv", size=265_771)
    labkit.fetch(f"{NAB}/labels/combined_windows.json", DIR / "combined_windows.json", size=15_359)


def load_data(smoke=False):
    """Half-hourly passenger counts (a float Series with a timestamp index) and the five
    labelled windows as (start, end) Timestamps in time order. Smoke keeps the last 6 weeks."""
    counts = pd.read_csv(DIR / "nyc_taxi.csv", parse_dates=["timestamp"], index_col="timestamp")["value"]
    labels = json.loads((DIR / "combined_windows.json").read_text())[KEY]
    if smoke:
        counts = counts.iloc[-6 * WEEK:]
    return counts.astype(float), [(pd.Timestamp(a), pd.Timestamp(b)) for a, b in labels]


def report(mode, scores, versus=None):
    """Print the RESULT lines for one detector: the contract the lab file names.

    scores: windows_hit (of 5), false_alarms_per_day, delays_min (one per window in time
    order, None when missed), and in --break also std_ratio and windows_hit_outside_stats.
    versus: the causal z-score's scores, so --change also prints its deltas against them.
    """
    step = {"baseline": "P1", "change": "P2", "break": "P3"}[mode]
    hit_step = "baseline" if mode == "baseline" else step  # P1 asks about false alarms only
    alarm_step = "break" if mode == "break" else step  # P3 asks about windows hit only
    labkit.result(f"{hit_step}.windows_hit", scores["windows_hit"], unit="of_5")
    labkit.result(f"{alarm_step}.false_alarms_per_day", scores["false_alarms_per_day"], unit="per_day")
    if versus is not None:
        labkit.result(f"{step}.windows_hit_delta", scores["windows_hit"] - versus["windows_hit"], unit="of_5")
        labkit.result(f"{step}.false_alarms_per_day_delta",
                      scores["false_alarms_per_day"] - versus["false_alarms_per_day"], unit="per_day")
    for i, delay in enumerate(scores["delays_min"], 1):
        labkit.result(f"{mode}.delay_min_w{i}", "miss" if delay is None else delay, unit="min")
    if mode == "break":
        labkit.result("break.std_ratio", scores["std_ratio"], unit="ratio")
        labkit.result("break.windows_hit_outside_stats", scores["windows_hit_outside_stats"], unit="of_5")


# The harness goes here (see the lab file, section 3). You write trailing_z_alarms() and
# score_windows(); the AI writes the Isolation Forest, the break and the three modes from your prompt.


if __name__ == "__main__":
    args = labkit.start(lab=17, device="cpu")
    if args.mode == "download":
        download()
    elif args.mode == "smoke":  # smoke checks the plumbing only: load_data() and report(), placeholder scores
        counts, windows = load_data(smoke=True)
        nan = float("nan")
        placeholder = {"windows_hit": nan, "false_alarms_per_day": nan, "delays_min": [None] * len(windows),
                       "std_ratio": nan, "windows_hit_outside_stats": nan}
        for mode in ("baseline", "change", "break"):
            report(mode, placeholder, versus=placeholder if mode == "change" else None)
    else:
        raise NotImplementedError("write the harness: see the lab file")
