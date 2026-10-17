# 28. Pixel baseline, then SGD by hand: loss, gradient and learning rate: reference answers

> Spoilers. The AI opens one block at a time, only after that step's prediction row exists and the learner pasted their own RESULT lines, or after 'debrief 28'.

**HW:** `HW chip='Apple M4 Pro' cpu=14 gpu=20 mem_gib=24 macos=26.5.1 python=3.13.7 torch=2.14.1 device=cpu`
**Seeds:** 0, 1 and 2 for every step (light lane). The learner runs seed 0, the default, so grade against seed 0 and the learner's own pasted line.
**Reference script:** `m5-under-the-hood/scripts/28_sgd_by_hand.py` (level W: the learner's script is the reference), sha256 prefix `65bb49d53a2db58c`.
**Runs and wall times (seeds 0, 1, 2, cpu, light lock):** baseline 3.8 s, 1.9 s, 1.9 s; change 1.8 s, 1.9 s, 1.9 s; break 3.7 s, 2.0 s, 2.1 s. Precomputed steps: none.
**Tolerance rule:** tol = spread (max - min) over seeds 0, 1, 2; heavy labs: the baseline spread applies to every step. P2 is a dir: the same band in its lab row (under 0.005 either way) sets the label, and the P2 block says how to grade it. P3 is a pick, so it has no numeric tolerance: the seed-0 option is the answer, and seeds 1 and 2 show how stable it is.

<details><summary>P1. Validation accuracy of "closer to the mean 3 or the mean 7" by L1 distance</summary>

**Answer:** 0.951423. Tolerance 0.0 (spread 0.0): the rule has no random part, so seeds 1 and 2 give the same 0.951423.

```
RESULT P1.mean_image_acc=0.951423 unit=fraction seed=0
RESULT baseline.acc_epoch1=0.785574 unit=fraction seed=0
RESULT baseline.acc_epoch5=0.946516 unit=fraction seed=0
RESULT baseline.acc_epoch20=0.967125 unit=fraction seed=0
RESULT baseline.epoch_losses=0.3978,0.1268,0.07666,0.06159,0.05344,0.04832,0.0446,0.04171,0.03948,0.03766,0.03624,0.03495,0.03381,0.03276,0.03178,0.0309,0.03008,0.02935,0.02868,0.02805 seed=0
RESULT baseline.loss_ratio=0.070524 unit=epoch20/epoch1 seed=0
RESULT baseline.loss_outcome=still_falls seed=0
```

Other seeds: `baseline.acc_epoch1` 0.916094 and 0.909715; `baseline.acc_epoch5` 0.957311 and 0.952895; `baseline.acc_epoch20` 0.973013 and 0.969087; `baseline.loss_ratio` 0.165488 and 0.10235; `baseline.loss_outcome` `still_falls` at both.

**Why:** the two mean images are the whole model, so nothing is learned and nothing depends on the seed. A 7 puts its ink on a top bar and one diagonal, a 3 on two curves down the right side, so most images sit closer to their own average; the misses are mostly 3s (fastbook prints 0.9168 for 3s and 0.9854 for 7s). It is a high bar: at seed 0 the trained linear model is still under it after 5 epochs (`baseline.acc_epoch5` 0.946516) and clears it by epoch 20 (`baseline.acc_epoch20` 0.967125); seeds 1 and 2 clear it by epoch 5 (0.957311, 0.952895).

**Common wrong prediction:** far below what a trained model gets, because averaging pixels sounds too crude to work.

</details>

<details><summary>P2. One hidden layer of 30 ReLU units: accuracy after 20 epochs vs the linear model</summary>

**Answer:** same. Seed 0: `P2.acc_epoch20` 0.970069 and `P2.delta_vs_linear` 0.00294405, inside the same band of the lab's P2 row (under 0.005 either way). Seeds 1 and 2: `P2.delta_vs_linear` -0.000490665 and -0.00343478, also inside the band, so the label is same at every seed and only the sign flips. Tolerance 0.00637883 (spread of `P2.delta_vs_linear`); the band, not the tolerance, sets the label. The mkanswers effect (`P2.acc_epoch20` minus `baseline.acc_epoch20`, mean over seeds 0 to 2) is -0.0003270000000000402 against a spread of 0.006869000000000014: under 2x the spread, a null effect, and the lab teaches it as one. At one seed both models train on the same batch order (the shuffles have their own generator), so the delta compares the two architectures, not two batch orders.

**Grading:** take the label from the learner's pasted `P2.delta_vs_linear` and the band: same when it is under 0.005 either way, up or down when it is 0.005 or more on that side. A same call hits when the pasted delta is inside the band, and inside the learner's own range if they wrote a narrower one. An up or down call hits only when the pasted delta is outside the band on that side and inside the call's size range. At seed 0 the delta is inside the band, so an up or down call misses, even one whose range reaches down to the pasted value. Inside the band the sign is seed noise at this configuration (positive at seed 0, negative at seeds 1 and 2), so a right sign alone teaches nothing.

```
RESULT change.acc_epoch1=0.919529 unit=fraction seed=0
RESULT change.acc_epoch5=0.957802 unit=fraction seed=0
RESULT P2.acc_epoch20=0.970069 unit=fraction seed=0
RESULT P2.delta_vs_linear=0.00294405 unit=fraction seed=0
RESULT change.epoch_losses=0.1413,0.06701,0.05314,0.04501,0.0403,0.03629,0.03297,0.0313,0.02903,0.02704,0.0265,0.02547,0.02473,0.02438,0.02386,0.02334,0.02302,0.02263,0.02235,0.02214 seed=0
RESULT change.loss_ratio=0.156742 unit=epoch20/epoch1 seed=0
```

Other seeds: `P2.acc_epoch20` 0.972522 and 0.965653; `change.acc_epoch1` 0.930815 and 0.502453; `change.acc_epoch5` 0.95633 and 0.502944.

**Why:** both models are held back by the optimizer, not by what they can draw. With N(0, 1) weights over 784 pixels most starting outputs sit far out on the sigmoid's flat tails, where the slope, and so every gradient, is close to zero; the hidden layer sums 30 such units, so the deeper net starts further out still (the build's init probe at seed 0, which the lab does not print: median starting |logit| 10.6884 for the linear model, 23.2856 for the hidden net; the slope at 5 is under 0.007, against 0.25 at 0). At seed 2 the hidden net sat at chance for its first 15 epochs (`change.acc_epoch1` 0.502453, `change.acc_epoch5` 0.502944, `change.epoch_losses` between 0.492 and 0.4973 for epochs 1 to 15) before it escaped to 0.965653, and since 3s vs 7s is close to linearly separable, a bent boundary has little to add in 20 epochs.

**To see it in the learner's own output** (after the session, since nothing runs after 0:42): `python scripts/28_sgd_by_hand.py --change --seed 2`, then open `~/ml-data/results/lab28/loss-change-seed2.png`. The batch loss sits flat for 15 epochs, then drops. At level W the AI may also draw, on request, a histogram of the starting outputs (logits) at seed 0, which shows the probe's figures.

**Common wrong prediction:** up by one to two points, from "more capacity is better" or from fastbook's 30-unit net at 0.982826, which used a different setting (PyTorch's small default init, learning rate 0.1, 40 epochs).

</details>

<details><summary>P3. Learning rate x 100: diverges to NaN, still falls, or oscillates or stalls</summary>

**Answer (seed 0):** `still_falls`. Seeds 1 and 2: `oscillates_or_stalls` and `still_falls`. No seed gives `diverges_to_nan`. The option depends on the seed: in 20 seeds of `--break` run before the review round (tagged exploration runs with the earlier shuffle wiring, see the build notes), 17 gave `still_falls`, 3 froze and gave `oscillates_or_stalls` (seeds 1, 5 and 15 under that wiring), and none gave NaN or inf. The current script's seeds 0 to 2 give the same options as those runs. Compare the learner's confidence with that 17 of 20.

```
RESULT break.acc_epoch20=0.98528 unit=fraction seed=0
RESULT break.epoch_losses=0.0577,0.02215,0.01762,0.01559,0.01341,0.01288,0.01184,0.0116,0.01157,0.01149,0.01063,0.01048,0.01044,0.009699,0.009395,0.009073,0.009265,0.008881,0.008922,0.008573 seed=0
RESULT break.loss_ratio=0.148597 unit=epoch20/epoch1 seed=0
RESULT P3.loss_outcome=still_falls seed=0
```

Other seeds: `break.loss_ratio` 1.00843 and 0.195885; `break.acc_epoch20` 0.504416 and 0.984789. The mkanswers effect (`break.loss_ratio` minus `baseline.loss_ratio`) is 0.33818333333333334 against a spread of 0.859833: under 2x the spread, because seed 1 froze.

**Why:** `mnist_loss` averages sigmoid outputs, so it can never leave 0 to 1, and its gradient per weight is at most the sigmoid's top slope (0.25) times a pixel (at most 1): a 100x step is large but finite, so nothing overflows to inf or NaN. At the base rate the N(0, 1) start leaves most outputs on the flat tails and the steps are small; at 100 the same small gradients make steps big enough to find a good boundary inside the first epoch (`break.epoch_losses` starts at 0.0577, the base rate at 0.3978), and the model ends higher (`break.acc_epoch20` 0.98528 against `baseline.acc_epoch20` 0.967125). The risk is the first few steps: at seed 1 they pushed every output deep into the 7 side, where the slope is about zero, so learning stopped; accuracy is 0.504416, the share of 7s in the validation set, and each batch's loss is just its share of 3s. So from epoch 3 on the epoch mean sits at 0.4945, just under the share of 3s in the training set (6,131 of 12,396), after 0.4904 in epoch 1 and 0.4946 in epoch 2. A stall, not a bounce, which the rule labels `oscillates_or_stalls`.

**Common wrong prediction:** diverges to NaN. That is what a 100x rate does when nothing caps the loss: a squared error on raw outputs, or a hand-written log of a probability that rounds to 0. `mnist_loss` has neither.

</details>

<details><summary>Rebuild check</summary>

Solution: `answers/rebuild/28_mean_image_and_sgd.py`; the stub is `m5-under-the-hood/rebuild/28_mean_image_and_sgd.py`. `rebuildcheck`: stub fails as it should (exit 1, NotImplementedError); solution passes (exit 0, `check: PASS`); `REBUILDCHECK OK`.

`check()` compares `mean_image_accuracy` with scipy `cdist(metric="cityblock")` plus scikit-learn `accuracy_score` on made-up float64 images, `mnist_loss` with `F.l1_loss` on sigmoid outputs, and `sgd_epoch` with `torch.optim.SGD` bit for bit (`torch.equal`), once as one step (batch 20) and once as three steps (batches 8, 8 and 4), at learning rate 0.5 so that the product with the gradient is exact. It fails on six broken variants: no gradient zeroing, no learning rate, no `torch.no_grad()`, a flipped loss, L2 instead of L1, and a summed loss.

</details>

<details><summary>Card drafts</summary>

| ID | Lab | Type | Question |
|---|---|---|---|
| 28-M | 28 | M | In a hand-written SGD step, why does the parameter update run under `torch.no_grad()`, and why are the gradients zeroed after it? |
| 28-N | 28 | N | On MNIST 3s vs 7s, what validation accuracy does "closer to the mean 3 or the mean 7" by L1 distance score, what about the two digits explains it, and which digit takes most of the misses? |
| 28-D | 28 | D | A sigmoid-output classifier trained with `mnist_loss` (the mean distance between each sigmoid output and its 0 or 1 target) keeps a mean training loss between 0.4904 and 0.4946 for all 20 epochs. Validation accuracy equals the share of one class, and nothing is NaN. What happened, and what do you check first? |

Keys:

- **28-M:** (1) the update is not part of the model, so autograd must not record it; an in-place change to a leaf that requires grad raises an error. (2) `backward()` adds into `.grad`, so without zeroing every step would use the running sum of all earlier gradients.
- **28-N:** 0.951423 (`P1.mean_image_acc`, the same at every seed). (1) A 3 and a 7 put their ink in different places (a 7 on a top bar and one diagonal, a 3 on two curves down the right side), so the two mean images differ a lot and most images sit closer to their own. (2) The 3s: fastbook ch 4 prints 0.9168 for 3s and 0.9854 for 7s, with the same rule on the same validation images.
- **28-D:** (1) Every output is pushed to one side of the sigmoid, so every image gets the same class. (2) The sigmoid's slope there is about zero, so the gradient vanished and training stopped without any error. (3) First check the size of the outputs before the sigmoid (the logits), then lower the learning rate or shrink the init. Context, not a must-mention: lab 28's `--break` at seed 1 did this and called every image a 7 (accuracy 0.504416, the share of 7s).

</details>

<details><summary>Build notes</summary>

The numbers below are copied from the `notes` field of `28-sgd-by-hand.json`, except the wall times, which come from its `runs` list, and the effects, which come from its `effects` field.

- **Knob changes:** none. Every spec configuration is kept: learning rate 1.0, batch 256, N(0, 1) init, 20 epochs, 30 hidden units, learning rate x 100.
- **Precomputed steps:** none. Seed-0 wall times are 3.8 s (baseline), 1.8 s (change) and 3.7 s (break). Earlier rounds ran while other builds shared the CPU slots and took longer, still under a minute, so the lab header says 3 runs x 1 min.
- **Where the spec is silent, the simplest correct choice:**
  - A seeded reshuffle every epoch, from its own generator, seeded with `--seed` and restarted for each model, so the baseline, change and break runs at one seed train on the same batch order. fastbook's hand loop does not shuffle, so its batches run all 3s, then all 7s.
  - P1 is plain accuracy over all 2,038 validation images. fastbook prints the mean of the two per-class accuracies.
  - The P3 rule: `still_falls` when the epoch-20 mean loss is under half of epoch 1's, `diverges_to_nan` on any NaN or inf, `oscillates_or_stalls` otherwise. A plain "epoch 20 below epoch 1" rule would call frozen seed 5 `still_falls` (0.5097 to 0.5061, a tagged run with the earlier wiring), so the rule asks for a fall to under half. The third label was `oscillates` until the fix round. It was renamed because a frozen run sits flat instead of bouncing.
  - The P2 same band: a delta under 0.005 either way (about 10 of the 2,038 validation images) is same. Up or down needs 0.005 or more on that side. The lab file states the band before any run, as a grading definition.
  - An epoch's loss is the mean loss per training image: each batch's mean weighted by its size (48 batches of 256 images and one of 108).
  - `--smoke` uses 40 images per folder and all 20 epochs, so it prints the same names through the same code path. It draws its three plots in memory and saves none. It takes `P2.delta_vs_linear` against its own linear run, so it needs no stored `--baseline` value.
  - Record extras: `loss_ratio` and `loss_outcome` show the P3 rule's inputs and its label on the base rate, and `change.epoch_losses` shows the seed-2 stall.
- **Fix round:** `--smoke` no longer saves loss plots, so no loss curve exists before the measured runs. The `backward()` comment no longer says it fills `p.grad`. The rerun of the 9 reference runs reproduced all 51 RESULT lines exactly. Only the text of the seed-1 P3 label changed (`oscillates` to `oscillates_or_stalls`).
- **Verifier round:** in `--smoke`, `P2.delta_vs_linear` now compares with smoke's own linear run instead of a stored `--baseline` value. Before, a learner's first `--smoke` (no `--baseline` run yet) printed a NOTE telling them to run `--baseline` first, which would show the P1 value before its row is logged. Now it prints only SMOKE lines, checked at a seed with no stored values. No training code changed: the rerun of the 9 reference runs reproduced all 51 RESULT lines exactly.
- **Review round** (an independent reviewer), two training-code fixes:
  - The shuffles now come from their own generator. Before, they came from the init's generator, so the hidden net's larger init (23,581 parameters against 785) moved its batch order away from the linear model's at the same seed, and `P2.delta_vs_linear` compared two batch orders as well as two architectures.
  - An epoch's loss is now the mean per training image. Before, it averaged the 49 batch means equally, so the last batch of 108 images counted as much as a full batch of 256.
  - The init draws did not change. The rerun of the 9 reference runs changed every trained value. P1 did not change, and every label held at every seed: `baseline.loss_outcome` `still_falls` at seeds 0 to 2, P2 same at seeds 0 to 2, P3 `still_falls`, `oscillates_or_stalls` and `still_falls`.
  - The frozen seed-1 break run now sits flat from epoch 3 on, at 0.4945, just under the share of 3s in the training set (6,131 of 12,396). Under the unweighted mean its epoch means moved with the share of 3s in each epoch's last batch.
- **Effects under 2x the spread, kept and explained, not inflated:**
  - P2 is a null effect at this configuration. The mkanswers effect is -0.0003270000000000402 against a spread of 0.006869000000000014.
  - The P3 loss ratio effect is 0.33818333333333334 against a spread of 0.859833, because seed 1 froze. What the lab teaches as robust is the absence of NaN, which holds on every seed.
  - Why the knobs stay: the factor 100 is the lab's stated goal, and N(0, 1), learning rate 1.0 and 20 epochs are the spec's configuration. The null and the freeze are the findings.
- **Tagged exploration runs** (ignored by mkanswers), made before the review round with the earlier wiring: shuffles from the init's generator and an unweighted epoch mean. They were not rerun. Init and batch order are random draws in both wirings, so the tallies still estimate how often each outcome occurs, but which seed gives which outcome can differ in the current script. At seeds 0 to 2 the current script gives the same outcome as these runs at every step. Before the review round, every seed a later script reran matched exactly: seeds 0 to 2 in the reference runs, break seeds 3 to 7 as tagged tally runs.
  - `--break`, seeds 0 to 19: `oscillates_or_stalls` (frozen) at seeds 1, 5 and 15, `still_falls` at the other 17, `diverges_to_nan` at none. Seeds 1 and 15 call every image a 7 (`break.acc_epoch20` 0.504416); seed 5 calls every image a 3 (0.495584). Seed 16 sat near 0.5 in epoch 1 (epoch-1 loss 0.5029) and escaped in epoch 2 (0.05061).
  - `--baseline` then `--change`, seeds 0 to 11: `P2.delta_vs_linear` from -0.00490677 (seed 2) to 0.00834155 (seed 9), mean 0.000736028. By sign: 7 up, 4 down, 1 tie. By the 0.005 band: 11 same, 1 up (seed 9). One stall in 12: seed 2 (`change.acc_epoch1` 0.501963).
- **Init probe** (build-only, the lab's init order, seed 0, all training images): linear model median |logit| 10.6884, share with |logit| over 5 0.75355; hidden net median |logit| 23.2856, share over 5 0.898032. The sigmoid's slope at 5 is under 0.007, against 0.25 at 0. The review round did not change the init draws, so the probe holds for the current script. The probe stays build-only: a printed starting-logit line would sit in the script the learner reads before predicting, and would point at the mechanism behind P2 and P3. The P2 block points to an after-session `--change --seed 2` run and an on-request plot instead.
- **Prototype comparison.** The spec has no `[answers only]` prototype values for this lab, so the comparison is with fastbook ch 4's published runs:
  - P1: cell 99 prints 0.9168 (3s), 0.9854 (7s) and 0.9511 (their mean). Ours, 0.951423, is the plain accuracy over the same images, so it weights the two classes by their counts. Consistent.
  - Linear model: cell 289 (N(0, 1) init, learning rate 1.0, batch 256, no shuffle, 1 + 20 epochs) ends at 0.9696. Ours after 20 shuffled epochs: 0.967125, 0.973013 and 0.969087. Consistent.
  - Hidden layer: cell 331, simple_net with fastai's Learner, ends at 0.982826, but with PyTorch's default init, learning rate 0.1 and 40 epochs. Our hand loop in that setting (build-only prototype with the earlier wiring, seeds 0 to 2) gives 0.982336, 0.982336 and 0.981354, so the loop is sound. With PyTorch's default init at learning rate 1.0 for 20 epochs, the hidden net gives 0.984298, 0.983317 and 0.983808 and the linear model 0.982826, 0.982336 and 0.982336. So the N(0, 1) init, not the loop, is what holds both models under their default-init values, and the P2 null is a finding, not a bug.
- **Repo link:** the spec lists none and says no repo file covers optimization. The lab links the payments-risk model lifecycle deep dive, §5, which answers the Staff follow-up (a worse nightly retrain must not reach production), not the optimizer itself.
- **Rebuild:** `check()` fails on six broken variants (no gradient zeroing, no learning rate, no `torch.no_grad()`, a flipped loss, L2 instead of L1, a summed loss).

</details>
