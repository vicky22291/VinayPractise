# 03. Tabular in ten minutes: majority baseline, logistic regression and LightGBM: reference answers

> Spoilers. The AI opens one block at a time, only after that step's prediction row exists and the learner pasted their own RESULT lines, or after 'debrief 03'.

- **HW:** `HW chip='Apple M4 Pro' cpu=14 gpu=20 mem_gib=24 macos=26.5.1 python=3.13.7 torch=2.14.1 device=cpu`
- **Seeds:** 0, 1 and 2 for `--baseline`, `--change` and `--break` (light lane, 9 runs); seed 0 only for the optional `--tabpfn`.
- **Reference script:** `ml-learning/m1-whole-game/scripts/03_tabular_in_ten_minutes.py`. Level W, so the learner's script is the reference. script_sha256 `d590573e72951060`.
- **Tolerance rule:** tol = spread (max - min) over seeds 0, 1, 2; heavy labs: the baseline spread applies to every step. Spreads below are rounded to 6 significant digits. All values: [`03-tabular-in-ten-minutes.json`](03-tabular-in-ten-minutes.json). Raw seed-0 output: [`03-tabular-in-ten-minutes.out`](03-tabular-in-ten-minutes.out).
- **Runs and wall times** (seconds, on a build queue shared with other labs):

| Mode | Seed 0 | Seed 1 | Seed 2 |
|---|---|---|---|
| baseline | 7.6 | 5.3 | 6.8 |
| change | 5.6 | 7.1 | 5.8 |
| break | 7.1 | 5.4 | 7.2 |
| tabpfn (optional) | 296.4 | | |

<details><summary>P1. Test AUC (area under the receiver operating characteristic curve) of LightGBM (defaults, 100 trees) on 39,073 training rows, and the gap in AUC points, LightGBM minus logistic regression</summary>

**Answer:** AUC **0.92843** at seed 0, tolerance plus or minus 0.003259. The gap is **2.23919** AUC points with LightGBM ahead, tolerance plus or minus 0.10412 points. A hit needs both numbers inside your 80% ranges; Off by uses the AUC.

Seed-0 RESULT lines:

```
RESULT baseline.acc_majority=0.760672 unit=fraction seed=0
RESULT baseline.auc_majority=0.5 unit=fraction seed=0
RESULT baseline.acc_logreg=0.853619 unit=fraction seed=0
RESULT baseline.auc_logreg=0.906038 unit=fraction seed=0
RESULT baseline.acc_lgbm=0.871942 unit=fraction seed=0
RESULT P1.auc_lgbm=0.92843 unit=fraction seed=0
RESULT P1.gap_vs_logreg_points=2.23919 unit=auc_points seed=0
```

Other seeds: `P1.auc_lgbm` 0.930639 (seed 1) and 0.931689 (seed 2). `P1.gap_vs_logreg_points` 2.3424 and 2.23828. `baseline.auc_logreg` 0.906038, 0.907215 and 0.909306.

Why: boosted trees split on thresholds and on groups of categories, and each of the 100 trees corrects the ones before it, so they capture interactions and bends (such as `capital-gain`, zero for most rows and very large for a few) that a linear model cannot draw without hand-made crosses. Logistic regression on scaled and one-hot columns is already strong here, because much of Adult's signal is close to additive in the log-odds. So the trees buy a couple of points, not ten. Over the three seeds the gap averages 0.022733 AUC, that is 2.2733 AUC points, against a seed spread of 0.003268 AUC (0.3268 points), so it passes the 2x rule and is real.

The majority row: accuracy 0.760672 is just the share of `<=50K` rows in the test split (the same at every seed, because the split is stratified), while AUC 0.5 means it ranks nothing, since every row gets the same score. The two metrics disagree completely about this model.

Common wrong prediction: a gap of 5 to 10 points ("trees crush linear models"), or an AUC close to LightGBM's accuracy (0.871942), as if the two metrics measured the same thing.
</details>

<details><summary>P2. LightGBM trained on 5,000 rows instead of 39,073: AUC direction and size</summary>

**Answer:** down, by a little. Seed 0: AUC **0.912911**, so `P2.delta_points` is **-1.55195** AUC points against P1's 0.92843. Tolerance: plus or minus 0.005063 on the AUC, plus or minus 0.28545 points on the delta. A hit needs "down" and the size of the delta inside your size range.

Seed-0 RESULT lines:

```
RESULT P2.auc_5000_rows=0.912911 unit=fraction seed=0
RESULT P2.delta_points=-1.55195 unit=auc_points seed=0
```

Other seeds: `P2.auc_5000_rows` 0.917974 and 0.917733. `P2.delta_points` -1.2665 and -1.39556. The mean effect over seeds 0 to 2 is -0.0140467 AUC (-1.40467 AUC points) against a spread of 0.005063 AUC (0.5063 points), so it passes the 2x rule.

Why: with 7.8 times fewer rows, each of the 31 leaves in each tree averages over fewer examples, so leaf values get noisier, rare categories (small countries, rare occupations) seldom earn a split of their own, and the 100 boosting rounds fit more of that noise. The loss stays small because the first splits of each tree, on the strongest columns, still see thousands of rows and land close to where the full data puts them; most of what the other 34,073 rows add is detail deep in the trees and in rare categories. The paired deltas vary less across seeds (spread 0.28545 AUC points) than the AUCs themselves (0.3259 points for `P1.auc_lgbm`, 0.5063 points for `P2.auc_5000_rows`), because each seed draws a new test set, and an easy or hard draw moves both runs of that seed together.

Common wrong prediction: a big drop of 5 points or more, because "boosting needs big data"; or no change at all, because the table looks easy.
</details>

<details><summary>P3. AUC of LightGBM trained on a shuffled target</summary>

**Answer:** chance level. Seed 0: **0.496038**, tolerance plus or minus 0.015446. Seeds 1 and 2: 0.484166 and 0.480592. The rule this step teaches: an honest pipeline scores 0.5 plus or minus noise here, and any AUC above 0.55 means a leak or a bug.

Seed-0 RESULT line:

```
RESULT P3.auc_shuffled=0.496038 unit=fraction seed=0
```

Why: shuffling cuts every link between the features and the labels the model learns from, so whatever LightGBM fits is noise and its scores say nothing about the true test labels; AUC, the chance that a random positive outranks a random negative, then sits at 0.5 in expectation. The scatter around 0.5 is wider than for independent random scores (about 0.007 standard deviation for this split's 2,338 positives and 7,431 negatives), because a tree gives a whole region of similar rows one shared noisy score. Six extra tagged seeds (3 to 8, kept out of the json) fell on both sides of 0.5 and all stayed under 0.55, so three values below 0.5 here are noise, not a bias. Against P1 the mean effect is -0.443321 AUC with a spread of 0.015446, so it passes the 2x rule: every bit of lift above a coin flip came from the labels.

Common wrong prediction: 0.6 to 0.7, on the idea that the unchanged features still carry "some" signal; or exactly 0.500, forgetting that a finite test set adds noise.
</details>

<details><summary>Optional --tabpfn. TabPFN v2 against LightGBM on the same 1,000 training rows</summary>

Seed 0 only, so there is no tolerance. Both models train on the same stratified 1,000 rows and score the same 9,769 test rows.

```
RESULT tabpfn.auc_lgbm_1000_rows=0.885742 unit=fraction seed=0
RESULT tabpfn.auc_tabpfn_1000_rows=0.900388 unit=fraction seed=0
```

TabPFN (Tabular Prior-data Fitted Network) v2 scored 0.900388 against LightGBM's 0.885742 on the same rows. Why: TabPFN was pretrained only on synthetic tables, so it arrives with a strong prior about what tabular relationships look like. LightGBM has to estimate every leaf from 1,000 rows. Both stay below LightGBM on all 39,073 rows (0.92843), and on a CPU (central processing unit) v2 refuses more than 1,000 training rows unless you override its limit.

Read with P2 and P1, LightGBM traces a learning curve at seed 0: 0.885742 on 1,000 rows, 0.912911 on 5,000 rows and 0.92843 on 39,073 rows. The first 4,000 extra rows bought more AUC than the next 34,073 did.

The run took 296.4 s on the shared build queue with torch on one thread (see build notes). In the first build's probe, most of the time went to TabPFN scoring the 9,769 test rows. v2 ran with no login: its Hugging Face repo is ungated, and `TABPFN_NO_BROWSER=1` stops any licence page.
</details>

<details><summary>Rebuild check</summary>

Stub: `ml-learning/m1-whole-game/rebuild/03_auc.py`. Solution: [`rebuild/03_auc.py`](rebuild/03_auc.py). Its two bodies are the AUC block of the lab script, line for line, so the rebuild is a retype of code the learner read at 0:05. `rebuildcheck` verdict: the stub fails as it should (exit 1, NotImplementedError), the solution passes (exit 0, prints `check: PASS`), REBUILDCHECK OK.

The check draws 2,000 synthetic labels and scores, rounds the scores to 0.1 so most of them tie, and needs both `auc_pairwise` and `auc_rank` to equal scikit-learn's `roc_auc_score` within 1e-12. The two traps, both confirmed to fail the check: counting a tie as 0 instead of 0.5, and ordinal ranks instead of average ranks.
</details>

<details><summary>Card drafts</summary>

| ID | Lab | Type | Question |
|---|---|---|---|
| 03-M | 03 | M | In lab 03 the 5,000-row and the full-data LightGBM were scored on the same test rows at each seed. Why did the AUC difference between them vary less from seed to seed than either AUC did? |
| 03-N | 03 | N | On the Adult census test split, what accuracy and what AUC does "always predict `<=50K`" score, and what does that say about accuracy as a yardstick? |
| 03-D | 03 | D | A fraud model retrained on a shuffled target still scores 0.62 AUC on the holdout. What do you check first? |

Keys:
- **03-M:** (1) each seed draws a new test set, and an easy or hard draw moves both models' AUCs the same way, because both score those same rows; (2) the difference cancels that shared part (the variance of A minus B is Var A + Var B - 2 Cov(A, B), and the covariance is positive), so compare models on the same rows and judge an effect against the spread of the paired difference.
- **03-N:** (1) accuracy 0.760672, which is just the share of `<=50K` rows; (2) AUC 0.5, because every row gets the same score and nothing is ranked; (3) a real model must clear that accuracy just to beat doing nothing, so accuracy hides how little a model adds on imbalanced data.
- **03-D:** (1) a path from the true labels around the shuffle: test rows that reach training with their true labels, or a preprocessing step the pipeline fits on rows that include the test labels (for example a target encoder fitted on every row); (2) that the shuffle really reached the labels the model trained on, and the score uses the true holdout labels; (3) the rule: an honest pipeline lands at 0.5 plus or minus test-set noise, so anything above the 0.55 alarm points at the pipeline, not the data. A post-outcome column, such as a chargeback flag, does not trip this alarm: with shuffled labels the model cannot learn its link to the label. Lab 07's single-column scan is the check for that one.

Reference soundbite (the 0:57 card can borrow it): "GBDT (gradient-boosted decision trees) first: on Adult, LightGBM trained in seconds on a CPU, beat logistic regression by about 2.2 AUC points and fell to about 0.50 on a shuffled target. In the repo's design a GBDT scores in about 2.5 ms on CPU with TreeSHAP reasons (SHAP: SHapley Additive exPlanations, computed fast for trees); Stripe moved Radar from XGBoost plus a DNN (deep neural network) to DNN-only in mid-2022, so the bar to move is a DNN that wins in shadow at a latency the inline budget can carry."

Staff follow-up answer (migration), from the repo link: release the DNN the way §7's "Model release" row says: shadow first (it scores live payments after the response and decides nothing), review the disagreement set, then a canary behind decline, step-up and review guardrails with the GBDT one registry pointer flip away (§5.5: canary at 5%, 25% and 100%, rollback under 1 minute), because outcomes take 60 to 90 days and an offline win on old labels does not prove it on today's traffic. It replaces the GBDT inline only if it also fits the in-process CPU budget of about 2.5 ms per score (§7, "Where the model runs"); if it does not, it earns its place as the heavier post-authorization model (§7, "Model family inline").
</details>

<details><summary>Build notes</summary>

- **Knob changes:** none. All three effects passed the 2x spread rule: the change (`P2.auc_5000_rows` against `P1.auc_lgbm`), the break (`P3.auc_shuffled` against `P1.auc_lgbm`) and the P1 gap (`P1.auc_lgbm` against `baseline.auc_logreg`).
- **Precomputed steps:** none. The longest seed-0 run is `--tabpfn` at 296.4 s, under the 6-minute cap, on a shared build queue.
- **Prototype comparison:** the spec's prototype values are logistic regression 0.906, LightGBM 0.928 and shuffled 0.496. Seed 0 gave 0.906038, 0.92843 and 0.496038: the same direction, and each gap far below its seed spread.
- **Review fixes that changed the script (all reference modes rerun):** the script now holds the AUC block (`auc_pairwise` and `auc_rank`), because a level W rebuild must retype code the learner read, and `score()` uses it: `auc_rank` gives the AUC and an assert checks that `auc_pairwise` agrees on every call. The UCI (University of California Irvine) fallback now reads `adult.test` before `adult.data` (OpenML 1590's row order, see Data). The third `# Q:` prompt is now a pure question. Accuracy thresholds the predicted probability at 0.5 (`p > 0.5`), which is what `predict()` does for the three models that print an accuracy, and it saves TabPFN a second pass over the test rows. A shorter main block keeps the script at 149 lines. Every RESULT value of the nine light-lane runs and of `--tabpfn` reproduced the previous reference exactly; only wall times moved.
- **OpenMP (Open Multi-Processing) clash (deviation, `--tabpfn` only):** LightGBM 4.7.0 links Homebrew's libomp and torch 2.14.1 ships its own. In one process they deadlocked (TabPFN's model load hung at full torch threads) or segfaulted (torch imported before LightGBM ran). The only order that worked in probes: fit LightGBM first, then `torch.set_num_threads(1)` before TabPFN. `KMP_DUPLICATE_LIB_OK` stays unset, as the spec requires.
- **Where the spec was silent:** the 5,000-row and 1,000-row subsets are stratified random draws from the training split (`train_test_split`, `random_state=seed`). The shuffle is a numpy permutation of the training labels at the seed; test labels are untouched. LightGBM's `random_state=seed` changes nothing with these defaults (no bagging), so its seed spread comes from the split.
- **Data:** category columns are recast through `object` to `category`, so all three download sources give the same sorted levels. In a probe of the script's own `load_adult()` with the OpenML API (application programming interface) and then the parquet copy forced to fail, both fallbacks matched the OpenML frame row for row: the same labels, values and categories, so the same seed-0 split. The UCI concat is identical even in dtypes; the parquet copy stores some integer columns as `uint8` or `float64`, which every model here turns into the same floats. No lab mode ran on the fallbacks.
- **Download and smoke:** `--download` also fetches the TabPFN v2 weights (29.0 MB) when tabpfn is installed, by fitting once on 100 rows with the public API. The script defaults `TABPFN_MODEL_CACHE_DIR` to `~/ml-data/tabpfn`, so the weights stay out of `~/Library/Caches`. `--smoke` runs all four steps on 7,000 rows (its 5,600 training rows hold the 5,000-row subset, and TabPFN gets 200 rows), and the TabPFN step only when tabpfn is installed.
- **P2 delta:** `P2.delta_points` comes from `labkit.prior`, so it prints only after `--baseline` ran with the same seed. The reference runs ran each seed's modes in order.
- **Spoiler choices in the lab file:** it leaves out the spec's "23.9% positive" (it answers the N card) and the 0.55 alarm threshold (it hints at P3's size). The Goal line drops the spec's "use a shuffled-target AUC as a leak alarm", because an alarm implies a known resting value for an honest pipeline, which is P3's answer. P1 asks for the signed gap (negative if logistic regression is ahead) instead of how far LightGBM "sits above" it. The leak-alarm framing lives here and in the module README's concept section, which is after-lab reading.
- **TabPFN 3.5:** `ml-learning/CLAUDE.md` §9 lists it among the learner's human steps. It needs a Prior Labs login, so the lab names it as optional and uncaptured, and no reference value exists.
- **Soundbite wording:** two sentences, as the lab template asks. It uses the repo's own Stripe wording (§10.8: moved from XGBoost plus a DNN to DNN-only), takes "mid-2022" from the spec note and the Stripe post the module README cites, and drops the spec note's "when more data stopped helping XGBoost", which nothing in the repo backs up.
- **Extra experiments:** six tagged `--break` runs (seeds 3 to 8, tag `null`) checked the shuffled AUC for bias. They were rerun on the current script and gave the same values as in the first build; mkanswers ignores tagged runs.
- **Verifier probe (card 03-D):** one tagged experiment (tag `v03leak`, kept out of the json) retrained LightGBM on the shuffled target at seeds 0, 1 and 2 on this lab's split, with one planted leak at a time. A raw column equal to the label, and a copy of it with 20% of rows flipped, stayed between 0.45 and 0.55 at every seed, like the honest pipeline. A target encoder on `fnlwgt` fitted on train plus test rows, and the test rows added to training with their true labels, each tripped the 0.55 alarm at every seed. So the 03-D key names only the paths that survive a shuffle, and sends post-outcome columns to lab 07's single-column scan.
</details>
