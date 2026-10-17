# 16. Forecast demand: seasonal naive first, then lag features

> Goal: after this I can forecast zone-hour taxi pickups for 59 zones with a seasonal-naive baseline and LightGBM, and prove that every lag points at the past. (No result values anywhere in this file.)

**Level:** C (see `ml-learning/CLAUDE.md`). **Output style:** Learning
**Concept link:** [`../README.md#forecasting-baselines-and-lag-features`](../README.md#forecasting-baselines-and-lag-features) (read after the lab)
**Borrowed from:** Kaggle Learn [Time Series](https://www.kaggle.com/learn/time-series): [Trend](https://www.kaggle.com/code/ryanholbrook/trend), [Seasonality](https://www.kaggle.com/code/ryanholbrook/seasonality) and [Time Series as Features](https://www.kaggle.com/code/ryanholbrook/time-series-as-features). Do it after the lab, as the second contact 1 to 3 days later.
**Dataset:** NYC (New York City) TLC (Taxi and Limousine Commission) yellow taxi trips, January 2024, 2,964,624 trips, 49.96 MB parquet, aggregated to zone-hour pickups for the 59 zones averaging at least 100 pickups a day, [trip file](https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-01.parquet) and [zone lookup](https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv) from the [TLC trip record page](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page), [nyc.gov terms of use](https://www.nyc.gov/main/terms-of-use)
**Runs on:** cpu. **Lane:** light. **Compute:** 3 runs x 1 min (plus `--baseline` and `--change` again after your fix), at most 6 min per run. Precomputed steps: none
**Needs:** base install only (pyarrow and lightgbm are in the base)
**Before the session** (from the module folder, see section 2): `--download` (50 MB into `~/ml-data/tlc/`, shared with labs 20 and 26 and Capstone B), then `--smoke`. No human steps before the session.
**Interview question:** Forecast pickups per zone per hour for driver positioning: what baseline must a model beat, and how does a lag feature read the future?
**Repo link:** [`hld/driver-hot-clusters/solution.md`](../../../hld/driver-hot-clusters/solution.md#44-institutions-hourly-final-private-files), section 4.4 "Institutions: hourly, final, private files". No repo file covers forecasting; this is where an hourly count becomes final.
**Captured by the script:** baseline and change, as shipped and again after your fix; the reference `--break` lines, shown at the debrief. **Human steps:** what you found and the hints you used (the Record table's learner row)
**Status:** todo

## 0. Retrieval (0:00, 5 min, closed book, no AI)

The AI asks up to three due cards from `../../quiz-bank.md`, one at a time. Do not open the bank first.

## 1. Predict (0:05, 7 min, no AI)

Read `scripts/16_forecast_demand.py` for 4 minutes first. Your TODO(human) is the body of `seasonal_naive_mae()`; you write it at 0:12.

Write each row here before anything runs; the AI copies it into `../../prediction-log.md` word for word. A row that asks for several numbers becomes one log row per number, each with its own range.

| Step | Question | Kind | Prediction | 80% range or confidence |
|---|---|---|---|---|
| P1 | MAE (mean absolute error, pickups per zone-hour) of seasonal naive (the forecast is the same zone at the same hour one week earlier, `lag_168`) on the last 7 days of January (25 to 31 January), 59 zones, as shipped | num | | |
| P2 | LightGBM (500 trees, objective l1, seed 0) with lags 1, 24 and 168 plus hour-of-week, one hour ahead, as shipped: direction and size of `P2.improvement_pct` = 100 x (seasonal-naive MAE minus LightGBM MAE) / seasonal-naive MAE, on the same test week. Up means LightGBM's MAE is lower (up, down or same, plus a size range in %) | dir | | |
| P3 | FIND-IT. Is the shipped LightGBM MAE honest? Your honest MAE for the same model and the same test week, with an 80% range | num | | |

## 2. Setup (before the session)

```
$ source ~/.venvs/ml/bin/activate
$ cd m3-more-of-the-map    # from ml-learning/, where sessions start
$ python scripts/16_forecast_demand.py --download
$ python scripts/16_forecast_demand.py --smoke
```

## 3. Baseline (0:12, 10 min)

Why: "same hour last week" is the bar any forecast has to clear, and it costs one line.

Write the TODO first: the body of `seasonal_naive_mae()` in `scripts/16_forecast_demand.py`. Run `--check` until it prints `check: PASS`, then run the baseline.

```
$ python scripts/16_forecast_demand.py --check
$ python scripts/16_forecast_demand.py --baseline
(paste your RESULT lines)
```

Prediction vs actual, one sentence. The reference run is in `../../answers/`; the AI opens it only after your P1 row exists and you have pasted your own RESULT lines.

## 4. Change one thing (0:22, 10 min)

Why: a model earns its place only by its margin over the baseline, on the same test week.

Change: LightGBM (500 trees, objective l1) with lag features at 1, 24 and 168 hours and hour-of-week, one hour ahead. P2 is logged above.

```
$ python scripts/16_forecast_demand.py --change
(paste your RESULT lines)
```

## 5. Break it (0:32, 10 min, AI gives hints only; the run finishes by 0:40)

Something in the shipped code makes these numbers wrong. Find it before you run --break.

```
$ python scripts/16_forecast_demand.py --baseline    # again, after your fix
$ python scripts/16_forecast_demand.py --change      # again, after your fix
$ python scripts/16_forecast_demand.py --break       # one line: where the reveal lives
$ python ../answers/16_forecast_demand_ref.py --break  # the AI runs this, after your fix or 'debrief 16'
(paste your RESULT lines)
```

Why, in three sentences, written without AI:

## 6. Explain-back (0:42, 5 min) and rebuild (0:47, 10 min), no AI

- Five sentences for a smart engineer new to ML, written without AI. The AI names your weakest claim after the session (section 7).
- Rebuild: the AI copies `rebuild/16_lag_features.py` in from `answers/rebuild/stubs/` at 0:47. Write the four bodies from memory, then run `python rebuild/16_lag_features.py`. Its `check()` compares with scikit-learn's `mean_absolute_error` and with pandas, never with this lab's results.

## 7. What I learned

After the session (about 5 minutes): the AI names the weakest claim in your five sentences and asks one question that tests it. Edit the sentences here.

## 8. Interview soundbite (one of the three cards written at 0:57)

> One or two sentences only someone who ran this would say.

Staff follow-up (trade-off): at 14:00 the forecast for 14:00 to 15:00 wants lag 1, the 13:00 to 14:00 count, but section 4.4 makes an hour final only after a 15-minute late-data cutoff. Which count does serving read, and what do you train on so the model sees the same thing? Answer in 2 sentences from the repo link (section 4.4, and section 5.3 for how far provisional and final differ).

## 9. Quiz cards (0:57, 3 min)

The AI drafts three cards (M, N, and T or D). Edit or replace them. Questions go to `../../quiz-bank.md`, keys to `../../answers/quiz-key.md`.

## Record

The script prints these as RESULT lines. Paste, do not type.

| Metric | Your run | Hardware (the script's HW line) | Captured by (script or learner) |
|---|---|---|---|
| `P1.seasonal_naive_mae`, as shipped | | | script |
| `change.lightgbm_mae`, as shipped | | | script |
| `P2.improvement_pct`, as shipped | | | script |
| `P1.seasonal_naive_mae`, your fixed copy | | | script |
| `change.lightgbm_mae`, your fixed copy: your own check of your fix; P3 is graded on `P3.honest_lightgbm_mae` | | | script |
| `P2.improvement_pct`, your fixed copy | | | script |
| `P3.honest_lightgbm_mae`: from the reference `--break`, shown at the debrief | | | script |
| `break.honest_seasonal_naive_mae`: from the reference `--break`, shown at the debrief | | | script |
| `break.honest_improvement_pct`: from the reference `--break`, shown at the debrief | | | script |
| `break.leaky_lightgbm_mae`: the honest model with one extra feature, from the reference `--break`, shown at the debrief | | | script |
| Three more lines from the reference `--break` about the planted problem, unnamed here because their names would give it away; shown at the debrief | | | script |
| What you found, and the hints you used | | | learner |
