# Announcing the Preview of Serverless Compute for Databricks SQL on Azure Databricks

- Source: https://www.databricks.com/blog/2022/08/03/announcing-the-preview-of-serverless-compute-for-databricks-sql-on-azure-databricks.html
- Published: 2022-08-03
- Authors: Nikhil Jethava, Shankar Sivadasan
- Categories: platform, announcements, data-warehousing
- Images: 0 total, 0 extracted as architecture

[Databricks SQL Serverless](https://www.databricks.com/product/databricks-sql) is now generally available. Read [our blog](https://www.databricks.com/blog/announcing-general-availability-databricks-sql-serverless) to learn more.

 

We are excited to announce the preview of Serverless compute for [Databricks SQL](https://www.databricks.com/product/databricks-sql) (DBSQL) on Azure Databricks. DBSQL Serverless makes it easy to get started with data warehousing on the lakehouse. Serverless compute for DBSQL frees up time, lowers costs, and enables you to focus on delivering the most value to your business rather than managing infrastructure. In this blog post, we will go over the benefits of DBSQL Serverless and show how you can integrate with popular business intelligence tools such as Microsoft Power BI to get powerful analytics and insights from your data.

Serverless compute for DBSQL helps address challenges customers face with cluster startup time, capacity management, and infrastructure costs:

- **Instant and elastic:** Serverless compute brings a truly elastic environment that's instantly available and scales with your needs. You'll benefit from simple usage-based pricing, without worrying about idle time charges. Imagine no longer needing to wait for clusters to become available to run queries or overprovisioning resources to handle spikes in usage. Databricks SQL Serverless dynamically grows and shrinks resources to handle whatever workload you throw at it.
- **Eliminate management overhead:** Serverless transforms DBSQL into a fully managed service, eliminating the burden of capacity management, patching, upgrading, and performance optimization of the cluster. You only need to focus on your data and the insights it holds. Additionally, the simplified pricing model means there's only one bill to track and only one place to check costs.
- **Lower infrastructure costs:** Under the covers, the serverless compute platform uses machine learning algorithms to provision and scale compute resources right when you need them. This enables substantial cost savings without the need to manually shut down clusters.

## Using Databricks SQL Serverless with Power BI

Once your administrator enables Serverless for your Azure Databricks workspace, you will see the Serverless option when creating a SQL warehouse.

This short video shows how you can create a Serverless SQL warehouse and connect it to Power BI. The seamless integration enables you to use Databricks SQL and Power BI to analyze, visualize and derive insights from your data instantly without worrying about managing your infrastructure.

## Get Started

Serverless compute for Databricks SQL will be rolling out over the next few days to Azure East US 2, Azure East US, Azure West Europe. Please [submit](http://bit.ly/DBSQLServerless-Azure) a request to start using DBSQL Serverless on Azure. For instructions on connecting Power BI with Databricks SQL warehouse, visit the [Power BI documentation page](https://docs.microsoft.com/en-us/azure/databricks/integrations/bi/power-bi).
