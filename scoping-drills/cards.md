# Scoping Drill Cards (interviewer only)

> **Candidate: do not read past this line.** This file is for the voice agent. The rules, scorecard and log live in [`README.md`](README.md).

**One line:** 48 hidden cards for 10-minute sprints. 12 come from reported interview prompts (Part A). 22 are Stripe-style prompts constructed from Stripe's public product behaviour (Part B). 6 are general Staff prompts (Part C). 8 more reported prompts come from the desktop research (Part D).

---

## 0. How to run a rep (voice agent)

1. Pick the next card in the rotation (§0.1) that is not already in the log in `README.md` §8.
2. Check the card's **mode** in §0.1. **Stripe mode:** scope closes by minute 5, then the candidate sketches the API and a skeleton until minute 10. **Ambiguity mode:** scope closes by minute 8.
3. Read **only the "Say" line** aloud. Start a 10-minute clock.
4. **The one open question.** If the candidate asks about product intent, answer from **Product context**. If a card says "You pick", say exactly that.
5. **Scale.** On a Stripe-mode card, if asked for numbers, give the card's **Numbers** line. Stripe interviewers state scale up front. What they hold back is the hostile world: retries, misbehaving tenants, attacker input.
6. **Hidden constraints.** Reveal one only when its **trigger** fires: the candidate proposes something that conflicts with it, or asks the precise question. Reveal it in one sentence, as a correction: "Actually, ..."
7. **Other open questions that could have been assumptions** ("what latency?"): reply "What would you assume?" and note it for check 6.
8. **Do not correct unrealistic numbers or weak cuts during the rep.** Silence is not confirmation. Grade them at the end.
9. **Minute 8: one probe.** Ask one "what happens if..." question built from a hidden constraint the candidate has not surfaced. One exchange, then let them continue.
10. **At 10 minutes, stop**, even mid-sentence. Then:
    - Reveal the card: context, all 3 constraints, crux, wrong cut.
    - Score the 9 checks in `README.md` §8. Note the minute the crux was named, and the count of proposals vs open questions.
    - Give **one change** for the next rep. Only one.
    - Write the log row into `README.md` §8. If you cannot write to the repo, say the row aloud so the candidate can paste it.
11. Three sprints a sitting, short breaks between. No deep dive. Optional warm-up: one speed rep (§0.3).

### 0.1 Rotation

Stripe mode first, because the round is 2026-10-19 and 2026-10-20.

- **Stripe mode (29):** `R1, D3, C5, C1, R8, D1, C4, C2, R7, D2, C6, C3, C7, C8, C9, C14, C15, C17, C13, C19, C16, C18, C20, C21, C22, C10, C11, C12, R6`
- **Ambiguity mode (19):** `R2, R3, R4, R5, R9, R10, R11, D4, D5, D6, D7, D8, R12, G1, G2, G3, G4, G5, G6`

### 0.2 Numbers to judge against

Stripe numbers are in `README.md` §7. The short version: ~1k payments/s average, ~2.5k/s at the Black Friday peak, ~27k API req/s peak, 5B ledger events/day, ~5M businesses. A candidate proposing 100k payments/s is 40x high. That fails check 5.

### 0.3 Speed reps

When the candidate asks for a speed rep: a 5-minute clock, scope only, no skeleton. The card is the problem's `hld/<folder>/README.md` plus `solution.md` §1. The list is in `README.md` §10. Score only checks 1, 5 and 8. Log it with the ID `S-<folder>`.

---

## Part A. Reported prompts (12)

The prompt shape is real. Where no source reveals the hidden context, the card is constructed and says so.

### R1. A new service inside a simplified Stripe

- **Say:** "Here is a simplified Stripe: an API gateway, a Charges service, a Customers service, a Ledger and a Webhooks service. Design a new service that lets merchants authorize a card now and capture the money later."
- **Source:** Stripe onsite, reported on [Blind 2021](https://www.teamblind.com/post/stripe-system-design-bxptt8eb) and [Blind 2023](https://www.teamblind.com/post/stripe-system-design-jeaobs2m). The candidate "worked with the interviewer to decide the scale" and got average and peak traffic only on asking. The service choice here is constructed.
- **Product context:** hotels, car rentals and marketplaces that ship later. They hold the money at order time and charge it at shipment.
- **Hidden constraints:**
  1. An authorization expires after about 7 days for most online card payments. **Trigger:** the candidate holds funds "until capture" with no expiry.
  2. Capture is one time, for at most the authorized amount. The rest is released. **Trigger:** the candidate allows several captures or capturing more.
  3. The existing services cannot change. Use the Charges and Ledger APIs as they are. **Trigger:** the candidate edits Charges or writes to the ledger store directly.
- **If asked for traffic:** 300/s average and 1,000/s peak for this service.
- **Crux:** a hold state machine with expiry and exactly one capture under retries, built on services the candidate does not own.
- **Good cuts:** incremental authorization, multi-capture, 3DS, fraud scoring, refunds after capture.
- **Wrong cut:** the expiry and capture lifecycle.

### R2. Payment service provider

- **Say:** "Design a payment service provider."
- **Source:** Adyen, reported on [techprep](https://www.techprep.app/community/interview-experiences/adyen-staff-software-engineer-interview-2025) (snippets only). A rejected loop's feedback, paraphrased: the candidate "did not clarify functional and non-functional requirements" and had "gaps in authorization within the APIs". An Adyen Staff follow-up: "a merchant-to-acquirer call times out. Did the customer get charged twice?"
- **Product context:** online shops send card payments to us. We route each one to an acquiring bank and the card networks. Merchants integrate with our API.
- **Hidden constraints:**
  1. An acquirer call can time out with the outcome unknown, and merchants retry on timeout. **Trigger:** a synchronous charge call, or any mention of retries.
  2. Each merchant has API credentials and many stores. Every request is authorized for that merchant account. **Trigger:** an API sketched with no auth.
  3. There are several acquirers, routed by card type, region and cost. One can go down. **Trigger:** a single bank or network assumed.
- **Crux:** unknown-outcome payment calls. An idempotent merchant API, plus checking the acquirer's state before any retry.
- **Good cuts:** settlement files, fraud model internals, merchant onboarding and KYC, chargebacks.
- **Wrong cut:** timeout and unknown-outcome handling.
- **Numbers:** Adyen processed about €1.3T in 2024. That is the same order as Stripe: about 1k payments/s average, a few thousand at peak.

### R3. Online bank account opening

- **Say:** "Design an online bank account opening workflow."
- **Source:** Coinbase online assessment, Sep 2025, [PracHub](https://prachub.com/interview-questions/design-account-opening-workflow). In the original prompt these constraints are stated. Here they are held back.
- **Product context:** people apply on web or mobile. The business is regulated and runs in several regions.
- **Hidden constraints:**
  1. One person gets exactly one account, even when they retry or resume from another device. **Trigger:** a plain "create account" call, or any mention of retries.
  2. KYC, AML and sanctions checks are asynchronous. They take seconds to days, some go to manual review, and sanctions are re-checked after approval. **Trigger:** a synchronous approval.
  3. Applicants save partial progress, resume later and see live status. **Trigger:** a single-session form.
- **If asked for scale:** "millions of applications a day". That is the only number. About 2M/day is ~23/s.
- **Crux:** a long-running, partly manual workflow, keyed so one person maps to one application and one account.
- **Good cuts:** the OCR model, mobile UI, card issuing, fraud model internals, support tooling.
- **Wrong cut:** the asynchronous verification and manual review states.
- **Watch for:** heavy scale infrastructure. This is a low-QPS, high-correctness problem.

### R4. Embeddable pay-by-bank widget

- **Say:** "Design an embeddable pay-by-bank widget for merchant websites."
- **Source:** Plaid onsite, Aug 2026, [PracHub](https://prachub.com/interview-questions/design-an-embeddable-pay-by-bank-widget). The listed topics are secret boundaries, origin validation, asynchronous payment state and retries. Triggers are constructed.
- **Product context:** a merchant's checkout embeds our widget. The customer logs in to their bank and approves a bank payment. The merchant learns the result.
- **Hidden constraints:**
  1. The merchant page must never see bank credentials or tokens. Login runs in an iframe on our origin, and messages pass through postMessage with origin checks. **Trigger:** merchant JavaScript calls the bank login or handles tokens.
  2. Bank payments settle over days. The widget can only say "initiated". The final status reaches the merchant backend later by webhook. **Trigger:** the widget returns "paid".
  3. The merchant backend swaps a short-lived public token for a credential, server to server. **Trigger:** asking how the merchant backend gets the result.
- **Crux:** the secret boundary between the merchant page, the iframe and the backends, plus asynchronous payment state.
- **Good cuts:** per-bank login flows, transaction sync, merchant payouts, reconciliation.
- **Wrong cut:** origin validation or the token exchange.
- **Numbers:** a few hundred payments/s. Not a scale problem.

### R5. Scheduled payments and cancellation

- **Say:** "Design a service to create, update, execute and cancel future-dated payments."
- **Source:** Coinbase online assessment, Sep 2025, [PracHub](https://prachub.com/interview-questions/design-scheduled-payments-and-cancellation).
- **Product context:** users schedule one-time and recurring transfers, such as rent on the 1st.
- **Hidden constraints:**
  1. Recurrence runs in the user's time zone. It must handle daylight-saving gaps and overlaps, and "the 31st" in short months. **Trigger:** storing UTC timestamps or a cron string.
  2. Cancel races execute, for example a cancel at 8:59:59 for a 9:00 payment. **Trigger:** cancel modelled as a simple delete.
  3. Execution hits the ledger exactly once, even though the runner can pick a job up twice. After an outage, missed jobs backfill without a thundering herd. **Trigger:** a cron worker that scans for due jobs.
- **Crux:** exactly-once execution, plus the cancel race.
- **Good cuts:** FX, KYC, notifications, crypto custody.
- **Wrong cut:** the executor. The verb is "execute".
- **Numbers:** none given, so the candidate proposes them. Expect a spike on the 1st of the month.

### R6. Ads aggregation

- **Say:** "Design an ads aggregation system."
- **Source:** Stripe SDE onsite, [1point3acres](https://www.1point3acres.com/interview/thread/1103507), title only. The card is constructed.
- **Product context:** advertisers see clicks and spend on a dashboard and are billed from the same numbers.
- **Hidden constraints:**
  1. Advertisers are billed from these aggregates, so billing counts must be exact. **Trigger:** approximate counts or sampling.
  2. Events arrive up to hours late (offline mobile) and are duplicated by client retries. **Trigger:** processing-time windows, or counting raw events.
  3. The dashboard needs about 1-minute freshness. Billing numbers are final once a day. **Trigger:** one pipeline serving both with one SLA.
- **Crux:** two consumers with different correctness needs: a fast, approximate dashboard and an exact, final billing count.
- **Good cuts:** the auction, creative serving, click-fraud models.
- **Wrong cut:** dedup and late events.
- **Numbers:** about 10B events/day, ~115k/s average. Accept anything within 3x.

### R7. Take a payments API global

- **Say:** "Our payments API runs in one US region. Take it global."
- **Source:** Stripe Staff, Glassdoor, Jan 2026: "an architecture problem about scaling a global system". Summary only. The card is constructed.
- **Product context:** more than half of new Stripe businesses in 2025 were outside the US. European merchants feel the extra latency.
- **Hidden constraints:**
  1. Data residency. India requires payment data to be stored only in India (RBI). Some enterprise merchants need data to stay in the EU by contract. **Trigger:** replicating all data everywhere.
  2. European merchants pay about 100 to 150 ms extra round trip to the US. The target is p99 under 300 ms for creating a payment. **Trigger:** asking why we are going global.
  3. Each merchant account has one home region. Balances and the ledger have a single writer. **Trigger:** active-active writes everywhere.
- **Crux:** deciding what is global and what is regional. A home region per account for money, regional edges for latency, residency-pinned data.
- **Good cuts:** CDN vendor choice, mobile clients, team structure.
- **Wrong cut:** migration from the existing single region. The prompt starts from a running system, and a Staff answer moves it with zero downtime.
- **Numbers:** ~27k API req/s peak (2023), ~6k average.

### R8. A key component of our payments system

- **Say:** "Design a key component of our payments system."
- **Source:** Stripe, Seattle 2024, Glassdoor summary. The card is constructed.
- **If asked which component:** "You pick. Tell me why." Grade the choice. The strong pick is the payment lifecycle state machine: create, wait for customer action, process, succeed or fail. If they pick something peripheral (notifications, a dashboard), ask "why is that the key one?"
- **Hidden constraints (for the payment state machine pick):**
  1. 3DS bank challenges make a payment wait minutes for the customer. **Trigger:** a synchronous charge.
  2. Card network calls time out with an unknown outcome. **Trigger:** any retry design.
  3. Merchant servers retry with an idempotency key, which is kept at least 24 hours. **Trigger:** "create payment" with no dedup.
- **Crux:** choosing the component is the test. After that: a payment state machine with asynchronous customer action and unknown outcomes.
- **Good cuts:** payouts, disputes, Radar, the dashboard.
- **Wrong cut:** picking a component off the money path.
- **Numbers:** ~1k payments/s average, ~2.5k/s peak.

### R9. Mobile check deposit

- **Say:** "Design mobile check deposit."
- **Source:** Chime, Senior SWE, Jan 2025, Glassdoor summary. The card is constructed.
- **Product context:** members photograph a paper check and the money appears in their account.
- **Hidden constraints:**
  1. Regulation says a small first slice is available the next business day and the rest after a hold. A check can bounce days later. **Trigger:** crediting the full amount at once.
  2. The same check gets deposited twice, by re-upload or at another bank. **Trigger:** any talk of upload retries.
  3. Some images fail automatic reading and go to human review. The check must be endorsed "for mobile deposit only". **Trigger:** assuming OCR always works.
- **Crux:** no double credit, plus holds and returns that unfold over days.
- **Good cuts:** the OCR model, camera UX, check-clearing network details, fraud models.
- **Wrong cut:** the returned-check path.
- **Numbers:** about 10M members and a few hundred thousand deposits a day, ~5/s. A correctness problem.

### R10. End-to-end banking system

- **Say:** "Design an end-to-end banking system."
- **Source:** Block, New York, Feb 2026, Glassdoor snippet. The card is constructed.
- **If asked which product:** "Like Cash App. A balance, direct deposit in, peer-to-peer sends, and a debit card."
- **Hidden constraints:**
  1. Card authorizations arrive in real time from the network and need an answer within about a second. Direct deposits arrive in ACH batches. **Trigger:** one synchronous transfer flow for everything.
  2. The balance can never go negative from a card authorization and a peer-to-peer send at the same moment. **Trigger:** read the balance, then write it.
  3. A peer-to-peer send is instant for the user, and later reversible as fraud. **Trigger:** treating sends as final.
- **Crux:** one balance fed by several rails with very different timing, and concurrency on that balance.
- **Good cuts:** lending, investing, crypto, regulatory reporting, the app UI.
- **Wrong cut:** the debit card path, if the candidate defined the product to include it.
- **Numbers:** Cash App has about 57M monthly transacting actives (Block, 2024).

### R11. Pagination for a large dataset

- **Say:** "Design pagination for an API over a large dataset."
- **Source:** Coinbase, Feb 2026, PracHub category summary. The card is constructed.
- **Product context:** the transaction history API. Some users have millions of transactions, and new ones arrive while they page.
- **Hidden constraints:**
  1. New rows land while the client pages, so offset paging skips or repeats rows. **Trigger:** offset and limit.
  2. Clients filter and sort by date, asset and amount. **Trigger:** a single cursor on id.
  3. In tax season some clients want all 5M rows. **Trigger:** any talk of page size or big clients.
- **Crux:** a stable cursor under concurrent inserts, with sort and filter. Bulk export is a separate path.
- **Good cuts:** storage engine choice, UI infinite scroll, a caching layer.
- **Wrong cut:** consistency between pages.
- **Numbers:** about 100M users, p99 under 200 ms per page.

### R12. Picture upload pipeline

- **Say:** "Design an end-to-end pipeline for user picture uploads."
- **Source:** Coinbase, Aug 2025, PracHub category summary. The card is constructed.
- **Product context:** users upload profile pictures and photos of identity documents for verification.
- **Hidden constraints:**
  1. Identity documents are PII. They are encrypted, access is audited, and they never go on a public CDN. Profile pictures are public. **Trigger:** all images on a CDN.
  2. Phones on flaky networks upload files up to 20 MB, so uploads must resume. **Trigger:** one POST through the API servers.
  3. Every image is scanned before anyone can see it. Resizing is asynchronous. **Trigger:** images visible immediately.
- **Crux:** the PII split, plus direct-to-storage upload with asynchronous processing.
- **Good cuts:** image ML models, editing UI, video.
- **Wrong cut:** the identity-document path.
- **Numbers:** about 1M uploads a day, ~12/s.

---

## Part B. Stripe-style prompts (22, constructed)

None of these is a reported prompt. Each is built from how Stripe's product works in its public docs. Constraint numbers are interviewer choices.

### C1. Payouts

- **Say:** "Design the system that pays merchants their balance."
- **Product context:** we collect card payments for merchants. They want the money in their bank account.
- **Hidden constraints:**
  1. Funds sit as pending for days while card payments settle. Payouts come only from the available balance. **Trigger:** paying out each payment as it arrives.
  2. A payout can be marked paid and still fail days later, when the bank returns it (for example, a closed account). The money comes back to the balance. **Trigger:** "send and done".
  3. Refunds and disputes after a payout can push the balance negative. Then the next payout shrinks or the bank account is debited. **Trigger:** assuming the balance is never below zero.
- **Crux:** computing a correct available balance and paying it out exactly once while money keeps moving underneath.
- **Good cuts:** instant payouts to debit cards (seam: rail choice), multi-currency payouts, tax forms, the dashboard.
- **Wrong cut:** failed and returned payouts.
- **Numbers:** ~5M businesses, about 1 to 2M payouts a day, batched by bank cut-off times. Payout create is capped at 15/s per account. Not a QPS problem.

### C2. Refunds

- **Say:** "Design refunds."
- **Product context:** merchants refund customers through the API or the dashboard.
- **Hidden constraints:**
  1. Refunds can be partial, and a payment can have many, but the total never exceeds the captured amount. Two support agents can click refund at the same time. **Trigger:** one simple "refund payment" call.
  2. A refund can fail days later because the card was closed or expired. The money returns to the merchant, who must be told. **Trigger:** a synchronous success.
  3. A refund debits the merchant's balance. If the balance is too low, the refund still goes through and the balance goes negative. **Trigger:** checking the balance and rejecting the refund.
- **Crux:** concurrent partial refunds that never exceed the captured amount, plus asynchronous failure.
- **Good cuts:** refund UI, currency conversion, refund-fraud detection, refund-reason analytics.
- **Wrong cut:** the failure path.
- **Numbers:** a few percent of payments, ~50/s. A correctness problem.

### C3. Disputes

- **Say:** "Design dispute handling for merchants."
- **Product context:** a cardholder tells their bank they did not make a payment. The card network tells us, and the merchant can fight it.
- **Hidden constraints:**
  1. The money and a dispute fee are taken from the merchant as soon as the dispute opens. **Trigger:** holding money only if the dispute is lost.
  2. The network sets a hard evidence deadline, typically 7 to 21 days. Missing it is an automatic loss. Evidence can be submitted only once. **Trigger:** a draft-and-edit loop, or no deadline.
  3. Network messages are asynchronous and batchy. The outcome arrives weeks to months later. **Trigger:** expecting a synchronous answer.
- **Crux:** a long-lived, deadline-driven case workflow that moves money at open and again at close, with one-shot submission.
- **Good cuts:** fraud prevention, ML evidence generation, inquiry vs dispute differences, dashboard UI.
- **Wrong cut:** the deadline and reminder mechanism.
- **Numbers:** well under 1% of payments, ~1 to 5/s.

### C4. API keys

- **Say:** "Design API keys for a payments platform."
- **Product context:** merchants authenticate every API call with a secret key.
- **Hidden constraints:**
  1. Every request checks the key: 27k req/s at peak, with under 1 ms to spare. **Trigger:** a database lookup per request.
  2. A leaked key must stop working within seconds. Leaks are often found on public code hosts and reported automatically. **Trigger:** caching keys for minutes.
  3. "Roll key" keeps the old key working for a chosen window, up to days, so the merchant can deploy. Restricted keys carry per-resource permissions. **Trigger:** rotation as an instant swap.
- **Crux:** fast verification with no database hit, against fast revocation. The cache and revocation must agree.
- **Good cuts:** OAuth for platforms, dashboard UI, usage analytics.
- **Wrong cut:** revocation.
- **Numbers:** ~5M businesses with a few keys each, 10 to 20M keys. Small enough to fit in memory.

### C5. Hosted checkout page

- **Say:** "Design a hosted checkout page that merchants redirect customers to."
- **Product context:** the merchant's server creates a session with line items, then redirects the customer to our page.
- **Hidden constraints:**
  1. Customers open the link in two tabs, double-click Pay, or come back later. Charge at most once per session. **Trigger:** creating a payment on every click.
  2. The redirect back to the merchant can fail when the customer closes the tab. The merchant must fulfil from a server-side event, not the redirect. **Trigger:** using the success redirect as the signal.
  3. Sessions expire, by default after 24 hours. A 3DS bank challenge can pause the flow for minutes. **Trigger:** assuming a synchronous click-to-paid.
- **Crux:** exactly one successful payment per session, across tabs, retries, bank challenges and an unreliable redirect.
- **Good cuts:** theming, tax, address autocomplete, localization.
- **Wrong cut:** the fulfilment event.
- **Numbers:** ~1k payments/s, 2.5k/s at the Black Friday peak. Single-merchant flash sales spike hard.

### C6. Public API versioning

- **Say:** "Design how our public API changes over time without breaking integrations."
- **Product context:** millions of merchant integrations, many of which never update their code.
- **Hidden constraints:**
  1. Integrations written years ago must keep working unchanged. Merchants upgrade when they choose. **Trigger:** sunsetting old versions after N months.
  2. Webhook payloads are rendered in the merchant's version too, not just API responses. **Trigger:** looking only at request and response.
  3. Engineers ship many breaking changes a year, so keeping N copies of the code is not an option. **Trigger:** parallel `/v1` and `/v2` code paths.
- **Crux:** one current code path, plus a chain of small transforms that turn the current response back into each account's pinned version.
- **Good cuts:** SDK generation, the docs site, GraphQL.
- **Wrong cut:** webhooks, or pinning a version per account.
- **Numbers:** 27k req/s at peak, so each transform must be cheap. Dozens of versions over a decade.

### C7. Usage-based billing

- **Say:** "Design usage-based billing."
- **Product context:** SaaS and AI companies charge their customers per API call or per token. They send usage events to us, and we invoice at the end of the period.
- **Hidden constraints:**
  1. Customers retry sends, so events arrive duplicated. Each event carries an identifier for dedup. **Trigger:** counting raw events.
  2. Events arrive minutes to hours late. The invoice is drafted at period end and finalized about an hour later. Usage after that goes on the next invoice. **Trigger:** invoicing at exactly period end.
  3. A few customers send 10k+ events/s (AI token metering) while most send few. Customers want near-real-time usage so they can cap spend. **Trigger:** assuming uniform load.
- **Crux:** exactly-once aggregation per customer per period, with late events and a finalization cut-off.
- **Good cuts:** pricing-model UI, tax, revenue recognition, invoice PDFs.
- **Wrong cut:** the late-event and finalization rule.
- **Numbers:** accept 100k to 1M events/s in total if justified. Flag billions per second.

### C8. Failed subscription payments

- **Say:** "Design how we handle failed subscription payments."
- **Product context:** about 200M active subscriptions. Renewals bunch up on the 1st of the month, and a slice of them fail on expired cards or insufficient funds.
- **Hidden constraints:**
  1. Retries spread over about 2 weeks, by default about 8 attempts, at chosen times. **Trigger:** an immediate retry loop.
  2. Banks push new card details when a card is reissued, so retry with the updated card. **Trigger:** "just email the customer".
  3. The merchant configures what happens to the subscription (past due, then canceled or unpaid), and gates access through webhooks. **Trigger:** ignoring the subscription state.
- **Crux:** a long-lived retry state machine per invoice, across a start-of-month spike, never charging twice.
- **Good cuts:** the retry-timing model internals, email templates, tax.
- **Wrong cut:** the subscription outcome.
- **Numbers:** if 30% renew on the 1st, that is ~60M renewals in a day, ~700/s. Assume a 5 to 10% failure rate.

### C9. Saved cards

- **Say:** "Design saving customers' cards so they can pay again later."
- **Product context:** merchants want returning customers to pay in one click.
- **Hidden constraints:**
  1. Merchant servers must never see the card number (PCI scope). The card is typed into our iframe, and the merchant gets a token. **Trigger:** a merchant backend sending card numbers.
  2. Cards expire or get reissued. Network updates keep a saved card working. **Trigger:** treating the card number as static.
  3. Merchants want to spot the same card on two customers without ever seeing the number. **Trigger:** any dedup discussion.
- **Crux:** a tiny, high-security vault holding raw card numbers, with everything else working on tokens.
- **Good cuts:** 3DS, wallets, fraud, UI.
- **Wrong cut:** the PCI boundary.
- **Numbers:** hundreds of millions of saved cards. Vault reads only at charge time, ~1k/s.

### C10. Test environment

- **Say:** "Design a test environment where developers can try our API without moving real money."
- **Product context:** every developer builds against test mode before going live.
- **Hidden constraints:**
  1. It must behave exactly like live: same API, versions, webhooks and errors, but never touch card networks. Special test card numbers trigger outcomes such as a decline or a 3DS challenge. **Trigger:** a separate, simplified mock service.
  2. Developers test monthly renewals without waiting a month, so time must be simulated. **Trigger:** asking about time-based features.
  3. Test traffic must never affect live data, limits or availability. Some customers load-test against it. **Trigger:** sharing infrastructure without isolation.
- **Crux:** the same code path as live, with the money-moving edges swapped for simulators, plus simulated time.
- **Good cuts:** test-data generation UI, sharing a sandbox between teammates.
- **Wrong cut:** isolation from live.
- **Numbers:** the sandbox limit is 25 req/s per account (docs), against 100 in live.

### C11. Payout reconciliation reports

- **Say:** "Design reports that let merchants reconcile their payouts with their bank statement."
- **Product context:** merchant finance teams close their books every month.
- **Hidden constraints:**
  1. Every bank deposit must tie, to the cent, to the payments, refunds, fees and disputes inside it. **Trigger:** a report built by querying API objects by date.
  2. Large merchants have tens of millions of transactions a month. Reports run asynchronously and download as files. **Trigger:** synchronous queries.
  3. A closed period is never rewritten. A dispute weeks later shows up in a later period. **Trigger:** regenerating historical reports.
- **Crux:** reports derived from the ledger, with immutable periods that tie each payout to its parts.
- **Good cuts:** charts, custom SQL, accounting-software integrations.
- **Wrong cut:** the link from a payout to its transactions.
- **Numbers:** 5B ledger events a day.

### C12. Local-currency pricing

- **Say:** "Let merchants show prices in the customer's local currency."
- **Product context:** a US merchant sells to customers in Japan in yen and gets settled in dollars.
- **Hidden constraints:**
  1. The rate shown must be the rate charged, while FX moves as the customer shops. A quote is locked for a period. **Trigger:** converting at charge time.
  2. A refund weeks later returns the same yen amount to the customer. Someone bears the FX difference. **Trigger:** refunds, or asking about refunds.
  3. Currencies have different minor units: yen has none, some have three. Store amounts as integers in the smallest unit. **Trigger:** floats or a fixed 2 decimals.
- **Crux:** who bears FX risk between quote, charge, refund and settlement, and locking and recording the rate.
- **Good cuts:** FX hedging, tax, price-rounding UI.
- **Wrong cut:** the refund rate rule.
- **Numbers:** 135+ currencies.

### C13. In-person card payments

- **Say:** "Design in-person card payments for merchants' card readers in stores."
- **Product context:** cafes and retailers take card payments at the counter with our readers and a point-of-sale app.
- **Hidden constraints:**
  1. When the store's internet goes down, the store must keep selling. The reader stores payments and forwards them later. A forwarded payment can be declined, the merchant bears that loss, and the merchant sets offline limits. **Trigger:** assuming the reader is always online.
  2. Each stored payment is forwarded exactly once, even if the reader reboots or retries. **Trigger:** forwarding without dedup, or any talk of retries.
  3. Tap to approved takes about 2 s at the counter. Card data is encrypted inside the reader, so the point-of-sale app never sees it. **Trigger:** card data routed through the app or the merchant's server.
- **Crux:** offline store-and-forward with bounded risk and exactly-once forwarding.
- **Good cuts:** reader hardware, fleet software updates, tipping UI, receipts.
- **Wrong cut:** offline mode, once it has been raised. A store that stops selling when Wi-Fi drops is the failure the product exists to prevent.
- **Numbers:** hundreds of thousands of readers. A few hundred payments/s in total, peaking at lunch and on holidays.

### C14. Local payment methods

- **Say:** "Add local payment methods from around the world to our payments API."
- **Product context:** outside the US, many customers don't pay by card. Examples: bank redirects in the Netherlands, cash vouchers in Mexico and Brazil, direct debit in Europe.
- **Hidden constraints:**
  1. Some methods finish days later. A customer pays a cash voucher at a store within a few days, or never. **Trigger:** a synchronous result.
  2. Redirect methods send the customer to their bank's site, and the customer may never come back. **Trigger:** one API call per payment.
  3. Direct debits can be reversed by the customer weeks after they "succeeded". Some methods don't support refunds or partial refunds. **Trigger:** treating success as final, or assuming every method refunds the same way.
- **Crux:** one payment state machine that covers instant, redirect and days-later methods, with each method's capabilities declared as data.
- **Good cuts:** per-provider integration details, FX, per-method UI, fraud.
- **Wrong cut:** the "pending for days" state.
- **Numbers:** about 125 payment methods. Cards are most of the volume, but local methods decide whether a merchant can sell in a country at all.

### C15. Marketplace split payments

- **Say:** "Let marketplaces split a customer's payment between the platform and its sellers."
- **Product context:** a marketplace takes one payment at checkout, keeps a fee and pays each seller their share.
- **Hidden constraints:**
  1. One order can contain items from three sellers. Each seller is paid separately, and the platform keeps a fee. **Trigger:** one payment to one seller.
  2. A refund or dispute after the sellers were paid must claw back from the right seller, even if that seller's balance is empty. Someone bears the loss: the platform or the seller. **Trigger:** treating a refund as a simple reversal of the charge.
  3. Sellers are in different countries and get paid on their own schedules, in their own currency. **Trigger:** a single payout path.
- **Crux:** fanning one payment out to N balances with later reversals, and an explicit rule for who bears losses.
- **Good cuts:** seller onboarding, tax, the platform's UI.
- **Wrong cut:** reversals after payout.
- **Numbers:** ~1k payments/s across all of Stripe. Marketplaces are a slice. Up to 10 sellers per order is a fine assumption.

### C16. Seller onboarding for platforms

- **Say:** "Design how platforms onboard and verify their sellers so the sellers can get paid."
- **Product context:** a platform like a booking or delivery app signs up thousands of small sellers. We must verify each one before money moves to them.
- **Hidden constraints:**
  1. Required information differs by country and business type, and it changes when regulations change. Existing sellers then get new requirements with a deadline. **Trigger:** a hard-coded onboarding form.
  2. A seller can start taking payments before full verification. Payouts stay paused until they are verified. **Trigger:** all-or-nothing approval.
  3. Some platforms build their own onboarding UI on our API, so requirements must be exposed as data, not as a page. **Trigger:** assuming a hosted form only.
- **Crux:** verification requirements as versioned data per country, gating separate capabilities (charges vs payouts), with deadlines for existing accounts.
- **Good cuts:** document OCR, the sanctions-screening model, the platform's UI.
- **Wrong cut:** requirement changes for existing sellers. That is the long-lived part.
- **Numbers:** millions of connected accounts. Account creation is capped at 30/s per platform in live mode.

### C17. Merchant fee calculation

- **Say:** "Design how we calculate the fees we charge merchants."
- **Product context:** every payment has a fee deducted before the money reaches the merchant's balance.
- **Hidden constraints:**
  1. Pricing varies by card type, country, cross-border use and currency conversion. Large merchants have negotiated rates, and some pay the actual card-network cost plus a margin. **Trigger:** a single fee formula.
  2. For cost-plus pricing, the real network cost is known only days later, at settlement. The balance needs a fee at payment time. **Trigger:** computing the final fee at payment time.
  3. Price changes take effect on a date. A refund months later uses the price that applied to the original payment. **Trigger:** looking fees up in the current price table.
- **Crux:** a fee computed with incomplete information at payment time and trued up later, against versioned price plans.
- **Good cuts:** sales quoting tools, fee invoices, tax on fees.
- **Wrong cut:** the true-up.
- **Numbers:** one fee per payment, ~1k/s average, 2.5k/s peak.

### C18. Sales tax at checkout

- **Say:** "Calculate sales tax for merchants at checkout."
- **Product context:** merchants selling across US states and abroad don't want to track tax rules themselves.
- **Hidden constraints:**
  1. A merchant has to collect tax in a US state only after crossing that state's sales threshold. Rates change many times a year across thousands of jurisdictions. **Trigger:** a simple rate table by country.
  2. The calculation runs inline at checkout, in under about 100 ms. Checkout must not fail when tax is slow. **Trigger:** a synchronous call with no fallback.
  3. The exact rule and rate used are recorded per transaction for audits years later. Refunds reverse tax in proportion. **Trigger:** recomputing tax at report time.
- **Crux:** point-in-time correct rules on the hot path, plus a record of what was applied.
- **Good cuts:** filing returns with governments, product-taxability models, UI.
- **Wrong cut:** the recorded calculation, which is the audit trail.
- **Numbers:** up to the checkout rate, ~1k/s average, 2.5k/s peak.

### C19. Subscription plan changes

- **Say:** "Let customers upgrade or downgrade their subscription mid-cycle."
- **Product context:** a SaaS customer moves from the Basic plan to Pro on day 12 of a monthly cycle.
- **Hidden constraints:**
  1. An upgrade charges the difference, prorated to the second. A downgrade becomes a credit on the next invoice. **Trigger:** changes only at period end.
  2. The invoice preview shown before the customer confirms must equal the final invoice exactly. **Trigger:** a separate or approximate preview calculation.
  3. Changes can be scheduled for future dates and can stack within one cycle, together with trials and coupons. **Trigger:** a single "current plan" field.
- **Crux:** billing computed deterministically from a versioned subscription timeline, so the preview equals the final invoice and a replay gives the same answer.
- **Good cuts:** tax, payment collection, pricing UI.
- **Wrong cut:** preview consistency.
- **Numbers:** 200M subscriptions. Plan changes are a small fraction, tens per second.

### C20. Business bank transfers

- **Say:** "Let merchants accept bank transfers from their business customers."
- **Product context:** a B2B software company invoices customers, who pay by wire or ACH instead of by card.
- **Hidden constraints:**
  1. Customers send transfers with a missing or wrong reference, so you cannot tell which invoice is being paid. A virtual account number per customer at least tells you who paid. **Trigger:** matching on the reference only.
  2. Partial payments, overpayments, and one transfer covering several invoices. **Trigger:** one transfer equals one invoice.
  3. Transfers arrive in bank files a few times a day, sometimes days late, and some get returned. **Trigger:** assuming real time.
- **Crux:** reconciling incoming money with unreliable references against open invoices, with a customer balance for leftovers.
- **Good cuts:** FX, the manual-review UI, refunds by bank transfer.
- **Wrong cut:** handling unmatched and partial funds.
- **Numbers:** few transfers, large amounts. Tens of thousands a day.

### C21. Merchant loans repaid from sales

- **Say:** "Design loans for merchants that are repaid automatically from their sales."
- **Product context:** a merchant gets a cash advance based on their sales history on our platform.
- **Hidden constraints:**
  1. Repayment is a fixed percentage withheld from each day's sales before payout, not a monthly bill. **Trigger:** a monthly instalment.
  2. Offers are computed from processing history and refreshed as sales change. Lending is regulated and runs through a partner bank. **Trigger:** static eligibility.
  3. If sales drop or the merchant leaves, the loan still exists, and there is a minimum repayment per period. Refunds and disputes interact with withholding. **Trigger:** withholding as the only repayment path.
- **Crux:** loan state wired into the money flow, so withholding from payouts stays correct when flows reverse.
- **Good cuts:** underwriting model internals, collections, offer marketing.
- **Wrong cut:** withholding from payouts. That is how the product works.
- **Numbers:** low QPS. One withholding per merchant per payout.

### C22. API request logs for developers

- **Say:** "Let developers see and search every API request their account made."
- **Product context:** developers debug their integration by finding the failing request and seeing exactly what was sent and returned.
- **Hidden constraints:**
  1. Requests contain card numbers, secrets and personal data, so logs are redacted before storage. **Trigger:** storing raw request bodies.
  2. Developers mostly look at the last few days, by request id, idempotency key, endpoint or error. Retention is limited. **Trigger:** indexing everything forever in an OLTP database.
  3. A developer must see a failed request within seconds while debugging. **Trigger:** an hourly batch.
- **Crux:** write-heavy ingest with redaction, plus cheap, per-account, recent-first search.
- **Good cuts:** analytics dashboards, anomaly detection, log export.
- **Wrong cut:** redaction.
- **Numbers:** 27k req/s peak x ~5 KB is ~135 MB/s. About 2.5 TB/day at the ~6k/s average.

---

## Part C. General Staff prompts (6, constructed)

Not fintech. Use them for variety, or after the Stripe round. None is in `hld/`.

### G1. Code deployment system

- **Say:** "Design a code deployment system."
- **Product context:** about 2,000 engineers ship about 500 deploys a day to 10k hosts in 3 regions.
- **Hidden constraints:**
  1. A bad deploy must roll back in under 5 minutes, everywhere. **Trigger:** rollback as "deploy the old version again" at normal speed.
  2. Rollouts go in waves (canary, one region, all), and a wave is promoted only if health metrics hold. **Trigger:** push to all hosts at once.
  3. During an incident, deploys freeze except for the fix. **Trigger:** no freeze or override path.
- **Crux:** a safe progressive rollout with automatic, fast rollback. Distributing the artifact to 10k hosts quickly is the second-hardest part.
- **Good cuts:** the CI build, code review, secrets management.
- **Wrong cut:** automatic rollback.
- **Numbers:** a 500 MB artifact to 10k hosts is 5 TB per deploy, so peer-to-peer or regional caches.

### G2. Distributed tracing

- **Say:** "Design a distributed tracing system."
- **Product context:** 500 microservices. Engineers need to see why one request was slow.
- **Hidden constraints:**
  1. Keeping 100% of traces is too expensive, but the slow and failed ones must be kept. **Trigger:** head sampling at a fixed rate.
  2. Spans from one trace arrive from many services, out of order and late. **Trigger:** assuming one trace arrives together.
  3. Seven days of retention, and search by service, latency and error. **Trigger:** keeping everything forever.
- **Crux:** the keep-or-drop decision needs the whole trace, but the trace is spread across services. That is tail-based sampling.
- **Good cuts:** the UI, metrics derived from spans, client SDKs.
- **Wrong cut:** sampling policy.
- **Numbers:** about 1M spans/s at ~500 B is ~500 MB/s before sampling.

### G3. Web crawler

- **Say:** "Design a web crawler."
- **Product context:** it feeds a search index of about 5B pages.
- **Hidden constraints:**
  1. Politeness: at most one request every few seconds per host, and robots.txt is obeyed. **Trigger:** a global queue with workers grabbing any URL.
  2. Duplicates: the same page under many URLs, plus near-duplicate content. **Trigger:** dedup by URL only.
  3. Freshness differs by site: news hourly, static pages monthly. **Trigger:** one recrawl interval.
- **Crux:** scheduling the URL frontier per host, for politeness and freshness, at billions of URLs.
- **Good cuts:** indexing and ranking, JavaScript rendering, the content store format.
- **Wrong cut:** politeness. Without it you get blocked or take sites down.
- **Numbers:** 5B pages a month is ~2k pages/s.

### G4. Calendar with meeting invites

- **Say:** "Design a calendar with meeting invites."
- **Product context:** a work calendar for companies of up to 100k people.
- **Hidden constraints:**
  1. Recurring meetings have exceptions ("move just this Tuesday"), and they recur in the organizer's time zone across daylight-saving changes. **Trigger:** storing each occurrence, or using UTC only.
  2. You can see colleagues' free/busy status but not their event details. **Trigger:** sharing full events.
  3. Invites go to people outside the company by email, and their replies come back by email. **Trigger:** internal users only.
- **Crux:** a recurrence model with exceptions, plus fast free/busy queries across many people.
- **Good cuts:** room booking, reminders, the mobile app.
- **Wrong cut:** recurrence exceptions.
- **Numbers:** 100k users and about 20 events each per week. A low write rate. Free/busy reads dominate.

### G5. Online coding judge

- **Say:** "Design an online coding judge."
- **Product context:** users submit code and get a pass or fail against hidden tests. Weekly contests.
- **Hidden constraints:**
  1. The submitted code is untrusted. It can try to read the tests, the network or other users' code. **Trigger:** running code in a plain container next to other jobs.
  2. Contest start brings 50x normal traffic within a minute. **Trigger:** sizing for the average.
  3. Results must be fair: equal CPU time, and no queue-jumping during a contest. **Trigger:** best-effort shared workers.
- **Crux:** strongly isolated execution under a predictable contest spike.
- **Good cuts:** the editor UI, plagiarism detection, the problem authoring tools.
- **Wrong cut:** the sandbox.
- **Numbers:** 100 submissions/s normally, 5k/s at contest start. Each run takes about 2 s of CPU.

### G6. Game leaderboard

- **Say:** "Design a leaderboard for a mobile game."
- **Product context:** 100M players. Weekly seasons.
- **Hidden constraints:**
  1. Every player sees the global top 100 and their own exact rank. **Trigger:** top 100 only, or an approximate rank.
  2. Seasons reset weekly, and past seasons stay viewable. **Trigger:** a single all-time board.
  3. Cheaters are removed after the fact, and every rank below them shifts. **Trigger:** append-only scores.
- **Crux:** an exact rank for any player at 100M scale. Decide whether to keep it exact or to make it exact only near the top.
- **Good cuts:** the friends leaderboard, rewards payout, anti-cheat detection.
- **Wrong cut:** "my rank".
- **Numbers:** 10k score updates/s and 50k rank reads/s at peak.

---

## Part D. Reported prompts, round 2 (8)

Found by the desktop research (2026-10-09). The prompts are reported. Unless a source says otherwise, the hidden constraints are constructed.

### D1. Internal authorization redesign

- **Say:** "Redesign our internal authorization system across services."
- **Source:** Stripe. The [Aced Stripe guide](https://www.aced.io/blog/stripe-system-design-interview) calls it one interviewer's staple. Secondhand. If the candidate builds `hld/authorization-service/` (#30), retire this card.
- **Product context:** hundreds of internal services each check permissions their own way, with hard-coded role checks and per-service tables. Support agents, engineers and batch jobs all touch merchant data. Rules are inconsistent, access changes take days, and auditors ask who accessed which merchant's data.
- **Hidden constraints:**
  1. A permission check sits on the request path of every internal call. It must add under ~5 ms p99, and the auth system must not become a single point of failure. **Trigger:** a central service called synchronously, with no local decision or fallback.
  2. Revocation (an employee leaves, or a credential leaks) must take effect everywhere within a minute. **Trigger:** caches or tokens that live for hours.
  3. Hundreds of services cannot switch at once. Old and new run side by side, and the new system runs in shadow mode, comparing decisions, before it enforces anything. **Trigger:** a big-bang cutover.
- **Crux:** one central policy model with decisions made locally on the request path, fast revocation, and an incremental rollout behind shadow mode.
- **Good cuts:** the identity provider and SSO, the policy-authoring UI, merchant-facing dashboard roles.
- **Wrong cut:** migration. The verb is "redesign", so a running system exists.
- **Numbers:** internal calls run several times the external 27k req/s peak. Accept 50k to 500k checks/s.

### D2. URL shortener

- **Say:** "Design a URL shortener."
- **Source:** Stripe, [Blind, Apr 2025](https://www.teamblind.com/post/stripe-system-design-interview-questions-qsbyrhsz). The Stripe twist here is constructed.
- **Product context (give if asked who uses it):** merchants share short links to payment pages and invoices over SMS, email and social posts.
- **Hidden constraints:**
  1. The links point at payment pages and invoices, so they are a phishing and enumeration target. With sequential or very short codes, anyone can walk every merchant's links and see names and amounts. **Trigger:** counter-based or short IDs.
  2. A merchant must be able to disable a link instantly (sold out, or fraud), and the redirect must stop everywhere within seconds. **Trigger:** permanent 301 redirects or long CDN caching.
  3. Merchants can use their own domain, with TLS. **Trigger:** one shared domain assumed.
- **Crux:** unguessable IDs and fast disable for links that point at money. Raw redirect throughput is what the textbook answer optimizes, and it is the wrong target here.
- **Good cuts:** click analytics, QR codes, the link-management UI.
- **Wrong cut:** abuse and enumeration.
- **Numbers:** a few thousand redirects/s at peak, with viral spikes on single links. Low create rate. Flag 100k+ writes/s or billions of links a day.

### D3. E-commerce system

- **Say:** "Design an e-commerce system."
- **Source:** Stripe SWE, San Francisco, Mar 2025, [Taro](https://www.jointaro.com/interviews/companies/stripe/experiences/software-engineer-san-francisco-ca-march-21-2025-no-offer-positive-83c574db/), firsthand. The card is constructed.
- **If asked which part:** "You pick. Tell me why." The strong pick is checkout and order placement, where inventory, payment and the order meet. A weak pick is catalog browsing (a read-heavy cache problem with no money in it). Ask "why that part?" if they pick it.
- **Product context:** a mid-size online store with 50k products and occasional flash sales.
- **Hidden constraints (for the checkout pick):**
  1. A flash sale puts 10k buyers on 500 units within a minute. Never oversell, and don't hold stock forever for abandoned carts. **Trigger:** decrementing stock at add-to-cart, or only after payment with no reservation.
  2. Payment is an external call. It can time out, or pause for minutes on a 3DS challenge. Never charge twice, and never charge without an order. **Trigger:** "charge, then create the order" as one synchronous step.
  3. Fulfilment ships from a warehouse system we don't own. It consumes order events and may see duplicates. **Trigger:** calling the warehouse synchronously from the order service.
- **Crux:** a checkout flow across stock reservation, an external payment with an unknown outcome, and fulfilment. The invariants: never oversell, never double-charge.
- **Good cuts:** search, recommendations, reviews, catalog management, shipping rates.
- **Wrong cut:** payment failure handling. At Stripe, that is the point.
- **Numbers:** ~50 orders/s normally. ~2k checkouts/s in a flash sale, all on a few products (a hot key).

### D4. A mobile feature with a little server support

- **Say:** "Design a mobile feature that needs a little bit of server support."
- **Source:** Google Staff, Bangalore, [LeetCode](https://leetcode.com/discuss/post/1173438/google-staff-engineer-bangalore-reject-b-h1co/), firsthand. That candidate was rejected for not clarifying. The card is constructed.
- **If asked which feature:** "You choose." Grade whether the candidate proposes a concrete feature quickly and defines what "a little server support" means. If they stall for two exchanges, offer: "Say, splitting a restaurant bill with friends: scan the receipt, assign items, everyone sees what they owe."
- **Hidden constraints (for the bill-splitting default):**
  1. Some friends don't have the app. They get an SMS link and must see and settle their share in a browser. **Trigger:** assuming every participant is an app user.
  2. Two people edit the same bill offline at the table, because restaurant signal is bad. Totals must reconcile, and nobody's share changes silently after they've paid. **Trigger:** last-write-wins, or ignoring offline.
  3. "A little server support" means a small team. No custom real-time infrastructure. Use push notifications and a simple API, and run receipt OCR on the phone. **Trigger:** a heavy distributed backend.
- **Crux:** picking the feature and keeping the server thin. Then a bill that stays consistent across devices that edit offline.
- **Good cuts:** payments between friends, group history, receipt OCR quality.
- **Wrong cut:** offline edits.
- **Numbers:** about 5M users and a few bills a week each. Tens of writes per second.

### D5. Blob storage for a lunar base

- **Say:** "Design a blob storage system for a lunar base."
- **Source:** Coinbase SWE, Dec 2025, [PracHub](https://prachub.com/companies/coinbase/categories/system-design), summary only. The card is constructed.
- **Product context:** a research base on the Moon produces camera footage, sensor data and science files. The crew reads and writes locally. Scientists on Earth need the data.
- **Hidden constraints:**
  1. Earth is about 1.3 s away one way. The link is up only in windows, about 6 hours a day, at about 50 Mbps. **Trigger:** synchronous replication to Earth, or local reads that depend on Earth.
  2. Hardware cannot be replaced for months. Disks fail, and radiation flips bits. **Trigger:** assuming failed nodes are swapped quickly, or no checksums and scrubbing.
  3. The base makes about 1 TB a day, but the link moves about 135 GB a day. Something decides what goes down first and what gets dropped. **Trigger:** "send everything to Earth".
- **Crux:** a local-first store that survives on its own (erasure coding, checksums, scrubbing), plus prioritized, resumable sync over a slow link that comes and goes.
- **Good cuts:** auth details, Earth-side analytics, a UI.
- **Wrong cut:** the link model. The Moon is the whole problem.
- **Numbers:** 50 Mbps x 6 h is ~135 GB/day, about 13% of what the base generates.

### D6. Message and thread deletion in group chat

- **Say:** "Design message and thread deletion for a group chat service."
- **Source:** Databricks Senior+, Jul 2026, [PracHub](https://prachub.com/companies/databricks/categories/system-design), summary only. The card is constructed.
- **Product context:** an existing Slack-like chat. Users delete their own messages, and admins can delete any message.
- **Hidden constraints:**
  1. A deleted message must vanish from every copy: members' devices (including ones offline for days), the search index, push-notification previews and link unfurls. **Trigger:** deleting the row in the messages table and stopping there.
  2. Deleting a parent with 500 replies leaves a "message deleted" placeholder, and the replies stay unless an admin deletes the whole thread. **Trigger:** assuming a cascade delete, or asking what happens to replies.
  3. Some workspaces are under legal hold: a user's delete hides the message, but compliance keeps it for years. Others need a hard delete within 30 days. **Trigger:** one delete semantics for everyone.
- **Crux:** deletion as a propagated tombstone that reaches every copy, with different meanings for user delete, admin delete and retention.
- **Good cuts:** edit history, the send path, search ranking.
- **Wrong cut:** offline clients and derived copies.
- **Numbers:** 1B messages sent a day. About 1% deleted is ~10M/day, ~115/s, each fanned out to every member of the channel.

### D7. Real-time asset price service

- **Say:** "Design a real-time asset price service."
- **Source:** Coinbase Backend Senior+, Jun 2026, [PracHub](https://prachub.com/companies/coinbase/categories/system-design). The summary says the service grows from one upstream provider to several. The rest is constructed.
- **Product context:** the app shows live prices for ~500 crypto assets. The same prices feed trading quotes.
- **Hidden constraints:**
  1. Today there is one upstream provider. Four more are coming next quarter, and providers disagree: one is often stale or wrong. **Trigger:** a design wired to one source. Good as the minute-8 probe if not surfaced.
  2. There are two consumers. Display prices for app users can be slightly stale. Trade quotes must be fresh, and a price older than ~1 s is rejected, because a stale quote loses money. **Trigger:** one freshness rule for both.
  3. 10M users are connected, and popular assets tick many times a second. Each user needs only the assets on screen, at a few updates a second. **Trigger:** pushing every tick to every client.
- **Crux:** turning disagreeing sources into one trusted price, then fanning it out to millions with different freshness rules per consumer.
- **Good cuts:** historical charts, price alerts, order execution.
- **Wrong cut:** multi-source aggregation.
- **Numbers:** 500 assets x ~10 ticks/s per source is ~5k ticks/s in. Going out, 10M clients x ~2 updates/s is ~20M messages/s, so edge fan-out.

### D8. Package-tracking widget in an email inbox

- **Say:** "Design a package-tracking widget for an email inbox."
- **Source:** Rippling Senior+, Aug 2026, [PracHub](https://prachub.com/companies/rippling?amp%3Bcategory=System+Design), summary only. The card is constructed.
- **Product context:** an email client shows a card at the top of shipping-confirmation emails: carrier, status and ETA, kept up to date.
- **Hidden constraints:**
  1. Tracking numbers come from parsing the emails of thousands of retailers. Email content is private, so parsing happens inside the mail system's privacy boundary, and only the tracking number leaves it. **Trigger:** sending email bodies to a separate service or a third party.
  2. Carrier APIs are rate-limited. Some carriers offer webhooks and some only allow polling. There are 100M active shipments. **Trigger:** polling every package every few minutes.
  3. Users rarely reopen the email. The status must be fresh when they do, and a push goes out on "out for delivery" and "delivered". **Trigger:** updating only when viewed, or polling everything at one fixed rate.
- **Crux:** keeping 100M shipments fresh within carrier rate limits, using webhooks plus adaptive polling, with extraction kept inside the privacy boundary.
- **Good cuts:** retailer partnerships, a map view, returns.
- **Wrong cut:** carrier rate limits.
- **Numbers:** 100M shipments refreshed every 2 hours is ~14k carrier calls/s, which is over most carriers' limits. That forces the adaptive design.
