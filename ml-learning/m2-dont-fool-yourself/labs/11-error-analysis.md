# 11. Error analysis by hand: errors decide the next experiment

> Goal: after this I can tally the 50 highest-loss validation images into categories in 15 minutes, and measure how well the highest training losses find flipped labels. (No result values anywhere in this file.)

**Level:** C (see `ml-learning/CLAUDE.md`). **Output style:** Learning
**Concept link:** `../README.md#error-analysis` (read after the lab)
**Borrowed from:** Andrew Ng, [Machine Learning Yearning](https://info.deeplearning.ai/machine-learning-yearning-book), the error analysis chapters; fast.ai [Lesson 2](https://course.fast.ai/Lessons/lesson2.html), `plot_top_losses`. Do it after the lab, as the second contact 1 to 3 days later.
**Dataset:** Oxford-IIIT Pet, 7,390 images of 37 breeds (shared with lab 01), 811.7 MB, https://s3.amazonaws.com/fast-ai-imageclas/oxford-iiit-pet.tgz, CC BY-SA 4.0. Plus the ResNet-34 ImageNet weights, 87 MB from download.pytorch.org.
**Runs on:** mps. **Lane:** heavy. **Compute:** 4 runs x at most 5 min (`--check` under 1, baseline 3, change 1, break 5, rounded up from the reference runs), at most 6 min per run. Precomputed steps: none
**Needs:** base install only
**Before the session** (from the module folder, see section 2): `python scripts/11_error_analysis.py --download` (it finds the images and weights if lab 01 already fetched them), then `python scripts/11_error_analysis.py --smoke` (under a minute). Both work before the TODO is written. Plan 15 minutes of the session for the hand tally.
**Interview question:** Precision fell 5 points after a retrain: how do you tell whether it is the model, the labels or one segment?
**Repo link:** `hld/payments-risk-decisioning/edge-cases.md`, ["Edge case: friendly fraud poisons the labels"](../../../hld/payments-risk-decisioning/edge-cases.md#edge-case-friendly-fraud-poisons-the-labels) and ["Edge case: a new model doubles the decline rate in one segment"](../../../hld/payments-risk-decisioning/edge-cases.md#edge-case-a-new-model-doubles-the-decline-rate-in-one-segment)
**Captured by the script:** the baseline error rate, the 50 highest-loss validation images (a plot and a CSV in `~/ml-data/results/lab11/`), the `most_confused(min_val=3)` pairs with the top pair, and the flipped labels among the 50 highest training losses. **Human steps:** the tally of the 50 images into categories, the label-error count (the actual for P1), and the first fix with its reason.
**Status:** todo

## 0. Retrieval (0:00, 5 min, closed book, no AI)

The AI asks up to three due cards from `../../quiz-bank.md`, one at a time. Do not open the bank first.

## 1. Predict (0:05, 7 min, no AI)

Level C: you write the TODO(human) function `top_losses()` in `scripts/11_error_analysis.py` at 0:12. Predict first.

Write each row here before anything runs; the AI copies it into `../../prediction-log.md` word for word. A row that asks for several numbers becomes one log row per number, each with its own range.

Every step uses lab 01's recipe at seed 0: an ImageNet-pretrained ResNet-34, `fine_tune(1)` at base learning rate 2e-3, each image resized to 448 px, then augmented and cropped to 224 px, batch 64. The split is lab 01's, `RandomSplitter(valid_pct=0.2, seed=42)`: 5,912 training and 1,478 validation images of 37 breeds. A loss is the per-image cross-entropy against the image's label.

| Step | Question | Kind | Prediction | 80% range or confidence |
|---|---|---|---|---|
| P1 | Of the 50 highest-loss validation images of the seed 0 model, how many carry a wrong or ambiguous label rather than a model mistake? Your own tally gives the actual | num | | |
| P2 | Will the top pair of `interp.most_confused(min_val=3)` on the same model fall inside your largest error category from the tally? Yes or no | pick | | |
| P3 | Flip exactly 10% of the training labels (591 of 5,912, each to a random other breed, flip seed 0) and retrain with the same recipe. Of the 50 highest training losses, computed without augmentation against the labels the model trained on, how many are flipped labels? | num | | |

## 2. Setup (before the session)

```
$ source ~/.venvs/ml/bin/activate
$ cd m2-dont-fool-yourself    # from ml-learning/, where sessions start
$ python scripts/11_error_analysis.py --download
$ python scripts/11_error_analysis.py --smoke
```

## 3. Baseline (0:12, 10 min)

Why: the highest losses are the images where the model and the label disagree most. Reading them shows which kind of error to fix first.

Write the TODO first, from its docstring: `top_losses()`, a few lines. Run `--check` until it prints `check: PASS`, then the baseline. The AI gives hints, or a draft it explains line by line that you type. The baseline trains for about 3 minutes, then writes two files to `~/ml-data/results/lab11/`: `top_losses_seed0.png` (fastai's `plot_top_losses(50)`, titled predicted/actual/loss/probability) and `top_losses_seed0.csv` (rank, file, actual, predicted, loss and an empty category column).

```
$ python scripts/11_error_analysis.py --check
$ python scripts/11_error_analysis.py --baseline
(paste your RESULT lines)
```

Tally (human step, no AI, about 15 minutes at 18 s per image, done by 0:31): open the plot and the CSV side by side. Make the categories by looking, then write one per row in the category column; a second category per image is allowed. Mark each category as a label problem (a wrong or ambiguous label) or a model mistake.

| Category | Label problem or model mistake | Count | Share of 50 |
|---|---|---|---|
| | | | |

Prediction vs actual, one sentence. The actual for P1 is your count of label problems, not a RESULT line. The reference run is in `../../answers/`; the AI opens it only after your P1 row exists and your count is written.

## 4. Change one thing (0:22, 10 min)

Change: find the largest error category with `interp.most_confused(min_val=3)` on the same seed 0 model, instead of reading images. P2 is logged above.

Why: a confusion count costs no reading time. See whether it finds the category your reading found. `--change` reloads the baseline model from `~/ml-data/results/lab11/model_seed0.pth` and runs in about a minute, so finish the tally first.

```
$ python scripts/11_error_analysis.py --change
(paste your RESULT lines)
```

## 5. Break it (0:32, 10 min, AI gives hints only; the run finishes by 0:40)

Break: flip 10% of the training labels to a random other breed (flip seed 0), retrain with the same recipe, then rank the training images by loss and count the flipped ones among the top 50. There is no second hand tally: the script knows which labels it flipped. The run takes about 5 minutes. P3 is logged above.

```
$ python scripts/11_error_analysis.py --break
(paste your RESULT lines)
```

Why, in three sentences, written without AI:

## 6. Explain-back (0:42, 5 min) and rebuild (0:47, 10 min), no AI

- Five sentences for a smart engineer new to ML, written without AI. The AI names your weakest claim after the session (section 7).
- Rebuild: open `rebuild/11_top_losses.py`, write the bodies of `top_losses()`, `flip_labels()` and `tally()` from memory, then run `python rebuild/11_top_losses.py`. Its `check()` compares with PyTorch (`F.cross_entropy(reduction='none')` and `topk`) and pandas (`value_counts`) on synthetic data, never with this lab's results.

## 7. What I learned

After the session (about 5 minutes): the AI names the weakest claim in your five sentences and asks one question that tests it. Edit the sentences here.

## 8. Interview soundbite (one of the three cards written at 0:57)

> (Your soundbite: one or two sentences only someone who ran this would say.)

Staff follow-up (failure modes): friendly fraud is label noise at scale. Which label fields would you check before trusting a chargeback as fraud, and who must never be able to write a fraud label? Answer in 2 sentences from the repo link. Rotate: simplest design, failure modes, migration, what pages at 3 am, cost, trade-off.

## 9. Quiz cards (0:57, 3 min)

The AI drafts three cards (M, N, and T or D). Edit or replace them. Questions go to `../../quiz-bank.md`, keys to `../../answers/quiz-key.md`.

## Record

The script prints these as RESULT lines. Paste, do not type. The learner rows come from your tally and your judgement.

| Metric | Your run | Hardware (the script's HW line) | Captured by (script or learner) |
|---|---|---|---|
| `baseline.error_rate`: validation error rate of the seed 0 model (fraction) | | | script |
| `baseline.valid_errors`: misclassified validation images (images) | | | script |
| `baseline.top50_misclassified`: misclassified images among the 50 highest losses (images) | | | script |
| Category counts and shares, from the tally table above | | | learner |
| The label-error count: label problems among the 50 (images) | | | learner |
| `P2.top_pair`: the top pair of `most_confused(min_val=3)` (actual/predicted) | | | script |
| `change.top_pair_count`: validation images in the top pair (images) | | | script |
| `change.pairs_min3`: pairs seen at least 3 times (pairs) | | | script |
| `change.images_in_pairs_min3`: validation errors inside those pairs (images) | | | script |
| `P3.flipped_in_top50`: flipped labels among the 50 highest training losses (images) | | | script |
| `break.chance_in_top50`: 50 x the share of training labels flipped (images) | | | script |
| `break.flipped_memorised`: share of flipped training images the model predicts as their flipped label (fraction) | | | script |
| `break.error_rate`: validation error rate after training on the flipped labels (fraction) | | | script |
| The first fix and why: which category you would fix first, and how | | | learner |
