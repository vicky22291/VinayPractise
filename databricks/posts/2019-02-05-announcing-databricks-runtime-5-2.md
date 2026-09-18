# Announcing Databricks Runtime 5.2

- Source: https://www.databricks.com/blog/2019/02/05/announcing-databricks-runtime-5-2.html
- Published: 2019-02-05
- Authors: Nakul Jamadagni
- Categories: engineering, product, announcements
- Images: 2 total, 0 extracted as architecture

We are excited to announce the release of Databricks Runtime 5.2 which introduces several new features including the following:

1. Delta Time Travel
2. Fast Parquet Import
3. Databricks Advisor

Let’s unpack each of these features in more detail:

### Delta Time Travel

Time Travel, released as an [Experimental](https://docs.databricks.com/release-notes/release-types.html#runtime-releases) feature, adds the ability to query a snapshot of a table using a timestamp string or a version, using SQL syntax as well as DataFrameReader options for timestamp expressions.

**Sample code**

**SELECT** **count**(*) **FROM** events **TIMESTAMP** **AS** **OF** timestamp_expression
**SELECT** **count**(*) **FROM** events **VERSION** **AS** **OF** **version**

Delta Time Travel is useful for

- Re-creating analyses, reports, or outputs (for example, the output of a machine learning model), which is useful for debugging or auditing, especially in regulated fields.
- Writing complex temporal queries.
- Fixing mistakes in your data.
- Providing snapshot isolation for a set of queries for fast changing tables.

You can find more detail about Time Travel at [this blog](https://www.databricks.com/blog/2019/02/04/introducing-delta-time-travel-for-large-scale-data-lakes.html) and from the product documentation.([Azure](https://docs.microsoft.com/en-us/azure/databricks/delta/delta-batch#deltatimetravel) | [AWS](https://docs.databricks.com/delta/delta-batch.html#deltatimetravel))

### Fast Parquet Import

Fast Parquet import enables users to import Parquet files into a Delta table without copying data. This feature makes it easier to convert existing Parquet tables and migrate pipelines to Delta.  For more details please see the documentation([Azure](https://docs.microsoft.com/en-us/azure/databricks/spark/latest/spark-sql/language-manual/delta-convert-to-delta#convert-to-delta-delta) | [AWS](https://docs.databricks.com/spark/latest/spark-sql/language-manual/delta-convert-to-delta.html#convert-to-delta-delta)).

**Sample code**

**CONVERT** **TO** DELTA parquet.`path/**to**/**table**` [**NO** **STATISTICS**]
 [PARTITIONED **BY** (col_name1 col_type1, col_name2 col_type2, ...)]

### Databricks Advisor

Databricks Advisor is a new feature within Notebooks. It automatically analyzes commands and displays advice notifications to assist you in improving the performance of your query. We are launching Databricks Advisor with two hint types in this release: for DBIO cache and range joins. There will be more advice to come in future releases. For more details please see the documentation([Azure](https://docs.microsoft.com/en-us/azure/databricks/notebooks/notebooks-use#databricks-advisor) | [AWS](https://docs.databricks.com/notebooks/notebooks-use.html#id1)).

 To read more about the above new features and to see the full list of improvements included in Databricks Runtime 5.2, please see the release notes ([Azure](https://docs.microsoft.com/en-us/azure/databricks/release-notes/runtime/5.2) | [AWS](https://docs.databricks.com/release-notes/runtime/5.2.html)).
