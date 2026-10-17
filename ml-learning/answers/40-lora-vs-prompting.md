# 40. LoRA on a 4-bit model vs 5-shot prompting: when to fine-tune at all: reference answers

> Spoilers. The AI opens one block at a time, only after that step's prediction row exists and the learner pasted their own RESULT lines, or after 'debrief 40'.

- **HW:** `HW chip='Apple M4 Pro' cpu=14 gpu=20 mem_gib=24 macos=26.5.1 python=3.13.7 torch=2.14.1 mlx=0.32.4 device=mlx`
- **Seeds:** seed 0 for every step, plus seeds 1 and 2 for the baseline (heavy lane) and for the break (to give its effect a seed spread). Seed 0 uses train rows 0 to 4 as the shots. Seeds 1 and 2 draw 5 train rows at random (rows 510, 34, 753, 949, 471 and rows 298, 109, 834, 260, 413, from the runs' `shots=` tags).
- **Reference script:** `answers/40_lora_vs_prompting_ref.py` (script hash 3bb6ed93ca9d17bf). Every run below is current.
- **Runs and wall times:** baseline 55.5 s at seed 0 (86.0 s at seed 1, 77.8 s at seed 2); change 280.0 s; break 946.5 s at seed 0 (848.7 s at seed 1, 825.2 s at seed 2), precomputed. All on the heavy lock.
- **Tolerance rule (from the .json):** tol = spread (max - min) over seeds 0, 1, 2; heavy labs: the baseline spread applies to every step. Here the baseline spread is 7 points of exact match; it is the tolerance for P1 and P2. One exception, also recorded in the .json notes: P3 uses its own seed spread, 0 iterations, because the break ran at seeds 0, 1 and 2 and a spread in exact-match points cannot measure an iteration count.

<details><summary>P1. Exact match on the 100 WikiSQL test rows with a 5-shot prompt (the first 5 train rows), Llama-3.2-1B-Instruct-4bit, greedy, seed 0</summary>

**Answer: 15% (15 of 100 items). Tolerance: 7 points, the seed spread (max minus min).**

```
RESULT P1.exact_match_pct=15 unit=pct n=100 shots=0-1-2-3-4 seed=0
RESULT baseline.prompt_tokens=413.13 unit=tokens seed=0
```

Other seeds, 5 random train rows as the shots: 21% at seed 1 and 22% at seed 2, so the spread is 7 points. Prompt length: 422.13 and 437.13 tokens (spread 24.0).

Why: exact match rewards the dataset's conventions, not valid SQL. WikiSQL's labels select one column, write the aggregate (COUNT, MIN, MAX) exactly where the annotators put it, and name the WHERE column the label uses. Five examples show the shape but cannot teach those habits; four of the five shots come from one table, and only one shows an aggregate. Most 5-shot misses get the SELECT clause wrong, and many of those list several columns, the way SQL usually reads; WikiSQL's labels almost never do. The shot draw alone moves the score by 7 points, so prompt choice is part of the baseline's noise.

Common wrong prediction: 40% to 70%, from "a chat model knows SQL". It does write SQL; the misses are convention misses, and exact match counts every one of them.

</details>

<details><summary>P2. LoRA for N = 300 iterations instead of the prompt, scored zero-shot on the same 100 items: exact-match change in points, and flips each way</summary>

**Answer: up 48 points (15% to 63%). Tolerance: 7 points, the baseline spread. Flips: 51 to right, 3 to wrong.**

```
RESULT P2.em_change_pts=48 unit=pts n=100 iters=300 seed=0
RESULT P2.flips_to_right=51 unit=items seed=0
RESULT P2.flips_to_wrong=3 unit=items seed=0
RESULT change.exact_match_pct=63 unit=pct seed=0
RESULT change.sign_test_p=2.91878e-12 unit=p seed=0
RESULT change.ci95_width_pts=21.9214 unit=pts seed=0
RESULT change.prompt_tokens=56.13 unit=tokens seed=0
RESULT change.trainable_pct=0.456063 unit=pct seed=0
RESULT change.lora_rank=8 unit=r seed=0
RESULT change.lora_scale=20 unit=scale seed=0
RESULT change.peak_mem_gb=3.93578 unit=GB seed=0
RESULT change.train_tok_per_s=496.632 unit=tok/s device=mlx batch=4 warmup=10 stat=median n=290 seed=0
RESULT change.tok_s_3b_share=0.577825 unit=fraction device=mlx batch=4 warmup=10 stat=median n=20 seed=0
```

One seed (heavy lane). The effect, 48 points, is 6.9 times the 7-point baseline spread; the .json effect check says ok.

Why: 300 iterations at batch 4 is 1,200 examples, 1.2 epochs of the 1,000 train rows. That is enough for the adapter to learn the label habits the prompt could only hint at: one column, WikiSQL's aggregate words, its column names. Pairing is what makes 100 items decisive: only the 54 items that flip carry information, and 51 against 3 gives an exact sign-test p of 2.91878e-12. The paired 95% interval is 21.9214 points wide, about plus or minus 11 points, as the spec's "about 100 items give about plus or minus 10 points" warns; 48 points clears it, a 5-point gain would not. The 3 flips to wrong are the adapter over-applying WikiSQL's aggregate habit (MIN or COUNT where the label has none), and once trimming a junk suffix that the gold answer keeps.

Cost, the half the interview question asks about: the 5-shot prompt costs 413.13 tokens per item against 56.13 zero-shot, 7.4 times the tokens on every call. The adapter costs one training run: 0.456063% of the parameters train (rank 8 on all 7 projections of the 16 blocks; the embedding gets none), 3.93578 GB peak, 496.632 training tokens per second on this M4 Pro. The 3B 4-bit model trains at 0.577825 of the 1B's speed on the same batches. mlx-lm's scale of 20 multiplies B A directly, where the rebuild's alpha / r is 16 / 8 = 2: mlx-lm's update is 10 times larger at the same rank.

Common wrong prediction: a modest gain, 5 to 15 points, with flips about even both ways. A strict output format with in-distribution training rows is the case where fine-tuning wins big, and the flips are lopsided because the prompt's errors are systematic.

</details>

<details><summary>P3. LoRA on the first 100 train rows for 1,000 iterations (40 epochs at batch 4), validation every 25 iterations, seed 0: the iteration where validation loss bottoms out</summary>

**Answer: iteration 50 (precomputed; the seed-0 run took 946.5 s). Tolerance: 0 iterations, P3's own seed spread (the one exception to the heavy-lab rule, see the tolerance rule above): seeds 0, 1 and 2 all bottom out at iteration 50. Validation runs every 25 iterations, so the answer can only land on that grid.**

```
RESULT P3.best_iter=50 unit=iteration every=25 iters=1000 seed=0
RESULT break.val_loss_start=3.4239 unit=nats seed=0
RESULT break.val_loss_min=1.70133 unit=nats seed=0
RESULT break.val_loss_final=2.6995 unit=nats seed=0
RESULT break.train_loss_final=0.0753718 unit=nats seed=0
```

Other seeds (a different LoRA init and batch order, the same 100 rows): best iteration 50 at seeds 1 and 2 (spread 0). Validation loss at iteration 1 is 3.4239 at every seed (spread 0.0), because B starts at zeros. Minimum 1.71462 and 1.67848 (spread 0.03614000000000006); final 2.59614 and 2.64355 (spread 0.1033599999999999); training loss at the end 0.08036 and 0.0730588 (spread 0.007301200000000008).

Why: 100 rows at batch 4 is 25 iterations per epoch, so the minimum sits at 2 epochs (49 updates, since mlx-lm validates before the update of the iteration it prints). The first two epochs teach the format, which carries over to the validation rows. After that the adapter memorizes its 100 rows: training loss falls to 0.0753718 while validation loss climbs from 1.70133 to 2.6995. Over the three seeds the rise from the minimum to iteration 1,000 averages 0.9482533333333333 nats. At no seed does it return to its iteration-50 level: the last 95% of the run buys nothing on held-out rows. The fix is early stopping on a held-out curve, or more rows.

Common wrong prediction: several hundred iterations, from "more epochs help until late". With 100 rows, mlx-lm's default learning rate and a scale of 20, the useful signal is spent in about 2 epochs.

</details>

<details><summary>Rebuild check</summary>

Solution: `answers/rebuild/40_lora_linear.py`. `rebuildcheck`: the stub fails as it should (NotImplementedError), the solution passes (`check: PASS`): REBUILDCHECK OK.

What `check()` tests: the layer equals its base at init; B starts at zeros and A random; after one SGD step only A and B may move (only B does, because A's gradient is proportional to B, which is still zero); with B random, the layer equals `F.linear` with the merged weight W + (alpha / r) B A; the trainable share is 0.77% for one 2048 x 2048 layer at r = 8; exact match ignores case and whitespace. Five broken versions each fail it: no scale, base not frozen, B random at init, no lowercasing, a wrong share.

</details>

<details><summary>Card drafts</summary>

| ID | Lab | Type | Question |
|---|---|---|---|
| 40-M | 40 | M | Why does LoRA start B at zeros and A at small random values, rather than both random or both zero? |
| 40-N | 40 | N | LoRA at rank 8 on every projection of Llama-3.2-1B's 16 blocks trains what share of the model's parameters, and where does that number come from? |
| 40-D | 40 | D | A LoRA run on 100 rows for 40 epochs ends with training loss near zero, and the adapter scores worse on held-out items than an early checkpoint did. What do you check first, and what do you change? |
| 40-T | 40 | T | Alternate for a close where the last card was a D: a disputes team wants an LLM to tag chargeback notes with one of 12 reason codes, and a 5-shot prompt is live. What evidence would make you switch to a LoRA adapter, and what does each option cost to run? |

Keys, 1 to 3 must-mention items each:

- **40-M:** (1) B = 0 makes the adapted layer equal the frozen base at step 0, so training starts from the pretrained model. (2) A random gives B a nonzero gradient; with both zero, neither gets one. (3) On the first step only B moves, because A's gradient is proportional to B.
- **40-N:** (1) About 0.46% (0.456063% in the reference run). (2) Each projection adds r x (d_in + d_out) numbers instead of d_in x d_out. (3) The embedding and the norms get no adapter.
- **40-D:** (1) The validation loss per epoch on held-out rows: in the reference it bottoms out at iteration 50 and rises after, while training loss keeps falling. (2) Keep the checkpoint at the validation minimum (early stopping), or add rows or cut epochs.
- **40-T:** (1) A paired eval on the same held-out items: flips each way and a sign test, not two separate accuracies. (2) Per call, the 5-shot prompt carried 7.4 times the zero-shot tokens in the reference. (3) The adapter is a one-time training run, repeated whenever the base model changes.

</details>

<details><summary>Build notes</summary>

- **Knob changes:** none for the 2x rule. The P2 effect (48 points) is 6.9 times the baseline spread (7 points). The P3 effect (0.9482533333333333 nats) is 9.2 times its own seed spread (0.1033599999999999 nats).
- **N = 300.** The spec sets N = min(600, the iterations that fit 6 minutes) from a 20-iteration smoke. Two reference smokes measured 0.54 and 0.76 s per iteration (median of 2-iteration windows after the first) under varying background load on this shared Mac. A phase probe put the rest of `--change` at about 96 s: imports and loads, the first-window compile, scoring 100 items, the 3B speed run. That gives 347 to 488 iterations; 300 keeps the run under 6 minutes at the slowest rate seen. The seed-0 change run took 280.0 s.
- **Precomputed: P3.** The break runs over the 6-minute cap, with `--timeout 2700`: 946.5 s at seed 0 (see Reruns), 848.7 s at seed 1 and 825.2 s at seed 2. Its 41 validation passes over 100 rows are about a third of each run.
- **Where the spec is silent, the simplest correct option:**
  - Seeds. A greedy 5-shot eval has no random choice, so seeds 1 and 2 draw 5 random train rows as the shots; seed 0 keeps the first 5, the spec's config. The P1 spread is the shot-choice spread.
  - Prompts. Raw text, no chat template, for both arms: the same format LoRA trains on. The prediction is the first line of the output.
  - mlx-lm through its Python API: `mlx_lm.lora.train_model` with `CONFIG_DEFAULTS` plus the spec's flags, and `mlx_lm.generate`. Same defaults as `mlx_lm lora --train`, and the script reads speed, memory and loss from mlx-lm's callback.
  - No validation during `--change`, which saves about 22 s of the budget. Validation runs only in `--break`, on all 100 validation rows every 25 iterations (one epoch of the 100-row set).
  - The 3B share. Both models train the same first 30 batches (same seed, same data order); the share compares iterations 11 to 30, the second and third 10-iteration windows: the spec's "over 20 iterations".
  - The 95% interval. Normal approximation on the per-item paired difference: 2 x 1.96 x the sample standard deviation over the square root of 100.
  - Iterations are reported as mlx-lm prints them; it validates before that iteration's update.
- **Effect check for P3.** The heavy-lane protocol runs the break at seed 0 only, which left its effect with no spread to compare with. Seeds 1 and 2 of the break were run for that, unchanged script. The effect is the validation-loss rise from the minimum to iteration 1,000 (`break.val_loss_final` minus `break.val_loss_min`): 0.9482533333333333 nats, the mean over seeds 0, 1 and 2, against a spread of 0.1033599999999999 nats (the larger of the two values' spreads). The .json effect check says ok. At every seed the curve bottoms out at iteration 50 and never returns to its minimum.
- **Prototype comparison.** The spec has no `[answers only]` values for this lab. The author note's "about 100 items give about plus or minus 10 points at 95%" matches the measured paired interval, 21.9214 points wide. The concept line says LoRA trains "about 1%" of the parameters; at rank 8 on Llama-3.2-1B it is 0.456063%, because the embedding (about 263 M of the parameters) gets no adapter and the MLP (multilayer perceptron) projections are wide. The docs' 250 tokens/s is a different setup (full-precision 7B, batch 1, M1 Max) and is not compared.
- **Reruns.** Change and break at seed 0 ran a second time, unchanged script, with a wider console (`COLUMNS=250`), because mlx-lm's header panel had wrapped the long build data path and mkanswers could not sanitize it in the `.out`. Every accuracy and loss value came back identical (greedy decoding, seeded training). The two speed values moved by about a tenth between the two runs under the build's background load (peak memory hardly moved), so read the speeds as plus or minus 15%.
- **mlx-lm detail.** `iterate_batches` sorts by `len()` of the raw row dict, which is 1 for every `{"text": ...}` row, so batches are consecutive file-order groups of 4, shuffled each epoch. The CLI does the same.
- **Reference length:** 163 lines, over the 150 guideline: two models, three training modes, the paired test and the speed share.

</details>
