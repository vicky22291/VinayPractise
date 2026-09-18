# Introducing the Support of Lateral Column Alias

*A New SQL Feature to Simplify Your Queries*

- Source: https://www.databricks.com/blog/introducing-support-lateral-column-alias
- Published: 2023-09-19
- Authors: Xinyi Yu, Wenchen Fan, Gengliang Wang
- Categories: engineering, data-warehousing
- Images: 0 total, 0 extracted as architecture

We are thrilled to introduce the support of a new SQL feature in Apache Spark and Databricks: Lateral Column Alias (LCA). This feature simplifies complex SQL queries by allowing users to reuse an expression specified earlier in the same SELECT list, eliminating the need to use nested subqueries and Common Table Expressions (CTEs) in many cases. This blog post discusses the use cases of the feature and the benefits it brings to Spark and Databricks users.

## What is Lateral Column Alias Support?

Lateral Column Alias (LCA) provides users the capability to reuse an expression specified earlier within the same SELECT list.
 This feature can be better understood through the example provided below. Here is a simple query:

In the absence of LCA support, users will get an error on this query that the latter `a` in the SELECT list cannot be resolved:

 

`[UNRESOLVED_COLUMN.WITHOUT_SUGGESTION] A column or function parameter with name `a` cannot be resolved. ; line 1 pos 15;`

 

Fortunately, with the LCA feature, this second a in the query now successfully identifies as the previously defined alias in the same SELECT list : 1 AS a. Users are no longer faced with an error, but instead provided with the following results:

## Eliminate Complex Subqueries and CTEs with LCA Chaining

While the previous examples showcase the basic concept of LCA, the true power of this feature lies in its ability to eliminate complex subqueries and CTEs.

Before the introduction of LCA, users had to deal with multiple subqueries and CTEs when trying to reference any attribute defined by a previous alias. This increased the complexity and verbosity of SQL queries, making them hard to read, write and maintain. In contrast, LCA support fundamentally simplifies these queries, making them more user-friendly and manageable.

Let's take an example. Suppose there is a `products` table storing product information such as name, category, price and customer rating. Our goal is to compute an adjusted price based on several influencing factors. The scenario will clearly delineate how LCA can turn a convoluted query into a significantly simplified version.

Here is the table structure:

We would like to calculate the adjusted price for each product on the greater value of two factors: the price increase percentage based on users' rating of the product and based on the rank of the product within its category. Without LCA support, the query looks like this:

The logic contains many chaining operations wherein a latter calculation depends on previously calculated results. Therefore it requires multiple CTEs to store each intermediate calculation in a manner suitable for later references in the subsequent stages of the query.

However, with LCA, it is possible to express the query as one single SELECT statement instead:

LCAs can also be chained! This means the current alias expression, which can be referenced by subsequent expressions, can reference a previously defined lateral alias. For example, the definition of `final_increase_percentage` depends on two lateral column aliases: `increase_percentage_based_on_rating` and `increase_percentage_based_on_rank`. The following calculation of `adjusted_price` then refers to `final_increase_percentage`. This chaining power of LCA allows users to create a series of dependent calculations, where the results of one calculation are used as inputs for the next.

As we can see in the above example, LCA largely simplifies the query, eliminating repeated calculation or the need for multiple CTEs, making it easier to understand, maintain and debug. It also improves readability since the calculation definition and the usage are close together in the query.

## LCA Everything

### Simple, aggregation or window expressions

Almost every expression can reside within a lateral column alias. The examples in the last section show that complex CASE-WHEN expressions, as well as GREATEST function expressions or even window functions, can live inside a lateral column alias for further use in subsequent expressions.

By the same token, we may also nest aggregation expressions in this way. Here is an example on the same `products` table:

### Complex data types

LCA also works well with complex data types like struct, array and map. For example,

### Non-deterministic expressions

LCA guarantees that non-deterministic expressions are evaluated only once, mirroring the "run-once" semantics that CTEs offer. This ensures consistent results when using non-deterministic expressions in the query.

For example, consider a scenario where there is a `member_price` for each product in the above `products` table. We would like to apply a random discount percentage between 0% and 5% to each product and then calculate the discounted price of both the `price` and `member_price`. This exercise should guarantee that the discount percentage applied to both prices remains the same.

With LCA, we can write:

In this example, Databricks calculates the `discounted_rate` once, and this value remains the same through all subsequent references including the calculation of `adjusted_price` and `adjusted_member_price`.

On the other hand, if we are simply copying non-deterministic expressions, this behavior does not apply because it would evaluate each expression separately, causing inconsistent discount rates for the two prices:

## Try LCA!

In summary, Lateral Column Alias is a powerful feature that significantly simplifies SQL queries by allowing users to define a named alias over an expression tree and then reference this alias later within the same SELECT clause.

- This saves repeating the same expressions multiple times or the need for subqueries or CTEs, instead generating concise and readable SELECT queries.
- It is compatible with all kinds of expressions and complex data types. The SQL syntax supports chaining these aliases for greater flexibility as well.
- It ensures that each non-deterministic expression is evaluated only once, thus enabling consistent results across multiple references.

LCA is fully available and enabled by default in [Databricks Runtime 12.2](https://docs.databricks.com/release-notes/runtime/12.2.html#implicit-lateral-column-aliasing-support) LTS and later, in [Databricks SQL 2023.20](https://docs.databricks.com/sql/release-notes/index.html#databricks-sql-version-202320-available) and above, and Apache Spark 3.4.

## Read More

- [Resolution order](https://docs.databricks.com/en/sql/language-manual/sql-ref-name-resolution.html)
 Curious readers may be interested in the name resolution order in SQL queries with the introduction of LCA. This Databricks Name resolution document defines a clear set of ordered rules and concrete examples to resolve references, including the role of LCA in this process.
