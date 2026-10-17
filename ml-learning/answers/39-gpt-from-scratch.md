# 39. A GPT from scratch: attention, the causal mask and sampling: reference answers

> Spoilers. The AI opens one block at a time, only after that step's prediction row exists and the learner pasted their own RESULT lines, or after 'debrief 39'.

- HW line: `HW chip='Apple M4 Pro' cpu=14 gpu=20 mem_gib=24 macos=26.5.1 python=3.13.7 torch=2.14.1 device=mps`
- Seeds: the baseline at 0, 1 and 2; the change and the break at 0 (heavy lane). `PYTHONHASHSEED=0` in every run.
- Reference script: `m7-language-models/scripts/39_gpt_from_scratch.py` (level W, so the learner's script is the reference), sha256 prefix `f46c2aa354d45495`.
- Configuration: N = 350 iterations (max_iters = lr_decay_iters), set from the smoke's seconds per iteration and hard-coded in the script (Build notes show the steps), batch 64 x 256 characters, eval_iters 20, float32 on MPS.
- Runs and wall times: baseline seed 0 245.1 s, seed 1 243.2 s, seed 2 247.3 s; change seed 0 8.5 s; break seed 0 162.2 s. All ran under the heavy lock, one heavy job at a time, and no light job ran beside them. No step is precomputed.
- Tolerance rule: tol = spread (max - min) over seeds 0, 1, 2; heavy labs: the baseline spread applies to every step. P2 and P3 ran at seed 0 only, so each takes the spread of its baseline partner: `baseline.word_share_t10` for P2 and `baseline.train_loss_300` for P3.
- Raw seed-0 output: `39-gpt-from-scratch.out`. Values, spreads and effects: `39-gpt-from-scratch.json`.

<details><summary>P1. Validation loss at step 0, before any update (seed 0)</summary>

**Answer:** 4.29206 nats at seed 0, tolerance ±0.10031 (the spread over seeds 0, 1 and 2). For comparison, ln 65 = 4.1744.

```
RESULT P1.val_loss_step0=4.29206 unit=nats seed=0
```

Other seeds: 4.19175 (seed 1) and 4.26887 (seed 2).

Why: a model that bets evenly on all 65 characters scores ln 65 = 4.1744 nats on any text, and nanoGPT's init is close to even but not flat. Its weights start at std 0.02, the final LayerNorm scales each hidden state to unit size, and each position's 65 logits come out with a std of about 0.4. Uneven bets cost extra on the characters they do not favour, about std² / 2, which is 0.08 to 0.09 nats here, so all three seeds land above ln 65. The spread across seeds is wide only at step 0: the init also gives each character a small random bias shared by every position, and at seed 1 that bias happens to favour common characters (see Build notes).

Common wrong prediction: ln 65 exactly, with a narrow range. The reasoning is right, but the init is not flat. Another is the unigram entropy of the text, 3.31 nats, which a model reaches only after it has learned how often each character appears.
</details>

<details><summary>P1b. Validation loss at the end of the N = 350 iteration baseline run (seed 0)</summary>

**Answer:** 1.99028 nats at seed 0, tolerance ±0.0096.

```
RESULT P1.val_loss_step0=4.29206 unit=nats seed=0
RESULT baseline.val_loss_250=2.09734 unit=nats seed=0
RESULT baseline.val_loss_300=2.03037 unit=nats seed=0
RESULT P1b.val_loss_final=1.99028 unit=nats seed=0
```

Other seeds: 1.98068 (seed 1) and 1.98659 (seed 2). At iteration 250 the seeds read 2.09734, 2.10619 and 2.09408.

Why: the loss falls fast while the model learns which characters are common and which pairs follow each other, then slowly while it learns words. Most of the drop from 4.29206 is done by iteration 250, and the last 100 iterations run on a learning rate that decays to 1e-4 at iteration 350. The 350 updates show the model 5.7 M characters, about 5.7 passes over the 1.0 M training characters, but the update count is what limits it. The README's 1.4697 is the best validation loss of this config's 5,000-iteration run, 14 times as many updates, and its 1.88 comes from a 4-layer, 128-wide model given 2,000 updates, which ends lower with fewer characters seen (1.5 M).

Common wrong prediction: near 1.4697 because this is the same config; that number is the best of a 5,000-iteration run. Another is a value below 1.88 because the GPU is faster than the CPU; speed only buys more iterations if the run spends them.
</details>

<details><summary>P2. 500 characters at temperature 1.5 from the baseline checkpoint: share of whitespace-separated words found in the training text (seed 0)</summary>

**Answer:** 0.255814 at seed 0, tolerance ±0.033144 (the seed spread of the baseline's own temperature 1.0 share, the nearest baseline value).

```
RESULT change.word_share_t05=0.728155 unit=fraction temperature=0.5 chars=500 words=103 seed=0
RESULT change.word_share_t10=0.477273 unit=fraction temperature=1 chars=500 words=88 seed=0
RESULT P2.word_share_t15=0.255814 unit=fraction temperature=1.5 chars=500 words=86 seed=0
```

Other seeds: the change ran at seed 0 only. The baseline's temperature 1.0 sample gives the spread: 0.477273, 0.505618 and 0.510417 at seeds 0, 1 and 2. At seed 0 the change's temperature 1.0 sample is the same text as the baseline's: the same weights and the same random draws.

Why: temperature divides the logits before the softmax. At 1.5 every gap between two logits shrinks by a third, so unlikely characters gain probability. A word of 5 characters has 5 chances to go wrong, so the word share falls faster than the per-character error rises. At 0.5 the gaps double and sampling sticks to the likeliest characters: more real words, but loops such as "the the".

Common wrong prediction: near 0, as if 1.5 were pure noise, or close to the temperature 1.0 share, as if 1.5 were only a little hotter.
</details>

<details><summary>P3. Causal mask deleted, retrained 300 iterations: training loss at iteration 300 vs the baseline's at 300 (seed 0)</summary>

**Answer:** down. Break minus baseline at iteration 300 is -1.88956 nats: 0.0117554 with the mask deleted against 1.90131 for the baseline. Tolerance ±0.01874, the seed spread of `baseline.train_loss_300`.

```
RESULT break.val_loss_0=4.29159 unit=nats seed=0
RESULT break.val_loss_250=0.0125086 unit=nats seed=0
RESULT break.val_loss_300=0.0120476 unit=nats seed=0
RESULT P3.train_loss_300=0.0117554 unit=nats iters=300 seed=0
RESULT P3.delta_train_loss_300=-1.88956 unit=nats seed=0
RESULT break.word_share_t10=0 unit=fraction temperature=1 chars=500 words=3 seed=0
RESULT break.attention_is_causal=false seed=0
```

The baseline at iteration 300 for seeds 0, 1 and 2: 1.90131, 1.88881 and 1.90755. The effect check (break minus baseline at seed 0, from the rounded RESULT values) is -1.8895546 against a spread of 0.01874.

Why: the target at position t is the character at position t + 1, and that character is also in the input. With the mask gone, position t can attend to position t + 1 and copy its own answer, so by iteration 250 the loss is near zero: the model learned a lookup, not language. Validation runs the same leaky forward pass, so the validation loss falls too (0.0120476 at iteration 300): the metric that should catch the leak is fooled by it. At generation there is no next character to copy, and the sample collapses: 497 of its 500 characters are newlines, and its 3 whitespace-separated tokens are lone punctuation marks, none of them a training word.

Common wrong prediction: "up", because the model has lost its structure, or a small drop of 0.1 to 0.5 nats. The size is the surprise: the drop is almost the whole baseline loss.
</details>

<details><summary>Rebuild check</summary>

Stub: `m7-language-models/rebuild/39_attention_head.py`. Solution: `answers/rebuild/39_attention_head.py`.

Verdict from `rebuildcheck`: the stub fails as it should (exit 1, with NotImplementedError), the solution passes (exit 0, `check: PASS`), REBUILDCHECK OK.

What `check()` tests: `Head(32, 16, 64)` on a random (2, 20, 32) input equals `F.scaled_dot_product_attention(q, k, v, is_causal=True)` on the head's own projections, to atol 1e-6. Then `assert_causal(head, x, 9)` must pass, and after `head.tril.fill_(1.0)` the same call must raise. An `assert_causal` that checks nothing fails that last step.
</details>

<details><summary>Card drafts</summary>

| ID | Lab | Type | Question |
|---|---|---|---|
| 39-M | 39 | M | Why does deleting the causal mask drive a character model's training loss toward zero while its samples get worse? |
| 39-N | 39 | N | A character GPT with a 65-symbol vocabulary is evaluated before any update. What validation loss do you expect, and why does nanoGPT's init land a little above it? |
| 39-D | 39 | D | A new language model's training and validation loss both fall to almost 0 within a few hundred steps, but its samples are one character repeated. What do you check first? |

Keys (1 to 3 must-mention items each):

- 39-M: (1) the target at position t is the input at t + 1, so without the mask that position can read its own answer; (2) at generation there is no future token, so the shortcut has nothing to read; (3) validation runs the same leaky forward pass, so it cannot catch the leak.
- 39-N: (1) ln 65 = 4.17 nats, the loss of an even guess; (2) the reference run measured 4.29206 at seed 0, and 4.19175 to 4.29206 over 3 seeds; (3) the init's logits spread with a std of about 0.4, which adds about std² / 2.
- 39-D: (1) the target leaking into the input: a missing or wrong causal mask (`is_causal`, the tril buffer) or misaligned targets; (2) the test: change the tokens after position t and check that the outputs at 0 to t do not move.
</details>

<details><summary>Build notes</summary>

**N, the knob the build chose, from the smoke.** N is a configuration, not a result. Brief section 4 has the build measure seconds per iteration in `--smoke`, set N from it and hard-code N as the script's default. The lab file names N because P1b asks about it. The smoke's `baseline.mps_s_per_iter` (the median of 18 iterations after 2 warm-up ones) gives N in four steps.

1. The spec's formula, N = min(1,500, floor(360 s / s_per_iter)), budgets 360 s for training iterations only. The first smoke read 0.667954 s per iteration, so the formula gives 538.
2. The baseline run does more than train. It evaluates 20 batches per split at iterations 0, 250, 300 and N, samples 500 characters and times 22 CPU iterations. A probe baseline at N = 400 took 353.6 s of wall time at a median 0.57921 s per iteration. That leaves 353.6 - 400 x 0.57921 = 121.9 s of fixed cost. At the formula's 538, the run would take about 121.9 + 538 x 0.57921 = 433.5 s, plus a fifth eval at iteration 500. That is over the 6-minute cap. The baseline would then be a precomputed step, and the session's `--change` would have no checkpoint to load.
3. The build keeps the formula's 360 s budget but spends it on the whole run: N = floor((360 - 121.9) / 0.667954) = 356. Rounded down to 350 for margin.
4. A smoke on the final script read 0.61405 s per iteration, which shows the smoke's own run-to-run spread. The same whole-run rule gives floor((360 - 121.9) / 0.61405) = 387, and the spec's formula gives 586. So 350 still fits, with margin. N stays 350 because two earlier baselines at the same N took over 5 minutes, with two light jobs running beside them.

Check: the reference baselines at N = 350 took 245.1, 243.2 and 247.3 s. Their median iteration (0.442953 s at seed 0) is faster than the smoke's 18 early iterations, so a smoke-based N is conservative. Even at the reference runs' own speeds, the spec's 586 would take 349.6 to 356.5 s before the fifth eval at iteration 500. That reaches the cap with no room for other work on the learner's Mac.

**Deviation: train.py's loop in-process, not `python train.py`.** train.py hard-codes `torch.manual_seed(1337)`, so `--seed` could not change the init, the batches or dropout, and it times iterations with `time.time()` and no MPS synchronize, which the timing rule forbids. The script keeps train.py's settings: config/train_shakespeare_char.py (6 layers, 6 heads, 384 wide, block 256, batch 64, dropout 0.2, learning rate 1e-3, 100 warmup iterations, cosine decay to 1e-4, beta2 0.99), train.py's defaults (weight decay 0.1, beta1 0.9, gradient clipping at 1.0, no bias) and the lab's flags (max_iters = lr_decay_iters = N, eval_iters 20, eval_interval 250, float32, no compile, mps). The model is nanoGPT's model.py, imported unchanged. Two differences from train.py: the loop stops after N updates (train.py makes one more update after its last eval), and it also evaluates at iteration 300 (for P3) and at N. sample.py is not used because it imports tiktoken, which the base install lacks; the script's `sample()` is `GPT.generate`'s loop, and sample.py's top_k of 200 is a no-op with 65 characters.

**Where the spec was silent.** The break keeps the baseline's schedule (lr_decay_iters = N) and stops at 300, so at iteration 300 the only difference is the mask: the same seed gives the same init and the same batches. "Training loss at iteration 300" is the train-split estimate at the iteration-300 eval (20 batches, dropout off), not train.py's single-batch log line, which is noisier and includes dropout. The change ran at seed 0 only, so the baseline also samples 500 characters at temperature 1.0 at every seed; that spread (0.033144) is P2's tolerance and its effect check. Attention itself lives in model.py, so the script's concept block for the two attention `# Q:` prompts is `matches_causal_formula`, which writes model.py's slow path out and compares it with the fused call. Sample RESULT lines carry `words=`, because the no-mask sample has almost no words and a share needs its denominator. Samples start from a newline, as sample.py does. The script is 184 lines, over the 150-line guide, because of the spec's steps: seven downloads, prepare.py and the patch, train.py's loop, MPS and CPU timings, three temperatures and the no-mask retrain.

**Prototype comparison.** The spec's prototype is P1 = ln 65 = 4.17. Measured: 4.29206, 4.19175 and 4.26887 at seeds 0, 1 and 2. A step-0 level has no direction to compare, and the gap at seed 0 (0.1177) is under 2x the 0.10031 spread. The cause, checked on the CPU with the same init on 16 validation windows of 256 characters: each position's logits have a std of 0.405 to 0.430, so ln 65 + std² / 2 = 4.257 to 4.267. A per-character bias shared by all positions (std 0.205 to 0.251) shifts the loss by -0.0011, -0.0818 and -0.0213 at seeds 0, 1 and 2 (minus the frequency-weighted sum of the biases), which is why seed 1 is lowest. With that bias removed, the three seeds read 4.2686, 4.2465 and 4.2770. Not a bug. The spec has no prototype values for P1b, P2 or P3.

**2x spread rule.** P2: effect -0.221459 against a spread of 0.033144, ok. P3: effect -1.8895546 against a spread of 0.01874, ok. No knob changed for the rule.

**Timings.** The five reference runs ran one at a time, with no light job beside them. The CPU timing still varies most: `baseline.cpu_tokens_per_s` spreads 1117.18 over the three seeds, 15% of its seed-0 value, against 2594.8 for `baseline.mps_tokens_per_s`, 7% of its seed-0 value. A learner with other work running on the Mac should expect slower numbers.

**Reruns.** The first seed-0 baseline, change and break went stale when the `words=` tag was added, and were rerun. The reruns repeated every sample exactly and every loss to the printed digits, except two no-mask losses that moved in the sixth significant digit (MPS arithmetic is not bit-exact). Only the timings moved: the stale seed-0 baseline, run on a quieter Mac, timed both devices faster than the rerun. Later the script's constants were regrouped by source (the config file or train.py's defaults) and the comments on the timing warm-up and the word share were reworded, with no change in behaviour. All five reference runs went stale and were rerun, with no light job beside them. The reruns repeated every word share, every seed-0 sample and every seed-0 baseline loss exactly. Seven losses, at seeds 1 and 2 or with the mask deleted, moved in the sixth significant digit. The timings moved most: these reruns timed both devices faster than the runs they replace, which had up to two light jobs beside them.
</details>
