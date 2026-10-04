# Diagrams: payroll run for ~1M small businesses

> One-line answer: twelve views of one design. Approval freezes a snapshot before a cut-off derived backwards from the bank's ACH (automated clearing house) windows. A saga fans the snapshot out to pure calc workers. Balanced, deterministically keyed instructions sit in a tenant-sharded payroll DB until a file builder claims whole runs, under each run's lock, into NACHA files, registers each file on a primary key that an orphan sweep can tombstone first, and a bank gateway uploads it at most once to one of two ODFIs. Returns come back as files, are matched by our own `ach_ref`, and are repaired forward. The file builder and bank gateway at the ODFI (originating bank) cut-off is the one red box.

The D1 to D12 set from `hld/CLAUDE.md` §4, each with a one-line caption. A diagram already in [`solution.md`](solution.md) gets a heading, a caption and a link, never a second copy. Acronyms: ODFI and RDFI (originating and receiving depository financial institution), FedACH (the Federal Reserve's ACH operator), EFTPS (Electronic Federal Tax Payment System), NOC (notification of change), WORM (write once, read many), AZ (availability zone), RPO (recovery point objective), EIN (employer identification number), PT and ET (Pacific and Eastern time).

| # | Diagram | Where it lives |
|---|---|---|
| D1 | Context | below |
| D2 | Data flow | below, plus D2b, the anatomy of one NACHA file |
| D3 | Component architecture (final design) | [solution §6](solution.md#6-final-design-and-the-six-core-flows) |
| D4 | Happy path per FR | FR1 approve: [solution §4.1](solution.md#41-schedule-and-approve-freeze-a-snapshot-before-the-cut-off). FR2 calc: [solution §4.2](solution.md#42-calculate-a-pure-function-of-the-snapshot). FR3 night drop: [solution §4.3](solution.md#43-move-money-exactly-once-instructions-then-files-then-the-bank); tax deposit: below. FR4 R01 return: [solution §4.4](solution.md#44-retry-and-repair-forward-only-corrections); R03 re-issue: below |
| D5 | Failure paths | Upload timeout: [solution Flow 3](solution.md#flow-3-the-upload-of-file-c-times-out-at-605-pm-pt). Shard failover at 4:59:50 PM: [solution §10.4](solution.md#104-failure-timeline). Below: a paused file builder loses to a tombstone, a calc worker dies mid-chunk, EFTPS rejects a deposit |
| D6 | Decision flow | Upload outcome: [solution §5.3](solution.md#53-the-upload-timed-out-did-the-bank-get-it-exactly-once-money-movement). Approval admission: below |
| D7 | Entity relationship | [solution §3.3](solution.md#33-data-model) |
| D8 | State machines | Pay run: [solution §4.4](solution.md#44-retry-and-repair-forward-only-corrections). Instruction and NACHA file: below |
| D9 | Deployment / topology | below |
| D10 | Scaling / partitioning | below |
| D11 | Failure mode map | below, two trees |
| D12 | Rollout / migration | below |

## D1. Context (zoom-out)

The payroll engine as one box: admins and employees in, money and records out through banks, agencies and the ledger.

```mermaid
%% D1: the system as one box with every external actor and what flows on each edge.
flowchart LR
    ADM[Admins, accountants,<br/>auto-payroll]:::client -->|"schedules, inputs,<br/>approve, corrections"| SYS[Payroll engine<br/>approve, calc, money movement,<br/>returns and repair]:::service
    SYS -->|"preview, debit amount,<br/>alerts, return notices"| ADM
    EMP[Employees]:::client -->|"bank account, W-4"| SYS
    SYS -->|"pay stubs"| EMP
    SYS -->|"NACHA files, once each"| BANK[Two ODFIs, FedACH,<br/>employee and employer banks]:::external
    BANK -->|"acks, returns, NOCs,<br/>daily statement"| SYS
    SYS -->|"tax deposits"| TAXAG[EFTPS and<br/>state agencies]:::external
    TAXC[Tax content team<br/>or vendor]:::external -->|"signed tax releases"| SYS
    SYS -->|"verify the employer's<br/>funding account"| AGG[Account verification<br/>aggregator]:::external
    SYS -->|"journal events"| GL[QuickBooks ledger]:::external
    SYS -->|"7-year records, read-only"| AUD[Auditors and<br/>regulators]:::external
    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

- The banks are drawn as one box on purpose: we only ever talk to our two ODFIs, each company homed at one. FedACH and every RDFI sit behind them.
- QuickBooks' ledger consumes the journal; it never writes back ([`../quickbooks-ledger/`](../quickbooks-ledger/)). The aggregator is the one used by [`../bank-feed-aggregation/`](../bank-feed-aggregation/).

## D2. Data flow (DFD)

Inputs to outputs on the design-peak night (Wednesday 28 October 2026). Stores are cylinders, processes are rounded boxes, every edge has a format, size and rate.

```mermaid
%% D2: what flows where, with sizes and rates at the design peak. 6 M paychecks, 600k runs at one cut-off.
flowchart LR
    APR[Approvals]:::client -->|"JSON ~2 KB, ~70/s,<br/>~700/s final minute"| PRS("Pay run service"):::service
    PRS -->|"snapshot ~20 KB per run,<br/>~12 GB on the night"| SNAP[(Snapshot store)]:::store
    REL[(Tax releases)]:::store -->|"bundle ~50 MB,<br/>a few a month"| CALC("Calc workers"):::service
    SNAP -->|"snapshot slices"| CALC
    CALC -->|"paychecks ~3.5 KB,<br/>3,333/s worst case"| PDB[(Payroll DB)]:::store
    PDB -->|"instructions ~500 B,<br/>6.6 M READY"| FB("File builder"):::critical
    FB -->|"94-byte records, ~7 files<br/>of ~95 MB, ~620 MB"| ODFI[Two ODFIs]:::external
    FB -->|"registry rows, ~20 a day,<br/>fallback trace index"| RAILS[(Rails DB)]:::store
    ODFI -->|"return files, a few thousand<br/>entries a day, ach_ref in each"| RET("Returns service"):::service
    RET -->|"RETURNED, journal,<br/>reissue rows"| PDB
    PDB -->|"liabilities, ~40 M<br/>deposits a year"| TD("Tax deposit service"):::service
    TD -->|"EFTPS and state files"| AG[EFTPS and states]:::external
    FB -->|"file bytes, raw bank files,<br/>~40 GB a year"| WORM[(WORM store)]:::store
    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

- The return volume is an `[estimate]`; the rest follows from solution §2. The file builder is red because every one of the night's ~$17 B of entries passes through it before the ODFI cut-off.

### D2b. Zoom-in: one NACHA file

The run from solution §3.3 inside a file: one batch per company and entry class, control records that the bank checks and we reconcile.

```mermaid
%% D2b: anatomy of one night file. One batch per company and entry class. The control records carry counts and totals the bank checks and we reconcile against.
flowchart LR
    FH["1 File header<br/>origin, date, modifier C"] -->|"contains"| BH1["5 Batch header<br/>company c_7, CCD, eff. Thu"]
    FH -->|"contains"| BH2["5 Batch header<br/>company c_7, PPD, eff. Fri"]
    BH1 -->|"entries"| E1["6 Entry, debit<br/>employer account, 2542018"]
    BH2 -->|"entries"| E2["6 Entry x 12, credits<br/>net pay, ach_ref in each"]
    E1 -->|"closed by"| BC1["8 Batch control<br/>count 1, total debit"]
    E2 -->|"closed by"| BC2["8 Batch control<br/>count 12, total credit"]
    BC1 -->|"summed into"| FC["9 File control<br/>batches, entries, hash,<br/>12-digit totals"]
    BC2 -->|"summed into"| FC
    FC -->|"must equal"| REG[(Registry row<br/>count, totals, sha256)]

    class FH,BH1,BH2,E1,E2,BC1,BC2,FC service
    class REG store

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
```

- Records are 94 characters, blocked in tens. An entry's amount is 10 digits (at most $99,999,999.99), a file's total debits 12 digits (at most $9,999,999,999.99), and the File ID Modifier one character (36 files a day). Source: the [ACH developer guide](https://achdevguide.nacha.org/ach-file-details). Positions 40 to 54 of each entry (Identification Number, 15 characters) carry our `ach_ref`, which a return copies back.

## D3. Component architecture

The final design is in [solution §6](solution.md#6-final-design-and-the-six-core-flows): 14 nodes, the file builder and bank gateway red. Not repeated here.

## D4. Happy paths, one per FR

FR1 to FR4's main sequences are in solution §4.1 to §4.4 (linked in the table above). Two more happy paths that solution.md describes only in prose:

### D4 FR3. A federal tax deposit, from liability to EFTPS

The payday was Friday 30 October 2026; the company is a semiweekly depositor under $100k of liability per payday, so the deposit is due Wednesday 4 November (counted on the DC legal-holiday calendar) and goes in the day before.

```mermaid
%% D4 (FR3, tax deposits): liabilities accrued by the run become one deposit instruction per EIN, agency and due date, sent through the same registry and gateway.
sequenceDiagram
    autonumber
    participant T as Tax deposit service
    participant D as Payroll DB shard
    participant F as File builder
    participant R as Rails DB
    participant B as Bank gateway
    participant E as EFTPS
    Note over T: Tue 3 Nov, 09:00 ET, deposits due Wed 4 Nov
    T->>D: TAX_LIABILITY due 2026-11-04, agency IRS, grouped by EIN
    D-->>T: c_7 EIN 12-345..., 44270 from run r_93 (paid Fri 30 Oct)
    Note over T,D: a payday at or over 100k of liability would have been due Mon 2 Nov
    T->>D: INSERT TAX_DEPOSIT id H(c_7, IRS, 2026Q4, 2026-11-04) ON CONFLICT DO NOTHING
    F->>D: claim READY deposits for the EFTPS window
    F->>R: register EFTPS batch file, sha256, count, total
    B->>E: upload the registered file, PGP over SFTP
    E-->>B: accepted, acknowledgement numbers per deposit
    B->>D: deposit SENT, acknowledgement number stored
    D->>D: journal Dr IRS payable 44270, Cr settlement bank 44270
```

- EFTPS requires a deposit over $1 M to be submitted by 8 PM ET the day before the due date (IRS Notice 931); submitting every federal deposit the day before means no deposit depends on the same-day option. The $100,000 next-day rule (IRS Pub 15) overrides the schedule: any company with ~$476k of debit on a payday (~280+ employees), and the 50k-employee tenant every payday (~$17.6 M, ~$350k per day late at 2%), deposits the next business day. The EFTPS batch file format itself is not modelled here.

### D4 FR4. An R03 credit return is re-issued

```mermaid
%% D4 (FR4, re-issue): the employee's credit comes back R03. The money is ours again, still owed to the employee. A new instruction with a derived id pays it once the account is fixed.
sequenceDiagram
    autonumber
    participant O as ODFI
    participant X as Returns service
    participant D as Payroll DB shard
    participant M as Employee app
    O-->>X: Mon 19 Oct, R03 no account, trace ...0107, ach_ref 2F0000000093118, 154147
    X->>D: shard 2F, read by ach_ref, trace, amount and account match
    X->>D: NET_PAY RETURNED R03, journal Dr settlement bank, Cr net pay payable
    X->>M: your pay could not be delivered, update your account
    M->>D: new bank account token, MFA step-up, notice to old contact
    X->>D: INSERT REISSUE id H(original, REISSUE, 1), 154147, window SAMEDAY-1 Tue
    Note over X,D: a second click or a replayed return file collides on the same id
    D-->>X: READY for Tue 20 Oct same-day window 1, settles 13:00 ET
```

## D5. Failure paths

Two failure paths live in solution.md (the upload timeout and the shard failover across the cut-off). Three more:

### D5a. A paused file builder loses to a tombstone

```mermaid
%% D5a (failure): builder A pauses past its lease. Builder B tombstones A's file id on the registry primary key before freeing its rows, so A's late registration fails on the same key and its file can never be uploaded.
sequenceDiagram
    autonumber
    participant A as File builder A
    participant B as File builder B
    participant D as Payroll DB shard
    participant R as Rails DB registry
    participant G as Bank gateway
    A->>R: lease for NIGHT, epoch 12
    A->>D: lock PAY_RUN r_81, all 13 READY, claim all into F5, COMMIT
    Note over A: 17:06 PT, a 40 s pause, lease expires after 30 s
    B->>R: lease for NIGHT, epoch 13
    B->>R: INSERT NACHA_FILE F5 VOID, a tombstone on the primary key, wins
    B->>D: rows of F5 back to READY, safe because F5 can never be registered
    B->>D: lock PAY_RUN r_81, claim all 13 into F6, COMMIT
    B->>R: INSERT NACHA_FILE F6 BUILT
    A->>R: INSERT NACHA_FILE F5 BUILT
    R-->>A: unique violation, F5 is VOID, A exits
    G->>R: UPDATE F6 BUILT to UPLOADING where state is BUILT
    G->>G: SFTP put of F6's registered bytes, once
```

- The order is the point. Freeing rows first and checking "never registered" second lets A register in between, and both files pay the same run: that race is 102 of the 53,717 bad outcomes in the reviewer's 175,120 interleavings ([`deep-dives/exactly-once-money-movement.md`](deep-dives/exactly-once-money-movement.md) §4). The epoch is only an early exit; the primary key decides.

### D5b. A calc worker dies after 300 of 500 employees

```mermaid
%% D5b (failure): a worker crash mid-chunk. The activity is retried from the snapshot. Stored paychecks are compared by hash, and instructions are written only after the whole run is calculated.
sequenceDiagram
    autonumber
    participant W as Pay run saga
    participant C1 as Calc worker 1
    participant C2 as Calc worker 2
    participant D as Payroll DB shard
    W->>C1: calc(r_77, chunk 1 of 1, 500 employees, snapshot s_61)
    C1->>D: UPSERT paychecks 1 to 300, three statements of 100
    Note over C1: killed after 300, heartbeats stop
    Note over W: heartbeat timeout 30 s, the activity is retried
    W->>C2: calc(r_77, chunk 1 of 1), attempt 2
    C2->>C2: recompute all 500 from s_61, release R2026.41, engine 3.18
    C2->>D: UPSERT 500, ON CONFLICT compare result_hash
    D-->>C2: 300 identical so no-op, 200 inserted
    C2-->>W: chunk done, totals equal preview_hash
    W->>D: r_77 CALCULATED, then instructions in one transaction
```

### D5c. EFTPS rejects a deposit on the eve of its due date

```mermaid
%% D5c (failure): a federal deposit is rejected for a company enrollment problem. The same deposit id is retried, and past the EFTPS deadline the IRS same-day wire is the fallback.
sequenceDiagram
    autonumber
    participant B as Bank gateway
    participant E as EFTPS
    participant T as Tax deposit service
    participant H as Tax ops on-call
    B->>E: deposit for EIN 98-765..., 1,240,000.00, due Wed
    E-->>B: Tue 15:10 ET, rejected, EIN not enrolled
    B->>T: deposit REJECTED, reason code
    T->>H: page, over 1 M, deadline 20:00 ET today
    H->>E: complete the enrollment through the batch provider channel
    T->>B: same deposit id, attempt 2
    alt accepted before 20:00 ET
        E-->>B: accepted, acknowledgement number
    else still failing at 19:00 ET
        H->>H: IRS same-day wire on Wed, same deposit id, rail WIRE
    end
```

- IRS Notice 931 names the same-day wire as the option when an EFTPS deposit misses its deadline. Late by 1 to 5 days would cost 2% of $1.24 M, ~$24,800, so this pages.

## D6. Activity / decision flow

The upload-outcome tree is in [solution §5.3](solution.md#53-the-upload-timed-out-did-the-bank-get-it-exactly-once-money-movement). Here, the approval admission decision inside the pay run service's one transaction:

```mermaid
%% D6: what the approve call checks, in order, inside one transaction on the tenant's shard. Every refusal comes with the next option.
flowchart TD
    REQ[Approve request<br/>signed received_at]:::client --> C1{received_at before<br/>cutoff_at?}:::decision
    C1 -->|"no"| R1[409 CUTOFF_PASSED<br/>next-day or later pay date]:::client
    C1 -->|"yes"| C2{input_version and<br/>preview still current?}:::decision
    C2 -->|"no"| R2[409 STALE, re-preview]:::client
    C2 -->|"yes"| C3{Tier HOLD?}:::decision
    C3 -->|"yes"| R3[402 FUNDING_REQUIRED<br/>wire instructions]:::client
    C3 -->|"no"| C4{Speed allowed<br/>for the tier?}:::decision
    C4 -->|"no"| R4[409 SPEED_NOT_ALLOWED<br/>offer 4-day or 2-day]:::client
    C4 -->|"yes"| C5{Debit within limit and<br/>exposure under cap?}:::decision
    C5 -->|"no"| R3
    C5 -->|"yes"| C6{Blocking anomaly<br/>rule fires?}:::decision
    C6 -->|"yes"| R5[Held for review,<br/>admin told why]:::client
    C6 -->|"no"| OK[APPROVED, exposure reserved,<br/>outbox run-approved]:::service
    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

- The anomaly model from solution §12 only adds review flags at preview; only deterministic rules can hold a run here.

## D7. Entity relationship

In [solution §3.3](solution.md#33-data-model), with the access patterns and partition keys.

## D8. State machines

The pay run lifecycle is in [solution §4.4](solution.md#44-retry-and-repair-forward-only-corrections). Two more entities have lifecycles that carry the exactly-once story.

### D8a. Payment instruction

```mermaid
%% D8a: one instruction. Released means a REISSUE freed by the reversal's timer. It only moves forward, except a claim whose file was voided, rejected or confirmed not received. A re-freeze supersedes, repairs are new instructions, and Closed can still take a late return.
stateDiagram-v2
    direction LR
    [*] --> Created: run instructed
    Created --> Ready: balanced or released
    Ready --> Superseded: re-freeze
    Ready --> Cancelled: cancel before claim
    Ready --> Claimed: whole run claimed
    Claimed --> Ready: void, rejected, absent
    Claimed --> Sent: file acked
    Sent --> Settled: settlement date
    Settled --> Returned: return file
    Settled --> Reversed: reversal settled
    Settled --> Closed: return window over
    Closed --> Returned: late R31, R06, R11
    Returned --> [*]: reissue is a new row
    Closed --> [*]
    Reversed --> [*]
    Cancelled --> [*]
    Superseded --> [*]
```

### D8b. NACHA file

```mermaid
%% D8b: one file in the registry, keyed by file_id. A tombstone (Void) and a registration (Built) race on the same key. UNKNOWN is first-class. A rebuild happens only after Void, Rejected, or NotReceived, which is final only after 2:15 AM ET.
stateDiagram-v2
    direction LR
    [*] --> Built: registered
    [*] --> Void: sweep tombstone
    Built --> Void: old epoch, voided
    Built --> Uploading: adopted or current
    Uploading --> Built: connect failed
    Uploading --> Uploaded: put complete
    Uploading --> Unknown: failed mid-put
    Unknown --> Uploaded: bank has it
    Unknown --> Uploading: none, before cut-off
    Unknown --> NotReceived: none, final at 0215 ET
    Uploaded --> Acked: totals match
    Uploaded --> Rejected: bank rejects file
    Acked --> [*]
    Rejected --> [*]: rows back to Ready
    NotReceived --> [*]: rows back to Ready
    Void --> [*]: rows back to Ready
```

## D9. Deployment / topology

Two regions, three AZs each. Region A is active for every writer; region B is warm. One shard cluster is drawn; the other seven have the same shape.

```mermaid
%% D9: where each piece runs. Dashed edges cross a region boundary. No synchronous commit crosses a region, and only one region's gateway may talk to the bank.
flowchart LR
    subgraph RA[Region A, active]
        subgraph AZA[AZ a]
            APP[Pay run service, calc pods,<br/>Temporal, file builder]:::service
            P1[(Shard cluster 1 primary)]:::store
        end
        subgraph AZB[AZ b]
            S1[(Sync standby 1)]:::store
            GW[Bank gateway, active]:::critical
        end
        subgraph AZC[AZ c]
            S2[(Sync standby 2)]:::store
            RDB[(Rails DB primary)]:::store
        end
    end
    subgraph RB[Region B, warm]
        R1[(Async replicas,<br/>all clusters)]:::store
        GWB[Bank gateway, standby]:::service
    end
    OBJ[(Multi-region object storage<br/>snapshots, releases, WORM)]:::store
    ODFI[Two ODFIs, companies<br/>split by cohort]:::external
    APP -->|"money txns"| P1
    P1 -->|"sync WAL, ANY 1 of 2"| S1
    P1 -->|"sync WAL, ANY 1 of 2"| S2
    P1 -.->|"async WAL, ~1 s"| R1
    APP -->|"registry, lease"| RDB
    GW -->|"SFTP + PGP, one sender per bank"| ODFI
    GWB -.->|"enabled only after asking the<br/>bank and reconciling"| ODFI
    APP -->|"snapshots, files"| OBJ
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

- 8 shard clusters × (primary + 2 sync standbys + 1 async replica in region B). The rails DB has the same shape. WAL is the write-ahead log.
- **Crosses a region:** async WAL (~1 s RPO), object storage replication, edge logs. Never a synchronous commit, and never two active gateways: the standby gateway is enabled by a human after the bank confirms which files it has (solution §5.5).

## D10. Scaling / partitioning

Tenant to logical shard to cluster, and how the night's instructions funnel back into a handful of files.

```mermaid
%% D10: 1 M tenants over 64 logical shards on 8 clusters. The 50k-employee tenant is moved alone. Every shard drains into one file builder per window, which is the funnel and the red node.
flowchart LR
    T[Tenant t_42]:::client -->|"lookup"| DIR[(Shard directory<br/>1 M tenants to 64 shards)]:::store
    DIR -->|"shards 0 to 31"| C1[(Clusters 1 to 4<br/>~500k small tenants)]:::store
    DIR -->|"shards 32 to 62"| C2[(Clusters 5 to 8<br/>~500k small tenants)]:::store
    BIG[50k-employee tenant]:::client -->|"moved alone"| L63[(Logical shard 63<br/>big tenants only)]:::store
    C1 -->|"~3.3 M READY rows"| FB[File builder<br/>one lease per window]:::critical
    C2 -->|"~3.3 M READY rows"| FB
    L63 -->|"own file group"| FB
    FB -->|"~7 files over two ODFIs,<br/>at most 1 M entries each"| F1[Files A to G]:::service
    FB -->|"big tenant's own file"| F2[File H]:::service
    GROW{10x tenants}:::decision -.->|"more clusters, more origin ids,<br/>a third ODFI by cohort"| FB
    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

- Per cluster at the design peak: ~75k runs, ~8k rows/s for the 30-minute worst case, ~150 GB a year of hot data. No shard is hot by itself; the funnel is the window. See [`../../concepts/sharding.md`](../../concepts/sharding.md).
- The partition key is `tenant_id` everywhere. Within a file, entries are ordered by `(company_id, instruction_id)`, so a rebuild of a rejected file produces the same batches.

## D11. Failure mode map

Component, what fails, blast radius, mitigation. Split in two to stay under 15 nodes each.

### D11a. Money path

```mermaid
%% D11a: failures on the path from instructions to the bank. The bank connection at the cut-off is red: the widest blast radius we do not control.
flowchart TD
    MP[Money path]:::service --> F1[One ODFI's SFTP down<br/>near the cut-off]:::critical
    MP --> F2[Upload outcome<br/>unknown]:::decision
    MP --> F3[Bank rejects a file]:::decision
    MP --> F4[Window exposure over<br/>a bank's limit]:::decision
    F1 -->|"blast radius"| B1[runs homed at that bank,<br/>about half the window]:::client
    F2 -->|"blast radius"| B2[one file, up to 1 M entries,<br/>double pay if re-sent blindly]:::client
    F3 -->|"blast radius"| B3[one file, or one big<br/>tenant's file group]:::client
    F4 -->|"blast radius"| B4[that bank holds its<br/>whole window]:::client
    B1 -->|"mitigation"| M1[probe from 3 PM, backup channel,<br/>same bytes, fallback ladder]:::service
    B2 -->|"mitigation"| M2[UNKNOWN, ask the bank,<br/>never re-send after cut-off]:::service
    B3 -->|"mitigation"| M3[fix, rebuild with a new modifier,<br/>dry run at 4 PM catches most]:::service
    B4 -->|"mitigation"| M4[page at 80%, push large<br/>runs to wire]:::service
    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

### D11b. Calc, data and control plane

```mermaid
%% D11b: failures off the bank path. A bad engine or tax release has the widest blast radius here, and both are stopped before they reach a file.
flowchart TD
    CP[Calc, data, control]:::service --> F5[Shard primary dies]:::decision
    CP --> F6[Temporal or calc<br/>pool down]:::decision
    CP --> F7[Bad engine or<br/>tax release]:::decision
    CP --> F8[Region lost]:::decision
    F5 -->|"blast radius"| B5[1/8 of tenants, ~30 s]:::client
    F6 -->|"blast radius"| B6[approvals fine,<br/>calc barrier at risk]:::client
    F7 -->|"blast radius"| B7[every run in a cohort<br/>or a jurisdiction]:::client
    F8 -->|"blast radius"| B8[all tenants, RTO ~15 min]:::client
    B5 -->|"mitigation"| M5[sync standby, 120 s<br/>commit grace]:::service
    B6 -->|"mitigation"| M6[outbox drains later, page<br/>at barrier + 10 min]:::service
    B7 -->|"mitigation"| M7[replay gate, shadow, cohorts,<br/>supersede and re-freeze]:::service
    B8 -->|"mitigation"| M8[promote replicas, ask the bank,<br/>recompute from snapshots]:::service
    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

## D12. Rollout / migration

From a legacy engine (one job that calculates and writes files) to this design: the five phases of [solution §8](solution.md#8-staff-level-notes), plus the second ODFI, which is onboarded in parallel and gets its cohort once every company is on the new path. Each milestone is that phase's rollback point. Durations are estimates. The first money-ownership flips avoid quarter ends, so a quarter's tax forms come from one system.

```mermaid
%% D12: migration phases. Shadow first, money last. Exactly one system owns a company's money at any time, flipped only between its pay cycles.
gantt
    title Migration from the legacy payroll engine
    dateFormat  YYYY-MM-DD
    axisFormat  %b %Y
    todayMarker off
    section Phase 1 shadow calc
    New engine computes every live run from snapshots   :p1a, 2026-10-05, 182d
    Diff against legacy paychecks, two full quarters    :p1b, 2026-10-05, 182d
    Rollback point, shadow flag off                     :milestone, m1, after p1a, 0d
    section Phase 2 shadow ledger
    Instructions from legacy paychecks, totals compared :p2a, after m1, 42d
    Rollback point, drop the shadow ledger              :milestone, m2, after p2a, 0d
    section Phase 3 money ownership by cohort
    Cohort 1 percent, flipped between pay cycles        :p3a, after m2, 21d
    Cohorts 10 and 50 percent                           :p3b, after p3a, 42d
    Cohort 100 percent                                  :p3c, after p3b, 28d
    Rollback point, money_owner back to legacy          :milestone, m3, after p3c, 0d
    section Phase 4 tax deposits and returns
    Deposits and returns move to the new path           :p4a, after m3, 28d
    Rollback point, deposits back to legacy             :milestone, m4, after p4a, 0d
    section Phase 5 decommission
    Legacy read-only for audit, then retired            :p5a, after m4, 60d
    section Second ODFI at 1x
    Onboard bank 2, settlement account, reconciliation  :q1, 2027-01-04, 120d
    Move a 20 to 50 percent cohort, home_bank flag      :q2, after m3, 28d
    Rollback point, home_bank back to bank 1            :milestone, mq, after q2, 0d
```

- The rollback at every phase is a flag, never a data migration, because each run lives in exactly one system. YTD balances move as opening balances in phase 3 and are checked against legacy totals per employee before a company's first flip.
