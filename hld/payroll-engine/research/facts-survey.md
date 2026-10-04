# Payroll Engine: Facts Survey

**Date**: October 4, 2026
**Scope**: NACHA ACH rules, federal tax deposits, payroll scale at Intuit/Gusto/ADP, idempotency in money movement
**Sources**: NACHA.org, IRS.gov, Federal Reserve, Intuit 10-K, Gusto/ADP/Rippling websites, Stripe/Modern Treasury/Increase docs

---

## Checklist

| Fact | Value | URL | Status |
|------|-------|-----|--------|
| Same Day ACH Window 1 (ET) | Submit 10:30 AM, settle 1:00 PM | https://www.nacha.org/rules/same-day-ach-moving-payments-faster-phase-1 | verified |
| Same Day ACH Window 2 (ET) | Submit 2:45 PM, settle 5:00 PM | https://www.nacha.org/rules/same-day-ach-moving-payments-faster-phase-1 | verified |
| Same Day ACH Window 3 (ET) | Submit 4:45 PM, settle 6:00 PM | https://www.nacha.org/rules/same-day-ach-moving-payments-faster-phase-1 | verified |
| Same Day ACH Window 4 (ET, proposed) | Submit 8:00 PM, settle 10:00 PM; effective Sept 19, 2026 | https://www.nacha.org/rules/same-day-ach-moving-payments-faster-phase-1 | verified |
| Same Day ACH per-transaction limit (current) | $1,000,000 (increased from $100k on March 1, 2022) | https://www.nacha.org/million | verified |
| Same Day ACH per-transaction limit (proposed) | $10,000,000 | https://www.nacha.org/million | verified |
| Standard ACH settlement | 1 business day (next business day); ~80% of all ACH volume | https://www.nacha.org/news/significant-majority-ach-payments-settle-one-business-day-or-less | verified |
| ACH credit forward dating | Same-day, 1 banking day forward, 2 banking days forward (originator option) | https://www.nacha.org/rules/same-day-ach-moving-payments-faster-phase-1 | verified |
| Prenote requirements | Zero-dollar test entry; recommended 3 business days before live entry | https://www.nacha.org/system/files/2023-04/Account-Validation-FAQs-Oct-19-2020.pdf | verified |
| ACH return code R01 | Account overdrawn; valid for future authorized debit and credit entries | https://www.nacha.org/rules/ach-network-risk-and-enforcement-topics | verified |
| ACH return code R02 | Account Closed | https://www.nacha.org/rules/ach-network-risk-and-enforcement-topics | verified |
| ACH return code R03 | No Account / Unable to Locate Account | https://www.nacha.org/rules/ach-network-risk-and-enforcement-topics | verified |
| ACH return code R04 | Invalid Account Number Structure | https://www.nacha.org/rules/ach-network-risk-and-enforcement-topics | verified |
| ACH return code R16 | Account Frozen - Access restricted by RDFI or legal action | https://www.nacha.org/rules/ach-network-risk-and-enforcement-topics | verified |
| ACH return code R29 | Unauthorized transaction (CCD & CTX to non-consumer accounts) | https://www.nacha.org/rules/ach-network-risk-and-enforcement-topics | verified |
| Return timeframe (non-consumer) | 2 banking days from settlement date | https://www.nacha.org/rules/reversals-and-enforcement | verified |
| Return timeframe (consumer) | 60 calendar days from settlement date; requires written statement | https://www.nacha.org/rules/reversals-and-enforcement | verified |
| ACH reversal window | 5 banking days from settlement date | https://www.nacha.org/rules/reversals-and-enforcement | verified |
| Allowed reversal reasons | Originator error (wrong date, amount, account); specific enumerated categories only | https://www.nacha.org/rules/reversals-and-enforcement | verified |
| NACHA file format | Fixed-width ASCII, 94 characters per record | https://achdevguide.nacha.org/ach-file-details | verified |
| Trace number format | 15 characters: ODFI RTN (8) + sequence (7); must be unique within file | https://achdevguide.nacha.org/ach-file-details | verified |
| File ID modifier | Position 34, 1 character; distinguishes multiple files per day; used for duplicate detection | https://achdevguide.nacha.org/ach-file-details | verified |
| ACH record types | Type 1 (File Header), 5 (Batch Header), 6 (Entry Detail), 7 (Addenda), 8 (Batch Trailer), 9 (File Trailer) | https://achdevguide.nacha.org/ach-file-details | verified |
| Semiweekly depositor schedule | Sat/Sun/Mon/Tues paydays → Friday deposit; Wed/Thu/Fri paydays → Wednesday deposit | https://www.irs.gov/pub/irs-pdf/n931.pdf | verified |
| Monthly depositor deadline | 15th of following month (all paydays regardless of frequency) | https://www.irs.gov/pub/irs-pdf/n931.pdf | verified |
| $100k next-day deposit rule | Accumulate $100k+ in tax liability → next business day deposit (any depositor type) | https://www.irs.gov/pub/irs-pdf/n931.pdf | verified |
| Electronic deposit cutoff time (ET) | 8:00 PM day before due date | https://www.irs.gov/pub/irs-pdf/n931.pdf | verified |
| Monthly vs semiweekly threshold | $50k lookback period: <= $50k = monthly, > $50k = semiweekly | https://www.irs.gov/pub/irs-pdf/n931.pdf | verified |
| Form 941 | Quarterly employer federal tax return (wages, withheld taxes, deposits) | https://www.irs.gov/taxtopics/tc757 | verified |
| IRS failure-to-deposit penalty (1-5 days late) | 2% | https://www.irs.gov/payments/failure-to-deposit-penalty | verified |
| IRS failure-to-deposit penalty (6-15 days late) | 5% | https://www.irs.gov/payments/failure-to-deposit-penalty | verified |
| IRS failure-to-deposit penalty (>15 days late) | 10% | https://www.irs.gov/payments/failure-to-deposit-penalty | verified |
| IRS failure-to-deposit penalty (unpaid >10 days after notice) | Additional 5% (total 15% with 10% base) | https://www.irs.gov/payments/failure-to-deposit-penalty | verified |
| Penalty exception (small shortfalls) | No penalty if shortfall <= $100 or <= 2% of required amount, made by makeup date | https://www.irs.gov/payments/failure-to-deposit-penalty | verified |
| QuickBooks Payroll same-day direct deposit cutoff | 7:00 AM PT | https://quickbooks.intuit.com/payroll/direct-deposit/ | verified |
| QuickBooks Payroll next-day direct deposit cutoff | 5:00 PM PT | https://quickbooks.intuit.com/payroll/direct-deposit/ | verified |
| QuickBooks Payroll 2-day direct deposit | Standard offering | https://quickbooks.intuit.com/learn-support/en-ca/help-article/payroll-processes/direct-deposit-processing-timeline/L6aKf86Ms_CA_en_CA | verified |
| QuickBooks Payroll customers | 1.4 million businesses | https://quickbooks.intuit.com/learn-support/en-us/employees-and-payroll/direct-deposit/00/1156665 | verified |
| Gusto customers | 500,000+ businesses | https://gusto.com/product/pricing | verified |
| Gusto annual processing | Processes tens of billions of dollars per year | https://gusto.com/product/pricing | verified |
| Gusto pay frequency options | Weekly, biweekly, twice monthly, monthly; unlimited payroll runs | https://gusto.com/product/pricing | verified |
| ADP workers served | 42 million US workers (1 in 6 US workers) | https://www.adp.com/-/media/corporate-overview/adp-corporate-overview.pdf | verified |
| Rippling payroll processing speed | 90 seconds per pay run | https://www.rippling.com/blog/ach-payroll | verified |
| Rippling geographic coverage | 50+ US states, 185+ countries, 50+ currencies | https://www.rippling.com/blog/ach-payroll | verified |
| BLS pay frequency (biweekly) | 36.5% of US private businesses | https://www.bls.gov/ces/publications/length-pay-period.htm | verified |
| BLS pay frequency (weekly) | 32.4% of US private businesses | https://www.bls.gov/ces/publications/length-pay-period.htm | verified |
| Stripe idempotency key retention | 24 hours (30 days for API v2) | https://docs.stripe.com/api/idempotent_requests | verified |
| Stripe idempotency key mechanism | Saves status code and body of first request; returns same result on retry with same key | https://docs.stripe.com/api/idempotent_requests | verified |
| Stripe idempotency key parameter validation | Validates incoming parameters match original; errors if different | https://docs.stripe.com/api/idempotent_requests | verified |
| Modern Treasury idempotency key retention | 24 hours with state machine enforcement | https://docs.moderntreasury.com/platform/reference/idempotent-requests | verified |
| Modern Treasury idempotency implementation | State machines track payment status and enforce step sequence | https://docs.moderntreasury.com/platform/reference/idempotent-requests | verified |
| Increase idempotency header | Idempotency-Key header (renamed from unique_identifier January 2024) | https://increase.com/documentation/unique_identifiers | verified |
| Increase idempotency scope | Applies to ACH transfers, account transfers, check transfers, RTP transfers, wire transfers | https://increase.com/documentation/unique_identifiers | verified |

---

## Domain Mechanics

### ACH (Automated Clearing House) Network

The ACH network is the US electronic fund transfer system managed by NACHA (National Automated Clearing House Association) and the Federal Reserve. Payroll is a primary use case.

**Same-Day ACH Submission Windows** (Eastern Time):
- Window 1: Submit by 10:30 AM ET, funds available 1:00 PM ET same day.
- Window 2: Submit by 2:45 PM ET, funds available 5:00 PM ET same day.
- Window 3: Submit by 4:45 PM ET, funds available 6:00 PM ET same day.
- Window 4 (proposed effective Sept 19, 2026): Submit by 8:00 PM ET, funds available 10:00 PM ET.

**Per-Payment Limits**:
- Same-Day ACH: current $1M per transaction (raised from $100k on March 1, 2022); proposed $10M.
- Standard ACH: no per-transaction limit; unlimited.
- Standard ACH settlement: 1 business day (covers ~80% of all ACH volume).

**ACH Credit Forward Dating**:
- Originators can date credits same-day, 1 banking day forward, or 2 banking days forward.
- Enables payroll scheduling: submit today for Friday payment, or Thursday for Monday payment.

**Prenotes**:
- Zero-dollar test ACH entry sent before live payment.
- Validates account and routing number.
- Recommended timing: 3 business days before first live entry.

### NACHA ACH File Format

ACH files are fixed-width ASCII, 94 characters per record. Hierarchical structure: File Header → Batch Headers (multiple batches per file) → Entry Details (multiple entries per batch) → Batch Trailer → File Trailer.

**Key fields for duplicate detection**:
- Trace number (positions 80-94): 15 digits = ODFI Routing Transit Number (8) + sequence (7). Must be unique within file. Identifies individual entry.
- File ID modifier (position 34): 1 character, sequential through day (A, B, C... or 0, 1, 2...). Enables ACH Operator to distinguish multiple submissions on same day and prevent reprocessing.

**Record types**:
- Type 1: File Header (metadata).
- Type 5: Batch Header (identifies batch type, e.g. PPD for payroll).
- Type 6: Entry Detail (payment instruction).
- Type 7: Addenda (optional, for payment reference/notes).
- Type 8: Batch Trailer (batch control totals).
- Type 9: File Trailer (file control totals).

### Federal Payroll Tax Deposits

The IRS mandates deposit of withheld payroll taxes (federal income tax, Social Security, Medicare) via EFTPS (Electronic Federal Tax Payment System).

**Depositor Classification**:
- Lookback period: prior 12 calendar months.
- Monthly depositor: tax liability <= $50k → deposit by 15th of following month.
- Semiweekly depositor: tax liability > $50k → deposit per schedule based on payment day:
  - Saturday, Sunday, Monday, Tuesday paydays → Friday deposit.
  - Wednesday, Thursday, Friday paydays → Wednesday deposit.

**$100k Next-Day Deposit Rule**:
- Accumulate $100k or more in tax liability on any day → deposit required next business day.
- Overrides monthly/semiweekly schedule.
- Applies to both types of depositors.

**Electronic Deposit Cutoff**:
- EFTPS submissions must be initiated by 8:00 PM ET day before due date to be timely.
- Methods: Business tax account, Direct Pay for businesses, EFTPS.

**Form 941**:
- Quarterly employer federal tax return (covers wages, withheld taxes, deposited amounts).
- Due date: month + 10 days after quarter end (e.g., April 30 for Q1).

### ACH Return Codes and Timeframes

Returns are rejections of ACH entries by the receiving bank (RDFI) or originating bank (ODFI).

**Common payroll-relevant return codes**:
- R01: Account overdrawn; valid for future authorized debits/credits.
- R02: Account closed.
- R03: No account / unable to locate.
- R04: Invalid account number structure.
- R16: Account frozen (RDFI or legal action).
- R29: Unauthorized (non-consumer accounts only; CCD/CTX entries).

**Return timeframes**:
- Non-consumer accounts: 2 banking days from settlement to return.
- Consumer accounts: 60 calendar days from settlement; requires written statement from consumer.

**Reversals**:
- 5 banking days from settlement to initiate reversal.
- Allowed reasons: originator error (wrong date, amount, account); specific enumerated categories only.
- Not allowed: lack of authorization, customer dispute of legitimate payment, originator cancellation.

### Idempotency in Money Movement

**Stripe**:
- Idempotency key: up to 255 characters, custom string provided by client.
- Retention: 24 hours (30 days for API v2).
- Mechanism: System saves HTTP status code and response body of first request; retry with same key returns identical result.
- Parameter validation: System validates incoming parameters match original request; errors if different (prevents duplicate-with-different-params).

**Modern Treasury**:
- Idempotency key: header-based, 24-hour retention.
- State machines: Track payment status through state lifecycle (pending → submitted → accepted → settled).
- Enforcement: State machines prevent duplicate processing by enforcing allowed step sequences.

**Increase**:
- Idempotency-Key header (renamed from unique_identifier in January 2024).
- Applies to: ACH transfers, account transfers, check transfers, RTP transfers, wire transfers.
- Deduplication: System records key and prevents duplicate submission.

---

## How Real Companies Build It

### Intuit / QuickBooks Payroll

**Scale**:
- 1.4 million businesses using QuickBooks Payroll.
- Services tens of millions of payroll runs per year.

**Direct deposit timing options**:
- Same-day: submit by 7:00 AM PT on payday; funds same business day.
- Next-day: submit by 5:00 PM PT two banking days before payday; funds next business day.
- 2-day: submit by 5:00 PM PT three banking days before payday; funds 2 business days later.
- 5-day: standard ACH settlement.
- Full Service Workforce customers get same-day; others get next-day/2-day/5-day options.

**Payroll processing pipeline**:
- Intake: capture payroll data (hours, deductions, tax withholdings).
- Tax calculation: federal, state, local, FICA.
- ACH file generation: batch processing for all employees in run.
- Submission: transmit to bank's ACH originator.
- Settlement tracking: poll for acks and returns; notify customer of discrepancies.
- Tax deposit: separate pipeline for federal/state tax deposits via EFTPS.

### Gusto

**Scale**:
- 500,000+ businesses (as of 2025).
- Processes tens of billions of dollars annually.

**Pay frequency support**:
- Weekly (52 periods/year).
- Biweekly (26 periods/year).
- Twice monthly (24 periods/year).
- Monthly (12 periods/year).
- Unlimited payroll runs within any frequency.

**Payroll strategy**:
- White-label ACH origination; Gusto integrates with banking partners for file submission.
- Same-day, next-day, and 2-day direct deposit options.
- Embedded tax compliance (federal, state, local filing).

### ADP

**Scale**:
- 42 million US workers (1 in 6 US workers) processed by ADP.
- Largest global payroll processor.

**Service model**:
- Payroll processing (weekly, biweekly, semimonthly, monthly).
- Tax compliance and filing (federal, state, local, multi-state).
- HRIS integration; benefits administration.
- COBRA administration.

### Rippling

**Scale**:
- 90-second payroll processing time per run (claimed).
- 50+ US states coverage.
- 185+ countries, 50+ currencies (global expansion).

**Integrated model**:
- Payroll + HR + benefits in single platform.
- Direct ACH submission (NACHA file generation, Fed Reserve integration).
- State tax filing automation.

---

## Interview Framing

### Where This Topic Appears

1. **Hello Interview**: "Design a payroll engine for 1M small businesses. Crux: exactly-once money movement at scale with deadline pressure (pay dates concentrate on Fridays, 15th, last day of month)."

2. **System Design Blogs**: Gusto engineering on payroll processing at scale, idempotency in ACH, dead-letter queues for failed transfers.

3. **Blind / LeetCode**: "Design a payment system that guarantees exactly-once ACH submission" (LeetCode Discuss, fintech tags).

4. **Exponent / Pramp**: "How would you handle payroll at 500k businesses with 36% biweekly frequency?" or "Walk me through tax deposit deadlines and how you avoid IRS penalties."

### Key Interview Probes

- **Exactly-once semantics**: How do you prevent duplicate ACH submissions if a network failure occurs mid-transmission?
- **Pay date hotspots**: 36.5% of businesses pay biweekly; concentrations on Friday create surge. Scaling strategy?
- **Tax deadlines**: Semiweekly schedule creates hard deadlines (Wed/Fri). What fails first if you miss by 1 day?
- **Idempotency strategy**: Idempotency keys live 24 hours. What happens if retry comes at hour 25?
- **Return handling**: R01, R02, R03 returns from bank. How do you notify customer and offer remediation?
- **State complexity**: 50 states with different tax rates, filing deadlines, rules. Data model for compliance?
- **Consistency model**: Are payroll runs atomic or eventual? What if ACH submits but tax deposit fails?
- **Failure modes**: Bank API timeout during submission window. Retry strategy without duplicating?

---

## Numbers Worth Quoting

1. **Same-Day ACH windows**: 3 current (10:30 AM, 2:45 PM, 4:45 PM ET), 4th proposed 8:00 PM ET (Sept 19, 2026).
   URL: https://www.nacha.org/rules/same-day-ach-moving-payments-faster-phase-1

2. **Same-Day ACH limit**: $1M per transaction (current); raised from $100k March 1, 2022; proposed $10M.
   URL: https://www.nacha.org/million

3. **Standard ACH settlement**: 1 business day; 80% of all ACH volume.
   URL: https://www.nacha.org/news/significant-majority-ach-payments-settle-one-business-day-or-less

4. **ACH file format**: 94 characters per record; fixed-width ASCII.
   URL: https://achdevguide.nacha.org/ach-file-details

5. **Trace number**: 15 characters (ODFI RTN 8-digit + 7-digit sequence); must be unique within file.
   URL: https://achdevguide.nacha.org/ach-file-details

6. **Prenote timing**: Zero-dollar test entry; recommended 3 business days before live entry.
   URL: https://www.nacha.org/system/files/2023-04/Account-Validation-FAQs-Oct-19-2020.pdf

7. **Semiweekly depositor deadlines**: Sat/Sun/Mon/Tues paydays → Friday; Wed/Thu/Fri paydays → Wednesday.
   URL: https://www.irs.gov/pub/irs-pdf/n931.pdf

8. **Monthly depositor deadline**: 15th of following month for all paydays.
   URL: https://www.irs.gov/pub/irs-pdf/n931.pdf

9. **$100k next-day rule**: Accumulate $100k+ tax liability → deposit next business day (overrides schedule).
   URL: https://www.irs.gov/pub/irs-pdf/n931.pdf

10. **IRS failure-to-deposit penalties**: 2% (1-5 days), 5% (6-15 days), 10% (>15 days), +5% if unpaid >10 days after notice.
    URL: https://www.irs.gov/payments/failure-to-deposit-penalty

11. **Return timeframe (non-consumer)**: 2 banking days from settlement.
    URL: https://www.nacha.org/rules/reversals-and-enforcement

12. **Return timeframe (consumer)**: 60 calendar days from settlement; requires written statement.
    URL: https://www.nacha.org/rules/reversals-and-enforcement

13. **Reversal window**: 5 banking days from settlement; originator errors only.
    URL: https://www.nacha.org/rules/reversals-and-enforcement

14. **QuickBooks Payroll scale**: 1.4 million businesses; direct deposit timing (same-day 7 AM PT, next-day 5 PM PT).
    URL: https://quickbooks.intuit.com/payroll/direct-deposit/

15. **Gusto scale**: 500,000+ businesses; processes tens of billions annually; unlimited payroll runs.
    URL: https://gusto.com/product/pricing

16. **ADP scale**: 42 million US workers (1 in 6); largest global payroll processor.
    URL: https://www.adp.com/-/media/corporate-overview/adp-corporate-overview.pdf

17. **Rippling speed**: 90-second payroll processing per run; 185+ countries, 50+ currencies.
    URL: https://www.rippling.com/blog/ach-payroll

18. **BLS pay frequency**: 36.5% biweekly (most common), 32.4% weekly.
    URL: https://www.bls.gov/ces/publications/length-pay-period.htm

19. **Stripe idempotency retention**: 24 hours (30 days API v2); validates parameters; prevents duplicate-with-different-params.
    URL: https://docs.stripe.com/api/idempotent_requests

20. **Modern Treasury idempotency**: 24-hour retention with state machines preventing duplicate processing.
    URL: https://docs.moderntreasury.com/platform/reference/idempotent-requests

---

## Sources

| URL | Content / Purpose |
|-----|-------------------|
| https://www.nacha.org/rules/same-day-ach-moving-payments-faster-phase-1 | NACHA Same-Day ACH rules: 3 windows, limits, settlement times |
| https://www.nacha.org/million | NACHA same-day ACH: $1M limit (current), $10M proposed; history of $100k to $1M increase March 2022 |
| https://www.nacha.org/news/significant-majority-ach-payments-settle-one-business-day-or-less | NACHA standard ACH: 1-day settlement, 80% of volume |
| https://www.nacha.org/rules/ach-network-risk-and-enforcement-topics | NACHA ACH network rules: return codes (R01-R29) meanings |
| https://achdevguide.nacha.org/ach-file-details | ACH Dev Guide: file format (94 char, fixed-width), trace number, record types |
| https://www.nacha.org/system/files/2023-04/Account-Validation-FAQs-Oct-19-2020.pdf | NACHA prenotes: zero-dollar entry, 3-business-day timing |
| https://www.nacha.org/rules/reversals-and-enforcement | NACHA reversals: 5-day window, allowed reasons; return timeframes (2 business days non-consumer, 60 calendar days consumer) |
| https://www.irs.gov/pub/irs-pdf/n931.pdf | IRS Notice 931: deposit schedule (monthly vs semiweekly), $100k next-day rule, electronic cutoff time (8 PM ET) |
| https://www.irs.gov/taxtopics/tc757 | IRS Topic 757: Form 941 (quarterly employer tax return) |
| https://www.irs.gov/payments/failure-to-deposit-penalty | IRS failure-to-deposit penalties: 2% / 5% / 10% / 15% (+ 5% if unpaid >10 days after notice) |
| https://quickbooks.intuit.com/payroll/direct-deposit/ | QuickBooks Payroll: direct deposit timing (same-day 7 AM PT, next-day 5 PM PT, 2-day, 5-day) |
| https://quickbooks.intuit.com/learn-support/en-ca/help-article/payroll-processes/direct-deposit-processing-timeline/L6aKf86Ms_CA_en_CA | QuickBooks Payroll: settlement timeline details |
| https://quickbooks.intuit.com/learn-support/en-us/employees-and-payroll/direct-deposit/00/1156665 | QuickBooks Payroll: 1.4M businesses using payroll |
| https://gusto.com/product/pricing | Gusto: 500k+ businesses, tens of billions annually, unlimited payroll runs, pay frequency options |
| https://www.adp.com/-/media/corporate-overview/adp-corporate-overview.pdf | ADP: 42M US workers (1 in 6), largest global payroll processor |
| https://www.rippling.com/blog/ach-payroll | Rippling: 90-second payroll run, 185+ countries, 50+ currencies; ACH integration |
| https://www.bls.gov/ces/publications/length-pay-period.htm | BLS: US private business pay frequency (36.5% biweekly, 32.4% weekly) |
| https://docs.stripe.com/api/idempotent_requests | Stripe idempotency: 24-hour retention, parameter validation, prevents duplicate-with-different-params |
| https://docs.moderntreasury.com/platform/reference/idempotent-requests | Modern Treasury idempotency: 24-hour retention, state machines, duplicate prevention |
| https://increase.com/documentation/unique_identifiers | Increase: Idempotency-Key header (renamed Jan 2024), applies to ACH/check/wire/RTP transfers |


---

## Spot-check notes (editor, 2026-10-04)

Writers: verify these rows before quoting them, they look wrong or weakly sourced.
- "Same Day ACH Window 4, 8:00 PM ET, effective Sept 19, 2026" and "per-payment limit proposed $10 M": not confirmed. Open the Nacha page. If you cannot confirm, design with the three windows (10:30 AM, 2:45 PM, 4:45 PM ET submission) and the $1 M limit, and mark the rest [unverified].
- "R01 = Account overdrawn; valid for future authorized debit and credit entries": garbled. R01 is Insufficient Funds. Use the Nacha return code list.
- "QuickBooks Payroll customers 1.4 million": the URL is a community forum page, not an Intuit disclosure. Use the README's ~1 M companies as the design number and quote 1.4 M only as [unverified].
- "Rippling 90 seconds per pay run": a marketing claim. Quote as such or skip.
- QuickBooks direct deposit cut-offs (same-day 7 AM PT on payday, next-day 5 PM PT the day before, 2-day 5 PM PT two banking days before): open the QuickBooks page and confirm all three before using them.
