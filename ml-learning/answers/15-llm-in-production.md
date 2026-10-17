# 15. LLM in production: latency, schema validity and a regression gate: reference answers

> Spoilers. The AI opens one block at a time, only after that step's prediction row exists and the learner pasted their own RESULT lines, or after 'debrief 15'.

- **HW:** `HW chip='Apple M4 Pro' cpu=14 gpu=20 mem_gib=24 macos=26.5.1 python=3.13.7 torch=2.14.1 device=cpu`. The script's own work is CPU. Every timing is the Ollama 0.18.0 server on the same Mac: `qwen2.5:7b` (Q4_K_M) with all 29 layers on the Metal GPU, 4 parallel slots, context 4,096 per slot.
- **Seeds:** 0 (the learner's default), 1 and 2. A seed picks the 154 queries, their order, the 77 few-shot examples and the warm-up queries.
- **Reference script:** `answers/15_llm_in_production_ref.py` (sha256 prefix `5fcd56240fe4decc`). Raw seed-0 output: `answers/15-llm-in-production.out`.
- **Runs and wall times:** baseline 208.6 s (seed 0), 245.0 s (seed 1), 253.3 s (seed 2); change 152.9 s, 157.2 s, 161.8 s (seeds 0, 1, 2); break 78.4 s (seed 0, both of its passes). All in the heavy lane.
- **Tolerance rule (from the .json):** tol = spread (max - min) over seeds 0, 1, 2; heavy labs: the baseline spread applies to every step. So P1 takes its own baseline spread, P2 the baseline spread of exact match in points, and P3 the baseline spread of the valid share (each block says how). Change also ran at seeds 1 and 2, but only to check P2's direction: their range is shown, and it is not a tolerance. The break ran at seed 0 only.
- **Reproducibility:** replies are deterministic at temperature 0 on this Mac. Three seed-0 baseline runs hours apart gave the same exact match (0.597403). The full rerun for this version repeated every exact match, flip count and sign-test p at all three seeds, and the break's split. So a learner's P2 and P3 at seed 0 should match the reference or miss by a query or two. P1 is a timing and moves with load on the Mac.

<details><summary>P1. p95 time to first token with 4 requests in flight, as a multiple of p95 with 1 in flight (qwen2.5:7b, OLLAMA_NUM_PARALLEL=4, prompt v1 with the schema, 154 queries, seed 0)</summary>

**Answer:** 3.39888, tolerance 0.57429 (the baseline seed spread). Seeds 0, 1, 2: 3.39888, 2.82459, 2.8645.

Seed-0 RESULT lines:

```
RESULT baseline.ttft_p50_ms_c1=211.142 unit=ms stat=p50 device=ollama batch=1 concurrency=1 warmup=3 n=154 seed=0
RESULT baseline.ttft_p95_ms_c1=251.607 unit=ms stat=p95 device=ollama batch=1 concurrency=1 warmup=3 n=154 seed=0
RESULT baseline.tokens_per_s_c1=50.1932 unit=tokens_per_s stat=median device=ollama batch=1 concurrency=1 warmup=3 n=154 seed=0
RESULT baseline.mac_s_per_1000_c1=657.536 unit=s device=ollama batch=1 concurrency=1 warmup=3 n=154 seed=0
RESULT baseline.ttft_p50_ms_c4=643.986 unit=ms stat=p50 device=ollama batch=1 concurrency=4 warmup=4 n=154 seed=0
RESULT baseline.ttft_p95_ms_c4=855.182 unit=ms stat=p95 device=ollama batch=1 concurrency=4 warmup=4 n=154 seed=0
RESULT baseline.tokens_per_s_c4=6.82613 unit=tokens_per_s stat=median device=ollama batch=1 concurrency=4 warmup=4 n=154 seed=0
RESULT baseline.mac_s_per_1000_c4=659.687 unit=s device=ollama batch=1 concurrency=4 warmup=4 n=154 seed=0
RESULT P1.ttft_p95_ratio_c4_c1=3.39888 unit=ratio seed=0
RESULT baseline.exact_match_v1=0.597403 unit=fraction seed=0
RESULT baseline.schema_valid_share=1 unit=fraction seed=0
RESULT baseline.ollama_num_parallel=4 seed=0
```

Other seeds:

| Value | Seed 1 | Seed 2 | Spread |
|---|---|---|---|
| `baseline.ttft_p50_ms_c1` | 261.612 | 277.337 | 66.195 |
| `baseline.ttft_p95_ms_c1` | 340.021 | 355.925 | 104.31800000000001 |
| `baseline.tokens_per_s_c1` | 49.0014 | 47.1324 | 3.0608000000000004 |
| `baseline.mac_s_per_1000_c1` | 842.784 | 875.716 | 218.18000000000006 |
| `baseline.ttft_p50_ms_c4` | 667.064 | 707.64 | 63.653999999999996 |
| `baseline.ttft_p95_ms_c4` | 960.42 | 1019.55 | 164.36799999999994 |
| `baseline.tokens_per_s_c4` | 6.33283 | 6.64964 | 0.4932999999999996 |
| `baseline.mac_s_per_1000_c4` | 702.049 | 720.964 | 61.277000000000044 |
| `P1.ttft_p95_ratio_c4_c1` | 2.82459 | 2.8645 | 0.57429 |
| `baseline.exact_match_v1` | 0.616883 | 0.584416 | 0.03246699999999991 |
| `baseline.schema_valid_share` | 1 | 1 | 0 |
| `baseline.ollama_num_parallel` | 4 | 4 | 0 |

**Why.** The 4 slots do run together, but they share one GPU, and on this Mac the server got little extra throughput from them. At seed 0, Mac-seconds per 1,000 requests were 657.536 at 1 in flight and 659.687 at 4, while each request's output speed fell from 50.1932 to 6.82613 tokens per second. Seeds 1 and 2 gained about a fifth in throughput: their Mac-seconds per 1,000 fell from 842.784 to 702.049 and from 875.716 to 720.964. With throughput up by a fifth at most, Little's law (requests in flight = throughput x time per request) says 4 in flight make every request take 3 to 4 times as long. The first token is the front of that: the new query's prefill runs in GPU steps shared with three other requests, so it arrives about 3 times later.

**Common wrong prediction:** 1x, because 4 slots hold 4 requests and nothing waits. Or 4x, because the requests run one at a time. The slots do run at once; what they share is the GPU, whose throughput grew by a fifth at most.

The absolute timings move between runs. Here seed 0's p95 at 1 in flight was the lowest of the three (251.607 ms, against 340.021 and 355.925), and its p95 at 4 in flight sat less far below the others, so its ratio is the highest. Every run shared the Mac with jobs from other builds (see Build notes).

</details>

<details><summary>P2. Prompt v2 (v1 plus one train example per intent, 77 examples, seed 0) vs v1, both with the schema and 1 in flight, same 154 queries: exact-match change in points, and how many queries flip each way</summary>

**Answer:** up. +5.19481 points (v1 0.597403, v2 0.649351). 7 queries flip right to wrong and 15 wrong to right. The exact sign test gives a two-sided p of 0.133801.

**Tolerance**, by the heavy-lane rule: the baseline spread of exact match. `baseline.exact_match_v1` spread is 0.03246699999999991 as a fraction of the 154 queries, so 3.25 points in P2's units. The flip counts have no baseline counterpart. Each is marked against the learner's own range, as Grading P2 in the lab file says. Change also ran at seeds 1 and 2, only to check the direction: it was up at all three seeds.

Seed-0 RESULT lines:

```
RESULT change.ttft_p50_ms_c1=297.706 unit=ms stat=p50 device=ollama batch=1 concurrency=1 warmup=3 n=154 seed=0
RESULT change.ttft_p95_ms_c1=368.994 unit=ms stat=p95 device=ollama batch=1 concurrency=1 warmup=3 n=154 seed=0
RESULT change.tokens_per_s_c1=46.1937 unit=tokens_per_s stat=median device=ollama batch=1 concurrency=1 warmup=3 n=154 seed=0
RESULT change.mac_s_per_1000_c1=893.504 unit=s device=ollama batch=1 concurrency=1 warmup=3 n=154 seed=0
RESULT change.exact_match_v2=0.649351 unit=fraction seed=0
RESULT P2.exact_match_delta_pts=5.19481 unit=points seed=0
RESULT P2.right_to_wrong=7 unit=queries seed=0
RESULT P2.wrong_to_right=15 unit=queries seed=0
RESULT change.sign_test_p=0.133801 unit=p_two_sided seed=0
```

Other seeds (each seed draws its own 154 queries and its own 77 examples). The last column shows how far each value moved over seeds 0, 1 and 2. It is not P2's tolerance.

| Value | Seed 1 | Seed 2 | Range over seeds |
|---|---|---|---|
| `change.ttft_p50_ms_c1` | 300.911 | 310.441 | 12.734999999999957 |
| `change.ttft_p95_ms_c1` | 417.862 | 419.62 | 50.625999999999976 |
| `change.tokens_per_s_c1` | 45.6924 | 45.4497 | 0.7439999999999998 |
| `change.mac_s_per_1000_c1` | 928.152 | 952.862 | 59.35799999999995 |
| `change.exact_match_v2` | 0.75974 | 0.662338 | 0.11038899999999996 |
| `P2.exact_match_delta_pts` | 14.2857 | 7.79221 | 9.09089 |
| `P2.right_to_wrong` | 4 | 3 | 4 |
| `P2.wrong_to_right` | 26 | 15 | 11 |
| `change.sign_test_p` | 5.94761e-05 | 0.00753784 | 0.1337415239 |

**Why.** The 77 intents are fine grained: 10 labels start with `card_` and 6 with `top_up_`. One customer phrasing per label helps the model pick between near neighbours, so 15 queries moved to the right label. A single example can also pull a query toward the wrong neighbour, so 7 moved the other way. Only those 22 discordant queries carry evidence. A fair coin splits 22 tosses at least as unevenly as 15 to 7 with p = 0.133801, so at seed 0 the gate cannot call v2 better. It finds no sign of a regression either: fewer queries broke than were fixed. Seeds 1 and 2 drew other queries and other examples, gained more, and the sign test called those gains significant (p of 5.94761e-05 and 0.00753784). The size of a few-shot gain depends on which examples you draw.

**Common wrong prediction:** a large gain with almost no queries flipping the other way, because "examples only add information". Or calling +5 points on 154 items a win without the sign test. Here 7 of the 22 flips at seed 0 went the wrong way, and the gate could not separate the gain from chance.

Cost, for the Staff follow-up: v2's system message carries 77 example lines on top of v1's 77 labels, so every call sends a much longer prompt. Its Mac-seconds per 1,000 at 1 in flight were 893.504 against v1's 657.536 at seed 0, and v2 cost more at seeds 1 and 2 as well. The server's prefix cache keeps the long shared system prompt warm, so no timed request pays its full prefill: the warm-up calls absorb it (see Build notes). What v2 still pays on every call is the longer context. Its p50 time to first token was higher and its tokens per second lower than v1's at all three seeds (this table and P1's). A cold cache would pay the full prefill on top.

</details>

<details><summary>P3. Prompt v1 without the schema (the instruction stays), the first 48 sampled queries with 8 in flight: the share of replies that fail to parse or name an unknown intent</summary>

**Answer:** 0.0416667 (2 of 48), the absolute share the question asks for. Both were unknown intents. There were 0 parse failures. The valid share without the schema was 0.958333. The matched control sent the same 48 queries with the same prompt and the same 8 in flight, with the schema on. Its valid share was 1. The two passes differ only in the `format` field, so on these 48 queries the schema is what turned those 2 replies valid.

**Tolerance**, by the heavy-lane rule: the baseline spread of the valid share, `baseline.schema_valid_share`, which is 0. That spread comes from passes with the schema on, where decoding cannot leave the list. So it cannot say how far the share without the schema moves. The break ran at seed 0 only. Read P3 at its resolution instead: one reply moves it by 1/48. The count describes this one run on these 48 queries. It is not an estimate of a production rate.

Seed-0 RESULT lines:

```
RESULT break.ttft_p50_ms_c8=3220.04 unit=ms stat=p50 device=ollama batch=1 concurrency=8 warmup=8 n=48 seed=0
RESULT break.ttft_p95_ms_c8=4507.26 unit=ms stat=p95 device=ollama batch=1 concurrency=8 warmup=8 n=48 seed=0
RESULT break.tokens_per_s_c8=5.87115 unit=tokens_per_s stat=median device=ollama batch=1 concurrency=8 warmup=8 n=48 seed=0
RESULT break.mac_s_per_1000_c8=651.755 unit=s device=ollama batch=1 concurrency=8 warmup=8 n=48 seed=0
RESULT P3.invalid_share=0.0416667 unit=fraction seed=0
RESULT break.parse_fail_share=0 unit=fraction seed=0
RESULT break.unknown_intent_share=0.0416667 unit=fraction seed=0
RESULT break.schema_valid_share=0.958333 unit=fraction seed=0
RESULT break.with_schema_valid_share=1 unit=fraction seed=0
```

Other seeds: none (heavy lane: the break runs at seed 0 only).

**Why.** Without the schema, nothing in decoding ties the label to the list. qwen2.5:7b at temperature 0 still wrote well-formed JSON every time in this pass, so the failures were names, not syntax: 2 replies named a label that is not one of the 77. Probe 3 replayed the earlier seed-0 break and printed both (see Build notes); this run gave the same split. Both were near misses that blend real labels: `getting_physical_card` (the list has `get_physical_card` and `getting_spare_card`) and `get_virtual_card` (the list has `getting_virtual_card` and `get_disposable_virtual_card`). With the schema, the `enum` in `format` masks every token that would leave the list, so a reply can only hold a listed label, right or wrong. In the replay, the schema pass at 1 in flight gave those two queries `getting_spare_card` and `get_disposable_virtual_card`: both listed, both wrong. On this model the instruction alone got 46 of the 48 replies valid, and the schema, on the same queries at the same 8 in flight, got all 48. The interview question's 3% is that prompt's hypothetical. This run can neither confirm it nor set a production rate.

**Common wrong prediction:** 10% to 30% broken JSON, or exactly 0 because the model follows the instruction. Here the JSON never broke; the label did. A parser that only calls `json.loads` would have passed both bad replies.

TTFT at 8 in flight (3220.04 ms p50 at seed 0) is mostly queueing: the server has 4 slots, so half the requests wait for one to free before their prefill starts. These timings come from the pass without the schema (the control prints no timings), so compare them with the baseline's only loosely.

</details>

<details><summary>Rebuild check</summary>

- Stub: `m3-more-of-the-map/rebuild/15_paired_gate.py`. Solution: `answers/rebuild/15_paired_gate.py`.
- `rebuildcheck`: the stub fails as it should (exit 1, NotImplementedError), the solution passes (exit 0, `check: PASS`). Verdict: REBUILDCHECK OK.
- `check()` compares `paired_flips()` with `sklearn.metrics.confusion_matrix` on 50 random label sets of 40 items, and `exact_sign_test()` with `scipy.stats.binomtest(k, n, 0.5).pvalue` on 964 `(n_ab, n_ba)` pairs to 1e-12 (n = 0 must give 1).

</details>

<details><summary>Card drafts</summary>

| ID | Lab | Type | Question |
|---|---|---|---|
| 15-M | 15 | M | Why can a JSON schema in Ollama's `format` field guarantee a reply that parses and names a listed label, when the same request written in the prompt cannot? |
| 15-N | 15 | N | On the M4 Pro with 4 Ollama slots, what multiple of the 1-request p95 time to first token did 4 requests in flight cost in the reference run, and what did Mac-seconds per 1,000 requests show about why? |
| 15-D | 15 | D | After a client refactor, your intent service's validator starts rejecting a few replies in every hundred, though most still pass. What do you check first in the request, and what second? |

Key:

| ID | Answer | Must mention |
|---|---|---|
| 15-M | The schema turns on constrained decoding: at each step the server allows only tokens that keep the output valid against the schema, and an `enum` allows only the listed labels. An instruction in the prompt only shifts probabilities, so the model can still drift. | 1) the server masks invalid tokens at every decoding step; 2) the enum limits the label to the list; 3) the instruction enforces nothing |
| 15-N | About 3x: 3.39888 at seed 0, 2.82459 to 3.39888 over seeds 0 to 2. Mac-seconds per 1,000 requests barely moved (657.536 at 1 in flight, 659.687 at 4, seed 0), so the 4 slots shared one GPU's throughput and each request waited behind the others. | 1) about 3x; 2) throughput nearly flat; 3) the slots share one GPU, so requests wait for it |
| 15-D | First: does the request still send the schema in `format`? Without it, the model can write a label outside the list (here 2 of 48 did, and 0 of the same 48 with the schema) or broken JSON. Second: `done_reason` of `length`, which means the output cap cut the reply. | 1) the schema in `format` is present; 2) the validator rejects labels outside the list; 3) `done_reason` length, the output cap |

T alternative, if the last close drew D:

| ID | Lab | Type | Question |
|---|---|---|---|
| 15-T | 15 | T | A dispute-reason classifier on a hosted API has an 8 s p95 at peak. Which two levers from this lab cut it, and what does each cost? |

| ID | Answer | Must mention |
|---|---|---|
| 15-T | Cap output tokens: fewer decode steps, but a cut reply can break the JSON, so keep the schema. Cut requests in flight per replica, or add replicas: by Little's law each request then waits less, at the price of capacity or money. | 1) an output cap; 2) fewer requests in flight per replica, or more replicas; 3) what each one costs |

</details>

<details><summary>Build notes</summary>

- **Knob changes:** none. The spec's configuration ran as written: 154 queries (2 per intent), 77 examples, 48 queries at 8 in flight for the break.
- **Precomputed steps:** none. The longest run, baseline at seed 2, took 253.3 s.
- **Runs beyond the heavy-lane minimum:** change also ran at seeds 1 and 2. P2 is a direction question and its seed-0 effect fell inside 2x the baseline spread, so the extra seeds check whether the direction holds. The break ran at seed 0 only.
- **2x spread rule:** P3 is the absolute invalid share the spec asks for. The break's matched control (deviation 8) makes the schema comparison like for like: the same 48 queries, the same prompt and the same 8 in flight, with and without the schema. At seed 0 the valid shares were 1 with the schema and 0.958333 without it, a gap of 2 replies. The break ran at seed 0 only (heavy lane), so mkanswers has no seed spread for either share, and the build registers no P3 effect with it. The heavy-lane yardstick, the baseline spread of `baseline.schema_valid_share`, is 0: the 2x test passes trivially and says little. The answer gives the count and its 1/48 resolution instead. P2's effect (`change.exact_match_v2` minus `baseline.exact_match_v1`) is 0.09090899999999998 averaged over seeds 0, 1, 2, against a spread of 0.11038899999999996: below 2x. mkanswers tests an effect against the larger of its two values' spreads. Here that is v2's, and it comes from which 77 examples each seed draws. P2's grading tolerance is still the baseline spread, as the tolerance rule says. P2 is reported with its spread, not inflated. The direction was up at all three seeds (paired deltas 5.19481, 14.2857 and 7.79221 points). The lab teaches the gate's verdict, and at seed 0 that verdict is that 154 queries cannot confirm a gain of this size. A larger knob would break the spec: two examples per intent would nearly fill the 4,096-token context (by probe 1's prompt token counts), and more queries would push the baseline past 6 minutes.
- **Deviations from the spec, and the simplest choices where it is silent:**
  1. Warm-up is max(3, c) calls before each timed pass, not 3. At 4 and 8 in flight, three calls leave a slot without the cached system prompt, so one timed request would pay a cold prefill.
  2. Mac-seconds per 1,000 requests print at every concurrency, not only at 1 in flight.
  3. `baseline.ollama_num_parallel` records the script's environment (mlrun exports 4). The server log confirms the runner loaded with `Parallel:4` and `KvSize:16384` (4 slots x 4,096).
  4. `--change` reads v1's replies saved by `--baseline` at the same seed, so v1 is not sent again.
  5. The reference is 182 lines, over the 150 guideline: a streaming client, three concurrency levels, two prompts, the gate and the break's control pass. The learner's starter is 102 lines.
  6. Timing lines carry `concurrency=` beside the contract's `batch=1`.
  7. Silent spec points, simplest choice: temperature 0, `num_predict` 48, `num_ctx` 4096, the few-shot examples as one line each in the system message, the request order of the shuffled stratified sample, and the first 48 of it for the break. TTFT starts just before the POST.
  8. The break runs a second pass, the matched control: the same first 48 queries, prompt v1 and 8 in flight, with the schema on, after its own 8 warm-up calls. It prints only `break.with_schema_valid_share`. The break's timing lines come from the pass without the schema. The spec's break names only the pass without the schema. The control turns the Record row "schema-valid share with and without the schema" into a like-for-like comparison. It adds one 48-query pass, and the break run stays far inside the 6-minute cap.
- **Contention:** every reference run shared the Mac with jobs from other labs' builds: mostly light CPU runs, which mlrun's heavy lane allows beside it, and two downloads. Overlapping jobs per run: baseline 8, 2, 7 (seeds 0, 1, 2); change 6, 5, 2; break 2. Absolute timings carry that noise, and a job count says nothing about how heavy each job was: seed 0 overlapped the most jobs, yet its p50 TTFT at 1 in flight was the lowest, 211.142 ms against 261.612 and 277.337 at seeds 1 and 2. Two earlier seed-0 baselines of the same code path (one before the `batch=1` tag, one before the control pass) gave the same exact match, 0.597403, and ratios inside this run's tolerance.
- **Prototype comparison:** the spec gives no `[answers only]` prototype values for lab 15. Three build probes checked the mechanisms instead. They are not ledger runs, so their figures stay out of this file.
  - Probe 2 (32 queries, seed-1 sample) timed 1 and 4 in flight with and without the schema. p95 TTFT rose by a similar factor both ways, so the slowdown is the shared GPU, not the schema's grammar.
  - Probe 1 counted prompt tokens: both prompts fit well inside `num_ctx` 4096. It also timed a cold model load and a cold v2 prefill. Each takes seconds, and both fall inside warm-up calls, never in a timed pass.
  - Probe 3 replayed the seed-0 break through the reference as it stood before the control pass (imported, so no ledger run went stale). It printed each invalid reply beside its gold label and the label from the schema pass at 1 in flight. It gave the same split as both reference break runs, no parse failures and two unknown intents, and those are the near misses named in P3.
  - No run disagrees in direction with the probes.

</details>
