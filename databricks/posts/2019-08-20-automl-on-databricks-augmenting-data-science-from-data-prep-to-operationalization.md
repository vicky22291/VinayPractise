# AutoML on Databricks: Augmenting Data Science from Data Prep to Operationalization

- Source: https://www.databricks.com/blog/2019/08/20/automl-on-databricks-augmenting-data-science-from-data-prep-to-operationalization.html
- Published: 2019-08-20
- Authors: Clemens Mewald
- Categories: product, announcements, engineering, data-science-machine-learning, company
- Images: 0 total, 0 extracted as architecture

Thousands of data science jobs are going unfilled today as global demand for the talent greatly outstrips supply. Every day, businesses pay the price of the data scientist shortage in missed opportunities and slow innovation. For organizations to realize the full potential of machine learning, data teams have to build hundreds of predictive models a year. For most enterprises, only a fraction of that number is actually achieved due to understaffed data science teams.

Databricks can help data science teams be more productive by automating various steps of the data science workflow  – including feature engineering, hyperparameter tuning, model search, and deployment – for a fully controlled and transparent augmented ML experience. This goes well beyond just automated model search, which is commonly referred to as AutoML.

Today's blog summarizes new and existing capabilities available on the Unified Analytics Platform enabling all levels of expertise, specifically:

1. AutoML Toolkit: Automating end-to-end machine learning pipelines, including feature engineering, model search, and deployment is available via Databricks Labs custom solutions for citizen and expert data scientists. AutoML Toolkit executions are automatically tracked in MLflow.
2. HyperOpt, MLlib, and MLflow integration in the Databricks Runtime for ML: Data scientists looking to automate hyperparameter tuning or model search can now benefit from deeper integrations between Hyperopt, MLlib, and MLflow as part of the Databricks Runtime for ML. This integration enables simplified distributed conditional hyperparameter tuning, automated tracking, and enhanced visualizations.
3. Custom AutoML Solutions: Databricks' Unified Analytics Platform provides data engineers and data scientists the ability to run all analytics processes in one place, from ETL to model building and inference. Deep integrations and optimizations with the most popular open source libraries provide expert data scientists and ML engineers the flexibility and control they need to run end to end ML pipelines, and automate chosen steps with production jobs on Databricks.
4. Integration with Azure Machine Learning:  Building upon the open source MLflow collaboration between Databricks and Microsoft announced in April, this integration allows customers access to the automated machine learning capabilities offered by Azure Machine Learning.  See this [article](https://docs.microsoft.com/en-us/azure/machine-learning/how-to-configure-environment#azure-databricks) to learn more.

## From Feature Factory to Deployment with AutoML Toolkit

[Databricks Labs](https://github.com/databrickslabs/) is a collection of projects created by engineers in the field to solve problems we see over and over again with our customers. With the [AutoML Toolkit](https://github.com/databrickslabs/automl-toolkit), the goal is to automate the building of ML pipelines from feature transformations to hyperparameter tuning, model search, and finally inference while still providing fine grain control in the process.

This Databricks Labs project is an experimental end-to-end supervised learning solution for automating:

- Feature clean-up
- Feature vectorization
- Model selection and training
- Hyper parameter optimization and selection
- Batch Prediction
- Logging of model results and training runs (using [MLflow](https://mlflow.org/))

This solution can be implemented with no-code or fine tuned by experts as they see fit.

## Simplified Distributed Hyperparameter Tuning and Model Search with Hyperopt and MLflow in the Databricks Runtime for ML

Data scientists looking at accelerating their workflows can also benefit from deeper integrations between Hyperopt, MLlib, and MLflow in the [Databricks Runtime for ML](https://www.databricks.com/product/machine-learning-runtime) for optimized and distributed hyperparameter and model search.

- Automated Model Search: Optimized and distributed conditional hyperparameter search with enhanced Hyperopt and automated tracking to MLflow.
- Automated Hyperparameter Tuning: Optimized and distributed hyperparameter search with enhanced Hyperopt and automated tracking to MLflow. Deep integration with PySpark MLlib's Cross Validation allows to automatically track MLlib experiments in MLflow.

See for example how to track the results from hyperparameter tuning at scale on Databricks with enhanced Hyperopt and MLflow integration:

https://www.youtube.com/watch?v=b2KxgBjpe8M

Here are some additional resources to learn more:

- [Hyperparameter Tuning with MLflow, Apache Spark MLlib and Hyperopt Blog](https://info.databricks.com/c0400CvY0hCM0aoSl0jSW00)
- [Automated Hyperparameter Tuning, Scaling and Tracking: On-Demand Webinar and FAQs now available!](https://www.databricks.com/blog/2019/07/18/automated-hyperparameter-tuning-scaling-and-tracking-on-demand-webinar-and-faqs-now-available.html)
- [Hyperparameter Tuning Documentation](https://info.databricks.com/P000C0oYhM0vQ40W0jjSaC0?_ga=2.45558829.862635893.1565129007-1060340547.1550816532&_gac=1.242426294.1564706994.EAIaIQobChMIvO6H4vvi4wIVLR6tBh1ngw5yEAAYASAAEgLIQPD_BwE)
- [Distributed Hyperopt + Automated MLflow Tracking Notebook](https://docs.databricks.com/_static/notebooks/hyperopt-spark-mlflow.html)
- [MLlib + Automated MLflow Tracking Notebook](https://docs.databricks.com/applications/machine-learning/automl-hyperparam-tuning/mllib-mlflow-integration.html)

## Full Flexibility & Performance for Custom AutoML Solutions

More advanced users also have the ability to run all AutoML steps on Databricks, from ETL to model training and inference, by leveraging the extensibility and built-in optimizations of the Unified Analytics Platform with popular open source libraries.

The Databricks Runtime for ML also provides a reliable and secure distribution of the most popular open source ML frameworks (e.g. TensorFlow, Keras, PyTorch, XGBoost, scikit-learn,...) with out of the box optimizations and integrations with Horovod for distributed deep learning as well as [MLflow](https://www.databricks.com/product/managed-mlflow) for built-in experiment and visualization tracking for hyperparameter tuning.

Below are additional resources to dive deeper:

- [Advanced Hyperparameter Optimization for Deep Learning with MLflow](https://info.databricks.com/SM0S0o0jh040CYv0a00WCnU)
- [MLflow integrations with H20.ai GPyOpt, HyperOpt](https://info.databricks.com/CMv00k0Rh0WY0Coj0C0aS04)

Watch [Automating Predictive Modeling at Zynga with Pandas UDFs](https://www.databricks.com/session/automating-predictive-modeling-at-zynga-with-pyspark-and-pandas-udfs) for an example of a custom-based solution running on Databricks.

## Next Step

Visit [https://www.databricks.com/product/automl](https://www.databricks.com/product/automl) to learn more and start a free trial of Databricks.
