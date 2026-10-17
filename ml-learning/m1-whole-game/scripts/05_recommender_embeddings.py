"""05. Recommender: embeddings learned from ratings. Learned user and movie vectors against three baselines with no vectors.

Modes: --download, --smoke, --baseline (P1), --change (P2), --break (P3).
"""
import json
import sys
import warnings
from pathlib import Path
sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "labkit.py").exists())))
import labkit  # before numpy, torch, transformers: it sets cache defaults
import numpy as np
import pandas as pd
import torch
warnings.filterwarnings("ignore", "`torch.jit.script` is deprecated", FutureWarning)  # printed while fastai imports
from fastai.callback.core import Callback
from fastai.collab import CollabDataLoaders
from fastai.layers import Embedding, sigmoid_range
from fastai.learner import Learner
from fastai.losses import MSELossFlat
from fastai.torch_core import Module, defaults

URL = "https://files.grouplens.org/datasets/movielens/ml-100k.zip"
ZIP = labkit.DATA / "ml-100k" / "ml-100k.zip"
DIR = labkit.DATA / "ml-100k" / "ml-100k"
RUNS = {"baseline": dict(bias=False, wd=0.1, epochs=5),  # P1
        "change": dict(bias=True, wd=0.1, epochs=5),     # P2: add the bias terms
        "break": dict(bias=False, wd=0.0, epochs=20)}    # P3: no weight decay, 20 epochs
ANCHOR = "Star Wars (1977)"  # --change prints the 5 movies whose learned vectors sit nearest to this one's


def rmse(pred, target):
    """Root mean squared error: the typical miss, in stars."""
    return float(np.sqrt(np.mean((np.ravel(pred).astype(float) - np.ravel(target)) ** 2)))


def baselines(train, valid, damping=5):
    """Three predictions that learn no vectors: the global mean, each movie's mean, and the damped bias baseline."""
    mu = train["rating"].mean()
    movie_mean = valid["title"].map(train.groupby("title")["rating"].mean()).fillna(mu)  # unseen movie: global mean
    resid = train["rating"] - mu  # a bias is a residual sum over (count + damping): few ratings, a bias near 0
    user_bias = resid.groupby(train["user"]).sum() / (train.groupby("user").size() + damping)
    resid = resid - train["user"].map(user_bias)  # the movie bias fits what the user bias leaves
    movie_bias = resid.groupby(train["title"]).sum() / (train.groupby("title").size() + damping)
    bias = mu + valid["user"].map(user_bias).fillna(0) + valid["title"].map(movie_bias).fillna(0)  # unseen: bias 0
    return dict(global_mean=np.full(len(valid), mu), movie_mean=movie_mean.to_numpy(), bias_baseline=bias.to_numpy())


def nearest_items(item_emb, item_id, k=5):
    """Row numbers of the k rows of item_emb with the highest cosine similarity to row item_id, itself left out."""
    unit = item_emb / np.linalg.norm(item_emb, axis=1, keepdims=True)
    return [int(i) for i in np.argsort(-(unit @ unit[item_id])) if i != item_id][:k]


class DotProduct(Module):
    """One vector of n_factors numbers per user and per movie; the score is their dot product."""
    def __init__(self, n_users, n_movies, n_factors=50, y_range=(0, 5.5)):
        self.user_factors, self.movie_factors = Embedding(n_users, n_factors), Embedding(n_movies, n_factors)
        self.y_range = y_range

    def score(self, x):  # x holds (user, movie) code pairs, one row per rating
        return (self.user_factors(x[:, 0]) * self.movie_factors(x[:, 1])).sum(dim=1, keepdim=True)

    def forward(self, x):
        # Q: every rating is 1 to 5. Why squash the score into y_range (0, 5.5) and not (1, 5)?
        return sigmoid_range(self.score(x), *self.y_range)


class DotProductBias(DotProduct):
    """DotProduct plus one learned number per user and one per movie, added to the score."""
    def __init__(self, n_users, n_movies, n_factors=50, y_range=(0, 5.5)):
        super().__init__(n_users, n_movies, n_factors, y_range)
        self.user_bias, self.movie_bias = Embedding(n_users, 1), Embedding(n_movies, 1)

    def score(self, x):
        # Q: the movie bias is added to every user's predicted rating for that movie. What does a large positive one say?
        return super().score(x) + self.user_bias(x[:, 0]) + self.movie_bias(x[:, 1])


def predict(model, ds):  # score every (user, movie) row of a fastai dataset with the model's current weights
    with torch.no_grad():
        return model(torch.tensor(ds.xs.to_numpy(), dtype=torch.long)).squeeze(1).numpy()


class EpochRMSE(Callback):  # after each epoch: RMSE on every training rating and on every validation rating
    def after_epoch(self):
        for part, ds in (("train", self.dls.train_ds), ("valid", self.dls.valid_ds)):
            labkit.result(f"break.{part}_rmse_ep{self.epoch + 1:02d}", rmse(predict(self.model, ds), ds.ys), unit="stars")


def fit(dls, bias, wd, epochs, cbs=()):
    """Train DotProduct or DotProductBias with 50 factors; return the model and its validation RMSE."""
    model = (DotProductBias if bias else DotProduct)(len(dls.classes["user"]), len(dls.classes["title"]), n_factors=50)
    learn = Learner(dls, model, loss_func=MSELossFlat(), cbs=list(cbs))
    with learn.no_bar(), learn.no_logging():
        # Q: wd pulls weights toward zero a little at each step. Which tables in this model does it pull,
        # and what rating does a user get whose vector has been pulled to all zeros?
        learn.fit_one_cycle(epochs, 5e-3, wd=wd)
    return model, rmse(predict(model, dls.valid_ds), dls.valid_ds.ys)


def save_for_lab33(valid_idx, rmses):
    """Seed 0 only: lab 33 reuses this exact split (fastai RandomSplitter, valid_pct=0.2, seed=42) and these RMSEs."""
    path = labkit.DATA / "results" / "lab05.json"
    with labkit.locked(path):
        saved = json.loads(path.read_text()) if path.exists() else {"rmse": {}}
        saved["rmse"].update(rmses)  # dot_bias is from --change, break_valid from --break, the rest from --baseline
        saved.update(valid_idx=sorted(int(i) for i in valid_idx), about="valid_idx: 0-based u.data line numbers")
        path.write_text(json.dumps(saved))
    print(f"WROTE {path}")


if __name__ == "__main__":
    args = labkit.start(lab=5, device="cpu")
    if args.mode == "download":
        labkit.extract(labkit.fetch(URL, ZIP, size=4_924_029), ZIP.parent)
        sys.exit()
    if not (DIR / "u.data").exists():
        sys.exit("No data yet: run python scripts/05_recommender_embeddings.py --download")
    defaults.use_cuda = False  # fastai issue 3924: collab training crashes on Apple GPUs, so stay on the CPU
    ratings = pd.read_csv(DIR / "u.data", sep="\t", names=["user", "movie", "rating", "timestamp"])  # file order
    movies = pd.read_csv(DIR / "u.item", sep="|", encoding="latin-1", header=None, usecols=[0, 1], names=["movie", "title"])
    ratings["title"] = ratings["movie"].map(movies.set_index("movie")["title"])  # the title is the item id, as in fastbook
    ratings = ratings.iloc[:5000] if labkit.smoke() else ratings  # smoke checks the plumbing: every mode, 1 epoch
    dls = CollabDataLoaders.from_df(ratings, user_name="user", item_name="title", rating_name="rating",
                                    valid_pct=0.2, seed=42 + args.seed, bs=64, num_workers=0)
    train, valid = ratings.loc[dls.train_ds.items.index], ratings.loc[dls.valid_ds.items.index]
    print("NOTE this split is random; lab 19 shows what a random split hides", flush=True)
    base = {name: rmse(pred, valid["rating"]) for name, pred in baselines(train, valid).items()}
    for mode in (RUNS if labkit.smoke() else [args.mode]):
        cfg = dict(RUNS[mode], epochs=1) if labkit.smoke() else RUNS[mode]
        if mode == "baseline":
            for name, value in base.items():  # baseline.global_mean_rmse, .movie_mean_rmse, .bias_baseline_rmse
                labkit.result(f"baseline.{name}_rmse", value, unit="stars")
            saved = dict(base, dot=fit(dls, **cfg)[1])
            labkit.result("P1.dot_rmse", saved["dot"], unit="stars")
        elif mode == "change":
            model, dot_bias = fit(dls, **cfg)
            saved = dict(dot_bias=dot_bias)
            labkit.result("P2.dot_bias_rmse", dot_bias, unit="stars")
            if labkit.prior("P1.dot_rmse") is not None:  # the delta needs --baseline at the same seed first
                labkit.result("P2.delta_rmse", dot_bias - labkit.prior("P1.dot_rmse"), unit="stars")
            near = nearest_items(model.movie_factors.weight.detach().numpy(), dls.classes["title"].o2i[ANCHOR])
            if not labkit.smoke():  # smoke prints no results
                print(f"NOTE nearest to {ANCHOR} by cosine: {'; '.join(dls.classes['title'][i] for i in near)}", flush=True)
        else:
            saved = dict(break_valid=fit(dls, **cfg, cbs=[EpochRMSE()])[1])
            labkit.result("P3.valid_rmse", saved["break_valid"], unit="stars")
            labkit.result("P3.valid_minus_global_mean", saved["break_valid"] - base["global_mean"], unit="stars")
    if args.seed == 0 and not labkit.smoke():
        save_for_lab33(dls.valid_ds.items.index, saved)
