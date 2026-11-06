# Webhook delivery service: implemented Java practice

This standalone project implements **all three stages** of the question in `stripe-staff-coding/questions/`. It follows the QA Bank approach: a thin HTTP layer, domain records, services, in-memory storage where needed, and tests. Read [TASK.md](TASK.md) for stage one and [interviewer/FOLLOWUPS.md](interviewer/FOLLOWUPS.md) for later requirements.

## Run

With Maven and JDK 21 or newer installed, use the scripts to build and test:

```bash
./scripts/build.sh             # clean and package the executable JAR; skips test execution
./scripts/test.sh              # run all tests
./scripts/test.sh -Dtest=StarterControllerTest  # run one test class
```

The scripts work from any directory when invoked by path and forward additional arguments to Maven. Build output and test reports are under `target/`.

```bash
cd lld-practise/webhook-delivery/practice-version
mvn test                    # business, concurrency (where relevant), and MockMvc API tests
mvn compile exec:java       # runnable three-stage example; no server required
mvn spring-boot:run          # API on :8096
mvn package                 # executable Spring Boot JAR
```

Use `PORT=9000 mvn spring-boot:run` for another port. Open [requests.http](requests.http) in IntelliJ and run requests sequentially; response handlers save generated IDs for later requests. Java 21 target, Spring Boot 3.5.16, Jackson, validation, MapStruct and JUnit 5 remain configured. The test-only subclass mock maker avoids agent self-attachment on restricted JDKs. `/health` and `/echo` remain available.

## Implemented stages and APIs

| Stage | Implementation | Main checks |
|---|---|---|
| 1 | Endpoint subscriptions, routing, HTTP sender, attempt outcomes | Explicit state machine and unknown timeout outcome |
| 2 | Exponential backoff and bounded attempts | Injected clock, no sleeps in tests, stable delivery identity |
| 3 | Expiring worker leases and claim tokens | Crash recovery, stale-worker rejection, concurrent claims |

| Method | Path | Result |
|---|---|---|
| POST | `/endpoints` | Register `destination`, `eventTypes`: 201; idempotency key required |
| POST | `/events` | Publish `id`, `type`, optional string `payload`: 201; idempotency key required |
| GET | `/deliveries` | Delivery snapshots: 200 |
| GET | `/deliveries/{id}` | One delivery and its attempt history: 200 |
| POST | `/deliveries/claim` | Claim next due delivery with `workerId`: 200, or 204 if none |
| POST | `/deliveries/{id}/attempts` | Record `leaseToken` and `outcome`: 200 |
| POST | `/workers/run-once` | Claim, send a real HTTP POST, record response; body `workerId`: 200/204 |

For a manual worker, claim then complete with `SUCCEEDED`, `FAILED`, or `UNKNOWN`. Completion is fenced by its lease token, rather than a client idempotency key; repeated or expired completions return 409. The real sender treats HTTP 2xx as success, other status codes as failure, and I/O timeouts/errors as unknown. It includes stable `Webhook-Event-Id` and `Webhook-Delivery-Id` headers and serializes the event as JSON.

Default policy: 3 total attempts, backoff of 1 then 2 seconds, 30-second leases, backoff capped at 60 seconds. Retry/recovery runs when a worker polls; no background scheduler is started. The Java demo uses an advancing clock and fake sender to demonstrate failure, worker crash and successful recovery without network calls or waiting.

## Integration tests

`FullStackApiTest` and `ExerciseApiTest` send JSON through MockMvc using the complete Spring Boot application context. Controllers, services and repositories are real beans. No internal application beans are mocked; writes are followed by GET requests and assertions on stored data. Run `mvn test '-Dtest=FullStackApiTest,ExerciseApiTest'` for these integration tests, or `mvn test` for all tests.

The full-stack suite invokes `/workers/run-once` through MockMvc and sends real HTTP requests to a local receiver. It checks received JSON/headers, 503 retries, an actual sender timeout, attempt history, concurrent claims and actual lease expiry. No sender or clock is mocked. Allow roughly a minute and enable loopback socket access for these tests.

## Contract and design

Client writes require a nonblank `Idempotency-Key` (except webhook worker commands, which use claim tokens). Keys are global within this single-tenant service, across operations and targets. Reusing a key with the same normalized request returns the original immutable result, even after later changes; a different request returns 409. Rejected operations do not consume keys. Reads always return current snapshots.

Bad input returns 400, missing resources return 404, and invalid state or retry conflicts return 409. Monetary amounts use integer minor units and three-letter currency codes normalized to uppercase.

See [docs/design/Overview.md](docs/design/Overview.md) for state transitions, assumptions, concurrency boundaries and stage-three trade-offs. `src/main/java/com/practice/stripe/Practice.java` is a small end-to-end walkthrough. `src/test/java/com/practice/stripe/` contains the executable examples and failure cases.

These are local practice implementations: stored data and retry results live only for the lifetime of the JVM. The separate `~/workspaces/stripe-webhook-delivery` copy is not synchronized by these changes.
