# answers/ (spoilers)

> **Spoiler warning.** Every measured result in this curriculum lives in this folder. Do not browse this folder before a lab.

## What lives here

| Path | Holds |
|---|---|
| `NN-<slug>.md` | The reference answers: HW line, seeds, runs, tolerance rule, then one `<details>` block per step (P1, P2, P3, rebuild check), a find-it debrief in labs 10, 16, 19, 20 and 27, card drafts and build notes |
| `NN-<slug>.json` | RESULT values by seed, with a tolerance per value (the seed spread). Precomputed steps are marked |
| `NN-<slug>.out` | Raw reference output, redirected, never printed |
| `NN_<slug>_ref.py` | Reference script for levels C, S and B. A level W reference is the script in `scripts/` |
| `rebuild/NN_<piece>.py` | Rebuild solutions: each stub with its body written |
| `rebuild/stubs/NN_<piece>.py` | Labs 16, 19, 20 and 27: the rebuild stub, kept here because it would reveal the planted bug. The AI copies it into the module's `rebuild/` at 0:47 |
| `quiz-key.md` | One key per quiz card: ID, answer, must-mention items |

## The gate

- The AI opens a file here only after that step's row in `../prediction-log.md` holds your prediction (an 80% range or a confidence) and you pasted your own RESULT lines, or after you say `debrief NN`.
- It opens only the `<details>` block for the step that is due. Never another lab's. It never searches this folder.
- A quiz key is shown only after you answer its card.

Do not browse this folder before a lab.
