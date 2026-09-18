# Joint Blog Post: Bringing ORC Support into Apache Spark

- Source: https://www.databricks.com/blog/2015/07/16/joint-blog-post-bringing-orc-support-into-apache-spark.html
- Published: 2015-07-16
- Authors: Zhan Zhang, Cheng Liang, Patrick Wendell
- Categories: engineering, open-source
- Images: 0 total, 0 extracted as architecture

This is a joint blog post with our partner Hortonworks. Zhan Zhang is a member of technical staff at Hortonworks, where he collaborated with the Databricks team on this new feature.

---

In version 1.2.0, Apache Spark introduced a [Data Source API](https://www.databricks.com/blog/2015/01/09/spark-sql-data-sources-api-unified-data-access-for-the-spark-platform.html) ([SPARK-3247](https://issues.apache.org/jira/browse/SPARK-3247)) to enable deep platform integration with a larger number of data sources and sinks. We are proud to announce that support for the Apache [Optimized Row Columnar](https://orc.apache.org/) (ORC) file format is included in Spark 1.4 as a new data source. This support was added through a collaboration between Hortonworks and Databricks, tracked by [SPARK-2883](https://issues.apache.org/jira/browse/SPARK-2883).

The Apache ORC file format and associated libraries recently became [a top level project](https://orc.apache.org/) at the Apache Software Foundation. ORC is a self-describing type-aware columnar file format designed for [Hadoop ecosystem](https://www.databricks.com/glossary/hadoop-ecosystem) workloads. The columnar format lets the reader read, decompress, and process only the columns that are required for the current query. In addition, it has support for ACID transactions and snapshot isolation, build-in indexes and complex types. Many large Hadoop deployments rely on ORC, including those at Yahoo! and Facebook.

Spark’s ORC support leverages recent improvements to the data source API included in Spark 1.4 ([SPARK-5180](https://issues.apache.org/jira/browse/SPARK-5180)). This API makes it easier to bring more data to Spark by simply providing new data source implementations. The API includes support for optimizations such as data partitioning and filter push-down. Since these concepts are now first class in the data source API, new data source implementations only need to focus on the data format specific logic in the physical plan execution without worrying about higher layer query plan optimization.

As ORC is one of the primary file formats supported in [Apache Hive](https://www.databricks.com/glossary/apache-hive), users of Spark’s SQL and DataFrame APIs will now have fast access to ORC data contained in Hive tables.

## Accessing ORC in Spark

Spark’s ORC data source supports complex data types (i.e., array, map, and struct), and provides read and write access to ORC files. It leverages Spark SQL's Catalyst engine to do common optimizations, such as column pruning, predicate push-down, and partition pruning, etc.

We’ll now give several examples of Spark’s ORC integration and show how such optimizations are applied to user programs. To get started, Spark’s ORC support requires only a HiveContext instance:

Our examples will use a few data structures to demonstrate working with complex types. The **Person** struct has name, age, and a sequence of **Contact**’s, which are themselves defined by names and phone numbers.

We create 100 records as below to be used in our example. In the physical file, they will be saved in the columnar format, but users still see rows when accessing ORC files via DataFrame API. Each row represents one Person record.

## Reading and Writing with ORC

Spark’s **DataFrameReader** and **DataFrameWriter** are used to access ORC files, in a similar manner to other data sources.

We can write People objects as ORC files to directory “people” using

Furthermore, we can read it back by

For reuse in future operations, we register it as a temporary table “people” as below:

## Column Pruning

Now the table is registered as a temporary table named “people”. The following SQL query references two columns from the underlying table. At runtime, the physical table scan will only load columns **name** and **age**, without reading the **contacts** column from the file system, and thus speeds up read performance:

## Predicate Push-down

The columnar nature of the ORC format helps to avoid reading unnecessary columns. However, we are still reading unnecessary rows even if the query has *WHERE* clause filter. In our example, we have to read all rows with age between 0 and 100, although only the rows with age less than 15 are required and all others will be discarded.  Such full table scanning is an expensive operation. ORC is able to avoid this type of overhead by performing predicate push-down with its build-in indexes.  ORC provides three level of indexes within each file, file level, stripe level, and row level. The file and stripe level statistics are in the file footer so that they are easy to access to determine if the rest of the file needs to be read at all. Row level indexes include both column statistics for each row group and position for seeking to the start of the row group. ORC utilizes these indexes to moves the filter operation to the data loading phase by only reading the data that potentially includes required rows.. The combination of indexed data and columnar storage reduces disk IO significantly, especially for larger datasets where IO bandwidth becomes the main bottleneck for performance. By default, ORC predicate push-down is disabled in the Spark SQL and need to be explicitly enabled:

## Partition Pruning

When predicate pushdown is not applicable, for example if all stripes containing records matching the predicate condition, a query with *WHERE* clause filter may need to read the entire data set, which becomes a bottleneck over a large table. Partition pruning is another optimization method that can avoid reading large amounts of data by exploiting query semantics.

Partition pruning is possible when data within a table is split across multiple logical partitions. Each partition corresponds to a particular value(s) of partition column(s) and is stored as a sub-directory within the table’s root directory on HDFS. When the table is queried, where applicable, only the required partitions (subdirectories) of the table are queried, thereby avoiding unnecessary IO.

Spark supports saving data out in a partitioned layout seamlessly, through the **partitionBy **method available during data source writes. In this example we partition the people table by the “age” column:

Records will be automatically partitioned by the age field and saved into different directories, for example, peoplePartitioned/age=1/, peoplePartitioned/age=2/, etc.

After partitioning the data, future queries which access the data will be able to skip large amounts of IO when the partition column is referenced in predicates. For example, following query will automatically locate and load the file under peoplePartitioned/age=20/ only, and skip all others.

## DataFrame Support

Spark 1.3 added a new DataFrame API. DataFrames look similar to Spark’s RDDs, but have higher level semantics built into their operators, allowing optimization to be pushed down to the underlying query engine. ORC data can be conveniently loaded into DataFrames.

Here's the Scala API translation of the SELECT query above using the DataFrame API

val sqlContext = new org.apache.spark.sql.hive.HiveContext(sc)
 sqlContext.setConf("spark.sql.orc.filterPushdown", "true")
 val people = sqlContext.read.format("orc").load("peoplePartitioned")
 people.filter(people("age")sqlContext = HiveContext(sc)
 sqlContext.setConf("spark.sql.orc.filterPushdown", "true")
 people = sqlContext.read.format("orc").load("peoplePartitioned")
 people.filter(people.age
 That's it! Simply save your data in ORC, adopt the DataFrame API for working with datasets, and you can significantly speedup queries over large datasets. And we haven't even looked at the compression and run-length encoding features yet—both of which can reduce the IO bandwidth even further.

## Putting It All Together

We've just given a quick overview of how Spark 1.4 supports ORC files. The combination of the ORC storage format, optimized for query performance, and the DataFrame API means that Spark applications can work with data stored in ORC files as easily as any other data source, yet gain significant performance advantages compared to unoptimized storage formats. And because it can also be used by other tools and applications in the Hadoop stack, ORC-formatted data generated by other parts of a large system, can be easily consumed by Spark applications and other interactive tools.

## What’s Next?

Currently, the code for Spark SQL ORC support is under package org.apache.spark.sql.hive and must be used together with Spark SQL's HiveContext. This is because ORC is still tightly coupled with Hive for now. However, it doesn't require existing Hive installation to access ORC files.

Now that ORC has already become an independent Apache top level project. After decoupling ORC from Hive, Hive dependencies will not be necessary to access ORC files.

We look forward to helping producing a future version of Apache Spark which makes ORC even easier to work with.

## Further Information

If you want to know more about Spark's ORC Support, [download Apache Spark](https://spark.apache.org/) 1.4.0 or later versions, and explore the new features through the [DataFrame API](https://spark.apache.org/docs/latest/sql-programming-guide.html).

## References

- Apache ORC website: [https://orc.apache.org/](https://orc.apache.org/)
- ORC performance: [https://blog.cloudera.com/orcfile-in-hdp-2-better-compression-better-performance/](https://blog.cloudera.com/orcfile-in-hdp-2-better-compression-better-performance/)
