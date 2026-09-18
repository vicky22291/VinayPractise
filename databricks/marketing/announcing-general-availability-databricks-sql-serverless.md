# Announcing the General Availability of Databricks SQL Serverless !

*Instant, elastic warehouses now generally available on Azure and AWS*

- Source: https://www.databricks.com/blog/announcing-general-availability-databricks-sql-serverless
- Published: 2023-05-18
- Authors: Cyrielle Simeone, Shant Hovsepian, Gaurav Saraf
- Categories: platform, announcements, data-warehousing
- Images: 1 total, 0 extracted as architecture

Today, we are thrilled to announce that serverless compute for [Databricks SQL](https://www.databricks.com/product/sql-analytics) is Generally Available on AWS and Azure! Databricks SQL (DB SQL) Serverless provides the best performance with instant and elastic compute, lowers costs, and enables you to focus on delivering the most value to your business rather than managing infrastructure. With GA, you can expect the highest level of stability, support and enterprise-readiness from Databricks for mission-critical workloads on the Databricks Lakehouse Platform.

In this blog post, we will review the benefits of DB SQL Serverless and discuss some of the latest features released to provide you with world-class data warehousing performance.

## Databricks SQL momentum, and the shift to serverless

Over the last couple of years, we've seen tremendous growth and adoption of Databricks SQL - our data warehouse purpose-built for the Lakehouse. DB SQL is helping leading companies like [Akamai](https://www.databricks.com/customers/akamai), [T-Mobile](https://www.databricks.com/customers/t-mobile), and [CRED](https://www.databricks.com/customers/cred/databricks-sql) drive innovation by powering modern analytics use cases around the globe - at any scale. From startups to enterprises, thousands of companies are using Databricks SQL to power the next generation of self-service analytics and data applications, and serverless makes their experience even better with instant, elastic compute, lower infrastructure costs, and no management overhead.

> "Our analysts rely on Databricks SQL to derive business intelligence from over 2PB of data. With serverless, we get reliability, scalability, and efficiency - all by simply checking a box. Our teams no longer have to worry about performance, sizing and administering infrastructure. With the push-button simplicity of Databricks SQL Serverless, we have 30% better performance and have reduced costs by 20% on average." —Allard de Boer, Global Director of Analytics, Adevinta

It's been an incredible journey so far. As we always thrive to provide you with the best experiences, we built Databricks SQL serverless so you can benefit from:

- **Instant and elastic compute:** Serverless compute brings a truly elastic environment that's instantly available and scales with your needs. You'll benefit from simple usage-based pricing without worrying about idle time charges. Imagine no longer needing to wait for infrastructure resources to become available to run queries or overprovisioning resources to handle spikes in usage. DB SQL Serverless dynamically grows and shrinks resources to handle whatever workload you throw at it.
- **Lower infrastructure costs:** Under the covers, the serverless compute platform uses machine learning algorithms to provision and scale compute resources right when you need them. This enables substantial cost savings without the need to shut down clusters manually.
- **Eliminate management overhead:** Serverless transforms DB SQL into a fully managed service, eliminating the burden of capacity management, patching, upgrading, and performance optimization of the cluster. You only need to focus on your data and the insights it holds. Additionally, the simplified pricing model means there's only one bill to track and only one place to check costs.

> "We rely on Databricks SQL to power the business intelligence tools used by our analysts. Databricks SQL Serverless allows us to use the power of Databricks SQL while being much more efficient with our infrastructure. Checking the serverless box resulted in a 3x reduction in our infrastructure costs, which is why we're integrating Databricks SQL Serverless into more and more data pipelines." —R Tyler Croy, Director of Platform Engineering, Scribd

## Continuously improving performance and lowering costs with serverless

In addition to all the infrastructure improvements mentioned above, DB SQL Serverless is also packed with performance and cost optimizations features for all analytics use cases:

- ***Predictive I/O:*** Machine Learning powered optimizations to [make your point lookups faster and cheaper](https://www.databricks.com/blog/announcing-general-availability-predictive-io-reads.html), and to [make data updates/deletes blazing fast](https://www.databricks.com/blog/announcing-public-preview-predictive-io-updates).
- ***[Results caching](https://www.databricks.com/blog/understanding-caching-databricks-sql-ui-result-and-disk-caches):*** Improves query result caching by using a two-tier system with a local cache and a persistent remote cache across all serverless warehouses in a workspace.

## Getting started

Did you know that you can benefit today from a price reduction on Databricks SQL Serverless? Visit [our pricing page](https://www.databricks.com/product/pricing/databricks-sql) for more information and watch our latest virtual event [The Case for Moving to the Lakehouse](https://www.databricks.com/resources/webinar/goodbye-data-warehouse-hello-lakehouse) co-presented with Fivetran and dbt to learn more about our Data Warehouse offering, including Databricks SQL Serverless and Unity Catalog.

If you are already a Databricks customer, simply follow the guide to get started on [AWS](https://docs.databricks.com/sql/admin/serverless.html) or [Azure](https://learn.microsoft.com/en-us/azure/databricks/sql/admin/serverless). As a reminder, Databricks SQL Serverless is now supported on AWS in the [following regions](https://docs.databricks.com/resources/supported-regions.html#regions-aws): and on Azure in the [following regions](https://learn.microsoft.com/en-us/azure/databricks/resources/supported-regions), and more coming soon.

Creating a serverless SQL warehouse in Databricks SQL

Join us at [Data + AI Summit 2023](https://www.databricks.com/dataaisummit/) to learn more.
