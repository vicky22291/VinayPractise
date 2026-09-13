# Diagrams: datacenter network throttling / hierarchical rate limiting

The D1 to D12 set for [`solution.md`](solution.md). Each diagram appears once in the repo: the ones embedded in `solution.md` are linked from here, not repeated. Colors per root `CLAUDE.md` §3. Red is used only for the report interval (the accuracy knob that breaks first) and the hot account shard.

Legend reminder: 🔵 client / edge, 🟢 stateless compute, 🟣 durable storage, 🟡 cache or losable, 🔷 queue, 🔴 bottleneck or SPOF, ⚪ external, 🩷 decision.

---

## D1. Context (zoom-out)

Our system is the enforcer library plus the allocator service. Everyone else either sends traffic through it or configures it.

```mermaid
%% D1: context. Traffic passes through enforcers; only policy and ownership touch durable stores.
flowchart LR
    U[Tenant clients] -->|"requests, 2 M/s peak"| GW[Gateways / sidecars / host agents<br/>with enforcer library]
    GW -->|"ALLOW or 429 / shaped bytes"| U
    GW -->|"reports every 100 ms"| SYS[Throttling system<br/>allocator shards]
    SYS -->|"leases"| GW
    ADM[Operators, product teams] -->|"PutPolicy, SetShadow"| SYS
    SYS -->|"policy watch"| PS[(Policy store)]
    SYS -->|"shard ownership"| ET[(etcd)]
    SYS -->|"1 s rollups"| OBS[Metrics / dashboards]
    EXT[Cloud provider APIs<br/>with their own quotas] -.->|"429 / 403 if we exceed"| GW

    class U,ADM client
    class GW,SYS service
    class PS,ET store
    class OBS,EXT external

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

## D2. Data flow (DFD)

What flows, how big, how often. Peak numbers for one region.

```mermaid
%% D2: data flow. Request path never leaves the enforcer; reports are the only fleet-wide stream.
flowchart LR
    REQ[request + descriptors<br/>5 keys, ~200 B, 2 M/s] --> CHK([local check<br/>5 bucket reads, 5 us])
    CHK -->|"ALLOW 95%+"| OUT[response + rate headers]
    CHK -->|"429, retry_after"| OUT
    CHK -->|"hits, rejected, wanted per key<br/>per-core counters"| AGG([per-enforcer aggregation<br/>~300 keys per 100 ms])
    AGG -->|"Report, ~15 KB, 10/s per enforcer<br/>300 MB/s fleet, 20 k RPC/s"| ALC([allocator shard<br/>global bucket + water-fill])
    ALC -->|"Leases, ~40 B per key"| AGG
    ALC -->|"top-k + 1 s rollups, 60 k points/s"| TS[(time series)]
    POL[(policy store)] -->|"watch, ~10 changes/s"| ALC
    ET[(etcd)] -->|"shard map, epochs"| ALC
    ET -->|"shard map cache"| AGG

    class REQ,OUT client
    class CHK,AGG,ALC service
    class TS,POL,ET store

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
```

## D3. Component architecture

Embedded in [`solution.md` §6](solution.md#6-final-design). Not repeated here.

## D4. Sequence, happy path, one per FR

- D4a admit or reject: [`solution.md` §4.1](solution.md#41-admit-or-reject-against-every-limit-in-the-hierarchy).
- D4b policy change: [`solution.md` §4.2](solution.md#42-limits-are-policy-hot-reloaded-within-seconds).
- D4c fairness among siblings: [`solution.md` §4.3](solution.md#43-work-conserving-and-fair-across-the-hierarchy).
- D4d observability and shadow mode, below.

```mermaid
%% D4d: shadow mode. The allocator computes as usual; the enforcer counts instead of rejecting.
sequenceDiagram
    autonumber
    participant Op as Operator
    participant PS as Policy store
    participant A as Allocator shard
    participant E as Enforcer
    participant TS as Time series
    Op->>PS: SetShadow(rlg=api_query, on)
    PS-->>A: watch event
    E->>A: Report(hits, wanted)
    A-->>E: Lease(share, reject_fraction=0.4, shadow=true)
    E->>E: would_reject += 40% of requests, ALLOW all
    E->>A: Report(hits, would_reject)
    A->>TS: rollup would_reject per key
    Op->>TS: compare would_reject to expected before enabling
```

## D5. Sequence, failure paths

- D5a allocator owner dies: [`solution.md` §5.4](solution.md#54-the-node-that-owns-the-biggest-tenants-counters-dies-what-is-lost-and-can-two-nodes-own-it).
- D5b second-by-second failover: [`solution.md` §10.4](solution.md#104-failure-timeline).
- D5c a stale owner after a partition, below.
- D5d 10x burst in the first 100 ms, below.

```mermaid
%% D5c: split brain attempt. Epochs make the stale owner's leases unusable.
sequenceDiagram
    autonumber
    participant E as Enforcer
    participant A1 as A1 (old owner, epoch 7, partitioned from etcd)
    participant ET as etcd
    participant A2 as A2 (new owner, epoch 8)
    Note over A1: A1 cannot renew its etcd lease, local lease clock says valid until t=5 s
    ET->>ET: t=5 s: A1's lease expires, shards released
    A2->>ET: t=5.1 s: claim shard, epoch 8
    E->>A2: Report
    A2-->>E: Lease(epoch 8)
    Note over A1: partition heals at t=6 s, A1 still thinks it owns the shard
    E->>A1: (stale shard map) Report
    A1->>A1: lease clock expired at t=5 s: refuse to answer, return WRONG_OWNER
    Note over E: even if A1 answered, Lease(epoch 7) < seen epoch 8, dropped
    E->>ET: refresh shard map
```

```mermaid
%% D5d: 10x demand step. One interval of overshoot, then payback from the deficit.
sequenceDiagram
    autonumber
    participant C as Clients (D = 10 L)
    participant E as Enforcers (2,000)
    participant A as Allocator
    Note over E: t=0: old lease shares sum to L, local caps 2x share, bootstrap for new keys
    C->>E: 10 L requests/s
    E->>E: t=0 to 100 ms: admit up to caps, 2 L x 0.1 s = 0.2 L requests (0.1 L allowed)
    E->>A: t=100 ms: Report wanted=1.0 L, hits=0.2 L (per 100 ms)
    A->>A: bucket: 0.1 L - 0.2 L = -0.1 L, reject_for_ms = 100
    A-->>E: Lease(reject_fraction 0.9, reject_for_ms 100)
    E->>E: t=100 to 200 ms: reject all (paying back)
    E->>A: t=200 ms: Report wanted=1.0 L, hits~0
    A-->>E: Lease(reject_fraction 0.9, reject_for_ms 0)
    E->>E: steady: admit L, reject 9 L. First 1 s window ~L, 10 s window <= 1.01 L
```

## D6. Activity / decision flow

The hardest decision inside the enforcer: what to do with a key on each request given its lease state.

```mermaid
%% D6: enforcer decision per key. Which state is this key in, and what may I admit?
flowchart TD
    S[key from descriptor] --> L{lease present?}
    L -->|no| B{bootstrap bucket has tokens?}
    B -->|yes| ADM[ALLOW, hits++, mark key for next report]
    B -->|no| REJ[429 Retry-After, rejected++, wanted++]
    L -->|yes| F{"lease fresh?<br/>age below ttl"}
    F -->|no| G{"in grace?<br/>age below ttl + 10 s"}
    G -->|yes| RF[use last share as refill rate]
    G -->|no| SP{on_control_loss}
    SP -->|open| ADM
    SP -->|local_cap x| CAP[refill at x] --> TB
    SP -->|static_split| SS[refill at rate / expected_enforcers] --> TB
    F -->|yes| RJF{"reject_for_ms remaining<br/>or hash of request below reject_fraction?"}
    RJF -->|yes| REJ
    RJF -->|no| RF
    RF --> TB{"local bucket has token?<br/>cap 2x share"}
    TB -->|yes| ADM
    TB -->|no| REJ

    class S client
    class L,B,F,G,SP,RJF,TB decision
    class ADM,RF,CAP,SS service
    class REJ cache

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef cache    fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

## D7. Entity relationship

Embedded in [`solution.md` §3.3](solution.md#33-data-model). Not repeated here.

## D8. State machine

Lifecycle of a limit key on one enforcer.

```mermaid
%% D8: a key's lease state on one enforcer. Grace is the bridge over an allocator failover.
stateDiagram-v2
    [*] --> Unseen
    Unseen --> Bootstrap : first hit, admit from bootstrap bucket
    Bootstrap --> Leased : lease arrives (next report)
    Leased --> Leased : report / lease every T, policy version bump
    Leased --> Deficit : lease carries reject_for_ms > 0
    Deficit --> Leased : reject_for_ms elapsed
    Leased --> Grace : no lease for ttl (1 s)
    Deficit --> Grace : no lease for ttl
    Grace --> Leased : allocator answers (possibly learning-mode echo)
    Grace --> SafePolicy : grace exhausted (10 s)
    SafePolicy --> Leased : allocator answers
    Leased --> Idle : no hits for 60 s
    Idle --> Bootstrap : hit again
    Idle --> [*] : evicted after 10 min
```

## D9. Deployment / topology

Where each piece runs. One region, three zones.

```mermaid
%% D9: one region. Enforcers are zonal and stateless; allocators are zonal with cross-zone shard ownership; etcd spans zones.
flowchart TD
    subgraph Z1[Zone a]
        E1[Enforcers x700<br/>gateway pods]
        A1[Allocators x7<br/>own ~1,365 virtual shards]
        ET1[(etcd member)]
    end
    subgraph Z2[Zone b]
        E2[Enforcers x700]
        A2[Allocators x7]
        ET2[(etcd member)]
    end
    subgraph Z3[Zone c]
        E3[Enforcers x600]
        A3[Allocators x6]
        ET3[(etcd member)]
    end
    E1 -->|"reports cross zone by shard, ~1 ms"| A2
    E2 -->|"reports"| A3
    E3 -->|"reports"| A1
    A1 <-->|"raft"| ET1
    ET1 <-->|"raft, 3 of 3"| ET2
    ET2 <-->|"raft"| ET3
    PS[(Policy store<br/>regional, replicated)] -->|"watch"| A1
    PS -->|"watch"| A2
    PS -->|"watch"| A3

    class E1,E2,E3,A1,A2,A3 service
    class ET1,ET2,ET3,PS store

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
```

Zone loss: the 1/3 of enforcers there are gone with their traffic (the load balancer moves it). The 1/3 of shards owned there fail over within 5 s. etcd keeps quorum with 2 of 3. Reports cross zones because ownership is by key, not by zone; the ~1 ms cross-zone RTT is fine on a 100 ms loop. Zone-local ownership would be cheaper but would give each zone its own view of one key, which is the `L / N` problem with `N = 3`.

## D10. Scaling / partitioning

Keys are owned by the hash of the tree root. The 30% account is the hot shard; delegated budgets split it.

```mermaid
%% D10: partitioning by tree root, and the delegated-budget split for the hot account.
flowchart LR
    K1["account:small-1 tree<br/>account, 3 workspaces, 40 users"] -->|"hash(root) % 4096"| S7[Shard 7 on node A]
    K2["account:small-2 tree"] -->|"hash(root)"| S7
    K3["endpoint:/query flat key"] -->|"hash(key)"| S9[Shard 9 on node B]
    K4["account:big tree<br/>30% of traffic, 100 k users"] -->|"hash(root)"| S3[Shard 3 on node C<br/>1.8 M entries/s, 100 k-node walk]
    S3 -->|"split: budget lease per workspace per 100 ms"| S11["Shard 11: workspace big/ws-1 subtree"]
    S3 -->|"budget lease"| S12["Shard 12: workspace big/ws-2 subtree"]
    S11 -->|"leases to enforcers"| E[Enforcers]
    S12 -->|"leases"| E
    S3 -->|"only k workspace summaries in"| S3

    class K1,K2,K3,K4 client
    class S7,S9,S11,S12 service
    class S3 critical
    class E service

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
```

After the split, shard 3 sees `k` workspace-level rows per interval instead of 100 k user rows, and each workspace shard does its own water-fill among users. Cross-workspace fairness is one interval staler. The split is a policy attribute (`delegate_children: true` on the account node) so it can be applied per tenant without redeploys.

## D11. Failure mode map

```mermaid
%% D11: what fails, who feels it, what limits the damage.
flowchart TD
    F1[Enforcer pod dies] -->|"blast: its in-flight requests"| M1[LB reroutes; counters worth one interval lost]
    F2[Allocator node dies] -->|"blast: its shards' keys, 5 to 7 s"| M2[old lease, then grace share; etcd expiry; new owner in learning mode]
    F3[etcd unavailable] -->|"blast: no ownership changes"| M3[owners serve until local lease clock expires, then step down; fleet goes to safe policy; page]
    F4[Policy store unavailable] -->|"blast: no policy changes"| M4[allocators keep last policy; leases keep flowing]
    F5[Bad policy pushed] -->|"blast: one tenant, fleet-wide, 200 ms"| M5[validation, shadow default for new nodes, one-command rollback]
    F6[Network partition, enforcers vs allocators] -->|"blast: partitioned enforcers"| M6[grace 10 s, then per-RLG safe policy]
    F7[Hot account shard at 100% CPU] -->|"blast: that account's leases go stale"| M7[delegate_children, report suppression, alert at 60%]
    F8[Clock jump on a pod] -->|"blast: none"| M8[monotonic clocks, durations in leases]
    F9[Report storm from a buggy enforcer] -->|"blast: one allocator's CPU"| M9[per-enforcer report rate limit 100/s, mTLS identity]

    class F1,F2,F3,F4,F6,F8,F9 client
    class F5,F7 critical
    class M1,M2,M3,M4,M5,M6,M7,M8,M9 service

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
```

## D12. Rollout / migration

From "Envoy → rate limit service → Redis" to this design. Each phase has a rollback that is a flag flip because both paths see every request.

```mermaid
%% D12: migration. Shadow first, then flip RLG by RLG, then remove the old path.
gantt
    title Migration from synchronous Redis limiter
    dateFormat  YYYY-MM-DD
    axisFormat  %b %d
    section Foundations
    Allocator + etcd ownership in prod, no traffic     :a1, 2026-10-01, 14d
    Enforcer sidecar next to Envoy, shadow mode         :a2, after a1, 7d
    section Validate
    Compare would_reject vs Redis rejects per key       :b1, after a2, 14d
    Traffic simulation - burst, failover, partition      :b2, after a2, 14d
    section Flip
    Flip low-risk RLGs, old path in shadow (rollback - flag) :c1, after b1, 7d
    Flip tenant-facing RLGs, canary 1 percent then all  :c2, after c1, 14d
    Flip external-quota RLGs with static_split safe policy :c3, after c2, 7d
    section Retire
    Redis to read-only, alarms on any write             :d1, after c3, 7d
    Remove old filter and Redis                         :d2, after d1, 7d
```

Rollback points: end of each phase. Before `d2`, rollback is a flag on the Envoy filter chain (which path enforces, which shadows). After `d2`, rollback means redeploying the old filter, which is why Redis stays read-only for a week first.
