# Introducing Apache Spark 2.4

- Source: https://www.databricks.com/blog/2018/11/08/introducing-apache-spark-2-4.html
- Published: 2018-11-08
- Authors: Wenchen Fan, Xiao Li, Reynold Xin
- Categories: engineering, solutions, data-engineering, data-science-machine-learning, platform, open-source
- Images: 1 total, 0 extracted as architecture

**UPDATED: 11/19/2018**

We are excited to announce the availability of [Apache Spark 2.4](https://spark.apache.org/releases/spark-release-2-4-0.html) on Databricks as part of the [Databricks Runtime 5.0](https://docs.microsoft.com/en-us/azure/databricks/release-notes/runtime/5.0). We want to thank the Apache Spark community for all their valuable contributions to the Spark 2.4 release.

Continuing with the objectives to make Spark faster, easier, and smarter, Spark 2.4 extends its scope with the following features:

- A scheduler to support barrier mode for better integration with MPI-based programs, e.g. distributed deep learning frameworks
- Introduce a number of built-in higher-order functions to make it easier to deal with complex data types (i.e., array and map)
- Provide experimental support for Scala 2.12
- Allow the eager evaluation of DataFrames in notebooks for easy debugging and troubleshooting.
- Introduce a new built-in Avro data source

In addition to these new features, the release focuses on usability, stability, and refinement, resolving over 1000 tickets. Other salient features from Spark contributors include:

- Eliminate the 2 GB block size limitation [[SPARK-24296](https://issues.apache.org/jira/browse/SPARK-24296), [SPARK-24307](https://issues.apache.org/jira/browse/SPARK-24307)]
- Pandas UDF improvements [[SPARK-22274](https://issues.apache.org/jira/browse/SPARK-22274), [SPARK-22239](https://issues.apache.org/jira/browse/SPARK-22239), [SPARK-24624](https://issues.apache.org/jira/browse/SPARK-24624)]
- Image schema data source [[SPARK-22666]](https://issues.apache.org/jira/browse/SPARK-22666)
- Spark SQL enhancements [[SPARK-23803](https://issues.apache.org/jira/browse/SPARK-23803), [SPARK-4502](https://issues.apache.org/jira/browse/SPARK-4502), [SPARK-24035](https://issues.apache.org/jira/browse/SPARK-24035), [SPARK-24596](https://issues.apache.org/jira/browse/SPARK-24596), [SPARK-19355](https://issues.apache.org/jira/browse/SPARK-19355)]
- Built-in file source improvements [[SPARK-23456](https://issues.apache.org/jira/browse/SPARK-23456), [SPARK-24576](https://issues.apache.org/jira/browse/SPARK-24576), [SPARK-25419](https://issues.apache.org/jira/browse/SPARK-25419), [SPARK-23972](https://issues.apache.org/jira/browse/SPARK-23972), [SPARK-19018](https://issues.apache.org/jira/browse/SPARK-19018), [SPARK-24244](https://issues.apache.org/jira/browse/SPARK-24244)]
- Kubernetes integration enhancement [[SPARK-23984](https://issues.apache.org/jira/browse/SPARK-23984), [SPARK-23146](https://issues.apache.org/jira/browse/SPARK-23146)]

In this blog post, we briefly summarize some of the higher-level features and improvements, and in the coming days, we will publish in-depth blogs for these features. For a comprehensive list of major features across all Spark components and JIRAs resolved, read the Apache Spark 2.4.0 [release notes](https://spark.apache.org/releases/spark-release-2-4-0.html).

## Barrier Execution Mode

Barrier execution mode is part of [Project Hydrogen](https://www.databricks.com/blog/2018/07/25/bay-area-apache-spark-meetup-summary-databricks-hq.html), which is an Apache Spark initiative to bring state-of-the-art big data and AI together. It enables proper embedding of distributed training jobs from AI frameworks as Spark jobs. They usually explore complex communication patterns like [All-Reduce](https://github.com/baidu-research/baidu-allreduce), and hence all tasks need to run at the same time. This doesn’t fit the MapReduce pattern currently used by Spark. Using this new execution mode, Spark launches all training tasks (e.g., [MPI tasks](https://en.wikipedia.org/wiki/Message_Passing_Interface)) together and restarts all tasks in case of task failures. Spark also introduces a new mechanism of fault tolerance for barrier tasks. When any barrier task failed in the middle, Spark would abort all the tasks and restart the stage.

## Built-in Higher-order Functions

Before Spark 2.4, for manipulating the complex types (e.g. array type) directly, there are two typical solutions: 1) exploding the nested structure into individual rows, and applying some functions, and then creating the structure again. 2) building a User Defined Function (UDF). The new built-in functions can manipulate complex types directly, and the higher-order functions can manipulate complex values with an anonymous lambda function as you like, similar to UDFs but with much better performance.

You can read our [blog on high-order functions](https://www.databricks.com/blog/2018/11/16/introducing-new-built-in-functions-and-higher-order-functions-for-complex-data-types-in-apache-spark.html).

## Built-in Avro Data Source

[Apache Avro](https://avro.apache.org) is a popular data serialization format. It is widely used in the Apache Spark and Apache Hadoop ecosystem, especially for Kafka-based data pipelines. Starting from Apache Spark 2.4 release, Spark provides built-in support for reading and writing Avro data. The new built-in spark-avro module is originally from Databricks’ open source project [Avro Data Source for Apache Spark](https://github.com/databricks/spark-avro) (referred to spark-avro from now on). In addition, it provides:

- New functions *from_avro()* and *to_avro()* to read and write Avro data within a DataFrame instead of just files.
- [Avro logical types](https://avro.apache.org/docs/1.8.2/spec.html#Logical+Types) support, including Decimal, Timestamp and Date type. See the related [schema conversions](https://spark.apache.org/docs/latest/sql-data-sources-avro.html#supported-types-for-spark-sql---avro-conversion) for details.
- 2X read throughput improvement and 10% write throughput improvement.

You can read more about the built-in Avro Data Source in our [in-depth technical blog](https://www.databricks.com/blog/2018/11/30/apache-avro-as-a-built-in-data-source-in-apache-spark-2-4.html).

## Experimental Scala 2.12 Support

Starting from Spark 2.4, Spark supports Scala 2.12 and is cross-built with both Scala 2.11 and 2.12, which are available in both Maven repository and the download page. Now users can write Spark applications with Scala 2.12, by picking the Scala 2.12 Spark dependency.

Scala 2.12 brings better interoperability with Java 8, which offers improved serialization of lambda functions. It also includes new features and bug fixes that users desire.

## Pandas UDF Improvement

[Pandas UDF](https://www.databricks.com/blog/2017/10/30/introducing-vectorized-udfs-for-pyspark.html) was introduced in Spark 2.3.0. During this release, we collected feedback from users, and have kept improving the Pandas UDF.

Other than bug fixes, there are 2 new features in Spark 2.4: [SPARK-22239](https://issues.apache.org/jira/browse/SPARK-22239) User defined window functions with Pandas UDF. [SPARK-22274](https://issues.apache.org/jira/browse/SPARK-22274) User-defined aggregation functions with pandas udf. We believe these new features will further improve the adoption of Pandas UDF, and we will keep improving Pandas UDF in next releases.

## Image Data Source

The community sees more use cases around image/video/audio processing. Providing Spark built-in data sources for those simplifies users’ work to get data into ML training. In the Spark 2.3 release, the image data source is implemented via ImageSchema.readImages. [SPARK-22666](https://issues.apache.org/jira/browse/SPARK-22666) in the Spark 2.4 release introduces a new Spark data source that can load image files recursively from a directory as a DataFrame. Now it’s as simple to load images as:

You can read more about the built-in Image Data Source in our [in-depth technical blog](https://www.databricks.com/blog/2018/12/10/introducing-built-in-image-data-source-in-apache-spark-2-4.html).

## Kubernetes Integration Enhancement

Spark 2.4 includes many enhancements for the Kubernetes integration. We mention three highlights. First, this release supports running containerized PySpark and SparkR applications on Kubernetes. Spark ships the [Dockerfiles](https://github.com/apache/spark/tree/branch-2.4/resource-managers/kubernetes/docker/src/main/dockerfiles/spark) for both Python and R binding for users to build a base image or customize it to build a custom image. Second, the client mode is provided. Users can run interactive tools (e.g., shell or notebooks) in a pod running in a Kubernetes cluster or on a client machine outside a cluster. And finally, mounting the following types of Kubernetes volumes are supported: [emptyDir](https://kubernetes.io/docs/concepts/storage/volumes/#emptydir), [hostPath](https://kubernetes.io/docs/concepts/storage/volumes/#hostpath), and [persistentVolumeClaim](https://kubernetes.io/docs/concepts/storage/volumes/#persistentvolumeclaim). For details, see the [technical blog](https://www.databricks.com/blog/2018/09/26/whats-new-for-apache-spark-on-kubernetes-in-the-upcoming-apache-spark-2-4-release.html).

## Flexible Streaming Sink

Many external storage systems already have batch connectors, but not all of them have streaming sinks. In this release, even if the storage systems do not support streaming as a sink, [`streamingDF.writeStream.foreachBatch(...)`](https://docs.databricks.com/spark/latest/structured-streaming/foreach.html#id1) allows you to use the batch data writers on the output of each microbatch. For example, you can use the existing Apache Cassandra connector inside `foreachBatch` to directly write the output of a streaming query to Cassandra.

Similarly, you can also use it to apply to each micro-batch output many DataFrame/Dataset operations that are not supported in streaming DataFrames. For example, `foreachBatch` can be used to avoid recomputations for streaming queries when writing to multiple locations. For example,

## What’s Next

Once again, we appreciate all the contributions from the Spark community!

While this blog post only summarized some of the salient features in this release, you can read the official [release notes](https://spark.apache.org/releases/spark-release-2-4-0.html) to see the complete list of changes. Stay tuned as we will be publishing technical blogs explaining some of these features in more technical depth.

If you want to try Apache Spark 2.4 in [Databricks Runtime 5.0](https://docs.databricks.com/release-notes/runtime/5.0.html), sign up for a free [trial account here](https://www.databricks.com/try-databricks).
