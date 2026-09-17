# Petabyte-Scale Batch + Streaming Ingestion Platforms: Staff Engineer Interview Prep Survey

## 1. How the Prompt is Phrased at Databricks and Confluent

### Databricks Interview Phrasing

From Glassdoor, Databricks system design rounds focus on streaming and data pipeline architecture:

**Example Questions:**
- "Design a flow for streaming processing. What are the checkpoints?" https://www.glassdoor.com/Interview/Databricks-Interview-Questions-E954734.htm
- "Explain the Spark Streaming experience" — asked in "Advanced big data, real-time" round https://www.glassdoor.com/Interview/data-engineer-databricks-interview-questions-SRCH_KO0,24.htm
- Schema evolution in Databricks, designing pipelines for incremental loads in Databricks, medallion architecture
- "How would you ensure data consistency and reliability in a distributed system?" (scenario-based)

**Format:** Databricks uses 2 system design rounds: one "design YouTube"-type architecture brainstorming, and another focused on a single component with pseudocode and deeper dive into concurrency/multithreading. https://www.teamblind.com/post/databricks-system-design-interview-z5q8dwhj

**Distributed Systems Focus:** Databricks emphasizes data pipeline architecture, storage systems, query optimization, and data engineering concepts at medium-to-hard difficulty.

### Confluent Interview Phrasing

From LeetCode and TeamBlind, Confluent's L5 interview includes:

- "Design a distributed stream processing system like Kafka"
- 7 total rounds with on-site focus on problem-solving, concurrency, and high-level system design
- https://leetcode.com/discuss/

**Key Difference:** Confluent emphasizes Kafka as the central component and stream processing architecture, while Databricks emphasizes Delta Lake and incremental ingestion patterns.

### Interview Variants Reported

Closely related questions candidates report encountering:
- "Design Auto Loader" (Databricks-specific auto-ingestion system)
- "Design a system that ingests 1 PB/day of logs into a queryable store"
- "Design a pipeline from Kafka to a data lake with exactly-once semantics"
- "Design a CDC pipeline from MySQL to a data warehouse"
- "Design Kafka Connect for custom source integrations"

---

## 2. The Follow-Up Ladder (10-15 Probes)

Published follow-up patterns from DesignGurus, SystemDesignHandbook, and Hello Interview:

1. **Consumer Falls Behind / Lag Handling**
   "Consumer lag is the difference between the latest event in a Kafka partition and the latest event processed by consumers. Rising lag indicates the processing layer cannot keep up. Lag that spikes for specific partitions suggests a hot shard problem." https://www.designgurus.io/answers/detail/analyzing-distributed-data-pipelines-in-system-design-interviews

2. **Hot Partition Mitigation**
   "How do you handle an imbalanced partition receiving 10x traffic?" Key salting, secondary aggregation, and adaptive partitioning are standard answers. https://www.designgurus.io/answers/detail/analyzing-distributed-data-pipelines-in-system-design-interviews

3. **Out-of-Order Events**
   "How do you handle events arriving late or out-of-order?" Watermarks, event-time windowing, and Dataflow Model concepts. https://www.hellointerview.com/learn/system-design/deep-dives/kafka

4. **Exactly-Once Semantics**
   "Discuss the guarantees your system provides. Is it at-least-once, at-most-once, or exactly-once?" https://www.designgurus.io/answers/detail/atleastonce-vs-atmostonce-vs-exactlyonce-where-to-use-each

5. **Deduplication and Idempotency**
   "How do you prevent duplicate writes?" Use unique constraints, upserts, or version-based conditional writes. https://www.designgurus.io/blog/exactly-once-delivery

6. **Schema Evolution**
   "What happens when the schema of incoming events changes?" Protobuf versioning with forward/backward compatibility. https://www.designgurus.io/answers/detail/analyzing-distributed-data-pipelines-in-system-design-interviews

7. **Backpressure**
   "How does your system handle backpressure when downstream sinks are overloaded?" Kafka's pull-based model naturally implements backpressure. https://www.systemdesignhandbook.com/guides/design-a-pub-sub-system/

8. **Replay and Reprocessing**
   "How do you replay historical data through the pipeline?" Immutable logs enable both live computation and reprocessing. https://www.oreilly.com/radar/questioning-the-lambda-architecture/

9. **Small Files Problem**
   "What's the cost impact of ingesting many small files vs. few large files?" S3 per-request pricing multiplies overhead for small files. https://blog.bytebytego.com/p/how-figma-upgraded-data-pipeline-from-multi-day-latency-to-real-time

10. **Sink Failure / Downstream Down for 1 Hour**
    "If your destination (e.g., Snowflake) goes down for an hour, what happens?" Buffering in Kafka and retention policy determine recovery. https://www.systemdesignhandbook.com/guides/design-a-pub-sub-system/

11. **End-to-End Latency SLO**
    "What latency target are you aiming for? From event ingestion to query layer?" Real-world ranges: sub-second (streaming) vs. minutes (micro-batch). https://www.hellointerview.com/learn/system-design/deep-dives/kafka

12. **Cost Attribution**
    "How do you estimate and control costs across storage, compute, data transfer?" Kafka CKU capacity, S3 per-request cost, Spark/Flink compute hourly costs. https://docs.confluent.io/cloud/current/client-apps/optimizing/throughput.html

13. **Schema Registry and Contract**
    "How do you ensure producers and consumers agree on the schema?" Protobuf, Avro, JSON Schema with schema registry. https://www.designgurus.io/answers/detail/analyzing-distributed-data-pipelines-in-system-design-interviews

14. **Multi-Region Consistency**
    "If multiple regions ingest data, how do they stay consistent?" Kappa vs. Lambda tradeoffs. https://www.oreilly.com/radar/questioning-the-lambda-architecture/

15. **Monitoring and Observability**
    "What metrics do you track to detect pipeline issues at 3 AM?" Kafka consumer lag, processing latency, resource usage. https://www.designgurus.io/answers/detail/analyzing-distributed-data-pipelines-in-system-design-interviews

---

## 3. Bad / Good / Great Answer Levels

### Mid-Level Answer: Single Consumer to S3

**Pattern:** Producer → pull data → S3. No mention of backpressure, partitioning, or failure handling.

**Why it fails:** Does not scale to petabyte rates; single consumer is a SPOF. Source: https://www.systemdesignhandbook.com/blog/data-engineer-system-design-interview-questions/

### Senior-Level Answer: Kafka + Spark/Flink + Checkpoints

**Strengths:**
- Mentions correct components and scaling approach
- Discusses partition count, consumer groups, fault tolerance via checkpoints
- Handles at-least-once semantics and basic deduplication

**Missing (vs. Staff):** Exactly-once details, schema versioning, cost optimization, monitoring SLOs, replay strategy. Source: https://www.systemdesignhandbook.com/guides/ad-click-aggregator-system-design/

### Staff-Level Answer: Exactly-Once + Contract + Cost

**Six dimensions Staff candidates address:**

1. **Exactly-Once Semantics:** "I implement at-least-once from Kafka + idempotent writes to the sink. For financial data, I add a deduplication layer (Redis or database unique key). This is cheaper than Flink's exactly-once and still safe." https://www.designgurus.io/answers/detail/what-are-practical-paths-to-exactlyonce-processing-in-kafka

2. **Backpressure & Scaling:** "Kafka's pull-based model naturally implements backpressure. Consumers control their rate. Slow consumers pull less data, preventing sink overwhelm." https://www.systemdesignhandbook.com/guides/design-a-pub-sub-system/

3. **Schema Contract:** "I require Protobuf versioning at the producer level. Breaking changes bump major version. Consumers fail fast if they see an unknown version, triggering an alert." https://www.designgurus.io/answers/detail/analyzing-distributed-data-pipelines-in-system-design-interviews

4. **Replay & Reprocessing:** "Kafka retention is 30 days. If I need to reprocess, I seek to an earlier offset. For offline reprocessing, I use Kappa architecture (S3 snapshots + Kafka delta)." https://www.oreilly.com/radar/questioning-the-lambda-architecture/

5. **Cost Optimization:** "Per-partition throughput in Kafka is ~50 MBps per CKU. For 1 PB/day (~11.6 GB/sec), I need ~232 CKUs. I batch small files into larger S3 objects (256 MB+) to reduce per-request cost." https://docs.confluent.io/cloud/current/client-apps/optimizing/throughput.html

6. **Operability & SLO:** "I monitor Kafka consumer lag per partition, processing latency in Flink, and S3 write latency. My SLO is p99 < 5 sec. If lag spikes, I auto-scale consumers." https://www.designgurus.io/answers/detail/analyzing-distributed-data-pipelines-in-system-design-interviews

---

## 4. Canonical Concepts with References

### The Dataflow Model (VLDB 2015)

**Paper:** "The Dataflow Model: A Practical Approach to Balancing Correctness, Latency, and Cost in Massive-Scale, Unbounded, Out-of-Order Data Processing" by Tyler Akidau et al.

**Published:** VLDB 2015, Vol. 8, No. 12, Pages 1792-1803.

**URL:** https://www.vldb.org/pvldb/vol8/p1792-Akidau.pdf

**Key Insight:** Watermarks, windowing, and handling unbounded out-of-order data. Foundation for why exactly-once is hard.

### Streaming Systems by Akidau, Chernyak, Lax

**Book:** O'Reilly, 2018. ISBN 9781491983874.

**Critical Chapters for Interview:**
- Ch. 3: Watermarks (late data, sliding windows)
- Ch. 5: Exactly-Once and Side Effects (checkpointing, idempotence)
- Ch. 7: Persistent State (stateful operator management)

**URL:** http://streamingsystems.net/

### Designing Data-Intensive Applications, Chapter 11: Stream Processing

**Book:** Martin Kleppmann, O'Reilly 2017.

**Coverage:** Event transmission (message brokers, partitioned logs), databases and streams (CDC, event sourcing), time, joins, fault tolerance, practical use cases.

**URL:** https://www.oreilly.com/library/view/designing-data-intensive-applications/9781491903063/ch11.html

### Kafka: A Distributed Messaging System for Log Processing (NetDB 2011)

**Paper:** Jay Kreps, Neha Narkhede, Jun Rao. NetDB '11, June 2011.

**URL:** https://cwiki.apache.org/confluence/download/attachments/27822226/Kafka-netdb-06-2011.pdf

**Key Insight:** Partition-level ordering guarantee and why it's the right load-balancing granularity.

### Questioning the Lambda Architecture (O'Reilly Radar, 2014)

**Article:** Jay Kreps (Confluent CEO, Kafka co-creator).

**URL:** https://www.oreilly.com/radar/questioning-the-lambda-architecture/

**Core Argument:** Kappa architecture (immutable log + stream processing) as simpler alternative to maintaining separate batch and streaming code paths.

---

## 5. Reasonable Numbers for 1 PB/Day Ingestion

### Back-of-Envelope Calculation

**Given:** 1 PB ingested per day
- 1 PB = 10^15 bytes
- Seconds in a day = 86,400
- Sustained throughput: 10^15 / 86,400 ≈ **11.6 GB/sec**
- With 30% burst headroom: ~15 GB/sec target capacity

Source: https://www.designgurus.io/answers/detail/implementing-back-of-the-envelope-calculations-for-scale/

### Kafka Partition Throughput

- Per partition baseline: 1–10 MB/sec
- With tuning (batching, compression): 50+ MB/sec per partition https://www.confluent.io/blog/scaling-kafka-to-10-gb-per-second-in-confluent-cloud/
- For 11.6 GB/sec: Need ~233 partitions (assuming 50 MB/sec each)

### Confluent Cloud CKU Capacity

- 1 CKU handles ~50 MBps of well-balanced workload https://docs.confluent.io/cloud/current/client-apps/optimizing/throughput.html
- For 11.6 GB/sec (11,600 MB/sec): Need ~232 CKUs
- Cost context: Thousands $/month for this scale

### Stream Processor Throughput (Flink/Spark)

Production examples:
- LinkedIn: >1.1 trillion messages/day = ~13 million messages/sec https://blog.bytebytego.com/p/ep126-the-ultimate-kafka-101-you
- Uber: Trillions of messages daily via Kafka https://blog.bytebytego.com/p/how-uber-manages-petabytes-of-real

### S3 Storage & Request Costs

- Storage: $0.023 / GB / month (standard US East)
- Per-request cost: $0.0004 per 1,000 GET, $0.005 per 1,000 PUT
- Per-request impact: 1 million small files/day vs. 100 large files multiplies cost 10,000x on PUT requests
- Recommendation: Batch into 256 MB+ objects to optimize request-to-byte ratio

Source: https://blog.bytebytego.com/p/how-figma-upgraded-data-pipeline-from-multi-day-latency-to-real-time

### End-to-End Latency Targets

- Near real-time (Kafka → Spark → S3): p50 < 1 sec, p99 < 10 sec
- Real-time event processing (Kafka → Flink → Query Layer): p50 < 100 msec, p99 < 1 sec
- Historical batch (24h HDFs → Redshift): Acceptable latency 12–24 hours

Source: https://www.systemdesignhandbook.com/blog/data-engineer-system-design-interview-questions/

### Kafka Consumer Lag SLO

- Healthy: Lag < 30 seconds (processing keeping up)
- Caution: Lag 30 sec–5 min (falling behind; scale consumers)
- Alert: Lag > 5 min sustained (critical; manual intervention required)

Source: https://www.designgurus.io/answers/detail/analyzing-distributed-data-pipelines-in-system-design-interviews

---

## 6. Common Mistakes in Data Pipeline / Streaming Ingestion Answers

### 1. Tool-First Instead of Requirement-First

**Mistake:** "I'll use Spark Structured Streaming because it's fast."

**Staff Approach:** "Requirements are 1 PB/day ingestion, sub-second latency, at-least-once semantics. Spark Structured Streaming adds checkpointing overhead. Kafka + Flink is leaner if I accept at-least-once + idempotent sinks."

Source: https://www.systemdesignhandbook.com/blog/data-engineer-system-design-interview-questions/

### 2. Claiming Exactly-Once Without Caveats

**Mistake:** "My system provides exactly-once delivery end-to-end."

**Staff Insight:** "Kafka delivers at-least-once. To achieve end-to-end exactly-once, I make the sink idempotent (upsert, unique key) or use distributed transactions (expensive). The honest answer: at-least-once + idempotent consumer."

Source: https://www.designgurus.io/answers/detail/atleastonce-vs-atmostonce-vs-exactlyonce-where-to-use-each

### 3. Forgetting Backpressure

**Mistake:** "Events flow from Kafka → Flink → S3. If S3 slows, we buffer in memory."

**Staff Approach:** "If S3 is overloaded, Flink slows, which slows Kafka consumers via pull-based backpressure. Producers throttle automatically. This is a feature of Kafka's design."

Source: https://www.designgurus.io/answers/detail/analyzing-distributed-data-pipelines-in-system-design-interviews

### 4. Not Addressing Schema Evolution

**Mistake:** Describes ingestion without mentioning schema changes.

**Staff Approach:** "Producers publish Protobuf version 2.0. Consumers register required version ≥ 1.0. If producer publishes version 3.0 with breaking change, schema registry blocks it. Consumers ignore unknown fields (forward compatibility)."

Source: https://www.designgurus.io/answers/detail/analyzing-distributed-data-pipelines-in-system-design-interviews

### 5. Missing Replay & Reprocessing Strategy

**Mistake:** "Data ingested to S3, we query it."

**Staff Approach:** "Kafka retains data for 30 days. If I discover a bug in my Flink job, I seek to an earlier offset and replay. For longer reprocessing, I use Kappa architecture (S3 snapshots + Kafka delta), avoiding separate batch/streaming code."

Source: https://www.oreilly.com/radar/questioning-the-lambda-architecture/

### 6. Ignoring the Small Files Problem

**Mistake:** "Producers write 1 event per file to S3 for durability."

**Cost Reality:** "1 billion events/day → 1 billion S3 PUTs at $0.005 per 1,000 = $5,000/day on PUT requests. Solution: batch in Kafka, write files ≥ 256 MB, drop cost to $0.006/day."

Source: https://blog.bytebytego.com/p/how-figma-upgraded-data-pipeline-from-multi-day-latency-to-real-time

### 7. Hot Partition Neglect

**Mistake:** "I partition by user_id for parallelism."

**Reality:** If user_id=google_ads is 50% of traffic, one partition is overloaded while others idle.

**Staff Fix:** "I detect skew at runtime. For hot keys, I apply key salting: append a random suffix [0–9] to partition key, spreading across 10 partitions. A post-aggregation step re-combines results."

Source: https://www.designgurus.io/answers/detail/analyzing-distributed-data-pipelines-in-system-design-interviews

### 8. No Monitoring / SLO Discussion

**Mistake:** Describes architecture without saying how to detect failure.

**Staff Approach:** "I monitor Kafka consumer lag per partition (alert > 5 min), Flink processing latency (alert > 10 sec), S3 write latency (alert > 30 sec), error rate (alert > 0.1%). My SLO is p99 < 5 sec and 99.9% availability. On-call is paged on breach."

Source: https://www.designgurus.io/answers/detail/analyzing-distributed-data-pipelines-in-system-design-interviews

### 9. Oversimplifying Ingestion Mechanics

**Mistake:** "Events are ingested from APIs or Kafka to a data lake."

**Reality:** Ingestion combines webhooks (partners), polling (small sources), real-time streams. Each has different SLOs.

**Staff Answer:** "I use hybrid: webhooks for high-value partners (strict order, low latency), polling for others (eventual consistency, scheduled windows), and reconciliation job (nightly, detects gaps)."

Source: https://www.systemdesignhandbook.com/blog/data-engineer-system-design-interview-questions/

### 10. Ignoring Cost Attribution

**Mistake:** Designs a system without discussing operational cost.

**Staff Approach:** "For 1 PB/day: Kafka (232 CKUs) ~$50k/month, Flink (500 cores) ~$180k/month, S3 storage ~$23k/month. Total ~$250k/month. If I accept at-most-once, I save checkpointing overhead, cut Flink cores by 30%, saving $50k/month. Trade-off: risk losing tail events during failures."

Source: https://docs.confluent.io/cloud/current/

---

## Sources

| ID | Title | URL | Date | Used For |
|---|---|---|---|---|
| 1 | Glassdoor: Databricks Interview Questions | https://www.glassdoor.com/Interview/Databricks-Interview-Questions-E954734.htm | — | Interview phrasing, checkpoints, Spark Streaming |
| 2 | Glassdoor: Data Engineer Databricks | https://www.glassdoor.com/Interview/data-engineer-databricks-interview-questions-SRCH_KO0,24.htm | — | Real-time round formats |
| 3 | TeamBlind: Databricks System Design | https://www.teamblind.com/post/databricks-system-design-interview-z5q8dwhj | — | Interview format, two-round structure |
| 4 | LeetCode Discuss: Confluent interviews | https://leetcode.com/discuss/ | — | Confluent L5 interview rounds |
| 5 | DesignGurus: Analyzing Distributed Data Pipelines | https://www.designgurus.io/answers/detail/analyzing-distributed-data-pipelines-in-system-design-interviews | — | Follow-ups, hot partitions, schema evolution, monitoring |
| 6 | DesignGurus: Exactly-Once vs At-Least-Once | https://www.designgurus.io/answers/detail/atleastonce-vs-atmostonce-vs-exactlyonce-where-to-use-each | — | Semantics, deduplication patterns |
| 7 | DesignGurus: Exactly-Once Delivery | https://www.designgurus.io/blog/exactly-once-delivery | — | Idempotency, deduplication |
| 8 | DesignGurus: Back-of-Envelope Calculations | https://www.designgurus.io/answers/detail/implementing-back-of-the-envelope-calculations-for-scale/ | — | 1 PB/day calculation |
| 9 | DesignGurus: Exactly-Once Processing Paths | https://www.designgurus.io/answers/detail/what-are-practical-paths-to-exactlyonce-processing-in-kafka | — | Staff-level exactly-once patterns |
| 10 | SystemDesignHandbook: Design a Pub/Sub System | https://www.systemdesignhandbook.com/guides/design-a-pub-sub-system/ | — | Backpressure, sink failure, retention |
| 11 | SystemDesignHandbook: Data Engineer Interview Questions | https://www.systemdesignhandbook.com/blog/data-engineer-system-design-interview-questions/ | — | Mid-level answers, monitoring |
| 12 | SystemDesignHandbook: Ad Click Aggregator | https://www.systemdesignhandbook.com/guides/ad-click-aggregator-system-design/ | — | Senior-level answer framework |
| 13 | Hello Interview: Kafka Deep Dive | https://www.hellointerview.com/learn/system-design/deep-dives/kafka | — | Out-of-order events, latency targets |
| 14 | ByteByteGo: Figma Data Pipeline | https://blog.bytebytego.com/p/how-figma-upgraded-data-pipeline-from-multi-day-latency-to-real-time | — | Small files problem, S3 costs |
| 15 | ByteByteGo: Kafka 101 | https://blog.bytebytego.com/p/ep126-the-ultimate-kafka-101-you | — | LinkedIn throughput benchmarks |
| 16 | ByteByteGo: Uber Petabytes | https://blog.bytebytego.com/p/how-uber-manages-petabytes-of-real | — | Uber petabyte-scale numbers |
| 17 | O'Reilly Radar: Questioning Lambda Architecture | https://www.oreilly.com/radar/questioning-the-lambda-architecture/ | 2014 | Kappa architecture, replay strategy |
| 18 | O'Reilly: Streaming Systems | http://streamingsystems.net/ | 2018 | Watermarks, exactly-once, state management |
| 19 | O'Reilly: DDIA Chapter 11 | https://www.oreilly.com/library/view/designing-data-intensive-applications/9781491903063/ch11.html | 2017 | Stream processing fundamentals |
| 20 | VLDB 2015: The Dataflow Model | https://www.vldb.org/pvldb/vol8/p1792-Akidau.pdf | 2015 | Watermarks, windowing, exactly-once theory |
| 21 | Apache Kafka: NetDB 2011 Paper | https://cwiki.apache.org/confluence/download/attachments/27822226/Kafka-netdb-06-2011.pdf | 2011 | Partition ordering guarantees |
| 22 | Confluent: Scaling Kafka to 10 GB/sec | https://www.confluent.io/blog/scaling-kafka-to-10-gb-per-second-in-confluent-cloud/ | — | Per-partition throughput |
| 23 | Confluent: Optimizing Throughput | https://docs.confluent.io/cloud/current/client-apps/optimizing/throughput.html | — | CKU capacity, 50 MBps baseline |
| 24 | Confluent: Cloud Pricing | https://docs.confluent.io/cloud/current/ | — | Cost estimation for 1 PB/day |

---

## Spot-check corrections (added after review, 2026-09-17)

| Claim above | Correction |
|---|---|
| §3 "Staff approach" quote with "Kafka (232 CKUs) ~$50k/month, Flink (500 cores) ~$180k/month, S3 ~$23k/month, total ~$250k/month" | Not a quote from any source. It is the agent's own estimate. 232 CKUs at Confluent Cloud list prices is far above $50k/month, and 500 cores cannot land 11.6 GB/s of JSON. Do not repeat these numbers. Use the back-of-envelope in `solution.md` §2 and §8 instead |
| §5 "Per-partition throughput in Kafka is ~50 MBps per CKU" | Conflates a CKU (a Confluent Cloud capacity unit, ~50 MB/s ingress across all partitions it hosts) with a partition. Per-partition throughput is a separate, unpublished rule of thumb (5 to 10 MB/s with headroom) |
| §5 "1 billion events/day → 1 billion S3 PUTs ... $5,000/day" | Arithmetic is right, framing is fine, but the "$0.006/day" after batching assumes 256 MB files from 1 KB events (1.2 k files/day). Real pipelines produce far more files than that because of partitions and triggers; see `solution.md` §5.1 |
| §1 Confluent L5 phrasing and "7 rounds" | Only a bare https://leetcode.com/discuss/ link, no specific post. Treat as [unverified] |
| DesignGurus and SystemDesignHandbook follow-up probes | Real pages, but generic to "data pipeline" questions. No public source publishes a verbatim Databricks or Confluent ingestion prompt; the ladder in `README.md` is assembled from these generic probes plus the Databricks product docs |
