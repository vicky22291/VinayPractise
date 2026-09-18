# Introducing New Built-in and Higher-Order Functions for Complex Data Types in Apache Spark 2.4

- Source: https://www.databricks.com/blog/2018/11/16/introducing-new-built-in-functions-and-higher-order-functions-for-complex-data-types-in-apache-spark.html
- Published: 2018-11-16
- Authors: Takuya Ueshin, Herman van Hövell
- Categories: engineering, open-source
- Images: 0 total, 0 extracted as architecture

>  [Try this notebook in Databricks](https://docs.databricks.com/_static/notebooks/apache-spark-functions.html)

[Apache Spark 2.4](https://www.databricks.com/blog/2018/11/08/introducing-apache-spark-2-4.html) introduces 29 new built-in functions for manipulating complex types (for example, array type), including higher-order functions.

Before Spark 2.4, for manipulating the complex types directly, there were two typical solutions: 1) Exploding the nested structure into individual rows, and applying some functions, and then creating the structure again 2) Building a User Defined Function (UDF).

In contrast, the new built-in functions can directly manipulate complex types, and the higher-order functions can manipulate complex values with an anonymous lambda function similar to UDFs but with much better performance.

In this blog, through some examples, we’ll show some of these new built-in functions and how to use them to manipulate complex data types.

## Typical solutions

Let’s review the typical solutions with the following examples first.

### Option 1 - Explode and Collect

We use explode to break the array into individual rows and evaluate `val + 1`, and then use collect_list to restructure the array as follows:

This is error-prone and inefficient for three reasons. First, we have to be diligent to ensure that the recollected arrays are made exactly from the original arrays by grouping them by the unique key. Second, we need a `group-by`, which means a shuffle operation; a shuffle operation is not guaranteed to keep the element order of the re-collected array from the original array. And finally, it is expensive.

### Option 2 - User Defined Function

Next, we use Scala UDF which takes Seq[Int] and add 1 to the each element in it:

or we can also use Python UDF, and then:

This is simpler and faster and does not suffer from correctness pitfalls, but it might still be inefficient because the data serialization into Scala or Python can be expensive.

You can see the examples in a notebook in a [blog that we published](https://www.databricks.com/blog/2017/05/24/working-with-nested-data-using-higher-order-functions-in-sql-on-databricks.html) and try them.

## New Built-in Functions

Let's see the new built-in functions for manipulating complex types directly. The notebook lists the examples for each function. The signatures and arguments for each function are annotated with their respective types T or U to denote as array element types and K, V as map and value types.

## Higher-Order Functions

For further manipulation for array and map types, we used known syntax in SQL for the anonymous lambda function and higher-order functions to take the lambda functions as arguments.

The syntax for the lambda function is as follows:

The left side of the symbol -> defines the argument list, and the right side defines the function body which can use the arguments and other variables in it to calculate the new value.

### Transform with Anonymous Lambda Function

Let’s see the example with `transform` function that employs an anonymous lambda function.

Here we have a table of data that contains 3 columns: a key as an integer; values of array of integer; and nested_values of array of array of integers.

| key | values | nested_values |
|---|---|---|
| 1 | [1, 2, 3] | [[1, 2, 3], [], [4, 5]] |

When we execute the following SQL:

the `transform` function iterates over the array and applies the lambda function, adding 1 to each element, and creates a new array.

We can also use other variables besides the arguments, for example: key, which is coming from the outer context, a column of the table, in the lambda function:

If you want to manipulate a deeply nested column, like nested_values in this case, you can use the nested lambda functions:

You can use `key` and `arr` in the internal lambda function that are coming from the outer context, a column of the table and an argument of the outer lambda function.

Note, you can see the same examples as the typical solution in the notebook for them, and the examples of the other higher-order functions are included in the notebook for built-in functions.

## Conclusion

Spark 2.4 introduced 24 new built-in functions, such as `array_union`, `array_max/min`, etc., and 5 higher-order functions, such as `transform`, `filter`, etc. for manipulating complex types. The whole list and their examples are in this [notebook](https://docs.databricks.com/_static/notebooks/apache-spark-functions.html). If you have any complex values, consider using them and let us know of any issues.

We would like to thank contributors from the Apache Spark community Alex Vayda, Bruce Robbins, Dylan Guedes, Florent Pepin, H Lu, Huaxin Gao, Kazuaki Ishizaki, Marco Gaido, Marek Novotny, Neha Patil, Sandeep Singh, and many others.

## Read More

To find out more about higher-order and built-in functions, see the following resources:

1. Try the [accompanying notebook](https://docs.databricks.com/_static/notebooks/apache-spark-functions.html)
2. Read the previous [blog on higher-order functions](https://www.databricks.com/blog/2017/05/24/working-with-nested-data-using-higher-order-functions-in-sql-on-databricks.html)
3. Watch the [Spark + AI Summit Europe Talk on Higher-Order Functions](https://www.databricks.com/session/an-introduction-to-higher-order-functions-in-spark-sql)
