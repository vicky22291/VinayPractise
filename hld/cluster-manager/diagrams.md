# Diagrams: autoscaling cluster manager

The D1 to D12 set from `hld/CLAUDE.md` §4. Diagrams already embedded in [`solution.md`](solution.md) get a pointer, not a second copy.

| # | Diagram | Where |
|---|---|---|
| D1 | Context | below |
| D2 | Data flow | below |
| D3 | Component architecture (final design) | `solution.md` §6 |
| D4 | Happy path per FR | FR1 create: §4.1 (naive) and §6 Flow 1 (warm start). FR2 placement: §6 Flow 1 steps 6 to 9, plus the score pipeline in §5.3. FR3 autoscale: §6 Flow 2 (up) and Flow 5 (down). FR4 spot: §10.4 spot interruption timeline. FR5 preemption: below |
| D5 | Failure paths | Provisioner crash after launch: §5.5. Cell master failover: §10.4. 00:00 burst with a capacity error: §10.4. Partitioned VM: below. Two capacity-manager leaders: below |
| D6 | Decision flow (one pending container) | `solution.md` §4.5 |
| D7 | Entity relationship | `solution.md` §3.3 |
| D8 | State machines (cluster, VM, container) | below |
| D9 | Deployment / topology | below |
| D10 | Scaling / partitioning (cells, accounts, the launch budget) | below |
| D11 | Failure mode map | below, in two parts |
| D12 | Rollout / migration from classic | below |
| Zoom-ins | Incremental steps, capacity tiers, provisioner red node, placement pipeline, spot diversification | `solution.md` §4.1 to §4.4, §5.1, §5.2, §5.3, §5.4 |

## D1. Context (zoom-out)

The cluster manager as one box: callers on the left, the cloud on the right, three services we use but do not own.

```mermaid
%% D1: the cluster manager as one box. Callers create clusters, the cloud sells VMs and warns about spot, billing and identity sit outside our scope.
flowchart LR
    JS[Job scheduler] <-->|"create / resize / terminate, idempotency key,<br/>next-hour forecast. back: events RUNNING,<br/>SPOT_LOST, PREEMPTED, TERMINATED"| CM[Cluster manager<br/>1 region, 3 AZ cells,<br/>6k to 16k VMs]
    NB[Notebooks, SQL warehouses] -->|"create / resize / terminate"| CM
    CM -->|"verify caller, get tenant"| IDP[Identity]
    CM <-->|"launch N / terminate, client token, tags<br/>back: instance ids, ICE, THROTTLED"| CLOUD[Cloud APIs<br/>8 accounts]
    CLOUD -->|"spot warnings, state changes"| EQ[Cloud event stream]
    EQ -->|"instance id, deadline"| CM
    CM -->|"shuffle overflow,<br/>runtime checkpoints"| OBJ[(Object store)]
    CM -->|"per-second usage records"| BILL[Billing]

    class JS,NB client
    class CM service
    class OBJ store
    class EQ queue
    class CLOUD,IDP,BILL external
    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

## D2. Data flow (DFD)

Every edge with data, size and rate at peak. Rates come from `solution.md` §2; sizes marked `~` are assumptions.

```mermaid
%% D2: what flows where at peak. Heartbeats are the biggest stream and never touch a store; launches are the smallest stream and the only rate-limited one.
flowchart LR
    JS[Job scheduler,<br/>notebooks, SQL] -->|"create spec, JSON ~1 KB,<br/>3.5/s avg, 83/s at 00:00"| API(Cluster service)
    API -->|"spec row ~2 KB, 300k/day"| DB[(Cluster DB)]
    API -->|"spec copy, ~28/s per cell at 00:00"| CM(Cell master x3)
    DRV(Spark drivers<br/>12k clusters) -->|"ReportDemand ~200 B,<br/>every 5 s, 2,400/s region"| CM
    AG(Node agents<br/>5.3k VMs per cell) -->|"Heartbeat 2 KB, 1,100/s per cell,<br/>2.2 MB/s, memory only"| CM
    CM -->|"Assign / Kill + epoch,<br/>~220/s per cell at 00:00"| AG
    CM -->|"Txns, under 1,000/s per cell,<br/>state ~100 MB"| CS[(Cell store x3)]
    CS -->|"capacity_request ~300 B,<br/>1 per batch, 5 s loop"| PV(Provisioner)
    PV -->|"launch N + 6 types, client token,<br/>~40k VMs/day, 140/min per cell before 00:00"| CL[Cloud APIs<br/>8 accounts]
    CL -->|"interruption warning ~1 KB,<br/>one per reclaimed spot VM"| EQ[Event stream]
    EQ -->|"instance id, deadline"| CM
    CM -->|"usage record ~200 B per container-minute,<br/>~1.7k/s at 100k containers"| BILL[Billing]

    class JS client
    class API,CM,DRV,AG,PV service
    class DB,CS store
    class EQ queue
    class CL,BILL external
    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

## D4 (FR5). Preemption as a bridge

A P1 worker waits 5 s, the cold path is too slow, one P4 worker is evicted within its cluster's budget, and the victim later lands on the VM already in flight.

```mermaid
%% D4 (FR5): preemption as a bridge. Nominate and evict in one Txn, 30 s grace, then place. The in-flight VM serves the victim (late binding), so nothing extra is bought.
sequenceDiagram
    autonumber
    participant SCH as Scheduler (az-b, epoch 7)
    participant CAP as Capacity manager
    participant CS as Cell store
    participant AG as Node agent (VM 2207)
    participant D88 as Driver of c88 (P4)
    SCH->>SCH: w1 (P1 worker, 8 vCPU) pending 5 s. No free slot, no hot VM
    SCH->>CAP: ETA for one VM of this shape?
    CAP-->>SCH: r90 in flight, cold ETA 60 s, w1 budget left 25 s
    SCH->>SCH: pick VM 2207. Only P4 victim v3 of c88, under its 25% budget
    SCH->>CS: Txn v3 DECOMMISSIONING + VM 2207 nominated_for w1, if leader 7 and mod_revision r, ok
    SCH->>AG: Kill(v3, epoch 7, grace 30 s)
    SCH->>D88: decommission executor v3, driver moves its shuffle blocks to peers
    AG-->>SCH: v3 exited (t = 20 s)
    SCH->>CS: Txn w1 on VM 2207, clear nominated_for, v3 PREEMPTED then PENDING at P4
    SCH->>AG: Assign(w1, epoch 7). w1 running at t = 25 s
    CAP->>CAP: next 5 s loop. pending v3, in-flight r90 covers it, buy 0
    Note over SCH,CAP: r90's VM registers at t ~65 s and v3 is placed on it. P1 never preempts P1, so no cascade
```

## D5 (fifth). Partitioned VM: suspect at 30 s, replace at 2 min, terminate at 10 min

The agent never kills customer work on its own. The epoch covers a reconnect; the cloud API is the fence for everything else.

```mermaid
%% D5: a VM loses its network. Detection is cheap, replacement is patient, and the cloud API is the fence. A reconnect before 10 min is resolved by the epoch.
sequenceDiagram
    autonumber
    participant AG as Node agent (VM 3105)
    participant CM as Cell master (epoch 7)
    participant CS as Cell store
    participant PV as Provisioner
    participant CL as Cloud API
    Note over AG,CM: t = 0, network partition. Agent keeps c1 and c2 running, heartbeats fail and retry every 5 s
    CM->>CS: t = 30 s, no heartbeat. VM 3105 SUSPECT, no new placements
    CM->>CS: t = 2 min. c1, c2 LOST (driver has usually dropped them), replaced on free slots, 3105 desired set empty at epoch 8
    alt agent reconnects before 10 min (t = 4 min)
        AG->>CM: Heartbeat, running c1 and c2 at epoch 7
        CM-->>AG: desired set epoch 8, no c1, no c2
        AG->>AG: kill c1 and c2 (older epoch), VM back to ACTIVE, empty
    else still unreachable at 10 min
        CM->>CS: VM 3105 TERMINATING
        PV->>CL: TerminateInstances 3105 (idempotent)
        CL-->>PV: terminated, billing stops, VM cannot come back. PV records TERMINATED
    end
```

## D5 (sixth). Two capacity-manager leaders after a blip: no double buy

Two fences in series: the old leader's write fails the `leader_epoch` compare, and the provisioner acts only on rows stamped with the current epoch. The new leader **adopts** the old leader's open rows by re-stamping them (same `request_id` and `attempt`), so a launch that was already queued or in flight keeps its client token and is never bought twice ([`../../concepts/leases-fencing-clocks.md`](../../concepts/leases-fencing-clocks.md)).

```mermaid
%% D5: a network blip leaves two processes that think they lead cell az-a. Every intent row carries the epoch; the store and the provisioner both check it. The new leader adopts open rows, so one purchase reaches the cloud.
sequenceDiagram
    autonumber
    participant L as Old leader (epoch 7)
    participant S as Standby
    participant CS as Cell store
    participant PV as Provisioner
    participant CL as Cloud API
    L->>CS: Txn put r59 (10 VMs) if leader == 7, ok (t = -2 s)
    Note over PV,CL: r59 waits in the band-ordered queue behind the token bucket
    L-xCS: network blip, lease renewals fail (t = 0)
    S->>CS: lease expired at t = 10 s. campaign, Txn leader = 8 (t = 10.2 s)
    S->>CS: Txn re-stamp open rows, r59 now epoch 8, same id and attempt
    PV->>CS: dequeue r59, epoch 8 == leader, launch it
    PV->>CL: launch 10, ClientToken r59:a1
    S->>CS: loop at t = 15 s. r59 counts as in-flight supply, buy 0
    L->>CS: blip heals, Txn put r60 (10 VMs) if leader == 7 (t = 16 s)
    CS-->>L: compare failed, leader is 8. L steps down and exits
    Note over S,CL: bought once (r59). A row the provisioner sees before the re-stamp simply waits for it
```

## D8. State machines

Three lifecycles, three owners: the cluster (cluster service and cell), the VM (capacity manager), the container (scheduler). Autoscaling happens inside cluster `RUNNING`; only a user resize enters `RESIZING`.

### D8a. Cluster

```mermaid
%% D8a: cluster lifecycle, as the cluster service and the cell see it. Losing the driver is the only way a running cluster errors.
stateDiagram-v2
    direction LR
    [*] --> PENDING: POST /clusters
    PENDING --> STARTING: cell chosen
    STARTING --> RUNNING: driver + min running
    STARTING --> ERROR: start failed
    RUNNING --> RESIZING: PATCH min or max
    RESIZING --> RUNNING: in new range
    RUNNING --> ERROR: driver lost
    RUNNING --> TERMINATING: terminate or idle
    STARTING --> TERMINATING: terminate
    RESIZING --> TERMINATING: terminate
    ERROR --> TERMINATING: clean up
    TERMINATING --> TERMINATED: all containers gone
    TERMINATED --> [*]
```

### D8b. VM

```mermaid
%% D8b: VM lifecycle in the cell store. WARM is the hot pool. SUSPECT waits, TERMINATING uses the cloud as the fence, LOST closes a row whose instance vanished.
stateDiagram-v2
    direction LR
    [*] --> REQUESTED: capacity request
    REQUESTED --> BOOTING: instance id back
    BOOTING --> WARM: agent registered
    BOOTING --> LOST: missing 10 min
    WARM --> ACTIVE: first placement
    ACTIVE --> WARM: empty, pool below target
    ACTIVE --> SUSPECT: no heartbeat 30 s
    SUSPECT --> ACTIVE: heartbeat back
    SUSPECT --> TERMINATING: unreachable 10 min
    SUSPECT --> LOST: gone from cloud list
    ACTIVE --> DRAINING: empty 2 min or spot
    WARM --> DRAINING: idle above target
    DRAINING --> TERMINATING: alloc is zero
    DRAINING --> TERMINATED: reclaimed at T
    TERMINATING --> TERMINATED: cloud confirms
    TERMINATED --> [*]
    LOST --> [*]
```

### D8c. Container

```mermaid
%% D8c: container lifecycle. Every planned exit from RUNNING (scale-down, spot notice, preemption) goes through DECOMMISSIONING, so shuffle blocks move before the executor dies.
stateDiagram-v2
    direction LR
    [*] --> PENDING: create or scale-up
    PENDING --> PLACED: Txn commit, CAS
    PLACED --> STARTING: Assign acked
    STARTING --> RUNNING: executor registered
    RUNNING --> DECOMMISSIONING: scale-down, spot, Kill
    DECOMMISSIONING --> TERMINATED: blocks migrated
    DECOMMISSIONING --> PREEMPTED: victim exited
    DECOMMISSIONING --> LOST: VM gone at T
    RUNNING --> LOST: VM silent 2 min
    RUNNING --> TERMINATED: cluster terminated
    PREEMPTED --> PENDING: requeued, own band
    TERMINATED --> [*]
    LOST --> [*]
```

## D9. Deployment / topology

One cell per AZ with its own master and etcd; four regional pieces; one cloud behind 8 accounts.

```mermaid
%% D9: one region, three AZ cells. Everything a running cluster needs stays inside its AZ. Only control traffic (spec copies, request rows, cloud events) crosses AZs.
flowchart TB
    CLOUD[Cloud APIs<br/>8 accounts, shared VPC]
    subgraph REG[Regional, replicas spread over the 3 AZs]
        API[Cluster service<br/>stateless replicas]
        DB[(Cluster DB<br/>primary + standby)]
        PV[Provisioner<br/>token buckets, orphan GC]
        EQ[Event stream<br/>one queue per region]
    end
    subgraph AZA[AZ a, cell a]
        CMA[Cell master<br/>leader + 2 hot standbys]
        ESA[(etcd, 5 members)]
        VMA[5.3k VMs, node agents<br/>drivers + executors]
        HOTA[Hot pool ~100 VMs<br/>20% on-demand]
    end
    subgraph AZB[AZ b, cell b]
        CB[Same layout<br/>master x3, etcd x5, 5.3k VMs]
    end
    subgraph AZC[AZ c, cell c]
        CC[Same layout<br/>master x3, etcd x5, 5.3k VMs]
    end
    CLOUD -->|"spot warnings"| EQ
    CLOUD <-->|"launch / terminate"| PV
    API -->|"spec rows"| DB
    API -->|"cross-AZ: spec copy"| CMA
    API -->|"cross-AZ: spec copy"| CB
    API -->|"cross-AZ: spec copy"| CC
    EQ -->|"cross-AZ: warnings"| CMA
    PV <-->|"cross-AZ: request rows, ids"| ESA
    CMA <-->|"Txn, watch, lease 10 s"| ESA
    CMA <-->|"Assign / Kill, heartbeat 5 s,<br/>AZ-local"| VMA
    CMA -->|"place"| HOTA
    CLOUD -.->|"new VMs, any account"| HOTA

    class API,PV,CMA,VMA,CB,CC service
    class DB,ESA store
    class HOTA cache
    class EQ queue
    class CLOUD external
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef cache    fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

- Never crosses an AZ: heartbeats, `Assign`, shuffle, the etcd quorum, so an AZ loss takes one cell and a third of clusters. Crosses AZs: spec copies, request rows, cloud events, all control traffic off the running job's path. Cells b and c have the same edges as cell a, and draw VMs from all 8 accounts through a shared VPC.

## D10. Scaling / partitioning: cells by AZ, launches by account

The per-account launch budget at 00:00 is the hot shard. The fix is a path around it, not a faster box.

```mermaid
%% D10: demand is partitioned by AZ (cluster to cell) and launches by account (provisioner shard). The per-account launch budget is red. The fix changes the shape of demand, not our code.
flowchart LR
    D["00:00 burst<br/>5,000 starts = 4,000 new VMs"] -->|"cluster service routes,<br/>key = AZ"| CA[Cell az-a<br/>~1,400 VMs]
    D -->|"key = AZ"| CB[Cell az-b<br/>~1,300 VMs]
    D -->|"key = AZ"| CC[Cell az-c<br/>~1,300 VMs]
    CA -->|"request rows"| PV[Provisioner<br/>shard key = account]
    CB -->|"request rows"| PV
    CC -->|"request rows"| PV
    PV -->|"naive: 1 account, buy at T"| BUD["Per-account launch budget<br/>1,000 burst, then 2/s<br/>4,000 VMs = 25 min, p99 blown"]
    FC[Job calendar forecast] -->|"buy from T - 10 min,<br/>140 VMs/min per cell"| PV
    BIG[64 vCPU instances] -->|"1 token = 7 containers"| PV
    PV -->|"fix: 8 accounts,<br/>8,000 burst, 16/s"| ACC["Accounts 1 to 8<br/>8 x (1,000 + 600 x 2) = 17,600<br/>launches possible before T"]
    ACC -->|"VMs WARM by 23:59"| READY[Starts at 00:00<br/>p50 ~6 s]

    class D,FC client
    class CA,CB,CC,PV,READY service
    class BIG decision
    class BUD critical
    class ACC external
    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

- The fix needs all three: the forecast spreads 1,400 launches per cell over 600 s, 8 accounts multiply the bucket, big instances make one token carry 7 containers. The scheduler is not sharded further: 55 decisions/s per cell against 2,000/s per core.

## D11. Failure mode map

Component, then blast radius (pink), then mitigation (blue), in two parts to stay under 15 nodes. Quorum loss is not in `solution.md` §8; its row follows from §5.5 (data plane independence) and §5.2 (AZ routing).

### D11a. Capacity side

```mermaid
%% D11a: VMs, spot, accounts, provisioner, AZ. Each row is component, blast radius, mitigation. The provisioner is red: its outage is the one that stops all new capacity in the region.
flowchart TD
    VM[One VM dies] --> VM1["At most 25% of a cluster's workers,<br/>about 1 executor from each of ~7 clusters"]
    VM1 --> VM2["Replacements on free slots or hot pool (~6 s),<br/>Spark reruns the lost tasks"]
    SP[Spot pool reclaimed] --> SP1["At most 20% of a cluster's spot workers,<br/>replacement demand for a scarce shape"]
    SP1 --> SP2["6+ types, 120 s decommission,<br/>pool quarantine 30 min, on-demand fallback"]
    AC[One cloud account throttled] --> AC1["1/8 of launch rate and quota"]
    AC1 --> AC2[Provisioner shifts to the other 7,<br/>own token buckets stop retry storms]
    PV[Provisioner down] --> PV1[No new VMs in the region,<br/>free slots + hot pool carry 5 to 10 min]
    PV1 --> PV2[Requests are rows: restart replays same token,<br/>orphan GC, P1 preempts P4 meanwhile]
    AZ[Whole AZ lost] --> AZ1["1/3 of clusters die,<br/>other 2 cells need +50% capacity"]
    AZ1 --> AZ2[Job scheduler retries in 2 AZs,<br/>hot targets raised, P1 retries launched first]

    class VM,SP,AC,AZ service
    class PV critical
    class VM1,SP1,AC1,PV1,AZ1 decision
    class VM2,SP2,AC2,PV2,AZ2 client
    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

### D11b. Control side

```mermaid
%% D11b: cell master, cell store, cluster DB, bad rollout. None of the first three touches running work. The bad rollout has the widest blast radius, so it is the one with the slowest rollout.
flowchart TD
    CMF[Cell master leader dies] --> CMF1[That AZ cannot place, scale or buy<br/>for under 15 s, running work untouched]
    CMF1 --> CMF2[etcd lease 10 s, 2 hot standbys,<br/>leader_epoch fences the old leader]
    ESQ["Cell store loses quorum (3 of 5)"] --> ESQ1[That AZ cannot place, scale or buy<br/>until quorum returns, running work untouched]
    ESQ1 --> ESQ2[5 members survive 2 losses,<br/>new clusters routed to the other 2 cells]
    DBF[Cluster DB down] --> DBF1[No create, resize or terminate,<br/>running clusters keep autoscaling]
    DBF1 --> DBF2[Spec copy in each cell, job scheduler<br/>retries with the same idempotency key]
    SC[Bad scorer rolled out] --> SC1["Packing drops in every cell it reaches,<br/>1 point = $2M a year"]
    SC1 --> SC2[Shadow score first, one cell at a time,<br/>1 h bake, flag back to old weights]

    class CMF,ESQ,DBF,SC service
    class CMF1,ESQ1,DBF1,SC1 decision
    class CMF2,ESQ2,DBF2,SC2 client
    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

## D12. Rollout / migration from classic (one VM per worker)

Five phases, each ending in a rollback point that is a flag flip.

```mermaid
%% D12: five phases from solution.md §8. Each ends in a rollback point that is a flag, because nothing is migrated: clusters drain on their own in about 20 minutes.
gantt
    title Classic one VM per worker to the shared, packed fleet
    dateFormat  YYYY-MM-DD
    todayMarker off
    section Phase 0 shadow
    Shadow classic fleet, idempotent launches, orphan GC  :p0, 2026-10-05, 35d
    Rollback, stop shadow                                  :milestone, r0, after p0, 0d
    section Phase 1 hot pools
    Hot pools per workspace, no packing change             :p1, after p0, 28d
    Rollback, pool size 0                                  :milestone, r1, after p1, 0d
    section Phase 2 factor 1
    Serverless opts in, 1 container per shared VM          :p2, after p1, 28d
    Rollback, placement flag to classic                    :milestone, r2, after p2, 0d
    section Phase 3 factor 7
    Sandbox, 7 per VM, az-a then az-b then az-c            :p3, after p2, 28d
    Rollback, flag to factor 1                             :milestone, r3, after p3, 0d
    section Phase 4 spot and bands
    6-type spot, 20 percent pool cap, bands P1 to P4       :p4, after p3, 35d
    Rollback, ON_DEMAND and preemption off                 :milestone, r4, after p4, 0d
```

- Order and flags from `solution.md` §8; durations are assumptions. Phase 2 is the key de-risking step: the new control plane does the old thing (packing factor 1) before it does anything new, so any bug found there is a control-plane bug, not a packing or sandbox bug.
