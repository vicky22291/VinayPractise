# LLD and machine-coding practice

This folder holds runnable practice projects and interview prompts.

| Folder | Practice |
|---|---|
| [`stripe-staff-coding/`](stripe-staff-coding/README.md) | A Stripe-oriented practice path: candidate-reported coding formats plus four new payment-domain LLD drills |
| [`invoice-matching/practice-version/`](invoice-matching/practice-version/README.md) | Standalone Java workspace: payment and invoice reconciliation |
| [`transaction-rules/practice-version/`](transaction-rules/practice-version/README.md) | Standalone Java workspace: ordered transaction rule evaluation |
| [`bikemap-integration/practice-version/`](bikemap-integration/practice-version/README.md) | Standalone Java starter: recorded rides and a documented map-rendering API |
| [`payment-lifecycle/practice-version/`](payment-lifecycle/practice-version/README.md) | Standalone Java workspace: authorization, capture, and idempotency |
| [`ledger-transfers/practice-version/`](ledger-transfers/practice-version/README.md) | Standalone Java workspace: transfers, immutable entries, and reversals |
| [`subscription-proration/practice-version/`](subscription-proration/practice-version/README.md) | Standalone Java workspace: prorated subscription charges and credits |
| [`webhook-delivery/practice-version/`](webhook-delivery/practice-version/README.md) | Standalone Java workspace: webhook delivery and retries |
| [`hotel-booking/`](hotel-booking/README.md) | 90-minute staged hotel reservation API |
| [`rate_limiter/`](rate_limiter/README.md) | Thread-safe in-process rate limiter |
| [`qa-bank/`](qa-bank/README.md) | Question and answer API machine-coding exercise |

For each rep, timebox yourself, say your assumptions aloud, and keep a short run log. Start with the prompt only. Treat follow-ups as new requirements, not as an invitation to rewrite everything.

## Fresh Java starters

Each `fresh-practise-version-1` contains Java 21, Spring Boot, MapStruct, an Echo controller, a MockMvc request/response test, and executable build/test/run scripts. Start with its `TASK.md` and implement the exercise yourself.

| Question | Fresh starter | Default HTTP port |
|---|---|---:|
| Payment and invoice reconciliation | [fresh-practise-version-1](invoice-matching/fresh-practise-version-1/README.md) | 8101 |
| Transaction rules | [fresh-practise-version-1](transaction-rules/fresh-practise-version-1/README.md) | 8102 |
| Payment authorization and capture | [fresh-practise-version-1](payment-lifecycle/fresh-practise-version-1/README.md) | 8103 |
| Ledger transfers and reversals | [fresh-practise-version-1](ledger-transfers/fresh-practise-version-1/README.md) | 8104 |
| Webhook delivery service | [fresh-practise-version-1](webhook-delivery/fresh-practise-version-1/README.md) | 8105 |
| BikeMap integration | [fresh-practise-version-1](bikemap-integration/fresh-practise-version-1/README.md) | 8106 |
| Subscription proration (existing) | [fresh-practise-version-1](subscription-proration/fresh-practise-version-1/README.md) | 8096 |

From any starter directory, run `./scripts/build.sh`, `./scripts/test.sh`, or `./scripts/run.sh`. Override the server port with `PORT=9000 ./scripts/run.sh`. BikeMap also includes its current ride fixture, vendor reference, and unchanged simulator.
