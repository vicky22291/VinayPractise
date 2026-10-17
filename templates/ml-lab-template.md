# NN. <Lab title>

> Goal: after this I can <one concrete skill, with a number>. (No result values anywhere in this file.)

**Level:** W | C | S | B (see `ml-learning/CLAUDE.md`). **Output style:** Explanatory (W, S, B) | Learning (C)
**Concept link:** `../README.md#<concept-section-anchor>` (read after the lab)
**Borrowed from:** <unit and link>. Do it after the lab, as the second contact 1 to 3 days later. (Labs 30, 38 and 39: write P1 to P3 first, then watch before the lab.)
**Dataset:** <name>, <rows>, <MB>, <URL>, <licence>
**Runs on:** cpu | mps | mlx | cpu+ollama. **Lane:** light | heavy. **Compute:** <N runs x M min>, at most 6 min per run. Precomputed steps: <none | step>
**Needs:** base install only | `python -m pip install <pkg>==<pin>`
**Before the session** (from the module folder, see section 2): <downloads, `--smoke`, `ollama serve`, human steps such as labelling 20 pairs>
**Interview question:** <one question>
**Repo link:** <verified repo path, section>
**Captured by the script:** <steps>. **Human steps:** <steps or none>
**Status:** todo

## 0. Retrieval (0:00, 5 min, closed book, no AI)

The AI asks up to three due cards from `../../quiz-bank.md`, one at a time. Do not open the bank first.

## 1. Predict (0:05, 7 min, no AI)

Level W only: before the session, read `scripts/NN_<slug>.py` (about 10 minutes) and answer its three `# Q:` prompts here. At 0:05 you only predict.

Write each row here before anything runs; the AI copies it into `../../prediction-log.md` word for word. A row that asks for several numbers becomes one log row per number, each with its own range.

| Step | Question | Kind | Prediction | 80% range or confidence |
|---|---|---|---|---|
| P1 | <baseline question, exact config named> | num | | |
| P2 | <change one thing: direction and size> | dir | | |
| P3 | <break it: what happens> | num, dir or pick | | |

## 2. Setup (before the session)

```
$ source ~/.venvs/ml/bin/activate
$ cd <module-folder>    # from ml-learning/, where sessions start
$ python scripts/NN_<slug>.py --download
$ python scripts/NN_<slug>.py --smoke
```

## 3. Baseline (0:12, 10 min)

Why: <one line>

```
$ python scripts/NN_<slug>.py --baseline
(paste your RESULT lines)
```

Prediction vs actual, one sentence. The reference run is in `../../answers/`; the AI opens it only after your P1 row exists and you have pasted your own RESULT lines.

## 4. Change one thing (0:22, 10 min)

Change: <exactly one knob>. P2 is logged above.

```
$ python scripts/NN_<slug>.py --change
(paste your RESULT lines)
```

## 5. Break it (0:32, 10 min, AI gives hints only; the run finishes by 0:40)

Break: <what you do, never what happens>. P3 is logged above.

```
$ python scripts/NN_<slug>.py --break
(paste your RESULT lines)
```

Why, in three sentences, written without AI:

## 6. Explain-back (0:42, 5 min) and rebuild (0:47, 10 min), no AI

- Five sentences for a smart engineer new to ML, written without AI. The AI names your weakest claim after the session (section 7).
- Rebuild: open `rebuild/NN_<piece>.py`, write the body from memory, then run `python rebuild/NN_<piece>.py`. Its `check()` compares with <library>, never with this lab's results.

## 7. What I learned

After the session (about 5 minutes): the AI names the weakest claim in your five sentences and asks one question that tests it. Edit the sentences here.

## 8. Interview soundbite (one of the three cards written at 0:57)

> One or two sentences only someone who ran this would say.

Staff follow-up: <the next probe>, answered in 2 sentences from the repo link. Rotate: simplest design, failure modes, migration, what pages at 3 am, cost, trade-off.

## 9. Quiz cards (0:57, 3 min)

The AI drafts three cards (M, N, and T or D). Edit or replace them. Questions go to `../../quiz-bank.md`, keys to `../../answers/quiz-key.md`.

## Record

The script prints these as RESULT lines. Paste, do not type.

| Metric | Your run | Hardware (the script's HW line) | Captured by (script or learner) |
|---|---|---|---|
| <metric> | | | script |
