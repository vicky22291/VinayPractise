# How to Monitor Streaming Queries in PySpark

- Source: https://www.databricks.com/blog/2022/05/27/how-to-monitor-streaming-queries-in-pyspark.html
- Published: 2022-05-27
- Authors: Hyukjin Kwon, Karthik Ramasamy, Alexander Balikov
- Categories: engineering, open-source, data-streaming
- Images: 1 total, 0 extracted as architecture

[Streaming](https://www.databricks.com/product/data-streaming) is one of the most important data processing techniques for ingestion and analysis. It provides users and developers with low latency and real-time data processing capabilities for analytics and triggering actions. However, monitoring streaming data workloads is challenging because the data is continuously processed as it arrives. Because of this always-on nature of stream processing, it is harder to troubleshoot problems during development and production without real-time metrics, alerting and dashboarding.

Structured Streaming in Apache Spark™ addresses the problem of monitoring by providing:

- A [Dedicated UI](https://spark.apache.org/docs/latest/web-ui.html#structured-streaming-tab) with real-time metrics and statistics. For more information, see [A look at the new Structured Streaming UI in Apache Spark 3.0.](https://www.databricks.com/blog/2020/07/29/a-look-at-the-new-structured-streaming-ui-in-apache-spark-3-0.html)
- An [Observable API](https://spark.apache.org/docs/latest/api/scala/org/apache/spark/sql/Dataset.html#observe(name:String,expr:org.apache.spark.sql.Column,exprs:org.apache.spark.sql.Column*):org.apache.spark.sql.Dataset%5BT%5D) that allows for advanced monitoring capabilities such as alerting and/or dashboarding with an external system.

Until now, the Observable API has been missing in PySpark, which forces users to use the Scala API for their streaming queries to avail the functionality of alerting and dashboarding with other external systems. The lack of this functionality in Python has become more critical as the importance of Python grows, given that [almost 70% of notebook commands run on Databricks are in Python](https://www.databricks.com/blog/2020/06/18/introducing-apache-spark-3-0-now-available-in-databricks-runtime-7-0.html).

In Databricks Runtime 11, we're happy to announce that the Observable API is now available in PySpark. In this blog post, we introduce the Python Observable API for Structured Streaming, along with a step-by-step example of a scenario that adds alerting logic into a streaming query.

## Observable API

Developers can now send streaming metrics to external systems, e.g., for alerting and dashboarding with custom metrics, using a combination of the streaming query listener interface and the Observable API in PySpark. The Streaming Query Listener interface is an abstract class that has to be inherited and should implement all methods as shown below:

Note that they all work asynchronously.

- `StreamingQueryListener.onQueryStarted` is triggered when a streaming query is started, e.g., `DataStreamWriter.start`.
- `StreamingQueryListener.onQueryProgress` is invoked when each micro-batch execution is finished.
- `StreamingQueryListener.onQueryTerminated` is called when the query is stopped, e.g., `StreamingQuery.stop`.

The listener has to be added in order to be activated via `StreamingQueryManager` and can also be removed later as shown below:

In order to capture custom metrics, they have to be added via `DataFrame.observe`. The custom metrics are defined as arbitrary aggregate functions such as `count("value")` as shown below.

## Error Alert Scenario

In this section, we will describe an example of a real world use case with the Observable API. Suppose you have a directory where new CSV files are continuously arriving from another system, and you have to ingest them in a streaming fashion. In this example, we will use a local file system for simplicity so that the API can be easily understood. The code snippets below can be copied and pasted in the `pyspark` shell for you to run and try out.

First, let's import the necessary Python classes and packages, then create a directory called `my_csv_dir` that will be used in this scenario.

Next, we define our own custom streaming query listener. The listener will alert when there are too many malformed records during CSV ingestion for each process. If the malformed records are more than 50% of the total count of processed records, we will print out a log message. However, in production scenarios, you can connect to the external systems instead of simply printing out.

To activate the listener, we add it before the query in this example. However, it is important to note that you can add the listener regardless of the query start and termination because they work asynchronously. This allows you to attach and detach to your running streaming queries without halting them.

Now we will start a streaming query that ingests the files in `my_csv_dir` directory. During processing, we also observe the number of malformed records and processed records. The CSV data source stores malformed records at `_corrupt_record`, by default, so we will count the column for the number of malformed records.

Now that we have defined the streaming query and the alerting capabilities, let's create CSV files so they can be ingested in a streaming fashion:

Here we will see that the query start, termination and processes are logged properly. Because there are two malformed records in the CSV files, the alert is raised properly with the following error message:

`...
ALERT! Ouch! there are too many malformed records 2 out of 3!
 ...`

## Conclusion

PySpark users are now able to set their custom metrics and observe them via the streaming query listener interface and Observable API. They can attach and detach such logic into running queries dynamically when needed. This feature addresses the need for dashboarding, alerting and reporting to other external systems.

The Streaming Query Listener interface and Observable API are available in DBR 11 Beta, and expected to be available in the future Apache Spark. Try out both new capabilities today on Databricks through DBR 11 Beta.
