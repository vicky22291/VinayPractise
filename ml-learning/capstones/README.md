# Capstones

> One line: four 4-session projects that join a module's labs into one system, end to end. You write the design, the AI writes the code from it, and your own runs are the only numbers. No starter script, no reference run, no answers file.

| Capstone | When | Sessions | Data | Maps to |
|---|---|---|---|---|
| [A. Card-fraud model, end to end](a-card-fraud/README.md) | After M4 (lab 27) | [1](a-card-fraud/session-1-framing-and-baseline.md), [2](a-card-fraud/session-2-as-of-velocity-features.md), [3](a-card-fraud/session-3-delayed-labels-and-thresholds.md), [4](a-card-fraud/session-4-shadow-plan-and-mock.md) | IBM TabFormer, synthetic card payments (fallback: `paystream.py`, synthetic) | [`hld/payments-risk-decisioning/`](../../hld/payments-risk-decisioning/README.md) |
| [B. Ride-hailing demand and ETA](b-ride-demand-eta/README.md) | After M7 (lab 40) | [1](b-ride-demand-eta/session-1-zone-hour-demand.md), [2](b-ride-demand-eta/session-2-duration-residual.md), [3](b-ride-demand-eta/session-3-drift-january-vs-july.md), [4](b-ride-demand-eta/session-4-latency-and-serving-cost.md) | NYC TLC yellow taxi trips, January and July 2024 | [`hld/driver-hot-clusters/solution.md`](../../hld/driver-hot-clusters/solution.md) (demand only; no repo file covers ETA) |
| [C. Support triage with retrieval and a small LLM](c-support-triage/README.md) | After M7 (lab 40) | [1](c-support-triage/session-1-tfidf-and-confused-pairs.md), [2](c-support-triage/session-2-embedding-knn.md), [3](c-support-triage/session-3-llm-judge.md), [4](c-support-triage/session-4-lora-vs-few-shot.md) | BANKING77, 13,083 banking queries, 77 intents | [`hld/financial-ai-assistant/solution.md`](../../hld/financial-ai-assistant/solution.md) (the intent router) |
| [D. Recommendations with bandits](d-recommendations-bandits/README.md) | After M5 (lab 33) | [1](d-recommendations-bandits/session-1-framing-and-simulated-user.md), [2](d-recommendations-bandits/session-2-explore-vs-exploit.md), [3](d-recommendations-bandits/session-3-off-policy-evaluation.md), [4](d-recommendations-bandits/session-4-ranking-stage-and-mock.md) | MovieLens 100K, 100,000 ratings, and a synthetic click world fit on one half of them | [`hld/news-aggregator/deep-dives/ranking-and-cold-start.md`](../../hld/news-aggregator/deep-dives/ranking-and-cold-start.md) (the exploration slot; no repo file covers a streaming home page) |

## What a capstone is

- **4 sessions of 60 minutes.** Each session file follows the [lab template](../../templates/ml-lab-template.md) in spirit: a goal, what to do before the session, a predict table (P1 to P3), steps with empty `(paste your RESULT lines)` blocks, explain-back, what I learned, and a soundbite.
- **Level B, Explanatory output style** ([`../CLAUDE.md`](../CLAUDE.md#7-code-by-level) §7). Before any code exists you write the design: what varies, what is fixed, the repeats, the stop rule and the RESULT contract. The AI then writes the script from it, and you annotate each block with one line before the first run.
- **No reference runs and no answers.** Nothing in `answers/` covers a capstone, and nothing will. Your pasted RESULT lines are the result. The spoiler gate ([`../CLAUDE.md`](../CLAUDE.md#2-spoiler-gate) §2) still holds: the AI states, hints at or confirms no value, direction or size a row asks you to predict until that row is in [`../prediction-log.md`](../prediction-log.md). It has nothing stored to reveal, so "debrief" here means the AI critiques your write-up against the repo HLD.
- **Grading.** Hit uses only the range you wrote before the run, as in the labs. There is no seed spread from a reference run. Before the write-up calls an effect real, rerun that step at `--seed 1` and `--seed 2` after the session: an effect under 2x that spread is noise, and the write-up must call it noise.
- **Never put a capstone result in a memory file.** Memory loads into every later session.

## The 60-minute loop, adapted

The lab loop becomes four blocks: framing, baseline, one change, write-up.

| Clock | Block | Min | You | The AI |
|---|---|---|---|---|
| 0:00 | Framing | 7 | Session 1: a 5-minute framing sprint, then the 6-field framing line. Sessions 2 to 4: reread the line and write what this session changes in it | Plays the interviewer in the sprint, nothing else |
| 0:07 | Predict | 5 | P1 to P3, here and in `../prediction-log.md` | Nothing |
| 0:12 | Baseline | 15 | The design first (about 5 min), then annotate each block the AI wrote, `--smoke`, `--baseline`, paste | Writes the script from your design |
| 0:27 | Change one thing | 15 | One knob, `--change`, paste. The run finishes by 0:40 | Hints only, by the hint ladder |
| 0:42 | Write-up | 15 | Explain-back in 5 sentences, then this session's part of the deliverable | Silent; afterwards names the weakest claim |
| 0:57 | Close | 3 | Edit the card, answer the Staff follow-up, set Status | Drafts one card |

- **The framing sprint** follows the propose-and-confirm rule in [`scoping-drills/README.md`](../../scoping-drills/README.md#3-drill-2-propose-and-confirm) §3: state an assumption, attach its consequence, invite correction. Every capstone keeps one framing line: `decision | prediction time | label and its maturity | offline metric | online metric | guardrail`.
- **What the loop drops.** The retrieval opener (the weekly sweep in [`../quiz-bank.md`](../quiz-bank.md) keeps the cards moving), the break step (the change step carries the experiment), and the rebuild (you designed every function the script holds).
- **Writing the design early is allowed.** Write it the day before, and the AI may write the script then too, running `--smoke` only. You still annotate every block before 0:12.
- **Run caps.** Each run is capped at 6 minutes, and nothing runs after 0:42. If a run would pass 6 minutes, shrink the data with a seeded sample and say so in the Record table.
- **Session A4 is the exception.** It runs one shadow replay, writes the plan in numbers, then spends 0:13 to 0:58 on a timed 45-minute mock. Its self-grade takes 25 minutes within 24 hours.
- **Cards.** The AI drafts one card per session from your run: type T in sessions 1 and 3, D in sessions 2 and 4. The ID is the session, for example `A1-T`. Questions go to `../quiz-bank.md`, keys to `../answers/quiz-key.md`, and the key cites your own RESULT line.
- **Prediction log.** The Lab column holds the session, `A1` to `C4`.

## Scripts and data

- One script per session in the capstone's `scripts/` folder, created in that session: for example `capstones/a-card-fraud/scripts/a1_framing_and_baseline.py`. Run every mode from the capstone folder, as the labs do from their module folder.
- Each script imports [`../labkit.py`](../labkit.py) before numpy, as every lab script does, and calls `labkit.start(lab=NN)`. labkit takes a number, so the 16 sessions use ids 41 to 56: A1 to A4 are 41 to 44, B1 to B4 are 45 to 48, C1 to C4 are 49 to 52, D1 to D4 are 53 to 56. Each session then keeps its own `~/ml-data/runs/labNN/`.
- Modes: `--download`, `--smoke`, `--baseline` and `--change`, with `--seed S` (seed 0 by default). `--download` prints paths and sizes only. `--smoke` runs every mode on a seeded sample sized to finish in under 60 seconds and prints `SMOKE <name> ok`, never a value.
- Results print as `RESULT <step>.<name>=<value> unit=<unit> seed=<seed>` through `labkit.result()`. Timing lines add `device=`, `batch=`, `warmup=`, `n=` and `stat=median`.
- Data lives in `~/ml-data/` (TabFormer in `~/ml-data/tabformer/`, the trip files in `~/ml-data/tlc/`, BANKING77 in `~/ml-data/banking77/`). What one session saves for the next goes to `~/ml-data/capstones/a/`, `b/`, `c/` or `d/`, plots included. Nothing lands in the repo except your scripts and your markdown.
- Installs: A, B and D need the base install only. C adds `python -m pip install sentence-transformers==6.1.0 mlx==0.32.4 mlx-lm==0.32.2` and Ollama with `qwen2.5:7b`, all of which labs 12, 14, 15 and 40 already set up.

## When to do each

- **A after M4.** It needs every M4 lab (19 to 27) plus labs 03, 09 and 10. In the interview-track order it comes right after lab 27, with the timed mock. At 3 sessions a week it starts in about week 9.
- **B and C after M7,** in either order. B builds on labs 16, 20 and 26. C builds on labs 04, 12, 14, 15 and 40.
- **D after M5,** or as soon as labs 05, 13, 18, 23, 25 and 33 are done. It builds on labs 05 and 33 (the ratings model), 13 (candidates, then a ranker), 18 (k-means hygiene), 23 (propensity weights) and 25 (A/B power), and ends with a timed mock.
- **Pace.** At 3 sessions a week the 40 labs take about 13.5 weeks and the 16 capstone sessions about 5.5 more, about 19 weeks in all, plus about 3 hours a week of borrowed video as second contacts. Labs 30, 38 and 39 need their videos before the lab (2 evenings each), so put them in lighter weeks.
- Open a capstone file only after its labs. The sessions assume their debriefs.

## Links

- Tutor and build rules: [`../CLAUDE.md`](../CLAUDE.md). Lab template: [`../../templates/ml-lab-template.md`](../../templates/ml-lab-template.md).
- The six Staff criteria every write-up is graded on: root [`CLAUDE.md`](../../CLAUDE.md#7-staff-level-bar-calibrate-answers-to-this) §7.
- Labs live in the module folders: [`m1-whole-game/labs/`](../m1-whole-game/labs/), [`m2-dont-fool-yourself/labs/`](../m2-dont-fool-yourself/labs/), [`m3-more-of-the-map/labs/`](../m3-more-of-the-map/labs/), [`m4-production-ml-payments/labs/`](../m4-production-ml-payments/labs/), [`m7-language-models/labs/`](../m7-language-models/labs/).
- Prediction log: [`../prediction-log.md`](../prediction-log.md). Quiz bank: [`../quiz-bank.md`](../quiz-bank.md).
