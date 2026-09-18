# Announcing Apache Spark 1.1

- Source: https://www.databricks.com/blog/2014/09/11/announcing-spark-1-1.html
- Published: 2014-09-11
- Authors: Patrick Wendell
- Categories: engineering, open-source, data-engineering
- Images: 0 total, 0 extracted as architecture

Today we’re thrilled to announce the release of Apache Spark 1.1! Apache Spark 1.1 introduces many new features along with scale and stability improvements. This post will introduce some key features of Apache Spark 1.1 and provide context on the priorities of Spark for this and the next release.

In the next two weeks, we’ll be publishing blog posts with more details on feature additions in each of the major components. Apache Spark 1.1 is already available to Databricks customers and has also been posted today on the [Apache Spark website](https://spark.apache.org/releases/spark-release-1-1-0.html).

## Maturity of SparkSQL

The 1.1 released upgrades Spark SQL significantly from the preview delivered in Apache Spark 1.0. At Databricks, we’ve migrated all of our customer workloads from Shark to Spark SQL, with between 2X and 5X [performance improvements](https://www.databricks.com/blog/2014/06/02/exciting-performance-improvements-on-the-horizon-for-spark-sql.html) across the board. Apache Spark 1.1 adds a JDBC server for Spark SQL, a key feature allowing direct upgrade of Shark installations which relied on JDBC. We’ve also opened up the Spark SQL type system with a public types API, allowing for rich integration with third party data sources. This will provide an extension point for many future integrations, such as the Datastax Cassandra driver. Using this types API, we’ve added turn-key support for loading JSON data into Spark's native ShemaRDD format:

# Create a JSON RDD in Python
 >>> people = sqlContext.jsonFile(“s3n://path/to/files...”)
 # Visualize the inferred schema
 >>> people.printSchema()
 # root
 # |-- age: integer (nullable = true)
 # |-- name: string (nullable = true)

## Expansion of MLlib

Spark’s machine learning library adds several new algorithms, including a library for [standard exploratory statistics](https://www.databricks.com/blog/2014/08/27/statistics-functionality-in-spark.html) such as sampling, correlations, chi-squared tests, and randomized inputs. This allows data scientists to avoid exporting data to single-node systems (R, SciPy, etc) and instead directly operate on large scale datasets in Spark. Optimizations to internal primitives provide a 2-5X performance improvement in most MLlib algorithms out of the box. Decision trees, a popular algorithm, has been ported to Java and Python. Several other algorithms have also been added, including TF-IDF, SVD via Lanczos, and nonnegative matrix factorization. The next release of MLlib will introduce an enhanced API for end-to-end machine learning pipelines.

## Sources and Libraries for Spark Streaming

Spark streaming extends its library of ingestion sources in this release adding two new sources. The first is support for Amazon Kinesis, a hosted stream processing engine. Spark Streaming also adds H/A source for Apache Flume using a new data source which provides transactional hand-off of events from Flume to gracefully tolerate worker failures. Apache Spark 1.1 adds the first of a set of online machine learning algorithms with the introduction of a streaming linear regression. Looking forward, the Spark Streaming roadmap will feature a general recoverability mechanism for all input sources, along with an ever-growing list of connectors. The example below shows training a linear model using incoming data, then using an updated model to make a prediction:

> val stream = KafkaUtils.createStream(...)

// Train a linear model on a data stream
 > val model = new StreamingLinearRegressionWithSGD()
 .setStepSize(0.5)
 .setNumIterations(10)
 .setInitialWeights(Vectors.dense(...))
 .trainOn(DStream.map(record => createLabeledPoint(record))

// Predict using the latest updated model
 > model.latestModel().predict(myDataset)

## Performance in Spark Core

This release adds significant internal changes to Spark focused on improving performance for large scale workloads. Apache Spark 1.1 features a new implementation of the Spark shuffle, a key internal primitive used by almost all data-intensive programs. The new shuffle improves performance by more than 5X for workloads with extremely high degree of parallelism, a key pain point in earlier versions of Spark. Apache Spark 1.1 also adds a variety of other improvements to decrease memory usage and improve performance.

## Optimizations and Features in PySpark

Several of the disk-spilling modifications introduced in Apache Spark 1.0 have been ported to Spark’s Python runtime extension. This release also adds support in Python for reading and writing data from SequenceFiles, Avro, and other Hadoop-based input formats. PySpark now supports the entire Spark SQL API, including support for nested types inside of SchemaRDD’s.

The efforts on improving scale and robustness of Spark and PySpark are based on feedback from the community along with direct interactions with our customer workloads at Databricks. The next release of Spark will continue along this theme, with a focus on improving instrumentation and debugging for users to pinpoint performance bottlenecks.

This post only scratches the surface of interesting features in Apache Spark 1.1. Head on over to the [official release notes](https://spark.apache.org/releases/spark-release-1-1-0.html) to learn more about this release and stay tuned to hear more about Apache Spark 1.1 from Databricks over the coming days!
