# Announcing Apache Spark 1.3!

- Source: https://www.databricks.com/blog/2015/03/13/announcing-spark-1-3.html
- Published: 2015-03-13
- Authors: Patrick Wendell
- Categories: engineering, open-source, data-science-machine-learning
- Images: 0 total, 0 extracted as architecture

Today I’m excited to announce the general availability of Apache Spark 1.3! Apache Spark 1.3 introduces the widely anticipated DataFrame API, an evolution of Spark’s RDD abstraction designed to make crunching large datasets simple and fast. Apache Spark 1.3 also boasts a large number of improvements across the stack, from Streaming, to ML, to SQL. The release has been posted today on the Apache Spark website.

We’ll be publishing in depth overview posts covering Spark’s new features over the coming weeks. Some of the salient features of this release are:

## A new DataFrame API

The DataFrame API that we [recently announced](https://www.databricks.com/blog/2015/02/17/introducing-dataframes-in-spark-for-large-scale-data-science.html) officially ships in Apache Spark 1.3. DataFrames evolve Spark’s RDD model, making operations with structured datasets even faster and easier. They are inspired by, and fully interoperable with, Pandas and R data frames, and are available in Spark’s Java, Scala, and Python API’s as well as the upcoming (unreleased) R API. DataFrames introduce new simplified operators for filtering, aggregating, and projecting over large datasets. Internally, DataFrames leverage the Spark SQL logical optimizer to intelligently plan the physical execution of operations to work well on large datasets. This planning permeates all the way into physical storage, where optimizations such as predicate pushdown are applied based on analysis of user programs. Read more about the data frames API in the SQL programming guide.

## Spark SQL Graduates from Alpha

Spark SQL graduates from an alpha component in this release, guaranteeing compatibility for the SQL dialect and semantics in future releases. Spark SQL’s data source API now fully interoperates with the new DataFrame component, allowing users to create DataFrames directly from Hive tables, Parquet files, and other sources. Users can also intermix SQL and data frame operators on the same data sets. New in 1.3 is the ability to read and write tables from a JDBC connection, with native support for Postgres and MySQL and other RDBMS systems. That API adds has write support for producing output tables as well, to JDBC or any other source.

## Built-in Support for Spark Packages

We [earlier announced](https://www.databricks.com/blog/2014/12/22/announcing-spark-packages.html) an initiative to create a community package repository for Spark at the end of 2014. Today [Spark Packages](https://spark-packages.org/) has 45 community projects catering to Spark developers, including data source integrations, testing utilities, and tutorials. To make packages easy for Spark users, Apache Spark 1.3 includes support for pulling published packages into the Spark shell or a program with a single flag.

For developers, Spark Packages has also created an [SBT plugin](https://github.com/databricks/sbt-spark-package) to make publishing packages easy and introduced automatic Spark compatibility checks of new releases.

## Lower Level Kafka Support in Spark Streaming

Over the last few releases, Kafka has become a popular input source for Spark streaming. Apache Spark 1.3 adds a new Kakfa streaming source that leverages Kafka’s replay capabilities to provide reliable delivery semantics without the use of a write ahead log. It also provides primitives which enable exactly once guarantees for applications that have strong consistently requirements. Kafka support adds a Python API in this release, along with new primitives for creating Python API’s in the future. For a full list of Spark streaming features see the upstream release notes.

## New Algorithms in MLlib

Apache Spark 1.3 provides a rich set of new algorithms. The latent Dirichlet allocation (LDA) is one of the first topic modeling algorithms to appear in MLlib. We’ll be documenting LDA in more detail in a follow-up post. Spark’s logistic regression has been generalized to multinomial logistic regression for multiclass classification. This release also adds improved clustering through Gaussian mixture models and power iteration clustering, and frequent itemsets mining through FP-growth. Finally, an efficient block matrix abstraction is introduced for distributed linear algebra. Several other algorithms and utilities are added and discussed in the full release notes.

## Related in-depth blog posts:

- [What’s new for Spark SQL in Spark 1.3](https://www.databricks.com/blog/2015/03/24/spark-sql-graduates-from-alpha-in-spark-1-3.html)
- [Topic modeling with LDA: MLlib meets GraphX](https://www.databricks.com/blog/2015/03/25/topic-modeling-with-lda-mllib-meets-graphx.html)
- [Improvements to Kafka integration of Spark Streaming](https://www.databricks.com/blog/2015/03/30/improvements-to-kafka-integration-of-spark-streaming.html)

---

This post only scratches the surface of interesting features in Apache Spark 1.3. Overall, this release contains more than 1000 patches from 176 contributors making it our largest yet. Head over to the [official release notes](https://spark.apache.org/releases/spark-release-1-3-0.html) to learn more about this release, and watch the Databricks blog for more detailed posts about the major features in the next few weeks!
