# Diagrams: employee identity + integration platform

The D1 to D12 set from `hld/CLAUDE.md` §4. Diagrams already in [`solution.md`](solution.md) are listed with a pointer, not pasted twice. Every diagram below adds a zoom-in or a path that `solution.md` does not draw. Numbers match `solution.md` and [`research/facts-survey.md`](research/facts-survey.md). New numbers are marked [estimate].

| # | Diagram | Where |
|---|---|---|
| D1 | Context | below |
| D2 | Data flow | below |
| D3 | Component architecture | Zoom-out: `solution.md` §6 (dispatcher in red). Growth steps: §4.1 to §4.4. One call through the buckets: §5.3. Zoom-ins below: D3a control plane, D3b one engine process, D3c credential path |
| D4 | Happy path per FR | In `solution.md`: FR2 title change §4.2, FR3 reconcile §4.3. FR1 connect: D3a. Below: D4a FR2 hire, D4b FR2 termination, D4c FR4 event out, D4d FR4 webhook in, D4e FR5 retry and re-authorize |
| D5 | Failure paths | In `solution.md`: crash after create §10.4 A, 2-hour app outage §10.4 B. Below: D5a zombie worker, D5b revoked grant, D5c partition takeover, D5d empty list |
| D6 | Decision flow | Create decision: §5.2. Below: D6a render, diff, apply, D6b `classify`, D6c the guard |
| D7 | Entity relationship | Hot tables: §3.3. Below: the full set, with partner subscriptions and the inbox |
| D8 | State machines | Below: D8a link state, D8b connection status, D8c task lifecycle, D8d guard hold |
| D9 | Deployment / topology | below |
| D10 | Scaling / partitioning | below |
| D11 | Failure mode map | Table: §5.8. Tree below |
| D12 | Rollout / migration | below |

## D1. Context (zoom-out)

The platform as one box. Traffic is small, about 115 calls a second. What binds is the quota on the right, which other companies own.

```mermaid
%% D1: the platform as one box, every actor around it. Grey = outside our trust boundary.
flowchart LR
    HR[HR admins, HR API,<br/>bulk imports] -->|"hires, edits, terminations<br/>~685k changes/day, ~170/s in an import"| IP[Integration platform<br/>identity, planner, dispatcher,<br/>workers, reconciler, console]
    IT[IT admins<br/>console] -->|"connect, rules, preview,<br/>approve holds, retry"| IP
    T46[Termination orchestrator<br/>problem 46] -->|"termination, SSO cut first"| IP
    IP -->|"per-app done, or blocked:<br/>needs re-auth"| T46
    IP -->|"create, update, deactivate, list<br/>~10 M calls/day, ~115/s avg, ~1,500/s peak"| APPS[Third-party apps<br/>600+ connectors, ~750k connections]
    APPS -->|"webhooks ~1 M/day,<br/>hints to re-read"| IP
    IP -->|"consent, token refresh<br/>~1.5 M/day"| AUTH[App OAuth servers]
    IP -->|"signed thin events ~1.4 M/day,<br/>delivered by problem 58"| PE[Partner and customer<br/>endpoints]
    PE -->|"scoped reads of current state<br/>~1.4 M/day"| IP
    IP -->|"wrap, unwrap tenant DEKs"| KMS[Regional KMS]
    IP -->|"pages, status banner"| OC[On-call, status page]
    class HR,IT,T46,OC client
    class IP service
    class APPS,AUTH,PE,KMS external
    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

## D2. Data flow (DFD)

Inputs to outputs, with format, size and rate. Rounded boxes are processes, cylinders are stores.

```mermaid
%% D2: data flow with sizes and rates. Rates from solution 2 and the corrections. Sizes new here are estimates.
flowchart TD
    ADM(Admins and HR API) -->|"employee edit, JSON ~2 KB<br/>~685k/day, ~8/s avg, ~170/s import"| ID(Identity service)
    ID -->|"row, version ~2 KB, outbox row<br/>1 txn, ~1.4 GB/day"| IDB[(Identity DB)]
    IDB -->|"outbox relay, thin event ~1 KB<br/>employee or entity, ids, version,<br/>field names, ~0.7 GB/day"| K[(Kafka<br/>employee-changes)]
    K -->|"64 partitions, key tenant and employee"| PL(Planner)
    PL -->|"task upsert ~200 B<br/>~3 M/day, ~700/s in an import"| PDB[(Provisioning DB<br/>tasks, links, attempts<br/>~5,000 to 6,000 writes/s peak)]
    ADM -->|"config JSON ~10 KB, ~1,000 edits/day<br/>retry, skip, approve"| API(Integration API<br/>admin and partner)
    API -->|"enable: 1,000-row batches<br/>~100k rule-change tasks/day"| PDB
    PDB -->|"ready rows, leases<br/>~1,500 grants/s peak"| ENG(Engine: dispatcher,<br/>workers, reconciler)
    ENG -->|"link ~400 B + attempt ~300 B per call<br/>~3 GB/day of attempts"| PDB
    ENG -->|"read employee ~5 KB per task<br/>~50/s avg, ~900/s peak"| IDB
    ENG -->|"capability ~300 B, token back"| CRED(Credential service)
    CRED -->|"refresh grant ~1 KB<br/>~1.5 M/day, ~100/s peak"| APP[Third-party apps]
    ENG -->|"SCIM or REST JSON ~1 to 3 KB<br/>~10 M/day incl. ~1 M delta polls"| APP
    APP -->|"list pages ~40 KB avg, up to ~1 MB<br/>~3 M/day, ~120 GB/day"| ENG
    APP -->|"webhook JSON ~2 KB, ~1 M/day"| RX(Webhook receiver)
    RX -->|"inbox row ~200 B, observe task<br/>~0.3 M re-reads/day"| PDB
    K -->|"same thin events"| PUB(Event publisher)
    PUB -->|"signed thin event ~500 B<br/>~1.4 M/day via problem 58"| PE[Partner endpoints]
    PE -->|"GET employee, ~2 KB back<br/>~1.4 M/day"| API
    PDB -->|"attempt partitions over 90 days<br/>~0.6 GB/day compressed"| ARC[(Object storage<br/>7 years)]
    class ADM client
    class ID,PL,API,ENG,CRED,RX,PUB service
    class IDB,PDB,ARC store
    class K queue
    class APP,PE external
    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

Reconcile is ~30% of calls but most of the bytes: ~120 GB a day of list pages against ~20 GB of change calls [estimate, ~40 objects of ~1 KB per page]. The task row carries no employee values. Peak reads: ~1,500 calls/s at ~1.6 calls per task is ~900 tasks/s [estimate].

## D3. Component architecture

The zoom-out is the final design in `solution.md` §6, with the dispatcher in red. Three zoom-ins follow.

### D3a. Control plane: connect, plan, enable

```mermaid
%% D3a: connect, plan, enable. Red = the dispatcher: plan reads spend the same quota as live work, so they take lane-3 tokens like a reconcile.
flowchart LR
    ADM[IT admin console] -->|"connect, config If-Match,<br/>approve plan and its count"| API[Integration API<br/>tenant from session, audited]
    API -->|"redirect, narrowest scopes"| AUTH[App OAuth server]
    AUTH -->|"code, exchanged once"| CRED[Credential service]
    CRED -->|"wrapped tokens, cred_version 1"| CS[(CREDENTIAL)]
    API -->|"rules, mappings, policies<br/>config_version 8"| CFG[(CONNECTION +<br/>config versions)]
    API -->|"start plan, or preview a rule edit"| WF[Temporal workflow<br/>plan, wait, enable]
    WF -->|"run"| PJ[Plan job<br/>match, diff, no writes]
    PJ -->|"list pages"| DSP[Dispatcher<br/>lane-3 tokens]
    DSP -->|"paged reads only"| APP[App API]
    PJ -->|"creates, links by match,<br/>conflicts, 0 deactivations"| PLN[(Plan result)]
    WF -->|"enable if still config 8: links,<br/>tasks lane 3, approved count"| LT[(ACCOUNT_LINK +<br/>SYNC_TASK)]
    WF -.->|"409 config_changed"| CFG
    class ADM client
    class API,CRED,WF,PJ service
    class CS,CFG,PLN,LT store
    class DSP critical
    class AUTH,APP external
    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

The plan is a preview, not a script: tasks re-render when they run, and a first connect never deactivates. The count the admin approves is what batch admission (D6c) later allows, plus 10%. §4.1 draws the plan job calling the app directly. Here it goes through lane 3: on GitHub a 20,000-person plan is ~110 list pages of the 5,000-an-hour window.

### D3b. One engine process

16 processes. Each holds 4 of the 64 dispatcher partitions and a 500-slot async worker pool.

```mermaid
%% D3b: inside one engine process. Red = the dispatcher: it alone decides which waiting call gets the next token for ~47k connections.
flowchart LR
    LS[(Partition lease<br/>~10 s, partition epoch)] -->|"owns 4 of 64 partitions"| DSP
    PL[Planner] -->|"lane-0 nudge"| DSP
    PDB[(Provisioning DB, 4 shards<br/>SYNC_TASK, CONNECTION)] -->|"ready rows by lane, risk,<br/>ready_at, 200 ms poll"| DSP[Dispatcher, ~47k connections<br/>lanes, reserve, DRR, breakers]
    DSP -->|"1 token from each bucket"| BK[Buckets by vendor scope key<br/>fixed window from headers,<br/>or refilling, in memory]
    DSP -->|"app-wide tokens, lane passed,<br/>~1 s batches"| RD[(Redis app-wide buckets<br/>20 pct lane-0 reserve,<br/>10 pct per tenant)]
    DSP -->|"lease if partition epoch current,<br/>epoch from shard sequence, 60 s"| PDB
    DSP -->|"task + signed capability<br/>adaptive cap + 1 lane-0 slot,<br/>app 125, tenant 10, lane 0 25 of 500"| POOL[Async worker pool<br/>500 slots]
    POOL -->|"outcome class, slot freed"| DSP
    POOL -->|"read employee at<br/>want_version or later"| IDB[(Identity DB replica)]
    POOL -->|"one instance per task"| CN[Connector<br/>this connection only]
    CN -->|"capability"| CRED[Credential service]
    CN -->|"SCIM or REST, 30 s timeout"| EG[Egress proxy<br/>fixed IPs, host allowlist]
    EG -->|"HTTPS"| APP[App API]
    APP -.->|"429, Retry-After,<br/>remaining, reset"| BK
    POOL -->|"renew before each call, heartbeat 10 s,<br/>one fenced txn: link and complete"| PDB
    class PL,POOL,CN,CRED,EG service
    class LS,PDB,IDB store
    class BK,RD cache
    class DSP critical
    class APP external
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef cache    fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

- `750k / 64 ≈ 11.7k` connections per partition, ~47k per process. Fleet caps per process: 25% per app is 125 slots, 2% per tenant is 10, and 5% reserved for lane 0 is 25.
- The per-connection in-flight cap is `ceil(learned_rate x mean latency)`, minimum 2, starting at 4, plus 1 spare slot only lane 0 may use. Little's law uses the mean: Google's ~40/s at ~0.6 s needs ~25 in flight. A p50-based cap (~0.3 s) would give 12 and run Google at about half its quota.
- A missing Redis key starts at 0, never full. Without Redis, each partition takes a static 1/64 of an app-wide limit.

### D3c. Credential path

```mermaid
%% D3c: how a worker gets a token. Red = the refresh: under rotation, a second refresher presents an already-rotated token and the provider may revoke the grant (RFC 9700 4.14.2).
flowchart LR
    W[Worker + connector<br/>capability from the dispatcher:<br/>tenant, connection, task, epoch, 60 s] -->|"token request + capability"| CRED[Credential service, 3 replicas<br/>checks signature, expiry,<br/>connection.tenant = cap.tenant]
    CRED -->|"hit, until 5 min before expiry"| TC[(Access token cache<br/>per connection)]
    CRED -->|"miss: read row"| CR[(CREDENTIAL<br/>wrapped DEK, ciphertext,<br/>cred_version)]
    CRED -->|"unwrap tenant DEK"| KMS[Regional KMS key]
    CRED -->|"expiring"| SF[Single-flight refresh<br/>60 s lease on the row,<br/>20 s token call, others wait]
    SF -->|"refresh_token grant"| TE[App token endpoint]
    TE -->|"new access token,<br/>rotated refresh token"| SF
    SF -->|"CAS cred_version 4 to 5,<br/>store before use"| CR
    SF -->|"invalid_grant"| AD[Auth-anomaly detector<br/>max of 2 pct and 10 connections<br/>of an app in 10 min pages]
    CRED -->|"access token, this connection only"| W
    W -->|"Bearer token"| EG[Egress proxy] -->|"HTTPS from fixed IPs"| APP[App API]
    class W,CRED,AD,EG service
    class TC cache
    class CR store
    class SF critical
    class KMS,TE,APP external
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef cache    fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

No API returns a refresh token. Google keeps 100 refresh tokens per account per client and silently drops the oldest, so the code exchange runs once per connection, never per worker. The manifest says `refresh_rotation: none | strict | grace(seconds)`. Residual risk on `strict`: a crash after the token endpoint answers but before the CAS write loses the rotated token. That is one `NEEDS_REAUTH`, counted as its own metric.

## D4. Happy paths, one per FR

### D4a. FR2: a hire starting Monday, provisioned on Friday

```mermaid
%% D4a: hire with provision_lead 3 days. The worker re-arms a task that is not due. Created suspended with pinned keys, activated at the start instant.
sequenceDiagram
    autonumber
    participant HR as HR admin
    participant ID as Identity service
    participant PL as Planner
    participant TS as Task store
    participant W as Worker
    participant G as Google Directory
    HR->>ID: Tuesday, hire Ana, start Monday 09:00
    ID->>PL: v1 via outbox and Kafka, key tenant and ana
    PL->>TS: upsert google ana, want 1, lane 1, reasons hire, ready now
    TS->>W: leased, epoch 9001
    W->>W: render as of DB clock, not due until Friday 09:00
    W->>TS: re-arm ready_at to Friday 09:00, start minus provision_lead
    TS->>W: Friday 09:00, leased, epoch 9188
    W->>TS: link CREATING, create_keys userName and externalId, create_started_at
    W->>G: users.insert, primaryEmail, externalIds ana, suspended true, no manager yet
    G-->>W: 201, id 1177
    W->>TS: one fenced txn, link PRESENT, id 1177, re-arm Monday 09:00
    ID->>PL: Monday 09:00, v2 committed at the effective instant
    PL->>TS: upsert google ana, want 2
    W->>G: PATCH suspended false, manager filled in, 200
```

Group tasks for `eng` and `all-staff` add Ana once her link exists. Google allows at most 10 user creates per domain per second, so a 5,000-person hiring wave takes at least 8.3 min there.

### D4b. FR2: a termination at 17:00

```mermaid
%% D4b: termination in lane 0. Reserve token and slot, renew before the call, verify written before the call, one fenced transaction.
sequenceDiagram
    autonumber
    participant ID as Identity service
    participant PL as Planner
    participant TS as Task store
    participant D as Dispatcher
    participant W as Worker
    participant S as Slack SCIM
    Note over ID,TS: 16:00 pre-flight on all 11 connections, 16:55 again for apps where Ana is an admin
    ID->>ID: 17:00:00, v58 committed at the effective instant, terminated, SSO cut first
    ID->>PL: ana v58, key tenant and ana
    PL->>D: 11 upserts, lane 0, risk set, reasons termination, ready now, nudge
    D->>W: lease slack ana, epoch 9107, reserve token, lane-0 slot
    W->>ID: read ana at v58 or later
    W->>W: render active false. Terminated in the render, so the guard never holds it
    W->>TS: renew if epoch 9107 and 30 s left, write row verify-ana due 17:05
    W->>S: PATCH Users id, active false
    S-->>W: 200, about 2 s after 17:00
    W->>TS: one fenced txn, link DEACTIVATED v58, complete if epoch and dirty_gen match
    W->>S: 17:05 verify, GET Users id
    S-->>W: active false, observed_hash and observed_at written
```

- The other 10 apps run the same path in parallel. On each connection the employee who owns its OAuth grant goes last, after admins and production access.
- The verify task has its own key, subject `verify:<employee_id>`. On the deactivation's own row it would bump `dirty_gen`, fence the completion, and the `LEAST` rule would make it due at once: replayed in SQLite, that version ran the verify at ~17:00, not 17:05.

### D4c. FR4: an event out to a partner

```mermaid
%% D4c: thin event, signed per Standard Webhooks, partner reads current state with its own scopes.
sequenceDiagram
    autonumber
    participant K as Kafka
    participant PUB as Event publisher
    participant WD as Webhook delivery, problem 58
    participant P as Partner endpoint
    participant PA as Partner API
    K->>PUB: ana v42, changed title, manager_id
    PUB->>PUB: subscriptions for employee.updated, drop field names the scopes hide
    PUB->>WD: evt_9f2, employee.updated, v42, changed title
    WD->>WD: HMAC over msg_id.timestamp.payload
    WD->>P: POST, webhook-id, webhook-timestamp, webhook-signature
    P->>P: verify, timestamp within 5 min, dedup by id
    P-->>WD: 200
    P->>PA: GET employees ana, OAuth token with scopes
    PA-->>P: allowed fields only, version 42 or later
    P->>P: keep the highest version, ignore older events
    Note over WD,P: on failure, retries for up to 3 days, then the endpoint is disabled and its owner emailed
```

### D4d. FR4: a webhook in from an app

```mermaid
%% D4d: an app webhook is a hint. Deduped, acked fast, it only marks an observe task, which reads the app before diffing.
sequenceDiagram
    autonumber
    participant S as Slack
    participant RX as Webhook receiver
    participant INB as Inbox
    participant TS as Task store
    participant W as Worker
    S->>RX: POST user_change for bob, signed
    RX->>INB: signature ok, insert delivery id, on conflict do nothing
    RX-->>S: 200 within 3 s
    RX->>TS: team id to connection c9, upsert bob, lane 2, reasons webhook
    W->>S: reasons include webhook, so GET Users bob first
    S-->>W: title edited in Slack's console
    W->>W: desired differs from observed on a managed field, policy enforce
    W->>S: PATCH title back to the HR value, 200
    W->>TS: observed_hash, observed_at, applied_hash, one fenced txn
    Note over S,INB: a duplicate delivery hits the inbox key, gets 200, nothing else. A lost one is found by the daily reconcile
```

### D4e. FR5: retry after a permanent error, then re-authorize

```mermaid
%% D4e: admin actions are writes to the task or connection row, so the admin reads their own write. The OAuth code is exchanged once.
sequenceDiagram
    autonumber
    participant A as Tenant admin
    participant API as Integration API
    participant AU as App OAuth server
    participant CR as Credential service
    participant PDB as Provisioning DB
    API-->>A: Zoom link ERROR for ana, no licences left on your plan
    A->>API: buys licences, then POST subjects ana retry
    API->>PDB: upsert zoom ana, attempts 0, ready now, reasons admin, new dirty_gen
    API-->>A: 202. Seconds later sync-status says Zoom in sync
    Note over A,PDB: later, GitHub for this tenant is NEEDS_REAUTH
    A->>API: POST connections c9 reauthorize
    API-->>A: authorize_url, narrowest scopes, state
    A->>AU: consent
    AU-->>API: redirect with code and state
    API->>CR: exchange code, once
    CR->>AU: authorization_code grant
    AU-->>CR: access and refresh tokens
    CR->>PDB: wrap with tenant DEK, CAS cred_version 4 to 5
    API->>PDB: NEEDS_REAUTH to ACTIVE, nudge, schedule a reconcile
    Note over PDB: parked rows lease in lane order, lane 0 first
```

## D5. Failure paths

### D5a. A zombie worker, past the renew, caught by the fence and the verify read

```mermaid
%% D5a: worker 1 pauses right after its pre-call renew. A termination takes over its stale lease. Defences from solution 5.1 and corrections C20, C29.
sequenceDiagram
    autonumber
    participant W1 as Worker 1
    participant TS as Task store
    participant W2 as Worker 2
    participant S as Slack SCIM
    W1->>TS: t = 0, lease slack ana, epoch 9040, want 42
    W1->>TS: t = 1 s, renew if epoch 9040 and 30 s left, ok to t = 61 s
    Note over W1,TS: t = 1 s, GC pause for 70 s right after the renew. Heartbeats stop
    TS->>TS: t = 30 s, termination upsert, lane 0, heartbeat 29 s old, takes the lease
    W2->>TS: epoch 9107 from the shard sequence, want 43
    W2->>TS: renew ok, verify task written first
    W2->>S: PATCH active false
    S-->>W2: 200
    W2->>TS: one fenced txn, link DEACTIVATED v43, complete
    W1->>S: t = 71 s, wakes and sends its old PATCH. Title only, never active
    S-->>W1: 200, or 412 where the app has ETags. Account stays inactive
    W1->>TS: fenced txn matches 0 rows, applied_hash NULL, observe task
    W2->>S: verify read, GET Users id
    alt account inactive
        S-->>W2: active false, in sync
    else a write slipped through with active true
        S-->>W2: active true
        W2->>TS: lane-0 task again, page the connector on-call
    end
```

A worker 1 that pauses *before* its renew is stopped by it: the renew matches 0 rows and no call goes out. The renew only narrows the window, so the verify read stays. The verify runs at +5 min on its own key (D4b).

### D5b. A revoked grant, with parked tasks and a termination due

```mermaid
%% D5b: one tenant removes our app from Google. AUTH never counts toward the app breaker, so the other ~20,000 Google connections never notice.
sequenceDiagram
    autonumber
    participant TA as Tenant admin
    participant G as Google
    participant W as Worker
    participant CR as Credential service
    participant PDB as Provisioning DB
    participant T46 as Termination, problem 46
    TA->>G: removes our app from the domain
    W->>G: PATCH user title
    G-->>W: 401
    W->>CR: one refresh, capability
    CR->>G: refresh_token grant
    G-->>CR: invalid_grant. Auth anomaly counts 1, under max of 2 pct and 10
    CR-->>W: AUTH
    W->>PDB: connection NEEDS_REAUTH, task kept, attempts unchanged
    PDB-->>TA: one email, console banner
    Note over W,PDB: the dispatcher skips the connection. New changes coalesce into parked rows
    T46->>PDB: 16:00 pre-flight for a 17:00 termination
    PDB-->>T46: Google blocked, needs re-auth
    T46->>TA: page the admin now, re-authorize with another admin if it is the leaver's grant
    TA->>CR: re-authorizes, see D4e
    PDB->>W: ACTIVE, parked rows lease in lane order, termination first
    W->>G: PATCH suspended true, 200. If nobody acted, evidence says blocked
```

### D5c. A dispatcher partition changes owner

```mermaid
%% D5c: the engine holding partition 17 dies. Ready rows resume after one partition lease. In-flight rows are taken over once their heartbeat is 20 s old, lane 0 first.
sequenceDiagram
    autonumber
    participant P1 as Engine 1, old owner
    participant LS as Partition lease
    participant P2 as Engine 2
    participant TS as Task store
    participant A as App API
    P1->>LS: renew partition 17, partition epoch 4
    Note over P1,LS: t = 0, process killed with 2 lane-0 calls in flight
    P2->>LS: t = 10 s, lease expired, acquire, partition epoch 5
    P2->>TS: load ready rows for ~11.7k connections
    P2->>P2: buckets from learned_rate at half rate, windows from headers
    P2->>A: lane 0 first. Headers correct the buckets within a few calls
    Note over TS: the 2 in-flight lane-0 rows keep engine 1's lease until their heartbeat is 20 s old
    P2->>TS: t = 20 s, take over both, lane 0 first, new epochs from the shard sequence
    P2->>A: set_active false again, same state if it had landed
    A-->>P2: 200
    P1->>TS: if only paused, it wakes and tries to lease a row
    TS-->>P1: refused, partition epoch 4 is not current
```

An unowned partition pages at 30 s. The two terminations land at ~21 s, inside the 60 s target, because the new owner re-leases rows whose heartbeat is older than 20 s, lane 0 first. Waiting for the full 60 s task lease would land them at ~61 s.

### D5d. An empty list, caught by list trust and the batch guard

```mermaid
%% D5d: a reconcile reads 0 accounts for a 3,000-person Slack connection whose last complete count was 3,000. Rules from corrections C6 and C8.
sequenceDiagram
    autonumber
    participant R as Reconciler
    participant S as Slack SCIM
    participant G as Guard
    participant A as Tenant admin
    R->>S: GET Users, every page, lane-3 tokens, at most 10 pct of each bucket
    S-->>R: 0 resources, totalResults 0
    R->>R: equals totalResults, but not within 10 pct of 3,000. Untrusted
    R->>S: GET a sample of 20 missing ids
    alt accounts exist, an admin narrowed our app's scope
        S-->>R: 200 for all 20
        R->>A: alert, the list lied. Nothing concluded
    else 404 for all 20, the accounts are really gone
        S-->>R: 404
        R->>G: one batch, 3,000 re-creates, reasons drift
        G->>G: 3,000 over max of 3 and 60 an hour, hold the whole batch
        G->>A: GUARD_HOLD with config_version and items, samples
        A->>G: reject. It sticks while config_version is current
    end
```

## D6. Decision flows

### D6a. The worker's render, diff, apply loop

```mermaid
%% D6a: one leased task. No red: the risky branch is the guard, drawn in D6c. The create path is solution 5.2 with pinned create_keys.
flowchart TD
    T[Leased task: epoch e, dirty_gen g<br/>read employee at want_version<br/>or later, DB clock as_of] -->|"record"| RN[Render desired as of now<br/>manager not linked: write the rest,<br/>pending_reference]
    RN -->|"desired"| DUE{Due now?}
    DUE -->|"no"| RA[Re-arm ready_at to the next<br/>instant the render changes]
    DUE -->|"yes"| OBS{reasons include drift,<br/>webhook or verify?}
    OBS -->|"yes: GET first,<br/>compare with observed"| K{Desired vs<br/>the app}
    OBS -->|"no: compare<br/>with applied_hash"| K
    K -->|"no account yet"| CR[Create path<br/>search_settle, adopt, 6 rounds]
    K -->|"equal"| FD[One fenced txn: link, attempt,<br/>delete if epoch e and dirty_gen g]
    K -->|"deactivate, delete, re-create,<br/>role or net group removal"| G{Guard allows?<br/>D6c}
    K -->|"attributes differ,<br/>or activate"| PD[Build the call<br/>changed fields only, never active,<br/>If-Match etag]
    G -->|"held"| H[Wait on a GUARD_HOLD]
    G -->|"allowed, or terminated<br/>in the render"| PD
    PD -->|"call ready"| RNW{Renew: epoch e<br/>and 30 s left?}
    RNW -->|"no"| AB[No call, observe task]
    RNW -->|"yes"| CALL[Lane-0 deactivate: verify first.<br/>Call via egress, classify D6b]
    CALL -->|"OK"| FD
    class T,RN,RA,CR,PD,H,AB,CALL service
    class DUE,OBS,K,G,RNW decision
    class FD store
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

A fenced txn that matches 0 rows has two meanings. `dirty_gen` moved: run again at once. The epoch moved: write `applied_hash = NULL` and an observe task. For PUT-only apps, `active` comes from the status re-read at call time.

### D6b. `classify`, and what each class does

```mermaid
%% D6b: every response goes through the connector's classify. TRANSIENT feeds the breakers. THROTTLED feeds the bucket.
flowchart TD
    RSP[Response or timeout] -->|"connector error map"| C{classify}
    C -->|"2xx"| OK[OK<br/>one fenced txn]
    C -->|"5xx, timeout, reset"| TR[TRANSIENT<br/>backoff 30 s x2 to 1 h, full jitter,<br/>budget max of 2 and 20 pct, 72 h,<br/>feeds connection and app breakers]
    C -->|"429, GitHub 403 remaining 0"| TH[THROTTLED<br/>pause until Retry-After or reset,<br/>AIMD, no attempt used]
    C -->|"401, invalid_grant"| AU{One refresh<br/>works?}
    AU -->|"yes"| RT[Retry the call]
    AU -->|"no"| NR[NEEDS_REAUTH<br/>tasks parked, admin told once,<br/>never counts toward app breaker]
    C -->|"400, no licences"| PE[PERMANENT<br/>link ERROR in plain words, no retry<br/>until the input or an admin changes]
    C -->|"404"| NF{Desired state<br/>still has the account?}
    NF -->|"yes"| RC[Re-create through the guard]
    NF -->|"no"| DL[Link DELETED, done]
    C -->|"409"| CO[CONFLICT<br/>find by pinned create_keys, adopt,<br/>else CONFLICT for the admin]
    C -->|"412"| ST[STALE<br/>re-read, re-diff, retry at once]
    class RSP,OK,TR,TH,RT,NR,PE,RC,DL,CO,ST service
    class C,AU,NF decision
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

The app breaker trips on the app-wide rate: 50% `TRANSIENT` over at least 200 calls in 2 min. A connection breaker opens on 3 `TRANSIENT` in a row, or 50% of at least 20 in 2 min. A `404` on a deactivate or delete means the account is already gone.

### D6c. The mass-change guard

```mermaid
%% D6c: the guard reads the current render, not reasons. Rules from corrections C4 to C7. No red: this is the backstop for our own bugs.
flowchart TD
    OP[Deactivate, delete, re-create,<br/>admin-role or net group removal] -->|"render"| C1{Employee terminated<br/>in the current render?}
    C1 -->|"yes"| PASS[Run, never held. HR needs a second<br/>approver above max of 20 and 5 pct an hour]
    C1 -->|"no"| RJ{Rejected at this<br/>config_version?}
    RJ -->|"yes"| REF[Refused, rejection sticks]
    RJ -->|"no"| C2{Part of a batch: rule edit,<br/>reconcile, import, release?}
    C2 -->|"yes"| BA{Whole count over max of 3<br/>and 2 pct, and over the<br/>previewed count + 10 pct?}
    C2 -->|"no, one at a time"| C3{Over max of 3 and 2 pct an hour,<br/>or max of 10 and 5 pct a day?}
    BA -->|"no"| RUN[Run]
    C3 -->|"no"| RUN
    BA -->|"yes: hold all of it"| HOLD[GUARD_HOLD with config_version<br/>and items. Others flow]
    C3 -->|"yes"| HOLD
    HOLD -->|"counted"| FL[Fleet detector: holds from over 20<br/>tenants in 10 min, or a connector at 3x<br/>its baseline: page, freeze its counted ops]
    HOLD -->|"admin decides"| APR[Approve: ready now,<br/>re-rendered as of now]
    class OP,PASS,REF,RUN,HOLD,FL,APR service
    class C1,RJ,C2,BA,C3 decision
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

`reasons` only labels a hold's cause. Reactivation is never caused by drift or reconcile, only by an identity change newer than the deactivation. Provisioning pages the identity team if it sees more new terminations than the HR threshold without a `bulk_action_id`.

## D7. Entity relationship

`solution.md` §3.3 has the hot tables. This is the full set, including partner subscriptions and the inbox. Columns already in §3.3 are not repeated, except keys and the task row. Keys lead with `tenant_id`. `CONNECTOR`, `CONNECTION_CONFIG`, `GROUP_MEMBER`, `OUTBOX`, `EVENT_SUBSCRIPTION` and `INBOX` are new here.

```mermaid
%% D7: full schema. EMPLOYEE and OUTBOX live in the Identity DB. The rest is in the Provisioning DB, sharded by hash of tenant_id over 4 shards. ATTEMPT is partitioned by day.
erDiagram
    CONNECTOR ||--o{ CONNECTION : "installed as"
    CONNECTION ||--o{ CONNECTION_CONFIG : "versions"
    CONNECTION ||--|| CREDENTIAL : "authenticates with"
    CONNECTION ||--o{ ACCOUNT_LINK : "owns"
    EMPLOYEE ||--o{ ACCOUNT_LINK : "has accounts"
    CONNECTION ||--o{ GROUP_MEMBER : "memberships we added"
    CONNECTION ||--o{ SYNC_TASK : "pending work"
    CONNECTION ||--o{ GUARD_HOLD : "may pause"
    GUARD_HOLD ||--o{ GUARD_HOLD_ITEM : "holds"
    ACCOUNT_LINK ||--o{ ATTEMPT : "audited by"
    EMPLOYEE ||--o{ OUTBOX : "one row per commit"
    OUTBOX }o--o{ EVENT_SUBSCRIPTION : "fans out to, same tenant"
    CONNECTION ||--o{ INBOX : "app deliveries for"
    CONNECTOR {
        string connector_id PK "slack, google, github"
        int version PK "manifest: limits, scope keys, refresh_rotation, search_settle"
    }
    CONNECTION {
        uuid tenant_id PK
        uuid connection_id PK
        string status "DRAFT, ACTIVE, PAUSED, NEEDS_REAUTH, QUARANTINED, DISABLED"
        int connector_version "canary pin"
        string owner "v1 or v2 during migration"
    }
    CONNECTION_CONFIG {
        uuid tenant_id PK
        uuid connection_id PK
        int config_version PK "If-Match on edit"
        json rules_mappings_policies "enforce or report per attribute, provision_lead"
    }
    ACCOUNT_LINK {
        uuid tenant_id PK
        uuid connection_id PK
        uuid employee_id PK
        string state "CREATING, PRESENT, SUSPENDED, DEACTIVATED, DELETED, CONFLICT, IGNORED, ERROR"
        bool pending_reference
        json create_keys "userName, externalId pinned by the intent"
        timestamp create_started_at
        timestamp observed_at "with observed_hash"
    }
    GROUP_MEMBER {
        uuid tenant_id PK
        uuid connection_id PK
        uuid group_id PK
        uuid employee_id PK "about 300 M rows of about 100 B"
    }
    SYNC_TASK {
        uuid tenant_id PK
        uuid connection_id PK
        string subject PK "employee or group id"
        bigint want_version "GREATEST on upsert"
        smallint lane "0 to 3, LEAST on upsert"
        smallint risk "admin, production access, grant owner last"
        string reasons "hire, edit, termination, rule, release, drift, webhook, verify, delete_timer, admin"
        bigint dirty_gen "shard sequence, every upsert"
        timestamp ready_at
        int attempts
        string lease_owner
        bigint lease_epoch "shard sequence"
        timestamp lease_until
    }
    GUARD_HOLD {
        uuid tenant_id PK
        uuid hold_id PK
        int config_version "a rejection sticks while current"
        string cause "rule, release, reconcile, import, unexplained"
        string status "OPEN, APPROVED, REJECTED"
    }
    GUARD_HOLD_ITEM {
        uuid hold_id PK
        string subject PK
        string op PK "deactivate, delete, recreate, remove_group, remove_admin"
    }
    EMPLOYEE {
        uuid tenant_id PK
        uuid employee_id PK
        bigint version "new version at every effective instant"
    }
    OUTBOX {
        bigint outbox_id PK
        string kafka_key "tenant_id and employee_id"
        string changed_fields "names, no values, purged after 7 days"
    }
    EVENT_SUBSCRIPTION {
        uuid tenant_id PK
        uuid endpoint_id PK
        uuid client_id "partner OAuth client, its scopes filter field names"
        string secret_ref "old secret valid 24 h on rotation"
        string status "ACTIVE, DISABLED after 3 days failing"
    }
    INBOX {
        string source PK "slack, okta, google, github"
        string delivery_id PK "the app's own id, TTL 7 days"
    }
```

- A membership an app admin added by hand is not in `GROUP_MEMBER`, so we never remove it.
- `CREDENTIAL` sits in its own schema that only the credential service's role can read. Event and delivery rows belong to #58.
- The 7-day outbox purge and inbox TTL are [estimate]. They only need to outlast the senders' retries (Slack 3, Okta at most 1) and Kafka's 7-day retention.

## D8. State machines

### D8a. `ACCOUNT_LINK.state`

```mermaid
%% D8a: one link per connection and employee. Accounts created suspended before the start date go straight to SUSPENDED. pending_reference is a flag on PRESENT.
stateDiagram-v2
    direction LR
    [*] --> CREATING: intent committed
    [*] --> Exists: matched at enable
    CREATING --> Exists: 201 or adopted
    state "Account exists" as Exists {
        direction TB
        [*] --> PRESENT
        PRESENT --> SUSPENDED: leave, pre-start
        SUSPENDED --> PRESENT: start date
    }
    Exists --> DEACTIVATED: termination
    DEACTIVATED --> Exists: rehire, reactivate
    DEACTIVATED --> DELETED: 30 days later
    DELETED --> CREATING: rehire, new account
    Exists --> CREATING: 404, still in scope
    state "Waits on an admin" as Human {
        direction TB
        CONFLICT
        ERROR
        IGNORED
    }
    CREATING --> CONFLICT: not ours, or inactive
    CONFLICT --> Exists: admin links it
    CREATING --> ERROR: PERMANENT
    Exists --> ERROR: PERMANENT, or 72 h
    ERROR --> CREATING: retry, no account
    ERROR --> Exists: retry, input fixed
    Exists --> IGNORED: admin skips
    IGNORED --> DEACTIVATED: termination
```

- An `IGNORED` link skips updates but is still deprovisioned. A termination on a `CREATING` link runs the same find-and-wait first.
- A rehire reuses the old account if the app still has it. A *new* employee with a reused email never adopts it, and no inactive account is ever auto-adopted: `CONFLICT`.

### D8b. `CONNECTION.status`, with the connection breaker inside `ACTIVE`

```mermaid
%% D8b: connection status. The connection breaker lives inside ACTIVE. Quarantine probes at 6 h, 12 h, 24 h, then daily.
stateDiagram-v2
    direction LR
    [*] --> DRAFT: POST connection
    DRAFT --> ACTIVE: plan enabled
    state ACTIVE {
        direction TB
        [*] --> Closed
        Closed --> Open: 3 in a row, or 50 pct
        Open --> HalfOpen: cool-down 30 s to 15 min
        HalfOpen --> Closed: probe ok, ramp
        HalfOpen --> Open: probe fails
    }
    ACTIVE --> PAUSED: admin pauses
    PAUSED --> ACTIVE: admin resumes
    ACTIVE --> NEEDS_REAUTH: refresh fails
    NEEDS_REAUTH --> ACTIVE: re-authorized
    ACTIVE --> QUARANTINED: failing for a day
    QUARANTINED --> ACTIVE: probe ok
    QUARANTINED --> DISABLED: 28 days
    ACTIVE --> DISABLED: admin disconnects
    DISABLED --> [*]
```

- `PAUSED` stops lanes 1 to 3. Lane 0 still runs.
- The app breaker sits above this, on the app-wide error rate (D6b). On close, the app's rows in transient backoff become due, lane 0 first (skipping the ramp, not the 10x ceiling) and lanes 1 to 3 on a ramp. More than 3 apps' breakers opening within 2 min pages the platform team: suspect our egress.

### D8c. The task lifecycle

```mermaid
%% D8c: one SYNC_TASK row. Waiting, Ready, Leased, Parked and Held are derived from ready_at, lease columns and connection status, not stored.
stateDiagram-v2
    direction LR
    [*] --> Waiting: upsert, due later
    [*] --> Ready: upsert, due now
    Waiting --> Ready: due, or higher lane
    Ready --> Parked: breaker, AUTH, 429
    Parked --> Ready: closed, re-auth, tokens
    Ready --> Leased: epoch from shard seq
    Leased --> Leased: lane-0 takeover
    Leased --> Done: fenced txn, same gen
    Leased --> Ready: dirtied again
    Leased --> Waiting: backoff, or re-arm
    Leased --> Held: guard
    Held --> Ready: admin approves
    Held --> Done: admin rejects
    Leased --> Done: PERMANENT, 72 h
    Done --> [*]
```

Every upsert takes a new `dirty_gen`, so a second dirtying during a run is never swallowed. A same-lane upsert with `attempts = 0` takes the earlier `ready_at`. A lane-0 upsert may take over a lease whose heartbeat is older than 20 s. Given-up rows leave the link in `ERROR`, and the daily re-render brings them back.

### D8d. `GUARD_HOLD.status`

```mermaid
%% D8d: a hold never approves itself. A rejection sticks until the connection's config_version changes. The fleet freeze is global and not a hold state.
stateDiagram-v2
    direction LR
    [*] --> OPEN: batch or window over
    OPEN --> OPEN: more ops join
    OPEN --> APPROVED: admin approves
    OPEN --> REJECTED: admin rejects
    APPROVED --> [*]: tasks re-rendered
    REJECTED --> [*]: config_version changes
```

## D9. Deployment / topology

Each region is a full cell for its tenants. Only database replication crosses a region boundary.

```mermaid
%% D9: one home region over 3 AZs plus its paired DR region. 16 engines split 6, 5, 5. Each Postgres shard has two standbys in other AZs with quorum commit (ANY 1), so losing one standby never stalls commits.
flowchart LR
    subgraph RA[Home region, one full cell]
        subgraph Z1[AZ 1]
            E1[Engine x6, 24 partitions<br/>3,000 slots, credential svc]
            D1[(PG primaries, shards 1 and 2<br/>Kafka broker, Redis primary)]
            X1[Egress proxy x3<br/>fixed IPs]
        end
        subgraph Z2[AZ 2]
            E2[Engine x5, 20 partitions<br/>2,500 slots, credential svc]
            D2[(PG primaries, shards 3 and 4<br/>standbys 1 and 2, Kafka broker)]
            X2[Egress proxy x3<br/>fixed IPs]
        end
        subgraph Z3[AZ 3]
            E3[Engine x5, 20 partitions<br/>2,500 slots, credential svc]
            D3[(PG standbys 3 and 4<br/>Kafka broker, Redis replica)]
            X3[Egress proxy x3<br/>fixed IPs]
        end
    end
    KMS[Regional KMS key]
    APPS[Third-party apps<br/>allowlist both regions' IPs]
    DR[(Paired DR region<br/>async replicas, own KMS key,<br/>own egress IPs, cold engines)]
    D1 -->|"sync replication"| D2
    D2 -->|"sync replication"| D3
    E1 -->|"tasks, leases on any shard"| D2
    E1 -->|"calls"| X1
    E2 -->|"calls"| X2
    E3 -->|"calls"| X3
    X1 & X2 & X3 -->|"HTTPS"| APPS
    E3 -->|"unwrap DEKs"| KMS
    D2 -.->|"async, Identity and Provisioning DB,<br/>RPO seconds, crosses the region"| DR
    class E1,E2,E3,X1,X2,X3 service
    class D1,D2,D3,DR store
    class KMS,APPS external
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

- **AZ loss.** Losing AZ 1 takes 6 engines and 2 shard primaries. Partitions move in ~10 s, standbys promote in ~30 s. 10 engines leave 5,000 slots, 4.5x the ~1,100 in flight at peak. Kafka keeps writing on 2 of 3 replicas.
- **Region loss.** The new primary's identity version is the truth: tasks reset `want_version` to it. A change that would reactivate an account whose `applied_version` is newer than the identity version is held for HR review. Terminations from the last 24 h get lane-0 tasks again, and every connection reconciles within 6 h. Both regions' egress IPs are published from day one. Kafka and Redis are rebuilt, not replicated.
- The 6, 5, 5 split is [estimate]. Each DEK is wrapped twice, under the home region's KMS key and the DR region's, because a DEK wrapped only at home cannot be unwrapped in DR. DR drills decrypt from the second region.

## D10. Scaling / partitioning

Tenant for data, employee for change events, the vendor's scope for dispatch, and one shared key per app for app-wide quota.

```mermaid
%% D10: partition keys. Red = the app-wide bucket: the one piece of dispatcher state that cannot be partitioned. One Redis key per app serves every partition.
flowchart LR
    TD[Tenant directory<br/>hash of tenant_id,<br/>overrides for the largest] -->|"tenant to shard"| SH[(4 Postgres shards<br/>~1,500 writes/s each at peak)]
    BIG[Largest tenant<br/>50k employees, ~0.5 M links] -->|"pinned"| SH
    KF[(Kafka, 64 partitions<br/>key tenant and employee)] -->|"a 50k import spreads<br/>over all 64"| PLN[Planner, 16-way per<br/>partition, page on lag over 10 s]
    PLN -->|"upserts"| SH
    CN[750k connections] -->|"hash of vendor_scope_key mod 64"| DP[64 dispatcher partitions<br/>~11.7k connections each]
    DP -->|"4 per process"| EN[16 engine processes]
    DP -->|"ready rows from all 4 shards"| SH
    DP -->|"~1 s batches, lane passed"| AB[App-wide bucket, Jira<br/>65,000 points/h for all tenants,<br/>20 pct lane-0 reserve]
    IMP[One tenant's Jira import] -->|"at most 10 pct: ~1.8/s"| AB
    VS[Two connections on one Slack org,<br/>or many on one SCIM host] -->|"same scope key,<br/>same partition, one bucket"| DP
    class TD,PLN,DP,EN service
    class SH,KF store
    class CN,BIG,IMP,VS client
    class AB critical
    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
```

- **Shards by tenant.** Every query is tenant-scoped. The largest tenant is ~0.5% of links, so pinning is for burst isolation (a 50k connect), not size. A partition reads all 4 shards, so a shard failover pauses ~1/4 of every partition.
- **Kafka by tenant and employee.** One tenant's import no longer queues ahead of ~780 other tenants' terminations. Per-employee order still holds.
- **The app-wide bucket.** `65,000 / 3,600 ≈ 18` points/s for every Jira tenant together. The 10% tenant share makes a 20,000-create Jira import ~3 h [estimate, 1 point per call].
- **Partitions by vendor scope.** `vendor_scope_key` (installation, org or account id, or the target host for generic SCIM) picks the partition. Connections that share one vendor quota share one owner and one exact in-memory bucket. A tenant's 15 connections still spread over ~15 partitions.

## D11. Failure mode map

One tree. Each leaf is a failure and its mitigation. The blast radius is on the arrow.

```mermaid
%% D11: red = a dispatcher bug, the one failure that reaches every tenant on an app at once. The other global failures are caught by detectors that look across tenants.
flowchart LR
    ROOT[Platform] -->|"every tenant on an app:<br/>429s, ban risk, lane 0 stuck"| F1[Dispatcher bug in lanes or buckets<br/>slot caps, learned rates, page at 5 pct 429s]
    ROOT -->|"4 partitions ~10 s,<br/>in-flight rows ~20 s"| F2[Engine process dies<br/>partition epoch, takeover at half rate]
    ROOT -->|"~1/4 of tenants, ~30 s"| F3[DB shard loses primary<br/>sync standby, planner retries]
    ROOT -->|"new changes wait"| F4[Kafka down<br/>outbox keeps them, relay catches up]
    ROOT -->|"app-wide quota apps slower"| F5[Redis down<br/>static 1/64 per partition]
    ROOT -->|"after cached tokens expire"| F6[Credential service down<br/>3 replicas, tokens last ~55 min]
    ROOT -->|"tasks wait"| F13[Identity DB down<br/>no renders, replicas drain]
    ROOT -->|"one app, all tenants"| F7[App outage<br/>app breaker, ramp 2x to 10x, ~17 min drain]
    ROOT -->|"one connection"| F8[Grant revoked<br/>NEEDS_REAUTH, parked, pre-flight]
    ROOT -->|"every tenant on that app"| F9[Our client secret or app suspended<br/>auth anomaly, page, hold emails 1 h]
    ROOT -->|"one connection"| F10[A list lies or is garbage<br/>AND trust rule, sample of 20 GETs]
    ROOT -->|"one connection, or a fleet"| F11[Rule typo or bad release<br/>batch admission, sticky reject, fleet freeze]
    ROOT -->|"several apps at once"| F12[Our egress fails<br/>over 3 app breakers in 2 min pages]
    class ROOT service
    class F2,F3,F4,F5,F6,F7,F8,F9,F10,F11,F12,F13 decision
    class F1 critical
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

Region loss is in D9. The outage drain is ~70k rows under a ceiling that starts at 2x normal and doubles every 2 min up to 10x, with ~10/s of new work still arriving.

## D12. Rollout / migration

From per-connector code in the monolith (v1) to this engine (v2), as in `solution.md` §8. Ownership is a column on `CONNECTION`, so a connection never has two writers. Durations are [estimate], except the two-week shadow.

```mermaid
%% D12: four phases. Each milestone is a rollback point. Cut-over and rollback are per connection, by flag (problem 56).
gantt
    title Migration from v1 connectors to the v2 engine
    dateFormat YYYY-MM-DD
    axisFormat %b %d
    section Phase 1 backfill
    Links from v1 stored external ids            :p1a, 2026-11-02, 14d
    Read-only reconcile fills observed_hash      :p1b, after p1a, 7d
    Rollback point, v2 has written nothing       :milestone, m1, after p1b, 0d
    section Phase 2 shadow
    v2 renders and diffs, connectors in dry run  :p2a, after m1, 14d
    Compare with v1 calls, ticket each mismatch  :p2b, after m1, 21d
    Rollback point, switch shadow off            :milestone, m2, after p2b, 0d
    section Phase 3 cut over
    Generic SCIM apps on small tenants           :p3a, after m2, 21d
    Top 20 connectors                            :p3b, after p3a, 42d
    Google, Microsoft and Slack last             :p3c, after p3b, 28d
    Rollback point per connection, owner flips back :milestone, m3, after p3a, 0d
    section Phase 4 retire
    v1 read-only, owner flips still possible     :p4a, after p3c, 30d
    v1 code deleted                              :milestone, m4, after p4a, 0d
```

Rollback is flipping `CONNECTION.owner` back. v2 records only what it applied, and v1 resumes from its own state. A reconcile after the flip closes any gap. Each shadow mismatch is a v1 bug, a v2 bug or a mapping difference, and each class gets a ticket. Cut-over order follows blast radius: small tenants first, the three biggest apps last.
