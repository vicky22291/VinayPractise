# Five Spark SQL Utility Functions to Extract and Explore Complex Data Types

- Source: https://www.databricks.com/blog/2017/06/13/five-spark-sql-utility-functions-extract-explore-complex-data-types.html
- Published: 2017-06-13
- Authors: Jules Damji
- Categories: engineering, open-source, data-engineering
- Images: 1 total, 0 extracted as architecture

[Try this notebook on Databricks](https://docs.databricks.com/_static/notebooks/complex-nested-structured.html)

For developers, often the ***how*** is as important as the ***why***. While our in-depth blog explains the [concepts and motivations](https://www.databricks.com/blog/2017/02/23/working-complex-data-formats-structured-streaming-apache-spark-2-1.html) of *why* handling complex data types and formats are important, and equally explains their utility in processing complex data structures, this blog post is a preamble to the *how* as a [notebook tutorial](https://docs.databricks.com/_static/notebooks/complex-nested-structured.html).

In this tutorial, I show and share ways in which you can explore and employ five [Spark SQL](https://www.databricks.com/glossary/what-is-spark-sql) utility functions and APIs. Introduced in Apache Spark 2.x as part of [*org.apache.spark.sql.functions*,](https://spark.apache.org/docs/latest/api/scala/index.html#org.apache.spark.sql.functions$) they enable developers to easily work with complex data or nested data types.

In particular, they come in handy while doing Streaming ETL, in which data are JSON objects with complex and nested structures: Map and Structs embedded as JSON. This notebook tutorial focuses on the following Spark SQL functions:

- [*get_json_object()*](https://spark.apache.org/docs/latest/api/scala/index.html#org.apache.spark.sql.functions$)
- [*from_json()*](https://spark.apache.org/docs/latest/api/scala/index.html#org.apache.spark.sql.functions$)
- [*to_json()*](https://spark.apache.org/docs/latest/api/scala/index.html#org.apache.spark.sql.functions$)
- [*explode()*](https://spark.apache.org/docs/latest/api/scala/index.html#org.apache.spark.sql.functions$)
- [*selectExpr()*](https://spark.apache.org/docs/latest/api/scala/index.html#org.apache.spark.sql.functions$)

To give you a glimpse, consider this nested schema that defines what your IoT events may look like coming down an Apache Kafka stream or deposited in a data source of your choice.

[code_tabs]

[/code_tabs]

And its corresponding sample DataFrame/Dataset data may look as follows:

[code_tabs]

[/code_tabs]

If you examine the respective schemas in Scala or Python notebook, you can see the nested structures:

[code_tabs]

[/code_tabs]

I use a sample of these JSON event data from IoT and Nest devices to illustrate how to use these functions. The takeaway from this tutorial is that there are myriad ways to slice and dice nested JSON structures with Spark SQL utility functions, namely the aforementioned list.

*[nest image source](https://developers.nest.com/documentation/api-reference)*

Since I would be repeating here what I already demonstrated in the notebook, I encourage that you explore the [accompanying notebook](https://docs.databricks.com/_static/notebooks/complex-nested-structured.html), import it into your Databricks workspace, and have a go at it.

## What's Next?

In a follow-up tutorial on [Higher Order Functions](https://www.databricks.com/blog/2017/05/24/working-with-nested-data-using-higher-order-functions-in-sql-on-databricks.html), I'll explore how to use these powerful SQL functions to manipulate structured data.

If you don’t have a Databricks account, get one [Databricks today](https://www.databricks.com/try-databricks).
