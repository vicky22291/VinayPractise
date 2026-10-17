# 09. Accuracy lies on rare events: PR-AUC, cost thresholds and their noise: reference answers

> Spoilers. The AI opens one block at a time, only after that step's prediction row exists and the learner pasted their own RESULT lines, or after 'debrief 09'.

- **HW:** `HW chip='Apple M4 Pro' cpu=14 gpu=20 mem_gib=24 macos=26.5.1 python=3.13.7 torch=2.14.1 device=cpu`
- **Seeds:** 0, 1 and 2 for every step (light lane). The predictions are graded on seed 0. Seeds 1 and 2 are other stratified 80/20 splits of the same 284,807 payments, and other bootstrap draws.
- **Reference script:** `answers/09_metrics_for_rare_events_ref.py` (script_sha256 c4634e792362f9a4). The learner's starter `m2-dont-fool-yourself/scripts/09_metrics_for_rare_events.py` is generated from it by make_c_starter.
- **Runs and wall times (seeds 0, 1, 2):** baseline 14.6, 18.5 and 16.6 s; change 3.1, 5.6 and 4.5 s; break 6.5, 4.3 and 4.0 s. All on cpu, timed while other labs shared the CPU. Precomputed steps: none.
- **Tolerance rule (from the .json):** tol = spread (max - min) over seeds 0, 1, 2. The tolerances below are the .json spreads, rounded to the precision the script prints.
- **Raw output:** `answers/09-metrics-for-rare-events.out` (seed 0, every mode).

Counts below are exact conversions of the printed fractions: recall x 98 test frauds, and frauds caught / precision for the number of payments declined.

<details><summary>P1. ROC-AUC and PR-AUC (average precision) of logistic regression on the test set, and the gap between them</summary>

ROC-AUC is the area under the receiver operating characteristic curve. PR-AUC is the area under the precision-recall curve, computed here as average precision.

**Answer (seed 0):** ROC-AUC 0.965091 (tolerance 0.026206), PR-AUC 0.722553 (tolerance 0.094738), gap 0.242538 (tolerance 0.075677). The 95% bootstrap intervals (500 resamples of the test rows) are [0.938518, 0.986113] for ROC-AUC and [0.62636, 0.804083] for PR-AUC.

```
RESULT baseline.never_fraud_accuracy=0.99828 unit=fraction seed=0
RESULT P1.roc_auc=0.965091 unit=fraction seed=0
RESULT P1.pr_auc=0.722553 unit=fraction seed=0
RESULT P1.gap=0.242538 unit=fraction seed=0
RESULT baseline.roc_auc_lo=0.938518 unit=fraction seed=0
RESULT baseline.roc_auc_hi=0.986113 unit=fraction seed=0
RESULT baseline.pr_auc_lo=0.62636 unit=fraction seed=0
RESULT baseline.pr_auc_hi=0.804083 unit=fraction seed=0
RESULT baseline.recall=0.622449 unit=fraction seed=0
RESULT baseline.precision=0.847222 unit=fraction seed=0
RESULT baseline.cost=196 unit=false_declines seed=0
RESULT baseline.recall_at_95_precision=0.142857 unit=fraction seed=0
```

| Name | Seed 1 | Seed 2 | Tolerance |
|---|---|---|---|
| `P1.roc_auc` | 0.981598 | 0.991297 | 0.026206 |
| `P1.pr_auc` | 0.814736 | 0.817291 | 0.094738 |
| `P1.gap` | 0.166861 | 0.174005 | 0.075677 |
| `baseline.roc_auc_lo` | 0.964192 | 0.982771 | 0.044253 |
| `baseline.roc_auc_hi` | 0.995361 | 0.997917 | 0.011804 |
| `baseline.pr_auc_lo` | 0.731943 | 0.733911 | 0.107551 |
| `baseline.pr_auc_hi` | 0.887413 | 0.890438 | 0.086355 |
| `baseline.never_fraud_accuracy` | 0.99828 | 0.99828 | 0.0 |
| `baseline.recall` (threshold 0.5) | 0.704082 | 0.693878 | 0.081633 |
| `baseline.precision` (threshold 0.5) | 0.873418 | 0.906667 | 0.059445 |
| `baseline.cost` (threshold 0.5) | 155 | 157 | 41 |
| `baseline.recall_at_95_precision` | 0.387755 | 0.336735 | 0.244898 |

**Why.** ROC-AUC is the chance that a random fraud outscores a random good payment. Its false positive rate divides by 56,864 good payments, so the hundreds of good payments that outscore some frauds barely move it. PR-AUC (average precision) is the mean precision at each fraud's rank, and those same good payments sit inside every declined set, so it falls. No skill scores 0.5 on ROC-AUC but only the fraud rate, 0.0017, on PR-AUC, so the two numbers are not on one scale.

**The rest of the baseline.** Never-fraud accuracy is 0.99828 for a model that catches nothing. At the default 0.5 the model declines 72 payments, catches 61 of 98 frauds and costs 196 false-decline units.

**Noise.** At seed 0 the PR-AUC interval runs from 0.62636 to 0.804083 on 98 frauds. Seeds 1 and 2 land at 0.814736 and 0.817291, above that interval: the bootstrap resamples the test rows of one split with the model fixed, while a new seed also changes the training rows and so the model. Recall at 95% precision is the noisiest number in the lab (0.142857, 0.387755 and 0.336735): the few good payments with the very highest scores decide it.

**Common wrong prediction.** PR-AUC close to ROC-AUC, as if they were two views of one number, or PR-AUC read against a 0.5 chance line.

</details>

<details><summary>P2. Recall at the cheapest threshold when a missed fraud costs 5x a false decline</summary>

**Answer (seed 0):** recall 0.836735, 82 of 98 frauds (tolerance 0.05102). The cheapest threshold is 0.0306176. It declines 119 payments (82 frauds and 37 good ones), precision 0.689076, cost 117 against 196 at 0.5.

```
RESULT change.threshold=0.0306176 unit=probability seed=0
RESULT P2.recall=0.836735 unit=fraction seed=0
RESULT change.precision=0.689076 unit=fraction seed=0
RESULT change.cost=117 unit=false_declines seed=0
```

| Name | Seed 1 | Seed 2 | Tolerance |
|---|---|---|---|
| `change.threshold` | 0.0425415 | 0.0894984 | 0.0588808 |
| `P2.recall` | 0.887755 | 0.846939 | 0.05102 |
| `change.precision` | 0.701613 | 0.83 | 0.140924 |
| `change.cost` | 92 | 92 | 25 |

**Why.** At 5:1, declining one more payment saves cost whenever that payment is fraud more than 1 time in 6. So the search lowers the threshold far below 0.5: 26 more false declines buy 21 more caught frauds, and cost falls from 196 to 117. It also lands far below the textbook threshold for calibrated probabilities, 1/(1+5) = 1/6, from the repo link's p* = C_fd / (C_fd + L). The reason: the 47 payments scoring between 0.0306176 and 0.5 had a fraud rate of 0.447 but a mean score of only 0.168, so these scores understate the risk. The 1/6 threshold would cost 154. That is §4's "calibrate first", measured.

**In-sample.** The threshold is chosen on the seed's test rows and priced on the same rows, as the spec's prototype did. So the recall, precision and cost above show what the 5:1 rule picks on these rows. They are not an estimate of what that threshold would catch or cost on new payments. Its cost is the lowest over every distinct score of these very rows, so it is optimistic, and more so with only 98 frauds. The 1/6 threshold is fixed before any label is seen, so part of its gap to the cheapest cost can be that optimism. To ship a threshold, choose it on separate validation rows (or out-of-fold scores on the training rows), confirm it once on untouched test rows, then monitor it.

**Effect check.** P2.recall minus baseline.recall is 0.183673 on average over the seeds, against 2x spread 0.163266: it passes, so the recall gain is taught as a real effect. The cost effect (change.cost minus baseline.cost, mean -69.0 against 2x spread 82) fails the 2x rule, so its size is not claimed as an established effect. It fails only against the level spread of the cost at 0.5, which moves with the split. Its direction holds on every split by construction, because both thresholds are priced on the rows the cheapest one was chosen on: the cheapest threshold is the lowest cost over every distinct score, and 0.5 declines the same payments as one of them. That guarantee is in-sample only (In-sample, above). Its per-seed paired differences agree: -79, -63 and -65.

**Common wrong prediction.** A small move from 0.5 because 0.5 feels like the natural cut, or the fear that a low threshold floods the decline queue. The cheapest threshold still declines only 119 of 56,962 test payments.

</details>

<details><summary>P3. Recall at the threshold that maximises accuracy</summary>

**Answer (seed 0):** recall 0.673469, 66 of 98 frauds (tolerance 0.163266, the widest of the three). The max-accuracy threshold is 0.3978. Its accuracy is 0.999245 (43 errors) against 0.99828 for never-fraud (98 errors). Priced at 5:1 it costs 171, which is 54 more than the cheapest threshold.

```
RESULT break.threshold=0.3978 unit=probability seed=0
RESULT break.accuracy=0.999245 unit=fraction seed=0
RESULT P3.recall=0.673469 unit=fraction seed=0
RESULT break.precision=0.857143 unit=fraction seed=0
RESULT break.cost=171 unit=false_declines seed=0
RESULT break.extra_cost=54 unit=false_declines seed=0
```

| Name | Seed 1 | Seed 2 | Tolerance |
|---|---|---|---|
| `break.threshold` | 0.150232 | 0.10642 | 0.29138 |
| `break.accuracy` | 0.999386 | 0.999438 | 0.000193 |
| `P3.recall` | 0.826531 | 0.836735 | 0.163266 |
| `break.precision` | 0.818182 | 0.836735 | 0.038961 |
| `break.cost` | 103 | 96 | 75 |
| `break.extra_cost` | 11 | 4 | 50 |

**Why.** Accuracy counts a missed fraud and a false decline as one error each, so it is the cost rule at 1:1. It stops declining once the next payments are less than half fraud. The 5:1 rule keeps going while more than 1 in 6 are fraud. At seed 0 the 42 payments between 0.0306176 and 0.3978 held 16 frauds and 26 good payments: at 5:1 declining them saves 80 and costs 26, but at 1:1 it saves 16 and costs 26, so accuracy leaves them and misses 16 more frauds.

**Noise.** How many frauds sit in that band depends on the split: 6 at seed 1 and 1 at seed 2, so the extra cost was 11 and 4 there. The direction never changes here, because both thresholds are chosen and priced on the same test rows, where the cheapest threshold is the minimum by construction: the max-accuracy threshold can only tie it or cost more. That guarantee is in-sample. Chosen on validation rows and priced on untouched test rows, either threshold could come out cheaper in a given split. The size is noise, and seed 0 is the large case. The learner's break loop shows this directly.

**Effect check.** P3.recall minus P2.recall averages -0.0782313 against 2x spread 0.326532, and break.cost minus change.cost averages 23.0 against 2x spread 150. Both fail the 2x rule, so this answer reports the size of the max-accuracy penalty as split noise, not as an established effect, and claims only its direction. The cost direction holds by construction (Noise, above). So does the recall direction: accuracy is the cost rule at 1:1, and raising the price of a miss can only keep or lower the cheapest threshold, so recall at 5:1 is never below recall at the max-accuracy threshold. The recall argument needs only both thresholds chosen on the same rows, since recall can only rise as the threshold falls on any rows, so it would survive a validation split. The cost argument needs the same rows for choosing and pricing, so it would not. See the Build notes.

**Common wrong prediction.** A high recall because accuracy is 99.9%, or a max-accuracy threshold at 0.5. Here it is 0.3978 at seed 0 and 0.150232 and 0.10642 at seeds 1 and 2, below 0.5 for the same reason as in P2: the scores understate the risk in that range.

</details>

<details><summary>Rebuild check</summary>

- Solution: `answers/rebuild/09_average_precision.py` (`pr_curve`, `average_precision` and `cheapest_threshold`). Stub: `m2-dont-fool-yourself/rebuild/09_average_precision.py`.
- `rebuildcheck` verdict: stub fails as it should (exit 1, NotImplementedError); solution passes (exit 0, `check: PASS`); REBUILDCHECK OK.
- `check()` runs on 50,000 synthetic rows at 0.17% positives (82 positives, 121 distinct scores, ties forced by rounding to 2 decimals). It compares `pr_curve` with scikit-learn's `confusion_matrix_at_thresholds` (exact thresholds and counts), `average_precision` with `average_precision_score` to 1e-12, and `cheapest_threshold` with a brute-force `confusion_matrix` search over every distinct score.
- Build test of the check: a trapezoid-rule PR-AUC and a `pr_curve` without tie handling both fail it.

</details>

<details><summary>Card drafts</summary>

| ID | Lab | Type | Question |
|---|---|---|---|
| 09-N | 09 | N | On card data with 0.17% fraud, what accuracy does 'never fraud' score, and why does that make accuracy useless here? |
| 09-M | 09 | M | One fraud model's test scores give a ROC-AUC far above their PR-AUC. What does each metric count, and why does a rare positive class pull them apart? |
| 09-D | 09 | D | A teammate says a new fraud model lifts PR-AUC from 0.72 to 0.80 on one 80/20 split with 98 test frauds. What do you check before you believe it? |

Keys:

- **09-N.** About 99.83% (1 minus the 0.1727% fraud rate; 0.99828 on the 98-fraud test set). Must mention: (1) the number, about 99.8%; (2) a model that declines nothing scores it, so accuracy cannot separate a useless model from a good one; (3) the best threshold only reaches 0.999245, a gap of a tenth of a point.
- **09-M.** Must mention: (1) ROC-AUC is the chance a fraud outscores a good payment, and its false positive rate divides by about 56,864 good payments, so hundreds of false declines barely move it; (2) PR-AUC (average precision) is the mean precision at each fraud's rank, which those same false declines cut; (3) no skill is 0.5 on ROC-AUC but the fraud rate, 0.0017, on PR-AUC. Reference at seed 0: 0.965091 and 0.722553.
- **09-D.** Must mention: (1) noise first: one split's 95% bootstrap interval for PR-AUC ran from 0.62636 to 0.804083, and the same model scored 0.814736 and 0.817291 on two other splits; (2) compare both models on the same test rows with a paired bootstrap of the difference, over several splits; (3) judge the decision too: cost or recall at the chosen threshold, not PR-AUC alone.

</details>

<details><summary>Build notes</summary>

**Configuration, as the spec says.** Stratified 80/20 split with `random_state` = seed, so seed 0 is the spec's `random_state=0`: 56,962 test rows, 98 frauds. `make_pipeline(StandardScaler(), LogisticRegression(max_iter=5000))`. PR-AUC is average precision, never the trapezoid rule. 500 bootstrap resamples. 5:1 cost. Features are V1 to V28 and Amount: OpenML marks Time as the row id, so `fetch_openml` drops it, and the prototype used the same 29 columns.

**Thresholds are chosen in-sample, as the spec's prototype chose them.** Both thresholds are chosen on the test rows and priced on the same rows. The spec's prototype values for the cheapest and the max-accuracy thresholds (recall and cost on the 98 test frauds) were made the same way, so the configuration is kept and the prototype comparison stays like for like. P2, P3 and the costs at the two chosen thresholds therefore show each rule's mechanism, not production estimates, and the lab file and the P2 and P3 blocks say so. The by-construction cost directions are in-sample guarantees. The recall direction does not depend on the rows it is scored on. An honest estimate would choose each threshold on validation rows (for example out-of-fold scores on the 80% training rows) and price it on the untouched test rows. That is not built, because it would change the spec's P2 and P3 configuration. An independent review flagged the missing caveat.

**Where the spec was silent (simplest correct option).**
- Thresholds are searched over every distinct test score, declining s >= t, and a tie goes to the highest threshold (the fewest declines at equal cost). The prototype used a grid of 2,001 quantiles instead.
- The bootstrap is a plain percentile bootstrap of the test rows with `default_rng(seed)`. Both AUCs come from the same resamples. A resample with no fraud would be skipped; none occurred.
- Recall at 95% precision comes from scikit-learn's `precision_recall_curve`. The max-accuracy threshold comes from scikit-learn's `confusion_matrix_at_thresholds` counts, the same rows as `pr_curve`.
- Cost is reported in false-decline units: 5 x missed frauds + false declines.
- `--smoke` uses a stratified 5% sample and 20 resamples. scikit-learn's `average_precision_score` and a brute-force `confusion_matrix` search stand in for the two TODO functions, so the starter passes `--smoke` with its TODO open.

**Deviations, and why.**
- `pr_curve()` ships working, outside the CONCEPT markers. The TODO is then exactly the two functions the spec names; the rebuild asks for all three from memory.
- The lab file runs `--break` at seeds 0, 1 and 2 (the spec names one run). The size of the max-accuracy penalty depends on the split, so the learner sees the noise lesson directly. It adds two runs of about 4 s each.
- The `--check` fixture (20 rows, tied scores) tests `cheapest_threshold` at 5:1, 1:1, 4:1 and 10:2; the 4:1 case has a tie at the lowest cost, so it tests the tie rule.
- The rebuild `check()` also tests `pr_curve` and `cheapest_threshold`, beyond the spec's average precision check.
- Card type D was picked for this lab, assuming D falls on odd labs.

**2x spread rule (mkanswers effects).**
- P1, `P1.roc_auc` minus `P1.pr_auc`: 0.194469 against 2x spread 0.189476. Passes, just.
- P2, `P2.recall` minus `baseline.recall`: 0.183673 against 0.163266. Passes.
- P2 cost, `change.cost` minus `baseline.cost`: -69.0 against 82. Fails against the level spread of the cost at 0.5. The per-seed paired differences are -79, -63 and -65, all the same sign and similar size.
- P3, `P3.recall` minus `P2.recall`: -0.0782313 against 0.326532. P3 cost, `break.cost` minus `change.cost`: 23.0 against 150. Both fail. The per-seed paired differences are -0.163266, -0.061224 and -0.010204 in recall and 54, 11 and 4 in cost.
- Knob trial (tagged run `baseline-s0-explore`, 20 splits at test_size 0.2 and 10 at 0.5, cost factors 5, 10 and 20). On seeds 0 to 2 no combination brings the break effect above 2x the seed spread: the recall effect falls 2.6 to 4.2 times short and the cost effect 3.2 to 6.5 times short. The max-accuracy threshold itself moves between splits, because accuracy is flat near its maximum. Over 20 splits at 5:1 and test_size 0.2, its extra cost had mean 28.5, standard deviation 18.7, min 0 and max 59, and its recall gap had mean -0.0898 and standard deviation 0.0539.
- So the spec's configuration is kept and no effect is inflated. Resolution, by the BRIEF rule for small or null effects: the three failing comparisons (the change cost and both break comparisons) are reported with their spreads and explained. The answer claims only their direction, which holds on every split by construction (in-sample, see the threshold note above), and frames their size as split noise in the P2 and P3 blocks. The lab file's break step asks the learner to judge `break.extra_cost` against its own seed-to-seed spread, so the lab teaches the noise check, not a fixed size.
- Band check (tagged run `baseline-s0-bands`, used in P2 and P3). Between the cheapest threshold and 0.5, the fraud rate was 0.447, 0.400 and 0.600 at seeds 0, 1 and 2, against mean scores of 0.168, 0.182 and 0.268. The calibrated-probability threshold 1/6 would cost 154, 118 and 125.

**Prototype comparison (seed 0 against the spec's values).**
- ROC-AUC 0.965091 against 0.965, and PR-AUC 0.722553 against 0.723: match.
- PR-AUC interval [0.62636, 0.804083] against [0.626, 0.804]: match. It uses the same resampling sequence, `default_rng(0)` with `integers(0, n, n)`.
- Max-accuracy threshold: recall 0.673469 against 0.673, and cost 171 against 171: match. The threshold is 0.3978 against 0.373 because the prototype took the lowest point of its quantile grid that gives the same decisions. Equal counts at both thresholds mean no test score lies between them.
- Cheapest threshold: recall 0.836735 against 0.837: match. Cost is 117 against 118, and the threshold 0.0306176 against 0.029: the exact search over every distinct score found one fewer false decline than the grid. No gap exceeds the spread, and no direction differs.

**Other checks.**
- The parquet fallback was exercised once by forcing the OpenML call to fail. It gives the same rows and labels, with features equal to within 1e-16 (text parsing).
- The starter fails `--check` with NotImplementedError and passes `--download` and `--smoke` with its TODO open.

</details>
