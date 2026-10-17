"""Rebuild 21: observed labels as of a date, a weekly cohort report, and the naive and mature training sets.

Write the three bodies from memory, then run: python rebuild/21_label_maturity.py
check() compares them with a brute-force loop over 1,000 synthetic rows, never with this lab's results.
"""
import numpy as np
import pandas as pd

DAY = pd.Timedelta(1, unit="D")


def observed_labels(tx, today):
    """1 for a fraud whose dispute has arrived by today (label_available_at <= today), else 0, as an int
    Series on tx's index. today is one timestamp, or one per row (a Series on tx's index)."""
    return ((tx.is_fraud == 1) & (tx.label_available_at <= today)).astype(int)


def cohort_report(tx, today, freq="W"):
    """One row per cohort: the payments grouped by tx_datetime.dt.to_period(freq), in time order. Columns:
    true_rate (the mean of is_fraud), observed_rate (the mean of the observed label today) and n (payments)."""
    rates = pd.DataFrame({"true_rate": tx.is_fraud, "observed_rate": observed_labels(tx, today)})
    groups = rates.groupby(tx.tx_datetime.dt.to_period(freq))
    return groups.mean().assign(n=groups.size())


def training_sets(tx, today, max_delay_days=120):
    """(naive, mature), each a (rows, labels) pair. naive: every row of tx with its observed label today.
    mature: only the rows with tx_datetime + max_delay_days <= today, with the same labels."""
    y = observed_labels(tx, today)
    mature = tx.tx_datetime + max_delay_days * DAY <= today
    return (tx, y), (tx[mature], y[mature])


def check():
    rng = np.random.default_rng(0)
    n, start = 1_000, pd.Timestamp("2018-04-01")
    today = start + 183 * DAY
    secs = rng.integers(0, 183 * 86400, n)
    secs[:2] = 63 * 86400, 63 * 86400 + 1  # exactly on the 120-day maturity line, and one second after it
    tx = pd.DataFrame({"tx_datetime": start + pd.to_timedelta(np.sort(secs), unit="s"),
                       "is_fraud": (rng.random(n) < 0.2).astype(int)})
    delay = pd.to_timedelta(np.round(rng.uniform(7, 120, n) * 86400), unit="s")
    tx["label_available_at"] = (tx.tx_datetime + delay).where(tx.is_fraud == 1)  # NaT for a legitimate payment
    edge = tx.index[(tx.is_fraud == 1) & (tx.tx_datetime > today - 100 * DAY)][:2]
    tx.loc[edge, "label_available_at"] = [today, today + pd.Timedelta(1, unit="s")]  # lands today, a second late
    rows = list(tx.itertuples())

    def seen(r, when):  # the brute-force observed label
        return int(r.is_fraud == 1 and pd.notna(r.label_available_at) and r.label_available_at <= when)

    for when in (today, today - 45 * DAY):
        got = observed_labels(tx, when)
        assert list(got.index) == list(tx.index), "observed_labels keeps tx's index"
        assert got.tolist() == [seen(r, when) for r in rows], "observed_labels differs from the loop"
    per_row = observed_labels(tx, tx.tx_datetime + 30 * DAY)  # each payment read at age 30 days
    assert per_row.tolist() == [seen(r, r.tx_datetime + 30 * DAY) for r in rows], "a per-row today differs"
    for freq in ("W", "D"):
        groups = {}
        for r in rows:  # brute force: the Monday (or the day) on which each payment's cohort starts
            day = r.tx_datetime.normalize()
            groups.setdefault(day - pd.Timedelta(day.weekday(), unit="D") if freq == "W" else day, []).append(r)
        want = [(k, len(g), np.mean([r.is_fraud for r in g]), np.mean([seen(r, today) for r in g]))
                for k, g in sorted(groups.items())]
        report = cohort_report(tx, today, freq)
        got = [(p.start_time, int(c.n), c.true_rate, c.observed_rate) for p, c in report.iterrows()]
        assert len(got) == len(want), f"freq {freq}: one row per cohort"
        for (k1, n1, t1, o1), (k2, n2, t2, o2) in zip(got, want):
            assert k1 == k2 and n1 == n2, f"freq {freq}: cohort {k2:%Y-%m-%d} has the wrong start or size"
            assert abs(t1 - t2) < 1e-12 and abs(o1 - o2) < 1e-12, f"freq {freq}: cohort {k2:%Y-%m-%d} rates differ"
    (naive, y_naive), (mature, y_mature) = training_sets(tx, today)
    assert list(naive.index) == list(tx.index), "the naive set keeps every row"
    assert y_naive.tolist() == [seen(r, today) for r in rows], "naive labels differ from the loop"
    assert list(mature.index) == [r.Index for r in rows if r.tx_datetime + 120 * DAY <= today], "mature rows differ"
    assert (y_mature == mature.is_fraud).all(), "every mature label must equal the true label"
    print("check: PASS")


if __name__ == "__main__":
    check()
