# MLflow On-Demand Webinar and FAQ Now Available!

- Source: https://www.databricks.com/blog/2018/09/12/mlflow-on-demand-webinar-and-faq-now-available.html
- Published: 2018-09-12
- Authors: Matei Zaharia, Denny Lee
- Categories: product, engineering, data-science-machine-learning, platform, solutions
- Images: 0 total, 0 extracted as architecture

On August 30th, our team hosted a live webinar—[Introducing MLflow: Infrastructure for a complete Machine Learning lifecycle](https://pages.databricks.com/Reg-Introducing-MLflow.html)—with Matei Zaharia, Co-Founder and Chief Technologist at Databricks.

In this webinar, we walked you through [MLflow](https://www.mlflow.org), a new open source project from Databricks that aims to design an open ML platform where organizations can use any ML library and development tool of their choice to reliably build and share ML applications. MLflow introduces simple abstractions to package reproducible projects, track results, and encapsulate models that can be used with many existing tools, accelerating the ML lifecycle for organizations of any size.

In particular, we showed how to:

- Keep track of experiments runs and results across popular frameworks with MLflow Tracking
- Execute a MLflow Project published on GitHub from the command line or Databricks notebook as well as remotely execute your project on to a Databricks cluster
- Quickly deploy MLflow Models on-prem or in the cloud and expose them via REST APIs

If you missed the webinar, you can [view](https://pages.databricks.com/Reg-Introducing-MLflow.html) it now. Also, we demonstrated the following notebook and datasets.

More code samples and tutorials are available on [GitHub](https://github.com/mlflow/mlflow/tree/master/examples), including hyperparameter tuning, as well as model training and tracking on Tensorflow, Pytorch, and scikit-learn.

If you’d like free access [Databricks Unified Analytics Platform](https://www.databricks.com/product/data-lakehouse) and try our notebooks on it, you can access a [free trial here](https://www.databricks.com/try-databricks).

Toward the end, we held a Q&A, and below are the questions and their answers.

 

**General Questions**

**Q: As MLflow is in alpha version, what is the timeline for the first stable version ?**

We care a lot about API stability and making MLflow a library that you can build on for the long term. We want the API to be stable as quickly as possible and are currently targeting first half of 2019 to start guaranteeing stability.

**Q: Do we have to use MLflow modules together or can we use only the tracking module?**

Yes, you can use just one module at a time: [*MLflow Tracking*](https://mlflow.org/docs/latest/tracking.html), [*MLflow Projects*](https://mlflow.org/docs/latest/projects.html), or [*MLflow Models*](https://mlflow.org/docs/latest/models.html). MLflow was designed to be modular to provide maximum flexibility and integrate easily into users’ existing ML development processes.

**Q: Does MLflow work with Azure? Cloudera? Other vendors?**

You can use the open source MLflow software on any platform. Storage works locally or in the cloud on Azure Blob Storage, S3, or Google Cloud Storage and we have a few [docs](https://mlflow.org/docs/latest/index.html) on how to use MLflow with or without Databricks.

**Q: Do you plan for supporting any AutoML, like auto parameter tuning in the future?**

MLflow is easy to integrate with existing hyperparameter tuning tools such as Hyperopt or GPyOpt. You can use these tools to automatically run an MLflow project with different hyperparameters to find the best hyperparameter combination. There’s an [example](https://github.com/mlflow/mlflow/tree/master/examples/hyperparam) included in the MLflow codebase.

**Q: How is MLflow different than H2O AutoML?**

MLflow doesn’t aim to be a pure AutoML solution that automates the whole model development process. Instead, it aims to streamline the ML development process and make existing ML developers (both data scientists and production engineers) more productive by letting them easily track, reproduce and compare results. These features should be useful for going into production and reliably maintaining models even if you use AutoML, and they work with other ML tools as well, not just those supported in AutoML libraries.

**Q: Has there been any thought to integrating something like TransmogrifAI (automated feature engineering) as a part of MLflow?**

Yes, our goal is to easily support using arbitrary ML libraries, including TransmogrifAI. For example, you can log parameters and metrics to TransmorgifAI using MLflow, and then visualize to discover the patterns so you can reconfigure your TransmogrifAI experiments for better performance.

 

**Questions on MLflow Tracking **

*MLflow Tracking allows to record and query experiments: code, data, config, results. In this webinar, we demonstrated how you can track results from a linear regression model using a generic Python function as well as scikit-learn with MLflow. See more examples on *[*Github*](https://github.com/mlflow/mlflow/tree/master/examples)*.*

**Q: Do you have documentation of using a shared MLflow Tracking server in a team setting? Is there any security for the shared tracking server? If I want to know who ran a particular experiment.**

Absolutely, here is our documentation for [MLflow Tracking](https://mlflow.org/docs/latest/tracking.html) as well as the [MLflow Tracking server](https://mlflow.org/docs/latest/tracking.html#running-a-tracking-server) that can be setup for collaboration purposes. In addition, The MLflow Tracking UI lets you see who has been logging runs into the MLflow Tracking Server. The MLflow tracking server just provides a HTTP interface, so we recommend placing it behind a HTTP proxy or a VPN for secure authentication.

**Q: Where are the metrics/parameters recorded? **

MLflow runs can be recorded either locally in files or remotely to a [MLflow tracking server](https://mlflow.org/docs/latest/tracking.html#running-a-tracking-server). It works with Azure Blob Storage, S3, or Google Cloud Storage. More detailed information is available in our [documentation](https://mlflow.org/docs/latest/tracking.html#where-runs-get-recorded).

**Q: How can I run the MLflow UI from Azure Databricks?**

You can use MLflow on Azure Databricks by using open source MLflow like we demonstrated in this webinar. You can refer to our [documentation](https://docs.microsoft.com/en-us/azure/databricks/applications/machine-learning/#mlflow) for more information. In the 0.6 release, MLflow will automatically understand if you're running your experiments in Databricks and will record a link to your notebook or job.

We are also offering a private preview of hosted MLflow on Databricks to customers. You can sign-up at [https://www.databricks.com/product/managed-mlflow](https://www.databricks.com/product/managed-mlflow) for more information.

**Q: Do you have future plans to enable storage on databases as well?**

Yes, we are also planning to include a database storage back-end so that you can plug in common SQL databases. The storage back-end in MLflow is already pluggable so we welcome open source contributions to add this.

**Q: If I am running a Grid search function in a Databricks notebook, can that be tracked directly into MLflow?**

Yes, you can even run multiple experiments in the same cell in a loop. MLflow will record all of the runs whenever you use the API.

 

**Questions on MLflow Projects**

*MLflow Projects allows to package format for reproducible runs on any platform. Learn more *[*here*](https://mlflow.org/docs/latest/projects.html)*.*

**Q: Do Github projects need to have a MLproject file already available to support runs via MLflow?**

We currently advise that you create a MLproject file when executing MLflow against GitHub projects.  While you can also run code in GitHub repositories without one (by just specifying a script in the repository as your entry point), the `MLProject` helps to document the entry points (i.e. how to run the code) and their dependencies.

 

**Questions on MLflow Models**

*MLflow Models provides a general model format that supports diverse deployment tools. Learn more *[*here*](https://mlflow.org/docs/latest/models.html)*.*

**Q: How configurable is the "run in the cloud" function? What if I want to run a job against a CPU-strong VM and then later against a GPU-strong VM?**

MLflow is designed to be agnostic to your environment, so as long as your ML library supports running on different types of hardware, it should be possible to package it up in an MLflow Model and deploy it in these settings. The project comes with built in integrations with popular ML libraries which we intend to tune for good performance.

**Q: Is exporting a Databricks notebook to Azure ML web service available as part of open source MLflow**

Exporting a model to Azure ML is currently supported in MLflow, though we're not exporting a notebook. We're just exporting the model that you built, that function, and yes it is supported today. You can read more about this in our [documentation](https://mlflow.org/docs/latest/models.html#microsoft-azureml).

**Q: Does MLflow supports deploying scikit learn models to Amazon Sagemaker, how does it work?**

The [mlflow.sagemaker](https://mlflow.org/docs/latest/python_api/mlflow.sagemaker.html#module-mlflow.sagemaker) module can deploy python_function models on SageMaker or locally in a Docker container with SageMaker compatible environment.  You have to set up your environment and user accounts first in order to deploy to SageMaker with MLflow. Also, in order to export a custom model to SageMaker, you need a MLflow-compatible Docker image to be available on Amazon ECR. MLflow provides a default Docker image definition; however, it is up to you to build the actual image and upload it to your ECR account. MLflow includes a utility to perform this step. Once built and uploaded, the MLflow container can be used for all MLflow models. For more information, refer to [our documentation](https://mlflow.org/docs/latest/models.html#amazon-sagemaker).

 

*To get started with MLflow, follow the instructions at [mlflow.org](https://www.mlflow.org/) or check out the alpha release code on [Github](https://github.com/databricks/mlflow). We’ve also recently created a [Slack channel](https://mlflow-users.slack.com/join/shared_invite/enQtMzkxMTAwNTcyODM5LTNkNTc5YWZlNDNjMzZiYWJhOTQwMjYwYWE3NDU2YTgzMDViYjJhNWI1MGI4NjViNTA0M2FhMzNhZTVkODE2NmU) for MLflow as well for real time questions, and you can follow [@MLflow](https://twitter.com/MLflow) on Twitter. We are excited to hear your feedback on the concepts and code!*
