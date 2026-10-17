# 14. An eval set and an LLM judge: judges need a human ceiling

> Goal: after this I can measure a local LLM judge's agreement with human verdicts on 50 pairs, compare it with human-human agreement, and measure its position bias. (No result values anywhere in this file.)

**Level:** S (see `ml-learning/CLAUDE.md`). **Output style:** Explanatory
**Concept link:** [`../README.md#llm-judges-and-eval-sets`](../README.md#llm-judges-and-eval-sets) (read after the lab)
**Borrowed from:** Zheng et al. 2023, "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena" ([arXiv 2306.05685](https://arxiv.org/abs/2306.05685)); Chip Huyen, *AI Engineering* (O'Reilly, 2025), chapters 3 and 4 ([book repo](https://github.com/chiphuyen/aie-book)); Shankar et al. 2024, "Who Validates the Validators?" ([arXiv 2404.12272](https://arxiv.org/abs/2404.12272)). Do it after the lab, as the second contact 1 to 3 days later.
**Dataset:** MT-Bench human judgments ([`lmsys/mt_bench_human_judgments`](https://huggingface.co/datasets/lmsys/mt_bench_human_judgments), from Zheng et al. 2023), `human` split: 3,355 pairwise verdicts (1,293 model_a, 1,282 model_b, 780 tie) by 65 expert and author judges, on 80 questions, 6 models and 2 turns; 961 pairs carry 2 or more human votes. One parquet file, 0.74 MB (738,612 B), <https://huggingface.co/datasets/lmsys/mt_bench_human_judgments/resolve/main/data/human-00000-of-00001-25f4910818759289.parquet>, ungated, CC BY 4.0. The lab uses 50 turn-1 pairs with at least 2 votes and a non-tie majority. Judge: Ollama `qwen2.5:7b` (4.68 GB, public registry, no login)
**Runs on:** cpu+ollama. **Lane:** heavy. **Compute:** 3 runs x up to 6 min (the seed-0 reference runs, rounded up: baseline 4 min, change 6 min, break 3 min), at most 6 min per run. Precomputed steps: none
**Needs:** base install only (the script calls Ollama's HTTP API with `requests`); Ollama 0.18 with `qwen2.5:7b`, no Python package
**Before the session** (from the module folder, see section 2): start Ollama (`ollama serve` in a second terminal, or the menu-bar app), then `ollama pull qwen2.5:7b` (your store may not hold it yet) and `curl -s localhost:11434/api/version`. Run `python scripts/14_llm_judge.py --download` (the parquet into `~/ml-data/mt_bench_human_judgments/`, the eval set ids and a labelling sheet into `~/ml-data/lab14/`), then `--smoke`. Human step, about 30 minutes, the day before: read the 20 pairs in `~/ml-data/lab14/to_label.txt` and write A or B for each in `~/ml-data/lab14/my_labels.csv` (no ties, no lookups, no AI). `--smoke` counts how many you have filled.
**Interview question:** How do you know a prompt or model change did not make the assistant worse before it ships, and when can you trust an LLM judge?
**Repo link:** [`hld/financial-ai-assistant/deep-dives/offline-evals-and-rollout.md`, §5 The judge, and how far to trust it](../../../hld/financial-ai-assistant/deep-dives/offline-evals-and-rollout.md#5-the-judge-and-how-far-to-trust-it); [§3 The statistics: what the suite can and cannot see](../../../hld/financial-ai-assistant/deep-dives/offline-evals-and-rollout.md#3-the-statistics-what-the-suite-can-and-cannot-see), for the first half of the interview question
**Captured by the script:** P1 to P3 and every Record row; `baseline.my_agreement_pct` only once your labels are in `my_labels.csv`. **Human steps:** label 20 pairs before the session (above). You also write the harness prompt, `confusion()` and `agreement_and_kappa()` in section 3
**Status:** todo

## 0. Retrieval (0:00, 5 min, closed book, no AI)

The AI asks up to three due cards from `../../quiz-bank.md`, one at a time. Do not open the bank first.

## 1. Predict (0:05, 7 min, no AI)

Level S: read `scripts/14_llm_judge.py` for 2 minutes first. `load_data()`, `write_label_sheet()`, `check_server()` and `report()` are given; `report()` is the RESULT contract your harness feeds. `JUDGE`, `FORMAT_V1`, `FORMAT_V2`, `PAIR` and `OPTIONS` are fixed. `JUDGE` is adapted from MT-Bench's pairwise judge prompt (Zheng et al. 2023), without its written explanation and its tie option.

Write each row here before anything runs; the AI copies it into `../../prediction-log.md` word for word. A row that asks for several numbers becomes one log row per number, each with its own range.

| Step | Question | Kind | Prediction | 80% range or confidence |
|---|---|---|---|---|
| P1 | `qwen2.5:7b` on Ollama 0.18, prompt v1 (`JUDGE` plus `FORMAT_V1`, the verdict-only schema), `OPTIONS` (temperature 0, Ollama seed 42, `num_ctx` 4096), the 50 pairs at `--seed 0`, answer A shown first: agreement in % between the judge's winner and the human majority winner | num | | |
| P2 | Prompt v2 (`JUDGE` plus `FORMAT_V2`: score both answers from 1 to 3 on correctness, helpfulness and concision, then the verdict) instead of v1, everything else as in P1: the agreement change in points vs P1 (up, down or same, plus a size range) | dir | | |
| P3 | Prompt v1 as in P1, but every pair shown with answer B first: the share of the 50 pairs whose winning answer differs from the P1 run, in % | num | | |

Terms, fixed so your numbers compare with the reference:

- **Pairs.** Turn 1 only. A pair is one question and two models, whatever order each human saw them in. Each human row is one vote: answer A, answer B or a tie. Answer A belongs to the model first in name order, answer B to the other. Model names never reach the judge.
- **Eval set.** Pairs with 2 or more votes and a strict non-tie majority: the verdict with the most votes among A, B and tie is unique, and it is not tie. 303 pairs qualify. `load_data(seed)` numbers them `p000` to `p302` in (question_id, model_a, model_b) order, draws 50 with `sample(n=50, random_state=seed)`, keeps that order, and saves the ids to `~/ml-data/lab14/eval_ids_seed<S>.csv`. `--seed S` draws other pairs; `OPTIONS` stay fixed.
- **Messages.** The system message is `JUDGE + " " + FORMAT_V1` for v1, or `JUDGE + " " + FORMAT_V2` for v2. The user message is `PAIR.format(question=..., a=..., b=...)`, with `a` the answer shown first and `b` the answer shown second.
- **Schemas (the `format` field).** v1: `{"type": "object", "properties": {"verdict": {"type": "string", "enum": ["A", "B"]}}, "required": ["verdict"]}`. v2: the keys `"a"`, `"b"` and `"verdict"`, in that order, all required. `"a"` and `"b"` are objects with the required keys `"correctness"`, `"helpfulness"` and `"concision"`, each `{"type": "integer", "enum": [1, 2, 3]}`. `"verdict"` is as in v1. Ollama turns the schema into a grammar, so every reply parses.
- **Request.** `POST /api/chat` with `model: qwen2.5:7b`, `stream: false`, `format` and `options: OPTIONS`. One request at a time. Each mode first sends one untimed warm-up call (a tiny made-up pair), which loads the model.
- **Verdict.** The reply's `"verdict"` names a slot: `"A"` is the answer shown first. In `--break`, `"A"` is answer B.
- **Agreement and kappa.** The judge's winner against the human majority over the 50 pairs, from the formula in section 3.
- **Human-human agreement, the ceiling.** Within each of the 50 pairs, every two votes that are both not tie form a vote pair. The ceiling is the share of vote pairs that name the same answer; `n=` counts the vote pairs.
- **Flip.** A pair flips when its winning answer under `--break` differs from its winner under `--baseline`. `--baseline` saves its verdicts to `~/ml-data/results/lab14/v1_seed<S>.json`, and `--change` and `--break` read them, so prompt v1 in the original order is sent once.
- **Change counts.** Right to wrong: v1 picked the human majority winner and v2 did not. Wrong to right: the reverse.
- **Tokens and seconds.** Ollama's `prompt_eval_count`, `eval_count` and `total_duration` for each judged pair, as the median over the 50. The warm-up call is not counted.
- **Your labels.** `--download` lists the first 20 pairs at seed 0 in `~/ml-data/lab14/to_label.txt` and writes `~/ml-data/lab14/my_labels.csv` (columns `pair_id` and `my_verdict`) once, never over your edits. `--baseline` compares your A or B verdicts with the human majority on the labelled pairs that are in its eval set.

## 2. Setup (before the session)

```
$ source ~/.venvs/ml/bin/activate
$ cd m3-more-of-the-map    # from ml-learning/, where sessions start
$ python scripts/14_llm_judge.py --download
$ python scripts/14_llm_judge.py --smoke
```

Ollama runs in its own terminal (`ollama serve`) or as the menu-bar app. Leave `OLLAMA_HOST` unset: the script defaults to `127.0.0.1:11434`. `--smoke` checks the given plumbing only (the server and the model, `load_data()` and `report()`) and counts the verdicts in your `my_labels.csv`. `--baseline`, `--change` and `--break` stop with NotImplementedError until the harness exists.

## 3. Baseline (0:12, 10 min)

Why: a judge is worth using only if it picks the winner people pick, so the first number is its agreement with the human majority on a fixed, saved set of pairs, next to how often the humans agree with each other.

You write first, in this file, no AI (about 5 min). This is the prompt the AI builds from:

1. The eval set: what `load_data(seed)` returns and saves, in your words, and which 20 pairs you labelled.
2. Both judge prompts (the system and user messages built from `JUDGE`, `FORMAT_V1`, `FORMAT_V2` and `PAIR`), both JSON verdict schemas, and the request body.
3. What each mode sends and keeps: the prompt, the order, the warm-up, the saved baseline verdicts, and how a letter from the swapped order maps back to answer A or B.
4. The RESULT contract: which `report()` call each mode makes, with which `scores` and `usage` (see its docstring).

Then write `confusion(human, judge)` and `agreement_and_kappa(human, judge)` yourself, in `scripts/14_llm_judge.py`, from this formula:

```
2 x 2 table over n items: rows = human majority verdict (A or B), columns = judge verdict (A or B)
p_o   = (n_AA + n_BB) / n                                         observed agreement
p_e   = (row_A / n) * (col_A / n) + (row_B / n) * (col_B / n)     chance agreement at each rater's own rates
kappa = (p_o - p_e) / (1 - p_e)
```

`confusion()` returns the 2 x 2 counts as a numpy array. `agreement_and_kappa()` returns `(p_o, kappa)`, both as fractions.

The AI then writes the schemas, the `/api/chat` calls, the human-human agreement, the agreement on your labels, the saved verdicts and the three modes from your prompt. Annotate each AI block with one line before the first run.

`--baseline` judges the 50 pairs with prompt v1, answer A shown first.

```
$ python scripts/14_llm_judge.py --baseline
(paste your RESULT lines)
```

Prediction vs actual, one sentence. The reference run is in `../../answers/`; the AI opens it only after your P1 row exists and you have pasted your own RESULT lines.

## 4. Change one thing (0:22, 10 min)

Change: prompt v2, which is `FORMAT_V2` in place of `FORMAT_V1` with the v2 schema: the judge scores both answers from 1 to 3 on correctness, helpfulness and concision, then gives the verdict. Same 50 pairs, same order. P2 is logged above.

Why: a rubric makes the judge commit to named criteria before it picks. Only the pairs whose verdict changes carry evidence about that, so the run also counts them each way.

```
$ python scripts/14_llm_judge.py --change
(paste your RESULT lines)
```

## 5. Break it (0:32, 10 min, AI gives hints only; the run finishes by 0:40)

Break: swap the order of the two answers in every pair (answer B shown first) and judge all 50 pairs again with prompt v1. P3 is logged above.

Why: the answers stay the same and only their order changes, so at temperature 0 a verdict that changes was decided by position. `--break` also prints the agreement of the swapped run, defined in the Record table.

```
$ python scripts/14_llm_judge.py --break
(paste your RESULT lines)
```

Why, in three sentences, written without AI:

## 6. Explain-back (0:42, 5 min) and rebuild (0:47, 10 min), no AI

- Five sentences for a smart engineer new to ML, written without AI. The AI names your weakest claim after the session (section 7).
- Rebuild: open `rebuild/14_judge_agreement.py`, write `confusion()`, `agreement_and_kappa()` and `flip_rate()` from memory, then run `python rebuild/14_judge_agreement.py`. Its `check()` compares with scikit-learn's `confusion_matrix`, `accuracy_score` and `cohen_kappa_score`, never with this lab's results.

## 7. What I learned

After the session (about 5 minutes): the AI names the weakest claim in your five sentences and asks one question that tests it. Edit the sentences here.

## 8. Interview soundbite (one of the three cards written at 0:57)

> One or two sentences only someone who ran this would say.

Staff follow-up: failure modes. The team swaps the judge's model, or someone edits its prompt: what do you re-run before you trust its verdicts again, and what bar must it clear? Answer in 2 sentences from the offline evals deep dive, §5. Rotate: simplest design, failure modes, migration, what pages at 3 am, cost, trade-off.

## 9. Quiz cards (0:57, 3 min)

The AI drafts three cards (M, N, and T or D). Edit or replace them. Questions go to `../../quiz-bank.md`, keys to `../../answers/quiz-key.md`.

## Record

The script prints these as RESULT lines. Paste, do not type. Shares are in % of the 50 pairs unless `n=` says otherwise. Timing lines carry `device=ollama`, `batch=1` (one request at a time), `warmup=1`, `n=` and `stat=median`.

| Metric | Your run | Hardware (the script's HW line) | Captured by (script or learner) |
|---|---|---|---|
| `P1.agreement_pct` (v1, answer A first, vs the human majority) | | | script |
| `baseline.kappa` (Cohen's kappa, v1 vs the human majority) | | | script |
| `baseline.picks_a_pct` (v1 verdicts that pick answer A, shown first) | | | script |
| `baseline.human_a_pct` (pairs whose human majority is answer A) | | | script |
| `baseline.human_human_pct` (the ceiling on the same 50 pairs; `n=` vote pairs) | | | script |
| `baseline.my_agreement_pct` (your labels vs the human majority; `n=` your labelled pairs) | | | learner |
| `baseline.prompt_tokens` (median per judged pair) | | | script |
| `baseline.output_tokens` | | | script |
| `baseline.s_per_item` (median seconds per judged pair, from `total_duration`) | | | script |
| `change.agreement_pct` (v2 vs the human majority) | | | script |
| `change.kappa` | | | script |
| `change.picks_a_pct` | | | script |
| `P2.agreement_delta_pts` (v2 minus v1, points) | | | script |
| `change.right_to_wrong` (pairs) | | | script |
| `change.wrong_to_right` (pairs) | | | script |
| `change.prompt_tokens` | | | script |
| `change.output_tokens` | | | script |
| `change.s_per_item` | | | script |
| `P3.flip_rate_pct` (pairs whose winner changes under the swap) | | | script |
| `break.picks_a_pct` (swapped verdicts that pick answer A, now shown second) | | | script |
| `break.agreement_pct` (swapped verdicts vs the human majority) | | | script |
| `break.prompt_tokens` | | | script |
| `break.output_tokens` | | | script |
| `break.s_per_item` | | | script |
