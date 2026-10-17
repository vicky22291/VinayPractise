"""Rebuild for lab 04: TF-IDF by hand, written from memory.

Write the body, then run: python rebuild/04_tfidf.py
check() compares it with scikit-learn's TfidfVectorizer() defaults: the same vocabulary in the same order,
and the same numbers.
"""
import re
from collections import Counter

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer


def tfidf(docs):
    """TF-IDF of a list of strings with TfidfVectorizer's defaults. Returns (matrix, vocabulary).

    - Words: lowercase each document, then take every match of the regex (?u)\\b\\w\\w+\\b (2 or more word characters).
    - Vocabulary: every word seen, sorted. Column j of the matrix belongs to vocabulary[j].
    - idf(t) = ln((1 + N) / (1 + df(t))) + 1, where N is the number of documents and df(t) how many contain t.
    - Each cell: the raw count of the word in that document times the word's idf.
    - Then each row divided by its L2 length (the square root of its sum of squares).
    - A document with no words (empty, or punctuation only) keeps a row of zeros.
    matrix is a dense float64 numpy array with one row per document; vocabulary is a list of strings.
    """
    words = [re.findall(r"(?u)\b\w\w+\b", d.lower()) for d in docs]
    vocabulary = sorted({w for ws in words for w in ws})
    column = {w: j for j, w in enumerate(vocabulary)}
    counts = np.zeros((len(docs), len(vocabulary)))
    for i, ws in enumerate(words):
        for w, k in Counter(ws).items():
            counts[i, column[w]] = k
    df = (counts > 0).sum(axis=0)  # documents that contain each word
    idf = np.log((1 + len(docs)) / (1 + df)) + 1
    matrix = counts * idf
    length = np.sqrt((matrix ** 2).sum(axis=1, keepdims=True))  # each row's L2 length
    return matrix / np.where(length == 0, 1, length), vocabulary  # a document with no words stays a row of zeros


def check():
    """Exactly equal (largest absolute difference 0.0) on short reviews, within 1e-12 on longer ones.

    Each short review has at most two distinct words (one has none), so the order in which the squares are added cannot
    change a single bit. Longer rows can differ in the last bit, because scikit-learn adds the squares in its
    own internal order.
    """
    short = ["Great film!", "A dull, DULL plot.", "Loved it", "Café: 10/10", "Plot? Dull.",
             "great great GREAT", "It's a film", "x y z film", "!!!"]
    longer = ["I loved the acting, hated the plot, and the ending is a bore.",
              "The best film I have seen in years. Go see it!", "Not good: the plot was dull and the acting worse.",
              "It's a GREAT cast in a dull film; the score is great too."]
    for docs, tol in ((short, 0.0), (longer + short, 1e-12)):
        vec = TfidfVectorizer()
        want = vec.fit_transform(docs).toarray()
        got, vocabulary = tfidf(docs)
        assert list(vocabulary) == list(vec.get_feature_names_out()), "the vocabulary or its order differs"
        diff = np.abs(np.asarray(got) - want).max()
        assert diff <= tol, f"largest absolute difference {diff}, allowed {tol}"
    print("check: PASS")


if __name__ == "__main__":
    check()
