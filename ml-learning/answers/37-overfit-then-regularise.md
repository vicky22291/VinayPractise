# 37. Overfit on purpose, then regularise: reference answers

> Spoilers. The AI opens one block at a time, only after that step's prediction row exists and the learner pasted their own RESULT lines, or after 'debrief 37'.

**HW:** `HW chip='Apple M4 Pro' cpu=14 gpu=20 mem_gib=24 macos=26.5.1 python=3.13.7 torch=2.14.1 device=mps`
**Seeds:** baseline at seeds 0, 1 and 2. Change and break at seed 0 only (heavy lane). `--seed` changes the training subset, the starting weights and the batch order together.
**Reference script:** [`37_overfit_then_regularise_ref.py`](37_overfit_then_regularise_ref.py), sha256 prefix `43f401f63d4a849e`. Values by seed: [`37-overfit-then-regularise.json`](37-overfit-then-regularise.json). Raw seed-0 output: [`37-overfit-then-regularise.out`](37-overfit-then-regularise.out). Lab file: [`37-overfit-then-regularise.md`](../m6-deep-nets-on-a-mac/labs/37-overfit-then-regularise.md).
**Runs and wall times (M4 Pro, mps, batch 128):** baseline 46.4 s (seed 0), 38.8 s (seed 1), 39.5 s (seed 2). Change 44.5 s (seed 0). Break 12.3 s (seed 0). No precomputed steps.
**Tolerance rule:** tol = spread (max - min) over seeds 0, 1, 2; heavy labs: the baseline spread applies to every step. Here P1 and P2 use the `P1.gap` spread, 3.19 points. P3 uses the `baseline.val_acc` spread, 3.49 points.

<details><summary>P1. Training minus validation accuracy, in points: 5,000 training images (500 per class, seed 0), no augmentation, after 30 epochs.</summary>

**Answer:** 39.36 points at seed 0, tolerance 3.19 points. Hit when the value sits inside the learner's 80% range.

Seed-0 RESULT lines:

```
RESULT P1.gap=39.36 unit=points seed=0
RESULT baseline.train_acc=99.7 unit=percent seed=0
RESULT baseline.val_acc=60.34 unit=percent seed=0
```

Other seeds: `P1.gap` 39.14 (seed 1) and 36.17 (seed 2). `baseline.train_acc` 99.96 and 100. `baseline.val_acc` 60.82 and 63.83.

**Why:** The network has about 0.3 M parameters, roughly 60 per training image, and 30 epochs at batch 128 is 1,200 Adam steps over the same 5,000 images. That is enough to fit almost every training image, background and label quirks included, so training accuracy ends at 99.7%. Validation accuracy counts only what carries over to new images, 60.34% here, and the rest of the training accuracy is memorization.

**Common wrong prediction:** a small gap, 5 to 15 points, on the idea that a 0.3 M-parameter network is too small to memorize. Capacity per training image decides, and Zhang et al. (ICLR 2017) showed standard CNNs fit even random labels.
</details>

<details><summary>P2. Add random crop (4-pixel reflect padding) and horizontal flip (p = 0.5) to the training batches of the same run (5,000 images, seed 0, 30 epochs): the gap, direction (up, down or same) and size as the gap difference, augmented minus plain, in points.</summary>

**Answer:** down. The gap goes from 39.36 to 9.33 points, `P2.gap_delta` = -30.03 points, tolerance 3.19 points. The effect `P2.gap:P1.gap` is -30.03 points, more than 2x the spread (ok true). Hit when the prediction says down and its size range holds the delta.

Seed-0 RESULT lines:

```
RESULT P2.gap=9.33 unit=points seed=0
RESULT P2.gap_delta=-30.03 unit=points seed=0
RESULT change.train_acc=74.68 unit=percent seed=0
RESULT change.val_acc=65.35 unit=percent seed=0
```

Other seeds: none (heavy lane: change runs at seed 0 only).

**Why:** Each training image now arrives as one of 162 versions (81 crop offsets times 2 flips), so in 30 epochs the network meets any one version about 0.2 times and cannot memorize pixels. Most of the narrowing comes from the training side: training accuracy on the stored images falls from 99.7% to 74.68%, while validation accuracy moves from 60.34% to 65.35% (effect `change.val_acc:baseline.val_acc` = 5.01 points). That validation gain is under 2x the baseline validation spread (3.49 points) and rests on one seed, so this build does not claim it as established. At a fixed 30-epoch budget the augmented model now underfits (the "training accuracy low?" branch of the module README diagram), which is why augmented recipes train for longer.

**Common wrong prediction:** "the gap closes because validation accuracy jumps". Here the gap closes mostly because training accuracy falls. A narrower gap is not by itself a better model: read validation accuracy, with its seed spread, next to the gap.
</details>

<details><summary>P3. 500 training images (50 per class, seed 0, inside the 5,000), no augmentation, trained until training accuracy first reaches 100% (checked after every epoch, cap 100 epochs): validation accuracy on the 10,000 test images, in percent.</summary>

**Answer:** 36.96% at seed 0, tolerance 3.49 points. Training accuracy reached 100% after 24 epochs, inside the 100-epoch cap.

Seed-0 RESULT lines:

```
RESULT P3.val_acc=36.96 unit=percent seed=0
RESULT break.train_acc=100 unit=percent seed=0
RESULT break.gap=63.04 unit=points seed=0
RESULT break.epochs_to_100=24 unit=epochs seed=0
```

Other seeds: none (heavy lane: break runs at seed 0 only).

**Why:** Fifty images per class take 4 batches per epoch, and the network memorizes all of them in 24 epochs, so 100% training accuracy is cheap and says nothing about new images. Validation accuracy falls from 60.34% at 5,000 images to 36.96% at 500 (effect `P3.val_acc:baseline.val_acc` = -23.38 points), and the gap grows from 39.36 to 63.04 points (effect `break.gap:P1.gap` = 23.68 points). Those two points are the learning curve: 10x the data buys validation accuracy and shrinks the gap, and both effects clear 2x the spread.

**Common wrong prediction:** near 10% (chance), on "a memorized set learns nothing", or near the 5,000-image validation accuracy, on "100% training accuracy means it learned the classes". Fifty images per class carry real signal, well above chance, but far less than 500.
</details>

<details><summary>Rebuild check</summary>

Solution: [`rebuild/37_dropout_and_augment.py`](rebuild/37_dropout_and_augment.py). Stub: [`m6-deep-nets-on-a-mac/rebuild/37_dropout_and_augment.py`](../m6-deep-nets-on-a-mac/rebuild/37_dropout_and_augment.py). Verdict: REBUILDCHECK OK. The stub fails with NotImplementedError (exit 1) and the solution prints `check: PASS` (exit 0).

`check()` compares with torch only (`F.dropout`, `F.pad` with `mode="reflect"`, `Tensor.flip`), never with this lab's results. It checks: the mean stays within 1% at p = 0.3 on 200,000 ones; survivors equal F.dropout's 1 / (1 - p) and the keep rate matches; eval mode returns the input; augment keeps the batch shape; every output image is a 32 x 32 window of the reflect-padded input, flipped or not; crops and flips are drawn per image; pad 0 with flip_p 0 returns the batch, and flip_p 1 flips every image.
</details>

<details><summary>Card drafts</summary>

| ID | Lab | Type | Question |
|---|---|---|---|
| 37-M | 37 | M | Random crop and flip narrowed the train-validation gap on 5,000 CIFAR-10 images at the same 30-epoch budget. Which side of the gap moved most, and why does augmentation move it? |
| 37-N | 37 | N | A 0.3 M-parameter ResNet trained on 500 CIFAR-10 images until training accuracy first hit 100%: about what validation accuracy did it reach, and what does that say about 100% training accuracy? |
| 37-D | 37 | D | You add random crop and flip, the training accuracy your loop logs drops sharply, and a teammate says augmentation hurt the model. What do you check first? |

Keys:

- **37-M:** training accuracy moved most (99.7% to 74.68% on the stored images, seed 0), validation less (60.34% to 65.35%). Must mention: (1) 162 versions per image, so pixels cannot be memorized; (2) at a fixed budget the model now underfits, so train longer; (3) a narrower gap alone is not a better model.
- **37-N:** about 36.96% (seed 0, M4 Pro reference run), against 60.34% at 5,000 images and 10% chance. Must mention: (1) 100% training accuracy came in 24 epochs, so it is cheap; (2) training accuracy measures fit to seen images, and only held-out accuracy measures generalization; (3) going from 5,000 to 500 images changed validation accuracy by -23.38 points.
- **37-D:** Must mention: (1) where the logged training accuracy is measured: on augmented batches in train mode it is lower by design, so score the stored training images in eval mode, as this lab does, before comparing (augmentation can still lower that number, see 37-M); (2) compare validation accuracy with the plain run at the same seed, against the seed spread; (3) training accuracy down with validation flat or up is less memorization, not a worse model.
</details>

<details><summary>Build notes</summary>

- **Knob changes:** none. Every effect the lab teaches clears 2x the seed spread at the spec's configs: `P2.gap:P1.gap` (augmentation narrows the gap), `P3.val_acc:baseline.val_acc` and `break.gap:P1.gap` (the 2-point learning curve), all ok true in the .json.
- **Secondary effect, not taught as real:** `change.val_acc:baseline.val_acc` = 5.01 points against a spread of 3.49 points, ok false. It rests on one seed, and the lab's question is about the gap, so it is reported with its spread and not inflated. The seed spread is unpaired (each seed draws a different 5,000-image subset), while change and baseline at one seed share the subset, the starting weights and the batch order, so the rule is conservative here. A longer budget for both runs would likely separate it, but that changes the spec's 30-epoch P1 config, so the build kept the spec.
- **Precomputed steps:** none. Smoke times one 5,000-image epoch on random pixels, plain and augmented, so the runs could be sized: every step sits far under 6 minutes, as the wall times above confirm.
- **Calibration fix:** the first smoke warmed up on 8 full batches only, so the timed plain epoch paid MPS graph compilation for the last partial batch of 8 and read slower than the augmented epoch. The warmup is now one full epoch and the timing a median of 3. Smoke only: no measured mode changed, and all five reference runs come from the current script.
- **Choices inside the spec:** the 500 break images are the first 50 per class in the same seed's order, so they sit inside the 5,000 and the learning curve is nested. "100% train accuracy" is scored in eval mode (batch norm running statistics) on the stored images after each epoch, cap 100. The augmented run's training accuracy is scored on the stored, unaugmented images in eval mode, so it compares with the baseline's. The validation set is the 10,000 CIFAR-10 test images. Each channel is normalized with the training subset's own mean and std. The batch order has its own generator seeded by `--seed`, so plain and augmented runs see the same batches; the crop and flip draw from the global CPU generator. Dropout p is 0.0 (the identity) in all three steps; the 0.3 stretch is the learner's and is not run by the build.
- **Download:** the Toronto server was slow during the build, so the tar took most of an hour; two earlier attempts by a previous build agent failed on the mlrun timeout and on a local DNS outage. The tar matched the published MD5, and the Hugging Face fallback was not needed. The lab file's advice to start `--download` a day early stays.
- **Prototype comparison:** the spec carries no `[answers only]` prototype values for lab 37, so there is nothing numeric to compare. Each direction in the spec's concept text holds: with no augmentation at 5,000 images the network memorizes, augmentation narrows the gap, and 500 images give lower validation accuracy and a larger gap.
</details>
