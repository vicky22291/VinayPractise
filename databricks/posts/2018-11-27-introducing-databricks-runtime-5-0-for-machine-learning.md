# Introducing Databricks Runtime 5.0 for Machine Learning

- Source: https://www.databricks.com/blog/2018/11/27/introducing-databricks-runtime-5-0-for-machine-learning.html
- Published: 2018-11-27
- Authors: Andy Zhang, Hanyu Cui, Hossein Falaki
- Categories: platform, announcements, solutions, engineering, data-science-machine-learning, company
- Images: 1 total, 0 extracted as architecture

*Free Edition has replaced Community Edition, offering enhanced features at no cost. Start using *[*Free Edition *](https://login.databricks.com/?intent=SIGN_UP&amp;signup_experience_step=EXPRESS&amp;provider=DB_FREE_TIER&amp;dbx_source=www)*today.*
 

Six months ago we [introduced the Databricks Runtime for Machine Learning](https://www.databricks.com/blog/2018/06/05/announcing-databricks-runtime-for-machine-learning.html) with the goal of making machine learning performant and easy on the Databricks Unified Analytics Platform. The Databricks Runtime for ML comes pre-packaged with many ML frameworks and enables distributed training and inference. Today we are excited to release the second iteration including Conda support, the latest version of TensorFlow, [HorovodRunner API for Distributed Deep Learning](https://www.databricks.com/blog/2018/11/19/introducing-horovodrunner-for-distributed-deep-learning-training.html) training, and performance optimizations for Graphframes and MLlib.

Our customers’ excitement and reception of the first experimental release of Databricks Runtime for ML, version 4.1, was beyond our expectations. This encouraged us to move the Runtime to a regular production cadence. Starting with Runtime 5.0, we will release a new Runtime for ML with every new DBR release with the most recent stable versions of the main frameworks, such as TensorFlow.

This 5.0 release is available on all Databricks tiers, including the Community Edition. You can find the list of included libraries in our [release notes](https://docs.databricks.com/release-notes/runtime/5.0ml.html), most notably our new API for distributed deep learning training with [HorovodRunner](https://www.databricks.com/blog/2018/11/19/introducing-horovodrunner-for-distributed-deep-learning-training.html). In addition, we are introducing several key improvements that data scientists and machine learning engineers rely on.

## Conda Managed Runtime

Databricks Runtime 5.0 for ML is the first one on which we use Conda for Python package management. All Python packages are installed in a single environment. This is the same environment our library management will install Egg and PyPi packages into.

This is our first step toward a much more data scientist-friendly environment. We will be adding many more features using Conda and make it more prominent as a package manager on our Runtime for ML. You can find instructions for using Conda inside cluster initialization scripts or notebooks [here](https://docs.databricks.com/runtime/mlruntime.html#).

## Upgraded Tensorflow

This version upgrades Tensorflow to [version 1.10](https://github.com/tensorflow/tensorflow/releases/tag/v1.10.0). On GPU clusters, customers will have the CUDA-optimized version, and on standard instances we provide the package that takes advantage of [Intel MKL-DNN](https://www.intel.com/content/www/us/en/developer/tools/oneapi/onemkl.html) to deliver maximum performance on Intel CPUs for numerical computation. Keras version 2.2.4 is also provided.

## Optimized Training Algorithms

We made performance improvements to Spark MLlib logistic regression and tree classifiers, the most popular estimators used by Databricks customers. We observed ~40% speed-up in [Spark Performance Tests](https://github.com/databricks/spark-sql-perf) compared to Apache Spark 2.4.0. You can take advantage of the improved performance on both Databricks Runtime 5.0 and Databricks Runtime 5.0 ML.

The GraphFrames library bundled with Runtime 5.0 ML contains an optimized connected components implementation. It now runs 2-4x faster and supports even bigger graphs. Graph queries will utilize [Spark cost-based optimization (CBO)](https://www.databricks.com/blog/2017/08/31/cost-based-optimizer-in-apache-spark-2-2.html) to determine join orders if the underlying node and edge tables contain column statistics. This can lead to 100x speed-up, depending on your workload and data skew.

## Popular ML Packages

We are including the latest stable version of several other popular machine learning libraries from the Apache Spark and Tensorflow ecosystems.

- XGBoost v0.80
- GraphFrames v0.6.0-db1
- MLeap  v0.13.0
- TensorFrames v0.5.0
- Spark Deep Learning v1.3.0-db1
