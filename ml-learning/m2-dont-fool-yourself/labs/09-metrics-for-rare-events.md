# 09. Accuracy lies on rare events: PR-AUC, cost thresholds and their noise

> Goal: after this I can report ROC-AUC (area under the receiver operating characteristic curve) and PR-AUC (area under the precision-recall curve) with a bootstrap interval, pick the cheapest threshold for a 5:1 cost, and show what the max-accuracy threshold costs. (No result values anywhere in this file.)

**Level:** C (see `ml-learning/CLAUDE.md`). **Output style:** Learning
**Concept link:** `../README.md#metrics-for-rare-events` (read after the lab)
**Borrowed from:** Google [Machine Learning Crash Course: Classification](https://developers.google.com/machine-learning/crash-course/classification) (thresholds and the confusion matrix, accuracy, precision and recall, ROC and AUC). Do it after the lab, as the second contact 1 to 3 days later.
**Dataset:** Credit Card Fraud from ULB (Université Libre de Bruxelles), OpenML 1597, name `creditcard`. It holds 284,807 card transactions, 492 of them fraud (0.1727%). The features are V1 to V28, anonymised PCA (principal component analysis) components, and Amount. OpenML marks Time as the row id, so the loader drops it. The download is 69 MB of gzipped ARFF (Attribute-Relation File Format) from https://www.openml.org/d/1597. Licence: "Public", from the OpenML licence field. Labs 22, 24 and 27 reuse the same file.
**Runs on:** cpu. **Lane:** light. **Compute:** 6 runs x 1 min (`--check`, baseline and change once each, and break at seeds 0, 1 and 2), at most 6 min per run. Precomputed steps: none
**Needs:** base install only
**Before the session** (from the module folder, see section 2): `--download` (OpenML 1597 into `~/ml-data/openml/`; if the OpenML server is down, it fetches the 73 MB parquet copy into `~/ml-data/creditcard/`) and `--smoke`. Both work before the TODO is written.
**Interview question:** Fraud is 0.17% of payments: which metric do you report to the business, and where do you set the decline threshold?
**Repo link:** `hld/payments-risk-decisioning/deep-dives/model-lifecycle-shadow-and-labels.md`, §4 "Thresholds from cost, and why the inputs must scale"
**Captured by the script:** every RESULT line of `--baseline`, `--change` and `--break`. **Human steps:** none
**Status:** todo

## 0. Retrieval (0:00, 5 min, closed book, no AI)

The AI asks up to three due cards from `../../quiz-bank.md`, one at a time. Do not open the bank first.

## 1. Predict (0:05, 7 min, no AI)

Level C: you write the two TODO(human) functions in `scripts/09_metrics_for_rare_events.py`, `average_precision()` and `cheapest_threshold()`, at 0:12. Predict first.

Write each row here before anything runs; the AI copies it into `../../prediction-log.md` word for word. A row that asks for several numbers becomes one log row per number, each with its own range.

Every step uses one model and one split. The model is `StandardScaler` then `LogisticRegression(max_iter=5000)`. It trains on a stratified 80% of the payments and is scored on the other 20%: 56,962 test payments, 98 of them fraud. The split's `random_state` is the seed, 0 by default. A payment is declined when its fraud score is at least the threshold. Cost = 5 x missed frauds + 1 x false declines, counted in false declines. Thresholds are searched over every distinct test score, so each threshold is chosen on the same test rows it is then scored on. That makes P2, P3 and the cost at each chosen threshold in-sample: they show how each rule picks its threshold, not what that threshold would do on new payments. A threshold you ship is chosen on separate validation rows and confirmed on untouched test rows.

| Step | Question | Kind | Prediction | 80% range or confidence |
|---|---|---|---|---|
| P1 | ROC-AUC and PR-AUC (computed as average precision, never the trapezoid rule) of the logistic regression on the seed 0 test set, and the gap ROC-AUC minus PR-AUC (signed: negative if PR-AUC is higher). Three point estimates, each with its own 80% range; Hit is scored per number | num | | |
| P2 | Recall (share of the 98 test frauds declined) at the cheapest threshold when a missed fraud costs 5x a false decline, seed 0 | num | | |
| P3 | Recall at the threshold that maximises test accuracy, seed 0 | num | | |

## 2. Setup (before the session)

```
$ source ~/.venvs/ml/bin/activate
$ cd m2-dont-fool-yourself    # from ml-learning/, where sessions start
$ python scripts/09_metrics_for_rare_events.py --download
$ python scripts/09_metrics_for_rare_events.py --smoke
```

## 3. Baseline (0:12, 10 min)

Why: choose the number you would report to the business before choosing a threshold, and see how far 98 test frauds let it move.

Write the TODO first, from the docstrings: `average_precision()` and `cheapest_threshold()`. Both build on `pr_curve()`, which ships working: read it first. Keep them fast: `--baseline` calls `average_precision()` 501 times, so use the `pr_curve()` arrays and do not loop over thresholds. Run `--check` until it prints `check: PASS`, then the baseline. The AI gives hints, or a draft it explains line by line that you type.

```
$ python scripts/09_metrics_for_rare_events.py --check
$ python scripts/09_metrics_for_rare_events.py --baseline
(paste your RESULT lines)
```

Prediction vs actual, one sentence. The reference run is in `../../answers/`; the AI opens it only after your P1 row exists and you have pasted your own RESULT lines.

## 4. Change one thing (0:22, 10 min)

Change: the decline threshold, from 0.5 to the cheapest threshold for a 5:1 cost, found by your `cheapest_threshold()`. P2 is logged above.

Why: 0.5 is a default, not a business decision. Here a missed fraud is priced at 5 false declines.

```
$ python scripts/09_metrics_for_rare_events.py --change
(paste your RESULT lines)
```

## 5. Break it (0:32, 10 min, AI gives hints only; the run finishes by 0:40)

Break: choose the threshold that maximises test accuracy instead, then price it at 5:1 against the cheapest threshold. Seed 0 answers P3. Seeds 1 and 2 are two more 80/20 splits of the same data. P3 is logged above.

Why: accuracy is the number most dashboards show first, so its best threshold is the one a team picks by default.

```
$ for s in 0 1 2; do python scripts/09_metrics_for_rare_events.py --break --seed $s; done
(paste your RESULT lines)
```

Why, in three sentences, written without AI. Use all three seeds: is `break.extra_cost` bigger than its own seed-to-seed spread, and what does that let you claim?

## 6. Explain-back (0:42, 5 min) and rebuild (0:47, 10 min), no AI

- Five sentences for a smart engineer new to ML, written without AI. The AI names your weakest claim after the session (section 7).
- Rebuild: open `rebuild/09_average_precision.py`, write the bodies of `pr_curve()`, `average_precision()` and `cheapest_threshold()` from memory, then run `python rebuild/09_average_precision.py`. Its `check()` compares with scikit-learn (`average_precision_score`, `confusion_matrix_at_thresholds` and `confusion_matrix`) on 50,000 synthetic rows with tied scores, never with this lab's results.

## 7. What I learned

After the session (about 5 minutes): the AI names the weakest claim in your five sentences and asks one question that tests it. Edit the sentences here.

## 8. Interview soundbite (one of the three cards written at 0:57)

> (Your soundbite: one or two sentences only someone who ran this would say.)

Staff follow-up (cost): the 5:1 ratio is an estimate. How would you measure what a false decline really costs, without running a new experiment? Answer in 2 sentences from the repo link. Rotate: simplest design, failure modes, migration, what pages at 3 am, cost, trade-off.

## 9. Quiz cards (0:57, 3 min)

The AI drafts three cards (M, N, and T or D). Edit or replace them. Questions go to `../../quiz-bank.md`, keys to `../../answers/quiz-key.md`.

## Record

The script prints these as RESULT lines. Paste, do not type. Your run: the seed 0 value; the last row comes from the break loop.

| Metric | Your run | Hardware (the script's HW line) | Captured by (script or learner) |
|---|---|---|---|
| `baseline.never_fraud_accuracy`: accuracy when no payment is declined (fraction) | | | script |
| `P1.roc_auc`: ROC-AUC of the test scores (fraction) | | | script |
| `P1.pr_auc`: PR-AUC as average precision (fraction) | | | script |
| `P1.gap`: ROC-AUC minus PR-AUC (fraction) | | | script |
| `baseline.roc_auc_lo`: ROC-AUC, 2.5th percentile of 500 bootstrap resamples (fraction) | | | script |
| `baseline.roc_auc_hi`: ROC-AUC, 97.5th percentile of 500 bootstrap resamples (fraction) | | | script |
| `baseline.pr_auc_lo`: PR-AUC, 2.5th percentile of 500 bootstrap resamples (fraction) | | | script |
| `baseline.pr_auc_hi`: PR-AUC, 97.5th percentile of 500 bootstrap resamples (fraction) | | | script |
| `baseline.recall`: recall at threshold 0.5 (fraction) | | | script |
| `baseline.precision`: precision at threshold 0.5 (fraction) | | | script |
| `baseline.cost`: cost at threshold 0.5 (false declines) | | | script |
| `baseline.recall_at_95_precision`: the highest recall whose precision is at least 0.95 (fraction) | | | script |
| `change.threshold`: the cheapest threshold at 5:1 (probability) | | | script |
| `P2.recall`: recall at the cheapest threshold (fraction) | | | script |
| `change.precision`: precision at the cheapest threshold (fraction) | | | script |
| `change.cost`: cost at the cheapest threshold (false declines) | | | script |
| `break.threshold`: the max-accuracy threshold (probability) | | | script |
| `break.accuracy`: accuracy at the max-accuracy threshold (fraction) | | | script |
| `P3.recall`: recall at the max-accuracy threshold (fraction) | | | script |
| `break.precision`: precision at the max-accuracy threshold (fraction) | | | script |
| `break.cost`: cost of the max-accuracy threshold at 5:1 (false declines) | | | script |
| `break.extra_cost`: that cost minus the cheapest threshold's cost (false declines) | | | script |
| `P3.recall` and `break.extra_cost` at seeds 1 and 2, from the break loop | | | script |
