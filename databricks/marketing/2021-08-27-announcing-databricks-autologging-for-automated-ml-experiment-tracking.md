# Announcing Databricks Autologging for Automated ML Experiment Tracking

- Source: https://www.databricks.com/blog/2021/08/27/announcing-databricks-autologging-for-automated-ml-experiment-tracking.html
- Published: 2021-08-27
- Authors: Corey Zumar, Kasey Uhlenhuth
- Categories: engineering, data-science-machine-learning
- Images: 0 total, 0 extracted as architecture

Machine learning teams require the ability to reproduce and explain their results--whether for regulatory, debugging or other purposes. This means every production model must have a record of its lineage and performance characteristics. While some ML practitioners diligently version their source code, hyperparameters and performance metrics, others find it cumbersome or distracting from their rapid prototyping. As a result, data teams encounter three primary challenges when recording this information: (1) standardizing machine learning artifacts tracked across ML teams, (2) ensuring reproducibility and auditability across a diverse set of ML problems and (3) maintaining readable code across many logging calls.

## Ensure reproducibility of ML models

  

*Databricks Autologging automatically tracks model training sessions from a variety of ML frameworks, as demonstrated in this scikit-learn example. Tracked information is displayed in the Experiment Runs sidebar and in the MLflow UI.*

To address these challenges, we are happy to announce [Databricks Autologging](https://docs.databricks.com/applications/mlflow/databricks-autologging.html), a no-code solution that leverages [Managed MLflow](https://www.databricks.com/product/managed-mlflow) to provide automatic experiment tracking for all ML models across an organization. With Databricks Autologging, model parameters, metrics, files and lineage information are captured when users run training code in a notebook – without needing to import MLflow or write lines of logging instrumentation.

Training sessions are recorded as [MLflow Tracking Runs](https://docs.databricks.com/applications/mlflow/tracking.html) for models from a variety of popular ML libraries, including scikit-learn, PySpark MLlib and TensorFlow. Model files are also tracked for seamless registration with the [MLflow Model Registry](https://docs.databricks.com/applications/mlflow/model-registry.html) and deployment for real-time scoring with [MLflow Model Serving](https://docs.databricks.com/applications/mlflow/model-serving.html).

## Use Databricks Autologging

To use Databricks Autologging, simply train a model in a [supported framework](https://docs.databricks.com/applications/mlflow/databricks-autologging.html#supported-environments-and-frameworks)of your choice via an interactive Databricks Python notebook. All relevant model parameters, metrics, files and lineage information are collected automatically and can be viewed on the Experiment page. This makes it easy for data scientists to compare various training runs to guide and influence experimentation. Databricks Autologging also tracks hyperparameter tuning sessions in order to help you define appropriate search spaces with UI visualizations, such as the[MLflow parallel coordinates plot](https://www.youtube.com/watch?v=pBr7jlXjqHs).

You can customize the behavior of Databricks Autologging using API calls. The [mlflow.autolog() API](https://mlflow.org/docs/latest/python_api/mlflow.html#mlflow.autolog) provides configuration parameters to control model logging, collection of input examples from training data, recording of model signature information and more use cases. Finally, you can use the [MLflow Tracking API](https://docs.databricks.com/applications/mlflow/tracking.html) to add supplemental parameters, tags, metrics and other information to model training sessions recorded by Databricks Autologging.

## Manage MLflow runs

All model training information tracked with Autologging is stored in [Managed MLflow](https://www.databricks.com/product/managed-mlflow) on Databricks and secured by [MLflow Experiment permissions](https://docs.databricks.com/security/access-control/workspace-acl.html#mlflow-experiment-permissions-1). You can share, modify or delete model training information using the [MLflow Tracking API](https://docs.databricks.com/applications/mlflow/tracking.html) or UI.

## Next steps

Databricks Autologging will begin rolling out to select Databricks workspaces in Public Preview, beginning with version 9.0 of the [Databricks Machine Learning Runtime](https://www.databricks.com/product/machine-learning-runtime), and will become broadly available over the next several months. To learn more about feature availability, see the [Databricks Autologging documentation](https://docs.databricks.com/applications/mlflow/databricks-autologging.html).
