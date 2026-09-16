# Diagrams: VM network QoS

The D1 to D12 set from `hld/CLAUDE.md` §4. A diagram is drawn once: the ones embedded in [`solution.md`](solution.md) are linked here, not repeated.

| # | Diagram | Where |
|---|---|---|
| D1 | Context | below |
| D2 | Data flow | below |
| D3 | Component architecture (final design) | `solution.md` §6 |
| D4 | Happy path per FR | FR1 egress: `solution.md` §6 Flow 1. FR2 ingress: §6 Flow 2 and §5.2 (the loop). FR3 create: §6 Flow 4. FR4 metering: below |
| D5 | Failure paths | Agent crash: `solution.md` §6 Flow 5. UDP flood: §10.4. Proxy death: below |
| D6 | Decision flow in the datapath | `solution.md` §5.1 |
| D7 | Entity relationship | `solution.md` §3.3 |
| D8 | Lease state machine | `solution.md` §5.3 |
| D9 | Deployment / topology | below |
| D10 | Scaling / partitioning | `solution.md` §5.4 |
| D11 | Failure mode map | below |
| D12 | Rollout / migration | below |

---

## D1. Context (zoom-out)

```mermaid
%% D1: context. Our system is the proxy tier plus the host datapath and agent. Everything else is outside.
flowchart LR
    INET((Internet senders<br/>and receivers)) -->|"ingress packets"| SYS[VM network QoS<br/>proxies + host datapath + agent]
    SYS -->|"egress packets"| INET
    T[Tenant / operator API] -->|"create, resize, delete VM, get usage"| SYS
    SYS -->|"packets"| VMS[Tenant VMs]
    VMS -->|"packets"| SYS
    SYS -->|"usage samples 1/s"| BILL[Billing]
    CM[Cluster manager<br/>placement] -->|"candidate hosts"| SYS
    EDGE[Edge routers<br/>ECMP, BGP] -->|"1/8 of flows per proxy"| SYS

    class INET,EDGE,CM,BILL external
    class T,VMS client
    class SYS service

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

## D2. Data flow (DFD)

```mermaid
%% D2: data flow with sizes and rates. The packet path carries 100 Gbps; the control path carries kilobytes per 100 ms.
flowchart LR
    IN((Internet)) -->|"ingress, up to 50 Gbps per host"| PX(Proxy: bucket, encap)
    PX -->|"Geneve, vm_id, <= sum of leases"| DP(Host datapath)
    DP -->|"deliver"| VM[VM]
    VM -->|"egress, up to 100 Gbps"| DP
    DP -->|"EDT-paced"| IN
    PX -->|"Report, 1.1 KB, every 100 ms"| AG(Host agent)
    AG -->|"Leases, 1.1 KB, every 100 ms"| PX
    AG -->|"SetClass rate, pps, policer"| DP
    DP -->|"counters, read every 1 s"| AG
    AG -->|"usage_sample, 40 B, 2/s per VM"| K[[Kafka]]
    K -->|"consume"| TS[(Time series store)]
    CT(Controller) -->|"vm row, floors, ip map: on change only"| AG
    CT -->|"ip -> vm map"| PX
    CT <-->|"txn"| DB[(Policy store)]

    class IN external
    class VM client
    class PX,DP,AG,CT service
    class K queue
    class TS,DB store

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

## D4 (FR4). Metering, happy path

```mermaid
%% D4 (FR4): metering. Counters are read on the host, samples are upserted, so retries never double bill.
sequenceDiagram
    autonumber
    participant DP as Host datapath
    participant AG as Host agent
    participant K as Kafka (partition by vm_id)
    participant C as Consumer
    participant TS as Time series store
    participant API as GET /vms/id/usage
    loop every 1 s
        AG->>DP: read per-VM counters (sum per-core)
        DP-->>AG: bytes_in, bytes_out, pkts, dropped per VM
        AG->>K: usage_sample(vm, dir, ts_1s, bytes, pkts, dropped)
    end
    K->>C: batch
    C->>TS: upsert keyed (vm, dir, ts_1s)
    API->>TS: range(vm, from, to)
    TS-->>API: samples, hourly rollup
```

## D5 (third). Proxy death

```mermaid
%% D5c: one of 8 proxies dies. Flows move, the moved VMs run at floor for one interval, then get leases.
sequenceDiagram
    autonumber
    participant E as Edge router
    participant P3 as Proxy 3
    participant P4 as Proxy 4
    participant A as Host agent
    Note over P3: crashes at t=0
    E->>P3: BFD hello, no reply (3 x 100 ms)
    Note over E: t=300 ms: route via P3 withdrawn, re-hash
    E->>P4: flows that were on P3 now arrive here
    P4->>P4: no lease covers the new demand: admit at floor Y_in/8, count wanted
    P4->>A: t=400 ms: Report shows wanted up on P4, P3 silent
    A->>A: re-split each VM's allocation over the 7 live proxies by wanted
    A-->>P4: Leases covering the moved demand
    Note over P4: t=400..500 ms: full rate restored
```

## D9. Deployment / topology

```mermaid
%% D9: one region. Proxies are per proxy group at the edge, agents are per host, controller is regional and replicated. Nothing crosses a region boundary on the hot loop.
flowchart TD
    subgraph REGION[Region: 10k hosts, 500 proxies, 3 AZs]
        subgraph EDGEZ[Edge, spans AZs]
            ER[Edge routers, ECMP]
            PG[Proxy groups 1..62<br/>8 proxies each, 100 Gbps each<br/>spread over 3 AZs]
        end
        subgraph AZ1[AZ 1: racks of 40 hosts]
            H1[Host: SmartNIC datapath<br/>+ QoS agent on mgmt cores]
            TOR1[ToR switch]
        end
        subgraph CTRLZ[Control plane, 3 replicas across AZs]
            CT[Controller, leader elected]
            DB[(Policy store, sync replication)]
            K[[Kafka, RF 3]]
        end
    end
    ER -->|"ingress"| PG
    PG -->|"encap"| TOR1
    TOR1 -->|"downlink 100 Gbps"| H1
    PG -.->|"Report / Leases, mgmt network"| H1
    CT -->|"watch, push"| H1
    CT -->|"ip map, floors"| PG
    CT <-->|"txn"| DB
    H1 -->|"usage"| K

    class ER client
    class PG,H1,CT service
    class TOR1 client
    class DB store
    class K queue

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
```

## D11. Failure mode map

```mermaid
%% D11: what fails, who feels it, what limits the damage. The only red path is non-proxied traffic reaching the NIC, which the design cannot shape.
flowchart TD
    F1[Host agent dies] -->|"no leases 500 ms"| S1[One host: no bursting for ~1 s]
    S1 -->|"mitigation"| M1[Proxies fall to floor, epoch on restart]
    F2[Proxy dies] -->|"BFD 300 ms"| S2[1/8 of a group's flows re-hash]
    S2 -->|"mitigation"| M2[Floor for one interval, then leases]
    F3[Controller or DB down] -->|"no writes"| S3[No create / resize region-wide]
    S3 -->|"mitigation"| M3[Hot loop unaffected, local caches on restart]
    F4[Bad ip map push] -->|"wrong host"| S4[One VM loses 1/8 inbound]
    S4 -->|"mitigation"| M4[Fail closed on host, no_such_vm alert, versioned re-push]
    F5[Non-proxied traffic floods NIC] -->|"ToR drops everyone"| S5[Guarantee broken on that host]
    S5 -->|"mitigation"| M5[Headroom 10 percent, NIC ACL, NIC > 95 percent pages]
    F6[Metering lag] -->|"billing stale"| S6[No packet effect]
    S6 -->|"mitigation"| M6[1 h agent buffer, proxy counters as second source]

    class F1,F2,F3,F4,F6 service
    class F5,S5 critical
    class S1,S2,S3,S4,S6 decision
    class M1,M2,M3,M4,M5,M6 store

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

## D12. Rollout / migration

```mermaid
%% D12: from static per-VM caps to leased bursting. Every phase has a rollback that returns to the previous phase's behaviour within seconds.
gantt
    title Migration from static caps to leased QoS
    dateFormat YYYY-MM-DD
    axisFormat %b %d
    section Phase 1 shadow
    Deploy agents and proxies, leases disabled     :p1, 2026-10-01, 14d
    Compare shadow leases with demand              :p1b, after p1, 7d
    section Phase 2 leases
    Enable leases on one proxy group (canary)      :p2, after p1b, 7d
    Enable leases on 10 percent of groups          :p2b, after p2, 7d
    Enable leases on all groups                    :p2c, after p2b, 14d
    section Phase 3 datapath
    HTB to EDT on SmartNIC hosts, host by host     :p3, after p2c, 30d
    Remove HTB path                                :p3b, after p3, 7d
```

Rollback points: phase 1 has nothing to roll back (no behaviour change). Phase 2 rollback is `leases_enabled = false` per group, effective within 1 s. Phase 3 rollback is a qdisc swap per host.
