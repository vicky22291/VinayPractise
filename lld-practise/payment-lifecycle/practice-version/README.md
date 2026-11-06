# Payment authorization and capture: implemented Java practice

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
cd lld-practise/payment-lifecycle/practice-version
mvn test                    # business, concurrency (where relevant), and MockMvc API tests
mvn compile exec:java       # runnable three-stage example; no server required
mvn spring-boot:run          # API on :8093
mvn package                 # executable Spring Boot JAR
```

Use `PORT=9000 mvn spring-boot:run` for another port. Open [requests.http](requests.http) in IntelliJ and run requests sequentially; response handlers save generated IDs for later requests. Java 21 target, Spring Boot 3.5.16, Jackson, validation, MapStruct and JUnit 5 remain configured. The test-only subclass mock maker avoids agent self-attachment on restricted JDKs. `/health` and `/echo` remain available.

## Implemented stages and APIs

| Stage | Implementation | Main checks |
|---|---|---|
| 1 | Create, authorize, full capture, cancel | Positive money, normalized currency, legal transitions |
| 2 | Multiple partial captures and idempotent writes | No overcapture, original result replay, payload conflicts |
| 3 | Processor interface, unknown outcome, reservation and reconciliation | Accepted-but-timed-out capture cannot charge twice |

| Method | Path | Result |
|---|---|---|
| POST | `/payments` | Create with `amount`, `currency`: 201 |
| GET | `/payments/{id}` | Current payment snapshot: 200 |
| POST | `/payments/{id}/authorize` | Authorize: 200 |
| POST | `/payments/{id}/cancel` | Cancel before any capture or reservation: 200 |
| POST | `/payments/{id}/captures` | Capture with `amount`, or `{}` for all remaining funds: 201 |
| GET | `/payments/{id}/captures` | Capture records: 200 |
| POST | `/payments/{id}/captures/{captureId}/reconcile` | Resolve an uncertain capture: 200 |

The default processor simulator succeeds. To exercise an accepted charge whose response is lost:

```bash
mvn spring-boot:run -Dspring-boot.run.arguments=--processor.timeout-after-accept=true
```

The first capture returns `UNKNOWN`; authorization remains reserved. Reconcile with a new request key to query/retry the **same processor capture ID**. The simulator returns the previously accepted charge. Replaying the original capture key still returns its original `UNKNOWN` snapshot; GET returns current state. The plain Java demo exercises this path automatically.

## Integration tests

`FullStackApiTest` and `ExerciseApiTest` send JSON through MockMvc using the complete Spring Boot application context. Controllers, services and repositories are real beans. No internal application beans are mocked; writes are followed by GET requests and assertions on stored data. Run `mvn test '-Dtest=FullStackApiTest,ExerciseApiTest'` for these integration tests, or `mvn test` for all tests.

`UncertainCaptureApiTest` also tests accepted processor timeouts and reconciliation using the actual configured `SimulatedProcessor`. It verifies that competing captures/cancellation are blocked while funds are reserved, retries retain their original snapshot, and reconciliation creates no duplicate processor charge. Include it with `mvn test '-Dtest=FullStackApiTest,ExerciseApiTest,UncertainCaptureApiTest'`.

## Contract and design

Client writes require a nonblank `Idempotency-Key` (except webhook worker commands, which use claim tokens). Keys are global within this single-tenant service, across operations and targets. Reusing a key with the same normalized request returns the original immutable result, even after later changes; a different request returns 409. Rejected operations do not consume keys. Reads always return current snapshots.

Bad input returns 400, missing resources return 404, and invalid state or retry conflicts return 409. Monetary amounts use integer minor units and three-letter currency codes normalized to uppercase.

See [docs/design/Overview.md](docs/design/Overview.md) for state transitions, assumptions, concurrency boundaries and stage-three trade-offs. `src/main/java/com/practice/stripe/Practice.java` is a small end-to-end walkthrough. `src/test/java/com/practice/stripe/` contains the executable examples and failure cases.

These are local practice implementations: stored data and retry results live only for the lifetime of the JVM. The separate `~/workspaces/stripe-payment-lifecycle` copy is not synchronized by these changes.
