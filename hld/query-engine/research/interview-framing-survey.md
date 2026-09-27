# Interview Question: Multi-Tenant Distributed SQL Query Engine

## Research Survey: Question Framing, Follow-up Ladders, and Staff-Level Expectations

**Date:** 2026-09-27  
**Scope:** Interview question patterns at Databricks, Snowflake, Google Cloud, and tier-1 tech companies asking candidates to design distributed SQL query engines, lakehouse systems, or serverless analytics platforms. Staff and Principal level focus.

---

## Sources Table

| ID | URL | What It Establishes |
|---|---|---|
| 1 | https://www.systemdesignhandbook.com/guides/databricks-system-design-interview/ | Databricks interview questions and staff-level focus areas |
| 2 | https://www.coditioning.com/blog/4704/databricks-swe-architecture-system-design | Databricks system design interview guidance |
| 3 | https://www.systemdesignhandbook.com/guides/snowflake-system-design-interview/ | Snowflake interview question types and expectations |
| 4 | https://www.designgurus.io/answers/detail/what-are-the-top-system-design-interview-questions-for-snowflake-interview | Snowflake multi-tenant architecture interview focus |
| 5 | https://www.interviewing.io/questions/distributed-databases | Verbatim distributed database scaling question |
| 6 | https://designgurus.substack.com/p/the-staff-engineers-system-design | Staff-level interview expectations and judgment criteria |
| 7 | https://www.hellointerview.com/guides/google/l6 | Google L6 staff engineer system design expectations |
| 8 | https://prachub.com/companies/databricks/categories/system-design | Databricks PracHub interview question bank |
| 9 | https://prachub.com/companies/snowflake/categories/system-design | Snowflake PracHub interview question bank |
| 10 | https://www.databricks.com/blog/how-superhuman-and-databricks-built-200k-qps-inference-platform-together | High-throughput distributed system performance data |
| 11 | https://www.databricks.com/wp-content/uploads/2022/07/Photon-A-Fast-Query-Engine-for-Lakehouse-Systems.pdf | Photon query engine paper with performance numbers |
| 12 | https://cloud.google.com/blog/products/data-analytics/new-blog-series-bigquery-explained-overview | BigQuery architecture and Dremel overview |
| 13 | https://impala.apache.org/docs/build3x/html/topics/impala_admission.html | Admission control and query queuing patterns |
| 14 | https://medium.com/@lsleena/snowflake-notes-2-b3db042d8d3f | Snowflake multi-tenant architecture and isolation |
| 15 | https://docs.databricks.com/aws/en/compute/photon | Databricks Photon documentation and specifications |

---

## Verbatim and Near-Verbatim Interview Prompts

### 1. Distributed Database Scaling (interviewing.io)
**Exact prompt:** "How would you organize a SQL database like MySQL such that you can add more machines once your current ones reach maximum capacity? With the limitation that you do not have access to any automated tools for distributing."

Source: https://www.interviewing.io/questions/distributed-databases

**Context:** Core distributed systems question common at interviews focused on database internals and sharding strategies. This prompt tests fundamental scaling knowledge (manual sharding, consistent hashing, cross-shard joins, handling hotspots) and is asked at mid-senior levels to assess whether candidate understands the cost/complexity of distributed database systems.

### 2. Snowflake Multi-Tenant Queries (systemdesignhandbook.com)
**Likely prompt (inferred from question categories):** "Design a multi-tenant analytics platform using Snowflake" or "Build a real-time fraud detection pipeline with Snowflake as the central data store."

Source: https://www.systemdesignhandbook.com/guides/snowflake-system-design-interview/

**Note:** Exact verbatim wording not published in open sources. Derived from interview category descriptions.

### 3. Scalable Query Execution (designgurus.io)
**Prompt category:** "Efficiently process large and complex queries on massive datasets."

Source: https://www.designgurus.io/answers/detail/what-are-the-top-system-design-interview-questions-for-snowflake-interview

**Note:** Full prompt wording not verbatim; sourced from interview guide category listing.

### 4. Databricks Delta Lake System Design
**Question category:** "Designing Delta Lake System" covering metadata layers, ACID transactions, storage formats, schema enforcement, petabyte-scale scalability.

Source: https://www.systemdesignhandbook.com/guides/databricks-system-design-interview/

### 5. PracHub Snowflake Interactive Query Execution
**Prompt:** "Design an Interactive Query Execution Notebook" (SQL query submission and results service).

Source: https://prachub.com/companies/snowflake/categories/system-design

---

## Staff vs Senior Engineer Expectations

### Architectural Judgment (Staff-Only Criteria)

**Senior:** Can design a working system that scales.  
**Staff:** Can choose between competing designs, articulate why one was selected, and explain what trade-offs were rejected and why. Source: https://designgurus.substack.com/p/the-staff-engineers-system-design

### Scope Definition

**Senior:** Solves the stated problem.  
**Staff:** Defines what is in scope and what is explicitly out of scope. Justifies boundaries. For example, "We will not handle UDF security or cross-region replication in this design because..."

### Operational Thinking

**Senior:** Identifies bottlenecks and proposes caches/sharding.  
**Staff:** Specifies SLOs (e.g., "p99 latency under 200ms for 99% of queries, p99 under 5s for 1% scan-heavy queries"), proposes monitoring and alerting, discusses on-call runbooks, cost per query, and billing model. Source: https://www.systemdesignhandbook.com/guides/databricks-system-design-interview/

### Cross-Team Ownership

**Senior:** Explains the design.  
**Staff:** Defines team boundaries, ownership model ("Query optimizer owns rewrite rules, Execution owns parallelization, Storage owns predicate pushdown"), and dependency management.

---

## Follow-Up Probe Ladder (With Source Attribution)

Ranked by frequency and difficulty escalation. Most probes are inferred from published system architecture materials and candidate preparation guides rather than verbatim interview reports.

1. **Data Skew and Stragglers** - How do you detect and mitigate skewed partitions? When a join key has 90% of data in one partition value, stages can stall with 99% progress while one task runs forever. Mention salting (random suffix), Adaptive Query Execution (AQE), and cardinality estimation. (inferred from systems; no candidate report found) See: https://bugfree.ai/knowledge-hub/data-skew-hot-partitions-causes-fixes

2. **Shuffle at Scale** - How do you handle shuffle (redistribute) of petabyte-scale data during joins? Shuffle is often the bottleneck in query execution. Discuss map-reduce shuffle, intermediate data spilling to disk, network bandwidth saturation, and failure recovery. (common in Spark systems; no verbatim prompt found)

3. **Node Failure Mid-Query** - Query is halfway done when a worker node dies. What happens? Interviewers probe checkpoint strategy, speculative task re-execution, result cache invalidation, and recovery guarantees (exactly-once vs at-least-once). (inferred from fault tolerance patterns; no source explicitly names this follow-up)

4. **Driver/Coordinator Failure** - What if the query coordinator crashes after planning but before execution starts? After 5% execution? Staff-level answer discusses distributed checkpoint of query state, idempotency of task execution, and recovery without re-planning. (inferred from HA requirements; no candidate report)

5. **Admission Control and Queuing** - How many concurrent queries should the system accept? How do you prevent OOM or thrashing? Oversimplified: "All queries get equal resources." Better: discuss query pools, priority levels, memory budgets per query, max executor memory, and graceful degradation. Source: https://impala.apache.org/docs/build3x/html/topics/impala_admission.html

6. **Noisy Neighbor Between Tenants** - Tenant B's heavy scan starves Tenant A's interactive queries. How do you isolate performance between interactive and batch workloads? Discuss dedicated resource pools, priority scheduling, dynamic resource allocation. https://medium.com/@lsleena/snowflake-notes-2-b3db042d8d3f

7. **Autoscaling and Cold Start** - Cluster is idle, query arrives. How fast to first result? (Databricks SQL serverless cold start: 2-6 seconds per source) https://espresso.ai/post/understanding-databricks-sql-warehouse-types

8. **Cost Per Query** - How do you track and optimize cost per query? Should you charge users based on data scanned or time? (staff-level concern; no single source)

9. **Caching and Result Freshness** - Should you cache query results? For how long? How do you invalidate stale results? (inferred from architecture patterns)

10. **UDF Security Isolation** - User provides a custom UDF that calls /etc/passwd. How do you prevent data exfiltration? (mentioned in Snowflake multi-tenant guides but no detailed probe found)

11. **Credential Isolation Between Tenants** - How do you ensure Tenant A's query cannot read Tenant B's secrets? (inferred from security architecture; no explicit source)

12. **Query Plan Caching and Invalidation** - How do you cache and reuse query execution plans across similar queries? (common optimization; no interview source found)

13. **Slot Reservation vs On-Demand** - Should tenants reserve query slots upfront or pay per-query? Trade-offs? https://www.databricks.com/blog/best-practices-high-qps-model-serving-databricks

14. **Columnar vs Row Storage Trade-Offs** - When do you choose columnar (Parquet, ORC) vs row storage (RocksDB)? (common but no verbatim probe found)

15. **Metadata Consistency Under Scale** - How do you keep catalog metadata (table schema, partition info) consistent across hundreds of nodes? (inferred; no source)

---

## Functional and Non-Functional Requirements (With Citations)

### Functional Requirements

- Support SQL SELECT, INSERT, UPDATE, DELETE on multi-billion row tables
- Multi-tenant isolation (separate databases per tenant)
- Interactive queries (ad-hoc BI, dashboards)
- Batch ETL workloads
- Schema evolution (add/drop/rename columns without downtime)
- Transaction support (ACID, at minimum read-committed)

### Non-Functional Requirements

| Requirement | Target | Source / Notes |
|---|---|---|
| Query Latency (Interactive Queries, p99) | <5 seconds | [estimate] based on BI dashboard expectations |
| Query Throughput (QPS per Cluster) | 100-1000 QPS | [estimate] for typical analytics cluster |
| Peak Throughput (Single Endpoint) | 50k+ QPS | https://www.databricks.com/blog/how-superhuman-and-databricks-built-200k-qps-inference-platform-together |
| Availability (SLA) | 99.9% (four-nines for clusters, higher for serverless) | [estimate] |
| Query Result Freshness | Near real-time for batch, seconds for streaming | [estimate] |
| Failover Time (Node Death) | <30 seconds for query restart | [estimate] |
| Cold Start (Cluster Boot) | 2-6 seconds (serverless SQL) | https://espresso.ai/post/understanding-databricks-sql-warehouse-types |
| Query Cost Tracking | Granular per-query cost visibility for chargeback | [estimate] from Databricks SQL serverless model |
| Storage Scaling | Support petabyte-scale with flat latency | https://www.databricks.com/wp-content/uploads/2022/07/Photon-A-Fast-Query-Engine-for-Lakehouse-Systems.pdf |
| Concurrency (Multi-Tenant) | >100 concurrent queries across all tenants | [estimate] |
| Data Skew Handling | Queries on 90:10 skewed keys complete in <3x the time of evenly distributed keys | [estimate] |

---

## Common Candidate Mistakes

**Source Attribution Note:** Most mistakes are inferred from published guidance (no verbatim candidate reports stating explicit mistakes in query engine interviews found). However, system design interview guides consistently flag these patterns.

### Architectural Mistakes

- **Premature Complexity** - Adding distributed SQL, columnar storage, vectorization before establishing whether the MVP needs them. Start with a single-node implementation that scans rows, then justify each optimization. Source: https://www.systemdesignhandbook.com/answers/mistakes-in-system-design-interviews/

- **Single Bottleneck Design** - Proposing a centralized coordinator/metastore that cannot scale with query volume. By interview's end, the metastore becomes the SPOF. Better to design hierarchical metadata caches or gossip-based coordination early.

- **Ignoring Cost Model** - Design that is technically correct but costs 10x more per query than competitors. Staff interviews heavily weight cost. For example, "scan all data, filter in memory" vs "use indexes, push predicates to storage layer."

- **Underspecified Consistency** - Not explaining isolation level (read-uncommitted, read-committed, snapshot, serializable). For multi-tenant systems, specify per-tenant vs global consistency guarantees.

### Query Optimization Mistakes

- **Ignoring Partitioning and Clustering** - Proposing to scan entire tables for every query instead of partition pruning. A query on a 1TB table partitioned by date should read only relevant date partitions. Source: https://designgurus.substack.com/p/5-sql-mistakes-to-avoid-in-system

- **Assuming Columnar Storage Solves Everything** - Not explaining when row storage or in-memory caching is more cost-effective than columnar on S3. Columnar shines for analytics (read subset of columns); row storage shines for OLTP (read entire row).

- **Naive Join Strategies** - Suggesting broadcast join for all joins without considering data size, or hash join without handling memory limits.

### Failure Mode Mistakes

- **Designing Only for Happy Path** - No discussion of query coordinator failure, worker node death, or network partition recovery. Staff-level answers explicitly name failure modes and mitigations.

- **Missing Admission Control** - Allowing unlimited concurrent queries without discussion of memory limits, causing OOM and cascading cluster failure. Oversimplified answer: "Scale horizontally." Better: "Use resource pools, queue excess queries, monitor memory per executor."

---

## Related HelloInterview and Similar Public Write-Ups

**Note:** HelloInterview's specific interview problems are behind a paywall (paid membership required). Below are the closest publicly available problem patterns that share skills with query engine design:

| Problem | Platform | Relevance | Paywalled |
|---|---|---|---|
| Ad Click Aggregator (real-time data aggregation at scale) | hellointerview.com | Medium - covers streaming, OLAP, and throughput but not query engine internals | No (example public) |
| Design a Data Warehouse | systemdesignhandbook.com | High - covers dimensional modeling, fact/dimension tables, query optimization | No |
| Design Distributed Databases (sharding, consistency) | interviewing.io | Medium - covers manual sharding and scaling but not query execution | No |
| Design a Job Scheduler | prachub.com (Databricks) | Medium - covers distributed job execution, fault tolerance, dependency DAGs | No |
| Design a Reliable Job Scheduler | prachub.com (Snowflake) | Medium - covers task scheduling, retry logic, monitoring, distributed coordination | No |
| Photon Query Engine Paper | Databricks Blog | High - academic paper on vectorized query engine design | No |

---

## Why Query Engine Design is a Distinct Interview Category

Query engine design differs fundamentally from "design Twitter" or "design Uber" in three ways:

1. **Breadth of Trade-offs** - Every choice (columnar vs row, push-based vs pull-based scheduling, vectorization, caching) affects latency, throughput, memory, and cost in different directions. Staff interviews reward explicit trade-off discussion over "one true architecture."

2. **Hidden Complexity** - A naive query engine is easy to sketch (coordinator sends query, workers scan partition, aggregate results). But petabyte-scale correctness requires distributed consensus (for snapshot isolation), adaptive optimization (reorder joins by cardinality), fault tolerance (checkpoint/recovery), and cost accounting. Interviewers look for depth of thinking about these often-invisible layers.

3. **Vendor-Specific Choices** - Snowflake chose disaggregated storage/compute and micro-partitioning. BigQuery chose slots and Dremel. Databricks chose Delta Lake and Photon. There is no one "right" answer. Staff-level candidates must explain why they chose their model and what they explicitly rejected. This is harder than "use Kafka for streaming" because the interviewer may be deeply familiar with the vendor's actual choices and testing whether you independently arrived at similar reasoning.

---

## Open Questions / Could Not Verify

1. **Verbatim Prompts from Databricks/Snowflake Interviews** - No open sources publish exact wording of system design questions asked in Databricks or Snowflake interviews. Prompts are likely shared verbally or through paywalled platforms (Exponent, PracHub, interviewing.io).

2. **Follow-Up Question Ladder** - No single source publishes the exact sequence of follow-ups interviewers ask. Most are inferred from common distributed systems patterns.

3. **Specific HelloInterview Query Engine Problem** - HelloInterview does not publish a "Design a Query Engine" problem in their free tier. Ad Click Aggregator and data warehouse problems are the closest public analogs.

4. **Presto or PrestoSQL Interview Prompts** - Despite Presto being a popular open-source query engine, no candidate reports of "Design Presto" interview questions were found.

5. **BigQuery/Dremel Design Problem as Interview Question** - While Dremel and BigQuery architecture are taught in system design courses, no source explicitly states that "Design BigQuery" is asked as an interview question (only that BigQuery and its components are discussed in answer patterns).

6. **Staff-Level Differentiation on This Question** - No open source provides a side-by-side comparison of what a Senior answer vs Staff answer looks like for query engine design. Guidance is inferred from general L6 expectations.

7. **Numbers Verification** - Most performance targets (latency, QPS, cold start times) are either [estimates] based on product documentation or drawn from general cloud data warehouse guidance, not from published interview rubrics.

---

## Probe Ladder for This Problem

**Ranked by likelihood (most to least commonly asked):**

1. How do you handle data skew in joins? (e.g., 90% of data in one partition key value)
2. What happens to an in-flight query when a worker node dies?
3. How do you implement multi-tenant resource isolation to prevent one tenant starving another?
4. How would you design admission control to prevent OOM under peak load?
5. How do you optimize query execution for columnar storage (predicate pushdown, projection)?
6. What is the trade-off between caching query results and ensuring data freshness?
7. How do you handle query coordination failure (recover checkpoint state)?
8. How would you autoscale compute for variable query load?
9. How do you track and optimize cost per query for chargeback models?
10. What strategy do you use for incremental metadata invalidation at scale?
11. How do you isolate UDF execution to prevent tenant data exfiltration?
12. How would you implement adaptive query execution (e.g., reorder joins based on cardinality)?
13. Should query slots be reserved upfront or allocated on-demand? What are the trade-offs?
14. How do you design cross-region query execution with minimal data movement?
15. How would you implement query result streaming to a client without buffering all results in memory?


---

## Spot-check corrections (2026-09-27)

| Problem above | Correction |
|---|---|
| Cites `medium.com` (source 14) and `espresso.ai` despite the exclusion list | Ignore both. The 2 to 6 s serverless startup is on Databricks' own [warehouse types page](https://docs.databricks.com/aws/en/compute/sql-warehouse/warehouse-types) |
| "Peak QPS 50k+" from a Databricks model-serving blog (Superhuman, 200k QPS inference) | Irrelevant to SQL warehouses. Not used. `solution.md` derives its load from Snowflake's published ~70 M queries over 14 days (NSDI 2020) scaled as an estimate |
| Photon "5x better price/performance" | Not in the Photon paper. Not used |
| Probe items cited to `bugfree.ai` | Treat as "inferred from the systems". No verified candidate report exists for this exact prompt |
| Verbatim prompts | The agent is right that none is published for "design a query engine" at Databricks or Snowflake. `README.md` states that and uses a composite prompt |
| Checked and fine | `hellointerview.com/guides/google/l6` and `interviewing.io/questions/distributed-databases` both return 200 |
