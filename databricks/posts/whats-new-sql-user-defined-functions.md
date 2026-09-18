# What’s New With SQL User-Defined Functions

- Source: https://www.databricks.com/blog/whats-new-sql-user-defined-functions
- Published: 2023-01-18
- Authors: Allison Wang, Daniel Tenedorio
- Categories: engineering, data-science-machine-learning
- Images: 0 total, 0 extracted as architecture

Since their [initial release](https://www.databricks.com/blog/2021/10/20/introducing-sql-user-defined-functions.html), [SQL user-defined functions](https://docs.databricks.com/sql/language-manual/sql-ref-syntax-ddl-create-sql-function.html) have become hugely popular among both Databricks Runtime and Databricks SQL customers. This simple yet powerful extension to SQL supports defining and re-using custom transformation logic.

In this blog, we describe several enhancements we have recently made to make SQL user-defined functions even more user-friendly and powerful, along with examples of how you can use them to wrap encapsulated logic in components suitable for using on your own or sharing with others. This way, you can keep queries simple while enjoying strong type-safety thanks to the Databricks SQL analyzer. Please read on for more details.

## Default parameters

> This feature is available in DBR 10.4 LTS and later versions.
 > This feature is available in DBSQL.

You can now specify default values for the parameters of your SQL UDF at declaration time. Future calls to the function can leave out these arguments, and the query analyzer will fill them in for you automatically. This feature can be useful for adding optional arguments to make user-defined functions more flexible over time. Consider the following example:

This feature also works well to extend existing user-defined SQL functions already in use since adding new default parameters to existing functions does not break any existing call sites. You can add sentinel values like NULL or the empty string to indicate that function calls did not provide any value and respond to this in the function body accordingly using [conditional logic](https://docs.databricks.com/sql/language-manual/functions/if.html) as [needed](https://docs.databricks.com/sql/language-manual/functions/case.html).

## Optional RETURNS clause

> This feature is available in DBR 11.3 LTS and later versions.
 > This feature is available in DBSQL.

The [original launch](https://www.databricks.com/blog/2021/10/20/introducing-sql-user-defined-functions.html) of SQL user-defined functions at Databricks specified a required result type for each SQL UDF declaration. In general, this appears in the function declaration's RETURNS clause. At declaration time, the Databricks SQL query analyzer validates that the type of the expression in the function body is equivalent or coercible to this manually specified return type, adding an implicit type coercion if necessary or returning an error if the types are not compatible.

As of DBR 11.3 LTS and later, this RETURNS clause is now optional. If absent, the SQL analyzer will infer the function's return type directly from the resolved result type of the function body instead. This is often more convenient when this result type is obvious from the contents of the function logic. For example, let's modify the example earlier in this blog post accordingly:

It still works exactly the same way.

This even works for more complex result types like [STRUCT](https://docs.databricks.com/sql/language-manual/data-types/struct-type.html) and [ARRAY](https://docs.databricks.com/sql/language-manual/data-types/array-type.html) types, potentially saving lots of complexity from typing out all of the nested fields or element types. Here's a more powerful example that truncates multiple string fields of a nested structure to a maximum length:

You can also omit the result table schema for user-defined SQL table functions. Just include RETURNS TABLE by itself, without any column names or types, and the Databricks SQL analyzer will infer this information for you as well.

## Unity Catalog support

> This feature is in public preview.

### How it works

You can now create and share SQL user-defined functions with fine-grained access control using [Unity Catalog](https://www.databricks.com/product/unity-catalog). In general, Unity Catalog brings [fine-grained governance](https://www.databricks.com/blog/2021/05/26/introducing-databricks-unity-catalog-fine-grained-governance-for-data-and-ai-on-the-lakehouse.html) for all your data and AI assets on any cloud, including files, tables, functions, machine learning models, and dashboards. It brings your lakehouse to the next level by empowering you to share assets between multiple individuals and groups within your team or with partner organizations.

Use Unity Catalog to simplify your life by retaining just one copy of your data and metadata assets and defining access control rights to others as needed instead of creating and maintaining several ETL pipelines to generate separate copies for different purposes.

You can now define your user-defined SQL function logic once with Unity Catalog and reuse it across multiple sessions and even multiple users!

Once any function is created, you can use GRANT and REVOKE commands to manage access:

For introspection, you can use the [INFORMATION_SCHEMA](https://docs.databricks.com/sql/language-manual/sql-ref-information-schema.html) to query more information about functions in any catalog:

We are very excited about Unity Catalog as one place for powerful governance over your relational logic, from tables and schemas to functions and much more!

## Dependency tracking

Unity Catalog takes care of dependency tracking as you build your SQL function collections. In general, such SQL functions lend themselves well to building libraries of reusable logic in layers that depend on each other. For example, string manipulation functions within such a group may call other functions as helpers:

When resolving the `word_count_greater_than` function, the Databricks SQL analyzer looks up the signature for the `word_count` function referenced therein, making sure that it exists and that its result type makes sense in the context of the call site, and checking for the presence of circular dependencies. The same dependency management and tracking also hold for the names of referenced tables, files, and all other assets within the Unity Catalog.

## What's next

- SQL standard support for named arguments in function calls.
- Optional generic argument types with late resolution at call time.
- Overloaded function groups sharing the same name but with different numbers and/or types of input arguments.

## Conclusions

SQL user-defined functions comprise strong additions to Databricks' extensive [built-in functions](https://docs.databricks.com/sql/language-manual/sql-ref-functions-builtin-alpha.html) catalog. They help make SQL more reusable and secure and also incur no extra performance overhead since the Databricks SQL query analyzer resolves the function logic into the containing query plan at each call site.

Learn more about SQL user-defined functions in this [documentation](https://docs.databricks.com/sql/language-manual/sql-ref-syntax-ddl-create-sql-function.html) and how to build unit test suites [here](https://docs.databricks.com/notebooks/testing.html#language-SQL).

For even more extensibility, if you are interested in using user-defined functions with Python, check out [Python UDFs in Databricks SQL](https://www.databricks.com/blog/2022/07/22/power-to-the-sql-people-introducing-python-udfs-in-databricks-sql.html).

Enjoy, and happy querying!
