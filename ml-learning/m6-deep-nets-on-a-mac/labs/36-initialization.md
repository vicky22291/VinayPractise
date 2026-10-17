# 36. Initialization and activation statistics

> Goal: after this I can predict and measure, in log10, the activation standard deviation (std) after each of 10 ReLU (rectified linear unit, max(0, z)) layers for four inits, and measure each run's training loss and test accuracy after 2 epochs. (No result values anywhere in this file.)

**Level:** C (see `ml-learning/CLAUDE.md`). **Output style:** Learning
**Concept link:** [`../README.md#initialization-and-activation-statistics`](../README.md#initialization-and-activation-statistics) (read after the lab)
**Borrowed from:** fast.ai Part 2 Lesson 17, initialization and normalization ([course.fast.ai](https://course.fast.ai/Lessons/lesson17.html)); Karpathy, makemore part 3, activations, gradients and BatchNorm ([video](https://www.youtube.com/watch?v=P6sfmUTpUmc)); He et al. 2015, "Delving Deep into Rectifiers", the paper behind Kaiming init ([arXiv 1502.01852](https://arxiv.org/abs/1502.01852)). Do it after the lab, as the second contact 1 to 3 days later.
**Dataset:** Fashion-MNIST (Zalando), 60,000 train and 10,000 test images of clothing at 28x28 in 10 classes, 36.11 MB of parquet from [Hugging Face](https://huggingface.co/datasets/zalando-datasets/fashion_mnist) (fallback: the gz files at https://github.com/zalandoresearch/fashion-mnist, 30.88 MB), MIT licence. The statistics use 512 standardized training images. Saved in `~/ml-data/fashion_mnist`.
**Runs on:** cpu. **Lane:** light. **Compute:** 3 runs x 1 min, at most 6 min per run. Precomputed steps: none
**Needs:** base install only
**Before the session** (from the module folder, see section 2): `--download` (36.11 MB into `~/ml-data/fashion_mnist`), then `--smoke`, which passes with the TODO still open.
**Interview question:** Why do deep nets need careful initialization or normalization, and what does an exploding layer look like in activation statistics?
**Repo link:** [`hld/payments-risk-decisioning/deep-dives/model-lifecycle-shadow-and-labels.md`](../../../hld/payments-risk-decisioning/deep-dives/model-lifecycle-shadow-and-labels.md#5-proving-a-model-before-it-declines-anyone), §5 "Proving a model before it declines anyone" (the shadow gates and the leading indicators)
**Captured by the script:** every Record row, from `--baseline`, `--change` and `--break`. **Human steps:** none (you write the `layer_stds()` body, and `--check` grades it)
**Status:** todo

## 0. Retrieval (0:00, 5 min, closed book, no AI)

The AI asks up to three due cards from `../../quiz-bank.md`, one at a time. Do not open the bank first.

## 1. Predict (0:05, 7 min, no AI)

Level C: predict first. You write the `TODO(human)` in section 3, before the baseline runs.

Write each row here before anything runs; the AI copies it into `../../prediction-log.md` word for word. A row that asks for several numbers becomes one log row per number, each with its own range.

Every step uses the same setup. 512 training images, picked at seed 0, are standardized with the training set's pixel mean and std, so the inputs have std 1. They pass through 10 layers of width 100. Each layer is a matrix multiply with no bias, then ReLU, and layer 1 takes the 784 pixels. "The std after layer 10" is the std of all 512 x 100 values after the 10th ReLU. Training adds a linear head to the 10 classes and runs plain SGD (stochastic gradient descent): learning rate 0.05, batch 64, 2 epochs over the 60,000 training images, seed 0. The head has no bias and is drawn with the same init and scale as the 10 layers. Losses are cross-entropy in nats (natural log).

| Step | Question | Kind | Prediction | 80% range or confidence |
|---|---|---|---|---|
| P1 | log10 of the activation std after layer 10 with N(0, 1) weights (std 1 in every layer), on the 512 standardized images (10 ReLU layers of width 100, seed 0) | num | | |
| P2 | The same with Kaiming init, std sqrt(2 / fan_in) in each layer, where fan_in is the layer's number of inputs (784 for layer 1, then 100): log10 of the std after layer 10 (seed 0) | num | | |
| P3 | Kaiming x 10 and Kaiming x 0.1: every layer's Kaiming weights, the head included, times 10 or times 0.1. Each trains 2 epochs (plain SGD, learning rate 0.05, batch 64, seed 0). Which runs end with a training loss (the mean batch loss of epoch 2) within 0.1 nats of ln 10? ln 10 is the loss of a uniform guess, where every class gets probability 0.1. Pick x 10, x 0.1, both or neither | pick | | |

## 2. Setup (before the session)

```
$ source ~/.venvs/ml/bin/activate
$ cd m6-deep-nets-on-a-mac    # from ml-learning/, where sessions start
$ python scripts/36_initialization.py --download
$ python scripts/36_initialization.py --smoke
```

## 3. Baseline (0:12, 10 min)

Why: `torch.randn` with nothing else is the first init most people write, and the std after each layer is the cheapest health check a deep net has.

First the TODO: write the body of `layer_stds()` in `scripts/36_initialization.py` (marked `TODO(human)`; its docstring is the spec). The AI may give hints, or a draft explained line by line that you type. Then run `python scripts/36_initialization.py --check` until it prints `check: PASS`. It feeds a 20-row fixture to your function and to torch's own layers (`nn.Linear`, `nn.BatchNorm1d`, `nn.ReLU`) with the same random draws. It compares the std after each layer for five configurations: the four inits, plus Kaiming with BatchNorm (batch normalization: each unit standardized over the batch). A failure names the configuration and the layers that differ, never the values. Every measured mode calls your function for the statistics.

```
$ python scripts/36_initialization.py --baseline
(paste your RESULT lines)
```

Prediction vs actual, one sentence. The reference run is in `../../answers/`; the AI opens it only after your P1 row exists and you have pasted your own RESULT lines.

## 4. Change one thing (0:22, 10 min)

Change: Kaiming init, std sqrt(2 / fan_in), instead of N(0, 1) (`run("kaiming", ...)` in the script). P2 is logged above.

Why: Kaiming init (He et al. 2015, in PyTorch as `nn.init.kaiming_normal_`) is the usual alternative to raw `torch.randn` for ReLU layers; only the weight scale changes, while the data, the depth and the random draws stay the same.

```
$ python scripts/36_initialization.py --change
(paste your RESULT lines)
```

Record only: after the P2 lines, `--change` also measures and trains a second configuration, Kaiming with an `nn.BatchNorm1d` layer before every ReLU. No prediction rides on it. Its lines go in the Record table.

## 5. Break it (0:32, 10 min, AI gives hints only; the run finishes by 0:40)

Break: multiply every layer's Kaiming weights, the head included, by 10, then by 0.1, and train each for 2 epochs (`--break` runs both). P3 is logged above.

Why: a wrong constant in an init is an easy slip, for example a variance typed where a std belongs.

```
$ python scripts/36_initialization.py --break
(paste your RESULT lines)
```

Why, in three sentences, written without AI:

## 6. Explain-back (0:42, 5 min) and rebuild (0:47, 10 min), no AI

- Five sentences for a smart engineer new to ML, written without AI. The AI names your weakest claim after the session (section 7).
- Rebuild: open `rebuild/36_layer_stds.py` and write the body of `layer_stds()` from memory, about 10 lines, without looking at your TODO. Then run `python rebuild/36_layer_stds.py`. Its `check()` compares with torch, never with this lab's results: `nn.init.kaiming_normal_` on a 1,000 x 1,000 weight within 0.002, plus `nn.init.normal_`, `nn.Linear` and `nn.BatchNorm1d`.

## 7. What I learned

After the session (about 5 minutes): the AI names the weakest claim in your five sentences and asks one question that tests it. Edit the sentences here.

## 8. Interview soundbite (one of the three cards written at 0:57)

> One or two sentences only someone who ran this would say.

Staff follow-up: what pages at 3 am. A retrained fraud model ships with one input scaled wrong. In production you see scores, not activation statistics. Which leading indicator from the repo link catches it before any label arrives, and at what threshold? Answered in 2 sentences from the repo link. Rotate: simplest design, failure modes, migration, what pages at 3 am, cost, trade-off.

## 9. Quiz cards (0:57, 3 min)

The AI drafts three cards (M, N, and T or D). Edit or replace them. Questions go to `../../quiz-bank.md`, keys to `../../answers/quiz-key.md`.

## Record

The script prints these as RESULT lines. Paste, do not type.

| Metric | Your run | Hardware (the script's HW line) | Captured by (script or learner) |
|---|---|---|---|
| `baseline.log10_std_by_layer`, N(0, 1): log10 of the std after layers 1 to 10 (log10) | | | script |
| `P1.log10_std_layer10`, N(0, 1) (log10) | | | script |
| `baseline.train_loss`, N(0, 1): mean batch loss of epoch 2 (nats) | | | script |
| `baseline.test_acc`, N(0, 1): accuracy on the 10,000 test images (fraction) | | | script |
| `change.log10_std_by_layer`, Kaiming (log10) | | | script |
| `P2.log10_std_layer10`, Kaiming (log10) | | | script |
| `change.train_loss`, Kaiming (nats) | | | script |
| `change.test_acc`, Kaiming (fraction) | | | script |
| `change.bn_log10_std_by_layer`, Kaiming with BatchNorm (log10) | | | script |
| `change.bn_log10_std_layer10`, Kaiming with BatchNorm (log10) | | | script |
| `change.bn_train_loss`, Kaiming with BatchNorm (nats) | | | script |
| `change.bn_test_acc`, Kaiming with BatchNorm (fraction) | | | script |
| `break.x10_log10_std_by_layer`, Kaiming x 10 (log10) | | | script |
| `break.x10_log10_std_layer10`, Kaiming x 10 (log10) | | | script |
| `P3.x10_train_loss`, Kaiming x 10 (nats) | | | script |
| `break.x10_test_acc`, Kaiming x 10 (fraction) | | | script |
| `break.x01_log10_std_by_layer`, Kaiming x 0.1 (log10) | | | script |
| `break.x01_log10_std_layer10`, Kaiming x 0.1 (log10) | | | script |
| `P3.x01_train_loss`, Kaiming x 0.1 (nats) | | | script |
| `break.x01_test_acc`, Kaiming x 0.1 (fraction) | | | script |
| `P3.near_untrained`, the runs that end within 0.1 nats of ln 10: x10, x0.1, both or neither | | | script |
