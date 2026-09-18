# Introducing Apache Spark 2.1

- Source: https://www.databricks.com/blog/2016/12/29/introducing-apache-spark-2-1.html
- Published: 2016-12-29
- Authors: Reynold Xin
- Categories: engineering, open-source
- Images: 0 total, 0 extracted as architecture

*Spark Summit will be held in Boston on Feb 7-9, 2017. Check out the [full agenda](https://www.databricks.com/dataaisummit) and [get your ticket](https://gtrnow.com/online-reg-help/?remv=Spark_Summit_East_2017) before it sells out!*

---

Today we are happy to announce the availability of [Apache Spark 2.1.0](https://spark.apache.org/releases/spark-release-2-1-0.html).

This release makes measurable strides in the production readiness of Structured Streaming, with added support for event time watermarks and Apache Kafka 0.10 support. In addition, the release focuses more on usability, stability, and refinement, resolving over 1200 tickets, than previous Spark releases.

This blog post discusses some of the high-level changes to help you navigate the 1200+ improvements and bug fixes:

- Production readiness of Structured Streaming
- Expanding SQL functionalities
- New distributed machine learning algorithms in R

## Structured Streaming

Introduced in Spark 2.0, [Structured Streaming](https://www.databricks.com/blog/2016/07/28/structured-streaming-in-apache-spark.html) is a high-level API for building [continuous applications](https://www.databricks.com/blog/2016/07/28/continuous-applications-evolving-streaming-in-apache-spark-2-0.html). The main goal is to make it easier to build end-to-end streaming applications, which integrate with storage, serving systems, and batch jobs in a consistent and fault-tolerant way.

- **Event-time watermarks:** This change lets applications hint to the system when events are considered “too late” and allows the system to bound internal state tracking late events.
- **Support for all file-based formats and all file-based features:** With these improvements, Structured Streaming can read and write all file-based formats, e.g. JSON, text, Avro, CSV. In addition, all file-based features—e.g. partitioned files and bucketing—are supported on all formats.
- **Apache Kafka 0.10:** This adds native support for Kafka 0.10, including manual assignment of starting offsets and rate limiting.

Streaming applications run 24/7 continuously and put stringent requirements on the visibility and manageability of the underlying system. To that end, Spark 2.1 adds the following features:

- **GUID:** The addition of a GUID that can be used to identify a streaming query across restarts.
- **Forward compatible & human readable checkpoint logs:** A stable JSON format is now used for all checkpoint logs, which allows users to upgrade a streaming query from Spark 2.1 to future versions of Spark. In addition, the log format is designed so it can be inspected readily by a human, to gain visibility into the running systems.
- **Improved reporting of query status:** The query status API has been updated to include more information based on our own production experience, for both current query status as well as historical progress.

At Databricks, we religiously believe in dogfooding. Using a release candidate version of Spark 2.1, we have ported some of our internal data pipelines as well as worked with some of our customers to port their production pipelines using Structured Streaming. In coming weeks, we will be publishing a series of blog posts on various aspects of Structured Streaming as well as our experience with it. Stay tuned for more deep dives.

## SQL and Core APIs

Since Spark 2.0 release, Spark is now one of the most feature-rich and standard-compliant SQL query engine in the Big Data space. It can connect to a variety of data sources and perform SQL-2003 feature sets such as [analytic functions and subqueries](https://www.databricks.com/blog/2016/06/17/sql-subqueries-in-apache-spark-2-0.html). Spark 2.1 adds a number of SQL functionalities:

- **Table-valued functions:** Spark 2.1 introduces the concept of table-valued functions, or TVF, a function that returns a relation, or a set of rows. The first built-in table-valued functions is “range”, a TVF that returns a range of rows. As an example, “SELECT count(*) FROM range(1000)” would return 1000.
- **Enhanced partition column inference:** Added support for inferring date, timestamp, and decimal type for partition columns.
- **Enhanced inline tables:** While Spark 2.0 added support for inline tables, Spark 2.1 enhanced inline tables to support specifying values using any foldable expressions and also automatically coerced types. As an example, “SELECT * FROM VALUES (1, “one”), (1 + 1, “two”)” selects from a table with 2 rows.
- **Null ordering:** Users can now specify how to order nulls, e.g. NULLS FIRST or NULLS LAST in ORDER BY clause.
- **Binary literals:** X'1C7' would mean a binary literal (byte array) 0x1c7.
- **MINUS:** Added support for MINUS set operation, which is the equivalent of EXCEPT DISTINCT.
- **to_json and from_json functions:** All along Spark automatically infers types for JSON datasets. We have also seen a lot of datasets in which one or two string columns are JSON encoded. Two new functions work with JSON columns.
- **Cross join hint:** When working with a large amount of data, a cross join can be extremely expensive and users often don’t want to actually perform a cross join. Spark 2.1 out of the box disables cross join support, unless users explicitly issue a query with “CROSS JOIN” syntax. That is to say, Spark 2.1 will reject “SELECT * FROM a JOIN b”, but allow “SELECT * FROM a CROSS JOIN b.” This way Spark prevents users from shooting themselves in the shoot. To disable this behavior, change “spark.sql.crossJoin.enabled” to “true”.

Spark 2.1 also adds a number of improvements to the core Dataset/DataFrame API, mostly in the typed API:

- **KeyValueGroupedDataset.mapValues:** Users can now map over the values on a KeyValueGroupedDataset, without modifying the keys.
- **Partial aggregation for KeyValueGroupedDataset.reduceGroups:** reduceGroups now supports partial aggregation to reduce the amount of data shuffled across the network.
- **Encoder for java.util.Map:** java.util.Map types can be automatically inferred as a Spark map type.

## MLlib and SparkR

The last major set of changes in Spark 2.1 focuses on advanced analytics. The following new algorithms were added to MLlib and GraphX:

- [Locality Sensitive Hashing](https://www.databricks.com/blog/2017/05/09/detecting-abuse-scale-locality-sensitive-hashing-uber-engineering.html)
- Multiclass Logistic Regression
- Personalized PageRank

Spark 2.1 also adds support for the following distributed algorithms in SparkR:

- ALS
- Isotonic Regression
- Multilayer Perceptron Classifier
- Random Forest
- Gaussian Mixture Model
- LDA
- Multiclass Logistic Regression
- Gradient Boosted Trees

With the addition of these algorithms, SparkR has become the most comprehensive library for distributed machine learning on R.

This blog post only covered some of the major features in this release. You can head over to the [official release notes](https://spark.apache.org/releases/spark-release-2-1-0.html) to see the complete list of changes.

We will be posting more details about some of these new features in the coming weeks. Stay tuned to the Databricks blog to learn more about Spark 2.1. If you want to try out these new features, you can already use Spark 2.1 in Databricks, alongside older versions of Spark. [Sign up for a free trial account here.](https://www.databricks.com/try-databricks)
