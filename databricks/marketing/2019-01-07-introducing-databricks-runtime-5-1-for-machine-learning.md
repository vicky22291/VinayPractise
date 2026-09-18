# Introducing Databricks Runtime 5.1 for Machine Learning

- Source: https://www.databricks.com/blog/2019/01/07/introducing-databricks-runtime-5-1-for-machine-learning.html
- Published: 2019-01-07
- Authors: Hossein Falaki, Hanyu Cui, Andy Zhang
- Categories: engineering, company, data-science-machine-learning, announcements, open-source
- Images: 1 total, 0 extracted as architecture

Last week, we released Databricks Runtime 5.1 Beta for Machine Learning. As part of our commitment to provide developers with the latest deep learning frameworks, this release includes the best of these libraries. In particular, our [PyTorch](https://pytorch.org/) addition makes it simple for a developer to simply import the appropriate Python `torch` modules and start coding, without installing all of its myriad dependencies. In this blog, we briefly cover these additions.

## PyTorch

[PyTorch](https://pytorch.org/) project is a popular deep learning Python package that provides GPU accelerated tensor computation and high-level functionalities for building deep learning networks. PyTorch provides flexible Tensors APIs that are similar to NumPy arrays but they can be accelerated on GPUs.

Several Databricks customers asked for built-in support for PyTorch, both for single-node and distributed deep learning applications using [HorovodRunner](https://www.databricks.com/blog/2018/11/19/introducing-horovodrunner-for-distributed-deep-learning-training.html). With this release, we are including Pytorch version 0.4.1 along with tensorboardX version 1.4. In the future releases, we plan to keep PyTorch support up to date.

To get started quickly, we have included a few examples of how to use PyTorch on Databricks for single-node and distributed deep learning in our user guide (see documentation below).

https://www.youtube.com/watch?v=Sq5PV3mlUCI

## Updated TensorFlow

To keep abreast with the fast-moving TensorFlow project and provide our customers with its latest features, we have included the latest stable version of [TensorFlow 1.12](https://www.tensorflow.org/) as part of Databricks Runtime 5.1 ML Beta.

## Other Machine Learning Packages

We updated the following packages

- [XGBoost 0.8.1](https://xgboost.readthedocs.io/en/latest/)
- [TensorFrames 0.6.0](https://github.com/databricks/tensorframes/releases)
- [Spark Deep Learning 1.4.0-db2](https://spark-packages.org/package/databricks/spark-deep-learning)

## Read More

- Read more about Databricks Runtime (DBR) 5.1 Beta for ML for [Azure Databricks](https://docs.microsoft.com/en-us/azure/databricks/release-notes/runtime/5.1ml#databricks-runtime-5-1-ml-beta) and [AWS](https://docs.databricks.com/release-notes/runtime/5.1ml.html#databricks-runtime-5-1-ml-beta)
- Try the Horovod notebooks for Distributed Training for [Azure Databricks](https://docs.microsoft.com/en-us/azure/databricks/applications/machine-learning/train-model/distributed-training/horovod-runner#horovodrunner) and [AWS](https://docs.databricks.com/applications/machine-learning/train-model/distributed-training/horovod-runner.html#horovodrunner) on DBR ML 5.1 Beta.
