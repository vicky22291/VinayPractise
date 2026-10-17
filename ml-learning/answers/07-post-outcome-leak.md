# 07. Leak through a post-outcome column: ask when each value is known: reference answers

> Spoilers. The AI opens one block at a time, only after that step's prediction row exists and the learner pasted their own RESULT lines, or after 'debrief 07'.

- **HW:** `HW chip='Apple M4 Pro' cpu=14 gpu=20 mem_gib=24 macos=26.5.1 python=3.13.7 torch=2.14.1 device=cpu`
- **Seeds:** 0, 1 and 2 for every step (light lane). The defaults reproduce seed 0.
- **Reference script:** `answers/07_post_outcome_leak_ref.py` (script_sha256 `fe1b63e142d9da0d`). The starter `m2-dont-fool-yourself/scripts/07_post_outcome_leak.py` is the same file with the body of `leak_scan()` stubbed.
- **Runs and wall times (s), seeds 0, 1, 2:** baseline 2.1, 2.3, 2.4; change 2.2, 2.2, 2.2; break 1.7, 1.8, 1.7. Lock: light. Nothing is precomputed.
- **Tolerance rule:** tol = spread (max - min) over seeds 0, 1, 2; heavy labs: the baseline spread applies to every step.
- **Values:** `answers/07-post-outcome-leak.json`. Raw seed-0 output: `answers/07-post-outcome-leak.out`.

<details><summary>P1. LightGBM defaults, 5-fold stratified cross-validation (CV), seed 0: accuracy on the 7 boarding-time columns (pclass, sex, age, sibsp, parch, fare, embarked; no boat, no body)</summary>

**Answer:** 0.792223 at seed 0, tolerance 0.02212599999999998 (the spread over seeds 0 to 2).

```
RESULT P1.cv_accuracy=0.792223 unit=fraction seed=0
```

Other seeds: 0.799093 (seed 1), 0.814349 (seed 2).

**Why:** Lifeboat places went mostly to women and children and to the upper classes, so sex and pclass carry most of what is known at boarding; age, fare and family size add a little. The rest is luck no column records, such as where a passenger stood when the boats left. That puts an honest model well above always predicting death and well short of perfect.

**Common wrong prediction:** above 0.9, anchored on public Titanic leaderboards, whose near-perfect scores come from looking up published survivor lists: a leak of its own.

</details>

<details><summary>P2. Add boat and body (9 columns), same model and folds, seed 0: CV accuracy direction and size</summary>

**Answer:** up. `P2.cv_accuracy` 0.955684 at seed 0, tolerance 0.006113000000000035. The size: `P2.delta_points` 16.3461 points at seed 0, tolerance 2.2119999999999997 points.

```
RESULT P2.cv_accuracy=0.955684 unit=fraction seed=0
RESULT P2.delta_points=16.3461 unit=points seed=0
RESULT change.top3_gain_share=boat:0.538,sex:0.167,pclass:0.089 seed=0
RESULT change.scan_auc_boat=0.975243 unit=auc seed=0
RESULT change.scan_auc_body=0.574787 unit=auc seed=0
RESULT change.scan_flagged=boat seed=0
```

Other seeds: `P2.cv_accuracy` 0.949577 (seed 1), 0.95569 (seed 2); `P2.delta_points` 15.0484 (seed 1), 14.1341 (seed 2). `change.top3_gain_share` is boat:0.538,sex:0.167,pclass:0.089 on every seed (one deterministic fit on all rows). `change.scan_auc_boat` 0.975067 and 0.975111; `change.scan_auc_body` 0.574833 and 0.57476; `change.scan_flagged` is boat on every seed.

Effect check (mkanswers): `P2.cv_accuracy:P1.cv_accuracy` effect 0.15176199999999998, spread 0.02212599999999998, ok.

**Why:** `boat` is filled in only for people who got into a lifeboat, and almost everyone in a lifeboat lived, so "boat present" is close to the label itself. `body` is filled in only for recovered bodies, so it marks some of the dead, but too few rows to matter much. The gain shares show the tilt: boat:0.538 means more than half of all gain sits on one column. The scan finds boat (single-column AUC, the area under the receiver operating characteristic curve, 0.975243, flagged) and misses body (0.574787): a scan catches a strong leak, and only the question "when is this value known?" catches both.

**Common wrong prediction:** a small bump, as for any extra feature, or "same" on the idea that a mostly missing column carries little. Here the missingness is the signal.

</details>

<details><summary>P3. Score the P2 model as at boarding time (same LightGBM, 9 columns and 5 folds, boat and body blanked in each test fold), seed 0: above, below or the same as the honest model's P1 accuracy, and by how many points</summary>

**Answer:** below. `P3.leaky_vs_honest` is below on seeds 0, 1 and 2. The size: `P3.gap_points` -5.42219 points at seed 0, tolerance 3.132690000000001 points.

```
RESULT P3.leaky_blanked_accuracy=0.738001 unit=fraction seed=0
RESULT P3.gap_points=-5.42219 unit=points seed=0
RESULT P3.leaky_vs_honest=below seed=0
RESULT break.leaky_real_accuracy=0.955684 unit=fraction seed=0
RESULT break.predicted_survival_rate=0.155105 unit=fraction seed=0
RESULT break.actual_survival_rate=0.381972 unit=fraction seed=0
RESULT break.all_died_accuracy=0.618028 unit=fraction seed=0
```

Other seeds:

| RESULT | seed 1 | seed 2 | spread |
|---|---|---|---|
| `P3.leaky_blanked_accuracy` | 0.741031 | 0.7288 | 0.012230999999999992 |
| `P3.gap_points` | -5.80621 | -8.55488 | 3.132690000000001 |
| `break.leaky_real_accuracy` | 0.949577 | 0.95569 | 0.006113000000000035 |
| `break.predicted_survival_rate` | 0.16426 | 0.138282 | 0.025978 |
| `break.actual_survival_rate` | 0.381972 | 0.381972 | 0.0 |
| `break.all_died_accuracy` | 0.618028 | 0.618028 | 0.0 |

The honest model on these folds is the baseline's, so `P3.gap_points` is `P3.leaky_blanked_accuracy` minus `P1.cv_accuracy` (0.792223, 0.799093, 0.814349). `break.leaky_real_accuracy` equals `P2.cv_accuracy` on every seed: the same model, columns and folds. The last two rows do not move because stratified folds put the same number of survivors in each test fold on every seed; only which passengers land there changes.

Effect checks (mkanswers): the comparison P3 asks about, `P3.leaky_blanked_accuracy:P1.cv_accuracy`, effect -0.06594433333333334, spread 0.02212599999999998, ok. The collapse, `P3.leaky_blanked_accuracy:break.leaky_real_accuracy`, effect -0.21770633333333334, spread 0.012230999999999992, ok.

**Why:** In the training folds a blank `boat` meant no lifeboat on record, and boat alone nearly separates survivors from the dead (scan AUC 0.975243), so the model leans on it: the same LightGBM fit on all rows puts 0.538 of its gain on boat. At boarding time every boat is blank, the value that meant no lifeboat in training, so the model predicts survival for only 0.155105 of the passengers while 0.381972 survived. With boat and body blank, only the seven honest columns still tell passengers apart, and they pick out enough survivors to land above always predicting death (0.618028) but not enough to reach the honest model, which learned from the same seven columns with no boat to lean on. The same models scored with the real columns read 0.955684, the P2 number a team would have shipped on.

**Common wrong prediction:** about level with the honest model, on the idea that a blank column just falls back to the other seven. It does not. In training a blank boat never meant unknown: it meant no lifeboat on record, which nearly always meant death. With every boat blank, the model predicts survival for 0.155105 of the passengers against 0.381972 who survived, and it lands below the honest model on every seed.

</details>

<details><summary>Rebuild check</summary>

- Solution: `answers/rebuild/07_leak_scan.py`. Stub: `m2-dont-fool-yourself/rebuild/07_leak_scan.py` (the same file with the three bodies replaced by `raise NotImplementedError("write this from memory")`).
- `rebuildcheck`: stub fails as it should (exit 1, NotImplementedError); solution passes (exit 0, prints `check: PASS`); verdict `REBUILDCHECK OK`.
- `check()` tests `as_numeric()` on three small series (text, category and numbers, each with a missing value). On a 40-row toy frame it compares `leak_scan()` with analytic values (the planted `boat`, whose codes split the classes, scores 1; a constant column scores 0.5) and with AUCs computed once with scikit-learn 1.9.1's `cross_val_score` and hard-coded, so the stub shows no line to copy. `boat` has a value on every row, so missingness does not encode the label. `score_without()` must score one half with `DummyClassifier(strategy="most_frequent")` on the balanced folds and match a hard-coded `cross_val_score` accuracy for a depth-2 tree.
- The lab's own `--check`: the reference prints `check: PASS`; the starter raises `NotImplementedError: TODO(human)` (exit 1). Its 20-row fixture is built the same way. The wrong bodies tried against both checks are in the build notes.

</details>

<details><summary>Card drafts</summary>

Three cards go to the bank: 07-M, 07-N, and 07-T or 07-D, whichever type is due at this close (T and D alternate from one close to the next). Labs 06 and 08 draft D, so 07-T is the default and 07-D the spare.

| ID | Lab | Type | Question |
|---|---|---|---|
| 07-M | 07 | M | Why does the Titanic model trained with `boat` score below the honest model when `boat` is blank at boarding time, even though it still has all seven honest columns? |
| 07-N | 07 | N | In lab 07, what did 5-fold CV accuracy do when `boat` and `body` joined the seven boarding-time columns, and why that much? |
| 07-T | 07 | T | Name a payments field that plays the role of Titanic's `boat`. What does a fraud model trained with it do at authorization time, when that field is blank, and what fixes it? |
| 07-D | 07 | D | A new fraud model's offline AUC jumps after a feature join, but in shadow it would approve almost every payment. What do you check first, and how do you confirm it? |

Keys:

- **07-M:** (1) in training a blank boat meant no lifeboat on record, which nearly always meant death, so the model leans on boat; (2) at boarding time every boat is blank, so every passenger looks like one with no lifeboat, and the seven honest columns win back only some of the survivors; (3) so it predicts too few survivors. Numbers are optional; if given, about 0.15 predicted against about 0.38 actual (accept 0.138282 to 0.16426 predicted over seeds 0 to 2; actual 0.381972 on every seed).
- **07-N:** (1) up about 15 points, from about 0.80 to about 0.95 (accept 14.1341 to 16.3461 points over seeds 0 to 2; P1 0.792223 to 0.814349, P2 0.949577 to 0.95569); (2) boat is recorded only for people who reached a lifeboat, and nearly all of them lived, so its presence nearly is the label (single-column AUC about 0.975: 0.975067 to 0.975243).
- **07-T:** (1) a field written after the decision and filled in mostly for one outcome, such as a chargeback or a fraud report on the payment; (2) at authorization it is blank for every payment, and in training a blank field went mostly with legitimate payments, so the model flags almost no fraud, as lab 07's model predicted too few survivors; (3) the fix: train on the feature vector logged at decision time, so the field has nothing to join to (repo edge-cases, "the leakage trap in training data").
- **07-D:** (1) first: for each newly joined column, ask when its value is written relative to the decision; a single-column scan flags the loud one, a column whose AUC alone is near 1; (2) to confirm: rescore the holdout with that column as it looks at decision time (blank, or joined as of the decision) and compare with a model trained without it, as lab 07's break did.

</details>

<details><summary>Build notes</summary>

**Knob changes:** one, in the break. The spec scores one 20% holdout. The reference scores the P2 model on the same 5 stratified folds as P1 and P2, each test fold with boat and body blanked, so every passenger is scored once, as at boarding time. Each test fold is still a 20% holdout.

Why: the first build scored one 262-row holdout, and its comparison of the blanked leaky model with the honest model on that holdout failed mkanswers' 2x rule (twice the larger raw spread). The build kept it on the claim that the split moves both models together, so the paired gap cancels it. That claim was wrong. A scratch harness copied the old break step exactly, reproduced its seeds 0 to 2, then ran split seeds 0 to 19. The two holdout accuracies were essentially uncorrelated, the gap's split-to-split standard deviation was larger than either accuracy's, and twice a median three-seed range of the gap exceeded the mean gap. The gap was below zero on all 20 splits, so the sign was real, but one holdout's size was not gradeable. The same harness ran the 5-fold break over seeds 0 to 19: the gap was below zero on all 20, with a split-to-split standard deviation several times smaller. Everything else is the spec's: LightGBM defaults, `StratifiedKFold(5, shuffle=True)`, name, ticket, cabin and home.dest dropped, boat categorical, body numeric, `pd.api.types.is_numeric_dtype` in `as_numeric()`.

**2x spread rule:** every effect passed to mkanswers clears twice the larger raw spread. P2 against P1: effect 0.15176199999999998, spread 0.02212599999999998. The comparison P3 asks about, `P3.leaky_blanked_accuracy:P1.cv_accuracy` (on the same folds the honest model is the baseline's): effect -0.06594433333333334, spread 0.02212599999999998. The collapse, `P3.leaky_blanked_accuracy:break.leaky_real_accuracy`: effect -0.21770633333333334, spread 0.012230999999999992. The graded size, `P3.gap_points`, is -5.42219, -5.80621 and -8.55488, all below zero, with a spread of 3.132690000000001. Its mean clears twice that spread too, narrowly: seed 2 has the highest `P1.cv_accuracy` and the lowest blanked accuracy of the three. With the leak in, few rows stay hard, so reshuffling the folds moves the P2 score less than P1's (spread 0.006113000000000035 against 0.02212599999999998).

**Precomputed steps:** none. Every run takes seconds.

**Choices where the spec is silent:**

- The break uses the baseline's and the change's folds, `StratifiedKFold(5, shuffle=True, random_state=seed)`, and reports the mean over the 5 test folds, as `cross_val_score` does. So `break.leaky_real_accuracy` equals `P2.cv_accuracy`, and the stratified folds keep `break.actual_survival_rate` and `break.all_died_accuracy` the same on every seed.
- Top-3 importances are LightGBM gain shares from one model fit on all rows with boat and body. Split counts favour many-valued numeric columns such as age and fare; gain shows where the predictions come from. Lab 08 compares split, gain and permutation importance.
- LightGBM runs with `n_jobs=1` and `verbose=-1`: bit-reproducible, and no thread contention when three light runs share the CPU.
- `--smoke` uses a 300-row sample. Its stand-in for `leak_scan()` is `roc_auc_score` on boat and body only, the two columns the change step prints, built differently from the TODO, so the starter passes smoke with the TODO open.
- `load_data()` turns sex, embarked and boat into unordered categories built from their string values. The parquet fallback stores ordered categories and uint8 integers, and LightGBM treats ordered categories as numbers. After this step both sources give identical frames (checked with `pd.testing.assert_frame_equal`).
- Both `check()` fixtures plant boat with a value on every row and codes that split the two classes, instead of "filled in only for survivors", so missingness does not encode the label and the fixture does not preview the lab's mechanism. Age has a few missing values, so the -999 path runs. Expected AUCs are analytic (planted 1, constant 0.5) or computed once with scikit-learn 1.9.1's `cross_val_score` and hard-coded, so neither check shows the recipe. Both fixtures are built from arithmetic, not a random generator, so a NumPy upgrade cannot shift them.
- Wrong bodies, run through the shipped `check()` code in a scratch harness. The lab's `--check`, 13 wrong `leak_scan()` bodies: 12 fail (depth 2, unlimited depth, unshuffled folds, plain `KFold`, accuracy instead of AUC, ascending sort, the target left in, pooled out-of-fold AUC, the median of the fold AUCs, inline codes with missing as -1, inline codes with missing as NaN, missing filled with the column mean). The one that passes fills missing with 0: a tree cannot tell 0 from -999 when both sit below every age, so it behaves the same. The rebuild's `check()`: the same 13 `leak_scan()` bodies give the same verdicts, and every wrong `score_without()` (plain `KFold`, unshuffled folds, the target kept, the model argument ignored, AUC instead of accuracy) and every wrong `as_numeric()` (no fill, missing left as NaN, fill with 0, fill with the mean, a `dtype == object` test) fails.
- The TODO is `leak_scan()` alone, 7 body lines, below the fading plan's 12 to 20. The spec fixes it (`TODO(human): leak_scan()`), so the short size is by design. `as_numeric()` and `score_without()` ship working outside the CONCEPT markers, and the rebuild asks for all three from memory, about 12 body lines, as lab 09 does with `pr_curve()`.

**Deviations from the spec:**

- The break scores 5 folds, not one 20% holdout (knob change above).
- P3 is Kind dir, not the spec's pick. The spec's P3 asks "above or below ... and by how many points", and a pick row grades only the option. On 5 folds the size is stable enough to grade on `P3.gap_points`. The question offers above, below or the same, the three values `P3.leaky_vs_honest` can print.
- `P3.honest_accuracy` is gone. On the same folds the honest model is the baseline's, so the break reads `P1.cv_accuracy` with `labkit.prior()` instead of retraining the baseline. `P3.gap_points` and `P3.leaky_vs_honest` print only when the baseline ran first at the same seed, like `P2.delta_points`.
- `leak_scan()` and `score_without()` take a `seed=0` keyword beyond the spec's signatures, so `--seed` reaches the scan's folds and the CV folds. At the default they behave as the spec's signatures.
- RESULT lines beyond the spec's Record list: `P2.delta_points`, `P3.gap_points` and `P3.leaky_vs_honest`, so P2 and P3 grade mechanically; and `change.scan_auc_boat`, `change.scan_auc_body` and `change.scan_flagged`, because `--change` runs the learner's `leak_scan()` (the TODO) and the goal names the scan.

**Prototype comparison** (spec values against the reference; the prototype scored one 20% holdout, the reference averages 5 test folds):

| Quantity | Prototype | Reference seed 0 | Seeds 1 and 2 | Verdict |
|---|---|---|---|---|
| CV accuracy, honest (P1) | 0.804 | 0.792223 | 0.799093, 0.814349 | inside the seed range |
| CV accuracy, with boat and body (P2) | 0.947 | 0.955684 | 0.949577, 0.95569 | same direction, gap under 2x spread |
| Leaky model, real columns | 0.960 | 0.955684 | 0.949577, 0.95569 | gap under 2x spread |
| Leaky model, blanked | 0.753 | 0.738001 | 0.741031, 0.7288 | same direction, gap under 2x spread |
| Honest model | 0.787 | 0.792223 (P1, same folds) | 0.799093, 0.814349 | gap under 2x spread |
| Blanked minus honest | 0.753 minus 0.787 | -5.42219 points | -5.80621, -8.55488 | same sign, gap under 2x spread |
| Predicted survival, blanked | 15.2% | 0.155105 | 0.16426, 0.138282 | inside the seed range |
| Actual survival | 38% | 0.381972 | 0.381972, 0.381972 | match |
| All-died accuracy | 61.8% | 0.618028 | 0.618028, 0.618028 | match |

Every direction matches, and every gap is under 2x the seed spread, so no cause is needed. The prototype's holdout values also sit inside the range of the scratch harness's 20 holdout splits of the old break step (blanked, honest, real columns, predicted survival and the gap): one 262-row holdout can land there.

**Card type:** labs 06 and 08 draft D cards, so lab 07 drafts 07-T as the default and keeps 07-D as the spare. The AI uses whichever type is due at the close.

</details>
