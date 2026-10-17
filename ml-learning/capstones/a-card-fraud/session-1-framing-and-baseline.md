# A1. Framing and baseline: a time split by year and a LightGBM with an interval

> Goal: after this I can frame a card-fraud model in 6 fields, split a synthetic card sample by year, and report a LightGBM PR-AUC (area under the precision-recall curve) with a 95% bootstrap interval over 1,000 resamples of cards. (No result values anywhere in this file. Capstones have no reference run and no answers file: your run is the answer.)

**Capstone:** [A, card-fraud model, end to end](README.md), session 1 of 4, labkit id 41. **Level:** B (see `ml-learning/CLAUDE.md`). **Output style:** Explanatory
**Builds on:** labs 03 (baselines first, then LightGBM), 09 (PR-AUC on rare events) and 10 (a time split)
**Dataset:** IBM TabFormer, synthetic card transactions: 10% of the users (seed 0; 200 of 2,000), about a tenth of the 24 M rows, from a 278.6 MB tgz, Apache-2.0 ([Data](README.md#data)). Fallback: `paystream.py`, synthetic ([fallback](README.md#fallback-the-paystream-generator-synthetic))
**Runs on:** cpu. **Lane:** light. **Compute:** no reference run; 2 measured runs, each capped at 6 min. Precomputed steps: none
**Needs:** base install only
**Before the session:** the AI writes the `--download` and `--smoke` modes of `scripts/a1_framing_and_baseline.py` from the README's Data section; you run `--download` once (278.6 MB, then chunked reads of the 2.35 GB CSV, so keep about 2.7 GB of disk free).
**Interview question:** You get 24 M card payments with a fraud flag: what do you frame first, what is your first baseline, and how sure are you of its PR-AUC?
**Repo link:** [`hld/payments-risk-decisioning/README.md`, Non-functional requirements](../../../hld/payments-risk-decisioning/README.md#non-functional-requirements) (the loss budget row: fraud loss and false declines are the product metrics); [`deep-dives/model-lifecycle-shadow-and-labels.md`, §5 Proving a model before it declines anyone](../../../hld/payments-risk-decisioning/deep-dives/model-lifecycle-shadow-and-labels.md#5-proving-a-model-before-it-declines-anyone) (offline: an out-of-time test per segment)
**Captured by the script:** P1 to P3 and every Record row. **Human steps:** the framing sprint, the design and the write-up
**Status:** todo

## 0. Framing (0:00, 7 min, no AI except as the interviewer)

**0:00 to 0:05, the framing sprint.** Tell the AI "play the interviewer for a card-fraud model". Then propose and confirm, by the rule in [`scoping-drills/README.md`](../../../scoping-drills/README.md#3-drill-2-propose-and-confirm) §3: state each assumption, attach its consequence, invite correction, and ask at most one open question. Cover:

- Who decides. The repo HLD decides as a payment processor for its merchants. TabFormer's rows are a card issuer's view: every payment of one cardholder, across merchants. Say which one you frame, and what that changes.
- When the model decides, what it must never do, and the scale.
- The failure default when the model is down.

The AI confirms or corrects each assumption in one line. It never proposes a metric, a split or a threshold.

**0:05 to 0:07, the framing line.** One value per field. It opens `design-doc.md` at 0:42.

decision ___ | prediction time ___ | label and its maturity ___ | offline metric ___ | online metric ___ | guardrail ___

The guardrail sets the decline rate that sessions 3 and 4 use (0.5% unless you write another).

## 1. Predict (0:07, 5 min, no AI)

First name your years in the Terms below, from the rows per year that `--download` printed. Then write each row here and in `../../prediction-log.md` (Lab `A1`) before anything runs. Give rates as a percent.

| Step | Question | Kind | Prediction | 80% range or confidence |
|---|---|---|---|---|
| P1 | The fraud rate of the test year in the sample (10% of users, seed 0), as a percent of its payments | num | | |
| P2 | PR-AUC on the test year of `LGBMClassifier(n_estimators=300, learning_rate=0.05, num_leaves=31, random_state=0)` trained on every payment of the training years, with the raw columns in Terms | num | | |
| P3 | The width of the 95% bootstrap interval of P2's PR-AUC: 1,000 resamples of the test year's cards with replacement, each card keeping all its test-year payments, seed 0, in PR-AUC points | num | | |

Terms, fixed so the runs in sessions 2 to 4 compare with this one:

- **Split.** Test: the last calendar year with all 12 months in the sample. Validation: the year before it. Train: every year before that. Write them here: train ___ to ___, validation ___, test ___. The validation year is held for calibration and thresholds in session 3. No choice in any session is made on the test year.
- **Raw columns.** Amount in dollars, hour, day of week, MCC, Use Chip, Merchant State (missing becomes its own level), a Zip-present flag, and Errors? as none or any. MCC, Use Chip and Merchant State go to LightGBM as `category` columns. Merchant Name waits for session 2.
- **Training rows.** Every payment of the training years. No downsampling, so the scores stay on the payment scale.
- **The one-line rule.** Amount itself as the score: a bigger payment ranks as riskier.
- **PR-AUC.** `sklearn.metrics.average_precision_score` on the test year, lab 09's metric.
- **Bootstrap.** 1,000 resamples, `numpy.random.default_rng(seed)`, a percentile interval from the 2.5th to the 97.5th value. By row: draw test payments. By card: draw (User, Card) pairs and keep all their test payments. Width = high minus low.
- **Saved for later (seed 0 only).** The split years and LightGBM's test-year scores with each payment's row id, to `~/ml-data/capstones/a/`. Session 4 reads them as the champion.

## 2. Setup (before the session)

```
$ source ~/.venvs/ml/bin/activate
$ cd ml-learning/capstones/a-card-fraud
$ python scripts/a1_framing_and_baseline.py --download
$ python scripts/a1_framing_and_baseline.py --smoke
```

There is no script until the AI writes one. Before the session, ask it for `--download` and `--smoke` only, from the README's Data section: the fetch with its size, the sha256 check, the extract, the chunked 10% user sample at seed 0, and rows per year. `--download` prints paths, sizes, users found, users kept and rows per year, never a fraud count. If the fetch fails, use the README's Box link, then the fallback.

## 3. Baseline (0:12, 15 min)

Why: on rare events every precision is read against the base rate, so measure it, and the cheapest rule's PR-AUC, before any model.

You write first, in this file, no AI (about 5 min). This is the prompt the AI builds from:

1. The split: the three year ranges, and the rule that no choice touches the test year.
2. The metric: PR-AUC, both bootstrap schemes, the seed.
3. The RESULT contract: every name in the Record table, the mode that prints it, and its unit. Each mode prints only its own rows.

The AI then writes `--baseline` and `--change` from your prompt, with `labkit.start(lab=41)`. Annotate each AI block with one line before the first run.

```
$ python scripts/a1_framing_and_baseline.py --smoke
$ python scripts/a1_framing_and_baseline.py --baseline
(paste your RESULT lines)
```

Prediction vs actual, one sentence. There is no reference run: the AI fills Actual and Hit in `../../prediction-log.md` from your pasted lines.

## 4. Change one thing (0:27, 15 min; the run finishes by 0:40)

Change: LightGBM on the raw columns replaces Amount as the score, then 1,000 bootstrap resamples by row and by card. P2 and P3 are logged above.

Why: a model earns its place by its margin over the one-line rule, and a margin means nothing without its interval.

```
$ python scripts/a1_framing_and_baseline.py --change
(paste your RESULT lines)
```

Prediction vs actual, one sentence each for P2 and P3.

## 5. Write-up (0:42, 15 min, no AI)

- **Explain-back (5 min).** Five sentences for a smart engineer new to ML. Then ask the AI for the weakest claim, not a rewrite.
- **Deliverable (10 min).** Start `design-doc.md` in this folder: the framing line, then §1 Framing (who decides, when, what must never happen) and §2 Offline and online metrics (PR-AUC with its interval, the online metric, the guardrail). At most 4 lines each.

## 6. What I learned

The five explain-back sentences, edited after the AI's question.

## 7. Interview soundbite (the card written at 0:57)

> One or two sentences only someone who ran this would say.

Framing: decision ___ | prediction time ___ | label and its maturity ___ | offline metric ___ | online metric ___ | guardrail ___

Staff follow-up (simplest design): what is the simplest model you would ship first at about 3 M payments a day, and what did you refuse to build? Answer in 2 sentences from the repo link, plus [`latency-budget-and-hot-path.md` §5](../../../hld/payments-risk-decisioning/deep-dives/latency-budget-and-hot-path.md#5-what-else-is-in-process-and-why) for why the model runs in process.

## 8. Close (0:57, 3 min)

The AI drafts card `A1-T` from your run. Edit or replace it. The question goes to `../../quiz-bank.md`, the key to `../../answers/quiz-key.md`, citing your RESULT line. Set Status here and in the [README](README.md#sessions).

## Record

Suggested names: if your RESULT contract renames them, edit this table first. Paste, do not type.

| Metric | Your run | Hardware (the script's HW line) | Captured by (script or learner) |
|---|---|---|---|
| The split years, users found, users kept and rows per year (from `--download`) | | | learner |
| `P1.base_rate_test` (percent of test-year payments that are fraud) | | | script |
| `baseline.base_rate_train` and `baseline.base_rate_valid` (percent) | | | script |
| `baseline.n_test` (test-year payments) | | | script |
| `baseline.pr_auc_amount` (Amount as the score, test year) | | | script |
| `P2.pr_auc` (LightGBM, test year) | | | script |
| `change.roc_auc` (LightGBM, test year) | | | script |
| `change.pr_auc_lift` (P2 divided by the test-year base rate) | | | script |
| `P3.ci95_width_cards` (by-card bootstrap, PR-AUC points) | | | script |
| `change.ci95_width_rows` (by-row bootstrap, PR-AUC points) | | | script |
| `change.train_s` (LightGBM fit seconds, M4 Pro, cpu) | | | script |
