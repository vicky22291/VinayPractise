# 12. Lexical vs dense retrieval: BM25, embeddings and fusion: reference answers

> Spoilers. The AI opens one block at a time, only after that step's prediction row exists and the learner pasted their own RESULT lines, or after 'debrief 12'.

- **HW:** `HW chip='Apple M4 Pro' cpu=14 gpu=20 mem_gib=24 macos=26.5.1 python=3.13.7 torch=2.14.1 device=cpu`
- **Seeds:** 0, 1 and 2 for baseline, change and break (light lane). Reference script: `answers/12_lexical_vs_dense_retrieval_ref.py` (sha256 prefix `9bb98b0d261c4a61`). Raw seed-0 output: `answers/12-lexical-vs-dense-retrieval.out`.
- **Runs and wall times (seeds 0, 1, 2):** baseline 81.9 s, 84.7 s, 83.3 s. Change 82.6 s, 93.6 s, 77.0 s. Break 36.9 s, 63.5 s, 63.4 s. All on the light lane, sharing the CPU (central processing unit) with other labs' runs, so the wall times move from run to run.
- **Tolerance rule:** tol = spread (max - min) over seeds 0, 1, 2; heavy labs: the baseline spread applies to every step.
- **What the seed does here:** nothing in retrieval is random (fixed models, fixed 300 queries, no training), so every nDCG@10 (normalized discounted cumulative gain over the top 10) value is identical at all three seeds and its tolerance is 0.0. The seed only drives the bootstrap that resamples the queries in `--change`. Read that interval, not the seed spread, as the noise yardstick.
- **Grading the learner's TODO:** `bm25_scores()` feeds the BM25 (Best Matching 25) line and every P2 line, so compare the learner's `baseline.ndcg10_bm25` with the one in the P1 block before grading P2. A correct TODO matches it to all six printed digits. In the build's test, a float64 numpy version, a float32 numpy version and bm25s itself gave the reference's BM25 top 10 on all 300 queries, and the same `baseline.ndcg10_bm25` and P2 lines. So any difference, even in the last printed digit, means a bug in the TODO: send the learner back to `--check`.

<details><summary>P1. nDCG@10 of all-MiniLM-L6-v2 on the 300 test queries (BEIR published BM25 at 0.665 and a dense model trained elsewhere at 0.318)</summary>

**Answer: 0.645082** (tolerance 0.0: seeds 0, 1 and 2 all give 0.645082).

Seed-0 RESULT lines:

```
RESULT baseline.ndcg10_bm25=0.662528 unit=ndcg@10 seed=0
RESULT P1.ndcg10_dense=0.645082 unit=ndcg@10 seed=0
RESULT baseline.docs_per_s=101.005 unit=docs/s device=cpu batch=64 warmup=1 n=10 stat=median seed=0
```

Other seeds: `P1.ndcg10_dense` 0.645082 and 0.645082; `baseline.ndcg10_bm25` 0.662528 and 0.662528; `baseline.docs_per_s` 101.204 and 157.729 (it moves with CPU sharing, not with the seed).

Why: BM25 rewards exact overlap on rare words through idf (inverse document frequency), and SciFact claims are short technical statements whose key terms (genes, drugs, diseases, numbers) appear word for word in the right abstract. The dense model squeezes each abstract, cut at 256 word pieces, into one 384-dimensional vector learned from over a billion mostly general sentence pairs, so rare biomedical terms get blurred. Its [model card](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) lists scientific data in that mix (citation and title-abstract pairs from S2ORC, the Semantic Scholar Open Research Corpus, plus SPECTER citation triplets): a likely reason, not tested here, that it lands close to BM25 instead of near the 0.318 that BEIR, a zero-shot information retrieval benchmark, reports for DPR (Dense Passage Retrieval, trained on question-answering data only). Our 0.645082 matches the 0.64508 that MTEB (the Massive Text Embedding Benchmark) publishes for this model on SciFact, which also confirms the hand-written nDCG@10.

Our BM25 (0.662528) vs the published 0.665: BEIR's figure is Elasticsearch with a stemmer and title and text as two fields. Pyserini publishes BM25 with one field and a Porter stemmer at 0.679, and with two fields at 0.665. We use one field, English stopwords and no stemmer, so the gap to the stemmed one-field run is the price of skipping the stemmer (plus a different tokenizer). Landing near 0.665 is two opposite effects roughly cancelling.

Common wrong prediction: the dense model above BM25 ("embeddings understand meaning"), or anchoring on 0.318 and expecting a dense model to collapse out of domain.

</details>

<details><summary>P2. Fuse BM25 and dense rankings with reciprocal rank fusion (k = 60): nDCG@10 direction and size vs the better single method</summary>

**Answer: up, by 0.0279512** (hybrid 0.690479 vs BM25 0.662528, the better single method; tolerance 0.0 for both lines: every seed gives the same values).

Seed-0 RESULT lines:

```
RESULT P2.ndcg10_hybrid=0.690479 unit=ndcg@10 seed=0
RESULT P2.delta_vs_best=0.0279512 unit=ndcg@10 seed=0
RESULT change.delta_ci95_low=0.0070094 unit=ndcg@10 seed=0
RESULT change.delta_ci95_high=0.0497443 unit=ndcg@10 seed=0
```

Other seeds: `P2.ndcg10_hybrid` 0.690479 and 0.690479; `P2.delta_vs_best` 0.0279512 and 0.0279512. The 95% interval (2,000 bootstrap resamples of the 300 queries) at seeds 1 and 2: 0.00720544 to 0.04943, and 0.00730033 to 0.0490848.

Why: BM25 and the dense model miss different documents. BM25 misses an abstract that says the claim in other words; the dense model misses one that hinges on an exact rare term. RRF (reciprocal rank fusion) gives each document 1 / (60 + rank) from each list, so a document near the top of both lists rises and one list's confident hit still survives; k = 60 flattens the top ranks, so neither list dominates and no score calibration is needed. The interval excludes 0, so the gain is real, but 300 queries cannot pin its size: anything from 0.0070094 to 0.0497443 fits.

Common wrong prediction: "fusion averages the two, so it lands between them", or "no change, because BM25 already wins".

</details>

<details><summary>P3. Documents embedded with all-MiniLM-L6-v2 and queries with bge-small-en-v1.5 (both 384-dimensional): nDCG@10</summary>

**Answer: 0.136588** (tolerance 0.0: seeds 0, 1 and 2 all give 0.136588). Against the matched MiniLM run that is a change of -0.508494.

Seed-0 RESULT line:

```
RESULT P3.ndcg10_mismatched=0.136588 unit=ndcg@10 seed=0
```

Why: each model learns its own coordinate system, so a bge query vector scored against MiniLM document vectors is a cosine across two different spaces, and since the shapes match, nothing errors. The score still sits far above a random order, which gets about 0.001 with one relevant document in 5,183. The two models share an ancestor: during the build their token-embedding tables lined up token by token (the same 30,522-token uncased vocabulary and 384 dimensions), so their output spaces stay partly aligned and some results still look on topic. bge-small-en-v1.5 is not weak on its own: its model card reports 0.71275 nDCG@10 on MTEB SciFact when it embeds both sides.

Common wrong prediction: an error, a value near 0 (random), or a small drop "because both are 384-dimensional sentence models".

</details>

<details><summary>Rebuild check</summary>

Solution: `answers/rebuild/12_bm25.py`. Stub: `m3-more-of-the-map/rebuild/12_bm25.py`.

`rebuildcheck`: stub fails as it should (exit 1), solution passes (exit 0), `REBUILDCHECK OK`.

The check compares rank order with bm25s 0.3.11 (`method='lucene'`, k1 = 1.2, b = 0.75) on 8 toy abstracts and 6 queries, never raw scores (bm25s drops the constant k1 + 1 factor). The sixth query, "fracture risk in older adults", mixes words that appear in 1, 2 and 4 of the 8 abstracts, so its order depends on the idf form. Under three tokenizers (`\w+`, `\w\w+`, `split()`) the check fails for the textbook idf ln(N/df) (N documents, df of them holding the word), the Robertson idf, no idf, no length normalization, raw tf (term frequency) times idf, df counted as total occurrences, swapped k1 and b, an inverted length ratio, and no division by avgdl (the mean document length). It still passes a de-duplicated query, ln(1 + N/df), and (with `\w+` or `split()`) the unique-token document length; the lab's `--check` fails all three. Correct versions pass: the reference, an algebraically equal idf form, and float64 and float32 numpy versions.

</details>

<details><summary>Card drafts</summary>

| ID | Lab | Type | Question |
|---|---|---|---|
| 12-M | 12 | M | In BM25, why does each extra repeat of a term in a document add less and less to the score, and why is the term frequency divided by a factor that grows with document length? |
| 12-N | 12 | N | On SciFact's 300 test queries, how did RRF (k = 60) change nDCG@10 against the better single method, and how do you know the change is real? |
| 12-D | 12 | D | A teammate re-indexes the help articles with a stemmer. Nothing errors, but BM25 now returns nothing for queries such as "failed refunds", while "refund" alone still works. What do you check first, and what is the fix? |

Keys:

- **12-M:** (1) k1 saturates tf: the term's contribution keeps rising with each repeat but approaches a ceiling of (k1 + 1) times idf, so the tenth repeat adds far less than the first and keyword stuffing cannot win. (2) b makes the divisor grow with document length over avgdl, so a long document does not win just by containing more words.
- **12-N:** (1) Up by 0.0279512 over BM25, the better single method (hybrid 0.690479 vs 0.662528). A hit gets the direction, BM25 as the better single method, and the size to two decimals. (2) A paired bootstrap over the 300 queries gave a 95% interval of 0.0070094 to 0.0497443, which excludes 0, so the gain is real but its size is loose.
- **12-D:** (1) Check that the query path runs the same analyzer as the index (tokenizer, stopword list, stemmer). The index now holds stems such as "fail" and "refund", while the queries still send "failed" and "refunds", so no token overlaps. It is the lexical twin of one embedding space. (2) Fix: one analyzer shared by both paths and stored with the index, like the embedding model's name and version, so a query from any other analyzer or encoder is refused. Gate every re-index on nDCG@10 over a fixed query set.

</details>

<details><summary>Build notes</summary>

- **Knob changes:** none. Both taught effects exceed 2x the seed spread: hybrid minus BM25 by seed (stored as 0.027950999999999948 in the .json) and mismatched minus matched (-0.508494), each with spread 0.0. Because the spread is 0, the 2x rule cannot tell signal from noise here, so the build added the query bootstrap (below) as the real test for P2.
- **Seed:** the spec is silent on what `--seed` changes in a lab with no randomness. Simplest correct option: it only seeds the paired bootstrap of the P2 delta (2,000 resamples of the 300 queries), printed as `change.delta_ci95_low` and `change.delta_ci95_high`. These two Record rows are an addition to the spec's Record list.
- **Precomputed steps:** none. The longest seed-0 run was change at 82.6 s; the slowest run of all was change at seed 1, 93.6 s, while sharing the CPU.
- **Choices where the spec is silent:**
  - BM25's top 100 keeps only documents with a positive score (a document with no query token is not retrieved, as in Lucene). 2 of the 300 queries match fewer than 100 documents, so this only affects the fusion input for them.
  - A repeated query token counts again in BM25, as in bm25s and Lucene. 56 of the 300 queries repeat a token after stopword removal; the `--check` fixture includes one such query, so a de-duplicating version fails it.
  - RRF ties keep insertion order (BM25's list first), through `Counter.most_common`.
  - bge-small queries are encoded without bge's optional retrieval instruction, because the break is about the model mismatch. The lab's P3 row says so.
  - Measured modes load the models with `local_files_only=True` (no Hub calls after `--download`), and `HF_HUB_DISABLE_PROGRESS_BARS` silences the weight-loading bars.
  - torch is imported before `labkit.start`, so it is seeded, and sentence-transformers only inside `download()` and `embed()`. Its import prints a macOS-only torch notice ("Redirects are currently not supported in MacOs"), which now lands after the HW and SEED lines, and `--check` skips the slow import.
  - Documents per second is the median over 10 chunks of the corpus after one warmup batch, at torch's default thread count. It moved with CPU sharing (101.005, 101.204, 157.729), so treat it as a busy-machine figure.
- **Deviations:**
  - The reference is 178 lines and the starter 168, above the 150-line guide, because of the zip fallback, the 20-row `--check` and the bootstrap. The optional nomic-embed-text path through Ollama was not built.
  - The lab file adds two things the spec does not list. A learner-captured Record row for our BM25 vs the published 0.665 (the gap and one reason), because the author note asks to record that gap and why. A second Repo link, to section 4 "Evaluation and migration" of `concepts/rag-and-react.md` (the spec names section 3 only), because section 4 holds the zero-downtime re-index the Staff follow-up asks about.
- **Fallback test:** the BEIR zip path was run in a scratch folder with the Hugging Face URLs unreachable. The first version needed two fixes: keep only `_id`, `title` and `text` (the jsonl carries an empty metadata struct that pyarrow cannot write), and fill the missing query title with an empty string. It also moved `qrels/test.tsv` out of the extracted folder, so a second `--download` during the same outage crashed with FileNotFoundError; it now copies the file. In the fix round the fallback ran twice in a row, and both runs left tables and qrels identical to the Hugging Face files.
- **Check fixture test:** the 20-row `--check` draws words from a Zipf-like 300-word vocabulary, so most words appear in 1 to 3 of the 20 documents and the commonest in 16, as on SciFact. Its fourth query mixes the commonest word with a rare one. It passes for the reference, an algebraically equal idf form, and float64 and float32 numpy versions. It fails for the textbook idf ln(N/df), the Robertson idf, ln(1 + N/df), no idf, no length normalization, raw tf times idf, a de-duplicated query, df counted as total occurrences, the unique-token document length, swapped k1 and b, an inverted length ratio and no avgdl division. The first build's fixture drew from 25 words, so every word was common and ln(N/df) passed it.
- **Prototype comparison:** the spec carries no [answers only] prototype values for this lab, so the build compared with published figures. BM25: ours 0.662528 vs BEIR's 0.665; Pyserini lists one-field stemmed BM25 at 0.679 and two-field at 0.665 ([Pyserini BEIR results](https://castorini.github.io/pyserini/2cr/beir.html)). Dense: ours 0.645082 vs MTEB's 0.64508 for all-MiniLM-L6-v2 on SciFact ([MTEB results repo](https://github.com/embeddings-benchmark/results), mteb 1.12.75), a match. bge-small-en-v1.5 alone: 0.71275 on its model card (71.275 on the card's 0 to 100 scale). Directions agree with the spec's concept: the lexical baseline ahead out of domain, fusion above both, the mismatch far below matched. The above-random mismatch score was explained by a light check of the two models' token-embedding tables (shared ancestry), not by a bug: the break code does embed queries with bge-small and documents with MiniLM.

</details>
