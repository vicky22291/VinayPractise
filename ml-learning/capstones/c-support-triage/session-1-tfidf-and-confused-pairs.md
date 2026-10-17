# C1. TF-IDF intent classifier and its most confused intent pairs

> Goal: after this I can train a TF-IDF (term frequency, inverse document frequency) plus logistic regression classifier on 10,003 BANKING77 queries, report accuracy and macro-F1 on all 3,080 test queries, and name the 10 intent pairs it confuses most. (No result values anywhere in this file. Capstones have no reference run and no answers file: your run is the answer.)

**Capstone:** [C, support triage with retrieval and a small LLM](README.md), session 1 of 4, labkit id 49. **Level:** B (see `ml-learning/CLAUDE.md`). **Output style:** Explanatory
**Builds on:** lab 04 (TF-IDF as the bar a bigger model must beat, and ms per 1,000 items)
**Dataset:** BANKING77, 10,003 train and 3,080 test queries, 77 intents, 1.1 MB of CSV, CC BY 4.0 ([Data](README.md#data))
**Runs on:** cpu. **Lane:** light. **Compute:** no reference run; 2 measured runs, each capped at 6 min. Precomputed steps: none
**Needs:** base install only (scikit-learn and scipy are in it)
**Before the session:** `--download` (both CSVs into `~/ml-data/banking77/`), then `--smoke`.
**Interview question:** Route 13,000 banking support queries to 77 intents: what is your first model, and where does it fail?
**Repo link:** [`hld/financial-ai-assistant/solution.md`, §5.6 "The LLM provider is down. What still works?": availability](../../../hld/financial-ai-assistant/solution.md#56-the-llm-provider-is-down-what-still-works-availability) (the local intent matcher, keywords plus a small classifier, ~5 ms)
**Captured by the script:** P1 to P3 and every Record row. **Human steps:** the framing sprint, the design and the write-up
**Status:** todo

## 0. Framing (0:00, 7 min, no AI except as the interviewer)

**0:00 to 0:05, the framing sprint.** Tell the AI "play the interviewer for a support-query router". Propose and confirm, by the rule in [`scoping-drills/README.md`](../../../scoping-drills/README.md#3-drill-2-propose-and-confirm) §3: state each assumption, attach its consequence, invite correction, and ask at most one open question. Cover what a routed query triggers (a team queue, a help article, an automated flow), when the route is chosen, which misroute must never happen, and the failure default when the router is down. The AI confirms or corrects in one line each, and never proposes a metric.

**0:05 to 0:07, the framing line.** It opens `write-up.md` at 0:42.

decision ___ | prediction time ___ | label and its maturity ___ | offline metric ___ | online metric ___ | guardrail ___

## 1. Predict (0:07, 5 min, no AI)

Write each row here and in `../../prediction-log.md` (Lab `C1`) before anything runs. Accuracy is a percent; its changes are in points.

| Step | Question | Kind | Prediction | 80% range or confidence |
|---|---|---|---|---|
| P1 | Test accuracy on the 3,080 queries of `TfidfVectorizer()` (word unigrams, scikit-learn defaults) plus `LogisticRegression(max_iter=2000)`, trained on the 10,003 train queries | num | | |
| P2 | Character 2- to 5-grams instead of words, `TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5))`, the same classifier: accuracy minus P1 (up, down or same, plus a size range), and the flips each way | dir | | |
| P3 | The share of the word model's test errors that fall inside its 10 most confused intent pairs, as a percent | num | | |

Terms, fixed so sessions 2 to 4 compare with this one:

- **Macro-F1.** The plain mean of the 77 per-intent F1 scores, `sklearn.metrics.f1_score(average="macro")`. Recorded with every accuracy.
- **Confused pair.** An unordered pair {gold intent, predicted intent}. Its count is the errors in both directions. The top 10 by count, ties broken by name.
- **Flips.** Test queries that one model gets right and the other wrong. To right: the word model wrong, the character model right. To wrong: the reverse.
- **Sign test.** The exact two-sided binomial test of the to-right flips out of all flips at p = 0.5, `scipy.stats.binomtest`.
- **Seconds per 1,000 queries.** Predict time on the CPU for all 3,080 test queries, the median of 5 runs, scaled to 1,000. The fit time is recorded apart.
- **Saved for later (seed 0 only).** Each test query's word-model prediction and its probability, to `~/ml-data/capstones/c/`. Sessions 2 to 4 read them.

## 2. Setup (before the session)

```
$ source ~/.venvs/ml/bin/activate
$ cd ml-learning/capstones/c-support-triage
$ python scripts/c1_tfidf_and_confused_pairs.py --download
$ python scripts/c1_tfidf_and_confused_pairs.py --smoke
```

There is no script until the AI writes one. For the setup it needs only `--download` (both CSVs with their sizes from the README) and `--smoke` (500 train rows, 200 test rows). `--download` prints paths and sizes only.

## 3. Baseline (0:12, 15 min)

Why: a linear model on word counts is the cheapest router that could work, and its errors show where the 77 intents overlap.

You write first, in this file, no AI (about 5 min). This is the prompt the AI builds from:

1. The data and the two metrics, and how the confused pairs are counted.
2. The timing rule for seconds per 1,000 queries.
3. The RESULT contract: every name in the Record table, the mode that prints it, and its unit. The 10 pairs print as TABLE lines.

The AI then writes the script with `labkit.start(lab=49)`. Annotate each AI block with one line before the first run.

```
$ python scripts/c1_tfidf_and_confused_pairs.py --smoke
$ python scripts/c1_tfidf_and_confused_pairs.py --baseline
(paste your RESULT lines)
```

Prediction vs actual, one sentence each for P1 and P3. There is no reference run: the AI fills Actual and Hit from your pasted lines.

## 4. Change one thing (0:27, 15 min; the run finishes by 0:40)

Change: character 2- to 5-grams within word boundaries replace whole words. The classifier, the data and the metrics stay fixed. P2 is logged above.

Why: the change swaps the unit the model counts, words for pieces of words, and leaves everything else alone.

```
$ python scripts/c1_tfidf_and_confused_pairs.py --change
(paste your RESULT lines)
```

Prediction vs actual, one sentence.

## 5. Write-up (0:42, 15 min, no AI)

- **Explain-back (5 min).** Five sentences for a smart engineer new to ML. Then ask the AI for the weakest claim, not a rewrite.
- **Deliverable (10 min).** Start `write-up.md` in this folder: the framing line, the TF-IDF rows of the 4-method table (all 3,080 queries for now), and 2 lines on what the top confused pairs say about the 77 intents: a model problem, or a taxonomy problem?

## 6. What I learned

The five explain-back sentences, edited after the AI's question.

## 7. Interview soundbite (the card written at 0:57)

> One or two sentences only someone who ran this would say.

Framing: decision ___ | prediction time ___ | label and its maturity ___ | offline metric ___ | online metric ___ | guardrail ___

Staff follow-up (simplest design): why is a TF-IDF classifier a sound first router, and where does the HLD keep one even after an LLM router exists? Answer in 2 sentences from the repo link.

## 8. Close (0:57, 3 min)

The AI drafts card `C1-T` (the payments version or a variant you did not run) from your run. Edit or replace it. The question goes to `../../quiz-bank.md`, the key to `../../answers/quiz-key.md`, citing your RESULT line. Set Status here and in the [README](README.md#sessions).

## Record

Suggested names: if your RESULT contract renames them, edit this table first. Paste, do not type.

| Metric | Your run | Hardware (the script's HW line) | Captured by (script or learner) |
|---|---|---|---|
| `baseline.n_train`, `baseline.n_test` and `baseline.n_intents` | | | script |
| `P1.accuracy` (word TF-IDF, percent of 3,080) | | | script |
| `baseline.macro_f1` (word TF-IDF) | | | script |
| `P3.top10_pair_error_share` (percent of the word model's errors) | | | script |
| The 10 most confused pairs with their counts (TABLE lines) | | | script |
| `baseline.fit_s` and `baseline.sec_per_1k` (word TF-IDF, M4 Pro, cpu) | | | script |
| `change.accuracy` and `change.macro_f1` (character n-grams) | | | script |
| `P2.accuracy_change_pts` (character minus word) | | | script |
| `change.flips_to_right`, `change.flips_to_wrong` and `change.sign_test_p` | | | script |
| `change.sec_per_1k` (character n-grams) | | | script |
