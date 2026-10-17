# 03. Tabular in ten minutes: majority baseline, logistic regression and LightGBM

> Goal: after this I can train and compare three models on a 48,842-row table in under 2 minutes, and say what a shuffled-target AUC (area under the receiver operating characteristic curve) tells me about a pipeline. (No result values anywhere in this file.)

**Level:** W (see `ml-learning/CLAUDE.md`). **Output style:** Explanatory
**Concept link:** [`../README.md#tabular-baselines-and-gradient-boosted-trees`](../README.md#tabular-baselines-and-gradient-boosted-trees) (read after the lab)
**Borrowed from:** fast.ai [Lesson 6](https://course.fast.ai/Lessons/lesson6.html); Kaggle [Intro to Machine Learning](https://www.kaggle.com/learn/intro-to-machine-learning); the [TabPFN README](https://github.com/PriorLabs/TabPFN) (TabPFN: Tabular Prior-data Fitted Network) for the optional section. Do it after the lab, as the second contact 1 to 3 days later.
**Dataset:** Adult census income (OpenML 1590), 48,842 rows, 14 features, target `class` (`<=50K` or `>50K`), 0.66 MB download, https://www.openml.org/d/1590, OpenML 'Public'; the UCI (University of California Irvine) Machine Learning Repository original is CC BY 4.0 (Creative Commons Attribution)
**Runs on:** cpu. **Lane:** light. **Compute:** 3 runs x 1 min, plus the optional `--tabpfn` run x 5 min, at most 6 min per run. Precomputed steps: none
**Needs:** base install only. The optional `--tabpfn` section needs `python -m pip install tabpfn==9.2.0`
**Before the session** (from the module folder, see section 2): run `--download` and `--smoke` (section 2). For the optional section, install tabpfn first, so `--download` also fetches the TabPFN v2 weights (29.0 MB, no login).
**Interview question:** What is your first model for a new fraud problem, what baseline must it beat, and what evidence would make you move off gradient-boosted trees?
**Repo link:** `hld/payments-risk-decisioning/solution.md`: [§7 Trade-offs](../../../hld/payments-risk-decisioning/solution.md#7-trade-offs), rows "Model family inline" and "Model release", and [§10.8 How the big companies do it](../../../hld/payments-risk-decisioning/solution.md#108-how-the-big-companies-do-it)
**Captured by the script:** baseline, change, break, and the optional `--tabpfn` section. **Human steps:** none in the session. Optional and uncaptured: TabPFN 3.5 with your own Prior Labs login (see the optional section)
**Status:** todo

## 0. Retrieval (0:00, 5 min, closed book, no AI)

The AI asks up to three due cards from `../../quiz-bank.md`, one at a time. Do not open the bank first.

## 1. Predict (0:05, 7 min, no AI)

Level W only: before the session, read `scripts/03_tabular_in_ten_minutes.py` (about 10 minutes) and answer its three `# Q:` prompts here. At 0:05 you only predict. Read the concept functions `logreg`, `lgbm`, `auc_pairwise`, `auc_rank`, `score`, `baseline`, `change` and `break_it`. Skip the data loader and the TabPFN code.

1. Why does the StandardScaler sit inside the pipeline instead of scaling the whole table once before the split?
2. Why does LightGBM need no one-hot step for the category columns, when logistic regression does?
3. What does accuracy score here, what does AUC score, and when can the two disagree?

Write each row here before anything runs; the AI copies it into `../../prediction-log.md` word for word. A row that asks for several numbers becomes one log row per number, each with its own range.

All three steps score on the same 9,769 test rows: a stratified 80/20 split, seed 0. One AUC point is 0.01 AUC. P1 asks for two numbers: write each with its own 80% range. A hit needs both inside their ranges, and Off by uses the AUC.

| Step | Question | Kind | Prediction | 80% range or confidence |
|---|---|---|---|---|
| P1 | LightGBM with defaults (100 trees, 31 leaves, learning rate 0.1) trained on all 39,073 training rows, seed 0. Two numbers, each with its own 80% range: (a) its test AUC; (b) the gap in AUC points, LightGBM AUC minus logistic regression AUC (StandardScaler and one-hot in a pipeline, max_iter 2000), negative if logistic regression is ahead | num | (a) (b) | (a) (b) |
| P2 | The same LightGBM trained on a stratified random 5,000 of the 39,073 training rows, seed 0: AUC direction (up, down or same) and size in AUC points against P1 | dir | | |
| P3 | The same LightGBM on all 39,073 training rows, but trained on the target column shuffled at seed 0, then scored against the true test labels: test AUC | num | | |

## 2. Setup (before the session)

```
$ source ~/.venvs/ml/bin/activate
$ cd m1-whole-game    # from ml-learning/, where sessions start
$ python scripts/03_tabular_in_ten_minutes.py --download
$ python scripts/03_tabular_in_ten_minutes.py --smoke
```

## 3. Baseline (0:12, 10 min)

Why: a majority baseline and logistic regression set the bar a tree model is measured against on the same test rows.

```
$ python scripts/03_tabular_in_ten_minutes.py --baseline
(paste your RESULT lines)
```

Prediction vs actual, one sentence. The reference run is in `../../answers/`; the AI opens it only after your P1 row exists and you have pasted your own RESULT lines.

## 4. Change one thing (0:22, 10 min)

Why: fraud labels take 60 to 90 days to mature, so measure what training-set size does to AUC before you plan a launch around it.

Change: LightGBM trains on a stratified random 5,000 of the 39,073 training rows. Its settings and the 9,769 test rows stay the same. P2 is logged above.

```
$ python scripts/03_tabular_in_ten_minutes.py --change
(paste your RESULT lines)
```

## 5. Break it (0:32, 10 min, AI gives hints only; the run finishes by 0:40)

Why: before you trust any AUC, know what this exact pipeline reports when the training labels are shuffled.

Break: shuffle the target column of the training set, retrain LightGBM with the same settings, and score it against the true test labels. P3 is logged above.

```
$ python scripts/03_tabular_in_ten_minutes.py --break
(paste your RESULT lines)
```

Why, in three sentences, written without AI:

## 6. Explain-back (0:42, 5 min) and rebuild (0:47, 10 min), no AI

- Five sentences for a smart engineer new to ML, written without AI. The AI names your weakest claim after the session (section 7).
- Rebuild: open `rebuild/03_auc.py`, write the bodies of `auc_pairwise` and `auc_rank` from memory (the AUC block you read in the script at 0:05), then run `python rebuild/03_auc.py`. Its `check()` compares with scikit-learn's `roc_auc_score` on scores with forced ties, never with this lab's results.

## 7. What I learned

After the session (about 5 minutes): the AI names the weakest claim in your five sentences and asks one question that tests it. Edit the sentences here.

## 8. Interview soundbite (one of the three cards written at 0:57)

> One or two sentences only someone who ran this would say. Write yours from your own RESULT lines.

Staff follow-up (migration): "A deep neural network (DNN) now beats the inline GBDT (gradient-boosted decision trees) offline on matured labels. How do you move it onto the payment path with a rollback, without wrongly blocking more legitimate payments?" Answer in 2 sentences from the repo link: §7, rows "Model release" and "Model family inline". Rotate: simplest design, failure modes, migration, what pages at 3 am, cost, trade-off.

## 9. Quiz cards (0:57, 3 min)

The AI drafts three cards (M, N, and T or D). Edit or replace them. Questions go to `../../quiz-bank.md`, keys to `../../answers/quiz-key.md`.

## Optional: TabPFN v2 on 1,000 rows (after the session)

Do this section with the second contact, 1 to 3 days after the lab: run `--tabpfn`, then read the TabPFN README.

TabPFN is a transformer pretrained on synthetic tables. It reads the training rows as context and predicts the test rows with no training loop. Version 2's weights are ungated. Versions 2.5 to 3.5 need a Prior Labs browser login, so the script and the reference run use v2 only. Trying TabPFN 3.5 with your own login is an optional human step: the build never ran it, so the answer file holds no value for it. On a CPU (central processing unit), v2 accepts at most 1,000 training rows by default, so LightGBM gets the same 1,000 rows here.

Needs `python -m pip install tabpfn==9.2.0`, then `--download` once for the weights. The script runs torch on one thread, because LightGBM and torch load two different OpenMP (Open Multi-Processing) runtimes that deadlock otherwise.

```
$ python scripts/03_tabular_in_ten_minutes.py --tabpfn
(paste your RESULT lines)
```

## Record

The script prints these as RESULT lines. Paste, do not type.

| Metric | Your run | Hardware (the script's HW line) | Captured by (script or learner) |
|---|---|---|---|
| `baseline.acc_majority`: accuracy of always predicting `<=50K` | | | script |
| `baseline.auc_majority`: AUC of the majority model | | | script |
| `baseline.acc_logreg`: logistic regression accuracy | | | script |
| `baseline.auc_logreg`: logistic regression AUC | | | script |
| `baseline.acc_lgbm`: LightGBM accuracy, 39,073 training rows | | | script |
| `P1.auc_lgbm`: LightGBM AUC, 39,073 training rows | | | script |
| `P1.gap_vs_logreg_points`: LightGBM AUC minus logistic regression AUC, in AUC points | | | script |
| `P2.auc_5000_rows`: LightGBM AUC, 5,000 training rows | | | script |
| `P2.delta_points`: P2 minus P1, in AUC points (printed when `--baseline` ran first with the same seed) | | | script |
| `P3.auc_shuffled`: LightGBM AUC after training on the shuffled target | | | script |
| `tabpfn.auc_lgbm_1000_rows`: LightGBM AUC, the same 1,000 training rows (optional) | | | script |
| `tabpfn.auc_tabpfn_1000_rows`: TabPFN v2 AUC, the same 1,000 training rows (optional) | | | script |
