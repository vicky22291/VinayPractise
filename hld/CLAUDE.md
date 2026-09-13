# hld/ conventions

This folder holds one sub-folder per HLD problem. The goal is depth, not
coverage: for every problem I should be able to answer the edge cases an
interviewer probes with, confidently and with a diagram.

The root `CLAUDE.md` still applies (answer style, color legend, Staff bar).
This file adds the folder layout, the answer template, the required diagram
set, and the workflow for HLD problems.

---

## 1. Layout

```
hld/
  README.md                     Practice index: ranked list of problems, status per problem
  CLAUDE.md                     This file
  <problem-slug>/
    README.md                   Problem statement + requirements + what interviewers probe
    solution.md                 AI-generated full HLD, following the template in §3 of this file
    diagrams.md                 The full diagram set for the problem (see §4). solution.md embeds the key ones and links here for the rest
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
| `solution.md` | AI | The full HLD answer following the template in §3. This is the reference answer. Interview-scope sections first, then the nitty-gritty sections that go past what fits in 45 minutes. |
| `diagrams.md` | AI | Every diagram in §4 for this problem, each with a one-line caption. `solution.md` embeds the 3 to 5 most important ones and links here for the rest. |
| `<slug>.excalidraw` | me | My own diagram, drawn from memory after studying. AI must never create or modify this file. If it is missing, the problem is not done. |
| `edge-cases.md` | AI + me | The list of "what if" questions and their answers. See §5. |
| `deep-dives/*.md` | AI | Zoom-in on one component or one hard sub-problem. Each is a standalone note with its own diagram. Cross-link to `concepts/` where a reusable concept exists. |
| `my-attempt.md` | me, then AI critique | My answer written before reading the solution. AI critiques it against the Staff bar (root `CLAUDE.md` §7) and lists what I missed. |

---

## 3. solution.md template (the delivery framework)

This is the Hello Interview delivery framework, extended with the repo's
numbers-first and Staff-bar rules. The structure is fixed. Do not invent a new
one per problem. `templates/hld-template.md` mirrors this section.

The core idea: **requirements drive the outline.** Every functional
requirement becomes one High-Level Design section. Every non-functional
requirement becomes one Deep Dive section. Nothing appears in the design
without a requirement pointing at it.

```
0.  One-line answer
1.  Understanding the problem
    1.1 Functional requirements     Core (3 to 5) + Below the line (explicitly out of scope)
    1.2 Non-functional requirements Ask for scale FIRST, then Core + Below the line.
                                    Table with numbers: peak QPS, avg QPS, p99 latency, availability, consistency, durability
2.  Back-of-envelope                DAU -> QPS (peak = 10x avg is the default heuristic) -> storage/yr -> bandwidth. Show the math.
3.  The set-up                      Pick ONE style based on the problem:
    Product-style (user-facing)     3.1 Core entities   3.2 API (table)   3.3 Data model (erDiagram + access patterns + partition key)
    Data-processing style           3.1 System interface (Input / Output)   3.2 Data flow (numbered, deliberately naive)   3.3 Data model (erDiagram of events + aggregates)
4.  High-level design               ONE subsection per functional requirement, in order.
    4.N <FR restated as a sentence>
        Bad / Good / Great ladder. Each rung: Approach -> diagram -> Challenges (why this rung breaks).
        Skip a rung only if there is genuinely no alternative worth naming.
        End the subsection with the sequenceDiagram for the chosen rung.
5.  Deep dives                      ONE subsection per non-functional requirement, phrased as the question the interviewer asks.
    5.N "How do we <meet NFR>?"     Walk the request path and name each bottleneck in order. Same Bad / Good / Great ladder.
                                    Mark the real bottleneck red in the diagram. At least one rung must include a "push back on the
                                    textbook answer" note (e.g. checkpointing is pointless with 1 minute windows plus stream replay).
6.  Final design                    One flowchart composing every "Great" pick. Under 15 nodes. Link to diagrams.md for zoom-ins.
7.  Trade-offs                      Table: Decision | Option A | Option B | Chose | Why. Include what we refused to build.
8.  Staff-level notes               Failure modes and blast radius, migration path, operability (SLO, what pages at 3am), cost, team boundaries.
9.  What is expected at each level  Mid (80/20 breadth/depth) | Senior (60/40) | Staff+ (40/60). One paragraph each: what the
                                    interviewer expects me to say unprompted at that level for THIS problem.
10. Nitty-gritty (past interview scope)   See §3.1 below. This is where depth lives.
11. Follow-up questions to expect   Ranked by how likely an interviewer asks them. Each links to an edge case or deep dive.
```

Rules for the ladder:

- **Bad** is not a strawman. It is what a mid-level candidate would say. Explain precisely which number breaks it.
- **Good** works. Say what it costs (latency, ops, money) that Great fixes.
- **Great** is the answer. Say what new problem it introduces. Every Great rung has a Challenges block too.
- Each rung gets its own small diagram if the architecture changes. A rung that only changes a parameter shares the diagram.

### 3.1 Nitty-gritty section (section 10)

The interview article stops where the clock runs out. This section keeps going.
Every problem's `solution.md` must include the following, and each item must be
short, concrete, and diagrammed where possible. Long items move to
`deep-dives/` and get linked.

| # | Item | What it must contain |
|---|---|---|
| 10.1 | **Internals of each chosen technology** | How the thing actually works, not what it is. Kafka: partitions, ISR, acks, consumer groups, offset commit. Flink: event time vs processing time, watermarks, window types, state backend, checkpoint barrier. Redis: single-threaded event loop, persistence modes, cluster slots. One diagram per technology. |
| 10.2 | **Configuration knobs that matter** | The 3 to 5 settings per component that change behaviour, with the value we would pick and why. E.g. `acks=all`, `min.insync.replicas=2`, retention 7d, Flink checkpoint interval, Redis `maxmemory-policy`. |
| 10.3 | **Capacity math per component** | Not just the system total. Per shard, per partition, per node: bytes/s, records/s, memory for in-flight state, disk for retention. Show which component is closest to its limit. |
| 10.4 | **Failure timeline** | For the top 2 to 3 failures: a second-by-second sequenceDiagram of what happens. Detection time, failover time, data at risk, what the user sees, what the on-call sees. |
| 10.5 | **Exactly-once / idempotency story end to end** | Where duplicates can enter, where they are removed, what the dedup key is, how long it lives, what happens on retry at every hop. |
| 10.6 | **Consistency model per edge** | Every arrow in the final diagram labelled strong / read-your-writes / eventual, and where it changes. |
| 10.7 | **Alternatives rejected** | Table: Alternative | Why it looked attractive | The specific reason we rejected it. Includes tech choices (TSDB vs OLAP, Kinesis vs Kafka, Spark Streaming vs Flink). |
| 10.8 | **How the big companies do it** | 2 to 4 bullets with real-world references: the published system that solves this (e.g. Meta Scribe, Google Photon, LinkedIn Samza). What they do differently and why. |
| 10.9 | **Operational runbook** | Dashboards: the 5 metrics. Alerts: threshold and who gets paged. Rollout: canary plan. Rollback: how, and what data needs backfill. |
| 10.10 | **Security and abuse** | Auth boundary, signed tokens, rate limits, what a malicious client can and cannot do. |
| 10.11 | **Evolution** | What changes at 10x scale. What changes if a new requirement lands (multi-region, GDPR delete, new dimension to slice by). Name the seam. |

---

## 4. Required diagram set (diagrams.md)

Every problem gets all of these unless a row says "if applicable". Mermaid
only, colored per root `CLAUDE.md` §3, `%% comment` above each, every arrow
labelled with what flows on it. Mermaid has no native activity or DFD types, so
the table says which Mermaid type stands in.

| # | Diagram | Mermaid type | What it must show |
|---|---|---|---|
| D1 | **Context (zoom-out)** | `flowchart LR` | Our system as one box, every external actor and system around it, what flows on each edge. Under 10 nodes. |
| D2 | **Data flow (DFD)** | `flowchart LR` | Inputs to outputs. Each edge labelled with data name, format, size, rate (e.g. `click event, JSON ~100B, 10k/s peak`). Stores as cylinders, processes as rounded boxes. |
| D3 | **Component architecture** | `flowchart LR` / `TD` | The main HLD diagram. Every service, store, cache, queue. This is the "Final design" from solution.md §6. |
| D4 | **Sequence, happy path, one per FR** | `sequenceDiagram` with `autonumber` | The full request path for that FR including the redirect or the response. |
| D5 | **Sequence, failure path, at least two** | `sequenceDiagram` | What happens when a dependency times out, a node dies mid-request, a duplicate arrives. Show retries and timeouts explicitly. |
| D6 | **Activity / decision flow** | `flowchart TD` with diamond decision nodes | The branching logic inside the hardest component (dedup check, hot-key routing, retry policy). Decision nodes colored `decision`. |
| D7 | **Entity relationship** | `erDiagram` | Events, aggregates, and reference entities. Include PK, partition key, and TTL where relevant. |
| D8 | **State machine (if applicable)** | `stateDiagram-v2` | Any entity with a lifecycle: job, order, message, session, stream processor task. |
| D9 | **Deployment / topology** | `flowchart` with `subgraph` per region or AZ | Where each component runs, replication factor, what crosses a region boundary. |
| D10 | **Scaling / partitioning** | `flowchart LR` | How data is sharded: partition key, number of shards, the hot shard colored red, the fix. |
| D11 | **Failure mode map** | `flowchart TD` | Each component -> what fails -> blast radius -> mitigation. One tree. |
| D12 | **Rollout / migration (if applicable)** | `gantt` | Phases to get from the current system to this one with a rollback point per phase. |

Guidelines:

- Under 15 nodes per diagram. Split into zoom-out plus zoom-in when bigger.
- The same diagram is never pasted twice. `solution.md` embeds a diagram once and links to `diagrams.md` anchors for the rest.
- Red is reserved for the one thing that breaks first. That node must appear in solution.md §5 or §7.

---

## 5. edge-cases.md format

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

## 6. Workflow for a new problem

1. Create the folder and `README.md` with the problem statement and probe questions.
2. Write `my-attempt.md` in 45 minutes, timed, without looking anything up.
3. Ask AI to generate `solution.md` (template §3) and `diagrams.md` (set §4), and to critique `my-attempt.md`.
4. Ask AI to generate `edge-cases.md` and the `deep-dives/` that the critique and §3.1 exposed.
5. Draw `<slug>.excalidraw` from memory. Compare with `solution.md` §6. Fix gaps.
6. Mark every edge case with a confidence level. Revisit the shaky ones.
7. Update the status row and the file index for the problem in `hld/README.md`.

A problem is **done** only when: the excalidraw exists, every edge case is
marked `confident`, and I can give the one-line answer plus trade-offs from
memory.

---

## 7. Rules for AI when working in this folder

- Always structure `solution.md` per §3 and start from `templates/hld-template.md`. Do not invent a new structure.
- Always produce the full diagram set in §4 as `diagrams.md`. Rows marked "if applicable" may be skipped with a one-line reason.
- Section 10 (nitty-gritty) is mandatory, not optional. It is the reason this repo exists. If it gets long, split into `deep-dives/` and link.
- Never create, edit, or overwrite `*.excalidraw` files.
- When asked to critique `my-attempt.md`, grade against the six Staff criteria and say which were missed. Critique before agreeing.
- Keep `README.md` per problem short. Depth goes into `solution.md`, `diagrams.md`, `edge-cases.md`, and `deep-dives/`.
- Every deep-dive gets its own colored Mermaid diagram. Red is only for the real bottleneck.
- Cross-link to `concepts/` and `popular_systems_deepdive/` instead of re-explaining a building block.
- When a source article (e.g. Hello Interview) exists for the problem, follow its FR and NFR list and its Bad / Good / Great picks, then go past it in section 10. Cite the source once at the top of `solution.md`.
- Whenever a file is added, renamed, or removed in any `<problem-slug>/` folder, update that problem's entry in `hld/README.md` in the same change: bump the status if it changed, and keep the per-problem file index (links to `solution.md`, `diagrams.md`, `edge-cases.md`, each `deep-dives/*.md`) accurate. `hld/README.md` is the single place to see what exists for every problem.
- No em-dashes in generated notes. Short sentences.
