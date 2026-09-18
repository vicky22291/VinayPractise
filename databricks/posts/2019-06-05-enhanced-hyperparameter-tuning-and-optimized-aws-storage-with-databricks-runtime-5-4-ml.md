# Enhanced Hyperparameter Tuning and Optimized AWS Storage with Databricks Runtime 5.4 ML

- Source: https://www.databricks.com/blog/2019/06/05/enhanced-hyperparameter-tuning-and-optimized-aws-storage-with-databricks-runtime-5-4-ml.html
- Published: 2019-06-05
- Authors: Yifan Cao, Joseph Bradley
- Categories: engineering, company, product, data-science-machine-learning, announcements, platform, solutions
- Images: 1 total, 0 extracted as architecture

We are excited to announce the release of Databricks Runtime 5.4 ML ([Azure](https://docs.microsoft.com/en-us/azure/databricks/release-notes/runtime/5.4ml) | [AWS](https://docs.databricks.com/release-notes/runtime/5.4ml.html)). This release includes two Public Preview features to improve data science productivity, optimized storage in AWS for developing distributed applications, and a number of Python library upgrades.

To get started, you simply select the Databricks Runtime 5.4 ML from the drop-down list when you create a new cluster in Databricks.

 Databricks Runtime for Machine Learning, version 5.4

## Public Preview: Distributed Hyperopt + Automated MLflow Tracking

Hyperparameter tuning is a common technique to optimize machine learning models based on hyperparameters, or parameters that are not learned during model training. However, one major challenge with hyperparameter tuning is that it can be both computationally expensive and slow.

[Hyperopt](https://github.com/hyperopt/hyperopt) is a popular open-source hyperparameter tuning library with strong community support (600,000+ PyPI downloads, 3300+ stars on Github as of May 2019). Data scientists like Hyperopt for its simplicity and effectiveness. Hyperopt offers two tuning algorithms: Random Search and the Bayesian method Tree of Parzen Estimators, which offers improved compute efficiency compared to a brute force approach such as grid search. However, distributing Hyperopt previously did not work out of the box and required manual [setup](https://github.com/hyperopt/hyperopt/wiki/Parallelizing-Evaluations-During-Search-via-MongoDB).

In Databricks Runtime 5.4 ML, we introduce an implementation of Hyperopt powered by Apache Spark. Using a new Trials class `SparkTrials`, you can easily distribute a Hyperopt run without making any changes to the current Hyperopt APIs. You simply need to pass in the `SparkTrials` class when applying the `hyperopt.fmin` function (see the example code below). In addition, all tuning experiments, along with the tuned hyperparameters and targeted metrics, are automatically logged to MLflow in Databricks. With this feature, we aim to improve efficiency, scalability, and simplicity when conducting hyperparameter tuning.

This feature is now in Public Preview and we encourage Databricks customers to try it. You can learn more about the feature in the Documentation ([Azure](https://docs.microsoft.com/en-us/azure/databricks/applications/machine-learning/automl-hyperparam-tuning/hyperopt-spark-mlflow-integration) | [AWS](https://docs.databricks.com/applications/machine-learning/automl-hyperparam-tuning/hyperopt-spark-mlflow-integration.html)) section.

At Databricks, we embrace open source communities and APIs. We are working with the Hyperopt community to contribute this Spark-powered implementation to open source Hyperopt. Stay tuned.

## Public Preview: MLlib + Automated MLflow Tracking

Databricks Runtime 5.4 and 5.4 ML supports automatic logging of MLflow runs for models trained using PySpark MLlib tuning algorithms [CrossValidator](https://spark.apache.org/docs/latest/ml-tuning.html) and [TrainValidationSplit](https://spark.apache.org/docs/latest/ml-tuning.html). Before this feature, if you wanted to track PySpark MLlib cross validation or tuning in MLflow, you would have to make explicit MLflow API calls in Databricks notebooks. With MLflow-MLlib integration, when you tune hyperparameters by running `CrossValidator` or `TrainValidationSplit`, parameters and evaluation metrics will be automatically logged to MLflow. You can then review how the tuning affects evaluation metrics in MLflow.

https://www.youtube.com/watch?v=DFn3hS-s7OA

This feature is now in Public Preview. We encourage Databricks users to try it ([Azure](https://docs.microsoft.com/en-us/azure/databricks/applications/machine-learning/automl-hyperparam-tuning/mllib-mlflow-integration) | [AWS](https://docs.databricks.com/applications/machine-learning/automl-hyperparam-tuning/mllib-mlflow-integration.html)).

## Default Optimized FUSE Mount on AWS

The Databricks Runtime has a basic FUSE client for [DBFS](https://docs.databricks.com/data/databricks-file-system.html), a local view of a distributed file system installed on Databricks clusters. This feature has been very popular as it allows local access to remote storage. However, the previous implementation did not allow fast enough data access required for developing distributed deep learning applications.

In Databricks Runtime 5.4, Databricks on AWS now offers an optimized FUSE mount by default. You can now have high-performance data access during training and inference without applying init scripts. Data stored under `dbfs:/ml` and accessible locally at `file:/dbfs/ml` is now backed by this optimized FUSE mount. If you are running on a Databricks Runtime version prior to 5.4, you can follow our [instructions](https://docs.databricks.com/applications/machine-learning/load-data/index.html) to install a high-performance third-party FUSE client.

We introduced the default optimized FUSE mount for Azure Databricks in [Databricks Runtime 5.3](https://www.databricks.com/blog/2019/04/03/databricks-runtime-5-3-ml-now-generally-available.html). By making it available under the same folder name, we achieved feature parity across Azure and AWS platforms.

In the upcoming months, we plan to enhance the DBFS FUSE client for data scientists who would like flexibility in how they access data.

## Display HorovodRunner Training Logs

In the past we introduced [HorovodRunner](https://www.databricks.com/blog/2018/11/19/introducing-horovodrunner-for-distributed-deep-learning-training.html), a simple way to distribute Deep Learning training workloads in Databricks. Databricks Runtime 5.4 ML improves the user experience by displaying HorovodRunner training logs in Databricks Notebook cells. In order to review training logs to better understand optimization progress, you no longer have to look through executor logs under the Spark UI ([Azure](https://docs.microsoft.com/en-us/azure/databricks/clusters/clusters-manage#clusters-sparkui) | [AWS](https://docs.databricks.com/clusters/clusters-manage.html)). Now, while the HorovodRunner jobs are being executed, training logs will be automatically collected to the driver node and displayed in the notebook cells. You can learn more in our Documentation ([Azure](https://docs.microsoft.com/en-us/azure/databricks/applications/machine-learning/train-model/deep-learning#distributed-training) | [AWS](https://docs.databricks.com/applications/machine-learning/train-model/deep-learning.html#distributed-training)).

## Other Library Updates

We updated the following libraries in Databricks Runtime 5.4 ML:

- Pre-installed XGBoost Python package 0.80.
- r-base version bumped from 3.5.2 to 3.6.0.
- We published instructions ([Azure](https://docs.microsoft.com/en-us/azure/databricks/applications/machine-learning/train-model/tensorflow) | [AWS](https://docs.databricks.com/applications/machine-learning/train-model/tensorflow.html)) to install TensorFlow 1.13 and 2.0-alpha to Databricks Runtime ML

## Read More

- Databricks Runtime 5.4 ML release notes ([Azure](https://docs.microsoft.com/en-us/azure/databricks/release-notes/runtime/5.4ml#databricks-runtime-5-4-ml) | [AWS](https://docs.databricks.com/release-notes/runtime/5.4ml.html#databricks-runtime-5-4-ml))
- Databricks Documentation - Machine Learning ([Azure](https://docs.microsoft.com/en-us/azure/databricks/applications/machine-learning/#machine-learning) | [AWS](https://docs.databricks.com/applications/machine-learning/index.html#machine-learning))
- Hyperparameter Tuning Overview ([blog post](https://www.databricks.com/blog/2019/06/07/hyperparameter-tuning-with-mlflow-apache-spark-mllib-and-hyperopt.html) and [June 20 webinar](https://pages.databricks.com/201906-WB-AutomatedHyperparameterTuning_Reg.html))
- Spark AI Summit 2019 Talk: “[Best Practices for Hyperparameter Tuning with MLflow](https://www.databricks.com/session/best-practices-for-hyperparameter-tuning-with-mlflow)” by Joseph Bradley
- Spark AI Summit 2019 Talk: [“Advanced Hyperparameter Optimization for Deep Learning with MLflow”](https://www.databricks.com/session/advanced-hyperparameter-optimization-for-deep-learning-with-mlflow) by Maneesh Bhide
- Try the example notebooks for distributed deep learning training for [Azure Databricks](https://docs.microsoft.com/en-us/azure/databricks/applications/machine-learning/train-model/distributed-training/horovod-runner#examples) and [AWS](https://docs.databricks.com/applications/machine-learning/train-model/distributed-training/horovod-runner.html#examples) on Databricks Runtime 5.4 ML
