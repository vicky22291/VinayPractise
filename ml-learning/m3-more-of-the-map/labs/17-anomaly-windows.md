# 17. Anomaly windows: unsupervised detection, scored by windows and delay

> Goal: after this I can run a causal z-score and an Isolation Forest on a real series of 10,320 half-hour points and report windows hit (of 5 labelled windows), false alarms per day and detection delay. (No result values anywhere in this file.)

**Level:** S (see `ml-learning/CLAUDE.md`). **Output style:** Explanatory
**Concept link:** [`../README.md#anomaly-detection-scored-by-windows`](../README.md#anomaly-detection-scored-by-windows) (read after the lab)
**Borrowed from:** the [NAB (Numenta Anomaly Benchmark) README](https://github.com/numenta/NAB) and paper ([Lavin and Ahmad 2015, arXiv 1510.03336](https://arxiv.org/abs/1510.03336)); the [scikit-learn outlier detection guide](https://scikit-learn.org/stable/modules/outlier_detection.html). Do it after the lab, as the second contact 1 to 3 days later.
**Dataset:** NAB `realKnownCause/nyc_taxi.csv`: 10,320 half-hour New York City (NYC) taxi passenger counts (2014-07-01 to 2015-01-31) with 5 labelled windows from `labels/combined_windows.json`; 0.27 MB (265,771 B) plus 15,359 B of labels; <https://raw.githubusercontent.com/numenta/NAB/master/data/realKnownCause/nyc_taxi.csv> and <https://raw.githubusercontent.com/numenta/NAB/master/labels/combined_windows.json>; NAB repo licence MIT
**Runs on:** cpu. **Lane:** light. **Compute:** 3 runs x 1 min, at most 6 min per run. Precomputed steps: none
**Needs:** base install only
**Before the session** (from the module folder, see section 2): `python scripts/17_anomaly_windows.py --download` (two files into `~/ml-data/nab/`), then `--smoke`.
**Interview question:** A card-testing wave starts tonight: what detects it within a minute without paging on-call ten times a night?
**Repo link:** [`hld/payments-risk-decisioning/deep-dives/features-and-freshness.md`, §3 Freshness against an attack, in numbers](../../../hld/payments-risk-decisioning/deep-dives/features-and-freshness.md#3-freshness-against-an-attack-in-numbers); [`hld/credit-score-alerts/deep-dives/bad-batch-circuit-breaker.md`, §3 The rule](../../../hld/credit-score-alerts/deep-dives/bad-batch-circuit-breaker.md#3-the-rule)
**Captured by the script:** P1 to P3 and every Record row. **Human steps:** none (you write `trailing_z_alarms()`, `score_windows()` and the prompt in section 3)
**Status:** todo

## 0. Retrieval (0:00, 5 min, closed book, no AI)

The AI asks up to three due cards from `../../quiz-bank.md`, one at a time. Do not open the bank first.

## 1. Predict (0:05, 7 min, no AI)

Level S: read `scripts/17_anomaly_windows.py` for 2 minutes first. `load_data()` and `report()` are given; `report()` is the RESULT contract your harness feeds.

Write each row here before anything runs; the AI copies it into `../../prediction-log.md` word for word. A row that asks for several numbers becomes one log row per number, each with its own range.

| Step | Question | Kind | Prediction | 80% range or confidence |
|---|---|---|---|---|
| P1 | Causal 3-sigma z-score on the week-over-week log change: window 336 points (1 week), mean and standard deviation (std) from the previous 336 points only, alarm when abs(z) > 3. False alarms per day over the 215 days | num | | |
| P2 | Isolation Forest instead (contamination 0.01, 100 trees, `random_state` 0), fit on and applied to all points but the first 48. Features: value (the raw half-hour count), hour-of-week (`dayofweek * 24 + hour`, Monday 00:00 = 0), and the mean and std of the previous 48 raw counts, which the first 48 points lack. Windows hit (of 5) and false alarms per day, each as a direction vs the P1 z-score (up, down or same, plus a size range). Graded on `P2.windows_hit_delta` and `P2.false_alarms_per_day_delta`: a hit needs both signs right and both sizes inside their ranges; Off by uses the false-alarms delta | dir | | |
| P3 | The same z-score, but one mean and one std from the whole series, anomalies included: windows hit (of 5) | num | | |

Terms, fixed so your numbers compare with the reference:

- **Signal.** The z-scores read `change_t = log(count_t / count_(t-336))`, the log change against the same half-hour one week earlier, not the raw count. The forest reads the raw count (P2).
- **Hit.** A window with at least one alarm inside it, start and end included.
- **False alarm.** An alarm point outside all 5 windows. False alarms per day divide their count by 215 days (10,320 points / 48). Every detector is scored on all 10,320 points, including the early points where it cannot alarm yet.
- **Delay.** The first alarm inside a window minus the window's start, in minutes. NAB centers each 103-hour window on its labelled event, so a delay counts from about two days before the event.
- **Windows** w1 to w5, in time order: 30 Oct to 3 Nov 2014, 25 to 29 Nov, 23 to 27 Dec, 29 Dec to 3 Jan 2015, 24 to 29 Jan.

## 2. Setup (before the session)

```
$ source ~/.venvs/ml/bin/activate
$ cd m3-more-of-the-map    # from ml-learning/, where sessions start
$ python scripts/17_anomaly_windows.py --download
$ python scripts/17_anomaly_windows.py --smoke
```

`--smoke` checks the given plumbing only (`load_data()` and `report()` on the last 6 weeks). `--baseline`, `--change` and `--break` stop with NotImplementedError until the harness exists.

## 3. Baseline (0:12, 10 min)

Why: the causal z-score is the simplest detector that uses only the past, and it is scored the way on-call will feel it.

You write first, no AI (6 min for all three). If it runs over, the change slot absorbs it: `--change` is one short run.

1. `trailing_z_alarms(values, window, threshold)` in `scripts/17_anomaly_windows.py`, from the formula below. `values` is the change series: the harness computes change_t and passes it in.
2. `score_windows(alarm_times, windows, n_days)` in the same file, from the Terms in section 1. `alarm_times` holds the timestamps of the alarm points, `windows` the five (start, end) pairs from `load_data()`, and `n_days` the days the series covers (215). It returns the dict `report()` reads: `windows_hit`, `false_alarms_per_day` and `delays_min` (one per window in time order, None for a miss).
3. The prompt for the AI, 2 to 4 lines, in this file: the RESULT contract, that is, which `report()` call each mode makes with which scores (`versus=` in `--change`). Point at the P1 row for the detector and at sections 4 and 5 for the forest and the break. No split: nothing trains on the labels, and every detector is scored on the whole series.

The formula for step 1:

```
change_t = log(count_t) - log(count_(t-336))
z_t      = (change_t - mean(change_(t-336) .. change_(t-1))) / std(change_(t-336) .. change_(t-1))
alarm_t  = abs(z_t) > 3          (a point never enters its own mean or std)
```

The std is the sample std, ddof 1 (delta degrees of freedom: divide by n minus 1), as pandas computes it. The first 672 points have no z and never alarm.

The AI then writes the rest of the harness from your prompt: the change series, the Isolation Forest, the break with its two diagnostics, and the three modes. Annotate each AI block with one line before the first run.

```
$ python scripts/17_anomaly_windows.py --baseline
(paste your RESULT lines)
```

Prediction vs actual, one sentence. The reference run is in `../../answers/`; the AI opens it only after your P1 row exists and you have pasted your own RESULT lines.

## 4. Change one thing (0:22, 10 min)

Change: an Isolation Forest replaces the z-score: `IsolationForest(contamination=0.01, random_state=seed)` with its default 100 trees, fit on and applied to every point that has all four features. Its features are the raw half-hour count, hour-of-week (`dayofweek * 24 + hour`, Monday 00:00 = 0) and the mean and std of the previous 48 raw counts, so the first 48 points are left out. The knob is the detector with its own inputs: the z-score reads the weekly log change, and the forest reads raw counts plus hour-of-week. P2 is logged above.

Why: the forest weighs several features at once (the level, the hour of the week, the last day's level and spread), where the z-score reads one signal. What does that change?

```
$ python scripts/17_anomaly_windows.py --change
(paste your RESULT lines)
```

## 5. Break it (0:32, 10 min, AI gives hints only; the run finishes by 0:40)

Break: compute the z-score's mean and std once, from the whole series of week-over-week log changes, anomalies included, instead of from the previous 336 points. P3 is logged above.

Why: it is the z-score most notebooks write first. `--break` also prints two diagnostics, defined in the block below. Open it after your P3 row is logged; your prompt at 0:12 needs it.

<details><summary>The two break diagnostics (open after your P3 row is logged)</summary>

- `break.std_ratio`: the std of all the changes over the std of the changes outside the 5 windows.
- `break.windows_hit_outside_stats`: windows hit (of 5) by the same rule, with the mean and std taken from the changes outside the 5 windows.

</details>

```
$ python scripts/17_anomaly_windows.py --break
(paste your RESULT lines)
```

Why, in three sentences, written without AI:

## 6. Explain-back (0:42, 5 min) and rebuild (0:47, 10 min), no AI

- Five sentences for a smart engineer new to ML, written without AI. The AI names your weakest claim after the session (section 7).
- Rebuild: open `rebuild/17_window_scoring.py`, write `trailing_z_alarms()` and `score_windows()` from memory, then run `python rebuild/17_window_scoring.py`. Its `check()` compares with a brute-force numpy loop over the previous window, a planted spike, and alarms planted on a window's start and end, never with this lab's results.

## 7. What I learned

After the session (about 5 minutes): the AI names the weakest claim in your five sentences and asks one question that tests it. Edit the sentences here.

## 8. Interview soundbite (one of the three cards written at 0:57)

> One or two sentences only someone who ran this would say.

Staff follow-up (trade-off): the bad-batch circuit breaker holds only when a robust z-score and an absolute floor are both crossed. Why pair them, and which false hold does the floor stop? Answer in 2 sentences from the second repo link, §3. Rotate: simplest design, failure modes, migration, what pages at 3 am, cost, trade-off.

## 9. Quiz cards (0:57, 3 min)

The AI drafts three cards (M, N, and T or D). Edit or replace them. Questions go to `../../quiz-bank.md`, keys to `../../answers/quiz-key.md`.

## Record

The script prints these as RESULT lines. Paste, do not type. Each delay prints minutes from its window's start, or `miss` when the window got no alarm.

| Metric | Your run | Hardware (the script's HW line) | Captured by (script or learner) |
|---|---|---|---|
| `baseline.windows_hit` (causal z-score, of 5) | | | script |
| `P1.false_alarms_per_day` (causal z-score) | | | script |
| `baseline.delay_min_w1` | | | script |
| `baseline.delay_min_w2` | | | script |
| `baseline.delay_min_w3` | | | script |
| `baseline.delay_min_w4` | | | script |
| `baseline.delay_min_w5` | | | script |
| `P2.windows_hit` (Isolation Forest, of 5) | | | script |
| `P2.false_alarms_per_day` (Isolation Forest) | | | script |
| `P2.windows_hit_delta` (forest minus z-score) | | | script |
| `P2.false_alarms_per_day_delta` (forest minus z-score) | | | script |
| `change.delay_min_w1` | | | script |
| `change.delay_min_w2` | | | script |
| `change.delay_min_w3` | | | script |
| `change.delay_min_w4` | | | script |
| `change.delay_min_w5` | | | script |
| `P3.windows_hit` (whole-series z-score, of 5) | | | script |
| `break.false_alarms_per_day` (whole-series z-score) | | | script |
| `break.delay_min_w1` | | | script |
| `break.delay_min_w2` | | | script |
| `break.delay_min_w3` | | | script |
| `break.delay_min_w4` | | | script |
| `break.delay_min_w5` | | | script |
| `break.std_ratio` (a break diagnostic, defined in section 5) | | | script |
| `break.windows_hit_outside_stats` (a break diagnostic, defined in section 5) | | | script |
