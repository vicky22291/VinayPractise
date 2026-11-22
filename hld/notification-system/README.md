# Notification system: critical and promotional sends at 1M a second

> One-line answer: separate the two kinds of traffic everywhere, not just in a priority field. A critical send (chat message, order event, OTP) is one API call for one user. It is written durably, checked against preferences and expiry, and handed to its own queue, its own workers and its own reserved provider capacity, so it leaves for Apple or Google in under a second. A promotional send is a campaign. It is expanded from a segment into recipient chunks by a scheduler that releases them at a rate we choose, inside quiet hours, frequency caps and the campaign's expiry. Both lanes share one dedup store keyed per (notification, user, channel) with a TTL sized to the type, and both pass the remaining lifetime to the provider so a late message is dropped, not delivered. The red node is provider egress: push provider quotas and connections, not our CPU, bound the 1M a second.

Status: **studied** (solution, diagrams, edge cases, 6 deep dives with runnable simulations, facts survey). Missing: `my-attempt.md` and my excalidraw.

Tier 3, problem #60 in [`hld/README.md`](../README.md). Reported at Coupang for Staff (5 Staff reports on Hello Interview's community board, latest late September 2026), also seen at Merge, Microsoft and others. Related: [`../credit-score-alerts/`](../credit-score-alerts/) (preferences, dedup, delivery scheduler, the app herd after a push), [`../email-campaign-sending/`](../email-campaign-sending/) (the email channel at scale), [`../webhook-delivery/`](../webhook-delivery/) (per-destination isolation, retries, breakers), [`../slack-messaging/`](../slack-messaging/) (push for offline users), [`../distributed-job-scheduler/`](../distributed-job-scheduler/) (scheduled campaigns), [`../../concepts/fan-out-fan-in.md`](../../concepts/fan-out-fan-in.md), [`../../concepts/rate-limiting-and-load-shedding.md`](../../concepts/rate-limiting-and-load-shedding.md), [`../../concepts/exactly-once.md`](../../concepts/exactly-once.md).

## Problem statement (as reported, paraphrased)

Design a notification system that sends to one user or to many users at once. It carries two kinds of message: critical, time-sensitive ones (a 1:1 chat message is the example given) and promotional ones (system-generated recommendations) that can target thousands of users in one send. Plan for up to 1M notifications a second, an expiry rule per notification type, and a roughly 80/20 split between critical and promotional.

Scoping questions to ask in the first 5 minutes:
- **1M a second of what?** API calls or delivered messages? We take it as delivered messages (one user on one channel = one delivery) at peak.
- **80/20 of what?** We take it as 80% of API calls are critical single-user sends and 20% are promotional. Most promotional calls are single-user recommendations (price drop, back in stock), which take the promotional lane because the type, not the API, picks the lane; ~50 campaigns a day of 10^3 to 2 x 10^7 users carry most promotional decisions. Per-user caps (2 a day, 6 a week [estimate]) let at most ~60M promotional pushes leave a day, so critical sends dominate the day; the 1M a second peak is still ~93% promotional, because it is the first big campaign of the day.
- **Which channels?** Push (APNs, FCM), SMS, email, and an in-app inbox.
- **Who calls us?** Internal product services (chat, orders, payments, marketing). No external tenants.

## Functional requirements

Core:
1. **Critical send.** A service sends a notification to one user (chat message, order shipped, payment done, OTP) with a type, a template, an idempotency key and an expiry. We pick channels from the type and the user's preferences and devices.
2. **Promotional send.** Marketing sends a campaign to a segment or a user list (10^3 to 2 x 10^7 users), now or at a scheduled time, with a send window and an expiry.
3. **Preferences and rules.** Users opt out per category and channel and set quiet hours. Every send checks them, plus frequency caps and the legal rules for advertising messages.
4. **Status and inbox.** Each delivery has a status (accepted, suppressed with a reason, sent, delivered, opened, expired, failed, unknown) that callers can query. Users see recent notifications in an in-app inbox.

Below the line: template authoring UI, A/B testing of campaigns, the segment engine itself (we call a segment service that returns user ids), rich media, marketing analytics.

## Non-functional requirements

| Dimension | Target |
|---|---|
| Scale | Peak 1M deliveries a second (given). Critical API calls ~5k a second on average, ~50k at peak [estimate]. Promotional: ~1 B per-user decisions a day, of which caps let at most ~60 M pushes leave, released in bursts up to the peak [estimate] |
| Critical latency | Accepted to handed to the provider, p99 under 1 s, even while a 20M-user campaign is sending. Device delivery after that is the provider's |
| Promotional latency | A campaign finishes inside its send window (default 30 min) at a rate we set. Never early, never after its expiry |
| Expiry | Every notification has `expires_at`. Defaults by type: OTP = code lifetime (3 min), chat 5 min, order status 24 h, promotion = campaign end. We never send after `expires_at`: it is checked at every dequeue and passed to the provider (apns-expiration, FCM ttl, Twilio ValidityPeriod), which drops late copies on a best-effort basis. `expires_at` comes from the caller's `created_at`, so a retry cannot extend it |
| Durability | Inside a region, an accepted critical notification is never silently lost. On region loss the RPO is the cross-region mirror lag (p99 under 2 s), and callers re-send anything without a terminal status from their own outbox with the same idempotency key. A campaign survives a crash and resumes without resending; a bulk sender crash can drop up to ~2.5k in-flight promotional sends (at most once), reported as `unknown` |
| Duplicates | At most one send per (notification, user, channel) inside the type's dedup window, except a resend after a sender crash. Critical sends are at-least-once: a push resend carries the same collapse id and replaces the first (best effort, a dismissed one can reappear), an OTP SMS resend carries the same code, an email resend is a rare visible duplicate. Promotions are at most once at the send hop |
| Availability | Critical send API 99.99%. Campaign path 99.9% |
| Isolation | A slow or failing provider (one SMS vendor, FCM) must not slow any other channel, and promotions must never delay critical sends |
| Provider limits | FCM's default quota is 600k messages a minute per project, ~10k a second, raised in +25% steps that each need 80% usage for 5 minutes first (most handled within ~2 weeks), or for an event through Firebase Support at least 15 days ahead. One Android device takes at most 240 a minute. An SMS short code sends ~100 a second. So 1M a second is a capacity contract with the providers, not just our fleet size ([facts survey](research/facts-survey.md)) |

## What interviewers probe

1. Where does 1M a second actually bind? (Not the API. The fan-out, the device-token reads, and provider quotas and connections.)
2. A 20M-user campaign is mid-send. A chat message must still reach Apple or Google in under a second. How?
3. FCM or the SMS vendor is slow or down for 30 minutes. What queues, what expires, what fails over, and what is dropped?
4. A worker crashes right after the provider accepted the message. How do you avoid a second OTP or a second promotion? What is the dedup key, and how long does it live?
5. A flash sale push goes to 20M users at 10:00. What about the app traffic 2 minutes later, quiet hours, the Korean night-time rule for adverts, and per-user caps?

## Files

[`solution.md`](solution.md) · [`diagrams.md`](diagrams.md) · [`edge-cases.md`](edge-cases.md) · deep dives: [priority lanes and isolation](deep-dives/priority-lanes-and-isolation.md), [campaign fan out and scheduling](deep-dives/campaign-fan-out-and-scheduling.md), [provider egress and quotas](deep-dives/provider-egress-and-quotas.md), [expiry dedup and retries](deep-dives/expiry-dedup-and-retries.md), [preferences and compliance](deep-dives/preferences-and-compliance.md), [status tracking and inbox](deep-dives/status-tracking-and-inbox.md) · research: [facts survey](research/facts-survey.md) · missing: `notification-system.excalidraw` (mine to draw), `my-attempt.md`
