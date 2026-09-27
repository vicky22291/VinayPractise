# Interview Framing Survey: Server Health Monitoring and Alerting

One-line summary: How interviewers define requirements, scale, and probe sequencing for metrics monitoring / alerting systems across FAANG and Staff-level rounds.

## 1. Public Framings and Scale Assumptions

### Hello Interview Metrics Monitoring Breakdown
https://www.hellointerview.com/learn/system-design/problem-breakdowns/metrics-monitoring

Functional requirements:
- Ingest metrics (CPU, memory, latency, custom counters) from services
- Query and visualize metrics on dashboards with filters, aggregations, and time ranges
- Define alert rules with thresholds over time windows (e.g., p99 latency >500ms for 5 min)
- Receive notifications when alerts fire (email, Slack, PagerDuty)

Scale assumptions (enterprise baseline):
- 500k servers monitored
- 5 million metrics per second ingestion rate at peak
- 100 metric data points per server every 10 seconds
- ~1GB/second raw data volume (100-200 bytes per metric)
- Alert evaluation latency < 1 minute
- Dashboard query latency within seconds (spanning days/weeks)

### DesignGurus Metrics & Monitoring System
https://designgurus.substack.com/p/design-a-metrics-and-monitoring-system

Functional requirements:
- Support pushing metrics via API or agent with tags
- Querying with aggregations over time ranges
- Visualization for line charts and gauges
- Alert rule definition and notifications
- Multi-dimensional tagging for flexible queries

Scale (enterprise level):
- 100,000 monitored hosts
- 99% write, 1% read workload distribution
- Write acknowledgment < 50ms to agents
- Dashboard response < 500ms
- Alert triggering ~1 minute from event

Retention strategy (tiered):
- Raw 10-second granularity: 7 days
- 1-minute resolution: 30 days
- 1-hour resolution: 1 year

### ByteByteGo Metric Monitoring Architecture
https://blog.bytebytego.com/p/metric-monitoring

High-level architecture components:
- Metrics sources (application servers, SQL databases, message queues)
- Metrics collector (gathers and writes to time-series database)
- Kafka (decouples collection from processing, provides durability)
- Stream consumers (Apache Storm, Flink, Spark process and push downstream)
- Time-series database with label indexes for fast lookups
- Query service for retrieval and aggregation
- Alerting system (sends notifications to multiple destinations)
- Visualization system (graphs, charts, dashboards)

### Google SRE Book: Four Golden Signals
https://sre.google/sre-book/monitoring-distributed-systems/

Core metrics for user-facing systems:
- Latency (distinguish successful vs. failed requests; slow errors worse than fast)
- Traffic (HTTP requests per second, concurrent sessions)
- Errors (explicit failures, implicit failures, policy violations like SLO breaches)
- Saturation (most-constrained resource; latency increases are leading indicator)

### Google SRE Book: Practical Alerting
https://sre.google/sre-book/practical-alerting/

Alert severity levels:
- Page-worthy: Critical, requires immediate on-call response
- Subcritical: Important but non-urgent, directed to ticket queues
- Informational: Supports dashboards without notifications

Every page must satisfy:
- Detect otherwise undetected, urgent, actionable, user-visible condition
- Be ignorable only in specific, understood scenarios
- Indicate actual user impact
- Enable actionable responses
- Avoid duplicate paging across teams

## 2. Follow-Up Probe Ladder (Ranked by Likelihood)

1. **Push vs. Pull model tradeoff** https://www.designgurus.io/course-play/grokking-the-system-design-interview/doc/push-vs-pull-architecture

   Prometheus (pull): Services expose /metrics endpoint; Prometheus server scrapes at defined intervals. Control of ingestion rate by monitoring system. Immediate outage detection when scraping fails.
   
   InfluxDB/Datadog (push): Applications send metrics directly to database. Database is passive. Rate control burden on application layer. https://designgurus.substack.com/p/system-design-of-time-series-databases

2. **Heartbeat interval and detection time** https://designgurus.substack.com/p/a-crash-course-on-distributed-systems

   Short interval + short timeout = fast failure detection but high false positive rate. Long interval = fewer false positives but slow detection. Tradeoff: choose based on SLO and false positive tolerance.

3. **Network partitions and false positives** https://designgurus.substack.com/p/a-crash-course-on-distributed-systems

   Server may be slow, not dead. Heartbeat timeout cannot distinguish. Solution: use multiple independent networks; mark node down only after "down" appears in all monitored paths. Or require N consecutive missed heartbeats before declaring failure.

4. **Alert storm from cascading failures** https://sre.google/sre-book/practical-alerting/

   Single node failure should not page on-call. Aggregate signals before alerting. Example: alert only if error rate > 1% AND error count > 1/sec simultaneously. Use AND logic, not OR.

5. **Alert deduplication and grouping** https://image-ppubs.opensource.gov/dirsearch-public/print/downloadPdf/12368733

   Spatial dedup: multiple instances of same message combined into single alert. Temporal dedup: repeated occurrences of same alert combined. Grouping: multiple related alerts clustered into single incident for on-call visibility.

6. **Alert flapping prevention** https://sre.google/sre-book/practical-alerting/

   Rules require minimum duration (typically 2+ rule evaluation cycles) for condition to be true before firing. Prevents rapid on/off cycling when metric hovers near threshold. Hysteresis logic needed in threshold evaluation.

7. **Who monitors the monitoring system** https://www.hellointerview.com/learn/system-design/problem-breakdowns/metrics-monitoring

   Monitoring infrastructure itself must be monitored (recursive problem). Borgmon-style: one Borgmon per datacenter monitoring local jobs, 2+ global Borgmons aggregating across datacenters for redundancy.

8. **Cardinality explosion** https://www.hellointerview.com/learn/system-design/problem-breakdowns/metrics-monitoring

   High-dimensional tags (service, region, datacenter, endpoint, status code, method) create exponential label combinations. Example: 20 services x 5 regions x 100 endpoints = 10k unique metrics per base metric type. Storage and query performance degrade.

9. **Storage: TSDB vs. wide-column stores** https://designgurus.substack.com/p/system-design-of-time-series-databases

   Prometheus uses local file-based TSDB with mmap. InfluxDB uses log-structured merge tree with Gorilla compression. Cassandra/HBase: wide-column, built by KairosDB/OpenTSDB, excellent for high write throughput. Tradeoff: local vs. distributed, compression vs. query speed.

10. **Retention and downsampling strategy** https://designgurus.substack.com/p/system-design-of-time-series-databases

   Raw 10-second data retained 7 days costs massive storage. Solution: after 7 days, downsample to 1-minute averages for 30 days, then 1-hour for 1 year. Reduces storage 90%+ while preserving trend visibility.

11. **Kafka in front of TSDB** https://blog.bytebytego.com/p/metric-monitoring

   Metrics producer -> Kafka -> consumers (Storm, Flink, Spark) -> TSDB. Decouples collection from processing. Provides durability. Allows replay for reprocessing. Risk: adds latency and complexity; verify it's needed at scale.

12. **Multi-region architecture** https://sre.google/sre-book/managing-critical-state/

   Bigtable replicated in each region. Alerting rules evaluated in each region independently. Global aggregation layer for cross-region incident correlation. Replicate monitoring to handle regional failure.

## 3. Senior vs. Staff Distinction

### What Hello Interview Identifies as Staff-Level
https://www.hellointerview.com/blog/staff-level-system-design

Senior focuses on building functional systems; Staff focuses on architectural judgment:
- Choose between competing designs and explain why, not present one option.
- Define the problem scope, not just solve the one handed.
- Lead the conversation about tradeoffs across teams.
- Make business-level decisions visible (latency over cost, time-to-market over correctness).
- Own end-to-end deployment, monitoring, scaling, evolution story.

For health monitoring specifically:
- Senior designs a working metrics pipeline and alerting rules.
- Staff designs how multiple teams consume and trust the monitoring system, how on-call shifts use it, what SLO it itself must meet, and how org structure owns correctness.

### DesignGurus Staff-Level Playbook
https://designgurus.substack.com/p/the-staff-engineers-system-design

Shift from knowledge to judgment. Measure whether candidate can lead conversation and handle organizational complexity, not just technical prowess.

## 4. Common Mistakes Candidates Make

https://www.designgurus.io/blog/system-design-tips-from-ex-google-interviewer

1. **Skip requirement clarification.** Jump to architecture without asking what metrics to monitor, expected scale, alert latency tolerance. Cost 10-15 minutes of bad assumptions.

2. **Ignore data volume.** Claim "we'll use Redis" or "Prometheus" without calculating: 5M metrics/second at 200 bytes each = 1GB/second raw. Wrong storage choice becomes showstopper.

3. **Miss alert SLO.** Claim alerts fire in seconds. At 5M metrics/second, rule evaluation window must be batched. Realistic target is 30-60 seconds, not 5 seconds.

4. **No deduplication or grouping.** Assume each alert fires independently. With cascading failures, a single datacenter outage triggers 100k page-outs to on-call. Candidate lacks production experience.

5. **False positive blind spot.** Claim "heartbeat every 5 seconds, declare dead after 15 seconds" without discussing network flakiness, GC pauses, or load spikes that cause false positives.

6. **Treat monitoring as afterthought.** Only mention it when asked. Staff-level candidates mention it unprompted and tie SLO of monitoring itself to business SLO.

## Consolidated Functional Requirements

The following functional requirements appear across all framings (Hello Interview, DesignGurus, ByteByteGo, Google SRE):

- **Metrics ingestion**: Ingest metrics from distributed servers and services at 5M metrics per second. Accept push or pull model. Support custom application metrics, not just system metrics (CPU, memory).
  
- **Time-series storage**: Store metrics durably in a time-series database with label indexes for fast lookups by tag combinations. Support range queries and aggregations.

- **Alert rule evaluation**: Evaluate alert rules defined over metrics (e.g., "error rate > 5% for 5 minutes") with latency < 1 minute from metric emission to alert decision.

- **Alert notification**: Send notifications via email, Slack, PagerDuty, SMS when alerts fire. Deduplicate and group related alerts before notifying to reduce alert fatigue.

- **Dashboard visualization**: Render metrics on dashboards with aggregation (sum, avg, p50, p99), filtering (by tags), and time-range selection (last hour to last year). Return results in < 500ms.

- **Multi-dimensional tagging**: Support querying by multiple label dimensions (service, region, datacenter, endpoint, method, status code). Enable drill-down analysis from aggregate to specific instance.

- **Out-of-order handling**: Handle metrics that arrive late or in wrong sequence. Buffer and reorder if needed, or discard with explicit policy.

- **Historical retention**: Store metrics at multiple granularities: 10-second raw for 7 days, 1-minute aggregates for 30 days, 1-hour for 1 year. Support querying across all retention tiers.

## Consolidated Non-Functional Requirements

Based on Hello Interview, DesignGurus, and Google SRE guidance:

**Scale**: 500k servers monitored, 5 million metrics per second at peak ingestion. Each metric ~100-200 bytes (timestamp, value, ~5 labels at 20 bytes each). Implies 1GB/second raw data bandwidth and petabytes per year storage without downsampling.

**Latency targets**:
  - Ingestion write acknowledgment to agent: < 50ms (implies batching, not immediate persistence).
  - Alert rule evaluation: < 1 minute from metric emission to alert state change. Latency < 60s at 5M metrics/sec implies batch windows, not per-metric evaluation.
  - Dashboard query: < 500ms even for year-long time ranges. Requires aggressive downsampling and indexing.

**Availability**: 99.9% uptime for monitoring platform itself. Monitoring system becoming SPOF is unacceptable. Design for geographic redundancy and fault isolation.

**Consistency model**: Eventual consistency acceptable for dashboards (5-10 second staleness tolerable). Strong consistency required for alert rule evaluation state to avoid duplicate firing or missed alerts.

**Data retention** (tiered by queryability and cost):
  - Raw 10-second granularity: 7 days (recent high-fidelity analysis).
  - 1-minute roll-up: 30 days (trend analysis).
  - 1-hour roll-up: 1 year (historical comparison and capacity planning).
  - Older data archived to cold storage or discarded per retention policy.

**Failure mode tolerance**:
  - Metric loss acceptable during transient ingestion failure (fire-and-forget UDP-style or batches) but not for alerting (must guarantee alert evaluation completes).
  - False positive rate must be < 1% under normal operation to avoid alert fatigue and on-call burnout.
  - False negative rate (missed alerts) must be < 0.1% under normal operation to maintain SLO compliance.

## Top 10 Probe Ladder

Ranked by frequency and impact on design:

1. **Push or pull metrics collection model? Why?**
   Probes architectural knowledge and tradeoff reasoning. Expected: justify choice based on scale, network topology, failure detection speed. Weak answer: "use Prometheus because it's popular." Strong answer: "We choose pull because we control ingestion rate and immediately detect service failures when scraping fails. Tradeoff: services must expose /metrics endpoint and be network-accessible to collectors."

2. **How do you prevent alert storms when a rack fails and 1000 servers go dark?**
   Tests understanding of aggregation and alert design maturity. Expected: aggregate by region/service before alerting, use AND logic over multiple signals, dedup related alerts. Weak answer: fire 1000 individual alerts. Strong answer: "Define rules like 'alert if error rate > 5% for region X AND error count > 1000/sec.' Deduplicate: merge into single incident for on-call."

3. **What heartbeat interval do you choose and why? How do you handle network partitions?**
   Probes distributed systems fundamentals and false-positive tolerance. Expected: name interval (10-30 sec common), acknowledge false positive risk, discuss multiple missed heartbeats (N >= 3). Weak answer: "heartbeat every 5 seconds, declare dead after 10 seconds." Strong answer: "30-second interval with 3 missed = 90 second detection. Rationale: tolerates GC pauses, network flakiness under load."

4. **How do you distinguish between a slow server and a dead server?**
   Tests whether candidate understands FLP impossibility. Expected: acknowledge you cannot, discuss timeout vs. false positive tradeoff, mention multiple independent channels as mitigation. Weak answer: "just check if response time > X." Strong answer: "Fundamentally impossible. We mitigate with multiple networks and require server to be down on all paths before alerting."

5. **How do you prevent alert flapping when a metric hovers near the threshold?**
   Probes alert quality. Expected: require minimum duration (2+ cycles) before firing, mention hysteresis logic. Weak answer: fire immediately. Strong answer: "Rule is true for at least 2 consecutive 1-minute evaluation windows before we fire. Prevents oscillation at threshold."

6. **Who monitors the monitoring system? What happens if the monitoring system itself fails?**
   Tests end-to-end thinking and SPOF awareness. Expected: run 2+ independent global monitors, each monitoring the other, discuss local monitors in each datacenter. Weak answer: "use Prometheus, assume it works." Strong answer: "Global monitors health-check each other and local datacenters. If global A fails, global B takes over. Local monitor continues even if global is down."

7. **How do you handle cardinality explosion from high-dimensional tags?**
   Tests production experience. Expected: discuss label design limits, prune unused combinations, mention cardinality buckets. Weak answer: "use all labels." Strong answer: "Limit unique value counts per tag (e.g., 100 endpoints max). Prune label combinations that never appear. Monitor cardinality growth and alert if it exceeds threshold."

8. **Which time-series database and why? (Prometheus local vs. InfluxDB vs. Cassandra/HBase)**
   Tests storage design tradeoffs. Expected: name specific choice with scale justification and failure modes. Weak answer: "use TSDB." Strong answer: "Prometheus for < 1M metrics/sec single region (simple, works out of box). Cassandra + KairosDB for 10M+/sec multi-region (distributed, complex to operate, adds ~100ms latency)."

9. **How do you store 1GB/second of metrics long-term without bankrupting the company?**
   Tests cost-awareness and downsampling understanding. Expected: describe tiered retention with downsampling. Weak answer: "store everything forever." Strong answer: "7-day raw 10-sec, 30-day 1-min (90% compression), 1-year 1-hour (further 60x). Total cost: ~$2-5M/year for 5M metrics/sec."

10. **How do you evaluate alert rules across 5 million metrics per second in under 60 seconds?**
    Tests throughput and latency understanding. Expected: discuss batching, parallel evaluation, sherding of rules by metric type. Weak answer: "evaluate each metric one by one." Strong answer: "Batch metrics by rule set. Evaluate rules in 10-15 second windows. Parallelize evaluation across 100+ CPUs. Alert fires within 60 seconds of metric arrival."

## Sources Table

| Source | URL | Reliability |
|--------|-----|-------------|
| Hello Interview | https://www.hellointerview.com/learn/system-design/problem-breakdowns/metrics-monitoring | FAANG staff engineers, official breakdown |
| DesignGurus | https://designgurus.substack.com/p/design-a-metrics-and-monitoring-system | System design course, ex-Google |
| ByteByteGo | https://blog.bytebytego.com/p/metric-monitoring | Alex Xu, author of System Design Interview Vol. 2 |
| Google SRE Book | https://sre.google/sre-book/monitoring-distributed-systems/ | Official Google production guidance |
| Google SRE Alerting | https://sre.google/sre-book/practical-alerting/ | Official Google alerting requirements |
| DesignGurus Staff Bar | https://designgurus.substack.com/p/the-staff-engineers-system-design | L6+ interview criteria |
| LeetCode Discuss | https://leetcode.com/discuss/interview-question/system-design/958919/ | Candidate reports on health monitoring questions |

## What This Means for the Design

1. **Establish scale upfront.** Always confirm in clarification phase: 500k servers or 50k? 5M metrics/second or 500k? Are metrics pushed by agents or pulled by collectors? Do not assume the Hello Interview baseline applies to your interviewer's company. Some companies monitor fewer servers but require faster alerting or more complex aggregation.

2. **Separate collection from rule evaluation.** Metrics ingest pipeline (agent or scraper -> storage) is independent from alert rule evaluation engine (reads from storage, evaluates rules, fires alerts). One can scale without the other. Decoupling via Kafka is a common pattern but adds latency; verify latency budget supports it.

3. **Push or pull is not a later question.** Decide early because it affects ingestion pipeline, failure detection strategy, and network requirements. Pull (Prometheus-style): Services expose /metrics endpoint, collectors scrape periodically. Immediate outage detection but requires collector to reach targets. Push (InfluxDB-style): Agents push to central database. Rate control at agent but requires agent installation and network access to database.

4. **Storage engine choice couples to scale.** Local time-series database (Prometheus) is simple, works for single-region < 1M metrics/sec. Distributed wide-column store (Cassandra + KairosDB, or OpenTSDB on HBase) needed for > 5M metrics/sec multi-region. Name the inflection point explicitly and justify. Do not hand-wave "use Cassandra."

5. **Ingestion rate controls everything.** At 5M metrics/second, 100-200 bytes each, raw throughput is 1GB/second. This determines: batch size to agents (500MB batches every 500ms?), consumer parallelism (100+ Kafka consumers for Storm/Flink?), database write throughput (sharding factor?), and which components fail first at 2x or 10x scale.

6. **Alert design is where most candidates fail.** Default: alert on single-server failure. Result: 1000 alerts per datacenter failure. Fix: aggregate before alerting. Example: "page only if error rate > 5% AND error count > 100/sec across region." AND logic is essential. Also require minimum duration (2+ evaluation cycles) before firing to prevent flapping.

7. **Heartbeat latency-false-positive tradeoff is non-negotiable.** Interviewer asks: "A server crashes. How long before we know?" Answer must include false positive rate. Claim: "5 seconds detection time" without mentioning false positive rate from network flakes, GC pauses, or load spikes signals inexperience. Realistic: 30-60 seconds with multiple missed heartbeats (N >= 3) to tolerate transient failures.

8. **Downsampling is mandatory, not optional.** Five million metrics per second at 200 bytes each, stored raw for 1 year, equals exabytes. Physically impossible and economically insane. Solution: after 7 days, downsample to 1-minute aggregates (coarse 10:1 reduction). After 30 days, downsample to 1-hour (further 60:1). Justify each tier by query needs: what queries run against 1-year-old data?

9. **Monitoring stack must not be a SPOF.** If monitoring goes down, nobody can detect or respond to system failures. Run 2+ independent global aggregation servers (Borgmon-style per Google SRE). Each datacenter runs its own local monitor. Monitors health-check each other. Discuss: what happens if global monitor A fails? (Answer: Global monitor B takes over; no gap in alert evaluation.)

10. **Cardinality explosion is a silent performance killer.** High-dimensional labels (service, version, region, datacenter, endpoint, method, status_code, client_type) create label combinations that explode in storage and query time. Example: 30 services x 5 regions x 100 endpoints = 15k unique metric combinations. With 50 base metric types, that's 750k time series. Indexing all combinations is expensive. Solution: (a) Prune unused combinations at ingestion, (b) Limit label cardinality per metric type, (c) Index strategically.

11. **Operator burden is part of the design.** Staff-level answer includes: How do on-call engineers acknowledge alerts? How do they silence noisy alerts during maintenance? How do they test new alert rules without triggering paging? How do they replay history for post-mortems? These operational concerns are part of the SLO contract.

12. **Business tradeoffs must be visible.** Do not hide design decisions. State them explicitly: "We accept 60-second alert latency to avoid building a real-time stream processor, reducing complexity and cost by 3x. Tradeoff: some failure modes take 1 minute to detect instead of 10 seconds." Good answers name the tradeoff, bad answers hide it and later get caught by follow-up.

13. **Common follow-up sequence.** Expect interviewer to escalate: Start with basic architecture. Then: "What breaks at 10x scale?" (Usually: single database becomes bottleneck, or cardinality explosion breaks indexes.) Then: "Fix it." (Usually: add sharding, cardinality limits, or downsampling.) Then: "Now roll this to 10 engineering teams without breaking cross-team visibility." (Org problem, not just technical. Answer must address: shared label schema, quota enforcement, cascading dashboards.)

14. **Distinguish Prometheus vs. InfluxDB use cases.** Prometheus is simpler, self-contained, and works well for 1-10M metrics/sec in single region. InfluxDB is more complex but distributed and better for 10M+ metrics/sec or multi-region with required high availability. Name which you'd pick and why, relative to scale and consistency requirements.

---

## Spot-check corrections (editor, 2026-09-27)

Checked by fetching the cited pages (`curl` plus tag stripping). The agent's text above is left as written; use this table where they disagree.

| Claim in this survey | Status | Correct value and source |
|---|---|---|
| Hello Interview FRs, NFRs (500k servers, 100 points every 10 s, 5M/s, 100 to 200 B per point, 1 GB/s, alerts under 1 minute) and the four deep dives | Verified | Public part of https://www.hellointerview.com/learn/system-design/problem-breakdowns/metrics-monitoring. The Bad / Good / Great picks are premium and were not seen |
| DesignGurus: 100,000 hosts, 99% writes, < 50 ms write ack, 500 ms dashboards, ~1 min alerts, 99.9%, eventual (5 s behind), retention 10 s for 7 d, 1 min for 30 d, 1 h for 1 y | Verified | Free part of https://designgurus.substack.com/p/design-a-metrics-and-monitoring-system. The rest of that post is paywalled |
| ByteByteGo: collectors, Kafka, Storm / Flink / Spark consumers, TSDB, query service, alerting, visualization | Verified | https://blog.bytebytego.com/p/metric-monitoring |
| Borgmon: one per datacenter, 2+ global | Verified | SRE book ch. 10: "a single Borgmon per cluster, and a pair at the global level" and "two or more global Borgmon ... one Borgmon in each datacenter" |
| Probe 5 source `https://image-ppubs.opensource.gov/...` | **Does not resolve** | Treat as fabricated. The dedup and grouping concepts are standard; cite the Alertmanager docs instead: https://prometheus.io/docs/alerting/latest/alertmanager/ |
| "Strong answer: 30 s heartbeat, 3 missed = 90 s", "weak answer: 5 s heartbeat, dead after 10 s" | **Not on the cited page** | The DesignGurus crash course only says there is no perfect timeout, "only a trade-off between false positives and response time". The 90 s recommendation is the agent's opinion. Our design uses 5 s heartbeats and a 15 s silence, made safe by a 2 of 3 observer quorum plus probes. For scale: Kubernetes marks a node unreachable after 50 s |
| "Mark node down only after it is down on all monitored paths / multiple independent networks" | Not on the cited page | Reasonable idea, not sourced. Our version: 2 of 3 observers, probes from 3 other racks, BMC over the management network |
| "Prometheus < 1M/s single region, Cassandra + KairosDB for 10M+/s, adds ~100 ms" and item 14 "Prometheus works well for 1 to 10M/s" | **Unverified and wrong** | One Prometheus handles a few hundred thousand samples/s ([`../../../concepts/time-series-db.md`](../../../concepts/time-series-db.md) §14). Horizontally scaled Prometheus-compatible stores go far past 10M/s: Grafana Mimir was tested at 1 billion active series, ~50M samples/s (https://grafana.com/blog/2022/04/08/how-we-scaled-our-new-prometheus-tsdb-grafana-mimir-to-1-billion-active-series/) |
| "Total cost ~$2 to 5M/year for 5M metrics/s" | **Invented** | Our math: ~27 TB in object storage (~$620/month) plus ~2,800 vCPU (~$70k/month). See `../solution.md` §2 and §8 |
| "5M metrics/s at 200 B stored raw for 1 year equals exabytes" | **Arithmetic wrong** | 1 GB/s × 31.5M s ≈ 31.5 PB uncompressed. At ~1.4 B per stored sample (Gorilla) it is 5M × 1.4 B × 31.5M s ≈ 220 TB |
| "Strong consistency required for alert rule evaluation state" | Unsourced, and the opposite of practice | Monarch §2 trades consistency for availability on the alerting path. Alertmanager HA is gossip, eventually consistent, deduped by a notification log. We run duplicate evaluators and dedup at the router |
| "False positive rate < 1%, false negative rate < 0.1%" | Not in any cited source | Our NFR: zero pages from monitor-side partitions, false DOWN < 0.1% of DOWN verdicts, measured by `boot_id` |
| Multi-region probe cites SRE book "Managing critical state" | Wrong source | That chapter is about Paxos-based consensus. The regional point is in Monarch §2 and §5.3 (up to 95% of standing queries evaluated inside a zone) |
| "Common mistakes" list cited to a DesignGurus blog post | Not checked | Treat as the agent's synthesis |
| LeetCode Discuss 958919 | Could not open (HTTP 403) | Content unverified |

Added by the editor (verified):
- SRE book ch. 11: an incident takes ~6 hours of work, so "the maximum number of incidents per day is 2 per 12-hour on-call shift" (https://sre.google/sre-book/being-on-call/). This is the page budget in `../solution.md` §1.2.
- SRE book ch. 10: alert `for` durations are "typically ... at least two rule evaluation cycles to ensure no missed collections cause a false alert".
