# Scalable End-to-End Deep Learning using TensorFlow™ and Databricks: On-Demand Webinar and FAQ Now Available!

- Source: https://www.databricks.com/blog/2018/07/13/scalable-end-to-end-deep-learning-using-tensorflow-and-databricks-on-demand-webinar-and-faq-now-available.html
- Published: 2018-07-13
- Authors: Brooke Wenig, Siddharth Murching
- Categories: platform, solutions, product, engineering, open-source, data-science-machine-learning
- Images: 1 total, 0 extracted as architecture

On July 9th, our team hosted a live webinar—*[Scalable End-to-End Deep Learning using TensorFlow™ and Databricks](https://pages.databricks.com/Reg-DeepLearning-TensorFlow.html)*—with Brooke Wenig, Data Science Solutions Consultant at Databricks and Sid Murching, Software Engineer at Databricks.

In this webinar, we walked you through how to use TensorFlow™ and Horovod (an open-source library from Uber to simplify distributed model training) on the [Databricks Unified Analytics Platform](https://www.databricks.com/product/data-lakehouse) to build a more effective recommendation system at scale.

In particular, we covered some of the newly introduced capabilities to simplify distributed deep learning:

- The [new Databricks Runtime for ML](https://www.databricks.com/blog/2018/06/05/announcing-databricks-runtime-for-machine-learning.html), shipped with pre-installed libraries such as Keras, Tensorflow, Horovod, and XGBoost to enable data scientists to get started with distributed Machine Learning more quickly
- The newly-released [Databricks HorovodEstimator API](https://docs.databricks.com/applications/machine-learning/train-model/distributed-training/horovod-estimator.html#horovodestimator-distributed-deep-learning-with-horovod-and-spark) for distributed, multi-GPU training of deep learning models against data in Apache Spark™
- How to make predictions at scale with deep learning pipelines

 

If you missed the webinar, you can [view](https://pages.databricks.com/Reg-DeepLearning-TensorFlow.html) it now. Also, we demonstrated the following notebook:

- *[Scalable Movie Recommendations with Horovod Demo Notebook](https://databricks-prod-cloudfront.cloud.databricks.com/public/13fe59d17777de29f8a2ffdf85f52925/5638528096339357/5040085/5645744322526873/latest.html)*

If you’d like free access [Databricks Unified Analytics Platform](https://www.databricks.com/product/data-lakehouse) and try our notebooks on it, you can access a [free trial here](https://www.databricks.com/try-databricks).

 

Toward the end, we held a Q&A, and below are all the questions and their answers. You can also provide us with your feedback on this webinar by filling-out this [short survey](https://www.surveymonkey.com/r/YCRGVGW), so that we can continue to improve your experience!

 

**Q: Can you perform hyper-parameter tuning of the model in TensorFlow in a distributed fashion?**

There are a number of ways you could do this including but not limited to:

- Train multiple single-node models in parallel on your cluster (i.e. one model per machine), or
- launch multiple distributed training jobs and do a grid search across those distributed training jobs.

In terms of what the [HorovodEstimator](https://docs.databricks.com/applications/machine-learning/train-model/distributed-training/horovod-estimator.html) supports, we are exploring adding functionality for it to work with MLlib’s native tuning APIs so that you can kick-off hyper parameter tuning through multiple distributed training jobs.

Alternatively, Deep Learning Pipeline (an OSS library from Databricks) allows for parallelized hyperparameter tuning of single-node Keras models on image data.

 

**Q: What does ALS stand for?**

ALS stands for Alternating Least Squares. It's a technique used for Collaborative Filtering. You can learn more about its implementation in Apache Spark here.

 

****Q: **In your demo how many servers did you use? how many cores?**

Here is our config for this demo:

- Databricks Runtime Version: 4.1 ML Beta
- Python Version: 3
- i3.x large (1 Driver + 2 Workers)

 

****Q: **Was the data replicated on each local machine? Does each worker node use all the data while training?**

A unique subset of the training data is copied to the local disk of each machine, so each worker node trains on a unique subset of the data. During a single training step, each worker processes a batch of training data, computing gradients that are then averaged using Horovod’s ring-allreduce functionality and applied to the model.

 

****Q: **How do you compare dist-keras and Horovod?**

Dist-keras is another open source framework for training a [Keras model](https://www.databricks.com/glossary/keras-model) in a distributed manner on a Spark Dataframe, and is another great solution for training Keras models. We worked with both. One of the thing we liked about Horovod is that it comes with benchmarks from Uber, and it's used in production by Uber. For that reason we decided to build the [HorovodEstimator](https://docs.databricks.com/applications/machine-learning/train-model/distributed-training/horovod-estimator.html) around Horovod, due to the fact that it's used by large industry company, and will be well supported moving forward.

 

****Q: **How long does single machine training take vs. distributed training?**

This is a good question - in general there are many factors that influence performance when comparing single-machine and distributed training. Distributed training incurs communication overhead from communicating gradient updates, but also allows for speedups by processing batches of training data in parallel across machines. With [HorovodEstimator](https://docs.databricks.com/applications/machine-learning/train-model/distributed-training/horovod-estimator.html) there’s also a fixed startup cost of writing the input Spark DataFrame in TFRecord format on the local disks of our cluster nodes. Our recommendation is to try single machine training first and explore distributed training only if single-machine training does not scale sufficiently.

 

****Q: **Hey, thanks for the talk. That was a great notebook scenario, but in a team of multiple data scientists working on different experiments on little different datasets, do you have functionality to track that? What other collaborative features do you support?**

This is a great question! We recently announced a new open source project called [MLflow](http://www.mlflow.org) just for that. With MLflow, practitioners can package and reuse models across frameworks, track and share experiments locally or in the cloud, and deploy models virtually anywhere. In addition, Databricks provides shared notebooks for Python or R development that also support track changes and versions history with GitHub.

Read Matei Zaharia's blog post on the [MLflow 0.2 release](https://www.databricks.com/blog/2018/07/03/mlflow-0-2-released.html) for the latest update on this initiative, and join our [upcoming webinar](https://pages.databricks.com/Reg-Introducing-MLflow.html) on August 30 with Matei Zaharia to learn more.

 

****Q: **I don’t have much data and I’m using LSTM model and TensorFlow. Will you still recommend me Databricks and Apache Spark ?**

Apache Spark is great for any type of distributed training or ETL, it unifies data processing with machine learning, but still needs effort to be installed, configured, and maintained. Databricks gives you a flexible way to run jobs from single node to multiple nodes use cases on Apache Spark. You can easily add more nodes to your clusters, with a click of a button. Databricks unifies all analytics in one place so that you can also prepare clean data sets for training your models. Databricks Runtime comes with TensorFlow pre-installed and configured, along with Keras, Horovod, but also XGBoost, scikit-learn, etc... giving you maximum choice and flexibility to build and train ML models. Last but not least, Databricks notebooks provide a collaborative environment to manage the entire lifecycle in one place, from data prep, to model training and serving.

 

****Q: **Can you train binary model with HorovodEstimator?**

Yes. [HorovodEstimator API](https://docs.databricks.com/applications/machine-learning/train-model/distributed-training/horovod-estimator.html) simply provides a way to run any TensorFlow code in a distributed setting against large scale data, including binary classification, for example.

 

****Q: **Does the cluster support multi-tenancy?**

Yes, you can have multiple notebooks attached to your cluster, or multiple users on your cluster. You can also manage [cluster permissions](https://docs.microsoft.com/en-us/azure/databricks/administration-guide/access-control/cluster-acl#types-of-permissions) at various levels on Databricks for maximum flexibility and security.

 

****Q: C**ould we share the scripts and slides of the presenters after webinar?**

Yes, you can now access the [notebook](https://databricks-prod-cloudfront.cloud.databricks.com/public/13fe59d17777de29f8a2ffdf85f52925/5638528096339357/5040085/5645744322526873/latest.html). You'll just need to add the training set to your Databricks Workspace to run this notebook. Sign-up for a [free 14-day trial](https://www.databricks.com/try-databricks) to get started!

 

**Q: What is the difference between Apache Spark and Databricks?**

[Databricks Unified Analytics Platform](https://www.databricks.com/product/data-lakehouse) provides a hosted version of Apache Spark both on AWS and Azure, and much more. We provide built-in notebooks and APIs to manage and automate analytics in one place, as well as additional optimizations to Apache Spark, including [Databricks Delta Lake](https://www.databricks.com/product/delta-lake-on-databricks) that is up to 100x faster than Apache Spark on Parquet, [Databricks Runtime for ML](https://www.databricks.com/blog/2018/06/05/announcing-databricks-runtime-for-machine-learning.html), and the [HorovodEstimator](https://docs.databricks.com/applications/machine-learning/train-model/distributed-training/horovod-estimator.html). We also significantly simplify DevOps with auto-config and auto-scaling of clusters, and provide enterprise-grade security features and compliance with a HIPAA and SOC 2 type 2 certified platform.
