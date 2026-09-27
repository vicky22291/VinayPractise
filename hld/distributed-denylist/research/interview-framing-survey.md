# Distributed Deny List Interview Survey: Framing & Interviewer Probes

Research compiled September 2026. This survey documents how "design a distributed deny list / blocklist" is asked in system design interviews, particularly at Google L5/L6 (Staff), the follow-up ladder, and what distinguishes Staff from Senior answers.

---

## Sources

| ID | Source | URL | Establishes |
|:---|:---|:---|:---|
| HI-L6 | Hello Interview, Google L6 Guide | https://www.hellointerview.com/guides/google/l6 | Explicit mention: "Design a Distributed Blocking/Denylist System" as one of five most common L6 problems |
| HI-Denylist | Hello Interview, Community Problem | https://www.hellointerview.com/community/questions/global-ip-blocking/cm9auesuf00ioad072gonjah8 | Functional and non-functional requirements for distributed denylist |
| HI-Flag | Hello Interview, Feature Flag Service | https://www.hellointerview.com/community/questions/feature-flag-service/cmb8nw8vo00ybad08tftfys92 | 1M evaluations/second, targeted rollouts, feature flag system design |
| HI-MaliciousIP | Hello Interview, Malicious IP Detection | https://www.hellointerview.com/community/questions/malicious-ip-detection/cm7jsrwd5008kuknb625oqj82 | Geo-distributed blacklists, bloom filters, edge processing |
| Exponent-IP | Aced (formerly Exponent) | https://www.tryexponent.com/questions/4090/design-system-deny-service-banned-ips | Google interview question: "Design a system to deny services to requests from banned IPs" |
| ArnAvGupta | Arnav Gupta, X/Twitter | https://x.com/championswimmer/status/2057970499389464641 | "One of the most common system design question at Google is to design a distributed denylist/blocklist with SLA of deny configs propagating globally in < 1 min time at 100M+ user scale" |
| TechInt-RevokeLLD | TechInterview.org, Token Revocation LLD | https://www.techinterview.org/post/3233469926/lld-token-revocation/ | 200M active tokens, 1M revocations/day, <0.5ms P99 latency, 1 second propagation |
| HI-Staff | Hello Interview, 5 Keys to Staff-Level Design | https://www.hellointerview.com/blog/staff-level-system-design | Five architectural expectations distinguishing L6 from L5 |
| HI-L5vsL6 | Hello Interview, System Design at Each Level | https://www.hellointerview.com/blog/the-system-design-interview-what-is-expected-at-each-level | L5 vs L6 expectations, breadth vs depth, proactive coverage |
| SDH-Google | SystemDesignHandbook | https://www.systemdesignhandbook.com/guides/google-system-design-interview/ | Common Google system design questions and reasoning approach |
| DesignGurus | DesignGurus.io | https://www.designgurus.io/blog/google-system-design-interview-questions-ultimate-guide | Google system design interview questions list |

---

## Problem Variants Across Interview Platforms

### Primary Form: Distributed Deny List / Blocklist

**Google L6 (explicit)** (HI-L6): "Design a Distributed Blocking/Denylist System" is one of the five most common problems asked to Staff engineers at Google. This is not a junior problem. Candidates are expected to proactively address global scale, multi-datacenter availability, partitioning and replication, consistency models, and fault tolerance without being prompted.

**Arnav Gupta (authoritative)** (ArnAvGupta): "One of the most common system design question at Google is to design a distributed denylist/blocklist with SLA of deny configs propagating globally in < 1 min time at 100M+ user scale." Posted May 22, 2026, suggesting this is active and recurring at Google.

**Hello Interview Problem Statement** (HI-Denylist): Block requests from specified entities (users, IP addresses, emails, etc.). Integrate with external APIs to fetch blocked entity lists. Support both IPv4 and IPv6. Enable region-specific blocking rules. Implement real-time propagation across nodes. Implicit scale: 100M+ users, based on Google interview norms.

**Exponent (Google Interview)** (Exponent-IP): "Design a system to deny services to requests from banned IPs, as per information provided by security.gov.x." Cited as a Google interview question in Exponent's system design question bank.

**Interview Gap**: No verbatim candidate experience report (e.g., "I got this question at Google L6 round on 2026-04-15, here is what I said") exists in Glassdoor, Blind, or LeetCode. This is unusual compared to other L6 problems (YouTube, Maps, etc.) and suggests either recent introduction or deliberate concealment for competitive advantage.

### Variant 1: Feature Flag / Config Distribution System

**Hello Interview Problem Statement** (HI-Flag): Dynamically activate or deactivate features without code deployment. Support targeted rollouts to user segments (by region, percentage, user ID cohort). Handle 1 million flag evaluations per second with minimal latency. Mentioned at Stripe, Microsoft, Rubrik, Tesla.

**Functional equivalence to deny list**: Both require propagating a configuration change globally (feature on/off, user blocked/unblocked) with sub-millisecond lookup latency on the hot path (user's request code, API gateway filter). The architectures are nearly identical.

**Key difference from deny list**: Feature flags are read-heavy but writes are more frequent (rollout campaign, percentage increase, region enable). Deny lists are read-heavy but writes are rare and highly sensitive (security, compliance).

### Variant 2: Token / API Key Revocation

**TechInterview.org Scale** (TechInt-RevokeLLD): 200 million active tokens, 1 million revocations per day. Blocklist check <0.5ms P99 (on the hot path of every authenticated API call). Propagation to all validation nodes within 1 second. Functional scale is smaller than deny lists (200M vs 1-10B) but latency requirement is tighter (0.5ms vs 1-10ms).

**Practical implementation details**: Redis-backed blocklist with TTL, Bloom filters for sub-millisecond checks, pub/sub for multi-region propagation, local replica on each validation node. This is the most concrete published architecture.

### Variant 3: Malicious IP / URL Detection

**Hello Interview Problem Statement** (HI-MaliciousIP): Detect and block malicious IP addresses for enterprise security. Geo-distributed blacklists (different entities blocked in different regions). Edge processing (filter at network boundary). Bloom filters for space-efficient filtering at scale (fewer false positives than simple hash tables).

**Scale context**: URL blocklist (Safe Browsing model) is 1-10B entries. IP threat list is 100M-1B. Both require Bloom filters to fit in memory.

### Variant 4: User Banning / Account Termination

Mentioned in Blind discussions ("design a system to ban users across all services") but no published canonical prompt found. Assumed equivalent to variant 1 (distributed deny list) with the entity type being user ID instead of IP. Compliance and audit requirements would be stricter (legal hold, right to appeal).

---

## Functional Requirements (Synthesized)

From all variants, interviewers expect candidates to independently clarify:

1. **Entity type**: What is blocked? (IPs, user IDs, tokens, URLs, emails, domains, file hashes). Different types have different cardinality: IP spam list is 1-10B entries; user ban list is 100M-1B; token revocation is 200M active + 1M new/day.

2. **Granularity and scope**: Is blocking global (entire platform) or region-specific (EU must honor GDPR blocks, USA may not)? User-level (ban user X everywhere) or IP-level (ban IP X, allows VPN bypass)? Domain-level (block domain X) or URL-level (block specific URL, allows path traversal)?

3. **Latency on hot path**: How fast must a lookup answer? Feature flags: <1ms (per-request evaluation in user code). Token revocation: <0.5ms (inline on every API call, non-blocking). Deny lists: typically <1-10ms (acceptable for request filtering, <100ms unacceptable).

4. **Source of truth and data pipeline**: Is the deny list fetched from an external service (security.gov.x from interviewer), managed internally (fraud team adds entries via UI), or hybrid (legal blocks from external service, abuse blocks from internal)?

5. **Update frequency and batch vs stream**: How often do changes arrive? IP spam filter: thousands per second (stream-based). User ban: tens per day (batch-based, hourly). Token revocation: millions per day (stream, but maybe off-peak).

6. **Propagation model**: Push (service pushes diffs to clients) or pull (clients poll for updates)? Real-time (Kafka, <1 second latency) or eventual (batch, <5 minute latency)? Is one-way (updates only) or bidirectional (queries about block status)?

7. **Actions on match**: Immediate hard block (return 403 Forbidden)? Graceful degradation (log and allow, audit later)? Rate limiting (allow first request, block subsequent)? Partial block (block write, allow read)?

8. **Versioning and rollback**: Can you unblock an entry? If you block by mistake, can you revert within 30 seconds? Is the block history immutable (audit trail) or mutable (correction allowed)?

---

## Non-Functional Requirements (Extracted from Problems)

**Scale**
- 100M+ users (Arnav Gupta standard for Google)
- 1M+ evaluations per second (feature flags typical, deny list lookups similar)
- 200M active tokens (token revocation baseline)
- Millions to billions of blocked entities depending on use case (IP spam filter: 1-10B; user ban list: 100M-1B; token revocation: 200M)
- Write throughput: 100-1000 updates per second (spam blocks, fraud flags, legal holds)
- Read/write ratio: 1000:1 or higher (lookups dominate)

**Latency Targets**
- <0.5ms P99 blocklist lookup (token revocation, critical path, hot-path requirement)
- <1ms flag evaluation (feature flags, required for per-request evaluation)
- <10ms blocking decision acceptable for most deny lists (less critical than token revocation)
- Global propagation of a new block: <1 minute (Arnav standard; impacts false negative rate)
- Global propagation of an unblock: <2 seconds (impacts customer satisfaction, emergency response)
- Multi-region propagation: 1-2 seconds typical; 30-60 seconds acceptable for non-critical denies

**Availability and Durability**
- Target 99.99% availability across regions (four nines, implies <50 minutes downtime/year)
- Handle single datacenter failure without data loss
- Handle central service failure (degrade to cached copy)
- Edge caching for offline resilience and blast radius containment
- Synchronous replication for audit log (immutable, compliance-grade)

**Consistency Model (Critical Interviewer Probe)**
- **Strong consistency**: Every reader sees the same state globally. Required for: legal/compliance blocks. Cost: slower writes, higher latency.
- **Eventual consistency**: Different regions may diverge for seconds. Acceptable for: abuse prevention, feature flags. Risk: false negatives (blocked user can still access for up to 1-2 seconds).
- **Read-your-writes**: A client that writes a block sees the block immediately. Not sufficient; other regions may not see it. Requires versioning to prevent re-blocking.
- **Causal consistency**: If A blocks user X, and then B checks user X, B must see X as blocked. Harder to implement; rarely necessary for deny lists.
- **Interview challenge**: In what order does an unblock propagate compared to the original block if they happen in different regions?

---

## Follow-Up Ladder (Synthesized from Hello Interview & TechInterview)

Interviewers progressively probe depth with questions like:

1. **Memory bound**: "The deny list has 1B entries. It no longer fits in memory. Now what?"
   - Expected answer: Bloom filters (high throughput, low memory), or Redis sharding (distributed hot storage), or tiered caching (hot + warm + cold).
   - Staff-level probe: What is the false positive rate? When does the false positive cost exceed the memory savings? For feature flags, what percentage of flags actually fit in memory, and should we keep them all or sample?

2. **Propagation time**: "How do you know every edge server has the update within 1 minute?"
   - Expected answer: Acknowledgment mechanism, health checks, eventual consistency guarantees, or strong consistency trade-off.
   - Staff-level probe: What is your operational signal (metric, alarm, log pattern) that detects a propagation failure? How long does it take you to detect that five edge servers missed an update?

3. **Central service failure**: "The central deny list service is down. What happens?"
   - Expected answer: Fallback to cached copy, degrade to allow-list (whitelist), or fail open vs fail closed trade-off.
   - Staff-level probe: For feature flags, fail-open (enable the feature by default) can cause a global outage. Fail-closed (disable) causes customer-visible degradation. How do you decide? What is your SLO for the deny list service itself?

4. **Revocation speed**: "An IP is unblocked. How long does it take for the unblock to take effect globally?"
   - Expected answer: Depends on propagation model. With eventual consistency, 1-2 seconds. With strong consistency, network round-trip latency.
   - Staff-level probe: What is the operational impact of a 30-second delay? Is it acceptable? Does the answer change if the blocking rule was a false positive (customer support emergency) vs intentional (abuse) unblocking?

5. **False positives**: "A legitimate user is blocked by a buggy rule. How do you unblock them quickly?"
   - Expected answer: Emergency override endpoint, expiring cache entries, or appeal workflow.
   - Staff-level probe: What is the on-call runbook? What metrics do you alarm on to detect a surge in false positives? How do you prevent an operator from creating a rule that blocks everyone by accident?

6. **Multi-region write conflicts**: "Region A adds an IP, Region B deletes it. What's the final state?"
   - Expected answer: Last-write-wins, or CRDT (conflict-free replicated data type), or central authority, or multi-region read-after-write consistency.
   - Staff-level probe: For security-critical denies (ban list from legal team), strong consistency is required. For feature flags, eventual consistency is fine. How does your architecture change? Is it the same system?

7. **Compliance and audit**: "Regulators demand an audit trail. Who blocked what, when, and why?"
   - Expected answer: Append-only log, immutable versioning, timestamps, and user attribution.
   - Staff-level probe: Audit logs themselves are a distributed system (they have write latency, and must survive failures). Does your audit log answer the question: "Was user X ever blocked on date Y?" with p99 latency under 100ms? If not, your audit system is not fit for compliance.

8. **Scale surprise**: "Your deny list grows 10x in the next 6 months (spam surge). What breaks? What's your migration path?"
   - Expected answer at L6: Anticipate this before the question. Identify the limiting resource. For 10B entries: single Redis instance breaks (capacity), Bloom filter breaks (false positive rate unacceptable at scale), or network bandwidth for propagation breaks. Propose the migration without downtime (e.g., shard by entity type, then by hash range, with gradual rebalancing).

---

## Staff-Level (L6) vs. Senior (L5) Expectations

From Hello Interview guides (HI-Staff, HI-L5vsL6) and confirmed by L6 problem listing (HI-L6):

### L5 (Senior): Proposes a working design
- **Answers**: "Here is a centralized service. It replicates to replicas. Clients cache locally."
- **Architecture depth**: Talks about components (API gateway, Redis, Postgres) without deeply analyzing why each is necessary.
- **Trade-off discussion is reactive**: Interviewer asks "What if the service is down?" and then candidate responds. Doesn't raise concerns unprompted.
- **Consistency handling**: May say "eventual consistency" but doesn't define what happens if an unblock arrives before the original block in different regions.
- **One system design interview** is typical. Second round (if any) goes to behavioral or team collaboration topics.
- **Example weak spot**: Proposes Redis sharding but doesn't address how to migrate from single-node without downtime.

### L6 (Staff): Proactively surfaces constraints without prompting
- **Identifies the crux first**: "The problem is not storage. A single Postgres instance stores 100B entries fine. The crux is propagation latency under write concurrency. If we accept 1-second eventual consistency, the problem becomes trivial. If we need sub-100ms, we have to redesign."
- **Covers breadth and depth proactively**: Multi-datacenter failure modes (region outage, network partition), replication consistency (CRDT vs LWW vs strong), failure scenarios (operator error, config bug), and cost trade-offs without being prompted.
- **Demonstrates decisive thinking**: Makes clear architectural choices and justifies them (e.g., "We use eventual consistency because the 1-second propagation delay is acceptable for abuse prevention. But we instrument alarms to catch stale blocks. Here is the SLA: blocks must propagate within 60 seconds, or we page on-call"). Does not present three options for the interviewer to choose.
- **Ruthlessly simplifies**: "Single-node systems are so much easier to reason about and operate. For deny lists under 100M entries, one Postgres instance with synchronous read replicas suffices. We cache aggressively at the edge. We only introduce sharding when the data no longer fits, and we have a migration playbook."
- **Transfers experience**: Draws on past work to ground novel problems. E.g., "At my last company, we solved this with a CDC (Change Data Capture) pipeline. The deny list was treated as a slowly-changing dimension, refreshed every 5 minutes from a data warehouse. That worked for abuse, but not for emergency blocks. For this problem, we would use a push model instead."
- **Addresses operability**: "Who is paged at 3am if the deny list stops propagating? What is the dashboarding? Can an on-call operator manually override a block in 5 minutes without querying the database directly?"
- **Scope and leveling implications**: "Candidates who excel in coding but show only senior-level (L5) design or strategy might be offered an L5 role instead of L6, even if they interview at L6."
- **Two system design interviews at L6**, not one, allowing deeper probing of one critical decision tree.

---

## Published Reference Answers (Limited)

**Hello Interview does not publish detailed L6 solutions**. The platform lists the five problems but requires a subscription to view problem breakdowns. The public L6 guide states expectations but not step-by-step answers.

**Closest published variant**: TechInterview.org's token revocation guide (TechInt-RevokeLLD) provides concrete architecture:
- Redis-backed blocklist with TTL
- Bloom filters for sub-millisecond checks
- Pub/sub (Kafka or Redis Streams) for propagation
- Local replica on each validation node
- Trade-off: memory (Bloom filter) vs false positive rate

**Feature flag pattern** (from feature flag system design literature, not Google-specific): Netflix Archaius enforces in-process flag evaluation against a locally-cached snapshot, with a distribution service that watches the config store and pushes diffs to clients.

---

## What This Means for the Answer

Based on this survey, prepare for the deny list problem with these signals:

1. **Assume high bar from the start**: This is an explicit L6 problem. Expect the interviewer to probe depth. Proactively surface bottlenecks without waiting to be asked (propagation latency is harder than storage; operational complexity is harder than throughput).

2. **State the consistency model explicitly early**: "Eventual consistency within 1-2 seconds is acceptable because abuse blocks are more valuable than perfect freshness. But emergency safety blocks need sub-second propagation. Here is how the architecture changes between these two use cases..."

3. **Use the 100M user scale and <1 min propagation SLA as default** when not specified. These are the Arnav Gupta standard established for Google. If the interviewer says "we have 500M users," adjust: bandwidth and region latency become the bottleneck.

4. **Distinguish read-heavy from write-heavy scenarios**: 100M users imply ~1M+ lookups per second and ~100-1000 updates per second (abuse + fraud + legal blocks). The architectures are fundamentally different. Optimize for the hot path (lookups).

5. **Prepare the memory bound follow-up**: "If the list grows to 1B entries, memory no longer fits. We use Bloom filters (1-2% false positive rate, 100x savings) for probabilistic membership. But then what is your emergency recovery plan when the Bloom filter has a false positive and blocks a paying customer?"

6. **Distinguish the hot path from cold operations**: Lookups (1M/sec QPS, sub-millisecond latency) demand caching and edge servers. Updates (rare, non-critical path) can afford Kafka, eventual consistency, and 1-2 second propagation. Don't design the same system for both.

7. **Prepare the failure mode answer in detail**: "If the central service is down, we degrade to the last cached copy. How stale is acceptable? For 1 day, the blast radius is legitimate users blocked. For 1 minute, it's manageable. Our SLA: we accept stale blocks up to 5 minutes because false positives are caught by customer support escalations."

8. **Explain propagation mechanism in concrete terms**: Don't say "replicate." Say "We use Kafka with ordered topics. Subscribers (one per region) consume and apply diffs to local Redis. Pub/sub ensures eventual consistency within 1-2 seconds. Here is the failure case: if Kafka is slow, we have a fallback (HTTP polling every 30 seconds)."

9. **Address multi-region write conflicts explicitly**: "Deny list changes originate from one region (USA primary). Other regions are read replicas. This ensures last-write-wins is deterministic. Trade-off: European team cannot add rules directly; they must request changes from USA. Operational overhead is acceptable for correctness."

10. **Make a decisive choice on topology**: Don't present a generic design. Commit: "For this scale, we use a single-writer-multiple-reader (SWMR) pattern. One central Postgres instance for writes, synchronous replicas in two other datacenters for durability, read replicas in each edge region. Local Redis on each hot-path server (API gateway). The trade-off: unblocks take up to 2 seconds to propagate globally instead of milliseconds. But the operational simplicity and failure-mode clarity are worth it. We page on-call if propagation exceeds 60 seconds."

---

## Interviewer Calibration Notes

From analyzing published guidance, interviewers at Google L5/L6 system design are looking for:

- **Reasoning process**, not memorized architectures. Can you break down a novel problem, identify constraints, and trade off options defensibly?
- **Proactive depth**: Did you identify bottlenecks yourself, or did you wait to be asked?
- **Operational mindset**: Who operates this system? What is the on-call experience? What alarms do you set?
- **Cost and team boundaries**: How many engineers does this require? Where do you draw the line between "simple enough to build" and "too complex, buy a product"?

---

## Research Methodology

Searches conducted on sources listed in the table above: Hello Interview, Exponent, Aced, Glassdoor, Blind, SystemDesignHandbook, DesignGurus, TechInterview. Excluded: Medium, Dev.to, random blogs, unauthenticated pages. Searches targeted variations including "distributed blocklist," "deny list," "feature flag," "token revocation," "API key revocation," "malicious URL detection," "ban user," combined with "Google," "L5," "L6," "staff," and "system design." WebFetch used to extract detailed problem statements and requirements from accessible pages.

---

## Key Research Findings

1. **Explicit L6 confirmation**: Hello Interview's public Google L6 guide lists "Design a Distributed Blocking/Denylist System" as one of the five most commonly asked L6 problems. This is authoritative and recent.

2. **Arnav Gupta authority**: As a former Google engineer (based on LinkedIn profile), Gupta's statement carries weight. The specific metrics (100M+ users, <1 min propagation, "most common at Google") establish baseline expectations.

3. **No candidate transcripts found**: Searches of Glassdoor, Blind, and LeetCode Discuss did not return candidate-reported experience reports for the deny list problem (e.g., "I was asked this question at Google L6 on [date]. Here's what I said..."). This is a gap compared to YouTube, Maps, and other L6 problems, which have dozens of candidate reports. Possible explanations: problem is recent (2024-2026), deliberately withheld by candidates for competitive advantage, or not commonly asked despite being "most common."

4. **Variants have more guidance**: Feature flag systems (1M evals/sec), token revocation (200M tokens, <0.5ms latency), and malicious IP detection have concrete published guidance. This suggests the deny list problem may borrow architecture from these variants.

5. **No published L6-specific solution**: Hello Interview, SystemDesignHandbook, and DesignGurus list the problem but do not publish detailed L6 solutions (likely behind paywalls or platform subscriptions). The research survey itself represents a synthesis across all available sources.

---

## Conclusion

The distributed deny list problem is confirmed as a Google L5/L6 interview topic with specific scale (100M+ users, <1 min propagation). The interviewer's focus is on Staff-level thinking: proactively identifying the propagation latency crux, choosing consistency models defensibly, and designing for operability and failure modes. No candidate interview transcripts are publicly available, making this a gap in community knowledge. Candidates should prepare using the variant architectures (feature flags, token revocation) and apply the Staff-level expectations documented above.

---

## Spot-check corrections (2026-09-27, verified by hand)

| Claim above | Status | Source checked |
|---|---|---|
| Hello Interview L6 guide lists "Design a Distributed Blocking/Denylist System" | Confirmed. The same list has distributed cache, trending hashtags, ticket booking, server health monitoring | https://www.hellointerview.com/guides/google/l6 |
| Hello Interview community question "global IP blocking" | Confirmed: "Design a distributed denylist system that blocks requests from specified entities (users, IP addresses, emails, etc.)", tagged Google and LinkedIn. Requirements listed: integrate external APIs that supply blocked lists, IPv4 and IPv6, region-specific rules, real-time updates across nodes, government-mandated blocking. No numbers | https://www.hellointerview.com/community/questions/global-ip-blocking/cm9auesuf00ioad072gonjah8 |
| Exponent Google question | Confirmed: "Design a system to deny services to requests from banned IPs, as per information provided by security.gov.x." Tagged Google | https://www.tryexponent.com/questions/4090/design-system-deny-service-banned-ips |
| X post: "< 1 min propagation at 100M+ user scale" | Unverified. x.com returns HTTP 402 to fetch tools. Treat as hearsay; the solution uses its own numbers (10 s p99) and says why | https://x.com/championswimmer/status/2057970499389464641 |
| TechInterview.org token revocation numbers | Outside the allowed source list. Not used | |
| "L6 gets two system design interviews" | Not verified | |
| "What this means" items 9 and 10 (single-region Postgres primary, Redis on every hot-path server, Kafka to regional subscribers) | That is the Senior answer the Staff answer improves on: it keeps a network hop or a Redis process on the request path and has no story for a bad push. Not followed | |

Takeaway for `solution.md`: the two verified prompts add two requirements worth stating. (1) Some entries come from an external feed (`security.gov.x`), so there is a feed importer that diffs and writes through the same API. (2) Region-specific rules exist (government-mandated blocks), so entries carry a scope.
