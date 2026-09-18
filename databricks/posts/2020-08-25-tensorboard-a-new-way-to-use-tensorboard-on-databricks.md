# %tensorboard - a new way to use TensorBoard on Databricks

- Source: https://www.databricks.com/blog/2020/08/25/tensorboard-a-new-way-to-use-tensorboard-on-databricks.html
- Published: 2020-08-25
- Authors: Jerry Liang, Hossein Falaki
- Categories: engineering, data-science-machine-learning
- Images: 0 total, 0 extracted as architecture

## Introduction

With the [Databricks Runtime 7.2 release](https://docs.databricks.com/release-notes/runtime/7.2.html), we are introducing a new magic command `%tensorboard`. This brings the interactive TensorBoard experience Jupyter notebook users expect to their Databricks notebooks. The `%tensorboard` command starts a TensorBoard server and embeds the TensorBoard user interface inside the Databricks notebook for data scientists and machine learning engineers to visualize and debug their machine learning projects. We’ve made it much easier to use TensorBoard in Databricks.

## Motivation

In 2017, we released the  `dbutils.tensorboard.start()` API to manage and use TensorBoard inside Databricks python notebooks. This API only permits one active TensorBoard process on a cluster at any given time - which hinders multi-tenant use-cases. Early last year, TensorBoard released its own API for notebooks via the `%tensorboard` python magic command. This API not only starts TensorBoard processes but also exposes the TensorBoard’s command line arguments in the notebook environment. In addition, it embeds the TensorBoard UI inside notebooks, whereas the `dbutils.tensorboard.start` API prints a link to open TensorBoard in a new tab.

## Welcoming `%tensorboard`

Upgrading to the `%tensorboard` magic command in Databricks has allowed us to take advantage of TensorBoard’s new API features. It is now possible to have multiple concurrent TensorBoard processes on a cluster as well as to interact with a TensorBoard UI inline in a notebook.

We’ve built upon the TensorBoard experience to better integrate it into the Databricks workflow:

- A link on top of the embedded TensorBoard UI to open TensorBoard in a new browser tab.
- Notebook-scoped process re-use to improve performance.
- The ability to stop a notebook’s TensorBoard servers and free up cluster resources by detaching the notebook or clearing its state.

With the introduction of `%tensorboard` magic command we are deprecating `dbutils.tensorboard.start` and plan to remove it in a future major Databricks Runtime release.

## How to get started

Here’s how you can quickly start using `%tensorboard` in your machine learning project. Inside your Databricks notebook:

1. Run `%load_ext tensorboard` to enable the `%tensorboard` magic command
2. Start and view your TensorBoard by running `%tensorboard --logdir $experiment_log_dir`, where `experiment_log_dir` is the path to a directory in DBFS dedicated to TensorBoard logs.
3. Use TensorBoard callbacks or TensorFlow or PyTorch file writers to generate logs during your training process. To make sure your logs are separated by runs, set the function’s log directory to a run specific subdirectory in DBFS. For TensorFlow, this is as simple as:

1. Refresh your TensorBoard user interface to visualize your training process using the data you just generated

For an end-to-end example, [check out this notebook](https://www.databricks.com/notebooks/tensorflow-single-node.html) using TensorBoard in a TensorFlow project.

For more details on using `%tensorboard` in Databricks, you can read [our official documentation](https://docs.databricks.com/applications/machine-learning/train-model/tensorflow.html#using-tensorboard).
