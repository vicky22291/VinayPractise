# C2. Embedding kNN vs TF-IDF: all-MiniLM-L6-v2 neighbours on the same queries

> Goal: after this I can classify BANKING77 queries by their 10 nearest training neighbours in all-MiniLM-L6-v2 space, compare that with C1's TF-IDF model on the same 3,080 queries with an exact paired test, repeat both with only 10 training queries per intent, and time the kNN path per 1,000 queries. (No result values anywhere in this file. Capstones have no reference run and no answers file: your run is the answer.)

**Capstone:** [C, support triage with retrieval and a small LLM](README.md), session 2 of 4, labkit id 50. **Level:** B (see `ml-learning/CLAUDE.md`). **Output style:** Explanatory
**Builds on:** lab 12 (dense retrieval with all-MiniLM-L6-v2 on the CPU) and lab 04 (TF-IDF against a pretrained model), plus your C1 model
**Dataset:** BANKING77, 10,003 train and 3,080 test queries, 77 intents, CC BY 4.0 ([Data](README.md#data)); model `sentence-transformers/all-MiniLM-L6-v2` (90.9 MB, Apache-2.0)
**Runs on:** cpu. **Lane:** light. **Compute:** no reference run; 2 measured runs, each capped at 6 min. Precomputed steps: none
**Needs:** `python -m pip install sentence-transformers==6.1.0` (lab 12's pin)
**Before the session:** C1 done at seed 0, so its predictions sit in `~/ml-data/capstones/c/`. `--download` fetches the model into `~/ml-data/hf/` if lab 12 has not, then `--smoke`.
**Interview question:** Embeddings or TF-IDF for intent routing, and what changes when a new intent has only 10 labelled examples?
**Repo link:** [`concepts/rag-and-react.md`, section 3 "Retrieval quality: dense, sparse, hybrid, rerank"](../../../concepts/rag-and-react.md#3-retrieval-quality-dense-sparse-hybrid-rerank); [`hld/financial-ai-assistant/deep-dives/offline-evals-and-rollout.md`, §1 The pipeline](../../../hld/financial-ai-assistant/deep-dives/offline-evals-and-rollout.md#1-the-pipeline)
**Captured by the script:** P1 to P3 and every Record row. **Human steps:** the design and the write-up
**Status:** todo

## 0. Framing (0:00, 7 min, no AI)

Reread your framing line in `write-up.md`. Under it, write one line on what this session changes: what the router compares a new query with, and what a new intent needs before the router can serve it.

## 1. Predict (0:07, 5 min, no AI)

Write each row here and in `../../prediction-log.md` (Lab `C2`) before anything runs. Accuracy differences are in points.

| Step | Question | Kind | Prediction | 80% range or confidence |
|---|---|---|---|---|
| P1 | kNN on all-MiniLM-L6-v2 embeddings (normalized, k = 10, each neighbour's vote weighted by its cosine similarity), all 10,003 train queries as the index: test accuracy minus C1's word TF-IDF accuracy on the same 3,080 queries. Up, down or same, plus a size range | dir | | |
| P2 | Both methods rebuilt on 10 train queries per intent (770 rows, seed 0): kNN accuracy minus TF-IDF accuracy on the 3,080 test queries. Up, down or same, plus a size range | dir | | |
| P3 | Seconds per 1,000 queries for the kNN path on the CPU: embed at batch 64, one matrix product against the train embeddings, then a top 10, the median of 5 runs | num | | |

Terms, fixed so C3 and C4 can reuse these predictions:

- **Embeddings.** `SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", device="cpu")`, `normalize_embeddings=True`, so a dot product is the cosine similarity. 384 dimensions.
- **Vote.** Each of the 10 neighbours adds its cosine similarity to its intent's score; the top score wins, and a tie goes to the intent of the nearest neighbour.
- **10 per intent.** `numpy.random.default_rng(seed)`, 10 train queries per intent without replacement, 770 rows. The TF-IDF model at 770 rows is C1's word model refit on them.
- **Paired test.** Against C1's word model on the same 3,080 queries: flips each way and the exact two-sided sign test, as in C1.
- **Seconds per 1,000.** Wall time on the CPU for all 3,080 test queries, embedding included, scaled to 1,000. The time to embed the 10,003 train queries is recorded apart, as the index build.
- **Saved for later (seed 0 only).** Each test query's kNN prediction, full-data index, to `~/ml-data/capstones/c/`. C3 and C4 read it.

## 2. Setup (before the session)

```
$ source ~/.venvs/ml/bin/activate
$ python -m pip install sentence-transformers==6.1.0
$ cd ml-learning/capstones/c-support-triage
$ python scripts/c2_embedding_knn.py --download
$ python scripts/c2_embedding_knn.py --smoke
```

`--download` checks the BANKING77 files and C1's saved predictions, fetches the model inside `labkit.locked(...)` if it is missing, and prints paths and sizes only.

## 3. Baseline (0:12, 15 min)

Why: neighbours in an embedding space vote by meaning and TF-IDF counts shared words, and the same 3,080 queries decide between them.

You write first, in this file, no AI (about 5 min). This is the prompt the AI builds from:

1. The index, the vote, the tie rule, and the paired test against C1.
2. The timing rule, and what counts as the index build.
3. The RESULT contract: every name in the Record table, the mode that prints it, and its unit.

The AI then writes the script with `labkit.start(lab=50)`. Annotate each AI block with one line before the first run.

```
$ python scripts/c2_embedding_knn.py --smoke
$ python scripts/c2_embedding_knn.py --baseline
(paste your RESULT lines)
```

Prediction vs actual, one sentence each for P1 and P3. There is no reference run: the AI fills Actual and Hit from your pasted lines.

## 4. Change one thing (0:27, 15 min; the run finishes by 0:40)

Change: both methods learn from 10 train queries per intent instead of all 10,003. The test set, k, the vote and the TF-IDF settings stay fixed. P2 is logged above.

Why: a new intent arrives with a handful of labelled examples, so a router has to work at 10 per intent too.

```
$ python scripts/c2_embedding_knn.py --change
(paste your RESULT lines)
```

Prediction vs actual, one sentence.

## 5. Write-up (0:42, 15 min, no AI)

- **Explain-back (5 min).** Five sentences for a smart engineer new to ML. Then ask the AI for the weakest claim, not a rewrite.
- **Deliverable (10 min).** Add the kNN rows to the 4-method table in `write-up.md` (all 3,080 queries for now), the 770-row comparison, and 1 line on what the index costs to rebuild when an intent is added.

## 6. What I learned

The five explain-back sentences, edited after the AI's question.

## 7. Interview soundbite (the card written at 0:57)

> One or two sentences only someone who ran this would say.

Framing: decision ___ | prediction time ___ | label and its maturity ___ | offline metric ___ | online metric ___ | guardrail ___

Staff follow-up (migration): how do you move the router from TF-IDF to embeddings without a big-bang switch, and what does the eval pipeline check first? Answer in 2 sentences from the repo link (§1), then [§6 Shadow without extra reads](../../../hld/financial-ai-assistant/deep-dives/offline-evals-and-rollout.md#6-shadow-without-extra-reads).

## 8. Close (0:57, 3 min)

The AI drafts card `C2-D` (a symptom and the first check) from your run. Edit or replace it. The question goes to `../../quiz-bank.md`, the key to `../../answers/quiz-key.md`, citing your RESULT line. Set Status here and in the [README](README.md#sessions).

## Record

Suggested names: if your RESULT contract renames them, edit this table first. Paste, do not type.

| Metric | Your run | Hardware (the script's HW line) | Captured by (script or learner) |
|---|---|---|---|
| `baseline.accuracy` and `baseline.macro_f1` (kNN, all 10,003 in the index) | | | script |
| `P1.accuracy_gap_pts` (kNN minus C1's word TF-IDF, same 3,080 queries) | | | script |
| `baseline.flips_to_right`, `baseline.flips_to_wrong` and `baseline.sign_test_p` (kNN against TF-IDF) | | | script |
| `baseline.index_build_s` (embedding the 10,003 train queries, M4 Pro, cpu) | | | script |
| `P3.sec_per_1k` (the kNN path, batch 64, median of 5) | | | script |
| `change.accuracy_knn_770` and `change.accuracy_tfidf_770` | | | script |
| `change.macro_f1_knn_770` and `change.macro_f1_tfidf_770` | | | script |
| `P2.accuracy_gap_pts_770` (kNN minus TF-IDF, 770 training rows) | | | script |
| `change.sign_test_p_770` | | | script |
