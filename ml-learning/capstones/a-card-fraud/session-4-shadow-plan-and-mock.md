# A4. Shadow plan and mock: a matched decline rate, swap sets, an exploration slice, then 45 minutes on the ladder

> Goal: after this I can replay a test year through a champion and a challenger at a matched 0.5% decline rate, count the swap sets, size an approve-exploration slice by its interval width and its fraud dollars per 30 days, and answer the 8-probe payments-risk ladder in 45 minutes, graded on 6 criteria. (No result values anywhere in this file. Capstones have no reference run and no answers file: your run is the answer.)

**Capstone:** [A, card-fraud model, end to end](README.md), session 4 of 4, labkit id 44. **Level:** B (see `ml-learning/CLAUDE.md`). **Output style:** Explanatory
**Builds on:** labs 23 (the exploration slice and its interval widths), 24 (matched decline rates and swap sets), 25 (label maturity sets the experiment clock) and 26 (PSI, population stability index), plus sessions A1 to A3
**Dataset:** the test-year scores A1 and A2 saved in `~/ml-data/capstones/a/` (synthetic)
**Runs on:** cpu. **Lane:** light. **Compute:** no reference run; 1 measured run (the replay), capped at 6 min. Precomputed steps: none
**Needs:** base install only
**Before the session:** write the replay design in section 3 (at the end of A3, or the day before), let the AI write `scripts/a4_shadow_replay.py` from it, annotate it, and run `--smoke` only. Have your lab 23 Record table open: its interval widths at the 0.1%, 1% and 5% slices.
**Interview question:** How do you prove a new fraud model is better before it declines a real customer, and how do you learn anything about the payments you declined?
**Repo link:** [`hld/payments-risk-decisioning/README.md`, What interviewers probe (the ladder)](../../../hld/payments-risk-decisioning/README.md#what-interviewers-probe-the-ladder); [`deep-dives/model-lifecycle-shadow-and-labels.md`, §3 Two exploration slices, because 3DS biases one](../../../hld/payments-risk-decisioning/deep-dives/model-lifecycle-shadow-and-labels.md#3-two-exploration-slices-because-3ds-biases-one); [same file, §5 Proving a model before it declines anyone](../../../hld/payments-risk-decisioning/deep-dives/model-lifecycle-shadow-and-labels.md#5-proving-a-model-before-it-declines-anyone)
**Captured by the script:** P1 to P3 and every replay row. **Human steps:** the replay design, the plan, the mock and the self-grade
**Status:** todo

This session runs its own clock: predict 0:00, replay 0:04, plan 0:09, mock 0:13 to 0:58, close 0:58. The self-grade is a separate 25-minute block within 24 hours.

## 0. Framing (inside the predict block, no AI)

Reread your framing line. This session fills its online metric and guardrail with a rollout plan: shadow, then canary.

## 1. Predict (0:00, 4 min, no AI)

Write each row here and in `../../prediction-log.md` (Lab `A4`) before the replay runs.

| Step | Question | Kind | Prediction | 80% range or confidence |
|---|---|---|---|---|
| P1 | Champion = A1's LightGBM, challenger = A2's as-of LightGBM, each declining its own top 0.5% of test-year scores: swap-ins (payments the challenger declines and the champion approves) as a percent of the challenger's declines | num | | |
| P2 | The fraud precision of those swap-ins on true labels, which stand in for the analysts' daily review of the disagreement set, as a percent | num | | |
| P3 | A random 1% of the champion's would-be declines approved instead (an approve-exploration slice, seed 0): the fraud dollars it lets through per 30 days of the test year | num | | |

Terms:

- **Matched decline rate.** Each model's threshold is its own 99.5th percentile of test-year scores, so both decline 0.5%. Scores are never compared across the two models: their scales differ.
- **Swap sets.** By row id: overlap (both decline), swap-in (the challenger only), swap-out (the champion only).
- **Fraud precision.** Frauds over payments in a set, on true labels.
- **Exploration slices.** A Bernoulli draw with probability eps among the champion's would-be declines, eps = 0.1%, 1% and 5%, seed 0, with the propensity logged. P3 is the 1% slice. Per 30 days = the test-year total x 30 / the days in the test year.
- **IPW interval width.** Lab 23's method on this data: the challenger's recall estimated with inverse propensity weighting (IPW, weight 1 / eps on each revealed row) over 200 random reveals per eps. The width is the 2.5th to 97.5th spread, in points.

## 2. Setup (before the session)

```
$ source ~/.venvs/ml/bin/activate
$ cd ml-learning/capstones/a-card-fraud
$ python scripts/a4_shadow_replay.py --download
$ python scripts/a4_shadow_replay.py --smoke
```

`--download` only checks that both saved score files exist and cover the same row ids, and prints their paths.

## 3. Shadow replay (0:04, 5 min)

Why: a shadow is judged at the champion's decline rate, not at its threshold, and the decisions that change are the swap sets.

The replay design, written before the session, no AI. This is the prompt the AI built the script from:

1. What is replayed (the test year, both saved score files, joined by row id), and what counts as the champion path.
2. The matched rate, the swap sets, the slices and their seed.
3. The RESULT contract: every name in the Record table, with `labkit.start(lab=44)`.

```
$ python scripts/a4_shadow_replay.py --baseline
(paste your RESULT lines)
```

Prediction vs actual, one sentence for each of P1 to P3. There is no reference run.

## 4. The plan in numbers (0:09, 4 min, no AI)

Write in `design-doc.md`, in note form:

- **Slice size.** Set this replay's IPW widths beside your lab 23 widths at the same eps. A width shrinks with the square root of the frauds a slice labels. Pick the smallest eps whose width you would act on. Its fraud dollars per 30 days become the monthly dollar cap that risk policy sets for the slice (§3 of the lifecycle deep dive).
- **Monitoring.** 3 to 5 signals as `signal | threshold | window | who it pages`, drawn from labs 21 and 26 and the leading indicators in [`solution.md` §5.5](../../../hld/payments-risk-decisioning/solution.md#55-labels-arrive-60-to-90-days-later-how-do-you-train-and-how-do-you-know-a-new-model-is-better-before-it-declines-real-customers-loss-budget-the-model).

## 5. Mock (0:13, 45 min, timed, closed book, no AI)

- Open only the [ladder](../../../hld/payments-risk-decisioning/README.md#what-interviewers-probe-the-ladder): the 8 probes. Close every other file and the AI chat. Start a 45-minute timer.
- Write `hld/payments-risk-decisioning/my-attempt.md`. It is the file [`hld/CLAUDE.md`](../../../hld/CLAUDE.md#6-workflow-for-a-new-problem) §6 step 2 reserves for a timed attempt; problem 52's row in `hld/README.md` lists it as missing.
- First 5 minutes: the one-line answer and your framing line. Then about 5 minutes per probe, with numbers from your runs (marked synthetic) and from memory. Note the minute each probe starts.
- Stop at 45 minutes, mid-sentence if need be.

## 6. Self-grade (within 24 hours, 25 min)

1. **No AI, 10 min.** Under the attempt, grade it on the six criteria of root [`CLAUDE.md`](../../../CLAUDE.md#7-staff-level-bar-calibrate-answers-to-this) §7, one row each: `| Criterion | Where in my answer | hit, partial or miss |`. The six: the simplest design and what it refused to build; failure modes and blast radius; migration with zero downtime and a rollback; operability (what pages at 3 am, the SLO, service level objective); cost in dollars and engineer-time, plus team boundaries; the trade-off made explicit. Name the weakest.
2. **With the AI, 5 min.** Ask it to critique the attempt against the same six. By the rules in [`hld/CLAUDE.md`](../../../hld/CLAUDE.md#7-rules-for-ai-when-working-in-this-folder) §7 it grades against the six Staff criteria, says which you missed and critiques before agreeing. It names the gaps and never rewrites your answer ([`../../CLAUDE.md`](../../CLAUDE.md#6-hints-and-critique) §6). The hld section makes it update problem 52's row in `hld/README.md`, because a file was added.
3. **No AI, 10 min.** Finish `design-doc.md`: §7 Serving, §9 A/B testing (shadow, canary, the slice) and §10 Monitoring. Then write the 5 soundbites, each with the section of [`hld/payments-risk-decisioning/`](../../../hld/payments-risk-decisioning/README.md) it was checked against.

## 7. What I learned

Five sentences on what the mock exposed, edited after the AI's critique.

## 8. Interview soundbite (the card written at 0:58)

> One or two sentences only someone who ran this would say.

Framing: decision ___ | prediction time ___ | label and its maturity ___ | offline metric ___ | online metric ___ | guardrail ___

Staff follow-up (migration): how do you move from the champion to the challenger with no surprise declines and a rollback in under a minute? Answer in 2 sentences from the repo link (§5), then [§6 Rolling a model back](../../../hld/payments-risk-decisioning/deep-dives/model-lifecycle-shadow-and-labels.md#6-rolling-a-model-back).

## 9. Close (0:58, 2 min)

The AI drafts card `A4-D` (a symptom and the first check) from your replay. Edit or replace it. The question goes to `../../quiz-bank.md`, the key to `../../answers/quiz-key.md`, citing your RESULT line. Set Status here and in the [README](README.md#sessions). Capstone A is done when `design-doc.md`, its 5 soundbites and the graded `my-attempt.md` all exist.

## Record

Suggested names: if your RESULT contract renames them, edit this table first. Paste, do not type.

| Metric | Your run | Hardware (the script's HW line) | Captured by (script or learner) |
|---|---|---|---|
| `baseline.champion_threshold` and `baseline.challenger_threshold` (each model's 99.5th percentile score) | | | script |
| `baseline.overlap`, `baseline.swap_in` and `baseline.swap_out` (payments) | | | script |
| `P1.swap_in_share` (percent of the challenger's declines) | | | script |
| `P2.swap_in_precision` (percent) | | | script |
| `baseline.swap_out_precision` (percent) | | | script |
| `baseline.declined_frauds_30d` (frauds in the champion's declines per 30 days) | | | script |
| `P3.slice_fraud_dollars_30d` (the 1% slice) | | | script |
| `baseline.slice_fraud_dollars_30d_0p1` and `baseline.slice_fraud_dollars_30d_5` | | | script |
| `baseline.ipw_width_0p1`, `baseline.ipw_width_1` and `baseline.ipw_width_5` (points) | | | script |
| Your lab 23 widths at the same slices | | | learner |
| Mock: probes answered in 45 minutes, and the minute each started | | | learner |
| Self-grade: hits of 6, and the weakest criterion | | | learner |
