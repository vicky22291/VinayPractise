# 37. Overfit on purpose, then regularise

> Goal: after this I can measure the train-validation gap at 500 and 5,000 images and show what random crop and flip do to it. (No result values anywhere in this file.)

**Level:** S (see `ml-learning/CLAUDE.md`). **Output style:** Explanatory
**Concept link:** [`../README.md#overfitting-and-regularisation`](../README.md#overfitting-and-regularisation) (read after the lab)
**Borrowed from:** Kaggle Learn [Intro to Deep Learning](https://www.kaggle.com/learn/intro-to-deep-learning), lessons ["Overfitting and Underfitting"](https://www.kaggle.com/code/ryanholbrook/overfitting-and-underfitting) and ["Dropout and Batch Normalization"](https://www.kaggle.com/code/ryanholbrook/dropout-and-batch-normalization) (they use Keras: read them, then port the exercise to PyTorch); fastbook ch 7, data augmentation ([07_sizing_and_tta.ipynb](https://github.com/fastai/fastbook/blob/master/07_sizing_and_tta.ipynb)). Do it after the lab, as the second contact 1 to 3 days later.
**Dataset:** CIFAR-10, 50,000 train and 10,000 test images at 32x32 in 10 classes, 170.50 MB, the Toronto python tar https://www.cs.toronto.edu/~kriz/cifar-10-python.tar.gz (fallback built in: the Hugging Face parquet copy, https://huggingface.co/datasets/uoft-cs/cifar10). The lab uses 5,000 training images (500 per class, seed 0), 500 of those (50 per class) for the break, and all 10,000 test images as the validation set. Licence: "unknown" in the Hugging Face card's licence field. Saved in `~/ml-data/cifar10`.
**Runs on:** mps. **Lane:** heavy. **Compute:** 3 runs x 1 min, at most 6 min per run. Precomputed steps: none
**Needs:** base install only
**Before the session** (from the module folder, see section 2): `--download` (170.5 MB into `~/ml-data/cifar10`, then one `cifar10.npz`; the Toronto server can be slow, so start it a day early), then `--smoke` (under a minute, a stand-in model checks the data and the RESULT contract). Close other GPU-heavy apps.
**Interview question:** You have 5,000 labelled images and a 30-point train-validation gap: which regularizer do you try first, and how do you know it worked in production?
**Repo link:** [`hld/streetview-ingestion/deep-dives/privacy-blur-and-takedowns.md`, §1 Recall first, because the detector will miss](../../../hld/streetview-ingestion/deep-dives/privacy-blur-and-takedowns.md#1-recall-first-because-the-detector-will-miss)
**Captured by the script:** P1, P2, P3 and every Record row except the stretch. **Human steps:** none (the dropout stretch is optional and not captured)
**Status:** todo

## 0. Retrieval (0:00, 5 min, closed book, no AI)

The AI asks up to three due cards from `../../quiz-bank.md`, one at a time. Do not open the bank first.

## 1. Predict (0:05, 7 min, no AI)

Level S: first read `load_data()` and `report()` in `scripts/37_overfit_then_regularise.py` (2 minutes). They fix the training subsets, the validation set and the RESULT names your harness must print. There is no model or loop to read yet: predict from the configs below.

Every step uses one model and one recipe: a small ResNet (about 0.3 M parameters: a 32-channel stem, residual blocks of 32, 64 and 128 channels, global average pooling, one linear layer), Adam at learning rate 1e-3, batch 128, float32 on MPS, and the same starting weights at one seed. Training accuracy is scored on the training images as stored (no augmentation) and validation accuracy on all 10,000 test images, both in eval mode after the last epoch. The gap is training minus validation accuracy, in percentage points.

Write each row here before anything runs; the AI copies it into `../../prediction-log.md` word for word. A row that asks for several numbers becomes one log row per number, each with its own range.

| Step | Question | Kind | Prediction | 80% range or confidence |
|---|---|---|---|---|
| P1 | Training minus validation accuracy, in points: 5,000 training images (500 per class, seed 0), no augmentation, after 30 epochs. | num | | |
| P2 | Add random crop (4-pixel reflect padding) and horizontal flip (p = 0.5) to the training batches of the same run (5,000 images, seed 0, 30 epochs): the gap, direction (up, down or same) and size as the gap difference, augmented minus plain, in points. | dir | | |
| P3 | 500 training images (50 per class, seed 0, inside the 5,000), no augmentation, trained until training accuracy first reaches 100% (checked after every epoch, cap 100 epochs): validation accuracy on the 10,000 test images, in percent. | num | | |

## 2. Setup (before the session)

```
$ source ~/.venvs/ml/bin/activate
$ cd m6-deep-nets-on-a-mac    # from ml-learning/, where sessions start
$ python scripts/37_overfit_then_regularise.py --download
$ python scripts/37_overfit_then_regularise.py --smoke
```

## 3. Baseline (0:12, 10 min)

Why: one model, one training budget, 5,000 images and no regulariser. The gap says how much of the training accuracy carries over to images the network never saw.

You write these first, with no AI (about 6 minutes). Each blank takes one line.

1. The run plan, in your own words:
   - Sizes: which training images each step uses, and why the 500 sit inside the 5,000:
   - Epochs: what each step trains for, and why the break stops on a training-accuracy rule instead of a fixed count:
   - Fixed: what stays the same across the three steps, and the one thing each step changes:
2. `load_data()` and `report()` already exist: say what they fix, what `--seed` changes, and what each mode passes to `report()`.
   - Split:
   - Metric:
   - RESULT contract:
3. Two functions in `scripts/37_overfit_then_regularise.py`, from this description:
   - `dropout(x, p, training)`: if `training` is false, return `x` unchanged. Otherwise keep each element with probability 1 - p (a mask `torch.rand_like(x) >= p`) and return `x * mask / (1 - p)`. Same shape, dtype and device as `x`.
   - `augment(batch, pad=4, flip_p=0.5)`: `batch` is N x C x 32 x 32. Reflect-pad the last two dims by `pad` on every side, `F.pad(batch, (pad, pad, pad, pad), mode="reflect")`, which gives N x C x 40 x 40. For each image, draw its own top-left offset `dy, dx` in 0 to `2 * pad` and keep the window `[dy:dy + 32, dx:dx + 32]`. Then flip that image left to right (the last dim) with probability `flip_p`. Return N x C x 32 x 32, the input's shape.

Then prompt the AI with your plan and the three lines of item 2. It writes the harness for all three modes in one pass, and it has to cover:

- The model: a stem of a 3x3 convolution to 32 channels, batch norm and ReLU; three residual blocks (two 3x3 convolutions with batch norm each, plus a shortcut that is a 1x1 convolution when the shape changes) at 32, 64 (stride 2) and 128 (stride 2) channels; global average pooling; your `dropout()` with p from a `DROPOUT` constant set to 0.0, the identity; one linear layer to 10 classes.
- The loop: Adam at 1e-3, batch 128, cross-entropy, a fresh shuffle every epoch from its own generator seeded by `--seed`, so the batch order is the same with and without augmentation. `labkit.seed_all(seed)` right before the model is built, so every mode starts from the same weights.
- Scoring: accuracy in eval mode, 1,000 images at a time, on the training images as stored and on the 10,000 validation images.
- Baseline: 5,000 images, 30 epochs, no augmentation.
- Change: the same run with `augment()` on every training batch, and the gap delta against the baseline run at the same seed (`labkit.prior("P1.gap")`).
- Break: 500 images, no augmentation, training accuracy checked after every epoch, stop at the first 100% (cap 100 epochs), and the epoch count.

Annotate each AI block in one line before the first run.

```
$ python scripts/37_overfit_then_regularise.py --baseline
(paste your RESULT lines)
```

Prediction vs actual, one sentence. The reference run is in `../../answers/`; the AI opens it only after your P1 row exists and you have pasted your own RESULT lines.

## 4. Change one thing (0:22, 10 min)

Why: augmentation shows the network a new version of each training image every epoch, at the same data size and the same budget.

Change: random crop with 4-pixel reflect padding, plus horizontal flip at p = 0.5, on the training batches only (your `augment()`). The training-accuracy pass and the validation images are scored as stored. The script prints the change against your baseline run at the same seed, so run `--baseline` first. P2 is logged above.

```
$ python scripts/37_overfit_then_regularise.py --change
(paste your RESULT lines)
```

## 5. Break it (0:32, 10 min, AI gives hints only; the run finishes by 0:40)

Why: training accuracy is the number a training run shows by default. This run trains on a tenth of the data under a fixed stop rule and asks what training accuracy is worth on images the network never saw.

Break: train on 500 images (50 per class, inside the 5,000) with no augmentation until training accuracy first reaches 100%, checked after every epoch, cap 100 epochs. P3 is logged above.

```
$ python scripts/37_overfit_then_regularise.py --break
(paste your RESULT lines)
```

Why, in three sentences, written without AI:

## 6. Explain-back (0:42, 5 min) and rebuild (0:47, 10 min), no AI

- Five sentences for a smart engineer new to ML, written without AI. The AI names your weakest claim after the session (section 7).
- Rebuild: at 0:47, not before, open `rebuild/37_dropout_and_augment.py`, write both bodies from memory, then run `python rebuild/37_dropout_and_augment.py`. Its `check()` compares with torch (`F.dropout`, `F.pad` with `mode="reflect"`, `Tensor.flip`) on random tensors, never with this lab's results.

## 7. What I learned

After the session (about 5 minutes): the AI names the weakest claim in your five sentences and asks one question that tests it. Edit the sentences here.

## 8. Interview soundbite (one of the three cards written at 0:57)

> (Your soundbite: one or two sentences only someone who ran this would say.)

Staff follow-up (failure modes): the regularised model ships as the face detector behind the blur. What tells you it still misses faces in production, and what handles the faces it misses? Answer in 2 sentences from the repo link (§1). Rotate: simplest design, failure modes, migration, what pages at 3 am, cost, trade-off.

## 9. Quiz cards (0:57, 3 min)

The AI drafts three cards (M, N, and T or D). Edit or replace them. Questions go to `../../quiz-bank.md`, keys to `../../answers/quiz-key.md`.

## Record

The script prints these as RESULT lines. Paste, do not type. Stretch, after the session and not captured: set `DROPOUT = 0.3` in your script, run `--change` again, and write its two accuracies in the last row by hand.

| Metric | Your run | Hardware (the script's HW line) | Captured by (script or learner) |
|---|---|---|---|
| `P1.gap`: training minus validation accuracy, 5,000 images, no augmentation, 30 epochs | | | script |
| `baseline.train_acc`: training accuracy on the 5,000 images as stored, eval mode | | | script |
| `baseline.val_acc`: validation accuracy on the 10,000 test images | | | script |
| `P2.gap`: the same gap with random crop and flip on the training batches | | | script |
| `P2.gap_delta`: augmented gap minus plain gap (needs `--baseline` run first with the same seed) | | | script |
| `change.train_acc`: training accuracy, augmentation in training, scored on the 5,000 images as stored | | | script |
| `change.val_acc`: validation accuracy, augmentation in training | | | script |
| `P3.val_acc`: validation accuracy, 500 images trained to 100% training accuracy | | | script |
| `break.train_acc`: training accuracy on the 500 images when training stopped (below 100 means the cap came first) | | | script |
| `break.gap`: training minus validation accuracy at 500 images | | | script |
| `break.epochs_to_100`: epochs until training accuracy first reached 100% (100, the cap, if it never did) | | | script |
| Stretch: training and validation accuracy with `DROPOUT = 0.3` on top of augmentation (`--change`) | | | learner |
