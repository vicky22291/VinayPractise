# 29. Softmax and cross-entropy: from 2 digits to 10: reference answers

> Spoilers. The AI opens one block at a time, only after that step's prediction row exists and the learner pasted their own RESULT lines, or after 'debrief 29'.

- HW: `HW chip='Apple M4 Pro' cpu=14 gpu=20 mem_gib=24 macos=26.5.1 python=3.13.7 torch=2.14.1 device=cpu`
- Seeds: 0, 1 and 2 for baseline, change and break (light lane). The same seed gives the same init and the same batch order in all three modes, so each delta is paired.
- Reference script: `answers/29_softmax_and_cross_entropy_ref.py` (sha256 prefix `c2fbca7ccc30b820`). The starter `m5-under-the-hood/scripts/29_softmax_and_cross_entropy.py` comes from `make_c_starter`.
- Runs, wall time at seeds 0 / 1 / 2, light lock: baseline 4.3 / 4.4 / 5.3 s, change 3.2 / 2.3 / 2.0 s, break 2.3 / 2.4 / 2.4 s. Seed-0 logs: `29-softmax-and-cross-entropy.out`. Values by seed: `29-softmax-and-cross-entropy.json`.
- Tolerance rule: tol = spread (max - min) over seeds 0, 1, 2; heavy labs: the baseline spread applies to every step.

<details><summary>P1. Cross-entropy loss on the first batch of 64 training images, before any update (linear 784-to-10, init std 0.01, zero bias, seed 0)</summary>

**Answer:** 2.3101 nats at seed 0, tolerance ±0.01977 (the seed spread). That is ln 10 = 2.303 plus a little.

```
RESULT P1.first_batch_loss=2.3101 unit=nats seed=0
RESULT baseline.test_accuracy=0.909 unit=fraction seed=0
RESULT baseline.min_batch_loss=0.174214 unit=nats seed=0
```

Other seeds: first-batch loss 2.2951 (seed 1) and 2.31487 (seed 2). Test accuracy 0.9088 and 0.9095 (spread 0.0007). Lowest batch loss 0.116976 and 0.161438 (spread 0.057238).

**Why:** weights near zero make every logit near zero, so softmax gives each of the 10 digits about 1/10, and the loss is minus the log of 1/10: ln 10 = 2.303. With std 0.01 over 784 pixels in [0, 1], the logits spread by about 0.094, which adds only about 0.004 on average; the rest of the gap between seeds is the random weights meeting the 64 images that land in the first batch. The class count alone sets the number: 2 classes start at ln 2 = 0.693, 1,000 classes at 6.91.

**Common wrong prediction:** 0 ("nothing is learned yet, so no loss"), 0.9 or 1 (an error rate, not a log loss), or about 0.69 carried over from a 2-class model. A first-batch loss far from ln(number of classes) means a bug or a bad init, so check it before you train.
</details>

<details><summary>P2. MSE between the softmax probabilities and one-hot targets instead of cross-entropy: test accuracy after 1 epoch, direction and size</summary>

**Answer:** down, by about 10 points. The graded line is `P2.accuracy_delta`, MSE minus cross-entropy as a fraction: -0.1056 at seed 0 (tolerance ±0.0129). MSE reaches 0.8034 test accuracy at seed 0 (tolerance ±0.0136) against 0.909 for cross-entropy. Mean effect over the 3 seeds: -0.10523, against a spread of 0.0136, so above 2x the spread.

```
RESULT P2.test_accuracy=0.8034 unit=fraction seed=0
RESULT P2.accuracy_delta=-0.1056 unit=fraction seed=0
RESULT change.min_batch_loss=0.0337847 unit=mse seed=0
```

Other seeds: accuracy 0.7973 (seed 1) and 0.8109 (seed 2). Delta -0.1115 and -0.0986. Lowest batch MSE 0.0333402 and 0.0333637 (MSE units, not comparable with the nats of the other two runs).

**Why:** the MSE gradient reaches the logits through the slope of the softmax, so it is small: at init (p = 0.1 for every digit) the push on the right digit's logit is 0.018 per image against 0.9 for cross-entropy, 50 times smaller. That is a factor of 10 from `F.mse_loss` averaging over the 10 outputs, and a factor of 5 from the softmax slope (p = 0.1) times the 2 that the square brings down. Worse, MSE gives almost no gradient to a confidently wrong image, exactly where cross-entropy pushes hardest: with the right digit's logit at -5, one wrong digit at +5 and the other eight at 0, the right digit gets p = 0.00004, and the push on its logit is about 0.000016 from MSE against about 1.0 from cross-entropy. The model and its 938 batches are the same in both runs, so only the loss changed, and its gradient changes both the size of each step and which images drive it: after 1 epoch the MSE model is still far behind.

**Common wrong prediction:** "about the same, since both losses are lowest at the right answer", or a drop of 1 or 2 points. The best point is the same; the road to it is not.
</details>

<details><summary>P3. Softmax applied before nn.CrossEntropyLoss (a double softmax): test accuracy after 1 epoch, and the floor under its loss (the greatest lower bound)</summary>

**Answer:** two rows in the prediction log, each graded on its own.

- `P3.test_accuracy`: 0.8216 at seed 0 (tolerance ±0.0014), about 9 points below cross-entropy (mean effect -0.08743 over the 3 seeds, spread 0.0014).
- `P3.lowest_possible_loss`: 1.46115 nats, the same at every seed (spread 0, so a hit needs the 80% range to contain it). The exact floor is -ln(e / (e + 9)). It is an infimum, not a minimum: the loss approaches it as the first softmax output approaches one-hot, and finite logits never reach it. The printed value is the float32 loss at the end of the script's search, a finite-precision estimate that equals the bound to float32 precision.

The lowest batch loss seen in the epoch was 1.6227 at seed 0 (tolerance ±0.03346), against 0.174214 for cross-entropy (mean effect +1.45641, spread 0.057238).

```
RESULT P3.test_accuracy=0.8216 unit=fraction seed=0
RESULT P3.lowest_possible_loss=1.46115 unit=nats seed=0
RESULT break.min_batch_loss=1.6227 unit=nats seed=0
```

Other seeds: accuracy 0.8224 (seed 1) and 0.821 (seed 2). Lowest batch loss 1.58924 and 1.60993.

**Why:** `nn.CrossEntropyLoss` applies log-softmax itself, so it reads the probabilities as if they were logits. Probabilities sit in [0, 1], so the right digit can lead the others by less than 1. The bound is the limit where the first softmax output reaches [1, 0, ..., 0]: the second softmax would then give the right digit e / (e + 9) = 0.232, a loss of 1.461, never 0. Finite logits never make the first softmax exactly one-hot, so in exact arithmetic the loss stays strictly above 1.461 and only approaches it. The script's search runs in float32: once the right logit leads by enough, its probability rounds to 1.0 and the others are too small to move the second softmax, so the printed value lands on the bound. That is a numerical estimate, not the proof; the proof is the limit above. The gradient also passes through two softmaxes: at init it is 0.09 on the right logit against 0.9 for cross-entropy, and it fades further as the first softmax saturates. Accuracy still climbs, because softmax keeps the order of the scores and the argmax does not change; it just climbs more slowly.

**Common wrong prediction:** accuracy at chance (0.1), because "the loss is wrong"; no change at all, because "softmax is monotonic"; or a floor of 0. The symptom to remember: a training loss that flattens well above 0 while accuracy keeps creeping up.
</details>

<details><summary>Rebuild check</summary>

Solution: `answers/rebuild/29_softmax_cross_entropy.py` (the stub is `m5-under-the-hood/rebuild/29_softmax_cross_entropy.py`). `rebuildcheck`: the stub fails as it should (exit 1, NotImplementedError), the solution passes (exit 0, `check: PASS`), verdict `REBUILDCHECK OK`. A version without the row maximum fails `check()` on the rows shifted by 1,000 ("softmax differs from torch.softmax").
</details>

<details><summary>Card drafts</summary>

Three cards go to the bank: 29-M, 29-N, and 29-T or 29-D, whichever type is due at this close (T and D alternate from one close to the next).

| ID | Lab | Type | Question |
|---|---|---|---|
| 29-M | 29 | M | Why can a model with a softmax placed before `nn.CrossEntropyLoss` never reach a loss of 0, even when every prediction is right? |
| 29-N | 29 | N | A 10-class linear classifier starts with weights near zero. What cross-entropy do you expect on its first batch, and why that number? |
| 29-T | 29 | T | A fraud model scores each payment with 2 logits, softmax and cross-entropy, and 1% of payments are fraud. With weights near zero and zero bias, what loss does its first batch show, and what output bias would make it start at the 1% base rate instead? |
| 29-D | 29 | D | In its first epoch, a 10-class classifier's lowest batch loss is about 1.6 nats, far above 0, while its accuracy keeps creeping up. What do you check first? |

Keys (must mention):

- 29-M: (1) `nn.CrossEntropyLoss` applies log-softmax itself, so it treats the probabilities as logits; (2) probabilities sit in [0, 1], so the right class leads by at most 1; (3) for 10 classes the right class's probability approaches e / (e + 9) = 0.232 as the first softmax nears one-hot, so the loss approaches a floor of 1.461 nats that finite logits never reach.
- 29-N: (1) about ln 10 = 2.303 nats (reference run: 2.3101 at seed 0); (2) near-zero logits make softmax uniform, 1/10 per class, and the loss is -ln(1/10); (3) a first-batch loss far from ln(number of classes) means a bug or a bad init.
- 29-T: (1) ln 2 = 0.693 nats whatever the fraud rate, because near-zero logits give each class p = 0.5; (2) set the fraud bias minus the legit bias (or a sigmoid model's single bias) to the log-odds ln(0.01 / 0.99) = -4.6, so every payment starts at p = 0.01; (3) the first loss then sits near the base-rate entropy, -0.01 ln 0.01 - 0.99 ln 0.99 = 0.056 nats, so the first steps are not spent learning the bias. Sources: Karpathy, "A Recipe for Training Neural Networks" (2019, https://karpathy.github.io/2019/04/25/recipe/), the "verify loss @ init" and "init well" tips; makemore part 3 on the loss at initialization.
- 29-D: (1) a softmax already applied before `nn.CrossEntropyLoss`, a double softmax; (2) its floor is 1.461 nats for 10 classes, so no amount of training gets below it; the reference run's lowest batch loss after 1 epoch was 1.6227; (3) the fix: return raw logits and let the loss apply log-softmax.
</details>

<details><summary>Build notes</summary>

- **Knob changes:** none. The spec's configuration ran as written (linear 784-to-10, init std 0.01, zero bias, batch 64, SGD lr 0.1, 1 epoch). Every effect the lab teaches cleared 2x the seed spread on the first try: P2 accuracy -0.10523 against a spread of 0.0136, P3 accuracy -0.08743 against 0.0014, and the double softmax's lowest batch loss +1.45641 against 0.057238.
- **Precomputed steps:** none. Seed-0 wall times are 4.3 s (baseline), 3.2 s (change) and 2.3 s (break), so the lab file says 3 runs x 1 min.
- **Where the spec is silent (the simplest correct option):**
  - MSE is `F.mse_loss(softmax(logits), one_hot)` with the default mean over all 640 entries of a batch. "MSE on one-hot targets" could also mean regressing the raw logits onto one-hot targets. Using the softmax probabilities keeps the model and its outputs fixed, so only the loss changes, and it is the version whose mechanism (the softmax slope) the concept names. It matches the prototype.
  - Pixels are scaled to [0, 1] with no mean and std normalization; the bias starts at zero; `nn.Linear` is re-initialized with `normal_(std=0.01)`.
  - The baseline trains with the learner's `cross_entropy()`, so the TODO is written before the baseline and `--check` gates it. The break uses `nn.CrossEntropyLoss`, as the spec says.
  - The TODO is `cross_entropy()` alone, because the spec says "TODO(human): cross_entropy()". Its body is 3 lines; the signature and docstring bring the function to 11, one under the fading plan's 12 to 20 for a concept piece. The rebuild piece is larger (`softmax()` plus `cross_entropy()`, 18 lines), because the spec sets the TODO and the rebuild separately. The docstring states the rule (minus the log of the softmax probability of the right class, logsumexp with the row maximum subtracted) but not the formula, so the learner derives it. `softmax()` is written from memory only in the rebuild.
  - P3's "lowest loss it can ever reach" (the spec's wording) prints as `P3.lowest_possible_loss`. A review pointed out that the floor is an infimum, not a loss finite logits attain: the first softmax is never exactly one-hot, so in exact arithmetic the loss stays strictly above -ln(e / (e + 9)). The lab file's P3 row therefore asks for the floor (the greatest lower bound) and says the RESULT is a float32 estimate of it. The RESULT name and the script stay unchanged, so no rerun was needed. The RESULT is the double-softmax loss after 100 Adam steps (learning rate 1.0) on a free 10 x 10 logit tensor, one row per digit, started at zero. The search is deterministic, so every seed prints the same value. An inspection run of the same search, in float32 like the script, matches the exact -ln(e / (e + 9)) to float32 precision within 25 steps. An earlier version built the best-case input by hand (a logit of 100 on the right class, with a comment saying so). Review moved it to the search, because those lines in the starter showed the floor's derivation before P3 is logged. The Record row "the lowest batch loss of each run" prints as `<mode>.min_batch_loss`.
  - P3 asks for two numbers, so the lab file has two P3 rows and tells the learner to log two rows in `prediction-log.md`, one per RESULT name, each with its own range. One row holding two numbers would leave Off by undefined.
  - `P2.accuracy_delta` reads `baseline.test_accuracy` through `labkit.prior()`, so it needs the baseline at the same seed first. The lab file's P2 row says the graded size is this delta, as a fraction.
  - `--check`: 20 rows x 10 classes in float64, 5 rows shifted by 1,000 and one logit of 1,000. It compares the value and the gradient with `F.cross_entropy` within 1e-6. A naive exp version returns a non-finite loss on this fixture.
  - Repo link: the spec lists none. The lab uses `hld/payments-risk-decisioning/deep-dives/model-lifecycle-shadow-and-labels.md` §4, whose "Calibrate first" bullet says the cost threshold assumes p is a probability. The Staff follow-up is a trade-off (trust the cross-entropy score as a probability, or recalibrate it monthly), so it does not repeat lab 28's failure-modes probe.
  - Download: torchvision first (the ossci-datasets mirror, then yann.lecun.com), then the Hugging Face parquet files with exact sizes. The first fallback test ran on an earlier version of the script, so it was repeated on the final scripts (reference `c2fbca7ccc30b820`, starter `e969d244170efdb6`) with tagged runs of a build-only harness. The harness runs the script unchanged, points `ML_DATA` at a throwaway folder (deleted afterwards) and makes torchvision's download raise. `--download` and `--smoke` passed for both scripts through the parquet branch, and the decoded 70,000 images and labels are identical to the torchvision tensors, in the same order.
  - Card types: M, N, and both a T and a D draft, because T and D alternate from one close to the next. D fits because the break is a debugging symptom (a loss stuck well above 0). T is the payments version: a 2-class fraud model's loss at init and the bias that starts it at the base rate.
- **Deviations from the spec wording:** the spec's interview question ("What should a classifier's loss be before any training, and why do we not train classifiers with MSE?") and its goal ("explain why a double softmax stalls") each state a direction the learner is asked to predict in P2 and P3. The lab file asks the question neutrally and says "explain what a double softmax does to training". The spec's wording is the right frame for the soundbite after the lab. The spec's rebuild says "12 to 15 lines"; the two bodies take 6, so the lab file and the rebuild stub say "a few lines each", and a correct short answer does not look unfinished.
- **Prototype comparison** (spec value against seed 0, with 2x the seed spread):
  - first batch 2.331 against 2.3101: gap 0.0209, 2x spread 0.03954. Both sit near ln 10 = 2.303.
  - cross-entropy accuracy 0.908 against 0.909: gap 0.001, 2x spread 0.0014.
  - MSE accuracy 0.791 against 0.8034: gap 0.0124, 2x spread 0.0272. Same direction.
  - double softmax accuracy 0.820 against 0.8216: gap 0.0016, 2x spread 0.0028.
  - double softmax lowest batch loss 1.614 against 1.6227: gap 0.0087, 2x spread 0.06692.
  - floor -ln(e / (e + 9)) = 1.461 against 1.46115: equal.
  - Every direction agrees and every gap is under 2x the spread, so nothing points at a bug.
</details>
