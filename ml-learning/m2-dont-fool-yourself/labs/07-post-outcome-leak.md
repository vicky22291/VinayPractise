# 07. Leak through a post-outcome column: ask when each value is known

> Goal: after this I can find a post-outcome column with a single-column scan (flag a column whose AUC, the area under the receiver operating characteristic curve, is 0.9 or more) and show what it does to a model scored as at decision time. (No result values anywhere in this file.)

**Level:** C (see `ml-learning/CLAUDE.md`). **Output style:** Learning
**Concept link:** `../README.md#post-outcome-columns` (read after the lab)
**Borrowed from:** Kaggle Learn [Intermediate Machine Learning](https://www.kaggle.com/learn/intermediate-machine-learning), lesson "Data Leakage"; fast.ai [Lesson 5](https://course.fast.ai/Lessons/lesson5.html), the Titanic notebooks. Do it after the lab, as the second contact 1 to 3 days later.
**Dataset:** Titanic, OpenML 40945, 1,309 rows, 14 columns (target `survived`; `boat` and `body` are filled in after the sinking), about 0.05 MB, https://www.openml.org/d/40945, OpenML "Public". Fallback: the same file as parquet, https://data.openml.org/datasets/0004/40945/dataset_40945.pq
**Runs on:** cpu. **Lane:** light. **Compute:** 3 runs x 1 min (plus `--check`, under 1 min), at most 6 min per run. Precomputed steps: none
**Needs:** base install only
**Before the session** (from the module folder, see section 2): `--download` and `--smoke` (see Setup). Both run with the TODO still open.
**Interview question:** Which of these is not known at authorization time: the AVS (address verification service) result, the 3DS (3-D Secure) outcome, the merchant's current tier, or chargebacks on the card?
**Repo link:** [`hld/payments-risk-decisioning/edge-cases.md`](../../../hld/payments-risk-decisioning/edge-cases.md#edge-case-the-leakage-trap-in-training-data), section "Edge case: the leakage trap in training data"
**Captured by the script:** P1, P2, P3 and every Record row. **Human steps:** none
**Status:** todo

## 0. Retrieval (0:00, 5 min, closed book, no AI)

The AI asks up to three due cards from `../../quiz-bank.md`, one at a time. Do not open the bank first.

## 1. Predict (0:05, 7 min, no AI)

Level C: you write the TODO(human) function in `scripts/07_post_outcome_leak.py`, `leak_scan()`, at 0:12. Predict first.

Write each row here before anything runs; the AI copies it into `../../prediction-log.md` word for word. A row that asks for several numbers becomes one log row per number, each with its own range.

The model in every step: LightGBM with its defaults (100 trees, learning rate 0.1, 31 leaves). Cross-validation (CV) here is 5-fold, stratified, shuffled with seed 0, and every step uses the same 5 folds. Accuracy is a fraction from 0 to 1; one accuracy point is 0.01.

| Step | Question | Kind | Prediction | 80% range or confidence |
|---|---|---|---|---|
| P1 | LightGBM defaults, 5-fold stratified CV, seed 0: accuracy on the 7 boarding-time columns only: pclass, sex, age, sibsp, parch, fare, embarked (no boat, no body) | num | | |
| P2 | Add boat and body (9 columns), same model, same folds, seed 0: does CV accuracy go up, down or stay the same, and by how many accuracy points? | dir | | |
| P3 | Score the P2 model as at boarding time: the same LightGBM, 9 columns and 5 folds (seed 0), with boat and body set to missing in each test fold. Is its CV accuracy above, below or the same as the honest model's P1 accuracy, and by how many accuracy points? | dir | | |

## 2. Setup (before the session)

```
$ source ~/.venvs/ml/bin/activate
$ cd m2-dont-fool-yourself    # from ml-learning/, where sessions start
$ python scripts/07_post_outcome_leak.py --download
$ python scripts/07_post_outcome_leak.py --smoke
```

## 3. Baseline (0:12, 10 min)

Why: get the honest number first, from the 7 columns a clerk could fill in at boarding.

Write the TODO first: the body of `leak_scan()` in `scripts/07_post_outcome_leak.py`, between the `CONCEPT` markers, from its docstring. Run `--check` until it prints `check: PASS`, then run the baseline. The AI gives hints, or a draft it explains line by line that you type. The `--change` run uses your scan. `--change` and `--break` both read this run's P1 value, so run the steps in order at one seed.

```
$ python scripts/07_post_outcome_leak.py --check
$ python scripts/07_post_outcome_leak.py --baseline
(paste your RESULT lines)
```

Prediction vs actual, one sentence. The reference run is in `../../answers/`; the AI opens it only after your P1 row exists and you have pasted your own RESULT lines.

## 4. Change one thing (0:22, 10 min)

Why: a real feature table carries columns that were written later; this step lets two of them in.

Change: add `boat` and `body` to the features. Same model, same folds. The run also prints the top 3 columns by LightGBM gain and, from your `leak_scan()` over all 9 columns, the AUC of boat, the AUC of body and the flagged columns. P2 is logged above.

```
$ python scripts/07_post_outcome_leak.py --change
(paste your RESULT lines)
```

## 5. Break it (0:32, 10 min, AI gives hints only; the run finishes by 0:40)

Why: a model is used at decision time, so score it with only what is known then.

Break: on the same 5 folds, train the leaky model (9 columns) on 4 folds and score the fifth with `boat` and `body` set to missing, as they are at boarding time. Each fold takes one turn as the test fold. The run compares the result with your P1 line. P3 is logged above.

```
$ python scripts/07_post_outcome_leak.py --break
(paste your RESULT lines)
```

Why, in three sentences, written without AI:

## 6. Explain-back (0:42, 5 min) and rebuild (0:47, 10 min), no AI

- Five sentences for a smart engineer new to ML, written without AI. The AI names your weakest claim after the session (section 7).
- Rebuild: open `rebuild/07_leak_scan.py`, write the bodies of `as_numeric()`, `leak_scan()` and `score_without()` from memory, then run `python rebuild/07_leak_scan.py`. Its `check()` compares with values from scikit-learn's `cross_val_score` on a toy frame, never with this lab's results.

## 7. What I learned

After the session (about 5 minutes): the AI names the weakest claim in your five sentences and asks one question that tests it. Edit the sentences here.

## 8. Interview soundbite (one of the three cards written at 0:57)

> One or two sentences only someone who ran this would say.

Staff follow-up (migration): the fraud model was trained on today's tables. How do you move its training onto the feature vectors logged at decision time, and what stops a column written after the decision from coming back? Answer in 2 sentences from the repo link. Rotate: simplest design, failure modes, migration, what pages at 3 am, cost, trade-off.

## 9. Quiz cards (0:57, 3 min)

The AI drafts three cards (M, N, and T or D). Edit or replace them. Questions go to `../../quiz-bank.md`, keys to `../../answers/quiz-key.md`.

## Record

The script prints these as RESULT lines. Paste, do not type.

| Metric | Your run | Hardware (the script's HW line) | Captured by (script or learner) |
|---|---|---|---|
| `P1.cv_accuracy`: CV accuracy, 7 boarding-time columns | | | script |
| `P2.cv_accuracy`: CV accuracy, boat and body added | | | script |
| `P2.delta_points`: P2 minus P1 in accuracy points (printed when your baseline ran first, same seed) | | | script |
| `change.top3_gain_share`: top 3 columns by share of LightGBM gain, one model fit on all rows with boat and body | | | script |
| `change.scan_auc_boat`: single-column AUC of boat in your `leak_scan()` | | | script |
| `change.scan_auc_body`: single-column AUC of body | | | script |
| `change.scan_flagged`: the columns your scan flags at AUC 0.9 or above | | | script |
| `P3.leaky_blanked_accuracy`: CV accuracy of the leaky model, boat and body blanked in each test fold | | | script |
| `P3.gap_points`: leaky blanked minus `P1.cv_accuracy`, in accuracy points (printed when your baseline ran first, same seed) | | | script |
| `P3.leaky_vs_honest`: above, below or same, against `P1.cv_accuracy` (printed when your baseline ran first, same seed) | | | script |
| `break.leaky_real_accuracy`: CV accuracy of the same leaky models, real boat and body | | | script |
| `break.predicted_survival_rate`: share of passengers the leaky model predicts survive, boat and body blanked (mean over the 5 test folds) | | | script |
| `break.actual_survival_rate`: share of passengers who survived (mean over the 5 test folds) | | | script |
| `break.all_died_accuracy`: accuracy of predicting that everyone died (mean over the 5 test folds) | | | script |
