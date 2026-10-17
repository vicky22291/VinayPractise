# 06. Leak through preprocessing: fit every transform inside each fold

> Goal: after this I can measure what target-encoding before the split does to the CV MAE (mean absolute error), in dollars and in percent, and explain why rows per level drive it. (No result values anywhere in this file.)

**Level:** C (see `ml-learning/CLAUDE.md`). **Output style:** Learning
**Concept link:** `../README.md#leakage-through-preprocessing` (read after the lab)
**Borrowed from:** Kaggle [Intermediate Machine Learning](https://www.kaggle.com/learn/intermediate-machine-learning): Pipelines, Cross-Validation, Data Leakage. Do it after the lab, as the second contact 1 to 3 days later.
**Dataset:** House Prices (OpenML 42165, derived from the Ames housing data, De Cock 2011), 1,460 rows, 81 columns, target `SalePrice`, 0.2 MB, https://www.openml.org/d/42165, licence: the OpenML licence field says "NA"
**Runs on:** cpu. **Lane:** light. **Compute:** 9 runs x 1 min (baseline, change and break, each at seeds 0, 1 and 2), at most 6 min per run. Precomputed steps: none
**Needs:** base install only
**Before the session** (from the module folder, see section 2): `--download` (OpenML 42165 into `~/ml-data/openml/`) and `--smoke`. Both work before the TODO is written.
**Interview question:** Your target-encoded merchant_id lifts offline AUC (area under the ROC, receiver operating characteristic, curve) by 0.05: how do you prove it is not leaking?
**Repo link:** `hld/payments-risk-decisioning/deep-dives/model-lifecycle-shadow-and-labels.md`, §2 "Leakage: the trap in the training data"
**Captured by the script:** every RESULT line of `--baseline`, `--change` and `--break` at seeds 0, 1 and 2. **Human steps:** the seed spread of each MAE, by hand from your three seeds
**Status:** todo

## 0. Retrieval (0:00, 5 min, closed book, no AI)

The AI asks up to three due cards from `../../quiz-bank.md`, one at a time. Do not open the bank first.

## 1. Predict (0:05, 7 min, no AI)

Level C: you write the two TODO(human) functions in `scripts/06_leak_through_preprocessing.py`, `encode()` and `cv_mae()`, at 0:12. Predict first.

Write each row here before anything runs; the AI copies it into `../../prediction-log.md` word for word. A row that asks for several numbers becomes one log row per number, each with its own range.

Every step uses the same model and folds: LightGBM with 300 trees and learning rate 0.05, on the 36 numeric columns plus one target-encoded column (smoothing 10), scored by `KFold(5, shuffle=True, random_state=seed)`. The predictions are for seed 0.

| Step | Question | Kind | Prediction | 80% range or confidence |
|---|---|---|---|---|
| P1 | 5-fold CV (cross-validation) MAE in dollars, seed 0, with Neighborhood (25 levels, about 58 rows each) target-encoded inside each fold | num | | |
| P2 | Fit the Neighborhood encoding on all 1,460 rows before KFold instead, seed 0: the MAE change (leaky minus in-fold), as up, down or same, plus a range in dollars for the change. Same means the change is smaller in size than the seed spread of `P1.mae_infold` (max minus min over your three baseline seeds). Up and down mean a change at least that big, on that side | dir | | |
| P3 | Key Neighborhood x YearBuilt (501 levels, 2.9 rows each), seed 0, encoded on all rows before KFold vs inside each fold: the MAE gap, (in-fold MAE minus leaky MAE) / in-fold MAE, in percent, with its sign | num | | |

## 2. Setup (before the session)

```
$ source ~/.venvs/ml/bin/activate
$ cd m2-dont-fool-yourself    # from ml-learning/, where sessions start
$ python scripts/06_leak_through_preprocessing.py --download
$ python scripts/06_leak_through_preprocessing.py --smoke
```

## 3. Baseline (0:12, 10 min)

Why: the number with no validation leak. Each fold's encoding is fit on its own training rows only, so no validation price reaches it, and a validation house is scored like a house the model has never seen.

Write the TODO first: `encode()` and `cv_mae()`, from their docstrings. Run `--check` until it prints `check: PASS`, then the baseline. The AI gives hints, or a draft it explains line by line that you type. P1 is the seed 0 line; seeds 1 and 2 are for the Record's spread.

```
$ python scripts/06_leak_through_preprocessing.py --check
$ for s in 0 1 2; do python scripts/06_leak_through_preprocessing.py --baseline --seed $s; done
(paste your RESULT lines)
```

Prediction vs actual, one sentence. The reference run is in `../../answers/`; the AI opens it only after your P1 row exists and you have pasted your own RESULT lines.

## 4. Change one thing (0:22, 10 min)

Change: fit the Neighborhood encoding once, on all 1,460 rows, before KFold (`cv_mae(..., leaky=True)`). P2 is logged above.

Why: this is how a notebook often does it: encode the whole table, then cross-validate. Each seed reads its own baseline value, so run the baseline loop first.

```
$ for s in 0 1 2; do python scripts/06_leak_through_preprocessing.py --change --seed $s; done
(paste your RESULT lines)
```

After the loop: write each seed's `P2.mae_change` next to the seed spread of `P1.mae_infold` from your baseline loop.

## 5. Break it (0:32, 10 min, AI gives hints only; the run finishes by 0:40)

Break: swap the key for Neighborhood x YearBuilt (501 levels) and encode it both ways, inside each fold and on all rows before KFold. P3 is logged above.

Why: the same model, folds and smoothing, on a finer key: 2.9 rows per level instead of about 58.

```
$ for s in 0 1 2; do python scripts/06_leak_through_preprocessing.py --break --seed $s; done
(paste your RESULT lines)
```

After the loop: write each seed's `break.mae_change` next to the seed spread of `break.mae_cross_infold` over the same three seeds.

Why, in three sentences, written without AI:

## 6. Explain-back (0:42, 5 min) and rebuild (0:47, 10 min), no AI

- Five sentences for a smart engineer new to ML, written without AI. The AI names your weakest claim after the session (section 7).
- Rebuild: open `rebuild/06_in_fold_target_encoding.py`, write the bodies of `encode()` and `cv_mae()` from memory, then run `python rebuild/06_in_fold_target_encoding.py`. Its `check()` compares with scikit-learn (`TargetEncoder`, and a `Pipeline` inside `cross_val_score`) and with a pandas groupby mean, never with this lab's results.

## 7. What I learned

After the session (about 5 minutes): the AI names the weakest claim in your five sentences and asks one question that tests it. Edit the sentences here.

## 8. Interview soundbite (one of the three cards written at 0:57)

> (Your soundbite: one or two sentences only someone who ran this would say.)

Staff follow-up (failure modes): your in-fold CV is clean, but the production merchant_id encoding is rebuilt every night from all chargebacks to date, and training joins it to last month's payments. Which item of §2 does that break, and what should the training job check? Answer in 2 sentences from the repo link. Rotate: simplest design, failure modes, migration, what pages at 3 am, cost, trade-off.

## 9. Quiz cards (0:57, 3 min)

The AI drafts three cards (M, N, and T or D). Edit or replace them. Questions go to `../../quiz-bank.md`, keys to `../../answers/quiz-key.md`.

## Record

The script prints these as RESULT lines. Paste, do not type. Your run: the seed 0 value; the last row uses all three seeds.

| Metric | Your run | Hardware (the script's HW line) | Captured by (script or learner) |
|---|---|---|---|
| `baseline.mae_numeric_only`: CV MAE, numeric columns only (usd) | | | script |
| `P1.mae_infold`: CV MAE, Neighborhood encoded inside each fold (usd) | | | script |
| `P2.mae_leaky`: CV MAE, Neighborhood encoded on all rows before KFold (usd) | | | script |
| `P2.mae_change`: leaky minus in-fold, Neighborhood (usd) | | | script |
| `change.gap_pct`: in-fold minus leaky, as a share of in-fold, Neighborhood (percent) | | | script |
| `break.mae_cross_infold`: CV MAE, Neighborhood x YearBuilt encoded inside each fold (usd) | | | script |
| `break.mae_cross_leaky`: CV MAE, Neighborhood x YearBuilt encoded on all rows before KFold (usd) | | | script |
| `break.mae_change`: leaky minus in-fold, Neighborhood x YearBuilt (usd) | | | script |
| `P3.gap_pct`: in-fold minus leaky, as a share of in-fold, Neighborhood x YearBuilt (percent) | | | script |
| Seed spread of each MAE: max minus min over seeds 0, 1 and 2 | | | learner |
