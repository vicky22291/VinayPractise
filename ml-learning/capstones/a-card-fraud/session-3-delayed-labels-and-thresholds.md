# A3. Delayed labels and thresholds: mature only, mature plus proxy, and a price on every decline

> Goal: after this I can simulate dispute delays of 7 to 120 days with a proxy flag, compare mature-only and mature-plus-proxy training on true labels at a 0.5% decline rate, and score amount-aware thresholds in net dollars against one flat threshold. (No result values anywhere in this file. Capstones have no reference run and no answers file: your run is the answer.)

**Capstone:** [A, card-fraud model, end to end](README.md), session 3 of 4, labkit id 43. **Level:** B (see `ml-learning/CLAUDE.md`). **Output style:** Explanatory
**Builds on:** labs 21 (delayed labels) and 22 (calibration and amount-aware thresholds), plus your A2 features
**Dataset:** the A1 sample with A2's features (synthetic). The dispute delays and the proxy flag are simulated here, so they are synthetic too. On the fallback, paystream ships both: use lab 21's calendar, as the README's [fallback section](README.md#fallback-the-paystream-generator-synthetic) says
**Runs on:** cpu. **Lane:** light. **Compute:** no reference run; 2 measured runs, each capped at 6 min. Precomputed steps: none
**Needs:** base install only
**Before the session:** A2 done, so its features sit in `~/ml-data/capstones/a/`. Nothing to download.
**Interview question:** Disputes land 7 to 120 days late: what do you train on today, and how does one decline threshold treat a $20 payment and a $2,000 one?
**Repo link:** [`hld/payments-risk-decisioning/deep-dives/model-lifecycle-shadow-and-labels.md`, §1 Where labels come from, and when](../../../hld/payments-risk-decisioning/deep-dives/model-lifecycle-shadow-and-labels.md#1-where-labels-come-from-and-when); [same file, §4 Thresholds from cost, and why the inputs must scale](../../../hld/payments-risk-decisioning/deep-dives/model-lifecycle-shadow-and-labels.md#4-thresholds-from-cost-and-why-the-inputs-must-scale)
**Captured by the script:** P1 to P3 and every Record row. **Human steps:** the labelling rules, the calibration decision, the design and the write-up
**Status:** todo

## 0. Framing (0:00, 7 min, no AI)

Reread your framing line in `design-doc.md`. Under it, write one line on what this session changes: the label, its maturity, and the price of each decision.

## 1. Predict (0:07, 5 min, no AI)

Write each row here and in `../../prediction-log.md` (Lab `A3`) before anything runs. Recall is a percent of the test year's frauds; its changes are in points. The 0.5% decline rate is the guardrail from your A1 framing line; if you set another there, rewrite these rows first.

| Step | Question | Kind | Prediction | 80% range or confidence |
|---|---|---|---|---|
| P1 | Trained as of today (the first day of the validation year) on mature labels only: every training payment at least 120 days before today, A2's as-of config. Recall at a 0.5% decline rate on the test year, scored on true labels | num | | |
| P2 | Mature plus proxy: the same, plus the last 120 days before today, each payment labelled fraud when its simulated dispute or its proxy flag arrived by today. Recall at the same 0.5% decline rate on the test year (true labels), minus P1, in points. Up, down or same, plus a size range | dir | | |
| P3 | On the P2 model's scores: decline when p > p\*(a) = C_fd(a) / (C_fd(a) + L(a)), with L(a) = a + $15 and C_fd(a) = 0.13a + $8, against one flat threshold, p\* at the median training Amount. Net dollars on the test year, amount-aware minus flat. Up, down or same, plus a size range in dollars | dir | | |

Terms, fixed so your numbers compare with A2:

- **Today.** The first day of the validation year. Training uses only payments before today, with labels as they are known today.
- **Simulated delays (synthetic, seed 0).** Each fraud's dispute arrives U(7, 120) days after the payment. A proxy flag fires on half of the frauds, plus enough legitimate payments for a precision of 0.4, and arrives U(1, 7) days after the payment. These are paystream's parameters, so TabFormer and the fallback agree.
- **Mature only.** Training payments at least 120 days before today. Every one of their labels has arrived.
- **Mature plus proxy.** Mature only, plus the last 120 days before today, labelled fraud when the dispute or the proxy arrived by today and legitimate otherwise.
- **Oracle (recorded, not predicted).** A2's as-of model, trained with every label final, at the same decline rate.
- **Recall at 0.5%.** Decline the top 0.5% of test-year scores. Recall = declined frauds / all frauds of the test year, on true labels.
- **Calibration.** p\*(a) assumes p is a probability. Compare the P2 model's mean predicted probability with the observed fraud rate on the validation year (true labels), then decide whether to calibrate there with isotonic regression, as the HLD does monthly. Write which you did before the change run.
- **Net dollars.** Against approving everything: each declined fraud saves L(a), each declined legitimate payment costs C_fd(a), with a the payment's Amount. A payment of $0 or less is never declined.
- **Costs.** The repo's estimates, which give p\* of 0.23, 0.14 and 0.12 at $20, $200 and $2,000. Mark them as estimates in the write-up.
- **Intervals.** Each recall and dollar difference gets a 95% interval from 1,000 paired bootstrap resamples of test cards.

## 2. Setup (before the session)

```
$ source ~/.venvs/ml/bin/activate
$ cd ml-learning/capstones/a-card-fraud
$ python scripts/a3_delayed_labels_and_thresholds.py --download
$ python scripts/a3_delayed_labels_and_thresholds.py --smoke
```

`--download` only checks that A1's sample and A2's features exist, and prints their paths.

## 3. Baseline (0:12, 15 min)

Why: a label that has not arrived yet looks exactly like a legitimate payment, so first measure what training on finished labels alone gives.

You write first, in this file, no AI (about 5 min). This is the prompt the AI builds from:

1. The two labelling rules, one sentence each, and what "today" is.
2. The delay and proxy simulation, its seed, and the labels each model is scored on.
3. The RESULT contract: every name in the Record table, the mode that prints it, and its unit.

The AI then writes the script with `labkit.start(lab=43)`. Annotate each AI block with one line before the first run.

```
$ python scripts/a3_delayed_labels_and_thresholds.py --smoke
$ python scripts/a3_delayed_labels_and_thresholds.py --baseline
(paste your RESULT lines)
```

Prediction vs actual, one sentence. There is no reference run: the AI fills Actual and Hit from your pasted lines.

## 4. Change one thing (0:27, 15 min; the run finishes by 0:40)

Change: mature plus proxy replaces mature only. The same run then prices both threshold rules on the new model's scores, after your calibration decision. P2 and P3 are logged above.

Why: the last 120 days hold the newest payments and the fewest finished labels, and the proxy that covers them arrives in 1 to 7 days and is wrong 60% of the time.

```
$ python scripts/a3_delayed_labels_and_thresholds.py --change
(paste your RESULT lines)
```

Prediction vs actual, one sentence each for P2 and P3.

## 5. Write-up (0:42, 15 min, no AI)

- **Explain-back (5 min).** Five sentences for a smart engineer new to ML. Then ask the AI for the weakest claim, not a rewrite.
- **Deliverable (10 min).** Add to `design-doc.md` §3 Labels (the sources, the maturity, the proxy rule, and what the run showed with its interval), §6 Training (the window, today, which labels) and §8 Evaluation (recall at 0.5% on true labels, the two threshold rules in net dollars, the cost estimates). At most 4 lines each.

## 6. What I learned

The five explain-back sentences, edited after the AI's question.

## 7. Interview soundbite (the card written at 0:57)

> One or two sentences only someone who ran this would say.

Framing: decision ___ | prediction time ___ | label and its maturity ___ | offline metric ___ | online metric ___ | guardrail ___

Staff follow-up (trade-off): mature only waits for every label, and mature plus proxy trusts a flag that is wrong 60% of the time. Which do you ship, and what number would change your mind? Answer in 2 sentences from the repo link (§1), then §4 for who signs the cost weights.

## 8. Close (0:57, 3 min)

The AI drafts card `A3-T` (the payments version or a variant you did not run) from your run. Edit or replace it. The question goes to `../../quiz-bank.md`, the key to `../../answers/quiz-key.md`, citing your RESULT line. Set Status here and in the [README](README.md#sessions).

## Record

Suggested names: if your RESULT contract renames them, edit this table first. Paste, do not type.

| Metric | Your run | Hardware (the script's HW line) | Captured by (script or learner) |
|---|---|---|---|
| `baseline.observed_share_30d` (share of the last 30 days' frauds whose dispute arrived by today) | | | script |
| `baseline.oracle_recall` (A2's model, every label final, 0.5% decline rate) | | | script |
| `P1.recall_mature` (percent of test-year frauds) | | | script |
| `baseline.recall_mature_ci95_low` and `baseline.recall_mature_ci95_high` | | | script |
| `baseline.mean_p_valid` and `baseline.fraud_rate_valid` (the calibration check, validation year) | | | script |
| Your calibration decision | | | learner |
| `change.recall_proxy` (percent of test-year frauds) | | | script |
| `P2.recall_change` (mature plus proxy minus mature only, points) | | | script |
| `change.recall_change_ci95_low` and `change.recall_change_ci95_high` | | | script |
| `change.flat_threshold` (p\* at the median training Amount) | | | script |
| `change.net_flat` and `change.net_aware` (dollars, test year) | | | script |
| `P3.net_gain` (amount-aware minus flat, dollars) | | | script |
| `change.net_gain_ci95_low` and `change.net_gain_ci95_high` | | | script |
| `change.decline_rate_flat` and `change.decline_rate_aware` (percent of test-year payments) | | | script |
