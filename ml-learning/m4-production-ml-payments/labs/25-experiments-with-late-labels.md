# 25. A/B power, peeking and label maturity

> Goal: after this I can size a fraud-model A/B test (a randomized experiment with two arms) in payments per arm and in calendar days. I can also measure the false-positive rate of 400 A/A tests checked every day for 20 days. An A/A test gives both arms the same model, so every significant result is a false positive. (No result values anywhere in this file.)

**Level:** B (see `ml-learning/CLAUDE.md`). **Output style:** Explanatory
**Concept link:** [`../README.md#experiments-when-labels-arrive-late`](../README.md#experiments-when-labels-arrive-late) (read after the lab)
**Borrowed from:** the statsmodels [`NormalIndPower` docs](https://www.statsmodels.org/stable/generated/statsmodels.stats.power.NormalIndPower.html); Johari, Pekelis and Walsh 2015, "Always Valid Inference: Bringing Sequential Analysis to A/B Testing" ([arXiv 1512.04922](https://arxiv.org/abs/1512.04922)). Do it after the lab, as the second contact 1 to 3 days later.
**Dataset:** synthetic, no download: closed-form sample sizes plus a seeded numpy simulation (400 A/A runs x 20 daily looks x 2 arms of binomial draws, seed 0), 0 MB on disk, no URL, no licence (the script draws it)
**Runs on:** cpu. **Lane:** light. **Compute:** 3 runs x 1 min, at most 6 min per run. Precomputed steps: none
**Needs:** `python -m pip install statsmodels==0.15.0`
**Before the session** (from the module folder, see section 2): `python -m pip install statsmodels==0.15.0`. Nothing to download. There is no script yet. In section 3 you start `scripts/25_experiments_with_late_labels.py` with `n_per_arm()`, the AI extends it from your design, and `--smoke` runs then.
**Interview question:** Fraud is 0.1% and labels mature in 120 days: how long does a model experiment run, and what decides the launch in the meantime?
**Repo link:** [`hld/payments-risk-decisioning/deep-dives/model-lifecycle-shadow-and-labels.md`, §5 Proving a model before it declines anyone](../../../hld/payments-risk-decisioning/deep-dives/model-lifecycle-shadow-and-labels.md#5-proving-a-model-before-it-declines-anyone); [`hld/feature-flag-service/deep-dives/evaluation-and-bucketing.md`, §3 Measured: sticky, monotonic, independent, uniform](../../../hld/feature-flag-service/deep-dives/evaluation-and-bucketing.md#3-measured-sticky-monotonic-independent-uniform)
**Captured by the script:** P1 to P3 and every Record row. **Human steps:** none (you write the experiment design, `n_per_arm()` and `aa_false_positive_rates()`)
**Status:** todo

## 0. Retrieval (0:00, 5 min, closed book, no AI)

The AI asks up to three due cards from `../../quiz-bank.md`, one at a time. Do not open the bank first.

## 1. Predict (0:05, 7 min, no AI)

Level B: there is no script to read. Predict before you open section 3, which holds the sample-size formula.

Write each row here before anything runs; the AI copies it into `../../prediction-log.md` word for word. A row that asks for several numbers becomes one log row per number, each with its own range.

| Step | Question | Kind | Prediction | 80% range or confidence |
|---|---|---|---|---|
| P1 | Users per arm to detect a 5% relative lift on a 2% base rate (2.0% to 2.1%): two-sided pooled two-proportion z-test, alpha 0.05, power 80%, two equal arms, rounded up to a whole user | num | | |
| P2 | The outcome becomes fraud: a 0.1% base rate and a 10% relative drop (0.1% to 0.09%), one payment per unit, the same test, alpha and power, 1.5 M payments per arm per day, each label final 120 days after its payment: calendar days to a decision (enrollment days plus 120) | num | | |
| P3 | 400 A/A runs (both arms at 2%, each arm getting the P1 users per arm / 20 users a day), the z-test after every day for 20 days, stop at the first p below 0.05, seed 0: false-positive rate, as the share of the 400 runs that stop | num | | |

Terms, fixed so your numbers compare with the reference:

- **Test.** Two-sided pooled two-proportion z-test, alpha 0.05, power 80%, two equal arms. Sample sizes are rounded up to a whole unit.
- **Unit.** Every sample size counts units per arm, and the formula treats the units as independent. In P1, the A/A runs and the sample-ratio check, a unit is a user. In the fraud case and the guardrail, a unit is one payment, assigned to an arm by its payment id. So 1.5 M payments per arm per day is 1.5 M units per arm per day.
- **Enrollment days.** Payments per arm / 1,500,000 payments per arm per day, rounded up to whole days.
- **Calendar days.** Enrollment days plus 120: the label of the last enrolled payment is final 120 days after it.
- **Guardrail.** The approval rate moving from 95% to 94.5%, one payment per unit, under the same test, alpha and power. Approval is known at decision time, so it has no maturity wait. The script reports how long its traffic takes at the full 1.5 M payments per arm per day, in days, not rounded. The time scales with 1 / the arm's daily traffic, so a canary arm that gets 5% of 1.5 M payments a day takes 20 times as long.
- **A/A run.** Both arms convert at 2%. Each arm gets ceil(P1 users per arm / 20) users a day. After each day, one z-test on the cumulative counts. Fixed horizon: only the test after day 20 counts. Peeking: the run stops at the first look with p below 0.05. A run that stops, or that is significant at its one look, is a false positive.
- **Sample-ratio check.** 2 x the P1 users per arm, each assigned to treatment with probability 50.5% (one binomial draw), then a chi-square goodness-of-fit test against 50/50 (`scipy.stats.chisquare`), flagged when p is below 0.001.
- **Seed.** `np.random.default_rng(seed)` draws the A/A counts and the assignment. Seed 0 is the default.

## 2. Setup (before the session)

```
$ source ~/.venvs/ml/bin/activate
$ python -m pip install statsmodels==0.15.0
$ cd m4-production-ml-payments    # from ml-learning/, where sessions start
```

Level B ships no script, and the data is synthetic, so nothing else happens before the session. Once the script exists (you start it in section 3, and the AI extends it):

```
$ python scripts/25_experiments_with_late_labels.py --download
$ python scripts/25_experiments_with_late_labels.py --smoke
```

`--download` only prints that nothing is fetched. `--smoke` runs the baseline and change paths in seconds and prints `SMOKE <name> ok` lines, never values. Once you fill in `aa_false_positive_rates()` in section 5, it adds the break path on tiny inputs (5 looks, 20 A/A runs).

## 3. Baseline (0:12, 10 min)

Why: the users per arm follow from four numbers fixed before launch: the base rate, the smallest lift worth detecting, alpha and power.

You write first, in this file, no AI (about 5 min). This is the prompt the AI builds from:

1. The experiment design for all three steps: what varies, what is fixed, the repeats and the stop rule. Write it, then check it against the Terms. Add one line each for the choices the Terms leave open:
   - The unit you would randomize on in a real fraud test, and what it does to the Terms' rule that units are independent.
   - How the harness marks a run as stopped once one look has p below 0.05.
   - The standard error of a false-positive rate estimated from 400 runs, near your P3 prediction.
   - One Terms choice you would change for a real launch, and why.
2. The RESULT contract: every name in the Record table, the mode that prints it, and its unit. Each mode prints only its own rows.

Then write `n_per_arm(p1, rel_lift, alpha=0.05, power=0.80)` yourself (about 2 min), from the formula below. Put it in a new file, `scripts/25_experiments_with_late_labels.py`, which the AI then extends.

<details><summary>The formula: open at 0:12, after P1 to P3 are logged</summary>

```
p2    = p1 * (1 + rel_lift)                     a drop has a negative rel_lift
p_bar = (p1 + p2) / 2
z_a   = NormalDist().inv_cdf(1 - alpha / 2)     NormalDist from the statistics module
z_b   = NormalDist().inv_cdf(power)
n     = ceil((z_a * sqrt(2 * p_bar * (1 - p_bar)) + z_b * sqrt(p1 * (1 - p1) + p2 * (1 - p2)))^2 / (p2 - p1)^2)
```

</details>

The AI then extends the file from your prompt. It writes the three modes, the statsmodels cross-check (`NormalIndPower().solve_power` on Cohen's h from `proportion_effectsize`), the sample-ratio check and the plot. It leaves `aa_false_positive_rates()` as a stub for section 5, and until then `--smoke` skips the break path. Annotate the baseline blocks with one line each before the first run.

```
$ python scripts/25_experiments_with_late_labels.py --smoke
$ python scripts/25_experiments_with_late_labels.py --baseline
(paste your RESULT lines)
```

Prediction vs actual, one sentence. The reference run is in `../../answers/`; the AI opens it only after your P1 row exists and you have pasted your own RESULT lines.

## 4. Change one thing (0:22, 10 min)

Change: label maturity, from a label known at once to a label final 120 days after its payment. Calendar days = enrollment days plus 120. P2 is logged above.

The setting, not the knob: the run moves to the fraud test in the P2 row (a 0.1% base rate, a 10% relative drop, one payment per unit, 1.5 M payments per arm per day) and sizes it with your `n_per_arm()`. Its payments per arm are a new sizing, not a contrast with P1, because the base rate and the relative change both move. The controlled contrast sits inside this run, at the same payments per arm and the same traffic: `change.enrollment_days` is the decision day if each label were known at once, and `P2.calendar_days` waits for maturity. The same run sizes the approval-rate guardrail (95% to 94.5%) at the same traffic.

Why: a fraud model is judged on a label that arrives months after the payment, so the clock to a decision has two parts, enrollment and label maturity.

Before the run, annotate the AI's change and break blocks with one line each.

```
$ python scripts/25_experiments_with_late_labels.py --change
(paste your RESULT lines)
```

## 5. Break it (0:32, 10 min, AI gives hints only; the run finishes by 0:40)

Break: peek daily for 20 days in 400 A/A runs and stop at the first p below 0.05. P3 is logged above.

Why: experiment dashboards refresh every day, and teams stop a test the first time it shows p below 0.05.

You write first, no AI (about 5 min): the body of `aa_false_positive_rates(p, users_per_day, days, n_sims, seed)`. Draw every count at once with `rng.binomial(users_per_day, p, size=(n_sims, days, 2))`, where `rng = np.random.default_rng(seed)`. Take cumulative sums over the days, and run the pooled z-test at every look. Return `(fixed, peeking)`: the share of runs with p below 0.05 at the last look, and the share with p below 0.05 at any look. The AI's plot code redraws the same counts and works out, per look, the share of runs already stopped. `--break` also writes `~/ml-data/results/lab25/peeking-seed0.png`.

```
$ python scripts/25_experiments_with_late_labels.py --break
(paste your RESULT lines)
```

Why, in three sentences, written without AI:

## 6. Explain-back (0:42, 5 min) and rebuild (0:47, 10 min), no AI

- Five sentences for a smart engineer new to ML, written without AI. The AI names your weakest claim after the session (section 7).
- Rebuild: open `rebuild/25_power_and_peeking.py`, write `n_per_arm()` and `aa_false_positive_rates()` from memory, then run `python rebuild/25_power_and_peeking.py`. Its `check()` compares with statsmodels (`NormalIndPower` on Cohen's h within 0.5%, and `proportions_ztest` look by look on the same draws), never with this lab's results.

## 7. What I learned

After the session (about 5 minutes): the AI names the weakest claim in your five sentences and asks one question that tests it. Edit the sentences here.

## 8. Interview soundbite (one of the three cards written at 0:57)

> One or two sentences only someone who ran this would say.

Framing line, yours to fill: decision | prediction time | label and its maturity | offline metric | online metric | guardrail.

Staff follow-up (failure modes): the approval-rate canary passes. Months later the matured labels show that the challenger let a new fraud pattern through. Which gate in §5 of the lifecycle deep dive should have caught it first? §5 splits the canary by payment-id hash, so which unit fits a 120-day fraud read, and what does §3 of the bucketing deep dive say keeps a unit in its arm? Answer in 2 sentences from the repo links. Rotate: simplest design, failure modes, migration, what pages at 3 am, cost, trade-off.

## 9. Quiz cards (0:57, 3 min)

The AI drafts three cards (M, N, and T or D). Edit or replace them. Questions go to `../../quiz-bank.md`, keys to `../../answers/quiz-key.md`.

## Record

The script prints these as RESULT lines. Paste, do not type.

| Metric | Your run | Hardware (the script's HW line) | Captured by (script or learner) |
|---|---|---|---|
| `P1.n_per_arm` (2% base, 5% relative lift, your formula, users per arm) | | | script |
| `baseline.n_per_arm_cohens_h` (the same case from statsmodels: Cohen's h and `NormalIndPower`, rounded up) | | | script |
| `baseline.srm_p_value` (chi-square p for 2 x P1 users split 50.5/49.5; optional) | | | script |
| `baseline.srm_caught` (true when that p is below 0.001; optional) | | | script |
| `change.n_per_arm` (fraud: 0.1% base, 10% relative drop, payments per arm) | | | script |
| `change.n_per_arm_cohens_h` (the same case from statsmodels, payments per arm) | | | script |
| `change.enrollment_days` (payments per arm at 1.5 M payments per arm per day, rounded up) | | | script |
| `P2.calendar_days` (enrollment days plus 120) | | | script |
| `change.guardrail_n_per_arm` (approval rate 95% to 94.5%, payments per arm) | | | script |
| `change.guardrail_n_per_arm_cohens_h` (the same case from statsmodels, payments per arm) | | | script |
| `change.guardrail_days` (the time to collect the guardrail's payments per arm at 1.5 M payments per arm per day, in days, not rounded) | | | script |
| `break.fpr_fixed` (400 A/A runs, one test after day 20) | | | script |
| `P3.fpr_peeking` (the same 400 runs, stop at the first p below 0.05) | | | script |
