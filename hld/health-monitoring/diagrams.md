# Diagrams: Server-health monitoring and alerting

The D1 to D12 set from `hld/CLAUDE.md` §4. A diagram is drawn once: the ones embedded in [`solution.md`](solution.md) are linked here, not repeated.

| # | Diagram | Where |
|---|---|---|
| D1 | Context | below |
| D2 | Data flow | below |
| D3 | Component architecture (final design) | `solution.md` §6 |
| D4 | Happy path per FR | FR1, FR3, FR5 disk fills to a ticket: `solution.md` §6 Flow 1. FR4 one server dies: §6 Flow 2. FR2 dashboard range query: below |
| D5 | Failure paths | Reconnect storm: `solution.md` §5.3. PDU fails: §6 Flow 3. Router partition: §6 Flow 4. Ingester OOM-killed, all evaluators die: below |
| D6 | Decision flow | Liveness verdict per host: `solution.md` §5.5. Alert router pipeline: §10.1. Remediation safety budget: below |
| D7 | Entity relationship | `solution.md` §3.3 |
| D8 | State machine | Host health: `solution.md` §4.4. Alert and incident lifecycle: below |
| D9 | Deployment / topology | One region: below. Cross-region watchers: `solution.md` §5.7 |
| D10 | Scaling / partitioning | Zone-aware ring: `solution.md` §10.1. Failure-domain trees: §5.6. Hot tenant and the limit: below |
| D11 | Failure mode map | below, split into metrics path and alert path |
| D12 | Rollout / migration | below |

---

## D1. Context (zoom-out)

```mermaid
%% D1: context. Our system is one box, deployed as 10 regional stacks. Servers feed it, teams configure it, on-call and the repair system act on what it says.
flowchart LR
    SRV[500k servers<br/>agent on each] -->|"metrics every 10 s,<br/>heartbeat every 5 s"| SYS[Health monitoring system<br/>10 regional stacks]
    TEAMS[Service teams] -->|"rules and silences via git"| SYS
    ENG[Engineers] -->|"dashboard queries"| SYS
    INV[(Asset inventory<br/>DC ops)] -->|"topology change feed"| SYS
    SYS -->|"pages with dedup_key"| PD[PagerDuty, chat, tickets]
    PD -->|"page or ticket"| ONC[On-call rotations]
    SYS -->|"HostStateChanged"| REP[Repair system<br/>fleet team]
    SYS -->|"Watchdog every 1 min"| DMS[External dead man's switch]

    class SRV,TEAMS,ENG,ONC client
    class SYS,REP service
    class INV store
    class PD,DMS external

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

## D2. Data flow (DFD)

```mermaid
%% D2: data flow for one region (50k hosts). Names, formats, sizes and rates on every edge. Red: ingesters.
flowchart LR
    AG([Agent]) -->|"push, protobuf + snappy ~2 KB,<br/>5k/s, ~10 MB/s"| DIST([Distributors])
    DIST -->|"samples x3,<br/>1.5M writes/s"| ING([Ingesters]):::critical
    ING -->|"2 h blocks,<br/>~180 GB/day before dedup"| OBJ[(Object storage)]
    OBJ <-->|"merge, keep 1 of 3,<br/>~60 GB/day raw + rollups"| COMP([Compactor])
    ING -->|"range results,<br/>~130 QPS, ~40 after cache"| QF([Query path])
    ING -->|"instant query results,<br/>220 evals/s"| EV([Evaluators])
    AG -->|"heartbeat, UDP 64 B,<br/>30k/s to 3 replicas"| LIV([Liveness x3])
    LIV -->|"silent-set bitmap 6 KB,<br/>1/s per replica"| COR([Correlator x3])
    TOPO[(Topology)] -->|"domain trees ~50 MB,<br/>change feed"| COR
    EV -->|"alerts, ~2k firing"| AR([Alert router x3])
    COR -->|"verdicts, a few DOWN/day<br/>per region"| AR
    COR -->|"HostStateChanged ~200 B"| REP([Repair system])
    AR -->|"Events API v2,<br/>at most 2 pages per shift"| PD([PagerDuty])

    class AG client
    class DIST,COMP,QF,EV,LIV,COR,AR,REP service
    class OBJ,TOPO store
    class PD external

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
```

Push rate: 500k hosts / 10 s = 50k pushes/s globally, 5k/s per region. Heartbeats: 50k hosts / 5 s × 3 replicas = 30k/s per region. Blocks leave the ingesters 3 times (RF 3) and the compactor keeps one copy.

## D4. FR2 dashboard range query (happy path)

```mermaid
%% D4 (FR2): a 7-day panel. Finished days come from the cache, today is split between ingester memory and store gateways, replicas are deduped by timestamp.
sequenceDiagram
    autonumber
    participant U as Dashboard
    participant F as Query frontend
    participant C as Results cache
    participant Q as Querier
    participant I as Ingesters
    participant S as Store gateways
    participant O as Object storage
    U->>F: avg cpu by rack in cluster c2, last 7 days, step 5 min
    F->>F: split into 7 one-day sub-queries, align the step
    F->>C: look up the 6 finished days
    C-->>F: 6 hits
    F->>Q: today only
    Q->>I: last 13 h from the in-memory head
    Q->>S: 13 h to 24 h ago
    S->>O: fetch chunks, index-headers are local
    I-->>Q: up to 3 replicas per series
    S-->>Q: chunks for older hours
    Q->>Q: dedup replicas by timestamp, evaluate PromQL
    Q-->>F: today
    F-->>U: 7 days merged, under 1 s
```

## D5. Ingester OOM-killed mid-write

```mermaid
%% D5: failure path. One of the 3 replicas dies. Quorum 2 of 3 still holds, so agents see nothing. WAL replay brings it back.
sequenceDiagram
    autonumber
    participant A as Agents
    participant D as Distributor
    participant I1 as Ingester c1-3
    participant I2 as Ingester c2-1
    participant I3 as Ingester c3-4
    participant Q as Queriers
    A->>D: push batch
    D->>I1: write
    Note over I1: t0 OOM-killed
    D->>I2: write
    D->>I3: write
    I2-->>D: ack
    I3-->>D: ack
    D-->>A: 200, quorum 2 of 3 met
    Note over D,I1: t0 + ~1 min memberlist marks c1-3 unhealthy
    Q->>I2: queries skip c1-3
    Q->>I3: dedup the 2 remaining copies
    I1->>I1: t0 + 2 to 5 min, restart and replay WAL
    I1->>D: rejoins the ring
    Note over I1,I3: its gap is filled at query time and by the compactor merge
```

## D5. All rule evaluators die

```mermaid
%% D5: failure path. Every evaluator crashloops. Firing alerts expire and resolve, which looks like health. The Watchdog and the watcher canaries make the silence loud.
sequenceDiagram
    autonumber
    participant E as Evaluators
    participant R as Alert router
    participant D as Dead man's switch
    participant W as Watcher regions
    participant O as Monitoring on-call
    E->>R: DiskFull firing, valid_until t0 + 4 min
    E->>R: Watchdog rule, always firing
    R->>D: Watchdog every 1 min
    Note over E: t0 bad release, every evaluator crashloops
    W->>E: canary read-back fails from t0 + 10 s
    W->>O: t0 + 2 to 3 min, page, Region R monitoring blind
    R->>R: t0 + 4 min, DiskFull and Watchdog pass valid_until
    R->>O: DiskFull resolve, misleading on its own
    D->>O: Watchdog missing 5 min, SMS via second provider
    Note over R,O: liveness verdicts keep working, correlators do not use evaluators
```

## D6. Remediation safety budget

```mermaid
%% D6: decision flow before automation takes a live host out of service. Dead hosts skip the budget. Anything outside the budget stops automation and pages a human.
flowchart TD
    V[Verdict for host h] --> L{Host still live?<br/>heartbeats arrive}
    L -->|"no, DOWN"| DEAD[Mark unschedulable,<br/>ticket, no budget used]
    L -->|"yes, UNHEALTHY"| S{Target set empty<br/>or over 1,000 hosts?}
    S -->|"yes"| HALT[Stop automation,<br/>page: automation halted]
    S -->|"no"| C{Cluster drains under 1 pct<br/>and under 5 racks?}
    C -->|"no"| HALT
    C -->|"yes"| F{Fleet drains this hour<br/>under 0.5 pct?}
    F -->|"no"| HALT
    F -->|"yes"| DR[Drain h, then reboot or reimage,<br/>attempt row before each step]

    class V,DEAD,DR service
    class L,S,C,F decision
    class HALT external

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

## D8. Alert lifecycle

```mermaid
%% D8: one alert label set inside an evaluator. for gives Pending, keep_firing_for stops a hovering metric from resolving and re-firing.
stateDiagram-v2
    direction LR
    [*] --> Inactive
    Inactive --> Pending: expr true
    Pending --> Inactive: expr false
    Pending --> Firing: true for the full for
    Firing --> KeepFiring: expr false
    KeepFiring --> Firing: expr true again
    KeepFiring --> Resolved: keep_firing_for ends
    Resolved --> [*]
```

## D8. Incident lifecycle at the pager

```mermaid
%% D8: one incident keyed by dedup_key. A duplicate trigger from a partitioned router replica lands on the same incident.
stateDiagram-v2
    direction LR
    [*] --> Triggered: first send, key k
    Triggered --> Triggered: same key, appended
    Triggered --> Acknowledged: on-call acks
    Triggered --> Escalated: no ack in time
    Escalated --> Acknowledged: secondary acks
    Acknowledged --> Resolved: resolve event
    Triggered --> Resolved: resolve event
    Resolved --> [*]
```

## D9. Deployment / topology

```mermaid
%% D9: one region, repeated 10 times. Every component has a replica in each of the region's 3 clusters. Only canaries, global queries, pages and replicated blocks cross the region boundary.
flowchart LR
    subgraph REG[Region R]
        subgraph C1[Cluster c1]
            S1[Distributors,<br/>query path, evaluators]
            I1[Ingesters x5]:::critical
            L1[Liveness, correlator,<br/>router, probers]
        end
        subgraph C2[Cluster c2]
            S2[Distributors,<br/>query path, evaluators]
            I2[Ingesters x5]:::critical
            L2[Liveness, correlator,<br/>router, probers]
        end
        subgraph C3[Cluster c3]
            S3[Distributors,<br/>query path, evaluators]
            I3[Ingesters x5]:::critical
            L3[Liveness, correlator,<br/>router, probers]
        end
        OBJ[(Regional object storage)]
    end
    S1 -->|"RF 3, one per cluster"| I1
    S1 -->|"RF 3"| I2
    S1 -->|"RF 3"| I3
    I2 -->|"2 h blocks"| OBJ
    L1 <-->|"gossip log, silences"| L2
    L2 <-->|"gossip"| L3
    OBJ -->|"async block replication"| DR[(Blocks replica,<br/>other region)]
    WATCH[Watcher regions R+1, R+2] <-->|"canary push and read-back"| S2
    GQ[Global query layer] -->|"fan-out, partial if missing"| S3
    L3 -->|"pages"| PD[PagerDuty]

    class S1,S2,S3,L1,L2,L3,WATCH,GQ service
    class OBJ,DR store
    class PD external

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
```

Each distributor pod writes every series to one ingester in each cluster; only c1's edges are drawn. Losing a whole cluster leaves 2 of 3 replicas of every component.

## D10. Hot tenant and the limit

```mermaid
%% D10: the series hash spreads a tenant's series over all 15 ingesters, so an explosion is not one hot shard to move: every ingester grows together. The fix sits before the ring.
flowchart LR
    T1[Tenant infra<br/>5M series, stable] -->|"hash tenant + labels"| DIST[Distributors<br/>per-tenant 8M,<br/>per-metric 500k]
    T2[Tenant team-x<br/>new flow_id label,<br/>series x50] -->|"new-series burst"| DIST
    SCH[Agent schema allowlist] -->|"unknown labels dropped<br/>on the host"| T2
    DIST -->|"within limits,<br/>spread over the ring"| ING[Ingesters x15<br/>~1M series each,<br/>hard series cap]:::critical
    DIST -->|"past the limit:<br/>4xx on new series only"| REJ[Rejected, loud,<br/>attributed to team-x]
    DIST -->|"new-series-rate alert"| TIX[Ticket to team-x]

    class T1,T2,SCH client
    class DIST service
    class REJ,TIX external

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
```

Existing series keep working when the limit trips; only new series are refused. Shuffle sharding (pinning each tenant to a subset of ingesters, as Mimir can) would shrink the blast radius further; it is an option, not part of the chosen design.

## D11. Failure mode map: metrics path

```mermaid
%% D11a: metrics path. Component failure, blast radius, mitigation. Red: the ingester tier.
flowchart TD
    ROOT[Metrics path]
    ROOT --> F1[Agent crashes<br/>or bad release]
    ROOT --> F2[Distributors down<br/>or misconfigured]
    ROOT --> F3[Ingester OOM or<br/>cardinality blow-up]:::critical
    ROOT --> F4[Object storage<br/>slow or down]
    F1 --> B1[One host AGENT_DEAD,<br/>MassSilence if fleet-wide]
    F2 --> B2[Region writes fail,<br/>agents buffer up to 2 h]
    F3 --> B3[One pod: nothing.<br/>Tier-wide: dashboards and rules blind]
    F4 --> B4[History and compaction stall,<br/>alerts unaffected]
    B1 --> M1[Probes + BMC, release by cluster,<br/>mass-silence gate]
    B2 --> M2[Lag guard at 30 s, watcher canary,<br/>config rollback]
    B3 --> M3[RF 3 by cluster, tenant and<br/>metric limits, ingester cap]
    B4 --> M4[Ingesters serve 13 h,<br/>block upload retries]

    class ROOT,M1,M2,M3,M4 service
    class F1,F2,F4 decision
    class B1,B2,B3,B4 external

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
```

## D11. Failure mode map: alert path

```mermaid
%% D11b: alert path. Each node pairs the failure with its blast radius and mitigation.
flowchart TD
    ROOT[Alert path]
    ROOT --> E[All evaluators down]
    ROOT --> L[One liveness replica<br/>partitioned or paused]
    ROOT --> C[Correlator bug<br/>or stale topology]
    ROOT --> R[Router replica<br/>partitioned]
    ROOT --> P[PagerDuty down]
    E --> EB[Alerts expire in 4 min and resolve.<br/>Watchdog and canaries page]
    L --> LB[Nothing: 2 of 3 quorum.<br/>Self-check abstains]
    C --> CB[Wrong grouping or verdicts.<br/>Remediation budget caps damage]
    R --> RB[Maybe a duplicate send.<br/>dedup_key keeps one incident]
    P --> PB[Failures over 1 pct page via<br/>second provider, DMS uses SMS]

    class ROOT,EB,LB,CB,RB,PB service
    class E,L,C,R,P decision

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

## D12. Rollout and migration

```mermaid
%% D12: from per-datacenter Prometheus and Nagios to regional stacks. Every phase rolls back by switching a receiver or pinning a version.
gantt
    title Migration to regional health monitoring
    dateFormat YYYY-MM-DD
    section Collect
    Agent with dual export, one cluster then fleet     :a1, 2026-10-05, 21d
    Regional stacks live, dashboards only              :a2, after a1, 14d
    section Alerts
    Shadow router, diff pages against the old system   :b1, after a2, 14d
    Team by team cutover, rules backtested in CI       :b2, after b1, 42d
    Old system read-only, then off                     :b3, after b2, 30d
    section Liveness and repair
    Verdicts ticket-only, false DOWN measured by boot_id :c1, after a2, 30d
    Repair automation at 0.1 pct budget                :c2, after c1, 21d
    Raise budget to 1 pct of a cluster                 :c3, after c2, 14d
```

Rollback points: a1 pins the old agent version, b1 and b2 switch the receiver back to the old system, c2 and c3 set the budget to 0. Nothing is destructive.
