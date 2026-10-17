# 08. Which features does the model use? Split counts, permutation importance and reason codes: reference answers

> Spoilers. The AI opens one block at a time, only after that step's prediction row exists and the learner pasted their own RESULT lines, or after 'debrief 08'.

- **HW:** `HW chip='Apple M4 Pro' cpu=14 gpu=20 mem_gib=24 macos=26.5.1 python=3.13.7 torch=2.14.1 device=cpu`
- **Seeds:** 0, 1 and 2 for every step (light lane).
- **Reference script:** `answers/08_feature_importance_and_reason_codes_ref.py` (script_sha256 `cfd0b7e896269d82`). The learner's starter, `m2-dont-fool-yourself/scripts/08_feature_importance_and_reason_codes.py`, differs only in the TODO body.
- **Runs and wall times (seeds 0, 1, 2):** baseline 15.0, 20.1, 22.9 s; change 13.2, 19.1, 14.0 s; break 39.9, 35.0, 39.6 s. The build shared the CPU with other labs' runs, so these are upper bounds.
- **Tolerance rule:** tol = spread (max - min) over seeds 0, 1, 2; heavy labs: the baseline spread applies to every step.
- Raw seed-0 output: `08-feature-importance-and-reason-codes.out`. Values, spreads and effects: `08-feature-importance-and-reason-codes.json`.

<details><summary>P1. With 100 trees, the random column's rank out of 15 under split-count importance, and under validation permutation importance</summary>

**Answer:** split count ranks `random` 5 of 15 (tolerance 1). Validation permutation importance ranks it 14 of 15 (tolerance 1). Grading: each rank has its own 80% range and a hit needs both inside; Off by uses the split-count rank.

Seed-0 RESULT lines (baseline):

```
RESULT P1.random_rank_split=5 unit=rank_of_15 seed=0
RESULT P1.random_rank_perm=14 unit=rank_of_15 seed=0
RESULT baseline.random_rank_gain=10 unit=rank_of_15 seed=0
RESULT baseline.auc=0.928516 unit=fraction seed=0
RESULT baseline.sex_shap_rank=9 unit=rank_of_15 seed=0
RESULT baseline.reasons_1=capital-gain=15024:+6.33|age=43:+0.79|relationship=Wife:+0.75 unit=column=value:log_odds score=0.999 seed=0
RESULT baseline.reasons_2=capital-gain=15024:+6.15|education-num=15:+0.82|age=39:+0.67 unit=column=value:log_odds score=0.999 seed=0
RESULT baseline.reasons_3=capital-gain=99999:+5.60|education-num=15:+0.73|age=38:+0.71 unit=column=value:log_odds score=0.999 seed=0
RESULT baseline.ms_per_score=0.0293955 unit=ms device=cpu batch=1 warmup=20 n=200 stat=median threads=1 seed=0
RESULT baseline.ms_per_explanation=0.654459 unit=ms device=cpu batch=1 warmup=20 n=200 stat=median threads=1 seed=0
```

Other seeds (1, 2): split rank 4, 5; permutation rank 15, 15; gain rank 10, 10 (spread 0); validation AUC (area under the receiver operating characteristic curve) 0.931301, 0.932056 (spread 0.0035399999999999876).

**Why.** Split count rewards any column the trees can cut often. LightGBM sorts each numeric column into at most 255 histogram bins. A column with 10,000 distinct values fills them all, so every node offers it many thresholds, and one of them nearly always buys a small gain by fitting noise in the training rows. `fnlwgt`, the near-unique census sampling weight, rides the same effect and ranks above `random` at every seed. Permutation importance asks the validation rows instead: shuffling a column the model needs costs AUC, and shuffling pure noise costs nothing on average, so `random` sinks to the bottom. At seed 0 `education` lands below it, because `education-num` carries the same information and shuffling `education` alone costs almost nothing.

Gain (the total loss reduction from a column's splits) sits in between, 10 of 15 at every seed: many splits, each buying little.

**Reason codes and the `sex` rank (Record rows).** For the 3 highest-scored validation rows, `capital-gain` carries most of the push in log-odds at every seed, followed by `age`, `education-num` or a household column. `sex` ranks 9 of 15 by mean absolute SHAP (SHapley Additive exPlanations) value at every seed (spread 0). That rank is a weak fairness check. In a build-time crosstab, `relationship` is Husband or Wife on almost half the rows, and those two values fix `sex` almost exactly. So the model can use sex through `relationship`, its top column by gain, while the `sex` column itself ranks in the middle. A fairness review compares outcomes by group, such as positive rates and error rates for women and men, not attribution ranks.

**What an explanation costs (Record rows).** One row on one thread at seed 0: 0.0293955 ms to score and 0.654459 ms to explain; seeds 1 and 2: 0.0338545 and 0.661083 ms, 0.031375 and 0.749729 ms. The ratio of the two understates the compute gap. Most of a one-row score is the fixed cost of one `Booster.predict` call, which the explanation pays too: in a build probe, a call that used 1 tree cost most of what the 100-tree call cost. The explanation is compute-bound. TreeSHAP, the exact SHAP algorithm for trees, visits every leaf of every tree: O(T L D^2) per row, against O(T D) for a score ([module README](../m2-dont-fool-yourself/README.md#feature-importance-and-reason-codes)). Per row inside one call over all 9,769 validation rows, the probe's explanation-to-score ratio was two to three times its one-row ratio, and the gap grows with the model. Both one-row times stay far below the repo's 100 ms decision budget (solution.md §5.1). The Staff point is where that cost lands: batch the explanations, or compute them asynchronously for declined and reviewed payments only, as solution.md §5.9 does. The timing spreads (0.004459000000000001 and 0.09526999999999997 ms) come from other build jobs sharing the CPU, not from the model.

**Common wrong prediction.** "The model cannot use noise, so both measures put `random` last." Split counts measure use on the training rows, not value on new rows. The opposite miss also happens: expecting permutation importance to rank `random` high because the trees split on it so often.

</details>

<details><summary>P2. Drop relationship, then drop relationship and marital-status together: AUC change for each, direction and size</summary>

**Answer:** dropping `relationship` alone leaves AUC about the same, a sliver down: -0.000345235 at seed 0 (tolerance 0.001021545). Dropping `relationship` and `marital-status` together lowers it: -0.0277801 at seed 0 (tolerance 0.0053113000000000014). Both are AUC differences on the 0 to 1 scale (`unit=fraction`). A range written in AUC points (hundredths of AUC, lab 03's unit) is divided by 100 before grading. Grading: both drops must be hits by the dir rule; Off by uses the two-column drop, because the one-column change sits near zero.

Seed-0 RESULT lines (change):

```
RESULT P2.auc_without_relationship=0.928171 unit=fraction seed=0
RESULT P2.auc_change_without_relationship=-0.000345235 unit=fraction seed=0
RESULT P2.auc_without_both=0.900736 unit=fraction seed=0
RESULT P2.auc_change_without_both=-0.0277801 unit=fraction seed=0
```

Other seeds (1, 2): change without `relationship` -0.000850396, -0.00136678; change without both -0.0291113, -0.0330914. AUC without `relationship` 0.930451, 0.93069; without both 0.90219, 0.898965.

Effect check (mkanswers): without both minus `baseline.auc` averages -0.029994000000000003 against a spread of 0.0035399999999999876, more than 2x the spread. Without `relationship` alone it averages -0.0008536666666666785 against the same spread, under 2x by design: the lab teaches it as a null effect. The paired change is negative at all three seeds but smaller than the seed-to-seed spread of AUC itself, so a "same" or a small "down" with a range that covers it is a hit.

**Why.** `relationship` and `marital-status` describe the same household from two sides: Husband or Wife almost always means Married-civ-spouse. Without `relationship`, the trees rebuild nearly the same splits from `marital-status`, so AUC barely moves. Remove both and no other column carries the household signal, so AUC falls. Gain ranks `relationship` first at every seed, yet dropping it alone costs almost nothing: an importance score says what the model used, not what it would lose.

**Common wrong prediction.** "The top-gain column must cost the most when dropped", or "two drops cost about twice one drop".

</details>

<details><summary>P3. Retrain with 500 trees: the random column's split-count rank</summary>

**Answer:** 2 of 15 at seed 0 (tolerance 1), a climb from 5 at 100 trees. Effect check (mkanswers): -3.0 ranks against a spread of 1, more than 2x the spread.

Seed-0 RESULT lines (break):

```
RESULT P3.random_rank_split=2 unit=rank_of_15 seed=0
RESULT break.random_rank_perm=11 unit=rank_of_15 seed=0
RESULT break.random_rank_gain=8 unit=rank_of_15 seed=0
RESULT break.auc=0.926012 unit=fraction seed=0
```

Other seeds (1, 2): split rank 1, 2; permutation rank 15, 14 (spread 4); gain rank 6, 7 (spread 2); AUC 0.928565, 0.929327 (spread 0.003315000000000068).

**Why.** Each new tree fits what the trees before it left. After about a hundred trees most of the real signal is used up, and what is left on the training rows is noise. Columns with the most distinct values offer the most ways to fit it, so `random` and `fnlwgt` take the top two split-count spots at every seed (`fnlwgt` edges ahead at seeds 0 and 2). Validation AUC is a little lower at 500 trees at every seed (0.926012, 0.928565, 0.929327 against 0.928516, 0.931301, 0.932056), the tell that the extra splits fit noise. Permutation importance stays low but wanders (11, 15, 14): `random` is independent of everything, so its expected drop is exactly zero, but the noise around zero grows as the model leans on it.

That noise floor is why a planted random column is useful: a real column that ranks below it has no evidence of value.

**Common wrong prediction.** "The rank stays put, since the column is still noise", or "more trees average the noise out, so `random` drops toward the bottom".

</details>

<details><summary>Rebuild check</summary>

Solution: `answers/rebuild/08_permutation_importance.py`. Stub: `m2-dont-fool-yourself/rebuild/08_permutation_importance.py`. `rebuildcheck`: the stub fails as it should (NotImplementedError), and the solution exits 0 and prints `check: PASS`: REBUILDCHECK OK.

`check()` fits LogisticRegression on 1,000 synthetic rows with 4 columns of falling weight (the last has none). On 500 more rows it compares the ranks with `sklearn.inspection.permutation_importance(scoring='roc_auc', n_repeats=5, random_state=0)`, and the mean drops must agree within 0.06.

</details>

<details><summary>Card drafts</summary>

| ID | Lab | Type | Question |
|---|---|---|---|
| 08-M | 08 | M | Why can a column of random integers rank near the top of a gradient-boosted model's split-count importance, and why must permutation importance be scored on validation rows, not training rows? |
| 08-N | 08 | N | On Adult with a 100-tree LightGBM, about how much validation AUC do you lose by dropping `relationship` alone, and by dropping it together with `marital-status`? Why so different? |
| 08-T | 08 | T | A merchant asks why their customer's payment was declined. What does the merchant get, what does a risk analyst get, and why is the TreeSHAP explanation computed off the payment's request path? |
| 08-D | 08 | D | A fraud model's importance report puts `merchant_txn_id`, a random-looking ID, in its top 3 by split count. What do you check first, and what result clears it or condemns it? |

08-T and 08-D are alternatives. At close, draft the one the T and D alternation calls for (D every other lab).

Keys:

- **08-M:** (1) many distinct values give many thresholds, so the trees always find a small training-set gain by fitting noise; (2) split counts measure use on training rows, not value on new rows; (3) on training rows the trees fit the noise, so shuffling a noise column there costs AUC and makes it look useful, while on validation rows that fitted noise is worth nothing and the drop is about zero.
- **08-N:** (1) alone: about zero, a sliver down (seeds 0 to 2: -0.00136678 to -0.000345235); "no change", or any drop inside the seed-to-seed AUC spread (0.0035399999999999876), is a hit; (2) both: about 0.03 down, hit band -0.0330914 to -0.0277801 over seeds 0 to 2; (3) the two columns carry the same household information, so either one covers for the other.
- **08-T:** (1) the merchant gets a category and an action ("card used unusually, ask the customer to try 3-D Secure or another card"), never the score, the rule or the SHAP factors, because those teach an attacker the boundary; (2) the analyst gets rule hits, the model version, the score, the top SHAP factors and a replay from the snapshot; (3) an explanation costs more than the score it explains (lab 08, seed 0, one row, one thread: 0.654459 ms against 0.0293955 ms, and the gap grows with trees, leaves and depth), so the repo computes SHAP asynchronously for `DECLINE` and `REVIEW` only, about 2% of payments, off the 100 ms path (solution.md §5.9).
- **08-D:** (1) permutation importance on validation next to a planted random column, or retrain without the ID; (2) a drop no bigger than the random column's means the trees fit noise; (3) a real drop on an ID points to leakage, such as IDs issued in time order or after the outcome.

</details>

<details><summary>Build notes</summary>

- **Knob changes:** none. The spec's configuration ran as written: lab 03's split (stratified 80/20, `random_state` = seed), `LGBMClassifier(n_estimators=100, random_state=seed)`, then 500 trees, the random column from `np.random.default_rng(seed).integers(0, 10_000)`, and validation permutation importance with roc_auc and 5 repeats.
- **Effects:** dropping both columns and the 500-tree split rank both clear 2x the spread. Dropping `relationship` alone does not, by design (see P2).
- **Precomputed steps:** none. Every seed-0 run took under a minute, so the lab's Compute line is 3 runs x 1 min.
- **Where the spec was silent (simplest correct choice):**
  - `verbose=-1` on every `LGBMClassifier`. It silences LightGBM's warnings and leaves the model unchanged.
  - Ranks: 1 = most important, `method="min"`, so ties share the better rank (split counts can tie: `education` and `relationship` do at seed 0). The lab file says so next to the Predict table.
  - AUC lines carry `unit=fraction`, as in lab 03, and the P2 row asks for each size as an AUC difference on the 0 to 1 scale, so a range written in AUC points is not misgraded.
  - Reason codes: the 3 columns with the largest positive SHAP contribution (log-odds) for each of the 3 highest-scored validation rows, as one RESULT token `column=value:log_odds`. The script asserts that each row's contributions plus the expected value add up to the raw score.
  - `sex` is ranked among all 15 inputs. A build-time inspection (not a RESULT line) found `random` below `sex` by mean absolute SHAP at every seed, so `sex` has the same rank among the 14 real columns.
  - Timing: the booster scores a category-coded numeric row with `num_threads=1`, as the median of 200 calls after 20 warm-up calls. In a probe, the scikit-learn wrapper's per-call DataFrame conversion cost more than either the score or the explanation, which hid the TreeSHAP cost. One thread matches one request per worker and avoids OpenMP (Open Multi-Processing, LightGBM's thread pool) wake-up noise on a busy CPU. Even so, the one-row score is mostly fixed call overhead (see P1), so the two lines measure per-request latency, not the compute ratio of the two algorithms. The script asserts the booster's score equals `predict_proba` on the DataFrame row.
  - P2's change lines read the same seed's `baseline.auc` through `labkit.prior` instead of retraining the baseline. Each reference baseline ran before its change run. Without a stored baseline the script prints a NOTE and only the raw AUCs.
  - `--check`: a 20-row fixture (10 positives, 10 negatives) with a scrambled index and a category column no tree uses, scored with 50 repeats. In a probe, three correct implementations with different shuffling code failed a 5-repeat value check on some of 40 seeds; with 50 repeats none did, and five common bugs (category dtype lost, index-aligned assignment, reset index, sum instead of mean, sign flip) all fail. The rebuild's 0.06 tolerance came from the same probe (100 seeds).
  - The TODO docstring names the positional shuffle, `X[col].values[rng.permutation(len(X))]`, a deviation from a bare TODO. The two obvious ways to shuffle both fail on this table, and a build check confirmed each: a NumPy shuffle of a category column returns plain objects, which LightGBM rejects, and a pandas shuffle assigned back realigns on the index, which undoes the shuffle. The positional line keeps a category column's dtype and skips index alignment, so the TODO fits its 10-minute baseline block. The learner still writes the base score, both loops, the drop and the mean.
  - Fallback data: `load_data` runs lab 03's category line, `X[text].astype(object).astype("category")`, which sorts every text column's categories, then casts the numeric columns to int64. The OpenML parquet copy lists the categories of 7 of the 8 text columns in a different order from the ARFF (Attribute-Relation File Format) file, and it stores six numeric columns as uint8 or float64. Without the two lines, the same rows get other category codes on the parquet path. In a build probe the seed-0 100-tree model then differed: other split counts, another split rank for `random`, and over a tenth of the validation probabilities moved by more than 0.05. Reason codes also printed `15024.0` for `15024`. With the two lines, the reference's own `load_data` returns identical frames from both sources at seeds 0, 1 and 2 (pandas `assert_frame_equal`), so every reference number holds on either source. On the ARFF both lines change nothing, because its categories are already sorted and its numbers are already int64. The whole-number cast is not in lab 03, which prints no raw values; here it keeps the reason-code strings the same on both sources.
  - The lab file's Goal line rewords the spec's goal ("show a random column fooling one of them") so the lab file does not say that a measure gets fooled.
- **Fix round (review findings):** `load_data` gained lab 03's category line and the whole-number cast (above), the AUC lines gained `unit=fraction`, and the TODO docstring now says "by position, not by index label". The script hash changed, so the starter was regenerated with `make_c_starter` and all 9 reference runs were rerun, plus `--download`, `--smoke` and `--check` on both files (the reference passes `--check`, the starter fails it with NotImplementedError). Every value came back identical to the first build except the wall times and the two timing lines, which are remeasured on every run.
- **Prototype comparison.** The .json notes field holds the spec's values. Prototype values (spec, answers only): the random column ranked 5th of 15 by split count at 100 trees and 1st at 500, 10th and 8th by gain, last by permutation; dropping one correlated column cost 0.0006 AUC, both 0.0275; sex ranked 9th of 14 by mean |SHAP|. Build: no knob changes and no precomputed steps; the drop-one effect is a null effect by design (correlated features share importance).
  - Split count at 100 trees: prototype 5th, ours 5 at seed 0. Match.
  - Split count at 500 trees: prototype 1st, ours 2 at seed 0 (1 at seed 1, spread 1). A one-rank gap, within 2x the spread. Cause: `fnlwgt` beats `random` by a few splits at seeds 0 and 2 (see the break table in the .out).
  - Gain: prototype 10th and 8th, ours 10 and 8 at seed 0. Match.
  - Permutation at 100 trees: prototype last, ours 14 at seed 0 and 15 at seeds 1 and 2 (spread 1). Within the spread; at seed 0 `education` sits below it (see P1).
  - Permutation at 500 trees, reading the prototype's "last by permutation" as both tree counts: prototype last, ours 11 at seed 0, 15 and 14 at seeds 1 and 2 (spread 4). The seed-0 gap is 4 ranks, within 2x the spread. At 500 trees the model leans on `random` more, so its drop wanders further around zero (see P3).
  - One correlated column: prototype cost 0.0006 AUC, ours -0.000345235 at seed 0 (tolerance 0.001021545). Within 2x the spread.
  - Both columns: prototype 0.0275, ours -0.0277801 at seed 0. Match.
  - `sex` by mean absolute SHAP: prototype 9th of 14, ours 9 of 15 at every seed, also 9th of the 14 real columns. Match.

</details>
