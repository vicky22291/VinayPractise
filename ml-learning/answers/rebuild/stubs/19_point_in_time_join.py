"""Rebuild 19: a point-in-time join. Write known_before() from memory, then run:

    python rebuild/19_point_in_time_join.py

check() compares your function with a brute-force count on 150 synthetic events with same-second ties.
"""
import numpy as np
import pandas as pd


def known_before(events, labels):
    """For each event, how many labels at its terminal arrived strictly before the event's time.

    events: DataFrame with terminal_id and t (a payment's tx_datetime), in any order.
    labels: DataFrame with terminal_id and label_available_at, one row per fraud.
    Returns an int64 numpy array, one count per event, in the order of events.
    Build a per-terminal cumulative count in label_available_at order, join it to the events with
    pd.merge_asof(by="terminal_id", allow_exact_matches=False), then assert that every joined
    label predates its event.
    """
    raise NotImplementedError("write this from memory")


def check():
    """Compare known_before() with a brute-force count on 150 events with same-second ties."""
    rng = np.random.default_rng(19)
    start = pd.Timestamp("2018-04-01")
    events = pd.DataFrame({"terminal_id": rng.integers(0, 5, 150),
                           "t": start + pd.to_timedelta(rng.integers(0, 60, 150), unit="s")})
    labels = pd.DataFrame({"terminal_id": rng.integers(0, 5, 60),
                           "label_available_at": start + pd.to_timedelta(rng.integers(0, 60, 60), unit="s")})
    assert events["t"].isin(labels["label_available_at"]).any(), "the fixture needs same-second ties"
    same = events["terminal_id"].to_numpy()[:, None] == labels["terminal_id"].to_numpy()[None, :]
    before = labels["label_available_at"].to_numpy()[None, :] < events["t"].to_numpy()[:, None]
    want = (same & before).sum(axis=1)
    got = np.asarray(known_before(events, labels))
    assert got.shape == want.shape, f"expected {want.shape[0]} counts, got shape {got.shape}"
    assert (got == want).all(), f"{int((got != want).sum())} of 150 counts differ from the brute force"
    print("check: PASS")


if __name__ == "__main__":
    check()
