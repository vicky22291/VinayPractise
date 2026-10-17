# 27. Audit an AI-written fraud pipeline: silent bugs in fluent code: reference answers

> Spoilers. The AI opens one block at a time, only after that step's prediction row exists and the learner pasted their own RESULT lines, or after 'debrief 27'.

`HW chip='Apple M4 Pro' cpu=14 gpu=20 mem_gib=24 macos=26.5.1 python=3.13.7 torch=2.14.1 device=cpu`

- Seeds 0, 1 and 2, light lane, 9 runs (baseline, change, break at each seed), none precomputed.
- Seed-0 wall times: baseline 4.2 s, change 3.6 s, break 5.0 s (the reference's change and break include the 10-split means; the shipped script's runs take seconds).
- Reference: `answers/27_audit_an_ai_written_pipeline_ref.py`. It holds the shipped path (copied unchanged from `m4-production-ml-payments/scripts/27_audit_an_ai_written_pipeline.py`), the fixed copy, the corrected core and the `--break` reveal. Values: `answers/27-audit-an-ai-written-pipeline.json`. Raw seed-0 output: `answers/27-audit-an-ai-written-pipeline.out`.
- Tolerance rule (from the .json): tol = spread (max - min) over seeds 0, 1, 2; heavy labs: the baseline spread applies to every step.
- Lines tagged `n=10` are means over 10 splits per seed (sub-seeds seed x 10 + r). Every variant uses the same sub-seeds, not the same rows: a variant that resamples before its split splits other rows (Find-it debrief). Build notes say why 10 splits.

<details><summary>P1. The script reports a PR-AUC: your honest PR-AUC on next month's traffic</summary>

**Answer: 0.726696** (seed 0), tolerance 0.018908000000000036. The script reported 0.96309.

```
RESULT P1.honest_pr_auc=0.726696 unit=fraction seed=0
RESULT baseline.pr_auc=0.96309 unit=fraction seed=0
RESULT break.shipped_pr_auc_next=0.791778 unit=fraction seed=0
```

| | seed 0 | seed 1 | seed 2 |
|---|---|---|---|
| `baseline.pr_auc`, the script's report | 0.96309 | 0.968584 | 0.954601 |
| `P1.honest_pr_auc`, the corrected core on next month | 0.726696 | 0.707788 | 0.725884 |
| `break.shipped_pr_auc_next`, the shipped model on next month | 0.791778 | 0.706771 | 0.752971 |

Why: the script's test rows were resampled with everything else: 15.5% fraud (`break.shipped_test_fraud_share` 0.154932) against 0.13% next month, and every test fraud row had a copy in the training rows. PR-AUC averages precision over recall, and precision at every recall level climbs when legitimate rows are scarce, so a ranking scores near 1 on such rows. Hold the model fixed and change only the rows: the shipped model itself scores 0.791778 on next month's 56,962 payments (`break.shipped_pr_auc_next`), so most of the gap sits in the rows that graded the report, not in the model; those rows differ from next month in fraud mix, copies and time at once, and no run here isolates one of the three. The corrected core gets 0.726696; the shipped model edges it at seeds 0 and 2, probably because the core holds back the latest quarter of history to tune its threshold and so fits on 360 of the 417 frauds.

Common wrong prediction: a few points below the reported number, as if the gap were overfitting. Honest minus reported is -0.24196900000000002 over the three seeds (spread 0.018908000000000036), but that compares another model on other rows, so it sizes the error in the report, not one cause of it. With the model held fixed, the shipped model on next month minus its own report is -0.21158500000000002 (spread 0.08500699999999994): most of the gap stays when only the rows change.

</details>

<details><summary>P2. How many independent silent bugs the script contains</summary>

**Answer: 3** (all seeds, spread 0).

```
RESULT P2.silent_bugs=3 unit=count seed=0
```

1. `rebalance()` draws each fraud 10 times with replacement before `train_test_split`.
2. `evaluate()` tunes the threshold on the same test rows that report recall and precision.
3. `rebalance()` keeps 10% of the legitimate payments before the split, and nothing corrects for it: the scores, the threshold and `decline_rate()` all sit on that scale.

Each has its own fix, and each fix alone moves a number by more than 2x the seed spread (Find-it debrief).

Common wrong predictions: 2, counting "resampling before the split" once. The oversampling puts copies of training frauds in the test rows; the downsampling changes the scale of every score and rate, and moving it after the split still leaves the odds to correct. Or 4 and up, counting weaker choices that were not planted: F1 instead of a cost-based threshold, and a random split inside history. The reference never fixes either one alone, so these runs give them no size. The fixed copy, which still splits at random, reports a 10-split mean PR-AUC of 0.746899 at seed 0, near the corrected core's 0.726696 on next month, but the two differ in model, rows and fraud rate, so that pair is no measure of the random split.

</details>

<details><summary>P3. The script's threshold claims to fit a 0.2% decline budget: its decline rate on next month's traffic</summary>

**Answer: 0.00365156** (seed 0), tolerance 0.00010533000000000027. The script expected 0.00162172.

```
RESULT P3.decline_rate_next=0.00365156 unit=fraction seed=0
RESULT baseline.decline_rate=0.00162172 unit=fraction seed=0
RESULT break.shipped_precision_next=0.307692 unit=fraction seed=0
RESULT break.shipped_recall_next=0.853333 unit=fraction seed=0
```

| | seed 0 | seed 1 | seed 2 |
|---|---|---|---|
| `baseline.decline_rate`, the script's estimate | 0.00162172 | 0.00165683 | 0.00160855 |
| `P3.decline_rate_next`, the same threshold on next month | 0.00365156 | 0.00375689 | 0.00373933 |
| `baseline.precision`, on its own test rows | 0.983762 | 0.984106 | 0.987722 |
| `break.shipped_precision_next` | 0.307692 | 0.294393 | 0.295775 |
| `baseline.recall`, on its own test rows | 0.871703 | 0.890887 | 0.868106 |
| `break.shipped_recall_next` | 0.853333 | 0.84 | 0.84 |
| `break.shipped_split_decline_rate_next_min`, 10 splits per seed | 0.00254556 | 0.00280889 | 0.00249289 |
| `break.shipped_split_decline_rate_next_max`, 10 splits per seed | 0.0124644 | 0.0102524 | 0.00788245 |

Why: the estimate is base_rate x recall / precision, which is right only when precision comes from rows with the real mix. Here precision came from rows with a tenth of the legitimate payments and 10 copies of each fraud, so it read 0.983762; next month the same threshold has precision 0.307692. Recall held (0.853333), so the extra declines are false declines: the rate is 2.3x the estimate and over the budget. The three seeds land close together by luck: across 10 splits per seed the same pipeline gives 0.00249289 to 0.0124644, and every one of the 30 is over the 0.2% budget.

Common wrong prediction: about 0.002, trusting the budget check, or lower, expecting a leaky model to catch fewer frauds. The model still catches frauds; the scale of the rows that tuned and measured it was wrong.

</details>

<details><summary>Rebuild check</summary>

- Solution: `answers/rebuild/27_honest_core.py`. Stub: `answers/rebuild/stubs/27_honest_core.py`, copied into `m4-production-ml-payments/rebuild/` at 0:47.
- `honest_core()`: split by time first, fit the scaler on the training rows only, keep every training fraud plus 10% of the training legit rows, fit `LogisticRegression(max_iter=1000)`, correct the validation scores with p' = b p / (b p - p + 1) for b = 0.10, pick the best-F1 threshold on the validation rows.
- `check()`: on a 40,000-row `make_classification` toy with 5% positives, the scaler mean equals the training slice's mean (`numpy.allclose`), the corrected mean probability is within 10% of the validation base rate, and the threshold's F1 (`sklearn.metrics.f1_score`) is at least that of 200 quantile thresholds. The uncorrected scores fail the base-rate check.
- `rebuildcheck`: stub fails as it should (exit 1); solution passes (exit 0); REBUILDCHECK OK.

</details>

<details><summary>Find-it debrief</summary>

Each single fix runs alone, with the other two bugs left in, as a mean over the same 10 sub-seeds per seed as the shipped script (`n=10` lines). Same sub-seeds, not the same rows: a fix that changes what is resampled before the split also changes what the test rows hold. So the first three columns are each variant's own report, on its own test rows, and their effects are effects on the number the script reports. Only the last column scores every variant on the same rows, all of next month's traffic. Seed 0 shown; the effects are means over the three seeds, from the .json.

| Variant (10-split means, seed 0) | reported PR-AUC | reported recall | expected decline rate | decline rate on next month |
|---|---|---|---|---|
| Shipped | 0.96319 | 0.883453 | 0.00165749 | 0.00533865 |
| Fix 1 only: oversample after the split | 0.9 | 0.844578 | 0.00161851 | 0.0018802 |
| Fix 2 only: tune the threshold on untouched rows | 0.96833 | 0.798882 | 0.00146795 | 0.0012008 |
| Fix 3 only: thin training rows only, correct the odds | 0.90307 | 0.852038 | 0.0016452 | 0.00214178 |

**Bug 1: frauds drawn 10 times with replacement before the split.**
- Where: `rebalance()`, the `fraud.sample(frac=FRAUD_COPIES, replace=True, ...)` line, called by `main()` before `train_test_split`.
- Why it inflates: copies of one payment land on both sides. Every one of the 834 test fraud rows (360 unique payments at seed 0) has a copy in the training rows (`break.shipped_test_frauds_seen` 1 at every seed). The copies also multiply the test rows' fraud share by 10. For a logistic regression the share seems to do most of the work: fix 1 alone and fix 3 alone each remove one factor of 10 and leave test rows at the same tenfold mix, one without copies of training frauds (fix 1) and one with them (fix 3), and both land near 0.9 (0.9 and 0.90307). Their rows and models differ too, so this points at the share; it does not measure it.
- Fix: split the real rows first, then oversample the training rows only, or use class weights.
- Effect alone on the reported PR-AUC, each variant on its own test rows: -0.06423166666666669 (spread 0.008067000000000046). The report moves because the fix changes what the test rows hold. On the shared next-month rows it also cuts the decline rate from 0.00533865 to 0.0018802 at seed 0.

**Bug 2: the threshold is tuned on the rows that report it.**
- Where: `evaluate()` calls `choose_threshold(y, scores, base_rate)` on the test rows, then reports recall and precision on those same rows.
- Why it inflates: the operating point is fitted to the rows that grade it. Worse, those rows are 15.5% fraud, so best F1 accepts false declines it would refuse at 0.13% fraud.
- Fix: hold out untouched rows before any resampling, tune the threshold there, report on the test rows.
- Effect alone on the reported recall, each variant on its own test rows: -0.08969433333333332 (spread 0.021245999999999987). The threshold cannot move PR-AUC by itself: for fixed scores on fixed rows, PR-AUC does not depend on the threshold. This variant changes both. It holds out a quarter of history before resampling, so it fits its model on fewer rows and reports on other test rows. Its PR-AUC (0.96833 at seed 0, against the shipped 0.96319) differs for that reason, not because of the threshold. On the shared next-month rows the decline rate falls to 0.0012008 at seed 0, the closest of the three single fixes to the corrected core.

**Bug 3: legitimate payments thinned to 10% with no correction.**
- Where: `rebalance()`, the `legit.sample(frac=LEGIT_SHARE, ...)` line, before the split; nothing downstream corrects the scores, and `decline_rate()` takes precision from those rows.
- Why it misleads: the model trains on odds 100 times the real ones (10 copies of each fraud, 1 in 10 legit payments), so its scores are not fraud probabilities: put through the correction below (b = 0.01), the shipped cut of 0.634736 becomes about 0.02, against 0.37427 for the corrected core. The test rows hold a tenth of the legitimate payments, so each caught fraud there comes with a tenth of the false declines it brings in production: precision reads high, and the decline estimate built on it reads low.
- Fix: thin the training rows only; correct the scores with p' = b p / (b p - p + 1), where b = 0.10 / 10 = 0.01 for both resamplings; take the threshold and the decline rate on rows at the real scale.
- Effect alone on the next-month decline rate, on the shared next-month rows: -0.003015463333333334 (spread 0.0007689400000000001). This variant fixes bug 3 only. It thins and corrects the training rows, but it still oversamples before its split and tunes its threshold on its test rows, which keep the legitimate payments unthinned but hold 10 copies of each fraud. So its threshold and its decline estimate are not taken on rows at the real scale: its own estimate (0.0016452 at seed 0) still sits below what it declines next month (0.00214178). Its reported PR-AUC is 0.90307 at seed 0.

**The honest numbers.** The fixed copy on history (three fixes, random splits as shipped): `change.pr_auc` 0.789902 in one run at seed 0 (spread 0.056147999999999976), 10-split mean 0.746899. The corrected core on next month's traffic, seed 0:

```
RESULT P1.honest_pr_auc=0.726696 unit=fraction seed=0
RESULT break.honest_threshold=0.37427 unit=probability seed=0
RESULT break.honest_recall_next=0.733333 unit=fraction seed=0
RESULT break.honest_precision_next=0.733333 unit=fraction seed=0
RESULT break.honest_decline_rate_next=0.00131667 unit=fraction seed=0
```

Its threshold is tuned on the latest quarter of history, which holds only 57 frauds, so best F1 jumps between two plateaus across seeds (0.37427, 0.355798, 0.970332) and its recall and decline rate move with it (0.733333, 0.72, 0.586667; 0.00131667, 0.00128156, 0.000807556). Its next-month decline rate minus the shipped threshold's (P3), averaged over the seeds: -0.0025806646666666666 (spread 0.0005091140000000001).

</details>

<details><summary>Card drafts</summary>

| ID | Lab | Type | Question |
|---|---|---|---|
| 27-M | 27 | M | Oversampling frauds 10x before train_test_split inflates test PR-AUC even for a logistic regression, which barely memorizes rows. Why? |
| 27-N | 27 | N | The audited script expected its threshold to decline 0.16% of payments. What did that model and threshold decline on next month's traffic, and which reported metric was furthest off? |
| 27-D | 27 | D | An offline report shows precision 0.98 at the operating threshold, and the launch declines twice the planned share of payments. What do you check first? |

Keys:

- **27-M:** (1) the test rows inherit the 10x fraud share; (2) precision at every recall level rises when legitimate rows are scarce, so PR-AUC rises for the same ranking; (3) copies of training frauds in the test rows are a second, smaller effect for a linear model.
- **27-N:** (1) 0.37% (0.00365156 at seed 0), about 2.3x the estimate and over the 0.2% budget; (2) precision: 0.98 on the resampled test rows, 0.31 on next month; (3) recall held near 0.85, so the extra declines are false declines.
- **27-D:** (1) the class mix of the rows that measured precision and tuned the threshold: resampled or not, against the production fraud rate; (2) then recompute precision and the decline rate on untouched, later rows.

</details>

<details><summary>Build notes</summary>

**Knobs.** No spec knob changed: frauds drawn 10 times with replacement, 10% of the legitimate payments kept, best-F1 threshold, 0.2% decline budget, logistic regression. The first build round sized each single fix from one split per seed. The fix effects and the fixed copy's effect failed the 2x rule there, because an honest 20% test split of history holds about 83 frauds and its PR-AUC swings by several points. The reference now measures each single fix, and the fixed copy's effect, as means over 10 splits per seed, on the same sub-seeds for every variant (not the same rows: see the Find-it debrief). The shipped script, the single-run lines and every learner-facing number are unchanged. The oversampling factor stays at 10: bug 1's effect clears 2x its spread with room, so the spec's fallback (raise the factor) was not needed.

**Review round.** An outside review found wording the runs do not support, now fixed: the `n=10` lines were called paired on the same splits (they share sub-seeds only), the P1 gap and the random split were sized from comparisons that change model and rows at once, and the fix-3-only variant was read as tuning on rows at the real scale (it keeps bug 1's oversampling). The same-model effect `break.shipped_pr_auc_next:baseline.pr_auc` was added to back the P1 explanation. The shipped script's module docstring no longer lists the steps in order. The reference changed in comments only, and its nine reruns reproduced every value. A second review found the fix-2 debrief calling its PR-AUC unchanged; it now says that variant fits another model and reports on other rows. Text only, no reruns.

**Precomputed steps.** None. Every run takes seconds.

**Deviations from the spec, and why.**
- Bug 3's downsampling sits in the same `rebalance()` call as bug 1, before the split, where the spec says "legitimate training rows". The spec also says the threshold and the claimed decline rate are "taken on that scale", and only rows that are thinned too can carry that scale. With training-only thinning, the threshold would be tuned on test rows at another mix, and the odds correction is monotonic, so it cannot change a best-F1 decision: bug 3 would move nothing but the threshold's number.
- "Claims its threshold declines 0.2% of payments": a best-F1 threshold cannot be pinned to exactly 0.2%. The script picks the best F1 among thresholds whose estimated decline rate, base_rate x recall / precision, fits a 0.2% budget. The lab file quotes the budget, a constant in the code. The estimate itself is the measured `baseline.decline_rate`.
- P1 is the corrected core's PR-AUC on next month: split history by time (first 75% fit, last 25% tune), resample the fitting rows only, correct the odds with b = 0.01. The shipped model's own next-month PR-AUC is printed too (`break.shipped_pr_auc_next`); it is close and noisier.
- P1 and P3 print from the reference's `--break`, the only mode that scores next month's traffic, and P2 from its `--change`. The shipped script prints no P line, so all three rows are graded at the debrief.
- `--change`: the shipped script's `--change` runs the as-shipped path under `change.*` names, for the learner's copy. The reference's `--change` is the fixed copy an audit should end with (split the real rows first, tune on untouched training rows, resample the fitting rows only, correct the odds), one run plus a 10-split mean, and it prints P2 as the number of fixes it applies.
- Model: `make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000))`. The spec is silent; this matches labs 09 and 22 and the rebuild's scaler check.
- History is the first 80% of rows: both data sources store the payments in Time order (checked on the parquet's Time column), and OpenML drops Time as the row id.
- Length: the shipped script is 126 lines, as the spec asks. The reference runs to about 250 lines because it holds the shipped path, the fixed copy, the corrected core, the single fixes and the leak diagnostics; only the AI reads it, at the debrief.

**Prototype comparison.** The spec gives no `[answers only]` prototype values for lab 27, so there is nothing to compare. Internal checks instead: the shipped script and the reference's as-shipped path print identical RESULT lines (seed 0 `--baseline`, seed 1 `--change`); the shipped test rows are 15.5% fraud at every seed and every test fraud row has a copy in the training rows; the rebuild stub fails and its solution passes.

</details>
