# 17. Anomaly windows: unsupervised detection, scored by windows and delay: reference answers

> Spoilers. The AI opens one block at a time, only after that step's prediction row exists and the learner pasted their own RESULT lines, or after 'debrief 17'.

- **HW:** `HW chip='Apple M4 Pro' cpu=14 gpu=20 mem_gib=24 macos=26.5.1 python=3.13.7 torch=2.14.1 device=cpu`
- **Seeds:** 0, 1 and 2 for baseline, change and break (light lane, 9 runs, none stale).
- **Reference script:** `answers/17_anomaly_windows_ref.py` (script_sha256 bdf80d5eeab86dbe). The learner's starter is `m3-more-of-the-map/scripts/17_anomaly_windows.py`.
- **Wall times:** seed 0: baseline 1.8 s, change 2.4 s, break 2.4 s, on cpu. All nine runs took 1.6 to 4.4 s (lock waits excluded), so the Compute line is 3 runs x 1 min.
- **Tolerance rule (from the .json):** tol = spread (max - min) over seeds 0, 1, 2. Both z-scores make no random choice, so their spread, and so their tolerance, is 0. Only the Isolation Forest moves with the seed.
- **Reading delays:** NAB windows are 103 hours long and centered on the labelled event, so the event sits 3,090 minutes after each window's start (label-file arithmetic). A delay under 3,090 means the first alarm came before the labelled event point.
- **Build inspection:** a figure tagged "build inspection" comes from `mlpy` on the same two data files with the reference's own functions, not from a reference run, and is not in the .json. Every untagged number is a copy from the .json, a fact of the data or label files, or plain arithmetic.

<details><summary>P1. False alarms per day for a causal 3-sigma z-score over a trailing 1-week window (week-over-week log change)</summary>

**Answer: 0.972093 false alarms per day, tolerance 0.0.** The same detector hits all 5 windows, each before its labelled event.

Seed-0 RESULT lines:

```
RESULT baseline.windows_hit=5 unit=of_5 seed=0
RESULT P1.false_alarms_per_day=0.972093 unit=per_day seed=0
RESULT baseline.delay_min_w1=600 unit=min seed=0
RESULT baseline.delay_min_w2=360 unit=min seed=0
RESULT baseline.delay_min_w3=540 unit=min seed=0
RESULT baseline.delay_min_w4=3060 unit=min seed=0
RESULT baseline.delay_min_w5=1680 unit=min seed=0
```

Seeds 1 and 2: identical (0.972093 false alarms per day, 5 windows, the same five delays).

Why: 3 sigma promises 0.27% of points only for Gaussian data, about 26 alarms over the 9,648 scored points, or 0.12 a day (arithmetic). Week-over-week changes have fat tails: about half of the 209 false-alarm points (0.972093 x 215 days) fall on unlabelled holidays (Labor Day, Columbus Day, Martin Luther King Day) or are echoes, points whose comparison point 336 points earlier lies in a labelled window or on one of those three holidays (build inspection: 47 holiday points and 62 echoes, no point in both). The alarms come in runs of consecutive half-hours: the 209 points form 60 episodes, so a pager that merges each run into one page would ring about 0.28 times a day (build inspection).

Grading aid for the debrief (build inspection, same data, not reference runs): false alarms per day is sensitive to details that windows hit is not.

- 0.944186 (203 points, first w1 alarm at 630 minutes): each point entered its own mean and std (no `shift(1)`).
- 0.976744 (210 points): the population std (ddof 0).
- 0 false alarms with 1 window hit: the z-score ran on raw counts.
- 0.772093 with all 5 windows: the plain difference instead of the log change.
- 0.488372 with 4 windows: a one-sided rule (z < -3 only).
- 1.70233 (366 points): `score_windows()` counted every alarm, inside the windows too.
- 0.27907 (60): it counted episodes, not alarm points.
- 1.0398: it divided by the 201 days after the 672-point warm-up instead of 215.
- Window ends included or excluded change nothing here: no alarm of the three reference detectors (seeds 0 to 2) sits on a window's start or end.

Common wrong prediction: the Gaussian figure, about 0.1 a day. Or near 0, because "3 sigma is strict".

</details>

<details><summary>P2. Isolation Forest (contamination 0.01): windows hit (of 5) and false alarms per day, direction vs the z-score</summary>

**Answer: both down.** Graded on `P2.windows_hit_delta` and `P2.false_alarms_per_day_delta`: a hit needs both signs right and both sizes inside their ranges; Off by uses the false-alarms delta. Windows hit 4 against the z-score's 5 (`P2.windows_hit_delta=-1`, tolerance 0). False alarms per day 0 at seed 0 against 0.972093 (`P2.false_alarms_per_day_delta=-0.972093`, tolerance 0.018604999999999983; `P2.false_alarms_per_day` itself has tolerance 0.0186047). Mean effects over the three seeds: -1.0 window and -0.9658914333333333 false alarms per day.

Seed-0 RESULT lines:

```
RESULT P2.windows_hit=4 unit=of_5 seed=0
RESULT P2.false_alarms_per_day=0 unit=per_day seed=0
RESULT P2.windows_hit_delta=-1 unit=of_5 seed=0
RESULT P2.false_alarms_per_day_delta=-0.972093 unit=per_day seed=0
RESULT change.delay_min_w1=3720 unit=min seed=0
RESULT change.delay_min_w2=3660 unit=min seed=0
RESULT change.delay_min_w3=3330 unit=min seed=0
RESULT change.delay_min_w4=miss unit=min seed=0
RESULT change.delay_min_w5=3330 unit=min seed=0
```

Seeds 1 and 2: windows hit 4 and 4. False alarms per day 0 and 0.0186047 (4 points at seed 2), so deltas -0.972093 and -0.953488. Delays, seeds 0, 1 and 2: w1 3720, 3720, 3780; w2 3660, 3630, 3660; w3 3330, 3300, 3330; w4 miss at every seed; w5 3330, 3660, 3090.

Why: contamination 0.01 is an alarm budget, not a significance level: the forest flags the 1% of its 10,272 rows (10,320 minus the first 48) that the fewest random splits isolate, 103 points at every seed (build inspection), wherever they are. Here those are the deepest lows, the blizzard night and the Christmas lull, almost all inside windows, so false alarms nearly vanish. New Year's Eve peaks near 30,000 rides at 01:00, a level a busy Saturday night also reaches (build inspection: 30,236 at 01:00 on 1 January, 30,373 at 23:00 on Saturday 6 September), so isolating it needs splits on value and hour-of-week together; it never makes the top 1%, and w4 is missed at every seed. The forest is also late: its first alarms land at or after the labelled event (delays of 3,090 or more), while the z-score's all land before it.

Caveats for the debrief:

- **Batch, not causal.** The forest was fit on the whole series and applied to the same rows, so where its 1% budget lands depends on later data, the same look-ahead the break gives the z-score. A causal version would fit on past data only (the first weeks, or a weekly refit), so these delays and false alarms are not what it would achieve live (build inspection: fit on its first 4 weeks of rows only, then applied to every row, it hit all 5 windows at 0.54 to 0.96 false alarms a day over seeds 0 to 2).
- **Unequal spans.** The forest can alarm from point 48, the causal z-score only from point 672, and every false-alarm count is divided by the same 215 days. All 4 of the forest's seed-2 false-alarm points fall in points 48 to 335 (build inspection), so the whole P2 tolerance comes from that warm-up span, not from detector behaviour. Counted from point 672 on, the forest raises no false alarm at seeds 0 to 4 (build inspection). No direction changes, and the bias works against the forest.
- **Seed sensitivity.** The windows-hit count is less steady than its 0 spread suggests: seeds 3 and 4 gave 4 and 2 windows (build inspection, not reference runs). The direction held at all 5 seeds: fewer windows and fewer false alarms than the z-score.

Common wrong prediction: "the forest raises more false alarms, because it flags 1% of everything" (about 0.4 a day if its 103 alarms fell at random: 103 x 90% of rows outside the windows / 215 days, arithmetic), or "it catches more windows, because it is the stronger model".

</details>

<details><summary>P3. A z-score with mean and std from the whole series, anomalies included: windows hit (of 5)</summary>

**Answer: 4 of 5, tolerance 0.** It misses w1 (30 October to 3 November: Halloween, the marathon and the daylight-saving change), which the causal z-score hit.

Seed-0 RESULT lines:

```
RESULT P3.windows_hit=4 unit=of_5 seed=0
RESULT break.false_alarms_per_day=0.227907 unit=per_day seed=0
RESULT break.delay_min_w1=miss unit=min seed=0
RESULT break.delay_min_w2=2580 unit=min seed=0
RESULT break.delay_min_w3=2520 unit=min seed=0
RESULT break.delay_min_w4=3060 unit=min seed=0
RESULT break.delay_min_w5=2070 unit=min seed=0
RESULT break.std_ratio=1.73518 unit=ratio seed=0
RESULT break.windows_hit_outside_stats=5 unit=of_5 seed=0
```

Seeds 1 and 2: identical.

Why: one mean and one std over all 215 days include every anomaly, and the largest sets the std: at 03:00 on 27 January the blizzard left 8 rides against 1,584 a week earlier, a log change near -5.3, and leaving out w5 alone cuts the std by about 30% (build inspection: the rides, the log change, and the std falling from 0.299 to 0.211). With all five windows in, the std is 1.73518 times the std of the points outside them (`break.std_ratio`). Divided by that inflated std, w1's largest change scores abs(z) near 2.2 instead of 3.7 and never crosses 3 (build inspection), while the same rule with mean and std from outside the windows hits all 5 (`break.windows_hit_outside_stats=5`): one window masked. Mostly the same inflation cuts false alarms to 0.227907 a day and delays w2 from 360 to 2580 minutes and w3 from 540 to 2520; the rest comes from one global mean and std replacing the trailing week's, since the outside-window rule lands between the two (build inspection: 0.781 false alarms a day, w2 at 990 and w3 at 1140 minutes).

Common wrong prediction: "more windows, because the whole-series mean and std see the future". Look-ahead usually flatters an offline score. Here the future holds the largest anomaly, and it hides a smaller one.

Also: masking reaches the causal detector too. w4's trailing week holds the Christmas window, which inflates its std, so w4 is the causal z-score's weakest window (largest abs(z) 4.26 against 7 to 10 elsewhere, build inspection) and its latest first alarm (3060 minutes).

Also: the whole-series z-score can alarm from point 336, the causal one only from point 672, and both divide by 215 days. 6 of the break's 49 false-alarm points (0.227907 x 215) fall in points 336 to 671 (build inspection), so the drop in false alarms against P1 is, if anything, understated. No direction changes.

</details>

<details><summary>Rebuild check</summary>

Solution: `answers/rebuild/17_window_scoring.py`. Stub: `m3-more-of-the-map/rebuild/17_window_scoring.py`.

`rebuildcheck` verdict: REBUILDCHECK OK. The stub fails with NotImplementedError (exit 1). The solution prints `check: PASS` (exit 0). On 2,000 Gaussian points, `trailing_z_alarms()` must equal a brute-force numpy loop over the previous window twice: 96 points at threshold 3, and 10 points at threshold 0.5, where the ddof and the window length change dozens of alarms. A point whose z is exactly 3 must not alarm, and the planted spike must. `score_windows()` must return 2 windows hit, the right two delays and the right false alarms per day, with alarms planted exactly on the second window's start and end.

Build inspection of the check itself: no `shift(1)`, ddof 0, a window one point short, a window one point long without the shift, a one-sided rule, a whole-series z, `>=` in place of `>`, an exclusive window start or end, delays in hours, every alarm counted as false, and alarms counted as hits all fail it. `rolling(window, closed="left")` and a plain numpy loop pass.

</details>

<details><summary>Card drafts</summary>

| ID | Lab | Type | Question |
|---|---|---|---|
| 17-M | 17 | M | Why can a z-score whose mean and std come from the whole series miss an anomaly that a trailing, past-only z-score catches? |
| 17-N | 17 | N | On NAB's NYC taxi series, about how many false alarms a day did a causal 3-sigma z-score on week-over-week log changes raise, how does that compare with what 3 sigma promises, and why? |
| 17-D | 17 | D | A 3-sigma z-score over a trailing 1-week window of raw half-hourly taxi counts almost never fires in 7 months, not even on Christmas. What do you check first, and what does it tell you? |

Keys:

- **17-M:** (1) the global mean and std include every anomaly, so the std is inflated (here 1.73518 times the std outside the windows, mostly from the blizzard window, build inspection); (2) a milder anomaly divided by the inflated std stays under the threshold: masking (w1 missed, 4 of 5 windows); (3) a trailing window holds only the previous week, unless an earlier anomaly sits inside it.
- **17-N:** (1) about 1 a day (0.972093, 209 alarm points in 215 days); (2) 3 sigma promises 0.27% of points only for Gaussian data, about 0.12 a day here; (3) fat tails: unlabelled holidays and their echoes one week later.
- **17-D:** (1) compare the trailing std with the day-night swing; (2) on raw counts the daily cycle, not the anomalies, sets that std, so a 3-sigma band spans almost every normal half-hour and an anomaly that is large for its hour stays inside it. Accept any fix that removes the cycle before the z-score (the same half-hour last week, an hour-of-week profile, a seasonal decomposition).

</details>

<details><summary>Build notes</summary>

**Knob change (deviation from the spec): the z-scores read the week-over-week log change, not the raw count.** The window (336 points, 1 week) and the threshold (3 sigma) are the spec's. Build inspection with `mlpy` on the same two files, not reference runs:

- On raw counts the std over any week is about 6,900 rides (median trailing 1-week std 6,908; whole-series std 6,939 on a mean of 15,138). The day-night cycle sets it, not the anomalies. A 3-sigma rule then fired once in 215 days, at 01:00 on 2 November 2014 (39,197 rides, the night the clocks fell back, so that half-hour bin likely holds two half-hours). The causal and the whole-series versions gave the same single alarm. So P1 would be 0 false alarms per day and P3 would equal the baseline, and the lab could not show masking at all. Removing all 5 windows changed the raw std by under 1% (6,939 to 6,899).
- The absolute week-over-week difference (count minus the count 336 points earlier) fixed P1 but not P3. Both versions hit all 5 windows, at 0.77 and 0.51 false alarms a day, and masking showed only as delay.
- The log change is scale-free: a night half-hour at 2,000 rides and a day half-hour at 20,000 weigh the same per percent. It keeps the window and the threshold, and it shows masking on the quantity P3 asks for. Per-window largest abs(z): causal 8.31, 6.99, 8.40, 4.26, 9.95; whole series 2.17, 3.86, 6.46, 6.11, 17.64; mean and std from outside the windows 3.68, 6.85, 11.36, 10.46, 30.74. Every hit and miss in P1, P3 and the outside-stats diagnostic clears 3 by at least 0.68, so ddof or shift details do not flip a window.

**Grading aid:** it sits in the P1 block, because the tutor opens only the due step's block.

**Choices where the spec is silent (simplest correct option):**

- Hour-of-week is `dayofweek * 24 + hour` (0 to 167, Monday 00:00 = 0). The trailing 1-day mean and std use the previous 48 raw counts (`rolling(48)` then `shift(1)`, the same causal rule as the z-score). The first 48 rows lack them and are dropped.
- The forest uses scikit-learn defaults (100 trees, `max_samples="auto"`) with `random_state` = the seed. It is fit on and applied to the 10,272 rows with complete features, as the spec implies; `predict() == -1` is an alarm. That makes it a batch detector, not a causal one (P2 caveats).
- P2 compares two detectors, each with its own inputs. The z-score reads the weekly log change (the knob change above). The forest keeps the spec's raw-count features and has to learn the cycle from hour-of-week and the 1-day mean and std. The lab file's Change line says so. A forest fed the log change instead, with the same four features built on it, kept both directions (build inspection, seeds 0 to 2, not reference runs: 3 windows, 0.05 to 0.08 false alarms a day), so the P2 directions do not hinge on the input swap.
- A false alarm is an alarm point, not an episode (the spec's definition). The day count is 10,320 / 48 = 215. Windows include both ends. A missed window prints its delay as `miss`.
- The scoring spans differ, and the stated definition is kept. The causal z-score can alarm from point 672, the whole-series z-score from point 336 and the forest from point 48, and all three divide by 215 days. The forest's seed-2 false alarms and 6 of the break's 49 fall where the causal z-score cannot alarm (P2 and P3 blocks), so the P2 tolerance reflects warm-up, not detector behaviour. No effect changes direction, and the bias is conservative for every conclusion here. Scoring all three from point 672 on was the alternative. It would change the definition the lab file and P1 state, and it changes no direction.
- `--change` recomputes the causal z-score for the deltas instead of reading `labkit.prior()`. It takes milliseconds, makes no random choice, and keeps the deltas independent of run order.
- The learner writes `score_windows()` in section 3, next to `trailing_z_alarms()`, from the Terms list. So the concept piece and the rebuild piece are the same lines (the fading plan), and the rebuild is a retrieval. The AI writes the forest, the break with its diagnostics, and the three modes.
- The masking record is two diagnostics with neutral names: `break.std_ratio` and `break.windows_hit_outside_stats`. Their definitions sit in a collapsed block in the lab file's section 5, opened after the P3 row is logged, so neither the Record table nor the Predict block hints at P3. Masked windows = 5 - 4 = 1. That subtraction is exact here because the outside-stats rule hits every window.
- `--smoke` keeps the last 6 weeks (2,016 points); the starter's smoke feeds placeholder scores to `report()`, so it checks only the plumbing.

**2x spread rule:** every effect the lab teaches passes (from the .json `effects`):

| Effect | Mean over seeds | Spread | OK |
|---|---|---|---|
| `P2.windows_hit` minus `baseline.windows_hit` | -1.0 | 0 | yes |
| `P2.false_alarms_per_day` minus `P1.false_alarms_per_day` | -0.9658914333333333 | 0.0186047 | yes |
| `P3.windows_hit` minus `baseline.windows_hit` | -1.0 | 0 | yes |
| `break.false_alarms_per_day` minus `P1.false_alarms_per_day` | -0.744186 | 0.0 | yes |

The forest's seed sensitivity beyond the three reference seeds is in the P2 caveats.

**Precomputed steps:** none. Every run takes seconds.

**Prototype comparison:** the spec carries no `[answers only]` prototype values for lab 17, so there is no number to compare. Its structural facts hold: 10,320 points, 336 points per week, 215 days, 5 windows (207 points each, 1,035 in all). The design-review rebuild prototype (`lab15_window_scoring.py`) used threshold 4.0 and a 288-point window on synthetic 5-minute data. The spec's 3 sigma and 1 week are used here. Its `rolling().shift(1)` construction and its planted-spike check carried over into `rebuild/17_window_scoring.py`, which the review round extended with a low-threshold comparison, an exact-threshold point and alarms on a window's start and end.

</details>
