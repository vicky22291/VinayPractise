# What's new with MLflow? On-Demand Webinar and FAQs now available!

- Source: https://www.databricks.com/blog/2019/06/26/whats-new-with-mlflow-on-demand-webinar-and-faqs-now-available.html
- Published: 2019-06-26
- Authors: Clemens Mewald
- Categories: engineering, data-science-machine-learning
- Images: 1 total, 0 extracted as architecture

On June 6th, our team hosted a live webinar—[Managing the Complete Machine Learning Lifecycle: What's new with MLflow](https://pages.databricks.com/201906-US-WB-New-with-MLflow_Reg.html)—with Clemens Mewald, Director of Product Management at Databricks.

Machine learning development brings many new complexities beyond the traditional software development lifecycle. Unlike in traditional software development, ML developers want to try multiple algorithms, tools and parameters to get the best results, and they need to track this information to reproduce work. In addition, developers need to use many distinct systems to productionize models.

To solve for these challenges, last June, we unveiled MLflow, an open source platform to manage the complete machine learning lifecycle. Most recently, we announced the [General Availability of Managed MLflow on Databricks](https://www.databricks.com/blog/2019/04/25/announcing-general-availability-of-managed-mlflow-on-databricks.html) and the [MLflow 1.0 Release](https://www.databricks.com/blog/2019/06/06/announcing-the-mlflow-1-0-release.html).

In this webinar, we reviewed new and existing MLflow capabilities that allow you to:

- Keep track of experiments runs and results across frameworks.
- Execute projects remotely on to a Databricks cluster, and quickly reproduce your runs.
- Quickly productionize models using Databricks production jobs, Docker containers, Azure ML, or Amazon SageMaker

We demonstrated these concepts using [notebooks and tutorials](https://docs.databricks.com/applications/mlflow/index.html) from our public documentation so that you can practice at your own pace. If you’d like free access [Databricks Unified Analytics Platform](https://www.databricks.com/product/data-lakehouse) and try our notebooks on it, you can access a [free trial here](https://www.databricks.com/try-databricks).

Toward the end, we held a Q&A and below are the questions and answers.

**Q: Apart from having the trouble of all the set-up, is there any missing features/disadvantages of using MLflow on-premises rather than in the cloud on Databricks?**

Databricks is very committed to the open source community. Our founders are the original creators of Apache SparkTM - a widely adopted open source unified analytics engine - and our company still actively maintains and contributes to the open source Spark code. Similarly, for both [Delta Lake](https://www.delta.io) and [MLflow](https://www.mlflow.org), we're equally committed to help the open source community benefit from these products, as well as provide an out-of-the-box managed version of these products.

When we think about features to provide on the open source or the managed version of Delta Lake or MLflow, we don't think about whether we should hold back a feature on a version or another. We think about what additional features we can provide that only make sense in a hosted and managed version for enterprise users. Therefore, all the benefits you get from managed MLflow on Databricks are that you don't need to worry about the setup, managing the servers, and all these integrations with the Databricks Unified Analytics Platform that makes it seamlessly work with the rest of the workflow. Visit [https://www.databricks.com/product/managed-mlflow](https://www.databricks.com/product/managed-mlflow) to learn more.

**Q: Does MLflow 1.0 supports Windows?**

Yes, we added support to run the MLflow client on windows. Please see our release notes [here](https://github.com/mlflow/mlflow/releases/tag/1.0.0).

**Q: Is MLflow complements or competes with TensorFlow?**

It’s a perfect complement. You can train TensorFlow models and log the metrics and models with MLflow.

**Q: How many different metrics can we track using MLflow? Are there any restrictions imposed on it?**

MLflow doesn’t impose any limits on the number of metrics you can track. The only limitations are in the backend that is used to store those metrics.

**Q: How to parallelize models training with MLflow?**

MLflow is agnostic to the ML framework you use to train the model. If you use TensorFlow or PyTorch you can distribute your training jobs with for example [HorovodRunner](https://docs.databricks.com/applications/machine-learning/train-model/distributed-training/horovod-runner.html#horovodrunner-distributed-deep-learning-with-horovod) and use MLflow to log your experiments, runs, and models.

**Q: Is there a way to bulk extract the MLflow info to perform operational analytics (e.g. how many training runs were there in the last quarter. How many people are training models etc.)?**

We are working on a way to more easily extract the MLflow tracking metadata into a format that you can do data science with, e.g. into a [pandas dataframe](https://www.databricks.com/glossary/pandas-dataframe).

**Q: Is it possible to train and build a MLflow model using a platform (e.g. like Databricks using TensorFlow with PySpark) and then reuse that MLflow model in another platform (for example in R using RStudio) to score any input?**

The MLflow Model format and abstraction allows using any MLflow model from anywhere you can load them. E.g., you can use the python function flavor to call the model from any Python library, or the r function flavor to call it as an R function. MLflow doesn’t rewrite the models into a new format, but you can always expose an MLflow model as a REST endpoint and then call it in a language agnostic way.

**Q: To serve a model, what are the options to deploy outside of databricks, eg. Sagemaker. Do you have any plans to deploy as AWS Lambdas?**

We provide several ways you can deploy MLflow models, including Amazon SageMaker, Microsoft Azure ML, Docker Containers, Spark UDF and more... See [this page](https://www.mlflow.org/docs/latest/models.html#built-in-deployment-tools) for a list. To give one example of how to use MLflow models with AWS Lambda, you can use the python function flavor which enables you to call the model from anywhere you can call a Python function.

**Q: Can MLflow be used with python programs outside of Databricks?**

Yes, MLflow is an open source product and can be found on [GitHub](https://github.com/mlflow/mlflow) and [PyPi](https://pypi.org/project/mlflow/).

**Q: What is the pricing model for Databricks?**

Please see [https://www.databricks.com/product/pricing](https://www.databricks.com/product/pricing)

**Q: How do you see MLflow evolving in relation to Airflow?**

We are looking into ways to support multi-step workflows. One way we could do this is by using Airflow. We haven’t made these decisions yet.

**Q: Suggestions for deploying multi-step models for example ensemble of several base models.**

Right now you can deploy those as MLflow models by writing code to ensemble other models. E.g. similar to how the[multi-step workflow](https://github.com/mlflow/mlflow/tree/master/examples/multistep_workflow) example is implemented.

**Q: Does MLflow provide a framework to do feature engineering on data?**

Not specifically, but you can use any other framework together with MLflow.

*To get started with MLflow, follow the instructions at *[*mlflow.org*](https://www.mlflow.org/)* or check out the release code on *[*Github*](https://github.com/databricks/mlflow)*. We’ve also recently created a *[*Slack channel*](https://mlflow-users.slack.com/join/shared_invite/enQtMzkxMTAwNTcyODM5LTNkNTc5YWZlNDNjMzZiYWJhOTQwMjYwYWE3NDU2YTgzMDViYjJhNWI1MGI4NjViNTA0M2FhMzNhZTVkODE2NmU)* for MLflow as well for real time questions, and you can follow *[*@MLflow*](https://twitter.com/MLflow)* on Twitter. We are excited to hear your feedback!*
