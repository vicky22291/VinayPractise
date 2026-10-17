"""33. Embeddings from scratch: DotProductBias and what factors encode. DotProductBias in plain PyTorch on
lab 05's split, the first PCA axis of its movie rows, and the RMSE of users the model never saw.

Modes: --download, --smoke, --baseline (P1), --change (P2), --break (P3).
Level S starter: load_data() and report() are given. You write DotProductBias from the formula in the lab
file, then the AI writes the harness for the three measured modes.
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


# Your DotProductBias goes here, from the formula in the lab file. The AI's harness goes below it.


if __name__ == "__main__":
    args = labkit.start(lab=33, device="cpu")
    if args.mode == "download":
        labkit.extract(labkit.fetch(URL, ZIP, size=4_924_029), ZIP.parent)
        print(f"HAVE {LAB05}" if LAB05.exists() else f"MISSING {LAB05}: run {PRODUCER} --baseline", flush=True)
        sys.exit()
    if args.mode != "smoke":
        raise NotImplementedError("write the harness: see the lab file")
    # smoke checks the plumbing only: the movie-mean prediction stands in for the model and harness you will write
    data = load_data(smoke=True)
    train, valid = data["train"], data["valid"]
    movie_mean = valid["i"].map(train.groupby("i")["rating"].mean()).fillna(train["rating"].mean())
    stand_in = float(np.sqrt(np.mean((movie_mean.to_numpy() - valid["rating"].to_numpy()) ** 2)))
    for mode, names in CONTRACT.items():
        report(mode, dict.fromkeys(names, stand_in), notes=["pca1 one end: (titles)", "pca1 other end: (titles)"])
