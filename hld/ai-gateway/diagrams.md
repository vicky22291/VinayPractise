# Diagrams: AI gateway for thousands of tenants

The D1 to D12 set from `hld/CLAUDE.md` §4. Diagrams already embedded in [`solution.md`](solution.md) are listed with a pointer, not pasted twice. Red is used for one thing only: the shared provider quota, the resource that breaks first (solution §5.2, §7, §10.3).

| # | Diagram | Where |
|---|---|---|
| D1 | Context | below |
| D2 | Data flow | below |
| D3 | Component architecture (final design) | `solution.md` §6 |
| D4 | Happy path per FR | FR1 to FR4 end to end: §6 Flow 1. FR2 identity detail: below. FR3 budget at the cap: §6 Flow 2; lease protocol: below. FR4 streaming, simple version: §4.4. FR5 MCP tool call: §5.5. FR6 usage and tracing: below |
| D5 | Failure paths | Provider error before the first token: §5.3. Client disconnect: §6 Flow 4. Quota shard dies: §6 Flow 7. Provider region outage and Envoy pod crash: §10.4. Bad policy snapshot: below |
| D6 | Decision flow | Admission per LLM request: §5.1. Routing and fallback: §5.4. SSE parser: §10.1 |
| D7 | Entity relationship | `solution.md` §3.3 |
| D8 | State machine | One LLM request: below. A principal's budget: [`deep-dives/token-budgets-and-rate-limiting.md`](deep-dives/token-budgets-and-rate-limiting.md) |
| D9 | Deployment / topology | below |
| D10 | Scaling / partitioning | below |
| D11 | Failure mode map | below |
| D12 | Rollout / migration | below |

---

## D1. Context (zoom-out)

```mermaid
%% D1: the gateway as one box. Callers on the left, identity and admins above, everything it spends money on or reaches on the right.
flowchart LR
    APP[Tenant apps and SDKs<br/>OpenAI-compatible] -->|"chat, embeddings, 20k req/s peak"| GW[AI gateway<br/>3 regions, 72 Envoy pods]
    AG[Coding agents, IDEs<br/>MCP clients] -->|"MCP Streamable HTTP, 20k req/s peak"| GW
    ADM[Tenant admins] -->|"keys, limits, budgets, aliases, MCP registry"| GW
    IDP[Tenant identity providers] -.->|"JWKS for OAuth and OIDC tokens"| GW
    GW -->|"translated requests, SSE back"| PROV[Model providers<br/>about 200 deployments]
    GW -->|"OpenAI-format requests"| SH[Self-hosted model pools]
    GW -->|"tool calls with user credentials"| MCP[MCP servers<br/>managed and tenant-registered]
    GW -->|"usage records, 1.4 TB/day"| BI[(Billing and analytics<br/>Delta tables)]
    GW -->|"upstream tokens, provider keys"| VA[(Vault)]

    class APP,AG,ADM client
    class GW service
    class BI,VA store
    class IDP,PROV,SH,MCP external

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

## D2. Data flow (DFD)

```mermaid
%% D2: what flows where at peak, with format, size and rate. Processes are rounded, stores are cylinders.
flowchart LR
    C[Clients] -->|"chat request, JSON 12 KB mean, 20k/s"| G(Envoy + AI module)
    G -->|"translated request, JSON 12 KB, 20k/s"| P[Providers]
    P -->|"SSE events, 200 B each, 1.3M/s"| G
    G -->|"SSE events, 1.3M/s, 2.6 Gbps"| C
    C -->|"MCP JSON-RPC, 2 KB, 20k/s"| G
    G -->|"tool calls, 16k/s after catalog cache"| M[MCP servers]
    G -->|"Grant on miss, 200 B, about 5k/s"| Q[(Quota Service)]
    G -->|"Commit batches, about 50 records each"| Q
    F(Policy feed) -->|"deltas, 1 KB, about 1/s"| G
    S[(Snapshot store)] -->|"snapshot, 60 MB, at boot"| G
    G -->|"usage record, 1 KB protobuf, 40k/s"| K[[Kafka usage.v1<br/>40 MB/s peak]]
    K -->|"records, 1.4 TB/day"| J(Stream job)
    J -->|"columnar, 150 GB/day"| D[(Delta usage tables)]
    D -->|"day and month spend, on cold start"| Q

    class C client
    class G,J,F service
    class Q,S,D store
    class K queue
    class P,M external

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

## D3. Component architecture

The final design is in [`solution.md` §6](solution.md#6-final-design-and-the-seven-core-flows). Zoom-ins: filter chain in §5.6, control plane in §5.7, multi-region in §5.8, module threads and Quota shard in §10.1.

## D4. Happy path per functional requirement

### D4, FR2: identity and grants

```mermaid
%% D4 (FR2): both credential kinds. JWTs are verified by the native filter; API keys by the module from the snapshot. Neither makes a network call.
sequenceDiagram
    autonumber
    participant C as Client
    participant J as jwt_authn (native)
    participant M as AI module
    participant S as Policy snapshot (in process)
    C->>J: Authorization Bearer credential
    alt credential is a JWT from a tenant IdP
        J->>J: verify signature with cached JWKS, iss, aud is the gateway, exp
        J->>M: claims in dynamic metadata
        M->>S: map iss and sub to principal
    else credential is an sk-gw API key
        J->>M: not a JWT, rule allows it through
        M->>M: SHA-256 of the key
        M->>S: key_hash lookup
        S-->>M: key_id, tenant T, principal p, status active
    end
    M->>S: principal p to groups to grants
    alt alias not granted, or key revoked
        M-->>C: 403 with reason code
    else granted
        M->>M: continue to admission (solution 5.1)
    end
    Note over M,S: the snapshot is swapped in the background when a delta arrives. The module rejects any request with neither a verified JWT nor a valid key
```

### D4, FR3: the lease protocol

```mermaid
%% D4 (FR3): leases for one key active on two pods. Grants on cold start and at 50%, commits every 100 ms, exact mode near the cap.
sequenceDiagram
    autonumber
    participant A as Module on pod A
    participant B as Module on pod B
    participant Q as Quota shard for tenant T
    A->>Q: Grant key k, want 60k tokens, 1.20 dollars, 4 slots
    Q-->>A: granted in full, ttl 10 s, mode lease
    loop each request on pod A
        A->>A: reserve estimate locally, 2 us
    end
    B->>Q: Grant key k (k is now active on B too)
    Q-->>B: granted, sized as remaining over 2 x pods holding k
    A->>Q: refill at 50 percent, in the background
    Q-->>A: granted
    A->>Q: Commit batch with request_ids, actual usage, slots returned
    B->>Q: Commit batch
    Q->>Q: remaining below headroom + 10 requests, switch k to exact mode
    Q-->>A: next reply says mode exact
    A->>Q: Grant per request for the worst case, in + max_tokens
    Q-->>A: granted or denied
```

### D4, FR6: usage record and trace

```mermaid
%% D4 (FR6): one request's usage from the module to invoices. Access log and trace share x-request-id.
sequenceDiagram
    autonumber
    participant M as AI module
    participant E as Envoy access log and tracer
    participant O as OTel collector (node-local)
    participant K as Kafka usage.v1
    participant J as Stream job
    participant D as Delta tables
    M->>E: dynamic metadata, tokens by type, cost, deployment, tags, estimated flag
    E->>O: access log record, 1 KB, at stream end
    E->>O: spans for gateway, attempts, upstream
    O->>K: batch every 200 ms, key tenant_id, acks all
    K->>J: consume
    J->>J: check price table version, recompute cost if it changed
    J->>D: MERGE usage_events on date and request_id
    J->>D: update usage_by_principal_day
    D-->>M: nothing direct, dashboards and invoices read D, Quota Service rebuilds from D
```

## D5. Failure path: a bad policy snapshot

```mermaid
%% D5 (failure): an admin bulk operation would revoke 40% of a tenant's keys. The compiler's blast limit holds it; if a bad version ships anyway, rollback is one publish.
sequenceDiagram
    autonumber
    participant A as Admin script
    participant CP as Config API and compiler
    participant O as On-call and tenant owner
    participant F as Policy feed
    participant M as Modules on 72 pods
    A->>CP: bulk revoke, 4,000 of 10,000 keys of tenant T
    CP->>CP: blast limit check, over 10 percent of a tenant's keys in one change
    CP->>O: hold the delta, ask for approval
    alt approved
        O->>CP: approve
        CP->>F: publish version v+1
        F->>M: delta within 1 s
    else rejected
        O->>CP: reject, nothing published
    end
    Note over CP,M: if a bad version ships anyway, CP publishes v+2 equal to v. Pods apply it within 2 s. Quota grants for wrongly revoked keys resume at the next grant
```

## D6. Decision flows

Admission per LLM request: [`solution.md` §5.1](solution.md#51-how-do-you-rate-limit-tokens-when-output-tokens-are-known-only-at-stream-end-reserve-lease-reconcile). Routing and fallback: [§5.4](solution.md#54-route-across-200-deployments-fail-over-and-keep-prompt-caches-warm-routing-and-fallback). SSE parser: [§10.1](solution.md#101-internals-of-each-chosen-technology).

## D7. Entity relationship

In [`solution.md` §3.3](solution.md#33-data-model), with primary keys, partition keys and TTLs.

## D8. State machine: one LLM request

```mermaid
%% D8: lifecycle of one LLM request in the module. Settled states say what the counter learns: actual usage, an estimate, or a released reservation.
stateDiagram-v2
    direction LR
    [*] --> Received
    Received --> Admitted: reserved
    Received --> Queued: deployment full
    Received --> Rejected: 401, 403, 429
    Queued --> Admitted: slot freed
    Queued --> Rejected: wait timeout
    Admitted --> Attempting: route chosen
    Attempting --> Attempting: retriable, next
    Attempting --> Streaming: first event out
    Attempting --> Failed: attempts used up
    Streaming --> Completed: usage seen
    Streaming --> Aborted: disconnect, reset
    Completed --> Committed: commit actual
    Aborted --> Estimated: commit estimate
    Failed --> Released: return reserve
    Rejected --> [*]
    Committed --> [*]
    Estimated --> [*]
    Released --> [*]

    classDef service fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef queue fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef store fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef cache fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
    class Received,Admitted,Attempting,Streaming service
    class Queued queue
    class Completed,Committed store
    class Aborted,Estimated cache
    class Rejected,Failed,Released external
```

## D9. Deployment / topology

```mermaid
%% D9: three regions, each a full stack. What crosses a region boundary: config replication, async replicas of quota shards, cross-region grants for remote traffic. EU usage never leaves the EU.
flowchart LR
    DNS[GeoDNS + L4 LBs] -->|"nearest healthy"| EENV
    DNS -->|"nearest healthy"| WENV
    DNS -->|"EU-pinned tenants"| UENV
    subgraph EAST["Region east"]
        EENV[Envoy: 8 cells x 3 pods<br/>one pod per zone]
        EQS[(Quota: 16 shards<br/>primary zone a, sync replica zone b)]
        ECP[Control plane primary<br/>Postgres primary + sync standby]
        EK[[Kafka, RF 3 over 3 zones]]
    end
    subgraph WEST["Region west"]
        WENV[Envoy: 8 cells x 3 pods]
        WQS[(Quota: 16 shards)]
        WCP[Postgres replica, feed replica]
        WK[[Kafka, RF 3]]
    end
    subgraph EU["Region EU"]
        UENV[Envoy: 8 cells x 3 pods]
        UQS[(Quota: 16 shards, EU tenants)]
        UK[[Kafka, RF 3, EU data only]]
    end
    EENV -->|"grants, commits"| EQS
    EENV -->|"access logs"| EK
    ECP -.->|"xDS, policy feed"| EENV
    WENV -->|"grants, west tenants"| WQS
    WENV -->|"access logs"| WK
    UENV -->|"grants, commits"| UQS
    UENV -->|"access logs"| UK
    ECP -.->|"async replication, config"| WCP
    EQS -.->|"async replica of east-homed shards"| WQS
    WENV -->|"cross-region grant, 70 ms, refilled ahead"| EQS
    EK -->|"usage, non-EU tenants"| DL[(Delta, global)]
    UK -->|"usage, stays in EU"| DLU[(Delta, EU)]

    class DNS client
    class EENV,WENV,UENV,ECP,WCP service
    class EQS,WQS,UQS,DL,DLU store
    class EK,WK,UK queue

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
```

## D10. Scaling / partitioning

```mermaid
%% D10: capacity is partitioned into provider deployments. The partition key is the alias plus the affinity hash. The hot partition is red; the fix is leases, bounded load and spill. Quota Service shards by tenant hash and absorbs hot tenants with leases.
flowchart LR
    REQ[Requests for alias frontier-large] -->|"alias lookup"| MAP[Ordered clusters<br/>of the alias]
    MAP -->|"partition key: affinity hash"| RING[Ring hash<br/>bounded load 150%]
    RING -->|"45% of sessions"| D1[Deployment east<br/>20M TPM, 90% used at peak]
    RING -->|"30% of sessions"| D2[Deployment central<br/>15M TPM, 60% used]
    RING -->|"25% of sessions"| D3[Deployment west<br/>15M TPM, 55% used]
    D1 -->|"lease spent: queue, then spill"| D2
    FIX[Fix: lease caps east at 18M TPM,<br/>bounded load moves new sessions,<br/>fair queues share the rest] -.->|"applied to"| D1
    HOT[Hot tenant: 5k req/s on one key] -->|"big leases, batched commits"| QS[(Quota Service<br/>16 shards by hash of tenant_id)]
    QS -->|"deployment leases"| FIX

    class REQ,HOT client
    class MAP,RING,FIX service
    class QS store
    class D1 critical
    class D2,D3 external

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

Why the Quota Service is not the hot partition: a tenant at 5k req/s on one key makes about 30 grant RPCs/s (large leases, one per pod every few seconds) and at most 240 commit batches/s to its shard, well under 1% of a single-threaded shard's capacity (solution §10.3).

## D11. Failure mode map

```mermaid
%% D11: each component, how it fails, blast radius and mitigation. One tree.
flowchart TD
    ROOT[AI gateway region] -->|"pod OOM or crash"| F1[Envoy pod]
    ROOT -->|"bad build"| F2[AI module]
    ROOT -->|"process or zone loss"| F3[Quota shard]
    ROOT -->|"429 storm or outage"| F4[Provider deployment]
    ROOT -->|"down or partitioned"| F5[Control plane and feed]
    ROOT -->|"broker down"| F6[Kafka ledger]
    F1 -->|"blast and fix"| M1[7k to 11k streams break, clients retry.<br/>N+1 per zone, LB health checks in 3 s]
    F2 -->|"blast and fix"| M2[One cell, 1/8 of region.<br/>Cell canary, shuffle sharding, rollback image]
    F3 -->|"blast and fix"| M3[1 of 16 shards. Grants last 10 s,<br/>fail static, replica promoted in 5 s]
    F4 -->|"blast and fix"| M4[Aliases on it. Fallback before first byte,<br/>leases stop the fleet exceeding quota]
    F5 -->|"blast and fix"| M5[No config changes. Pods run the last<br/>snapshot and xDS config, page at 60 s lag]
    F6 -->|"blast and fix"| M6[Dashboards stale. Collectors buffer 1 h,<br/>counters unaffected]

    class ROOT client
    class F1,F2 service
    class F3 store
    class F4 critical
    class F5 service
    class F6 queue
    class M1,M2,M3,M4,M5,M6 decision

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

## D12. Rollout and migration

From tenants calling providers directly (or through an older proxy) to the gateway. Every phase is a per-tenant flag with its own rollback point.

```mermaid
%% D12: migration phases per tenant cohort, each with a rollback point.
gantt
    title Migration to the AI gateway
    dateFormat YYYY-MM-DD
    axisFormat %b %d
    section Phase 0 shadow
    Gateway in path for pilot tenants, limits logged only :p0, 2026-10-05, 14d
    Rollback point, SDK base URL back to provider :milestone, m0, after p0, 0d
    section Phase 1 cutover
    Cohorts of tenants move by base URL, 10 then 30 then 100 percent :p1, after p0, 21d
    Rollback point, per-tenant base URL flag :milestone, m1, after p1, 0d
    section Phase 2 budgets
    Daily budgets notify only :p2a, after p1, 14d
    Daily budgets enforced, then monthly caps :p2b, after p2a, 14d
    Rollback point, enforcement flag per tenant :milestone, m2, after p2b, 0d
    section Phase 3 MCP
    Registry in allow-all mode, observe tool use :p3a, after p1, 14d
    Narrow tool policies, per-user credentials :p3b, after p3a, 21d
    Rollback point, allow-all flag per tenant :milestone, m3, after p3b, 0d
    section Phase 4 routing
    Fallback aliases and cache-aware stickiness :p4, after p2b, 21d
    Rollback point, alias back to one deployment :milestone, m4, after p4, 0d
```
