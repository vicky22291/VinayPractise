# 20. Training-serving skew replay: two code paths, one feature: reference answers

> Spoilers. The AI opens one block at a time, only after that step's prediction row exists and the learner pasted their own RESULT lines, or after 'debrief 20'.

- **HW:** `HW chip='Apple M4 Pro' cpu=14 gpu=20 mem_gib=24 macos=26.5.1 python=3.13.7 torch=2.14.1 device=cpu`
- **Seeds:** 0, 1 and 2 for every step (light lane). The seed draws the 200,000 queries. LightGBM at these settings has no random step, so the query sample is the only source of spread.
- **Reference script:** `answers/20_training_serving_skew_ref.py` (sha256 prefix `381054b17e537fa6`), run from `m4-production-ml-payments/`. It imports the provided `m4-production-ml-payments/scripts/serving_features.py` for `--change`. Raw seed-0 output: `answers/20-training-serving-skew.out`.
- **Runs and wall times (seed 0 / 1 / 2):** baseline 26.1 / 16.9 / 7.7 s, change 53.5 / 34.8 / 45.1 s, break 174.9 / 176.9 / 146.9 s. All 9 runs shared the CPU with other build jobs (see Build notes), so these are upper bounds.
- **Tolerance rule:** tol = spread (max - min) over seeds 0, 1, 2 (from the `.json`). A learner's own run at seed 0 should match the seed-0 value within tol.

<details><summary>P1. Test MAE of LightGBM (300 trees, seed 0) on last-hour count, hour, weekday and zone, batch train and batch serve</summary>

**Answer:** 22.4356 pickups at seed 0, tolerance 0.2053. Seeds 1 and 2: 22.4213 and 22.2303.

```
RESULT P1.mae=22.4356 unit=pickups seed=0
```

**Why.** The test queries average 174.032 pickups in the next hour (`break.test_mean_target`), so the error is about 13% of the mean (22.4356 / 174.032). Next-hour demand in a zone tracks last-hour demand closely, and hour, weekday and zone correct for the daily cycle. Part of what is left is count noise that no model removes: a Poisson count near 174 has a standard deviation near 13 (the square root of 174), so even a model that knew each zone's true rate would still miss by several pickups on average.

**Common wrong prediction:** single digits. That pictures an average zone-hour across all zones, most of them quiet. Queries here are a pickup-weighted sample, so the typical query sits in a busy zone at a busy hour, where counts and errors are both large.

</details>

<details><summary>P2. The same model, test features from the shipped serving path: MAE direction and size as the ratio P2 / P1</summary>

**Answer:** up, by a ratio of 6.66929 at seed 0 (`P2.mae` 149.63 against `P1.mae` 22.4356). Tolerance 0.07557 on the ratio and 1.79 on the MAE. Seeds 1 and 2: ratio 6.59372 and 6.65497, MAE 147.84 and 147.942. Effect `P2.mae` minus `P1.mae`, mean over the three seeds: 126.108 pickups, far above 2x the spread.

```
RESULT P2.mae=149.63 unit=pickups seed=0
RESULT P2.mae_ratio=6.66929 unit=ratio seed=0
```

**Why.** The shipped serving path returned 0 for every one of the 200,000 requests (`break.serving_zero_share` = 1). The batch-trained model reads 0 as "nothing happened here in the last hour" and predicts a quiet zone: its mean prediction on the served inputs is 24.4992 (`break.mean_prediction_shipped`) against a mean target of 174.032. When almost every prediction is too low, the MAE is close to the mean target minus the mean prediction: 174.032 - 24.4992 = 149.533, next to the measured 149.63. Nothing crashes and nothing warns: the inputs are valid integers and the model file is the same, which is why skew stays silent offline.

**Common wrong prediction:** up by 10 to 50%. That pictures skew as a noisy copy of the feature. A clock error on one side of a window comparison does not add noise: it moves the window to where there is no data yet.

</details>

<details><summary>P3. FIND-IT: share of the 200,000 queries whose last-hour count differs between batch_counts() and the shipped serving_counts()</summary>

**Answer:** 0.99167 at seed 0, tolerance 0.000225. Seeds 1 and 2: 0.991895 and 0.991775.

```
RESULT P3.mismatch_rate=0.99167 unit=fraction seed=0
```

**Why.** The serving path served 0 everywhere, and the batch count is 0 for only 0.00833 of the queries (`break.batch_zero_share`). So the mismatch rate is exactly the share of queries with at least one pickup in the hour before: 1 - 0.00833 = 0.99167. A mismatch rate counts rows that differ, not by how much: a dead feature and an off-by-one window edge both score near 1 (see the debrief).

**Common wrong prediction:** a few percent. That pictures a boundary bug that only touches rows near the window edges. Each planted difference, on its own, changes nearly every row.

</details>

<details><summary>Rebuild check</summary>

- Stub: `answers/rebuild/stubs/20_skew_parity.py`. The AI copies it into `m4-production-ml-payments/rebuild/` at 0:47. Solution: `answers/rebuild/20_skew_parity.py`.
- `rebuildcheck` verdict: stub fails as it should (exit 1, NotImplementedError), solution passes (exit 0, `check: PASS`), `REBUILDCHECK OK`.
- `check()` draws 20,000 synthetic pickup times over 7 days, takes 1,000 of them as queries (so every query is itself a pickup) and adds a pickup exactly 1 h before every 10th query. Both counts must equal a brute-force numpy count of [t - 1 h, t), and their mismatch rate must be 0.0. At build time, a right-closed window, a window closed at both ends, a left-open window and a 5 h shift each failed it.

</details>

<details><summary>Find-it debrief</summary>

Both planted differences live in `scripts/serving_features.py`, uncommented.

1. **The clock (line 25).** `ZoneWindows.last_hour()` converts the request time with `tz_localize("America/New_York").tz_convert("UTC").tz_localize(None)`, which adds 5 h in January, while the pickup times from the stream stay on the trip file's local clock. The window becomes (t + 4 h, t + 5 h] on the pickups' clock. The store has only seen pickups up to t, so the eviction loop empties the zone's deque and every request gets 0. A live service would get the same 0: those pickups have not happened yet. **Fix:** compare on one clock. Drop the conversion, or convert both sides.
2. **The window edges (lines 42 and 27).** The window is (t - 1 h, t] where the definition says [t - 1 h, t). In `serving_counts()`, `time <= q_time` delivers the pickups at the request's own second before answering, so each query counts its own pickup (plus any other pickup in that second). In `last_hour()`, `window[0] <= now - HOUR` drops a pickup exactly 1 h old. **Fix:** `<` in both places.

Each difference on its own (reference `--break`, seed 0):

| Serving path | Mismatch rate vs batch | MAE, batch-trained model |
|---|---|---|
| As shipped | 0.99167 (`P3.mismatch_rate`) | 149.63 (`P2.mae`) |
| Clock fixed, both edges as shipped | 0.963035 | 22.4144 (`break.mae_fix_clock`) |
| Both edges fixed, clock as shipped | 0.99167 | not measured: every count is still 0, as shipped |
| Clock and right edge fixed, left edge as shipped | 0.0423 | not measured |
| All fixed | 0 | 22.4356 (`break.mae_fixed`), equal to P1 |

What the table teaches:

- **One fix is not the fix.** Fixing the edges alone leaves the mismatch rate where it was (0.99167). Fixing the clock alone leaves it at 0.963035. Keep going until the mismatch is exactly 0, not until it improves.
- **Mismatch rate and MAE measure different things.** The window edges alone mismatch 0.963035 of rows, yet move the MAE by a mean of -0.0175333 pickups over the three seeds, inside the spread of 0.2134. The shift is not the same on every row. Each row gains the pickups at t (the query's own, plus any in the same second) and loses the pickups exactly at t - 1 h. That is +1 when the query's pickup is alone at t and nothing is exactly 1 h old, more when other pickups share its second, and less, 0 included, when pickups exactly 1 h old drop out. The rows where the two edges cancel are the ones the 0.963035 does not count. A shift of that size is small next to counts near 174, so a tree model's predictions barely move. Watch both on a skew dashboard: one counts rows, the other weighs damage.
- **A 20-row comparison can miss the left edge.** With the clock and the right edge fixed, 0.0423 of rows still differ, from pickups exactly 1 h old to the second. That is fewer than 1 row in 20, so a 20-row sample often shows none of them. The full-population mismatch rate catches it.

**The honest numbers.** After all three edits, the serving path equals the batch path on every query (`break.mismatch_rate_fixed` = 0 at all three seeds). Batch train with serving serve then gives 22.4356, exactly P1. A learner's own fixed `--change` should print `P2.mae` equal to their `P1.mae` and a ratio of 1.

**The third combination: serving train, serving serve** (Rules of ML #29, train on the feature values the serving path logged). `break.mae_logged` is 28.2738 at seed 0, tolerance 0.2349 (seeds 1 and 2: 28.0389 and 28.2555).

```
RESULT break.mae_logged=28.2738 unit=pickups seed=0
```

Training on the logged values removes the skew by construction: 28.2738 against 149.63 for the skewed pair (effect -120.281 pickups, mean over seeds). It does not bring the feature back. The logged count is 0 on every row, so the model learns from hour, weekday and zone only and pays 5.827 pickups over P1 (mean over seeds, spread 0.2349). Logging the served vector fixes skew; only a parity check (Rules of ML #37, measure training-serving skew) finds that a feature is broken. This is the `solution.md` §4.3 "Chosen" rung plus its skew test: backfill, then compare against the logged values.

**The payments version.** "Authorizations on this card in the last hour" written once in Spark and once in the scoring service has the same two failure points: the clock (UTC event time against a local or merchant time zone) and the window edge (does the current authorization count itself?).

</details>

<details><summary>Card drafts</summary>

| ID | Lab | Type | Question |
|---|---|---|---|
| 20-M | 20 | M | Why does training on the feature vector logged at serving time remove training-serving skew by construction, and what can it not fix? |
| 20-N | 20 | N | In lab 20 the shipped serving path returned 0 for every request. What share of the 200,000 queries mismatched the batch path, and why is that share not exactly 1? |
| 20-D | 20 | D | Offline MAE is fine, production MAE is several times worse, and the serving log shows a velocity feature at 0 on every request. What do you check first, and how? |

Keys, 1 to 3 must-mention items each:

- **20-M:** (1) training and serving then read the same values, so no second code path can disagree; (2) it cannot repair a feature the serving path computes wrongly: the model learns around it (lab 20: 28.2738 against P1's 22.4356, with a dead feature); (3) keep a parity check, the mismatch rate between a recomputation and the log, to find broken features.
- **20-N:** (1) 0.99167 at seed 0; (2) it equals the share of queries with at least one pickup in the hour before, since the batch count is 0 for 0.00833 of them; (3) the rate counts rows that differ, not how much they differ.
- **20-D:** (1) compare the two paths row by row on the same requests: the mismatch rate, then a few rows side by side; (2) check the clock on each side of the window comparison: a UTC request time against local event times puts the window in the future, where a live store has nothing; (3) then the window edges: does the current event count itself?

If this close needs a T card instead of the D: "A card-velocity feature counts authorizations in [t - 1 h, t) in the batch job and in (t - 1 h, t] in the scoring service. Which rows differ, and would you expect the model's offline metric to move much?" Key: (1) nearly every row: the scoring service adds the current authorization (and any others at the same instant) and drops any exactly 1 h old, so a row matches only where the two cancel (lab 20: 0.963035 of rows differ from the edges alone); (2) the metric barely moves: the shift varies by row, the events at t minus those exactly at t - 1 h, but it is small next to typical counts (lab 20: a mean MAE change of -0.0175333 pickups, inside the spread); (3) a threshold rule such as "more than 5 in an hour" flips on every row the shift carries across 5, mostly firing early because the current authorization counts itself, so rules feel it more than the model.

</details>

<details><summary>Build notes</summary>

- **Knob changes:** none. Every effect the lab teaches as real exceeded 2x the seed spread on the first configuration (effects in the `.json`, means over seeds 0 to 2): `P2.mae` minus `P1.mae` 126.108 (spread 1.79); `P3.mismatch_rate` minus `break.mismatch_rate_fixed` 0.99178 (spread 0.000225); `break.mae_logged` minus `P2.mae` -120.281 (spread 1.79); `break.mae_logged` minus `P1.mae` 5.827 (spread 0.2349). `break.mae_fix_clock` minus `P1.mae` (-0.0175333, spread 0.2134) is the effect the lab teaches as small, reported with its spread and not inflated.
- **Precomputed steps:** none. The longest run, seed-1 `--break`, took 176.9 s under load, under the 6-minute cap.
- **Wall times:** the 9 reference runs behind the `.json` ran while other build jobs held the CPU (load average above 100). The first full round, at lower load and with fewer reveal lines in `--break`, took about 5 s, 14 s and 43 s for baseline, change and break. The lab header's Compute line rounds up the seed-0 times of the runs behind the `.json`, so it is an upper bound.
- **Replay semantics (the spec is silent; the simplest correct option).** The serving path is replayed as-of: the stream delivers pickups in time order up to each request, as a live service would see them, and only then does the request read its window. With the planted clock (+5 h), the window sits in the future, where a live store has no pickups, so the shipped feature is 0 on every request. A replay that let the serving code read the whole month would have counted pickups 4 to 5 h in the future, which no serving system can see, and the logged-value run would then train on future data.
- **The window edges.** The spec plants (t - 1 h, t]. In a deque replay that is two comparisons: the stream's `<=` (right edge, the own pickup) and the eviction's `<=` (left edge). The debrief treats them as one planted difference with two lines to fix, and `--break` shows each edge separately.
- **Choices where the spec is silent.** Target: pickups in [t, t + 1 h), the same count taken at t + 1 h, so the feature and target windows meet without overlap. Split: train on queries before 24 January 23:00 (a 1 h gap, so no training target reaches the test week), test on 25 to 31 January, lab 16's test week. Queries: 200,000 pickups with a full January hour before and after. Zones 264 and 265 ("Unknown", "Outside of NYC") and the 18 trips outside January are dropped. Model: `LGBMRegressor(n_estimators=300, random_state=seed, n_jobs=4, verbose=-1)` with the default objective (L2) and settings, zone as a pandas category. Two fits at one seed gave identical predictions, and seed 1 gave the same model as seed 0, so the seed acts only through the sample.
- **The 20 rows.** The spec's "compare the two paths on 20 rows" is built into the starter's `report()` contract: `--change` prints 20 seeded test rows side by side, so the learner's harness prints the same rows.
- **Reveal robustness.** The starter's `--break` prints one line, no reveal. The reference's `--break` computes every reveal line with `replay()`, a copy of `serving_counts()` with three switches (clock, right edge, left edge). It reads `serving_features.py` only in its last line, `break.mismatch_rate_your_fix`, inside a try block, so a half-finished edit cannot hide the lines above. At build time that file is as shipped, so the line equals `P3.mismatch_rate` at every seed. At build time, `replay()` with all switches on matched the provided file on all 200,000 seed-0 queries, and with all off it matched the batch path; the batch feature and the target matched a brute-force count on 300 random queries. The reveal therefore holds after the learner edits the provided file.
- **What the lab file states.** The Terms define the feature as the pickups in [t - 1 h, t), because P1 must be gradeable and the learner writes `batch_counts()` from it. That half-open interval fixes both endpoints: a pickup exactly 1 h old counts, and a pickup at t does not, so a query, itself a pickup at t, never counts itself. The Terms leave that consequence for the learner to work out, and they name no time zone: the spec's rebuild line says "in local time", and the lab file leaves those words out because they would point at the clock. The rebuild stub, whose docstring states both in words, stays in `answers/rebuild/stubs/` until 0:47.
- **Reveal lines beyond the spec's record:** the mismatch with each difference alone, the zero shares, the test mean target and the mean prediction on the shipped values, so the debrief can explain P2 and P3 with measured numbers.
- **Prototype comparison:** the spec gives no `[answers only]` prototype values for this lab, so there is nothing to compare.
- **Links:** the Concept link (`m4-production-ml-payments/README.md`, "Training-serving skew") and both Repo links resolve to existing headings. The module README's section points back to this lab's Terms for the definition and names neither planted difference.

</details>
