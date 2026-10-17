# 39. A GPT from scratch: attention, the causal mask and sampling

> Goal: after this I can train a 10.7 M-parameter character GPT (generative pre-trained transformer) on MPS (Metal Performance Shaders, PyTorch's backend for the Apple graphics processor) inside 6 minutes. I can predict its loss at step 0 and show what deleting the causal mask does. (No result values anywhere in this file.)

**Level:** W (see `ml-learning/CLAUDE.md`). **Output style:** Explanatory
**Concept link:** [`../README.md#attention-and-the-causal-mask`](../README.md#attention-and-the-causal-mask) (read after the lab)
**Borrowed from:** Karpathy, ["Let's build GPT: from scratch, in code, spelled out"](https://www.youtube.com/watch?v=kCc8FmEb1nY) (1:56:20). [nanoGPT](https://github.com/karpathy/nanoGPT), MIT licence: its README calls it deprecated since November 2025, and this lab pins commit 3adf61e. Raschka, [Build a Large Language Model (From Scratch)](https://github.com/rasbt/LLMs-from-scratch) ch 3 to 5. This lab is an exception to "after the lab": write P1, P1b, P2 and P3 (section 1) first, then watch the video before the lab. nanoGPT's README and Raschka ch 3 to 5 come after the lab, as the second contact 1 to 3 days later.
**Dataset:** TinyShakespeare, a subset of Shakespeare's works, prepared by nanoGPT's `data/shakespeare_char/prepare.py`. 1,115,394 characters, a 65-character vocabulary, 1,003,854 train and 111,540 validation tokens (the first 90% and the last 10% of the file). 1.1 MB, https://raw.githubusercontent.com/karpathy/char-rnn/master/data/tinyshakespeare/input.txt. Licence: the text is public domain. char-rnn's Readme says MIT, though the repo has no LICENSE file. nanoGPT's code is MIT.
**Runs on:** mps. **Lane:** heavy. **Compute:** 3 runs: baseline 5 min, change 1, break 3 (rounded up from the reference runs; other work on the Mac can add a minute to the baseline), at most 6 min per run. Precomputed steps: none
**Needs:** base install only (torch, numpy and requests). Skip nanoGPT's own install line: transformers, datasets, tiktoken and wandb are not needed.
**Before the session** (from the module folder, see section 2): first run `python scripts/39_gpt_from_scratch.py --download`. It fetches nanoGPT's six files at commit 3adf61e into `~/ml-data/nanoGPT/` and the 1.1 MB text. Then it runs nanoGPT's `prepare.py` and writes the patched copy `~/ml-data/nanoGPT-nomask/model.py`. Run `--smoke` next, under a minute. Its one number, `baseline.mps_s_per_iter`, is the calibration N came from. Then, days before the session and with no AI: read the script for 4 minutes, answer its three `# Q:` prompts, and write P1, P1b, P2 and P3 (section 1 and `../../prediction-log.md`). Then watch the video over 2 evenings.
**Interview question:** Explain attention and the causal mask, and why generation latency grows with output length.
**Repo link:** `hld/financial-ai-assistant/deep-dives/latency-cost-and-context.md` [§1 "Where the time goes"](../../../hld/financial-ai-assistant/deep-dives/latency-cost-and-context.md#1-where-the-time-goes) and [§2 "Why the answer is capped at 150 tokens: the sensitivity"](../../../hld/financial-ai-assistant/deep-dives/latency-cost-and-context.md#2-why-the-answer-is-capped-at-150-tokens-the-sensitivity)
**Captured by the script:** P1 and P1b validation losses, the evals between them and the training loss at iteration 300. Seconds per iteration and tokens per second on MPS, tokens per second on the CPU (central processing unit) for 20 iterations, N and the attention check. Samples at temperatures 0.5, 1.0 and 1.5 with their word shares. The no-mask run's losses, sample, word share and attention check. **Human steps:** none
**Status:** todo

## 0. Retrieval (0:00, 5 min, closed book, no AI)

The AI asks up to three due cards from `../../quiz-bank.md`, one at a time. Do not open the bank first.

## 1. Predict (0:05, 7 min, no AI)

This lab is an exception: you write this section days before the session, before you watch the video.

1. **Days before, no AI.** Level W: read `scripts/39_gpt_from_scratch.py` for 4 minutes. Read `matches_causal_formula`, `sample`, `train` and `lr_at`, and skim the rest. Answer its three `# Q:` prompts here. Then write P1, P1b, P2 and P3 in the table below.
2. **At 0:05 (7 min).** Reread your answers and rows, and change nothing. Then reread `CausalSelfAttention.forward` in `~/ml-data/nanoGPT/model.py`, nanoGPT's own worked example. `matches_causal_formula` writes out its slow path, and `GPT.generate` is the loop in `sample`.

- Q1, `matches_causal_formula`: why divide by sqrt(head_size)?
- Q2, `matches_causal_formula`: what does the tril mask stop?
- Q3, `sample`: what does temperature do to the logits?

Write each row here before any measured mode runs; the AI copies it into `../../prediction-log.md` word for word. A row that asks for several numbers becomes one log row per number, each with its own range. `--download` and `--smoke` print nothing you predict.

| Step | Question | Kind | Prediction | 80% range or confidence |
|---|---|---|---|---|
| P1 | Validation loss at step 0, before any update (`P1.val_loss_step0`). nanoGPT's shakespeare_char model: 6 layers, 6 heads, 384 wide, a 256-character context, the 65-character vocabulary, about 10.7 M parameters, seed 0. Mean cross-entropy in nats over 20 validation batches of 64 x 256 characters. | num | | |
| P1b | Validation loss at the end of the N = 350 iteration baseline run (`P1b.val_loss_final`): the same model and seed, batch 64 x 256, learning rate 1e-3 with 100 warmup iterations and cosine decay to 1e-4 at iteration 350, dropout 0.2, float32 on MPS. README anchors: 1.88 for a 4-layer, 4-head, 128-wide model with a 64-character context, batch 12, no dropout and 2,000 iterations, on a CPU in about 3 minutes; 1.4697, the best validation loss of this config's 5,000-iteration run on one NVIDIA A100. | num | | |
| P2 | 500 characters sampled at temperature 1.5 from the baseline checkpoint (seed 0, starting from a newline, no top-k). The share of the sample's whitespace-separated tokens (punctuation and case kept) that occur exactly as a whitespace-separated token of the train split (`P2.word_share_t15`). | num | | |
| P3 | Delete the causal mask and retrain 300 iterations (seed 0, the baseline's settings and learning-rate schedule): training loss at iteration 300 vs the baseline's at 300. Direction, and size as break minus baseline in nats (`P3.delta_train_loss_300`). Both are the train-split loss over 20 batches at the iteration-300 eval. | dir | | |

## 2. Setup (before the session)

```
$ source ~/.venvs/ml/bin/activate
$ cd m7-language-models    # from ml-learning/, where sessions start
$ python scripts/39_gpt_from_scratch.py --download
$ python scripts/39_gpt_from_scratch.py --smoke
```

## 3. Baseline (0:12, 10 min)

Why: a training run is judged by two numbers, the loss before the first update and the loss after the last. This run gives both for nanoGPT's Shakespeare config, inside the 6-minute cap.

```
$ python scripts/39_gpt_from_scratch.py --baseline
(paste your RESULT lines)
```

The run evaluates at iterations 0, 250, 300 and 350, saves `~/ml-data/results/lab39/ckpt-seed0.pt`, prints a 500-character sample at temperature 1.0, then times 20 iterations on the CPU.

Prediction vs actual, one sentence. The reference run is in `../../answers/`; the AI opens it only after your P1 and P1b rows exist.

## 4. Change one thing (0:22, 10 min)

Change: the sampling temperature, 0.5, 1.0 and 1.5, on the baseline checkpoint (no retraining). P2 is logged above.

Why: the weights and the random draws stay fixed, so any difference between the three samples comes from the temperature alone.

```
$ python scripts/39_gpt_from_scratch.py --change
(paste your RESULT lines)
```

## 5. Break it (0:32, 10 min, AI gives hints only; the run finishes by 0:40)

Break: delete the causal mask. `--break` imports `~/ml-data/nanoGPT-nomask/model.py`, a copy of model.py with two edits: `is_causal=False` in the flash path, and the `masked_fill` line removed from the slow path. On torch 2.x the flash path runs, so `is_causal` is the edit that takes effect. The `diff` below shows both. `--break` retrains 300 iterations from the same seed with the baseline's settings, then samples 500 characters at temperature 1.0. P3 is logged above.

Why: a missing mask is a one-line bug that raises no error. This run shows what it does to the numbers you would watch: train loss, validation loss and a sample.

```
$ diff ~/ml-data/nanoGPT/model.py ~/ml-data/nanoGPT-nomask/model.py
$ python scripts/39_gpt_from_scratch.py --break
(paste your RESULT lines)
```

Why, in three sentences, written without AI:

## 6. Explain-back (0:42, 5 min) and rebuild (0:47, 10 min), no AI

- Five sentences for a smart engineer new to ML, written without AI. The AI names your weakest claim after the session (section 7).
- Rebuild: open `rebuild/39_attention_head.py`, write the body from memory (`Head` and `assert_causal`), then run `python rebuild/39_attention_head.py`. Its `check()` compares with torch's `F.scaled_dot_product_attention(is_causal=True)`, never with this lab's results.

## 7. What I learned

After the session (about 5 minutes): the AI names the weakest claim in your five sentences and asks one question that tests it. Edit the sentences here.

## 8. Interview soundbite (one of the three cards written at 0:57)

> One or two sentences only someone who ran this would say.

Staff follow-up (simplest design): the repo's uncapped 300-token answer missed its 8 s p95 (95th percentile) target. What is the simplest change that brings it under, and what does it cost the user? Answer in 2 sentences from the repo link §1 and §2. Rotate: simplest design, failure modes, migration, what pages at 3 am, cost, trade-off.

## 9. Quiz cards (0:57, 3 min)

The AI drafts three cards (M, N, and T or D). Edit or replace them. Questions go to `../../quiz-bank.md`, keys to `../../answers/quiz-key.md`.

## Record

The script prints these as RESULT lines. Paste, do not type.

| Metric | Your run | Hardware (the script's HW line) | Captured by (script or learner) |
|---|---|---|---|
| `P1.val_loss_step0`: validation loss before any update (nats) | | | script |
| `baseline.val_loss_250`: validation loss at iteration 250 | | | script |
| `baseline.val_loss_300`: validation loss at iteration 300 | | | script |
| `P1b.val_loss_final`: validation loss at iteration 350 | | | script |
| `baseline.train_loss_300`: train-split loss at iteration 300 | | | script |
| `baseline.mps_s_per_iter`: seconds per training iteration on MPS, median | | | script |
| `baseline.mps_tokens_per_s`: tokens per second on MPS, median | | | script |
| `baseline.word_share_t10`: word share of 500 characters at temperature 1.0 | | | script |
| `baseline.attention_is_causal`: layer 0 matches the causal formula | | | script |
| `baseline.cpu_tokens_per_s`: tokens per second on the CPU, 20 iterations, median | | | script |
| `baseline.max_iters`: N | | | script |
| `change.word_share_t05`: word share at temperature 0.5 | | | script |
| `change.word_share_t10`: word share at temperature 1.0 | | | script |
| `P2.word_share_t15`: word share at temperature 1.5 | | | script |
| `break.val_loss_0`: validation loss before any update, mask deleted | | | script |
| `break.val_loss_250`: validation loss at iteration 250, mask deleted | | | script |
| `break.val_loss_300`: validation loss at iteration 300, mask deleted | | | script |
| `P3.train_loss_300`: train-split loss at iteration 300, mask deleted | | | script |
| `P3.delta_train_loss_300`: break minus baseline at iteration 300 | | | script |
| `break.word_share_t10`: word share of 500 characters at temperature 1.0, mask deleted | | | script |
| `break.attention_is_causal`: layer 0 matches the causal formula, mask deleted | | | script |
| One line from each of the five samples, and what it shows | | | learner |
