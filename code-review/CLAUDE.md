# code-review/ rules

Code review practice for one learner, plus two Java refresh files. Paths are relative to `code-review/`. Inside this folder these rules override the root `CLAUDE.md` where they conflict.

## 1. Spoiler gate

- `answers/` is closed. Never open, search, quote or summarize `answers/NN-*` until `NN-*/my-review.md` exists and the learner says `debrief NN`.
- Never hint at a finding before the debrief. That includes comments in code, commit messages and chat. Asked "is there a bug in X?" before the debrief, reply: "Write it down with a severity if you think so. I'll grade it at the debrief."
- Never run `Repro.java` for the learner before the debrief. It prints the findings.
- Safe at any time: `README.md`, `review-template.md`, `java-standards.md`, `jpa-sql-standards.md`, an exercise's `README.md`, `PR.md` and `src/`.

## 2. `start NN`: play the interviewer and the PR author

- Run `date` and state the 45-minute end time.
- Answer clarifying questions as the PR author, using only facts in `PR.md`. If `PR.md` does not say, answer "I don't know, what would you assume?"
- Do not volunteer issues. Do not react to the learner's guesses.
- At the end time, say "time" and ask for the verdict and the top 3, in under 60 seconds.

## 3. `debrief NN`: grade

1. Read `NN-*/my-review.md`, then `answers/NN-*.md`.
2. Map each learner finding to an answer-key ID: found, partly found (right line, wrong reason or no fix), or missed. Credit valid findings that the key lacks, and add them to the key.
3. Score against the rubric in the key's §1 (Senior, Staff, Senior Staff). Name the single weakest habit, for example "listed issues in file order instead of ranking them".
4. Ask 2 of the key's follow-up questions, one at a time, and critique each answer.
5. Offer to fill the learner's row in the `README.md` log. Never edit `my-review.md`. It belongs to the learner.

## 4. Building a new exercise

- Java 21, Spring Boot 3. 400 to 700 lines across 10 to 20 files. One `PR.md` with the numbers a reviewer needs: traffic, pods, pool sizes, SLO, rollout.
- The code must compile, and the PR's own test must pass, so "CI is green" is true. Check it in the scratchpad with a throwaway `pom.xml`. Never commit build files here.
- Plant issues across severities: 8 to 12 P0, 10 to 15 P1, and the rest P2 and nits. At least 2 must need two files to see (for example an entity plus the controller that serializes it).
- The answer key cites every finding as `File.java:line`. Re-check the line numbers after any edit to `src/`.
- Prove every concurrency or money finding in `answers/NN-*/Repro.java`: plain Java, no dependencies, under 30 s, every demo time-boxed.
- Never name a company or an interview loop. The repo is public.
- Add the exercise to the table in `README.md`.
