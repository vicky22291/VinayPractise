"""23. Counterfactual evaluation: declined payments never get a label. A champion declines its top 1% of each
era B day, and a challenger is scored on approvals only, by IPW over a logged exploration slice, and on the truth.

The data is synthetic: scripts/paystream.py generates it. Approved labels count as matured.
Modes: --download, --smoke, --baseline (P1), --change (P2), --break (P3).
This starter loads the data, builds the inputs and owns the RESULT contract. You write the split, the exploration
policy, the metric and the RESULT contract in the lab file, then ipw_recall() below; the AI writes the harness
(the champion and its declines, the challenger in shadow, the slices, the era B training sets, the three modes).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "labkit.py").exists())))
import labkit  # before numpy and pandas: it sets cache defaults
import numpy as np
import pandas as pd

import paystream

ERA_B, TEST_FROM = 91, 151  # era A is days 0 to 90 (no model); era B is days 91 to 182; --break tests 151 to 182
DECLINE = 0.01  # every model declines the payments at or above the 99th percentile of its own day's scores
CHAMPION = ["amount", "hour", "cust_count_1d", "cust_count_7d", "cust_mean_30d"]
CHALLENGER = ["amount", "hour", "cust_count_1d", "cust_mean_1d", "cust_count_7d", "cust_mean_7d",
              "cust_count_30d", "cust_mean_30d", "amount_over_30d_mean", "terminal_frauds_30d"]
SLICES, MODELS = ("0p1pct", "1pct", "5pct"), ("drop", "as_fraud", "weighted", "oracle")
CONTRACT = {  # mode: "name:unit" items in print order; P1, P2 and P3 are the values a prediction asks for
    "baseline": "P1.recall_approved_only:fraction P1.recall_true:fraction P1.gap_points:points "
                "baseline.champion_decline_rate:fraction baseline.challenger_decline_rate:fraction "
                "baseline.frauds:count baseline.frauds_declined:count baseline.hidden_share:fraction "
                "baseline.catches_hidden_share:fraction",
    "change": "P2.ci_width:points change.ipw_recall_1pct:fraction change.ci_lo_1pct:fraction "
              "change.ci_hi_1pct:fraction change.draws_mean_1pct:fraction change.draws_width_1pct:points "
              "change.ci_width_0p1pct:points change.ci_width_5pct:points "
              + " ".join(f"change.explored_{s}:count change.explored_frauds_{s}:count "
                         f"change.fraud_dollars_{s}:dollars" for s in SLICES),
    "break": "P3.recall_drop:fraction P3.recall_weighted:fraction P3.gap_points:points "
             "break.recall_as_fraud:fraction break.recall_oracle:fraction "
             "break.explored_train:count break.explored_train_frauds:count break.blind_frauds:count "
             + " ".join(f"break.blind_recall_{m}:fraction" for m in MODELS),
}


def known_terminal_frauds(tx, labelled, days=30):
    """Per payment at time t: the frauds at its terminal from the `days` days before t whose label arrived
    before t. Only labelled payments count, because a declined payment never becomes a dispute. labelled is
    a boolean array on tx's rows. Sorted keys (terminal * 2**32 + seconds) count every payment at once."""
    secs = lambda when: (when - paystream.START).dt.total_seconds().to_numpy().astype(np.int64)
    fraud = tx[(tx["is_fraud"].to_numpy() == 1) & labelled]
    key = fraud["terminal_id"].to_numpy(np.int64) * 2**32
    arrived, aged_out = key + secs(fraud["label_available_at"]), key + secs(fraud["tx_datetime"]) + days * 86400
    keep = arrived < aged_out  # a label that lands after its window has closed never counts
    now = tx["terminal_id"].to_numpy(np.int64) * 2**32 + secs(tx["tx_datetime"])
    return np.searchsorted(np.sort(arrived[keep]), now) - np.searchsorted(np.sort(aged_out[keep]), now)


def load_data(smoke=False):
    """The synthetic paystream (seed 0) in time order, with day (2018-04-01 is day 0), hour and the customer
    inputs, each from that customer's payments strictly before this one: count and mean amount over the last
    1, 7 and 30 days, and amount / cust_mean_30d. Call known_terminal_frauds() for terminal_frauds_30d once you
    know which payments got a label. Smoke keeps customers 0 to 499, so the 183-day calendar stays whole."""
    tx = paystream.load()
    tx = tx[tx["customer_id"] < 500].reset_index(drop=True) if smoke else tx
    tx["day"], tx["hour"] = (tx["tx_datetime"] - paystream.START).dt.days, tx["tx_datetime"].dt.hour
    ordered = tx.sort_values(["customer_id", "tx_datetime"], kind="stable")
    for n in (1, 7, 30):
        window = (ordered.set_index("tx_datetime").groupby("customer_id")["amount"]
                  .rolling(f"{n}D", closed="left").agg(["count", "mean"]).set_axis(ordered.index))
        tx[f"cust_count_{n}d"], tx[f"cust_mean_{n}d"] = window["count"].fillna(0), window["mean"]
    tx["amount_over_30d_mean"] = tx["amount"] / tx["cust_mean_30d"]
    return tx


def report(mode, values):
    """Print one mode's RESULT lines in CONTRACT order; values maps every RESULT name to its number."""
    names = dict(item.split(":") for item in CONTRACT[mode].split())
    assert set(values) == set(names), f"{mode}: names differ from CONTRACT: {sorted(set(values) ^ set(names))}"
    for name, unit in names.items():
        labkit.result(name, values[name], unit=unit)


def ipw_recall(declined_by_challenger, is_fraud, labeled, propensity, n_boot=200, rng=None):
    """Recall from the labelled rows only, each weighted by 1 / propensity, with a bootstrap interval.

    One entry per payment: the challenger's decline, the fraud label (read only where labeled), whether the
    payment was labelled, and its logged propensity, the probability that the policy let it be labelled.
    Returns (recall, lo, hi): lo and hi are the 2.5th and 97.5th percentiles of n_boot recalls, each on the
    rows resampled with replacement (both nan when n_boot is 0).
    """
    raise NotImplementedError("TODO(human): write this from the IPW formula in the lab file")


# The harness goes here (see the lab file). You write ipw_recall() above; the AI writes the rest from your
# prompt: the champion and its daily declines, the challenger in shadow, the exploration slices, the four
# era B training sets and the three modes, each passing its values to report().


if __name__ == "__main__":
    args = labkit.start(lab=23, device="cpu")
    if args.mode == "download":  # no file to fetch: paystream.py generates the synthetic stream once
        path = paystream.write("v1")
        print(f"HAVE {path} {path.stat().st_size / 1e6:.1f} MB", flush=True)
    elif args.mode == "smoke":  # smoke checks the plumbing only: the inputs build, every CONTRACT name prints
        tx = load_data(smoke=True)
        tx["terminal_frauds_30d"] = known_terminal_frauds(tx, np.ones(len(tx), bool))
        assert set(CHALLENGER) <= set(tx.columns), "load_data() is missing an input"
        for mode, items in CONTRACT.items():
            report(mode, {item.split(":")[0]: float("nan") for item in items.split()})
    else:
        raise NotImplementedError("write the harness: see the lab file")
