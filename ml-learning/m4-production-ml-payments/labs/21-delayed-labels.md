# 21. Delayed labels: mature, proxy or naive, and an attack that started 3 weeks ago

> Goal: after this I can draw a label-maturity curve and compare mature-only, mature-plus-proxy and naive training on the newest cohort, scored on true labels and on a new card-testing attack. (No result values anywhere in this file.)

**Level:** S (see `ml-learning/CLAUDE.md`). **Output style:** Explanatory
**Concept link:** [`../README.md#delayed-labels`](../README.md#delayed-labels) (read after the lab; at step 3 you open only its Key definition block)
**Borrowed from:** Stripe docs, [How disputes work](https://docs.stripe.com/disputes/how-disputes-work) (the 120-day dispute window, and Stripe's note that about 40% of Visa and Mastercard early fraud warnings become fraud disputes); Chip Huyen, *Designing Machine Learning Systems* (O'Reilly, 2022), chapter 4 (natural labels and the length of the feedback loop). Do it after the lab, as the second contact 1 to 3 days later.
**Dataset:** The generated payments stream, synthetic: `scripts/paystream.py` at seed 0, shared with labs 19 and 23. 1,795,646 synthetic payments by 5,000 customers at 10,000 terminals over 183 days from 2018-04-01, with a dispute date and an early proxy flag on its frauds. About 30 MB of parquet in `~/ml-data/paystream/v1/`. No URL: it is generated on this Mac, with no network. Licence: written for this repo; the parameters follow the [Fraud Detection Handbook chapter 3 simulator](https://fraud-detection-handbook.github.io/fraud-detection-handbook/Chapter_3_GettingStarted/SimulatedDataset.html), and none of its GPL-3.0 code is copied
**Runs on:** cpu. **Lane:** light. **Compute:** 3 runs x 1 min, at most 6 min per run. Precomputed steps: none
**Needs:** base install only
**Before the session** (from the module folder, see section 2): `python scripts/21_delayed_labels.py --download` (it writes the synthetic stream with `scripts/paystream.py` once, seed 0, if lab 19 has not already), then `--smoke`.
**Interview question:** Chargebacks land up to 120 days later: what do you train on this month, how do you evaluate last week's model, and how do you still catch an attack that started 10 days ago?
**Repo link:** [`hld/payments-risk-decisioning/deep-dives/model-lifecycle-shadow-and-labels.md`, §1 Where labels come from, and when](../../../hld/payments-risk-decisioning/deep-dives/model-lifecycle-shadow-and-labels.md#1-where-labels-come-from-and-when); [`hld/payments-risk-decisioning/edge-cases.md`, Edge case: labels arrive 60 to 90 days late](../../../hld/payments-risk-decisioning/edge-cases.md#edge-case-labels-arrive-60-to-90-days-late)
**Captured by the script:** P1 to P3 and every Record row, plus the weekly cohort TABLE lines from `--baseline`. **Human steps:** none (you write the harness prompt, `observed_labels()` and `training_sets()` in section 3)
**Status:** todo

## 0. Retrieval (0:00, 5 min, closed book, no AI)

The AI asks up to three due cards from `../../quiz-bank.md`, one at a time. Do not open the bank first.

## 1. Predict (0:05, 7 min, no AI)

Level S: read `scripts/21_delayed_labels.py` for 2 minutes first. `load_data()` (the synthetic stream and its as-of inputs), `report()` (the RESULT contract your harness feeds) and the `MODEL` settings are given.

Write each row here before anything runs; the AI copies it into `../../prediction-log.md` word for word. A row that asks for several numbers becomes one log row per number, each with its own range. Give shares and rates as fractions (0.01 is 1%).

| Step | Question | Kind | Prediction | 80% range or confidence |
|---|---|---|---|---|
| P1 | Dispute delays are uniform on 7 to 120 days. Of the frauds in a cohort that is 30 days old today, what share is visible today, because its dispute has arrived? (`P1.visible_share_30d`, a fraction) | num | | |
| P2 | Add proxy labels for days 63 to 169 to the mature-only training set (`LGBMClassifier`, 100 trees, the `MODEL` settings, seed 0). Recall at a 1% decline rate on the newest cohort, days 170 to 182, scored on true labels: direction and size of the change from the mature-only model (`P2.recall_1pct_delta`) | dir | | |
| P3 | Train naively on days 0 to 169 with the labels known by today (the same model, seed 0). Is its mean predicted fraud probability on the newest cohort above or below the cohort's true fraud rate, and by what factor? (`P3.mean_p_ratio`, the mean predicted probability over the true rate) | pick | | |

Terms, fixed so your numbers compare with the reference:

- **Calendar.** Day 0 is 2018-04-01. Today is day 183, 2018-10-01 00:00, the morning after the last synthetic payment. The training rows are the payments of days 0 to 169. The newest cohort is days 170 to 182, and nothing trains on it.
- **Inputs.** The 10 columns `load_data()` builds as of each payment's time t, lab 19's honest windowed features: the amount, the hour, the customer's payment count and mean amount over the 1, 7 and 30 days before t, the amount over that 30-day mean, and the terminal's frauds of the 30 days before t whose dispute arrived before t.
- **Observed label.** On a given date, a payment counts as fraud only when it is a fraud and its dispute has arrived by that date (`label_available_at <= date`). Before that it looks legitimate.
- **Mature-only (`--baseline`).** The training rows with `tx_datetime + 120 days <= today`, which are days 0 to 62, each with its observed label today.
- **Mature plus proxy (`--change`).** The mature rows with their labels, plus days 63 to 169, each labelled fraud when its dispute or its proxy flag has arrived by today (`proxy_flag and proxy_at <= today`). The synthetic proxy flag lands 1 to 7 days after the payment, with recall 0.5 and precision 0.4.
- **Naive (`--break`).** Days 0 to 169, each with its observed label today.
- **Model.** `LGBMClassifier(n_estimators=100, random_state=seed, verbose=-1, **MODEL)`, with no class weights, one fit per mode.
- **Decline at 1%.** Score the newest cohort and decline its top 1%: `p >= numpy.quantile(p, 0.99)`. **Recall:** declined true frauds over all true frauds in the newest cohort, read from `is_fraud`, never from an observed label. **Scenario-4 recall:** the same over the card-testing payments (`scenario == 4`), the synthetic attack that started on day 160.
- **Mean probability.** `mean_p` is the mean score over the newest cohort and `true_rate` its share of true frauds. `mean_p_ratio = mean_p / true_rate`. `mean_p_ratio_no_s4` is the same ratio over the newest cohort without its scenario-4 payments. `train_label_rate` is the share of the mode's training rows labelled fraud.
- **Maturity rows (`--baseline`).** For each age a of 7, 14, 30, 60, 90 and 120 days, take every payment at least a days old today and read its label as it stood when the payment was a days old. That reads every past cohort on the day it was a days old, a steadier estimate than one cohort alone. `true_rate_age{a}` and `observed_rate_age{a}` are those payments' true and observed fraud rates, and `P1.visible_share_30d = observed_rate_age30 / true_rate_age30`. The `TABLE cohort` lines show each calendar week's true and observed fraud rate as of today.
- **Seed.** `--seed` sets LightGBM's row and column sampling. The synthetic stream is always seed 0, so the maturity rows do not move with the seed.

## 2. Setup (before the session)

```
$ source ~/.venvs/ml/bin/activate
$ cd m4-production-ml-payments    # from ml-learning/, where sessions start
$ python scripts/21_delayed_labels.py --download
$ python scripts/21_delayed_labels.py --smoke
```

`--download` needs no network: `scripts/paystream.py` writes the synthetic stream to `~/ml-data/paystream/v1/` once. `--smoke` checks the given plumbing only: `load_data()` on customers 0 to 499, and `report()` printing every RESULT name. `--baseline`, `--change` and `--break` stop with NotImplementedError until the harness exists.

## 3. Baseline (0:12, 10 min)

Why: before choosing a training set, measure how fast a cohort's labels arrive, and score the one training set whose labels are all final.

You write first, in this file, no AI (about 4 min). This is the prompt the AI builds from:

1. The three labelling rules. For mature-only, mature plus proxy and naive: which rows go in, which label each row gets, and which comparison against today decides it.
2. The cohort definition. What "a cohort of age a" is for the maturity rows, and when its labels are read. Then the weekly table.
3. The RESULT contract. For every name in `CONTRACT`: the model, the rows and the formula behind it.

Then write `observed_labels()` and `training_sets()` in the script yourself, no AI, from the Key definition block of the Concept link section. Your P1 to P3 rows are logged, so opening that one block now is safe. Do not read the rest of the section until after the lab.

The AI then writes the harness for all three modes from your prompt, with `--smoke` running all three on customers 0 to 499. Annotate each AI block with one line before the first run.

```
$ python scripts/21_delayed_labels.py --baseline
(paste your RESULT lines)
```

Prediction vs actual, one sentence. The reference run is in `../../answers/`; the AI opens it only after your P1 row exists and you have pasted your own RESULT lines.

## 4. Change one thing (0:22, 10 min)

Change: keep days 0 to 62 with their matured labels, and add days 63 to 169, each labelled fraud when its dispute or its proxy flag has arrived by today. P2 is logged above. `P2.recall_1pct_delta` reads the baseline's recall at the same seed, so `--baseline` runs first.

```
$ python scripts/21_delayed_labels.py --change
(paste your RESULT lines)
```

## 5. Break it (0:32, 10 min, AI gives hints only; the run finishes by 0:40)

Break: train on days 0 to 169 with the labels known today, the naive set from your `training_sets()`. P3 is logged above.

```
$ python scripts/21_delayed_labels.py --break
(paste your RESULT lines)
```

Why, in three sentences, written without AI:

## 6. Explain-back (0:42, 5 min) and rebuild (0:47, 10 min), no AI

- Five sentences for a smart engineer new to ML, written without AI. The AI names your weakest claim after the session (section 7).
- Rebuild: open `rebuild/21_label_maturity.py`, write `observed_labels()`, `cohort_report()` and `training_sets()` from memory, then run `python rebuild/21_label_maturity.py`. Its `check()` compares them with a brute-force loop over 1,000 synthetic rows, using pandas weekly periods for the cohorts, never with this lab's results.

## 7. What I learned

After the session (about 5 minutes): the AI names the weakest claim in your five sentences and asks one question that tests it. Edit the sentences here.

## 8. Interview soundbite (one of the three cards written at 0:57)

> One or two sentences only someone who ran this would say.

Framing: decision ___ | prediction time ___ | label and its maturity ___ | offline metric ___ | online metric ___ | guardrail ___

Staff follow-up (failure modes): a card-testing attack starts this morning. What stops it in the first hour, and what tells you, before any dispute lands, whether the model has learned it? Answer in 2 sentences from the repo link (§1 of the model-lifecycle deep dive), with [`rules-engine-and-attack-response.md` §1 Rules and the model do different jobs](../../../hld/payments-risk-decisioning/deep-dives/rules-engine-and-attack-response.md#1-rules-and-the-model-do-different-jobs). Rotate: simplest design, failure modes, migration, what pages at 3 am, cost, trade-off.

## 9. Quiz cards (0:57, 3 min)

The AI drafts three cards (M, N, and T or D). Edit or replace them. Questions go to `../../quiz-bank.md`, keys to `../../answers/quiz-key.md`.

## Record

The script prints these as RESULT lines. Paste, do not type. `--baseline` also prints the weekly `TABLE cohort` lines; paste them under step 3.

| Metric | Your run | Hardware (the script's HW line) | Captured by (script or learner) |
|---|---|---|---|
| `P1.visible_share_30d` (frauds at least 30 days old: the share whose dispute arrived within 30 days) | | | script |
| `baseline.true_rate_age7` (true fraud rate, payments at least 7 days old) | | | script |
| `baseline.observed_rate_age7` (the same payments, labels read at age 7 days) | | | script |
| `baseline.true_rate_age14` (true fraud rate, payments at least 14 days old) | | | script |
| `baseline.observed_rate_age14` (labels read at age 14 days) | | | script |
| `baseline.true_rate_age30` (true fraud rate, payments at least 30 days old) | | | script |
| `baseline.observed_rate_age30` (labels read at age 30 days) | | | script |
| `baseline.true_rate_age60` (true fraud rate, payments at least 60 days old) | | | script |
| `baseline.observed_rate_age60` (labels read at age 60 days) | | | script |
| `baseline.true_rate_age90` (true fraud rate, payments at least 90 days old) | | | script |
| `baseline.observed_rate_age90` (labels read at age 90 days) | | | script |
| `baseline.true_rate_age120` (true fraud rate, payments at least 120 days old) | | | script |
| `baseline.observed_rate_age120` (labels read at age 120 days) | | | script |
| `baseline.recall_1pct` (mature-only, recall at a 1% decline rate, newest cohort, true labels) | | | script |
| `baseline.mean_p_ratio` (mature-only, mean predicted probability over the true rate) | | | script |
| `baseline.recall_s4` (mature-only, recall on the scenario-4 card-testing frauds) | | | script |
| `baseline.mean_p` (mature-only, mean predicted probability, newest cohort) | | | script |
| `baseline.true_rate` (true fraud rate, newest cohort) | | | script |
| `baseline.mean_p_ratio_no_s4` (mature-only, the ratio without the scenario-4 payments) | | | script |
| `baseline.train_label_rate` (share of the mature-only training rows labelled fraud) | | | script |
| `P2.recall_1pct` (mature plus proxy, recall at a 1% decline rate) | | | script |
| `P2.recall_1pct_delta` (mature plus proxy minus mature-only, same seed) | | | script |
| `change.mean_p_ratio` (mature plus proxy, mean predicted probability over the true rate) | | | script |
| `change.recall_s4` (mature plus proxy, recall on the scenario-4 frauds) | | | script |
| `change.mean_p` (mature plus proxy, mean predicted probability) | | | script |
| `change.true_rate` (true fraud rate, newest cohort) | | | script |
| `change.mean_p_ratio_no_s4` (mature plus proxy, the ratio without the scenario-4 payments) | | | script |
| `change.train_label_rate` (share of the mature-plus-proxy training rows labelled fraud) | | | script |
| `P3.mean_p_ratio` (naive, mean predicted probability over the true rate) | | | script |
| `break.recall_1pct` (naive, recall at a 1% decline rate) | | | script |
| `break.recall_s4` (naive, recall on the scenario-4 frauds) | | | script |
| `break.mean_p` (naive, mean predicted probability) | | | script |
| `break.true_rate` (true fraud rate, newest cohort) | | | script |
| `break.mean_p_ratio_no_s4` (naive, the ratio without the scenario-4 payments) | | | script |
| `break.train_label_rate` (share of the naive training rows labelled fraud) | | | script |
