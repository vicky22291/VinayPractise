# New Features in MLflow v0.5.2 Release

- Source: https://www.databricks.com/blog/2018/08/21/whats-new-in-mlflow-v0-5-0-release.html
- Published: 2018-08-21
- Authors: Aaron Davidson, Jules Damji
- Categories: engineering, data-science-machine-learning, platform, open-source
- Images: 2 total, 0 extracted as architecture

Today, we’re excited to announce MLflow v0.5.0, MLflow v0.5.1, and MLflow v0.5.2, which were released last week with some new features. [MLflow 0.5.2](https://mlflow.org) is already available on [PyPI](https://pypi.org/project/mlflow/) and docs are [updated](https://mlflow.org/docs/latest/index.html). If you do `pip install mlflow` as described in the MLflow quickstart guide, you will get the recent release.

In this post, we’ll describe new features and fixes in these releases.

## Keras and PyTorch Model Integration

As part of MLflow 0.5.2 and continued effort to offer a range of machine learning frameworks, we’ve extended support to save and load Keras and PyTorch models using [*log_model*](https://mlflow.org/docs/latest/models.html) APIs. These model flavors APIs export their models in their respective formats, so either Keras or PyTorch applications can reuse them, not only from MLflow but natively from Keras or PyTorch code too.

### Using Keras Model APIs

Once you have defined, trained, and evaluated your Keras model, you can log the model as part of an MLflow artifact as well as export the model in [Keras HDF5](https://keras.io/getting_started/faq/#how-can-i-use-hdf5-inputs-with-keras) format for others to load it or serve it for predictions. For example, this Keras snippet code shows how:

### Using PyTorch Model APIs

Similarly, you can use the model APIs to log models in PyTorch, too. For example, the code snippets below are similar in PyTorch, with minor changes in how PyTorch exposes its methods. However, with *pyfunc* the method is the same: *predict()*:

## Python APIs for Experiment and Run Management

To query past runs and experiments, we added new public APIs as part of [`mlflow.tracking`](https://mlflow.org/docs/latest/python_api/mlflow.tracking.html) module. In the process, we have also refactored the old APIs into [`mlflow`](https://mlflow.org/docs/latest/python_api/mlflow.html) module for logging parameters and metrics for current runs. So for example, to log basic parameters and metrics for the current run, you can use the *mlflow.log_xxxx()* calls.

However, to access this run's results, say in another part of application, you can use `mflow.tracking` APIs as such:

While the former deals with persisting metrics, parameters and artifacts for the currently active run, the latter allows managing experiments and runs (especially historical runs).

With this new APIs, developers have access to Python CRUD interface to [MLflow Experiments and Runs](https://mlflow.org/docs/latest/python_api/mlflow.tracking.html). Because it is a lower level API, it maps well to REST calls. As such you can build a REST-based service around your experimental runs.

## UI Improvements for Comparing Runs

Thanks to Toon Baeyens ([Issue #268](https://github.com/mlflow/mlflow/pull/268), @ToonKBC), in the [MFlow Tracking UI](https://mlflow.org/docs/latest/tracking.html#tracking-ui) we can compare two runs with a scatter plot. For example, this image shows a number of trees and its corresponding rmse metric.

Also, with better columnar and tabular presentation and organization of experimental runs, metrics, and parameters, you can easily visualize the outcomes and compare runs. Together with navigation breadcrumbs, the overall encounter is a better UI experience.

## Other Features and Bug Fixes

In addition to these features, other items, bugs and documentation fixes are included in this release. Some items worthy of note are:

- [Sagemaker] Users can specify a custom VPC when deploying SageMaker models (#304, @dbczumar)
- [Artifacts] SFTP artifactory store added (#260, @ToonKBC)
- [Pyfunc] Pyfunc serialization now includes the Python version and warns if the major version differs (can be suppressed by using `load_pyfunc(suppress_warnings=True))` (#230, @dbczumar)
- [Pyfunc] Pyfunc serve/predict will activate conda environment stored in MLModel. This can be disabled by adding `--no-conda` to `mlflow pyfunc serve` or `mlflow pyfunc predict` (#225, @0wu)
- [CLI] `mlflow run` can now be run against projects with no `conda.yaml` specified. By default, an empty conda environment will be created -- previously, it would just fail. You can still `pass --no-conda` to avoid entering a conda environment altogether (#218, @smurching)
- Fix with mlflow.start_run() as run to actually set run to the created Run (previously, it was None) (#322, @tomasatdatabricks)
- [BUG-FIXES] Fixes to DBFS artifactory to throw an exception if logging an artifact fails (#309) and to mimic FileStore's behavior of logging subdirectories (#347, @andrewmchen)
- [BUG-FIXES] Fix spark.load_model not to delete the DFS tempdir (#335, @aarondav)
- [BUG-FIXES] Make Python API forward-compatible with newer server versions of protos (#348, @aarondav)
- [BUG-FIXES] Fix a bug with ECR client creation that caused `mlflow.sagemaker.deploy()` to fail when searching for a deployment Docker image (#366, @dbczumar)
- [UI] Improved API docs (#305, #284, @smurching)

The full list of changes and contributions from the community can be found in the 0.5.2 Changelog. We welcome more input on [mlflow-users@googlegroups.com](https://groups.google.com/forum/#!forum/mlflow-users) or by [filing issues](https://github.com/databricks/mlflow/pulls) or submitting patches on GitHub. For real-time questions about MLflow, we’ve also recently created a [Slack channel](https://mlflow-users.slack.com/join/shared_invite/enQtMzkxMTAwNTcyODM5LTNkNTc5YWZlNDNjMzZiYWJhOTQwMjYwYWE3NDU2YTgzMDViYjJhNWI1MGI4NjViNTA0M2FhMzNhZTVkODE2NmU) for MLflow as well as you can follow [@MLflow](https://twitter.com/MLflow) on Twitter.

## Credits

MLflow 0.5.2 includes patches, bug fixes, and doc changes from Aaron Davidson, Adrian Zhuang, Alex Adamson, Andrew Chen, Arinto Murdopo, Corey Zumar, Jules Damji, Matei Zaharia, @RBang1, Siddharth Murching, Stephanie Bodoff, Tomas Nykodym, Tingfan Wu, Toon Baeyens, and Yassine Alouini.
