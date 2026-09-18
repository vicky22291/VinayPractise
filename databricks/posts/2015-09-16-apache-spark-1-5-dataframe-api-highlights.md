# Apache Spark 1.5 DataFrame API Highlights: Date/Time/String Handling, Time Intervals, and UDAFs

- Source: https://www.databricks.com/blog/2015/09/16/apache-spark-1-5-dataframe-api-highlights.html
- Published: 2015-09-16
- Authors: Michael Armbrust, Yin Huai, Davies Liu, Reynold Xin
- Categories: engineering, open-source
- Images: 0 total, 0 extracted as architecture

*To try new features highlighted in this blog post, [download Spark 1.5](https://spark.apache.org/downloads.html) or [sign up Databricks for a 14-day free trial today](https://accounts.cloud.databricks.com/registration.html#signup).*

---

A few days ago, [we announced the release of Apache Spark 1.5](https://www.databricks.com/blog/2015/09/09/announcing-apache-spark-1-5.html). This release contains major under-the-hood changes that improve Spark’s performance, usability, and operational stability. Besides these changes, we have been continuously improving DataFrame API. In this blog post, we’d like to highlight three major improvements to DataFrame API in Spark 1.5, which are:

- New built-in functions;
- Time intervals; and
- Experimental user-defined aggregation function (UDAF) interface.

## New Built-in Functions in Spark 1.5

In Spark 1.5, we have added a comprehensive list of built-in functions to the DataFrame API, complete with optimized code generation for execution. This code generation allows pipelines that call functions to take full advantage of the efficiency changes made as part of [Project Tungsten](https://www.databricks.com/blog/2015/04/28/project-tungsten-bringing-spark-closer-to-bare-metal.html). With these new additions, Spark SQL now supports a wide range of built-in functions for various use cases, including:

| Category | Functions |
|---|---|
| Aggregate Functions | `approxCountDistinct, avg, count, countDistinct, first, last, max, mean, min, sum, sumDistinct` |
| Collection Functions | `array_contains, explode, size, sort_array` |
| Date/time Functions | **Date/timestamp conversion:** `unix_timestamp, from_unixtime, to_date, quarter, day, dayofyear, weekofyear, from_utc_timestamp, to_utc_timestamp`**Extracting fields from a date/timestamp value:**`year, month, dayofmonth, hour, minute, second`**Date/timestamp calculation:**`datediff, date_add, date_sub, add_months, last_day, next_day, months_between`**Misc.:**`current_date, current_timestamp, trunc, date_format` |
| Math Functions | `abs, acros, asin, atan, atan2, bin, cbrt, ceil, conv, cos, sosh, exp, expm1, factorial, floor, hex, hypot, log, log10, log1p, log2, pmod, pow, rint, round, shiftLeft, shiftRight, shiftRightUnsigned, signum, sin, sinh, sqrt, tan, tanh, toDegrees, toRadians, unhex` |
| Misc. Functions | `array, bitwiseNOT, callUDF, coalesce, crc32, greatest, if, inputFileName, isNaN, isnotnull, isnull, least, lit, md5, monotonicallyIncreasingId, nanvl, negate, not, rand, randn, sha, sha1, sparkPartitionId, struct, when` |
| String Functions | `ascii, base64, concat, concat_ws, decode, encode, format_number, format_string, get_json_object, initcap, instr, length, levenshtein, locate, lower, lpad, ltrim, printf, regexp_extract, regexp_replace, repeat, reverse, rpad, rtrim, soundex, space, split, substring, substring_index, translate, trim, unbase64, upper` |
| Window Functions (in addition to Aggregate Functions) | `cumeDist, denseRank, lag, lead, ntile, percentRank, rank, rowNumber` |

For all available built-in functions, please refer to our API docs ([Scala Doc](https://spark.apache.org/docs/latest/api/scala/index.html#org.apache.spark.sql.functions$) and [Java Doc](https://spark.apache.org/docs/latest/api/java/org/apache/spark/sql/functions.html).

Unlike normal functions, which execute immediately and return a result, DataFrame functions return a `Column`, that will be evaluated inside of a parallel job. These columns can be used inside of DataFrame operations, such as `select`, `filter`, `groupBy`, etc. The input to a function can either be another Column (i.e. `df['columnName']`) or a literal value (i.e. a constant value). To make this more concrete, let’s look at the syntax for calling the `round` function in Python.

`round` is a function that rounds a numeric value to the specified precision. When the given precision is a positive number, a given input numeric value is rounded to the decimal position specified by the precision. When the specified precision is a zero or a negative number, a given input numeric value is rounded to the position of the integral part specified by the precision.

Alternatively, all of the added functions are also available from SQL using standard syntax:

[sql]SELECT round(i, 1) FROM dataFrame[/sql]

Finally, you can even mix and match SQL syntax with DataFrame operations by using the `expr` function. By using `expr`, you can construct a DataFrame column expression from a SQL expression String.

## Time Interval Literals

In the last section, we introduced several new date and time functions that were added in Spark 1.5 (e.g. `datediff`, `date_add`, `date_sub`), but that is not the only new feature that will help users dealing with date or timestamp values. Another related feature is a new data type, interval, that allows developers to represent fixed periods of time (i.e. 1 day or 2 months) as interval literals. Using interval literals, it is possible to perform subtraction or addition of an arbitrary amount of time from a date or timestamp value. This representation can be useful when you want to add or subtract a time period from a fixed point in time. For example, users can now easily express queries like *“Find all transactions that have happened during the past hour”*.

An interval literal is constructed using the following syntax:

[sql]INTERVAL value unit[/sql]

Breaking the above expression down, all time intervals start with the `INTERVAL` keyword. Next, the value and unit together specify the time difference. Available units are `YEAR`, `MONTH`, u`DAY`, `HOUR`, `MINUTE`, `SECOND`, `MILLISECOND`, and `MICROSECOND`. For example, the following interval literal represents 3 years.

[sql]INTERVAL 3 YEAR[/sql]

In addition to specifying an interval literal with a single unit, users can also combine different units. For example, the following interval literal represents a 3-year and 3-hour time difference.

[sql]INTERVAL 3 YEAR 3 HOUR[/sql]

In the DataFrame API, the `expr` function can be used to create a `Column` representing an interval. The following code in Python is an example of using an interval literal to select records where `start_time` and `end_time` are in the same day and they differ by less than an hour.

## User-defined Aggregate Function Interface

For power users, Spark 1.5 introduces an experimental API for user-defined aggregate functions (UDAFs). These UDAFs can be used to compute custom calculations over groups of input data (in contrast, UDFs compute a value looking at a single input row), such as calculating geometric mean or calculating the product of values for every group.

A UDAF maintains an aggregation buffer to store intermediate results for every group of input data. It updates this buffer for every input row. Once it has processed all input rows, it generates a result value based on values of the aggregation buffer.

An UDAF inherits the base class `UserDefinedAggregateFunction` and implements the following eight methods, which are:

- `inputSchema: inputSchema` returns a `StructType` and every field of this StructType represents an input argument of this UDAF.
- `bufferSchema: bufferSchema` returns a `StructType` and every field of this StructType represents a field of this UDAF’s intermediate results.
- `dataType: dataType` returns a `DataType` representing the data type of this UDAF’s returned value.
- `deterministic: deterministic` returns a boolean indicating if this UDAF always generate the same result for a given set of input values.
- `initialize: initialize` is used to initialize values of an aggregation buffer, represented by a `MutableAggregationBuffer`.
- `update: update` is used to update an aggregation buffer represented by a `MutableAggregationBuffer` for an input `Row`.
- `merge: merge` is used to merge two aggregation buffers and store the result to a `MutableAggregationBuffer`.
- `evaluate: evaluate` is used to generate the final result value of this UDAF based on values stored in an aggregation buffer represented by a `Row`.

Below is an example UDAF implemented in Scala that calculates the [geometric mean](https://en.wikipedia.org/wiki/Geometric_mean) of the given set of double values. The geometric mean can be used as an indicator of the typical value of an input set of numbers by using the product of their values (as opposed to the standard builtin mean which is based on the sum of the input values). For the purpose of simplicity, null handling logic is not shown in the following code.

import org.apache.spark.sql.expressions.MutableAggregationBuffer
 import org.apache.spark.sql.expressions.UserDefinedAggregateFunction
 import org.apache.spark.sql.Row
 import org.apache.spark.sql.types._

class GeometricMean extends UserDefinedAggregateFunction {
 def inputSchema: org.apache.spark.sql.types.StructType =
 StructType(StructField("value", DoubleType) :: Nil)

def bufferSchema: StructType = StructType(
 StructField("count", LongType) ::
 StructField("product", DoubleType) :: Nil
 )

def dataType: DataType = DoubleType

def deterministic: Boolean = true

def initialize(buffer: MutableAggregationBuffer): Unit = {
 buffer(0) = 0L
 buffer(1) = 1.0
 }

def update(buffer: MutableAggregationBuffer,input: Row): Unit = {
 buffer(0) = buffer.getAs[Long](0) + 1
 buffer(1) = buffer.getAs[Double](1) * input.getAs[Double](0)
 }

def merge(buffer1: MutableAggregationBuffer, buffer2: Row): Unit = {
 buffer1(0) = buffer1.getAs[Long](0) + buffer2.getAs[Long](0)
 buffer1(1) = buffer1.getAs[Double](1) * buffer2.getAs[Double](1)
 }

def evaluate(buffer: Row): Any = {
 math.pow(buffer.getDouble(1), 1.toDouble / buffer.getLong(0))
 }
 }

A UDAF can be used in two ways. First, an instance of a UDAF can be used immediately as a function. Second, users can register a UDAF to Spark SQL’s function registry and call this UDAF by the assigned name. The example code is shown below.

import org.apache.spark.sql.functions._
 // Create a simple DataFrame with a single column called "id"
 // containing number 1 to 10.
 val df = sqlContext.range(1, 11)

// Create an instance of UDAF GeometricMean.
 val gm = new GeometricMean

// Show the geometric mean of values of column "id".
 df.groupBy().agg(gm(col("id")).as("GeometricMean")).show()

// Register the UDAF and call it "gm".
 sqlContext.udf.register("gm", gm)
 // Invoke the UDAF by its assigned name.
 df.groupBy().agg(expr("gm(id) as GeometricMean")).show()

## Summary

In this blog post, we introduced three major additions to DataFrame APIs, a set of built-in functions, time interval literals, and user-defined aggregation function interface. With new built-in functions, it is easier to manipulate string data and data/timestamp data, and to apply math operations. If your existing programs use any user-defined functions that do the same work with these built-in functions, we strongly recommend you to migrate your code to these new built-in functions to take full advantage of the efficiency changes made as part of [Project Tungsten](https://www.databricks.com/blog/2015/04/28/project-tungsten-bringing-spark-closer-to-bare-metal.html). Combining date/time functions and interval literals, it is much easier to work with date/timestamp data and to calculate date/timestamp values for various use cases. With user-defined aggregate function, users can apply custom aggregations over groups of input data in the DataFrame API.

To try new these new features, [download Spark 1.5](https://spark.apache.org/downloads.html) or [sign up Databricks for a 14-day free trial today](https://accounts.cloud.databricks.com/registration.html#signup).

## Acknowledgements

The development of features highlighted in this blog post has been a community effort. In particular, we would like to thank the following contributors: Adrian Wang, Tarek Auel, Yijie Shen, Liang-Chi Hsieh, Zhichao Li, Pedro Rodriguez, Cheng Hao, Shilei Qian, Nathan Howell, and Wenchen Fan.
