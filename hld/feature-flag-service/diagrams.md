# Diagrams: feature flag service

The D1 to D12 set from `hld/CLAUDE.md` §4. Diagrams already in [`solution.md`](solution.md) are listed with a pointer, not pasted twice. Every diagram below adds a zoom-in or a path that `solution.md` does not draw. Numbers match `solution.md`. Timeouts and durations that are new here are marked [estimate] in the caption.

| # | Diagram | Where |
|---|---|---|
| D1 | Context | below |
| D2 | Data flow | below |
| D3 | Component architecture | Zoom-out: `solution.md` §6 (publisher in red). Zoom-ins below: D3a control plane, D3b one host |
| D4 | Happy path per FR | Already in `solution.md`: FR1 edit with a conflict §4.2, FR2 one check §4.1, FR3 one edit propagating §4.3. FR1 approval path: D3a and D8a. Below: D4a FR2 one request with a reload mid-request, D4b FR3 kill and the propagation view, D4c FR4 audit and revert |
| D5 | Failure paths | Kill during publisher failover: §10.4. Below: D5a host back from a partition, D5b boot during a control-plane outage, D5c break-glass kill |
| D6 | Decision flow | Agent validation chain: §5.4. Below: D6a SDK evaluation order, D6b agent poll loop, prefix rule and kill overlay |
| D7 | Entity relationship | Control-plane schema: §3.3. Below: published files, host reports, governance |
| D8 | State machines | Guarded ramp and flag lifecycle: §5.7. Below: D8a change request, D8b host freshness |
| D9 | Deployment / topology | below |
| D10 | Scaling / partitioning | below |
| D11 | Failure mode map | below, D11a and D11b |
| D12 | Rollout / migration | Kill timing budget: §5.3. Below: migration of existing flags |

---

## D1. Context (zoom-out)

The flag service as one box. People write about 3,000 times a day. The fleet reads about 20 M times a second, but only from its own memory.

```mermaid
%% D1: the system as one box. Writers on the left, the fleet that reads on the right. Grey = systems we depend on but do not own.
flowchart LR
    ENG[Engineers<br/>console, CLI, scripts] -->|"create, edit, kill, revert, approve<br/>~3,000 edits/day"| FFS[Feature flag service<br/>admin API, Flag DB, publisher,<br/>files, host agents, SDKs]
    SRE[On-call SRE pair] -->|"break-glass kill, signed<br/>state OFF only, up to 100 flags"| FFS
    IDP[Identity provider<br/>SSO, team groups] -->|"who may edit which flag"| FFS
    FFS -->|"files to every host: pointer and override<br/>polls ~4,000 req/s, mostly 304 or 404"| FLEET[Service fleet<br/>~1,000 services, ~50,000 processes]
    FLEET -->|"watermarks, eval counts"| FFS
    USR[Merchants and their customers] -->|"~1 M requests/s peak,<br/>~20 checks each, all in process"| FLEET
    FLEET -->|"request metrics tagged on, next or off,<br/>edge logs with merchant ids"| MET[Metrics and edge logs]
    MET -->|"errors per slice, cohorts<br/>recomputed from merchant ids"| FFS
    FFS -->|"latest snapshot per deploy"| CI[Deploy pipeline]
    CI -->|"deploy artifact with a<br/>deploy-time bootstrap snapshot"| FLEET
    FFS -->|"pages, stale-flag tickets"| PAGE[Paging and ticketing]

    class ENG,SRE,USR,FLEET client
    class FFS service
    class IDP,MET,CI,PAGE external

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

No arrow from the fleet back to the flag service carries a check. The only reads are file polls, off the request path.

## D2. Data flow (DFD)

What moves where, with format, size and rate. The steady state is tiny: one ~1 KB delta per edit to every host. A full 8 MB snapshot moves only when a host boots without a disk copy, falls behind the previous snapshot, or rejects a file and finds a newer snapshot, or into a deploy.

```mermaid
%% D2: data flow with sizes and rates. Rounded boxes are processes, cylinders are stores. The metrics store is the company's, shown because watermarks, tagged request metrics and edge logs live there.
flowchart LR
    ENG(Console, CLI, scripts) -->|"PATCH JSON ~1 KB<br/>0.035/s avg, up to ~12/s"| API(Flag admin API)
    API -->|"one txn: FLAG_VERSION ~1 KB<br/>+ CHANGE_LOG row, ~70 ms"| DB[(Flag DB<br/>~1.1 GB/year)]
    DB -->|"CHANGE_LOG rows after last seq<br/>read every 200 ms"| PUB(Publisher)
    PUB -->|"create-only signed delta ~1 KB per edit, ~1 MB per batch<br/>snap 8 MB per 1,000 changes or 1 h, pointer as_of every 60 s"| OBJ[(Object storage<br/>3 regions, deltas kept 7 days)]
    OBJ -->|"cache miss, coalesced<br/>1 origin GET per object"| CDN(Regional HTTP cache)
    CDN -->|"pointer ~100 B with recent_kills + override<br/>~4,000 req/s fleet, mostly 304 or 404<br/>delta 1 KB x 10k hosts = 10 MB per edit"| AG(Host agent x10k)
    AG -->|"snapshot.seq 8 MB<br/>tmp, fsync, rename"| DISK[(Local disk<br/>current + previous)]
    DISK -->|"parse on new generation<br/>segments by mmap"| SDK(SDK in ~50k processes)
    SDK -->|"loaded seq on each swap<br/>eval counts ~10 KB/host/min"| AG
    AG -->|"watermark = min loaded seq, up to 1 per 5 s<br/>eval counts ~1.7 MB/s fleet"| WM[(Metrics store<br/>watermarks, eval, request metrics)]
    SDK -->|"request metrics tagged on, next or off<br/>guarded flags only, up to 50"| WM
    WM -->|"errors per slice from edge logs<br/>looked at every 10 s"| GRD(Guard monitor)
    GRD -->|"rollout to 0 bp and page, rare"| API
    OBJ -->|"snap 8 MB per deploy"| CI(Deploy pipeline)
    CI -->|"bootstrap snapshot<br/>inside the deploy artifact"| SDK

    class ENG client
    class API,PUB,AG,SDK,GRD service
    class DB,OBJ,DISK,WM store
    class CDN cache
    class CI external

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef cache    fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

The biggest single transfer in steady state is a ~1 MB delta, from a 1,000-change batch or a 40k-id segment edit: `10,000 x 1 MB = 10 GB` across 3 regions in one 5 s poll window, ~0.7 GB/s per region (`solution.md` §2, §5.5).

## D3. Component architecture

The zoom-out is the final design in `solution.md` §6, with the publisher in red. Two zoom-ins follow.

### D3a. Control plane zoom-in

Inside the admin API and the Flag DB. Every path ends in one transaction that writes a version and a change-log row together, so the change log is also the outbox.

```mermaid
%% D3a: the write path. Red = the seq counter row: every commit takes the next seq from one row, so commits serialize at about one quorum round trip each (~70 ms). That caps single edits at ~12 to 15 a second, the first limit hit if edit volume grows (solution §3.3, §7).
flowchart LR
    ENG[Engineers<br/>console, CLI] -->|"PATCH or revert with If-Match, kill"| AUTH[AuthN and RBAC<br/>owner team or delegate]
    SCR[Scripts] -->|"batch, up to 1,000 changes"| AUTH
    GRD[Guard monitor] -->|"rollout to 0 bp, or pause<br/>if kill_safe = false"| AUTH
    AUTH -->|"allowed"| VAL[Validator<br/>limits at ~80%, no id on both lists,<br/>segment exists, 200 flags/h per person]
    VAL -->|"valid edit"| RISK{Exposure grows on high risk,<br/>over 200 flags, or a kill of<br/>a kill_safe = false flag?}
    RISK -->|"yes, 202"| CR[(CHANGE_REQUEST<br/>pending, base version)]
    CR -->|"second engineer approves"| TXN[Edit transaction<br/>If-Match, insert version, bump head,<br/>sign the version, admin key]
    RISK -->|"no: kills, decreases,<br/>no exposure change"| TXN
    TXN -.->|"409 at apply: back to pending"| CR
    TXN -->|"next seq, or n seqs for a batch"| CTR[(seq counter row<br/>one row, every commit)]
    TXN -->|"insert v13, head = 13"| FV[(FLAG and FLAG_VERSION<br/>kept forever)]
    TXN -->|"insert seq row, same commit"| CL[(CHANGE_LOG<br/>dense seq, the outbox)]
    CL -->|"tail seq after last, 200 ms"| PUB[Publisher]
    ENG -->|"propagation view for a seq"| PV[Propagation view<br/>reads watermarks]

    class ENG,SCR client
    class GRD,AUTH,VAL,TXN,PUB,PV service
    class RISK decision
    class CR,FV,CL store
    class CTR critical

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

"Exposure grows" means any edit, revert or unkill that raises the share of units that get `true`: a rollout increase, `OFF -> ON`, `allow_add`, a new allow segment, `block_remove`, a reshuffle, or a segment member edit that widens exposure. The guard's rollback to 0 bp is a decrease, so it needs no approval. A kill carries an `Idempotency-Key`: a retry returns the same version, but every distinct kill writes a new one. Real load is 0.035 edits/s, about 340x below the cap. A kill queued behind a batch waits one commit, under a second.

### D3b. One host zoom-in

One agent keeps a file current. About five service processes read it. The check path on the right has no I/O and no locks.

```mermaid
%% D3b: one host. No red: nothing here is shared beyond one host. A stuck agent freezes one host at its seq; checks keep working.
flowchart LR
    CDN[Regional HTTP cache]
    DISK[(Local disk<br/>snapshot.current, .previous,<br/>segments, generation header)]
    WMS[(Metrics store)]
    subgraph AGENT[Host agent, 1 per host]
        POLL[Poller and fetcher<br/>pointer, override, kill overlay,<br/>prefix rule] -->|"new delta or snap"| VAL{Validate: checksum, both signatures,<br/>order, size, schema, touched<br/>and count, per flag}
        VAL -->|"pass, applied to a copy"| WR[Writer<br/>tmp, fsync, rename,<br/>bump generation]
        WR -->|"applied seq"| REP[Reporter<br/>min loaded seq, eval counts]
        VAL -->|"fail: keep last-known-good,<br/>report reject"| REP
    end
    subgraph PROC[Service process, about 5 per host]
        WATCH[Watcher thread<br/>inotify or 100 ms header poll,<br/>reloads only a higher seq] -->|"parse with the segment<br/>manifest, then swap"| PTR[Atomic snapshot pointer<br/>RCU]
        H[Handler<br/>~20 checks per request] -->|"is_enabled"| REQ[Request context<br/>pinned snapshot, bucket memo]
        REQ -->|"one atomic load at first check"| PTR
        REQ -->|"probe, ~0.1 us"| SEG[Segments<br/>mmapped, one copy per host]
    end
    CDN -->|"pointer and override every 5 s, deltas"| POLL
    WR -->|"new files"| DISK
    REP -->|"up to 1 per 5 s"| WMS
    DISK -->|"new generation"| WATCH
    DISK -->|"mmap, OS page cache"| SEG
    REQ -.->|"eval counts"| REP
    WATCH -.->|"loaded seq on each swap"| REP

    class CDN cache
    class POLL,WR,REP,WATCH,REQ,H service
    class VAL decision
    class DISK,WMS store
    class PTR,SEG cache

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef cache    fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

Agents verify two signatures: the admin API's on each flag version, and the publisher's on each file. The old in-memory snapshot is freed when the last request pinned to it finishes; pins expire after ~10 s. Segments are read-only files with a static open-addressing index, one copy per host in the page cache. Each snapshot's manifest names the segment versions to load with it.

## D4. Happy paths, one per FR

### D4a. FR2: one request, three checks, a reload mid-request

```mermaid
%% D4a (FR2): one request makes three checks while a reload lands. The request stays pinned to the snapshot it started with, so it sees one version. Nothing leaves the process.
sequenceDiagram
    autonumber
    participant H as Handler
    participant C as Request context
    participant S as SDK
    participant W as Watcher thread
    participant P as Snapshot pointer
    participant G as Segment, mmapped
    H->>S: is_enabled new_checkout, merchant acct_123, default false
    S->>P: atomic load, generation 41, seq 884212
    S->>C: pin generation 41, expires after about 10 s
    S->>S: v12 ON, rollout 1000 bp, not blocked, not allowed, bucket 1374
    S->>C: memo new_checkout and acct_123 to bucket 1374
    S-->>H: false, NOT_IN_ROLLOUT, v12
    W->>P: swap to generation 42, seq 884213, new_checkout v13 at 2000 bp
    H->>S: is_enabled new_checkout again, from a helper
    S->>C: pinned generation 41, memo hit, no hash
    S-->>H: false, NOT_IN_ROLLOUT, v12, same answer as step 6
    H->>S: is_enabled instant_payouts, merchant acct_123
    S->>G: probe the slot for the 64-bit hash, compare the full id
    G-->>S: found in block segment risky_merchants
    S-->>H: false, BLOCKED
    Note over H,S: next request pins generation 42, gets true, IN_ROLLOUT, v13
```

Each check is ~0.3 us. The memo means a flag checked five times in one request hashes once.

### D4b. FR3: a kill, from click to "how far did it get"

```mermaid
%% D4b (FR3): a kill from click to the propagation view. Typical times, not worst case. The kill rides in the pointer's recent_kills too, so an agent applies it at once even when big deltas are queued ahead of it. The watermark is the lowest seq any process on the host has loaded.
sequenceDiagram
    autonumber
    participant E as On-call
    participant API as Flag admin API
    participant DB as Flag DB
    participant P as Publisher
    participant C as Storage and cache
    participant G as Host agent
    participant WM as Watermarks
    E->>API: POST kill refund_v2, Idempotency-Key k-77, reason, t = 0
    API->>DB: txn: v9 = v8 with state OFF, signed, seq 884300
    API-->>E: 200 v9, seq 884300, propagation view opens
    P->>DB: tail seq after 884299, t = 0.2 s
    P->>P: build delta/884300, base 884299, validate, sign
    P->>C: per region, create-only delta, then pointer with recent_kills, epoch, If-Match, t = 0.7 s
    G->>C: GET pointer If-None-Match, t = 2.9 s
    C-->>G: 200 seq 884300, recent_kills refund_v2 at 884300
    G->>G: OFF overlay at once
    G->>C: GET delta/884300, 1 KB
    G->>G: delta ok, write, drop overlay
    Note over C,G: processes swap in about 0.1 s and report seq 884300
    G->>WM: host-0412, min loaded 884300, at 3.1 s
    E->>API: GET propagation for seq 884300
    API->>WM: live hosts at or above 884300, laggards
    WM-->>API: ~60% at 4 s, 99.2% of live hosts at 10 s, 30 laggards
    API-->>E: laggard list, each with its last report age
```

The SLO counts **live** hosts: those whose agent reported in the last 30 s. A laggard is a host still below the seq 30 s after publish, classed as dead (no report for 30 s), rejecting, or slow region. Simulated: p50 3.4 s, p99 6.5 s on a healthy fleet. Behind 10 batches the overlay keeps a kill at p99 7.3 to 7.4 s, against 32 s without it.

### D4c. FR4: audit and revert

```mermaid
%% D4c (FR4): read the history, revert by writing a new version with If-Match, and answer which version was live on one host at one time, from watermarks plus versions. The salt is on each version, so the answer includes the exact cohort.
sequenceDiagram
    autonumber
    participant E as Engineer
    participant API as Flag admin API
    participant DB as Flag DB
    participant WM as Watermarks
    E->>API: GET versions of new_checkout
    API->>DB: FLAG_VERSION by flag_key, newest first
    DB-->>API: v13 ramp to 20% by alice at 14:02, seq 884213, then v12, v11
    API-->>E: diffs with author, reason, approver, seq, time
    E->>API: POST revert to_version 11, If-Match v13, reason errors after v13
    API->>DB: txn: head is v13, v14 = copy of v11 with its salt, seq 884310
    API-->>E: 200 v14, seq 884310
    Note over E,API: a kill that landed first would make If-Match v13 fail with 409, never a silent unkill
    E->>API: which version was live on host h-88 at 14:05
    API->>WM: highest seq h-88 had loaded by 14:05
    WM-->>API: seq 884213, loaded 14:02:04
    API->>DB: new_checkout version with the highest seq at or below 884213
    DB-->>API: v13, 2,000 bp, salt of v13
    API-->>E: v13 was live on h-88 at 14:05, cohort recomputable from its salt
```

## D5. Failure paths

### D5a. A host comes back from a 2 h partition

It served its old copy the whole time. A lagging cache node serves an old pointer, and one delta arrives corrupt. The 2 s timeout is an [estimate].

```mermaid
%% D5a: stale pointer ignored, behind the previous snapshot so the snapshot first, then deltas one at a time in order, one corrupt file re-fetched once from origin. The host is at one exact seq at every moment.
sequenceDiagram
    autonumber
    participant G as Host agent
    participant C as Regional cache
    participant O as Object storage origin
    participant WM as Watermarks
    Note over G,WM: local seq 884100, 2 h old. Stale alarm fired, checks never stopped
    G->>C: GET pointer, timeout 2 s
    C-->>G: seq 884090, from a lagging cache node
    G->>G: below local, ignore it
    G->>C: next poll, about 5 s later
    C-->>G: seq 884350, snap_seq 884300, prev_snap_seq 884200
    G->>G: local is below prev_snap_seq, snapshot first
    G->>C: GET snap/884300, same region as the pointer
    C-->>G: 8 MB, newest step of the header chain ok
    G->>C: GET delta/884301, then each next file by last_seq
    C-->>G: files ok until delta/884320 fails its checksum
    G->>O: re-fetch delta/884320 once, bypassing the cache
    O-->>G: checksum ok
    G->>G: apply in order, write 884350
    G->>WM: min loaded seq 884350, caught up
```

If the origin copy also fails, the delta counts as bad: load `snap/{snap_seq}` if it is newer than local, otherwise keep last-known-good (D6b). Deltas are kept 7 days.

### D5b. A new host boots during a control-plane outage, with its region's cache down too

The Flag DB and publisher have been down since 10:00, so the pointer's `as_of` stopped at 09:59. Region A's cache is down. Region B's object storage and cache still serve files. Timeouts are [estimate].

```mermaid
%% D5b: boot order under failure. The agent polls at once and falls back to another region's cache. A payment service opted into readiness refuses traffic until its snapshot was confirmed current within 24 h, measured from the pointer's signed as_of.
sequenceDiagram
    autonumber
    participant LB as Readiness probe
    participant S as Payment service SDK
    participant G as Host agent
    participant CA as Cache region A
    participant CB as Cache region B
    Note over G,CA: new host, empty disk, control plane down since 10:00
    G->>CA: GET pointer at once, timeout 2 s
    CA--xG: timeout
    G->>CA: retry at 1 s, timeout again
    G->>CB: GET pointer from region B
    CB-->>G: seq 884290, snap_seq 884000, as_of 09:59
    S->>S: no agent file, direct mode waits on region A, load the last deploy's bootstrap, 3 days old
    LB->>S: ready check
    S-->>LB: not ready, as_of older than 24 h, payment opt-in
    G->>CB: GET snap/884000, then the deltas one at a time
    CB-->>G: 8 MB plus about 290 KB
    G->>G: validate, write snapshot.884290, fsync, rename, generation 1
    S->>S: load the agent file, as_of 09:59, 41 min old, swap
    LB->>S: ready check
    S-->>LB: ready
    Note over LB,G: without the opt-in it serves on the bootstrap. No bootstrap means code defaults, NO_SNAPSHOT
```

Every fallback can predate a kill. A 3-day-old bootstrap can show a killed flag as ON, which is why payment paths wait and why a booting agent polls at once.

### D5c. Break-glass kill while the Flag DB is down

```mermaid
%% D5c: the kill path that does not need the control plane. The override is its own object, signed with a separate SRE key, and may only set state OFF. It is never deleted: a signed retire_at_seq tells each agent to drop it once its local seq reaches the real kill.
sequenceDiagram
    autonumber
    participant O1 as On-call 1
    participant O2 as On-call 2
    participant T as Break-glass tool
    participant API as Flag admin API
    participant OBJ as Object storage, 3 regions
    participant G as Host agents
    O1->>T: override refund_v2 to state OFF, reason incident 4411
    O2->>T: second approval
    T->>T: state OFF only, up to 100 flags, never kill_safe = false, expires_at, next counter, SRE key
    T->>OBJ: PUT /v1/override in all 3 regions
    G->>OBJ: conditional GET of /v1/override on every poll, through the cache
    OBJ-->>G: override naming 1 flag
    G->>G: verify SRE key, apply OFF over 884290
    Note over G,OBJ: 99% of hosts within about 8 s. A live override pages until retired
    Note over O1,API: later, the control plane is back
    O1->>API: POST kill refund_v2, reason replaces override
    API-->>O1: 200, seq 884291
    O1->>T: retire the override at seq 884291
    T->>OBJ: PUT override with signed retire_at_seq 884291
    G->>G: drop override once local seq is 884291
```

The override has its own conditional GET on every poll: about +2,000 req/s fleet-wide, ~4,000 with the pointer, nearly all `404` or `304`. Deleting it instead would turn the feature back on for any host that has not yet applied seq 884291.

## D6. Decision flows

The agent's per-file validation chain is in `solution.md` §5.4. Below are the two other branching components.

### D6a. SDK evaluation order

```mermaid
%% D6a: the evaluation order, identical in every SDK language. Three exits: the code default, false, or true. Each edge names the reason returned. The kill is read before the rest of the record, so a host that cannot parse a flag's rules still honours its kill. OFF beats allow, block beats allow, and no unit id never falls to a random bucket.
flowchart TD
    IN[is_enabled key, ctx, default] -->|"pinned snapshot"| S0{Snapshot<br/>loaded?}
    S0 -->|"no: NO_SNAPSHOT"| DEF[Return the code default]
    S0 -->|"yes"| S1{Flag present and<br/>not archived?}
    S1 -->|"no: FLAG_NOT_FOUND"| DEF
    S1 -->|"yes"| S2{state OFF?<br/>tiny fixed schema, read first}
    S2 -->|"yes: OFF"| F[Return false]
    S2 -->|"no"| S3{Rest of the record<br/>parsed on this host?}
    S3 -->|"no: ERROR"| DEF
    S3 -->|"yes"| S4{Unit id present, a non-empty<br/>string, valid Unicode?}
    S4 -->|"no"| S4B{rollout_bp<br/>is 10,000?}
    S4B -->|"yes: NO_UNIT"| T[Return true]
    S4B -->|"no: NO_UNIT"| F
    S4 -->|"yes"| S5{On block list<br/>or block segment?}
    S5 -->|"yes: BLOCKED"| F
    S5 -->|"no"| S6{On allow list<br/>or allow segment?}
    S6 -->|"yes: ALLOWED"| T
    S6 -->|"no"| B["bucket = SHA-256 of salt_hex:unit,<br/>first 8 bytes as unsigned 64-bit, mod 10,000"]
    B -->|"memoized per request"| S7{bucket below<br/>rollout_bp?}
    S7 -->|"yes: IN_ROLLOUT"| T
    S7 -->|"no: NOT_IN_ROLLOUT"| F

    class IN,B service
    class S0,S1,S2,S3,S4,S4B,S5,S6,S7 decision
    class DEF,F,T client

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

- The salt is 16 random bytes written as 32 lowercase hex characters, so the hash input for an `acct_` id is ~54 bytes, one SHA-256 block.
- The cross-language trap is the 8 bytes read as a **signed** integer (Java `%` or `floorMod`, JavaScript `parseInt`). Every SDK must read them unsigned. The golden file catches it.
- `2^64 mod 10,000 = 1,616`, so the low 1,616 buckets get one extra preimage in 1.8 x 10^19.

### D6b. Agent poll loop, prefix rule and kill overlay

```mermaid
%% D6b: one agent tick. Kills in the pointer apply at once as an OFF-only overlay. The prefix then advances one exact seq at a time: a gap or a failed file falls back to a newer snapshot, never to a torn mix. "Validation chain" is the flow in solution §5.4.
flowchart TD
    T[Timer, every 5 s<br/>jitter 20%] -->|"tick"| P[GET pointer and override,<br/>pointer.canary if in canary range]
    P -->|"poll fails: retry at 1, 2, 4 s"| T
    P -->|"response"| Q{304, or seq at<br/>or below local?}
    Q -->|"yes: nothing new, or a stale cache"| T
    Q -->|"no"| O[Apply recent_kills above local<br/>as an OFF-only overlay,<br/>new generation at once]
    O -->|"then the prefix"| N{Behind the previous<br/>snapshot?}
    N -->|"yes"| S[GET snap at snap_seq]
    N -->|"no"| D[GET delta/local+1, then each<br/>next by last_seq, same region]
    S -->|"file"| V{Fits the prefix, checksum ok,<br/>validation chain passes?}
    D -->|"files"| V
    V -->|"checksum fails: once from origin"| D
    V -->|"gap, or fails"| X{snap_seq newer than<br/>local, not tried yet?}
    X -->|"yes"| S
    X -->|"no"| K[Keep last-known-good,<br/>report reject, alert]
    K -->|"retry next tick"| T
    V -->|"ok"| A[Apply in order<br/>local = last_seq]
    A -->|"check"| M{local below<br/>pointer seq?}
    M -->|"yes"| D
    M -->|"no"| W[Write tmp, fsync, rename, fsync dir,<br/>bump generation, drop overlay<br/>entries at or below local]
    W -->|"processes report loaded seq"| R[Report watermark,<br/>min loaded seq, up to 1 per 5 s]
    R -->|"wait"| T

    class T,P,O,D,S,A,R service
    class Q,N,V,X decision
    class M decision
    class K,W store

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

The overlay can only turn flags off, so it never exposes a unit. It also reaches a host stuck behind a rejected file. A reject report triggers an on-demand snapshot at the publisher.

## D7. Entity relationship

The control-plane schema (FLAG, FLAG_VERSION, SEGMENT, SEGMENT_CHANGE, CHANGE_LOG, CHANGE_REQUEST) is in `solution.md` §3.3. Below: what the publisher writes, what hosts report, and governance. FLAG and FLAG_VERSION appear only with the attributes §3.3 does not list.

```mermaid
%% D7: files are immutable, create-only and keyed by seq, with the schema version in the path. Only POINTER and the override are rewritten. Watermarks and eval counts live in the metrics store, partitioned by host and by flag.
erDiagram
    CHANGE_LOG }|--|| DELTA_FILE : "one commit, one file"
    SNAPSHOT_FILE ||--o{ DELTA_FILE : "deltas after it"
    POINTER }o--|| SNAPSHOT_FILE : "names snap_seq"
    POINTER }o--|| DELTA_FILE : "names head seq"
    SNAPSHOT_FILE }o--o{ SEGMENT_FILE : "manifest names"
    FLAG ||--o{ FLAG_VERSION : "signed versions"
    DELTA_FILE }o--o{ FLAG_VERSION : "carries records"
    FLAG ||--o{ EVAL_COUNT : "evaluated as"
    FLAG ||--o{ RAMP_SCHEDULE : "ramped by"
    FLAG }o--o| OVERRIDE_FILE : "break-glass kill"
    POINTER {
        string region PK "one per region"
        string channel PK "main or canary"
        bigint seq "head, only moves forward"
        bigint snap_seq
        int epoch "publisher lease, fences writes"
        timestamp as_of "signed, rewritten every 60 s"
        string recent_kills "kills of the last 10 min, up to 100"
    }
    DELTA_FILE {
        bigint first_seq PK "path v8/delta/first_seq"
        bigint base_seq "first_seq minus 1"
        bigint last_seq "larger than first_seq for a batch"
        bool bulk "set only by an approved batch"
        string signature "publisher key"
        int ttl_days "7"
    }
    SNAPSHOT_FILE {
        bigint seq PK "every 1,000 changes or 1 h"
        bigint prev_snap_seq "header chain"
        int prev_flag_count "count check across snapshots"
        string segment_manifest "segment versions at this seq"
        int size_bytes "8 MB today, cap 32 MB"
    }
    SEGMENT_FILE {
        string name PK
        bigint seq PK
        int id_count "cap 1 M"
        int size_bytes "about 42 MB file at 1 M ids"
        bool prefetched "switch only at 99% of live hosts"
    }
    OVERRIDE_FILE {
        string path PK "v1/override"
        string flags "state OFF only, up to 100"
        bigint counter "monotonic, no replay"
        timestamp expires_at
        bigint retire_at_seq "never deleted"
        string signature "SRE key"
    }
    HOST_WATERMARK {
        string host PK "partition key"
        bigint seq "min loaded across processes"
        timestamp applied_at
        string agent_version
    }
    EVAL_COUNT {
        string flag_key PK "partition key"
        string host PK
        timestamp minute PK
        string reason
        int sdk_level "gates min_sdk_level"
        int count "feeds stale and ERROR alerts"
    }
    RAMP_SCHEDULE {
        string flag_key PK
        int step PK "1, 5, 25, 50, 100 percent"
        int bake_min "30"
        int min_requests "about 1,500 on the new slice"
        string status "waiting, baking, held, done"
        string on_regression "0 bp and page, pause if not kill_safe"
    }
    FLAG {
        string flag_key PK
        string bucket_algo "v1, or legacy_v1 for imports"
        bool propagate "pass the decision downstream"
        bool kill_safe "default true"
        string async_mode "behaviour-only or format-carrying"
    }
    FLAG_VERSION {
        string flag_key PK
        int version PK
        int min_sdk_level "older SDKs return ERROR"
        string version_sig "admin API key"
    }
```

Access patterns: agents read `POINTER` by region every 5 s, then `DELTA_FILE` by `first_seq`. The propagation view counts `HOST_WATERMARK` rows at or above a seq. The stale-flag job reads `EVAL_COUNT` by `flag_key` over 30 days, and the publisher reads it by `sdk_level` to gate a flag's `min_sdk_level` at 99.9% of that flag's evaluators over 7 days. The guard monitor reads at most 50 active `RAMP_SCHEDULE` rows. Deltas live 7 days.

## D8. State machines

The guarded ramp and the flag's own lifecycle (full, stale, archived, key reserved forever) are in `solution.md` §5.7. Below: a change request, and one host's freshness.

### D8a. Change request on a high-risk flag

```mermaid
%% D8a: a change request applies with its base version as If-Match. If the head moved first (a kill landed), it goes back for re-approval instead of being applied blind. Approval follows effective exposure, including reverts and unkills.
stateDiagram-v2
    direction LR
    [*] --> Pending: needs an approver
    Pending --> Approved: second engineer
    Pending --> Rejected: approver declines
    Approved --> Applied: If-Match ok
    Approved --> Pending: 409, rebased
    Rejected --> [*]
    Applied --> [*]
```

### D8b. One host's freshness

```mermaid
%% D8b: freshness as the agent and the propagation view see it. Checks keep serving in every state inside Serving, and kills still arrive through the pointer overlay. Only opt-in services fail readiness, and only without a snapshot confirmed current within 24 h.
stateDiagram-v2
    direction LR
    [*] --> Booting
    Booting --> Serving: disk copy valid
    Booting --> Fetching: empty disk
    Fetching --> Serving: snapshot validated
    Fetching --> NoCopy: every cache down
    NoCopy --> Fetching: retry, backoff
    state "Serving a snapshot" as Serving {
        direction TB
        [*] --> Current
        Current --> Behind: pointer ahead
        Behind --> Current: deltas applied
        Behind --> Stale: over 5 min, flagged
        Stale --> Current: caught up
        Behind --> Rejecting: file fails checks
        Rejecting --> Current: newer snapshot
    }
```

In `NoCopy`, processes run on the bootstrap snapshot or, without one, on code defaults (`NO_SNAPSHOT`). A `Stale` host is flagged. More than 1% of live hosts stale pages someone. "Confirmed current" is measured from the pointer's signed `as_of`, so a quiet day never fails readiness.

## D9. Deployment / topology

Three regions. Only Raft replication, the publisher's file writes, and an agent's fallback to another region's cache cross a region boundary.

```mermaid
%% D9: the Flag DB has 3 nodes in each region and replicates by Raft. The publisher runs active in region 1 with a warm standby in region 2 and writes to every region's bucket. Hosts read their own region's cache.
flowchart TB
    DB[(Flag DB: 3 nodes in each region<br/>Raft, 1 replica per region per range)]
    PA[Publisher, active<br/>runs in region 1, holds lease]
    PS[Publisher, warm standby<br/>runs in region 2]
    subgraph R1[Region 1]
        O1[(Bucket)]
        C1[Cache x3]
        H1[~3,300 hosts<br/>1 agent each]
    end
    subgraph R2[Region 2]
        O2[(Bucket)]
        C2[Cache x3]
        H2[~3,300 hosts<br/>1 agent each]
    end
    subgraph R3[Region 3]
        O3[(Bucket)]
        C3[Cache x3]
        H3[~3,300 hosts<br/>1 agent each]
    end
    DB -->|"tail CHANGE_LOG, 200 ms"| PA
    DB -.->|"tail, waits for the lease"| PS
    PA -->|"create-only files, then fenced pointer"| O1
    PA -->|"same, cross-region, independent"| O2
    PA -->|"same, cross-region, independent"| O3
    O1 -->|"miss"| C1
    O2 -->|"miss"| C2
    O3 -->|"miss"| C3
    C1 -->|"poll, deltas"| H1
    C2 -->|"poll, deltas"| H2
    C3 -->|"poll, deltas"| H3

    class DB,O1,O2,O3 store
    class PA,PS service
    class C1,C2,C3 cache
    class H1,H2,H3 client

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef cache    fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#111
```

- Each Raft range has one replica per region, so a commit needs one cross-region round trip (~70 ms) and survives a region loss.
- Each region is published independently, so a slow region never delays a kill elsewhere. The pointer write carries the lease `epoch` and is conditional on the last ETag. The active publisher re-reads each region's pointer every 1 s and rewrites it if it is not its own.
- An agent whose region cache is down polls another region's cache (not drawn, to keep the regions side by side).
- The admin API is stateless and runs next to the Flag DB in every region. Total: 9 DB nodes, 2 publishers, 9 cache boxes (`solution.md` §2).

## D10. Scaling / partitioning

The data plane is replicated, not sharded: every host holds every flag. The Flag DB ranges are keyed by `flag_key`, but every commit also touches the one seq counter row (red in D3a). So the interesting picture is the fan-out tree and its one hot spot.

```mermaid
%% D10: the fan-out tree per region. Red = the regional cache during a cold boot of a whole region with no disk copies, the component closest to a limit in solution §10.3.
flowchart LR
    PUB[Publisher<br/>1 active] -->|"each file once per region"| OBJ[(Object storage<br/>3 regions)]
    OBJ -->|"1 origin GET per object, coalesced"| CA[Regional cache, 3 boxes<br/>~1,100 hosts, ~220 polls/s each]
    CA -->|"1 KB delta per edit"| HOST[~3,300 hosts per region<br/>1 agent each]
    HOST -->|"1 file, about 5 readers"| PROC[Processes<br/>one parse each, segments shared]
    CA -->|"8 MB snap x 3,300 hosts = 26 GB"| BOOT[Cold region boot<br/>no disk copies]
    F1[Fix 1: disk copy<br/>boot is a catch-up] -.->|"removes most downloads"| BOOT
    F2[Fix 2: admission control<br/>100 concurrent, ~30 s at ~1 GB/s] -.->|"caps egress"| CA
    TEN{10x flags: 200k,<br/>80 MB snapshot} -->|"seam"| NS[Per-service namespaces<br/>SDK loads only its prefixes]
    NS -.->|"agent still holds all"| HOST

    class PUB,HOST,PROC,F1,F2,NS service
    class OBJ store
    class CA critical
    class BOOT client
    class TEN decision

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

Steady state per cache box: ~220 pointer polls/s (twice that with the override poll) and ~1,100 delta fetches per edit, ~10x headroom. The largest delta is ~1 MB: a 1,000-change batch or a 40k-id segment edit. Replacing a whole list ships a new segment file (~42 MB at 1 M ids). Agents prefetch it as soon as it is published, and the switch edit is allowed only once 99% of live hosts have it; otherwise the switch would pull ~140 GB per region at once. Kills never wait behind it (overlay). Per process: ~400 checks/s against ~3 M/s per core.

## D11. Failure mode map

Component and failure, then blast radius (on the arrow), then mitigation. Split in two to stay under 15 nodes.

### D11a. Control plane and distribution

```mermaid
%% D11a: red = a bad file from the publisher, the only failure here that reaches every host within seconds. Every other branch costs freshness, not correctness.
flowchart TD
    CP[Control plane and distribution] -->|"fails"| F1[Flag DB loses a region]
    CP -->|"fails"| F2[Flag DB fully down]
    CP -->|"fails"| F3[Publisher dies or pauses]
    CP -->|"fails"| F4[Publisher emits a bad file]
    CP -->|"fails"| F5[One region's bucket or cache down]
    F1 -->|"none: writes on 2 of 3"| M1[Raft quorum, range<br/>leases move in ~10 s]
    F2 -->|"no edits, no API kills"| M2[Fail static, break-glass<br/>override file]
    F3 -->|"kill reaches 99% at p99 17 to 19 s"| M3[Standby takes the 10 s lease,<br/>epoch and If-Match fence the old one]
    F4 -->|"every host in seconds"| M4[Publisher and agent checks, per-flag<br/>isolation, same seq re-rendered as a snapshot]
    F5 -->|"that region stops updating"| M5[Agents use another region's<br/>cache, alarm at 5 min]

    class CP service
    class F1,F2,F3,F5 decision
    class F4 critical
    class M1,M2,M3,M4,M5 service

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

### D11b. Hosts, code and people

```mermaid
%% D11b: no red. Each failure here is bounded to one host, one service or one flag. The human branches are the most likely outages once the data plane is robust (solution §5.7).
flowchart TD
    HP[Hosts, code, people] -->|"fails"| F6[Agent crashes or hangs]
    HP -->|"fails"| F7[SDK below a flag's min_sdk_level]
    HP -->|"fails"| F8[Process boots with no snapshot]
    HP -->|"fails"| F9[Ramp 1% to 100% in one click]
    HP -->|"fails"| F10[Old flag key reused]
    HP -->|"fails"| F11[Script touches 6,000 flags]
    F6 -->|"one host frozen at its seq"| M6[Watchdog restart,<br/>laggard after 30 s]
    F7 -->|"that flag returns ERROR there"| M7[State read first so kills work,<br/>publish at 99.9% of its evaluators]
    F8 -->|"code defaults, NO_SNAPSHOT"| M8[Deploy-time bootstrap, poll at once,<br/>readiness on as_of]
    F9 -->|"users of that flag"| M9[Approver when exposure grows,<br/>guard drops rollout to 0 bp, pages]
    F10 -->|"dead code wakes on old hosts"| M10[Keys reserved forever]
    F11 -->|"30% of flags changed at once"| M11[200 flags/h per person unless bulk<br/>and approved, agents' touched and count checks]

    class HP service
    class F6,F7,F8,F9,F10,F11 decision
    class M6,M7,M8,M9,M10,M11 service

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

## D12. Rollout / migration

From env vars, per-service YAML or a Redis lookup to this service (`solution.md` §8). Each milestone is a rollback point. Durations are [estimate].

```mermaid
%% D12: four phases. Buckets are preserved with legacy_v1 so no merchant is reshuffled. Cut-over is per service, gated on mismatches.
gantt
    title Migration to the flag service
    dateFormat YYYY-MM-DD
    axisFormat %b %d
    section Phase 1 import
    Import flags with an owner and a unit        :p1a, 2026-11-02, 14d
    Unowned flags to a triage queue              :p1b, 2026-11-02, 21d
    Rollback point, nothing reads the new copy   :milestone, m1, after p1a, 0d
    section Phase 2 keep buckets
    legacy_v1 bucketing in every SDK             :p2a, after m1, 21d
    Golden tests for both hash functions         :p2b, after m1, 21d
    Rollback point, previous SDK release         :milestone, m2, after p2a, 0d
    section Phase 3 dual read
    Old system stays write master, importer copies edits :p3w, after m2, 84d
    SDK evaluates both, returns the old answer   :p3a, after m2, 28d
    Cut over per service at under 0.01 percent   :p3b, after p3a, 56d
    Rollback point, per-service source setting   :milestone, m3r, after p3a, 0d
    Writes flip to the new system                :milestone, m3, after p3b, 0d
    section Phase 4 retire
    Old system read-only                         :p4a, after m3, 30d
    Legacy flags drain at 0 or 100 percent       :p4b, after m3, 90d
    Old system deleted                           :milestone, m4, after p4a, 0d
```

A service cuts over after a week under 0.01% mismatches. The importer keeps both systems on the same state, so migrated services see new edits. Rollback stays one per-service setting until the old system is deleted.

A new snapshot schema follows the same idea at a smaller scale: `pointer.canary` to 1%, then 10%, then all hosts, over about an hour, and only after telemetry shows the fleet can read it. The publisher writes two file chains for the same seqs, with the schema version in the path (`v7/delta/...`, `v8/delta/...`). Rollback at any step is dropping `pointer.canary`. Value changes never wait for this.
