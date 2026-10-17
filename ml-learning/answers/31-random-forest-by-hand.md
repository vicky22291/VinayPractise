# 31. Random forest by hand: one deep tree vs many averaged trees: reference answers

> Spoilers. The AI opens one block at a time, only after that step's prediction row exists and the learner pasted their own RESULT lines, or after 'debrief 31'.

- **HW:** `HW chip='Apple M4 Pro' cpu=14 gpu=20 mem_gib=24 macos=26.5.1 python=3.13.7 torch=2.14.1 device=cpu`
- **Seeds:** 0, 1 and 2 for every step (light lane). The seed changes the 80/20 split, the 10,000-row training sample, every bootstrap draw and every feature sample.
- **Reference script:** `answers/31_random_forest_by_hand_ref.py` (sha256 prefix `76afed937f1404fe`). The learner's starter is `m5-under-the-hood/scripts/31_random_forest_by_hand.py`.
- **Runs and wall times** (light lane; other labs shared the CPU slots):

  | Mode | Seed 0 | Seed 1 | Seed 2 |
  |---|---|---|---|
  | baseline | 27.2 s | 47.0 s | 41.5 s |
  | change | 14.7 s | 9.5 s | 8.7 s |
  | break | 1.8 s | 5.3 s | 3.3 s |

- **Tolerance rule:** tol = spread (max - min) over seeds 0, 1, 2. A Hit uses only the learner's own range and RESULT line. A learner value more than 2x tol from the seed-0 reference points at a harness difference worth checking, not at noise.
- Raw seed-0 output: `answers/31-random-forest-by-hand.out`. Values, spreads and effects: `answers/31-random-forest-by-hand.json`.

<details><summary>P1. Validation accuracy of your bagged forest with 100 trees (all 14 features considered at every split)</summary>

**Answer:** 0.857201 at seed 0, tolerance 0.004401 (the seed spread). Seed 1: 0.856382. Seed 2: 0.8528.

```
RESULT P1.valid_acc=0.857201 unit=fraction trees=100 seed=0
RESULT baseline.valid_acc_1_tree=0.823319 unit=fraction seed=0
RESULT baseline.valid_acc_10_trees=0.850343 unit=fraction seed=0
RESULT baseline.valid_error=0.142799 unit=fraction seed=0
RESULT baseline.oob_error=0.1455 unit=fraction seed=0
```

Other seeds: `baseline.valid_acc_1_tree` 0.818303 and 0.822909; `baseline.valid_acc_10_trees` 0.851264 and 0.851059; `baseline.oob_error` 0.1467 and 0.1454; `baseline.valid_error` 0.143618 and 0.1472.

**Why.** Each bootstrap tree is deep (no depth limit, min_samples_leaf 5), so its small leaves fit noise, and the bootstrap makes that noise different from tree to tree. Averaging the leaf shares cancels much of it: at seed 0 the forest goes from 0.823319 with 1 tree to 0.850343 with 10 and 0.857201 with 100. The part that averages away shrinks roughly like 1 over the number of trees, so most of the gain has arrived by tree 10; what is left is bias plus the error every tree shares, and that is where more trees stop helping. The out-of-bag error (0.1455) sits next to the validation error (0.142799) because each training row is graded only by the roughly 37 trees in 100 whose bootstrap never drew it: a free validation score.

**Common wrong prediction:** 0.90 or more, because "random forests are strong". Income depends on much that 14 census columns do not record, so many rows that look alike earn on both sides of 50K. Always answering "50K or less" already scores about 0.76 on this split, so the forest's lift over that is about 10 points.

</details>

<details><summary>P2. Consider 4 random features per split (sqrt of 14): accuracy at 100 trees and out-of-bag error, direction and size</summary>

**Answer:** accuracy up by a few tenths of a point at every seed. This is the graded half: Hit and Off by use `P2.valid_acc_change` only (the lab's P2 row says so). Out-of-bag error went down at every seed too, but the 2x rule does not establish that change, so it is reported, not graded: a "same" call is as defensible as "down".

- Validation accuracy: `P2.valid_acc` 0.860068 at seed 0 (seed 1: 0.85976, seed 2: 0.856894). Against the baseline at the same seed, `P2.valid_acc_change` is 0.286621 points at seed 0 (seed 1: 0.337803, seed 2: 0.409458). Tolerance for the size: 0.122837 points, the spread of that paired change. Each of the three values is above 2x that spread, so this change passes the 2x rule.
- Out-of-bag error: `P2.oob_error` 0.1382 at seed 0 (seed 1: 0.1432, seed 2: 0.1441). `P2.oob_error_change` is -0.73 points at seed 0 (seed 1: -0.35, seed 2: -0.13). Its spread, 0.6 points, is larger than the average change itself, so it is far from 2x.

```
RESULT P2.valid_acc=0.860068 unit=fraction trees=100 seed=0
RESULT change.valid_acc_1_tree=0.819634 unit=fraction seed=0
RESULT change.valid_acc_10_trees=0.85628 unit=fraction seed=0
RESULT change.valid_error=0.139932 unit=fraction seed=0
RESULT P2.oob_error=0.1382 unit=fraction seed=0
RESULT P2.valid_acc_change=0.286621 unit=points seed=0
RESULT P2.oob_error_change=-0.73 unit=points seed=0
```

Other seeds: `change.valid_acc_1_tree` 0.815846 and 0.825878; `change.valid_acc_10_trees` 0.857918 and 0.855973; `change.valid_error` 0.14024 and 0.143106.

**A small effect, reported with its spread.** Averaged over the seeds, the accuracy level moves by 0.003446, below 2x the level spread of 0.004401; the out-of-bag level moves by -0.004033, below 2x its spread of 0.0059. The accuracy level spread is mostly which 9,769 rows each seed holds out. The out-of-bag level is scored on each seed's own 10,000 training rows instead, so its spread comes from which rows each seed draws and from every bootstrap draw. Paired at the same seed, on the same split and the same training rows, the accuracy change clears 2x its own spread: real here, but smaller than the noise between splits, so only a paired comparison shows it. The paired out-of-bag change kept its sign at all three seeds, and in the scikit-learn proxy (Build notes), but its size does not clear 2x its spread. A learner's harness draws its random numbers in a different order, so its paired changes will not match these to the digit. The scikit-learn proxy, which also draws differently, shows how far they can move (Prototype comparison, Build notes).

**Why.** With all 14 features, every bootstrap tree makes the same greedy choices: the same root split, and many deep cuts on `fnlwgt`, a census sampling weight with thousands of distinct values and almost no signal. With 4 random features per split, `fnlwgt` is in the draw at fewer nodes, so each tree spends less of its depth fitting noise, and the average tree scores better on its own (mechanism checks, Build notes). The forest gains only a few tenths of a point because most of that noise differs from tree to tree, and averaging 100 trees already cancels that part in the 14-feature forest: in Brier score, the single trees improve several times as much as the forest does (Brier check, Build notes). One tree is too noisy to rank the two plans: the gap between the two 1-tree lines changes sign across seeds.

**Common wrong prediction:** a jump of a point or more, from the textbook line that random forests beat bagging; or a drop, because each split sees fewer features. Both stories sound right. On this table the accuracy sign is steady and the size is smaller than the spread between splits.

</details>

<details><summary>P3. One tree with unlimited depth and min_samples_leaf 1: train accuracy minus validation accuracy, in points</summary>

**Answer:** 19.1936 points at seed 0, tolerance 0.2866 points (the seed spread). Seed 1: 19.2036. Seed 2: 19.4802.

```
RESULT P3.train_minus_valid=19.1936 unit=points seed=0
RESULT break.train_acc=0.9999 unit=fraction seed=0
RESULT break.valid_acc=0.807964 unit=fraction seed=0
RESULT break.leaves=1501 seed=0
RESULT break.depth=37 seed=0
```

Other seeds: `break.train_acc` 1 and 0.9999; `break.valid_acc` 0.807964 and 0.805098; `break.leaves` 1485 and 1447; `break.depth` 30 and 31.

**Why.** With min_samples_leaf 1 and no depth limit, the tree keeps splitting until each leaf is pure or its rows match on every feature, so it memorizes its training rows: 1501 leaves for 10,000 rows at depth 37, and a train accuracy of 0.9999. The one training miss sits in a leaf whose rows share every feature but not the label, which no split can separate. On validation it scores 0.807964, below one bagged tree with min_samples_leaf 5 (`baseline.valid_acc_1_tree` 0.823319) and well below the 100-tree forest (`P1.valid_acc` 0.857201): its leaves fit noise that does not repeat on new rows. The forest cuts that noise two ways: its trees keep at least 5 rows per leaf, and averaging 100 of them cancels the part that differs from tree to tree.

**Common wrong prediction:** 2 to 5 points, the gap people see with tuned or regularized models. An unlimited tree scores about 100% on its own rows, so the gap is the whole distance from 100% down to one tree's validation accuracy.

</details>

<details><summary>Rebuild check</summary>

Solution: `answers/rebuild/31_best_split.py`. Stub: `m5-under-the-hood/rebuild/31_best_split.py`.

`rebuildcheck` verdict: stub fails as it should (exit 1, `NotImplementedError`); solution passes (exit 0, `check: PASS`); `REBUILDCHECK OK`.

`check()` compares the threshold and the weighted Gini with scikit-learn's `DecisionTreeClassifier(max_depth=1)` on 40 random features (integer features with many repeated values, and continuous ones rounded to float32 because scikit-learn casts X to float32), with min_samples_leaf 1 and 5, to 1e-6.

</details>

<details><summary>Card drafts</summary>

| ID | Lab | Type | Question |
|---|---|---|---|
| 31-M | 31 | M | Why does going from 10 to 100 bootstrap trees add much less validation accuracy than going from 1 to 10, and what sets the level where adding trees stops helping? |
| 31-N | 31 | N | On Adult with 10,000 training rows, one tree grown with no depth limit and min_samples_leaf 1: about how many points is its train accuracy above its validation accuracy, and why is the gap that big? |
| 31-D | 31 | D | Your hand-written forest reports an out-of-bag error several points below its validation error on a random split. What do you check first? |

Keys:

- **31-M:** (1) the part of the error that averaging removes shrinks like 1 over the tree count, so most of the gain comes early (0.823319 at 1 tree, 0.850343 at 10, 0.857201 at 100, seed 0); (2) what is left is bias plus the error all the trees share, which no number of trees averages away, so that sets the level.
- **31-N:** (1) about 19 points (19.1936 at seed 0: train 0.9999, validation 0.807964); (2) it splits until every leaf is pure (1501 leaves for 10,000 rows), so it memorizes noise that does not repeat on new rows.
- **31-D:** (1) the out-of-bag mask: a row's vote must come only from trees whose bootstrap never drew it, because trees that trained on a row score it far better than they score a new row, so a mask that lets in-bag trees vote pulls the out-of-bag error toward the training error; (2) then compare the gap with the seed spread: in this lab the two errors sat within half a point (0.1455 out-of-bag vs 0.142799 validation at seed 0).

</details>

<details><summary>Build notes</summary>

**Knob changes: none.** The P2 effects on the accuracy and out-of-bag levels are below 2x their seed spread (effects `P2.valid_acc:P1.valid_acc` and `P2.oob_error:baseline.oob_error`, both `ok: false` in the .json). The accuracy level spread is split noise: each seed holds out a different 9,769 rows, and the standard error of an accuracy near 0.86 on 9,769 rows is about 0.0035, so three splits spread over a few tenths of a point by themselves. The out-of-bag level is scored on each seed's own 10,000 training rows, so its spread is training-sample and bootstrap noise. No knob shrinks either spread without breaking the rule that the seed changes the split. A build-only scikit-learn proxy on the same rows tried the nearby knobs (all 39,073 training rows, min_samples_leaf 1, 2 features per split): in none did the accuracy or the out-of-bag level effect exceed 2x its level spread. So the knob stays at the spec's 4 features, and P2 is taught as a small effect, graded on the paired same-seed accuracy change `P2.valid_acc_change`: each of its three values is above 2x its spread of 0.122837 points. The paired out-of-bag change `P2.oob_error_change` has a spread (0.6 points) larger than its average size, so it is reported with its spread and not graded. In the proxy at the lab's own knobs neither paired change cleared 2x its spread, but the paired accuracy change stayed positive at all three seeds in every one of the eight knob settings tried. The effects the lab teaches as large all pass: `break.train_acc:break.valid_acc` (the P3 gap), `P1.valid_acc:break.valid_acc` (forest vs one deep tree) and `P1.valid_acc:baseline.valid_acc_1_tree` (100 trees vs 1).

**Precomputed steps: none.** Seed-0 runs took 27.2 s (baseline), 14.7 s (change) and 1.8 s (break), far under the 6-minute cap, and 100 trees fit the spec's 2-minute budget with the 10,000-row cap.

**Choices where the spec is silent, and deviations:**

- Features per split: 4, as the spec says. scikit-learn's `max_features="sqrt"` would floor the square root of 14 to 3.
- Download: OpenML 1590 first (lab 03's source), then the spec's ADULT_SAMPLE fallback. Lab 03's parquet and UCI zip fallbacks are left out to keep the script within 150 lines. The fallback CSV names the target `salary` (`>=50k` and `<50k`) and has missing values in `education-num` and `occupation`; `load_data()` maps them to -1. Tested at build time on the downloaded archive: 10,000 training and 6,513 validation rows, no missing values left.
- Gini formula: the spec has the learner write `best_split()` "from the README formula". The lab file gives the formula in section 3 instead, because level S needs it during the session and the module README's concept section is after-lab reading.
- Voting: the soft vote, the average of the trees' leaf shares cut at 0.5 (an average of exactly 0.5 votes 0, the majority class), as scikit-learn does. The lab file states the rule as "an average above 0.5 votes 1", so a learner's harness breaks ties the same way. Hard majority voting is the other common choice.
- Bootstrap: an index array drawn with replacement, so min_samples_leaf counts repeated rows. scikit-learn counts distinct rows and weights the repeats.
- Feature sampling: a node whose sampled features offer no allowed cut becomes a leaf, as in Breiman's original code, and the lab file's recursion says so. scikit-learn 1.9.1 draws past `max_features` only while every feature drawn so far is constant in the node. A feature whose cuts are all blocked by min_samples_leaf still counts toward `max_features`, and that node becomes a leaf there too. So the two differ only at nodes where every sampled feature is constant.
- Break: one tree on all 10,000 training rows, with no bootstrap and all 14 features. The spec names only the depth limit and min_samples_leaf 1. Without a bootstrap, `break.train_acc` is scored on exactly the rows the tree was grown on; a bootstrap tree would leave about a third of them out.
- Start-up check: the lab asks the AI's harness to check the learner's `best_split()` against `DecisionTreeClassifier(max_depth=1)` on two training columns before it grows anything, so a subtle split bug stops the run instead of being graded. The reference skips it: its `best_split()` is the same function as the rebuild solution, which passes `rebuildcheck`. A build-only run of that comparison on the reference's `best_split()` matched on all 14 training columns, with min_leaf 1 and 5, at seeds 0, 1 and 2, on the full and the smoke rows, so a correct function passes it.
- Random numbers: one numpy Generator per run, seeded by `--seed`, draws the 10,000-row training sample first (so all three modes see the same rows at a seed), then the bootstrap rows and feature samples. The split uses `random_state` = seed.
- Rebuild: `best_split(x, y, min_leaf=1)` keeps the spec's `best_split(x, y)` call and adds the optional leaf limit, so the rebuild is the same function the forest uses; `check()` also tests min_samples_leaf 5.
- Repo link: the spec lists none. The lab links `hld/payments-risk-decisioning/solution.md` §10.1. Its GBDT inference bullet answers the Staff follow-up (migration): the isotonic calibration table and the segment thresholds are fit to the GBDT's scores, so they must be refit on the forest's averaged leaf shares, and `UNAVAILABLE` values follow a learned default branch that a forest coding missing values as -1 does not have, so each missing pattern needs the validated lookup again. Lab 28 asks failure modes, lab 29 the trade-off, lab 30 simplest design and lab 32 what pages at 3 am, so migration repeats no other lab in the module.
- Smoke: all three modes on 2,000 training and 2,000 validation rows, with each plan's tree count capped at 10. The lab file asks the AI's harness for the same smoke, so `--smoke` runs the learner's own `best_split()` before the 100-tree run.
- `break.valid_acc` is the same at seeds 0 and 1 (0.807964): two different splits and two different trees (1501 and 1485 leaves) that both get 7,893 of 9,769 rows right. A coincidence, not a seeding bug.
- Title: the spec first titled this lab "Random forest by hand: a deep tree has high variance, and averaging lowers it". That states the P3 direction before the learner predicts it. So the lab file, its module README row, this file and the spec's title fields use the neutral "Random forest by hand: one deep tree vs many averaged trees". The old title is the lab's takeaway, for after P3.

**Prototype comparison.** The spec carries no `[answers only]` prototype values for this lab. In their place, a build-only scikit-learn run on exactly the same rows (`RandomForestClassifier` with 100 trees, min_samples_leaf 5, bootstrap, `max_features` None or 4; `DecisionTreeClassifier` with min_samples_leaf 1; seeds 0, 1, 2) gave: bagging 0.8563, 0.8554 and 0.8525; 4 features 0.8588, 0.8597 and 0.8584 (paired change +0.26, +0.43 and +0.59 points; out-of-bag change -0.03, -0.60 and -0.29 points); deep tree gap 19.24, 19.52 and 19.40 points, with 1497, 1486 and 1446 leaves at depths 37, 30 and 31. The direction matches everywhere, and every gap to the by-hand values is under 2x that value's seed spread, so no bug is indicated. (Re-run on the final reference script: the same numbers.)

**Mechanism checks behind the P2 answer** (build-only, re-run on the final reference script; earlier logs of these checks predate it). Roots, 30 bootstrap trees per plan at seed 0: with 14 features, all 30 split first on `relationship`; with 4, the root varied over seven features. Depth bands, 20 trees per plan at seed 0: `fnlwgt` took 35% of the splits below the top three levels with 14 features and 22% with 4. Brier decomposition (the Brier score is the mean squared error of a predicted share against the 0/1 label), 100 trees per plan at seeds 0 and 1: the forest's Brier score equals the mean single-tree Brier score minus the spread term, the trees' variance around the forest's prediction averaged over rows (the printed values add up). With 4 features the single trees are better (Brier 0.1357 against 0.1486 at seed 0 and 0.1359 against 0.1473 at seed 1; mean single-tree accuracy 0.8225 against 0.8183 at seed 0), and the spread term is smaller, not larger (0.0383 against 0.0486, and 0.0392 against 0.0483). The forest's Brier still improves (0.0975 against 0.1000 at seed 0). So the 4-feature gain is per-tree: better single trees, while the part that averaging removes shrank. The mean pairwise correlation of the trees' residuals rose (0.716 against 0.670 at seed 0), but residuals y - p share the label noise, so that measure rises whenever the trees get individually better. It cannot separate decorrelation from tree strength. The spec's concept line says feature sampling decorrelates the trees; these runs do not show that on this table, which is why the P2 answer leads with the greedy choices.

</details>
