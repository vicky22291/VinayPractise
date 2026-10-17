# B1. Zone-hour demand: seasonal naive, then LightGBM 1 hour and 3 hours ahead

> Goal: after this I can forecast July 2024 taxi pickups per zone-hour for the busy zones with a seasonal-naive baseline and LightGBM, 1 hour and 3 hours ahead, with every lag proven to point at the past. (No result values anywhere in this file. Capstones have no reference run and no answers file: your run is the answer.)

**Capstone:** [B, ride-hailing demand and ETA](README.md), session 1 of 4, labkit id 45. **Level:** B (see `ml-learning/CLAUDE.md`). **Output style:** Explanatory
**Builds on:** lab 16 (seasonal naive first, lags checked against direct lookups), on a month that lab never saw
**Dataset:** NYC TLC yellow taxi trips, July 2024, 52.30 MB parquet ([Data](README.md#data)), aggregated to pickups per zone-hour for the zones averaging at least 100 pickups a day on July 1 to 24; nyc.gov terms of use
**Runs on:** cpu. **Lane:** light. **Compute:** no reference run; 2 measured runs, each capped at 6 min. Precomputed steps: none
**Needs:** base install only
**Before the session:** `--download` (the July file and the zone lookup into `~/ml-data/tlc/`, if lab 26 has not put them there), then `--smoke`.
**Interview question:** Forecast pickups per zone 3 hours ahead for driver positioning: what must the model beat, and what does the longer horizon cost?
**Repo link:** [`hld/driver-hot-clusters/solution.md`, 4.2 Count: distinct drivers per cell over the last 20 minutes](../../../hld/driver-hot-clusters/solution.md#42-count-distinct-drivers-per-cell-over-the-last-20-minutes) (the supply side of the same positioning decision); [5.3 "Institutions and ops see different numbers. Which is right?"](../../../hld/driver-hot-clusters/solution.md#53-institutions-and-ops-see-different-numbers-which-is-right) (provisional vs final counts)
**Captured by the script:** P1 to P3 and every Record row. **Human steps:** the framing sprint, the design and the write-up
**Status:** todo

## 0. Framing (0:00, 7 min, no AI except as the interviewer)

**0:00 to 0:05, the framing sprint.** Tell the AI "play the interviewer for a pickup-demand forecast". Propose and confirm, by the rule in [`scoping-drills/README.md`](../../../scoping-drills/README.md#3-drill-2-propose-and-confirm) §3: state each assumption, attach its consequence, invite correction, and ask at most one open question. Cover who acts on the forecast (dispatch positioning idle drivers, or pricing), how far ahead they need it, what must never happen, and the failure default when the forecast is missing. The AI confirms or corrects in one line each, and never proposes a metric or a split.

**0:05 to 0:07, the demand framing line.** It opens `write-up.md` at 0:42. B2 adds a second line for the ETA half.

decision ___ | prediction time ___ | label and its maturity ___ | offline metric ___ | online metric ___ | guardrail ___

## 1. Predict (0:07, 5 min, no AI)

Write each row here and in `../../prediction-log.md` (Lab `B1`) before anything runs.

| Step | Question | Kind | Prediction | 80% range or confidence |
|---|---|---|---|---|
| P1 | MAE (mean absolute error, pickups per zone-hour) of seasonal naive, the same zone and hour 168 hours earlier, on July 25 to 31 over the busy zones in Terms | num | | |
| P2 | LightGBM (500 trees, objective l1, seed 0) with lags 1, 24 and 168, hour-of-week and zone, 1 hour ahead, trained on July 8 to 24: MAE improvement in % over seasonal naive on the same test week. Up, down or same, plus a size range | dir | | |
| P3 | The same LightGBM 3 hours ahead, with lags 3, 24 and 168 (no lag shorter than the horizon): its MAE minus the 1-hour model's MAE, in % of the 1-hour MAE. Up, down or same, plus a size range | dir | | |

Terms, fixed so the two horizons compare:

- **Month.** Pickups with `tpep_pickup_datetime` in [2024-07-01, 2024-08-01). Zones 264 and 265 dropped.
- **Busy zones.** Zones with a mean of at least 100 pickups a day over July 1 to 24. Training days only, so the test week never chooses the zones.
- **The zone-hour table and its lags.** Built exactly as your lab 16 fix builds them. Lab 16's check runs first: 200 random lags equal a direct lookup of the same zone k hours earlier.
- **Horizon.** 1 hour ahead: the forecast for the hour starting at H may use counts up to the hour before H, so lag 1. 3 hours ahead: the newest usable count is 3 hours before H, so lag 3.
- **Train and test.** Train on July 8 to 24: earlier rows have no lag 168 inside July, so they drop. Test on every busy zone-hour of July 25 to 31.
- **Improvement %.** (seasonal-naive MAE minus model MAE) / seasonal-naive MAE x 100. WAPE (weighted absolute percentage error), the sum of absolute errors over the sum of actual pickups, is recorded beside each MAE.
- **Interval.** Each MAE difference gets a 95% interval from 1,000 paired bootstrap resamples of test zone-days.

## 2. Setup (before the session)

```
$ source ~/.venvs/ml/bin/activate
$ cd ml-learning/capstones/b-ride-demand-eta
$ python scripts/b1_zone_hour_demand.py --download
$ python scripts/b1_zone_hour_demand.py --smoke
```

There is no script until the AI writes one. For the setup it needs only `--download` and `--smoke`: the July file and the zone lookup with their sizes from the README, and a smoke run on two zones and two weeks. `--download` prints paths and sizes only.

## 3. Baseline (0:12, 15 min)

Why: "same hour last week" is the bar, and on a new month it has to be cleared again.

You write first, in this file, no AI (about 5 min). This is the prompt the AI builds from:

1. The zone-hour table, the lag rule from your lab 16 fix, the check, and the horizon rule.
2. The split, the busy-zone rule, and the metric with its interval.
3. The RESULT contract: every name in the Record table, the mode that prints it, and its unit.

The AI then writes `--baseline` and `--change` with `labkit.start(lab=45)`. Annotate each AI block with one line before the first run.

```
$ python scripts/b1_zone_hour_demand.py --smoke
$ python scripts/b1_zone_hour_demand.py --baseline
(paste your RESULT lines)
```

Prediction vs actual, one sentence each for P1 and P2. There is no reference run: the AI fills Actual and Hit from your pasted lines.

## 4. Change one thing (0:27, 15 min; the run finishes by 0:40)

Change: forecast 3 hours ahead. Lags 3, 24 and 168 replace lags 1, 24 and 168; the trees, the split and the zones stay fixed. P3 is logged above.

Why: a driver needs time to reposition, so the forecast that matters is made 3 hours before the hour it covers.

```
$ python scripts/b1_zone_hour_demand.py --change
(paste your RESULT lines)
```

Prediction vs actual, one sentence.

## 5. Write-up (0:42, 15 min, no AI)

- **Explain-back (5 min).** Five sentences for a smart engineer new to ML. Then ask the AI for the weakest claim, not a rewrite.
- **Deliverable (10 min).** Start `write-up.md` in this folder: the demand framing line, then §1 Demand: both MAEs at both horizons, with intervals, and one line on what the horizon cost.

## 6. What I learned

The five explain-back sentences, edited after the AI's question.

## 7. Interview soundbite (the card written at 0:57)

> One or two sentences only someone who ran this would say.

Framing: decision ___ | prediction time ___ | label and its maturity ___ | offline metric ___ | online metric ___ | guardrail ___

Staff follow-up (what pages at 3 am): which number about this forecast pages someone at 3 am, and at what threshold? Answer in 2 sentences: start from the reconciliation metric that pages in the repo link's §5.3, then name the forecast's own signal and its threshold.

## 8. Close (0:57, 3 min)

The AI drafts card `B1-T` (the payments version or a variant you did not run) from your run. Edit or replace it. The question goes to `../../quiz-bank.md`, the key to `../../answers/quiz-key.md`, citing your RESULT line. Set Status here and in the [README](README.md#sessions).

## Record

Suggested names: if your RESULT contract renames them, edit this table first. Paste, do not type.

| Metric | Your run | Hardware (the script's HW line) | Captured by (script or learner) |
|---|---|---|---|
| `baseline.zones` (busy zones) | | | script |
| `baseline.lag_check` (lags of the 200 that match a direct lookup) | | | script |
| `P1.naive_mae` (pickups per zone-hour, July 25 to 31) | | | script |
| `baseline.naive_wape` | | | script |
| `baseline.lgbm_mae_1h` and `baseline.lgbm_wape_1h` | | | script |
| `P2.improvement_pct_1h` (over seasonal naive) | | | script |
| `baseline.improvement_ci95_low` and `baseline.improvement_ci95_high` | | | script |
| `change.lgbm_mae_3h` and `change.lgbm_wape_3h` | | | script |
| `P3.mae_change_pct_3h` (3-hour minus 1-hour MAE, % of the 1-hour MAE) | | | script |
| `change.improvement_pct_3h` (over seasonal naive) | | | script |
| `change.train_s` (LightGBM fit seconds, M4 Pro, cpu) | | | script |
