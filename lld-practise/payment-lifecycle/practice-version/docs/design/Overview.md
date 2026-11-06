# Payment lifecycle design

## Stage 1: responsibilities and transitions

`PaymentController` translates HTTP DTOs into service calls. `PaymentService` owns orchestration, retry results and processor interaction. `Payment` is an immutable snapshot with transition methods; `PaymentRepository` owns stored snapshots and the transaction lock. `CaptureProcessor` is the external-system boundary. `SimulatedProcessor` models accepted charges and lost responses without network traffic.

Amounts are positive `long` minor units. Currency accepts exactly three ASCII letters and is normalized to uppercase; this is syntax validation, not an ISO currency catalog. IDs are UUIDs. Authorization is local in this exercise; the external interface models capture uncertainty.

| Current state | Operation | Result |
|---|---|---|
| CREATED | Authorize | AUTHORIZED |
| CREATED or AUTHORIZED with no reservations | Cancel | CANCELED |
| AUTHORIZED or PARTIALLY_CAPTURED | Reserve capture within remaining amount | State stays; reserved amount increases |
| Capture UNKNOWN | Processor confirms success | Reservation becomes captured money; PARTIALLY_CAPTURED or CAPTURED |
| Capture UNKNOWN | Processor declines | Reservation released; AUTHORIZED or PARTIALLY_CAPTURED |
| Capture UNKNOWN | Timeout / unknown | Reservation retained; caller sees UNKNOWN |
| CANCELED or CAPTURED | New authorize/capture/cancel | Reject without change |

Cancellation is rejected after any successful partial capture, even if some authorization remains. Releasing the unused portion after a partial capture would be a separate operation. A capture body `{}` requests all remaining unreserved funds, preserving the stage-one full-capture path.

## Stage 2: retries and concurrency

A key records the operation, target ID and immutable request payload plus the original response. Currency normalization happens before comparison; an omitted capture amount is a distinct request from an explicit amount. Keys are global in this local single-tenant service. In a multitenant API, scope them by account. Invalid requests do not consume keys. A replay returns its original response snapshot; a GET returns current state.

The repository lock serializes the remaining-authorization check, reservation, capture record and idempotency result. Two racing captures cannot both reserve the last funds. The invariant is `0 <= captured + reserved <= authorized amount`. All returned records are immutable. The concurrency tests check both different-key races and same-key retries.

## Stage 3: processor uncertainty

1. Allocate a capture UUID and store an UNKNOWN capture plus its reservation before calling the processor.
2. Send that UUID as the processor idempotency identifier. Never generate a new processor identifier when retrying this capture.
3. A definitive success moves reserved money to captured money. A definitive decline releases the reservation. A timeout or exception keeps the reservation.
4. Reconciliation calls the processor with the same command and identifier. A processor with idempotency support returns the already accepted outcome instead of charging again.
5. Reconcile with a new service request key to observe progress. Replaying the old capture/reconciliation key preserves its original result. GET exposes current records.

An UNKNOWN capture is not available for another charge or cancellation. The simulator deliberately accepts the first request and hides its success when `processor.timeout-after-accept=true`. Reconciliation returns that same charge; tests assert one processor charge and no duplicated local settlement. A DECLINED capture is terminal and releases its reserved amount.

The local payment/operation records track intent and the processor tracks actual external charges; reconcile the two. A real processor may offer an explicit status lookup instead of replaying its capture command. Keep that detail behind `CaptureProcessor`.

## Persistence boundary and follow-ups

The repository callback is an in-process critical section, not a database transaction with automatic rollback. Validate before writing; the only expected uncertainty after the reservation is stored becomes UNKNOWN. This implementation holds the lock during the simulated processor call to make one process easy to reason about. It therefore serializes captures across payments.

For a real service, commit the reservation, capture intent and retry identity durably before I/O, release the database lock, then settle the outcome in another transaction. Use an outbox/worker plus reconciliation so a restart between commit and send is recoverable. Persist processor idempotency mappings for at least the supported retry window; a provider key that expires cannot safely be replaced without checking the charge. This in-memory example handles lost responses while the JVM lives; it does not survive process restart.

Watch unknown-capture age and reserved totals. Reconcile processor IDs, amounts and currency; never infer a failure solely from a timeout. `PaymentServiceTest` covers transitions, overcapture, retry conflicts, processor declines, exceptions, accepted timeouts and races. `UncertainCaptureApiTest` exercises reconciliation through HTTP.
