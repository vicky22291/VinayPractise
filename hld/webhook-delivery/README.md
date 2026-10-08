# Webhook delivery service (Stripe style)

> Status: **todo**. Registered 2026-10-08 so a later session can build the full set. The crux: at-least-once delivery to thousands of merchant endpoints you do not control. One slow or dead endpoint must not delay anyone else, and retries must not become a self-inflicted DDoS. Events carry an id so receivers can drop duplicates, and a signed timestamp so they can reject replays.

Tier 3, problem #58 in [`hld/README.md`](../README.md). **Guide-only for Stripe:** no candidate post names it. DesignGurus lists it among Stripe's "Reported questions" ("a rate limiter, a metrics service, a distributed cache, a webhook delivery service, and a ledger", [DesignGurus](https://www.designgurus.io/blog/stripe-interview-guide)) without a source. It is registered anyway because webhooks are Stripe's own product, and because the same mechanics appear in reported prompts (#32 integration platform for Rippling, the outbox in #57).

Evidence and the rest of the Stripe loop: [`../company-questions.md` §3](../company-questions.md#3-stripe-staff-l4). Related: [`../payments-ledger/`](../payments-ledger/) (idempotency), [`../email-campaign-sending/`](../email-campaign-sending/) (per-destination throttling and reputation), [`../../concepts/rate-limiting-and-load-shedding.md`](../../concepts/rate-limiting-and-load-shedding.md), [`../../concepts/exactly-once.md`](../../concepts/exactly-once.md).

## Problem statement (working version)

There is no verbatim prompt. Working version:

> Design the service that delivers events (`payment_intent.succeeded`, `invoice.paid`, ...) from our platform to the HTTPS endpoints our merchants register. Merchants pick which event types each endpoint receives. Delivery must survive endpoint outages, and merchants must be able to see and replay what was sent.

## What Stripe's own docs say (checked 2026-10-08)

From [docs.stripe.com/webhooks](https://docs.stripe.com/webhooks):
- **Retries:** "Stripe attempts to deliver events to your destination for up to three days with an exponential back off in live mode." Sandbox events are retried "three times over the course of a few hours".
- **No ordering:** "Stripe doesn't guarantee the delivery of events in the order that they're generated."
- **Duplicates happen:** "Webhook endpoints might occasionally receive the same event more than once." Receivers are told to log processed event ids, and to "Track event IDs to identify duplicate deliveries" rather than use `created`.
- **Signatures:** the signature covers a timestamp. "Our libraries have a default tolerance of 5 minutes between the timestamp and the current time."

## Functional requirements

Core:
1. Merchants register endpoints and choose event types per endpoint.
2. Every matching event is delivered to every subscribed endpoint, at least once, signed.
3. Failed deliveries are retried with backoff for up to 3 days, then marked failed. Endpoints that keep failing get disabled, and the merchant is notified.
4. Merchants can see delivery attempts and replay one event or a time range.

Below the line: transforming payloads per merchant, guaranteed ordering, non-HTTP transports (queues, EventBridge), inbound webhooks.

## Non-functional requirements

All numbers are [estimate] until the build session checks them:

| Dimension | Target |
|---|---|
| Scale | ~1 M endpoints. ~500 M deliveries a day, ~5,800 a second on average, ~30k a second at peak [estimate] |
| Latency | First attempt within 5 s of the event, p99, for healthy endpoints [estimate] |
| Isolation | An endpoint that times out after 30 s must not slow delivery to any other endpoint |
| Durability | An accepted event is never silently dropped. Each one ends delivered, failed after 3 days, or skipped because the endpoint is disabled |
| Security | HMAC signature with a timestamp, secret rotation with an overlap, and no SSRF into our own network through a merchant-supplied URL |

## What interviewers probe

1. The event is written to the payments DB, but the publish to the delivery pipeline is lost. How do you make sure it is sent (outbox)?
2. One merchant's endpoint hangs for 30 s on every call. How do you stop it from eating every worker (per-endpoint queues, concurrency caps, circuit breaker)?
3. After a 2-hour outage on our side, 50 M deliveries are due at once. How do you avoid a retry storm against merchants and against ourselves?
4. Receivers see duplicates and out-of-order events. What do you promise, and what do you tell receivers to do?
5. A merchant registers `http://169.254.169.254/...` as an endpoint. What happens?

## Files

| File | What it is |
|---|---|
| `solution.md` | Not written yet |
| `diagrams.md` | Not written yet |
| `edge-cases.md` | Not written yet |
| `deep-dives/` | Planned: outbox and event fan-out, per-endpoint isolation and scheduling, retry policy and storms, signing and secret rotation, SSRF and egress, replay and delivery logs |
| `webhook-delivery.excalidraw` | My drawing. Missing until I draw it |
