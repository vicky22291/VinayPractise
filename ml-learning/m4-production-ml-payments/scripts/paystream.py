"""paystream: a seeded, synthetic payments stream for labs 19, 21 and 23 and the Capstone A fallback.

The data is synthetic: no real customer, card, terminal or payment is behind any row. The parameters
follow the transaction data simulator in chapter 3 of the Fraud Detection Handbook (the comments in
generate() give each one): https://fraud-detection-handbook.github.io/fraud-detection-handbook/Chapter_3_GettingStarted/SimulatedDataset.html
The code is written fresh: nothing is copied from the handbook's GPL-3.0 code and no pickle is loaded.
Card testing (scenario 4), the dispute delay and the proxy flag are additions for these labs.

Labs:  import paystream; tx = paystream.load()   (generates the file first if it is missing)
Shell: python scripts/paystream.py --download [--seed 0]   ~/ml-data/paystream/v1/transactions.parquet
       python scripts/paystream.py --smoke                 500 customers, 60 days, ~/ml-data/paystream/smoke/
"""
import sys
from pathlib import Path

sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "labkit.py").exists())))
import labkit  # before numpy: it sets cache defaults
import numpy as np
import pandas as pd

START = pd.Timestamp("2018-04-01")
DAYS = 183
COLUMNS = ["tx_id", "tx_datetime", "customer_id", "terminal_id", "amount", "is_fraud",
           "scenario", "label_available_at", "proxy_flag", "proxy_at"]
SIZES = {"v1": dict(customers=5000, terminals=10000, days=DAYS),
         "smoke": dict(customers=500, terminals=10000, days=60)}
DAY = 86400  # seconds


def generate(seed=0, customers=5000, terminals=10000, days=DAYS):
    """One synthetic stream as a DataFrame with COLUMNS, sorted by tx_datetime."""
    rng = np.random.default_rng(seed)
    home = rng.uniform(0, 100, (customers, 2))  # customer (x, y) on a 100 x 100 square
    mean_amount = rng.uniform(5, 100, customers)  # amounts are N(mean, mean / 2)
    per_day = rng.uniform(0, 4, customers)  # payments a day are Poisson(per_day)
    spot = rng.uniform(0, 100, (terminals, 2))  # terminal (x, y)
    near = [np.flatnonzero(((spot - xy) ** 2).sum(1) < 5 ** 2) for xy in home]  # within distance 5
    n_near = np.array([len(t) for t in near])
    flat, first = np.concatenate(near), np.cumsum(n_near) - n_near  # all lists end to end, and each start

    def terminal_for(cust):  # one of each customer's nearby terminals, uniformly
        return flat[first[cust] + rng.integers(0, n_near[cust])]

    # Legitimate payments. A customer with no terminal nearby never pays. The time of day is
    # N(noon, 20,000 s), out-of-day draws dropped; a negative amount is redrawn from U(0, 2 x mean).
    counts = rng.poisson(per_day[:, None], (customers, days)) * (n_near > 0)[:, None]
    cell = np.repeat(np.arange(customers * days), counts.ravel())  # one (customer, day) cell per payment
    secs = rng.normal(DAY / 2, 20000, len(cell))
    keep = (secs >= 0) & (secs < DAY)
    cust, day, secs = cell[keep] // days, cell[keep] % days, secs[keep].astype(np.int64)
    amount = rng.normal(mean_amount[cust], mean_amount[cust] / 2)
    amount = np.round(np.where(amount < 0, rng.uniform(0, 2 * mean_amount[cust]), amount), 2)
    term = terminal_for(cust)

    # Scenario 1: amount over 220. 2: each day 2 terminals are compromised for 28 days, all their payments.
    # 3: each day 3 customers are compromised for 14 days, a third of their payments, at 5 x the amount.
    scenario = np.where(amount > 220, 1, 0)
    hot_term, hot_cust = np.zeros((terminals, days), bool), np.zeros((customers, days), bool)
    for d in range(days):
        hot_term[rng.choice(terminals, 2, replace=False), d:d + 28] = True
        hot_cust[rng.choice(customers, 3, replace=False), d:d + 14] = True
    scenario[(scenario == 0) & hot_term[term, day]] = 2  # a payment keeps its first scenario
    s3 = (scenario == 0) & hot_cust[cust, day] & (rng.random(len(cust)) < 1 / 3)
    amount[s3], scenario[s3] = amount[s3] * 5, 3

    # Scenario 4, card testing: in the last 23 days (from day 160 of 183), 20 customers a day
    # get 5 extra payments of U(0.5, 3) within one hour, at their nearby terminals.
    test_days = np.arange(max(days - 23, 0), days)
    victims = np.concatenate([rng.choice(np.flatnonzero(n_near > 0), 20, replace=False) for _ in test_days])
    c4, d4 = np.repeat(victims, 5), np.repeat(test_days, 20 * 5)
    s4 = np.repeat(rng.integers(0, DAY - 3600, len(victims)), 5) + rng.integers(0, 3600, len(c4))
    t4, a4 = terminal_for(c4), rng.uniform(0.5, 3, len(c4))

    df = pd.DataFrame({
        "tx_datetime": START + pd.to_timedelta(np.concatenate([day * DAY + secs, d4 * DAY + s4]), unit="s"),
        "customer_id": np.concatenate([cust, c4]), "terminal_id": np.concatenate([term, t4]),
        "amount": np.round(np.concatenate([amount, a4]), 2),
        "scenario": np.concatenate([scenario, np.full(len(c4), 4)]),
    }).sort_values("tx_datetime", kind="stable", ignore_index=True)
    n, fraud = len(df), df.scenario.to_numpy() > 0

    def later(lo, hi, mask):  # tx_datetime plus U(lo, hi) days in whole seconds; NaT where mask is False
        delay = np.round(rng.uniform(lo, hi, n) * DAY)
        return df.tx_datetime + pd.to_timedelta(np.where(mask, delay, np.nan), unit="s")

    # The dispute (the label) lands 7 to 120 days after a fraud. The proxy flag, an early warning,
    # lands 1 to 7 days after, with recall 0.5 and precision 0.4 (1.5 false flags per true one).
    flag = fraud & (rng.random(n) < 0.5)
    flag |= ~fraud & (rng.random(n) < 1.5 * flag.sum() / (~fraud).sum())
    df["tx_id"] = np.arange(n)
    df["is_fraud"] = fraud.astype(np.int64)
    df["label_available_at"] = later(7, 120, fraud)
    df["proxy_flag"] = flag
    df["proxy_at"] = later(1, 7, flag)
    return df[COLUMNS]


def write(version="v1", seed=0, force=False):
    """Generate one version to its parquet file unless it is there (locked, atomic); return the path."""
    out = labkit.DATA / "paystream" / version / "transactions.parquet"
    with labkit.locked(out):
        if force or not out.exists():
            generate(seed, **SIZES[version]).to_parquet(out.with_suffix(".part"), index=False)
            out.with_suffix(".part").replace(out)
            print(f"WROTE {out} {out.stat().st_size / 1e6:.1f} MB", flush=True)
    return out


def load(smoke=False):
    """The stream (seed 0) as a DataFrame; generates the file first if it is missing."""
    return pd.read_parquet(write("smoke" if smoke else "v1"))


if __name__ == "__main__":
    args = labkit.start(lab=19, description="Write the synthetic payments stream under ML_DATA/paystream/.")
    if args.mode not in ("download", "smoke"):
        sys.exit(f"paystream.py only writes data: use --download or --smoke (--{args.mode} is a lab script mode)")
    out = write("smoke" if args.smoke else "v1", args.seed, force=args.smoke)
    df = pd.read_parquet(out)
    frauds = df.scenario[df.is_fraud == 1].value_counts().sort_index()
    print(f"PAYSTREAM {out} rows={len(df)} days={(df.tx_datetime.max() - START).days + 1} "
          f"fraud_share={df.is_fraud.mean():.2%} " + " ".join(f"scenario{k}={v}" for k, v in frauds.items()))
