# Navigating a Synapse Migration to Databricks

*A practical guide to moving from Synapse's Dedicated SQL, Serverless, and Spark pools to one unified Databricks Lakehouse governed by Unity Catalog*

- Source: https://www.databricks.com/blog/navigating-synapse-migration-databricks
- Published: 2026-07-08
- Authors: Olga Romanova, Johannes Oehler
- Categories: engineering, data-warehousing
- Images: 3 total, 0 extracted as architecture

**Key takeaways**

- Synapse customers are stuck stitching together Dedicated SQL, Serverless SQL, Spark Pools, and ADF — paying for duplicated governance, extra tooling, and operational overhead on a warehouse that was never built for ML, streaming, and AI.
- The blog is a practical, field-tested playbook for migrating from Azure Synapse (Dedicated SQL Pools, Serverless SQL, and Spark Pools) to a unified Databricks Lakehouse, structured as a phased program.
- The payoff: streamlined Synapse migration and practical field engineering tips for simpler architecture, better performance and lower costs.

*Azure Synapse has served as a reliable foundation for SQL analytics at scale, and teams that built on it made a sensible choice at the time. However, a platform primarily designed around a data warehouse isn't built for the full range of what data teams are now expected to deliver. Filling those gaps usually involves adding more services, integrations and operational overhead, which builds up over time. *

*Migrating to Databricks is one way to address this issue. In this blog we address how to approach Synapse migration and what to keep in mind while executing it.*

## What a Synapse Migration Unlocks

Across Synapse migration engagements we see with our customers, three business drivers come up consistently:

1. **Unified data estate.** As data platforms grow, the number of services involved increases too. For example, Synapse Analytics pools handle one set of workloads, Spark pools handle another, and serverless SQL provides ad hoc access. Azure Data Factory often sits alongside these to orchestrate everything. Many organisations also have legacy SSIS workloads that still need to be supported. None of these components are problematic in isolation. However, the challenge arises when additional services are introduced, as this adds another layer of governance, monitoring, permissions management and operational overhead.
Databricks addresses this issue by unifying data engineering, analytics, machine learning and governance on a single platform. Rather than moving between services with different operating models, teams can work against the same underlying architecture and governance framework. The result is reduced complexity, fewer integration points, and a platform that's easier to operate at scale.
2. **Future readiness.** Focus of modern data teams now is shifted towards supporting machine learning models, real-time data pipelines, and AI-powered applications. All of these workloads depend on the same underlying data. The challenge is that traditional, warehouse-centric architectures were not designed for this level of convergence and were primarily targeting BI needs. As requirements expand, organisations often find themselves adding more services and specialised tools to fill capability gaps.
Databricks is built for this convergence, unifying data, analytics, and AI on a single platform. With Unity Catalog providing consistent governance across data, notebooks, and AI/ML assets, and Unity AI Gateway extending those controls to models, agents, and AI applications, organizations can adopt new AI workloads without adding new governance silos.
3. **Operational efficiency.** While most migration business cases begin with licensing costs, that's rarely where the biggest savings come from. The larger impact often comes from reducing the number of systems that teams need to operate and support. Fewer services means fewer integrations, fewer handoffs between tools, and fewer potential issues.

Synapse < > Databricks: Capabilities Overview

Organisations that have already made the move are seeing tangible results. For example, [Casey's](https://www.databricks.com/customers/casey/lakehouse), the third-largest convenience store chain in the United States, migrated its analytics environment from Synapse to Databricks Lakehouse (formerly Databricks SQL), reducing operational data delivery times from eight hours to four. As another example, [Italgas](https://www.databricks.com/customers/italgas/ai-bi) simplified its architecture by removing both Synapse and Azure Analysis Services. The company reported a 73% reduction in workload costs while serving both Power BI and AI-driven analytics directly from Databricks. 

While the specifics vary from organisation to organisation, the pattern remains consistent: simpler architectures, faster data delivery and a platform better aligned to the demands placed on modern data teams.

## Understanding What You Are Actually Migrating

One thing that often catches teams off guard early in a Synapse migration is the scope of what they are moving. Although Azure Synapse is often considered a single platform, in practice it comprises a variety of distinct services operating under one brand, each of those may require different migration strategies and has a different level of complexity.

Most migrations spend the majority of their effort on Dedicated SQL Pools, where business logic, stored procedures, distribution strategies, indexing decisions, and performance optimisations have accumulated over years. But the complexity rarely stops at the SQL. The same migration usually has to account for orchestration (Azure Data Factory and Synapse Pipelines), permissions and governance (SQL permissions plus Microsoft Purview, with lineage often stitched together manually), and BI and third-party connectivity (semantic models, reports, and downstream tools wired directly into Synapse endpoints). This is the part of the estate that demands the most redesign, testing, and validation - and the part most likely to be underestimated.

Serverless SQL Pools are generally simpler, because they primarily provide a query layer over files in a data lake. Migration here is mostly about re-establishing views, external tables, and access patterns rather than redesigning complex workloads. Spark Pools are the simplest component to move, since Synapse Spark and Databricks are both built on Apache Spark and notebooks can often migrate with relatively few changes.

The important point is that these components move at different speeds, involve different stakeholders, and present different risks. Organisations that approach the migration as a single workstream with a single timeline often underestimate both effort and complexity. That's where schedules start to slip and migration programmes begin to expand beyond their original scope. To migrate successfully, teams should structure the migration journey.

## How to Structure the Migration

A Synapse-to-Databricks migration is not a single workstream. You're moving three different compute models, consolidating governance, modernising orchestration, and reworking years of accumulated T-SQL logic. The teams that handle this well treat it as a structured programme rather than a technical project with the phased approach.

**Discovery.** Every migration starts with understanding what is actually running. [Lakebridge Profiler](https://databrickslabs.github.io/lakebridge/docs/assessment/profiler/) scans the Synapse estate and collects metadata on configuration, resource utilisation, query patterns, and performance baselines. Output is used to build a TCO case.

**Assessment.** Once the inventory is in place, the next step is understanding complexity. [Lakebridge Analyzer](https://databrickslabs.github.io/lakebridge/docs/assessment/analyzer/) evaluates the T-SQL codebase, classifying every object by complexity, flagging unsupported constructs, and mapping dependencies. Output can be used to assess the migration timeline and associated efforts as well as defining the priority of assets migrations. Start with the lower- and medium-complexity workloads as low hanging fruits, and plan effort afterwards for the most critical use cases.

**Design.** With visibility into the estate, attention shifts to the architecture and design. The first is approach: lift-and-shift, modernise, or hybrid. For most Synapse migrations, hybrid is the right answer. Automated tooling handles the bulk of code conversion to get off Synapse on schedule, while modernisation happens incrementally once workloads are running on Databricks. 

The second decision is sequencing. A [BI-first approach](https://www.databricks.com/blog/navigating-your-migration-databricks-architectures-and-strategic-approaches) tends to build momentum faster than starting with ETL. Using Lakehouse Federation, you can expose Synapse data through Unity Catalog before the underlying pipelines have moved - and a practical way to start is to land the business-facing, augmented data (your data marts) on Databricks first, then put it directly in front of business users with Genie for natural-language analytics. Business stakeholders see progress and value early, while engineering teams modernise the more complex ETL underneath. Read our [blog post](https://www.databricks.com/blog/warehouse-lakehouse-migration-approaches-databricks) to define the right migration approach for you.

**Pilot.** Before scaling, the migration strategy needs to be validated end-to-end against a real workload. Pick one lighthouse use case, migrate it from ingestion through to consumption, and cut it over to production. A pilot validates the architecture, governance model, testing procedures, and tooling against real-world conditions, and produces reusable assets for the waves that follow.

**Migration in waves.** For scale phase, migration in waves is recommended. Each wave is designed to deliver a visible business win and establishes the feedback loop with end users. 

Execution typically runs as four parallel workstreams: ingestion (moving ADF and Synapse Pipeline workloads to Lakeflow Connect), transformation (migrating T-SQL procedures and business logic to Databricks), orchestration (moving schedules and dependencies to Databricks Workflows), and consumption (repointing BI tools and semantic models to Databricks SQL Warehouses). Running them in parallel lets teams deliver value early and retire Synapse on a predictable timeline.

Databricks supports Synapse migrations from multiple angles: advisory and delivery from our [Forward Deployed Engineering](https://www.databricks.com/blog/forward-deployed-engineering-delivering-business-outcomes-ai) team, certified [Brickbuilder partners](https://www.databricks.com/blog/2022/03/17/brickbuilder-solutions-partner-developed-industry-solutions-for-the-lakehouse.html), and accelerators like Lakebridge that automate the heavy lifting. The goal is not just to complete the migration but to [build the skills](https://www.databricks.com/learn/training/home) and operating model the team needs to sustain the platform long after the project ends.

## Data Ingestion

Before converting SQL code, data must first be ingested into the lakehouse. Databricks provides several options depending on the source systems and operational requirements.

For many common enterprise sources, [Lakeflow Connect](https://learn.microsoft.com/en-us/azure/databricks/ingestion/overview) offers a managed ingestion experience with built-in connectors and automated pipeline management. At the same time, Databricks is built on open storage formats, allowing organizations to use a wide range of third-party ingestion tools. Solutions such as Fivetran, Airbyte, and other ETL/ELT platforms can ingest data directly into Delta Lake, enabling customers to integrate with existing data integration ecosystems rather than being tied to a single ingestion framework.

## Code Conversion in Practice

With the data available in the lakehouse, the migration effort shifts to code conversion, which is typically the most complex phase of the migration. While automated tooling handles the majority of the translation, typically around 80-90%, the remaining effort is spent refining procedural logic and resolving patterns that cannot be translated automatically.

Below are some differences to watch out for in Synapse and Databricks syntax.

### Removing Physical Directives

The most common conversion pattern is the removal of physical optimization directives. Dedicated SQL Pools rely heavily on constructs such as HASH distribution, ROUND_ROBIN distribution, REPLICATE distribution, and clustered columnstore indexes. These are fundamental to Synapse performance tuning but have no direct equivalent in Databricks, so they are typically omitted during migration.

Instead, Databricks relies on storage optimization and Liquid Clustering to improve query performance. The former is handled automatically through [Predictive Optimization](https://docs.databricks.com/aws/en/optimizations/predictive-optimization), which continuously performs maintenance operations such as file compaction, statistics collection, and VACUUM for Delta tables. The latter is provided by [Liquid Clustering](https://docs.databricks.com/aws/en/tables/clustering), which organizes data within Delta tables using one or more clustering columns to improve query performance. Selecting the optimal clustering columns, however, depends on understanding how data is queried, a task that is often difficult in practice and frequently changes as workloads evolve. To reduce this operational burden, Databricks introduced CLUSTER BY AUTO, which automatically identifies and continuously refines clustering columns based on observed query access patterns. Together, these capabilities significantly reduce the amount of manual physical tuning required compared to Dedicated SQL Pools.

Physical design decisions that consumed significant engineering effort in Synapse are simply dropped. The platform handles what was previously manual.

### Function Remapping

Most commonly used T-SQL functions have direct Databricks equivalents, and Lakebridge handles the vast majority of mappings automatically.

| T-SQL | Databricks SQL |
|---|---|
| GETDATE() | CURRENT_TIMESTAMP() |
| ISNULL(a, b) | COALESCE(a, b) or IFNULL(a, b) |
| LEN(s) | LENGTH(s) |
| CHARINDEX(sub, str) | LOCATE(sub, str) |
| SELECT TOP 10 | SELECT ... LIMIT 10 |
| CONVERT(INT, col) | CAST(col AS INT) |

The more common source of issues is not the function mappings themselves but behavioral differences that affect results in subtle ways. String comparison is a good example. Synapse Dedicated SQL Pools typically operate with case-insensitive collations, while Databricks SQL is case-sensitive by default. Logic that implicitly relies on case-insensitive matching may return different results after migration. Where needed, comparisons should be made explicit using LOWER() or UPPER() on both sides. Syntax conversion is usually straightforward; semantic differences require more care.

### Stored Procedures: Migrate First, Optimize Second

With native stored procedure support in Databricks, most Synapse procedures can migrate with their overall structure intact. Parameters, variables, conditional logic, and DML operations are all supported.

The procedure itself is rarely the problem. The complexity lives inside it: cursors, row-by-row processing, dynamic SQL, and Synapse-specific performance optimizations. Those patterns require judgment, not just translation.

### SCD Type 2: Preserving History with Delta Lake

Slowly Changing Dimensions are one of the areas where Synapse implementations vary the most. Many organizations have accumulated custom stored procedures and merge logic over years. The migration goal is not to reproduce that implementation exactly but to preserve the business requirement: maintaining historical versions of dimension records while keeping the current state queryable.

A common Databricks approach uses two steps. First, expire the records that have changed. Then insert the new versions.

Delta Lake's ACID transactions make this pattern safe even when multiple operations are involved.

### Error Handling

Many Synapse stored procedures rely on TRY...CATCH blocks to capture failures or write audit records. Databricks SQL provides native equivalents through condition handlers, so most existing patterns can stay SQL-based.

Simple scenarios like audit logging and controlled failures typically translate directly. More complex workflows may need additional design, particularly where downstream coordination through Databricks Workflows is involved.

## What Field Experience Teaches

A few lessons come up consistently across Synapse migrations, regardless of organization size or estate complexity.

**Start with assessment, not conversion.** Run Lakebridge Profiler and Analyzer before writing a single line of converted code. Get clear on actual usage, scope, complexity, and dependencies - and use that data to cut scope where you can.

**Automate aggressively. **Lakebridge handles 80–90% of code conversion. Concentrate engineering time on the 10–20% that needs human judgment - cursors, dynamic SQL, complex error handling.

**Never underestimate the validation.** In practice, validation often consumes more effort than the migration itself. The most effective approach is to run reconciliation after every migration wave, comparing row counts, aggregations, hash-based record comparisons, and tolerance-based checks for values where exact equality is not appropriate. Lakebridge Reconcile supports this across all these dimensions. For business-critical workloads, running both environments in parallel before final cutover lets teams compare outputs side-by-side while users continue working with familiar reports.

**Steer from Synapse-shaped thinking.** A good example is table design. Teams frequently attempt to map Synapse HASH distribution keys directly to Delta Lake partition columns. In most cases, this introduces unnecessary complexity and poor performance characteristics. High-cardinality values such as customer IDs or order IDs are rarely suitable partition keys and are often better handled through liquid clustering and Databricks' automated optimisation capabilities like predictive maintenance.

**Don't recreate what the platform now handles.** Migrations create an opportunity to simplify architectures rather than reproduce them exactly. Delta Lake, automated optimisation, and modern lakehouse patterns eliminate many of the manual tuning techniques that were necessary in traditional warehouse environments. Carrying every historical optimisation decision into Databricks often preserves old constraints without preserving the reasons those constraints existed.

**Prepare operational readiness.** Delta tables naturally accumulate small files as incremental workloads run over time. Without compaction and maintenance processes, performance can gradually degrade. Teams coming from traditional data warehouse platforms are often surprised that storage optimisation becomes part of the ongoing operating model. It's not difficult to manage, but it does need to be planned from the beginning.

**Plan for change management. **Most Synapse teams are new to Databricks, and underinvesting in enablement is one of the most common reasons projects miss adoption targets. Work the enablement plan as seriously as the technical plan.

**Avoid early decommissioning of Synapse.** Most successful migrations keep the legacy environment available for a period after production workloads have moved. Compute can be paused to minimise costs while preserving a rollback option if unexpected issues emerge. More importantly, maintaining that safety net gives business stakeholders confidence while the new platform proves itself under real-world usage.

Migrating from Synapse to Databricks is rarely just a technology project. At its core, it involves simplifying a platform that has become increasingly complex over time, while establishing a foundation that can support the next generation of analytics, AI and data products. While the technical work is important, the organisations that benefit most from these migrations are those that use the opportunity to simplify their architecture, eliminate unnecessary complexity and modernise their operating practices simultaneously. The greater benefit is ending up with a data platform that's simpler to operate, easier to extend and better aligned with the organisation's future direction.

## What to do next

If you're at the start of a Synapse migration:

- Run [Lakebridge Profiler and Analyzer](https://github.com/databrickslabs/lakebridge) on your environment. Get the data before you scope the work.
- Read the [Migration Strategy: Lessons Learned](https://www.databricks.com/blog/databricks-migration-strategy-lessons-learned) blog and the [Transforming Legacy Data Warehouses eBook](https://www.databricks.com/resources/ebook/migrate-your-legacy-data-warehouse-databricks).
- If you want hands-on help, [Databricks FDE Team](https://www.databricks.com/professional-services) and [certified migration partners](https://www.databricks.com/solutions/migration/data-warehouse) deliver Synapse migrations end-to-end.
