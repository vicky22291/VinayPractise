# Webhook delivery design

## Stage 1: routing and attempts

`DeliveryController` is the HTTP adapter. `DeliveryService` owns endpoint registration, event fanout, claims and completion. `DeliveryRepository` serializes local state changes. `DeliveryWorker` coordinates service and `WebhookSender`; `HttpWebhookSender` does real HTTP with Java's `HttpClient`. The CLI demo and service tests inject a fake sender.

An endpoint has a UUID, an absolute HTTP(S) destination and a set of exact, case-sensitive event types. Publishing creates one delivery for every currently subscribed endpoint. Event IDs are unique: republishing the same ID and payload does not fan out twice, even with a fresh service key. Different data for an existing event ID is rejected. Endpoints added later do not receive historical events automatically. Endpoints and event payloads are snapshotted into deliveries.

| From | Trigger | To |
|---|---|---|
| PENDING or due RETRY_SCHEDULED | Atomic claim | IN_FLIGHT; attempt count increments; lease/token assigned |
| IN_FLIGHT with a current, unexpired token | 2xx / SUCCEEDED | DELIVERED |
| IN_FLIGHT with a current token | FAILED or UNKNOWN below attempt limit | RETRY_SCHEDULED |
| IN_FLIGHT with a current token | FAILED or UNKNOWN at attempt limit | DEAD |
| IN_FLIGHT with expired lease | Polling worker recovery | UNKNOWN attempt; RETRY_SCHEDULED or DEAD |
| Terminal delivery or stale/expired claim | Completion | 409, unchanged |

A claimed attempt initially has UNKNOWN outcome and no finish time. Completion or lease recovery closes that attempt in immutable history. A timeout does not imply that a receiver did nothing: it may have committed a side effect before the sender lost the response. Non-2xx responses are retryable failures in this simplified policy, including 4xx. Redirects are not automatically followed.

## Stage 2: retries and delivery guarantee

`RetryPolicy` configures total maximum attempts (including the first), initial/capped exponential backoff and lease duration. The default gives three attempts with 1 and 2 seconds between them. A normal retry is due at completion time plus backoff. Lease recovery schedules from the expired lease's end plus backoff; if polling happens later than that, recovery can immediately claim again. All timing uses injected `Clock`; tests advance it without sleeping. Exhaustion produces DEAD even for repeated unknown outcomes.

The sender permits duplicate deliveries and offers bounded retry attempts, not an exactly-once or guaranteed-eventual-success contract. A receiver may already have processed a DEAD delivery whose replies were repeatedly lost. Deduplicate by the stable event ID in the receiver's consumer/endpoint scope (or stable delivery ID for this particular subscription). Commit the deduplication marker in the same transaction as the receiver's business side effect, then acknowledge. Both IDs remain unchanged across retries and lease recovery; claim tokens change per attempt.

`Idempotency-Key` applies to registration and publishing, with payload conflict checks and immutable original results. Worker commands use lease tokens instead: a repeated completion is rejected and workers can GET current state. Losing a claim response can leave a delivery leased until expiry, but cannot lose it forever.

## Stage 3: worker recovery, fencing and ordering

Claim selection and lease installation share a repository lock. Concurrent workers cannot obtain two live claims for the same delivery. The worker releases this lock before HTTP I/O, allowing other workers to process unrelated deliveries while one endpoint is slow. Before completing, check status, token and current time against lease expiry; an old worker cannot overwrite a newer attempt's result. Fencing protects local state, but cannot undo a request the receiver already accepted. Receiver deduplication remains necessary.

Leases and attempt history are stored in the repository. A new polling worker recovers expired claims if the first worker dies. With this in-memory repository, recovery models a **worker** crash while the service/store survives. A process restart loses the queue; a durable database claim (`lease_until`, unique attempt token, conditional updates) is needed for restart recovery. Lease renewal can support longer sends; here the HTTP request timeout is 10 seconds and default lease is 30 seconds.

Per-endpoint strict ordering is **not required** in this implementation. Due work is selected in insertion order, but events can be in flight concurrently and retries can be overtaken. This avoids head-of-line blocking and improves throughput. Strict ordering would require per-endpoint sequence numbers plus a single eligible head delivery per endpoint, with a deliberate policy for DEAD items; one slow/failed event would delay that endpoint's later events.

## Operations and release discussion

A caller drives one send with `/workers/run-once`; there is no background thread in this exercise. A worker can instead use claim/complete to integrate another transport. Multiple workers prevent one slow customer from holding the entire queue lock. A production queue would add per-endpoint concurrency limits, fair scheduling and isolated retry budgets to prevent a failing customer monopolizing worker capacity.

Operators can inspect status, attempt count, next retry, lease owner/expiry and per-attempt outcomes through GET. Useful metrics include oldest pending age, due queue depth, expired leases, unknown outcomes, retries, DEAD count and endpoint success/latency. A manual replay feature should preserve the original event identity and append new attempt history under an audited operator command, so the receiver can still deduplicate; this API does not reset DEAD deliveries.

For a first release, keep bounded retries, stable IDs, clear support visibility and receiver deduplication guidance. Add durable queue storage and authentication/signing plus controlled endpoint access before deployment. Canary the sender, limit concurrency and monitor unknown/DEAD rates. These are design follow-ups rather than infrastructure needed for the local exercise.

`DeliveryServiceTest` covers routing, immutable attempt history, unknown outcomes, backoff timing, exhaustion, worker crashes, stale tokens, claim races and I/O outside the lock. `ExerciseApiTest` exercises the manual worker HTTP journey without contacting external destinations.
