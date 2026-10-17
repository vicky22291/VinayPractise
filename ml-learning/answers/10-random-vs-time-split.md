# 10. Random vs time split: test on the future, not a shuffle: reference answers

> Spoilers. The AI opens one block at a time, only after that step's prediction row exists and the learner pasted their own RESULT lines, or after 'debrief 10'.

- **HW:** `HW chip='Apple M4 Pro' cpu=14 gpu=20 mem_gib=24 macos=26.5.1 python=3.13.7 torch=2.14.1 device=cpu`
- **Seeds:** 0, 1 and 2 for every step (light lane), `PYTHONHASHSEED=0`.
- **Reference script:** `answers/10_random_vs_time_split_ref.py` (script_sha256 `542c77ca0835a05b`). The starter, `m2-dont-fool-yourself/scripts/10_random_vs_time_split.py`, is this file with `time_split()` stubbed and the `--break` branch replaced by one line.
- **Runs:** 9, all current, cpu, light lock. Wall times in seconds for seeds 0, 1 and 2: baseline 2.6, 3.0, 2.7; change 3.0, 2.8, 2.4; break 3.0, 3.4, 4.1. Raw seed-0 output: `answers/10-random-vs-time-split.out`.
- **Tolerance rule:** tol = spread (max - min) over seeds 0, 1, 2. Spreads and effects below are the .json values shown to 6 significant digits.
- **Find-it gate:** the P1 and P2 blocks do not name the planted bug, point at its effect or point at P3. P3, the find-it debrief, the card drafts and the build notes do: open them only after the learner's own fix or 'debrief 10'.

<details><summary>P1. Test RMSE (bikes per hour) of LightGBM with a random 80/20 split, as shipped</summary>

- **Answer:** 3.25804 bikes per hour at seed 0, tolerance 0.69175 (the seed spread).
- **Seed-0 RESULT line:** `RESULT P1.rmse_random=3.25804 unit=bikes_per_hour seed=0`
- **Other seeds:** 2.88242 (seed 1), 3.57417 (seed 2).
- **Why:** A random split shuffles the 17,379 hours and holds out 20% of them, drawn from the whole two years. The seed only moves which hours land in that test 20%, and that is the whole spread here: LightGBM at these settings has no row or column sampling, so it ignores its seed. What sets the value itself is in the Find-it debrief block, opened only after the learner's fix or 'debrief 10'.
- **Common wrong prediction:** much higher than the actual.

</details>

<details><summary>P2. Test on the last 30 days instead: RMSE direction and size</summary>

- **Answer:** same, or slightly down. `P2.rmse_time` is 2.28975 at every seed, tolerance 0.0: the time split has no randomness, and LightGBM without row or column sampling ignores its seed. The delta versus P1 (`P2.rmse_time_minus_random`, P2 minus P1 in bikes per hour) is -0.968288 at seed 0, tolerance 0.691756; seeds 1 and 2 give -0.592674 and -1.28443. The mean effect over the three seeds, -0.94846, is inside 2 x 0.69175 (the random split's seed spread), so the build treats it as no real change.
- **Grading (the dir rule, for every label):** a hit needs the right direction and the delta inside the learner's size range. The delta is the learner's own pasted `P2.rmse_time_minus_random`; at seed 0 the reference gives -0.968288 (tolerance 0.691756). "Same" and "down" both count as the right direction, because the change is under 2x the seed spread and the delta is negative at every seed. Each is a hit only when its size range covers the delta. "Up" is a miss whatever its range.
- **Seed-0 RESULT lines:** `RESULT P2.rmse_time=2.28975 unit=bikes_per_hour seed=0` and `RESULT P2.rmse_time_minus_random=-0.968288 unit=bikes_per_hour seed=0`
- **Why:** The last 30 days are December 2012, a quieter month with fewer very busy hours, and this model makes most of its error in the busiest hours. So the time split does not raise the error here. `P2.rmse_time` is the same at every seed, so the delta moves only with P1's random test 20%. The rest of the mechanism is in the Find-it debrief block.
- **Common wrong prediction:** up, by a lot, because a time split is usually harder.

</details>

<details><summary>P3. FIND-IT. Is the baseline RMSE honest? Your honest random-split RMSE, with an 80% range</summary>

Open only after the learner's own fix or 'debrief 10'.

- **Answer:** no, the baseline is not honest. Honest random-split RMSE: 40.1979 bikes per hour at seed 0, tolerance 2.9244. Seeds 1 and 2: 38.5854 and 41.5098.
- **Seed-0 RESULT lines (reference `--break`):** `RESULT P3.rmse_random_honest=40.1979 unit=bikes_per_hour seed=0` and `RESULT break.rmse_time_honest=66.4537 unit=bikes_per_hour seed=0`. The honest time split gives 66.4537 at every seed, tolerance 0.0.
- **Why:** With `casual` and `registered` gone, the model has to predict demand from the hour, temperature, year and day type (the hour carries most of the gain), so the random-split error rises by 36.8595 bikes per hour on average over the three seeds (P3 minus P1, far above 2 x 2.9244). Now the time split does hurt: 66.4537 sits 26.356 above the honest random split on average, also far above 2 x 2.9244. A random split lets each test hour borrow from training hours on the same days. The time split has no hour of its 30 test days in training, so it scores hours up to 30 days after its last training hour, and most of its error falls in the last two weeks of December, where it over-predicts through the holiday lull. Both honest numbers are nowcasts: each hour is scored at its own start, with that hour's weather taken as known (Find-it debrief block, the prediction time).
- **Common wrong prediction:** that P1 was honest, or an honest value close to P1. A learner who dropped the two columns and reran `--baseline` at seed 0 sees exactly 40.1979, and `--change` (with a `time_split()` that gives the reference split) exactly 66.4537, because the honest path is the same code without those two inputs.

</details>

<details><summary>Rebuild check</summary>

- **Stub:** `m2-dont-fool-yourself/rebuild/10_rolling_origin_splits.py`. **Solution:** `answers/rebuild/10_rolling_origin_splits.py`.
- **Verdict:** `rebuildcheck` says the stub fails as it should (NotImplementedError, exit 1) and the solution passes (exit 0, `check: PASS`): REBUILDCHECK OK.
- **What check() compares:** the four folds of `rolling_origin_splits(times, 4, 30, 24)` on 17,379 gap-free hourly timestamps against `TimeSeriesSplit(n_splits=4, test_size=720, gap=24)`, index for index. Then `random_vs_time_rmse` on 2,000 synthetic hourly rows (y = 3x plus noise, `LinearRegression`) against `train_test_split(random_state=0)` and the last `TimeSeriesSplit` fold, both scored with `root_mean_squared_error`.
- **Why time-based folds equal row-based ones there:** with no gaps, 30 days are exactly 720 rows and 24 hours exactly 24 rows. The real `hour.csv` is missing 165 hours (731 days x 24 = 17,544 hours, 17,379 rows), so on the lab data a days-based split and a rows-based split differ.

</details>

<details><summary>Find-it debrief</summary>

- **Where:** the `FEATURES` list at the top of `scripts/10_random_vs_time_split.py` ends with `casual` and `registered`, uncommented.
- **Why it inflates the number:** `casual + registered == cnt` in all 17,379 rows. They are the same rentals as the target, split by rider type, so neither is known before the hour ends: neither exists at prediction time. The model only has to add two inputs (most of its gain goes to `registered`), and trees add in steps, which leaves the few bikes of error seen in P1 and P2. Both splits look great because a time split protects against future rows, not future columns: the leaked columns sit inside every test row. So the leak also hides the time split's cost. P2 did not rise, against the usual lesson that testing on the future is harder, and that clash was the clue in the runs. With the leak gone, the time split does hurt (P3 block).
- **The fix:** drop both from `FEATURES`, keep the other 12 inputs (`season` to `windspeed`), and rerun `--baseline`, then `--change`. That order matters: `--change` reads the stored P1 for its delta, so it must follow the fixed baseline. The general check: for every feature, ask when the value is known relative to the prediction time. A column computed from the outcome, or one that adds up to the target, is a leak.
- **The prediction time, and what the honest path still assumes:** a nowcast, a prediction for the hour that is starting. A model trained once on every hour before the cut scores each test hour at that hour's start, and the hour's weather (`weathersit`, `temp`, `atemp`, `hum`, `windspeed`) counts as known then: the current observation, or a forecast an hour or so ahead. The calendar inputs (`season` to `workingday`) are known at any horizon. Under that setup no input comes from the outcome, so both honest numbers are free of the planted leak, and the time split adds that no hour of its test month is in training. They are not the error of one forecast made at the cut for all 30 days. Hourly weather that far ahead is unknown, and `hour.csv` holds observed weather with no archived forecasts, so that model would have to drop the five weather inputs or use forecasts archived as of the cut. This lab measures neither. A learner who also drops the weather inputs has picked that stricter prediction time: credit the reasoning, and expect their reruns to differ from the reference `--break`, which keeps the weather.
- **Honest numbers (reference `--break`, seed 0):** random split 40.1979 (tolerance 2.9244), last 30 days 66.4537 (tolerance 0.0). As shipped they were 3.25804 and 2.28975.
- **Payments version:** the same leak in a fraud model is a field filled after the decision, such as chargebacks on the card joined as of today, or the issuer's auth result fed to the inline model (repo link §2, items 1 and 2).

</details>

<details><summary>Card drafts</summary>

| ID | Lab | Type | Question |
|---|---|---|---|
| 10-M | 10 | M | With no leaky inputs, why does a random split of hourly demand data score better than testing on the last 30 days? |
| 10-N | 10 | N | Bike Sharing hourly, LightGBM 300 trees, random 80/20 split, seed 0: what RMSE with the two rider-type count columns kept, what after dropping them, and why the gap? |
| 10-D | 10 | D | A demand model scores about the same RMSE on a random split and on the last 30 days, and both look too good. What do you check first? |

Keys (must-mention items):

- **10-M:** (1) a random split leaves the neighbouring hours of each test hour, on the same days, in training, so the model interpolates; (2) in a time split every test hour comes after all the training hours, so no same-day neighbours are in training and the model must extrapolate the trend and the calendar.
- **10-N:** (1) kept: 3.25804 (seed spread 0.69175); dropped: 40.1979 (seed spread 2.9244); accept the right size for each; (2) casual plus registered equals cnt, so the model only adds two inputs.
- **10-D:** (1) for every feature, when is the value known relative to the prediction time; (2) a column computed from the outcome, or one that sums to the target; (3) a time split guards against future rows, not future columns.

</details>

<details><summary>Build notes</summary>

- **Knob changes:** none. Every effect was measured on the spec's configuration.
- **The 2x spread rule:** P3 minus P1 is 36.8595 (spread 2.9244, ok). The honest time split minus the honest random split is 26.356 (spread 2.9244, ok). The as-shipped P2 minus P1 is -0.94846 (spread 0.69175), under 2x the spread. That is the find-it working as designed: the planted columns make the model nearly exact under either split, so the time split cannot show its cost until the fix. It is reported as "same" with its spread and was not inflated.
- **Precomputed steps:** none. Every run took a few seconds.
- **Deviation 1, the interview question:** the spec's wording is "Offline RMSE is 40 and production behaves like 70: how did you split, and what does a time split show?". The honest reference values sit close to both figures (40.1979 and 66.4537 at seed 0), so in the lab header the figures would anchor P3. The lab file uses "Offline RMSE (root mean squared error) looks good and production behaves much worse: how did you split, and what does a time split show?".
- **Deviation 2, the starter:** `make_c_starter` output plus one scripted post-edit that replaces the reference's `--break` branch (the honest path) with the one-line message the brief asks for, because `make_c_starter` copies everything outside the concept markers. The script asserts that the starter names the two planted columns only inside `FEATURES` and holds no "honest", "leak" or "answers only" text.
- **Deviation 3, the rebuild check:** the spec's `check()` compares only the folds of `rolling_origin_splits` with `TimeSeriesSplit(n_splits=4, test_size=720, gap=24)`. The rebuild's `check()` also tests `random_vs_time_rmse` against `train_test_split`, the last `TimeSeriesSplit` fold and `root_mean_squared_error`, because `random_vs_time_rmse` is half the rebuild and needs its own library check. The docstring words the gap the way `TimeSeriesSplit` defines it (gap_hours hours left out between the last train row and the first test row), so counting from the first test row and counting from the cut give the same folds. A fold mismatch prints both row counts, so an off-by-one shows as one row.
- **Deviation 4, the TODO size:** the TODO body is 5 lines (12 with its signature and docstring), short of the fading plan's 12 to 20 lines. The spec fixes the TODO's scope (the last-30-days split that `--change` uses), and in a find-it lab the hunt is the main work of the session. The from-memory writing sits in the rebuild.
- **Choices where the spec is silent:** LightGBM `n_estimators=300`, `n_jobs=4` (three light runs share 14 cores), `random_state=seed`, everything else default (learning rate 0.1, 31 leaves, no row or column sampling, so the seed only moves the random split). Random split: `train_test_split(test_size=0.2, random_state=seed)`. Last 30 days: rows with `time > max(time) - 30 days`, so 2012-12-02 00:00 to 2012-12-31 23:00, no gap. P2 also prints its delta versus P1 through `labkit.prior()`. `--check`: the fixture in the next bullet. Smoke: the first 2,000 rows and 20 trees, with `TimeSeriesSplit(n_splits=2)` standing in for the TODO. Download: the spec's URL only, since the spec names no fallback; `labkit.fetch` retries three times. The scripts write `pd.Timedelta(n, unit="D")`, not `pd.Timedelta(days=n)`: with numpy 2.5.4 and pandas 2.3.3 the keyword form raises a DeprecationWarning about the generic timedelta unit. A learner who writes the keyword form in the TODO sees that warning, and the code still works.
- **The `--check` fixture:** 20 six-hourly timestamps ending 2012-12-05 18:00, with 2012-12-05 06:00 missing, and `test_days=2`, against the last fold of `TimeSeriesSplit(n_splits=2, test_size=7)`. A split by row count, a `>=` cut and a window one day short all fail it; the several rows per day are what catch the first and the last. The missing timestamp sits inside the test window, as `hour.csv` is missing hours inside its last 30 days, so a split that counts test_days times rows per day fails too. The last row ends its day, as in `hour.csv`, so a split by calendar date passes, and it gives the reference split on the lab data. In a build-time probe of eleven `time_split()` variants, each one passed this fixture exactly when it gave the reference split on `hour.csv`. Review replaced the first build's 20 daily timestamps, which a split by row count also passed.
- **Prototype comparison:** the spec holds no `[answers only]` prototype values for lab 10. Its interview question quotes 40 offline and 70 in production; the honest reference values (40.1979 random, 66.4537 time) match both in direction and sit within 2 x 2.9244 of them. No gap to explain.
- **Mechanism checks (a build-time inspection, not lab runs, so no numbers are quoted):** the as-shipped model's error is largest in the busiest hours, and the last 30 days hold fewer of them, which is why P2 is not above P1. The honest random-split model scores about the same on its own test rows inside the last 30 days as on all its test rows, so the honest time-split gap comes from the split, not from December being hard. Most of the honest time-split error falls in the last two weeks of December, where the model over-predicts. Time tests on December 2011 and on November 2012 also scored worse than the honest random split.
- **Review fixes (independent review):** (1) the honest path keeps each hour's observed weather, and the P3 block had called the time split a forecast up to 30 days ahead. The spec's honest path drops only the two planted columns, so the code and the runs are unchanged. The Find-it debrief now names the prediction time (a nowcast) and limits the honesty claim to it, and the P3 block no longer says forecast. (2) The lab file's break section asked for RESULT lines from the starter's `--break`, which prints one line only. It now says the AI runs the reference `--break` after the fix, and shows that command.
- **Reproducibility:** three full rounds of the nine runs gave identical values. The third came after the `--check` fixture change, which is off the measured path, and it is the one in the .json.

</details>
