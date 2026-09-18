# Quickly Deploy, Test, and Manage ML Models as REST Endpoints with MLflow Model Serving on Databricks

- Source: https://www.databricks.com/blog/2020/11/02/quickly-deploy-test-and-manage-ml-models-as-rest-endpoints-with-mlflow-model-serving-on-databricks.html
- Published: 2020-11-02
- Authors: Aaron Davidson, Tomas Nykodym, Clemens Mewald
- Categories: data-science-machine-learning, engineering
- Images: 2 total, 0 extracted as architecture

> MLflow Model Registry now provides turnkey model serving for dashboarding and real-time inference, including code snippets for tests, controls, and automation.

MLflow Model Serving on Databricks provides a turnkey solution to host machine learning (ML) models as REST endpoints that are updated automatically, enabling data teams to own the end-to-end lifecycle of a real-time machine learning model from training to production.

Since [its launch](https://www.databricks.com/blog/2020/06/25/announcing-mlflow-model-serving-on-databricks.html), Model Serving has enabled many Databricks customers to seamlessly deliver their ML models as REST endpoints without having to manage additional infrastructure or configure integrations. To simplify Model Serving even more, the MLflow Model Registry now shows the serving status of each model and deep links into the Model Serving page.

To simplify the consumption of MLflow Models even more, the Model Serving page now provides curl and Python snippets to make requests to the model. Requests can be made either to the latest version at a deployment stage, e.g. model/clemens-windfarm-signature/Production or to a specific version number, e.g. model/clemens-windfarm-signature/2

Databricks customers have utilized Model Serving for several use cases including making model predictions in Dashboards or serving forecasts for finance teams. Freeport McMoRan is serving TensorFlow models to simulate operations for their plants:

> “We simulate different scenarios for our plants and operators need to review recommendations in real-time to make decisions, optimizing plant operations and saving cost. Databricks MLflow Model Serving enables us to seamlessly deliver low latency machine learning insights to our operators while maintaining a consolidated view of end to end model lifecycle.”

Model Serving on Databricks is now in public preview and provides cost-effective, one-click deployment of models for real-time inference, tightly integrated with the MLflow Model Registry for ease of management. See our documentation for how to get started [[AWS](https://docs.databricks.com/applications/mlflow/model-serving.html), [Azure](https://docs.microsoft.com/en-us/azure/databricks/applications/mlflow/model-serving)]. While this service is in preview, we recommend its use for low throughput and non-critical applications.
