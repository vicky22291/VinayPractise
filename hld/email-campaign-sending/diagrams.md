# Diagrams: Mailchimp campaign sending

> One-line answer: twelve views of one design. A control path (campaign service, scheduler, snapshot store, dispatcher) decides what to send and paces it. A sending path (render workers, MTA fleet with one queue per (IP, provider) and journal ids on a buddy host, quota service) delivers it at the rate each receiver accepts. A feedback path (feedback ingest, suppression store, Kafka, reputation service with a canary for risky campaigns) turns bounces, complaints and unsubscribes into the next send's rules. The mailbox providers' acceptance for our pools is the one red box.

The D1 to D12 set from `hld/CLAUDE.md` §4, each with a one-line caption. A diagram already in [`solution.md`](solution.md) gets a heading, a caption and a link, never a second copy. Acronyms: MTA (mail transfer agent), MX (mail exchanger DNS record), SMTP (Simple Mail Transfer Protocol), DKIM (DomainKeys Identified Mail), SPF (Sender Policy Framework), DMARC (Domain-based Message Authentication, Reporting and Conformance), DSN (delivery status notification, a bounce), ARF (Abuse Reporting Format, a complaint report), FBL (feedback loop), VERP (variable envelope return path), DRR (deficit round robin), KMS (key management service), AIMD (additive increase multiplicative decrease), MIME (the standard email message format), CAS (compare-and-set), DNS (Domain Name System).

| # | Diagram | Where it lives |
|---|---|---|
| D1 | Context | below |
| D2 | Data flow | below |
| D3 | Component architecture (final design) | [solution §6](solution.md#6-final-design-and-the-six-core-flows) |
| D4 | Happy path per FR | FR1 final first minute: below. FR2 throttle: [solution §4.2](solution.md#42-throttle-per-receiver-one-queue-per-ip-provider-rates-learned-from-replies). FR3 domain verification: below (the signed send itself is in [solution §4.3](solution.md#43-protect-reputation-pools-authentication-warm-up-an-abuse-loop)). FR4 async bounce and complaint: below (one-click unsubscribe is in [solution §4.4](solution.md#44-close-the-loop-bounces-complaints-unsubscribes-stats)) |
| D5 | Failure paths | Render worker dies mid-chunk, quota service shard lost, suppression feed stale: below. MTA crash after 250: [solution §5.5](solution.md#55-an-mta-crashes-after-the-receiver-said-250-ok-but-before-we-recorded-it-duplicate-loss-or-neither). Gmail throttles a pool: [solution §10.4](solution.md#104-failure-timeline) |
| D6 | Decision flow | SMTP reply classifier: below. Import and probe gates: [solution §5.3](solution.md#53-a-new-customer-imports-a-purchased-list-and-15-bounce-how-do-you-protect-everyone-else-on-the-shared-pool) |
| D7 | Entity relationship | [solution §3.3](solution.md#33-data-model) |
| D8 | State machines | Message, campaign, sending IP: below |
| D9 | Deployment / topology | below |
| D10 | Scaling / partitioning | below |
| D11 | Failure mode map | below, two trees |
| D12 | Rollout / migration | below |

## D1. Context (zoom-out)

Our system as one box: customers send campaigns in, mail goes out to mailbox providers, and four kinds of feedback come back.

```mermaid
%% D1: the system as one box with every external actor. The providers' acceptance is red: it sets the speed of every send.
flowchart LR
    CUST[Customers<br/>~500k campaigns a day] -->|"campaigns, imports,<br/>domain verification"| SYS[Campaign sending platform<br/>snapshot, pace, render,<br/>deliver, learn]
    SYS -->|"reports, pause notices"| CUST
    AUD[Audience service] -->|"frozen recipient snapshot"| SYS
    SYS -->|"SMTP, ~2 B messages a day"| MBP[Mailbox providers<br/>Gmail, Microsoft, Yahoo,<br/>Apple, long tail]
    MBP -->|"replies, DSNs, ARF,<br/>one-click POSTs"| SYS
    RCPT[Recipients] -->|"read, report spam, unsubscribe"| MBP
    RCPT -->|"clicks, preference page"| SYS
    MBP -.->|"SPF, DKIM, DMARC lookups"| DNS[Customer DNS]
    PMT[Postmaster Tools,<br/>blocklists] -->|"daily spam rate per Feedback-ID,<br/>listings"| SYS
    OPS[Compliance and<br/>deliverability staff] -->|"reviews, holds, pool policy"| SYS

    class CUST,RCPT,OPS client
    class SYS service
    class AUD store
    class MBP critical
    class DNS,PMT external

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

## D2. Data flow (DFD)

Inputs to outputs with data name, format, size and rate. Stores are cylinders, processes rounded. Rates are averages from solution §2 unless marked peak.

```mermaid
%% D2: what flows where. 6.5 B events a day is ~75k/s. Unsubscribes are ~0.2% of sends, ~46/s.
flowchart LR
    AUD[(Audience DB)] -->|"contact rows, ~500 B,<br/>20 M in ~40 s"| SNAPP(Snapshot builder)
    SNAPP -->|"chunk files per provider,<br/>10k rows, encrypted"| SNAP[(Snapshot store)]
    SNAP -->|"provider-chunks by credit"| RND(Render + DKIM sign)
    TPL[(Content versions)] -->|"HTML template ~50 KB,<br/>once per campaign"| RND
    RND -->|"MIME ~50 KB, 23k/s,<br/>200k/s peak"| MTA(MTA fleet)
    MTA -->|"SMTP, ~9.3 Gbps"| OUT[Mailbox providers]
    OUT -->|"reply code + text ~100 B,<br/>one per attempt"| MTA
    OUT -->|"DSN ~70/s, ARF ~5/s,<br/>one-click POST ~46/s"| FB(Feedback ingest)
    FB -->|"suppression ~100 B,<br/>~280/s, ~3k/s peak"| SUP[(Suppression store)]
    SUP -->|"outbox relay, JSON"| KF[(Kafka)]
    MTA -->|"delivery events JSON ~300 B,<br/>~75k/s"| KF
    KF -->|"Parquet ~400 GB/day"| LAKE[(Event lake)]
    KF -->|"counters per campaign,<br/>provider, outcome"| RPT(Stats job)

    class SNAPP,RND,MTA,FB,RPT service
    class AUD,SNAP,TPL,SUP,LAKE store
    class KF queue
    class OUT critical

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
```

## D3. Component architecture

The final design, 14 nodes, is [solution §6](solution.md#6-final-design-and-the-six-core-flows). The MTA zoom-in is in [solution §10.1](solution.md#101-internals-of-each-chosen-technology).

## D4. Happy paths, one per FR

### D4 FR1 final: the first minute of the 20 M campaign

The final design: early snapshot, a free 500-recipient chunk 0 per provider, credit from the allowed rate, the target host recorded before injecting, ids on a buddy. Times are typical.

```mermaid
%% D4 FR1 final: from the scheduler to the first Gmail 250, with the dispatcher in the path.
sequenceDiagram
    autonumber
    participant S as Scheduler
    participant SN as Snapshot store
    participant D as Dispatcher
    participant RW as Render worker
    participant M as MTA, pool P
    participant G as Gmail MX
    S->>SN: 09:50:00 snapshot, 20 M rows, chunks per provider
    SN-->>S: 09:50:40 done, 800 Google chunks of 2,000
    S->>D: 10:00:00 campaign SENDING
    D->>RW: chunk 0 per provider, 500 recipients, free of credit
    D->>D: fill credit, allowed 1,200 per s x 600 s = 720k
    RW->>RW: skip suppressed since 09:50:40, render, sign with shop.com and the pool tier's signer
    RW->>M: record target host on the chunk row, then InjectBatch 500
    M->>M: fsync spool, ids acked by buddy, queue (IP, google), DRR
    M->>M: tokens for IP key and leased pool and domain keys
    M->>G: SMTP on a pooled connection
    G-->>M: 250 OK at ~10:00:02
    M-->>D: queue depth per key, every 1 s
```

### D4 FR2: throttle per receiver

Embedded in [solution §4.2](solution.md#42-throttle-per-receiver-one-queue-per-ip-provider-rates-learned-from-replies) (a Gmail pause on one IP while the Yahoo queue keeps sending). The global-key version is [solution §5.2](solution.md#52-gmail-starts-answering-421-4728-for-one-ip-pool-what-changes-in-what-order-automatically).

### D4 FR3: a customer verifies a sending domain

Before any send from `shop.com`, the customer proves control in DNS and delegates DKIM to keys we hold and can rotate.

```mermaid
%% D4 FR3: domain verification and DKIM delegation by CNAME. Rotation later is a CNAME target change on our side.
sequenceDiagram
    autonumber
    participant C as Customer
    participant CS as Campaign service
    participant K as KMS
    participant D as shop.com DNS
    C->>CS: POST /v1/sending-domains shop.com
    CS->>K: generate RSA-2048 key pair for selector mc1, wrap private key
    K-->>CS: wrapped key, stored as dkim_key_ref
    CS-->>C: publish mc1._domainkey CNAME, em CNAME, DMARC suggestion
    C->>D: adds the records
    C->>CS: POST /v1/sending-domains/shop.com/verify
    CS->>D: resolve mc1._domainkey.shop.com and em.shop.com
    D-->>CS: CNAMEs point to our key host and bounce host
    CS->>CS: SENDING_DOMAIN status VERIFIED
    CS-->>C: verified, From addresses at shop.com allowed
```

### D4 FR4: an asynchronous bounce and a Yahoo complaint

Both arrive by mail days or minutes after the send. Both map to the message by its signed id, with no lookup table.

```mermaid
%% D4 FR4: a DSN to the VERP address and an ARF report from Yahoo's CFL become events, suppressions and abuse-loop counters.
sequenceDiagram
    autonumber
    participant MX as Receiving MX
    participant FI as Feedback ingest
    participant K as Kafka
    participant SW as Suppression writer
    participant S as Suppression store
    participant R as Reputation service
    MX->>FI: DSN to bounce+c_42.ct_9.hmac at em.shop.com, our bounce host
    FI->>FI: decode id, check HMAC, parse status 5.1.1
    FI->>K: event bounced, hard, message c_42.ct_9
    MX->>FI: ARF report from Yahoo CFL, original headers attached
    FI->>FI: message id from our header, check HMAC
    FI->>K: event complained, message c_42.ct_4
    K->>SW: both events
    SW->>S: upsert account scope suppressions, idempotent
    K->>R: per campaign counters, bounce and complaint rates
    R->>R: under 5 pct bounces and 0.3 pct complaints, no action
```

## D5. Failure paths

### D5a. A render worker dies mid-chunk, and the pool changes

The next owner resumes from the checkpoint with a higher epoch and sends the retried batch to the host recorded on the chunk row. Rendezvous hashing alone would move ~1 in 5 of those ids when a host joins ([delivery dive](deep-dives/delivery-semantics-and-mta-failures.md) §2).

```mermaid
%% D5a: lease expiry, fencing by epoch, the intent row, and spool-level dedup by message id. No recipient gets two copies.
sequenceDiagram
    autonumber
    participant W1 as Render worker 1
    participant CDB as Campaign DB, chunk row
    participant W2 as Render worker 2
    participant M as MTA h3, gen 2
    W1->>CDB: lease chunk 17, epoch 4
    W1->>CDB: intent batch 1 to h3 gen 2, epoch 4
    W1->>M: InjectBatch rows 500 to 999
    M-->>W1: ack 300 of 500
    Note over W1: worker crashes before checkpoint 1000
    Note over CDB,M: host h5 joins the pool, a rehash would move ~1 in 5 ids
    Note over CDB: 30 s later the lease expires
    W2->>CDB: lease chunk 17, epoch 5, read intent h3 gen 2
    W2->>M: InjectBatch rows 500 to 999 to h3, not by hash
    M-->>W2: 300 duplicates rejected, 200 accepted
    W2->>CDB: checkpoint 1000, epoch 5
    W1->>CDB: late write with epoch 4 after restart
    CDB-->>W1: rejected, stale epoch
```

### D5b. A quota service shard is lost

MTAs keep sending more slowly on their last leases; a new owner rebuilds the keys from the next round of reports.

```mermaid
%% D5b: soft state means a lost shard costs a few seconds at half rate, never a burst.
sequenceDiagram
    autonumber
    participant M as MTA hosts
    participant Q1 as Quota shard 3
    participant Q2 as Quota shard 7, new owner
    participant G as Gmail
    M->>Q1: t=0 report and lease request
    Q1-->>M: leases for keys on shard 3, valid 2 s
    Note over Q1: t=0.5 s shard 3 host dies
    M->>Q1: t=1 s lease request times out
    M->>M: t=2 s leases expire, run those keys at last rate x 0.5
    M->>G: SMTP continues, slower
    Note over Q2: t=5 s ring membership moves the keys to shard 7
    M->>Q2: t=6 s reports with current rates and demand
    Q2->>Q2: rebuild key state from the reports
    Q2-->>M: t=7 s leases at the rebuilt rates
    Note over M,Q2: no page under 1 min unreachable, metric records 5 s of fallback
```

### D5c. The suppression feed goes stale

Kafka is unavailable. MTAs keep their filters fresh by pulling the suppression store's `created_at` index, hold canary and probation sends, and keep counting bounces locally. Mail is held only when both feeds are stale.

```mermaid
%% D5c: fail toward checking more, never toward sending to someone who left. Two feeds, so one outage costs nothing.
sequenceDiagram
    autonumber
    participant K as Kafka suppressions
    participant M as MTA
    participant S as Suppression store
    participant G as Gmail
    K--xM: t=0 consumer stops receiving
    M->>S: t=2 s pull created_at after last seen, per bucket range
    S-->>M: suppressions written since then
    M->>M: add to today's filter slice, feed age 2 s
    Note over M,S: every 2 s, ~150 range reads per s fleet-wide, not 100k point reads
    M->>M: hold canary and probation sends, their verdicts cannot flow
    M->>M: count bounces per campaign locally, 5 and 10 pct lines still act
    M->>G: send the rest, filter positives confirmed with the store
    Note over M,S: store also down and both feeds stale 60 s, hold all mail and page
    K->>M: t=12 min back, replay from last offset, adds are idempotent
```

## D6. Activity / decision flow

The SMTP reply classifier inside every MTA: one reply in, one action out. The `4.7.28` variants follow the wording on [Google's SMTP error page](https://support.google.com/mail/answer/3726730); for the unscoped one Google says "assume that all three are affected".

```mermaid
%% D6: reply classifier. Decision nodes in pink. Every throttle action applies to a key, not to the message, except the same Message-ID variant.
flowchart TD
    R{Reply class} -->|"2xx"| OK[Delivered, write done,<br/>count toward additive increase]
    R -->|"4xx"| Q28{Google 4.7.28,<br/>which variant?}
    Q28 -->|"names a scope"| PK[Pause the named key<br/>IP, netblock, DKIM, SPF or URL domain,<br/>our tier signer pauses one tier<br/>10 min, then 1 connection]
    Q28 -->|"no scope"| PA[Pause IP, DKIM and<br/>SPF keys together]
    Q28 -->|"same Message-ID"| MID[No key paused, page,<br/>a bug resent one id]
    Q28 -->|"not 4.7.28"| QU{450 4.2.1, one user<br/>receiving too fast?}
    QU -->|"yes"| RU[Retry this message in 30 min]
    QU -->|"no"| QD{Deferrals over 2 pct<br/>of the key in 60 s?}
    QD -->|"yes"| HV[Halve rate and connections<br/>message keeps its place]
    QD -->|"no"| RT[Retry message on schedule<br/>15 min, 45 min, every 2 h, 4 days]
    R -->|"5xx"| Q5{Which 5xx?}
    Q5 -->|"5.1.1, no such user"| HB[Hard bounce, suppress,<br/>count for the account]
    Q5 -->|"5.7.1 reputation block"| BL[Pause IP and provider 1 h,<br/>page if pool wide]
    Q5 -->|"5.7.26 or 5.7.515 auth"| AU[Page platform on-call,<br/>our signing or DNS is broken]

    class R,Q28,QU,QD,Q5 decision
    class OK,PK,PA,MID,RU,HV,RT,HB,BL,AU service

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

## D7. Entity relationship

Embedded in [solution §3.3](solution.md#33-data-model) with the access patterns and partition keys.

## D8. State machines

### D8a. Message

One message per (campaign, recipient). Throttle deferrals keep it `Queued`; only message-level failures spend an attempt.

```mermaid
%% D8a: message lifecycle. Delivered can still turn into a complaint or an unsubscribe later.
stateDiagram-v2
    direction LR
    [*] --> Rendered
    Rendered --> Queued: spool fsync
    Queued --> Queued: key paused
    Queued --> Suppressed: pre-SMTP check
    Queued --> InFlight: tokens granted
    InFlight --> Delivered: 250
    InFlight --> Deferred: 4xx for message
    Deferred --> Queued: retry time
    Deferred --> Expired: 4 days
    InFlight --> Bounced: 5xx
    state "Delivered, then feedback" as Final {
        direction TB
        Delivered --> Complained: ARF later
        Delivered --> Unsubscribed: one-click
    }
    Suppressed --> [*]
    Bounced --> [*]
    Expired --> [*]
```

### D8b. Campaign

The abuse loop and the customer can both pause; only the customer or a reviewer resumes.

```mermaid
%% D8b: campaign lifecycle. Canary and AutoPaused are entered by the reputation service, not by the customer.
stateDiagram-v2
    direction LR
    [*] --> Draft
    Draft --> Scheduled: schedule
    Scheduled --> Draft: unschedule
    Scheduled --> Snapshotting: due
    Snapshotting --> Sending: send_at
    Snapshotting --> Canary: new or risky
    Canary --> Sending: verdict passed
    Canary --> AutoPaused: lines crossed
    state Sending {
        direction TB
        [*] --> Releasing
        Releasing --> Draining: all released
    }
    Sending --> Paused: customer
    Paused --> Sending: resume
    Sending --> AutoPaused: abuse threshold
    AutoPaused --> Sending: review passed
    AutoPaused --> Cancelled: review failed
    Paused --> Cancelled: cancel
    Sending --> Completed: all final
    Completed --> [*]
    Cancelled --> [*]
```

### D8c. Sending IP

An IP's reputation is its value. rDNS is reverse DNS (a PTR record), which Google requires for every sending IP. SendGrid: "If you haven't sent email messages through your IP address in more than 30 days, warm it up again" ([SendGrid](https://www.twilio.com/docs/sendgrid/ui/sending-email/warming-up-an-ip-address)).

```mermaid
%% D8c: sending IP lifecycle. Warming caps grow daily for about 41 days.
stateDiagram-v2
    direction LR
    [*] --> Provisioned
    Provisioned --> Warming: rDNS and pool set
    Warming --> Warming: next day cap
    Warming --> Active: cap reached
    Active --> Cold: 30 days idle
    Cold --> Warming: re-warm
    Active --> Listed: blocklist hit
    Listed --> Remediation: cause removed
    Remediation --> Warming: delisted
    Active --> Retired: pool shrink
    Retired --> [*]
```

## D9. Deployment / topology

Two sites. Every pool keeps half its IPs in each, so a site loss halves rates instead of stopping a pool. Inside a site, each MTA host has a buddy in another rack that holds its journal ids, and a registry hands out send leases and generations. Across sites, a compact final-id stream tells each site what the other delivered. Control-plane data replicates asynchronously; the suppression topic is mirrored both ways because every MTA needs every suppression.

```mermaid
%% D9: two sites. Cross-site edges are dashed. IP addresses never move between sites.
flowchart LR
    subgraph SA[Site A, primary control plane]
        CSA[Campaign service<br/>scheduler, dispatcher]
        CDBA[(Campaign DB primary<br/>+ sync standby)]
        RWA[Render pool<br/>autoscaled, up to 300 cores]
        MTAA[MTA hosts x 100<br/>2,500 IPs, half of each pool,<br/>buddy pairs across racks]
        REGA[(Registry A<br/>send leases, generations)]
        KA[[Kafka A]]
        SUPA[(Suppression store<br/>3 replicas)]
    end
    subgraph SB[Site B, standby control plane]
        CDBB[(Campaign DB replica)]
        RWB[Render pool]
        MTAB[MTA hosts x 100<br/>2,500 IPs, other half,<br/>buddy pairs across racks]
        REGB[(Registry B<br/>send leases, generations)]
        KB[[Kafka B]]
        SUPB[(Suppression store<br/>3 replicas)]
    end
    CSA -->|"campaigns"| CDBA
    CDBA -.->|"async replication, ~1 s"| CDBB
    CSA -->|"chunks by pool"| RWA
    CSA -->|"chunks by pool"| RWB
    RWA -->|"inject"| MTAA
    RWB -->|"inject"| MTAB
    KA <-.->|"mirror suppressions both ways"| KB
    SUPA <-.->|"multi-site replication"| SUPB
    MTAA -->|"events"| KA
    MTAA <-.->|"final-id stream both ways,<br/>~50 B per message, ~5 MB/s"| MTAB
    MTAB -->|"events"| KB
    MTAA -->|"lease renewals, 1 s"| REGA
    MTAB -->|"lease renewals, 1 s"| REGB

    class CSA,RWA,RWB,MTAA,MTAB service
    class CDBA,CDBB,SUPA,SUPB,REGA,REGB store
    class KA,KB queue

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
```

## D10. Scaling / partitioning

Work is partitioned by the throttle key, not by customer or campaign. The hot key is the big sender's pool to Google; the fix is planned IP capacity and fair sharing, not more machines.

```mermaid
%% D10: partition keys at each stage. Red is the hot key, (pool P, google), draining at 1,200/s.
flowchart LR
    SNP[Snapshot<br/>split by provider] -->|"800 Google chunks"| DSG[Dispatcher shard<br/>by pool]
    SNP -->|"1,200 other chunks"| DSG
    DSG -->|"credit 720k"| HOT[Key pool P, google<br/>20 IPs x 60 per s<br/>= 1,200 per s]
    DSG -->|"credit 420k"| MSK[Key pool P, microsoft<br/>700 per s]
    DSG -->|"credit 240k"| YHK[Key pool P, yahoo<br/>400 per s]
    HOT -.->|"fix, planned 6 weeks ahead"| FIX1[More warmed IPs, sized<br/>from p10 measured rates,<br/>40 IPs halves the time]
    HOT -.->|"fix, same day"| FIX2[DRR shares the key,<br/>small free chunk 0 per campaign]
    EVT[[delivery-events<br/>256 partitions by message id]] -->|"spread evenly"| ST[Stats job keyed by campaign]
    SUPK[(Suppression store<br/>account plus bucket 0 to 63)] -->|"largest account over 64 partitions"| SUPC[Snapshot anti-join]

    class SNP,DSG,ST,SUPC service
    class MSK,YHK queue
    class HOT critical
    class FIX1,FIX2 decision
    class EVT queue
    class SUPK store

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

## D11. Failure mode map

### D11a. Sending path

Component, what fails, blast radius, mitigation. The receiver's block is the widest radius and the slowest to heal.

```mermaid
%% D11a: sending path failures. Red is the receiver, the failure we cannot fix by restarting anything.
flowchart TD
    ROOT[Sending path] --> C1[Render worker dies]
    ROOT --> C2[MTA host dies]
    ROOT --> C3[Quota service shard lost]
    ROOT --> C4[Provider blocks a pool<br/>550 5.7.1]
    C1 -->|"blast"| B1[One chunk, 30 s]
    B1 -->|"mitigation"| M1[Lease expiry, epoch fence,<br/>spool dedup by id]
    C2 -->|"blast"| B2[25 IPs silent ~34 s, 0 lost,<br/>~128 to 133 duplicates, disk or not]
    B2 -->|"mitigation"| M2[Ids on a buddy, send lease<br/>and generation fence,<br/>re-render from snapshot]
    C3 -->|"blast"| B3[Its keys at half rate<br/>for ~5 s]
    B3 -->|"mitigation"| M3[Soft state rebuilt<br/>from MTA reports]
    C4 -->|"blast"| B4[Every sender on the pool,<br/>hours to days]
    B4 -->|"mitigation"| M4[Pause pool to provider, page,<br/>find and remove the sender]

    class ROOT,C1,C2,C3 service
    class C4 critical
    class B1,B2,B3,B4 decision
    class M1,M2,M3,M4 service

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

### D11b. Control and feedback path

```mermaid
%% D11b: control and feedback failures. None of these can send mail to someone who left, by design.
flowchart TD
    ROOT[Control and feedback] --> C1[Scheduler or campaign DB fails over]
    ROOT --> C2[Kafka unavailable]
    ROOT --> C3[Suppression store down]
    ROOT --> C4[Abuse loop false positive]
    C1 -->|"blast"| B1[Campaigns due in the gap<br/>start up to ~1 min late]
    B1 -->|"mitigation"| M1[Idempotent start by state CAS,<br/>catch up on the due index]
    C2 -->|"blast"| B2[Suppressions, verdicts and<br/>stats stop being pushed]
    B2 -->|"mitigation"| M2[Pull the store's created_at<br/>index every 2 s, hold canaries,<br/>count bounces locally]
    C3 -->|"blast"| B3[Unsubscribe writes and<br/>filter confirms fail]
    B3 -->|"mitigation"| M3[Ingest publishes to the topic,<br/>positives held, replay later]
    C4 -->|"blast"| B4[A good sender's campaign<br/>paused for minutes]
    B4 -->|"mitigation"| M4[Customer notified, one-click review,<br/>remaining rows unrendered]

    class ROOT,C1,C2,C3,C4 service
    class B1,B2,B3,B4 decision
    class M1,M2,M3,M4 service

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

## D12. Rollout / migration

From static per-domain MTA configs and nightly bounce processing to the design in solution §6. Every phase has a per-pool or per-feature flag as its rollback point; phases 1 to 3 change no sending behaviour.

```mermaid
%% D12: migration phases. Rollback points are the flags named in each task. No colons in task names.
gantt
    title Migration to adaptive, provider-keyed sending
    dateFormat YYYY-MM-DD
    axisFormat %b %d
    section Observe
    Provider keys and per-key metrics in shadow     :p1, 2027-01-11, 14d
    Buddy id replication and send-lease registry    :p0, 2027-01-11, 21d
    Quota service in observe mode vs static configs :p3, after p1, 14d
    section Suppression
    Stream and MTA filter in log-only mode          :p2, 2027-01-11, 10d
    Enforce pre-SMTP check, flag per pool           :p2b, after p2, 7d
    section Throttling
    Adaptive throttling on one shared B pool        :p4, after p3, 7d
    All shared pools, then dedicated pools          :p4b, after p4, 21d
    section Pacing and abuse
    Dispatcher credit for new campaigns             :p5, after p4b, 14d
    Streaming abuse loop and canary alert-only      :p6, after p2b, 14d
    Auto-pause on, old static path removed          :p6b, after p5, 7d
```

Rollback per phase: shadow phases have nothing to roll back; enforcement and throttling flip back to the old path per pool by flag, and the MTAs keep both code paths until the last task; the dispatcher can be bypassed per campaign, which falls back to render-as-fast-as-possible. Avoid starting any phase in the six weeks before Black Friday: that window is for warming IPs, not for changing how they are driven.
