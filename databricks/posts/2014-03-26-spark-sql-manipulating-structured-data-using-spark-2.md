# Spark SQL: Manipulating Structured Data Using Apache Spark

- Source: https://www.databricks.com/blog/2014/03/26/spark-sql-manipulating-structured-data-using-spark-2.html
- Published: 2014-03-26
- Authors: Michael Armbrust, Reynold Xin
- Categories: engineering, open-source
- Images: 0 total, 0 extracted as architecture

[Read Rise of the Data Lakehouse](https://www.databricks.com/resources/ebook/rise-data-lakehouse?itm_data=sparksqlmanipulatingstructureddataspark2-blog-riselakehousebook) to explore why lakehouses are the data architecture of the future with the father of the data warehouse, Bill Inmon.

---

Building a unified platform for [big data analytics](https://www.databricks.com/glossary/big-data-analytics) has long been the vision of Apache Spark, allowing a single program to perform ETL, [MapReduce](https://www.databricks.com/glossary/mapreduce), and complex analytics. An important aspect of unification that our users have consistently requested is the ability to more easily import data stored in external sources, such as [Apache Hive](https://www.databricks.com/glossary/apache-hive). Today, we are excited to announce [Spark SQL](https://spark.apache.org/docs/latest/sql-programming-guide.html), a new component recently merged into the Spark repository.

Spark SQL brings native support for SQL to Spark and streamlines the process of querying data stored both in RDDs (Spark’s distributed datasets) and in external sources. Spark SQL conveniently blurs the lines between RDDs and relational tables. Unifying these powerful abstractions makes it easy for developers to intermix SQL commands querying external data with complex analytics, all within in a single application. Concretely, Spark SQL will allow developers to:

- Import relational data from Parquet files and Hive tables
- Run SQL queries over imported data and existing RDDs
- Easily write RDDs out to Hive tables or Parquet files

## Spark SQL In Action

Now, let’s take a closer look at how Spark SQL gives developers the power to integrate SQL commands into applications that also take advantage of MLlib, Spark’s [machine learning library](https://www.databricks.com/glossary/what-is-machine-learning-library). Consider an application that needs to predict which users are likely candidates for a service, based on their profile. Often, such an analysis requires joining data from multiple sources. For the purposes of illustration, imagine an application with two tables:

- Users(userId INT, name String, email STRING,
 age INT, latitude: DOUBLE, longitude: DOUBLE,
 subscribed: BOOLEAN)
- Events(userId INT, action INT)

Given the data stored in in these tables, one might want to build a model that will predict which users are good targets for a new campaign, based on users that are similar.

// Data can easily be extracted from existing sources,
 // such as Apache Hive.
 val trainingDataTable = sql("""
 SELECT e.action
 u.age,
 u.latitude,
 u.logitude
 FROM Users u
 JOIN Events e
 ON u.userId = e.userId""")

// Since `sql` returns an RDD, the results of the above
 // query can be easily used in MLlib
 val trainingData = trainingDataTable.map { row =>
 val features = Array[Double](row(1), row(2), row(3))
 LabeledPoint(row(0), features)
 }

val model =
 new LogisticRegressionWithSGD().run(trainingData)

Now that we have used SQL to join existing data and train a model, we can use this model to predict which users are likely targets.

val allCandidates = sql("""
 SELECT userId,
 age,
 latitude,
 logitude
 FROM Users
 WHERE subscribed = FALSE""")

// Results of ML algorithms can be used as tables
 // in subsequent SQL statements.
 case class Score(userId: Int, score: Double)
 val scores = allCandidates.map { row =>
 val features = Array[Double](row(1), row(2), row(3))
 Score(row(0), model.predict(features))
 }
 scores.registerAsTable("Scores")

val topCandidates = sql("""
 SELECT u.name, u.email
 FROM Scores s
 JOIN Users u ON s.userId = u.userId
 ORDER BY score DESC
 LIMIT 100""")

// Send emails to top candidates to promote the service.

In this example, Spark SQL made it easy to extract and join the various datasets preparing them for the machine learning algorithm. Since the results of Spark SQL are also stored in RDDs, interfacing with other Spark libraries is trivial. Furthermore, Spark SQL allows developers to close the loop, by making it easy to manipulate and join the output of these algorithms, producing the desired final result.

To summarize, the unified Spark platform gives developers the power to choose the right tool for the right job, without having to juggle multiple systems. If you would like to see more concrete examples of using Spark SQL please check out the programming guide.

## Optimizing with Catalyst

In addition to providing new ways to interact with data, Spark SQL also brings a powerful new optimization framework called Catalyst. Using Catalyst, Spark can automatically transform SQL queries so that they execute more efficiently. The Catalyst framework allows the developers behind Spark SQL to rapidly add new optimizations, enabling us to build a faster system more quickly. In one recent example, we found an inefficiency in Hive group-bys that took an experienced developer an entire weekend and over 250 lines of code to fix; we were then able to make the same fix in Catalyst in only a few lines of code.

## Future of Shark

The natural question that arises is about the future of Shark. Shark was among the first systems that delivered up to 100X speedup over Hive. It builds on the Apache Hive codebase and achieves performance improvements by swapping out the physical execution engine part of Hive. While this approach enables Shark users to speed up their Hive queries without modification to their existing warehouses, Shark inherits the large, complicated code base from Hive that makes it hard to optimize and maintain. As Spark SQL matures, Shark will transition to using Spark SQL for query optimization and physical execution so that users can benefit from the ongoing optimization efforts within Spark SQL.

In short, we will continue to invest in Shark and make it an excellent drop-in replacement for Apache Hive. It will take advantage of the new Spark SQL component, and will provide features that complement it, such as Hive compatibility and the standalone SharkServer, which allows external tools to connect queries through JDBC/ODBC.

## What’s next

Spark SQL will be included in Spark 1.0 as an alpha component. However, this is only the beginning of better support for relational data in Spark, and this post only scratches the surface of Catalyst. Look for future blog posts on the following topics:

- Generating custom bytecode to speed up expression evaluation
- Reading and writing data using other formats and systems, include Avro and HBase
- API support for using Spark SQL in Python and Java
