# 35. Learning-rate finder and one-cycle

> Goal: after this I can run lr_find, train a ResNet from scratch on Imagenette at 128 px for 5 epochs with one-cycle, and compare it with a constant rate and a 10x rate. (No result values anywhere in this file.)

**Level:** C (see `ml-learning/CLAUDE.md`). **Output style:** Learning
**Concept link:** [`../README.md#learning-rates-and-one-cycle`](../README.md#learning-rates-and-one-cycle) (read after the lab)
**Borrowed from:** fastbook ch 5, "The Learning Rate Finder" ([05_pet_breeds.ipynb](https://github.com/fastai/fastbook/blob/master/05_pet_breeds.ipynb)); fastbook ch 7, "Imagenette" and "Normalization" ([07_sizing_and_tta.ipynb](https://github.com/fastai/fastbook/blob/master/07_sizing_and_tta.ipynb)); fast.ai Part 2 [Lesson 18](https://course.fast.ai/Lessons/lesson18.html), "Accelerated SGD & ResNets"; Smith 2018, the one-cycle paper ([arXiv 1803.09820](https://arxiv.org/abs/1803.09820)). Do it after the lab, as the second contact 1 to 3 days later.
**Dataset:** Imagenette 160 px (fast.ai), 10 ImageNet classes, 9,469 train and 3,925 validation images (the official split), 99.0 MB, https://s3.amazonaws.com/fast-ai-imageclas/imagenette2-160.tgz, Apache-2.0. Trained at 128 px. Shared with lab 02. Saved in `~/ml-data/imagenette2-160`.
**Runs on:** mps. **Lane:** heavy. **Compute:** 3 runs x 4 min, at most 6 min per run. Precomputed steps: none
**Needs:** base install only
**Before the session** (from the module folder, see section 2): `--download` (99.0 MB into `~/ml-data/imagenette2-160`), then `--smoke`, which passes with the TODO still open. Close other GPU-heavy apps.
**Interview question:** A 5-day training job diverges on day 3: what do you check, and how do you pick a learning rate without a full sweep?
**Repo link:** [`databricks/posts/fast-fault-tolerant-pytorch-training-ai-runtime.md`](../../../databricks/posts/fast-fault-tolerant-pytorch-training-ai-runtime.md#impact-2-checkpoint-frequency-decides-your-recovery-cost), "Impact 2: Checkpoint frequency decides your recovery cost", and ["Impact 4: Forgetting the data pipeline silently corrupts your model"](../../../databricks/posts/fast-fault-tolerant-pytorch-training-ai-runtime.md#impact-4-forgetting-the-data-pipeline-silently-corrupts-your-model) (what a resume must restore besides the weights)
**Captured by the script:** every Record row, from `--baseline`, `--change` and `--break`, plus the lr_find plot. **Human steps:** none (you write the `lr_find()` body, and `--check` grades it)
**Status:** todo

## 0. Retrieval (0:00, 5 min, closed book, no AI)

The AI asks up to three due cards from `../../quiz-bank.md`, one at a time. Do not open the bank first.

## 1. Predict (0:05, 7 min, no AI)

Level C: predict first. You write the `TODO(human)` in section 3, before the baseline runs.

Write each row here before anything runs; the AI copies it into `../../prediction-log.md` word for word. A row that asks for several numbers becomes one log row per number, each with its own range.

Every step uses the same setup. The model is fastai's xresnet18 (a ResNet-18 variant) with random weights and fastai's head for the 10 classes: `vision_learner(dls, xresnet18, pretrained=False)`. It trains on the 9,469 training images at 128 px (`Resize(128)`: a square crop, at a random spot in training and centered for validation), batch 64, AdamW with fastai's Adam defaults (betas 0.9 and 0.99, eps 1e-5, weight decay 0.01), seed 0, 5 epochs. Each run first calls your `lr_find()`: 100 steps, rates from 1e-7 to 10. The suggested rate is fastbook ch 5's rule, fastai's `minimum`: one tenth of the rate where the smoothed loss is lowest, read from the curve without its first 10 and last 5 points, as fastai's own `lr_find` reads it. Accuracy is on the 3,925 validation images after epoch 5, in percent.

| Step | Question | Kind | Prediction | 80% range or confidence |
|---|---|---|---|---|
| P1 | Validation accuracy (percent) after 5 epochs of `fit_one_cycle` at the suggested rate (xresnet18 from scratch, 128 px, batch 64, seed 0). For scale: the Imagenette leaderboard shows 87.43% at 128 px in 5 epochs, from fastai's `train_imagenette.py` plus MaxBlurPool and tuned hyperparameters, the mean of 5 runs | num | | |
| P2 | `fit` at a constant rate equal to the same peak, instead of `fit_one_cycle` (no warmup, no annealing, momentum fixed at 0.9), 5 epochs, seed 0: validation accuracy up, down or same vs P1, and by how many points | dir | | |
| P3 | `fit_one_cycle` at 10x the suggested rate, 5 epochs, seed 0: validation accuracy (percent) | num | | |

## 2. Setup (before the session)

```
$ source ~/.venvs/ml/bin/activate
$ cd m6-deep-nets-on-a-mac    # from ml-learning/, where sessions start
$ python scripts/35_learning_rates_and_one_cycle.py --download
$ python scripts/35_learning_rates_and_one_cycle.py --smoke
```

`--smoke` runs all three steps on one image in 20 for 2 epochs each, with fastai's own `lr_find` standing in for your TODO. Its one value line, `smoke.sec_per_full_epoch_est`, is a calibration: the second smoke epoch scaled up to all the images.

## 3. Baseline (0:12, 10 min)

Why: lr_find costs about 100 mini-batches instead of a sweep of full runs, and one-cycle at its suggestion is fastai's default recipe for training from scratch.

First the TODO: write the body of `lr_find()` in `scripts/35_learning_rates_and_one_cycle.py` (marked `TODO(human)`; its docstring is the spec). The AI may give hints, or a draft explained line by line that you type. Then run `python scripts/35_learning_rates_and_one_cycle.py --check` until it prints `check: PASS`. It runs your function on a 20-row fixture (a linear model, SGD with momentum) and compares the rates with `np.geomspace`, the smoothed losses with pandas `ewm(adjust=True)`, the stop with the 4x rule, and the weights and optimizer state after the call with deep copies taken before it. Every measured mode calls your function first.

The baseline also draws the lr_find curve (the `PLOT` line names the PNG in `~/ml-data/results/lab35/`). It prints fastai 2.8's default rule, `valley`, next to the suggested rate, for comparison: no run trains at it. And it times every epoch twice: once reading the clock after `torch.mps.synchronize()`, once reading it without the sync.

```
$ python scripts/35_learning_rates_and_one_cycle.py --baseline
(paste your RESULT lines)
```

Prediction vs actual, one sentence. The reference run is in `../../answers/`; the AI opens it only after your P1 row exists and you have pasted your own RESULT lines.

## 4. Change one thing (0:22, 10 min)

Change: a constant learning rate at the same peak instead of one-cycle, `learn.fit(5, peak)` in place of `learn.fit_one_cycle(5, peak)`. P2 is logged above.

Why: one-cycle changes the rate at every step, with a warmup from peak/25 and an anneal down to peak/1e5. The constant rate removes both phases and keeps everything else. The run calls your `lr_find()` again at the same seed, and `change.peak_lr` shows the peak it used.

```
$ python scripts/35_learning_rates_and_one_cycle.py --change
(paste your RESULT lines)
```

## 5. Break it (0:32, 10 min, AI gives hints only; the run finishes by 0:40)

Break: one-cycle at 10x the suggested rate, with the same warmup and anneal shape. P3 is logged above.

Why: 10x is one decade to the right on the lr_find plot's log axis, the size of slip a hand-picked rate makes.

```
$ python scripts/35_learning_rates_and_one_cycle.py --break
(paste your RESULT lines)
```

Why, in three sentences, written without AI:

## 6. Explain-back (0:42, 5 min) and rebuild (0:47, 10 min), no AI

- Five sentences for a smart engineer new to ML, written without AI. The AI names your weakest claim after the session (section 7).
- Rebuild: open `rebuild/35_lr_find.py`, write the body of `lr_find()` from memory, without looking at your TODO (about 20 lines: save, step at a growing rate, smooth, stop, restore), then run `python rebuild/35_lr_find.py`. Its `check()` compares with numpy (`np.geomspace`), pandas (`ewm` with `adjust=True`) and torch (`state_dict`, `torch.equal`) on a toy network with a BatchNorm layer, never with this lab's results.

## 7. What I learned

After the session (about 5 minutes): the AI names the weakest claim in your five sentences and asks one question that tests it. Edit the sentences here.

## 8. Interview soundbite (one of the three cards written at 0:57)

> One or two sentences only someone who ran this would say.

Staff follow-up: failure modes. The job that diverged on day 3 had just resumed from a checkpoint. Which state besides the weights must the resume restore, and which extra piece does a one-cycle job need that a constant-rate job does not? Answered in 2 sentences from the repo link. Rotate: simplest design, failure modes, migration, what pages at 3 am, cost, trade-off.

## 9. Quiz cards (0:57, 3 min)

The AI drafts three cards (M, N, and T or D). Edit or replace them. Questions go to `../../quiz-bank.md`, keys to `../../answers/quiz-key.md`.

## Record

The script prints these as RESULT lines. Paste, do not type.

| Metric | Your run | Hardware (the script's HW line) | Captured by (script or learner) |
|---|---|---|---|
| `baseline.lr_find_steps`: steps your `lr_find()` took before it stopped, of 100 (steps) | | | script |
| `baseline.suggested_lr`: the suggested rate, fastai's `minimum` rule on your curve (lr) | | | script |
| `baseline.valley_lr`: fastai 2.8's default rule, `valley`, on the same curve, for comparison only (lr) | | | script |
| The lr_find curve: the PNG on the `PLOT` line, in `~/ml-data/results/lab35/` | | | script |
| `P1.valid_acc`: one-cycle at the suggested rate, after epoch 5 (percent) | | | script |
| `baseline.acc_by_epoch`: validation accuracy after epochs 1 to 5 (percent) | | | script |
| `baseline.sec_per_epoch`: seconds per epoch, train plus validation, clock read after `torch.mps.synchronize()`, median of epochs 2 to 5 (s) | | | script |
| `baseline.sec_per_epoch_nosync`: the same epochs, clock read without the sync (s) | | | script |
| `change.peak_lr`: the constant rate (lr) | | | script |
| `P2.valid_acc`: constant rate, after epoch 5 (percent) | | | script |
| `P2.delta_vs_P1`: P2 minus P1, same seed (points) | | | script |
| `change.acc_by_epoch`: constant rate, epochs 1 to 5 (percent) | | | script |
| `break.peak_lr`: 10x the suggested rate (lr) | | | script |
| `P3.valid_acc`: one-cycle at 10x, after epoch 5 (percent) | | | script |
| `break.delta_vs_P1`: P3 minus P1, same seed (points) | | | script |
| `break.acc_by_epoch`: one-cycle at 10x, epochs 1 to 5 (percent) | | | script |
