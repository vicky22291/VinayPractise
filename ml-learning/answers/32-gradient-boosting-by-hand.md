# 32. Gradient boosting by hand: each small tree fits what the others missed: reference answers

> Spoilers. The AI opens one block at a time, only after that step's prediction row exists and the learner pasted their own RESULT lines, or after 'debrief 32'.

- **HW:** `HW chip='Apple M4 Pro' cpu=14 gpu=20 mem_gib=24 macos=26.5.1 python=3.13.7 torch=2.14.1 device=cpu`
- **Seeds:** 0, 1 and 2 for every step (light lane). The seed sets the stratified split (`random_state`), the tie-breaks inside each `DecisionTreeRegressor`, and LightGBM's `random_state`.
- **Reference script:** `answers/32_gradient_boosting_by_hand_ref.py` (script_sha256 `8cc4b91a349d714a`). Values by seed: `32-gradient-boosting-by-hand.json`. Raw seed-0 output: `32-gradient-boosting-by-hand.out`.
- **Runs and wall times (seeds 0 / 1 / 2):** baseline 38.0 / 37.7 / 30.3 s; change 11.5 / 15.7 / 11.7 s; break 9.5 / 11.8 / 9.1 s. All cpu, light lock, run while other build jobs shared the machine.
- **Tolerance rule:** tol = spread (max - min) over seeds 0, 1, 2; heavy labs: the baseline spread applies to every step.
- **Metric definitions the numbers depend on:** every log-loss is `sklearn.metrics.log_loss` on sigmoid(raw score), which clips probabilities to [eps, 1 - eps] with float64 eps; every AUC (area under the receiver operating characteristic curve) is `roc_auc_score` on the raw score (log-odds). LightGBM is scored the same way, on `predict_proba(X, raw_score=True)`; its built-in eval metric is never read. The lab file gives the learner the same definitions.

<details><summary>P1. Validation AUC of your loop after 300 depth-3 trees at learning rate 0.1, minus LightGBM's (learning rate 0.1, early stopping 50)</summary>

**Answer:** -0.019119 at seed 0, tolerance 0.0015949999999999992 (the seed spread). The loop sits below LightGBM at every seed.

Seed-0 RESULT lines:

```
RESULT P1.auc_gap=-0.019119 unit=auc seed=0
RESULT baseline.loop_auc=0.909384 unit=auc seed=0
RESULT baseline.lgbm_auc=0.928502 unit=auc seed=0
RESULT baseline.loop_logloss_10=0.494205 unit=logloss seed=0
RESULT baseline.loop_logloss_100=0.362802 unit=logloss seed=0
RESULT baseline.loop_logloss_300=0.321561 unit=logloss seed=0
RESULT baseline.lgbm_logloss=0.275635 unit=logloss seed=0
RESULT baseline.lgbm_best_iter=173 unit=trees seed=0
RESULT baseline.lgbm_depth=11.8844 unit=levels seed=0
RESULT baseline.lgbm_us_300=32.542 unit=us device=cpu batch=1 warmup=20 n=200 stat=median threads=1 seed=0
RESULT baseline.lgbm_us_1000=58.958 unit=us device=cpu batch=1 warmup=20 n=200 stat=median threads=1 seed=0
```

Other seeds: `P1.auc_gap` -0.017524 (seed 1), -0.0180343 (seed 2). Loop AUC 0.912843 and 0.913431; LightGBM AUC 0.930367 and 0.931465. LightGBM's best iteration 133 and 176 (spread 43). Mean LightGBM tree depth 12.0075 and 11.9375 split levels. The loop-minus-LightGBM AUC effect over the three seeds is -0.01822533333333339 against a spread of 0.004047000000000023, so the gap is real, not noise.

Why: each loop leaf holds the mean residual, a plain gradient step, while LightGBM's leaf is a Newton step (the sum of residuals over the sum of p(1 - p)), which is several times larger in size because p(1 - p) is at most 0.25. So at rate 0.1 the loop moves slowly and is still descending at tree 300 (0.494205, 0.362802, 0.321561 at trees 10, 100, 300). LightGBM's trees are also much deeper (11.8844 split levels on average, 31 leaves, against 3 levels and 8 leaves), so each tree captures interactions a depth-3 tree cannot. Early stopping then picks LightGBM's tree count on the same validation rows, which flatters it slightly.

Common wrong prediction: a gap near zero, from "300 trees is plenty". With mean-residual leaves at rate 0.1 the loop has not converged by tree 300. The opposite miss is a gap of several AUC points: the 10-line loop does get close.

The timing rows are a Record, not a prediction: at seed 0, one single-row call on one thread took 32.542 us with the first 300 trees and 58.958 us with all 1,000. Seeds 1 and 2 gave 29 and 54.104 us, then 35.9375 and 63.0625 us. The spread (6.9375 and 8.9585 us) reflects a shared machine: the seed-0 and seed-1 baselines ran at the same time, beside other labs' build runs. A straight line through the two points puts the fixed per-call overhead (Python and input checks) at most of the 300-tree time, and the per-tree walk at tens of nanoseconds. §10.1 of the repo design estimates about 2.5 ms for about 1,000 trees, about 2.5 us per tree, dominated by cache misses. Its trees are a few hundred nodes each (§10.1), of depth 8, over about 300 features (§10.2). So its model is far larger than this one, and a request's node reads mostly miss the CPU caches. This benchmark is a warm-cache floor: it scores 220 validation rows of 14 features back to back against trees of 31 leaves (at most 61 nodes each), so the whole model stays cached. Fetching the 300 features is a separate stage of the design's latency budget, outside both numbers.
</details>

<details><summary>P2. Learning rate 1.0 in your loop: validation log-loss at tree 300, direction and size as the log-loss difference, rate 1.0 minus rate 0.1</summary>

**Answer:** down. At seed 0 the delta is -0.0423736 (`P2.loop_logloss_300` 0.279188 against `baseline.loop_logloss_300` 0.321561). Tolerance: 0.0031079999999999997 on the value and 0.004829100000000003 on the delta. The effect over three seeds is -0.04210400000000001 against a spread of 0.0034989999999999744, so it passes the 2x spread rule.

Seed-0 RESULT lines:

```
RESULT P2.loop_logloss_300=0.279188 unit=logloss seed=0
RESULT P2.loop_logloss_300_delta=-0.0423736 unit=logloss seed=0
RESULT change.loop_logloss_10=0.358523 unit=logloss seed=0
RESULT change.loop_logloss_100=0.29111 unit=logloss seed=0
RESULT change.loop_auc=0.927098 unit=auc seed=0
```

Other seeds: `P2.loop_logloss_300` 0.278507 (seed 1) and 0.27608 (seed 2); delta -0.039555 and -0.0443841; AUC 0.927884 and 0.930271.

Why: a mean-residual leaf is bounded (a residual lies between -1 and 1), so even at rate 1.0 each tree moves F by at most 1, and the step shrinks as the residuals shrink. At rate 0.1 the loop needs roughly ten times the trees to travel as far, so at tree 300 it is still underfit, and rate 1.0 simply gets further. Rate 1.0 is still improving between tree 100 (0.29111) and tree 300 (0.279188): small trees with gradient steps have not started to overfit. Its AUC (0.927098) is close to LightGBM's at rate 0.1 (0.928502): over three seeds the gap averages -0.0016936666666667044 against a seed spread of 0.0031729999999999814, inside one spread, though the loop sits below LightGBM at every seed.

Common wrong prediction: up, from the textbook rule "a learning rate of 1.0 overfits". That rule holds for Newton-step boosters with big trees (the break shows it), not for this loop at 300 trees.
</details>

<details><summary>P3. LightGBM with learning_rate 1.0, 300 trees and no early stopping: validation log-loss at tree 300</summary>

**Answer:** 6.73391 at seed 0, tolerance 0.41859. Seeds 1 and 2: 6.64654 and 7.06513. The effect against LightGBM at rate 0.1 is 6.541957333333333 against a spread of 0.41859, so it passes the 2x spread rule.

Seed-0 RESULT lines:

```
RESULT P3.lgbm_logloss_300=6.73391 unit=logloss seed=0
RESULT break.lgbm_auc_300=0.784803 unit=auc seed=0
RESULT break.lgbm_best_iter=5 unit=trees seed=0
RESULT break.lgbm_best_logloss=0.291881 unit=logloss seed=0
```

Other seeds: AUC at tree 300 0.781876 and 0.802646; best iteration with `early_stopping(50)` 4 and 5; log-loss there 0.298851 and 0.290167.

Why: LightGBM sets each leaf to the sum of residuals over the sum of hessians, p(1 - p), with no shrinkage at rate 1.0 and no L2 penalty by default. As rows get fit, p(1 - p) shrinks toward zero, so a leaf whose residual sum comes from confidently wrong rows divides a large number by a tiny one. The step stays finite: LightGBM's default `min_sum_hessian_in_leaf` of 1e-3 (`min_child_weight` in the scikit-learn API) rejects any split that would leave a leaf with a smaller hessian sum, so a leaf's step is at most 1,000 times the size of its residual sum. That still allows huge steps, and over 300 trees they saturate the scores: most validation probabilities round to exactly 0 or 1. Each confidently wrong row then costs the clip, -log(eps) = 36.04 for float64, so the tree-300 log-loss is about 36 times the share of rows that are confidently wrong. The ranking breaks too, not just the probabilities (AUC 0.784803 at tree 300).

The early-stopping rows are a Record, not a prediction: `early_stopping(50)` keeps tree 5 at 0.291881, which rescues the model. It stays worse than rate 0.1 (0.275635 at tree 173), because a 5-tree model has taken only a few huge steps. That holds at every seed, by a margin near the 2x line: over three seeds the gap is 0.020397 against a spread of 0.00868399999999997, and seed 0 alone falls short of twice the spread.

Grading note: the lab file asks for sklearn's `log_loss` and `roc_auc_score` on raw scores for both models. A harness that reads LightGBM's own `binary_logloss` instead gets a slightly lower number, because LightGBM clips at 1e-15 rather than at float64 eps. One that takes AUC from probabilities gets a lower AUC on this saturated model (a probe at seed 0), because the probabilities tie at exactly 0 and 1.

Common wrong prediction: a little above the best value (0.3 to 0.5), from "LightGBM is robust, it only overfits mildly". The real value is more than an order of magnitude above the base-rate model's log-loss. The clip sets the cost of each confidently wrong row (about 36). The model sets how many such rows there are, and the total is roughly that cost times their share.
</details>

<details><summary>Rebuild check</summary>

- Solution: `answers/rebuild/32_boosting_loop.py`. Stub: `m5-under-the-hood/rebuild/32_boosting_loop.py`.
- `rebuildcheck`: "stub fails as it should (exit 1)", "solution passes (exit 0)", REBUILDCHECK OK.
- `check()` runs on synthetic `make_classification` data (4,000 rows, 3 informative features, `class_sep=2.0`, about 25% positive). It asserts five things: F0 equals log(p / (1 - p)); one tree at lr 1.0 moves every training score 10 times as far as one tree at lr 0.1 (to 1e-9); with X_new = X, F_new equals the last training scores (to 1e-9); the training log-loss never rises over the first 20 trees at rate 0.1; and test AUC is within 0.01 of `GradientBoostingClassifier(max_depth=3, learning_rate=0.1, n_estimators=50)`.
- A probe ran 21 loops through `check()`. Eight correct loops pass: the solution, tree `random_state` 1, 42 or None, a hand-written sigmoid, F_new summed from the stored trees at the end, and an in-place update with or without a copy in history. Eleven wrong loops fail: F0 = 0, F0 = p, a tree fit to y - p every round, the step's sign flipped, one tree only, no sigmoid in the residual, no lr, lr hard-coded at 0.1, no lr on F_new, F_new starting at 0, and F_new stepping by 2 x lr. The last five passed the earlier three-assertion check.
- Two loops still pass: a residual scaled by a constant (2(y - sigmoid(F)) acts like a learning rate twice as large) and LightGBM-style Newton leaves (still gradient boosting on log-loss). Failing them would need the residual written into `check()`, which the learner reads at 0:47.
</details>

<details><summary>Card drafts</summary>

| ID | Lab | Type | Question |
|---|---|---|---|
| 32-M | 32 | M | Your loop's leaves and LightGBM's default leaves both start from the residuals y - sigmoid(F) of the rows that land in them. What value does each kind of leaf store, and what does that do to the step at learning rate 1.0? |
| 32-N | 32 | N | Your depth-3 loop on Adult at seed 0, 300 trees: validation log-loss at learning rate 1.0 minus at 0.1. Give the signed difference and the reason for its sign. |
| 32-D | 32 | D | After a retrain, a LightGBM model's validation log-loss is many times the base-rate model's, yet its AUC is still well above 0.5. What do you check first, what do you expect to find, and what fixes it? |

Keys:

- **32-M:** (1) The loop's leaf stores the mean residual, a gradient step between -1 and 1, so even at rate 1.0 a tree moves F by less than 1. (2) LightGBM's leaf stores the sum of residuals over the sum of p(1 - p), with p = sigmoid(F): a Newton step with no L2 penalty by default. It has the mean residual's sign and at least 4 times its size, because p(1 - p) is at most 0.25. (3) As rows get fit, p(1 - p) shrinks toward 0, so at rate 1.0 a leaf over confidently wrong rows takes a huge but finite step (LightGBM's default floor of 1e-3 on a leaf's hessian sum caps it at 1,000 times the size of the residual sum). Steps that large pin the probabilities at 0 or 1, while the loop's steps stay below 1 in size.
- **32-N:** (1) -0.0423736 at seed 0 (0.279188 at rate 1.0 against 0.321561 at rate 0.1), so rate 1.0 is lower. (2) Mean-residual steps are small, so at rate 0.1 the loop is still underfit at tree 300 and the larger rate gets further. (3) Rate 1.0 has not started to overfit: it is still improving between trees 100 and 300.
- **32-D:** (1) The training config: a learning rate near 1.0 with a fixed tree count and no early stopping. (2) Probabilities pinned at exactly 0 or 1, where each confidently wrong row costs the log-loss clip, about 36. (3) The fix is early stopping on held-out rows, which stops within the first few trees (tree 5 at seed 0).
</details>

<details><summary>Build notes</summary>

**Knob changes:** none. Every taught effect passed the 2x spread rule at the spec's configuration (P2 and P3 above; the loop-minus-LightGBM AUC gap in P1 too). Two Record effects are also registered in the .json, so the prose about them carries a spread: the rate-1.0 loop's AUC against LightGBM's at rate 0.1 (taught as close: inside one spread, not a 2x effect) and LightGBM's early-stopped log-loss at rate 1.0 against rate 0.1 (worse at every seed, just past 2x on the three-seed mean).

**Precomputed steps:** none. Seed-0 runs took 38.0, 11.5 and 9.5 s.

**Choices where the spec is silent, and deviations:**

- Categorical columns become integer codes (-1 for missing) in one numeric matrix that both the loop and LightGBM read. So LightGBM makes no native categorical splits (lab 03 uses pandas category columns). Why: `DecisionTreeRegressor` needs numbers, one matrix makes P1 a booster comparison, and with codes LightGBM at rate 1.0 builds all 300 trees at seeds 0, 1 and 2 (checked in tagged probes). With category columns it stops adding trees at 285 at seed 0, so "tree 300" would not exist.
- Validation is the 9,769 held-out rows of the lab 03 and 31 split. LightGBM's early stopping and every reported metric use those same rows, as the spec says ("early stopping on validation"). No third split was made.
- LightGBM's early-stopping run at rate 0.1 is capped at 1,000 trees; it stops long before that. The timing model is a separate LightGBM at rate 0.1 with 1,000 trees and no early stopping, timed with its first 300 and all 1,000 trees.
- Every log-loss uses sklearn's `log_loss` on sigmoid(raw score), and every AUC is on the raw score. On the saturated tree-300 model at rate 1.0, an AUC computed from probabilities adds ties at exactly 0 and 1 (a probe at seed 0 gave a lower value), so the raw score measures the ranking itself. The lab file states these definitions for both models, so a learner's harness scores LightGBM the same way.
- Added Record rows: `baseline.lgbm_depth` (the author note asks to record that LightGBM's trees are deeper) and `break.lgbm_auc_300` (the ranking breaks too).
- P3 stays in linear units, as the spec words it. The three seeds sit within one order of magnitude, and a log10 question would itself hint at a blow-up.
- The lab file's Goal drops the spec's "lands near LightGBM's AUC", because it states the size of the P1 answer before the learner predicts it.
- The rebuild check uses an easy synthetic set because on harder ones (5 informative features, `class_sep` 1.0) a correct 50-tree gradient-step loop is more than 0.01 AUC behind sklearn's Newton-step `GradientBoostingClassifier`. On the chosen set a correct loop passes with margin.
- The rebuild stub's docstring gives the interface only (the inputs, the returned triple, the tree class), so the 0:47 rebuild is recall, not copying: the start value, the residual and the update are left out. Its `check()` adds two assertions to the spec's three, because the three alone passed a loop with no learning rate. A review proposed a first-step assertion against a hand-built `DecisionTreeRegressor` step instead. That would print the residual and the update inside the stub's `check()`, so the build tests the same two things another way: the step scales with lr, and X_new is scored like the training rows.
- The timing rows were measured while other build jobs shared the machine: the seed-0 and seed-1 baselines ran at the same time, beside other labs' runs. The light lane allows this because no prediction asks about timing. The review fixes found the queue still busy, so the baselines were not rerun.
- Reference smoke runs all three mode blocks on 2,000 training and 1,000 validation rows with a 10-call timing. The starter's smoke has a 10-tree `GradientBoostingClassifier` stand in, so `report()` prints every contract name.
- `lightgbm` 4.7.0 deprecates `eval_set`; the reference uses `eval_X` and `eval_y`.

**Prototype comparison (spec values vs seed 0 here):**

- Loop at 0.1, 300 trees: prototype 0.318 and AUC 0.911; here 0.321561 and 0.909384. Within 2x the spread.
- Loop at 1.0: prototype 0.280 and 0.927, still improving; here 0.279188 and 0.927098, still improving (0.29111 at tree 100). Agrees.
- LightGBM at 0.1 with early stopping: prototype tree 131 (0.276, AUC 0.929); here 173 (0.275635, AUC 0.928502). The best-iteration spread is 43, so the gap is within 2x. A tagged probe with pandas category columns gave tree 131 exactly.
- LightGBM at 1.0 with early stopping: prototype best tree 6 (0.296); here 5 (0.291881). Within 2x the spread (1 tree and 0.00868399999999997).
- LightGBM at 1.0, tree 300, no early stopping: prototype 9.44; here 6.73391, a gap over 2x the spread (0.41859). Cause, from a tagged probe on the same seed-0 split: the prototype used pandas category columns and LightGBM's own `binary_logloss`. With category columns LightGBM stops at 285 trees; its own metric at the last tree gives 9.4399, and sklearn's `log_loss` on the same model gives 9.8512 (the gap between those two is the clip: 1e-15 against float64 eps). With the integer-coded matrix all 300 trees exist and the value is lower. Same direction, same mechanism: not a bug.
- Loop time: the prototype's 300 trees took about 14 s; here a whole change run (one 300-tree loop plus loading) took 11.5 s.
</details>
