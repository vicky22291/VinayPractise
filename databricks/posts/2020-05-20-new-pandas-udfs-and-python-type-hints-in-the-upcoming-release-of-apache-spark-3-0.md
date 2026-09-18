# New Pandas UDFs and Python Type Hints in the Upcoming Release of Apache Spark 3.0

- Source: https://www.databricks.com/blog/2020/05/20/new-pandas-udfs-and-python-type-hints-in-the-upcoming-release-of-apache-spark-3-0.html
- Published: 2020-05-20
- Authors: Hyukjin Kwon
- Categories: platform, engineering, open-source
- Images: 0 total, 0 extracted as architecture

Pandas user-defined functions (UDFs) are one of the most significant enhancements in [Apache SparkTM](https://spark.apache.org/) for data science. They bring many benefits, such as enabling users to use [Pandas](https://pandas.pydata.org/) APIs and improving performance.

However, Pandas UDFs have evolved organically over time, which has led to some inconsistencies and is creating confusion among users. The full release of Apache Spark 3.0, expected soon, will introduce a new interface for Pandas UDFs that leverages [Python type hints](https://www.python.org/dev/peps/pep-0484/) to address the proliferation of Pandas UDF types and help them become more Pythonic and self-descriptive.

This blog post introduces new Pandas UDFs with Python type hints, and the new Pandas Function APIs including grouped map, map, and co-grouped map.

## **Pandas UDFs**

Pandas UDFs were introduced in Spark 2.3, see also [Introducing Pandas UDF for PySpark](https://www.databricks.com/blog/2017/10/30/introducing-vectorized-udfs-for-pyspark.html). Pandas is well known to data scientists and has seamless integrations with many Python libraries and packages such as [NumPy](https://numpy.org/), [statsmodel](https://www.statsmodels.org/stable/index.html), and [scikit-learn](https://scikit-learn.org/stable/), and Pandas UDFs allow data scientists not only to scale out their workloads, but also to leverage the Pandas APIs in Apache Spark.

The user-defined functions are executed by:

- [Apache Arrow](https://arrow.apache.org), to exchange data directly between JVM and Python driver/executors with near-zero (de)serialization cost.
- Pandas inside the function, to work with Pandas instances and APIs.

The Pandas UDFs work with Pandas APIs inside the function and Apache Arrow for exchanging data. It allows vectorized operations that can increase performance up to 100x, compared to row-at-a-time Python UDFs.

The example below shows a Pandas UDF to simply add one to each value, in which it is defined with the function called `pandas_plus_one` decorated by `pandas_udf` with the Pandas UDF type specified as `PandasUDFType.SCALAR`.

The Python function takes and outputs a Pandas Series. You can perform a vectorized operation for adding one to each value by using the rich set of Pandas APIs within this function. (De)serialization is also automatically vectorized by leveraging Apache Arrow under the hood.

## **Python Type Hints**

Python type hints were officially introduced in [PEP 484](https://www.python.org/dev/peps/pep-0484/) with Python 3.5. Type hinting is an official way to statically indicate the type of a value in Python. See the example below.

The name: `str`indicates the name argument is of str type and the `->` syntax indicates the `greeting()` function returns a string.

Python type hints bring two significant benefits to the PySpark and Pandas UDF context.

- It gives a clear definition of what the function is supposed to do, making it easier for users to understand the code. For example, unless it is documented, users cannot know if `greeting` can take `None` or not if there is no type hint. It can avoid the need to document such subtle cases with a bunch of test cases and/or for users to test and figure out by themselves.
- It can make it easier to perform static analysis. IDEs such as PyCharm and [Visual Studio Code](https://code.visualstudio.com/) can leverage type annotations to provide code completion, show errors, and support better go-to-definition functionality.

## **Proliferation of Pandas UDF Types**

Since the release of Apache Spark 2.3, a number of new Pandas UDFs have been implemented, making it difficult for users to learn about the new specifications and how to use them. For example, here are three Pandas UDFs that output virtually the same results:

Although each of these UDF types has a distinct purpose, several can be applicable. In this simple case, you could use any of the three. However, each of the Pandas UDFs expects different input and output types, and works in a different way with a distinct semantic and different performance. It confuses users about which one to use and learn, and how each works.

Furthermore, `pandas_plus_one` in the first and second cases can be used where the regular PySpark columns are used. Consider the argument of `withColumn` or the function with the combinations of other expressions such as `pandas_plus_one("id") + 1`. However, the last `pandas_plus_one` can only be used with `groupby(...).apply(pandas_plus_one)`.

This level of complexity has triggered numerous discussions with Spark developers, and drove the effort to introduce the new Pandas APIs with Python type hints via an[official proposal](https://docs.google.com/document/d/1-kV0FS_LF2zvaRh_GhkV32Uqksm_Sq8SvnBBmRyxm30/edit?usp=sharing). The goal is to enable users to naturally express their pandas UDFs using Python type hints without confusion as in the problematic cases above. For example, the cases above can be written as below:

## **New Pandas APIs with Python Type Hints**

To address the complexity in the old Pandas UDFs, from Apache Spark 3.0 with Python 3.6 and above, Python type hints such as `pandas.Series`, `pandas.DataFrame`, `Tuple`, and `Iterator` can be used to express the new Pandas UDF types.

In addition, the old Pandas UDFs were split into two API categories: Pandas UDFs and Pandas Function APIs. Although they work internally in a similar way, there are distinct differences.

You can treat Pandas UDFs in the same way that you use other PySpark column instances. However, you cannot use the Pandas Function APIs with these column instances. Here are these two examples:

Also, note that Pandas UDFs require Python type hints whereas the type hints in Pandas Function APIs are currently optional. Type hints are planned for Pandas Function APIs and may be required at some point in the future.

### **New Pandas UDFs**

Instead of defining and specifying each Pandas UDF type manually, the new Pandas UDFs infer the Pandas UDF type from the given Python type hints at the Python function. There are currently four supported cases of the Python type hints in Pandas UDFs:

- Series to Series
- Iterator of Series to Iterator of Series
- Iterator of Multiple Series to Iterator of Series
- Series to Scalar (a single value)

Before we do a deep dive into each case, let’s look at three key points about working with the new Pandas UDFs.

- Although Python type hints are optional in the Python world in general, you must specify Python type hints for the input and output in order to use the new Pandas UDFs.
- Users can still use the old way by manually specifying the Pandas UDF type. However, using Python type hints is encouraged.
- The type hint should use `pandas.Series` in all cases. However, there is one variant in which `pandas.DataFrame` should be used for its input or output type hint instead: when the input or output column is of `StructType.`Take a look at the example below:

#### **Series to Series**

Series to Series is mapped to scalar Pandas UDF introduced in Apache Spark 2.3. The type hints can be expressed as `pandas.Series, ... -> pandas.Series`. It expects the given function to take one or more `pandas.Series` and outputs one `pandas.Series`. The output length is expected to be the same as the input.

The example above can be mapped to the old style with scalar Pandas UDF, as below.

#### **Iterator of Series to Iterator of Series**

This is a new type of Pandas UDF coming in Apache Spark 3.0. It is a variant of Series to Series, and the type hints can be expressed as `Iterator[pd.Series] -> Iterator[pd.Series]`. The function takes and outputs an iterator of `pandas.Series`.

The length of the whole output must be the same length of the whole input. Therefore, it can prefetch the data from the input iterator as long as the lengths of entire input and output are the same. The given function should take a single column as input.

It is also useful when the UDF execution requires expensive initialization of some state. The pseudocode below illustrates the case.

Iterator of Series to Iterator of Series can be also mapped to the old Pandas UDF style. See the example below.

#### **Iterator of Multiple Series to Iterator of Series**

This type of Pandas UDF will be also introduced in Apache Spark 3.0, together with Iterator of Series to Iterator of Series. The type hints can be expressed as `Iterator[Tuple[pandas.Series, ...]] -> Iterator[pandas.Series]`.

It has the similar characteristics and restrictions with Iterator of Series to Iterator of Series. The given function takes an iterator of a tuple of `pandas.Series` and outputs an iterator of `pandas.Series`. It is also useful when to use some states and when to prefetch the input data. The length of the entire output should also be the same as the length of the entire input. However, the given function should take multiple columns as input, unlike Iterator of Series to Iterator of Series.

This can also be mapped to the old Pandas UDF style as below.

#### **Series to Scalar**

Series to Scalar is mapped to the grouped aggregate Pandas UDF introduced in Apache Spark 2.4. The type hints are expressed as `pandas.Series, ... -> Any`. The function takes one or more pandas.Series and outputs a primitive data type. The returned scalar can be either a Python primitive type, e.g., `int`, `float`, or a NumPy data type such as `numpy.int64`, `numpy.float64`, etc. `Any` should ideally be a specific scalar type accordingly.

The example above can be converted to the example with the grouped aggregate Pandas UDF as you can see here:

### **New Pandas Function APIs**

This new category in Apache Spark 3.0 enables you to directly apply a Python native function, which takes and outputs Pandas instances against a PySpark DataFrame. Pandas Functions APIs supported in Apache Spark 3.0 are: grouped map, map, and co-grouped map.

Note that the grouped map Pandas UDF is now categorized as a group map Pandas Function API. As mentioned earlier, the Python type hints in Pandas Function APIs are optional currently.

#### **Grouped Map**

Grouped map in the Pandas Function API is `applyInPandas` at a grouped DataFrame, e.g., `df.groupby(...)`. This is mapped to the grouped map Pandas UDF in the old Pandas UDF types. It maps each group to each `pandas.DataFrame` in the function. Note that it does not require for the output to be the same length of the input.

Grouped map type is mapped to grouped map Pandas UDF supported from Spark 2.3, as below:

#### **Map**

Map Pandas Function API is `mapInPandas` in a DataFrame. It is new in Apache Spark 3.0. It maps every batch in each partition and transforms each. The function takes an iterator of `pandas.DataFrame` and outputs an iterator of `pandas.DataFrame`. The output length does not need to match the input size.

#### **Co-grouped Map**

Co-grouped map, `applyInPandas` in a co-grouped DataFrame such as `df.groupby(...).cogroup(df.groupby(...))`, will also be introduced in Apache Spark 3.0. Similar to the grouped map, it maps each group to each `pandas.DataFrame` in the function but it groups with another DataFrame by common key(s) and then the function is applied to each cogroup. Likewise, there is no restriction on the output length.

## **Conclusion and Future Work**

The upcoming release of Apache Spark 3.0 ([read our preview blog for details](https://www.databricks.com/blog/2020/05/13/now-on-databricks-a-technical-preview-of-databricks-runtime-7-including-a-preview-of-apache-spark-3-0.html)). will offer Python type hints to make it simpler for users to express Pandas UDFs and Pandas Function APIs. In the future, we should consider adding support for other type hint combinations in both Pandas UDFs and Pandas Function APIs. Currently, the supported cases are only few of many possible combinations of Python type hints. There are also other ongoing discussions in the Apache Spark community. Visit [Side Discussions and Future Improvement](https://docs.google.com/document/d/1-kV0FS_LF2zvaRh_GhkV32Uqksm_Sq8SvnBBmRyxm30/edit#heading=h.h3ncjpk6ujqu) to learn more.

Learn more about Spark 3.0 in our [preview webinar.](https://www.databricks.com/p/webinar/apache-spark-3-0)  Try out these new capabilities today for [free on Databricks](https://www.databricks.com/try-databricks) as part of the Databricks Runtime 7.0 Beta.
