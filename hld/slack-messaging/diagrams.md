# Diagrams: Slack / large-scale messaging platform

The D1 to D12 set from `hld/CLAUDE.md` §4. Diagrams already embedded in [`solution.md`](solution.md) are linked, not pasted twice. Colors per root `CLAUDE.md` §3. Red is only for the thing that breaks first: the owner of a hot channel.

| # | Diagram | Where |
|---|---|---|
| D1 | Context | below |
| D2 | Data flow | below |
| D3 | Component architecture | [`solution.md` §6](solution.md#6-final-design) |
| D4 | Happy path per FR | FR1 send and FR3 sync in `solution.md` §4.1 and §4.3; FR2 receive, FR4 unread, FR5 presence below |
| D5 | Failure paths | owner failover in §5.1, gateway death and region loss in §10.4; slow gateway resync and duplicate send below |
| D6 | Decision flow: gateway delivery | below |
| D7 | Entity relationship | [`solution.md` §3.3](solution.md#33-data-model) |
| D8 | State machines: message, socket session, owner actor | below |
| D9 | Deployment topology | below |
| D10 | Scaling and partitioning | below |
| D11 | Failure mode map | below |
| D12 | Migration from workspace sharding | below |

---

## D1. Context

Our system is one box. Everything around it and what flows on each edge.

```mermaid
%% D1: the messaging platform in its environment
flowchart LR
    U[Users on web, desktop, mobile<br/>5 devices per user] -- "send, subscribe, sync<br/>receive events" --> M[Messaging platform<br/>gateways, owners, store]
    B[Bots and integrations<br/>via API] -- "send, read" --> M
    ADM[Workspace admins] -- "retention, roles,<br/>shared channel approval" --> M
    M -- "push notifications" --> APN[APNs / FCM]
    M -- "attachment pointers,<br/>signed upload URLs" --> BLOB[Blob store]
    M -- "message events (CDC)" --> SRCH[Search index]
    M -- "metrics, traces" --> MON[Monitoring]
    ID[Identity / SSO] -- "session tokens" --> M
    M -. "async replication" .-> DR[DR region]

    class U,B,ADM client
    class M service
    class APN,BLOB,SRCH,MON,ID,DR external

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

## D2. Data flow

Inputs to outputs with name, format, size, and rate at peak.

```mermaid
%% D2: data flow with sizes. Stores as cylinders, processes as rounded boxes.
flowchart LR
    C[Client] -- "POST message<br/>JSON ~1 KB, 350k/s" --> API(API tier)
    API -- "append RPC<br/>protobuf ~1 KB, 350k/s" --> OWN(Channel owner)
    OWN -- "INSERT IF NOT EXISTS<br/>batched, ~70k LWT/s" --> MS[(Message store<br/>3 TB/day)]
    OWN -- "deliver event<br/>~1 KB, 7M/s to gateways" --> GW(Gateway)
    GW -- "WS message ~1 KB to open sessions<br/>WS tick ~40 B to watched<br/>9M pushes/s" --> C
    OWN -- "mention / push / index events<br/>~200 B, 500k/s peak" --> K[[Kafka]]
    K -- "consume" --> W(Workers)
    W -- "counter += 1" --> CUR[(Cursor store<br/>50k writes/s)]
    W -- "notify ~300 B" --> PUSH[APNs / FCM]
    W -- "index doc ~1 KB" --> IDX[(Search index)]
    C -- "POST /sync<br/>{channel: seq} x 200, 20/min/session" --> SY(Sync service)
    SY -- "cursors, 170k reads/s at 9 am" --> CUR
    SY -- "heads for active channels" --> OWN
    C -- "GET after / before<br/>50 to 200 rows, 2M reads/s" --> MS
    GW -- "heartbeat 30 s<br/>670k/s" --> PR(Presence)
    PR -- "SET EX 60" --> RD[/Redis/]

    class C client
    class API,OWN,GW,W,SY,PR service
    class MS,CUR,IDX store
    class K queue
    class RD cache
    class PUSH external

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef cache    fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

## D3. Component architecture

See [`solution.md` §6](solution.md#6-final-design).

## D4. Happy paths per FR

FR1 send: [`solution.md` §4.1](solution.md#41-send-a-message-who-decides-the-order-and-is-it-durable). FR3 sync: [`solution.md` §4.3](solution.md#43-history-and-reconnect-sync).

### D4.2 FR2: receive on every device, including the sender's other devices

```mermaid
%% D4.2: one message, two members, one of them on two devices on two gateways
sequenceDiagram
    autonumber
    participant O as Owner C42 (epoch 8)
    participant G1 as Gateway G1
    participant G2 as Gateway G2
    participant A1 as Alice laptop (C42 open)
    participant A2 as Alice phone (C42 watched)
    participant B1 as Bob (C42 open)
    Note over O: seq 1006 applied at quorum, sender acked
    O->>G1: deliver(C42, 1006, epoch 8, body)
    O->>G2: deliver(C42, 1006, epoch 8, body)
    G1->>G1: epoch 8 >= last seen 8? yes. subs[C42] = {A1, B1}
    G1-->>A1: message(C42, 1006, body). Client checks 1006 == 1005 + 1
    G1-->>B1: message(C42, 1006, body)
    G2->>G2: subs[C42] = {A2}, A2 has C42 watched
    G2-->>A2: tick(C42, head 1006) coalesced 1/s. Badge = 1006 - last_read
```

### D4.4 FR4: unread and mentions across devices

```mermaid
%% D4.4: Alice reads on her phone, her laptop's badge clears within one delivery latency
sequenceDiagram
    autonumber
    participant P as Alice phone
    participant API as API
    participant CUR as Cursor store
    participant UO as Owner of user:alice
    participant G1 as Gateway G1
    participant L as Alice laptop
    P->>API: POST /channels/C42/read {last_read_seq: 1006}
    API->>CUR: last_read_seq = max(1001, 1006), unread_mentions = 0
    API-->>P: ok
    API->>UO: append(user:alice, read(C42, 1006))
    UO->>G1: deliver(user:alice, read event) once per gateway with alice sessions
    G1-->>L: read(C42, 1006). Laptop badge 5 -> 0
    Note over CUR: Mentions: Kafka worker does unread_mentions += 1 only for messages that mention alice
```

### D4.5 FR5: presence for visible users only

```mermaid
%% D4.5: presence is a subscription to the users on screen, batched every 5 s
sequenceDiagram
    autonumber
    participant B as Bob's client
    participant G as Gateway
    participant PR as Presence service
    participant R as Redis
    participant A as Alice's client
    A->>G: ping (every 30 s)
    G->>PR: heartbeat(alice)
    PR->>R: SET presence:alice active EX 60
    B->>G: WS subscribe presence [alice, carol, ... 200 visible users]
    G->>PR: subscribe(G, [alice, ...])
    PR->>PR: alice active -> away (TTL expired at 60 s, or explicit)
    PR->>G: batch every 5 s: [{alice: away}, {carol: active}]
    G-->>B: presence batch to sessions with those users visible
    Note over B,A: If Redis dies: everyone "unknown". Messages unaffected.
```

## D5. Failure paths

Owner failover mid-send: [`solution.md` §5.1](solution.md#51-two-senders-in-the-same-millisecond-who-is-first-and-what-if-the-owner-dies). Gateway death and region loss: [`solution.md` §10.4](solution.md#104-failure-timelines).

### D5.3 Slow gateway: backpressure turns push into pull

```mermaid
%% D5.3: a gateway falls behind, the owner drops its queue and tells it to resync instead of blocking
sequenceDiagram
    autonumber
    participant O as Owner C42
    participant Q as Outbound queue -> G3 (cap 10k)
    participant G3 as Gateway G3 (GC pause)
    participant C as Clients on G3
    O->>Q: deliver 1007 .. 11006 (10k events, G3 not draining)
    O->>Q: deliver 11007: queue full
    O->>Q: drop all queued for G3, enqueue single resync(C42, head 11007)
    Note over O: other gateways unaffected, owner never blocked
    G3->>G3: resumes, reads resync(C42, 11007)
    G3-->>C: resync(C42, 11007) to every session subscribed to C42
    C->>C: open sessions: GET after=last_seen (bounded, truncated if > 10k)
    C->>C: watched sessions: treat as tick(11007)
```

### D5.4 Duplicate send after a client timeout

```mermaid
%% D5.4: client retries with the same client_msg_id, no second seq is ever assigned
sequenceDiagram
    autonumber
    participant C as Client
    participant API as API
    participant O as Owner C42
    participant DB as Message store
    C->>API: POST msg client_msg_id u5
    API->>O: append(C42, u5)
    O->>DB: INSERT (C42, 1008, u5) IF NOT EXISTS
    DB-->>O: applied
    Note over API,C: response lost on the network
    C->>API: retry POST msg u5 (same id)
    API->>O: append(C42, u5)
    O->>O: LRU hit u5 -> seq 1008
    O-->>C: 200 {seq: 1008}
    Note over O: if the LRU was evicted (failover): lookup dedup table (C42, u5) -> 1008, 24 h TTL
```

## D6. Decision flow: what a gateway does with a delivered event

```mermaid
%% D6: gateway delivery logic per event per session. The hardest branching in the system.
flowchart TD
    E[deliver event arrives<br/>channel C, seq N, epoch e] --> EP{epoch e >= last<br/>epoch seen for C?}
    EP -- no --> DROP1[Drop: stale owner]
    EP -- yes --> HAS{any local sessions<br/>subscribed to C?}
    HAS -- no --> UNSUB[Unsubscribe from owner<br/>after 60 s grace]
    HAS -- yes --> LOOP[For each session S in subs C]
    LOOP --> OPEN{C open<br/>on S?}
    OPEN -- yes --> GAP{N == last_delivered S,C + 1?}
    GAP -- yes --> SEND[Write full event to socket<br/>last_delivered = N]
    GAP -- no, N greater --> RESYNC[Send resync C, N<br/>client pulls after=last]
    GAP -- no, N smaller or equal --> DROP2[Drop: already delivered]
    OPEN -- no, watched --> TICK{tick for C sent<br/>in last 1 s?}
    TICK -- yes --> COAL[Coalesce: update pending head]
    TICK -- no --> SENDT[Write tick C, N]
    SEND --> QF{socket write<br/>queue full?}
    QF -- yes --> KILL[Close socket<br/>client reconnects with backoff]
    QF -- no --> DONE[Done]

    class E service
    class EP,HAS,OPEN,GAP,TICK,QF decision
    class DROP1,DROP2,UNSUB,SEND,RESYNC,COAL,SENDT,DONE,LOOP service
    class KILL critical

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
```

## D7. Entity relationship

See [`solution.md` §3.3](solution.md#33-data-model).

## D8. State machines

### D8.1 Message

```mermaid
%% D8.1: a message from the client's point of view and the server's
stateDiagram-v2
    [*] --> Composing
    Composing --> Sending: POST with client_msg_id
    Sending --> Sending: timeout, retry same id (backoff)
    Sending --> Acked: 200 {seq}
    Sending --> Failed: 4xx (not a member, rate limited, too large)
    Acked --> Delivered: members' gateways pushed it (best effort)
    Delivered --> Read: member advanced cursor past seq
    Acked --> Edited: edit event with new seq, target = seq
    Edited --> Edited: further edits
    Acked --> Deleted: tombstone; row kept, body cleared
    Edited --> Deleted
    Deleted --> [*]: retention TTL expires
    Read --> [*]: retention TTL expires
```

### D8.2 Socket session at the gateway

```mermaid
%% D8.2: one websocket session. Backoff and admission happen before Connected.
stateDiagram-v2
    [*] --> Connecting: token
    Connecting --> Rejected: admission full, retry-after
    Rejected --> Connecting: backoff 1 s .. 60 s, full jitter
    Connecting --> Connected: token valid
    Connected --> Subscribed: subscribe open + watched channels, presence list
    Subscribed --> Subscribed: events, ticks, ping/pong every 30 s
    Subscribed --> Draining: gateway deploy, reconnect(after jitter)
    Subscribed --> Dead: 2 pings missed or write queue full
    Draining --> Connecting: client reconnects elsewhere
    Dead --> Connecting: client detects, backoff
    Subscribed --> [*]: client logout
```

### D8.3 Owner actor for one channel

```mermaid
%% D8.3: the per-channel actor inside an owner node. Fenced by epoch at Loading.
stateDiagram-v2
    [*] --> Unloaded
    Unloaded --> Loading: first append or subscribe
    Loading --> Serving: read head, CAS epoch old -> old+1 succeeded
    Loading --> Unloaded: CAS failed (another owner won), return NOT_OWNER
    Serving --> Serving: append, deliver, subscribe, heartbeat
    Serving --> Fenced: lease lost or ring moved channel away
    Fenced --> Unloaded: drop queues, reply NOT_OWNER to in-flight
    Serving --> Unloaded: idle 30 min, evict
```

## D9. Deployment topology

```mermaid
%% D9: home region holds owners and stores; gateways are everywhere; DR is async
flowchart TD
    subgraph EU [EU region: home for EU workspaces]
        subgraph AZ1 [AZ a]
            G1[Gateways x67]
            O1[Owners x33]
            M1[(Store replica 1)]
        end
        subgraph AZ2 [AZ b]
            G2[Gateways x67]
            O2[Owners x33]
            M2[(Store replica 2)]
        end
        subgraph AZ3 [AZ c]
            G3[Gateways x67]
            O3[Owners x34]
            M3[(Store replica 3)]
        end
        K[Coordination store<br/>5 nodes across AZs]
        Q[[Kafka, 6 brokers,<br/>ISR 2 across AZs]]
    end
    subgraph US [US region]
        GU[Gateways for US users<br/>of EU workspaces]
        MU[(DR replica of EU store<br/>async, lag ~2 s)]
        OU[Owners for US-homed<br/>workspaces]
    end
    O1 -- "LOCAL_QUORUM<br/>2 of 3 AZs" --> M1
    O1 --> M2
    O1 --> M3
    GU -- "subscribe / deliver<br/>over backbone ~80 ms" --> O1
    M1 -. "async replication" .-> MU
    K -. "leases" .-> O1

    class G1,G2,G3,GU,O1,O2,O3,OU service
    class M1,M2,M3,MU,K store
    class Q queue

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
```

What crosses a region boundary: gateway subscriptions and deliveries for users away from their workspace's home (adds ~80 ms), async store replication (RPO), nothing on the LWT path.

## D10. Scaling and partitioning

```mermaid
%% D10: two rings and one store, all keyed by channel_id. The hot partition is the busy channel's latest bucket.
flowchart LR
    CH[channel_id] -- "consistent hash<br/>100 vnodes per owner" --> OR[Owner ring<br/>100 nodes, ~1% channels each]
    CH -- "partition key<br/>channel_id, seq / 10000" --> P0[(bucket 0<br/>seq 0..9999, ~10 MB)]
    CH --> P1[(bucket 1<br/>seq 10000..19999)]
    CH --> PN[(bucket N, latest<br/>all writes + live reads)]:::critical
    U[user_id] -- "partition key" --> CU[(cursors: one partition<br/>per user, 200 rows)]
    OR -- "one actor per channel<br/>ring change moves 1/N" --> OR2[Add owner node:<br/>1% of channels move,<br/>actors reload heads]
    PN -- "fix: owner 100-msg cache,<br/>read coalescing, per-channel<br/>rate limit 1k/s" --> FIX[Hot partition contained]

    class OR,OR2,FIX service
    class P0,P1,CU store
    class CH,U client
    class PN critical

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
```

## D11. Failure mode map

```mermaid
%% D11: component -> what fails -> blast radius -> mitigation
flowchart TD
    GW[Gateway node] --> GWF[200k sockets drop] --> GWB[0.5% of users, 30 s reconnect] --> GWM[Backoff + jitter, admission, no durable state]
    OW[Owner node] --> OWF[1% of channels cannot send] --> OWB[~11 s per channel] --> OWM[Lease expiry, ring reassign, LWT fence, client retry same id]
    HOT[One hot channel] --> HOTF[Owner actor saturated]:::critical --> HOTB[That channel slow, node neighbours slower] --> HOTM[Per-channel rate limit, relay split later]
    MS[Message store AZ] --> MSF[1 of 3 replicas gone] --> MSB[LWT p99 up, no data loss] --> MSM[LOCAL_QUORUM survives; repair on return]
    K[Coordination store] --> KF[Ring frozen] --> KB[Nothing until an owner also dies] --> KM[Page; owners keep serving on last lease view]
    KA[Kafka] --> KAF[Mentions, push, index stall] --> KAB[Badges lag, no message impact] --> KAM[Replay on recovery, 3 d retention]
    RD[Presence Redis] --> RDF[Presence unknown] --> RDB[Cosmetic] --> RDM[Separate SLO, rebuild from heartbeats in 60 s]
    RG[Home region] --> RGF[All sends for its workspaces fail] --> RGB[RTO ~10 min, RPO ~2 s] --> RGM[Promote DR, rebuild ring, flip home]
    CL[Bad client release] --> CLF["/sync storm"] --> CLB[Everyone] --> CLM[Server-side version kill switch]

    class GW,OW,MS,K,KA,RD,RG,CL,HOT service
    class GWF,OWF,MSF,KF,KAF,RDF,RGF,CLF decision
    class GWB,OWB,MSB,KB,KAB,RDB,RGB,CLB,HOTB store
    class GWM,OWM,MSM,KM,KAM,RDM,RGM,CLM,HOTM service
    class HOTF critical

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
```

## D12. Migration from workspace-sharded MySQL to channel-keyed storage with an owner ring

This is the Slack Vitess story with a rollback point per phase. Each phase is flag-controlled; rollback is flipping the flag.

```mermaid
%% D12: zero-downtime migration. Old path authoritative until phase 4.
gantt
    title Migration: workspace shards -> channel-keyed store + owner ring
    dateFormat  YYYY-MM-DD
    axisFormat  %b
    section Phase 1 shadow
    Owner ring in shadow, assigns seq, writes new store, old path still acks     :p1, 2026-01-01, 30d
    Nightly diff old vs new (count, order)                                         :p1b, 2026-01-10, 21d
    section Phase 2 dual read
    1% of channels read history from new store, diff against old                   :p2, 2026-02-01, 21d
    Rollback point, flag off, old store serves                                     :milestone, 2026-02-22, 0d
    section Phase 3 backfill
    Copy historical rows per channel (VReplication-style), verify counts           :p3, 2026-02-15, 45d
    section Phase 4 cutover
    Per-workspace flag, new path authoritative, dual-write to old for 14 d         :p4, 2026-04-01, 30d
    Rollback point, flip flag back, old store is current                           :milestone, 2026-04-15, 0d
    section Phase 5 retire
    Stop old writes, archive old shards                                            :p5, 2026-05-01, 14d
```

Backfill needs care on one point: historical messages have no `seq`. Assign seqs in `ts` order per channel during backfill, and start the owner's `head_seq` above the backfilled maximum before phase 4 flips that workspace. Rollback after phase 4 needs a reverse copy of anything written to the new store during dual-write, which is why dual-write to the old store stays on for 14 days.
