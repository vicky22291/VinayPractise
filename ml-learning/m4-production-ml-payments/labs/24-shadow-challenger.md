# 24. Shadow challenger: matched decline rates, swap sets and the latency bill

> Goal: after this I can replay 56,962 transactions through a champion and a shadow challenger, compare them at a matched decline rate, and state the p99 (99th-percentile latency) and core cost of each shadow design. (No result values anywhere in this file.)

**Level:** B (see `ml-learning/CLAUDE.md`). **Output style:** Explanatory
**Concept link:** [`../README.md#shadow-launches`](../README.md#shadow-launches) (read after the lab)
**Borrowed from:** AWS, [SageMaker shadow tests](https://docs.aws.amazon.com/sagemaker/latest/dg/shadow-tests.html); Google, [SRE (site reliability engineering) Workbook chapter 16, Canarying Releases](https://sre.google/workbook/canarying-releases/). Do it after the lab, as the second contact 1 to 3 days later.
**Dataset:** Credit Card Fraud, ULB (Université Libre de Bruxelles), OpenML 1597, `creditcard`: 284,807 card payments with 492 frauds (0.17%), V1 to V28 (components from PCA, principal component analysis), Amount and the label. 68.8 MB of ARFF (Attribute-Relation File Format), gzipped, or the 73.2 MB parquet fallback, <https://www.openml.org/d/1597>, licence Public (OpenML). The lab replays lab 22's 56,962 test payments one at a time through lab 22's saved champion (logistic regression) and challenger (LightGBM, 100 trees), read from `~/ml-data/models/lab22/`. `--download` adds a 1,000-tree LightGBM (3.6 MB) in `~/ml-data/models/lab24/`
**Runs on:** cpu. **Lane:** light. **Compute:** 3 runs x 1 min, at most 6 min per run. Precomputed steps: none
**Needs:** base install only
**Before the session** (from the module folder, see section 2): lab 22's `--baseline` at seed 0 has run, so `~/ml-data/models/lab22/` holds `champion_lr.joblib`, `challenger_lgbm.joblib` and `test_idx.npy`. OpenML 1597 sits in `~/ml-data/openml/` from lab 22's `--download`. There is no script yet: in section 3 you start `scripts/24_shadow_challenger.py`, the AI writes the harness from your design, and then `--download` (it trains the 1,000-tree LightGBM once, under a minute) and `--smoke` run. `--break` measures latency, so keep the Mac on power and quit other heavy apps first.
**Interview question:** How do you launch a new fraud model without declining good customers or adding checkout latency, and what does it cost in cores at 2,000 payments a second?
**Repo link:** [`hld/payments-risk-decisioning/deep-dives/latency-budget-and-hot-path.md`, §5 What else is in process, and why](../../../hld/payments-risk-decisioning/deep-dives/latency-budget-and-hot-path.md#5-what-else-is-in-process-and-why); [`hld/payments-risk-decisioning/deep-dives/model-lifecycle-shadow-and-labels.md`, §5 Proving a model before it declines anyone](../../../hld/payments-risk-decisioning/deep-dives/model-lifecycle-shadow-and-labels.md#5-proving-a-model-before-it-declines-anyone)
**Captured by the script:** P1 to P3 and every Record row. **Human steps:** none (you write the experiment design, the RESULT contract, `matched_threshold()` and `swap_sets()`)
**Status:** todo

## 0. Retrieval (0:00, 5 min, closed book, no AI)

The AI asks up to three due cards from `../../quiz-bank.md`, one at a time. Do not open the bank first.

## 1. Predict (0:05, 7 min, no AI)

Level B: there is no script to read. Read the Terms below, then predict before you open section 3.

Write each row here before anything runs; the AI copies it into `../../prediction-log.md` word for word. A row that asks for several numbers becomes one log row per number, each with its own range. Give rates and shares as fractions (0.5 is 50%).

| Step | Question | Kind | Prediction | 80% range or confidence |
|---|---|---|---|---|
| P1 | The champion's threshold is the 0.998 quantile of the champion's scores on the 56,962 replayed payments, so the champion declines 0.2% of them. Lab 22's LightGBM challenger (100 trees, `random_state` 0) is given that same threshold: the share of the 56,962 payments it declines | num | | |
| P2 | The challenger gets its own threshold instead, the 0.998 quantile of its own scores, so it also declines 0.2%. The share of the challenger's declines that the champion approves (swap-in count / challenger declines) | num | | |
| P3 | Lab 22's LightGBM challenger scored in a background thread of the same Python process, fed by a 50-slot bounded queue (seed 0 replay order, 56,962 single-row requests in 5 blocks): is the champion's p99 closer to its p99 alone or to its p99 with an inline shadow? | pick | | |

P3 is a pick: write alone or inline, and a confidence from 50 to 100.

Terms, fixed so your numbers compare with the reference:

- **Replay.** Lab 22's 56,962 test payments (its stratified 80/20 split at seed 0, the row positions in `test_idx.npy`). One payment is one 1 x 29 float64 row: V1 to V28 and Amount, the columns lab 22 trained on.
- **Models.** Lab 22's files, loaded and never retrained. Champion: `make_pipeline(StandardScaler(), LogisticRegression(max_iter=5000))`. Challenger: `LGBMClassifier(n_estimators=100, random_state=0)`. A score is `predict_proba(row)[0, 1]`. LightGBM runs with `n_jobs=1`: one thread per call, as a server scores one payment per request.
- **Thresholds and declines.** Decline when score > threshold. The champion's threshold is `numpy.quantile(champion scores on the 56,962 payments, 0.998)`. The matched threshold (step 4) is the same quantile of the challenger's own scores.
- **Swap sets.** Overlap: declined by both. Swap-in: declined by the challenger only. Swap-out: declined by the champion only. All three are counts.
- **Analyst review, simulated.** Each payment's held-out fraud label stands in for an analyst's verdict. The precision of a set is its fraud share.
- **Request.** One timed call: the champion's score on one row, the decline decision, then the shadow hand-off for that design. The clock is `time.perf_counter_ns()` around the whole request.
- **Designs.** Alone: the champion only. Inline: the challenger also scores the same row inside the request, before the reply. Thread: the request puts the row on a `queue.Queue(maxsize=50)` with `put_nowait` and returns. A `threading.Thread` in the same process takes rows off the queue and scores them. A row that finds the queue full is dropped and counted. Each pass starts a new thread with an empty queue. After the pass the thread scores what is still queued, then stops.
- **Walk.** A second shadow scorer: the challenger's own 100 trees (from `booster_.dump_model()`) walked in pure Python, which gives the same probabilities as LightGBM. It runs in the inline and thread designs too, and its RESULT names end in `_walk`.
- **Blocks and passes.** The replay order is `numpy.random.default_rng(seed).permutation` of the 56,962 payments, split into 5 blocks with `numpy.array_split`. Per block, in this order: one pass alone, then an inline pass and a thread pass for LightGBM, then the same two for the walk. A pass is 100 untimed warm-up requests (the block's first 100 rows), `gc.collect()`, then one timed request per row of the block. The 5 blocks are fixed in advance, with no early stop.
- **Latency statistics.** Per pass: p50 (the median) and p99 with `numpy.percentile(..., method="inverted_cdf")`. Reported: the median over the 5 blocks, and the block spread (max minus min of the 5 block p99s).
- **p99 position.** (thread p99 minus alone p99) / (inline p99 minus alone p99), with the same scorer in both designs: 0 is alone, 1 is inline. `P3.closer_to` is inline when the position is above 0.5, else alone.
- **Drop share.** Rows dropped / rows handed to the queue, warm-up included, over all 5 blocks.
- **CPU cost.** CPU-ms (milliseconds of processor time) per single-row `predict_proba`, from `time.thread_time_ns()` over the first 2,000 requests of the replay order, after 100 warm-up calls: the median of 5 passes. Measured for the champion, the 100-tree challenger and the 1,000-tree LightGBM. Cores at 2,000 decisions a second = 2,000 x CPU-ms / 1,000.
- **1,000-tree LightGBM.** Lab 22's challenger parameters with `n_estimators=1000` and `learning_rate=0.01`, trained once by `--download` on lab 22's 227,845 training rows and saved to `~/ml-data/models/lab24/`.
- **Seed.** `--seed` sets the replay order only. The models and the test set are fixed.

## 2. Setup (before the session)

```
$ source ~/.venvs/ml/bin/activate
$ cd m4-production-ml-payments    # from ml-learning/, where sessions start
$ ls ~/ml-data/models/lab22/
```

Level B ships no script, so nothing else runs before the session. If `ls` does not show `champion_lr.joblib`, `challenger_lgbm.joblib` and `test_idx.npy`, run lab 22's `python scripts/22_calibration_and_thresholds.py --baseline` (seed 0) first. Once the script exists (you start it in section 3, and the AI extends it):

```
$ python scripts/24_shadow_challenger.py --download
$ python scripts/24_shadow_challenger.py --smoke
```

`--download` checks OpenML 1597 and lab 22's three files, then trains the 1,000-tree LightGBM once. `--smoke` runs all three modes on 3,000 payments (600 requests in the break path) and prints `SMOKE <name> ok` lines, never values.

## 3. Baseline (0:12, 10 min)

Why: a threshold is a point on one model's score scale, so first see what the champion's threshold does on the challenger's scale.

You write first, in this file, no AI (about 5 min). This is the prompt the AI builds from:

1. The experiment design for all three steps: what is replayed, the warm-up, the repeats, the stop rule, and what counts as the champion path (what sits inside the clock). Write it, then check it against the Terms. Add one line each for the choices the Terms leave open:
   - Where the champion's threshold would come from before a real launch, since here it comes from the replayed payments themselves.
   - Why each pass gets warm-up requests and a `gc.collect()` before the clock starts.
   - What you would do if a block spread came out larger than the gap you want to see.
   - How the harness shows whether the thread shadow kept up with the replay.
   - One Terms choice you would change for a real launch, and why.
2. The RESULT contract: every name in the Record table, the mode that prints it, and its unit. Each mode prints only its own rows.

Then write `matched_threshold(scores, decline_rate)` yourself (about 2 min): the threshold, by quantile, at which `decline_rate` of `scores` are declined (decline when score > threshold). Put it in a new file, `scripts/24_shadow_challenger.py`, which the AI then extends.

The AI then extends the file from your prompt. It writes `--download`, the loading of lab 22's files, the three modes, the inline and thread designs, the walk and the CPU-time cost. It leaves `swap_sets()` as a stub for section 4. In `--smoke` only, the harness stands in numpy's `intersect1d` and `setdiff1d` for it, with one comment saying smoke checks the plumbing only. Annotate each AI block with one line before the first run.

```
$ python scripts/24_shadow_challenger.py --download
$ python scripts/24_shadow_challenger.py --smoke
$ python scripts/24_shadow_challenger.py --baseline
(paste your RESULT lines)
```

Prediction vs actual, one sentence. The reference run is in `../../answers/`; the AI opens it only after your P1 row exists and you have pasted your own RESULT lines.

## 4. Change one thing (0:22, 10 min)

Change: match the challenger's decline rate to the champion's 0.2% with a quantile threshold (`matched_threshold()` on the challenger's own scores), instead of reusing the champion's threshold. P2 is logged above.

Why: a launch decision compares two models at the same operating point, and only the swap sets change any payment's decision.

You write first, no AI (about 2 min): the body of `swap_sets(champ_decl, chal_decl)`. Two boolean decline masks over the same payments go in. `(overlap, swap_in, swap_out)` comes out, as counts.

```
$ python scripts/24_shadow_challenger.py --change
(paste your RESULT lines)
```

## 5. Break it (0:32, 10 min, AI gives hints only; the run finishes by 0:40)

Break: run the shadow in the request path (inline), then in a background thread in the same process with a 50-slot bounded queue. P3 is logged above.

Why: a shadow is only safe to run in production once you know what it does to the champion's latency, so measure where each design puts the challenger's work. The same run measures the cost rows: CPU-ms per decision for the champion and for LightGBM with 100 and 1,000 trees, and the cores each needs at 2,000 decisions a second.

`--break` takes about a minute. Keep other apps quiet while it runs.

```
$ python scripts/24_shadow_challenger.py --break
(paste your RESULT lines)
```

Why, in three sentences, written without AI:

## 6. Explain-back (0:42, 5 min) and rebuild (0:47, 10 min), no AI

- Five sentences for a smart engineer new to ML, written without AI. The AI names your weakest claim after the session (section 7).
- Rebuild: open `rebuild/24_swap_sets.py`, write `matched_threshold()` and `swap_sets()` from memory, then run `python rebuild/24_swap_sets.py`. Its `check()` compares with numpy (the decline rate within 1/n of the target on synthetic scores, and the three counts against `intersect1d` and `setdiff1d` on the declined indices), never with this lab's results.

## 7. What I learned

After the session (about 5 minutes): the AI names the weakest claim in your five sentences and asks one question that tests it. Edit the sentences here.

## 8. Interview soundbite (one of the three cards written at 0:57)

> One or two sentences only someone who ran this would say.

Framing line, yours to fill: decision | prediction time | label and its maturity | offline metric | online metric | guardrail.

Staff follow-up (what pages at 3 am): the repo scores its shadow after the response, in the same process (§5 of the latency-budget deep dive). Name the two shadow metrics you would page on, with a threshold for each, and the §5 lifecycle gate each one protects. Answer in 2 sentences from the repo links. Rotate: simplest design, failure modes, migration, what pages at 3 am, cost, trade-off.

## 9. Quiz cards (0:57, 3 min)

The AI drafts three cards (M, N, and T or D). Edit or replace them. Questions go to `../../quiz-bank.md`, keys to `../../answers/quiz-key.md`.

## Record

The script prints these as RESULT lines. Paste, do not type.

| Metric | Your run | Hardware (the script's HW line) | Captured by (script or learner) |
|---|---|---|---|
| `P1.challenger_decline_rate` (the challenger at the champion's threshold, fraction of the 56,962) | | | script |
| `baseline.champion_threshold` (the champion's 0.998 quantile, probability) | | | script |
| `baseline.champion_decline_rate` (the champion at its own threshold, fraction) | | | script |
| `baseline.challenger_declines` (the challenger at the champion's threshold, count) | | | script |
| `P2.swap_in_share` (swap-in / challenger declines at the matched rate, fraction) | | | script |
| `change.challenger_threshold` (the challenger's own 0.998 quantile, probability) | | | script |
| `change.challenger_decline_rate` (the challenger at its own threshold, fraction) | | | script |
| `change.overlap` (declined by both, count) | | | script |
| `change.swap_in` (declined by the challenger only, count) | | | script |
| `change.swap_out` (declined by the champion only, count) | | | script |
| `change.swap_in_precision` (fraud share of the swap-in set: the simulated analyst review) | | | script |
| `change.swap_out_precision` (fraud share of the swap-out set) | | | script |
| `P3.closer_to` (alone or inline, the LightGBM thread shadow) | | | script |
| `break.thread_p99_position` (the LightGBM thread design between alone, 0, and inline, 1, ratio) | | | script |
| `break.thread_drop_share` (rows dropped / rows handed to the LightGBM thread shadow, fraction) | | | script |
| `break.thread_walk_p99_position` (the same position for the walk, ratio) | | | script |
| `break.thread_walk_drop_share` (the same drop share for the walk, fraction) | | | script |
| `break.p50_alone_ms` (champion alone, median of the 5 block p50s, ms) | | | script |
| `break.p99_alone_ms` (champion alone, median of the 5 block p99s, ms) | | | script |
| `break.p99_block_spread_alone_ms` (max minus min of the 5 block p99s, ms) | | | script |
| `break.p50_inline_ms` (LightGBM inline, median of block p50s, ms) | | | script |
| `break.p99_inline_ms` (LightGBM inline, median of block p99s, ms) | | | script |
| `break.p99_block_spread_inline_ms` (LightGBM inline, block spread, ms) | | | script |
| `break.p50_thread_ms` (LightGBM thread, median of block p50s, ms) | | | script |
| `break.p99_thread_ms` (LightGBM thread, median of block p99s, ms) | | | script |
| `break.p99_block_spread_thread_ms` (LightGBM thread, block spread, ms) | | | script |
| `break.p50_inline_walk_ms` (walk inline, median of block p50s, ms) | | | script |
| `break.p99_inline_walk_ms` (walk inline, median of block p99s, ms) | | | script |
| `break.p99_block_spread_inline_walk_ms` (walk inline, block spread, ms) | | | script |
| `break.p50_thread_walk_ms` (walk thread, median of block p50s, ms) | | | script |
| `break.p99_thread_walk_ms` (walk thread, median of block p99s, ms) | | | script |
| `break.p99_block_spread_thread_walk_ms` (walk thread, block spread, ms) | | | script |
| `break.cpu_ms_champion` (CPU-ms per single-row call, median of 5 passes) | | | script |
| `break.cores_champion` (cores at 2,000 decisions a second) | | | script |
| `break.cpu_ms_lgbm_100` (CPU-ms per call, 100-tree LightGBM) | | | script |
| `break.cores_lgbm_100` (cores at 2,000 decisions a second, 100 trees) | | | script |
| `break.cpu_ms_lgbm_1000` (CPU-ms per call, 1,000-tree LightGBM) | | | script |
| `break.cores_lgbm_1000` (cores at 2,000 decisions a second, 1,000 trees) | | | script |
