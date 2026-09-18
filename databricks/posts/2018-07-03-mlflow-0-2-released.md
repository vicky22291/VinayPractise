# MLflow 0.2 Released

- Source: https://www.databricks.com/blog/2018/07/03/mlflow-0-2-released.html
- Published: 2018-07-03
- Authors: Mani Parkhe, Matei Zaharia
- Categories: engineering, open-source, data-science-machine-learning
- Images: 0 total, 0 extracted as architecture

At this year’s [Spark+AI Summit](https://www.databricks.com/sparkaisummit/north-america/sessions), we [introduced MLflow](https://www.databricks.com/blog/2018/06/05/introducing-mlflow-an-open-source-machine-learning-platform.html), an open source platform to simplify the machine learning lifecycle. In the 3 weeks since the release, we’ve already seen a lot of interest from data scientists and engineers in using and contributing to MLflow. MLFlow’s [GitHub repository](https://github.com/databricks/mlflow) already has 180 forks, and over a dozen contributors have submitted issues and pull requests. In addition, close to 100 people came to our first [MLflow meetup](https://www.meetup.com/Bay-Area-MLflow/events/251995571/) last week.

Today, we’re excited to announce MLflow v0.2, which we released a few days ago with some of the most requested features from internal clients and open source users. MLflow 0.2 is already available if you `pip install mlflow` as described in the [MLflow quickstart guide](https://mlflow.org/docs/latest/quickstart.html). In this post, we’ll cover the main new features in this release.

## Built-In TensorFlow Integration

MLflow makes it easy to train and serve models from any machine learning library as long as you can wrap them in a Python function, but for very commonly used libraries, we want to provide built-in support. In this release, we added the `mlflow.tensorflow` package, which makes it easy to log a TensorFlow model to MLflow Tracking. Once you have logged a model this way, you can immediately pass it to all the deployment tools already supported by MLflow (e.g. local REST servers, Azure ML serving, or Apache Spark for batch inference).

The following example shows how users can log trained TF models and use inbuilt functionality to deploy it using pyfunc abstraction.

Training environment: Save trained TF model

Deployment environment: Load saved TF model and predict

## Production Tracking Server

In MLflow 0.2, we’ve added a new `mlflow server` command that launches a production version of the MLflow Tracking server for tracking and querying experiment runs. Unlike the local `mlflow ui` command, `mlflow server` can support multiple worker threads and S3-backed storage as described below. You can read through the MLflow documentation to learn [how to run a tracking server](https://www.mlflow.org/docs/latest/tracking.html#running-a-tracking-server).

## S3-Backed Artifact Storage

One of the key features in MLflow is logging the outputs of your training runs, which can include arbitrary files called “artifacts.” However, the first version of MLflow only supported logging artifacts to a shared POSIX file system. In MLflow 0.2, we’ve added support for storing artifacts in S3, through the `--artifact-root` parameter to the `mlflow server` command. This makes it easy to run MLflow training jobs on multiple cloud instances and track results across them. The following example shows how to launch the tracking server with an S3 artifact store.

Running MLflow Server on an EC2 instance:

MLflow Client:

## Other Improvements

In addition to these larger features, several bugs and documentation fixes are included in this release. The full list of changes can be found [in the CHANGELOG](https://github.com/databricks/mlflow/blob/master/CHANGELOG.rst). We welcome more input on [mlflow-users@googlegroups.com](https://groups.google.com/forum/#!forum/mlflow-users) or by [filing issues](https://github.com/databricks/mlflow/pulls) or [submitting patches](https://github.com/databricks/mlflow/blob/master/CONTRIBUTING.rst) on GitHub. For real-time questions about MLflow, we’ve also recently created a [Slack channel](https://mlflow-users.slack.com/join/shared_invite/enQtMzkxMTAwNTcyODM5LTNkNTc5YWZlNDNjMzZiYWJhOTQwMjYwYWE3NDU2YTgzMDViYjJhNWI1MGI4NjViNTA0M2FhMzNhZTVkODE2NmU) for MLflow.

## What’s Next for MLflow?

We plan to keep updating MLflow rapidly while it’s in alpha. For example, our ongoing work includes built-in integrations with more libraries (such as PyTorch, Keras, and MLlib) and further improvements to the usability of the tracking server. For an overview of what we’re working on next, take a look at the roadmap slides in our [presentation](https://www.slideshare.net/databricks/introduction-fo-mlflow) from last week’s meetup or [watch the meetup presentation](https://vimeo.com/278050994).

For Databricks users who would like to try a hosted version of MLflow, we are also accepting signups at [databricks.com/mlflow](https://www.databricks.com/product/managed-mlflow).

## Credits

MLflow 0.2 includes patches from Aaron Davidson, Andrew Chen, Andy Konwinski, David Matthews, Denny Lee, Jiaxin Shan, Joel Akeret, Jules Damji, Juntai Zheng, Justin Olsson, Mani Parkhe, Manuel Garrido, Matei Zaharia, Michelangelo D'Agostino, Ndjido Ardo Bar, Peng Yu, Siddharth Murching, Stephanie Bodoff, Tingfan Wu, Tomas Nykodym, and Xue Yu
