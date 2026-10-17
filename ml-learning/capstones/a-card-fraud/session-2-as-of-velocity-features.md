# A2. As-of velocity features: a point-in-time join, then a latest-value join

> Goal: after this I can build 6 as-of features per card (count and amount in the last 1 h and 24 h, first time at this merchant, first time in this MCC), prove them against a brute-force count on 200 random payments, and measure what a latest-value join does to the PR-AUC. (No result values anywhere in this file. Capstones have no reference run and no answers file: your run is the answer.)

**Capstone:** [A, card-fraud model, end to end](README.md), session 2 of 4, labkit id 42. **Level:** B (see `ml-learning/CLAUDE.md`). **Output style:** Explanatory
**Builds on:** labs 19 (as-of features) and 20 (one feature function for both paths), plus your A1 split and model
**Dataset:** the A1 sample, `~/ml-data/tabformer/sample.parquet` (synthetic). On the fallback, see the README's [fallback table](README.md#fallback-the-paystream-generator-synthetic): no MCC, so 5 features
**Runs on:** cpu. **Lane:** light. **Compute:** no reference run; 2 measured runs, each capped at 6 min. Precomputed steps: none
**Needs:** base install only
**Before the session:** A1 done, so its split and scores sit in `~/ml-data/capstones/a/`. Nothing to download.
**Interview question:** How do you build "payments on this card in the last hour" for training so that it equals what the authorization path saw at that moment?
**Repo link:** [`hld/payments-risk-decisioning/deep-dives/features-and-freshness.md`, §6 Point-in-time correctness](../../../hld/payments-risk-decisioning/deep-dives/features-and-freshness.md#6-point-in-time-correctness); [`deep-dives/model-lifecycle-shadow-and-labels.md`, §2 Leakage: the trap in the training data](../../../hld/payments-risk-decisioning/deep-dives/model-lifecycle-shadow-and-labels.md#2-leakage-the-trap-in-the-training-data)
**Captured by the script:** P1 to P3 and every Record row. **Human steps:** the window rules, the design and the write-up
**Status:** todo

## 0. Framing (0:00, 7 min, no AI)

Reread your framing line in `design-doc.md`. Under it, write one line: which features this session adds, and the prediction time each one must respect.

## 1. Predict (0:07, 5 min, no AI)

Write each row here and in `../../prediction-log.md` (Lab `A2`) before anything runs. PR-AUC differences are in PR-AUC points (0.01 is one point).

| Step | Question | Kind | Prediction | 80% range or confidence |
|---|---|---|---|---|
| P1 | A1's LightGBM config (300 trees, learning rate 0.05, 31 leaves, seed 0) with the 6 as-of features in Terms added to the raw columns, A1's split: PR-AUC on the test year minus A1's P2. Up, down or same, plus a size range | dir | | |
| P2 | The same model, but every payment gets its card's 6 values as computed at that card's last payment in the sample (the latest-value join): PR-AUC on the test year minus the as-of model's. Up, down or same, plus a size range | dir | | |
| P3 | In the as-of model, which group holds more of LightGBM's total gain: the 6 as-of features, or the raw columns? One option and a confidence from 50 to 100 | pick | | |

Terms, fixed so your numbers compare with A1:

- **Card and time.** A card is the pair (User, Card). t is the payment's timestamp, to the minute.
- **The 6 features.** `n_1h` and `amt_1h`: the count and the summed Amount of the card's earlier payments in the hour before t. `n_24h` and `amt_24h`: the same over 24 hours. `first_merchant`: 1 if the card has no earlier payment at this Merchant Name. `first_mcc`: 1 if it has no earlier payment in this MCC. Merchant Name itself is not a feature.
- **Window rule.** You write it in section 3, per feature: where the window starts and ends relative to t, which ends are open, and how payments in the same minute count. The check uses your rule.
- **As-of join.** Each value is computed from the card's history before t only, by your window rule.
- **Latest-value join.** Compute the 6 values once per card, as of that card's last payment in the whole sample, and give that one row to every payment of the card. It is what a table of current features returns when you join it to old payments.
- **Brute-force check.** 200 random payments, seed 0. For each one, recount the 6 values with a plain loop over its card's payments, by your window rule. All 200 must match before any model trains.
- **Gain share.** The 6 features' share of `booster_.feature_importance(importance_type="gain")`, summed over all features. P3's answer is "as-of" when the share is above 0.5.
- **Intervals.** Each PR-AUC difference gets a 95% interval from 1,000 paired bootstrap resamples of test cards: both models are scored on the same resample.
- **Saved for later (seed 0 only).** The as-of model's test-year scores with row ids (session 4's challenger) and the 6 as-of features for every payment (session 3), to `~/ml-data/capstones/a/`.

## 2. Setup (before the session)

```
$ source ~/.venvs/ml/bin/activate
$ cd ml-learning/capstones/a-card-fraud
$ python scripts/a2_as_of_velocity_features.py --download
$ python scripts/a2_as_of_velocity_features.py --smoke
```

`--download` only checks that the A1 sample and its saved split exist, and prints their paths. The script exists once the AI writes it in section 3, or the day before from your design.

## 3. Baseline (0:12, 15 min)

Why: a velocity feature is only as honest as its window. The model may use only what the authorization path could know at t.

You write first, in this file, no AI (about 5 min). This is the prompt the AI builds from:

1. The window rule for each of the 6 features: start, end, open or closed ends, and same-minute ties.
2. How the join runs without a loop per payment (for example per card, in time order), and the 200-row brute-force check that runs before anything trains.
3. The RESULT contract: every name in the Record table, the mode that prints it, and its unit.

The AI then writes the script with `labkit.start(lab=42)` and the same feature function for both joins. Annotate each AI block with one line before the first run. `--baseline` runs the check first and stops if any of the 200 rows differs.

```
$ python scripts/a2_as_of_velocity_features.py --smoke
$ python scripts/a2_as_of_velocity_features.py --baseline
(paste your RESULT lines)
```

Prediction vs actual, one sentence each for P1 and P3. There is no reference run: the AI fills Actual and Hit from your pasted lines.

## 4. Change one thing (0:27, 15 min; the run finishes by 0:40)

Change: the latest-value join replaces the as-of join for the 6 features. The split, the model and the raw columns stay fixed. P2 is logged above.

Why: a feature store holds today's values, and joining them to last year's payments is a one-line change any pipeline can make by accident.

```
$ python scripts/a2_as_of_velocity_features.py --change
(paste your RESULT lines)
```

Prediction vs actual, one sentence.

## 5. Write-up (0:42, 15 min, no AI)

- **Explain-back (5 min).** Five sentences for a smart engineer new to ML. Then ask the AI for the weakest claim, not a rewrite.
- **Deliverable (10 min).** Add to `design-doc.md` §4 Features (the 6 features, their window rules, the check, and what the latest-value join did, with its interval) and §5 Model (the LightGBM config and why GBDT comes first, in the README's wording). At most 4 lines each.

## 6. What I learned

The five explain-back sentences, edited after the AI's question.

## 7. Interview soundbite (the card written at 0:57)

> One or two sentences only someone who ran this would say.

Framing: decision ___ | prediction time ___ | label and its maturity ___ | offline metric ___ | online metric ___ | guardrail ___

Staff follow-up (failure modes): during a card-testing attack, the streaming counter behind `n_1h` lags 30 s. What does the model see, and what catches the attack instead? Answer in 2 sentences from [`features-and-freshness.md` §3 Freshness against an attack, in numbers](../../../hld/payments-risk-decisioning/deep-dives/features-and-freshness.md#3-freshness-against-an-attack-in-numbers).

## 8. Close (0:57, 3 min)

The AI drafts card `A2-D` (a symptom and the first check) from your run. Edit or replace it. The question goes to `../../quiz-bank.md`, the key to `../../answers/quiz-key.md`, citing your RESULT line. Set Status here and in the [README](README.md#sessions).

## Record

Suggested names: if your RESULT contract renames them, edit this table first. Paste, do not type.

| Metric | Your run | Hardware (the script's HW line) | Captured by (script or learner) |
|---|---|---|---|
| Your window rule per feature | | | learner |
| `baseline.check_rows` (rows of the 200 that match the brute force) | | | script |
| `baseline.feature_s` (seconds to build the 6 features for every payment) | | | script |
| `baseline.pr_auc` and `baseline.roc_auc` (as-of model, test year) | | | script |
| `P1.pr_auc_gain` (as-of minus A1, PR-AUC points) | | | script |
| `baseline.pr_auc_gain_ci95_low` and `baseline.pr_auc_gain_ci95_high` | | | script |
| `P3.gain_share_asof` (share of total gain in the 6 as-of features) | | | script |
| `change.pr_auc` and `change.roc_auc` (latest-value join, test year) | | | script |
| `P2.pr_auc_change` (latest-value minus as-of, PR-AUC points) | | | script |
| `change.pr_auc_change_ci95_low` and `change.pr_auc_change_ci95_high` | | | script |
| `change.rows_differ_24h` (share of test payments whose `n_24h` differs between the two joins) | | | script |
