# Interoperability between Koalas and Apache Spark

*How PySpark users effectively work with Koalas*

- Source: https://www.databricks.com/blog/2020/08/11/interoperability-between-koalas-and-apache-spark.html
- Published: 2020-08-11
- Authors: Takuya Ueshin, Hyukjin Kwon, Xiao Li
- Categories: solutions, engineering
- Images: 1 total, 0 extracted as architecture

Koalas is an open source project which provides a drop-in replacement for pandas, enabling efficient scaling out to hundreds of worker nodes for everyday data science and machine learning. After over one year of development since it was [first introduced last year](https://www.databricks.com/session/official-announcement-of-koalas-open-source-project), [Koalas 1.0 was released](https://www.databricks.com/blog/2020/06/24/introducing-koalas-1-0.html).

pandas is a Python package commonly used among data scientists, but it does not scale out to big data. When their data becomes large, they have to choose and learn another system such as Apache Spark from the beginning in order to adopt and convert their existing workload.  Koalas fills the gap by providing pandas equivalent APIs that work on Apache Spark. Many of these are introduced in the previous [blog post](https://www.databricks.com/blog/2020/03/31/10-minutes-from-pandas-to-koalas-on-apache-spark.html), which also includes the best practices when working with Koalas.

Koalas is useful for not only pandas users but also PySpark users because Koalas supports many features difficult to do with PySpark. For example, Spark users can plot data directly from their PySpark DataFrame via the [Koalas plotting APIs](https://koalas.readthedocs.io/en/latest/reference/frame.html#plotting), similar to pandas. PySpark DataFrame is more SQL compliant and Koalas DataFrame is closer to Python itself which provides more intuitiveness to work with Python in some contexts. In the [Koalas documentation](https://koalas.readthedocs.io/en/latest/), there are the various pandas equivalent APIs implemented.

In this blog post, we focus on how PySpark users can leverage their knowledge and the native interaction between PySpark and Koalas to write code faster.  We include many self-contained examples, which you can run if you have Spark with [Koalas installed](https://koalas.readthedocs.io/en/latest/getting_started/install.html), or you are using the Databricks Runtime. From Databricks Runtime 7.1, Koalas is packaged together so you can run it without the manual installation.

## Koalas and PySpark DataFrames

Before a deep dive, let’s look at the general differences between Koalas and PySpark DataFrames first.

Externally, they are different. Koalas DataFrames seamlessly follow the structure of [pandas DataFrames](https://www.databricks.com/glossary/pandas-dataframe) and implement an index/identifier under the hood. The PySpark DataFrame, on the other hand, tends to be more compliant with the relations/tables in relational databases, and does not have unique row identifiers.

Internally, Koalas DataFrames are built on PySpark DataFrames. Koalas translates pandas APIs into the logical plan of Spark SQL. The plan is optimized and executed by the sophisticated and robust Spark SQL engine which is continually being improved by the Spark community. Koalas also follows Spark to keep the lazy evaluation semantics for maximizing the performance. To implement the pandas DataFrame structure and pandas’ rich APIs that require an implicit ordering, Koalas DataFrames have the internal metadata to represent pandas-equivalent indices and column labels mapped to the columns in PySpark DataFrame.

Even though Koalas leverages PySpark as the execution engine, you might still face slight performance degradation when compared to PySpark. As discussed in the [migration experience in Virgin Hyperloop One](https://www.databricks.com/blog/2019/08/22/guest-blog-how-virgin-hyperloop-one-reduced-processing-time-from-hours-to-minutes-with-koalas.html), the major causes are usually:

- **The default index is used.** The overhead for building the default index depends on the data size, cluster composition, etc. Therefore, it is always preferred to avoid using the default index. It will be discussed more about this in other sections below.

- **Some APIs in PySpark and pandas have the same name but different semantics.** For example, both Koalas DataFrame and PySpark DataFrame have the count API. The former counts the number of non-NA/null entries for each column/row and the latter counts the number of retrieved rows, including rows containing null.

## Conversion from and to PySpark DataFrames

For a PySpark user, it’s good to know how easily you can go back and forth between a Koalas DataFrame and PySpark DataFrame and what’s happening under the hood so that you don’t need to be afraid of entering Koalas world to apply the highly scalable pandas APIs on Spark.

#### to_koalas()

When importing the Koalas package, it automatically attaches the to_koalas() method to PySpark DataFrames. You can simply use this method to convert PySpark DataFrames to Koalas DataFrames.

Let’s suppose you have a PySpark DataFrame:

First, import the Koalas package. You conventionally use ks as an alias for the package.

Convert your Spark DataFrame to a Koalas DataFrame with the to_koalas() method as described above.

kdf is a Koalas DataFrame created from the PySpark DataFrame. The computation is lazily executed when the data is actually needed, for example showing or storing the computed data, the same as PySpark.

#### to_spark()

Next, you should also know how to go back to a PySpark DataFrame from Koalas. You can use the to_spark() method on the Koalas DataFrame.

Now you have a PySpark DataFrame again. Notice that there is no longer the index column that the Koalas DataFrame contained. The best practices for handling the index below will be discussed later.

### Index and index_col

As shown above, Koalas internally manages a couple of columns as “index” columns in order to represent the pandas’ index. The “index” columns are used to access rows by loc/iloc indexers or used in the sort_index() method without specifying the sort key columns, or even used to match corresponding rows for operations combining more than two DataFrames or Series, for example df1 + df2, and so on.

If there are already such columns in the PySpark DataFrame, you can use the index_col parameter to specify the index columns.

This time, column x is not considered as one of the regular columns but the index.

If you have multiple columns as the index, you can pass the list of column names.

When going back to a PySpark DataFrame, you also use the index_col parameter to preserve the index columns.

Otherwise, the index is lost as below.

The number of the column names should match the number of index columns.

### Default Index

As you have seen, if you don’t specify index_col parameter, a new column is created as an index.

Where does the column come from?

The answer is “default index”. If the index_col parameter is not specified, Koalas automatically attaches one column as an index to the DataFrame. There are three types of default indices: “sequence”, “distributed-sequence”, and “distributed”. Each has its distinct characteristics and limitations such as performance penalty. For reducing the performance overhead, it is highly encouraged to specify index columns via index_col when converting from a PySpark DataFrame.

The default index is also used when Koalas doesn’t know which column is intended for the index. For example, reset_index() without any parameters which tries to convert all the index data to the regular columns and recreate an index:

You can change the default index type by setting it as a Koalas option “compute.default_index_type”:

or

#### sequence type

The "sequence" type is currently used by default in Koalas as it guarantees the index increments continuously, like pandas. However, it uses a non-partitioned window function internally, which means all the data needs to be collected into a single node. If the node doesn't have enough memory, the performance will be significantly degraded, or OutOfMemoryError will occur.

#### distributed-sequence type

When the "distributed-sequence" index is used, the performance penalty is not as significant as "sequence" type. It computes and generates the index in a distributed manner but it needs another extra Spark Job to generate the global sequence internally. It also does not guarantee the natural order of the results. In general, it becomes a continuously increasing number.

#### distributed type

“distributed" index has almost no performance penalty and always creates monotonically increasing numbers. If the index is just needed as unique numbers for each row, or the order of rows, this index type would be the best choice. However, the numbers have an indeterministic gap. That means this index type will unlikely be used as an index for operations combining more than two DataFrames or Series.

#### Comparison

As you have seen, each index type has its distinct characteristics as summarized in the table below. The default index type should be chosen carefully considering your workloads.

|  | Distributed computation | Map-side operation | Continuous increment | Performance |
|---|---|---|---|---|
| sequence | No, in a single worker node | No, requires a shuffle | Yes | Bad for large dataset |
| distributed-sequence | Yes | Yes, but requires another Spark job | Yes, in most cases | Good enough |
| distributed | Yes | Yes | No | Good |

See also [Default Index type in Koalas document](https://koalas.readthedocs.io/en/latest/user_guide/options.html#default-index-type).

## Using Spark I/O

There are a lot of functions to read and write data in pandas, and in Koalas as well.

Here is the list of functions from pandas, where Koalas uses Spark I/O under the hood.

- [DataFrame.to_csv](https://koalas.readthedocs.io/en/latest/reference/api/databricks.koalas.DataFrame.to_csv.html) / [ks.read_csv](https://koalas.readthedocs.io/en/latest/reference/api/databricks.koalas.read_csv.html)
- [DataFrame.to_json](https://koalas.readthedocs.io/en/latest/reference/api/databricks.koalas.DataFrame.to_json.html) / [ks.read_json](https://koalas.readthedocs.io/en/latest/reference/api/databricks.koalas.read_json.html)
- [DataFrame.to_parquet](https://koalas.readthedocs.io/en/latest/reference/api/databricks.koalas.DataFrame.to_parquet.html) / [ks.read_parquet](https://koalas.readthedocs.io/en/latest/reference/api/databricks.koalas.read_parquet.html)
- [ks.read_sql_table](https://koalas.readthedocs.io/en/latest/reference/api/databricks.koalas.read_sql_table.html)
- [ks.read_sql_query](https://koalas.readthedocs.io/en/latest/reference/api/databricks.koalas.read_sql_query.html)

The APIs and their arguments follow the APIs corresponding to pandas. However, there are subtle differences in the behaviors currently. For example, pandas’ read_csv can read a file over http protocol, but Koalas still does not support it since the underlying Spark engine itself does not support it.

These Koalas functions also have the index_col argument to specify which columns should be used as an index or what the index column names should be, similarly to the to_koalas() or to_spark() function as described above. If you don’t specify it, the default index is attached or the index column is lost.

For example, if you don’t specify index_col parameter, the default index is attached as below - distributed default index was used for simplicity.

Whereas if you specify the index_col parameter, the specified column becomes an index.

In addition, each function takes keyword arguments to set options for the DataFrameWriter and DataFrameReader in Spark. The given keys are directly passed to their options and configure the behavior. This is useful when the pandas-origin arguments are not enough to manipulate your data but PySpark supports the missing functionality.

### Koalas specific I/O functions

In addition to the above functions from pandas, Koalas has its own functions.

- [DataFrame.to_table](https://koalas.readthedocs.io/en/latest/reference/api/databricks.koalas.DataFrame.to_table.html) / [ks.read_table](https://koalas.readthedocs.io/en/latest/reference/api/databricks.koalas.read_table.html)
- [DataFrame.to_spark_io](https://koalas.readthedocs.io/en/latest/reference/api/databricks.koalas.DataFrame.to_spark_io.html) / [ks.read_spark_io](https://koalas.readthedocs.io/en/latest/reference/api/databricks.koalas.read_spark_io.html)
- [DataFrame.to_delta](https://koalas.readthedocs.io/en/latest/reference/api/databricks.koalas.DataFrame.to_delta.html) / [ks.read_delta](https://koalas.readthedocs.io/en/latest/reference/api/databricks.koalas.read_delta.html)

Firstly, DataFrame.to_table and ks.read_table is to write and read Spark tables by just specifying the table name. It is analogous to DataFrameWriter.saveAsTable and DataFrameReader.table in Spark, respectively.

Secondly, DataFrame.to_spark_io and ks.read_spark_io are for general Spark I/O. There are a few optional arguments for ease of use, and the others are keyword arguments. You can freely set the options used for DataFrameWriter.save and DataFrameReader.load in Spark.

The ORC format in the above example is not supported in pandas, but Koalas can write and read it because the underlying Spark I/O supports it.

Last but not least, Koalas also can write and read Delta tables if you have Delta Lake [installed](https://docs.delta.io/latest/quick-start.html#set-up-apache-spark-with-delta-lake).

[Delta Lake](https://docs.delta.io/latest/delta-intro.html) is an open source storage layer that brings reliability to data lakes. Delta Lake provides ACID transactions, scalable metadata handling, and unifies streaming and batch data processing.

Different from the other file sources, the read_delta function enables users to specify the version of the table to time travel.

Please see [Delta Lake](https://delta.io/) for more details.

## Spark accessor

Koalas provides the spark accessor for users to leverage the existing PySpark APIs more easily.

### Series.spark.transform and Series.spark.apply

Series.spark accessor has transform and apply functions to handle underlying Spark Column objects.

For example, suppose you have the following Koalas DataFrame:

You can cast type with astype function, but if you are not used to it yet, you can use cast of Spark column using Series.spark.transform function instead:

The user function passed to the Series.spark.transform function takes Spark’s Column object and can manipulate it using PySpark functions.

Also you can use functions of pyspark.sql.functions in the transform/apply functions:

The user function for Series.spark.transform should return the same length of Spark column as its input’s, whereas one for Series.spark.apply can return a different length of Spark column, such as calling the aggregate functions.

### DataFrame.spark.apply

Similarly, DataFrame.spark accessor has an apply function. The user function takes and returns a Spark DataFrame and can apply any transformation. If you want to keep the index columns in the Spark DataFrame, you can set index_col parameter. In that case, the user function has to contain a column of the same name in the returned Spark DataFrame.

If you omit index_col, it will use the default index.

### Spark schema

You can see the current underlying Spark schema by DataFrame.spark.schema and DataFrame.spark.print_schema. They both take the index_col parameter if you want to know the schema including index columns.

### Explain Spark plan

If you want to know the current Spark plan, you can use DataFrame.spark.explain().

### Cache

The spark accessor also provides cache related functions, cache, persist, unpersist, and the storage_level property. You can use the cache function as a context manager to unpersist the cache. Let’s see an example.

When it is no longer needed, you have to call DataFrame.spark.unpersist() explicitly to remove it from cache.

### Hints

There are some join-like operations in Koalas, such as merge, join, and update. Although the actual join method depends on the underlying Spark planner under the hood, you can still specify a hint with the ks.broadcast() function or DataFrame.spark.hint() method.

In particular, DataFrame.spark.hint() is more useful if the underlying Spark is 3.0 or above since more hints are available in  Spark 3.0.

## Conclusion

Koalas DataFrame is similar to PySpark DataFrame because Koalas uses PySpark DataFrame internally. Externally, Koalas DataFrame works as if it is a pandas DataFrame.

In order to fill the gap, Koalas has numerous features useful for users familiar with PySpark to work with both Koalas and PySpark DataFrame easily. Although there is some extra care required to deal with the index during the conversion, Koalas provides PySpark users the easy conversion between both DataFrames, the input/output APIs to read/write for PySpark and the spark accessor to expose PySpark friendly features such as caching and exploring the DataFrame internally. In addition, the spark accessor provides a natural way to play with Koalas Series and PySpark columns.

PySpark users can benefit from Koalas as shown above. Try out the examples and learn more in Databricks Runtime.

## Read More

To find out more about Koalas, see the following resources:

1. Try the accompanying [notebook](https://www.databricks.com/notebooks/interoperability-koalas-apache-spark.html)
2. Read the previous [blog on 10 Minutes from pandas to Koalas on Apache Spark](https://www.databricks.com/blog/2020/03/31/10-minutes-from-pandas-to-koalas-on-apache-spark.html)
3. Spark+AI Summit 2020 talk “[Koalas: Pandas on Apache Spark](https://www.databricks.com/session_na20/koalas-pandas-on-apache-spark)”
4. Spark+AI Summit 2020 talk “[Koalas: Making an Easy Transition from Pandas to Apache Spark](https://www.databricks.com/session_na20/koalas-making-an-easy-transition-from-pandas-to-apache-spark)”
