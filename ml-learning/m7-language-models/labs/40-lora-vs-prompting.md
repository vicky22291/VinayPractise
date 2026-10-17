# 40. LoRA on a 4-bit model vs 5-shot prompting: when to fine-tune at all

> Goal: after this I can fine-tune Llama-3.2-1B-Instruct-4bit with LoRA (low-rank adaptation) on MLX, compare it with a 5-shot prompt on the same 100 held-out items with a paired test, and read where validation loss bottoms out when 100 examples train for 40 epochs. (No result values anywhere in this file.)

**Level:** S (see `ml-learning/CLAUDE.md`). **Output style:** Explanatory
**Concept link:** [`../README.md#prompting-vs-lora`](../README.md#prompting-vs-lora) (read after the lab)
**Borrowed from:** [mlx-lm LORA.md](https://github.com/ml-explore/mlx-lm/blob/main/mlx_lm/LORA.md); [Hu et al. 2021, LoRA (arXiv 2106.09685)](https://arxiv.org/abs/2106.09685); Raschka, *Build a Large Language Model (From Scratch)*, appendix E (parameter-efficient fine-tuning with LoRA); Huyen, *AI Engineering*, chapter 7 (Finetuning). Do it after the lab, as the second contact 1 to 3 days later.
**Dataset:** mlx-examples WikiSQL text data: `train.jsonl` 1,000 rows (272,537 B), `valid.jsonl` 100 rows (28,495 B), `test.jsonl` 100 rows (27,862 B), from <https://github.com/ml-explore/mlx-examples/tree/main/lora/data> (the script fetches the raw files), MIT licence (the mlx-examples repo). Model `mlx-community/Llama-3.2-1B-Instruct-4bit` (695.3 MB, Llama 3.2 Community License, ungated, no token); `mlx-community/Llama-3.2-3B-Instruct-4bit` (1,807.5 MB) only for a speed ratio.
**Runs on:** mlx. **Lane:** heavy. **Compute:** 2 runs x 5 min (`--baseline` 1 min, `--change` 5 min), at most 6 min per run. Precomputed steps: P3 (`--break`, 16 min)
**Needs:** `python -m pip install mlx==0.32.4 mlx-lm==0.32.2` (mlx 0.32.4's wheel is tagged macOS 26; this Mac runs 26.5.1)
**Before the session** (from the module folder, see section 2): `python scripts/40_lora_vs_prompting.py --download` (the three WikiSQL files into `~/ml-data/wikisql/`, both models, 2.5 GB, into `~/ml-data/hf/`), then `--smoke`.
**Interview question:** Prompting, RAG (retrieval-augmented generation) or fine-tuning for this use case: what evidence decides, and what does each cost to run and maintain?
**Repo link:** [`hld/financial-ai-assistant/deep-dives/offline-evals-and-rollout.md`, §1 The pipeline](../../../hld/financial-ai-assistant/deep-dives/offline-evals-and-rollout.md#1-the-pipeline); [same file, §3 The statistics: what the suite can and cannot see](../../../hld/financial-ai-assistant/deep-dives/offline-evals-and-rollout.md#3-the-statistics-what-the-suite-can-and-cannot-see)
**Captured by the script:** P1 to P3 and every Record row. **Human steps:** the eval protocol (items, scoring, the paired test, the RESULT contract) and your ship rule in section 3, before the AI writes the harness; a one-line annotation of each AI block before the first run; `LoRALinear()`, `trainable_share()` and `exact_match()`, drafted in a scratch copy in section 4 while `--change` trains, then written from memory in `rebuild/40_lora_linear.py` at 0:47
**Status:** todo

## 0. Retrieval (0:00, 5 min, closed book, no AI)

The AI asks up to three due cards from `../../quiz-bank.md`, one at a time. Do not open the bank first.

## 1. Predict (0:05, 7 min, no AI)

Level S: read `scripts/40_lora_vs_prompting.py` for 2 minutes first. `load_data()` and `report()` are given; `report()` is the RESULT contract your harness feeds.

Write each row here before anything runs; the AI copies it into `../../prediction-log.md` word for word. A row that asks for several numbers becomes one log row per number, each with its own range.

| Step | Question | Kind | Prediction | 80% range or confidence |
|---|---|---|---|---|
| P1 | Exact match, in percent of the 100 WikiSQL test rows, for `mlx-community/Llama-3.2-1B-Instruct-4bit` with a 5-shot prompt (the first 5 train rows), greedy decoding, at most 64 new tokens, seed 0 | num | | |
| P2 | LoRA on the same 1B model for N = 300 iterations instead of the prompt (`--batch-size 4 --num-layers 16 --max-seq-length 512` on all 1,000 train rows, every other flag at mlx-lm's default, no validation, seed 0), scored zero-shot on the same 100 items: the exact-match change in points (up, down or same, plus a size range), and how many items flip each way | dir | | |
| P3 | LoRA on the first 100 train rows for 1,000 iterations (the same 1B model and training flags as P2, 40 epochs at batch 4, seed 0), validation loss on all 100 validation rows at iteration 1 and then every 25 iterations up to 1,000: the iteration where validation loss bottoms out | num | | |

P2's Hit uses the points change, graded as dir. Also write the two flip counts in the same row, each a number with its own 80% range; each is graded as num.

Terms, fixed so your numbers compare with the reference:

- **Item.** One test row. Its prompt is the row's text up to and including its last `A:`; its gold answer is the SQL (structured query language) after that.
- **5-shot prompt.** The first 5 train rows in full, each followed by a blank line, then the item's prompt. Raw text, no chat template: the same format LoRA trains on.
- **Zero-shot prompt.** The item's prompt alone. The LoRA model gets this one.
- **Prediction.** The first line of the model's output, greedy, at most 64 new tokens.
- **Exact match.** The prediction equals the gold answer after lowercasing, trimming both ends and collapsing runs of whitespace to one space.
- **Flip.** An item one method gets right and the other gets wrong. To right: 5-shot wrong, LoRA right. To wrong: 5-shot right, LoRA wrong.
- **Sign test.** Exact two-sided binomial test of the to-right flips out of all flips, at p = 0.5 (`scipy.stats.binomtest`).
- **95% interval width.** 2 x 1.96 x the sample standard deviation of the per-item difference (LoRA right minus 5-shot right, so -1, 0 or 1), divided by the square root of 100, in points.
- **Pairing.** `--baseline` saves each item's right or wrong to `~/ml-data/results/lab40/baseline-s0.json`; `--change` reads it, so run `--baseline` first.
- **Iteration.** mlx-lm's own count, as it prints it. It validates before the update of that iteration, so iteration 1 is the untrained model.

## 2. Setup (before the session)

```
$ source ~/.venvs/ml/bin/activate
$ cd m7-language-models    # from ml-learning/, where sessions start
$ python scripts/40_lora_vs_prompting.py --download
$ python scripts/40_lora_vs_prompting.py --smoke
```

`--smoke` checks the given plumbing only: the data loads, the 1B model generates, mlx-lm trains for 20 iterations (it prints seconds per iteration, the calibration behind N in section 4), and `report()` parses. `--baseline`, `--change` and `--break` stop with NotImplementedError until the harness exists.

## 3. Baseline (0:12, 10 min)

Why: a fine-tune is worth its cost only if it beats the cheapest thing that could work, so the 5-shot prompt sets the bar on the same items.

You write first, in this file, no AI (about 5 min). This is the prompt the AI builds from:

1. The items and the scoring, from the Terms in section 1, in your own words: which rows, how a row splits into prompt and gold answer, what counts as the prediction, and how you normalize before comparing.
2. The paired test, from the same Terms: what you record per item, the exact test on the flips, and the 95% interval width.
3. The RESULT contract: which `report()` call each mode makes, and how each value in it is computed.
4. Your ship rule, the one decision here that is yours: the paired result (flips each way, sign-test p-value, size of the change) that would make you ship the adapter instead of the prompt.

The AI then writes the generation loop and the mlx-lm calls (`load`, `generate`, and `train_model` with the flags in section 4) from your prompt. Annotate each AI block with one line before the first run.

```
$ python scripts/40_lora_vs_prompting.py --baseline
(paste your RESULT lines)
```

Prediction vs actual, one sentence. The reference run is in `../../answers/`; the AI opens it only after your P1 row exists and you have pasted your own RESULT lines.

## 4. Change one thing (0:22, 10 min)

Change: the adaptation method, from the 1B base with 5 shots in the prompt to the same base plus a LoRA adapter with no shots (two coupled parts, one decision). P2 is logged above.

- **Training.** `mlx_lm lora --train` settings on all 1,000 train rows: `--iters 300 --batch-size 4 --num-layers 16 --max-seq-length 512`, every other flag at mlx-lm's default, no validation during the run.
- **Scoring.** The adapter answers the same 100 items zero-shot, and each item pairs with its baseline result.
- **N = 300** is the build's setting: N = min(600, the iterations that fit 6 minutes after the run's fixed cost of loading, scoring 100 items and the 3B run), rounded down for margin. Seconds per iteration come from the 20-iteration smoke.
- **Speed ratio.** The same run also trains the 3B 4-bit model for 30 iterations with the same flags, seed and batches.

Why: LoRA trains two small matrices beside each frozen 4-bit projection in the adapted blocks; the question is whether 300 iterations of training on 1,000 examples beats 5 examples in the prompt, and on how many of the same items.

LoRA in one formula, for a frozen linear layer W with d_in inputs and d_out outputs:

```
y = W x + (alpha / r) * B (A x)
A: r x d_in, small random values      B: d_out x r, zeros at the start
only A and B train: r * (d_in + d_out) numbers instead of d_in * d_out
```

mlx-lm puts this on the attention and MLP (multilayer perceptron) projections of the last `--num-layers` blocks. Its config names one multiplier, `scale`, where the paper writes alpha / r.

```
$ python scripts/40_lora_vs_prompting.py --change
(paste your RESULT lines)
```

While `--change` trains, write `LoRALinear()` from the formula above, `trainable_share()` from its docstring, and `exact_match()` from the Exact match term in section 1, no AI. Work in a scratch copy outside the repo, so the rebuild file stays empty until 0:47. The copy's `check()` prints `check: PASS` when all three are right.

```
$ cp rebuild/40_lora_linear.py ~/ml-data/results/lab40/lora_draft.py
$ python ~/ml-data/results/lab40/lora_draft.py
```

## 5. Break it (0:32, 10 min, AI gives hints only; the run finishes by 0:40)

Break: train on the first 100 train rows for 1,000 iterations (40 epochs at batch 4), validating on all 100 validation rows every 25 iterations, and record where validation loss bottoms out. P3 is logged above.

Why: 40 epochs on 100 rows is the common shortcut when labelled rows are scarce, and only the held-out validation loss shows what each extra epoch does.

Precomputed: this run took 16 minutes on the build Mac, over the 6-minute cap, so the session does not run it. After your P3 row exists, the AI reveals its stored RESULT lines from `../../answers/`. Run it after the session if you want the curve on your own Mac.

```
$ python scripts/40_lora_vs_prompting.py --break
(paste your RESULT lines)
```

Why, in three sentences, written without AI:

## 6. Explain-back (0:42, 5 min) and rebuild (0:47, 10 min), no AI

- Five sentences for a smart engineer new to ML, written without AI. The AI names your weakest claim after the session (section 7).
- Rebuild: open `rebuild/40_lora_linear.py` and write `LoRALinear()`, `trainable_share()` and `exact_match()` from memory, without your section 4 draft, then run `python rebuild/40_lora_linear.py`. Its `check()` compares with torch's own `nn.Linear` and `F.linear`, never with this lab's results.

## 7. What I learned

After the session (about 5 minutes): the AI names the weakest claim in your five sentences and asks one question that tests it. Edit the sentences here.

## 8. Interview soundbite (one of the three cards written at 0:57)

> One or two sentences only someone who ran this would say.

Staff follow-up: the trade-off. Hold your section 3 ship rule against §3 of the repo link: what can 100 paired items see and not see, and on how many items would you trust that rule? Answer in 2 sentences from the repo link. Rotate: simplest design, failure modes, migration, what pages at 3 am, cost, trade-off.

## 9. Quiz cards (0:57, 3 min)

The AI drafts three cards (M, N, and T or D). Edit or replace them. Questions go to `../../quiz-bank.md`, keys to `../../answers/quiz-key.md`.

## Record

The script prints these as RESULT lines. Paste, do not type.

| Metric | Your run | Hardware (the script's HW line) | Captured by (script or learner) |
|---|---|---|---|
| `P1.exact_match_pct` (5-shot, percent of the 100 test items) | | | script |
| `baseline.prompt_tokens` (mean tokens per 5-shot prompt) | | | script |
| `P2.em_change_pts` (LoRA minus 5-shot, points) | | | script |
| `P2.flips_to_right` (5-shot wrong, LoRA right) | | | script |
| `P2.flips_to_wrong` (5-shot right, LoRA wrong) | | | script |
| `change.exact_match_pct` (LoRA, zero-shot) | | | script |
| `change.sign_test_p` (exact two-sided sign test on the flips) | | | script |
| `change.ci95_width_pts` (width of the 95% interval of the paired difference, points) | | | script |
| `change.prompt_tokens` (mean tokens per zero-shot prompt) | | | script |
| `change.trainable_pct` (LoRA parameters as a percent of the base model's) | | | script |
| `change.lora_rank` (from the adapter config mlx-lm writes) | | | script |
| `change.lora_scale` (from the same config; set it beside the rebuild's alpha / r) | | | script |
| `change.peak_mem_gb` (peak memory while the 1B trains) | | | script |
| `change.train_tok_per_s` (1B training tokens per second, median of the 10-iteration windows after the first) | | | script |
| `change.tok_s_3b_share` (3B tokens per second over iterations 11 to 30, as a share of the 1B's on the same batches) | | | script |
| `P3.best_iter` (the iteration with the lowest validation loss) | | | script |
| `break.val_loss_start` (validation loss at iteration 1) | | | script |
| `break.val_loss_min` (the lowest validation loss) | | | script |
| `break.val_loss_final` (validation loss at iteration 1,000) | | | script |
| `break.train_loss_final` (mean training loss over iterations 991 to 1,000) | | | script |
