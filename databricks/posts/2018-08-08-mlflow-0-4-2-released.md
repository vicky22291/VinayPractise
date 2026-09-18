# MLflow 0.4.2 Released

- Source: https://www.databricks.com/blog/2018/08/08/mlflow-0-4-2-released.html
- Published: 2018-08-08
- Authors: Aaron Davidson, Denny Lee
- Categories: company, engineering, data-science-machine-learning, announcements, open-source
- Images: 2 total, 0 extracted as architecture

Today, we’re excited to announce MLflow v0.4.0, MLflow v0.4.1, and v0.4.2 which we released within the last week with some of the recently requested features. MLflow 0.4.2 is already available on [PyPI](https://pypi.org/project/mlflow/) and docs are [updated](https://mlflow.org/docs/latest/index.html). If you do `pip install mlflow` as described in the MLflow quickstart guide, you will get the recent release.

In this post, we’ll describe the new features and fixes in this release.

## Azure Blob Storage Artifact Support

As part of MLflow 0.4.0, we’ve added support for storing artifacts in Azure Blob Storage, through the `--default-artifact-root` parameter to the `mlflow server` command. This makes it easy to run MLflow training jobs on multiple Azure cloud VMs and track results across them. The following example shows how to launch the tracking server with an Azure Blob Storage artifact store. You will need to set the `AZURE_STORAGE_CONNECTION_STRING` environment variable as noted in [MLflow Tracking > Azure Blob Storage](https://mlflow.org/docs/latest/tracking.html#azure-blob-storage).

## Using MLflow with PyTorch and Tensorboard

We’ve added some samples that include advanced tracking, including a PyTorch TensorBoard Sample with the following MLflow UI and TensorBoard output.

https://www.youtube.com/watch?v=3un20Ey9iPY

https://www.youtube.com/watch?v=sxzyEqxVFS8

## H2O Integration

Thanks to [PR 170](https://github.com/mlflow/mlflow/pull/170), MLflow now includes support for H2O model export and serving.

 

## Other Features and Bug Fixes

In addition to these features, other items, bugs and documentation fixes are included in these releases. Some items worthy of note are:

-  MLflow experiments REST API and mlflow experiments create now support providing `--artifact-location` (Issue #232)
- [UI] Show GitHub links in the UI for projects run from http(s):// GitHub URLs (Issue #235)
- Fix Spark model support when saving/loading models to/from distributed filesystems (Issue #180)
- [Tracking] GCS artifact storage is now a pluggable dependency (no longer installed by default). To enable GCS support, install google-cloud-storage on both the client and tracking server via pip. (Issue #202)
- [Projects] Support for running projects in subdirectories of Git repos (Issue #153)
-  [SageMaker] Support for specifying a compute specification when deploying to SageMaker (Issue #185)

The full list of changes and contributions from the community can be found in the 0.4.2 Changelog. We welcome more input on [mlflow-users@googlegroups.com](https://groups.google.com/forum/#!forum/mlflow-users) or by [filing issues](https://github.com/databricks/mlflow/pulls) or submitting patches on GitHub. For real-time questions about MLflow, we’ve also recently created a [Slack channel](https://mlflow-users.slack.com/join/shared_invite/enQtMzkxMTAwNTcyODM5LTNkNTc5YWZlNDNjMzZiYWJhOTQwMjYwYWE3NDU2YTgzMDViYjJhNWI1MGI4NjViNTA0M2FhMzNhZTVkODE2NmU) for MLflow as well as you can follow [@MLflow](https://twitter.com/MLflow) on Twitter.

## Watch More

[Watch Introduction to MLflow with Matei Zaharia](https://vimeo.com/284199854) from the [Seattle Spark+AI Meetup on August 2, 2018](https://www.meetup.com/Seattle-Spark-Meetup/events/252959137/); thanks to Scott Klein for the recording.

## Credits

MLflow 0.4.2 includes patches from Aaron Davidson, Andrew Chen, Arinto Murdopom, Corey Zumar, Javier Luraschi, Joel Akeret, Juntai Zheng, Matei Zaharia, Siddharth Murching, Stephanie Bodoff, Tomas Nykodym, Toon Baeyen
