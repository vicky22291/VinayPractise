# Real-world survey: central authorization service (RBAC + ReBAC + ABAC, Zanzibar style)

Scope: facts for the study note "Design a central authorization service for a multi-tenant B2B SaaS company." Interview contexts: Stripe (internal authorization redesign, guide-only prompt) and Rippling (permissions engine, guide-only prompt).

Labels used in this file:
- **[verified]** = read on the source page (or in the fetched text) during this survey.
- **[unverified]** = only seen in a search snippet, a secondary article, or a summary I could not check against the primary page.
- **guide, not first-hand** = interview-prep site. Used only in section 1.

Date of survey: 2026-10-16.

---

## 0. Summary of what is and is not public

| Topic | Primary source found? | Notes |
|---|---|---|
| Google Zanzibar | Yes (USENIX ATC 2019 paper) | Best source for numbers and the data model |
| Airbnb Himeji | Partly (InfoQ news + Airbnb Medium post URL, Medium not fetched) | Numbers come from InfoQ |
| Figma permissions DSL | Yes (Figma blog) | No shadow-evaluation or mismatch numbers in the post |
| Uber Charter / ABAC | Yes (Uber engineering blog) | 70 services, no latency for the full path |
| Carta AuthZ | No (Medium post not fetched) | Only an Auth0 podcast page and a slide reference |
| GitHub | No engineering post found | Third-party only |
| Netflix OPA | No blog post found | Talk slides exist; not fetched |
| Pinterest, Slack, Notion, Canva, Segment, Lyft | Not found | Do not cite them as authorization examples without a source |
| Google Cloud IAM incident (14 Dec 2020) | Yes (Google Cloud status page) | Used for section 6 |
| Stripe roles, keys, RAKs | Yes (Stripe docs) | Strong source |
| AWS IAM evaluation logic | Yes (AWS docs) | Strong source |
| Rippling permissions | Yes (Rippling product pages only) | No Rippling engineering blog found |
| Microsoft Entra CAE | Yes (Microsoft Learn) | Strong source for revocation timing |
| Okta token revocation | Yes (Okta developer docs) | Page gives no timings |

---

## 1. Interview framing (guide, not first-hand)

One-line framing: prep guides describe the Stripe prompt as an internal authorization redesign across many services, and the Rippling prompt as a permissions engine tied to an employee graph.

| Guide | Label | What it says | URL |
|---|---|---|---|
| DesignGurus, "What to Expect in the Stripe System Design Interview" | guide, not first-hand | Worked example is a metrics service, not an authorization prompt. Lists these FR-style points: batched ingestion, per-tenant limits, retention. Scale example "millions of points per second across customers". | https://www.designgurus.io/answers/detail/what-to-expect-in-the-stripe-system-design-interview |
| Search snippet, techinterview.org (Stripe authorization) | guide, not first-hand | Says one interviewer's prompt was an internal authorization redesign with a stated service count and request rate, plus a rollout plan. Snippet only. [unverified] | https://www.techinterview.org/post/3233465793/system-design-identity-service/?format=md |
| Aced.io Stripe guide | guide, not first-hand | Not found in search. Could not confirm its wording. [unverified: not checked] | (not retrieved) |
| DesignGurus, "What to Expect in the Rippling System Design Interview" | guide, not first-hand | Prompts: "Design the employee graph", "Design the onboarding/offboarding cascade", "Design cross-product policy enforcement". Lists RBAC and least privilege. No Supergroups. Offboarding wants "instant device locks, remote wipes, license revocation, and SSO deactivation". | https://www.designgurus.io/answers/detail/what-to-expect-in-the-rippling-system-design-interview |
| SystemDesignHandbook Rippling guide | guide, not first-hand | FRs: payroll, payment rails, SSO and SCIM provisioning, RBAC where "HR can view payroll data and IT cannot", offboarding. NFRs: strong consistency for payroll ledgers, "near five 9s availability", multi-region failover, sharding by tenant ID. Gives no permissions engine detail. | https://www.systemdesignhandbook.com/?p=3067 |
| techinterview.org Rippling guide (search snippet) | guide, not first-hand | Mentions Employee Graph queries under access control, and rule engines over shared state. Snippet only. [unverified] | https://www.techinterview.org/companies/rippling/ |
| Hello Interview "design authorization / Zanzibar" | guide, not first-hand | Not found in search. [unverified: not checked] | (not retrieved) |
| techinterview.org "System Design: Access Control and Authorization" (2025) | guide, not first-hand | Explains tuples, expanding group membership, and consistency tokens (Zookies). Used only as a pointer; numbers taken from the paper instead. | https://techinterview.org/system-design-access-control/ |

Likely FR list for the note (derived, not sourced): check permission for (principal, action, resource); write or revoke a relation; list resources a user can see; audit who-can-do-what; per-tenant isolation.

Likely NFR list for the note (derived from the guides and the Zanzibar paper): p95 check latency under 10 ms (Zanzibar, section 4); availability of at least 99.999% (Zanzibar, section 4); a revoke must be visible to the next check (Zanzibar consistency model, section 4); fail-closed on errors (section 6).

---

## 2. Rippling: public permissions model

Caveat: only marketing and product pages were found. No Rippling engineering blog post on the permissions engine was found. Search for "Rippling engineering blog permissions" returned only a job posting.

| Claim | Label | Source |
|---|---|---|
| "Permission profiles are attached to attributes, not people." | [verified] product page | https://www.rippling.com/products/it/platform/permissions |
| Supergroups are "dynamic membership lists built using attributes like level or location." | [verified] product page | https://www.rippling.com/products/it/platform/permissions |
| "As an employee's attributes change, their permissions update." | [verified] product page | https://www.rippling.com/products/it/platform/permissions |
| A permission profile has three parts: scope (for example a reporting line or department), access (data type, such as payroll), and actions (view, edit, approve). | [verified] product page | https://www.rippling.com/products/it/platform/permissions |
| Admins can preview what a person gains or loses before a change. | [verified] product page | https://www.rippling.com/products/it/platform/permissions |
| Custom roles are mentioned. | [unverified] Not on the page I read. The page describes profiles, not custom roles. | https://www.rippling.com/products/it/platform/permissions |
| How fast a termination revokes app access. | Not published on the permissions page. "The page makes no claims about how quickly access is revoked." | https://www.rippling.com/products/it/platform/permissions |
| Permissions team builds a "Permissions Platform used by end users and internal developers". | [verified] from a job listing, no architecture | https://careers.threshold.vc/companies/rippling/jobs/45552572-full-stack-backend-engineer-ii-platform |

Trade-off to note: Rippling's model ties access to attributes, so the authorization system depends on HR data quality. A wrong attribute grants or removes access without any explicit grant.

---

## 3. Stripe: public authorization model

### 3a. Dashboard roles

Stripe's doc lists 26 built-in roles, each with an SSO role ID. Sample rows verified on the page:

| Role | SSO role ID | Verified scope |
|---|---|---|
| Administrator | admin | Manage most things, invite and remove team members, create and delete API keys. Cannot delete default bank account or change owner. |
| IAM Administrator | iam_admin | Invite, edit, remove users, create and manage user groups. Cannot manage payments or products. Cannot assign Administrator or Super Administrator. |
| Super Administrator | super_admin | Same as Administrator plus can assign Super Administrator. |
| Developer | developer | Create, view, edit, delete API keys. Cannot invite team members. |
| Analyst | analyst | Refunds, payouts, exports. Cannot edit payout schedules or account settings. |
| Dispute Analyst | dispute_analyst | Disputes only, plus read access to payments, products, customers. |
| Refund Analyst | refund_analyst | Refunds and credit notes. Cannot create payments. |
| View Only | view_only | Read most objects, no writes. |

Other verified roles: Connect Onboarding Analyst, Transfer Analyst, Connect Risk Analyst, Sandbox Admin, Sandbox User, Identity Analyst, Identity View Only, Data Migration Specialist, Support Associate, Support Communications, Support Specialist, Terminal Specialist, Tax Analyst, Accountant, Top-up Specialist, Financial Connections Specialist, Data Engineer, and Account owner.

Key mechanism, verified: "If you assign a user multiple roles, they're assigned all the permissions of each individual role." This is a union of roles, with no deny. Source: https://docs.stripe.com/get-started/account/teams/roles

Built-in roles only. The doc does not mention custom Dashboard roles. [unverified: custom Dashboard roles not confirmed either way.]

Security note on the same page, verified: "If an attacker compromises a user with one, they can invite additional users under their control." This is an escalation path through invite rights.

Source for all of 3a: https://docs.stripe.com/get-started/account/teams/roles

### 3b. API keys and restricted API keys (RAKs)

| Claim | Verified text | Source |
|---|---|---|
| Key types: publishable, restricted (rk_), secret (sk_), organisation (sk_org_). | Table on the API keys page | https://docs.stripe.com/keys |
| Permission levels per resource | "None", "Read", or "Write" | https://docs.stripe.com/keys/restricted-api-keys.md |
| Write implies read | "Write permissions imply read permissions" | https://docs.stripe.com/keys/restricted-api-keys.md |
| HTTP mapping used for audit | "GET requests are reads", "POST and DELETE requests are writes" | https://docs.stripe.com/keys/restricted-api-keys.md |
| Error when a key lacks permission | Invalid request error; response body names the permission to add | https://docs.stripe.com/keys/restricted-api-keys.md |
| One RAK per service | "create a separate restricted key for each service" | https://docs.stripe.com/keys/restricted-api-keys.md |
| Secret keys are unrestricted | "Full access to every API resource" | https://docs.stripe.com/keys/restricted-api-keys.md |
| Rotation grace period | "both the old and new keys work for up to 7 days" | https://docs.stripe.com/keys.md |
| Access policies (IP, ASN, country, threat sources) | "Stripe blocks the request and notifies you." Policy changes "apply immediately to all API keys it's assigned to." | https://docs.stripe.com/keys.md |
| Deleting an access policy | "Those keys allow requests from any source until you apply another policy." | https://docs.stripe.com/keys.md |
| Agent-tagged keys go through approval rules | Payouts, refunds, account config need a reviewer | https://docs.stripe.com/keys.md |
| Unused keys lose access | Keys unused for creating transfers or payouts for "over 180 days" get limited access | https://docs.stripe.com/keys.md |

Mechanism to quote: a RAK is "drop-in replacement" for a secret key, and migration is done by reading request logs to derive the permission set. Source: https://docs.stripe.com/keys/restricted-api-keys.md

Connect: the RAK form lets you "select the permission to allow for this key when accessing connected accounts" [verified]. Source: https://docs.stripe.com/keys/restricted-api-keys.md

Internal policy engine: no Stripe engineering blog post about an internal authorization engine was found. Job listings for "Authorization Infrastructure" describe a platform that "enforces access controls, provides access observability, and handles policy governance." [verified from listings, weak source] Example: https://jobs.khoslaventures.com/companies/stripe/jobs/49824802-backend-engineer-security-authorization-infrastructure

Internal employee access to merchant data: no public blog found. [unverified: not found]

---

## 4. Company implementations

Ordering: companies with numbers first.

### 4.1 Google Zanzibar (reference design, 2019)

| Claim | Label | Source |
|---|---|---|
| Scales to "trillions of access control lists" | [verified] abstract | https://www.usenix.org/system/files/atc19-pang.pdf |
| "millions of authorization requests per second" | [verified] abstract | same |
| "95th-percentile latency of less than 10 milliseconds" | [verified] abstract | same |
| "availability of greater than 99.999%" | [verified] abstract | same |
| "over 3 years of production use" | [verified] abstract | same |
| "hundreds of client services" | [verified] abstract | same |
| Data model: relation tuples (object, relation, user) | [verified] paper text summarised by fetch; cross-check in the PDF | https://www.usenix.org/system/files/atc19-pang.pdf |
| Consistency via zookies (consistency tokens returned by writes) | [unverified: taken from a TechInterview summary, not the paper text] | https://techinterview.org/system-design-access-control/ |
| Stored in Spanner | [unverified: secondary summary only] | https://www.techinterview.org/post/3233466288/system-design-access-control/ |
| Talk page | [verified] | https://www.usenix.org/conference/atc19/presentation/pang |

Talk metadata: USENIX ATC '19, Renton, WA, July 2019. Authors include Ruoming Pang, Abhishek Parmar, and others. Source: https://www.usenix.org/conference/atc19/presentation/pang

### 4.2 Airbnb Himeji (Zanzibar-inspired)

| Claim | Label | Source |
|---|---|---|
| Throughput grew from zero in March 2020 to "850k entities/sec in March 2021" | [verified] via InfoQ news summary | https://www.infoq.com/news/2021/05/airbnb-himeji |
| "99.999% availability" | [verified] via InfoQ | same |
| "12-millisecond latency at the 99 percentile" | [verified] via InfoQ | same |
| Sharded, replicated in-memory cache, Aurora durable store | [verified] via InfoQ | same |
| "ensures a 98% hit ratio" | [unverified] appears in a Substack explainer and InfoQ; not checked on the Airbnb Medium post | https://arpit.substack.com/p/how-airbnb-designed-and-scaled-its |
| Invalidation via SpinalTap and Kafka | [verified] via InfoQ | https://www.infoq.com/news/2021/05/airbnb-himeji |
| Data model: principal, entity, relation; tuples "<entity> # <relation> @ <principal>"; unions to avoid storing every derived permission | [verified] via Substack explainer | https://arpit.substack.com/p/how-airbnb-designed-and-scaled-its |
| Original post | Airbnb Engineering, "Himeji: A Scalable Centralized System for Authorization at Airbnb" (Medium). Not fetched directly. | https://medium.com/airbnb-engineering/himeji-a-scalable-centralized-system-for-authorization-at-airbnb-341664924574 |
| Current scale "over 8 million authorization checks per second" | [unverified] Airbnb job posting quoted by a search summary; not checked | (search summary, no stable URL) |
| Migration approach | Not found in fetched text | n/a |

Note: the 850k figure is "entities/sec", not checks/sec. Do not mix the two in the note.

### 4.3 Figma permissions DSL

| Claim | Label | Source |
|---|---|---|
| Permission checks were "around 20%" of database load | [verified] via fetch summary of the post | https://www.figma.com/blog/how-we-rolled-out-our-own-permissions-dsl-at-figma/ |
| Lazy loading "more than halved" total permissions evaluation time | [verified] via fetch summary | same |
| Some checks could load "more than a dozen tables" | [verified] via fetch summary | same |
| Porting the engine to another language took "two to three days for a senior engineer" | [verified] via fetch summary | same |
| Migration relied on "hundreds of tests written over many years" | [verified] via fetch summary | same |
| Policies "would be fully abstract and contain no code execution" | [verified] quote via fetch summary | same |
| "We all but eliminated incidents and bugs caused by drifts in the logic between our Ruby and LiveGraph codebase" | [verified] quote via fetch summary | same |
| Written in TypeScript | [verified] | same |
| Shadow evaluation (run new and old side by side) | NOT confirmed. Post as fetched has no shadow or mismatch section. | same |

Mechanism: one policy language, one cross-platform evaluator, so client and server agree. Relevant to the "two engines drift" failure mode in section 5.

### 4.4 Uber Charter and authfx (ABAC)

| Claim | Label | Source |
|---|---|---|
| Published July 13, 2023 by Alan Cao (Core Security Engineering) | [verified] | https://eng.uber.com/blog/attribute-based-access-control-at-uber/ |
| Charter is the central service where policies are managed, then distributed to services | [verified] | https://www.uber.com/blog/attribute-based-access-control-at-uber |
| authfx is a local library in each service that evaluates policies | [verified] | same |
| "70 Uber services have implemented ABAC policies" | [verified] | same |
| CEL expression evaluation takes "only a few microseconds" | [verified] | same |
| Why the basic model was extended: resource attributes beyond a UUID, actor-resource relationships (manager of an employee), and AND across multiple groups | [verified] | same |
| Attribute stores: one service can use several stores, one store can serve several services | [verified] | same |
| Migration or rollout plan | Not in the article. | same |

Note: the Uber post says Charter is "similar in concept to AWS IAM or Google Cloud IAM". [verified]

### 4.5 Okta FGA (OpenFGA, Zanzibar-inspired, commercial)

| Claim | Label | Source |
|---|---|---|
| Scale test at "1 million Requests per Second (RPS) and 100 billion relationship tuples" | [unverified] seen in a search summary of Okta material; not checked on the primary page | https://auth0.com/blog/getting-unlimited-scalability-with-okta-fine-grained-authorization/ |
| "approximately 100 billion relationships and over 1 million requests per second" | [verified] via Help Net Security news | https://www.helpnetsecurity.com/2024/03/05/okta-fga/ |
| Built on OpenFGA, "inspired by Google Zanzibar" | [verified] via search summary of Okta text | https://openfga.dev/docs/adopters.md |
| Named customers | Not found with latency data. | n/a |

### 4.6 Carta (Zanzibar-based AuthZ)

| Claim | Label | Source |
|---|---|---|
| Post title "AuthZ: Carta's highly scalable permissions system" exists on Medium | [unverified] title seen in an Auth0 slide reference; Medium not fetched | https://authorizationinsoftware.auth0.com/public/49/Authorization-in-Software-f9b69587/9bc5ba32 |
| Numbers, migration, tuple counts | Not found. | n/a |

### 4.7 GitHub (fine-grained permissions)

| Claim | Label | Source |
|---|---|---|
| No GitHub engineering post on its internal authorization service found. | [verified] negative result from search | n/a |
| Fine-grained PATs: per-repository permissions, org owner approval, one-year maximum lifetime | [unverified] from a DevClass news article, not the GitHub docs | https://www.devclass.com/development/2022/10/19/github-fixes-over-broad-token-permissions-with-fine-grained-personal-access-tokens-and-controversial-enforced-expiration/1626486 |
| Five fine-grained repository roles; custom roles for Enterprise | [unverified] from Aserto analysis (vendor) | https://aserto.com/blog/authorize-like-github |

### 4.8 Netflix (OPA / distributed authorization)

| Claim | Label | Source |
|---|---|---|
| Velocity 2018 talk, "The distributed authorization system: A Netflix case study" (Manish Mehta and Torin Sandall) | [unverified] title and host found in search; slides not fetched | https://conferences.oreilly.com/velocity/vl-ca-2018/ (slide PDF listed in search) |
| KubeCon 2017 talk on OPA-based access control | [unverified] | https://raw.githack.com/mm-k8s-ug/kubecon-slides/master/slides/2017-kubecon-na/How%20Netflix%20Is%20Solving%20Authorization%20Across%20Their%20Cloud%20%5BI%5D%20-%20Manish%20Mehta%20&%20Torin%20Sandall,%20Netflix%20-%20Manish%20Mehta%20Netflix%20AuthZ%20V4.pdf |
| Numbers | None found. | n/a |

### 4.9 Companies searched with no primary source found

| Company | Result |
|---|---|
| Pinterest | No Zanzibar-style authorization post found. Search returned only Zanzibar background. |
| Slack | No Slack engineering post found. One Django library doc says Zanzibar-inspired systems are used by Slack. [unverified, secondhand] https://django-rebac.readthedocs.io/en/latest/getting-started/zanzibar-model/ |
| Notion, Canva, Segment, Lyft | Not searched in this pass. Do not cite without a source. |
| Google Cloud IAM | Public docs exist; policy model not re-fetched here. Uber's post compares Charter to it. [verified: comparison only] |
| AWS IAM | See section 4.10. |

### 4.10 AWS IAM policy evaluation (explicit deny wins)

| Claim | Verified text | Source |
|---|---|---|
| Identity and resource policies: union of allows | "If an action is allowed by an identity-based policy, a resource-based policy, or both, then AWS allows the action." | https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_evaluation-logic.html |
| Explicit deny overrides allow | "An explicit deny in either of these policies overrides the allow." | same |
| Permissions boundary is an intersection | "the resulting permissions are the intersection of the two categories" | same |
| SCP and RCP must also allow | "an action must be allowed by all three policy types" | same |
| Per-second evaluation volume | Not published on this page. | n/a |

Interview use: explicit deny plus default deny is the right default for the note.

### 4.11 Comparison table

| Company or system | Model | Numbers published (primary) | Migration story | Source |
|---|---|---|---|---|
| Google Zanzibar | ReBAC, tuples | Yes: trillions of ACLs, millions RPS, p95 under 10 ms, 99.999% | Not in abstract | https://www.usenix.org/system/files/atc19-pang.pdf |
| Airbnb Himeji | ReBAC, Zanzibar-like | 850k entities/s (InfoQ), 12 ms p99, 99.999% | Not found | https://www.infoq.com/news/2021/05/airbnb-himeji |
| Figma | Custom DSL, RBAC-like rules | 20% DB load, halved eval time | Rewrite with tests, no shadow data | https://www.figma.com/blog/how-we-rolled-out-our-own-permissions-dsl-at-figma/ |
| Uber Charter | ABAC with CEL | 70 services, microseconds for CEL | Not in article | https://eng.uber.com/blog/attribute-based-access-control-at-uber/ |
| Okta FGA | ReBAC on OpenFGA | 100B tuples, 1M RPS (news) | Not found | https://www.helpnetsecurity.com/2024/03/05/okta-fga/ |
| Stripe | Roles plus RAK scopes | Not published | Log-driven RAK migration (docs) | https://docs.stripe.com/keys/restricted-api-keys.md |
| Rippling | Attribute-driven profiles | Not published | Not published | https://www.rippling.com/products/it/platform/permissions |

---

## 5. Migration stories (per-service checks to a central service)

What is public:

| Item | Label | Source |
|---|---|---|
| Figma moved "all our most important permissions rules" into a new engine | [verified] | https://www.figma.com/blog/how-we-rolled-out-our-own-permissions-dsl-at-figma/ |
| Figma's rollout risk was measured by "hundreds of tests written over many years" | [verified] | same |
| Figma's motivation: "bugs, support tickets, and delayed projects" in early 2021 | [verified] via search summary of the post | same |
| Airbnb: a central store and cache, invalidated by change events | [verified] | https://www.infoq.com/news/2021/05/airbnb-himeji |
| Uber: rules moved from service code into Charter, enforced by authfx | [verified] | https://eng.uber.com/blog/attribute-based-access-control-at-uber/ |
| Shadow mode, mismatch rate, duration, rollback | NOT found in any primary post reviewed. Do not state numbers for these. | n/a |

Mechanism to propose for the note, flagged as a design choice, not a sourced fact:
1. Dual-evaluate: serve the old answer, log the new answer, count mismatches per (tenant, action).
2. Gate cutover on a mismatch budget per tenant, then per action.
3. Rollback is a flag flip back to the in-service check.

Source for the pattern itself: none found in this pass. [unverified: design pattern, not a published case]

---

## 6. Incidents and failure modes

| # | Date | Duration | Root cause (as published) | Lesson | Source | Label |
|---|---|---|---|---|---|---|
| 6.1 | 14 Dec 2020 | 47 min (status page); 03:46 to 04:33 PT impact window | User ID Service moved to a new quota system. Old tooling reported usage as zero. After a grace period, automated quota reduction stopped the Paxos leader from writing, and reads went stale, causing authentication lookup errors. Existing safety checks did not cover zero reported load. | A global automated change can cut a shared identity dependency. Add checks for "zero load" and slow global rollouts. | https://status.cloud.google.com/incident/zall/20013 | [verified] |
| 6.2 | 14 Dec 2020 | (same) | Remediation: "Review our quota management automation to prevent fast implementation of global changes" and "Limit the impact on the data plane during User ID Service failures." | Blast radius of identity down means data plane impact. | same | [verified] |
| 6.3 | Nov 2024 | About 16 hours (secondary) | Microsoft MFA outage: latency between MFA frontend and cache under load, then a race condition in backend responses. | Caches on the auth path are on the critical path. | https://duo.com/decipher/software-update-led-to-microsoft-azure-mfa-outage | [unverified] secondary |
| 6.4 | Unknown | Unknown | Microsoft Entra signing-key cleanup job ignored a "retain" state and deleted a key. Relying apps stopped trusting tokens. | Automated key cleanup can revoke trust. Keep a deletion guard. | https://learn.microsoft.com/en-us/answers/a/317011 | [unverified] Microsoft Q&A notice, full RCA not found |
| 6.5 | 29 Oct 2025 | Start 15:45 UTC (one source says 15:41), mitigation 00:05 UTC 30 Oct (secondary) | Azure Front Door configuration change deployed globally, disrupted Entra ID routing and sign-in for dependent services. Sources disagree on timing. | A global config push is a single point of failure for auth. Use staged rollouts. | No primary URL retrieved. Azure status history (official PIR) not fetched. A Medium repost was seen and rejected as a source. | [unverified] |
| 6.6 | Dec 2024 | Unknown | Okta: a change applied incorrectly before deployment pointed login pages at an unavailable Sign-In Widget version. | Deployment ordering breaks login. | https://pingoru.io/providers/okta/incidents/459873 (aggregator) | [unverified] aggregator; check okta.com |
| 6.7 | Dec 2024 | Unknown | Okta: an automated cleanup job removed a reserved DNS record. Okta disabled the job. | Cleanup automation again. | https://pingoru.io/providers/okta/incidents/459848 (aggregator) | [unverified] aggregator |

Notes on section 6:
- The Google incident is the strongest primary source here.
- The Microsoft and Okta items are secondary or aggregator sources. Verify against the official PIR before using numbers.
- No primary "fail open" authorization postmortem from Slack, GitHub, or Figma was found in this pass. [unverified: not searched exhaustively]

Fail-closed rule for the note: when the authorization service cannot answer, deny. Sources: this is a design rule, not a sourced incident. Microsoft's CAE docs say long-lived tokens (up to 28 hours in CAE sessions) are safe only because critical events drive revocation (section 7).

---

## 7. Offboarding and revocation timings

| System | Revocation mechanism | Stated timing | Source | Label |
|---|---|---|---|---|
| Microsoft Entra CAE | Critical events (account disabled or deleted, password reset, MFA enabled, admin revokes refresh tokens, high user risk) | "near real time", with "latency of up to 15 minutes" from event propagation | https://learn.microsoft.com/en-us/entra/identity/conditional-access/concept-continuous-access-evaluation | [verified] |
| Microsoft Entra CAE | IP location policy change | "IP locations policy enforcement is instant" | same | [verified] |
| Microsoft Entra CAE | Token lifetime in CAE sessions | "up to 28 hours" long-lived; default lifetime without CAE is 1 hour | same | [verified] |
| Microsoft Entra CAE | Policy and group changes | "could take up to one day" to replicate; reduced to "two hours" for some policy updates | same | [verified] |
| Microsoft Entra CAE | Immediate effect | Run "revoke-mgusersign" or "Revoke Session" | same | [verified] |
| Microsoft Entra CAE | Guest users | "CAE doesn't support Guest user accounts" | same | [verified] |
| Microsoft Entra CAE | Re-enable after disable | SharePoint and Teams about 15 min; Exchange 35 to 40 min | same | [verified] |
| Okta | Token and session revocation API | Revoke tokens via /revoke; revoke all user sessions via Users API, optionally with oauthTokens | https://developer.okta.com/docs/guides/revoke-tokens/main/ | [verified] |
| Okta | Timing | Page does not say whether access tokens stop immediately or at expiry. No timings. | same | [verified: absence] |
| Okta SCIM | Deactivation as PATCH active=false, not DELETE | Event-driven per a white paper; no Okta number | https://devforum.okta.com/t/challenges-with-scim-delete-implementation-with-just-in-time/33790 | [unverified] forum |
| Stripe | Rotate or expire keys | Rotation grace period up to 7 days; expire is immediate | https://docs.stripe.com/keys.md | [verified] |
| Stripe | Access policy removal | Immediate; "Those keys allow requests from any source" after policy deletion | same | [verified] |
| Rippling | Termination revokes app access | No public timing | https://www.rippling.com/products/it/platform/permissions | [verified: absence] |
| Rippling (guide) | Offboarding target | "Urgent steps (identity session kill, SSO disable, device lock) complete within minutes" | https://www.designgurus.io/answers/detail/what-to-expect-in-the-rippling-system-design-interview | guide, not first-hand |

Design implications for the note:
- Split revocation into urgent (session kill, token revoke, minutes) and eventual (app deprovisioning, hours).
- Use an event push (like CAE) for the urgent path, and a TTL cap as backstop (Microsoft uses 1 hour for non-CAE clients).
- Measure revoke-to-deny latency per tenant and page on breach.

---

## 8. Numbers to use

| Number | Value | Source URL | Verified or [unverified] |
|---|---|---|---|
| Zanzibar ACLs | Trillions | https://www.usenix.org/system/files/atc19-pang.pdf | verified (abstract) |
| Zanzibar checks | Millions per second | same | verified (abstract) |
| Zanzibar p95 latency | Under 10 ms | same | verified (abstract) |
| Zanzibar availability | Above 99.999% | same | verified (abstract) |
| Zanzibar production years | Over 3 | same | verified (abstract) |
| Himeji throughput | 850k entities/s (Mar 2021) | https://www.infoq.com/news/2021/05/airbnb-himeji | verified (InfoQ), not on Airbnb primary |
| Himeji p99 latency | 12 ms | same | verified (InfoQ), not on Airbnb primary |
| Himeji cache hit ratio | About 98% | https://arpit.substack.com/p/how-airbnb-designed-and-scaled-its | [unverified] |
| Himeji availability | 99.999% | https://www.infoq.com/news/2021/05/airbnb-himeji | verified (InfoQ) |
| Himeji current checks | Over 8 million per second | (job posting via search) | [unverified] |
| Figma DB load from permission checks | About 20% | https://www.figma.com/blog/how-we-rolled-out-our-own-permissions-dsl-at-figma/ | verified (fetch summary) |
| Figma eval time cut by lazy loading | More than half | same | verified (fetch summary) |
| Uber ABAC services | 70 | https://www.uber.com/blog/attribute-based-access-control-at-uber | verified |
| Uber CEL eval time | Few microseconds | same | verified |
| Okta FGA scale | 1M RPS, 100B tuples | https://www.helpnetsecurity.com/2024/03/05/okta-fga/ | [unverified] news, primary not checked |
| Google outage duration | 47 min | https://status.cloud.google.com/incident/zall/20013 | verified |
| Google outage impact window | 03:46 to 04:33 PT, 14 Dec 2020 | same | verified |
| Stripe RAK permission levels | None, Read, Write | https://docs.stripe.com/keys/restricted-api-keys.md | verified |
| Stripe key rotation grace | Up to 7 days | https://docs.stripe.com/keys.md | verified |
| Stripe built-in roles | 26 | https://docs.stripe.com/get-started/account/teams/roles | verified (counted from page) |
| Stripe key inactivity limit | 180 days | https://docs.stripe.com/keys.md | verified |
| Entra CAE revocation latency | Up to 15 min | https://learn.microsoft.com/en-us/entra/identity/conditional-access/concept-continuous-access-evaluation | verified |
| Entra token lifetime, default | 1 hour | same | verified |
| Entra token lifetime, CAE | Up to 28 hours | same | verified |
| Entra policy replication | Up to 1 day, 2 hours for some | same | verified |
| Rippling Supergroups | Attribute-based dynamic lists | https://www.rippling.com/products/it/platform/permissions | verified (no numbers) |
| Microsoft MFA outage | About 16 hours | https://duo.com/decipher/software-update-led-to-microsoft-azure-mfa-outage | [unverified] secondary |
| Zanzibar consistency token | Zookie | https://techinterview.org/system-design-access-control/ | [unverified] |

---

## Gaps and next steps

- Carta, Pinterest, Slack, Notion, Canva, Segment, Lyft: no primary source reviewed. Fetch the Carta Medium post and the Netflix Velocity 2018 slides before citing.
- Figma shadow evaluation: confirm on the full post or Figma's other permissions posts.
- Aced (Stripe) and Hello Interview (Zanzibar) guides: not retrieved.
- Entra CAE and Okta: find official post-incident reviews on the Azure status history and okta.com trust pages.
- Stripe internal policy engine: no Stripe engineering post found. Check stripe.com/blog for "authorization".
