# Expense Rules Engine at Scale: Mechanisms Survey

**Status:** Primary source research for Staff-level system design (Rippling case study)
**Scope:** Card authorization, rule evaluation engines, concurrency patterns, money handling
**Cutoff:** September 2026

---

## Sources Index

| ID | URL | Establishes |
|----|-----|-------------|
| S1 | https://docs.stripe.com/issuing/controls/spending-controls | Stripe spending_controls fields, intervals, aggregation delay |
| S2 | https://docs.stripe.com/radar/rules | Stripe Radar rule actions (Allow, Block, Review, Request 3DS), precedence order |
| S3 | https://docs.stripe.com/issuing/controls/real-time-authorizations | Stripe webhook 2-second response deadline |
| S4 | https://www.iso.org/standard/79450.html | ISO 18245:2023 MCC standard, structure, maintenance |
| S5 | https://www.checkout.com/blog/iso-8583-merchants | ISO 8583 message types, authorization/clearing/settlement flow |
| S6 | https://www.openpolicyagent.org/docs/policy-performance | OPA 1ms latency budget, rule indexing, constant-time evaluation |
| S7 | https://github.com/google/cel-spec | CEL non-Turing-completeness, termination guarantee, linear evaluation |
| S8 | https://dl.acm.org/doi/10.1145/3649835 | Cedar OOPSLA 2024: constant-time operators, SMT-based verification |
| S9 | https://arxiv.org/abs/2403.04651 | Cedar arxiv 2403.04651, performance benchmarking methodology |
| S10 | https://docs.jboss.org/drools/release/6.4.0.Final/drools-docs/html/ch05.html | Drools Phreak: lazy, goal-oriented, aggressively delayed partial matching |
| S11 | https://www.kie.org/2014/02/drools-6-performance-with-the-phreak-algorithm.html | Phreak batch evaluation, graceful degradation with complexity |
| S12 | https://ics.uci.edu/~cs223/papers/p405-o_neil.pdf | O'Neil Escrow (ACM TODS 1986): nonblocking long-lived transaction updates |
| S13 | https://link.springer.com/article/10.1007/BF01232643 | Demarcation Protocol (Barbara, Garcia-Molina 1992): linear arithmetic constraints |
| S14 | https://www.postgresql.org/docs/current/sql-select.html | PostgreSQL SELECT FOR UPDATE, row-level lock modes, NOWAIT/SKIP LOCKED |
| S15 | https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/transaction-apis.html | DynamoDB TransactWriteItems, ConditionExpression, per-partition 1000 WCU / 3000 RCU |
| S16 | https://redis.io/docs/latest/commands/wait/ | Redis WAIT: acknowledged writes, failover risk, Lua script limitations |
| S17 | https://docs.adyen.com/development-resources/currency-codes | ISO 4217 minor units: JPY 0, USD 2, BHD 3 |
| S18 | https://www.chargebackgurus.com/blog/credit-card-authorization-hold | Authorization hold times: 7 days standard, 30 days hotels/car rental MCC |
| S19 | https://wallesthub.com/answers/cc/how-much-do-gas-stations-hold-on-credit-cards | Fuel pump pre-auth: up to $175 (Visa/Mastercard 2022 increase) |
| S20 | https://www.checkout.com/blog/what-is-tip-tolerance | Restaurant tip tolerance: 20% of base amount (Visa guideline) |
| S21 | https://www.checkout.com/blog/what-are-incremental-authorizations | Hotel incremental auth: additional authorizations for extended stay |
| S22 | https://www.researchgate.net/publication/241171085_Improving_Rete_algorithm | Rete II: 50-100x faster than original Rete, match-phase ~90% runtime |
| S23 | https://github.com/google/cel-go | CEL evaluation: linear time + space cost, nanoseconds-to-microseconds, cost units |
| S24 | https://docs.camunda.io/docs/components/best-practices/modeling/choosing-the-dmn-hit-policy/ | DMN hit policies: UNIQUE (U), FIRST (F), PRIORITY (P), COLLECT (C) |
| S25 | https://docs.stripe.com/connect/currencies | Stripe multi-currency: FX rate applies at settlement (1-3 days after purchase) |

---

## A. Card Authorization Mechanics

### A1. Stripe Issuing Real-Time Authorizations [S1, S3]

Stripe Issuing webhooks (`issuing_authorization.request`) enforce a hard deadline of **2 seconds** to respond with approve/decline decision. Timeout behavior configurable via webhook settings; without explicit response, system defaults to configured Autopilot rules.

Spending controls (checked before webhook) include:
- `allowed_categories`, `blocked_categories`: merchant category filters.
- `allowed_merchant_countries`, `blocked_merchant_countries`: geography controls.
- `allowed_card_presences`: physical/virtual/online card transaction types.
- `spending_limits` array with `interval` options: `per_authorization`, `daily`, `weekly`, `monthly`, `yearly`, `all_time`. Default limit if not set: 500 USD/day per card. Unconfigurable system default: 10,000 USD per authorization.
- Spending aggregation: best-effort, up to **30 seconds delay** between transaction and aggregation [S1].

### A2. Card Network Authorization Lifecycle [S5, S18, S19, S20, S21]

ISO 8583 message types define lifecycle:
- **0100/0110 (Authorization request/response)**: Issuer verifies cardholder identity, checks balance, places funds hold. Reply includes approval code or decline code. Hold is conditional payment obligation, not actual fund transfer.
- **0200 (Clearing request)**: Post-authorization aggregation by card network. Merchant submits captured transaction batches. Issuer/acquirer net obligations calculated.
- **0420 (Reversal)**: Cancels authorized hold (merchant network timeout, declined capture, etc).

Settlement (actual funds transfer) happens via wire transfer between issuer and acquirer, typically 1-3 days after clearing.

Authorization hold expiration:
- Standard MCCs: **7 days** [S18].
- Hotels (MCC 7011), car rental (MCC 3667): **30 days** if merchant properly registered [S18].
- Holds can be released early by merchant reversal (0420 message).

Incremental authorization: Hotels place additional auth holds for extended stay [S21]. Each hold is separate ISO 8583 0100 message. Authorization hold aggregates: issuer may apply daily/lifetime limits to sum of all holds.

Tip tolerance (restaurants, MCC 5812/5814): Merchant can add up to **20% of base auth amount** in clearing without new authorization [S20]. If tip exceeds tolerance, transaction downgrades to higher interchange category.

Fuel pump pre-authorization: Networks allow up to **$175 hold** (increased from $125 in 2022) [S19]. Hold releases after transaction settles.

### A3. Merchant Category Codes (MCC) [S4, S18]

ISO 18245:2023 (current standard; 2003 version superseded): 4-digit classification standardized internationally. Card networks (Visa, Mastercard, Amex, Discover) implement ISO 18245 with network-specific extensions.

Common codes:
- Restaurants: 5812 (eating places), 5814 (fast food).
- Airlines: 4511, also range 3000-3350.
- Hotels: 7011, also range 3500-3999.
- Gas stations: 5542.
- Entertainment: 7999.

Assignment authority: card networks + acquirers. Reliability concerns: merchant-provided at signup, occasionally misclassified (merchant gaming to avoid restrictions or honest mistake). Networks audit but not real-time (reactive). MCC changes logged but not always immediate. Rippling policy engine must handle MCC drift and should verify at transaction time.

Impact on spend policies: different MCCs have different authorization hold durations, tip tolerances, and fraud scoring. MCC on transaction determined by merchant's registration at acquirer; cardholder cannot override.

### A4. Visa Stand-In Processing (STIP)

When issuer system unavailable, Visa automatically approves/declines using issuer-configured parameters (pre-defined spend limits, velocity rules). No authorization webhook sent. AI-enhanced variant (Smarter STIP) uses historical patterns for better decisions.

---

## B. Rule Representation and Evaluation

### B1. Rete Algorithm (Forgy 1982) [S22]

Optimizes many-rules-x-many-facts pattern matching via partial evaluation caching. Built on observation that working memory facts change slowly through inference cycles. Trades increased memory for improved performance. Match-phase consumes **~90% of typical runtime** in production systems. Rete II successor achieves **50-100x speedup** over original Rete depending on rule/object complexity [S22].

Rete networks maintain discriminator nodes, beta memory nodes, and right memories for partial match state. Incremental as facts change.

Successor algorithm: **Drools Phreak** [S10, S11]. Lazy, goal-oriented; aggressively delays partial matching until facts activate rule preconditions. Starts with all rules unlinked from pattern data. Insert/update/delete queued; Phreak heuristically selects next rule for evaluation based on activation likelihood. When preconditions satisfied, rule linked and placed in goal priority queue ordered by salience. Batch evaluates activated rules. Graceful degradation with complexity (forgiving of poorly-written rule bases vs. Rete's sensitive performance cliff). No expensive wasted work on unactivated rules.

### B2. Google Common Expression Language (CEL) [S7, S23]

Non-Turing-complete by design: guaranteed termination. Linear time evaluation O(n) relative to expression size and input (when macros disabled). Cost model: machine-independent cost units; default estimated-cost limit high (triggers only on O(n²) or worse over unbounded data). Actual cost enforcement halts execution on threshold exceed. Computational complexity specified for all language constructs and standard functions.

Evaluation latency: **nanoseconds to microseconds** [S23]. No resource consumption surprise.

Used in: Kubernetes ValidatingAdmissionPolicy (schema validation), Envoy RBAC (authorization), Firebase security rules, untrusted expression execution environments.

Rationale: primary use case is execution of untrusted expressions with reliable containment. Time and space cost guarantees essential to security posture.

### B3. AWS Cedar (OOPSLA 2024) [S8, S9]

Authorization language for expressive, fast, safe, analyzable policies. Performance: most Cedar operators **constant-time**; loop constructs **linear**. Policy set slicing evaluates only relevant policies per request (semantic analysis pre-identifies applicable policies). Formal verification via SMT reduction: symbolic compiler translates Cedar policies to SMT, producing decidable, sound, complete encoding of policy semantics. Cedar semantics formalized in Lean proof assistant.

Type system helps policy writers avoid mistakes; optional typing does not require full program annotation.

Paper arxiv 2403.04651 (published OOPSLA 2024 / ACM PACMPL Vol. 8) includes benchmarks (100k authorization requests across 200 random entity stores, 3 application scenarios with entity generators and request distributions). Exact latency numbers not extractable from PDF format, but methodology clear: 100k request throughput measured across entity stores. Performance compared to OpenFGA and Rego in paper.

### B4. Open Policy Agent / Rego [S6]

OPA designed for **1 millisecond latency budget** (e.g., microservice authorization decisions). Rego is declarative language for expressing policies over hierarchical JSON data. Applications query OPA with structured input; OPA evaluates rules and returns decision.

Partial evaluation: rules generate sets of values (not just boolean). Incremental rule building: each rule contributes to decision set.

Rego fragment (linear fragment) uses special indexing algorithms to achieve near-constant-time evaluation as policy grows. Not all Rego is linear (some features require scanning), but indexed subset can be constant-time even with many rules. Recommendation: write rules with indexed statements for effective rule-indexing.

Benchmarking: `opa bench` command repeats evaluation, reports performance. `--optimize-store-for-read-speed` flag improves read-heavy workloads (trade-off: write latency). `--metrics` and `--benchmem` enable detailed analysis. E2E benchmarking with `--e2e` includes server overhead.

### B5. Other DSLs: JsonLogic, DMN, Stripe Radar [S2, S24]

JsonLogic: JSON-based syntax (`{"===": [1, 1]}`, `{"and": [true, false]}`); compiler caches rule as delegate tree on first evaluation.

DMN decision tables: hit policies define multi-rule evaluation. **UNIQUE (U):** one match only. **FIRST (F):** first match (order matters). **PRIORITY (P):** matches with output priority. **COLLECT (C):** all matches (optional aggregate operator) [S24].

Stripe Radar rules syntax: `{action} if {attribute} {operator} {value}`. Actions: Request 3DS (evaluated first) > Allow (overrides others) > Block > Review. Rule order within same action type does not matter (action type precedence is deterministic) [S2].

---

## C. Aggregate & Budget Enforcement Under Concurrency

### C1. Escrow & Demarcation [S12, S13]

**Escrow (O'Neil, ACM TODS Vol. 11 No. 4, Dec 1986)**: permits long-lived transaction record updates without forbidding concurrent reads/writes by other transactions. Escrow method: reserves ranges of field values for active transactions. Updates checked against reserved ranges; no exclusive lock required. Reduces lock contention for long-lived transactions (e.g., report generation, batch jobs). Trade-off: requires pre-reservation of field ranges and careful range overlap detection.

**Demarcation Protocol (Barbara & García-Molina, 1992, EDBT/VLDB)**: maintains linear arithmetic constraints (e.g., `balance + delta <= limit`) in distributed databases without centralized coordinator or high message overhead. Establishes safe limits ("demarcation lines drawn in the sand" for updates). Lazy constraint propagation: allows local updates up to safe limit, propagates constraint tightening asynchronously. Applicable to linear constraints, existential constraints, key constraints, approximate copy constraints. Avoids locking or resource hold-up during protocol execution.

Example: global budget limit of $10,000 across 3 regions. Each region pre-reserved $3,500 (demarcation line). Region 1 can authorize spending up to $3,500 without coord message. When limit approaches, coordinator tightens demarcation line (e.g., $2,000) via background message. No transaction blocks waiting for coordinator.

### C2. PostgreSQL Row-Level Locking [S14]

`SELECT ... FOR UPDATE` acquires exclusive row locks until transaction end (COMMIT or ROLLBACK). Lock modes:
- `FOR UPDATE`: exclusive, blocks other updates and FOR SHARE.
- `FOR NO KEY UPDATE`: weaker exclusive, allows FOR KEY SHARE.
- `FOR SHARE`: shared, multiple concurrent readers can hold.
- `FOR KEY SHARE`: weakest shared, allows other FOR KEY SHARE.

Options: `NOWAIT` (error immediately if locked), `SKIP LOCKED` (skip locked rows; useful for queue processing).

With LIMIT/OFFSET: locking stops once limit rows obtained (offset rows still locked but then released).

Pattern for budget check:
```sql
BEGIN;
SELECT balance FROM accounts WHERE id=? FOR UPDATE;
IF balance+charge <= limit THEN
  UPDATE accounts SET balance=balance+charge WHERE id=?;
COMMIT;
```
Ensures no race: row locked from SELECT through UPDATE.

Atomicity: transaction all-or-nothing; rollback on failure undoes all work. Deadlock risk if multiple transactions lock rows in inconsistent order.

### C3. DynamoDB Conditional Writes [S15]

`TransactWriteItems`: up to 100 write actions, max 4 MB aggregate size. Actions: Put, Update, Delete, ConditionCheck. Cannot target same item multiple times in single transaction. Atomicity: all-or-none. `ConditionExpression` evaluated server-side (e.g., `attribute_exists(pk) AND #b + #c <= #limit`). If any condition fails, entire transaction rolls back. No partial success.

Isolation: Serializable between transactional and standard operations (GetItem, PutItem, UpdateItem, DeleteItem). Read-committed isolation vs. multi-item reads (BatchGetItem, Query, Scan).

Per-partition throughput limits: **1,000 WCU (write capacity units)** and **3,000 RCU (read capacity units)** per second [S15]. Transactions consume 2x capacity: one WCU to prepare, one to commit (visible in CloudWatch metrics). Provisioned capacity planning must account for 2x overhead. Conflict handling: TransactionCanceledException on concurrent TransactWriteItems to same item; includes CancellationReasons array per item. CloudWatch TransactionConflict metric incremented per failed request.

Idempotency: optional ClientRequestToken (10-minute window); repeated call with same token returns success without changes.

Partitions auto-split at 10 GB. Hot partition (high traffic to single partition key) throttles at 1000 WCU / 3000 RCU even if table has more provisioned capacity.

### C4. Redis Lua Scripts [S16]

Lua scripts execute atomically via EVAL/EVALSHA: no other commands interleave during script execution. Other clients see either pre-script state or post-script state (no partial visibility). All write side effects propagated to replicas to maintain consistency.

WAIT command: blocks until N replicas acknowledge previous writes. `WAIT numreplicas timeout_ms` waits up to timeout for acknowledgment. Returns actual number of replicas that acknowledged (may be less than requested if timeout). Improves real-world data safety: write transferred to replica is more likely to survive master failover.

Critical limitation: **acknowledged writes can still be lost during failover** (async replication) [S16]. WAIT is not strong consistency; Sentinel/Cluster failover can lose acknowledged data if replica crashes before replicating to another replica.

WAIT inside Lua (Redis 7.0+): if WAIT sent in transaction context (inside MULTI or inside script in certain modes), does not block. Returns immediately with current replica ack count. Prevents Lua script from blocking (scripts must execute fast).

Master-replica replication: async by default (master replies immediately, replication in background). Replica failure after ack but before full persistence = lost write.

---

## D. Money & Time Details

### D1. Currency Representation [S17]

Store as integer minor units per ISO 4217:
- JPY (Japanese Yen): **0 minor units** (no fractional part).
- USD (US Dollar): **2 minor units** (cents).
- BHD (Bahraini Dinar): **3 minor units** (0.001 dinar) [S17].

Encode exponent in currency code. Never use floating-point for monetary amounts.

### D2. FX Rate Timing [S25]

Exchange rate applied at settlement (1-3 business days after authorization), not at authorization time. Card network (Visa, Mastercard) determines rate; platform has no control over network rate unless using Marqeta multi-currency settlement (which settles directly in destination currency, avoiding network FX spread and ~1% international assessment).

Timing risk: EUR-to-USD authorization at EUR/USD 1.10, but settle at 1.08 = merchant takes 2% loss.

Stripe FX Quotes API allows locking rates for 5 minutes, 1 hour, or 24 hours at time of authorization request (useful for price quotes before payment commits customer). Extended quote holds rate reservation. Practical for cross-border transactions where volatility is concern.

---

## Key Numbers Summary (Confidence Ranges)

**High confidence (primary docs, numeric claims):**
- Stripe webhook timeout: **2 seconds** (S3)
- Spending aggregation delay: **30 seconds** (S1)
- Standard authorization hold: **7 days**; hotels/car rental: **30 days** (S18)
- Restaurant tip tolerance: **20%** of base (S20)
- Fuel pump hold cap: **$175** (S19)
- DynamoDB per-partition limits: **1,000 WCU / 3,000 RCU** (S15)
- OPA latency target: **1 millisecond** (S6)
- Rete II speedup: **50-100x** over original (S22)
- CEL latency: **nanoseconds to microseconds** (S23)
- ISO 4217 minor units: JPY 0, USD 2, BHD 3 (S17)

**Moderate confidence (secondary claims in primary sources):**
- Default Stripe per-card limit: **500 USD/day**
- System-wide Stripe limit: **10,000 USD per authorization**
- Rete match-phase overhead: **~90% of runtime** (context-dependent)
- FX settlement rate timing: **1-3 days after auth**

**Unverified (no numeric detail found):**
- Marqeta JIT Funding timeout (documentation access restricted)
- Lithic Auth Stream Access timeout (documentation access restricted)
- Cedar paper exact benchmark numbers (PDF unreadable in text extraction)
- Incremental authorization timeout per Visa/Mastercard


---

## Spot-check corrections (editor, 2026-09-30)

Checked by hand against the primary pages. The agent reported 249 lines and marked Marqeta, Lithic and the Cedar numbers as inaccessible; all three were one fetch away.

| Claim above | Status | What the primary source says |
|---|---|---|
| Stripe `issuing_authorization.request` deadline 2 s | Correct | "If Stripe doesn't receive your approve or decline response within 2 seconds, the Authorization is automatically approved or declined based on your timeout settings" (docs.stripe.com/issuing/controls/real-time-authorizations) |
| Stripe spending aggregation delay 30 s | Correct | "Spending aggregation is done on a best-effort basis. You might notice a delay of up to 30 seconds". Also: "Spending controls run before real-time authorisations", date-based intervals start at midnight UTC, and "Additional tips and fees can be posted at a later time, causing a spending limit to be exceeded" (docs.stripe.com/issuing/controls/spending-controls) |
| (missing) captures and controls | Added | "Spending controls, real time authorization controls, and card status ... don't apply for capture ... captures for approved authorizations always succeed" (docs.stripe.com/issuing/purchases/transactions) |
| Lithic ASA timeout "documentation access restricted" | Wrong, the page opens | "If no response is received within 6 seconds, the transaction will be declined for the cardholder ... We recommend responding within 3 seconds" (docs.lithic.com/docs/auth-stream-access-asa) |
| Marqeta JIT timeout "documentation access restricted" | Partly wrong | The JIT page opens. It gives the fallback chain, not a timeout number: network STIP if the network cannot reach Marqeta, and "If your system cannot respond to a Gateway JIT Funding request, the Marqeta platform uses Commando Mode to make a decision in your place based on defined business rules" (marqeta.com/docs/developer-guides/about-jit-funding). The timeout in seconds stays unverified |
| Cedar numbers "not extractable" | Wrong, `pdftotext` works | Median over input sizes: Cedar 28.7x, 34.4x, 35.2x faster than OpenFGA and 60.4x, 80.8x, 42.8x faster than Rego (gdrive, github, TinyTodo). Rego gdrive median 76 µs at 5 entities, 676 µs at 50. SMT encode and solve 75.1 ms on average (arXiv 2403.04651) |
| CEL "nanoseconds to microseconds" | Not the spec's wording | cel-spec README: "CEL evaluates in linear time, is mutation free, and not Turing-complete"; cel-go README: linear in expression and input size "when macros are disabled" |
| Restaurant tip tolerance 20% (S20 checkout.com blog) | Unverified | S20 is an acquirer's blog, not network rules, and its text did not load. Used in `solution.md` only as a tenant-tunable buffer marked [estimate] |
| Hold expiry 7 days, hotels and car rental 30 days (S18) | Unverified | Secondary merchant-services page. `solution.md` uses the processor's per-MCC expiry instead of a number |
| Fuel pre-auth cap $175, "Rete II 50 to 100x" | Unverified / vendor claim | Not used |
