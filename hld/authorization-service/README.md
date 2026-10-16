# Authorization service (RBAC + ReBAC + ABAC, Zanzibar style)

> One-line answer: one **central check service** answers `check(subject, permission, resource, context)` for every service, about **1 M checks a second at peak, p99 under 10 ms**. Permissions are a small, code-reviewed **schema**. Access facts are **relationship tuples** (`employee:e42#manager@employee:e7`, `role_binding:rb9#holder@group:hr#member`) stored in a 3-region consensus SQL store with MVCC. Custom roles are tuples, not schema. Request-time attributes (IP, ticket expiry) are **caveats** evaluated at check time. Every check runs at **one snapshot**: by default ~5 s old, so it is served from the local replica, and both cache layers are snapshot-correct (a late invalidation can make them miss, never lie). A content write gets a **zookie** (a snapshot token) from a fully consistent check and stores it with the content, so later reads demand "at least this fresh", which kills the new-enemy problem. Terminations use a **suspension overlay** that every check server polls every 500 ms and enforces in-process, so it denies within 2 s. The red node is the check service itself: it sits on every request, so it gets regional replicas, cells, a snapshot-keyed result cache with single-flight plus a watch-invalidated relation cache, a flattened group index for deep nesting, and **fails closed with a 503, never a 403**.

Tier 2, problem #30 in [`hld/README.md`](../README.md). Guide-only at **Stripe** ("redesign an internal authorization system across services", which a prep guide calls "one interviewer's staple") and **Rippling** ("permissions engine"). Google built the reference system (Zanzibar, USENIX ATC 2019). No first-hand candidate post names this prompt, so the README states the prompt in the shape both guides imply. Evidence: [`../company-questions.md`](../company-questions.md) §2 and §3.

Closest solved problems: [`../feature-flag-service/`](../feature-flag-service/) (same "decision on every request" shape, but flags are an 8 MB dataset you ship to every process, and tuples are a 1 TB dataset you cannot) and [`../distributed-denylist/`](../distributed-denylist/) (the suspension overlay is a small deny list). Reusable blocks: [`../../concepts/caching-patterns.md`](../../concepts/caching-patterns.md) (versioned keys, single-flight), [`../../concepts/mvcc-and-isolation.md`](../../concepts/mvcc-and-isolation.md), [`../../concepts/sharding.md`](../../concepts/sharding.md), [`../../concepts/oauth.md`](../../concepts/oauth.md) (authentication, which this service does not do). Sources: [`research/`](research/).

## Problem statement (as implied by the guides)

> Every service in the company decides "can this caller do this to this object" in its own code, against its own tables. Roles mean different things in different products, nobody can answer "who can see this employee's salary", and offboarding someone means hoping 400 services each remove them. Design one authorization system that every service calls. It must support fixed and customer-defined roles, relationships (manager of, owner of, member of a group, child of a folder), and conditions on attributes (department, network, time-bound access). It sits on the request path of every product.

Stripe's version adds: Dashboard roles, restricted API keys, Connect platforms acting on connected accounts, and support staff viewing merchant data. Rippling's version adds: roles scoped to attribute-defined groups of employees ("HR admin for everyone in Engineering in the US"), the manager chain, and instant revocation at termination. §12 of [`solution.md`](solution.md) maps both onto the same model.

## Clarifying questions, and the answers this design assumes

| Question | Assumed answer |
|---|---|
| Who calls it: our services only, or customers' own apps too? | Our ~400 internal services. Customers manage roles through our admin UI and API, which writes tuples. A customer-facing authz product is below the line |
| Authentication too? | No. The caller arrives with a verified identity (session, OAuth token, mTLS service identity). This service decides, it does not authenticate ([`../../concepts/oauth.md`](../../concepts/oauth.md)) |
| How many tenants, principals, objects, checks per second? | 200k tenants, 30 M principals (users, API keys, service accounts), ~3 B relationship tuples. 1 M checks/s at peak, 200k/s average |
| Latency budget per check? | p99 under 10 ms measured at the caller, in region. p50 ~2 ms. A request makes ~5 checks |
| How fast must a revoke take effect? | Termination or compromise: denied everywhere within 2 s. Ordinary revoke (removed from a group): within 10 s for default checks, immediately for checks that carry the write's zookie |
| Unreachable authz: fail open or closed? | Closed, as a **503 (retry)**, never a 403 (no access). A few reviewed low-risk reads may opt into a 60 s last-known decision |
| Do we need "list what I can see" and "who can see this"? | Yes. List pages, search, and quarterly access reviews need both |
| Audit? | Every deny and every check on a sensitive permission is logged with its snapshot and path. "Why does Bob have access?" is answerable |
| Data residency? | EU tenants' tuples stay in the EU. Below the line for the core design, seam in §10.11 |

## Functional requirements

Core:
1. **Check.** `check(subject, permission, resource, context, consistency)` returns ALLOW, DENY or CONDITIONAL (context missing), plus the snapshot it used. Batch form for up to 100 checks.
2. **Manage access facts and policy.** Services and tenant admins write relationship tuples atomically, with preconditions and idempotency, and get a zookie back. The platform team owns a versioned schema of permissions. Tenants define custom roles as data. Product databases (HRIS, documents) mirror their relationships in through change data capture.
3. **List and filter.** "Which employees can this user see" (LookupResources) and "who can see this object" (LookupSubjects), paged, fast enough for list pages and search.
4. **Audit and explain.** A decision log, an explain API that shows the path that granted access, and access reviews.

Below the line: authentication and sessions, customer-facing policy authoring (AWS IAM style JSON policies), row-level security inside each product database, entitlements by billing plan (that is feature flags, [#56](../feature-flag-service/)), consent management, data residency (seam only).

## Non-functional requirements

| Dimension | Target |
|---|---|
| Check latency | p50 ~2 ms, p99 < 10 ms at the caller, in region. Deadline 25 ms, then UNAVAILABLE. Checks that demand a very fresh snapshot: p99 < 100 ms in the tenant's home region |
| Write latency | p50 ~70 ms (every commit crosses regions) |
| Check throughput | 1 M/s peak, 200k/s average (~17 B/day) |
| Check availability | 99.99% per region at the caller (52 min/yr). A cell or region failure is invisible to callers in other cells and regions |
| Write throughput | 1k tuple writes/s average, 10k/s peak, bulk imports in a separate capped lane |
| Revocation | Suspension: 2 s p99 on every check server. Ordinary revoke: 10 s p99 for default checks, 0 s for checks carrying a zookie at or after the revoke |
| Consistency | Each check reads one snapshot (no torn reads). Writes are externally consistent. Default reads are bounded-stale (~5 s). `at_least_as_fresh(zookie)` gives causal consistency where it matters (new enemy) |
| Durability | RPO 0 for tuples and schema (synchronous consensus). The decision log tolerates loss of seconds |
| Scale | 3 B tuples (~0.9 TB logical), 200k tenants, largest tenant 100k employees and ~10 M tuples, groups nested up to 10 deep, folder trees up to 30 deep |

## What interviewers probe (the ladder)

1. RBAC, ABAC, or relationships? Model "managers see their reports' salary, HR admins see salary for their departments, support sees an account only during an open ticket" and say what each model cannot express.
2. Alice removes Bob from a document, then Charlie adds new text to it. How do you guarantee Bob never sees it? And why is the folder version of this question easier? (The new-enemy problem.)
3. You are on every request path at 1 M checks/s. How is p99 under 10 ms, and what happens when you are slow or down?
4. Cache invalidation: a role changes. Which cached decisions are wrong, and how do you avoid invalidating anything?
5. "Show me the 50 employees on page 3 that I can see" for an HR admin with 50k visible employees. Check each one, or something else?
6. An employee is terminated. How fast do they lose access everywhere, and how do you prove it?
7. Migrate 400 services that each have their own checks onto this without a single wrong deny.

## Files

| File | What it is |
|---|---|
| [`solution.md`](solution.md) | Full HLD in flow-first form: one incremental diagram, one walkthrough per FR, deep dives that mutate the design, then nitty-gritty |
| [`diagrams.md`](diagrams.md) | The D1 to D12 diagram set |
| [`edge-cases.md`](edge-cases.md) | Every "what if" with a 60-second answer and a confidence box |
| [`deep-dives/data-model-and-evaluation.md`](deep-dives/data-model-and-evaluation.md) | Tuples, schema, custom roles as data, caveats, dynamic groups, the check algorithm, a runnable evaluator |
| [`deep-dives/consistency-and-new-enemy.md`](deep-dives/consistency-and-new-enemy.md) | Snapshots, zookies, the default staleness, mirrored tuples and CDC lag, the suspension overlay, a revocation-window simulation |
| [`deep-dives/check-latency-caching-and-hot-spots.md`](deep-dives/check-latency-caching-and-hot-spots.md) | Dispatch by consistent hashing, the snapshot-keyed cache and tenant revisions, single-flight, hedging, the group index, hot tenants, capacity math |
| [`deep-dives/list-filtering-and-search.md`](deep-dives/list-filtering-and-search.md) | Post-filter vs LookupResources vs scope predicates vs ACLs in the search index, pagination, staleness at display time |
| [`deep-dives/availability-and-failure-modes.md`](deep-dives/availability-and-failure-modes.md) | Fail closed as 503, cells, regions, load shedding, circular dependencies, break-glass, the incidents that shaped it |
| [`deep-dives/migration-and-safe-policy-changes.md`](deep-dives/migration-and-safe-policy-changes.md) | From 400 services' own checks to one service with shadow mode, schema change validation by replay, audit, explain, access reviews |
| [`research/`](research/) | Raw web research with source links. Input to the files above, not study material |
| `authorization-service.excalidraw` | My drawing. Missing until I draw it |
