# Diagrams: stock trading / order execution system

The D1 to D12 set for [`solution.md`](solution.md). Each diagram appears once in the repo: the ones embedded in `solution.md` are linked from here, not repeated. Colors per root `CLAUDE.md` §3. Red is used only for the single-writer matcher of the hottest symbol (the one core that is the ceiling) and, in the failure map, for the sequencer's replicated log (the one thing that must not lose a byte).

Legend reminder: 🔵 client / edge, 🟢 stateless compute, 🟣 durable storage, 🟡 cache or losable, 🔷 queue / log, 🔴 bottleneck or SPOF, ⚪ external, 🩷 decision.

---

## D1. Context (zoom-out)

Our system is the exchange: gateways, risk, sequencer, matchers, publishers, post-trade. Members and retail apps send orders in; clearing takes the trade file out; the regulator gets the audit trail.

```mermaid
%% D1: context. Orders in from members and retail, prices out to everyone, trades out to clearing, every event out to audit.
flowchart LR
    M[Member firms<br/>FIX / OUCH sessions in colo] -->|"NewOrder, Cancel, Replace"| SYS[Order execution system<br/>gateway, risk, sequencer,<br/>matcher, publishers, post-trade]
    SYS -->|"ExecutionReport, in session order"| M
    R[Retail apps via broker<br/>REST + WebSocket] -->|"orders"| SYS
    SYS -->|"fills, live prices"| R
    SYS -->|"ITCH-style L2 / L3 feed<br/>multicast in colo"| MD[Market data consumers<br/>vendors, SIP, algos]
    SYS -->|"trade file, netted, end of day"| CH[Clearing house<br/>NSCC / DTCC]
    CH -->|"settlement T+1"| SYS
    SYS -->|"every order event, 6 yr"| REG[Regulator / CAT<br/>audit trail]
    OPS[Exchange operations] -->|"halt, kill switch, params"| SYS

    class M,R,OPS client
    class SYS service
    class MD,CH,REG external

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

## D2. Data flow (DFD)

What flows, how big, how often. Peak numbers for the first minute after the open.

```mermaid
%% D2: data flow. Two logs carry everything: the sequenced input log and the matcher output log. Every store is a projection of them.
flowchart LR
    C[Clients] -->|"order msg, binary ~64 B<br/>500 k/s peak, 43 k/s avg"| GW(Gateway<br/>auth, ClOrdID dedup, normalise)
    GW -->|"risk check request<br/>~80 B, same rate"| RK(Risk engine<br/>per account shard)
    RK -->|"approved order + hold id"| SQ(Sequencer<br/>per symbol group)
    SQ -->|"append seq, ts<br/>~100 B x 500 k/s = 50 MB/s"| IL[[Input log<br/>replicated 3x, ~100 GB/day]]
    IL -->|"tail, in seq order"| ME(Matching engine<br/>one thread per shard)
    ME -->|"ack, fill, cancel, book delta<br/>~2 events per input, ~150 B"| OL[[Output log<br/>~200 GB/day]]
    OL -->|"per session, per seq"| ER(Execution report publisher)
    ER -->|"ExecutionReport ~150 B"| C
    OL -->|"book deltas"| MP(Market data publisher)
    MP -->|"L2 incremental, multicast<br/>~1 M msg/s peak"| MD[Market data consumers]
    OL -->|"fills only, ~100 M/day"| PT(Post-trade<br/>ledger, positions)
    PT -->|"double-entry postings"| LG[(Ledger DB<br/>per account)]
    OL -->|"every event"| AU[(Audit store<br/>object storage, 6 yr)]
    OL -->|"projection"| OD[(Order DB<br/>query by order, account)]

    class C,MD client
    class GW,RK,SQ,ME,ER,MP,PT service
    class IL,OL queue
    class LG,AU,OD store

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
```

## D3. Component architecture

Embedded in [`solution.md` §6](solution.md#6-final-design). Not repeated here.

## D4. Sequence, happy path, one per FR

D4a (place and match a limit order) is embedded in [`solution.md` §4.1](solution.md#41-place-an-order-and-match-it-by-price-time-priority). The rest are here.

### D4b. Cancel a working order

```mermaid
%% D4b: cancel. The cancel is sequenced like any order, so it either finds the order resting or arrives after the fill.
sequenceDiagram
    autonumber
    participant C as Client
    participant GW as Gateway
    participant SQ as Sequencer
    participant ME as Matcher
    participant ER as Exec report publisher
    C->>GW: OrderCancelRequest(ClOrdID=c2, OrigClOrdID=c1)
    GW->>GW: map c1 to exchange order id 7781, dedup c2
    GW->>SQ: Cancel(order 7781)
    SQ->>SQ: seq 90212, replicate, ack
    SQ->>ME: seq 90212 Cancel 7781
    alt order 7781 still on the book
        ME->>ME: lookup map[7781], unlink from price level, O(1)
        ME->>ER: out event Cancelled(7781, seq 90212)
        ER-->>C: ExecutionReport(ExecType=Canceled, leaves=0)
    else order 7781 already filled at seq 90190
        ME->>ER: out event CancelReject(7781, reason=too late)
        ER-->>C: OrderCancelReject(CxlRejReason=TooLateToCancel)
    end
```

### D4c. Pre-trade risk hold before sequencing

```mermaid
%% D4c: the hold. Buying power is reserved on the account shard before the order reaches the symbol shard. Release is driven by matcher output.
sequenceDiagram
    autonumber
    participant GW as Gateway
    participant RK as Risk engine (account A shard)
    participant SQ as Sequencer (symbol shard)
    participant ME as Matcher
    participant PT as Post-trade
    GW->>RK: Check(account A, buy 100 XYZ @ 50.00, ClOrdID)
    RK->>RK: collar ok, size ok, notional 5,000 <= available 12,000
    RK->>RK: available -= 5,000, hold h1 (in memory + WAL)
    RK-->>GW: Approved(hold h1)
    GW->>SQ: NewOrder(..., hold h1)
    SQ->>ME: seq n
    ME->>PT: Fill 100 @ 49.98 (notional 4,998)
    PT->>RK: Release(h1, used 4,998)
    RK->>RK: hold h1 closed, available += 2 (unused part)
    Note over RK,PT: On reject or cancel the same Release arrives with used=0
```

### D4d. Execution report delivery with session sequence numbers

```mermaid
%% D4d: every message to a session carries a per-session MsgSeqNum. The client detects a gap and asks for a resend from the output log.
sequenceDiagram
    autonumber
    participant ER as Exec report publisher
    participant C as Client session S
    ER->>C: ExecReport seq 501 (Ack 7781)
    ER->>C: ExecReport seq 502 (Fill 7781, 40)
    Note over ER,C: TCP reconnect, message 503 lost in flight
    ER->>C: ExecReport seq 504 (Fill 7781, 60)
    C->>ER: ResendRequest(503, 503)
    ER->>ER: read output log at session cursor 503
    ER->>C: ExecReport seq 503 PossDup=Y (Fill 7781, 0 partial ack)
    C->>C: apply 503, then buffered 504, in order
```

### D4e. Market data snapshot plus incremental

```mermaid
%% D4e: a consumer joins mid-day. It buffers incrementals, fetches a snapshot, and applies buffered updates newer than the snapshot seq.
sequenceDiagram
    autonumber
    participant MP as Market data publisher
    participant S as Snapshot service
    participant K as Consumer
    K->>MP: subscribe XYZ L2
    MP->>K: incremental seq 1001, 1002, 1003 (buffered by K)
    K->>S: get snapshot XYZ
    S-->>K: snapshot as of seq 1001 (10 levels each side)
    K->>K: drop 1001, apply 1002, 1003
    MP->>K: incremental seq 1004
    K->>K: apply, book is live
    Note over MP,K: gap detected at any point: rebuffer, re-snapshot
```

## D5. Sequence, failure paths

D5a (matcher crashes between match and publish) is embedded in [`solution.md` §10.4](solution.md#104-failure-timeline). The rest are here.

### D5b. Client retry creates a duplicate order attempt

```mermaid
%% D5b: the client's ack is lost, it retries with the same ClOrdID. The gateway's dedup table answers from the log, no second order is created.
sequenceDiagram
    autonumber
    participant C as Client
    participant GW as Gateway
    participant SQ as Sequencer
    participant ME as Matcher
    C->>GW: NewOrderSingle(ClOrdID=c1)
    GW->>GW: dedup[session, c1] = pending
    GW->>SQ: NewOrder
    SQ->>ME: seq 3301
    ME-->>GW: Ack(order 9001, seq 3301)
    GW->>GW: dedup[session, c1] = order 9001
    Note over GW,C: ack lost on the wire, client times out after 1 s
    C->>GW: NewOrderSingle(ClOrdID=c1) again
    GW->>GW: dedup hit, order 9001
    GW-->>C: ExecutionReport(Ack, order 9001, PossResend)
    Note over GW: dedup entry lives until session end + 1 day, rebuilt from the output log on gateway restart
```

### D5c. Sequencer leader loses its lease mid-burst

```mermaid
%% D5c: leader election on the replicated log. The new leader owns a new epoch, the old leader's late writes are fenced.
sequenceDiagram
    autonumber
    participant GW as Gateways
    participant L1 as Sequencer leader (epoch 4)
    participant F as Followers (2)
    participant L2 as New leader (epoch 5)
    GW->>L1: orders
    L1->>F: append seq 5000..5010, wait 1 of 2 acks
    Note over L1: t=0 GC pause / NIC failure, no heartbeats
    F->>F: t=300 ms election timeout, vote, L2 wins epoch 5
    L2->>L2: log ends at seq 5008 (5009, 5010 never reached a quorum)
    GW->>L2: t=350 ms retry 5009, 5010 with same ClOrdIDs
    L2->>F: append as seq 5009, 5010, epoch 5
    L1->>F: t=400 ms late append seq 5011 epoch 4
    F-->>L1: reject, epoch 4 < 5 (fenced)
    Note over GW,L2: orders 5009, 5010 were never acked to clients under epoch 4, so no ack is contradicted
```

### D5d. Broker variant: venue confirms a fill after our timeout

```mermaid
%% D5d: we are the broker. The venue filled the order but our call timed out. The order stays PENDING until the venue's own record says what happened.
sequenceDiagram
    autonumber
    participant U as User app
    participant OMS as Our order service
    participant DB as Our order DB
    participant V as Venue (external)
    participant DC as Drop copy / recon
    U->>OMS: buy 10 XYZ
    OMS->>DB: insert order PENDING_NEW, ClOrdID c9
    OMS->>V: NewOrder(c9)
    Note over OMS,V: no response in 2 s
    OMS->>DB: order stays PENDING_NEW, flag unknown_at_venue
    OMS-->>U: "order submitted, awaiting confirmation"
    V-->>OMS: t=5 s ExecutionReport Fill(c9) arrives on the session
    OMS->>DB: PENDING_NEW to FILLED, idempotent on (c9, ExecID)
    OMS-->>U: push filled
    Note over DC: if nothing arrives in 30 s, OrderStatusRequest(c9) then drop copy reconciliation decides, never a blind retry with a new ClOrdID
```

## D6. Activity / decision flow

The matching loop for an incoming order, inside the matcher thread.

```mermaid
%% D6: the matching loop. Every branch is deterministic given the book state and the input event, no clock, no random, no IO.
flowchart TD
    A[Incoming order at seq n] --> B{Opposite side best price<br/>crosses the order?}
    B -->|no| C{Time in force?}
    C -->|IOC or FOK| D[Cancel remainder, emit Cancelled]
    C -->|day or GTC| E[Append to price level FIFO<br/>map order id to node<br/>emit Ack]
    B -->|yes| F{FOK and total available<br/>< order qty?}
    F -->|yes| D
    F -->|no| G[Take head order at best level<br/>fill min of both qtys<br/>at resting price]
    G --> H[Emit Fill x2, one per side<br/>trade id = seq n, fill index]
    H --> I{Resting order fully filled?}
    I -->|yes| J[Unlink head, if level empty<br/>clear bit, advance best]
    I -->|no| K[Decrement resting qty]
    J --> L{Incoming remainder > 0<br/>and next level still crosses?}
    K --> L
    L -->|yes| G
    L -->|no| C

    class A service
    class B,C,F,I,L decision
    class D,E,G,H,J,K service

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

## D7. Entity relationship

Embedded in [`solution.md` §3.3](solution.md#33-data-model). Not repeated here.

## D8. State machine

The order lifecycle as the matcher and the client see it. The broker variant adds `PENDING_NEW` and `UNKNOWN_AT_VENUE` in front (see [`deep-dives/broker-variant.md`](deep-dives/broker-variant.md)).

```mermaid
%% D8: order lifecycle. Terminal states are FILLED, CANCELLED, REJECTED, EXPIRED. Every transition is one output log event.
stateDiagram-v2
    [*] --> RiskCheck : NewOrder at gateway
    RiskCheck --> Rejected : collar, size, buying power, dup
    RiskCheck --> Sequenced : hold taken, seq assigned
    Sequenced --> Filled : crosses fully
    Sequenced --> PartiallyFilled : crosses partly
    Sequenced --> Working : rests on book, Ack
    Sequenced --> Cancelled : IOC or FOK remainder
    Working --> PartiallyFilled : opposite order arrives
    PartiallyFilled --> Filled : remainder crosses
    PartiallyFilled --> Cancelled : cancel wins race
    Working --> Cancelled : cancel wins race
    Working --> Replaced : replace, new seq, lose time priority if price or qty up
    Replaced --> Working
    Working --> Expired : day order at close
    Filled --> [*]
    Cancelled --> [*]
    Rejected --> [*]
    Expired --> [*]
```

## D9. Deployment / topology

One primary data centre, one warm DR site. Inside the primary: two halls (or AZs) with the matcher primary and hot standby split across them and the log's third replica in the other hall.

```mermaid
%% D9: topology. Primary and hot standby matchers for a shard never share a hall. The log has 3 replicas across 2 halls, ack on 2. DR replays the log asynchronously.
flowchart TB
    subgraph P["Primary DC (colo, members cross-connect here)"]
        subgraph H1["Hall 1"]
            GW1[Gateways x20]
            SQ1["Sequencer shard S (leader)"]
            ME1["Matcher S primary<br/>pinned core, busy spin"]
            L1[[log replica 1]]
        end
        subgraph H2["Hall 2"]
            GW2[Gateways x20]
            SQ2["Sequencer shard S (follower)"]
            ME2["Matcher S hot standby<br/>replays same log"]
            L2[[log replica 2]]
            L3[[log replica 3]]
        end
        RK[Risk engines<br/>sharded by account, x2 each]
        PUB[Publishers, post-trade,<br/>audit writers]
    end
    subgraph DR["DR site (100+ km, warm)"]
        LD[[log replica, async]]
        MED["Matcher S cold standby"]
    end
    GW1 -->|"orders"| SQ1
    GW2 -->|"orders"| SQ1
    SQ1 -->|"replicate, ack on 2 of 3"| L1
    SQ1 -->|"replicate"| L2
    SQ1 -->|"replicate"| L3
    L1 -->|"tail"| ME1
    L2 -->|"tail"| ME2
    L3 -.->|"async ship, RPO seconds"| LD
    LD -.-> MED

    class GW1,GW2 client
    class SQ1,SQ2,ME1,ME2,RK,PUB,MED service
    class L1,L2,L3,LD queue

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
```

## D10. Scaling / partitioning

Shard by symbol. Cold symbols share a shard; the hottest symbol gets a shard, a core, and a machine of its own. Risk is sharded on a different key (account), which is why the hold pattern exists.

```mermaid
%% D10: partitioning. Symbol to shard is a table, not a hash, so a hot symbol can be moved. The hot symbol's single matcher thread is the ceiling.
flowchart LR
    T[(Symbol to shard table<br/>versioned, pushed to gateways)]
    T --> S1["Shard 1: ~2,000 cold symbols<br/>5 k msg/s"]
    T --> S2["Shard 2: ~500 mid symbols<br/>50 k msg/s"]
    T --> S3["Shard 3: XYZ alone<br/>~25 k msg/s avg, 250 k/s at open"]
    T --> S4["Shard 4..N"]
    S3 --> M3[Matcher thread<br/>~1 to 5 M msg/s ceiling<br/>headroom 4x to 20x at open]
    subgraph Fix["When XYZ outgrows one core"]
        F1[Batch inputs per loop iteration]
        F2[Move output publish off the thread]
        F3[Kernel bypass NIC, huge pages]
        F4[Last resort: split by price band<br/>or list on a second venue, none are clean]
    end
    M3 -.-> Fix
    R[(Account to risk shard table)] --> RK1[Risk shard 1..M]

    class T,R store
    class S1,S2,S4,RK1 service
    class S3,M3 critical
    class F1,F2,F3,F4 decision

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

## D11. Failure mode map

```mermaid
%% D11: what fails, who feels it, what bounds it. The log is the only component whose loss is unrecoverable, so it is the one built to never lose a byte.
flowchart TD
    GW[Gateway dies] -->|"blast: its sessions"| GW1[Clients reconnect to another gateway,<br/>resend from last seq, dedup table rebuilt from output log]
    RK[Risk shard dies] -->|"blast: its accounts cannot place new orders"| RK1[Standby replays risk WAL, holds intact,<br/>failover 1 to 2 s, resting orders unaffected]
    SQ[Sequencer leader dies] -->|"blast: one symbol group, ~300 ms"| SQ1[Election, new epoch, unacked tail retried<br/>by gateways with same ClOrdID]
    ME[Matcher primary dies] -->|"blast: one shard, ~1 s"| ME1[Hot standby already at same seq,<br/>promoted with new epoch, republishes from last committed out seq]
    LOG[Log loses quorum] -->|"blast: symbol group halts"| LOG1[Halt trading on that group, never guess.<br/>Third replica in other hall makes this a two-hall failure]
    PUB[Publisher dies] -->|"blast: latency on reports / market data"| PUB1[Stateless, restart, resume from cursor.<br/>Clients see a gap, resend or re-snapshot]
    PT[Post-trade / ledger down] -->|"blast: balances stale, holds not released"| PT1[Trading continues from the log.<br/>Replay catches up, holds are conservative]
    DC[Whole primary DC lost] -->|"blast: market halted"| DC1[DR replays async log, RPO seconds, RTO 15 to 60 min,<br/>members re-enter orders, exchange declares a state]

    class GW,RK,SQ,ME,PUB,PT,DC service
    class LOG critical
    class GW1,RK1,SQ1,ME1,LOG1,PUB1,PT1,DC1 decision

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

## D12. Rollout / migration

From a database-backed matcher (orders in Postgres, matching in transactions) to the log-based design, with a rollback point per phase. Dates are illustrative.

```mermaid
%% D12: migration from a DB-backed matcher. Shadow first, then one cold symbol, then the rest by tier, then retire the DB path.
gantt
    title Migration from DB-backed matching to sequenced log matching
    dateFormat  YYYY-MM-DD
    axisFormat  %b %d
    section Shadow
    Tee all orders to new sequencer and matcher, compare fills offline    :a1, 2026-10-01, 21d
    Rollback point, nothing live on new path                              :milestone, m1, 2026-10-22, 0d
    section Pilot
    Move 50 cold symbols, old path in shadow                              :a2, 2026-10-22, 14d
    Rollback point, flip symbol table back                                :milestone, m2, 2026-11-05, 0d
    section Tiers
    Move mid symbols by tier, one tier per week                           :a3, 2026-11-05, 28d
    Move top 20 symbols, one per day, off-peak cutover                    :a4, 2026-12-03, 20d
    section Retire
    Old matcher read-only, DB becomes a projection of the output log      :a5, 2026-12-23, 14d
    Decommission DB matching path                                         :milestone, m3, 2027-01-06, 0d
```
