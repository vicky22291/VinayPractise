# 1. Payment authorization and capture

**Language:** Java. **Timebox:** 50 to 60 minutes. Implement a small in-memory payment service. Use integer minor units for amounts.

## Stage 1: Core lifecycle

Build operations to create a payment, authorize it, capture it, and cancel it. A payment has an ID, amount, currency, and status.

Rules:

- Amount must be positive. Currency is a three-letter code.
- A capture can only happen after authorization. For this stage, allow one capture for the full authorized amount.
- A payment cannot be captured after cancellation, or canceled after capture.
- Invalid transitions return a clear error and leave the payment unchanged.

Before coding, ask which statuses and error behavior the caller needs. State any assumptions you make.
