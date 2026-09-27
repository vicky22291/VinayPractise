# Distributed Deny List Systems in Production

A research survey on how production systems distribute configuration and blocklists to very large enforcement fleets. These patterns appear across security (Safe Browsing, revocation), networking (DNS blocklists, WAF IP sets), and operational configuration (Meta Configerator, Cloudflare Quicksilver, Netflix Hollow, AWS constant-work patterns, Envoy xDS).

Each system makes trade-offs between: consistency (strong vs. eventual), latency (seconds vs. minutes), size (bandwidth), complexity (push vs. pull vs. hybrid), and failure modes (fail-open vs. fail-static vs. circuit breaker). No single pattern dominates; the choice depends on whether stale data is acceptable, how many consumers exist, and how fast changes must propagate.

This survey reviews what gets distributed, how large it is, how many endpoints consume it, whether data flows push or pull, how incremental vs. snapshot updates work, propagation latency, local lookup performance, failure-mode handling, and documented incidents. Numbers are cited directly from sources.

## Sources

| ID | URL | Establishes |
|---|---|---|
| SB-v4 | https://developers.google.com/safe-browsing/v4/update-api | Safe Browsing v4 hash prefix sizes, compression |
| SB-v4-freq | https://developers.google.com/safe-browsing/v4/request-frequency | minimumWaitDuration semantics |
| CRL-Moz-2025 | https://hacks.mozilla.org/2025/08/crlite-fast-private-and-comprehensive-certificate-revocation-checking-in-firefox/ | CRLite total size, daily delta, snapshot interval |
| CRL-blog | https://blog.mozilla.org/security/2020/01/09/crlite-part-1-all-web-pki-revocations-compressed/ | CRLite design rationale |
| CRL-clubcards | https://research.mozilla.org/files/2025/04/clubcards_for_the_webpki.pdf | Clubcard filter sizes |
| QS-2020 | https://blog.cloudflare.com/introducing-quicksilver-configuration-distribution-at-internet-scale/ | Quicksilver reads, writes, propagation time |
| QS-v2-p1 | https://blog.cloudflare.com/quicksilver-v2-evolution-of-a-globally-distributed-key-value-store-part-1/ | Quicksilver v2 tiered design rationale |
| Hollow | https://netflixtechblog.com/netflixoss-announcing-hollow-5f710eefca4b | Hollow snapshots, deltas, memory |
| Envoy-xDS | https://www.envoyproxy.io/docs/envoy/latest/api-docs/xds_protocol | xDS delta, ACK/NACK semantics |
| RFC-5782 | https://datatracker.ietf.org/doc/rfc5782/ | DNS blocklists architecture |
| Spamhaus | https://www.spamhaus.org/faqs/dnsbl-usage/ | Spamhaus rsync zone interval |
| AWS-WAF | https://docs.aws.amazon.com/waf/latest/developerguide/limits.html | AWS WAF IP set max, propagation |
| GCP-June25 | https://status.cloud.google.com/incidents/ow5i3PPK96RduMcb1SsW | Google Cloud Service Control outage 2025-06-12 |
| CF-Nov25 | https://blog.cloudflare.com/18-november-2025-outage/ | Cloudflare bot mgmt feature file incident |
| CF-Jul25 | https://blog.cloudflare.com/5-december-2025-outage/ | Cloudflare Dec 5 2025 outage |
| CF-Jul19 | https://blog.cloudflare.com/details-of-the-cloudflare-outage-on-july-2-2019/ | Cloudflare WAF regex incident |
| CS-CF291 | https://www.crowdstrike.com/blog/channel-file-291-rca-available/ | CrowdStrike parameter mismatch incident |

## 1. Google Safe Browsing API v4/v5

**What is distributed:** Hash prefixes of malicious URLs (4 to 32 bytes, with Rice-Golomb compression for 4-byte prefixes in v4, extended to all sizes in v5 using big-endian encoding) (SB-v4). Includes phishing, malware, and unwanted software lists.

**Data size:** Handled by local database on client (Chrome, Firefox, Safari). Clients perform prefix lookup locally and request full hashes only on hit. Prefix-only model keeps local DB small (megabytes range).

**Consumer count:** Billions of browsers (Chrome, Firefox, Safari, etc.) performing ~1 trillion Safe Browsing checks daily at scale.

**Push vs pull:** Pull. Clients request updates from servers; servers return updates containing new hashes and removals using RawHashes or RiceDeltas compression format. Client drives update frequency.

**Snapshot vs delta:** Both. Clients maintain a local database; updates are deltas that add and remove entries. Removal uses RiceDeltas encoding. Full refresh happens periodically or on significant list change.

**Propagation latency:** minimumWaitDuration in server response enforces minimum request interval (typical 600+ seconds, ~10 minutes). New threat hashes propagate within hours after detection and deployment (SB-v4-freq). Slow propagation acceptable for malware detection (hours OK).

**Lookup locally:** Hash prefix lookup in local database. On match, client requests full SHA256 hash from server to confirm. Allows safe-browsing to scale: most requests answered locally.

**Failure mode:** If distribution plane fails (server unreachable), clients fall back to previously cached database. No safety loss, only staleness risk increases. This fail-static pattern preferred over blocking on network failure.

**Published incident:** None documented in primary sources for Safe Browsing itself.

## 2. Certificate Revocation: CRLSets and CRLite

**What is distributed:** CRLSets (Chrome): Precomputed CRL snapshots from all CAs. CRLite (Mozilla): Filter cascade (Cuckoo filters) over CRL snapshot, plus deltas (CRL-Moz-2025, CRL-blog). Represents entire revoked certificate list for TLS ecosystem.

**Data size:** CRLite: 4 MB snapshot every 45 days, ~54.3 kB average delta update, ~300 kB revocation data per browser per day combined (CRL-Moz-2025). CRLSets have maximum size constraints (not published). CRLite filters represent millions of revoked certificates in highly compressed form.

**Consumer count:** Chrome: 1.5B+ users. Mozilla Firefox: 400M+ users. Each TLS handshake triggers revocation check on client side.

**Push vs pull:** Pull. Firefox periodically fetches CRLite snapshot and deltas; Chrome receives CRLSets bundled in browser updates (automatic during browser auto-update).

**Snapshot vs delta:** CRLite uses both: 4 MB snapshot every 45 days + daily deltas (54.3 kB avg). Delta updates use IXFR-style incremental zone transfer (per RFC 5782 semantics). Snapshots ensure clients can recover even if delta chain broken.

**Propagation latency:** CRLite: 45-day snapshot cycle with daily deltas (typically published daily or on-demand). CRLSets: Updated with browser releases (roughly quarterly to monthly) (CRL-Moz-2025). Fast revocation slow compared to OCSP but more private.

**Lookup locally:** Cuckoo filter lookup (O(1) time, very high speed, minimal memory overhead). False positives trigger full SHA256 hash check against CRL snapshot. Filter chosen specifically for fast hardware lookup without memory bloat.

**Failure mode:** Revocation checks fail open (assume certificate valid) if update plane fails. Safe default: accept certificate. Mozilla moving to CRLite to avoid OCSP dependency (Let's Encrypt ending OCSP stapling in 2025 due to privacy, scaling concerns).

**Published incident:** None major. CRLite introduced precisely to avoid single points of failure (OCSP responders).

## 3. Cloudflare Quicksilver

**What is distributed:** Key-value configuration (rules, routes, edge settings, customer policies) replicated to every point-of-presence globally. Includes DNS settings, SSL certificate data, bot rules, DDoS configs.

**Data size:** 2.5 trillion reads/day, ~30 million writes/day average (QS-2020). Early deployments: 200 servers per PoP, thousands of PoPs globally. Per-server dataset: gigabytes on replica servers, megabytes on proxy caches.

**Consumer count:** 200+ cities, 90+ countries, thousands of edge servers (QS-2020).

**Push vs pull:** Push. Server pushes updates to all PoP replicas via replication stream. Quicksilver v1: full replication to every machine. Quicksilver v2: tiered replica-proxy design because "storing the full dataset on every server is inefficient" — only ~20% of keyspace used in large DCs, ~1% in small DCs (QS-v2-p1).

**Snapshot vs delta:** Delta only. Incremental updates streamed continuously to replicas and proxies.

**Propagation latency:** v1: Within seconds globally (typical 1-5 seconds). v2: Sub-second p99 latency reported. Tiered design adds relay servers within each data center to fan-out updates from replica servers (prevents thundering herd of proxies connecting directly to single replica).

**Lookup locally:** In-memory key-value lookup, microsecond latency.

**Failure mode:** v2: Replica servers fail over to next replica. Proxy caches can serve evicted keys with staleness. Reads degrade gracefully (stale data possible).

**Published incidents:** Quicksilver v2 2025 redesign mentions scaling constraints from universal replication (QS-v2-p1). No major outage documented.

## 4. Meta Configerator (Facebook SOSP 2015 Paper)

**What is distributed:** Service configuration (feature flags, quotas, service parameters, database routing) to all servers (Configerator: "Holistic Configuration Management at Facebook" in SOSP 2015 Proceedings, pp. 328-343). Single source of truth for config across billions of users.

**Data size:** Multiple thousands of distinct config parameters per service. Size grows linearly with service complexity. Replicated to millions of servers in a datacenter.

**Consumer count:** 100K-1M+ servers per datacenter. Each service instance reads config on startup and via observer updates.

**Push vs pull:** Push via observers on every server. Zeus control plane propagates config changes to observers. PackageVessel used for large configs via BitTorrent to avoid bandwidth saturation on control plane. Proxies on each server cache configs locally and serve all reads (zero latency, no network hop).

**Snapshot vs delta:** Deltas. Only changed config values pushed (canary and gatekeeper gates changes before global rollout). Eliminates propagating unchanged config to entire fleet.

**Propagation latency:** [unverified — specific time values not found in accessible sources; paper not directly fetched]. Likely sub-second to seconds based on observer push model.

**Lookup locally:** In-memory on observer process; local proxy serves lookups with millisecond latency. All reads satisfied locally (no network round-trip).

**Failure mode:** Static stability: system continues on last known good config. Canary gates detect bad configs before fleet-wide rollout (changes tested on 1% before 50% before 100%). Rollback via config version control.

**Published incident:** None documented in primary sources. Design explicitly targets preventing config-driven outages.

## 5. Netflix Hollow

**What is distributed:** Read-only datasets (movie metadata, user profiles, catalogs, recommendations) as snapshots plus deltas to consumer JVMs in Netflix edge and internal services (Hollow).

**Data size:** Entire dataset held in-memory on each consumer. Encoding and bit-packing minimize heap footprint. Deduplication automatically removes redundant data across dataset (Hollow). Typical datasets range from 100 MB to several GB per service.

**Consumer count:** 1K-100K+ consumer instances per service. Each instance holds entire dataset independently (total in-memory cache).

**Push vs pull:** Pull. Consumers periodically pull snapshots and deltas from blob storage (S3 or similar). Consumers drive update frequency, no server-side push needed.

**Snapshot vs delta:** Both. Producer writes snapshot to blob storage; Hollow auto-generates deltas. Consumers cycle through snapshots and apply deltas. Delta cost negligible compared to snapshot because only changes propagated.

**Propagation latency:** Cycle interval (configurable, typically minutes to hours). Single cycle means consumer reads new snapshot once locally loaded. Near-instant within a cycle for deltas (Hollow).

**Lookup locally:** Direct in-memory fixed-length encoding; no hash table overhead (replaces POJOs). Deduplication optimizes heap; encoding is compact. Fast traversal without deserialization cost.

**Failure mode:** If blob storage unreachable, consumers keep using last-known dataset in memory indefinitely. High-density caching means no data loss risk. Consumers degrade gracefully (serve stale data).

**Published incident:** None documented. Design chosen for reliability: in-memory cache never evicts, never has misses once loaded.

## 6. AWS WAF IP Sets

**What is distributed:** List of IP addresses (up to 10,000 addresses/ranges per IP set) for blocking/allowing in WAF rules (AWS-WAF). Rules reference IP sets which are evaluated on every HTTP/HTTPS request.

**Data size:** 10,000 max addresses/ranges per IP set (AWS-WAF). Multiple IP sets may be associated with a rule. Total per WAF instance typically 10s to 100s of sets.

**Consumer count:** All AWS WAF evaluation engines in all regions. CloudFront, ALB, API Gateway integration points globally.

**Push vs pull:** Push. Changes propagate to all regions' WAF evaluation engines. Updates triggered by customer API calls (UpdateIPSet) or console changes.

**Snapshot vs delta:** Full config snapshot pushed (AWS Builders Library constant work pattern: full config pushed every few seconds regardless of change). Simplicity over optimization.

**Propagation latency:** "From a few seconds to a number of minutes" per AWS documentation (AWS-WAF). During propagation, updates visible in one region while still propagating to another. Eventual consistency model.

**Lookup locally:** O(n) worst-case or trie lookup on every request. Typically optimized with hash set (O(1) average). No per-request network call.

**Failure mode:** Gradual propagation means clients may see inconsistent block/allow decisions during rollout (split-brain risk). No fast global rollback mechanism (must iterate through each region).

**Published incident:** No major incident documented in primary sources for WAF IP sets specifically. Constant work pattern trades efficiency for robustness.

## 7. DNS-Based Blocklists (DNSxL)

**What is distributed:** Lists of IP addresses (for blocking spam, malware) accessed via DNS queries. Spamhaus, Barracuda, and others operate public blocklists (RFC-5782, Spamhaus). Querying mechanism decouples list operator from list consumer.

**Data size:** Large lists (millions of IPs for major blocklists), stored as DNS zone data. Zone stored as distributed DNS resource records queryable by any nameserver.

**Consumer count:** All mail servers, ISPs, enterprises subscribing (estimates: 10s of millions of mail servers worldwide). Decentralized consumer model.

**Push vs pull:** Hybrid. Pull via DNS queries (client initiates lookup) OR push via rsync zone transfer (Spamhaus: "Data Feed service is intended for corporate networks, spam filter companies, and ISPs") (Spamhaus). Corporate deployments use rsync for fast local delivery.

**Snapshot vs delta:** IXFR-style zone transfers (incremental changes) supported for rsync (RFC 5782 IXFR). Spamhaus DNS zones allow incremental fetches. Rsync feeds: full zone every sync cycle for speed.

**Propagation latency:** Spamhaus SBL: rebuilt every 5 minutes. PBL: every 15 minutes (Spamhaus). DNS queries: immediate once zone propagated to querying nameserver. TTL typically 1-5 minutes means cached queries stale by that much.

**Lookup locally:** DNS server (BIND, Unbound, etc.) caches zone locally after rsync/IXFR. Query-time lookup: O(1) in cache. No network call per-message if cached.

**Failure mode:** If blocklist service unreachable, mail server falls back to accepting mail (fail-open). Safe default: allow rather than block legitimate traffic on network outage.

**Published incident:** None major documented. Decentralization and DNS redundancy make single-point failures rare.

## 8. Envoy xDS and Service Mesh

**What is distributed:** RBAC policies, IP allowlists, route configs, certificate data to sidecar proxies and gateways (Envoy-xDS). ACLs determine which workload can call which. IP allowlists implement service-to-service authentication.

**Data size:** Per-workload configuration (small to medium, typically 10s to 100s KB per sidecar). Scales linearly with number of rules and policies.

**Consumer count:** 1M+ sidecars in large service meshes (Kubernetes, on-prem, cloud deployments). Each sidecar connects to control plane independently.

**Push vs pull:** Push. Management plane (Istiod in Istio, custom xDS server in Envoy-native) pushes xDS resources to proxies via gRPC streaming. Proxies connect and hold open connection.

**Snapshot vs delta:** Delta xDS (incremental). Only changed resources sent (RDS, CDS, EDS, LDS resource types). Full state-of-the-world on reconnect or explicit request. Nonce field pairs requests and responses for ACK/NACK.

**Propagation latency:** gRPC streaming: milliseconds to seconds depending on network, batch size, and control plane processing. Bidirectional streaming allows server to stream updates in real-time (Envoy-xDS).

**Lookup locally:** In-memory trie or hash map on proxy. RBAC/IP allowlist checks on every request. No network round-trip to control plane for each request.

**Failure mode:** Proxy NACKs invalid config (error_detail present in DeltaDiscoveryRequest). Stays on last-known good version indefinitely. No unsafe config ever applied. Prevents cascading failures from bad policies.

**Published incident:** None major documented. Incremental protocol and ACK/NACK validation make config errors non-catastrophic.

## 9. Global Config Push Incidents

Distributed configuration systems inevitably fail because humans write config, and config validation is hard. These incidents show actual production failures and recovery strategies.

### Google Cloud Service Control (June 12, 2025)

Outage: 10:51 to 18:18 UTC (7h 27m total impact). A new feature added May 29 for "additional quota policy checks" went into code but had unsafe assumptions. On June 12, a policy change inserted into regional Spanner tables with "unintended blank fields" (GCP-June25). The code path for null field handling never exercised during canary rollout because canary used different policy values. Null pointer dereference caused Service Control binaries to crash loop across all regions. Impact: authentication and authorization failed globally until rollback. Lesson: validate configs at producer before replication; test on representative data during canary; use optional fields, never assume presence.

### Cloudflare Bot Management (November 18, 2025)

Outage: 11:20 UTC start, ~10 minutes to detection, ~30 minutes to resolution (40-minute window). Root cause: database permissions change caused ClickHouse query to return duplicate metadata from both `default` and `r0` shards. Feature file doubled in size. Bot Management system has a hard limit: 200 machine learning features; normal load ~60 features. System panicked with "unwrap() on Err value" when exceeding 200 (CF-Nov25). Feature file generated every 5 minutes by ClickHouse query. Because all servers received the file simultaneously (global push, no gradual rollout), panic crashed the entire fleet in minutes. Impact: HTTP 5xx errors across all customers. Lesson: set rate limits and validate file size before propagation; implement server-side circuit breakers for config constraints; always use canary or staged deployment even for "small" changes.

### Cloudflare WAF Regex (July 2, 2019)

Outage: 13:42-14:52 UTC (70 minutes). New WAF Managed Rules deployed at 13:42 UTC intended to block inline JavaScript in XSS attacks. One rule contained regex `(?:(?:\"|'|\]|\}|\\|\d|(?:nan|infinity|true|false|null|undefined|symbol|math)|\`|\-|\+)+[)]*;?((?:\s|-|~|!|{}|\|\||\+)*.*(?:.*=.*)))`  with catastrophic backtracking in the pattern `.*(?:.*=.*)` (CF-Jul19). CPUs hit 100% across entire fleet within 3 minutes. Global WAF termination issued at 14:09 UTC restored traffic instantly. Total outage 27 minutes. Lesson: test regexes for ReDoS attacks (Regular Expression Denial of Service); use regex engine with worst-case guarantees (re2, Rust regex); never deploy untested rules to WAF globally; always canary regex rules; consider simple string matching instead.

### Cloudflare Body Parsing (December 5, 2025)

Outage: 08:47-09:12 UTC (25 minutes). Two config changes made simultaneously while addressing CVE-2025-55182. Change 1: increase WAF buffer size to 1 MB. Change 2 (problematic): turn off internal WAF testing tool (felt unnecessary). Global configuration system propagates "within seconds to the entire fleet" with no gradual rollout (CF-Jul25). FL1 version of proxy had unhandled code path: disabling WAF testing tool caused error state. 28% of Cloudflare's HTTP traffic impacted. Lesson: global config system must support canary rollout or circuit breakers; test config changes in staging first; never assume disabling a tool is "safe" without explicit test coverage.

### CrowdStrike Falcon Sensor (July 19, 2024)

Outage: 04:09-05:27 UTC (78 minutes). Content update for Channel File 291 (named pipe execution detection rules). New IPC Template Type had 21 input parameter fields, but integration code supplied only 20 values. Mismatch caused out-of-bounds memory read in Content Interpreter, crashing Windows kernel (CS-CF291). Wildcard matching in tests masked the bug until non-wildcard deployment. ~13 million Windows hosts crashed globally. Recovery: rollback deployed; ~99% sensors online by July 29. Lesson: validate all template parameters; treat parameter counts as critical invariants; test with non-wildcard matching; implement producer-side validation before sending config to fleet; validate consumer receives expected parameter count before use.

## Numbers Most Likely Quoted in Interview

| Number | Meaning | Source |
|---|---|---|
| 4 to 32 bytes | Safe Browsing hash prefix size range | SB-v4 |
| 2.5 trillion | Quicksilver reads per day | QS-2020 |
| 30 million | Quicksilver writes per day | QS-2020 |
| 4 MB / 45 days | CRLite snapshot size and interval | CRL-Moz-2025 |
| 54.3 kB | Average CRLite daily delta size | CRL-Moz-2025 |
| 300 kB/day | CRLite bandwidth per browser | CRL-Moz-2025 |
| 10,000 | AWS WAF max IP set addresses | AWS-WAF |
| 5 minutes | Spamhaus SBL rebuild interval | Spamhaus |
| 15 minutes | Spamhaus PBL rebuild interval | Spamhaus |
| 200 features | Cloudflare bot mgmt feature limit (Nov 25) | CF-Nov25 |
| 5 minutes | Cloudflare feature file refresh interval | CF-Nov25 |
| 20 parameters | CrowdStrike Falcon expected input count | CS-CF291 |
| 21 parameters | CrowdStrike Falcon actual input count (fault) | CS-CF291 |
| 7h 27m | Google Cloud Service Control outage duration | GCP-June25 |
| 25 minutes | Cloudflare Dec 5 2025 outage duration | CF-Jul25 |
| 28% | Traffic impact of Dec 5 Cloudflare outage | CF-Jul25 |
| 70 minutes | Cloudflare July 2 2019 WAF outage duration | CF-Jul19 |
| 3 minutes | Time to CPU 100% in WAF outage | CF-Jul19 |
| 100% CPU | Peak CPU utilization in WAF outage | CF-Jul19 |

## Key Patterns from Real Systems

Push is used when latency is critical (Service Mesh with xDS, Configerator for fast config changes). Pull is used when consumers are decentralized (browsers checking Safe Browsing, mail servers checking DNSBLs). Hybrid is used when both parties want to optimize (Spamhaus rsync + DNS).

Snapshot + delta is always better than full push every time (Netflix Hollow, CRLite, Envoy xDS). Deltas compress dramatically and clients can apply incrementally. Snapshots provide recovery and circuit-break cascading failures from corrupted delta chains.

Validation at producer beats validation at consumer (Google Cloud incident: null field in Spanner should have been rejected before replication). Validate early. Canary gates beat global propagation (Cloudflare incidents: feature file should have been tested on 1% before 100%).

Every system that failed did so with a single propagation event (Cloudflare Nov 18: all servers hit at once with doubled file). Staged rollout plus circuit breakers (max file size, max feature count, parameter count validation) prevent these cascades.

Local lookup always wins. All systems cache data locally and serve requests without network round-trip to control plane. This is non-negotiable for latency and availability.

Fail-static (keep last known config) is safer than fail-open (accept all) for blocklists but may be wrong for feature flags. Choose based on business semantics: blocking malware should stay safe on network outage; feature flags typically fail-open (disable feature, not enable it).

---

## Spot-check corrections (2026-09-27, verified against the primary source by hand)

The agent's text above is kept as written. Where it disagrees with this table, this table wins. Numbers used in `solution.md` come from this table only.

| Claim above | Correct value | Source checked |
|---|---|---|
| Cloudflare 18 Nov 2025: "~30 minutes to resolution (40-minute window)" | Failures began 11:20 UTC, core traffic "largely flowing as normal" by 14:30, all systems normal at 17:06. The feature file "is refreshed every few minutes and published to our entire network". Limit 200 features, ~60 in use. Remediation: harden ingestion of config files "like user-generated input", more kill switches, review failure modes of core proxy modules | https://blog.cloudflare.com/18-november-2025-outage/ |
| Google Cloud 12 Jun 2025: "10:51 to 18:18 UTC" and "canary used different policy values" | Times are US/Pacific. Policy data with "unintended blank fields" was written to regional Spanner tables and "replicated globally within seconds". Code path had no error handling and was "not feature flag protected". Red-button rollout completed "within 40 minutes"; us-central1 took "up to ~2h 40 mins" because Service Control lacked randomized exponential backoff (herd on its Spanner dependency). The "different canary values" sentence is not in the report | https://status.cloud.google.com/incidents/ow5i3PPK96RduMcb1SsW |
| Cloudflare 2 Jul 2019: "70 minutes" and "27 minutes" both called the outage | Rule deployed 13:42, global WAF kill 14:07, traffic and CPU normal by 14:09 (27 minutes of impact). 14:52 is when the WAF was re-enabled. At the time Quicksilver distributed about 350 changes/s with a p99 of 2.29 s to every machine worldwide. Remediation included "staged rollouts of rules" and re2 / Rust regex | https://blog.cloudflare.com/details-of-the-cloudflare-outage-on-july-2-2019/ |
| CrowdStrike: "~13 million Windows hosts" | 8.5 million Windows devices, under 1% of Windows machines (Microsoft). RCA: IPC Template Type defined 21 input fields, sensor supplied 20; findings include "Template Instances should have staged deployment" and runtime bounds checks | https://blogs.microsoft.com/blog/2024/07/20/helping-our-customers-through-the-crowdstrike-outage/ and https://www.crowdstrike.com/wp-content/uploads/2024/08/Channel-File-291-Incident-Root-Cause-Analysis-08.06.2024.pdf |
| CRLite: "filter cascade (Cuckoo filters)", "IXFR-style deltas", "54.3 kB average delta" | 2025 CRLite uses clubcards, a "partitioned two-level cascade of Ribbon filters" (the 2017 design was a Bloom filter cascade). 4 MB snapshot every 45 days, delta updates every 12 hours, users download 300 kB of revocation data per day on average. CRLSets cover about 1% of revocations (35k of 4 M). OCSP blocks the handshake 100 ms at the median. The 54.3 kB figure and the IXFR link were not found | https://hacks.mozilla.org/2025/08/crlite-fast-private-and-comprehensive-certificate-revocation-checking-in-firefox/ |
| Quicksilver v1: "200 servers per PoP, thousands of PoPs", "typical 1 to 5 s" | 2.5 trillion reads/day, 30 million writes/day, 90,000 database instances, 200 cities in 90 countries. LMDB on every server because several processes can read one store concurrently. Three-tier fan-out: nodes query main-nodes, which query top-mains. Secondary mains keep about a week of history so a machine offline for a week can resync. No per-server size given | https://blog.cloudflare.com/introducing-quicksilver-configuration-distribution-at-internet-scale/ |
| Quicksilver v2: "sub-second p99" | Not in part 1. What is there: about 20% of the keyspace was in use in large data centers and about 1% in small ones, so full replication everywhere wasted disk. New roles: replica (full dataset) and proxy (persistent cache that evicts unused keys). "Over 3 billion keys per second" served | https://blog.cloudflare.com/quicksilver-v2-evolution-of-a-globally-distributed-key-value-store-part-1/ |
| Configerator: "100K to 1M+ servers per datacenter", propagation unverified | Paper numbers: three-level tree leader to observer to proxy, hundreds of observers under the leader, clusters of thousands of servers. Commit to servers about 14.5 s baseline: about 5 s git commit, 5 s git tailer, 4.5 s through the tree "to reach hundreds of thousands of servers distributed across multiple continents". Automated canary about 10 minutes. The proxy keeps an on-disk cache so an app can read its config "even if all Configerator components fail". A reconnecting observer sends its latest transaction id and asks for the missing writes. PackageVessel (BitTorrent) for configs larger than 1 MB, delivered in under 4 minutes. 16% of high-impact incidents over three months were configuration related | https://research.facebook.com/file/877841159827226/holistic-configuration-management-at-facebook.pdf |
| AWS WAF IP sets use "constant work, full config pushed every few seconds" | Not supported. Constant work is described for AWS Hyperplane (under Network Load Balancer): customer changes go into a configuration file in Amazon S3, and Hyperplane nodes "fetch this configuration from Amazon S3 every few seconds", loading it "even if nothing has changed". WAF docs only say propagation takes seconds to minutes | https://aws.amazon.com/builders-library/reliability-and-constant-work/ (read via web.archive.org, the live URL redirects to a JS page) |
| Safe Browsing: "~1 trillion checks daily", "minimumWaitDuration typical 600 s" | Not verified. What the docs do say: most prefixes are 4 bytes, any length 4 to 32; after each update the client computes SHA-256 of its lexicographically sorted local list and compares it with the server's checksum; on mismatch it clears the list and requests a full update; removals are indices into the sorted list | https://developers.google.com/safe-browsing/v4/local-databases |
