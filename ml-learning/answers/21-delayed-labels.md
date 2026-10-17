# 21. Delayed labels: mature, proxy or naive, and an attack that started 3 weeks ago: reference answers

> Spoilers. The AI opens one block at a time, only after that step's prediction row exists and the learner pasted their own RESULT lines, or after 'debrief 21'.

- **HW:** `HW chip='Apple M4 Pro' cpu=14 gpu=20 mem_gib=24 macos=26.5.1 python=3.13.7 torch=2.14.1 device=cpu`
- **Seeds:** 0, 1 and 2 for baseline, change and break (light lane), `PYTHONHASHSEED=0`. The seed sets LightGBM's row and column sampling only. The synthetic stream is always seed 0.
- **Reference script:** `answers/21_delayed_labels_ref.py` (sha256 prefix `cd35a06942f8f69a`), run from `m4-production-ml-payments/`. Raw seed-0 output: `answers/21-delayed-labels.out`.
- **Runs and wall times (seeds 0, 1, 2, light lock):** baseline 14.4 s, 14.1 s, 14.9 s; change 14.0 s, 14.5 s, 26.1 s; break 25.0 s, 18.1 s, 16.3 s. All 9 runs are current. No precomputed steps.
- **Tolerance rule:** tol = spread (max - min) over seeds 0, 1, 2. P1, the maturity rows, every `true_rate` and every `train_label_rate` come from the fixed synthetic stream, so their spread is 0. Grade P1 on the learner's own 80% range.

<details><summary>P1. Dispute delays are uniform on 7 to 120 days: the share of a 30-day-old cohort's frauds that is visible today</summary>

**Answer: 0.202677** (`P1.visible_share_30d`), tolerance 0 (the stream is fixed, so no seed moves it). The formula gives F(30) = (30 - 7) / (120 - 7) = 23/113 = 0.2035.

Seed-0 RESULT lines:

```
RESULT P1.visible_share_30d=0.202677 unit=fraction seed=0
RESULT baseline.true_rate_age7=0.00952607 unit=fraction seed=0
RESULT baseline.observed_rate_age7=0 unit=fraction seed=0
RESULT baseline.true_rate_age14=0.00912124 unit=fraction seed=0
RESULT baseline.observed_rate_age14=0.000552272 unit=fraction seed=0
RESULT baseline.true_rate_age30=0.00851781 unit=fraction seed=0
RESULT baseline.observed_rate_age30=0.00172637 unit=fraction seed=0
RESULT baseline.true_rate_age60=0.00842171 unit=fraction seed=0
RESULT baseline.observed_rate_age60=0.00395164 unit=fraction seed=0
RESULT baseline.true_rate_age90=0.00826683 unit=fraction seed=0
RESULT baseline.observed_rate_age90=0.00606 unit=fraction seed=0
RESULT baseline.true_rate_age120=0.0077173 unit=fraction seed=0
RESULT baseline.observed_rate_age120=0.0077173 unit=fraction seed=0
```

Seeds 1 and 2: 0.202677 and 0.202677, and every age row is identical, because no maturity row touches the model.

**Why.** A fraud is visible at age a only when its dispute delay is at most a days. `scripts/paystream.py` draws each delay from U(7, 120) days, so the maturity curve is the straight line F(a) = (a - 7) / 113 from 7 to 120 days. The measured share is that line plus sampling noise: 12,774 frauds are at least 30 days old, so one standard error is 0.0036, and 0.202677 sits 0.24 standard errors below 23/113. The other ages trace the same line (observed over true): 0 at 7 days, 0.0605 at 14 (F = 0.0619), 0.4692 at 60 (0.4690), 0.7331 at 90 (0.7345), and exactly 1 at 120 (0.0077173 both).

**The weekly table** (`TABLE cohort` lines in the .out) is the same curve read by calendar week as of today. The week of 2018-09-24 shows `observed_rate=0.000000` against `true_rate=0.019831`. Every week up to the one of 2018-05-28 shows observed equal to true. The card-testing attack doubles the true weekly rate from the week of 2018-09-10 (`true_rate=0.019480`, against 0.009048 in the week of 2018-08-27), while the observed rate of that week is 0.001791: on observed labels the attack is invisible.

**Common wrong predictions.** 0.25, from 30/120, forgetting that no dispute lands in the first 7 days. Above 0.5, from reading "most chargebacks within 60 to 90 days" as "most fraud is known within a month". Or a rate instead of a share (0.00172637 is the observed fraud rate at age 30, not the visible share).

</details>

<details><summary>P2. Add proxy labels for days 63 to 169 to the mature-only training set: recall at a 1% decline rate on the newest cohort (true labels), direction and size</summary>

**Answer: up, by 0.157853** (`P2.recall_1pct_delta`, tolerance 0.011929), from 0.230219 (`baseline.recall_1pct`, tolerance 0.009543) to 0.388072 (`P2.recall_1pct`, tolerance 0.021472). Over seeds 0 to 2 the mean effect is +0.151889 (rounded from the .json), more than 2x the spread (0.042944), so the gain is real.

Seed-0 RESULT lines (the mature-only rows are in the P1 block's run, `--baseline`):

```
RESULT baseline.recall_1pct=0.230219 unit=fraction seed=0
RESULT baseline.mean_p_ratio=0.544726 unit=ratio seed=0
RESULT baseline.recall_s4=0.0130769 unit=fraction seed=0
RESULT baseline.mean_p=0.0106346 unit=fraction seed=0
RESULT baseline.true_rate=0.0195229 unit=fraction seed=0
RESULT baseline.mean_p_ratio_no_s4=1.11643 unit=ratio seed=0
RESULT baseline.train_label_rate=0.0077173 unit=fraction seed=0
RESULT P2.recall_1pct=0.388072 unit=fraction seed=0
RESULT P2.recall_1pct_delta=0.157853 unit=fraction seed=0
RESULT change.mean_p_ratio=0.825467 unit=ratio seed=0
RESULT change.recall_s4=0.366923 unit=fraction seed=0
RESULT change.mean_p=0.0161155 unit=fraction seed=0
RESULT change.true_rate=0.0195229 unit=fraction seed=0
RESULT change.mean_p_ratio_no_s4=1.46537 unit=ratio seed=0
RESULT change.train_label_rate=0.0122796 unit=fraction seed=0
```

Other seeds: `P2.recall_1pct` 0.375746 and 0.3666; `P2.recall_1pct_delta` 0.151889 and 0.145924; `baseline.recall_1pct` 0.223857 and 0.220676; `change.recall_s4` 0.350769 (tolerance 0.039231) and 0.327692; `baseline.recall_s4` 0.0146154 and 0.0107692.

**Why.** About half of the newest cohort's frauds are card testing (1,300 of 2,515, a diagnostic count), and the mature-only set ends on day 62, about 100 days before that attack began: its scenario-4 recall is 0.0130769. The proxy flag lands within 7 days with recall 0.5, so about half of the card-testing frauds of days 160 to 169 enter training labelled fraud, and scenario-4 recall rises to 0.366923 (a mean effect of +0.335641 over seeds, against 2x the spread, 0.078462). Overall recall gains less than that, because the proxy's 1.5 false flags per true one put noise into the newer rows (`train_label_rate` 0.0122796 against 0.0077173 for mature-only) and the 1% decline budget now goes partly to card testing. The ceiling is low too: declining 1% of a cohort that is 0.0195229 fraud can never reach more than about 0.51 recall (0.01 / 0.0195229).

**What it costs.** The proxy model over-predicts the old scenarios: `change.mean_p_ratio_no_s4` is 1.46537, against 1.11643 for mature-only. Its overall `change.mean_p_ratio` of 0.825467 is closer to 1 only because the under-predicted card testing cancels part of that.

**Common wrong predictions.** Down or flat, "because 60% of the proxy labels are wrong": a label that is right on half the new attack beats no label at all. Or a small gain of a few points, from forgetting that half the newest fraud is a pattern the mature set never saw.

</details>

<details><summary>P3. Train naively on days 0 to 169 with labels known by today: is the mean predicted fraud probability on the newest cohort above or below the true rate, and by what factor</summary>

**Answer: below, by a factor of about 2.7.** `P3.mean_p_ratio` = 0.373352 (tolerance 0.005824): a mean predicted probability of 0.00728891 against a true rate of 0.0195229, and 1 / 0.373352 = 2.678. Seeds 1 and 2: 0.379176 and 0.375187 (factors 2.637 and 2.665). Against the truth, `break.mean_p` minus `break.true_rate` averages -0.0121841 over seeds (rounded from the .json), far beyond 2x the spread (0.00022742). Against mature-only, the ratio falls by 0.167355 on average (2x the spread: 0.011648).

Seed-0 RESULT lines:

```
RESULT P3.mean_p_ratio=0.373352 unit=ratio seed=0
RESULT break.recall_1pct=0.249304 unit=fraction seed=0
RESULT break.recall_s4=0.0792308 unit=fraction seed=0
RESULT break.mean_p=0.00728891 unit=fraction seed=0
RESULT break.true_rate=0.0195229 unit=fraction seed=0
RESULT break.mean_p_ratio_no_s4=0.736203 unit=ratio seed=0
RESULT break.train_label_rate=0.00597784 unit=fraction seed=0
```

Other seeds: `break.recall_1pct` 0.258847 and 0.270775 (tolerance 0.021471); `break.recall_s4` 0.110769 and 0.114615 (tolerance 0.0353842); `break.mean_p_ratio_no_s4` 0.745677 and 0.732883.

**Why.** The naive set calls a payment fraud only once its dispute has arrived by day 183, and a fraud from day d has a chance F(183 - d) of that: 1 for days 0 to 62, 0.47 for day 123, 0.20 for day 153 and 0.06 for day 169. So the naive training label rate is 0.00597784 while the same rows' true fraud rate is about 0.0092 (a diagnostic count), and a model trained without class weights sets its mean probability near its training label rate. Two shortfalls stack on the newest cohort: the missing labels (even without the card-testing payments the ratio is 0.736203), and the new attack, whose training rows are almost all still unlabelled (scenario-4 recall 0.0792308, more than mature-only's 0.0130769 but far below the proxy model's 0.366923).

**Ranking hides it.** Naive recall at a 1% decline rate, 0.249304, is about the same as mature-only's 0.230219. The naive minus mature-only difference averages 0.034725 over seeds, inside 2x the spread (0.042942), so the lab does not teach it as an effect. A team that reads only recall at a fixed decline rate never sees that the probability scale shrank by a factor of about 2.7. A fixed probability threshold, as in lab 22, would decline far fewer payments.

**Common wrong predictions.** Above, "because naive training sees the newest weeks". Or a factor near 1.2, from assuming only the last two weeks of labels are missing: label delay reaches back 120 days, and the newest fraud is the least labelled.

</details>

<details><summary>Rebuild check</summary>

- **Solution:** `answers/rebuild/21_label_maturity.py`. **Stub:** `m4-production-ml-payments/rebuild/21_label_maturity.py`.
- **rebuildcheck:** stub fails as it should (exit 1, NotImplementedError); solution passes (exit 0, `check: PASS`); `REBUILDCHECK OK`.
- `check()` compares `observed_labels()`, `cohort_report()` (weekly and daily periods) and `training_sets()` with a brute-force loop over 1,000 synthetic rows. The fixture plants a dispute landing exactly today and one landing a second later, plus one payment exactly on the 120-day maturity line and one a second past it. It also asserts that every mature label equals the true label.
- Build-time mutation test: `<` in place of `<=` in `observed_labels()` or in the mature test, and naive labels taken from `is_fraud`, each fail `check()`. A `pd.Grouper` week index fails too, because the docstring asks for `to_period(freq)`.

</details>

<details><summary>Card drafts</summary>

| ID | Lab | Type | Question |
|---|---|---|---|
| 21-M | 21 | M | A fraud model retrains on every payment up to last week, each labelled with the disputes known today. Why does its mean predicted probability on new payments fall below the true fraud rate? |
| 21-N | 21 | N | Disputes land uniformly 7 to 120 days after a fraud. What share of a 30-day-old cohort's frauds can you see today, and how do you get it? |
| 21-D | 21 | D | After a retrain, the model's mean score on this week's payments sits far below the fraud rate that later matures, yet recall at a 1% decline rate barely moved. What do you check first? |

Keys:

- **21-M.** Frauds whose dispute has not arrived enter training as legitimate rows, so the training label rate (0.00597784 in the naive set, against about 0.0092 true on the same rows) sets a lower probability scale; the newest frauds, including a new attack, are the least labelled. Reference: `P3.mean_p_ratio` 0.373352. Must mention: (1) "not disputed yet" counted as legitimate; (2) the mean prediction follows the training label rate; (3) the newest rows and the new attack carry the fewest labels.
- **21-N.** F(30) = (30 - 7) / (120 - 7) = 23/113, about 0.20 (the reference measured 0.202677 on 12,774 frauds). Must mention: (1) the formula (a - 7) / 113; (2) about 0.2; (3) none visible at 7 days, all at 120.
- **21-D.** Check the training labels' maturity: the training label rate by cohort week against a fully matured cohort's rate. Recent weeks near zero mean naive labels. Must mention: (1) label rate by cohort age; (2) recall at a fixed decline rate hides a shrunken probability scale (naive 0.249304 vs mature-only 0.230219 recall, mean probability 0.373352 of the truth); (3) the fix: mature-only plus a proxy, and evaluation on matured cohorts.

</details>

<details><summary>Build notes</summary>

**Knob changes:** none. All four effects the lab teaches pass the 2x-spread rule at the spec's configuration (see the .json `effects`). The P2 recall gain is +0.151889 against 2x the spread of 0.042944. The scenario-4 recall gain is +0.335641 against 0.078462. The P3 ratio drop against mature-only is -0.167355 against 0.011648. The naive mean probability minus the true rate is -0.0121841 against 0.00022742. The naive minus mature-only overall recall at 1% (+0.034725 mean, 2x the spread 0.042942) is reported with its spread and taught as about the same, never as an effect.

**Precomputed steps:** none. The seed-0 wall times are 14.4 s, 14.0 s and 25.0 s, so the lab header says 3 runs x 1 min.

**Choices where the spec is silent (the simplest correct option each time):**

- **Model.** `LGBMClassifier(n_estimators=100, random_state=seed, verbose=-1)` with `subsample=0.8, subsample_freq=1, colsample_bytree=0.8, n_jobs=4, deterministic=True, force_col_wise=True`, and no class weights. Bagging makes `--seed` matter, since it is the only random choice. The two LightGBM flags make a same-seed refit bitwise identical. Without them a refit moved predictions by up to 1.4e-12 and never moved a printed value (tagged run `determinism`). No class weights keeps the probability scale tied to the training label rate, which P3 measures.
- **Features.** Lab 19's honest windowed set, written fresh in both scripts: amount, hour, the customer's count and mean amount over the 1, 7 and 30 days strictly before t, the amount over the 30-day mean, and the terminal's frauds with t - 30 days <= tx_j < t and `label_available_at_j < t`. That last one is the README's event-time window, windowed and not cumulative, as lab 19's spec asks. A brute-force loop on 500 rows, half with a known terminal fraud, found 0 mismatches (tagged run `verify`).
- **Maturity rows.** Every payment at least a days old, with its label read at age a: a pooled estimate of F(a) over 12,774 frauds at age 30. One calendar cohort holds about 95 frauds a day and moves by about 0.04. The frauds made 29 to 30 and 30 to 31 days before today give 0.2449 and 0.1828; the week 27 to 34 days old gives 0.2233 (tagged run `verify`).
- **Decline at 1%.** The top 1% of the newest cohort's own scores, `p >= quantile(p, 0.99)`. No mode had a tie at the threshold, and each declined 0.01001 of the cohort (tagged run `verify`).
- **Smoke.** Customers 0 to 499 of the full stream with 20 trees, all three modes in one process. The 60-day smoke stream of `scripts/paystream.py` cannot hold a calendar that ends on day 183.
- **Extra RESULT rows beyond the record:** `mean_p_ratio_no_s4` and `train_label_rate` in every mode, to separate the label delay from the new attack in the P2 and P3 explanations.
- **Labels checked:** `observed_labels()` equals a plain numpy comparison on all 1,795,646 rows. The mature set (617,962 rows, days 0 to 62) equals the truth. The proxy rule matches an independent recomputation (tagged run `verify`).

**Prototype comparison** (spec `[answers only]` values against seed 0 here):

| Value | Prototype | This build | Gap against 2x spread |
|---|---|---|---|
| P1 visible share at 30 days | 23/113 = 0.2035 | 0.202677 | spread 0; 0.24 binomial standard errors below the formula |
| Recall at 1%, mature-only | 0.113 | 0.230219 | over (2x spread 0.019086) |
| Recall at 1%, mature plus proxy | 0.383 | 0.388072 | inside |
| Recall at 1%, naive | 0.229 | 0.249304 | inside |
| Scenario-4 recall, mature-only | 0.017 | 0.0130769 | inside |
| Scenario-4 recall, mature plus proxy | 0.448 | 0.366923 | just over (2x spread 0.078462) |
| Scenario-4 recall, naive | 0.150 | 0.0792308 | at the line (gap 0.0708, 2x spread 0.0707684) |
| Mean p, mature plus proxy | 1.75% | 0.0161155 | over (2x spread 0.0004332) |
| Mean p, naive | 0.80% | 0.00728891 | over (2x spread 0.00022742) |
| True rate, newest cohort | 1.92% | 0.0195229 | the stream as built here |

Every direction matches the prototype: proxy is above naive and mature-only on overall and scenario-4 recall, mature-only barely touches the attack, and naive under-predicts the true rate. The gaps are not bugs, as far as the checks reach. Features and labels match brute force. The tagged run `proto` (seed 0) varied what the spec leaves open: the terminal window (event time as built, arrival time, cumulative), dropping the terminal or the ratio feature, and a threshold set on the training scores. No variant brings mature-only recall near 0.113: it stays between 0.177 and 0.230 with the newest-cohort threshold, and between 0.186 and 0.322 with a training-score threshold. The reason is the newest cohort's makeup: 79 scenario-1 frauds (amount over 220) and 409 scenario-3 frauds (5 x the amount), which mature-only catches at 0.949 and 0.848 (tagged run `verify`). Any tree model learns amount-driven fraud from days 0 to 62. The cumulative terminal count moves the proxy and naive values toward the prototype (scenario-4 recall 0.416 and 0.134, mean p ratio 0.948 and 0.424), so the prototype probably used a terminal feature closer to that one. This build keeps lab 19's windowed definition. An earlier draft of this build windowed the terminal count on the dispute arrival time; it was replaced by the README's event-time formula before any counted run.

The diagnostic logs are in the build's `runs/21/` folder (`baseline-s0-verify.log`, `baseline-s0-proto.log`, `baseline-s0-determinism.log`); they are experiments, not reference runs.

</details>
