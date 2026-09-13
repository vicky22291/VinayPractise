# Edge cases: Visa-scale payments + ledger + duplicate payment prevention

Every entry must be answerable out loud in under 60 seconds. Mark confidence after each study pass. Categories per `hld/CLAUDE.md` §5: failure, consistency, scale, data, operations, security.

Design recap for context: `POST /payments` inserts an idempotency row (key, fingerprint, `locked_at`, `recovery_point`) in the same transaction as the payment; every rail call has an `attempt_id` that is the rail's idempotency key and returns `APPROVED / DECLINED / UNKNOWN`; every money movement is a journal entry with `entry_id = uuid5(payment_id, kind, attempt_id)` and balanced lines, inside one ledger shard; constrained accounts have a synchronously updated balance with two-phase holds, everything else is append-only with snapshots; hot constrained ledgers get a single-writer batch; cross-ledger money goes through clearing accounts; a sweeper drives stuck payments; reconciliation matches the rail's files by `rail_ref` at T+1. Details in [`solution.md`](solution.md).

---

## 1. Failure

## Edge case: client times out and retries the POST
- **Trigger:** mobile network drop after the request was sent; the LB or SDK retries.
- **Symptom:** two identical POSTs seconds apart, same `Idempotency-Key`.
- **Answer:**
  - Second POST hits the unique index on `(tenant_id, key)`. Fingerprint matches. If the first is still `in_progress` with a fresh lock: 409 with `Retry-After: 1`. If `done`: 200 with the stored response. Never a second payment.
  - If the client did not send a key, we generate none for it; the docs say a missing key means no dedup. Stripe and the IETF draft take the same position. In practice the SDKs always send one.
  - If the retry arrives after 24 h: the key is gone and this is a new payment. Say it: the TTL is the trade, and 24 h covers every realistic retry.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: rail call times out, outcome unknown
- **Trigger:** the issuer or PSP does not answer within 5 s; socket reset mid-response.
- **Symptom:** the adapter returns `UNKNOWN`; the payment sits in `authorizing_unknown`; the client got `202 pending`.
- **Answer:**
  - We never map timeout to failure. The card may have been charged.
  - Resolver after 10 s: if the rail has a status query (PSP), query by `attempt_id` and advance accordingly. If not (ISO 8583), send a `0400` reversal carrying the original STAN, repeat every 2 s until `0410`. Reversing a charge that never happened is a no-op on the network.
  - ACH has neither: stays `pending` until settlement or a return code, days.
  - T+1 recon checks the rail's file for the attempt. If the rail captured it anyway (reversal lost), that is a rail-only row against a `reversed` attempt: auto-refund with `uuid5(attempt_id, dup_refund)` and page.
- **Diagram:** [`solution.md` §4.2 D5a](solution.md#42-drive-the-payment-through-the-rail-with-a-retry-safe-state-machine), [`diagrams.md` D6b](diagrams.md#d6-activity--decision-flow).
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: API pod dies after the rail approved, before the ledger posted
- **Trigger:** OOM kill, deploy, node loss between phases.
- **Symptom:** payment `authorized` in the DB, `recovery_point = authorized`, idempotency row `in_progress` with an aging lock, client got no response.
- **Answer:**
  - The client retries. Within 30 s: 409. After 30 s: the new pod sees a stale lock, takes it over with a conditional update on `locked_at`, reads `recovery_point`, and resumes at the ledger post. It does not call the rail again because the phase after the rail call already committed.
  - If no client ever retries, the sweeper finds `authorized` payments older than their deadline and runs the same resumption. Nothing depends on the client.
  - If the crash was after the rail call but before `recovery_point = authorized` committed: the attempt row exists with `sent_at` and no outcome. Resumption treats it as unknown and goes through the resolver (query or reverse). The attempt id is stable so a re-send is not a new charge.
- **Diagram:** [`diagrams.md` D5b](diagrams.md#d5-sequence-failure-path).
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: ledger primary dies after commit, before ack
- **Trigger:** primary crash with the WAL record already on a synchronous standby.
- **Symptom:** the ledger writer's `Post` times out. Was the entry committed?
- **Answer:**
  - Do not care. After failover (5 to 30 s) retry `Post` with the same `entry_id`. `INSERT ... ON CONFLICT DO NOTHING RETURNING` either inserts or returns the existing entry.
  - Un-acked commits that had not reached a standby are gone with the primary. Those were never acked, so the writer retries and applies them fresh. RPO 0 for acked, by definition.
  - The old primary is fenced by epoch so it cannot come back and accept a conflicting sequence.
- **Diagram:** [`solution.md` §10.4](solution.md#104-failure-timeline).
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: the rail is down for 20 minutes
- **Trigger:** PSP outage, network scheme incident, issuer host down.
- **Symptom:** `UNKNOWN` and connection errors on every auth for that rail.
- **Answer:**
  - Card auth cannot be queued; the cardholder is at the checkout. Fail closed fast: 503 with `Retry-After`, circuit breaker per rail open after 50% errors in 10 s, half-open probes every 5 s. Say why: retrying into a dead rail creates unknowns, and every unknown is a reversal and a recon row.
  - Payouts and ACH are queued by nature; they wait for the next window.
  - If we have a second acquirer or PSP for the same card brand, route new auths there (an `attempt` on a different rail, never the same attempt re-sent elsewhere; in-flight unknowns on the dead rail are still resolved on the dead rail when it returns).
  - The issuer-down case on the card network is handled by STIP: the network answers within issuer-set limits and forwards the advice later. That is the network's problem, not ours.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: Kafka is down
- **Trigger:** broker quorum loss, misconfigured ACL.
- **Symptom:** outbox rows accumulate, webhooks stop, sweeper events stop.
- **Answer:**
  - No money impact. State changes commit with their outbox row; the relay just cannot publish. Backlog is bounded by disk on the payments shards (rows are 1 KB, an hour at peak is 720 GB across 20 shards, fine).
  - The sweeper also runs from a table scan on a timer, not only from events, so stuck payments still resolve.
  - Page at `outbox_oldest_unpublished_age > 60 s`. On recovery the relay drains in id order; the idempotent producer prevents duplicates within its session; consumers dedup on `event_id`.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: region loss
- **Trigger:** cloud region outage.
- **Symptom:** all shards with that home region unreachable; async standbys in region 2 are up to 1 s behind.
- **Answer:**
  - Promote standbys with an epoch bump; fail the API over; RTO about 2 min.
  - RPO about 1 s: acked writes in that window may be missing. Three recoveries: orchestrator retries re-post entries by deterministic id; the sweeper reverses payments it cannot confirm; recon at T+1 compares against the rail, which is the source of truth for what was actually charged.
  - When the old region returns, it does not resume as primary (fenced). It re-syncs as a standby. Any write it accepted after the partition and before fencing (the ~1 s) is compared by a divergence job and, if it was an entry, re-applied under a new sequence in the new primary or refunded, both through recon.
  - State the trade: synchronous cross-region commit would make this RPO 0 at 60 to 100 ms per entry. We chose 1 s of exposure that recon covers.
- **Diagram:** [`diagrams.md` D9](diagrams.md#d9-deployment--topology).
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: two ledger writers both think they own a shard
- **Trigger:** GC pause or partition on writer 1; lease expires; writer 2 takes over; writer 1 wakes up.
- **Symptom:** two processes with in-memory balances for the same ledger.
- **Answer:**
  - Every batch commit carries the writer's epoch; the shard's current epoch is in a row the commit checks (`UPDATE shard_epoch SET epoch = 9 WHERE epoch = 9` as the first statement). Writer 1's batch with epoch 8 fails the check and aborts. It then re-reads ownership and steps down.
  - Nothing was applied out of order because the check is inside the transaction. Same pattern as chunk-server leases in the file system.
  - Writer 2 rebuilds in-memory balances from the materialized rows plus the tail on startup, which is why constrained balances are materialized.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

---

## 2. Consistency

## Edge case: two requests with the same key arrive at the same millisecond on two pods
- **Trigger:** double click, two SDK threads, a retry racing the original.
- **Symptom:** two `INSERT idempotency_record` on one shard.
- **Answer:**
  - The unique index picks one. The loser reads the row, compares fingerprints, returns 409 (in progress) or 200 (done). No distributed lock, no Redis `SETNX`, no leader.
  - Both pods must route the key to the same shard, which they do because the shard key is `tenant_id` and the key is scoped per tenant.
  - Concurrency on different keys for the same payer is not deduped; that is two payments. Velocity limits in risk cover "same card, same amount, 3 times in 2 s" as a fraud signal, not as idempotency.
- **Diagram:** [`diagrams.md` D5c](diagrams.md#d5-sequence-failure-path).
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: same key, different body
- **Trigger:** client bug reuses a key with a different amount; or a legitimate retry after the client mutated the request.
- **Symptom:** fingerprint mismatch on the existing row.
- **Answer:**
  - 422 `idempotency_mismatch`, the record is untouched, the original payment stands. Stripe returns 400 for this. Never silently process the new body, never return the old response as if it matched.
  - Fingerprint is a hash of the canonical body (sorted keys, no whitespace) plus the path. Headers are excluded except the key itself.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: two concurrent debits from a constrained account with just enough for one
- **Trigger:** a wallet with 100 and two 60 payments at once.
- **Symptom:** both read 100 before either writes.
- **Answer:**
  - Not with our write: the hold is `UPDATE balance SET available = available - 60 WHERE account_id = w AND available >= 60`. Row lock serializes the two; the second sees 40 and updates 0 rows; the writer returns `insufficient_funds` and the payment is declined before any rail call.
  - In the single-writer batch model the same check is in memory in batch order, one thread, so there is no race at all.
  - Capture never fails for funds because the hold reserved them; that is the point of two-phase.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: capture arrives before the authorization's ledger hold is visible
- **Trigger:** manual capture from a merchant system that got the auth webhook faster than our replica caught up; or the orchestrator's own retry ordering.
- **Symptom:** `PostHold(entry_id)` for an entry that the replica does not show.
- **Answer:**
  - Ledger writes go to the shard primary, never a replica, so the hold is visible to the capture. The interviewer's real question is about ordering across two writers; the answer is that the payment's `version` conditional update serializes transitions: capture requires `status = authorized AND version = n`, and only one transition wins.
  - Webhooks are eventual and out of order by design; the merchant's capture call is validated against the primary.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: cross-ledger transfer with the second half missing
- **Trigger:** orchestrator posted the debit + clearing credit in ledger A, then died before ledger B.
- **Symptom:** clearing accounts across ledgers do not net to zero; the receiver does not see the money.
- **Answer:**
  - The orchestrator's retry (or the sweeper) re-runs the transfer by `transfer_id`: ledger A's entry exists (idempotent), ledger B's is posted now. Bounded by the retry deadline, 60 s.
  - The 5 min invariant job flags a non-zero clearing sum older than 60 s as a break, which pages. Under 60 s it is "in flight".
  - We refused cross-shard atomicity for this; the trade is a bounded window of eventual consistency and one more invariant to monitor. Banks call this a suspense account.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: refund larger than what is left
- **Trigger:** two partial refunds racing, sum exceeds captured amount.
- **Symptom:** two refund POSTs with different keys, both read `captured - refunded = 50`, both want 40.
- **Answer:**
  - The refund create transaction does `UPDATE payment SET refunded = refunded + 40 WHERE id = p AND captured - refunded >= 40` on the payment row. Second one updates 0 rows and gets 422. Same conditional-update pattern as balances, on the payment row, which is not hot (one row per payment).
  - The rail also refuses over-refund, but we do not rely on it.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: clock skew between pods and the rail
- **Trigger:** a pod's clock is 5 minutes off.
- **Symptom:** `locked_at` staleness checks and hold expiries misjudge time; `effective_at` on entries looks wrong.
- **Answer:**
  - `locked_at`, `posted_at`, `expires_at` are set by the database (`now()` on the primary), not by the pod. One clock per shard.
  - Ordering in the ledger is by `seq`, never by timestamp. As-of queries resolve a timestamp to a `seq` once, then use `seq`.
  - The rail's timestamps in clearing files are the rail's; matching is by `rail_ref`, not time.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

---

## 3. Scale

## Edge case: one merchant is 5% of all volume
- **Trigger:** a marketplace or a large retailer on the platform.
- **Symptom:** thousands of entries/s into one ledger; if its payable account had a synchronous balance row, lock wait and `deadlock_timeout` firing.
- **Answer:**
  - Its payable is not constrained, so it has no synchronous balance row. Entries are inserts. Balance is snapshot + tail.
  - Its ledger is still one shard; at 10 k entries/s peak it exceeds the 5 k txn/s of a direct-write primary. Promote it to a single-writer batch: one commit per 4 k entries, 100 k/s ceiling.
  - Its fee lines go to a per-ledger fee sub-account (the platform revenue account is the sum across ledgers), so no platform-wide hot row either.
- **Diagram:** [`solution.md` §5.1](solution.md#51-one-merchant-is-5-of-volume-its-account-gets-thousands-of-updates-a-second-what-breaks).
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: a constrained account that is also hot
- **Trigger:** a prefunded platform float that every payout draws from; a payroll funding account paying 50 k employees in one run.
- **Symptom:** thousands of `available >= x` checks per second on one row.
- **Answer:**
  - Single-writer batch for that ledger: the check runs in memory in order; one commit per batch. 100 k checks/s on one core.
  - If it must be spread across writers (rare), sub-accounts with a rebalancer; say the cost (readers must sum, debits can fail on one sub-account while the total suffices).
  - For payroll specifically: reserve the run's total with one hold up front (one check), then post 50 k lines against the hold. One contended operation per run, not per employee.
- **Diagram:** [`deep-dives/hot-accounts-and-contention.md`](deep-dives/hot-accounts-and-contention.md).
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: Black Friday, 10x for 6 hours
- **Trigger:** 650 k payments/s.
- **Symptom:** every tier at 10x.
- **Answer:**
  - API and payments DB: horizontal, pre-scaled shards (vshards make a split a metadata move). Rail adapter: in-flight count is `p99 x qps`, so 1.3 M connections; pre-warm.
  - Ledger DB: the first thing to hit its limit. Batch every ledger, not only the top 5%, for the event; batching is a per-ledger flag.
  - The rail is the real cap: our acquirer and the network have their own throughput commitments; a Staff answer says we agreed on a peak with them beforehand.
  - Recon lag grows; that is fine, it is T+1 by contract.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: idempotency store growth
- **Trigger:** 864 M keys/day at 10 k/s.
- **Symptom:** 430 GB live in the payments shards.
- **Answer:**
  - Rows expire at 24 h; a partition-per-hour table makes expiry a `DROP PARTITION`, not a delete.
  - Replays are 1 to 5% of traffic, point lookups on the primary key; no separate cache needed.
  - Do not move keys to a cheaper store; the whole point is that they are in the payment's transaction.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: thundering herd of retries after an outage
- **Trigger:** the rail returns; 10 minutes of clients retrying at once.
- **Symptom:** a burst of replays and new payments.
- **Answer:**
  - Replays are cheap (one read). New payments are rate limited per tenant at the gateway with `Retry-After` jitter.
  - The resolver's reversal queue drains at a controlled rate so we do not flood the returning rail with `0400`s.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

---

## 4. Data

## Edge case: partial capture, then partial refund, then chargeback
- **Trigger:** auth 100, capture 80, refund 30, then the cardholder disputes and loses 50.
- **Symptom:** the interviewer wants the entries and the states.
- **Answer:**
  - Hold 100 (pending). Capture: post 80 of the hold, void 20 (available restored). Refund 30: new entries, debit merchant payable, credit card receivable; the original capture entry is untouched. Chargeback 50: entries debit merchant payable 50 + chargeback fee, credit card receivable 50; state `charged_back`; if the merchant wins the dispute, a further entry reverses it.
  - Payment shows `captured 80, refunded 30, disputed 50`. Nothing was edited; everything is a new entry with a deterministic id.
- **Diagram:** [`diagrams.md` D4b](diagrams.md#d4-sequence-happy-path-one-per-fr).
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: rounding and currencies
- **Trigger:** 2.9% of 999 = 28.971; JPY has no minor unit; a BHD amount has 3.
- **Symptom:** an entry that does not balance by 1 minor unit after FX.
- **Answer:**
  - Amounts are integers in minor units with the ISO 4217 exponent (USD 2, JPY 0, BHD 3). No floats anywhere.
  - Fees round half-up per fee line, and the rounding rule is stored on the entry. An FX entry balances per currency, with a rounding line to an `fx_rounding` account for the residual. The FX rate is on the entry.
  - The invariant is "sum per currency per entry = 0", never "sum across currencies".
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: balance as of last Tuesday 14:00
- **Trigger:** auditor or dispute.
- **Symptom:** need a point-in-time balance for one account.
- **Answer:**
  - Resolve the timestamp to the last `seq` in that ledger with `posted_at <= T` (one index lookup). Read the snapshot at or before that `seq`, sum lines between. Deterministic because entries are immutable and `seq` is total within a ledger.
  - `effective_at` (business date) can differ from `posted_at`; finance asks by effective date, disputes ask by posted date. Both are on the entry.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: schema change on the ledger
- **Trigger:** new field on lines (say, `settlement_batch_id`).
- **Symptom:** 400 TB/yr of immutable rows.
- **Answer:**
  - Additive only, nullable, default null. Never rewrite an existing line. New meaning for old rows is derived, not stored.
  - Kinds are an enum in code with a versioned mapping; an unknown kind in an old row is a reader problem, not a writer one.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: GDPR delete request
- **Trigger:** a cardholder asks to be forgotten.
- **Symptom:** the ledger must keep entries for 7 years.
- **Answer:**
  - Entries contain account ids and tokens, never names, emails, or PANs. Delete the person-to-account mapping and the vault token; the ledger becomes pseudonymous for that account. Regulators accept this; say "legal basis: financial record keeping".
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: replaying the ledger to rebuild balances
- **Trigger:** a snapshot job bug corrupted materialized balances.
- **Symptom:** balance reads wrong; invariant job flags `materialized != snapshot + tail`.
- **Answer:**
  - Balances are derived. Rebuild from lines in `seq` order per account; a single pass over the ledger shard. For a hot ledger this is minutes; do it on a replica and swap.
  - The invariant job runs every 5 min so the blast radius is 5 min of wrong reads, and constrained writes during that window are protected because the writer re-derives on startup from lines when the invariant fails.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

---

## 5. Operations

## Edge case: what pages at 3am
- **Trigger:** any of: unbalanced entry rejected, constrained balance negative, `rail_unknown_rate > 1%` for 5 min, sweeper backlog age > 60 s, ledger replica lag > 5 s, shard without owner > 10 s, hot-row lock wait p99 > 100 ms.
- **Symptom:** the first two mean a bug is live; the rest mean money is delayed, not lost.
- **Answer:**
  - Unbalanced or negative: halt deploys, roll back the writer, run the invariant job on the affected ledger, open an incident. Nothing was posted wrong because the check rejected it; the alert exists to find the bug.
  - Unknown rate: check the rail's status page, watch the reversal queue, consider failing closed for that rail.
  - Everything else follows the runbook in [`solution.md` §10.9](solution.md#109-operational-runbook).
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: recon finds a duplicate charge at T+1
- **Trigger:** a reversal was lost; the rail captured a charge we marked `reversed`.
- **Symptom:** a rail-only row whose `attempt_id` matches a reversed attempt.
- **Answer:**
  - Auto-refund with a deterministic id, post the refund entries, notify the merchant and cardholder, and page in the morning with an incident. The customer was charged twice for up to a day; that is the failure this whole design minimizes, and recon is why it is a day and not forever.
  - Metric: `duplicates_found_by_recon` should be zero. Any non-zero value gets a postmortem.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: migrating from a balance column with no idempotency
- **Trigger:** the existing system.
- **Symptom:** duplicates today are found by customer complaints.
- **Answer:**
  - Five phases, flag per tenant, rollback at each: idempotency layer in shadow then enforced; dual-write journal entries and backfill, compare balances daily; reads from ledger; writes through the new orchestrator; drop the old table after a signed quarter close. Stripe's migration pattern.
- **Diagram:** [`diagrams.md` D12](diagrams.md#d12-rollout--migration).
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: payroll run of 50 k ACH entries crashes at employee 31,204
- **Trigger:** worker node loss mid-run.
- **Symptom:** a half-built NACHA file and 31,204 `attempt` rows.
- **Answer:**
  - The run is a payment batch with one hold for the total. Each employee payment has `attempt_id = uuid5(run_id, employee_id, pay_period)`, so a restart regenerates the same ids and skips the ones with `sent_at` set.
  - The file is built and submitted as one unit per window; a half-built file is never submitted (write to temp, rename). If the crash was after submission, the trace numbers in the file are our attempt ids and the restart sees them as sent.
  - Rippling's "what if this runs twice" question is answered by the deterministic ids at every level: run, employee, file.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: a bad deploy of the ledger writer
- **Trigger:** a code change computes fee lines wrong; entries still balance.
- **Symptom:** balanced but wrong entries for one canary shard group for an hour.
- **Answer:**
  - The sum-zero invariant does not catch semantically wrong entries; the canary plus recon does: the clearing file amounts will not match our fee split, showing as amount-mismatch breaks in the 1% canary within the day.
  - Fix forward with correcting entries (never edit), generated from the diff, with a `kind = correction` and a ticket id.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

---

## 6. Security and abuse

## Edge case: a merchant's API key leaks
- **Trigger:** key in a public repo.
- **Symptom:** attacker can create payments and refunds as that merchant.
- **Answer:**
  - Charges go to the merchant's own payable, so the attacker gains nothing by charging. Refunds and payouts are the attack: they move money out. Velocity limits and daily caps on refund and payout endpoints, a page on breach, and key rotation with immediate revocation.
  - Tenant isolation means the blast radius is one merchant.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: malformed or adversarial idempotency keys
- **Trigger:** 10 MB keys, keys with PII, key collisions across tenants.
- **Symptom:** storage abuse or cross-tenant replay attempts.
- **Answer:**
  - Keys are max 255 characters, opaque, scoped per tenant in the unique index; a tenant can never hit another tenant's row. PII in a key is the client's choice and the docs warn against it, as Stripe's do.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: forged webhook
- **Trigger:** attacker posts `payment.succeeded` to a merchant's endpoint.
- **Symptom:** merchant ships goods.
- **Answer:**
  - Webhooks carry an HMAC over the body with a timestamp, 5 min tolerance; merchants verify or, better, treat the webhook as a hint and `GET /payments/{id}` before acting. The docs say so.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: insider edits the ledger
- **Trigger:** an engineer with DB access.
- **Symptom:** an entry changed or deleted.
- **Answer:**
  - The writer role has INSERT on entries and lines, UPDATE on balances and holds only; no DELETE anywhere; humans have read-only. The per-ledger hash chain is verified by a job with separate credentials; a break pages security, not on-call. Manual adjustments are entries with a ticket id and a second approver.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident
