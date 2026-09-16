# tool-practise/ conventions

This folder is a hands-on lab. One sub-folder per open source tool (Redis,
Kafka, etcd, Postgres, ...). The goal is muscle memory: run the tool locally,
poke at it with its CLI, break it, watch how it fails, and write down what I
saw. Reading about a system lives in `concepts/` and
`popular_systems_deepdive/`. Running it lives here.

The root `CLAUDE.md` still applies (answer style, color legend, Staff bar).
This file adds the folder layout, the exercise format, and the workflow.

---

## 1. Layout

```
tool-practise/
  README.md                     Index: every tool, status, what I have practised
  CLAUDE.md                     This file
  <tool-slug>/
    README.md                   What the tool is, how to start it, cheat-sheet of CLI commands, links to exercises
    docker-compose.yml          Single command to bring the tool up locally. Keep it minimal
    exercises/
      01-<topic>.md             One exercise per file, numbered. See §2 for the format
      02-<topic>.md
    notes.md                    Free-form: things that surprised me, gotchas, "aha" moments
    scripts/                    Optional: small client programs (Python by default) that exercise the tool
```

Slug is `kebab-case`, e.g. `tool-practise/redis/`, `tool-practise/kafka/`.

Every tool gets a folder even if it starts with only a `README.md` and a
`docker-compose.yml`.

---

## 2. Exercise format

Every `exercises/NN-<topic>.md` has this shape. Copy
`templates/tool-exercise-template.md` to start one.

1. **Goal.** One line. What I should be able to do after this.
2. **Concept link.** Which note in `concepts/` or `popular_systems_deepdive/`
   this exercise makes concrete.
3. **Setup.** The exact commands to get into the starting state.
4. **Steps.** Numbered. Each step is a command plus the output I expect and a
   one-line "why".
5. **Break it.** At least one step that makes the tool fail or degrade: kill a
   node, fill memory, partition the network, send a bad payload. Observe and
   record what happened.
6. **What I learned.** 3 to 5 bullets, in my own words. Numbers where
   possible ("~120k ops/sec on one shard with pipelining", not "fast").
7. **Interview soundbite.** One or two sentences I can say out loud that only
   someone who has actually run the tool would say.

Rules:

- Commands must be copy-pasteable. Prefix with `$` for shell, `>` for the
  tool's own CLI (`redis-cli`, `kafka-console-producer`, `psql`).
- Show real output, trimmed. Do not invent output I did not see.
- One exercise = 15 to 45 minutes. Split anything bigger.
- Order exercises from "hello world" to "make it fail".

---

## 3. What each file is for

| File | Owner | Purpose |
|---|---|---|
| `README.md` | AI + me | What the tool is (one line), how to start and stop it, the 10 to 20 CLI commands worth memorising, index of exercises with status. |
| `docker-compose.yml` | AI | The smallest compose file that gives me a working local instance. Pin image versions. Multi-node only when an exercise needs it. |
| `exercises/*.md` | AI writes the skeleton, I fill in outputs and "what I learned" | The actual practice. |
| `notes.md` | me | Scratch notes and gotchas. AI never edits this file. |
| `scripts/` | AI + me | Client code that exercises the tool. Python unless the tool's ecosystem strongly prefers something else. Keep each script under ~100 lines. |

---

## 4. Workflow

1. `docker compose up -d` in the tool folder.
2. Open the next `todo` exercise, run it top to bottom, paste real output.
3. Do the "break it" step. Do not skip it. This is where the interview
   answers come from.
4. Fill in "what I learned" and the soundbite.
5. Flip status in the tool's `README.md` and in `tool-practise/README.md`.
6. `docker compose down -v` when done so the next run starts clean.

Status legend: `todo` | `in-progress` | `done`.

---

## 5. Docker rules

- Pin image tags (`redis:7.4`, not `redis:latest`).
- Expose the tool's default port on localhost only.
- No volumes unless persistence is the thing being practised.
- Keep every compose file under ~40 lines. If it grows past that, the exercise
  is probably too big.
- Never commit data directories. `.gitignore` handles `tool-practise/**/data/`.

---

## 6. What NOT to put here

- Long explanations of how the tool works internally. Those go in
  `concepts/` or `popular_systems_deepdive/` and get linked from the exercise.
- Production configs, Helm charts, Terraform. This is a laptop lab.
- Anything that needs cloud credentials.
