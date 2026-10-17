"""23. Counterfactual evaluation: declined payments never get a label. A champion declines its top 1% of each
era B day, and a declined payment never gets a label. Score a challenger three ways (on the champion's approvals,
by IPW over a logged exploration slice, on the synthetic truth), then retrain it on era B three ways.

The data is synthetic: scripts/paystream.py generates it. Approved labels count as matured.
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
    rng = np.random.default_rng(0) if rng is None else rng
    w = np.where(labeled, 1.0 / np.where(labeled, propensity, 1.0), 0.0) * (np.asarray(is_fraud) == 1)
    hit, boots = w * np.asarray(declined_by_challenger, dtype=float), []
    for _ in range(n_boot):
        i = rng.integers(0, len(w), len(w))  # the rows, resampled with replacement
        boots.append(hit[i].sum() / w[i].sum())
    lo, hi = np.percentile(boots, [2.5, 97.5]) if n_boot else (np.nan, np.nan)
    return hit.sum() / w.sum(), lo, hi


EPS = 0.01  # the logged exploration slice: P2 estimates with it and --break trains with it
SIZES = {"0p1pct": 0.001, "1pct": EPS, "5pct": 0.05}  # --change sizes the slice three ways


def fit(X, y, trees, seed, weight=None):
    """LightGBM at its defaults apart from the tree count; the seed drives its bin sampling."""
    trees = min(trees, 20) if labkit.smoke() else trees  # smoke checks the plumbing only
    return LGBMClassifier(n_estimators=trees, random_state=seed, verbose=-1).fit(X, y, sample_weight=weight)


def declines(model, rows, features):
    """True where the model's score is at or above the 99th percentile of its own day's scores."""
    score = model.predict_proba(rows[features])[:, 1]
    cut = pd.Series(score).groupby(rows["day"].to_numpy()).transform(lambda s: np.quantile(s, 1 - DECLINE))
    return score >= cut.to_numpy()


def world(tx, seed):
    """Era A (no model, every label arrives) trains the champion, which declines its top 1% of each era B day.
    Only era A rows and era B approvals feed terminal_frauds_30d; the slice's few labels are left out of it, so
    every slice scores the same challenger. Then one uniform draw per era B row: a would-be decline is
    explored (approved anyway, propensity logged) when its draw is below the slice size."""
    in_a = (tx["day"] < ERA_B).to_numpy()
    champ = declines(fit(tx.loc[in_a, CHAMPION], tx.loc[in_a, "is_fraud"], 150, seed), tx[~in_a], CHAMPION)
    labelled = in_a.copy()
    labelled[~in_a] = ~champ
    tx["terminal_frauds_30d"] = known_terminal_frauds(tx, labelled)
    rng = np.random.default_rng(seed)
    return tx[in_a], tx[~in_a], champ, rng.random(int((~in_a).sum())), rng


def challenger(A, B, seed):
    """The challenger, trained on era A, deciding era B at the matched 1% decline rate (shadow: never acted on)."""
    return declines(fit(A[CHALLENGER], A["is_fraud"], 300, seed), B, CHALLENGER)


def run_baseline(tx, seed):
    A, B, champ, _, _ = world(tx, seed)
    chall, fraud = challenger(A, B, seed), B["is_fraud"].to_numpy() == 1
    approved_only, true = chall[fraud & ~champ].mean(), chall[fraud].mean()
    return {"P1.recall_approved_only": approved_only, "P1.recall_true": true,
            "P1.gap_points": 100 * (approved_only - true), "baseline.champion_decline_rate": champ.mean(),
            "baseline.challenger_decline_rate": chall.mean(), "baseline.frauds": fraud.sum(),
            "baseline.frauds_declined": (fraud & champ).sum(), "baseline.hidden_share": (fraud & champ).sum() / fraud.sum(),
            "baseline.catches_hidden_share": (fraud & champ & chall).sum() / (fraud & chall).sum()}


def run_change(tx, seed):
    A, B, champ, u, rng = world(tx, seed)
    chall, fraud, amount, values = challenger(A, B, seed), B["is_fraud"].to_numpy() == 1, B["amount"].to_numpy(), {}
    for name, eps in SIZES.items():
        explored = champ & (u < eps)  # nested: the 0.1% slice sits inside the 1%, the 1% inside the 5%
        recall, lo, hi = ipw_recall(chall, fraud, ~champ | explored, np.where(champ, eps, 1.0), 200, rng)
        values.update({f"change.explored_{name}": explored.sum(), f"change.explored_frauds_{name}": (explored & fraud).sum(),
                       f"change.fraud_dollars_{name}": amount[explored & fraud].sum(),
                       ("P2.ci_width" if name == "1pct" else f"change.ci_width_{name}"): 100 * (hi - lo)})
        if name == "1pct":
            values.update({"change.ipw_recall_1pct": recall, "change.ci_lo_1pct": lo, "change.ci_hi_1pct": hi})
    draws = [ipw_recall(chall, fraud, ~champ | (champ & (rng.random(len(B)) < EPS)), np.where(champ, EPS, 1.0), 0)[0]
             for _ in range(200)]  # 200 fresh 1% slices: the spread one log's bootstrap stands in for
    lo, hi = np.percentile(draws, [2.5, 97.5])
    values.update({"change.draws_mean_1pct": np.mean(draws), "change.draws_width_1pct": 100 * (hi - lo)})
    return values


def run_break(tx, seed):
    _, B, champ, u, _ = world(tx, seed)
    train = (B["day"] < TEST_FROM).to_numpy()
    T, S, every = B[train], B[~train], np.ones(int(train.sum()), bool)
    y, approved, explored = T["is_fraud"].to_numpy(), ~champ[train], (champ & (u < EPS))[train]
    sets = {"drop": (approved, y, None), "as_fraud": (every, np.where(approved, y, 1), None),  # rows, label, weight
            "weighted": (approved | explored, y, np.where(explored, 1 / EPS, 1.0)), "oracle": (every, y, None)}
    fraud, blind, recall, values = S["is_fraud"].to_numpy() == 1, champ[~train], {}, {}  # blind: champion declines
    for name, (rows, label, weight) in sets.items():
        model = fit(T[CHALLENGER][rows], label[rows], 300, seed, None if weight is None else weight[rows])
        dec = declines(model, S, CHALLENGER)
        recall[name], values[f"break.blind_recall_{name}"] = dec[fraud].mean(), dec[fraud & blind].mean()
    return {**values, "P3.recall_drop": recall["drop"], "P3.recall_weighted": recall["weighted"],
            "P3.gap_points": 100 * (recall["drop"] - recall["weighted"]), "break.recall_as_fraud": recall["as_fraud"],
            "break.recall_oracle": recall["oracle"], "break.explored_train": explored.sum(),
            "break.explored_train_frauds": (explored & (y == 1)).sum(), "break.blind_frauds": (fraud & blind).sum()}


if __name__ == "__main__":
    args = labkit.start(lab=23, device="cpu")
    if args.mode == "download":  # no file to fetch: paystream.py generates the synthetic stream once
        path = paystream.write("v1")
        sys.exit(print(f"HAVE {path} {path.stat().st_size / 1e6:.1f} MB", flush=True))
    tx = load_data(smoke=labkit.smoke())
    steps = {"baseline": run_baseline, "change": run_change, "break": run_break}
    for mode in (steps if labkit.smoke() else [args.mode]):  # smoke runs every step on 500 customers
        report(mode, steps[mode](tx, args.seed))
