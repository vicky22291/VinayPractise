"""27. Audit an AI-written fraud pipeline: silent bugs in fluent code. The script under audit: it trains a card-fraud model on payment history and reports its offline numbers.

Modes: --download, --smoke, --baseline, --change, --break.

The pipeline fits a standardized logistic regression to the payment history (the first 80%
of payments by time), balancing the rare fraud class so the model learns it, and reports
PR-AUC on held-out rows plus the operating point the risk team ships.
--baseline and --change run the same pipeline; --change labels its lines change.*, so a
copy you edit can be compared with this script's --baseline. --break prints one line.
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
HISTORY_SHARE = 0.80    # train and evaluate on the first 80% of payments by time
FRAUD_COPIES = 10       # rebalancing: each fraud is drawn this many times
LEGIT_SHARE = 0.10      # rebalancing: share of the legitimate payments kept
TEST_SIZE = 0.20        # share of rows held out for evaluation
DECLINE_BUDGET = 0.002  # risk policy: decline at most 0.2% of payments
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


def load_history(smoke=False):
    """The payment history: FEATURES plus is_fraud for the first HISTORY_SHARE of rows.

    The table is stored in time order, so the first rows are the oldest payments.
    Smoke keeps every 5th row.
    """
    pq = labkit.DATA / "creditcard" / "dataset_1597.pq"  # present only if --download used the fallback
    df = pd.read_parquet(pq) if pq.exists() else labkit.openml(1597)
    df = df.assign(is_fraud=pd.to_numeric(df["Class"].astype(str)).astype(int))[FEATURES + ["is_fraud"]]
    if smoke:
        df = df.iloc[::5]
    return df.iloc[: int(len(df) * HISTORY_SHARE)].reset_index(drop=True)


def rebalance(payments, seed):
    """Balance the classes so the model sees enough fraud.

    Fraud is a tiny share of payments, so draw each fraud FRAUD_COPIES times and keep
    LEGIT_SHARE of the legitimate payments, then shuffle the rows.
    """
    fraud = payments[payments.is_fraud == 1]
    legit = payments[payments.is_fraud == 0]
    fraud = fraud.sample(frac=FRAUD_COPIES, replace=True, random_state=seed)
    legit = legit.sample(frac=LEGIT_SHARE, random_state=seed)
    return pd.concat([fraud, legit]).sample(frac=1, random_state=seed)


def train_model(X, y):
    """Standardize the features, then fit a logistic regression."""
    return make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000)).fit(X, y)


def decline_rate(base_rate, recall, precision):
    """Share of all payments declined: caught frauds plus false declines.

    Declines = frauds caught / precision, and frauds caught = base_rate * recall per payment.
    """
    return base_rate * recall / np.maximum(precision, 1e-12)


def choose_threshold(y_true, scores, base_rate):
    """The operating threshold: the best F1 among thresholds whose decline rate fits DECLINE_BUDGET."""
    precision, recall, thresholds = precision_recall_curve(y_true, scores)
    precision, recall = precision[:-1], recall[:-1]  # the last point has no threshold
    f1 = 2 * precision * recall / np.maximum(precision + recall, 1e-12)
    allowed = decline_rate(base_rate, recall, precision) <= DECLINE_BUDGET
    return thresholds[np.argmax(np.where(allowed, f1, -1.0))]


def evaluate(model, X, y, base_rate):
    """PR-AUC on the held-out rows, then the operating point: threshold, recall, precision, decline rate."""
    scores = model.predict_proba(X)[:, 1]
    threshold = choose_threshold(y, scores, base_rate)
    declined = scores >= threshold
    recall, precision = declined[y == 1].mean(), y[declined].mean()
    return {"pr_auc": average_precision_score(y, scores), "threshold": threshold, "recall": recall,
            "precision": precision, "decline_rate": decline_rate(base_rate, recall, precision)}


def main():
    args = labkit.start(lab=27, device="cpu")
    if args.mode == "download":
        return download()
    if args.mode == "break":
        return print("--break runs from the reference: after your audit, ask the AI to run it, "
                     "or ask for 'debrief 27'.", flush=True)
    history = load_history(smoke=labkit.smoke())
    base_rate = history.is_fraud.mean()
    print(f"DATA history: {len(history):,} payments, {history.is_fraud.sum()} frauds", flush=True)
    data = rebalance(history, args.seed)
    X_train, X_test, y_train, y_test = train_test_split(
        data[FEATURES], data.is_fraud.to_numpy(), test_size=TEST_SIZE,
        stratify=data.is_fraud, random_state=args.seed)
    model = train_model(X_train, y_train)
    report = evaluate(model, X_test, y_test, base_rate)
    for mode in ("baseline", "change") if labkit.smoke() else (args.mode,):
        for name, value in report.items():
            labkit.result(f"{mode}.{name}", value, unit=UNITS[name])


if __name__ == "__main__":
    main()
