# Interviewer: reveal one stage at a time

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
