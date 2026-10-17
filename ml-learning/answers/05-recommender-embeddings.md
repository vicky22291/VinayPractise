# 05. Recommender: embeddings learned from ratings: reference answers

> Spoilers. The AI opens one block at a time, only after that step's prediction row exists and the learner pasted their own RESULT lines, or after 'debrief 05'.

- HW line: `HW chip='Apple M4 Pro' cpu=14 gpu=20 mem_gib=24 macos=26.5.1 python=3.13.7 torch=2.14.1 device=cpu`
- Seeds: 0, 1 and 2 for every step (light lane). `--seed S` sets the split seed to 42 + S and also drives the initial vectors and the batch order, so every spread below includes a new 80/20 split.
- Reference script: `m1-whole-game/scripts/05_recommender_embeddings.py` (level W: the learner's script is the reference), sha256 prefix `adb9d394465b49e7`. Values: [`05-recommender-embeddings.json`](05-recommender-embeddings.json). Seed-0 logs: [`05-recommender-embeddings.out`](05-recommender-embeddings.out).
- Precomputed steps: none.
- Tolerance rule: tol = spread (max - min) over seeds 0, 1, 2; heavy labs: the baseline spread applies to every step.

Runs and wall times in seconds (light lane, CPU slots shared with other builds):

| Mode | Seed 0 | Seed 1 | Seed 2 |
|---|---|---|---|
| baseline | 45.9 | 60.2 | 62.8 |
| change | 61.9 | 64.9 | 61.4 |
| break | 84.7 | 110.5 | 121.4 |

<details><summary>P1. Validation RMSE of DotProduct: 50 factors, no bias terms, weight decay 0.1, 5 epochs, seed 0</summary>

**Answer:** 0.923509 stars, tolerance ±0.010173 (the seed spread of `P1.dot_rmse`).

Seed-0 RESULT lines:

```
RESULT baseline.global_mean_rmse=1.1179 unit=stars seed=0
RESULT baseline.movie_mean_rmse=1.01814 unit=stars seed=0
RESULT baseline.bias_baseline_rmse=0.949938 unit=stars seed=0
RESULT P1.dot_rmse=0.923509 unit=stars seed=0
```

| Value | Seed 0 | Seed 1 | Seed 2 | Spread |
|---|---|---|---|---|
| `baseline.global_mean_rmse` | 1.1179 | 1.12532 | 1.12065 | 0.00742 |
| `baseline.movie_mean_rmse` | 1.01814 | 1.02917 | 1.02335 | 0.01103 |
| `baseline.bias_baseline_rmse` | 0.949938 | 0.959282 | 0.95758 | 0.009344 |
| `P1.dot_rmse` | 0.923509 | 0.933682 | 0.93317 | 0.010173 |

**Why:** The global mean predicts one number for every rating, so its RMSE is the spread of the ratings themselves. The movie mean removes the "which movie" part of that spread (1.01814), and the damped bias baseline also removes "this user rates high or low" (0.949938), still with no learned vectors. The dot product is below that bar at all three seeds, on average by 0.0254797 against a spread of 0.010173, because its 50 numbers per user and per movie also learn which users like which kind of movie, and weight decay 0.1 keeps them small enough to hold shared taste rather than single ratings. The seed spread is mostly the split: the global-mean baseline has no randomness of its own and still moves by 0.00742 across the three splits.

**Common wrong prediction:** an RMSE near 0.5, as if a trained model gets most ratings nearly right. Ratings are whole stars from 1 to 5, and even the trained model misses by most of a star on a typical rating.

</details>

<details><summary>P2. Add the user and movie bias terms (DotProduct to DotProductBias): RMSE direction and size</summary>

**Answer:** down, by a few thousandths of a star: `P2.delta_rmse` = -0.00580384 at seed 0, tolerance ±0.0021433 (the seed spread of `P2.delta_rmse`). Grade the size on the delta: it is paired (same split, same starting factor vectors), so the split noise cancels. `P2.dot_bias_rmse` itself is 0.917706, ±0.011804.

Seed-0 RESULT lines, then the run's NOTE line (copied from the .out; mkanswers does not parse NOTE lines):

```
RESULT P2.dot_bias_rmse=0.917706 unit=stars seed=0
RESULT P2.delta_rmse=-0.00580384 unit=stars seed=0
NOTE nearest to Star Wars (1977) by cosine: Empire Strikes Back, The (1980); Return of the Jedi (1983); Raiders of the Lost Ark (1981); Man Who Would Be King, The (1975); Indiana Jones and the Last Crusade (1989)
```

| Value | Seed 0 | Seed 1 | Seed 2 | Spread |
|---|---|---|---|---|
| `P2.dot_bias_rmse` | 0.917706 | 0.928691 | 0.92951 | 0.011804 |
| `P2.delta_rmse` | -0.00580384 | -0.00499015 | -0.00366054 | 0.0021433 |

**Why:** A bias is one number per user and one per movie, added outside the dot product, so "everyone likes this movie" costs one number instead of a pattern spread across 50 factors. The 50 free factors had already learned most of that offset (a factor on which most users have a positive weight works like a movie bias), so the explicit biases help at all three seeds, but only a little. Users keep many ratings in training: every user has at least 20 in the full data, and the seed-0 training split still gives each user at least 12, the median user 52. Biases earn more where data is thin, such as a new user or a rare movie, and a random split, whose validation ratings fall mostly on popular movies, barely tests that case.

Nearest movies (the NOTE line of each seed's change log; seeds 1 and 2 are in ledger jobs 05-change-s1-154734-53487 and 05-change-s2-154841-56157): the two Star Wars sequels are the top two at all three seeds, Raiders of the Lost Ark is third at seeds 0 and 2, and the other places change with the seed. Nobody named the 50 factors, yet movies that the same users rate alike end up pointing the same way. No prediction asks about this line.

**Common wrong prediction:** a drop of several hundredths, because popularity is a large part of a rating. It is (P1's movie-mean baseline shows it), but the 50-factor model had already learned it.

Effect check: the mean change over the three seeds is -0.004818 against a raw seed spread of 0.011804, below the build's 2x rule. The build notes explain why the knob was not changed.

</details>

<details><summary>P3. Weight decay 0 for 20 epochs: does validation RMSE end above or below the global-mean baseline?</summary>

**Answer:** above, at all three seeds. At seed 0 `P3.valid_rmse` is 1.17451 against the global mean's 1.1179: `P3.valid_minus_global_mean` = 0.056606, tolerance ±0.0063443. The `P3.valid_rmse` spread is ±0.0012. Any confidence on "above" scores as a hit.

Seed-0 RESULT lines (the per-epoch lines are in the table below):

```
RESULT P3.valid_rmse=1.17451 unit=stars seed=0
RESULT P3.valid_minus_global_mean=0.056606 unit=stars seed=0
```

| Value | Seed 0 | Seed 1 | Seed 2 | Spread |
|---|---|---|---|---|
| `P3.valid_rmse` | 1.17451 | 1.17558 | 1.17571 | 0.0012 |
| `P3.valid_minus_global_mean` | 0.056606 | 0.0502617 | 0.0550587 | 0.0063443 |
| `break.train_rmse_ep20` | 0.255702 | 0.254065 | 0.256854 | 0.002789 |

Per-epoch RMSE at seed 0 (`break.train_rmse_epNN` and `break.valid_rmse_epNN`):

| Epoch | Train RMSE | Validation RMSE |
|---|---|---|
| 1 | 1.26816 | 1.27308 |
| 2 | 0.953255 | 0.977926 |
| 3 | 0.872792 | 0.947665 |
| 4 | 0.751086 | 0.956295 |
| 5 | 0.638387 | 0.997625 |
| 6 | 0.564905 | 1.0346 |
| 7 | 0.515357 | 1.06676 |
| 8 | 0.484043 | 1.0873 |
| 9 | 0.450504 | 1.10674 |
| 10 | 0.420639 | 1.12191 |
| 11 | 0.395269 | 1.13086 |
| 12 | 0.366551 | 1.14247 |
| 13 | 0.339636 | 1.1494 |
| 14 | 0.314083 | 1.15796 |
| 15 | 0.2943 | 1.16398 |
| 16 | 0.277931 | 1.16914 |
| 17 | 0.266229 | 1.17155 |
| 18 | 0.259243 | 1.17375 |
| 19 | 0.256188 | 1.17438 |
| 20 | 0.255702 | 1.17451 |

**Why:** With weight decay 0 nothing shrinks the vectors, so they grow until their dot products reproduce each training rating: train RMSE falls every epoch, to 0.255702. Validation RMSE is lowest at epoch 3 (0.947665), then rises every epoch and passes the global mean between epochs 9 and 10 (1.10674, then 1.12191, against 1.1179). For a user and movie pair it never saw, the model multiplies two large memorized vectors, so the score lands far from zero and the sigmoid pushes the prediction toward 0 or 5.5: confident, large misses.

Curve note: epoch 1 is above the global mean too, for another reason. The vectors start near zero, so every prediction sits near the sigmoid's middle, 2.75, and one-cycle starts at a small learning rate.

**Common wrong prediction:** below, because a trained model cannot do worse than the average. It can: weight decay and stopping at 5 epochs are what kept the same model below all three baselines in P1.

</details>

<details><summary>Rebuild check</summary>

Solution: [`rebuild/05_baselines.py`](rebuild/05_baselines.py). Stub: `m1-whole-game/rebuild/05_baselines.py`. Verdict from `rebuildcheck`: the stub fails as it should (exit 1, NotImplementedError), the solution passes (exit 0, `check: PASS`): REBUILDCHECK OK. `check()` compares `rmse` with the square root of `sklearn.metrics.mean_squared_error` and `nearest_items` with `sklearn.neighbors.NearestNeighbors(metric="cosine")` on a random 30 x 8 matrix. It tests `bias_baseline` on a complete additive toy matrix (damping 0 recovers every rating, a huge damping gives the global mean, an unseen user and movie get the global mean) and `split` on sizes, coverage and seeding.

Three of the four bodies are retypes of script code: the script's `rmse`, the damped part of its `baselines` and its `nearest_items` give the same output as the solution's `rmse`, `bias_baseline` and `nearest_items` (a build inspection on a 100,000-row split and a random 40 x 6 matrix). `split` is written from its docstring, because the script leaves the split to fastai.

</details>

<details><summary>Card drafts</summary>

| ID | Lab | Type | Question |
|---|---|---|---|
| 05-M | 05 | M | A dot-product recommender trained with weight decay 0 for 20 epochs ends worse on held-out ratings than predicting the global mean. What happens inside the model to cause that? |
| 05-N | 05 | N | On MovieLens 100K with a random 80/20 split, what validation RMSE does the global mean plus a damped user bias and a damped movie bias score (no learned vectors), and why is that the bar for a user with 20 ratings? |
| 05-D | 05 | D | A recommender's train RMSE falls every epoch while its validation RMSE rises after the first few epochs. What do you check first? |

Keys:

- 05-M: (1) nothing shrinks the user and movie vectors, so they grow until they reproduce each training rating (train RMSE 0.255702 at seed 0); (2) for an unseen pair, two large vectors give a large score that the sigmoid pushes toward 0 or 5.5. Not graded: weight decay is what keeps the vectors small, so unseen pairs stay near sensible ratings.
- 05-N: (1) about 0.95: 0.949938 at seed 0, seed spread 0.009344, and a hit is within 0.03 of it (0.92 to 0.98); (2) a user with 20 ratings has a known bias, and so does every movie, so the bar already holds "this user rates high or low" and "everyone likes this movie": a model beats it only by learning taste, as the 50-factor dot product did, on average 0.0254797 lower. Not graded, the interview question's other half: for a brand-new user the user bias is 0, so the bar falls back to the movie mean, which is popularity (the movie-mean baseline's 1.01814 at seed 0 is over known users only: this split holds no brand-new user).
- 05-D: (1) the training call's regularization: is weight decay set at all (0, or not passed, which leaves fastai's 0.01), and is the epoch count past the epoch with the lowest validation RMSE (epoch 3, 0.947665, in this lab's break run at seed 0). Not graded, the next check: compare validation RMSE with the global-mean baseline on the same split, to see whether the model now does worse than a prediction that learns nothing.

</details>

<details><summary>Build notes</summary>

- Knob changes: none. Precomputed steps: none; the slowest seed-0 run (break) took 84.7 s.
- Review round (script sha256 prefix adb9d394465b49e7): the script gained a warnings filter, a third baseline, a nearest-movies NOTE line and two reworded `# Q:` prompts, so all 9 reference runs were rerun. Every value the earlier version printed came out identical, because the new code draws no random numbers.
  - The filter hides one FutureWarning (`torch.jit.script` is deprecated) that the fastai import printed to stderr, so every log and the .out now start with the HW and SEED lines.
  - The first seed-0 break run of this version (job 05-break-s0-155011-59428) shared the CPU with two heavy and two light runs from other labs, so its wall time did not represent the lab. It was rerun once (job 05-break-s0-160011-91355) with identical RESULT lines, and mkanswers keeps the rerun.
  - To stay at 150 lines, load_ratings() moved into the `__main__` block (which replaced main()), each pair of embeddings shares one line, and two plumbing helpers (predict and EpochRMSE) carry a comment instead of a docstring.
- Rebuild alignment (level W: the rebuild is a retype of code the learner read). The spec's rebuild is rmse, a damped bias_baseline, nearest_items by cosine and a seeded 90/10 split; the earlier script held only rmse. Now baselines() also computes the damped user-plus-movie bias (damping 5), printed as `baseline.bias_baseline_rmse`, and --change calls nearest_items on movie_factors. A build inspection found both give the same output as the rebuild solution's functions. split stays fastai's RandomSplitter in the script, because the spec fixes CollabDataLoaders(valid_pct=0.2, seed=42) and lab 33 reads that exact split; the lab file says to write split from its docstring. The model itself is not rebuilt here: lab 33's rebuild is DotProductBias plus a training step.
- Deviation from the spec's record: `baseline.bias_baseline_rmse` and the --change NOTE line are additions. The NOTE names the 5 titles whose movie_factors rows have the highest cosine similarity to Star Wars (1977). It prints at every seed, never in smoke, and only the seed-0 line is in the .out. Effect P1 vs the bias baseline: mean -0.0254797 against a spread of 0.010173, so it passes the 2x rule, and `P1.dot_rmse` is below `baseline.bias_baseline_rmse` at all three seeds.
- Models: P1 has no bias terms and collab_learner always adds them, so the script uses fastbook's DotProduct (fastai Embedding, init std 0.01, sigmoid_range into y_range (0, 5.5)) with Learner, MSELossFlat and fit_one_cycle(5, 5e-3, wd=0.1). The change uses DotProductBias, the same class plus one user and one movie bias embedding, so the bias terms are the only difference; at the same seed both models start from the same factor vectors.
- Break model (the spec names only wd and epochs): DotProduct with no bias terms, as in P1, with wd 0 and 20 epochs, so each step differs from the baseline in one place. The script passes wd=0.0 explicitly, because fastai's Adam applies wd 0.01 when wd is not passed.
- Split: CollabDataLoaders.from_df(item_name='title', valid_pct=0.2, seed=42 + --seed, bs=64). --seed 0 gives the spec's seed 42, and the seed also drives the initial vectors and the batch order, so every seed spread includes a new split. Ratings keep u.data line order (pandas 2.3.3 map and merge both keep it), so the validation indices are u.data line numbers and equal fastai RandomSplitter(valid_pct=0.2, seed=42).
- Items are titles, as in fastbook: 1,664 titles for 1,682 movie ids. fastai's df_shrink turns the title column into a pandas category before Categorify, so every title gets an embedding row, including titles seen only in validation.
- Baselines: the movie mean is the plain mean of each title's training ratings, and a title missing from training gets the global mean. The bias baseline is the global mean, plus each user's residual sum over (count + 5), plus each title's residual sum over (count + 5) on what the user bias left; an unseen user or title adds 0. It is the rebuild's bias_baseline, keyed by title.
- Per-epoch train and validation RMSE: a callback scores the full training set and the full validation set with the current weights after each epoch (not fastai's smoothed train loss).
- Record table: the lab file groups the 40 per-epoch names (break.train_rmse_ep01 to ep20 and break.valid_rmse_ep01 to ep20) into two rows, not one row per name as BRIEF section 6 asks, so the table stays readable. The script prints all 40, and the P3 block lists the seed-0 values.
- lab05.json for lab 33: every measured mode writes it at --seed 0, merged under a file lock. Keys: rmse.global_mean, rmse.movie_mean, rmse.bias_baseline, rmse.dot (--baseline), rmse.dot_bias (--change), rmse.break_valid (--break), valid_idx (20,000 sorted 0-based u.data line numbers) and a one-line about.
- Lab file Goal line: the spec's "say how far it beats" became "say how far its RMSE is from", so the lab file carries no direction hint. It names the three baselines.
- Effect P2 (bias terms) is below the 2x rule: mean change -0.004818 against a raw seed spread of 0.011804. The raw spread is mostly the split changing with the seed, which moves P1 and P2 together. The paired delta P2.delta_rmse is negative at all three seeds and its own spread is 0.0021433, so P2's size is graded on P2.delta_rmse. No knob was changed: the spec fixes the P1 config, the change is binary, and the small size is the lesson: 50 factors already carry most of a per-movie offset when users keep many ratings in training. Every user has at least 20 ratings in the full data; an inspection of the seed-0 training split (no training) found at least 12 per user there, a median of 52, and 121 of 943 users below 20. Effects P3 vs P1 (0.245146 against a spread of 0.010173) and P3 vs the global mean (0.0539767 against 0.00742) pass.
- Prototype comparison. The spec's answers-only note: wd 0 for 20 epochs gave validation 1.208 vs the global mean's 1.123, train 0.278. Here at seed 0: validation 1.17451 vs 1.1179, train 0.255702. Same direction: above the global mean at all three seeds. The global-mean gap is inside its spread (0.00742): the prototype used another split (at seed 42, u.data order gives 1.1179 and the grouped-by-movie order of older pandas merges gives 1.1279). The break gap is about 28 times the 0.0012 spread, so it is a configuration difference, not noise. Tagged runs at seed 0, not in the .json, ruled out the obvious causes without an exact match. Each value is in the log of the ledger job named after it:
  - bias terms, DotProductBias with wd 0 for 20 epochs: validation 1.1732, train 0.2473; the RMSE definition: fastai's own validation loss gives 1.1745 and the square root of its smoothed train loss gives 0.2534 (job 05-break-s0-protobias-102933-36538);
  - no y_range: validation 1.1010, train 0.3324; a constant learning rate, fit instead of fit_one_cycle: validation 1.2176, train 0.4199 (job 05-break-s0-protovariants-104938-1259);
  - fastai's default wd 0.01 from not passing wd, DotProduct: validation 1.1280, train 0.2690 (job 05-break-s0-protovariants2-105520-21225, which printed this line, then exited 1 on its second variant);
  - the same default with collab_learner: validation 1.1183, train 0.2559; lr 1e-2: validation 1.1811, train 0.2601 (job 05-break-s0-protovariants3-110053-45064, the fixed rerun).
  Of these, only the higher peak learning rate (lr 1e-2) moved both final numbers toward the prototype's, which supports the schedule hypothesis. The prototype most likely ran another schedule or library version. The reference keeps the spec's stated config. One trap worth knowing: forgetting to pass wd=0 leaves fastai's 0.01, and collab_learner then ends level with the global mean.

</details>
