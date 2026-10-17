# 26. Drift: two-sample tests, PSI and a domain classifier

> Goal: after this I can flag drift between two months with KS (Kolmogorov-Smirnov) tests, PSI (population stability index) and a domain classifier, measure the false-alarm rate on a no-shift control, and tie a shift to a forecaster's MAE (mean absolute error). (No result values anywhere in this file.)

**Level:** S (see `ml-learning/CLAUDE.md`). **Output style:** Explanatory
**Concept link:** [`../README.md#drift-monitoring`](../README.md#drift-monitoring) (read after the lab)
**Borrowed from:** Rabanser, Günnemann and Lipton 2018, "Failing Loudly: An Empirical Study of Methods for Detecting Dataset Shift" ([arXiv 1810.11953](https://arxiv.org/abs/1810.11953)); Chip Huyen, *Designing Machine Learning Systems* (O'Reilly 2022), chapter 8, "Data Distribution Shifts and Monitoring". Do it after the lab, as the second contact 1 to 3 days later.
**Dataset:** NYC TLC (Taxi and Limousine Commission) yellow taxi trips, January 2024 (2,964,624 trips, 49,961,641 bytes of parquet) and July 2024 (3,076,903 trips, 52,299,432 bytes of parquet): 200,000 sampled trips per side in `--baseline` and `--change`, every trip of 1 to 14 January in `--break`. [January file](https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-01.parquet) and [July file](https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-07.parquet) from the [TLC trip record page](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page), [nyc.gov terms of use](https://www.nyc.gov/main/terms-of-use)
**Runs on:** cpu. **Lane:** light. **Compute:** 3 runs x 1 min, at most 6 min per run. Precomputed steps: none
**Needs:** base install only
**Before the session** (from the module folder, see section 2): `python scripts/26_drift_monitoring.py --download` (two files, 102 MB, into `~/ml-data/tlc/`; the January file is shared with labs 16 and 20), then `--smoke`. No human steps.
**Interview question:** How do you know the inputs have shifted since training, and which shift justifies a page, a retrain or nothing?
**Repo link:** [`hld/payments-risk-decisioning/deep-dives/model-lifecycle-shadow-and-labels.md`, §5 Proving a model before it declines anyone](../../../hld/payments-risk-decisioning/deep-dives/model-lifecycle-shadow-and-labels.md#5-proving-a-model-before-it-declines-anyone); [`hld/payments-risk-decisioning/solution.md`, §5.5 "Labels arrive 60 to 90 days later"](../../../hld/payments-risk-decisioning/solution.md#55-labels-arrive-60-to-90-days-later-how-do-you-train-and-how-do-you-know-a-new-model-is-better-before-it-declines-real-customers-loss-budget-the-model), its "Leading indicators" bullet (PSI of the top 30 features, daily, alert above 0.2); [`hld/credit-score-alerts/deep-dives/bad-batch-circuit-breaker.md`, §3 The rule](../../../hld/credit-score-alerts/deep-dives/bad-batch-circuit-breaker.md#3-the-rule)
**Captured by the script:** P1 to P3 and every Record row, plus one TABLE line per feature in each run (KS statistic, KS p-value, PSI). **Human steps:** none (you write the monitoring spec, the harness prompt and `psi()` in section 3)
**Status:** todo

## 0. Retrieval (0:00, 5 min, closed book, no AI)

The AI asks up to three due cards from `../../quiz-bank.md`, one at a time. Do not open the bank first.

## 1. Predict (0:05, 7 min, no AI)

Level S: read `scripts/26_drift_monitoring.py` for 2 minutes first. `load_data()` and `report()` (the RESULT contract your harness feeds) are given.

Write each row here before anything runs; the AI copies it into `../../prediction-log.md` word for word. A row that asks for several numbers becomes one log row per number, each with its own range.

| Step | Question | Kind | Prediction | 80% range or confidence |
|---|---|---|---|---|
| P1 | Domain classifier, seed 0: LightGBM with 100 trees on the ten features in Terms (datetime columns excluded), 200,000 January trips labelled 0 against 200,000 July trips labelled 1, out-of-fold probabilities from 5 stratified folds. Its AUC: the area under the ROC (receiver operating characteristic) curve, 0.5 when it cannot tell the samples apart and 1.0 when it always can | num | | |
| P2 | The same classifier, seed 0, on two random halves of January, 200,000 trips each: its AUC, and how many of the ten features have PSI above 0.2 (bins from the first half) | num | | |
| P3 | A two-sample KS test per feature (`scipy.stats.ks_2samp`) on every trip of January week 1 (1 to 7 January) against every trip of week 2 (8 to 14 January), no sampling: how many of the ten features are flagged at p below 0.05 | num | | |

Terms, fixed so your numbers compare with the reference:

- **Features (10).** `trip_distance`, `fare_amount`, `tip_amount`, `total_amount`, `passenger_count`, `payment_type`, `PULocationID`, `DOLocationID`, `duration_min` (dropoff minus pickup, in minutes) and `hour` (the pickup hour, 0 to 23). IDs and codes are compared as numbers.
- **Datetime columns.** The raw pickup and dropoff timestamps enter no test; only `hour` and `duration_min` are derived from them. A timestamp identifies the window it came from directly, so it stays outside the feature set.
- **Reference.** The first sample of each pair: January in P1, the first half in P2, week 1 in P3. PSI bins come from it.
- **KS test.** `ks_2samp` on one feature with its missing values dropped. Flagged at p below 0.05.
- **PSI.** Your `psi()` (formula in section 3), missing values dropped. Flagged above 0.2, the repo's alert line.
- **Domain classifier.** Reference rows get label 0 and the other sample's rows label 1. `LGBMClassifier(n_estimators=100, random_state=seed)`, `cross_val_predict` over `StratifiedKFold(5, shuffle=True, random_state=seed)`, then `roc_auc_score` on those out-of-fold probabilities. Missing values stay in: LightGBM handles them.
- **Samples.** `--baseline` draws 200,000 trips from each month and `--change` draws 400,000 January trips, all with `DataFrame.sample(random_state=seed)`; the change splits its draw into a first and a second 200,000. Only pickups inside the month count.
- **Weeks.** Monday to Sunday. January week 1 is 1 to 7 January, week 2 is 8 to 14, week 3 is 15 to 21 and week 4 is 22 to 28. July week 2 is 8 to 14 July.
- **Forecaster.** Lab 16's LightGBM forecaster with your fix from its debrief: zone-hour pickups for the 59 zones that average at least 100 pickups a day in January, one hour ahead, on lags of 1, 24 and 168 hours plus hour-of-week, `LGBMRegressor(n_estimators=500, objective="l1")`. It trains on January weeks 1 to 3 (the rows whose three lags exist) and scores January week 4 and July week 2, where July's lags come from July. Its MAE is in pickups per zone-hour.

## 2. Setup (before the session)

```
$ source ~/.venvs/ml/bin/activate
$ cd m4-production-ml-payments    # from ml-learning/, where sessions start
$ python scripts/26_drift_monitoring.py --download
$ python scripts/26_drift_monitoring.py --smoke
```

`--smoke` checks the given plumbing only: both months load, and `report()` prints every RESULT name from placeholder values. `--baseline`, `--change` and `--break` stop with NotImplementedError until the harness exists. The datetime columns stay out of the domain classifier on purpose (see Terms).

## 3. Baseline (0:12, 10 min)

Why: each detector answers a different question: KS asks whether two distributions differ at all, PSI asks how far the binned shares moved, and a domain classifier asks whether any mix of features tells the two windows apart.

You write first, in this file, no AI (about 5 min). This is the prompt the AI builds from:

1. The monitoring spec: the features you monitor, the reference window, and your alert threshold for each detector (KS, PSI and the domain classifier's AUC), with what each alert triggers: a page, a retrain ticket or nothing. The RESULT contract still counts KS flags at p below 0.05 and PSI flags above 0.2, so your thresholds sit beside the reference's.
2. The comparisons: the two samples each mode compares, which one is the reference, and how many trips each side gets (Terms).
3. The RESULT contract: the `report()` call each mode makes and its values: `domain_auc` in every mode, plus `mae_jan_w4`, `mae_jul_w2` and `pred_psi` from the forecaster in `--baseline`, and `n_week1` and `n_week2` in `--break`. `pred_psi` is your `psi()` of the July week 2 predictions against the January week 4 predictions.

Then write `psi(expected, actual, bins=10)` yourself, in `scripts/26_drift_monitoring.py`, from this formula:

```
edges  = np.quantile(expected, [0.1, 0.2, ..., 0.9]), duplicate edges dropped
bins   = the outer bins run to -inf and +inf; a value equal to an edge goes to the bin above it
e_i    = the share of expected in bin i, a_i = the share of actual in bin i, each floored at 0.0001
PSI    = sum over the bins of (a_i - e_i) * ln(a_i / e_i)
```

A feature with many ties (`passenger_count`, `payment_type`) keeps fewer than 10 bins once duplicate edges drop. Your `psi()` should allow for that.

The AI then writes the KS and PSI loop over the features, the domain classifier, the forecaster and the three modes from your prompt, with `--smoke` running all three on small samples. Annotate each AI block with one line before the first run.

```
$ python scripts/26_drift_monitoring.py --baseline
(paste your RESULT lines)
```

Prediction vs actual, one sentence. The reference run is in `../../answers/`; the AI opens it only after your P1 row exists and you have pasted your own RESULT lines.

## 4. Change one thing (0:22, 10 min)

Change: compare two random halves of January (200,000 trips each, no trip in both) instead of January and July. Everything else stays fixed. P2 is logged above.

Why: a no-shift control measures each detector's false-alarm rate, which is what an alert threshold has to be set against.

```
$ python scripts/26_drift_monitoring.py --change
(paste your RESULT lines)
```

## 5. Break it (0:32, 10 min, AI gives hints only; the run finishes by 0:40)

Break: run the KS test on every feature with every trip of January week 1 against every trip of week 2, no sampling. P3 is logged above. `--break` also prints PSI and the domain classifier for the same two weeks.

Why: a dashboard has every row of a window for free, so whole-window tests are how drift checks often run in production.

```
$ python scripts/26_drift_monitoring.py --break
(paste your RESULT lines)
```

Why, in three sentences, written without AI:

## 6. Explain-back (0:42, 5 min) and rebuild (0:47, 10 min), no AI

- Five sentences for a smart engineer new to ML, written without AI. The AI names your weakest claim after the session (section 7).
- Rebuild: open `rebuild/26_drift_tests.py`, write `ks_statistic()`, `domain_classifier_auc()` and `psi()` from memory, then run `python rebuild/26_drift_tests.py`. Its `check()` compares with `scipy.stats.ks_2samp`, with a PSI computed by hand through `numpy.histogram`, and with the known best AUC for a one-standard-deviation shift in a normal feature (`scipy.stats.norm`), never with this lab's results.

## 7. What I learned

After the session (about 5 minutes): the AI names the weakest claim in your five sentences and asks one question that tests it. Edit the sentences here.

## 8. Interview soundbite (one of the three cards written at 0:57)

> One or two sentences only someone who ran this would say.

Framing: decision ___ | prediction time ___ | label and its maturity ___ | offline metric ___ | online metric ___ | guardrail ___

Staff follow-up (what pages at 3 am): the payments model's top 30 features get a drift check every day. Which signal pages on-call, which only opens a retrain ticket, and what must the model's own error show before either? Answer in 2 sentences from the repo links (solution §5.5, then the circuit breaker's §3). Rotate: simplest design, failure modes, migration, what pages at 3 am, cost, trade-off.

## 9. Quiz cards (0:57, 3 min)

The AI drafts three cards (M, N, and T or D). Edit or replace them. Questions go to `../../quiz-bank.md`, keys to `../../answers/quiz-key.md`.

## Record

The script prints these as RESULT lines. Paste, do not type. Each run also prints ten TABLE lines (one per feature: KS statistic, KS p-value, PSI); paste them under their step.

| Metric | Your run | Hardware (the script's HW line) | Captured by (script or learner) |
|---|---|---|---|
| `P1.domain_auc` (January against July, out-of-fold AUC) | | | script |
| `baseline.ks_flagged` (January against July, features with KS p below 0.05, of 10) | | | script |
| `baseline.psi_flagged` (January against July, features with PSI above 0.2, of 10) | | | script |
| `baseline.max_ks_stat` (January against July, the largest KS statistic of the 10 features) | | | script |
| `baseline.max_psi` (January against July, the largest PSI of the 10 features) | | | script |
| `baseline.mae_jan_w4` (forecaster MAE on January week 4, pickups per zone-hour) | | | script |
| `baseline.mae_jul_w2` (forecaster MAE on July week 2, pickups per zone-hour) | | | script |
| `baseline.pred_psi` (PSI of the forecaster's July week 2 predictions against its January week 4 predictions) | | | script |
| `P2.domain_auc` (two random halves of January, out-of-fold AUC) | | | script |
| `P2.psi_flagged` (halves, features with PSI above 0.2, of 10) | | | script |
| `change.ks_flagged` (halves, features with KS p below 0.05, of 10) | | | script |
| `change.max_ks_stat` (halves, the largest KS statistic) | | | script |
| `change.max_psi` (halves, the largest PSI) | | | script |
| `P3.ks_flagged` (every trip of week 1 against week 2, features with KS p below 0.05, of 10) | | | script |
| `break.psi_flagged` (week 1 against week 2, features with PSI above 0.2, of 10) | | | script |
| `break.domain_auc` (week 1 against week 2, out-of-fold AUC) | | | script |
| `break.max_ks_stat` (week 1 against week 2, the largest KS statistic) | | | script |
| `break.max_psi` (week 1 against week 2, the largest PSI) | | | script |
| `break.n_week1` (trips in January week 1) | | | script |
| `break.n_week2` (trips in January week 2) | | | script |
