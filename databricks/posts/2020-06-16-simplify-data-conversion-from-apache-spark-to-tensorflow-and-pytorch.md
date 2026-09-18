# Simplify Data Conversion from Apache Spark to TensorFlow and PyTorch

- Source: https://www.databricks.com/blog/2020/06/16/simplify-data-conversion-from-apache-spark-to-tensorflow-and-pytorch.html
- Published: 2020-06-16
- Authors: Liang Zhang, Weichen Xu
- Categories: platform, engineering, open-source
- Images: 0 total, 0 extracted as architecture

Petastorm is a popular open-source library from Uber that enables single machine or distributed training and evaluation of deep learning models from datasets in Apache Parquet format. We are excited to announce that Petastorm 0.9.0 supports the easy conversion of data from Apache Spark DataFrame to TensorFlow Dataset and PyTorch DataLoader. The new Spark Dataset Converter API makes it easier to do distributed model training and inference on massive data, from multiple data sources. The Spark Dataset Converter API was contributed by Xiangrui Meng, Weichen Xu, and Liang Zhang (Databricks), in collaboration with Yevgeni Litvin and Travis Addair (Uber).

## Why is data conversion for Deep Learning hard?

A key step in any deep learning pipeline is converting data to the input format of the DL framework. Apache Spark is the most popular big data framework. The data conversion process from Apache Spark to deep learning frameworks can be tedious. For example, to convert an Apache Spark DataFrame with a feature column and a label column to a TensorFlow Dataset file format, users need to either save the Apache Spark DataFrame on a distributed filesystem in parquet format and load the converted data  with third-party tools such as Petastorm, or save it directly in TFRecord files with spark-tensorflow-connector and load it back using TFRecordDataset. Both approaches take more than 20 lines of code to manage the intermediate data files, rely on different parsing syntax, and require extra attention for handling columns in the Spark DataFrames. Those engineering frictions hinder the data scientists’ productivity.

## Solution at a glance

Databricks contributed a new [Spark Dataset Converter API](https://petastorm.readthedocs.io/en/latest/readme_include.html#spark-dataset-converter-api) to Petastorm to simplify these tedious data conversion process steps. With the new API, it takes a few lines of code to convert a Spark DataFrame to a [TensorFlow Dataset](https://www.tensorflow.org/datasets) or a [PyTorch DataLoader](https://pytorch.org/docs/stable/data.html) with default parameters.

## What does the Spark Dataset Converter do?

The Spark Dataset Converter API provides the following features:

- **Cache management.** The Converter caches the Spark DataFrame in a distributed filesystem and deletes the cached files when the interpreter exits with best effort. Explicit deletion API is also provided.
- **Rich parameters to customize the output dataset.** Users can customize and control the output dataset by setting batch_size, workers_count and prefetch to achieve the best I/O performance.
- **Transform function defined on [pandas dataframe](https://www.databricks.com/glossary/pandas-dataframe).** Many deep learning datasets include images, audio or video bytes, which can be loaded into Spark DataFrames as binary columns. These binary columns need decoding before feeding into deep learning models. The Converter exposes a hook for transform functions to specify the decoding logic. The transform function will take as input the pandas dataframe converted from the Spark DataFrame, and must return a pandas dataframe with the decoded data.

- **MLlib vector handling.** Besides primitive data types, the Converter supports Spark MLlib Vector types by automatically converting them to array columns before caching the Spark DataFrame. You can also reshape 1D arrays to multi-dimensional arrays in the transform function.
- **Remote data loading.** The Converter can be pickled to a Spark worker and used to create TensorFlow Dataset or PyTorch DataLoader on the worker. You can specify whether to read a specific shard or the whole dataset in the parameters.
- **Easy migration from single-node to distributed computing.** Migrating your single-node inference code to distributed inference requires no code change in data handling, it just works on Spark. For distributed training, you only need to add two parameters to the API that indicate shard index and total number of shards. In our end-to-end example notebooks, we illustrated how to migrate single-node code to distributed inference and distributed training with [Horovod](https://github.com/horovod/horovod).

Checkout the links in the Resources section for more details.

## Getting Started

Try out the end-to-end example notebooks linked below and in the Resources section on Databricks Runtime for Machine Learning 7.0 Beta with all the requirements installed.

**AWS Notebooks**

- [Simplify data conversion from Spark to TensorFlow](https://www.databricks.com/notebooks/simple-aws/petastorm-spark-converter-tensorflow.html)
- [Simplify data conversion from Spark to PyTorch](https://www.databricks.com/notebooks/simple-aws/petastorm-spark-converter-pytorch.html)

**Azure Notebooks**

- [Simplify data conversion from Spark to TensorFlow](https://www.databricks.com/notebooks/simple-azure/petastorm-spark-converter-tensorflow.html)
- [Simplify data conversion from Spark to PyTorch](https://www.databricks.com/notebooks/simple-azure/petastorm-spark-converter-pytorch.html)

## Acknowledgements

Thanks to Petastorm authors Yevgeni Litvin and Travis Addair from Uber for the detailed reviews and discussions to enable this feature!

## Resources

Databricks documentation with end-to-end examples ( [AWS](https://docs.databricks.com/applications/machine-learning/load-data/petastorm.html) | [Azure](https://docs.microsoft.com/en-us/azure/databricks/applications/machine-learning/load-data/petastorm) )
[Petastorm GitHub Homepage](https://github.com/uber/petastorm)
[Petastorm SparkDatasetConverter API documentation](https://petastorm.readthedocs.io/en/latest/api.html#module-petastorm.spark.spark_dataset_converter)
