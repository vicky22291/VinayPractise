# Diagrams: Visa-scale payments + ledger + duplicate payment prevention

The D1 to D12 set for [`solution.md`](solution.md). Each diagram appears once in the repo: the ones embedded in `solution.md` are linked from here, not repeated. Colors per root `CLAUDE.md` §3. Red is used only for the hot constrained balance row (the thing that serializes first) and, in D11, for the two failures that can lose or duplicate money.

Legend reminder: 🔵 client / edge, 🟢 stateless compute, 🟣 durable storage, 🟡 cache or losable, 🔷 queue, 🔴 bottleneck or SPOF, ⚪ external, 🩷 decision.

---

## D1. Context (zoom-out)

Our system is the payments API, orchestrator, ledger, and reconciliation. Money actually moves outside it, on the rails.

```mermaid
%% D1: context. Callers send intents; rails move money; files come back for reconciliation.
flowchart LR
    M[Merchants, payroll engine,<br/>wallet apps] -->|"POST payments + Idempotency-Key"| SYS[Payments platform<br/>API, orchestrator, ledger, recon]
    SYS -->|"status, webhooks with event_id"| M
    SYS -->|"tokenize at the edge"| V[Card vault<br/>PCI scope]
    V -->|"token"| SYS
    SYS -.->|"0100 auth, 0400 reversal"| CN[Card network -> issuer]
    CN -.->|"0110, 0410"| SYS
    SYS -.->|"charge with Idempotency-Key"| PSP[PSP]
    SYS -.->|"NACHA file per window"| ACH[ACH operator -> banks]
    CN -.->|"clearing + settlement files, T+1"| SYS
    ACH -.->|"returns R01.., settlement T+1"| SYS
    F[Finance, auditors] -->|"balance as of seq, breaks"| SYS
    R[Risk service] -->|"score, 50 ms"| SYS

    class M,F client
    class SYS,R service
    class V store
    class CN,PSP,ACH external

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

## D2. Data flow (DFD)

What flows, how big, how often. Peak numbers (65 k payments/s).

```mermaid
%% D2: data flow. The synchronous path is three writes and one external call. Everything else hangs off the outbox and the rail files.
flowchart LR
    REQ[payment request<br/>JSON ~600 B, 65 k/s] --> IDEM([idempotency check<br/>insert or read, 3 ms])
    IDEM -->|"replay 1 to 5%"| RESP[response<br/>JSON ~800 B]
    IDEM -->|"new"| PAY([create payment + outbox<br/>1 txn, 1.2 KB, 65 k/s])
    PAY --> HOLD([ledger hold<br/>1 entry, 2 lines, 400 B, 65 k/s])
    HOLD --> RAIL([rail call<br/>ISO 8583 ~1 KB, 65 k/s, 0.1 to 2 s])
    RAIL --> POST([ledger post<br/>1 entry, 3 lines, 560 B, 65 k/s])
    POST --> RESP
    PAY -->|"outbox rows, 200 k/s"| K[[Kafka<br/>200 MB/s]]
    K -->|"events"| WH([webhooks<br/>65 k/s, 3 d retry])
    K -->|"events"| SW([sweeper<br/>non-terminal older than deadline])
    HOLD --> LDB[(ledger lines<br/>520 k/s, 83 MB/s, 1.1 TB/day)]
    POST --> LDB
    LDB -->|"CDC"| ARC[(columnar archive<br/>100 TB/yr compressed)]
    FILES[rail clearing files<br/>~1 GB/day per rail] --> RC([reconciliation<br/>864 M row join, T+1])
    LDB -->|"entries by rail_ref"| RC
    RC -->|"breaks by age"| BRK[(break table + alerts)]

    class REQ,RESP,FILES client
    class IDEM,PAY,HOLD,RAIL,POST,WH,SW,RC service
    class LDB,ARC,BRK store
    class K queue

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
```

## D3. Component architecture

Embedded in [`solution.md` §6](solution.md#6-final-design). Not repeated here.

## D4. Sequence, happy path, one per FR

- **D4a, create + authorize + auto capture (FR1, FR2, FR3):** embedded in [`solution.md` §4.1](solution.md#41-create-a-payment-exactly-once-from-the-callers-point-of-view).
- **D4b, refund (FR2):** below.
- **D4c, reconciliation run (FR5):** below.
- **D4d, status read with read-your-writes (FR6):** below.

```mermaid
%% D4b: partial refund. A child object with its own state machine, its own attempt id, and a reversing entry that never edits the original.
sequenceDiagram
    autonumber
    participant C as Merchant
    participant A as Payments API
    participant P as Payments DB
    participant L as Ledger
    participant R as Rail adapter
    C->>A: POST /payments/p1/refund, key k2, amount 3000
    A->>P: txn: idem(k2) insert, refund r1(created, parent p1), check captured - refunded >= 3000
    A->>L: Post(entry_id = uuid5(r1, refund_hold), lines: pending debit merchant payable 3000, pending credit card receivable 3000)
    L-->>A: ok (available on merchant payable reduced by 3000)
    A->>P: attempt a7(refund, r1) sent
    A->>R: Refund(a7, original rail_ref of p1, 3000)
    R-->>A: ACCEPTED
    A->>P: txn: a7 accepted, r1 = submitted, outbox(refund.created)
    A-->>C: 201 refund r1 pending
    Note over R,L: T+1 clearing file shows the refund
    R->>P: settlement record matched to a7
    A->>L: PostHold(uuid5(r1, refund_hold)) -> posted
    A->>P: r1 = settled, p1 = partially_refunded, outbox(refund.succeeded)
```

```mermaid
%% D4c: one reconciliation run. Matching is by rail_ref, never by day. Every unmatched row gets an age and an owner.
sequenceDiagram
    autonumber
    participant N as Card network SFTP
    participant I as File ingester
    participant S as Settlement records
    participant L as Ledger
    participant J as Matcher (batch)
    participant B as Break table
    N-->>I: clearing file f-2026-09-12 (dedup by file_id)
    I->>S: upsert rows by rail_ref (864 M/day)
    J->>S: read unmatched rows
    J->>L: entries with kind capture or refund, by rail_ref
    J->>J: classify: matched, ledger-only, rail-only, amount mismatch
    J->>L: Post(uuid5(file_id, settlement)) batch: debit bank cash, credit card receivable per matched row
    J->>B: rail-only with attempt reversed -> DUPLICATE, auto refund, page
    J->>B: ledger-only aged > 48 h -> LOST_CAPTURE, page
    J->>B: amount mismatch -> FX or fee check, else break
    J->>B: clearing accounts across ledgers net != 0 -> IN_FLIGHT if < 60 s else break
```

```mermaid
%% D4d: status read. The creating client reads its own write without touching the primary for every read.
sequenceDiagram
    autonumber
    participant C as Client
    participant A as Payments API
    participant RR as Read replica
    participant PR as Shard primary
    C->>A: GET /payments/p1 (header: X-Min-Version 3, from the create response)
    A->>RR: SELECT payment p1
    RR-->>A: version 2 (replica lag)
    A->>PR: SELECT payment p1
    PR-->>A: version 3, status authorized
    A-->>C: 200 authorized, version 3
    Note over A,RR: 99% of reads are satisfied by the replica, the rest fall through
```

## D5. Sequence, failure path

- **D5a, rail timeout, unknown outcome, reversal:** embedded in [`solution.md` §4.2](solution.md#42-drive-the-payment-through-the-rail-with-a-retry-safe-state-machine).
- **D5b, API pod dies mid-flow, another pod takes over from the recovery point:** below.
- **D5c, two concurrent requests with the same key:** below.

```mermaid
%% D5b: pod crash after the rail approved but before the ledger posted. The next attempt resumes from recovery_point, it does not re-authorize.
sequenceDiagram
    autonumber
    participant C as Client
    participant A1 as API pod 1 (dies)
    participant P as Payments DB
    participant N as Rail
    participant L as Ledger
    participant A2 as API pod 2
    C->>A1: POST, key k
    A1->>P: idem(k) in_progress, locked_at t0, payment created, recovery_point = started
    A1->>N: Authorize(a1)
    N-->>A1: APPROVED
    A1->>P: a1 approved, payment authorized, recovery_point = authorized
    Note over A1: crash before ledger post and before response
    C--xA1: timeout
    C->>A2: retry POST, key k (t0 + 8 s)
    A2->>P: idem(k): in_progress, locked_at t0 (8 s old, < 30 s)
    A2-->>C: 409 in use, Retry-After 1
    C->>A2: retry POST, key k (t0 + 35 s)
    A2->>P: idem(k): locked_at stale, take over (UPDATE ... WHERE locked_at = t0)
    A2->>P: read recovery_point = authorized (do NOT call the rail again)
    A2->>L: Post(uuid5(p1, capture))
    L-->>A2: ok
    A2->>P: payment captured, idem(k) done + response
    A2-->>C: 201 captured
```

```mermaid
%% D5c: two pods, same key, same instant. The unique index is the lock. No distributed lock service.
sequenceDiagram
    autonumber
    participant C as Client (double click)
    participant A1 as API pod 1
    participant A2 as API pod 2
    participant P as Payments DB (one shard)
    C->>A1: POST key k
    C->>A2: POST key k
    A1->>P: INSERT idem(k, fp1) ...
    A2->>P: INSERT idem(k, fp1) ...
    P-->>A1: inserted (wins the unique index)
    P-->>A2: unique violation
    A2->>P: SELECT idem(k)
    P-->>A2: in_progress, fingerprint fp1 = fp1
    A2-->>C: 409 in use, Retry-After 1
    A1->>A1: run phases
    A1-->>C: 201 payment p1
    C->>A2: retry key k
    A2->>P: SELECT idem(k) -> done
    A2-->>C: 200 payment p1 (same body)
```

## D6. Activity / decision flow

Embedded in [`solution.md` §4.1](solution.md#41-create-a-payment-exactly-once-from-the-callers-point-of-view) (the idempotency decision). The second hardest branch, the resolver's decision on an unknown outcome, is below.

```mermaid
%% D6b: what the resolver does with an unknown outcome. Per-rail capabilities decide the branch.
flowchart TD
    U[payment in authorizing_unknown<br/>older than 10 s] --> Q{rail has a status query?}
    Q -->|yes, e.g. PSP| QQ[GET by attempt_id]
    QQ --> QR{result?}
    QR -->|approved| OK[advance to authorized]
    QR -->|declined or not found| REL[release hold, declined]
    QR -->|still unknown| RV
    Q -->|no, e.g. ISO 8583| RV{rail supports reversal?}
    RV -->|yes| SEND[send 0400 with original STAN<br/>repeat every 2 s until 0410]
    SEND --> DONE[reversed, hold released,<br/>idem done, webhook failed]
    RV -->|no, e.g. ACH| PEND[keep pending,<br/>resolve by settlement or return, mark for recon]
    OK --> REC[recon still verifies at T+1]
    DONE --> REC
    PEND --> REC

    class U client
    class Q,QR,RV decision
    class QQ,SEND,OK,REL,DONE,PEND,REC service

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

## D7. Entity relationship

Embedded in [`solution.md` §3.3](solution.md#33-data-model).

## D8. State machine

Payment lifecycle embedded in [`solution.md` §4.2](solution.md#42-drive-the-payment-through-the-rail-with-a-retry-safe-state-machine). The idempotency record's own lifecycle is below because the takeover rule is where candidates get it wrong.

```mermaid
%% D8b: idempotency record lifecycle. Takeover is allowed only when the lock is stale, and it resumes, never restarts.
stateDiagram-v2
    [*] --> in_progress : INSERT wins, locked_at = now
    in_progress --> in_progress : retry with fresh lock -> 409
    in_progress --> in_progress : lock stale (> 30 s) -> takeover, resume from recovery_point
    in_progress --> done : final phase committed, response stored
    done --> done : retry -> 200 stored response
    in_progress --> mismatch_rejected : same key, different fingerprint -> 422 (record unchanged)
    mismatch_rejected --> in_progress
    done --> expired : 24 h
    expired --> [*] : row deleted, key reusable as a new payment
```

## D9. Deployment / topology

```mermaid
%% D9: one home region, three AZs, synchronous within region, async to a standby region. Rails are reached from the home region only.
flowchart TB
    subgraph R1[Home region for tenant T]
        direction LR
        subgraph AZ1[AZ 1]
            A1[API + orchestrator pods]
            P1[(payments shard primary)]
            L1[(ledger shard primary)]
            W1[ledger writer, owner epoch 8]
        end
        subgraph AZ2[AZ 2]
            A2[API + orchestrator pods]
            P2[(payments sync standby)]
            L2[(ledger sync standby)]
        end
        subgraph AZ3[AZ 3]
            A3[API + orchestrator pods]
            P3[(payments sync standby)]
            L3[(ledger sync standby)]
        end
        K[[Kafka RF 3 across AZs]]
        E[(etcd, shard ownership + epochs)]
    end
    subgraph R2[Standby region]
        PS[(payments async standby, lag ~1 s)]
        LS[(ledger async standby, lag ~1 s)]
        AS[API pods, cold]
    end
    P1 -->|"WAL, sync ANY 1"| P2
    P1 -->|"WAL, sync ANY 1"| P3
    L1 -->|"WAL, sync ANY 1"| L2
    L1 -->|"WAL, sync ANY 1"| L3
    P1 -.->|"WAL, async"| PS
    L1 -.->|"WAL, async"| LS
    W1 -->|"lease, epoch"| E
    RAIL[Card network, PSP, ACH] -.->|"from home region only"| A1

    class A1,A2,A3,W1,AS service
    class P1,P2,P3,L1,L2,L3,PS,LS,E store
    class K queue
    class RAIL external

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

## D10. Scaling / partitioning

The hot-account diagram is embedded in [`solution.md` §5.1](solution.md#51-one-merchant-is-5-of-volume-its-account-gets-thousands-of-updates-a-second-what-breaks). The shard map itself is below.

```mermaid
%% D10b: two independent shard maps. Payments by tenant, ledger by ledger_id. A big merchant is one ledger and gets a single-writer batch.
flowchart LR
    REQ[payment for tenant T, merchant M] -->|"hash(tenant_id) -> 4096 vshards -> 20 shard sets"| PS[(payments shard 7)]
    REQ -->|"ledger_id of M -> 4096 vshards -> 40 shard sets"| LS[(ledger shard 23)]
    LS --> N{hot ledger?<br/>top 5% by entries/s}
    N -->|"no: 95% of ledgers"| DIRECT[direct Post per entry<br/>5 k txn/s per primary]
    N -->|"yes"| BATCH[single-writer batch<br/>4 k entries per commit, 100 k/s]
    BATCH --> LS
    DIRECT --> LS
    LS --> CL[clearing account per ledger<br/>cross-ledger money goes through here]
    CL -.->|"invariant: sum over all ledgers = 0"| REC[reconciliation]

    class REQ client
    class N decision
    class DIRECT,BATCH,REC service
    class PS,LS,CL store

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

## D11. Failure mode map

```mermaid
%% D11: component -> failure -> blast radius -> mitigation. Red marks the two failures that can lose or duplicate money without the mitigation.
flowchart TD
    API[API pod dies mid-flow] -->|"blast: that request"| M1[recovery_point resume, 409 then takeover after 30 s]
    PDB[Payments shard primary dies] -->|"blast: 1 tenant group, 10 to 30 s"| M2[sync standby promoted, epoch bump, retries by key]
    LDB[Ledger shard primary dies after commit] -->|"blast: unknown commit"| M3[retry Post with same entry_id, ON CONFLICT returns existing]
    RAIL[Rail timeout] -->|"blast: possible double charge"| M4[UNKNOWN state, same attempt_id retry, 0400 reversal, recon T+1]
    HOT[Hot constrained balance row] -->|"blast: one merchant's p99, then the shard"| M5[unconstrained = no row, constrained = single-writer batch]
    KAF[Kafka down] -->|"blast: webhooks, sweeps lag"| M6[outbox accumulates, no money impact]
    REG[Region dark] -->|"blast: ~1 s acked writes"| M7[async standby promoted, sweeper reverses unknowns, recon fills gaps]
    BUG[Deploy posts unbalanced entries] -->|"blast: the books"| M8[sum = 0 check rejects at commit, invariant job 5 min, canary 1%]
    FILE[Rail file late or duplicated] -->|"blast: false breaks"| M9[dedup by file_id, match by rail_ref, 48 h aging]
    SPLIT[Two ledger writers think they own a shard] -->|"blast: divergent sequence"| M10[lease + epoch fencing at the DB, old epoch rejected]

    class RAIL,HOT critical
    class API,PDB,LDB,KAF,REG,BUG,FILE,SPLIT service
    class M1,M2,M3,M4,M5,M6,M7,M8,M9,M10 store

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
```

## D12. Rollout / migration

Applicable: most companies arrive here from a `balance` column and a `transactions` table with no idempotency. Each phase has a rollback point that is a flag flip.

```mermaid
%% D12: from balance-column system to this design. Rollback at each phase is a flag, the old table is dropped last.
gantt
    title Migration from balance column to idempotent ledger
    dateFormat  YYYY-MM-DD
    axisFormat  %b
    section Phase 1 idempotency in front
    Key layer in shadow mode, log would-be duplicates      :p1, 2026-10-01, 30d
    Enforce keys per tenant behind flag                    :p1b, after p1, 30d
    section Phase 2 dual write ledger
    Emit journal entries from old write path               :p2, 2026-11-01, 45d
    Backfill history, run invariants, compare balances daily :p2b, after p2, 30d
    section Phase 3 reads
    Balance API from ledger per tenant flag                :p3, 2027-01-15, 30d
    section Phase 4 writes
    New orchestrator per tenant flag, keep old dual write  :p4, 2027-02-15, 60d
    Finance signs a full quarter close from ledger         :p4b, after p4, 30d
    section Phase 5 cleanup
    Stop old writes, archive old table                     :p5, after p4b, 30d
```

Rollback points: Phase 1, turn enforcement off (shadow keeps logging). Phase 2, stop emitting entries; nothing reads them yet. Phase 3, flip reads back to the old column per tenant. Phase 4, flip writes back per tenant; the old table is still being written so no backfill. Phase 5 is the only irreversible step and happens after a quarter close.
