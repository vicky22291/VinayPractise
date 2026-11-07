# 4. Webhook delivery service

**Language:** Java. **Timebox:** 50 to 60 minutes. Model event delivery to customer endpoints. Assume handlers may fail or time out.

## Stage 1: Route and deliver

An event has an ID and type. An endpoint subscribes to event types and has a destination. Implement a service that creates a delivery for each matching endpoint and records the outcome of an attempt.

For this stage, define a small delivery state machine and make invalid transitions explicit. Treat a timeout as an unknown outcome rather than proof that the receiver did nothing.
