# Databricks Runtime 5.2 ML Features Multi-GPU Workflow, Pregel API, and Performant GraphFrames

- Source: https://www.databricks.com/blog/2019/01/30/databricks-runtime-5-2-ml-features-multi-gpu-workflow-pregel-api-and-performant-graphframes.html
- Published: 2019-01-30
- Authors: Yifan Cao, Joseph Bradley
- Categories: engineering, data-science-machine-learning, platform, open-source
- Images: 1 total, 0 extracted as architecture

We are excited to announce the release of Databricks Runtime 5.2 for Machine Learning. This release includes several new features and performance improvements to help developers easily use machine learning on the [Databricks Unified Analytics Platform](https://www.databricks.com/product/data-lakehouse).

Continuing our efforts to make developers’ lives easy to build deep learning applications, this release includes the following features and improvements:

- HorovodRunner includes a simplified workflow for multi-GPU machines and support for a return value.
- GraphFrames introduces a [Pregel-like API](https://graphframes.github.io/graphframes/docs/_site/api/python/graphframes.lib.html#graphframes.lib.Pregel) for bulk-synchronous message-passing using DataFrame operations, with performance optimizations on Databricks.
- Clusters now start faster.

## Using HorovodRunner for Distributed Training

In [Databricks Runtime 5.0 ML](https://www.databricks.com/blog/2018/11/27/introducing-databricks-runtime-5-0-for-machine-learning.html), we introduced HorovodRunner, a new API for distributed deep learning training. In this release, we introduce two new features.

First, HorovodRunner provides built-in support for using nodes that each have multiple GPUs. On a GPU cluster, each Horovod process maps to one GPU on the cluster, and those processes are placed as groups on compute nodes. For example, if you run a job with np=7 processes on a GPU cluster with 4 GPUs on each node, then you will have 4 processes on the first node and 3 processes on the second node. This simplifies job setup while reducing the inter-task communication costs.

Second, the *HorovodRunner.run()* call can return the value from MPI process 0. This makes it easier for data scientists to fetch helpful results, such as training metrics or the trained model, as in the following code snippet.

To learn about how to run distributed deep learning training on Databricks Runtime 5.2 ML, see the docs at [Azure Databricks](https://docs.microsoft.com/en-us/azure/databricks/applications/machine-learning/train-model/distributed-training/) and [AWS](https://docs.databricks.com/applications/machine-learning/train-model/distributed-training/index.html).

## Pregel API in GraphFrames

[GraphFrames](https://github.com/graphframes/graphframes) is the open-source graph processing library built on top of Apache Spark DataFrames. In the latest release, GraphFrames exposes the Pregel API, which is a bulk-synchronous message-passing API for implementing iterative graph algorithms. For example, the snippet below runs PageRank.

For more details, check the [Scala API](http://graphframes.github.io/graphframes/docs/_site/api/scala/index.html#org.graphframes.lib.Pregel) and [Python API](http://graphframes.github.io/graphframes/docs/_site/api/python/graphframes.lib.html#graphframes.lib.Pregel).

On Databricks Runtime 5.2 ML, we further improved the speed of Pregel implementation from open-source GraphFrames by up to 10x.

## Performance improvements

Including PyTorch in Databricks Runtime 5.1 ML Beta increased cluster start times. In this release, we removed some duplicate libraries that helped lead to 25% faster start times.

## Other Package Updates

We updated the following packages:

- Horovod 0.15.0 to 0.15.2
- TensorBoard 1.12.0 to 1.12.2

## Read More

- Read more about Databricks Runtime 5.2 ML Beta for [Azure Databricks](https://docs.microsoft.com/en-us/azure/databricks/release-notes/runtime/5.2ml#databricks-runtime-5-2-ml-beta) and [AWS](https://docs.databricks.com/release-notes/runtime/5.2ml.html#databricks-runtime-5-2-ml-beta).
- Try the example notebooks for distributed deep learning training for [Azure Databricks](https://docs.microsoft.com/en-us/azure/databricks/applications/machine-learning/train-model/distributed-training/horovod-runner#horovodrunner) and [AWS](https://docs.databricks.com/applications/machine-learning/train-model/distributed-training/horovod-runner.html#horovodrunner) on Databricks Runtime 5.2 ML Beta.
