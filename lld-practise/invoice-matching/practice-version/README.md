# Payment and invoice reconciliation: implemented Java practice

This standalone project implements **all three stages** from [TASK.md](TASK.md) and [interviewer/FOLLOWUPS.md](interviewer/FOLLOWUPS.md). Like payment-lifecycle, it has domain records, a service, a thin HTTP layer, a runnable Java demo, business tests and full-context MockMvc tests.

## Run

With Maven and JDK 21 or newer installed, use the scripts to build and test:

```bash
./scripts/build.sh             # clean and package the executable JAR; skips test execution
./scripts/test.sh              # run all tests
./scripts/test.sh -Dtest=StarterControllerTest  # run one test class
```

The scripts work from any directory when invoked by path and forward additional arguments to Maven. Build output and test reports are under `target/`.

```bash
cd lld-practise/invoice-matching/practice-version
mvn test                    # matching, parsing, validation and HTTP tests
mvn compile exec:java       # runnable examples for all three stages
mvn spring-boot:run          # API on :8091
mvn package                 # executable Spring Boot JAR
```

For another port: `PORT=9000 mvn spring-boot:run`. Open [requests.http](requests.http) in IntelliJ for examples. Java 21, Spring Boot 3.5.16, validation, Jackson, MapStruct and JUnit 5 remain configured; `/health` and `/echo` remain available. The test-only subclass mock maker avoids agent self-attachment on restricted JDKs.

## Implemented stages

| Stage | Selector | Behavior |
|---|---|---|
| 1 | `MEMO_ONLY` | First still-open whole invoice ID in memo order, regardless of amount |
| 2 | `EXACT_AMOUNT` | Memo first; otherwise exact amount, earliest due date then lexical invoice ID |
| 3 | `TOLERANCE` | Memo, then exact amount, then inclusive amount tolerance; earliest due date then lexical ID |

Payments run in input order. An invoice is consumed once per batch across **all** rules. Tolerance candidates are ordered by due date and ID, not by smallest amount difference. Each result includes the payment, the matched invoice (or `null`) and its rule: `MEMO`, `EXACT_AMOUNT`, `TOLERANCE` or `NONE`.

The plain Java entry points are:

```java
var service = new ReconciliationService();
service.reconcile(payments, invoices);                             // stage 1
service.reconcile(payments, invoices, MatchingStage.EXACT_AMOUNT, 0); // stage 2
service.reconcile(payments, invoices, 5);                          // stage 3, tolerance 5
```

## HTTP contract

`POST /reconciliations` returns 200 with one result per payment:

```json
{
  "payments": ["p1,500,Paying INV-12, thanks", "p2,500,"],
  "invoices": ["INV-1,500,2026-11-10", "INV-12,700,2026-11-12"],
  "stage": "TOLERANCE",
  "tolerance": 5
}
```

```json
{
  "results": [
    {
      "payment": {"id": "p1", "amount": 500, "memo": "Paying INV-12, thanks"},
      "invoice": {"id": "INV-12", "amount": 700, "dueDate": "2026-11-12"},
      "rule": "MEMO"
    },
    {
      "payment": {"id": "p2", "amount": 500, "memo": ""},
      "invoice": {"id": "INV-1", "amount": 500, "dueDate": "2026-11-10"},
      "rule": "EXACT_AMOUNT"
    }
  ]
}
```

The HTTP defaults are `stage=TOLERANCE` and `tolerance=0`; explicitly select `MEMO_ONLY` to exercise the original two-argument Java contract. Omitted or null optional fields use those defaults. Tolerance must be a nonnegative `long`; fractional numeric tolerance values are rejected. Earlier stages ignore a valid tolerance.

## Parsing and batch scope

Malformed input rejects the whole batch with `IllegalArgumentException` in Java or HTTP 400 with an `error` string. Row errors identify the payment/invoice and its one-based row number. Both lists are required, but may be empty. Null rows and duplicate payment/invoice IDs are rejected. Structured fields are trimmed; memos retain their original text, including commas and empty text. Amounts are unsigned decimal integers in `[0, Long.MAX_VALUE]`, and dates must be real ISO calendar dates in `YYYY-MM-DD` form. These are delimited rows, not quoted CSV.

Memo IDs are case-sensitive `INV-` plus ASCII digits. Letters, numbers, underscores and hyphens cannot touch either side of an ID; spaces and other punctuation delimit it. Thus `(INV-12), thanks` matches `INV-12`, while `INV-12x`, `xINV-12`, `INV-12-extra` and `INV-123` do not match `INV-12`. Leading zeros are significant: `INV-01` and `INV-1` are distinct IDs. Unknown or already-consumed references are skipped so a later open reference can win.

Each call is independent and has no external effects or stored state. Identical batch retries return equal results. This is not a persistent settlement system: separate requests may match the same invoice supplied in each request. See [docs/design/Overview.md](docs/design/Overview.md) for indexing, complexity, retry/concurrency trade-offs and disputed-match logging.

## Tests

`ReconciliationServiceTest` covers the prompt example, parsing, ID boundaries, memo order, rule priority, date/lexical tie-breaking, consumption across rules, tolerance boundaries, zero and maximum amounts, malformed rows, batch independence and immutable results. `FullStackApiTest` sends JSON through real application beans, testing all stages, HTTP defaults, retries and 400 responses. The starter HTTP/MapStruct tests also remain.

```bash
mvn test '-Dtest=ReconciliationServiceTest,FullStackApiTest'
```

The separate `~/workspaces/stripe-invoice-matching` copy is not synchronized by these changes.
