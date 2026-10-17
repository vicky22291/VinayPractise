# 30. micrograd: the chain rule and a gradient check

> Goal: after this I can write `__mul__` and `backward()` for a scalar autograd engine (19 lines) and catch a gradient bug with a central finite-difference check at h = 1e-6. (No result values anywhere in this file.)

**Level:** C (see `ml-learning/CLAUDE.md`). **Output style:** Learning
**Concept link:** [`../README.md#backpropagation`](../README.md#backpropagation) (read after the lab)
**Borrowed from:** Karpathy, [micrograd video](https://www.youtube.com/watch?v=VMj-3S1tku0) (2:25:52). This lab is an exception: write P1 to P3 first, then watch the video over 2 evenings before the lab. [fast.ai Part 2 Lesson 13](https://course.fast.ai/Lessons/lesson13.html) comes after the lab, as the second contact 1 to 3 days later.
**Dataset:** synthetic: 20 random expressions over + and * from seed 42, with tanh nodes added to the same 20 in `--change` and `--break`, made by the script at run time, 0 MB, no URL (nothing to download), no licence needed (generated here)
**Runs on:** cpu. **Lane:** light. **Compute:** 3 runs x 1 min, at most 6 min per run. Precomputed steps: none
**Needs:** base install only
**Before the session** (from the module folder, see section 2): write P1 to P3 (section 1 and `../../prediction-log.md`), then watch the micrograd video over 2 evenings. Run `--download` (nothing to fetch) and `--smoke`.
**Interview question:** How does backprop handle a value used twice, and how do you test a gradient implementation?
**Repo link:** [`hld/payments-risk-decisioning/deep-dives/model-lifecycle-shadow-and-labels.md`](../../../hld/payments-risk-decisioning/deep-dives/model-lifecycle-shadow-and-labels.md#5-proving-a-model-before-it-declines-anyone), section 5, "Proving a model before it declines anyone"
**Captured by the script:** baseline, change, break (`--check` prints pass or fail only). **Human steps:** none
**Status:** todo

## 0. Retrieval (0:00, 5 min, closed book, no AI)

The AI asks up to three due cards from `../../quiz-bank.md`, one at a time. Do not open the bank first.

## 1. Predict (0:05, 7 min, no AI)

This lab is an exception: write these rows before you watch the video, days before the session. At 0:05, reread them and change nothing. Spend the rest of the block reading `scripts/30_micrograd.py`: the TODO is `__mul__` and `backward()`.

Write each row here before anything runs; the AI copies it into `../../prediction-log.md` word for word. A row that asks for several numbers becomes one log row per number, each with its own range.

Every synthetic expression has 2 to 6 + or * steps over inputs x, y and z, each drawn from -1 to 1. Each step combines the latest node with one earlier node, so an earlier node can feed more than one step. `--change` keeps the same 20 expressions and inputs and adds tanh: after each step, with probability 1/3, a tanh node takes that step's result, and later steps use the tanh node instead. A second random stream picks the tanh nodes, so nothing else changes.

| Step | Question | Kind | Prediction | 80% range or confidence |
|---|---|---|---|---|
| P1 | Correct engine, ops + and * only, 20 synthetic expressions from seed 42. The largest absolute gap between the engine's gradient and the central finite difference (h = 1e-6, plain Python floats), over all 20 expressions and all 3 inputs, as log10 | num | | |
| P2 | `--change`: the same 20 synthetic expressions and inputs as P1, with tanh nodes added (after each step with probability 1/3; local derivative 1 - tanh^2). The same largest gap, as log10 | num | | |
| P3 | `--break`: every `.grad +=` in `_backward` becomes `.grad =`. For c = a*b + a at a = 0.7 and b = -1.3, after `c.backward()`: the value `a.grad` shows | num | | |

## 2. Setup (before the session)

```
$ source ~/.venvs/ml/bin/activate
$ cd m5-under-the-hood    # from ml-learning/, where sessions start
$ python scripts/30_micrograd.py --download
$ python scripts/30_micrograd.py --smoke
```

## 3. Baseline (0:12, 10 min)

Why: a gradient check can flag a bug only if you know the gap a correct engine leaves.

Write the TODO first: `Value.__mul__` and `Value.backward()` in `scripts/30_micrograd.py`. Use `__add__` as the pattern, with `+=` for every gradient. Write each update as `x.grad += ...`: `--break` rewrites that text, and stops with a message if `__mul__` has none. The AI gives hints, or a draft explained line by line that you type. Run `--check` until it prints `check: PASS`, then run the baseline.

```
$ python scripts/30_micrograd.py --check
$ python scripts/30_micrograd.py --baseline
(paste your RESULT lines)
```

Prediction vs actual, one sentence. The reference run is in `../../answers/`; the AI opens it only after your P1 row exists and you have pasted your own RESULT lines.

## 4. Change one thing (0:22, 10 min)

Why: every new op brings its own local derivative, and the gradient check is how you know it is right.

Change: `--change` adds tanh nodes (the engine's `tanh()` has local derivative 1 - tanh^2) to the same 20 synthetic expressions from seed 42. The + and * steps, their operands and the inputs stay exactly as in the baseline, so tanh is the only thing that changes. P2 is logged above.

```
$ python scripts/30_micrograd.py --change
(paste your RESULT lines)
```

## 5. Break it (0:32, 10 min, AI gives hints only; the run finishes by 0:40)

Why: a node used twice receives one gradient contribution per use, and this run shows what the gradient check sees when they are assigned instead of added.

Break: `--break` rewrites every `.grad +=` in the `Value` class as `.grad =`, your `__mul__` included. It computes `a.grad` for c = a*b + a at a = 0.7 and b = -1.3, then reruns the gradient check on the synthetic `--change` expressions. P3 is logged above.

```
$ python scripts/30_micrograd.py --break
(paste your RESULT lines)
```

Why, in three sentences, written without AI:

## 6. Explain-back (0:42, 5 min) and rebuild (0:47, 10 min), no AI

- Five sentences for a smart engineer new to ML, written without AI. The AI names your weakest claim after the session (section 7).
- Rebuild: open `rebuild/30_mul_and_backward.py` and write `__mul__` and `backward()` from memory (`__init__` and `__add__` are given as the pattern). Then run `python rebuild/30_mul_and_backward.py`. Its `check()` compares with torch autograd and a central finite difference, never with this lab's results.

## 7. What I learned

After the session (about 5 minutes): the AI names the weakest claim in your five sentences and asks one question that tests it. Edit the sentences here.

## 8. Interview soundbite (one of the three cards written at 0:57)

> One or two sentences only someone who ran this would say.

Staff follow-up: simplest design. A central finite difference needs two forward passes for every weight it checks, so it cannot cover every weight of a production model. What is the smallest gradient test you would run in CI (continuous integration), and what does the section 5 shadow stage catch that no unit test can? Answer in 2 sentences from the repo link. Rotate: simplest design, failure modes, migration, what pages at 3 am, cost, trade-off.

## 9. Quiz cards (0:57, 3 min)

The AI drafts three cards (M, N, and T or D). Edit or replace them. Questions go to `../../quiz-bank.md`, keys to `../../answers/quiz-key.md`.

## Record

The script prints these as RESULT lines. Paste, do not type.

| Metric | Your run | Hardware (the script's HW line) | Captured by (script or learner) |
|---|---|---|---|
| `P1.log10_max_gap`: largest gap, correct engine, + and * (log10) | | | script |
| `baseline.a_grad`: a.grad for c = a*b + a, correct engine | | | script |
| `P2.log10_max_gap`: largest gap with tanh (log10) | | | script |
| `P3.a_grad`: a.grad for c = a*b + a with `=` | | | script |
| `break.log10_max_gap`: largest gap with `=` (log10) | | | script |
| `break.worst_expr`: the expression with the worst gap under `=` | | | script |
