# Introducing Flint: A time-series library for Apache Spark

- Source: https://www.databricks.com/blog/2018/09/11/introducing-flint-a-time-series-library-for-apache-spark.html
- Published: 2018-09-11
- Authors: Li Jin, Kevin Rasmussen
- Categories: company, open-source, engineering, customers, news
- Images: 0 total, 0 extracted as architecture

*This is a joint guest community blog by [Li Jin](https://www.linkedin.com/in/li-jin-94950b27/) at [Two Sigma](https://www.twosigma.com/) and Kevin Rasmussen at Databricks; they share how to use Flint with Apache Spark.*

[Try this notebook in Databricks](https://databricks-prod-cloudfront.cloud.databricks.com/public/4027ec902e239c93eaaa8714f173bcfc/1281142885375883/1566406256250190/7729323681064935/latest.html)

## Introduction

The volume of data that data scientists face these days increases relentlessly, and we now find that a traditional, single-machine solution is no longer adequate to the demands of these datasets. Over the past few years, Apache Spark has become the standard for dealing with big-data workloads, and we think it promises data scientists huge potential for analysis of large time series. We have developed [Flint](https://github.com/twosigma/flint) at [Two Sigma](http://www.twosigma.com) to enhance Spark’s functionality for time series analysis. Flint is an open source library and available via Maven and PyPI.

### Time Series Analysis

Time series analysis has two components: time series manipulation and time series modeling.

**Time series manipulation** is the process of manipulating and transforming data into features for training a model. Time series manipulation is used for tasks like data cleaning and feature engineering. Typical functions in time series manipulation include:

- *Joining*: joining two time-series datasets, usually by the time
- *Windowing*: feature transformation based on a time window
- *Resampling*: changing the frequency of the data
- *Filling in* missing values or removing NA rows.

**Time series modeling** is the process of identifying patterns in time-series data and training models for prediction. It is a complex topic; it includes specific techniques such as ARIMA and autocorrelation, as well as all manner of general machine learning techniques (e.g., linear regression) applied to time series data.

Flint focuses on **time series manipulation**. In this blog post, we demonstrate Flint functionalities in time series manipulation and how it works with other libraries, e.g., Spark ML, for a simple time series modeling task.

## Flint Overview

Flint takes inspiration from an internal library at Two Sigma that has proven very powerful in dealing with time-series data.

Flint’s main API is its Python API. The entry point — **TimeSeriesDataFrame** — is an extension to PySpark DataFrame and exposes additional time series functionalities.

Here is a simple example showing how to read data into Flint and use both PySpark DataFrame and Flint functionalities:

## Flint Functionalities

In this section, we introduce a few core Flint functionalities to deal with time series data.

### Asof Join

*Asof Join* means joining on time, with inexact matching criteria. It takes a tolerance parameter, e.g, ‘1day’ and joins each left-hand row with the closest right-hand row within that tolerance. Flint has two asof join functions: **LeftJoin** and **FutureLeftJoin**. The only difference is the temporal direction of the join: whether to join rows in the past or the future.

For example...

Asof Join is useful for dealing with data with different frequency, misaligned timestamps, etc. Further illustrations of this function appear below, in the Case Study section.

### AddColumnsForCycle

***Cycle*** in Flint is defined as “data with the same timestamp”. It is common for people to want to transform data with the same timestamp, for instance, to rank features that have the same timestamp. AddColumnsForCycle is a convenient function for this type of computation.

AddColumnsForCycle takes a user defined function that maps a Pandas series to another Pandas series of the same length.

Some examples include:

**Rank values for each cycle**:

**[Box-Cox transformation](https://en.wikipedia.org/wiki/Power_transform)** is a useful data transformation technique to make the data more like a normal distribution. The following example performs Box-Cox transformation for each cycle:

### Summarizer

Flint summarizers are similar to Spark SQL aggregation functions. Summarizers compute a single value from a list of values. See a full description of Flint summarizers here: [https://ts-flint.readthedocs.io/en/latest/reference.html#module-ts.flint.summarizers](https://ts-flint.readthedocs.io/en/latest/reference.html#module-ts.flint.summarizers).

Flint’s summarizer functions are:

- **summarize**: aggregate data across the entire data frame
- **summarizeCycles**: aggregate data with the same timestamp
- **summarizeIntervals**: aggregate data that belongs to the same time range
- **summarizeWindows**: aggregate data that belongs to the same window
- **addSummaryColumns**: compute cumulative aggregation, such as cumulative sum

An example includes computing [maximum draw-down](https://en.wikipedia.org/wiki/Drawdown_(economics)):

### Window

Flint’s **summarizeWindows** function is similar to rolling window functions in Spark SQL in that it can compute things like rolling averages. The main difference is that summarizeWindows doesn’t require a partition key and can, therefore, handle a single large time series.

Some examples include:

Compute **rolling exponential moving average**:

## Case Study

Now we consider an example where Flint functionalities perform a simple time-series analysis.

### Data Preparation

We have downloaded daily price data for the S&P 500 into a CSV file. First we read the file into a Flint data frame and add a “return” column:

Here, we want to test a very simple idea: can a previous day’s returns be used to predict the next day’s returns? To test the idea, we first need to self-join the return table, so as to create a “preview_day_return” column:

But there is a problem with the joined result: previous_day_return for Mondays are null! That is because we don’t have any return data on weekends, so Monday cannot simply join the return data from Sunday. To deal with this problem, we set the tolerance parameter of leftJoin to '3days', a duration large enough to cover two-day weekends, so Monday can join with last Friday’s returns:

### Feature Engineering

Next we use Flint for some feature transformation. In time-series analysis, it’s quite common to transform a feature based on its past values. Flint’s **summarizeWindows** function can be used for this type of transformation. Below we offer two examples of time-based feature transformation using summarizeWindows: one with built-in summarizer and one with user-defined functions (UDF).

Built-in summarizer:

UDF:

### Model Training

Now that we have prepared the data, we can train a model on it. Here we use Spark ML to fit a linear regression model:

Now that we’ve trained the model, a reasonable next step would be to inspect the results by introspecting the model object to see whether our idea actually works. That takes us outside of our scope in this blog post, so (as the saying goes) we leave model evaluation as an exercise for the reader.

You can try this notebook at [Flint Demo (Databricks Notebook](https://databricks-prod-cloudfront.cloud.databricks.com/public/4027ec902e239c93eaaa8714f173bcfc/1281142885375883/1566406256250190/7729323681064935/latest.html)); refer to `[databricks-flint](https://github.com/databricks/databricks-accelerators/tree/master/projects/databricks-flint)` for more information.

## Summary and Future Roadmap

Flint is a useful library for time-series analysis, complementing other functionality available in Spark SQL. In internal research at Two Sigma, there have been many success stories in using Flint to scale up time-series analysis. We are publishing Flint now, in the hope that it addresses common needs for time-series analysis with Spark. We look forward to working with the Apache Spark community in making Flint an asset not just for Two Sigma, but for the entire community.

In the near future, we plan to start conversations with core Spark maintainers, to discuss a path to make that happen. We also plan to integrate Flint with Catalyst and Tungsten to achieve better performance.

This blog is also cross-posted at [Two Sigma website](https://www.twosigma.com/articles/introducing-flint-a-time-series-library-for-apache-spark/).
