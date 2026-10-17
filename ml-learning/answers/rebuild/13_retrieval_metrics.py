"""13 rebuild: exact top-k, recall@k, nDCG@k and ANN recall, written from memory.

Write the four bodies, then run: python rebuild/13_retrieval_metrics.py
check() compares with numpy's full argsort and scikit-learn, never with the lab's results.
"""
import numpy as np
from sklearn.metrics import ndcg_score, recall_score


def exact_topk(user_vecs, item_vecs, k):
    """Exact top-k item ids per user by inner product, best first: the ground truth for ANN recall.

    user_vecs is (n_users, d), item_vecs is (n_items, d). Return an (n_users, k) array of item ids.
    Use argpartition to find each row's k best, then sort only those k.
    """
    scores = user_vecs @ item_vecs.T
    top = np.argpartition(-scores, k, axis=1)[:, :k]
    order = np.argsort(-np.take_along_axis(scores, top, axis=1), axis=1)
    return np.take_along_axis(top, order, axis=1)


def recall_at_k(ranked, relevant, k):
    """Share of the relevant items (a non-empty set) that appear in the first k of ranked."""
    return sum(item in relevant for item in ranked[:k]) / len(relevant)


def ndcg_at_k(ranked, relevant, k=10):
    """nDCG@k with binary gains.

    DCG: add 1 / log2(i + 2) for each relevant item at position i < k (0 is the top).
    Divide by the DCG of an ideal list that puts min(k, len(relevant)) relevant items first.
    """
    discount = 1 / np.log2(np.arange(k) + 2)
    dcg = sum(d for item, d in zip(ranked[:k], discount) if item in relevant)
    return dcg / discount[:min(k, len(relevant))].sum()


def ann_recall(ann_ids, exact_ids, k=10):
    """Mean over queries of |first k ANN ids & first k exact ids| / k."""
    return float(np.mean([len(set(a[:k]) & set(e[:k])) / k for a, e in zip(ann_ids, exact_ids)]))


def check():
    rng = np.random.default_rng(0)
    users, items = rng.normal(size=(50, 16)), rng.normal(size=(500, 16))
    top = exact_topk(users, items, 100)
    assert np.array_equal(top, np.argsort(-(users @ items.T), axis=1)[:, :100]), "top-100 differs from a full argsort"
    y_true = (rng.random((20, 30)) < 0.2).astype(int)
    y_true[np.arange(20), rng.integers(0, 30, 20)] = 1  # every row has a relevant item
    for t, s in zip(y_true, rng.random((20, 30))):
        ranked, relevant = np.argsort(-s), set(np.flatnonzero(t))
        top10 = np.isin(np.arange(30), ranked[:10]).astype(int)
        assert abs(recall_at_k(ranked, relevant, 10) - recall_score(t, top10)) < 1e-12, "recall_at_k"
        assert abs(ndcg_at_k(ranked, relevant, 10) - ndcg_score([t], [s], k=10)) < 1e-12, "ndcg_at_k"
    noisy = exact_topk(users + 0.5 * rng.normal(size=users.shape), items, 10)  # stands in for an ANN index
    found, truth = np.zeros((50, 500), int), np.zeros((50, 500), int)
    np.put_along_axis(found, noisy, 1, axis=1)
    np.put_along_axis(truth, top[:, :10], 1, axis=1)
    assert abs(ann_recall(noisy, top, 10) - recall_score(truth, found, average="samples")) < 1e-12, "ann_recall"
    print("check: PASS")


if __name__ == "__main__":
    check()
