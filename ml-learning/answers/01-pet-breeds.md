# 01. Pet breeds: reuse all, part or none of a pretrained network: reference answers

> Spoilers. The AI opens one block at a time, only after that step's prediction row exists and the learner pasted their own RESULT lines, or after 'debrief 01'.

- HW (hardware) line: `HW chip='Apple M4 Pro' cpu=14 gpu=20 mem_gib=24 macos=26.5.1 python=3.13.7 torch=2.14.1 device=mps`. Here `mps` is MPS (Metal Performance Shaders), PyTorch's backend for the Apple GPU (graphics processing unit).
- Seeds: baseline at 0, 1 and 2; change and break at 0 (heavy lane). `--seed S` draws its own split (`RandomSplitter(0.2, seed=42 + S)`), head init, augmentation, batch order and dropout, so seed 0 is the spec's `seed=42` split.
- Reference script: `ml-learning/m1-whole-game/scripts/01_pet_breeds.py` (level W: the shipped script is the reference), sha256 prefix `9863cd3ba7217f2d`.
- Runs and wall times: baseline 208.1 s (seed 0), 208.1 s (seed 1), 220.7 s (seed 2); change 202.9 s; break 233.6 s. All on mps under the heavy lock, data loading in the main process (`workers=0`).
- Timing conditions for every epoch time below: M4 Pro, mps, batch 64, workers 0, train plus validation, each epoch timed from the end of its first training batch (`warmup=1`, so the one-time start-up in that batch is left out). One epoch per value in the baseline, median of 2 in the change and break runs. Epoch times include image loading on the CPU (central processing unit) and move from run to run for reasons this build did not isolate, so read them only within one run (see the timing notes).
- Tolerance rule: tol = spread (max - min) over seeds 0, 1, 2; heavy labs: the baseline spread applies to every step. Here that is the P1 spread, 0.0155615 as a fraction (1.55615 points), for P1, P2 and P3.

<details><summary>P1. Error rate on the 20% validation split after fine_tune(1) with a pretrained resnet34 at 224 px, seed 0</summary>

**Answer: 0.0913396** (135 of 1,478 validation images wrong), tolerance plus or minus 0.0155615 (the seed spread). Seeds 1 and 2: 0.0757781 (112 wrong) and 0.0818674 (121 wrong). Part of that spread is the split itself, because each seed validates on a different 1,478 images. The rest comes from head initialization, augmentation, batch order and dropout.

```
RESULT P1.error_rate=0.0913396 unit=fraction seed=0
RESULT baseline.trainable_frozen=563328 unit=params seed=0
RESULT baseline.trainable_unfrozen=21830976 unit=params seed=0
RESULT baseline.sec_per_epoch_frozen=81.3044 unit=s device=mps batch=64 workers=0 warmup=1 n=1 stat=median seed=0
RESULT baseline.sec_per_epoch_unfrozen=115.753 unit=s device=mps batch=64 workers=0 warmup=1 n=1 stat=median seed=0
RESULT baseline.export_mb=87.6369 unit=MB seed=0
```

Why: the body arrives with ImageNet features (edges, fur textures, faces, ear shapes), and ImageNet itself has about 120 dog breeds, so a new 37-way head on top of those features has little left to learn. The first epoch trains the head while the body is frozen (plus the body's BatchNorm layers, which fastai keeps training), and the second unfreezes every layer, at peak learning rates from 1e-5 for the early body to 1e-3 for the head. Two passes over 5,912 training images land in the same band as fastbook's published `fine_tune(2)` run (chapter 5, cell 33: 0.095399 after its first unfrozen epoch, 0.080514 after its second).

Common wrong prediction: 20 to 40% error, because 37 classes and 2 epochs sound hard. The opposite miss is carrying over fastbook chapter 1's cats-vs-dogs error (0.004060), which is a 2-class problem.

</details>

<details><summary>P2. The same fine_tune(1), body kept frozen for both epochs: error rate up, down or same vs P1, and by how many percentage points</summary>

**Answer: same, within noise.** At seed 0 the frozen-body run came out 0.67659 points lower than P1 (`P2.delta_vs_P1` -0.67659; `P2.error_rate` 0.0845737, 125 wrong, vs 0.0913396, 135 wrong). That is 10 of the 1,478 images, under half of one seed spread (1.55615 points, 23 images). So the effect does not clear the 2x-spread bar (mkanswers: effect -0.0067659, ok false).

Grading uses the prediction-log rule for dir rows and the learner's own pasted `P2.delta_vs_P1`. "Same" counts as the right direction, because it is the verdict. "Down" or "up" counts only when it matches the sign of the learner's own delta. Hit when the direction counts and their delta is inside their written range. Compare sizes (absolute values) when the range is a size, such as "down, 1 to 3 points", and the signed delta when the range is signed, such as "same, -2 to 2". The tolerance only says whether their run reproduces this one.

```
RESULT P2.error_rate=0.0845737 unit=fraction seed=0
RESULT P2.delta_vs_P1=-0.67659 unit=points seed=0
RESULT change.sec_per_epoch=92.5009 unit=s device=mps batch=64 workers=0 warmup=1 n=2 stat=median seed=0
```

Why: freezing does not stop learning. The head trains, and fastai keeps the body's BatchNorm weights training too (`train_bn=True`), so 563,328 parameters train while frozen (546,304 in the head, 17,024 in the body's BatchNorm layers) against 21,830,976 unfrozen. The two runs share their first epoch exactly (the same losses and error rate in the `.out`). In the second epoch P1's unfrozen body trains at peak rates of only 1e-5 (early layers) and 1e-4 (later layers), too little in one epoch to improve features that already suit pets, while the head and BatchNorm layers train in both runs. P1 ends that epoch with the lower training loss but not the lower validation loss (one seed only). Pets look like ImageNet, so frozen features are already good: fastbook's own frozen `fit_one_cycle(3, 3e-3)` (chapter 5, cell 125: 0.074425) lands as low as its 3-epoch `fine_tune(2)` (0.080514).

Common wrong prediction: up by 3 to 10 points, from "unfreezing always helps". Unfreezing pays when the images are far from ImageNet (X-rays, satellite tiles, document scans) or when there are enough epochs and data to adapt the body. Neither holds in a 2-epoch Pets run.

</details>

<details><summary>P3. The same resnet34 trained 2 epochs from random weights: error rate (Parkhi et al. 2012 reached 59.21% accuracy)</summary>

**Answer: 0.879567** (1,300 of 1,478 wrong, so accuracy 0.120433), tolerance plus or minus 0.0155615. The effect vs P1 is 0.7882274 (mkanswers ok true), far above 2x the spread.

```
RESULT P3.error_rate=0.879567 unit=fraction seed=0
RESULT break.sec_per_epoch=109.976 unit=s device=mps batch=64 workers=0 warmup=1 n=2 stat=median seed=0
RESULT break.best_accuracy=0.915426 unit=fraction runs=3 seed=0
RESULT break.best_minus_parkhi=32.3326 unit=points seed=0
```

Why: from random weights every filter starts as noise and must be learned from 5,912 images in 2 passes, far too little signal for 21,830,976 parameters. These runs do not isolate that cause, because no pair of them differs only in the starting weights. Against P1, P3 also changes the schedule: one `fit_one_cycle(2, 2e-3)` with every layer training from the first step, where `fine_tune(1)` has a frozen warm-up epoch and then discriminative rates. Against P2 (0.0845737), P3 changes the schedule in the same way, and also which layers train: every layer, where P2 trains only the head and the body's BatchNorm layers. So the effect vs P1 is the whole recipe change. The mechanism points at the starting weights as the main cause, but no run here splits the gap between them and the other difference. A one-knob test would swap only the weights inside one recipe (a random-weight learner run through `fine_tune(1)`, or frozen like P2); the build did not run one. Accuracy 0.120433 is above chance (1 in 37, 0.027) but far below Parkhi et al. 2012's 59.21% from hand-built features, while the best of the three runs (`break.best_accuracy` 0.915426, the frozen-body P2 run) beats Parkhi by 32.3326 points.

Common wrong prediction: 40 to 60% error, from assuming a modern network trained from scratch at least matches 2012's hand-built features. Without pretraining, 2 epochs get nowhere near them.

</details>

<details><summary>Rebuild check</summary>

- Solution: `ml-learning/answers/rebuild/01_fine_tune_by_hand.py`. Stub: `ml-learning/m1-whole-game/rebuild/01_fine_tune_by_hand.py`.
- `rebuildcheck`: stub fails as it should (exit 1, NotImplementedError); solution passes (exit 0, `check: PASS`); REBUILDCHECK OK.
- `check()` compares with the libraries only: `nn.Linear(512, 37)` has 18,981 parameters and torchvision's `resnet18(num_classes=37)` has 11,195,493; the frozen epoch must expose exactly the head, the unfrozen epochs everything; the learning rates must be base_lr for the head while frozen, then base_lr / 200 and base_lr / 2; `conv1` must not move while frozen and must move after unfreezing.
- Mutation tests, rerun in the fix round: a version that never freezes, a version with one learning rate after unfreezing, and a version that keeps the BatchNorm layers trainable while frozen (as fastai's `train_bn=True` does) all fail `check()`. The last one fails at the trainable-count assert by design: the stub asks for a simplified fine_tune that freezes the whole body.
- The stub and solution docstrings are identical. They call the function a simplified fine_tune, say only that its freezing, parameter groups and schedule are simpler than fastai's (so the lab's Q3 stays open), and list the PyTorch calls the bodies need: `requires_grad`, `nn.Linear(model.fc.in_features, n_classes)`, `named_parameters()` and Adam with parameter groups. The lab file's rebuild bullet says the same.

</details>

<details><summary>Card drafts</summary>

| ID | Lab | Type | Question |
|---|---|---|---|
| 01-M | 01 | M | On Oxford Pets, `fine_tune(1)` with the ResNet-34 body kept frozen for both epochs matched the normal `fine_tune(1)` within the seed spread. Why, and when would unfreezing the body win? |
| 01-N | 01 | N | After `fine_tune(1)` at 224 px (2 epochs in all), what error rate did a pretrained resnet34 reach on 37 pet breeds, and what did the same network reach after 2 epochs from random weights? Why the gap? |
| 01-D | 01 | D | With fastai 2.8 defaults on an M4 Pro, the frozen first epoch of `fine_tune(1)` trains only a small fraction of the parameters, yet takes most of the time of the unfrozen second epoch. Give two reasons, and the first measurement you would take. |

Keys:

- 01-M: (1) ImageNet features already fit pets (about 120 of ImageNet's classes are dog breeds), so the head does most of the work; (2) the runs differ only in the second epoch, and one unfrozen epoch at body rates of 1e-5 and 1e-4 barely moves the body, while the head and the BatchNorm layers train in both runs; (3) unfreeze for images far from ImageNet (X-rays, satellite, documents) or with more epochs and data.
- 01-N: (1) both numbers: pretrained 0.0913396 at seed 0, accept 0.075 to 0.092 (the seed range, 0.0757781 to 0.0913396); random weights 0.879567, accept 0.86 to 0.90 (plus or minus one seed spread, 0.0155615); (2) the main reason: pretrained filters already detect useful features, while from random weights every filter must be learned from 5,912 images in 2 passes. Context, not required: the scratch run also uses a different schedule from `fine_tune(1)`, so the gap is not a pure pretraining effect; it is still above chance (1 in 37) and far below Parkhi 2012's 59.21%.
- 01-D: (1) data loading costs the same in both epochs: fastai 2.8 runs `num_workers=0` on macOS, so decoding and resizing every image happen on the CPU in the main process; (2) with `train_bn=True` the BatchNorm layers in the frozen body still train, so the backward pass still runs back through the whole body and only the convolution weight gradients are skipped; (3) the first measurement: time one pass over `dls.train` with no model and compare it with the epoch time. Context: in the seed-0 reference run (M4 Pro, mps, batch 64, each epoch timed after its first batch) the frozen epoch took 81.3044 s and the unfrozen one 115.753 s.

</details>

<details><summary>Build notes</summary>

**Knob changes: none for effect size.** The P2 effect (-0.0067659) is under half of one seed spread, so it fails the 2x rule (ok false). It was not tuned up: the spec asks P2 as up, down or same, and the concept claims a real effect only for pretraining vs random weights (P3, effect 0.7882274, ok true). Per `ml-learning/CLAUDE.md` section 12 a small or null effect is reported with its spread, never inflated. The heavy-lane protocol runs change at seed 0 only, so the P2 vs P1 comparison is one paired seed. The third fix round (below) changed how the change is built so that it varies one knob, not to move its effect.

**Precomputed steps: none.** The longest seed-0 run is the break at 233.6 s, under the 6-minute cap.

**Fix round.** After review the script changed in three places, so all five reference runs were redone: two comments were corrected (the MPS pooling note and the `__main__` guard), and each epoch is now timed from the end of its first training batch (`warmup=1`), because the first build's epoch times included one-time start-up. The rerun reproduced every error rate, per-epoch loss, parameter count and export size of the first build exactly (fastai `set_seed(reproducible=True)` on MPS); only the timings moved. The seed-0 baseline rewrote the files lab 02 reads (`export.pkl` and `valid_files.txt`) from that identical training, and `load_learner(path, cpu=True)` loads the new export and predicts.

**Second fix round (independent review), text only.** The P3 answer had credited its whole gap to the starting weights, and the lab file did not say what the change and the break fail to isolate. The P3 answer, the 01-N card key, the lab file's change and break Why lines and the P2 deviation note below now name the schedule and trainable-layer differences. No script, run or .json value changed, so nothing was rerun.

**Third fix round (second independent review), code change.** The second review found that the change still varied two knobs against P1: a single frozen `fit_one_cycle(2, 2e-3)` replaced `fine_tune(1)`, so the schedule changed as well as the unfreeze. The change now runs the baseline's own `fine_tune(1, base_lr=2e-3)` call with one extra callback, `KeepFrozen`, whose `before_fit` calls `learn.freeze()`. `fine_tune` unfreezes the body between its two `fit_one_cycle` calls, and the callback freezes it again before the second call's first step, so the schedule and learning rates stay the baseline's. Two checks back this. On CPU, with a tiny synthetic learner (not a lab run), `KeepFrozen` left the body's convolution weights unchanged while its BatchNorm weights and the head moved, and the second fit's learning-rate schedule matched plain `fine_tune`'s exactly. And the seed-0 change run's first epoch reproduces the baseline's first epoch exactly (the same losses and error rate in the `.out`). To keep the script within 150 lines, `EpochTimer` and one line of `download` were written more compactly, with no change in behaviour. The script hash changed, so the smoke run and all five reference runs were redone, and mkanswers rebuilt the .json and .out. P1 at all three seeds and P3 reproduced the earlier runs exactly. P2, its delta, the break's best-of-three values and every timing are new. `baseline.export_mb` moved in the fourth decimal and now differs by 0.0001 MB across seeds. A tensor's byte size is fixed by its shape, so the difference sits in the pickled Python objects, not in the weights. `load_learner(path, cpu=True)` loads the rewritten export and predicts. The lab file's P2 row, change section, break Why line, reading list and Compute line were updated to match.

**Deviations from the spec, and why:**

- `Resize(448)`, not 460. On MPS with torch 2.14.1 the spec's `Resize(460)` crashed the first smoke run in the validation pass: `RuntimeError: Adaptive pool MPS: input sizes must be divisible by output sizes` (PyTorch issue 96056). fastai's bilinear GPU augmentation (`_grid_sample` in `fastai/vision/augment.py`) first area-downsamples any batch more than 2x the target size, through `adaptive_avg_pool2d`, and 460 to 448 is not divisible. 448 is exactly 2 x 224, so that step is skipped and the presizing idea is unchanged: one large per-item resize on the CPU, then one GPU augmentation pass down to 224. The script comment and the Q prompt say 448. `PYTORCH_ENABLE_MPS_FALLBACK` was not tried (forbidden).
- `Normalize.from_stats(*imagenet_stats)` sits in `batch_tfms` explicitly. `vision_learner` adds ImageNet normalization only when `pretrained=True`, so without it the break would change two things (weights and input scaling). For the pretrained runs this is exactly the transform fastai would add (it does not add a second one).
- `num_workers`: the spec says set and record it. fastai 2.8.12's `DataLoader` forces 0 on macOS whatever is passed (`fastai/data/load.py`: `if sys.platform == "darwin" and num_workers > 0: num_workers = 0`). The script sets `WORKERS = 0` and records the effective value in the DATA line and in every timing RESULT line (`workers=0`). The `__main__` guard stays, so the script is safe if workers are turned on. In the first build, a tagged experiment (job `01-baseline-s7-w8`) ran a scratch copy of the script that overrode fastai's macOS guard to use 8 workers. Both of its epochs ran much shorter than any reference epoch. Its figures live only in the build log `runs/01/baseline-s7-w8.log`, not in the .json, and it is not like-for-like: seed 7, the first build's timer (start-up included), and two light jobs beside it on average. So read its saving only as a lower bound on what main-process loading costs. Not adopted: it needs an override of a library guard in a script the learner reads line by line.
- The spec is silent on these, so the simplest option was taken: P3 is `fit_one_cycle(2, 2e-3)` on a learner that `vision_learner` leaves unfrozen when `pretrained=False` (every parameter group at 2e-3, the same base learning rate as `fine_tune`'s default). Seconds per epoch are train plus validation, from a fastai Callback that calls `labkit.clock` (MPS synchronize) after each epoch's first training batch and again at `after_epoch` (`warmup=1`). Error rates are fastai's last-epoch `error_rate` (`learn.final_record`), with no extra validation pass.
- P2 changes one thing against P1: whether the body unfreezes for the second epoch. The spec words the change as `fit_one_cycle` on a frozen learner. `fine_tune` is two `fit_one_cycle` calls, so the change keeps both calls, with their learning rates and schedules, and the `KeepFrozen` callback keeps the learner frozen through both. The callback also keeps Q2 open, because the change block names no learning rates. The first build's single `fit_one_cycle(2, 2e-3)` changed the schedule as well (see the third fix round). P3 is not a one-knob change: it differs from P1 in the schedule too, and from P2 in the schedule and in which layers train. So the P3 answer and the lab's break Why line treat its gap as the effect of the whole recipe, with the starting weights as the likely main cause by mechanism, not by measurement.
- The goal line gives the measured run length ("one run of under 4 minutes on this Mac", from the same seed-0 wall times as the Compute line) instead of the spec's "about 2 minutes of MPS compute". That estimate counted compute only, before image loading.
- `learn.dls.device` is printed on its own DATA line (`DATA device=mps ...`), not in the HW line as the spec's note asks, because labkit writes the HW line. The HW line's `device=` comes from `labkit.pick_device()`, and the DATA line shows that the DataLoaders use the same device.
- Lab 02 interface, written by the seed-0 baseline only: `~/ml-data/models/lab01/export.pkl` (`learn.export()`; `load_learner(path, cpu=True)` loads it and predicts, checked during the build) and `~/ml-data/models/lab01/valid_files.txt` (1,478 lines, each a path relative to `ML_DATA` such as `oxford-iiit-pet/images/Abyssinian_10.jpg`, sorted by file name). Seeds 1 and 2 export to a temporary folder, only to measure `baseline.export_mb` (87.6369 MB at seeds 0 and 1, 87.637 MB at seed 2; see the third fix round).
- Data layout: the archive is `~/ml-data/oxford-iiit-pet.tgz`, extracted to `~/ml-data/oxford-iiit-pet/images/` (lab 11 shares it); the Oxford fallback unpacks into the same `images/` folder. The ResNet-34 weights come through torchvision's own hash-checked downloader inside `labkit.locked`, into the torch hub cache.
- Smoke: every 20th image (370 images: 296 train, 74 valid), all three steps in a row on the same code path, with the export going to a temporary folder. Every smoke run finished inside the 60 s smoke budget.

**Timing notes.** Every epoch time includes image loading in the main process, so it can move with CPU contention. The heavy lock lets up to two light jobs run beside a heavy one. During these five runs the ledger shows a few short lab 18 jobs beside the seed-0 baseline and change, and none beside the break or the seed 1 and 2 baselines. The times still moved. Over seeds, the frozen-epoch spread is 9.7262 s and the unfrozen 15.703 s, and the seed-1 baseline, which ran alone, has the slowest frozen epoch (91.0306 s) and the fastest unfrozen one (104.337 s). The change run's frozen epochs (92.5009 s) ran a little slower than the slowest baseline frozen epoch, and the break's epochs (109.976 s) fall inside the baseline's unfrozen range (104.337 to 120.04 s). The cause was not isolated. The candidates are the GPU job just before (every run started within 13 s of another heavy job ending, most of them lab 37 runs), the machine's thermal or power state, and any start-up work that the excluded first batch does not cover. No prediction asks about time, so no timing comparison across runs is drawn and nothing was rerun for it.

**Prototype comparison.** The spec carries no `[answers only]` values for lab 01. Its compute note (teaching review: 188 img/s fine-tuned, 639 frozen, "about 31 s and 9 s per epoch before loading") counts compute only, and it does not say whether its frozen run kept BatchNorm training. Here the seed-0 epochs take 115.753 s unfrozen and 81.3044 s frozen, with image loading in the main process. Two shared costs keep the frozen epoch from being several times faster. Loading costs the same in both epochs (the 8-worker experiment gives a lower bound on it), and with fastai's `train_bn=True` the frozen epoch still back-propagates through the whole body to reach the BatchNorm weights, skipping only the convolution weight gradients. Neither cost was broken down further on MPS, so the gap to the review's figures is not a like-for-like comparison, and it points to no model bug: the parameter counts match the architecture and the error rates reproduce exactly. The published fastbook chapter 5 outputs (a CUDA GPU, CUDA being NVIDIA's GPU computing platform; `Resize(460)`; its own file order and split) agree on direction and size: `fine_tune(2)` 0.095399 then 0.080514 (cell 33), frozen `fit_one_cycle(3, 3e-3)` 0.074425 (cell 125), against P1 0.0757781 to 0.0913396 and P2 0.0845737 here. Their epoch times show a similarly small frozen-to-unfrozen gap (about 20 s vs 24 s). No fastbook run matches P3: cell 112 is `fine_tune(1, base_lr=0.1)`, a too-high learning rate (0.834235), not random weights.

**Other.** Every run prints a `torch.jit.script` FutureWarning at import, from a dependency. It is harmless.

</details>
