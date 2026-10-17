"""19. Time split and as-of features. One LightGBM on the inputs features_v0.py ships, scored on a time split and a random split.

The data is synthetic: scripts/paystream.py generates it.

Modes: --download, --smoke, --baseline (P1), --change (P2), --break (P3).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "labkit.py").exists())))
import labkit  # before numpy and pandas: it sets cache defaults
import numpy as np
import pandas as pd

import features_v0
import paystream


def download():
    """No file to fetch: paystream.py generates the synthetic stream once and caches it."""
    path = paystream.write("v1")
    print(f"HAVE {path} {path.stat().st_size / 1e6:.1f} MB", flush=True)


def load_data(smoke=False):
    """The synthetic paystream transactions (seed 0) by tx_datetime, plus day (0 is 2018-04-01). Smoke: 60 days."""
    tx = paystream.load(smoke=smoke)
    tx["day"] = (tx["tx_datetime"] - paystream.START).dt.days
    return tx


def report(mode, auc, importances=None, versus=None):
    """Print the RESULT lines for one mode: the contract the lab file names.

    auc: this mode's test AUC. importances: in --baseline, LightGBM's gain importance as a pandas
    Series indexed by feature name. versus: in --change, the --baseline AUC, so the mode also
    prints the difference.
    """
    step = {"baseline": "P1", "change": "P2"}[mode]
    labkit.result(f"{step}.auc", auc, unit="auc")
    if versus is not None:
        labkit.result(f"{step}.auc_delta", auc - versus, unit="auc")
    if importances is not None:
        share = (importances / importances.sum()).sort_values(ascending=False)
        labkit.result(f"{mode}.top3", ",".join(share.index[:3]))
        labkit.result(f"{mode}.top1_share", share.iloc[0], unit="fraction")


# The harness goes here (see the lab file). The AI writes it from your prompt: the inputs from
# features_v0.build_features(), the two splits, LightGBM, the test AUC and the two modes.


if __name__ == "__main__":
    args = labkit.start(lab=19, device="cpu")
    if args.mode == "download":
        download()
    elif args.mode == "smoke":  # smoke checks the plumbing only: load_data(), build_features(), report()
        tx = load_data(smoke=True)
        X = features_v0.build_features(tx)
        report("baseline", 0.5, importances=pd.Series(1.0, index=X.columns))
        report("change", 0.5, versus=0.5)
    elif args.mode == "break":
        print("--break runs from the reference: after your fix, ask the AI to run it, or ask for 'debrief 19'.")
    else:
        raise NotImplementedError("write the harness: see the lab file")
