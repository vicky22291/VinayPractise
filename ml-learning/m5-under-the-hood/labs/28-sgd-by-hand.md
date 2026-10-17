# 28. Pixel baseline, then SGD by hand: loss, gradient and learning rate

> Goal: after this I can write one SGD (stochastic gradient descent) step by hand, beat a mean-image baseline on 3s vs 7s, and show what a 100x learning rate does. (No result values anywhere in this file.)

**Level:** W (see `ml-learning/CLAUDE.md`). **Output style:** Explanatory
**Concept link:** [`../README.md#loss-gradient-and-one-sgd-step`](../README.md#loss-gradient-and-one-sgd-step) (read after the lab)
**Borrowed from:** fast.ai Lesson 3 ([course.fast.ai/Lessons/lesson3.html](https://course.fast.ai/Lessons/lesson3.html)) and fastbook ch 4, "Under the Hood: Training a Digit Classifier" ([04_mnist_basics.ipynb](https://github.com/fastai/fastbook/blob/master/04_mnist_basics.ipynb)). Do it after the lab, as the second contact 1 to 3 days later. Chapter 4 prints the P1 answer (cell 99) and its own training runs, so keep it closed until the lab is done.
**Dataset:** MNIST_SAMPLE (3s and 7s), 12,396 training and 2,038 validation images at 28x28, 3.21 MB, https://s3.amazonaws.com/fast-ai-sample/mnist_sample.tgz (fastai `URLs.MNIST_SAMPLE`), MNIST listed as MIT on Hugging Face
**Runs on:** cpu. **Lane:** light. **Compute:** 3 runs x 1 min, at most 6 min per run. Precomputed steps: none
**Needs:** base install only
**Before the session** (from the module folder, see section 2): `--download` (3.2 MB into `~/ml-data/mnist_sample/`), then `--smoke`.
**Interview question:** Your training loss turns to NaN (not a number) after two epochs: what happened, and what do you change first?
**Repo link:** [`hld/payments-risk-decisioning/deep-dives/model-lifecycle-shadow-and-labels.md`](../../../hld/payments-risk-decisioning/deep-dives/model-lifecycle-shadow-and-labels.md#5-proving-a-model-before-it-declines-anyone), §5 "Proving a model before it declines anyone". No repo file covers optimization; this section answers the Staff follow-up.
**Captured by the script:** P1 to P3 and every Record row, plus one per-step loss plot for each of `--baseline`, `--change` and `--break` in `~/ml-data/results/lab28/` (`--smoke` saves none). **Human steps:** none
**Status:** todo

## 0. Retrieval (0:00, 5 min, closed book, no AI)

The AI asks up to three due cards from `../../quiz-bank.md`, one at a time. Do not open the bank first.

## 1. Predict (0:05, 7 min, no AI)

Level W only: before the session, read `scripts/28_sgd_by_hand.py` (about 10 minutes) and answer its three `# Q:` prompts here. At 0:05 you only predict.

- `mnist_loss`: what does it return for a perfect prediction?
- `sgd_epoch`: why does the update run under `torch.no_grad()`?
- `sgd_epoch`: why are the gradients zeroed after every step?

Write each row here before anything runs; the AI copies it into `../../prediction-log.md` word for word. A row that asks for several numbers becomes one log row per number, each with its own range.

| Step | Question | Kind | Prediction | 80% range or confidence |
|---|---|---|---|---|
| P1 | Validation accuracy (fraction right of all 2,038 validation images) of the rule "closer to the mean 3 or the mean 7" by L1 distance (mean absolute pixel difference). Mean images from all 12,396 training images. No training, no seed. | num | | |
| P2 | Add one hidden layer of 30 ReLU units (rectified linear unit: max(z, 0)), 784 to 30 to 1, with the same N(0, 1) init (normal, mean 0, standard deviation 1), learning rate 1.0, batch 256 and seed 0. Validation accuracy after 20 epochs minus the linear model's (`P2.delta_vs_linear`, a fraction: 0.01 is one point): up, down or same, plus a size range. Same means under 0.005 either way (about 10 of the 2,038 validation images). Up and down count only at 0.005 or more on that side. | dir | | |
| P3 | Linear model with the learning rate x 100 (1.0 to 100), batch 256, 20 epochs, seed 0. What does the training loss do? Pick one: diverges to NaN (any NaN or infinite value), still falls (epoch 20's mean loss under half of epoch 1's), or oscillates or stalls (neither). | pick | | |

## 2. Setup (before the session)

```
$ source ~/.venvs/ml/bin/activate
$ cd m5-under-the-hood    # from ml-learning/, where sessions start
$ python scripts/28_sgd_by_hand.py --download
$ python scripts/28_sgd_by_hand.py --smoke
```

## 3. Baseline (0:12, 10 min)

Why: a rule with no learning sets the bar a trained model must clear. The same run then trains the linear model (784 weights and a bias, learning rate 1.0, 20 epochs), the control for P2 and P3.

```
$ python scripts/28_sgd_by_hand.py --baseline
(paste your RESULT lines)
```

Prediction vs actual, one sentence. The reference run is in `../../answers/`; the AI opens it only after your P1 row exists and you have pasted your own RESULT lines.

## 4. Change one thing (0:22, 10 min)

Why: test whether a non-linearity buys accuracy on 3s vs 7s when nothing else changes.

Change: one hidden layer of 30 ReLU units between the pixels and the output (784 to 30 to 1). Same init, learning rate, batch size and epochs. P2 is logged above.

```
$ python scripts/28_sgd_by_hand.py --change
(paste your RESULT lines)
```

## 5. Break it (0:32, 10 min, AI gives hints only; the run finishes by 0:40)

Why: the learning rate sets how far each step moves along the gradient. Here each step is 100 times as long as the base rate would take from the same gradient.

Break: multiply the learning rate by 100 (1.0 to 100) on the linear model. Everything else as in the baseline. P3 is logged above.

```
$ python scripts/28_sgd_by_hand.py --break
(paste your RESULT lines)
```

The per-step loss plots of all three runs are in `~/ml-data/results/lab28/`.

Why, in three sentences, written without AI:

## 6. Explain-back (0:42, 5 min) and rebuild (0:47, 10 min), no AI

- Five sentences for a smart engineer new to ML, written without AI. The AI names your weakest claim after the session (section 7).
- Rebuild: open `rebuild/28_mean_image_and_sgd.py`, write the three bodies (`mean_image_accuracy`, `mnist_loss`, `sgd_epoch`) from memory, then run `python rebuild/28_mean_image_and_sgd.py`. Its `check()` compares with scipy (`cdist`), scikit-learn (`accuracy_score`) and torch (`F.l1_loss`, `torch.optim.SGD`) on made-up data, never with this lab's results.

## 7. What I learned

After the session (about 5 minutes): the AI names the weakest claim in your five sentences and asks one question that tests it. Edit the sentences here.

## 8. Interview soundbite (one of the three cards written at 0:57)

> One or two sentences only someone who ran this would say.

Staff follow-up (failure modes): a nightly retrain produces a model that is worse than the one it replaces. What stops it from declining real payments? Answer in 2 sentences from the repo link (§5). Rotate: simplest design, failure modes, migration, what pages at 3 am, cost, trade-off.

## 9. Quiz cards (0:57, 3 min)

The AI drafts three cards (M, N, and T or D). Edit or replace them. Questions go to `../../quiz-bank.md`, keys to `../../answers/quiz-key.md`.

## Record

The script prints these as RESULT lines. Paste, do not type.

| Metric | Your run | Hardware (the script's HW line) | Captured by (script or learner) |
|---|---|---|---|
| `P1.mean_image_acc`: mean-image baseline accuracy | | | script |
| `baseline.acc_epoch1`: linear model accuracy after 1 epoch | | | script |
| `baseline.acc_epoch5`: linear model accuracy after 5 epochs | | | script |
| `baseline.acc_epoch20`: linear model accuracy after 20 epochs | | | script |
| `baseline.epoch_losses`: base-rate loss curve, mean training loss per epoch | | | script |
| `baseline.loss_ratio`: base rate, epoch 20 loss / epoch 1 loss | | | script |
| `baseline.loss_outcome`: the P3 rule applied to the base rate | | | script |
| `change.acc_epoch1`: hidden-layer accuracy after 1 epoch | | | script |
| `change.acc_epoch5`: hidden-layer accuracy after 5 epochs | | | script |
| `P2.acc_epoch20`: hidden-layer accuracy after 20 epochs | | | script |
| `P2.delta_vs_linear`: `P2.acc_epoch20` minus `baseline.acc_epoch20`, same seed | | | script |
| `change.epoch_losses`: hidden-layer loss curve, mean training loss per epoch | | | script |
| `change.loss_ratio`: hidden layer, epoch 20 loss / epoch 1 loss | | | script |
| `break.acc_epoch20`: linear model accuracy after 20 epochs at 100x | | | script |
| `break.epoch_losses`: 100x loss curve, mean training loss per epoch | | | script |
| `break.loss_ratio`: 100x, epoch 20 loss / epoch 1 loss | | | script |
| `P3.loss_outcome`: `diverges_to_nan`, `still_falls` or `oscillates_or_stalls` | | | script |
