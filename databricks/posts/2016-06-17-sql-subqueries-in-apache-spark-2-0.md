# SQL Subqueries in Apache Spark 2.0

- Source: https://www.databricks.com/blog/2016/06/17/sql-subqueries-in-apache-spark-2-0.html
- Published: 2016-06-17
- Authors: Davies Liu, Herman van Hövell
- Categories: engineering, open-source
- Images: 1 total, 0 extracted as architecture

[Try this notebook in Databricks](https://databricks-prod-cloudfront.cloud.databricks.com/public/4027ec902e239c93eaaa8714f173bcfc/2728434780191932/1483312212640900/6987336228780374/latest.html)

In the upcoming Apache Spark 2.0 release, we have substantially expanded the SQL standard capabilities. In this brief blog post, we will introduce subqueries in Apache Spark 2.0, including their limitations, potential pitfalls and future expansions, and through a notebook, we will explore both the scalar and predicate type of subqueries, with short examples that you can try yourself.

A subquery is a query that is nested inside of another query. A subquery as a source (inside a `SQL FROM` clause) is technically also a subquery, but it is beyond the scope of this post. There are basically two kinds of subqueries: scalar and predicate subqueries. And within scalar and predicate queries, there are uncorrelated scalar and correlated scalar queries and nested predicate queries respectively.

For brevity, we will let you jump and explore the notebook, which is more an interactive experience rather than an exposition here in the blog. Click on this diagram below to view and explore the subquery notebook with [Apache Spark 2.0 preview](https://spark.apache.org/news/spark-2.0.0-preview.html) on Databricks.

## What’s Next

Subquery support in Apache Spark 2.0 provides a solid solution for the most common subquery usage scenarios. However, there is room for improvement in the areas noted in detail at the end of [the notebook](https://databricks-prod-cloudfront.cloud.databricks.com/public/4027ec902e239c93eaaa8714f173bcfc/2728434780191932/1483312212640900/6987336228780374/latest.html).

To try this notebook on Databricks, sign up now.
