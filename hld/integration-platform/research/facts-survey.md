# Facts survey: employee identity and integration platform (Rippling style)

Date: 2026-10-16

Three-line summary:
1. SCIM 2.0 gives a standard create, patch, deactivate and filter API, but rate limits, batch support and ETags differ per vendor, so the platform must discover and adapt per connector.
2. Vendor limits are per app, per tenant, per user or per account, and most signal overload with 429 plus Retry-After. Google, Graph, GitHub, Jira, Zoom and Slack each use a different scope.
3. Industry provisioning engines (Entra, Okta) use watermark-based incremental sync, retry with backoff, quarantine when error rates spike, and accidental-deletion circuit breakers. These are the design patterns to copy.

## Spot-check notes (conflicting or fragile numbers)

- GitHub App installation cap: the general text says "The rate limit cannot increase beyond 12,500 requests per hour." The Enterprise Cloud text says "has a rate limit of 15,000 requests per hour." These are two different tiers, not a true conflict. Recorded as PARTIAL.
- Slack Web API tiers: the page quotes "at least 20 requests per minute" for Tier 2 and "larger number" for Tier 3, but the roughly 50 and 100 per minute figures are my reading of the tier names, not verbatim text. Recorded as PARTIAL.
- Okta: the only per-minute users number on the fetched page is an illustrative example ("a quota of 1000 requests per minute") for an org-wide bucket `/api/v1/users/*`. It is not a published table value. Recorded as PARTIAL.
- Google Directory: the limits page gives 2,400 queries per minute per user per project. The users.insert page gives no quota text. The "10 users per domain per second" figure is specific to creating users. Not a conflict, but scope differs.
- Stripe retry window: "up to three days" in live mode, confirmed. The sandbox note says "three times over the course of a few hours." Different modes, not a conflict.
- Entra incremental interval: the user's belief of "~40 minutes" is NOT confirmed. The Entra page says the interval is "defined in the tutorial specific to each application." Also, the quarantine page says quarantine cycles run "once per day." Recorded as UNVERIFIED for the 40 min figure.
- Standard Webhooks retry schedule: the spec example table (immediate, 5 s, 5 min, 30 min, 2 h, 5 h, 10 h, 14 h, 20 h, 24 h) came from a summary of the spec and was not quoted verbatim. The spec text says only "retry delivery following a retry schedule spanning multiple days, with an exponential backoff." Treated as PARTIAL.
- Standard Webhooks 5 minute tolerance: NOT found in the fetched spec text. The spec only says "some allowable tolerance." The 5 minute value is Stripe's default, not the Standard Webhooks default. Recorded as a conflict with the user's brief.
- Microsoft Graph `$batch` limit of 20 requests: NOT found on the throttling page I fetched. Recorded as UNVERIFIED.
- Editor spot-check (2026-10-17, from the full plain-text RFCs at https://www.rfc-editor.org/rfc/rfc7644.txt and https://www.rfc-editor.org/rfc/rfc9110.txt):
  - RFC 7644 section 3.12 error table: `412 (Precondition Failed)` for PUT, PATCH, DELETE: "Failed to update. Resource has changed on the server." So row 13 is CONFIRMED.
  - RFC 7644 section 3.14: "Service providers MAY support weak ETags as the preferred mechanism for performing conditional retrievals and ensuring that clients do not inadvertently overwrite each other's changes". ETags are optional.
  - RFC 7644 section 3.12 table, 413 row, gives the example `{"maxOperations": 1000,"maxPayloadSize": 1048576}` for Bulk. Example values, not a mandated limit.
  - RFC 7644 section 3.14 example create sends both `userName` and `externalId` in the POST body.
  - RFC 9110 section 10.2.3: "The Retry-After field value can be either an HTTP-date or a number of seconds to delay after receiving the response." So row 68 is CONFIRMED.

---

## 1. SCIM 2.0 (RFC 7643, RFC 7644)

Sources: https://www.rfc-editor.org/rfc/rfc7644 and https://www.rfc-editor.org/rfc/rfc7643

- `id` vs `externalId`:
  - `id`: "The value of the "id" attribute is always issued by the service provider and MUST NOT be specified by the client." (RFC 7643 section 3.1)
  - `externalId`: "The value of the "externalId" attribute is always issued by the provisioning client." (RFC 7643 section 3.1)
  - "The service provider MUST always interpret the externalId as scoped to the provisioning domain." (RFC 7643 section 3.1)
  - Design take: store the provider `id` for every later PATCH or DELETE. Use your own employee ID as `externalId`.
- `userName`:
  - "This identifier MUST be unique across the service provider's entire set of Users." (RFC 7643 section 4.1.1)
  - Attribute is "REQUIRED and is case insensitive." (RFC 7643 section 4.1.1)
  - Note: the schema `uniqueness` keyword for `server` says only "SHOULD be unique within the context of the current SCIM endpoint (or tenancy)." (RFC 7643 section 7). MUST vs SHOULD is a real gap to call out.
- `active`:
  - "A Boolean value indicating the user's administrative status." (RFC 7643 section 4.1.1)
  - Deactivation is `active = false`, not DELETE. Entra sends `active` false on disable (see section 4).
- Create and conflict:
  - "an HTTP response SHALL be returned with HTTP status code 201 (Created)." (RFC 7644 section 3.3)
  - "MUST return HTTP status code 409 (Conflict) with a "scimType" error code of "uniqueness"" (RFC 7644 section 3.3)
  - POST create idempotency: NOT defined by SCIM. No idempotency key appears in the sections fetched. Use upsert keyed on `externalId` or a `filter` lookup before create. [UNVERIFIED: full section 3.3 text not fully read beyond the quoted sentences.]
- PATCH:
  - "HTTP PATCH is an OPTIONAL server function" (RFC 7644 section 3.5.2)
  - "A PATCH request, regardless of the number of operations, SHALL be treated as atomic." (RFC 7644 section 3.5.2)
  - add: "The operation MUST contain a "value" member whose content specifies the value to be added." (section 3.5.2.1)
  - remove without path: "the operation fails with HTTP status code 400 and a "scimType" error code of "noTarget"." (section 3.5.2.2)
  - replace on a single-value attribute: "the attributes value is replaced." (section 3.5.2.3)
  - Entra's real-world behaviour differs: Entra sends `"op": "Replace"` with string `"False"` by default, and `"op": "replace"` with boolean `false` only when a compliance flag is set. Source: https://learn.microsoft.com/en-us/entra/identity/app-provisioning/application-provisioning-config-problem-scim-compatibility
  - Group member removal in Entra with the flag: `members[value eq "<id>"]`. Without the flag it sends a `members` array value. Same source.
- Group member PATCH: covered by the same PATCH rules. Entra note above is the practical example.
- Filter syntax:
  - "Attribute names and attribute operators used in filters are case insensitive." (RFC 7644 section 3.4.2.2)
  - "Each expression MUST contain an attribute name followed by an attribute operator and optional value." (RFC 7644 section 3.4.2.2)
  - Example you will use: `filter=userName eq "alice@example.com"`. [UNVERIFIED: exact example string not quoted from the RFC excerpt; the syntax is standard.]
- Pagination:
  - startIndex: "The 1-based index of the first query result." (RFC 7644 section 3.4.2.4)
  - count: "the service provider MUST NOT return more results than specified" (section 3.4.2.4)
  - count default: "If unspecified, the maximum number of results is set by the service provider." (section 3.4.2.4)
  - No fixed maximum page size in the RFC. Each vendor sets one. [UNVERIFIED for specific vendors here.]
- ETags and versioning:
  - `meta.version`: "This value must be the same as the entity-tag (ETag) HTTP response header." Versioning is optional. (RFC 7643 section 3.1)
  - Weak tag: "the origin server MUST mark the "version" (entity-tag) as weak by prefixing its opaque value" with `W/`. (RFC 7643 section 3.1)
  - If-Match example appears in RFC 7644 section 3.5.1 (`If-Match: W/"a330bc54f0671c9"` on PUT).
  - 412 on mismatch: NOT verified in the fetched text (section 3.12 was cut off). [UNVERIFIED]
- Bulk:
  - "The SCIM bulk operation is an optional server feature" (RFC 7644 section 3.7)
  - failOnErrors and bulk maximums are in section 3.7.4, cut off in my fetch. [UNVERIFIED]
- ServiceProviderConfig:
  - Filter support is advertised on `/ServiceProviderConfig` (RFC 7644 section 3.4.2.2 mention). Full capability fields (etag, patch, bulk, maxResults) are in section 4 of RFC 7644, not read. [UNVERIFIED for field names.]
- Entra's published SCIM quirks (useful for connector tests):
  - Entra requires `/scim` in the endpoint root, and used the older `customappsso` job until Dec 2018. Source: https://learn.microsoft.com/en-us/entra/identity/app-provisioning/application-provisioning-config-problem-scim-compatibility

## 2. Vendor rate limits and throttling

### 2a. Google Workspace Admin SDK Directory API
- Source: https://developers.google.com/workspace/admin/directory/v1/limits
- "The default value set in the Google Cloud console is 2,400 queries per minute per user per Google Cloud project." Scope: per user per project.
- "You cannot create more than 10 users per domain per second using the Directory API."
- "You cannot create/update more than 1 organizational unit per customer per second using the Directory API."
- Mobile device limits: 20 action requests/s, 20 delete/s, 10 get/s, 10 list/s.
- "This limit is per Google Workspace account, not per API client or per user." (applies to a limit on the page; the exact limit it refers to is not clear from the excerpt. PARTIAL.)
- Per-day quota: not stated on the page. [UNVERIFIED]
- Creation response codes (users.insert): 200 created, 202 invited, 409 "a conflicting account exists so the user wasn't created." Source: https://developers.google.com/workspace/admin/directory/reference/rest/v1/users/insert
- Propagation: "A mutate call right after creation may fail with a propagation-related error." Retry after time. Same source.
- Batch requests: the limits page did not quote batch numbers. [UNVERIFIED]

### 2b. Slack
- SCIM rate limit numbers: NOT found. Slack's SCIM API is for Enterprise Grid and its numbers were not fetched. [UNVERIFIED]
- Web API tiers, source https://docs.slack.dev/apis/web-api/rate-limits/:
  - Tier 1: "Access tier 1 methods infrequently. A small amount of burst behavior is tolerated." (roughly 1/min)
  - Tier 2: "Most methods allow at least 20 requests per minute, while allowing for occasional bursts of more requests."
  - Tier 3: "Tier 3 methods allow a larger number of requests." (roughly 50/min, PARTIAL)
  - Tier 4: "Enjoy a large request quota for Tier 4 methods, including generous burst behavior." (roughly 100/min, PARTIAL)
  - Special tier: "Rate limiting conditions are unique for methods with this tier."
- 429 with: "a `Retry-After` HTTP header containing the number of seconds until you can retry."
- Scope: "Your app's requests to the Web API are evaluated per method, per workspace."
- users.admin is not public per the brief. [UNVERIFIED: not checked.]

### 2c. Microsoft Graph
- Source: https://learn.microsoft.com/en-us/graph/throttling
- "When a throttling threshold is exceeded, Microsoft Graph: Limits any further requests from that client app for some time. Returns HTTP status code 429 Too Many Requests and the requests fail. Returns a suggested wait time in the response header of the failed request."
- Scope: "A large number of requests across all applications in a tenant." and "A large number of requests from a particular application across all tenants."
- Retry: "Backing off requests using the Retry-After delay is the fastest way to recover from throttling because Microsoft Graph continues to log resource usage while a client is being throttled."
- No Retry-After: "we recommend implementing an exponential backoff retry policy."
- Avoid polling: "use change tracking and change notifications when available."
- Batch: "Requests in a batch are evaluated individually against throttling limits and if any request exceeds the limits, it fails with a status code of 429... The batch itself succeeds with a status code of 200 (OK)."
- `$batch` max of 20 requests: NOT found on the throttling page. [UNVERIFIED]
- Per-resource numbers live on the "Service-specific limits" page (not fetched). [UNVERIFIED]

### 2d. Okta Management API
- Source: https://developer.okta.com/docs/reference/rl-global-mgmt/ and https://developer.okta.com/docs/reference/rate-limits/
- Users bucket example: "there exists a bucket with org-wide scope for /api/v1/users/* with a quota of 1000 requests per minute" (illustrative, PARTIAL).
- 429: "further requests are rejected with an HTTP 429 Too Many Requests response until the quota resets."
- Headers: X-Rate-Limit-Limit, X-Rate-Limit-Remaining, X-Rate-Limit-Reset are NOT named on the fetched pages. The pages say "by inspecting the rate limiting headers included in API responses." [UNVERIFIED names.]
- Per-endpoint bucket table: in the Rate Limit Dashboard, not fetched. [UNVERIFIED]

### 2e. GitHub REST API
- Source: https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api
- Installation tokens: "use the installation's minimum rate limit of 5,000 requests per hour."
- Enterprise Cloud: "has a rate limit of 15,000 requests per hour."
- Scaling: over 20 repositories: "another 50 requests per hour for each repository."
- Cap: "The rate limit cannot increase beyond 12,500 requests per hour." (conflict note above)
- Secondary limits:
  - "No more than 100 concurrent requests are allowed."
  - "No more than 900 points per minute are allowed for REST API endpoints."
  - "No more than 90 seconds of CPU time per 60 seconds of real time is allowed."
  - "no more than 500 content-generating requests per hour are allowed."
  - "No more than 2,000 OAuth access token requests per hour are allowed for GitHub Apps and OAuth apps."
- Signals: "If you exceed your primary rate limit, you will receive a 403 or 429 response." "the x-ratelimit-remaining header will be 0." `retry-after`: "you should not retry your request until after that many seconds has elapsed."
- "The x-ratelimit-* headers are the authoritative source for your current rate limit status."
- GitHub SCIM "not more than 1,000 users per hour" advice: seen only in a search summary, not fetched. [UNVERIFIED]

### 2f. Zoom
- Source: https://developers.zoom.us/docs/api/rate-limits/
- Categories: "Light, Medium, Heavy, or Resource-intensive."
- Free plan daily: Light 6,000, Medium 2,000, Heavy 1,000, Resource-intensive 30,000.
- Pro: "30,000 requests/day for heavy and resource-intensive APIs"
- Business+: "60,000 requests/day for heavy and resource-intensive APIs"
- Scope: "Rate limits are applied at the account level." "shared by users for all apps installed on the account." Important: a Zoom account-level limit is shared across all apps, so a noisy neighbour can starve your connector.
- 429: "When you exceed a rate limit, the API request will fail and return a HTTP 429 status code."

### 2g. Atlassian Jira Cloud
- Source: https://developer.atlassian.com/cloud/jira/platform/rate-limiting/
- "Your app shares a single 65,000 point hourly quota across all tenants."
- "Your app receives a separate hourly quota for each tenant, with limits varying by their edition."
- "Per-tenant rate limits are capped at 500,000 points per hour for Standard, Premium, and Enterprise editions."
- 429: "All requests are denied until the next hourly reset." Retry-After: "Only returned with 429 responses."
- X-RateLimit-Reset is an ISO 8601 timestamp; X-RateLimit-NearLimit true at under 20% remaining.

### 2h. Salesforce daily API allocation
- Source tried: developer.salesforce.com app limits cheatsheet. Returned HTTP 403 twice. [UNVERIFIED. Reason: 403 from WebFetch.]

### 2i. HubSpot per-app limits
- Source tried: developers.hubspot.com usage-details. Returned HTTP 404. [UNVERIFIED. Reason: 404.]

## 3. Change feeds and push notifications

### 3a. Microsoft Graph delta query (users)
- Source: https://learn.microsoft.com/en-us/graph/delta-query-users
- Initial call: `GET /users/delta`. Follow `@odata.nextLink` until `@odata.deltaLink`. "Save the deltatoken and use it in the subsequent request URL."
- Deletes: "@removed" annotation. "reason": "changed" for soft delete, "reason": "deleted" for permanent delete.
- "Only properties included in $select are tracked for changes."
- Replication delay: "This request might have replication delays for users that were recently created, updated, or deleted. Retry the @odata.nextLink or @odata.deltaLink after some time to retrieve the latest changes."
- Validity: how long a deltaLink stays valid is NOT stated on this page. [UNVERIFIED. Check delta-query-overview.] Design take: treat an invalid token as a full resync.

### 3b. Google Directory push notifications (watch)
- Source: https://developers.google.com/workspace/admin/directory/v1/guides/push
- Delivery: "Whenever a watched resource changes, the Directory API sends a notification message as a POST request to that URL."
- Expiry: a `ttl` (seconds) or `expiration` (ms) can be set. "the more restrictive value is used." Default not stated. [UNVERIFIED default.]
- Renewal: "Currently, there's no automatic way to renew a notification channel." So you must re-`watch` on a timer.
- Retry: retries for 500, 502, 503 and 504 when using the client library. "Every other return status code is considered to be a message failure."
- Guarantee: not stated. Treat as best effort and run periodic reconciliation.

### 3c. Okta Event Hooks
- Source: https://developer.okta.com/docs/concepts/event-hooks/
- "Events are delivered at least once." Also "Okta delivers events on a best-effort basis."
- Duplicates and reordering possible. Dedupe on `eventId`, order by `published`.
- "There's no guarantee of maximum delay between event occurrence and delivery."
- Retry: "Okta attempts at most one retry." 5xx retried, 4xx not.
- Timeout: "it enforces a default timeout of three seconds."

### 3d. Slack Events API (user_change, team_join)
- Source: https://docs.slack.dev/apis/events-api/
- "Your app should respond to the event request with an HTTP 2xx within three seconds."
- Retries: "a failed request up to 3 times in a gradually increasing timetable." First retry almost immediately, second after one minute, third after five minutes.
- Header `X-Slack-Retry-Num` (values 1 to 3) and `X-Slack-Retry-Reason` (timeout, non-200, etc.).
- `user_change` and `team_join` event names: NOT in the fetched content. [UNVERIFIED]
- Design take: ack fast, enqueue, dedupe on event ID because retries can deliver twice.

## 4. Provisioning engines in the industry (highest value)

### 4a. Microsoft Entra ID provisioning service
Sources: https://learn.microsoft.com/en-us/entra/identity/app-provisioning/how-provisioning-works , https://learn.microsoft.com/en-us/entra/identity/app-provisioning/application-provisioning-quarantine-status , https://learn.microsoft.com/en-us/entra/identity/app-provisioning/accidental-deletions , https://learn.microsoft.com/en-us/entra/identity/app-provisioning/application-provisioning-when-will-provisioning-finish-specific-user

- Cycles:
  - Initial cycle: "Query all users and groups from the source system" then match on matching attributes, create or update, then "Persist a watermark at the end of the initial cycle."
  - Incremental cycle: "Query the source system for any users and groups that were updated since the last watermark was stored." Then "Persist a new watermark at the end of the incremental cycle."
  - Interval: "The provisioning service continues running back-to-back incremental cycles indefinitely, at intervals defined in the tutorial specific to each application." The 40 minute figure is NOT confirmed. [UNVERIFIED]
  - Source of change: the service uses "the delta query to track changes in Microsoft Graph data."
- Matching: a matching attribute, for example userPrincipalName mapped to userName, is used to find an existing target user. Initial and incremental both use it.
- Scoping: "Sync only assigned users and groups" or attribute scoping filters. "Nested groups. The Microsoft Entra user provisioning service can't read or provision users in nested groups."
- Deprovisioning: "For SCIM applications, a disable is a request to set the active property to false on a user." A hard delete happens "30 days after they're soft-deleted."
- Errors and retries: "If an error in the target system prevents an individual user from being added, updated, or deleted in the target system, the operation is retried in the next sync cycle. The errors are continually retried, gradually scaling back the frequency of retries."
- Common failures: required attribute missing, or a unique constraint conflict in the target system.
- Quarantine:
  - Triggered when "most or all of the calls that are made against the target system consistently fail" (example: invalid admin credentials).
  - Escrow thresholds: "more than 40% of provisioning events fail, or there are more than 40,000 failures." Minimum evaluation point: "5,000 failures are the minimum to start evaluating." Absolute: "an absolute threshold of 60,000 failures."
  - Retry after failure: "the first retry will happen in 6 hours." Then "12 hours after the first failure," then "24 hours after the first failure," then every 24 hours.
  - Retries go on "for 28 days after the first failure after which the escrow entry is removed and the job is disabled."
  - In quarantine: "the frequency of incremental cycles is gradually reduced to once per day."
  - Exit: "The provisioning job is removed from quarantine after all errors are fixed and the next sync cycle starts."
- Accidental deletions prevention:
  - "Anything above the threshold that you set requires an admin to explicitly allow the processing of the deletions."
  - "When the deletion threshold is met, the job goes into quarantine, and a notification email is sent."
  - "It's evaluated each cycle."
  - Default threshold value: NOT found in the page text. [UNVERIFIED]
  - Example test threshold given: "for example 3".
- Throughput:
  - Initial cycle formula, for "Sync assigned user and groups only": "Minimum minutes = 0.01 x [Number of assigned users, groups, and group members]" and "Maximum minutes = 0.08 x [...]".
  - "Some target systems implement request rate limits and throttling... an app that receives too many requests too fast might slow its response rate or close the connection."
  - "Sync jobs for which all users are created for the first time take about twice as long as sync jobs for which all users are matched to existing users."
- Gallery vs custom rate limit: Microsoft Q&A says gallery apps have a minimum of 25 requests per second per job. This is from a Q&A answer, not primary. [UNVERIFIED]

### 4b. Okta Lifecycle Management and SCIM push
- Not fetched in this pass beyond the Event Hooks page. Matching on import, push groups, and outbound rate limits: [UNVERIFIED]. Next step: developer.okta.com or help.okta.com "Provisioning" pages.

### 4c. Google Workspace and AWS IAM Identity Center SCIM limits
- Google: see section 2a. Google Cloud Identity SCIM-specific limit: [UNVERIFIED].
- AWS IAM Identity Center: not fetched. [UNVERIFIED]

### 4d. Unified-API vendors (Merge, Finch, Workato)
- Not fetched. Not used as evidence. [UNVERIFIED]

### 4e. Kubernetes controllers (reference for level-triggered reconciliation)
- Source: https://kubernetes.io/docs/concepts/architecture/controller/
- "In Kubernetes, controllers are control loops that watch the state of your [cluster], then make or request changes where needed. Each controller tries to move the current cluster state closer to the desired state."
- "The important point here is that the controller makes some changes to bring about your desired state, and then reports the current state back to your cluster's API server."
- "Your cluster could be changing at any point as work happens and control loops automatically fix failures."
- Level-triggered vs edge-triggered wording: NOT found in the fetched text. [UNVERIFIED]
- client-go workqueue, source: https://pkg.go.dev/k8s.io/client-go/util/workqueue
  - "AddRateLimited adds an item to the workqueue after the rate limiter says it's ok"
  - "if an item is added multiple times before it can be processed, it will only be processed once."
  - "a single item will not be processed multiple times concurrently"
  - "if it has been marked as dirty again while it was being processed, it will be re-added to the queue for re-processing."
- Design take: key the queue by `(tenant, app, employee)`. Coalesce many change events into one reconcile. Requeue failures with rate-limited backoff.

## 5. OAuth credential lifecycle

- RFC 9700 (OAuth 2.0 Security BCP): https://www.rfc-editor.org/rfc/rfc9700.html
  - Section 2.2.2: "Refresh tokens for public clients MUST be sender-constrained or use refresh token rotation as described in Section 4.14."
  - Section 4.14 text (rotation and reuse detection): NOT read. The fetched page was truncated. [PARTIAL; reuse detection behaviour is UNVERIFIED in quoted form.]
- RFC 6749 refresh token basics: not fetched. [UNVERIFIED]
- Google OAuth refresh tokens: https://developers.google.com/identity/protocols/oauth2
  - "There is currently a limit of 100 refresh tokens per Google Account per OAuth 2.0 client ID."
  - "If the limit is reached, creating a new refresh token automatically invalidates the oldest refresh token without warning."
  - Unused: "The refresh token has not been used for six months."
  - Testing apps: "is issued a refresh token expiring in 7 days"
  - Password change: applies if the refresh token has Gmail scopes.
  - Failure: "the call will fail with an error type invalid_grant" for session control policies.
- Microsoft refresh token lifetime: not fetched. [UNVERIFIED]
- Salesforce and Xero rotating refresh tokens: not fetched (Salesforce 403). [UNVERIFIED]
- Two workers refreshing the same rotating token at once: this is a known failure mode. The second refresh uses a token the server has already rotated. With reuse detection, the server may revoke the whole token family. Mitigation: single-flight refresh per (tenant, app) with a lock, and a durable store for the newest refresh token. Design take only, not sourced. [UNVERIFIED: the revocation behaviour is from RFC 9700 section 4.14, which was not read.]

## 6. HTTP retry semantics

- RFC 9110 Retry-After: section 10.2.3 per the table of contents. Quoted text NOT read. [UNVERIFIED text]. Source: https://www.rfc-editor.org/rfc/rfc9110.html
- RFC 9110 idempotent methods: section 9.2.2 per TOC. Quoted text NOT read. [UNVERIFIED text]
- RFC 6585 (429 Too Many Requests): NOT fetched. [UNVERIFIED]
- IETF RateLimit header draft: https://datatracker.ietf.org/doc/draft-ietf-httpapi-ratelimit-headers/
  - Draft-ietf-httpapi-ratelimit-headers-11, dated 23 May 2026, "Standards Track" intent, NOT an RFC yet.
  - "RateLimit-Policy" response header field, "The "RateLimit-Policy" response header field is a non-empty List."
  - "q" (quota) parameter REQUIRED. "w" (window) parameter OPTIONAL.
  - "RateLimit" header: "r" (remaining) REQUIRED and "t" (time) OPTIONAL.
  - Vendors use their own X-RateLimit-* names today (Jira, GitHub). The draft is not yet a standard.

## 7. Webhooks

### 7a. Standard Webhooks
- Spec source used: https://github.com/standard-webhooks/standard-webhooks/blob/main/spec/standard-webhooks.md (the standardwebhooks.com/spec URL returned 404).
- Headers: "All of the headers should be prefixed with webhook- and follow the exact naming as below." Names: `webhook-id`, `webhook-timestamp`, `webhook-signature`.
- `webhook-timestamp`: "integer unix timestamp (seconds since epoch)."
- Signature header: "a space delimited list of signatures associated with this webhook."
- Signed content: "The content to be signed is therefore: msg_id.timestamp.payload."
- Tolerance: "Make sure to verify the webhook-timestamp header has a timestamp that is within some allowable tolerance..." The spec does NOT say 5 minutes. [conflict with brief; PARTIAL]
- Retry: "It's recommended to retry delivery following a retry schedule spanning multiple days, with an exponential backoff." (Example table, PARTIAL.)
- Security: "Every webhook implementation needs to protect themselves and their users from SSRF, spoofing, and replay attacks." (source: https://www.standardwebhooks.com/ )

### 7b. Stripe
- Source: https://docs.stripe.com/webhooks
- "Stripe attempts to deliver events to your destination for up to three days with an exponential backoff in live mode."
- Manual resend: "This works for up to 15 days after the event creation." (Dashboard) and "This works for up to 30 days after the event creation." (CLI)
- Ordering: "Stripe doesn't guarantee the delivery of events in the order that they're generated."
- Duplicates: "Webhook endpoints might occasionally receive the same event more than once."
- Dedupe: "Track event IDs to identify duplicate deliveries instead." Do not use `created` for ordering: "Snapshot events record created in seconds, so distinct events can share a timestamp."
- Signature: "Our libraries have a default tolerance of 5 minutes between the timestamp and the current time." Do not use 0 ("disables the recency check entirely").
- Header: `Stripe-Signature` with `t=` and `v1=`. Signed payload is timestamp, ".", raw JSON body.
- Timeout: "Your endpoint must quickly return a successful status code (2xx) before any complex logic that could cause a timeout." Stripe's table calls out timeouts but does not state a number in the text I read.
- Endpoints: "You can register up to 16 event destinations with Stripe."
- Secret roll: "delay its expiry for up to 24 hours".

### 7c. GitHub webhook deliveries
- Source: https://docs.github.com/en/webhooks/using-webhooks/handling-webhook-deliveries
- "Your server should respond with a 2XX response within 10 seconds of receiving a webhook delivery."
- Automatic redelivery: NOT stated on the page. [UNVERIFIED]
- Manual redelivery: "You can also redeliver a previous webhook delivery."

### 7d. Slack
- See section 3d (3-second ack, 3 retries).

## 8. Rippling

- App Shop integration count:
  - rippling.com/platform/integrations: "650+ integrations" (quoted from search summary, not fetched directly; date not shown). Source: https://www.rippling.com/platform/integrations
  - rippling.com/rippling-it/integrations: "600+" (search summary). Source: https://rippling.com/rippling-it/integrations
  - The app-shop URL (https://www.rippling.com/app-shop) returned an error page with no count. [UNVERIFIED for date]
  - A third-party review says "over 500 integrations." Not a primary source; do not cite as fact.
- Provisioning method (SCIM vs API, supergroups, attribute rules): NOT verified from a Rippling primary source. Rippling's developer portal returned empty content. [UNVERIFIED]
- Partner developer platform (third-party docs only):
  - OAuth 2.0 via App Listing, scopes like `employees:read departments:read`, token URL `app.rippling.com/api/o/token/`. Source: https://prismatic.io/docs/components/rippling (third-party, PARTIAL)
  - Webhooks restricted for App Shop integrations; partner apps can provide a webhook URL. Source: search summary of docs.blinkops.com (third-party, PARTIAL). Merge help says a webhook token is supplied by the Rippling contact. Source: https://help.merge.dev/articles/9265388-rippling-how-do-i-set-up-my-integration (third-party).
  - Partner review: "if you are rejected during either the pre-vet review or the Rippling App Shop application, you, unfortunately, won't be able to integrate with Rippling via Merge or otherwise." (third-party, Merge)
- Architecture (engineering blog or Temporal case study):
  - Rippling engineering blog post on Temporal or multi-tenancy: NOT found. [UNVERIFIED]
  - Temporal customer story: https://temporal.io/in-use/re-building-async-processing-at-rippling-using-temporal . Quote: "At our current scale, we see wear and tear - owing to maintenance challenges, like missed executions, non-stateful retries, observability. We find Temporal to be a right fit here on our use-cases." Rippling's in-house job system is named ETA and integrates with Django. (Customer story, PARTIAL: vendor-written summary.)
  - Temporal multi-tenant guidance (not Rippling-specific): https://docs.temporal.io/production-deployment/multi-tenant-patterns recommends per-tenant task queues in a shared namespace. Summary from search, PARTIAL.
- Approximate customer count with date: NOT found. [UNVERIFIED]

## 9. Interview evidence

Searches run: several, including "design an app provisioning system", "identity sync", "integration platform", "third-party rate limit", across Rippling, Stripe, Okta, Plaid, Merge, Workday, Gusto, Deel. PracHub, LeetCode Discuss, Glassdoor-visible pages, DesignGurus and Hello Interview were NOT fetched in this pass.

Result count: 1 candidate-style post (Blind), 0 Rippling/Stripe/Okta/Plaid/Merge/Workday/Gusto/Deel hits, and several guide or prep pages that do not count.

| # | Company | Level | Date | Round | Prompt sentence | URL | Type |
|---|---|---|---|---|---|---|---|
| I1 | Not stated | Not stated | Not stated | Not stated | "a system accepting around 100 requests per second must call a third-party API capped at 100 per second. The poster asks how to avoid dropping users when that API gives no explicit rate-limit signal." | https://www.teamblind.com/post/system-design-interview-question-3rd-party-api-lwgs3pxm | Candidate-style post, company NOT confirmed. Use as a prompt idea only. |

Guide or prep pages (NOT candidate evidence): Scoutify (ID.me, Saviynt) at https://scoutify.com/companies/idme/interview/ and https://scoutify.com/companies/saviynt/interview/ ; a Dataford question for Ping Identity at https://dataford.io/questions/how-would-you-design-a-high-throughput-low-latency-identity-provider-system-for-ping-identity (question bank, not verified); a Glassdoor page for Modular Open Source Identity Platform (design-role, not system design).

Gap: no PracHub, LeetCode Discuss, Hello Interview or DesignGurus page was checked for this prompt. Next step: targeted searches with `site:` filters on those sites.

## Design takeaways (from the facts above)

- Store the provider `id` and your own `externalId`. Never rely on `userName` alone as a key, because SCIM only says SHOULD for server uniqueness on some schemas.
- Deactivate with `active=false`. Hard delete only after a grace period (Entra uses 30 days).
- Per-connector token bucket. Limits differ by scope: per user per project (Google), per method per workspace (Slack), per tenant plus shared global (Jira), per account shared by all apps (Zoom).
- Use Retry-After first, then exponential backoff. Avoid immediate retries (Graph says so explicitly).
- Use watermark or delta sync for inbound changes (Graph delta, Entra watermark). Add periodic full reconciliation because push channels expire or are best effort (Google watch, Okta at-least-once with one retry).
- Quarantine: when a connector's failure rate is high, stop hammering it, lower frequency, and alert. Entra's example: 40% failure rate or 40,000 failures.
- Accidental deletion breaker: pause when deactivations exceed a threshold in a cycle, and require admin allow.
- Webhook egress: sign, timestamp, dedupe on event ID, handle out-of-order and duplicates.
- Refresh tokens: single-flight refresh per connection. Persist the newest rotating token before use.

## 10. Gap fill (2026-10-17)

Scope: the coordinator's priority list. Quotes come from tool output. Where a fetch was truncated, the sentence says so. Status changes are listed in the final table (rows 13, 14, 23, 26, 28, 41, 55, 58, 63, 70, 81, 82, 91 to 96).

### 10.1 Slack SCIM API rate limits (priority 1)
- Source: https://docs.slack.dev/reference/scim-api/rate-limits
- "In your organization, Slack applies per-minute rate limits across all SCIM endpoints in certain sets."
- "Each call to any of the endpoints in that set counts toward the **same** rate limit."
- "unlike many of the other Slack API rate limits, the limits below apply to all SCIM apps in an org, not on a per-app basis."
- Figures (from the tables, PARTIAL):
  - Org-wide writes (POST, PUT, PATCH, DELETE): 600 per minute.
  - Org-wide reads (GET): 1,000 per minute.
  - Users and Groups endpoints: writes mostly 180 per minute, GET 300 per minute. Burst allowances from 20 to 300.
- "Small bursts above the limit are acceptable."
- On 429: "parse the `Retry-After` header and retry your request after that time."
- Also from https://docs.slack.dev/admins/scim-api/ : "The SCIM API is rate limited. If your requests are being limited, an `HTTP: 429` error will be returned."
- Derived (arithmetic, not a Slack claim): at 180 user writes per minute, a 1,000-user big-bang onboarding needs about 6 minutes of pure write time. A 10,000-user onboarding needs about 56 minutes. Org-wide sharing means two connectors in one Slack org compete for the same budget.

### 10.2 Okta rate-limit headers and /api/v1/users (priority 2)
- Source: https://developer.okta.com/docs/reference/rl-best-practices/
- "X-Rate-Limit-Limit": "the rate limit ceiling that's applicable for the current request."
- "X-Rate-Limit-Remaining": "the number of requests left for the current rate-limit window."
- "X-Rate-Limit-Reset": "the time at which the rate limit resets, specified in UTC epoch time (in seconds)."
- 429: "The default rate limit exceeded and requests were denied with 429 response code."
- Concurrent limit: "The first two header values are always 0 for concurrent rate limit errors." And "The X-Rate-Limit-Reset time for concurrent rate limits is only a suggested value."
- Retry-After: not documented on this page. [UNVERIFIED for Okta management]
- Per-minute users number: NOT on this page. Scope: "primarily scoped to orgs unless otherwise specified" (source: https://developer.okta.com/docs/reference/rl-additional-limits/ ). The per-endpoint values are in the Rate Limit Buckets table in the Okta dashboard. The only figure seen is the illustrative 1,000 per minute for `/api/v1/users/*` (https://developer.okta.com/docs/reference/rl-global-mgmt/). Status stays PARTIAL.

### 10.3 Microsoft Graph JSON batching (priority 3)
- Source: https://learn.microsoft.com/en-us/graph/json-batching
- "Microsoft Graph supports batching up to 20 requests into the JSON object."
- "JSON batch requests are currently limited to 20 individual requests."
- "Requests in a batch are evaluated individually against the applicable throttling limits and if any request exceeds the limits, it fails with a status of `429`."
- Dependencies: "If an individual request fails, any request that depends on that request fails with status code `424` (Failed Dependency)."
- "Batch should be either fully sequential or fully parallel."
- Batch-level status: "If the batch request is parseable, the status code is `200`." Each child has its own status.

### 10.4 Graph delta token validity (priority 3)
- Source: https://learn.microsoft.com/en-us/graph/delta-query-overview
- "For directory objects, the limit is seven days."
- "In case the token expires, the service should respond with a 40X-series error with error codes such as `syncStateNotFound`."
- 410: "Delta query can return a response code of `410 Gone` and a **Location** header containing a request URL with an empty `$deltatoken` (same as the initial query)." "...is an indication that the application must restart with a full synchronization of the target tenant."
- Replays: "Your application must be prepared for replays, which occur when the same change appears in subsequent responses."
- Sync from now: "Append `$deltatoken=latest` to the `delta` function and the response contains a `@odata.deltaLink` and no resource data."
- User and group delta: "`$top` isn't supported." "`$orderby` isn't supported." "`$expand` isn't supported."
- Removed reasons: "`changed` indicates the item was deleted and can be restored from deletedItems." "`deleted` indicates the item is deleted and can't be restored."
- Design take: 7 days is the replay budget. An outage longer than that needs a full resync, and the 410 path must trigger it.

### 10.5 Entra accidental deletions default threshold (priority 4)
- Source: https://learn.microsoft.com/en-us/entra/identity/app-provisioning/accidental-deletions
- The page gives no default number. The setup step reads: "Under **Settings**, select the **Prevent accidental deletions** check box and specify a deletion threshold."
- The only number is the test example: "by setting the threshold to a low number, for example 3".
- The "500" default from the brief is NOT on this page. Status: UNVERIFIED. Do not use 500 as a cited fact.
- "It's evaluated each cycle. If the number of deletions doesn't exceed the threshold during a single cycle, the 'circuit breaker' isn't triggered."

### 10.6 RFC 7644 gaps (priority 5)
- Source: https://www.rfc-editor.org/rfc/rfc7644.txt (plain text fetched, but only the first 100,000 characters were read. The file is 170,460 characters.)
- Section 3.14 (412 Precondition Failed): NOT reached. UNVERIFIED.
- Section 3.7 bulk: "The client MAY override this behavior by specifying a value for the "failOnErrors" attribute."
- "The "failOnErrors" attribute defines the number of errors that the service provider should accept before failing"
- "If a bulk job is processed successfully, HTTP response code 200 OK MUST be returned"
- Section 3.7.4 maxOperations and maxPayloadSize: NOT reached. UNVERIFIED.
- Discovery of capabilities (section 3.4.2.2, 3.5.2, 3.7): "Clients MAY discover service provider filter capabilities by looking at the "filter" attribute" ; "Clients may discover service provider support for PATCH by querying the service provider configuration" ; "Support for bulk requests can be discovered by querying the service provider configuration"
- ServiceProviderConfig attribute names (patch, bulk, filter.maxResults, etag): section 4 NOT reached. UNVERIFIED names.

### 10.7 RFC 9700 section 4.14.2 (priority 7)
- Source: https://www.rfc-editor.org/rfc/rfc9700.txt (section 4.14.2, "Recommendations", "Refresh token rotation")
- Rotation: "the authorization server issues a new refresh token with every access token refresh response."
- Reuse detection: "If a refresh token is compromised and subsequently used by both the attacker and the legitimate client, one of them will present an invalidated refresh token, which will inform the authorization server of the breach."
- Consequence (as quoted in the fetch output): the server "revokes the active refresh token," which "stops the attack at the cost of forcing the legitimate client to obtain a fresh authorization grant."
- Requirement: "Authorization servers MUST utilize one of these methods to detect refresh token replay," meaning sender-constrained tokens or rotation.
- Grace period: none found in 4.14.2. Treat as "no grace period in the spec text read".
- Race for the design: two workers refreshing the same rotating token concurrently means the second one presents an invalidated token. Under reuse detection, the legitimate chain can be forced into a fresh grant. Mitigation: single-flight refresh per connection, plus a durable write of the new token before any use. This is a derived design point, not a spec quote.

### 10.8 HTTP retry semantics (priority 6)
- RFC 6585 section 4, source https://www.rfc-editor.org/rfc/rfc6585.txt :
  - "The 429 status code indicates that the user has sent too many requests in a given amount of time ("rate limiting")."
  - "The response representations SHOULD include details explaining the condition, and MAY include a Retry-After header indicating how long to wait before making a new request."
  - "Responses with the 429 status code MUST NOT be stored by a cache."
- RFC 9110 section 5.6.7 (HTTP-date grammar, the part of Retry-After that is a date): "HTTP-date = IMF-fixdate / obs-date". Source: https://www.rfc-editor.org/rfc/rfc9110.txt
- RFC 9110 section 10.2.3 (Retry-After delay-seconds) and section 9.2.2 (idempotent methods): NOT reached. The text file is 502,907 characters, and only the first 100,000 were read. UNVERIFIED wording. Section numbers come from the table of contents.

### 10.9 GitHub failed deliveries (priority 8)
- Source: https://docs.github.com/en/webhooks/using-webhooks/handling-failed-webhook-deliveries
- "GitHub does not automatically redeliver failed deliveries."
- "You can manually redeliver failed deliveries."

### 10.10 Google batch and push (priority 9)
- Batch source: https://developers.google.com/workspace/admin/directory/v1/guides/batch
- "You're limited to 1000 calls in a single batch request."
- "If you must make more calls than that, use multiple batch requests."
- "A set of n requests batched together counts toward your usage limit as n requests, not as one request."
- Push channel default and maximum expiration: NOT on the guide fetched earlier. The only statements are the ttl and expiration parameters, where "the more restrictive value is used." Still UNVERIFIED for defaults.

### 10.11 Okta Lifecycle Management (priority 10)
- Developer deactivate guide (https://developer.okta.com/docs/guides/deactivate-user/main/) returned HTTP 404. Help page (https://help.okta.com/en-us/content/topics/users-groups-profiles/usgp-deactivate-user.htm) was not fetched successfully. Deactivate vs delete: UNVERIFIED.
- Matching (search snippets only, PARTIAL). From the Okta "Add provisioned users" page (https://help.okta.com/en-us/Content/Topics/Provisioning/lcm/lcm-about-user-management.htm), as shown in the snippet: when an account in an external app corresponds to an existing Okta account, "the two can be linked", and "new AppUser objects are created to match against existing Okta users or to create new ones."
- CSV import (support.okta.com snippet, https://support.okta.com/help/s/article/application-import-via-csv-not-auto-matching-users): the import "does not automatically match users."
- Auto-confirm (https://support.okta.com/help/s/article/auto-confirm-provisioning-options, snippet): auto-confirm applies "only when there is an exact match on the predefined criteria."
- Profile sourcing (snippet): when a directory is the source, the linked profile's data and lifecycle state "come entirely from that source", and the profile is read-only in Okta.

### 10.12 Interview evidence, second pass (priority 11)
- Not site-restricted. The searches were run without a `site:` filter, so PracHub, LeetCode Discuss, HelloInterview and DesignGurus were NOT targeted directly. Gap remains.
- Rippling (candidate-style threads, content NOT read, only titles seen in the snippet):
  - https://www.1point3acres.com/interview/thread/1045467 : "Rippling 2024 System Design Interview Experience (Tech Phone Screen)". Level and round from title: phone screen, 2024.
  - https://www.1point3acres.com/interview/thread/1158885 : "Rippling On-Site Software Engineer System Design Interview". Round: on-site. Date not in snippet.
  - https://www.1point3acres.com/interview/thread/1013175 : "Rippling Interview Experience - System Design and Project Deep Dive". Round: system design plus project deep dive. Date not in snippet.
  - https://www.1point3acres.com/interview/thread/1041843 : "Rippling System Design Technical Phone Screen Experience". Round: phone screen. Date not in snippet.
- Rippling guides (not candidate evidence): https://www.systemdesignhandbook.com/guides/rippling-system-design-interview/ ; https://www.techinterview.org/companies/rippling/ ; https://www.designgurus.io/answers/detail/what-to-expect-in-the-rippling-system-design-interview
- Guide-reported prompt (from search summary, not a candidate report): a cross-module workflow engine "that terminates IT access and recovers devices when HR terminates an employee", and "account lifecycle across hundreds of third-party SaaS apps, with attention to drift detection." Source guide URL not isolated. Treat as UNVERIFIED prompt.
- Stripe (candidate-style, one anonymous post, content from search summary):
  - https://www.teamblind.com/post/stripe-system-design-bxptt8eb : anonymous system design round; the summary says the candidate was asked to "build a service which interacted with existing Stripe services" and discussed "API, DB, scalability". Level and date not shown.
  - https://www.1point3acres.com/interview/thread/1087138 : "stripe Full-Time SDE Technical Phone Screen and VO Interview Experience". Content not read.
- Stripe guide: https://dataford.io/interview-guides/stripe/solutions-architect (Solutions Architect, not SWE).
- Count: 1 Blind Stripe post, 4 Rippling 1point3acres threads, 1 Stripe 1point3acres thread. All candidate threads are unread beyond titles. No Okta, Plaid, Merge, Workday, Gusto or Deel hits in this pass. No SCIM or provisioning prompt confirmed from a candidate's own words.

### 10.13 Rippling App Shop and customer count (priority 12)
- App Shop count from a fetched page: https://www.rippling.com/platform/integrations : "Explore 600+ out-of-the-box integrations", footer "© 2026 Rippling People Center Inc." The 650+ figure from the earlier search summary is not on the fetched page. Use 600+.
- Customer count: no Rippling primary source found. Third-party trackers conflict. One profile says "more than 30,000 customer companies by 2026"; a May 2025 item says "above 20,000 customers"; a 2019 figure of about 2,000 is old. Source for the 2026 employee figure of 3,920 is a third-party stats page (https://fmcgroup.com/rippling-employee-count/ ). Not verified. Do not cite these as facts.
- Irish headcount (Eurofound snippet, https://apps.eurofound.europa.eu/restructuring-events/detail/300475 ): plan for 150 new roles in Dublin, "more than 300" Irish employees. Snippet only.

## Final status table

| # | claim | status | URL |
|---|---|---|---|
| 1 | id is issued by the service provider and MUST NOT be specified by the client | CONFIRMED | https://www.rfc-editor.org/rfc/rfc7643 |
| 2 | externalId is issued by the provisioning client, interpreted as scoped to provisioning domain | CONFIRMED | https://www.rfc-editor.org/rfc/rfc7643 |
| 3 | userName MUST be unique across the service provider's entire set of Users, case insensitive | CONFIRMED | https://www.rfc-editor.org/rfc/rfc7643 |
| 4 | Server uniqueness for the schema attribute is only SHOULD within the endpoint or tenancy | CONFIRMED | https://www.rfc-editor.org/rfc/rfc7643 |
| 5 | active is a Boolean for administrative status | CONFIRMED | https://www.rfc-editor.org/rfc/rfc7643 |
| 6 | Create returns 201 Created | CONFIRMED | https://www.rfc-editor.org/rfc/rfc7644 |
| 7 | Uniqueness conflict returns 409 with scimType uniqueness | CONFIRMED | https://www.rfc-editor.org/rfc/rfc7644 |
| 8 | PATCH is an OPTIONAL server function and is atomic | CONFIRMED | https://www.rfc-editor.org/rfc/rfc7644 |
| 9 | Remove without path returns 400 noTarget | CONFIRMED | https://www.rfc-editor.org/rfc/rfc7644 |
| 10 | Filter attribute names and operators are case insensitive | CONFIRMED | https://www.rfc-editor.org/rfc/rfc7644 |
| 11 | startIndex is 1-based, count is capped by provider, no fixed max | CONFIRMED | https://www.rfc-editor.org/rfc/rfc7644 |
| 12 | meta.version equals ETag, optional, weak prefix W/ | CONFIRMED | https://www.rfc-editor.org/rfc/rfc7643 |
| 13 | 412 on If-Match mismatch | CONFIRMED (editor, RFC 7644 section 3.12 table) | https://www.rfc-editor.org/rfc/rfc7644.txt |
| 14 | Bulk is optional; failOnErrors defined; 200 OK on success; maxOperations not read | PARTIAL | https://www.rfc-editor.org/rfc/rfc7644.txt |
| 15 | SCIM has no POST idempotency key | PARTIAL (no key appears in sections read) | https://www.rfc-editor.org/rfc/rfc7644 |
| 16 | Google: 2,400 queries per minute per user per project | CONFIRMED | https://developers.google.com/workspace/admin/directory/v1/limits |
| 17 | Google: 10 users per domain per second on create | CONFIRMED | https://developers.google.com/workspace/admin/directory/v1/limits |
| 18 | Google: per-day quota | UNVERIFIED | https://developers.google.com/workspace/admin/directory/v1/limits |
| 19 | Google users.insert: 409 conflicting account not created | CONFIRMED | https://developers.google.com/workspace/admin/directory/reference/rest/v1/users/insert |
| 20 | Slack Web API: Tier 2 at least 20 per minute, Retry-After on 429 | CONFIRMED | https://docs.slack.dev/apis/web-api/rate-limits/ |
| 21 | Slack Tier 3 about 50 and Tier 4 about 100 per minute | PARTIAL | https://docs.slack.dev/apis/web-api/rate-limits/ |
| 22 | Slack limits per method per workspace per app | CONFIRMED | https://docs.slack.dev/apis/web-api/rate-limits/ |
| 23 | Slack SCIM: Users GET 300 per minute, writes 180 per minute; org-wide 600 writes and 1,000 reads | PARTIAL (numbers are in tables, not sentences) | https://docs.slack.dev/reference/scim-api/rate-limits |
| 24 | Graph: 429 plus Retry-After, limits per app per tenant and across tenants | CONFIRMED | https://learn.microsoft.com/en-us/graph/throttling |
| 25 | Graph: batch requests evaluated individually, batch returns 200 | CONFIRMED | https://learn.microsoft.com/en-us/graph/throttling |
| 26 | Graph JSON batch: "JSON batch requests are currently limited to 20 individual requests." | CONFIRMED | https://learn.microsoft.com/en-us/graph/json-batching |
| 27 | Okta: 429 until quota resets; example 1000 per minute for /api/v1/users/* | PARTIAL | https://developer.okta.com/docs/reference/rl-global-mgmt/ |
| 28 | Okta headers X-Rate-Limit-Limit, X-Rate-Limit-Remaining, X-Rate-Limit-Reset | CONFIRMED | https://developer.okta.com/docs/reference/rl-best-practices/ |
| 29 | GitHub installation token: 5,000 per hour, +50 per repo over 20, cap 12,500 | CONFIRMED | https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api |
| 30 | GitHub Enterprise Cloud installation: 15,000 per hour | PARTIAL (conflicts with 12,500 cap for the general tier; different tier) | https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api |
| 31 | GitHub secondary: 900 points per minute REST, 100 concurrent | CONFIRMED | https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api |
| 32 | GitHub: primary exhaustion returns 403 or 429, x-ratelimit-remaining 0 | CONFIRMED | https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api |
| 33 | GitHub SCIM: no more than 1,000 users per hour advice | UNVERIFIED | https://docs.github.com/en/enterprise-cloud@latest/admin/managing-iam/provisioning-user-accounts-with-scim/provisioning-users-and-groups-with-scim-using-the-rest-api |
| 34 | Zoom Free daily: Light 6,000, Medium 2,000, Heavy 1,000, Resource 30,000 | CONFIRMED | https://developers.zoom.us/docs/api/rate-limits/ |
| 35 | Zoom Business+ 60,000 per day heavy and resource-intensive, account-level shared by all apps | CONFIRMED | https://developers.zoom.us/docs/api/rate-limits/ |
| 36 | Jira: 65,000 points per hour shared across tenants | CONFIRMED | https://developer.atlassian.com/cloud/jira/platform/rate-limiting/ |
| 37 | Jira: per-tenant cap 500,000 points per hour | CONFIRMED | https://developer.atlassian.com/cloud/jira/platform/rate-limiting/ |
| 38 | Salesforce Enterprise daily API allocation | UNVERIFIED (403) | https://developer.salesforce.com/docs/atlas.en-us.salesforce_app_limits_cheatsheet.meta/salesforce_app_limits_cheatsheet/salesforce_app_limits_platform_apirequests.htm |
| 39 | HubSpot per-app limits | UNVERIFIED (404) | https://developers.hubspot.com/docs/developer-tooling/platform/api-usage/usage-details |
| 40 | Graph delta: deltaLink and nextLink flow, @removed reason changed or deleted | CONFIRMED | https://learn.microsoft.com/en-us/graph/delta-query-users |
| 41 | Graph delta: directory object tokens valid 7 days, then 40X (syncStateNotFound) and 410 Gone resync | CONFIRMED | https://learn.microsoft.com/en-us/graph/delta-query-overview |
| 42 | Google watch: POST notification, no automatic renewal | CONFIRMED | https://developers.google.com/workspace/admin/directory/v1/guides/push |
| 43 | Google watch: default expiry | UNVERIFIED | https://developers.google.com/workspace/admin/directory/v1/guides/push |
| 44 | Okta event hooks: at least once, best effort, no max delay | CONFIRMED | https://developer.okta.com/docs/concepts/event-hooks/ |
| 45 | Okta event hooks: one retry, 5xx retried, 3 second timeout | CONFIRMED | https://developer.okta.com/docs/concepts/event-hooks/ |
| 46 | Slack Events: 2xx within 3 seconds, up to 3 retries (about immediate, 1 min, 5 min) | CONFIRMED (retry times as "gradually increasing timetable"; the exact 1 and 5 minute values are PARTIAL) | https://docs.slack.dev/apis/events-api/ |
| 47 | Slack user_change and team_join event names | UNVERIFIED | https://docs.slack.dev/apis/events-api/ |
| 48 | Entra incremental cycle every about 40 minutes | UNVERIFIED (interval set per app tutorial) | https://learn.microsoft.com/en-us/entra/identity/app-provisioning/how-provisioning-works |
| 49 | Entra initial and incremental cycle steps, watermark | CONFIRMED | https://learn.microsoft.com/en-us/entra/identity/app-provisioning/how-provisioning-works |
| 50 | Entra disable is active=false, hard delete 30 days after soft delete | CONFIRMED | https://learn.microsoft.com/en-us/entra/identity/app-provisioning/how-provisioning-works |
| 51 | Entra quarantine: incremental once per day, disabled after 4 weeks | CONFIRMED | https://learn.microsoft.com/en-us/entra/identity/app-provisioning/application-provisioning-quarantine-status |
| 52 | Entra escrow: over 40% failures or 40,000 failures, 5,000 minimum, 60,000 absolute | CONFIRMED (logic "subject to change") | https://learn.microsoft.com/en-us/entra/identity/app-provisioning/application-provisioning-quarantine-status |
| 53 | Entra retries: 6 h, 12 h, 24 h, then daily for 28 days | CONFIRMED | https://learn.microsoft.com/en-us/entra/identity/app-provisioning/application-provisioning-quarantine-status |
| 54 | Entra accidental deletion threshold: evaluated per cycle, admin must allow | CONFIRMED | https://learn.microsoft.com/en-us/entra/identity/app-provisioning/accidental-deletions |
| 55 | Entra accidental deletion default threshold value (500 per brief) | UNVERIFIED (page gives no default number; 500 not found) | https://learn.microsoft.com/en-us/entra/identity/app-provisioning/accidental-deletions |
| 56 | Entra gallery apps minimum 25 requests per second | UNVERIFIED (Q&A only) | https://learn.microsoft.com/en-us/answers/questions/1233453/azure-ad-scim-provisioning-rate-limiting-for-multi |
| 57 | Entra initial cycle time formula (0.01 to 0.08 per object) | CONFIRMED | https://learn.microsoft.com/en-us/entra/identity/app-provisioning/application-provisioning-when-will-provisioning-finish-specific-user |
| 58 | Okta import links an external account to a matching Okta user; CSV import does not auto-match | PARTIAL (search snippets of Okta help, pages not fetched) | https://help.okta.com/en-us/Content/Topics/Provisioning/lcm/lcm-about-user-management.htm |
| 59 | Kubernetes controllers move current state toward desired state | CONFIRMED | https://kubernetes.io/docs/concepts/architecture/controller/ |
| 60 | Kubernetes controllers are level-triggered (wording) | UNVERIFIED | https://kubernetes.io/docs/concepts/architecture/controller/ |
| 61 | client-go workqueue: AddRateLimited, dedupe while queued, no concurrent processing of one item | CONFIRMED | https://pkg.go.dev/k8s.io/client-go/util/workqueue |
| 62 | RFC 9700 2.2.2: public client refresh tokens MUST be sender-constrained or rotated (4.14) | CONFIRMED | https://www.rfc-editor.org/rfc/rfc9700.html |
| 63 | RFC 9700 4.14.2 rotation and reuse detection ("the authorization server issues a new refresh token with every access token refresh response") | CONFIRMED | https://www.rfc-editor.org/rfc/rfc9700.txt |
| 64 | Google: 100 refresh tokens per account per client, oldest silently invalidated | CONFIRMED | https://developers.google.com/identity/protocols/oauth2 |
| 65 | Google: refresh token unused 6 months, testing apps 7 days | CONFIRMED | https://developers.google.com/identity/protocols/oauth2 |
| 66 | Microsoft refresh token lifetime | UNVERIFIED | https://learn.microsoft.com/en-us/entra/identity/ |
| 67 | Salesforce or Xero rotating refresh token grace period | UNVERIFIED | https://developer.salesforce.com/ |
| 68 | RFC 9110 Retry-After text (section 10.2.3) | CONFIRMED (editor) | https://www.rfc-editor.org/rfc/rfc9110.html |
| 69 | RFC 9110 idempotent methods (section 9.2.2) | UNVERIFIED (text not read) | https://www.rfc-editor.org/rfc/rfc9110.html |
| 70 | RFC 6585 section 4: 429 "indicates that the user has sent too many requests"; "MAY include a Retry-After header" | CONFIRMED | https://www.rfc-editor.org/rfc/rfc6585.txt |
| 71 | RateLimit header draft (draft-ietf-httpapi-ratelimit-headers-11) is not yet an RFC | CONFIRMED | https://datatracker.ietf.org/doc/draft-ietf-httpapi-ratelimit-headers/ |
| 72 | Standard Webhooks headers webhook-id, webhook-timestamp, webhook-signature | CONFIRMED | https://github.com/standard-webhooks/standard-webhooks/blob/main/spec/standard-webhooks.md |
| 73 | Standard Webhooks signed content msg_id.timestamp.payload | CONFIRMED | https://github.com/standard-webhooks/standard-webhooks/blob/main/spec/standard-webhooks.md |
| 74 | Standard Webhooks 5 minute tolerance | UNVERIFIED (spec says only "some allowable tolerance") | https://github.com/standard-webhooks/standard-webhooks/blob/main/spec/standard-webhooks.md |
| 75 | Standard Webhooks multi-day retry with exponential backoff (example table) | PARTIAL | https://github.com/standard-webhooks/standard-webhooks/blob/main/spec/standard-webhooks.md |
| 76 | Stripe: retry up to three days with exponential backoff (live mode) | CONFIRMED | https://docs.stripe.com/webhooks |
| 77 | Stripe: no ordering guarantee, duplicates possible, track event IDs | CONFIRMED | https://docs.stripe.com/webhooks |
| 78 | Stripe: 5 minute default signature tolerance | CONFIRMED | https://docs.stripe.com/webhooks |
| 79 | Stripe: manual resend 15 days (Dashboard) and 30 days (CLI) | CONFIRMED | https://docs.stripe.com/webhooks |
| 80 | GitHub webhook: 2XX within 10 seconds | CONFIRMED | https://docs.github.com/en/webhooks/using-webhooks/handling-webhook-deliveries |
| 81 | GitHub: "GitHub does not automatically redeliver failed deliveries." | CONFIRMED | https://docs.github.com/en/webhooks/using-webhooks/handling-failed-webhook-deliveries |
| 82 | Rippling App Shop: "Explore 600+ out-of-the-box integrations" (footer 2026); the 650+ search snippet is not confirmed | CONFIRMED (600+, 2026) | https://www.rippling.com/platform/integrations |
| 83 | Rippling App Shop: 600+ integrations (IT page) | PARTIAL (search summary, no date) | https://rippling.com/rippling-it/integrations |
| 84 | Rippling provisioning method (SCIM vs API, supergroups) | UNVERIFIED | https://developer.rippling.com/ |
| 85 | Rippling partner OAuth scopes and token URL | PARTIAL (third-party docs) | https://prismatic.io/docs/components/rippling |
| 86 | Rippling webhooks restricted for App Shop integrations | PARTIAL (third-party docs) | https://docs.blinkops.com/docs/integrations/rippling/triggers/rippling-webhook-event.md |
| 87 | Rippling runs Temporal for async jobs, "missed executions, non-stateful retries, observability" | PARTIAL (vendor customer story) | https://temporal.io/in-use/re-building-async-processing-at-rippling-using-temporal |
| 88 | Rippling engineering blog on architecture | UNVERIFIED | https://www.rippling.com/blog |
| 89 | Rippling customer count with date | UNVERIFIED | https://www.rippling.com/ |
| 90 | Interview prompt: 100 TPS third-party API, dropped users (Blind) | PARTIAL (company and level unknown) | https://www.teamblind.com/post/system-design-interview-question-3rd-party-api-lwgs3pxm |
| 91 | Interview evidence: Rippling and Stripe candidate threads exist, but content was not read and no SCIM prompt is confirmed | PARTIAL | https://www.1point3acres.com/interview/thread/1158885 |
| 92 | Google batch: "You're limited to 1000 calls in a single batch request." | CONFIRMED | https://developers.google.com/workspace/admin/directory/v1/guides/batch |
| 93 | Slack SCIM: "parse the Retry-After header and retry your request after that time." | CONFIRMED | https://docs.slack.dev/reference/scim-api/rate-limits |
| 94 | Okta X-Rate-Limit reset is UTC epoch seconds; no Retry-After on the Okta page | CONFIRMED | https://developer.okta.com/docs/reference/rl-best-practices/ |
| 95 | Okta deactivate vs delete semantics | UNVERIFIED (developer and help pages returned 404 or not fetched) | https://help.okta.com/en-us/content/topics/users-groups-profiles/usgp-deactivate-user.htm |
| 96 | Rippling customer count (30,000+ or 20,000+) and employee count (3,920 to 7,700) | UNVERIFIED (third-party trackers that conflict; no primary source) | https://fmcgroup.com/rippling-employee-count/ |

Line count: see the reply to the parent agent.
