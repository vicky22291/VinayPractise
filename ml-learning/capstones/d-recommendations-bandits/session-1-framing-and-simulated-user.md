# D1. Framing and a simulated user: a synthetic click world, three baselines and regret

> Goal: after this I can frame a one-title home-page slot in 6 fields, split 100,000 MovieLens ratings per user into a world half and a policy half, turn the world half into a synthetic click probability for 943 users x 200 titles, and report clicks per 1,000 visits and cumulative regret for random, most popular, the oracle and greedy on a history model that never saw the world's half, over 500,000 synthetic visits. (No result values anywhere in this file. Capstones have no reference run and no answers file: your run is the answer.)

**Capstone:** [D, recommendations with bandits](README.md), session 1 of 4, labkit id 53. **Level:** B (see `ml-learning/CLAUDE.md`). **Output style:** Explanatory
**Builds on:** labs 05 (MovieLens 100K, and baselines before any model) and 33 (DotProductBias in plain PyTorch)
**Dataset:** MovieLens 100K, 100,000 ratings by 943 users, 1,682 movie ids under 1,664 titles, 4.92 MB zip, GroupLens research use only ([Data](README.md#data)). From one half of it, a synthetic click world over the 200 most-rated titles; from the other half, every policy-side model
**Runs on:** cpu. **Lane:** light. **Compute:** no reference run; 2 measured runs, each capped at 6 min. Precomputed steps: none
**Needs:** base install only
**Before the session:** the AI writes the `--download` and `--smoke` modes of `scripts/d1_framing_and_simulated_user.py` from the README's Data section; you run `--download` once (it reuses lab 05's zip in `~/ml-data/ml-100k/`, or fetches the 4.92 MB).
**Interview question:** You have 100,000 ratings and must pick one title per home-page visit: what is the baseline, what is the ceiling, and how do you measure the gap before anything is live?
**Repo link:** [`hld/news-aggregator/deep-dives/ranking-and-cold-start.md`, §10 Trade-offs](../../../hld/news-aggregator/deep-dives/ranking-and-cold-start.md#10-trade-offs) (a formula before any model, and what it refused); [same file, §11 What the interviewer probes next](../../../hld/news-aggregator/deep-dives/ranking-and-cold-start.md#11-what-the-interviewer-probes-next) (evolve from a popularity baseline)
**Captured by the script:** P1 to P3 and every Record row. **Human steps:** the framing sprint, the design and the write-up
**Status:** todo

## 0. Framing (0:00, 7 min, no AI except as the interviewer)

**0:00 to 0:05, the framing sprint.** Tell the AI "play the interviewer for a streaming home page recommendation". Then propose and confirm, by the rule in [`scoping-drills/README.md`](../../../scoping-drills/README.md#3-drill-2-propose-and-confirm) §3: state each assumption, attach its consequence, invite correction, and ask at most one open question. Cover:

- What one visit decides. Netflix reports "about 40 rows on each homepage ... and up to 75 videos per row" ([Sources](README.md#sources)). This capstone fills one slot with one title. Say what that leaves out.
- The label and when it matures. Here it is a synthetic click inside the visit. On a real service it is a play, or a play of some minimum length. Say what a click rewards that a play would not.
- The scale, the time budget per page, and the failure default when the ranker is down.

The AI confirms or corrects each assumption in one line. It never proposes a metric, a policy or an exploration rate.

**0:05 to 0:07, the framing line.** One value per field. It opens `design-doc.md` at 0:42.

decision ___ | prediction time ___ | label and its maturity ___ | offline metric ___ | online metric ___ | guardrail ___

D2 to D4 keep this line. D4 turns its online metric and guardrail into thresholds.

## 1. Predict (0:07, 5 min, no AI)

Write each row here and in `../../prediction-log.md` (Lab `D1`) before anything runs. Rates are synthetic clicks per 1,000 visits.

| Step | Question | Kind | Prediction | 80% range or confidence |
|---|---|---|---|---|
| P1 | Random: a uniform title from the 200 at every visit, 500,000 synthetic visits, seed 0. Clicks per 1,000 visits | num | | |
| P2 | Most popular: the title with the highest rating count in H (Terms) at every visit, the same visits. Its clicks per 1,000 visits as a percent of the oracle's | num | | |
| P3 | Greedy on the history model (lab 33's config trained on H1, which shares no rating with the world's W), the same visits: clicks per 1,000 visits minus most popular's. Up, down or same, plus a size range | dir | | |

Terms, fixed so sessions 2 to 4 compare with this one:

- **Items and catalogue.** The title is the item, as in labs 05 and 33. The catalogue is the 200 most-rated titles over all 100,000 ratings, in that order, most first, ties broken by title in string order. Every policy picks from it.
- **Split (fixed, whatever the seed).** One `numpy.random.default_rng(0)` shuffles each user's ratings, in `u.data` row order, users in id order. The first half of each user's shuffled ratings, rounded down, is W, and the rest is H. W trains the world and nothing else. H is the policy side: every policy-side model learns from it, and none ever sees W. Then every rating of the 20 new titles leaves H, and each user's remaining H ratings, still in shuffled order, split the same way: the first half, rounded down, is H1 for the history model, and the rest is H2 for D3's challenger. The script asserts that W, H1 and H2 share no rating and that H1 and H2 hold no rating of a new title.
- **New titles.** Ranks 10, 20, ..., 200 of the catalogue: 20 titles spread over its popularity range. No policy-side model or cluster sees a rating of them, while the world, fit on W, still sets their click probabilities. They are new to the policies, not new to the world. Every model-based pick (greedy on the history model, D3's challenger, D4's candidates) ranges over the other 180 titles: a model holds no trained row for a title it never saw. D2 also hides them until visit 250,000.
- **Rating count.** For every policy that sorts by popularity: a title's ratings in H, so 0 for a new title, with ties going to the earlier title in the catalogue order. Only the catalogue and its order use all 100,000 ratings, a fixed setup that no policy learns from.
- **The world (synthetic truth).** Lab 33's P1 config, with every setting its section 3 lists (50 factors, weight decay 0.1, 5 epochs, AdamW on a one-cycle schedule to 5e-3, batch 64, every table from N(0, 0.01), sigmoid_range 0 to 5.5), trained on W only at seed 0. r_hat(u, m) is its predicted rating.
- **Coupling that remains.** W and H share no rating, but they are the same 943 users' tastes, so a policy that learns H well has learned the users the world was fit on. Every number in this capstone holds inside this MovieLens-derived simulator, and your §3 says so in one sentence.
- **Synthetic click probability.** p(u, m) = sigmoid(2 x (r_hat(u, m) - 5)) for each of the 943 users and 200 titles. A title predicted at 5 stars is clicked half the time, and each star lower divides the odds of a click by e^2, about 7.4. No real click is behind any p.
- **Fit once.** `--baseline` at seed 0 fits the world and saves it. Every later run, at any seed, reads the saved split and world: `--seed` changes the visits, the clicks and the policies' own draws, never the split or the world.
- **The stream.** `rng = numpy.random.default_rng(seed)` draws 500,000 users uniformly from the 943, then 500,000 uniform numbers, before any policy draws. A visit shows one title, and its synthetic click is 1 when its uniform number is below p(user, title). Every policy sees the same users in the same order with the same numbers.
- **Policies.** Random: a uniform title from the 200, drawn from its own generator, `numpy.random.default_rng([seed, 1])`. Most popular: the title with the highest rating count in H, for everyone. Oracle: the title with the highest p for the visiting user, from all 200. It reads the world, which no real system can.
- **History model (the change).** The same config trained on H1 at seed 0: the model a platform trains on its own logs. p_hat(u, m) applies the same link to its predicted rating. Greedy on it shows each user the title with the highest p_hat among the 180 that are not new.
- **Clicks per 1,000 visits.** 1,000 x synthetic clicks / visits. The expected version puts p in place of each click, so it carries no click noise.
- **Cumulative regret.** At visit T: the sum over the first T visits of p(user, the oracle's title) minus p(user, the policy's title), in synthetic clicks. Checkpoints at 10,000, 100,000 and 500,000 visits, and every curve in one plot, `~/ml-data/capstones/d/d1-regret-seed<S>.png`.
- **Saved for later.** `--download` saves the split to `split.npz`: the row ids of W, H1 and H2, the 20 new titles, and each catalogue title's rating count in H. At seed 0 only, `--baseline` saves the catalogue with its rating counts, r_hat and p (943 x 200) to `world.npz`, and `--change` saves p_hat and the history model's 943 user rows to `history.npz`. All three go to `~/ml-data/capstones/d/`.

## 2. Setup (before the session)

```
$ source ~/.venvs/ml/bin/activate
$ cd ml-learning/capstones/d-recommendations-bandits
$ python scripts/d1_framing_and_simulated_user.py --download
$ python scripts/d1_framing_and_simulated_user.py --smoke
```

There is no script until the AI writes one. Before the session, ask it for `--download` and `--smoke` only, from the README's Data section and the Split and New titles terms above: reuse lab 05's zip or fetch it with its size, extract it, build the 200-title catalogue and the split, save `split.npz`, and print paths, sizes, ratings, users, titles, the catalogue size and its smallest rating count, the sizes of W, H1 and H2, the new titles' ratings removed from H, and the fewest ratings any user keeps in H1 and in H2, never a click rate. `--smoke` fits each model for 1 epoch on 10,000 ratings of its own part, W or H1, and runs 5,000 visits per policy.

## 3. Baseline (0:12, 15 min)

Why: a recommender is judged against the cheapest policies and against its ceiling, so measure random, most popular and the oracle on one stream before anything learns.

You write first, in this file, no AI (about 5 min). This is the prompt the AI builds from:

1. The split and the world: what W, H1 and H2 hold and why no policy-side model may see W, the link from a predicted rating to a click probability, why it is fit once at seed 0, and what `--seed` may change.
2. The stream, the three policies, and both metrics with their checkpoints.
3. The RESULT contract: every name in the Record table, the mode that prints it, and its unit. Each mode prints only its own rows.

Then write `cumulative_regret(p, users, picks, best)` yourself, no AI (about 2 min), from the Cumulative regret term: one running sum, one value per visit. The AI then writes `--baseline` and `--change` from your prompt, with `labkit.start(lab=53)`. Annotate each AI block with one line before the first run.

```
$ python scripts/d1_framing_and_simulated_user.py --smoke
$ python scripts/d1_framing_and_simulated_user.py --baseline
(paste your RESULT lines)
```

Prediction vs actual, one sentence each for P1 and P2. There is no reference run: the AI fills Actual and Hit in `../../prediction-log.md` from your pasted lines.

## 4. Change one thing (0:27, 15 min; the run finishes by 0:40)

Change: greedy on the history model replaces popularity. The split, the world, the catalogue and the stream stay fixed. P3 is logged above.

Why: a platform never sees the world, only its own logs, so its first real policy is the argmax of a model trained on them. H1 plays those logs, and it shares no rating with W.

```
$ python scripts/d1_framing_and_simulated_user.py --change
(paste your RESULT lines)
```

Prediction vs actual, one sentence.

## 5. Write-up (0:42, 15 min, no AI)

- **Explain-back (5 min).** Five sentences for a smart engineer new to ML. Then ask the AI for the weakest claim, not a rewrite.
- **Deliverable (10 min).** Start `design-doc.md` in this folder: the framing line, then §1 Framing (the slot, the label and when it matures, the failure default), §2 Metrics (clicks per 1,000 visits and regret, the online metric, the guardrail) and §3 The simulator (the split, the link and the fit-once rule; the coupling that remains, in one plain sentence: W and H are the same 943 users' tastes, so every result holds inside this MovieLens-derived simulator; and two things this world cannot tell you about a real home page). At most 4 lines each.

## 6. What I learned

The five explain-back sentences, edited after the AI's question.

## 7. Interview soundbite (the card written at 0:57)

> One or two sentences only someone who ran this would say.

Framing: decision ___ | prediction time ___ | label and its maturity ___ | offline metric ___ | online metric ___ | guardrail ___

Staff follow-up (simplest design): what is the simplest home-page recommender you would ship first, and what did you refuse to build? Answer in 2 sentences from the repo link: the v1 ranker row of §10 and its Refused row.

## 8. Close (0:57, 3 min)

The AI drafts card `D1-T` (a variant you did not run, or the payments version) from your run. Edit or replace it. The question goes to `../../quiz-bank.md`, the key to `../../answers/quiz-key.md`, citing your RESULT line. Set Status here and in the [README](README.md#sessions).

## Record

Suggested names: if your RESULT contract renames them, edit this table first. Paste, do not type.

| Metric | Your run | Hardware (the script's HW line) | Captured by (script or learner) |
|---|---|---|---|
| Ratings, users, titles, the catalogue size and its smallest rating count (from `--download`) | | | learner |
| The split: W, H1 and H2 sizes, the new titles' ratings removed from H, and the fewest ratings any user keeps in H1 and in H2 (from `--download`) | | | learner |
| `baseline.world_train_rmse` (the world model on W, its own ratings, stars) | | | script |
| `baseline.p_mean` (mean synthetic p over the 943 x 200 pairs) | | | script |
| `P1.ctr_random` (clicks per 1,000 visits) | | | script |
| `baseline.ctr_popular` and `baseline.ctr_oracle` (clicks per 1,000 visits) | | | script |
| `baseline.expected_ctr_random`, `baseline.expected_ctr_popular` and `baseline.expected_ctr_oracle` (from p) | | | script |
| `P2.popular_pct_of_oracle` (percent) | | | script |
| `baseline.regret_random_<T>` and `baseline.regret_popular_<T>` at T = 10k, 100k and 500k (synthetic clicks) | | | script |
| `baseline.oracle_titles` (distinct titles the oracle shows across the 943 users) | | | script |
| `baseline.fit_s` (world fit seconds, M4 Pro, cpu) | | | script |
| `change.history_heldout_rmse` (the history model on H2, policy-side ratings it never saw, stars) | | | script |
| `change.ctr_history` and `change.expected_ctr_history` (clicks per 1,000 visits) | | | script |
| `P3.history_minus_popular` (clicks per 1,000 visits) | | | script |
| `change.regret_history_<T>` at T = 10k, 100k and 500k | | | script |
| `change.top1_agreement` (share of users whose history pick is the oracle's) | | | script |
| `change.history_titles` (distinct titles greedy on the history model shows) | | | script |
