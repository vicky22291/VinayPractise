# Subscription proration design

## Stage 1: pure calculation

`ProrationController` maps the JSON contract to `ProrationCalculator`. `Plan`, `PlanChange` and `Proration` are immutable domain values. The calculator has no repository or clock: all time and price inputs are explicit, so identical requests give identical results.

All prices are nonnegative integer minor units for one common full period and currency. Quantities are positive; a zero-priced plan is supported. Currency is a normalized three-letter code. Time is `Instant`, so offset timestamps resolve to UTC instants. The period and every plan interval are start-inclusive/end-exclusive. A change must satisfy `start <= change < end`. The end time itself is rejected, per the prompt's exclusive boundary. A new period should handle a change at that boundary.

For one change, the signed adjustment is `(new price - old price) * remaining duration / period duration`. Round only the final adjustment with HALF_UP, including negative ties away from zero. Zero-duration and reversed periods are invalid.

## Stage 2: quantities and several changes

The initial plan is the already billed baseline for the entire period. Changes are replacement plans (unit price and quantity), supplied in strictly increasing order. Duplicate timestamps and unsorted changes are rejected. A change at the period start is valid and produces no empty initial interval. An empty change list produces zero adjustment.

Build adjacent intervals from period start through every change to period end. For each interval, compare its full-period `price * quantity` to the initial baseline, weight that difference by the interval duration, and add the exact results. This is equivalent to summing each change's incremental difference weighted by its remaining duration. Comparing every interval to the same baseline prevents double-counting already billed time.

Arithmetic uses `BigInteger` numerators and a common denominator, retaining all precision until the single final minor-unit rounding. Duration is proportional to seconds, represented exactly as integer nanoseconds to avoid losing fractional seconds. Multiplying large prices by quantities cannot overflow an intermediate `long`; a final adjustment outside `long` range is rejected. The result includes each interval's numerator and the shared denominator for inspection. Do not round individual returned interval fractions independently.

DST and leap days require no local-time conversion here: UTC durations reflect actual elapsed time. A product that bills by calendar day needs a separate policy and an agreed billing timezone; it can produce different charges around DST or unequal month lengths. Leap seconds are not separately modeled by Java `Instant`.

## Stage 3: implemented discount and invoice discussion

The implemented extension is a **uniform percentage discount**, expressed in basis points: 1000 means 10%, 10000 means free. The same discount applies to both the originally billed baseline and every replacement plan. Multiply the exact net adjustment by `(10000 - discountBasisPoints) / 10000` before the single final rounding. This preserves credit signs and avoids rounding drift. Zero discount reproduces stages one and two. Fixed coupons, discount caps, different old/new discounts and tax are not modeled by this extension.

An invoice adapter would need explicit rules for the other follow-ups:

- **Discounts that change mid-period:** retain the effective discount with each historical interval; credit the actual discounted amount previously billed, rather than today's list price.
- **Tax:** determine jurisdiction, tax-inclusive vs exclusive prices and discount ordering. Calculate tax using the invoice's rounding/allocation rules after determining taxable discounted amounts. If line rounding is required, allocate any invoice rounding remainder deterministically; do not independently round every fractional plan interval.
- **Billing-period reset:** close the old period, calculate any old-period unused-time credit under its own denominator, then create a new billing period and full charge. An anchor reset is more than a price replacement in the old period.
- **Draft vs finalized invoice:** attach the adjustment to a draft using a persistent operation ID. After finalization/payment, append a credit note or debit adjustment referencing the original invoice; preserve its historical lines, prices, quantities, discounts and tax instead of editing the paid invoice. Posting that correction must be idempotent even though this pure calculator is stateless.

The calculator deliberately does not store or mutate invoices; the question requests one implemented extension and a discussion of invoice integration. `ProrationCalculatorTest` verifies upgrades, credits, signed ties, boundaries, quantities, exact adjacent intervals, rounding drift, discounts, leap day, fractional seconds and large arithmetic. `ExerciseApiTest` checks the HTTP contract and malformed input.
