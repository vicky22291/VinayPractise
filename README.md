# Staff Engineer Interview Prep

Study repo for HLD, LLD, distributed systems concepts, DSA, and behavioral prep.
Everything is explained with **colored Mermaid diagrams** and plain language.

Read `CLAUDE.md` for the answer style, color legend, and templates.

| Folder | What lives here |
|---|---|
| `hld/` | System design case studies |
| `lld/` | Object-oriented design problems |
| `concepts/` | Reusable building blocks (CAP, sharding, Kafka, caching, consensus) |
| `problem_solving/` | DSA patterns and solutions (Python) |
| `behavioral/` | Staff-level STAR stories |
| `templates/` | Templates + canonical color legend |

## Color legend

```mermaid
flowchart LR
    C[Client / Edge] --> S[Service] --> D[(Database)]
    S -.-> K[/Cache/]
    S --> Q[[Queue]]
    S --> X[Bottleneck / SPOF]
    S -.-> E[Third-party]
    S --> T{Trade-off}

    class C client
    class S service
    class D store
    class K cache
    class Q queue
    class X critical
    class E external
    class T decision

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef cache    fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

## How to study here

1. Ask for a design: *"design a rate limiter"* -> a file appears in `hld/` or `lld/`.
2. Try answering first, then ask for a critique against the Staff bar in `CLAUDE.md` §7.
3. Concepts you keep tripping on go into `concepts/` as one-page notes.
