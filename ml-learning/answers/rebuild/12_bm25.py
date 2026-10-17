"""Rebuild 12: BM25 from memory, checked against bm25s. Run from the module folder: python rebuild/12_bm25.py"""
import math
import re
from collections import Counter

import bm25s
import numpy as np


def tokenize(text):
    """Lowercase word tokens of text, as a list of strings."""
    return re.findall(r"\w+", text.lower())


def bm25_scores(query, docs, k1=1.2, b=0.75):
    """BM25 score of every doc for one query: a list of floats in docs order.

    query is a token list; docs is a list of token lists. Use the Lucene idf,
    ln(1 + (N - df + 0.5) / (df + 0.5)), so your ranks can match bm25s. The rest is yours.
    """
    n = len(docs)
    avgdl = sum(len(d) for d in docs) / n
    df = Counter(t for d in docs for t in set(d))
    scores = []
    for d in docs:
        tf = Counter(d)
        s = 0.0
        for t in query:
            if t in tf:
                idf = math.log(1 + (n - df[t] + 0.5) / (df[t] + 0.5))
                s += idf * tf[t] * (k1 + 1) / (tf[t] + k1 * (1 - b + b * len(d) / avgdl))
        scores.append(s)
    return scores


def check():
    """Rank order must equal bm25s 0.3.11 (method='lucene', k1=1.2, b=0.75) on a toy corpus.

    bm25s drops a constant factor, so raw scores differ: the check compares ranks only.
    """
    texts = [
        "Vitamin D deficiency raises the risk of hip fracture in older adults",
        "Fracture healing is faster with early weight bearing after surgery",
        "No association between vitamin C intake and the common cold was found",
        "Vitamin D and calcium supplements did not reduce hip fracture rates",
        "Statins lower LDL cholesterol and the risk of heart attack",
        "Early weight bearing did not change healing time in ankle fracture patients",
        "Vitamin C shortened colds in marathon runners in one small trial",
        "Cholesterol levels in children predict heart disease decades later",
    ]
    docs = [tokenize(t) for t in texts]
    index = bm25s.BM25(method="lucene", k1=1.2, b=0.75)
    index.index(docs, show_progress=False)
    queries = ("vitamin d hip fracture", "common cold vitamin c", "early weight bearing healing", "cholesterol heart risk",
               "statins fracture", "fracture risk in older adults")
    for q in queries:
        tokens = tokenize(q)
        ours = [int(i) for i in np.argsort(-np.asarray(bm25_scores(tokens, docs), dtype=float), kind="stable")]
        lib = [int(i) for i in np.argsort(-index.get_scores(tokens), kind="stable")]
        assert ours == lib, f"{q!r}: your order {ours}, bm25s {lib}"
    print("check: PASS")


if __name__ == "__main__":
    check()
