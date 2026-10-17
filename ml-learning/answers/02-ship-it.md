# 02. Ship it: a model is a service with a size, a p95 and inputs it has never seen: reference answers

> Spoilers. The AI opens one block at a time, only after that step's prediction row exists and the learner pasted their own RESULT lines, or after 'debrief 02'.

- HW (hardware) line: `HW chip='Apple M4 Pro' cpu=14 gpu=20 mem_gib=24 macos=26.5.1 python=3.13.7 torch=2.14.1 device=cpu`
- Seeds: 0, 1 and 2 for every step (light lane). In this lab `--seed S` changes one random choice: which 4 photos per non-pet class the break draws (`random.Random(S)`; the three seeds drew 60 different photos). The model (lab 01's seed-0 export) and the 200 pet photos are fixed, so the baseline and change seeds are repeat runs: their spread is run-to-run timing noise, and accuracy has no spread at all.
- Reference script: `ml-learning/m1-whole-game/scripts/02_ship_it.py` (level W: the learner's script is the reference), sha256 prefix `53d96ac69929a127`. Values: [`02-ship-it.json`](02-ship-it.json). Seed-0 logs: [`02-ship-it.out`](02-ship-it.out).
- Precomputed steps: none.
- Tolerance rule: tol = spread (max - min) over seeds 0, 1, 2; heavy labs: the baseline spread applies to every step.
- Timing conditions for every latency below: M4 Pro, cpu, `torch.set_num_threads(1)`, batch 1 (one photo per call), 10 warm-up calls, then 200 timed calls of `learn.predict` on one JPEG file's bytes each, `time.perf_counter_ns` around the whole call, percentiles by nearest rank (p50 is the 100th of the 200 sorted timings, p95 the 190th). Each measured run held the build's exclusive lock, so no other build job ran beside it. Processes outside the build kept running (a document pipeline held one core near 100%, plus desktop apps), and the DATA lines show a 1-minute load average from 5.4 to 7.7 on the 14-core Mac. Two earlier reference sets (outside load not recorded for the first, a load average up to 17.9 for the second, and a lab 37 download job running beside both) had spreads of 13.4733 and 7.0174 ms on the P2 latency effect against 1.4672 ms here, and are not used (Build notes).

Runs and wall times in seconds (each includes Python start-up, imports and loading the model):

| Mode | Seed 0 | Seed 1 | Seed 2 |
|---|---|---|---|
| baseline | 12.8 | 12.6 | 12.6 |
| change | 11.5 | 11.7 | 11.1 |
| break | 8.0 | 8.1 | 7.6 |

<details><summary>P1. p95 latency in ms of one learn.predict call on one CPU thread after 10 warm-up calls: lab 01's resnet34 at 224 px, 200 timed calls on the 200 held-out pet photos, seed 0</summary>

**Answer: 24.7684 ms**, tolerance plus or minus 1.3196 ms (the seed spread). Seeds 1 and 2: 25.9139 and 26.088 ms.

Seed-0 RESULT lines:

```
DATA requests=200 input=1x3x224x224 threads=1 warmup=10 load1=5.4
RESULT P1.p95_ms=24.7684 unit=ms device=cpu batch=1 warmup=10 n=200 threads=1 stat=p95 seed=0
RESULT baseline.p50_ms=23.3536 unit=ms device=cpu batch=1 warmup=10 n=200 threads=1 stat=p50 seed=0
RESULT baseline.max_ms=108.445 unit=ms device=cpu batch=1 warmup=10 n=200 threads=1 stat=max seed=0
RESULT baseline.accuracy=0.88 unit=fraction px=224 n=200 seed=0
RESULT baseline.pet_share_above_0_9=0.62 unit=fraction n=200 threshold=0.9 seed=0
RESULT baseline.export_mb=87.6373 unit=MB seed=0
RESULT baseline.params=21830976 unit=params seed=0
```

| Value | Seed 0 | Seed 1 | Seed 2 | Spread |
|---|---|---|---|---|
| `P1.p95_ms` | 24.7684 | 25.9139 | 26.088 | 1.3196 |
| `baseline.p50_ms` | 23.3536 | 23.8602 | 23.9682 | 0.6146 |
| `baseline.max_ms` | 108.445 | 116.7 | 114.196 | 8.255 |
| `baseline.accuracy` | 0.88 | 0.88 | 0.88 | 0 |
| `baseline.pet_share_above_0_9` | 0.62 | 0.62 | 0.62 | 0 |
| `baseline.export_mb` | 87.6373 | 87.6373 | 87.6373 | 0 |
| `baseline.params` | 21830976 | 21830976 | 21830976 | 0 |

**Why:** every call does a fixed part (decode the JPEG, resize it to lab 01's 448 px square, and `learn.predict`'s own machinery: a one-item DataLoader per call, the transform pipeline, the callbacks, decoding the answer) and a part that grows with the pixels, the resnet34 forward pass: about 3.6 billion multiply-adds at 224 px (He et al. 2016). At batch 1, PyTorch runs the convolutions as matrix multiplies in Apple's Accelerate library (`BLAS_INFO=accelerate` in this build, oneDNN off), and with PyTorch's thread pool set to one thread the whole call takes tens of milliseconds. p95 sits only 1.41 ms above p50 at seed 0 because nearly every call does the same work. The candidates for the tail, bigger JPEGs (slower to decode), other processes taking the core and garbage collection passes, were not separated.

Max: every timed run in this set had a call above 100 ms (108.445 ms at seed 0, 4.6 times p50), yet p95 stayed close to p50: p95 is the 190th of 200 sorted calls, so it ignores the 10 slowest. The cause of those stalls was not separated (Build notes).

Size: `export.pkl` is 87.6373 MB for 21,830,976 parameters. At 4 bytes per 32-bit weight that is 87.32 MB; the other 0.31 MB hold what is not a parameter: BatchNorm running statistics, the pickled preprocessing and the class names (not broken down further).

Common wrong prediction: hundreds of milliseconds (one CPU core sounds slow for a 21.8 million parameter network), or a few milliseconds (counting only the multiply-adds, or recalling GPU numbers). A second one: predicting the mean, or p50, when the question asks for p95.

</details>

<details><summary>P2. The same model, photos and harness with 160 px inputs instead of 224 px, seed 0: p95 and accuracy, direction and size</summary>

**Answer: p95 down, ratio 0.844575 at seed 0** (`P2.p95_ms` 20.9188 ms against P1 24.7684 ms), and **accuracy down, `P2.accuracy_delta_vs_224` = -4.5 points** (0.835 against 0.88, that is 167 against 176 of the 200 photos right).

- Latency, tolerance plus or minus 1.4672 ms on `P2.p95_ms` (the larger of the P1 and P2 spreads) and plus or minus 0.066231 on the ratio. The per-seed differences P2 minus P1 are -3.8496, -4.1413 and -5.7826 ms, mean -4.59117 ms: down at every seed, and more than twice the spread (2.9344 ms), so the effect passes the 2x rule (`ok: true` in the .json). The ratio by seed: 0.844575, 0.840192 and 0.778344.
- Accuracy, tolerance 0: the same weights on the same 200 photos give the same answers every run, so the delta is exactly -4.5 points at every seed (effect -0.045, `ok: true`).

Seed-0 RESULT lines:

```
DATA requests=200 input=1x3x160x160 threads=1 warmup=10 load1=5.4
RESULT P2.p95_ms=20.9188 unit=ms device=cpu batch=1 warmup=10 n=200 threads=1 stat=p95 seed=0
RESULT change.p50_ms=19.4555 unit=ms device=cpu batch=1 warmup=10 n=200 threads=1 stat=p50 seed=0
RESULT change.max_ms=108.279 unit=ms device=cpu batch=1 warmup=10 n=200 threads=1 stat=max seed=0
RESULT P2.accuracy=0.835 unit=fraction px=160 n=200 seed=0
RESULT P2.p95_ratio_vs_224=0.844575 unit=ratio seed=0
RESULT P2.accuracy_delta_vs_224=-4.5 unit=points seed=0
```

| Value | Seed 0 | Seed 1 | Seed 2 | Spread |
|---|---|---|---|---|
| `P2.p95_ms` | 20.9188 | 21.7726 | 20.3054 | 1.4672 |
| `change.p50_ms` | 19.4555 | 19.6242 | 19.1653 | 0.4589 |
| `change.max_ms` | 108.279 | 105.651 | 102.311 | 5.968 |
| `P2.accuracy` | 0.835 | 0.835 | 0.835 | 0 |
| `P2.p95_ratio_vs_224` | 0.844575 | 0.840192 | 0.778344 | 0.066231 |
| `P2.accuracy_delta_vs_224` | -4.5 | -4.5 | -4.5 | 0 |

**Why:** 160 px has 49% fewer pixels than 224 px (1 minus (160/224) squared) and the convolution work scales with pixels, but the decode, the 448 px resize and `learn.predict`'s machinery cost the same at both sizes (the change swaps only the last resize, and even adds one area-downsampling step, 448 to 320 px, before it). The p50s split the call: their mean over the three seeds falls from 23.73 ms to 19.41 ms, so the part that scales is about 8.8 ms (4.31 / 0.49) and the fixed part about 63% of a 224 px call, which is why the p95 ratio is nowhere near 0.51. Accuracy drops because lab 01 trained the network on 224 px crops: at 160 px each cat covers fewer pixels, so the face and fur detail that separate these 6 cat breeds reach the filters smaller and blurrier than in training. Adaptive pooling lets the network run at any input size; it does not make it equally accurate at every size.

Common wrong prediction: p95 halves with the pixel count (it ignores the fixed per-call cost), and accuracy stays the same because the network "accepts any size".

</details>

<details><summary>P3. Back at 224 px: share of the 20 non-pet photos (4 each of church, parachute, golf ball, gas pump, garbage truck, drawn with seed 0) whose top breed probability is above 0.9</summary>

**Answer: 0** (0 of 20), tolerance plus or minus 0 (the seed spread): seeds 1 and 2 also gave 0, so none of the 60 different non-pet photos went above 0.9. The most confident non-pet answer was 0.623649 at seed 0 (0.541302 and 0.617037 at seeds 1 and 2).

Seed-0 lines:

```
DATA requests=20 input=1x3x224x224 threads=1 warmup=10 load1=6.7
NONPET class=church file=n03028079_28352.JPEG breed=american_pit_bull_terrier top_prob=0.0914
NONPET class=church file=n03028079_901.JPEG breed=samoyed top_prob=0.1932
NONPET class=church file=n03028079_29920.JPEG breed=basset_hound top_prob=0.1039
NONPET class=church file=n03028079_1002.JPEG breed=basset_hound top_prob=0.1409
NONPET class=parachute file=n03888257_20572.JPEG breed=Bombay top_prob=0.6236
NONPET class=parachute file=n03888257_38501.JPEG breed=Ragdoll top_prob=0.2014
NONPET class=parachute file=n03888257_3651.JPEG breed=basset_hound top_prob=0.1575
NONPET class=parachute file=n03888257_31742.JPEG breed=miniature_pinscher top_prob=0.2302
NONPET class=golf_ball file=n03445777_2362.JPEG breed=german_shorthaired top_prob=0.5505
NONPET class=golf_ball file=n03445777_501.JPEG breed=Bombay top_prob=0.3450
NONPET class=golf_ball file=n03445777_3321.JPEG breed=Bombay top_prob=0.2697
NONPET class=golf_ball file=n03445777_6421.JPEG breed=Bombay top_prob=0.2229
NONPET class=gas_pump file=n03425413_14552.JPEG breed=german_shorthaired top_prob=0.2740
NONPET class=gas_pump file=n03425413_20562.JPEG breed=Maine_Coon top_prob=0.1542
NONPET class=gas_pump file=n03425413_1342.JPEG breed=miniature_pinscher top_prob=0.2584
NONPET class=gas_pump file=n03425413_15321.JPEG breed=pug top_prob=0.2473
NONPET class=garbage_truck file=n03417042_1330.JPEG breed=pug top_prob=0.2395
NONPET class=garbage_truck file=n03417042_9620.JPEG breed=Bengal top_prob=0.4265
NONPET class=garbage_truck file=n03417042_12002.JPEG breed=pug top_prob=0.1788
NONPET class=garbage_truck file=n03417042_6662.JPEG breed=pug top_prob=0.2885
RESULT P3.share_above_0_9=0 unit=fraction n=20 threshold=0.9 seed=0
RESULT break.max_top_prob=0.623649 unit=probability n=20 seed=0
```

| Value | Seed 0 | Seed 1 | Seed 2 | Spread |
|---|---|---|---|---|
| `P3.share_above_0_9` | 0 | 0 | 0 | 0 |
| `break.max_top_prob` | 0.623649 | 0.541302 | 0.617037 | 0.082347 |

Breeds given to the 20 seed-0 non-pets: Bombay 4, pug 4, basset_hound 3, miniature_pinscher 2, german_shorthaired 2, american_pit_bull_terrier 1, samoyed 1, Ragdoll 1, Maine_Coon 1, Bengal 1. Their top probabilities run from 0.0914 to 0.6236.

**Why:** softmax turns the 37 scores into 37 probabilities that sum to 1, so every photo still got a breed: "none of these" is not an answer the model can give. On these photos no breed fit much better than the rest, so the scores came out close and the probability was split between breeds instead of piled on one (the maximum-softmax baseline of Hendrycks and Gimpel 2017, working on inputs far from pets). The 0.9 guard therefore refused all 60 non-pets, but it also refuses 38% of the real pets (`baseline.pet_share_above_0_9` = 0.62): safety bought with coverage (effect against the pets' share -0.62, `ok: true`). It does not make the model safe, and this sample cannot say how safe it is.

**What this sample did not establish.** The spec frames this step as "a softmax that is confidently wrong on out-of-distribution inputs". This lab did not show that, and it did not show the opposite. The 0 of 60 speaks only for photos like these: far from any pet, from 5 Imagenette classes, and enlarged from 160 px to 448 px (a blur that may lower confidence by itself, not tested). Even for them it is a loose bound: with 0 of 60 above 0.9, the true share could still be as high as about 5% (the rule of three: 3 / 60 is a one-sided 95% upper bound). How often this model is confidently wrong on other unfamiliar inputs, such as a dog breed outside the 37 or a cat drawing, was not measured. That stays an open question to test on held-out data before any threshold ships. It is not a lesson of this lab.

Common wrong prediction: a high share, primed by the interview question's 0.97. The opposite mistake matters more: reading 0 of 20 as "the model knows when it does not know".

</details>

<details><summary>Rebuild check</summary>

- Solution: `ml-learning/answers/rebuild/02_latency_harness.py`. Stub: `ml-learning/m1-whole-game/rebuild/02_latency_harness.py`.
- `rebuildcheck`: stub fails as it should (exit 1, NotImplementedError); solution passes (exit 0, `check: PASS`); REBUILDCHECK OK.
- `check()` compares `percentile` with `numpy.percentile(method="inverted_cdf")` at p50, p95 and p99 for 1, 7, 20, 199, 200 and 1,001 values. It runs `latency_report` on a fake model whose first call sleeps 200 ms (a cold start) and whose input 7 always sleeps 20 ms, and requires: the warm-up calls made first, the outputs in input order, p50 under 10 ms, and a max of at least 20 ms but under 150 ms (so the warm-up is left out). It compares `confident_share` with numpy on 500 random probability rows, plus one row exactly at 0.9, which must not count.
- Mutation tests: six broken versions all fail `check()`: numpy's default linear percentile, `round` instead of `ceil`, no warm-up, warm-up calls timed, seconds instead of milliseconds, and `>=` instead of `>`.
- The bodies are the same lines as `percentile`, `latency_report` and `confident_share` in the lab script; only the defaults differ (the script takes them from its WARMUP and THRESHOLD constants). The stub's docstrings equal the solution's.

</details>

<details><summary>Card drafts</summary>

| ID | Lab | Type | Question |
|---|---|---|---|
| 02-M | 02 | M | A 37-breed softmax classifier is shown a photo of a church. Why can it not answer "none of these", and what does its top probability measure instead? |
| 02-N | 02 | N | On one CPU thread of the M4 Pro, about how many ms did one `learn.predict` call of lab 01's resnet34 take at p95 at 224 px, and why did 160 px inputs (about half the pixels) cut it by much less than half? |
| 02-T | 02 | T | A payments fraud model gives a 0.97 score to a transaction from a merchant category it never saw in training. What does the 0.97 tell you, and what do you do with the decision? |

Keys:

- 02-M: (1) softmax makes the 37 probabilities sum to 1, so all of the probability goes to some breed (in lab 02 all 60 non-pets got one); (2) the top probability says how far one breed beat the other 36 on this input, not whether the input looks like the training data; (3) "not a pet" needs its own signal: a reject class trained on non-pets, an out-of-distribution detector tested on held-out unfamiliar inputs, or monitoring of the inputs.
- 02-N: (1) the number: P1 at seed 0 is 24.7684 ms, tolerance plus or minus 1.3196 ms (the seed spread), so accept 23.4 to 26.1 ms; (2) the reason: a fixed per-call cost (JPEG decode, the 448 px resize, `learn.predict`'s per-call DataLoader and decoding) does not shrink with input size, and only the convolution work, about 37% of a call here, scales with the pixels.
- 02-T: (1) the score measures fit among the outcomes the model knows, not familiarity with the input (lab 02: a 37-breed model named a breed for every church and golf ball); (2) guard outside the model: flag unseen categories and drifted features, then route the decision to rules, limits or review instead of trusting the score; (3) test any confidence threshold on held-out shifted data first, and count what it refuses among the known-good cases.

</details>

<details><summary>Build notes</summary>

**Knob changes: none.** All three effects pass the 2x rule in the reference set: the P2 latency effect is -4.59117 ms against twice its spread, 2.9344 ms; the P2 accuracy effect is -0.045 with spread 0; P3 against the pets' share is -0.62 with spread 0. The P2 latency effect failed the rule in two earlier sets because of load beside the timed runs (Reruns). It was not tuned up: the change stays at the spec's 160 px. P3 is null at every seed and is reported as measured, not inflated (see the prototype comparison).

**Reruns.** Three reference sets of nine runs each. Set 1 (the same code before the DATA line gained `load1`): P1 29.9194, 28.5989, 33.3475 ms and P2 21.1755, 31.0536, 34.6488 ms, effect -1.66263 ms against a spread of 13.4733 ms. Its change runs at seeds 1 and 2 had p50s 27% and 42% slower than seed 0 for identical work. Set 2 (this script, load1 11.7 to 17.9): P1 24.8021, 26.6777, 31.8195 ms and P2 22.5779, 22.8254, 21.7336 ms, effect -5.38747 ms against a spread of 7.0174 ms. A lab 37 download job ran beside every run of both sets (downloads take no lane lock), on top of the load from outside the build. Set 3 is the one in the .json: the same script, unchanged, run seed by seed with each change right after its own baseline, at load1 5.4 to 7.7, with no build job beside any run. Its effect is -4.59117 ms against a spread of 1.4672 ms, `ok: true`. Only the load on the machine changed between sets 2 and 3. A learner on a busy Mac can land outside these tolerances: compare the `load1` field in the DATA line first.

**Precomputed steps: none.** The longest seed-0 run is the baseline at 12.8 s.

**Deviations from the spec, and why:**

- Parachute: the spec's synset `n03888605` is not one of Imagenette's 10 class folders. Imagenette's parachute folder is `n03888257` (390 validation photos), and the script uses it.
- Which 4 photos per class: the spec does not say. They are drawn with `random.Random(seed)` from the sorted file list, so seed 0 is a fixed set and seeds 1 and 2 test other photos.
- The held-out pets are the spec's "first 200 of lab 01's validation list by filename". The list is sorted by file name and the cat breeds are capitalized, so all 200 are cats: 34 Abyssinian, 44 Bengal, 33 Birman, 46 Bombay, 40 British Shorthair and 3 Egyptian Mau. The lab file says so in P1. The accuracy here is 6 cat breeds scored over all 37 classes, not lab 01's 37-breed accuracy.
- The change keeps lab 01's `Resize(448)` and changes only the size of the last resize (`RandomResizedCropGPU.size`), so exactly one thing differs: the tensor the model sees (`input=1x3x160x160` in the DATA line).
- Requests are each photo's JPEG bytes, read before timing (`learn.predict` accepts bytes), so the clock covers decode, resize, normalize, model and softmax, and no disk read.
- `torch.set_num_threads(1)` is set once in `main()`, before the model loads, so it covers the warm-up and the timed calls in every mode. Every timing line records `threads=1`.
- Extra Record values, cheap, and no prediction asks about them: `baseline.pet_share_above_0_9` (the 0.9 guard's coverage on real pets, the comparison for P3), `baseline.params` (to check size against 4 bytes per parameter), `break.max_top_prob`, and the NONPET lines (the spec's "the breed each was given"). The DATA line's `load1` is a diagnostic, not a result.
- Gradio and Hugging Face Spaces never run in the reference.

**Prototype comparison.** The spec carries no `[answers only]` values for lab 02. Its concept line expects "a softmax that is confidently wrong on out-of-distribution inputs", and P3 came out the other way: none of 60 non-pet photos above 0.9. Checked for a bug before accepting it. The non-pets go through the same `serve()` path that scores 0.88 on the pets. Each photo's 37 probabilities come from `learn.predict` (fastai's softmax activation), and every NONPET line names a breed. The DATA line confirms 224 px inputs. So the null result stands for this model and these photos. Candidates for why: content far from any pet, the 160 px source photos enlarged to 448 px, and lab 01's short training (2 epochs). So this lab does not demonstrate the spec's concept claim, and the answer file does not teach it as a result. The P3 block keeps to what was measured (every input gets a breed, these far non-pets all stayed under 0.9, the guard also refuses real pets) and names what the sample leaves open. No learner-visible file states the claim. The lab file asks P3 without a direction, and the module README's concept text says only that an out-of-distribution input has all of its probability spread over the 37 breeds with no "none of these" output, which every NONPET line shows. The spec's concept line is a build input and stays as written; it is flagged here as unsupported by this lab's runs. The other remedy, drawing non-pet photos until some cross 0.9, was not taken: it would swap the spec's 5 classes and seeded draw for a sample picked for its result. The spec's interview question (a wrong answer at 0.97) stays as a question, and card 02-T's key rests only on what this lab measured.

**Other.**

- The maxima: in set 3 every baseline and change run had a call above 100 ms (102.311 to 116.7 ms), while set 2's maxima ran from 30.5804 to 37.9381 ms with the same photos and code, so neither the photos nor the model explain them. The cause was not separated. Candidates: a Python garbage collection pass over the objects `learn.predict` builds per call, and memory pressure (3 of the Mac's 4 GB of swap were in use just after these runs, and each set-3 run took about 4.1 s longer from start to exit than its set-2 twin). p50 and p95 ignore a stall in 10 or fewer calls, so P1 and P2 are unaffected; read `baseline.max_ms` and `change.max_ms` with care.
- `torch.set_num_threads(1)` limits PyTorch's own thread pool. Whether Apple's Accelerate library, which runs the matrix multiplies, spreads one multiply over more cores was not measured. "One CPU thread" in this lab means that PyTorch setting, as the spec defines it.
- Every run prints a `torch.jit.script` FutureWarning at import and fastai's pickle warning from `load_learner`. Both are harmless.

</details>
