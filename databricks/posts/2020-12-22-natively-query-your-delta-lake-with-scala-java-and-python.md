# Natively Query Your Delta Lake With Scala, Java, and Python

*Use Delta Standalone Reader and the Delta Rust API to query your Delta Lake without Apache Spark*

- Source: https://www.databricks.com/blog/2020/12/22/natively-query-your-delta-lake-with-scala-java-and-python.html
- Published: 2020-12-22
- Authors: Shixiong Zhu, Scott Sandre, Denny Lee
- Categories: engineering, open-source
- Images: 1 total, 0 extracted as architecture

Today, we’re happy to announce that you can natively query your Delta Lake with Scala and Java (via the Delta Standalone Reader) and Python (via the [Delta Rust API](https://github.com/delta-io/delta.rs)). Delta Lake is an open-source storage layer that brings reliability to data lakes. Delta Lake provides ACID transactions, scalable metadata handling, and unifies streaming and batch data processing. Delta Lake runs on top of your existing data lake and is fully compatible with Apache Spark™ APIs. The project has been deployed at thousands of organizations and processes more **exabytes of data each week**, becoming an indispensable pillar in data and AI architectures. More than 75% of the data scanned on the Databricks Data + AI Platform is on Delta Lake!

In addition to Apache Spark, Delta Lake has integrations with Amazon Redshift, Redshift Spectrum, Athena, Presto, Hive, and more; you can find more information in the [Delta Lake Integrations](https://docs.delta.io/latest/integrations.html). For this blog post, we will discuss the most recent release of the Delta Standalone Reader and the [Delta Rust API](https://github.com/delta-io/delta.rs) that allows you to query your Delta Lake with Scala, Java, and Python without Apache Spark.

 

 Get an early preview of [O'Reilly's new ebook](https://www.databricks.com/resources/ebook/delta-lake-running-oreilly?itm_data=querydlscalapython-blog-oreillydlupandrunning) for the step-by-step guidance you need to start using Delta Lake.

## Delta Standalone Reader

The Delta Standalone Reader (DSR) is a JVM library that allows you to read Delta Lake tables without the need to use Apache Spark; i.e. it can be used by any application that cannot run Spark. The motivation behind creating DSR is to enable [better integrations with other systems](https://docs.delta.io/latest/integrations.html) such as Presto, Athena, Redshift Spectrum, Snowflake, and [Apache Hive](https://www.databricks.com/glossary/apache-hive). For Apache Hive, we rewrote it using DSR to get rid of the embedded Spark in the new release.

To use DSR using `sbt` include `delta-standalone` as well as hadoop-client and parquet-hadoop.

`libraryDependencies ++= Seq(
 "io.delta" %% "delta-standalone" % "0.2.0",
 "org.apache.hadoop" % "hadoop-client" % "2.7.2",
 "org.apache.parquet" % "parquet-hadoop" % "1.10.1")`

## Using DSR to query your Delta Lake table

Below are some examples of how to query your Delta Lake table in Java.

### Reading the Metadata

After importing the necessary libraries, you can determine the table version and associated metadata (number of files, size, etc.) as noted below.

## Reading the Delta Table

To query the table, open a snapshot and then iterate through the table as noted below.

### Requirements

DSR has the following requirements:

- JDK 8 or above
- Scala 2.11 or Scala 2.12
- Dependencies on `parquet-hadoop` and `hadoop-client `

For more information, please refer to the Java API docs or Delta Standalone Reader wiki.

## Delta Rust API

[delta.rs](https://github.com/delta-io/delta.rs) is an experimental interface to Delta Lake for Rust. This library provides low-level access to Delta tables and is intended to be used with data processing frameworks like datafusion, ballista, [rust-dataframe](https://github.com/nevi-me/rust-dataframe), and [vega](https://github.com/rajasekarv/vega). It can also act as the basis for native bindings in other languages such as Python, Ruby, or Golang.

QP Hou and R. Tyler Croy at Scribd use [Delta Lake to enable the world’s largest digital library](https://www.databricks.com/blog/2020/11/20/how-scribd-uses-delta-lake-to-enable-the-worlds-largest-digital-library.html) are the initial creators of this API. The Delta Rust API has quickly gained traction in the community with a special callout of community-driven [Azure support](https://github.com/delta-io/delta-rs/pull/34) within weeks after the initial release.

## Reading the Metadata (Cargo)

You can use the API or CLI to inspect the files of your Delta Lake table as well as provide the metadata information; below are sample commands using the CLI via cargo. Once the 0.2.0 release of [delta.rs](https://github.com/delta-io/delta.rs) has been published, `cargo install deltalake` will provide the delta-inspect binary.

To inspect the files, check out the source and use delta-inspect files:

`❯ cargo run --bin delta-inspect files ./tests/data/delta-0.2.0`

`part-00000-cb6b150b-30b8-4662-ad28-ff32ddab96d2-c000.snappy.parquet
 part-00000-7c2deba3-1994-4fb8-bc07-d46c948aa415-c000.snappy.parquet
 part-00001-c373a5bd-85f0-4758-815e-7eb62007a15c-c000.snappy.parquet`

To inspect the metadata, use delta-inspect info:

`❯ cargo run --bin delta-inspect info ./tests/data/delta-0.2.0
 DeltaTable(./tests/data/delta-0.2.0)
 version: 3
 metadata: GUID=22ef18ba-191c-4c36-a606-3dad5cdf3830, name=None, description=None, partitionColumns=[], configuration={}
 min_version: read=1, write=2
 files count: 3`

### Reading the Metadata (Python)

You can also use the [delta.rs](https://github.com/delta-io/delta.rs/)to query Delta Lake using Python via the [delta.rs Python bindings](https://github.com/delta-io/delta.rs/tree/main/python).

To obtain the Delta Lake version and files, use the .version() and .files() methods respectively.

`from deltalake import DeltaTable
 dt = DeltaTable("../rust/tests/data/delta-0.2.0")`

`# Get the Delta Lake Table version
 dt.version()`

`# Example Output
 3`

`# List the Delta Lake table files
 dt.files()`

`# Example Output
 ['part-00000-cb6b150b-30b8-4662-ad28-ff32ddab96d2-c000.snappy.parquet', 'part-00000-7c2deba3-1994-4fb8-bc07-d46c948aa415-c000.snappy.parquet', 'part-00001-c373a5bd-85f0-4758-815e-7eb62007a15c-c000.snappy.parquet']`

### Reading the Delta Table (Python)

To read a Delta table using the delta.rs Python bindings, you will need to convert the Delta table into a PyArrow Table and [Pandas Dataframe](https://www.databricks.com/glossary/pandas-dataframe).

### Notes

Currently, you can also query your Delta Lake table through delta.rs using Python and Ruby, but the underlying Rust APIs should be straightforward to integrate into Golang or other languages too.. Refer to delta.rs for more information. There's lots of opportunity to contribute to Delta.rs, so be sure to check out the open issues! https://github.com/delta-io/delta.rs/issues

## Discussion

We’d like to thank Scott Sandre and the Delta Lake Engineering team for creating the Delta Standalone Reader and QP Hou and R. Tyler Croy for creating the [Delta Rust API](https://github.com/delta-io/delta.rs). Try out the Delta Standalone Reader and Delta Rust API today - no Spark required!

Join us in the Delta Lake community through our Public Slack Channel ([Register here](https://join.slack.com/t/delta-users/shared_invite/zt-ngdxlkxh-c~rjOonFCDS2xve_lx3TIA)| [Log in here](https://delta-users.slack.com/)) or [Public Mailing list](https://delta-users.slack.com/).
