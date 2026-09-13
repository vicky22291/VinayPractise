# Book seller broker: edge cases

> One-line answer: preserve the final-answer boundary, expose unknown seller coverage, and bound work at every failure point.

Use the [diagram index](diagrams.md) for visual rehearsal. Answers fit within about 60 seconds each. Learner confidence boxes are intentionally unmarked.

## Edge case: Ten sellers time out

- **Trigger:** 10 of 100 selected sellers miss the cutoff.
- **Symptom:** Missing offers, possibly including the cheapest.
- **Answer:** Return the minimum final-valid observed quote with PARTIAL and timeout counts. If no valid offer exists, return UNAVAILABLE, not no stock. Never claim globally cheapest.
- **Diagram:** [D5a](diagrams.md#d5a-seller-timeout-and-late-response).
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: A cheaper quote arrives after finalization

- **Trigger:** Late callback or socket completion.
- **Symptom:** A cheaper price appears after the buyer received a result.
- **Answer:** Final state is immutable. Drop the event for that query and record a bounded metric. A new comparison can observe newer prices; late events cannot resurrect deleted owner state.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: Quote and deadline execute together

- **Trigger:** Timer and outcome become runnable together.
- **Symptom:** Unsafe implementations double-count or publish twice.
- **Answer:** One serialized owner checks monotonic time immediately before acceptance. Accept only before cutoff; equality belongs to timeout. One terminal transition wins. Network arrival before cutoff is insufficient if validation finishes afterward.
- **Diagram:** [Cutoff race](deep-dives/deadlines-and-aggregation.md#the-cutoff-and-finalization-race).
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: A seller ignores cancellation

- **Trigger:** Local interest ends but server computation continues.
- **Symptom:** Background work, delayed cleanup, or continued charges.
- **Answer:** Freeze the answer and supervise bounded cleanup separately. Account local transport permits until completion; do not refund spent rate tokens. Remote concurrency guarantees require seller cooperation or a known maximum work lifetime.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: One seller blocks the runtime

- **Trigger:** Blocking SDK, DNS, parsing, or decompression on the shared event loop.
- **Symptom:** Healthy sellers also miss deadlines.
- **Answer:** Use nonblocking clients, bounded bodies, isolated worker pools for blocking adapters, and seller/process caps. Measure event-loop lag separately from seller latency; a bounded executor with an unbounded queue is insufficient.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: Healthy sellers have exhausted quota

- **Trigger:** Aggregate broker demand exceeds the seller contract.
- **Symptom:** Admission skips or HTTP 429.
- **Answer:** Enforce quota across replicas/regions, use permitted reuse, and report skipped coverage. Retry-After is useful only within remaining budget. Broker autoscaling does not increase seller capacity.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: Quota Redis fails over

- **Trigger:** Primary fails before recent debits replicate.
- **Symptom:** A replacement may reissue spent tokens.
- **Answer:** Atomic scripting is not a failover proof. Fail closed on uncertainty; hard ceilings need durable admission and fenced egress or conservative algorithm-specific recovery. Never reset a full bucket or allow two active dispatch authorities.
- **Diagram:** [Global admission](deep-dives/seller-limits-and-scale.md#global-rate-admission).
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: Broker crashes mid-request

- **Trigger:** Process dies after some responses.
- **Symptom:** Reset/error/timeout; in-memory offers disappear.
- **Answer:** Baseline retry creates a new query with jitter and admission. Preserving the same request requires committed query/outcome state and dispatch intents before durable acceptance. A load balancer cannot recover memory.
- **Diagram:** [D5b](diagrams.md#d5b-broker-crash).
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: Buyer retries after the answer was lost

- **Trigger:** Computed or committed answer was not delivered.
- **Symptom:** Caller cannot know whether the operation finished.
- **Answer:** Baseline performs a fresh read-only search, possibly at a different price. Durable mode returns the existing tenant-scoped idempotency mapping; changed payload with the same key returns 409. Replay is bounded by retention.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: A seller response is duplicated

- **Trigger:** Transport retry, callback redelivery, or outbox replay.
- **Symptom:** Counts falsely suggest every seller completed.
- **Answer:** Settle each `(queryId, sellerId)` once using known attempt IDs. Durable mode requires uniqueness plus the query-row lock used by finalization. Uniqueness alone does not prevent a late write after finalization.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: A hot book creates a thundering herd

- **Trigger:** Many identical requests arrive after cache expiry.
- **Symptom:** Provider overload despite reusable work.
- **Answer:** Coalesce by complete seller/context/version key, bound waiters, jitter expiry, and cap refresh admission. Cancellation removes only that waiter; work continues for others. Cache reuse must include tenant pricing and authorization scope.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: Traffic grows tenfold tomorrow

- **Trigger:** Peak becomes 12,000 searches/s.
- **Symptom:** Offered load becomes 1.2 M seller attempts/s.
- **Answer:** Preserve caps and expose rejection/coverage immediately. Scale measured broker bottlenecks while reducing duplicate calls and negotiating provider capacity. Retries and autoscaling must not bypass global rate admission.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: Directory grows to 100000 sellers

- **Trigger:** N increases by three orders of magnitude.
- **Symptom:** Blind fan-out needs 120 M attempts/s at the worked peak.
- **Answer:** Filter using a complete eligibility index where possible. A feed-ranked shortlist changes the guarantee and must be declared. If all sellers must be queried live, reconsider deadline, buyer rate, or contracts; a fan-out tree does not remove total calls.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: The cheapest quote expires

- **Trigger:** Lowest candidate expires before finalization or checkout.
- **Symptom:** A stored running minimum is no longer valid.
- **Answer:** Keep bounded candidates and revalidate at close to select the next valid offer. Cache TTL respects quote expiry and freshness limits. Checkout needs revalidation or a seller price guarantee/reservation, outside quote-only scope.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: Currency or price basis differs

- **Trigger:** Missing shipping, different currency, condition, or edition.
- **Symptom:** The numerical minimum is not comparable.
- **Answer:** Validate BookContext and price basis; compare integer minor units with currency-aware scale. Reject unknown components. Future currency conversion must pin rate/time and label an estimate; never silently mix landed and pre-tax prices.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: Seller changes its schema

- **Trigger:** Renamed fields, changed price units, or unknown enums.
- **Symptom:** Invalid quotes or a 100x price error.
- **Answer:** Version adapters, validate bounded schemas and money ranges, and compare against sanitized recordings. Unknown required semantics become INVALID. Pin adapter/comparison versions per query and include them in reuse keys.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: Feed backfill replays old prices

- **Trigger:** Optional catalog pipeline reprocesses old updates.
- **Symptom:** Stale cheap offers overwrite newer values or deleted listings return.
- **Answer:** Apply seller/offer sequence ordering, preserve tombstones, stage a versioned index, and reconcile snapshot/incremental handoff. Historical timestamps cannot be presented as fresh live quotes.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: Retention grows for three years

- **Trigger:** All quote observations are retained indefinitely.
- **Symptom:** 1.5 TB/day approaches 1.64 PB raw in three years.
- **Answer:** Avoid full retention by default; sample sanitized summaries and expire durable results within contract. Monitor expiry/outbox backlog and size indexes, WAL, and replicas separately from raw records.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: A tenant requests deletion

- **Trigger:** Privacy policy requires deletion of retained personal context.
- **Symptom:** Addresses or tenant-linked histories remain in logs/cache/results.
- **Answer:** Minimize context up front; delete or expire identifiable records under policy. Retain only permitted minimal dedup state. Signed callback expiry prevents deleted queries from being rebuilt, and backup expiry follows the retention policy.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: Region goes down

- **Trigger:** Entire broker region is unavailable.
- **Symptom:** Active searches are lost; failover can overload shared sellers.
- **Answer:** Route new comparisons to healthy capacity with retry control. Maintain global quotas or conservative regional allocations. Baseline cannot recover live query state; durable mode states DB RPO/RTO and fences the old primary before failover writes.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: Registry or cache is unavailable

- **Trigger:** Config DB, cache, or refresh path fails.
- **Symptom:** Unknown selection or increased live seller demand.
- **Answer:** Use last-known registry state only within bounded staleness and emergency revocation rules. Cache misses still pass provider/process caps. Without trustworthy eligibility, return unavailable rather than no eligible sellers.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: A rollout lowers coverage at 3am

- **Trigger:** Adapter, retry, or shared pool config regresses.
- **Symptom:** API is fast but quote yield falls.
- **Answer:** Alert on coverage/yield as well as latency. Diagnose seller-specific versus shared failures; roll back versioned adapter/policy while retaining quota caps. Recorded-response comparisons and peak-period canaries catch errors without doubling live calls.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: Buyer submits malicious input

- **Trigger:** Arbitrary seller URLs, huge bodies, or unbounded seller lists.
- **Symptom:** Internal network access or fan-out/memory amplification.
- **Answer:** Endpoints come from an allowlisted registry with egress, redirect, and DNS controls. Validate/cap inputs before work; enforce caller, query, process, and seller limits. Clients cannot choose arbitrary fan-out directly.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: Forged callback or cross-tenant reuse

- **Trigger:** Guessed query ID or incomplete pricing cache key.
- **Symptom:** Fake cheap quote or another tenant's negotiated price exposed.
- **Answer:** Authenticate/sign callback correlation with expiry and replay checks; authorize polling by owner. Include authorization scope in cache/coalescing keys. IDs alone grant no access and unauthenticated callbacks cannot create query state.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident
