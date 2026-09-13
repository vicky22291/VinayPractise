# Payment Systems Mechanisms: Double-Entry Ledger & Duplicate Prevention

## Sources Reference Table

| ID | URL | Establishes |
|---|---|---|
| S1 | https://docs.stripe.com/api/idempotent_requests | Stripe idempotency key 24-hour retention, fingerprint check behavior |
| S2 | https://datatracker.ietf.org/doc/html/draft-ietf-httpapi-idempotency-key-header-07 | IETF draft v7 idempotency key spec, UUID recommendation |
| S3 | https://brandur.org/idempotency-keys | Brandur's locked_at, recovery_point, atomic phases pattern |
| S4 | https://kafka.apache.org/41/configuration/producer-configs/ | Kafka max.in.flight (5), transaction.timeout.ms (60000 ms), enable.idempotence requirements |
| S5 | https://cwiki.apache.org/confluence/display/KAFKA/KIP-98+-+Exactly+Once+Delivery+and+Transactional+Messaging | Kafka KIP-98 producer IDs, sequence numbers, exactly-once per partition |
| S6 | https://cwiki.apache.org/confluence/display/KAFKA/KIP-129%253A%2BStreams%2BExactly-Once%2BSemantics | Kafka KIP-129 streams exactly-once with sendOffsetsToTransaction |
| S7 | https://microservices.io/patterns/data/transactional-outbox.html | Transactional outbox pattern, message relay |
| S8 | https://microservices.io/patterns/data/saga.html | Saga pattern, compensating transactions, orchestration vs choreography |
| S9 | https://www.moderntreasury.com/journal/double-entry-accounting | Modern Treasury double-entry: debits == credits, account normality |
| S10 | https://www.moderntreasury.com/journal/what-is-a-ledger | Ledger basics, journal entries, immutable append-only |
| S11 | https://docs.tigerbeetle.com/single-page/ | TigerBeetle batch size 8,190, pending/posted two-phase, no row locks |
| S12 | https://www.postgresql.org/docs/current/mvcc-serialization-failure-handling.html | Postgres SSI error 40001 (serialization_failure) |
| S13 | https://www.postgresql.org/docs/current/runtime-config-locks.html | Postgres deadlock_timeout default 1 second |
| S14 | https://en.wikipedia.org/wiki/Rounding | Banker's rounding (round-to-even) vs half-up |
| S15 | https://en.wikipedia.org/wiki/ISO_8583 | ISO 8583: MTI codes, reversals (0400), advice messages |
| S16 | https://research.google.com/pubs/archive/45855.pdf | Spanner external consistency stronger than linearizability, CAP position |
| S17 | https://docs.aws.amazon.com/qldb/latest/developerguide/qldb-glossary.html | QLDB immutable journal, hash chains, digests, tamper-proof |
| S18 | https://www.cockroachlabs.com/solutions/usecases/payments/ | CockroachDB serializable isolation for payments |
| S19 | https://docs.stripe.com/error-low-level | Stripe unknown outcome problem: timeout returns indeterminate, retry with idempotency key |
| S20 | https://www.moderntreasury.com/journal/how-to-scale-a-ledger-part-v | Modern Treasury immutability, discarded_at timestamps |

---

## 1. Idempotency Keys End to End

Client generates UUID v4/v7 or high-entropy string (up to 255 chars, no sensitive data) [S1][S2].
Scope: per-account per-endpoint, stored in unique index on `(account_id, idempotency_key)` [S1].

Request fingerprint check: same key + different body returns 409 Conflict [S1].
In-progress state: return 409 Conflict while first attempt is running; acquire lock to serialize retries.

Storage: save response status code and body, regardless of success/failure.
Retention: minimum 24 hours; can be pruned after 24 hours [S1].

Lock/lease pattern (Brandur): use atomic phases with `locked_at` (indicates active processing) and `recovery_point` (text label of last completed phase: "started" → "ride_created" → "charge_created" → "finished") [S3].
Each phase commits in SERIALIZABLE transaction before next phase.
On retry, jump to recovery_point instead of restarting.
Fingerprint mismatch: return 409 or 400, reject divergent parameters with same key [S1][S3].

---

## 2. Exactly-Once Effects Across Services

At-least-once delivery + idempotent consumer = effectively exactly-once [S7].

Transactional outbox pattern: write event + state in one DB txn, commit atomically [S7].
Message relay retrieves outbox messages and publishes to Kafka (may publish duplicates if relay crashes).
Consumer deduplicates via inbox table tracking message IDs already processed [S7].

Kafka producer: idempotence requires `enable.idempotence=true`, `max.in.flight.requests.per.connection <= 5`, `retries > 0`, `acks=all` [S4].
Transactions: use `transactional.id` to assign producer ID; `producer.sendOffsetsToTransaction()` wraps offset commits atomically with message writes [S5][S6].
Exactly-once per partition: producer deduplicates via sequence numbers (each message tagged with PID + sequence); replays detected and rejected [S5].
Important: exactly-once per partition only, NOT across multiple partitions without transactions [S5].

Dual-write problem: if you write to DB and separately to Kafka, one can fail; solved by outbox (DB is source of truth, relay publishes) [S7].

---

## 3. Double-Entry Ledger Invariants

Core rule: debits == credits per journal entry; sum of all balances == 0 [S9].

Entries immutable, append-only; no updates, only reversals (new entries that negate) [S20].
Account types: asset (owns money), liability (owes money), normal balance side (asset-debit increases, liability-credit increases) [S9].

Journal entry = ordered list of 2+ ledger entries (each with direction: debit or credit) [S9].
Entry line = individual debit or credit amount in an entry.

States: pending (authorization hold), posted (settled), available (posted balance minus pending holds) [S11].
Effective date (when transaction logically occurs) vs posted date (when recorded in ledger).
Multi-currency: each line specifies amount + currency; conversion at entry time or post time, with rounding applied per line [S20].

Reversals instead of updates preserve audit trail and prevent reuse-after-delete [S20].

---

## 4. Hot Account Problem & Balance Contention

Single merchant/platform account row becomes serialization point: row lock limits updates to ~1000s per second in Postgres per row [unverified exact number].
Symptom: deadlock timeouts, p99 latency spikes.

Fixes:
- Balance sharding / sub-accounts: split account balance across N sub-accounts, read-sum on balance queries [unverified pattern name].
- Append-only entries + snapshots: store immutable ledger lines, compute running balance at checkpoint + tail sum on read.
- Balance buckets: similar to sharding, bucket by transaction time.
- Optimistic concurrency: version number on balance row, `UPDATE ... WHERE version = old_version AND balance >= amount` [unverified].

TigerBeetle answer: single-threaded state machine, no row locks, batch up to 8,190 transfers per request [S11].
Result: ~1M TPS without contention (claim stated on homepage; exact TPS in primary docs not pinned [unverified]).

---

## 5. Overdraft / Negative Balance Prevention Under Concurrency

SELECT ... FOR UPDATE: row lock, serializes all updates, bottleneck at scale.
Serializable isolation (Postgres SSI): `SET TRANSACTION ISOLATION LEVEL SERIALIZABLE` [S12].
If serialization violation occurs, Postgres rejects with error 40001 (serialization_failure); application retries whole transaction [S12].

Conditional update: `UPDATE account SET balance = balance - amount WHERE balance >= amount` [unverified exact syntax].
Two-phase transfers (TigerBeetle): pending phase reserves funds (updates pending field only, fails if would go negative), then post phase commits (updates posted) [S11].

Sharded balance: reserve from one shard; if insufficient, fallback to rebalancing across shards (requires careful coordination, risk of deadlock).

---

## 6. Distributed Transactions: Ledger + Processor + External Rail

2PC does NOT extend to external card networks (no coordinator, unreliable).

Saga pattern: state machine per payment (created -> authorized -> captured -> settled -> refunded/reversed/failed) [S8].
Each step publishes event that triggers next service. Compensating transactions unwind on failure [S8].
Orchestration: central state machine drives flow. Choreography: each service listens and acts [S8].

Timeouts + unknown outcome: request to network times out; you don't know if it was executed [S19].
Solution: use idempotency key on external call; retry with same key. Network re-checks its own idempotency keys.

ISO 8583 reversals: 0400 message code reverses prior transaction [S15].
Advice messages: point-to-point, informational, no response needed (vs requests which are end-to-end with timeout/retry) [S15].

---

## 7. Reconciliation

Three-way: internal ledger vs processor reports vs bank statement [S1].
Settlement files, T+1 / T+2 delays [S1].
Break detection and aging: track unmatched entries by age, investigate over time.
Tolerance: allow small rounding differences, currency conversion spreads.
Unrecognized transaction: in statement but not ledger; investigate source.

Reconciliation is last line of defense for duplicates; catches errors missed by idempotency / deduplication.

---

## 8. Storage & Durability Choices

Postgres (sharded by account via Vitess/Citus): strong consistency, ACID per shard; cross-shard queries weak consistency [unverified].
Spanner / CockroachDB: global SERIALIZABLE across regions, external consistency stronger than linearizability [S16][S18].
Event-sourced: Kafka + materialized balance view (eventual consistency for reads, strong for writes) [S6].
Write-ahead log / append-only ledger with hash chains: Uber LedgerStore, AWS QLDB (tamper-proof, cryptographic digests for verification) [S17].

fsync implications: each durable write = disk I/O (~1-10ms per fsync).
Postgres default `fsync=on`; commit latency ~5-10ms per transaction (batching helps).
QLDB stores blocks in S3, hashes cryptographically; can be verified against digest [S17].

---

## 9. Consistency & CAP Position for Money

Which parts must be linearizable:
- Balance check + entry append (atomic, no dirty reads).
- Idempotency key lookup + result storage (prevent duplicates).

Which can be eventual:
- Reporting, analytics (may lag).
- Notifications to client (ok to be async).

Read-your-writes for payer UI: after payment request, payer sees result immediately (may be tentative).
Settlement reports on processor: may take hours (eventual).

Spanner/CockroachDB choose strong C over A; Postgres+sharding trades off global consistency for availability.

---

## 10. Money Math

Always use integers in minor units (cents, smallest unit per currency); never floats [unverified in primary sources].
Currency exponent (ISO 4217): USD = 2 (cents), JPY = 0 (no fraction), BHD/KWD = 3 (millis) [S15 implies via currency codes].

Rounding rules: banker's rounding (round-to-even, default in IEEE 754, minimizes bias) vs half-up (always away from zero, traditional) [S14].
FX rounding: apply at conversion time per line; rounding line = row in journal entry where amount is recomputed [unverified].
Fees & commissions: specify rounding rule in journal entry metadata.

Example: 100 JPY (no decimals) + 50.125 USD at 1.05 rate = needs rounding rule in entry.

---

## Numbers the Solution Will Use

| Number | Value | Source ID | Confidence |
|--------|-------|-----------|-----------|
| Stripe idempotency key TTL | 24 hours | S1 | High |
| IETF idempotency header draft | v7 (expires 2026-04-18) | S2 | High |
| Kafka max.in.flight.per.connection | 5 | S4 | High |
| Kafka transaction.timeout.ms default | 60,000 ms (1 min) | S4 | High |
| TigerBeetle batch size | 8,190 transfers | S11 | High |
| Postgres deadlock_timeout default | 1 second | S13 | High |
| Postgres SSI failure error code | 40001 | S12 | High |
| JPY currency exponent | 0 (no decimals) | ISO 4217 | High |
| BHD/KWD currency exponent | 3 (3 decimals) | ISO 4217 | High |
| ISO 8583 reversal message code | 0400 | S15 | High |
| Single Postgres row update throughput | [unverified] | - | Low |
| TigerBeetle throughput (TPS) | [unverified - claim 1M TPS] | S11 | Low |

---

## Spot-check corrections (added after review, 2026-09-13)

| Claim above | Correction |
|---|---|
| §7 reconciliation cites [S1] (Stripe idempotency docs) | Wrong source. Three-way reconciliation and T+1 / T+2 come from the Stripe Ledger post (clearing, timeliness, completeness) and Modern Treasury's reconciliation posts. See the architectures survey spot-check table |
| "Same key + different body returns 409" | Stripe returns **400** with `idempotency_error` for a parameter mismatch and **409** `idempotency_key_in_use` when the first request is still in flight. https://docs.stripe.com/api/idempotent_requests |
| Section 4 "row lock limits updates to ~1000s per second" | Unverified, but the order of magnitude is right: a serialized read-modify-write on one row costs one round trip plus commit (roughly 1 to 5 ms with synchronous replication), so a hot row tops out at hundreds to low thousands of updates/s. The number in `solution.md` is derived from that latency, not from a benchmark |
| Section 10 "[S15 implies via currency codes]" | ISO 8583 does not define exponents. ISO 4217 does: USD 2, JPY 0, BHD and KWD 3. https://www.iso.org/iso-4217-currency-codes.html |
| Section 8 fsync "1 to 10 ms" | Fine for network SSD with synchronous replica. Local NVMe fsync is 20 to 100 us; the cost is the replica round trip, not the disk |
