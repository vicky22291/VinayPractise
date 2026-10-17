# D4. The ranking stage and the mock: exploration as a cost, a bandit vs an A/B test, then 45 minutes on the ladder

> Goal: after this I can put a bandit at the ranking stage of a two-stage recommender, price its exploration in clicks per 1,000 visits, compare a 4-arm A/B test that holds each user in one arm and computes its interval over users with a 4-arm Thompson bandit in clicks lost over 200,000 visits, measure the effective catalogue size of 500,000 impressions, and answer the 8-probe streaming home page ladder in 45 minutes, graded on 6 criteria. (No result values anywhere in this file. Capstones have no reference run and no answers file: your run is the answer.)

**Capstone:** [D, recommendations with bandits](README.md), session 4 of 4, labkit id 56. **Level:** B (see `ml-learning/CLAUDE.md`). **Output style:** Explanatory
**Builds on:** labs 13 (candidates, then a ranker), 25 (A/B power, peeking and label maturity) and 23 (an exploration slice priced in what it lets through), plus sessions D1 to D3
**Dataset:** the split, the world, the history model and the challenger saved in `~/ml-data/capstones/d/` (synthetic)
**Runs on:** cpu. **Lane:** light. **Compute:** no reference run; 1 measured run (the replay), capped at 6 min. Precomputed steps: none
**Needs:** base install only
**Before the session:** write the replay design in section 3 (at the end of D3, or the day before), let the AI write `scripts/d4_ranking_stage_replay.py` from it, annotate it, and run `--smoke` only. Have your D3 Record table and your lab 25 `n_per_arm()` open.
**Interview question:** Design the recommendations for a streaming home page: where does a bandit sit, what does its exploration cost, and when do you still run an A/B test?
**Repo link:** [`hld/news-aggregator/deep-dives/ranking-and-cold-start.md`, §1 Candidate lanes](../../../hld/news-aggregator/deep-dives/ranking-and-cold-start.md#1-candidate-lanes) (the scorer is the red node, and a v2 model must fit about 1 ms); [same file, §8 Feedback loops and popularity bias](../../../hld/news-aggregator/deep-dives/ranking-and-cold-start.md#8-feedback-loops-and-popularity-bias); [`hld/payments-risk-decisioning/deep-dives/model-lifecycle-shadow-and-labels.md`, §3 Two exploration slices, because 3DS biases one](../../../hld/payments-risk-decisioning/deep-dives/model-lifecycle-shadow-and-labels.md#3-two-exploration-slices-because-3ds-biases-one) (a slice with logged propensities and a monthly cap)
**Captured by the script:** P1 to P3 and every replay row. **Human steps:** the replay design, the plan, the mock and the self-grade
**Status:** todo

This session runs its own clock: predict 0:00, replay 0:04, plan 0:09, mock 0:13 to 0:58, close 0:58. The self-grade is a separate 25-minute block within 24 hours.

## 0. Framing (inside the predict block, no AI)

Reread your framing line. This session turns its online metric and guardrail into a rollout: exploration at the ranking stage, then a bandit or an A/B test.

## 1. Predict (0:00, 4 min, no AI)

Write each row here and in `../../prediction-log.md` (Lab `D4`) before the replay runs. Clicks are synthetic.

| Step | Question | Kind | Prediction | 80% range or confidence |
|---|---|---|---|---|
| P1 | Each user's candidates are the champion model's top 20 of the 180 titles that are not new (D1's Terms). Epsilon-greedy at 0.05 among them (a uniform candidate on explore, else candidate 1) against candidate 1 always, 500,000 synthetic visits, seed 0: expected clicks per 1,000 visits given up | num | | |
| P2 | Four rankers over the same candidates as arms: candidate 1, the challenger's top candidate, the candidate most rated in H and a uniform candidate. An A/B test (each user held in one of the 4 for the whole replay, by a hash of the user id) and a Thompson bandit over the 4 (Beta(1, 1) each, choosing per visit), 200,000 visits each: regret against always running the best ranker, A/B test minus bandit. Up, down or same, plus a size range in synthetic clicks | dir | | |
| P3 | The effective catalogue size of the 500,000 impressions: candidate 1 always minus the oracle (each user's best of all 200 titles). Up, down or same, plus a size range in titles | dir | | |

Terms:

- **Candidates.** The champion model's (D1's history model's) top 20 titles per user by p_hat, from the 180 that are not new: lab 13's first stage. Candidate 1 is the champion's pick, g_A(u).
- **Recall ceiling.** The share of users whose oracle title is among their 20 candidates: lab 13's recall@K with one relevant title per user. No ranker over these candidates can show the rest.
- **Exploration at the ranking stage.** With probability 0.05 a uniform candidate of the 20, else candidate 1. Its cost is the expected clicks per 1,000 visits of candidate 1 always, minus this policy's, from p. The catalogue version explores over all 200 titles instead, as D3's behaviour policy did. Each is its own policy, with its own cost and its own ECS.
- **Rankers, the arms.** (1) Candidate 1. (2) The candidate with the challenger's highest p_hat. (3) The candidate with the highest rating count in H, lab 13's popularity sort. (4) A uniform candidate. A ranker's true value is 1,000 x the mean over users of p(u, its pick), and for (4) the mean over each user's 20 candidates.
- **A/B test.** Each user stays in one of the 4 rankers for the whole replay: the arm is SHA-256 of `d4-<seed>:<user id>`, its first 8 bytes read as a big-endian integer, mod 4. That is the bucket function of the [bucketing deep dive](../../../hld/feature-flag-service/deep-dives/evaluation-and-bucketing.md#3-measured-sticky-monotonic-independent-uniform) §3 with the seed as the salt, so a new seed is a fresh, independent assignment. It runs for 200,000 visits. The unit is the user: each user's clicks per 1,000 of their own visits is one value, and an arm's estimate is the mean of those values over its users. It ships the arm with the highest mean.
- **Declared comparison.** Ranker 2 minus ranker 1, the challenger's re-rank against the champion, written in the replay design before any run. Its 95% interval is the difference of the two arms' means ± 1.96 x sqrt(s_1² / n_1 + s_2² / n_2), with s the SD of an arm's per-user values and n its users: lab 25's unpooled arithmetic, with the user, not the visit, as the independent unit. For contrast only, the script also prints the half-width with each visit as a unit, which treats one user's visits as independent.
- **Top two.** The two arms with the highest per-user means, picked after the run. Their difference on the same replay is biased up by the pick, so record it with no interval. Their interval comes from a fresh replay at seed 1,000 + S: a new salt, new visits and new clicks.
- **Bandit.** Thompson sampling over the 4 rankers, one Beta(1, 1) per ranker on its synthetic clicks, choosing per visit, on the same 200,000 visits.
- **Regret against the best ranker.** The sum over visits of the best ranker's true value minus the true value of the ranker that served the visit, divided by 1,000: synthetic clicks. It is a descriptive replay metric only: it carries no interval, so the seed reruns decide whether a gap is real. A recorded variant runs rankers 1 and 2 only, its A/B arm the same hash mod 2.
- **ECS (effective catalogue size).** Gomez-Uribe and Hunt 2015, Appendix A, on hours streamed there and on impressions here. Sort titles by impressions, most first, with s_i the share of the i-th title: ECS = 2 x (the sum over i of i x s_i) minus 1. It is 1 when one title takes every impression, and N when N titles share them equally. Recorded for 4 policies, each over its 500,000 impressions: candidate 1 always, the oracle, and the two exploration policies.
- **Concentration (recorded).** The percent of impressions on the 10 titles with the highest rating count in H.

## 2. Setup (before the session)

```
$ source ~/.venvs/ml/bin/activate
$ cd ml-learning/capstones/d-recommendations-bandits
$ python scripts/d4_ranking_stage_replay.py --download
$ python scripts/d4_ranking_stage_replay.py --smoke
```

`--download` only checks that `split.npz`, `world.npz`, `history.npz` and `challenger.npz` exist, and prints their paths. `--smoke` runs 1% of each full run's visits and prints `smoke.loop_s`. Over 3 s is a conservative warning (100 x 3 s is 5 minutes of loops, and at 3.6 s the loops alone would fill the 6-minute cap): fix the loop first.

## 3. Ranking-stage replay (0:04, 5 min)

Why: at the ranking stage a bandit chooses among a model's candidates, so its exploration, its experiment and the spread of what it shows are all priced in clicks on the same visits.

The replay design, written before the session, no AI. This is the prompt the AI built the script from:

1. The candidates, the exploration policy and its catalogue version, and the recall ceiling.
2. The 4 rankers; the A/B test's user hash, its declared comparison with the interval over users, and the fresh seed for the top two; the bandit; and the regret they share, descriptive only.
3. The ECS, written yourself as `ecs(impressions)` from its Term, no AI, and the RESULT contract: every name in the Record table, with `labkit.start(lab=56)`.

```
$ python scripts/d4_ranking_stage_replay.py --baseline
(paste your RESULT lines)
```

Prediction vs actual, one sentence for each of P1 to P3. There is no reference run.

## 4. The plan in numbers (0:09, 4 min, no AI)

Write in `design-doc.md`, in note form:

- **Exploration budget.** P1 and its catalogue version, each times an assumed 10 M home-page visits a day [assumed], in clicks a day. Then say which challengers each scope lets D3's estimators value: a challenger whose pick sits outside the 20 candidates has propensity 0 there, your D3 P3.
- **Bandit or A/B test.** Size a 2-arm A/B test of the challenger against the champion with your lab 25 `n_per_arm()`, at the champion's synthetic click rate and the smallest lift worth shipping, in visits per arm and in days at the assumed traffic. A click matures inside the visit, so add no maturity wait (lab 25 added 120 days for fraud). `n_per_arm()` counts independent units, and a production test holds each user in one arm, as your replay did: say in one line why that visit count is a floor, from your two half-widths. Then one line each: what the A/B test gives that the bandit does not, and what the bandit needs to keep up with drift (Lattimore and Szepesvári, ch 31, in the README's [Sources](README.md#sources)).
- **Monitoring.** 3 to 5 signals as `signal | threshold | window | who it pages`. One of them is the share of impressions logged with a propensity, which must be 100%.

## 5. Mock (0:13, 45 min, timed, closed book, no AI)

- Open only the [ladder](README.md#the-mock-design-the-recommendations-for-a-streaming-home-page): the 8 probes. Close every other file and the AI chat. Start a 45-minute timer.
- Write `mock-attempt.md` in this folder. No repo HLD covers a streaming home page, so the attempt lives here, not in `hld/`.
- First 5 minutes: the one-line answer and your framing line. Then about 5 minutes per probe, with numbers from your runs (marked synthetic) and from memory. Note the minute each probe starts.
- Stop at 45 minutes, mid-sentence if need be.

## 6. Self-grade (within 24 hours, 25 min)

1. **No AI, 10 min.** Under the attempt, grade it on the six criteria of root [`CLAUDE.md`](../../../CLAUDE.md#7-staff-level-bar-calibrate-answers-to-this) §7, one row each: `| Criterion | Where in my answer | hit, partial or miss |`. The six: the simplest design and what it refused to build; failure modes and blast radius; migration with zero downtime and a rollback; operability (what pages at 3 am, the SLO, service level objective); cost in dollars and engineer-time, plus team boundaries; the trade-off made explicit. Use the table under the ladder to find where each probe is answered. Name the weakest criterion.
2. **With the AI, 5 min.** Ask it to critique the attempt against the same six. It names the gaps and never rewrites your answer ([`../../CLAUDE.md`](../../CLAUDE.md#6-hints-and-critique) §6).
3. **No AI, 10 min.** Finish `design-doc.md`: §8 Serving at the ranking stage, §9 Bandit or A/B test, and §10 Monitoring and guardrails. Then write the 5 soundbites, each with the section of [Repo HLD it maps to](README.md#repo-hld-it-maps-to) it was checked against.

## 7. What I learned

Five sentences on what the mock exposed, edited after the AI's critique.

## 8. Interview soundbite (the card written at 0:58)

> One or two sentences only someone who ran this would say.

Framing: decision ___ | prediction time ___ | label and its maturity ___ | offline metric ___ | online metric ___ | guardrail ___

Staff follow-up (migration): how do you move the exploration slot from a uniform draw to a bandit without losing an unbiased replay log, and how do you roll back? Answer in 2 sentences from [§7](../../../hld/news-aggregator/deep-dives/ranking-and-cold-start.md#7-cold-start-and-moving-to-a-learned-model) of the ranking deep dive (LinUCB as v2 for the slot, and the rollout) and the Exploration row of its [§10](../../../hld/news-aggregator/deep-dives/ranking-and-cold-start.md#10-trade-offs).

## 9. Close (0:58, 2 min)

The AI drafts card `D4-D` (a symptom and the first check) from your replay. Edit or replace it. The question goes to `../../quiz-bank.md`, the key to `../../answers/quiz-key.md`, citing your RESULT line. Set Status here and in the [README](README.md#sessions). Capstone D is done when `design-doc.md`, its 5 soundbites and the graded `mock-attempt.md` all exist.

## Record

Suggested names: if your RESULT contract renames them, edit this table first. Paste, do not type.

| Metric | Your run | Hardware (the script's HW line) | Captured by (script or learner) |
|---|---|---|---|
| `baseline.recall_at_20` (share of users whose oracle title is among their 20 candidates) | | | script |
| `baseline.ctr_candidate1` and `baseline.ctr_best_candidate` (expected clicks per 1,000 visits: candidate 1 always, and each user's best of the 20) | | | script |
| `P1.explore_cost` (expected clicks per 1,000 visits given up, ε = 0.05 among the 20) | | | script |
| `baseline.explore_cost_catalogue` (the same, ε = 0.05 over all 200 titles) | | | script |
| `baseline.ranker_value_1` to `baseline.ranker_value_4` (true clicks per 1,000 visits) | | | script |
| `baseline.ab_users_min` and `baseline.ab_users_max` (users in the smallest and the largest of the 4 A/B arms) | | | script |
| `baseline.ab_regret` and `baseline.bandit_regret` (synthetic clicks over 200,000 visits, descriptive) | | | script |
| `P2.ab_minus_bandit` (synthetic clicks) | | | script |
| `baseline.ab_winner_correct` (true when the arm with the highest per-user mean is the best ranker) and `baseline.bandit_best_share_last_10k` (percent of the bandit's last 10,000 visits on the best ranker) | | | script |
| `baseline.ab_diff_2v1`, `baseline.ab_diff_2v1_ci95_low` and `baseline.ab_diff_2v1_ci95_high` (the declared comparison, ranker 2 minus ranker 1, per-user means, clicks per 1,000 visits), and `baseline.ab_diff_2v1_covers` (true when the interval holds ranker_value_2 minus ranker_value_1) | | | script |
| `baseline.ab_halfwidth_user` and `baseline.ab_halfwidth_visit` (the declared comparison's 95% half-width with the user and with the visit as the unit, clicks per 1,000 visits; only the first is valid) | | | script |
| `baseline.ab_top2` (the two arms with the highest per-user means, best first) and `baseline.ab_top2_diff` (their difference on the same replay, no interval) | | | script |
| `baseline.ab_top2_diff_fresh`, `baseline.ab_top2_ci95_low_fresh` and `baseline.ab_top2_ci95_high_fresh` (the same two arms on the fresh replay at seed 1,000 + S, clicks per 1,000 visits) | | | script |
| `baseline.ab_minus_bandit_2arm` (rankers 1 and 2 only) | | | script |
| `baseline.ecs_candidate1`, `baseline.ecs_oracle`, `baseline.ecs_explore_candidates` and `baseline.ecs_explore_catalogue` (titles; the last two are ε = 0.05 among the 20 candidates and ε = 0.05 over all 200 titles) | | | script |
| `P3.ecs_gap` (candidate 1 minus the oracle, titles) | | | script |
| `baseline.top10_share_candidate1` and `baseline.top10_share_oracle` (percent of impressions) | | | script |
| Your D3 IPS widths at ε = 0.01, 0.05, 0.1 and 0.3, and the unsupported share | | | learner |
| The A/B sizing: visits per arm, days at the assumed traffic, and the line on why that visit count is a floor | | | learner |
| Mock: probes answered in 45 minutes, and the minute each started | | | learner |
| Self-grade: hits of 6, and the weakest criterion | | | learner |
