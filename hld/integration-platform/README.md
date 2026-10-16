# Employee identity + integration platform (SCIM, connectors, webhooks)

> One-line answer: the traffic is small (about **10 M external calls a day**, ~115/s on average) and the hard parts are all correctness under someone else's rules. So sync **desired state, not events**. Every employee change only marks a task `(connection, employee)` as dirty, and repeated changes **coalesce** into one row. A worker reads the employee's current record, renders what the account in that app should look like, compares it with what we last applied, and sends only the difference. That makes retries, reordering and replays harmless. Creates are the one non-idempotent call, so they write an intent first and look for the account before trying again. A dispatcher holds a **token bucket per connection and per app**, with priority lanes and a reserve so a termination never waits behind a 20,000-person import. Errors are classified, and breakers are scoped so one tenant's revoked token never pauses everyone. A daily reconcile reads each app back and catches drift, behind a **mass-change guard** that refuses to deprovision hundreds of people because a list call came back empty.

Tier 3, problem #32 in [`hld/README.md`](../README.md). **Guide-only.** No candidate post names this prompt. Guides list it as Rippling's core product: "employee identity system" ([SystemDesignHandbook](https://www.systemdesignhandbook.com/guides/rippling-system-design-interview/)), "app provisioning" and "onboarding and offboarding cascade" ([DesignGurus](https://www.designgurus.io/answers/detail/what-to-expect-in-the-rippling-system-design-interview)). The closest reported prompt is the termination orchestrator in [`../employee-ops-bundle/`](../employee-ops-bundle/) (#46, Rippling onsite, May 2026), which is one workflow over these connectors. Stripe tests the same mechanics from the other side: its onsite has an "integration against real APIs" round and its own product is webhooks ([`../webhook-delivery/`](../webhook-delivery/), #58). Evidence and loop notes: [`../company-questions.md` §2](../company-questions.md#2-rippling-staff). Facts and URLs: [`research/facts-survey.md`](research/facts-survey.md).

Reusable blocks: [`../../concepts/rate-limiting-and-load-shedding.md`](../../concepts/rate-limiting-and-load-shedding.md), [`../../concepts/exactly-once.md`](../../concepts/exactly-once.md), [`../../concepts/oauth.md`](../../concepts/oauth.md), [`../../concepts/temporal-durable-execution.md`](../../concepts/temporal-durable-execution.md), [`../../concepts/leases-fencing-clocks.md`](../../concepts/leases-fencing-clocks.md).

## Problem statement (working version)

There is no verbatim prompt. Working version:

> Rippling is the system of record for employees. Customers connect third-party apps (Google Workspace, Slack, GitHub, Microsoft 365, Zoom, Salesforce, ...). When someone is hired, changes team or manager, or leaves, Rippling must create, update or remove their account and group memberships in every connected app they should have, through each app's SCIM or REST API. Partner apps and customers also subscribe to employee changes by webhook. Design the platform. The external APIs have rate limits, go down, and get changed by people clicking in their admin consoles.

## Clarifying questions, and the answers this design assumes

| Question | Assumed answer |
|---|---|
| How many companies, employees, connected apps? | ~50k tenants, ~10 M employees (mean 200, largest ~50k), ~15 apps per tenant: ~750k connections, ~100 M account links [estimate] |
| Do we build the 600 connectors? | We build the framework, a generic SCIM 2.0 connector, and the top ~20 apps by hand. Connector teams build the rest on the SDK |
| Which direction does data flow? | Rippling to apps (outbound provisioning). Apps that are a source of truth (an ATS on hire) are below the line |
| How fast must a termination reach every app? | Started within 10 s of the effective time. Done in 60 s p99 per healthy app with quota. "All apps" in 5 min p99, apps in outage or needing re-auth excluded and shown |
| How fast for ordinary edits? | p99 5 min for healthy apps |
| What if an admin edits an account directly in the app? | Tenant policy per connection: enforce (overwrite), or report only. Default: enforce managed attributes, report unmanaged accounts, never auto-delete them |
| Is this the identity provider for login too? | SSO (SAML / OIDC) exists and is below the line, except that disabling the identity is step one of a termination (#46) |

## Functional requirements

Core:
1. **Connect an app.** An admin connects an app (OAuth consent or API key), chooses who gets access (rules on department, location, employment type), maps attributes and groups, and sees a **preview plan** before enabling. Existing accounts are matched, never duplicated.
2. **Provision on every change.** A hire, edit, group change or termination in the employee record becomes create, update, suspend or deactivate calls in every connected app the person is in scope for. Terminations go first.
3. **Reconcile.** Read each app back on a schedule, detect accounts that drifted or were created outside Rippling, and correct or report them per policy.
4. **Events out and in.** Partner apps and customer endpoints subscribe to employee change events by signed webhook. Apps' own webhooks into us are accepted as hints to re-read.
5. **Show and control.** Per employee and per app: status, the last error in plain words, retry, skip, re-authorize. Every external call is audited.

Below the line: SSO login itself, password vaulting, device management, inbound sync from apps that own data (ATS, payroll carriers), file-based integrations (SFTP, EDI), building every connector, cross-app transactions.

## Non-functional requirements

| Dimension | Target |
|---|---|
| Scale | ~10 M external calls a day, ~115/s average, ~1,500/s peak. ~3 M change-driven account operations a day. Bulk jobs (a 50k-person connect, a rule change) up to 100k operations each [estimate] |
| Deprovision latency | Dispatched within 10 s of the effective time, applied within 60 s p99 per healthy app with quota |
| Update latency | p99 5 min end to end for healthy apps |
| Correctness | Never apply an older state over a newer one. Never create a duplicate account on retry. Never act on tenant B's app with tenant A's credential |
| Isolation | A 50k-person import, a slow app or one tenant's broken token must not delay other tenants or other apps |
| Quota | Stay under every app's limit: 429s under 1% of calls per app, never sustained. Our OAuth client must never get throttled or banned for all tenants |
| Durability | An accepted change is never lost. Every link ends in sync, or in a visible error the admin can act on |
| Safety | No mass deprovision from a rule mistake or an empty list response without a human approving it |
| Availability | Change pipeline 99.95%. Console 99.9%. An app being down is normal, not an incident for us |
| Security | Credentials encrypted per tenant with envelope encryption, least-privilege scopes, fixed egress IPs, no PII in logs |

## What interviewers probe

1. An employee's title changes three times in a minute, and a retry of the first change arrives last. What ends up in Slack, and how many API calls did it cost?
2. The worker crashed after `POST /Users` returned 201 but before we saved the id. What stops a second account on retry?
3. This GitHub installation allows 5,000 requests an hour, and the tenant just connected 20,000 people. Someone is fired now. How long until their access is gone? And a 5,000-person layoff?
4. Google is down for 2 hours. What happens when it comes back? One tenant revoked our OAuth grant. What happens to the other 20,000 Google tenants?
5. The nightly reconcile reads an empty user list from an app and concludes everyone left. What stops you from deactivating 3,000 accounts?
6. How do partners get employee changes, in what order, and what do you sign?

## Files

| File | What it is |
|---|---|
| [`solution.md`](solution.md) | Full HLD in flow-first form: one incremental diagram, one walkthrough per FR, deep dives that mutate the design, then nitty-gritty |
| [`diagrams.md`](diagrams.md) | The D1 to D12 diagram set |
| [`edge-cases.md`](edge-cases.md) | Every "what if" with a 60-second answer and a confidence box |
| [`deep-dives/desired-state-sync-and-ordering.md`](deep-dives/desired-state-sync-and-ordering.md) | Level vs edge triggered, the task row and coalescing, version guards, zombie workers and `If-Match`, effective dating |
| [`deep-dives/idempotent-creates-and-account-matching.md`](deep-dives/idempotent-creates-and-account-matching.md) | The crash after create, intent rows, natural keys, search before create, matching on first connect, rehires |
| [`deep-dives/rate-limits-priority-and-fairness.md`](deep-dives/rate-limits-priority-and-fairness.md) | Hierarchical token buckets, learned limits, priority lanes and the P0 reserve, fair share across tenants, slow apps |
| [`deep-dives/failures-retries-and-circuit-breakers.md`](deep-dives/failures-retries-and-circuit-breakers.md) | Error classes, backoff with jitter, retry budgets, breakers scoped by connection and app, draining a backlog after an outage |
| [`deep-dives/drift-reconciliation-and-mass-change-guard.md`](deep-dives/drift-reconciliation-and-mass-change-guard.md) | Full and incremental reconcile, attribute policies, unmanaged accounts, the mass-change guard |
| [`deep-dives/connectors-credentials-and-webhooks.md`](deep-dives/connectors-credentials-and-webhooks.md) | Connector SDK and manifest, generic SCIM, connector versioning, OAuth refresh single-flight, envelope encryption, egress, webhooks in and out |
| [`research/facts-survey.md`](research/facts-survey.md) | Raw web research notes with source links. Input to the files above, not study material |
| `integration-platform.excalidraw` | My drawing. Missing until I draw it |
