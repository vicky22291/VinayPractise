# How to Work with Avro, Kafka, and Schema Registry in Databricks

- Source: https://www.databricks.com/blog/2019/02/15/how-to-work-with-avro-kafka-and-schema-registry-in-databricks.html
- Published: 2019-02-15
- Authors: Wenchen Fan, Michael Armbrust
- Categories: product, solutions, engineering, open-source, data-engineering, data-streaming, company
- Images: 0 total, 0 extracted as architecture

In the [previous blog post](https://www.databricks.com/blog/2018/11/30/apache-avro-as-a-built-in-data-source-in-apache-spark-2-4.html), we introduced the new built-in Apache Avro data source in Apache Spark and explained how you can use it to build streaming data pipelines with the `from_avro` and `to_avro` functions. Apache Kafka and Apache Avro are commonly used to build a scalable and near-real-time data pipeline. In this blog post, we introduce how to build more reliable pipelines in Databricks, with the integration of [Confluent Schema Registry](https://docs.confluent.io/current/schema-registry/docs/index.html). This feature is available since Databricks Runtime 4.2.

## Schema Evolution

For long-running streaming jobs, the schema of data streams often changes over time. Schema evolution is a typical problem in the streaming world. For example, to support changes in business logic, you need to make the corresponding changes by adding new columns to a data stream. The schema changes could break the existing data pipelines and cause a service outage. Instead of stopping, updating, and restarting your pipeline in case of schema evolution, the pipeline design needs to answer the following questions:

1. Which schema changes are safe to do?
2. How to read data from a data stream in a future-proof way?
3. How to track the change history of a data stream?

[Schema Registry](https://docs.confluent.io/current/schema-registry/docs/index.html) is the most popular solution for Kafka-based data pipelines. Like an [Apache Hive](https://www.databricks.com/glossary/apache-hive) metastore, it records the schema of all the registered data streams, as well as the schema change history. It also defines multiple compatibility levels. For example, you can enforce that only backward-compatible schema changes are allowed.

To support reading data stream in a future-proof way, you need to embed the schema info in each record. Thus, the schema identifier, rather than a full schema, is part of each record. Schema Registry provides the custom Avro encoder/decoder. You can encode and decode the Avro records using the schema identifiers.

Databricks has integrated Schema Registry into the `from_avro` and `to_avro` functions. You can easily migrate your streaming pipelines, which are built on Schema Registry, to Spark Structured Streaming. Furthermore, the `from_avro` and `to_avro` functions can be used in batch queries as well, because Structured Streaming unifies batch and streaming processing in the [Spark SQL](https://www.databricks.com/glossary/what-is-spark-sql) engine.

## Sample Code for Using Schema Registry

You can import the notebook with the examples and play it with yourself, or preview it [online](https://docs.databricks.com/_static/notebooks/schema-registry-integration/index.html).

Assume you have already deployed Kafka and Schema Registry in your cluster, and there is a Kafka topic "t", whose key and value are registered in Schema Registry as subjects "t-key" and "t-value" of type string and int respectively.

The following code reads the topic "t" into a Spark DataFrame with schema ``

The following code writes the Spark DataFrame with schema ` into the Kafka topic "t"`.

## Read More

- Read more about Schema Registry for [Azure Databricks](https://docs.databricks.com/spark/latest/structured-streaming/avro-dataframe.html#avro-dataframe) and [AWS](https://docs.databricks.com/spark/latest/structured-streaming/avro-dataframe.html#avro-dataframe).
- Download the notebook or read it [here](https://docs.databricks.com/_static/notebooks/schema-registry-integration/index.html).
