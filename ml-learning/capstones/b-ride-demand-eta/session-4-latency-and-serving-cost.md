# B4. Latency budget and serving cost: p50 and p99 per prediction, and the cores at peak

> Goal: after this I can measure p50 and p99 ms per single-trip prediction of the B2 model in process on the M4 Pro, see what LightGBM's thread count does to the tail and to CPU time, and turn CPU-ms into cores at an assumed 10,000 predictions a second, against DeepETA's "within a few milliseconds at most". (No result values anywhere in this file. Capstones have no reference run and no answers file: your run is the answer.)

**Capstone:** [B, ride-hailing demand and ETA](README.md), session 4 of 4, labkit id 48. **Level:** B (see `ml-learning/CLAUDE.md`). **Output style:** Explanatory
**Builds on:** lab 24 (latency per decision and cores at a peak rate) and lab 20 (one feature function for both paths), plus your B2 model
**Dataset:** January 25 to 31, 2024 trips as requests ([Data](README.md#data)), with B2's saved model and tables; nyc.gov terms of use
**Runs on:** cpu. **Lane:** light, but run it with nothing else busy on the Mac: it measures latency. **Compute:** no reference run; 2 measured runs, each capped at 6 min. Precomputed steps: none
**Needs:** base install only
**Before the session:** B2 done at seed 0, so its model and tables sit in `~/ml-data/capstones/b/`. `--download` only checks them, then `--smoke`.
**Interview question:** Your ETA model must answer within a few milliseconds at 10,000 requests a second: what is its p99, and how many cores does it need?
**Repo link:** none for ETA: no repo file covers ETA ([README](README.md#repo-hld-it-maps-to)). The payments HLD's analogue: [`latency-budget-and-hot-path.md`, §5 What else is in process, and why](../../../hld/payments-risk-decisioning/deep-dives/latency-budget-and-hot-path.md#5-what-else-is-in-process-and-why) (a model server is a second fan-out leg with its own tail; the in-process GBDT runs on one core)
**Captured by the script:** P1 to P3 and every Record row. **Human steps:** your reading of "a few milliseconds", the design and the write-up
**Status:** todo

## 0. Framing (0:00, 7 min, no AI)

Reread the ETA framing line in `write-up.md`. Then define the loaded word, the scoping-drills rule: write the number of milliseconds you take DeepETA's "a few milliseconds" to mean, before anything runs.

"A few milliseconds" means ___ ms at p99 for me.

## 1. Predict (0:07, 5 min, no AI)

Write each row here and in `../../prediction-log.md` (Lab `B4`) before anything runs.

| Step | Question | Kind | Prediction | 80% range or confidence |
|---|---|---|---|---|
| P1 | p99 ms per single-trip prediction (the baseline and distance lookups plus the LightGBM residual, one row per call), LightGBM's default thread count, 10,000 requests from January 25 to 31 after 100 warm-up calls, the median p99 of 5 repeats | num | | |
| P2 | The same with `num_threads=1` in the predict call: p99 minus P1, in ms. Up, down or same, plus a size range | dir | | |
| P3 | Cores needed at an assumed peak of 10,000 predictions a second with `num_threads=1`: 10,000 x its CPU-ms per prediction / 1,000 | num | | |

Terms, fixed so the two thread settings compare:

- **Request.** One test trip's pickup zone, dropoff zone and pickup time. The serving path builds the 7 inputs with B2's feature function, looks up the baseline and the median past distance, and calls the model on a 1 x 7 numpy row. The prediction is baseline plus residual.
- **Wall clock.** `time.perf_counter_ns()` around the whole path, per request. p50 and p99 over the 10,000.
- **CPU time.** `time.process_time_ns()` over all 10,000 requests, which counts every thread of the process, divided by 10,000: CPU-ms per prediction.
- **Repeats.** 5 repeats of 10,000 requests. Report the median p50 and p99 and their spread across repeats (max minus min). Timing lines carry `device=cpu batch=1 warmup=100 n=10000 stat=median`.
- **Cost.** Cores = 10,000 x CPU-ms / 1,000. Dollars a month = cores x 730 hours x an assumed $0.04 per core-hour. Both the peak and the price are assumptions: label them so.

## 2. Setup (before the session)

```
$ source ~/.venvs/ml/bin/activate
$ cd ml-learning/capstones/b-ride-demand-eta
$ python scripts/b4_latency_and_serving_cost.py --download
$ python scripts/b4_latency_and_serving_cost.py --smoke
```

`--download` only checks that B2's model and tables exist, and prints their paths. `--smoke` times 200 requests and prints `SMOKE` lines, never a time.

## 3. Baseline (0:12, 15 min)

Why: an ETA is a service before it is a model, so its first number is the tail latency of one call.

You write first, in this file, no AI (about 5 min). This is the prompt the AI builds from:

1. What one request is, what the timer wraps, the warm-up, the repeats and the stop rule.
2. How CPU time is read, and how it can differ from wall time.
3. The RESULT contract: every name in the Record table, the mode that prints it, and its unit.

The AI then writes the script with `labkit.start(lab=48)`. Annotate each AI block with one line before the first run.

```
$ python scripts/b4_latency_and_serving_cost.py --smoke
$ python scripts/b4_latency_and_serving_cost.py --baseline
(paste your RESULT lines)
```

Prediction vs actual, one sentence. Then the conditions in prose, for example "`<t>` ms p99, M4 Pro, cpu, batch 1, default threads, median of 5 repeats of 10,000".

## 4. Change one thing (0:27, 15 min; the run finishes by 0:40)

Change: `num_threads=1` in the predict call. The model, the requests and the timer stay fixed. P2 and P3 are logged above.

Why: the thread count is set once and rarely revisited, and the wall clock and the CPU bill are two different numbers.

```
$ python scripts/b4_latency_and_serving_cost.py --change
(paste your RESULT lines)
```

Prediction vs actual, one sentence each for P2 and P3.

## 5. Write-up (0:42, 15 min, no AI)

- **Explain-back (5 min).** Five sentences for a smart engineer new to ML. Then ask the AI for the weakest claim, not a rewrite.
- **Deliverable (10 min).** Finish `write-up.md`: §4 Serving (p50 and p99 with their conditions, against your reading of "a few milliseconds"), §5 Cost (cores and dollars a month, assumptions labelled) and §6 Links (the [`hld/driver-hot-clusters/solution.md`](../../../hld/driver-hot-clusters/solution.md) link for demand, and the sentence "No repo file covers ETA."). Capstone B is done when all 6 parts exist.

## 6. What I learned

The five explain-back sentences, edited after the AI's question.

## 7. Interview soundbite (the card written at 0:57)

> One or two sentences only someone who ran this would say.

Framing: decision ___ | prediction time ___ | label and its maturity ___ | offline metric ___ | online metric ___ | guardrail ___

Staff follow-up (cost): what does serving cost per million ETAs at your measured CPU-ms, and what is the cheapest way to halve it? Answer in 2 sentences, using the repo link's reasons to keep a model in process.

## 8. Close (0:57, 3 min)

The AI drafts card `B4-D` (a symptom and the first check) from your run. Edit or replace it. The question goes to `../../quiz-bank.md`, the key to `../../answers/quiz-key.md`, citing your RESULT line. Set Status here and in the [README](README.md#sessions).

## Record

Suggested names: if your RESULT contract renames them, edit this table first. Paste, do not type.

| Metric | Your run | Hardware (the script's HW line) | Captured by (script or learner) |
|---|---|---|---|
| Your reading of "a few milliseconds", written before the run | | | learner |
| `baseline.p50_ms` (default threads) | | | script |
| `P1.p99_ms` (default threads) | | | script |
| `baseline.p99_spread_ms` (max minus min over the 5 repeats) | | | script |
| `baseline.cpu_ms_per_pred` (default threads) | | | script |
| `change.p50_ms` and `change.p99_ms` (`num_threads=1`) | | | script |
| `P2.p99_change_ms` (one thread minus default) | | | script |
| `change.p99_spread_ms` | | | script |
| `change.cpu_ms_per_pred` (`num_threads=1`) | | | script |
| `P3.cores_at_peak` (10,000 predictions a second, assumed) | | | script |
| `change.dollars_per_month` (at an assumed $0.04 per core-hour) | | | script |
