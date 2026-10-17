# 14. An eval set and an LLM judge: judges need a human ceiling: reference answers

> Spoilers. The AI opens one block at a time, only after that step's prediction row exists and the learner pasted their own RESULT lines, or after 'debrief 14'.

- **HW:** `HW chip='Apple M4 Pro' cpu=14 gpu=20 mem_gib=24 macos=26.5.1 python=3.13.7 torch=2.14.1 device=cpu`. The judge is `qwen2.5:7b` on the build's own Ollama 0.18.0 server (started with `OLLAMA_NUM_PARALLEL=4`; the script sends one request at a time).
- **Seeds:** 0 for every step, plus 1 and 2 for the baseline (heavy lane). `--seed` draws the 50 pairs. The judge's `OPTIONS` (temperature 0, Ollama seed 42, `num_ctx` 4096) are the same at every seed.
- **Reference script:** `answers/14_llm_judge_ref.py` (script sha256 prefix `b0d9ad7321126ff6`). Raw seed-0 output: `answers/14-llm-judge.out`.
- **Runs and wall times:** baseline seed 0 237.5 s, seed 1 128.6 s, seed 2 105.9 s; change seed 0 301.2 s; break seed 0 130.3 s. No step is precomputed.
- **Tolerance rule:** tol = spread (max - min) over seeds 0, 1, 2; heavy labs: the baseline spread applies to every step. Here the P1 spread is 0, because each of the three 50-pair draws agreed on 41 of 50. That is a coincidence: the binomial standard error at n = 50 is 5.4 points, so read every agreement or share below as carrying about 5 points of sampling noise. Hit still uses only the learner's own range.

<details><summary>P1. qwen2.5:7b, prompt v1, the 50 pairs at seed 0 with answer A first: agreement in % with the human majority winner</summary>

**Answer:** 82%. Tolerance 0 by the seed-spread rule (seeds 1 and 2 also gave 82); about 5 points of sampling noise at n = 50.

Seed-0 RESULT lines:

```
RESULT P1.agreement_pct=82 unit=pct n=50 seed=0
RESULT baseline.kappa=0.636511 unit=kappa n=50 seed=0
RESULT baseline.picks_a_pct=54 unit=pct n=50 seed=0
RESULT baseline.human_a_pct=56 unit=pct n=50 seed=0
RESULT baseline.human_human_pct=89.5652 unit=pct n=115 seed=0
RESULT baseline.prompt_tokens=682.5 unit=tokens device=ollama batch=1 warmup=1 n=50 stat=median seed=0
RESULT baseline.output_tokens=8 unit=tokens device=ollama batch=1 warmup=1 n=50 stat=median seed=0
RESULT baseline.s_per_item=4.07712 unit=s device=ollama batch=1 warmup=1 n=50 stat=median seed=0
```

The reference prints `SKIP baseline.my_agreement_pct` instead of a value: it has no human labels. That row is the learner's own (a human step).

Other seeds (1, then 2): `P1.agreement_pct` 82 and 82; `baseline.kappa` 0.614065 and 0.64; `baseline.human_human_pct` 86.9159 and 89.4309; `baseline.picks_a_pct` 36 and 50; `baseline.human_a_pct` 38 and 48; `baseline.prompt_tokens` 540.5 and 648; `baseline.output_tokens` 8 and 8; `baseline.s_per_item` 2.07176 and 1.86258.

**Why.** The eval set keeps only pairs with a clear human majority, and most of them set gpt-4, claude-v1 or gpt-3.5-turbo against a 13B model, where the better answer is easy to see: at seed 0 the judge picked the human winner on 28 of those 32 pairs, but on only 3 of the 6 pairs between two strong models. Kappa (0.636511) sits well below the raw 82% because both raters split near half and half (the judge picked answer A on 54% of pairs, the human majority on 56%), so chance alone would agree on about half the pairs. On the same 50 pairs the humans agree with each other on 89.5652% of vote pairs, so the judge is under the human ceiling. Zheng et al. report GPT-4 at the human level; this 7B judge is close on easy pairs and near a coin flip on hard ones.

**Common wrong prediction:** near chance, 55 to 65%, from "a 7B model cannot grade GPT-4-level answers". On clear-majority pairs most items have one plainly weaker answer, and a small judge sees that too. The opposite error is to read 82% as "as good as humans" without the ceiling next to it.

</details>

<details><summary>P2. Prompt v2 (a 3-point rubric before the verdict) instead of v1: agreement direction and size</summary>

**Answer:** down 4 points (82% to 78%), within noise. Tolerance 0 by the rule (the baseline spread). The honest read is "no detectable change": 3 pairs went right to wrong and 1 wrong to right, and a two-sided exact sign test on 3 against 1 gives p = 0.625.

Seed-0 RESULT lines:

```
RESULT change.agreement_pct=78 unit=pct n=50 seed=0
RESULT change.kappa=0.56 unit=kappa n=50 seed=0
RESULT change.picks_a_pct=50 unit=pct n=50 seed=0
RESULT P2.agreement_delta_pts=-4 unit=points n=50 seed=0
RESULT change.right_to_wrong=3 unit=pairs seed=0
RESULT change.wrong_to_right=1 unit=pairs seed=0
RESULT change.prompt_tokens=726.5 unit=tokens device=ollama batch=1 warmup=1 n=50 stat=median seed=0
RESULT change.output_tokens=57 unit=tokens device=ollama batch=1 warmup=1 n=50 stat=median seed=0
RESULT change.s_per_item=5.56422 unit=s device=ollama batch=1 warmup=1 n=50 stat=median seed=0
```

Other seeds: none. The heavy lane runs the change at seed 0 only.

**Why.** A rubric changes what the judge attends to, but on clear-majority pairs v1 already picks the human winner on most items, so there is little room to move: only 4 of 50 verdicts changed. The 4-point drop is a net of 2 pairs. With 4 discordant pairs a sign test cannot tell that from a coin, and the baseline's own sampling noise is about 5 points. What the rubric surely changes is cost: 57 output tokens per pair instead of 8, and 5.56422 s per pair. The scores are not saved, so which criterion moved those 4 verdicts is not recorded.

**Common wrong prediction:** up, by 5 to 10 points, from "structured reasoning before a verdict always helps". On this judge and these items the rubric changes few verdicts and supports no direction. The lesson for the interview question: a prompt change is judged on the items that flip, with a paired test, never on a 4-point move across 50 items.

</details>

<details><summary>P3. Swap the order of the two answers, prompt v1: share of verdicts that flip</summary>

**Answer:** 14%, 7 of the 50 pairs. Tolerance 0 by the rule; about 5 points of sampling noise at n = 50. An order-blind judge flips 0 pairs, and this judge is deterministic at temperature 0 (the 25 pairs that two baseline draws share got identical verdicts in separate runs), so every flip was decided by position.

Seed-0 RESULT lines:

```
RESULT P3.flip_rate_pct=14 unit=pct n=50 seed=0
RESULT break.picks_a_pct=44 unit=pct n=50 seed=0
RESULT break.agreement_pct=84 unit=pct n=50 seed=0
RESULT break.prompt_tokens=682.5 unit=tokens device=ollama batch=1 warmup=1 n=50 stat=median seed=0
RESULT break.output_tokens=8 unit=tokens device=ollama batch=1 warmup=1 n=50 stat=median seed=0
RESULT break.s_per_item=2.06231 unit=s device=ollama batch=1 warmup=1 n=50 stat=median seed=0
```

Other seeds: none. The heavy lane runs the break at seed 0 only.

**Why.** The same answer is picked less often once it moves from first to second place: answer A's pick share falls from 54% to 44%, so 6 of the 7 flips went to whichever answer was shown first and 1 to the second. That is a first-position bias, despite the prompt's line telling the judge to avoid one. Agreement hides it: the swapped run agrees with the humans on 84% against 82% in the original order, because 4 flips turned a wrong verdict right and 3 turned a right verdict wrong. Counting a win only when it holds in both orders, the fix in Zheng et al., leaves 38 of 50 pairs (76%) and calls the 7 flipped pairs ties.

**Common wrong prediction:** 0 to 5%, from "temperature 0 makes the judge deterministic". Deterministic means the same input gives the same verdict. A swapped pair is a different input, and the judge reads position as part of it.

</details>

<details><summary>Rebuild check</summary>

Solution: `answers/rebuild/14_judge_agreement.py`. Its bodies are the same lines as `confusion()`, `agreement_and_kappa()` and `flip_rate()` in the reference script.

`rebuildcheck`, given the absolute paths of `m3-more-of-the-map/rebuild/14_judge_agreement.py` and `answers/rebuild/14_judge_agreement.py`: the stub fails as it should (NotImplementedError, exit 1), the solution passes (`check: PASS`, exit 0): `REBUILDCHECK OK`.

What `check()` tests: the 2 x 2 table against `sklearn.metrics.confusion_matrix`, agreement against `accuracy_score` and kappa against `cohen_kappa_score` to 1e-12, on 300 random draws (it skips the rare draw where both raters give one and the same label, since kappa is undefined there); an always-'A' judge on 80% 'A' labels, which must give raw agreement 0.8 and kappa 0; and the flip rate against `1 - accuracy_score` of the winning answers, on 100 random swaps whose letters it builds itself.

</details>

<details><summary>Card drafts</summary>

| ID | Lab | Type | Question |
|---|---|---|---|
| 14-M | 14 | M | Why can a judge show high raw agreement with human labels and a Cohen's kappa near 0, and what exactly does kappa subtract? |
| 14-N | 14 | N | On the lab's 50 clear-majority MT-Bench pairs, what share of qwen2.5:7b's verdicts flipped when only the order of the two answers was swapped, and what did that do to its agreement with humans? |
| 14-D | 14 | D | A new judge prompt lifts agreement with human labels from 74% to 80% on a 50-item eval set, and the team wants to switch. What do you check first? |

Keys:

- **14-M.** Kappa subtracts chance agreement at each rater's own label rates, p_e = row A share x column A share + row B share x column B share. Must mention: (1) when one label dominates, p_e is high, so raw agreement can be high while kappa is near 0; (2) the always-'A' judge on 80% 'A' items: 80% raw, kappa 0; (3) kappa = (p_o - p_e) / (1 - p_e).
- **14-N.** 14%, 7 of 50 pairs, at seed 0 (6 of them toward the answer shown first). Must mention: (1) about 14%; (2) agreement barely moved (82% to 84%), so agreement alone hides position bias; (3) the fix: judge both orders and count a win only when it holds in both.
- **14-D.** Count the items that flipped each way: only discordant items carry evidence. Must mention: (1) 6 points on 50 items is 3 net items, so run a paired sign test on the flips; (2) the same saved item ids in both runs, judged in both answer orders; (3) compare with the human-human ceiling on the same items before calling either prompt good.

</details>

<details><summary>Build notes</summary>

**Knob changes:** none. P1 to P3 run at the spec's configuration: 50 turn-1 pairs with at least 2 human votes and a non-tie majority, drawn by the seed, judged by `qwen2.5:7b` with temperature 0 and Ollama seed 42.

**Where the spec is silent, the simplest correct option:**

- **Pair identity and order.** A pair is one question and two models, whatever order each human saw them in, because the dataset stores both orientations of the same pair. Answer A is the model first in name order. That keeps the human majority close to half A, which the kappa and position checks need.
- **Strict majority.** The verdict with the most votes among A, B and tie, unique and not tie. 303 turn-1 pairs qualify. Grouping votes by pair this way reproduces the spec's 961 pairs with 2 or more votes (both turns).
- **`num_ctx` 4096 in `OPTIONS`.** The spec gives temperature 0 and seed 42 only. 4096 is the build server's default on this Mac, it is pinned so a learner's server with a smaller default cannot truncate the prompt, and the longest eligible pair (probe run) uses under half of it. It also matches lab 15's `num_ctx`.
- **Prompts.** `JUDGE` is MT-Bench's pairwise judge prompt without its written explanation and its tie option. Both format lines ask for one-line JSON: a probe showed `qwen2.5:7b` pretty-printing the v2 object, which cost generation time. The wording is fixed in the starter so the learner's numbers compare with the reference. The learner's harness prompt states how the messages are built.
- **v2 schema.** Three integer scores per answer (`enum` [1, 2, 3]) under `"a"` and `"b"`, then `"verdict"`. Key order is generation order, so the scores come first.
- **Requests.** One at a time, with one untimed warm-up call per mode. `prompt_eval_count` counts the whole prompt even when Ollama reuses a cached prefix (checked in the probe), so the token rows are full prompt lengths.
- **The eval set lives in given code.** `load_data()` in the starter draws the 50 pairs, because the 20-pair labelling sheet has to exist before the session. The learner still states the selection rule in their harness prompt.
- **Saved verdicts.** `--baseline` saves its per-pair v1 verdicts; `--change` and `--break` read them (exit 2 with the command when missing), so v1 in the original order is judged once.
- **Record rows beyond the spec's list:** `picks_a_pct` in each mode and `baseline.human_a_pct` (to read kappa's chance term and the position shift), the change's right-to-wrong and wrong-to-right counts (the paired view), and `break.agreement_pct` (to show that agreement hides the flips).
- **Your labels.** `--download` writes `~/ml-data/lab14/to_label.txt` and `my_labels.csv` for the first 20 pairs at seed 0. The reference skips `baseline.my_agreement_pct` and says so in a SKIP line.
- **Length.** The reference is 244 lines, over the brief's 150. Its first 130 lines are the starter's given parts (the prompt constants, `load_data()`, the labelling sheet, `check_server()`, `report()`), which the pre-session human step and the spec's Record list need; the harness and the learner's piece add the rest.
- **Starter checks.** `--download` and `--smoke` pass on the starter, and its `--baseline` stops with NotImplementedError, as a level S starter should.

**Precomputed steps:** none. The longest seed-0 run took 301.2 s (the change).

**The 2x spread rule.** The P1 spread is 0 by coincidence (41 of 50 at every seed), so the rule is vacuous here; the binomial standard error, 5.4 points at n = 50, is the realistic noise scale. Effects in the JSON: `change.agreement_pct:P1.agreement_pct` is -4 and `break.agreement_pct:P1.agreement_pct` is 2, both "ok" only because the spread is 0. P2 is reported as within noise with its paired counts (3 against 1, p = 0.625), not inflated. P3's own effect is the flip rate against the 0 flips of an order-blind judge, checked by hand because mkanswers takes two RESULT names: 7 of 50 pairs, above 2 standard errors. The judge is deterministic here: the 25 pairs that two baseline draws share (6 + 10 + 9), judged in separate runs in the same order, got identical verdicts, so every flip comes from the order.

**Offline analysis** (from the dataset and the saved seed-0 verdicts, no extra judge calls): all eligible pairs together have 89.34% human-human agreement over 694 vote pairs. At seed 0, by model pair: strong against 13B, 28 of 32 right; strong against strong, 3 of 6; 13B against 13B, 10 of 12 (strong = gpt-4, claude-v1, gpt-3.5-turbo). From the break's own lines: 6 of the 7 flips went to the answer shown first and 1 to the second; 4 flips turned a wrong verdict right and 3 a right one wrong; a win counted only when it holds in both orders gives 38 of 50 (76%).

**Prototype comparison.** The spec's prototype gives whole-file human-human agreement of 1,282 of 1,550 vote pairs (82.7%) without ties and 65.5% with ties. Both reproduce exactly from the parquet with the pair rule above (with ties: 1,552 of 2,368). The lab's ceiling on its 50 pairs is higher (89.5652, 86.9159 and 89.4309 at seeds 0, 1 and 2) because keeping only strict-majority pairs selects items humans agree on. The direction is the one the module README predicts, so no bug. The spec's "median input about 510 tokens" compares with 682.5 tokens at seed 0 (540.5 and 648 at seeds 1 and 2): the longer MT-Bench-style system prompt and the answer markers account for it. Its "200 calls take about 5 to 8 minutes" compares with the three seed-0 runs of 50 calls each, 237.5, 301.2 and 130.3 s, which ran beside other jobs. Seconds per item depend on that load: the baseline (4.07712 s per item) and the break (2.06231 s) send the same prompt lengths, so the gap is the machine's load, not the prompt.

</details>
