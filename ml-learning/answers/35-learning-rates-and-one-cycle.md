# 35. Learning-rate finder and one-cycle: reference answers

> Spoilers. The AI opens one block at a time, only after that step's prediction row exists and the learner pasted their own RESULT lines, or after 'debrief 35'.

`HW chip='Apple M4 Pro' cpu=14 gpu=20 mem_gib=24 macos=26.5.1 python=3.13.7 torch=2.14.1 device=mps`

- Seeds: 0 for every step, plus 1 and 2 for the baseline (heavy lane). Seed 0 is the learner's default.
- Reference script: `answers/35_learning_rates_and_one_cycle_ref.py` (script sha256 prefix `e886c2f879197892`). The learner's starter, `m6-deep-nets-on-a-mac/scripts/35_learning_rates_and_one_cycle.py`, is the same file with the `lr_find()` body stubbed (make_c_starter).
- Runs and wall times in seconds (mps, heavy lock, one heavy job at a time): baseline 186.6, 185.0 and 169.7 (seeds 0, 1, 2); change 183.3 (seed 0); break 188.6 (seed 0). Each wall time covers loading, the 100-step `lr_find()` and 5 epochs.
- Tolerance rule (from the .json): tol = spread (max - min) over seeds 0, 1, 2; heavy labs: the baseline spread applies to every step.
- Raw seed-0 output: `answers/35-learning-rates-and-one-cycle.out`. Values by seed, spreads and effects: `answers/35-learning-rates-and-one-cycle.json`.

<details><summary>P1. Validation accuracy (percent) after 5 epochs of fit_one_cycle at the suggested rate (xresnet18 from scratch, 128 px, batch 64, seed 0)</summary>

**Answer: 79.6433** (percent), tolerance 0.17839999999999634 (the seed spread). Seeds 1 and 2: 79.7962 and 79.6178.

Seed-0 RESULT lines (the `PLOT` line names `~/ml-data/results/lab35/lr_find_seed0.png`):

```
RESULT baseline.lr_find_steps=89 unit=steps seed=0
RESULT baseline.suggested_lr=0.00453488 unit=lr seed=0
RESULT baseline.valley_lr=0.000432876 unit=lr seed=0
RESULT P1.valid_acc=79.6433 unit=percent epochs=5 n=3925 seed=0
RESULT baseline.acc_by_epoch=38.19,56.82,56.94,77.38,79.64 unit=percent seed=0
RESULT baseline.sec_per_epoch=31.5179 unit=s device=mps batch=64 warmup=1 n=4 stat=median seed=0
RESULT baseline.sec_per_epoch_nosync=31.5179 unit=s device=mps batch=64 warmup=1 n=4 stat=median seed=0
```

Other seeds: `baseline.lr_find_steps` 89 and 90. `baseline.suggested_lr` 0.00657933 and 0.00546228. `baseline.valley_lr` 0.000911163 and 0.000521401. `baseline.acc_by_epoch` `46.85,52.13,69.50,77.17,79.80` (seed 1) and `42.24,64.46,69.48,76.97,79.62` (seed 2). `baseline.sec_per_epoch` 32.865 and 30.381, and `baseline.sec_per_epoch_nosync` the same two values.

Why: the anneal decides the final number. After epoch 3, while the rate is still high, accuracy is noisy across seeds (56.94, 69.50 and 69.48). Epochs 4 and 5 bring the rate down toward peak/1e5 on a cosine, and all three seeds finish within 0.17839999999999634 points of each other. The suggested rate moved by 1.45x across seeds (0.00453488 to 0.00657933, with the init and batch order changing too), so one-cycle is flat around this rate. The leaderboard's 87.43% is a tuned recipe (fastai's `train_imagenette.py`, MaxBlurPool, tuned hyperparameters, the mean of 5 runs); this run uses fastai defaults, a plain xresnet18 and no augmentation beyond the random square crop of `Resize`, and lands 7.79 points below it.

Timing: the clock with `torch.mps.synchronize()` and the clock without it agree to all 6 printed digits at every seed. fastai's `Recorder` copies every batch's loss to the CPU (`AvgSmoothLoss.accumulate` calls `to_detach`, which calls `.cpu()`), and that copy waits for the GPU. So the GPU queue is already empty when an epoch callback reads the clock. The sync matters when the clock is read while work is still queued, for example around one forward pass with no `.item()`. An epoch moves 9,469 training and 3,925 validation images in 31.5179 s at seed 0, about 425 images per second overall.

Common wrong prediction: anchoring on the 87.43% leaderboard figure, or the pretrained-model habit of expecting 90% or more. The opposite slip is expecting a from-scratch net to stay under 50% after 5 epochs.

</details>

<details><summary>P2. fit at a constant rate equal to the same peak, instead of fit_one_cycle, 5 epochs, seed 0: validation accuracy up, down or same vs P1, and by how many points</summary>

**Answer: down, by 12.3312 points** (`P2.delta_vs_P1` at seed 0): 67.3121 against 79.6433. Tolerance 0.17839999999999634 (the baseline spread, heavy lane). The effect is 69x the spread.

Seed-0 RESULT lines:

```
RESULT change.peak_lr=0.00453488 unit=lr seed=0
RESULT P2.valid_acc=67.3121 unit=percent epochs=5 n=3925 seed=0
RESULT P2.delta_vs_P1=-12.3312 unit=points seed=0
RESULT change.acc_by_epoch=46.85,63.90,64.56,72.31,67.31 unit=percent seed=0
```

Why: the constant rate leads early and loses late. After epochs 1 and 2 it is ahead of one-cycle (46.85 vs 38.19, 63.90 vs 56.82), because one-cycle spends its first 25% of steps below the peak. But it never anneals: epochs 4 and 5 still take full-size steps, so the weights keep bouncing around the low region instead of settling into it, and the accuracy at the end of an epoch is a noisy sample. Here it fell from 72.31 to 67.31 in the last epoch, while one-cycle's falling rate took it from 56.94 to 79.64 over epochs 4 and 5. Momentum also stays at 0.9 instead of moving 0.95, 0.85, 0.95.

Size caveat: this is one seed. The constant run's own swing between epochs 4 and 5 (5 points) is far larger than the baseline seed spread, so the size of P2 is less certain than the tolerance suggests. The sign is not in doubt.

Common wrong prediction: "about the same, since the peak is the same", or "higher, since it spends more steps at the high rate". The final rate, not the average rate, sets the final accuracy.

</details>

<details><summary>P3. fit_one_cycle at 10x the suggested rate, 5 epochs, seed 0: validation accuracy (percent)</summary>

**Answer: 77.5796** (percent), tolerance 0.17839999999999634 (the baseline spread, heavy lane). That is 2.0637 points below P1 (`break.delta_vs_P1`), 11.6x the spread.

Seed-0 RESULT lines:

```
RESULT break.peak_lr=0.0453488 unit=lr seed=0
RESULT P3.valid_acc=77.5796 unit=percent epochs=5 n=3925 seed=0
RESULT break.delta_vs_P1=-2.0637 unit=points seed=0
RESULT break.acc_by_epoch=23.36,44.03,65.50,70.93,77.58 unit=percent seed=0
```

Why: the minimum rule divides the rate at the lowest smoothed loss by 10, so 10x the suggestion is that rate itself (step index 70 of the curve, 0.0453488). The finder stopped at step 89, where the rate was about 1.29 (1e-7 x 1e8 ** (88 / 99)), 28x higher. One-cycle also starts this run at peak/25, 0.0018, below the baseline's own peak, and AdamW plus BatchNorm keep each step bounded. So the run does not diverge. It pays early instead: 23.36 vs 38.19 after epoch 1 and 44.03 vs 56.82 after epoch 2. Then the anneal recovers most of the gap.

Common wrong prediction: "it diverges to about 10%, chance level". With one-cycle's warmup and anneal, 10x this suggestion wastes about 2 points, not the run. This lab did not test a constant rate at 10x, or a peak near where the finder stopped.

</details>

<details><summary>Rebuild check</summary>

Solution: `answers/rebuild/35_lr_find.py`. Stub: `m6-deep-nets-on-a-mac/rebuild/35_lr_find.py`.

`rebuildcheck` verdict: `stub     fails as it should (exit 1)`, `solution passes (exit 0)`, `REBUILDCHECK OK`.

The stub's `check()` builds a toy network (Linear 4 to 16, BatchNorm1d, ReLU, Linear 16 to 1) on 256 synthetic rows in batches of 64, takes 2 real SGD steps with momentum 0.9 so the optimizer holds momentum buffers, then calls `lr_find()`. It asserts: one rate and one smoothed loss per step; an early stop (the toy blows up before the rate reaches 10); rates equal to `np.geomspace(1e-7, 10, 100)`; smoothed losses equal to pandas `ewm(alpha=0.02, adjust=True)`, which is the bias-corrected average; a stop right after the first point above 4x the running minimum; `state_dict` (weights and BatchNorm running statistics) restored exactly with `torch.equal`; gradients cleared; optimizer param groups and momentum buffers restored exactly. A second call with `start_lr=1e-6, end_lr=1e-4, n_steps=30` must run all 30 steps at `np.geomspace(1e-6, 1e-4, 30)`, so a body that ignores its arguments fails.

</details>

<details><summary>Card drafts</summary>

| ID | Lab | Type | Question |
|---|---|---|---|
| 35-M | 35 | M | One-cycle and a constant rate share the same peak. The constant run is ahead after epoch 2 but behind after epoch 5. Why both? |
| 35-N | 35 | N | In lab 35, what did one-cycle at 10x the suggested rate (fastbook's minimum rule) score after 5 epochs, against the run at the suggested rate, and why did it not diverge? |
| 35-T | 35 | T | A team keeps last quarter's learning rate after raising the batch size 4x and switching optimizer. What do you tell them, and how do you get a new rate without a sweep of full runs? |

Keys:

- 35-M: (1) one-cycle warms up from peak/25 over the first 25% of steps, so its early epochs move slower; (2) it then anneals to peak/1e5, so the last steps are small and the weights settle, while the constant run still takes full-size steps and its final accuracy is a noisy sample (it fell from 72.31 to 67.31 in its last epoch).
- 35-N: (1) 77.5796 vs 79.6433 at seed 0, 2.0637 points lower (seed spread 0.17839999999999634); (2) 10x the minimum rule is the rate at the lowest smoothed loss, 28x below the rate where the finder stopped; (3) the warmup starts at peak/25 and the anneal recovers most of the early loss.
- 35-T: (1) the usable rate moves with batch size, optimizer and model (Goyal et al. 2017 scale the rate with the batch size), so the old rate is a guess; (2) rerun lr_find, about 100 mini-batches, on the new setup and read the curve (minimum / 10, or a point on the falling stretch), then train with one-cycle.

</details>

<details><summary>Build notes</summary>

Knob changes: the suggested-rate rule. The first full set of runs (an earlier script) used fastai 2.8's default rule, `valley`. Its 10x break beat its own baseline at seed 0 by a margin far above the seed spread, so the break did not break: 10x valley lands next to the loss minimum (here 10 x 0.000432876 is 0.95 of 0.00453488). The final script uses fastbook ch 5's rule, fastai's `minimum` (one tenth of the rate at the lowest smoothed loss), which is the unit the lab borrows from, and prints valley as a Record row only (`baseline.valley_lr`). All five reference runs were rerun on the final script. No other knob changed.

Effects (from the .json):

| Effect (A minus B) | Seed-0 effect | Spread | Clears 2x spread |
|---|---|---|---|
| `P2.valid_acc` minus `P1.valid_acc` | -12.331199999999995 | 0.17839999999999634 | true |
| `P3.valid_acc` minus `P1.valid_acc` | -2.063699999999997 | 0.17839999999999634 | true |

Precomputed steps: none. The seed-0 runs took 186.6, 183.3 and 188.6 s, so the Compute line reads 3 runs x 4 min.

Deviation from the spec's wording: its concept line says 10x the suggested rate "wastes the run or diverges". At seed 0 it cost 2.0637 points and did not diverge. That is reported as measured, not inflated: the cost is real (11.6x the spread), and the P3 block explains why one-cycle survives it.

Choices where the spec is silent:

- The finder follows the spec's rebuild line: rates `start_lr * (end_lr / start_lr) ** (i / (n_steps - 1))`, so step 99 would be exactly 10. fastai's own `lr_find` divides by `num_it` instead. The curve is trimmed as fastai trims it (drop the first `n_steps // 10` and the last 5 points) before `minimum` and `valley` read it.
- One AdamW optimizer, wrapped in fastai's `OptimWrapper` with fastai's Adam defaults (betas 0.9 and 0.99, eps 1e-5) and torch's default weight decay 0.01, serves `lr_find()` and then training. `lr_find()` restores the weights and the optimizer state, so every mode trains from the same random weights, and the seed is reset before `fit` so crops and dropout draws match.
- `change.peak_lr` equals `baseline.suggested_lr` at seed 0 and `break.peak_lr` is exactly 10x it, so the finder picked the same rate in three separate processes on mps.
- No augmentation beyond `Resize(128)` (a random square crop in training, centered in validation). Workers 0, fastai's rule on macOS.
- Smoke uses fastai's own `Learner.lr_find` as the stand-in for the TODO, on one image in 20 for 2 epochs. Its calibration line, `smoke.sec_per_full_epoch_est`, is `smoke_ok`: no prediction asks about it.
- Epoch times are the median of epochs 2 to 5 (warmup 1). Equal synced and unsynced times are a real result, explained in the P1 block, checked in the fastai 2.8.12 source.
- A tagged build experiment (scratch script outside the repo) ran fastai's `Learner.lr_find` on the same seed-0 learner. It stopped 2 steps later than `lr_find()`, and its `minimum` suggestion was 12% lower with the minimum at the same step index, 70. Its schedule divides by `num_it`, so at step 70 its rate is 1e8 ** (-70 / 9900), 0.878, of this one: the whole gap.

Prototype comparison: the spec holds no [answers only] values for lab 35. Against what it does give: (1) the published 87.43% is a tuned recipe, and P1 is 7.79 points below it, the expected side for fastai defaults; (2) the budget note "3 runs x 5 epochs at 128 px take about 8 to 12 minutes with loading" matches the 558.5 s of the three seed-0 runs (9.3 minutes); (3) the note's 626 images per second of compute compares with about 425 per second overall here (9,469 training plus 3,925 validation images per 31.5179 s epoch), which includes decoding and resizing in the main process.

</details>
