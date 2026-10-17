# 23. Counterfactual evaluation: declined payments never get a label: reference answers

> Spoilers. The AI opens one block at a time, only after that step's prediction row exists and the learner pasted their own RESULT lines, or after 'debrief 23'.

- **HW:** `HW chip='Apple M4 Pro' cpu=14 gpu=20 mem_gib=24 macos=26.5.1 python=3.13.7 torch=2.14.1 device=cpu`
- **Seeds:** 0, 1 and 2, with `PYTHONHASHSEED=0`. Seed 0 is the script's default and the learner's run.
- **Reference script:** `answers/23_selective_labels_and_exploration_ref.py` (sha256 prefix `1fb8a8a2dae9d4fe`), run from `m4-production-ml-payments/` on the synthetic paystream (seed 0).
- **Runs and wall times:** 9 runs on the light lane, each while other build jobs shared the CPU. `--baseline` 41.1, 30.7, 44.2 s; `--change` 49.5, 53.3, 45.6 s; `--break` 97.5, 99.5, 73.0 s (seeds 0, 1 and 2). No precomputed steps.
- **Tolerance rule (from the .json):** tol = spread (max - min) over seeds 0, 1, 2; heavy labs: the baseline spread applies to every step. This lab is light, so every value carries its own spread.
- **Raw output:** `23-selective-labels-and-exploration.out` (seed 0). Values: `23-selective-labels-and-exploration.json`.

<details><summary>P1. Measured on champion-approved rows only, is the challenger's recall at a 1% decline rate higher or lower than its true recall, and by how many points?</summary>

**Answer:** lower, by 20.1791 points at seed 0 (`P1.gap_points` = -20.1791), tolerance 0.5694 points. Approved-only recall 0.146624, true recall 0.348415: the approved-only view reads well under half the truth.

Seed 0 RESULT lines:

```
RESULT P1.recall_approved_only=0.146624 unit=fraction seed=0
RESULT P1.recall_true=0.348415 unit=fraction seed=0
RESULT P1.gap_points=-20.1791 unit=points seed=0
RESULT baseline.champion_decline_rate=0.0100539 unit=fraction seed=0
RESULT baseline.challenger_decline_rate=0.0100539 unit=fraction seed=0
RESULT baseline.frauds=10476 unit=count seed=0
RESULT baseline.frauds_declined=2626 unit=count seed=0
RESULT baseline.hidden_share=0.250668 unit=fraction seed=0
RESULT baseline.catches_hidden_share=0.684658 unit=fraction seed=0
```

| RESULT | seed 0 | seed 1 | seed 2 | spread (tolerance) |
|---|---|---|---|---|
| `P1.recall_approved_only` | 0.146624 | 0.146973 | 0.1418 | 0.005173 |
| `P1.recall_true` | 0.348415 | 0.34307 | 0.341256 | 0.007159 |
| `P1.gap_points` | -20.1791 | -19.6097 | -19.9457 | 0.5694 |
| `baseline.frauds_declined` | 2626 | 2631 | 2641 | 15 |
| `baseline.hidden_share` | 0.250668 | 0.251145 | 0.2521 | 0.001432 |
| `baseline.catches_hidden_share` | 0.684658 | 0.679188 | 0.689231 | 0.010043 |

**Why.** The champion and the challenger rank the same frauds highest: large amounts (scenario 1 is any amount over 220, and scenario 3 multiplies the amount by 5) and sudden customer bursts. The champion's daily top 1% therefore holds 0.250668 of all era B frauds (2626 of 10476), and 0.684658 of the challenger's true catches sit inside those declines. The approved-only view drops exactly those rows from the numerator and the denominator, so it keeps mostly the frauds both models miss. The bias grows with how much the two models agree: a challenger identical to the champion would score 0 on this view.

**Common wrong prediction:** "about the same, because the champion declines only 1% of payments". That 1% holds a quarter of the frauds, and the easiest ones.

</details>

<details><summary>P2. With a logged 1% exploration slice of would-be declines approved and weighted by 100: the width of the 95% interval of the IPW recall estimate</summary>

**Answer:** 12.2816 points at seed 0 (`P2.ci_width`), tolerance 1.2218 points. The interval runs from 0.318909 to 0.441725 around an IPW estimate of 0.382581; the true recall is 0.348415 (P1).

Seed 0 RESULT lines:

```
RESULT P2.ci_width=12.2816 unit=points seed=0
RESULT change.ipw_recall_1pct=0.382581 unit=fraction seed=0
RESULT change.ci_lo_1pct=0.318909 unit=fraction seed=0
RESULT change.ci_hi_1pct=0.441725 unit=fraction seed=0
RESULT change.draws_mean_1pct=0.349895 unit=fraction seed=0
RESULT change.draws_width_1pct=12.4093 unit=points seed=0
RESULT change.ci_width_0p1pct=33.9579 unit=points seed=0
RESULT change.ci_width_5pct=5.10079 unit=points seed=0
RESULT change.explored_0p1pct=8 unit=count seed=0
RESULT change.explored_frauds_0p1pct=6 unit=count seed=0
RESULT change.fraud_dollars_0p1pct=2314.2 unit=dollars seed=0
RESULT change.explored_1pct=98 unit=count seed=0
RESULT change.explored_frauds_1pct=30 unit=count seed=0
RESULT change.fraud_dollars_1pct=9087.82 unit=dollars seed=0
RESULT change.explored_5pct=466 unit=count seed=0
RESULT change.explored_frauds_5pct=151 unit=count seed=0
RESULT change.fraud_dollars_5pct=48261.5 unit=dollars seed=0
```

| RESULT | seed 0 | seed 1 | seed 2 | spread (tolerance) |
|---|---|---|---|---|
| `P2.ci_width` | 12.2816 | 11.4789 | 11.0598 | 1.2218 |
| `change.ipw_recall_1pct` | 0.382581 | 0.330589 | 0.32669 | 0.055891 |
| `change.draws_mean_1pct` | 0.349895 | 0.34139 | 0.34109 | 0.008805 |
| `change.draws_width_1pct` | 12.4093 | 10.9977 | 13.1712 | 2.1735 |
| `change.explored_1pct` | 98 | 85 | 87 | 13 |
| `change.explored_frauds_1pct` | 30 | 26 | 23 | 7 |
| `change.fraud_dollars_1pct` | 9087.82 | 7265.69 | 7034.52 | 2053.3 |
| `change.ci_width_0p1pct` | 33.9579 | 24.5896 | 30.8785 | 9.3683 |
| `change.explored_frauds_0p1pct` | 6 | 1 | 3 | 5 |
| `change.ci_width_5pct` | 5.10079 | 4.70586 | 5.40543 | 0.69957 |
| `change.explored_frauds_5pct` | 151 | 100 | 124 | 51 |
| `change.fraud_dollars_5pct` | 48261.5 | 30641.2 | 35969.4 | 17620.3 |

**Why.** The width is set by the explored frauds, not by the era B row count: at seed 0 the slice approved 98 would-be declines, 30 of them fraud, and each stands for 100 payments like it, so a handful of rows swings the estimate. The bootstrap from this one log agrees with the spread over 200 fresh 1% slices (12.4093 points), and their mean (0.349895) sits on the true recall while this log reads 0.382581: on target on average, noisy in any one log. Strictly, the estimate is a ratio of two weighted sums. Each sum is unbiased for its true total, but the ratio is only consistent: it carries a small finite-sample bias that shrinks as the explored frauds grow. The 200 fresh slices show that bias sits inside their noise here: an empirical check, not a guarantee. The slice is bought in fraud dollars: 1% let $9087.82 of fraud through over 92 days, 5% let $48261.5 through for a 5.10079-point interval, and 0.1% explored only 6 frauds for a 33.9579-point interval, a width that itself moves by 9.3683 points across seeds, so its size is uncertain (Build notes).

**Common wrong prediction:** under 2 points, reasoning from the hundreds of thousands of era B rows. Only the explored frauds carry information about the champion's declines.

</details>

<details><summary>P3. Retrain the challenger on era B with declined rows dropped (shortcut a) vs trained with the weighted slice: true recall on days 151 to 182, direction and size</summary>

**Answer:** shortcut a is lower, by 0.803366 points at seed 0 (`P3.gap_points` = -0.803366; shortcut a 0.216718, weighted 0.224751), tolerance 1.09028 points. The sign is the same in every seed (-1.89365 at seed 1, -1.3772 at seed 2), but the size sits inside the retraining noise: the shortcut-a model's own recall has a seed spread of 0.021423. Treat this as a small effect (Build notes).

Seed 0 RESULT lines:

```
RESULT P3.recall_drop=0.216718 unit=fraction seed=0
RESULT P3.recall_weighted=0.224751 unit=fraction seed=0
RESULT P3.gap_points=-0.803366 unit=points seed=0
RESULT break.recall_as_fraud=0.211362 unit=fraction seed=0
RESULT break.recall_oracle=0.251913 unit=fraction seed=0
RESULT break.explored_train=61 unit=count seed=0
RESULT break.explored_train_frauds=18 unit=count seed=0
RESULT break.blind_frauds=974 unit=count seed=0
RESULT break.blind_recall_drop=0.710472 unit=fraction seed=0
RESULT break.blind_recall_as_fraud=0.962012 unit=fraction seed=0
RESULT break.blind_recall_weighted=0.740246 unit=fraction seed=0
RESULT break.blind_recall_oracle=0.918891 unit=fraction seed=0
```

| RESULT | seed 0 | seed 1 | seed 2 | spread (tolerance) |
|---|---|---|---|---|
| `P3.recall_drop` | 0.216718 | 0.195295 | 0.209832 | 0.021423 |
| `P3.recall_weighted` | 0.224751 | 0.214231 | 0.223604 | 0.01052 |
| `P3.gap_points` | -0.803366 | -1.89365 | -1.3772 | 1.09028 |
| `break.recall_as_fraud` | 0.211362 | 0.212318 | 0.214614 | 0.003252 |
| `break.recall_oracle` | 0.251913 | 0.249044 | 0.257651 | 0.008607 |
| `break.blind_recall_drop` | 0.710472 | 0.581633 | 0.676768 | 0.128839 |
| `break.blind_recall_as_fraud` | 0.962012 | 0.966327 | 0.962626 | 0.004315 |
| `break.blind_recall_weighted` | 0.740246 | 0.70102 | 0.736364 | 0.039226 |
| `break.blind_recall_oracle` | 0.918891 | 0.923469 | 0.912121 | 0.011348 |

**Why.** Dropping the declined rows deletes the champion's region from training, so the new model's behavior there is whatever its trees extrapolate: it keeps 0.710472 of the 974 test-window frauds the champion declines at seed 0 (from 0.581633 to 0.710472 across seeds), against 0.918891 for the oracle. The 1% slice adds only 61 rows, 18 of them fraud, in 60 training days: too few to rebuild that region (0.740246). Overall recall hides most of the damage, because every model still spends its full 1% budget on other frauds, and the card-testing attack that starts on day 160, inside the test window, is new to all four. Shortcut b keeps 0.962012 of the champion's catches by copying its opinion, yet its overall recall (0.211362) is the lowest of the four at seed 0: it relearns the champion, blind spot included.

**Common wrong prediction:** a drop of 5 points or more in overall recall. The damage concentrates where the champion declines (the blind recall rows), and the overall number moves by about the retraining noise. A slice sized for evaluation is not big enough to retrain on.

</details>

<details><summary>Rebuild check</summary>

- Stub: `m4-production-ml-payments/rebuild/23_ipw_recall.py`. Solution: `answers/rebuild/23_ipw_recall.py`.
- `rebuildcheck`: the stub fails as it should (NotImplementedError), the solution passes (`check: PASS`), `REBUILDCHECK OK`.
- `check()` uses a fully labelled toy (200,000 rows, a toy champion declining 10%) with its own random stream for the reveals, so a correct body passes whatever its bootstrap draws. It compares the point estimate with `numpy.average` and with scikit-learn's `recall_score` under the same weights, checks that the 95% interval holds the estimate, and checks that the mean over 200 random 1% reveals sits within 2 standard errors of the toy's true recall. An unweighted version fails both the `numpy.average` match and that last check. The toy challenger catches frauds at one rate inside and outside the toy champion's declines, so the learner-visible stub says nothing about P1's direction.

</details>

<details><summary>Card drafts</summary>

| ID | Lab | Type | Question |
|---|---|---|---|
| 23-M | 23 | M | A challenger is scored only on the payments the champion approved. Why does its recall read lower than its true recall, and what must the decision log record to fix the estimate? |
| 23-N | 23 | N | In lab 23, a 1% exploration slice of the champion's would-be declines was reweighted by 100. About how wide was the 95% interval of the IPW recall, and what sets that width? |
| 23-D | 23 | D | You retrain the fraud model on last quarter's labelled payments. Offline recall on held-out labels holds, but after launch the frauds the old model used to stop start getting through. What do you check first? |

If the last close used D, swap 23-D for this transfer card:

| ID | Lab | Type | Question |
|---|---|---|---|
| 23-T | 23 | T | Your exploration slice sends would-be declines to a 3DS step-up instead of approving them. What does an IPW estimate from those rows measure, and what goes wrong at the next threshold review? |

Keys (1 to 3 must-mention items each):

- **23-M:** (1) the champion's declines hold the frauds both models find easiest, so they leave the numerator and the denominator together (here 0.250668 of era B frauds and 0.684658 of the challenger's catches); (2) a random exploration slice of would-be declines, approved, with each row's propensity logged; (3) weight each labelled row by 1 / propensity.
- **23-N:** (1) about 12 points (12.2816 at seed 0; 200 fresh slices gave 12.4093); (2) the explored frauds set it (30 at seed 0, each weighted 100), not the era B row count; (3) a 5% slice narrowed it to 5.10079 points for about 5 times the fraud dollars.
- **23-D:** (1) whether the training set dropped the champion's declines (or labelled them all fraud), which leaves the champion's region unlearned; (2) measure recall on the champion's would-be declines with the weighted exploration slice, not on approved-only labels.
- **23-T:** (1) a step-up changes the outcome: fraudsters abandon and liability shifts to the issuer, so chargebacks collapse; (2) the estimate measures fraud under step-up, not fraud if approved; (3) the decline band looks safer than it is, so the threshold loosens (repo model-lifecycle §3).

</details>

<details><summary>Build notes</summary>

**Knob changes:** none. The spec's configuration stands: champion LightGBM 150 trees on 5 inputs, challenger 300 trees on 10, both trained on era A; each model declines at or above its own day's 99th percentile; a 1% slice (propensity 0.01) for P2 and for P3's weighted training set; 200 bootstrap resamples.

**The 2x spread rule** (effects from the .json; spread is the larger of the two names' spreads):

| Effect (A minus B, mean over seeds) | Effect | Spread | Over 2x spread | Taught as |
|---|---|---|---|---|
| `P1.recall_approved_only:P1.recall_true` | -0.199115 | 0.007159 | yes | real: the approved-only bias |
| `change.ipw_recall_1pct:P1.recall_approved_only` | 0.201488 | 0.055891 | yes | real: IPW removes the bias |
| `change.ipw_recall_1pct:P1.recall_true` | 0.002373 | 0.055891 | no | null: one log is noisy, with no shift beyond that noise |
| `change.draws_mean_1pct:P1.recall_true` | -0.000122 | 0.008805 | no | null: the mean of 200 logs lands on the truth within its noise |
| `P2.ci_width:change.ci_width_5pct` | 6.53607 | 1.2218 | yes | real: a bigger slice narrows the interval |
| `change.ci_width_0p1pct:P2.ci_width` | 18.2019 | 9.3683 | no | uncertain size, reported with its spread: wider than 1% in every seed, but the 0.1% width is itself erratic |
| `P3.recall_weighted:P3.recall_drop` | 0.0135803 | 0.021423 | no | small: inside the retraining noise |
| `break.blind_recall_weighted:break.blind_recall_drop` | 0.0695857 | 0.128839 | no | small, noisy: the drop model's blind spot |
| `break.recall_oracle:P3.recall_drop` | 0.0455877 | 0.021423 | yes | real: the price of the blind spot |

- The two null rows are null by design. The IPW recall's numerator and denominator are each unbiased for their true totals (each labelled row weighted by 1 / propensity, a Horvitz-Thompson sum). Their ratio is consistent, not exactly unbiased: its finite-sample bias shrinks as the explored frauds grow. So a single log lands within its noise of the truth, and the mean of 200 logs lands on the truth within its own noise. That agreement is an empirical check on these runs, not a guarantee of zero bias.
- `change.ci_width_0p1pct:P2.ci_width` misses the rule, so the lab does not teach its size as a real effect. It reports the 0.1% width with its spread (24.5896 to 33.9579 points across seeds, spread 9.3683) and teaches only what holds in every seed: the 0.1% interval is wider than the 1% interval, and too erratic to size a slice by. The slice-size lesson rests on the 1% against 5% row, which clears the rule. The 0.1% slice explored 1 to 6 frauds across seeds, so its bootstrap width is itself erratic (it is narrowest at the seed that explored a single fraud, because a bootstrap of one log only reshuffles the frauds that log happened to explore). No knob fixes this without changing the slice the spec names, and the instability is part of the lesson.
- P3 (`P3.recall_weighted:P3.recall_drop`) is below 2x the spread, and so is its blind-recall version. The binding term is the shortcut-a model's own seed spread: with no training rows in the champion's region, its behavior there depends on LightGBM's seeded bin sampling. The paired gap has the same sign in all three seeds. A tagged sweep (`break-s0-sweep`, `break-s1-sweep`, `break-s2-sweep` in the ledger, the same code plus extra weighted models) tried 2%, 5%, 10% and 20% training slices. Each beat the 1% slice in every seed, but none cleared the rule against shortcut a, because even the oracle only just does (`break.recall_oracle:P3.recall_drop` above). The sweep printed diagnostic lines, not RESULT lines, so its values are not in the .json and are not quoted here. So the spec's 1% slice stays, and the answer teaches P3 as a small effect with its spread. Fixing LightGBM's binning would shrink the spread to zero but hide real retraining noise and make the tolerance zero, so it was not done.

**Choices where the spec is silent (simplest correct option):**

1. `terminal_frauds_30d` counts only labelled frauds: every era A payment plus the champion's era B approvals. A declined payment never becomes a dispute, so a label-derived input must not see it either. The exploration slice's labels are left out of this input, so every slice scores the same challenger.
2. The terminal window is on the fraud's event time (the frauds of the 30 days before t whose label arrived before t), the key formula in the module README's Point-in-time features section and lab 21's choice.
3. The interval bootstraps all era B rows, as the README formula says. `--change` adds 200 fresh 1% slices from the same generator to show the estimator's spread and its mean next to the one-log bootstrap.
4. Extra RESULT lines beyond the spec's Record: the fresh-draw mean and width, explored frauds per slice, and blind recall (recall over the test-window frauds the champion declines) per training set, because P3's mechanism lives there.
5. `--smoke` keeps customers 0 to 499 of the full stream (so the eras and the test window stay whole) and caps every model at 20 trees. A 300-tree smoke ran over the brief's 60 s smoke limit while other build jobs shared the CPU; the 20-tree smoke finishes in seconds.
6. Approved labels are treated as matured (the spec's assumption), so `is_fraud` is the label of every approved payment.
7. Length: the reference is 189 lines, over the brief's 150-line guide. Its first 95 lines carry the code the starter also ships (docstring, imports, inputs, contract, `report()`, `ipw_recall()`); the harness adds the champion, four era B training sets, three slices and the fresh draws. The learner-visible starter stays at 108 lines.
8. Reruns repeat: the tagged sweep and the plain `--break` runs, and the tagged prototype-gap run and the plain `--baseline`, agree to every digit the experiments printed, so the seed spread is model and slice noise, not run-to-run jitter.

**Prototype comparison** (spec values in brackets):

- Champion decline rate 0.0100539 [1.006%], holding 2626 of 10476 era B frauds [2,575 of 10,512]. The stream has the prototype's 1,795,646 rows, but its era B fraud count differs slightly, so the fraud draws are not identical.
- P1 gap -20.1791 points [0.079 minus 0.289, so -21.0]: within 2x the spread. The levels differ by more than that: true recall 0.348415 [0.289] and approved-only 0.146624 [0.079]. Cause, from a tagged run (`baseline-s0-protogap`, seed 0, the baseline under four versions of `terminal_frauds_30d`): the terminal input's window. That run printed diagnostic lines, not RESULT lines, so its values are not in the .json and are not quoted here. Both recalls fell at each step from this lab's input (event-time window, labelled frauds only), to the same window with the declined frauds' labels counted too, to an arrival-time window (the labels that landed in the last 30 days), to no terminal input. Almost all of that fall sat in scenario 2, the compromised terminals. The arrival-time window landed close to the prototype's levels, closer than any other version, so the prototype most likely used it. The lab keeps the event-time window for consistency with the module README and lab 21. The predicted quantity, the gap, moved far less than the levels: -20.1791 here and -21.0 in the prototype.
- P2 width 12.2816 points [0.124, so 12.4]; at 0.1% 33.9579 [39.7]; at 5% 5.10079 [5.7]; 98 rows explored at 1% [about 90]. All within 2x the spread. The fresh-draw mean 0.349895 sits on the true recall, as the prototype's IPW mean did.
- Time: the prototype took 13 s; here seed-0 runs took 41.1 to 97.5 s with other build jobs on the CPU. The learner's idle machine will be faster.
- P3 has no prototype values.
- The earlier partial build of this lab (tagged `try` and `diag` runs in the ledger) counted the declined frauds' labels in the terminal input; those runs are superseded.

</details>
