# 05. Recommender: embeddings learned from ratings

> Goal: after this I can train a dot-product recommender in under 2 minutes on the CPU and say how far its RMSE (root mean squared error) is from three baselines that learn no vectors: the global mean, the movie mean and a damped user-plus-movie bias. (No result values anywhere in this file.)

**Level:** W (see `ml-learning/CLAUDE.md`). **Output style:** Explanatory
**Concept link:** [`../README.md#embeddings-from-ratings`](../README.md#embeddings-from-ratings) (read after the lab)
**Borrowed from:** fast.ai Practical Deep Learning [Lesson 7, collaborative filtering](https://course.fast.ai/Lessons/lesson7.html); fastbook [chapter 8, collaborative filtering deep dive](https://github.com/fastai/fastbook/blob/master/08_collab.ipynb), cells 62 to 105. Do it after the lab, as the second contact 1 to 3 days later. Those cells print results for setups close to P1 to P3, so open them only after your runs.
**Dataset:** MovieLens 100K, 100,000 ratings (943 users, 1,682 movies), 4.92 MB, https://files.grouplens.org/datasets/movielens/ml-100k.zip, GroupLens research use only, no redistribution
**Runs on:** cpu. **Lane:** light. **Compute:** 3 runs x at most 2 min (baseline 1, change 2, break 2, rounded up from the seed-0 reference runs), at most 6 min per run. Precomputed steps: none
**Needs:** base install only
**Before the session** (from the module folder, see section 2): `--download` (the 4.92 MB zip into `~/ml-data/ml-100k/`), then `--smoke`. Neither prints a result value: `--smoke` prints `SMOKE <name> ok` lines.
**Interview question:** Recommend movies for a user with 20 ratings and for a brand-new user: what baseline must the model beat, and what does a random split hide?
**Repo link:** [`hld/news-aggregator/deep-dives/ranking-and-cold-start.md`](../../../hld/news-aggregator/deep-dives/ranking-and-cold-start.md), [§7 Cold start, and moving to a learned model](../../../hld/news-aggregator/deep-dives/ranking-and-cold-start.md#7-cold-start-and-moving-to-a-learned-model) and [§8 Feedback loops and popularity bias](../../../hld/news-aggregator/deep-dives/ranking-and-cold-start.md#8-feedback-loops-and-popularity-bias)
**Captured by the script:** P1, P2, P3, the three baselines, train and validation RMSE after every epoch of the break run, the split note, and the `--change` note naming the 5 movies nearest to Star Wars (1977). **Human steps:** none
**Status:** todo

## 0. Retrieval (0:00, 5 min, closed book, no AI)

The AI asks up to three due cards from `../../quiz-bank.md`, one at a time. Do not open the bank first.

## 1. Predict (0:05, 7 min, no AI)

Level W only: before the session, read `scripts/05_recommender_embeddings.py` (about 10 minutes) and answer its three `# Q:` prompts here. At 0:05 you only predict. Read `DotProduct`, `DotProductBias` and `fit` first: the three prompts sit there. Then read `rmse`, `baselines` and `nearest_items`, which you rebuild at 0:47. Skip the rest: download, smoke and the file for lab 33.

- Q1, `y_range` (0, 5.5):
- Q2, a large positive movie bias:
- Q3, what `wd` (weight decay) pulls toward zero:

Write each row here before anything runs; the AI copies it into `../../prediction-log.md` word for word. A row that asks for several numbers becomes one log row per number, each with its own range.

| Step | Question | Kind | Prediction | 80% range or confidence |
|---|---|---|---|---|
| P1 | Validation RMSE, in stars, of `DotProduct`: 50 factors, no bias terms, weight decay 0.1, 5 epochs of fastai's one-cycle schedule at a peak learning rate of 5e-3, batch 64, random 80/20 split with seed 42 (`--seed 0`). | num | | |
| P2 | Add the user and movie bias terms (`DotProduct` to `DotProductBias`), everything else as P1: does validation RMSE go up, down or stay the same, and by how much (`P2.delta_rmse`)? | dir | | |
| P3 | Weight decay 0 for 20 epochs, `DotProduct` with no bias terms, everything else as P1: does the final validation RMSE end above or below the global-mean baseline? | pick | | |

## 2. Setup (before the session)

```
$ source ~/.venvs/ml/bin/activate
$ cd m1-whole-game    # from ml-learning/, where sessions start
$ python scripts/05_recommender_embeddings.py --download
$ python scripts/05_recommender_embeddings.py --smoke
```

At `--seed 0` each measured run also saves the split and its RMSEs to `~/ml-data/results/lab05.json`. Lab 33 reads that file.

## 3. Baseline (0:12, 10 min)

Why: a learned model earns its keep only by beating predictions with no learned vectors, so three baselines print before the model trains: the global mean, the movie mean, and the global mean plus a damped user bias and a damped movie bias.

```
$ python scripts/05_recommender_embeddings.py --baseline
(paste your RESULT lines)
```

Prediction vs actual, one sentence. The reference run is in `../../answers/`; the AI opens it only after your P1 row exists and you have pasted your own RESULT lines.

## 4. Change one thing (0:22, 10 min)

Why: a bias is one number per user and one per movie, outside the dot product; this run isolates what it changes.

Change: add the user and movie bias terms (`DotProduct` to `DotProductBias`); the factors, weight decay, epochs and split stay as in the baseline. P2 is logged above.

The run also prints one `NOTE` line: the 5 movies whose learned vectors have the highest cosine similarity to the vector of Star Wars (1977). It is this lab's only look inside the embeddings, and no prediction asks about it.

```
$ python scripts/05_recommender_embeddings.py --change
(paste your RESULT lines)
```

## 5. Break it (0:32, 10 min, AI gives hints only; the run finishes by 0:40)

Why: P1 fixed weight decay at 0.1 and stopped at 5 epochs without testing either choice. This run removes the decay, trains 4 times as long, and prints train and validation RMSE after every epoch, so you see the whole path, not only the end point.

Break: train `DotProduct` (no bias terms, as in the baseline) with weight decay 0 for 20 epochs. P3 is logged above.

```
$ python scripts/05_recommender_embeddings.py --break
(paste your RESULT lines)
```

Why, in three sentences, written without AI:

## 6. Explain-back (0:42, 5 min) and rebuild (0:47, 10 min), no AI

- Five sentences for a smart engineer new to ML, written without AI. The AI names your weakest claim after the session (section 7).
- Rebuild: open `rebuild/05_baselines.py`, write its four bodies from memory, then run `python rebuild/05_baselines.py`. Three are retypes of code you read in the script: `rmse`, `bias_baseline` (the damped part of the script's `baselines`, with `movie` where the script has `title`) and `nearest_items`. The fourth, a seeded 90/10 `split`, is the one piece the script leaves to fastai (`valid_pct=0.2, seed=42`), so write it from its docstring. The file's `check()` compares with scikit-learn (`mean_squared_error` and `NearestNeighbors(metric="cosine")`), never with this lab's results.

## 7. What I learned

After the session (about 5 minutes): the AI names the weakest claim in your five sentences and asks one question that tests it. Edit the sentences here.

## 8. Interview soundbite (one of the three cards written at 0:57)

> (your one or two sentences, written after the runs: something only someone who ran this would say)

Staff follow-up (failure modes): a recommender's offline RMSE on a random split of logged ratings looks good enough to ship. Name two ways it can still lose online, and say how you would launch it. Answer in 2 sentences from §7 (offline vs online, rollout) and §8 (feedback loops) of the repo link. Rotate: simplest design, failure modes, migration, what pages at 3 am, cost, trade-off.

## 9. Quiz cards (0:57, 3 min)

The AI drafts three cards (M, N, and T or D). Edit or replace them. Questions go to `../../quiz-bank.md`, keys to `../../answers/quiz-key.md`.

## Record

The script prints these as RESULT lines. Paste, do not type.

| Metric | Your run | Hardware (the script's HW line) | Captured by (script or learner) |
|---|---|---|---|
| `baseline.global_mean_rmse` | | | script |
| `baseline.movie_mean_rmse` | | | script |
| `baseline.bias_baseline_rmse` (the global mean plus a damped user bias and a damped movie bias) | | | script |
| `P1.dot_rmse` | | | script |
| `P2.dot_bias_rmse` | | | script |
| `P2.delta_rmse` (printed when `--baseline` ran first at the same seed) | | | script |
| The `NOTE` line from `--change`: the 5 movies nearest to Star Wars (1977) by cosine | | | script |
| `break.train_rmse_ep01` to `break.train_rmse_ep20`, one line per epoch | | | script |
| `break.valid_rmse_ep01` to `break.valid_rmse_ep20`, one line per epoch | | | script |
| `P3.valid_rmse` | | | script |
| `P3.valid_minus_global_mean` | | | script |
| The `NOTE` line: this split is random; lab 19 shows what a random split hides | | | script |
