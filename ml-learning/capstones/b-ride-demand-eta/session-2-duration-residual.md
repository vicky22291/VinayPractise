# B2. Trip duration at pickup: a residual over a zone-pair median, without the metered distance

> Goal: after this I can predict January 2024 taxi trip durations in seconds at pickup time, as a LightGBM residual over the median duration per zone pair and hour, measure its margin over that median with an interval, and show what the metered distance, known only at dropoff, would do to the number. (No result values anywhere in this file. Capstones have no reference run and no answers file: your run is the answer.)

**Capstone:** [B, ride-hailing demand and ETA](README.md), session 2 of 4, labkit id 46. **Level:** B (see `ml-learning/CLAUDE.md`). **Output style:** Explanatory
**Builds on:** lab 20 (one feature function for training and serving) and lab 07's question, "when is this value known?"
**Dataset:** NYC TLC yellow taxi trips, January 2024, 2,964,624 trips, 49.96 MB parquet ([Data](README.md#data)); nyc.gov terms of use
**Runs on:** cpu. **Lane:** light. **Compute:** no reference run; 2 measured runs, each capped at 6 min (if a fit would pass that, train on a seeded sample of training trips and say so). Precomputed steps: none
**Needs:** base install only
**Before the session:** `--download` (the January file into `~/ml-data/tlc/`, if labs 16 and 20 have not put it there), then `--smoke`.
**Interview question:** Predict trip duration at pickup: what is your baseline, and which tempting feature can you not use?
**Repo link:** none for ETA: no repo file covers ETA ([README](README.md#repo-hld-it-maps-to)). For the rule behind P3, the payments HLD's leakage list: [`model-lifecycle-shadow-and-labels.md`, §2 Leakage: the trap in the training data](../../../hld/payments-risk-decisioning/deep-dives/model-lifecycle-shadow-and-labels.md#2-leakage-the-trap-in-the-training-data), item 2 (post-decision events)
**Captured by the script:** P1 to P3 and every Record row. **Human steps:** the ETA framing line, the design and the write-up
**Status:** todo

## 0. Framing (0:00, 7 min, no AI)

Reread the demand framing line in `write-up.md`. Under it, write the ETA framing line: who sees the duration, at what moment it is predicted, when its label exists, and what guards it.

decision ___ | prediction time ___ | label and its maturity ___ | offline metric ___ | online metric ___ | guardrail ___

## 1. Predict (0:07, 5 min, no AI)

Write each row here and in `../../prediction-log.md` (Lab `B2`) before anything runs. Durations and MAE are in seconds.

| Step | Question | Kind | Prediction | 80% range or confidence |
|---|---|---|---|---|
| P1 | MAE on January 25 to 31 of the zone-pair median baseline: the median duration per pickup zone, dropoff zone and hour of day over January 1 to 24, with the fallbacks in Terms | num | | |
| P2 | LightGBM (300 trees, objective l1, learning rate 0.05, seed 0) on the residual, duration minus the baseline, from the 7 inputs in Terms; the prediction is baseline plus residual: MAE minus P1. Up, down or same, plus a size range | dir | | |
| P3 | The same model with each trip's metered `trip_distance` added as an eighth input: MAE on the same week | num | | |

Terms, fixed so sessions 3 and 4 reuse this model:

- **Trips.** Pickups in [2024-01-01, 2024-02-01). Duration = dropoff minus pickup, in seconds, kept from 60 s to 3 h (10,800 s). Zones 1 to 263 at both ends.
- **Train and test.** Train on pickups of January 1 to 24, test on January 25 to 31 (lab 16's test week).
- **Baseline.** The median duration per (pickup zone, dropoff zone, hour of day) when that cell has at least 5 training trips. Otherwise the pair's median over all hours (at least 5 trips), then the pickup zone's median, then the overall median. The share of test trips on each fallback is recorded.
- **The 7 inputs.** Hour of day, weekday, pickup zone, dropoff zone (both as `category`), the pair's median past distance, the baseline itself, and the pair's training trip count.
- **Median past distance.** The median `trip_distance` of the pair's training trips with a distance above 0, or the pickup zone's median when the pair is unseen. It comes from past trips only, so it exists at pickup.
- **Metered `trip_distance`.** This trip's own distance, final only when the meter stops at dropoff. Only P3's model uses it, and that model can never ship.
- **Interval.** Each MAE difference gets a 95% interval from 1,000 paired bootstrap resamples of test trips.
- **Saved for later (seed 0 only).** The baseline tables, the distance medians, the residual model (LightGBM's text dump) and the test-week predictions, to `~/ml-data/capstones/b/`. Sessions 3 and 4 read them.

## 2. Setup (before the session)

```
$ source ~/.venvs/ml/bin/activate
$ cd ml-learning/capstones/b-ride-demand-eta
$ python scripts/b2_duration_residual.py --download
$ python scripts/b2_duration_residual.py --smoke
```

`--download` prints paths and sizes only. The script exists once the AI writes it in section 3, or the day before from your design.

## 3. Baseline (0:12, 15 min)

Why: an ETA model must beat the lookup a dispatcher could write in one line, the usual duration for this pair at this hour.

You write first, in this file, no AI (about 5 min). This is the prompt the AI builds from:

1. The filters, the split, the baseline with its fallback order, and the one feature function that builds the 7 inputs for training and, in session 4, for serving.
2. The metric and its interval.
3. The RESULT contract: every name in the Record table, the mode that prints it, and its unit.

The AI then writes the script with `labkit.start(lab=46)`. Annotate each AI block with one line before the first run.

```
$ python scripts/b2_duration_residual.py --smoke
$ python scripts/b2_duration_residual.py --baseline
(paste your RESULT lines)
```

Prediction vs actual, one sentence. There is no reference run: the AI fills Actual and Hit from your pasted lines.

## 4. Change one thing (0:27, 15 min; the run finishes by 0:40)

Change: LightGBM learns the residual over the baseline from the 7 inputs. The same run then fits the eighth-input model for P3. P2 and P3 are logged above.

Why: the model only has to learn what the median misses, from inputs that exist when the rider presses the button.

```
$ python scripts/b2_duration_residual.py --change
(paste your RESULT lines)
```

Prediction vs actual, one sentence each for P2 and P3.

## 5. Write-up (0:42, 15 min, no AI)

- **Explain-back (5 min).** Five sentences for a smart engineer new to ML. Then ask the AI for the weakest claim, not a rewrite.
- **Deliverable (10 min).** Add the ETA framing line and §2 Duration to `write-up.md`: the baseline and model MAE with the interval, the fallback shares, and the metered-distance number labelled "cannot ship".

## 6. What I learned

The five explain-back sentences, edited after the AI's question.

## 7. Interview soundbite (the card written at 0:57)

> One or two sentences only someone who ran this would say.

Framing: decision ___ | prediction time ___ | label and its maturity ___ | offline metric ___ | online metric ___ | guardrail ___

Staff follow-up (simplest design): why is a zone-pair median the right first ETA, and what did you refuse to build (a road graph, live traffic)? No repo file covers ETA, so answer in 2 sentences from your own Record table.

## 8. Close (0:57, 3 min)

The AI drafts card `B2-D` (a symptom and the first check) from your run. Edit or replace it. The question goes to `../../quiz-bank.md`, the key to `../../answers/quiz-key.md`, citing your RESULT line. Set Status here and in the [README](README.md#sessions).

## Record

Suggested names: if your RESULT contract renames them, edit this table first. Paste, do not type.

| Metric | Your run | Hardware (the script's HW line) | Captured by (script or learner) |
|---|---|---|---|
| `baseline.n_train` and `baseline.n_test` (trips after the filters) | | | script |
| `P1.baseline_mae_s` (zone-pair median, January 25 to 31) | | | script |
| `baseline.fallback_pair_share`, `baseline.fallback_zone_share` and `baseline.fallback_global_share` (test trips on each fallback) | | | script |
| `change.model_mae_s` (baseline plus residual) | | | script |
| `P2.mae_change_s` (model minus baseline, seconds) | | | script |
| `change.mae_change_ci95_low` and `change.mae_change_ci95_high` | | | script |
| `P3.mae_metered_s` (with the metered distance; cannot ship) | | | script |
| `change.train_s` (LightGBM fit seconds, M4 Pro, cpu) | | | script |
