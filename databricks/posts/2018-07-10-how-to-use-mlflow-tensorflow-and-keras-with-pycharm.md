# How to Use MLflow, TensorFlow, and Keras with PyCharm

*Simple steps to get started on your favorite Python IDE*

- Source: https://www.databricks.com/blog/2018/07/10/how-to-use-mlflow-tensorflow-and-keras-with-pycharm.html
- Published: 2018-07-10
- Authors: Jules Damji
- Categories: engineering, open-source, data-science-machine-learning
- Images: 6 total, 0 extracted as architecture

*Free Edition has replaced Community Edition, offering enhanced features at no cost. Start using *[*Free Edition *](https://login.databricks.com/?intent=SIGN_UP&amp;signup_experience_step=EXPRESS&amp;provider=DB_FREE_TIER&amp;dbx_source=www)*today.*
 

At [Data + AI Summit](https://www.databricks.com/dataaisummit) in June, we announced [MLflow](https://www.databricks.com/blog/2018/06/05/introducing-mlflow-an-open-source-machine-learning-platform.html), an open-source platform for the complete machine learning cycle. The platform’s philosophy is simple: work with any popular [machine learning library](https://www.databricks.com/glossary/what-is-machine-learning-library); allow machine learning developers to experiment with their models, preserve the training environment, parameters, and dependencies, and reproduce their results; and finally deploy, monitor and serve them seamlessly—all in an open manner with limited constraints.

All that is important. Equally important—no matter the philosophy or design principles—are factors that make the platform easy to use:

- Minimal effort to get started
- Easy and intuitive set of developer APIs that make developers productive
- Vibrant community, voluble documentation, and code examples to learn from.

In this blog, we will focus on one of the factors: Minimal time to get started. In upcoming blogs, we will elaborate on the other factors, albeit we’ll briefly mention them here.

Let’s consider the level of effort it takes to get started using MLflow in your favorite IDE.

## Quick Start, Minimal Effort: Python and PyCharm

Python seems to be the most popular programming language for machine learning. Most common machine learning frameworks such as TensorFlow, [Keras](https://keras.io/), [PyTorch](https://pytorch.org/), and [Apache Spark MLlib](https://spark.apache.org/) provide Python APIs.

As a result, many Python developers elect [PyCharm](https://www.jetbrains.com/pycharm/) as an IDE. Why? For one, it offers a Community Edition. Second, it creates a [Python Virtual Environment](https://docs.python.org/3/tutorial/venv.html) or Conda Environment, without you having to explicitly do it. And third, if you have used IntelliJ, you are set to *flow*—all that counts toward minimal effort to get started.

For you to use MLflow along with your machine learning models developed with [TensorFlow](https://www.databricks.com/glossary/what-is-tensorflow) or Keras APIs, three simple steps will get you ready to *flow*.

1. Download [PyCharm CE](https://www.jetbrains.com/pycharm/) for your laptop (Mac or Linux)
2. Create a project and import your MLflow project sources directory
3. Configure PyCharm environment.

By default [PyCharm](https://www.databricks.com/glossary/what-is-pycharm) creates Python Virtual Environment, but you can configure to create a Conda environment or use an existing one.

This short video details steps 2 and 3 after you have installed PyCharm on your laptop.

## MLflow [Keras Model](https://www.databricks.com/glossary/keras-model)

Our example in the video is a simple Keras network, modified from [Keras Model Examples](https://gist.github.com/candlewill/552fa102352ccce42fd829ae26277d24), that creates a simple multi-layer binary classification model with a couple of hidden and dropout layers and respective activation functions. Binary classification is a common machine learning task applied widely to classify images or text into two classes. For example, an image is a cat or dog; or a tweet is positive or negative in sentiment; and whether mail is spam or not spam.

But the point here is not so much to demonstrate a complex [neural network](https://www.databricks.com/glossary/neural-network) model as to show the ease with which you can develop with Keras and TensorFlow, log an MLflow run, and experiment—all within PyCharm on your laptop.

With default or user-specified tuning parameters as command line arguments, [*keras_nn_model.py*](https://github.com/dmatrix/jsd-mlflow-examples/blob/master/keras/keras_nn_model.py) can be executed, tracked, and experimented with MLflow in two ways: with command line or from PyCharm.

### Command Line: Specify tuning parameters as arguments

`python keras/keras_nn_mode.py --drop_rate=0.3 --epochs=40 --output=64 --train_batch_size=256`

### PyCharm: Specify parameters as arguments in the run configuration

Whether run from the command line or from PyCharm, all parameters and resulting metrics are logged using the *mflow.log_param()* APIs as seen here:

## Visualizing Your Runs in MLflow

You can repeat the experiments in either modes—command line or PyCharm—and view your results within the MLflow ui.

`mlflow ui`

Examining your runs and its respective metrics in the MLflow UI gives you insight into how your model performs with different tuning parameters.

Having examined some runs, what’s next for you? You can do one of two things.
Use this dashboard as a leaderboard to compare other models and their respective runs inside your organization. Or save the model for deployment if satisfied with runs. Read the documentation to learn how to [deploy MLflow models](https://mlflow.org/docs/latest/models.html#built-in-deployment-tools).

## Easy APIs, Documentation, and Code Examples

Earlier in the blog, we noted that three factors that make a platform easier to use. We detailed the first one—easy of use. Next, we want to briefly share our core design philosophy for MLflow that contributes to the two other factors.

First, we designed MLflow with *API-first principle* and *open-source*, with [Python APIs](https://mlflow.org/docs/latest/python_api/index.html), meaning that these APIs are designed to offer developer building blocks to extend and employ MLflow’s three core components: [Tracking](https://mlflow.org/docs/latest/tracking.html#), [Projects](https://mlflow.org/docs/latest/projects.html), and [Models](https://mlflow.org/docs/latest/models.html#model-api). Along with REST APIs and [Command Line Interface](https://mlflow.org/docs/latest/cli.html), these APIs enable developers to carry out complex machine learning lifecycle tasks:

- Experiment and track with parameters and log metrics locally or remotely
- Save models in default storage or custom formats for deployment in many environments (Docker, Azure ML, Databricks, or Apache Spark UDF) and reload wherever you can run Python code
- Package MLFlow projects as self-described and self-contained entities reusable and reproducible by others from GitHub repositories

And second, we have [good documentation](https://mlflow.org/docs/latest/index.html) for you to get started, and we are earnestly building a [community of contributors](https://github.com/databricks/mlflow/graphs/contributors). While existing code examples will get you started, overtime this repository of samples will grow in scope with your contributions. You can start pursuing some MLflow projects at [mlflow-examples](https://github.com/mlflow/mlflow-apps) and examine this blog’s Keras network model [here](https://github.com/dmatrix/jsd-mlflow-examples.git).

So to recap, three factors affect platform’s ease of use: quick developer start time; intuitive APIs with docs and code samples; and emerging community. We touched on all three aspects, and you can help with them too.

## What’s Next

Here are some ways you can learn more about MLflow or even contribute:

1. Join our [Google User Group](mailto:mlflow-users@googlegroups.com), [MLflow Meetup](https://www.meetup.com/Bay-Area-MLflow/?_cookie-check=1Ks94mENLPF3Xn47), and [MLflow Slack channel](https://mlflow-users.slack.com/join/shared_invite/enQtMzkxMTAwNTcyODM5LTNkNTc5YWZlNDNjMzZiYWJhOTQwMjYwYWE3NDU2YTgzMDViYjJhNWI1MGI4NjViNTA0M2FhMzNhZTVkODE2NmU)
2. Contribute on GitHub: [https://github.com/databricks/mlflow](https://github.com/databricks/mlflow)
3. Try MLflow Project Examples: [https://github.com/mlflow/mlflow-apps](https://github.com/mlflow/mlflow-apps)
4. Find out more at [www.mlflow.org](https://www.mlflow.org/)
5. Read our blog: [Introducing MLflow: an Open Source Machine Learning Platform](https://www.databricks.com/blog/2018/06/05/introducing-mlflow-an-open-source-machine-learning-platform.html)
6. Find out what's new in [MLflow v0.2.1](https://www.databricks.com/blog/2018/07/03/mlflow-0-2-released.html)
