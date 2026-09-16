# CLAUDE.md — Staff Engineer Interview Prep Repo

This repo is a **study workspace**, not a product. Everything here exists to make
concepts stick fast: HLD, LLD, distributed-systems fundamentals, DSA, and
behavioral prep for **Staff / Principal Engineer** interviews.

---

## 1. Non-negotiable answer style

Every explanation follows this shape:

1. **One-line answer first.** What is it / what would I build. No preamble.
2. **Diagram second.** A Mermaid diagram, colored per the legend in §3.
3. **Brief prose third.** Short bullets, plain English, no jargon walls.
4. **Trade-offs last.** What we gave up, and why. Staff interviews are won here.

Hard rules:

- **Always draw a diagram.** If a concept can be drawn, draw it. Text-only
  answers are a last resort, not the default.
- **Simple language.** Explain like to a smart engineer who has not seen this
  system before. Expand an acronym the first time it appears.
- **Brief.** Bullets over paragraphs. Aim for the diagram to carry 60% of the load.
- **Numbers, not adjectives.** "~50k QPS, p99 120ms" beats "high traffic, fast".
- **Never hand-wave a bottleneck.** Name it, color it red, then solve it.
- **Don't dump code** unless the topic is LLD or DSA. Then show real, runnable code.

---

## 2. Diagram rules

- Use **Mermaid** for everything (renders in GitHub, VS Code, and Claude artifacts).
- Pick the right diagram type:

| Situation | Diagram type |
|---|---|
| System architecture, HLD | `flowchart LR` / `flowchart TD` |
| Request flow, protocol, handshake | `sequenceDiagram` |
| LLD classes, relationships | `classDiagram` |
| Object/entity lifecycle, order states | `stateDiagram-v2` |
| Data model, schema | `erDiagram` |
| Rollout plan, migration phases | `gantt` |
| Trade-off / decision tree | `flowchart TD` with decision nodes |

- Keep one diagram to **≤ 15 nodes**. More than that → split into a "zoom-out"
  diagram plus per-component "zoom-in" diagrams.
- Label every arrow with what flows on it (`write`, `async event`, `cache miss`).
- Add a `%% comment` above each diagram saying what it is showing.

---

## 3. Color legend (use these exact classDefs)

Always apply colors. Always set `color:#111` so text is readable in dark mode.
Copy this block into diagrams — the canonical copy lives in
`templates/color-legend.md`.

```
classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
classDef cache    fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#111
classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

| Class | Color | Means |
|---|---|---|
| `client` | 🔵 blue | Clients, edge, API gateway, load balancer |
| `service` | 🟢 green | Stateless compute / microservices |
| `store` | 🟣 purple | Databases, durable storage, blob store |
| `cache` | 🟡 amber | Redis, CDN, local cache — anything losable |
| `queue` | 🔷 cyan | Kafka, SQS, streams, async pipes |
| `critical` | 🔴 red, thick | **Bottleneck, SPOF, hot path, consistency risk** |
| `external` | ⚪ grey, dashed | Third-party / outside our trust boundary |
| `decision` | 🩷 pink | Trade-off points, alternatives being weighed |

**Red is reserved.** Only color a node red if it is genuinely the thing that
breaks first under load or failure. That node must be discussed in the trade-offs.

---

## 4. Repo layout

```
hld/          One file per system design case study (URL shortener, feed, chat, …)
lld/          One file per object-design problem (parking lot, rate limiter, …)
concepts/     Reusable building blocks (CAP, consensus, sharding, Kafka, caching)
problem_solving/  DSA — Python. Patterns + solved problems.
behavioral/   Staff-level STAR stories, scope/influence/ambiguity narratives
templates/    Study templates + the canonical color legend
tool-practise/  Hands-on lab: one folder per open source tool (Redis, Kafka, ...), docker-compose + exercises
```

- File names: `kebab-case.md`, e.g. `hld/design-whatsapp.md`.
- Start every new HLD from `templates/hld-template.md`, every LLD from
  `templates/lld-template.md`. Don't invent a new structure per file.
- Cross-link. An HLD that shards should link to `concepts/sharding.md`.

---

## 5. HLD answer skeleton (follow this order)

1. **Requirements** — functional (3–5 bullets) + non-functional (latency, scale,
   consistency, availability target).
2. **Back-of-envelope** — DAU → QPS → storage/year → bandwidth. Show the math.
3. **API design** — a handful of endpoints, request/response shape.
4. **Data model** — `erDiagram`, plus the *access patterns* that justify it.
5. **High-level architecture** — the main colored `flowchart`.
6. **Deep dive** — 2–3 components only, the ones an interviewer would probe.
7. **Bottlenecks & scaling** — mark them red, then fix them.
8. **Trade-offs** — a table: option A vs B, what we chose, why.

Always state the **consistency model** explicitly (strong / read-your-writes /
eventual) and where it changes across the system.

---

## 6. LLD answer skeleton

1. Clarify requirements + scope out what is *not* built.
2. Identify core entities → `classDiagram`.
3. Name the design patterns used and **why** (Strategy, State, Observer, Factory…).
4. Lifecycle via `stateDiagram-v2` if the object has states.
5. Code: interfaces first, then one meaty implementation. Keep it compilable.
6. Concurrency: what is shared, what is locked, what is immutable.
7. Extensibility: "if the interviewer adds requirement X, here's the seam."

Default language for LLD examples: **Java**, unless asked otherwise.
Default for DSA: **Python**.

---

## 7. Staff-level bar (calibrate answers to this)

A Senior answer designs the system. A **Staff** answer additionally:

- Picks the **simplest** design that meets the requirement, and says what it
  refused to build.
- Names **failure modes** and blast radius, not just the happy path.
- Talks about **migration**: how do we get here from an existing system, with
  zero downtime and a rollback path.
- Covers **operability**: what metric pages someone at 3am, what the SLO is.
- Discusses **cost** ($ and eng-time), and org/team boundaries around the design.
- Makes the **trade-off explicit** rather than presenting one true answer.

When reviewing my answer, grade it against these six and tell me which I missed.

---

## 8. How to work with me here

- Default mode is **teaching**: correct me, ask me the follow-up an interviewer
  would ask, and point out the weakest part of my answer.
- If I ask "design X", produce the full HLD skeleton in a new file under `hld/`.
- If I give an answer, **critique it** against §7 before agreeing with it.
- Keep responses in chat brief; put the long-form content in the markdown file
  and link it.
- No em-dashes in generated study notes; use short sentences instead.
- Don't add dependencies, build tooling, or CI to this repo. It's notes and code
  snippets only.
