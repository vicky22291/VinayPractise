# A Pattern for the Lightweight Deployment of Distributed XGBoost and LightGBM Models

- Source: https://www.databricks.com/blog/pattern-lightweight-deployment-distributed-xgboost-and-lightgbm-models
- Published: 2023-10-06
- Authors: Jesse Heravi, Sean Owen, Marshall Carter, Nichole Lu, Bryan Smith
- Categories: engineering, data-science-machine-learning
- Images: 0 total, 0 extracted as architecture

A common challenge data scientists encounter when developing machine learning solutions is training a model on a dataset that is too large to fit into a server's memory. We encounter this when we wish to train a model to predict customer churn or propensity and need to deal with tens of millions of unique customers. We encounter this when we need to calculate the lift associated with hundreds of millions of advertising impressions made during a given period. And we encounter this when we need to evaluate the billions of online interactions for anomalous behaviors.

One solution commonly employed to overcome this challenge is to rewrite the model to work against an Apache Spark dataframe. With a Spark dataframe, the dataset is broken up into smaller subsets known as partitions which are distributed across the collective resources of a Spark cluster. Need more memory? Just add more servers to the cluster.

## Not So Fast

While this sounds like a great solution for overcoming the memory limitations of a given server, the fact is that not every model has been written to take advantage of a distributed Spark dataframe. While the Spark MLlib family of models addresses many of the core algorithms data scientists employ, there are many other models that have not yet implemented support for distributed data processing.

In addition, if we wish to use a model trained on a Spark dataframe for inference (prediction), that model must run in the context of a Spark environment. This dependency creates an overhead that limits the scenarios within which such models can be deployed.

## Overcoming the Challenge

Recognizing that memory limitations are a key blocker for an increasing number of machine learning scenarios, more and more ML models are being updated to support Spark dataframes. This includes the very popular XGBoost family of models and the lightweight variants in the LightGBM model family. The support for Spark dataframes in these two model families unlocks access to distributed data processing for many, many data scientists. But how might we overcome the downstream problem of model overhead during inference?

In the [notebook assets](https://notebooks.databricks.com/notebooks/RCG/xgboost-serving-enabler/index.html) accompanying this blog, we document a simple pattern for training both an XGBoost and a LightGBM model in a distributed manner using a Spark dataframe and then transferring the information learned to a non-distributed version of the model. The non-distributed version carries with it no dependencies on Apache Spark and as such can be deployed in a more lightweight manner that's more conducive to microservice and edge deployment scenarios. The precise details behind this approach are captured in the following notebooks:

- XGBoost
- LightGBM

It's our hope that this pattern will help customers unlock the full potential of their data.

Learn more about [XGBoost on Databricks](https://docs.databricks.com/en/machine-learning/train-model/xgboost.html)
