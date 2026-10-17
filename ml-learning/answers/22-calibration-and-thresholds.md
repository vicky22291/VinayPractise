# 22. Calibration and decline thresholds: what downsampling does to probabilities: reference answers

> Spoilers. The AI opens one block at a time, only after that step's prediction row exists and the learner pasted their own RESULT lines, or after 'debrief 22'.

- **HW:** `HW chip='Apple M4 Pro' cpu=14 gpu=20 mem_gib=24 macos=26.5.1 python=3.13.7 torch=2.14.1 device=cpu`
- **Seeds:** 0, 1 and 2 for every mode, `--amount` included. A seed changes the 80/20 split and the downsampling draw.
- **Reference script:** `answers/22_calibration_and_thresholds_ref.py` (script_sha256 `b10ee8078955727d`). Raw seed-0 output: `22-calibration-and-thresholds.out`. RESULT values below are copied from the .json; TABLE lines (reliability tables, not RESULT lines) are copied from the .out.
- **Runs and wall times:** 12 runs, all light lane, none precomputed. Seed 0: baseline 3.1 s, change 2.1 s, break 2.3 s, amount 1.9 s. Seed 1: 4.1, 2.6, 2.2 and 1.7 s. Seed 2: 4.7, 1.9, 2.1 and 1.9 s.
- **Tolerance rule:** tol = spread (max - min) over seeds 0, 1, 2; heavy labs: the baseline spread applies to every step. A prediction hits when the actual lies inside the learner's own 80% range; the tolerance says how much a rerun on another split moves the number.

<details><summary>P1. Mean predicted fraud probability of the full-data logistic regression on the untouched test set (true rate 0.17%)</summary>

**Answer:** 0.0017368 at seed 0, tolerance 0.00014596. The test set's observed fraud rate is 0.00172045 at every seed (98 frauds in 56,962, by the stratified split).

```
RESULT P1.mean_p=0.0017368 unit=fraction seed=0
RESULT baseline.mean_p_legit=0.000671211 unit=fraction seed=0
RESULT baseline.fraud_rate=0.00172045 unit=fraction seed=0
RESULT baseline.threshold=0.0387062 unit=probability seed=0
RESULT baseline.decline_rate=0.00200133 unit=fraction seed=0
RESULT baseline.false_declines=34 unit=count seed=0
RESULT baseline.frauds_caught=80 unit=count seed=0
RESULT baseline.brier=0.000728463 unit=brier seed=0
TABLE full bin mean_p observed
TABLE full   1 0.000026 0.000000
TABLE full   2 0.000060 0.000176
TABLE full   3 0.000089 0.000000
TABLE full   4 0.000123 0.000000
TABLE full   5 0.000167 0.000000
TABLE full   6 0.000223 0.000176
TABLE full   7 0.000302 0.000351
TABLE full   8 0.000431 0.000527
TABLE full   9 0.000688 0.000878
TABLE full  10 0.015256 0.015096
```

Other seeds: P1.mean_p 0.00188276 (seed 1) and 0.00183574 (seed 2).

**Why.** A logistic regression with an intercept is fitted until its predicted probabilities average to the training fraud rate (up to the solver's tolerance), so on an untouched test set drawn at random from the same payments the mean lands next to the true rate: calibration in the large comes with the loss. The reliability table shows the rest of the shape: nine bins near zero, and most of the probability mass in the top bin, whose mean predicted 0.015256 sits on its observed 0.015096. The decline threshold (0.0387062, the champion's 99.8th percentile on its training payments) declines 0.00200133 of the test payments: 80 frauds caught and 34 false declines.

**Common wrong prediction:** an answer an order of magnitude off in either direction, from treating a classifier's score as a ranking with no scale. Logistic regression trained on the real class mix is the case where the score is already close to a probability.
</details>

<details><summary>P2. Trained on all frauds plus 10% of legitimate rows: mean predicted probability on the same test set</summary>

**Answer:** 0.00470345 at seed 0, tolerance 0.00038976. That is 2.7 times P1 (0.00470345 / 0.0017368), not 10 times. Effect P2 minus P1, mean over the three seeds: 0.00305013, against a spread of 0.00038976, so it passes the 2x rule.

```
RESULT P2.mean_p=0.00470345 unit=fraction seed=0
RESULT change.mean_p_legit=0.00333985 unit=fraction seed=0
RESULT change.mean_p_corrected=0.00188795 unit=fraction seed=0
RESULT change.brier=0.00086552 unit=brier seed=0
RESULT change.brier_corrected=0.000697716 unit=brier seed=0
TABLE downsampled bin mean_p observed
TABLE downsampled   1 0.000106 0.000000
TABLE downsampled   2 0.000266 0.000000
TABLE downsampled   3 0.000406 0.000000
TABLE downsampled   4 0.000568 0.000176
TABLE downsampled   5 0.000774 0.000000
TABLE downsampled   6 0.001056 0.000000
TABLE downsampled   7 0.001481 0.000000
TABLE downsampled   8 0.002230 0.000702
TABLE downsampled   9 0.003816 0.000527
TABLE downsampled  10 0.036328 0.015798
TABLE corrected bin mean_p observed
TABLE corrected   1 0.000011 0.000000
TABLE corrected   2 0.000027 0.000000
TABLE corrected   3 0.000041 0.000000
TABLE corrected   4 0.000057 0.000176
TABLE corrected   5 0.000077 0.000000
TABLE corrected   6 0.000106 0.000000
TABLE corrected   7 0.000148 0.000000
TABLE corrected   8 0.000223 0.000702
TABLE corrected   9 0.000383 0.000527
TABLE corrected  10 0.017805 0.015798
```

Other seeds: P2.mean_p 0.00509321 and 0.00480902; change.mean_p_corrected 0.00198063 and 0.00182854; change.mean_p_legit 0.00361443 and 0.00337744.

**Why.** Keeping 10% of the legitimate rows multiplies the fraud odds in the training data by 10, and the model is calibrated to that mix (394 frauds in 23,139 training rows, 1.7%), so its scores rise, but the mean rises far less than 10 times, for two reasons. First, the 98 test frauds already score high and carry 61% of the champion's mean (98.9 of probability mass in all, 38.2 of it on legitimate rows, from P1.mean_p and baseline.mean_p_legit), and a probability cannot pass 1: a fraud at 0.9 can only climb toward 1, so the frauds' average moves only from about 0.62 to about 0.80. Second, the legitimate payments' mean rises 5.0 times (change.mean_p_legit 0.00333985 against baseline.mean_p_legit 0.000671211), not 10. The refit moves the slopes as well as the intercept, because a linear logit is not exactly right for this data, so the best fit depends on the class mix and the lift differs from payment to payment.

**The prior correction** p' = b p / (b p - p + 1) with b = 0.10 brings the mean to 0.00188795, about 10% above the true rate 0.00172045. It lowers the Brier score at all three seeds: 0.00086552 to 0.000697716 at seed 0, and 0.000757481 to 0.000522793 and 0.000585561 to 0.00048383 at seeds 1 and 2. Each drop is smaller than the seed spread of the raw Brier score (0.000279959), so read it as a paired, same-sign effect that is small next to how far the Brier level moves from one split to the next. Bin by bin the corrected scores are not the champion's: at every seed its bins 1 to 9 sit below the champion's matching bins, and at seeds 0 and 1 its top bin sits above its observed rate (0.017805 against 0.015798 at seed 0), so the correction fixes the level, not every bin. Interview line: after 10:1 downsampling, a raw 0.3 means about 0.041 (0.1 x 0.3 / (0.03 - 0.3 + 1)).

**Common wrong prediction:** about 10 times P1 (near 0.017), from "odds times 10 means probability times 10". That holds only for small probabilities of a model whose logit is exactly right; the high-scoring frauds and the refit slopes both pull the mean ratio down.
</details>

<details><summary>P3. Ship the downsampled model with the full-data threshold: the new decline rate, and false declines per 56,962 test transactions</summary>

**Answer:** decline rate 0.0103578 (tolerance 0.00168535) and 505 false declines (tolerance 101) at seed 0, against the champion's 0.00200133 and 34 at the same threshold. P3 is graded as two numbers (lab file): a hit needs both inside the learner's ranges, and Off by uses the false declines. Effects, mean over three seeds: decline rate up 0.00723875 (spread 0.00168535) and false declines up 407.333 (spread 101); both pass the 2x rule.

```
RESULT P3.decline_rate=0.0103578 unit=fraction seed=0
RESULT P3.false_declines=505 unit=count seed=0
RESULT break.frauds_caught=85 unit=count seed=0
RESULT break.decline_rate_corrected=0.00214178 unit=fraction seed=0
RESULT break.false_declines_corrected=43 unit=count seed=0
RESULT break.frauds_caught_corrected=79 unit=count seed=0
RESULT break.new_fd_gap=6.18394 unit=ratio seed=0
RESULT break.new_fd_lift=12.2305 unit=ratio seed=0
```

Other seeds: P3.decline_rate 0.00886556 and 0.00867245; P3.false_declines 415 and 404; break.frauds_caught 90 and 90; break.new_fd_gap 5.68828 and 6.25137; break.new_fd_lift 9.92798 and 9.37861. Prior-corrected: decline rate 0.00242267 and 0.002054, false declines 50 and 34, frauds caught 88 and 83. Champion at seeds 1 and 2: decline rate 0.00217689 and 0.00200133, false declines 37 and 31, frauds caught 87 and 83.

**Why.** The threshold did not move, and the downsampled model did not lift every score by one factor: the refit changed the slopes as well as the intercept (P2), so the lift varies widely from payment to payment, and a fixed cutoff picks out the legitimate payments whose scores rose most. The ones that newly cross started a median 6.18394 times below the cutoff (break.new_fd_gap) and rose a median 12.2305 times (break.new_fd_lift), about the full odds factor of 10, while the legitimate mean rose 5.0 times: they were not good payments sitting just under the line. That takes false declines from 34 to 505, 15 times, while frauds caught move only from 80 to 85, because most frauds were above the line already: the extra 471 good customers declined bought 5 more frauds. The decline rate grows less, 5.2 times (0.0103578 / 0.00200133), because frauds were 80 of the champion's 114 declines.

**The prior correction** before the same threshold puts the operating point back near the champion's: decline rate 0.00214178, 43 false declines and 79 frauds caught, gaps that sit inside the corrected values' own seed spread (0.00036867 and 16). So the threshold ships and rolls back with the model version and its calibration (repo §6).

**Common wrong prediction:** "the model ranks payments about as well, so the decline rate barely moves". A fixed threshold reads the scale, not the rank order. The other common miss multiplies the champion's 0.2% by one factor, 10 from the odds argument or about 5 from the legitimate mean. The rate depends on which payments cross the cutoff, not on one factor: at seeds 0, 1 and 2 it came out 5.2, 4.1 and 4.3 times the champion's, while the legitimate mean rose 5.0, 5.2 and 5.3 times, so the two do not track each other.
</details>

<details><summary>--amount. Net test-set dollars at a flat vs an amount-aware threshold (Record only, no prediction)</summary>

**Answer:** at seed 0 the flat rule (p\*($200) = 0.14 for every payment) nets $3505 and the amount-aware rule (p\*(a) per payment) nets $3445.24, a gain of -59.7597 dollars. The two rules decide 8 of 56,962 test payments differently, and 4 of those 8 are frauds.

```
RESULT amount.net_flat=3505 unit=dollars seed=0
RESULT amount.net_aware=3445.24 unit=dollars seed=0
RESULT amount.net_gain=-59.7597 unit=dollars seed=0
RESULT amount.declines_flat=91 unit=count seed=0
RESULT amount.declines_aware=83 unit=count seed=0
RESULT amount.changed=8 unit=count seed=0
RESULT amount.changed_frauds=4 unit=count seed=0
```

Other seeds (`--amount` also ran at seeds 1 and 2 to give it a spread): net_gain -38.6599 and -66.2657 (spread 27.6058); changed 4 and 6; changed_frauds 3 and 4. net_flat 8256.32 and 9963.29, net_aware 8217.66 and 9897.02 (their spread is the split, not the rule).

**Why.** The rules disagree only where a score falls between p\*(a) and 0.14. At every seed, declines_flat minus declines_aware equals changed, so every disagreement is a payment the amount-aware rule approved, which only happens under $200, where p\*(a) climbs to 0.23 at $20 and 0.35 at $0. Half or more of those payments were frauds, more than their scores (all between 0.14 and 0.35) claim, so approving them cost more than the false declines saved. The loss is a handful of payments and its mean is below 2x its seed spread: read it as small, not as proof that a flat threshold is better.

**The lesson:** the run shows a handful of payments under $200, scored between p\*($200) and p\*(a), whose observed fraud share exceeds their scores. That is a sign of miscalibration in the low-amount band, and p\*(a) is right only if the probabilities are calibrated inside each amount band, so check calibration per band before trusting p\*(a) for small payments. The cost side is domain reasoning, not a measured result. L(a) = a + $15 both sets the rule and scores the dollars here, so the run cannot show whether it underprices small frauds. The repo's §4 notes that small payments are where card testing lives, and a card test's real cost is the next payment on that card, which argues for pricing card testing separately (velocity rules, step-up).
</details>

<details><summary>Rebuild check</summary>

Stub: `m4-production-ml-payments/rebuild/22_calibration.py`. Solution: `answers/rebuild/22_calibration.py`. `rebuildcheck` verdict: the stub fails as it should (exit 1, NotImplementedError), the solution passes (exit 0, `check: PASS`), `REBUILDCHECK OK`. `check()` compares `brier()` with `sklearn.metrics.brier_score_loss` to 1e-15, `reliability_table()` with `sklearn.calibration.calibration_curve(strategy="quantile")` to 1e-12 on 20,000 synthetic rows, and fits a scikit-learn `LogisticRegression` on a 200,000-row toy logistic model with 10% of its negatives kept: the corrected mean must return to the base rate within 5%.
</details>

<details><summary>Card drafts</summary>

| ID | Lab | Type | Question |
|---|---|---|---|
| 22-M | 22 | M | You train on every fraud plus 10% of the legitimate rows. Why does the mean predicted probability on untouched data rise far less than 10 times? |
| 22-N | 22 | N | On 56,962 test payments, the champion's threshold made 34 false declines. About how many did the 10%-downsampled model make at the same threshold, and why? |
| 22-D | 22 | D | A retrained fraud model went live and the decline rate jumped from 0.2% to about 1% overnight, while frauds caught barely moved. What do you check first, and what is the fix? |

Keys:

- **22-M:** (1) the keep rate multiplies the fraud odds by 10, not the probability: frauds already score high, far above the legitimate payments, and carry most of the mean (61% here), and a probability cannot pass 1, so the fraud part barely moves; (2) the legitimate payments' mean rises about 5 times, not 10, because the refit changes the slopes as well as the intercept.
- **22-N:** (1) about 505, 15 times more (seed spread 101); (2) the cutoff did not move while the lift varied by payment: the legitimate payments that newly cross started about 6 times below it and rose a median 12 times, near the full odds factor of 10, not the 5 times of the legitimate mean; (3) only 5 more frauds caught, because most frauds were above the line already.
- **22-D:** (1) whether the training sampling rate changed without a new calibration or threshold: compare the mean predicted probability with the observed fraud rate; (2) fix with the prior correction p' = b p / (b p - p + 1), or reset the threshold to the matched decline rate; (3) ship the threshold and calibration with the model version, so they flip and roll back together.
</details>

<details><summary>Build notes</summary>

- **Knob change (threshold rows).** The first reference runs set the champion's threshold at the 99.8th percentile of its scores on the 56,962 test payments. Both P3 effects then fell just short of 2x their seed spread: the 99.8th percentile of 56,962 scores rests on about 114 rows and moved a lot between splits, and P3 moved with it. The threshold now comes from the champion's scores on its own 227,845 training payments, so it is fixed before the test traffic arrives. That halved the P3 spread and both effects pass. The seed-0 threshold barely moved. The lab file's P3 row and Terms say "0.2% of its training payments". These are in-sample scores. A side check with 5-fold out-of-fold scores on the training rows moved the threshold by less than its seed spread and the P3 false declines by well under theirs, so the numbers stand for this L2 logistic regression. A flexible model such as lab 24's LightGBM needs held-out or out-of-time scores; the lab file's Terms say so.
- **Diagnostics added beyond the spec's Record list:** `baseline.mean_p_legit` and `change.mean_p_legit` (the legitimate payments' mean rises about 5 times, not 10), `baseline.fraud_rate`, the frauds-caught counts, and `amount.changed` and `amount.changed_frauds` (how few payments the two amount rules decide differently). Review round: `break.new_fd_gap` and `break.new_fd_lift`, medians over the legitimate test payments the downsampled model declines and the champion approves, of threshold / champion score and of downsampled score / champion score. An earlier P3 explanation said every legitimate score rose about 5 times and that hundreds of good payments sat just under the cutoff. A review check showed that only a handful of legitimate test payments sit within 20% below the threshold, and that a uniform lift by the legitimate mean multiple reproduces roughly half of the new false declines or fewer at every seed. The two diagnostics show the real mechanism in the RESULT contract. Adding them changed the reference hash, so all 12 reference runs were redone, and every earlier value reproduced exactly.
- **Side checks, not in the RESULT contract.** A refit with almost no penalty (C = 10,000) gave about the same mean ratios, so the L2 penalty is not the cause of the 5 times. The per-payment lift (downsampled score / champion score) of the legitimate test payments is widely spread at every seed, as a refit that moves the slopes would give.
- **`--amount` at seeds 1 and 2 as well** (the plan asked for seed 0 only), so its values carry a spread. The spec does not name the flat threshold: it is p\*($200) under the same L(a) and C_fd(a), the repo's $200 example, so the comparison isolates the amount dependence. Scores are the champion's. A review check of the changed payments found that most are tiny, but at seeds 0 and 2 the largest single contributor to `amount.net_gain` is a changed fraud well above $1, so the --amount lesson claims only miscalibration in the band under $200.
- **29 features, not 30.** OpenML marks Time as the row identifier of dataset 1597, so `fetch_openml` leaves it out. The models take `FEATURES` = V1 to V28 plus Amount, in that order, as float64 numpy arrays. Lab 24's spec mentions a 1 x 30 row: it should replay 1 x 29 rows in `FEATURES` order. Saved at seed 0: `champion_lr.joblib`, `challenger_lgbm.joblib` (`LGBMClassifier(n_estimators=100, random_state=0, verbose=-1)`; `verbose=-1` only silences logging) and `test_idx.npy` (positions in the OpenML frame, from `train_test_split(np.arange(n), test_size=0.2, stratify=y, random_state=0)`, the same split as labs 09 and 27 when they split the same frame). No threshold file is saved. Lab 24's "champion's threshold" is this lab's: `numpy.quantile` at 0.998 of the champion's scores on the training rows, which are every row not in `test_idx.npy`. Recomputed that way from the saved champion it equals `baseline.threshold` at seed 0.
- **Parquet fallback checked:** `dataset_1597.pq` has the same 284,807 rows in the same order with identical labels and features (it also carries Time, which `FEATURES` ignores).
- **Choices where the spec is silent:** downsampling draws exactly round(0.10 x legitimate training rows) without replacement with `numpy.random.default_rng(seed)`; the threshold uses numpy's default linear quantile and a decline means a score strictly above it; the reliability tables use `calibration_curve(strategy="quantile")` on the test rows; smoke runs all four modes on a fixed 30,000-row sample.
- **Starter:** beyond `load_data()` and `report()`, it ships `save_for_lab24()` (so lab 24's file names cannot drift) and a `correct_for_downsampling()` stub that raises NotImplementedError until the learner writes it. Its `--smoke` prints every RESULT name with placeholder values. At the current starter version, `--download` and `--smoke` pass and `--baseline` raises NotImplementedError("write the harness: see the lab file"), all three in tagged check runs.
- **Prototype comparison** (spec values, all within 2x the seed spread, same directions): mean p 0.174% full against 0.0017368; 0.479% downsampled against 0.00470345 (2.8 against 2.7 times); 0.187% corrected against 0.00188795; threshold 0.0385 against 0.0387062; 1.124% and 555 false declines against 0.0103578 and 505; 34 against 34; corrected 0.225% and 48 against 0.00214178 and 43. The prototype's P3 sits above seed 0 but inside seed 0's tolerance; a different downsampling draw is enough to explain it.
</details>
