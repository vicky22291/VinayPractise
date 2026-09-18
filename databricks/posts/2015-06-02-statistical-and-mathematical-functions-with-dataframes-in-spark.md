# Statistical and Mathematical Functions with DataFrames in Apache Spark

- Source: https://www.databricks.com/blog/2015/06/02/statistical-and-mathematical-functions-with-dataframes-in-spark.html
- Published: 2015-06-02
- Authors: Burak Yavuz, Reynold Xin
- Categories: engineering, open-source, data-science-machine-learning
- Images: 0 total, 0 extracted as architecture

We [introduced DataFrames](https://www.databricks.com/blog/2015/02/17/introducing-dataframes-in-spark-for-large-scale-data-science.html) in Apache Spark 1.3 to make Apache Spark much easier to use. Inspired by data frames in R and Python, [DataFrames in Spark expose an API](https://www.databricks.com/blog/2016/07/14/a-tale-of-three-apache-spark-apis-rdds-dataframes-and-datasets.html) that’s similar to the single-node data tools that data scientists are already familiar with. Statistics is an important part of everyday data science. We are happy to announce improved support for statistical and mathematical functions in the upcoming 1.4 release.

In this blog post, we walk through some of the important functions, including:

1. Random data generation
2. Summary and descriptive statistics
3. Sample covariance and correlation
4. Cross tabulation (a.k.a. contingency table)
5. Frequent items
6. Mathematical functions

We use Python in our examples. However, similar APIs exist for Scala and Java users as well.

## 1. Random Data Generation

Random data generation is useful for testing of existing algorithms and implementing randomized algorithms, such as random projection. We provide methods under sql.functions for generating columns that contains i.i.d. values drawn from a distribution, e.g., uniform (`rand`),  and standard normal (`randn`).

## 2. Summary and Descriptive Statistics

The first operation to perform after importing data is to get some sense of what it looks like. For numerical columns, knowing the descriptive summary statistics can help a lot in understanding the distribution of your data. The function `describe` returns a DataFrame containing information such as number of non-null entries (count), mean, standard deviation, and minimum and maximum value for each numerical column.

If you have a DataFrame with a large number of columns, you can also run describe on a subset of the columns:

Of course, while describe works well for quick exploratory data analysis, you can also control the list of descriptive statistics and the columns they apply to using the normal select on a DataFrame:

## 3. Sample covariance and correlation

[Covariance](https://en.wikipedia.org/wiki/Covariance) is a measure of how two variables change with respect to each other. A positive number would mean that there is a tendency that as one variable increases, the other increases as well. A negative number would mean that as one variable increases, the other variable has a tendency to decrease. The sample covariance of two columns of a DataFrame can be calculated as follows:

As you can see from the above, the covariance of the two randomly generated columns is close to zero, while the covariance of the id column with itself is very high.

The covariance value of 9.17 might be hard to interpret. [Correlation](https://en.wikipedia.org/wiki/Correlation) is a normalized measure of covariance that is easier to understand, as it provides quantitative measurements of the statistical dependence between two random variables.

In the above example, id correlates perfectly with itself, while the two randomly generated columns have low correlation value.

## 4. Cross Tabulation (Contingency Table)

[Cross Tabulation](https://en.wikipedia.org/wiki/Contingency_table) provides a table of the frequency distribution for a set of variables. Cross-tabulation is a powerful tool in statistics that is used to observe the statistical significance (or independence) of variables. In Spark 1.4, users will be able to cross-tabulate two columns of a DataFrame in order to obtain the counts of the different pairs that are observed in those columns. Here is an example on how to use crosstab to obtain the contingency table.

One important thing to keep in mind is that the cardinality of columns we run crosstab on cannot be too big. That is to say, the number of distinct “name” and “item” cannot be too large. Just imagine if “item” contains 1 billion distinct entries: how would you fit that table on your screen?!

## 5. Frequent Items

Figuring out which items are frequent in each column can be very useful to understand a dataset. In Spark 1.4, users will be able to find the frequent items for a set of columns using DataFrames. We have implemented an [one-pass algorithm](https://dl.acm.org/doi/10.1145/762471.762473?cookieSet=1) proposed by Karp et al. This is a fast, approximate algorithm that always return all the frequent items that appear in a user-specified minimum proportion of rows. Note that the result might contain false positives, i.e. items that are not frequent.

Given the above DataFrame, the following code finds the frequent items that show up 40% of the time for each column:

As you can see, “11” and “1” are the frequent values for column “a”. You can also find frequent items for column combinations, by creating a composite column using the struct function:

From the above example, the combination of “a=11 and b=22”, and “a=1 and b=2” appear frequently in this dataset. Note that “a=11 and b=22” is a false positive.

## 6. Mathematical Functions

Spark 1.4 also added a suite of mathematical functions. Users can apply these to their columns with ease. The list of math functions that are supported come from [this file](https://github.com/apache/spark/blob/efe3bfdf496aa6206ace2697e31dd4c0c3c824fb/python/pyspark/sql/functions.py#L109) (we will also post pre-built documentation once 1.4 is released). The inputs need to be columns functions that take a single argument, such as `cos`, `sin`, `floor`, `ceil`. For functions that take two arguments as input, such as `pow`, `hypot`, either two columns or a combination of a double and column can be supplied.

## What’s Next?

All the features described in this blog post will be available in Spark 1.4 for Python, Scala, and Java, to be released in the next few days. If you can’t wait, you can also build Spark from the 1.4 release branch yourself: [https://github.com/apache/spark/tree/branch-1.4](https://github.com/apache/spark/tree/branch-1.4)

Statistics support will continue to increase for DataFrames through better integration with Spark MLlib in future releases. Leveraging the existing Statistics package in MLlib, support for feature selection in pipelines, Spearman Correlation, ranking, and aggregate functions for covariance and correlation.

At the end of the blog post, we would also like to thank Davies Liu, Adrian Wang, and rest of the Spark community for implementing these functions.
