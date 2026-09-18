# Introducing HorovodRunner for Distributed Deep Learning Training

- Source: https://www.databricks.com/blog/2018/11/19/introducing-horovodrunner-for-distributed-deep-learning-training.html
- Published: 2018-11-19
- Authors: Yogesh Garg, Lu Wang, Bagrat Amirbekian, Joseph Bradley, Jules Damji
- Categories: engineering
- Images: 0 total, 0 extracted as architecture

Today, we are excited to introduce HorovodRunner in our [Databricks Runtime 5.0 ML](https://docs.databricks.com/release-notes/runtime/5.0ml.html)!

HorovodRunner provides a simple way to scale up your deep learning training workloads from a single machine to large clusters, reducing overall training time.

Motivated by the needs of many of our users who want to train deep learning models on datasets that do not fit on a single machine and reduce overall training time, HorovodRunner addresses this requirement by distributing training across your clusters, hence processing more data per second and decreasing the training time from hours to minutes.

As part of an effort to integrate distributed deep learning with Apache Spark, leveraging [Project Hydrogen,](https://www.databricks.com/blog/2018/07/25/bay-area-apache-spark-meetup-summary-databricks-hq.html) HorovodRunner utilizes barrier execution mode introduced in [Apache Spark 2.4.](https://www.databricks.com/blog/2018/11/08/introducing-apache-spark-2-4.html) This new model of execution is different from the generic Spark execution model and is catered to distributed training in its fault-tolerance needs and modes of communication between tasks on each worker node in the cluster.

In this blog, we describe HorovodRunner and how you can use HorovodRunner’s simple API to train your deep learning model in a distributed fashion, letting Apache Spark handle all the coordination and communication among tasks on each worker node in the cluster.

## HorovodRunner’s Simple API

[Horovod](https://github.com/horovod/horovod), Uber’s open source distributed training framework, supports [TensorFlow](https://www.tensorflow.org/), [Keras](https://keras.io/), and [PyTorch](https://pytorch.org/). HorovodRunner, built on top of Horovod, inherits the support of these deep learning frameworks and makes it much easier to run.

Under the hood, HorovodRunner shares code and libraries across machines, configures SSH, and executes the complicated MPI commands required for distributed training.

As result, data scientists are freed from the burden of operational requirements and can now focus on tasks at hand—building models, experimenting, and deploying them to production quickly.

Also, HorovodRunner provides a simple interface that allows you to easily distribute your workloads on a cluster. For example, the snippet below runs the train function on 4 worker machines. This can help you achieve good scaling of your workloads, accelerate model experimenting, and shorten the time to production.

The train method below contains the Horovod training code. The sample code outlines the small changes to your single-node workloads to use Horovod. With a few lines of code changes and using HorovodRunner, you can start leveraging the power of a cluster in a matter of minutes.

## Integrated Workflow on Databricks

HorovodRunner launches Horovod training jobs as Spark jobs. So your development workflow is exactly the same as other Spark jobs on Databricks. For example, you can check training logs from Spark UI as shown in the animated Fig 1. below.

https://www.youtube.com/watch?v=tlbK4ODANZU

Or you can just as easily trace the error back to a notebook cell and code as shown in animated Fig 2. here.

https://www.youtube.com/watch?v=3uQPrfMKEog

Tools like [TensorBoard](https://www.tensorflow.org/tensorboard) and [Horovod Timeline](https://horovod.readthedocs.io/en/latest/timeline.html) are also supported within Databricks.

## Get started!

To get started, check out [example notebooks](https://docs.databricks.com/applications/machine-learning/train-model/distributed-training/horovod-runner.html#examples) to classify MNIST dataset using TensorFlow, Keras, or PyTorch in Databricks Runtime 5.0 ML! To migrate your single node workloads to a distributed setting, you can simply follow the steps outlined in this documentation.

Try [Databricks today](https://www.databricks.com/try-databricks) with Apache Spark 2.4 and Databricks Runtime 5.0.

## Read More

- Learn about[Barrier Execution in Apache Spark 2.4](https://www.databricks.com/blog/2018/11/08/introducing-apache-spark-2-4.html)
- Read about [HorovodRunner Documentation](https://docs.databricks.com/applications/machine-learning/train-model/distributed-training/index.html)
- Listen to the [Project Hydrogen: State of the Art Deep Learning on Apache Spark](https://www.datasciencecentral.com/dsc-webinar-series-state-of-the-art-deep-learning-on-apache-spark/) webinar
- Find out more about [Databricks Runtime 5.0 ML](https://docs.databricks.com/release-notes/runtime/5.0ml.html)

Get more info on [Horovod](https://github.com/horovod/horovod) and [HorovodEstimator](https://docs.databricks.com/applications/machine-learning/train-model/distributed-training/horovod-estimator.html)
