# Introducing MLflow Run Sidebar in Databricks Notebooks

- Source: https://www.databricks.com/blog/2019/04/30/introducing-mlflow-run-sidebar-in-databricks-notebooks.html
- Published: 2019-04-30
- Authors: Andrew Chen, Matei Zaharia
- Categories: platform, announcements, engineering, data-science-machine-learning, company
- Images: 1 total, 0 extracted as architecture

At Spark+AI Summit 2019, we [announced the GA of Managed MLflow on Databricks](https://www.databricks.com/blog/2019/04/25/announcing-general-availability-of-managed-mlflow-on-databricks.html) in which we take the latest and greatest of open source MLflow and make it easily accessible to all users of Databricks. In that blog post, we promised to build features which bridge Databricks and MLflow concepts to create a seamless integration between the two.

Today, we’re excited to announce the MLflow notebook sidebar which is the first of these integrations.

Tracking experiments and producing reproducible machine learning code inside a notebook is hard. We love the notebook interface because it provides for quick iteration cycles between writing code and seeing results. However, these benefits also make it difficult for us to keep track of all of the notebook revisions. Often we ask the question: was it untitled.ipynb or untitled(1).ipynb which created this training run with x% validation accuracy?

*Was it UNTITLED which created the best model or UNTITLED(1)? This meme has been adapted from Joel Grus’ JupyterCon talk: [I don’t like notebooks](https://www.youtube.com/watch?v=7jiPeIFXb6U).*

 

Traditional version management tools like Git aren’t really designed for this use case either. Creating a Git branch for each and every training run you create is only marginally better than making copies of the notebook since you still have to keep track of the performance of each branch.

With the MLflow Runs Sidebar feature, we attempt to bridge the gap between the quick iteration cycles of notebooks and the difficulties of keeping track of code revisions. With MLflow’s easy to use tracking APIs, a user can already keep track of the hyperparameters and the output metrics of each training run. In Managed MLflow on Databricks, we also will automatically take a snapshot of the notebook revision which created the training run and store it as part of the run metadata.

Using this data, we’ve created a notebook sidebar that displays all of the experiment runs you’ve logged from this notebook. With this sidebar, users can quickly browse through their training runs and view the exact version of the notebook that created each one, the way it looked at that point in time. Of course, if you find a notebook revision you want to restore, we also allow you to save it as a new notebook in your Databricks workspace.

https://www.youtube.com/watch?v=v-dkc2DvSw4

In addition, all of the data shown on the MLflow Runs Sidebar is also displayed in the full MLflow UI we all know and love.

https://www.youtube.com/watch?v=s4OPfXjFUE8

## Next Steps

The MLflow Runs Sidebar is just the start -- we plan to extend Databricks Managed MLflow with more integrations and even simpler workflows as we develop the service. We think that what we have so far is already useful for many teams, however, we would love to hear your feedback.

If you're an existing Databricks user, you can start using Managed MLflow by importing the **Quick Start Notebook** for [Azure Databricks](https://docs.microsoft.com/en-us/azure/databricks/applications/mlflow/quick-start) or [AWS](https://docs.databricks.com/applications/mlflow/quick-start.html). If you're not yet a Databricks user, visit [databricks.com/product/managed-mlflow](https://www.databricks.com/product/managed-mlflow) to start a free trial of Databricks and Managed MLflow.
