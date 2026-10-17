# 20. Training-serving skew replay: two code paths, one feature

> Goal: after this I can measure the mismatch rate between a batch feature and its serving twin over 200,000 queries, find what differs, and compare three train-serve combinations by MAE. (No result values anywhere in this file.)

**Level:** S (see `ml-learning/CLAUDE.md`). **Output style:** Explanatory
**Concept link:** [`../README.md#training-serving-skew`](../README.md#training-serving-skew) (read after the lab)
**Borrowed from:** Google's [Rules of Machine Learning](https://developers.google.com/machine-learning/guides/rules-of-ml), rules #29 and #37; Chip Huyen, *Designing Machine Learning Systems* (O'Reilly, 2022), chapter 7. Do it after the lab, as the second contact 1 to 3 days later.
**Dataset:** NYC TLC (Taxi and Limousine Commission) yellow taxi trips, January 2024, 2,964,624 trips, 49.96 MB parquet, the same file as lab 16: [trip file](https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-01.parquet) from the [TLC trip record page](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page), [nyc.gov terms of use](https://www.nyc.gov/main/terms-of-use). The script keeps the January pickups in zones 1 to 263 and samples 200,000 of them as queries.
**Runs on:** cpu. **Lane:** light. **Compute:** 4 runs x 3 min at most: `--baseline` 1 min, `--change` 1 min and again after your fix, and the reference `--break` the AI runs, 3 min (measured while other jobs shared the CPU). At most 6 min per run. Precomputed steps: none
**Needs:** base install only (pyarrow and lightgbm are in the base)
**Before the session** (from the module folder, see section 2): `--download` (the 50 MB trip file into `~/ml-data/tlc/`, shared with labs 16 and 26; a copy already there is reused), then `--smoke`. No human steps.
**Interview question:** Offline MAE is 12 and production behaves like 18: where do you look first, and how do you make skew impossible by construction?
**Repo link:** [`hld/payments-risk-decisioning/solution.md`, §4.3 Learn: features, labels, retraining, safe rollout](../../../hld/payments-risk-decisioning/solution.md#43-learn-features-labels-retraining-safe-rollout) (the "What breaks, compressed" ladder: naive, better, chosen); [`hld/driver-hot-clusters/deep-dives/hourly-institution-export.md`, §2 The hourly pipeline](../../../hld/driver-hot-clusters/deep-dives/hourly-institution-export.md#2-the-hourly-pipeline) (one library run in stream and batch mode, and a reconciliation metric between them)
**Captured by the script:** P1; P2 and its 20 side-by-side rows, as shipped and again after your fix; the reference `--break` lines, shown at the debrief. **Human steps:** none (you write `batch_counts()`, the prompt and the fix)
**Status:** todo

## 0. Retrieval (0:00, 5 min, closed book, no AI)

The AI asks up to three due cards from `../../quiz-bank.md`, one at a time. Do not open the bank first.

## 1. Predict (0:05, 7 min, no AI)

Level S: read `load_data()` and `report()` in `scripts/20_training_serving_skew.py`, and all of `scripts/serving_features.py`, for 3 minutes. `report()` is the RESULT contract your harness feeds. `serving_features.py` is the serving path as it ships; leave it as it is until section 5.

Write each row here before anything runs; the AI copies it into `../../prediction-log.md` word for word. A row that asks for several numbers becomes one log row per number, each with its own range.

| Step | Question | Kind | Prediction | 80% range or confidence |
|---|---|---|---|---|
| P1 | Test MAE of the model below at seed 0, with the last-hour count from your `batch_counts()` for training and test (batch train, batch serve) | num | | |
| P2 | The same trained model on the same test queries, but each test query's last-hour count comes from the shipped `serving_features.serving_counts()` (batch train, serving serve). MAE direction (up, down or same) and size, as the ratio P2 MAE / P1 MAE | dir | | |
| P3 | FIND-IT. Of the 200,000 queries (seed 0), the share whose last-hour count differs between your `batch_counts()` and the shipped `serving_counts()`, a fraction from 0 to 1 | num | | |

Terms, fixed so your numbers compare with the reference:

- **Stream.** Every January pickup in TLC zones 1 to 263, as zone and time, with time from `tpep_pickup_datetime`. `load_data()` returns it as `events`, sorted by time.
- **Query.** One of 200,000 pickups, sampled with the seed from those with a full hour of January before and after them. `load_data()` returns them as `queries`, sorted by time. A query's time is t.
- **Feature.** "Pickups in this zone in the last hour": the stream's pickups in the query's zone with a time in [t - 1 h, t).
- **Target.** The stream's pickups in the query's zone with a time in [t, t + 1 h): the same count, taken at t + 1 h.
- **Split.** Train on the queries before 24 January 23:00, so every training target ends before the test week. Test on the queries from 25 January 00:00 on.
- **Model.** `lightgbm.LGBMRegressor(n_estimators=300, random_state=seed, n_jobs=4, verbose=-1)`, otherwise default settings, on four inputs: the last-hour count, the hour of day (0 to 23), the weekday (0 to 6), and the zone as a pandas category with categories 1 to 263.
- **Metric.** MAE (mean absolute error) on the test queries, in pickups.

## 2. Setup (before the session)

```
$ source ~/.venvs/ml/bin/activate
$ cd m4-production-ml-payments    # from ml-learning/, where sessions start
$ python scripts/20_training_serving_skew.py --download
$ python scripts/20_training_serving_skew.py --smoke
```

`--smoke` checks the given plumbing only: `load_data()` on 3 zones, `serving_counts()`, and `report()` with placeholder values. `--baseline` and `--change` stop with NotImplementedError until the harness exists.

## 3. Baseline (0:12, 10 min)

Why: a model trained and tested on one batch feature function is the offline number a launch review sees first.

You write first, in this file, no AI (about 5 min). This is the prompt the AI builds from:

1. The split, the target and the metric, from the Terms in section 1.
2. The RESULT contract: `--baseline` calls `report("baseline", mae)`. `--change` calls `report("change", mae, versus=labkit.prior("P1.mae"), rows=rows)`, where `rows` holds 20 test queries sampled with the seed, sorted by time, with the columns zone, time, last_hour_batch and last_hour_serving.

Then write `batch_counts()` yourself, in `scripts/20_training_serving_skew.py`, from the Feature definition:

```
batch_counts(event_times, query_times)
    event_times   one zone's pickup times, a sorted numpy datetime64 array
    query_times   a numpy datetime64 array
    returns       an int array: for each t in query_times, how many event_times fall in [t - 1 h, t)
```

The AI then writes the rest: `batch_counts()` zone by zone for every query, the target as the same count at t + 1 h, the four inputs, the split, LightGBM and the two modes. Annotate each AI block with one line before the first run.

```
$ python scripts/20_training_serving_skew.py --baseline
(paste your RESULT lines)
```

Prediction vs actual, one sentence. The reference run is in `../../answers/`; the AI opens it only after your P1 row exists and you have pasted your own RESULT lines.

## 4. Change one thing (0:22, 10 min)

Change: the test queries' last-hour count comes from the shipped `serving_features.serving_counts(events, queries)` instead of `batch_counts()`. The trained model, the training rows and the test rows stay the same. P2 is logged above.

Why: in production the model never calls the batch function. It gets whatever the serving path computes at request time.

```
$ python scripts/20_training_serving_skew.py --change
(paste your RESULT lines)
```

## 5. Break it (0:32, 10 min, AI gives hints only; the run finishes by 0:40)

Something in the shipped code makes these numbers wrong. Find it before you run --break.

```
$ python scripts/20_training_serving_skew.py --change    # again, after your fix
$ python scripts/20_training_serving_skew.py --break       # one line: where the reveal lives
$ python ../answers/20_training_serving_skew_ref.py --break  # the AI runs this, after your fix or 'debrief 20'
(paste your RESULT lines)
```

Why, in three sentences, written without AI:

## 6. Explain-back (0:42, 5 min) and rebuild (0:47, 10 min), no AI

- Five sentences for a smart engineer new to ML, written without AI. The AI names your weakest claim after the session (section 7).
- Rebuild: the AI copies `rebuild/20_skew_parity.py` in from `answers/rebuild/stubs/` at 0:47. Write the three bodies from memory, then run `python rebuild/20_skew_parity.py`. Its `check()` compares both of your counts with a brute-force numpy count, never with this lab's results.

## 7. What I learned

After the session (about 5 minutes): the AI names the weakest claim in your five sentences and asks one question that tests it. Edit the sentences here.

## 8. Interview soundbite (one of the three cards written at 0:57)

> One or two sentences only someone who ran this would say.

Framing, one line in your words: decision | prediction time | label and its maturity | offline metric | online metric | guardrail.

Staff follow-up (migration): the live model was trained on batch values. How do you move it to training on the logged feature vector without a cliff, and what do you do for a brand-new feature that has no logged history yet? Answer in 2 sentences from the repo links: §4.3 of `solution.md` (the "Chosen" rung), and §2 of the export deep dive (one library in both modes, a reconciliation metric). Rotate: simplest design, failure modes, migration, what pages at 3 am, cost, trade-off.

## 9. Quiz cards (0:57, 3 min)

The AI drafts three cards (M, N, and T or D). Edit or replace them. Questions go to `../../quiz-bank.md`, keys to `../../answers/quiz-key.md`.

## Record

The script prints these as RESULT lines. Paste, do not type. Rows marked reference come from the reference `--break`: the AI runs it after your fix, or at 'debrief 20', and shows its lines at the debrief. Its RESULT lines are numbered in the order it prints them.

| Metric | Your run | Hardware (the script's HW line) | Captured by (script or learner) |
|---|---|---|---|
| `P1.mae` (batch train, batch serve) | | | script |
| `P2.mae` (batch train, serving serve), as shipped | | | script |
| `P2.mae_ratio` (P2 MAE / P1 MAE), as shipped | | | script |
| `P2.mae`, after your fix | | | script |
| `P2.mae_ratio`, after your fix | | | script |
| `P3.mismatch_rate`, reference `--break`, RESULT line 1 (your P3 answer) | | | script |
| Reference `--break`, RESULT line 2: unnamed here, like lines 3 to 11, because the names of these reveal lines would give the planted problem away | | | script |
| Reference `--break`, RESULT line 3, unnamed for the same reason | | | script |
| Reference `--break`, RESULT line 4, unnamed for the same reason | | | script |
| Reference `--break`, RESULT line 5, unnamed for the same reason | | | script |
| Reference `--break`, RESULT line 6, unnamed for the same reason | | | script |
| Reference `--break`, RESULT line 7, unnamed for the same reason | | | script |
| Reference `--break`, RESULT line 8, unnamed for the same reason | | | script |
| Reference `--break`, RESULT line 9, unnamed for the same reason | | | script |
| Reference `--break`, RESULT line 10, unnamed for the same reason | | | script |
| Reference `--break`, RESULT line 11, unnamed for the same reason | | | script |
| `break.mae_logged`, reference `--break`, RESULT line 12: the model trained and tested on the values the shipped serving path served (serving train, serving serve) | | | script |
| `break.mismatch_rate_your_fix`, reference `--break`, RESULT line 13: your fixed `serving_features.py` against the reference batch count, on every query | | | script |
| What you found: each difference between the two paths, where it is, and your fix | | | learner |
