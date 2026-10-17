# 27. Audit an AI-written fraud pipeline: silent bugs in fluent code

> Goal: after this I can audit a 120-line training and evaluation script, find its silent bugs with hints only, and state the honest metrics on next month's traffic. (No result values anywhere in this file.)

**Level:** B (see `ml-learning/CLAUDE.md`). **Output style:** Explanatory
**Concept link:** [`../README.md#reviewing-ai-written-ml-code`](../README.md#reviewing-ai-written-ml-code) (read after the lab)
**Borrowed from:** Kaggle Learn [Intermediate Machine Learning](https://www.kaggle.com/learn/intermediate-machine-learning), lesson 7; [Rules of ML](https://developers.google.com/machine-learning/guides/rules-of-ml) rule #30; Dal Pozzolo, Caelen, Johnson and Bontempi 2015 (IEEE Symposium Series on Computational Intelligence); Shen and Tamkin 2026, Anthropic's randomized trial of AI help while learning to code ([arXiv 2601.20245](https://arxiv.org/abs/2601.20245), [blog](https://www.anthropic.com/research/AI-assistance-coding-skills)), where the largest gap between the groups was on debugging. Do it after the lab, as the second contact 1 to 3 days later.
**Dataset:** Credit Card Fraud, ULB (Université Libre de Bruxelles), OpenML 1597 (`creditcard`): 284,807 card payments over two days with 492 frauds (0.17%), V1 to V28 (components from PCA, principal component analysis), Amount and the label, stored in time order (OpenML keeps Time as the row id). The script reads the first 80%, called history in this lab: 227,845 payments, 417 frauds. The reference `--break` scores the last 20%, called next month's traffic: 56,962 payments, 75 frauds, the last 7.7 hours of the two days. 68.8 MB of gzipped ARFF (Attribute-Relation File Format) or the 73 MB parquet fallback, <https://www.openml.org/d/1597>, licence Public (OpenML). Shared with labs 09, 22 and 24
**Runs on:** cpu. **Lane:** light. **Compute:** 3 runs x 1 min (`--baseline`, `--change` on your copy after each fix, the reference `--break`), at most 6 min per run. Precomputed steps: none
**Needs:** base install only
**Before the session** (from the module folder, see section 2): `python scripts/27_audit_an_ai_written_pipeline.py --download` (OpenML 1597 into `~/ml-data/openml/`, shared with labs 09, 22 and 24), then `--smoke`. Do not read the script before 0:05.
**Interview question:** An AI assistant wrote your team's fraud training pipeline and its offline PR-AUC looks great: what checks do you run before anyone trusts that number?
**Repo link:** [`hld/payments-risk-decisioning/deep-dives/model-lifecycle-shadow-and-labels.md`, §2 Leakage: the trap in the training data](../../../hld/payments-risk-decisioning/deep-dives/model-lifecycle-shadow-and-labels.md#2-leakage-the-trap-in-the-training-data); [`hld/payments-risk-decisioning/edge-cases.md`, Edge case: the leakage trap in training data](../../../hld/payments-risk-decisioning/edge-cases.md#edge-case-the-leakage-trap-in-training-data). Read them at 0:57, for the Staff follow-up.
**Captured by the script:** the shipped report (`--baseline`), your copy's report after each fix (`--change`), and the reference `--break` after the audit: the honest numbers on next month's traffic, the threshold and its decline rate, and the effect of each single fix. **Human steps:** the audit itself: each bug you find, where it is, the hints you used and the minutes it took.
**Status:** todo

## 0. Retrieval (0:00, 5 min, closed book, no AI)

The AI asks up to three due cards from `../../quiz-bank.md`, one at a time. Do not open the bank first.

## 1. Predict (0:05, 7 min, no AI)

Level B, the audit: skim `scripts/27_audit_an_ai_written_pipeline.py` for 4 minutes first. Read it as its reviewer would, without running it and without AI. It is the only code you get, and you write nothing else until the audit is done.

Write each row here before anything runs; the AI copies it into `../../prediction-log.md` word for word. A row that asks for several numbers becomes one log row per number, each with its own range. Give rates as fractions (0.01 is 1%).

| Step | Question | Kind | Prediction | 80% range or confidence |
|---|---|---|---|---|
| P1 | The script reports a PR-AUC (area under the precision-recall curve, computed as average precision) on its own test rows. Your honest PR-AUC: logistic regression trained on history by a corrected pipeline (the reference's, run after your audit), scored on next month's 56,962 payments with 75 frauds, seed 0 | num | | |
| P2 | How many independent silent bugs the script contains. Count a bug when it has its own fix and fixing it alone moves a number the script reports or ships | num | | |
| P3 | The script picks the best-F1 threshold within its 0.2% decline budget (`DECLINE_BUDGET`) and reports the decline rate it expects (`baseline.decline_rate`). Ship that model and threshold: the decline rate on next month's 56,962 payments, seed 0 | num | | |

## 2. Setup (before the session)

```
$ source ~/.venvs/ml/bin/activate
$ cd m4-production-ml-payments    # from ml-learning/, where sessions start
$ python scripts/27_audit_an_ai_written_pipeline.py --download
$ python scripts/27_audit_an_ai_written_pipeline.py --smoke
```

`--smoke` runs the whole pipeline on every 5th payment and prints `SMOKE ... ok` lines only. `--break` in this script prints one line: the reveal lives in the reference.

## 3. Baseline (0:12, 3 min)

Why: these are the numbers the script's author would bring to a launch review, so see them before you read the code again.

```
$ python scripts/27_audit_an_ai_written_pipeline.py --baseline
(paste your RESULT lines)
```

Prediction vs actual: not yet. P1 and P3 are about next month's traffic, which only the reference `--break` scores, so all three rows are graded at the debrief. The reference run is in `../../answers/`; the AI opens it only then.

## 4. Change one thing (0:15, the audit, 23 min; one block from 0:12 to 0:42)

Change: the audit. Find the bugs with the hint ladder only, and fix each one in a copy of the script. P2 is logged above.

Why: a bug you find yourself is the skill this lab trains; a fix the AI shows you is not.

You write first, in this file, no AI (3 min): your audit plan. List the script's steps in order. For each step, write the one question you will ask of it. Add a stop rule: when you stop looking for more.

Rules for the AI: hints only, one per message, by the ladder in `ml-learning/CLAUDE.md` §6. It never points at a line before three hints and an explicit "show me". For each bug, log in the Record where it is, the highest hint you needed and the minutes it took.

```
$ cp scripts/27_audit_an_ai_written_pipeline.py scripts/27_audit_copy.py
$ python scripts/27_audit_copy.py --change      # after each fix, on your copy only
(paste your RESULT lines)
```

`--change` runs the same pipeline as `--baseline` and labels its lines `change.*`, so each run of your copy reads against the shipped baseline above. Leave the shipped script as it is.

## 5. Break it (0:38, the end of the audit block; the run finishes by 0:40)

Something in the shipped code makes these numbers wrong. Find it before you run --break.

P3 is logged above. Stop the audit at 0:38. The AI then runs the reference `--break`, which scores next month's traffic and prints the reported against the honest numbers and the effect of each single fix, and pastes its RESULT lines here.

```
$ python scripts/27_audit_an_ai_written_pipeline.py --break       # one line: where the reveal lives
$ python ../answers/27_audit_an_ai_written_pipeline_ref.py --break  # the AI runs this, after your audit
(paste your RESULT lines)
```

Why, in three sentences, written without AI:

## 6. Explain-back (0:42, 5 min) and rebuild (0:47, 10 min), no AI

- Five sentences for a smart engineer new to ML, written without AI. The AI names your weakest claim after the session (section 7).
- Rebuild: the AI copies `rebuild/27_honest_core.py` in from `answers/rebuild/stubs/` at 0:47. Write the body of `honest_core()` from memory, then run `python rebuild/27_honest_core.py`. Its `check()` compares with numpy and scikit-learn on a toy dataset, never with this lab's results.

## 7. What I learned

After the session (about 5 minutes): the AI names the weakest claim in your five sentences and asks one question that tests it. Edit the sentences here.

## 8. Interview soundbite (one of the three cards written at 0:57)

> One or two sentences only someone who ran this would say.

Framing: decision ___ | prediction time ___ | label and its maturity ___ | offline metric ___ | online metric ___ | guardrail ___

Staff follow-up (simplest design): which one offline check would you make a launch gate for every fraud model, whoever wrote the code, and what would it have shown in this lab? Answer in 2 sentences from the repo link (§2 item 5, §8 item 5, and the edge case's answer). Rotate: simplest design, failure modes, migration, what pages at 3 am, cost, trade-off.

## 9. Quiz cards (0:57, 3 min)

The AI drafts three cards (M, N, and T or D). Edit or replace them. Questions go to `../../quiz-bank.md`, keys to `../../answers/quiz-key.md`.

## Record

The script prints these as RESULT lines. Paste, do not type.

| Metric | Your run | Hardware (the script's HW line) | Captured by (script or learner) |
|---|---|---|---|
| `baseline.pr_auc`: the shipped report, PR-AUC on its own test rows | | | script |
| `baseline.threshold`: the threshold the script picked | | | script |
| `baseline.recall`: recall at that threshold, on its own test rows | | | script |
| `baseline.precision`: precision at that threshold, on its own test rows | | | script |
| `baseline.decline_rate`: the decline rate the script expects at its threshold | | | script |
| `change.pr_auc`, from your copy after each fix | | | script |
| `change.threshold`, from your copy after each fix | | | script |
| `change.recall`, from your copy after each fix | | | script |
| `change.precision`, from your copy after each fix | | | script |
| `change.decline_rate`, from your copy after each fix | | | script |
| `break.shipped_pr_auc_next`: the shipped model's PR-AUC on next month's traffic, from the reference `--break` | | | script |
| `break.shipped_recall_next`: the shipped model and threshold, recall on next month's traffic, from the reference `--break` | | | script |
| `break.shipped_precision_next`: the shipped model and threshold, precision on next month's traffic, from the reference `--break` | | | script |
| `P3.decline_rate_next`: the shipped model and threshold, decline rate on next month's traffic, from the reference `--break` (your P3 answer) | | | script |
| `P1.honest_pr_auc`: the corrected pipeline's PR-AUC on next month's traffic, from the reference `--break` (your P1 answer) | | | script |
| `break.honest_threshold`: the corrected pipeline's threshold, from the reference `--break` | | | script |
| `break.honest_recall_next`: the corrected pipeline's recall on next month's traffic, from the reference `--break` | | | script |
| `break.honest_precision_next`: the corrected pipeline's precision on next month's traffic, from the reference `--break` | | | script |
| `break.honest_decline_rate_next`: the corrected pipeline's decline rate on next month's traffic, from the reference `--break` | | | script |
| The other reference `--break` lines: the diagnostics and the effect of each single fix, unnamed and uncounted here because their names and number would give the audit away (the AI pastes them after your audit) | | | script |
| Each bug you found: where it is, the highest hint you used, the minutes it took | | | learner |
