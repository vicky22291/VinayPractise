# Announcing Databricks Runtime 5.0

- Source: https://www.databricks.com/blog/2018/11/18/announcing-databricks-runtime-5-0.html
- Published: 2018-11-18
- Authors: Todd Greenstein
- Categories: announcements, product, open-source, company
- Images: 0 total, 0 extracted as architecture

We’re excited to announce the general availability of Databricks Runtime 5.0. Included in this release is [Spark 2.4](https://www.databricks.com/blog/2018/11/08/introducing-apache-spark-2-4.html). This release offers substantial performance increases within key areas of the platform. Benchmarking workloads have shown a 16% improvement in total execution time and Databricks Delta benefits from substantial improvements to [metadata caching](https://docs.databricks.com/delta/optimizations/delta-cache.html), improving query latency by 30%. Beyond these powerful performance improvements we've packed this release with many new features and improvements. I'll highlight some of these now.

### **Enhanced Writes with MERGE, DELETE and UPDATE for Databricks Delta**

With Databricks Runtime 5.0 we've improved the usage for MERGE commands:

- Scalable MERGE command with Databricks Delta: There is no longer a limit on the number of inserts and updates that can be performed with a merge. We've eliminated any previous limits allowing merge scalability to billions of rows.
 You can also now use MERGE for SCD Type 1 and Type 2 queries. SCD Type 2 queries track historical data by creating multiple records for a given natural key in the dimensional tables. A typical use case that Databricks Delta now supports might look like: Given a table with a list of customers and their current address, SCD Type 2 queries allow you to update a customer's current address and maintain the record for their previous address along with the active date range in one query. For further information on MERGE, and these new features see consult the [documentation](https://docs.databricks.com/spark/latest/spark-sql/language-manual/delta-merge-into.html#merge-into-delta).
- Subqueries are now supported in the WHERE clause for DELETE and UPDATE Commands. Any subquery you would normally put in a WHERE clause for DELETE and UPDATE are now supported in Databricks Delta, such as the following examples:

For further information on UPDATE and DELETE commands, please refer to the Databricks [Delta Documentation](https://docs.databricks.com/spark/latest/spark-sql/language-manual/delta-update.html).

### **Improved reads using OPTIMIZE command with Databricks Delta**

In addition to the new features in this release we’ve invested heavily in improvements for Databricks Delta, including work to improve performance and stability for the OPTIMIZE command:

- The OPTIMIZE command now commits batches as soon as possible, where in previous releases this was performed at the end. This improves optimize time and performance.
- We reduced the default number of threads OPTIMIZE runs in parallel. This dramatically improves optimize performance for large tables.
- Databricks Runtime 5.0 speeds up OPTIMIZE writes by avoiding unnecessarily sorting the data when writing a to a partitioned table.
- Beginning with Databricks Runtime 5.0, OPTIMIZE ZORDER is now incremental, eliminating the need for rewriting data files that were previously Z-Ordered by the same column(s).

We’ve improved the isolation level for Databricks Delta queries. Any query with multiple references to a single Databricks Delta table (self-joins etc) will read from the same snapshot even if there are concurrent updates to the table.

Lastly, we want to point out the improved query latency for small Databricks Delta tables (release notes for Databricks Runtime 5.0.

### **Structured Streaming - New Features**

We’ve upgraded the streaming source Kafka client to version 2.0.0, which is an important milestone. Databricks now supports kafka.isolation.level to read only committed records from Kafka topics that are written using a transactional producer.

We’ve also included the new Azure Blob Storage file notification based Streaming Source. Instead of listing to find new files for processing, this streaming source, can directly read file event notifications to find new files. This can significantly reduce listing costs for Structured Streaming queries on files in Azure Blob Storage.

To read more about the above new features and to see the full list of improvements included in Databricks Runtime 5.0, refer to the release notes in the following locations:

- Amazon Web Services: [Databricks Runtime 5.0 release notes](https://docs.databricks.com/release-notes/runtime/5.0.html)
- Microsoft Azure: [Azure Databricks Runtime 5.0 release notes](https://docs.microsoft.com/en-us/azure/databricks/release-notes/runtime/5.0)

We recommend all customers upgrade to Databricks Runtime 5.0 to take advantage of these new features and performance optimizations.
