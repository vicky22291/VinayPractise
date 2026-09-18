# How to Use MLflow To Reproduce Results and Retrain Saved Keras ML Models

*Examine experiment results with TensorBoard and MLFlow UI*

- Source: https://www.databricks.com/blog/2018/09/21/how-to-use-mlflow-to-reproduce-results-and-retrain-saved-keras-ml-models.html
- Published: 2018-09-21
- Authors: Jules Damji
- Categories: platform, engineering, data-science-machine-learning
- Images: 3 total, 0 extracted as architecture

In [part 2](https://www.databricks.com/blog/2018/08/23/how-to-use-mlflow-to-experiment-a-keras-network-model-binary-classification-for-movie-reviews.html) of our series on MLflow blogs, we demonstrated how to use MLflow to track experiment results for a Keras network model using binary classification. We classified reviews from an IMDB dataset as positive or negative. And we created one baseline model and two experiments. For each model, we tracked its respective training accuracy and loss and validation accuracy and loss.

In this third part in our series, we’ll show how you can save your model, reproduce results, load a saved model, predict unseen reviews—all easily with MLFlow—and view results in TensorBoard.

## Saving Models in MLFlow

[MLflow logging APIs](https://mlflow.org/docs/latest/python_api/mlflow.html) allow you to save models in two ways. First, you can save a model on a local file system or on a cloud storage such as S3 or Azure Blob Storage; second, you can log a model along with its parameters and metrics. Both preserve the [Keras HDF5](https://keras.io/getting_started/faq/#how-can-i-install-HDF5-or-h5py-to-save-my-models-in-Keras) format, as noted in [MLflow Keras documentation](https://mlflow.org/docs/latest/models.html#keras-keras).

First, if you save the model using [MLflow Keras model API](https://www.mlflow.org/docs/1.20.2/python_api/mlflow.keras.html) to a store or filesystem, other ML developers not using MLflow can access your saved models using the generic [Keras Model APIs](https://keras.io/getting_started/faq/#how-can-i-save-a-keras-model). For example, within your MLflow runs, you can save a Keras model as shown in this sample snippet:

Once saved, ML developers outside MLflow can simply use the Keras APIs to load the model and predict it. For example,

Second, you can save the model as part of your run experiments, along with other metrics and artifacts as shown in the code snippet below:

With this second approach, you can access its run_uuid or location from the MLflow UI runs as part of its saved artifacts:

Fig 1. MLflow UI showing artifacts and Keras model saved

In our IMDB example, you can view code for both modes of saving in [*train_nn.py*](https://github.com/dmatrix/jsd-mlflow-examples/blob/master/keras/imdbclassifier/train_nn.py), class *KTrain()*. Saving model in this way provides access to reproduce the results from within MLflow platform or reload the model for further predictions, as we’ll show in the sections below.

## Reproducing Results from Saved Models

As part of machine development life cycle, reproducibility of any model experiment by ML team members is imperative. Often you will want to either retrain or reproduce a run from several past experiments to review respective results for sanity, audibility or curiosity.

One way, in our example, is to manually copy logged hyper-parameters from the MLflow UI for a particular `run_uuid` and rerun using [*`main_nn.py`*](https://github.com/dmatrix/jsd-mlflow-examples/blob/master/keras/imdbclassifier/main_nn.py) or [*`reload_nn.py`*](https://github.com/dmatrix/jsd-mlflow-examples/blob/master/keras/imdbclassifier/reload_nn.py) with the original parameters as arguments, as explained in the [README.md](https://github.com/dmatrix/jsd-mlflow-examples/blob/master/README.md#2-classifying-movie-reviews-a-keras-binary-classification-example).

Either way, you can reproduce your old runs and experiments:

Or use `mlflow run command`:

By default, the `tracking_server` defaults to the local `mlruns` directory. Here is an animated sample output from a reproducible run:

https://www.youtube.com/watch?v=tAg7WiraUm0
 Fig 2. Run showing reproducibility from a previous run_uuid

## Loading and Making Predictions with Saved Models

In the previous sections, when executing your test runs, the models used for these test runs also saved via the `mlflow.keras.log_model(model, "models")`. Your Keras model is saved in HDF5 file format as noted in [MLflow > Models > Keras](https://mlflow.org/docs/latest/models.html#keras-keras). Once you have found a model that you like, you can re-use your model using MLflow as well.

This model can be loaded back as a `Python Function` as noted noted in `mlflow.keras` using `mlflow.keras.load_model(path, run_id=None)`.

To execute this, you can load the model you had saved within MLflow by going to the MLflow UI, selecting your run, and copying the path of the stored model as noted in the screenshot below.

Fig 3. MLflow model saved in the Artifacts

With your model identified, you can type in your own review by loading your model and executing it. For example, let’s use a review that is not included in the IMDB Classifier dataset:

>  this is a wonderful film with a great acting, beautiful cinematography, and amazing direction

 

To run a prediction against this review, use the `predict_nn.py` against your model:

Or you can run it directly using `mlflow` and the `imdbclassifer` repo package:

The output for this command should be similar to the following output predicting a positive sentiment for the provided review.

## Examining Results with TensorBoard

In addition to reviewing your results in the MLflow UI, the code samples save TensorFlow events so that you can visualize the TensorFlow session graph. For example, after executing the statement `python main_nn.py,` you will see something similar to the following output:

You can extract the TensorBoard log directory with the output line stating `Writing TensorFlow events locally to ....` And to start TensorBoard, you can run the following command:

[Github Link](https://github.com/dmatrix/jsd-mlflow-examples/blob/master/images/visualize-graph-tensorboard-animated.gif)

Within the TensorBoard UI:

- Click on **Scalars** to review the same metrics recorded within MLflow: binary loss, binary accuracy, validation loss, and validation accuracy.
- Click on **Graph** to visualize and interact with your session graph

## Closing Thoughts

In this blog post, we demonstrated how to use MLflow to save models and reproduce results from saved models as part of the machine development life cycle. In addition, through both `python` and `mlflow` command line, we loaded a saved model and predicted the sentiment of our own custom review unseen by the model. Finally, we showcased how you can utilize MLflow and TensorBoard side-by-side by providing code samples that generate TensorFlow events so you can visualize the metrics as well as the session graph.

## What’s Next?

You have seen, in three parts, various aspects of MLflow: from experimentation to reproducibility and using MLlfow UI and TensorBoard for visualization of your runs.

You can try MLflow at [mlflow.org](https://mlflow.org/) to get started. Or try some of tutorials and examples in the documentation, including our example notebook Keras_IMDB.py for this blog.

## Read More

Here are some resources for you to learn more:

- Read [MLflow Docs](https://www.mlflow.org/docs/latest/index.html)
- Find out [How to Use Keras, TensorFlow, and MLflow with PyCharm](https://www.databricks.com/blog/2018/07/10/how-to-use-mlflow-tensorflow-and-keras-with-pycharm.html)
- Learn [How to Use MLflow to Experiment a Keras Network Model: Binary Classification for Movie Reviews](https://www.databricks.com/blog/2018/08/23/how-to-use-mlflow-to-experiment-a-keras-network-model-binary-classification-for-movie-reviews.html)
- Learn from [Introducing mlflow-apps: A Repository of Sample Applications for MLflow](https://www.databricks.com/blog/2018/08/16/introducing-mlflow-apps-a-repository-of-sample-applications-for-mlflow.html)
- View MLflow [Meetup Presentations](https://vimeo.com/284199854) and [Slides](https://www.slideshare.net/databricks/introduction-fo-mlflow)
- Get Github [sources for this blog example](https://github.com/dmatrix/jsd-mlflow-examples/tree/master/keras/imdbclassifier)
- Find out [New Features in MLflow Release v0.6.0](https://www.databricks.com/blog/2018/09/13/whats-new-in-mlflow-v0-6-0.html)
