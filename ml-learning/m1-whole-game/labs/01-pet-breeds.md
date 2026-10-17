# 01. Pet breeds: reuse all, part or none of a pretrained network

> Goal: after this I can fine-tune a pretrained ResNet-34 on 37 pet breeds in one run of under 4 minutes on this Mac, and say, with error rates, what pretraining and freezing each buy. (No result values anywhere in this file.)

**Level:** W (see `ml-learning/CLAUDE.md`). **Output style:** Explanatory
**Concept link:** [`../README.md#transfer-learning`](../README.md#transfer-learning) (read after the lab)
**Borrowed from:** fast.ai [Lesson 1](https://course.fast.ai/Lessons/lesson1.html) and [Lesson 2](https://course.fast.ai/Lessons/lesson2.html); fastbook [ch 1](https://github.com/fastai/fastbook/blob/master/01_intro.ipynb) (cats vs dogs on the same Oxford-IIIT Pet photos) and [ch 5](https://github.com/fastai/fastbook/blob/master/05_pet_breeds.ipynb) (pet breeds); the Kaggle notebook ['Is it a bird?'](https://www.kaggle.com/code/jhoward/is-it-a-bird-creating-a-model-from-your-own-data) for the optional own-images extra. Do it after the lab, as the second contact 1 to 3 days later. Both chapters print results for setups close to this lab's, so open them only after your runs.
**Dataset:** Oxford-IIIT Pet, 7,390 images of 37 breeds (12 cat and 25 dog breeds, about 200 each), 811.7 MB, https://s3.amazonaws.com/fast-ai-imageclas/oxford-iiit-pet.tgz (fallback: the originals at https://www.robots.ox.ac.uk/~vgg/data/pets/), CC BY-SA 4.0
**Runs on:** mps. **Lane:** heavy. **Compute:** 3 runs x at most 4 min (baseline 4, change 4, break 4, rounded up from the reference runs), at most 6 min per run. Precomputed steps: none
**Needs:** base install only. The optional own-images extra, never captured: `python -m pip install ddgs==9.16.0` (DuckDuckGo may answer scripts with HTTP 202)
**Before the session** (from the module folder, see section 2): `python scripts/01_pet_breeds.py --download` (the 812 MB Pets archive plus the ResNet-34 ImageNet weights from download.pytorch.org), then `python scripts/01_pet_breeds.py --smoke` (under a minute). Optional human step: your own 2-class images with ddgs for the extra.
**Interview question:** You have 200 labelled photos and one day: how do you ship a usable classifier, how much does pretraining save over random weights, and when would you fine-tune the whole backbone instead of only a new head?
**Repo link:** `hld/streetview-ingestion/deep-dives/privacy-blur-and-takedowns.md` [§1 "Recall first, because the detector will miss"](../../../hld/streetview-ingestion/deep-dives/privacy-blur-and-takedowns.md#1-recall-first-because-the-detector-will-miss); `hld/streetview-ingestion/deep-dives/processing-pipeline-and-reprocessing.md` [§10 "The blur-model backfill"](../../../hld/streetview-ingestion/deep-dives/processing-pipeline-and-reprocessing.md#10-the-blur-model-backfill-from-19-b-re-tiles-to-500-m)
**Captured by the script:** P1 to P3 error rates, seconds per epoch for each run, trainable parameters frozen and unfrozen, best accuracy vs Parkhi 2012, the export.pkl size; at seed 0 the baseline also saves `~/ml-data/models/lab01/export.pkl` and `valid_files.txt` for lab 02. **Human steps:** none for the record; the own-images extra is optional and never captured.
**Status:** todo

## 0. Retrieval (0:00, 5 min, closed book, no AI)

This is the first lab, so `../../quiz-bank.md` has no due cards yet. The AI asks items 20, 24 and 26 of the fastbook chapter 1 questionnaire instead, one at a time. Do not look them up first.

Ungraded warm-up: after each answer the AI gives the chapter's answer in two sentences. These items do not go into `../../quiz-bank.md`.

## 1. Predict (0:05, 7 min, no AI)

Level W only: before the session, read `scripts/01_pet_breeds.py` (about 10 minutes) and answer its three `# Q:` prompts here. At 0:05 you only predict.

Read `pet_dataloaders`, `trainable`, `baseline`, `KeepFrozen`, `change` and `break_it`. `download`, `EpochTimer`, `quiet` and `timing` are plumbing you can skip.

- Q1, `Resize(448)` first, then 224 px:
- Q2, the two epochs of `fine_tune(1)`:
- Q3, what still trains with the body frozen:

Write each row here before anything runs; the AI copies it into `../../prediction-log.md` word for word. A row that asks for several numbers becomes one log row per number, each with its own range.

| Step | Question | Kind | Prediction | 80% range or confidence |
|---|---|---|---|---|
| P1 | Error rate (fraction wrong) on the 20% validation split (1,478 images, `RandomSplitter(0.2, seed=42)`) after `fine_tune(1)`: 1 frozen epoch, then 1 unfrozen. Pretrained resnet34, presize 448 px, 224 px crops, batch 64, base learning rate 2e-3, seed 0. | num | | |
| P2 | The same `fine_tune(1, base_lr=2e-3)` call as P1 (same start, schedule, learning rates and seed 0), but the body stays frozen for both epochs: a `KeepFrozen` callback freezes it again after `fine_tune` unfreezes it. Error rate up, down or same vs P1, and by how many percentage points of error rate (1 point = 0.01)? | dir | | |
| P3 | The same resnet34 from random weights (`pretrained=False`), every layer training, `fit_one_cycle(2, 2e-3)`, seed 0: error rate as a fraction wrong (1 minus accuracy). Published reference: Parkhi et al. 2012 reached 59.21% accuracy. | num | | |

## 2. Setup (before the session)

```
$ source ~/.venvs/ml/bin/activate
$ cd m1-whole-game    # from ml-learning/, where sessions start
$ python scripts/01_pet_breeds.py --download
$ python scripts/01_pet_breeds.py --smoke
```

## 3. Baseline (0:12, 10 min)

Why: the standard recipe (an ImageNet body, a new 37-class head, `fine_tune`) is the bar the change and the break are measured against.

```
$ python scripts/01_pet_breeds.py --baseline
(paste your RESULT lines)
```

Prediction vs actual, one sentence. The reference run is in `../../answers/`; the AI opens it only after your P1 row exists and you have pasted your own RESULT lines.

## 4. Change one thing (0:22, 10 min)

Why: it changes one knob, whether the body unfreezes for the second epoch. The call, schedule, learning rates, data and seed are the baseline's, so `P2.delta_vs_P1` measures that one difference.

Change: pass `KeepFrozen()` to the baseline's `fine_tune(1)` call. Its `before_fit` calls `learn.freeze()` at the start of every fit, so `fine_tune`'s unfreeze step does not take effect. P2 is logged above. `P2.delta_vs_P1` prints only after a `--baseline` run with the same seed.

```
$ python scripts/01_pet_breeds.py --change
(paste your RESULT lines)
```

## 5. Break it (0:32, 10 min, AI gives hints only; the run finishes by 0:40)

Why: it asks what the ImageNet starting point is worth, with the architecture, data, epochs and base learning rate held fixed. It is not a one-knob test. Against the baseline the schedule also changes (`fit_one_cycle`, not `fine_tune`). Against the change the schedule changes too, and every layer trains instead of a frozen body. So each gap mixes the starting weights with other differences.

Break: build the same resnet34 with `pretrained=False` and train every layer for the same 2 epochs, `fit_one_cycle(2, 2e-3)`. P3 is logged above. Start it by 0:34.

```
$ python scripts/01_pet_breeds.py --break
(paste your RESULT lines)
```

Why, in three sentences, written without AI:

## 6. Explain-back (0:42, 5 min) and rebuild (0:47, 10 min), no AI

- Five sentences for a smart engineer new to ML, written without AI. The AI names your weakest claim after the session (section 7).
- Rebuild: open `rebuild/01_fine_tune_by_hand.py`, write the bodies of `trainable` and `fine_tune_by_hand` from memory, then run `python rebuild/01_fine_tune_by_hand.py`. It is a simplified `fine_tune`: its freezing, parameter groups and schedule are simpler than fastai's, so follow its docstring. Its `check()` compares with torch.nn and torchvision's `resnet18` (parameter counts, learning rates, which weights move), never with this lab's results.

## 7. What I learned

After the session (about 5 minutes): the AI names the weakest claim in your five sentences and asks one question that tests it. Edit the sentences here.

## 8. Interview soundbite (one of the three cards written at 0:57)

> (one or two sentences only someone who ran this would say)

Staff follow-up (simplest design): the Street View face and plate blur in the repo link runs an image detector that will miss. What is the simplest design that ships with a detector you know misses, and what does swapping in a better model cost later? Answer in 2 sentences from privacy-blur §1 and processing-pipeline §10. Rotate: simplest design, failure modes, migration, what pages at 3 am, cost, trade-off.

## 9. Quiz cards (0:57, 3 min)

The AI drafts three cards (M, N, and T or D). Edit or replace them. Questions go to `../../quiz-bank.md`, keys to `../../answers/quiz-key.md`.

## Record

The script prints these as RESULT lines. Paste, do not type.

| Metric | Your run | Hardware (the script's HW line) | Captured by (script or learner) |
|---|---|---|---|
| `P1.error_rate`: fine-tuned, fraction | | | script |
| `P2.error_rate`: body frozen, fraction | | | script |
| `P2.delta_vs_P1`: percentage points of error rate | | | script |
| `P3.error_rate`: random weights, fraction | | | script |
| `baseline.trainable_frozen`: parameters | | | script |
| `baseline.trainable_unfrozen`: parameters | | | script |
| `baseline.sec_per_epoch_frozen`: s | | | script |
| `baseline.sec_per_epoch_unfrozen`: s | | | script |
| `change.sec_per_epoch`: s, median of 2 | | | script |
| `break.sec_per_epoch`: s, median of 2 | | | script |
| `break.best_accuracy`: best of the three runs, fraction | | | script |
| `break.best_minus_parkhi`: percentage points vs 59.21% | | | script |
| `baseline.export_mb`: MB | | | script |
