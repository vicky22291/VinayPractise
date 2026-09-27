# Diagrams: distributed deny list

The D1 to D12 set from `hld/CLAUDE.md` §4. Diagrams already embedded in [`solution.md`](solution.md) are listed with a pointer, not pasted twice.

| # | Diagram | Where |
|---|---|---|
| D1 | Context | below |
| D2 | Data flow | below |
| D3 | Component architecture (final design) | `solution.md` §6 |
| D4 | Happy path per FR | FR1 check: §6 Flow 1. FR2 + FR3 emergency add and propagation: §6 Flow 2. Host boot: §6 Flow 4. FR4 explain and revert: below |
| D5 | Failure paths | Distributor death: §5.4. Spanner region loss: §10.4. Bad batch: §10.4. Gap older than the buffer: below. Truncated feed: below |
| D6 | Decision flow (host agent, per batch) | `solution.md` §5.3 |
| D7 | Entity relationship | `solution.md` §3.3 |
| D8 | State machines | Entry lifecycle: §5.5. Host readiness lifecycle: below |
| D9 | Deployment / topology | below |
| D10 | Scaling / partitioning | below |
| D11 | Failure mode map | below |
| D12 | Rollout / migration | below |

---

## D1. Context (zoom-out)

The deny list as one box: writers on the left, 200k enforcement hosts on the right, one store as the truth.

```mermaid
%% D1: the system as one box. Humans, detectors and an external feed write; every enforcement host reads a local copy; support explains and undoes.
flowchart LR
    TS[T&S analysts] -->|"add, remove, approve<br/>~1 change/s"| DL[Distributed deny list<br/>store, publishers, distributors,<br/>host agents]
    DET[Abuse and DDoS detectors] -->|"add with TTL 1 h<br/>2k/s avg, 20k/s burst"| DL
    GOV[External feed<br/>security.gov.x] -->|"full list, fetched every 5 min"| DL
    DL -->|"Batch stream + snapshots<br/>64 KB/s per host avg"| FE[Enforcement hosts x200k<br/>front-ends, gateways, edge]
    U[Users and attackers] -->|"50 M requests/s"| FE
    FE -->|"allow, 403, or packet drop"| U
    FE -->|"deny events, acks"| DL
    SUP[Support console] -->|"Lookup at_time, Revert"| DL

    class TS,DET,SUP,U client
    class GOV external
    class DL service
    class FE client

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

## D2. Data flow (DFD)

What moves where, with format, size and rate. Deltas dominate the steady state; snapshots dominate boots.

```mermaid
%% D2: data flow with sizes and rates. Stores are cylinders, processes are rounded boxes.
flowchart LR
    W(Writers) -->|"AddEntries, protobuf ~200 B/entry,<br/>2k/s avg, 20k/s burst"| API(Denylist API + gate)
    API -->|"impact query per broad entry, ~ms"| TI[(Traffic index<br/>1% sample, 500k samples/s in)]
    API -->|"ENTRY upsert + CHANGE row,<br/>~500 B + 200 B, 2k txn/s"| SP[(Spanner<br/>5 GB live, 35 GB/day CHANGE)]
    SP -->|"CHANGE rows a..b, 16 range reads,<br/>10 times/s"| PUB(Publishers x2)
    SP -->|"snapshot read at T,<br/>~400 MB every 10 min"| SB(Snapshot builder)
    SB -->|"signed file, ~100 MB zstd"| BL[(Blob store)]
    PUB -->|"Batch, 32 B/op, 2k ops/s avg,<br/>20k burst, signed"| DS(Distributors x540)
    DS -->|"Batch + 1 s heartbeat,<br/>64 KB/s avg, 640 KB/s burst per host"| AG(Host agent)
    BL -->|"snapshot ~100 MB, only at boot<br/>without a local copy"| AG
    AG -->|"shared memory, 255 MB per host"| LIB(Enforcement lib)
    LIB -->|"deny events: all account/key,<br/>1% of IP, ~50k/s"| DLG[(Decision log)]
    AG -->|"Ack W, at most 1/s"| DS
    DS -->|"watermark histograms, 540/s"| TR(Propagation tracker)

    class W client
    class API,PUB,SB,AG,TR service
    class TI,SP,BL,DLG store
    class DS queue
    class LIB client

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
```

## D3. Component architecture

The final design, with the publisher pair in red. See `solution.md` §6.

## D4. Happy path: FR4 explain and revert

A wrongly blocked customer is explained from a timestamped read and unblocked by a forward revert in about 2 s.

```mermaid
%% D4 (FR4): support explains a deny from the decision log and a Spanner read at the request time, then reverts the detector's bad run as a new change set.
sequenceDiagram
    autonumber
    participant CU as Customer
    participant SUP as Support console
    participant DLG as Decision log
    participant API as Denylist API
    participant SP as Spanner
    participant PUB as Publishers + distributors
    participant AG as Host agents
    participant TR as Tracker
    CU->>SUP: 403 page, ref code 7f3a..
    SUP->>DLG: find deny event by ref code
    DLG-->>SUP: group account-deny, key 12345, W 09:41:07, host h-88
    SUP->>API: Lookup(account, 12345, at_time 09:41:07)
    API->>SP: read ENTRY + CHANGE at timestamp 09:41:07
    SP-->>API: entry added by detector-7 at 09:12, reason spam-score, ticket none
    API-->>SUP: entry, actor, reason, full history
    SUP->>API: Revert(account-deny, actor detector-7, 09:10, 09:20, revert_id r-55)
    API->>SP: read state at 09:10 and 09:20, compute inverse changes
    API->>SP: commit inverse change set in one txn, commit_ts t1
    SP-->>API: t1
    API-->>SUP: t1, emergency lane (removes always are)
    PUB->>AG: Batch covering t1, removes applied, W past t1
    AG->>PUB: Ack W
    SUP->>TR: GetPropagation(account-deny, t1)
    TR-->>SUP: 99.2% of hosts at or past t1, about 2 s after commit
```

## D5. Failure paths

### D5a. A host's gap is older than the distributor's 60 minute buffer

The host cannot replay, so it rebuilds from the latest snapshot and replays from that boundary. It keeps enforcing throughout.

```mermaid
%% D5a: a host returns after 90 minutes offline (network maintenance). Its W is older than the distributor buffer, so it loads a snapshot and replays.
sequenceDiagram
    autonumber
    participant AG as Host agent
    participant RD as Regional distributor
    participant BL as Blob store
    participant LB as Load balancer
    Note over AG: W = 08:30:00.0, now 10:00:05, keeps enforcing the old list
    AG->>RD: Subscribe(group, from 08:30:00.0)
    RD-->>AG: too old, buffer starts at 09:00:05, latest snapshot T = 10:00:00
    AG->>LB: stale over 5 min, critical-tier group, drain unless site over 20% stale
    AG->>RD: GetSnapshot(group, at or after 10:00:00)
    RD-->>AG: retry after 4 s (50 concurrent downloads already)
    AG->>BL: GetSnapshot(group, 10:00:00), signed, ~100 MB
    BL-->>AG: snapshot file
    AG->>AG: verify signature and checksum, build new base, new generation
    AG->>RD: Subscribe(group, from 10:00:00.0)
    RD-->>AG: replay 10:00:00.0 to 10:00:09.3 from buffer, then live
    AG->>AG: contiguity ok, checksums ok, W = 10:00:09.3
    AG->>LB: ready again
    Note over AG: lookups never paused, the old list served until the new generation
```

### D5b. The external feed comes back truncated

A partial download must not unblock the whole government list.

```mermaid
%% D5b: the feed importer's shrink guard. A feed that shrinks by more than 20% in one fetch is treated as a broken download, not as a mass unblock.
sequenceDiagram
    autonumber
    participant FI as Feed importer
    participant GOV as security.gov.x
    participant API as Denylist API
    participant SP as Spanner
    participant ON as On-call
    FI->>GOV: fetch full list (every 5 min)
    GOV-->>FI: 48,000 entries (last good fetch had 120,000)
    FI->>API: read current gov-feed entries with source = feed
    API->>SP: strong read
    SP-->>FI: 120,000 active entries
    FI->>FI: diff = 72,000 removes, 0 adds, shrink 60% over 20% guard
    FI->>FI: apply adds only (none), skip all removes, keep last good list
    FI->>ON: page, feed shrank 60%, removes held
    FI->>GOV: refetch after 5 min
    GOV-->>FI: 120,150 entries
    FI->>API: ImportJob(gov-feed, 150 adds, 0 removes), bulk lane 5k/s
    API->>SP: commit, normal propagation
```

## D6. Decision flow

The host agent's per-batch decision (signature, duplicate, gap, bounds, canary keys, checksum). See `solution.md` §5.3.

## D7. Entity relationship

GROUP, ENTRY, CHANGE, APPROVAL, ACTOR_QUOTA, SNAPSHOT, HOST_STATE. See `solution.md` §3.3.

## D8. State machines

The entry lifecycle (shadow, canary, enforcing) is in `solution.md` §5.5. Below: the host's readiness lifecycle.

```mermaid
%% D8: host agent and readiness lifecycle. Staleness is a health signal: only critical-tier groups drain, and never when more than 20% of the site is stale (panic hold).
stateDiagram-v2
    direction LR
    [*] --> Booting
    state "Loading" as Loading {
        direction TB
        LocalCopy: local disk copy
        Download: snapshot download
        LocalCopy --> Download: missing or over 24 h
    }
    Booting --> Loading: agent start
    Loading --> CatchingUp: base mapped
    CatchingUp --> Ready: W within 30 s of head
    Ready --> Stale: no batch 30 s
    Stale --> Ready: replay done
    Stale --> Draining: critical, over 5 min
    Stale --> PanicHold: site over 20% stale
    Draining --> PanicHold: site over 20% stale
    Draining --> CatchingUp: stream back
    PanicHold --> CatchingUp: stream back
    CatchingUp --> Loading: gap beyond buffer
    Loading --> PanicHold: plane down, site 20%
```

State meanings: `Ready` serves traffic with a fresh list. `Stale` serves traffic with the last good list (fail-static). `Draining` fails readiness so the load balancer moves traffic away. `PanicHold` serves traffic with whatever the host has, because draining a fifth of the site for the same upstream cause would remove capacity, not risk.

## D9. Deployment / topology

Where each piece runs. Only Spanner replication, the batch stream, snapshot downloads and ack histograms cross a region boundary.

```mermaid
%% D9: three regions and two PoPs. Publishers run in two regions. Each region has 8 regional distributors; each PoP has 2 distributors fed from two regions. Hosts talk only to distributors in their own site.
flowchart LR
    subgraph R1[Region us-central]
        SP1[(Spanner replicas)]
        PA[Publisher A]
        RD1[Regional distributors x8]
        H1[Hosts ~5,000]
    end
    subgraph R2[Region europe-west]
        SP2[(Spanner replicas)]
        PB[Publisher B]
        RD2[Regional distributors x8]
        H2[Hosts ~5,000]
    end
    subgraph R3[Region asia-east]
        SP3[(Spanner replicas)]
        RD3[Regional distributors x8]
        H3[Hosts ~5,000]
    end
    subgraph P1[PoP Paris]
        PD1[PoP distributors x2]
        HP1[Hosts ~330]
    end
    subgraph P2[PoP Tokyo]
        PD2[PoP distributors x2]
        HP2[Hosts ~330]
    end
    SP1 <-->|"Paxos replication, cross-region"| SP2
    SP2 <-->|"Paxos replication, cross-region"| SP3
    PA -->|"Batch, cross-region to all 30"| RD2
    PB -->|"Batch, cross-region to all 30"| RD3
    PA -->|"Batch"| RD1
    RD1 -->|"Batch, in region"| H1
    RD2 -->|"Batch, in region"| H2
    RD3 -->|"Batch, in region"| H3
    RD2 -->|"Batch, primary upstream"| PD1
    RD1 -.->|"Batch, second upstream"| PD1
    RD3 -->|"Batch, primary upstream"| PD2
    RD2 -.->|"Batch, second upstream"| PD2
    PD1 -->|"Batch, in PoP"| HP1
    PD2 -->|"Batch, in PoP"| HP2

    class SP1,SP2,SP3 store
    class PA,PB service
    class RD1,RD2,RD3,PD1,PD2 queue
    class H1,H2,H3,HP1,HP2 client

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
```

What crosses a region boundary: Spanner's own replication; publisher to regional distributor batch streams (each distributor subscribes to both publishers, so both A and B reach every region; two edges are drawn for readability); PoP distributors' upstream streams (two regions each); snapshot downloads from the multi-region blob store when a host has no local copy; and ack histograms to the tracker. Requests and lookups never cross a region boundary.

## D10. Scaling / partitioning

The unit of ordering is the group. Hosts subscribe by role. The regional distributor during a mass boot is what saturates first.

```mermaid
%% D10: partitioning by group and role, the hot spot, its fixes, and the 10x path. Red is the regional distributor at mass boot (solution §5.2 and §10.3).
flowchart LR
    G1[Group edge-ip-drop<br/>one ordered stream] -->|"subscribed by"| EDGE[Edge hosts<br/>IP groups only]
    G2[Group account-deny<br/>one ordered stream] -->|"subscribed by"| APPFE[App front-ends<br/>account groups]
    G3[Group api-key-revoked<br/>one ordered stream] -->|"subscribed by"| GW[API gateways<br/>key groups]
    BOOT[Region boot<br/>5,000 hosts x 100 MB = 500 GB] -->|"snapshot requests"| RD[Regional distributor<br/>625 hosts, 3.2 Gbps burst<br/>+ ~3 GB/s of snapshots]
    DISK[Fix 1: local disk copy<br/>boot is a catch-up] -.->|"removes most downloads"| RD
    ADM[Fix 2: 50 concurrent,<br/>retry-after with jitter] -.->|"caps egress"| RD
    BL[(Fix 3: blob store fallback)] -.->|"absorbs the rest"| BOOT
    TEN[10x: long-tail group<br/>100 M keys] -->|"base becomes"| BF[Binary fuse filter<br/>~9 bits/key, 0.4% FP, 113 MB]
    BF -->|"filter hit, 400k/s fleet-wide"| LK[Regional lookup service<br/>full group, 3 to 5 replicas]

    class G1,G2,G3 queue
    class EDGE,APPFE,GW,BOOT client
    class RD critical
    class DISK,ADM service
    class BL store
    class TEN decision
    class BF cache
    class LK service

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef cache    fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

Attack-driven groups (DDoS IPs) never take the filter path: under attack their positives are the traffic, and a remote confirm would reflect the attack into the lookup service.

## D11. Failure mode map

Component, what fails, blast radius, mitigation. Split in two to stay under 15 nodes each.

### D11a. Distribution plane

```mermaid
%% D11a: failures between the store and the host. Every branch ends in "enforcement continues"; only freshness is at risk.
flowchart TD
    PL[Distribution plane] --> F1[One distributor dies]
    PL --> F2[One publisher dies]
    PL --> F3[Both publishers or Spanner down]
    PL --> F4[Region partitioned]
    F1 -->|"blast radius"| B1[~625 hosts 4 s staler, once]
    F2 -->|"blast radius"| B2[none]
    F3 -->|"blast radius"| B3[no new changes anywhere,<br/>enforcement unchanged]
    F4 -->|"blast radius"| B4[that region stale]
    B1 -->|"mitigation"| M1[3 s silence, reconnect with W,<br/>replay from 60 min buffer]
    B2 -->|"mitigation"| M2[other publisher's identical batches]
    B3 -->|"mitigation"| M3[fail-static, page at 30 s,<br/>panic threshold stops drains]
    B4 -->|"mitigation"| M4[fail-static, PoPs use second region]

    class PL service
    class F1,F2,F3,F4 decision
    class B1,B2,B3,B4 client
    class M1,M2,M3,M4 service

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

### D11b. Data, hosts and code

```mermaid
%% D11b: failures on the host and in the data itself. The bad change is the largest blast radius, so it has the most layers.
flowchart TD
    HD[Hosts, data, code] --> F5[Bad change reaches the stream]
    HD --> F6[Agent crashes]
    HD --> F7[Host clock jumps]
    HD --> F8[Bad agent or lib build]
    F5 -->|"blast radius"| B5[every subscribing host in ~1 s]
    F6 -->|"blast radius"| B6[none on the data path]
    F7 -->|"blast radius"| B7[one host expires early or late]
    F8 -->|"blast radius"| B8[hosts in the rollout stage]
    B5 -->|"mitigation"| M5[gate, quotas, shadow and canary modes,<br/>host bounds, quarantine, kill switch,<br/>forward revert ~1 s]
    B6 -->|"mitigation"| M6[list stays mapped in shm,<br/>agent restarts, resubscribes from W]
    B7 -->|"mitigation"| M7[compare with batch to,<br/>clamp expiry to W..W+60 s]
    B8 -->|"mitigation"| M8[code ships slowly 1%, region, world,<br/>new fields behind a flag]

    class HD service
    class F5,F6,F7,F8 decision
    class B5,B6,B7,B8 client
    class M5,M6,M7,M8 service

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

## D12. Rollout / migration

From per-service blocklists or a central Redis to this design, in four flag-guarded phases (`solution.md` §8). Each phase has a rollback point that is one flag.

```mermaid
%% D12: four migration phases. Each milestone is the rollback point for its phase: flip one flag back.
gantt
    title Migration to the distributed deny list
    dateFormat  YYYY-MM-DD
    axisFormat  %b %d
    section Phase 1 build and shadow
    Store, publishers, distributors up          :p1a, 2026-10-01, 14d
    Backfill existing lists into groups         :p1b, after p1a, 7d
    Agent and lib in shadow on all hosts        :p1c, after p1b, 14d
    Rollback point, disable shadow flag         :milestone, m1, after p1c, 0d
    section Phase 2 enforce per group
    Flip enforcement group by group             :p2a, after m1, 14d
    Old path kept live as fallback              :p2b, after m1, 14d
    Rollback point, per-group enforce flag      :milestone, m2, after p2a, 0d
    section Phase 3 move writers
    Detectors, feeds, console to the API        :p3a, after m2, 7d
    Dual-write to the old store                 :p3b, after m2, 14d
    Rollback point, writer routing flag         :milestone, m3, after p3b, 0d
    section Phase 4 delete old paths
    Remove old blocklists and old store         :p4a, after m3, 7d
    Rollback point, restore from old snapshot   :milestone, m4, after p4a, 0d
```
