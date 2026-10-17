"""Rebuild 17: a causal (past-only) z-score detector and labelled-window scoring, from memory.

Write both bodies, then run from the module folder: python rebuild/17_window_scoring.py
check() compares with a brute-force numpy loop, a planted spike and alarms planted on a window's
start and end, never with the lab's results.
"""
import numpy as np
import pandas as pd


def trailing_z_alarms(values, window, threshold):
    """values: a pandas Series. Return a boolean Series, True where |z| > threshold, with z from
    the mean and std of the previous `window` points only (a point never sees itself).
    The first `window` points have no z and never alarm."""
    mean = values.rolling(window).mean().shift(1)
    std = values.rolling(window).std().shift(1)
    return ((values - mean) / std).abs() > threshold


def score_windows(alarm_times, windows, n_days):
    """alarm_times: a DatetimeIndex. windows: (start, end) Timestamps, both ends inside.

    Return {"windows_hit": windows with at least one alarm,
            "false_alarms_per_day": alarms outside every window, divided by n_days,
            "delays_min": per window, minutes from its start to its first alarm, None when missed}.
    """
    inside = np.zeros(len(alarm_times), dtype=bool)
    delays = []
    for start, end in windows:
        in_window = (alarm_times >= start) & (alarm_times <= end)
        inside |= in_window
        hits = alarm_times[in_window]
        delays.append(int((hits.min() - start).total_seconds() // 60) if len(hits) else None)
    return {"windows_hit": sum(d is not None for d in delays),
            "false_alarms_per_day": (~inside).sum() / n_days, "delays_min": delays}


def check():
    rng = np.random.default_rng(17)
    values = pd.Series(rng.normal(100.0, 5.0, 2000))
    values.iloc[1500] += 60.0  # a planted spike
    v = values.to_numpy()
    for window, threshold in ((96, 3.0), (10, 0.5)):  # the low threshold makes the std and window details count
        alarms = np.asarray(trailing_z_alarms(values, window, threshold), dtype=bool)
        brute = np.zeros(len(v), dtype=bool)
        for t in range(window, len(v)):  # each point against the window before it
            past = v[t - window:t]
            brute[t] = abs(v[t] - past.mean()) / past.std(ddof=1) > threshold
        assert np.array_equal(alarms, brute), f"z must use the previous {window} points only, sample std (ddof 1)"
        if window == 96:
            assert alarms[1500], "the planted spike should alarm"
            flagged = brute.copy()
    edge = trailing_z_alarms(pd.Series([-1, 0, 1, 3], dtype=float), 3, 3.0)  # the last z is exactly 3
    assert not bool(edge.iloc[-1]), "alarm only when |z| is strictly above the threshold"
    times = pd.date_range("2024-01-01", periods=len(v), freq="30min")
    windows = [(times[1490], times[1530]), (times[1700], times[1710])]
    flagged[1700:1711] = False
    flagged[[1700, 1710]] = True  # alarms exactly on the second window's start and end
    got = score_windows(times[flagged], windows, n_days=len(v) / 48)
    in_w1 = (times >= windows[0][0]) & (times <= windows[0][1])
    inside = in_w1 | ((times >= windows[1][0]) & (times <= windows[1][1]))
    first = int(np.flatnonzero(flagged & in_w1)[0])
    assert got["windows_hit"] == 2 and got["delays_min"] == [(first - 1490) * 30, 0], got
    assert np.isclose(got["false_alarms_per_day"], (flagged & ~inside).sum() / (len(v) / 48)), got
    print("check: PASS")


if __name__ == "__main__":
    check()
