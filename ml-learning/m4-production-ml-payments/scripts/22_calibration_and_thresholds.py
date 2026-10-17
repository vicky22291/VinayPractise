"""22. Calibration and decline thresholds: what downsampling does to probabilities.
Scores and declines of a model trained on 10% of the legitimate rows, the prior correction, amount pricing.

Modes: --download, --smoke, --baseline (P1), --change (P2), --break (P3), --amount.
This starter loads the data and owns the RESULT contract. You specify the harness in the lab file and
the AI writes it below; you write correct_for_downsampling() yourself.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "labkit.py").exists())))
import labkit  # before numpy: it sets cache defaults
import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import calibration_curve

FEATURES = [f"V{i}" for i in range(1, 29)] + ["Amount"]  # OpenML keeps Time as a row id, not a feature
PARQUET = "https://data.openml.org/datasets/0000/1597/dataset_1597.pq"
KEEP_RATE = 0.10      # change: every training fraud plus this share of the legitimate training rows
DECLINE_RATE = 0.002  # the champion's threshold declines this share of its own training payments
FLAT_AMOUNT = 200.0   # amount: the flat threshold is the cost threshold of one $200 payment
CONTRACT = {  # mode: "RESULT name:unit" items, printed in this order
    "baseline": "P1.mean_p:fraction baseline.mean_p_legit:fraction baseline.fraud_rate:fraction "
                "baseline.threshold:probability baseline.decline_rate:fraction baseline.false_declines:count "
                "baseline.frauds_caught:count baseline.brier:brier",
    "change": "P2.mean_p:fraction change.mean_p_legit:fraction change.mean_p_corrected:fraction "
              "change.brier:brier change.brier_corrected:brier",
    "break": "P3.decline_rate:fraction P3.false_declines:count break.frauds_caught:count "
             "break.decline_rate_corrected:fraction break.false_declines_corrected:count "
             "break.frauds_caught_corrected:count break.new_fd_gap:ratio break.new_fd_lift:ratio",
    "amount": "amount.net_flat:dollars amount.net_aware:dollars amount.net_gain:dollars amount.declines_flat:count "
              "amount.declines_aware:count amount.changed:count amount.changed_frauds:count",
}


def download():
    """Fetch OpenML 1597 once into the scikit-learn cache; if OpenML fails, fetch its parquet copy."""
    try:
        labkit.openml(1597)
        for f in sorted((labkit.DATA / "openml").rglob("creditcard*")):
            print(f"HAVE {f} {f.stat().st_size / 1e6:.1f} MB", flush=True)
    except Exception as e:
        print(f"RETRY parquet fallback ({type(e).__name__})", flush=True)
        labkit.fetch(PARQUET, labkit.DATA / "creditcard" / "dataset_1597.pq", size=73_231_184)


def load_data(smoke=False):
    """(X, y, amount): the FEATURES columns, the 0/1 fraud label and the amount; smoke keeps 30,000 rows."""
    pq = labkit.DATA / "creditcard" / "dataset_1597.pq"  # there only when --download needed the fallback
    df = pd.read_parquet(pq) if pq.exists() else labkit.openml(1597)
    df = df.sample(30_000, random_state=0) if smoke else df
    y = pd.to_numeric(df["Class"].astype(str)).astype(int).to_numpy()
    return df[FEATURES].to_numpy(dtype=np.float64), y, df["Amount"].to_numpy(dtype=np.float64)


def report(mode, values, tables=None):
    """Print a mode's RESULT lines in CONTRACT order, then a 10-bin reliability table per {label: (y, p)}."""
    names = dict(item.split(":") for item in CONTRACT[mode].split())
    assert set(values) == set(names), f"{mode}: RESULT names differ from CONTRACT: {sorted(set(values) ^ set(names))}"
    for name, unit in names.items():
        labkit.result(name, values[name], unit=unit)
    for label, (y, p) in (tables or {}).items():
        observed, mean_p = calibration_curve(y, p, n_bins=10, strategy="quantile")
        rows = [f"TABLE {label} {i:>3} {m:.6f} {o:.6f}" for i, (m, o) in enumerate(zip(mean_p, observed), 1)]
        print(f"SMOKE table.{label} ok" if labkit.smoke() else "\n".join([f"TABLE {label} bin mean_p observed", *rows]))


def save_for_lab24(champion, challenger, test_idx):
    """Write the three files lab 24 reads (seed 0 only): the champion, the challenger, the test row positions."""
    out = labkit.models_dir(22)
    joblib.dump(champion, out / "champion_lr.joblib")
    joblib.dump(challenger, out / "challenger_lgbm.joblib")
    np.save(out / "test_idx.npy", test_idx)
    print(f"SAVED {out}: champion_lr.joblib challenger_lgbm.joblib test_idx.npy", flush=True)


def correct_for_downsampling(p_sample, keep_rate):
    """Map scores of a model trained on keep_rate of the legitimate rows back to the true fraud scale."""
    raise NotImplementedError("TODO(human): write this from the formula in the module README")


args = labkit.start(lab=22, device="cpu", extra_modes=("amount",))
if args.mode == "download":
    sys.exit(download())
if not labkit.smoke():
    raise NotImplementedError("write the harness: see the lab file")
# Smoke checks the plumbing only: the data loads, every RESULT name in CONTRACT prints, a table builds.
X, y, amount = load_data(smoke=True)
for mode, items in CONTRACT.items():
    values = {item.split(":")[0]: float("nan") for item in items.split()}
    report(mode, values, tables={"plumbing": (y, np.linspace(0, 1, len(y)))})
