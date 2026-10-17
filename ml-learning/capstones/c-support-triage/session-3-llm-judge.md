# C3. An LLM judge on disputed predictions: qwen2.5:7b against gold labels

> Goal: after this I can pick 50 test queries where C1 and C2 disagree, ask a local `qwen2.5:7b` judge which of the two intents fits, in both answer orders, and measure its agreement with gold labels, its flip rate under a swap, and its tokens and seconds per item. (No result values anywhere in this file. Capstones have no reference run and no answers file: your run is the answer.)

**Capstone:** [C, support triage with retrieval and a small LLM](README.md), session 3 of 4, labkit id 51. **Level:** B (see `ml-learning/CLAUDE.md`). **Output style:** Explanatory
**Builds on:** lab 14 (an LLM judge against human labels, both orders) and lab 15 (BANKING77 through Ollama with a JSON schema), plus your C1 and C2 predictions
**Dataset:** BANKING77 test queries where C1 and C2 disagree, CC BY 4.0 ([Data](README.md#data)); judge `qwen2.5:7b` through Ollama (4.68 GB, Apache-2.0)
**Runs on:** cpu+ollama. **Lane:** heavy: one Ollama job at a time. **Compute:** no reference run; 2 runs of 100 judge calls, each capped at 6 min. Precomputed steps: none
**Needs:** base install only (Ollama over HTTP with requests), plus Ollama 0.18 with `qwen2.5:7b`
**Before the session:** `ollama serve`, `ollama pull qwen2.5:7b` (skip it if labs 14 and 15 pulled it), `curl -s localhost:11434/api/version`, then `--download` and `--smoke`.
**Interview question:** Can an LLM settle the cases where two classifiers disagree, and how do you know when to trust it?
**Repo link:** [`hld/financial-ai-assistant/deep-dives/offline-evals-and-rollout.md`, §5 The judge, and how far to trust it](../../../hld/financial-ai-assistant/deep-dives/offline-evals-and-rollout.md#5-the-judge-and-how-far-to-trust-it)
**Captured by the script:** P1 to P3 and every Record row. **Human steps:** both judge prompts, the design and the write-up
**Status:** todo

## 0. Framing (0:00, 7 min, no AI)

Reread your framing line in `write-up.md`. Under it, write one line on the judge's job: which queries reach it, what it may decide, and who checks it.

## 1. Predict (0:07, 5 min, no AI)

Write each row here and in `../../prediction-log.md` (Lab `C3`) before anything runs.

| Step | Question | Kind | Prediction | 80% range or confidence |
|---|---|---|---|---|
| P1 | Agreement with gold, in % of the 50 disputed queries, of `qwen2.5:7b` with your prompt v1 in order 1 (intent A = C1's word TF-IDF prediction, intent B = C2's kNN prediction, a verdict of A or B), temperature 0, seed 42 | num | | |
| P2 | Prompt v2, which adds 3 training queries for each candidate intent (seed 0): agreement in order 1 minus P1, in points (up, down or same, plus a size range), and the flips each way | dir | | |
| P3 | Swap A and B (order 2) and judge the same 50 with prompt v1: the share of the 50 whose chosen intent changes, as a percent | num | | |

Terms, fixed so the two prompts compare:

- **Disputed.** Test queries where C1's word model and C2's kNN predict different intents and the gold intent is one of the two, so a verdict can be graded. Draw 50 with seed 0. Record how many disputed queries exist, and how many had gold in neither.
- **Judge call.** `POST /api/chat` on `OLLAMA_HOST` (default `127.0.0.1:11434`), `stream: false`, `options: {temperature: 0, seed: 42}`, `keep_alive: "10m"`, and `format` set to a JSON schema whose only field is `verdict` with the enum `["A", "B"]`. Three warm-up calls are excluded.
- **Prompts.** You write v1 and v2 in section 3: the query, the two intent names as A and B, and the question. v2 adds 3 training queries per candidate intent, drawn with seed 0, never a test query.
- **Orders.** Order 1: A is C1's intent, B is C2's. Order 2: swapped.
- **Agreement.** The share of the 50 where the chosen intent equals gold.
- **Flip.** The chosen intent differs between order 1 and order 2.
- **Cost per item.** Prompt and output tokens from `prompt_eval_count` and `eval_count`, seconds from `total_duration`. Mac-seconds per 1,000 judged queries = the mean seconds per item x 1,000, one call at a time.

## 2. Setup (before the session)

```
$ ollama serve
$ ollama pull qwen2.5:7b
$ curl -s localhost:11434/api/version
$ source ~/.venvs/ml/bin/activate
$ cd ml-learning/capstones/c-support-triage
$ python scripts/c3_llm_judge.py --download
$ python scripts/c3_llm_judge.py --smoke
```

`--download` checks C1's and C2's saved predictions and that the server answers, and prints the disputed count only. `--smoke` sends 3 calls and prints `SMOKE` lines, never a verdict.

## 3. Baseline (0:12, 15 min)

Why: a judge is worth asking only on the queries C1 and C2 dispute, and only if it beats a coin and does not follow the answer order.

You write first, in this file, no AI (about 5 min). This is the prompt the AI builds from:

1. Prompt v1 and prompt v2, word for word, and the JSON schema.
2. The disputed-query rule, the draw, both orders, and how agreement and flips are counted.
3. The RESULT contract: every name in the Record table, the mode that prints it, and its unit.

The AI then writes the HTTP client and the report with `labkit.start(lab=51)`. Annotate each AI block with one line before the first run. `--baseline` judges the 50 in both orders with v1, 100 calls.

```
$ python scripts/c3_llm_judge.py --smoke
$ python scripts/c3_llm_judge.py --baseline
(paste your RESULT lines)
```

Prediction vs actual, one sentence each for P1 and P3. There is no reference run: the AI fills Actual and Hit from your pasted lines.

## 4. Change one thing (0:27, 15 min; the run finishes by 0:40)

Change: prompt v2 replaces v1, with 3 training queries for each candidate intent. The 50 queries, both orders, the model and its options stay fixed. P2 is logged above.

Why: the change shows the judge what customers actually wrote under each intent, and it costs more prompt tokens on every call.

```
$ python scripts/c3_llm_judge.py --change
(paste your RESULT lines)
```

Prediction vs actual, one sentence.

## 5. Write-up (0:42, 15 min, no AI)

- **Explain-back (5 min).** Five sentences for a smart engineer new to ML. Then ask the AI for the weakest claim, not a rewrite.
- **Deliverable (10 min).** Add §2 The judge to `write-up.md`: agreement with gold in both orders for both prompts, the flip rate, tokens and Mac-seconds per 1,000 judged queries, and your rule for when this judge may settle a dispute.

## 6. What I learned

The five explain-back sentences, edited after the AI's question.

## 7. Interview soundbite (the card written at 0:57)

> One or two sentences only someone who ran this would say.

Framing: decision ___ | prediction time ___ | label and its maturity ___ | offline metric ___ | online metric ___ | guardrail ___

Staff follow-up (failure modes): what agreement would let this judge settle disputes in production, and against which human baseline? Answer in 2 sentences from the repo link (its calibration rule).

## 8. Close (0:57, 3 min)

The AI drafts card `C3-T` (the payments version or a variant you did not run) from your run. Edit or replace it. The question goes to `../../quiz-bank.md`, the key to `../../answers/quiz-key.md`, citing your RESULT line. Set Status here and in the [README](README.md#sessions).

## Record

Suggested names: if your RESULT contract renames them, edit this table first. Paste, do not type.

| Metric | Your run | Hardware (the script's HW line) | Captured by (script or learner) |
|---|---|---|---|
| `baseline.disputed_total` and `baseline.gold_in_neither` (test queries) | | | script |
| `P1.agreement_pct` (v1, order 1) | | | script |
| `baseline.agreement_pct_order2` (v1, order 2) | | | script |
| `P3.flip_rate` (v1, percent of 50) | | | script |
| `baseline.prompt_tokens` and `baseline.output_tokens` (v1, mean per item) | | | script |
| `baseline.sec_per_item` and `baseline.mac_sec_per_1k` (v1, M4 Pro, Ollama, one call at a time) | | | script |
| `change.agreement_pct` and `change.agreement_pct_order2` (v2) | | | script |
| `P2.agreement_change_pts` (v2 minus v1, order 1) | | | script |
| `change.flips_to_right`, `change.flips_to_wrong` and `change.sign_test_p` (v2 against v1, order 1) | | | script |
| `change.flip_rate` (v2) | | | script |
| `change.prompt_tokens` and `change.mac_sec_per_1k` (v2) | | | script |
