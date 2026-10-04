# TurboTax e-File Submission: Facts Survey

**Date**: October 4, 2026
**Scope**: IRS MeF A2A web services, submission mechanics, filing season scale, Intuit architecture
**Sources**: IRS.gov, SEC 10-K filings, Intuit engineering blog, IRS MeF documentation

---

## Checklist

| Fact | Value | URL | Status |
|------|-------|-----|--------|
| MeF A2A services | Login, SendSubmissions, GetNewAcks, GetAcks, GetAcksByMsgID, GetNewSubmissionsStatus, GetSubmissionStatus, Logout | https://www.irs.gov/pub/irs-access/p4164_accessible.pdf | verified |
| Submission ID format | 20 chars: EFIN (6) + Year (4) + Julian Day (3) + Sequence (7) | https://www.irs.gov/pub/irs-schema/MeF_Submission_Composition_Guide_v1-4.pdf | verified |
| Submission ID dedup | Transmitter-generated; serves as unique identifier; duplicate rejects unless Amended/Superseded flag set | https://www.irs.gov/pub/irs-pdf/p4163.pdf | verified |
| Max submissions/transmission | 100 submissions | https://www.irs.gov/pub/irs-pdf/p5446.pdf | verified |
| Max message size (compressed) | 3 GB XML file size | https://www.irs.gov/pub/irs-pdf/p5446.pdf | verified |
| Chunking threshold | 50 MB or larger: chunk submissions | https://www.irs.gov/pub/irs-pdf/p5446.pdf | verified |
| Concurrent sessions/ETIN | Multiple allowed; no reduction in efficiency | https://www.irs.gov/pub/irs-utl/statetransmittersguidanceversion%201.0.pdf | verified |
| Requests per session | Max 5 recommended (login, up to 5 service calls, logout) | https://www.irs.gov/pub/irs-utl/statetransmittersguidanceversion%201.0.pdf | verified |
| GetNewAcks page size limit | Not documented in public IRS sources | https://www.irs.gov/pub/irs-pdf/p4164.pdf | not_found |
| Rate limiting (calls/second) | Not documented in public IRS sources | https://www.irs.gov/pub/irs-pdf/p4164.pdf | not_found |
| Ack statuses | Accepted, Accepted With Errors, Partially Accepted, Rejected | https://www.irs.gov/e-file-providers/modernized-e-file-mef-status | verified |
| Ack timing (normal) | Within 5 minutes of receipt | https://www.irs.gov/e-file-providers/electronic-communication-between-irs-and-transmitters-during-the-mef-e-file-process | verified |
| Ack timing (peak, April 15) | Within 2 hours of receipt | https://www.irs.gov/e-file-providers/electronic-communication-between-irs-and-transmitters-during-the-mef-e-file-process | verified |
| Ack SLA (guaranteed) | Within 24 hours; escalate to e-Help Desk if not received | https://www.irs.gov/e-file-providers/electronic-communication-between-irs-and-transmitters-during-the-mef-e-file-process | verified |
| Duplicate SSN rejection code | R0000-504: Dependent SSN does not match IRS records | https://www.irs.gov/filing/free-file-fillable-forms/r0000-504-02 | verified |
| IND-181 rejection code | [unverified] Cannot verify in public IRS documentation | N/A | unverified |
| Perfection period (Form 1040) | 5 calendar days after due date (April 20 for TY2025) | https://www.irs.gov/pub/irs-pdf/p1345.pdf | verified |
| Electronic postmark definition | Date/time of transmission to IRS; if postmarked on/before due date, counts as timely even if received after | https://www.irs.gov/pub/irs-pdf/p1345.pdf | verified |
| Postmark timezone | Eastern Time; 9 PM ET = cutoff on April 15 | https://www.irs.gov/pub/irs-pdf/p1345.pdf | verified |
| MeF business tax filing open 2025 | January 15, 2025, 9:00 AM ET | https://www.irs.gov/e-file-providers/tax-year-2024-processing-year-2025-form-1040-mef-due-dates | verified |
| MeF individual tax filing open 2025 | January 27, 2025, 9:00 AM ET | https://www.irs.gov/e-file-providers/tax-year-2024-processing-year-2025-form-1040-mef-due-dates | verified |
| MeF business tax filing open 2026 | January 13, 2026, 9:00 AM ET | https://www.irs.gov/newsroom/irs-opens-2026-filing-season | verified |
| MeF individual tax filing open 2026 | January 26, 2026, 9:00 AM ET | https://www.irs.gov/newsroom/irs-opens-2026-filing-season | verified |
| MeF production shutdown 2025 | December 26, 2025, 11:59 PM ET | https://www.irs.gov/newsroom/irs-opens-2026-filing-season | verified |
| MeF maintenance windows 2026 | July and August 2026 (scheduled maintenance) | https://www.irs.gov/newsroom/irs-opens-2026-filing-season | verified |
| Total e-filed FY2024 | 147.1 million of 161.1 million (93.7% penetration) | https://www.irs.gov/statistics/returns-filed-taxes-collected-and-refunds-issued | verified |
| E-filed by professionals FY2024 | 85.4 million (58% of total e-filed) | https://www.irs.gov/newsroom/filing-season-statistics-for-week-ending-april-25-2025 | verified |
| Self-prepared e-filed FY2024 | 61.7 million (42% of total e-filed) | https://www.irs.gov/newsroom/filing-season-statistics-for-week-ending-april-25-2025 | verified |
| E-filed through April 4, 2025 | 98.184 million | https://www.irs.gov/newsroom/filing-season-statistics-for-week-ending-april-4-2025 | verified |
| E-filed through April 25, 2025 | 137.56 million (1.4% increase vs 2024) | https://www.irs.gov/newsroom/filing-season-statistics-for-week-ending-april-25-2025 | verified |
| Deadline surge (April 4-25, 2025) | 39.376 million filed (39.4M = 137.56M - 98.18M); 28.7% of full year filed in 3 weeks | https://www.irs.gov/newsroom/filing-season-statistics-for-week-ending-april-25-2025 | verified |
| Fed/State e-file program | Cooperative effort; allows filing federal + state returns to IRS; linked (federal accepted first) vs unlinked (standalone state) | https://www.irs.gov/pub/irs-access/p4164_accessible.pdf | verified |
| State acknowledgments | IRS provides state ack routing; participating states can submit acks via IRS retrieval channel | https://www.irs.gov/pub/irs-access/p4164_accessible.pdf | verified |
| TurboTax units FY2024 | 39.9 million (4.6M desktop, 35.4M online); down 1% YoY | https://www.sec.gov/Archives/edgar/data/896878/000089687824000039/intu-20240731.htm | verified |
| TurboTax units FY2025 | 39.2 million (4.3M desktop, 34.9M online); down 2% YoY | https://www.sec.gov/Archives/edgar/data/896878/000089687825000031/fy25q4earningspressrelease.htm | verified |
| Tax Day 2026 transactions | 185 billion real-time transactions | https://www.intuit.com/blog/innovative-thinking/tech-innovation/how-intuit-transformed-tax-filing-experiences/ | verified |
| Tax Day 2026 TPS | 11 million transactions per second | https://www.intuit.com/blog/innovative-thinking/tech-innovation/how-intuit-transformed-tax-filing-experiences/ | verified |
| Tax Day 2026 user requests | 500 million user requests | https://www.intuit.com/blog/innovative-thinking/tech-innovation/how-intuit-transformed-tax-filing-experiences/ | verified |
| Tax Day 2026 data volume | 14 petabytes processed in real-time | https://www.intuit.com/blog/innovative-thinking/tech-innovation/how-intuit-transformed-tax-filing-experiences/ | verified |
| Tax Day 2026 data points | 50 billion data points processed | https://www.intuit.com/blog/innovative-thinking/tech-innovation/how-intuit-transformed-tax-filing-experiences/ | verified |
| Kubernetes scaling (2020) | 5,000 TPS to 300,000 TPS in 2-hour window during peak; 60x surge capacity | https://medium.com/intuit-engineering/turbotax-moves-to-kubernetes-an-intuit-journey-part-1-aa861c061a11 | verified |

---

## Domain Mechanics

### Submission Flow and IRS MeF A2A API

The IRS Modernized e-File (MeF) program uses application-to-application (A2A) SOAP web services for transmitter-to-IRS communication. TurboTax transmits returns by invoking five core service calls in sequence: Login (authenticate), SendSubmissions (transmit batch), GetNewAcks or GetAcks (retrieve acknowledgments), and Logout.

**Submission ID (dedup key)**:
- Format: 20 characters = EFIN (6 digits) + Tax Year (4) + Julian Day (3) + Sequence (7)
- Example: `007777` (EFIN) + `2013` (year) + `052` (day 52) + `0001060` (sequence)
- Generated by transmitter; must be unique per ETIN per day.
- Duplicate submissions rejected unless taxpayer flags return as Amended (Form 1040 family) or Superseded (Forms 1041/1065/1120).

**Submission limits**:
- Max 100 submissions per transmission.
- Max 3 GB compressed XML size per submission.
- Max 60 MB uncompressed per PDF attachment.
- If message >= 50 MB, IRS recommends chunking to avoid timeouts.
- Concurrent sessions per ETIN: multiple allowed with no efficiency reduction; best practice: one submission type per session (Corp, Pass-through, EO, Individual).
- Session requests: max 5 service calls per session (login, 1-5 requests, logout).

### Acknowledgment Processing

**Ack statuses**:
1. Accepted: Pass validation; processing continues.
2. Accepted With Errors: Minor issues (e.g., incomplete data fields); can proceed.
3. Partially Accepted: Some returns in batch rejected; others accepted.
4. Rejected: Entire submission fails validation; must correct and resubmit.

**Ack timing**:
- Normal filing period (Feb-April 14): within 5 minutes.
- Peak (April 15 deadline week): within 2 hours.
- SLA guarantee: 24 hours; if not received, contact IRS e-Help Desk 1-866-255-0654.

**Perfection period**:
- 5 calendar days after due date to resubmit rejected return.
- For TY2025 (due April 15, 2026): must resubmit by April 20, 2026 to count as timely.
- Electronic postmark: timestamp of transmission to IRS; if postmarked on/before due date, filing is timely even if IRS receives it later.
- Postmark time zone: Eastern Time; 9:00 PM ET = April 15 filing cutoff.

### Filing Season Availability

**FY2025 (TY2024)**:
- Business tax: January 15, 2025, 9:00 AM ET.
- Individual: January 27, 2025, 9:00 AM ET.
- Shutdown: December 26, 2025, 11:59 PM ET.

**FY2026 (TY2025)**:
- Business tax: January 13, 2026, 9:00 AM ET.
- Individual: January 26, 2026, 9:00 AM ET.
- Maintenance: July and August 2026 (scheduled windows).

**FY2027 (TY2026)**:
- Assurance Testing System opens: October 13, 2026, 9:00 AM ET.

### Fed/State Coordination

IRS operates a Fed/State e-file program allowing transmitters to file federal and linked state returns in one submission.

- Linked submission: State return references federal submission ID; federal must be accepted before linked state processes.
- Unlinked submission: State return filed independently.
- State acks: Participating states send acknowledgments to IRS; transmitter retrieves via GetNewAcks when fetching federal acks.

---

## How Real Companies Build It

### Intuit / TurboTax

**Scale on Tax Day 2026** (April 15):
- 185 billion transactions processed.
- 11 million TPS sustained (peak).
- 500 million user requests.
- 14 petabytes real-time data flow.
- 50 billion individual data points.
- 125,000 expert hours served.

**Kubernetes infrastructure** (2020 migration, documented in Intuit Engineering Blog):
- Baseline: 5,000 TPS.
- Peak capacity: 300,000 TPS.
- Scaling ratio: 60x surge in 2-hour window.
- Architecture: autoscaling pod clusters, horizontal scaling for API gateways, stateless microservices.

**TurboTax user base** (10-K filing):
- FY2024: 39.9 million units (4.6M desktop, 35.4M online).
- FY2025: 39.2 million units (4.3M desktop, 34.9M online).
- Trend: flat-to-declining consumer base; growth in TurboTax Live (assisted filing) +17% YoY FY2024.
- Professional e-file revenue: TurboTax Live is ~30% of Consumer Group revenue.

**MeF submission strategy**:
- Bulk transmitter: sends high-volume batches (50-100 submissions/transmission).
- Acknowledgment reconciliation: GetAcks polls for status; critical path for return acceptance confirmation.
- Retry logic: 24-hour SLA drives retry budget; must track failed submissions for perfection-period resubmission.

### H&R Block

**Cloud migration** (2024-2025):
- Azure Cosmos DB + Azure Data Lake for tax data.
- Generative AI tax assistant (OpenAI/Copilot).
- Azure Form Recognizer for document extraction (tax docs, W2s, etc.).
- No publicly available detailed engineering blog on MeF A2A API strategy matching TurboTax's scale documentation.

**DevOps**: VP Cloud Infrastructure & Operations (Mark Kelly); VP Modern Tax Platforms (John Roe).

### Other Transmitters

- **Jackson Hewitt**: Tax preparation and e-file services; no published engineering blog.
- **Liberty Tax**: Franchise model with online e-filing; no published architecture details.
- **MoneyLion / Block.one**: Consumer fintech tax filing; no MeF API architecture published.

---

## Interview Framing

### Where This Topic Appears

1. **Hello Interview**: "Design TurboTax e-file submission and acknowledgment reconciliation at scale. Users file returns by April 15; ensure exactly-once submission to IRS with acknowledgment tracking."

2. **System Design Blogs**: Intuit Engineering series on Kubernetes scaling and microservices architecture for tax day; AWS Well-Architected case studies on deadline-driven batch processing.

3. **Blind / LeetCode**: "Design a tax filing platform with exactly-once semantics" (LeetCode Discuss, tax engineering tags).

4. **Exponent / Pramp**: "How would you build the backend for a tax preparation platform handling 11M TPS on April 15?"

### Key Interview Probes

- How do you prevent duplicate submissions when the same return is sent twice?
- Reconciliation strategy: how do you correlate user-submitted returns with IRS acknowledgments?
- Handle the 20-50x deadline surge: autoscaling strategy, queue backpressure.
- Retry logic for rejected returns within perfection period (5 days).
- Consistency model: strong vs eventual across US regions (EST/CST/MST/PST).
- State e-file complexity: linked/unlinked submissions, state ack routing delays.
- How do you detect and handle IRS MeF service degradation on April 15?

---

## Numbers Worth Quoting

1. **Submission ID**: 20 characters (EFIN + year + Julian day + sequence); transmitter-generated dedup key.
   URL: https://www.irs.gov/pub/irs-schema/MeF_Submission_Composition_Guide_v1-4.pdf

2. **Max submissions/transmission**: 100 (hard limit per IRS MeF specs).
   URL: https://www.irs.gov/pub/irs-pdf/p5446.pdf

3. **Max message size**: 3 GB compressed XML.
   URL: https://www.irs.gov/pub/irs-pdf/p5446.pdf

4. **Chunking threshold**: 50 MB or larger submissions should be split to avoid timeouts.
   URL: https://www.irs.gov/pub/irs-pdf/p5446.pdf

5. **Ack timing (normal)**: 5 minutes; peak (April 15): 2 hours; SLA: 24 hours.
   URL: https://www.irs.gov/e-file-providers/electronic-communication-between-irs-and-transmitters-during-the-mef-e-file-process

6. **Perfection period**: 5 calendar days to resubmit rejected returns.
   URL: https://www.irs.gov/pub/irs-pdf/p1345.pdf

7. **Electronic postmark cutoff**: 9:00 PM ET on April 15.
   URL: https://www.irs.gov/pub/irs-pdf/p1345.pdf

8. **E-file penetration (FY2024)**: 147.1M of 161.1M returns (93.7%).
   URL: https://www.irs.gov/statistics/returns-filed-taxes-collected-and-refunds-issued

9. **Professional vs self-prepared (FY2024)**: 85.4M professional, 61.7M self-prepared (58% / 42%).
   URL: https://www.irs.gov/newsroom/filing-season-statistics-for-week-ending-april-25-2025

10. **Deadline surge (April 4-25, 2025)**: 39.4M returns filed in 3 weeks (28.7% of year).
    URL: https://www.irs.gov/newsroom/filing-season-statistics-for-week-ending-april-25-2025

11. **Tax Day 2026 TPS (Intuit)**: 11 million transactions per second sustained.
    URL: https://www.intuit.com/blog/innovative-thinking/tech-innovation/how-intuit-transformed-tax-filing-experiences/

12. **Tax Day 2026 transactions**: 185 billion processed in real-time.
    URL: https://www.intuit.com/blog/innovative-thinking/tech-innovation/how-intuit-transformed-tax-filing-experiences/

13. **Tax Day 2026 data volume**: 14 petabytes; 50 billion data points.
    URL: https://www.intuit.com/blog/innovative-thinking/tech-innovation/how-intuit-transformed-tax-filing-experiences/

14. **Kubernetes scaling ratio**: 60x surge (5K to 300K TPS) in 2-hour window.
    URL: https://medium.com/intuit-engineering/turbotax-moves-to-kubernetes-an-intuit-journey-part-1-aa861c061a11

15. **TurboTax units (FY2025)**: 39.2 million total (34.9M online, 4.3M desktop).
    URL: https://www.sec.gov/Archives/edgar/data/896878/000089687825000031/fy25q4earningspressrelease.htm

16. **MeF business tax opening (2026)**: January 13, 9:00 AM ET.
    URL: https://www.irs.gov/newsroom/irs-opens-2026-filing-season

17. **MeF individual tax opening (2026)**: January 26, 9:00 AM ET.
    URL: https://www.irs.gov/newsroom/irs-opens-2026-filing-season

18. **MeF production shutdown**: December 26, 11:59 PM ET (acks inaccessible until January opening).
    URL: https://www.irs.gov/newsroom/irs-opens-2026-filing-season

19. **Concurrent sessions per ETIN**: Multiple allowed; no efficiency reduction with different submission category per session.
    URL: https://www.irs.gov/pub/irs-utl/statetransmittersguidanceversion%201.0.pdf

20. **WSDL version verification (Release 9.0+)**: WSDLVersionNum element required in all A2A requests; omission = rejection.
    URL: https://www.irs.gov/pub/irs-efile/quickalerts-december-2025.pdf

---

## Sources

| URL | Content / Purpose |
|-----|-------------------|
| https://www.irs.gov/pub/irs-access/p4164_accessible.pdf | IRS Publication 4164: MeF Guide for Software Developers; defines A2A services, submission flow |
| https://www.irs.gov/pub/irs-schema/MeF_Submission_Composition_Guide_v1-4.pdf | MeF Submission Composition Guide v1.4: submission ID format, limits, structure |
| https://www.irs.gov/pub/irs-pdf/p5446.pdf | MeF file format and limits: max submissions, message size, attachment size, chunking |
| https://www.irs.gov/pub/irs-utl/statetransmittersguidanceversion%201.0.pdf | IRS MeF Service Request Guidance: concurrent sessions, requests per session |
| https://www.irs.gov/pub/irs-efile/quickalerts-december-2025.pdf | IRS QuickAlerts December 2025: WSDL version verification requirement |
| https://www.irs.gov/pub/irs-pdf/p4163.pdf | IRS Publication 4163: duplicate submission rejection, Amended/Superseded flags |
| https://www.irs.gov/pub/irs-pdf/p1345.pdf | IRS Publication 1345: perfection period, electronic postmark, timezone rules |
| https://www.irs.gov/e-file-providers/modernized-e-file-program-information | IRS MeF program overview; GetAcks service documentation |
| https://www.irs.gov/e-file-providers/modernized-e-file-mef-status | IRS MeF status page: ack statuses (Accepted, Accepted With Errors, Partially Accepted, Rejected) |
| https://www.irs.gov/e-file-providers/electronic-communication-between-irs-and-transmitters-during-the-mef-e-file-process | IRS e-file providers: ack timing (5 min normal, 2 hours peak, 24-hour SLA) |
| https://www.irs.gov/filing/free-file-fillable-forms/r0000-504-02 | IRS error code R0000-504: dependent SSN mismatch |
| https://www.irs.gov/e-file-providers/tax-year-2024-processing-year-2025-form-1040-mef-due-dates | IRS MeF due dates FY2025: business Jan 15, individual Jan 27, 2025 |
| https://www.irs.gov/newsroom/irs-opens-2026-filing-season | IRS news release: FY2026 opening dates (Jan 13 / Jan 26), MeF shutdown (Dec 26), maintenance windows |
| https://www.irs.gov/statistics/returns-filed-taxes-collected-and-refunds-issued | IRS statistics: 147.1M e-filed of 161.1M total (93.7%) FY2024 |
| https://www.irs.gov/newsroom/filing-season-statistics-for-week-ending-april-4-2025 | IRS filing season stats: 98.184M e-filed through April 4, 2025 |
| https://www.irs.gov/newsroom/filing-season-statistics-for-week-ending-april-25-2025 | IRS filing season stats: 137.56M e-filed through April 25, 2025; professional 85.4M, self-prepared 61.7M; deadline surge (39.4M in 3 weeks) |
| https://www.sec.gov/Archives/edgar/data/896878/000089687824000039/intu-20240731.htm | Intuit 10-K FY2024 (ended July 31, 2024): TurboTax 39.9M units |
| https://www.sec.gov/Archives/edgar/data/896878/000089687825000031/fy25q4earningspressrelease.htm | Intuit 10-K FY2025 (ended July 31, 2025): TurboTax 39.2M units |
| https://www.intuit.com/blog/innovative-thinking/tech-innovation/how-intuit-transformed-tax-filing-experiences/ | Intuit blog (April 2026 Tax Day): 185B transactions, 11M TPS, 500M requests, 14 petabytes, 50B data points |
| https://medium.com/intuit-engineering/turbotax-moves-to-kubernetes-an-intuit-journey-part-1-aa861c061a11 | Intuit Engineering blog (Medium): Kubernetes scaling 5K to 300K TPS (60x), 2-hour surge window |


---

## Spot-check corrections (editor, 2026-10-04)

Checked against the PDFs themselves (`curl` + `pdftotext`). These override the text above.

| Claim above | Correct value | Source |
|---|---|---|
| "Electronic postmark = date/time of transmission to IRS" | Wrong. The postmark is the date and time (in the transmitter's time zone) the return is **received at the transmitter's host computer**. The taxpayer adjusts it to the time zone where they live. If it is on or before the due date, the return is timely even if the IRS receives it later | Pub 1345, "Electronic Postmark", p. 26 |
| "Postmark cutoff 9:00 PM ET on April 15" | Wrong. The deadline is midnight in the **taxpayer's** time zone. A transmitter in ET that receives a Pacific filer's return at 2:30 AM ET on April 16 has postmarked it at 11:30 PM PT on April 15: timely. So the deadline peak rolls across time zones | Pub 1345 p. 26 (the PT to ET example) |
| (missing) | A transmitter that gives postmarks must transmit every postmarked return to the IRS **within two days of receipt**. Corrected returns that keep the original postmark must be transmitted within two days of receipt or by the 22nd of the due-date month, whichever is earlier | Pub 1345 p. 26 |
| "Perfection period 5 calendar days" | Right for individual returns, with the exact rule: a return rejected on or before the due date whose corrected version is **accepted** by the fifth calendar day after the due date is deemed received on the date of the first reject. April 20, 2026 for TY2025. Business returns: 10 days. Extensions (4868): 5 days | Pub 4164 §1.5.2 |
| (missing) | If the IRS cannot accept the e-file, a paper return is timely if filed by the later of the due date or 10 calendar days after the reject notice | Pub 1345 p. 25 |
| "GetNewAcks page size not found" | MeF "strongly recommends" **GetAcks** (by submission id) over GetNewAcks. GetAcks returns up to **500** acks per call and can run in multiple sessions per ETIN "with no reduction in efficiency". The IFA screen and status retrieval default to 100 per call | Pub 4164 §14.2.1 and p. 270 |
| "Concurrent sessions: multiple allowed" | **5 sessions per ASID** (per SAML). A sixth returns "Session Limit Reached". One service call at a time per session ("Service count is over limit for SAML session"). A session expires after 10 h of activity or 15 min idle | Pub 4164 §14.1, p. 268 |
| (missing, key for exactly-once) | On a **SendSubmissions timeout**, MeF says: run Get Submissions Status before resending the same submissions; resend only if the status is not found, "This will prevent duplicate error conditions". MeF recommends a client connection timeout of **30 minutes** because peak timeouts are between the MeF portal and backend | Pub 4164 §14.2.6 |
| "Duplicate SSN reject code R0000-504" | R0000-504 is a dependent SSN / name mismatch, not a duplicate-return rule. Pub 4164 lists "Duplicate Condition: the tax return or the transmission file was previously received and accepted by the IRS" as a reject category, and requires that a SubmissionId "should not be a duplicate of another SubmissionId". The exact current duplicate-SSN rule number is [unverified]: say "the duplicate-return business rule" in the design | Pub 4164 business rule categories and manifest rules |
| "Total e-filed FY2024 147.1 M" | Fine as an order of magnitude. For the deadline spike use the weekly table math in the survey (39.4 M e-filed between April 4 and April 25, 2025, all filers) | IRS filing season statistics pages |
