# 22. Calibration and decline thresholds: what downsampling does to probabilities

> Goal: after this I can show what training on 10% of the legitimate rows does to the mean predicted probability and to the decline rate at a fixed threshold, correct it, and set amount-aware thresholds. (No result values anywhere in this file.)

**Level:** S (see `ml-learning/CLAUDE.md`). **Output style:** Explanatory
**Concept link:** [`../README.md#calibration-and-decline-thresholds`](../README.md#calibration-and-decline-thresholds) (read after the lab; at step 4 you open only its prior-correction formula)
**Borrowed from:** [Guo et al. 2017, On Calibration of Modern Neural Networks (arXiv 1706.04599)](https://arxiv.org/abs/1706.04599); the [scikit-learn calibration guide](https://scikit-learn.org/stable/modules/calibration.html); Dal Pozzolo, Caelen, Johnson and Bontempi 2015, ["Calibrating Probability with Undersampling for Unbalanced Classification"](https://doi.org/10.1109/SSCI.2015.33) (Symposium Series on Computational Intelligence); [Rules of Machine Learning (ML)](https://developers.google.com/machine-learning/guides/rules-of-ml) #15 and #30; Google ML Crash Course, [Imbalanced datasets](https://developers.google.com/machine-learning/crash-course/overfitting/imbalanced-datasets). Do it after the lab, as the second contact 1 to 3 days later.
**Dataset:** Credit Card Fraud, ULB (Université Libre de Bruxelles), OpenML 1597, `creditcard`: 284,807 card payments with 492 frauds (0.17%), V1 to V28 (components from PCA, principal component analysis), Amount and the label (OpenML keeps Time as a row id, so it is not a feature). 68.8 MB of ARFF (Attribute-Relation File Format), gzipped, or the 73.2 MB parquet fallback, <https://www.openml.org/d/1597>, licence Public (OpenML). Shared with labs 09, 24 and 27, with the same stratified 80/20 split (56,962 test rows)
**Runs on:** cpu. **Lane:** light. **Compute:** 4 runs x 1 min, at most 6 min per run. Precomputed steps: none
**Needs:** base install only
**Before the session** (from the module folder, see section 2): `python scripts/22_calibration_and_thresholds.py --download` (OpenML 1597 into `~/ml-data/openml/`, shared with labs 09, 24 and 27), then `--smoke`.
**Interview question:** After downsampling legitimate payments 10:1, what does a score of 0.3 mean, who owns the decline threshold, and why should $20 and $2,000 payments get different thresholds?
**Repo link:** [`hld/payments-risk-decisioning/deep-dives/model-lifecycle-shadow-and-labels.md`, §4 Thresholds from cost, and why the inputs must scale](../../../hld/payments-risk-decisioning/deep-dives/model-lifecycle-shadow-and-labels.md#4-thresholds-from-cost-and-why-the-inputs-must-scale); [§6 Rolling a model back](../../../hld/payments-risk-decisioning/deep-dives/model-lifecycle-shadow-and-labels.md#6-rolling-a-model-back)
**Captured by the script:** P1 to P3 and every Record row; `--baseline` at seed 0 also saves the champion, the challenger and the test row positions to `~/ml-data/models/lab22/` for lab 24. **Human steps:** none (you write the harness prompt in section 3 and `correct_for_downsampling()` in section 4)
**Status:** todo

## 0. Retrieval (0:00, 5 min, closed book, no AI)

The AI asks up to three due cards from `../../quiz-bank.md`, one at a time. Do not open the bank first.

## 1. Predict (0:05, 7 min, no AI)

Level S: read `scripts/22_calibration_and_thresholds.py` for 2 minutes first. `load_data()`, `report()` (the RESULT contract your harness feeds) and `save_for_lab24()` are given.

Write each row here before anything runs; the AI copies it into `../../prediction-log.md` word for word. A row that asks for several numbers becomes one log row per number, each with its own range. Give probabilities and rates as fractions (0.5 is 50%).

| Step | Question | Kind | Prediction | 80% range or confidence |
|---|---|---|---|---|
| P1 | The champion, `make_pipeline(StandardScaler(), LogisticRegression(max_iter=5000))`, trained on all 227,845 training rows (stratified 80/20 split, `random_state` 0): its mean predicted fraud probability on the untouched 56,962 test payments, whose true fraud rate is 0.17% | num | | |
| P2 | The same pipeline trained on every training fraud plus 10% of the legitimate training rows (sampled with seed 0; the test set is untouched): its mean predicted probability on the same 56,962 test payments | num | | |
| P3 | Ship the P2 model with the champion's threshold, the champion score that declined 0.2% of its 227,845 training payments. Two numbers, each with its own 80% range: (a) the new decline rate on the 56,962 test payments; (b) the false declines out of 56,962 | num | (a) (b) | (a) (b) |

P3 asks for two numbers: write each with its own 80% range. A hit needs both inside their ranges, and Off by uses the false declines. The two are linked by definition: every decline is either a false decline or a fraud caught, and frauds caught cannot exceed the test set's frauds (0.17% of 56,962), so keep your two numbers consistent.

Terms, fixed so your numbers compare with the reference:

- **Split.** `train_test_split` on the row positions, `test_size=0.2`, stratified on the label, `random_state` = the seed. No model trains on the test rows and no sample draws from them.
- **Downsampled training set.** Every fraud in the training split plus a random 10% of its legitimate rows, drawn without replacement with `numpy.random.default_rng(seed)`.
- **Threshold.** The champion's 99.8th percentile score on its own training payments (`numpy.quantile(p_train, 0.998)`), so it is fixed before the test traffic arrives. It is set once, from the champion, and reused unchanged for every other model. These are in-sample scores, from the rows the champion was fit on: a simplification this lab accepts for a logistic regression. A flexible model such as lab 24's LightGBM needs held-out or out-of-time scores to set its threshold.
- **Decline.** A score above the threshold. **False decline:** a declined legitimate payment. **Fraud caught:** a declined fraud.
- **Prior-corrected.** The P2 model's scores passed through your `correct_for_downsampling(p, 0.10)`.
- **Reliability table.** 10 quantile bins of the test scores, mean predicted and observed fraud rate per bin, as `sklearn.calibration.calibration_curve(strategy="quantile")` bins them. **Brier score:** the mean of (p minus y) squared over the test payments, lower is better.
- **Amount rules (`--amount`, on the champion's scores).** A declined fraud saves L(a) = a + $15 and a declined good payment costs C_fd(a) = 0.13a + $8, with a the payment's Amount read as dollars. Decline when p > p\*(a) = C_fd(a) / (C_fd(a) + L(a)), which is 0.23 at $20, 0.14 at $200 and 0.12 at $2,000 (the repo's numbers). The flat rule uses p\*($200) for every payment. **Net dollars:** fraud losses avoided minus false-decline costs, against approving every payment.

## 2. Setup (before the session)

```
$ source ~/.venvs/ml/bin/activate
$ cd m4-production-ml-payments    # from ml-learning/, where sessions start
$ python scripts/22_calibration_and_thresholds.py --download
$ python scripts/22_calibration_and_thresholds.py --smoke
```

`--smoke` checks the given plumbing only: `load_data()` on a 30,000-row sample, and `report()` printing every RESULT name and a reliability table per mode. `--baseline`, `--change`, `--break` and `--amount` stop with NotImplementedError until the harness exists.

## 3. Baseline (0:12, 10 min)

Why: a decline threshold is a point on the model's probability scale, so first measure where the champion's scale sits against the true fraud rate.

You write first, in this file, no AI (about 4 min). This is the prompt the AI builds from:

1. One line: the split, the downsampled training set and the threshold follow the Terms. Then one choice the Terms leave open: how `--break` and `--amount` get the champion's scores and its threshold (refit the champion on the same split in each mode, or reuse what `--baseline` produced: its printed threshold through `labkit.prior()`, its saved model at seed 0), and why.
2. The RESULT contract for `P1.mean_p`, `P2.mean_p`, `P3.decline_rate` and `P3.false_declines`: the model, the rows and the formula behind each. Add one-line formulas for a decline rate, false declines, the Brier score and net dollars. The AI fills the other `CONTRACT` names from the Terms and the Record table.

Your prompt also says that the baseline at seed 0 calls `save_for_lab24()` with the champion, an `LGBMClassifier(n_estimators=100, random_state=0)` challenger trained on the same training rows, and the test row positions.

The AI then writes the harness for all four modes from your prompt, with `--smoke` running all four on the 30,000-row sample. It leaves `correct_for_downsampling()` as your stub: in `--smoke` only, the harness passes the raw scores through in its place, with one comment saying smoke checks the plumbing only. Annotate each AI block with one line before the first run.

```
$ python scripts/22_calibration_and_thresholds.py --baseline
(paste your RESULT lines)
```

Prediction vs actual, one sentence. The reference run is in `../../answers/`; the AI opens it only after your P1 row exists and you have pasted your own RESULT lines.

## 4. Change one thing (0:22, 10 min)

Change: train the same pipeline on every training fraud plus 10% of the legitimate training rows (seed 0), and score the same untouched test set. P2 is logged above.

Why: teams downsample the legitimate class to cut training time and ease the class imbalance, so this run measures what that one choice does to the scores.

Before the run, write `correct_for_downsampling(p_sample, keep_rate)` in the script yourself, no AI, from the prior-correction formula in the Concept link section. Your P1 to P3 rows are logged, so opening that formula now is safe. `--change` also prints the prior-corrected mean, both Brier scores and two reliability tables.

```
$ python scripts/22_calibration_and_thresholds.py --change
(paste your RESULT lines)
```

## 5. Break it (0:32, 10 min, AI gives hints only; the run finishes by 0:40)

Break: ship the downsampled model with the full-data model's threshold. P3 is logged above. `--break` also applies that threshold to the prior-corrected scores and prints the two `break.new_fd_` rows of the Record table.

Why: a threshold table is configuration that a retrain can leave untouched, so this run reuses it exactly as shipped.

```
$ python scripts/22_calibration_and_thresholds.py --break
(paste your RESULT lines)
```

Why, in three sentences, written without AI:

Then price the threshold by amount. Record only, no prediction; the run takes seconds and also finishes by 0:40.

Why: a wrong decision on a $2,000 payment costs more than one on a $20 payment, so the threshold may depend on the amount.

```
$ python scripts/22_calibration_and_thresholds.py --amount
(paste your RESULT lines)
```

Note which payments the two rules decide differently (`amount.changed`, `amount.changed_frauds`).

## 6. Explain-back (0:42, 5 min) and rebuild (0:47, 10 min), no AI

- Five sentences for a smart engineer new to ML, written without AI. The AI names your weakest claim after the session (section 7).
- Rebuild: open `rebuild/22_calibration.py`, write `correct_for_downsampling()` from memory, and `reliability_table()` and `brier()` from their docstrings, then run `python rebuild/22_calibration.py`. Its `check()` compares with scikit-learn (`brier_score_loss`, `calibration_curve(strategy="quantile")`, and a `LogisticRegression` toy trained with 10% of its negatives kept), never with this lab's results.

## 7. What I learned

After the session (about 5 minutes): the AI names the weakest claim in your five sentences and asks one question that tests it. Edit the sentences here.

## 8. Interview soundbite (one of the three cards written at 0:57)

> One or two sentences only someone who ran this would say.

Framing: decision ___ | prediction time ___ | label and its maturity ___ | offline metric ___ | online metric ___ | guardrail ___

Staff follow-up (failure modes): a retrain switches to 10% downsampling and ships with the old threshold table. What must flip together with a model version, and what keeps the rollback itself fast on every pod? Answer in 2 sentences from the repo link (§6). Rotate: simplest design, failure modes, migration, what pages at 3 am, cost, trade-off.

## 9. Quiz cards (0:57, 3 min)

The AI drafts three cards (M, N, and T or D). Edit or replace them. Questions go to `../../quiz-bank.md`, keys to `../../answers/quiz-key.md`.

## Record

The script prints these as RESULT lines. Paste, do not type. `--baseline` and `--change` also print TABLE lines (the reliability tables); paste them under their step.

| Metric | Your run | Hardware (the script's HW line) | Captured by (script or learner) |
|---|---|---|---|
| `P1.mean_p` (champion, mean predicted probability on the test set) | | | script |
| `baseline.mean_p_legit` (champion, mean predicted probability over the legitimate test payments only) | | | script |
| `baseline.fraud_rate` (observed fraud rate of the test set) | | | script |
| `baseline.threshold` (the champion score that declined 0.2% of its training payments) | | | script |
| `baseline.decline_rate` (champion at that threshold, on the test payments) | | | script |
| `baseline.false_declines` (champion, of 56,962) | | | script |
| `baseline.frauds_caught` (champion) | | | script |
| `baseline.brier` (champion) | | | script |
| `P2.mean_p` (downsampled model, raw scores) | | | script |
| `change.mean_p_legit` (downsampled model, raw scores, legitimate test payments only) | | | script |
| `change.mean_p_corrected` (downsampled model, prior-corrected) | | | script |
| `change.brier` (downsampled model, raw scores) | | | script |
| `change.brier_corrected` (downsampled model, prior-corrected) | | | script |
| `P3.decline_rate` (downsampled model at the champion's threshold) | | | script |
| `P3.false_declines` (downsampled model at the champion's threshold, of 56,962) | | | script |
| `break.frauds_caught` (downsampled model at the champion's threshold) | | | script |
| `break.decline_rate_corrected` (prior-corrected scores at the champion's threshold) | | | script |
| `break.false_declines_corrected` (prior-corrected scores, of 56,962) | | | script |
| `break.frauds_caught_corrected` (prior-corrected scores) | | | script |
| `break.new_fd_gap` (median of the threshold over the champion score, across the legitimate test payments that the downsampled model declines and the champion approves at the champion's threshold) | | | script |
| `break.new_fd_lift` (median of the downsampled score over the champion score, across the same payments) | | | script |
| `amount.net_flat` (dollars, champion with the flat p\*($200) rule) | | | script |
| `amount.net_aware` (dollars, champion with p\*(a) per payment) | | | script |
| `amount.net_gain` (dollars, amount-aware minus flat) | | | script |
| `amount.declines_flat` (payments declined by the flat rule) | | | script |
| `amount.declines_aware` (payments declined by the amount-aware rule) | | | script |
| `amount.changed` (test payments the two rules decide differently) | | | script |
| `amount.changed_frauds` (frauds among those payments) | | | script |
