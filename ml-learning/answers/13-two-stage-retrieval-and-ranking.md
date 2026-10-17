# 13. Two-stage retrieval, then ranking: how much can the re-ranker recover?: reference answers

> Spoilers. The AI opens one block at a time, only after that step's prediction row exists and the learner pasted their own RESULT lines, or after 'debrief 13'.

- **HW:** `HW chip='Apple M4 Pro' cpu=14 gpu=20 mem_gib=24 macos=26.5.1 python=3.13.7 torch=2.14.1 device=cpu`
- **Seeds:** 0, 1 and 2 for every step (light lane). The split is by time, so the seed moves only the TruncatedSVD start; LightGBM is deterministic at these settings (build notes).
- **Reference script:** `ml-learning/answers/13_two_stage_retrieval_and_ranking_ref.py` (sha256 prefix `1067e66a7a5a3712`). The starter is `ml-learning/m3-more-of-the-map/scripts/13_two_stage_retrieval_and_ranking.py`. Seed-0 logs: `13-two-stage-retrieval-and-ranking.out`.
- **Runs and wall times (seeds 0, 1, 2, light lock, one run at a time, back to back by seed):** baseline 7.6, 4.5, 4.8 s; change 9.2, 8.4, 7.4 s; break 5.5, 7, 5.3 s. Precomputed steps: none.
- **Tolerance rule:** tol = spread (max - min) over seeds 0, 1, 2; heavy labs: the baseline spread applies to every step. Every comparison below is an effect in the .json: A minus B averaged over the three seeds, against the larger of the two seed spreads, and reliable only when it exceeds 2x that spread.

<details><summary>P1. recall@100 of the candidate stage on test-period positives</summary>

**Answer:** `P1.recall_at_100` = 0.269545 at seed 0 (a fraction), tolerance plus or minus 0.006094 (the seed spread). Seeds 1 and 2: 0.264829 and 0.270923.

Seed-0 RESULT lines (`--baseline`):

```
RESULT baseline.p50_ms=0.075708 stat=median unit=ms device=cpu batch=1 warmup=20 n=1139 seed=0
RESULT baseline.p99_ms=0.119262 stat=p99 unit=ms device=cpu batch=1 warmup=20 n=1139 seed=0
RESULT P1.recall_at_100=0.269545 unit=fraction users=1159 seed=0
RESULT baseline.recall_at_10=0.0531043 unit=fraction users=1159 seed=0
RESULT baseline.ndcg_at_10=0.179265 unit=ndcg@10 users=1159 seed=0
```

**Why.** The candidate stage is one dot product per movie against a 64-dimension SVD (singular value decomposition) of who rated what before T2, so it ranks by the broad taste and popularity that the past matrix carries. The test positives are every movie a user rated 4 or 5 after T2, and the last tenth of ratings by time runs from late December 2000 to February 2003, so the model of the past is asked about two years of future taste. The heaviest users also have more test positives than the 100 slots, which caps their recall below 1. So about a quarter of the positives make the cut and only 0.0531043 reach the top 10 (`baseline.recall_at_10`); every positive outside the 100 is lost before the re-ranker starts.

**Common wrong prediction:** a high number, 0.6 to 0.9, because 100 movies is the top 3% of the catalogue. The top 3% of one model of the past is not where two years of future taste lands.

</details>

<details><summary>P2. Re-rank the 100 candidates with LightGBM: nDCG@10 direction and size vs candidates only</summary>

**Answer:** up. `P2.ndcg_delta` = 0.00518761 at seed 0 (re-ranked minus candidate order): nDCG@10 goes from 0.179265 (candidate order) to 0.184453 (`P2.ndcg_at_10`), about 2.9% more. Tolerances (seed spread): `P2.ndcg_delta` plus or minus 0.00504959, `P2.ndcg_at_10` plus or minus 0.00327. Seeds 1 and 2: delta 0.0102372 and 0.00595158; nDCG@10 0.187723 and 0.185598. Effect over the three seeds (`P2.ndcg_at_10` minus `baseline.ndcg_at_10`): 0.00712567 against a spread of 0.00327, more than 2x the spread, so a reliable difference, but only just: 2x the spread is 0.00654. The ranker is a single pre-registered configuration: the spec, fixed before any run, names no LightGBM setting, so it runs at the library defaults, and nothing was tuned on any window. The test period is not untouched (the first build explored other configs on it), but no score chose this one (build notes).

Seed-0 RESULT lines (`--change`):

```
RESULT change.p50_ms=0.715875 stat=median unit=ms device=cpu batch=1 warmup=20 n=1139 seed=0
RESULT change.p99_ms=1.06869 stat=p99 unit=ms device=cpu batch=1 warmup=20 n=1139 seed=0
RESULT P2.ndcg_at_10=0.184453 unit=ndcg@10 users=1159 seed=0
RESULT P2.ndcg_delta=0.00518761 unit=ndcg@10 users=1159 seed=0
RESULT change.recall_at_10=0.0539146 unit=fraction users=1159 seed=0
RESULT change.popsort_ndcg_at_10=0.204257 unit=ndcg@10 users=1159 seed=0
```

**Why.** The lambdarank objective learns an order inside each user's 100 candidates from five features known before the cutoff. It can lift positives from ranks 11 to 100 into the top 10, or reorder the positives already there. recall@10 measures the first: 0.0531043 (`baseline.recall_at_10`) against 0.0539146 (`change.recall_at_10`) at seed 0, and over the three seeds the change is -0.000250067 against a spread of 0.0047599, under 2x the spread, so no reliable difference by the rule. These runs therefore cannot say which of the two moves produced the gain. The room above is large: in the first build's test-period exploration, a list that puts every positive among the 100 candidates first scores about 0.69 (build notes).

**Popularity sort.** The same 100 candidates sorted by popularity alone score 0.204257 at seed 0 (`change.popsort_ndcg_at_10`; seeds 1 and 2: 0.202326 and 0.199375). The sort minus the candidate order (`change.popsort_ndcg_at_10` minus `baseline.ndcg_at_10`, three seeds) is 0.023187 against a spread of 0.004882, more than 2x the spread, so a reliable difference. The ranker minus the sort (`P2.ndcg_at_10` minus `change.popsort_ndcg_at_10`, three seeds) is -0.0160613 against a spread of 0.004882, more than 2x the spread, so a reliable difference: the sort is ahead at every seed. So popularity is a strong baseline on these candidates, and this ranker does not beat it. The comparison does not say which of the ranker's five features drive its order, or whether it learned any taste beyond popularity: a feature ablation would, and none was run.

**Timing (Record rows, not a prediction):** at seed 0 (M4 Pro, cpu, batch 1, median of 1,139 requests after 20 warmup requests), p50 per request goes from 0.075708 ms (candidates only) to 0.715875 ms with the re-rank, and p99 from 0.119262 to 1.06869 ms. Over the three seeds, `change.p50_ms` minus `baseline.p50_ms` is 0.556223 ms against a spread of 0.202833 ms, more than 2x the spread, so a reliable difference; `change.p99_ms` minus `baseline.p99_ms` is 0.795335 ms against a spread of 0.355662 ms, more than 2x the spread, so a reliable difference. The added time is the re-rank step, the only work the timed request adds: building the features and LightGBM's predict on 100 rows through its scikit-learn wrapper.

**Common wrong prediction:** a big jump (0.05 or more), because gradient boosting usually wins. Here the gain over the candidate order is only just over 2x the seed spread, and sorting the same candidates by popularity alone scores higher than the ranker. Explanations to test next, none tested here: five coarse features, about 2,450 positive training rows, and counts that grow between the T1 snapshot the ranker trains on and the T2 snapshot it serves from (build notes).

</details>

<details><summary>P3. Pass only 10 candidates to the re-ranker: nDCG@10 change vs the candidate order</summary>

**Answer:** `P3.ndcg_delta` = -0.00234847 at seed 0 (re-ranked from 10 minus the candidate order), tolerance plus or minus 0.00461458 (the seed spread). Seeds 1 and 2: 0.00226611 and 0.000654924. The re-ranked list itself scores 0.176917 (`break.ndcg_at_10`; seeds 1 and 2: 0.179752 and 0.180301, spread 0.003384). Against zero, that is against the candidate order (`break.ndcg_at_10` minus `baseline.ndcg_at_10`, three seeds): 0.000191 against a spread of 0.003384, under 2x the spread, so no reliable difference by the rule; the sign flips between seeds (below it at seed 0, above it at seeds 1 and 2). Against re-ranking from 100 (`P3.ndcg_delta` minus `P2.ndcg_delta`, three seeds): -0.00693461 against a spread of 0.00504959, under 2x the spread, so no reliable difference by the rule. So these three seeds cannot say whether cutting to 10 candidates costs anything here; the P2 gain it could give back is itself only just over 2x its spread.

Seed-0 RESULT lines (`--break`):

```
RESULT break.p50_ms=0.241292 stat=median unit=ms device=cpu batch=1 warmup=20 n=1139 seed=0
RESULT break.p99_ms=0.393813 stat=p99 unit=ms device=cpu batch=1 warmup=20 n=1139 seed=0
RESULT P3.ndcg_delta=-0.00234847 unit=ndcg@10 users=1159 seed=0
RESULT break.ndcg_at_10=0.176917 unit=ndcg@10 users=1159 seed=0
RESULT break.recall_at_10=0.0531043 unit=fraction users=1159 seed=0
```

**Why.** With 10 candidates the top 10 is the same set of movies the candidate stage picked, so recall@10 cannot move: `break.recall_at_10` equals `baseline.recall_at_10` at every seed (0.0531043, 0.05386, 0.0578642). That is an identity, not a noisy estimate. The re-ranker can only reorder those 10, so nDCG@10 moves only by the gaps between the discounts at positions 1 to 10, and here it lands within noise of the candidate order. With 100 candidates the ranker can also lift positives from ranks 11 to 100, but P2's recall@10 shows no reliable difference, so these runs do not show that it did.

**Timing (Record rows, not a prediction):** at seed 0 (M4 Pro, cpu, batch 1, median of 1,139 requests after 20 warmup requests), p50 per request is 0.241292 ms against 0.715875 ms for 100 candidates, and p99 0.393813 against 1.06869 ms. Over the three seeds, `break.p50_ms` minus `change.p50_ms` is -0.30393 ms against a spread of 0.202833 ms, under 2x the spread, so no reliable difference by the rule; `break.p99_ms` minus `change.p99_ms` is -0.396302 ms against a spread of 0.355662 ms, under 2x the spread, so no reliable difference by the rule. Both changes are inconclusive at three seeds.

**Common wrong prediction:** a clear drop below the candidate order ("fewer candidates, a worse list"). It does not happen: reordering the same 10 movies lands within noise of the candidate order, with the sign flipping between seeds. The opposite guess, the same change as P2 ("same ranker, same score"), cannot be ruled out at three seeds either: the gap to P2 is under 2x the spread.

</details>

<details><summary>Rebuild check</summary>

Solution: `ml-learning/answers/rebuild/13_retrieval_metrics.py`. Stub: `ml-learning/m3-more-of-the-map/rebuild/13_retrieval_metrics.py`. `rebuildcheck` verdict: the stub fails as it should (exit 1, NotImplementedError), the solution passes (exit 0, `check: PASS`), REBUILDCHECK OK. `check()` compares `exact_topk` with a full `np.argsort` at k = 100, `recall_at_k` with `sklearn.metrics.recall_score`, `ndcg_at_k` with `sklearn.metrics.ndcg_score` to 1e-12, and `ann_recall` with `recall_score(average="samples")` on 0/1 indicator rows.

</details>

<details><summary>Card drafts</summary>

The third card follows the T and D alternation in `ml-learning/CLAUDE.md` section 4: use 13-D when a D is due and 13-T when a T is due.

| ID | Lab | Type | Question |
|---|---|---|---|
| 13-M | 13 | M | You pass 10 candidates instead of 100 to the same LightGBM re-ranker. Which recall number cannot change, and what is the only way nDCG@10 can still move? |
| 13-N | 13 | N | On MovieLens 1M with 64-dimension SVD candidates fit before T2, about what share of a user's movies rated 4 or 5 after T2 land in the top 100, and why does it come out at that size? |
| 13-D | 13 | D | Your LightGBM re-ranker over 100 candidates gains only a little nDCG@10 over the candidate order. Before anyone tunes it, what one baseline do you compare it with, and what did that show here? |
| 13-T | 13 | T | Your catalogue grows to 10 M items, so the exact dot-product search behind the candidate stage becomes an HNSW index. What new recall loss enters, and how do you measure it before launch? |

Key:

- **13-M:** (1) with 10 candidates the top-10 set is fixed, so recall@10 equals the candidate stage's (`break.recall_at_10` equals `baseline.recall_at_10` at every seed); (2) the ranker can only reorder those 10, so nDCG@10 moves only through where the positives already in the list land (the gaps between the discounts at positions 1 to 10); (3) here it landed within noise of the candidate order (under 2x the seed spread, the sign flipping between seeds).
- **13-N:** (1) about 0.27 (`P1.recall_at_100`: 0.269545, 0.264829, 0.270923 over seeds 0 to 2); (2) the test positives span about two years after T2 (late December 2000 to February 2003), scored by one model of the past; (3) the heaviest users have more test positives than the 100 slots, so their recall cannot reach 1.
- **13-D:** (1) the same 100 candidates sorted by popularity alone (`change.popsort_ndcg_at_10`), the cheapest re-ranker any model must beat; (2) here the sort scored higher than the ranker at every seed, by more than 2x the seed spread (0.204257 against 0.184453 at seed 0), so this ranker does not beat the simplest baseline; (3) the comparison does not show which features drive the ranker or whether it learned taste beyond popularity: that needs a feature ablation.
- **13-T:** (1) ANN recall@k: the share of the exact top k that the index returns, measured on sampled queries against brute-force search; (2) it stacks on the candidate-stage ceiling: a positive must be in the exact top 100 and also be found by the index; (3) pick ef_search where ANN recall flattens and p99 still fits the latency budget.

</details>

<details><summary>Build notes</summary>

Note from the .json (the ranker config and why, users, timing, prototype values):

> Ranker config (fix round 3): LightGBM lambdarank at the library defaults (LightGBM 4.7.0: 100 trees of 31 leaves, learning rate 0.1). It is one pre-registered configuration with no search: the spec names no LightGBM setting, so the defaults are its configuration, and nothing was tuned on any window. Why a third round: the first build scored about a dozen configs on the test period (positives after T2) and picked learning rate 0.03; fix round 2 replaced that with 7 leaves, picked on the [T1, T2) validation window but from a grid set after that test-period exploration, so the test period still shaped the pick. The test period is not untouched: the first build's exploration also scored the defaults on it, and they scored below every other LightGBM config it tried. They are used because the spec names no setting, not because of that score, so the choice cannot favour the test period. Every ranker value in these answers comes from runs made after this change; they reproduce that exploration's scores for the defaults to the five decimals it printed (the pipeline is deterministic per seed). Oracle: in the first build's test-period exploration, a list that puts every positive among the 100 candidates first scores about 0.69 nDCG@10; it depends on the candidates only, not on any ranker config. Users: the test set is the 1,159 users with a rating before T2 and a positive after it; 29 users with a test positive but no earlier rating are cold start and left out. The ranker trains on the 492 of the 1,103 users with a positive in [T1, T2) who also rated a movie before T1 (about 2,450 positive rows); the other 611 (55%) are cold start at T1, so train_ranker() leaves them out, as evaluate() does at T2. Timing: the nine reference runs ran one at a time, back to back by seed, with no other build job running beside any of them; work outside the build kept the machine's one-minute load average between about 7 and 10 on 14 cores, so the timing rows are noisier than a quiet machine would give. Two earlier sets of the nine runs in this round were replaced because heavy jobs from other labs ran beside them (lab 15's local LLM beside every run of the first, smoke jobs from labs 37 and 01 beside four runs of the second). Their ranking values were identical; only their timing rows differed, and those were seen before each replacement. This set was declared final before it ran. The spec gives no prototype values for lab 13.

Other choices where the spec is silent, each the simplest correct option:

- **Implicit matrix:** every rating before the cutoff counts as 1, whatever its stars. Positives (training labels and test) are ratings of 4 or 5.
- **Candidate score:** the rank-64 reconstruction (TruncatedSVD `fit_transform` row times `components_`), seen movies set to minus infinity, `argpartition`, then a sort of the top n.
- **Features:** popularity and user activity are raw counts before the cutoff. Mean rating is NaN for a movie with no rating yet (LightGBM treats it as missing). Genre overlap is the user's genre mix (share of past movies in each of 18 genres) dotted with the movie's 0/1 genre vector. The ranker trains at T1 and serves at T2, so counts grow by about an eighth between the two snapshots; a share of all ratings would remove that skew (a follow-up, not done).
- **Ranker:** `LGBMRanker(objective="lambdarank", n_jobs=1, random_state=seed)`, every other parameter at the library default (LightGBM 4.7.0: 100 trees of 31 leaves, learning rate 0.1), as the note above describes. One thread, so a request runs on one core and the shared lane is not oversubscribed. Training users with no positive among their candidates stay in; they add no gradient. At these settings LightGBM is deterministic (no bagging, no feature subsampling, fewer rows than its bin-sampling threshold): on the real training matrix, `random_state` 0, 1 and 2 gave identical predictions at the defaults (checked in fix round 3, as at the earlier rounds' settings), so every tolerance here is TruncatedSVD-start noise.
- **Users:** the ranker trains only on users with a rating before T1, and the test set holds only users with a rating before T2 (counts in the note above). Cold-start users are out of scope for this lab; `train_ranker()` and `evaluate()` each say so in a comment.
- **P3 asked as a change:** the spec's P3 asks for nDCG@10 after re-ranking 10 candidates. The Predict row asks for its change against the candidate order (`P3.ndcg_delta`), the way P2 is asked, because every row is written at 0:05, before the learner has seen any nDCG@10 for this setup. The absolute value is the Record row `break.ndcg_at_10`. The kind stays num.
- **Popularity sort:** `--change` also prints `change.popsort_ndcg_at_10`, the same 100 candidates sorted by popularity before the cutoff (ties keep the candidate order), outside the timed request. It is the simplest re-ranker, the baseline any learned ranker must beat, and its comparisons with the candidate order and with the ranker rest on reference runs at every seed. It does not show which features drive the ranker; that needs a feature ablation, which was not run. It is an addition to the spec's Record list.
- **Effects recorded:** every comparison in these answers is an effect in the .json (A minus B averaged over seeds 0 to 2, against the larger of the two seed spreads). Reliable by the 2x rule: `P2.ndcg_at_10` minus `baseline.ndcg_at_10`, `P2.ndcg_at_10` minus `change.popsort_ndcg_at_10`, `change.popsort_ndcg_at_10` minus `baseline.ndcg_at_10`, `change.p50_ms` minus `baseline.p50_ms` and `change.p99_ms` minus `baseline.p99_ms`. No reliable difference: `P3.ndcg_delta` minus `P2.ndcg_delta`, `break.ndcg_at_10` minus `baseline.ndcg_at_10`, `change.recall_at_10` minus `baseline.recall_at_10`, `break.p50_ms` minus `change.p50_ms` and `break.p99_ms` minus `change.p99_ms`.
- **Names and units:** `P2.ndcg_delta` and `P3.ndcg_delta` are sign-neutral on purpose, because the Predict rows ask for a direction or a signed change. Every nDCG line carries `unit=ndcg@10`.
- **Latency:** one request at a time with `time.perf_counter`, the first 20 requests dropped, p50 and p99 over the rest. The re-rank time includes the per-call overhead of LightGBM's scikit-learn wrapper. Timing rows move with other jobs on the machine; the note above says what ran beside the reference runs.
- **LightGBM and faiss:** LightGBM is imported inside `train_ranker()`. On this Mac the two in one process crash (a segfault when LightGBM loads first, a hang when faiss loads first: two OpenMP runtimes), so `--stretch` never loads LightGBM.
- **Script length:** the reference is about 210 lines against the 150-line guide. The level C `--check` fixture, the two scikit-learn smoke stand-ins and the `--stretch` mode add about 45 lines; those helpers sit below `main()` so the pipeline reads first, and the lab file points the 4-minute read at the pipeline functions.
- **Stretch:** implemented, never run on MovieLens 32M. Its code path ran on a stand-in `ratings.csv` built from ML-1M with every value masked (labkit's smoke default), once in the build and again in the first fix round, so no stretch number exists anywhere. Settings: the first 1,000 users as queries, no seen-movie filter (it measures the index, not the recommender), HNSW M = 32, efConstruction 200, ef_search 16, 64 and 256. Exact search is a faiss `IndexFlatIP`, so exact and HNSW searches both run one query at a time on one thread (`faiss.omp_set_num_threads(1)`, set after the HNSW graph is built on all cores). A numpy matrix product runs on Apple's Accelerate library, which threadpoolctl cannot limit, so it could not give a one-core baseline.
- **Precomputed steps:** none. Every reference run took under a minute.
- **Prototype comparison:** the spec gives no prototype values for lab 13. Sanity checks that hold at every seed: `break.recall_at_10` equals `baseline.recall_at_10`; `P2.ndcg_delta` equals `P2.ndcg_at_10` minus `baseline.ndcg_at_10`, and `P3.ndcg_delta` equals `break.ndcg_at_10` minus `baseline.ndcg_at_10`, to print precision. Fix round 3 changed only the ranker settings and the docstring title: every value that does not depend on the ranker (`P1.recall_at_100`, `baseline.recall_at_10`, `baseline.ndcg_at_10`, `break.recall_at_10`, `change.popsort_ndcg_at_10`) reproduced the earlier runs exactly, and `P2.ndcg_at_10` and `break.ndcg_at_10` match the first build's test-period scores for the defaults to the five decimals that exploration printed.

</details>
