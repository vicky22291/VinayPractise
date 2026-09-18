# SQL Pivot: Converting Rows to Columns

- Source: https://www.databricks.com/blog/2018/11/01/sql-pivot-converting-rows-to-columns.html
- Published: 2018-11-01
- Authors: MaryAnn Xue
- Categories: engineering, open-source
- Images: 0 total, 0 extracted as architecture

[Try this notebook in Databricks](https://docs.databricks.com/_static/notebooks/pivot-in-sql.html)

 Check out the[Why the Data Lakehouse is Your Next Data Warehouse](https://www.databricks.com/resources/ebook/bring-data-warehousing-data-lakes?itm_data=sqlpivot-blog-whylakehouseisnextdw) ebook to discover the inner workings of the Databricks Lakehouse Platform.

**UPDATED 11/10/2018**

Pivot was first introduced in Apache Spark 1.6 as a new DataFrame feature that allows users to rotate a table-valued expression by turning the unique values from one column into individual columns.

The [Apache Spark 2.4](https://www.databricks.com/blog/2018/11/08/introducing-apache-spark-2-4.html) release extends this powerful functionality of pivoting data to our SQL users as well. In this blog, using temperatures recordings in Seattle, we’ll show how we can use this common SQL Pivot feature to achieve complex data transformations.

## Examining Summer Temperatures with Pivot

This summer in Seattle temperatures rose to uncomfortable levels, peaking to high 80s and 90, for nine days in July.

| Date | Temp (°F) |
|---|---|
| 07-22-2018 | 86 |
| 07-23-2018 | 90 |
| 07-24-2018 | 91 |
| 07-25-2018 | 92 |
| 07-26-2018 | 92 |
| 07-27-2018 | 88 |
| 07-28-2018 | 85 |
| 07-29-2018 | 94 |
| 07-30-2018 | 89 |

Suppose we want to explore or examine if there were a historical trend in rising mercury levels. One intuitive way to examine and present these numbers is to have months as the columns and then each year’s monthly average highs in a single row. That way it will be easy to compare the temperatures both horizontally, between adjacent months, and vertically, between different years.

Now that we have support for `PIVOT` syntax in Spark SQL, we can achieve this with the following SQL query.

The above query will produce a result like:

| YEAR | JAN | FEB | MAR | APR | MAY | JUNE | JULY | AUG | SEPT | OCT | NOV | DEC |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2018 | 49.7 | 45.8 | 54.0 | 58.6 | 70.8 | 71.9 | 82.8 | 79.1 | NULL | NULL | NULL | NULL |
| 2017 | 43.7 | 46.6 | 51.6 | 57.3 | 67.0 | 72.1 | 78.3 | 81.5 | 73.8 | 61.1 | 51.3 | 45.6 |
| 2016 | 49.1 | 53.6 | 56.4 | 65.9 | 68.8 | 73.1 | 76.0 | 79.5 | 69.6 | 60.6 | 56.0 | 41.9 |
| 2015 | 50.3 | 54.5 | 57.9 | 59.9 | 68.0 | 78.9 | 82.6 | 79.0 | 68.5 | 63.6 | 49.4 | 47.1 |

Well, looks like there are good years and bad years. The year 2016 seems a rather energy-friendly year.

## Pivoting in SQL

Let’s take a closer look at this query to understand how it works. First, we need to specify the `FROM` clause, which is the input of the pivot, in other words, the table or subquery based on which the pivoting will be performed. In our case, we are concerned about the years, the months, and the high temperatures, so those are the fields that appear in the sub-query.

Second, let’s consider another important part of the query, the `PIVOT` clause. The first argument of the `PIVOT` clause is an aggregate function and the column to be aggregated. We then specify the pivot column in the `FOR` sub-clause as the second argument, followed by the `IN` operator containing the pivot column values as the last argument.

The pivot column is the point around which the table will be rotated, and the pivot column values will be transposed into columns in the output table. The `IN` clause also allows you to specify an alias for each pivot value, making it easy to generate more meaningful column names.

An important idea about pivot is that it performs a grouped aggregation based on a list of implicit `group-by` columns together with the pivot column. The implicit `group-by` columns are columns from the `FROM` clause that do not appear in any aggregate function or as the pivot column.

In the above query, with the pivot column being the column month and the implicit `group-by` column being the column year, the expression `avg(temp)` will be aggregated on each distinct value pair of `(year, month)`, where month equals to one of the specified pivot column values. As a result, each of these aggregated values will be mapped into its corresponding cell of row `year` and `column` month.

It is worth noting that because of this implicit `group-by`, we need to make sure that any column that we do not wish to be part of the pivot output should be left out from the `FROM` clause, otherwise the query would produce undesired results.

## Specifying Multiple Aggregate Expressions

The above example shows only one aggregate expression being used in the `PIVOT` clause, while in fact, users can specify multiple aggregate expressions if needed. Again, with the weather data above, we can list the maximum high temperatures along with the average high temperatures between June and September.

In case of multiple aggregate expressions, the columns will be the Cartesian product of the pivot column values and the aggregate expressions, with the names as `_`.

| year | JUN_avg | JUN_max | JUL_avg | JUL_max | AUG_avg | AUG_max | SEP_avg | SEP_max |
|---|---|---|---|---|---|---|---|---|
| 2018 | 71.9 | 88 | 82.8 | 94 | 79.1 | 94 | NULL | NULL |
| 2017 | 72.1 | 96 | 78.3 | 87 | 81.5 | 94 | 73.8 | 90 |
| 2016 | 73.1 | 93 | 76.0 | 89 | 79.5 | 95 | 69.6 | 78 |
| 2015 | 78.9 | 92 | 82.6 | 95 | 79.0 | 92 | 68.5 | 81 |

## Grouping Columns vs. Pivot Columns

Now suppose we want to include low temperatures in our exploration of temperature trends from this table of daily low temperatures:

| Date | Temp (°F) |
|---|---|
| ... | ... |
| 08-01-2018 | 59 |
| 08-02-2018 | 58 |
| 08-03-2018 | 59 |
| 08-04-2018 | 58 |
| 08-05-2018 | 59 |
| 08-06-2018 | 59 |
| ... | ... |

To combine this table with the previous table of daily high temperatures, we could join these two tables on the “Date” column. However, since we are going to use pivot, which performs grouping on the dates, we can simply concatenate the two tables using `UNION ALL`. And you’ll see later, this approach also provides us with more flexibility:

Now let’s try our pivot query with the new combined table:

As a result, we get the average high and average low for each month of the past 4 years in one table. Note that we need to include the column `flag` in the pivot query, otherwise the expression `avg(temp)` would be based on a mix of high and low temperatures.

| year | H/L | JUN | JUL | AUG | SEP |
|---|---|---|---|---|---|
| 2018 | H | 71.9 | 82.8 | 79.1 | NULL |
| 2018 | L | 53.4 | 58.5 | 58.5 | NULL |
| 2017 | H | 72.1 | 78.3 | 81.5 | 73.8 |
| 2017 | L | 53.7 | 56.3 | 59.0 | 55.6 |
| 2016 | H | 73.1 | 76.0 | 79.5 | 69.9 |
| 2016 | L | 53.9 | 57.6 | 59.9 | 52.9 |
| 2015 | H | 78.9 | 82.6 | 79.0 | 68.5 |
| 2015 | L | 56.4 | 59.9 | 58.5 | 52.5 |

You might have noticed that now we have two rows for each year, one for the high temperatures and the other for low temperatures. That’s because we have included one more column, `flag`, in the pivot input, which in turn becomes another implicit grouping column in addition to the original column `year`.

Alternatively, instead of being a grouping column, the `flag` can also serve as a pivot column. So now we have two pivot columns, `month` and `flag`:

This query presents us with a different layout of the same data, with one row for each year, but two columns for each month.

| year | JUN_hi | JUN_lo | JUL_hi | JUL_lo | AUG_hi | AUG_lo | SEP_hi | SEP_lo |
|---|---|---|---|---|---|---|---|---|
| 2018 | 71.9 | 53.4 | 82.8 | 58.5 | 79.1 | 58.5 | NULL | NULL |
| 2017 | 72.1 | 53.7 | 78.3 | 56.3 | 81.5 | 59.0 | 73.8 | 55.6 |
| 2016 | 73.1 | 53.9 | 76.0 | 57.6 | 79.5 | 57.9 | 69.6 | 52.9 |
| 2015 | 78.9 | 56.4 | 82.6 | 59.9 | 79.0 | 58.5 | 68.5 | 52.5 |

## What’s Next

To run the query examples used in this blog, please check the pivot SQL examples in this [accompanying notebook](https://docs.databricks.com/_static/notebooks/pivot-in-sql.html).

Thanks to the Apache Spark community contributors for their contributions!
