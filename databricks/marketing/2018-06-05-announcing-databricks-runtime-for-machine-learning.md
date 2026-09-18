# Announcing Databricks Runtime for Machine Learning

- Source: https://www.databricks.com/blog/2018/06/05/announcing-databricks-runtime-for-machine-learning.html
- Published: 2018-06-05
- Authors: Paul Ogilvie
- Categories: product, announcements, engineering, data-science-machine-learning, company
- Images: 1 total, 0 extracted as architecture

*Databricks is thrilled to announce the Databricks Runtime for Machine Learning, including ready-to-use Machine Learning frameworks, simplified distributed training, and GPU Support. *[*Register*](https://pages.databricks.com/201806-WB-Deep-Learning-on-Spark-and-Databricks_Landing.html)* for our upcoming webinar to learn more.*

Today more than ever, data scientists and Machine Learning practitioners have the opportunity to transform their business by implementing sophisticated models for recommendation engines, ads targeting, speech recognition, object recognition, bots, sentiment analysis, predictive analysis, and more.

However, practitioners face multiple challenges when implementing such applications:

1. **Environment Configuration: **Ability to setup and maintain complex environments due to the multitude of Machine Learning frameworks available.
2. **Distributed Training:** Ability to train models in a distributed fashion to get results faster. This requires specialized skills and complex code to manage.
3. **Compute Power: **Ability to run parallelized workloads on GPUs for maximum performances. This is essential for Deep Learning applications.

In this blog post, we will cover how Databricks can help overcome these challenges.

**Introducing Databricks Runtime for Machine Learning**

**Pre-configured Machine Learning frameworks, including XGBoost, scikit-learn, TensorFlow, Keras, Horovod, and more.**

Based on customer demand, we are excited to announce the new native and deep integration of popular Machine Learning frameworks as a part of the [Databricks Runtime for ML](https://docs.microsoft.com/en-us/azure/databricks/runtime/mlruntime). The new runtime features XGBoost, scikit-learn, and numpy as well as popular Deep Learning frameworks such as TensorFlow, Keras, Horovod, and their dependencies.

The Databricks Runtime for ML is a convenient way to start a Databricks cluster with the many libraries required for distributed Deep Learning training on TensorFlow. Furthermore, it ensures compatibility of the libraries included (e.g. between TensorFlow and CUDA / cuDNN), and substantially decreases the cluster start-up time compared to using init scripts.

When you create a cluster, select a Databricks Runtime ML version from the drop-down.

**Simplified Distributed Training on Horovod, TensorFlow and Apache Spark**

In addition, we are pleased to introduce the HorovodEstimator aiming at simplifying distributed Deep Learning. The Horovod framework - originally introduced by Uber - is a popular framework for distributed training on Tensorflow, Keras, and PyTorch.

[HorovodEstimator](https://docs.microsoft.com/en-us/azure/databricks/applications/machine-learning/train-model/distributed-training/horovod-estimator) is an MLlib-style estimator API that leverages Horovod and facilitates distributed, multi-GPU training of deep neural networks on Spark DataFrames. It dramatically simplifies the integration of ETL in Spark with model training in TensorFlow, streamlining the end-to-end workflow from data ingest to model training.

Download this [notebook](https://docs.databricks.com/_static/notebooks/deep-learning/horovod-estimator.html) to get started today.

**Maximum Compute Power with GPU Support**

All of this would still have limited impact without the ability to run distributing computing on GPU accelerated hardware.

For these demanding workloads, we are also expanding Databricks supported clusters to the Microsoft Azure GPU NC, NCv3, and AWS P3 GPU series. More detailed pricing information is available for [Azure Databricks](https://azure.microsoft.com/en-us/pricing/details/databricks/) as well [Databricks on AWS](https://www.databricks.com/product/aws-pricing/instance-types).

## **Next Steps**

With built-in Machine Learning frameworks and the superior performance of the Databricks Runtime coupled with GPU-based parallel compute capabilities, Databricks Unified Analytics Platform uniquely serves the needs for state-of-the-art Deep Learning use cases that are computationally challenging.

Get started today at [Databricks.com](https://www.databricks.com) and [register](https://pages.databricks.com/201806-WB-Deep-Learning-on-Spark-and-Databricks_Landing.html) for our exclusive webinar, *Scalable End-to-End Deep Learning on Apache Spark** and Databricks*, on June 27th at 10 am PST for a deeper dive and live demos with experts Sue Ann Hong and Siddharth Murching, Software Development Engineers at Databricks.

We look forward to seeing you there!
