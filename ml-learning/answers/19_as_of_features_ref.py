"""19. Time split and as-of features. One LightGBM, shipped vs point-in-time inputs, time vs random split.

Reference, both paths, synthetic data. --baseline and --change run features_v0.py as shipped: terminal_fraud_rate is
the mean of every final label at the terminal, the row's own included. --break swaps in the frauds whose dispute
reached the terminal in the 30 days before the payment (as-of on label_available_at) and prints the 2x3 table.
Modes: --download, --smoke, --baseline (P1), --change (P2), --break (P3).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "labkit.py").exists())))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "m4-production-ml-payments" / "scripts"))
import labkit  # before numpy and pandas: it sets cache defaults
import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

import features_v0
import paystream

TIME_SPLIT = {"full": (120, 127), "smoke": (40, 47)}  # train on days before the first, test from the second
TERMINAL_INPUTS = {"asof": "terminal_known_30d",            # disputes that reached the terminal in [t - 30 d, t)
                   "final_others": "terminal_rate_others",  # final fraud rate at the terminal, own label left out
                   "final_all": "terminal_fraud_rate"}      # final fraud rate, own label in: as shipped
OTHER_INPUTS = ["amount", "hour", "cust_count_1d", "cust_mean_1d", "cust_count_7d", "cust_mean_7d",  # by name, so
                "cust_count_30d", "cust_mean_30d", "amount_over_30d_mean"]  # --break still runs on a fixed features_v0


def download():
    """No file to fetch: paystream.py generates the synthetic stream once and caches it."""
    path = paystream.write("v1")
    print(f"HAVE {path} {path.stat().st_size / 1e6:.1f} MB", flush=True)


def load_data(smoke=False):
    """The synthetic paystream transactions (seed 0) by tx_datetime, plus day (0 is 2018-04-01). Smoke: 60 days."""
    tx = paystream.load(smoke=smoke)
    tx["day"] = (tx["tx_datetime"] - paystream.START).dt.days
    return tx


def report(mode, auc, importances=None, versus=None, table=None):
    """Print the RESULT lines for one mode: the contract the lab file names.

    auc: this mode's test AUC. importances: LightGBM gain importance, a Series by feature name.
    versus: in --change, the --baseline AUC (prints the difference). table: in --break, the 2x3 AUC table.
    """
    step = {"baseline": "P1", "change": "P2", "break": "P3"}[mode]
    labkit.result(f"{step}.auc", auc, unit="auc")
    if versus is not None:
        labkit.result(f"{step}.auc_delta", auc - versus, unit="auc")
    if importances is not None:
        share = (importances / importances.sum()).sort_values(ascending=False)
        labkit.result(f"{mode}.top3", ",".join(share.index[:3]))
        labkit.result(f"{mode}.top1_share", share.iloc[0], unit="fraction")
    if table is not None:
        for row in table.index:
            for col in table.columns:
                labkit.result(f"break.auc_{col}_{row}", table.loc[row, col], unit="auc")
        if not labkit.smoke():
            faked = table - table.loc["asof", "time"]
            print("test AUC, terminal input x split:", table.round(3).to_string(),
                  "AUC faked, against the as-of input on the time split:", faked.round(3).to_string(), sep="\n")


def time_masks(tx, smoke):
    train_before, test_from = TIME_SPLIT["smoke" if smoke else "full"]
    return (tx["day"] < train_before).to_numpy(), (tx["day"] >= test_from).to_numpy()


def random_masks(tx, seed):
    test = np.random.default_rng(seed).permutation(len(tx)) < len(tx) // 5  # exactly 20% of rows
    return ~test, test


def fit_auc(X, y, masks, seed):
    """Train the lab's LightGBM on the train rows; return the test AUC, the gain importance and the test scores."""
    train, test = masks
    model = lgb.LGBMClassifier(n_estimators=20 if labkit.smoke() else 200, learning_rate=0.05,
                               min_child_samples=200, subsample=0.8, subsample_freq=1, colsample_bytree=0.8,
                               random_state=seed, n_jobs=4, verbose=-1).fit(X[train], y[train])
    scores = model.predict_proba(X[test])[:, 1]
    return roc_auc_score(y[test], scores), pd.Series(model.booster_.feature_importance("gain"), index=X.columns), scores


def by_scenario(mode, tx, test, scores):
    """Reference-only diagnostics: each fraud scenario's test frauds ranked against every legitimate test row."""
    scenario, legit = tx["scenario"].to_numpy()[test], scores[tx["is_fraud"].to_numpy()[test] == 0]
    for k in sorted(set(scenario[scenario > 0])):
        frauds = scores[scenario == k]
        auc = roc_auc_score(np.r_[np.zeros(len(legit)), np.ones(len(frauds))], np.r_[legit, frauds])
        labkit.result(f"{mode}.auc_s{k}", auc, unit="auc", n=len(frauds))


def known_before(events, labels):
    """For each event, the labels at its terminal that arrived strictly before its time t (rebuild 19)."""
    labels = labels.sort_values("label_available_at", kind="stable")
    labels = labels.assign(known=labels.groupby("terminal_id").cumcount() + 1)
    order = events.assign(row=np.arange(len(events))).sort_values("t", kind="stable")
    joined = pd.merge_asof(order, labels[["terminal_id", "label_available_at", "known"]], left_on="t",
                           right_on="label_available_at", by="terminal_id", allow_exact_matches=False)
    matched = joined["label_available_at"].notna()
    snapshot, event = joined.loc[matched, "label_available_at"], joined.loc[matched, "t"]
    assert (snapshot < event).all(), "a joined label arrived at or after its event"
    out = np.zeros(len(events), dtype=np.int64)
    out[joined["row"].to_numpy()] = joined["known"].fillna(0).to_numpy(dtype=np.int64)
    return out


def terminal_inputs(tx):
    """The three terminal inputs of the --break table, one column each, on the index of tx."""
    labels = tx.loc[tx["is_fraud"] == 1, ["terminal_id", "label_available_at"]]
    now = tx[["terminal_id"]].assign(t=tx["tx_datetime"])
    month_ago = tx[["terminal_id"]].assign(t=tx["tx_datetime"] - np.timedelta64(30, "D"))
    by_terminal = tx.groupby("terminal_id")["is_fraud"]
    total, count = by_terminal.transform("sum"), by_terminal.transform("count")
    return pd.DataFrame({"terminal_known_30d": known_before(now, labels) - known_before(month_ago, labels),
                         "terminal_rate_others": (total - tx["is_fraud"]) / (count - 1),
                         "terminal_fraud_rate": total / count}, index=tx.index)


if __name__ == "__main__":
    args = labkit.start(lab=19, device="cpu")
    if args.mode == "download":
        sys.exit(download())
    smoke = labkit.smoke()  # smoke runs all three paths on the 60-day stream
    tx = load_data(smoke)
    X, y = features_v0.build_features(tx), tx["is_fraud"].to_numpy()
    print(f"DATA rows={len(tx)} frauds={int(y.sum())} days={tx['day'].max() + 1}", flush=True)
    if args.mode in ("baseline", "smoke"):
        masks = time_masks(tx, smoke)
        p1, gain, scores = fit_auc(X, y, masks, args.seed)
        report("baseline", p1, importances=gain)
        by_scenario("baseline", tx, masks[1], scores)
    if args.mode in ("change", "smoke"):
        masks = random_masks(tx, args.seed)
        p2, _, scores = fit_auc(X, y, masks, args.seed)
        report("change", p2, versus=p1 if smoke else labkit.prior("P1.auc"))
        by_scenario("change", tx, masks[1], scores)
    if args.mode in ("break", "smoke"):
        inputs, others = terminal_inputs(tx), X[OTHER_INPUTS]
        table = pd.DataFrame(index=list(TERMINAL_INPUTS), columns=["time", "random"], dtype=float)
        for split, masks in (("time", time_masks(tx, smoke)), ("random", random_masks(tx, args.seed))):
            for row, column in TERMINAL_INPUTS.items():
                inputs_v = others.assign(**{column: inputs[column]})
                table.loc[row, split], gain, scores = fit_auc(inputs_v, y, masks, args.seed)
                if (row, split) == ("asof", "time"):
                    honest = gain, masks[1], scores
        report("break", table.loc["asof", "time"], importances=honest[0], table=table)
        by_scenario("break", tx, honest[1], honest[2])
