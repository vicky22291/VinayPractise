# Subscription proration: implemented Java practice

This standalone project implements **all three stages** of the question in `stripe-staff-coding/questions/`. It follows the QA Bank approach: a thin HTTP layer, domain records, services, in-memory storage where needed, and tests. Read [TASK.md](TASK.md) for stage one and [interviewer/FOLLOWUPS.md](interviewer/FOLLOWUPS.md) for later requirements.

## Run

With Maven and JDK 21 or newer installed, use the scripts to build and test:

```bash
./scripts/build.sh             # clean and package the executable JAR; skips test execution
./scripts/test.sh              # run all tests
./scripts/test.sh -Dtest=ProrationCalculatorTest  # run one test class
```

The scripts work from any directory when invoked by path and forward additional arguments to Maven. Build output and test reports are under `target/`.

```bash
cd lld-practise/subscription-proration/practice-version
mvn test                    # business, concurrency (where relevant), and MockMvc API tests
mvn compile exec:java       # runnable three-stage example; no server required
mvn spring-boot:run          # API on :8095
mvn package                 # executable Spring Boot JAR
```

Use `PORT=9000 mvn spring-boot:run` for another port. Open [requests.http](requests.http) in IntelliJ and run requests sequentially; response handlers save generated IDs for later requests. Java 21 target, Spring Boot 3.5.16, Jackson, validation, MapStruct and JUnit 5 remain configured. The test-only subclass mock maker avoids agent self-attachment on restricted JDKs. `/health` and `/echo` remain available.

## Implemented stages and APIs

| Stage | Implementation | Main checks |
|---|---|---|
| 1 | Pure signed plan-change adjustment | UTC time, `[start,end)`, half units away from zero |
| 2 | Quantities and multiple consecutive plan intervals | Exact arithmetic, no gaps or overlaps, one final rounding |
| 3 | Uniform percentage discount in basis points | Discount applied before rounding; tax/reset/finalization discussed in design |

`POST /prorations` returns 200 with the signed minor-unit `adjustment`, exact numerator/denominator, and interval breakdown. There is no stored state, so no idempotency header is needed.

```json
{
  "currency": "USD",
  "start": "2026-01-01T00:00:00Z",
  "end": "2026-01-31T00:00:00Z",
  "initial": {"price": 2000, "quantity": 1},
  "changes": [
    {"at": "2026-01-16T00:00:00Z", "plan": {"price": 3000, "quantity": 1}}
  ],
  "discountBasisPoints": 0
}
```

This returns +500. Set `discountBasisPoints` to 1000 (10%) for +450. Omit it for zero discount. Use a one-element change list for stage one; add strictly increasing changes and quantities for stage two. A change at period end is rejected because the period end is exclusive.

## Integration tests

`FullStackApiTest` and `ExerciseApiTest` send JSON through MockMvc using the complete Spring Boot application context. Controllers, services and repositories are real beans. No internal application beans are mocked; writes are followed by GET requests and assertions on stored data. Run `mvn test '-Dtest=FullStackApiTest,ExerciseApiTest'` for these integration tests, or `mvn test` for all tests.

## Contract and design

Bad input returns 400, missing resources return 404, and invalid state or retry conflicts return 409. Monetary amounts use integer minor units and three-letter currency codes normalized to uppercase.

See [docs/design/Overview.md](docs/design/Overview.md) for state transitions, assumptions, concurrency boundaries and stage-three trade-offs. `src/main/java/com/practice/stripe/Practice.java` is a small end-to-end walkthrough. `src/test/java/com/practice/stripe/` contains the executable examples and failure cases.

These are local practice implementations: stored data and retry results live only for the lifetime of the JVM. The separate `~/workspaces/stripe-subscription-proration` copy is not synchronized by these changes.
