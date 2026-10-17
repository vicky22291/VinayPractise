"""26. Drift: two-sample tests, PSI and a domain classifier. Flag drift between two months of NYC
taxi trips three ways, count false alarms on a no-shift control, and tie a shift to a forecaster's MAE.

Modes: --download, --smoke, --baseline (P1), --change (P2), --break (P3).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "labkit.py").exists())))
import labkit  # before numpy: it sets cache defaults
import lightgbm as lgb
import numpy as np
import pandas as pd
from scipy.stats import ks_2samp
from sklearn.metrics import mean_absolute_error, roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict

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
LAGS, FX = (1, 24, 168), ["lag_1", "lag_24", "lag_168", "hour_of_week"]  # the forecaster's inputs, as in lab 16


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
    """Population stability index of actual against expected, the reference sample."""
    inner = np.unique(np.quantile(expected, np.linspace(0, 1, bins + 1)[1:-1]))  # reference deciles
    e = np.bincount(np.searchsorted(inner, expected, side="right"), minlength=len(inner) + 1) / len(expected)
    a = np.bincount(np.searchsorted(inner, actual, side="right"), minlength=len(inner) + 1) / len(actual)
    e, a = np.maximum(e, 1e-4), np.maximum(a, 1e-4)  # an empty bin would make ln(a / e) infinite
    return float(np.sum((a - e) * np.log(a / e)))


def domain_auc(old, new, seed):
    """Out-of-fold AUC of LightGBM (100 trees) telling new rows from old ones on FEATURES, 5 folds."""
    X = pd.concat([old[FEATURES], new[FEATURES]], ignore_index=True)
    y = np.r_[np.zeros(len(old)), np.ones(len(new))]
    model = lgb.LGBMClassifier(n_estimators=100, random_state=seed, verbose=-1)
    p = cross_val_predict(model, X, y, cv=StratifiedKFold(5, shuffle=True, random_state=seed), method="predict_proba")
    return roc_auc_score(y, p[:, 1])


def compare(old, new, seed):
    """KS test and PSI per feature (old is the reference, missing values dropped), and the domain AUC."""
    rows = []
    for f in FEATURES:
        a, b = old[f].dropna().to_numpy(float), new[f].dropna().to_numpy(float)
        rows.append((f, *ks_2samp(a, b)[:2], psi(a, b)))  # the KS statistic and p-value, then PSI
    return pd.DataFrame(rows, columns=["feature", "ks_stat", "ks_p", "psi"]), domain_auc(old, new, seed)


def zone_hours(trips, zones, month):
    """Pickups per zone and hour on the full zone x hour grid of the month (an hour with no pickup
    is a 0 row), so shift(k) inside a zone is exactly k hours back; plus hour_of_week."""
    hours = pd.date_range(f"{month}-01", periods=31 * 24, freq="h")  # January and July have 31 days
    t = trips[trips.PULocationID.isin(zones)]
    counts = t.groupby([t.PULocationID.rename("zone"), t.pickup.dt.floor("h").rename("hour")]).size()
    grid = pd.MultiIndex.from_product([zones, hours], names=["zone", "hour"])
    table = counts.reindex(grid, fill_value=0).rename("pickups").reset_index()
    assert table.pickups.sum() == len(t), "every pickup must land on the grid"
    for k in LAGS:
        table[f"lag_{k}"] = table.groupby("zone").pickups.shift(k)
    table["hour_of_week"] = table.hour.dt.dayofweek * 24 + table.hour.dt.hour
    return table


def forecast(jan, jul, seed):
    """Lab 16's honest forecaster (LightGBM, 500 trees, L1 loss) trained on January weeks 1 to 3,
    scored on January week 4 and July week 2: both MAEs and the PSI of July's predictions."""
    per_day = jan.groupby("PULocationID").size() / 31
    zones = per_day.index[per_day >= 100][:3 if labkit.smoke() else None]  # 100+ pickups a day in January
    jt, st = zone_hours(jan, zones, "2024-01"), zone_hours(jul, zones, "2024-07")
    train = jt[jt.hour < "2024-01-22"].dropna(subset=FX)  # weeks 1 to 3; week 1 only feeds the lags
    w4 = jt[(jt.hour >= "2024-01-22") & (jt.hour < "2024-01-29")]
    w2 = st[(st.hour >= "2024-07-08") & (st.hour < "2024-07-15")]
    model = lgb.LGBMRegressor(n_estimators=20 if labkit.smoke() else 500, objective="l1",
                              random_state=seed, verbose=-1).fit(train[FX], train.pickups)
    p4, p2 = model.predict(w4[FX]), model.predict(w2[FX])
    return {"mae_jan_w4": mean_absolute_error(w4.pickups, p4), "mae_jul_w2": mean_absolute_error(w2.pickups, p2),
            "pred_psi": psi(p4, p2)}


def main():
    args = labkit.start(lab=26, device="cpu")
    if args.mode == "download":
        return download()
    n = 5_000 if labkit.smoke() else 200_000  # trips per sample in --baseline and --change
    modes = ("baseline", "change", "break") if labkit.smoke() else (args.mode,)
    jan = load_data("2024-01")
    if "baseline" in modes:  # P1: January, the reference, against July
        jul = load_data("2024-07")
        table, auc = compare(jan.sample(n, random_state=args.seed), jul.sample(n, random_state=args.seed), args.seed)
        report("baseline", table, domain_auc=auc, **forecast(jan, jul, args.seed))
    if "change" in modes:  # P2: two random halves of January, a no-shift control
        both = jan.sample(2 * n, random_state=args.seed)
        table, auc = compare(both.iloc[:n], both.iloc[n:], args.seed)
        report("change", table, domain_auc=auc)
    if "break" in modes:  # P3: every trip of January week 1 (1 to 7) against week 2 (8 to 14)
        w1 = jan[jan.pickup < "2024-01-08"]
        w2 = jan[(jan.pickup >= "2024-01-08") & (jan.pickup < "2024-01-15")]
        w1, w2 = (w1.sample(n, random_state=0), w2.sample(n, random_state=0)) if labkit.smoke() else (w1, w2)
        table, auc = compare(w1, w2, args.seed)
        report("break", table, domain_auc=auc, n_week1=len(w1), n_week2=len(w2))


if __name__ == "__main__":
    main()
