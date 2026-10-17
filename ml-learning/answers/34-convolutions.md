# 34. Convolutions by hand, then a CNN: reference answers

> Spoilers. The AI opens one block at a time, only after that step's prediction row exists and the learner pasted their own RESULT lines, or after 'debrief 34'.

- HW: `HW chip='Apple M4 Pro' cpu=14 gpu=20 mem_gib=24 macos=26.5.1 python=3.13.7 torch=2.14.1 device=cpu`
- Seeds: 0, 1 and 2 for every step (light lane). Seed 0 is the learner's default and the value to grade against.
- Reference script: `m6-deep-nets-on-a-mac/scripts/34_convolutions.py`, the learner's own script (level W), script hash `86798c9905a9b580`. Raw seed-0 output: `34-convolutions.out`.
- Runs: 9, all current (baseline, change and break at seeds 0, 1 and 2). Wall times in seconds for seeds 0, 1 and 2: baseline 4.4, 4.2, 3.7; change 41.0, 49.0, 47.8; break 47.3, 41.6, 43.3. Every run shared the machine with one or two heavy runs and other light runs, so these are upper bounds. Precomputed steps: none.
- Tolerance rule (from the .json): tol = spread (max - min) over seeds 0, 1, 2; heavy labs: the baseline spread applies to every step.

<details><summary>P1. Test accuracy (fraction) of the MLP, 784 to 26 to 10, about 20,500 parameters, after 1 epoch (Adam lr 1e-3, batch 64, seed 0)</summary>

**Answer:** 0.9207, tolerance 0.0019 (the seed spread). The MLP has 20680 parameters.

Seed-0 RESULT lines:

```
RESULT baseline.mlp_params=20680 seed=0
RESULT P1.mlp_test_acc=0.9207 unit=fraction seed=0
```

Other seeds: `P1.mlp_test_acc` is 0.9209 at seed 1 and 0.919 at seed 2.

**Why.** The MLP's first layer gives each of its 26 hidden units one weight per pixel position: 784 x 26 = 20,384 of its 20680 parameters. Each digit is squeezed into 26 features, and one epoch is 938 Adam steps of 64 digits, so about 8 test digits in 100 come out wrong. The seed barely matters: the spread is about a fifth of a point.

**Common wrong prediction:** 0.97 to 0.98, the figure people remember for MNIST MLPs. Those have hundreds of hidden units and train for many epochs. This one has 26 units and sees each digit once.

</details>

<details><summary>P2. The CNN instead of the MLP, about the same parameter count, the same training (1 epoch, Adam lr 1e-3, batch 64, seed 0): its test accuracy against the MLP's, direction and size in points</summary>

**Answer:** up. The CNN scores 0.975 (tolerance 0.0005), 5.43 points above the MLP at seed 0 (tolerance 0.14 points). Over the three seeds the mean effect is +0.0548 in accuracy against a spread of 0.0019, far over 2x. The CNN has 20490 parameters.

Seed-0 RESULT lines:

```
WINDOW rows 6 to 8, cols 7 to 9 of the first test digit, pixels out of 255: [[0, 0, 0], [185, 159, 151], [254, 254, 254]]
RESULT change.top_edge_by_hand=2.98824 row=6 col=7 seed=0
RESULT change.top_edge_conv2d=2.98824 row=6 col=7 seed=0
RESULT change.hand_max_abs_diff=4.76837e-07 seed=0
RESULT change.unfold_max_abs_diff=5.96046e-07 seed=0
RESULT change.cnn_params=20490 seed=0
RESULT P2.cnn_test_acc=0.975 unit=fraction seed=0
RESULT P2.cnn_minus_mlp_points=5.43 unit=points seed=0
```

Other seeds: `P2.cnn_test_acc` is 0.9752 and 0.9747; `P2.cnn_minus_mlp_points` is 5.43 and 5.57 (seeds 1 and 2). The hand-convolution lines are the same at every seed: they do not depend on it.

**Why.** Both models spend about the same budget, but the CNN's two conv layers hold only 160 + 4,640 = 4,800 of its parameters (the other 15,690 sit in the linear head over the 32 x 7 x 7 maps), and each 3x3 kernel is reused at every position: 784 positions in layer 1, 196 in layer 2. So every training digit updates each stroke detector from hundreds of windows at once, while the MLP must learn the same stroke separately at every place it appears. The price is compute: about 1.03 million multiply-adds per image against about 21,000 for the MLP, roughly 50 times as many.

**The by-hand check.** In the `WINDOW` the bottom row sums to 762 and the top row to 0, and 762 / 255 is the 2.98824 that the loops and `F.conv2d` both print. Over the whole output the loops and `F.conv2d` differ by at most 4.76837e-07, and `F.unfold` plus one matrix multiply by at most 5.96046e-07: float32 rounding, because the products are added in a different order. `F.conv2d` does not flip the kernel (it is a cross-correlation), which is why a plain window-times-kernel loop matches it.

**Common wrong prediction:** about the same, because the parameter counts match. Equal counts do not mean equal learning: weight sharing lets each conv weight learn from every position of every digit.

</details>

<details><summary>P3. Shift every test digit 4 pixels right (4 blank columns enter on the left) and re-score both seed-0 models, neither of which trains on shifted digits: which model loses more test accuracy, and how many points does each one lose?</summary>

**Answer:** the MLP, at all three seeds. At seed 0 the MLP falls from 0.9207 to 0.2438, a drop of 67.69 points (tolerance 2.20). The CNN falls from 0.975 to 0.5349, a drop of 44.01 points (tolerance 5.88). The MLP loses 23.68 points more (tolerance 7.11). For the Brier score, a right pick at confidence c scores (1 - c/100)^2.

Seed-0 RESULT lines:

```
RESULT break.mlp_test_acc=0.9207 unit=fraction seed=0
RESULT break.mlp_shifted_acc=0.2438 unit=fraction seed=0
RESULT P3.mlp_drop_points=67.69 unit=points seed=0
RESULT break.cnn_test_acc=0.975 unit=fraction seed=0
RESULT break.cnn_shifted_acc=0.5349 unit=fraction seed=0
RESULT P3.cnn_drop_points=44.01 unit=points seed=0
RESULT P3.loses_more=mlp seed=0
RESULT P3.gap_points=23.68 unit=points seed=0
```

Other seeds (1 and 2): `P3.mlp_drop_points` 69.89 and 68.92; `P3.cnn_drop_points` 43.48 and 38.13; `P3.gap_points` 26.41 and 30.79; `P3.loses_more` mlp and mlp. The original-digit accuracies repeat `P1.mlp_test_acc` and `P2.cnn_test_acc` exactly: `--break` rebuilds the same two models.

**Why.** The MLP's first-layer weights are tied to pixel positions, so a digit moved 4 pixels lands on weights trained for other strokes, and its 26 features describe a different picture: it gets about a quarter of the digits right. The CNN's kernels still fire on the same strokes, 4 pixels over, because a convolution is shift-equivariant: the feature map moves with the input. But two 2x2 max-pools turn a 4-pixel shift into a one-cell shift on the 7x7 maps, and the linear head reads those maps cell by cell, so the CNN loses a lot too, just less. At 4 pixels, a whole multiple of the two pools' combined stride, the pools absorb none of the shift: away from the borders the maps move exactly one cell, so each head weight now reads a different part of the digit.

**Common wrong prediction:** the CNN loses almost nothing, because "CNNs are translation invariant". The conv layers are equivariant, not invariant. Invariance would need pooling over the whole image (global average pooling) before the head, and this CNN ends in a position-specific linear layer.

</details>

<details><summary>Rebuild check</summary>

Solution: `answers/rebuild/34_conv2d.py`. Verdict from `rebuildcheck`: the stub `m6-deep-nets-on-a-mac/rebuild/34_conv2d.py` fails as it should (exit 1, NotImplementedError) and the solution passes (exit 0, `check: PASS`), so REBUILDCHECK OK.

`check()` compares `conv_one` with `F.conv2d` on a 9x11 image, and `conv_batch` with `F.conv2d` on a (4, 3, 10, 9) batch and 5 kernels at stride 1 and 2 and padding 0 and 1, shapes and values within 1e-5. Mutation tests during the build: a flipped kernel, the height used for the output width, a size formula without the padding, and an unfold without the stride all fail; a float32 output buffer, as in the lab script, passes.

</details>

<details><summary>Card drafts</summary>

| ID | Lab | Type | Question |
|---|---|---|---|
| 34-M | 34 | M | An MLP and a CNN both have about 20,500 parameters. Why does the CNN learn MNIST better in one epoch, and what does it pay for that? |
| 34-N | 34 | N | Every MNIST test digit moves 4 pixels right. A 784 to 26 to 10 MLP and a two-conv CNN, about 20,500 parameters each, each trained 1 epoch on the centred digits, are scored on the shifted ones. Roughly how many accuracy points does each lose, and why does the CNN lose any? |
| 34-D | 34 | D | A digit classifier scores well on its own test set but far worse on images from a new scanner, and the labels check out. What do you check first, and what fixes it without a new architecture? |

Keys, with the must-mention items:

- 34-M: (1) weight sharing: each 3x3 kernel is reused at every position, so each digit trains it from hundreds of windows, while the MLP learns each stroke at each position separately; (2) the price is compute, about 50 times the multiply-adds per image.
- 34-N: (1) the MLP about 68 points (0.9207 to 0.2438 at seed 0), the CNN about 44 at seed 0 (44.01, 43.48 and 38.13 over seeds 0 to 2); (2) two 2x2 max-pools make the shift one cell on the 7x7 maps, and the linear head reads those maps position by position; (3) convolution is equivariant, not invariant.
- 34-D: (1) compare the inputs before the model: plot a few raw digits, or the mean image, from training and from the new scanner, and look first for digits sitting off centre (in this lab a 4-pixel shift took the CNN from 0.975 to 0.5349 at seed 0); (2) if they are off centre, fix the crop or re-centre the digits in preprocessing (MNIST itself centres each digit by its centre of mass), or train with random shifts; (3) re-measure on a shifted holdout before shipping.

</details>

<details><summary>Build notes</summary>

- **Architectures.** The spec says only "about 20,500 parameters". MLP: 784 to 26 ReLU to 10, 20680 parameters. CNN: 3x3 conv 1 to 16 (padding 1), ReLU, 2x2 max-pool; 3x3 conv 16 to 32 (padding 1), ReLU, 2x2 max-pool; linear 1,568 to 10, 20490 parameters. Both counts equal the prototype's exactly, so these are taken to be the prototype's layers.
- **Training.** The spec's Adam 1e-3, batch 64, 1 epoch, with cross-entropy. Where the spec is silent, the simplest choice: PyTorch's default initialization; pixels scaled to [0, 1] with no mean and std normalization, so the shift's zero fill equals the background; each model built right after `torch.manual_seed(seed)`; the batch order drawn from a separate generator seeded with the seed, so both models see the same batches; accuracy scored 1,000 digits at a time; the shift zero-fills (`F.pad`, then a crop) instead of wrapping with `torch.roll`.
- **`--break` retrains instead of loading saved models.** It rebuilds both models with the same seed and batch order, so it needs no model files and runs on its own. Checked: its original-digit accuracies equal `P1.mlp_test_acc` and `P2.cnn_test_acc` at all three seeds, so CPU training here is deterministic from run to run. Neither model ever trains on a shifted digit.
- **Knob change: the shift is 4 pixels, not the spec's 3.** A full 3-pixel round of reference runs (script hash a93958b918c9e504, otherwise the same script) gave CNN drops of 24.61, 18.44 and 14.16 points: nonzero at every seed, but as a stand-alone effect (-0.1907 in accuracy against a spread of 0.1042) under 2x its spread. The gap between the drops cleared 2x there (mean 29.34 points against a spread of 10.45), and so did the MLP's drop. A tagged 4-pixel experiment at seeds 0 to 2, then the 4-pixel reference rounds, put every effect over 2x. One pixel more is the least change that does it, and 4 pixels is exactly one cell on the CNN's 7x7 maps. The lab file's goal, P3 row and break section say 4 pixels. The .json note keeps the 3-pixel values.
- **Effects in the .json:** `P2.cnn_test_acc:P1.mlp_test_acc` (over 2x: yes), `P3.mlp_drop_points:P3.cnn_drop_points` (the gap, yes), `break.mlp_shifted_acc:break.mlp_test_acc` (the MLP's drop, yes) and `break.cnn_shifted_acc:break.cnn_test_acc` (the CNN's drop, yes).
- **Prototype comparison.** Parameter counts 20680 and 20490: exact. MLP 0.920 against 0.9207: a gap of 0.0007, under 2x the spread. CNN 0.976 against 0.975: a gap of 0.001, equal to 2x the spread, not over it. At the spec's 3 pixels the prototype took the MLP to 0.460 and the CNN to 0.773. The 3-pixel round gave 0.4488, 0.4279 and 0.4317 for the MLP and 0.7289, 0.7908 and 0.8331 for the CNN (seeds 0, 1, 2): the same direction, and no gap over 2x the spread (1.1 points against 4.2 for the MLP, 4.4 against 20.8 for the CNN). The 4-pixel values have no prototype.
- **Names and units.** The P2 delta is `P2.cnn_minus_mlp_points`, a neutral name: an earlier draft's name stated the direction in a learner-visible file. Points are percentage points, rounded to 2 decimals because accuracies are multiples of 1/10,000.
- **Hand convolution.** The first test digit (a 7) and fastbook's top-edge kernel. The `WINDOW` line prints the 3x3 pixels under the strongest output for the learner's paper step. Nothing in it depends on the seed. It prints before the CNN trains, and the three hand-convolution RESULT lines print after training, so the paper step is done before its answer is on screen. `--smoke` skips the `WINDOW` line and prints only HW, SEED and SMOKE lines. On a machine where no `--baseline` run has stored P1 for that seed yet, as at the learner's first `--smoke`, it also prints the `NOTE` line about `P2.cnn_minus_mlp_points`, which holds no value.
- **Fix round (script hash 86798c9905a9b580).** Review fixes changed the script: the `WINDOW` print got a smoke guard and `flush=True`, the hand-convolution RESULT lines moved after `train(cnn, ...)`, and the torchvision import moved to the top of the file, so the script stays at 150 lines. All 9 reference runs were redone. Every value equals the previous round's (script hash 05422e58984ef07f) at every seed, as expected from deterministic CPU training and a change that only moves prints.
- **Run order.** In this round all three `--baseline` runs finished before any `--change` run started, so `P2.cnn_minus_mlp_points` at each seed reads that seed's P1 from this round. In the previous round the seed-0 `--change` read the P1 stored by an earlier round's baseline, an identical value. On any rerun, finish `--baseline` before starting `--change` at each seed.
- **Timing.** Seed-0 wall times were 4.4, 41.0 and 47.3 s, each beside a heavy run and other light runs. The previous round, with up to 3 light runs sharing the CPU, took 5.3, 50.0 and 102.6 s; the 3-pixel round, with less sharing, took 2.9, 26.4 and 24.0 s (the code path and its cost are the same). The lab's Compute line, 3 runs x 1 min, rounds this round's seed-0 times up. No step is precomputed.
- **Interview question kept as the spec wrote it.** A review noted that "Why use a CNN for images instead of an MLP with the same parameter count?" presumes the CNN is the better pick. The brief says to copy it from the spec, and the module README's lab table repeats it, so a neutral wording would have to change both files. That is left to the curriculum owner.
- **Borrowed from.** The spec's after-lab pointer "fastbook ch 13 cell 187" was not checked against the notebook in this build (no network lookups). The lab file cites the chapter's two section names instead.
- **Script length.** 150 lines, the brief's upper bound: the hand convolution, the unfold convolution, two models and the shift sit in one level W file.

</details>
