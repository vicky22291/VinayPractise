# Ledger transfers and reversals: implemented Java practice

This standalone project implements **all three stages** of the question in `stripe-staff-coding/questions/`. It follows the QA Bank approach: a thin HTTP layer, domain records, services, in-memory storage where needed, and tests. Read [TASK.md](TASK.md) for stage one and [interviewer/FOLLOWUPS.md](interviewer/FOLLOWUPS.md) for later requirements.

## Run

```bash
cd lld-practise/ledger-transfers/practice-version
mvn test                    # business, concurrency (where relevant), and MockMvc API tests
mvn compile exec:java       # runnable three-stage example; no server required
mvn spring-boot:run          # API on :8094
mvn package                 # executable Spring Boot JAR
```

Use `PORT=9000 mvn spring-boot:run` for another port. Open [requests.http](requests.http) in IntelliJ and run requests sequentially; response handlers save generated IDs for later requests. Java 21 target, Spring Boot 3.5.16, Jackson, validation, MapStruct and JUnit 5 remain configured. The test-only subclass mock maker avoids agent self-attachment on restricted JDKs. `/health` and `/echo` remain available.

## Implemented stages and APIs

| Stage | Implementation | Main checks |
|---|---|---|
| 1 | Accounts and atomic same-currency transfers | Positive money, sufficient funds, no partial updates |
| 2 | Immutable paired entries and idempotent writes | Balanced history and safe retries |
| 3 | Append-only reversal and concurrent operations | One reversal, no overdrafts, balance reconstruction |

| Method | Path | Result |
|---|---|---|
| POST | `/accounts` | Create with `currency`, `openingBalance`: 201 |
| GET | `/accounts/{id}` | Account snapshot: 200 |
| GET | `/accounts/{id}/audit` | Compare stored balance to opening balance plus entries: 200 |
| POST | `/transfers` | Transfer with `sourceId`, `destinationId`, `amount`: 201 |
| GET | `/transfers/{id}` | Transfer and reversal links: 200 |
| POST | `/transfers/{id}/reversals` | Append a full compensating transfer: 201 |
| GET | `/entries` | Immutable signed entries: 200 |

A reversal needs sufficient funds in the original destination. Failure leaves the original transfer and all balances unchanged. Reversing a reversal is rejected. Retry the original reversal key to retrieve its result; another key cannot reverse the original again.

## Integration tests

`FullStackApiTest` and `ExerciseApiTest` send JSON through MockMvc using the complete Spring Boot application context. Controllers, services and repositories are real beans. No internal application beans are mocked; writes are followed by GET requests and assertions on stored data. Run `mvn test '-Dtest=FullStackApiTest,ExerciseApiTest'` for these integration tests, or `mvn test` for all tests.

## Contract and design

Client writes require a nonblank `Idempotency-Key` (except webhook worker commands, which use claim tokens). Keys are global within this single-tenant service, across operations and targets. Reusing a key with the same normalized request returns the original immutable result, even after later changes; a different request returns 409. Rejected operations do not consume keys. Reads always return current snapshots.

Bad input returns 400, missing resources return 404, and invalid state or retry conflicts return 409. Monetary amounts use integer minor units and three-letter currency codes normalized to uppercase.

See [docs/design/Overview.md](docs/design/Overview.md) for state transitions, assumptions, concurrency boundaries and stage-three trade-offs. `src/main/java/com/practice/stripe/Practice.java` is a small end-to-end walkthrough. `src/test/java/com/practice/stripe/` contains the executable examples and failure cases.

These are local practice implementations: stored data and retry results live only for the lifetime of the JVM. The separate `~/workspaces/stripe-ledger-transfers` copy is not synchronized by these changes.
