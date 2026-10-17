# 34. Convolutions by hand, then a CNN

> Goal: after this I can compute a 3x3 convolution by hand that matches `F.conv2d`, and show what a 4-pixel shift does to a multi-layer perceptron (MLP) and to a convolutional neural network (CNN) of the same size (about 20,500 parameters each). (No result values anywhere in this file.)

**Level:** W (see `ml-learning/CLAUDE.md`). **Output style:** Explanatory
**Concept link:** [`../README.md#convolutions`](../README.md#convolutions) (read after the lab)
**Borrowed from:** fast.ai Lesson 8, convolutions ([course.fast.ai](https://course.fast.ai/Lessons/lesson8.html)); fastbook ch 13, "Convolutional Neural Networks", the sections "The Magic of Convolutions" and "Our First Convolutional Neural Network" ([13_convolutions.ipynb](https://github.com/fastai/fastbook/blob/master/13_convolutions.ipynb)); Kaggle Learn, Computer Vision ([kaggle.com/learn/computer-vision](https://www.kaggle.com/learn/computer-vision)). Do it after the lab, as the second contact 1 to 3 days later.
**Dataset:** MNIST, 60,000 train and 10,000 test digits at 28x28, about 11.6 MB of gz files, torchvision download (first mirror https://ossci-datasets.s3.amazonaws.com/mnist/; fallback, the Hugging Face parquet copy at https://huggingface.co/datasets/ylecun/mnist, 15.6 MB plus 2.6 MB), the Hugging Face card lists MIT. Shared with lab 29 in `~/ml-data/mnist`.
**Runs on:** cpu. **Lane:** light. **Compute:** 3 runs x 1 min, at most 6 min per run. Precomputed steps: none
**Needs:** base install only
**Before the session** (from the module folder, see section 2): `--download` (about 11.6 MB into `~/ml-data/mnist`; if lab 29 already fetched it, it only lists the files), then `--smoke`.
**Interview question:** Why use a CNN for images instead of an MLP with the same parameter count?
**Repo link:** [`hld/streetview-ingestion/deep-dives/privacy-blur-and-takedowns.md`](../../../hld/streetview-ingestion/deep-dives/privacy-blur-and-takedowns.md#1-recall-first-because-the-detector-will-miss), §1 "Recall first, because the detector will miss", [§2 "Blur is destructive, and a pure function that only adds"](../../../hld/streetview-ingestion/deep-dives/privacy-blur-and-takedowns.md#2-blur-is-destructive-and-a-pure-function-that-only-adds) (the "Only adds" bullet), plus [§11 "What the interviewer asks next"](../../../hld/streetview-ingestion/deep-dives/privacy-blur-and-takedowns.md#11-what-the-interviewer-asks-next) (the bullet on measuring recall in production)
**Captured by the script:** every Record row except your paper value, from `--baseline`, `--change` and `--break`. **Human steps:** one top-edge output worked out on paper from the `WINDOW` line that `--change` prints (section 4)
**Status:** todo

## 0. Retrieval (0:00, 5 min, closed book, no AI)

The AI asks up to three due cards from `../../quiz-bank.md`, one at a time. Do not open the bank first.

## 1. Predict (0:05, 7 min, no AI)

Level W only: before the session, read `scripts/34_convolutions.py` (about 10 minutes) and answer its three `# Q:` prompts here. At 0:05 you only predict. Start at `conv_one()`: `download()` and `load_data()` are plumbing.

- Q1, the first conv in `cnn()`: what is its output shape for a batch of 64 digits?
- Q2, the first max-pool in `cnn()`: what does max-pooling drop from each 2x2 window?
- Q3, the second conv in `cnn()`. That layer has 16 input and 32 output channels, but the prompt asks a smaller case: how many parameters are in a 3x3 conv with 8 input and 16 output channels? After `--change`, check the same rule, summed over every layer, against `change.cnn_params`.

Write each row here before anything runs; the AI copies it into `../../prediction-log.md` word for word. A row that asks for several numbers becomes one log row per number, each with its own range.

Every step uses the same setup. Data: MNIST, the 60,000 training digits and the 10,000 test digits, pixels scaled to [0, 1]. Training: cross-entropy loss, Adam with learning rate 1e-3, batch 64, 1 epoch, PyTorch's default initial weights, seed 0, on the CPU. Both models see the same batches in the same order. Accuracy is the fraction of the 10,000 test digits whose top score is the right digit. A point is one percentage point (0.01).

- MLP: 784 pixels to 26 ReLU (rectified linear unit) units to 10 scores, about 20,500 parameters.
- CNN: a 3x3 conv with 16 kernels, ReLU, 2x2 max-pool; a 3x3 conv with 32 kernels, ReLU, 2x2 max-pool; one linear layer to 10 scores. Both convs pad the border by 1 pixel. About 20,500 parameters.

| Step | Question | Kind | Prediction | 80% range or confidence |
|---|---|---|---|---|
| P1 | Test accuracy (fraction) of the MLP, 784 to 26 to 10, about 20,500 parameters, after 1 epoch (Adam lr 1e-3, batch 64, seed 0) | num | | |
| P2 | The CNN above instead of the MLP, about the same parameter count, the same training (1 epoch, Adam lr 1e-3, batch 64, seed 0): its test accuracy against the MLP's, direction and size in points | dir | | |
| P3 | Shift every test digit 4 pixels right (4 blank columns enter on the left) and re-score both seed-0 models from P1 and P2. Neither model trains on shifted digits. Which model loses more test accuracy? Pick one with a confidence: the pick is graded, with its Brier score. Also write how many points each one loses: two point estimates, not graded, for the Lesson column | pick | | |

## 2. Setup (before the session)

```
$ source ~/.venvs/ml/bin/activate
$ cd m6-deep-nets-on-a-mac    # from ml-learning/, where sessions start
$ python scripts/34_convolutions.py --download
$ python scripts/34_convolutions.py --smoke
```

## 3. Baseline (0:12, 10 min)

Why: the MLP is the yardstick; the CNN in section 4 gets the same data, the same batches and about the same number of parameters.

```
$ python scripts/34_convolutions.py --baseline
(paste your RESULT lines)
```

Prediction vs actual, one sentence. The reference run is in `../../answers/`; the AI opens it only after your P1 row exists and you have pasted your own RESULT lines.

## 4. Change one thing (0:22, 10 min)

Change: the CNN (`cnn()` in the script) instead of the MLP, at about the same parameter count. P2 is logged above.

Why: the same parameter budget, laid out differently. The CNN's conv layers reuse a few small kernels at every position, while the MLP's first layer has one weight per pixel per hidden unit. The run first slides one kernel by hand.

Before the CNN trains, the run slides fastbook's top-edge kernel `[[-1, -1, -1], [0, 0, 0], [1, 1, 1]]` over the first test digit with two loops (`conv_one`) and with `F.conv2d`. It prints one `WINDOW` line: the 3x3 pixels, out of 255, under the strongest top edge. While the CNN trains, work that output out on paper: multiply the window by the kernel cell by cell, add the nine products, and divide by 255. Write it in the Record. After training, the run prints `change.top_edge_by_hand` and `change.top_edge_conv2d` at that row and col, so you can compare. Then it checks `conv_batch` (`F.unfold` plus one matrix multiply) against `F.conv2d` on 64 test digits, with 4 edge kernels, stride 1 and 2, and padding 0 and 1. The CNN's lines come last.

```
$ python scripts/34_convolutions.py --change
(paste your RESULT lines)
```

`P2.cnn_minus_mlp_points` prints only after a `--baseline` run with the same seed.

## 5. Break it (0:32, 10 min, AI gives hints only; the run finishes by 0:40)

Break: shift every test digit 4 pixels right (4 blank columns enter on the left, the 4 rightmost columns fall off) and re-score both models, without training on shifted digits. P3 is logged above.

Why: real inputs are rarely centred the way MNIST's digits are, so this measures what each model does when the same digits move.

How: `--break` first trains the two models again exactly as `--baseline` and `--change` did (same seed, same batches), so its accuracies on the original digits repeat your earlier lines. Then it scores each model on the shifted digits.

```
$ python scripts/34_convolutions.py --break
(paste your RESULT lines)
```

Why, in three sentences, written without AI:

## 6. Explain-back (0:42, 5 min) and rebuild (0:47, 10 min), no AI

- Five sentences for a smart engineer new to ML, written without AI. The AI names your weakest claim after the session (section 7).
- Rebuild: open `rebuild/34_conv2d.py`, write `conv_one()` (two loops over 3x3 windows) and `conv_batch()` (`F.unfold`, then one matrix multiply, then the output height and width) from memory, about 15 lines in all, then run `python rebuild/34_conv2d.py`. Its `check()` compares with torch's `F.conv2d` at stride 1 and 2 and padding 0 and 1, never with this lab's results.

## 7. What I learned

After the session (about 5 minutes): the AI names the weakest claim in your five sentences and asks one question that tests it. Edit the sentences here.

## 8. Interview soundbite (one of the three cards written at 0:57)

> One or two sentences only someone who ran this would say.

Staff follow-up: migration. The blur stage in the repo link runs an image detector for faces and plates on every panorama. A retrained detector looks better on the offline test set: how do you ship it without losing recall on real panoramas? Answered in 2 sentences from the repo link (§11, the recall bullet, and §2, "Only adds"). Rotate: simplest design, failure modes, migration, what pages at 3 am, cost, trade-off.

## 9. Quiz cards (0:57, 3 min)

The AI drafts three cards (M, N, and T or D). Edit or replace them. Questions go to `../../quiz-bank.md`, keys to `../../answers/quiz-key.md`.

## Record

The script prints these as RESULT lines. Paste, do not type.

| Metric | Your run | Hardware (the script's HW line) | Captured by (script or learner) |
|---|---|---|---|
| `baseline.mlp_params`, parameters in the MLP | | | script |
| `P1.mlp_test_acc` (fraction) | | | script |
| Your paper value for the `WINDOW` line | | | learner |
| `change.top_edge_by_hand`, the strongest top-edge output from the two loops, with its row and col | | | script |
| `change.top_edge_conv2d`, `F.conv2d` at the same row and col | | | script |
| `change.hand_max_abs_diff`, the largest gap between the loops and `F.conv2d` over the whole output | | | script |
| `change.unfold_max_abs_diff`, the largest gap between `F.unfold` plus one matrix multiply and `F.conv2d` (4 edge kernels, 64 digits, stride 1 and 2, padding 0 and 1) | | | script |
| `change.cnn_params`, parameters in the CNN | | | script |
| `P2.cnn_test_acc` (fraction) | | | script |
| `P2.cnn_minus_mlp_points`, CNN minus MLP at the same seed (points) | | | script |
| `break.mlp_test_acc`, the MLP on the original digits (fraction) | | | script |
| `break.mlp_shifted_acc`, the MLP on the shifted digits (fraction) | | | script |
| `P3.mlp_drop_points`, original minus shifted (points) | | | script |
| `break.cnn_test_acc`, the CNN on the original digits (fraction) | | | script |
| `break.cnn_shifted_acc`, the CNN on the shifted digits (fraction) | | | script |
| `P3.cnn_drop_points`, original minus shifted (points) | | | script |
| `P3.loses_more`, the model with the bigger drop (mlp or cnn) | | | script |
| `P3.gap_points`, the bigger drop minus the smaller one (points) | | | script |
