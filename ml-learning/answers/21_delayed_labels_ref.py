"""21. Delayed labels: mature, proxy or naive, and an attack that started 3 weeks ago.
Three training sets cut from one synthetic stream as of day 183, each scored on the newest cohort's true labels.

Modes: --download, --smoke, --baseline (P1), --change (P2), --break (P3).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "labkit.py").exists())))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "m4-production-ml-payments" / "scripts"))
import labkit  # before numpy and pandas: it sets cache defaults
import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier
import paystream

DAY = pd.Timedelta(1, unit="D")
TODAY = paystream.START + 183 * DAY   # 2018-10-01 00:00, the morning after the last payment
CUTOFF = paystream.START + 170 * DAY  # training rows end here; days 170 to 182 are the newest cohort
AGES = (7, 14, 30, 60, 90, 120)       # cohort ages in days for the maturity rows
DECLINE_RATE = 0.01                   # decline this share of the newest cohort, highest scores first
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
    return ((tx.is_fraud == 1) & (tx.label_available_at <= today)).astype(int)


def training_sets(tx, today, max_delay_days=120):
    """(naive, mature), each (rows, labels). naive: every row of tx with the labels known today.
    mature: only the rows old enough that every label is final (tx_datetime + max_delay_days <= today)."""
    y = observed_labels(tx, today)
    mature = tx.tx_datetime + max_delay_days * DAY <= today
    return (tx, y), (tx[mature], y[mature])


def cohort_report(tx, today, freq="W"):
    """One row per cohort (payments grouped by freq on tx_datetime): true and observed fraud rate today, and n."""
    rates = pd.DataFrame({"true_rate": tx.is_fraud, "observed_rate": observed_labels(tx, today)})
    groups = rates.groupby(tx.tx_datetime.dt.to_period(freq))
    return groups.mean().assign(n=groups.size())


def label_set(mode, train):
    """The mode's training rows and labels, read as of TODAY: mature-only, mature plus proxy, or naive."""
    (rows, y), (mature_rows, y_mature) = training_sets(train, TODAY)
    if mode == "baseline":  # mature-only: days 0 to 62, every label final
        return mature_rows, y_mature
    if mode == "change":  # a newer row counts as fraud when its dispute or its proxy flag arrived by today
        y = y.where(rows.index.isin(mature_rows.index), y | (rows.proxy_flag & (rows.proxy_at <= TODAY)).astype(int))
    return rows, y  # change, or break (naive: every row with the labels known today)


def run(mode, tx, X, seed, smoke, done):
    """Train on the mode's training set, score the newest cohort on its true labels, print the results."""
    rows, y = label_set(mode, tx[tx.tx_datetime < CUTOFF])
    new = tx[(tx.tx_datetime >= CUTOFF) & (tx.tx_datetime < TODAY)]
    model = LGBMClassifier(n_estimators=20 if smoke else 100, random_state=seed, verbose=-1, **MODEL)
    p = model.fit(X.loc[rows.index], y).predict_proba(X.loc[new.index])[:, 1]
    declined = p >= np.quantile(p, 1 - DECLINE_RATE)
    fraud, s4 = new.is_fraud.to_numpy() == 1, new.scenario.to_numpy() == 4
    values = dict(recall_1pct=declined[fraud].mean(), recall_s4=declined[s4].mean(), mean_p=p.mean(),
                  true_rate=fraud.mean(), mean_p_ratio=p.mean() / fraud.mean(),
                  mean_p_ratio_no_s4=p[~s4].mean() / fraud[~s4].mean(), train_label_rate=y.mean())
    if mode == "baseline":  # maturity at age a: every payment at least a days old, its label read at age a
        for a in AGES:
            old = tx[tx.tx_datetime + a * DAY <= TODAY]
            values.update({f"true_rate_age{a}": old.is_fraud.mean(),
                           f"observed_rate_age{a}": observed_labels(old, old.tx_datetime + a * DAY).mean()})
        values["visible_share_30d"] = values["observed_rate_age30"] / values["true_rate_age30"]
        table = [f"TABLE cohort week_of={w.start_time:%Y-%m-%d} n={int(r.n)} true_rate={r.true_rate:.6f} observed_rate="
                 f"{r.observed_rate:.6f}" for w, r in cohort_report(tx, TODAY).iterrows()]  # each week, as of today
        print("SMOKE table.cohorts ok" if smoke else "\n".join(table), flush=True)
    if mode == "change":
        before = done["baseline"]["recall_1pct"] if "baseline" in done else labkit.prior("baseline.recall_1pct")
        values["recall_1pct_delta"] = None if before is None else values["recall_1pct"] - before
    done[mode] = values
    report(mode, values)


if __name__ == "__main__":
    args = labkit.start(lab=21, device="cpu")
    if args.mode == "download":  # no file to fetch: paystream.py generates the synthetic stream once
        path = paystream.write("v1")
        print(f"HAVE {path} {path.stat().st_size / 1e6:.1f} MB", flush=True)
    else:  # smoke runs all three modes on 500 customers: the same code path, values hidden
        tx, X = load_data(smoke=labkit.smoke())
        done = {}
        for mode in ("baseline", "change", "break") if labkit.smoke() else (args.mode,):
            run(mode, tx, X, args.seed, labkit.smoke(), done)
