# Multi-tenant distributed SQL query engine (Spark / Photon style)

> One-line answer: a control plane (gateway, a workload manager that queues and admits statements per warehouse, a compute manager that hands out VMs from a warm pool) in front of per-tenant warehouses, each 1 to N clusters of one driver plus K workers; the driver pins one snapshot of every table, plans with a cost-based optimizer, cuts the plan into stages at every shuffle and re-plans at each stage boundary from real sizes; workers run a vectorized columnar engine over Parquet files pruned by statistics, cache hot files on local NVMe, and write shuffle output to local disk; tenants never share a VM, small queries get cores ahead of big ones inside a cluster, clusters are added when queue time grows, a dead worker costs a re-run of only the shuffle outputs it held, a dead driver costs a transparent retry of its read-only statements, and cost is billed on warehouse-seconds and attributed to statements by the task-seconds they used.

Tier 2, problem #17 in [`hld/README.md`](../README.md). Asked at Databricks and Snowflake as "design a distributed SQL engine over S3", "design Spark SQL / Databricks SQL", "design BigQuery", "design a serverless SQL service for many customers". It is Databricks' product in disguise (Photon, SQL warehouses), so interviewers drill into mechanisms: how a plan becomes stages, why the shuffle hurts, what a lost node costs, how one tenant is kept from hurting another. Reusable blocks: [`../delta-lake-transactions/`](../delta-lake-transactions/) (the table format we read, snapshot pinning), [`../../concepts/columnar-db.md`](../../concepts/columnar-db.md) (Parquet, stats, vectorised execution), [`../../concepts/fan-out-fan-in.md`](../../concepts/fan-out-fan-in.md) (stragglers and tail latency), [`../../concepts/rate-limiting-and-load-shedding.md`](../../concepts/rate-limiting-and-load-shedding.md) (admission control), [`../../concepts/caching-patterns.md`](../../concepts/caching-patterns.md), [`../distributed-job-scheduler/`](../distributed-job-scheduler/) (DAG execution, leases). Sources in [`research/`](research/).

## Problem statement (as asked)

No verbatim prompt is published for this question (see [`research/interview-framing-survey.md`](research/interview-framing-survey.md)). The composite version:

Thousands of companies keep their tables as Parquet files in object storage (S3, ADLS, GCS) under a table format. Their analysts run SQL from BI dashboards, notebooks and scheduled jobs: millions of small queries that must come back in about a second, and some joins over tens of terabytes. Design the service that plans and runs those queries across many machines, keeps tenants from seeing or slowing each other, survives machines dying mid-query, starts compute in seconds but costs nothing when idle, and tells each tenant what every query cost.

## Functional requirements

Core:
- **Run a SQL query and get the result.** Submit over JDBC/ODBC or REST, poll or cancel, get small results inline and large results as downloadable chunks.
- **Distribute the work.** One query runs on tens to hundreds of machines. Scans split into tasks over files. Joins and aggregations repartition rows between machines (shuffle).
- **Share the service between tenants.** Compute on demand in seconds, nothing billed when idle, no tenant sees or slows another. Inside a tenant, a dashboard query is not stuck behind a batch query.
- **Survive failure.** A dead worker, a slow node, or a lost driver does not fail the query in the common case, and never returns a wrong or silently partial result.
- **Know and bound the cost of every query.** Meter every statement, attribute it to tenant and user, stop runaway queries with guardrails.

Below the line (say it out loud):
- The table format and its transactions (problem #15). We read a pinned snapshot and commit writes through it.
- Catalog internals and governance. Assume a service that maps names to paths, checks grants, applies row filters, and vends short-lived credentials.
- Streaming queries, Python and ML workloads beyond "user code runs sandboxed", cross-region federation, the SQL editor UI.

## Non-functional requirements

| Dimension | Target |
|---|---|
| Load | 10,000 active tenants per region, 20 M statements/day, peak ~2,300 submits/s |
| Query mix | 90% small (≤ 1 GB scanned after pruning), 9.5% medium (1 to 500 GB), 0.5% large (0.5 to 100 TB) |
| Latency | Small: p50 < 500 ms, p99 < 2 s excluding queue. Medium: p99 < 60 s on a right-sized warehouse. Large: bound by scan rate, ~40 GB/s on a 32-worker cluster |
| Concurrency | 10 running statements per cluster, then queue (≤ 1,000 per warehouse) or add a cluster |
| Startup | Stopped warehouse to first query in 2 to 6 s. New cluster for scale-out in < 30 s |
| Isolation | No VM or process shared across tenants. A heavy tenant moves another tenant's p99 by < 5%. A small query waits < 1 s behind a big one in the same cluster |
| Availability | 99.95% for submit, status and cancel. Infrastructure-caused query failures < 0.1% |
| Consistency | One snapshot per table per query. Cached results never stale. Read-your-writes within a session |
| Cost | Billed per second of warehouse uptime. Auto-stop after 10 min idle. Per-query attribution sums to the bill within 1% |

## What interviewers probe (the ladder)

1. Walk a `JOIN ... GROUP BY` from SQL text to tasks on machines. Where are the stage boundaries and why there?
2. One join key holds 30% of the rows. What happens to the stage, and how does the engine notice and fix it without the user?
3. A worker dies while the reduce stage is fetching. What exactly is lost, what is re-run, and how long does it take?
4. The driver dies. What happens to the 10 queries running on it? Which ones can you retry safely?
5. A 10 TB query and 200 dashboard users share one warehouse. Why does the dashboard get slow, and what are the three layers that fix it?
6. How does a stopped warehouse answer its first query in 5 seconds? What does that cost the provider, and who pays?
7. The shuffle for one query is 32 million blocks of 14 KB. Why is that bad, and what are the options (broadcast, AQE, push-merge, remote shuffle)?
8. How do you tell a tenant what one query cost when 10 queries share a cluster?
9. The result cache returned stale data after a write. How is that impossible by construction?
10. Why vectorized interpretation instead of code generation for the execution engine?

## Files

| File | What it is |
|---|---|
| [`solution.md`](solution.md) | Full HLD in flow-first form: one incremental diagram per functional requirement, deep dives that mutate the design, final design with six rehearsal flows, then nitty-gritty |
| [`diagrams.md`](diagrams.md) | The D1 to D12 diagram set |
| [`edge-cases.md`](edge-cases.md) | Every "what if" with a 60-second answer and a confidence box |
| [`deep-dives/query-planning-and-adaptive-execution.md`](deep-dives/query-planning-and-adaptive-execution.md) | Parse, analyze, rule and cost-based optimization, stages, AQE, runtime filters |
| [`deep-dives/vectorized-execution-and-scan-path.md`](deep-dives/vectorized-execution-and-scan-path.md) | Photon's vectorized model, Parquet read path, pruning, disk cache, memory reservations and spill |
| [`deep-dives/shuffle-and-joins.md`](deep-dives/shuffle-and-joins.md) | Join strategies, sort-based shuffle files, the M x R block problem, skew splitting, push-merge and remote shuffle |
| [`deep-dives/fault-tolerance-and-stragglers.md`](deep-dives/fault-tolerance-and-stragglers.md) | Task and stage retry, lineage, FetchFailed, speculation, decommission, driver loss, spooled exchanges |
| [`deep-dives/multi-tenant-isolation-and-admission.md`](deep-dives/multi-tenant-isolation-and-admission.md) | Warehouses, queueing, cost-predicting admission, fair slot scheduling, memory limits, security isolation |
| [`deep-dives/elasticity-warm-pools-and-cost.md`](deep-dives/elasticity-warm-pools-and-cost.md) | Warm pool math, autoscaling on queue time, auto-stop, metering and cost attribution, guardrails |
| [`research/`](research/) | Raw web research notes with source links. Input to the files above, not study material |
| `query-engine.excalidraw` | My drawing. Missing until I draw it |
