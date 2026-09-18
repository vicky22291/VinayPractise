# Announcing SQL Server connector from Lakeflow Connect, now Generally Available

*From database to insights, Databricks unlocks SQL Server data to help drive business results*

- Source: https://www.databricks.com/blog/announcing-sql-server-connector-lakeflow-connect-now-generally-available
- Published: 2025-09-25
- Authors: Elise Georis, Peter Pogorski, Giselle Goicochea
- Categories: platform, announcements, product, data-engineering, platform-and-products-and-announcements
- Images: 1 total, 0 extracted as architecture

**Key takeaways**

- The SQL Server connector from Lakeflow Connect is now Generally Available to help unlock insights from your data, featuring change tracking, CDC, and the ability to track historical changes with SCD Type 2.
- Lakeflow Connect helps large-scale customers like Cirrus Aircraft Limited, Ubisoft, and the Australian Red Cross to power SQL Server use cases across aviation, gaming, and healthcare.
- Simplify data ingestion with flexible, managed connectors for applications, databases, cloud storage, message buses, and more.

We’re excited to announce the **General Availability of the SQL Server connector from Lakeflow Connect**. This fully managed connector is designed for reliable, production-grade ingestion with built-in Change Data Capture (CDC) and Change Tracking (CT). By removing the need for custom pipelines or complex tools, it simplifies ingestion, ensures data freshness, and reduces operational overhead to accelerate insights. Also, for [BI-first migrations](https://www.databricks.com/blog/navigating-your-migration-databricks-architectures-and-strategic-approaches#section-1), built-in CDC support keeps analytics workloads continuously up to date, making it easier to bring SQL Server data into the lakehouse with the performance, security, and scalability that enterprises require.

Microsoft SQL Server powers some of the world’s most business-critical applications, yet its data is often locked in a system purpose-built for transactions, not analytics. As organizations move these workloads to the lakehouse, reliable ingestion is critical. Traditional ingestion pipelines are complex to build, costly to maintain, and can overload production systems, while multiple instances and hybrid on-premises and cloud environments lead to patchwork solutions that are hard to govern. The [SQL Server connector](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/sql-server-source-setup) from [Lakeflow Connect](https://www.databricks.com/product/data-engineering/lakeflow-connect) solves these challenges with a fully managed, streamlined and governed solution that unlocks SQL Server data for advanced analytics and AI.

## Built-in data ingestion support for many SQL Server database environments

The **SQL Server connector** makes it easy to ingest data from various SQL Server environments into the lakehouse, where it can be used for analytics and business intelligence across the organization, including: 

- Azure SQL
- Azure SQL Managed Instance
- AWS RDS for SQL Server
- SQL Server on GCP
- On-premises SQL Server deployments  

The connector is easy to set up with a point-and-click UI or simple API and integrates seamlessly with your existing workflows and deep platform integration with Databricks. For example, you can align with your CI/CD practices via [Declarative Automation Bundles](https://docs.databricks.com/aws/en/dev-tools/bundles/) or the [Databricks Terraform provider](https://docs.databricks.com/aws/en/dev-tools/terraform/).

It’s also built for efficiency. The connector supports both CDC and CT for incremental ingestion instead of needing to run full refreshes. By capturing only new or updated records, customers can keep their lakehouse continuously up-to-date to deliver valuable business insights, accelerate decision-making, and reduce costs.

For organizations that need to manage data changes over time—like customer details, product attributes, or organizational structures—Lakeflow Connect also provides out-of-the-box support for tracking historical changes with Slowly Changing Dimensions (SCD) Type 2, reducing the complexity with a critical feature to track historical changes alongside current values. 

**Demo: Learn how to use Lakeflow Connect for SQL Server to analyze customer purchase behavior.**

## Enterprise customers drive impact with Lakeflow Connect

Since we launched a year ago, more than 2,000 customers have used Lakeflow Connect to ingest their most business-critical data to drive positive results.

For example, **Cirrus Aircraft Limited**, founded in 1984, designs, develops, manufactures, and sells premium aircraft around the world. An early adopter of the SQL Server connector, they needed to move data off multiple hybrid SQL Server environments into their lakehouse to deliver more valuable data back to their teams. With its simple setup and efficient incremental ingestion, the connector enabled Cirrus to shift from pipeline integration and maintenance to strategic initiatives that moved the needle for their business.

> "Lakeflow Connect’s SQL Server connector is a game changer. We migrated hundreds of tables from hybrid environments in days-sometimes hours-instead of months. The real win: our developers can focus more time delivering higher-value data and insights to the business."—Nick Patullo, Data Engineer Sr., Cirrus Aircraft Limited

Another Databricks customer, the **Australian Red Cross Lifeblood **is funded by the Australian governments to provide life-giving blood, plasma, transplantation and biological products, including breast milk and FMT to deliver world-leading health outcomes with 10.5 million eligible donors. They use Lakeflow and the SQL Server connector to help build reliable, maintainable pipelines quickly and consistently. Learn more by watching their on-demand presentation, part of, [“From Burnout to Breakthrough: A New Approach to Data Engineering,”](https://www.databricks.com/resources/webinar/burnout-breakthrough-new-approach-data-engineering) or watch their 2025 Data + AI Summit session, “[From Datavault to Delta Lake: Streamlining Data Sync with Lakeflow Connect.](https://youtu.be/75nDOBqLQB0?feature=shared)”

> "Databricks Lakeflow Connect gives us a simple, reliable SQL Server connector that delivers data into our lakehouse without complex data engineering.” —Dr. Andrew Clarke, Senior AI/ML Engineer, Australian Red Cross Lifeblood

**Ubisoft** is a creator of worlds, committed to enriching players’ lives with original and memorable entertainment experiences. Ubisoft’s global teams create and develop a deep and diverse portfolio of games, featuring brands such as Assassin’s Creed®, Just Dance®, and a lot more.  For the 2024-25 fiscal year, Ubisoft generated net bookings of €1.85 billion. 

> "Ubisoft is looking forward to implementing the SQL Server connector from Lakeflow Connect across our brands for key projects to help accelerate translating SQL Server data into actionable game production insights.” —Valéry Simon, Director of Data Platform & Engineering, Ubisoft

## Unlock a wide range of SQL Server use cases with Databricks

The SQL Server connector enables a wide range of industry-specific use cases, such as customer 360, portfolio management, consumer analytics, and internal chatbots to help drive meaningful impact. 

For example, a Customer 360 use case in retail marketing may need to matching customer personas to the right promotions, which often means stitching together data from siloed systems, such as: 

- **SQL Server** *operational* data: promotions, inventory, transactions
- **Salesforce** *customer* data: emails, deals, personas

The challenge is that SQL Server also underpins mission-critical applications, so running heavy queries or performing full refreshes can introduce latency and impact operational performance.

With Lakeflow Connect, data flows seamlessly into the lakehouse without complex pipelines or operational impact. The SQL Server connector supports multi-environment ingestion with built-in CDC and CT, while the Salesforce connector incrementally ingests data from Salesforce core. Together, they deliver a governed, analytics-ready Customer 360 view—accelerating insights and removing the need for fragile third-party tools or custom code.

**Customer 360 Use Case with Lakeflow Connect**

## Getting started with Lakeflow Connect

[Lakeflow Connect](https://www.databricks.com/product/data-engineering/lakeflow-connect) offers simple and efficient connectors to ingest data from popular applications, databases, cloud storage sources, message buses, and more. Since the Data + AI Summit in June, we’ve continued to expand the breadth of supported data sources for Lakeflow Connect. Both the **ServiceNow** and **Google Analytics** connectors are now GA, with more releases coming for **Zerobus Ingest**, **SharePoint**, **PostgreSQL**, and **SFTP**. We also have new query-based connectors for database and data warehouse sources such as **Oracle DB**, **MySQL**, **Teradata**, and more, coming soon in preview.  Reach out to your account team if interested in participating. 

Get started today with the SQL Server connector to help unlock high-value use cases. Check out the [SQL Server documentation](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/sql-server-source-setup) for details on how to set up your SQL Server and the latest features, as well as more details on [rates](https://www.databricks.com/product/pricing/lakeflow-connect). You can learn more about Lakeflow capabilities through our new ["Data Engineering with Databricks" video series on YouTube](https://www.youtube.com/playlist?list=PLTPXxbhUt-YXQr3m1o48RfiswmInbaSg2) or register for [Lakeflow Connect courses](https://www.databricks.com/training/catalog?search=lakeflow+connect) from Databricks.
