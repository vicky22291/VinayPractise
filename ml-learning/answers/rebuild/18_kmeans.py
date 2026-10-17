"""Rebuild 18: standardize() and kmeans() from memory.

Write both bodies, then run from the module folder: python rebuild/18_kmeans.py
check() compares with scikit-learn's StandardScaler and with KMeans started from the
same initial centres. It never looks at this lab's results.
"""
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


def standardize(X):
    """Return X with each column shifted to mean 0 and scaled to standard deviation 1 (ddof=0)."""
    X = np.asarray(X, dtype=float)
    return (X - X.mean(axis=0)) / X.std(axis=0)


def kmeans(X, k, n_iter, seed):
    """Lloyd's algorithm on the rows of X. Return (labels, centres, inertia).

    Initial centres: the rows np.random.default_rng(seed).choice(len(X), size=k, replace=False) of X.
    Stop when no label changes, or after n_iter rounds. A centre that loses all its rows stays put.
    inertia: the sum of squared distances from each row to its own centre.
    """
    X = np.asarray(X, dtype=float)
    centres = X[np.random.default_rng(seed).choice(len(X), size=k, replace=False)]
    labels = None
    for _ in range(n_iter):
        new = ((X[:, None, :] - centres[None, :, :]) ** 2).sum(axis=2).argmin(axis=1)
        if labels is not None and np.array_equal(new, labels):
            break
        labels = new
        for j in range(k):
            if np.any(labels == j):  # an empty cluster keeps its centre
                centres[j] = X[labels == j].mean(axis=0)
    d2 = ((X[:, None, :] - centres[None, :, :]) ** 2).sum(axis=2)
    labels = d2.argmin(axis=1)
    return labels, centres, d2[np.arange(len(X)), labels].sum()


def check():
    rng = np.random.default_rng(0)
    blobs = [rng.normal(centre, spread, size=(60, 3)) for centre, spread in ((0, 1), (6, 2), (-5, 0.5))]
    X = np.vstack(blobs) * [1, 10, 100]  # three columns in different units
    Xs = standardize(X)
    assert np.allclose(Xs, StandardScaler().fit_transform(X)), "standardize() differs from StandardScaler"
    for k, seed in ((3, 0), (4, 1), (5, 2)):
        labels, centres, inertia = kmeans(Xs, k, n_iter=100, seed=seed)
        init = Xs[np.random.default_rng(seed).choice(len(Xs), size=k, replace=False)]
        ref = KMeans(n_clusters=k, init=init, n_init=1, max_iter=100, tol=0.0, algorithm="lloyd").fit(Xs)
        gap = abs(inertia - ref.inertia_) / ref.inertia_
        assert gap < 1e-6, f"k={k}: inertia {inertia:.6f}, sklearn {ref.inertia_:.6f}"
    print("check: PASS")


if __name__ == "__main__":
    check()
