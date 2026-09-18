# MLlib Highlights in Apache Spark 1.6

- Source: https://www.databricks.com/blog/2016/01/21/mllib-highlights-in-apache-spark-1-6.html
- Published: 2016-01-21
- Authors: Joseph Bradley
- Categories: engineering, open-source, data-science-machine-learning
- Images: 0 total, 0 extracted as architecture

To learn more about Apache Spark, attend [Spark Summit East in New York in Feb 2016](https://www.databricks.com/dataaisummit).

---

With the latest release, Apache Spark’s Machine Learning library (MLlib) includes many improvements and new features. Users can now save and load ML Pipelines, use extended R and Python APIs, and run new ML algorithms.  This blog post highlights major developments in MLlib 1.6 and mentions the roadmap ahead.

Many thanks to the 90+ contributors during this release, as well as the community for valuable feedback.  MLlib's continued success is due to your hard work!

## Pipeline persistence

After training an ML model, users often need to deploy it in production on another cluster or system.  Model persistence allows users to save a model trained on one system and load that model on a separate production system.  With MLlib 1.6, models and even entire pipelines can be saved and loaded.

This new persistence functionality is part of the Pipelines API, which integrates with DataFrames and provides tools for constructing ML workflows.  To refresh on Pipelines, see our [original blog post](https://www.databricks.com/blog/2015/01/07/ml-pipelines-a-new-high-level-api-for-mllib.html).  With this latest release, a user can train a pipeline, save it, and reload exactly the same pipeline at a later time or on another Spark cluster.  Users can also persist untrained pipelines and individual models.

Saving and loading a full pipeline may be done with single lines of code:

val model = pipeline.fit(data)
 model.save(“s3n://my-location/myModel”)
 val sameModel = PipelineModel.load(“s3n://my-location/myModel”)

To learn more, check out a [simple example in this notebook](https://www.databricks.com/).  Persistence is available in Scala and Java, and Python support will be added in the next release.

 

## New ML algorithms

MLlib 1.6 adds several new ML algorithms for important application areas.

- **Survival analysis** has many applications, such as modeling and predicting customer churn.  (*How long will a customer stay with our product, and what can be done to increase that lifetime?*)  MLlib now has [log-linear models for survival analysis](https://spark.apache.org/docs/latest/ml-classification-regression.html#survival-regression).
-  
- ****Streaming hypothesis testing** **can be used for A/B testing to choose between models or to do canary testing of a new model.  We now provide [testing using the Spark Streaming framework](https://spark.apache.org/docs/latest/mllib-statistics.html#streaming-significance-testing).
-  
- **Summary statistics** in DataFrames help users to quickly understand their data.  Spark 1.6 adds new statistics such as variance, standard deviation, correlations, skewness, and kurtosis.
- **Bisecting k-means clustering** is an accelerated clustering algorithm, useful for identifying patterns and groups within unlabeled data.  [See an example here](https://spark.apache.org/docs/latest/mllib-clustering.html#bisecting-k-means).
- **New feature transformers** in MLlib 1.6 include [ChiSqSelector](https://spark.apache.org/docs/latest/ml-features.html#chisqselector) (feature selection), [QuantileDiscretizer](https://spark.apache.org/docs/latest/ml-features.html#quantilediscretizer) (adaptive discretization of features), and [SQLTransformer](https://spark.apache.org/docs/latest/ml-features.html#sqltransformer) (SQL operations within ML Pipelines).

See the corresponding sections in the [ML User Guide](https://spark.apache.org/docs/latest/ml-guide.html) for examples.

 

## ML in SparkR

Spark 1.5 introduced MLlib in SparkR with Generalized Linear Models (GLMs) as described in the blog post [Generalized Linear Models in SparkR and R Formula Support in MLlib](https://www.databricks.com/blog/2015/10/05/generalized-linear-models-in-sparkr-and-r-formula-support-in-mllib.html). These efforts give R users access to distributed Machine Learning algorithms, using familiar APIs.  Spark 1.6 expands this functionality with two key features.

**Model summary**: R users who inspect Spark Linear Regression models using `summary(model)` will see more statistics, including deviance residuals and coefficient standard errors, t-values, and p-values.

**Feature interactions**: R users can build more expressive GLMs using feature interactions (using the R “:” operator).

The code snippet below demonstrates these new features; see the full example in [this notebook](https://www.databricks.com/).

Model summary statistics and feature interactions in R formulae are also available from the Scala, Java, and Python APIs.

 

## Testable example code (for developers)

For developers, one of the most useful additions to MLlib 1.6 is testable example code.  The code snippets in the user guide can now be tested more easily, which helps to ensure examples do not break across Spark versions.

Specifically, pieces of code in the [“examples” folder](https://github.com/apache/spark/tree/master/examples/src/main) can be inserted into the user guide automatically.  This means that scripts can check to ensure that examples compile and run, rather than requiring developers to check the user guide examples manually.  Thanks to the [many contributors](https://issues.apache.org/jira/browse/SPARK-11337) to this effort!

 

## Looking ahead

We hope to have more MLlib contributors than ever during the upcoming release cycle.

Given very positive feedback about ML Pipelines, we will continue to expand and improve upon this API.  Python support for Pipeline persistence is a top priority.

Generalized Linear Models (GLMs) and the R API are key features for data scientists.  In future releases, we plan to extend functionality with more models families and link functions, better model inspection, and more MLlib algorithms available in R.

For more details on the roadmap, please see the [MLlib 2.0 Roadmap JIRA](https://issues.apache.org/jira/browse/SPARK-12626).  We also recommend that users follow [Spark Packages](https://spark-packages.org/), where many new ML algorithms are hosted.

We always welcome new contributors!  To get started, check out the [MLlib 2.0 Roadmap JIRA](https://issues.apache.org/jira/browse/SPARK-12626) and the [Wiki on Contributing to Spark](https://cwiki.apache.org/confluence/display/SPARK/Contributing+to+Spark).

 

## Learning more

For details on the MLlib 1.6 release, see the release notes.  For guides, examples, and API docs, see the [MLlib User Guide](https://spark.apache.org/docs/latest/mllib-guide.html) and the [Pipelines guide](https://spark.apache.org/docs/latest/ml-guide.html).

Good luck, and thanks for your continued support of MLlib!
