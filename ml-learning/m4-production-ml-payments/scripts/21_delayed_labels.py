"""21. Delayed labels: mature, proxy or naive, and an attack that started 3 weeks ago.
Three training sets cut from one synthetic stream as of day 183, each scored on the newest cohort's true labels.

Modes: --download, --smoke, --baseline (P1), --change (P2), --break (P3).
This starter loads the synthetic stream, builds the model inputs and owns the RESULT contract. You write the
three labelling rules, the cohort definition and the RESULT contract in the lab file, then observed_labels()
and training_sets() below. The AI writes the harness: the training set per mode, the model, the scores, the table.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "labkit.py").exists())))
import labkit  # before numpy and pandas: it sets cache defaults
import numpy as np
import pandas as pd
import paystream

DAY = pd.Timedelta(1, unit="D")
TODAY = paystream.START + 183 * DAY   # 2018-10-01 00:00, the morning after the last payment
CUTOFF = paystream.START + 170 * DAY  # training rows end here; days 170 to 182 are the newest cohort
AGES = (7, 14, 30, 60, 90, 120)       # cohort ages in days for the maturity rows
DECLINE_RATE = 0.01                   # decline this share of the newest cohort, highest scores first
# The harness trains LGBMClassifier(n_estimators=100, random_state=seed, verbose=-1, **MODEL); smoke: 20 trees.
MODEL = dict(subsample=0.8, subsample_freq=1, colsample_bytree=0.8, n_jobs=4, deterministic=True, force_col_wise=True)
FEATURES = (["amount", "hour"] + [f"cust_{stat}_{d}d" for d in (1, 7, 30) for stat in ("count", "mean")]
            + ["amount_over_30d_mean", "terminal_known_frauds_30d"])
SCORED = "recall_s4:fraction mean_p:fraction true_rate:fraction mean_p_ratio_no_s4:ratio train_label_rate:fraction"
CONTRACT = {  # mode: "name:unit" items in print order; a name without a step prints as <mode>.<name>
    "baseline": "P1.visible_share_30d:fraction "
                + " ".join(f"true_rate_age{a}:fraction observed_rate_age{a}:fraction" for a in AGES)
                + " recall_1pct:fraction mean_p_ratio:ratio " + SCORED,
    "change": "P2.recall_1pct:fraction P2.recall_1pct_delta:fraction mean_p_ratio:ratio " + SCORED,
    "break": "P3.mean_p_ratio:ratio recall_1pct:fraction " + SCORED,
}


def past_window(ev_key, ev_time, key, time, n_days=None, weight=None):
    """Per query (key, time): same-key events with time - n_days <= event time < time (n_days None: all earlier
    events), counted or summed by weight. Times are timestamp Series; keys are integer arrays or Series."""
    ev_t, t = ((s - paystream.START).dt.total_seconds().to_numpy().astype(np.int64) for s in (ev_time, time))
    ev = np.asarray(ev_key, dtype=np.int64) * 2**32 + ev_t  # one sort key: the key, then seconds since START
    order = np.argsort(ev, kind="stable")
    ev, q = ev[order], np.asarray(key, dtype=np.int64) * 2**32 + t
    lo, hi = np.searchsorted(ev, q - (t if n_days is None else n_days * 86400)), np.searchsorted(ev, q)
    if weight is None:
        return hi - lo
    total = np.concatenate([[0.0], np.cumsum(weight[order])])
    return total[hi] - total[lo]


def add_features(tx):
    """The inputs as of each payment's time t: its customer's payments in the 1, 7 and 30 days before t
    (count, mean amount), and its terminal's frauds of the 30 days before t whose dispute arrived before t."""
    cust, amount, t = tx.customer_id, tx.amount.to_numpy(), tx.tx_datetime
    X = pd.DataFrame({"amount": amount, "hour": t.dt.hour}, index=tx.index)
    for d in (1, 7, 30):
        X[f"cust_count_{d}d"] = n = past_window(cust, t, cust, t, d)
        X[f"cust_mean_{d}d"] = past_window(cust, t, cust, t, d, weight=amount) / np.where(n > 0, n, np.nan)
    X["amount_over_30d_mean"] = amount / X["cust_mean_30d"]
    # Fraud j counts at t when label_available_at_j < t <= tx_datetime_j + 30 days: arrived, minus aged out.
    fast = tx[(tx.is_fraud == 1) & (tx.label_available_at < tx.tx_datetime + 30 * DAY)]
    X["terminal_known_frauds_30d"] = (past_window(fast.terminal_id, fast.label_available_at, tx.terminal_id, t)
                                      - past_window(fast.terminal_id, fast.tx_datetime + 30 * DAY, tx.terminal_id, t))
    return X[FEATURES]


def load_data(smoke=False):
    """(tx, X): the synthetic paystream (seed 0) and its inputs; smoke keeps customers 0 to 499, all 183 days."""
    tx = paystream.load()
    tx = tx[tx.customer_id < 500].reset_index(drop=True) if smoke else tx
    return tx, add_features(tx)


def report(mode, values):
    """Print one mode's RESULT lines in CONTRACT order; values maps each name, without its step, to a number."""
    names = {n.split(".")[-1]: (n if "." in n else f"{mode}.{n}", unit)
             for n, unit in (item.split(":") for item in CONTRACT[mode].split())}
    assert set(values) == set(names), f"{mode}: names differ from CONTRACT: {sorted(set(values) ^ set(names))}"
    for key, (name, unit) in names.items():
        if values[key] is None:  # only the P2 delta, before --baseline ran at this seed
            print(f"NOTE {name} needs --baseline at this seed first", flush=True)
        else:
            labkit.result(name, values[key], unit=unit)


def observed_labels(tx, today):
    """1 for a fraud whose dispute has arrived by today (label_available_at <= today), else 0.
    today is one timestamp, or one per row (a Series on tx's index)."""
    raise NotImplementedError("TODO(human): write this from the lab file's definitions")


def training_sets(tx, today, max_delay_days=120):
    """(naive, mature), each (rows, labels). naive: every row of tx with the labels known today.
    mature: only the rows old enough that every label is final (tx_datetime + max_delay_days <= today)."""
    raise NotImplementedError("TODO(human): write this from the lab file's definitions")


# The harness goes here, written by the AI from your prompt in the lab file: the training set per mode, the
# model, the newest-cohort scores, the maturity rows, the weekly cohort table and the three modes.


if __name__ == "__main__":
    args = labkit.start(lab=21, device="cpu")
    if args.mode == "download":  # no file to fetch: paystream.py generates the synthetic stream once
        path = paystream.write("v1")
        print(f"HAVE {path} {path.stat().st_size / 1e6:.1f} MB", flush=True)
    elif args.mode == "smoke":  # smoke checks the plumbing only: the inputs build and every CONTRACT name prints
        tx, X = load_data(smoke=True)
        assert list(X.columns) == FEATURES and len(X) == len(tx), "load_data() returned the wrong shape"
        for mode, items in CONTRACT.items():
            report(mode, {item.split(":")[0].split(".")[-1]: float("nan") for item in items.split()})
    else:
        raise NotImplementedError("write the harness: see the lab file")
