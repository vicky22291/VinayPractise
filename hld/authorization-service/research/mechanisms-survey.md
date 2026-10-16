# Authorization service: verified mechanisms survey

Study note input for: "Design a central authorization service (RBAC + ReBAC + ABAC, Zanzibar style) for a multi-tenant B2B SaaS company".

Research date: 2026-10-17. Method: fetched the Zanzibar paper PDF and extracted its text with `pdftotext`, then read the cited sections. Fetched SpiceDB, OpenFGA, Ory, OPA, and Cedar docs. Search results are marked as such.

## 0. How to read this file

- Every number has a source URL next to it.
- `[verified]` means I read the value in the primary source text.
- `[search snippet]` means the value came from a search result summary, not a full fetch.
- `[unverified]` means I could not confirm it from a primary source.
- Paper section numbers (`§`) refer to the USENIX ATC 2019 paper.
- Paper PDF: https://www.usenix.org/system/files/atc19-pang.pdf
- Paper page: https://www.usenix.org/conference/atc19/presentation/pang

## 1. One-line answer

A Zanzibar-style service stores relation tuples in a globally consistent database, evaluates nested graph checks with a shared cache and a lock table, and uses "zookies" (consistency tokens) so that a permission check never reads ACLs older than the content it guards.



## 2. Zanzibar paper: headline numbers

### 2.1 Scale and load

| Claim | Value | Quote | Source | Status |
|---|---|---|---|---|
| ACL volume | more than 2 trillion | "It stores more than two trillion ACLs" (§1) | https://www.usenix.org/system/files/atc19-pang.pdf | [verified] |
| Check rate | millions per second | "performs millions of authorization checks per second" (§1) | same | [verified] |
| Client QPS | more than 10 million | "Zanzibar serves more than 10 million client queries per second (QPS)" (§4) | same | [verified] |
| Peak Check | about 4.2M QPS | "Check requests peak at roughly 4.2M QPS" (7-day sample, Dec 2018) | same | [verified] |
| Peak Read | about 8.2M QPS | "Read at 8.2M" | same | [verified] |
| Peak Expand | about 760K QPS | "Expand at 760K" | same | [verified] |
| Peak Write | about 25K QPS | "and Write at 25K" | same | [verified] |
| Read vs write ratio | two orders of magnitude | "Queries that read data are thus two orders of magnitude more frequent than those that write data" | same | [verified] |
| Servers | more than 10,000 | "distributes this load across more than 10,000 servers" (§4) | same | [verified] |
| Clusters | several dozen | "organized in several dozen clusters around the world" | same | [verified] |
| Servers per cluster | under 100 to over 1,000, median near 500 | "ranges from fewer than 100 to more than 1,000, with the median near 500" | same | [verified] |
| Namespaces | more than 1,500 | "Zanzibar manages more than 1,500 namespaces" (§4.5) | same | [verified] |
| Tuples per namespace | one to a trillion, median near 15,000 | "tens to a trillion, with the median near 15,000" | same | [verified] |
| Replicas | more than 30 locations | "fully replicated in more than 30 locations around the world" | same | [verified] |
| Voting replicas | 5, in 3 metro areas, within 25 ms | "The 5 voting replicas ... within 25 milliseconds of each other" (§3.1) | same | [verified] |

Share of requests (derived, not in the paper): using the peak values above (not simultaneous peaks), Check is about 32%, Read about 62%, Expand about 6%, Write about 0.2% of the sum of peaks. The paper gives the peak numbers, not a percentage split. Source for inputs: the same paper, §4.

### 2.2 Latency

| Claim | Value | Quote | Source | Status |
|---|---|---|---|---|
| Headline | under 10 ms for most checks | "Zanzibar responds to more than 95% of authorization checks within 10 milliseconds" (§1) | https://www.usenix.org/system/files/atc19-pang.pdf | [verified] |
| Check Safe percentiles | about 3, 11, 20, 93 ms at p50, p95, p99, p99.9 | "peaks at roughly 3, 11, 20, and 93 msec, respectively" (§4.2, Figure 4) | same | [verified] |
| Table 2, Check Safe | mean (sd) of percentile per day: 3.0, 9.46, 15.0 ms at 50/95/99 | Table 2 | same | [verified] |
| Table 2, Check Recent | 2.86, 60.0, 76.3 ms at 50/95/99 | Table 2 | same | [verified] |
| Table 2, Write | 127, 233, 401 ms at 50/95/99 | Table 2 | same | [verified] |
| Spanner read | 0.5 ms median, 2 ms p95 | "Zanzibar's Spanner reads take 0.5 msec at the median, and 2 msec at the 95th percentile" (§4.4) | same | [verified] |
| Leopard | under 150 us median, under 1 ms p99 | "respond in fewer than 150 µsec at the median, or under 1 msec at the 99th percentile" (§4.4) | same | [verified] |

Note: the paper's p95 and p99 numbers are the Check Safe numbers. Recent checks are much slower (p95 60 ms). The p95 under 10 ms headline is for the Safe path.

### 2.3 Availability

| Claim | Value | Quote | Source | Status |
|---|---|---|---|---|
| Availability | above 99.999% over 3 years | "Availability has remained above 99.999% over the past 3 years of operation" (§4.3) | https://www.usenix.org/system/files/atc19-pang.pdf | [verified] |
| Downtime budget | under 2 min global downtime per quarter | "less than 2 minutes of global downtime" | same | [verified] |
| Error budget | under 13 min when error ratio above 10% | "fewer than 13 minutes when the global error ratio exceeds 10%" | same | [verified] |

### 2.4 Cache and RPC numbers

| Claim | Value | Quote | Source | Status |
|---|---|---|---|---|
| Delegated RPCs | 22M per second at peak | "At peak, Zanzibar handles 22 million internal 'delegated' RPCs per second" (§4.4) | https://www.usenix.org/system/files/atc19-pang.pdf | [verified] |
| In-memory lookups | about 200M per second at peak | "approximately 200 million lookups per second at peak, 150 million from checks and 50 million from reads" | same | [verified] |
| Check cache hit rates | 10% delegate side, +12% lock table; 2% delegator side, +3% lock table | §4.4 | same | [verified] |
| Delegated read hit rates | 24% cache, 9% lock table on delegate side | §4.4 | same | [verified] |
| Cache effect | prevents 500K internal RPCs/s from creating hot spots | "they prevent 500K internal RPCs per second from creating hot spots" | same | [verified] |
| Hedging of Spanner | 1% of Spanner reads, 200K/s, benefit | "1% of Spanner reads, or 200K reads per second, benefit from hedging" | same | [verified] |
| Hedging delay | "Nth percentile" latency; exact N not in extracted text | §3.2.7 | same | [unverified] for the exact N |

The paper does not give an overall cache hit rate. The numbers above are per-path rates for specific paths.

## 3. Data model and API (Zanzibar)

### 3.1 Relation tuples

- Format: `object#relation@user`. The paper's grammar is `<namespace>:<object id>#<relation>@<user>`. Source: §2.1, https://www.usenix.org/system/files/atc19-pang.pdf.
- A userset lets a tuple point to a set: `doc:readme#viewer@group:eng#member`. Source: §2.1 (userset grammar).
- Primary key of a tuple: namespace, object id, relation, user. Source: §2.1.
- Storage: each namespace has its own database; rows keyed by (shard ID, object ID, relation, user, commit timestamp). Multiple versions are kept so checks can read any timestamp inside the GC window. Source: §3.1.1.

### 3.2 Namespace config and userset rewrite rules

Rewrite rules are per relation. Three building blocks, quoted from §2.3.1:

- `_this`: "Returns all users from stored relation tuples" for the object. Default when no rewrite rule is given.
- `computed_userset`: computes a userset from the same object (for example, "editor" implies "viewer").
- `tuple_to_userset`: follows a tuple (for example, `parent` folder) and evaluates a relation on the target.

Set operators: union, intersection, and exclusion (§2.3.1). Figure 1 in the paper is a `viewer` rule that is a union of `_this`, `computed_userset editor`, and `tuple_to_userset parent->viewer`. Source: https://www.usenix.org/system/files/atc19-pang.pdf.

### 3.3 APIs

| API | Purpose | Source |
|---|---|---|
| Check | "does user U have relation R to object O?" | §1, §2.4.4 |
| Read | Read tuples with optional zookie; can read a set of tuplesets | §2.4.1 |
| Expand | Returns the effective userset as a tree; set nodes are union, intersection, exclusion | §2.4.5 |
| Write | Add or remove tuples; optimistic read-modify-write with a lock tuple | §2.4.2 |
| Watch | Stream of tuple changes from a zookie; heartbeat zookies for resume | §2.4.3 |

Watch details: "A watch request specifies one or more namespaces and a zookie representing the time to start watching" (§2.4.3). Source: https://www.usenix.org/system/files/atc19-pang.pdf.

Content-change check: a special check with no zookie. It is evaluated at the latest snapshot, and the response returns a zookie for the content version (§2.4.4).

## 4. Zanzibar consistency

### 4.1 The "new enemy" problem

The paper gives two examples (§1, page 1 to 2). Quoted steps:

- Example A, neglecting ACL update order: "Alice removes Bob from the ACL of a folder; ... Bob should not be able to see the new documents, but may do so if the ACL check neglects the ordering between the two ACL changes."
- Example B, misapplying old ACL to new content: "Alice removes Bob from the ACL of a document; ... Bob should not be able to see the new contents, but may do so if the ACL check is evaluated with a stale ACL from before Bob's removal."

Source: https://www.usenix.org/system/files/atc19-pang.pdf (§1).

The fix: "External consistency and snapshot reads with staleness bounded by zookie prevent the 'new enemy' problem" (§2.2). Source: same.

### 4.2 Zookies

- Definition: "A zookie is an opaque byte sequence encoding a client content version, or a read snapshot." Source: §2.4.
- How clients get and store one: the client calls a content-change check before saving content. Zanzibar "encodes a current global timestamp in the zookie and ensures that all prior ACL writes have lower timestamps." The client stores the zookie "in an atomic write to the client storage." Source: §2.2.
- How it is used: "The client sends this zookie in subsequent ACL check requests to ensure that the check snapshot is at least as fresh as the zookie" (§2.2).
- Staleness rule: "a check is always evaluated at a consistent snapshot no earlier than the given zookie" (§2.4.4).
- Without a zookie: "If the request doesn't contain a zookie, Zanzibar will choose a reasonably recent snapshot, possibly offering a lower-latency response" (§2.4.1). Source: same.

### 4.3 Snapshot reads on Spanner, TrueTime, default staleness

- Storage: Spanner, with external consistency. Source: §2.2 and §3.1.
- Default staleness: the server learns a "safe" staleness per request from hints on each Spanner read, updates the default to the lowest safe value, and can raise it with a two-proportion z-test (§3.2.1). Quote: "This default staleness mechanism is purely a performance optimization. It does not violate consistency semantics because Zanzibar always respects zookies when provided." Source: §3.2.1.
- Safe vs Recent: "Safe requests have zookies more than 10 seconds old and can be served within the region most of time, while Recent requests" need the leader (§4.2). Source: same.
- Quantization: "We choose evaluation timestamps rounded up to a coarse granularity, such as one or ten seconds, while respecting staleness constraints from request zookies" (§3.2.1 region, quantization paragraph). Quantization keeps cache keys shared. The paper gives no hit-rate percentage for this effect. [unverified] for any exact percentage.
- TrueTime: "a snapshot read at timestamp T will observe all writes up to T ... even if T is in the future, in which case the read will wait until TrueTime has moved past T" (§3.2.1 region). Source: same.

## 5. Zanzibar serving

### 5.1 Consistent hashing and cache

- "Cache entries are distributed across Zanzibar servers with consistent hashing." Source: §3.2.5 (https://www.usenix.org/system/files/atc19-pang.pdf).
- Servers "delegate checks and reads to each other based on consistent hashing, and both the caller and the callee sides ... cache the results" (§4.4).
- Cache key includes the snapshot timestamp: "We avoid reusing results evaluated from a different snapshot by encoding snapshot timestamps in cache keys" (§3.2.4 region).
- Blog summary of the same mechanism: https://authzed.com/blog/hotspot-caching-in-google-zanzibar-and-spicedb (AuthZed, vendor blog). It says the cache "is used to address latency problems when the same data is accessed frequently." It gives an example of quantization "up to 1s stale" with a 1 s interval.

### 5.2 Lock table and request deduplication (cache stampede)

- "To handle the 'cache stampede' problem, where concurrent requests create flash hot spots before the cache is populated with results, we maintain a lock table on each server to track outstanding reads and checks." Source: §3.2.4 region.
- Eager cancellation: "we delay eager cancellation when there are waiters on the corresponding lock table entry." Source: §3.2.5.
- Lock table keys are per client, so Spanner throttling of one client does not affect another (§3.2.6). Source: same.

### 5.3 Hot spots

- "We found the handling of hot spots to be the most critical frontier in our pursuit of low latency and high availability." Source: §3.2.5.
- Hot objects: the paper reads and caches all tuples of a hot object:key. Hot objects are detected by tracking request rates (§3.2.5). Source: same.
- Super-hot groups: "For super-hot groups, Zanzibar further optimizes..." (§4.4). Source: same.
- Hot forwarding keys: "To handle hot forwarding keys, we cache results ... attribute hot keys to multiple servers" (§3.2.4). Source: same.

### 5.4 Hedged requests

- Hedging for Spanner and Leopard only. "we send one request and defer sending hedged requests until the initial request is known to be slow" (§3.2.7).
- Delay: a per-server estimator tracks an "Nth percentile latency" (§3.2.7). The text I extracted does not give the value of N. [unverified] for the exact delay.
- No hedging between Zanzibar servers, because "Hedging check requests would result in duplicating the most expensive workloads" (§3.2.7).

### 5.5 Leopard index

- Purpose: "Recursive pointer chasing during check evaluation has difficulty maintaining low latency with groups that are deeply nested or have a large number of child groups." Leopard "supports efficient set computation." Source: §3.2.4.
- Stored form: `(T, s, e)` tuples, where T is the set type and s and e are 64-bit set and element IDs. Queries are union, intersection, or exclusion of named sets. Source: §3.2.4.
- Group membership: the paper names `MEMBER2GROUP` in the index functions (§3.2.4). I did not verify `GROUP2GROUP` in the extracted text. [unverified] for the exact name.
- Incremental updates: "Leopard servers maintain an incremental layer that indexes all updates since the offline snapshot, where each update is represented by a (T, s, e, t, d) tuple" (§3.2.4). Updates come from the Watch stream.
- Numbers (7-day sample): 1.56M QPS median, 2.22M QPS p99; under 150 us median latency, under 1 ms p99; incremental layer writes about 500 updates/s median and 1.5K/s p99 (§4.4). Source: same.

### 5.6 Deep and wide nesting, deadlines

- Deep and wide nesting is handled by Leopard for selected namespaces (§3.2.4).
- Deadlines: the paper says clients "sometimes send RPCs with short deadlines or cancel their in-progress RPCs" (§4.2). No default deadline value is stated in the extracted text. [unverified] for any default.
- Limits: each server limits concurrent RPCs and "limits the maximum number of concurrent reads per (object, client)" (§3.2.6).

### 5.7 Changelog and Watch

- Changelog: "a history of tuple updates for the Watch API" (§3.1.2).
- Watchservers "tail the changelog and serve a stream of namespace changes to clients in near real time" (§3.1 diagram text). Source: same.

## 6. SpiceDB (AuthZed)

### 6.1 Schema language

Source: https://authzed.com/docs/spicedb/concepts/schema

- Definition: "An Object Type definition is used to represent classes of objects."
- Relation: "defines how two objects (or an object and subject) can relate to one another."
- Permission: "a _computed_ set of subjects"; permissions cannot be written as relationships.
- Arrow `->`: "walks from one object to a related object." Example: `parent_folder->read`.
- Set operators: `+` union, `&` intersection, `-` exclusion. Union binds more tightly than `&` and `-`. The docs recommend parentheses.
- Caveats: "Caveats are expressions that can return true or false." Example: `caveat ip_allowlist(user_ip ipaddress, cidr string) { user_ip.in_cidr(cidr) }`. The page does not name CEL.
- No limit on schema size or relation count on the schema page. Identifiers are "3-64 characters long and end with an alphanumeric character."

### 6.2 Relationship format and expiration

Source: https://authzed.com/docs/spicedb/concepts/relationships

- Format: `document:readme#editor@user:emilia`.
- Usersets: `document:readme#editor@team:engineering#member`.

Expiring relationships (source: https://authzed.com/docs/spicedb/concepts/expiring-relationships):

- Syntax: a schema `use expiration` clause and `<type> with expiration`; the API field is `OptionalExpiresAt` in RFC 3339 format.
- Version: the page says "After SpiceDB v1.4.0". The same page also has a stray "v1.40" mention. The version is [verified] as v1.4.0 from the page text, with the typo flagged.
- At expiry: "As soon as a relationship expires, it will no longer be used in permission checks." Physical deletion happens at GC.
- GC: "expired relationships will be reclaimed after 24 hours" on Spanner and CockroachDB. Postgres and MySQL use a GC job with a configurable 24 h default.
- Caveat: "SpiceDB will respond with the cached value even if a fresh datastore read would exclude that relationship." Use `fully_consistent` to avoid this.

### 6.3 Consistency options and ZedTokens

Source: https://authzed.com/docs/spicedb/concepts/consistency

- `minimize_latency`: "will attempt to minimize the latency of the API call." It can leave a window for the New Enemy Problem.
- `at_least_as_fresh`: data "at least as fresh as the point-in-time specified in the ZedToken."
- `at_exact_snapshot`: "It is recommended to only use this option if you are paginating over results within a short window." Can fail with "Snapshot Expired" after GC.
- `fully_consistent`: "This consistency mode explicitly bypasses caching, dramatically impacting latency."
- ZedToken: "A ZedToken is an opaque token representing a point-in-time of the SpiceDB datastore." It is the SpiceDB equivalent of the Zanzibar zookie.
- Defaults: "WriteRelationships, DeleteRelationships, ReadSchema, and WriteSchema default to fully_consistent. All other APIs default to minimize_latency."

### 6.4 Revision quantization and defaults

Source for values: https://authzed.com/docs/spicedb/concepts/commands and the Go flag source at https://github.com/authzed/spicedb/blob/main/pkg/cmd/datastore/datastore.go.

| Flag | Default | Source | Status |
|---|---|---|---|
| `--datastore-revision-quantization-interval` | `5s` | commands page: "boundary interval to which to round the quantized revision" | [verified] |
| `--datastore-revision-quantization-max-staleness-percent` | `0.1` ("1 = 100%") | commands page: "Defaults to 0.1 (representing 10%)" | [verified] |
| `--datastore-gc-window` | `24h0m0s` | commands page | [verified] |
| `--dispatch-max-depth` | `50` | commands page: "maximum recursion depth for nested calls" | [verified] |
| `--dispatch-cache-max-cost` | `30%` of memory | commands page | [verified] |
| `--dispatch-cache-enabled` | `true` | commands page | [verified] |
| `--dispatch-hashring-replication-factor` | `100` | commands page | [verified] |
| `--dispatch-chunk-size` | `100` | https://authzed.com/docs/spicedb/ops/performance: "Start with the default (100)" | [verified] |

Quantization in the SpiceDB docs: the quantization interval "determines how long cached results will live" (load-testing guide, https://authzed.com/blog/spicedb-load-testing-guide, January 17, 2024). An Issue thread (search snippet only) describes a worst case of 500 ms staleness with the defaults. [unverified].

### 6.5 Dispatch and caching

- Dispatch across nodes uses consistent hashing (the `--dispatch-hashring-replication-factor` flag above).
- Dispatch cache: "Each SpiceDB node maintains an in-memory cache of permissions queries it has resolved in the past." Source: https://authzed.com/docs/spicedb/ops/performance.
- Max depth: 50 by default (commands page above).

### 6.6 LookupResources, LookupSubjects, CheckBulkPermissions

- Cost: the load-testing guide says intersections and exclusions "can significantly hurt LookupResources performance." Source: https://authzed.com/blog/spicedb-load-testing-guide (search snippet only, not full fetch).
- The schema docs warn that arrows over subject relations would force a full LookupSubjects call, making CheckPermission potentially very expensive. Source: https://authzed.com/docs/spicedb/concepts/schema (search snippet).
- Pagination: AuthZed's list-endpoint guide suggests a loop of fetch, bulk check, repeat, with cursor-based paging. Source: https://authzed.com/docs/spicedb/modeling/protecting-a-list-endpoint (search snippet only).
- CheckBulkPermissions per-request item cap: not found in primary docs. [unverified].
- LookupResources cost units and per-call limits: not found in primary docs. [unverified].
- Cursor support: the April 2026 changelog says the Postgres FDW datastore "fully supports cursoring" for LookupResources, LookupSubjects, and ReadRelationships. Source: https://authzed.com/changelog (search snippet only). [unverified].

### 6.7 Datastores and their consistency

Source: https://authzed.com/docs/spicedb/concepts/datastores

- CockroachDB: "`fully_consistent` does not guarantee read-after-write consistency on CockroachDB." Read-after-write needs a ZedToken with `at_least_as_fresh`. Watch via native changefeed.
- Cloud Spanner: "relies on Google's TrueTime." The driver "assumes the database is linearizable." Watch: not named on that page.
- PostgreSQL: read replicas keep consistency, falling back to the primary. Watch requires commit timestamp tracking. Postgres 15 or newer advised.
- MySQL: "Not recommended; only use if you cannot use PostgreSQL." Replicas cannot sit behind a load balancer and still keep consistency.
- memdb: data is ephemeral. "Cannot be ran highly-available as multiple instances will not share the same in-memory data."

### 6.8 Published benchmark numbers

- The load-testing guide (https://authzed.com/blog/spicedb-load-testing-guide, dated January 17, 2024) gives no QPS or latency numbers. It gives scaling advice such as "less than 30% CPU utilization." [verified: no numbers].
- The hotspot caching blog gives no measured hit rates. [verified: no numbers].
- A "1 million QPS" benchmark: not found in the sources I read. [unverified, not found].

### 6.9 AuthZed Materialize

Source: https://authzed.com/docs/authzed/concepts/authzed-materialize (search snippet for the description).

- "You give it a list of permissions to precompute, and it recalculates them as relationships or schemas change."
- Accelerated Queries serve CheckPermission, CheckBulkPermissions, LookupResources, and LookupSubjects from a precomputed cache.
- It subscribes to SpiceDB's change stream and computes "only the affected permission deltas."
- Availability: a blog post (https://authzed.com/blog/authzed-materialize-generally-available) is listed as dated September 10, 2026 in a search snippet. The product page says early access. [unverified] for GA status.

## 7. OpenFGA

### 7.1 Modeling and conditions

Source: https://openfga.dev/docs/modeling/conditions

- Conditions use CEL. Conditions are declared as named blocks with typed parameters, for example `condition non_expired_grant(current_time: timestamp, grant_time: timestamp, grant_duration: duration)`.
- A type restriction then requires the condition: `user with non_expired_grant`.
- Server CEL cost cap: "a maximum Google CEL expression evaluation cost of 100 (by default)".
- Persisted condition context on a tuple: "limited to 32KB in size."
- Request-time context: "overall request size limit of 512KB."
- Contextual tuples: not covered on that page. [unverified] for any contextual tuple details.

### 7.2 Consistency

Source: https://openfga.dev/docs/interacting/consistency

- Two options: MINIMIZE_LATENCY (default) and HIGHER_CONSISTENCY.
- MINIMIZE_LATENCY: "OpenFGA will serve queries from the cache when possible."
- HIGHER_CONSISTENCY: "OpenFGA will skip the cache and query the database directly."
- Caching is disabled by default. Then every query is strongly consistent, whatever mode is set.

### 7.3 ListObjects and BatchCheck limits

Source: https://openfga.dev/docs/interacting/relationship-queries (fetched).

- `listObjectsDeadline`: default 3s.
- `listObjectsMaxResults`: default 1000.
- Whichever limit is hit first ends the search. Partial results come back without a signal that they are incomplete (GitHub issue, not docs): https://github.com/openfga/openfga/issues/2828.
- The streamed ListObjects variant has no fixed count cap, only the deadline (search snippet of the API docs).
- BatchCheck: server cap per request, and the SDK default is 50 "configurable on the server" (https://openfga.dev/docs/interacting/batch-check). Default server cap not stated on that page. [unverified].

### 7.4 Performance numbers

- Not searched in depth. OpenFGA published performance figures: [unverified, not found in this pass].

## 8. Ory Keto

- Self-description (https://www.ory.com/docs/keto, fetched via redirect from ory.sh/docs/keto): "the first and most popular open source implementation of 'Zanzibar'." It also claims "Low latency permission checks (sub-10ms)" and "Horizontal scaling to billions of relationships." These are vendor claims. [unverified as benchmarks].
- Supports ReBAC. Namespaces use the Ory Permission Language (`class Document implements Namespace {}`).
- Snaptokens: a search snippet of the Keto proto docs says the check `snaptoken` field "is not implemented yet and has no effect." Source: https://github.com/ory/keto (search only). [unverified against current code].
- Caching: the Keto guide advises against caching responses for revocations. [search snippet].
- The open source edition is described as suitable for "run unimportant workloads without SLAs." Source: Keto site above.

## 9. Policy engines for contrast

### 9.1 OPA

- Decision logs: each event "includes the policy that was queried, the input to the query," plus bundle metadata. Source: https://www.openpolicyagent.org/docs/latest/management-decision-logs/ [verified].
- Upload interval and buffer defaults: not stated on that page. [unverified].
- Rate limit option: `max_decisions_per_second` sets "the maximum number of decision log events to buffer per second," and OPA "will drop events if the rate limit is exceeded." Same source.
- Partial evaluation for data filtering: "OPA can be used to derive the needed SQL filter at run time, leveraging OPA's partial evaluation feature." Example output: `WHERE employees.department = 'engineering'`. Source: https://www.openpolicyagent.org/docs/latest/filtering/ [verified].
- No latency numbers in these pages. [unverified].

### 9.2 AWS Cedar

- Conflict rule: "If any forbid policy evaluates to true, then the final result is Deny." Source: https://docs.cedarpolicy.com/auth/authorization.html [verified].
- Default: "by default, the decision is Deny." Same source [verified].
- Analyzable: Cedar validates policies against a schema (https://docs.cedarpolicy.com/overview/terminology.html and the Cedar site). The "analyzable" property as a formal claim is from the Cedar paper, not checked here. [unverified].
- Evaluation latency: no measured numbers found in primary sources. A third-party benchmark exists (https://goteleport.com/blog/benchmarking-policy-languages/), but it is not primary. [unverified].

### 9.3 Amazon Verified Permissions

- Quota: IsAuthorized is 200 requests per second per Region, adjustable. Source: https://docs.aws.amazon.com/general/latest/gr/verifiedpermissions.html and https://aws.amazon.com/about-aws/whats-new/2024/03/amazon-verified-permissions-default-quota-authorization-apis/ (search snippets, not fetched). [search snippet].
- The raise from 30 TPS to 200 TPS was in March 2024 (AWS what's new post, search snippet). [search snippet].
- BatchIsAuthorized default: 30 requests per second per Region per policy store (search snippet). [search snippet].
- Latency numbers: not found. [unverified].

## 10. Contradictions and gaps

- The SpiceDB quantization staleness: the flag text says "1 = 100%" and the default reads "0.1." Consistent. Earlier search results said "10%". Same value.
- Expiring relationships: the doc says "v1.4.0" and then "v1.40" in a caveat paragraph. Treat v1.4.0 as the intended version. [verified with note].
- Zanzibar p95 headline: "under 10 ms" is the aggregate; Check Safe p95 is about 11 ms and Recent p95 is 60 ms (Table 2 and Figure 4). Quote both when used.
- The Zanzibar paper gives no request deadlines, no hedging delay value, no hit-rate for quantization, and no max depth. Use SpiceDB's 50 as the reference, labeled as SpiceDB.
- No primary source gave published latency numbers for SpiceDB, OpenFGA, Cedar, or AVP. Use the Zanzibar numbers as the only verified latency baseline.

## 11. Numbers to use

| # | Number | Value | Source URL | Status |
|---|---|---|---|---|
| 1 | ACLs stored | more than 2 trillion | https://www.usenix.org/system/files/atc19-pang.pdf (§1, §2.1) | [verified] |
| 2 | Client QPS | more than 10 million | same (§4) | [verified] |
| 3 | Peak Check QPS | about 4.2M | same (§4) | [verified] |
| 4 | Peak Read QPS | about 8.2M | same (§4) | [verified] |
| 5 | Servers | more than 10,000 | same (§4) | [verified] |
| 6 | Clusters | several dozen | same (§4) | [verified] |
| 7 | Namespaces | more than 1,500 | same (§4.5) | [verified] |
| 8 | Check p95 under 10 ms (headline) | more than 95% of checks | same (§1) | [verified] |
| 9 | Check Safe p95 / p99 | about 11 ms / 20 ms | same (§4.2) | [verified] |
| 10 | Check Recent p95 | about 60 ms | same (Table 2) | [verified] |
| 11 | Availability | above 99.999%, 3 years | same (§4.3) | [verified] |
| 12 | Leopard QPS (median / p99) | 1.56M / 2.22M | same (§4.4) | [verified] |
| 13 | Leopard latency (median / p99) | under 150 us / under 1 ms | same (§4.4) | [verified] |
| 14 | Safe zookie age | older than 10 s | same (§4.2) | [verified] |
| 15 | Timestamp quantization | 1 or 10 s (paper) | same (§3.2.4 region) | [verified] |
| 16 | SpiceDB quantization interval | 5s | https://authzed.com/docs/spicedb/concepts/commands | [verified] |
| 17 | SpiceDB quantization staleness | 0.1 (10%) | https://authzed.com/docs/spicedb/concepts/commands | [verified] |
| 18 | SpiceDB dispatch max depth | 50 | https://authzed.com/docs/spicedb/concepts/commands | [verified] |
| 19 | SpiceDB dispatch chunk size | 100 | https://authzed.com/docs/spicedb/ops/performance | [verified] |
| 20 | SpiceDB GC window | 24h | https://authzed.com/docs/spicedb/concepts/commands | [verified] |
| 21 | SpiceDB expiration introduced | v1.4.0 | https://authzed.com/docs/spicedb/concepts/expiring-relationships | [verified, typo noted] |
| 22 | Expired row reclaimed (Spanner, CRDB) | 24 h | same | [verified] |
| 23 | OpenFGA CEL cost cap | 100 | https://openfga.dev/docs/modeling/conditions | [verified] |
| 24 | OpenFGA condition context per tuple | 32 KB | same | [verified] |
| 25 | OpenFGA ListObjects deadline | 3 s | https://openfga.dev/docs/interacting/relationship-queries | [verified] |
| 26 | OpenFGA ListObjects max results | 1000 | same | [verified] |
| 27 | OpenFGA BatchCheck SDK default | 50 | https://openfga.dev/docs/interacting/batch-check | [verified] |
| 28 | AVP IsAuthorized quota | 200 RPS per Region | https://docs.aws.amazon.com/general/latest/gr/verifiedpermissions.html | [search snippet] |
| 29 | AVP BatchIsAuthorized quota | 30 RPS per Region | search snippet | [search snippet] |
| 30 | Cedar default decision | Deny | https://docs.cedarpolicy.com/auth/authorization.html | [verified] |
| 31 | SpiceDB published QPS benchmark | none found | https://authzed.com/blog/spicedb-load-testing-guide | [unverified, not found] |
| 32 | Hedging delay (Zanzibar) | Nth percentile, N not given | https://www.usenix.org/system/files/atc19-pang.pdf (§3.2.7) | [unverified] |
