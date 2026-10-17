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
from sklearn.ensemble import IsolationForest

NAB = "https://raw.githubusercontent.com/numenta/NAB/master"
KEY = "realKnownCause/nyc_taxi.csv"
DIR = labkit.DATA / "nab"
DAY, WEEK = 48, 336  # half-hour points
THRESHOLD = 3.0


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


def trailing_z_alarms(values, window, threshold):
    """Alarm where |z| > threshold, with z from the mean and std of the previous `window` points only."""
    mean = values.rolling(window).mean().shift(1)
    std = values.rolling(window).std().shift(1)
    return ((values - mean) / std).abs() > threshold


def whole_series_z_alarms(values, threshold):
    """The break: one mean and one std from the whole series, anomalies included."""
    return ((values - values.mean()) / values.std()).abs() > threshold


def forest_alarms(counts, seed):
    """Isolation Forest on value, hour-of-week and the trailing 1-day mean and std."""
    features = pd.DataFrame({
        "value": counts,
        "hour_of_week": counts.index.dayofweek * 24 + counts.index.hour,
        "mean_1d": counts.rolling(DAY).mean().shift(1),
        "std_1d": counts.rolling(DAY).std().shift(1),
    }).dropna()
    forest = IsolationForest(contamination=0.01, random_state=seed).fit(features)
    flagged = pd.Series(forest.predict(features) == -1, index=features.index)
    return flagged.reindex(counts.index, fill_value=False)


def score_windows(alarm_times, windows, n_days):
    """Windows hit, false alarms per day (alarms outside every window), and per window the
    minutes from its start to its first alarm (None when missed)."""
    inside = np.zeros(len(alarm_times), dtype=bool)
    delays = []
    for start, end in windows:
        in_window = (alarm_times >= start) & (alarm_times <= end)
        inside |= in_window
        hits = alarm_times[in_window]
        delays.append(int((hits.min() - start).total_seconds() // 60) if len(hits) else None)
    return {"windows_hit": sum(d is not None for d in delays),
            "false_alarms_per_day": (~inside).sum() / n_days, "delays_min": delays}


if __name__ == "__main__":
    args = labkit.start(lab=17, device="cpu")
    if args.mode == "download":
        download()
        sys.exit(0)
    counts, windows = load_data(smoke=labkit.smoke())
    n_days = len(counts) / DAY
    change = np.log(counts).diff(WEEK)  # log change vs the same half-hour one week earlier

    def score(alarms):
        return score_windows(counts.index[alarms.to_numpy()], windows, n_days)

    causal = score(trailing_z_alarms(change, WEEK, THRESHOLD))
    if args.mode in ("baseline", "smoke"):
        report("baseline", causal)
    if args.mode in ("change", "smoke"):
        report("change", score(forest_alarms(counts, args.seed)), versus=causal)
    if args.mode in ("break", "smoke"):
        whole = score(whole_series_z_alarms(change, THRESHOLD))
        outside = np.ones(len(counts), dtype=bool)
        for start, end in windows:
            outside &= ~((counts.index >= start) & (counts.index <= end))
        clean = change[outside]  # masking check: the same rule with the windows left out of mean and std
        clean_alarms = ((change - clean.mean()) / clean.std()).abs() > THRESHOLD
        whole["std_ratio"] = change.std() / clean.std()
        whole["windows_hit_outside_stats"] = score(clean_alarms)["windows_hit"]
        report("break", whole)
