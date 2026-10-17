"""33. Embeddings from scratch: DotProductBias and what factors encode. DotProductBias in plain PyTorch on
lab 05's split, the first PCA axis of its movie rows, and the RMSE of users the model never saw.

Modes: --download, --smoke, --baseline (P1), --change (P2), --break (P3).
Reference: the starter's load_data() and report(), the learner's DotProductBias, then the AI's harness.
"""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "labkit.py").exists())))
import labkit  # before numpy and torch: it sets cache defaults
import numpy as np
import pandas as pd
import torch  # imported before labkit.start, so --seed seeds it
from torch import nn

URL = "https://files.grouplens.org/datasets/movielens/ml-100k.zip"
ZIP = labkit.DATA / "ml-100k" / "ml-100k.zip"
DIR = labkit.DATA / "ml-100k" / "ml-100k"
LAB05 = labkit.DATA / "results" / "lab05.json"  # written by lab 05 at seed 0: its split and its RMSEs
PRODUCER = "cd ../m1-whole-game && python scripts/05_recommender_embeddings.py"
CONTRACT = {  # the RESULT contract: every value this lab records, by mode, with its unit
    "baseline": {"P1.valid_rmse": "stars", "baseline.lab05_rmse": "stars", "baseline.minus_lab05": "stars"},
    "change": {"P2.valid_rmse": "stars", "P2.delta_rmse": "stars"},
    "break": {"P3.cold_rmse": "stars", "P3.closest": "choice", "break.warm_rmse": "stars",
              "break.cold_global_mean_rmse": "stars", "break.cold_movie_mean_rmse": "stars"}}
SKIPS = {"P2.delta_rmse": "run --baseline with the same seed first",  # why a value can be missing
         **dict.fromkeys(("baseline.lab05_rmse", "baseline.minus_lab05"), f"run {PRODUCER} --change first")}
RUNS = {"baseline": dict(n_factors=50, wd=0.1, epochs=5),  # P1
        "change": dict(n_factors=4, wd=0.1, epochs=5),     # P2: 4 factors instead of 50
        "break": dict(n_factors=50, wd=0.1, epochs=5)}     # P3: the baseline model, 50 users held out
LR, BS, N_COLD, TOP = 5e-3, 64, 50, 1000  # peak learning rate, batch, held-out users, titles in the PCA


def load_data(smoke=False):
    """Lab 05's split at every --seed: lab05.json's valid_idx (0-based u.data lines) validate, the rest train. Users and
    titles become codes u and i (the title is the item, as in lab 05). Smoke keeps the first 5,000 lines of u.data."""
    if not (DIR / "u.data").exists():
        sys.exit("No data yet: run python scripts/33_embeddings_from_scratch.py --download")
    lab05 = json.loads(LAB05.read_text()) if LAB05.exists() else {}
    if "valid_idx" not in lab05:
        print(f"MISSING {LAB05}: run lab 05 first: {PRODUCER} --baseline", flush=True)
        sys.exit(2)
    ratings = pd.read_csv(DIR / "u.data", sep="\t", names=["user", "movie", "rating", "timestamp"])  # file order
    movies = pd.read_csv(DIR / "u.item", sep="|", encoding="latin-1", header=None, usecols=[0, 1], names=["movie", "title"])
    ratings["title"] = ratings["movie"].map(movies.set_index("movie")["title"])
    ratings["u"], users = pd.factorize(ratings["user"], sort=True)
    ratings["i"], titles = pd.factorize(ratings["title"], sort=True)
    ratings = ratings.iloc[:5000] if smoke else ratings
    valid = ratings.index.isin(lab05["valid_idx"])
    return dict(train=ratings[~valid], valid=ratings[valid], all=ratings, n_users=len(users), n_items=len(titles),
                titles=list(titles), lab05_rmse=lab05.get("rmse", {}).get("dot_bias"))


def report(mode, values, notes=()):
    """Print this mode's RESULT lines in CONTRACT order (a missing value prints why), then NOTE lines."""
    for name, unit in CONTRACT[mode].items():
        if values.get(name) is None:
            print(f"SKIP {name}: {SKIPS.get(name, 'not computed')}", flush=True)
        else:
            labkit.result(name, values[name], unit=unit)
    for note in ([] if labkit.smoke() else notes):  # smoke prints no results
        print(f"NOTE {note}", flush=True)


class DotProductBias(nn.Module):
    """r_hat = sigmoid_range(user row . movie row + user bias + movie bias, 0, 5.5); every table starts N(0, 0.01)."""
    def __init__(self, n_users, n_items, n_factors=50):
        super().__init__()
        self.user_factors = nn.Parameter(torch.randn(n_users, n_factors) * 0.01)
        self.item_factors = nn.Parameter(torch.randn(n_items, n_factors) * 0.01)
        self.user_bias = nn.Parameter(torch.randn(n_users) * 0.01)
        self.item_bias = nn.Parameter(torch.randn(n_items) * 0.01)

    def forward(self, users, items):
        dot = (self.user_factors[users] * self.item_factors[items]).sum(dim=1)
        return 5.5 * torch.sigmoid(dot + self.user_bias[users] + self.item_bias[items])  # sigmoid_range(score, 0, 5.5)


def fit(train, n_users, n_items, n_factors, wd, epochs):
    """Lab 05's recipe in plain PyTorch: AdamW (decoupled weight decay, like fastai's Adam), one-cycle to LR, MSE."""
    model = DotProductBias(n_users, n_items, n_factors)
    users, items, ratings = (torch.tensor(train[c].to_numpy()) for c in ("u", "i", "rating"))
    opt = torch.optim.AdamW(model.parameters(), lr=LR, betas=(0.9, 0.99), eps=1e-5, weight_decay=wd)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=LR, total_steps=epochs * (len(train) // BS), pct_start=0.25)
    for _ in range(epochs):  # each row of the reshaped shuffle is one batch of 64; the last partial batch is dropped
        for b in torch.randperm(len(train))[:len(train) // BS * BS].view(-1, BS):
            loss = nn.functional.mse_loss(model(users[b], items[b]), ratings[b].float())
            opt.zero_grad()
            loss.backward()
            opt.step()
            sched.step()
    return model


def rmse(pred, target):  # in stars
    return float(np.sqrt(np.mean((np.ravel(pred).astype(float) - np.ravel(target)) ** 2)))


def model_rmse(model, df):  # the model's RMSE, in stars, on every (u, i, rating) row of df
    with torch.no_grad():
        return rmse(model(torch.tensor(df["u"].to_numpy()), torch.tensor(df["i"].to_numpy())).numpy(), df["rating"])


def pca_ends(model, train, titles, k=5):
    """The k titles at each end of the first principal axis of the movie rows of the TOP most-rated titles."""
    top = train["i"].value_counts().index.to_numpy()[:TOP]
    rows = model.item_factors.detach().numpy()[top]
    rows = rows - rows.mean(axis=0)
    axis = np.linalg.svd(rows, full_matrices=False)[2][0]  # the direction along which the rows spread most
    order = top[np.argsort(rows @ axis)]
    return [f"pca1 one end: {'; '.join(titles[i] for i in order[:k])}",
            f"pca1 other end: {'; '.join(titles[i] for i in order[::-1][:k])}"]


def cold_start(data, cfg, seed):
    """Hold out N_COLD random users (none of their ratings train), then score every rating they have."""
    cold_users = np.random.default_rng(seed).choice(np.unique(data["all"]["u"]), N_COLD, replace=False)
    train = data["train"][~data["train"]["u"].isin(cold_users)]
    cold = data["all"][data["all"]["u"].isin(cold_users)]
    warm = data["valid"][~data["valid"]["u"].isin(cold_users)]
    model = fit(train, data["n_users"], data["n_items"], **cfg)
    movie_mean = cold["i"].map(train.groupby("i")["rating"].mean()).fillna(train["rating"].mean())  # unseen: mu
    values = {"P3.cold_rmse": model_rmse(model, cold), "break.warm_rmse": model_rmse(model, warm),
              "break.cold_global_mean_rmse": rmse(np.full(len(cold), train["rating"].mean()), cold["rating"]),
              "break.cold_movie_mean_rmse": rmse(movie_mean, cold["rating"])}
    refs = dict(warm="break.warm_rmse", movie_mean="break.cold_movie_mean_rmse", global_mean="break.cold_global_mean_rmse")
    values["P3.closest"] = min(refs, key=lambda k: abs(values[refs[k]] - values["P3.cold_rmse"]))
    return values, [f"held-out users {N_COLD}, their ratings {len(cold)}, warm validation ratings {len(warm)}"]


args = labkit.start(lab=33, device="cpu")
if args.mode == "download":
    labkit.extract(labkit.fetch(URL, ZIP, size=4_924_029), ZIP.parent)
    print(f"HAVE {LAB05}" if LAB05.exists() else f"MISSING {LAB05}: run {PRODUCER} --baseline", flush=True)
    sys.exit()
data = load_data(smoke=labkit.smoke())
for mode in (RUNS if labkit.smoke() else [args.mode]):  # smoke checks the plumbing: every mode, 1 epoch
    cfg = dict(RUNS[mode], epochs=1) if labkit.smoke() else RUNS[mode]
    if mode == "break":
        report(mode, *cold_start(data, cfg, args.seed))
        continue
    model = fit(data["train"], data["n_users"], data["n_items"], **cfg)
    valid_rmse, lab05, p1 = model_rmse(model, data["valid"]), data["lab05_rmse"], labkit.prior("P1.valid_rmse")
    if mode == "baseline":
        report(mode, {"P1.valid_rmse": valid_rmse, "baseline.lab05_rmse": lab05,
                      "baseline.minus_lab05": None if lab05 is None else valid_rmse - lab05},
               notes=pca_ends(model, data["train"], data["titles"]))
    else:  # the delta needs --baseline at the same seed first
        report(mode, {"P2.valid_rmse": valid_rmse, "P2.delta_rmse": None if p1 is None else valid_rmse - p1})
