# 02. Ship it: a model is a service with a size, a p95 and inputs it has never seen

> Goal: after this I can measure p50 and p95 latency for single-image inference on one CPU thread and show how often the model gives a non-pet more than 0.9 probability. (No result values anywhere in this file.)

**Level:** W (see `ml-learning/CLAUDE.md`). **Output style:** Explanatory
**Concept link:** [`../README.md#inference-is-a-service`](../README.md#inference-is-a-service) (read after the lab)
**Borrowed from:** fast.ai [Lesson 2](https://course.fast.ai/Lessons/lesson2.html) (deployment with Gradio and Hugging Face Spaces); fastbook [ch 2, "From model to production"](https://github.com/fastai/fastbook/blob/master/02_production.ipynb). Do it after the lab, as the second contact 1 to 3 days later.
**Dataset:** lab 01's exported model (`~/ml-data/models/lab01/export.pkl`) and 200 held-out Oxford-IIIT Pet validation photos from its validation list (CC BY-SA 4.0, already on disk from lab 01's download); 20 Imagenette 160 validation photos from 5 non-animal classes (church, parachute, golf ball, gas pump, garbage truck; 4 each). Imagenette 160 px: 10 ImageNet classes, 9,469 train and 3,925 validation images, 99.0 MB, https://s3.amazonaws.com/fast-ai-imageclas/imagenette2-160.tgz, Apache-2.0. Shared with lab 35.
**Runs on:** cpu. **Lane:** light. **Compute:** 3 runs x at most 1 min (baseline, change and break each under 1 min, rounded up from the seed-0 reference runs), at most 6 min per run. Precomputed steps: none
**Needs:** base install only. Optional, never captured: `python -m pip install gradio==6.30.0` for a local UI around `learn.predict` (a Hugging Face Spaces deploy needs a login).
**Before the session** (from the module folder, see section 2): lab 01's `--baseline` at seed 0 has run (it writes `~/ml-data/models/lab01/`; without it this script prints lab 01's commands and exits 2). Then `python scripts/02_ship_it.py --download` (Imagenette, 99.0 MB, into `~/ml-data/imagenette2-160`) and `python scripts/02_ship_it.py --smoke`. Neither prints a result value: `--smoke` prints `SMOKE <name> ok` lines. Quit other CPU-heavy apps before the timed runs. Optional human step: the Gradio UI.
**Interview question:** Your model must answer in under 100 ms p95 on one CPU core and sometimes sees inputs unlike its training data: what do you measure, and what do you do with a wrong answer at 0.97 confidence?
**Repo link:** `hld/payments-risk-decisioning/deep-dives/latency-budget-and-hot-path.md` [§1 "The 100 ms, line by line"](../../../hld/payments-risk-decisioning/deep-dives/latency-budget-and-hot-path.md#1-the-100-ms-line-by-line) and [§5 "What else is in process, and why"](../../../hld/payments-risk-decisioning/deep-dives/latency-budget-and-hot-path.md#5-what-else-is-in-process-and-why)
**Captured by the script:** P1 to P3; p50, p95 and max at 224 and 160 px (200 timed calls each, after 10 warm-up calls, 1 CPU thread); accuracy at both sizes; the share of the 200 pet photos above 0.9; the export.pkl size and parameter count; the breed and top probability for each of the 20 non-pets (`NONPET` lines). **Human steps:** none for the record. The Gradio UI is optional and never captured.
**Status:** todo

## 0. Retrieval (0:00, 5 min, closed book, no AI)

The AI asks up to three due cards from `../../quiz-bank.md`, one at a time. Do not open the bank first.

## 1. Predict (0:05, 7 min, no AI)

Level W only: before the session, read `scripts/02_ship_it.py` (about 10 minutes) and answer its three `# Q:` prompts here. At 0:05 you only predict.

Read `percentile`, `latency_report`, `confident_share`, `serve`, `baseline`, `change`, `break_it` and `main`. `download`, `pet_files`, `non_pet_files`, `breed`, `report_latency` and `accuracy` are plumbing you can skip.

- Q1, why the first 10 calls are left out of the timings:
- Q2, what the 37 probabilities add up to, and what that leaves a non-pet:
- Q3, one CPU thread, and the core it runs on:

Write each row here before anything runs; the AI copies it into `../../prediction-log.md` word for word. A row that asks for several numbers becomes one log row per number, each with its own range.

| Step | Question | Kind | Prediction | 80% range or confidence |
|---|---|---|---|---|
| P1 | p95 latency in ms of one `learn.predict` call on one CPU thread (`torch.set_num_threads(1)`), after 10 warm-up calls. Lab 01's exported resnet34, inputs at 224 px, 200 timed calls: one per held-out pet photo (the first 200 files of lab 01's validation list by file name, which are cats of 6 breeds, Abyssinian to Egyptian Mau). Each request is one JPEG file's bytes, and the clock runs around the whole call (decode, resize, normalize, model, softmax). Percentile by nearest rank, seed 0. | num | | |
| P2 | The same model, photos and harness, but the model is handed 160 x 160 px inputs instead of 224 x 224 (only the last resize of the exported pipeline changes), seed 0. p95: up, down or same, and by what ratio to P1? Accuracy on the 200 photos: up, down or same, and by how many percentage points? | dir | | |
| P3 | Back at 224 px, the 20 non-pet photos (4 each from Imagenette's church, parachute, golf ball, gas pump and garbage truck validation folders, drawn with seed 0): what share of them (0 to 1) get a top breed probability above 0.9? | num | | |

## 2. Setup (before the session)

```
$ source ~/.venvs/ml/bin/activate
$ cd m1-whole-game    # from ml-learning/, where sessions start
$ python scripts/02_ship_it.py --download
$ python scripts/02_ship_it.py --smoke
```

## 3. Baseline (0:12, 10 min)

Why: a latency budget is a percentile on stated hardware, so the served model gets one measured p95, with its size and its accuracy, before anything changes.

```
$ python scripts/02_ship_it.py --baseline
(paste your RESULT lines)
```

Prediction vs actual, one sentence. The reference run is in `../../answers/`; the AI opens it only after your P1 row exists and you have pasted your own RESULT lines.

## 4. Change one thing (0:22, 10 min)

Why: input size is a serving knob. This run measures what it does to latency and to accuracy, with the same weights and the same 200 photos.

Change: the exported pipeline's last resize hands the model 160 x 160 px instead of 224 x 224 (`SIZE["change"]` in the script). P2 is logged above. `P2.p95_ratio_vs_224` and `P2.accuracy_delta_vs_224` print only after a `--baseline` run with the same seed.

```
$ python scripts/02_ship_it.py --change
(paste your RESULT lines)
```

## 5. Break it (0:32, 10 min, AI gives hints only; the run finishes by 0:40)

Why: a deployed model does not choose its inputs. This run asks the 37-breed model about photos from outside the 37 breeds.

Break: feed in the 20 Imagenette photos (church, parachute, golf ball, gas pump, garbage truck) at 224 px. P3 is logged above.

```
$ python scripts/02_ship_it.py --break
(paste your RESULT lines)
```

Why, in three sentences, written without AI:

## 6. Explain-back (0:42, 5 min) and rebuild (0:47, 10 min), no AI

- Five sentences for a smart engineer new to ML, written without AI. The AI names your weakest claim after the session (section 7).
- Rebuild: open `rebuild/02_latency_harness.py`, write the bodies of `percentile`, `latency_report` and `confident_share` from memory, then run `python rebuild/02_latency_harness.py`. Its `check()` compares `percentile` with `numpy.percentile(method="inverted_cdf")` at p50, p95 and p99, runs the harness on a fake model whose delays are known, and compares `confident_share` with numpy, never with this lab's results.

## 7. What I learned

After the session (about 5 minutes): the AI names the weakest claim in your five sentences and asks one question that tests it. Edit the sentences here.

## 8. Interview soundbite (one of the three cards written at 0:57)

> (one or two sentences only someone who ran this would say)

Staff follow-up (what pages at 3 am): in the repo's payments risk service the model has a stage deadline inside an 80 ms hard stop, and it runs in process. Which signal pages someone at 3 am, the model's p95 or something else, and what answer does a payment get while the model is slow? Answer in 2 sentences from latency-budget §1 and §5. Rotate: simplest design, failure modes, migration, what pages at 3 am, cost, trade-off.

## 9. Quiz cards (0:57, 3 min)

The AI drafts three cards (M, N, and T or D). Edit or replace them. Questions go to `../../quiz-bank.md`, keys to `../../answers/quiz-key.md`.

## Record

The script prints these as RESULT lines. Paste, do not type.

| Metric | Your run | Hardware (the script's HW line) | Captured by (script or learner) |
|---|---|---|---|
| `P1.p95_ms`: p95 at 224 px, ms | | | script |
| `baseline.p50_ms`: p50 at 224 px, ms | | | script |
| `baseline.max_ms`: slowest of the 200 calls at 224 px, ms | | | script |
| `baseline.accuracy`: fraction of the 200 pet photos right, 224 px | | | script |
| `baseline.pet_share_above_0_9`: fraction of the 200 pet photos with a top probability above 0.9 | | | script |
| `baseline.export_mb`: export.pkl, MB | | | script |
| `baseline.params`: parameters in the model | | | script |
| `P2.p95_ms`: p95 at 160 px, ms | | | script |
| `change.p50_ms`: p50 at 160 px, ms | | | script |
| `change.max_ms`: slowest call at 160 px, ms | | | script |
| `P2.accuracy`: fraction right, 160 px | | | script |
| `P2.p95_ratio_vs_224`: p95 at 160 px divided by p95 at 224 px | | | script |
| `P2.accuracy_delta_vs_224`: percentage points, 160 px minus 224 px | | | script |
| `P3.share_above_0_9`: fraction of the 20 non-pets with a top probability above 0.9 | | | script |
| `break.max_top_prob`: the highest top probability among the 20 non-pets | | | script |
| `NONPET` lines: the breed each non-pet was given, and its probability | | | script |
