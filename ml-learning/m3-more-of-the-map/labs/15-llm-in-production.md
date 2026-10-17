# 15. LLM in production: latency, schema validity and a regression gate

> Goal: after this I can measure p95 time to first token at 1 and 4 concurrent requests, show what a JSON schema buys, and run a paired regression gate for a prompt change. (No result values anywhere in this file.)

**Level:** S (see `ml-learning/CLAUDE.md`). **Output style:** Explanatory
**Concept link:** [`../README.md#llms-in-production`](../README.md#llms-in-production) (read after the lab)
**Borrowed from:** the [Ollama API docs](https://docs.ollama.com/) for `/api/chat` (`format`, `options`, `stream`, `eval_count`); Chip Huyen, [*AI Engineering*](https://github.com/chiphuyen/aie-book) (O'Reilly, 2025), chapters 3, 4 and 9; [Casanueva et al. 2020, the BANKING77 paper (arXiv 2003.04807)](https://arxiv.org/abs/2003.04807). Do it after the lab, as the second contact 1 to 3 days later.
**Dataset:** BANKING77 (Casanueva et al. 2020), CC BY 4.0: the test split, 3,080 banking queries in 77 intents (40 each), 0.24 MB (239,961 B), <https://raw.githubusercontent.com/PolyAI-LDN/task-specific-datasets/master/banking_data/test.csv>; the train split, 10,003 queries, 0.84 MB (839,073 B), <https://raw.githubusercontent.com/PolyAI-LDN/task-specific-datasets/master/banking_data/train.csv>. The lab sends a stratified sample of 154 test queries (2 per intent, seed 0). Model: Ollama `qwen2.5:7b` (4.7 GB, shared with lab 14)
**Runs on:** cpu+ollama. **Lane:** heavy. **Compute:** 3 runs x at most 4 min (baseline 4, change 3, break 2, rounded up from the reference runs), at most 6 min per run. Precomputed steps: none
**Needs:** base install only (`requests` streams NDJSON, newline-delimited JSON, from `/api/chat`); Ollama 0.18 with `qwen2.5:7b`, no Python package
**Before the session** (from the module folder, see section 2): quit the Ollama menu-bar app if it runs (it holds port 11434). In a second terminal start `OLLAMA_NUM_PARALLEL=4 ollama serve` and leave it running, then `ollama pull qwen2.5:7b` and `curl -s localhost:11434/api/version`. In the lab terminal `export OLLAMA_NUM_PARALLEL=4` (the server reads its own copy; the script records yours), then `python scripts/15_llm_in_production.py --download` (two CSV files into `~/ml-data/banking77/`) and `--smoke`. Quit other heavy apps: every timing is this Mac.
**Interview question:** Your LLM feature has an 8 s p95 and returns malformed JSON 3% of the time: what do you measure, what do you cap, and how does the fix pass a regression gate?
**Repo link:** [`hld/financial-ai-assistant/deep-dives/latency-cost-and-context.md`, §1 Where the time goes](../../../hld/financial-ai-assistant/deep-dives/latency-cost-and-context.md#1-where-the-time-goes) and [§4 Cost per question, and what moves it](../../../hld/financial-ai-assistant/deep-dives/latency-cost-and-context.md#4-cost-per-question-and-what-moves-it); [`hld/financial-ai-assistant/deep-dives/offline-evals-and-rollout.md`, §3 The statistics: what the suite can and cannot see](../../../hld/financial-ai-assistant/deep-dives/offline-evals-and-rollout.md#3-the-statistics-what-the-suite-can-and-cannot-see); [`hld/employee-ops-bundle/deep-dives/expense-assistant.md`, §4 The `QueryPlan` schema](../../../hld/employee-ops-bundle/deep-dives/expense-assistant.md#4-the-queryplan-schema)
**Captured by the script:** P1 to P3 and every Record row. **Human steps:** none (you write the harness prompt, `paired_flips()` and `exact_sign_test()` in section 3)
**Status:** todo

## 0. Retrieval (0:00, 5 min, closed book, no AI)

The AI asks up to three due cards from `../../quiz-bank.md`, one at a time. Do not open the bank first.

## 1. Predict (0:05, 7 min, no AI)

Level S: read `scripts/15_llm_in_production.py` for 2 minutes first. `load_data()`, `check_server()` and `report()` are given; `report()` is the RESULT contract your harness feeds, and `SYSTEM_V1` and `OPTIONS` are fixed.

Write each row here before anything runs; the AI copies it into `../../prediction-log.md` word for word. A row that asks for several numbers becomes one log row per number, each with its own range.

| Step | Question | Kind | Prediction | 80% range or confidence |
|---|---|---|---|---|
| P1 | `qwen2.5:7b` on Ollama 0.18 with `OLLAMA_NUM_PARALLEL=4`, prompt v1 with the JSON schema, the 154 sampled queries at seed 0: p95 time to first token with 4 requests in flight, as a multiple of p95 with 1 in flight | num | | |
| P2 | Prompt v2 (v1 plus one train example per intent: 77 examples, seed 0) vs v1, both with the schema and 1 request in flight, on the same 154 queries: the exact-match change in points (up, down or same, plus a size range), and how many queries flip right to wrong and wrong to right | dir | | |
| P3 | Prompt v1 without the schema (the "Answer in JSON only" instruction stays), the first 48 sampled queries with 8 requests in flight: the share of replies that fail to parse or name an unknown intent | num | | |

**Grading P2.** Hit and Off by use the exact-match change only, by the dir rule in `../../prediction-log.md`: the sign is right and the size is inside your range. Write each flip count as a whole number with its own 80% range in the same row. After the run, each count is marked in or out of its own range (a range, not an exact match). The counts do not change the row's Hit.

Terms, fixed so your numbers compare with the reference:

- **Sample.** 2 test queries per intent (154), drawn per intent with `random_state=seed`, then shuffled with the same seed. That order is the request order. The break sends the first 48 twice, both with 8 requests in flight: first without the schema, then with it.
- **Prompt v1.** The system message is `SYSTEM_V1` followed by the 77 labels in sorted order, one per line. The user message is the query text.
- **Prompt v2.** v1, then a blank line, the line `One example per intent:`, then one line per intent in label order: `<train text, whitespace collapsed> => {"intent": "<label>"}`. The 77 examples are one train query per intent, drawn with `random_state=seed`.
- **Schema.** `format = {"type": "object", "properties": {"intent": {"enum": <the 77 labels>}}, "required": ["intent"]}`. Without the schema, the request has no `format` field at all.
- **Request.** `/api/chat` with `model: qwen2.5:7b`, `stream: true`, `keep_alive: "10m"` and `options` = `OPTIONS` plus `seed`.
- **Concurrency c.** A closed loop: c workers, and each sends its next query as soon as its last reply has finished, so c requests are in flight.
- **Warm-up.** Before each timed pass, max(3, c) untimed calls at the same c, using train queries drawn with the seed. They load the model and put the shared prompt prefix into every server slot.
- **Time to first token (TTFT).** From just before the POST to the first streamed chunk whose `message.content` is not empty. p50 and p95 use `np.percentile` (linear).
- **Tokens per second.** `eval_count / eval_duration` from the final chunk (`done: true`), the median over requests.
- **Mac-seconds per 1,000 requests.** The timed pass's wall seconds, divided by its requests, times 1,000.
- **Valid.** `json.loads` of the reply returns an object whose `"intent"` is one of the 77 labels, character for character. A parse failure is `json.loads` raising. An unknown intent parses, but is not an object, or has no `"intent"`, or names something that is not a label.
- **Exact match.** The valid intent equals the gold `category`. An invalid reply counts as wrong. Exact match and validity come from the c = 1 pass.
- **Flips.** Right to wrong: v1 right, v2 wrong. Wrong to right: v1 wrong, v2 right. `--baseline` saves v1's predictions to `~/ml-data/results/lab15/`, and `--change` reads them, so v1 is not sent again.

## 2. Setup (before the session)

```
$ source ~/.venvs/ml/bin/activate
$ cd m3-more-of-the-map    # from ml-learning/, where sessions start
$ export OLLAMA_NUM_PARALLEL=4
$ python scripts/15_llm_in_production.py --download
$ python scripts/15_llm_in_production.py --smoke
```

The server runs in its own terminal: `OLLAMA_NUM_PARALLEL=4 ollama serve`. `--smoke` checks the given plumbing only (the server and the model, `load_data()` and `report()`). `--baseline`, `--change` and `--break` stop with NotImplementedError until the harness exists.

## 3. Baseline (0:12, 10 min)

Why: users wait for the first token, and a service always runs at some concurrency, so p95 TTFT at the concurrency you expect is the latency number to plan with.

You write first, in this file, no AI (about 5 min). This is the prompt the AI builds from:

1. The sampling rule: which queries, how many, in what order, at which seed.
2. Both prompts, the schema, and the request body.
3. The concurrency plan: which passes run at which c, the warm-ups, and what each pass times (TTFT, tokens per second, wall seconds).
4. The RESULT contract: which `report()` call each mode makes, with which `passes` and `scores` (see its docstring).

Then write `paired_flips(y, pred_a, pred_b)` and `exact_sign_test(n_ab, n_ba)` yourself, in `scripts/15_llm_in_production.py`, from these formulas:

```
n_ab = count of items with pred_a == y and pred_b != y     (right only under a)
n_ba = count of items with pred_a != y and pred_b == y     (right only under b)
n    = n_ab + n_ba                                         (items where a and b agree carry no evidence)
p    = min(1, 2 * sum(comb(n, i) for i in 0 .. min(n_ab, n_ba)) / 2**n)    (two-sided; n = 0 gives 1)
```

The AI then writes the streaming client, the concurrent passes, the timing and the three modes from your prompt. Annotate each AI block with one line before the first run.

`--baseline` sends prompt v1 with the schema twice, once at c = 1 and once at c = 4.

```
$ python scripts/15_llm_in_production.py --baseline
(paste your RESULT lines)
```

Prediction vs actual, one sentence. The reference run is in `../../answers/`; the AI opens it only after your P1 row exists and you have pasted your own RESULT lines.

## 4. Change one thing (0:22, 10 min)

Change: prompt v2, which is v1 plus one train example per intent (77 examples, seed 0), on the same 154 queries, with the schema and 1 request in flight. P2 is logged above.

Why: a prompt change is a release. Only the queries that flip carry evidence, so the gate counts the flips each way and asks the sign test whether that split could come from a fair coin.

```
$ python scripts/15_llm_in_production.py --change
(paste your RESULT lines)
```

## 5. Break it (0:32, 10 min, AI gives hints only; the run finishes by 0:40)

Break: drop the JSON schema and keep the "Answer in JSON only" instruction, then send the first 48 sampled queries with 8 requests in flight. P3 is logged above. Then the same 48 go again with 8 in flight and the schema back on: the matched control.

Why: the schema and the instruction ask for the same JSON in two places, the request's `format` field and the prompt. The two passes differ only in the `format` field: the same 48 queries, the same prompt, the same 8 in flight. So their two valid shares show what the field is worth on this model. The pass without the schema also times TTFT with 8 requests in flight on a server with 4 slots.

```
$ python scripts/15_llm_in_production.py --break
(paste your RESULT lines)
```

Why, in three sentences, written without AI:

## 6. Explain-back (0:42, 5 min) and rebuild (0:47, 10 min), no AI

- Five sentences for a smart engineer new to ML, written without AI. The AI names your weakest claim after the session (section 7).
- Rebuild: open `rebuild/15_paired_gate.py`, write `paired_flips()` and `exact_sign_test()` from memory, then run `python rebuild/15_paired_gate.py`. Its `check()` compares with scikit-learn's `confusion_matrix` and `scipy.stats.binomtest`, never with this lab's results.

## 7. What I learned

After the session (about 5 minutes): the AI names the weakest claim in your five sentences and asks one question that tests it. Edit the sentences here.

## 8. Interview soundbite (one of the three cards written at 0:57)

> One or two sentences only someone who ran this would say.

Staff follow-up: cost. Prompt v2 adds 77 examples to every request: what does that do to the cost of 1,000 requests with and without a prompt cache, and below what hit rate does caching lose money? Answer in 2 sentences from the latency, cost and context deep dive, §4. Rotate: simplest design, failure modes, migration, what pages at 3 am, cost, trade-off.

## 9. Quiz cards (0:57, 3 min)

The AI drafts three cards (M, N, and T or D). Edit or replace them. Questions go to `../../quiz-bank.md`, keys to `../../answers/quiz-key.md`.

## Record

The script prints these as RESULT lines. Paste, do not type. Timing lines carry `device=ollama`, `batch=1` (one query per request), `concurrency=` (requests in flight), `warmup=`, `n=` and `stat=`.

| Metric | Your run | Hardware (the script's HW line) | Captured by (script or learner) |
|---|---|---|---|
| `baseline.ttft_p50_ms_c1` (v1, schema, 1 in flight) | | | script |
| `baseline.ttft_p95_ms_c1` | | | script |
| `baseline.tokens_per_s_c1` | | | script |
| `baseline.mac_s_per_1000_c1` (Mac-seconds per 1,000 requests, 1 in flight) | | | script |
| `baseline.ttft_p50_ms_c4` (v1, schema, 4 in flight) | | | script |
| `baseline.ttft_p95_ms_c4` | | | script |
| `baseline.tokens_per_s_c4` | | | script |
| `baseline.mac_s_per_1000_c4` | | | script |
| `P1.ttft_p95_ratio_c4_c1` | | | script |
| `baseline.exact_match_v1` (fraction of the 154) | | | script |
| `baseline.schema_valid_share` (with the schema) | | | script |
| `baseline.ollama_num_parallel` (your `OLLAMA_NUM_PARALLEL`, or `unset`) | | | script |
| `change.ttft_p50_ms_c1` (v2, schema, 1 in flight) | | | script |
| `change.ttft_p95_ms_c1` | | | script |
| `change.tokens_per_s_c1` | | | script |
| `change.mac_s_per_1000_c1` | | | script |
| `change.exact_match_v2` (fraction of the 154) | | | script |
| `P2.exact_match_delta_pts` (v2 minus v1, points) | | | script |
| `P2.right_to_wrong` (queries) | | | script |
| `P2.wrong_to_right` (queries) | | | script |
| `change.sign_test_p` (two-sided exact sign test) | | | script |
| `break.ttft_p50_ms_c8` (v1, no schema, 8 in flight) | | | script |
| `break.ttft_p95_ms_c8` | | | script |
| `break.tokens_per_s_c8` | | | script |
| `break.mac_s_per_1000_c8` | | | script |
| `P3.invalid_share` (parse failures plus unknown intents, of 48) | | | script |
| `break.parse_fail_share` | | | script |
| `break.unknown_intent_share` | | | script |
| `break.schema_valid_share` (without the schema) | | | script |
| `break.with_schema_valid_share` (the matched control: the same 48 with 8 in flight, with the schema) | | | script |
