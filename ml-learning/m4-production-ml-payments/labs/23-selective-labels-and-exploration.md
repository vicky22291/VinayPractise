# 23. Counterfactual evaluation: declined payments never get a label

> Goal: after this I can estimate a challenger's recall under a champion's declines three ways (approved-only, inverse propensity weighting or IPW with an exploration slice, ground truth) and size the slice by its interval width and its fraud dollars. (No result values anywhere in this file.)

**Level:** S (see `ml-learning/CLAUDE.md`). **Output style:** Explanatory
**Concept link:** [`../README.md#selective-labels-and-exploration`](../README.md#selective-labels-and-exploration) (read after the lab)
**Borrowed from:** Stripe docs, [Radar risk evaluation](https://docs.stripe.com/radar/risk-evaluation) ("For a small subset of payments, Stripe modifies the reported risk score so we can measure the performance of our models"); Michael Manapat (Stripe), "Counterfactual evaluation of machine learning models", PyData Seattle 2015; Bottou et al. 2013, "Counterfactual Reasoning and Learning Systems" ([arXiv 1209.2355](https://arxiv.org/abs/1209.2355)); Dudík, Langford and Li 2011, "Doubly Robust Policy Evaluation and Learning" ([arXiv 1103.4601](https://arxiv.org/abs/1103.4601)); Lakkaraju et al. 2017, "The Selective Labels Problem" (KDD). Do it after the lab, as the second contact 1 to 3 days later.
**Dataset:** the generated payments stream, synthetic, seed 0, shared with labs 19 and 21 ([what it simulates](../README.md#the-generated-payments-stream)): 1,795,646 synthetic payments by 5,000 customers at 10,000 terminals over 183 days from 2018-04-01, 30.3 MB of parquet in `~/ml-data/paystream/v1/`, written on this Mac by `scripts/paystream.py` (no URL and no licence: the script draws it from the Fraud Detection Handbook's published parameters). Era A is days 0 to 90: no model, every payment approved. Era B is days 91 to 182: the champion declines its top 1% each day
**Runs on:** cpu. **Lane:** light. **Compute:** 3 runs x 2 min at most: `--baseline` 1 min, `--change` 1 min, `--break` 2 min (measured at seed 0 while other jobs shared the CPU), at most 6 min per run. Precomputed steps: none
**Needs:** base install only
**Before the session** (from the module folder, see section 2): `python scripts/23_selective_labels_and_exploration.py --download` (writes the synthetic stream to `~/ml-data/paystream/v1/` once, in seconds, no network; shared with labs 19 and 21), then `--smoke`.
**Interview question:** Declined payments never get a label: how do you know your declines are right, and how do you train the next model without learning your own blind spot?
**Repo link:** [`hld/payments-risk-decisioning/deep-dives/model-lifecycle-shadow-and-labels.md`, §3 Two exploration slices, because 3DS (3-D Secure) biases one](../../../hld/payments-risk-decisioning/deep-dives/model-lifecycle-shadow-and-labels.md#3-two-exploration-slices-because-3ds-biases-one); [`hld/payments-risk-decisioning/solution.md`, §5.5 "Labels arrive 60 to 90 days later"](../../../hld/payments-risk-decisioning/solution.md#55-labels-arrive-60-to-90-days-later-how-do-you-train-and-how-do-you-know-a-new-model-is-better-before-it-declines-real-customers-loss-budget-the-model); [`hld/payments-risk-decisioning/edge-cases.md`, "the exploration slice uses 3DS, which changes the outcome"](../../../hld/payments-risk-decisioning/edge-cases.md#edge-case-the-exploration-slice-uses-3ds-which-changes-the-outcome)
**Captured by the script:** P1 to P3 and every Record row. **Human steps:** none (you write the harness prompt in section 3 and `ipw_recall()` in section 4)
**Status:** todo

## 0. Retrieval (0:00, 5 min, closed book, no AI)

The AI asks up to three due cards from `../../quiz-bank.md`, one at a time. Do not open the bank first.

## 1. Predict (0:05, 7 min, no AI)

Level S: read `scripts/23_selective_labels_and_exploration.py` for 2 minutes first. `load_data()`, `known_terminal_frauds()` and `report()` (the RESULT contract your harness feeds) are given.

Write each row here before anything runs; the AI copies it into `../../prediction-log.md` word for word. A row that asks for several numbers becomes one log row per number, each with its own range. Give recalls as fractions (0.5 is 50%), and gaps and widths in points (1 point is 0.01 of recall).

| Step | Question | Kind | Prediction | 80% range or confidence |
|---|---|---|---|---|
| P1 | The challenger, `LGBMClassifier(n_estimators=300, random_state=0)` on the 10 `CHALLENGER` inputs, trained on era A, declines its top 1% of each era B day. Measured only on the frauds the champion approved, is its recall higher or lower than its true recall over every era B fraud, and by how many points? | dir | | |
| P2 | Approve a random, logged 1% of the champion's would-be declines (propensity 0.01, so each explored row weighs 100; draws from `numpy.random.default_rng(0)`). The width of the 95% interval of the challenger's IPW recall, from 200 bootstrap resamples of the era B rows, in points | num | | |
| P3 | Retrain the challenger (300 trees, `random_state` 0) on era B days 91 to 150 twice: once with the champion's declined rows dropped (shortcut a), once on the approvals plus the same 1% slice weighted by 100. True recall of each on days 151 to 182 at a 1% daily decline rate: shortcut a minus weighted, direction and size in points | dir | | |

Terms, fixed so your numbers compare with the reference:

- **Eras.** Era A is days 0 to 90 (`day < 91`): no model, so every payment is approved and labelled. Era B is days 91 to 182, with the champion live.
- **Inputs.** `CHAMPION`: amount, hour, the customer's payment count over the last 1 and 7 days, and its mean amount over the last 30 days. `CHALLENGER`: amount, hour, the customer's count and mean amount over the last 1, 7 and 30 days, amount over the 30-day mean, and `terminal_frauds_30d`. Every customer input uses only that customer's earlier payments.
- **`terminal_frauds_30d`.** `known_terminal_frauds(tx, labelled)`: the frauds at the payment's terminal in the 30 days before it whose label arrived before it, counting labelled payments only. Labelled means every era A payment plus the champion's era B approvals. The exploration slice's labels are left out of this input, so every slice scores the same challenger.
- **Champion.** `LGBMClassifier(n_estimators=150, random_state=seed, verbose=-1)` on `CHAMPION`, trained on every era A payment with `is_fraud` as the label.
- **Challenger.** `LGBMClassifier(n_estimators=300, random_state=seed, verbose=-1)` on `CHALLENGER`, trained the same way. It runs in shadow on era B: scored and logged, never acted on.
- **Decline rule.** A model declines a payment when its score is at or above `numpy.quantile(scores, 0.99)` over that day's era B scores. Each model has its own daily cut, so each declines about 1% of every day: the matched decline rate.
- **Labels.** An approved payment's label is final (`is_fraud`). The lab treats approved labels as matured, to separate selection from delay; lab 21 covers the delay. A declined payment has no label. The simulator still knows its outcome, and "true" means measured with that outcome.
- **Recall.** The share of frauds the challenger declines. Approved-only: over the era B frauds the champion approved. True: over every era B fraud.
- **Exploration slice.** One uniform draw per era B payment from `numpy.random.default_rng(seed)`, drawn once. A would-be decline whose draw is below ε is approved anyway, and its propensity ε is logged. An ordinary approval has propensity 1. The slices nest: 0.1% sits inside 1%, and 1% inside 5%.
- **IPW recall.** Your `ipw_recall()` computes:

```text
w_i      = 1 / π_i on labelled rows, 0 on the rest     π = 1 for an approval, ε for an explored would-be decline
recall   = sum_i w_i * fraud_i * caught_i  /  sum_i w_i * fraud_i      caught_i = 1 when the challenger declines row i
interval = resample the era B rows with replacement 200 times; the 2.5th and 97.5th percentiles of the 200 recalls
width    = 100 x (hi - lo), in points
```

- **Fresh draws.** `--change` also draws 200 new 1% slices from the same generator and reports the mean and the middle-95% width of their 200 IPW recalls. That is what many exploration logs would show, next to the bootstrap from one log.
- **Fraud dollars.** The total amount of the explored payments that were fraud: what the slice let through.
- **Era B training sets (`--break`).** Each trains `LGBMClassifier(n_estimators=300, random_state=seed)` on `CHALLENGER` over era B days 91 to 150, and is scored on days 151 to 182. Shortcut a drops the champion's declined rows. Shortcut b keeps them, every one labelled fraud. Weighted keeps the approvals and adds the 1% slice with `sample_weight` 100. Oracle trains on every true label, which only a simulator has.
- **Blind recall.** A model's recall over the days 151 to 182 frauds that the champion declines.
- **Gap.** 100 x (first minus second), in points. P1 is approved-only minus true. P3 is shortcut a minus weighted.

## 2. Setup (before the session)

```
$ source ~/.venvs/ml/bin/activate
$ cd m4-production-ml-payments    # from ml-learning/, where sessions start
$ python scripts/23_selective_labels_and_exploration.py --download
$ python scripts/23_selective_labels_and_exploration.py --smoke
```

`--smoke` checks the given plumbing only: `load_data()` and `known_terminal_frauds()` on customers 0 to 499 of the synthetic stream, and `report()` printing every RESULT name. `--baseline`, `--change` and `--break` stop with NotImplementedError until the harness exists.

## 3. Baseline (0:12, 10 min)

Why: a challenger scored only where the champion let labels through is scored on a population the champion already filtered, so first measure what that view does to its recall.

You write first, in this file, no AI (about 4 min). This is the prompt the AI builds from:

1. The split: which days train the champion and the challenger, which days they decide, and which days `--break` trains and tests on.
2. The exploration policy: the slice sizes, how one payment gets explored, and what is logged for every payment (the decision, explored or not, the propensity).
3. The metric: recall at the matched 1% decline rate, approved-only and true, and how IPW recall weighs each labelled row.
4. The RESULT contract: for every name in `CONTRACT`, the model, the rows and the formula behind it.

The AI then writes the harness for all three modes from your prompt, with `--smoke` running all three on customers 0 to 499. Annotate each AI block with one line before the first run.

```
$ python scripts/23_selective_labels_and_exploration.py --baseline
(paste your RESULT lines)
```

Prediction vs actual, one sentence. The reference run is in `../../answers/`; the AI opens it only after your P1 row exists and you have pasted your own RESULT lines.

## 4. Change one thing (0:22, 10 min)

Change: approve a random, logged 1% of the champion's would-be declines (propensity 0.01) and estimate the challenger's recall with inverse propensity weights. P2 is logged above.

Before the run, write `ipw_recall()` in the script yourself, no AI, from the IPW formula in the Terms above. `--change` also sizes the slice at 0.1% and 5%, counts each slice's explored payments, frauds and fraud dollars, and draws 200 fresh 1% slices.

```
$ python scripts/23_selective_labels_and_exploration.py --change
(paste your RESULT lines)
```

## 5. Break it (0:32, 10 min, AI gives hints only; the run finishes by 0:40)

Break: retrain the challenger on era B days 91 to 150 with two reject-inference shortcuts, (a) drop the declined rows and (b) label every declined row as fraud, next to a model trained on the approvals plus the weighted 1% slice and an oracle trained on every true label. P3 is logged above.

```
$ python scripts/23_selective_labels_and_exploration.py --break
(paste your RESULT lines)
```

Why, in three sentences, written without AI:

## 6. Explain-back (0:42, 5 min) and rebuild (0:47, 10 min), no AI

- Five sentences for a smart engineer new to ML, written without AI. The AI names your weakest claim after the session (section 7).
- Rebuild: open `rebuild/23_ipw_recall.py`, write `ipw_recall()` from memory, then run `python rebuild/23_ipw_recall.py`. Its `check()` compares with `numpy.average` and scikit-learn's `recall_score` under the same weights on a toy, and checks that the mean over 200 random 1% reveals sits within 2 standard errors of the toy's true recall, never with this lab's results.

## 7. What I learned

After the session (about 5 minutes): the AI names the weakest claim in your five sentences and asks one question that tests it. Edit the sentences here.

## 8. Interview soundbite (one of the three cards written at 0:57)

> One or two sentences only someone who ran this would say.

Framing: decision ___ | prediction time ___ | label and its maturity ___ | offline metric ___ | online metric ___ | guardrail ___

Staff follow-up (cost): risk policy caps the approve slice with a monthly dollar budget. How do you size the slice for a launch decision, and who signs the fraud losses it lets through? Answer in 2 sentences from the repo link (§3, then solution §5.5). Rotate: simplest design, failure modes, migration, what pages at 3 am, cost, trade-off.

## 9. Quiz cards (0:57, 3 min)

The AI drafts three cards (M, N, and T or D). Edit or replace them. Questions go to `../../quiz-bank.md`, keys to `../../answers/quiz-key.md`.

## Record

The script prints these as RESULT lines. Paste, do not type.

| Metric | Your run | Hardware (the script's HW line) | Captured by (script or learner) |
|---|---|---|---|
| `P1.recall_approved_only` (challenger, over the era B frauds the champion approved) | | | script |
| `P1.recall_true` (challenger, over every era B fraud) | | | script |
| `P1.gap_points` (approved-only minus true, points) | | | script |
| `baseline.champion_decline_rate` (share of era B payments the champion declines) | | | script |
| `baseline.challenger_decline_rate` (share of era B payments the challenger would decline) | | | script |
| `baseline.frauds` (era B frauds) | | | script |
| `baseline.frauds_declined` (era B frauds the champion declined, so never labelled) | | | script |
| `baseline.hidden_share` (the champion's caught frauds as a share of every era B fraud: what the approved-only view hides) | | | script |
| `baseline.catches_hidden_share` (share of the challenger's true catches that sit among the champion's declines) | | | script |
| `P2.ci_width` (1% slice: width of the 95% bootstrap interval of the IPW recall, points) | | | script |
| `change.ipw_recall_1pct` (IPW recall from the 1% slice) | | | script |
| `change.ci_lo_1pct` (its interval, low end) | | | script |
| `change.ci_hi_1pct` (its interval, high end) | | | script |
| `change.draws_mean_1pct` (mean IPW recall over 200 fresh 1% slices) | | | script |
| `change.draws_width_1pct` (middle-95% width of those 200 recalls, points) | | | script |
| `change.ci_width_0p1pct` (0.1% slice: bootstrap interval width, points) | | | script |
| `change.ci_width_5pct` (5% slice: bootstrap interval width, points) | | | script |
| `change.explored_0p1pct` (payments the 0.1% slice approved, era B) | | | script |
| `change.explored_frauds_0p1pct` (frauds among them) | | | script |
| `change.fraud_dollars_0p1pct` (their total amount, dollars) | | | script |
| `change.explored_1pct` (payments the 1% slice approved, era B) | | | script |
| `change.explored_frauds_1pct` (frauds among them) | | | script |
| `change.fraud_dollars_1pct` (their total amount, dollars) | | | script |
| `change.explored_5pct` (payments the 5% slice approved, era B) | | | script |
| `change.explored_frauds_5pct` (frauds among them) | | | script |
| `change.fraud_dollars_5pct` (their total amount, dollars) | | | script |
| `P3.recall_drop` (shortcut a, declined rows dropped: true recall, days 151 to 182) | | | script |
| `P3.recall_weighted` (approvals plus the 1% slice weighted by 100: true recall, days 151 to 182) | | | script |
| `P3.gap_points` (shortcut a minus weighted, points) | | | script |
| `break.recall_as_fraud` (shortcut b, every declined row labelled fraud: true recall, days 151 to 182) | | | script |
| `break.recall_oracle` (every true label: true recall, days 151 to 182) | | | script |
| `break.explored_train` (1% slice payments in the training days 91 to 150) | | | script |
| `break.explored_train_frauds` (frauds among them) | | | script |
| `break.blind_frauds` (days 151 to 182 frauds the champion declines) | | | script |
| `break.blind_recall_drop` (shortcut a, recall over those frauds) | | | script |
| `break.blind_recall_as_fraud` (shortcut b, recall over those frauds) | | | script |
| `break.blind_recall_weighted` (weighted 1% slice, recall over those frauds) | | | script |
| `break.blind_recall_oracle` (oracle, recall over those frauds) | | | script |
