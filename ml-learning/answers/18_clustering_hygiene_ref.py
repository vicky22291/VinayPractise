"""18. Clustering hygiene: what scaling and outliers do to k-means. Segments customers by recency, frequency and monetary value (RFM).

Modes: --download, --smoke, --baseline (P1), --change (P2), --break (P3).
"""
import io
import sys
import zipfile
from pathlib import Path
sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "labkit.py").exists())))
import labkit  # before numpy: it sets cache defaults
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

URL = "https://archive.ics.uci.edu/static/public/352/online+retail.zip"
ZIP_BYTES = 23_715_478
MEMBER = "Online Retail.xlsx"
PARQUET = labkit.DATA / "online_retail" / "online_retail.parquet"
STEP = {"baseline": "P1", "change": "P2", "break": "P3"}
SNAPSHOT = pd.Timestamp("2011-12-10")
K = 4
COLOURS, MARKERS = ("#2a78d6", "#eda100", "#1baf7a", "#e87ba4"), "os^D"


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


def rfm(lines):
    """One row per customer: recency (days from the last invoice to SNAPSHOT),
    frequency (distinct invoices) and monetary (sum of Quantity x UnitPrice)."""
    lines = lines.dropna(subset=["CustomerID"]).assign(spend=lambda d: d["Quantity"] * d["UnitPrice"])
    g = lines.groupby("CustomerID")
    return pd.DataFrame({"recency": (SNAPSHOT - g["InvoiceDate"].max()).dt.days,
                         "frequency": g["InvoiceNo"].nunique(),
                         "monetary": g["spend"].sum()})


def clean(lines):
    """Drop cancellation lines, rebuild RFM, then drop customers above the 99th percentile of monetary."""
    table = rfm(lines[~lines["InvoiceNo"].str.startswith("C")])
    return table[table["monetary"] <= table["monetary"].quantile(0.99)]


def plot(mode, table, labels):
    """Recency and frequency against monetary, one colour and marker per cluster, biggest first."""
    out = labkit.DATA / "results" / "lab18" / ("smoke" if labkit.smoke() else "")
    out.mkdir(parents=True, exist_ok=True)
    order = np.argsort(-np.bincount(labels, minlength=K), kind="stable")
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), sharey=True)
    for ax, col in zip(axes, ("recency", "frequency")):
        for slot, c in enumerate(order):
            rows = table[labels == c]
            ax.scatter(rows[col], rows["monetary"], s=10, color=COLOURS[slot], marker=MARKERS[slot],
                       label=f"cluster {slot + 1}, n = {len(rows)}")
        ax.set(xlabel=col, xscale="symlog" if col == "frequency" else "linear", yscale="symlog")
        ax.grid(alpha=0.25)
    axes[0].set_ylabel("monetary, pounds (symlog)")
    axes[1].legend(title=f"{mode}, k = {K}, seed {args.seed}")
    path = out / f"{mode}-s{args.seed}.png"
    fig.savefig(path, dpi=110, bbox_inches="tight")
    plt.close(fig)
    print(f"PLOT {path}", flush=True)


args = labkit.start(lab=18, device="cpu")
if args.mode == "download":
    download()
else:
    lines = load_data()
    for mode in (tuple(STEP) if labkit.smoke() else (args.mode,)):
        table = clean(lines) if mode == "change" else rfm(lines)
        X = table.to_numpy(float) if mode == "break" else StandardScaler().fit_transform(table)
        labels = KMeans(n_clusters=K, n_init=10, random_state=args.seed).fit_predict(X)
        report(mode, X, labels)
        plot(mode, table, labels)
        if mode == "baseline":  # the elbow: inertia for k = 2 to 8, same settings
            for k in range(2, 9):
                inertia = KMeans(n_clusters=k, n_init=10, random_state=args.seed).fit(X).inertia_
                labkit.result(f"baseline.inertia_k{k}", inertia, unit="sum_sq")
