# MLflow v0.8.0 Features Improved Experiment UI and Deployment Tools

- Source: https://www.databricks.com/blog/2018/11/21/mlflow-v0-8-0-features-improved-experiment-ui-and-deployment-tools.html
- Published: 2018-11-21
- Authors: Aaron Davidson, Jules Damji
- Categories: engineering, data-science-machine-learning
- Images: 0 total, 0 extracted as architecture

Last week we released [MLflow v0.8.0](https://www.mlflow.org/) with multiple new features, including improved UI experience and support for deploying models directly via Docker containers to the
[Azure Machine Learning Service Workspace](https://docs.microsoft.com/en-us/azure/machine-learning/quickstart-create-resources).

Now available on [PyPI](https://pypi.org/project/mlflow/) and with docs [online](https://mlflow.org/docs/latest/index.html), you can install this new release with `pip install mlflow` as described in the [MLflow quickstart guide](https://mlflow.org/docs/latest/quickstart.html).

In this post, we will describe a couple of major MLflow v0.8.0 features:

- An improved MLflow UI experience for tracking and categorizing experiments
- Support for deploying models in Docker containers to Azure Machine Learning Service

## Improved MLflow UI Experience

1. **Compact Display for Metrics and Parameters**: To avoid clutter and an explosion of columns for each metric or parameter, now we group them together in a single tabular column by default. That way, each runs’ parameters and metrics are listed nearby. Users can still click each parameter or metric to display it in a separate column or sort by it and customize their view this way.
2. **Nesting Runs**: For nested MLflow runs, which are common in hyperparameter search or multi-step workflows, the UI will display a collapsible tree underneath each parent run. This makes it much easier to organize and visualize multi-step workflows.
3. **Labeling Runs**: While MLflow gives each run a UUID by default, you can also now assign each run a name through the API. These names can also be edited in the UI.
4. **UI Persistence**: The MLflow UI now remembers your filters, sorting and column setup in browser local storage so you no longer need to reconfigure the view each time.

Let’s look at one of these features in more detail -- visualizing nested runs. First, we can use the following code to create nested default runs:

The MLflow UI will now display these runs in a tree and let you expand them:

https://www.youtube.com/watch?v=vBebliInvRs

In practice, of course, you usually won’t create nested runs in a single Python program as above. Instead, they will come up when you run multi-step workflows or hyperparameter search. MLflow includes examples of both [workflows](https://github.com/mlflow/mlflow/tree/master/examples/multistep_workflow) and [hyperparameter search](https://github.com/mlflow/mlflow/tree/master/examples/hyperparam).

## Deployment to Azure ML Service

Our [Microsoft Azure Machine Learning](https://mlflow.org/docs/latest/models.html#microsoft-azure-ml) deployment tool has been modified to use the updated Azure ML SDK for deploying MLflow models packaged as Docker containers. Using the [mlflow.azureml](https://www.mlflow.org/docs/latest/python_api/mlflow.azureml.html) module, you can package a ***python_function*** model into an Azure ML container image, and deploy this image to the Azure Kubernetes Service (AKS) and the Azure Container Instances (ACI) platforms for real-time serving.

For an example, [read the documentation](https://mlflow.org/docs/latest/models.html#microsoft-azure-ml) on how to build an image using the MLflow CLI and how to deploy it.

## Other Features and Bug Fixes

In addition to these features, several other new pieces of functionality are included in this release. Some items worthy of note are:

### Breaking changes:

- [CLI] `mlflow sklearn serve` has been removed in favor of `mlflow pyfunc serve`, which takes the same arguments but works against any pyfunc model (#690, @dbczumar).

### Features:

- [Scoring] The pyfunc server and SageMaker now support the pandas "split" JSON format in addition to the "records" format. The split format allows the client to specify the order of columns, which is necessary for some model formats. We recommend switching client code over to use this new format (by sending the Content-Type header `application/json; format=pandas-split`), as it will become the default JSON format in MLflow 0.9.0. (#690, @dbczumar)
- [Server/Python/Java] Add rename_experiment to Tracking API (#570, @aarondav)
- [Server] Add get_experiment_by_name to RestStore (#592, @dmarkhas)
- [Server] Allow passing gunicorn options when starting a mlflow server (#626, @mparkhe)
- [Artifacts] FTP artifact store (#287, @Shenggan).

### Bug Fixes:

- [Python] Update TensorFlow integration library to match API provided by other flavors (#612, @dbczumar; #670, @mlaradji)
- [Python] Support for TensorFlow 1.12 (#692, @smurching)
- [R] Explicitly loading Keras module at predict time no longer required (#586, @kevinykuo)
- [R] Pyfunc serve can correctly load models saved with the R Keras support (#634, @tomasatdatabricks)
- [R] Increase network timeout of calls to the RestStore from 1 second to 60 seconds (#704, @aarondav)
- [Server] Deleting the default experiment no longer causes it to be immediately recreated (#604, @andrewmchen; #641, @schipiga)
- [Server] Azure Blob Storage artifact repo supports Windows paths (#642, @marcusrehm)
- [Server] Improve behavior when environment and run files are corrupted (#632, #654, #661, @mparkhe).

The full list of changes and contributions from the community can be found in the 0.8.0 Changelog. We welcome more input on [mlflow-users@googlegroups.com](https://groups.google.com/forum/#!forum/mlflow-users) or by [filing issues](https://github.com/databricks/mlflow/pulls) on GitHub. For real-time questions about MLflow, we also offer a [Slack channel](https://mlflow-users.slack.com/join/shared_invite/enQtMzkxMTAwNTcyODM5LTNkNTc5YWZlNDNjMzZiYWJhOTQwMjYwYWE3NDU2YTgzMDViYjJhNWI1MGI4NjViNTA0M2FhMzNhZTVkODE2NmU). Finally, you can follow [@MLflowOrg](Kevin Kuo) on Twitter for the latest news.

## Credits

We want to thank the following contributors for updates, doc changes, and contributions in MLflow 0.8: Aaron Davidson, Adam Bernhard, Corey Zumar, Dror Atariah, GCBallesteros, Javier Luraschi, Jules Damji, Kevin Kuo, Mani Parkhe, Marcus Rehm, Mohamed Laradji, Richin Jain, Sergei Chipiga, Shenggan, Siddharth Murching, Stephanie Bodoff, Tomas Nykodym, Zhao Feng.
