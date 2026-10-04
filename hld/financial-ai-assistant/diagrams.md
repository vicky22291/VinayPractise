# Diagrams: GenAI assistant over a customer's financial data

> One-line answer: twelve views of one design. An orchestrator runs a bounded loop of model calls (router, plan, compose) through the AI gateway; a tool gateway binds the tenant from the session, exchanges the user's token for an on-behalf-of token per API and realm, and returns typed aggregates as citable evidence; the model writes claim slots and a deterministic claim check renders every value and checks the words around it before a sentence reaches the user; writes are proposals the user confirms; an eval and release platform gates every change. The model call is the one red box.

The D1 to D12 set from `hld/CLAUDE.md` §4, each with a one-line caption. A diagram already in [`solution.md`](solution.md) gets a pointer here, never a second copy. Acronyms: LLM (large language model), SSE (server-sent events), OBO (on-behalf-of), STS (security token service, the identity token service), JWT (JSON Web Token), PII (personally identifiable information), AZ (availability zone), QBO (QuickBooks Online), P&L (profit and loss), MCP (Model Context Protocol), CI (continuous integration), PR (pull request), TTL (time to live), KV (key-value), FR (functional requirement), DFD (data flow diagram), HTTPS (encrypted web requests).

| # | Diagram | Where it lives |
|---|---|---|
| D1 | Context | below |
| D2 | Data flow | below (D2a system, D2b inside the orchestrator) |
| D3 | Component architecture (final design) | [solution §6](solution.md#6-final-design-and-the-six-core-flows) |
| D4 | Happy path per FR | FR1: [solution §4.1](solution.md#41-answer-a-question-the-model-picks-tools-tools-compute-the-answer-cites-them) and §6 Flow 1; a two-round question with the calculator below. FR2: [solution §4.2](solution.md#42-act-on-request-the-model-proposes-the-user-confirms-our-code-executes-once); drafting an invoice with step-up below. FR3: [solution §4.3](solution.md#43-stay-inside-the-users-permissions-the-tool-gateway-and-on-behalf-of-tokens). FR4: [solution §4.4](solution.md#44-evaluate-before-rollout-the-eval-suite-is-the-test-suite) |
| D5 | Failure paths | Write timeout, dropped stream and crashed orchestrator, token service down: below. Number mismatch and injection: solution §6 Flows 2 and 4. Provider outage: [solution §10.4](solution.md#104-failure-timeline) |
| D6 | Decision flows | Loop control, tool gateway, verifier: solution §5.1, §5.2, §5.3. Release gate and model fallback chain: below |
| D7 | Entity relationship | [solution §3.3](solution.md#33-data-model) |
| D8 | State machines | Proposed action: solution §4.2. Capability state of a turn: solution §5.4. Turn and release: below |
| D9 | Deployment / topology | below |
| D10 | Scaling / partitioning | below |
| D11 | Failure mode map | below, two trees |
| D12 | Rollout / migration | below |

## D1. Context (zoom-out)

The assistant as one box: users ask and confirm, Intuit identity vouches for them, domain APIs own the data, model providers are reached only through the AI gateway.

```mermaid
%% D1: the system as one box with every external actor. Red: the model providers, the one dependency we neither run nor fully control.
flowchart LR
    USR[QuickBooks and TurboTax users]:::client -->|"questions, confirmations"| SYS[Financial AI assistant<br/>orchestrator, tool gateway,<br/>verifier, actions, evals]:::service
    SYS -->|"verified answers, cards,<br/>proposals to confirm"| USR
    IDP[Intuit identity<br/>sessions, token exchange]:::external -->|"session, OBO tokens"| SYS
    SYS -->|"reads and confirmed writes,<br/>as the user"| DOM[Domain APIs<br/>ledger, invoices, banking, tax]:::external
    DOM -->|"reminders, invoices by email"| CUS[The business's own customers]:::external
    SYS -->|"prompts, no pii_high"| AIG[AI gateway to<br/>model providers]:::critical
    AIG -->|"tool calls, draft text"| SYS
    EXP[Intuit experts]:::external -->|"hard eval cases, judge labels,<br/>tax questions handed off"| SYS
    SYS -->|"audit trail, consent records"| CMP[Security, privacy, auditors]:::external
    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

## D2. Data flow (DFD)

### D2a. The system

Inputs to outputs with format, size and rate. Peak rates from solution §2 (300 questions/s).

```mermaid
%% D2a: data flow. Processes are rounded, stores are cylinders. Token counts and sizes are the estimates from solution section 2.
flowchart LR
    U[Assist panel]:::client -->|"question JSON ~200 B, 300/s"| OR(Orchestrator):::service
    OR -->|"prompts ~8k tokens, 900 calls/s,<br/>~72 M uncached tokens/min, x-gw-session"| M(Model via AI gateway):::critical
    M -->|"tool calls, sentences with slots,<br/>~250 tokens per question"| OR
    OR -->|"tool call JSON ~300 B, 900/s"| TG(Tool gateway):::service
    TG -->|"token exchange ~1 KB, ~600/s"| STS(Token service):::service
    TG -->|"HTTPS + delegated JWT, 900/s"| D(Domain APIs):::service
    D -->|"aggregates ~2 KB, at most 25 rows"| TG
    TG -->|"evidence c1..cn, labelled"| OR
    OR -->|"turn ~5 KB, 25 GB/day"| CS[(Conversation store<br/>30 days, ~750 GB)]:::store
    OR -->|"redacted trace ~10 KB, ~3 MB/s"| K[[Kafka traces + audit]]:::queue
    K -->|"Parquet, ~4.5 TB at 90 days"| L[(Trace and audit lake)]:::store
    OR -->|"SSE status, card, text,<br/>~3 KB per turn"| U
    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
```

### D2b. Inside the orchestrator: two streams, one gate

The plan stream becomes `status` events and tool calls; the compose stream becomes `text` events, one checked sentence at a time, with values rendered by code.

```mermaid
%% D2b: how the orchestrator turns model streams into user-visible events. Nothing reaches the SSE stream without passing a validator.
flowchart LR
    PS[Plan call stream] -->|"partial JSON"| TP[Tool-call parser]
    TP -->|"complete call"| SV[Schema check]
    SV -->|"valid call"| ST[status event]
    SV -->|"valid call"| TG[Tool gateway]
    TG -->|"evidence"| CD[card event]
    CS2[Compose call stream] -->|"sentences with claim slots + cites"| SP[Sentence splitter]
    SP -->|"one sentence"| VF[Claim check<br/>slots, metric, period, entity]
    VF -->|"agrees, values rendered"| TX[text event]
    VF -->|"contradiction or free digits"| RG[Regenerate that sentence,<br/>or template]

    class PS,CS2 critical
    class TP,SV,TG,SP,VF,RG service
    class ST,CD,TX client

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
```

## D3. Component architecture

The final design is in [solution §6](solution.md#6-final-design-and-the-six-core-flows): 14 nodes, red on the model calls through the AI gateway.

## D4. Happy paths, one per FR

FR1 to FR4 each have their chosen-flow sequence in solution §4.1 to §4.4, and FR1's final version is solution §6 Flow 1. Two more variants worth rehearsing:

### D4 FR1. A two-round question that needs the calculator

"What was my average monthly revenue this year, and which month was best?" The average is not a field of any report, so the model calls `calculate`, and the answer can only refer to the average through that recorded derivation's slot.

```mermaid
%% D4 (FR1, two rounds): the second round is a calculator call. The derivation d1 becomes evidence that a claim slot can reference.
sequenceDiagram
    autonumber
    participant O as Orchestrator
    participant M as Model via AI gateway
    participant G as Tool gateway
    participant R as Reports API
    participant V as Verifier
    O->>M: plan, intent revenue_trend
    M-->>O: run_report(ProfitAndLoss, this_year, group_by month)
    O->>G: validated call
    G->>R: P&L by month, Jan to Sep 2026, as the user
    R-->>G: 9 monthly income totals
    G-->>O: c1, best month is a value in c1
    O->>M: step 2 with c1
    M-->>O: calculate(mean of c1.income by month)
    O->>G: calculate, no I/O, decimal arithmetic
    G-->>O: d1 = 41,237.18, inputs c1
    O->>M: compose with c1 and d1
    M-->>O: average {d1} a month this year, best was June at {c1.jun}
    O->>V: clause words vs metadata, average income 2026 for d1, June 2026 for c1.jun
    V-->>O: agrees, render $41,237 and $55,910
    O-->>O: stream text, done, 4 model steps used of 6
```

### D4 FR2. Draft a new invoice, with step-up above the threshold

"Invoice Acme for 10 hours of consulting at $150." The quantity and rate come from the user's own message, the total from the calculator, the customer id from a lookup that our code matches without handing names to the model, so the turn stays clean and can propose (solution §5.4).

```mermaid
%% D4 (FR2, invoice): every number in the proposal is traced before a card is shown. Step-up applies only above the threshold.
sequenceDiagram
    autonumber
    participant U as User
    participant O as Orchestrator
    participant G as Tool gateway
    participant A as Action service
    participant I as Invoices API
    U->>O: invoice Acme for 10 hours of consulting at 150
    O->>G: find_customer(Acme)
    G-->>O: c1, customer 58 at record version 14, exact name match, no free text
    O->>G: propose_invoice(customer 58, consulting, qty q.n1, rate q.n2)
    G->>G: 10 and 150 are slots to the user's message, total 1,500.00 by calculator
    G->>A: proposal a_12, recipient and version 14 in args_hash h7, 15 min
    A-->>U: card from a_12, Acme Corp, ap@acme.example, 10 x 150.00 = 1,500.00
    U->>A: confirm a_12 with h7
    alt total over 10,000 or a recipient changed in 30 days
        A-->>U: step-up, re-enter password or second factor
        U->>A: step-up token
    end
    A->>A: customer 58 still at version 14, else fail as stale
    A->>I: create invoice, Idempotency-Key a_12, as the user
    I-->>A: invoice 1088 created
    A-->>U: Invoice 1088 for $1,500.00 created
```

## D5. Failure paths

### D5a. The write times out, then the retry settles it

```mermaid
%% D5a: a timeout leaves the action UNKNOWN, never retried with a new key. The domain API's idempotency store returns the first result.
sequenceDiagram
    autonumber
    participant U as Assist panel
    participant A as Action service
    participant S as Conversation store
    participant I as Invoices API
    U->>A: confirm a_7
    A->>S: a_7 PROPOSED to EXECUTING
    A->>I: send invoice 1043, Idempotency-Key a_7:1043
    Note over A,I: 2 s timeout, the email may or may not have gone
    A->>S: a_7 UNKNOWN
    A-->>U: Sending, checking status
    A->>I: same request, same key, after 1 s backoff
    I-->>A: already processed, sent at 10:02:11
    A->>S: a_7 DONE with the stored result
    A-->>U: Sent
    Note over A,I: a new key here would risk a second email to the customer
```

### D5b. The stream drops, or the orchestrator dies mid-turn

```mermaid
%% D5b: turn_id makes both cases safe. A finished turn is replayed; a stale claim is re-run, which is safe because reads have no side effects and proposals are keyed.
sequenceDiagram
    autonumber
    participant U as Assist panel
    participant O1 as Orchestrator pod 1
    participant O2 as Orchestrator pod 2
    participant S as Conversation store
    U->>O1: POST turn t_9
    O1->>S: claim t_9, conditional put
    O1-->>U: status, card
    Note over U,O1: phone switches networks, SSE drops
    U->>O2: GET turn t_9
    O2->>S: read (tenant, user, t_9), owner check
    S-->>O2: answer stored, status DONE
    O2-->>U: replay card and verified text
    Note over O1,O2: second case, pod 1 crashes before any answer is stored
    U->>O2: POST turn t_9 again after 30 s
    O2->>S: claim t_9, older than 30 s with no answer
    O2-->>U: re-run the turn from the start
```

### D5c. The identity token service is down

```mermaid
%% D5c: tools fail closed. There is no fallback to a service credential, ever.
sequenceDiagram
    autonumber
    participant O as Orchestrator
    participant G as Tool gateway
    participant S as Token service
    participant D as Domain API
    Note over S: t = 0, token service unreachable
    O->>G: run_report, realm 9130354
    G->>G: cached delegated token, 40 s old, still valid
    G->>D: call with cached token
    D-->>G: result
    Note over G,S: t = 60 s, cached tokens expire
    O->>G: list_invoices
    G->>S: token exchange
    S--xG: timeout
    G-->>O: auth_unavailable, no data
    O-->>O: answer says I cannot reach your data right now, no card
    Note over O,G: page at 1 minute, quick answers also stop because they need tools too
```

## D6. Activity / decision flow

The three decision flows inside the hardest components are in the solution: the loop's budget checks (§5.1), the tool gateway's checks (§5.2) and the verifier (§5.3). Two more:

### D6c. The release gate pipeline

```mermaid
%% D6c: the release gate pipeline. Every pink gate can stop a release; every stage after offline can roll back to the previous release id.
flowchart LR
    C[Candidate release<br/>prompt, model, tools] -->|"suite v12"| O[Offline eval<br/>5,500 cases, synthetic tenants]
    O -->|"scores"| G1{Structural red team 100%,<br/>behavioral attack rate in bound,<br/>correctness drop at most 1 pt,<br/>cost within 10%?}
    G1 -->|"no"| X[Blocked, report to PR]
    G1 -->|"yes"| SH[Shadow, 5% mirrored, replays<br/>recorded evidence, hidden, no writes]
    SH -->|"3 days of paired traces"| G2{Paired online metrics ok?}
    G2 -->|"no"| X
    G2 -->|"yes"| CA[Canary 1, 5, 25, 100%<br/>sticky user cohorts]
    CA -->|"guardrail breach"| RB[Flag back to previous release]
    CA -->|"healthy"| GA[Current release]

    class C client
    class O,SH,CA,GA,RB,X service
    class G1,G2 decision

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

### D6d. Which model answers, or none

```mermaid
%% D6d: the fallback chain for one model step. Red: the provider calls. The last two boxes need no model at all.
flowchart TD
    S[Model step needed] -->|"prompt"| B1{Primary breaker closed,<br/>turn SLO not burning?}
    B1 -->|"yes"| P[Call primary]
    P -->|"stream"| T1{First token within 3 s?}
    T1 -->|"yes"| OK[Continue the loop]
    T1 -->|"no"| B2{Fallback breaker closed?}
    B1 -->|"no"| B2
    B2 -->|"yes"| F[One call on the evaluated fallback]
    F -->|"model output"| OK
    B2 -->|"no"| QA{Local intent matcher<br/>confidence at least 0.8?}
    QA -->|"yes"| TPL[Run the tool, render the template]
    QA -->|"no"| LNK[Assist is limited, links to reports]

    class S client
    class P,F critical
    class OK,TPL,LNK service
    class B1,T1,B2,QA decision

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

## D7. Entity relationship

In [solution §3.3](solution.md#33-data-model): conversations, turns, tool calls and derivations, proposed actions keyed by tenant; consent by user; releases and eval data global.

## D8. State machines

The proposed action (solution §4.2) and the capability state of a turn (solution §5.4) are in the solution. Two more:

### D8c. One turn

```mermaid
%% D8c: lifecycle of one turn. Composing includes the claim check of each sentence as it streams; Regenerating rewrites one sentence only. Budget and deadline exits go to the template, never to an error page.
stateDiagram-v2
    direction LR
    [*] --> Claimed: turn_id claimed
    Claimed --> Claimed: stale, re-run
    Claimed --> Planning: router done
    Planning --> Tools: tool calls
    Tools --> Planning: results
    Planning --> Composing: ready to answer
    Planning --> Templated: budget hit
    Composing --> Done: all clauses agree
    Composing --> Regenerating: contradiction, 2 s left
    Composing --> Templated: contradiction, no time
    Regenerating --> Done: sentence agrees
    Regenerating --> Templated: fails again
    Templated --> Done: template sent
    Done --> [*]
```

### D8d. One release

```mermaid
%% D8d: lifecycle of one release bundle. Only Current and canary cohorts serve users; RolledBack is a flag flip, not a deploy.
stateDiagram-v2
    direction LR
    [*] --> Candidate: PR builds bundle
    Candidate --> Blocked: offline gate fails
    Candidate --> Shadow: offline gates pass
    Shadow --> Blocked: shadow metrics fail
    Shadow --> Canary: shadow ok
    Canary --> RolledBack: guardrail breach
    Canary --> Current: 100% healthy
    Current --> RolledBack: incident
    Current --> Retired: next release
    Blocked --> [*]
    RolledBack --> [*]
    Retired --> [*]
```

## D9. Deployment / topology

Two US regions, active-active for the stateless tiers. Providers are reached in-region; nothing with customer data leaves the US.

```mermaid
%% D9: two US regions. Stateless tiers run in every AZ. Only conversation replication and model fallback can cross a region.
flowchart LR
    subgraph EAST["us-east, 3 AZs"]
        GE[API gateway]:::client -->|"turns"| OE[Orchestrator pods<br/>+ verifier]:::service
        OE -->|"tool calls"| TE[Tool gateway pods]:::service
        TE -->|"token exchange"| SE[Token service]:::service
        OE -->|"model calls"| AE[AI gateway east]:::service
        CE[(Conversation store,<br/>global table)]:::store
    end
    subgraph WEST["us-west, 3 AZs"]
        GW2[API gateway]:::client -->|"turns"| OW[Orchestrator pods<br/>+ verifier]:::service
        OW -->|"model calls"| AW[AI gateway west]:::service
        CW[(Conversation store,<br/>global table)]:::store
    end
    AE -->|"in-region endpoint"| PA[Provider A, US]:::critical
    AE -->|"fallback"| PB[Provider B, US]:::critical
    AW -->|"in-region endpoint"| PA
    OE -->|"turns"| CE
    OW -->|"turns"| CW
    CE <-->|"async replication, seconds"| CW
    TE -->|"calls routed to the realm's home region"| DOM[Domain APIs]:::external
    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

Replication factor: the conversation store keeps 3 copies per region plus the other region's copy. Orchestrator and tool gateway pods are spread over 3 AZs and sized to lose one. The tool gateway in the west region is not drawn; it is the same as the east one.

## D10. Scaling / partitioning

Our data partitions trivially by tenant. The hot spot is not a shard of ours: it is one provider deployment, made hot by how requests are routed to it.

```mermaid
%% D10: conversation data is partitioned by tenant_id, never hot. Red: the deployment that prefix-hash affinity overloads, because every user of a tool bundle sends the same first 2 KB. The fix is the session header.
flowchart LR
    Q[300 questions/s peak] -->|"any pod"| OR[Orchestrator pods, stateless]
    OR -->|"hash of tenant_id"| P1[(Partitions by tenant_id<br/>one realm = a few questions a minute)]
    OR -->|"900 model calls/s"| AG[AI gateway<br/>leases, weighted routing]
    AG -->|"without a session header:<br/>hash of first 2 KB, one bundle, one host"| D1[Provider A, east deployment<br/>a whole bundle, past its quota]
    AG -->|"x-gw-session = conversation_id:<br/>spread by conversation"| D2[Provider A, east and west<br/>deployments, even load]
    AG -->|"failover, SLO-burn weight"| D3[Provider B deployment]
    D1 -.->|"fix: send x-gw-session"| D2

    class Q client
    class OR,AG service
    class P1 store
    class D1 critical
    class D2,D3 external

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

Why no hot tenant: the biggest accounting firm is many realms, each its own conversation partition, and per-user and per-realm budgets (200 and 2,000 questions a day [estimate]) cap a script. Why the session header: the shared prefix is per (release, tool bundle), so prefix-hash affinity sends every user of a bundle to one deployment, and bounded load spills it only at 1.5x average (AI gateway §5.4). With `x-gw-session = conversation_id`, a conversation's plan and compose calls and its next turn land together (the conversation cache hits) and load spreads by conversation. The price is re-writing each bundle's ~6k-token static block once per deployment every 5 minutes, ~$4 an hour (solution §5.7).

## D11. Failure mode map

### D11a. The model and the loop

```mermaid
%% D11a: component, then failure and blast radius, then mitigation. Red: the provider, the most likely failure.
flowchart TD
    R[Assistant turn] -->|"depends on"| A[Model provider]
    R -->|"depends on"| B[Claim check]
    R -->|"depends on"| C[Orchestrator pod]
    R -->|"depends on"| D[Release]
    A -->|"failure, blast radius"| A1["Outage or slow first token:<br/>every turn on that provider"]
    A1 -->|"mitigation"| A2["Breaker, evaluated fallback,<br/>quick answers, product unaffected"]
    B -->|"failure, blast radius"| B1["Lexicon misses a paraphrase:<br/>a mislabelled number could show"]
    B1 -->|"mitigation"| B2["Fails closed to a rendered label,<br/>weekly expert sample, lexicon tests"]
    C -->|"failure, blast radius"| C1["Pod dies:<br/>~70 turns in flight on it"]
    C1 -->|"mitigation"| C2["Client retries same turn_id,<br/>stale claim re-run"]
    D -->|"failure, blast radius"| D1["Bad prompt or model:<br/>every user in the cohort"]
    D1 -->|"mitigation"| D2["Offline gates, cohort canary,<br/>flag rollback in 60 s"]

    class R client
    class A critical
    class B,C,D service
    class A1,B1,C1,D1 decision
    class A2,B2,C2,D2 service

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

### D11b. Data, identity and writes

```mermaid
%% D11b: the data path. Every mitigation fails closed: no token, no consent, no audit record, no data or write. A write timeout is D5a.
flowchart TD
    R[Tool or write call] -->|"depends on"| A[Tenant binding]
    R -->|"depends on"| B[Token and consent services]
    R -->|"depends on"| C[Domain API]
    R -->|"depends on"| D[Kafka audit stream]
    A -->|"failure, blast radius"| A1["Binding bug:<br/>possible cross-tenant read"]
    A1 -->|"mitigation"| A2["API audience check is a second wall,<br/>page on 401 audience or tenant denials"]
    B -->|"failure, blast radius"| B1["Down: every data tool,<br/>or tax tools for consent"]
    B1 -->|"mitigation"| B2["Cached tokens 60 s, then fail closed,<br/>consent denies by default"]
    C -->|"failure, blast radius"| C1["Slow: only its tools"]
    C1 -->|"mitigation"| C2["2 s timeout, own quota,<br/>answer says what is missing"]
    D -->|"failure, blast radius"| D1["Down: audit events cannot ship,<br/>~360 KB/s fleet-wide"]
    D1 -->|"mitigation"| D2["Spool to local disk,<br/>confirms fail closed when full"]

    class R client
    class A,B,C,D service
    class A1,B1,C1,D1 decision
    class A2,B2,C2,D2 service

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

## D12. Rollout / migration

From a first-generation assistant (help-article retrieval plus a data plugin on a service account) to this design. Every phase is a flag, and each one names its rollback point.

```mermaid
%% D12: migration phases. Each phase ends at a rollback point; nothing needs a coordinated deploy.
gantt
    title Migration to the tool-gateway assistant
    dateFormat YYYY-MM-DD
    axisFormat %b
    section Read path
    Tool gateway with reports tools, read-only, shadow vs old assistant :p1, 2026-11-02, 21d
    Rollback point, flag off, old assistant answers :milestone, m1, after p1, 0d
    section Delegated tokens
    Reports and transactions APIs accept OBO tokens :p2, after p1, 28d
    Invoices and banking APIs accept OBO tokens :p3, after p2, 28d
    Rollback point, interim service scope per API :milestone, m2, after p3, 0d
    section Grounding and evals
    Claim check in report-only mode :p4, after p1, 14d
    Claim check blocking once contradictions stay under 3 percent :p5, after p4, 14d
    Canary read answers 1 to 100 percent :p6, after p5, 21d
    Rollback point, flag to previous release :milestone, m3, after p6, 0d
    section Writes
    Categorization proposals, reversible :p7, after p6, 14d
    Reminders, then invoices :p8, after p7, 28d
    Retire the service-account plugin :p9, after p8, 14d
```

Rollback per phase: p1 is a flag (the old assistant still answers); p2 and p3 keep the interim path (session binding plus a narrow service scope) per API until its owner flips it; p4 to p6 are release flags; p7 and p8 turn proposal tools off per type; p9 happens only after 30 days with zero traffic on the old plugin.
