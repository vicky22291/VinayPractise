# Diagrams: Driver hot clusters in a city

The D1 to D12 set from `hld/CLAUDE.md` §4. A diagram is drawn once: the ones embedded in [`solution.md`](solution.md) are linked here, not repeated.

| # | Diagram | Where |
|---|---|---|
| D1 | Context | below |
| D2 | Data flow | below |
| D3 | Component architecture (final design) | `solution.md` §6 |
| D4 | Happy path per FR | FR1 to FR3 ping to screen: `solution.md` §6 Flow 1. FR4 hourly export: §6 Flow 2. FR5 history query: below |
| D5 | Failure paths | Stream job restart: `solution.md` §6 Flow 3. Clock 1 h ahead: §5.2. Hourly completeness gate fails: below |
| D6 | Decision flow | Stage 2 per presence fact: `solution.md` §5.1. Stage 1 cell assignment with hysteresis: below |
| D7 | Entity relationship | `solution.md` §3.3 |
| D8 | State machine | Hour lifecycle, provisional to final to restated: below |
| D9 | Deployment / topology | below |
| D10 | Scaling / partitioning | below |
| D11 | Failure mode map | below |
| D12 | Rollout / migration | below |

---

## D1. Context (zoom-out)

```mermaid
%% D1: context. Our system is one box. Drivers feed it through the shared location stack. Ops, analysts and institutions read from it.
flowchart LR
    DRV[Driver apps<br/>1.5 M online] -->|"ping every 10 s"| LOC[Location stack<br/>gateway + Kafka, shared with dispatch]
    LOC -->|"driver-locations topic"| SYS[Hot clusters system]
    SYS -->|"heatmap, clusters, 10 s"| OPS[Ops teams, 500 cities]
    SYS -->|"SQL on per-minute counts"| AN[Analysts]
    SYS -->|"hourly files, aggregated"| INST[Institutions<br/>regulators, city DOTs]
    LEGAL[Privacy and legal] -.->|"k_min, contracts"| SYS

    class DRV,OPS,AN client
    class SYS service
    class LOC queue
    class INST,LEGAL external

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

## D2. Data flow (DFD)

```mermaid
%% D2: data flow with names, formats, sizes and rates on every edge.
flowchart LR
    APP([Driver app]) -->|"ping, protobuf ~60 B, 150k/s peak"| K[(Kafka topic)]
    K -->|"ping, 150k/s"| S1([Stage 1: dedup + grid])
    S1 -->|"presence, ~40 B, ~30k/s"| S2([Stage 2: distinct per cell])
    S2 -->|"cell counts, ~20 B, up to 15k/s batched"| R[(Redis)]
    S2 -->|"minute rows, 2.5k/s, 6.5 GB/day"| CMC[(cell_minute_counts)]
    K -->|"raw, ~100 GB/day Parquet"| RAW[(raw_pings)]
    RAW -->|"1 h = ~4 GB, hourly"| HB([Hourly batch])
    HB -->|"final rows, 9 M per hour"| CMC
    CMC -->|"450k rows/h, ~15 MB"| EXP([Exporter])
    EXP -->|"Parquet + manifest per contract"| OUT[(Export bucket)]
    R -->|"~30 KB JSON per city, 100 reads/s"| API([Heatmap API])

    class APP client
    class S1,S2,HB,EXP,API service
    class K queue
    class R cache
    class CMC,RAW,OUT store

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef cache    fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
```

## D4. FR5 history query (happy path)

```mermaid
%% D4 (FR5): an analyst asks for last Tuesday. Only final rows, partition pruned by city and date.
sequenceDiagram
    autonumber
    participant A as Analyst
    participant Q as SQL engine
    participant T as cell_minute_counts
    A->>Q: SELECT cell, max(drivers_20m) WHERE city = X AND date = Tue GROUP BY cell
    Q->>T: prune to partition city = X, date = Tue
    T-->>Q: ~430k rows, version = final
    Q-->>A: 1,500 rows in ~2 s
```

## D5. Hourly completeness gate fails

```mermaid
%% D5: failure path. Lake ingestion is behind, so hour H waits instead of publishing an incomplete file.
sequenceDiagram
    autonumber
    participant SC as Scheduler
    participant L as Lake ingestion
    participant HB as Hourly batch
    participant OC as On-call
    SC->>L: H+15, watermark past H+1h15m?
    L-->>SC: no, at H+40m
    loop every 5 min
        SC->>L: check again
    end
    SC->>OC: H+30 alert to ingestion owner
    SC->>OC: H+45 page hot-clusters on-call
    L-->>SC: watermark reached at H+50
    SC->>HB: run hour H
    HB-->>SC: published at H+56, late but complete
```

## D6. Stage 1 cell assignment with hysteresis

```mermaid
%% D6: decision flow in stage 1 for one ping. Prevents boundary jitter from double counting and cuts pings to one fact per minute.
flowchart TD
    P[ping for driver d] --> S{seq already seen?}
    S -->|"yes"| X1[drop, retry]
    S -->|"no"| V{speed from last ping<br/>over 200 km/h?}
    V -->|"yes"| X2[drop, flag spoof]
    V -->|"no"| G[project, raw cell c]
    G --> H{c differs from current<br/>and accuracy under 100 m?}
    H -->|"no"| SAME[stay in current cell]
    H -->|"yes"| IN{50 m inside c,<br/>or 2nd ping in c?}
    IN -->|"no"| SAME
    IN -->|"yes"| SW[switch current to c]
    SAME --> M{first fact for this<br/>cell and minute?}
    SW --> M
    M -->|"yes"| EMIT[emit presence d, cell, minute]
    M -->|"no"| X3[drop, already counted]

    class P,G,SAME,SW,EMIT service
    class S,V,H,IN,M decision
    class X1,X2,X3 external

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

## D8. State machine: one hour of counts

```mermaid
%% D8: lifecycle of one city-hour in cell_minute_counts and its export files.
stateDiagram-v2
    direction LR
    [*] --> Provisional: stream writes minutes
    Provisional --> Waiting: hour closes
    Waiting --> Final: gate passes, batch swaps
    Waiting --> Late: H+45 not complete
    Late --> Final: gate passes
    Final --> Published: files + manifest
    Published --> Restated: D+1 value changed
    Published --> Frozen: D+1 no change
    Restated --> Frozen: v2 published
    Frozen --> [*]: 90 d to cold
```

## D9. Deployment / topology

```mermaid
%% D9: one region serves its cities. Everything spans three availability zones. Only the lake replicates across regions.
flowchart LR
    subgraph R1[Region, e.g. ap-south]
        subgraph AZ1[AZ a]
            GW1[Gateway]
            KB1[(Kafka broker)]
            TM1[Flink TMs]
            RP[(Redis primary)]
        end
        subgraph AZ2[AZ b]
            GW2[Gateway]
            KB2[(Kafka broker)]
            TM2[Flink TMs]
            RR[(Redis replica)]
        end
        subgraph AZ3[AZ c]
            KB3[(Kafka broker)]
            JM[Flink JobManager<br/>HA via ZooKeeper or K8s]
        end
        LAKE[(Lake bucket<br/>raw, counts, exports)]
    end
    LAKE -->|"async replication"| DR[(Lake replica<br/>other region)]
    RP -->|"async"| RR

    class GW1,GW2,TM1,TM2,JM service
    class KB1,KB2,KB3 queue
    class RP,RR cache
    class LAKE,DR store

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef cache    fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
```

## D10. Scaling / partitioning

```mermaid
%% D10: partition by driver first, re-key by cell after the 5x reduction. Partitioning Kafka by cell is the rejected option that creates a hot partition.
flowchart LR
    K[(Kafka, 64 partitions<br/>key driver_id, uniform)] -->|"150k/s"| S1[Stage 1, 16 subtasks<br/>~9k pings/s each]
    S1 -->|"hash cell_id, 30k/s"| S2[Stage 2, 16 subtasks<br/>512 key groups]
    S2 -->|"stadium cell,<br/>3,000 drivers = 50/s"| OK[Hot cell is cheap]
    ALT[(Rejected: Kafka keyed by cell_id)] -->|"stadium cell in one partition,<br/>per-driver order lost"| BAD[Hot partition]:::critical

    class K queue
    class S1,S2,OK service
    class ALT decision

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
```

## D11. Failure mode map

```mermaid
%% D11: component, what fails, blast radius, mitigation.
flowchart TD
    ROOT[Hot clusters system]
    ROOT --> F1[Stream job lost]
    ROOT --> F2[Redis lost]
    ROOT --> F3[Bad phone clock]
    ROOT --> F4[Lake ingestion late]
    ROOT --> F5[Bad stage 2 release]
    F1 --> B1[Ops map stale ~1 min<br/>institutions unaffected]
    F2 --> B2[Ops map errors ~15 s]
    F3 --> B3[Without clamp: a city reads 0<br/>with clamp: nothing]:::critical
    F4 --> B4[Hour H late, never incomplete]
    F5 --> B5[Provisional wrong]
    B1 --> M1[Checkpoint restore, Kafka replay,<br/>as_of banner]
    B2 --> M2[Replica promote,<br/>full re-emit every 60 s]
    B3 --> M3[Clamp at gateway,<br/>skew metric per app version]
    B4 --> M4[Completeness gate,<br/>alert H+30, page H+45]
    B5 --> M5[Reconciliation over 2% pages,<br/>batch pins older version]

    class ROOT,M1,M2,M3,M4,M5 service
    class F1,F2,F3,F4,F5 decision
    class B1,B2,B4,B5 external

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
```

## D12. Rollout / migration

```mermaid
%% D12: from the old ops view (snapshot of the dispatch geo index) to this system, then institutions. Each phase has a rollback point.
gantt
    title Migration to hot clusters
    dateFormat YYYY-MM-DD
    section Build
    Gateway clamp and server_ts        :a1, 2026-10-01, 7d
    Stream job in shadow               :a2, after a1, 14d
    section Ops
    Side by side maps, rollback by flag :b1, after a2, 14d
    Switch ops default                 :b2, after b1, 30d
    section Institutions
    Hourly batch and reconciliation    :c1, after a2, 14d
    Pilot with one institution         :c2, after c1, 14d
    All contracts                      :c3, after c2, 14d
```
