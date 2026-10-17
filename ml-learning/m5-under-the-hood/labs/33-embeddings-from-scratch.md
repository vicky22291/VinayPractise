# 33. Embeddings from scratch: DotProductBias and what factors encode

> Goal: after this I can write DotProductBias in plain PyTorch in about 10 lines, compare its RMSE (root mean squared error) with lab 05's fastai model on the same split, read the first PCA (principal component analysis) axis of the movie factors, and measure the RMSE of 50 users the model never saw (cold start). (No result values anywhere in this file.)

**Level:** S (see `ml-learning/CLAUDE.md`). **Output style:** Explanatory
**Concept link:** [`../README.md#what-embeddings-encode`](../README.md#what-embeddings-encode) (read after the lab)
**Borrowed from:** fast.ai Practical Deep Learning [Lesson 7, collaborative filtering](https://course.fast.ai/Lessons/lesson7.html); fastbook [chapter 8, collaborative filtering deep dive](https://github.com/fastai/fastbook/blob/master/08_collab.ipynb): "Weight Decay", "Creating Our Own Embedding Module", "Interpreting Embeddings and Biases" and "Bootstrapping a Collaborative Filtering Model". Do it after the lab, as the second contact 1 to 3 days later. The chapter prints results for a setup close to P1, so open it only after your runs.
**Dataset:** MovieLens 100K, 100,000 ratings (943 users with at least 20 each, 1,682 movies under 1,664 distinct titles; the title is the item, as in lab 05), 4.92 MB, https://files.grouplens.org/datasets/movielens/ml-100k.zip, GroupLens research use only, no redistribution. Split: lab 05's, read from `~/ml-data/results/lab05.json` (20,000 validation ratings, the other 80,000 train) at every `--seed`
**Runs on:** cpu. **Lane:** light. **Compute:** 3 runs x 1 min (baseline, change and break each finish within a minute in the seed-0 reference runs, rounded up), at most 6 min per run. Precomputed steps: none
**Needs:** base install only
**Before the session** (from the module folder, see section 2): lab 05 done at seed 0 (its `--baseline` and `--change` write `~/ml-data/results/lab05.json`: the split and lab 05's RMSEs). Then `--download` (it reuses lab 05's zip in `~/ml-data/ml-100k/` and says HAVE or MISSING for lab05.json), then `--smoke`. Neither prints a result value: `--smoke` prints `SMOKE <name> ok` lines.
**Interview question:** What does a learned item embedding encode, and how do you serve nearest neighbours for 10 M items in RAM?
**Repo link:** [`concepts/vector-index.md`, §3 Quantization: fitting in RAM](../../../concepts/vector-index.md#3-quantization-fitting-in-ram) and [`hld/news-aggregator/deep-dives/ranking-and-cold-start.md`, §7 Cold start, and moving to a learned model](../../../hld/news-aggregator/deep-dives/ranking-and-cold-start.md#7-cold-start-and-moving-to-a-learned-model)
**Captured by the script:** P1, P2, P3 and every Record row except your name for the first PCA axis. **Human steps:** none
**Status:** todo

## 0. Retrieval (0:00, 5 min, closed book, no AI)

The AI asks up to three due cards from `../../quiz-bank.md`, one at a time. Do not open the bank first.

## 1. Predict (0:05, 7 min, no AI)

Level S: first read `load_data()` and `report()` in `scripts/33_embeddings_from_scratch.py` (2 minutes). They fix the split and the RESULT names your harness must print. There is no model to read yet: predict from the configs in the table.

Write each row here before anything runs; the AI copies it into `../../prediction-log.md` word for word. A row that asks for several numbers becomes one log row per number, each with its own range.

| Step | Question | Kind | Prediction | 80% range or confidence |
|---|---|---|---|---|
| P1 | Validation RMSE of your DotProductBias with 50 factors, weight decay 0.1 and 5 epochs (AdamW, one-cycle schedule to learning rate 5e-3, batch 64, seed 0) on lab 05's split: 80,000 training ratings, 20,000 validation ratings, in stars. | num | | |
| P2 | 4 factors instead of 50, everything else as P1 (seed 0): validation RMSE direction (up, down or same) and size, as the RMSE difference 4 factors minus 50 factors, in stars. | dir | | |
| P3 | Hold out 50 random users (seed 0): none of their ratings train P1's model (50 factors). Score all their ratings. Is their RMSE closest to (a) the warm users' RMSE, from the same model on lab 05's validation ratings of the other 893 users, (b) the movie-mean baseline on the held-out ratings, or (c) the global-mean baseline on them? Pick one, with a confidence. | pick | | |

## 2. Setup (before the session)

```
$ source ~/.venvs/ml/bin/activate
$ cd m5-under-the-hood    # from ml-learning/, where sessions start
$ python scripts/33_embeddings_from_scratch.py --download
$ python scripts/33_embeddings_from_scratch.py --smoke
```

## 3. Baseline (0:12, 10 min)

Why: this is lab 05's DotProductBias written by hand and trained on lab 05's split, so the two RMSEs compare directly.

You write these first, with no AI (about 5 minutes). Each blank in items 1 and 2 takes one line.

1. The model plan, in your own words. Item 3 gives the formula; these lines ask for the reasons behind it.
   - Why picking row i of a table is the same as multiplying a one-hot vector by the table:
   - Why the score goes through sigmoid_range(score, 0, 5.5) and not straight out as the rating:
   - Why every table starts from N(0, 0.01) and not from N(0, 1):
2. `load_data()` and `report()` already exist: say what they fix, what `--seed` changes, and what each mode passes to `report()`. Every RMSE is in stars, against the true rating.
   - Split:
   - Metric:
   - RESULT contract:
3. `DotProductBias(n_users, n_items, n_factors)` in `scripts/33_embeddings_from_scratch.py`, an `nn.Module`, from this formula:
   - Four tables, each an `nn.Parameter` drawn from N(0, 0.01): `user_factors` (n_users x n_factors), `item_factors` (n_items x n_factors), `user_bias` (n_users) and `item_bias` (n_items). The harness reads `item_factors` for the PCA, so keep these names.
   - `forward(users, items)` takes two LongTensors of codes and returns one predicted rating per pair: r_hat = 5.5 x sigmoid(user row · movie row + user bias + movie bias), which is sigmoid_range(score, 0, 5.5).

Then prompt the AI with your plan and the three lines of item 2. It writes the harness for all three modes in one pass, and it has to cover:

- Training, for every mode: `torch.optim.AdamW` (decoupled weight decay, the form fastai's `Adam` used in lab 05) with betas (0.9, 0.99) and eps 1e-5, `OneCycleLR` to a peak of 5e-3 with pct_start 0.25, MSE (mean squared error) loss, 5 epochs, batches of 64 cut from a fresh random permutation of the training ratings each epoch, the last partial batch dropped.
- Baseline: 50 factors, weight decay 0.1. The validation RMSE, lab 05's DotProductBias RMSE from `lab05.json` and the difference. Then the PCA: the `item_factors` rows of the 1,000 most-rated titles in the training ratings, centred, projected on the first right singular vector, and the 5 titles at each end as two `NOTE pca1` lines.
- Change: 4 factors, with the RMSE delta from the baseline run at the same seed (`labkit.prior`).
- Break: 50 users drawn with `np.random.default_rng(seed)`, all their ratings dropped from the training set, then P1's model trained on the rest. Score every rating of the 50 users (cold), lab 05's validation ratings of the other users (warm), and two baselines on the cold ratings from the break's training ratings: the global mean, and each movie's mean (the global mean for a movie with no training rating). `P3.closest` names whichever of warm, movie_mean and global_mean has the RMSE nearest the cold RMSE.

Annotate each AI block in one line before the first run. If this block runs over, the change step absorbs it: the harness already covers `--change`, and that run is short, so the break still finishes by 0:40.

```
$ python scripts/33_embeddings_from_scratch.py --baseline
(paste your RESULT lines)
```

Read the two `NOTE pca1` lines and name the axis in the Record table: what do the 5 titles at one end share that the 5 at the other end lack? Its sign is arbitrary.

Prediction vs actual, one sentence. The reference run is in `../../answers/`; the AI opens it only after your P1 row exists and you have pasted your own RESULT lines.

## 4. Change one thing (0:22, 10 min)

Why: the factor count sets how many numbers each row holds; 4 factors leave each user and each movie four taste numbers plus the two biases.

Change: 4 factors instead of 50 (weight decay 0.1, 5 epochs, seed 0). It prints the change against your baseline run at the same seed, so run `--baseline` first. P2 is logged above.

```
$ python scripts/33_embeddings_from_scratch.py --change
(paste your RESULT lines)
```

## 5. Break it (0:32, 10 min, AI gives hints only; the run finishes by 0:40)

Why: every MovieLens 100K user has at least 20 ratings, so a random split of ratings almost never tests a brand-new user. This run makes 50 of them.

Break: hold out 50 users entirely (none of their ratings in training), then score all their ratings. P3 is logged above.

```
$ python scripts/33_embeddings_from_scratch.py --break
(paste your RESULT lines)
```

Why, in three sentences, written without AI:

## 6. Explain-back (0:42, 5 min) and rebuild (0:47, 10 min), no AI

- Five sentences for a smart engineer new to ML, written without AI. The AI names your weakest claim after the session (section 7).
- Rebuild: at 0:47, not before, open `rebuild/33_dot_product_bias.py`, write the bodies of `DotProductBias` and `train_step` from memory, then run `python rebuild/33_dot_product_bias.py`. Its `train_step` is not your lab harness: it takes one step of plain SGD (stochastic gradient descent) with an explicit L2 term, (wd / 2) x the sum of every parameter squared, in the loss. Its `check()` compares with PyTorch (`torch.optim.SGD(weight_decay=wd)`, to 1e-6) on synthetic ratings, never with this lab's results.

## 7. What I learned

After the session (about 5 minutes): the AI names the weakest claim in your five sentences and asks one question that tests it. Edit the sentences here.

## 8. Interview soundbite (one of the three cards written at 0:57)

> (Your soundbite: one or two sentences only someone who ran this would say.)

Staff follow-up (cost): the catalogue grows to 10 M items at 50 float32 factors each. How much RAM does the flat table take, and what do int8 scalar quantization and PQ (product quantization) save, at what recall cost? Answer in 2 sentences from the repo link (`vector-index.md` §3). Rotate: simplest design, failure modes, migration, what pages at 3 am, cost, trade-off.

## 9. Quiz cards (0:57, 3 min)

The AI drafts three cards (M, N, and T or D). Edit or replace them. Questions go to `../../quiz-bank.md`, keys to `../../answers/quiz-key.md`.

## Record

The script prints these as RESULT lines, plus two `NOTE pca1` lines in `--baseline`. Paste, do not type.

| Metric | Your run | Hardware (the script's HW line) | Captured by (script or learner) |
|---|---|---|---|
| `P1.valid_rmse`: your DotProductBias, 50 factors, validation RMSE on lab 05's split | | | script |
| `baseline.lab05_rmse`: lab 05's fastai DotProductBias on the same split, read from `lab05.json` | | | script |
| `baseline.minus_lab05`: yours minus lab 05's | | | script |
| The 5 titles at each end of the first PCA axis (the two `NOTE pca1` lines), and your name for the axis | | | learner |
| `P2.valid_rmse`: 4 factors, validation RMSE | | | script |
| `P2.delta_rmse`: 4 factors minus 50 factors (needs `--baseline` run first with the same seed) | | | script |
| `P3.cold_rmse`: the 50 held-out users, all their ratings | | | script |
| `P3.closest`: warm, movie_mean or global_mean, whichever RMSE sits nearest the cold RMSE | | | script |
| `break.warm_rmse`: the same model on lab 05's validation ratings of the other users | | | script |
| `break.cold_global_mean_rmse`: the mean training rating, scored on the cold ratings | | | script |
| `break.cold_movie_mean_rmse`: each movie's mean training rating, scored on the cold ratings | | | script |
