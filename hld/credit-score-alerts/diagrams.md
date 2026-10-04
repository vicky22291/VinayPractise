# Diagrams: Credit Karma score-change alerts

> One-line answer: twelve views of one design. Members are hashed into refresh slots, so bureau reports arrive at a flat ~330 a second. Diff workers diff each report against the visible snapshot and write a staged version plus typed change events with exact per-bureau ids. A batch-level quality gate promotes the version or holds alerting and display. An alert decider keeps material, wanted, not-yet-sent changes and puts them in a lane. A delivery scheduler sends P0 (possible fraud, one alert per change) at once and releases P1 (everything else) across the member's local morning by member hash, starting low and ramping on the read path's measured headroom, warming each score card first. The member read path is the one red box.

The D1 to D12 set from `hld/CLAUDE.md` §4, each with a one-line caption. A diagram already in [`solution.md`](solution.md) gets a heading, a caption and a link, never a second copy. Acronyms: KV (key-value store), APNs (Apple Push Notification service), FCM (Firebase Cloud Messaging), KMS (key management service), FCRA (Fair Credit Reporting Act), P0 (the possible-fraud lane: new account, new hard inquiry), P1 (every other alert, released in the local morning), TTL (time to live), RF (replication factor), DNS (Domain Name System), AZ (availability zone), RPO (recovery point objective).

| # | Diagram | Where it lives |
|---|---|---|
| D1 | Context | below |
| D2 | Data flow | below, plus D2b data lifecycle |
| D3 | Component architecture (final design) | [solution §6](solution.md#6-final-design-and-the-six-core-flows) |
| D4 | Happy path per FR | First versions: [solution §4.1 to §4.4](solution.md#4-high-level-design). Final versions: FR1 + FR2 pull to promotion, FR3 P0 trigger to push, FR3 + FR4 morning release and tap: below |
| D5 | Failure paths | Sender crash after APNs 200, gate hold and replay, FCM 429 mid-release: below. Region loss mid-release: [solution §10.4](solution.md#104-failure-timeline) |
| D6 | Decision flow | Score API with `min_version`: [solution §5.5](solution.md#55-the-member-taps-the-push-and-the-app-shows-last-weeks-score-from-a-cache-how-do-you-prevent-that). Alert decider: below. Release controller: [solution §10.1](solution.md#101-internals-of-each-chosen-technology) |
| D7 | Entity relationship | [solution §3.3](solution.md#33-data-model) |
| D8 | State machines | Batch: [solution §5.3](solution.md#53-a-bad-bureau-batch-drops-everyones-score-by-80-points-how-do-you-stop-it-before-the-pushes-go-out). Alert and snapshot version: below |
| D9 | Deployment / topology | below |
| D10 | Scaling / partitioning | below |
| D11 | Failure mode map | below, two trees |
| D12 | Rollout / migration | below |

## D1. Context (zoom-out)

Our system as one box: bureaus feed it, push and email providers carry its alerts, members read from it, on-call decides held batches.

```mermaid
%% D1: the alert system as one box with every external actor and what crosses each edge.
flowchart LR
    BU[TransUnion, Equifax]:::external -->|"reports ~330/s,<br/>triggers ~5/s, files"| SYS[Score-change alerts<br/>refresh, diff, gate,<br/>decide, deliver, read]:::service
    SYS -->|"soft pull with consent ref,<br/>mutual TLS"| BU
    SYS -->|"push with collapse id,<br/>no PII in text"| PUSH[APNs, FCM]:::external
    SYS -->|"email, P0 and opted-in P1"| MAIL[Email provider]:::external
    PUSH -->|"notification"| MEM[Members<br/>app and web]:::client
    MAIL -->|"email"| MEM
    MEM -->|"GET score with min_version,<br/>preferences, device tokens"| SYS
    SYS -->|"gate hold page"| OPS[On-call + bureau<br/>relationship owner]:::client
    OPS -->|"release, quarantine, replay"| SYS
    KMS[KMS]:::external <-->|"wrap and unwrap<br/>per-member keys"| SYS

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

## D2. Data flow (DFD)

Inputs to outputs with format, size and rate on every edge. Two lanes leave the decider: P0 at once, P1 through the scheduler.

```mermaid
%% D2: data flow. Processes are rounded, stores are cylinders. Rates are steady state; file mode in brackets.
flowchart LR
    BU[Bureaus] -->|"report XML or JSON,<br/>~30 KB, 330/s"| ING([Ingest])
    ING -->|"encrypted report, ~10 MB/s"| RAW[(Raw reports<br/>~15 TB, 90 days)]
    ING -->|"pointer ~300 B,<br/>330/s, 20k/s file mode"| KR[[reports]]
    BU -->|"trigger JSON ~1 KB,<br/>~5/s, bursts 50/s"| KT[[triggers]]
    KR -->|"pointer"| DIFF([Diff])
    DIFF -->|"staged version ~8 KB +<br/>score card, diffed vs visible"| KV[(Snapshot KV, 3 versions<br/>~4.8 TB, ~14 TB replicated)]
    DIFF -->|"change event ~200 B,<br/>~500/s"| CE[[change-events]]
    DIFF -->|"Parquet, ~400 GB/week"| LAKE[(History lake)]
    CE -->|"batch stats"| GATE([Quality gate])
    GATE -->|"promote, ~165/s avg"| KV
    CE -->|"events"| DEC([Decider])
    KT -->|"one KV check, then event"| DEC
    DEC -->|"alert ~500 B, ~41/s,<br/>sent-log row"| AS[(Alert store)]
    AS -->|"P0 ~5/s now, own cap ~500/s,<br/>P1 from 1k/s up to R_cap"| SCH([Scheduler +<br/>senders])
    SCH -->|"push ~300 B, email"| PRV[APNs, FCM,<br/>email]

    class BU,PRV external
    class ING,DIFF,GATE,DEC,SCH service
    class RAW,KV,LAKE,AS store
    class KR,KT,CE queue

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

### D2b. Data lifecycle and retention

Where each kind of data lives and when it goes away (solution §5.7). Hot data in the KV, evidence in the lake, raw reports gone at 90 days. Per-member keys crypto-shred the KV, raw reports and backups; the lake is encrypted per file and deletes by rewrite, because per-member encryption inside Parquet would defeat columnar compression.

```mermaid
%% D2b: data lifecycle. Per-member keys where data is per member, per-file keys and delete-by-rewrite in the columnar lake.
flowchart LR
    ING[Ingest] -->|"raw report, encrypted"| RAW[(Raw reports<br/>90-day lifecycle)]
    DW[Diff workers] -->|"latest + score card"| KV[(Snapshot KV<br/>last 3 versions)]
    DW -->|"events, score series,<br/>snapshots"| LAKE[(History lake, Parquet<br/>by bureau and week)]
    LAKE -->|"after 13 weeks,<br/>monthly or nothing"| ARC[(Archive tier)]
    KMS[KMS + per-member<br/>key table] -->|"per-member keys"| KV
    KMS -->|"per-member keys"| RAW
    KMS -->|"per-file keys"| LAKE
    DEL[Member closes account] -->|"delete member key"| KMS
    DEL -->|"row delete, monthly<br/>compaction rewrite"| LAKE

    class ING,DW service
    class KV,RAW,LAKE,ARC store
    class KMS external
    class DEL client

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

## D3. Component architecture

The final design, 14 nodes, red on the member read path: [solution §6](solution.md#6-final-design-and-the-six-core-flows).

## D4. Happy paths, one per FR

The first versions are in [solution §4](solution.md#4-high-level-design), one per FR. These are the final versions, after §5.

### D4 FR1 and FR2 final: a pull becomes a staged version, passes the gate, and is promoted

```mermaid
%% D4 FR1 + FR2 final: the diff always diffs against visible and writes staged. The gate judges the window; the promoter flips visible only for versions this batch wrote.
sequenceDiagram
    autonumber
    participant S as Refresh scheduler
    participant B as TransUnion API
    participant O as Object storage
    participant D as Diff worker
    participant V as Snapshot KV
    participant G as Quality gate
    S->>B: soft pull m_7, task 2026-W41, 02:13:07
    B-->>S: report r_881
    S->>O: put encrypted r_881
    S->>D: pointer via reports, key m_7
    D->>V: read m_7 TU, visible 41, max_version 41, known and trigger items
    D->>D: diff against visible 41, SCORE_CHANGED -24 and two more events
    D->>V: staged 42 from max_version, batch TU-pull-02:00, if pointers unchanged
    D->>G: events and stats for the batch
    Note over S,G: 02:15 window closes, 150k reports
    G->>G: shares vs same source and hour, last 4 weeks, in bounds
    G->>V: visible 42 where staged batch is still this one and 42 above 41
    G-->>D: batch PASSED, held alerts claim the sent-log, PENDING
```

### D4 FR3 P0 final: a trigger becomes a push in about a second

```mermaid
%% D4 FR3 P0 final: own topic, decider and sender pools. One alert per change, a re-entrant claim, and a display-only cross-bureau link through the P0 index.
sequenceDiagram
    autonumber
    participant B as TransUnion
    participant T as Trigger receiver
    participant K as Kafka triggers
    participant D as P0 decider
    participant L as Sent-log and P0 index
    participant S as P0 sender
    participant P as APNs
    B->>T: signed trigger, NEW_HARD_INQUIRY, X Bank
    T->>K: write, acks all
    T-->>B: 200, about 50 ms
    K->>D: trigger for m_7
    D->>D: record key not in known items, add to trigger items, P0
    D->>L: claim exact change_id, owner a_1 = hash of m_7, P0, change_id
    L-->>D: inserted, or exists with owner a_1 after a crash, carry on
    D->>L: P0 index compare-and-set, no linked Equifax item
    D->>S: ALERT a_1 PENDING, via alerts-p0
    S->>S: claim a_1, attempt 1, lease 60 s
    S->>P: push, collapse id a_1, priority 10
    P-->>S: 200, about 0.45 s after the trigger
    S->>S: a_1 SENT where attempt is 1, email sent in parallel
```

### D4 FR3 and FR4 final: the morning release and the tap

Flow 2 of solution §6 as a sequence: warm first, release by budget, read by version.

```mermaid
%% D4 FR3 + FR4 final: the morning release and the tap. Warm first, release by budget, read by version.
sequenceDiagram
    autonumber
    participant S as Delivery scheduler
    participant V as Snapshot KV
    participant C as Page cache
    participant P as APNs
    participant A as Member app
    participant R as Score read API
    Note over S,R: 08:45, minute 08:47 is two minutes away
    S->>S: re-check m_7 preferences, quiet hours, device zone
    S->>V: read m_7 TU, visible version and card
    V-->>S: visible 42, card v42
    S->>C: set card m_7 TU v42, TTL 48 h
    Note over S,R: 08:47, measured load plus load still to come 31%, release
    S->>S: claim a_2, PENDING to SENDING, lease 60 s
    S->>P: push a_2, collapse id a_2, expiration 11:00
    P-->>S: 200
    S->>S: a_2 SENT where attempt is 1
    A->>R: GET score TU, min_version 42
    R->>C: get card m_7 TU v42
    C-->>R: hit
    R-->>A: 688, -24, reasons, ~5 ms
```

## D5. Failure paths

### D5a. Sender crashes after APNs accepts the push

The ambiguous crash from solution §5.4. The lease turns it into a resend, the collapse id turns the resend into a replacement on the phone, and the attempt number fences the final write.

```mermaid
%% D5a: crash after the provider's 200 and before SENT. The member sees one notification.
sequenceDiagram
    autonumber
    participant S1 as Sender 1
    participant A as Alert store
    participant P as APNs
    participant S2 as Sender 2
    actor M as Member phone
    S1->>A: claim a_2, PENDING to SENDING, attempt 1, lease to 08:48:00
    S1->>P: push, apns-collapse-id a_2, 10 s timeout
    P-->>S1: 200
    P->>M: notification a_2 shown
    Note over S1,M: 08:47:00.151, killed before writing SENT
    Note over S1,M: 08:48:00, lease expired, sweeper re-publishes a_2
    S2->>A: claim a_2, attempt 2, lease to 08:49:00
    S2->>P: push, same apns-collapse-id a_2
    P-->>S2: 200
    P->>M: replaces notification a_2 in place
    S2->>A: a_2 SENT where attempt is 2
    Note over S1,M: a sender that was only slow times out at 10 s, inside the lease, and its late SENT for attempt 1 is rejected
    Note over S1,M: email has no collapse id, P0 resends email, P1 does not
```

### D5b. The gate holds a bad batch, on-call quarantines and replays

Flow 4 of solution §6. No member sees the bad score and no alert leaves.

```mermaid
%% D5b: our parser mismatch makes 31% of a window drop 50+ points. Held, paged, quarantined, replayed as a new batch. The pull circuit stays closed because the raw data is good.
sequenceDiagram
    autonumber
    participant D as Diff workers
    participant G as Quality gate
    participant O as On-call
    participant V as Snapshot KV
    participant A as Alert store
    D->>G: batch TU-pull-10:00, 150k reports, staged only
    G->>G: 31% moved 50+, baseline 0.5%, floor 2%
    G->>A: batch HELD, ~46k alerts stay HELD, no sent-log claims
    G->>O: page, delta histogram attached
    Note over D,A: members in the batch still see their previous visible version
    D->>G: batch TU-pull-10:15 also out of bounds
    G->>G: second hold, raw responses validate, pull circuit stays closed
    O->>G: quarantine both batches
    G->>V: void staged versions still owned by these batches, numbers never reused
    G->>A: cancel held alerts, nothing to free
    Note over O,D: 13:00, parser fixed
    O->>D: replay from stored raw reports, bounded rate
    D->>G: new batches, source replay, diffed against visible, PASSED
    G->>A: real alerts join the evening window, paced
```

### D5c. FCM answers 429 in the middle of a release

Another team's campaign shares the FCM project quota. P0 keeps its reserved share; P1 slows and rolls.

```mermaid
%% D5c: FCM quota exhausted mid-release. Backoff, a smaller Android share, P0 untouched, P1 rolls to the evening window.
sequenceDiagram
    autonumber
    participant C as Release controller
    participant S as P1 senders
    participant F as FCM
    participant Z as P0 senders
    S->>F: Android pushes, 3.5k/s
    F-->>S: 429 RESOURCE_EXHAUSTED
    S->>S: back off with jitter, 1 s, 2 s, 4 s
    S->>C: Android success rate under 50%
    C->>C: halve the Android share, iOS unchanged
    Z->>F: P0 push inside its reserved 120k a minute
    F-->>Z: 200
    Note over C,Z: 10:58, 400k Android P1 alerts not sent before the window ends
    C->>C: roll them to the 18:00 to 20:00 window
    Note over C,Z: page only if P0 sees a 429, P1 rollover over 5% is a ticket
```

## D6. Activity / decision flow

The score API's `min_version` logic is [D6a in solution §5.5](solution.md#55-the-member-taps-the-push-and-the-app-shows-last-weeks-score-from-a-cache-how-do-you-prevent-that) and the release control loop is in [solution §10.1](solution.md#101-internals-of-each-chosen-technology). Here is the hardest branching component: the alert decider.

### D6b. The alert decider, one change event

```mermaid
%% D6b: what happens to one change event. Pink diamonds are decisions. P0 claims at once and re-entrantly; P1 claims only when its batch passes and is re-checked at release.
flowchart TD
    E[Change event] --> M{Material and<br/>wanted?}
    M -->|"no"| N[Lake only, maybe digest]
    M -->|"yes"| L{P0 type?<br/>new account, inquiry}
    L -->|"yes"| D{Claim exact change_id:<br/>row free or ours?}
    D -->|"owned by another alert"| R[Drop: reason on the<br/>existing inbox entry]
    D -->|"yes, create alert if absent"| K{P0 index CAS:<br/>same lender at the<br/>other bureau?}
    K -->|"linked"| AO[Inbox: also on the<br/>other bureau, no push]
    K -->|"no match, err to push"| Q{Quiet hours?}
    Q -->|"no"| P0[alerts-p0: push + email,<br/>report-found ones after the batch]
    Q -->|"yes"| P0S[alerts-p0: soundless<br/>push + email]
    L -->|"no"| W[HELD in the member's minute,<br/>no claim until the batch passes]
    W -->|"batch passed, claim, then at release"| C{Prefs, zone and<br/>daily cap still allow?}
    C -->|"no"| IB[Inbox only or next window]
    C -->|"yes"| SND[Coalesced push<br/>for this member]

    class E client
    class M,L,D,K,Q,C decision
    class N,R,AO,P0,P0S,W,IB,SND service

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

## D7. Entity relationship

The `erDiagram` with partition keys and access patterns: [solution §3.3](solution.md#33-data-model).

## D8. State machines

The batch lifecycle is [D8a in solution §5.3](solution.md#53-a-bad-bureau-batch-drops-everyones-score-by-80-points-how-do-you-stop-it-before-the-pushes-go-out).

### D8b. Alert

Every transition is a conditional update on one row. A held alert claims the sent-log only on the way to `Pending`; a newer report for the member supersedes it. `SENDING` returns to itself on a lease expiry with a new attempt, and only the current attempt can write `Sent`.

```mermaid
%% D8b: one alert from creation to a terminal state. Held waits for the gate (only trigger alerts skip it), Pending waits for the scheduler.
stateDiagram-v2
    direction LR
    [*] --> Held: batch not checked yet
    [*] --> Pending: trigger, claimed
    Held --> Pending: passed, claimed
    Held --> Cancelled: batch quarantined
    Held --> Suppressed: superseded
    Pending --> Sending: claimed, lease 60 s
    Sending --> Sending: lease expired, retry
    Sending --> Sent: provider 200
    Pending --> Suppressed: seen or muted
    Pending --> Rolled: window ended
    Rolled --> Pending: next window
    Pending --> Expired: past expires_at
    Sent --> [*]
    Cancelled --> [*]
    Suppressed --> [*]
    Expired --> [*]
```

### D8c. One snapshot version

The lifecycle of one version on a snapshot row (`visible_version`, `staged_version`, `staged_batch_id`, `max_version`). Every diff is against the visible version; numbers come from `max_version` and are never reused; `visible` never moves back.

```mermaid
%% D8c: one version from staged to a terminal state. Only a version its own batch still owns can become visible, and only if it is newer.
stateDiagram-v2
    direction LR
    [*] --> Staged: diffed vs visible
    Staged --> Visible: passed, still owner
    Staged --> Superseded: newer report staged
    Staged --> Voided: quarantined
    Visible --> Replaced: newer visible
    Superseded --> [*]
    Voided --> [*]
    Replaced --> [*]
```

A correction (solution §5.3) is not a transition here: it is a new version, staged from a replay batch with `correction_of`, that replaces the wrong one by moving forward.

## D9. Deployment / topology

Two US regions. Each member has a home region for writes; reads are active-active; each region's read path can carry all traffic alone, which is why the scheduler budgets against one region's 30k.

```mermaid
%% D9: two regions, members split 50/50 by hash. Writes in the home region, async replication across, reads anywhere with the version check.
flowchart TB
    MEM[Members] -->|"app traffic"| DNS[Global DNS and<br/>load balancing]
    BU[Bureaus] -->|"triggers, pull responses"| DNS
    subgraph EAST [Region East, 3 AZs]
        ERP[Read path<br/>sized 30k req/s alone]
        EPIPE[Pipeline for East-home members<br/>ingest, diff, gate, decider,<br/>scheduler shards 0 to 31]
        EKV[(KV + alert store<br/>home for East members)]
        ERED[(Redis page cache)]
    end
    subgraph WEST [Region West, 3 AZs]
        WRP[Read path<br/>sized 30k req/s alone]
        WPIPE[Pipeline for West-home members<br/>scheduler shards 32 to 63]
        WKV[(KV + alert store<br/>home for West members)]
        WRED[(Redis page cache)]
    end
    DNS -->|"app, nearest region"| ERP
    DNS -->|"app, nearest region"| WRP
    DNS -->|"triggers, either region"| EPIPE
    DNS -->|"triggers, either region"| WPIPE
    EPIPE -->|"writes, Kafka RF 3"| EKV
    WPIPE -->|"writes, Kafka RF 3"| WKV
    EKV <-->|"async replication, ~1 s"| WKV
    ERP -->|"cards, then KV on miss"| ERED
    WRP -->|"cards, then KV on miss"| WRED
    EPIPE -->|"pushes"| PRV[APNs, FCM, email]
    WPIPE -->|"pushes"| PRV
    class MEM,DNS client
    class ERP,WRP critical
    class EPIPE,WPIPE service
    class EKV,WKV store
    class ERED,WRED cache
    class BU,PRV external

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef cache    fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

What crosses a region boundary: KV and alert-store replication (asynchronous), the §5.5 fallback read to the home region (rare), a trigger that lands in the non-home region (forwarded once to the home region's `triggers` topic), and shard leases on failover. Object storage is a multi-region bucket.

## D10. Scaling / partitioning

Salted hashes of `member_id` place a member everywhere: its refresh second, its Kafka partition, its KV tablet, its scheduler shard, and its release minute in the morning window. Hashing the member (not the alert) for the release minute keeps a member's two bureau alerts in one minute, so they coalesce into one push. The naive release (everything at 08:00) is the hot bucket; it overloads the red read path.

```mermaid
%% D10: how members and their alerts are spread. The pink box is the naive hot bucket; the red box is what it overloads; spread plus the ramp is the fix.
flowchart LR
    MID[member_id] -->|"hash mod 604,800"| SLOT[Refresh second<br/>~165 members each]
    MID -->|"hash mod 64"| KP[Kafka partition<br/>reports, change-events]
    MID -->|"hash8 prefix"| TAB[KV tablet<br/>row member + bureau]
    MID -->|"hash mod 64"| SH[Scheduler shard<br/>R / 64 each]
    MID -->|"naive: all at 08:00"| HOT{One bucket at 08:00<br/>12.5 M on a bunched day}
    MID -->|"salted hash mod 180"| SPREAD[180 minute buckets<br/>~70k members each,<br/>both bureaus coalesced]
    HOT -->|"~33.5k req/s, 112%"| RP["Member read path<br/>~30k req/s"]
    SPREAD -->|"~1.2k pushes/s,<br/>~7.8k req/s total"| CAP[Ramp from 1k/s,<br/>cap from measured p x k]
    CAP -->|"under 70%"| RP

    class MID client
    class SLOT,KP,TAB,SH,SPREAD,CAP service
    class HOT decision
    class RP critical

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
```

No other key is hot. A refresh second holds ~165 members (±13); a Kafka partition gets ~5 reports/s steady and ~310/s in file mode; a KV tablet split is automatic; a scheduler shard releases at most ~120 pushes/s.

## D11. Failure mode map

Component, what fails, blast radius, mitigation. Two trees so each stays under 15 nodes.

### D11a. Ingest, diff and gate

```mermaid
%% D11a: the pipeline side. Nothing here can hurt a member except a bad batch, and the gate is built for it. No red: the pipeline can catch up.
flowchart TD
    ROOT[Pipeline side] --> B1[Bureau API down or slow]
    ROOT --> B2[Trigger endpoint unreachable]
    ROOT --> B3[Bad batch from a bureau]
    ROOT --> B4[Diff worker dies]
    ROOT --> B5[Bad diff code release]
    ROOT --> B6[KV home region lost]
    ROOT --> B7[Decider dies after<br/>the sent-log claim]
    B1 -->|"one bureau's pulls"| M1[Breaker on raw-level errors,<br/>1% probe, catch-up at +50%]
    B2 -->|"P0 for one bureau"| M2[Bureau retries,<br/>endpoint in both regions]
    B3 -->|"every member in it"| M3["Gate holds visibility and alerts,<br/>human release, replay"]
    B4 -->|"its partitions, ~30 s"| M4[Rebalance, compare-and-set,<br/>deterministic ids]
    B5 -->|"every member"| M5[24 h shadow diff,<br/>cohort rollout, gate]
    B6 -->|"writes for half"| M6[Promote replica, RPO ~1 s,<br/>re-diff from raw]
    B7 -->|"one P0 alert"| M7[Re-entrant claim: own alert_id<br/>carries on, P0 sweeper]

    class ROOT client
    class B1,B2,B3,B4,B5,B6,B7 decision
    class M1,M2,M3,M4,M5,M6,M7 service

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

The widest blast radius on this side is a bad batch (every member in it), bounded by the gate (solution §5.3). Nothing here is red: the pipeline can fall behind and catch up. The red node is on the member side (D11b).

### D11b. Delivery and read

```mermaid
%% D11b: the member side. The read path is red: every mitigation here exists to keep opens under its 70% line.
flowchart TD
    ROOT[Member side] --> C1[Scheduler shard owner dies]
    ROOT --> C2[Sender dies after 200]
    ROOT --> C3[APNs or FCM 429 or outage]
    ROOT --> C4[Page cache lost]
    ROOT --> C5[Alert store region lost]
    ROOT --> C6["Member read path<br/>saturated"]:::critical
    C1 -->|"1/64 of P1, ~30 s"| N1[Lease expiry,<br/>claims protect in-flight]
    C2 -->|"one alert"| N2[Lease resend,<br/>collapse id replaces]
    C3 -->|"one platform"| N3[Backoff, P0 reserved share,<br/>P1 rolls, P0 email]
    C4 -->|"every open misses"| N4[KV takes ~1.1k/s organic,<br/>controller slows release]
    C5 -->|"sends for half"| N5[Other region takes shards,<br/>resends replace in place]
    C6 -->|"every open"| N6[Release drops to zero,<br/>shed non-essential calls]

    class ROOT client
    class C1,C2,C3,C4,C5 decision
    class N1,N2,N3,N4,N5,N6 service

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
```

## D12. Rollout / migration

From a nightly job that diffs scores and sends every alert at once, to this design. Each phase has a rollback point; no phase needs a coordinated deploy (solution §8).

```mermaid
%% D12: migration phases with a rollback point after each. Pulls move to slots last, without any member pulled twice in a week.
gantt
    title From the nightly job to slots, gate and scheduler
    dateFormat YYYY-MM-DD
    axisFormat %b %d
    section Build
    Snapshot KV and backfill of latest per member and bureau :p1, 2026-11-02, 14d
    Rollback point, drop the new KV, old job untouched :milestone, r1, after p1, 0d
    section Shadow
    Diff and decider in shadow, alerts not sent, daily diff vs old job :p2, after p1, 21d
    Rollback point, stop shadow consumers :milestone, r2, after p2, 0d
    section Cutover
    Scheduler sends for 1 then 10 then 50 then 100 percent of members :p3, after p2, 21d
    Rollback point, cohort flag back to old sender :milestone, r3, after p3, 0d
    section Gate
    Gate report-only, then enforcing :p4, after p2, 28d
    section Slots
    Pulls move to slots, first slot at least 7 days after last pull :p5, after p3, 14d
    Rollback point, scheduler reverts to the old pull calendar :milestone, r5, after p5, 0d
    section Retire
    Delete the nightly job and its tables :p6, after p5, 7d
```

The gate runs report-only from the start of shadow, so its thresholds are tuned on 4 weeks of real batches before it can hold anything. The slot move is last because it is the only phase that changes what we buy from the bureaus.
