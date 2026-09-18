# How (Not) to Tune Your Model With Hyperopt

*Use Hyperopt Optimally With Spark and MLflow to Build Your Best Model*

- Source: https://www.databricks.com/blog/2021/04/15/how-not-to-tune-your-model-with-hyperopt.html
- Published: 2021-04-15
- Authors: Sean Owen
- Categories: engineering, open-source, data-science-machine-learning
- Images: 1 total, 0 extracted as architecture

*Hyperopt is a powerful tool for tuning ML models with Apache Spark. Read on to learn how to define and execute (and debug) the tuning optimally!*

So, you want to build a model. You've solved the harder problems of accessing data, cleaning it and selecting features. Now, you just need to fit a model, and the good news is that there are many open source tools available: [xgboost](https://xgboost.readthedocs.io/en/latest/), [scikit-learn](https://scikit-learn.org/stable/), [Keras](https://keras.io/), and so on. The bad news is *also* that there are so many of them, and that they each have so many knobs to turn. How much regularization do you need? What learning rate? And what is ["gamma"](https://github.com/scikit-learn/scikit-learn/blob/95119c13a/sklearn/svm/_classes.py#L481) anyway?

There is no simple way to know which algorithm, and which settings for that algorithm ("hyperparameters"), produces the best model for the data. Any honest model-fitting process entails trying many combinations of hyperparameters, even many algorithms.

One popular open-source tool for hyperparameter tuning is [Hyperopt](https://github.com/hyperopt/hyperopt). It is simple to use, but using Hyperopt efficiently requires care. Whether you are just getting started with the library, or are already using Hyperopt and have had problems scaling it or getting good results, this blog is for you. It will explore common problems and solutions to ensure you can find the best model without wasting time and money. It will show how to:

- Specify the Hyperopt search space correctly
- Debug common errors
- Utilize parallelism on an Apache Spark cluster optimally
- Optimize execution of Hyperopt trials
- Use MLflow to track models

### What is Hyperopt?

[Hyperopt](https://github.com/hyperopt/hyperopt) is a Python library that can optimize a function's value over complex spaces of inputs. For machine learning specifically, this means it can optimize a model's accuracy (loss, really) over a space of hyperparameters. It's a Bayesian optimizer, meaning it is not merely randomly searching or searching a grid, but intelligently learning which combinations of values work well as it goes, and focusing the search there.

There are many optimization packages out there, but Hyperopt has several things going for it:

- Open source
- Bayesian optimizer - smart searches over hyperparameters (using a [Tree of Parzen Estimators](https://en.wikipedia.org/wiki/Kernel_density_estimation), FWIW), not grid or random search
- Integrates with Apache Spark for [parallel hyperparameter search](http://hyperopt.github.io/hyperopt/scaleout/spark/)
- [Integrates with MLflow](https://docs.databricks.com/applications/machine-learning/automl-hyperparam-tuning/hyperopt-spark-mlflow-integration.html) for automatic tracking of the search results
- Included already in the [Databricks ML runtime](https://docs.databricks.com/release-notes/runtime/8.0ml.html)
- Maximally flexible: can optimize literally any Python model with any hyperparameters

This last point is a double-edged sword. Hyperopt is simple and flexible, but it makes no assumptions about the task and puts the burden of specifying the bounds of the search correctly on the user. Done right, Hyperopt is a powerful way to efficiently find a best model. However, there are a number of best practices to know with Hyperopt for specifying the search, executing it efficiently, debugging problems and obtaining the best model via MLflow.

## Specifying the space: what's a hyperparameter?

When using any tuning framework, it's necessary to specify which hyperparameters to tune. But, what *are* hyperparameters?

They're not the *parameters* of a model, which are learned from the data, like the coefficients in a linear regression, or the weights in a deep learning network. Hyperparameters are inputs to the modeling process itself, which chooses the best parameters. This includes, for example, the strength of regularization in fitting a model. Scalar parameters to a model are probably hyperparameters. Whatever doesn't have an obvious single correct value is fair game.

Some arguments are *not tunable* because there's one correct value. For example, xgboost wants an objective function to minimize. For classification, it's often `reg:logistic`. For regression problems, it's `reg:squarederrorc`. But, these are not alternatives in one problem. It makes no sense to try `reg:squarederror `for classification. Similarly, in generalized linear models, there is often one [link function](https://en.wikipedia.org/wiki/Generalized_linear_model#Link_function) that correctly corresponds to the problem being solved, not a choice. For a simpler example: you don't need to tune `verbose` anywhere!

Some arguments are ambiguous because they are* tunable, but primarily affect speed. *Consider `n_jobs `in scikit-learn implementations . This controls the number of parallel threads used to build the model. It should not affect the final model's quality. It's not something to tune as a hyperparameter.

Similarly, parameters like convergence tolerances aren't likely something to tune. Too large, and the model accuracy *does* suffer, but small values basically just spend more compute cycles. These are the kinds of arguments that can be left at a default.

In the same vein, the number of epochs in a deep learning model is probably not something to tune. Training should stop when accuracy stops improving via early stopping. See "[How (Not) To Scale Deep Learning in 6 Easy Steps](https://www.databricks.com/blog/2019/08/15/how-not-to-scale-deep-learning-in-6-easy-steps.html)" for more discussion of this idea.

## Specifying the space: what range to choose?

Next, what range of values is appropriate for each hyperparameter? Sometimes it's obvious. For example, if choosing [Adam](https://en.wikipedia.org/wiki/Stochastic_gradient_descent#Adam) versus [SGD](https://en.wikipedia.org/wiki/Stochastic_gradient_descent) as the optimizer when training a neural network, then those are clearly the only two possible choices.

For scalar values, it's not as clear. Hyperopt requires a minimum and maximum. In some cases the minimum is clear; a learning rate-like parameter can only be positive. An [Elastic net](https://en.wikipedia.org/wiki/Elastic_net_regularization) parameter is a ratio, so must be between 0 and 1. But what is, say, a reasonable maximum ["gamma"](https://github.com/scikit-learn/scikit-learn/blob/95119c13a/sklearn/svm/_classes.py#L481) parameter in a support vector machine? It's necessary to consult the implementation's documentation to understand hard minimums or maximums and the default value.

If in doubt, choose bounds that are extreme and let Hyperopt learn what values aren't working well. For example, if a regularization parameter is typically between 1 and 10, try values from 0 to 100. The range should include the default value, certainly. At worst, it may spend time trying extreme values that do not work well at all, but it should learn and stop wasting trials on bad values. This may mean subsequently re-running the search with a narrowed range after an initial exploration to better explore reasonable values.

Some hyperparameters have a large impact on runtime. A large [max tree depth](https://xgboost.readthedocs.io/en/latest/parameter.html#parameters-for-tree-booster) in tree-based algorithms can cause it to fit models that are large and expensive to train, for example. Worse, sometimes models take a long time to train because they are overfitting the data! Hyperopt does not try to learn about runtime of trials or factor that into its choice of hyperparameters. If some tasks fail for lack of memory or run very slowly, examine their hyperparameters. Sometimes it will reveal that certain settings are just too expensive to consider.

A final subtlety is the difference between uniform and log-uniform hyperparameter spaces. Hyperopt offers [hp.uniform](https://github.com/hyperopt/hyperopt/wiki/FMin#21-parameter-expressions) and hp.loguniform, both of which produce real values in a min/max range. hp.loguniform is more suitable when one might choose a geometric series of values to try (0.001, 0.01, 0.1) rather than arithmetic (0.1, 0.2, 0.3). Which one is more suitable depends on the context, and typically does not make a large difference, but is worth considering.

To recap, a reasonable workflow with Hyperopt is as follows:

- Choose what hyperparameters are reasonable to optimize
- Define broad ranges for each of the hyperparameters (including the default where applicable)
- Run a small number of trials
- Observe the results in an MLflow parallel coordinate plot and select the runs with lowest loss
- Move the range towards those higher/lower values when the best runs' hyperparameter values are pushed against one end of a range
- Determine whether certain hyperparameter values cause fitting to take a long time (and avoid those values)
- Re-run with more trials
- Repeat until the best runs are comfortably within the given search bounds and none are taking excessive time

## Use hp.quniform for scalars, hp.choice for categoricals

Consider choosing the maximum depth of a tree building process. This must be an *integer* like 3 or 10. Hyperopt offers [hp.choice and hp.randint](https://github.com/hyperopt/hyperopt/wiki/FMin#21-parameter-expressions) to choose an integer from a range, and users commonly choose hp.choice as a sensible-looking range type.

However, these are exactly the wrong choices for such a hyperparameter. While these will generate integers in the right range, in these cases, Hyperopt would not consider that a value of "10" is larger than "5" and much larger than "1", as if scalar values. Yet, that is how a maximum depth parameter behaves. If 1 and 10 are bad choices, and 3 is good, then it should probably prefer to try 2 and 4, but it will not learn that with hp.choice or hp.randint.

Instead, the right choice is hp.quniform ("quantized uniform") or hp.qloguniform to generate integers. hp.choice *is* the right choice when, for example, choosing among categorical choices (which might in some situations even be integers, but not usually).

Here are a few common types of hyperparameters, and a likely Hyperopt range type to choose to describe them:

 

| **Hyperparameter Type** | **Suggested Hyperopt range** |
|---|---|
| Maximum depth, number of trees, max 'bins' in Spark ML decision trees | hp.quniform with min >= 1 |
| Learning rate | hp.loguniform with max = 0 (because exp(0) = 1.0) |
| Regularization strength | hp.uniform with min = 0 or hp.loguniform |
| Ratios or fractions, like Elastic net ratio | hp.uniform with min = 0, max = 1 |
| Shrinkage factors like eta in xgboost | hp.uniform with min = 0, max = 1 |
| Loss criterion in decision trees (ex: gini vs entropy) | hp.choice |
| Activation function (e.g. ReLU vs leaky ReLU) | hp.choice |
| Optimizer (e.g. Adam vs SGD) | hp.choice |
| Neural net layer width, embedding size | hp.quniform with min >>= 1 |

One final caveat: when using hp.choice over, say, two choices like "adam" and "sgd", the value that Hyperopt sends to the function (and which is auto-logged by MLflow) is an integer index like 0 or 1, not a string like "adam". To log the actual value of the choice, it's necessary to consult the list of choices supplied. Example:

 

## "There are no evaluation tasks, cannot return argmin of task losses"

One error that users commonly encounter with Hyperopt is: `There are no evaluation tasks, cannot return argmin of task losses.`

This means that no trial completed successfully. This almost always means that there is a bug in the objective function, and every invocation is resulting in an error. See the error output in the logs for details. In Databricks, the underlying error is surfaced for easier debugging.

It can also arise if the model fitting process is not prepared to deal with missing / NaN values, and is always returning a NaN loss.

Sometimes it's "normal" for the objective function to fail to compute a loss. Sometimes a particular configuration of hyperparameters does not work at all with the training data -- maybe choosing to add a certain exogenous variable in a time series model causes it to fail to fit. It's OK to let the objective function fail in a few cases if that's expected. It's also possible to simply return a very large dummy loss value in these cases to help Hyperopt learn that the hyperparameter combination does not work well.

## Setting SparkTrials parallelism optimally

Hyperopt can parallelize its trials across a Spark cluster, which is a great feature. Building and evaluating a model for each set of hyperparameters is inherently parallelizable, as each trial is independent of the others. Using Spark to execute trials is simply a matter of using "[SparkTrials](https://github.com/hyperopt/hyperopt/blob/master/docs/templates/scaleout/spark.md)" instead of "Trials" in Hyperopt. This is a great idea in environments like Databricks where a Spark cluster is readily available.

SparkTrials takes a `parallelism` parameter, which specifies how many trials are run in parallel. Of course, setting this too low wastes resources. If running on a cluster with 32 cores, then running just 2 trials in parallel leaves 30 cores idle.

Setting parallelism too high can cause a subtler problem. With a 32-core cluster, it's natural to choose parallelism=32 of course, to maximize usage of the cluster's resources. Setting it higher than cluster parallelism is counterproductive, as each wave of trials will see some trials waiting to execute.

However, Hyperopt's tuning process is iterative, so setting it to exactly 32 may not be ideal either. It uses the results of completed trials to compute and try the next-best set of hyperparameters. Consider the case where `max_evals` the total number of trials, is also 32. If parallelism is 32, then all 32 trials would launch at once, with no knowledge of each other’s results. It would effectively be a random search.

`parallelism` should likely be an order of magnitude smaller than `max_evals`. That is, given a target number of total trials, adjust cluster size to match a parallelism that's much smaller. If targeting 200 trials, consider parallelism of 20 and a cluster with about 20 cores.

There's more to this rule of thumb. It's also not effective to have a large parallelism when the number of hyperparameters being tuned is small. For example, if searching over 4 hyperparameters, parallelism should not be much larger than 4. 8 or 16 may be fine, but 64 may not help a lot. With many trials and few hyperparameters to vary, the search becomes more speculative and random. It doesn't hurt, it just may not help much.

Set parallelism to a small multiple of the number of hyperparameters, and allocate cluster resources accordingly. How to choose `max_evals` after that is covered below.

## Leveraging task parallelism optimally

There's a little more to that calculation. Some machine learning libraries can take advantage of multiple threads on one machine. For example, several scikit-learn implementations have an [n_jobs](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestClassifier.html) parameter that sets the number of threads the fitting process can use.

Although a single Spark task is assumed to use one core, nothing stops the task from using multiple cores. For example, with 16 cores available, one can run 16 single-threaded tasks, or 4 tasks that use 4 each. The latter is actually advantageous -- if the fitting process can efficiently use, say, 4 cores. This is because Hyperopt is iterative, and returning fewer results faster improves its ability to learn from early results to schedule the next trials. That is, in this scenario, trials 5-8 could learn from the results of 1-4 if those first 4 tasks used 4 cores each to complete quickly and so on, whereas if all were run at once, none of the trials' hyperparameter choices have the benefit of information from any of the others' results.

How to set `n_jobs` (or the equivalent parameter in other frameworks, like [nthread](https://xgboost.readthedocs.io/en/latest/parameter.html#parameters-for-tree-booster) in xgboost) optimally depends on the framework. scikit-learn and xgboost implementations can typically benefit from several cores, though they see diminishing returns beyond that, but it depends. One solution is simply to set `n_jobs `(or equivalent) higher than 1 without telling Spark that tasks will use more than 1 core. The executor VM may be overcommitted, but will certainly be fully utilized. If not taken to an extreme, this can be close enough.

This affects thinking about the setting of parallelism. If a Hyperopt fitting process can reasonably use parallelism = 8, then by default one would allocate a cluster with 8 cores to execute it. But if the individual tasks can each use 4 cores, then allocating a 4 * 8 = 32-core cluster would be advantageous.

Ideally, it's possible to tell Spark that each task will want 4 cores in this example. This is done by setting [spark.task.cpus](https://spark.apache.org/docs/latest/configuration.html#scheduling). This will help Spark avoid scheduling too many core-hungry tasks on one machine. The disadvantage is that this is a cluster-wide configuration, which will cause all Spark jobs executed in the session to assume 4 cores for any task. This is only reasonable if the tuning job is the only work executing within the session. Simply not setting this value may work out well enough in practice.

## Optimizing Spark-based ML jobs

The examples above have contemplated tuning a modeling job that uses a single-node library like scikit-learn or xgboost. Hyperopt can equally be used to tune modeling jobs that leverage Spark for parallelism, such as those from [Spark ML](https://spark.apache.org/docs/latest/ml-guide.html), [xgboost4j-spark](https://xgboost.readthedocs.io/en/latest/jvm/xgboost4j_spark_tutorial.html), or [Horovod](https://docs.databricks.com/applications/machine-learning/train-model/distributed-training/horovod-runner.html) with Keras or PyTorch.

However, in these cases, the modeling job itself is already getting parallelism from the Spark cluster. Just use Trials, not SparkTrials, with Hyperopt. Jobs will execute serially. Hence, it's important to [tune the Spark-based library's execution](https://docs.databricks.com/applications/machine-learning/automl-hyperparam-tuning/hyperopt-distributed-ml.html) to maximize efficiency; there is no Hyperopt parallelism to tune or worry about.

## Avoid large serialized objects in the objective function

When using SparkTrials, Hyperopt parallelizes execution of the supplied objective function across a Spark cluster. This means the function is magically serialized, like any Spark function, along with any objects the function refers to.

This can be bad if the function references a large object like a large DL model or a huge data set.

Hyperopt has to send the model and data to the executors repeatedly every time the function is invoked. This can dramatically slow down tuning. Instead, it's better to broadcast these, which is a fine idea even if the model or data aren't huge:

However, this will not work if the broadcasted object is more than 2GB in size. It may also be necessary to, for example, convert the data into a form that is serializable (using a NumPy array instead of a pandas DataFrame) to make this pattern work.

If not possible to broadcast, then there's no way around the overhead of loading the model and/or data each time. The objective function has to load these artifacts directly from distributed storage. This works, and at least, the data isn't all being sent from a single driver to each worker.

## Use Early Stopping

Optimizing a model's loss with Hyperopt is an iterative process, just like (for example) training a neural network is. It keeps improving some metric, like the loss of a model. However, at some point the optimization stops making much progress. It's possible that Hyperopt struggles to find a set of hyperparameters that produces a better loss than the best one so far. You may observe that the best loss isn't going down at all towards the end of a tuning process.

It's advantageous to stop running trials if progress has stopped. Hyperopt offers an `early_stop_fn` parameter, which specifies a function that decides when to stop trials before `max_evals` has been reached. Hyperopt provides a function `no_progress_loss`, which can stop iteration if best loss hasn't improved in *n* trials.

## How should I set max_evals?

Below is some general guidance on how to choose a value for `max_evals`

| Parameter Expression | Optimal Results | Fastest Results |
|---|---|---|
| (ordinal parameters) hp.uniform hp.quniform hp.loguniform hp.qloguniform | 20 x # parameters | 10 x # parameters |
| (categorical parameters) hp.choice | 15 x total categorical breadth* |  |

* “total categorical breadth” is the total number of categorical choices in the space.  If you have hp.choice with two options “on, off”, and another with five options “a, b, c, d, e”, your total categorical breadth is 10.

| Modifier | Optimal Results | Fastest Results |
|---|---|---|
| Parallelism | x # of workers | x ½ # of workers |

By adding the two numbers together, you can get a base number to use when thinking about how many evaluations to run, before applying multipliers for things like parallelism.

Example: You have two hp.uniform, one hp.loguniform, and two hp.quniform hyperparameters, as well as three hp.choice parameters. Two of them have 2 choices, and the third has 5 choices.To calculate the range for max_evals, we take 5 x 10-20 = (50, 100) for the ordinal parameters, and then 15 x (2 x 2 x 5) = 300 for the categorical parameters, resulting in a range of 350-450. With no parallelism, we would then choose a number from that range, depending on how you want to trade off between speed (closer to 350), and getting the optimal result (closer to 450). As you might imagine, a value of 400 strikes a balance between the two and is a reasonable choice for most situations. If we wanted to use 8 parallel workers (using SparkTrials), we would multiply these numbers by the appropriate modifier: in this case, 4x for speed and 8x for optimal results, resulting in a range of 1400 to 3600, with 2500 being a reasonable balance between speed and the optimal result.

One final note: when we say “optimal results”, what we mean is confidence of optimal results. It is possible, and even probable, that the fastest value and optimal value will give similar results. However, by specifying and then running more evaluations, we allow Hyperopt to better learn about the hyperparameter space, and we gain higher confidence in the quality of our best seen result.

## Avoid cross validation in the objective function

The objective function optimized by Hyperopt, primarily, returns a loss value. Given hyperparameter values that Hyperopt chooses, the function computes the loss for a model built with those hyperparameters. It returns a dict including the loss value under the key 'loss':

`return {'status': STATUS_OK, 'loss': loss}`

To do this, the function has to split the data into a training and validation set in order to train the model and then evaluate its loss on held-out data. A train-validation split is normal and essential.

It's common in machine learning to perform [k-fold cross-validation](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.KFold.html) when fitting a model. Instead of fitting one model on one train-validation split, *k* models are fit on *k* different splits of the data. This can produce a better estimate of the loss, because many models' loss estimates are averaged.

However, it's worth considering whether cross validation is worthwhile in a hyperparameter tuning task. It improves the accuracy of each loss estimate, and provides information about the certainty of that estimate, but it comes at a price: *k* models are fit, not one. That means each task runs roughly *k* times longer. This time could also have been spent exploring *k* other hyperparameter combinations. That is, increasing `max_evals` by a factor of k is probably better than adding k-fold cross-validation, all else equal.

If k-fold cross validation is performed anyway, it's possible to at least make use of additional information that it provides. With *k* losses, it's possible to estimate the variance of the loss, a measure of uncertainty of its value. This is useful to Hyperopt because it is updating a probability distribution over the loss. To do so, return an estimate of the variance under "loss_variance". Note that the losses returned from cross validation are just an estimate of the true population loss, so return the [Bessel-corrected](https://en.wikipedia.org/wiki/Bessel%27s_correction) estimate:

Note: Some specific model types, like certain time series forecasting models, estimate the variance of the prediction inherently without cross validation. If so, it's useful to return that as above.

## Choosing the Right Loss

An optimization process is only as good as the metric being optimized. Models are evaluated according to the loss returned from the objective function. Sometimes the model provides an obvious loss metric, but that may not accurately describe the model's usefulness to the business.

For example, classifiers are often optimizing a loss function like [cross-entropy loss](https://en.wikipedia.org/wiki/Cross_entropy#Cross-entropy_loss_function_and_logistic_regression). This expresses the model's "incorrectness" but does not take into account which way the model is wrong. Returning "true" when the right answer is "false" is as bad as the reverse in this loss function. However it may be much more important that the model rarely returns false negatives ("false" when the right answer is "true"). [Recall](https://en.wikipedia.org/wiki/Precision_and_recall) captures that more than cross-entropy loss, so it's probably better to optimize for recall. It's reasonable to return recall of a classifier in this case, not its loss. Note that Hyperopt is *minimizing* the returned loss value, whereas higher recall values are better, so it's necessary in a case like this to return `-recall`.

## Retraining the best model

Hyperopt selects the hyperparameters that produce a model with the lowest loss, and nothing more. Because it [integrates with MLflow](https://docs.databricks.com/applications/machine-learning/automl-hyperparam-tuning/hyperopt-spark-mlflow-integration.html), the results of every Hyperopt trial can be automatically logged with no additional code in the Databricks workspace. The results of many trials can then be compared in the MLflow Tracking Server UI to understand the results of the search. Hundreds of runs can be compared in a parallel coordinates plot, for example, to understand which combinations appear to be producing the best loss.

This is useful in the early stages of model optimization where, for example, it's not even so clear what is worth optimizing, or what ranges of values are reasonable.

However, the MLflow integration does not (cannot, actually) automatically log the models fit by each Hyperopt trial. This is not a bad thing. It may not be desirable to spend time saving every single model when only the best one would possibly be useful.

It is possible to manually log each model from within the function if desired; simply call MLflow APIs to add this or anything else to the auto-logged information. For example:

 

Although up for debate, it's reasonable to instead take the optimal hyperparameters determined by Hyperopt and re-fit one final model on *all* of the data, and log it with MLflow. While the hyperparameter tuning process had to restrict training to a train set, it's no longer necessary to fit the final model on just the training set. With the 'best' hyperparameters, a model fit on all the data might yield slightly better *parameters*. The disadvantage is that the generalization error of this final model can't be evaluated, although there is reason to believe that was well estimated by Hyperopt. A sketch of how to tune, and then refit and log a model, follows:

## More best practices

If you're interested in more tips and best practices, see additional resources:

- [Hyperopt best practices documentation from Databricks](https://docs.databricks.com/applications/machine-learning/automl-hyperparam-tuning/hyperopt-best-practices.html)
- [Best Practices for Hyperparameter Tuning with MLflow](https://www.databricks.com/session/best-practices-for-hyperparameter-tuning-with-mlflow) (talk) - SAIS 2019
- [Advanced Hyperparameter Optimization for Deep Learning with MLflow](https://www.databricks.com/session/advanced-hyperparameter-optimization-for-deep-learning-with-mlflow) (talk) - SAIS 2019
- [Scaling Hyperopt to Tune Machine Learning Models in Python](https://www.databricks.com/blog/2019/10/29/scaling-hyperopt-to-tune-machine-learning-models-in-python.html) - blog - 2019-10-29

## Conclusion

This blog covered best practices for using Hyperopt to automatically select the best machine learning model, as well as common problems and issues in specifying the search correctly and executing its search efficiently. It covered best practices for distributed execution on a Spark cluster and debugging failures, as well as integration with MLflow.

With these best practices in hand, you can leverage Hyperopt's simplicity to quickly integrate efficient model selection into any machine learning pipeline.

## Get started

Use [Hyperopt on Databricks](https://docs.databricks.com/applications/machine-learning/automl-hyperparam-tuning/hyperopt-best-practices.html) (with Spark and MLflow) to build your best model!
