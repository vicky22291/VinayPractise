# Announcing the MLflow 1.0 Release

- Source: https://www.databricks.com/blog/2019/06/06/announcing-the-mlflow-1-0-release.html
- Published: 2019-06-06
- Authors: Clemens Mewald, Matei Zaharia
- Categories: engineering, data-science-machine-learning, platform, solutions
- Images: 0 total, 0 extracted as architecture

[MLflow](https://mlflow.org/) is an open source platform to help manage the complete machine learning lifecycle. With MLflow, data scientists can track and share experiments locally (on a laptop) or remotely (in the cloud), package and share models across frameworks, and deploy models virtually anywhere.

Today we are excited to announce the release of MLflow 1.0. Since its launch one year ago, MLflow has been deployed at thousands of organizations to manage their production machine learning workloads, and has become generally available on services like [Managed MLflow on Databricks](https://www.databricks.com/product/managed-mlflow). The MLflow community has grown to over 100 contributors, and the MLflow PyPI package download rate has reached close to 600K times a month. The 1.0 release not only marks the maturity and stability of the APIs, but also adds a number of frequently requested features and improvements.

The release is publicly available starting today. [Install MLflow 1.0 using PyPl](https://pypi.org/project/mlflow/), read [our documentation](https://mlflow.org/docs/latest/index.html) to get started, and provide feedback on [GitHub](https://github.com/mlflow/mlflow). Below we describe just a few of the new features in MLflow 1.0. Please refer to the [release notes](https://github.com/mlflow/mlflow/releases/tag/1.0.0) for a full list.

## What’s New in MLflow 1.0

### Support for X Coordinates in the Tracking API

Data scientists and engineers who track metrics during ML training often either want to track summary metrics at the end of a training run, e.g., accuracy, or “streaming metrics” that are produced while the model is training, e.g., loss per mini-batch. Those streaming metrics are often computed for each mini-batch or epoch of training data. To enable accurate logging of these metrics, as well as better visualizations, the `log_metric` API now supports a step parameter.

The metric step can be any integer that represents the x coordinate for the metric. For example, if you want to log a metric for each epoch of data, the step would be the epoch number.

The MLflow UI now also supports plotting metrics against provided x coordinate values. In the example below, we show how the UI can be used to visualize two metrics against walltime. Although they were logged at different points in time (as shown by the misalignment of data points in the “relative time” view), the data points relate to the same x coordinates. By switching to the “steps” view you can see the data points from both metrics lined up by their x coordinate values.

### Improved Search Features

To improve search functionality, the search filter API now supports a simplified version of the SQL WHERE clause. In addition, it has been enhanced to support searching by run attributes and tags in addition to metrics and parameters. The example below shows a search for runs across all experiments by parameter and tag values.

### Batched Logging of Metrics

In experiments where you want to log multiple metrics, it is often more convenient and performant to log them as a batch, as opposed to individually. MLflow 1.0 includes a `runs/log-batch` REST API endpoint for logging multiple metrics, parameters, and tags with a single API request.

You can call this batched-logging endpoint from:

- [Python](https://www.mlflow.org/docs/latest/python_api/index.html)
- [R](https://mlflow.org/docs/latest/R-api.html)
- [Java](https://mlflow.org/docs/latest/java_api/index.html)

### Support for HDFS as an Artifact Store

In addition to local files, MLflow already supports the following storage systems as artifact stores: Amazon S3, Azure Blob Storage, Google Cloud Storage, SFTP, and NFS. With the MLflow 1.0 release, we add support for HDFS as an artifact store backend. Simply specify a `hdfs://` URI with `--backend-store-uri`:

### Windows Support for the MLflow Client

MLflow users running on the Windows Operating System can now track experiments with the MLflow 1.0 Windows client.

### Building Docker Images for Deployment

One of the most common ways of deploying ML models is to build a docker container. MLflow 1.0 adds a new command to build a docker container whose default entrypoint serves the specified MLflow pyfunc model at port 8080 within the container. For example, you can build a docker container and serve it at port 5001 on the host with these commands:

### ONNX Model Flavor

This release adds an experimental [ONNX](https://onnx.ai/) model flavor. To log ONNX models in MLflow format, use the `mlflow.onnx.save_model()` and `mlflow.onnx.log_model()` methods. These methods also add the `pyfunc` flavor to the MLflow Models that they produce, allowing the models to be interpreted as generic Python functions for inference via `mlflow.pyfunc.load_pyfunc()`. The pyfunc representation of an MLflow ONNX model uses the ONNX Runtime execution engine for evaluation. Finally, you can use the `mlflow.onnx.load_model()` method to load MLflow Models with the ONNX flavor in native ONNX format.

### Other Features and Updates

Note that this major version release includes several breaking changes. Please review the full list of changes and contributions from the community in the [1.0 release notes](https://github.com/mlflow/mlflow/releases/tag/1.0.0). We welcome more input on [mlflow-users@googlegroups.com](https://groups.google.com/forum/#!forum/mlflow-users) or by filing issues or submitting patches on GitHub. For real-time questions about MLflow, we also run a [Slack channel](https://mlflow-users.slack.com/join/shared_invite/enQtMzkxMTAwNTcyODM5LTNkNTc5YWZlNDNjMzZiYWJhOTQwMjYwYWE3NDU2YTgzMDViYjJhNWI1MGI4NjViNTA0M2FhMzNhZTVkODE2NmU) for MLflow, and you can follow [@MLflow](https://twitter.com/MLflow) on Twitter.

## What’s Next After 1.0

The 1.0 release marks a milestone for the MLflow components that have been widely adopted: Tracking, Models, and Projects. While we continue development on those components, we are also investing in new components to cover more of the ML lifecycle. The next major addition to MLflow will be a Model Registry that allows users to manage their ML model’s lifecycle from experimentation to deployment and monitoring. Watch the [recording of the Spark AI Summit Keynote on MLflow](https://youtu.be/QJW_kkRWAUs?t=1377) for a demo of upcoming features.

Don’t miss our upcoming webinar in which we’ll cover the 1.0 updates and more: [Managing the Machine Learning Lifecycle: What’s new with MLflow](https://pages.databricks.com/201906-US-WB-New-with-MLflow_Reg.html?utm_source=website&utm_medium=blog&utm_campaign=whats-new-mlflow&_ga=2.166135934.1784873400.1559256775-528444717.1555636081) – on Thursday June 6th.

Finally, join us for the Bay Area MLflow Meetup hosted by Microsoft on Thursday June 20th in Sunnyvale. [Sign up here](https://www.meetup.com/Bay-Area-MLflow/events/261840002/).

## Read More

To get started with MLflow on your laptop or on Databricks you can:

1. Read the [quickstart guide](https://mlflow.org/docs/latest/quickstart.html)
2. Work through the[tutorial](https://www.mlflow.org/docs/latest/tutorials-and-examples/tutorial.html)
3. Try Managed [MLflow on Databricks](https://www.databricks.com/product/managed-mlflow)

---

## Credits

We want to thank the following contributors for updates, doc changes, and contributions in MLflow 1.0: Aaron Davidson, Alexander Shtuchkin, Anca Sarb, Andrew Chen, Andrew Crozier, Anthony, Christian Clauss, Clemens Mewald, Corey Zumar, Derron Hu, Drew McDonald, Gábor Lipták, Jim Thompson, Kevin Kuo, Kublai-Jing, Luke Zhu, Mani Parkhe, Matei Zaharia, Paul Ogilive, Richard Zang, Sean Owen, Siddharth Murching, Stephanie Bodoff, Sue Ann Hong, Sungjun Kim, Tomas Nykodym, Yahro, Yorick, avflor, eedeleon, freefrag, hchiuzhuo, jason-huling, kafendt, vgod-dbx.
