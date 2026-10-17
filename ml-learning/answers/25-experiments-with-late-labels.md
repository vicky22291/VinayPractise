# 25. A/B power, peeking and label maturity: reference answers

> Spoilers. The AI opens one block at a time, only after that step's prediction row exists and the learner pasted their own RESULT lines, or after 'debrief 25'.

HW line: `HW chip='Apple M4 Pro' cpu=14 gpu=20 mem_gib=24 macos=26.5.1 python=3.13.7 torch=2.14.1 device=cpu`

Seeds 0, 1 and 2 for baseline, change and break (light lane, 9 runs, none stale). Reference script: `answers/25_experiments_with_late_labels_ref.py`. Raw seed-0 output: `answers/25-experiments-with-late-labels.out`. Wall times for seeds 0, 1 and 2: baseline 1.4, 1.3 and 1.5 s; change 1.6, 1.5 and 1.3 s; break 2.1, 1.7 and 2.1 s.

Tolerance rule (from the .json): tol = spread (max - min) over seeds 0, 1, 2. Every sample size and P2 is closed form, so its spread is 0: a learner's run matches to the unit and to the day when it uses the same pooled formula and rounds up. Only the break step and the sample-ratio draw depend on the seed.

<details><summary>P1. Users per arm to detect a 5% relative lift on a 2% base rate (2.0% to 2.1%), two-sided pooled z-test, alpha 0.05, power 80%</summary>

**Answer: 315,206 users per arm.** Tolerance 0 (closed form: 315206 at seeds 0, 1 and 2).

```
RESULT P1.n_per_arm=315206 unit=users seed=0
RESULT baseline.n_per_arm_cohens_h=315161 unit=users seed=0
RESULT baseline.srm_p_value=2.34504e-11 unit=p seed=0
RESULT baseline.srm_caught=true seed=0
```

Other seeds: `P1.n_per_arm` 315206 and 315206; `baseline.n_per_arm_cohens_h` 315161 and 315161; `baseline.srm_p_value` 1.38126e-17 (seed 1) and 4.72956e-15 (seed 2); `baseline.srm_caught` true at both.

Why: users per arm grow with the outcome's variance over the squared absolute gap, about 2 p(1 - p) (z_a + z_b)^2 / (p2 - p1)^2 with p the average rate, and (z_a + z_b)^2 is about 7.85 at alpha 0.05 and 80% power. A 5% relative lift on 2% is an absolute gap of only 0.1 points, and squaring that gap is what pushes n past 300,000; Lehr's rule of thumb, 16 p(1 - p) / delta^2, lands within 2%. statsmodels with Cohen's h (an arcsine distance) gives 315,161, 45 users lower, so the formula choice does not matter at this base rate. The sample-ratio check flags the 50.5/49.5 split at every seed, because at 630,412 users a 1-point imbalance is about 8 standard deviations.

Common wrong prediction: tens of thousands, from reading the 5% relative lift as the effect size instead of the 0.1-point absolute gap, or from scaling n with 1/delta instead of 1/delta^2.
</details>

<details><summary>P2. Fraud at 0.1% with a 10% relative drop, one payment per unit, labels final 120 days after the payment, 1.5 M payments per arm per day: calendar days to a decision</summary>

**Answer: 121 calendar days**: 1 day of enrollment plus 120 days of label maturity. Tolerance 0 (closed form: 121 at seeds 0, 1 and 2).

```
RESULT change.n_per_arm=1489870 unit=payments seed=0
RESULT change.n_per_arm_cohens_h=1488835 unit=payments seed=0
RESULT change.enrollment_days=1 unit=days seed=0
RESULT P2.calendar_days=121 unit=days seed=0
RESULT change.guardrail_n_per_arm=31234 unit=payments seed=0
RESULT change.guardrail_n_per_arm_cohens_h=31218 unit=payments seed=0
RESULT change.guardrail_days=0.0208227 unit=days seed=0
```

Other seeds: every value in this step is the same at seeds 1 and 2 (no random draw).

Why: n scales roughly with p / delta^2, and the base rate fell 20-fold while the absolute gap fell 10-fold (0.1 to 0.01 points), so the fraud case needs 1,489,870 payments per arm, 4.7 times the P1 case. That is still under one day at 1.5 M payments per arm per day, so enrollment takes 1 day and label maturity takes the other 120: traffic is not the bottleneck, label maturity is. The launch therefore rests on signals that arrive sooner: shadow scoring, whose disagreement set analysts label in days, and a guardrail canary on approval rate. Approval is known at decision time, so the guardrail's 31,234 payments per arm take 0.0208227 days, about 30 minutes at the full 1.5 M payments per arm per day.

Unit assumption: like the spec, the lab treats each payment as an independent unit. A real fraud test keeps each card or customer in one arm, and one card's payments are correlated. So n must grow by the design effect, about 1 + (m - 1) x ICC for m payments per card and an intra-class correlation ICC, or the analysis must run per card with the delta method. That lengthens enrollment and leaves the 120-day maturity wait unchanged.

Common wrong prediction: 150 to 240 days, from assuming a 0.1% outcome needs one to four months of enrollment. The payments per arm grow less than 5 times, and one day of traffic already covers them.
</details>

<details><summary>P3. 400 A/A runs, both arms at 2%, P1 users per arm / 20 a day, a z-test after each of 20 days, stop at the first p below 0.05: false-positive rate</summary>

**Answer: 0.2275 at seed 0**, tolerance 0.0175 (the seed spread).

```
RESULT break.fpr_fixed=0.045 unit=fraction seed=0
RESULT P3.fpr_peeking=0.2275 unit=fraction seed=0
```

Other seeds: `P3.fpr_peeking` 0.225 (seed 1) and 0.2425 (seed 2); `break.fpr_fixed` 0.0375 (seed 1) and 0.0475 (seed 2). Peeking minus fixed averages 0.188333 over the three seeds against a spread of 0.0175.

Why: under the null each look's z-score is about standard normal, but the 20 looks are correlated points on one cumulative random walk, and a rule that stops at the first crossing of 1.96 keeps every early excursion that would have drifted back by day 20. So the error compounds over looks: the theory value for 20 equally spaced looks is about 0.25 (Armitage, McPherson and Rowe 1969), and a 400-run estimate has a standard error near 0.02, so all three seeds sit within about one standard error of it. The same runs tested once after day 20 stay near alpha (0.045, 0.0375 and 0.0475). The plot (`~/ml-data/results/lab25/peeking-seed0.png`) climbs fastest over the first looks, where each day adds the most new data relative to what came before, so the early looks are the least correlated.

Common wrong prediction: 0.05 to 0.10, from treating each daily look as harmless; or about 0.64 = 1 - 0.95^20, from treating the 20 looks as independent tests.
</details>

<details><summary>Rebuild check</summary>

Solution: `answers/rebuild/25_power_and_peeking.py`. Stub: `m4-production-ml-payments/rebuild/25_power_and_peeking.py`.

`rebuildcheck`: the stub fails with NotImplementedError (exit 1) and the solution prints `check: PASS` (exit 0), so REBUILDCHECK OK. `check()` compares `n_per_arm()` with statsmodels `NormalIndPower().solve_power` on Cohen's h at six configurations that are not this lab's (within 0.5%), and `aa_false_positive_rates()` with `proportions_ztest` run look by look on the same draws (exact match).
</details>

<details><summary>Card drafts</summary>

| ID | Lab | Type | Question |
|---|---|---|---|
| 25-M | 25 | M | An A/A test is checked once a day for 20 days and stopped at the first p below 0.05. Why does it declare far more than 5% of runs significant when each daily test on its own is a valid 5% test, and what fixes it? |
| 25-N | 25 | N | Fraud runs at 0.1%, you want to detect a 10% relative drop at alpha 0.05 and 80% power, traffic is 1.5 M payments per arm per day, and labels are final after 120 days. About how many payments per arm, how many calendar days to a decision, and which part of the wait is traffic? |
| 25-D | 25 | D | A fraud-model A/B dashboard shows a significant win a few days after launch. What do you check first? |

Keys:

- **25-M.** (1) The mechanism: the 20 looks are correlated points on one cumulative random walk, and the first crossing of 1.96 ends the run, so early excursions that would have drifted back by day 20 still count. For context, the lab's rate lands between one test and 20 independent ones: 0.2275 at seed 0, against 0.045 for one test after day 20 and 1 - 0.95^20 = 0.64 for independent looks. (2) The fix: one pre-registered horizon, alpha spent across planned looks, or a sequential test with always-valid p-values (Johari et al. 2015).
- **25-N.** (1) About 1.49 M payments per arm (1,489,870, each payment an independent unit), which is 1 day of traffic. (2) 121 calendar days, 120 of them label maturity, so maturity sets the clock, not traffic.
- **25-D.** (1) Label maturity: a few days after launch almost no fraud label is final (the lab's labels take 120 days), so the win compares early, partial labels from the fastest disputes, which need not track the final fraud rate. (2) Peeking: was this the first day the dashboard showed p below 0.05? Stopping there inflates false positives: 0.2275 of the lab's A/A runs at seed 0 stopped this way, against 0.045 at one fixed horizon. (3) The sample-ratio check on the assignment counts: a mismatch means bucketing or exposure logging is broken, and no metric is trusted until it is fixed.

Reference soundbite: "At 0.1% fraud the sample fills in a day and the labels take 120, so traffic is not the bottleneck, label maturity is: gate the launch on shadow plus an approval-rate canary, and read fraud on matured cohorts."

Reference framing line: decision: promote the challenger fraud model | prediction time: at authorization, per payment | label and its maturity: fraud chargeback, final 120 days after the payment | offline metric: recall at the champion's decline rate on an out-of-time set | online metric: fraud rate on matured cohorts, read at day 121 | guardrail: approval rate, a drop from 95% to 94.5% detectable in about 30 minutes at the full 1.5 M payments per arm per day, or about 10 hours for a canary arm at 5% of that traffic.
</details>

<details><summary>Build notes</summary>

**Knob changes: none.** Every recorded effect cleared 2x the seed spread: `P2.calendar_days:change.enrollment_days` 120 days (spread 0), the change step's one knob, and `P3.fpr_peeking:break.fpr_fixed` 0.188333 (spread 0.0175, so 2x is 0.035).

**Precomputed steps: none.** Every run took 1.3 s to 2.1 s.

**Deviations from the spec, and why:**

- Goal line. The spec says "show the false-positive rate that daily peeking causes". The lab says "measure the false-positive rate of 400 A/A tests checked every day for 20 days", so the goal does not hint at the direction of the peeking effect. It also sizes the fraud test in payments per arm, to match the Unit term, and expands A/B and A/A at first use.
- The design is fixed in Terms. The spec's learner_builds has the learner design the simulation first, daily traffic included. The common.json gradeability rule wins: each predict row names the exact config, so the Terms fix the arms, traffic, looks, stop rule and repeats before P1 to P3. The learner still writes the design and checks it against the Terms. Then they add what the Terms leave open: the unit for a real fraud test, how the harness marks a run as stopped, the standard error at 400 runs, and one Terms choice to change for a real launch.
- Unit. The spec sizes "users per arm" but gives the fraud traffic in "payments per arm per day". The lab defines the unit: a user in P1, the A/A runs and the sample-ratio check, and one payment, randomized by payment id, in the fraud case and the guardrail. So the change rows print `unit=payments`. Like the spec, the formula treats every unit as independent; the P2 block gives the design effect a per-card test needs.
- One knob. The template's change names exactly one knob, but the spec's change moves the base rate, the relative change and the label maturity together. The lab names label maturity as the knob and the fraud test as its setting, sized by the same `n_per_arm()`. The controlled contrast is `change.enrollment_days` (the decision day if each label were known at once) against `P2.calendar_days` (matured labels), at the same payments per arm and traffic, and it is the change effect the .json records. The gap from P1 to `change.n_per_arm` mixes the base rate and the relative change, so it is not recorded as an effect; the P2 block explains it through the base rate and the absolute gap.
- The guardrail prints `change.guardrail_days`, the unrounded time at the full 1.5 M payments per arm per day, in the same unit as the enrollment row. Reporting it in hours told the learner its scale before the run.
- `aa_false_positive_rates()` takes a seed, which the spec's signature lacks, so `--seed` changes the draws. It returns `(fixed, peeking)`, as the rebuild does. The plot's per-look stopped share comes from a separate AI-side helper, `stopped_share_by_look()`, which redraws the same counts and tests every look with statsmodels' `proportions_ztest`. Its curve is identical to the in-function curve of the earlier build, and its last point equals `P3.fpr_peeking` at every seed. The rebuild keeps the spec's four arguments and adds `seed=0` and `alpha=0.05` defaults.

**Choices where the spec is silent** (the simplest correct option each time):

- A/A traffic. The spec gives no number for the break's daily traffic. The reference spreads the P1 sample over the 20 looks, ceil(315206 / 20) = 15,761 users per arm per day, so the fixed-horizon test is the P1 experiment itself. Under the normal approximation the peeking rate depends on the number of looks, not the traffic.
- Enrollment days are whole days, rounded up, so calendar days = 1 + 120.
- The guardrail is sized at the same 1.5 M payments per arm per day and is two-sided, like the main test and like the prototype's guardrail number. The Terms say its time scales with 1 / the arm's daily traffic, so an arm at 5% of that traffic takes 20 times as long.
- The optional sample-ratio row lives in `--baseline`: 2 x the P1 users per arm, one binomial draw at 50.5%, `scipy.stats.chisquare` against 50/50, flagged below p 0.001. Its p-value moves by orders of magnitude between seeds because the draw itself has a standard deviation near 397 users; it is flagged at every seed.
- P1 is the pooled formula the learner writes, the same as the rebuild's. statsmodels' Cohen's h numbers print beside it as the `*_cohens_h` rows.
- The rebuild's `check()` also compares `aa_false_positive_rates()` with statsmodels `proportions_ztest` on the same draws, beyond the spec's `n_per_arm` check against `NormalIndPower` within 0.5%. Both use configurations that are not this lab's.
- Level B ships no script (`scripts/` stays empty for this lab). Before the baseline the learner writes the design and the RESULT contract (about 5 min), then `n_per_arm()` (about 2 min) as the first function of a new `scripts/25_experiments_with_late_labels.py`. `aa_false_positive_rates()` comes at the start of the break step, and the annotations of the change and break blocks sit in section 4, so each block fits its 10 minutes. The sample-size formula sits in a `<details>` block, so reading ahead at 0:05 does not turn P1 and P2 into arithmetic. The third card is a D card.

**Prototype comparison** (spec author notes, Cohen's h):

- Users per arm: the prototype has 315,161, 1,488,839 and 31,217; the `*_cohens_h` rows here print 315161, 1488835 and 31218. Cause: the prototype rounds the closed form 2 ((z_a + z_b) / h)^2 to the nearest user, which ignores the far rejection tail of a two-sided test. statsmodels' power counts that tail, which lowers n by under 4 units in the fraud case, and the reference rounds up, which adds under 1. Every gap is 4 units or fewer, under 0.01%. The pooled formula (P1, `change.n_per_arm`, `change.guardrail_n_per_arm`) sits above Cohen's h by 45, 1035 and 16 units, under 0.1% each.
- Fraud calendar: the prototype says about 1 day of traffic, then 90 to 120 days. Here enrollment is 1 day and the spec fixes maturity at 120 days, so 121.
- Peeking: 0.2275 at seed 0 (0.225 and 0.2425 at seeds 1 and 2) against the prototype's 26%. The gap, 0.0325, is inside 2x the spread (0.035), in the same direction. Fixed horizon: 0.045 against the prototype's 4%, a gap of 0.005, inside 2x its spread (0.02). Both peeking estimates, this build's seeds and the prototype's, are consistent with the 20-look theory value of about 0.25: one seed's 400-run estimate has a standard error of about 0.02 there. The fixed-horizon rates are consistent with alpha 0.05: at 400 runs their standard error is about 0.011.
</details>
