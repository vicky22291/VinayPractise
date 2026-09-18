# Managed MLflow Now Available on Databricks Community Edition

- Source: https://www.databricks.com/blog/2019/10/17/managed-mlflow-now-available-on-databricks-community-edition.html
- Published: 2019-10-17
- Authors: Jules Damji, Siddharth Murching
- Categories: engineering, data-science-machine-learning
- Images: 3 total, 0 extracted as architecture

*Free Edition has replaced Community Edition, offering enhanced features at no cost. Start using *[*Free Edition *](https://login.databricks.com/?intent=SIGN_UP&amp;signup_experience_step=EXPRESS&amp;provider=DB_FREE_TIER&amp;dbx_source=www)*today.*
 

In February 2016, we introduced [Databricks Community Edition](https://www.databricks.com/blog/2016/02/17/introducing-databricks-community-edition-apache-spark-for-all.html), a Community Edition for big data developers to learn and get started quickly with [Apache Spark](https://spark.apache.org/). Since then our commitment to foster a community of developers remains steadfast: to date, we have over 150K registered Community Edition users; we have trained thousands of people at meetups and Spark + AI Summits, and other open-source events.

Today, we are excited to extend Databricks Community Edition with hosted [MLflow](https://www.databricks.com/blog/2019/03/06/managed-mlflow-on-databricks-now-in-public-preview.html) for free, as part of our ongoing commitment to help developers learn about machine learning lifecycle. With the Community Edition, you can try tutorials that demonstrate how to track results and experiments as you build machine learning models—a crucial stage in the machine learning model’s development lifecycle.

[MLflow](https://mlflow.org/) is an open-source platform for the machine learning lifecycle with four components: [MLflow Tracking](https://mlflow.org/docs/latest/tracking.html), [MLflow Projects](https://mlflow.org/docs/latest/projects.html), [MLflow Models](https://mlflow.org/docs/latest/models.html), and [MLflow Registry](https://mlflow.org/docs/latest/registry.html#registry). MLflow is now included in Databricks Community Edition, meaning that you can utilize its Tracking and Model APIs within a notebook or from your laptop just as easily as you would with managed MLflow in Databricks Enterprise Edition.

In this blog, we briefly explain how you can use MLflow in Community Edition. We’ll share an example notebook that trains a Keras/TensorFlow model and run it within Databricks Community Edition, followed by how to run [GitHub examples](https://github.com/mlflow/mlflow/tree/master/examples) on your laptop and log results remotely on [Databricks Community Edition](https://www.databricks.com/try-databricks).

## Run Experiments within Community Edition Workspace

First, register for [Community Edition](https://www.databricks.com/try-databricks). Then, create a cluster with **ML Runtime 6.0**, which ships with a pre-configured ML environment including mlflow, Keras, PyTorch, TensorFlow, and other libraries. With any other Runtime, you'll have to [install the mlflow library](https://docs.databricks.com/libraries/index.html#workspace-libraries) or run [`dbutils.library.installPyPI(“mlflow”)`](https://docs.databricks.com/dev-tools/databricks-utils.html#library-utilities) in one of the first cells of your notebook.

### Creating an Experiment in your Workspace

When in a notebook, MLflow will automatically log results to an [experiment associated with the notebook](https://docs.databricks.com/applications/mlflow/tracking.html#notebook-experiments). You can also explicitly create an experiment under which all your model training runs and results are tracked, as shown below:

### Logging Runs in your Default Notebook Experiment

While running your MLflow code within a notebook, the runs will be logged to a default experiment associated with the notebook. Alternatively, you can explicitly set an experiment name with `mflow.set_experiment(“path_to_experiment_name”)`, to aggregate and compare runs across multiple notebooks.

Under this workspace and default experiment name, we will train a Keras MNIST model with various regularization parameters—such as the number of epochs, hidden layers, units per layer, batch size, momentum, dropout, and activation function. We can run a few experiments with different regularization parameters and select the best model with the lowest validation loss and highest accuracy.

#### Creating an MLflow Session with the Tracking Server

By using the `mlflow.start_run(run_name=run_name)`, we automatically initiate a session with the tracking server, while the `mlflow.keras.autolog()` will pick up this current active run session and automatically log parameters, metrics, tags, and model. Below is an excerpt of the code from the [notebook](https://databricks-prod-cloudfront.cloud.databricks.com/public/4027ec902e239c93eaaa8714f173bcfc/8599738367597028/3770668600436233/3601578643761083/latest.html), which you can [import](https://docs.databricks.com/notebooks/notebooks-manage.html#import-a-notebook) into Community Edition.

As you can see from the above, the tracking experiment runs within a Community Edition is relatively simple. With a few lines of code, you can use the [MLflow Tracking and Model APIs](https://www.mlflow.org/docs/latest/tracking.html) to generate runs in your notebook and visualize their parameters and metrics for evaluation.

This step is an important stage in your model development life cycle.

## Run Experiments Locally and Track Results on Community Edition

You can also run experiments on your laptop or local machine, [tracking results to the Community Edition](https://mlflow.org/docs/latest/quickstart.html#log-to-databricks-community-edition). Only after configuring your local environment and registering for a Community Edition can you track results remotely.

### Configuring your Local Environment

1. `pip install mlflow`(as described in the [MLflow quickstart guide](https://mlflow.org/docs/latest/quickstart.html))
2. As above, create an experiment in your workspace and get its path.
3. Create a credentials file via `databricks configure` CLI (and answer the prompts)
  - **Databricks Host (should begin with https://)**: *https://community.cloud.databricks.com*
  - **Username:** *enter your login credentials*
  - **Password:** *enter password for Community Edition*
4. Configure MLflow to communicate with the Community Edition server: `export MLFLOW_TRACKING_URI=databricks`
5. Test out your configuration by creating an experiment via the CLI: `mlflow experiments create -n /Users//my-experiment`

After the above steps, you can run any Python, Java, or R script containing your machine learning and MLflow code locally and track the results on the MLflow Tracking Server hosted on Community Edition. In addition to the above steps, set the `MLFLOW_EXPERIMENT_NAME` environment variable to the experiment created above, or in Python:

For this experimental run, we are going to add the above lines to the [examples/sklearn_elasticnet_diabetes/osx/train_diabetes.py](https://github.com/mlflow/mlflow/blob/master/examples/sklearn_elasticnet_diabetes/osx/train_diabetes.py) from the MLflow GitHub Repository in our cloned repo.

Let’s execute three separate runs, each with different parameters on our laptop. With each run, the results will be logged on our Community Edition server under the experiment created above.

`python train_diabetes.py 0.01 0.01 && python train_diabetes.py 0.01 0.75 && python train_diabetes.py 0.01 1.0`

As shown in the animation above, when the code is executed locally, the runs’ results are logged remotely on the MLflow Tracking Server hosted on your Community Edition.

Or you could simply cut-and-paste this simple code into your favorite editor and run from your laptop, after configuring the laptop with Databricks MLflow credentials:

## Summary

To recap, MLflow is now available on Databricks Community Edition. As an important step in machine learning model development stage, we shared two ways to run your machine learning experiments using [MLflow APIs](https://www.mlflow.org/docs/latest/python_api/mlflow.html): one is by running in a notebook within Community Edition; the other is by running scripts locally on your laptop and logging results to the tracking server hosted on Community Edition.

Intended for rapid experimentation and learning, the MLflow server on Community Edition is not designed for production use. For example, it does not include the ability to [run and reproduce MLflow Projects](https://mlflow.org/docs/latest/projects.html#databricks-execution). And its scalability and uptime guarantees are limited.

Since its original release in February 2016, Community Edition has proved a useful tool for learning about Apache Spark, data science, and data engineering. We’re happy to extend it to learn about managing the machine learning lifecycle with MLflow.

## What’s Next

To get started, try some [examples from the MLflow GitHub repository](https://github.com/mlflow/mlflow/tree/master/examples) on your laptop. These Python scripts ([quickstart/mlflow_tracking.py](https://github.com/mlflow/mlflow/blob/master/examples/quickstart/mlflow_tracking.py) and [sklearn_elasticnet_wine/train.py](https://github.com/mlflow/mlflow/blob/master/examples/sklearn_elasticnet_wine/train.py)) are a good start to train models locally on your laptop and track remotely on the Community Edition. Or [import and run this notebook](https://databricks-prod-cloudfront.cloud.databricks.com/public/4027ec902e239c93eaaa8714f173bcfc/8599738367597028/3770668600436233/3601578643761083/latest.html) in your Community Edition.

Join the MLflow [community](https://mlflow.org/#community) and download the latest [MLflow 1.3](https://mlflow.org/news/2019/09/30/1.3.0-release/index.html). Finally, after using MLflow, feel free to [contribute](https://github.com/mlflow/mlflow).

## Read More

If you are new to MLflow, read the [MLflow quickstart](https://mlflow.org/docs/latest/quickstart.html). For production use cases, read about [Managed MLflow on Databricks](https://www.databricks.com/product/managed-mlflow).
