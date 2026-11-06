# 1. Payment authorization and capture

**Timebox:** 50 to 60 minutes. Implement a small in-memory payment service. Use integer minor units for amounts.

## Stage 1: Core lifecycle

Build operations to create a payment, authorize it, capture it, and cancel it. A payment has an ID, amount, currency, and status.

Rules:

- Amount must be positive. Currency is a three-letter code.
- A capture can only happen after authorization. For this stage, allow one capture for the full authorized amount.
- A payment cannot be captured after cancellation, or canceled after capture.
- Invalid transitions return a clear error and leave the payment unchanged.

Before coding, ask which statuses and error behavior the caller needs. State any assumptions you make.

## Stage 2: Partial capture and request retries

Add partial capture. A payment may have more than one capture, but the sum of captures must not exceed the authorized amount.

Add an idempotency key to mutating operations:

- Retrying the same key and same request returns the original result without applying the operation twice.
- Reusing a key with a different request is an error.

Keep Stage 1 behavior working.

## Stage 3: External processor uncertainty

Assume the processor may accept a capture and then time out before your service receives the response. Explain and model how a retry avoids charging twice. You may implement the state change, or describe the smallest interface and state needed to make the behavior safe.

## Interviewer follow-ups

- Two capture requests race when only enough authorization remains for one. Where is the invariant enforced?
- What should a caller see if the processor response is unknown?
- Which data is source of truth, and what would you reconcile?
- Which part would you keep in the domain model, and which part belongs behind an interface?
