# Diagrams: TurboTax e-file at the April 15 peak

> One-line answer: twelve views of one design. The File click is one durable write (postmark plus pre-minted submission IDs) answered in under 2 s, and a gateway-signed receipt token keeps the postmark if that write has to be retried; a transmitter drains the filing DB to IRS MeF in messages of 100 under leases; an ack reconciler pulls acks by submission ID and releases linked state returns; a sweeper proves every submission got an answer. The MeF send pool (sessions x 100 / MeF latency) is the one red box.

The D1 to D12 set from `hld/CLAUDE.md` §4, each with a one-line caption. A diagram already in [`solution.md`](solution.md) gets a heading, a caption and a link, never a second copy. Acronyms: MeF (Modernized e-File, the IRS e-file system), A2A (application-to-application, MeF's SOAP channel), ASID (Application System ID, one enrolled client system with 5 sessions), ETIN (Electronic Transmitter Identification Number), EFIN (Electronic Filing Identification Number), SAML (Security Assertion Markup Language), AZ (availability zone), KMS (key management service), ATS (Assurance Testing System, the IRS's pre-season test environment), SSN (Social Security number).

| # | Diagram | Where it lives |
|---|---|---|
| D1 | Context | below |
| D2 | Data flow | below |
| D3 | Component architecture (final design) | [solution §6](solution.md#6-final-design-and-the-six-core-flows) |
| D4 | Happy path per FR | FR1 File, FR2 Transmit, FR3 Acknowledge, FR4 Fix and resubmit: the sequence diagrams in [solution §4.1 to §4.4](solution.md#4-high-level-design). The linked state return end to end: below |
| D5 | Failure paths | Send timeout: [solution §5.3](solution.md#53-never-two-irs-submissions-for-one-attempt-even-when-a-send-times-out). DB failover at 11:59 PM: [solution §5.2](solution.md#52-zero-lost-returns-and-still-a-postmark-when-the-database-fails-over-at-1159-pm). MeF down 2 h: [solution §10.4](solution.md#104-failure-timeline). Dead transmit worker, poisoned message, double tap: below |
| D6 | Decision flows | Send limiter and breaker: [solution §5.5](solution.md#55-mef-is-down-for-two-hours-on-april-15-what-do-filers-see-and-what-happens-when-it-comes-back). Sweeper: [solution §5.6](solution.md#56-how-do-you-know-every-one-of-3-m-deadline-day-submissions-got-an-answer). What the File click blocks: below |
| D7 | Entity relationship | [solution §3.3](solution.md#33-data-model) |
| D8 | State machines | Submission: [solution §5.3](solution.md#53-never-two-irs-submissions-for-one-attempt-even-when-a-send-times-out). Filer-visible status and MeF session: below |
| D9 | Deployment / topology | below |
| D10 | Scaling / partitioning | below |
| D11 | Failure mode map | below, two trees |
| D12 | Rollout / migration | below |

## D1. Context (zoom-out)

Our system as one box: filers and the tax interview hand it signed returns, the IRS (and through it the states) answers, filers and the refund-status service hear the outcome, and humans take what the machine cannot resolve.

```mermaid
%% D1: the e-file platform as one box with every external actor. States never talk to us directly; MeF sits between.
flowchart LR
    FIL[Filers<br/>web, mobile, desktop]:::client -->|"File, resubmit,<br/>status reads"| SYS[TurboTax e-file platform<br/>intake, transmit,<br/>acks, sweeper]:::service
    TI[Tax interview<br/>builds + signs returns]:::service -->|"signed MeF XML<br/>packages by hash"| SYS
    SYS -->|"SendSubmissions, GetAcks,<br/>GetSubmissionsStatus"| MEF[IRS MeF A2A]:::external
    MEF -->|"receipts, acks,<br/>status records"| SYS
    MEF -->|"linked and unlinked<br/>state returns, hourly"| ST[State tax agencies]:::external
    ST -->|"state acks via MeF"| MEF
    SYS -->|"accepted, rejected,<br/>postmark"| NOTP[Email and push<br/>providers]:::external
    SYS -->|"accepted events"| RS[Refund status, problem 45]:::service
    SYS -->|"stuck IDs, 3rd reject,<br/>outage reports"| OPS[E-file ops, MeF Mailbox,<br/>IRS e-Help Desk]:::external

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

## D2. Data flow (DFD)

Inputs to outputs with the data name, format, size and peak rate on every edge. Stores are cylinders, processes are rounded. Rates are at the ~500 submissions/s peak minute unless marked "design" (1,000/s).

```mermaid
%% D2: data flow at the deadline peak. The heavy bytes go package store to transmitter to MeF; the click itself is small.
flowchart LR
    APP(Filer app) -->|"File request, JSON ~2 KB,<br/>280/s, design 560/s"| INT(Filing intake)
    TI(Tax interview) -->|"signed package, zipped XML<br/>~78 KB avg, ~500/s"| PKG[(Package store<br/>S3, ~6.3 TB/season)]
    INT -->|"attempt + submission rows<br/>~1.5 KB each, ~500/s"| DB[(Filing DB<br/>~120 GB/season)]
    INT -.->|"503 + signed receipt token ~300 B,<br/>only when the commit is late"| APP
    TI -->|"package hash on the return row,<br/>~280/s"| DB
    DB -->|"claims of 100 rows,<br/>~5 claims/s"| TX(Transmitter + packager)
    PKG -->|"package bytes,<br/>~39 MB/s"| TX
    TX -->|"SOAP container zip ~7.8 MB,<br/>~5 messages/s, 312 Mbit/s"| MEF(IRS MeF)
    MEF -->|"ack XML ~4 KB,<br/>up to 500 per GetAcks"| ACK(Ack reconciler)
    ACK -->|"raw ack ~4 KB, ~320 GB/season"| PKG
    ACK -->|"ACK row + status,<br/>~500/s at the ack wave"| DB
    DB -->|"status event, JSON ~300 B,<br/>~2.5k/s"| K[[Kafka filing-status]]
    K -->|"notification, ~500/s"| NOTIF(Notifier)
    K -->|"accepted events"| RS(Refund status, problem 45)

    class APP client
    class INT,TI,TX,ACK,NOTIF,RS service
    class PKG,DB store
    class K queue
    class MEF external

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

## D3. Component architecture

The final design with the red send pool lives in [solution §6](solution.md#6-final-design-and-the-six-core-flows). It is not repeated here.

## D4. Happy paths, one per FR

FR1 to FR4 are the sequence diagrams in [solution §4.1 to §4.4](solution.md#4-high-level-design). The one path those leave as a note is the linked state return after its release, which takes 12 to 24 h and involves a party we never talk to directly.

### D4 FR2 and FR3 for a state return: release, MeF check, state pickup, state ack

The California return goes out only after the federal accept; MeF checks it against that accept, the state picks it up in an hourly batch, and its ack comes back through MeF.

```mermaid
%% D4 (state path): a linked California return from release to ack. MeF checks the federal accept and the SSN match; the state batch runs hourly.
sequenceDiagram
    autonumber
    participant D as Filing DB
    participant T as Transmit worker
    participant M as IRS MeF
    participant S as California tax board
    participant R as Ack reconciler
    participant N as Notifier
    D->>T: CA submission QUEUED, linked to fed 0A7K29Q, priority 2
    T->>M: SendSubmissions, CA in a message of 100 state submissions
    M-->>T: receipt
    T->>D: CA RECEIPTED, first ack poll in 12 h
    M->>M: accepted federal under 0A7K29Q exists, SSN matches, CA participates
    M->>M: status READY FOR PICKUP, batched into the hourly CA file
    S->>M: GetNewSubmissions, about 10 min after the batch time
    S->>M: state ack Accepted
    R->>M: GetAcks for state IDs due, separate request from federal
    M-->>R: CA Accepted
    R->>D: ACK, CA ACCEPTED, outbox
    D-->>N: state.accepted via Kafka
    N-->>N: email + push, California return accepted
    Note over M,S: without an accepted federal, MeF marks the state DENIED BY IRS and the state never sees it
```

## D5. Failure paths

The send timeout, the 11:59 PM database failover and the two-hour MeF outage are in solution [§5.3](solution.md#53-never-two-irs-submissions-for-one-attempt-even-when-a-send-times-out), [§5.2](solution.md#52-zero-lost-returns-and-still-a-postmark-when-the-database-fails-over-at-1159-pm) and [§10.4](solution.md#104-failure-timeline). Three more below.

### D5a. A transmit worker dies mid-call

The rows it claimed must not go back to `QUEUED`: the call may have landed. Its ASID's sessions must not leak until MeF's nightly reaper.

```mermaid
%% D5a: worker death. Lease expiry leads to UNKNOWN and a status check, never to a blind resend. The new ASID owner logs out the leaked sessions.
sequenceDiagram
    autonumber
    participant W as Worker A (dies)
    participant D as Filing DB
    participant L as ASID lease table
    participant W2 as Worker B
    participant S as Sweeper
    participant M as IRS MeF
    W->>D: claim 100, SENDING, epoch 7, lease until 22:35
    W->>M: SendSubmissions on ASID a07 session 3
    Note over W: pod killed at 22:01, no Logout, no reply recorded
    L-->>W2: ASID a07 lease expires at 22:01:10, W2 takes it, epoch 12
    W2->>M: Logout the 5 stored session handles of a07, then Login
    Note over W2,M: session slots recovered in seconds, no Session Limit Reached
    S->>D: 22:35, lease passed, 100 rows SENDING to UNKNOWN
    S->>M: GetSubmissionsStatus for the 100 IDs
    M-->>S: all 100 RECEIVED
    S->>D: 100 rows RECEIPTED, ack polling starts
    Note over D,M: had MeF said not found twice with the watermark past M1, the rows would requeue with the same IDs, in their own message
```

### D5b. One bad package poisons a message

MeF rejects a message as a whole when its envelope or manifest is invalid, and "all submissions must be resubmitted". A deterministic packaging bug would fail again on every resend, so the transmitter bisects.

```mermaid
%% D5b: a message-level reject. Safe to resend with the same IDs because MeF stored nothing, but a poison submission is isolated by halving.
sequenceDiagram
    autonumber
    participant T as Transmit worker
    participant M as IRS MeF
    participant D as Filing DB
    participant O as E-file on-call
    T->>M: SendSubmissions M1, 100 submissions
    M-->>T: error, message ID M1 plus E, manifest invalid
    T->>D: 100 rows back to QUEUED, same IDs, poison suspect flag
    T->>M: M2 with the first 50
    M-->>T: receipt
    T->>M: M3 with the other 50
    M-->>T: error
    T->>M: halve again, 25 and 25, then 13 and 12, until one is left
    M-->>T: the single bad submission fails alone
    T->>D: bad one QUARANTINED, 99 RECEIPTED
    T->>O: page with the submission ID and the MeF error
    Note over T,D: about 7 extra calls to isolate 1 in 100, the other 99 lose minutes, not hours
```

### D5c. The filer double-taps File, then the app retries after a lost reply

Two requests with one key, then a retry after a timeout: one attempt, one postmark, one set of IDs.

```mermaid
%% D5c: duplicate File requests. The idempotency key and the one-open-submission-per-kind index make the second and third requests return the first answer.
sequenceDiagram
    autonumber
    participant F as Filer app
    participant I as Filing intake
    participant D as Filing DB
    F->>I: POST file r_42, key k1 (tap 1)
    F->>I: POST file r_42, key k1 (tap 2, 80 ms later)
    I->>D: tap 1, insert attempt with key k1, COMMIT
    I->>D: tap 2, insert attempt with key k1
    D-->>I: unique violation on k1
    I->>D: read attempt by key k1
    I-->>F: tap 2 gets the tap 1 answer, same postmark, same IDs
    Note over F,I: tap 1 reply lost on a flaky network
    F->>I: retry POST file r_42, key k1, 2 s later
    I-->>F: 202, the same attempt, postmark of tap 1
    Note over F,D: a new key on the same open return hits the per (return, kind) index and gets the existing attempt too
```

## D6. Activity / decision flows

The send limiter and breaker are D6a in [solution §5.5](solution.md#55-mef-is-down-for-two-hours-on-april-15-what-do-filers-see-and-what-happens-when-it-comes-back); the sweeper is D6b in [solution §5.6](solution.md#56-how-do-you-know-every-one-of-3-m-deadline-day-submissions-got-an-answer).

### D6c. What the File click blocks, and what it leaves to the IRS

At 11:59 PM a local block costs the filer the postmark; an IRS reject does not. So the click only blocks what cannot be sent, and the resubmit path checks the perfection window, whose dates come from the per-season rules table.

```mermaid
%% D6c: decisions at the File and resubmit click. Pink = decision. Only an unsendable package or a closed window changes the outcome.
flowchart TD
    C[File or resubmit request] --> Q1{Hash matches the<br/>return row, signed?}
    Q1 -->|"no"| B1["Reject the click: rebuild<br/>on the review screen"]
    Q1 -->|"yes"| Q2{Open submission of<br/>the same kind?}
    Q2 -->|"yes"| B2[Return the existing attempt]
    Q2 -->|"no"| Q3{Resubmit with<br/>a rejected parent?}
    Q3 -->|"no, first File"| P1[Postmark = this stamp, or a valid<br/>replayed token's earlier stamp]
    Q3 -->|"yes"| Q4{Before the season cutoff?<br/>earlier of filer and Eastern<br/>midnight, last retransmit day}
    Q4 -->|"yes"| P2[Postmark = the root attempt's,<br/>priority 0, transmit_by set]
    Q4 -->|"no"| P3[Postmark = own receipt time,<br/>UI warned before the click]
    P1 --> W[Mint IDs, one txn,<br/>202 RECEIVED]
    P2 --> W
    P3 --> W

    class C,B1,B2,P1,P2,P3,W service
    class Q1,Q2,Q3,Q4 decision

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

Predicted IRS business-rule failures are shown during the interview, not enforced at the click.

## D7. Entity relationship

The `erDiagram` with keys, the shard key and the access patterns is in [solution §3.3](solution.md#33-data-model).

## D8. State machines

The submission state machine (D8a) is in [solution §5.3](solution.md#53-never-two-irs-submissions-for-one-attempt-even-when-a-send-times-out). Two more lifecycles below.

### D8b. What the filer sees, per return

Internal states collapse into a few filer-facing ones. `SENDING`, `UNKNOWN` and `ESCALATED` all show as Sent. A banner, not a state, covers a slow IRS. A state return behind a federal return that is never fixed gets a timer and a prompt to send it unlinked or on paper (Orphaned).

```mermaid
%% D8b: filer-visible status of the federal return, with the state return's own lane. Labels are what the filer reads.
stateDiagram-v2
    direction LR
    state "Federal" as FED {
        direction LR
        Received --> Sent : claimed
        Sent --> Accepted : ack accepted
        Sent --> Rejected : ack rejected
        Rejected --> Received : resubmit by cutoff
    }
    state "Each state return" as STL {
        direction LR
        Waiting --> StateSent : federal accepted
        StateSent --> StateAccepted : state ack
        StateSent --> StateRejected : state or IRS denial
        Waiting --> Orphaned : federal never fixed
        Orphaned --> StateSent : sent unlinked
    }
    [*] --> FED : File click
    [*] --> STL : File click
    FED --> [*]
    STL --> [*]
```

### D8c. One MeF session (5 per ASID)

A session is the scarce unit. It runs one call at a time, dies after 10 h of activity or 15 min idle, and a Logout on an expired session fails, so a leaked one holds a slot until MeF's nightly cleanup unless its new owner logs it out within 15 minutes.

```mermaid
%% D8c: lifecycle of one MeF A2A session. LEAKED is why ASIDs have owners who log out a dead pod's sessions.
stateDiagram-v2
    direction LR
    [*] --> Idle : Login, SAML issued
    Idle --> InCall : start one call
    InCall --> Idle : reply or timeout
    Idle --> Expired : 15 min idle
    Idle --> Expired : 10 h of activity
    Idle --> Closed : Logout
    InCall --> Leaked : pod dies
    Idle --> Leaked : pod dies
    Leaked --> Closed : Logout within 15 min
    Leaked --> Reaped : expired, nightly cleanup
    Expired --> [*]
    Closed --> [*]
    Reaped --> [*]
```

## D9. Deployment / topology

Two AWS regions, three AZs each, the same shape Intuit runs TurboTax on. Region A is home for the filing DB, with the 4 shard writers spread so no AZ holds more than 2. Region B takes File traffic only after its replicas are promoted; receipt tokens keep every postmark taken meanwhile.

```mermaid
%% D9: where everything runs. Writers are spread over AZs; Aurora storage spans 3 AZs synchronously; only the async replicas and package copies cross regions.
flowchart LR
    subgraph RA["Region A (home)"]
        direction TB
        subgraph AZ1["AZ 1"]
            I1[Intake, transmit,<br/>reconciler pods]
            W1[(Writers of<br/>shards 1 and 4)]
        end
        subgraph AZ2["AZ 2"]
            I2[Intake, transmit,<br/>reconciler pods]
            W2[(Writer of shard 2,<br/>readers)]
        end
        subgraph AZ3["AZ 3"]
            I3[Intake, transmit,<br/>reconciler pods]
            W3[(Writer of shard 3,<br/>readers)]
        end
        S3A[(S3: packages,<br/>raw acks, evidence)]
    end
    subgraph RB["Region B (standby for File)"]
        direction TB
        IB[Intake pods,<br/>after promotion]
        RB2[(Aurora async replicas,<br/>about 1 s behind)]
        S3B[(S3 package copies)]
    end
    MEF[IRS MeF A2A]
    I1 -->|"commit to the<br/>shard's writer"| W1
    I2 -->|"commit"| W2
    I3 -->|"commit"| W3
    W1 -.->|"6-way storage,<br/>quorum 4 of 6"| W2
    W2 -.->|"6-way storage"| W3
    I2 -->|"SOAP over HTTPS,<br/>egress IPs per AZ"| MEF
    W3 -.->|"async replication"| RB2
    S3A -.->|"interview writes<br/>packages to both"| S3B
    IB -->|"commit after promotion,<br/>new epoch"| RB2

    class I1,I2,I3,IB service
    class W1,W2,W3,RB2,S3A,S3B store
    class MEF external

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

Transmission runs in one region at a time: the ASID owner leases live in the home region's DB, so a region switch moves the leases (and logs out the old sessions) before region B sends anything.

## D10. Scaling / partitioning

Returns are sharded by `hash(return_id)`; every shard has its own claimers, but all of them funnel into one shared send pool. That pool, not any shard, is the hot spot.

```mermaid
%% D10: partitioning. 4 shards scale with pods; the send pool scales only in steps of 5 sessions per enrolled ASID, so it is red.
flowchart LR
    H{"hash(return_id)<br/>mod 4"} -->|"about 25% each"| S1[(Shard 1)]
    H -->|"about 25% each"| S2[(Shard 2)]
    H -->|"about 25% each"| S3[(Shard 3)]
    H -->|"about 25% each"| S4[(Shard 4)]
    S1 -->|"claims of 100"| C1[Claimers 1]
    S2 -->|"claims of 100"| C2[Claimers 2]
    S3 -->|"claims of 100"| C3[Claimers 3]
    S4 -->|"claims of 100"| C4[Claimers 4]
    C1 -->|"in-flight calls"| SP[Send pool<br/>40 ASIDs, 200 sessions<br/>T = 20,000 / L]
    C2 -->|"in-flight calls"| SP
    C3 -->|"in-flight calls"| SP
    C4 -->|"in-flight calls"| SP
    SP -->|"SendSubmissions"| MEF[IRS MeF]
    FIX["Fix: one relative-latency limit,<br/>permits to the oldest queue head,<br/>ASIDs enrolled before April"] -.->|"sizes and guards"| SP

    class H decision
    class S1,S2,S3,S4 store
    class C1,C2,C3,C4,FIX service
    class SP critical
    class MEF external

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

Fairness across shards: a free send permit goes to the claimer group whose shard's queue head has the **oldest postmark** (not round robin), and each claim takes the oldest postmarks on its shard, so the oldest return anywhere goes first and one busy shard cannot starve another's old returns. The submission ID's sequence prefix encodes region, shard and the promotion epoch, so an ack finds its shard without a lookup and a promotion never reissues an ID.

## D11. Failure mode map

Each component, what fails, how far it spreads, and what contains it. Two trees: the accept path, then the send and ack path.

### D11a. Accept path

```mermaid
%% D11a: accept path. Every failure here ends in a retry that keeps its signed stamp or a promotion, so a click inside the deadline still gets its postmark.
flowchart TD
    AP[Accept path] --> F1[Intake pod dies]
    AP --> F2[Shard primary fails over]
    AP --> F3[Token signing key slow]
    AP --> F4[Home region unreachable]
    AP --> F5[Host clock skew]
    AP --> F6[One AZ lost]
    F1 -->|"blast: in-flight clicks on 1 pod"| M1[Client retry with same key,<br/>pre-scaled spare pods]
    F2 -->|"blast: 25% of clicks, ~1,300, ~30 s"| M2[503 + signed token,<br/>retry keeps the postmark]
    F3 -->|"blast: every click's token"| M3[Data key cached per host,<br/>stamp always logged]
    F4 -->|"blast: every click"| M4[File waits for promotion,<br/>tokens keep postmarks, new epoch]
    F5 -->|"blast: wrong postmarks"| M5[Host leaves the File lane<br/>above 50 ms skew]
    F6 -->|"blast: at most 2 of 4 writers"| M6[Writers spread over AZs,<br/>same token path]

    class AP service
    class F1,F2,F3,F4,F5,F6 decision
    class M1,M2,M3,M4,M5,M6 service

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

### D11b. Send and ack path

```mermaid
%% D11b: send and ack path. MeF slowness is red: it is the only failure we cannot fix on our side, and it hits the send pool first.
flowchart TD
    SP[Send and ack path] --> G1[MeF slow, minutes per call]
    SP --> G2[MeF down]
    SP --> G3[Transmit worker dies]
    SP --> G4[Session leak, Session Limit Reached]
    SP --> G5[Packaging bug]
    SP --> G6[Ack never arrives]
    G1 -->|"blast: 1 h target missed"| N1[Relative limiter, oldest postmark<br/>first, floor ~17/s over 2 days]
    G2 -->|"blast: all sends paused"| N2[Breaker, probe, status-check<br/>UNKNOWN first on return]
    G3 -->|"blast: up to 2,000 rows wait 35 min"| N3[Lease to UNKNOWN, status<br/>+ watermark, no blind resend]
    G4 -->|"blast: 5 sessions per ASID"| N4[ASID owner lease, Logout<br/>within 15 min idle]
    G5 -->|"blast: every message or every return"| N5[ATS, 1% canary, reject rate<br/>per rule, bisect poison]
    G6 -->|"blast: one filer unsure"| N6[Sweeper, MeF Mailbox at 24 h,<br/>completeness query]

    class SP service
    class G1 critical
    class G2,G3,G4,G5,G6 decision
    class N1,N2,N3,N4,N5,N6 service

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
```

## D12. Rollout / migration

From the existing transmitter to this one without a single shadow send. Ownership of each attempt moves by cohort; rollback flips ownership of new attempts back, and in-flight submissions finish where they started.

```mermaid
%% D12: migration across one filing season. Every cohort step has a rollback point; nothing changes between the April 1 freeze and the end of the perfection window.
gantt
    title Migration to the new transmitter, tax year 2025 season
    dateFormat YYYY-MM-DD
    axisFormat %b %d
    section Build and certify
    Build intake, transmit, acks         :b1, 2025-10-01, 60d
    ATS certification, ASIDs enrolled    :b2, 2025-11-15, 45d
    Load test at 1,000 per s             :b3, 2025-12-01, 30d
    section Cohort cutover
    Season opens, 1 pct owned by new     :c1, 2026-01-26, 7d
    Rollback point 1                     :milestone, m1, 2026-02-02, 0d
    10 pct, one product line             :c2, 2026-02-02, 7d
    Rollback point 2                     :milestone, m2, 2026-02-09, 0d
    50 pct then 100 pct                  :c3, 2026-02-09, 10d
    Rollback point 3                     :milestone, m3, 2026-02-19, 0d
    section Peak
    Pre-scale and change freeze          :crit, p1, 2026-04-01, 20d
    Deadline day                         :milestone, p2, 2026-04-15, 0d
    Perfection period ends               :milestone, p3, 2026-04-20, 0d
    section Retire
    Old path drains its in-flight acks   :r1, 2026-04-21, 30d
    Extension deadline                   :milestone, r2, 2026-10-15, 0d
    Old transmitter retired              :r3, 2026-10-16, 14d
```

Rollback at any point before April 1: flip the owner of new attempts back to the old transmitter. Submissions already owned by the new path finish on it, because moving an `UNKNOWN` submission between transmitters is the one way this migration could create a duplicate.
