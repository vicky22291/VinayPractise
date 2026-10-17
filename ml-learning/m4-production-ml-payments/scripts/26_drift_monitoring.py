"""26. Drift: two-sample tests, PSI and a domain classifier. Flag drift between two months of NYC
taxi trips three ways, count false alarms on a no-shift control, and tie a shift to a forecaster's MAE.

Modes: --download, --smoke, --baseline (P1), --change (P2), --break (P3).
This starter loads the data and owns the RESULT contract. You write the monitoring spec in the lab
file and psi() below; the AI writes the harness (the tests, the classifier, the forecaster, the modes).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "labkit.py").exists())))
import labkit  # before numpy: it sets cache defaults
import numpy as np
import pandas as pd

TLC = labkit.DATA / "tlc"
SIZES = {"2024-01": 49_961_641, "2024-07": 52_299_432}  # bytes of each monthly yellow-taxi file
FEATURES = ["trip_distance", "fare_amount", "tip_amount", "total_amount", "passenger_count",
            "payment_type", "PULocationID", "DOLocationID", "duration_min", "hour"]  # no datetime column
KS_P, PSI_LINE = 0.05, 0.2  # a feature is flagged at KS p below KS_P, or at PSI above PSI_LINE
CONTRACT = {  # mode: "RESULT name:unit" items in print order; P1, P2 and P3 mark what a prediction asks
    "baseline": "P1.domain_auc:auc baseline.ks_flagged:of_10 baseline.psi_flagged:of_10 baseline.max_ks_stat:fraction "
                "baseline.max_psi:psi baseline.mae_jan_w4:pickups baseline.mae_jul_w2:pickups baseline.pred_psi:psi",
    "change": "P2.domain_auc:auc P2.psi_flagged:of_10 change.ks_flagged:of_10 change.max_ks_stat:fraction "
              "change.max_psi:psi",
    "break": "P3.ks_flagged:of_10 break.psi_flagged:of_10 break.domain_auc:auc break.max_ks_stat:fraction "
             "break.max_psi:psi break.n_week1:trips break.n_week2:trips",
}


def download():
    """Fetch the January and July 2024 yellow-taxi trip files (January is shared with labs 16 and 20)."""
    for month, size in SIZES.items():
        labkit.fetch(f"https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_{month}.parquet",
                     TLC / f"yellow_tripdata_{month}.parquet", size=size)


def load_data(month):
    """Every trip picked up inside the month ("2024-01" or "2024-07"): the pickup time plus FEATURES,
    where duration_min is dropoff minus pickup in minutes and hour is the pickup hour, 0 to 23."""
    raw = ["tpep_pickup_datetime", "tpep_dropoff_datetime", *FEATURES[:8]]  # the last two are derived
    df = pd.read_parquet(TLC / f"yellow_tripdata_{month}.parquet", columns=raw)
    start = pd.Timestamp(f"{month}-01")
    df = df[(df.tpep_pickup_datetime >= start) & (df.tpep_pickup_datetime < start + pd.offsets.MonthBegin())]
    df = df.assign(pickup=df.tpep_pickup_datetime.astype("datetime64[ns]"), hour=df.tpep_pickup_datetime.dt.hour,
                   duration_min=(df.tpep_dropoff_datetime - df.tpep_pickup_datetime).dt.total_seconds() / 60)
    return df[["pickup", *FEATURES]].reset_index(drop=True)


def report(mode, table, **values):
    """Print one mode's RESULT lines in CONTRACT order, then one TABLE line per feature. table: one
    row per feature (feature, ks_stat, ks_p, psi), reference sample first. values: domain_auc, plus
    mae_jan_w4, mae_jul_w2 and pred_psi in --baseline, and n_week1 and n_week2 in --break."""
    values.update(ks_flagged=int((table.ks_p < KS_P).sum()), psi_flagged=int((table.psi > PSI_LINE).sum()),
                  max_ks_stat=table.ks_stat.max(), max_psi=table.psi.max())
    short = {n.split(".")[1]: (n, u) for n, u in (item.split(":") for item in CONTRACT[mode].split())}
    assert set(values) == set(short), f"{mode}: names differ from CONTRACT: {sorted(set(values) ^ set(short))}"
    for key, (name, unit) in short.items():
        labkit.result(name, values[key], unit=unit)
    rows = [f"TABLE {mode} {r.feature:<15} ks_stat={r.ks_stat:.6f} ks_p={r.ks_p:.3g} psi={r.psi:.6f}"
            for r in table.itertuples()]
    print(f"SMOKE table.{mode} ok" if labkit.smoke() else "\n".join(rows), flush=True)


def psi(expected, actual, bins=10):
    """Population stability index of actual against expected, the reference sample (formula in the lab file)."""
    raise NotImplementedError("TODO(human): write this from the formula in the lab file")


# The harness goes here (see the lab file). You write psi() above; the AI writes the KS and PSI
# loop over FEATURES, the domain classifier, the forecaster and the three modes from your prompt.


if __name__ == "__main__":
    args = labkit.start(lab=26, device="cpu")
    if args.mode == "download":
        download()
    elif args.mode == "smoke":  # smoke checks the plumbing only: both months load, every CONTRACT name prints
        months = {month: load_data(month) for month in SIZES}
        nan = float("nan")
        placeholder = pd.DataFrame({"feature": FEATURES, "ks_stat": nan, "ks_p": nan, "psi": nan})
        extras = {"baseline": ("mae_jan_w4", "mae_jul_w2", "pred_psi"), "change": (), "break": ("n_week1", "n_week2")}
        for mode in CONTRACT:
            report(mode, placeholder, domain_auc=nan, **dict.fromkeys(extras[mode], nan))
    else:
        raise NotImplementedError("write the harness: see the lab file")
