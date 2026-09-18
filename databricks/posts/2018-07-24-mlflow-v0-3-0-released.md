# MLflow v0.3.0 Released

- Source: https://www.databricks.com/blog/2018/07/24/mlflow-v0-3-0-released.html
- Published: 2018-07-24
- Authors: Aaron Davidson, Jules Damji
- Categories: announcements, engineering, open-source, data-science-machine-learning, company
- Images: 1 total, 0 extracted as architecture

Today, we’re excited to announce MLflow v0.3.0, which we released last week with some of the requested features from internal clients and open source users. MLflow 0.3.0 is already available on [PyPI](https://pypi.org/project/mlflow/) and docs are [updated](https://mlflow.org/docs/latest/index.html). If you do `pip install mlflow` as described in the MLflow quickstart guide, you will get the recent release.

In this post, we’ll describe a couple new features and enumerate other items and bug fixes filed as issues on the [Github repository](https://github.com/databricks/mlflow).

## GCP-Backed Artifact Support

We’ve added support for storing artifacts in Google Storage, through the `--default-artifact-root` parameter to the `mlflow server command`. This makes it easy to run MLflow training jobs on multiple cloud instances and track results across them. The following example shows how to launch the tracking server with a GCP artifact store. Also, you will need to setup [Authentication](https://google-cloud.readthedocs.io/en/latest/core/auth.html) as described in the [documentation](https://google-cloud.readthedocs.io/en/latest/core/auth.html). This item closes issue #152.

## Apache Spark MLlib Integration

As part of [MLflow’s Model](https://mlflow.org/docs/latest/models.html#) component, we have added [Spark MLlib model](https://mlflow.org/docs/latest/models.html#spark-mllib-spark) as a [model flavor](https://mlflow.org/docs/latest/models.html#built-in-model-flavors).
 This means that you can export Spark MLlib models as MLflow models. Exported models when saved using MLlib’s native serialization can be deployed and loaded as Spark MLlib models or as `Python Function` within MLflow. To save and load these models, use the [spark.mflow](https://mlflow.org/docs/latest/python_api/mlflow.spark.html#module-mlflow.spark) API. This addresses issue #72. For example, you can save a Spark MLlib model, as shown in the code snippet below:

Now we can access this MLlib persisted model in an MLflow application.

## Other Features and Bug Fixes

In addition to these features, other items, bugs and documentation fixes are included in this release. Some items worthy of note are:

- [SageMaker] Support for deleting and updating applications deployed via SageMaker (issue #145)
- [SageMaker] Pushing the MLflow SageMaker container now includes the MLflow version that it was published with (issue #124)
- [SageMaker] Simplify parameters to SageMaker deployment by providing sane defaults (issue #126)

The full list of changes and contributions from the community can be found in the [CHANGELOG](https://github.com/databricks/mlflow/blob/master/CHANGELOG.rst#030-2018-07-18). We welcome more input on [mlflow-users@googlegroups.com](https://groups.google.com/forum/#!forum/mlflow-users) or by [filing issues](https://github.com/databricks/mlflow/pulls) or [submitting patches](https://github.com/databricks/mlflow/blob/master/CONTRIBUTING.rst) on GitHub. For real-time questions about MLflow, we’ve also recently created a [Slack channel](https://mlflow-users.slack.com/join/shared_invite/enQtMzkxMTAwNTcyODM5LTNkNTc5YWZlNDNjMzZiYWJhOTQwMjYwYWE3NDU2YTgzMDViYjJhNWI1MGI4NjViNTA0M2FhMzNhZTVkODE2NmU) for MLflow.

## Read More

For an overview of what we’re working on next, take a look at the roadmap slides in our [presentation](https://www.slideshare.net/databricks/mlflow-infrastructure-for-a-complete-machine-learning-life-cycle) from last week’s [Bay Area Apache Spark Meetup](https://www.meetup.com/spark-users/events/251930598/) or [watch the meetup presentation](https://vimeo.com/281327641).

## Credits

MLflow 0.3.0 includes patches from Aaron Davidson, Andrew Chen, Bill Chambers, Brett Nekolny, Corey Zumar, Denny Lee, Emre Sevinç, Greg Gandenberger, Jules Damji, Juntai Zheng, Mani Parkhe, Matei Zaharia, Mike Huston, Siddharth Murching, Stephanie Bodoff, Sue Ann Hong, Tomas Nykodym, Vahe Hakobyan
