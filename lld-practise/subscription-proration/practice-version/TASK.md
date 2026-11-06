# 3. Subscription proration

**Language:** Java. **Timebox:** 50 to 60 minutes. Implement a pure proration calculator first. Represent money in integer minor units and timestamps in UTC.

## Stage 1: One plan change

Given the current plan price, new plan price, billing-period start and end, and change time, calculate the signed adjustment for the unused part of the billing period.

Use these assumptions unless you ask the interviewer and agree on others:

- Both prices are for the same full billing period and currency.
- Proration is proportional to elapsed seconds, with an inclusive start and exclusive end.
- A positive adjustment is an amount to charge; a negative adjustment is a credit.
- Round the final adjustment to the nearest minor unit, with half units rounded away from zero.
- Reject a change time outside the period or a non-positive period duration.

Example: a 30-day period, changed exactly halfway through, from 2,000 to 3,000 cents produces a +500 cent adjustment.
