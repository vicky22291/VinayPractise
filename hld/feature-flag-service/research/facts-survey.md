# Facts survey: feature flag service

Study note: "Design a feature flag service, like Amazon Weblab: on/off, percentage rollout, allow and block lists; many backend services check flags while handling requests." (Stripe Staff interview prompt)

Built 2026-10-08 from live fetches. This file is the evidence base. The note itself should quote from here.

## Method and tags

- SDK defaults and hashing: `curl` of raw source from raw.githubusercontent.com, then `grep -n` and `sed -n`. Code wins over docs when they disagree.
- PDFs: `pdftotext -layout`. Docs pages: `curl` then a Python tag-stripper (`python3 -I`), or WebFetch where curl returned a 404, a rate-limit page, or a JavaScript shell.
- WebSearch was used only to find leads. Nothing from a search snippet is used as a fact unless a page was opened.
- Tags used below:
  - [code] read in the source file at the URL given.
  - [doc] read in the docs or paper text at the URL given.
  - [webfetch-summary] returned by WebFetch's small model, not raw text. Treat as lower confidence than [code] or [doc].
  - [unverified] not opened, or opened but the value was not found. No number from these is used in the Numbers list.
- Integer counts only. Derived numbers show the arithmetic.
- Excluded by rule: Medium, dev.to, Wikipedia, ByteByteGo, DesignGurus, GeeksforGeeks, random blogs.

## 0. Quick answers for the note

- Flag rollout uses a deterministic hash of (flag key, salt, user key). It is not a random draw per request. [code: https://raw.githubusercontent.com/launchdarkly/go-server-sdk-evaluation/v3/evaluator_bucketing.go]
- Server SDKs evaluate in process. LaunchDarkly's Relay Proxy connects to the streaming API and proxies that connection to servers in the customer's network. [doc: https://docs.launchdarkly.com/home/relay-proxy]
- Polling defaults: LaunchDarkly 30 s (also its minimum). Unleash 15000 ms. [code: https://raw.githubusercontent.com/launchdarkly/go-server-sdk/v7/ldcomponents/polling_data_source_builder.go] [code: https://raw.githubusercontent.com/Unleash/unleash-client-node/main/src/repository/index.ts]
- Two of the three post-mortems in section 8 describe a change that reached every region before regional checks caught it (Google Cloud: "replicated globally within seconds"; Cloudflare: the feature file "was then propagated to all the machines"). The Knight Capital SEC order describes a repurposed flag that was live on 1 of 8 servers.

---

## 1. LaunchDarkly

### 1a. Delivery to server SDKs (streaming vs polling)

| Fact | Value (exact) | Source |
|---|---|---|
| Polling default | `DefaultPollInterval = 30 * time.Second` | [code: https://raw.githubusercontent.com/launchdarkly/go-server-sdk/v7/ldcomponents/polling_data_source_builder.go] |
| Polling minimum | "The default and minimum value is DefaultPollInterval. Values less than this will be set to the default." Same file. | [code: same URL] |
| Polls per day at 30 s per SDK instance | 86,400 s / 30 s = 2,880 requests | arithmetic on the row above |
| Streaming reconnect default | `DefaultInitialReconnectDelay = time.Second` (1 s) | [code: https://raw.githubusercontent.com/launchdarkly/go-server-sdk/v7/ldcomponents/streaming_data_source_builder.go] |
| Extended poll delay after failure | `defaultExtendedInitialPollDelay = 5 * time.Minute` (5 min) | [code: https://raw.githubusercontent.com/launchdarkly/go-server-sdk/v7/internal/datasource/polling_data_source.go] |
| Polling backoff rule | Source comment: "Effective ceiling is max(extendedPollMaxDelay, PollInterval)". Code: "initialDelay is clamped to at least PollInterval". | [code: https://raw.githubusercontent.com/launchdarkly/go-server-sdk/v7/internal/datasource/polling_strategy.go] |
| Init wait parameter | `MakeClient(sdkKey, waitFor)` takes the wait from the caller. No default in the constructor. A constant `highWaitForDuration = 60 * time.Second` logs a warning above 60 s. The doc comment says the constructor returns "when the timeout set by the waitFor parameter expires". | [code: https://raw.githubusercontent.com/launchdarkly/go-server-sdk/v7/ldclient.go] |
| Behaviour on init timeout (returns default value?) | [unverified] not opened | n/a |
| Behaviour when stream drops (last known values kept?) | [unverified] not opened. Only the reconnect default (1 s) is verified. | n/a |

### 1b. Where evaluation runs

- Relay Proxy: "The LaunchDarkly Relay Proxy is a small Go application that runs on your own infrastructure. It connects to the LaunchDarkly streaming API and proxies that connection to clients within your organization's network." [doc: https://docs.launchdarkly.com/home/relay-proxy]
- Relay Proxy scope, verbatim: "The Relay Proxy reduces outbound network connections, not billed service connections." [doc: https://docs.launchdarkly.com/home/relay-proxy]
- Client-side SDKs evaluate on LaunchDarkly servers: [unverified] the claim is common LaunchDarkly guidance but I did not open a page that states it. Do not quote it without a source.
- Relay Proxy daemon mode with a persistent store (Redis, Consul, DynamoDB): [unverified] the page I read was the overview. Store names are not verified here.

### 1c. Bucketing algorithm (percentage rollouts)

Code, Go evaluation package. [code: https://raw.githubusercontent.com/launchdarkly/go-server-sdk-evaluation/v3/evaluator_bucketing.go]

- Hash input when no seed: `key + "." + salt` and then `"." + bucketBy value`. If a seed is set, the input is `seed + "."` and then the value. Attribute default when `bucketBy` is unset: the context key. Experiments always bucket by key.
- Hash function: `sha1.Sum(hashInput.Data)`. SHA-1, not a fast non-crypto hash.
- Hex characters used: `hash := hexEncodedChars[:15]`, which is the first 15 hex characters (60 bits).
- Divisor: `longScale = float32(0xFFFFFFFFFFFFFFF)`. 0xFFFFFFFFFFFFFFF is 15 hex F characters, equal to 2^60 - 1 = 1152921504606846975 (confirmed by Python: `int('F'*15,16)`).
- Bucket: `bucket := float32(intVal) / longScale`, a value in [0,1].

Docs, same algorithm, quoted. [webfetch-summary: https://launchdarkly.com/docs/sdk/concepts/flag-evaluation-rules]

- "Concatenate the flag's key, the flag's salt, and the context's attribute value. Concatenate them with periods, `.`."
- "Copy the first 15 characters of the SHA1 of the above."
- "Divide the resulting base 10 integer by `0xFFFFFFFFFFFFFFF` (`1152921504606846975`)."
- "Weighted variations are a subset of the variation index and a non-negative integer between 0 and 100,000 acting as that variation's weight."

Scale in the note: weights are integers 0 to 100,000, and 100,000 = 100%. One unit = 100 / 100,000 = 0.001%. This matches the 0.001% resolution in the prompt. [webfetch-summary: https://launchdarkly.com/docs/sdk/concepts/flag-evaluation-rules]
Code vs docs (code wins): the docs describe exact integer division. The Go code computes `float32(intVal) / longScale`, so the division is done in 32-bit float. A float32 has a 24-bit mantissa, so the bucket is not exact to 2^-60. Buckets very close to a boundary may differ from an exact-integer implementation. This is a fidelity note, not a practical problem for percentages at 0.001% resolution. [code: https://raw.githubusercontent.com/launchdarkly/go-server-sdk-evaluation/v3/evaluator_bucketing.go]

### 1d. Evaluation order

[webfetch-summary: https://launchdarkly.com/docs/sdk/concepts/flag-evaluation-rules]

1. Off check: "If targeting is off, the SDK does not complete the rest of the checks, and serves the default off variation." Off reason: `OFF`.
2. Prerequisites: "Prerequisite evaluation is short-circuited, which means the SDK returns after the first failure."
3. Individual targets: "If a target contains the context's key, return the associated variation with the `TARGET_MATCH` evaluation reason."
4. Targeting rules: the first matching rule wins. The default rule runs only when "no rules matched the context".
5. Fallthrough: "Fallthrough is the last step in flag evaluation."

---

## 2. Unleash (open source)

### 2a. Poll interval and metrics

| Fact | Value (exact) | Source |
|---|---|---|
| `refreshInterval` default (code) | `refreshInterval = 15_000` (ms) = 15 s | [code: https://raw.githubusercontent.com/Unleash/unleash-client-node/main/src/repository/index.ts] |
| `refreshInterval` default (docs) | "The poll interval to check for updates. Defaults to 15000ms." | [doc: https://docs.getunleash.io/reference/sdks/node] |
| `metricsInterval` default (docs) | "How often the client should send metrics to Unleash API. Defaults to 60000ms." (60 s) | [doc: https://docs.getunleash.io/reference/sdks/node] |
| Polls per day at 15 s | 86,400 / 15 = 5,760 requests per client instance | arithmetic |
| Metrics sends per day at 60 s | 86,400 / 60 = 1,440 | arithmetic |
| Backoff after failures | `this.failures = Math.min(this.failures + 1, 10)`. Next delay = `refreshInterval + failures * refreshInterval`. | [code: https://raw.githubusercontent.com/Unleash/unleash-client-node/main/src/repository/polling-fetcher.ts] |
| Maximum poll delay under backoff | 15 s + 10 x 15 s = 165 s (failures capped at 10, so 15 x (1 + 10) = 165) | arithmetic on the rows above |

### 2b. Stickiness hash (percentage rollout)

Source: [code: https://raw.githubusercontent.com/Unleash/unleash-client-node/main/src/strategy/util.ts]

- Hash library: `import * as murmurHash3 from 'murmurhash3js';`
- Function: `murmurHash3.x86.hash32(`${groupId}:${id}`, seed)`. That is MurmurHash3, 32-bit, x86 variant.
- Seed for strategy rollouts: `const STRATEGY_SEED = 0;` (seed 0).
- Normalization: `return (hash % normalizer) + 1;` With normalizer 100 (`normalizedStrategyValue`), the output is an integer in 1..100. Resolution: 1 bucket = 1%.

Strategy-specific behaviour:

- `gradualRolloutUserId`: [code: https://raw.githubusercontent.com/Unleash/unleash-client-node/main/src/strategy/gradual-rollout-user-id.ts] uses `context.userId` only. If `userId` is missing it returns false. `groupId` defaults to the empty string.
- `flexibleRollout`: [code: https://raw.githubusercontent.com/Unleash/unleash-client-node/main/src/strategy/flexible-rollout-strategy.ts] `groupId = parameters.groupId || context.featureToggle || ''`. So the group id defaults to the flag name. This is what makes rollouts independent across flags. Enabled when `percentage > 0 && normalizedUserId <= percentage`.
- Default stickiness value (`STICKINESS.default`): [unverified] the constant was not opened.

### 2c. Bootstrap and backup when the server is unreachable

- Bootstrap read order: `if (this.url)` loads from URL, then `if (this.filePath)` loads from file. [code: https://raw.githubusercontent.com/Unleash/unleash-client-node/main/src/repository/bootstrap-provider.ts]
- `bootstrapOverride` default is `true`. [code: https://raw.githubusercontent.com/Unleash/unleash-client-node/main/src/repository/index.ts]
- Backup file name: `join(this.backupPath, `/unleash-backup-${safeName(key)}.json`)`. A `backupPath` is required; the constructor throws `'backup Path is required'` when it is missing. [code: https://raw.githubusercontent.com/Unleash/unleash-client-node/main/src/repository/storage-provider-file.ts]
- Docs: "until synchronization, all features will evaluate to `false` unless you have a bootstrapped configuration." [doc: https://docs.getunleash.io/reference/sdks/node]
- Docs: the SDK "writes a backup of the feature flag configuration to a file on disk" on each update. [doc: https://docs.getunleash.io/reference/sdks/node]

The docs state that an unsynced flag evaluates to `false` unless bootstrapped. The order in which bootstrap and the file backup are read at startup is not stated in the docs, so the note should not assert one.

### 2d. Unleash Edge

- Docs: "Unleash Enterprise Edge is a lightweight caching layer designed to improve scalability, performance, and resilience." [webfetch-summary: https://docs.getunleash.io/unleash-edge]
- Purpose in the note: a read replica between SDKs and the Unleash API, so many SDKs do not add read load to the main instance. [webfetch-summary: https://docs.getunleash.io/unleash-edge]

---

## 3. Hashing schemes in other SDKs (one row each)

| Scheme | Hash | Input | Resolution (per the code) | Source |
|---|---|---|---|---|
| LaunchDarkly | SHA-1, first 15 hex chars | `key.salt.attrValue` (or `seed.attrValue`) | 2^60 - 1 divisor, weights in 0.001% steps | [code: https://raw.githubusercontent.com/launchdarkly/go-server-sdk-evaluation/v3/evaluator_bucketing.go] |
| Unleash (Node) | MurmurHash3 x86 32-bit, seed 0 | `groupId:stickinessId` | `(hash % 100) + 1`, 1..100, 1% steps | [code: https://raw.githubusercontent.com/Unleash/unleash-client-node/main/src/strategy/util.ts] |
| GrowthBook v2 | FNV-1a 32-bit, applied twice | `fnv1a32(fnv1a32(seed + value) + "") % 10000 / 10000` | 10000 buckets, 0.01% steps | [code: https://raw.githubusercontent.com/growthbook/growthbook/main/packages/sdk-js/src/util.ts] |
| GrowthBook v1 | FNV-1a 32-bit, once | `fnv1a32(value + seed) % 1000 / 1000` | 1000 buckets, 0.1% steps | [code: same URL] |
| Statsig (Node) | `computeUserHash` (definition not opened), then BigInt `% 1000` | `salt + "." + unitID` | 1000 buckets, 0.1% steps | [code: https://raw.githubusercontent.com/statsig-io/node-js-server-sdk/main/src/Evaluator.ts] |
| OpenFeature flagd | MurmurHash3 32-bit (`murmur3.StringSum32`), then `(hash * totalWeight) >> 32` | `flagKey + targetingKey` unless `bucketBy` is set | 2^32 = 4294967296 positions | [code: https://raw.githubusercontent.com/open-feature/flagd/main/core/pkg/evaluator/fractional.go] |

Details and corrections for each row:

- GrowthBook default version: [unverified]. The JS docs page says "bucketingV2: >= v0.23.0" and the badge "v2 Hashing". [webfetch-summary: https://docs.growthbook.io/lib/js] The default `hashVersion` value was not found in the text read.
- Statsig: the prompt guessed SHA-256. The code shows `const hashAlgo = options?.hash ?? 'djb2';` (Evaluator.ts, the default for named hashes). `hashString` supports `'sha256' | 'djb2' | 'none'`. [code: https://raw.githubusercontent.com/statsig-io/node-js-server-sdk/main/src/utils/Hashing.ts] The bucketing path uses `computeUserHash` (imported, definition not opened), so the bucket hash function is [unverified].
- flagd bucketing key: `bucketBy = fmt.Sprintf("%s%s", properties.FlagKey, targetingKey)`, so the flag key is in the input. That gives per-flag independence. [code: same URL]

Rollout independence rule (verified in code for three schemes): the flag key or group id is part of the hash input. LaunchDarkly uses a per-flag salt. Unleash uses `groupId` defaulting to the flag name. flagd prefixes the flag key. Without this, the same users would land in the same 1% slice for every flag.

---

## 4. OpenFeature specification

All section numbers come from the spec repository. [doc: https://raw.githubusercontent.com/open-feature/spec/main/specification/sections/01-flag-evaluation.md] [doc: https://raw.githubusercontent.com/open-feature/spec/main/specification/types.md]

### 4a. API shape

- Typed evaluation methods take `flag key` (string, required), `default value` (required), and `evaluation context` (optional, dynamic-context paradigm) or `evaluation options` (optional). [doc: 01-flag-evaluation.md, Requirement 1.3.2.1 and Condition 1.3.1]

### 4b. Errors and the default value

- Requirement 1.4.10: "Methods, functions, or operations on the client **MUST NOT** throw exceptions, or otherwise abnormally terminate. Flag evaluation calls must always return the `default value` in the event of abnormal execution." [doc: 01-flag-evaluation.md]
- Requirement 1.4.8: in abnormal execution the evaluation details "**MUST** contain an `error code`." [doc: 01-flag-evaluation.md]
- Requirement 1.4.9: the `reason` "**SHOULD** indicate an error" in abnormal execution. [doc: 01-flag-evaluation.md]
- Requirement 1.3.4: a type mismatch "should be returned" as the `default value`. [doc: 01-flag-evaluation.md]
- Requirement 1.4.11: "Methods ... **SHOULD NOT** write log messages." Reason given: "The client methods (particularly the evaluation methods) run in hot code paths." [doc: 01-flag-evaluation.md]

### 4c. Error codes (count: 8)

Table "Error Code" in types.md: `PROVIDER_NOT_READY`, `FLAG_NOT_FOUND`, `PARSE_ERROR`, `TYPE_MISMATCH`, `TARGETING_KEY_MISSING`, `INVALID_CONTEXT`, `PROVIDER_FATAL`, `GENERAL`. [doc: https://raw.githubusercontent.com/open-feature/spec/main/specification/types.md, "Error Code" section, lines 102 to 109 of the file]

### 4d. Resolution reasons (count: 8)

Table "Resolution Reason" in types.md: `STATIC`, `DEFAULT`, `TARGETING_MATCH`, `SPLIT`, `CACHED`, `DISABLED`, `UNKNOWN`, `ERROR`. [doc: types.md, "Resolution Reason" section, lines 65 to 73 of the file]


---

## 5. AWS AppConfig (feature flags)

Source for deployment mechanics: [doc: https://docs.aws.amazon.com/appconfig/latest/userguide/appconfig-creating-deployment-strategy.html]

- Deployment types: "AWS AppConfig supports Linear and Exponential deployment types."
- Linear example, verbatim: "Here's an example timeline for a 10 hour deployment that uses 20% linear growth": 0 hour 0%, 2 hour 20%, 4 hour 40%, 6 hour 60%, 8 hour 80%, 10 hour 100%. Derived: 100% / 20% = 5 steps, 10 hours / 5 = 2 hours per step. Matches the doc.
- Exponential: "G*(2^N)", where G is the step percentage and N the number of steps. Example in the doc: growth factor 2 gives 2*(2^0), 2*(2^1), 2*(2^2) (2%, 4%, 8%). [doc: same URL]
- Bake time: "the amount of time AWS AppConfig monitors for Amazon CloudWatch alarms after the configuration has been deployed to 100% of its targets, before considering the deployment to be complete. If an alarm is triggered during this time, AWS AppConfig rolls back the deployment." [doc: same URL]
- Agent support: "AWS AppConfig Agent (version 2.0.136060 or later) supports deploying feature flag or fre[eform]..." (text truncated by extraction). [doc: same URL]
- Predefined strategy names and values (for example AllAtOnce, its bake time): [unverified]. The predefined-strategies page did not render through WebFetch or curl. Use `aws appconfig list-deployment-strategies` to fetch them. Do not quote values here.
- Feature flag size limit and quota names: [unverified]. The quotas page returned no content.

---

## 6. Meta: Configerator and Gatekeeper (Tang et al., SOSP 2015)

Paper: "Holistic Configuration Management at Facebook", SOSP 2015. PDF: https://research.facebook.com/file/877841159827226/holistic-configuration-management-at-facebook.pdf (the URL redirects to a Meta CDN; the text below was extracted with `pdftotext -layout` from the copy served by that redirect).

### 6a. Scale and change rate

- Abstract: "Every day, they undergo thousands of online configuration changes, and execute trillions of configuration checks". [doc: research.facebook.com PDF, abstract]
- Integer count of changes per day: [unverified]. Only "thousands" is stated.

### 6b. Propagation latency

- Pipeline, verbatim: "The git tailer writes the change to Zeus, which propagates the change to all subscribing servers through a distribution tree." [doc: same PDF, section 6.3 area]
- Three components, verbatim:
  - "It takes about 5 seconds to commit the change into the shared git repository"
  - "The git tailer ... takes about 5 seconds to fetch config changes from the shared git repository"
  - "The last step takes about 4.5 seconds to reach hundreds of thousands of servers distributed across multiple continents."
- Sum: 5 + 5 + 4.5 = 14.5 seconds end to end (arithmetic on the three numbers).
- Large configs via PackageVessel (section 3.5): "consistently and reliably delivers large configs to the live servers in less than four minutes." [doc: same PDF]

### 6c. Gatekeeper evaluation model

- Gatekeeper gate is a conjunction of predicates called restraints. "The condition in an if-statement is a conjunction of predicates called restraints." Once the if-statement matches, "it probabilistically determines whether to pass or fail the gate, depending on a configurable probability". [doc: same PDF, section 4]
- Restraints are statically implemented in PHP or C++: "Internally, a restraint is statically implemented in PHP or C++. Currently, hundreds of restraints have been implemented". [doc: same PDF, section 4]
- Rollout control: "controls user sampling, e.g., 1% or 10%." [doc: same PDF, section 4]
- Staged rollout example: "Gatekeeper may only enable the product feature to the engineers developing the feature ... increasing percentage of Facebook employees, e.g., 1%→10%→100%" then "5% of the users from a specific region" then "1%→ 10%→100%". [doc: same PDF, section 4]

### 6d. Config errors and canary

- Section 6.4 table, "Type of Config Issues": Type I "common config errors" 42%, Type II "subtle config errors" 36%, Type III "valid config changes exposing code bugs" 22%. These are shares of config issues. They are not shares of incidents. [doc: same PDF, section 6.4]
- Paper's own sentence: "Configuration errors are a major source of site outages". [doc: same PDF, section 3.3] No percentage of incidents is given.
- Canary service: "The canary service automatically tests a new config on a..." (section 3.3). A canary spec describes "the new config should not be more than x% lower than" a baseline. [doc: same PDF, section 3.3]

---

## 7. Internal systems: Amazon Weblab, Uber Flipr, Slack, Stripe

### 7a. Amazon Weblab

- No primary Amazon page about Weblab was opened. WebSearch returned job postings and a forum thread only. [unverified]

### 7b. Uber Flipr (primary: Uber engineering blog)

Source: [doc: https://www.uber.com/us/en/blog/flipr/] (article dated April 12, 2021 per the page text, via WebFetch summary of the page.)

- "Flipr manages over 350K active properties, with approximately 150K changes per week."
- "This configuration data is used by over 700 services at Uber across 50K+ hosts," and "generating around 3 million QPS for our backend systems."
- Gateway tier: "a fan-out cache of gateway services that keep up-to-date copies cached".
- Derived: 150K changes per week / 7 days = 21,428 changes per day (integer, truncated from 21,428.57).
- Derived: 3,000,000 QPS / 50,000 hosts = 60 QPS per host as an upper bound, since the article says "50K+" hosts.

### 7c. Slack

- No Slack primary page about its own feature flag or experiment system was opened. [unverified]
- Confidence (experimentation platform): no source linking Slack to it was found. Do not attribute it to Slack.

### 7d. Stripe

- Careers listing: [doc: https://stripe.com/careers/listing/staff-engineer-release-engineering/8038771] The text reads "...with Feature Deployments on change-safety tooling (feature flags, configuration management, change audit logs)...". This says collaboration on change-safety tooling. It does not say that the team owns the flag system. See Conflicts.
- Also in the listing: "...with regular collaboration with the Resource Automation and Feature Deployments teams." [doc: same URL]

---

## 8. Incidents where a flag or config change was the trigger

### 8a. Knight Capital, 1 August 2012 (SEC order, Release 34-70694)

Source: SEC order, [doc: https://www.sec.gov/litigation/admin/2013/34-70694.pdf]. Read from the PDF text (pdftotext). Paragraph numbers are the order's own.

- Paragraph 13: "The new RLP code also repurposed a flag that was formerly used to activate the Power Peg code." And: "Knight intended to delete the Power Peg code so that when this flag was set to 'yes,' the new RLP functionality ... would be engaged."
- Paragraph 15: "Beginning on July 27, 2012, Knight deployed the new RLP code in SMARS in stages"; "one of Knight's technicians did not copy the new code to one of the eight SMARS computer servers."
- Paragraph 16: "The seven servers that received the new code processed these orders correctly. However, orders sent with the repurposed flag to the eighth server triggered the defective Power Peg code still present on that server."
- Paragraph 17: "For the 212 incoming parent orders that were processed by the defective Power Peg code, SMARS sent millions of child orders, resulting in 4 million executions in 154 stocks for more than 397 million shares in approximately 45 minutes." And: "Knight inadvertently assumed an approximately $3.5 billion net long position in 80 stocks and an approximately $3.15 billion net short position in 74 stocks. Ultimately, Knight realized a $460 million loss on these positions."
- SEC press release (WebFetch summary): [webfetch-summary: https://www.sec.gov/newsroom/press-releases/2013-222] "requires Knight Capital to pay a $12 million penalty"; "eventually suffered a loss of more than $460 million"; "During the first 45 minutes after the market opened on August 1".
- Derived: 45 minutes = 2,700 s. $460,000,000 / 2,700 s = 170,370 dollars per second (truncated).
- Derived: 7 of 8 servers had the correct code = 87.5%. The eighth had the reused flag and the old Power Peg code.
- Deployment start: July 27, 2012 (paragraph 15). Incident: August 1, 2012 (paragraph 16).

### 8b. Google Cloud, 12 June 2025 (Service Control)

Source: [doc: https://status.cloud.google.com/incidents/ow5i3PPK96RduMcb1SsW] Times are US/Pacific as the page states.

- Trigger, verbatim: "On May 29, 2025, a new feature was added to Service Control for additional quota policy checks. This code change and binary release went through our region by region rollout, but the code path that failed was never exercised during this rollout due to needing a policy change that would trigger the code."
- Flag status, verbatim: "The issue with this change was that it did not have appropriate error handling nor was it feature flag protected." "If this had been flagged protected, the issue would have been caught in staging." The code had a red-button kill switch for the policy serving path, per the page.
- Propagation, verbatim: "this metadata was replicated globally within seconds."
- Timeline in the post: narrative "On June 12, 2025 at ~10:45am PDT, a policy change was inserted into the regional Spanner tables". Summary table: "Incident Start: 12 June, 2025 10:49", "All regions except us-central1 mitigated: 12 June, 2025 12:48", "Incident End: 12 June, 2025 13:49", "Duration: 3 hours".
- Recovery: "we bypassed the offending quota check, which allowed recovery in most regions within 2 hours."
- Derived: 10:49 to 13:49 = 180 minutes = 3 hours (matches the Duration row).

### 8c. Cloudflare, 18 November 2025 (Bot Management feature file)

Source: [doc: https://blog.cloudflare.com/18-november-2025-outage/] Times are UTC, as the post states.

- Start: "On 18 November 2025 at 11:20 UTC (all times in this blog are UTC), Cloudflare's network began experiencing significant failures to deliver core network traffic."
- Trigger, verbatim: "a change to one of our database systems' permissions which caused the database to output multiple entries into a 'feature file' used by our Bot Management system. That feature file, in turn, doubled in size."
- Permission change time in the post: "we made a change at 11:05 to make this access explicit" (ClickHouse metadata access). The post presents this as the change that exposed the duplicate output. Derived: 11:05 to 11:20 = 15 minutes.
- Limit, verbatim: "Currently that limit is set to 200, well above our current use of ~60 features." And: "the limit exists because for performance reasons we preallocate memory for the features."
- Panic: "When the bad file with more than 200 features was propagated to our servers, this limit was hit ... resulting in the system panicking."
- Fix time: "Errors continued until the underlying issue was identified and resolved starting at 14:30." And "Core traffic was largely flowing as normal by 14:30." "As of 17:06 all systems at Cloudflare were functioning as normal."
- Derived: 11:20 to 14:30 = 190 minutes (3 h 10 min). 11:20 to 13:05 = 105 minutes.
- Derived: the limit of 200 is about 3.33 times the ~60 features in use (200 / 60 = 3.33).

---

## 9. Experimentation basics that touch flags

### 9a. Sample ratio mismatch (SRM)

Source: [doc: https://exp-platform.com/Documents/2019_KDDFabijanGupchupFuptaOmhoverVermeerDmitriev.pdf] (Fabijan et al., KDD 2019; text extracted with pdftotext).

- Definition, verbatim: "deviations from the configured split were highly statistically significant so unlikely to happen just due to chance. This difference is commonly known as a Sample Ratio Mismatch (SRM)".
- Prevalence at Microsoft, verbatim: "approximately 6% of experiments at Microsoft exhibit an SRM."
- Prevalence at LinkedIn, verbatim: "about 10% of triggered analysis at LinkedIn have an SRM."
- Logging step: the paper lists the flow with the variant applied and "its usage is being logged." [doc: same PDF, section 2.2]

### 9b. Exposure logging: assignment vs exposure

- Rule for the note: log exposure when the flag is evaluated and the variant is returned to the caller, not when the flag is created or assigned. The Fabijan paper ties SRM to "the variant is applied, and its usage is being logged" (section 2.2). [doc: same PDF]

### 9c. Kohavi and the textbook

- Kohavi, Tang, Xu, "Trustworthy Online Controlled Experiments" (Cambridge University Press, 2020). Chapter 1 PDF URL: https://experimentguide.com/wp-content/uploads/TrustworthyOnlineControlledExperiments_PracticalGuideToABTesting_Chapter1.pdf. [unverified] found by WebSearch only, not opened. Chapter 21 on SRM is cited in the search summary. [unverified]

---

## Numbers worth quoting

- 30 s (polling default and minimum, `DefaultPollInterval = 30 * time.Second`), 1 s (streaming initial reconnect delay), 5 min (extended initial poll delay). https://raw.githubusercontent.com/launchdarkly/go-server-sdk/v7/ldcomponents/polling_data_source_builder.go ; https://raw.githubusercontent.com/launchdarkly/go-server-sdk/v7/ldcomponents/streaming_data_source_builder.go ; https://raw.githubusercontent.com/launchdarkly/go-server-sdk/v7/internal/datasource/polling_data_source.go
- 15 hex characters (60 bits), LaunchDarkly bucket hash prefix; divisor 1152921504606846975 (2^60 - 1). https://raw.githubusercontent.com/launchdarkly/go-server-sdk-evaluation/v3/evaluator_bucketing.go
- 100,000, LaunchDarkly weight total (100% = 100,000 units; 1 unit = 0.001%). https://launchdarkly.com/docs/sdk/concepts/flag-evaluation-rules
- 15000 ms (Unleash `refreshInterval` default), 60000 ms (`metricsInterval` default). https://raw.githubusercontent.com/Unleash/unleash-client-node/main/src/repository/index.ts ; https://docs.getunleash.io/reference/sdks/node
- 10, Unleash maximum failure count used in backoff (`Math.min(this.failures + 1, 10)`). https://raw.githubusercontent.com/Unleash/unleash-client-node/main/src/repository/polling-fetcher.ts
- 165 s, Unleash maximum poll delay under backoff (15 s x 11). Arithmetic on the two rows above.
- 1..100, Unleash stickiness bucket range (`(hash % 100) + 1`). https://raw.githubusercontent.com/Unleash/unleash-client-node/main/src/strategy/util.ts
- 1000 (Statsig `USER_BUCKET_COUNT`, https://raw.githubusercontent.com/statsig-io/node-js-server-sdk/main/src/Evaluator.ts); 10000 (GrowthBook v2 bucket count, 0.01% steps) and 1000 (v1, 0.1%), https://raw.githubusercontent.com/growthbook/growthbook/main/packages/sdk-js/src/util.ts
- 2^32 = 4294967296, flagd fractional hash space. https://raw.githubusercontent.com/open-feature/flagd/main/core/pkg/evaluator/fractional.go
- 8, OpenFeature error codes; 8, OpenFeature resolution reasons. https://raw.githubusercontent.com/open-feature/spec/main/specification/types.md
- 14.5 s, Meta config propagation end to end (5 + 5 + 4.5). Paper PDF at https://research.facebook.com/file/877841159827226/holistic-configuration-management-at-facebook.pdf
- "less than four minutes", Meta PackageVessel large config delivery. Same PDF.
- 42% / 36% / 22%, Meta config issue types (common, subtle, valid-config-exposes-code-bug). Same PDF, section 6.4. Share of config issues, not incidents.
- 350K active properties; 150K changes per week; 700 services; 50K+ hosts; around 3 million QPS. Uber Flipr, https://www.uber.com/us/en/blog/flipr/
- 21,428 changes per day (150K / 7, truncated). Arithmetic on the Flipr row.
- 60 QPS per host, upper bound (3,000,000 / 50,000). Arithmetic on the Flipr row.
- 20% linear growth over a 10 hour deployment, 0/20/40/60/80/100%. https://docs.aws.amazon.com/appconfig/latest/userguide/appconfig-creating-deployment-strategy.html
- 45 minutes, Knight Capital incident window; $460 million loss; 212 parent orders; 4 million executions in 154 stocks; 397 million shares; 1 of 8 servers missed the change. SEC order https://www.sec.gov/litigation/admin/2013/34-70694.pdf (paragraphs 15 to 17). $12 million penalty: https://www.sec.gov/newsroom/press-releases/2013-222
- 170,370 dollars per second (460,000,000 / 2,700 s, truncated). Arithmetic on the Knight row.
- 10:49 to 13:49 PDT, Google Cloud incident, 3 hours. https://status.cloud.google.com/incidents/ow5i3PPK96RduMcb1SsW
- 11:20 UTC, Cloudflare failure start; 14:30 UTC, fix starts; 13:05 UTC, Access rollback. https://blog.cloudflare.com/18-november-2025-outage/
- ~6%, experiments at Microsoft with an SRM; ~10%, triggered analyses at LinkedIn with an SRM. https://exp-platform.com/Documents/2019_KDDFabijanGupchupFuptaOmhoverVermeerDmitriev.pdf

---

## Conflicts and corrections

1. Google Cloud incident start time disagrees across the same post. Narrative: "~10:45am PDT". Summary table: "Incident Start: 12 June, 2025 10:49". Status banner: "began at 2025-06-12 10:51". Sources: https://status.cloud.google.com/incidents/ow5i3PPK96RduMcb1SsW . Use one and say which.
2. Google Cloud end time also disagrees by scope. Table: "Incident End: 12 June, 2025 13:49". Banner: "ended at 2025-06-12 18:18" for a list of products. Derived for the banner: 10:51 to 18:18 = 447 minutes. The two are different scopes, not a contradiction, but quote both with labels.
3. Stripe: a search summary said "Feature Deployments runs the company's feature flag system." The fetched careers page says only that the team works "with Feature Deployments on change-safety tooling (feature flags, configuration management, change audit logs)". The page does not say ownership. Correction: do not claim Stripe ownership from this listing. https://stripe.com/careers/listing/staff-engineer-release-engineering/8038771
4. LaunchDarkly bucketing: docs describe exact integer division by 0xFFFFFFFFFFFFFFF. Go code divides as float32. Code wins; note the float32 precision in the note if you cite the bucket value.
5. Statsig hashing: the prompt guessed SHA-256. Code default for named hashes is djb2 (`options?.hash ?? 'djb2'`), with SHA-256 optional. The bucket hash (`computeUserHash`) is not verified. https://raw.githubusercontent.com/statsig-io/node-js-server-sdk/main/src/Evaluator.ts
6. Unleash fallback: docs say unsynced flags are `false` unless bootstrapped. Node code also has a file backup via a storage provider read path. The docs text does not describe the order in which backup and bootstrap are used, so use the code order (bootstrap in `readBootstrap`, then storage provider backup read) for the note. [code: https://raw.githubusercontent.com/Unleash/unleash-client-node/main/src/repository/index.ts]
7. "Share of incidents caused by config changes" (prompt question 6): not in the Meta paper. The 42/36/22 figures are shares of config issues (section 6.4). The paper says configuration errors are "a major source of site outages" without a percentage.
8. Cloudflare trigger: the post describes a permission change at 11:05 UTC and the failure at 11:20 UTC. The post does not say the 11:05 change directly caused the feature file; it says the permission change "caused the database to output multiple entries". Quote as the post does.

## Gaps (not verified, do not quote)

- Amazon Weblab internals, Slack experimentation and flag system, Stripe flag system: no primary source found.
- LaunchDarkly: stream-drop behaviour, init-timeout default, client-side evaluation location, daemon-mode store names, published scale numbers.
- AppConfig: predefined strategies, custom-strategy default bake time, feature flag size limit, agent poll interval.
- GrowthBook default `hashVersion`; Statsig `computeUserHash` definition; Unleash `STICKINESS.default` and Edge numbers.
- Meta: integer daily change count; share of incidents caused by config changes. Kohavi book chapter text (search only).

## Sources table

| id | URL | Supports | Status |
|---|---|---|---|
| S1 | https://raw.githubusercontent.com/launchdarkly/go-server-sdk-evaluation/v3/evaluator_bucketing.go | LD bucketing hash, prefix, divisor, float32 | code, opened |
| S2 | https://launchdarkly.com/docs/sdk/concepts/flag-evaluation-rules | LD bucketing text, weights 0 to 100,000, evaluation order | webfetch-summary |
| S3 | https://raw.githubusercontent.com/launchdarkly/go-server-sdk/v7/ldcomponents/polling_data_source_builder.go | LD 30 s poll default and minimum | code, opened |
| S4 | https://raw.githubusercontent.com/launchdarkly/go-server-sdk/v7/ldcomponents/streaming_data_source_builder.go | LD 1 s reconnect default | code, opened |
| S5 | https://raw.githubusercontent.com/launchdarkly/go-server-sdk/v7/internal/datasource/polling_data_source.go | LD 5 min extended poll delay | code, opened |
| S6 | https://raw.githubusercontent.com/launchdarkly/go-server-sdk/v7/internal/datasource/polling_strategy.go | LD poll backoff comments | code, opened |
| S7 | https://raw.githubusercontent.com/launchdarkly/go-server-sdk/v7/ldclient.go | LD MakeClient waitFor, 60 s warning constant | code, opened |
| S8 | https://docs.launchdarkly.com/home/relay-proxy | Relay Proxy purpose and scope | doc, opened |
| S9 | https://raw.githubusercontent.com/Unleash/unleash-client-node/main/src/repository/index.ts | Unleash refreshInterval 15_000, bootstrapOverride default | code, opened |
| S10 | https://raw.githubusercontent.com/Unleash/unleash-client-node/main/src/repository/polling-fetcher.ts | Unleash backoff, cap 10, recoverable codes | code, opened |
| S11 | https://raw.githubusercontent.com/Unleash/unleash-client-node/main/src/strategy/util.ts | Unleash murmurhash3 x86 hash32, seed 0, 1..100 | code, opened |
| S12 | https://raw.githubusercontent.com/Unleash/unleash-client-node/main/src/strategy/gradual-rollout-user-id.ts | Unleash userId-only rollout | code, opened |
| S13 | https://raw.githubusercontent.com/Unleash/unleash-client-node/main/src/strategy/flexible-rollout-strategy.ts | Unleash groupId defaults to flag name | code, opened |
| S14 | https://raw.githubusercontent.com/Unleash/unleash-client-node/main/src/repository/bootstrap-provider.ts | Unleash bootstrap url then file | code, opened |
| S15 | https://raw.githubusercontent.com/Unleash/unleash-client-node/main/src/repository/storage-provider-file.ts | Unleash backup file name, backupPath required | code, opened |
| S16 | https://docs.getunleash.io/reference/sdks/node | Unleash refreshInterval 15000ms, metricsInterval 60000ms, backup and false-until-sync | doc, opened (webfetch-summary) |
| S17 | https://docs.getunleash.io/unleash-edge | Unleash Edge purpose | webfetch-summary |
| S18 | https://raw.githubusercontent.com/growthbook/growthbook/main/packages/sdk-js/src/util.ts | GrowthBook FNV-1a v1 and v2 formulas | code, opened |
| S19 | https://docs.growthbook.io/lib/js | GrowthBook bucketingV2 from v0.23.0 | webfetch-summary |
| S20 | https://raw.githubusercontent.com/statsig-io/node-js-server-sdk/main/src/Evaluator.ts | Statsig USER_BUCKET_COUNT 1000, user_bucket salt input, djb2 default | code, opened |
| S21 | https://raw.githubusercontent.com/statsig-io/node-js-server-sdk/main/src/utils/Hashing.ts | Statsig hashString algorithms, djb2 and sha256 | code, opened |
| S22 | https://raw.githubusercontent.com/open-feature/flagd/main/core/pkg/evaluator/fractional.go | flagd murmur3, flagKey prefix, (hash*total)>>32 | code, opened |
| S23 | https://raw.githubusercontent.com/open-feature/spec/main/specification/sections/01-flag-evaluation.md | OpenFeature requirements 1.3.x, 1.4.x | doc, opened |
| S24 | https://raw.githubusercontent.com/open-feature/spec/main/specification/types.md | OpenFeature error codes (8), resolution reasons (8) | doc, opened |
| S25 | https://docs.aws.amazon.com/appconfig/latest/userguide/appconfig-creating-deployment-strategy.html | AppConfig linear and exponential, bake time, rollback on CloudWatch alarm | doc, opened via curl |
| S26 | https://research.facebook.com/file/877841159827226/holistic-configuration-management-at-facebook.pdf | Meta abstract, 5 s / 5 s / 4.5 s, 4 minutes, restraints, 42/36/22 | doc, PDF text, opened via redirect |
| S27 | https://www.uber.com/us/en/blog/flipr/ | Flipr 350K, 150K per week, 700 services, 50K+ hosts, 3 million QPS | doc, webfetch-summary |
| S28 | https://stripe.com/careers/listing/staff-engineer-release-engineering/8038771 | Stripe Feature Deployments collaboration text (correction) | doc, webfetch-summary |
| S29 | https://www.sec.gov/litigation/admin/2013/34-70694.pdf | Knight paragraphs 13 to 17, 45 minutes, $460 million, 1 of 8 servers | doc, PDF text, opened via saved copy |
| S30 | https://www.sec.gov/newsroom/press-releases/2013-222 | Knight $12 million penalty, more than $460 million | webfetch-summary |
| S31 | https://status.cloud.google.com/incidents/ow5i3PPK96RduMcb1SsW | Google Cloud 12 June 2025 timeline and trigger | doc, opened via curl |
| S32 | https://blog.cloudflare.com/18-november-2025-outage/ | Cloudflare 11:20 UTC, 200 limit, ~60 features, 14:30 and 13:05 times | doc, opened via curl |
| S33 | https://exp-platform.com/Documents/2019_KDDFabijanGupchupFuptaOmhoverVermeerDmitriev.pdf | SRM definition, 6% Microsoft, 10% LinkedIn, exposure logging | doc, PDF text, opened |

---

## Spot-check notes (editor, 2026-10-08)

Re-fetched by hand before using in `solution.md`. All matched the survey:

| Claim | Check | Result |
|---|---|---|
| LaunchDarkly bucketing: SHA-1, first 15 hex chars, `float32(0xFFFFFFFFFFFFFFF)` | `curl` S1, `grep -n` lines 4, 15, 99, 102 | Confirmed, including the float32 divisor |
| LaunchDarkly `DefaultPollInterval = 30 * time.Second` | `curl` S3, line 17 | Confirmed |
| Unleash `murmurHash3.x86.hash32(groupId:id, seed)`, `(hash % normalizer) + 1`, `STRATEGY_SEED = 0`, `refreshInterval = 15_000` | `curl` S11 lines 4, 5, 8 and S9 line 100 | Confirmed. Also seen: `VARIANT_SEED = 86028157` for variants |
| Cloudflare: limit 200 vs ~60 features, file "doubled in size", 11:20 UTC start, core traffic normal by 14:30, all systems 17:06 | `curl` S32 + tag strip | Confirmed |
| Google Cloud: "nor was it feature flag protected", "replicated globally within seconds", Incident Start 10:49 US/Pacific | `curl` S31 + tag strip | Confirmed. `solution.md` uses 10:49 PDT (the summary table) |
| Knight Capital: "repurposed a flag", 1 of 8 servers, 212 parent orders, ~45 minutes, "$460 million loss" | SEC order PDF via WebFetch, `pdftotext` | Confirmed (SEC blocks plain `curl` with an HTML page) |

Not used in `solution.md` because unverified: Weblab internals, Stripe's internal flag system, AppConfig predefined strategies and quotas, LaunchDarkly stream-drop behaviour.
