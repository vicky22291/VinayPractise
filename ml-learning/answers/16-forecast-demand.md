# 16. Forecast demand: seasonal naive first, then lag features: reference answers

> Spoilers. The AI opens one block at a time, only after that step's prediction row exists and the learner pasted their own RESULT lines, or after 'debrief 16'.

- **HW:** `HW chip='Apple M4 Pro' cpu=14 gpu=20 mem_gib=24 macos=26.5.1 python=3.13.7 torch=2.14.1 device=cpu`
- **Seeds:** 0, 1 and 2 for baseline, change and break (light lane, 9 runs, all current in the ledger).
- **Reference script:** `ml-learning/answers/16_forecast_demand_ref.py` (holds the shipped path and the honest path; the learner's `ml-learning/m3-more-of-the-map/scripts/16_forecast_demand.py` holds only the shipped path).
- **Runs and wall times:** baseline 1.4 s, 1.2 s, 2.4 s; change 6.3 s, 4.8 s, 6.4 s; break 11.9 s, 15.6 s, 15.5 s (seeds 0, 1, 2, lock light; wall time includes sharing the CPU with other labs' runs). Precomputed steps: none.
- **Tolerance rule:** tol = spread (max - min) over seeds 0, 1, 2; heavy labs: the baseline spread applies to every step. Every spread here is 0.0: the split is by time and LightGBM at this config makes no random choice, so a rerun on this Mac with these pins should print the same digits.
- **Raw output:** `16-forecast-demand.out` (seed-0 logs). **Values:** `16-forecast-demand.json`.

<details><summary>P1. MAE (mean absolute error, pickups per zone-hour) of seasonal naive on the last 7 days of January, as shipped</summary>

**Answer:** 26.6441 pickups per zone-hour, tolerance 0.0.

```
RESULT P1.seasonal_naive_mae=26.6441 unit=pickups seed=0
```

Seed 1: 26.6441. Seed 2: 26.6441. Seasonal naive has no random choice, so the seed cannot move it.

**Why:** seasonal naive copies the `lag_168` column, so its MAE is the absolute gap between each test row's count and its `lag_168`, averaged over the test week's rows (25 to 31 January, 59 zones). Nothing is trained, so the number measures only how closely `lag_168` tracks each zone-hour's count. Section 5 comes back to this number.

**Common wrong prediction:** a few pickups per zone-hour, from the sense that a busy zone's week looks like the week before.

</details>

<details><summary>P2. LightGBM with lags 1, 24 and 168 plus hour-of-week, as shipped: direction and size of P2.improvement_pct, the MAE improvement in % over seasonal naive (up means LightGBM's MAE is lower)</summary>

**Answer:** up. `P2.improvement_pct` is 51.5853, tolerance 0.0: LightGBM's MAE is lower than seasonal naive's by 51.5853% of the seasonal-naive MAE. LightGBM MAE 12.8997 pickups per zone-hour, tolerance 0.0.

```
RESULT change.lightgbm_mae=12.8997 unit=pickups seed=0
RESULT P2.improvement_pct=51.5853 unit=percent seed=0
```

Seed 1: 12.8997 and 51.5853. Seed 2: 12.8997 and 51.5853. LightGBM at 500 trees and objective l1 uses no bagging or feature sampling, so `random_state` changes nothing.

**Why:** LightGBM gets `lag_1` and `lag_24` as well as `lag_168`, so `lag_1` lets it follow each zone's recent level, and `hour_of_week` gives it the weekly shape; seasonal naive only copies the `lag_168` column. `P2.improvement_pct` is 100 x (seasonal-naive MAE minus LightGBM MAE) / seasonal-naive MAE, both on the same test rows of the same table. Section 5 comes back to this margin.

**Common wrong prediction:** for the shipped code, a small win of a few percent. The Find-it debrief comes back to that guess.

</details>

<details><summary>P3. FIND-IT. Is the shipped LightGBM MAE honest? Your honest MAE, with an 80% range</summary>

**Answer:** no. The honest LightGBM MAE is 10.8973 pickups per zone-hour, tolerance 0.0, against the shipped 12.8997. The honest seasonal naive is 11.7621 against the shipped 26.6441, so the honest improvement is 7.35275% against the shipped 51.5853%.

```
RESULT break.missing_zone_hours_pct=4.13477 unit=percent seed=0
RESULT break.wrong_lag168_pct=69.3432 unit=percent seed=0
RESULT break.honest_seasonal_naive_mae=11.7621 unit=pickups seed=0
RESULT P3.honest_lightgbm_mae=10.8973 unit=pickups seed=0
RESULT break.honest_improvement_pct=7.35275 unit=percent seed=0
RESULT break.honest_lightgbm_mae_shipped_rows=11.3171 unit=pickups seed=0
RESULT break.leaky_lightgbm_mae=9.60074 unit=pickups seed=0
```

Seeds 1 and 2 print the same seven values.

**Why:** the shipped count table has no row for a zone-hour with no pickups (4.13477% of zone-hours in these 59 zones), and `shift(k)` moves k rows, not k hours. One missing hour shifts every `lag_168` in that zone for the next week, so 69.3432% of lagged rows read one or more hours further back than one week. Seasonal naive is nothing but `lag_168`, so it takes the full hit. LightGBM leans on `lag_1` and on `hour_of_week` (computed from the timestamp). In the shipped table `lag_1` is the zone's previous observed row, not always the hour before: it reads further back only on the first row after one or more zero-pickup hours, so it is wrong far less often than `lag_168`. So LightGBM moves less, and the number the bug inflates is the margin, not the model's MAE. Part of each honest MAE's change also comes from scoring the zero-pickup hours: easy rows that the shipped table never held. `break.honest_lightgbm_mae_shipped_rows` splits LightGBM's change in two: on the same rows, the corrected lags take it from 12.8997 to 11.3171, and adding the zero-pickup hours takes it to 10.8973.

A fix that builds every zone x hour with 0 and then shifts reproduces 10.8973 with `--change`. A fix that repairs only the lags (for example a merge on hour minus k) but keeps the zero-pickup hours out of the table scores a different set of test rows, so its number differs: the honest test week is every zone-hour, zeros included.

**Common wrong prediction:** "the honest MAE is higher", because a lag bug usually reads the future and flatters the model. This one points lags further into the past, so the shipped LightGBM MAE was pessimistic and the shipped baseline far worse.

</details>

<details><summary>Rebuild check</summary>

- Solution: `ml-learning/answers/rebuild/16_lag_features.py`. Stub: `ml-learning/answers/rebuild/stubs/16_lag_features.py`, copied to `m3-more-of-the-map/rebuild/16_lag_features.py` at 0:47 because its names and `check()` reveal the planted bug.
- `rebuildcheck`: stub fails as it should (exit 1), solution passes (exit 0), `REBUILDCHECK OK`.
- `check()` builds a synthetic 4-zone hourly series, drops the zero-pickup hours (as a groupby count does), then asserts: the grid is every zone x hour with the same total, 200 random lags per k equal direct `.loc` lookups k hours back, the seasonal-naive MAE equals scikit-learn's `mean_absolute_error`, and `assert_lag_is_past` rejects lags built on the gappy table.
- Build test: four wrong bodies (grid left gappy, lags built with `shift(-k)`, MAE without the test filter, an assert that does nothing) each fail `check()`.

</details>

<details><summary>Find-it debrief</summary>

**Bug 1: zero-pickup hours vanish, so lags count rows instead of hours.**
- Where: `count_pickups()` in `ml-learning/m3-more-of-the-map/scripts/16_forecast_demand.py` uses `groupby(["PULocationID", "hour"]).size()`, which makes a row only for a zone-hour with at least one trip. `add_features()` then uses `groupby("PULocationID").pickups.shift(k)`, which moves k rows.
- Why it inflates the number: 4.13477% of zone-hours have no row, and any one of them pushes every `lag_168` in that zone for the next 168 rows further back, so 69.3432% of lagged rows read the wrong hour (more than a week back, often a few hours earlier in the day). The same gaps also drop the zero-pickup hours from the test week, which an honest forecast must score too. Seasonal naive goes from 11.7621 (honest) to 26.6441 (shipped), LightGBM from 10.8973 to 12.8997, and the margin from 7.35275% to 51.5853%.
- The fix: reindex the counts onto every zone x every January hour (744 hours) with `fill_value=0`, then shift; prove it by checking a few hundred lags against direct lookups k hours back (`complete_grid` and `assert_lag_is_past` in the rebuild).
- Honest numbers: seasonal naive 11.7621, LightGBM 10.8973, improvement 7.35275%. The honest LightGBM scored on the shipped test rows alone: 11.3171.
- The P2 guess: the common wrong P2 prediction, a small win of a few percent from the sense that a good seasonal baseline is hard to beat, missed only the shipped number. The honest margin is 7.35275%, so that instinct holds once every lag points at the right hour.

**Bug 2 (planted in `--break` only): a feature that reads the next hour.**
- Where: the reference `--break` adds `lead_1 = groupby("PULocationID").pickups.shift(-1)` to the honest features.
- Why it inflates the number: `shift(-1)` is the next hour's count, which is not known at forecast time. With the hour before and the hour after, the model interpolates instead of forecasting. MAE drops from 10.8973 to 9.60074, a bigger gain than LightGBM's whole honest margin over seasonal naive (11.7621 to 10.8973).
- The fix: build every feature from data known at the forecast time. Ask "when is this value known?" for each column, and check every lag points k hours into the past.

</details>

<details><summary>Card drafts</summary>

| ID | Lab | Type | Question |
|---|---|---|---|
| 16-M | 16 | M | Why does `groupby(zone).pickups.shift(168)` on a table of pickup counts often not give "same hour last week", and what makes it right? |
| 16-N | 16 | N | In lab 16, what share of `shift(168)` lags on the count table pointed at the wrong hour, and why was it so much larger than the share of zone-hours with no row? |
| 16-D | 16 | D | A new demand model beats "same hour last week" on MAE by a far wider margin than you expected, across busy zones. What do you check first? |
| 16-T | 16 | T | A card-fraud feature, "payments on this card in the previous hour", is `shift(1)` within each card over a table of hourly payment counts. Most cards are idle most hours. What does the feature hold after an idle hour, and how do you build it right at payments scale? |

Draft 16-D or 16-T, not both: 16-T is the swap for 16-D. The close picks D or T by the alternation in `ml-learning/CLAUDE.md` §4 (D every other lab).

Keys (for `answers/quiz-key.md`):
- 16-M: (1) a count table has no row for an hour with zero pickups; (2) `shift` moves rows, not hours, so a missing hour makes the lag reach further back; (3) reindex onto every zone x hour with 0 first, then verify lags against direct lookups.
- 16-N: (1) about 70% of lagged rows, from a few percent of zone-hours missing; a hit is 65% to 75% (source: `break.wrong_lag168_pct` = 69.3432, `break.missing_zone_hours_pct` = 4.13477); (2) one missing hour corrupts the next 168 lags in that zone.
- 16-D: (1) sample a few hundred rows and check each lag equals a direct lookup k hours back; (2) check the table holds every zone x hour, zeros included; (3) recompute the baseline on the fixed table before believing the margin (here it fell from 51.5853% to 7.35275%).
- 16-T: (1) an idle hour has no row, so `shift(1)` returns the count from the card's last active hour, which can be days old, and a quiet card looks busy; (2) a full card x hour grid is too large and sparse at payments scale, so count from event timestamps over a window that ends at the decision time (a time-based rolling count or a range lookup), with 0 for an empty window; (3) check sampled rows against a direct count by timestamp.

</details>

<details><summary>Build notes</summary>

- **Knob changes:** none. Every effect in the .json is `ok` at spread 0.0, so the 2x spread rule holds trivially; the pipeline is deterministic (time split, LightGBM without bagging or feature sampling).
- **Precomputed steps:** none. The slowest seed-0 run is break at 11.9 s.
- **Reruns:** the nine reference runs were repeated twice. The first time, a docstring edit had made the first set stale. The second time, the review added `break.honest_lightgbm_mae_shipped_rows` to `--break`. Each new set printed the same values to every digit for every RESULT name the set before it had.
- **Prototype comparison:** the spec's answers-only prototype measured 4.1% of zone-hours missing and a naive `shift(168)` wrong on 69.3% of lagged rows. This build measures 4.13477% and 69.3432%: same direction, same size.
- **Choices where the spec is silent (simplest correct option):**
  - Zones: January pickups divided by 31 days, at least 100, after filtering pickups to [2024-01-01, 2024-02-01). This gives exactly the spec's 59 zones, and one of them is zone 264, "Unknown" in the zone lookup. Excluding it would give 58, so it stays. The zone lookup is downloaded as the spec says but not used by this lab.
  - LightGBM: the spec's 500 trees and objective l1, every other parameter at the LightGBM default (learning rate 0.1, 31 leaves). Features are exactly `lag_1`, `lag_24`, `lag_168` and `hour_of_week` (day of week x 24 + hour, numeric), with no zone id. Training rows are hours before 25 January with every feature present, so each zone's first week drops out. Test rows are every row from 25 January 00:00.
  - Honest grid: every busy zone x the 744 January hours, `fill_value=0`.
  - "Wrong hour": the timestamp the shipped `shift(168)` actually reads differs from hour minus 168 hours, over every row that has a lag (the whole month).
  - The extra leak: `lead_1` is added to the honest feature set on the honest grid (not swapped for `lag_1`), so its MAE compares directly with the honest LightGBM MAE.
  - The same-rows split (added at review): `break.honest_lightgbm_mae_shipped_rows` trains exactly as `P3.honest_lightgbm_mae` does (every grid hour before 25 January) and scores only the test zone-hours the shipped table holds. It splits LightGBM's shipped-to-honest change into the corrected lags and the zero-pickup hours; both effects are in the .json.
- **Spoiler placement (review fix):** P2's why says only that `lag_1` follows each zone's recent level, because the P2 block opens before the hunt. What the shipped `shift(1)` reads after a zero-pickup hour is in P3, which opens after the learner's fix or 'debrief 16'.
- **Card drafts:** the block holds M, N and D cards, plus 16-T as the swap for 16-D, so the close can pick D or T by the alternation in `ml-learning/CLAUDE.md` §4.
- **Deviations:**
  - The starter is `make_c_starter`'s output with the block between `# --- reference only start ---` and `# --- reference only end ---` (the honest path and the `--break` reveal) replaced by a `run_break()` that prints one line. Its diff from the reference is that block plus the TODO body. Both rules required this: the starter comes from the reference, and the honest path lives only in `answers/`.
  - The scripts write `pd.Timedelta(k, unit="h")`, not `pd.Timedelta(hours=k)`, because the keyword form raises a numpy DeprecationWarning under pandas 2.3.3 and numpy 2.5.4.
  - TODO size: the level C TODO is the spec's `seasonal_naive_mae()`, a 2-line body in the reference. That is short by design, next to the fading plan's 12 to 20 lines for a concept piece. The spec names this TODO and keeps the planted bug out of it. The lag concept is carried by the find-it fix at 0:32 and by the 0:47 rebuild (complete grid, lags, seasonal-naive MAE and the lag assert, 13 body lines).

</details>
