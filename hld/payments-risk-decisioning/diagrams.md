# Diagrams: QuickBooks Payments with inline risk decisioning

> One-line answer: twelve views of one design. A synchronous path (orchestrator, risk decision service with rules, GBDT and policy in process, one hedged 4-shard feature read, one counter-cluster script) answers in ~15 ms p50 and steps down a ladder (validated `PARTIAL`, rules on what arrived, a signed table under attempt and dollar budgets) when a stage misses its deadline. The orchestrator's payment row holds the inline decision of record. An asynchronous path (Kafka, Flink, decision lake, labels, training, control plane) learns. A post-auth path (re-scorer, review, payout risk) decides when money may leave. The online feature store is the one red box: its tail sets the decision's tail.

The D1 to D12 set from `hld/CLAUDE.md` §4, each with a one-line caption. A diagram already in [`solution.md`](solution.md) gets a heading, a caption and a link, never a second copy. Acronyms: ACH (automated clearing house), GBDT (gradient-boosted decision trees), 3DS (3-D Secure), AZ (availability zone), KV (key-value), TC40 (Visa issuer fraud report), ODFI (originating depository financial institution, the merchant-side bank in ACH), NSF (non-sufficient funds), WEB (internet-initiated ACH entry), CAPTCHA (a challenge that tells humans from bots), TTL (time to live), PSI (population stability index).

| # | Diagram | Where it lives |
|---|---|---|
| D1 | Context | below |
| D2 | Data flow | below, plus D2b the streaming feature job |
| D3 | Component architecture (final design) | [solution §6](solution.md#6-final-design-and-the-core-flows) |
| D4 | Happy path per FR | FR1 decide: [solution §4.1](solution.md#41-decide-inline-inside-the-budget). FR2 degrade: [§4.2](solution.md#42-degrade-safely-a-bounded-pre-agreed-answer). FR3 learn: [§4.3](solution.md#43-learn-features-labels-retraining-safe-rollout). FR4 act after: [§4.4](solution.md#44-act-after-the-payment-re-score-review-hold-the-money). New below: an ACH payment, a 3DS step-up, a payout |
| D5 | Failure paths | Below: a gray AZ and a dead replica, a resumed payment, the counter cluster fails during an attack, a re-sent dispute file. In solution: card testing (§5.3), risk unreachable after a bad deploy ([§10.4](solution.md#104-failure-timeline)) |
| D6 | Decision flow | Fallback: [solution §5.2](solution.md#5-deep-dives). Rule and model precedence: below |
| D7 | Entity relationship | [solution §3.3](solution.md#33-data-model) |
| D8 | State machines | Model version: [solution §5.5](solution.md#5-deep-dives). Rule (with auto-kill), payout hold, payment risk lifecycle: below |
| D9 | Deployment / topology | below |
| D10 | Scaling / partitioning | below |
| D11 | Failure mode map | below, two trees |
| D12 | Rollout / migration | below |

## D1. Context (zoom-out)

Our system as one box: the orchestrator asks, the networks and banks report outcomes weeks later, analysts steer, payouts ask how much may leave.

```mermaid
%% D1: risk decisioning as one box with every external actor. Nine nodes.
flowchart LR
    BUY[Buyers<br/>invoices, links, in person]:::client -->|"card or bank details,<br/>device session"| QBP[QuickBooks Payments<br/>orchestrator]:::service
    MER[Merchants<br/>QuickBooks users]:::client -->|"charges, keyed cards,<br/>instant deposit requests"| QBP
    QBP -->|"Decide, 100 ms"| SYS[Risk decisioning<br/>inline, post-auth,<br/>payout risk]:::service
    SYS -->|"APPROVE, STEP_UP,<br/>REVIEW, DECLINE"| QBP
    QBP -->|"authorize, capture,<br/>ACH files"| NET[Processor, card networks,<br/>ODFI bank]:::external
    NET -->|"disputes, TC40 reports,<br/>ACH returns"| SYS
    SYS -->|"holds, reserves,<br/>payable amount"| PAY[Payouts + ledger]:::external
    ANA[Risk analysts]:::client <-->|"rules, cases,<br/>labels"| SYS
    SYS -->|"reason category,<br/>hold notices"| MER
    ONB[Onboarding, KYB]:::external -->|"merchant facts,<br/>bank account changes"| SYS
    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

## D2. Data flow (DFD)

Inputs to outputs with format, size and rate. Peak today unless marked design (2k/s). Volumes from solution §2; marked [estimate] there.

```mermaid
%% D2: data flow. Processes are rounded, stores are cylinders. The online feature store is red because its read tail sets the decision's tail.
flowchart LR
    ORC[Payment orchestrator]:::service -->|"Decide, protobuf ~1 KB,<br/>350/s peak, 2k/s design"| RDS(Risk decision service):::service
    RDS -->|"RiskDecision ~0.5 KB,<br/>p99 under 100 ms"| ORC
    OFS[(Online feature store<br/>~120 GB, 4 shards)]:::critical -->|"~16 entity rows ~10 KB,<br/>8k multi-gets/s design"| RDS
    RDS <-->|"counter script ~200 B,<br/>2k/s at design"| HOT[(Counter cluster<br/>Redis ~4 GB)]:::cache
    RDS -->|"SET NX ~50 B, 48 h,<br/>2k/s at design"| DD[(Dedup cluster<br/>Redis ~17 GB)]:::cache
    RDS -->|"decision + snapshot ~2 KB,<br/>3 M/day, 6 GB/day"| K[[Kafka]]:::queue
    ORC -->|"payment events ~1 KB, 30 M/day,<br/>decision written to its own row first"| K
    NET[Processor, networks,<br/>ODFI]:::external -->|"dispute, TC40, return files,<br/>~10k rows/day"| LI(Label ingest):::service
    LI -->|"labels ~200 B, dedup<br/>on source_event_id"| K
    K -->|"events re-keyed by entity,<br/>~120k keyed updates/s design"| FL(Flink feature jobs):::service
    FL -->|"window upserts"| OFS
    K -->|"Parquet ~1.2 GB/day"| LAKE[(Decision lake<br/>~3 TB after 7 years)]:::store
    LAKE -->|"~23 M training rows,<br/>weekly"| TR(Training + registry):::service
    TR -->|"model ~30 MB, rule bundles,<br/>fallback table"| RDS
    K -->|"every payment, 350/s"| RS(Post-auth re-scorer):::service
    RS -->|"holds ~15k/day, cases ~2k/day,<br/>estimate"| PR[(Payout risk<br/>holds, reserves)]:::store
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef cache    fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

### D2b. Inside the streaming feature job

Duplicates are dropped by `event_id` in keyed state; windows run on event time; the sink only overwrites an older window version, so a replay after a restart is harmless.

```mermaid
%% D2b: the Flink job behind the streaming features. Idempotent end to end without transactional sinks.
flowchart LR
    K[[payment-events<br/>by payment_id]]:::queue -->|"consume"| FX[Fan out per entity<br/>card, merchant, device,<br/>IP, email, bank]:::service
    FX -->|"keyBy entity"| DD[Dedup on event_id<br/>keyed state, TTL 1 h]:::service
    DD -->|"event time,<br/>watermark 5 s"| W[Sliding windows<br/>1 min, 10 min, 1 h, 24 h]:::service
    W -->|"counts, sums, distincts"| SK[Sink: upsert only if<br/>window version is newer]:::service
    SK -->|"entity row"| OFS[(Online feature store)]:::store
    W -.->|"checkpoint every 30 s"| CK[(State checkpoint<br/>object storage)]:::store
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
```

- A restart replays up to 30 s of events from the last checkpoint. Dedup state and versioned upserts make the replay a no-op, which is why the stream can lag tens of seconds during a restart and why the synchronous counters exist (solution §5.3). See [`../../concepts/stream-processing.md`](../../concepts/stream-processing.md).

## D3. Component architecture

The final design, online feature store in red. Embedded once in [solution §6](solution.md#6-final-design-and-the-core-flows).

## D4. Happy paths, one per FR

The four FR sequences are in solution §4.1 to §4.4 (links in the table above). Three more paths an interviewer asks for:

### D4a. A buyer pays a $2,400 invoice by bank transfer from a new account

The step-up is required by Nacha before the first WEB debit from an account; the money becomes payable only after the short return window.

```mermaid
%% D4a: ACH happy path. Validation first, debit in the next file, release after the NSF window, reserve for the 60-day unauthorized tail.
sequenceDiagram
    autonumber
    participant B as Buyer pay page
    participant V as Account verification
    participant O as Orchestrator
    participant R as Risk service
    participant A as ACH file job
    participant Y as Payout risk
    B->>O: pay invoice INV-301, 2400 USD by bank, account never seen
    O->>R: Decide(p_7, ACH_WEB, 240000 minor, validated_at empty)
    R-->>O: STEP_UP ACCOUNT_VERIFICATION, on success REVIEW, release after return window
    O->>V: instant verification, buyer signs in to the bank
    V-->>O: account valid, owner name matches the invoice customer
    O->>R: verification result as an event, not a second Decide
    O->>A: debit queued for the next file window
    A->>A: re-score before cut-off, p_fraud 0.02, entry sent
    Note over A,Y: settlement in 1 to 2 banking days, estimate
    Y->>Y: payable after the ~2 banking day NSF and admin return window
    Note over Y: an unauthorized R10 or R11 return is still possible for 60 days, covered by the merchant reserve
```

### D4b. A 3DS step-up, frictionless or challenged

`STEP_UP` carries its own fallbacks, so the orchestrator never comes back for a second decision.

```mermaid
%% D4b: card step-up. The issuer decides frictionless or challenge. A successful authentication typically shifts fraud-dispute liability to the issuer.
sequenceDiagram
    autonumber
    participant B as Buyer pay page
    participant O as Orchestrator
    participant R as Risk service
    participant T as 3DS server
    participant I as Issuer ACS
    participant P as Processor
    B->>O: pay 1400 USD, card tok_4
    O->>R: Decide(p_8, CNP_ONLINE, tier B, medium band)
    R-->>O: STEP_UP THREE_DS, on_fail DECLINE, on_unavailable REVIEW
    O->>T: authenticate p_8 with device and transaction data
    T->>I: authentication request
    alt frictionless
        I-->>T: authenticated, no buyer action
    else challenge
        I-->>B: one-time passcode screen
        B->>I: passcode
        I-->>T: authenticated
    end
    T-->>O: authenticated
    O->>P: authorize with the authentication data
    P-->>O: approved
    O->>R: THREE_DS_RESULT event for features and labels
```

### D4c. The 5 PM payout asks what is payable

Payout risk is the last gate: holds and the reserve come off the settled balance.

```mermaid
%% D4c: the payable check. Holds and reserve are ledger entries, so the read is one consistent balance.
sequenceDiagram
    autonumber
    participant P as Payout service
    participant Y as Payout risk
    participant L as Ledger
    P->>Y: payable(m_7) for the 5 PM run
    Y->>L: settled balance of m_7
    L-->>Y: 12400 USD settled
    Y->>Y: minus open holds 600, minus 5 pct rolling reserve 620
    Y-->>P: payable 11180, held 600, reserve 620
    P->>L: payout 11180, idempotent on payout id
    Note over Y: the hold on p_3 is released at 17:20 by the re-score and joins tomorrow's payout
```

## D5. Failure paths

### D5a. A gray AZ, then a dead replica

Hedging hides a slow call; latency-based ejection hides a slow AZ, which health checks never see ([`deep-dives/latency-budget-and-hot-path.md`](deep-dives/latency-budget-and-hot-path.md) simulates both).

```mermaid
%% D5a: AZ a goes gray (slow, packet loss), then one replica dies. Ejection moves reads to AZ b within about a second. Zero fallbacks after the first second.
sequenceDiagram
    autonumber
    participant R as Risk pod, AZ a
    participant S as Shard 2 replica, AZ a
    participant S2 as Shard 2 replica, AZ b
    participant C as Store control
    Note over S: t = 0, AZ a network goes gray, 3 pct packet loss, every local replica slow
    R->>S: multi-get, 5 keys
    Note over R: 6 ms, no answer, hedge
    R->>S2: same multi-get
    S2-->>R: rows at 7.5 ms
    Note over R: hedges hit the 5 pct cap, a few decisions miss 30 ms and fall back
    R->>R: t = 1 s, over 30 pct of AZ a calls slower than 6 ms, eject AZ a for 5 s
    R->>S2: reads go straight to AZ b, plus 0.5 ms each
    Note over R,S2: re-probe AZ a every 5 s, page if the hedge rate sits at its cap for 1 min
    Note over S: t = 4 min, the shard 2 replica in AZ a dies outright
    C->>C: mark it down, rebuild from snapshot and stream replay
    Note over C: no fallbacks, about 2 ms more p99 from cross-AZ reads until rebuilt
```

### D5b. A resumed payment gets the stored decision

The orchestrator writes the inline decision to its payment row before the processor call; risk's 48 h dedup only covers the gap before that write (solution §5.4).

```mermaid
%% D5b (retry): case 1, the row has the decision, no Decide call. Case 2, the pod died before the row write, the dedup answers. No counter moves twice.
sequenceDiagram
    autonumber
    participant OA as Orchestrator pod A
    participant OB as Orchestrator pod B
    participant DB as Payment row
    participant R as Risk service
    participant D as Dedup cluster
    OA->>R: Decide(p_9, attempt_created_at)
    R->>R: ZADD NX p_9 into attempt sets, ZADD GT its card into card sets, score 0.03, APPROVE
    R->>D: SET NX dec:p_9 = APPROVE d_9, TTL 48 h
    R-->>OA: APPROVE d_9, INLINE
    OA->>DB: write d_9 before the processor call
    Note over OA: pod A dies before calling the processor
    OB->>DB: resume p_9
    DB-->>OB: d_9 APPROVE, no Decide call, no counter touched
    Note over OB,D: had A died before the row write, OB calls Decide(p_9) and the dedup returns d_9
    Note over R: an attempt older than 48 h gets STALE_ATTEMPT, never a fresh decision
```

### D5c. The counter cluster fails during a card-testing run

The synchronous counters go away for ~10 s; attack mode, already pushed to every pod, and the per-pod attack counters keep merchants protected.

```mermaid
%% D5c: the counter-cluster primary dies mid-attack. Stream counters, the in-process attack flag and per-pod counters cover the gap. About 1 s of increments is lost.
sequenceDiagram
    autonumber
    participant R as Risk service
    participant H as Counter primary
    participant H2 as Counter replica
    participant F as Feature store
    Note over H: t = 0, primary dies, m_3 has been in attack mode for 5 min
    R->>H: script for Decide(p_a40)
    Note over R,H: client timeout 4 ms, no answer
    R->>F: stream counters for m_3, about 20 s stale
    R->>R: rules on what arrived, attack mode in process, card not present, STEP_UP
    Note over R: a merchant not yet flagged trips the per-pod attack counter within seconds
    Note over H2: t = 10 s, replica promoted, about 1 s of ZADDs lost
    R->>H2: script for Decide(p_a41)
    H2-->>R: distinct cards on m_3 in 60 s = 37, a little under the truth
    R->>R: velocity rule still fires, DECLINE
```

### D5d. A dispute file is re-sent, and a label arrives before its decision

Labels are idempotent on the source's own id, and an early label waits for its decision instead of being dropped.

```mermaid
%% D5d: label ingestion under duplicates and ordering problems.
sequenceDiagram
    autonumber
    participant N as Processor dispute file
    participant I as Label ingest
    participant D as Label table
    participant L as Decision lake
    N->>I: daily file, 3120 rows
    I->>D: insert by source_event_id (dispute id)
    Note over N: next day the file is re-sent with 3120 old rows and 2980 new ones
    N->>I: re-sent file
    I->>D: 3120 conflicts ignored, 2980 inserted
    Note over I,D: a dispute for p_x whose decision has not reached the lake yet
    I->>D: label parked, join retried hourly for 7 days, then alert
    D->>L: labels joined to decisions by payment_id
```

## D6. Activity / decision flow

The fallback flow is in [solution §5.2](solution.md#5-deep-dives). This is the normal path: how rules and the model combine. Precedence runs top to bottom; within one level the most severe action wins.

```mermaid
%% D6: rule and model precedence inside one decision. Attack responses sit above allowlists, so an allowlisted pair cannot walk past an attack. Pink diamonds are the checks, green boxes the four actions.
flowchart TD
    A[Features and request ready] --> B{Hard block?<br/>blocklist, embargo, tier D}
    B -->|"yes"| DEC[DECLINE]
    B -->|"no"| E{Attack rule hit or<br/>merchant in attack mode?}
    E -->|"yes, per rule"| SU[STEP_UP]
    E -->|"no"| C{Required step missing?<br/>ACH account not validated}
    C -->|"yes, account verification"| SU
    C -->|"no"| D{Allowlisted pair?<br/>customer + payment method}
    D -->|"yes or no, always scored"| F[GBDT p_fraud,<br/>calibrated]
    F --> G{p above the decline<br/>threshold for this amount?}
    G -->|"yes"| DEC
    G -->|"yes, 1 pct step-up slice"| SU
    G -->|"yes, 0.1 pct approve slice"| APP[APPROVE]
    G -->|"no"| H{p in the step-up band?}
    H -->|"yes, buyer present"| SU
    H -->|"yes, allowlisted pair"| APP
    H -->|"yes, keyed or ACH"| REV[REVIEW<br/>deferred capture or debit]
    H -->|"no"| APP
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    class A client
    class F,DEC,SU,APP,REV service
    class B,C,D,E,G,H decision
```

- An allowlist only removes friction (a step-up for a known customer). It never overrides a block, an attack response or a model decline; an account takeover of a long-standing customer is exactly the case it must not wave through.
- Exploration (solution §5.5): the step-up slice estimates `P(fraud | step-up)` with TC40 plus 3DS-outcome labels; the approve slice (no rule hits, tiers A and B, under $50, a monthly dollar cap) is the only estimate of `P(fraud | approve)`. Neither runs for a merchant in attack mode, which never reaches this point anyway.

## D7. Entity relationship

In [solution §3.3](solution.md#33-data-model), with partition keys and TTLs.

## D8. State machines

### D8b. Rule

An emergency rule is born expiring; for its first 24 h a live hit share over 3x its shadow share sends it back to shadow; becoming permanent goes through the normal 7-day shadow.

```mermaid
%% D8b: rule lifecycle. Every enforced rule either expires, is killed, is auto-killed back to shadow in its first 24 h, or is reviewed into a permanent rule.
stateDiagram-v2
    direction LR
    [*] --> Draft
    Draft --> Backtested: backtest run
    Backtested --> Draft: impact too high
    Backtested --> Shadow: approved
    Shadow --> Draft: noisy hit rate
    Shadow --> Enforced: hit rate ok
    Enforced --> Killed: kill switch
    Enforced --> Shadow: auto-kill, first 24 h
    Enforced --> Expired: expiry reached
    Enforced --> Permanent: review approves
    Permanent --> Retired: no fires in 30 days
    Killed --> [*]
    Expired --> [*]
    Retired --> [*]
```

### D8c. Payout hold

A hold is released by a re-score, an analyst, or the end of the return window; nothing else moves it.

```mermaid
%% D8c: payout hold lifecycle. Each transition is one transaction with a matching ledger entry.
stateDiagram-v2
    direction LR
    [*] --> Held: hold placed
    Held --> Released: re-score clears
    Held --> InReview: case opened
    InReview --> Released: analyst clears
    InReview --> Confirmed: fraud confirmed
    Confirmed --> Refunded: buyers refunded
    Confirmed --> Reserve: kept for returns
    Reserve --> Released: window closed
    Released --> [*]
    Refunded --> [*]
```

### D8d. The risk life of one payment

From the 100 ms decision to the label that arrives weeks later. The inline decision never changes; `Rescored` is a new `RESCORE` decision linked by `parent_decision_id`.

```mermaid
%% D8d: one payment's risk lifecycle. Degraded decisions always pass through a re-score before any money leaves.
stateDiagram-v2
    direction LR
    [*] --> Decided: FULL or PARTIAL
    [*] --> Degraded: FALLBACK
    Degraded --> Rescored: deps healthy
    Decided --> Rescored: post-auth pass
    Rescored --> Cleared: score low
    Rescored --> Held: score high
    Held --> Cleared: review clears
    Held --> Voided: fraud, not captured
    Cleared --> Labelled: outcome arrives
    Held --> Labelled: outcome arrives
    Voided --> Labelled: outcome known
    Labelled --> [*]
```

## D9. Deployment / topology

Two regions, three AZs each; merchants are homed in one region so their counters are exact. Region A is drawn in full; region B has the same shape.

```mermaid
%% D9: where each piece runs. Dashed edges cross an AZ or region boundary. No synchronous call on the 100 ms path leaves the region.
flowchart LR
    subgraph RA[Region A, home of half the merchants]
        subgraph AZA[AZ a]
            PA[Orchestrator + risk pods]:::service
            FA[(Feature store,<br/>replica a of 4 shards)]:::critical
            HA[(Redis counter cluster<br/>primary)]:::cache
        end
        subgraph AZB[AZ b]
            PB[Orchestrator + risk pods]:::service
            FB[(Feature store,<br/>replica b of 4 shards)]:::store
            HB[(Counter replica +<br/>dedup cluster primary)]:::cache
        end
        subgraph AZC[AZ c]
            PC[Orchestrator + risk pods]:::service
            HC[(Counter replica)]:::cache
        end
        KA[[Kafka, 3 AZs]]:::queue
        FLA[Flink, re-scorer,<br/>payout risk]:::service
    end
    subgraph RB[Region B, same shape]
        GB[Pods, feature store,<br/>Redis, Kafka, Flink]:::service
    end
    CPL[(Control plane + decision lake<br/>multi-region object storage)]:::store
    PA -->|"AZ-local multi-get"| FA
    PA -.->|"hedge after 6 ms"| FB
    PA -->|"counter script"| HA
    PA -.->|"SET NX, 48 h"| HB
    HA -.->|"async replication"| HB
    HA -.->|"async replication"| HC
    KA -->|"events"| FLA
    FLA -->|"upserts to every replica"| FA
    KA -.->|"mirror decisions, labels"| CPL
    CPL -.->|"bundles, models, table"| PA
    KA -.->|"mirror for merchant re-homing"| GB
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef cache    fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
```

- Each region is sized to carry 2k/s alone. AZ c also has a full set of feature replicas (not drawn) so that any AZ can lose its own and hedge to another. A pod that sees over 30% of its AZ-local reads slower than 6 ms ejects that AZ for 5 s, and the orchestrator routes `Decide` away from a risk AZ whose p99 is out of line. The dedup cluster's replicas are not drawn; it is lossy by design, since the decision of record is the orchestrator's payment row ([`../payments-ledger/`](../payments-ledger/)).
- **Crosses a region:** decisions and labels mirrored to the lake, bundles and models from the control plane, and a merchant's re-homing after a region loss. The counters are per region (exact for merchant keys only); after a re-home they start empty and stream counters stand in for their first hour.

## D10. Scaling / partitioning

Entity keys hash to 4 shards; each decision sends one multi-get per shard. Red is the slow shard, not a hot key: at this scale the problem is tail latency, not load.

```mermaid
%% D10: feature-store partitioning and the per-decision fan-out. One slow shard slows every decision because every decision touches all four.
flowchart LR
    DEC[One decision<br/>~16 entity keys]:::client -->|"hash entity_key"| GRP[Group keys by shard<br/>4 multi-gets]:::service
    GRP -->|"~4 keys"| S1[(Shard 1<br/>30 GB)]:::store
    GRP -->|"~4 keys"| S2[(Shard 2<br/>30 GB)]:::store
    GRP -->|"~4 keys"| S3[(Shard 3, slow<br/>GC or resync)]:::critical
    GRP -->|"~4 keys"| S4[(Shard 4<br/>30 GB)]:::store
    GRP -.->|"hedge after 6 ms"| R3[(Shard 3 replica<br/>other AZ)]:::store
    MEM[In-process tables<br/>merchant, BIN, reputation]:::cache -->|"4 keys, no network"| DEC
    HOT[(Counter cluster<br/>one primary, 8 keys)]:::cache -->|"one script"| DEC
    K[[payment-events<br/>48 partitions by payment_id]]:::queue -->|"keyBy entity"| FLK[Flink]:::service
    FLK -->|"upserts"| S1
    GROW{10x: 16 shards with<br/>entity co-location}:::decision -.->|"keep about 4 calls<br/>per decision"| GRP
    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef cache    fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

- Per shard at design: ~2k multi-gets/s of ~4 keys and ~5k upserts/s, a light load for an in-memory node. The biggest merchant's row would be the hottest key, which is why merchant features live in process. See [`../../concepts/sharding.md`](../../concepts/sharding.md) and [`../../concepts/fan-out-fan-in.md`](../../concepts/fan-out-fan-in.md).

## D11. Failure mode map

Component, then what fails and how far it reaches, then the mitigation. Two trees to stay under 15 nodes each.

### D11a. The 100 ms path

```mermaid
%% D11a: inline path failures. The feature store is red: its tail is the first thing to break the budget.
flowchart TD
    ROOT[Inline decision path]:::client --> FS[Online feature store]:::critical
    ROOT --> HS[Counter cluster]:::cache
    ROOT --> RP[Risk pods]:::service
    ROOT --> CPD[Control plane push]:::service
    FS -->|"fails"| FS1[Slow replica or gray AZ:<br/>every decision touches it]:::decision
    FS1 -->|"mitigation"| FS2[Hedge, latency ejection, deadline,<br/>validated PARTIAL, rules, table]:::service
    HS -->|"fails"| HS1[Primary dies: no sync counters<br/>or budgets, 1 s of writes lost]:::decision
    HS1 -->|"mitigation"| HS2[Stream counters, per-pod attack<br/>counters and slices, promote in 10 s]:::service
    RP -->|"fails"| RP1[Bad deploy: one AZ,<br/>deploys go AZ by AZ]:::decision
    RP1 -->|"mitigation"| RP2[Orchestrator table copy, zone routing,<br/>rollout gate, re-score before payout]:::service
    CPD -->|"fails"| CP1[Bad rule or model:<br/>one segment or all]:::decision
    CP1 -->|"mitigation"| CP2[Backtest, shadow, canary, auto-kill,<br/>kill list outside the control plane]:::service
    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef cache    fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

### D11b. The learning and money path

```mermaid
%% D11b: asynchronous failures. None of them blocks a payment; each one either stales features, delays labels, or delays money. The payout gate reads the payment row, so a Kafka outage cannot hide a fallback.
flowchart TD
    ROOT[Async paths]:::client --> KF[Kafka]:::queue
    ROOT --> FLK[Flink jobs]:::service
    ROOT --> LBL[Label feeds]:::external
    ROOT --> RSC[Re-scorer + payout risk]:::service
    KF -->|"fails"| KF1[Broker or topic down:<br/>snapshots and events stall]:::decision
    KF1 -->|"mitigation"| KF2[Local spool on pods, daily<br/>DECIDED reconciliation]:::service
    FLK -->|"fails"| FL1[Restart or backlog:<br/>stream features lag minutes]:::decision
    FL1 -->|"mitigation"| FL2[Sync counters cover attacks,<br/>lag over 60 s pages]:::service
    LBL -->|"fails"| LB1[File missing or re-sent:<br/>training set incomplete]:::decision
    LB1 -->|"mitigation"| LB2[Dedup on source id,<br/>missing-day alert, park and retry]:::service
    RSC -->|"fails"| RS1[Backlog: fallback payments<br/>unscored at payout cut-off]:::decision
    RS1 -->|"mitigation"| RS2[Payouts read risk_source and<br/>rescored_at from the payment row]:::service
    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

## D12. Rollout / migration

From a legacy rules engine or vendor score to this design, the five phases of [solution §8](solution.md#8-staff-level-notes). Snapshots are logged from day one, so 90 days of skew-free training data exist by phase 5. Each milestone is that phase's rollback point. Durations are estimates.

```mermaid
%% D12: migration phases. Every rollback point is a flag or a pointer, never a data migration.
gantt
    title Migration to inline risk decisioning
    dateFormat  YYYY-MM-DD
    axisFormat  %b %d
    section Phase 1 log-only shadow
    New service scores 100 pct, snapshots on      :p1a, 2026-10-12, 21d
    Rollback point, shadow flag off               :milestone, m1, after p1a, 0d
    section Phase 2 model v0 and rules
    Train v0 on recomputed features               :p2a, after m1, 14d
    Migrate rules, diff against legacy decisions  :p2b, after m1, 21d
    Rollback point, legacy still decides          :milestone, m2, after p2b, 0d
    section Phase 3 enforce by cohort
    Card present and tier A                        :p3a, after m2, 14d
    Online and keyed card                          :p3b, after p3a, 14d
    ACH                                            :p3c, after p3b, 14d
    Rollback point, per-cohort flag                :milestone, m3, after p3c, 0d
    section Phase 4 payout risk
    Holds, reserves and payout delay move over     :p4a, after m3, 21d
    Rollback point, legacy payout rules            :milestone, m4, after p4a, 0d
    section Phase 5 retrain and retire
    Retrain on 90 days of logged snapshots         :p5a, after m4, 14d
    Retire legacy scoring                          :p5b, after p5a, 14d
    Rollback point, legacy kept warm 30 days       :milestone, m5, after p5b, 0d
```

- Phase 3 starts where a wrong decision is cheapest: card present (outside VAMP's card-not-present count) and established merchants. ACH goes last because its mistakes surface up to 60 days later.
