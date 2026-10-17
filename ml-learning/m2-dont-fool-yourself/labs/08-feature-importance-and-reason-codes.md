# 08. Which features does the model use? Split counts, permutation importance and reason codes

> Goal: after this I can rank 15 columns three ways, test each ranking against a planted random column, and print the top-3 reasons for one decision with the milliseconds they cost. (No result values anywhere in this file.)

**Level:** C (see `ml-learning/CLAUDE.md`). **Output style:** Learning
**Concept link:** [`../README.md#feature-importance-and-reason-codes`](../README.md#feature-importance-and-reason-codes) (read after the lab)
**Borrowed from:** [fastbook ch 9](https://github.com/fastai/fastbook/blob/master/09_tabular.ipynb) (feature importance, partial dependence, tree interpreter); Kaggle [Machine Learning Explainability](https://www.kaggle.com/learn/machine-learning-explainability) (permutation importance, partial plots, SHAP values; SHAP is SHapley Additive exPlanations); scikit-learn example [Permutation Importance vs Random Forest Feature Importance (MDI)](https://scikit-learn.org/stable/auto_examples/inspection/plot_permutation_importance.html) (MDI: mean decrease in impurity). Do it after the lab, as the second contact 1 to 3 days later.
**Dataset:** Adult census income (OpenML 1590, shared with lab 03), 48,842 rows, 14 columns plus one added column `random` (integers 0 to 9,999, drawn with the run's seed), about 0.7 MB (gzipped ARFF, the Attribute-Relation File Format, in `~/ml-data/openml`), https://www.openml.org/d/1590 (fallback https://data.openml.org/datasets/0000/1590/dataset_1590.pq), OpenML 'Public'; the UCI (University of California, Irvine) Machine Learning Repository original is CC BY 4.0 (Creative Commons Attribution 4.0)
**Runs on:** cpu. **Lane:** light. **Compute:** 3 runs x 1 min, at most 6 min per run. Precomputed steps: none
**Needs:** base install only (TreeSHAP, the exact SHAP algorithm for tree models, comes from LightGBM's `predict(pred_contrib=True)`; no `shap` package)
**Before the session** (from the module folder, see section 2): run `--download` and `--smoke` (both work while the TODO is still open). `--check` fails until you write the TODO; that is expected.
**Interview question:** A merchant asks why a payment was declined: what can you tell them, and what does each explanation cost at serving time?
**Repo link:** `hld/payments-risk-decisioning/solution.md` [§5.9 "A merchant asks why their customer was declined. And what is in PCI scope?"](../../../hld/payments-risk-decisioning/solution.md#59-a-merchant-asks-why-their-customer-was-declined-and-what-is-in-pci-scope-security) (PCI: Payment Card Industry), and `hld/payments-risk-decisioning/edge-cases.md` ["Edge case: a merchant asks why their customer was declined"](../../../hld/payments-risk-decisioning/edge-cases.md#edge-case-a-merchant-asks-why-their-customer-was-declined)
**Captured by the script:** P1, P2, P3 and every Record row. **Human steps:** none
**Status:** todo

## 0. Retrieval (0:00, 5 min, closed book, no AI)

The AI asks up to three due cards from `../../quiz-bank.md`, one at a time. Do not open the bank first.

## 1. Predict (0:05, 7 min, no AI)

Level C: read `scripts/08_feature_importance_and_reason_codes.py` for 3 minutes first, including the docstring of `permutation_importance_auc()`, the TODO you write in section 3.

Write each row here before anything runs; the AI copies it into `../../prediction-log.md` word for word. A row that asks for several numbers becomes one log row per number, each with its own range. Ranks count from 1 (most important) to 15 (least important). Ties share the better rank. P1 and P2 each ask for two answers: a hit needs both.

| Step | Question | Kind | Prediction | 80% range or confidence |
|---|---|---|---|---|
| P1 | `LGBMClassifier(n_estimators=100, random_state=0)` on lab 03's split (stratified 80/20, seed 0), all 15 columns: the rank of `random` under split-count importance (`feature_importances_`), and under validation permutation importance (mean drop in AUC, the area under the receiver operating characteristic curve, over 5 shuffles). Two ranks, each with its own 80% range | num | | |
| P2 | Same model and split, retrained without `relationship`, then without `relationship` and `marital-status` together: validation AUC change against the full model. For each drop: up, down or same, plus a size range as an AUC difference on the 0 to 1 scale | dir | | |
| P3 | Retrain with `n_estimators=500` (seed 0, `random` still present): the rank of `random` under split-count importance | num | | |

## 2. Setup (before the session)

```
$ source ~/.venvs/ml/bin/activate
$ cd m2-dont-fool-yourself    # from ml-learning/, where sessions start
$ python scripts/08_feature_importance_and_reason_codes.py --download
$ python scripts/08_feature_importance_and_reason_codes.py --smoke
```

## 3. Baseline (0:12, 10 min)

Why: before you trust a ranking, see where each measure puts a column that cannot carry signal.

First the TODO, before this run: write the body of `permutation_importance_auc()` in `scripts/08_feature_importance_and_reason_codes.py` (between the `CONCEPT` markers). Then run `python scripts/08_feature_importance_and_reason_codes.py --check` until it prints `check: PASS`. It compares your function with `sklearn.inspection.permutation_importance` on a 20-row fixture.

```
$ python scripts/08_feature_importance_and_reason_codes.py --baseline
(paste your RESULT lines)
```

Prediction vs actual, one sentence. The reference run is in `../../answers/`; the AI opens it only after your P1 row exists and you have pasted your own RESULT lines.

Then read the three `baseline.reasons_` lines and the two `baseline.ms_per_` lines. One sentence: what would you tell the merchant about the top-scored row, and what would it cost to explain every payment inline?

## 4. Change one thing (0:22, 10 min)

Change: drop `relationship` and retrain, then drop `relationship` and `marital-status` together and retrain (100 trees, same split). The script prints the validation AUC change each time. P2 is logged above.

Why: retraining without a column is the most direct test of what the model gets from it; here it runs for one column, then for two.

The change lines read the baseline's AUC for the same seed, so run `--baseline` first.

```
$ python scripts/08_feature_importance_and_reason_codes.py --change
(paste your RESULT lines)
```

## 5. Break it (0:32, 10 min, AI gives hints only; the run finishes by 0:40)

Break: retrain with 500 trees instead of 100, with `random` still present. P3 is logged above.

Why: the number of trees is the first knob most people raise, so read every ranking again at 500 trees.

```
$ python scripts/08_feature_importance_and_reason_codes.py --break
(paste your RESULT lines)
```

Why, in three sentences, written without AI:

## 6. Explain-back (0:42, 5 min) and rebuild (0:47, 10 min), no AI

- Five sentences for a smart engineer new to ML, written without AI. The AI names your weakest claim after the session (section 7).
- Rebuild: open `rebuild/08_permutation_importance.py`, write the body from memory, then run `python rebuild/08_permutation_importance.py`. Its `check()` compares with `sklearn.inspection.permutation_importance`, never with this lab's results.

## 7. What I learned

After the session (about 5 minutes): the AI names the weakest claim in your five sentences and asks one question that tests it. Edit the sentences here.

## 8. Interview soundbite (one of the three cards written at 0:57)

> (Your one or two sentences, written after the runs: only someone who ran this would say them.)

Staff follow-up (trade-off): why does the repo compute SHAP asynchronously, and only for `DECLINE` and `REVIEW`, instead of inline for every payment, and what does the merchant see meanwhile? Answer in 2 sentences from the repo link (solution.md §5.9). Rotate: simplest design, failure modes, migration, what pages at 3 am, cost, trade-off.

## 9. Quiz cards (0:57, 3 min)

The AI drafts three cards (M, N, and T or D). Edit or replace them. Questions go to `../../quiz-bank.md`, keys to `../../answers/quiz-key.md`.

## Record

The script prints these as RESULT lines. Paste, do not type.

| Metric | Your run | Hardware (the script's HW line) | Captured by (script or learner) |
|---|---|---|---|
| `P1.random_rank_split`: rank of `random` by split count, 100 trees (of 15) | | | script |
| `P1.random_rank_perm`: rank of `random` by validation permutation importance, 100 trees (of 15) | | | script |
| `baseline.random_rank_gain`: rank of `random` by total gain, 100 trees (of 15) | | | script |
| `baseline.auc`: validation AUC (fraction), 100 trees, all 15 columns | | | script |
| `baseline.sex_shap_rank`: rank of `sex` by mean absolute SHAP value (of 15), a first-pass fairness check | | | script |
| `baseline.reasons_1`: top-3 SHAP reasons (column=value:log-odds) for the highest-scored validation row | | | script |
| `baseline.reasons_2`: the same for the second-highest row | | | script |
| `baseline.reasons_3`: the same for the third-highest row | | | script |
| `baseline.ms_per_score`: ms to score one row (median of 200, one thread) | | | script |
| `baseline.ms_per_explanation`: ms to explain one row with TreeSHAP (median of 200, one thread) | | | script |
| `P2.auc_without_relationship`: validation AUC (fraction) without `relationship` | | | script |
| `P2.auc_change_without_relationship`: that AUC minus `baseline.auc` (fraction) | | | script |
| `P2.auc_without_both`: validation AUC (fraction) without `relationship` and `marital-status` | | | script |
| `P2.auc_change_without_both`: that AUC minus `baseline.auc` (fraction) | | | script |
| `P3.random_rank_split`: rank of `random` by split count, 500 trees (of 15) | | | script |
| `break.random_rank_perm`: rank of `random` by validation permutation importance, 500 trees (of 15) | | | script |
| `break.random_rank_gain`: rank of `random` by total gain, 500 trees (of 15) | | | script |
| `break.auc`: validation AUC (fraction), 500 trees | | | script |
