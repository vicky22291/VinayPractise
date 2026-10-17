# 31. Random forest by hand: one deep tree vs many averaged trees

> Goal: after this I can write the best-split search, build a 100-tree forest by hand in under 2 minutes, and show the single deep tree's train-validation gap. (No result values anywhere in this file.)

**Level:** S (see `ml-learning/CLAUDE.md`). **Output style:** Explanatory
**Concept link:** `../README.md#decision-trees-and-random-forests` (read after the lab)
**Borrowed from:** fast.ai Lesson 6, "How random forests really work" ([lesson 6](https://course.fast.ai/Lessons/lesson6.html), [Kaggle notebook](https://www.kaggle.com/code/jhoward/how-random-forests-really-work)); fastbook ch 9 ([09_tabular.ipynb](https://github.com/fastai/fastbook/blob/master/09_tabular.ipynb)). Do it after the lab, as the second contact 1 to 3 days later.
**Dataset:** Adult census income (OpenML 1590), 48,842 rows and 14 features, 0.66 MB (gzipped ARFF, the Attribute-Relation File Format), https://www.openml.org/d/1590, OpenML "Public" (the original in the UCI, University of California Irvine, Machine Learning Repository is CC BY 4.0). This lab uses lab 03's stratified 80/20 split (39,073 training and 9,769 validation rows, `random_state` = seed) and keeps 10,000 of the training rows. Fallback, only if OpenML is down: fastai ADULT_SAMPLE, 32,561 rows, 0.97 MB, https://s3.amazonaws.com/fast-ai-sample/adult_sample.tgz (same data source and licence; its numbers will not match the reference).
**Runs on:** cpu. **Lane:** light. **Compute:** 3 runs x 1 min, at most 6 min per run. Precomputed steps: none
**Needs:** base install only
**Before the session** (from the module folder, see section 2): `--download`, then `--smoke` (both work on the starter before you write any code)
**Interview question:** Why does averaging 100 deep trees beat one deep tree, and when does adding more trees stop helping?
**Repo link:** [`hld/payments-risk-decisioning/solution.md`, §10.1 Internals of each chosen technology](../../../hld/payments-risk-decisioning/solution.md#101-internals-of-each-chosen-technology), the "GBDT inference" bullet (GBDT: gradient-boosted decision trees)
**Captured by the script:** baseline, change and break (every row of the Record table). **Human steps:** none (you write the forest plan in section 1, and the three contract lines and `best_split()` in section 3)
**Status:** todo

## 0. Retrieval (0:00, 5 min, closed book, no AI)

The AI asks up to three due cards from `../../quiz-bank.md`, one at a time. Do not open the bank first.

## 1. Predict (0:05, 7 min, no AI)

Level S: first read `load_data()` and `report()` in `scripts/31_random_forest_by_hand.py` (2 minutes). They fix the split and the RESULT names your harness must print.

Write each row here before anything runs; the AI copies it into `../../prediction-log.md` word for word. A row that asks for several numbers becomes one log row per number, each with its own range.

| Step | Question | Kind | Prediction | 80% range or confidence |
|---|---|---|---|---|
| P1 | Validation accuracy, as a fraction of the 9,769 validation rows, of your bagged forest at seed 0: 100 trees, each grown on a bootstrap sample of the 10,000 training rows, no depth limit, min_samples_leaf 5, all 14 features considered at every split. The trees' leaf shares are averaged, and an average above 0.5 votes 1 (income over 50K) | num | | |
| P2 | The same forest at seed 0 with 4 random features per split (the square root of 14, rounded up): validation accuracy at 100 trees and out-of-bag error, each against your baseline at the same seed. Write the accuracy change first, then the out-of-bag change, each as up, down or same plus a size range in points. Hit and Off by use only the accuracy change (`P2.valid_acc_change`) | dir | | |
| P3 | One tree on the same 10,000 training rows at seed 0: no bootstrap, no depth limit, min_samples_leaf 1, all 14 features. Train accuracy minus validation accuracy, in points | num | | |

In the last minute, fill in your forest plan, one row per mode. It copies the knobs from P1 to P3, and it opens your prompt in section 3.

| Mode | Trees | Depth limit | Features per split | Min rows per leaf | Bootstrap |
|---|---|---|---|---|---|
| baseline | | | | | |
| change | | | | | |
| break | | | | | |

## 2. Setup (before the session)

```
$ source ~/.venvs/ml/bin/activate
$ cd m5-under-the-hood    # from ml-learning/, where sessions start
$ python scripts/31_random_forest_by_hand.py --download
$ python scripts/31_random_forest_by_hand.py --smoke
```

## 3. Baseline (0:12, 10 min)

Why: it sets the number the change and the break are compared with, and puts the out-of-bag error next to the validation error.

You write first, in this file, no AI (about 3 minutes). With your forest plan from section 1, these lines are the prompt the AI builds from. `load_data()` and `report()` already exist.

- Split: what `load_data()` fixes and what `--seed` changes.
- Metric: how validation accuracy and out-of-bag error are computed.
- RESULT contract: what each mode passes to `report()`.

Then write `best_split(x, y, min_leaf=1)` yourself, in `scripts/31_random_forest_by_hand.py`, from this formula:

- A node with a share p of positives has Gini impurity G = 1 - p² - (1 - p)² = 2p(1 - p).
- A cut that sends n_L rows left and n_R rows right scores (n_L x G_L + n_R x G_R) / n. Lower is better.
- Sort the rows by x. A cumulative sum of the sorted y counts the positives left of every cut. Only cut between two different x values, and leave at least min_leaf rows on each side.
- Score every cut at once with numpy arrays, with no Python loop over rows or cuts. The forest calls `best_split()` for every sampled feature at every node of every tree.
- Return (threshold, weighted Gini) for the best cut, with the threshold at the midpoint of the two x values around it, or (None, inf) when no cut is allowed.

Then the AI writes four blocks from your prompt, using your `best_split()`:

- **The recursion.** A node becomes a leaf, holding its share of positives, when it is pure, has fewer than 2 x min_leaf rows, or reaches the depth limit. Otherwise it draws the plan's number of features at random, without replacement, and splits on the cut with the lowest score. If none of the sampled features allows a cut, the node becomes a leaf too.
- **The prediction.** Each row goes down the tree and gets the share of the leaf it reaches.
- **The voting loop.** Each tree grows on a bootstrap sample of the training rows. The forest averages the trees' leaf shares, and an average above 0.5 votes 1. It records validation accuracy after every tree. A training row's out-of-bag vote comes only from the trees whose bootstrap never drew it.
- **The main block.** At start-up it checks your `best_split()` against scikit-learn's `DecisionTreeClassifier(max_depth=1)` on two training columns, with min_leaf 1 and 5, as `rebuild/31_best_split.py` does, and stops on a mismatch (no random draws). `--smoke` runs your forest in all three modes on the 2,000-row smoke sample, with each plan's tree count capped at 10, in place of the scikit-learn stand-in. Each mode ends with its `report()` call.

Write a one-line annotation above each of the four blocks. Run `python scripts/31_random_forest_by_hand.py --smoke` once, then the baseline. If this block runs over, the change step absorbs it: it is one plan row and one run, so the break still finishes by 0:40.

```
$ python scripts/31_random_forest_by_hand.py --baseline
(paste your RESULT lines)
```

Prediction vs actual, one sentence. The reference run is in `../../answers/`; the AI opens it only after your P1 row exists and you have pasted your own RESULT lines.

## 4. Change one thing (0:22, 10 min)

Change: sample 4 features at random per split instead of all 14. Four is the square root of 14, rounded up; scikit-learn's `max_features="sqrt"` would floor it to 3. The change row of your plan already says this; nothing else moves. It prints the change against your baseline run at the same seed, so run `--baseline` first. P2 is logged above.

Why: sampling features per split is the one thing a random forest adds to bagging. This measures what it changes.

```
$ python scripts/31_random_forest_by_hand.py --change
(paste your RESULT lines)
```

## 5. Break it (0:32, 10 min, AI gives hints only; the run finishes by 0:40)

Break: grow one tree with no depth limit and min_samples_leaf 1, on the 10,000 training rows with no bootstrap. P3 is logged above.

Why: the forest averages deep trees. This grows one tree as deep as the rows allow, on all 10,000 rows, with nothing to average.

```
$ python scripts/31_random_forest_by_hand.py --break
(paste your RESULT lines)
```

Why, in three sentences, written without AI:

## 6. Explain-back (0:42, 5 min) and rebuild (0:47, 10 min), no AI

- Five sentences for a smart engineer new to ML, written without AI. The AI names your weakest claim after the session (section 7).
- Rebuild: open `rebuild/31_best_split.py`, write the body from memory, then run `python rebuild/31_best_split.py`. Its `check()` compares with scikit-learn's `DecisionTreeClassifier(max_depth=1)` (threshold and weighted Gini, to 1e-6), never with this lab's results.

## 7. What I learned

After the session (about 5 minutes): the AI names the weakest claim in your five sentences and asks one question that tests it. Edit the sentences here.

## 8. Interview soundbite (one of the three cards written at 0:57)

> One or two sentences only someone who ran this would say.

Staff follow-up (migration): the team wants to replace the inline GBDT with a random forest like yours. What in the §10.1 scoring path has to be rebuilt and checked before the forest makes its first live decision? Answered in 2 sentences from the repo link. Rotate: simplest design, failure modes, migration, what pages at 3 am, cost, trade-off.

## 9. Quiz cards (0:57, 3 min)

The AI drafts three cards (M, N, and T or D). Edit or replace them. Questions go to `../../quiz-bank.md`, keys to `../../answers/quiz-key.md`.

## Record

The script prints these as RESULT lines. Paste, do not type.

| Metric | Your run | Hardware (the script's HW line) | Captured by (script or learner) |
|---|---|---|---|
| `P1.valid_acc`: validation accuracy, 100 bagged trees, 14 features per split | | | script |
| `baseline.valid_acc_1_tree`: the same forest after its first tree | | | script |
| `baseline.valid_acc_10_trees`: the same forest after 10 trees | | | script |
| `baseline.valid_error`: 1 minus validation accuracy at 100 trees | | | script |
| `baseline.oob_error`: out-of-bag error at 100 trees | | | script |
| `P2.valid_acc`: validation accuracy, 100 trees, 4 features per split | | | script |
| `P2.valid_acc_change`: against the baseline at the same seed, in points | | | script |
| `P2.oob_error`: out-of-bag error, 4 features per split | | | script |
| `P2.oob_error_change`: against the baseline at the same seed, in points | | | script |
| `change.valid_acc_1_tree`: the 4-feature forest after its first tree | | | script |
| `change.valid_acc_10_trees`: the 4-feature forest after 10 trees | | | script |
| `change.valid_error`: 1 minus validation accuracy at 100 trees | | | script |
| `P3.train_minus_valid`: the deep tree's train minus validation accuracy, in points | | | script |
| `break.train_acc`: the deep tree on its own training rows | | | script |
| `break.valid_acc`: the deep tree on the validation rows | | | script |
| `break.leaves`: leaves in the deep tree | | | script |
| `break.depth`: depth of the deep tree | | | script |
