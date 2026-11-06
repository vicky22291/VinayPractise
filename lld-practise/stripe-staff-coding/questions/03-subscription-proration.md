# 3. Subscription proration

**Timebox:** 50 to 60 minutes. Implement a pure proration calculator first. Represent money in integer minor units and timestamps in UTC.

## Stage 1: One plan change

Given the current plan price, new plan price, billing-period start and end, and change time, calculate the signed adjustment for the unused part of the billing period.

Use these assumptions unless you ask the interviewer and agree on others:

- Both prices are for the same full billing period and currency.
- Proration is proportional to elapsed seconds, with an inclusive start and exclusive end.
- A positive adjustment is an amount to charge; a negative adjustment is a credit.
- Round the final adjustment to the nearest minor unit, with half units rounded away from zero.
- Reject a change time outside the period or a non-positive period duration.

Example: a 30-day period, changed exactly halfway through, from 2,000 to 3,000 cents produces a +500 cent adjustment.

## Stage 2: Quantities and multiple changes

Add subscription quantity. Then support multiple changes during one period. Define how you avoid losing or double-counting time between adjacent plan intervals. Keep intermediate arithmetic precise and round at a clearly stated boundary.

## Stage 3: Invoice integration discussion

Explain how discounts, tax, a billing-period reset, and a finalized invoice would affect the calculation. Implement only one extension if time permits; keep the calculator's existing behavior stable.

## Interviewer follow-ups

- What happens around daylight-saving changes or leap days?
- Do you prorate by seconds or calendar days, and what product behavior does that imply?
- How do you avoid rounding drift across several line items?
- How would you correct a proration after an invoice was already paid?
