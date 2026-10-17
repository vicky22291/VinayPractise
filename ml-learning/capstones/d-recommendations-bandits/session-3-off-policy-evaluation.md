# D3. Off-policy evaluation: IPS, self-normalised IPS, the direct method and doubly robust on logged visits

> Goal: after this I can log 200 sets of 100,000 epsilon-greedy visits with their propensities, estimate a challenger's clicks per 1,000 visits from them with IPS (inverse propensity scoring), self-normalised IPS, the direct method and doubly robust, report each estimator's bias, SD (standard deviation) and RMSE (root mean squared error) against the simulator's true value at 4 exploration rates, and show what titles with zero propensity do to them. (No result values anywhere in this file. Capstones have no reference run and no answers file: your run is the answer.)

**Capstone:** [D, recommendations with bandits](README.md), session 3 of 4, labkit id 55. **Level:** B (see `ml-learning/CLAUDE.md`). **Output style:** Explanatory
**Builds on:** labs 23 (inverse propensity weights on a logged exploration slice) and 13 (offline scores cover only what the old ranker showed), plus your D1 world and history model
**Dataset:** the split, the synthetic world and the history model in `~/ml-data/capstones/d/`, plus a challenger this session trains on H2, the ratings in `~/ml-data/ml-100k/` that `split.npz` names
**Runs on:** cpu. **Lane:** light. **Compute:** no reference run; 2 measured runs, each capped at 6 min. Precomputed steps: none
**Needs:** base install only
**Before the session:** D1 done: `--download`, then both modes at seed 0. Nothing to download.
**Interview question:** You have a week of logs from the current ranker. Estimate a new ranker's click rate before it serves anyone: which estimator, what must the logs hold, and how wrong can it be?
**Repo link:** [`hld/news-aggregator/deep-dives/ranking-and-cold-start.md`, §7 Cold start, and moving to a learned model](../../../hld/news-aggregator/deep-dives/ranking-and-cold-start.md#7-cold-start-and-moving-to-a-learned-model) (offline vs online: replay on the uniform slot, and only the online A/B test decides); [`hld/payments-risk-decisioning/deep-dives/model-lifecycle-shadow-and-labels.md`, §3 Two exploration slices, because 3DS biases one](../../../hld/payments-risk-decisioning/deep-dives/model-lifecycle-shadow-and-labels.md#3-two-exploration-slices-because-3ds-biases-one) (weight by the logged propensity)
**Captured by the script:** P1 to P3 and every Record row. **Human steps:** the estimators, the design and the write-up
**Status:** todo

## 0. Framing (0:00, 7 min, no AI)

Reread your framing line in `design-doc.md`. Under it, write one line: what the log must hold for every impression, and which policy you want to value without serving it.

## 1. Predict (0:07, 5 min, no AI)

Write each row here and in `../../prediction-log.md` (Lab `D3`) before anything runs. Every value is in synthetic clicks per 1,000 visits.

| Step | Question | Kind | Prediction | 80% range or confidence |
|---|---|---|---|---|
| P1 | The champion's log: epsilon-greedy at 0.1 around greedy on the history model, with its propensities, 200 logs of 100,000 synthetic visits, seed 0. The challenger: greedy on the same config trained on H2, the half of H the champion never saw. The width of the middle 95% of the 200 IPS estimates of the challenger's clicks per 1,000 visits | num | | |
| P2 | The same 200 logs at ε = 0.01 instead: which of IPS, self-normalised IPS, the direct method and doubly robust has the lowest RMSE against the challenger's true value? One option and a confidence | pick | | |
| P3 | Positivity: ε = 0.1, but an explored visit shows a uniform title from the 50 with the highest rating count in H only. The mean of the 200 IPS estimates minus the true value. Up, down or same, plus a size range | dir | | |

Terms, fixed so your numbers compare with D1 and D2:

- **Champion.** g_A(u): the title that greedy on the history model, fit on H1, shows user u. Like every model-based pick, it ranges over the 180 titles that are not new (D1's Terms).
- **Behaviour policy.** With probability ε a uniform title from the 200, else g_A(u). ε = 0.1 in the baseline.
- **Propensity.** μ(a | u) = (1 - ε) x 1[a = g_A(u)] + ε / 200: the probability that the behaviour policy shows title a to user u. It is written into the log with every visit, as lab 23 logged each row's π.
- **A log.** 100,000 visits, each with its user, the shown title, its propensity and its synthetic click. 200 logs per setting, drawn in order from `numpy.random.default_rng(seed)`. Each log fixes its users, its explore draws and its click numbers once, and every setting reuses them, so explored visits nest as in lab 23: a visit explored at 0.01 is explored at 0.05, 0.1 and 0.3 too.
- **Challenger.** Lab 33's config trained on H2 at seed 0. Champion and challenger learn from two disjoint halves of H, and neither saw a rating in W or of a new title. Fit once and saved to `challenger.npz` for D4. g_B(u) is its top title for user u among the same 180.
- **True value.** 1,000 x the mean over the 943 users of p(u, g_B(u)), exact from the world. The champion's and the behaviour policy's true values come the same way.
- **Estimators.** For one log of n visits, valuing π = g_B:

```text
w_i   = 1[a_i = π(u_i)] / μ_i                      μ_i: the propensity logged with visit i
IPS   = 1000 * (1/n) * sum_i w_i * r_i             r_i: the synthetic click of visit i
SNIPS = 1000 * sum_i w_i * r_i / sum_i w_i         self-normalised IPS
DM    = 1000 * (1/n) * sum_i q(u_i, π(u_i))        the direct method; q is the champion model's p_hat
DR    = DM + 1000 * (1/n) * sum_i w_i * (r_i - q(u_i, a_i))      doubly robust
```

- **The reward model q.** The champion model's p_hat. It learned only from H1 and never saw W, so the direct method models rewards from the policy side's data alone, as a real platform must.
- **IPS is lab 23's IPW.** Lab 23 weighed each explored row by 1/ε to estimate a challenger's recall under the champion's declines. IPS puts the weight 1/μ on each logged visit whose title the challenger would also have shown.
- **Naive (recorded, not predicted).** 1,000 x the mean click over the logged visits whose title is the challenger's pick, unweighted.
- **Error over the 200 logs.** Bias: the mean of the 200 estimates minus the true value. SD: their standard deviation. RMSE: the square root of the mean squared gap to the true value. Width: the 97.5th minus the 2.5th percentile.
- **Exploration rates (change).** ε = 0.01, 0.05 and 0.3, beside the baseline's 0.1.
- **Positivity (change).** ε = 0.1, but an explored visit shows a uniform title from the 50 with the highest rating count in H only (D1's Terms). A title outside those 50 then has propensity 0, unless it is g_A(u). Every estimator runs unchanged, on the propensities in the log.

## 2. Setup (before the session)

```
$ source ~/.venvs/ml/bin/activate
$ cd ml-learning/capstones/d-recommendations-bandits
$ python scripts/d3_off_policy_evaluation.py --download
$ python scripts/d3_off_policy_evaluation.py --smoke
```

`--download` only checks that `split.npz`, `world.npz`, `history.npz` and the ratings exist, and prints their paths. `--smoke` fits the challenger for 1 epoch on 10,000 ratings of H2 and runs 5 logs of 1,000 visits per setting.

## 3. Baseline (0:12, 15 min)

Why: a log holds clicks only for the titles the behaviour policy showed, so the value of any other policy must reweight what was shown or model what was not.

You write first, in this file, no AI (about 5 min). This is the prompt the AI builds from:

1. The behaviour policy and its propensity, and what each logged visit holds.
2. How the 200 logs are drawn and reused across settings, the challenger's true value, and the four error measures.
3. The RESULT contract: every name in the Record table, the mode that prints it, and its unit.

Then write `ips`, `snips`, `dm` and `dr` yourself, no AI (about 3 min), one function each from the formulas in Terms. The AI then writes the script with `labkit.start(lab=55)`, with the challenger fit once at seed 0. Annotate each AI block with one line before the first run.

```
$ python scripts/d3_off_policy_evaluation.py --smoke
$ python scripts/d3_off_policy_evaluation.py --baseline
(paste your RESULT lines)
```

Prediction vs actual, one sentence for P1. There is no reference run: the AI fills Actual and Hit from your pasted lines.

## 4. Change one thing (0:27, 15 min; the run finishes by 0:40)

Change: the exploration rate, ε = 0.01, 0.05 and 0.3 on the same 200 logs, then the positivity log at ε = 0.1. The champion, the challenger and the four estimators stay fixed. P2 and P3 are logged above.

Why: the exploration rate sets how often a log holds the challenger's pick, and a production log often explores only part of the catalogue.

```
$ python scripts/d3_off_policy_evaluation.py --change
(paste your RESULT lines)
```

Prediction vs actual, one sentence each for P2 and P3.

## 5. Write-up (0:42, 15 min, no AI)

- **Explain-back (5 min).** Five sentences for a smart engineer new to ML. Then ask the AI for the weakest claim, not a rewrite.
- **Deliverable (10 min).** Add to `design-doc.md` §6 Logging and propensities (what every impression logs, and what the positivity log did) and §7 Offline evaluation (the four estimators at each ε as bias, SD and RMSE, and the one you would trust for a launch decision, with why). At most 4 lines each.

## 6. What I learned

The five explain-back sentences, edited after the AI's question.

## 7. Interview soundbite (the card written at 0:57)

> One or two sentences only someone who ran this would say.

Framing: decision ___ | prediction time ___ | label and its maturity ___ | offline metric ___ | online metric ___ | guardrail ___

Staff follow-up (cost): the news HLD prices its uniform slot at about 5% of clicks [estimate], and the payments HLD caps its approve slice with a monthly dollar budget. How large must your exploration be to value the challenger to within 1 click per 1,000 visits, and who signs off on the clicks it gives up? Answer in 2 sentences from [§4 of the ranking deep dive](../../../hld/news-aggregator/deep-dives/ranking-and-cold-start.md#4-one-card-per-story-diversity-exploration) and the payments link's §3.

## 8. Close (0:57, 3 min)

The AI drafts card `D3-T` (a variant you did not run, or the payments version) from your run. Edit or replace it. The question goes to `../../quiz-bank.md`, the key to `../../answers/quiz-key.md`, citing your RESULT line. Set Status here and in the [README](README.md#sessions).

## Record

Suggested names: if your RESULT contract renames them, edit this table first. Paste, do not type.

| Metric | Your run | Hardware (the script's HW line) | Captured by (script or learner) |
|---|---|---|---|
| `baseline.true_challenger`, `baseline.true_champion` and `baseline.true_behaviour` (clicks per 1,000 visits, exact from the world) | | | script |
| `baseline.agree_share` (share of users whose challenger pick is the champion's) | | | script |
| `baseline.matched_per_log` (mean visits per log whose shown title is the challenger's pick) | | | script |
| `P1.ips_width` (middle 95% of the 200 IPS estimates) | | | script |
| `baseline.<est>_bias`, `baseline.<est>_sd` and `baseline.<est>_rmse` for est = ips, snips, dm, dr and naive (ε = 0.1) | | | script |
| `change.<est>_bias_<eps>` and `change.<est>_rmse_<eps>` for est = ips, snips, dm and dr at eps = 0p01, 0p05 and 0p3 | | | script |
| `change.ips_width_<eps>` at eps = 0p01, 0p05 and 0p3 | | | script |
| `P2.lowest_rmse_0p01` (the estimator name) | | | script |
| `change.unsupported_share` (share of users whose challenger pick has propensity 0 in the positivity log) | | | script |
| `P3.ips_bias_positivity` | | | script |
| `change.snips_bias_positivity`, `change.dm_bias_positivity` and `change.dr_bias_positivity` | | | script |
| `baseline.fit_s` (the challenger fit, seconds, M4 Pro, cpu) | | | script |
