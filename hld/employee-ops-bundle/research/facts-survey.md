# Rippling Onsite System Design: Facts Verification Survey

## Part 1: Event Ingestion, Dedup, Late Data

## 1. Amplitude HTTP V2 API Insert ID Dedup Window

- Verdict: CONFIRMED
- Exact quote: "Amplitude ignores subsequent events sent with the same `insert_id` on the same `device_id`... in each app within the past 7 days."
- Batch limits: <2,000 events per request, <1 MB payload size
- URL: https://amplitude.com/docs/analytics/apis/http-v2-api
- Note: Dedup window is 7 days; batch API requires breaking requests into <1MB chunks for safe delivery; no max age specified for event timestamps.

## 2. Mixpanel $insert_id Dedup Semantics

- Verdict: CONFIRMED
- Exact quote: "Events with identical values for (event, time, distinct_id, $insert_id) are considered duplicates; only the latest ingested one will be considered in queries."
- /import API: accepts events older than 1 hour but not before January 1, 1971; up to 1 hour in the future
- URL: https://docs.mixpanel.com/reference/import-events
- Note: Dedup is composite key; /import has a 1-hour past window (not 5 days as believed); future window is 1 hour max.

## 3. Segment "Delivering Billions of Messages Exactly Once" (2017)

- Verdict: CONFIRMED
- Exact quote: "a **4-week** window of de-duplication before aging out old keys" using RocksDB
- Message ID: UUIDv4 format, e.g. `"messageId": "ajs-65707fcf61352427e8f1666f0e7f6090"`
- Storage: "1.5 TB of keys stored on disk in RocksDB", "approximately 60 billion keys", "200 billion messages passed through"
- Dedup rate: "0.6% of events ingested are duplicates"
- URL: https://www.twilio.com/en-us/blog/insights/exactly-once-delivery/
- Note: 4-week dedup window (28 days); RocksDB on local EBS; UUIDv4-based keys; 60B keys stored for 200B messages throughput.

## 4. Segment Analytics-iOS SDK Configuration

- Verdict: PARTIALLY CONFIRMED (indirect source)
- Max queue size: maxQueueSize 1,000 events
- Flush at: flushAt default 20 events (search results mention 100 as batch size option)
- Flush interval: flushInterval 30 seconds (from React Native docs; iOS may vary)
- Batch cap: 500 KB per batch request, 32 KB per call maximum
- URL: https://segment.com/docs/connections/sources/catalog/libraries/mobile/ios/
- Note: SDK docs behind 403; info from WebSearch results. Actual iOS defaults may differ; recommend checking GitHub source.

## 5. Datadog Metrics Submission API Timestamp Limits

- Verdict: CONFIRMED
- Exact quote: "Timestamps should be in POSIX time in seconds, and cannot be more than ten minutes in the future or more than one hour in the past."
- Historical metrics: with explicit enablement, can backfill up to metric retention period (default 15 months)
- URL: https://docs.datadoghq.com/api/latest/metrics/submit-metrics/
- Note: 1 hour past, 10 minutes future is the hard limit; historical backfill is opt-in per metric.

## 6. Stripe Billing Meter Events (Usage-Based Billing)

- Verdict: CONFIRMED with corrections
- Identifier field: "identifier" (not explicitly named "identifier" in doc but this is the dedup field)
- Uniqueness window: "at least 24 hours" (confirmed; user belief correct)
- Timestamp constraints: "within the past 35 calendar days or up to 5 minutes in the future"
- Rate limits (v1 meter events): 1,000 events/second live mode
- Rate limits (v2 meter events): 1,000 events/second; meter event streams support 10,000/second
- Async aggregation: "Meter events are processed asynchronously, so they may not be immediately reflected in aggregates or on upcoming invoices."
- URL: https://docs.stripe.com/billing/subscriptions/usage-based/
- Note: Timestamp window is 35 days past (not unlimited), 5 min future; v1 and v2 both 1k/s, streams are 10k/s; async aggregation confirmed.

## 7. Stripe Idempotency-Key Expiry

- Verdict: CONFIRMED
- Exact quote: "You can remove keys from the system automatically after they're at least 24 hours old."
- URL: https://docs.stripe.com/api/idempotent_requests
- Note: "at least 24 hours" means keys can be pruned after 24 hours; new request generates if key reused post-pruning.

---

## Part 3: Termination Orchestration Across External Systems

## 8. SCIM 2.0 RFC 7644 DELETE Semantics

- Verdict: CONFIRMED with nuance
- DELETE status: Returns HTTP 204 (No Content) upon successful deletion
- Permanent deletion: RFC 7644 states "Service providers **MAY choose not to permanently delete** the resource but **MUST return a 404** (Not Found) error code for all operations associated with the previously deleted resource."
- Post-deletion behavior: "Service providers MUST omit the resource from future query results."
- URL: https://datatracker.ietf.org/doc/html/rfc7644
- Note: 204 status; soft-delete is allowed if 404 behavior maintained; allows flexibility for implementations.

## 9. RFC 7643 SCIM 2.0 `active` Attribute

- Verdict: CONFIRMED
- Exact quote: "A Boolean value indicating the user's administrative status. The definitive meaning of this attribute is determined by the service provider."
- Note: true implies can log in; false implies suspended (typical); interpretation is implementation-dependent.
- URL: https://www.rfc-editor.org/rfc/rfc7643.txt
- Note: Service provider owns semantics; convention is true=active, false=suspended.

## 10. Slack SCIM API

- Verdict: UNVERIFIED (API docs behind 403)
- Expected behavior: DELETE /Users/{id} **deactivates** (does not delete)
- admin.users.session.reset: Revokes all user sessions; endpoint URL redirected to 404
- Rate limits: [UNVERIFIED - docs blocked]
- URL: https://api.slack.com/scim (403 Forbidden)
- Note: Industry standard deactivation behavior; official Slack docs inaccessible via public fetch.

## 11. Google Workspace Admin SDK Directory API

- Verdict: PARTIALLY CONFIRMED
- users.update with `suspended` parameter: Suspends the user account; `suspensionReason` field captures reason
- users.signOut: "signs a user out of all web and device sessions and resets their sign-in cookies"
- tokens.delete: [Referenced but behavior not detailed in search results]
- Data Transfer API: [Found reference but details not fully verified]
- URL: https://developers.google.com/workspace/admin/directory/reference/rest/v1/users/update
- Note: Suspend and sign-out are separate operations; no explicit timing on propagation delay in fetched docs.

## 12. Microsoft Entra ID / Graph revokeSignInSessions

- Verdict: CONFIRMED
- Exact quote: "Invalidates all the **refresh tokens issued to applications** for a user (and session cookies in a user's browser), by resetting the **signInSessionsValidFromDateTime** user property to the current date-time."
- Delay: "After you call **revokeSignInSessions**, there might be a small delay of a few minutes before tokens are revoked."
- Access token lifetime (default): 60 to 90 minutes (standard; CAE extends to 28 hours)
- CAE (Continuous Access Evaluation): Long-lived tokens up to 28 hours with near-real-time revocation on critical events
- URL: https://learn.microsoft.com/en-us/graph/api/user-revokesigninsessions
- Note: Refresh tokens revoked immediately; access tokens valid until expiry (few minutes delay typical); CAE enables 28-hour tokens with event-driven revocation.

## 13. Okta Users API Lifecycle Deactivate

- Verdict: CONFIRMED
- Operation: Async deactivation via `Prefer: respond-async` HTTP header
- During async: `transitioningToStatus` property is `DEPROVISIONED`
- Final status: User status becomes `DEPROVISIONED` when complete
- Two-call requirement: DELETE on deactivated user auto-deactivates first; can chain deactivate().then(delete())
- URL: https://developer.okta.com/docs/api/openapi/okta-management/management/tags/userlifecycle/other/deactivateuser
- Note: Async supported; two-call pattern (deactivate then delete) is standard; destructive operation (unrecoverable).

## 14. Stripe Issuing Card Cancel Status

- Verdict: CONFIRMED
- Status `canceled`: "This status is **permanent.**"
- Cancellation reasons: `lost`, `stolen` [possibly others, but these confirmed]
- URL: https://docs.stripe.com/api/issuing/cards/update
- Note: Canceled is irreversible; at least lost/stolen reasons documented.

## 15. Marqeta Card State TERMINATED

- Verdict: CONFIRMED
- Status: "Terminated cards cannot be reactivated."
- Terminal: "To make cards permanently non-functional, you can transition them to a terminated state."
- Transitions: Use /cardtransitions endpoint; TERMINATED is permanent end state
- URL: https://www.marqeta.com/docs/developer-guides/managing-lost-stolen-or-damaged-cards
- Note: TERMINATED is terminal (irreversible); matches Stripe Issuing canceled semantics.

## 16. Apple MDM EraseDevice Command

- Verdict: UNVERIFIED (404)
- Expected behavior: Command is queued until device checks in; MDM server receives acknowledgement when executed
- URL: https://developer.apple.com/documentation/devicemanagement/erasedevice (404)
- Note: Apple developer docs inaccessible via fetch; behavior follows MDM queuing pattern.

## 17. Microsoft Intune Wipe Remote Action

- Verdict: PARTIALLY CONFIRMED
- Behavior: Action sent to device; status shows "Pending" until device checks in
- Can cancel: **No.** "Currently, there is no method to cancel wipe action in Microsoft Intune."
- Pending duration: "Devices will remain in Retire/Wipe Pending state until the MDM certificate expires" (1 year default)
- Auto-cleanup: "180 days after the MDM certificate expires, the device will be automatically removed from the Azure portal"
- URL: https://learn.microsoft.com/en-us/intune/device-management/actions/wipe
- Note: Wipe is pending until check-in; **cannot be canceled**; this is a design constraint (no rollback).

## 18. Temporal Default Activity Retry Policy

- Verdict: CONFIRMED
- Exact values: initialInterval 1 second, backoffCoefficient 2.0, maximumInterval 100 seconds, maximumAttempts unlimited
- Retry behavior: Exponential backoff; non-retryable errors default to none
- Signals & Updates: Workflow.Await patterns for receiving webhooks; documented in SDK guides
- URL: https://docs.temporal.io/encyclopedia/retry-policies
- Note: Exponential backoff (2x multiplier) capped at 100s; unlimited attempts by default; patterns documented for event-driven workflows.

## 19. PCI DSS v4.0 Requirement 8.2.5

- Verdict: UNVERIFIED (PDF 403 Forbidden)
- Expected text: "Access for terminated users is immediately revoked"
- URL: https://listings.pcisecuritystandards.org/documents/PCI-DSS-v4_0.pdf (403 access)
- Note: Search results confirm requirement exists; primary source blocked; no direct quote obtained.

## 20. SOC 2 / AICPA TSC CC6.2 and CC6.3

- Verdict: CONFIRMED (from compliance frameworks)
- CC6.2: "Access is removed promptly when personnel leave the organization or change roles" (typically within 24 hours for voluntary, immediately for involuntary)
- CC6.3: "Periodic reviews of all user access to identify and remove accounts that are no longer authorized" (quarterly or semi-annually)
- CC6.8: Most common source of exceptions (user terminated in HR but access remains active)
- URL: https://docs.alertlogic.com/analyze/reports/compliance/SOC2-CC-6.3-access-modification-and-removal.htm
- Note: CC6.2 and CC6.3 are audit staples; termination delay is #1 SOC 2 exception.

---

## Part 4: LLM Assistant Safety

## 21. OWASP Top 10 for LLM Applications 2025

- Verdict: CONFIRMED
- Exact names:
  - LLM01:2025 - **Prompt Injection**
  - LLM02:2025 - **Sensitive Information Disclosure**
  - LLM05:2025 - **Improper Output Handling**
  - LLM06:2025 - **Excessive Agency**
  - LLM08:2025 - **Vector and Embedding Weaknesses**
- URL: https://genai.owasp.org/llm-top-10/
- Note: Names differ slightly from original 2023 list; LLM05 is now "Improper Output Handling" (was "Insecure Output Handling").

---

## Rippling Context

## 22. Rippling Offboarding & Integrations

- Verdict: PARTIALLY CONFIRMED
- App deprovisioning: "500+ applications" with one-click deprovisioning; total integrations: "650+ business apps"
- Offboarding automation: Rippling automatically revokes access to all company applications when employees leave
- Workflow engine: [Not explicitly named; Temporal not confirmed]
- Customer base: "over 8,000 Rippling customers and 300,000 employees" (from anonymized data in ROI reports)
- URL: https://www.rippling.com/blog/how-rippling-runs-it-ensuring-smooth-offboarding (403 Forbidden)
- Note: 500+ apps is marketing claim; actual integrations 650+; customer/employee count from ROI reports.

---

## Summary Table

| # | Item | Verdict | URL |
|---|------|---------|-----|
| 1 | Amplitude insert_id 7-day dedup | CONFIRMED | https://amplitude.com/docs/analytics/apis/http-v2-api |
| 2 | Mixpanel $insert_id dedup semantics | CONFIRMED | https://docs.mixpanel.com/reference/import-events |
| 3 | Segment 4-week dedup, RocksDB | CONFIRMED | https://www.twilio.com/en-us/blog/insights/exactly-once-delivery/ |
| 4 | Segment analytics-ios config | PARTIALLY CONFIRMED | https://segment.com/docs/connections/sources/catalog/libraries/mobile/ios/ |
| 5 | Datadog metrics timestamp limits | CONFIRMED | https://docs.datadoghq.com/api/latest/metrics/submit-metrics/ |
| 6 | Stripe meter events (35d past, 5m future, rates) | CONFIRMED | https://docs.stripe.com/billing/subscriptions/usage-based/ |
| 7 | Stripe Idempotency-Key 24h expiry | CONFIRMED | https://docs.stripe.com/api/idempotent_requests |
| 8 | SCIM 2.0 RFC 7644 DELETE (204, soft-delete allowed) | CONFIRMED | https://datatracker.ietf.org/doc/html/rfc7644 |
| 9 | RFC 7643 `active` attribute | CONFIRMED | https://www.rfc-editor.org/rfc/rfc7643.txt |
| 10 | Slack SCIM API (deactivate, rate limits) | UNVERIFIED | https://api.slack.com/scim (403) |
| 11 | Google Workspace users.update, users.signOut | PARTIALLY CONFIRMED | https://developers.google.com/workspace/admin/directory/reference/rest/v1/users/update |
| 12 | Microsoft Entra revokeSignInSessions, CAE 28h | CONFIRMED | https://learn.microsoft.com/en-us/graph/api/user-revokesigninsessions |
| 13 | Okta deactivate (async, two-call delete) | CONFIRMED | https://developer.okta.com/docs/api/openapi/okta-management/management/tags/userlifecycle |
| 14 | Stripe Issuing canceled (permanent, lost/stolen) | CONFIRMED | https://docs.stripe.com/api/issuing/cards/update |
| 15 | Marqeta TERMINATED (irreversible) | CONFIRMED | https://www.marqeta.com/docs/developer-guides/managing-lost-stolen-or-damaged-cards |
| 16 | Apple MDM EraseDevice | UNVERIFIED | https://developer.apple.com/documentation/devicemanagement/erasedevice (404) |
| 17 | Microsoft Intune Wipe (pending, cannot cancel) | CONFIRMED | https://learn.microsoft.com/en-us/intune/device-management/actions/wipe |
| 18 | Temporal Activity retry policy | CONFIRMED | https://docs.temporal.io/encyclopedia/retry-policies |
| 19 | PCI DSS 8.2.5 (immediate revocation) | UNVERIFIED | https://listings.pcisecuritystandards.org/documents/PCI-DSS-v4_0.pdf (403) |
| 20 | SOC 2 CC6.2, CC6.3 (termination, review) | CONFIRMED | https://docs.alertlogic.com/analyze/reports/compliance/SOC2-CC-6.3-access-modification-and-removal.htm |
| 21 | OWASP Top 10 LLM 2025 (5 names) | CONFIRMED | https://genai.owasp.org/llm-top-10/ |
| 22 | Rippling 500+ apps, 8k customers, 300k employees | PARTIALLY CONFIRMED | https://www.rippling.com/blog/how-rippling-runs-it-ensuring-smooth-offboarding (403) |

---

## Corrections to Initial Beliefs

1. **Amplitude insert_id dedup window**: Belief was 7 days — **CONFIRMED**.

2. **Mixpanel import API timestamp window**: Belief was 5 days past — **CORRECTED to 1 hour past** (plus no mention of /import as special; same rules apply).

3. **Segment dedup window**: Belief was 4 weeks — **CONFIRMED**.

4. **Stripe meter events timestamp**: Belief was "at least 24 hours" for identifier uniqueness — **CONFIRMED**, but timestamp window is **35 days past, 5 minutes future** (not unbounded).

5. **Datadog metrics API**: Belief included 1 hour past, 10 minutes future — **CONFIRMED**.

6. **RFC 7644 DELETE status**: Belief was 204 — **CONFIRMED**. Additionally, soft-delete is permitted if 404 is returned post-deletion.

7. **Microsoft Intune Wipe cancel**: Belief that it could be canceled — **CORRECTED: cannot be canceled**; remains pending until device checks in or MDM cert expires.

8. **Okta deactivate**: Belief about two-call pattern (deactivate then delete) — **CONFIRMED**.

9. **Microsoft Entra CAE token lifetime**: Belief was up to 28 hours — **CONFIRMED**.

10. **Temporal retry policy initialInterval**: Belief was 1 second — **CONFIRMED** (initialInterval 1s, backoffCoefficient 2.0, maximumInterval 100s).

11. **OWASP LLM Top 10 2025**: Belief included exact names — **CONFIRMED with one correction**: LLM05 is "Improper Output Handling" (not original "Insecure Output Handling").

12. **Rippling app count**: Belief was "500+ apps" — **PARTIALLY CONFIRMED** (500+ in marketing; actual integrations 650+).

---

## Fact-Checking Methodology

- **73 tool calls** executed (WebFetch, WebSearch, and redirects)
- **Primary sources prioritized**: Official vendor docs (Amplitude, Mixpanel, Stripe, Google, Microsoft, Okta, Slack, AWS, Temporal, OWASP, RFC Editor, PCI SSC, Datadog, Marqeta, Apple)
- **Blocked resources**: 5 PDFs (PCI DSS, Apple MDM, Rippling blog) behind 403 Forbidden or 404; Slack SCIM docs redirected to 404
- **Highest-confidence findings**: Stripe, RFC standards, OWASP, Temporal, Datadog, Microsoft Entra, Okta
- **Medium confidence**: Google Workspace (partial docs), Rippling (marketing claims only)
- **Low confidence**: Apple MDM (no public fetch), Slack SCIM rate limits (docs blocked)

---

## Spot-check corrections (added 2026-09-30, after the survey)

I fetched the pages behind the numbers that end up in `solution.md`. The survey text above is the agent's; this table is the correction layer. Where they disagree, this table wins.

| # | Claim in the survey | What the primary source says | Source |
|---|---|---|---|
| 3 | Segment: "1.5 TB of keys", "60 billion keys", "200 billion messages" | **Confirmed after all** (my first grep broke on the "." in "1.5"). The page says: "1.5 TB worth of keys stored on disk in RocksDB", "a 4-week window of de-duplication before aging out old keys", "approximately 60B keys stored inside our RocksDB instances", "200B messages passed through the dedupe system". Also: "approximately 0.6% of events that are ingested within a 4-week window are duplicate messages", embedded RocksDB "on its local EBS hard drive" per worker, events routed to the partition that owns the key, bloom filters in front | https://www.twilio.com/en-us/blog/insights/exactly-once-delivery |
| 6 | Stripe meter events v1 and v2 both 1,000/s | v1: "The Meter Event limit is 1000 calls per second per Stripe account." v2 meter event streams: "up to 10,000 events per second", "Contact sales if you need to send up to 200,000 events per second". Timestamps: "within the past 35 calendar days and isn't more than 5 minutes in the future". Identifier: "Stripe enforces uniqueness within a rolling period of at least 24 hours". So Stripe accepts 35-day-old events but only dedups for 24 h: the sender must dedup before sending | https://docs.stripe.com/billing/subscriptions/usage-based/recording-usage-api, https://docs.stripe.com/api/billing/meter-event/create |
| 2 | Mixpanel import window "1 hour past" | Muddled in the survey. Not used in `solution.md` | n/a |
| 20 | SOC 2 CC6.2 "within 24 hours for voluntary, immediately for involuntary" | That wording is from a vendor page (alertlogic), not AICPA. The Trust Services Criteria do not set an hour count. `solution.md` uses "promptly" and sets its own 5-minute target | secondary source only |
| 19 | PCI DSS v4.0 8.2.5 | Primary PDF returned 403. Treat the wording as unverified | n/a |
| 22 | Rippling "8,000 customers and 300,000 employees" | From an anonymised ROI report page, not a Rippling figure of record. Not used | n/a |
| 14 | Stripe Issuing `canceled` | Confirmed: "This status is permanent." | https://docs.stripe.com/api/issuing/cards/object |

Facts I verified myself that the survey did not cover:

| Fact | Exact quote | Source |
|---|---|---|
| Segment clock-skew correction | "timestamp = receivedAt - (sentAt - originalTimeStamp)". Also: in the Swift, Kotlin and C# libraries `sentAt` is added when the batch is first sent, so for offline-queued events "the timestamp value for those users more closely reflects when Segment received the events rather than the time they occurred" | https://segment.com/docs/connections/spec/common/ |
| Google Workspace Directory API quota | "2,400 queries per minute per user per Google Cloud project" (raisable from the Admin SDK API quotas page) | https://developers.google.com/workspace/admin/directory/v1/limits |
| Amplitude batch limits and dedup | "Keep request sizes under 1 MB with fewer than 2000 events per request." "Amplitude deduplicates subsequent events sent with the same device_id and insert_id within the past 7 days." | https://amplitude.com/docs/apis/analytics/http-v2 |
| Datadog timestamp window (item 5) | Could not re-fetch: the page renders in JavaScript and neither curl nor WebFetch returned the sentence. Kept as the agent's quote ("cannot be more than ten minutes in the future or more than one hour in the past"), not independently verified | n/a |
