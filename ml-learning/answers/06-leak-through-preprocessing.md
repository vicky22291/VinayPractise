# 06. Leak through preprocessing: fit every transform inside each fold: reference answers

> Spoilers. The AI opens one block at a time, only after that step's prediction row exists and the learner pasted their own RESULT lines, or after 'debrief 06'.

- HW: `HW chip='Apple M4 Pro' cpu=14 gpu=20 mem_gib=24 macos=26.5.1 python=3.13.7 torch=2.14.1 device=cpu`
- Seeds: 0, 1 and 2 for every step (light lane). The predictions name seed 0.
- Reference script: `answers/06_leak_through_preprocessing_ref.py` (sha256 prefix `ab05abea350be66a`). The learner's `m2-dont-fool-yourself/scripts/06_leak_through_preprocessing.py` is this file with `encode()` and `cv_mae()` stubbed.
- Runs and wall times in seconds, seeds 0, 1 and 2, light lock on a CPU shared with other builds: baseline 14.8, 14.8, 11.8; change 37.9, 16.7, 14.1; break 10.0, 19.1, 18.8.
- Tolerance rule: tol = spread (max - min) over seeds 0, 1, 2. All values: `06-leak-through-preprocessing.json`. Raw seed-0 output: `06-leak-through-preprocessing.out`.

<details><summary>P1. 5-fold CV MAE in dollars, seed 0, numeric columns plus Neighborhood target-encoded inside each fold</summary>

**Answer:** 16545.1 dollars at seed 0, tolerance 676.5 (the seed spread). Seeds 1 and 2: 16859.3 and 17221.6.

```
RESULT baseline.mae_numeric_only=17513.1 unit=usd seed=0
RESULT P1.mae_infold=16545.1 unit=usd seed=0
```

| RESULT | seed 0 | seed 1 | seed 2 | spread (tolerance) |
|---|---|---|---|---|
| `baseline.mae_numeric_only` | 17513.1 | 17090 | 17688.8 | 598.7999999999993 |
| `P1.mae_infold` | 16545.1 | 16859.3 | 17221.6 | 676.5 |

**Why:** location carries price signal that the 36 numeric columns only partly hold, and inside each fold a validation house's Neighborhood value is built from training houses only. So this MAE is honest about validation leakage: no validation price reaches any encoding, and it estimates what the 37-column pipeline scores on houses it has never seen. It came out below the numeric-only run on the same folds at each of the three seeds (17513.1 at seed 0), but the gain is not established: the effect check over seeds (`P1.mae_infold` minus `baseline.mae_numeric_only`, mean -555.3000000000005 against a spread of 676.5) is not above 2x the spread. Read P1 as close to the numeric-only error, likely a little below it, not as a measured gain.

**Common wrong prediction:** guessing from the price scale (houses sell for hundreds of thousands of dollars) and landing far too high, or expecting one categorical column to cut the error in half.

</details>

<details><summary>P2. Neighborhood encoded on all 1,460 rows before KFold: MAE change (leaky minus in-fold), direction and size</summary>

**Answer:** same. At seed 0 the change is 150.477 dollars, smaller in size than the seed spread of `P1.mae_infold` (676.5), which is the lab's yardstick for "same". Tolerance (the seed spread of `P2.mae_change`): 178.931. Seeds 1 and 2: -28.454 and 2.72062, so the sign flips with the split. The effect check over seeds (`P2.mae_leaky` minus `P1.mae_infold`, mean 41.60000000000097 against a spread of 676.5) is not above 2x the spread: the lab teaches this effect as null.

**Grading:** use the learner's own pasted `P2.mae_change` at seed 0 and their own seed spread of `P1.mae_infold` from the baseline loop (676.5 in the reference), as the lab's P2 row defines. The direction is "same" when the change is smaller in size than that spread, as here, and "up" or "down" only when it is at least that big. "Same" is a hit when the learner's range covers their seed-0 change (150.477 in the reference). "Up" and "down" miss here, even when their range covers the change, because the change is inside the seed spread.

```
RESULT P2.mae_leaky=16695.6 unit=usd seed=0
RESULT P2.mae_change=150.477 unit=usd seed=0
RESULT change.gap_pct=-0.909496 unit=percent seed=0
```

| RESULT | seed 0 | seed 1 | seed 2 | spread (tolerance) |
|---|---|---|---|---|
| `P2.mae_leaky` | 16695.6 | 16830.9 | 17224.3 | 528.7000000000007 |
| `P2.mae_change` | 150.477 | -28.454 | 2.72062 | 178.931 |
| `change.gap_pct` | -0.909496 | 0.168773 | -0.0157977 | 1.078269 |

**Why:** a house's own price is one of about 58 prices in its Neighborhood mean, and smoothing 10 pulls that mean toward the global mean, so on the leaky path its own price moves its value by about 1/68 of its gap from the level mean. Inside each fold the level means come from about 47 training rows per level, so they sit close to the all-rows means. The leaky and the in-fold columns are nearly the same column, too alike for the trees to exploit the difference, and the MAE moves less than the fold split moves it.

**Common wrong prediction:** "leakage always flatters the score, so down by hundreds of dollars." The leak is there, but here it is smaller than the seed noise.

</details>

<details><summary>P3. Neighborhood x YearBuilt (501 levels, 2.9 rows each), all rows vs inside each fold: the MAE gap, (in-fold minus leaky) / in-fold, in percent</summary>

**Answer:** 22.6293 percent at seed 0, tolerance 1.5059000000000005. Seeds 1 and 2: 21.9252 and 21.1234. In dollars at seed 0: `break.mae_change` is -4777.28, from 21111.1 in-fold to 16333.8 leaky. The effect check over seeds (`break.mae_cross_leaky` minus `break.mae_cross_infold`, mean -4586.0666666666675 against a spread of 377.8999999999978) is above 2x the spread.

```
RESULT break.mae_cross_infold=21111.1 unit=usd seed=0
RESULT break.mae_cross_leaky=16333.8 unit=usd seed=0
RESULT break.mae_change=-4777.28 unit=usd seed=0
RESULT P3.gap_pct=22.6293 unit=percent seed=0
```

| RESULT | seed 0 | seed 1 | seed 2 | spread (tolerance) |
|---|---|---|---|---|
| `break.mae_cross_infold` | 21111.1 | 20733.2 | 20995.9 | 377.8999999999978 |
| `break.mae_cross_leaky` | 16333.8 | 16187.4 | 16560.8 | 373.39999999999964 |
| `break.mae_change` | -4777.28 | -4545.79 | -4435.04 | 342.2399999999998 |
| `P3.gap_pct` | 22.6293 | 21.9252 | 21.1234 | 1.5059000000000005 |

**Why:** a row's own target sits in its level's encoding with weight 1 / (rows in the level + smoothing), so the leak grows as rows per level shrink: about 1/68 for Neighborhood, and 1/11 for a one-row level of the cross key, whose encoding is (price + 10 x mean_all) / 11, a straight line in the price (mean_all is the mean price of the rows the encoding is fit on). Encoded on all rows, the validation houses carry their own prices the same way the training houses do, so the trees read much of the answer off the column. Inside each fold, the training rows still carry their own prices, so the trees learn to lean on the column, but each validation house gets a mean without its own price, or just the training mean for a level the training rows never saw. So the in-fold cross-key run ends worse than numeric-only (21111.1 vs 17513.1 at seed 0), which is why scikit-learn's `TargetEncoder.fit_transform` cross-fits the training rows. What the gap measures: how far the all-rows encoding flatters the CV score of one pipeline. The in-fold MAE is honest about validation leakage: it is what this pipeline, the leaky notebook's included, scores on new houses, which get an encoding from training rows only. It is not the best encoder one could build: cross-fitting the training rows makes a better pipeline, a separate fix (build notes, mechanism check).

**Common wrong prediction:** a small gain, from "the cross key adds real information, so the in-fold run is already good". The in-fold run is the one that suffers, so the gap is large. A second miss: dividing by the numeric-only MAE instead of the in-fold cross-key MAE.

</details>

<details><summary>Rebuild check</summary>

Solution: `answers/rebuild/06_in_fold_target_encoding.py`. Stub: `m2-dont-fool-yourself/rebuild/06_in_fold_target_encoding.py`.

`rebuildcheck` verdict: the stub fails as it should (exit 1, NotImplementedError); the solution passes (exit 0, prints `check: PASS`); REBUILDCHECK OK.

`check()` compares `encode()` with a pandas groupby mean (smoothing 0) and with scikit-learn's `TargetEncoder` (smoothing 10, with a level the fit rows never saw). Then it runs `cv_mae()` both ways at fold seeds 0 and 1, on a pure-noise key with 1 to 5 rows per level, and compares each run with the same CV built from scikit-learn parts (a `Pipeline` inside `cross_val_score` for the in-fold path). The unequal level sizes matter: with equal sizes, a smoothed encoding is a straight-line function of the plain level mean, so `LinearRegression` cannot tell a leaky path that skips smoothing from the right one.

18 wrong versions each fail it, and each fails the script's `--check` too. In `encode()`: no smoothing, unseen level set to 0, global mean taken from the apply rows, an off-by-one denominator, and the mean of level means used as the global mean. In `cv_mae()`: the fold seed fixed at 0 (on both paths, on the leaky path only, on the in-fold path only), a leaky path without smoothing, always leaky, never leaky, validation rows encoded from themselves, training rows encoded from all rows, validation rows encoded from all rows, the model fit on all rows, no shuffle, 3 folds, and the median over folds instead of the mean.

</details>

<details><summary>Card drafts</summary>

Use 06-M, 06-N, and 06-T or 06-D, whichever type the last close did not use (T and D alternate from one close to the next, `ml-learning/CLAUDE.md` §4).

| ID | Lab | Type | Question |
|---|---|---|---|
| 06-M | 06 | M | Encoding a key on all rows before KFold faked a large gain for Neighborhood x YearBuilt (2.9 rows per level) and none for Neighborhood (58 rows per level). Why does rows per level decide it? |
| 06-N | 06 | N | In lab 06, about what share of the in-fold CV MAE did the all-rows encoding of Neighborhood x YearBuilt fake away, and why was the in-fold cross-key run worse than numeric-only? |
| 06-T | 06 | T | A fraud model target-encodes merchant_id, and most merchants have fewer than 5 payments in the training window. If the encoding is fit on all rows before CV, where does the fake gain concentrate, and what keeps the offline number honest? |
| 06-D | 06 | D | A target-encoded merchant_id lifts offline AUC by 0.05, and a shadow run shows no lift. What do you check first, and what result confirms a leak? |

Keys:

- 06-M: (1) a row's own target sits inside its level's encoding with weight 1 / (rows in the level + smoothing); (2) at 2.9 rows that weight is large (a one-row level is (price + 10 x mean_all) / 11, mean_all being the mean price of the fit rows), so the trees learn it and the validation rows still carry it; (3) at 58 rows the weight is about 1/68, too small to use.
- 06-N: (1) about 21 to 23 percent of the in-fold MAE (22.6293 at seed 0; 21.1234 to 22.6293 over seeds 0 to 2); (2) the in-fold cross-key run is worse than numeric-only because its training encodings hold each row's own price, so the trees trust a column that validation rows get without it.
- 06-T: (1) in the merchants with the fewest payments: a payment's own label sits in its merchant's value with weight 1 / (that merchant's payments + smoothing), 1/12 for a 2-payment merchant at smoothing 10, against about 1/68 for lab 06's Neighborhood; (2) fit the encoding inside each fold (a Pipeline handed to cross_val_score) and cross-fit the training rows (as TargetEncoder.fit_transform does), so no row's own label reaches its own value; (3) in production, build it as of each decision time from matured labels only, and validate on a later time window (repo link §2, items 1 and 5).
- 06-D: (1) refit the encoding inside each fold, or out of fold as of each decision time, and rerun: a lift that vanishes was the leak; (2) a placebo: a random id with the same payments per id; any lift from it is pure leak; (3) look where the lift lives: merchants with few payments leak the most.

</details>

<details><summary>Build notes</summary>

- **Knob changes:** none. The cross key's effect clears 2x the seed spread at the spec's configuration. The Neighborhood effect is taught as null and reported with its spread, never inflated. The P1 gain over numeric-only is reported with its spread too (a third effect in the .json), and the P1 text does not teach it as established.
- **Precomputed steps:** none. Every run takes under a minute, so the Compute line is 9 runs x 1 min (three steps at seeds 0, 1 and 2, as the lab asks).
- **Deviations from the spec, and why:**
  - `cv_mae()` also takes `model` and `seed`: `cv_mae(df, col, target, features, leaky, model, seed=0)`. `--check` passes `LinearRegression` on its 20-row fixture, because LightGBM's default `min_child_samples=20` cannot split 16 training rows. The rebuild keeps the same signature as the TODO.
  - Both `check()` functions compare `cv_mae()` at fold seeds 0 and 1, with the seed passed explicitly. A `cv_mae()` that fixes its fold seed at 0 fails, so the learner's seed 1 and 2 runs cannot silently reuse the seed 0 folds.
  - The rebuild `check()` has no "leaky comes out lower" assertion. It compares with a pandas groupby mean, scikit-learn's `TargetEncoder` and a scikit-learn CV of both paths on a pure-noise key, because a stated direction in a learner-visible stub would hint at P2 and P3 (brief section 9).
  - `--smoke` stands in `library_cv_mae()` for the TODO (scikit-learn `TargetEncoder` fit then transform, never `fit_transform`'s cross fitting, and a `Pipeline` for the in-fold path). `--check` compares against the same function. The `FitThenMap` docstring says what the class does, not why, so no learner-visible file names the cross fitting.
  - Where the spec is silent: the numeric features are all 36 numeric columns except `Id` and `SalePrice`; a level unseen in a training fold gets that fold's mean target (as `TargetEncoder` does); LightGBM runs with `n_jobs=4` and `force_col_wise=True`, so reruns on a shared CPU grow the same trees.
  - Sign conventions: the dollar change is leaky minus in-fold (`P2.mae_change`, `break.mae_change`), so a fake gain shows as a negative change. The percents, `change.gap_pct` and `P3.gap_pct`, are (in-fold minus leaky) / in-fold. Neither is named `fake_gain_pct`, and the lab sheet says "MAE gap" where the spec says "fake gain", so no name in the script, the Goal, the Predict table or the Record suggests a direction before P2 and P3 are logged.
  - Notation: lab 06's docstrings and this file write mean_all for the fit rows' mean target and spell out smoothing, so no symbol clashes with the module README, which writes m for the smoothing.
  - The Record's 3-seed spread is the learner's own: each step runs as a shell loop over seeds 0, 1 and 2. The P2 row defines "same" with the learner's seed spread of `P1.mae_infold`, and the change and break sections ask the learner to set each seed's change next to a seed spread after the loop.
  - Card drafts carry both 06-T and 06-D, because T and D alternate by close order (`ml-learning/CLAUDE.md` §4), not by lab number. Concept link checked: the module README has the heading "Leakage through preprocessing", anchor `#leakage-through-preprocessing`.
- **Review fixes (second round):** the changes above to both `check()` functions, the rebuild fixture (1 to 5 rows per level), the `change.gap_pct` name, the `FitThenMap` docstring and the mean_all notation changed the reference, so the starter was regenerated with `make_c_starter` and all 9 measured runs were rerun. Every value matched the earlier runs exactly.
- **Review fixes (third round):**
  - "Fake gain" in the Goal and the P3 row, and the RESULT name `P3.fake_gain_pct`, gave away the sign of P3 before it was logged, and hinted before P2 that the all-rows encoding lowers the MAE. The lab sheet now says "MAE gap" and "what target-encoding before the split does to the CV MAE", and the RESULT is `P3.gap_pct`, with the same formula. The spec's "fake gain" wording now lives only in `answers/`.
  - A reviewer asked for cross-fitted training encodings on the in-fold path, because its training rows carry their own targets. Not done: fit on the training fold and apply to both folds is the spec's design, and the spec's prototype in-fold cross-key value (above numeric-only) pins it. That CV MAE is the honest estimate for the very pipeline the leaky notebook deploys, so the gap isolates validation leakage. Cross-fitting builds a different, better pipeline (mechanism check below). The wording is now precise: the lab's Baseline Why says "no validation leak", and the P1 and P3 text says "honest about validation leakage".
  - The rename changed the reference, so the starter was regenerated with `make_c_starter`, all 9 measured runs were rerun, and `--check` and `--smoke` were rerun on both scripts. Every value, spread and effect matched the second-round runs exactly.
- **Prototype comparison** (spec value, then this build's seed-0 value and seed spread): numeric-only 17,513 vs 17513.1 (598.7999999999993); Neighborhood in-fold 16,530 vs 16545.1 (676.5); Neighborhood leaky 16,578 vs 16695.6 (528.7000000000007); cross in-fold 21,298 vs 21111.1 (377.8999999999978); cross leaky 16,155 vs 16333.8 (373.39999999999964); fake gain 5,143 dollars vs `break.mae_change` -4777.28 (342.2399999999998); 24.1% vs 22.6293 (1.5059000000000005). Every direction agrees and every gap is under 2x the spread, so no bug is indicated. Numeric-only matches to the dollar, so the folds and the model match the prototype; the encoded runs differ a little, and that was not chased further.
- **Mechanism check behind the P3 text** (a scratch script, not in the .json): at seed 0 the in-fold cross-key model gives the encoded column a far larger share of its split gain than the Neighborhood model does, and when the training rows are encoded out of fold instead (as `TargetEncoder.fit_transform` does) the cross-key MAE, still with no validation leak, comes back near numeric-only.
- **Soundbite tie** (from the spec, kept here because it hints at P3, and the seed of the 06-T card): merchant ids with few payments leak the same way.

</details>
