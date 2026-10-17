# 19. Time split and as-of features: point-in-time correct joins

> Goal: after this I can build fraud features as of each payment's own timestamp, split by time, and read a 2x3 table of how much test AUC (area under the receiver operating characteristic curve) each kind of leak fakes. (No result values anywhere in this file.)

**Level:** S (see `ml-learning/CLAUDE.md`). **Output style:** Explanatory
**Concept link:** [`../README.md#point-in-time-features`](../README.md#point-in-time-features) (read after the lab; in section 5, once you have found the problem, you open only its Key formula block; where it lets you pick the clock a window runs on, the Honest inputs term in section 1 decides)
**Borrowed from:** Google's [Rules of Machine Learning](https://developers.google.com/machine-learning/guides/rules-of-ml), rules #29, #31 and #33; [Feast point-in-time joins](https://docs.feast.dev/getting-started/concepts/point-in-time-joins); Chip Huyen, *Designing Machine Learning Systems* (O'Reilly, 2022), chapter 5; Fraud Detection Handbook, chapter 3, [baseline feature transformation](https://fraud-detection-handbook.github.io/fraud-detection-handbook/Chapter_3_GettingStarted/BaselineFeatureTransformation.html) (customer spending windows of 1, 7 and 30 days). Do it after the lab, as the second contact 1 to 3 days later.
**Dataset:** the generated payments stream, synthetic, from [`scripts/paystream.py`](../scripts/paystream.py) at seed 0: 5,000 customers, 10,000 terminals, 183 days from 2018-04-01, 1,795,646 transactions, 0.99% of them fraud from 4 scenarios, a dispute arrival time for every fraud and an early-warning proxy flag. 30.3 MB of parquet in `~/ml-data/paystream/v1/`, generated on this Mac in seconds, with no download. The parameters follow the [Fraud Detection Handbook, chapter 3 simulator](https://fraud-detection-handbook.github.io/fraud-detection-handbook/Chapter_3_GettingStarted/SimulatedDataset.html). The code is written fresh, because the Handbook's code is GPL-3.0 (the GNU General Public License), so no third-party data or licence comes with it. Shared with labs 21 and 23.
**Runs on:** cpu. **Lane:** light. **Compute:** 4 runs x 2 min at most: `--baseline` 1 min, `--change` 1 min, `--baseline` again after your fix 1 min, and the reference `--break` the AI runs, 2 min (measured while other jobs shared the CPU). At most 6 min per run. Precomputed steps: none
**Needs:** base install only (pandas, pyarrow, LightGBM and scikit-learn are in the base)
**Before the session** (from the module folder, see section 2): `python scripts/19_as_of_features.py --download` (writes the synthetic stream to `~/ml-data/paystream/v1/`, shared with labs 21 and 23; a copy already there is kept), then `--smoke`. No human steps.
**Interview question:** How do you build "transactions per card in the last hour" for training without leaking the future or the label itself?
**Repo link:** [`hld/payments-risk-decisioning/deep-dives/model-lifecycle-shadow-and-labels.md`, §2 Leakage: the trap in the training data](../../../hld/payments-risk-decisioning/deep-dives/model-lifecycle-shadow-and-labels.md#2-leakage-the-trap-in-the-training-data); [`hld/payments-risk-decisioning/deep-dives/features-and-freshness.md`, §6 Point-in-time correctness](../../../hld/payments-risk-decisioning/deep-dives/features-and-freshness.md#6-point-in-time-correctness). Open them at close, for the Staff follow-up.
**Captured by the script:** P1 and P2, as shipped; P1 again after your fix; the reference's `--break` lines and its per-scenario lines, shown at the debrief. **Human steps:** your harness prompt (split, metric, RESULT contract), the audit of `features_v0.py` and your fix, the explain-back
**Status:** todo

## 0. Retrieval (0:00, 5 min, closed book, no AI)

The AI asks up to three due cards from `../../quiz-bank.md`, one at a time. Do not open the bank first.

## 1. Predict (0:05, 7 min, no AI)

Level S: read `load_data()` and `report()` in `scripts/19_as_of_features.py`, and all of `scripts/features_v0.py`, for 3 minutes. `report()` is the RESULT contract your harness feeds. `features_v0.py` is the feature code as it ships; leave it as it is until section 5.

Write each row here before anything runs; the AI copies it into `../../prediction-log.md` word for word. A row that asks for several numbers becomes one log row per number, each with its own range.

| Step | Question | Kind | Prediction | 80% range or confidence |
|---|---|---|---|---|
| P1 | Test AUC at seed 0 of the model in the Terms below, on the time split (train days 0 to 119, test days 127 to 182), with the 10 inputs exactly as `features_v0.build_features()` ships them | num | | |
| P2 | The same model and inputs on a random 80/20 split of all rows instead, at seed 0. AUC direction (up, down or same) and size, as P2 AUC minus P1 AUC | dir | | |
| P3 | FIND-IT. Is the shipped AUC honest? The test AUC on the time split with the honest inputs in the Terms below, same model, seed 0, as a number with an 80% range | num | | |

Terms, fixed so your numbers compare with the reference:

- **Rows.** Every transaction of the synthetic stream, from `load_data()`, sorted by `tx_datetime`. A row's prediction time t is its `tx_datetime`. `day` counts whole days from 2018-04-01, which is day 0.
- **Label.** `is_fraud`.
- **Inputs.** The 10 columns that `features_v0.build_features(tx)` returns, in its `FEATURES` order.
- **Honest inputs (P3).** Inputs a live system could compute at t. An input may use the payment's own amount and time, other payments only if their `tx_datetime` is strictly before t, and a fraud label only once it is known: its `label_available_at` is strictly before t. P3 is graded against the reference's honest inputs. They keep each shipped input that obeys these rules, unchanged and in its place. Any input that breaks them is replaced, in its place, by a count on the same key over the 30 days before t. A count of fraud labels takes its 30 days on the arrival time, not the payment time: the frauds with `label_available_at` in [t - 30 d, t). Write your fix to these rules, so that your number after the fix compares with P3.
- **Time split.** Train on days 0 to 119. Test on days 127 to 182. Days 120 to 126 are a one-week gap that neither side uses.
- **Random split.** A random 20% of all rows, drawn with the seed, is the test set. The other 80% trains. Days play no part.
- **Model.** `lightgbm.LGBMClassifier(n_estimators=200, learning_rate=0.05, min_child_samples=200, subsample=0.8, subsample_freq=1, colsample_bytree=0.8, random_state=seed, n_jobs=4, verbose=-1)`.
- **Metric.** ROC AUC (the area under the receiver operating characteristic curve; 0.5 is a coin flip) of the predicted fraud probability on the test rows, from `sklearn.metrics.roc_auc_score`. The importances `report()` takes are LightGBM's gain importance, `model.booster_.feature_importance("gain")`, as a pandas Series indexed by input name.

## 2. Setup (before the session)

```
$ source ~/.venvs/ml/bin/activate
$ cd m4-production-ml-payments    # from ml-learning/, where sessions start
$ python scripts/19_as_of_features.py --download
$ python scripts/19_as_of_features.py --smoke
```

`--download` generates the synthetic stream on this Mac, with no network. `--smoke` checks the given plumbing only: `load_data()` on the 60-day synthetic smoke stream, `build_features()`, and `report()` with placeholder values. `--baseline` and `--change` stop with NotImplementedError until the harness exists.

## 3. Baseline (0:12, 10 min)

Why: an out-of-time test AUC on the inputs as they ship is the first number a model review sees.

You write first, in this file, no AI (about 5 min). This is the prompt the AI builds from:

1. The split and the metric, from the Terms in section 1.
2. The RESULT contract: `--baseline` calls `report("baseline", auc, importances=gain)`. `--change` calls `report("change", auc, versus=labkit.prior("P1.auc"))`.

The AI then writes the rest: the inputs from `features_v0.build_features(tx)`, the two splits, LightGBM, the test AUC and the two modes. Annotate each AI block with one line before the first run.

```
$ python scripts/19_as_of_features.py --baseline
(paste your RESULT lines)
```

Prediction vs actual, one sentence. The reference run is in `../../answers/`; the AI opens it only after your P1 row exists and you have pasted your own RESULT lines.

## 4. Change one thing (0:22, 10 min)

Change: a random 80/20 split of all rows instead of the time split (Terms, section 1). The inputs, the model and the seed stay the same. P2 is logged above.

Why: many tutorials and quick notebooks split at random, so this run measures that one choice on the same model and inputs.

```
$ python scripts/19_as_of_features.py --change
(paste your RESULT lines)
```

## 5. Break it (0:32, 10 min, AI gives hints only; the run finishes by 0:40)

Something in the shipped code makes these numbers wrong. Find it before you run --break. P3 is logged above.

```
$ python scripts/19_as_of_features.py --baseline    # again, after your fix
$ python scripts/19_as_of_features.py --break       # one line: where the reveal lives
$ python ../answers/19_as_of_features_ref.py --break  # the AI runs this, after your fix or 'debrief 19'
(paste your RESULT lines)
```

Why, in three sentences, written without AI:

## 6. Explain-back (0:42, 5 min) and rebuild (0:47, 10 min), no AI

- Five sentences for a smart engineer new to ML, written without AI. The AI names your weakest claim after the session (section 7).
- Rebuild: the AI copies `rebuild/19_point_in_time_join.py` in from `answers/rebuild/stubs/` at 0:47. Write the body from memory, then run `python rebuild/19_point_in_time_join.py`. Its `check()` compares your function with a brute-force numpy count on 150 synthetic rows that include same-second ties, never with this lab's results.

## 7. What I learned

After the session (about 5 minutes): the AI names the weakest claim in your five sentences and asks one question that tests it. Edit the sentences here.

## 8. Interview soundbite (one of the three cards written at 0:57)

> One or two sentences only someone who ran this would say.

Framing, one line in your words: decision | prediction time | label and its maturity | offline metric | online metric | guardrail.

Staff follow-up (simplest design): a new velocity feature has no logged history yet. What is the simplest way to get training rows for it that a live system could have computed, and what would you refuse to build? Answer in 2 sentences from the repo links: §6 of `features-and-freshness.md` and §2 of `model-lifecycle-shadow-and-labels.md`. Rotate: simplest design, failure modes, migration, what pages at 3 am, cost, trade-off.

## 9. Quiz cards (0:57, 3 min)

The AI drafts three cards (M, N, and T or D). Edit or replace them. Questions go to `../../quiz-bank.md`, keys to `../../answers/quiz-key.md`.

## Record

The script prints these as RESULT lines. Paste, do not type. Rows marked reference come from the reference script at the debrief: the AI runs its `--break`, and shows its per-scenario lines from `--baseline` and `--change`.

| Metric | Your run | Hardware (the script's HW line) | Captured by (script or learner) |
|---|---|---|---|
| `P1.auc` (time split), as shipped | | | script |
| `baseline.top3` (the 3 inputs with the most gain), as shipped | | | script |
| `baseline.top1_share` (the top input's share of all gain), as shipped | | | script |
| `baseline.auc_s1`, reference `--baseline`, as shipped: the AUC of fraud scenario 1's test frauds (the `scenario` column) against every legitimate test row, with `n=` those frauds | | | script |
| `baseline.auc_s2`, reference `--baseline`: the same for scenario 2 | | | script |
| `baseline.auc_s3`, reference `--baseline`: the same for scenario 3 | | | script |
| `baseline.auc_s4`, reference `--baseline`: the same for scenario 4 | | | script |
| `P2.auc` (random split), as shipped | | | script |
| `P2.auc_delta` (P2 AUC minus P1 AUC), as shipped | | | script |
| `change.auc_s1`, reference `--change`, as shipped: scenario 1 on the random split | | | script |
| `change.auc_s2`, reference `--change`: scenario 2 on the random split | | | script |
| `change.auc_s3`, reference `--change`: scenario 3 on the random split | | | script |
| `change.auc_s4`, reference `--change`: scenario 4 on the random split | | | script |
| `P1.auc`, after your fix | | | script |
| `baseline.top3`, after your fix | | | script |
| `baseline.top1_share`, after your fix | | | script |
| `P3.auc`, reference `--break` (your P3 answer) | | | script |
| `break.top3`, reference `--break`: the reference's honest model | | | script |
| `break.top1_share`, reference `--break`: the reference's honest model | | | script |
| `break.auc_time_asof`, reference `--break`: the 2x3 table, row 1, time split | | | script |
| `break.auc_random_asof`, reference `--break`: the 2x3 table, row 1, random split | | | script |
| Reference `--break`, the 2x3 table, row 2, time split: the third of the six `break.auc_<split>_<row>` lines, unnamed here because its row name would give the planted problem away | | | script |
| Reference `--break`, the 2x3 table, row 2, random split: the fourth of those lines, unnamed for the same reason | | | script |
| Reference `--break`, the 2x3 table, row 3, time split: the fifth of those lines, unnamed for the same reason | | | script |
| Reference `--break`, the 2x3 table, row 3, random split: the sixth of those lines, unnamed for the same reason | | | script |
| `break.auc_s1`, reference `--break`: scenario 1 for the reference's honest model, time split | | | script |
| `break.auc_s2`, reference `--break`: scenario 2, the same model | | | script |
| `break.auc_s3`, reference `--break`: scenario 3, the same model | | | script |
| `break.auc_s4`, reference `--break`: scenario 4, the same model | | | script |
| What you found: where the shipped code goes wrong, why that inflates the AUC, and your fix | | | learner |
