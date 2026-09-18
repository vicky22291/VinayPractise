# Announcing Ray support on Databricks and Apache Spark Clusters

- Source: https://www.databricks.com/blog/2023/02/28/announcing-ray-support-databricks-and-apache-spark-clusters.html
- Published: 2023-02-28
- Authors: Weichen Xu, Ben Wilson, Jiajun Yao, Zhe Zhang, Eric Liang, Xiangrui Meng, Corey Zumar
- Categories: engineering, open-source
- Images: 2 total, 0 extracted as architecture

[Ray](https://www.ray.io/) is a prominent compute framework for running scalable AI and Python workloads, offering a variety of distributed machine learning tools, large-scale hyperparameter tuning capabilities, reinforcement learning algorithms, model serving, and more. Similarly, Apache Spark™ provides a wide variety of high-performance algorithms for distributed machine learning through [Spark MLlib](https://spark.apache.org/docs/latest/ml-guide.html) and deep integrations with machine learning frameworks including [XGBoost](https://xgboost.readthedocs.io/en/stable/tutorials/spark_estimator.html), [TensorFlow](https://docs.databricks.com/machine-learning/train-model/distributed-training/horovod-spark.html), and [PyTorch](https://docs.databricks.com/machine-learning/train-model/distributed-training/horovod-spark.html). In order to build the best models, machine learning practitioners frequently need to explore multiple algorithms, often requiring the use of multiple platforms including both Ray and Spark. Today, with the release of Ray version 2.3.0, we are excited to announce that Ray workloads are now supported on Databricks and Spark standalone clusters, dramatically simplifying model development across both platforms.

**Create a Ray cluster on Databricks or Spark**
 To start Ray on your Databricks or Spark cluster, simply install the latest version of Ray and call the `ray.util.spark.setup_ray_cluster()` function, specifying the number of Ray workers and the compute resource allocation. Any Databricks cluster with [Databricks Runtime](https://docs.databricks.com/runtime/index.html) version 12.0 or above is supported, as well as any Spark cluster running version 3.3 or above. For example, the following code installs Ray in a Databricks notebook and initializes a Ray cluster with two worker nodes:

With just a few lines of code, you have created a Ray cluster and are ready to start training models.

**Train models with Ray Train and Ray RLlib**
 Now that you've started a Ray cluster, it's time to harness the power of distributed machine learning to build a model. All Ray applications and Ray-integrated machine learning algorithms are supported on Databricks and Spark clusters without any modifications. For example, you can use the [Ray Train API](https://docs.ray.io/en/latest/train/api.html) in your Databricks notebook to easily distribute your XGBoost model training, reducing training time and improving model accuracy:

Ray also provides native support for reinforcement learning. For example, you can run the following [Ray RLlib code](https://docs.ray.io/en/latest/rllib/index.html) in your Databricks notebook to train a PPO reinforcement learning algorithm in the [Taxi Gymnasium environment](https://gymnasium.farama.org/environments/toy_text/taxi/#taxi):

For additional model training information and examples, check out the [Ray Train documentation](https://docs.ray.io/en/latest/train/train.html#ray-train-scalable-model-training) and the [Ray RLlib documentation](https://docs.ray.io/en/latest/rllib/index.html).

**Find optimal models with Ray Tune**
 To improve the quality of your models, you can also leverage [Ray Tune](https://docs.ray.io/en/latest/tune/index.html) to explore thousands of model parameter configurations in parallel at scale. For example, the following code uses Ray Tune to optimize a scikit-learn classification model:

More information and examples about model tuning on Ray, including the use of [Ray with MLflow](https://docs.ray.io/en/latest/tune/examples/tune-mlflow.html), is available in the [Ray Tune documentation](https://docs.ray.io/en/latest/tune/index.html).

**View the Ray dashboard**

After starting Ray on a Databricks cluster, a link to the Ray dashboard is displayed.

Throughout model development, you can monitor the progress of your Ray machine learning tasks and the health of your Ray nodes using the [Ray dashboard](https://docs.ray.io/en/latest/ray-core/ray-dashboard.html). When you create your Ray cluster, the `ray.util.spark.setup_ray_cluster()` displays a link to the Ray dashboard.

The Ray dashboard provides a detailed view of your cluster's nodes, actors, logs, and more.

The Ray dashboard provides a comprehensive view of Ray cluster's nodes, actors, metrics, and event logs. You can easily view resource utilization metrics for individual nodes and aggregate metrics across all nodes. For more information about the Ray dashboard, visit the [Ray dashboard documentation](https://docs.ray.io/en/latest/ray-core/ray-dashboard.html).

**Get started with Ray on Databricks or Spark today**
 With the availability of Ray 2.3.0, you can start running Ray applications on your Databricks or Spark clusters today. If you're a Databricks customer, simply create a Databricks cluster with version 12.0 or higher of the [Databricks Runtime](https://docs.databricks.com/runtime/index.html) and check out the [Ray on Databricks documentation](https://docs.databricks.com/machine-learning/ray-integration.html) to get started. Finally, instructions for launching Ray on a standalone Spark cluster are provided in the [Ray on Spark documentation](https://docs.ray.io/en/latest/cluster/vms/user-guides/community/spark.html#deploying-on-spark-standalone-cluster), and you can visit [https://docs.ray.io/en/latest/](https://docs.ray.io/en/latest/) to learn more about machine learning on Ray.

We are very excited about this step forward in interoperability for distributed machine learning and look forward to powering your Ray applications on Apache Spark™ and Databricks!
