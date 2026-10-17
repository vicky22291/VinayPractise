# 24. Shadow challenger: matched decline rates, swap sets and the latency bill: reference answers

> Spoilers. The AI opens one block at a time, only after that step's prediction row exists and the learner pasted their own RESULT lines, or after 'debrief 24'.

- **HW:** `HW chip='Apple M4 Pro' cpu=14 gpu=20 mem_gib=24 macos=26.5.1 python=3.13.7 torch=2.14.1 device=cpu`
- **Seeds:** 0, 1 and 2 for every step (light lane). The seed sets only the replay order in `--break`. `--baseline` and `--change` score fixed models on a fixed test set, so their three seeds agree exactly.
- **Reference script:** `answers/24_shadow_challenger_ref.py` (sha256 prefix `3693a82578a7108c`), run from `m4-production-ml-payments/`. Raw seed-0 output: `answers/24-shadow-challenger.out`.
- **Runs and wall times (seeds 0, 1, 2):** baseline 3.4, 2.9, 2.9 s; change 3.0, 3.0, 2.9 s; break 49.5, 48.8, 49.2 s. The measured modes ran alone (the exclusive lane). Nothing is precomputed.
- **Tolerance rule:** tol = spread (max - min) over seeds 0, 1, 2; heavy labs: the baseline spread applies to every step. A spread of 0 means the value is deterministic: grade it with the learner's own 80% range. Spreads and effects below are shown to 6 significant digits; the .json holds the full floats.

<details><summary>P1. At the champion's threshold (which declines 0.2%), the decline rate the challenger produces</summary>

**Answer:** `P1.challenger_decline_rate` = 0.00238756 of the 56,962 payments, tolerance 0 (seeds 1 and 2: 0.00238756 and 0.00238756). That is 136 challenger declines at the champion's threshold of 0.0384511, where the champion declines 0.00200133.

Seed-0 RESULT lines:

```
RESULT P1.challenger_decline_rate=0.00238756 unit=fraction n=56962 seed=0
RESULT baseline.champion_threshold=0.0384511 unit=probability seed=0
RESULT baseline.champion_decline_rate=0.00200133 unit=fraction n=56962 seed=0
RESULT baseline.challenger_declines=136 unit=count seed=0
```

**Why.** A threshold is a point on one model's score scale. Lab 22's LightGBM is nearly binary on this data: most payments score close to 0 and its top 0.2% almost all score exactly 1.0 in float64 (see Build notes). Few payments sit between the champion's threshold and that top block, so reusing the threshold moves the challenger's decline rate by about a fifth, not by multiples. The size of the move comes from the shapes of the two score distributions, not from which model is better, so it says nothing about quality. That is why step 4 matches the rate.

**Common wrong prediction:** a large jump (2x or more, "boosted trees score hotter"), or exactly 0.2% on the belief that both models output calibrated probabilities on one scale. Close to 0.2% does not mean the two models decline the same payments: P2 shows they do not.

</details>

<details><summary>P2. With the challenger quantile-matched to 0.2%: the share of its declines the champion would approve</summary>

**Answer:** `P2.swap_in_share` = 0.359649, tolerance 0 (seeds 1 and 2: 0.359649 and 0.359649). At the matched rate both models decline 0.00200133 of the payments: overlap 73, swap-in 41, swap-out 41. The simulated analyst review: swap-in precision 0, swap-out precision 0.414634.

Seed-0 RESULT lines:

```
RESULT P2.swap_in_share=0.359649 unit=fraction seed=0
RESULT change.challenger_threshold=1 unit=probability seed=0
RESULT change.challenger_decline_rate=0.00200133 unit=fraction n=56962 seed=0
RESULT change.overlap=73 unit=count seed=0
RESULT change.swap_in=41 unit=count seed=0
RESULT change.swap_out=41 unit=count seed=0
RESULT change.swap_in_precision=0 unit=fraction seed=0
RESULT change.swap_out_precision=0.414634 unit=fraction seed=0
```

**Why.** At a matched rate both models decline the same number of payments, so every swap-in pairs with a swap-out and only those 41 + 41 payments change their decision. The challenger is the weaker ranker on this data (Build notes), so over a third of its declines are payments the champion approves, and the review finds no fraud among them. The 41 swap-outs at 0.414634 fraud hold 17 frauds and 24 good payments. So switching would catch 17 fewer frauds and decline 17 more good customers, at the same decline volume. A shadow compared at a matched rate, plus a review of the swap sets, catches this before the challenger declines anyone.

`change.challenger_threshold` prints as 1 because labkit rounds to 6 significant digits. The stored threshold sits just below 1.0, and 111 test payments score exactly 1.0 (Build notes). The quantile threshold lands cleanly only because that tie block is smaller than the 0.2% target.

**Common wrong prediction:** under 10%, on the belief that two decent models agree on the obvious frauds, or that a boosted model must rank better than a logistic regression at the very top.

</details>

<details><summary>P3. Shadow scored in a background thread with a 50-slot queue: is champion p99 closer to champion-alone or to the inline-shadow version?</summary>

**Answer:** `P3.closer_to` = alone at all three seeds (seeds 1 and 2: alone and alone). The thread design's p99 position is 0.0333416 (0 is alone, 1 is inline; seeds 1 and 2: 0.0179511 and 0.032063, spread 0.0153905). Champion p99 at seed 0, median of the 5 block p99s: alone 0.117666 ms, inline 0.363875 ms, thread 0.125875 ms. The thread shadow dropped 0.995562 of the rows handed to it (seeds 1 and 2: 0.995562 and 0.995545).

Seed-0 RESULT lines:

```
RESULT P3.closer_to=alone device=cpu batch=1 warmup=100 n=56962 blocks=5 seed=0
RESULT break.thread_p99_position=0.0333416 unit=ratio seed=0
RESULT break.thread_drop_share=0.995562 unit=fraction slots=50 seed=0
RESULT break.thread_walk_p99_position=0.174378 unit=ratio seed=0
RESULT break.thread_walk_drop_share=0.991299 unit=fraction slots=50 seed=0
RESULT break.p50_alone_ms=0.097875 unit=ms stat=median_of_block_p50 device=cpu batch=1 warmup=100 n=56962 blocks=5 seed=0
RESULT break.p99_alone_ms=0.117666 unit=ms stat=median_of_block_p99 device=cpu batch=1 warmup=100 n=56962 blocks=5 seed=0
RESULT break.p99_block_spread_alone_ms=0.021125 unit=ms stat=max_minus_min device=cpu batch=1 warmup=100 n=56962 blocks=5 seed=0
RESULT break.p50_inline_ms=0.269042 unit=ms stat=median_of_block_p50 device=cpu batch=1 warmup=100 n=56962 blocks=5 seed=0
RESULT break.p99_inline_ms=0.363875 unit=ms stat=median_of_block_p99 device=cpu batch=1 warmup=100 n=56962 blocks=5 seed=0
RESULT break.p99_block_spread_inline_ms=0.171209 unit=ms stat=max_minus_min device=cpu batch=1 warmup=100 n=56962 blocks=5 seed=0
RESULT break.p50_thread_ms=0.102458 unit=ms stat=median_of_block_p50 device=cpu batch=1 warmup=100 n=56962 blocks=5 seed=0
RESULT break.p99_thread_ms=0.125875 unit=ms stat=median_of_block_p99 device=cpu batch=1 warmup=100 n=56962 blocks=5 seed=0
RESULT break.p99_block_spread_thread_ms=0.0235 unit=ms stat=max_minus_min device=cpu batch=1 warmup=100 n=56962 blocks=5 seed=0
RESULT break.p50_inline_walk_ms=0.128583 unit=ms stat=median_of_block_p50 device=cpu batch=1 warmup=100 n=56962 blocks=5 seed=0
RESULT break.p99_inline_walk_ms=0.156375 unit=ms stat=median_of_block_p99 device=cpu batch=1 warmup=100 n=56962 blocks=5 seed=0
RESULT break.p99_block_spread_inline_walk_ms=0.019667 unit=ms stat=max_minus_min device=cpu batch=1 warmup=100 n=56962 blocks=5 seed=0
RESULT break.p50_thread_walk_ms=0.102917 unit=ms stat=median_of_block_p50 device=cpu batch=1 warmup=100 n=56962 blocks=5 seed=0
RESULT break.p99_thread_walk_ms=0.124416 unit=ms stat=median_of_block_p99 device=cpu batch=1 warmup=100 n=56962 blocks=5 seed=0
RESULT break.p99_block_spread_thread_walk_ms=0.021542 unit=ms stat=max_minus_min device=cpu batch=1 warmup=100 n=56962 blocks=5 seed=0
RESULT break.cpu_ms_champion=0.0973762 unit=ms clock=thread_time batch=1 warmup=100 n=2000 stat=median seed=0
RESULT break.cores_champion=0.194752 unit=cores qps=2000 seed=0
RESULT break.cpu_ms_lgbm_100=0.166541 unit=ms clock=thread_time batch=1 warmup=100 n=2000 stat=median seed=0
RESULT break.cores_lgbm_100=0.333081 unit=cores qps=2000 seed=0
RESULT break.cpu_ms_lgbm_1000=0.215464 unit=ms clock=thread_time batch=1 warmup=100 n=2000 stat=median seed=0
RESULT break.cores_lgbm_1000=0.430929 unit=cores qps=2000 seed=0
```

**Why.** The thread shadow did not slow the champion because it barely ran. It dropped 0.995562 of the 57,462 rows handed to it (56,962 timed plus 5 x 100 warm-up), so it scored about 255 rows, about 51 a block: the 50 queued rows each pass drains when it closes, plus about one. The request thread runs back to back with no idle time. It lets go of the GIL only for moments inside native code and takes it straight back, and each of those releases resets the waiting thread's 5 ms switch-interval wait, so the shadow thread almost never gets the GIL. That mechanism is inferred from CPython's GIL handoff; the drop share is what was measured. The bounded queue did its job and protected the champion by dropping, but a shadow that drops nearly everything measures nothing: the drop share is the number to page on. The pure-Python walk, which holds the GIL for a whole score once it runs, starved the same way: drop share 0.991299, p99 position 0.174378 at seed 0 (seeds 1 and 2: 0.0941865 and 0.33367).

Inline is the real bill. LightGBM in the request path moves the champion's p50 from 0.097875 to 0.269042 ms, which matches LightGBM's own 0.166541 CPU-ms per call. The p99 effect is 0.227736 ms against a spread of 0.040209 ms. The walk inline costs less (p50 0.128583 ms): for one 1 x 29 row, LightGBM's per-call wrapper costs more than walking 100 trees in Python.

Cost at 2,000 decisions a second (seed 0): the champion needs 0.194752 cores (0.0973762 CPU-ms per decision). An inline or same-process LightGBM shadow adds 0.333081 cores at 100 trees (0.166541 CPU-ms) or 0.430929 at 1,000 trees (0.215464 CPU-ms). Ten times the trees cost about 1.3 times the CPU per single-row call, because the per-call overhead dominates a single-row prediction. The 1,000 vs 100-tree effect is 0.0489663 CPU-ms against a spread of 0.008449.

What this replay does not show: real requests arrive with gaps. In the gaps a same-process shadow thread would get the GIL, and a request landing while it holds the GIL waits, so the champion's tail would pay instead of the drop share. The replay sends requests back to back, so it measures the starvation side only.

**Common wrong prediction:** inline, or about halfway, at high confidence, because the GIL makes the two threads take turns. The GIL is the right mechanism, but here its cost lands in the drop share, not in the champion's p99. Alone, picked because "a background thread is free", is the right pick for the wrong reason.

</details>

<details><summary>Rebuild check</summary>

Solution: `answers/rebuild/24_swap_sets.py`. Stub: `m4-production-ml-payments/rebuild/24_swap_sets.py`. `rebuildcheck` verdict: the stub fails as it should (exit 1, NotImplementedError), the solution passes (exit 0, `check: PASS`): REBUILDCHECK OK. `check()` uses synthetic beta-distributed scores and random masks, never this lab's results.

</details>

<details><summary>Card drafts</summary>

| ID | Lab | Type | Question |
|---|---|---|---|
| 24-M | 24 | M | Why do you compare a challenger with the champion at the champion's decline rate rather than at the champion's threshold, and where do you then look for the decisions that change? |
| 24-N | 24 | N | At a matched 0.2% decline rate on lab 22's 56,962 test payments, what share of the LightGBM challenger's declines were swap-ins, and what did the simulated analyst review find among them? |
| 24-D | 24 | D | A same-process thread shadow leaves the champion's p99 where it was, but the shadow's log holds far fewer scores than payments served. What do you check first, and what does it tell you? |

Keys:

- **24-M:** (1) a threshold is a point on one model's score scale, and the scales differ (lab 22's LightGBM piles up at exactly 1.0); (2) a matched rate fixes the operating point: the same number of declines, so the same customer cost; (3) only the swap-in and swap-out sets change a decision, so the review goes there.
- **24-N:** (1) 0.359649: 41 of the 73 + 41 = 114 challenger declines; (2) swap-in precision 0: no fraud among the new declines, while the swap-outs held 17 frauds; (3) so the challenger ranks worse at the top and should not ship.
- **24-D:** (1) the queue drop share, rows dropped / rows handed to the shadow (0.995562 in the lab); (2) the busy request thread starves the shadow thread of the GIL, so the bounded queue drops and the champion only looks unharmed; (3) move the shadow out of the request process, and page on the drop share.

</details>

<details><summary>Build notes</summary>

- **Inputs.** Lab 22's three files as shipped by its seed-0 baseline, never retrained. Rows are 1 x 29 (V1 to V28 and Amount), not the spec's 1 x 30: lab 22 trains without Time, which OpenML keeps as a row id. The champion's threshold is the 0.998 quantile of its scores on the replay itself, so it declines 0.2% of the replay, as P1 states.
- **Knobs.** None changed for the 2x rule. The spec's settings hold: 0.2%, a 50-slot queue, 100 warm-up calls, 5 repeats (blocks), 100 vs 1,000 trees, 2,000 decisions a second.
- **The walk.** The LightGBM thread shadow moved the champion's p99 by less than 2x the seed spread, so the reference adds the pure-Python tree walk the author notes ask for. The walk's scores equal LightGBM's to 1e-12 on the first 500 requests (asserted in `--break`). It starved too, so the GIL shows up as queue drops, not as p99. Both thread-design p99 effects are reported as small, with their spreads, and not inflated: thread 0.00634767 ms against a spread of 0.008375 ms (within 2x the spread), walk thread 0.00756967 ms against 0.008832 ms (within 2x the spread). P3 itself is stable: the position stays far below 0.5 at every seed.
- **Effects that the lab teaches as real** all clear 2x the spread: the change moves the challenger's decline rate by -0.00038623 (spread 0), inline p99 0.227736 ms (spread 0.040209), inline p50 0.170958 ms (spread 0.002375), walk inline p99 0.0358337 ms (spread 0.013709), 1,000 vs 100 trees 0.0489663 CPU-ms (spread 0.008449).
- **The 1,000-tree LightGBM** uses lab 22's parameters with `learning_rate=0.01`. The build's first `--download`, at lab 22's 0.1, stopped at 220 trees, because no split with positive gain was left. A builder spot check found 31 leaves in every tree of both models, so the cost row compares 10 times the tree work.
- **Prototype comparison, swap sets.** The prototype had both models decline 114 at 0.2% with 84 shared, so 26.3% new. Here both decline 114 (73 + 41) with 73 shared, so 0.359649 new: the same direction, a larger swap set. The spread is 0, so the gap needed a cause, and it is lab 22's challenger, not this lab's code. A builder inspection (mlpy, not RESULT lines, not in the .json) found that the default-parameter LightGBM is numerically degenerate on this data. Its raw scores run from about -331,000 to +21,000, and 111 of the 56,962 test scores are exactly 1.0. Its ROC AUC (area under the receiver operating characteristic curve) is 0.8298 against the champion's 0.9651, and its average precision 0.3722 against 0.7226. At 0.2% the overlap holds 63 frauds, so the champion's declines are 0.7018 fraud and the challenger's 0.5526. The likely cause: leaves with only a few frauds take huge Newton steps under extreme imbalance (`min_child_weight` 0.001, no L2 penalty). The prototype's challenger had 300 trees and was presumably healthier. This is reported to the orchestrator as a lab 22 issue. Lab 24 keeps lab 22's files as shipped, and its lesson holds: a matched-rate shadow and a swap-set review catch a weaker challenger before it declines anyone.
- **Tie hazard.** The matched threshold works only because the challenger's block of exact 1.0 scores (111) is smaller than the 0.2% target (114 declines). At a decline rate of 110 / 56,961 (about 0.19%) or lower, the quantile would be exactly 1.0 and `score > threshold` would decline nothing. The stored challenger threshold is 1 minus about 8.6e-10, with no ties at it.
- **Prototype comparison, latency.** The prototype measured single-row p99 at 0.60 ms for the logistic regression and 1.04 ms for a 300-tree LightGBM. Here the champion alone has p99 0.117666 ms, and the 100-tree LightGBM costs 0.166541 CPU-ms per call. The ratio of LightGBM to logistic regression is similar (about 1.7 in both), but the absolute level is about 5 times lower here. A builder spot check (mlpy while no measured run was in progress, 2,000 calls, not a reference run) found two contributors. A 1-row DataFrame costs the champion about 2.9 times the ndarray row at p99. LightGBM with its saved `n_jobs` (None, so all cores) costs about 1.9 times `n_jobs=1` at p99 over 300 calls. These explain part of the gap (about 2.9 of the champion's 5 times). The rest is not explained by anything the spec records, such as the prototype's host or its load. Nothing points to a bug, because internal checks on the reference agree: the inline p50 minus the alone p50 (0.170958 ms) matches LightGBM's 0.166541 CPU-ms, and the champion's p50 alone (0.097875 ms) matches its 0.0973762 CPU-ms.
- **Replay design.** Requests run back to back (a closed loop), as the spec's one-row-at-a-time replay implies. With open-loop arrivals at 2,000 a second, the shadow thread would run in the gaps, and the GIL would show in the champion's tail instead. This is not measured here, and the P3 debrief says so.
- **Length.** The reference is about 235 lines, over the 150-line guide, because it carries the walk, the thread shadow and the cost row. The learner never reads it before the debrief.

</details>
