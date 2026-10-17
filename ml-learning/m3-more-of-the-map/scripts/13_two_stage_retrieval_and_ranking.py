"""13. Two-stage retrieval, then ranking: how much can the re-ranker recover?
MovieLens 1M: 64-d SVD candidates, a LightGBM re-ranker, recall@k, nDCG@10 and ms per request.

Modes: --download, --smoke, --baseline (P1), --change (P2), --break (P3), --check, --stretch (not captured).
"""
import sys
import time
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "labkit.py").exists())))
import labkit  # before numpy: it sets cache defaults
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from sklearn.decomposition import TruncatedSVD
from sklearn.metrics import ndcg_score, recall_score

HOME = labkit.DATA / "movielens"
ML1M = ("https://files.grouplens.org/datasets/movielens/ml-1m.zip", 5_917_549)
ML32M = ("https://files.grouplens.org/datasets/movielens/ml-32m.zip", 238_950_008)
DIM, N_CAND, K, WARMUP = 64, 100, 10, 20  # SVD width, candidates passed on, list length, untimed requests


# --- CONCEPT start ---
def recall_at_k(ranked, relevant, k):
    """Share of the relevant items that appear in the first k of ranked.

    ranked: item ids, best first. relevant: a non-empty set of item ids.
    """
    raise NotImplementedError("TODO(human)")

def ndcg_at_k(ranked, relevant, k=10):
    """nDCG@k with binary gains: the DCG of ranked divided by the DCG of an ideal list.

    A relevant item at position i (0 is the top) adds 1 / log2(i + 2) to the DCG.
    The ideal list puts min(k, len(relevant)) relevant items first.
    """
    raise NotImplementedError("TODO(human)")


# --- CONCEPT end ---


def load_data(smoke):
    """Ratings with 0-based user and item ids, plus a movie x genre 0/1 matrix."""
    r = pd.read_csv(HOME / "ml-1m" / "ratings.dat", sep="::", engine="python",
                    names=["user", "movie", "rating", "ts"], nrows=50_000 if smoke else None)
    movies = pd.read_csv(HOME / "ml-1m" / "movies.dat", sep="::", engine="python",
                         names=["movie", "title", "genres"], encoding="latin-1").set_index("movie")
    ids = np.sort(r.movie.unique())
    r["user"], r["item"] = r.user - 1, np.searchsorted(ids, r.movie)
    return r, movies.loc[ids, "genres"].str.get_dummies("|").to_numpy(float)


def snapshot(r, genres, cutoff, seed):
    """Everything known before cutoff: 64-d user and item vectors, seen movies, ranker inputs."""
    past = r[r.ts < cutoff]
    seen = csr_matrix((np.ones(len(past)), (past.user, past.item)), shape=(r.user.max() + 1, len(genres)))
    svd = TruncatedSVD(DIM, random_state=seed)
    user_vecs = svd.fit_transform(seen)
    pop, activity = np.bincount(past.item, minlength=len(genres)), np.diff(seen.indptr)
    mean = np.bincount(past.item, past.rating, len(genres)) / np.where(pop > 0, pop, np.nan)
    share = (seen @ genres) / np.maximum(activity, 1)[:, None]  # each user's genre mix
    return SimpleNamespace(seen=seen, user_vecs=user_vecs, item_vecs=svd.components_.T, genres=genres,
                           pop=pop, mean=mean, activity=activity, share=share)


def retrieve(u, snap, n):
    """Stage 1: score every movie with one dot product, drop the ones u has seen, keep the best n."""
    scores = snap.item_vecs @ snap.user_vecs[u]
    scores[snap.seen.indices[snap.seen.indptr[u]:snap.seen.indptr[u + 1]]] = -np.inf
    cand = np.argpartition(-scores, n)[:n]
    cand = cand[np.argsort(-scores[cand])]
    return cand, scores[cand]


def features(u, cand, scores, snap):
    """Stage 2 inputs: candidate score, popularity, mean rating, user activity, genre overlap."""
    return np.column_stack([scores, snap.pop[cand], snap.mean[cand],
                            np.full(len(cand), snap.activity[u]), snap.genres[cand] @ snap.share[u]])


def train_ranker(r, genres, t1, t2, seed):
    """Stage 2: LightGBM lambdarank on each user's 100 candidates, labelled by positives in [T1, T2)."""
    import lightgbm as lgb  # imported here: lightgbm and faiss (--stretch) in one process crash
    snap, X, y = snapshot(r, genres, t1, seed), [], []
    for u, items in r[(r.ts >= t1) & (r.ts < t2) & (r.rating >= 4)].groupby("user").item:
        if snap.activity[u] > 0:  # a user with no rating before T1 is cold-start: left out, as in evaluate()
            cand, scores = retrieve(u, snap, N_CAND)
            X.append(features(u, cand, scores, snap))
            y.append(np.isin(cand, items))
    ranker = lgb.LGBMRanker(objective="lambdarank", n_jobs=1, random_state=seed, verbose=-1)  # library defaults
    return ranker.fit(np.vstack(X), np.concatenate(y).astype(int), group=[N_CAND] * len(X))


def timed(fn, inputs, step):
    """Call fn on one input at a time; print p50 and p99 ms per call, leaving out the first WARMUP."""
    out, ms = [], []
    for x in inputs:
        t0 = time.perf_counter()
        out.append(fn(x))
        ms.append(1e3 * (time.perf_counter() - t0))
    tags = dict(unit="ms", device="cpu", batch=1, warmup=WARMUP, n=len(ms) - WARMUP)
    labkit.result(f"{step}p50_ms", np.percentile(ms[WARMUP:], 50), stat="median", **tags)
    labkit.result(f"{step}p99_ms", np.percentile(ms[WARMUP:], 99), stat="p99", **tags)
    return out


def evaluate(r, snap, t2, n_cand, ranker, recall, ndcg, step):
    """Serve each test user one request at a time, then score the lists against positives after T2.

    Means of: candidate recall@100, served recall@10, nDCG@10 of the candidate order, of the served
    order and of the candidates sorted by popularity alone (untimed); plus the number of users.
    """
    test = {u: set(items) for u, items in r[(r.ts >= t2) & (r.rating >= 4)].groupby("user").item
            if snap.activity[u] > 0}  # a user with no history before T2 is cold-start: out of scope here

    def serve(u):
        cand, scores = retrieve(u, snap, n_cand)
        if ranker is None:
            return cand, cand
        return cand, cand[np.argsort(-ranker.predict(features(u, cand, scores, snap)))]

    rows = [[recall(c, test[u], N_CAND), recall(f, test[u], K), ndcg(c, test[u], K), ndcg(f, test[u], K),
             ndcg(c[np.argsort(-snap.pop[c], kind="stable")], test[u], K)]
            for u, (c, f) in zip(test, timed(serve, test, step))]
    return np.mean(rows, axis=0), len(rows)


def main():
    args = labkit.start(lab=13, device="cpu", extra_modes=("check", "stretch"))
    if args.mode in ("download", "check", "stretch"):
        return {"download": download, "check": check, "stretch": lambda: stretch(args.seed)}[args.mode]()
    r, genres = load_data(labkit.smoke())
    t1, t2 = np.quantile(r.ts, [0.8, 0.9])  # fit before T1, label in [T1, T2), refit before T2, test after
    # smoke checks the plumbing only: scikit-learn stands in for the two TODO functions
    metrics = (sk_recall_at_k, sk_ndcg_at_k) if labkit.smoke() else (recall_at_k, ndcg_at_k)
    test = snapshot(r, genres, t2, args.seed)
    if args.mode in ("baseline", "smoke"):
        (rec100, rec10, ndcg, _, _), n = evaluate(r, test, t2, N_CAND, None, *metrics, "baseline.")
        labkit.result("P1.recall_at_100", rec100, unit="fraction", users=n)
        labkit.result("baseline.recall_at_10", rec10, unit="fraction", users=n)
        labkit.result("baseline.ndcg_at_10", ndcg, unit="ndcg@10", users=n)
    ranker = None if args.mode == "baseline" else train_ranker(r, genres, t1, t2, args.seed)
    if args.mode in ("change", "smoke"):
        (_, rec10, ndcg_cand, ndcg, ndcg_pop), n = evaluate(r, test, t2, N_CAND, ranker, *metrics, "change.")
        labkit.result("P2.ndcg_at_10", ndcg, unit="ndcg@10", users=n)
        labkit.result("P2.ndcg_delta", ndcg - ndcg_cand, unit="ndcg@10", users=n)
        labkit.result("change.recall_at_10", rec10, unit="fraction", users=n)
        labkit.result("change.popsort_ndcg_at_10", ndcg_pop, unit="ndcg@10", users=n)
    if args.mode in ("break", "smoke"):
        (_, rec10, ndcg_cand, ndcg, _), n = evaluate(r, test, t2, K, ranker, *metrics, "break.")
        labkit.result("P3.ndcg_delta", ndcg - ndcg_cand, unit="ndcg@10", users=n)
        labkit.result("break.ndcg_at_10", ndcg, unit="ndcg@10", users=n)
        labkit.result("break.recall_at_10", rec10, unit="fraction", users=n)


def download():
    labkit.extract(labkit.fetch(ML1M[0], HOME / "ml-1m.zip", size=ML1M[1]), HOME)
    for path in (HOME / "ml-1m" / "ratings.dat", HOME / "ml-1m" / "movies.dat"):
        print(f"DATA {path} {path.stat().st_size / 1e6:.1f} MB")


def sk_recall_at_k(ranked, relevant, k):
    items = np.array(list(dict.fromkeys([*ranked, *relevant])))  # the list, then the missed relevant items
    return recall_score(np.isin(items, list(relevant)).astype(int), np.isin(items, ranked[:k]).astype(int))


def sk_ndcg_at_k(ranked, relevant, k=10):
    items = np.array(list(dict.fromkeys([*ranked, *relevant])))
    return ndcg_score([np.isin(items, list(relevant)).astype(int)], [-np.arange(len(items))], k=k)


def check():
    rng = np.random.default_rng(0)
    for _ in range(20):  # a 20-row fixture against scikit-learn
        ranked, relevant = rng.permutation(30), set(rng.choice(30, rng.integers(1, 13), replace=False))
        for k in (5, 10):
            assert abs(recall_at_k(ranked, relevant, k) - sk_recall_at_k(ranked, relevant, k)) < 1e-12
            assert abs(ndcg_at_k(ranked, relevant, k) - sk_ndcg_at_k(ranked, relevant, k)) < 1e-12
    print("check: PASS")


def stretch(seed):
    """Not captured: exact vs faiss HNSW (M=32) top-10 on MovieLens 32M, one query at a time, one thread."""
    import faiss  # python -m pip install faiss-cpu==1.15.1
    labkit.extract(labkit.fetch(ML32M[0], HOME / "ml-32m.zip", size=ML32M[1]), HOME)
    r = pd.read_csv(HOME / "ml-32m" / "ratings.csv", usecols=["userId", "movieId"])
    seen = csr_matrix((np.ones(len(r), np.float32), (pd.factorize(r.userId)[0], pd.factorize(r.movieId)[0])))
    svd = TruncatedSVD(DIM, random_state=seed)
    queries = np.ascontiguousarray(svd.fit_transform(seen)[:1000], dtype=np.float32)  # the first 1,000 users
    items = np.ascontiguousarray(svd.components_.T, dtype=np.float32)
    flat, index = faiss.IndexFlatIP(DIM), faiss.IndexHNSWFlat(DIM, 32, faiss.METRIC_INNER_PRODUCT)
    index.hnsw.efConstruction = 200
    flat.add(items)
    index.add(items)  # the graph builds on every core; every search below runs on one
    faiss.omp_set_num_threads(1)
    exact = timed(lambda q: flat.search(q[None], K)[1][0], queries, "stretch.exact_")  # brute force
    for ef in (16, 64, 256):  # ef_search: the beam width at query time
        index.hnsw.efSearch = ef
        found = timed(lambda q: index.search(q[None], K)[1][0], queries, f"stretch.hnsw_ef{ef}_")
        hits = [len(set(a) & set(b)) / K for a, b in zip(found, exact)]
        labkit.result(f"stretch.hnsw_ef{ef}_recall_at_10", np.mean(hits), unit="fraction", n=len(hits))


if __name__ == "__main__":
    main()
