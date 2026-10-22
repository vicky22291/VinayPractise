# Diagrams: superhero dispatch

The D1 to D12 set from `hld/CLAUDE.md` §4. Diagrams already in [`solution.md`](solution.md) are listed with a pointer, not pasted twice. Every diagram below adds a zoom-in or a path that `solution.md` does not draw. Numbers match `solution.md`. Durations that are new here are marked [estimate] in the caption.

| # | Diagram | Where |
|---|---|---|
| D1 | Context | below |
| D2 | Data flow | below |
| D3 | Component architecture | Zoom-out: `solution.md` §6 (Postgres primary in red). Zoom-ins below: [D3a dispatch core](#d3a-dispatch-core-zoom-in), [D3b hero connectivity](#d3b-hero-connectivity-zoom-in) |
| D4 | Happy path per FR | Already in `solution.md`: FR1 report §4.1, FR2 offers §4.2, FR3 two-hero race §4.3, FR4 window expiry §4.4, FR5 stale override §4.5. Below: [D4a](#d4a-fr1-report-with-a-retried-request) to [D4e](#d4e-fr5-dispatcher-cancels-an-assigned-incident) |
| D5 | Failure paths | Primary failover during an accept: §10.4 A. Below: [D5a](#d5a-accept-commits-the-response-is-lost-the-hero-retries) to [D5d](#d5d-the-cdc-slot-stalls) |
| D6 | Decision flow | Below: [D6a worker step function](#d6a-dispatch-worker-step-function), [D6b accept transaction](#d6b-accept-transaction-guards) |
| D7 | Entity relationship | System-of-record schema: §3.3. Below: [D7a retention and partitions](#d7a-retention-partitions-and-lifetimes), [D7b Redis keys](#d7b-redis-keys) |
| D8 | State machines | Incident lifecycle: §4.4. Below: [D8a offer](#d8a-offer-lifecycle), [D8b hero duty status](#d8b-hero-duty-status), [D8c assignment](#d8c-assignment-and-the-fencing-token) |
| D9 | Deployment / topology | below |
| D10 | Scaling / partitioning | below |
| D11 | Failure mode map | below, D11a and D11b |
| D12 | Rollout / migration | below |

---

## D1. Context (zoom-out)

The dispatch platform as one box. Three kinds of people use it. Two outside systems carry its messages. One outside system takes what it cannot handle.

```mermaid
%% D1: the system as one box. Blue = people and their apps. Grey dashed = systems outside our trust boundary.
flowchart LR
    CIV[Civilians<br/>~1 M registered] -->|"report incident, ~8/s peak<br/>status updates back"| SYS[Superhero dispatch platform<br/>API, workers, Postgres, Redis GEO,<br/>gateway, projection]
    HERO[Heroes<br/>~10k on duty] -->|"pings 670 to 2,000/s<br/>accept, decline, status"| SYS
    SYS -->|"offer cards ~42/s, taken notices"| HERO
    DISP[Dispatchers<br/>~200 on shift] -->|"cancel, reassign, assign by hand"| SYS
    SYS -->|"live zone view, escalations"| DISP
    SYS -->|"wake-up push, short TTL"| PUSH[APNs and FCM]
    PUSH -.->|"best effort, no receipt"| HERO
    SYS -->|"hand-off of unserved incidents"| E911[City 911 and CAD]
    SYS -->|"events, SLA reports"| WH[Analytics warehouse]

    class CIV,HERO,DISP client
    class SYS service
    class PUSH,E911 external
    class WH store

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

---

## D2. Data flow (DFD)

Inputs to outputs with format, size and peak rate. Two streams never touch: the location stream (big, losable) and the incident stream (small, must not lose).

```mermaid
%% D2: data flow. Location on top, incidents below. Every edge says what, how big, how often.
flowchart LR
    HAPP([Hero app]) -->|"ping, binary over WS, ~120 B, 2,000/s"| LOC([Location service])
    LOC -->|"GEOADD + ZADD last_seen, 2,000/s"| GEO[(Redis GEO, ~1 MB)]
    LOC -->|"checkpoint batch, ~170 rows/s"| PG[(Postgres)]
    CAPP([Civilian app]) -->|"report JSON, ~1 KB, 8.3/s"| API([Dispatch API])
    API -->|"txn, ~36 row writes per incident"| PG
    GEO -->|"50 candidates, ~25 searches/s"| DW([Dispatch workers])
    PG -->|"due tasks, ~100 steps/s"| DW
    DW -->|"offer card ~500 B, ~42/s"| HAPP
    HAPP -->|"accept or status, ~300 B, ~20/s"| API
    PG -->|"WAL change events, ~500 B, ~125/s"| K[(Kafka incident_events)]
    K -->|"zone deltas, ~2,500 msgs/s fan-out"| CON([Dispatcher console])
    K -->|"status push, ~33/s"| CAPP
    K -->|"all events, ~62 KB/s"| WH[(Warehouse)]

    class HAPP,CAPP,CON client
    class LOC,API,DW service
    class PG,WH store
    class GEO cache
    class K queue

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef cache    fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
```

---

## D3. Component architecture

The zoom-out is the final design in [`solution.md` §6](solution.md#6-final-design-and-the-core-flows). It is not repeated here. The two zoom-ins below show what sits inside the boxes.

### D3a. Dispatch core zoom-in

Everything that can change an incident's state goes through one function. Red = the primary, the single place all of it commits.

```mermaid
%% D3a: inside the Dispatch API and workers. Three callers, one transition function, one lock order, one primary.
flowchart TD
    HACC[Hero accept, status] -->|"offer_id or assignment_id"| TR[transition function<br/>lock incident, then offers, then hero]
    DCMD[Dispatcher command] -->|"expected_version"| TR
    WSTEP[Worker step<br/>claimed task, attempt n] -->|"expire, next wave, escalate, reassign"| TR
    REP[Report handler] -->|"report_id"| INS[Insert incident + event + task]
    TR -->|"guarded UPDATEs, event row, task due_at"| PG[(Postgres primary)]
    INS -->|"one txn"| PG
    PG -->|"unique violation on one_active_*"| GUARD{Constraint<br/>refused?}
    GUARD -->|"yes: rollback, 409, count it"| HACC
    SWP[Invariant sweeper<br/>every 10 s] -->|"5 index scans"| PG
    SWP -->|"repair task row or page"| TR
    PG -->|"sync WAL, ANY 1 of 2"| SB[(Standbys in AZ b and c)]

    class HACC,DCMD client
    class TR,WSTEP,REP,INS,SWP service
    class PG critical
    class SB store
    class GUARD decision

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

### D3b. Hero connectivity zoom-in

How an offer finds a hero. The socket is the primary path. Push only wakes the app so it can open a socket and pull.

```mermaid
%% D3b: hero connectivity. A losable routing hash maps hero to gateway node. Grey = push providers, best effort.
flowchart LR
    DW[Dispatch worker] -->|"lookup hero_id"| RT[(Redis hash<br/>hero_id to node, losable)]
    DW -->|"offer card via node RPC"| GW1[Gateway node 1]
    DW -.->|"no socket found"| PUSH[APNs and FCM<br/>high priority, TTL 15 s]
    GW1 -->|"WS frame, ack within 3 s"| APP[Hero app]
    APP -->|"delivered ack"| GW1
    GW1 -->|"delivered_at"| API[Dispatch API]
    PUSH -.->|"wake-up"| APP
    APP -->|"reconnect, jittered backoff"| GW2[Gateway node 2]
    APP -->|"GET /hero/me/offers, pull missed"| API
    GW2 -->|"register hero_id to node 2"| RT
    GW1 -->|"pings"| LOC[Location service]

    class APP,GW1,GW2 client
    class DW,API,LOC service
    class RT cache
    class PUSH external

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef cache    fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

---

## D4. Happy paths, one per FR

`solution.md` §4 already draws one sequence per FR. These five are the companion paths: each FR with the detail §4 leaves out.

### D4a. FR1: report with a retried request

The civilian's phone drops the first response. The retry with the same `report_id` returns the same incident. No second incident, no second dispatch.

```mermaid
%% D4a: report idempotency. The unique report_id turns a retry into a read.
sequenceDiagram
    autonumber
    participant C as Civilian app
    participant A as Dispatch API
    participant P as Postgres
    C->>A: POST /incidents report_id r1, P2 fire
    A->>P: txn INSERT incident i1, event v1, task due now
    P-->>A: commit
    A--xC: 201 lost, phone switches cell tower
    Note over C: no answer after 5 s, retry with backoff
    C->>A: POST /incidents report_id r1 again
    A->>P: INSERT, unique violation on report_once
    A->>P: SELECT incident WHERE report_id r1
    P-->>A: i1, state DISPATCHING, version 2
    A-->>C: 200 i1, DISPATCHING
    Note over C,P: one incident, one task, one dispatch loop
```

### D4b. FR2: wave with one undelivered offer

A P2 wave of 3. Two cards are acked in ~300 ms. The third is not, so its slot moves to the 4th candidate at 3 s instead of waiting 15 s.

```mermaid
%% D4b: the delivery check. The task row's due_at is the only timer.
sequenceDiagram
    autonumber
    participant W as Dispatch worker
    participant P as Postgres
    participant G as Hero gateway
    participant H1 as Hero 1
    participant H3 as Hero 3
    participant H4 as Hero 4
    W->>P: txn offers o1 o2 o3, task due in 3 s
    W->>G: send o1 o2 o3
    G->>H1: o1 delivered, ack at 250 ms
    G-->>H3: o3 sent, phone in a basement, no ack
    Note over W,P: t = 3 s, task due
    W->>P: claim task, o3 has no delivered_at
    W->>P: txn lock incident, o3 WITHDRAWN, INSERT o4, task due in 3 s
    W->>G: send o4
    G->>H4: o4 delivered, ack at 200 ms
    Note over W,P: window end set to sent_at + 15 s for o1 o2 o4
```

### D4c. FR3: the winner's accept and the losers' notices

The guaranteed notice path is the task row, woken in the accept transaction. The fast path is a best-effort send from the API right after commit.

```mermaid
%% D4c: how losers learn. Fast path from the API, guaranteed path from the task.
sequenceDiagram
    autonumber
    participant A as Hero A
    participant API as Dispatch API
    participant P as Postgres
    participant W as Dispatch worker
    participant G as Hero gateway
    participant B as Hero B
    A->>API: accept o1
    API->>P: txn lock i1, ASSIGNED, o1 ACCEPTED, o2 o3 WITHDRAWN, task due now
    P-->>API: commit
    API-->>A: 200 assignment a1, exact address
    API-)G: best effort taken notice o2 o3
    G--xB: dropped, socket reconnecting
    W->>P: claim task, WITHDRAWN offers with no notice_sent_at
    W->>G: taken notice o2 o3
    G->>B: taken, ack
    W->>P: set notice_sent_at, task due at next heartbeat check in 15 s
```

### D4d. FR4: from assigned to resolved

Every hero status update carries the assignment id. The task row turns into a heartbeat checker while the hero is assigned.

```mermaid
%% D4d: lifecycle after the accept. Fenced status updates and a heartbeat check every 15 s.
sequenceDiagram
    autonumber
    participant H as Hero A app
    participant API as Dispatch API
    participant P as Postgres
    participant W as Dispatch worker
    H->>API: status EN_ROUTE, a1, seq 1
    API->>P: transition, a1 is the active assignment, version 4
    loop every 15 s while assigned
        W->>P: claim task, last_heartbeat_at of hero A within 30 s, reschedule
    end
    H->>API: status ON_SCENE, a1, seq 2
    API->>P: transition, version 5
    H->>API: status RESOLVED, a1, seq 3
    API->>P: txn version 6 RESOLVED, assignment ended, hero AVAILABLE, DELETE task
    P-->>API: commit
    API-->>H: 200, back on duty
```

### D4e. FR5: dispatcher cancels an assigned incident

The cancel goes through the same `transition()`. The hero is released in the same transaction and hears about it through the task path.

```mermaid
%% D4e: a dispatcher override that wins. Same function, same lock, same notices path.
sequenceDiagram
    autonumber
    participant D as Dispatcher console
    participant API as Dispatch API
    participant P as Postgres
    participant W as Dispatch worker
    participant H as Hero A
    participant PR as Projection
    D->>API: cancel i9, reason duplicate, expected_version 5
    API->>P: lock i9, version is 5, ASSIGNED to A
    API->>P: CANCELLED version 6, a1 inactive, hero A AVAILABLE, task due now
    P-->>API: commit
    API-->>D: 200 version 6
    W->>P: claim task, notify the released hero, then DELETE task
    W->>H: released notice, incident cancelled
    P-)PR: event i9 v6 via CDC and Kafka
    PR-)D: delta i9 CANCELLED for every console watching the zone
```

---

## D5. Failure paths

The primary failover during an accept is in [`solution.md` §10.4 A](solution.md#104-failure-timeline). Four more below.

### D5a. Accept commits, the response is lost, the hero retries

The accept is idempotent per `offer_id`. No key store. The offer row is the record.

```mermaid
%% D5a: lost response after commit. The retry reads the committed state and returns the same answer.
sequenceDiagram
    autonumber
    participant H as Hero A app
    participant API as Dispatch API
    participant P as Postgres
    H->>API: accept o1
    API->>P: txn, ASSIGNED, o1 ACCEPTED, assignment a1
    P-->>API: commit
    API--xH: 200 lost, network timeout at 2 s
    Note over H: app shows Confirming and retries after 1 s
    H->>API: accept o1 again
    API->>P: lock i1, state ASSIGNED, 0 rows
    API->>P: read o1, ACCEPTED by hero A, active assignment a1
    P-->>API: o1 is this hero's accepted offer
    API-->>H: 200 assignment a1, same as the first time
    Note over H,P: a different hero sending accept for o1 gets 403, the token is bound to the hero
```

### D5b. Redis GEO primary lost, fallback to the 60 s checkpoint

The location index is losable by design. For ~15 s, candidates come from Postgres's 60 s checkpoint with a wider radius.

```mermaid
%% D5b: Redis failover. Dispatch keeps going on stale but durable locations. Times are [estimate].
sequenceDiagram
    autonumber
    participant W as Dispatch worker
    participant R as Redis GEO
    participant RR as Redis replica
    participant P as Postgres
    participant L as Location service
    Note over R: t = 0, Redis primary dies
    W->>R: GEOSEARCH, connection refused
    W->>P: fallback, heroes by last_location checkpoint, radius plus 1 km, last_seen within 90 s
    P-->>W: 18 candidates, up to 60 s stale
    W->>P: availability filter and offers as usual
    Note over RR: t = 10 s, replica promoted, missing about 1 s of pings
    L->>RR: GEOADD resumes on new primary
    Note over L,RR: t = 15 s, every hero has pinged again, index complete
    W->>RR: GEOSEARCH back to normal path
```

### D5c. Dispatcher cancel races a hero accept

Both writers lock the incident row first. Whoever gets the lock decides. The other gets a clear `409`.

```mermaid
%% D5c: two humans, one row. The accept wins here because it got the lock 20 ms earlier.
sequenceDiagram
    autonumber
    participant H as Hero A
    participant D as Dispatcher
    participant API as Dispatch API
    participant P as Postgres
    H->>API: accept o1
    D->>API: cancel i4, expected_version 3
    API->>P: txn H, lock i4 at version 3, DISPATCHING to ASSIGNED
    API->>P: txn D, lock i4, waits
    P-->>API: txn H commit, version 4
    API->>P: txn D wakes, version is 4, expected 3
    P-->>API: txn D rollback
    API-->>H: 200 assignment a1
    API-->>D: 409, now ASSIGNED to hero A, version 4
    Note over D: dispatcher re-sends cancel with expected_version 4 if still wanted, hero A is then released
```

### D5d. The CDC slot stalls

The read side may never hurt the write side. A dead Debezium connector pins WAL on the primary until the cap drops the slot.

```mermaid
%% D5d: stuck replication slot. The cap protects the primary's disk. Consoles fall back to replica polling.
sequenceDiagram
    autonumber
    participant P as Postgres primary
    participant C as Debezium
    participant PR as Projection
    participant D as Dispatcher console
    participant RP as Read replica
    Note over C: t = 0, connector stuck on a poison change
    P->>P: slot retains WAL, about 8 GB per hour at peak [estimate]
    Note over P: t = 2.5 h, retained WAL passes 20 GB, page DB on-call
    PR-->>D: banner, live view delayed
    D->>RP: console polls open incidents every 2 s
    Note over P: t = 6 h if nobody acts, max_slot_wal_keep_size 50 GB reached, slot invalidated
    P->>P: WAL recycled, primary disk safe, dispatch never paused
    C->>P: fixed connector re-creates slot, takes a fresh snapshot
    C->>PR: snapshot then stream, consoles back on push
```

---

## D6. Decision flows

### D6a. Dispatch worker step function

One claimed task, one step. The branch is the incident's state. Every exit sets the next `due_at` or deletes the task, inside the same transaction as the state change.

```mermaid
%% D6a: what a worker does with one claimed task. Pink = decisions, blue = handed to a human.
flowchart TD
    CL[Claim due task<br/>SKIP LOCKED, lease 10 s, attempt n] --> ST{Incident state?}
    ST -->|"REPORTED"| W1[GEOSEARCH 2 km, filter in Postgres<br/>offer wave 1, due in 3 s]
    ST -->|"DISPATCHING"| DC{Undelivered offers<br/>older than 3 s?}
    DC -->|"yes"| RP[Withdraw, offer next candidate<br/>due in 3 s]
    DC -->|"no"| WE{Window ended<br/>with no accept?}
    WE -->|"no"| NT[Send pending notices<br/>due at window end]
    WE -->|"yes"| NW{Waves left for<br/>this severity?}
    NW -->|"yes"| W2[Expire wave, radius 5 or 10 km<br/>next wave, due in 3 s]
    NW -->|"no"| ESC[ESCALATED<br/>due at dispatcher SLA 30 s]
    ST -->|"ASSIGNED, EN_ROUTE, ON_SCENE"| HB{Hero last_heartbeat_at<br/>in Postgres?}
    HB -->|"under 30 s"| OK[Due in 15 s]
    HB -->|"30 s to timeout"| AR[Flag AT_RISK, alert console<br/>due in 15 s]
    HB -->|"past 60 s P1 or 120 s"| RA[End assignment, DISPATCHING<br/>due now, exclude hero]
    ST -->|"terminal"| DEL[Send final notices<br/>DELETE task]

    class CL,W1,RP,NT,W2,OK,AR,RA,DEL service
    class ST,DC,WE,NW,HB decision
    class ESC client

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

`ESCALATED` is blue because it hands the incident to a human on the dispatcher console. It is not red: nothing in this flow is the first thing to break. From `ON_SCENE`, the reassign branch only recommends. A dispatcher confirms (`solution.md` §5.4). Every write ends with `UPDATE dispatch_task ... WHERE attempt = n`, so a fenced worker rolls back.

### D6b. Accept transaction guards

The order of checks inside the accept, and the response each failure maps to.

```mermaid
%% D6b: accept guards in lock order. Any 0-row step rolls back the whole transaction.
flowchart TD
    REQ[accept offer_id, token hero_id] --> OWN{offer.hero_id<br/>equals token?}
    OWN -->|"no"| R403[403 not your offer]
    OWN -->|"yes"| INC{Lock incident<br/>state DISPATCHING?}
    INC -->|"no, ASSIGNED to me via this offer"| R200[200 same assignment<br/>idempotent retry]
    INC -->|"no, taken or cancelled"| R409T[409 taken or cancelled]
    INC -->|"yes"| OFF{Offer still<br/>PENDING?}
    OFF -->|"no, EXPIRED or WITHDRAWN"| R409E[409 expired, rollback]
    OFF -->|"yes"| HER{Hero AVAILABLE<br/>and unique index ok?}
    HER -->|"no"| R409B[409 busy, rollback]
    HER -->|"yes"| COM[Withdraw others, task due now<br/>event row, COMMIT]
    COM --> OK[200 assignment, exact address]

    class REQ client
    class OWN,INC,OFF,HER decision
    class COM,OK,R200 service
    class R403,R409T,R409E,R409B external

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

The ownership check is a read before the lock. It touches no shared row, so it does not break the incident-first lock order.

---

## D7. Entity relationship

The system-of-record schema with PKs, FKs and unique indexes is in [`solution.md` §3.3](solution.md#33-data-model). The two diagrams below add what the ERD leaves out: how long each thing lives, and the losable keys in Redis.

### D7a. Retention, partitions and lifetimes

```mermaid
%% D7a: lifetimes. Hot rows in Postgres, cold months detached to object storage, tasks deleted at terminal state.
flowchart LR
    TASK[dispatch_task<br/>lives while incident is open<br/>a few thousand rows] -->|"DELETE at terminal state"| GONE[Removed in the same txn]
    INC[(incident, incident_event<br/>monthly range partitions<br/>90 days hot, ~130 GB)] -->|"detach month 4"| OBJ[(Object storage, Parquet<br/>7 years, ~3.6 TB)]
    OFF[(offer, assignment<br/>monthly partitions, 90 days hot)] -->|"detach month 4"| OBJ
    INC -->|"CDC, every event"| K[[Kafka, 7 day retention]]
    K -->|"load"| WH[(Warehouse<br/>SLA reports, audits)]
    HERO[(hero, civilian<br/>no partitions, small)] -->|"GDPR delete or pseudonymize"| PII[Civilian PII removed<br/>incident record kept]
    LOCCP[(hero.last_location<br/>overwritten every 60 s)] -->|"location history"| LH[(30 days, then dropped)]

    class TASK,GONE,PII service
    class INC,OFF,OBJ,WH,HERO,LOCCP,LH store
    class K queue

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
```

### D7b. Redis keys

Everything in Redis can be lost and rebuilt within one ping interval (15 s). Nothing in Redis is read at commit time.

```mermaid
%% D7b: the Redis key space. Amber = losable. The dashed edge is the only time Postgres stands in for Redis.
flowchart LR
    PING[Hero ping<br/>hero_id, lat, lng, heading, speed] -->|"GEOADD"| G[(heroes:geo<br/>sorted set, 52-bit geohash score<br/>~10k members, ~1 MB)]
    PING -->|"ZADD score = ping time"| LS[(heroes:last_seen<br/>sorted set)]
    SWEEP[60 s sweep] -->|"ZRANGEBYSCORE older than 60 s"| LS
    SWEEP -->|"ZREM from both"| G
    CONN[Socket connect] -->|"HSET hero_id node"| RT[(hero:route<br/>hash, hero_id to gateway node)]
    DW[Dispatch worker] -->|"GEOSEARCH 2 km COUNT 50 ASC"| G
    DW -->|"drop if older than 45 s"| LS
    DW -->|"node lookup for the offer"| RT
    DW -.->|"Redis down: checkpoint query"| PG[(Postgres hero.last_location)]

    class PING,CONN client
    class SWEEP,DW service
    class G,LS,RT cache
    class PG store

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef cache    fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#111
```

`maxmemory-policy noeviction`: eviction would silently remove heroes and look like "nobody nearby".

---

## D8. State machines

The incident lifecycle is in [`solution.md` §4.4](solution.md#44-lifecycle-a-validated-state-machine-with-one-clock). The three below are the other entities with a lifecycle.

### D8a. Offer lifecycle

Every arrow out of `PENDING` is a transition that first locks the incident row, so accept, expiry and withdrawal cannot both happen.

```mermaid
%% D8a: offer states. Expiry is a worker transition, not a clock comparison.
stateDiagram-v2
    [*] --> PENDING: wave committed, card sent
    PENDING --> ACCEPTED: hero accept wins the incident lock
    PENDING --> DECLINED: hero declines
    PENDING --> EXPIRED: worker at window end, 15 s
    PENDING --> WITHDRAWN: another hero won, or incident cancelled
    PENDING --> WITHDRAWN: no delivery ack in 3 s, slot moved
    ACCEPTED --> [*]
    DECLINED --> [*]
    EXPIRED --> [*]
    WITHDRAWN --> [*]
```

`one_pending_offer_per_hero` means a hero is in `PENDING` for at most one incident at a time.

### D8b. Hero duty status

`BUSY` holds exactly when the hero has an active assignment. `UNREACHABLE` keeps a hero who went silent out of new waves until they ping again.

```mermaid
%% D8b: hero duty status in Postgres. AT_RISK is a flag on the assignment, not a hero state.
stateDiagram-v2
    [*] --> OFF_DUTY
    OFF_DUTY --> AVAILABLE: goes on duty, first ping
    AVAILABLE --> BUSY: accept commits, or dispatcher assigns
    BUSY --> AVAILABLE: incident resolved or cancelled
    BUSY --> AVAILABLE: hero drops the incident
    BUSY --> UNREACHABLE: silent past reassign timeout
    AVAILABLE --> UNREACHABLE: silent 45 s while on duty
    UNREACHABLE --> AVAILABLE: ping received
    AVAILABLE --> OFF_DUTY: goes off duty
    UNREACHABLE --> OFF_DUTY: silent 30 min, auto off duty
```

### D8c. Assignment and the fencing token

The assignment id is checked on every hero status update. Once inactive, it can never become active again, so a released hero's late updates are refused forever.

```mermaid
%% D8c: assignment lifecycle. One active per incident and one active per hero, by partial unique index.
stateDiagram-v2
    [*] --> ACTIVE: accept or manual assign, unique index checked
    ACTIVE --> ACTIVE: AT_RISK flag set or cleared
    ACTIVE --> ENDED_RESOLVED: incident resolved
    ACTIVE --> ENDED_DROPPED: hero sends DROP
    ACTIVE --> ENDED_LOST_CONTACT: silent past 60 s P1 or 120 s
    ACTIVE --> ENDED_REASSIGNED: dispatcher reassigns
    ACTIVE --> ENDED_CANCELLED: incident cancelled
    ENDED_RESOLVED --> [*]
    ENDED_DROPPED --> [*]
    ENDED_LOST_CONTACT --> [*]
    ENDED_REASSIGNED --> [*]
    ENDED_CANCELLED --> [*]
```

---

## D9. Deployment / topology

One region, three AZs. The primary is red: the one box whose loss pauses writes (~30 s [estimate]). Only the async DR stream crosses the region boundary.

```mermaid
%% D9: deployment. Sync replication inside the region, async to DR. Stateless tiers in every AZ.
flowchart LR
    subgraph AZA[AZ a]
        PGP[(Postgres primary)]
        SA[API, workers, gateway<br/>1/3 of pods]
        RDP[(Redis GEO primary)]
    end
    subgraph AZB[AZ b]
        PGB[(Standby b, sync)]
        SB[API, workers, gateway<br/>1/3 of pods]
        RDR[(Redis replica)]
    end
    subgraph AZC[AZ c]
        PGC[(Standby c, sync)]
        SC[API, workers, gateway<br/>1/3 of pods]
        KF[[Kafka, 3 brokers<br/>one per AZ]]
    end
    subgraph DR[DR region]
        PGD[(Async replica<br/>RPO under 5 s)]
    end
    SA -->|"writes"| PGP
    SB -->|"writes, cross-AZ ~1 ms"| PGP
    SC -->|"writes, cross-AZ ~1 ms"| PGP
    PGP -->|"WAL, ANY 1 of b, c"| PGB
    PGP -->|"WAL, ANY 1 of b, c"| PGC
    PGP -.->|"async WAL, cross-region"| PGD
    RDP -->|"async replication"| RDR
    PGP -->|"logical slot via Debezium"| KF

    class PGP critical
    class PGB,PGC,PGD store
    class SA,SB,SC service
    class RDP,RDR cache
    class KF queue

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef cache    fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
```

---

## D10. Scaling / partitioning

**There is no sharding today.** One Postgres primary at ~100 commits/s and one Redis node at ~2% of a core are far from any limit (`solution.md` §10.3). The partitioning that matters is people: under a surge one zone runs out of heroes. The future shard key is `city_id`, one independent cell per city. Kafka is the only component that is partitioned now, by `incident_id`, so each incident's events stay in order.

```mermaid
%% D10: today one cell per city with no shards inside. Red = the hot zone's hero supply, the first thing that runs out. Fix: clustering, priority, reserves, batch matching.
flowchart LR
    RT[Edge router<br/>city from incident location] -->|"city A"| CA[Cell: city A<br/>own Postgres, Redis, workers]
    RT -->|"city B, future"| CB[Cell: city B]
    CA -->|"incidents by zone, h3_r6"| Z1[Zone 1<br/>~200 heroes, normal]
    CA -->|"50x surge"| ZH[Zone 7<br/>~200 heroes vs ~400 incidents in 10 min]
    ZH -->|"radius grows, keep 20% reserve"| Z1
    CA -->|"surge mode"| BM[2 s batch matcher<br/>per hot zone]
    BM -->|"assignment plan"| ZH
    CA -->|"events keyed by incident_id"| KP[[Kafka, 12 partitions<br/>~10 events/s each]]

    class RT client
    class CA,CB,BM service
    class Z1 store
    class ZH critical
    class KP queue

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
```

Why `city_id` and not H3 cells inside a city: an incident and its candidate heroes almost always share a city, so the accept stays single-shard. Sharding by cell inside a city would put heroes near a cell border in two shards and make the accept a cross-shard transaction.

---

## D11. Failure mode map

### D11a. Write path and state

```mermaid
%% D11a: component, then what fails, then blast radius, then mitigation. Red = the primary.
flowchart TD
    PG[Postgres primary] -->|"dies"| PG1[All writes paused ~30 s]
    PG1 -->|"mitigation"| PG2[Sync standby promoted, client retries<br/>no clock-based expiry, RPO 0]
    PG -->|"lock pile-up"| PG3[Slow accepts]
    PG3 -->|"mitigation"| PG4[lock_timeout 2 s, idle txn timeout 5 s<br/>no dashboard reads on primary]
    DW[Dispatch workers] -->|"all down"| DW1[No offers, timers stop]
    DW1 -->|"mitigation"| DW2[Overdue task alert at 30 s<br/>dispatchers assign by hand]
    DW -->|"one dies mid-step"| DW3[One incident paused up to 10 s]
    DW3 -->|"mitigation"| DW4[Lease expiry, attempt fencing<br/>resend by offer_id]
    BUG[transition code] -->|"bad deploy"| BUG1[Wrong or stuck states]
    BUG1 -->|"mitigation"| BUG2[Unique indexes still hold<br/>sweeper every 10 s, zone canary]

    class PG critical
    class DW,BUG service
    class PG1,DW1,DW3,BUG1 decision
    class PG2,PG4,DW2,DW4,BUG2 store

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

Pink here marks the blast radius, purple the mitigation.

### D11b. Read path, delivery and people

```mermaid
%% D11b: the losable and external parts. None of these can cause a double assignment. Red = hero supply, the first thing a surge exhausts.
flowchart TD
    RD[Redis GEO] -->|"primary lost"| RD1[No candidate search ~15 s]
    RD1 -->|"mitigation"| RD2[Replica promote, 60 s checkpoint<br/>radius plus 1 km]
    GW[Hero gateway node] -->|"lost"| GW1[1/3 of sockets drop]
    GW1 -->|"mitigation"| GW2[Reconnect to another node<br/>pull missed offers]
    PU[APNs and FCM] -->|"slow or down"| PU1[Socketless heroes miss offers]
    PU1 -->|"mitigation"| PU2[3 s delivery ack, slot moves on<br/>rank socket heroes higher]
    CDC[CDC and Kafka] -->|"stalled"| CDC1[Consoles stale, slot pins WAL]
    CDC1 -->|"mitigation"| CDC2[Replica polling, 50 GB WAL cap]
    SUP[Local hero supply] -->|"50x surge"| SUP1[Incidents wait, escalations pile up]
    SUP1 -->|"mitigation"| SUP2[Clustering, P1 first, smaller waves<br/>batch matching, zone reserves]

    class RD cache
    class GW client
    class PU external
    class CDC queue
    class SUP critical
    class RD1,GW1,PU1,CDC1,SUP1 decision
    class RD2,GW2,PU2,CDC2,SUP2 store

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef cache    fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

---

## D12. Rollout / migration

From a human dispatch center (phones, radios, a basic CAD) to automated offers, one severity at a time. Each phase has a rollback point: a per-severity, per-zone switch back to "assisted". The manual path never goes away. Durations are [estimate].

```mermaid
%% D12: migration phases. Milestones are the go or no-go gates, each one a rollback point.
gantt
    title Human dispatch to automated offers
    dateFormat YYYY-MM-DD
    axisFormat %b %d
    section Build
    Schema, transition, workers, sweeper     :b1, 2027-01-04, 42d
    Hero app offer flow, gateway             :b2, 2027-01-04, 42d
    section Shadow
    Shadow, compute offers, send nothing     :s1, after b1, 28d
    Gate top-3 match rate and latency        :milestone, m1, after s1, 0d
    section Assisted
    Console recommends, dispatcher clicks    :a1, after m1, 28d
    Gate rollback point 1                    :milestone, m2, after a1, 0d
    section Auto
    Auto offers for P3, zone by zone         :p3, after m2, 21d
    Gate rollback point 2                    :milestone, m3, after p3, 0d
    Auto offers for P2                       :p2, after m3, 28d
    Gate 0 drops, 0 double assignments 30d   :milestone, m4, after p2, 0d
    Auto offers for P1                       :p1, after m4, 28d
    Gate rollback point 4                    :milestone, m5, after p1, 0d
    section Steady state
    Dispatchers own the escalation queue     :st, after m5, 30d
```

Gates: shadow needs the human's chosen hero in our top 3 for at least 80% of incidents [estimate] and time to first offer p99 under 2 s. Each auto phase needs a month with zero sweeper violations and zero refused double assignments in the phase before. Rollback at any gate is the per-severity setting back to "assisted", with no data to backfill, because every incident is in Postgres either way.
