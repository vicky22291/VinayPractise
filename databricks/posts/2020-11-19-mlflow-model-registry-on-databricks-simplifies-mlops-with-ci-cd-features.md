# MLflow Model Registry on Databricks Simplifies MLOps With CI/CD Features

- Source: https://www.databricks.com/blog/2020/11/19/mlflow-model-registry-on-databricks-simplifies-mlops-with-ci-cd-features.html
- Published: 2020-11-19
- Authors: Sue Ann Hong, Ankit Mathur, Jules Damji, Mani Parkhe
- Categories: engineering, data-science-machine-learning
- Images: 0 total, 0 extracted as architecture

[MLflow](https://www.databricks.com/product/managed-mlflow) helps organizations manage the ML lifecycle through the ability to track experiment metrics, parameters, and artifacts, as well as deploy models to batch or real-time serving systems. The [MLflow Model Registry](https://www.databricks.com/product/mlflow-model-registry) provides a central repository to manage the model deployment lifecycle, acting as the hub between experimentation and deployment.

A critical part of [MLOps](https://www.databricks.com/glossary/mlops), or ML lifecycle management, is continuous integration and deployment (CI/CD). In this post, we introduce new features in the Model Registry on Databricks [[AWS](https://docs.databricks.com/applications/mlflow/model-registry.html)] [[Azure](https://docs.microsoft.com/en-us/azure/databricks/applications/mlflow/model-registry)] to facilitate the CI/CD process, including tags and comments which are now enabled for all customers, and the upcoming webhooks feature currently in private preview.

Today at the Data + AI Summit, we announced the general availability of Managed MLflow Model Registry on Databricks, and showcased the new features in this post. You can read more about the enterprise features of the managed solution in our [previous post on MLflow Model Registry on Databricks](https://www.databricks.com/blog/2020/04/15/databricks-extends-mlflow-model-registry-with-enterprise-features.html).

## Annotating Models and Model Versions with Tags

Registered models and model versions support key-value pair tags, which can encode a wide variety of information. For example, a user may mark a model with the deployment mode (e.g., batch or real-time), and a deployment pipeline could add tags indicating in which regions a model is deployed. And with the newly added ability to search and query by tags, it’s now easy to filter by these attributes so you can identify the models that are important to your task.

Tags can be added, edited, and removed from the model and model version pages, as well as through the [MLflow API](https://www.mlflow.org/docs/latest/python_api/mlflow.tracking.html#mlflow.tracking.MlflowClient.set_model_version_tag).

## Adding Comments to Model Versions

With the latest release of the Model Registry, your teams now have the ability to write free-form comments about model versions. Deployment processes often trigger in-depth discussions among ML engineers: whether to productionize a model, examine any cause of failures, ascertain model accuracies, reevaluate metrics, parameters, schemas, etc. Through comments, you can capture these discussions during a model’s deployment process, in a central location.

Moreover, as organizations look to automate their deployment processes, information about a deployed model can be spread out across various platforms. With comments, external CI/CD pipelines can post information like test results, error messages, and other notifications directly back into the model registry. Also, in conjunction with webhooks, you can set up your CI/CD pipelines to be triggered by specific comments.

Comments can be created and modified from the UI or from a REST API interface, which will be published shortly.

## Notifications via Webhooks

Webhooks are a common mechanism to invoke an action via a HTTP request upon an occurrence of an event. Model registry wehbooks facilitate the CI/CD process by providing a push mechanism to run a test or deployment pipeline and send notifications through the platform of your choice. Model registry webhooks can be triggered upon events such as creation of new model versions, addition of new comments, and transition of model version stages.

For example, organizations can use webhooks to automatically run tests when a new model version is created and report back results. When a user creates a transition request to move the model to production, a webhook tied to a messaging service like [Slack](https://api.slack.com/messaging/webhooks) could automatically notify members of the MLOps team. After the transition is approved, another webhook could automatically trigger deployment pipelines.

The feature is currently in private preview. Look for an in-depth guide to using webhooks as a central piece to CI/CD integration coming soon.

## Monitoring Events via Audit Logs

An important part of MLOps is the ability to monitor and audit issues in production. Audit logs (or diagnostic logs) on Databricks [[AWS](https://docs.databricks.com/administration-guide/account-settings/audit-logs.html)] [[Azure](https://docs.microsoft.com/en-us/azure/databricks/administration-guide/account-settings/azure-diagnostic-logs)] provide administrators a centralized way to understand and govern activities on the platform. If your workspace has audit logging enabled, model registry events, including those around comments and webhooks [[AWS](https://docs.databricks.com/administration-guide/account-settings/audit-logs.html#audit-events)] [[Azure](https://docs.microsoft.com/en-us/azure/databricks/administration-guide/account-settings/azure-diagnostic-logs#events)], will be logged automatically.

## Get Started with the Model Registry

To see the features in action, you can watch today’s keynote: Taking Machine Learning to Production with New Features in MLflow.

You can read more about MLflow Model Registry and how to use it on [AWS](https://docs.databricks.com/applications/mlflow/model-registry.html?_ga=2.96821599.1748635358.1605115932-1875528958.1586990484) or [Azure](https://docs.microsoft.com/en-us/azure/databricks/applications/mlflow/model-registry). Or you can try an example notebook [[AWS](https://docs.databricks.com/_static/notebooks/mlflow/mlflow-model-registry-example.html?_ga=2.96821599.1748635358.1605115932-1875528958.1586990484)] [[Azure](https://docs.microsoft.com/en-us/azure/databricks/_static/notebooks/mlflow/mlflow-model-registry-example.html)].

If you are new to MLflow, read the open source [MLflow quickstart](https://docs.databricks.com/applications/mlflow/quick-start.html). For production use cases, read about [Managed MLflow on Databricks](https://www.databricks.com/product/managed-mlflow) and get started on using the MLflow Model Registry.
