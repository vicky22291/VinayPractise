"""features_v0: the fraud model's inputs as they ship today.

build_features(tx) takes the paystream transactions and returns one row of inputs per
transaction, on the same index as tx, with the columns in FEATURES order.
"""
import pandas as pd

WINDOWS = (1, 7, 30)  # days
FEATURES = (["amount", "hour"]
            + [f"cust_{stat}_{days}d" for days in WINDOWS for stat in ("count", "mean")]
            + ["amount_over_30d_mean", "terminal_fraud_rate"])


def customer_window(tx, days):
    """For each transaction: its customer's transactions in the `days` days before it, as count and mean amount."""
    ordered = tx.sort_values(["customer_id", "tx_datetime"], kind="stable")
    window = (ordered.set_index("tx_datetime").groupby("customer_id")["amount"]
              .rolling(f"{days}D", closed="left").agg(["count", "mean"]))
    return window.set_axis(ordered.index).reindex(tx.index)


def build_features(tx):
    """The model inputs, one row per transaction, in FEATURES order."""
    out = pd.DataFrame({"amount": tx["amount"], "hour": tx["tx_datetime"].dt.hour}, index=tx.index)
    for days in WINDOWS:
        window = customer_window(tx, days)
        out[f"cust_count_{days}d"] = window["count"].fillna(0)
        out[f"cust_mean_{days}d"] = window["mean"]
    out["amount_over_30d_mean"] = tx["amount"] / out["cust_mean_30d"]
    out["terminal_fraud_rate"] = tx.groupby("terminal_id")["is_fraud"].transform("mean")
    return out[FEATURES]
