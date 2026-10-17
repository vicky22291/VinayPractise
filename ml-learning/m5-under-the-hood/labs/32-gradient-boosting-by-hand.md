# 32. Gradient boosting by hand: each small tree fits what the others missed

> Goal: after this I can write a 10-line boosting loop, measure its AUC (area under the receiver operating characteristic curve) against LightGBM's, and show what a learning rate of 1.0 does with and without early stopping. (No result values anywhere in this file.)

**Level:** S (see `ml-learning/CLAUDE.md`). **Output style:** Explanatory
**Concept link:** `../README.md#gradient-boosting` (read after the lab)
**Borrowed from:** [Kaggle Intermediate ML, XGBoost lesson](https://www.kaggle.com/code/alexisbcook/xgboost); [fastbook ch 9, the Boosting section](https://github.com/fastai/fastbook/blob/master/09_tabular.ipynb); [LightGBM docs, Parameters Tuning](https://lightgbm.readthedocs.io/en/latest/Parameters-Tuning.html); [Friedman 2001, "Greedy Function Approximation: A Gradient Boosting Machine"](https://doi.org/10.1214/aos/1013203451). Do it after the lab, as the second contact 1 to 3 days later.
**Dataset:** Adult census income (OpenML 1590), 48,842 rows and 14 features, split as in labs 03 and 31 (stratified 80/20, `random_state=0`: 39,073 training rows, 9,769 validation rows), 0.66 MB download, https://www.openml.org/d/1590, OpenML Public (the original in the UCI, University of California Irvine, Machine Learning Repository is CC BY 4.0, Creative Commons Attribution)
**Runs on:** cpu. **Lane:** light. **Compute:** 3 runs x 1 min, at most 6 min per run. Precomputed steps: none
**Needs:** base install only
**Before the session** (from the module folder, see section 2): `--download` (Adult into `~/ml-data/openml`, with two fallback sources built in), then `--smoke` (under a minute).
**Interview question:** Why does a GBDT (gradient-boosted decision trees) need about 1,000 trees, and what does each tree cost per request?
**Repo link:** [`hld/payments-risk-decisioning/solution.md`, §10.1 Internals of each chosen technology](../../../hld/payments-risk-decisioning/solution.md#101-internals-of-each-chosen-technology), the "GBDT inference" bullet
**Captured by the script:** P1, P2, P3 and every Record row. **Human steps:** none
**Status:** todo

## 0. Retrieval (0:00, 5 min, closed book, no AI)

The AI asks up to three due cards from `../../quiz-bank.md`, one at a time. Do not open the bank first.

## 1. Predict (0:05, 7 min, no AI)

Level S: first read `load_data()` and `report()` in `scripts/32_gradient_boosting_by_hand.py` (2 minutes). They fix the split and the RESULT names your harness must print. There is no loop to read yet: predict from the configs in the table.

Write each row here before anything runs; the AI copies it into `../../prediction-log.md` word for word. A row that asks for several numbers becomes one log row per number, each with its own range.

| Step | Question | Kind | Prediction | 80% range or confidence |
|---|---|---|---|---|
| P1 | Validation AUC of your loop after 300 depth-3 trees at learning rate 0.1, minus LightGBM's (defaults, 31 leaves per tree, learning rate 0.1, up to 1,000 trees, early stopping 50 on validation log-loss). Seed 0, 39,073 training rows, 9,769 validation rows, in AUC units. | num | | |
| P2 | Learning rate 1.0 in your loop (still 300 depth-3 trees, seed 0): validation log-loss at tree 300, direction (up, down or same) and size as the log-loss difference, rate 1.0 minus rate 0.1. | dir | | |
| P3 | LightGBM (defaults, 31 leaves) with learning_rate 1.0, 300 trees and no early stopping, seed 0: validation log-loss at tree 300. | num | | |

## 2. Setup (before the session)

```
$ source ~/.venvs/ml/bin/activate
$ cd m5-under-the-hood    # from ml-learning/, where sessions start
$ python scripts/32_gradient_boosting_by_hand.py --download
$ python scripts/32_gradient_boosting_by_hand.py --smoke
```

## 3. Baseline (0:12, 10 min)

Why: the loop and LightGBM read the same split and the same numeric matrix, so any AUC difference comes from the booster, not the data.

You write these first, with no AI (about 5 minutes). Each blank in items 1 and 2 takes one line.

1. The loop plan, in your own words. Item 3 gives the formula; these lines ask for the reasons behind it. The gradient is lab 28's, now taken with respect to the score F.
   - Why F0 is the log-odds of the base rate:
   - Why y - sigmoid(F) is the negative gradient of log-loss in F, in one line of calculus:
   - Why each round fits a tree to r instead of adding r to F directly:
2. `load_data()` and `report()` already exist: say what they fix, what `--seed` changes, and what each mode passes to `report()`. Your Metric line has to state these definitions. Every validation log-loss is `sklearn.metrics.log_loss` on sigmoid of the raw score F. Every AUC is `roc_auc_score` on the raw score F (the log-odds). LightGBM is scored the same way: on its raw score from `predict_proba(X, raw_score=True)`, never with its built-in eval metric, so your numbers and the reference use one definition.
   - Split:
   - Metric:
   - RESULT contract:
3. `boost(X, y, n_trees, lr, seed)` in `scripts/32_gradient_boosting_by_hand.py`, from this formula:
   - p = the mean of the training labels y. F0 = log(p / (1 - p)). F starts at F0 for every training row.
   - Repeat n_trees times: r = y - sigmoid(F); fit `DecisionTreeRegressor(max_depth=3, random_state=seed)` to (X, r); F = F + lr * tree.predict(X).
   - Return (F0, trees). A new row scores F0 + lr * (the sum of every tree's prediction for it), and its probability is sigmoid of that score.

Then prompt the AI with your plan and the three lines of item 2. It writes the harness for all three modes in one pass, and it has to cover:

- Baseline, your loop: `boost()` at learning rate 0.1, with the validation log-loss after 10, 100 and 300 trees and the AUC after 300.
- Baseline, LightGBM: its defaults (learning rate 0.1, up to 1,000 trees, `lgb.early_stopping(50)` on the validation rows), and the mean depth of its trees.
- Baseline, timing: one row per call, one thread, the median of 200 calls after 20 warmup calls, with the first 300 and then all 1,000 trees of a LightGBM model trained at rate 0.1 for 1,000 trees with no early stopping.
- Change: your loop at rate 1.0, with the same checkpoints and AUC, and the log-loss delta from the baseline run at the same seed (`labkit.prior`).
- Break: LightGBM at rate 1.0 for 300 trees with no early stopping, then again with `early_stopping(50)`.

Annotate each AI block in one line before the first run. If this block runs over, the change step absorbs it: the harness already covers `--change` and that run is short, so the break still finishes by 0:40.

```
$ python scripts/32_gradient_boosting_by_hand.py --baseline
(paste your RESULT lines)
```

Prediction vs actual, one sentence. The reference run is in `../../answers/`; the AI opens it only after your P1 row exists and you have pasted your own RESULT lines.

## 4. Change one thing (0:22, 10 min)

Why: the learning rate scales every tree's step, and holding the tree count at 300 shows what the step size alone does.

Change: learning rate 1.0 instead of 0.1 in your loop (300 depth-3 trees, seed 0). It prints the change against your baseline run at the same seed, so run `--baseline` first. P2 is logged above.

```
$ python scripts/32_gradient_boosting_by_hand.py --change
(paste your RESULT lines)
```

## 5. Break it (0:32, 10 min, AI gives hints only; the run finishes by 0:40)

Why: early stopping is what picks the tree count in practice. This run takes it away at the largest step size, then puts it back.

Break: train LightGBM at its defaults with learning_rate 1.0 for 300 trees and no early stopping; then train it again with `early_stopping(50)`. P3 is logged above.

```
$ python scripts/32_gradient_boosting_by_hand.py --break
(paste your RESULT lines)
```

Why, in three sentences, written without AI:

## 6. Explain-back (0:42, 5 min) and rebuild (0:47, 10 min), no AI

- Five sentences for a smart engineer new to ML, written without AI. The AI names your weakest claim after the session (section 7).
- Rebuild: at 0:47, not before, open `rebuild/32_boosting_loop.py`, write the body from memory, then run `python rebuild/32_boosting_loop.py`. Its `boost(X, y, X_new, n_trees, lr)` is not your lab `boost()`: it also scores a second matrix, X_new, and returns `(F0, history, F_new)`, where history holds the training scores after every tree. Its `check()` compares with scikit-learn (`GradientBoostingClassifier(max_depth=3, learning_rate=0.1, n_estimators=50)`, `log_loss`, `roc_auc_score`) on synthetic data, never with this lab's results.

## 7. What I learned

After the session (about 5 minutes): the AI names the weakest claim in your five sentences and asks one question that tests it. Edit the sentences here.

## 8. Interview soundbite (one of the three cards written at 0:57)

> (Your soundbite: one or two sentences only someone who ran this would say.)

Staff follow-up (what pages at 3 am): a new model version is live, and on a share of payments the model stage now misses its 45 ms deadline. What answer do those payments get, and which page fires? Answer in 2 sentences from the repo link (the stage deadlines in §10.2 and the pages in §8 of the same file). Rotate: simplest design, failure modes, migration, what pages at 3 am, cost, trade-off.

## 9. Quiz cards (0:57, 3 min)

The AI drafts three cards (M, N, and T or D). Edit or replace them. Questions go to `../../quiz-bank.md`, keys to `../../answers/quiz-key.md`.

## Record

The script prints these as RESULT lines. Paste, do not type.

| Metric | Your run | Hardware (the script's HW line) | Captured by (script or learner) |
|---|---|---|---|
| `P1.auc_gap`: loop AUC minus LightGBM AUC, validation, both at learning rate 0.1 | | | script |
| `baseline.loop_auc`: your loop, rate 0.1, after 300 trees | | | script |
| `baseline.lgbm_auc`: LightGBM, rate 0.1, at its best iteration | | | script |
| `baseline.loop_logloss_10`: your loop, rate 0.1, validation log-loss after 10 trees | | | script |
| `baseline.loop_logloss_100`: the same after 100 trees | | | script |
| `baseline.loop_logloss_300`: the same after 300 trees | | | script |
| `baseline.lgbm_logloss`: LightGBM, rate 0.1, validation log-loss at its best iteration | | | script |
| `baseline.lgbm_best_iter`: LightGBM's best iteration at rate 0.1, early stopping 50 | | | script |
| `baseline.lgbm_depth`: mean depth of LightGBM's trees in split levels (each loop tree has 3) | | | script |
| `baseline.lgbm_us_300`: microseconds per single-row prediction, first 300 trees, one thread | | | script |
| `baseline.lgbm_us_1000`: the same with all 1,000 trees | | | script |
| `P2.loop_logloss_300`: your loop, rate 1.0, validation log-loss after 300 trees | | | script |
| `P2.loop_logloss_300_delta`: rate 1.0 minus rate 0.1, after 300 trees (needs `--baseline` run first with the same seed) | | | script |
| `change.loop_logloss_10`: your loop, rate 1.0, after 10 trees | | | script |
| `change.loop_logloss_100`: your loop, rate 1.0, after 100 trees | | | script |
| `change.loop_auc`: your loop, rate 1.0, after 300 trees | | | script |
| `P3.lgbm_logloss_300`: LightGBM, rate 1.0, validation log-loss at tree 300, no early stopping | | | script |
| `break.lgbm_auc_300`: the same model's validation AUC | | | script |
| `break.lgbm_best_iter`: LightGBM's best iteration at rate 1.0, early stopping 50 | | | script |
| `break.lgbm_best_logloss`: LightGBM, rate 1.0, validation log-loss at that best iteration | | | script |
