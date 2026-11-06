# Payment and invoice reconciliation design

## Responsibilities and contract

`ReconciliationController` translates a JSON batch into a service call. `BatchParser` validates and parses every row before matching starts. `ReconciliationService` applies stage/rule priority and owns invocation-local indexes. `Payment`, `Invoice` and `MatchResult` are immutable snapshots. `Practice` demonstrates all stages without starting Spring.

No repository is needed: the exercise supplies the complete open-invoice list for each batch. No invoice is persisted or paid externally. The returned list is immutable, and caller-owned lists are not changed. Service state is local to each invocation, so concurrent batches cannot consume each other's input invoices.

Malformed rows reject the entire batch. Structured fields are trimmed, payment memos are preserved, and payment rows split only at their first two commas. Invoice rows must have exactly three fields. Null rows, missing lists, duplicate IDs, invalid dates and negative/out-of-range amounts are rejected. Empty lists and zero amounts are valid. Payment IDs are nonblank; invoice IDs use case-sensitive `INV-[0-9]+`, with leading zeros preserved. Dates use strict ISO parsing after checking the four-digit-year format. Amounts and tolerance use nonnegative `long` minor units; this batch assumes a common currency.

Whole memo IDs cannot touch Unicode letters/numbers, underscores or hyphens. Spaces and punctuation such as parentheses, colons, commas, periods and slashes delimit IDs. This deliberately treats `INV-1-extra` as one different identifier. The boundary policy is documented and tested because the prompt leaves it open. Quoted CSV escaping is outside this row format.

## Matching stages

For each payment in input order:

1. Scan whole ID occurrences left to right. Skip unknown and consumed invoices. The first open reference wins, even if its amount differs from the payment or another candidate is due earlier.
2. In stage two or three, if no memo match exists, find an open invoice with the same amount. Choose the earliest due date, then lexical ID (`INV-10` precedes `INV-2` on the same date).
3. In stage three, if exact matching fails, consider the inclusive amount range `[payment - tolerance, payment + tolerance]`. Choose by due date then lexical ID across that range; closeness of amount has no priority. Bounds saturate at zero and `Long.MAX_VALUE` to avoid overflow.
4. Remove the chosen invoice from every index. Emit the payment, invoice and rule; unmatched results contain `invoice=null` and `rule=NONE`.

The two-list Java method preserves stage one. An explicit stage enables stage two, and the tolerance overload enables all stages. HTTP defaults to all stages with zero tolerance, allowing exact fallback while requiring no tolerance field. Negative tolerance is invalid for every stage; earlier stages otherwise ignore it. Zero tolerance always produces an exact rule when an equal amount is available.

## Indexes and complexity

An ID hash map serves memo lookups. A `TreeMap<amount, TreeSet<Invoice>>` holds open invoices, each bucket sorted by due date then ID. All matches remove from both indexes, preventing reuse through a different rule.

Let `I` be invoice count, `P` payment count and `L` total input text length. Parsing costs `O(L)`; building indexes costs `O(I log I)`. Memo matching scans memo text with expected constant-time ID lookups. Exact fallback and match removal cost `O(log I)`. For tolerance, visit each distinct amount bucket in range and compare only its first (best) invoice. For `K` qualifying buckets with sizes `B1` through `BK`, this costs `O(log I + K + sum(log(Bj + 1)))`, including Java's tree-backed `first()` calls. Those bucket sizes sum to at most `I`, so a tolerance lookup is at worst `O(I)`. With broad tolerances, the batch worst case is `O(L + I log I + P I)`. Space is `O(I + P)` records/index entries, plus input text and the current memo match.

For larger batches, cache each bucket minimum to make range iteration `O(K)`, or use an augmented amount tree with subtree minima for range-minimum queries. Keep the simple implementation until measured batch size/tolerance distributions justify more machinery. Memo-only matching could omit the amount index entirely as another optimization.

## Retried batches and multiple workers

The function is deterministic for the same ordered inputs and options. Each invocation builds fresh indexes, so replay has no persistent effects. This deliberately does not enforce one match across batches: two workers supplied the same invoice can each propose it. Reversing payment order can change assignments because earlier payments consume candidates first.

If this becomes a settlement service, introduce durable batch IDs, immutable input/options fingerprints and stored results. A retry with the same ID and input should return the saved result; a conflicting payload should fail. Persist invoice claims and match records in a transaction using row locks or conditional version/state updates plus a uniqueness constraint on the consumed invoice ID. Candidate selection must retry if a competing worker claims the selected invoice. Define a global ordering policy if reproducibility across workers is required; locking alone prevents double consumption but does not make scheduling deterministic. Send downstream settlement through an outbox and an idempotent worker after committing the match.

## Disputed matches

The result already contains payment and invoice IDs, both amounts, the invoice due date and the winning rule. A production audit record should also retain batch ID, input position, matching algorithm version, stage/tolerance options, invoice version, relevant memo reference offsets and the fallback ordering keys. These explain why a mismatched memo amount was accepted or why an earlier-due tolerance invoice won. Store sensitive source memos under an appropriate access/retention policy rather than putting their full contents into ordinary logs. Track unmatched counts, fallback-rule counts and claim conflicts. No production logging or settlement side effects are added to this local exercise.
