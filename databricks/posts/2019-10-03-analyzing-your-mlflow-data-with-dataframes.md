# Analyzing Your MLflow Data with DataFrames

- Source: https://www.databricks.com/blog/2019/10/03/analyzing-your-mlflow-data-with-dataframes.html
- Published: 2019-10-03
- Authors: Max Allen
- Categories: engineering, data-science-machine-learning
- Images: 1 total, 0 extracted as architecture

>  Max Allen interned with Databricks Engineering in the Summer of 2019. This blog post, written by Max, highlights the great work he did while on the team.

## Introduction to MLflow and the Machine Learning Development Lifecycle

[MLflow](https://mlflow.org/) is an open source platform for the machine learning lifecycle, and many Databricks customers have been using it to develop and deploy models that [detect financial fraud](https://www.databricks.com/blog/2019/05/02/detecting-financial-fraud-at-scale-with-decision-trees-and-mlflow-on-databricks.html), [find sales trends](https://www.databricks.com/blog/2019/04/30/understanding-dynamic-time-warping.html), and [power ride-hailing](https://www.databricks.com/session/scaling-ride-hailing-with-machine-learning-on-mlflow). A critical part of the [machine learning development life cycle](https://www.databricks.com/product/machine-learning-runtime)is testing out different models, each of which could be constructed using different algorithms, hyperparameters and datasets. The MLflow Tracking component allows for all these parameters and attributes of the model to be tracked, as well as key metrics such as accuracy, loss, and AUC. Luckily, since we introduced auto-logging in [MLflow 1.1](https://www.databricks.com/blog/2019/07/23/announcing-the-mlflow-1-1-release.html), much of this tracking work will be taken care of for you.

The next step in the process is to understand which machine learning model performs the best based on the outcome metrics. When you just have a handful of runs to compare, the MLflow UI’s compare runs feature works well. You can view the metrics of the runs lined up next to each other and create scatter, line, and parallel coordinate plots.

## Two New APIs for Analyzing Your MLflow Data

However, as the number of runs and models in an experiment grows (particularly after running an [AutoML](https://www.databricks.com/product/automl)or hyperparameter search algorithm), it becomes cumbersome to do this analysis in the UI. In some cases, you’ll want direct access to the experiment data to create your own plots, do additional data-engineering, or use the data in a multi-step workflow. This is why we’ve created two new APIs that allow users to access their MLflow data as a DataFrame. The first is an [API accessible from the MLflow Python](https://docs.databricks.com/applications/mlflow/tracking.html)client that returns a [pandas DataFrame](https://www.databricks.com/glossary/pandas-dataframe). The second is an Apache Spark Data Source API that loads data from MLflow experiments into a Spark DataFrame. Once you have your run data accessible in a DataFrame, there are many different types of analyses that can be done to help you choose the best machine learning models for your application.

## pandas DataFrame Search API

*Note: The pandas DataFrame Search API is available in MLflow open source versions 1.1.0 or greater. It is also pre-installed on Databricks Runtime 6.0 ML and greater.*

Since pandas is such a commonly used library for data scientists, we decided to create a **mlflow.search_runs()** API that returns your MLflow runs in a [pandas DataFrame](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.html). This API takes in similar arguments as the **mlflow.tracking.search_runs()** API, except for the page_token parameter. This API automatically paginates through all your runs and adds them to the DataFrame. Using it is extremely simple:

If you don’t provide an experiment ID, the API tries to find the MLflow experiment associated with your notebook. This will work in the case when you’ve previously created MLflow runs in this notebook. Otherwise, to get the ID for a particular experiment, you can either find it in the MLflow UI:

Or you can get it programmatically if you know the full name of the experiment:

The search API also takes in optional parameters such as a filter string, which follows the search syntax described in the [MLflow search docs](https://mlflow.org/docs/latest/search-syntax.html). Loading the models with metric “accuracy” greater than 85% would look like the following query:
