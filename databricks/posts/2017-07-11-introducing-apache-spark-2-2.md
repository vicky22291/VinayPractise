# Introducing Apache Spark 2.2

- Source: https://www.databricks.com/blog/2017/07/11/introducing-apache-spark-2-2.html
- Published: 2017-07-11
- Authors: Michael Armbrust
- Categories: engineering, open-source
- Images: 1 total, 0 extracted as architecture

Today we are happy to announce the availability of [Apache Spark 2.2.0](https://spark.apache.org/releases/spark-release-2-2-0.html) on Databricks as part of the Databricks Runtime 3.0.

This release marks a major milestone for Structured Streaming by marking it as production ready and removing the experimental tag. In this release, we also support for arbitrary stateful operations in a stream, and Apache Kafka 0.10 support for both reading and writing using the streaming and batch APIs. In addition to extending new functionality to SparkR, Python, MLlib, and GraphX, the release focuses on usability, stability, and refinement, resolving over 1100 tickets.

This blog post discusses some of the high-level changes, improvements and bug fixes:

- Production ready Structured Streaming
- Expanding SQL functionalities
- New distributed machine learning algorithms in R
- Additional Algorithms in MLlib and GraphX

## Structured Streaming

Introduced in Spark 2.0, [Structured Streaming](https://www.databricks.com/blog/2016/07/28/structured-streaming-in-apache-spark.html) is a high-level API for building [continuous applications](https://www.databricks.com/blog/2016/07/28/continuous-applications-evolving-streaming-in-apache-spark-2-0.html). Our goal is to make it easier to build end-to-end streaming applications, which integrate with storage, serving systems, and batch jobs in a consistent and fault-tolerant way.

The third release in 2.x line, Spark 2.2 declares Structured Streaming as production ready, **meaning removing the experimental tag**, with additional high-level changes:

- **Kafka Source and Sink:** Support for [reading and writing data in streaming or batch to and from Apache Kafka](https://www.databricks.com/blog/2017/04/26/processing-data-in-apache-kafka-with-structured-streaming-in-apache-spark-2-2.html)
- **Kafka Improvements:** Cached producer for lower latency Kafka to Kafka streams
- **Additional Stateful APIs:** Support for complex stateful processing and timeouts using *[flat]MapGroupsWithState*
- **Run Once Triggers:** Allows to [trigger only one-time execution](https://www.databricks.com/blog/2017/05/22/running-streaming-jobs-day-10x-cost-savings.html), hence lowering the cost of clusters

At Databricks, we religiously believe in dogfooding. Using a release candidate version of Spark 2.2, we have ported some of our internal data pipelines as well as worked with some of our customers to port their [production pipelines using Structured Streaming](https://www.databricks.com/blog/2017/05/18/taking-apache-sparks-structured-structured-streaming-to-production.html).

## SQL and Core APIs

Since Spark 2.0 release, Spark is now one of the most feature-rich and standard-compliant SQL query engine in the Big Data space. It can connect to a variety of data sources and perform SQL-2003 feature sets such as [analytic functions and subqueries](https://www.databricks.com/blog/2016/06/17/sql-subqueries-in-apache-spark-2-0.html). Spark 2.2 adds a number of SQL functionalities:

- **API Updates:** Unify CREATE TABLE syntax for data source and hive serde tables and add broadcast hints such as BROADCAST, BROADCASTJOIN, and MAPJOIN for SQL Queries
- **Overall Performance and stability:**
  - Cost-based optimizer cardinality estimation for filter, join, aggregate, project and limit/sample operators and Cost-based join re-ordering
  - TPC-DS performance improvements using star-schema heuristics
  - File listing/IO improvements for CSV and JSON
  - Partial aggregation support of HiveUDAFFunction
  - Introduce a JVM object based aggregate operator
- **Other notable changes:**
  - Support for parsing multi-line JSON and CSV files
  - Analyze Table Command on partitioned tables
  - Drop Staging Directories and Data Files after completion of Insertion/CTAS against Hive-serde Tables

## MLlib, SparkR, and Python

The last major set of changes in Spark 2.2 focuses on advanced analytics and Python. Now you can install [PySpark from PyPI](https://pypi.org/project/pyspark/) package using pip install. To boost advanced analytics, a few new algorithms were added to MLlib and GraphX:

- [Locality Sensitive Hashing](https://www.databricks.com/blog/2017/05/09/detecting-abuse-scale-locality-sensitive-hashing-uber-engineering.html)
- Multiclass Logistic Regression
- Personalized PageRank

Spark 2.2 also adds support for the following distributed algorithms in SparkR:

- ALS
- Isotonic Regression
- Multilayer Perceptron Classifier
- Random Forest
- Gaussian Mixture Model
- LDA
- Multiclass Logistic Regression
- Gradient Boosted Trees
- Structured Streaming API for R
- column functions *to_json*, *from_json* for R
- Multi-column approxQuantile in R

With the addition of these algorithms, SparkR has become the most comprehensive library for distributed machine learning on R.

While this blog post only covered some of the major features in this release, you can read the official [release notes](https://spark.apache.org/releases/spark-release-2-2-0.html) to see the complete list of changes.

If you want to try out these new features, you can use Spark 2.2 in Databricks Runtime 3.0. Sign up for a [free trial account here](https://www.databricks.com/try-databricks).
