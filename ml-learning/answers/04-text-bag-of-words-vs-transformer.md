# 04. Text: bag of words vs a pretrained transformer: reference answers

> Spoilers. The AI opens one block at a time, only after that step's prediction row exists and the learner pasted their own RESULT lines, or after 'debrief 04'.

- HW (hardware) line: `HW chip='Apple M4 Pro' cpu=14 gpu=20 mem_gib=24 macos=26.5.1 python=3.13.7 torch=2.14.1 device=mps`. Here `mps` is MPS (Metal Performance Shaders), PyTorch's backend for the Apple GPU (graphics processing unit). The CPU (central processing unit) timings run with the model moved off the GPU.
- Seeds: baseline at 0, 1 and 2; change and break at 0 (heavy lane). `--seed S` draws its own 2,000 training reviews and drives the new head's initial weights, dropout, batch order and the break's shuffle. The 2,000 test reviews are the same at every seed (the spec's fixed test subset, drawn once with seed 0), so every spread below is training randomness only.
- Reference script: `ml-learning/m1-whole-game/scripts/04_text_bag_of_words_vs_transformer.py` (level W: the learner's script is the reference), sha256 prefix `40feb06831606283`. Values: [`04-text-bag-of-words-vs-transformer.json`](04-text-bag-of-words-vs-transformer.json). Seed-0 logs: [`04-text-bag-of-words-vs-transformer.out`](04-text-bag-of-words-vs-transformer.out).
- Runs and wall times: baseline 134.1 s (seed 0), 151.4 s (seed 1), 163.3 s (seed 2); change 32.0 s; break 139.1 s. All on mps under the heavy lock, with up to two light jobs from other labs beside them.
- Precomputed steps: none.
- Tolerance rule: tol = spread (max - min) over seeds 0, 1, 2; heavy labs: the baseline spread applies to every step. Here: `P1.gap_points` 0.45 points; `baseline.tfidf_accuracy` 0.0075 (0.75 points); `baseline.bert_accuracy` 0.012 (1.2 points). Spreads and effects are shown at the precision of the RESULT lines; the .json holds the same numbers with float noise (for example 0.0119999999999999 for 0.012).

<details><summary>P1. Accuracy gap in points, DistilBERT minus TF-IDF plus logistic regression, both trained on the same 2,000 reviews at 256 word pieces, seed 0</summary>

**Answer: 7.9 points** (DistilBERT 0.8755, TF-IDF 0.7965 on the 2,000 test reviews), tolerance plus or minus 0.45 points (the seed spread). Seeds 1 and 2: 7.45 and 7.45 points (DistilBERT 0.8635 and 0.867, TF-IDF 0.789 and 0.7925).

```
RESULT baseline.tfidf_train_s=0.163408 unit=s device=cpu warmup=0 n=1 stat=total seed=0
RESULT baseline.bert_train_s=90.1932 unit=s device=mps batch=16 warmup=0 n=250 stat=total seed=0
RESULT P1.gap_points=7.9 unit=points pieces=256 seed=0
RESULT baseline.tfidf_accuracy=0.7965 unit=fraction pieces=256 seed=0
RESULT baseline.bert_accuracy=0.8755 unit=fraction pieces=256 seed=0
RESULT baseline.tfidf_ms_per_1000=76.3 unit=ms device=cpu batch=50 warmup=1 n=20 stat=median threads=1 pieces=256 seed=0
RESULT baseline.bert_ms_per_1000=16796 unit=ms device=cpu batch=50 warmup=1 n=20 stat=median threads=10 pieces=256 seed=0
```

Why: TF-IDF plus logistic regression must learn every word's weight from these 2,000 reviews alone. Its seed-0 vocabulary has 20,605 words, and 4.3% of the test reviews' words are not in it, so they are dropped. DistilBERT arrives knowing English from pretraining, so near-synonyms, negation and context are already in its features, and rare words are spelled out as word pieces (no `[UNK]` piece in the 2,000 test reviews). That prior knowledge is what 2,000 labels cannot teach a word-count model. The cost side: on the CPU (batches of 50, tokenizing included) DistilBERT took 16,796 ms per 1,000 reviews against 76.3 ms for TF-IDF at seed 0, about 220 times more. Training took 90.1932 s on MPS against 0.163408 s on the CPU.

Common wrong prediction: 15 to 25 points, from "transformers crush bag of words". On sentiment, single words like "awful" and "superb" carry most of the signal, so a word-count model is a strong bar. The opposite miss is 0 points or negative, from "2,000 labels are too few to fine-tune 66 M parameters": fine-tuning starts from pretrained weights, so it needs far fewer labels than training from scratch.

</details>

<details><summary>P2. Every review cut to 32 word pieces instead of 256, for both models: accuracy direction and size for each</summary>

**Answer: both down, by about the same amount.** TF-IDF 0.6525 (`P2.tfidf_delta_vs_P1` -14.4 points), DistilBERT 0.7215 (`P2.bert_delta_vs_P1` -15.4 points). Tolerance: plus or minus 0.75 points for TF-IDF and 1.2 points for DistilBERT (their baseline seed spreads). Both effects pass the 2x-spread rule (mkanswers: -0.144 against a spread of 0.0075, and -0.154 against 0.012, ok true).

Grading: one prediction-log row with two parts. It is a hit when both directions are right and both deltas sit inside the written ranges, compared with the learner's own pasted `P2.*_delta_vs_P1` lines. If only one part hits, log a miss and say which part in the Lesson column. Compare sizes (absolute values) when the range is a size, such as "down, 10 to 20".

```
RESULT change.tfidf_train_s=0.0302128 unit=s device=cpu warmup=0 n=1 stat=total seed=0
RESULT change.bert_train_s=16.9127 unit=s device=mps batch=16 warmup=0 n=250 stat=total seed=0
RESULT P2.tfidf_accuracy=0.6525 unit=fraction pieces=32 seed=0
RESULT P2.tfidf_delta_vs_P1=-14.4 unit=points seed=0
RESULT P2.bert_accuracy=0.7215 unit=fraction pieces=32 seed=0
RESULT P2.bert_delta_vs_P1=-15.4 unit=points seed=0
RESULT change.tfidf_ms_per_1000=17.7217 unit=ms device=cpu batch=50 warmup=1 n=20 stat=median threads=1 pieces=32 seed=0
RESULT change.bert_ms_per_1000=2453.94 unit=ms device=cpu batch=50 warmup=1 n=20 stat=median threads=10 pieces=32 seed=0
```

Why: 32 pieces, minus [CLS] and [SEP], keep a median of 24 words of a review whose median length is 174 words, and both models lose the same evidence. The opening of a movie review is often plot set-up, while the verdict tends to come later. Neither model can use words it never sees, so the information loss hits both alike: DistilBERT stays ahead (0.7215 vs 0.6525, a 6.9-point gap at 32 pieces vs 7.9 at 256), but that 1-point narrowing is from one paired seed and only just above 2x the gap's seed spread, so do not read it as real. At 256 pieces the cut changes only 41.9% of the test reviews (the rest are shorter), which is why 256 is the usual budget. The cost moves the other way: at 32 pieces DistilBERT took 2,453.94 ms per 1,000 reviews on the CPU, about 7 times less than at 256, and its training on MPS took 16.9127 s instead of 90.1932 s.

Common wrong prediction: DistilBERT down 0 to 5 points and TF-IDF down 20 or more, from "the transformer understands context, so it needs fewer words". Context helps only with words that are there. The other common miss is "both collapse to chance (0.5)": 24 words still hold enough sentiment words to score far above chance.

</details>

<details><summary>P3. Shuffle the word order of every test review (no retraining): which model loses more accuracy, and by how many points</summary>

**Answer: DistilBERT**, by 10.7 points (0.8755 in order, 0.7685 shuffled), tolerance plus or minus 1.2 points (the DistilBERT baseline spread). TF-IDF loses exactly 0 points (0.7965 in order and shuffled), tolerance 0: no seed spread applies, because a shuffle leaves every TF-IDF vector unchanged at any seed. The DistilBERT effect is far above 2x the spread (mkanswers: -0.107 against 0.012, ok true). The TF-IDF effect is 0 by construction (ok false): the lab teaches it as a null effect, so it was not inflated. `--break` trains both models again from seed 0 on reviews in normal order, and its in-order accuracies reproduced the baseline's exactly (0.7965 and 0.8755).

Grading: one prediction-log row of kind pick. Hit and the Brier score come from the option alone, as the log's pick rule says: DistilBERT is a hit; TF-IDF or a tie is a miss. Then grade each drop on its own, against the learner's own pasted line, and write both results in the Lesson column. Neither drop changes Hit or the Brier score.

- `P3.bert_drop_points`: right when the learner's written range covers their pasted drop. A number written without a range is right when it is within 1.2 points of the pasted drop (the DistilBERT baseline spread). Otherwise note the gap in points.
- `P3.tfidf_drop_points`: the pasted line is exactly 0 at every seed, by construction (see Why), so the tolerance is 0. Right only when the learner wrote 0, or a range that includes 0. Any other number is wrong by its own size: that is the common wrong prediction below. A nonzero pasted value means the script was changed (for example bigrams or another tokenizer): check that before grading.

```
RESULT break.tfidf_train_s=0.112359 unit=s device=cpu warmup=0 n=1 stat=total seed=0
RESULT break.bert_train_s=91.9298 unit=s device=mps batch=16 warmup=0 n=250 stat=total seed=0
RESULT P3.tfidf_drop_points=0 unit=points pieces=256 seed=0
RESULT break.tfidf_accuracy=0.7965 unit=fraction pieces=256 seed=0
RESULT break.tfidf_accuracy_shuffled=0.7965 unit=fraction pieces=256 seed=0
RESULT P3.bert_drop_points=10.7 unit=points pieces=256 seed=0
RESULT break.bert_accuracy=0.8755 unit=fraction pieces=256 seed=0
RESULT break.bert_accuracy_shuffled=0.7685 unit=fraction pieces=256 seed=0
```

Why: unigram TF-IDF turns a review into word counts, and a shuffle keeps every word and its count, so each shuffled review gets the identical vector and the identical prediction. DistilBERT adds a position embedding to every piece, and its attention learned from ordered text, so shuffling breaks phrases and negation ("not good" becomes "good ... not") and feeds it inputs unlike anything in pretraining or fine-tuning. It still scores 0.7685, far above chance, because the single sentiment words survive the shuffle. Shuffled, it scores below TF-IDF (0.7685 vs 0.7965): its edge at 256 pieces comes from reading words in order.

Common wrong prediction: TF-IDF loses a few points too, from "any model needs order". A bag of words has no order to lose. The other miss is DistilBERT falling to chance (0.5): the words are still there.

</details>

<details><summary>Rebuild check</summary>

- Solution: `ml-learning/answers/rebuild/04_tfidf.py`. Stub: `ml-learning/m1-whole-game/rebuild/04_tfidf.py`.
- `rebuildcheck`: stub fails as it should (exit 1, NotImplementedError); solution passes (exit 0, `check: PASS`); REBUILDCHECK OK.
- `check()` compares with scikit-learn's `TfidfVectorizer()` only: the same vocabulary in the same order, then a largest absolute difference of exactly 0.0 on 9 short reviews, and at most 1e-12 on those plus 4 longer ones. One short review, "!!!", has no words, so its row must stay all zeros, as `TfidfVectorizer()` leaves it. The review added it and the zero-row rule in the docstring, because the first solution divided that row by its zero length and returned NaN (not a number).
- Why the exact part uses short reviews: each has at most two distinct words, so no summation order can change a bit. On longer rows scikit-learn 1.9.1 adds the squares for the L2 length in the order its CountVectorizer first met each word in the corpus (it remaps columns to alphabetical order without re-sorting them), so a correct hand-written version can differ in the last bit. A build probe measured 5.55e-17 for column-order, `np.linalg.norm` and plain numpy versions on 8 longer reviews.
- Mutation tests in the build: single-character words kept, no lowercasing, vocabulary in first-seen order, binary counts, idf without smoothing, idf without the + 1, L1 rows, and no zero-length guard (the NaN row) all fail `check()`. Three correct variants passed the fixture before "!!!" was added: a left-to-right sum of squares, `np.linalg.norm` and `np.einsum`. Each needs the same zero-length guard now.

</details>

<details><summary>Card drafts</summary>

| ID | Lab | Type | Question |
|---|---|---|---|
| 04-M | 04 | M | When every test review's words were shuffled, TF-IDF plus logistic regression kept exactly the same accuracy while fine-tuned DistilBERT lost about 11 points. Explain both, and why DistilBERT still stayed far above chance. |
| 04-N | 04 | N | On 2,000 IMDB training reviews at 256 word pieces, how many points of accuracy did fine-tuned DistilBERT gain over TF-IDF plus logistic regression, and roughly how many times more CPU time per 1,000 reviews did it cost? Why that cost gap? |
| 04-T | 04 | T | Bank-transaction descriptions are 10 to 30 word pieces, 1 M a day, 200 ms budget. From lab 04's 32-piece run, which model do you ship first, and what measurements decide whether the transformer replaces it? |

Keys:

- 04-M: (1) unigram TF-IDF is a bag of words: the shuffled review has the same counts, so the same vector and the same prediction (0 points); (2) DistilBERT adds position embeddings and its attention learned from ordered text, so shuffling breaks phrases and negation and gives it inputs unlike its training (0.8755 to 0.7685, 10.7 points at seed 0); (3) the single sentiment words survive the shuffle, so it stays far above 0.5.
- 04-N: (1) 7.9 points at seed 0, accept 7 to 8.5 (seeds 7.45 to 7.9); (2) about 200 times more CPU time per 1,000 reviews, accept 100 to 300 (16,796 vs 76.3 ms at seed 0, batches of 50, M4 Pro CPU; other seeds ran under heavier CPU load); (3) TF-IDF is one sparse dot product over the words present, while DistilBERT runs 6 transformer layers over every word piece, and attention grows with the square of the number of pieces.
- 04-T: (1) ship TF-IDF plus logistic regression first: it is the bar and the fallback, and at 32 pieces it cost 17.7217 ms per 1,000 on the CPU in batches of 50; (2) DistilBERT at 32 pieces cost 2,453.94 ms per 1,000, the median batch of 50 scaled up (M4 Pro CPU, 10 threads): that is batched throughput, so 1 M a day is about 41 minutes of this CPU per day and daily cost does not rule it out, but it says nothing about one request's latency or the tail against the 200 ms budget; (3) two measurements decide: the accuracy gap on your own labelled bank descriptions (on reviews it stayed about 7 points ahead at 32 pieces, 0.7215 vs 0.6525), and single-request latency with its p99 (99th percentile) on the serving CPU, at the serving batch size and under load, keeping the rule-based fallback for misses.

</details>

<details><summary>Build notes</summary>

**Knob changes: none.** Every effect the lab teaches as real passes the 2x-spread rule at the spec's knobs: the 32-piece cut costs DistilBERT -0.154 (spread 0.012) and TF-IDF -0.144 (spread 0.0075), and the shuffle costs DistilBERT -0.107 (spread 0.012). The TF-IDF shuffle effect is 0.0 (ok false) by design and is reported as a null effect.

**Precomputed steps: none.** The longest seed-0 run is the break at 139.1 s, under the 6-minute cap.

**Prototype comparison.** The spec's only `[answers only]` note is "TF-IDF cannot move" under the shuffle: confirmed, 0 points at seed 0, with identical in-order and shuffled accuracy (0.7965). Its compute anchor is 49 samples/s at 512 tokens on an M3 Max. Here 250 steps of 16 reviews (4,000 samples) took 90.1932 s, 44 samples/s at 256 pieces on the M4 Pro's 20-core GPU in fp32 (32-bit floats). With dynamic padding nearly every batch is 256 pieces long (41.9% of the test reviews fill all 256, and a batch pads to its longest review), so that is about 11,000 pieces/s against the anchor's about 25,000 tokens/s, roughly 2.2 times slower. An M3 Max has up to 40 GPU cores and more memory bandwidth, and the timed loop here also tokenizes each batch on a shared CPU, so the gap matches the hardware and points to no bug. No published accuracy matches this exact setup (2,000 training reviews, 2 epochs, 256 pieces); Sanh et al. 2019 fine-tune DistilBERT on all 25,000 reviews.

**Deviations from the spec, and why:**

- Fixed test subset. The spec asks for "a fixed 2,000-review test subset", so `TEST_SEED = 0` draws the test reviews at every `--seed`, while the training sample follows `--seed`. At seed 0 both draws use seed 0, as the spec says. Each draw is stratified: 1,000 reviews per label with pandas `groupby("label").sample(..., random_state=seed)`. Row ids are saved to `~/ml-data/results/lab04/ids-seed<S>.json` (smoke writes `ids-seed0-smoke.json`).
- "256 tokens for both models". Each review is cut at the character where its 254th word piece ends (the tokenizer's offset mapping, with [CLS] and [SEP] making 256), and that same text goes to both models. So TF-IDF reads exactly the words DistilBERT reads, and the change cuts both to 32 pieces the same way. Cutting TF-IDF by its own words instead would have handed it more text than DistilBERT sees.
- The break re-trains instead of loading saved models. `--break` trains both models from the same seed exactly as `--baseline` does, on reviews in normal order, then scores the test reviews in order and shuffled in the same run. No model is trained on shuffled text, which is what the spec's "no retraining" asks. This keeps each mode self-contained and avoids writing a 268 MB checkpoint per seed. The in-order accuracies reproduced the seed-0 baseline exactly.
- The shuffle permutes the whitespace-separated words of the 256-piece test text with `numpy.random.default_rng(seed)`, the same permutation for both models. A regex word never spans whitespace, so each review's TF-IDF counts are unchanged. A build check found DistilBERT's word-piece multiset unchanged too in 1,997 of the 2,000 reviews, and no shuffled review grew past 256 pieces, so the break changes order and nothing else.
- Training: a plain PyTorch loop, because the Trainer needs `accelerate`, which is not pinned. AdamW at 5e-5 (torch's default weight decay of 0.01), 2 epochs of shuffled batches of 16, a linear warm-up over the first 25 of 250 steps then a linear decay to 0 (`get_linear_schedule_with_warmup`), fp32, padding to the longest review in each batch, and no gradient clipping. `bert_train_s` times the loop only (model loading excluded), with `labkit.clock` synchronizing MPS at both ends. `tfidf_train_s` times `TfidfVectorizer()` plus `LogisticRegression(max_iter=1000)` fitting on the CPU.
- CPU cost: the first 1,000 test reviews in 20 batches of 50, one untimed warm-up batch, then the median batch time scaled to 1,000 reviews, tokenizing included. DistilBERT runs on the CPU after the MPS evaluation, with torch's default 10 threads; TF-IDF is single-threaded (`threads=1`). This is batched throughput: one request on its own and the p99 tail under load were not measured, so these lines support a cost per 1,000 items and no per-request latency claim. The break prints no cost lines, because its models equal the baseline's.
- Logging: `transformers` verbosity is set to error and its progress bars are off, so the logs show only the HW, SEED, DATA and RESULT lines (plus torch's harmless "Redirects are currently not supported in MacOs" note at import).
- The fallback download (the fast.ai `imdb.tgz`, converted to the same two parquet files) was not exercised in the build. Its row order differs from Hugging Face's, so a learner on the fallback gets other samples and should not expect these exact numbers.
- Smoke: 64 training and 64 test reviews, all three steps in one process on the same code path, 18.7 s and 19.9 s on the two smoke runs.

**Timing notes.** Two long lab 12 baselines and other light jobs ran beside all five reference runs, so CPU timings moved a lot across seeds: TF-IDF 76.3 to 166.218 ms per 1,000 and DistilBERT 16,796 to 19,327.9 ms per 1,000, with DistilBERT training at 90.1932 to 111.577 s. Read timings only within one run. No prediction asks about time.

</details>
