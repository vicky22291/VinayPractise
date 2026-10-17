"""22. Calibration and decline thresholds: downsampling moves the probability scale.
Scores and declines of a model trained on 10% of the legitimate rows, the prior correction, amount pricing.

Modes: --download, --smoke, --baseline (P1), --change (P2), --break (P3), --amount.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "labkit.py").exists())))
import labkit  # before numpy: it sets cache defaults
import joblib
import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.base import clone
from sklearn.calibration import calibration_curve
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

FEATURES = [f"V{i}" for i in range(1, 29)] + ["Amount"]  # OpenML keeps Time as a row id, not a feature
PARQUET = "https://data.openml.org/datasets/0000/1597/dataset_1597.pq"
KEEP_RATE = 0.10      # change: every training fraud plus this share of the legitimate training rows
DECLINE_RATE = 0.002  # the champion's threshold declines this share of its own training payments
FLAT_AMOUNT = 200.0   # amount: the flat threshold is the cost threshold of one $200 payment
LR = make_pipeline(StandardScaler(), LogisticRegression(max_iter=5000))  # clone(LR) gives an unfitted copy
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
    return keep_rate * p_sample / (keep_rate * p_sample - p_sample + 1)


def downsample(idx, y, keep_rate, rng):
    """Every fraud in idx plus a random keep_rate share of its legitimate rows."""
    legit = idx[y[idx] == 0]
    return np.concatenate([idx[y[idx] == 1], rng.choice(legit, size=round(keep_rate * len(legit)), replace=False)])


def declines(y, p, threshold):
    """Decline rate, false declines and frauds caught when every score above threshold is declined."""
    d = p > threshold
    return float(d.mean()), int((d & (y == 0)).sum()), int((d & (y == 1)).sum())


def cost_threshold(a):
    """Decline when p > C_fd / (C_fd + L), with L(a) = a + $15 and C_fd(a) = 0.13 a + $8."""
    return (0.13 * a + 8) / (0.13 * a + 8 + a + 15)


def net_dollars(y, a, declined):
    """Fraud losses avoided minus false-decline costs, against approving every payment."""
    return float(((a + 15) * (declined & (y == 1))).sum() - ((0.13 * a + 8) * (declined & (y == 0))).sum())


args = labkit.start(lab=22, device="cpu", extra_modes=("amount",))
if args.mode == "download":
    sys.exit(download())
X, y, amount = load_data(smoke=labkit.smoke())
tr, te = train_test_split(np.arange(len(y)), test_size=0.2, stratify=y, random_state=args.seed)
y_te, a_te = y[te], amount[te]
for mode in ("baseline", "change", "break", "amount") if labkit.smoke() else (args.mode,):
    if mode != "change":
        champion = clone(LR).fit(X[tr], y[tr])
        p_full = champion.predict_proba(X[te])[:, 1]
        threshold = float(np.quantile(champion.predict_proba(X[tr])[:, 1], 1 - DECLINE_RATE))
    if mode in ("change", "break"):
        ds = downsample(tr, y, KEEP_RATE, np.random.default_rng(args.seed))
        p_down = clone(LR).fit(X[ds], y[ds]).predict_proba(X[te])[:, 1]
        p_corr = correct_for_downsampling(p_down, KEEP_RATE)
    if mode == "baseline":
        challenger = LGBMClassifier(n_estimators=100, random_state=0, verbose=-1).fit(X[tr], y[tr])
        if args.seed == 0 and not labkit.smoke():
            save_for_lab24(champion, challenger, te)
        rate, fd, caught = declines(y_te, p_full, threshold)
        report(mode, {"P1.mean_p": p_full.mean(), "baseline.mean_p_legit": p_full[y_te == 0].mean(),
                      "baseline.fraud_rate": y_te.mean(), "baseline.threshold": threshold,
                      "baseline.decline_rate": rate, "baseline.false_declines": fd, "baseline.frauds_caught": caught,
                      "baseline.brier": brier_score_loss(y_te, p_full)}, tables={"full": (y_te, p_full)})
    elif mode == "change":
        report(mode, {"P2.mean_p": p_down.mean(), "change.mean_p_legit": p_down[y_te == 0].mean(),
                      "change.mean_p_corrected": p_corr.mean(), "change.brier": brier_score_loss(y_te, p_down),
                      "change.brier_corrected": brier_score_loss(y_te, p_corr)},
               tables={"downsampled": (y_te, p_down), "corrected": (y_te, p_corr)})
    elif mode == "break":
        raw, corr = declines(y_te, p_down, threshold), declines(y_te, p_corr, threshold)
        new = (p_down > threshold) & (p_full <= threshold) & (y_te == 0)  # legitimate, declined by the new model only
        report(mode, {"P3.decline_rate": raw[0], "P3.false_declines": raw[1], "break.frauds_caught": raw[2],
                      "break.decline_rate_corrected": corr[0], "break.false_declines_corrected": corr[1],
                      "break.frauds_caught_corrected": corr[2], "break.new_fd_gap": np.median(threshold / p_full[new]),
                      "break.new_fd_lift": np.median(p_down[new] / p_full[new])})
    else:
        flat, aware = p_full > cost_threshold(FLAT_AMOUNT), p_full > cost_threshold(a_te)
        net_flat, net_aware = net_dollars(y_te, a_te, flat), net_dollars(y_te, a_te, aware)
        report(mode, {"amount.net_flat": net_flat, "amount.net_aware": net_aware,
                      "amount.net_gain": net_aware - net_flat, "amount.declines_flat": int(flat.sum()),
                      "amount.declines_aware": int(aware.sum()), "amount.changed": int((flat != aware).sum()),
                      "amount.changed_frauds": int(((flat != aware) & (y_te == 1)).sum())})
