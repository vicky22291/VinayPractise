# Announcing Apache Spark 1.2

- Source: https://www.databricks.com/blog/2014/12/19/announcing-spark-1-2.html
- Published: 2014-12-19
- Authors: Patrick Wendell
- Categories: engineering, open-source
- Images: 0 total, 0 extracted as architecture

We at Databricks are thrilled to announce the release of Apache Spark 1.2! Apache Spark 1.2 introduces many new features along with scalability, usability and performance improvements. This post will introduce some key features of Apache Spark 1.2 and provide context on the priorities of Spark for this and the next release. In the next two weeks, we’ll be publishing blog posts with more details on feature additions in each of the major components. Apache Spark 1.2 has been posted today on the [Apache Spark website](https://spark.apache.org/releases/spark-release-1-2-0.html).

Learn more about specific new features in related in-depth posts:

- [Spark SQL data sources API](https://www.databricks.com/blog/2015/01/09/spark-sql-data-sources-api-unified-data-access-for-the-spark-platform.html)
- [JSON support in Spark SQL](https://www.databricks.com/blog/2015/02/02/an-introduction-to-json-support-in-spark-sql.html)
- [ML pipeline API](https://www.databricks.com/blog/2015/01/07/ml-pipelines-a-new-high-level-api-for-mllib.html)
- [Streaming k-means](https://www.databricks.com/blog/2015/01/28/introducing-streaming-k-means-in-spark-1-2.html)
- [Random forests and GBTs](https://www.databricks.com/blog/2015/01/21/random-forests-and-boosting-in-mllib.html)
- [Improved fault tolerance in Spark streaming](https://www.databricks.com/blog/2015/01/15/improved-driver-fault-tolerance-and-zero-data-loss-in-spark-streaming.html)

## Optimizations in Spark's core engine

Apache Spark 1.2 includes several cross-cutting optimizations focused on performance for large scale workloads. Two new features Databricks developed for our [world record petabyte sort](https://www.databricks.com/blog/2014/11/05/spark-officially-sets-a-new-record-in-large-scale-sorting.html) with Spark are turned on by default in Apache Spark 1.2. The first is a re-architected network transfer subsystem that exploits Netty 4’s zero-copy IO and off heap buffer management. The second is Spark's sort based shuffle implementation, which we've now made the default after significant testing in Apache Spark 1.1. Together, we've seen these features give as much as 5X performance improvement for workloads with very large shuffles.

## Spark SQL data sources and Hive 13

Until now, Spark SQL has supported accessing any data described in an [Apache Hive](https://www.databricks.com/glossary/apache-hive) metastore, along with a small number of native bindings for popular formats such as Parquet and JSON. This release introduces a standard API for native integration with other file formats and storage systems. The API supports low level optimizations such as predicate pushdown and direct access to Spark SQL’s table catalog. Any data sources written for this API are automatically queryable in Java, Scala and Python. At Databricks, we’ve released an [Apache Avro connector](https://github.com/databricks/spark-avro) based on this API (itself requiring less than 100 lines of code), and we expect several other connectors to appear in the coming months from the community. Using the input API is as simple as listing the desired format:

*Creating a Parquet Table**Creating a JSON Table*

| ``` CREATE TEMPORARY TABLE users_parquet USING org.apache.spark.sql.parquet OPTIONS (path 'hdfs://parquet/users');``` | ``` CREATE TEMPORARY TABLE users_json USING org.apache.spark.sql.json OPTIONS (path 'hdfs://json/users');``` |
|---|---|

Note that neither the schema nor the partitioning layout is specified here. Spark SQL is able to learn that automatically in both cases. For users reading data from Hive tables, we've bumped our support to Hive 0.13 and included support for its fixed-precision decimal type.

## Spark Streaming H/A and Python API

In this release, Spark Streaming adds a full H/A mode that uses a persistent Write Ahead Log (WAL) to provide recoverability for input sources if nodes crash. This feature removes any single-point-of-failure from Spark Streaming, a common request from production Spark Streaming users. The WAL mechanism is supported out-of-the-box for Apache Kafka, and the more general API for third-party connectors has been extended with durability support. In addition, this release adds a Python API for Spark Streaming, letting you create and transform streams entirely in Python.

## Machine learning pipelines

We've extended Spark's machine learning library with a new, higher-level API for constructing pipelines, in the `spark.ml` package. In practice, most machine learning workflows involve multiple preprocessing and featurization steps, as well as training and evaluating multiple models. The ML pipelines API provides first-class support for these types of pipelines, including the ability to search for parameters and automatically score models. It is modeled after high-level machine learning libraries like SciKit-Learn, and brings the same ease of use to learning on big data.

| *Defining a three-stage ML pipeline* |
|---|
| ``` val tokenizer = new Tokenizer() .setInputCol("text") .setOutputCol("words") val hashingTF = new HashingTF() .setInputCol(tokenizer.getOutputCol) .setOutputCol("features") val lr = new LogisticRegression().setMaxIter(10) val pipeline = new Pipeline() .setStages(Array(tokenizer, hashingTF, lr))``` |

The new ML API is experimental in Apache Spark 1.2 as we get feedback from users, but will be stabilized in 1.3.

## Stable GraphX API

The GraphX project graduates from alpha in this release, providing a stable API. This means applications written against GraphX can be safely migrated to future Spark 1.X versions without code changes. Coinciding with API stabilization, a handful of issues have been fixed which affect very large scale and highly iterative graphs seen in production workloads.

---

This post only scratches the surface of interesting features in Apache Spark 1.2. Overall, this release contains more than 1000 patches from 172 contributors** **making it our largest yet despite a year of tremendous growth. Head over to the [official release notes](https://spark.apache.org/releases/spark-release-1-2-0.html) to learn more about this release, and watch the Databricks blog for more detailed posts about the major features in the next few days!
