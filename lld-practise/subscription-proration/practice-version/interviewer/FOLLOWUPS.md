# Interviewer: reveal one stage at a time

## Stage 2: Quantities and multiple changes

Add subscription quantity. Then support multiple changes during one period. Define how you avoid losing or double-counting time between adjacent plan intervals. Keep intermediate arithmetic precise and round at a clearly stated boundary.

## Stage 3: Invoice integration discussion

Explain how discounts, tax, a billing-period reset, and a finalized invoice would affect the calculation. Implement only one extension if time permits; keep the calculator's existing behavior stable.

## Interviewer follow-ups

- What happens around daylight-saving changes or leap days?
- Do you prorate by seconds or calendar days, and what product behavior does that imply?
- How do you avoid rounding drift across several line items?
- How would you correct a proration after an invoice was already paid?
