# 4. Webhook delivery service

**Timebox:** 50 to 60 minutes. Model event delivery to customer endpoints. Assume handlers may fail or time out.

## Stage 1: Route and deliver

An event has an ID and type. An endpoint subscribes to event types and has a destination. Implement a service that creates a delivery for each matching endpoint and records the outcome of an attempt.

For this stage, define a small delivery state machine and make invalid transitions explicit. Treat a timeout as an unknown outcome rather than proof that the receiver did nothing.

## Stage 2: Retry

Retry failed or timed-out deliveries using exponential backoff and a maximum attempt count. Make the clock injectable so retry timing can be tested without sleeping. The same event may be delivered more than once, so document what guarantee your sender provides and what the receiver must do.

## Stage 3: Recovery and ordering

Assume workers can crash between selecting a delivery and recording the response. Explain or implement a lease/claim mechanism so work can resume after a worker dies. Decide whether events must be ordered per endpoint; state the throughput and complexity trade-off.

## Interviewer follow-ups

- How do you prevent one failing endpoint from blocking other merchants?
- What identifiers should a receiver use to deduplicate deliveries?
- How would operators replay a delivery safely?
- Which states and metrics would you expose to support teams?
- What is your smallest safe first release, and how would you roll it out?
