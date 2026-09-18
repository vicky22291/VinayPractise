# On-Demand Webinar and FAQ: Apache Spark MLlib 2.x: How to Productionize your Machine Learning Models

- Source: https://www.databricks.com/blog/2017/03/28/demand-webinar-faq-apache-spark-mllib-2-x-productionize-machine-learning-models.html
- Published: 2017-03-28
- Authors: Richard Garris, Jules Damji
- Categories: engineering, data-science-machine-learning, open-source
- Images: 0 total, 0 extracted as architecture

On March 9th, we hosted a live webinar—[Apache Spark MLlib 2.x: How to Productionize your Machine Learning Models](https://www.databricks.com/)—to address the following questions:

1. How do you deploy machine learning models to a production environment?
2. How do you embed what you've learned into customer facing data applications?
3. What are the best practices from Databricks on how customers productionize machine learning models?

To address the above concerns, we did a deep dive with actual customer case studies and showed live tutorials of a few example architectures and code in Python, Scala, Java and SQL.

If you missed the webinar, you can view it on-demand [here](https://www.databricks.com/), and the [slides](https://www.slideshare.net/julesdamji/apache-spark-mllib-2x-how-to-productionize-your-machine-learning-models) and [notebook](https://databricks-prod-cloudfront.cloud.databricks.com/public/4027ec902e239c93eaaa8714f173bcfc/1526931011080774/1904316851197504/6320440561800420/latest.html) are accessible as attachments to the webinar.

Toward the end, we did a Q&A, and below are all the questions with links to forums with their answers. (Follow the links below to view the answers.)

- [I thought that Machine Learning (ML) is an upgrade from MLlib. Is MLlib 2.x more update to date than ML?](https://community.databricks.com/s/#answer-11154)
- [PipelineModel instances all have Dataset objects as input and output, and creating a Dataset requires having a SparkSession active. (Right?) If I have a mainframe deployment environment where I just want to give it a single record and get a single record back, what are my options?](https://community.databricks.com/s/#answer-11157)
- [Most of the models in MLlib support PMML export. What was the motivation for developing a proprietary real-time scoring model export?](https://community.databricks.com/s/#answer-11159)
- [I assume this is a proprietary format for exporting the model. Why not use an open standard like pmml?](https://community.databricks.com/s/#answer-11161)
- [Are there any MLlib standard implementations of clustering algorithms other than k-means?](https://community.databricks.com/s/)
- [It seems like one might want to use similar DevOPs CD/CI techniques and apply to ML and model development. How do you see the flow and what products would help (e.g. like a Jenkins product, a build tool...?) to use with DevOps CD/CI scenario?](https://community.databricks.com/s/#answer-11166)
- [What common APIs have you seen that are used for scoring an Apache Spark ALS model in real-time?](https://community.databricks.com/s/#answer-11168)
- 1) [Why does the Spark model scoring (e.g decision tree ) make it hard or impossible to get a probability and easy to get a prediction (which is not very useful). 2) How can you export a model in a readable form (e.g. PMML) or generate code?](https://community.databricks.com/s/#answer-11171)
- [Is this databricks library compatible with the dataset-based SparkML (as opposed to MLlib)?](https://community.databricks.com/s/#answer-11173)
- [Can you give some prediction when RandomForest will become available in dbml-local?](https://community.databricks.com/s/#answer-11176)
- [Seems like we should be able to make an AWS Lambda microservice that picks up the trained model from S3, and uses the dbml-local library to make the predictions?](https://community.databricks.com/s/#answer-11178)
- [Can you give an example use case where a customer needed to train a model on Apache Spark, but deploy on an external system? How common is that?](https://community.databricks.com/s/#answer-11180)
- [We've been waiting for dbml-local for a long time! Great addition! When do you expect all classifiers in spark to be available in dbml-local?](https://community.databricks.com/s/#answer-11182)
- [Are all the spark mllib models available to use with dbml-local?](https://community.databricks.com/s/#answer-11184)
- [Is there support to export the model as a pojo object?](https://community.databricks.com/s/#answer-11187)
- [Is there any plan to implement k-mediods in Apache Spark](https://community.databricks.com/s/#answer-11190)
- [Are you planning to provide dbml outside of databricks? 2. how does dbml relate to tensorframes?](https://community.databricks.com/s/#answer-11193)
- [Can you comment on DataFrame model and MLlib for production?](https://community.databricks.com/s/#answer-11196)
- [Do you support other data formats such as netCDF?](https://community.databricks.com/s/#answer-11199)
- [Will scoring consider ML pipeline activities like feature extraction?](https://community.databricks.com/s/#answer-11201)
- [Is there any plan to publish rest APIs in Apache Spark itself to submit spark jobs?](https://community.databricks.com/s/#answer-11204)
- [Will the exportModel functionality available to other language like python or R?](https://community.databricks.com/s/#answer-11206)
- [In the decision tree visualization, can the real feature names (instead of feature 1, 2, 3, etc.) be displayed in the visualization?](https://community.databricks.com/s/#answer-11208)
- [As of now there is support only for logistics regression model to be used outside of Apache Spark?](https://community.databricks.com/s/#answer-11210)
- [What were the pros and cons of the 3 different schemes that you presented to productionalize ML models? Why specifically demonstrate the third option?](https://community.databricks.com/s/#answer-11212)
- [Do you plan to support other ML libraries in addition to MLlib?](https://community.databricks.com/s/#answer-11214)
- [Don't you think PMML is the standard for exchange format for predictive models?](https://community.databricks.com/s/#answer-11217)
- [Is dbml library available for community?](https://community.databricks.com/s/#answer-11219)
- [Could you please clarify what this model score option (private beta?) is? Is that available to all paying customers? If we do not use that, I'd like to know what we have to do achieve the same thing with Databricks, Apache  Spark and MLlib.](https://community.databricks.com/s/#answer-11221)
- [For raw input, how features are being computed that are being passed to model which you showed in eclipse?](https://community.databricks.com/s/#answer-11223)
- [How do you compare the quality and efficiency between spark ML 2.1 and scikit-learn?](https://community.databricks.com/s/#answer-11225)
- [Where can you obtain dbml-local jar? Only available to Databricks customers?](https://community.databricks.com/s/#answer-11227)
- [Today, some productionized machine learning models are updated each days. Do you have you a solution to obtain the optimized parameters model ? (RandomSearchCrossValidation, but it takes a certain time on a large and distributed configuration..)](https://community.databricks.com/s/#answer-11230)
- [What if we build a modeling technology of our own ? (creating a modeling class, based on Scala or Python libraries of our own), how would we ensure this could be deployed using the same approach you've shown?](https://community.databricks.com/s/#answer-11234)
- [I have found spark.ml gradient boosted trees to be slower than other packages, such as h2o sparkling water. Is there any focus on increasing the performance of the gradient boosted trees or better incorporating another package such as h2o sparkling water or xgboost4j?](https://community.databricks.com/s/#answer-11239)
- [Can you talk about how you would replicate the Spark training pipeline (string indexing, vector assembling, etc) in this application?](https://community.databricks.com/s/#answer-11241)
- [How would an ensemble of models run using this new scoring approach? By creating and saving an ensemble pipeline?](https://community.databricks.com/s/#answer-11243)
- [What is the best way to deploy a predictive model or recommendation engine if the scoring environment is on an IOS app?](https://community.databricks.com/s/#answer-11245)
- [dbml-local looks very much like mleap open-source project. Isn't it better for DB to contribute to that?](https://community.databricks.com/s/#answer-11247)
- [Can Spark MLlib (or dbml-local) somehow read scikit-learn's model file?](https://community.databricks.com/s/#answer-11249)
- [From performance perspective, have you done any performance comparison between spark.ml and sklearn (same algorithm and parameter)? And is there a list of algorithms that will run really well on Apache Spark?](https://community.databricks.com/s/#answer-11251)
- [When using or doing the 'local model' option, calculating 100 features has overhead- is precomputing always necessary?](https://community.databricks.com/s/#answer-11253)
- [Where can I find more information on dbml-local? Can't find it on your GitHub and not getting many results when searching on google.](https://community.databricks.com/s/#answer-11255)
- [Can you talk about the option to save as PMML?](https://community.databricks.com/s/#answer-11275)

If you'd like free access to Databricks, you can access the [free trial here](https://www.databricks.com/try-databricks).
