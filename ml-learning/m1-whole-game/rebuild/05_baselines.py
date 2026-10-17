"""Rebuild 05: the baselines a recommender must beat, from memory.

Write the four bodies (about 16 lines in all), then run:  python rebuild/05_baselines.py
check() compares rmse and nearest_items with scikit-learn on toy data, and tests
bias_baseline and split on small cases whose answers are known exactly.
"""
import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error
from sklearn.neighbors import NearestNeighbors


def rmse(a, b):
    """Root mean squared error between two equal-length sequences, as a float."""
    raise NotImplementedError("write this from memory")


def bias_baseline(train, valid, damping=5):
    """Predict valid's ratings with no learning.

    train and valid are DataFrames with user, movie and rating columns.
    1. Start from the global mean rating of train.
    2. User bias: the sum of each user's residuals divided by (that user's count + damping).
    3. Movie bias: the same, on the residuals left after the user bias.
    A user or movie that is not in train gets a bias of 0.
    Return a numpy array with one prediction per row of valid.
    """
    raise NotImplementedError("write this from memory")


def nearest_items(item_emb, item_id, k=5):
    """Row numbers of the k rows of item_emb with the highest cosine similarity to row
    item_id, most similar first, leaving item_id itself out."""
    raise NotImplementedError("write this from memory")


def split(n, valid_frac=0.1, seed=0):
    """A seeded random split of the row numbers 0 to n-1 into (train_idx, valid_idx),
    with int(n * valid_frac) rows in valid. The same seed gives the same split."""
    raise NotImplementedError("write this from memory")


def check():
    rng = np.random.default_rng(0)
    a, b = rng.normal(size=50), rng.normal(size=50)
    assert np.isclose(rmse(a, b), np.sqrt(mean_squared_error(a, b))), "rmse"

    emb = rng.normal(size=(30, 8))
    nn = NearestNeighbors(n_neighbors=6, metric="cosine").fit(emb)
    for item in (0, 7, 29):
        want = [int(i) for i in nn.kneighbors(emb[[item]], return_distance=False)[0] if i != item][:5]
        assert [int(i) for i in nearest_items(emb, item, k=5)] == want, f"nearest_items for row {item}"

    # every user rates every movie, and each rating is 3.5 + a user effect + a movie effect
    u_eff, m_eff = rng.normal(size=6), rng.normal(size=5)
    u_eff, m_eff = u_eff - u_eff.mean(), m_eff - m_eff.mean()
    full = pd.DataFrame([(u, m, 3.5 + u_eff[u] + m_eff[m]) for u in range(6) for m in range(5)],
                        columns=["user", "movie", "rating"])
    assert np.allclose(bias_baseline(full, full, damping=0), full["rating"]), "damping 0 should recover each rating"
    assert np.allclose(bias_baseline(full, full, damping=1e9), 3.5), "huge damping should give the global mean"
    stranger = pd.DataFrame({"user": [99], "movie": [99], "rating": [4.0]})
    assert np.allclose(bias_baseline(full, stranger), 3.5), "an unseen user and movie should get the global mean"

    train_idx, valid_idx = split(1000, 0.1, seed=0)
    assert len(valid_idx) == 100 and len(train_idx) == 900, "split sizes"
    assert sorted(np.concatenate([train_idx, valid_idx]).tolist()) == list(range(1000)), "split covers every row once"
    assert np.array_equal(split(1000, 0.1, seed=0)[1], valid_idx), "same seed, same split"
    assert not np.array_equal(split(1000, 0.1, seed=1)[1], valid_idx), "another seed, another split"
    print("check: PASS")


if __name__ == "__main__":
    check()
