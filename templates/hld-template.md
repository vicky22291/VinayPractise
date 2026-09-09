# HLD: <System Name>

> One-line answer: <what I would build, in a single sentence>

## 1. Requirements

**Functional**
- ...

**Non-functional**
| Dimension | Target |
|---|---|
| Scale | X DAU, Y QPS read / Z QPS write |
| Latency | p99 read < ..ms, write < ..ms |
| Availability | 99.9% / 99.99% |
| Consistency | strong / read-your-writes / eventual |
| Durability | ... |

**Out of scope:** ...

## 2. Back-of-envelope

```
DAU              = ...
Reads/user/day   = ...  -> read QPS  = ... (peak = 3x avg)
Writes/user/day  = ...  -> write QPS = ...
Row size         = ...  -> storage/yr = ...
Read:write ratio = ...  -> implication: ...
```

## 3. API

| Method | Path | Body / Params | Returns |
|---|---|---|---|
| POST | /v1/... | ... | ... |

## 4. Data model

```mermaid
erDiagram
    USER ||--o{ ITEM : owns
    USER { string id PK }
    ITEM { string id PK  string user_id FK }
```

Access patterns this model serves:
- ...

Partition key: `...` — chosen because ...

## 5. Architecture

```mermaid
%% End-to-end request path
flowchart LR
    U[Client] --> LB[API Gateway]
    LB --> S[Service]
    S --> DB[(Primary DB)]
    S -.cache miss.-> R[/Redis/]
    S --> Q[[Kafka]]

    class U,LB client
    class S service
    class DB store
    class R cache
    class Q queue

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef cache    fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

## 6. Deep dive

### 6.1 <Component the interviewer will probe>
```mermaid
sequenceDiagram
    autonumber
    participant C as Client
    participant S as Service
    participant D as DB
    C->>S: request
    S->>D: write
    D-->>S: ack
    S-->>C: 200
```
- ...

## 7. Bottlenecks and scaling

| # | Bottleneck | Symptom | Fix |
|---|---|---|---|
| 1 | ... | ... | ... |

## 8. Trade-offs

| Decision | Option A | Option B | Chose | Why |
|---|---|---|---|---|
| ... | ... | ... | ... | ... |

## 9. Staff-level notes
- **Failure modes / blast radius:** ...
- **Migration path from today:** ...
- **Operability:** SLO ..., alert on ..., dashboard shows ...
- **Cost:** ...
- **Team boundaries:** who owns what.

## 10. Follow-up questions to expect
- ...
