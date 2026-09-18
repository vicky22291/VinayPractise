# Apache Spark 2.0 Preview: Machine Learning Model Persistence

- Source: https://www.databricks.com/blog/2016/05/31/apache-spark-2-0-preview-machine-learning-model-persistence.html
- Published: 2016-05-31
- Authors: Joseph Bradley
- Categories: engineering, data-science-machine-learning
- Images: 1 total, 0 extracted as architecture

*Free Edition has replaced Community Edition, offering enhanced features at no cost. Start using *[*Free Edition *](https://login.databricks.com/?intent=SIGN_UP&amp;signup_experience_step=EXPRESS&amp;provider=DB_FREE_TIER&amp;dbx_source=www)*today.*
 

## Introduction

Consider these Machine Learning (ML) use cases:

- A data scientist produces an ML model and hands it over to an engineering team for deployment in a production environment.
- A data engineer integrates a model training workflow in Python with a model serving workflow in Java.
- A data scientist creates jobs to train many ML models, to be saved and evaluated later.

All of these use cases are easier with model persistence, the ability to save and load models. With the upcoming release of [Apache Spark 2.0](https://www.databricks.com/blog/2016/05/11/apache-spark-2-0-technical-preview-easier-faster-and-smarter.html), Spark’s [Machine Learning library](https://www.databricks.com/glossary/what-is-machine-learning-library) MLlib will include near-complete support for ML persistence in the DataFrame-based API. This blog post gives an early overview, code examples, and a few details of MLlib’s persistence API.

Key features of ML persistence include:

- Support for all language APIs in Spark: Scala, Java, Python & R
- Support for nearly all ML algorithms in the DataFrame-based API
- Support for single models and full Pipelines, both unfitted (a “recipe”) and fitted (a result)
- Distributed storage using an exchangeable format

Thanks to all of the community contributors who helped make this big leap forward in MLlib! See the JIRAs for [Scala/Java](https://issues.apache.org/jira/browse/SPARK-6725), [Python](https://issues.apache.org/jira/browse/SPARK-11939), and [R](https://issues.apache.org/jira/browse/SPARK-14311) for full lists of contributors.

## Learn the API

In Apache Spark 2.0, the DataFrame-based API for MLlib is taking the front seat for ML on Spark. (See [this previous blog post](https://www.databricks.com/blog/2015/01/07/ml-pipelines-a-new-high-level-api-for-mllib.html) for an introduction to this API and the “Pipelines” concept it introduces.) This DataFrame-based API for MLlib provides functionality for saving and loading models that mimics the familiar Spark Data Source API.

We will demonstrate saving and loading models in several languages using the popular MNIST dataset for handwritten digit recognition (LeCun et al., 1998; available from the [LibSVM dataset page](https://www.csie.ntu.edu.tw/~cjlin/libsvmtools/datasets/multiclass.html#mnist)). This dataset contains handwritten digits 0–9, plus the ground truth labels. Here are some examples:

Our goal will be to take new images of handwritten digits and identify the digit. See [this notebook](https://www.databricks.com/wp-content/uploads/hubfs/notebooks/spark2.0/ML%20persistence%20in%202.0.html) for the full example code to load this data, fit the models, and save and load them.

### Save & load single models

We first show how to save and load single models to share between languages. We will fit a Random Forest Classifier using Python, save it, and then load the same model back using Scala.

training = sqlContext.read... # data: features, label
rf = RandomForestClassifier(numTrees=20)
model = rf.fit(training)

We can simply call the `save` method to save this model, and the `load` method to load it right back:

model.save("myModelPath")
sameModel = RandomForestClassificationModel.load("myModelPath")

We could also load that same model (which we saved in Python) into a Scala or Java application:

// Load the model in Scala
val sameModel = RandomForestClassificationModel.load("myModelPath")

This works for both small, local models such as K-Means models (for clustering) and large, distributed models such as ALS models (for recommendation). The loaded model has the same parameter settings and data, so it will return the same predictions even if loaded on an entirely different Spark deployment.

### Save & load full Pipelines

So far, we have only looked at saving and loading a single ML model. In practice, ML workflows consist of many stages, from feature extraction and transformation to model fitting and tuning. MLlib provides Pipelines to help users construct these workflows.
MLlib allows users to save and load entire Pipelines. Let’s look at how this is done on an example Pipeline with these steps:

- Feature extraction: Binarizer to convert images to black and white
- Model fitting: Random Forest Classifier to take images and predict digits 0–9
- Tuning: Cross-Validation to tune the depth of the trees in the forest

Here is a snippet from our notebook to build this Pipeline:

// Construct the Pipeline: Binarizer + Random Forest
val pipeline = new Pipeline().setStages(Array(binarizer, rf))

// Wrap the Pipeline in CrossValidator to do model tuning.
val cv = new CrossValidator().setEstimator(pipeline) ...

Before we fit this Pipeline, we will show that we can save entire workflows (before fitting). This workflow could be loaded later to run on another dataset, on another Spark cluster, etc.

cv.save("myCVPath")
val sameCV = CrossValidator.load("myCVPath")

Finally, we can fit the Pipeline, save it, and load it back later. This saves the feature extraction step, the Random Forest model tuned by Cross-Validation, and the statistics from model tuning.

val cvModel = cv.fit(training)
cvModel.save("myCVModelPath")
val sameCVModel = CrossValidatorModel.load("myCVModelPath")

## Learn the details

### Python tuning

The one missing item in Spark 2.0 is Python tuning. Python does not yet support saving and loading CrossValidator and TrainValidationSplit, which are used to tune model hyperparameters; this issue is targeted for Spark 2.1 ([SPARK-13786](https://issues.apache.org/jira/browse/SPARK-13786)). However, it is still possible to save the results from CrossValidator and TrainValidationSplit from Python. For example, let’s use Cross-Validation to tune a Random Forest and then save the best model found during tuning.

### Define the workflow

rf = RandomForestClassifier()
cv = CrossValidator(estimator=rf, ...)

### Fit the model, running Cross-Validation

cvModel = cv.fit(trainingData)

### Extract the results, i.e., the best Random Forest model

bestModel = cvModel.bestModel

### Save the RandomForest model

bestModel.save("rfModelPath")

See [the notebook](https://www.databricks.com/wp-content/uploads/hubfs/notebooks/spark2.0/ML%20persistence%20in%202.0.html) for the full code.

### Exchangeable storage format

Internally, we save the model metadata and parameters as JSON and the data as Parquet. These storage formats are exchangeable and can be read using other libraries. Parquet allows us to store both small models (such as Naive Bayes for classification) and large, distributed models (such as ALS for recommendation). The storage path can be any URI supported by Dataset/DataFrame save and load, including paths to S3, local storage, etc.

### Language cross-compatibility

Models can be easily saved and loaded across Scala, Java, and Python. R has two limitations. First, not all MLlib models are supported from R, so not all models trained in other languages can be loaded into R. Second, the current R model format stores extra data specific to R, making it a bit hacky to use other languages to load models trained and saved in R. (See [the accompanying notebook](https://www.databricks.com/wp-content/uploads/hubfs/notebooks/spark2.0/ML%20persistence%20in%202.0.html) for the hack.) Better cross-language support for R will be added in the near future.

## Conclusion

With the upcoming 2.0 release, the DataFrame-based MLlib API will provide near-complete coverage for persisting models and Pipelines. Persistence is critical for sharing models between teams, creating multi-language ML workflows, and moving models to production. This feature was a final piece in preparing the DataFrame-based MLlib API to become the primary API for Machine Learning in Apache Spark.

## What’s next?

High-priority items include complete persistence coverage, including Python model tuning algorithms, as well as improved compatibility between R and the other language APIs.

**Get started** with [this tutorial notebook](https://www.databricks.com/wp-content/uploads/hubfs/notebooks/spark2.0/ML%20persistence%20in%202.0.html) in Scala and Python. You can also just update your current MLlib workflows to use save and load.
**Experiment with** this API using an Apache Spark branch-2.0 preview in the Databricks Community Edition beta program.

## Read More

- Read [the notebook](https://www.databricks.com/wp-content/uploads/hubfs/notebooks/spark2.0/ML%20persistence%20in%202.0.html) with the full code referenced in this blog post.
- Learn about the DataFrame-based API for MLlib & ML Pipelines:
  - [Original blog post on ML Pipelines](https://www.databricks.com/blog/2015/01/07/ml-pipelines-a-new-high-level-api-for-mllib.html)
