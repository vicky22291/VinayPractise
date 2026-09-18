# Introducing Python User-Defined Table Functions (UDTFs)

*What are Python user-defined table functions (UDTFs), why they matter, and how to use them*

- Source: https://www.databricks.com/blog/introducing-python-user-defined-table-functions
- Published: 2023-11-07
- Authors: Allison Wang, Daniel Tenedorio, Takuya Ueshin, Allan Folting
- Categories: engineering, data-engineering
- Images: 0 total, 0 extracted as architecture

Apache Spark™ 3.5 and Databricks Runtime 14.0 have brought an exciting feature to the table: Python user-defined table functions (UDTFs). In this blog post, we’ll dive into what UDTFs are, why they are powerful, and how you can use them.

## What are Python user-defined table functions (UDTFs)

A Python user-defined table function (UDTF) is a new kind of function that returns a table as output instead of a single scalar result value. Once registered, they can appear in the `FROM` clause of a SQL query.

Each Python UDTF accepts zero or more arguments, where each argument can be a constant scalar value such as an integer or string. The body of the function can inspect the values of these arguments in order to make decisions about what data to return.

## Why should you use Python UDTFs

In short, if you want a function that generates multiple rows and columns, and want to leverage the rich Python ecosystem, Python UDTFs are for you.

### Python UDTFs vs Python UDFs

While Python UDFs in Spark are designed to each accept zero or more scalar values as input, and return a single value as output, UDTFs offer more flexibility. They can return multiple rows and columns, extending the capabilities of UDFs.

### Python UDTFs vs SQL UDTFs

SQL UDTFs are efficient and versatile, but Python offers a richer set of libraries and tools. For transformations or computations needing advanced techniques (like statistical functions or machine learning inferences), Python stands out.

## How to create a Python UDTF

Let’s look at a basic Python UDTF:

In the above code, we've created a simple UDTF that takes two integers as inputs and produces two columns as output: the original number and its square.

The first step to implement a UDTF is to define a class, in this case

Next, you need to implement the `eval` method of the UDTF. This is the method that does the computations and returns rows, where you define the input arguments of the function.

Note the use of the `yield` statement; A Python UDTF requires the return type to be either a tuple or a `Row` object so that the results can be processed properly.

Finally, to mark the class as a UDTF, you can use the `@udtf` decorator and define the return type of the UDTF. Note the return type must be a StructType with block-formatting or DDL string representing a StructType with block-formatting in Spark.

## How to use a Python UDTF

### In Python

You can invoke a UDTF directly using the class name.

### In SQL

First, register the Python UDTF:

Then you can use it in SQL as a table-valued function in the FROM clause of a query:

## Arrow-optimized Python UDTFs

Apache Arrow is an in-memory columnar data format that allows for efficient data transfers between Java and Python processes. It can significantly boost performance when the UDTF outputs many rows. Arrow-optimization can be enabled using `useArrow=True`.

## Real-World Use Case with LangChain

The example above might feel basic. Let’s dive deeper with a fun example, integrating Python UDTFs with LangChain.

Now, you can invoke the UDTF:

## Get Started with Python UDTFs Today

Whether you're looking to perform complex data transformations, enrich your datasets, or simply explore new ways to analyze your data, Python UDTFs are a valuable addition to your toolkit. Try [this notebook](https://www.databricks.com/wp-content/uploads/notebooks/python-user-defined-table-functions-udtfs.html) and see the documentation for more information.

## Future Work

This functionality is only the beginning of the Python UDTF platform. Many more features are currently in development in Apache Spark to become available in future releases. For example, it will become possible to support:

- A polymorphic analysis wherein UDTF calls may dynamically compute their output schemas in response to the specific arguments provided for each call (including the types of provided input arguments and the values of any literal scalar arguments).
- Passing entire input relations to UDTF calls in the SQL FROM clause using the TABLE keyword. This will work with direct catalog table references as well as arbitrary table subqueries. It will be possible to specify custom partitioning of the input table in each query to define which subsets of rows of the input table will be consumed by the same instance of the UDTF class in the eval method.
- Performing arbitrary initialization for any UDTF call just once at query scheduling time and propagating that state to all future class instances for future consumption. This means that the UDTF output table schema returned by the initial static "analyze" method will be consumable by all future __init__ calls for the same query.
- Many more interesting features!
