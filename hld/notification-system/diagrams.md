# Diagrams: Notification system, critical and promotional, 1M deliveries a second

> One-line answer: twelve views of one design. A **critical lane** (send API, a small Kafka cluster with `acks=all`, planners on a CDC-fed profile copy, per-provider topics, critical senders that claim each message and send it with its remaining lifetime and a collapse id) and a **bulk lane** (frozen segment chunks, a release controller that computes the rate every second, expanders that decide per user and write through Kafka transactions, bulk senders that commit before sending) share nothing we can separate except the providers. A quota coordinator per provider account reserves 2x the critical peak, lets critical preempt the rest within 2 s, and leases what is left to promotions. Status is an event stream; a campaign's inbox entry is a bitmap. Provider egress (the FCM project quota and the APNs pools) is the red box.

The D1 to D12 set from `hld/CLAUDE.md` §4, each with a one-line caption. A diagram already in [`solution.md`](solution.md) gets a heading, a caption and a link, never a second copy. Acronyms: APNs (Apple Push Notification service), FCM (Firebase Cloud Messaging), OTP (one-time password), SMS (short message service), KST (Korea Standard Time), CDC (change data capture), TTL (time to live), DLR (SMS delivery receipt), AZ (availability zone), RF (replication factor), ISR (in-sync replicas), SDK (software development kit), JWT (JSON Web Token), DR (disaster recovery).

| # | Diagram | Where it lives |
|---|---|---|
| D1 | Context | below |
| D2 | Data flow | below |
| D3 | Component architecture (final design) | [solution §6](solution.md#6-final-design-and-the-six-core-flows) |
| D4 | Happy path per FR | FR1 critical send: [solution §4.1](solution.md#41-a-service-sends-a-critical-notification-to-one-user-and-it-reaches-apple-or-google-in-under-a-second). FR2 campaign: [solution §4.2](solution.md#42-marketing-sends-a-campaign-to-103-to-2-x-107-users-inside-a-window-at-a-rate-we-choose). FR3 opt-out during a campaign: [solution §4.3](solution.md#43-every-send-obeys-the-users-preferences-quiet-hours-frequency-caps-and-the-advertising-law). FR4 status and inbox: [solution §4.4](solution.md#44-callers-can-query-each-deliverys-status-and-users-see-recent-notifications-in-an-inbox). OTP by SMS and token registration with cleanup: below |
| D5 | Failure paths | Expander crash mid-chunk, SMS vendor failover, release controller failover: below. Sender crash after APNs 200: [solution §5.4](solution.md#54-a-worker-crashes-right-after-the-provider-accepted-the-message-how-do-you-avoid-a-second-otp-or-a-second-promotion-and-what-is-the-dedup-key). FCM down 30 minutes: [solution §10.4](solution.md#104-failure-timeline) |
| D6 | Decision flow | Per-user decision at release, and one message whose provider is down: below. Expiry at every hop: [solution §5.3](solution.md#53-every-notification-expires-who-enforces-it-and-what-does-a-provider-do-with-a-late-one). Inside a sender: [solution §10.1](solution.md#101-internals-of-each-chosen-technology) |
| D7 | Entity relationship | [solution §3.3](solution.md#33-data-model) |
| D8 | State machines | Critical delivery, campaign, promotional delivery, chunk: below |
| D9 | Deployment / topology | below |
| D10 | Scaling / partitioning | below |
| D11 | Failure mode map | below, two trees |
| D12 | Rollout / migration | below |

## D1. Context (zoom-out)

Our platform as one box: product services and marketing send in, providers carry messages out, phones send preferences, receipts and inbox reads back.

```mermaid
%% D1: the system as one box with every external actor. Providers sit outside our trust boundary and set the speed limit.
flowchart LR
    SVC[Product services<br/>chat, orders, payments, auth] -->|"critical and single-user sends,<br/>~5k/s avg, 50k/s peak"| SYS[Notification platform<br/>two lanes, status, inbox]
    MK[Marketing console] -->|"campaigns, ~50 a day,<br/>up to 2 x 10^7 users"| SYS
    SEG[Segment service] -->|"user ids, frozen at T minus 10 min"| SYS
    SYS -->|"HTTP/2, ~30% of push"| APNS[APNs]
    SYS -->|"HTTP v1, ~70% of push,<br/>quota per project"| FCM[FCM]
    SYS -->|"OTP, fallback, ~4.3 M a day"| SMS[SMS vendors A and B]
    SYS -->|"receipts, ~43 M a day"| EM[Email provider]
    APP[User app and SDK] -->|"preferences, tokens,<br/>receipts, inbox reads"| SYS
    APNS -->|"push"| APP
    FCM -->|"push"| APP

    class SVC,MK,APP client
    class SYS service
    class SEG,APNS,FCM,SMS,EM external

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

## D2. Data flow (DFD)

Inputs to outputs with format, size and rate. Peaks are the 1M a second design peak from solution §2; daily volumes in brackets.

```mermaid
%% D2: data flow. Stores are cylinders, processes are rounded. The bulk records are compact so Kafka carries ~306 MB/s, not ~1 GB/s.
flowchart LR
    IN1[Critical calls] -->|"JSON ~1 KB, 50k/s peak<br/>(432 M a day)"| P1(Send API and planners)
    P1 -->|"per-token record ~1 KB,<br/>55k/s push, 6k/s SMS and email"| CK[[Critical topics,<br/>short and long, 24 h]]
    IN2[Campaigns] -->|"20 M ids, 2,000 chunk files<br/>of ~20 KB, at T minus 10 min"| BL[(Blob store, chunks)]
    BL -->|"10k ids per chunk,<br/>~100 chunks/s at peak"| P2(Expanders)
    PR[(Profile caches<br/>30 GB each)] -->|"~1 KB per user,<br/>929k/s, ~560 MB/s"| P2
    P2 -->|"compact record ~300 B,<br/>1.02 M/s (at most ~66 M a day after caps)"| BK[[Bulk topics, zstd, 24 h]]
    CK -->|"records"| P3(Senders)
    BK -->|"records"| P3
    P3 -->|"request ~1 KB, 1.1 M/s,<br/>~9 Gbps (~0.55 TB a day)"| PV[Providers]
    P3 -->|"outcome ~150 B,<br/>~1.2 M/s peak"| OUT[[crit.outcomes and<br/>outcomes, 3 days]]
    OUT -->|"~71k/s point upserts"| ST[(Status rows<br/>30 days, ~16.5 TB)]
    OUT -->|"~2 B events a day"| OL[(Outcome log<br/>90 days, ~11 TB)]
    OUT -->|"bitmaps per campaign"| IB[(Inbox<br/>30 days, ~6.4 TB)]
    CK -->|"accepted, from crit.requests:<br/>status rows, inbox rows 15k/s"| ST
    CK -->|"inbox row on accepted"| IB

    class IN1,IN2 client
    class P1,P2,P3 service
    class BL,PR,ST,OL,IB store
    class CK,BK,OUT queue
    class PV external

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

## D3. Component architecture

The final design, 15 nodes, provider egress in red: [solution §6](solution.md#6-final-design-and-the-six-core-flows).

## D4. Happy paths, one per FR

**FR1 to FR4:** links in the table above. Two more paths that every answer leans on.

**OTP by SMS, with the lifetime handed to the vendor.** The code is fixed when planned, so any resend carries the same code.

```mermaid
%% D4 OTP: a 3-minute OTP leaves with ValidityPeriod 170 s, so it cannot reach the phone 10 hours later from the vendor's queue.
sequenceDiagram
    autonumber
    participant A as Auth service
    participant API as Send API
    participant P as Planner
    participant S as SMS sender
    participant V as SMS vendor A
    participant U as Phone
    A->>API: POST otp, code 482913, key login_77, lifetime 3 min
    API-->>A: 202 n_51c0, expires 11:03:00
    P->>P: render body with the code, record on crit.sms
    S->>S: 11:00:02, 178 s left, above the 30 s SMS margin
    S->>V: send, ValidityPeriod 168, OTP messaging service
    V-->>S: 201 accepted, message id
    V->>U: SMS at 11:00:04
    V-->>S: DLR delivered, status callback
    S->>S: outcomes sent then delivered
```

**Device token registration and cleanup on APNs 410.** A token is deleted only if it was registered before Apple's 410 timestamp, so a reinstall that re-registered the same token survives.

```mermaid
%% D4 tokens: registration updates registered_at. A 410 from APNs deletes the token only if registered_at is older than the 410 timestamp.
sequenceDiagram
    autonumber
    participant U as App
    participant PS as Preference service
    participant DR as Device registry
    participant C as profile caches
    participant S as APNs sender
    participant X as APNs
    U->>PS: POST devices, token t9, ios
    PS->>DR: upsert t9, registered_at 09:00
    DR->>C: CDC, t9 in both caches in about 1 s
    S->>X: push to t9 at 14:00
    X-->>S: 410 Unregistered, timestamp 13:59
    S->>DR: delete t9 if registered_at before 13:59
    DR->>DR: 09:00 is before 13:59, deleted, invalid_at set
    DR->>C: CDC, t9 gone, no more sends to it
```

If the user had reinstalled and the app re-registered `t9` at 14:01, `registered_at` would be later than the 410's timestamp and the delete would not apply.

## D5. Failure paths

**(a) An expander dies mid-chunk.** It decides the chunk in memory and writes it last in one ~30 ms transaction, so a crash almost always lands before anything is written. The re-run finds its own ledger entries as re-entrant, so no cap is counted twice and no user gets two. A crash inside the 30 ms window leaves an open transaction that aborts after `transaction.timeout.ms` (10 s) and meanwhile holds back only the 16 partitions of its block.

```mermaid
%% D5a: an expander dies while deciding a chunk. Nothing was written, so nothing can be sent. The re-run re-produces the same records without counting caps twice.
sequenceDiagram
    autonumber
    participant K as bulk.chunks
    participant E1 as Expander e2
    participant L as Promo ledger
    participant B as bulk.fcm and bulk.apns
    participant E2 as Expander e9
    K->>E1: chunk cmp_7 17, block 3, offset 340
    E1->>L: ledger script for 6,500 users, ALLOW
    E1->>E1: decide all 10k in memory, about 0.3 s
    Note over E1: process dies before the transaction opens
    Note over K,E2: about 10 s later, partition moves to e9
    K->>E2: chunk cmp_7 17, offset 340 again
    E2->>E2: campaign-progress caught up, no expanded marker
    E2->>L: ledger script, finds cmp_7 chunk 17
    L-->>E2: REENTRANT, cap not counted again
    E2->>B: one 30 ms transaction, 16 partitions per topic
    E2->>B: records, expanded marker, offset, commit
    Note over B: senders see each record once
```

**(b) SMS vendor A goes down at 03:00, when OTP runs at ~5 a second.** The volume rule (at least 200 attempts in 10 s) never fires at that rate, so each OTP fails over by itself after one timeout, and the breaker opens after 20 consecutive failures. Codes stuck in A's queue die with their validity period.

```mermaid
%% D5b: vendor A fails at night. Per-message failover with the same code, then the breaker. A same-code duplicate is possible and harmless.
sequenceDiagram
    autonumber
    participant S as SMS sender
    participant VA as Vendor A
    participant VB as Vendor B
    participant U as Phone
    participant OC as On-call
    S->>VA: 03:00:02 OTP n_51c0, ValidityPeriod 168
    VA--xS: timeout after 2 s
    S->>VB: n_51c0 at once, same code, ValidityPeriod 166
    VB->>U: SMS at 03:00:05
    S->>VA: next OTPs, each fails over after its own timeout
    S->>S: 20 consecutive failures, breaker A OPEN
    S->>VB: all OTP now goes to B first
    S->>OC: page, critical provider breaker open 60 s
    Note over VA,VB: if A recovers within 168 s it may deliver the same code once more
    Note over VA,VB: after 168 s A drops it in its own queue
    S->>VA: probe 1% every 5 s, close after 30 s clean
```

**(c) The release controller leader dies mid-campaign.** A new leader takes the lease, and Kafka's producer epoch fences the old one if it wakes up.

```mermaid
%% D5c: controller failover. About 10 s without releases. The topics hold ~30 s of work, so senders keep sending. A zombie leader cannot release.
sequenceDiagram
    autonumber
    participant R1 as Controller c1, leader
    participant LS as Lease store
    participant K as Kafka, bulk.chunks and campaign-progress
    participant R2 as Controller c2
    R1->>K: release chunks 900 to 905 with cursor, one transaction
    Note over R1: 10:03:00 stalls, long GC pause
    R2->>LS: 10:03:10 lease expired, acquire, term 8
    R2->>K: initTransactions, epoch bump fences c1
    R2->>K: read cursor, last committed 905
    R2->>K: release 906 onward at the current rate
    R1->>K: 10:03:15 wakes, tries to release 906
    K-->>R1: ProducerFenced, abort
    R1->>LS: lease lost, step down
```

## D6. Activity / decision flow

**(a) One user, one promotional decision at release.** Cheapest checks first. The ledger script is the last and only write.

```mermaid
%% D6a: the expander's per-user decision for an advertising campaign. Every exit is an outcome with a reason.
flowchart TD
    U[User in chunk] --> E{Profile exists and<br/>category on for channel?}
    E -->|"no"| S1[suppressed, opt_out or deleted]
    E -->|"yes"| C{Advertising consent,<br/>re-check not overdue?}
    C -->|"no"| S2[suppressed, no_ad_consent]
    C -->|"yes"| N{Account KR, 20:58 to 08:00 KST,<br/>no night consent?}
    N -->|"yes"| D1{Window includes 08:01,<br/>before expiry?}
    D1 -->|"yes"| DF[deferred, night_rule]
    D1 -->|"no"| S3[suppressed, night_rule]
    N -->|"no"| Q{In the user's quiet hours?}
    Q -->|"yes, wake before expiry"| DF2[deferred, quiet_hours]
    Q -->|"no"| L{Ledger script}
    L -->|"DUP or CAPPED"| S4[suppressed, dup or capped,<br/>inbox only if capped]
    L -->|"ALLOW or REENTRANT"| OK[records per token,<br/>user added to bitmap]

    class U service
    class E,C,N,D1,Q,L decision
    class S1,S2,S3,S4 store
    class DF,DF2 queue
    class OK service

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

Quiet hours whose end is after the expiry fall through to `suppressed, quiet_hours` (not drawn, to stay under 15 nodes).

**(b) One message whose provider's breaker is open.** The type registry decides: drop, switch channel, wait, or pause the campaign.

```mermaid
%% D6b: one message whose provider breaker is open. The type registry decides per type.
flowchart TD
    M[Message for a provider<br/>whose breaker is open] --> E{Still alive at<br/>the next dequeue?}
    E -->|"no"| EX[expired, counted per type]
    E -->|"yes"| F{Type has a fallback?}
    F -->|"OTP"| SMSB[Other SMS vendor<br/>or push and email]
    F -->|"payment_failed"| EM[Email after 60 s,<br/>push still waits]
    F -->|"none"| W{Lane?}
    W -->|"critical"| KQ[[Waits in its crit topic<br/>short-lived drained first, ramped]]
    W -->|"bulk"| BQ{Backlog under<br/>share x time left?}
    BQ -->|"yes"| BW[[Waits in bulk topic]]
    BQ -->|"no"| PA[Campaign paused<br/>for that provider]

    class M service
    class E,F,W,BQ decision
    class EX store
    class SMSB,EM,PA service
    class KQ,BW queue

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

## D7. Entity relationship

Type registry, notifications, claims, profiles, ledger, campaigns, chunks, bitmaps, inbox and outcomes, with keys and TTLs: [solution §3.3](solution.md#33-data-model).

## D8. State machines

**Critical delivery (one provider message).** `SENDING` is the claim; its lease is what lets a crashed sender's message be resent. A reader that finds a live lease parks the record, unresolved, until the lease runs out; it never skips it. A reader that finds `SENT` re-publishes the `sent` outcome before committing, so a crash between marking and publishing cannot leave the row at `accepted`.

```mermaid
%% D8a: one critical provider message. PARKED is a live lease seen on a re-read, held unresolved. Terminal states are SENT then receipts, EXPIRED, FAILED and SUPPRESSED.
stateDiagram-v2
    direction LR
    [*] --> PLANNED : planner writes record
    PLANNED --> SUPPRESSED : opt-out at plan
    PLANNED --> EXPIRED : dequeued too late
    PLANNED --> SENDING : claim NX, lease 10 s
    SENDING --> SENDING : lease expired, attempt 2
    SENDING --> PARKED : re-read, lease live
    PARKED --> SENDING : lease expired, attempt 2
    PARKED --> SENT : owner marked SENT
    SENT --> SENT : re-read, outcome re-published
    SENDING --> SENT : provider 200
    SENDING --> RETRY_15M : APNs 5xx, long-lived
    SENDING --> FAILED : 410, 400, 413
    RETRY_15M --> SENDING : due
    RETRY_15M --> EXPIRED : past expires_at
    SENT --> DELIVERED : SDK receipt
    DELIVERED --> OPENED : tap
    SENT --> OPENED : tap, no receipt
    OPENED --> [*]
    EXPIRED --> [*]
    FAILED --> [*]
    SUPPRESSED --> [*]
```

**Campaign.** Pause stops releases at the next second; records already queued (up to ~30 s of work) still go. Cancel carries a cancel epoch on the compacted `campaign-control` topic: every bulk sender drops the campaign's queued records at dequeue (`cancelled`), checks its cached control state again immediately before each provider call, and acknowledges the epoch. The campaign is `CANCELLING` until every sender has acknowledged, then `CANCELLED`; only work already handed to provider clients (~1 s per sender) still leaves. "All chunks expanded" is `DRAINING`, not done: the campaign is `COMPLETED` only when every delivery has a terminal outcome, and a drain job marks any record still without one at the expiry as `unknown`.

```mermaid
%% D8b: campaign lifecycle. CANCELLING waits for every sender to acknowledge the cancel epoch. DRAINING waits for a terminal outcome on every delivery.
stateDiagram-v2
    direction LR
    [*] --> DRAFT
    DRAFT --> SCHEDULED : approved
    SCHEDULED --> SNAPSHOTTED : T minus 10 min
    SNAPSHOTTED --> SENDING : window start
    SENDING --> PAUSED : pause or ledger down
    PAUSED --> SENDING : resume
    SENDING --> DRAINING : all chunks expanded
    DRAINING --> COMPLETED : every delivery terminal
    SENDING --> CANCELLING : cancel epoch n
    PAUSED --> CANCELLING : cancel epoch n
    DRAINING --> CANCELLING : cancel epoch n
    CANCELLING --> CANCELLED : all senders acked n
    PAUSED --> EXPIRED : past expires_at
    SENDING --> EXPIRED : past expires_at
    COMPLETED --> [*]
    CANCELLED --> [*]
    EXPIRED --> [*]
```

**Promotional delivery (one record on `bulk.fcm` or `bulk.apns`).** At most once: the offset is committed before the send, so a crash or an ambiguous timeout ends in `UNKNOWN`, never in a resend. `UNKNOWN` ranks with `FAILED` in the status merge.

```mermaid
%% D8d: one promotional delivery record. UNKNOWN is terminal: set by the sender on a timeout after the request was written, or by the drain job for records a crashed sender held.
stateDiagram-v2
    direction LR
    [*] --> QUEUED : expander commits record
    QUEUED --> CANCELLED : campaign cancelled
    QUEUED --> EXPIRED : dequeued too late
    QUEUED --> SUPPRESSED : withdrawn since decision
    QUEUED --> TAKEN : offset committed
    TAKEN --> SENT : provider 200
    TAKEN --> FAILED : definite error
    TAKEN --> UNKNOWN : timeout after write
    TAKEN --> UNKNOWN : sender crashed
    SENT --> DELIVERED : sampled receipt
    DELIVERED --> OPENED : tap
    SENT --> OPENED : tap
    OPENED --> [*]
    UNKNOWN --> [*]
    FAILED --> [*]
    CANCELLED --> [*]
    EXPIRED --> [*]
    SUPPRESSED --> [*]
```

**Chunk.** The state lives on `campaign-progress` in Kafka; the campaign DB is a projection for the console.

```mermaid
%% D8c: chunk lifecycle. An aborted expansion returns the chunk to RELEASED; an expanded marker makes a re-release a no-op.
stateDiagram-v2
    direction LR
    [*] --> PENDING : snapshot written
    PENDING --> RELEASED : controller, in a transaction
    RELEASED --> EXPANDING : expander reads it
    EXPANDING --> RELEASED : crash, transaction aborted
    EXPANDING --> EXPANDED : records, marker, offset commit
    EXPANDED --> EXPANDED : re-released, skipped
    PENDING --> SKIPPED : campaign cancelled or expired
    EXPANDED --> [*]
    SKIPPED --> [*]
```

## D9. Deployment / topology

One region, three AZs. Every tier is N+1 per AZ. A warm standby region receives mirrored Kafka and CDC so it can take over critical traffic; the RPO on region loss is the mirror lag, p99 under 2 s.

```mermaid
%% D9: one region, 3 AZs, two lanes per AZ with their own NAT. The four Redis clusters are separate, each with shards and replicas spread over the 3 AZs. Kafka RF 3 with one replica per AZ. A warm DR region gets mirrored topics.
flowchart LR
    subgraph AZA[AZ a]
        CA[Critical lane<br/>API 3, planners 3, senders 6,<br/>2 critical brokers]
        BA[Bulk lane<br/>expanders 10, senders 20,<br/>3 bulk brokers]
    end
    subgraph AZB[AZ b]
        CB[Critical lane, same]
        BB[Bulk lane, same]
    end
    subgraph AZC[AZ c]
        CC[Critical lane, same]
        BC[Bulk lane, same]
    end
    CA <-->|"Kafka replication, min ISR 2"| CB
    CB <-->|"replication"| CC
    BA <-->|"replication"| BB
    CA -->|"claim, park, mark"| CLM[(Claim store<br/>8 shards x 2)]
    CA -->|"1 read per send"| PCR[(profile-crit<br/>6 nodes)]
    BA -->|"ledger script"| LED[(Promo ledger<br/>24 shards x 2)]
    BA -->|"multi-get 500"| PBK[(profile-bulk<br/>15 nodes)]
    CA -->|"own NAT"| PV[APNs, FCM, SMS, email]
    BA -->|"own NAT"| PV
    CB -->|"mirror topics, CDC,<br/>lag p99 under 2 s"| DR[Warm DR region<br/>critical lane only]

    class CA,CB,CC,BA,BB,BC service
    class CLM,PCR,LED,PBK store
    class PV external
    class DR service

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

What crosses an AZ boundary: Kafka replication in both clusters, Redis replica sync, consumer reads from leaders in other AZs. The four Redis clusters are separate, each with shards and replicas spread over the AZs: the claim store (8 shards x 2) and `profile-crit` (6 nodes) serve the critical lane, the promo ledger (24 shards x 2) and `profile-bulk` (15 nodes) the bulk lane. That is the ~85 Redis nodes in the solution's cost model, and a ledger incident (which pauses campaigns) cannot take critical claims with it. Every AZ sends to the providers through its own NAT gateways, one set per lane, so ~9 Gbps of bulk egress cannot fill the critical path. Losing an AZ leaves the critical lane at 8 of 12 senders (`8 × 20k = 160k/s` against a 55k/s peak, ~3x) and the bulk lane at ~800k/s (solution §10.3).

**Losing the region.** The DR region runs the critical lane only; campaigns wait for the primary. Critical notifications accepted in the last mirror-lag window (p99 under 2 s) may be lost with the region. Callers re-send anything without a terminal status from their own outbox with the same idempotency key; the standby's claim store starts empty, so the re-sends go through, a push that had already gone out is replaced in place by its collapse id, and `expires_at` (from the caller's `created_at`) drops anything past its life.

## D10. Scaling / partitioning

Everything per user is keyed by `user_id`, so one user's tokens, ledger entry and per-device limits sit with one owner. The hot key is not a user: it is a single quota counter, if anyone builds one.

```mermaid
%% D10: partitioning by user_id at every hop, and the hot key that the coordinator design removes. The global counter is red: at 754k increments per s it is the first thing to melt.
flowchart LR
    R[Record for user_id] -->|"hash mod 64"| CP[Critical topics<br/>64 partitions, ~800/s each]
    R -->|"hash mod 256"| BP[Bulk topics<br/>256 partitions, ~2.8k/s each]
    R -->|"hash slot"| LG[(Ledger, 24 shards<br/>~39k scripts/s each)]
    CP -->|"owner"| CS[Critical sender<br/>per-token limiter local]
    BP -->|"owner"| BS[Bulk sender<br/>per-token limiter local]
    CS -->|"every message, rejected design"| GC[Global FCM counter<br/>754k INCR per s, one key]
    BS -->|"every message, rejected design"| GC
    CS -->|"demand every 1 s"| QC[Quota coordinator<br/>per provider account]
    BS -->|"demand every 1 s"| QC
    QC -->|"2 s lease, local bucket"| CS
    QC -->|"2 s lease, local bucket"| BS

    class R service
    class CP,BP queue
    class LG store
    class CS,BS,QC service
    class GC critical

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
```

- A seller account that receives thousands of order events a minute adds ~170/s to one critical partition, against ~800/s average: the partition is fine, the phone is not (FCM allows 240 a minute per Android device). Above 1 push a second per (user, type) the sender sends a digest every 10 s instead, and the inbox keeps every row. A user cannot be hot on the bulk lane, because the ledger caps promotions at 2 a day.
- The global counter is the "Good" rung of solution §5.1. Leases give the same bound with one message per node per second: 72 sender nodes, ~72 lease calls a second instead of 754k increments.
- Chunks are keyed by `campaign_id:chunk_no` on 32 partitions, so a re-released chunk lands on the same expander as its first copy and is skipped once that expander has caught up on `campaign-progress`. The frozen audience is sorted by partition block (`(hash(user_id) mod 256) div 16`), so one chunk writes to 16 of the 256 bulk partitions per topic, and chunks are released round robin over the 16 blocks.

## D11. Failure mode map

Component, what fails, blast radius, mitigation. Two trees to stay under 15 nodes. Matches solution §8.

```mermaid
%% D11 tree 1: the critical lane. The FCM quota is red: a breach of the critical reserve would 429 chat pushes.
flowchart TD
    ROOT[Critical lane] --> KF[Critical Kafka]
    ROOT --> CL[Claim store]
    ROOT --> SN[Critical sender node]
    ROOT --> FQ[FCM project quota]
    KF -->|"unavailable"| KFB[API returns 503,<br/>callers retry same key]
    KFB -->|"mitigate"| KFM[RF 3, 3 AZs,<br/>min ISR 2]
    CL -->|"down"| CLB[No claims,<br/>duplicates possible]
    CLB -->|"mitigate"| CLM[Fail open,<br/>collapse id replaces]
    SN -->|"crash after 200"| SNB[~700 resent<br/>after ~10 s]
    SNB -->|"mitigate"| SNM[Same collapse id,<br/>replaces in place, best effort]
    FQ -->|"429 on critical"| FQB[Chat and OTP<br/>back off, p99 blown]
    FQB -->|"mitigate"| FQM[Reserve 2x peak, preempt<br/>bulk up to 270k/s, page]

    class ROOT,KF,CL,SN service
    class FQ critical
    class KFB,CLB,SNB,FQB decision
    class KFM,CLM,SNM,FQM store

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

```mermaid
%% D11 tree 2: the bulk lane and shared inputs. A wrong campaign has the biggest blast radius: it cannot be recalled once sent.
flowchart TD
    ROOT[Bulk lane and inputs] --> LD[Promo ledger]
    ROOT --> CDC[CDC to profile caches]
    ROOT --> BN[Bulk sender node]
    ROOT --> WC[Wrong campaign]
    LD -->|"down"| LDB[No caps, no dedup]
    LDB -->|"mitigate"| LDM[Fail closed,<br/>campaigns pause]
    CDC -->|"lag over 30 s"| CDCB[Opt-outs not yet seen]
    CDCB -->|"mitigate"| CDCM[Campaigns auto-pause,<br/>page at 60 s]
    BN -->|"crash"| BNB[~2.5k reported unknown,<br/>buffer capped at 5k]
    BNB -->|"mitigate"| BNM[Accepted, at most once,<br/>counted as unknown]
    WC -->|"wrong segment or price"| WCB[~6 M phones<br/>in 60 s at 100k/s]
    WCB -->|"mitigate"| WCM[Second approver, 1% canary,<br/>cancel epoch acked by every sender,<br/>~100k in flight, correction by campaign id]

    class ROOT,LD,CDC,BN,WC service
    class LDB,CDCB,BNB,WCB decision
    class LDM,CDCM,BNM,WCM store

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

## D12. Rollout / migration

From a legacy sender (one queue, one worker pool, one Firebase project, campaigns as scripts) to the two lanes. Both systems spend the same FCM project quota until legacy is off, so legacy runs under a client-side limiter whose grant the coordinator accounts for. Each critical type has an owner flag with an `effective_from` a minute ahead; both systems compare `accepted_at` to it, so each notification has exactly one sender.

```mermaid
%% D12: migration phases with a rollback point at the end of each. Legacy keeps a static FCM grant until the last phase.
gantt
    title Legacy sender to critical and bulk lanes
    dateFormat YYYY-MM-DD
    axisFormat %b %d
    section Shadow
    CDC caches and planner decide in shadow, compare     :a1, 2026-12-01, 14d
    Coordinator observes, legacy gets a static FCM grant :a2, 2026-12-08, 7d
    Rollback point, drop shadow, no sends affected       :milestone, m1, after a2, 0d
    section Critical types
    order_status on the new lane                         :a3, after a2, 5d
    chat_message on the new lane                         :a4, after a3, 5d
    payment types, then otp last                         :a5, after a4, 7d
    Rollback point per type, new effective_from          :milestone, m2, after a5, 0d
    section Campaigns
    Legacy campaigns write the new ledger via adapter    :a6, after a2, 7d
    New campaigns on the bulk lane, one owner each       :a7, after a6, 14d
    Rollback point per campaign                          :milestone, m3, after a7, 0d
    section Legacy
    Legacy at zero traffic for 2 weeks                   :a8, after a7, 14d
    Remove legacy, give its FCM grant to the bulk share  :a9, after a8, 3d
```

Gates between steps: decisions in shadow agree with legacy on at least 99.9% of sends (the rest are explained bugs), the critical p99 stays under 1 s, zero reconciler gaps, no FCM 429 on the critical lane, and per-type expired and failed rates within 0.5 points of legacy.
