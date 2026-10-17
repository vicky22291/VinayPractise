# 13. Two-stage retrieval, then ranking: how much can the re-ranker recover?

> Goal: after this I can build a 2-stage recommender on 1 M ratings and measure its recall ceiling, what re-ranking changes and its p99 (99th percentile) latency per request. (No result values anywhere in this file.)

**Level:** C (see `ml-learning/CLAUDE.md`). **Output style:** Learning
**Concept link:** [`../README.md#two-stage-retrieval-and-ranking`](../README.md#two-stage-retrieval-and-ranking) (read after the lab)
**Borrowed from:** [Covington et al. 2016, Deep Neural Networks for YouTube Recommendations](https://static.googleusercontent.com/media/research.google.com/en//pubs/archive/45530.pdf) (candidate generation, then ranking); [FAISS (Facebook AI Similarity Search), arXiv 1702.08734](https://arxiv.org/abs/1702.08734); [HNSW (hierarchical navigable small world graphs), arXiv 1603.09320](https://arxiv.org/abs/1603.09320); on feedback loops, [Chaney et al. 2017, arXiv 1710.11214](https://arxiv.org/abs/1710.11214) and [Rules of ML #36](https://developers.google.com/machine-learning/guides/rules-of-ml#rule_36_avoid_feedback_loops_with_positional_features). Do it after the lab, as the second contact 1 to 3 days later.
**Dataset:** MovieLens 1M, 1,000,209 ratings by 6,040 users of 3,706 movies, 5.92 MB zip, [ml-1m.zip](https://files.grouplens.org/datasets/movielens/ml-1m.zip) from [GroupLens](https://grouplens.org/datasets/movielens/), research use only (no redistribution, no commercial use: see the README in the zip). Stretch, not captured: MovieLens 32M, 87,585 movies, 238.95 MB, [ml-32m.zip](https://files.grouplens.org/datasets/movielens/ml-32m.zip), same terms.
**Runs on:** cpu. **Lane:** light. **Compute:** 3 runs x 1 min (plus `--check`, seconds), at most 6 min per run. Precomputed steps: none
**Needs:** base install only (scikit-learn and LightGBM are in the base). Stretch only: `python -m pip install faiss-cpu==1.15.1`
**Before the session** (from the module folder, see section 2): `--download` (5.92 MB into `~/ml-data/movielens/`), then `--smoke`. No human steps before the session.
**Interview question:** Pick 10 movies per user from about 3,900 for 6,040 users, then from 10 M items for 200 M users under 100 ms: what recall does the candidate stage cost, and what does ANN (approximate nearest neighbour search) cost on top?
**Repo link:** [`hld/news-aggregator/deep-dives/ranking-and-cold-start.md`](../../../hld/news-aggregator/deep-dives/ranking-and-cold-start.md#1-candidate-lanes), section 1 "Candidate lanes" and [section 8 "Feedback loops and popularity bias"](../../../hld/news-aggregator/deep-dives/ranking-and-cold-start.md#8-feedback-loops-and-popularity-bias); [`concepts/vector-index.md`](../../../concepts/vector-index.md#2-hnsw-the-one-to-explain-on-a-whiteboard), section 2 "HNSW: the one to explain on a whiteboard".
**Captured by the script:** baseline, change and break: P1 to P3 and every Record row except the stretch rows. **Human steps:** the TODO(human) bodies of `recall_at_k()` and `ndcg_at_k()`; the optional stretch after the session (`--stretch`: exact vs HNSW on MovieLens 32M, downloads 239 MB on first run, needs faiss-cpu, not captured).
**Status:** todo

## 0. Retrieval (0:00, 5 min, closed book, no AI)

The AI asks up to three due cards from `../../quiz-bank.md`, one at a time. Do not open the bank first.

## 1. Predict (0:05, 7 min, no AI)

Read `scripts/13_two_stage_retrieval_and_ranking.py` for 4 minutes first: the two TODO(human) docstrings, then `snapshot()`, `retrieve()`, `features()`, `train_ranker()`, `evaluate()` and `main()`. The helpers below `main()` (download, the smoke stand-ins, `--check`, `--stretch`) can wait. Your TODO(human): the bodies of `recall_at_k()` and `ndcg_at_k()`; you write them at 0:12.

The time windows: T1 is the 80th and T2 the 90th percentile of rating time. A positive is a rating of 4 or 5. nDCG@10 is normalized discounted cumulative gain over the top 10, with binary gains.

Write each row here before anything runs; the AI copies it into `../../prediction-log.md` word for word. A row that asks for several numbers becomes one log row per number, each with its own range.

| Step | Question | Kind | Prediction | 80% range or confidence |
|---|---|---|---|---|
| P1 | recall@100 of the candidate stage: TruncatedSVD (a truncated singular value decomposition, 64 dimensions, seed 0) of the implicit user x movie matrix before T2, top 100 movies per user by dot product with seen movies removed, scored on each user's positives after T2, mean over users | num | | |
| P2 | Re-rank those 100 candidates with LightGBM lambdarank (library default settings, nothing tuned: 100 trees of 31 leaves, learning rate 0.1; 5 features, trained on positives in [T1, T2), seed 0): direction and size of the change in nDCG@10 versus the candidate order (`P2.ndcg_delta`, an absolute difference) | dir | | |
| P3 | Pass only the top 10 candidates to the same re-ranker (same model, seed 0): the change in nDCG@10 versus the candidate order (`P3.ndcg_delta`, an absolute difference) | num | | |

## 2. Setup (before the session)

```
$ source ~/.venvs/ml/bin/activate
$ cd m3-more-of-the-map    # from ml-learning/, where sessions start
$ python scripts/13_two_stage_retrieval_and_ranking.py --download
$ python scripts/13_two_stage_retrieval_and_ranking.py --smoke
```

## 3. Baseline (0:12, 10 min)

Why: a movie the candidate stage drops is a movie no re-ranker can show, so its recall bounds everything after it.

Write the TODO first: the bodies of `recall_at_k()` and `ndcg_at_k()` in `scripts/13_two_stage_retrieval_and_ranking.py`. Run `--check` until it prints `check: PASS`, then run the baseline.

```
$ python scripts/13_two_stage_retrieval_and_ranking.py --check
$ python scripts/13_two_stage_retrieval_and_ranking.py --baseline
(paste your RESULT lines)
```

Prediction vs actual, one sentence. The reference run is in `../../answers/`; the AI opens it only after your P1 row exists and you have pasted your own RESULT lines.

## 4. Change one thing (0:22, 10 min)

Why: a second model can reorder the candidates with signals one dot product does not carry.

Change: re-rank the 100 candidates with a LightGBM lambdarank ranker at the library default settings (100 trees of 31 leaves, learning rate 0.1, nothing tuned) on five features known before the cutoff: candidate score, movie popularity, movie mean rating, user activity and genre overlap. It trains on each user's 100 candidates from a model fit before T1, labelled by that user's positives in [T1, T2). The run also prints nDCG@10 for the same 100 candidates sorted by popularity alone (`change.popsort_ndcg_at_10`), the simplest re-ranker, as a reference point. P2 is logged above.

```
$ python scripts/13_two_stage_retrieval_and_ranking.py --change
(paste your RESULT lines)
```

## 5. Break it (0:32, 10 min, AI gives hints only; the run finishes by 0:40)

Why: the candidate count is the hand-off between the two stages, and it is the first knob a serving team turns.

Break: pass only the top 10 candidates to the same re-ranker, instead of 100. P3 is logged above.

```
$ python scripts/13_two_stage_retrieval_and_ranking.py --break
(paste your RESULT lines)
```

Why, in three sentences, written without AI:

## 6. Explain-back (0:42, 5 min) and rebuild (0:47, 10 min), no AI

- Five sentences for a smart engineer new to ML, written without AI. The AI names your weakest claim after the session (section 7).
- Rebuild: open `rebuild/13_retrieval_metrics.py`, write the four bodies (`exact_topk`, `recall_at_k`, `ndcg_at_k`, `ann_recall`) from memory in that file, then run `python rebuild/13_retrieval_metrics.py`. Its `check()` compares with numpy's full `argsort` and with scikit-learn's `ndcg_score` and `recall_score`, never with this lab's results.

## 7. What I learned

After the session (about 5 minutes): the AI names the weakest claim in your five sentences and asks one question that tests it. Edit the sentences here.

## 8. Interview soundbite (one of the three cards written at 0:57)

> One or two sentences only someone who ran this would say.

Staff follow-up (failure modes): the re-ranker learns only from movies the candidate stage put in front of it, and next month's training data comes from what this ranker showed. What loop does that build, and what do you add to break it? Answer in 2 sentences from the repo link (ranking-and-cold-start section 8).

## 9. Quiz cards (0:57, 3 min)

The AI drafts three cards (M, N, and T or D). Edit or replace them. Questions go to `../../quiz-bank.md`, keys to `../../answers/quiz-key.md`.

## Record

The script prints these as RESULT lines. Paste, do not type. The stretch rows come from `python scripts/13_two_stage_retrieval_and_ranking.py --stretch`, after the session; every stretch search runs one query at a time on one thread.

| Metric | Your run | Hardware (the script's HW line) | Captured by (script or learner) |
|---|---|---|---|
| P1.recall_at_100 (candidate stage) | | | script |
| baseline.recall_at_10 (candidate stage) | | | script |
| baseline.ndcg_at_10 (candidate order) | | | script |
| baseline.p50_ms (candidate stage, one user at a time) | | | script |
| baseline.p99_ms (candidate stage, one user at a time) | | | script |
| P2.ndcg_at_10 (re-ranked from 100) | | | script |
| P2.ndcg_delta (re-ranked from 100 minus candidate order) | | | script |
| change.recall_at_10 (re-ranked from 100) | | | script |
| change.popsort_ndcg_at_10 (the 100 candidates sorted by popularity alone) | | | script |
| change.p50_ms (candidates plus re-rank of 100) | | | script |
| change.p99_ms (candidates plus re-rank of 100) | | | script |
| P3.ndcg_delta (re-ranked from 10 minus candidate order) | | | script |
| break.ndcg_at_10 (re-ranked from 10) | | | script |
| break.recall_at_10 (re-ranked from 10) | | | script |
| break.p50_ms (candidates plus re-rank of 10) | | | script |
| break.p99_ms (candidates plus re-rank of 10) | | | script |
| stretch.exact_p50_ms (MovieLens 32M, exact search) | | | learner (stretch, not captured) |
| stretch.exact_p99_ms (MovieLens 32M, exact search) | | | learner (stretch, not captured) |
| stretch.hnsw_ef16_recall_at_10 | | | learner (stretch, not captured) |
| stretch.hnsw_ef16_p50_ms | | | learner (stretch, not captured) |
| stretch.hnsw_ef16_p99_ms | | | learner (stretch, not captured) |
| stretch.hnsw_ef64_recall_at_10 | | | learner (stretch, not captured) |
| stretch.hnsw_ef64_p50_ms | | | learner (stretch, not captured) |
| stretch.hnsw_ef64_p99_ms | | | learner (stretch, not captured) |
| stretch.hnsw_ef256_recall_at_10 | | | learner (stretch, not captured) |
| stretch.hnsw_ef256_p50_ms | | | learner (stretch, not captured) |
| stretch.hnsw_ef256_p99_ms | | | learner (stretch, not captured) |
