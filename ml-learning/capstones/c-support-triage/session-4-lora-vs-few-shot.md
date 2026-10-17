# C4. LoRA vs 5-shot prompting: Llama 3.2 1B 4-bit on 231 support queries

> Goal: after this I can score a 5-shot prompt and a LoRA (low-rank adaptation) adapter for `mlx-community/Llama-3.2-1B-Instruct-4bit` on the same 231 BANKING77 test queries, 3 per intent, compare them with an exact paired sign test, and complete the 4-method table with tokens and Mac-seconds per 1,000 queries. (No result values anywhere in this file. Capstones have no reference run and no answers file: your run is the answer.)

**Capstone:** [C, support triage with retrieval and a small LLM](README.md), session 4 of 4, labkit id 52. **Level:** B (see `ml-learning/CLAUDE.md`). **Output style:** Explanatory
**Builds on:** lab 40 (LoRA on this model against a 5-shot prompt, with a sign test), plus your C1 and C2 predictions
**Dataset:** BANKING77, 10,003 train queries for LoRA and a 231-query test sample, CC BY 4.0 ([Data](README.md#data)); model `mlx-community/Llama-3.2-1B-Instruct-4bit` (695.3 MB, Llama 3.2 Community License, ungated)
**Runs on:** mlx. **Lane:** heavy. **Compute:** no reference run; 2 measured runs, each capped at 6 min, the LoRA training included. Precomputed steps: none
**Needs:** `python -m pip install mlx==0.32.4 mlx-lm==0.32.2` (lab 40's pins; the mlx 0.32.4 wheel is tagged macOS 26)
**Before the session:** C1 and C2 done at seed 0. `--download` (the model, if lab 40 has not put it in `~/ml-data/hf/`), then `--smoke`, which trains 20 iterations and prints seconds per iteration. Set N from it (Terms) and write N into P2 before you predict.
**Interview question:** Prompting or fine-tuning a small model for intent routing: what paired evidence decides, and what does each cost per 1,000 queries?
**Repo link:** [`hld/financial-ai-assistant/deep-dives/offline-evals-and-rollout.md`, §3 The statistics: what the suite can and cannot see](../../../hld/financial-ai-assistant/deep-dives/offline-evals-and-rollout.md#3-the-statistics-what-the-suite-can-and-cannot-see); [`deep-dives/latency-cost-and-context.md`, §4 Cost per question, and what moves it](../../../hld/financial-ai-assistant/deep-dives/latency-cost-and-context.md#4-cost-per-question-and-what-moves-it)
**Captured by the script:** P1 to P3 and every Record row. **Human steps:** the eval protocol, N, the design and the write-up
**Status:** todo

## 0. Framing (0:00, 7 min, no AI)

Reread your framing line in `write-up.md`. Under it, write one line on what this session decides: whether a 1B model belongs in the router at all, and as the first pass or the fallback.

## 1. Predict (0:07, 5 min, no AI)

Write each row here and in `../../prediction-log.md` (Lab `C4`) before anything runs. Exact match is a percent of the 231 items; its changes are in points.

| Step | Question | Kind | Prediction | 80% range or confidence |
|---|---|---|---|---|
| P1 | Exact match for the 1B 4-bit model with the 5-shot prompt in Terms, greedy, at most 16 new tokens, on the 231 items | num | | |
| P2 | A LoRA adapter for N = ___ iterations (batch 4, 16 layers, max sequence length 128, on the 10,003 train queries), then the zero-shot prompt on the same 231 items: exact match minus P1 (up, down or same, plus a size range), and the flips each way | dir | | |
| P3 | The share of the 231 5-shot outputs that name no valid intent (not one of the 77 labels after normalization), as a percent | num | | |

Terms, fixed so the four methods compare on the same items:

- **Items.** 231 test queries, 3 per intent, drawn once with `numpy.random.default_rng(0)`. C1's and C2's saved predictions are restricted to the same 231 for the 4-method table.
- **Labels and normalization.** BANKING77's `category` strings, for example `card_arrival`. Normalize by lowercasing, trimming, and turning spaces into underscores.
- **5-shot prompt.** One line listing the 77 labels, then the first 5 train rows as `Query: <text>` and `Intent: <label>` blocks, then `Query: <item>` and `Intent:`. Raw text with no chat template, the format LoRA trains on (lab 40's choice).
- **Zero-shot prompt.** `Query: <item>` and `Intent:` alone. The LoRA model gets this one.
- **Prediction.** The first line of the output, normalized. Exact match: it equals the gold label. Invalid: it is not one of the 77.
- **N.** N = min(2,500, the iterations that fit 3.5 minutes), from the seconds per iteration that `--smoke` prints. 2,500 iterations at batch 4 is one pass over the 10,003 rows. N is a configuration, not a result: write it into P2.
- **Paired test.** Flips each way, the exact two-sided sign test (`scipy.stats.binomtest`), and the width of the 95% interval of the paired difference, as in lab 40.
- **Cost.** Tokens per query: prompt plus output tokens, from the tokenizer. Mac-seconds per 1,000 queries: wall seconds for all 231 items x 1,000 / 231, one process, one query at a time. LoRA's training time is recorded apart.
- **The 4-method table.** `--change` prints it as TABLE lines on the 231 items: C1's word TF-IDF, C2's kNN, 5-shot and LoRA, with accuracy, macro-F1, flips against TF-IDF each way, the sign-test p-value, tokens per query (none for TF-IDF and kNN, which run no LLM) and Mac-seconds per 1,000 queries (C1's and C2's from their Record tables).

## 2. Setup (before the session)

```
$ source ~/.venvs/ml/bin/activate
$ python -m pip install mlx==0.32.4 mlx-lm==0.32.2
$ cd ml-learning/capstones/c-support-triage
$ python scripts/c4_lora_vs_few_shot.py --download
$ python scripts/c4_lora_vs_few_shot.py --smoke
```

`--smoke` checks the plumbing only: the 231 items draw, the model generates for 3 of them, mlx-lm trains for 20 iterations and prints seconds per iteration (the one timing smoke may show: it sets N), and the RESULT contract parses.

## 3. Baseline (0:12, 15 min)

Why: a fine-tune earns its cost only if it beats the cheapest prompt that could work, on the same items.

You write first, in this file, no AI (about 5 min). This is the prompt the AI builds from:

1. The eval protocol: the items, the prompt formats, what counts as the prediction, the normalization and the invalid rule.
2. The paired test, and how the 4-method table joins C1's and C2's predictions to the same 231 items.
3. The RESULT contract: every name in the Record table, the mode that prints it, and its unit.

The AI then writes the generation loop and the mlx-lm calls with `labkit.start(lab=52, device="mlx")`. Annotate each AI block with one line before the first run.

```
$ python scripts/c4_lora_vs_few_shot.py --smoke
$ python scripts/c4_lora_vs_few_shot.py --baseline
(paste your RESULT lines)
```

Prediction vs actual, one sentence each for P1 and P3. There is no reference run: the AI fills Actual and Hit from your pasted lines.

## 4. Change one thing (0:27, 15 min; the run finishes by 0:40)

Change: a LoRA adapter replaces the 5-shot prompt. Train it with mlx-lm on the 10,003 train queries for N iterations (`--batch-size 4 --num-layers 16 --max-seq-length 128`, every other flag at mlx-lm's default), then score the zero-shot prompt on the same 231 items and pair them with the baseline item by item. P2 is logged above.

Why: LoRA trains two small matrices beside each frozen 4-bit weight, and the only question is whether that beats 5 examples in the prompt on the same items.

```
$ python scripts/c4_lora_vs_few_shot.py --change
(paste your RESULT lines)
```

Prediction vs actual, one sentence.

## 5. Write-up (0:42, 15 min, no AI)

- **Explain-back (5 min).** Five sentences for a smart engineer new to ML. Then ask the AI for the weakest claim, not a rewrite.
- **Deliverable (10 min).** Finish `write-up.md`: §1 the 4-method table on the 231 items (TF-IDF and kNN also on all 3,080), and §3 the router decision in 3 sentences, citing your numbers and the README's HLD sections. Capstone C is done when its 3 parts exist.

## 6. What I learned

The five explain-back sentences, edited after the AI's question.

## 7. Interview soundbite (the card written at 0:57)

> One or two sentences only someone who ran this would say.

Framing: decision ___ | prediction time ___ | label and its maturity ___ | offline metric ___ | online metric ___ | guardrail ___

Staff follow-up (trade-off): ship the adapter or the prompt? What paired result on how many items decides, and what does each cost per 1,000 queries? Answer in 2 sentences from the repo links (§3, then §4).

## 8. Close (0:57, 3 min)

The AI drafts card `C4-D` (a symptom and the first check) from your run. Edit or replace it. The question goes to `../../quiz-bank.md`, the key to `../../answers/quiz-key.md`, citing your RESULT line. Set Status here and in the [README](README.md#sessions).

## Record

Suggested names: if your RESULT contract renames them, edit this table first. Paste, do not type.

| Metric | Your run | Hardware (the script's HW line) | Captured by (script or learner) |
|---|---|---|---|
| N, from the smoke's seconds per iteration | | | learner |
| `P1.exact_match_pct` (5-shot, percent of 231) | | | script |
| `baseline.macro_f1` (5-shot, 231 items) | | | script |
| `P3.invalid_share` (5-shot outputs naming no valid intent, percent) | | | script |
| `baseline.prompt_tokens` and `baseline.output_tokens` (5-shot, mean per query) | | | script |
| `baseline.mac_sec_per_1k` (5-shot, M4 Pro, mlx, one query at a time) | | | script |
| `change.iters` (N, as trained) | | | script |
| `change.train_s`, `change.train_tok_per_s` and `change.peak_mem_gb` (LoRA training) | | | script |
| `change.exact_match_pct` and `change.macro_f1` (LoRA, zero-shot) | | | script |
| `P2.em_change_pts` (LoRA minus 5-shot) | | | script |
| `change.flips_to_right`, `change.flips_to_wrong`, `change.sign_test_p` and `change.ci95_width_pts` | | | script |
| `change.invalid_share` (LoRA) | | | script |
| `change.prompt_tokens` and `change.mac_sec_per_1k` (LoRA, zero-shot) | | | script |
| The 4-method table on the 231 items (TABLE lines) | | | script |
