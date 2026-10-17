"""18. Clustering hygiene: what scaling and outliers do to k-means. Segments customers by recency, frequency and monetary value (RFM).

Modes: --download, --smoke, --baseline (P1), --change (P2), --break (P3).
Level S starter: download(), load_data() and report() are written. Before the baseline you
write a harness prompt in the lab file and rfm() here; before the change you write clean() here.
The AI writes the harness from your prompt.
"""
import io
import sys
import zipfile
from pathlib import Path
sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "labkit.py").exists())))
import labkit  # before numpy: it sets cache defaults
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

URL = "https://archive.ics.uci.edu/static/public/352/online+retail.zip"
ZIP_BYTES = 23_715_478
MEMBER = "Online Retail.xlsx"
PARQUET = labkit.DATA / "online_retail" / "online_retail.parquet"
STEP = {"baseline": "P1", "change": "P2", "break": "P3"}


def download():
    """Fetch the zip once, then convert the Excel workbook to parquet once (about a minute in all)."""
    zip_path = labkit.fetch(URL, PARQUET.with_name("online_retail.zip"), size=ZIP_BYTES)
    with labkit.locked(PARQUET):
        if not PARQUET.exists():
            with zipfile.ZipFile(zip_path) as z:
                book = io.BytesIO(z.read(MEMBER))
            lines = pd.read_excel(book, engine="openpyxl",
                                  dtype={"InvoiceNo": str, "StockCode": str, "Description": str})
            part = PARQUET.with_suffix(".part")
            lines.to_parquet(part, index=False)
            part.replace(PARQUET)
    print(f"HAVE {PARQUET} {PARQUET.stat().st_size / 1e6:.1f} MB", flush=True)


def load_data():
    """Every invoice line as a DataFrame (the first 20,000 in --smoke).

    Columns: InvoiceNo (str; a leading C marks a cancellation), StockCode, Description,
    Quantity, InvoiceDate (datetime), UnitPrice (pounds sterling), CustomerID (NaN when
    missing), Country.
    """
    if not PARQUET.exists():
        print(f"missing {PARQUET}: run this script with --download first", flush=True)
        sys.exit(2)
    lines = pd.read_parquet(PARQUET)
    return lines.head(20_000) if labkit.smoke() else lines


def report(mode, X, labels):
    """The RESULT contract for one k-means run. X is the matrix KMeans saw, labels its cluster per row.

    Prints the customer count, the cluster sizes (biggest first), the step's biggest-cluster
    share, in --change the shift from the baseline share, and the silhouette on up to 5,000 rows.
    """
    sizes = np.sort(np.bincount(labels))[::-1]
    share = sizes[0] / len(labels)
    labkit.result(f"{mode}.n_customers", len(labels), unit="customers")
    labkit.result(f"{mode}.sizes", "/".join(str(s) for s in sizes), unit="customers")
    labkit.result(f"{STEP[mode]}.biggest_share", share, unit="fraction")
    if mode == "change" and (p1 := labkit.prior("P1.biggest_share")) is not None:
        labkit.result("P2.delta_share", share - p1, unit="fraction")
    sil = silhouette_score(X, labels, sample_size=min(5000, len(labels)), random_state=args.seed)
    labkit.result(f"{mode}.silhouette", sil, unit="score")


args = labkit.start(lab=18, device="cpu")
if args.mode == "download":
    download()
elif args.mode == "smoke":
    load_data()  # checks that the parquet loads
    # smoke checks the plumbing only: random points stand in for your RFM table
    X = np.random.default_rng(args.seed).normal(size=(300, 3))
    for mode in STEP:
        report(mode, X, KMeans(n_clusters=4, n_init=10, random_state=args.seed).fit_predict(X))
else:
    raise NotImplementedError("write the harness: see the lab file")
