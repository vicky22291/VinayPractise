# Diagrams: QuickBooks multi-tenant ledger

> One-line answer: twelve views of one design. A posting engine turns each business transaction into a balanced journal entry and writes it, its insert-only lines and its per-month and per-day balance deltas (made from the lines by a statement-level trigger) in one transaction on the company's shard; a manual post is acknowledged once the cross-region replica has flushed it. Reports are prefix sums over those delta rows on the shard primary. A bulk lane batches imports so a huge tenant's hot balance row is touched once per batch. A verifier, a shard mover and a CDC copy in a columnar store sit beside the write path, never on it. The ledger shard primary, with its hot balance row, is the one red box.

The D1 to D12 set from `hld/CLAUDE.md` §4, each with a one-line caption. A diagram already in [`solution.md`](solution.md) gets a heading, a caption and a link, never a second copy. Acronyms: CDC (change data capture), GL (general ledger), P&L (profit and loss), AR (accounts receivable), AP (accounts payable), FX (foreign exchange), AZ (availability zone), LSN (log sequence number), WAL (write-ahead log), OAuth (open authorization), KMS (key management service), WORM (write once, read many), ETL (extract, transform, load).

| # | Diagram | Where it lives |
|---|---|---|
| D1 | Context | below |
| D2 | Data flow | below |
| D3 | Component architecture (final design) | [solution §6](solution.md#6-final-design-and-the-six-core-flows) |
| D4 | Happy path per FR | FR1 post: [solution §4.1](solution.md#41-post-a-business-transaction-as-one-balanced-journal-entry). FR2 edit: [solution §4.2](solution.md#42-keep-history-immutable-edits-and-voids-post-reversals). FR3 closed period: [solution §4.3](solution.md#43-respect-closed-periods). FR4 report: [solution §4.4](solution.md#44-report-fast-over-the-whole-history). Bulk import and a foreign-currency invoice: below |
| D5 | Failure paths | Duplicate post, stale edit, batcher crash, close racing a post: below. Primary failover: [solution §10.4](solution.md#104-failure-timeline). Shard move: [solution §5.5](solution.md#55-a-shard-dies-or-a-company-must-move-how-do-you-keep-9995-and-move-it-with-zero-downtime) |
| D6 | Decision flow | Posting engine validation and the as-of read plan: below. Report planner: [solution §5.2](solution.md#52-balance-sheet-as-of-any-date-in-10-years-under-1-s-and-it-shows-the-post-i-just-made) |
| D7 | Entity relationship | [solution §3.3](solution.md#33-data-model) |
| D8 | State machines | Business transaction, accounting period, import item, company placement: below |
| D9 | Deployment / topology | below |
| D10 | Scaling / partitioning | Shard map: below. Hot row zoom-in: [solution §5.3](solution.md#53-one-company-syncs-1-m-shopify-orders-a-month-into-the-same-two-accounts-where-is-the-hot-spot) |
| D11 | Failure mode map | below, two trees |
| D12 | Rollout / migration | below |

## D1. Context (zoom-out)

Our system as one box: people and apps write business transactions, Intuit products and third parties feed it, accountants and auditors read it.

```mermaid
%% D1: the ledger as one box with every external actor. Every arrow into the ledger is scoped to one company by an OAuth token, except the firm view, scoped to the firm's grants.
flowchart LR
    OWN[Owners and bookkeepers]:::client -->|"invoices, bills, edits,<br/>closing date, reports"| SYS[QuickBooks ledger<br/>posting engine, shards,<br/>reports, verifier]:::service
    ACC[Accountants and firms]:::client -->|"adjusting entries,<br/>firm dashboard"| SYS
    APPS[Third-party apps<br/>Shopify connectors, add-ons]:::external -->|"API writes, OAuth,<br/>throttled per company"| SYS
    SRC[Intuit sources<br/>bank feeds, Payments, Payroll]:::external -->|"bank lines, payouts,<br/>payroll journals"| SYS
    FXP[Exchange-rate provider]:::external -->|"rates, every 4 hours"| SYS
    IDP[Intuit identity]:::external -->|"tokens, roles"| SYS
    SYS -->|"CDC, eventual"| ANA[Intuit analytics<br/>and model features]:::external
    SYS -->|"reports, audit exports,<br/>close snapshots"| AUD[Auditors, lenders,<br/>tax preparers]:::external
    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

## D2. Data flow (DFD)

Inputs to outputs with format, size and rate. Processes are rounded, stores are cylinders. Numbers from solution §2.

```mermaid
%% D2: data flow. Rates are fleet-wide unless marked per cluster. Estimates as in solution section 2.
flowchart LR
    APP[Apps and API clients]:::client -->|"post or edit, JSON ~2 KB,<br/>~900/s avg, ~10k/s peak"| PE(Posting engine):::service
    SRC[Feeds and bulk files]:::external -->|"bank lines and orders, JSON ~1 KB,<br/>bulk 1k/s per company max"| IMP(Import service<br/>and batcher):::service
    IMP -->|"one post, or 500 per txn"| PE
    PE -->|"~14 row writes per txn, ~2 KB stored,<br/>~160 commits/s per cluster peak"| DB[(Ledger shards<br/>58 TB/year primary)]:::store
    DB -->|"balance rows ~80 B, ~3k per report,<br/>~2.5k reports/s peak"| RS(Report service):::service
    RS -->|"report JSON ~10 to 50 KB"| APP
    DB -->|"row changes ~300 B,<br/>~13k/s avg, ~140k/s peak"| K[[Kafka CDC<br/>~4 MB/s avg]]:::queue
    K -->|"lines and balances,<br/>~2.5 TB/year compressed"| OL[(Columnar store)]:::store
    K -->|"each committed txn"| VER(Verifier):::service
    VER -->|"one root per company-day,<br/>~4 M/day × 32 B"| ARC[(WORM archive)]:::store
    K -->|"audit events ~200 B"| ARC
    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

## D3. Component architecture

The final design, 14 nodes, the ledger shard primary in red: [solution §6](solution.md#6-final-design-and-the-six-core-flows).

## D4. Happy paths

The four FR flows are in solution §4.1 to §4.4 (links in the table above). Two more flows that the FR walkthroughs do not cover:

### D4e. A bulk import batch of 500 orders

One batch of a 12 M-order migration. The hot balance rows are touched once, at the end.

```mermaid
%% D4e: one bulk batch. Duplicates drop out at the claim, deltas are summed only over rows actually inserted, balance rows are written last.
sequenceDiagram
    autonumber
    participant J as Bulk job store
    participant B as Batcher, lease on c_9
    participant P as Posting engine library
    participant S as Ledger shard
    B->>J: take lease on c_9 job, next 500 items
    J-->>B: items 20,001 to 20,500
    B->>P: validate 500 in memory, rules, balance, closing date
    P-->>B: 497 valid, 3 to the review list with reasons
    B->>S: BEGIN, company fence shared, read settings and placement
    B->>S: INSERT TXN for 497 source_refs ON CONFLICT DO NOTHING RETURNING
    S-->>B: 497 new, 0 duplicates
    B->>S: multi-row INSERT versions and entries for the 497 only
    B->>S: INSERT ~2,500 lines, check trigger, balance trigger upserts ~6 rows sorted
    S-->>B: COMMIT pipelined, ~80 ms, hot rows held ~2 ms
    B->>J: checkpoint item 20,500
    Note over B,S: admission keeps c_9 at 1k orders/s, the hot row sees ~2 updates/s
```

### D4f. A euro invoice, then its payment at a new rate

Home currency USD. The engine owns the rounding cent and the realized gain.

```mermaid
%% D4f: multi-currency. Lines carry euros and dollars. Dollars must sum to zero, so the residual goes to a home-only line.
sequenceDiagram
    autonumber
    participant A as App
    participant P as Posting engine
    participant R as Rate table
    participant S as Ledger shard
    A->>P: invoice 100.00 EUR, items 33.33, 33.33, 33.34
    P->>R: rate EUR to USD at txn_date
    R-->>P: 1.0877, rate id fx_8812
    P->>P: AR 108.77, items 36.25 + 36.25 + 36.26 = 108.76
    P->>P: residual 0.01, home-only line to exchange gain or loss
    P->>S: entry with rate fx_8812, 5 lines, EUR sum 0, USD sum 0
    S-->>P: COMMIT
    A->>P: payment 100.00 EUR, rate 1.1000
    P->>P: bank +110.00, AR -108.77, realized gain -1.23
    P->>S: entry, 3 lines, EUR sum 0, USD sum 0
    S-->>P: COMMIT
```

## D5. Failure paths

### D5a. The client retries a post whose commit landed

The response was lost after the commit. The retry returns the stored answer; no second invoice.

```mermaid
%% D5a: idempotency by claim. The first INSERT of the transaction is the request id, so a retry collides instead of re-posting.
sequenceDiagram
    autonumber
    participant A as App
    participant P1 as Engine pod 1
    participant P2 as Engine pod 2
    participant S as Ledger shard
    A->>P1: post, request_id r_91
    P1->>S: BEGIN, INSERT IDEMPOTENCY r_91, entry, lines, balances
    S-->>P1: COMMIT ok
    Note over P1: pod 1 dies before answering
    A->>A: timeout after 5 s, retry same r_91
    A->>P2: post, request_id r_91
    P2->>S: INSERT IDEMPOTENCY r_91 ON CONFLICT DO NOTHING
    S-->>P2: 0 rows, key exists
    P2->>S: SELECT stored response for r_91
    S-->>P2: t_5501, sync_token 0, same body hash
    P2-->>A: 201, the original result, as_of_commit is the current flush LSN
```

### D5b. Two apps edit the same invoice

A sync app holds an old copy. The second writer gets a conflict instead of silently erasing the first edit.

```mermaid
%% D5b: optimistic concurrency on the TXN header. The row lock serializes the two edits and the token comparison rejects the stale one.
sequenceDiagram
    autonumber
    participant U as Bookkeeper UI
    participant X as Sync app
    participant P as Posting engine
    participant S as Ledger shard
    U->>P: edit t_5501, sync_token 0, amount 1,200
    X->>P: edit t_5501, sync_token 0, memo changed
    P->>S: txn A, SELECT TXN t_5501 FOR UPDATE
    P->>S: txn B, SELECT TXN t_5501 FOR UPDATE, waits
    S-->>P: txn A sees token 0, writes v2, token 1, COMMIT
    S-->>P: txn B gets the row, sees token 1, not 0
    P->>S: txn B ROLLBACK
    P-->>U: 200, version 2, sync_token 1
    P-->>X: 409 STALE, current token 1
    X->>P: re-read t_5501, re-apply memo, sync_token 1
    P-->>X: 200, version 3, sync_token 2
```

### D5c. The batcher dies between the batch commit and its checkpoint

The batch committed; the checkpoint did not. The next lease holder replays the batch, and the claim makes it a no-op.

```mermaid
%% D5c: crash after COMMIT, before the checkpoint. Replay is safe because source_ref is unique forever and deltas follow only inserted rows.
sequenceDiagram
    autonumber
    participant J as Bulk job store
    participant B1 as Batcher 1
    participant B2 as Batcher 2
    participant S as Ledger shard
    B1->>S: batch 41, items 20,001 to 20,500, COMMIT ok
    Note over B1: dies before the checkpoint write
    Note over J: lease on c_9 expires after 30 s
    B2->>J: take lease, last checkpoint item 20,000
    B2->>S: BEGIN, claim 500 source_refs ON CONFLICT DO NOTHING RETURNING
    S-->>B2: 0 new rows
    B2->>S: no lines, no balance deltas, COMMIT
    B2->>J: checkpoint item 20,500, continue with batch 42
    Note over B2,S: inserting lines for the whole input instead of the RETURNING set would double count, the verifier would page
```

### D5d. The closing date is set while a post is in flight

The close waits for the post, and a post that arrives during the close queues behind it, so no post can land in a period after it was closed. The fence is an advisory lock on the company: shared for posts, exclusive for the close.

```mermaid
%% D5d: the company fence. Shared advisory lock in posts, exclusive in the close. The queue is fair, so T2 waits behind C instead of starving it.
sequenceDiagram
    autonumber
    participant T1 as Post Dec 30
    participant C as Close through Dec 31
    participant T2 as Post Dec 29
    participant F as Company fence
    T1->>F: advisory lock shared, then read close_date Nov 30
    C->>F: advisory lock exclusive, waits for T1
    T2->>F: advisory lock shared, queues behind C
    T1->>T1: Dec 30 is open, insert entry and lines
    T1->>F: COMMIT, shared lock released
    F-->>C: exclusive granted
    C->>C: SET close_date Dec 31, close snapshot includes T1
    C->>F: COMMIT, exclusive released
    F-->>T2: shared granted, reads close_date Dec 31
    T2-->>T2: Dec 29 is closed, 409 CLOSED_PERIOD unless override
```

## D6. Activity / decision flow

### D6a. Posting engine: from request to commit

The branching inside the hardest component. Pink diamonds are decisions.

```mermaid
%% D6a: the posting engine's checks, in the order they run. Everything after the claim is inside one transaction, so any refusal rolls back the claim too.
flowchart TD
    A[Post or edit request] --> B{request_id<br/>already claimed?}
    B -->|"yes"| R1[Return stored response]
    B -->|"no, claim it,<br/>fence shared"| C{Company placement<br/>ACTIVE?}
    C -->|"FROZEN or MOVED"| R2[Retryable MOVING,<br/>router refreshes]
    C -->|"yes"| D{Edit with a<br/>matching sync_token?}
    D -->|"stale"| R3[409 STALE]
    D -->|"create, or match"| E{Any affected date on or<br/>before the closing date?}
    E -->|"yes, no override"| R4[409 CLOSED_PERIOD,<br/>suggest first open day]
    E -->|"no, or override ok"| F[Build lines, convert,<br/>round half-even]
    F --> G{Residual within<br/>half a cent per line?}
    G -->|"no"| R5[400 unbalanced input]
    G -->|"yes"| H[Add home-only rounding line,<br/>write header, audit, entries]
    H -->|"lines, check set IMMEDIATE"| I{Check trigger:<br/>every entry sums to zero?}
    I -->|"yes"| OK[Balance trigger upserts,<br/>COMMIT, remote flush, respond]
    I -->|"no"| R6[Abort, page P1]

    class A client
    class B,C,D,E,G,I decision
    class F,H,OK service
    class R1,R2,R3,R4,R5,R6 service

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

### D6b. Which rows a balance sheet as of a date reads

How "as of June 15, 2019, fiscal year from January" decomposes. Every box is a range scan of delta rows; none of them grows with the company's volume.

```mermaid
%% D6b: the as-of read plan. Balance-sheet accounts are cumulative. income and expense split into retained earnings and net income at the fiscal-year start.
flowchart TD
    Q[Balance sheet as of<br/>2019-06-15] --> T{Account type?}
    T -->|"asset, liability, equity"| BS1[Month rows from the first<br/>month through May 2019]
    T -->|"income, expense"| PL{Before the fiscal<br/>year start?}
    BS1 -->|"plus"| BS2[Day rows June 1 to 15,<br/>or June minus 16 to 30]
    PL -->|"yes"| RE[Retained earnings:<br/>all rows before Jan 2019]
    PL -->|"no"| NI[Net income: months Jan to May<br/>plus days June 1 to 15]
    BS2 --> SUM[Group by account,<br/>one snapshot]
    RE --> SUM
    NI --> SUM
    SUM -->|"assets = liabilities + equity"| OUT[Report rows, ~5 ms<br/>for a median company]

    class Q client
    class T,PL decision
    class BS1,BS2,RE,NI,SUM service
    class OUT client

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

## D7. Entity relationship

In [solution §3.3](solution.md#33-data-model), with the access patterns and the partition key (`company_id`, first column of every primary key).

## D8. State machines

### D8a. Business transaction

A transaction moves through versions; its lines never change. "Locked" is not stored: it is derived from the closing date.

```mermaid
%% D8a: one business transaction. Each arrow is one posting transaction that writes a version, a reversal, or both.
stateDiagram-v2
    direction LR
    [*] --> Posted: create, v1
    Posted --> Posted: edit, reversal + vN
    Posted --> Locked: close date passes
    Locked --> Locked: override edit, audited
    Locked --> Posted: close date moved back
    Posted --> Voided: void, reversal only
    Locked --> Voided: override void
    Voided --> [*]
```

### D8b. Accounting period

What the closing date does to a month. Overrides do not reopen the period; they leave an audited exception.

```mermaid
%% D8b: one accounting period. The close snapshot is taken on the transition to Closed. exceptions are diffed against it.
stateDiagram-v2
    direction LR
    [*] --> Open
    Open --> Closed: close date set
    Closed --> Closed: override post, logged
    Closed --> Open: close date moved back
    Closed --> Filed: taxes filed
    Filed --> Filed: override, flagged
    Filed --> [*]
```

### D8c. Import item

A bank line or an order from arrival to the ledger.

```mermaid
%% D8c: one import item. The ledger is touched only on the transition to Posted. Duplicate is decided by the unique source_ref.
stateDiagram-v2
    direction LR
    [*] --> Received
    Received --> Duplicate: source_ref exists
    Received --> InReview: needs a human
    Received --> Posted: rule or bulk lane
    InReview --> Posted: accepted
    InReview --> Excluded: user excludes
    InReview --> ClosedPeriod: date is closed
    ClosedPeriod --> Posted: re-dated or override
    Posted --> [*]
    Duplicate --> [*]
    Excluded --> [*]
```

### D8d. Company placement during a shard move

The fence that makes a move safe. Only `Frozen` blocks writes, for ~1 to 3 s.

```mermaid
%% D8d: placement of one company. Abort is possible until the flip, and is always a drop of the target copy.
stateDiagram-v2
    direction LR
    [*] --> Active
    Active --> Copying: move starts
    Copying --> CatchingUp: snapshot loaded
    CatchingUp --> Frozen: lag under 1 s
    Frozen --> Moved: directory flipped
    Frozen --> Active: abort, drop target
    CatchingUp --> Active: abort, drop target
    Moved --> Cleaned: after 7 days
    Cleaned --> [*]
```

## D9. Deployment / topology

Where each piece runs. Synchronous replication stays inside the region. The cross-region replica is streamed asynchronously, but a manual or API post is acknowledged only after it has flushed, a wait that happens after `COMMIT`, outside every lock. Kafka and a CDC connector run in both regions; after a promotion, CDC resumes from region B on a new timeline.

```mermaid
%% D9: one cluster's placement plus the shared services. Dashed edges cross a region boundary. No lock is ever held across one.
flowchart LR
    subgraph RA[Region A, home]
        subgraph AZ1[AZ 1]
            SV1[Gateway, engine,<br/>report pods]
            P1[(Primary)]
        end
        subgraph AZ2[AZ 2]
            SV2[Gateway, engine,<br/>report pods]
            S2[(Sync standby 1<br/>heavy reports)]
        end
        subgraph AZ3[AZ 3]
            SV3[Gateway, engine,<br/>report pods]
            S3[(Sync standby 2)]
        end
        K[[Kafka + CDC connector,<br/>3 AZs]]
        OL[(Columnar store)]
        OBJ[(Object storage,<br/>WORM archive)]
    end
    subgraph RB[Region B, recovery]
        RP[(Async replica<br/>verifier recompute)]
        SVB[Warm pods]
        KB[[Kafka + CDC connector,<br/>warm]]
        OBJB[(Object storage copy)]
    end
    SV1 -->|"posts, reads"| P1
    P1 -->|"WAL, ANY 1 sync"| S2
    P1 -->|"WAL, ANY 1 sync"| S3
    P1 -.->|"WAL stream"| RP
    RP -.->|"flush position,<br/>manual acks wait"| SV1
    P1 -->|"logical decoding"| K
    K -->|"CDC"| OL
    K -->|"audit, roots"| OBJ
    K -.->|"topic mirror"| KB
    RP -.->|"after promotion,<br/>timeline + LSN"| KB
    OBJ -.->|"cross-region copy"| OBJB

    class SV1,SV2,SV3,SVB service
    class P1 critical
    class S2,S3,RP,OL,OBJ,OBJB store
    class K,KB queue

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
```

## D10. Scaling / partitioning

Directory placement: companies map to 1,024 logical shards, logical shards to 64 clusters. The biggest company is small as a tenant; its hot row is the red part. Zoom-in on the row and the batcher: [solution §5.3](solution.md#53-one-company-syncs-1-m-shopify-orders-a-month-into-the-same-two-accounts-where-is-the-hot-spot).

```mermaid
%% D10: placement. A company moves alone by changing one directory row. The red node is the single balance row that a non-batched bulk path would saturate.
flowchart LR
    C1[~8 M companies<br/>median 600 txns/month] -->|"company_id lookup"| DIR[(Shard directory<br/>company to logical shard,<br/>epoch, state)]
    CB[Largest company<br/>1 M txns/month] -->|"company_id lookup"| DIR
    DIR -->|"~7.8k companies each"| LS[1,024 logical shards]
    LS -->|"16 per cluster"| CL[64 clusters<br/>~125k companies,<br/>~9 TB at year 10]
    CL -->|"cluster 26 holds"| BIG[Largest company:<br/>~300 GB over 10 years,<br/>~3% of its cluster]
    BIG -->|"every order hits"| HOT[Sales income month row<br/>~500 updates/s ceiling]
    FIX1[Bulk batcher:<br/>1 update per 500 orders] -->|"protects"| HOT
    FIX2[Shard mover:<br/>own cluster if over 10%] -->|"relocates"| BIG

    class C1,CB client
    class DIR cache
    class LS,CL,BIG store
    class HOT critical
    class FIX1,FIX2 service

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef cache    fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
```

## D11. Failure mode map

### D11a. The write path

Component, what fails, blast radius, mitigation. The shard primary is red: it is the one stateful dependency every post needs.

```mermaid
%% D11a: write path failures. Blast radius is counted in companies.
flowchart TD
    W[Write path] --> E[Posting engine pod dies]
    W --> P[Shard primary dies]
    W --> H[Hot row under a bulk path]
    W --> R[Bad posting-rule release]
    E -->|"blast: in-flight requests only"| E2[Client retries,<br/>same request_id]
    P -->|"blast: ~125k companies,<br/>~15 to 30 s"| P2[Promote sync standby,<br/>503 + Retry-After, no data lost]
    H -->|"blast: one company's<br/>posts to that account"| H2[Batcher, admission,<br/>lock_timeout 200 ms]
    R -->|"blast: every company<br/>on the new version"| R2[Shadow diff 24 h,<br/>cohorts, trigger, verifier]

    class W client
    class E,H,R service
    class P critical
    class E2,P2,H2,R2 service

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
```

### D11b. Read, async and control paths

None of these can stop a post. They make data stale, slow or unverified, and each says so.

```mermaid
%% D11b: failures off the write path. The common pattern: posting continues, and the stale or degraded thing is labelled or paged.
flowchart TD
    A[Off the write path] --> K[Kafka or CDC stalls]
    A --> O[Columnar store down]
    A --> V[Verifier down]
    A --> D[Directory store down]
    A --> M[Shard move stuck]
    A --> R[Cross-region replica slow]
    K -->|"blast: firm views stale,<br/>verifier behind"| K2[Watermark banner,<br/>slot capped at 100 GB, page]
    O -->|"blast: firm dashboards"| O2[Drill-down still hits<br/>each client's shard]
    V -->|"blast: detection delayed"| V2[Replays from the slot,<br/>monthly recompute catches up]
    D -->|"blast: moves only"| D2[Pods route from<br/>in-process copies]
    M -->|"blast: one company,<br/>writes paused"| M2[Freeze timeout 10 s,<br/>abort, drop target]
    R -->|"blast: manual post<br/>acks slower"| R2[Wait capped at 1 s, then<br/>durability region, over 5 s<br/>lag: local-only acks, page]

    class A client
    class K,O,V,D,M,R service
    class K2,O2,V2,D2,M2,R2 service

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
```

## D12. Rollout / migration

From an existing ledger whose reports scan lines (or read nightly snapshot tables) and whose edits update lines in place. Lines stay the source of truth throughout, so every rollback is "stop using the new derived thing".

```mermaid
%% D12: six phases, one rollback point each. No phase needs a coordinated deploy or downtime.
gantt
    title Migration to delta rows, reversals and directory sharding
    dateFormat YYYY-MM-DD
    axisFormat %b %Y
    section 1 Balance rows
    Add PERIOD_BALANCE and the balance trigger, off :p1, 2027-01-04, 6w
    Per company, fence, backfill, flag on, recompute :p1b, after p1, 4w
    Rollback, turn the flag off                     :milestone, m1, after p1b, 0d
    section 2 Shadow reads
    Both report paths on 1 percent, diff totals     :p2, after p1b, 4w
    Verifier live on every shard                    :p2b, after p1b, 4w
    Rollback, stop the shadow reads                 :milestone, m2, after p2, 0d
    section 3 Flip reads
    Reports read delta rows, cohort by cohort       :p3, after p2, 6w
    Rollback, flag back to the old read path        :milestone, m3, after p3, 0d
    section 4 Immutability
    Edits become reversal plus version, per type    :p4, after p3, 8w
    Revoke UPDATE and DELETE, balance check trigger :p4b, after p4, 2w
    Rollback, re-grant                              :milestone, m4, after p4b, 0d
    section 5 Directory
    Load current placement as a no-op directory     :p5, after p3, 3w
    First moves with the shard mover                :p5b, after p5, 4w
    Rollback, move the company back                 :milestone, m5, after p5b, 0d
    section 6 CDC copy
    CDC into the columnar store, retire nightly ETL :p6, after p5b, 6w
    Rollback, nightly ETL kept until sign-off       :milestone, m6, after p6, 0d
```
