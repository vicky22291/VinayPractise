"""27. Audit an AI-written fraud pipeline: silent bugs in fluent code. Reference: the shipped path, the fixed path and the --break reveal on next month's traffic.

Modes: --download, --smoke, --baseline (the shipped report), --change (the fixed copy on history, one
run plus a 10-split mean, and P2), --break (P1 and P3 on next month's traffic, the corrected core, and
each single fix against the shipped script, both as 10-split means).

The three planted bugs, all in normal-looking code in scripts/27_audit_an_ai_written_pipeline.py:
  1 'oversampling': frauds drawn 10 times with replacement before train_test_split, so copies of
    one fraud sit in train and test, and the test set carries 10x its real fraud share.
  2 'threshold': the threshold maximizes F1 on the same test rows that report recall and precision.
  3 'scale': legitimate rows thinned to 10% with no correction, so the scores, the threshold and the
    decline rate (base_rate * recall / precision, with precision from those rows) sit on that scale.
The shipped functions below are copied unchanged; variant() applies any set of fixes.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "labkit.py").exists())))
import labkit  # before numpy: it sets cache defaults
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, precision_recall_curve
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

PARQUET = "https://data.openml.org/datasets/0000/1597/dataset_1597.pq"  # copy of OpenML 1597
FEATURES = [f"V{i}" for i in range(1, 29)] + ["Amount"]  # OpenML keeps Time as the row id
HISTORY_SHARE = 0.80    # history: the first 80% of payments by time; next month: the rest
FRAUD_COPIES = 10
LEGIT_SHARE = 0.10
TEST_SIZE = 0.20
DECLINE_BUDGET = 0.002
VAL_SIZE = 0.25         # fixed path: share of the rows that tunes the threshold
B = LEGIT_SHARE / FRAUD_COPIES  # legit rows kept per fraud row, relative to the real mix
FIXES = ("oversampling", "threshold", "scale")
REPEATS = 10            # splits averaged per seed for the fixed copy and for each single fix
UNITS = {"pr_auc": "fraction", "threshold": "probability", "recall": "fraction",
         "precision": "fraction", "decline_rate": "fraction"}


def download():
    """Fetch OpenML 1597 into the scikit-learn cache; if OpenML fails, fetch its parquet copy."""
    try:
        labkit.openml(1597)
        for f in sorted((labkit.DATA / "openml").rglob("creditcard*")):
            print(f"HAVE {f} {f.stat().st_size / 1e6:.1f} MB", flush=True)
    except Exception as e:
        print(f"RETRY parquet fallback ({type(e).__name__})", flush=True)
        labkit.fetch(PARQUET, labkit.DATA / "creditcard" / "dataset_1597.pq", size=73_231_184)


def load_payments(smoke=False):
    """(history, next_month): the shipped script's history and the 20% of later rows it never reads."""
    pq = labkit.DATA / "creditcard" / "dataset_1597.pq"  # present only if --download used the fallback
    df = pd.read_parquet(pq) if pq.exists() else labkit.openml(1597)
    df = df.assign(is_fraud=pd.to_numeric(df["Class"].astype(str)).astype(int))[FEATURES + ["is_fraud"]]
    if smoke:
        df = df.iloc[::5]
    cut = int(len(df) * HISTORY_SHARE)
    return df.iloc[:cut].reset_index(drop=True), df.iloc[cut:].reset_index(drop=True)


# --- shipped, unchanged ---
def rebalance(payments, seed):
    fraud = payments[payments.is_fraud == 1]
    legit = payments[payments.is_fraud == 0]
    fraud = fraud.sample(frac=FRAUD_COPIES, replace=True, random_state=seed)
    legit = legit.sample(frac=LEGIT_SHARE, random_state=seed)
    return pd.concat([fraud, legit]).sample(frac=1, random_state=seed)


def train_model(X, y):
    return make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000)).fit(X, y)


def decline_rate(base_rate, recall, precision):
    return base_rate * recall / np.maximum(precision, 1e-12)


def choose_threshold(y_true, scores, base_rate):
    precision, recall, thresholds = precision_recall_curve(y_true, scores)
    precision, recall = precision[:-1], recall[:-1]
    f1 = 2 * precision * recall / np.maximum(precision + recall, 1e-12)
    allowed = decline_rate(base_rate, recall, precision) <= DECLINE_BUDGET
    return thresholds[np.argmax(np.where(allowed, f1, -1.0))]
# --- end shipped ---


def oversample(rows, seed):
    """Bug 1's step alone: every fraud drawn FRAUD_COPIES times with replacement, legit rows as they are."""
    fraud = rows[rows.is_fraud == 1].sample(frac=FRAUD_COPIES, replace=True, random_state=seed)
    return pd.concat([fraud, rows[rows.is_fraud == 0]])


def downsample(rows, seed):
    """Bug 3's step alone: LEGIT_SHARE of the legitimate rows kept, every fraud kept."""
    legit = rows[rows.is_fraud == 0].sample(frac=LEGIT_SHARE, random_state=seed)
    return pd.concat([rows[rows.is_fraud == 1], legit])


def correct(p, b):
    """Odds correction for resampled training rows (Dal Pozzolo et al. 2015): p' = b p / (b p - p + 1)."""
    return b * p / (b * p - p + 1)


def operating_point(y, scores, threshold, base_rate):
    """The shipped evaluate() report, with the threshold passed in instead of tuned on these rows."""
    declined = scores >= threshold
    recall, precision = declined[y == 1].mean(), y[declined].mean() if declined.any() else 0.0
    return {"pr_auc": average_precision_score(y, scores), "threshold": threshold, "recall": recall,
            "precision": precision, "decline_rate": decline_rate(base_rate, recall, precision)}


def split(rows, share, seed):
    """train_test_split on whole rows, stratified on the label, as the shipped script splits."""
    return train_test_split(rows, test_size=share, stratify=rows.is_fraud, random_state=seed)


def variant(history, seed, fixes=frozenset()):
    """The shipped pipeline with the named fixes applied. No fixes reproduces the shipped run exactly.

    All three fixes is the fixed copy an audit should end with: split the real rows first, tune the
    threshold on untouched training rows, resample the fitting rows only, correct the odds.
    Returns (score, threshold, report): score(rows) gives the model's scores, corrected when 'scale' is fixed.
    """
    base_rate = history.is_fraud.mean()
    fixes = set(fixes)
    clean_split = {"oversampling", "scale"} <= fixes  # nothing resampled before the split
    rows, val = history, None
    if "threshold" in fixes and not clean_split:  # fix 2 alone: untouched rows held out before resampling
        rows, val = split(rows, VAL_SIZE, seed)
    if not clean_split:
        if "oversampling" in fixes:
            rows = downsample(rows, seed)  # bug 3 kept
        elif "scale" in fixes:
            rows = oversample(rows, seed)  # bug 1 kept
        else:
            rows = rebalance(rows, seed)  # bugs 1 and 3, as shipped
    train, test = split(rows, TEST_SIZE, seed)
    if "threshold" in fixes and clean_split:  # the fixed copy: tune on untouched training rows
        train, val = split(train, VAL_SIZE, seed)
    if "oversampling" in fixes:
        train = oversample(train, seed)  # fix 1: copies drawn from training rows only
    if "scale" in fixes:
        train = downsample(train, seed)  # fix 3: thin training rows only, and correct the odds below
    model = train_model(train[FEATURES], train.is_fraud.to_numpy())
    b = B if "scale" in fixes else 1.0
    score = lambda df: correct(model.predict_proba(df[FEATURES])[:, 1], b)  # noqa: E731
    tune = test if val is None else val
    threshold = choose_threshold(tune.is_fraud.to_numpy(), score(tune), base_rate)
    return score, threshold, operating_point(test.is_fraud.to_numpy(), score(test), threshold, base_rate)


def per_split(history, nxt, seed, fixes=frozenset()):
    """variant()'s report plus its next-month decline rate, one row per split, over REPEATS splits.

    An honest 20% test split of history holds about 83 frauds, so a single run is too noisy to size
    a fix. Every variant uses the sub-seeds seed * REPEATS + r, but a variant that resamples before
    its split splits other rows: only decline_rate_next scores every variant on the same rows.
    """
    reports = []
    for r in range(REPEATS):
        score, t, report = variant(history, seed * REPEATS + r, fixes)
        reports.append({**report, "decline_rate_next": float((score(nxt) >= t).mean())})
    return pd.DataFrame(reports)


def leak_facts(history, seed):
    """What the shipped test rows hold: fraud share, unique frauds, and the share of test fraud rows
    whose payment also sits in the training rows (rebalance keeps each payment's index)."""
    train, test = split(rebalance(history, seed), TEST_SIZE, seed)
    fraud = test[test.is_fraud == 1]
    seen = fraud.index.isin(train.index[train.is_fraud == 1]).mean()
    return test.is_fraud.mean(), fraud.index.nunique(), seen


def honest(history, seed):
    """The corrected core: split history by time first, resample the fitting rows only, correct the
    odds, tune the threshold on the latest quarter of history (57 frauds). The rebuild writes the same
    steps with downsampling only. Returns (score, threshold)."""
    base_rate = history.is_fraud.mean()
    cut = int(len(history) * (1 - VAL_SIZE))
    fit, val = history.iloc[:cut], history.iloc[cut:]
    fit = downsample(oversample(fit, seed), seed)
    model = train_model(fit[FEATURES], fit.is_fraud.to_numpy())
    score = lambda df: correct(model.predict_proba(df[FEATURES])[:, 1], B)  # noqa: E731
    return score, choose_threshold(val.is_fraud.to_numpy(), score(val), base_rate)


def on_next_month(score, threshold, nxt):
    """PR-AUC, recall, precision and decline rate of one model and threshold on next month's traffic."""
    y, s = nxt.is_fraud.to_numpy(), score(nxt)
    declined = s >= threshold
    return {"pr_auc": average_precision_score(y, s), "recall": declined[y == 1].mean(),
            "precision": y[declined].mean() if declined.any() else 0.0, "decline_rate": declined.mean()}


def run_break(history, nxt, seed):
    """P1 and P3 on next month's traffic, the corrected core's operating point, what the shipped test
    rows hold, and each single fix against the shipped script (10-split means)."""
    shipped_score, shipped_t, _ = variant(history, seed)
    shipped = on_next_month(shipped_score, shipped_t, nxt)
    labkit.result("break.shipped_pr_auc_next", shipped["pr_auc"], unit="fraction")
    labkit.result("break.shipped_recall_next", shipped["recall"], unit="fraction")
    labkit.result("break.shipped_precision_next", shipped["precision"], unit="fraction")
    labkit.result("P3.decline_rate_next", shipped["decline_rate"], unit="fraction")
    honest_score, honest_t = honest(history, seed)
    fair = on_next_month(honest_score, honest_t, nxt)
    labkit.result("P1.honest_pr_auc", fair["pr_auc"], unit="fraction")
    labkit.result("break.honest_threshold", honest_t, unit="probability")
    labkit.result("break.honest_recall_next", fair["recall"], unit="fraction")
    labkit.result("break.honest_precision_next", fair["precision"], unit="fraction")
    labkit.result("break.honest_decline_rate_next", fair["decline_rate"], unit="fraction")
    share, unique, seen = leak_facts(history, seed)
    labkit.result("break.shipped_test_fraud_share", share, unit="fraction")
    labkit.result("break.shipped_test_unique_frauds", unique, unit="count")
    labkit.result("break.shipped_test_frauds_seen", seen, unit="fraction")
    # Each fix alone, from the shipped script, against the shipped script on the same REPEATS sub-seeds.
    runs = {"shipped": per_split(history, nxt, seed)}
    runs.update({fix: per_split(history, nxt, seed, frozenset({fix})) for fix in FIXES})
    for label, df in runs.items():
        prefix = "break.shipped_avg" if label == "shipped" else f"break.fix_{label}"
        for name in ("pr_auc", "recall", "decline_rate", "decline_rate_next"):
            labkit.result(f"{prefix}_{name}", df[name].mean(), unit="fraction", n=REPEATS)
    labkit.result("break.shipped_split_decline_rate_next_min", runs["shipped"].decline_rate_next.min(),
                  unit="fraction", n=REPEATS)
    labkit.result("break.shipped_split_decline_rate_next_max", runs["shipped"].decline_rate_next.max(),
                  unit="fraction", n=REPEATS)


def main():
    args = labkit.start(lab=27, device="cpu")
    if args.mode == "download":
        return download()
    history, nxt = load_payments(smoke=labkit.smoke())
    print(f"DATA history: {len(history):,} payments, {history.is_fraud.sum()} frauds; "
          f"next month: {len(nxt):,} payments, {nxt.is_fraud.sum()} frauds", flush=True)
    if args.mode in ("smoke", "baseline"):  # the shipped report
        for name, value in variant(history, args.seed)[2].items():
            labkit.result(f"baseline.{name}", value, unit=UNITS[name])
    if args.mode in ("smoke", "change"):  # the fixed copy, reported on history as the script would
        for name, value in variant(history, args.seed, frozenset(FIXES))[2].items():
            labkit.result(f"change.{name}", value, unit=UNITS[name])  # one run: what your copy prints
        mean = per_split(history, nxt, args.seed, frozenset(FIXES)).mean()
        for name in ("pr_auc", "recall", "precision"):
            labkit.result(f"change.{name}_avg", mean[name], unit="fraction", n=REPEATS)
        labkit.result("P2.silent_bugs", len(FIXES), unit="count")
    if args.mode in ("smoke", "break"):
        run_break(history, nxt, args.seed)


if __name__ == "__main__":
    main()
