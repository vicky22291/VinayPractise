# B3. Drift, January vs July: PSI per feature and the duration MAE shift

> Goal: after this I can compute PSI (population stability index) for each of the B2 model's 7 inputs between January and July 2024, measure how far its MAE moves on a July week, and measure what rebuilding it on July buys back. (No result values anywhere in this file. Capstones have no reference run and no answers file: your run is the answer.)

**Capstone:** [B, ride-hailing demand and ETA](README.md), session 3 of 4, labkit id 47. **Level:** B (see `ml-learning/CLAUDE.md`). **Output style:** Explanatory
**Builds on:** lab 26 (PSI between these two months), plus your B2 model
**Dataset:** NYC TLC yellow taxi trips, January 2024 (49.96 MB) and July 2024 (52.30 MB) ([Data](README.md#data)), with B2's filters; nyc.gov terms of use
**Runs on:** cpu. **Lane:** light. **Compute:** no reference run; 2 measured runs, each capped at 6 min. Precomputed steps: none
**Needs:** base install only
**Before the session:** B2 done at seed 0, so its model and tables sit in `~/ml-data/capstones/b/`. `--download` fetches the July file if it is missing, then `--smoke`.
**Interview question:** Your ETA model was trained in January and it is now July: how do you know it drifted, and what does a retrain buy?
**Repo link:** none for ETA: no repo file covers ETA ([README](README.md#repo-hld-it-maps-to)). The payments HLD's drift rule is the analogue: [`model-lifecycle-shadow-and-labels.md`, §5 Proving a model before it declines anyone](../../../hld/payments-risk-decisioning/deep-dives/model-lifecycle-shadow-and-labels.md#5-proving-a-model-before-it-declines-anyone) (PSI above 0.2 on the top 30 features)
**Captured by the script:** P1 to P3 and every Record row. **Human steps:** the binning rule for zones, the design and the write-up
**Status:** todo

## 0. Framing (0:00, 7 min, no AI)

Reread the ETA framing line in `write-up.md`. Under it, write one line on what this session adds: the signal that says the model has aged, and what you would do when it fires.

## 1. Predict (0:07, 5 min, no AI)

Write each row here and in `../../prediction-log.md` (Lab `B3`) before anything runs. MAE is in seconds.

| Step | Question | Kind | Prediction | 80% range or confidence |
|---|---|---|---|---|
| P1 | How many of B2's 7 inputs have a PSI above 0.2 between January 1 to 24 (the reference) and July 1 to 24, with the bins in Terms | num | | |
| P2 | B2's January model scored on July 25 to 31: its MAE there minus its MAE on January 25 to 31. Up, down or same, plus a size range | dir | | |
| P3 | Refreshed on July: the baseline tables, the distance medians and the residual model rebuilt on July 1 to 24 with B2's config. MAE on July 25 to 31 minus the January model's MAE on the same week. Up, down or same, plus a size range | dir | | |

Terms, fixed so the two months compare:

- **July trips.** B2's filters, with pickups in [2024-07-01, 2024-08-01).
- **The 7 inputs, as the January model sees them.** Hour, weekday, pickup zone, dropoff zone, median past distance, baseline and pair trip count. The last three are looked up in January's tables for both months, exactly as serving would in July.
- **PSI.** The sum over bins of (a - e) ln(a / e), with e the January share and a the July share of a bin. Numeric inputs: 10 quantile bins cut on January. Zone ids: you choose the binning in section 3, for example one bin per zone, with zones under 0.5% of January trips pooled into one bin. Empty bins get a floor, for example 0.0001; write the value you use. Also the PSI of the model's predictions and of the duration itself.
- **Intervals.** P2 compares two different weeks, so its interval comes from 1,000 bootstrap resamples drawn from each week separately. P3 scores the same week twice, so it uses 1,000 paired resamples.

## 2. Setup (before the session)

```
$ source ~/.venvs/ml/bin/activate
$ cd ml-learning/capstones/b-ride-demand-eta
$ python scripts/b3_drift_january_vs_july.py --download
$ python scripts/b3_drift_january_vs_july.py --smoke
```

`--download` also checks that B2's saved model and tables exist, and prints their paths.

## 3. Baseline (0:12, 15 min)

Why: a drift alarm is worth having only if it says something about the error, so measure both on the same model.

You write first, in this file, no AI (about 5 min). This is the prompt the AI builds from:

1. The reference and current windows, and the binning for each input (zones included) with the floor.
2. Which MAE differences get which interval, and why.
3. The RESULT contract: every name in the Record table, the mode that prints it, and its unit.

The AI then writes the script with `labkit.start(lab=47)`, reusing B2's feature function. Annotate each AI block with one line before the first run.

```
$ python scripts/b3_drift_january_vs_july.py --smoke
$ python scripts/b3_drift_january_vs_july.py --baseline
(paste your RESULT lines)
```

Prediction vs actual, one sentence each for P1 and P2. There is no reference run: the AI fills Actual and Hit from your pasted lines.

## 4. Change one thing (0:27, 15 min; the run finishes by 0:40)

Change: rebuild the baseline tables, the distance medians and the residual model on July 1 to 24, with B2's config, and score July 25 to 31. P3 is logged above.

Why: a refresh is the cheapest response to drift, so price it before reaching for a new model.

```
$ python scripts/b3_drift_january_vs_july.py --change
(paste your RESULT lines)
```

Prediction vs actual, one sentence.

## 5. Write-up (0:42, 15 min, no AI)

- **Explain-back (5 min).** Five sentences for a smart engineer new to ML. Then ask the AI for the weakest claim, not a rewrite.
- **Deliverable (10 min).** Add §3 Drift to `write-up.md`: the PSI per input against 0.2, the MAE shift with its interval, and what the refresh bought.

## 6. What I learned

The five explain-back sentences, edited after the AI's question.

## 7. Interview soundbite (the card written at 0:57)

> One or two sentences only someone who ran this would say.

Framing: decision ___ | prediction time ___ | label and its maturity ___ | offline metric ___ | online metric ___ | guardrail ___

Staff follow-up (failure modes): PSI and MAE disagree, one past its threshold and the other not. Which do you page on, and what does "PSI above 0.2 on the top 30 features" in the payments HLD assume that a duration model may not meet? Answer in 2 sentences from the repo link (§5).

## 8. Close (0:57, 3 min)

The AI drafts card `B3-T` (the payments version or a variant you did not run) from your run. Edit or replace it. The question goes to `../../quiz-bank.md`, the key to `../../answers/quiz-key.md`, citing your RESULT line. Set Status here and in the [README](README.md#sessions).

## Record

Suggested names: if your RESULT contract renames them, edit this table first. Paste, do not type.

| Metric | Your run | Hardware (the script's HW line) | Captured by (script or learner) |
|---|---|---|---|
| Your zone binning and the floor | | | learner |
| `baseline.psi_hour`, `baseline.psi_weekday`, `baseline.psi_pu_zone`, `baseline.psi_do_zone`, `baseline.psi_pair_distance`, `baseline.psi_baseline` and `baseline.psi_pair_count` | | | script |
| `P1.n_psi_over_0p2` (inputs of 7) | | | script |
| `baseline.psi_prediction` and `baseline.psi_duration` | | | script |
| `baseline.mae_jan_s` (January 25 to 31) and `baseline.mae_jul_s` (July 25 to 31), the January model | | | script |
| `P2.mae_shift_s` (July minus January) | | | script |
| `baseline.mae_shift_ci95_low` and `baseline.mae_shift_ci95_high` | | | script |
| `change.mae_jul_refreshed_s` | | | script |
| `P3.mae_refresh_change_s` (refreshed minus January model, July 25 to 31) | | | script |
| `change.mae_refresh_ci95_low` and `change.mae_refresh_ci95_high` | | | script |
