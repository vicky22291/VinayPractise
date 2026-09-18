# Announcing Databricks Runtime 4.1

- Source: https://www.databricks.com/blog/2018/05/23/announcing-databricks-runtime-4-1.html
- Published: 2018-05-23
- Authors: Cihan Biyikoglu
- Categories: company, product, engineering
- Images: 0 total, 0 extracted as architecture

We have recently shipped the new Databricks Runtime version 4.1 powered by Apache Spark™. Version 4.1 brings improved performance on read/write from sources like S3 or Parquet, improved caching, and a great deal of quality and feature improvements for the preview of Databricks Delta focused on faster query execution and adaptive schema and type validation.

If you are participating in our preview of Databricks Delta on Azure Databricks or Amazon's AWS, it is highly recommended that you upgrade to version 4.1 today.

Let's take a closer look at some of the improvements:

- **Faster Query Execution: **There are a number of improvement in this area that benefit all queries like code generation enhancements. Here are a few specific highlights.
  - **Stats & Indexing (Delta): **Databricks Delta stats collection makes query execution smarter. In this release, collecting these stats has gotten more efficient. In our measurements internally, we see over 40% improvement in stats collections time.
  - **Faster OPTIMIZE (Delta):** `OPTIMIZE` command improves reads by consolidating files. With this release, `OPTIMIZE` now executes in parallel - greatly speeding up the time it takes to optimize a table.
  - **Lower Latencies with ****`LIMIT`**** (Delta): **There are also improvements in limit pushdown that reduce intermediate result sets size.
  - **Improved Streaming Throughput (Delta):** With this release, we are also pushing filters further down for improved streaming efficiency.
  - **Faster *****`UPDATE`*****, *****DELETE***** and *****`MERGE`***** (Delta):** Writes with `UPDATE,DELETE` and `MERGE` statements in Delta can now use stats and perform data skipping for lower latency executions.
- **Managing Schema Validation and Evolution (Delta):** Validating data is an important part of keeping your data pipelines robust. However the structure of real world data changes over time. Databricks Delta now provides two forms of schema evolution: automatic, which can generate the required DDL as new columns appear; or static, which provides greater control using standard `ALTER TABLE` DDL.  You can learn more about Schema Validation [here](https://docs.databricks.com/delta/delta-batch.html#schema-validation).
- **Faster Reads and Writes: **
  - **Faster Parquet:** We now have an improved decoder that is turned on by default in version 4.1. In our internal measurements done on AWS S3, the new parquet reader, combined with IO caching is about 3x faster in MB/sec!
  - **Improved S3 Access:** S3 Select brings efficiency to the retrieval of S3 data. With selective retrieval, less data is on the wire when you read a subset of JSON or CSV attributes. You can read more about S3 Select [here](https://docs.databricks.com/data/data-sources/aws/amazon-s3-select.html).

Databricks Delta remains in Private Preview, but the updates on version 4.1 represent a candidate release in anticipation of the upcoming general availability (GA) release. If you are not already participating in the Databricks Delta preview, you can still sign up [here](https://www.databricks.com/product/delta-lake-on-databricks).

This post touches on only a few select improvements in the 4.1 release. If you’d like to go over the full set of improvements, please visit the release notes for version 4.1 [here](https://docs.databricks.com/release-notes/runtime/4.1.html).

If you’d like to hear more about the features here and more about Databricks Runtime, stop by our booth at the Spark + AI Summit in San Francisco.

Come find out what’s new in Spark, Data, and AI! [Register now.](https://www.databricks.com/sparkaisummit/north-america-2020)
