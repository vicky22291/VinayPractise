# 33. Embeddings from scratch: DotProductBias and what factors encode: reference answers

> Spoilers. The AI opens one block at a time, only after that step's prediction row exists and the learner pasted their own RESULT lines, or after 'debrief 33'.

- HW: `HW chip='Apple M4 Pro' cpu=14 gpu=20 mem_gib=24 macos=26.5.1 python=3.13.7 torch=2.14.1 device=cpu`
- Seeds: 0, 1 and 2 for every step (light lane). The split is lab 05's at every seed (read from `lab05.json`); the seed changes the initialisation, the batch order and the 50 held-out users.
- Reference script: `answers/33_embeddings_from_scratch_ref.py` (script_sha256 `963e9c71b118d8a6`). Raw seed-0 output: `answers/33-embeddings-from-scratch.out`. Values and spreads: `answers/33-embeddings-from-scratch.json`.
- Runs and wall times (seed 0 / 1 / 2, light lock): baseline 31.6 / 35.8 / 44.5 s, change 23.0 / 18.2 / 19.6 s, break 38.1 / 36.5 / 29.0 s.
- Tolerance rule: tol = spread (max - min) over seeds 0, 1, 2; heavy labs: the baseline spread applies to every step.

<details><summary>P1. Validation RMSE of your DotProductBias (50 factors, weight decay 0.1, 5 epochs, AdamW, one-cycle to 5e-3, batch 64, seed 0) on lab 05's split</summary>

**Answer:** 0.900242 stars at seed 0, tolerance 0.001579 (the seed spread). Seeds 1 and 2: 0.901821 and 0.901048. That is 0.0174635 stars below lab 05's fastai DotProductBias on the same split (0.917706, read from `lab05.json`); the difference is -0.0158848 and -0.0166577 at seeds 1 and 2.

```
RESULT P1.valid_rmse=0.900242 unit=stars seed=0
RESULT baseline.lab05_rmse=0.917706 unit=stars seed=0
RESULT baseline.minus_lab05=-0.0174635 unit=stars seed=0
NOTE pca1 one end: McHale's Navy (1997); Jungle2Jungle (1997); Leave It to Beaver (1997); Super Mario Bros. (1993); Children of the Corn: The Gathering (1996)
NOTE pca1 other end: Close Shave, A (1995); Casablanca (1942); Dr. Strangelove or: How I Learned to Stop Worrying and Love the Bomb (1963); Big Sleep, The (1946); Lawrence of Arabia (1962)
```

**Why:** the model, the optimizer math and the split are lab 05's; the sampler is not. The plain loop cuts every epoch from a permutation, so each of the 80,000 training ratings is seen once per epoch. fastai 2.8.12 builds lab 05's training loader as `TabWeightedDL`, which draws each epoch's 80,000 rows with replacement, so an epoch sees about 63% of the distinct ratings and repeats others. Build experiments on this split at seed 0 narrow it down: fastai's own pipeline reran at 0.922561 (0.923422 at seed 1), fastai's Learner with this lab's model class gave 0.922749, and this lab's loop with fastai's `Adam` and fastai's one-cycle schedule (learning rate and momentum) in place of `AdamW` and `OneCycleLR` gave 0.900247, the same as the plain loop. That rules out the model, the optimizer, the schedule and the split, which leaves the sampler. It is a conclusion by elimination: no build run swapped the sampler alone.

**The first PCA axis:** one end holds widely panned films from 1993 to 1997 (family comedies, a video-game adaptation, a horror sequel); the other end holds acclaimed classics (Casablanca, Lawrence of Arabia, Dr. Strangelove) and the Wallace and Gromit short A Close Shave. It reads as a critics' taste axis, acclaimed films against broad mid-1990s releases, and the same titles recur across seeds. Seed 1: "Leave It to Beaver (1997); McHale's Navy (1997); Jungle2Jungle (1997); Super Mario Bros. (1993); Bio-Dome (1996)" against "Casablanca (1942); Close Shave, A (1995); Third Man, The (1949); Some Folks Call It a Sling Blade (1993); Secrets & Lies (1996)". Seed 2: "McHale's Navy (1997); Jungle2Jungle (1997); Leave It to Beaver (1997); Bio-Dome (1996); Children of the Corn: The Gathering (1996)" against "Casablanca (1942); Dr. Strangelove or: How I Learned to Stop Worrying and Love the Bomb (1963); Chinatown (1974); Lawrence of Arabia (1962); Close Shave, A (1995)". Which end is which flips with the sign of the axis, which is arbitrary.

**Common wrong prediction:** "the same as lab 05's" (it is one formula, but not one sampler), or "worse than lab 05's, because a hand-written loop lacks fastai's tricks".
</details>

<details><summary>P2. 4 factors instead of 50: validation RMSE direction and size (4 factors minus 50 factors, seed 0)</summary>

**Answer:** up by 0.0227451 stars at seed 0 (to 0.922987), tolerance 0.0018156 on the delta (its seed spread). Seeds 1 and 2: deltas 0.0245607 and 0.0231024, RMSE 0.926382 and 0.92415 (spread 0.003395). The effect over the three seeds is 0.0234693 stars against a spread of 0.003395, about 7x.

```
RESULT P2.valid_rmse=0.922987 unit=stars seed=0
RESULT P2.delta_rmse=0.0227451 unit=stars seed=0
```

**Why:** with 4 factors, each user and each movie get four taste numbers besides their biases, so the model has only four taste directions to work with: tastes that need more (a user who loves film noir and also Disney musicals, say) get folded together. With 50 factors, weight decay 0.1 keeps every row small but leaves room for many more independent taste directions, and the validation ratings reward them. The cost is close at every seed (0.0227451 to 0.0245607), so it is lost capacity, not noise. The cost is not "the fewer, the worse" all the way up: in the build scan it mostly shrinks as factors are added, sits inside the seed spread at 15 and 20 factors, and 25 factors beat 50 slightly (build notes).

**Common wrong prediction:** "down, because fewer factors overfit less" (4 factors is short of capacity, and with weight decay 0.1 the 50-factor RMSE sits within about 0.0034 stars of the best count scanned), or "same, because weight decay makes the factor count irrelevant".
</details>

<details><summary>P3. 50 users held out entirely: is their RMSE closest to the warm users, the movie-mean baseline or the global mean? (seed 0)</summary>

**Answer:** closest to the global mean, at every seed, and above it at every seed. Seed 0: cold 1.25812 stars, global mean 1.15882, movie mean 1.03565, warm 0.901012. Seed 1: cold 1.17816, global mean 1.065, movie mean 0.996679, warm 0.905683. Seed 2: cold 1.17263, global mean 1.09783, movie mean 0.989718, warm 0.903855. Tolerances (seed spreads): cold 0.08549, global mean 0.09382, movie mean 0.045932, warm 0.004671. The pick is graded on `P3.closest`, which is `global_mean` at all three seeds.

```
RESULT P3.cold_rmse=1.25812 unit=stars seed=0
RESULT P3.closest=global_mean unit=choice seed=0
RESULT break.warm_rmse=0.901012 unit=stars seed=0
RESULT break.cold_global_mean_rmse=1.15882 unit=stars seed=0
RESULT break.cold_movie_mean_rmse=1.03565 unit=stars seed=0
NOTE held-out users 50, their ratings 5342, warm validation ratings 18910
```

The distance from cold to each option, per seed: global mean 0.0993, 0.11316, 0.0748; movie mean 0.22247, 0.181481, 0.182912; warm 0.357108, 0.272477, 0.268775. Cold minus warm (0.299453 over the seeds) and cold minus movie mean (0.195621) both clear 2x the seed spread. Cold minus global mean is positive at every seed, but it is about 1x the spread of the global-mean RMSE, so say "no better than the global mean", not "reliably worse".

**Why:** a held-out user's factor row and bias never get a gradient, and AdamW's decoupled weight decay shrinks them at every step, so they end near zero (a build check at seed 0: mean user-row norm 0.0157 for the cold users against 1.13 for warm users; cold user bias about 0.0003 against a warm mean of 0.127). The prediction for a cold user is then 5.5 x sigmoid(movie bias). DotProductBias has no global-mean term: the rating level is carried by the warm users' biases and by a direction their factor rows share, and the cold user has neither, so every cold prediction sits low (the same check: mean prediction 2.94 stars against a mean cold rating of 3.57). That systematic offset is why the model loses even to the global mean, while the movie mean, which needs no user vector, does best of the three for these users.

**Common wrong prediction:** "the movie mean, because the model still knows every movie" (it knows each movie only relative to users it has seen), or "close to the warm users, because 50 factors generalise".
</details>

<details><summary>Rebuild check</summary>

- Stub: `m5-under-the-hood/rebuild/33_dot_product_bias.py`. Solution: `answers/rebuild/33_dot_product_bias.py`.
- `rebuildcheck`: the stub fails as it should (NotImplementedError, exit 1); the solution passes (exit 0, `check: PASS`). REBUILDCHECK OK.
- `check()` compares the explicit L2 term under plain SGD with `torch.optim.SGD(weight_decay=wd)` over 20 steps (largest parameter gap under 1e-6), checks the N(0, 0.01) start, outputs near 2.75 at the start and inside 0 to 5.5 at large scores, and a falling loss, all on synthetic ratings. The build confirmed it rejects three wrong bodies: the fastbook form wd x Σw² (gradient 2 x wd x w), an L2 term on the batch's rows only, and sigmoid_range(score, 1, 5).
</details>

<details><summary>Card drafts</summary>

| ID | Lab | Type | Question |
|---|---|---|---|
| 33-M | 33 | M | DotProductBias still returns a rating for a user who is in no training rating. What does it compute for that user, and why does that prediction sit below the average rating? |
| 33-N | 33 | N | On lab 05's MovieLens 100K split (wd 0.1, 5 epochs, AdamW), about how many stars of validation RMSE does DotProductBias give up going from 50 factors to 4, and what still carries most of the signal at 4 factors? |
| 33-D | 33 | D | A hand-written PyTorch loop and fastai's Learner train the same model with the same optimizer on the same split, and the fastai run is reliably worse. What do you check first, and how? |

Keys:

- 33-M: (1) the user's row and bias never get a gradient, and weight decay shrinks them to about zero; (2) the prediction is 5.5 x sigmoid(movie bias) alone; (3) the model has no global-mean term, so the rating level that warm users' biases and shared factors carried is missing.
- 33-N: (1) about 0.02 stars (0.0227451 to 0.0245607 over 3 seeds, 0.922987 against 0.900242 at seed 0); (2) the two biases, plus four broad taste axes.
- 33-D: (1) the batch sampler: does each epoch see every training row once? (2) count the distinct rows one epoch yields (fastai 2.8.12's tabular loader samples with replacement: 50,495 distinct (user, title) pairs in 80,000 rows here); (3) only then compare the schedule and the form of weight decay.
</details>

<details><summary>Build notes</summary>

- **Knob change, P2: 4 factors, not the spec's 5.** In the first full reference round (seeds 0 to 2), 5 factors gave 0.911949, 0.926005 and 0.913702 stars: an effect over 50 factors of 0.011707, 0.024184 and 0.0126537, with the 5-factor RMSE spread 0.014056 over seeds, so the effect failed the 2x rule. A first tagged scan (`kscan`, same `fit()`, seeds 0 to 2) gave 3 factors 0.917276 / 0.924505 / 0.929905, 2 factors 0.931950 / 0.912650 / 0.931706, and 1 factor 0.934214 / 0.933846 / 0.934632. Every factor column was alive (standard deviation over 0.05) in every run, so the noise is not dead factors: a few-factor fit lands in different solutions depending on the start. An earlier version of this lab moved P2 to 1 factor on that scan alone. A review pointed out that 4 factors, and counts between 5 and 50, were never tested, so a second tagged scan (`kscan2`, same `fit()`, seeds 0 to 2) ran them. Mean effect over 50 factors, then the rule's spread (the larger of the two RMSE spreads) and the ratio: 4 factors 0.0234693, 0.003395, 6.9x; 6 factors 0.012253, 0.004679, 2.6x; 8 factors 0.007083, 0.001664, 4.3x; 10 factors 0.004908, 0.001663, 2.9x; 15 factors 0.000925, 0.002553, 0.4x; 20 factors -0.001406, 0.001579, 0.9x; 25 factors -0.003426, 0.001579, 2.2x. So 4 and 6, one factor either side of the spec's 5, both clear the rule, and 1 factor was not the smallest change. The lab uses 4: the brief's remedy is a bigger shift away from 50, 4 is the smallest bigger shift, and it clears with the wider margin (6 clears at 2.6x). The review's other suggestion, the passing count nearest 50, moves further from the spec's 5, not closer, and at 25 factors the effect already passes the rule with the opposite sign. The reference reruns at 4 factors print the same RMSE as the scan at each seed, and the 4-factor figures above are the .json's. The lab file and the reference's `RUNS` say 4 factors; the spec's `change_one_thing` and P2 text say 5.
- **Deviation, the goal line.** The spec's goal says "match lab 05's RMSE". The plain loop beats it at every seed, by about 11x this lab's seed spread. fastai's pipeline rerun on this split (0.922561 and 0.923422) sits even further above, so the gap is not seed luck on lab 05's side. The likely cause is the sampler in P1, so the lab file says "compare" and holds no expected value. The cause, from the fastai source: `fastai/tabular/core.py` sets `TabularPandas._dl_type = TabWeightedDL`, and its `get_idxs` returns `list(np.random.choice(self.n, self.n, p=self.wgts))` when shuffling. One epoch of lab 05's training loader yielded 80,000 rows holding 50,495 distinct (user, title) pairs, of the 79,796 in the training set (29,412 once, 14,599 twice, 4,902 three times: the Poisson(1) shape of a bootstrap sample). Every lab that trains through a fastai TabularPandas loader has this sampler (lab 05's collab model, and fastai's `tabular_learner`); that was reported to the build, not changed here.
- **Prototype comparison** (the spec's prototype: cold users 1.198, global mean 1.095, movie mean 1.017, warm 0.972). Cold 1.25812 at seed 0 is within 2x its spread (0.08549) of 1.198; the global mean 1.15882 is within 2x 0.09382 of 1.095; the movie mean 1.03565 is within 2x 0.045932 of 1.017. The pick agrees: the global mean is nearest, as in the prototype, and the order cold, global mean, movie mean, warm holds at every seed. Warm differs: 0.901012 against 0.972, a gap of about 15x the warm spread (0.004671), in the better direction. That is not a bug here: the warm RMSE matches this harness's own P1 (0.900242) on nearly the same users, and lab 05's fastai model scores 0.917706 on the same split; the prototype's warm value is worse than both, so its training recipe (not recorded in the spec) must have been weaker.
- **Precomputed steps:** none. Every reference run finished within 44.5 s.
- **Smoke:** the reference runs all three modes for 1 epoch on the first 5,000 lines of `u.data`; the starter's smoke stands the movie mean in for the model and prints every RESULT name. On a clean machine `P2.delta_rmse` prints a SKIP line in smoke, because smoke stores no values for `labkit.prior`.
- **Experiments** (tagged, so mkanswers ignores them; scripts in the build's `tmp/`, logs in its `runs/33/`): `gapexp` (fastai pipeline against the plain loop), `optexp` (fastai `Adam` against `AdamW` inside the plain loop), `kscan` (factor counts 1, 2, 3 and 5), `kscan2` (factor counts 4, 6, 8, 10, 15, 20 and 25, script `exp33_factors2.py`), `coldexp` (what the break model predicts for cold users: the row norms, biases and mean prediction quoted in P3, and cold RMSE 1.1817 at seed 0 when the cold users get the mean warm user bias, which shows the shared factor direction carries part of the offset). Two untagged mlpy inspections in the same `tmp/` back other claims: `insp33.py` gives the loader counts above, and `mut33.py` shows the three wrong rebuild bodies fail. A second build pass reran both and got the same output.
</details>
