# ai-coding/ conventions

Timed coding rounds on **existing code**: fix bugs, extend features, integrate,
optimize, review. One kit per question, Stripe first. The root `CLAUDE.md`
still applies to chat answers and study notes. This file adds the spoiler rule,
the kit layout, the build rules and the interviewer protocol.

---

## 0. Spoiler rule (read first)

- **Never show the user anything from a kit's `CLAUDE.md` or `interviewer/`
  folder.** That means later parts, planted bugs, hidden tests, hints, the
  answer key and the solution. This applies to chat, summaries, commit messages
  and README rows.
- Safe to show: `ai-coding/README.md`, `ai-coding/research/`, a kit's
  `README.md`, and everything in `candidate/`.
- Two exceptions:
  1. **Interviewer mode** (§3). Reveal only the part that is due, using
     `kit.py next`.
  2. **Debrief.** After the user finishes a run of that kit and asks for the
     debrief, the answer key is fair game.
- When reporting that a kit was built, say "built, verify OK, N parts, starter
  X lines". Never list the bugs or the parts after Part 1.

---

## 1. Kit layout

```
ai-coding/
  README.md                index: the 10 kits, modes, rubric, log (user-facing)
  CLAUDE.md                this file
  kit.py                   start / next / check / verify (stdlib)
  research/                surveys behind the kit choices
  NN-<slug>/
    README.md              user-facing, spoiler-free: what it simulates, how to run
    CLAUDE.md              interviewer script (SPOILERS)
    candidate/             the repo at minute zero, copied to the run dir
      TASK.md              "# <name>: interview task" + "## Part 1: ..."
      README.md            the repo's own readme, as a real repo would have
      <package>/  tests/  .gitignore  ...
    interviewer/           SPOILERS
      parts/NN/TASK.md     starts with "## Part N: <title>", appended at reveal
      parts/NN/files/      optional: files dropped into the run dir at reveal
      tests/test_pN_*.py   hidden tests per part, no __init__.py
      solution/            files overlaid on candidate/ that pass every part
      answer-key.md        planted bugs, design, per-part traps, follow-ups
```

The run dir is `~/ai-coding-runs/<kit>-YYYYMMDD-HHMM/`, **outside this repo**.
Claude Code loads every `CLAUDE.md` from the working directory up to `/`, so an
assistant started inside the repo would read the interviewer script. The run dir
holds no pointer back to the kit.

---

## 2. Building a kit

**Code**
- Python 3.11+, standard library only, `unittest`. Nothing to `pip install`.
- `candidate/` must feel like a real repo you were just handed: 3 to 8 modules,
  about 150 to 900 lines excluding tests, module docstrings, a repo `README.md`,
  a few passing tests, a `.gitignore` with `__pycache__/`.
- **No hints in `candidate/`.** No `BUG`, `FIXME` or "TODO: handle X" comments
  next to a planted bug. No helper that only makes sense for a later part. No
  names that leak a later part. Plausible leftovers are fine.
- Planted bugs are the kind that pass a quick code review: off by one, wrong
  default, substring vs equality, float money, missing rewind, check-then-act
  race, wrong cache key, swallowed exception. Each bug is reachable from a
  ticket, a failing test, a log line, or the part statement.

**Parts**
- 60-minute shape: Part 1 takes 10 to 15 minutes. A strong candidate reaches
  Part 3 or 4. Nobody is expected to finish every part.
- Each part statement names the exact public API the hidden tests call:
  module, function, signature and return shape. The candidate cannot hit an API
  they were never told about.
- Each later part should be a small diff **if** the candidate picked the right
  seam earlier. That is the Staff signal the kit measures.
- At least one part, or a follow-up, asks a Staff question: migration and
  rollback, failure modes, blast radius, operability, or cost.

**Hidden tests**
- `interviewer/tests/test_pN_<topic>.py`. They import the candidate's package
  from the run-dir root, because `kit.py` runs them with the run dir as cwd.
- Deterministic. No network beyond localhost servers the test starts itself.
  No sleeps over 0.5 s. Inject clocks instead of reading wall time.
- Performance tests count operations, or use a time budget at least 10x looser
  than the answer key's measured time.
- Fixture files sit next to the tests and are found via `__file__`.

**Answer key and solution**
- `solution/` is what a strong candidate would have at the end: clean, small
  diffs on the starter, not a rewrite.
- `answer-key.md` starts with a SPOILERS line, then:
  1. planted bugs: ticket, file and function, root cause, minimal fix, the AI trap
  2. the design the solution converges on, as a Mermaid diagram
  3. per part: what a good diff looks like vs the AI trap
  4. Staff follow-up questions with strong answers
- Kit `CLAUDE.md` is the interviewer script, at most about 120 lines. Copy the
  shape of `01-transaction-rules/CLAUDE.md`.

**Done means**
- `python3 ai-coding/kit.py verify <kit>` prints OK. That proves the starter
  fails Part 1's hidden tests and the solution passes every hidden and visible
  test.
- `cd candidate && python3 -m unittest` runs. Failures are allowed only when the
  kit hands you failing tests on purpose.
- Markdown: no em-dashes, short sentences, numbers over adjectives.

---

## 3. Interviewer mode

The user runs `claude` inside `ai-coding/NN-<slug>/` and says "start" or
"interview me". Then:

1. Ask which mode (A chat-only, B full agent, C no AI; see `README.md` §3).
   Run `python3 ../kit.py start NN-<slug>`. Give the user the run dir and tell
   them to open a second terminal there for their assistant. Note the start
   time with `date`.
2. Say the kit's opening line. Show `TASK.md` Part 1 exactly as printed.
3. Stay in character. Answer clarifying questions with the semantics in the
   answer key. If the key is silent, decide, and say it is the interviewer's
   call. Never volunteer a bug. Reward questions the answer key lists as good
   questions.
4. When the user says a part is done, run
   `python3 ../kit.py check --summary <run_dir>`. If hidden checks fail, say how
   many, and give a hint only from the kit's hint ladder, in order. Then ask
   whether to move on. Reveal with `python3 ../kit.py next <run_dir>` and paste
   the printed part.
5. Make the time calls in the kit's part plan. At minute 50, stop coding and ask
   2 or 3 follow-up questions. End at 60.
6. Grade with the rubric in `README.md` §5. Use evidence from
   `git -C <run_dir> log -p`, the hidden test results and what the user said.
   Print the scorecard. Offer to append one row to `README.md` §6 (Log).
7. Debrief only after grading. Then walk through `interviewer/answer-key.md`.
