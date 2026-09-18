# Parameterized queries with PySpark

- Source: https://www.databricks.com/blog/parameterized-queries-pyspark
- Published: 2024-01-03
- Authors: Matthew Powers, Daniel Tenedorio, Hyukjin Kwon
- Categories: engineering, open-source
- Images: 0 total, 0 extracted as architecture

PySpark has always provided wonderful SQL and Python APIs for querying data. As of Databricks Runtime 15.2 and Apache Spark 4.0, parameterized queries support safe and expressive ways to query data with SQL using Pythonic programming paradigms.

This post explains how to make parameterized queries with PySpark and when this is a good design pattern for your code.

Parameters are helpful for making your Spark code easier to reuse and test. They also encourage good coding practices. This post will demonstrate the two different ways to parameterize PySpark queries:

1. PySpark [custom string formatting](https://docs.python.org/3/library/string.html#custom-string-formatting)
2. [Parameter markers](https://docs.databricks.com/en/sql/language-manual/sql-ref-parameter-marker.html)

Let's look at how to use both types of PySpark parameterized queries and explore why the built-in functionality is better than other alternatives.

## Benefits of parameterized queries

Parameterized queries encourage the "don't repeat yourself" (DRY) pattern, make unit testing easier, and make SQL easier-to-reuse. They also prevent SQL injection attacks, which can pose security vulnerabilities.

It can be tempting to copy and paste large chunks of SQL when writing similar queries. Parameterized queries encourage abstracting patterns and writing code with the DRY pattern.

Parameterized queries are also easier to test. You can parameterize a query so it is easy to run on production and test datasets.

On the other hand, manually parameterizing SQL queries with Python f-strings is a poor alternative. Consider the following disadvantages:

1. Python f-strings do not protect against SQL injection attacks.
2. Python f-strings do not understand Python native objects such as DataFrames, columns, and special characters.

Let's look at how to parameterize queries with parameter markers, which protect your code from SQL injection vulnerabilities, and support automatic type conversion of common PySpark instances in string format.

## Parameterized queries with PySpark custom string formatting

Suppose you have the following data table called `h20_1e9` with nine columns:

You would like to parameterize the following SQL query:

You'd like to make it easy to run this query with different values of `id1`. Here's how to parameterize and run the query with different `id1` values.

Now rerun the query with another argument:

The PySpark string formatter also lets you execute SQL queries directly on a DataFrame without explicitly defining temporary views.

Suppose you have the following DataFrame called `person_df`:

Here's how to query the DataFrame with SQL.

Running queries on a DataFrame using SQL syntax without having to manually register a temporary view is very nice!

Let's now see how to parameterize queries with arguments in parameter markers.

## Parameterized queries with parameter markers

You can also use a dictionary of arguments to formulate a parameterized SQL query with parameter markers.

Suppose you have the following view named `some_purchases:`

Here's how to make a parameterized query with [named parameter markers](https://docs.databricks.com/en/sql/language-manual/sql-ref-parameter-marker.html#named-parameter-markers&language-python) to calculate the total amount spent on a given item.

Compute the total amount spent on socks.

You can also parameterize queries with [unnamed parameter markers](https://docs.databricks.com/en/sql/language-manual/sql-ref-parameter-marker.html#unnamed-parameter-markers); see here for more information.

Apache Spark sanitizes parameters markers, so this parameterization approach also protects you from SQL injection attacks.

## How PySpark sanitizes parameterized queries

Here's a high-level description of how Spark sanitizes the named parameterized queries:

- The SQL query arrives with an optional key/value parameters list.
- Apache Spark parses the SQL query and replaces the parameter references with corresponding parse tree nodes.
- During analysis, a Catalyst rule runs to replace these references with their provided parameter values from the parameters.
- This approach protects against SQL injection attacks because it only supports literal values. Regular string interpolation applies substitution on the SQL string; this strategy can be vulnerable to attacks if the string contains SQL syntax other than the intended literal values.

As previously mentioned, there are two types of parameterized queries supported in PySpark:

- Client-side parameterization using the {} syntax based on [PEP 3101](https://peps.python.org/pep-3101/) (we've been referring to this as custom string formatting).
- Server-side parameterization using either [named parameter](https://docs.databricks.com/en/sql/language-manual/sql-ref-parameter-marker.html#named-parameter-markers) markers or [unnamed parameter markers](https://docs.databricks.com/en/sql/language-manual/sql-ref-parameter-marker.html#unnamed-parameter-markers).

The `{}` syntax does a string substitution on the SQL query on the client side for ease of use and better programmability. However, it does not protect against SQL injection attacks since the query text is substituted before being sent to the Spark server.

Parameterization uses the `args` argument of the `sql()` API and passes the SQL text and parameters separately to the server. The SQL text gets parsed with the parameter placeholders, substituting the values of the parameters specified in the `args` in the analyzed query tree.

There are two flavors of server-side parameterized queries: named parameter markers and unnamed parameter markers. Named parameter markers use the :`<param_name>` syntax for placeholders. See the documentation for more information on how to use unnamed parameter markers.

## Parameterized queries vs. string interpolation

You can also use regular Python string interpolation to parameterize queries, but it's not as convenient.

Here's how we'd have to parameterize our previous query with Python f-strings:

This isn't as nice for the following reasons:

- It requires creating a temporary view.
- We need to represent the date as a string, not a Python date.
- We need to wrap the date in single quotes in the query to format the SQL string properly.
- This doesn't protect against SQL injection attacks.

In sum, built-in query parameterization capabilities are safer and more effective than string interpolation.

## Conclusion

PySpark parameterized queries give you new capabilities to write clean code with familiar SQL syntax. They're convenient when you want to query a Spark DataFrame with SQL. They let you use common Python data types like floating point values, strings, dates, and datetimes, which automatically convert to SQL values under the hood. In this manner, you can now leverage common Python idioms and write beautiful code.

Start leveraging PySpark parameterized queries today, and you will immediately enjoy the benefits of a higher quality codebase.

This feature is officially supported from DBR 15.2.
