# SQL Gets Easier: Announcing New Pipe Syntax

*Make SQL simpler and stronger by expressing all transformations in order*

- Source: https://www.databricks.com/blog/sql-gets-easier-announcing-new-pipe-syntax
- Published: 2025-04-30
- Authors: Daniel Tenedorio
- Categories: engineering
- Images: 0 total, 0 extracted as architecture

**Key takeaways**

- SQL is successful because the language declares what data should come out of each query without specifying exactly how the engine should execute it.
- However, SQL can get confusing for new users to learn and for existing users to maintain, especially in the presence of many nested subqueries.
- Here we announce a new syntax to help with this by letting users compose SQL logic as a sequence of independent clauses arranged in any order, much like DataFrames.

SQL has been the lingua franca for structured data analysis for multiple decades, and we have done a lot of work in the last few years to support ANSI SQL and the various extensions to make SQL more delightful to use on Databricks. Today, we are excited to announce [SQL pipe syntax](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-syntax-qry-pipeline), the largest extension that we have done in recent years to make SQL dramatically easier to write and understand, in a fully backward compatible way.

One of the key challenges in SQL itself so far lies in the ordering of the “logic.” When writing a query, many authors think in terms of the following logical steps: identify the list of tables to query, join them together, filter out unwanted rows, and finally, aggregate. This logical ordering can be expressed in the following way:

The SQL query for these steps would look like this:

Instead of writing the steps in order (1, 2, 3) we must instead write them in the order (3, 2, 1). This is confusing and the problem only compounds as we add more logic and steps to each query.

## DataFrames and the people who love them

In contrast, let’s think about DataFrames. A big source of Apache Spark’s original popularity among data scientists is the powerful capability of its Scala and Python DataFrame APIs. Programs can apply these to express their logic in a natural ordering of steps. Starting from the source table, users can chain together independent and composable operations one after the other, making it easier to build complex data transformations in a clear and intuitive sequence.

This design promotes readability and simplifies debugging while maintaining flexibility. It is a major reason why Databricks has earned its massive growth in the industry so far in the data management space, and this momentum only continues to increase today.

Here’s how that same logic looks like in PySpark DataFrames:

This approach supports flexible iteration on ideas. We know that the source data exists in some file, so we can start right away by creating a DataFrame representing that data as a relation. After thinking for a bit, we realize that we want to filter the rows by the string column. OK, so we can add a .filter step to the end of the previous DataFrame. Oh, and we want to compute a projection at the end, so we add that at the end of the sequence.

Many of these users wish SQL would behave more similarly to modern data languages like this. Historically, this was not possible, and users had to choose one way of thinking or the other.

## Introducing new SQL pipe syntax!

Fast forward to today: it’s now possible to have the best of both worlds! Pipe syntax makes SQL both easier to write and also read and extend later, and frees us from this confusion by letting us simply use the same steps in the order that we thought about them.

In the [VLDB 2024 conference](https://vldb.org/2024/), Google published an [industrial paper](https://research.google/pubs/sql-has-problems-we-can-fix-them-pipe-syntax-in-sql/) proposing this as a new standard. Query processing engineers have implemented this functionality and enabled it by default in Apache Spark 4.0 ([documentation](https://github.com/apache/spark/blob/76a423955a8badfd82fe8fa88c76fba96adf8236/docs/sql-pipe-syntax.md)) and Databricks Runtime 16.2 ([documentation](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-syntax-qry-pipeline)) and onwards. It is backwards compatible with regular SQL syntax: users can write entire queries using this syntax, only certain subqueries, or any useful combination.

The industrial paper provides query 13 from the TPC-H benchmark as the first example:

Using pipe syntax to express the same logic, we apply operators in a sequence from beginning to end with any arbitrary ordering:

## And how do aggregations work?

With regular SQL, when we want to collect rows into groups based on column or expression values, we add a GROUP BY clause to the end of the SQL query under construction. The aggregations to perform remain stuck all the way up in the SELECT list at the very start of the query and every expression must now be either:

- A grouping key, in which case the GROUP BY clause must contain a copy of the expression (or an alias reference or ordinal).
- An aggregate function like SUM, COUNT, MIN, or MAX, accepting an expression based on input table columns like SUM(A + B). We can also compute projections on the result, like SUM(A) + 1.

Any SELECT item that does not meet one of these categories will raise some error like “expression X appeared in the SELECT list but was not grouped or aggregated.”

The rules of the WHERE clause also change:

- If it appears before the GROUP BY clause, then we filter out rows according to the specified criteria before aggregating them together.
- Otherwise, the query is not valid and we get a strange error. The user must instead write a HAVING clause with the same filtering condition and it must only appear after the GROUP BY clause, but not before it.
- The QUALIFY clause also serves as another example of needing to understand and use separate syntax to perform filtering depending on the context.

Pipe syntax solves this by separating each aggregation operation (with possible grouping) into a dedicated step that may apply at any time. Only expressions with aggregate functions inside may appear inside this step, and aggregate functions may not appear inside |> SELECT steps. If the SQL author forgets any of these invariants, the resulting error messages are very clear and easy to understand.

There’s also no need to repeat the grouping expressions anymore, since we can just write them in one GROUP BY clause.

Let’s look at the previous example with an aggregation appended to the end, which returns a result table with two columns L, M:

## Fun with subqueries

Regular SQL generally requires that the clauses appear in a specific order, without repeating. If we want to apply further operations on the result of a SQL query, the way to do that is to use a table subquery wherein we wrap the original query in parentheses and use it in the FROM clause of an enclosing query. The query at the beginning of this post shows a simple example of this.

Note that this nesting can happen any arbitrary number of times. For example, here’s TPC-DS query 23:

It’s getting confusing and harder to read with all the levels of parentheses and indentation!

On the other hand, with SQL pipe syntax there is no need for table subqueries at all. Since the pipe operators may appear in any order, we can just add new ones to the end at any time, and all the steps still work the same way.

## Get started easily with backwards compatibility

Pipe syntax reworks how authors write, read, and extend SQL. It might seem like a challenge to switch from the thinking of how regular SQL works over to this new paradigm. You might even have a large body of existing SQL queries written previously that you are responsible for maintaining and possibly extending later. How can we make this work with two SQL syntaxes?

Luckily, this is not a problem with our new SQL syntax. It is fully interoperable with regular SQL, where any query (or table subquery) may appear using either syntax. We can start writing new queries using SQL pipe syntax and keep our previous ones if needed. We can even start replacing table subqueries of our previous queries with the new syntax and keep everything else the same, such as updating only part of TPC-H Q13 from the start of this post:

Since SQL pipe operators may follow any valid query, it’s also possible to start appending them to existing regular SQL queries as well. For example:

## Go try it today!

SQL pipe syntax is ready for you to try out in Databricks Runtime version 16.2 and later. Or download Apache Spark 4.0 and give it a go in the open source world. The syntax conforms to the [Pipe Syntax in SQL](https://research.google/pubs/sql-has-problems-we-can-fix-them-pipe-syntax-in-sql/) industrial paper, so the new syntax will be portable with Google BigQuery as well as the open source [ZetaSQL project](https://github.com/google/zetasql).

This syntax is also starting to generate buzz in the community and show up elsewhere, increasing portability now and over time.

Give it a shot and experience the benefits of making SQL queries simpler to write for new and experienced users, and make future readability and extensibility easier by reducing the incidence of complex subqueries in favor of clear and composable operators instead.
