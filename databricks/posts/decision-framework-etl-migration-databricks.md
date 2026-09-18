# A Decision Framework for ETL Migration to Databricks

*How to choose between Spark Declarative Pipelines, Lakehouse or PySpark, and when to combine them*

- Source: https://www.databricks.com/blog/decision-framework-etl-migration-databricks
- Published: 2026-06-26
- Authors: Rafael Aielo
- Categories: engineering, data-warehousing, industries
- Images: 0 total, 0 extracted as architecture

**Key takeaways**

- Three paths, not one: Spark Declarative Pipelines (SDP), Lakeshouse and PySpark or Spark SQL notebooks address different migration scenarios. Most organizations end up using a combination.
- Phase for outcomes: A four-stage approach (assess, quick wins, modernize, optimize) lets you retire legacy systems incrementally instead of betting on a big-bang cutover.
- Let the tooling do the heavy lifting: Lakebridge, partner transpilers, and AI-assisted code conversion automate much of the mechanical translation so your team can focus on validation and optimization.

Your team has hundreds of stored procedures, a couple of schedulers, permissions scattered across roles and schemas, and a cloud data warehouse renewal deadline coming up. Nobody agrees on what to move first. Some want to rewrite everything in PySpark. Others want to move SQL as-is and call it done. Lost in the conversation: the metadata, lineage, and permissions that move with the code, plus the opportunity to consolidate them on the way.

Neither extreme works. The teams that succeed at data warehouse migration look at each workload individually and pick the right tool for the job. This post suggests a decision framework for selection: when to use Lakehouse (Databricks SQL), Spark Declarative Pipelines, or PySpark, and how to phase the work so you ship results instead of stalling on a plan.

## Three paths, one migration

On Databricks, you can migrate ETL pipelines in three primary ways, often used together.

#### **Spark Declarative Pipelines (**[**SDP**](https://www.databricks.com/product/data-engineering/spark-declarative-pipelines)**)** 

Which is part of Lakeflow, take a different approach. You declare what your pipeline should produce and the engine handles execution order, retries, and scaling. You get built-in data quality constraints, automatic dependency resolution, and unified batch-plus-streaming in the same definition.

Under the hood, [Enzyme](https://www.databricks.com/blog/2022/06/29/delta-live-tables-announces-new-capabilities-and-performance-optimizations.html) decides when to incrementally update versus fully recompute derived tables. Autoscaling adjusts capacity to data volume changes without manual tuning. Companies like [Block](https://www.databricks.com/customers/block/lakeflow-declarative-pipelines) lean on this declarative model to simplify pipeline orchestration as usage grows.

#### **Lakehouse (Databricks SQL) **

This is the most direct path for SQL-heavy teams. It covers a spectrum from simple to complex. It runs on SQL warehouses, which are Photon-accelerated by default and fully compatible with ANSI and Spark SQL (%sql). Choose Serverless for variable or unpredictable workloads (fast startup, scales to zero, pay per second). Choose Classic for steady workloads or when you need specific networking or cost controls.

A straightforward SQL task:

When the logic requires control-of-flow (conditionals), loops, variables, error handling, or parameter-driven execution, stored procedures give you that procedural layer. They are governed via Unity Catalog and can be called from Workflows with parameters.

The rule of thumb: if your legacy code is a single SQL statement, migrate it as a SQL task. If it has procedural logic (variables, loops, parameters, error handling), wrap it in a stored procedure, governed by Unity Catalog and callable from Workflows. Do not wrap simple SQL in a procedure just because the original system required it.

#### **PySpark and Spark SQL notebooks** 

Which gives you full control. They run on job clusters and handle the workloads that don't fit a SQL Warehouse or a declarative pipeline.

Reach for **PySpark** when the workload needs complex business logic, ML feature engineering, API integrations, or custom validation. The example below scores transactions with a model registered in Unity Catalog:

Reach for **Spark SQL in a notebook** when the language is still SQL but the workload may exceed SQL Warehouse fit: very large tables, heavy shuffles, long-running batch ETL where you want explicit control over partitioning, broadcast joins, or caching.

Enable [**Photon**](https://www.databricks.com/product/photon) on the job cluster for compute-bound SQL or DataFrame work: large joins, aggregations, window functions, scans over big columnar tables. Photon is a native, vectorized engine that accelerates these patterns without code changes, including Pandas UDFs (Arrow-based). Skip Photon when row-wise Python UDFs dominate, datasets are small, or the job is pure I/O.

Notebooks also fit well in hybrid pipelines: ingestion in SDP, enrichment in a notebook task.

## Decision matrix

The table below is a starting point for team conversations, not a hard rule.

| **Criteria** | **Spark Declarative Pipelines** | **Lakehouse (tasks and stored procs)** | **PySpark + Spark SQL notebooks** |
|---|---|---|---|
| Team profile | Data engineers and SQL teams building managed pipelines | SQL-heavy, DBAs, DW engineers | Python/Spark developers, ML engineers |
| Type of logic | Change Data Capture, bronze ingestion, batch updates | SQL ETL: simple tasks for single statements, stored procs for procedural logic | Complex logic, custom UDFs, ML prep |
| SQL migration speed | Medium: pipeline redesign, but SQL reuse and faster performance | High for SQL ANSI-like workloads | Variable: may require significant refactoring |
| Pipeline orchestration | Handled by pipelines with automatic dependency management | Workflows with SQL tasks or CALL procedure | Workflows with notebook tasks |
| Batch vs. streaming | Unified batch and streaming | Primarily batch | Batch and streaming via Structured Streaming |
| Data quality | Declarative constraints | Manual SQL checks | Custom validation in code |

## Quick decision grid

Find your team in the column and your workload complexity in the row. The cell may suggest where to start.

| **Workload complexity** | **SQL-first team** | **Hybrid team** | **Code-first team** |
|---|---|---|---|
| **Low** (batch loads, aggregations, MERGE) | SDP or SQL tasks in Workflows | SDP or SQL tasks in Workflows | SDP or PySpark |
| **Medium**(multi-step pipelines, CDC, data quality) | SDP or stored procedures | SDP | SDP or PySpark |
| **High** (ML prep, Custom UDFs, APIs, dense business logic) | SDP + PySpark assist | PySpark + SDP for ingestion | PySpark |

## Four phases instead of big-bang

Rather than deciding "which approach for everything," decide "what to do next" in each phase.

**Phase 1 — Assess.** Collect metrics from your legacy data warehouse: CPU time, runtime, frequency, source and target tables. Classify workloads by complexity. Use migration tools, when possible, to build an inventory scored by value versus difficulty. Where you find this data depends on the source. On *Teradata*, query [*DBC.QryLog*](https://docs.teradata.com/r/Enterprise_IntelliFlex_VMware/Data-Dictionary/Views-Reference/QryLogV). On *SQL Server*, use [*sys.dm_exec_query_stats*](https://learn.microsoft.com/en-us/sql/relational-databases/system-dynamic-management-views/sys-dm-exec-query-stats-transact-sql?view=sql-server-ver17)*. On Oracle, *[*AWR reports*](https://docs.oracle.com/en-us/iaas/performance-hub/doc/awr-report-ui.html)*. On Snowflake, *[*QUERY_HISTORY*](https://docs.snowflake.com/en/sql-reference/functions/query_history). The specifics may vary. If you have an integration tool in place, you can leverage its metadata to identify relationships between tables, or rely on an LLM to help build this lineage. The output is a map, not a rewrite plan. The goal remains the same: rank workloads by resource consumption and dependency level so you know where to start. Done well, this assessment takes days using migration tools, not weeks of manual scripting.

**Phase 2 — Quick wins.** Pick workloads that combine low migration risk with use cases with high business visibility. That might mean starting with heavy SQL jobs that are easy to convert, or with reporting pipelines that put the new platform in front of stakeholders early. Simple statements will become SQL tasks in Workflows. Procedural logic becomes stored procedures. Use transpilers and AI-assisted conversion for the initial translation. Run both systems side by side and compare row counts, checksums, sample records. The point is to build confidence, both technical and organizational.

[Walgreens](https://www.databricks.com/customers/walgreens), for example, retired on-premises Teradata in a phased migration and now processes around 40,000 data events per second on the lakehouse, powering supply-chain optimization across nearly 9,000 stores.

**Phase 3 — Modernize.** Now redesign the pipelines worth modernizing. Candidates: flows where data quality constraints and lineage reduce manual checks, batch jobs that benefit from streaming tables and CDC, pipelines where materialized views reduce complexity, and the metadata, permissions, and audit that previously lived in separate tools, now consolidated under Unity Catalog. A common pattern is keeping the legacy procedure as a fallback while the new pipeline runs in parallel until it passes validation. Modernized pipelines often cut batch windows from hours to minutes and remove the need for separate DQ tooling.

**Phase 4 — Optimize.** Consolidate redundant ETL pipelines that only existed to work around old DW limitations. Move complex hot spots to PySpark when it simplifies logic. Revisit batch vs. streaming boundaries now that you have a unified engine. This is where the migration pays off: the legacy platform is off, redundant pipelines are gone, and the architecture runs on one system instead of two.

## Where migration tools and AI fit

Migration tooling automates the mechanical work but does not replace architecture decisions. Three typical roles:

- **Profiling and assessment.** Discover stored procedures, SQL scripts, and ETL jobs. Map dependencies. Lakebridge ships an [Analyzer](https://databrickslabs.github.io/lakebridge/docs/assessment/analyzer/) component that scans legacy data warehouse platforms and builds an inventory of objects, usage patterns, and complexity.
- **Code conversion.** Translate SQL and ETL from Teradata, Oracle, SQL Server, DataStage, Informatica, and SSIS into Lakehouse or declarative pipelines. Lakebridge's Converter handles stored procedures and ETL flows, with [public guidance](https://www.databricks.com/blog/introducing-lakebridge-free-open-data-migration-databricks-sql) citing up to 80% automation and roughly 2x faster project timelines.
- **Validation.** Compare results across systems with automated checks on schemas, row counts, and aggregates. Lakebridge includes a *validator*. The Databricks migration methodology treats [reconciliation](https://databrickslabs.github.io/lakebridge/docs/overview/#post-migration-reconciliation) as a first-class phase, not an afterthought.

A pragmatic approach: let tooling cover 60-80% of the initial conversion and reserve engineer time for the patterns you actually want to modernize. This avoids a one-to-one port of technical debt.

## What gets removed

Successful migrations actively retire systems, not just convert code: standalone scheduler servers, custom DQ frameworks, separate lineage and metadata tools, vendor-specific stored-procedure compilers, and hand-rolled validation harnesses. The migration is not done until those systems are off and the bills stop.

## Three anti-patterns that stall migrations

- **Picking one path for everything** without considering team skills, risk profile, and workload type. The SQL-only team misses modernization opportunities. The PySpark-only team rewrites simple SQL for no reason.
- **Measuring only "percent migrated"** while ignoring parallel-run duration, validation time, and actual retirement of legacy systems. Fifty percent migrated means nothing if the old data warehouse platform is still running at full cost.
- **Recreating old schedulers and intermediate layers** on the lakehouse instead of using workflows and declarative pipelines. Migration is a chance to simplify pipeline orchestration. Take it.

If SQL ETL stays fragmented across engines, layers, and tools, the platform stays fragmented, even if the data sits in open formats.

There is no single right way to migrate data pipelines. Lakehouse gets you there fast: simple tasks for simple logic, stored procedures when you need procedural control. SDP gives you modern ETL pipelines with quality, lineage, and real-time streaming performance built in. Notebooks handle the rest, whether you reach for PySpark or Spark SQL. Phase the work, start with quick wins, and use every accelerator you can.

Explore the [Databricks Migration Guide](https://www.databricks.com/solutions/migration) for technical walkthroughs, or try it yourself with a [Databricks Free Edition](https://www.databricks.com/signup/free-edition?provider=DB_FREE_TIER&dbx_source=www&itm_data=dbx-web&l=en-EN).
