# Stripe Staff coding practice path

Use this as a practice plan for a Staff-level Stripe coding interview. It is a set of exercises, not a claim about Stripe's official interview loop.

## What to expect

Public evidence is incomplete. Stripe's current job listings describe coding as language-agnostic, but do not publish a Staff-specific coding rubric or a fixed round sequence. A current [Staff Backend Engineer listing](https://stripe.com/careers/listing/staff-backend-engineer-ci-services/8089815) emphasizes leading large technical projects, making architecture decisions, writing code, and mentoring. Recent candidate reports describe practical coding: extend a solution as requirements arrive, debug unfamiliar code, integrate an API, and explain edge cases. One September 2026 account reconstructed an invoice-matching prompt in three stages; another described the matching, redirect-debugging, map-integration, and transaction-rules rounds. These are individual reports, and the interviewer's exact prompt may differ.

For this round, prepare to:

- Clarify input, output, invariants, and ambiguous business rules before coding.
- Build a small correct first version, then adapt it while keeping previous behavior.
- Use tests and examples to check assumptions. Explain edge cases as you find them.
- Keep code easy to change. At Staff level, narrate why a seam is useful and where you would stop.
- Discuss concurrency, retries, and operational concerns when the prompt reaches them. Do not add distributed machinery before the requirements need it.

**Ask your recruiter what format and AI policy apply to your loop.** The reports below do not establish the current process for every team or level.

Sources: [Stripe engineering role listing](https://stripe.com/careers/listing/backend-engineer-payments-risk/8260985?gh_jid=8260985) (language-agnostic coding statement); [September 2026 candidate report](https://prachub.com/interview-experiences/stripe-software-engineer-interview-experience-reconciliation-a-requests-307-bug-squash-bikemap-and-an-ai-exercise-no-offer); [second September 2026 candidate report](https://prachub.com/interview-experiences/stripe-software-engineer-interview-experience-ai-coding-reconciliation-and-a-debugger-that-would-not-run). Candidate reports are anecdotal and some prompt details are reconstructed.

## Java workspaces

Each question has its own standalone Java project, following the `lld-practise/qa-bank/practice-version` layout. **The four Staff object-design questions (payment lifecycle, ledger transfers, subscription proration and webhook delivery) now have complete implementations of all three stages**, including HTTP APIs, plain Java demos, business/API tests and design notes. Invoice matching and transaction rules remain starters. There is also a separate workspace for each question under `~/workspaces`. Each project has its own Maven configuration, code, tests, initial prompt, and interviewer follow-ups.

| Question | Project in this repo | Workspace under `~/workspaces` | HTTP port |
|---|---|---|---:|
| Invoice matching | [practice-version](../invoice-matching/practice-version/README.md) | `stripe-invoice-matching` | 8091 |
| Transaction rules | [practice-version](../transaction-rules/practice-version/README.md) | `stripe-transaction-rules` | 8092 |
| Payment lifecycle | [practice-version](../payment-lifecycle/practice-version/README.md) | `stripe-payment-lifecycle` | 8093 |
| Ledger transfers | [practice-version](../ledger-transfers/practice-version/README.md) | `stripe-ledger-transfers` | 8094 |
| Subscription proration | [practice-version](../subscription-proration/practice-version/README.md) | `stripe-subscription-proration` | 8095 |
| Webhook delivery | [practice-version](../webhook-delivery/practice-version/README.md) | `stripe-webhook-delivery` | 8096 |

Libraries match `~/workspaces/qa-bank`: Java 21 compilation, Spring Boot 3.5.16, Spring Web, Jackson, validation, MapStruct, JUnit 5, Mockito, AssertJ, and MockMvc. Each project supports a plain Java entry point and an HTTP server, and builds on the installed JDK 27.

```bash
cd lld-practise/invoice-matching/practice-version
mvn test
mvn compile exec:java       # plain Java
mvn spring-boot:run         # HTTP API, when the question needs one
```

Read each project's `TASK.md` first. Later requirements are in `interviewer/FOLLOWUPS.md`, to be revealed one stage at a time during a mock. For the four implemented questions, the project README maps each stage to its implementation, `requests.http` exercises the APIs, and `docs/design/Overview.md` explains assumptions and follow-ups. Run `mvn compile exec:java` in any of those four projects for its three-stage walkthrough. The repo projects and the workspaces under `~/workspaces` are separate copies; these implementations update only the repo projects. The original Python debugging and API integration kits remain separate exercises.

### Integration tests for the four implemented projects

`FullStackApiTest` and `ExerciseApiTest` use `@SpringBootTest` plus `@AutoConfigureMockMvc`. Requests pass through JSON deserialization, validation, controllers, services and the actual in-memory repositories. Tests read data back through GET endpoints to verify persisted state. There are no mocked application beans, services or repositories. Each full-stack test closes its application context afterward to keep data independent between tests.

| Project | Application integration scenarios | What they verify |
|---|---:|---|
| Payment lifecycle | 8 | Lifecycle/cancellation, partial capture, original-result retries, rejection atomicity, concurrent captures, and accepted-timeout reconciliation with the actual configured processor simulator |
| Ledger transfers | 8 | Transfers and balance audits, immutable balanced entries, funded/unfunded reversals, arithmetic overflow, retry conflicts, concurrent transfers and reversals |
| Subscription proration | 6 | Upgrades/credits, signed rounding, quantities, adjacent intervals, exact fractions, discounts, chronology and validation |
| Webhook delivery | 9 | Routing, event deduplication, real HTTP sender success/503/timeout, bounded retries, claim races, actual lease expiry and stale-token rejection |

Run the complete test suite inside each project with `mvn test`. To run only the application integration scenarios:

```bash
mvn test '-Dtest=FullStackApiTest,ExerciseApiTest'
# Payment lifecycle additionally includes the processor-uncertainty scenario:
mvn test '-Dtest=FullStackApiTest,ExerciseApiTest,UncertainCaptureApiTest'
```

MockMvc exercises the full Spring request flow in-process. The webhook full-stack tests also start a local HTTP receiver and use the real `HttpWebhookSender`, asserting received JSON and stable identifiers. They wait for the real 10-second sender timeout and 30-second lease expiration, so that suite takes roughly a minute and needs loopback socket access. The faster unit tests use an injected clock to test retry timing without waiting.

## Practice order

### A. Start with reported practical-coding formats

These are already staged, spoiler-gated practice kits in [`ai-coding/`](../../ai-coding/README.md). Use their own instructions and avoid the `interviewer/` folders until after a run.

| Order | Kit | What it trains | Suggested time |
|---|---|---|---:|
| 1 | [`04-invoice-matching`](../../ai-coding/04-invoice-matching/README.md) | Evolving matching rules, preserving old behavior, edge cases | 60 min |
| 2 | [`02-http-redirect-bug-squash`](../../ai-coding/02-http-redirect-bug-squash/README.md) | Reproduce a bug, inspect unfamiliar code, make a narrow fix | 60 min |
| 3 | [`03-bikemap-integration`](../../ai-coding/03-bikemap-integration/README.md) | Read API docs, transform input, handle an HTTP response | 60 min |
| 4 | [`01-transaction-rules`](../../ai-coding/01-transaction-rules/README.md) | Extend a rule evaluator in stages and handle expression edge cases | 60 min |

Run a kit with `python3 ai-coding/kit.py start <kit-name>`. The kit README explains how to check your work and reveal the next part. Practice the reported formats both with and without AI where the kit recommends it; reports conflict or omit the policy for some rounds.

### B. Add Staff-level object-design coding reps

Do these as 50 to 60 minute sessions. Pick your interview language. Spend roughly 5 minutes clarifying, 5 minutes sketching the model, 30 to 35 minutes implementing, and the remaining time testing and discussing follow-ups. Each file has staged requirements: stop after each stage and ask your mock interviewer to reveal the next one.

| Order | Prompt | Main skill |
|---|---|---|
| 5 | [Payment authorization and capture](questions/01-payment-lifecycle.md) | State transitions, idempotency, safe retries |
| 6 | [Ledger transfers and reversals](questions/02-ledger-transfers.md) | Money invariants, atomic updates, immutable history |
| 7 | [Subscription proration](questions/03-subscription-proration.md) | Money arithmetic, time boundaries, evolving rules |
| 8 | [Webhook delivery service](questions/04-webhook-delivery.md) | Retry state, duplicate delivery, worker recovery |

## Score each rep

Give yourself 1 to 4 in each area, then write one concrete fix for the next run.

| Area | A 4 looks like |
|---|---|
| Clarifying | You asked about ambiguity that changes behavior, then stated your chosen assumptions. |
| Design | The smallest useful set of types and responsibilities; extensions fit without a rewrite. |
| Correctness | Core paths, invalid operations, and boundary cases are covered with examples or tests. |
| Communication | You explain decisions, trade-offs, and what you are checking as you work. |
| Staff judgment | You identify the important failure or concurrency boundary and defer unrelated infrastructure. |

## Run log

| Date | Prompt | Time | Finished stage | Strongest part | One fix for next time |
|---|---|---:|---|---|---|
| | | | | | |

For a mock, ask: **"Start Stripe practice question 5. Give me only the first stage, act as the interviewer, and wait for my clarifying questions before adding requirements."**
