# Book seller broker: diagram set

> One-line answer: trace seller selection, bounded fan-out, serialized aggregation, and the failure boundaries around a final answer.

Diagrams embedded elsewhere are linked rather than duplicated. Red identifies the seller-capacity bottleneck.

| ID | View | Location |
|---|---|---|
| D1 | Context | Below |
| D2 | Data flow | Below |
| D3 | Component architecture | [Solution §6](solution.md#6-final-design) |
| D4a | FR1 concurrent lookup | [Solution §4.1](solution.md#41-fr1-query-eligible-sellers-concurrently) |
| D4b | FR2 minimum and coverage | [Solution §4.2](solution.md#42-fr2-return-the-cheapest-valid-offer-with-coverage) |
| D4c | FR3 cancellation | [Solution §4.3](solution.md#43-fr3-bound-lifecycle-cancellation-and-retries) |
| D5a | Timeout and late response | Below |
| D5b | Broker crash | Below |
| D5c | Durable recovery | [Recovery timeline](deep-dives/crash-recovery.md#failure-timeline) |
| D6 | Reducer decisions | [Cutoff race](deep-dives/deadlines-and-aggregation.md#the-cutoff-and-finalization-race) |
| D7 | Entity relationship | Below |
| D8 | Query lifecycle | Below |
| D9 | Deployment | Below |
| D10 | Partitioning | Below |
| D11 | Failure map | Below |
| D12 | Rollout | Below |

## D1: Context

Buyer requests and seller quotes cross separate trust boundaries.

```mermaid
%% External actors and the data they exchange with the broker
flowchart LR
    C[Buyer] -->|ISBN and delivery context| B[Book seller broker]
    B -->|Best observed quote and coverage| C
    B -->|Quote requests and cancellation| S[Seller APIs]
    S -->|Prices, no stock, errors| B
    O[Integration operator] -->|Seller policy and contracts| B
    B -->|Health and quota incidents| O
    class C client
    class B service
    class S,O external
    classDef client fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

## D2: Data flow

The expensive edge is outbound fan-out, estimated before cache hits and rate denial.

```mermaid
%% Inputs become seller intents, normalized offers, and one comparison result
flowchart LR
    C[Buyer] -->|BookContext JSON 0.5 KB, 1200 per second peak| B(Select sellers)
    P[(Registry snapshot)] -->|Seller refs 2 KB each, local reads per query| B
    B -->|100 intents per query, 120k per second offered| A(Admit and dispatch)
    A -->|Quote JSON 0.5 KB, up to 120k per second primary| S[Seller APIs]
    S -->|Outcome JSON 1.5 KB assumed, admitted rate| R(Validate and reduce)
    A -->|Skipped outcome about 0.1 KB, overload dependent| R
    R -->|Final JSON about 1 KB, up to 1200 per second| C
    R -.->|Summary about 1 KB, bounded sample rate| O[(Operational summaries)]
    class C client
    class B,A,R service
    class P,O store
    class S external
    classDef client fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

## D5a: Seller timeout and late response

At 1.8 seconds the response freezes; a cheaper late quote cannot revise it.

```mermaid
%% One seller failure reduces coverage without blocking healthy outcomes
sequenceDiagram
    autonumber
    box rgb(219,234,254) Buyer
    participant C as Client
    end
    box rgb(220,252,231) Broker
    participant B as Query owner
    participant A as Adapter
    end
    box rgb(229,231,235) External
    participant S as Slow seller
    end
    C->>B: t=0.0 compare request
    B->>A: t=0.1 attempt with remaining deadline
    A->>S: t=0.1 outbound request
    Note over B: t=0.4 other sellers have valid quotes
    A->>A: t=1.6 seller timeout, no useful retry remains
    A-->>B: Terminal seller timeout
    B->>B: t=1.8 cutoff for other pending slots, freeze result
    B-->>C: t=1.8 to 2.0 PARTIAL and coverage
    B->>A: Cancel pending attempts
    S-->>A: t=1.9 late response if transport still alive
    A->>A: Ignore for settled slot and close transport
    Note over B,A: Metrics: seller timeout and cleanup lag; no per-query page
```

## D5b: Broker crash

Memory is lost; a retry is a new comparison subject to the same quotas.

```mermaid
%% A replacement broker cannot replay offers held only by the dead process
sequenceDiagram
    autonumber
    box rgb(219,234,254) Buyer and edge
    participant C as Client
    participant E as Edge
    end
    box rgb(220,252,231) Broker fleet
    participant A as Broker A
    participant B as Broker B
    end
    box rgb(229,231,235) External
    participant S as Sellers
    end
    C->>E: t=0.0 compare
    E->>A: Route request
    A->>S: t=0.1 admitted calls
    S-->>A: t=0.5 some offers
    Note over A: t=0.7 process dies, live offers lost
    E-->>C: t=0.7 to 2.0 reset or timeout
    Note over E: Transport or readiness probes remove failed broker
    C->>E: Permitted retry after bounded jitter
    E->>B: New query and deadline
    B->>S: Fresh calls after quota admission
    S-->>B: New observations
    B-->>E: New final result
    E-->>C: Response
    Note over A,B: On-call sees crashes, lost live queries, and retry amplification
```

## D7: Entity relationship

Query entities live in memory initially; durable mode persists them by query ID.

```mermaid
%% Keys correlate query, seller slots, attempts, and optional durable dispatch
%%{init: {"theme":"base","themeVariables":{"primaryColor":"#ede9fe","primaryTextColor":"#111","primaryBorderColor":"#7c3aed","lineColor":"#7c3aed"}}}%%
erDiagram
    SELLER ||--o{ SELLER_SLOT : selected_for
    QUERY ||--o{ SELLER_SLOT : contains
    SELLER_SLOT ||--o{ ATTEMPT : tries
    SELLER_SLOT ||--o| QUOTE : accepts
    QUERY ||--o{ OUTBOX : dispatches
    QUERY ||--o| IDEMPOTENCY : mapped_by
    SELLER {
        string seller_id PK
        string endpoint_ref
        string quota_contract_key
        string registry_version
    }
    QUERY {
        string query_id PK "partition seam"
        string tenant_id
        string context_hash
        string selected_set_version
        string state
        timestamp deadline "durable mode DB time"
        int version
        timestamp expires_at "24 h durable retention assumption"
    }
    SELLER_SLOT {
        string query_id PK,FK
        string seller_id PK,FK
        string terminal_outcome
        string accepted_attempt_id
    }
    ATTEMPT {
        string attempt_id PK
        string query_id FK
        string seller_id FK
        int attempt_number
        string transport_state
    }
    QUOTE {
        string query_id PK,FK
        string seller_id PK,FK
        string quote_id
        bigint total_minor
        string currency
        string price_basis
        timestamp observed_at
        timestamp valid_until
    }
    OUTBOX {
        string intent_id PK
        string query_id FK
        string seller_id FK
        string dispatch_state
        int owner_epoch
        timestamp claim_expires_at
    }
    IDEMPOTENCY {
        string tenant_id PK
        string idempotency_key PK
        string query_id FK
        string context_hash
        timestamp expires_at
    }
```

OUTBOX and IDEMPOTENCY apply only to durable mode. Baseline retention ends after response and bounded cleanup. Cached quotes use a full seller/context/version key, independent of a query's primary key.

## D8: State machine

Lifecycle and result quality are separate; FINAL can carry COMPLETE, PARTIAL, NO_OFFERS, or UNAVAILABLE.

```mermaid
%% One irreversible close transition; late events do not create transitions
stateDiagram-v2
    [*] --> RUNNING: validated and admitted
    RUNNING --> FINAL: all slots terminal or cutoff
    RUNNING --> CANCELLED: buyer cancellation wins
    FINAL --> [*]: response lifecycle ends
    CANCELLED --> [*]: cleanup supervised separately
    classDef service fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    class RUNNING service
    class FINAL,CANCELLED store
```

Baseline crashes lose this state. Durable retention expiry deletes records; it cannot reopen a finished query.

## D9: Deployment

Three AZs limit a broker/AZ failure's blast radius; one live query remains on one broker.

```mermaid
%% Regional topology and registry replication do not persist live query memory
flowchart TD
    E[Regional edge] -->|New queries| A[20 brokers]
    E -->|New queries| B[20 brokers]
    E -->|New queries| C[20 brokers]
    subgraph AZ_A[Region 1 AZ A]
        A
        P[(Registry primary)]
    end
    subgraph AZ_B[Region 1 AZ B]
        B
        R[(Registry standby)]
    end
    subgraph AZ_C[Region 1 AZ C]
        C
    end
    P -->|Synchronous WAL if configured| R
    A -->|Admission checks| Q[Shared quota authority]
    B -->|Admission checks| Q
    C -->|Admission checks| Q
    Q -->|Authorized dispatch through broker adapters| S[Seller APIs]
    P -.->|Async config backup, nonzero RPO| D[(Region 2 backup)]
    class E client
    class A,B,C,Q service
    class P,R,D store
    class S external
    classDef client fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

Quota checks and broker sends are folded into one logical dispatch arrow. The authority is partitioned across AZs with the [quota failover policy](deep-dives/seller-limits-and-scale.md#practical-redis-option-and-hard-contract-option). A standby needs a managed/fenced promotion mechanism; replication alone is not safe failover. No live query state crosses regions in the baseline.

## D10: Scaling and partitioning

Query ownership and quota admission use different keys.

```mermaid
%% Hashing query IDs cannot split a seller's shared commercial limit
flowchart LR
    E[Edge] -->|Load-balanced query IDs| B1[Broker group 1]
    E -->|Load-balanced query IDs| B2[Broker group 2]
    B1 -->|Hash seller contract key| Q1[Quota shard 1]
    B2 -->|Hash seller contract key| Q2[Quota shard 2]
    B1 -->|Common seller key| H[Hot seller quota key]
    B2 -->|Same common seller key| H
    H -->|Mitigation: reduce calls before admission| C[Seller-context reuse and coalescing]
    C -->|Only admitted unique lookups| S[Seller API]
    class E client
    class B1,B2,Q1,Q2,C service
    class H critical
    class S external
    classDef client fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

The mitigation edge is not runtime ordering: reuse occurs before quota consumption. Independent full-rate counters per shard violate the contract; allocated shares need a common total bound.

## D11: Failure mode map

Each failure maps to its user-visible effect and mitigation.

```mermaid
%% Failures have explicit blast radii and bounded responses
flowchart TD
    X[Comparison failure] -->|Slow dependency| S[Seller]
    X -->|Process exits| B[Broker]
    X -->|Admission uncertain| Q[Quota authority]
    X -->|Optimization unavailable| C[Quote cache]
    S -->|Missing subset of offers| SP[Partial result and seller bulkhead]
    B -->|Live queries on process lost| BP[Bounded retry on healthy broker]
    Q -->|Affected calls cannot be admitted| QP[Fail closed and expose skipped coverage]
    C -->|More live demand| CP[Retain caps and shed excess]
    class X,S,B,Q,SP,BP,QP,CP service
    class C cache
    classDef service fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef cache fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#111
```

## D12: Rollout

Illustrative phases include rollback gates; dates do not schedule a real deployment.

```mermaid
%% Recorded outcomes precede quota-safe live canaries
%%{init: {"theme":"base","themeVariables":{"primaryColor":"#dcfce7","primaryTextColor":"#111","primaryBorderColor":"#16a34a","taskTextColor":"#111","taskTextOutsideColor":"#111"}}}%%
gantt
    title Example broker migration
    dateFormat YYYY-MM-DD
    axisFormat %d %b
    section Contract
    Outcome schema and deadline metrics :a1, 2026-09-14, 2d
    Rollback response adapter :milestone, r1, after a1, 0d
    section Isolation
    Bounded adapters on recorded responses :a2, after a1, 2d
    Rollback adapter version :milestone, r2, after a2, 0d
    section Admission
    Global quota with conservative policy :a3, after a2, 2d
    Rollback to safe static shares :milestone, r3, after a3, 0d
    section Live traffic
    Canary 1 then 5 then 25 percent :a4, after a3, 3d
    Rollback routing and cache version :milestone, r4, after a4, 0d
    Expand after peak-period validation :a5, after a4, 2d
    Rollback to proven version :milestone, r5, after a5, 0d
```

## Technology internals

### Async HTTP runtime

Socket readiness uses small event-loop slices; blocking SDKs need isolated workers.

```mermaid
%% Event-loop threads share work while transport resources remain bounded
flowchart LR
    Q[Query tasks] -->|Admitted attempt| P[Connection pool]
    P -->|Socket readiness| E[Event loop]
    E -->|Bounded parse work| V[Validation]
    V -->|Typed outcome| R[Reducer]
    Q -->|Blocking SDK only| W[Small isolated pool]
    W -->|Typed outcome| R
    class Q,P,E,V,R,W service
    classDef service fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
```

### Redis admission

Primary atomicity and failover safety are distinct guarantees.

```mermaid
%% A shard serializes seller-key scripts but may replicate debits asynchronously
flowchart LR
    B[Broker] -->|Seller key and attempt admission| A[Quota service]
    A -->|Atomic refill and debit| P[(Redis primary shard)]
    P -->|Allow or deny| A
    A -->|Admission outcome| B
    P -.->|Async replication, possible lost debits| R[(Replica)]
    class B,A service
    class P,R store
    classDef service fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
```

### PostgreSQL state

Durable outcomes and finalizers lock the same query row and commit together.

```mermaid
%% WAL-backed transactions persist registry changes or optional query outcomes
flowchart LR
    A[Registry writer or durable worker] -->|Transaction and required row locks| T[Transaction]
    T -->|Rows and indexes| P[(Pages and buffers)]
    T -->|Commit records| W[(Write-ahead log)]
    W -->|Flush and configured replication ack| C[Commit acknowledgement]
    W -->|Replication records| R[(Standby replay)]
    C -->|Committed version| A
    class A,T,C service
    class P,W,R store
    classDef service fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
```
