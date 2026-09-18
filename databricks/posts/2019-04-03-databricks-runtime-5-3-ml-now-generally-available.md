# Databricks Runtime 5.3 ML Now Generally Available

- Source: https://www.databricks.com/blog/2019/04/03/databricks-runtime-5-3-ml-now-generally-available.html
- Published: 2019-04-03
- Authors: Yifan Cao, Hanyu Cui
- Categories: announcements, product, solutions, engineering, data-science-machine-learning, company
- Images: 0 total, 0 extracted as architecture

We are excited to announce the general availability (GA) of Databricks Runtime for Machine Learning, as part of the release of Databricks Runtime 5.3 ML. Built on top of Databricks Runtime, Databricks Runtime ML is the optimized runtime for developing ML/DL applications in Databricks. It offers native integration with popular ML/DL frameworks, such as scikit-learn, XGBoost, TensorFlow, PyTorch, Keras, Horovod, etc. In addition to pre-configuring these popular frameworks, DBR ML makes these frameworks easier to use, more reliable, and more performant.

Since we introduced Databricks Runtime for Machine Learning in preview in June 2018, we’ve witnessed exponential adoption in terms of both total workloads and the number of users. Close to 1000 organizations have tried Databricks Runtime ML preview versions over the past ten months. To meet the rapidly growing demand, we continued to improve our integration and testing to arrive at a robust cadence of updating and adding libraries in Databricks Runtime ML. In addition, Databricks offers optimized features to improve the experience using these frameworks for developers. The positive feedback from our customers has led us to make Databricks Runtime for Machine Learning generally available (GA).

Databricks Runtime ML is now generally available across all Databricks product offerings:

- Azure Databricks
- AWS cloud
- GPU clusters
- CPU clusters

To get started, you simply select the Databricks Runtime 5.3 ML from the drop-down list when you create a new cluster in Databricks:

https://www.youtube.com/watch?v=yhLKu0O_qds

## Advantages of Databricks Runtime for Machine Learning

Databricks Runtime for Machine Learning focuses on three key areas: usability, reliability, and performance.

### Ease of Use

All of the libraries identified in “Tiered Libraries in Databricks Runtime ML” (see below) come pre-configured in Databricks Runtime ML. You can start developing machine learning applications right away without the need to configure the environments themselves.

In the Databricks Runtime [5.0 ML](https://www.databricks.com/blog/2018/11/27/introducing-databricks-runtime-5-0-for-machine-learning.html) release, we introduced HorovodRunner, which makes it easy to use the distributed deep learning framework Horovod. One key challenge with Horovod is usability, as it requires you to share code and libraries across nodes, configure SSH, execute complicated MPI commands, and so on. HorovodRunner abstracts all of these complications by providing a simple API to allow you to easily leverage the benefits of Horovod. With a few lines of code change, you can easily migrate your single node deep learning training code to run in a Databricks cluster.

Many ML libraries are developed for single-node use cases. We are constantly evaluating popular ML libraries and looking for ways to make them easier to run in a distributed system. For example, we are currently working on a distributed hyperparameter tuning feature. Stay tuned.

### Reliability

Machine learning is a rapidly evolving space, and we want to make the latest and greatest tools available in Databricks Runtime for Machine Learning. Each of the pre-configured ML libraries in Databricks Runtime ML regularly releases new versions. To stabilize our environment, Databricks engineering runs daily integration tests against Databricks Runtime ML and stress-tests all new libraries before integrating or updating existing libraries.

Since the release of Databricks Runtime ML Beta ten months ago, we continued to expand our test suites and incorporated feedback from almost 1000 organizations to make ML workflows run smoothly.

We’ve taken a focused approach to maintaining and updating libraries in Databricks Runtime ML. Based on customer demand and market trends, we identified a list of libraries as “top-tier” libraries. For these “top-tier” libraries, Databricks plans to make faster updates and provides advanced support. See details in the “Tiered Libraries in Databricks Runtime ML” section below. With robust testing & integration in place, we feel confident to regularly add and update popular ML libraries in future Databricks Runtime ML releases.

Finally, a major initiative for Databricks Runtime ML in 2019 is to allow you to customize your ML environment. We are working on solutions that would let you to easily cherry-pick just the right set of ML libraries to include in Databricks Runtime ML. A lighter environment could lead to additional improvement in stability. Please stay tuned.

### Performance

Databricks Runtime ML includes performance improvements beyond what is available in “off the shelf” open-source versions of several libraries. In the Databricks Runtime [5.0 ML](https://www.databricks.com/blog/2018/11/27/introducing-databricks-runtime-5-0-for-machine-learning.html) release, we made improvements to both Apache Spark MLlib logistic regression and tree classifiers. When running in Databricks Runtime for ML, we observed ~40% speed-up in [Spark Performance Tests](https://github.com/databricks/spark-sql-perf) compared to Apache Spark 2.4.0.

The GraphFrames library in Databricks Runtime for ML also contains an optimized implementation. Starting in 5.0 ML, GraphFrames in Databricks Runtime ML runs 2-4 times faster and supports even bigger graphs compared to open-source GraphFrames. Graph queries will utilize [Spark cost-based optimization (CBO)](https://www.databricks.com/blog/2017/08/31/cost-based-optimizer-in-apache-spark-2-2.html) to determine the join orders if the underlying node and edge tables contain column statistics. This can lead to as much as 100 times speed up, depending on the workloads and data skew.

The improved performance is only available in Databricks. You can take advantage of the improved performance in both Databricks Runtime and Databricks Runtime for ML.

We’ve also improved cluster launch time by 25% by reducing image size.

## Tiered Libraries in Databricks Runtime ML

The Databricks Runtime for Machine Learning includes a variety of popular ML libraries. The libraries are updated regularly to include new features and fixes. A subset of popular libraries are marked as top-tier libraries. For these libraries, Databricks provides a faster update cadence, updating to the latest upstream package releases with each runtime release (barring dependency conflicts). Databricks also provides advanced support, testing, and embedded optimizations for top-tier libraries. Databricks Runtime 5.3 for Machine Learning includes the following libraries:

Top-tier libraries:

- TensorFlow / TensorBoard / tf.keras
- spark-tensorflow-connector
- PyTorch
- Horovod / HorovodRunner
- GraphFrames

Other provided libraries:

- Keras
- spark-xgboost
- MLeap
- scikit-learn
- pandas
- Deep Learning Pipelines for Apache Spark
- TensorFrames

## Default Optimized FUSE Mount in Azure Databricks

Databricks Runtime has a basic FUSE client for [DBFS](https://docs.databricks.com/data/databricks-file-system.html), a local distributed file system installed on Databricks clusters. This feature has been very popular as it allows local access to remote storage. However, the current implementation does not allow fast enough data access required for developing distributed applications.

In Databricks Runtime 5.3, Azure Databricks now offers an optimized FUSE mount by default. You can now have high-performance data access during training and inference without applying init scripts. Data stored under dbfs:/ml and accessible locally at file:/dbfs/ml is now backed by this optimized FUSE mount. If you are running on a Databricks Runtime version prior to 5.3, you can follow our [instructions](https://docs.microsoft.com/en-us/azure/databricks/applications/machine-learning/load-data/) to install a high-performance third-party FUSE client.

We are working on making a default optimized FUSE mount for Databricks users on AWS, thus achieving feature parity across Azure and AWS platforms.

## Private Preview: MLlib-MLflow Integration

Databricks Runtime 5.3 ML supports automatic logging of MLflow runs for models fit using PySpark MLlib tuning algorithms [CrossValidator](https://spark.apache.org/docs/latest/ml-tuning.html) and [TrainValidationSplit](https://spark.apache.org/docs/latest/ml-tuning.html). Before 5.3 ML, if you wanted to track PySpark MLlib cross validation or tuning in MLflow, you would have to make explicit MLflow API calls in Databricks notebooks. With MLflow-MLlib integration, when you tune hyperparameters by running CrossValidator or TrainValidationSplit, parameters and evaluation metrics will be automatically logged to MLflow. You can then review how the tuning affects evaluation metrics in MLflow.

This feature is in private preview. Contact your Databricks sales representative to learn about enabling it.

## Other Library Updates

We updated the following libraries in Databricks Runtime 5.3 ML:

- Horovod 0.16.0
- TensorBoardX 1.6
- PyArrow 0.12.1 (including support for BinaryType data)
- The Databricks ML Model Export API has been deprecated. Databricks recommends using MLeap instead, which provides broader coverage of MLlib model types

## Read More

- Read more about Databricks Runtime 5.3 ML for [Azure Databricks](https://docs.microsoft.com/en-us/azure/databricks/release-notes/runtime/5.3ml#databricks-runtime-5-3-ml-beta) and [AWS](https://docs.databricks.com/release-notes/runtime/5.3ml.html#databricks-runtime-5-3-ml-beta).
- Try the example notebooks for distributed deep learning training for [Azure Databricks](https://docs.microsoft.com/en-us/azure/databricks/applications/machine-learning/train-model/distributed-training/horovod-runner#examples) and [AWS](https://docs.databricks.com/applications/machine-learning/train-model/distributed-training/horovod-runner.html#examples) on Databricks Runtime 5.3 ML.
