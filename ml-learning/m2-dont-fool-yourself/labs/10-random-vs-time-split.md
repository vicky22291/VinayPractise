# 10. Random vs time split: test on the future, not a shuffle

> Goal: after this I can build an honest time split for hourly data (test on the last 30 days) and find a silent leak in code I did not write. (No result values anywhere in this file.)

**Level:** C (see `ml-learning/CLAUDE.md`). **Output style:** Learning
**Concept link:** [`../README.md#random-vs-time-splits`](../README.md#random-vs-time-splits) (read after the lab)
**Borrowed from:** [Rules of ML](https://developers.google.com/machine-learning/guides/rules-of-ml) rule #33, and Kaggle Learn [Time Series](https://www.kaggle.com/learn/time-series) lesson 1, "Linear Regression With Time Series". Do it after the lab, as the second contact 1 to 3 days later.
**Dataset:** Bike Sharing hourly file, UCI (University of California, Irvine) dataset 275: `hour.csv`, 17,379 rows (the UCI metadata says 17,389) and 17 columns, target `cnt`; 0.28 MB zip (279,992 B), 1.16 MB csv; https://archive.ics.uci.edu/static/public/275/bike+sharing+dataset.zip; CC BY 4.0 (Creative Commons Attribution 4.0)
**Runs on:** cpu. **Lane:** light. **Compute:** 3 runs x 1 min (baseline, change, break), at most 6 min per run. Precomputed steps: none
**Needs:** base install only
**Before the session** (from the module folder, see section 2): `python scripts/10_random_vs_time_split.py --download`, then `--smoke` (section 2).
**Interview question:** Offline RMSE (root mean squared error) looks good and production behaves much worse: how did you split, and what does a time split show?
**Repo link:** [`hld/payments-risk-decisioning/deep-dives/model-lifecycle-shadow-and-labels.md`](../../../hld/payments-risk-decisioning/deep-dives/model-lifecycle-shadow-and-labels.md#2-leakage-the-trap-in-the-training-data), §2 "Leakage: the trap in the training data", item 5 "Random splits"
**Captured by the script:** P1 (`--baseline`), P2 (`--change`), P3 and the honest time split (the reference `--break`, which the AI runs after your fix). **Human steps:** the TODO in `time_split()`; the fix in your copy and its two reruns (`--baseline`, then `--change`); what you found plus the hints you used.
**Status:** todo

## 0. Retrieval (0:00, 5 min, closed book, no AI)

The AI asks up to three due cards from `../../quiz-bank.md`, one at a time. Do not open the bank first.

## 1. Predict (0:05, 7 min, no AI)

Write each row here before anything runs; the AI copies it into `../../prediction-log.md` word for word. A row that asks for several numbers becomes one log row per number, each with its own range.

| Step | Question | Kind | Prediction | 80% range or confidence |
|---|---|---|---|---|
| P1 | Test RMSE in bikes per hour of LightGBM (300 trees, other settings default) with a random 80/20 split of the 17,379 hours, as shipped, seed 0 | num | | |
| P2 | Same model, inputs and seed, but test on the last 30 days (2012-12-02 00:00 to 2012-12-31 23:00) and train on every earlier hour: RMSE up, down or same versus P1, and the size as P2 minus P1 in bikes per hour | dir | | |
| P3 | FIND-IT. Is the baseline RMSE honest? Your honest random-split RMSE in bikes per hour (same model, split and seed 0), with an 80% range | num | | |

## 2. Setup (before the session)

```
$ source ~/.venvs/ml/bin/activate
$ cd m2-dont-fool-yourself    # from ml-learning/, where sessions start
$ python scripts/10_random_vs_time_split.py --download
$ python scripts/10_random_vs_time_split.py --smoke
```

## 3. Baseline (0:12, 10 min)

First, the TODO: write the body of `time_split()` in `scripts/10_random_vs_time_split.py`. It is the last-30-days split that `--change` uses. The AI may give hints, or a draft explained line by line that you type. Run `--check` until it prints `check: PASS`, then run the baseline.

Why: a shuffled 80/20 split is the default in most tutorials, so this is the number most notebooks would report.

```
$ python scripts/10_random_vs_time_split.py --check
$ python scripts/10_random_vs_time_split.py --baseline
(paste your RESULT lines)
```

Prediction vs actual, one sentence. The reference run is in `../../answers/`; the AI opens it only after your P1 row exists and you have pasted your own RESULT lines.

## 4. Change one thing (0:22, 10 min)

Change: test on the last 30 days instead of a random 20%, with your `time_split()`. P2 is logged above.

Why: in production the model scores hours that come after every hour it trained on, so the test set should too.

```
$ python scripts/10_random_vs_time_split.py --change
(paste your RESULT lines)
```

## 5. Break it (0:32, 10 min, AI gives hints only; the run finishes by 0:40)

Something in the shipped code makes these numbers wrong. Find it before you run --break. P3 is logged above.

After your fix, rerun both splits from your copy:

```
$ python scripts/10_random_vs_time_split.py --baseline   # after your fix
$ python scripts/10_random_vs_time_split.py --change     # after your fix and --baseline
(paste your RESULT lines)
```

`--break` runs from the reference, not from your copy. Your copy's `--break` prints one line that sends you to the AI, and no RESULT lines. After your fix, or after 'debrief 10', the AI runs the reference from this folder. Paste its RESULT lines here:

```
$ python ../answers/10_random_vs_time_split_ref.py --break   # the AI runs this, after your fix
(paste your RESULT lines)
```

Why, in three sentences, written without AI:

## 6. Explain-back (0:42, 5 min) and rebuild (0:47, 10 min), no AI

- Five sentences for a smart engineer new to ML, written without AI. The AI names your weakest claim after the session (section 7).
- Rebuild: open `rebuild/10_rolling_origin_splits.py`, write the bodies of `rolling_origin_splits()` and `random_vs_time_rmse()` from memory, then run `python rebuild/10_rolling_origin_splits.py`. Its `check()` compares your folds with scikit-learn's `TimeSeriesSplit(n_splits=4, test_size=720, gap=24)` on 17,379 hourly timestamps, and your two RMSEs with scikit-learn's `train_test_split` and `root_mean_squared_error`, never with this lab's results.

## 7. What I learned

After the session (about 5 minutes): the AI names the weakest claim in your five sentences and asks one question that tests it. Edit the sentences here.

## 8. Interview soundbite (one of the three cards written at 0:57)

> (your one or two sentences: something only someone who ran this would say)

Staff follow-up (failure modes): your payments model's split is now out-of-time, so it is clean on time. Name one way the same entity still ends up on both sides of a split, and how you split to stop it. Answer in 2 sentences from the repo link, §2 item 5. Rotate: simplest design, failure modes, migration, what pages at 3 am, cost, trade-off.

## 9. Quiz cards (0:57, 3 min)

The AI drafts three cards (M, N, and T or D). Edit or replace them. Questions go to `../../quiz-bank.md`, keys to `../../answers/quiz-key.md`.

## Record

The script prints these as RESULT lines. Paste, do not type.

| Metric | Your run | Hardware (the script's HW line) | Captured by (script or learner) |
|---|---|---|---|
| `P1.rmse_random`: random 80/20 split, as shipped | | | script |
| `P2.rmse_time`: last 30 days, as shipped | | | script |
| `P2.rmse_time_minus_random`: P2 minus your P1, same seed | | | script |
| `P1.rmse_random`, `P2.rmse_time` and `P2.rmse_time_minus_random` again, from your fixed copy (rerun `--baseline` first, then `--change`). Not the P1 or P2 Actuals | | | script |
| `P3.rmse_random_honest`: random split, from the reference `--break` | | | script |
| `break.rmse_time_honest`: last 30 days, from the reference `--break` | | | script |
| What you found, and the hints you used | | | learner |
