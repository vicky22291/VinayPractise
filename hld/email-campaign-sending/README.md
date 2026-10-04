# Mailchimp campaign sending

> One-line answer: a campaign send is a fan-out (one campaign to millions of recipients) that must drain through thousands of **narrow pipes**, one per (sending IP pool, receiving mailbox provider). At send time the audience is frozen into a recipient snapshot, cut into chunks, rendered per recipient (merge tags, a signed one-click unsubscribe link, tracking), and each message is routed to a queue keyed by the recipient's **mailbox provider** (resolved from MX records, so a Google Workspace domain shares Gmail's limits). MTAs (mail transfer agents) pull from those queues under per-pipe connection and rate limits that adapt to what the receiver says: 2xx keeps the rate, 4xx deferrals cut it (AIMD, additive increase multiplicative decrease), block codes pause the pool and page. Reputation is protected by **IP pools** grouped by sender quality, warm-up schedules for new IPs, DKIM signing with the customer's domain, an abuse loop that pauses an account within about a minute of its bounce rate crossing a threshold, and a **canary** for new and risky campaigns (a hashed sample of up to 10k recipients, held up to 2 h and judged on unsubscribes, Yahoo and Microsoft complaints and seed mailboxes, because Gmail reports complaints only daily), so one bad list cannot burn a shared pool. The thing that breaks first is the receiver's patience, not our hardware.

Tier 3, problem #54 in [`hld/README.md`](../README.md). From the user's Intuit Principal / Staff practice list (2026-10). Not a reported candidate prompt. Related: [`../network-throttling/`](../network-throttling/) (rate limiting), [`../credit-score-alerts/`](../credit-score-alerts/) (fan-out), [`../distributed-job-scheduler/`](../distributed-job-scheduler/). Sources: [`research/`](research/).

## Problem statement (as asked)

Mailchimp campaign sending. Crux: per-recipient-domain throttling and deliverability reputation at billions of sends per day.

Follow-ups that always come: a 20 M recipient campaign at 10:00 AM; Gmail deferring one IP pool; a new customer with a purchased list; an unsubscribe in the middle of a send; an MTA crash mid-send; Black Friday at 5x; Apple Mail Privacy Protection and open rates.

## Functional requirements

Core:
- **Send a campaign.** At a scheduled time (or per recipient local time), resolve the audience segment, render a personalized message per recipient, and deliver it.
- **Throttle per receiver.** Never exceed what each mailbox provider accepts from each of our IPs. Adapt to its responses.
- **Protect reputation.** Authenticate every message (SPF, DKIM, DMARC alignment), place senders in IP pools by quality, warm new IPs, and stop abusive senders fast.
- **Close the loop.** Process bounces, deferrals, complaints (feedback loops) and unsubscribes into a suppression list that every future send honors, and report delivery stats to the customer.

Below the line: the campaign editor and templates, audience segmentation queries (we consume a frozen list), automation journeys, transactional email (a separate product with its own pools, mentioned for priority), SMS, inbound mail.

## Non-functional requirements

| Dimension | Target |
|---|---|
| Scale | ~2 B messages/day [estimate] (avg ~23k/s). Sends cluster on round hours in US mornings, so peak ~200k/s for minutes. Largest single campaign ~20 M recipients. Black Friday week designed for 5x a normal day (a ceiling, not a forecast) [estimate] |
| Campaign start | First messages accepted by an MTA within 1 min of the scheduled time. A 20 M campaign fully attempted within ~2 h on a pool sized for it (~20 IPs to Google), unless receivers defer |
| Deliverability | Keep spam complaint rate under 0.1% per sender and never reach 0.3% (Gmail and Yahoo bulk-sender rules). Hard bounces under 2% per send |
| Correctness | One message per (campaign, recipient). An unsubscribe or hard bounce is honored by every later message, under 1 min for new sends. No send to a suppressed address |
| Availability | Scheduling and acceptance 99.95%. Deferred mail retried for up to ~4 days, then bounced |
| Isolation | One customer's bad list cannot hurt others on a shared pool for more than minutes of bounce harm, or more than one canary (~10k messages) of complaint harm |
| Security | Signed unsubscribe links, DKIM private keys wrapped by a KMS (key management service) and decrypted only in signer memory (an HSM per signature would mean ~200k signatures/s at peak), no open relay, customers can only send from domains they verified |

## What interviewers probe (the ladder)

1. A 20 M recipient campaign is scheduled for 10:00 AM. What happens in the first minute, and where is the queueing?
2. Gmail starts answering `421 4.7.28` for one IP pool. What changes, in what order, automatically?
3. A new customer imports a purchased list and 15% bounce. How do you protect everyone else on the shared pool?
4. A recipient clicks unsubscribe at 10:01. The campaign is still sending. Does she get the 10:05 message from the same customer?
5. An MTA crashes after the receiver said 250 OK but before we recorded it. Duplicate, loss, or neither?
6. Black Friday: 5x volume, and receivers do not scale for you. Who waits?
7. Opens are inflated by Apple Mail Privacy Protection. What do you report?

## Files

| File | What it is |
|---|---|
| [`solution.md`](solution.md) | Full HLD in flow-first form: one incremental diagram, one walkthrough per FR, deep dives that mutate the design, then nitty-gritty |
| [`diagrams.md`](diagrams.md) | The D1 to D12 diagram set |
| [`edge-cases.md`](edge-cases.md) | Every "what if" with a 60-second answer and a confidence box |
| [`deep-dives/per-domain-throttling.md`](deep-dives/per-domain-throttling.md) | Provider resolution from MX, per (IP, provider) budgets, AIMD on SMTP replies, global coordination across MTAs |
| [`deep-dives/reputation-and-ip-pools.md`](deep-dives/reputation-and-ip-pools.md) | Shared vs dedicated pools, warm-up, authentication, sender scoring, the abuse loop |
| [`deep-dives/campaign-fan-out-and-scheduling.md`](deep-dives/campaign-fan-out-and-scheduling.md) | Audience snapshot, chunking, rendering, round-hour bursts, send-time optimization, priority |
| [`deep-dives/bounces-complaints-and-suppression.md`](deep-dives/bounces-complaints-and-suppression.md) | Bounce classification, feedback loops, one-click unsubscribe, the suppression list on the hot path |
| [`deep-dives/delivery-semantics-and-mta-failures.md`](deep-dives/delivery-semantics-and-mta-failures.md) | Message ids, the SMTP duplicate window, MTA crash and spool recovery, retry schedule |
| [`research/`](research/) | Raw web research notes with source links. Input to the files above, not study material |
| `email-campaign-sending.excalidraw` | My drawing. Missing until I draw it |
