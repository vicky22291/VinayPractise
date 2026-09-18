# Deep Learning Tutorial Demonstrates How to Simplify Distributed Deep Learning Model Inference Using Delta Lake and Apache Spark™

- Source: https://www.databricks.com/blog/2019/11/21/simplifying-distributed-deep-learning-model-inference-webinar.html
- Published: 2019-11-21
- Authors: Cyrielle Simeone
- Categories: platform, solutions, product, engineering, data-science-machine-learning
- Images: 1 total, 0 extracted as architecture

On October 10th, our team hosted a live webinar—[Simple Distributed Deep Learning Model Inference](https://www.databricks.com/discover/simple-distributed-deep-learning-model-inference)—with Xiangrui Meng, Software Engineer at Databricks.

Model inference, unlike model training, is usually embarrassingly parallel and hence simple to distribute. However, in practice, complex data scenarios and compute infrastructure often make this "simple" task hard to do from data source to sink.

In this webinar, we provided a reference end-to-end pipeline for distributed deep learning model inference using the latest features from [Apache Spark](https://www.databricks.com/spark/about) and [Delta Lake](https://www.databricks.com/product/delta-lake-on-databricks). While the reference pipeline applies to various deep learning scenarios, we focused on image applications, and demonstrated specific pain points and proposed solutions.

The walkthrough starts from [data ingestion and ETL](https://www.databricks.com/glossary/extract-transform-load), using binary file data source from Apache Spark to load and store raw image files into a Delta Lake table. A small code change then enables Spark structure streaming to continuously discover and import new images, keeping the table up-to-date. From the Delta Lake table, [Pandas UDF](https://docs.databricks.com/spark/latest/spark-sql/udf-python-pandas.html) is used to wrap single-node code and perform distributed model inference in Spark.

We demonstrated these concepts using these [Simple Distributed Deep Learning Model Inference Notebooks](https://pages.databricks.com/rs/094-YMS-629/images/Simple-Distributed-Inference.zip) and Tutorials.

Here are some additional deep learning tutorials and resources available from Databricks.

- [Deep Learning Documentation](https://docs.databricks.com/applications/machine-learning/train-model/deep-learning.html)
- [Deep Learning Fundamental Series](https://www.databricks.com/tensorflow/deep-learning)
- [Simple Steps to Distributed Deep Learning](https://www.databricks.com/blog/2019/03/11/simple-steps-to-distributed-deep-learning-on-demand-webinar-and-faq-now-available.html)

If you’d like free access [Databricks Unified Analytics Platform](https://www.databricks.com/product/data-lakehouse) and try our notebooks on it, you can access a [free trial here](https://www.databricks.com/try-databricks).
