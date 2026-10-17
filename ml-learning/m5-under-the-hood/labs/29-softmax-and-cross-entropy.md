# 29. Softmax and cross-entropy: from 2 digits to 10

> Goal: after this I can predict a 10-class classifier's loss before any training, write cross-entropy from logits (the 10 raw scores before softmax) with logsumexp (the log of the sum of the exponentials) in under 15 lines, and explain what a double softmax does to training. (No result values anywhere in this file.)

**Level:** C (see `ml-learning/CLAUDE.md`). **Output style:** Learning
**Concept link:** [`../README.md#softmax-and-cross-entropy`](../README.md#softmax-and-cross-entropy) (read after the lab)
**Borrowed from:** fastbook ch 5, section "Cross-Entropy Loss" ([05_pet_breeds.ipynb](https://github.com/fastai/fastbook/blob/master/05_pet_breeds.ipynb)); fast.ai Lesson 7 ([course.fast.ai](https://course.fast.ai/Lessons/lesson7.html)); Karpathy, makemore part 3, the loss at initialization ([video](https://www.youtube.com/watch?v=P6sfmUTpUmc)). Do it after the lab, as the second contact 1 to 3 days later.
**Dataset:** MNIST, 60,000 train and 10,000 test digits at 28x28, about 11.6 MB of gz files, torchvision download (first mirror https://ossci-datasets.s3.amazonaws.com/mnist/; fallback, the Hugging Face parquet copy at https://huggingface.co/datasets/ylecun/mnist, 15.6 MB plus 2.6 MB), the Hugging Face card lists MIT. Shared with lab 34 in `~/ml-data/mnist`.
**Runs on:** cpu. **Lane:** light. **Compute:** 3 runs x 1 min, at most 6 min per run. Precomputed steps: none
**Needs:** base install only
**Before the session** (from the module folder, see section 2): `--download` (about 11.6 MB into `~/ml-data/mnist`), then `--smoke`, which passes with the TODO still open.
**Interview question:** What should a classifier's loss be before any training, and what happens if you train a classifier with MSE (mean squared error) instead of cross-entropy?
**Repo link:** [`hld/payments-risk-decisioning/deep-dives/model-lifecycle-shadow-and-labels.md`](../../../hld/payments-risk-decisioning/deep-dives/model-lifecycle-shadow-and-labels.md#4-thresholds-from-cost-and-why-the-inputs-must-scale), §4 "Thresholds from cost, and why the inputs must scale" (the "Calibrate first" bullet)
**Captured by the script:** every Record row, from `--baseline`, `--change` and `--break`. **Human steps:** none (you write the `cross_entropy()` body, and `--check` grades it)
**Status:** todo

## 0. Retrieval (0:00, 5 min, closed book, no AI)

The AI asks up to three due cards from `../../quiz-bank.md`, one at a time. Do not open the bank first.

## 1. Predict (0:05, 7 min, no AI)

Level C: predict first. You write the `TODO(human)` in section 3, before the baseline runs.

Write each row here before anything runs; the AI copies it into `../../prediction-log.md` word for word. A row that asks for several numbers becomes one log row per number, each with its own range.

Every step uses the same setup: a linear 784-to-10 model (one weight per pixel per digit, plus a bias), weights drawn from a normal with std (standard deviation) 0.01, zero bias, pixels scaled to [0, 1], batch 64, plain SGD (stochastic gradient descent) with learning rate (lr) 0.1, 1 epoch over the 60,000 training images, seed 0. Losses are in nats (natural log).

| Step | Question | Kind | Prediction | 80% range or confidence |
|---|---|---|---|---|
| P1 | Cross-entropy loss (nats) on the first batch of 64 training images, before any weight update (linear 784-to-10, init std 0.01, zero bias, seed 0) | num | | |
| P2 | MSE between the softmax probabilities and one-hot targets (`F.mse_loss`, default mean) instead of cross-entropy (linear 784-to-10, init std 0.01, batch 64, SGD lr 0.1, 1 epoch, seed 0). Test accuracy on the 10,000 test images: direction and size against cross-entropy. Graded on `P2.accuracy_delta`, MSE accuracy minus cross-entropy accuracy as a fraction (0.01 is 1 percentage point): its sign is the direction, its size the size | dir | | |
| P3 | Softmax on the outputs, then `nn.CrossEntropyLoss`, a double softmax (linear 784-to-10, init std 0.01, batch 64, SGD lr 0.1, 1 epoch, seed 0). Test accuracy on the 10,000 test images (`P3.test_accuracy`) | num | | |
| P3 | The same double softmax: the floor under its loss (nats), over any batch and any weights. The floor is the greatest lower bound, the value the loss can get as close to as you like (`P3.lowest_possible_loss`) | num | | |

P3 is two predictions. Log two P3 rows in `../../prediction-log.md`, one for `P3.test_accuracy` and one for `P3.lowest_possible_loss`. Each gets its own point estimate and 80% range and is graded on its own.

The floor is an exact-arithmetic bound: the loss can come arbitrarily close to it, but finite weights never land on it exactly. `P3.lowest_possible_loss` comes from a short float32 search over free logits, so it is a finite-precision estimate of that bound, not a proof.

## 2. Setup (before the session)

```
$ source ~/.venvs/ml/bin/activate
$ cd m5-under-the-hood    # from ml-learning/, where sessions start
$ python scripts/29_softmax_and_cross_entropy.py --download
$ python scripts/29_softmax_and_cross_entropy.py --smoke
```

## 3. Baseline (0:12, 10 min)

Why: lab 28 told 3s from 7s; now each of the 10 digits gets a score, softmax turns the 10 scores into probabilities, and the loss before any training is a number you can work out on paper.

First the TODO: write the body of `cross_entropy()` in `scripts/29_softmax_and_cross_entropy.py` (marked `TODO(human)`; its docstring is the spec). The AI may give hints, or a draft explained line by line that you type. Then run `python scripts/29_softmax_and_cross_entropy.py --check` until it prints `check: PASS`. It compares your function with `F.cross_entropy` on a 20-row fixture, value and gradient, including logits of 1,000. The baseline trains with your function.

```
$ python scripts/29_softmax_and_cross_entropy.py --baseline
(paste your RESULT lines)
```

Prediction vs actual, one sentence. The reference run is in `../../answers/`; the AI opens it only after your P1 row exists and you have pasted your own RESULT lines.

## 4. Change one thing (0:22, 10 min)

Change: MSE between the softmax probabilities and one-hot targets instead of cross-entropy (`mse_one_hot()` in the script). P2 is logged above.

Why: MSE is the loss you know from regression; the model, the init and the batch order stay the same, so only the loss differs.

```
$ python scripts/29_softmax_and_cross_entropy.py --change
(paste your RESULT lines)
```

`P2.accuracy_delta` (MSE minus cross-entropy) prints only after a `--baseline` run with the same seed.

## 5. Break it (0:32, 10 min, AI gives hints only; the run finishes by 0:40)

Break: apply softmax to the outputs before `nn.CrossEntropyLoss` (`double_softmax()` in the script). P3 is logged above.

Why: a softmax at the end of the model and `nn.CrossEntropyLoss` in the training loop each look like the textbook recipe, so the pair is an easy slip.

```
$ python scripts/29_softmax_and_cross_entropy.py --break
(paste your RESULT lines)
```

Why, in three sentences, written without AI:

## 6. Explain-back (0:42, 5 min) and rebuild (0:47, 10 min), no AI

- Five sentences for a smart engineer new to ML, written without AI. The AI names your weakest claim after the session (section 7).
- Rebuild: open `rebuild/29_softmax_cross_entropy.py`, write the bodies of `softmax()` and `cross_entropy()` from memory, without looking at your TODO (a few lines each, logsumexp with the row maximum subtracted), then run `python rebuild/29_softmax_cross_entropy.py`. Its `check()` compares with torch (`torch.softmax` and `F.cross_entropy`, within 1e-6, including logits of 1,000 that overflow a naive exp), never with this lab's results.

## 7. What I learned

After the session (about 5 minutes): the AI names the weakest claim in your five sentences and asks one question that tests it. Edit the sentences here.

## 8. Interview soundbite (one of the three cards written at 0:57)

> One or two sentences only someone who ran this would say.

Staff follow-up: trade-off. The fraud model's score feeds a cost threshold: decline when `p > C_fd / (C_fd + L)`, where C_fd is the cost of a false decline (a good payment declined) and L is the loss on an approved fraud. Do you trust a model trained with cross-entropy to hand you `p` as a probability, or add a recalibration step, and what does each option cost? Answered in 2 sentences from the repo link. Rotate: simplest design, failure modes, migration, what pages at 3 am, cost, trade-off.

## 9. Quiz cards (0:57, 3 min)

The AI drafts three cards (M, N, and T or D). Edit or replace them. Questions go to `../../quiz-bank.md`, keys to `../../answers/quiz-key.md`.

## Record

The script prints these as RESULT lines. Paste, do not type.

| Metric | Your run | Hardware (the script's HW line) | Captured by (script or learner) |
|---|---|---|---|
| `P1.first_batch_loss` (nats) | | | script |
| `baseline.test_accuracy` (fraction) | | | script |
| `baseline.min_batch_loss`, the lowest batch loss of the epoch (nats) | | | script |
| `P2.test_accuracy` (fraction) | | | script |
| `P2.accuracy_delta`, MSE minus cross-entropy at the same seed (fraction) | | | script |
| `change.min_batch_loss` (MSE units) | | | script |
| `P3.test_accuracy` (fraction) | | | script |
| `P3.lowest_possible_loss`, the float32 search's estimate of the floor under the double-softmax loss (nats) | | | script |
| `break.min_batch_loss` (nats) | | | script |
