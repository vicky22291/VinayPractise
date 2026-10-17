# 12. Lexical vs dense retrieval: BM25, embeddings and fusion

> Goal: after this I can score BM25 (Best Matching 25, the Okapi ranking function), a dense embedding model and a hybrid of the two on 300 SciFact queries with nDCG@10 (normalized discounted cumulative gain over the top 10, with binary gains), and explain what embedding the documents and the queries with two different models does to retrieval. (No result values anywhere in this file.)

**Level:** C (see `ml-learning/CLAUDE.md`). **Output style:** Learning
**Concept link:** [`../README.md#lexical-vs-dense-retrieval`](../README.md#lexical-vs-dense-retrieval) (read after the lab)
**Borrowed from:** BEIR, a zero-shot information retrieval benchmark (Thakur et al. 2021, [arXiv 2104.08663](https://arxiv.org/abs/2104.08663)); this repo's rag-react exercises [04 measure retrieval](../../../tool-practise/rag-react/exercises/04-measure-retrieval.md) and [05 hybrid and filters](../../../tool-practise/rag-react/exercises/05-hybrid-and-filters.md). Do it after the lab, as the second contact 1 to 3 days later.
**Dataset:** BEIR SciFact, 5,183 documents (scientific abstracts) and 300 test queries (claims) with qrels (relevance judgements), 4.5 MB, [BeIR/scifact](https://huggingface.co/datasets/BeIR/scifact) plus [BeIR/scifact-qrels](https://huggingface.co/datasets/BeIR/scifact-qrels) (fallback: the BEIR zip from public.ukp.informatik.tu-darmstadt.de), Hugging Face tag cc-by-sa-4.0 (the BEIR paper lists CC BY-NC 2.0). Models: sentence-transformers/all-MiniLM-L6-v2 and BAAI/bge-small-en-v1.5, both ungated.
**Runs on:** cpu. **Lane:** light. **Compute:** 3 runs x 2 min (baseline, change, break), plus `--check` in seconds, at most 6 min per run. Precomputed steps: none
**Needs:** `python -m pip install sentence-transformers==6.1.0 bm25s==0.3.11`
**Before the session** (from the module folder, see section 2): `--download` (about 4.5 MB of SciFact and about 226 MB of models into `~/ml-data`), then `--smoke`. No Ollama.
**Interview question:** Design search over 5,000 help articles: BM25, embeddings or hybrid, and which offline metric tells you a change helped before users see it?
**Repo link:** [`concepts/rag-and-react.md`, section 3 "Retrieval quality: dense, sparse, hybrid, rerank"](../../../concepts/rag-and-react.md#3-retrieval-quality-dense-sparse-hybrid-rerank) and section 4 ["Evaluation and migration"](../../../concepts/rag-and-react.md#4-evaluation-and-migration) (open at close, for the Staff follow-up).
**Captured by the script:** P1 to P3 and every Record row except the BM25 gap row (nDCG@10 for BM25, dense, hybrid and mismatched models; the hybrid's delta and its 95% interval; documents embedded per second). **Human steps:** the BM25 gap row in the Record table (you also write `bm25_scores()` before the baseline, section 3).
**Status:** todo

## 0. Retrieval (0:00, 5 min, closed book, no AI)

The AI asks up to three due cards from `../../quiz-bank.md`, one at a time. Do not open the bank first.

## 1. Predict (0:05, 7 min, no AI)

Level C: the TODO is `bm25_scores()` in `scripts/12_lexical_vs_dense_retrieval.py`. You write it at 0:12, before the baseline. Predict first.

Write each row here before anything runs; the AI copies it into `../../prediction-log.md` word for word. A row that asks for several numbers becomes one log row per number, each with its own range.

| Step | Question | Kind | Prediction | 80% range or confidence |
|---|---|---|---|---|
| P1 | nDCG@10 of sentence-transformers/all-MiniLM-L6-v2 (384-dimensional, cosine on normalized embeddings, seed 0) on the 300 SciFact test queries. BEIR published BM25 at 0.665 and a dense model trained elsewhere at 0.318. | num | | |
| P2 | Fuse the BM25 ranking (k1 = 1.2, b = 0.75) and the MiniLM ranking with reciprocal rank fusion (RRF, k = 60) over each method's top 100, seed 0: direction and size of the hybrid's nDCG@10 minus the better of BM25 and MiniLM (`P2.delta_vs_best`, an absolute difference on the 0 to 1 scale) | dir | | |
| P3 | Documents embedded with all-MiniLM-L6-v2 and queries with BAAI/bge-small-en-v1.5 (both 384-dimensional, no query instruction prefix), same 300 queries, seed 0: nDCG@10 | num | | |

## 2. Setup (before the session)

```
$ source ~/.venvs/ml/bin/activate
$ cd m3-more-of-the-map    # from ml-learning/, where sessions start
$ python -m pip install sentence-transformers==6.1.0 bm25s==0.3.11
$ python scripts/12_lexical_vs_dense_retrieval.py --download
$ python scripts/12_lexical_vs_dense_retrieval.py --smoke
```

## 3. Baseline (0:12, 10 min)

Why: score the lexical baseline (word counts, no model to train or run) and the embedding model on the same 300 queries and the same metric before trusting either one.

First write the TODO: fill in `bm25_scores()` from its docstring, then run `--check` until it prints `check: PASS`. The AI may give hints, or a draft explained line by line that you type. Then run the baseline.

```
$ python scripts/12_lexical_vs_dense_retrieval.py --check
$ python scripts/12_lexical_vs_dense_retrieval.py --baseline
(paste your RESULT lines)
```

Prediction vs actual, one sentence. The reference run is in `../../answers/`; the AI opens it only after your P1 row exists and you have pasted your own RESULT lines.

## 4. Change one thing (0:22, 10 min)

Why: BM25 scores and cosine similarities live on different scales, so the fusion uses ranks only.

Change: fuse the BM25 and dense rankings with reciprocal rank fusion (k = 60) over each method's top 100. P2 is logged above.

```
$ python scripts/12_lexical_vs_dense_retrieval.py --change
(paste your RESULT lines)
```

## 5. Break it (0:32, 10 min, AI gives hints only; the run finishes by 0:40)

Why: after a partial model upgrade, an index built with one embedding model gets queried with another, and nothing in the code checks that.

Break: embed the documents with all-MiniLM-L6-v2 and the queries with BAAI/bge-small-en-v1.5. Both are 384-dimensional. P3 is logged above.

```
$ python scripts/12_lexical_vs_dense_retrieval.py --break
(paste your RESULT lines)
```

Why, in three sentences, written without AI:

## 6. Explain-back (0:42, 5 min) and rebuild (0:47, 10 min), no AI

- Five sentences for a smart engineer new to ML, written without AI. The AI names your weakest claim after the session (section 7).
- Rebuild: open `rebuild/12_bm25.py`, write `tokenize()` and `bm25_scores()` from memory, then run `python rebuild/12_bm25.py`. Its `check()` compares rank order with bm25s 0.3.11 (`method='lucene'`), never with this lab's results. Optional, if time is left: add `rrf(rankings, k=60)` (about 6 lines) and test it by hand on two short lists.

## 7. What I learned

After the session (about 5 minutes): the AI names the weakest claim in your five sentences and asks one question that tests it. Edit the sentences here.

## 8. Interview soundbite (one of the three cards written at 0:57)

> One or two sentences only someone who ran this would say.

Staff follow-up (migration): you switch the 5,000 help articles to a new embedding model. How do you swap indexes with zero downtime and a rollback path, and what gate stops a bad swap? Answer in 2 sentences from the repo link. Rotate: simplest design, failure modes, migration, what pages at 3 am, cost, trade-off.

## 9. Quiz cards (0:57, 3 min)

The AI drafts three cards (M, N, and T or D). Edit or replace them. Questions go to `../../quiz-bank.md`, keys to `../../answers/quiz-key.md`.

## Record

The script prints these as RESULT lines. Paste, do not type.

| Metric | Your run | Hardware (the script's HW line) | Captured by (script or learner) |
|---|---|---|---|
| `baseline.ndcg10_bm25`: nDCG@10 for BM25, ours (English stopwords, no stemmer; BEIR published 0.665) | | | script |
| `P1.ndcg10_dense`: nDCG@10 for all-MiniLM-L6-v2 | | | script |
| `baseline.docs_per_s`: documents embedded per second on the CPU (central processing unit; batch 64, median of 10 chunks) | | | script |
| `P2.ndcg10_hybrid`: nDCG@10 for RRF (k = 60) over each method's top 100 | | | script |
| `P2.delta_vs_best`: hybrid minus the better single method | | | script |
| `change.delta_ci95_low`: low end of the 95% interval of that delta (2,000 resamples of the 300 queries) | | | script |
| `change.delta_ci95_high`: high end of the same interval | | | script |
| `P3.ndcg10_mismatched`: nDCG@10 for MiniLM documents with bge-small queries | | | script |
| Our BM25 vs the published 0.665: the gap and one reason | | | learner |
