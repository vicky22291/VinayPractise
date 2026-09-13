# hld/ conventions

This folder holds one sub-folder per HLD problem. The goal is depth, not
coverage: for every problem I should be able to answer the edge cases an
interviewer probes with, confidently and with a diagram.

The root `CLAUDE.md` still applies (answer style, color legend, Staff bar).
This file only adds the folder layout and workflow for HLD problems.

---

## 1. Layout

```
hld/
  README.md                     Practice index: ranked list of problems, status per problem
  CLAUDE.md                     This file
  <problem-slug>/
    README.md                   Problem statement + requirements + what interviewers probe
    solution.md                 AI-generated full HLD, built from templates/hld-template.md
    <problem-slug>.excalidraw   My own hand-drawn architecture (I draw this, AI never edits it)
    edge-cases.md               Checklist of edge cases + failure modes, each with a confident answer
    deep-dives/
      <component-or-topic>.md   One file per zoom-in (e.g. sharding.md, exactly-once.md, hot-keys.md)
    my-attempt.md               Optional: my answer before reading solution.md, plus critique
```

Slug is `kebab-case`, e.g. `hld/distributed-job-scheduler/`.

Do not put problem files directly in `hld/`. Every problem gets a folder, even
if it starts with only a `README.md`.

---

## 2. What each file is for

| File | Owner | Purpose |
|---|---|---|
| `README.md` | AI + me | Problem statement, functional and non-functional requirements, companies that ask it, the 3 to 5 questions an interviewer uses to probe depth. Short. |
| `solution.md` | AI | The full HLD answer following the 8-step skeleton in root `CLAUDE.md` §5. This is the reference answer. |
| `<slug>.excalidraw` | me | My own diagram, drawn from memory after studying. AI must never create or modify this file. If it is missing, the problem is not done. |
| `edge-cases.md` | AI + me | The list of "what if" questions and their answers. See §3. |
| `deep-dives/*.md` | AI | Zoom-in on one component or one hard sub-problem. Each is a standalone note with its own diagram. Cross-link to `concepts/` where a reusable concept exists. |
| `my-attempt.md` | me, then AI critique | My answer written before reading the solution. AI critiques it against the Staff bar (root `CLAUDE.md` §7) and lists what I missed. |

---

## 3. edge-cases.md format

This is the file that makes the difference in a Staff interview. Every entry
must be answerable in under 60 seconds out loud.

```
## Edge case: <one-line scenario>
- **Trigger:** what causes it (e.g. region outage, clock skew, duplicate delivery, hot partition)
- **Symptom:** what the user or on-call sees
- **Answer:** how the design handles it, in 2 to 4 bullets
- **Diagram:** (optional) small Mermaid diagram if the flow is non-obvious
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident
```

Minimum categories to cover for every problem:

1. **Failure:** node dies, region dies, dependency (DB, queue, cache) is down or slow.
2. **Consistency:** concurrent writes, stale reads, retries and idempotency, ordering.
3. **Scale:** hot key, hot partition, thundering herd, 10x traffic tomorrow.
4. **Data:** schema change, backfill, replay, deletion / GDPR, size growth over 3 years.
5. **Operations:** what pages at 3am, how to roll out and roll back, how to migrate from the old system.
6. **Security / abuse:** auth boundary, rate limiting, malicious or malformed input.

---

## 4. Workflow for a new problem

1. Create the folder and `README.md` with the problem statement and probe questions.
2. Write `my-attempt.md` in 45 minutes, timed, without looking anything up.
3. Ask AI to generate `solution.md` and critique `my-attempt.md`.
4. Ask AI to generate `edge-cases.md` and the `deep-dives/` that the critique exposed.
5. Draw `<slug>.excalidraw` from memory. Compare with `solution.md`. Fix gaps.
6. Mark every edge case with a confidence level. Revisit the shaky ones.
7. Update the status row in `hld/README.md`.

A problem is **done** only when: the excalidraw exists, every edge case is
marked `confident`, and I can give the one-line answer plus trade-offs from
memory.

---

## 5. Rules for AI when working in this folder

- Always start `solution.md` from `templates/hld-template.md`. Do not invent a new structure.
- Never create, edit, or overwrite `*.excalidraw` files.
- When asked to critique `my-attempt.md`, grade against the six Staff criteria and say which were missed. Critique before agreeing.
- Keep `README.md` per problem short. Depth goes into `solution.md`, `edge-cases.md`, and `deep-dives/`.
- Every deep-dive gets its own colored Mermaid diagram. Red is only for the real bottleneck.
- Cross-link to `concepts/` and `popular_systems_deepdive/` instead of re-explaining a building block.
- No em-dashes in generated notes. Short sentences.
