# 26. Drift: two-sample tests, PSI and a domain classifier: reference answers

> Spoilers. The AI opens one block at a time, only after that step's prediction row exists and the learner pasted their own RESULT lines, or after 'debrief 26'.

- **HW:** `HW chip='Apple M4 Pro' cpu=14 gpu=20 mem_gib=24 macos=26.5.1 python=3.13.7 torch=2.14.1 device=cpu`
- **Seeds:** 0, 1 and 2 for every step (light lane). The seed changes the samples, the folds and LightGBM's `random_state`.
- **Reference script:** `answers/26_drift_monitoring_ref.py` (sha256 prefix `f39a9d5518b4f239`), run from `m4-production-ml-payments/`. Raw seed-0 output: `answers/26-drift-monitoring.out`. Values, spreads and effects: `answers/26-drift-monitoring.json`.
- **Runs:** 9, none stale. Wall time at seeds 0, 1 and 2: `--baseline` 28.2, 27.0 and 81.7 s; `--change` 12.3, 30.2 and 79.4 s; `--break` 18.7, 31.7 and 109.9 s. Seeds 1 and 2 shared the Mac with other labs' runs; the Compute line uses seed 0.
- **Tolerance rule:** tol = spread (max - min) over seeds 0, 1, 2. A prediction is graded against the seed-0 value with that tolerance.

<details><summary>P1. Domain-classifier AUC for January against July, datetime columns excluded</summary>

**Answer: 0.60288 at seed 0, tolerance 0.002182 (the seed spread).** Seeds 1 and 2: 0.601866 and 0.600698.

Seed-0 lines:

```
RESULT P1.domain_auc=0.60288 unit=auc seed=0
RESULT baseline.ks_flagged=10 unit=of_10 seed=0
RESULT baseline.psi_flagged=0 unit=of_10 seed=0
RESULT baseline.max_ks_stat=0.06398 unit=fraction seed=0
RESULT baseline.max_psi=0.0314665 unit=psi seed=0
RESULT baseline.mae_jan_w4=11.5601 unit=pickups seed=0
RESULT baseline.mae_jul_w2=13.5945 unit=pickups seed=0
RESULT baseline.pred_psi=0.0176522 unit=psi seed=0
TABLE baseline trip_distance   ks_stat=0.033335 ks_p=5.6e-97 psi=0.005721
TABLE baseline fare_amount     ks_stat=0.048235 ks_p=1.25e-202 psi=0.010982
TABLE baseline tip_amount      ks_stat=0.063980 ks_p=0 psi=0.020683
TABLE baseline total_amount    ks_stat=0.035845 ks_p=4.54e-112 psi=0.006650
TABLE baseline passenger_count ks_stat=0.010144 ks_p=9.53e-09 psi=0.000482
TABLE baseline payment_type    ks_stat=0.043045 ks_p=1.92e-161 psi=0.031467
TABLE baseline PULocationID    ks_stat=0.028225 ks_p=1.21e-69 psi=0.008971
TABLE baseline DOLocationID    ks_stat=0.030960 ks_p=1.04e-83 psi=0.010490
TABLE baseline duration_min    ks_stat=0.050455 ks_p=1.11e-221 psi=0.015067
TABLE baseline hour            ks_stat=0.015030 ks_p=4.72e-20 psi=0.001718
```

Other seeds: `baseline.ks_flagged` 10 and 10, `baseline.psi_flagged` 0 and 0, `baseline.max_ks_stat` 0.06454 and 0.06285, `baseline.max_psi` 0.0320919 and 0.0325164. The three forecaster values are the same at every seed (spread 0).

**Why.** Every feature moved a little between January and July: all ten KS tests flag at 200,000 trips per side, yet no PSI comes near 0.2. The largest, `payment_type` at 0.031467, comes from the payment_type 0 rows, which also carry the missing `passenger_count` values: 0.0473 of January trips and 0.0907 of July trips. A domain classifier adds many small joint differences (fares, tips, durations, zones by hour) into one score, so it beats any single feature: the build's single-feature AUCs for these months top out at 0.549 (`fare_amount`). An AUC of 0.60288 says a model can guess the month better than a coin flip. It does not say that any model got worse.

**Common wrong prediction.** 0.8 or higher, because "winter against summer" sounds like a large shift. The trip-level features barely move (the largest KS statistic is 0.06398), so the classifier has little to work with. The opposite miss is 0.5, from expecting nothing to learn once the dates are gone. For these two windows all three seeds land at 0.600698 or above: the small per-feature gaps (all ten KS tests flag) add up in the classifier. That is what January against July 2024 shows here, not a rule for every pair of windows six months apart.

**The forecaster (Record rows of the same run).**

- `baseline.mae_jan_w4` = 11.5601 and `baseline.mae_jul_w2` = 13.5945 pickups per zone-hour: July week 2 is 2.0344 worse, a 17.6% higher MAE.
- `baseline.pred_psi` = 0.0176522: the forecaster's prediction distribution barely moved, so a PSI on its predictions would not have caught the error rise either.
- Mechanism, from the build diagnostics in the `.json` notes. Demand barely changed: mean pickups per zone-hour were 70.07 in January week 4 and 72.1 in July week 2. The last-hour naive MAE (lag_1 alone) stayed flat at 17.87 and 17.928. The seasonal-naive MAE (lag_168 alone) jumped from 14.371 to 24.415, because July week 2's lag_168 reads 1 to 7 July, the 4 July holiday week. The shift that moved the error sits in the model's own input, which a monitor on trip features never sees.

</details>

<details><summary>P2. Two random halves of January: domain-classifier AUC, and the number of features with PSI above 0.2</summary>

**Answer: AUC 0.49958 at seed 0, tolerance 0.00175; PSI flags 0 of 10 at every seed, tolerance 0.** Seeds 1 and 2: AUC 0.501214 and 0.499464; PSI flags 0 and 0.

Seed-0 lines:

```
RESULT P2.domain_auc=0.49958 unit=auc seed=0
RESULT P2.psi_flagged=0 unit=of_10 seed=0
RESULT change.ks_flagged=0 unit=of_10 seed=0
RESULT change.max_ks_stat=0.004275 unit=fraction seed=0
RESULT change.max_psi=0.00020016 unit=psi seed=0
TABLE change trip_distance   ks_stat=0.003730 ks_p=0.123 psi=0.000200
TABLE change fare_amount     ks_stat=0.004275 ks_p=0.0516 psi=0.000195
TABLE change tip_amount      ks_stat=0.001465 ks_p=0.983 psi=0.000038
TABLE change total_amount    ks_stat=0.003775 ks_p=0.115 psi=0.000173
TABLE change passenger_count ks_stat=0.001208 ks_p=0.999 psi=0.000009
TABLE change payment_type    ks_stat=0.000410 ks_p=1 psi=0.000002
TABLE change PULocationID    ks_stat=0.001440 ks_p=0.985 psi=0.000058
TABLE change DOLocationID    ks_stat=0.002185 ks_p=0.725 psi=0.000071
TABLE change duration_min    ks_stat=0.003830 ks_p=0.106 psi=0.000081
TABLE change hour            ks_stat=0.001685 ks_p=0.939 psi=0.000062
```

Other seeds: `change.ks_flagged` 1 and 0 (spread 1), `change.max_ks_stat` 0.004385 and 0.00299, `change.max_psi` 0.000112353 and 0.000126788.

**Why.** Two random halves are draws from one distribution, so the classifier has nothing to learn. Out-of-fold scoring stops memorized noise from raising the AUC, which lands within 0.002 of 0.5, the noise floor at 200,000 trips per side. PSI between two samples of one distribution is about (bins - 1) x (1/n1 + 1/n2), a few ten-thousandths here, so no feature gets near 0.2. The KS false alarms (`change.ks_flagged` 0, 1 and 0 at seeds 0 to 2) fit what p below 0.05 means: each test on its own flags a no-shift feature about 5% of the time, and less often for features with ties, where the test is conservative. It is not a cap per run. Ten tests per run expect about 0.5 false flags, so the one flag at seed 1 (10% of that run's features) is normal, and the three runs together flagged 1 of their 30 tests. The KS critical statistic at 200,000 per side is 0.0043, which is why `fare_amount` at seed 0 (statistic 0.004275, p 0.0516) only just misses.

**Effect against P1:** the AUC changes by -0.101729 (mean over seeds 0 to 2), against a spread of 0.002182. The PSI count is 0 in both steps, a null by design: it measures PSI's false-alarm rate, not an effect.

**Common wrong prediction.** An AUC of 0.52 to 0.55, from expecting LightGBM to find something in noise; out-of-fold probabilities cannot reward that. Or a PSI flag or two, from treating 0.2 as a sensitive line: noise PSI at this sample size sits about a thousand times below it.

</details>

<details><summary>P3. KS tests on every trip of January week 1 against week 2: features flagged at p below 0.05</summary>

**Answer: 10 of 10 at every seed, tolerance 0.** The break uses every trip (609,698 in week 1 and 676,839 in week 2), so the KS and PSI results do not depend on the seed. Only the classifier does.

Seed-0 lines:

```
RESULT P3.ks_flagged=10 unit=of_10 seed=0
RESULT break.psi_flagged=0 unit=of_10 seed=0
RESULT break.domain_auc=0.61046 unit=auc seed=0
RESULT break.max_ks_stat=0.0456651 unit=fraction seed=0
RESULT break.max_psi=0.0188949 unit=psi seed=0
RESULT break.n_week1=609698 unit=trips seed=0
RESULT break.n_week2=676839 unit=trips seed=0
TABLE break trip_distance   ks_stat=0.036051 ks_p=0 psi=0.007619
TABLE break fare_amount     ks_stat=0.028017 ks_p=3.64e-219 psi=0.005868
TABLE break tip_amount      ks_stat=0.045665 ks_p=0 psi=0.013822
TABLE break total_amount    ks_stat=0.025293 ks_p=1.09e-178 psi=0.006350
TABLE break passenger_count ks_stat=0.042748 ks_p=0 psi=0.010155
TABLE break payment_type    ks_stat=0.036465 ks_p=0 psi=0.009079
TABLE break PULocationID    ks_stat=0.028410 ks_p=2.38e-225 psi=0.006055
TABLE break DOLocationID    ks_stat=0.019033 ks_p=2.31e-101 psi=0.003013
TABLE break duration_min    ks_stat=0.008849 ks_p=3.02e-22 psi=0.001120
TABLE break hour            ks_stat=0.038173 ks_p=0 psi=0.018895
```

Other seeds: `break.domain_auc` 0.610389 and 0.610462 (spread 0.000073); every other value is identical.

**Why.** The KS test rejects when the largest gap between the two ECDFs (empirical cumulative distribution functions) passes about 1.358 x sqrt(1/n1 + 1/n2), which is 0.0024 for these two weeks. With over 600,000 trips a side, small gaps clear that line: every feature differs a little between the weeks, from `duration_min` (statistic 0.008849) to `tip_amount` (0.045665), so all ten flag, while the largest PSI is `hour` at 0.0188949. The tests show that the weeks differ, not why. Week 1 holds New Year's Day, but nothing in these runs isolates a holiday, the weather or any other calendar factor as the cause. With this many rows, a p-value measures the row count, not harm; alert on an effect size with a floor (PSI, a domain-AUC line) and on the model's error.

**Effects:** `P3.ks_flagged` minus `break.psi_flagged` is 10 on the same two weeks (spread 0), and `P3.ks_flagged` minus the no-shift control's `change.ks_flagged` is 9.666667 (spread 1).

**The same two weeks, by classifier.** `break.domain_auc` is 0.61046, about the same as January against July. The build ruled out the sample size: at 200,000 trips per side it measured 0.6076. The signal is joint. Speed (trip_distance / duration_min, median 0.172 against 0.159 miles per minute, week 1 being faster) gives 0.5566 on its own, above every single raw feature (0.506 to 0.5339). Dropping the two Mondays (1 and 8 January) only lowers the AUC to 0.5958. So a domain AUC needs its own week-over-week control before it pages anyone.

**Common wrong prediction.** 1 to 4 features, from treating two weeks of one month as "no shift" and expecting the P2 false-alarm rate. The other miss is 10 for the wrong reason, a big shift: every KS statistic is under 0.05 and every PSI under 0.02.

</details>

<details><summary>Rebuild check</summary>

- Solution: `answers/rebuild/26_drift_tests.py`. Stub: `m4-production-ml-payments/rebuild/26_drift_tests.py`.
- Verdict: `REBUILDCHECK OK`. The stub fails with NotImplementedError (exit 1); the solution prints `check: PASS` (exit 0).
- What `check()` tests: `ks_statistic` equals `scipy.stats.ks_2samp`'s statistic to 1e-12 on a small continuous pair, a large pair with a tiny shift and a discrete pair with ties. `psi` equals a `numpy.histogram` computation by hand to 1e-12 on the same pairs, stays under 0.01 for two halves of one sample and goes above 1 for disjoint samples. `domain_classifier_auc` lands within 0.03 of 0.5 for alike samples and within 0.04 of `norm.cdf(1 / sqrt(2))` for a 1-sd mean shift.
- Timing: on a busy machine LightGBM's default thread count makes the two AUC calls slow (about a minute in the build); on an idle Mac the check takes seconds.

</details>

<details><summary>Card drafts</summary>

| ID | Lab | Type | Question |
|---|---|---|---|
| 26-M | 26 | M | A KS test on every trip of two adjacent weeks of NYC taxi data flags all ten features at p below 0.05, yet every PSI stays under 0.02. Why does KS flag shifts that small, and what do teams alert on instead? |
| 26-N | 26 | N | 200,000 January against 200,000 July 2024 NYC taxi trips, ten trip features, no dates: what out-of-fold AUC did a 100-tree LightGBM domain classifier reach, and what did two random halves of January give? |
| 26-D | 26 | D | Your daily drift job flags all 30 monitored features (KS p below 0.05) this week, and the model's metrics look normal. What do you check first? |

Keys (must mention):

| ID | Key |
|---|---|
| 26-M | (1) The KS critical statistic shrinks with the row count, 1.358 x sqrt(1/n1 + 1/n2): 0.0024 at about 600,000 trips a week, so any real gap flags. (2) Real windows always differ a little, so significance is not size; the test does not say why they differ. (3) Alert on an effect size with a floor (PSI above 0.2, a domain-AUC line set on a no-shift control) and confirm with the model's error. |
| 26-N | (1) About 0.60 (0.60288 at seed 0, spread 0.002182). (2) The halves give about 0.50 (0.49958), the noise floor. (3) PSI above 0.2 flagged 0 of 10 features in both, so only the classifier separated the months. |
| 26-D | (1) The effect sizes (KS statistic, PSI) and the row count, not the p-values. (2) The same test on a no-shift control (two random halves, or last week against the week before) for the false-alarm rate. (3) Whether the model's error or score distribution moved; if neither did, no page. |

</details>

<details><summary>Build notes</summary>

**Knob changes:** none. Every effect the lab teaches as real clears 2x the seed spread at the spec's configuration (from the `.json`):

| Effect (A minus B) | Mean over seeds | Spread | 2x rule |
|---|---|---|---|
| `P2.domain_auc` minus `P1.domain_auc` | -0.101729 | 0.002182 | ok |
| `P3.ks_flagged` minus `break.psi_flagged` | 10.0 | 0 | ok |
| `P3.ks_flagged` minus `change.ks_flagged` | 9.666667 | 1 | ok |
| `baseline.mae_jul_w2` minus `baseline.mae_jan_w4` | 2.0344 | 0.0 | ok |

PSI above 0.2 flags no feature in any step. On the halves that is the point (the false-alarm rate). For January against July it is a real finding, not a bug: no trip feature moved that far, and the largest PSI is 0.0314665.

**Precomputed steps:** none. The seed-0 runs took 28.2, 12.3 and 18.7 s, so the Compute line says 3 runs x 1 min.

**Choices where the spec is silent (the simplest correct option each time):**

- **Weeks.** Monday to Sunday from the 1st; both months start on a Monday in 2024. January weeks 1 to 4 are 1 to 7, 8 to 14, 15 to 21 and 22 to 28 January; July week 2 is 8 to 14 July. The Record's "last week of January" is read as week 4, the last full week, right after the training weeks. The forecaster never scores 29 to 31 January; the P1 and P2 samples draw from the whole month.
- **Random halves.** 400,000 January trips drawn without replacement and split into two halves of 200,000, the P1 sample size, so the halves and P1 have the same noise floor. pandas `sample` takes a prefix of one permutation, so for a given seed the first half is exactly the P1 January sample.
- **Missing values.** KS and PSI drop them per feature; the classifier keeps them as NaN. `passenger_count` is missing on the payment_type 0 rows (0.0473 of January, 0.0907 of July), so that shift shows in `payment_type` and in the classifier, not in `passenger_count`'s tests. No other cleaning: negative fares, zero distances and long durations stay in, as a monitor on served features would see them.
- **PSI.** Decile edges from the reference with duplicates dropped, so discrete features get fewer bins; a value on an edge goes to the bin above it (`searchsorted(side="right")`); shares floored at 0.0001. IDs and codes are binned as numbers. A production monitor would bin categories by value.
- **Forecaster.** Lab 16's honest forecaster rebuilt from its spec: a complete zone x hour grid with zeros, so each lag is exactly k hours back; lags 1, 24 and 168 plus hour-of-week; `LGBMRegressor(n_estimators=500, objective="l1")`; training rows with a missing lag dropped, as lab 16's training does. Trained on January weeks 1 to 3, which leaves 8 to 21 January as training rows because week 1 only feeds the lags. Zones: the 59 averaging at least 100 pickups a day in January, also used for July. It has no random step, so its three values have zero spread.
- **Smoke.** All three modes on 5,000-trip samples, 3 zones and 20 trees, under 30 s.
- **Length.** The reference is 149 lines; the starter ships `download()`, `load_data()`, `report()` and the constants exactly as in the reference, plus a `psi()` stub.

**Prototype comparison.** The spec carries no `[answers only]` prototype values for this lab, so there is nothing to compare against. Instead the build checked the two surprising results with one-off diagnostics; the numbers are in the `.json` notes.

- `break.domain_auc` (0.61046) is about the same as `P1.domain_auc` (0.60288). It is not a sample-size effect (0.6076 at 200,000 per side) or a holiday artefact alone (0.5958 without the Mondays). It is a joint shift: speed alone gives 0.5566, and trip_distance plus duration_min together give 0.5614. Dropping any one feature lowers the AUC by at most 0.019 (hour), so the signal is spread across features.
- The forecaster's July error rise traces to the 4 July holiday week inside July week 2's lag_168 (seasonal-naive MAE 14.371 against 24.415, last-hour naive 17.87 against 17.928), not to the trip-feature drift. The spec's choice of July week 2 is kept; the P1 block explains it.

</details>
