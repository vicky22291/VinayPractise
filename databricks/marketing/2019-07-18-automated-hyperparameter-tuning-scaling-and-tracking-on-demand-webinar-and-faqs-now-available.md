# Automated Hyperparameter Tuning, Scaling and Tracking: On-Demand Webinar and FAQs now available!

- Source: https://www.databricks.com/blog/2019/07/18/automated-hyperparameter-tuning-scaling-and-tracking-on-demand-webinar-and-faqs-now-available.html
- Published: 2019-07-18
- Authors: Joseph Bradley, Yifan Cao, Cyrielle Simeone
- Categories: solutions, engineering, data-science-machine-learning
- Images: 1 total, 0 extracted as architecture

*Free Edition has replaced Community Edition, offering enhanced features at no cost. Start using *[*Free Edition *](https://login.databricks.com/?intent=SIGN_UP&amp;signup_experience_step=EXPRESS&amp;provider=DB_FREE_TIER&amp;dbx_source=www)*today.*
 

[Try this notebook in Databricks](https://info.databricks.com/ThCYW0v0a000jMO00h4CoS0)

On June 20th, our team hosted a live webinar—[Automated Hyperparameter Tuning, Scaling and Tracking on Databricks](https://pages.databricks.com/201906-WB-AutomatedHyperparameterTuning_Reg.html)—with Joseph Bradley,  Software Engineer, and Yifan Cao, Senior Product Manager at Databricks.

Automated Machine Learning (AutoML) has received significant interest recently because of its ability to shorten time-to-value for data science teams and maximize the predictive performance of models. However, getting to this ideal state can be a complex and resource-intensive process.

In this webinar, we covered:

- The landscape of AutoML offerings available on Databricks
- The most popular techniques for hyperparameter tuning as well as open source tools that implement each of these techniques.
- The improvements we built for these tools in Databricks, including integration with MLflow, specifically for Apache PySpark MLlib and Hyperopt.

We demonstrated these concepts using these notebooks and tutorials:

- [Notebook: Distributed Hyperopt + Automated MLflow Tracking](https://info.databricks.com/ThCYW0v0a000jMO00h4CoS0)
- [Notebook: MLlib + Automated MLflow Tracking](https://info.databricks.com/I0a0PYj0h4viCo0C0W0MS00)

If you’d like free access to the [Databricks Unified Analytics Platform](https://www.databricks.com/product/data-lakehouse) and try our notebooks on it, you can access a [free trial here](https://www.databricks.com/try-databricks).

Toward the end, we held a Q&A and below are the questions and answers.

**Q: Is there any cloud platform available for our experimentation? If so, how do we get access?**

Databricks AutoML features are available in both Azure Databricks and AWS. To get started, please follow our instructions to sign up for a [free trial](https://www.databricks.com/try-databricks).

**Q: How much of accuracy benefit should we expect from hyperparameter tuning?**

The accuracy benefit from performing hyperparameter tuning depends on the model, hyperparameters, and other factors. You can expect to see the largest gains from initial hyperparameter tuning, with diminishing returns as you spend more time tuning. E.g., the jump in accuracy from running Hyperopt with max_eval=50 will likely be much larger than the jump you would see in increasing max_eval from 50 to 100.

**Q: Can Hyperopt be applied to scikit-learn, TensorFlow?**

Yes. Our Distributed Hyperopt + MLflow feature applies to single-node machine learning training code and is agnostic to the underlying ML library. Hyperopt can take in a user function containing single-machine scikit-learn, TensorFlow, or other ML code. Note that, for distributed machine learning training, please consider using Apache Spark MLlib, which is automatically tracked in MLflow in Databricks.

**Q: What exactly was being open sourced?**

We are in the middle of open-sourcing distributed Hyperopt using Apache Spark via “SparkTrials.” Automated tracking to MLflow remains a Databricks-specific feature.

**Q: Can you elaborate more what conditional hyperparameter tuning is? How is it going to help with model search?**

Conditional hyperparameter tuning refers to tuning in which the search for some hyperparameters depends on the values of other hyperparameters.  For example, when tuning regularization for a linear model, one might search over one range of the regularization parameter “lambda” for L2 regularization but a different range of “lambda” for L1 regularization.  This technique helps with model search since different models have different hyperparameters. For instance, for a classification problem you may consider choosing between logistic regression or random forests. In the same Hyperopt search, you could test both algorithms, searching over different hyperparameters associated with each algorithm, for example regularization for logistic regression and the number of trees for random forests.

**Q: Does MLflow automatically choose the best model and make it as parent run and other runs as child?**

Our integrations of MLflow with MLlib and Hyperopt automatically choose the best model and structure runs with the parent-child hierarchy.  To be very clear, there are 2 parts to this integration which handle different aspects: (a) MLflow is being used simply for logging and tracking, whereas (b) MLlib and Hyperopt contain the tuning logic which chooses the best model.  Therefore, it is MLlib and Hyperopt which compare models, select a best model, and decide how to track models as MLflow runs.

**Q: Can I set a scheduled learning rate that slows down/changes as a hyperparameter?**

Yes, but the logic for slowing down would need to be in your custom ML code.  Some Deep Learning libraries support shrinking learning rates: e.g., [https://www.tensorflow.org/api_docs/python/tf/compat/v1/train/exponential_decay](https://www.tensorflow.org/api_docs/python/tf/compat/v1/train/exponential_decay).

**Q: Can we see the features that are all used for the model in MLflow Tracking UI?**

The features will not be logged by default, but you could add custom MLflow logging code to log feature names.  To do that, we recommend logging feature names under the main run for tuning. If the features are logged as a long list of names, it will be best to log them as an MLflow tag or artifact since those support larger/longer values than MLflow params in Databricks.

**Q: Is MLflow capable of handling automated feature engineering?**

You can easily install third-party libraries such as Featuretools to automatically feature engineering, and log the generated features to MLflow

**Q: How does MLflow help while performing Transfer Learning?**

There are many types of Transfer Learning, so it’s hard to give a single answer.  The most relevant type of Transfer Learning for this webinar topic is using the results from tuning hyperparameters for one model to warmstart tuning for another model.  MLflow can help with this by providing a knowledge repository for understanding past hyperparameters and performance, helping a user to select reasonable hyperparameters and ranges to search over in the future.  This application of past results to new tuning runs must be done manually currently.

**Q: Are these features available in the Community Edition?**

Not at the moment.

**Q: Is MLflow automated tracking available in Scala?**

Not at the moment. We will add it if there is enough customer demand.

**Additional resources:**

Documentation:

- [Hyperparameter Tuning Documentation](https://info.databricks.com/P000C0oYhM0vQ40W0jjSaC0)
- [MLflow integrations with H20.ai GPyOpt, HyperOpt](https://info.databricks.com/CMv00k0Rh0WY0Coj0C0aS04)

Blog:

- [Hyperparameter Tuning with MLflow, Apache Spark MLlib and Hyperopt](https://info.databricks.com/c0400CvY0hCM0aoSl0jSW00)

Videos:

- [Automating Predictive Modeling at Zynga with PySpark and Pandas UDFs](https://info.databricks.com/Q0WS0jM0YT0hC0Cao00m4v0)
- [Advanced Hyperparameter Optimization for Deep Learning with MLflow](https://info.databricks.com/SM0S0o0jh040CYv0a00WCnU)

*To get started with MLflow, follow the instructions at *[*mlflow.org*](https://www.mlflow.org/)* or check out the release code on *[*Github*](https://github.com/databricks/mlflow)*. We’ve also recently created a *[*Slack channel*](https://mlflow-users.slack.com/join/shared_invite/enQtMzkxMTAwNTcyODM5LTNkNTc5YWZlNDNjMzZiYWJhOTQwMjYwYWE3NDU2YTgzMDViYjJhNWI1MGI4NjViNTA0M2FhMzNhZTVkODE2NmU)* for MLflow as well for real time questions, and you can follow *[*@MLflow*](https://twitter.com/MLflow)* on Twitter. We are excited to hear your feedback on the concepts and code!*
