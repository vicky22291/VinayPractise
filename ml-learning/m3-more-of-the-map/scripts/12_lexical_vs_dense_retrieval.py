"""12. Lexical vs dense retrieval: BM25, embeddings and fusion. Scores BM25, a small embedding model and their rank fusion on BEIR SciFact with nDCG@10.

Modes: --download, --smoke, --baseline (P1), --change (P2), --break (P3), --check.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "labkit.py").exists())))
import labkit  # before numpy, torch, transformers: it sets cache defaults
import math
import os
import shutil
import time
from collections import Counter
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")  # no download or weight-loading bars
import bm25s
import numpy as np
import pandas as pd
import torch  # imported before labkit.start, so its RNG gets seeded

args = labkit.start(lab=12, device="cpu", extra_modes=("check",))
DIR = labkit.DATA / "scifact"
HF = "https://huggingface.co/datasets/BeIR"
FILES = {"corpus.parquet": (f"{HF}/scifact/resolve/main/corpus/corpus-00000-of-00001.parquet", 4_469_916),
         "queries.parquet": (f"{HF}/scifact/resolve/main/queries/queries-00000-of-00001.parquet", 64_982),
         "test.tsv": (f"{HF}/scifact-qrels/resolve/main/test.tsv", 5_389)}
ZIP = "https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/scifact.zip"
MODEL, BREAK_QUERY_MODEL = "sentence-transformers/all-MiniLM-L6-v2", "BAAI/bge-small-en-v1.5"


def download():
    from sentence_transformers import SentenceTransformer  # slow to import, and --check does not need it
    try:
        for name, (url, size) in FILES.items():
            labkit.fetch(url, DIR / name, size=size)
    except OSError:  # fallback: the BEIR zip has the same tables as jsonl; save them under the same names
        src = labkit.extract(labkit.fetch(ZIP, DIR / "scifact.zip", size=2_816_079), DIR) / "scifact"
        for name in ("corpus", "queries"):
            table = pd.read_json(src / f"{name}.jsonl", lines=True, dtype={"_id": str})
            table.reindex(columns=["_id", "title", "text"], fill_value="").to_parquet(DIR / f"{name}.parquet")
        shutil.copyfile(src / "qrels" / "test.tsv", DIR / "test.tsv")
    for name in (MODEL, BREAK_QUERY_MODEL):
        with labkit.locked(Path(os.environ["HF_HOME"]) / name.replace("/", "--")):
            SentenceTransformer(name, device="cpu")
        repo = Path(os.environ["HF_HOME"]) / "hub" / f"models--{name.replace('/', '--')}"
        print(f"MODEL {name} {repo} {sum(f.stat().st_size for f in repo.glob('blobs/*')) / 1e6:.1f} MB", flush=True)


def load_data():
    """Doc ids and texts (title + ' ' + text), the test queries, and each query's relevant doc ids."""
    qrels = pd.read_csv(DIR / "test.tsv", sep="\t", dtype=str)
    relevant = qrels[qrels["score"].astype(int) > 0].groupby("query-id")["corpus-id"].agg(set).to_dict()
    corpus, queries = (pd.read_parquet(DIR / f"{name}.parquet").astype({"_id": str}) for name in ("corpus", "queries"))
    queries = queries[queries["_id"].isin(relevant)]
    if labkit.smoke():  # tiny data: 20 queries, their documents and the first 400 others
        queries = queries.head(20)
        wanted = set().union(*(relevant[q] for q in queries["_id"]))
        corpus = corpus[corpus["_id"].isin(wanted) | (np.arange(len(corpus)) < 400)]
    docs = (corpus["title"] + " " + corpus["text"]).tolist()
    print(f"DATA docs={len(docs)} queries={len(queries)}", flush=True)
    return corpus["_id"].tolist(), docs, queries["_id"].tolist(), queries["text"].tolist(), relevant


# --- CONCEPT start ---
def bm25_scores(query, docs, k1=1.2, b=0.75):
    """BM25 score of every document for one query: a list of floats in docs order.

    query is a list of tokens; docs is a list of token lists. Compute N (number of
    docs), avgdl (mean doc length) and df[t] (docs that contain t) once, before the
    loop over docs. A doc's score sums, over the query tokens t it contains
    (a repeated query token counts again):
        idf(t) * tf * (k1 + 1) / (tf + k1 * (1 - b + b * len(doc) / avgdl))
    with idf(t) = ln(1 + (N - df[t] + 0.5) / (df[t] + 0.5)) and tf = count of t in the doc.
    """
    raise NotImplementedError("TODO(human)")


# --- CONCEPT end ---


def top(scores, k=100):
    """Indices of the k highest scores, best first; ties keep corpus order."""
    return np.argsort(-np.asarray(scores, dtype=float), kind="stable")[:k]


def bm25_top(docs, queries):
    """Top 100 doc indices per query by BM25 on bm25s tokens (English stopwords, no stemmer).

    A doc that shares no token with the query scores 0 and is not retrieved.
    """
    doc_tok, query_tok = (bm25s.tokenize(t, stopwords="en", return_ids=False, show_progress=False) for t in (docs, queries))
    score = lambda q: bm25_scores(q, doc_tok)
    if labkit.smoke():  # smoke checks the plumbing only: bm25s stands in for bm25_scores
        index = bm25s.BM25(method="lucene", k1=1.2, b=0.75)
        index.index(doc_tok, show_progress=False)
        score = index.get_scores
    return [[i for i in top(s) if s[i] > 0] for s in (np.asarray(score(q)) for q in query_tok)]


def embed(model_name, texts):
    """Unit-length embeddings, and texts embedded per second (median of 10 chunks, after 1 warmup batch)."""
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(model_name, device="cpu", local_files_only=True)  # --download fetched it
    model.encode(texts[:64], batch_size=64)
    step, parts, rates = -(-len(texts) // 10), [], []
    for i in range(0, len(texts), step):
        t0 = time.perf_counter()
        parts.append(model.encode(texts[i:i + step], batch_size=64, normalize_embeddings=True))
        rates.append(len(parts[-1]) / (time.perf_counter() - t0))
    return np.vstack(parts), float(np.median(rates))


def ndcg10(ranked, relevant):
    """Binary-gain nDCG@10 for one query: DCG of the top 10 over the best possible DCG."""
    dcg = sum(1 / math.log2(rank + 2) for rank, d in enumerate(ranked[:10]) if d in relevant)
    return dcg / sum(1 / math.log2(rank + 2) for rank in range(min(len(relevant), 10)))


def rrf(rankings, k=60):
    """Reciprocal rank fusion: each ranking adds 1 / (k + rank) to every doc it holds, rank 1 first."""
    fused = Counter()
    for ranking in rankings:
        for rank, d in enumerate(ranking, start=1):
            fused[d] += 1 / (k + rank)
    return [d for d, _ in fused.most_common()]


def check():
    """20 synthetic rows: ndcg10 matches scikit-learn, and bm25_scores ranks like bm25s (method='lucene')."""
    from sklearn.metrics import ndcg_score
    rng = np.random.default_rng(0)
    rel, score = rng.integers(0, 2, 20), rng.random(20)
    rel[0] = 1
    assert math.isclose(ndcg10(list(np.argsort(-score)), set(np.flatnonzero(rel))), ndcg_score([rel], [score], k=10))
    zipf = 1 / np.arange(1, 301)  # word frequencies as in real text: a few common words, many rare ones
    docs = [[f"w{i}" for i in rng.choice(300, rng.integers(3, 30), p=zipf / zipf.sum())] for _ in range(20)]
    index = bm25s.BM25(method="lucene", k1=1.2, b=0.75)
    index.index(docs, show_progress=False)
    for q in (["w1", "w2"], ["w3", "w3", "w7"], ["w0", "w9", "w24", "w13"], ["w0", "w9"]):
        assert list(top(bm25_scores(q, docs), 20)) == list(top(index.get_scores(q), 20)), f"rank order differs for {q}"
    print("check: PASS")


if args.mode == "download":
    download()
elif args.mode == "check":
    check()
else:
    ids, docs, qids, queries, relevant = load_data()
    ndcg = lambda rankings: np.array([ndcg10([ids[i] for i in r], relevant[q]) for r, q in zip(rankings, qids)])
    lexical = bm25_top(docs, queries) if args.mode != "break" else None
    doc_vecs, docs_per_s = embed(MODEL, docs)
    dense = [top(doc_vecs @ q) for q in embed(MODEL, queries)[0]]
    if args.mode in ("smoke", "baseline"):
        labkit.result("baseline.ndcg10_bm25", ndcg(lexical).mean(), unit="ndcg@10")
        labkit.result("P1.ndcg10_dense", ndcg(dense).mean(), unit="ndcg@10")
        labkit.result("baseline.docs_per_s", docs_per_s, unit="docs/s", device="cpu", batch=64, warmup=1, n=10, stat="median")
    if args.mode in ("smoke", "change"):
        hybrid = ndcg([rrf([a, b]) for a, b in zip(lexical, dense)])
        best = max(ndcg(lexical), ndcg(dense), key=np.mean)
        rows = np.random.default_rng(args.seed).integers(0, len(qids), (2000, len(qids)))  # resample the queries
        low, high = np.percentile((hybrid - best)[rows].mean(axis=1), [2.5, 97.5])  # 95% interval of the delta
        labkit.result("P2.ndcg10_hybrid", hybrid.mean(), unit="ndcg@10")
        labkit.result("P2.delta_vs_best", hybrid.mean() - best.mean(), unit="ndcg@10")
        labkit.result("change.delta_ci95_low", low, unit="ndcg@10")
        labkit.result("change.delta_ci95_high", high, unit="ndcg@10")
    if args.mode in ("smoke", "break"):
        mixed = [top(doc_vecs @ q) for q in embed(BREAK_QUERY_MODEL, queries)[0]]
        labkit.result("P3.ndcg10_mismatched", ndcg(mixed).mean(), unit="ndcg@10")
