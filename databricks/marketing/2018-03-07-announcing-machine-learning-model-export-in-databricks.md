# Announcing Machine Learning Model Export in Databricks

- Source: https://www.databricks.com/blog/2018/03/07/announcing-machine-learning-model-export-in-databricks.html
- Published: 2018-03-07
- Authors: Wayne Chan
- Categories: company, product, engineering, data-science-machine-learning, announcements, platform, open-source
- Images: 0 total, 0 extracted as architecture

In recent years, machine learning has become ubiquitous in industry and production environments. Both academic and industry institutions had previously focused on training and producing models, but the focus has shifted to productionizing the trained models. Now we hear more and more machine learning practitioners really trying to find the right model deployment options.

In most scenarios, deployment means shipping the trained models to some system that makes predictions based on unseen real-time or batch data, and serving those predictions to some end user, again in real-time or in batches.

This is easier said than done. There are a number of challenges that organizations face deploy these models:

- **Upfront Complexity** - Deploying a model into production can require a lot of upfront work that can slow down the deployment process by weeks or more.
- **Disjointed Teams** - Sharing models across teams for training and deployment can create challenges as teams try to deal with persistence formats, library dependencies, and different deployment environments.
- **Featurization Logic** - There is almost always data processing and featurization logic that proceeds the model application step which adds yet another thing to be implemented in deploying a model.
- **Inconsistent Deployment Environments** - Different deployment systems for different scenarios can cause machine learning prediction logic to behave differently, giving subtly incorrect results.

### **Introducing Machine Learning Export**

We are happy to announce the general availability of a powerful new feature called Databricks ML Model Export. This Databricks feature furthers our efforts to unify analytics across data engineering and data science by allowing you to export models and full machine learning pipelines from Apache Spark MLlib. These exported models and pipelines can be imported into other (Spark and non-Spark) platforms to do scoring and make predictions.

This new capability serves as an alternative to batch and streaming prediction within Spark, allowing companies to build low-latency and lightweight machine learning-powered applications with ease.

### **Seamless Deployment of Models**

When speaking with customers, one of the consistent pieces of feedback was that they love to do data science in our platform, but then they have to re-implement the code in a different system to deploy into production. With this new export feature, Databricks can truly serve as an end-to-end platform to build, train, and deploy machine learning models into production with blazing speed and higher reliability.

### **More Information**

To learn more about how to get started with Databricks Machine Learning Export as well as other relevant information, check out the following resources:

- [Documentation](https://docs.databricks.com/applications/machine-learning/index.html#databricks-ml-model-export)
- [On-Demand Webinar: Productionizing Apache Spark MLlib Models for Real-time Prediction Serving](https://pages.databricks.com/Reg-Real-time-Prediction-Serving.html) - presented by Joseph Bradley and Sue Ann Hong.

Also, look out for a follow on blog that will dive deeper into the inner workings of this new feature.
