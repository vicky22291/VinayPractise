# 19. Time split and as-of features: point-in-time correct joins: reference answers

> Spoilers. The AI opens one block at a time, only after that step's prediction row exists and the learner pasted their own RESULT lines, or after 'debrief 19'.

- **HW:** `HW chip='Apple M4 Pro' cpu=14 gpu=20 mem_gib=24 macos=26.5.1 python=3.13.7 torch=2.14.1 device=cpu`
- **Seeds:** 0, 1 and 2 for every step (light lane). The seed changes LightGBM's row and column sampling and the random split. The synthetic stream is always seed 0, and the time split has no randomness of its own.
- **Reference:** `answers/19_as_of_features_ref.py` (sha256 prefix `9c3c4470d0b6829f`). It holds both paths: `--baseline` and `--change` run `features_v0.py` as shipped, and `--break` swaps the terminal input. From the module folder: `python ../answers/19_as_of_features_ref.py --break`.
- **Data:** the synthetic paystream v1 at seed 0: 1,795,646 rows, 17,821 frauds, 183 days. Raw seed-0 output: `answers/19-as-of-features.out`.
- **Runs and wall times** (seconds, seeds 0, 1, 2, measured while other labs' jobs shared the CPU): baseline 34.2, 19.9, 32.3; change 38.1, 25.7, 32.0; break 120.0, 118.6, 105.2.
- **Tolerance:** tol = spread (max - min) over seeds 0, 1, 2. Precomputed steps: none.

<details><summary>P1. Test AUC at seed 0 on the time split (train days 0 to 119, test days 127 to 182), inputs as shipped</summary>

**Answer: 0.928158**, tolerance ±0.009924 (the seed spread). Seeds 1 and 2: 0.918234 and 0.924933.

```
RESULT P1.auc=0.928158 unit=auc seed=0
RESULT baseline.top3=terminal_fraud_rate,amount,amount_over_30d_mean seed=0
RESULT baseline.top1_share=0.467362 unit=fraction seed=0
```

Seeds 1 and 2: `baseline.top3` is the same at seed 1 and `terminal_fraud_rate,amount_over_30d_mean,cust_mean_7d` at seed 2; `baseline.top1_share` is 0.48788 and 0.464253.

**Why.** AUC is the chance that a random fraud outscores a random legitimate payment, so the 0.99% fraud rate does not pull it down. The time-split test set mixes four synthetic fraud scenarios, and the overall AUC is their fraud-weighted mean (exact, to 6 digits). Card testing is 2300 of the 7346 test frauds and starts on day 160, so no training day holds it: it scores 0.804077 and is the term that moves with the seed (spread 0.032499). Whether the rest of the number is earned is P3's question.

**Common wrong prediction:** well under 0.9, where real out-of-time fraud models often land. This synthetic stream plants two scenarios on the amount (over 220, and 5 x the customer's usual amount), which any tree ranks almost perfectly.

</details>

<details><summary>P2. A random 80/20 split instead of the time split: AUC direction and size</summary>

**Answer: up, by 0.0603581** at seed 0 (`P2.auc` 0.988516), tolerance ±0.010696 on the delta. Seeds 1 and 2: delta 0.0710541 and 0.0631274, `P2.auc` 0.989288 and 0.988061 (spread 0.001227). Over the three seeds the lift is 0.0648467, about 6 times the larger seed spread (0.009924), so it is real.

```
RESULT P2.auc=0.988516 unit=auc seed=0
RESULT P2.auc_delta=0.0603581 unit=auc seed=0
```

**Why.** A random split draws test rows from all 183 days, so card testing (days 160 to 182) sits in the training rows too, and the model learns it: card-testing AUC goes from 0.804077 on the time split to 0.993971 on the random split. Scoring card testing that way on the time split would lift P1 to 0.9876 on its own, so nearly the whole difference is one attack the time split never trained on. The random test set is also only 466 card-testing frauds of 3559 (0.130936), against 2300 of 7346 (0.313096) on the time split, so the hardest scenario weighs less. Rules of ML #33 is the fix: test on the days after training.

**Common wrong prediction:** about the same, because the synthetic stream has no drift and 1,795,646 rows is plenty. A new attack in the test window is drift, and a random split hides it.

</details>

<details><summary>P3. FIND-IT: is the shipped AUC honest? The time-split AUC with the honest inputs of the Terms</summary>

**Answer: no. The honest AUC is 0.709088** at seed 0, tolerance ±0.015956. Seeds 1 and 2: 0.693132 and 0.69381. Over the three seeds the shipped number is too high by 0.225098 (`P1.auc` minus `P3.auc`; the signed `P3.auc:P1.auc` effect in the .json is -0.225098), 14 times the larger seed spread.

```
RESULT P3.auc=0.709088 unit=auc seed=0
RESULT break.top3=amount,amount_over_30d_mean,cust_mean_30d seed=0
RESULT break.top1_share=0.407778 unit=fraction seed=0
RESULT break.auc_s1=0.999297 unit=auc n=333 seed=0
RESULT break.auc_s2=0.6257 unit=auc n=3135 seed=0
RESULT break.auc_s3=0.980741 unit=auc n=1578 seed=0
RESULT break.auc_s4=0.594354 unit=auc n=2300 seed=0
```

**Why.** The honest terminal input counts a fraud only once its dispute has arrived, 7 to 120 days after the payment. A terminal compromised for 28 days has had almost none of its frauds disputed while the attack runs, so the compromised-terminal scenario falls from 0.979889 as shipped to 0.6257 as of t. The amount scenarios hold (0.999297 and 0.980741), because the amount inputs carry them, and card testing stays weak (0.594354), because no training day holds it. The honest model's top inputs are the amount features; the as-of terminal input is not in the top 3 at any seed.

**Common wrong prediction:** a small drop of 0.02 to 0.05, "because the terminal rate is one input of ten". As shipped it held 0.467362 of all gain, and it carried a whole scenario.

**If your own fix scores differently.** The lab file's Terms (Honest inputs) fix the target: every shipped input that obeys the rules stays as shipped, and in the terminal input's place goes a count of the frauds at the terminal whose `label_available_at` falls in [t - 30 d, t). That is the reference input, so a fix written to the Terms builds the input `P3.auc` measures. The README's key formula windows the same count on event time instead. That is honest too, but it is another input: a build probe on the same model, split and seed gave it 0.7314, against 0.7091 for the reference input. Grade P3 against `P3.auc` and its spread. Judge a fix that departs from the Terms by whether every input is computable at t.

</details>

<details><summary>Rebuild check</summary>

- Solution: `answers/rebuild/19_point_in_time_join.py`. Stub: `answers/rebuild/stubs/19_point_in_time_join.py`, which the AI copies into `m4-production-ml-payments/rebuild/` at 0:47.
- `rebuildcheck`: the stub fails as it should (NotImplementedError, exit 1) and the solution passes (exit 0, `check: PASS`). Verdict: REBUILDCHECK OK.
- `check()` compares `known_before()` with a brute-force numpy count on 150 events and 60 labels at 5 terminals inside 60 seconds; 27 events have a label at the same terminal in the same second. In a build test, `allow_exact_matches=True` failed it (24 of 150 counts differ) and dropping `by="terminal_id"` failed it (149 of 150).

</details>

<details><summary>Find-it debrief</summary>

**The planted bug.** `scripts/features_v0.py`, in `build_features()`, the last input:

```python
out["terminal_fraud_rate"] = tx.groupby("terminal_id")["is_fraud"].transform("mean")
```

**Why it inflates the AUC.** It is the terminal's final fraud rate: the mean of `is_fraud` over every payment the terminal ever made, read from today's table. At prediction time t, three parts of that mean did not exist yet:

1. The labels of payments after t: the future.
2. The labels of past payments whose dispute had not arrived (`label_available_at >= t`): about half the frauds of the last 120 days.
3. The row's own label, which arrives 7 to 120 days after t.

So a compromised terminal looks compromised from its first fraud, and no fraud row ever sits at a terminal with rate 0. The customer windows above it are honest: `rolling(..., closed="left")` on a time index sees only rows strictly before t.

**The fix.** For each payment, count the frauds at its terminal whose dispute arrived in the 30 days before t: `label_available_at` in [t - 30 d, t). The reference takes the difference of two point-in-time joins, at t and at t - 30 d. Each join is a per-terminal cumulative count in `label_available_at` order, joined with `pd.merge_asof(by="terminal_id", allow_exact_matches=False)` (`known_before()`, the rebuild). Windowed, not cumulative: in a build probe, the all-time count averaged 0.1305 on training rows and 0.7892 on test rows, so one value meant different things in the two periods.

**The honest numbers.** Test AUC at seed 0, with the seed spread in brackets:

| Terminal input | Time split | Random split |
|---|---|---|
| As of t: disputes that arrived in the last 30 days | 0.709088 (0.015956) | 0.802777 (0.013797) |
| Final rate, own label left out | 0.845627 (0.015037) | 0.986601 (0.001948) |
| Final rate, own label in (as shipped) | 0.928158 (0.009924) | 0.988516 (0.001227) |

The as-shipped row equals `P1.auc` and `P2.auc` at every seed, as it should: the same inputs, model and seed.

**For the Record table.** The six table lines, then the reference's per-scenario lines as shipped, at seed 0 (the `--break` per-scenario lines are in the P3 block). Show them only after the learner's fix or 'debrief 19', never with the P1 or P2 answer: the as-shipped scenario 2 line is a clue to the planted problem.

```
RESULT break.auc_time_asof=0.709088 unit=auc seed=0
RESULT break.auc_random_asof=0.802777 unit=auc seed=0
RESULT break.auc_time_final_others=0.845627 unit=auc seed=0
RESULT break.auc_random_final_others=0.986601 unit=auc seed=0
RESULT break.auc_time_final_all=0.928158 unit=auc seed=0
RESULT break.auc_random_final_all=0.988516 unit=auc seed=0
RESULT baseline.auc_s1=0.999323 unit=auc n=333 seed=0
RESULT baseline.auc_s2=0.979889 unit=auc n=3135 seed=0
RESULT baseline.auc_s3=0.99122 unit=auc n=1578 seed=0
RESULT baseline.auc_s4=0.804077 unit=auc n=2300 seed=0
RESULT change.auc_s1=0.999044 unit=auc n=254 seed=0
RESULT change.auc_s2=0.985686 unit=auc n=1891 seed=0
RESULT change.auc_s3=0.988659 unit=auc n=948 seed=0
RESULT change.auc_s4=0.993971 unit=auc n=466 seed=0
```

**What each leak fakes** (the mean over the three seeds, with the larger seed spread of the two cells):

- Future and unarrived labels, time split: +0.139295 (spread 0.015956).
- The row's own label, time split: +0.085803 (spread 0.015037).
- The random split, honest inputs: +0.108169 (spread 0.015956).
- The random split, final rate without the own label: +0.148548 (spread 0.015037).
- Future and unarrived labels, random split: +0.179675 (spread 0.013797).
- The row's own label, random split: +0.00210133, inside 2 x its spread (0.001948), so a small effect. Once every other row's final label is in, the random split is near the ceiling, and the own label has little left to add.
- Everything at once: the as-shipped random-split AUC is 0.988516, against the honest time-split 0.709088.

**What the honest model leans on.** `break.top3` is `amount,amount_over_30d_mean,cust_mean_30d` at seeds 0 and 1, and `amount_over_30d_mean,cust_mean_7d,cust_count_30d` at seed 2; the top input's share of gain is 0.407778, 0.462112 and 0.40659. As shipped, `terminal_fraud_rate` held 0.467362 at seed 0. The as-of terminal input is weak because its signal arrives late. In build probe C, even the event-time version of it held only 0.143 of all gain.

**Scope.** The training target is the final label, as the spec has it. At a real day-127 cutoff, many disputes on training days would still be in flight. Lab 21 measures that.

</details>

<details><summary>Card drafts</summary>

| ID | Lab | Type | Question |
|---|---|---|---|
| 19-M | 19 | M | A fraud model's input is "the terminal's fraud rate", one groupby over the full labelled table. Name the three things inside that number that a live system could not know at prediction time t. |
| 19-N | 19 | N | On the synthetic paystream time split (train days 0 to 119, test days 127 to 182), roughly how much test AUC did the shipped terminal fraud rate fake over an as-of terminal input, and which fraud scenario lost the most? |
| 19-D | 19 | D | Offline AUC jumps by about 0.2 after a teammate adds a "merchant fraud rate" input, and it tops the gain importance. What is your first check, and what result confirms a leak? |

Keys:

- **19-M.** Must mention: (1) labels of payments after t; (2) labels of past payments whose dispute had not arrived (`label_available_at >= t`); (3) the row's own label.
- **19-N.** About 0.2: 0.928158 as shipped against 0.709088 as of t at seed 0, and 0.225098 on average over seeds 0 to 2. Must mention: (1) about 0.2 of AUC; (2) compromised terminals (scenario 2) lost the most, 0.979889 to 0.6257; (3) why: disputes arrive 7 to 120 days after each fraud, so a 28-day compromise is mostly over before its first label is known.
- **19-D.** Recompute the input as of each payment's time and retrain on the same out-of-time split. Must mention: (1) count a label only if `label_available_at < t`; (2) leave the row's own label out; (3) a large AUC drop on the out-of-time split confirms the leak.

D, not T, this time: lab 19 is a find-it lab, and the debugging card rehearses its first check.

</details>

<details><summary>Build notes</summary>

**Where the spec is silent, and why.**

- **Model.** LightGBM (gradient boosting, the module's thread for this lab), `LGBMClassifier(n_estimators=200, learning_rate=0.05, min_child_samples=200, subsample=0.8, subsample_freq=1, colsample_bytree=0.8, random_state=seed, n_jobs=4)`. Bagging stays on so that `--seed` changes the model, as the brief asks.
- **Knob change, and why.** The simplest option, LightGBM's defaults plus that bagging, failed the 2x rule. In build probe A (shipped inputs, time split, seeds 0, 1, 2) it gave 0.8539, 0.7487 and 0.8321, a spread of 0.1052, larger than the P2 effect. Nearly all of that spread is card testing: without it the AUC was 0.9721, 0.9712 and 0.9788, while card testing scored 0.595, 0.261 and 0.510. Card testing never appears in training, so its score is extrapolation, and default trees extrapolate it erratically. A lower learning rate (0.05) and larger leaves (`min_child_samples=200`) steady it: P1's spread is now 0.009924, and every effect the lab teaches clears 2 x its spread. With the default settings, two runs of seed 1 on the same code and data disagreed in the third decimal. With the reference settings, two separate runs of each baseline seed matched to 6 digits.
- **Random split.** Exactly 20% of rows, from `numpy.random.default_rng(seed).permutation`.
- **Honest terminal input.** A 30-day window on arrival time, the difference of two `known_before()` joins: the rebuild's mechanism, and the spec's "frauds known in the last 30 days". The README allows the event-time window too, so the lab file's Terms state the rule P3 grades against (Honest inputs) in general words that name no input: the payment's own amount and time, other payments strictly before t, a label only once `label_available_at` is strictly before t, and any input that breaks these replaced by a 30-day count on the same key, on the arrival time for labels. Build probe C on the reference model, time split, seed 0: event-time window 0.7314, arrival-time window 0.7091, cumulative 0.7053. The arrival-time count also starts low in the first weeks of the stream, because few disputes have had time to arrive (mean 0.0832 on training rows, 0.2791 on test rows; event-time 0.0162 and 0.0232).
- **Robust `--break`.** It selects the nine non-terminal inputs by name, so it still runs after the learner edits `features_v0.py`, whatever the fixed terminal column is called.
- **Diagnostics.** Each mode also prints the AUC of each fraud scenario against all legitimate test rows (`<mode>.auc_s1` to `auc_s4`, with `n=` the scenario's test frauds). The Record table gives every RESULT name its own row, these included, marked reference; the Find-it debrief holds the seed-0 lines to show. Four of the six 2x3 table names (rows `final_others` and `final_all`) describe the planted leak, so the Record table lists those four by table row and split, without the name.

**Prototype comparison** (the spec's prototype values against the reference at seed 0):

| Cell | Prototype | Reference, seed 0 | Seed spread | Verdict |
|---|---|---|---|---|
| Time, as of t | 0.62 | 0.709088 | 0.015956 | Higher by more than 2 x the spread: explained below |
| Time, final rate without own label | 0.77 | 0.845627 | 0.015037 | The same |
| Time, final rate with own label | 0.90 | 0.928158 | 0.009924 | The same |
| Random, as of t | 0.79 | 0.802777 | 0.013797 | Inside 2 x the spread |
| Random, final rate without own label | 0.98 | 0.986601 | 0.001948 | Just above the top of the prototype's rounding interval, by less than 2 x the spread; LightGBM's defaults give 0.9813 (probe B) |
| Random, final rate with own label | 0.99 | 0.988516 | 0.001227 | Inside 2 x the spread |

Every direction agrees: each leak raises the AUC, and the random split beats the time split in every row. The synthetic data agrees too: 1,795,646 rows, as in the prototype. The random column matches. The time column is higher in all three rows, so the build looked for the cause before calling it a bug.

The cause is the card-testing term. On the time split it is 2300 of 7346 test frauds (0.313096). It is an attack the training days never contain, so its AUC is the model's extrapolation, and this lab's runs and probes put it anywhere from 0.261 to 0.804077. The other three scenarios are steady (time split, seed 0, without card testing: 0.7614 as of t and 0.9847 as shipped). With them scored as here, the prototype's time cells imply card-testing AUCs of 0.31, 0.34 and 0.71 (using probe B's 0.9677 for the middle row), all inside that range. LightGBM's defaults (probe B, no bagging) give 0.6646, 0.7760 and 0.7761 on the time split, with card testing at 0.466, 0.356 and 0.344, and 0.8021, 0.9813 and 0.9847 on the random split, where card testing is in training. So the gap is a model-setting difference in the one term that no split-respecting model can learn. It is not a feature or join bug: the random column, where card testing is in training, matches.

**Deviations from the spec.**

- The spec's goal ("terminal-risk features ... with label delay") and its Borrowed-from note ("terminal risk behind a delay") name the planted bug, so the lab file rewords both. The lab file's Concept link sends the learner to the README's Key formula only once they have found the problem, and says the Terms decide which clock a window runs on. Its Repo link says to open the deep dives at close, because §2 of the lifecycle deep dive describes the same as-of-today join.
- `features_v0.py` is 31 lines; the spec says 30.
- The P1 and P2 blocks open before the break, so they never name the leaking input or the scenario it carries.

</details>
