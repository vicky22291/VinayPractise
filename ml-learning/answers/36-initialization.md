# 36. Initialization and activation statistics: reference answers

> Spoilers. The AI opens one block at a time, only after that step's prediction row exists and the learner pasted their own RESULT lines, or after 'debrief 36'.

`HW chip='Apple M4 Pro' cpu=14 gpu=20 mem_gib=24 macos=26.5.1 python=3.13.7 torch=2.14.1 device=cpu`

- Seeds: 0, 1 and 2 for every step (light lane). Seed 0 is the learner's default.
- Reference script: `answers/36_initialization_ref.py` (script sha256 prefix `82e5eedb25ba5b5f`). The learner's starter, `m6-deep-nets-on-a-mac/scripts/36_initialization.py`, is the same file with the `layer_stds()` body stubbed.
- Runs and wall times in seconds for seeds 0, 1 and 2 (cpu, light lock, up to 4 CPU jobs sharing the Mac, torch on 1 thread): baseline 5.8, 5.7, 5.1; change 7.0, 7.0, 7.2; break 6.5, 7.5, 8.1.
- Tolerance rule (from the .json): tol = spread (max - min) over seeds 0, 1, 2; heavy labs: the baseline spread applies to every step.
- Raw seed-0 output: `answers/36-initialization.out`. Values by seed, spreads and effects: `answers/36-initialization.json`.

<details><summary>P1. log10 of the activation std after layer 10 with N(0, 1) weights, on 512 standardized images (10 ReLU layers of width 100, seed 0)</summary>

**Answer: 8.76175** (log10), tolerance 0.18313999999999986 (the seed spread). Seeds 1 and 2: 8.86868 and 8.68554.

Seed-0 RESULT lines:

```
RESULT baseline.log10_std_by_layer=1.23,2.07,2.93,3.82,4.65,5.37,6.21,7.09,7.92,8.76 unit=log10 seed=0
RESULT P1.log10_std_layer10=8.76175 unit=log10 seed=0
RESULT baseline.train_loss=nan unit=nats seed=0
RESULT baseline.test_acc=0.1 unit=fraction seed=0
```

Other seeds: `baseline.log10_std_by_layer` was `1.23,2.06,2.91,3.81,4.70,5.56,6.35,7.10,7.96,8.87` (seed 1) and `1.23,2.03,2.89,3.76,4.59,5.48,6.35,7.18,7.99,8.69` (seed 2). `baseline.train_loss` was `nan` (NaN) at seeds 0, 1 and 2, spread `nan`, and `baseline.test_acc` was 0.1 at all three (spread 0.0).

Why: a layer with no bias multiplies the mean square of its input by fan_in x var(w), and ReLU keeps half of it, so with N(0, 1) weights layer 1 scales it by 784 / 2 = 392 and each later layer by 100 / 2 = 50. In log10 of the std that is 1.30 for layer 1 and 0.85 for each later layer, 8.94 in all. The std of a ReLU output is about 0.83 of its root mean square, which takes 0.08 off: about 8.86 by the formula. The per-layer list is that straight line in log10, and a straight climb per layer is what an exploding stack looks like in activation statistics.

Spread: at width 100 each layer's real gain wanders a few percent around the formula, and 10 gains multiply.

Training record: the first batch's loss and gradients are astronomically large, one SGD step throws the weights far out, and the second batch overflows float32 to NaN (a tagged debug run at seed 0 saw NaN from the second SGD step on). Every later loss and weight is NaN. An argmax over NaN rows picks class 0, so the test accuracy is the share of class 0 in the test set.

Common wrong predictions: 0, from "N(0, 1) is the standard normal, so the activations stay standard"; or about 10.4, from sqrt(fan_in) per layer with the ReLU's half left out (1.45 + 9 x 1.0).

</details>

<details><summary>P2. The same with Kaiming init, std sqrt(2 / fan_in): log10 of the std after layer 10 (seed 0)</summary>

**Answer: -0.180262** (log10), tolerance 0.18313400000000002. Seeds 1 and 2: -0.073331 and -0.256465.

Seed-0 RESULT lines:

```
RESULT change.log10_std_by_layer=-0.07,-0.07,-0.07,-0.03,-0.05,-0.17,-0.18,-0.15,-0.17,-0.18 unit=log10 seed=0
RESULT P2.log10_std_layer10=-0.180262 unit=log10 seed=0
RESULT change.train_loss=0.402957 unit=nats seed=0
RESULT change.test_acc=0.7862 unit=fraction seed=0
RESULT change.bn_log10_std_by_layer=-0.23,-0.23,-0.23,-0.23,-0.23,-0.24,-0.23,-0.22,-0.23,-0.23 unit=log10 seed=0
RESULT change.bn_log10_std_layer10=-0.226186 unit=log10 seed=0
RESULT change.bn_train_loss=0.428968 unit=nats seed=0
RESULT change.bn_test_acc=0.8536 unit=fraction seed=0
```

Other seeds: `change.log10_std_by_layer` was `-0.07,-0.09,-0.09,-0.03,0.01,0.01,-0.05,-0.14,-0.14,-0.07` and `-0.07,-0.12,-0.11,-0.09,-0.10,-0.07,-0.04,-0.06,-0.10,-0.26`. `change.train_loss` was 0.405192 and 0.406275 (spread 0.0033179999999999876); `change.test_acc` was 0.8429 and 0.8337 (spread 0.05669999999999997).

Why: Kaiming init sets var(w) = 2 / fan_in, so fan_in x var(w) / 2 = 1 in every layer and the mean square stays at the input's 1. The std after each ReLU sits near 0.83 of that, log10 about -0.08 by the formula, and the measured value is within one seed spread of it. The per-layer list wanders around the formula instead of drifting one way, because the gain is 1 only on average.

Same draws: every init draws the same random numbers at a given seed, so P2 minus P1 hardly moves between seeds. The effect in the .json is -8.942009333333333 (spread 0.18313999999999986), log10 of 1 / (sqrt(392) x sqrt(50)^9) to 4 decimals.

Kaiming with BatchNorm (a Record row, no prediction): `change.bn_log10_std_layer10` was -0.226186 at seed 0, -0.223282 and -0.235509 at seeds 1 and 2, spread 0.012226999999999988 against 0.18313400000000002 for plain Kaiming. The per-layer lists were `-0.23,-0.23,-0.23,-0.24,-0.23,-0.23,-0.23,-0.23,-0.23,-0.22` and `-0.24,-0.23,-0.23,-0.22,-0.23,-0.23,-0.23,-0.22,-0.22,-0.24` at seeds 1 and 2. Normalizing each unit to mean 0 and std 1 over the batch makes every layer's output the ReLU of a standard normal, whose std is sqrt(1/2 - 1/(2 pi)) = 0.584, log10 -0.23, whatever the scale of the weights. Both nets learn: `change.bn_train_loss` 0.428968, 0.42931, 0.434361 and `change.bn_test_acc` 0.8536, 0.8552, 0.8584 (spread 0.0048000000000000265). The plain Kaiming net's test accuracy spreads 0.05669999999999997 across seeds while its training loss spreads 0.0033179999999999876: the last SGD step of a 10-layer net without normalization lands at a noisier point.

Common wrong predictions: exactly 0, from "Kaiming keeps the std at 1", which forgets that a ReLU output is not zero-mean, so its std is below its root mean square; or a clearly negative value, from "deep nets shrink anyway".

</details>

<details><summary>P3. Kaiming x 10 and Kaiming x 0.1 (every layer, the head included), each trained 2 epochs: which runs end with a training loss within 0.1 nats of ln 10?</summary>

**Answer: x 0.1** (`P3.near_untrained=x0.1` at seeds 0, 1 and 2). Grading: the pick is right for x 0.1; Brier (1 - c/100)^2 on that pick, (c/100)^2 on any other. `P3.x01_train_loss` was 2.30259 at all three seeds (spread 0.0), ln 10 to 6 digits. `P3.x10_train_loss` was `nan` (NaN) at all three seeds, spread `nan`.

Seed-0 RESULT lines:

```
RESULT break.x10_log10_std_by_layer=0.93,1.93,2.93,3.97,4.95,5.83,6.82,7.85,8.83,9.82 unit=log10 seed=0
RESULT break.x10_log10_std_layer10=9.81974 unit=log10 seed=0
RESULT P3.x10_train_loss=nan unit=nats seed=0
RESULT break.x10_test_acc=0.1 unit=fraction seed=0
RESULT break.x01_log10_std_by_layer=-1.07,-2.07,-3.07,-4.03,-5.05,-6.17,-7.18,-8.15,-9.17,-10.18 unit=log10 seed=0
RESULT break.x01_log10_std_layer10=-10.1803 unit=log10 seed=0
RESULT P3.x01_train_loss=2.30259 unit=nats seed=0
RESULT break.x01_test_acc=0.1231 unit=fraction seed=0
RESULT P3.near_untrained=x0.1 seed=0
```

Other seeds: `break.x10_log10_std_layer10` was 9.92667 and 9.74353; `break.x01_log10_std_layer10` was -10.0733 and -10.2565. `break.x01_test_acc` was 0.0972 and 0.1071; `break.x10_test_acc` was 0.1 at all three.

Why: scaling every weight of a ReLU net without biases by c scales layer l's output by c^l, so x 0.1 makes the logits about 10^-11 of Kaiming's, the softmax uniform and the loss ln 10. Every gradient shrinks the same way, so SGD barely moves a weight and the loss stays at ln 10 for the whole run. At x 10 the first batch's loss and gradients are astronomically large, one SGD step throws the weights far out, and the second batch overflows float32 to NaN. Neither run learns anything, but they fail differently in a training log: a flat ln 10 is a vanishing signal, and a NaN in the first steps is an exploding one.

Evidence: with the same draws, the x 10 and x 0.1 lists are Kaiming's list plus or minus 1 per layer, and the layer-10 effects against Kaiming are 9.999999333333333 (spread 0.18313999999999986) and -10.000014 (spread 0.18320000000000114). In a tagged debug run at seed 0, the largest relative change of any x 0.1 weight matrix over all 1,876 steps was below 10^-9, and both exploding runs were NaN from the second SGD step on. The x 0.1 loss sits 1.897782 above the Kaiming run's (spread 0.0033179999999999876). Its test accuracy sits at chance: the tiny logits still have an order, from the random features of an untrained net.

Common wrong predictions: x 10, from "huge activations saturate the softmax and freeze the loss at chance"; neither, from "SGD will rescale the weights"; both, from "a bad init is a bad init". The x 0.1 run never turns NaN because 10^-10 is still far above the smallest normal float32, about 10^-38.

</details>

<details><summary>Rebuild check</summary>

Solution: `answers/rebuild/36_layer_stds.py`. Stub: `m6-deep-nets-on-a-mac/rebuild/36_layer_stds.py`.

`rebuildcheck` verdict: `stub     fails as it should (exit 1)`, `solution passes (exit 0)`, `REBUILDCHECK OK`.

The stub's `check()` compares with torch on independent library draws. First, `nn.init.kaiming_normal_` on a 1,000 x 1,000 weight within 0.002 (one layer on the identity, so z is the weight itself), then `nn.init.normal_` and 3 times Kaiming within 1%. Then five comparisons with `torch_layer_stds()`, a chain of `nn.Linear` with Kaiming weights times a scale, `nn.BatchNorm1d` in training mode when norm, and ReLU, on 500 rows of 100 inputs into 1,000 units per layer:

| Comparison | Tolerance | Catches |
|---|---|---|
| 1 layer from 100 inputs | 3% | a fan-in read from the wrong axis |
| 3 plain layers at 3 x Kaiming | 25% | a body that never feeds a layer's output into the next, one that reads fan_in from x in every layer, and one that feeds z on instead of relu(z) |
| 3 layers with BatchNorm | 2% | normalizing after the ReLU instead of before it |
| 1 BatchNorm layer on rows scaled from 0.1 to 10 | 5% | normalizing each row over its features (LayerNorm style) instead of each column over the batch |
| 1 BatchNorm layer from 1 input | 3% | normalizing over all values at once (no `dim`) |

A body that returns the std of z instead of relu(z) fails the first identity comparison. The probes behind these tolerances are in the build notes.

</details>

<details><summary>Card drafts</summary>

| ID | Lab | Type | Question |
|---|---|---|---|
| 36-M | 36 | M | Kaiming init sets the weight variance of a ReLU layer to 2 / fan_in. What does the fan_in cancel, and what goes wrong over 10 layers if you drop the 2? |
| 36-N | 36 | N | In lab 36, what was log10 of the activation std after 10 ReLU layers of width 100 with N(0, 1) weights on standardized Fashion-MNIST, and where does that size come from? |
| 36-D | 36 | D | A 10-class classifier logs the same training loss, 2.3026, at every step for 2 epochs, with no NaN. What do you check first, and what does it show if the init is the cause? |

Keys:

- 36-M: (1) each unit sums fan_in products, so a layer multiplies the mean square of its input by fan_in x var(w), and the 1 / fan_in cancels that; (2) the ReLU zeroes the negative half and halves the mean square in every layer, so with 1 / fan_in the signal halves in mean square at each layer and shrinks geometrically with depth (He et al. 2015, section 2.2).
- 36-N: (1) 8.76175 at seed 0, 8.68554 to 8.86868 over seeds 0 to 2; (2) sqrt(392) in layer 1, then sqrt(50) per layer: 1.30 + 9 x 0.85 in log10; (3) the ReLU keeps half the mean square.
- 36-D: (1) the per-layer activation std at init (and the gradient norms); (2) a vanishing init, such as Kaiming x 0.1, shows the std falling 10x per layer and gradients near zero, so the softmax stays uniform at ln 10.

</details>

<details><summary>Build notes</summary>

Knob changes: none. Every effect the lab teaches as real cleared 2x the seed spread on the first full set of runs:

| Effect (A minus B) | Mean over seeds | Spread | Clears 2x spread |
|---|---|---|---|
| `P2.log10_std_layer10` minus `P1.log10_std_layer10` | -8.942009333333333 | 0.18313999999999986 | true |
| `break.x10_log10_std_layer10` minus `P2.log10_std_layer10` | 9.999999333333333 | 0.18313999999999986 | true |
| `break.x01_log10_std_layer10` minus `P2.log10_std_layer10` | -10.000014 | 0.18320000000000114 | true |
| `P3.x01_train_loss` minus `change.train_loss` | 1.897782 | 0.0033179999999999876 | true |

The P3 effect is measured against the Kaiming run, not P1, because the N(0, 1) training loss is NaN. The x 10 loss is NaN too, so it has no numeric effect; its result is the divergence itself. `baseline.train_loss` and `P3.x10_train_loss` are NaN at every seed by the physics of the run, not a missing value. The .json stores each of their seed values, their value and their spread as the string `"nan"`.

Precomputed steps: none. Every seed-0 run took under 1 minute, so the Compute line reads 3 runs x 1 min.

Choices where the spec is silent (the simplest correct option each time):

- Architecture: layer 1 takes the 784 pixels (fan-in 784), layers 2 to 10 are 100 to 100, no biases anywhere, so the init alone sets every scale. Training adds a bias-free linear head from 100 to 10 classes with the same init.
- "Standardized" means one pixel mean and one std from the 60,000 training images, applied to train and test. The 512 images are a seeded random sample of the training set. "The std" is torch's std over all 512 x 100 values after a ReLU.
- Kaiming is the normal, fan-in, ReLU-gain version. The seed is reset before each init, so all inits draw the same random numbers and differ only in scale. The training net starts from the very weights the statistics measured: `make_net()` draws them in the same order and uses `nn.utils.skip_init`, so `nn.Linear` spends no extra random numbers.
- Training: plain SGD without momentum, learning rate 0.05, batch 64, 2 epochs. The training loss is the mean batch loss of epoch 2. Accuracy is on the 10,000 test images in eval mode. Tagged probes at seed 0 with learning rates 0.05 and 0.02 both trained the Kaiming and BatchNorm nets, with similar records; 0.05 was kept.
- "Near an untrained model's loss" (the spec's wording) means within 0.1 nats of ln 10, and the script prints the pick. The lab file asks it as "within 0.1 nats of ln 10, the loss of a uniform guess", because a net with a large init does not start at ln 10. The RESULT name `P3.near_untrained` keeps the spec's word.
- Kaiming with BatchNorm runs in `--change`, after the P2 lines, as a Record row.
- `torch.set_num_threads(1)`: with torch's default of 10 threads on a shared CPU, the BatchNorm net took about 2 minutes to train against about 10 s on one thread, and its BatchNorm records changed in the third decimal with the thread count (reduction order). One thread makes the run fast and the same on any Mac with this torch.
- `--check` feeds torch's own layers (`nn.Linear`, `nn.BatchNorm1d`, `nn.ReLU`) the same random draws as `layer_stds()` and compares the 4 per-layer stds within 1e-4 relative, for five configurations: the four inits, plus Kaiming with BatchNorm. A failure prints the configuration, the number of stds returned and the indices of the layers that differ, never the values. The fixture is a 4-layer miniature of P1 to P3, and `ml-learning/CLAUDE.md` §2 calls `--check` safe at any time, so it may run before the predictions exist. The spec's `nn.init.kaiming_normal_` comparison on a 1,000 x 1,000 weight lives in the rebuild check.
- Rebuild check: the first build dropped a 3-layer plain Kaiming comparison on independent draws, because two independent nets differ by a few percent per layer once gains multiply. It kept one layer at fan-in 100 (3%) and a 3-layer BatchNorm chain (2%). A review then showed that this passed two from-memory slips: a body that never feeds a layer's output into the next, and one that normalizes each row instead of each column. BatchNorm resets the spread at every layer, so the chain cannot see either slip. The fix round added three comparisons at width 1,000. The first is 3 plain layers at 3 x Kaiming at 25%, wide enough for the drift between two independent nets and far below the gap a non-chaining body leaves. The others are 1 BatchNorm layer on rows scaled from 0.1 to 10 (5%) and 1 BatchNorm layer from a single input (3%). The last one catches normalizing over all values at once, which the review did not list and which the old check also passed. The table in the Rebuild check block maps each comparison to the slip it catches.
- Rebuild probes (tagged scratch runs through mlrun, outside the repo): the exact new `check()`, run from 150 starting seeds, passed four correct bodies every time. They used two draw orders, torch's own init functions, and `nn.BatchNorm1d` inside the body. Every relative comparison stayed under half of its tolerance. Seven slips failed at all 30 seeds tried, each at the comparison in the table: no chaining, row normalization, fan_in read from x, normalization over all values, normalizing after the ReLU, z fed on instead of relu(z), and the std of z. The two slips the review named missed by at least 2.6x (no chaining) and 2.1x (row normalization) their tolerance, and normalization over all values missed by at least 2.3x.
- TODO length: the `layer_stds()` body is 10 lines, 19 with its signature and docstring. The fading plan asks for 12 to 20 lines and the spec estimates 15. This is deliberate: the 0:12 slot also holds `--check` and the baseline run, and a longer body would add lines, not concept. The rebuild asks for the same 10 lines.
- The .json is strict JSON. The first build wrote `baseline.train_loss`, `P3.x10_train_loss` and their spreads as bare NaN tokens (Python's json default), which JavaScript's JSON.parse rejects. A later independent review rated this major, so the fix went into the shared mkanswers tool. It now writes a non-finite float as the string Python prints for it (`"nan"`, `"inf"` or `"-inf"`), and `allow_nan=False` guards the write. Values, spreads and effects are computed as before; only the encoding changed. Every other lab's .json encodes to the same bytes under the new tool, so this is the only file that changed. No script changed, so no run was repeated: mkanswers was rerun, and all 9 runs are current.
- Fix round (after review): the `--check` failure message no longer prints the per-layer lists, the docstring says four inits and Kaiming with BatchNorm, the starter was regenerated with make_c_starter, and all 9 reference runs were rerun. Every RESULT value, spread and effect matched the first set digit for digit. Only the wall times and the script hash changed. The lab file now names the bias-free head and its scale, and splits the P3 question. The Goal no longer says "which of the runs learn anything". The change step has a one-sentence Why, with the BatchNorm run as a Record-only line below its command. The lab file also expands std, ReLU and BatchNorm at first use. The interview question stays as the spec writes it, since the module README's lab table carries the same text.
- The GitHub gz fallback reader returns the same arrays as the parquet reader (both splits, full and the 2,000-row smoke limit), checked once in the build.
- The reference script is 150 lines, with single blank lines between functions to stay at the cap.

Prototype comparison (the spec's [answers only] note): the layer-10 std was 2.3e8 for N(0, 1), 0.73 for Kaiming, 1.0e10 for x 10 and 6.6e-11 for x 0.1, which in log10 is 8.36, -0.14, 10.0 and -10.18. This build measured 8.76175, -0.180262, 9.81974 and -10.1803 at seed 0. Kaiming, x 10 and x 0.1 agree within one seed spread (about 0.18 in log10). N(0, 1) is about 0.40 higher, more than 2x the spread. Cause: the prototype's 10 layers all had fan-in 100. Its own N(0, 1) over Kaiming ratio, 2.3e8 / 0.73, is 10^8.50, which is sqrt(50)^10 (10^8.49). Here layer 1 takes the 784 pixels, so its N(0, 1) gain is sqrt(392) instead of sqrt(50), an extra 0.447 in log10, and this build's P2 minus P1 effect, -8.942009333333333, is log10 of 1 / (sqrt(392) x sqrt(50)^9). The direction of every step matches the prototype. This is a different first layer, not a bug: the spec's "10 ReLU layers of width 100 on 512 standardized images" is read here as layer 1 = 784 to 100.

</details>
