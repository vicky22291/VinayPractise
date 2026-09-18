# Intel’s BigDL on Databricks

- Source: https://www.databricks.com/blog/2017/02/09/intels-bigdl-databricks.html
- Published: 2017-02-09
- Authors: Sue Ann Hong, Joseph Bradley
- Categories: engineering, open-source, data-science-machine-learning
- Images: 1 total, 0 extracted as architecture

*Free Edition has replaced Community Edition, offering enhanced features at no cost. Start using *[*Free Edition *](https://login.databricks.com/?intent=SIGN_UP&amp;signup_experience_step=EXPRESS&amp;provider=DB_FREE_TIER&amp;dbx_source=www)*today.*
 

[Try this notebook on Databricks](https://databricks-prod-cloudfront.cloud.databricks.com/public/4027ec902e239c93eaaa8714f173bcfc/5669198905533692/2626293254583012/3983381308530741/latest.html)

Intel recently released its [BigDL project](https://www.intel.com/content/www/us/en/developer/articles/technical/bigdl-distributed-deep-learning-on-apache-spark.html) for distributed deep learning on Apache Spark. BigDL has native Spark integration, allowing it to leverage Spark during model training, prediction, and tuning. This blog post gives highlights of BigDL and a tutorial showing how to get started with BigDL on Databricks.

## Intel’s BigDL project

BigDL is an open source deep learning library from Intel. Modeled after Torch, BigDL provides functionality both for low-level numeric computing and high-level neural networks. BigDL is written on top of Apache Spark, allowing easy scale-out computing.

### Native Apache Spark integration

BigDL’s native Spark integration separates BigDL from many other deep learning projects. All major deep learning libraries can be integrated with Spark (see [our previous blog post](https://www.databricks.com/blog/2016/12/21/deep-learning-on-databricks.html)), but many libraries are best integrated by running the libraries separately on each Spark worker. This setup makes it easy to use Spark to distribute certain tasks, such as prediction and model tuning, but harder to distribute model training.

Since BigDL is built on top of Spark, it makes it easy to distribute model training, one of the most computationally intensive parts of deep learning. The user does not have to handle distributing computation explicitly. Instead, BigDL automatically spreads the work across a Spark cluster.

### Leveraging recent CPU architectures

Compared with other deep learning frameworks running on CPUs, BigDL also achieves speedups by leveraging the latest Intel architecture. In particular, it ships with the Intel Math Kernel Library (MKL), which can accelerate the heavy numerical computations required for deep learning. Check out [Intel’s BigDL article](https://www.intel.com/content/www/us/en/developer/articles/technical/bigdl-distributed-deep-learning-on-apache-spark.html) and the [BigDL GitHub page](https://github.com/intel-analytics/BigDL) for details.

## Tutorial: using BigDL on Databricks

In the rest of this blog post, we will walk through an example of training a deep neural network using BigDL on Databricks. Our application is a classic handwritten digit recognition problem using the MNIST dataset.

Given a dataset of handwritten digits, plus the true labels (0-9), we will use BigDL to train the [LeNet 5 network model](http://yann.lecun.com/exdb/lenet/). Our trained model will be able to take new images and infer their digits. This blog post gives a high-level description of the workflow, and you can check out the companion [Databricks notebook](https://databricks-prod-cloudfront.cloud.databricks.com/public/4027ec902e239c93eaaa8714f173bcfc/5669198905533692/2626293254583012/3983381308530741/latest.html) for the full details. The material largely comes from [this BigDL tutorial](https://github.com/intel-analytics/BigDL/wiki/).

### Set up a Spark cluster

To set up BigDL on a Spark cluster, you will need to:

- Build BigDL
- Create and configure your cluster --- This is a critical step in getting the best performance from BigDL.
- Import BigDL and attach the library to your cluster

Refer to the [companion notebook](https://databricks-prod-cloudfront.cloud.databricks.com/public/4027ec902e239c93eaaa8714f173bcfc/5669198905533692/2626293254583012/3983381308530741/latest.html) for details on building BigDL and configuring your cluster.

### Initialize BigDL

BigDL takes some special configurations telling it the dimensions of your Spark cluster. Given these dimensions, BigDL will figure out how to split tasks across the workers. Key configurations include:

- `nodeNumber`: the number of Spark executor nodes
- `coreNumber`: the number of cores per executor node
- `batchSize`: the number of data rows to be processed per iteration

Look at the `Engine.init` call in the [companion notebook](https://databricks-prod-cloudfront.cloud.databricks.com/public/4027ec902e239c93eaaa8714f173bcfc/5669198905533692/2626293254583012/3983381308530741/latest.html) to see how initialization is done.

### Download and prepare the MNIST data

To help you get started, we provide a script for downloading the MNIST byte data files, as well as methods for loading those byte files. Finally, we use those images to load our training and validation sets. For example, the snippet below loads the raw byte data, converts it to grayscale images, normalizes the image features, and groups the images into batches for training.

### Train the model

With the data loaded, we can now train our LeNet model to learn the network parameters. BigDL is using Stochastic Gradient Descent (SGD) for learning, so key learning parameters to tweak are:

- `learningRate`: “speed” at which to learn, where smaller values help avoid local optima but larger values produce more progress on each iteration
- `maxEpoch`: max number of outermost epochs, or iterations, for training

We create an initial model using the provided LeNet 5 network structure, specifying that we are predicting 10 classes (digits 0-9):

We next specify the optimizer, which includes the learning criterion we want to optimize. In this case, we minimize the class negative log likelihood criterion.

Finally, we specify a validation criterion (`Top1Accuracy`) for tracking accuracy on our test set, as well as a termination criterion (`Trigger.maxEpoch`) for deciding when to stop training. We call `optimize()`, and BigDL starts training!

### Make predictions and evaluate

With our `trainedModel`, we can now make predictions and evaluate accuracy on new data. BigDL provides a set of evaluation metrics via Validator and ValidationMethod classes.

Inspecting `result`, we can see that our model achieved about 99% accuracy, making correct predictions on 9884 out of 10,000 validation examples.

## Next steps

We have given a quick overview of BigDL and how to get started. To learn more about BigDL, we recommend checking out the [BigDL GitHub page](https://github.com/intel-analytics/BigDL) and the [BigDL talk](https://www.databricks.com/dataaisummit) at Spark Summit Boston 2017 (to be posted online at this link soon after the summit).

To get started with BigDL in Databricks, try out the [companion notebook](https://databricks-prod-cloudfront.cloud.databricks.com/public/4027ec902e239c93eaaa8714f173bcfc/5669198905533692/2626293254583012/3983381308530741/latest.html) for free on [Databricks Community Edition](https://www.databricks.com/try-databricks). The notebook provides a much more detailed walkthrough. Try tuning the model or learning settings to achieve even higher accuracy!
