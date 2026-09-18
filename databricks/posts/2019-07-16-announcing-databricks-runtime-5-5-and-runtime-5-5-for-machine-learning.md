# Announcing Databricks Runtime 5.5 and Runtime 5.5 for Machine Learning

- Source: https://www.databricks.com/blog/2019/07/16/announcing-databricks-runtime-5-5-and-runtime-5-5-for-machine-learning.html
- Published: 2019-07-16
- Authors: Yifan Cao
- Categories: announcements, company, data-science-machine-learning, open-source
- Images: 0 total, 0 extracted as architecture

Databricks is pleased to announce the release of Databricks Runtime 5.5.  This release includes Apache Spark 2.4.3 along with several important improvements and bug fixes as noted in the latest release notes [[Azure](https://docs.microsoft.com/en-us/azure/databricks/release-notes/runtime/5.5)|[AWS](https://docs.databricks.com/release-notes/runtime/5.5.html)].  We recommend all users upgrade to take advantage of this new runtime release.  This blog post gives a brief overview of some of the new high-value features that increase performance, compatibility, manageability and simplifying machine learning on Databricks.

- Faster Cluster Launches with Instance Pools - public preview
- Presto and Amazon Athena Compatibility with Delta Lake - public preview on AWS
- AWS Glue as the Databricks Metastore – generally available
- DBFS FUSE v2 - private preview
- Secrets API in R notebooks
- Plan to drop Python 2 support in Databricks Runtime 6.0
- Enhancements to Databricks Runtime for Machine Learning
  - Major package upgrades
  - Single-node operation for HorovodRunner
  - Faster model inference pipelines with improved binary file data source and scalar iterator Pandas UDF - public preview

 

## Faster Cluster Launches with Instance Pools - *public preview*

In Databricks Runtime 5.5 we are previewing a feature called Instance Pools, which significantly reduces the time it takes to launch a Databricks cluster. Today, launching a new cluster requires acquiring virtual machines from your cloud provider, which can take up to several minutes. With Instance Pools, you can hold back a set of virtual machines so they can be used to rapidly launch new clusters. You pay only cloud provider infrastructure costs while virtual machines are not being used in a Databricks cluster, and pools can scale down to zero instances, avoiding costs entirely when there are no workloads.

## Presto and Amazon Athena Compatibility with Delta Lake - *public preview on AWS*

As of Databricks Runtime 5.5, you can make Delta Lake tables available for querying from Presto and Amazon Athena. These tables can be queried just like tables with data stored in formats like Parquet. This feature is implemented using manifest files. When an external table is defined in the Hive metastore using manifest files, Presto and Amazon Athena use the list of files in the manifest rather than finding the files by directory listing.

## AWS Glue as the Databricks Metastore – *generally available*

We’ve partnered with Amazon Web Services to bring AWS Glue to Databricks. Databricks Runtime can now use AWS Glue as a drop-in replacement for the Hive metastore. For further information, see [Using AWS Glue Data Catalog as the Metastore for Databricks Runtime](https://docs.databricks.com/data/metastores/aws-glue-metastore.html#glue-metastore).

## DBFS FUSE v2 - *private preview*

The Databricks Filesystem (DBFS) is a layer on top of cloud storage that abstracts away peculiarities of underlying cloud storage providers. The existing DBFS FUSE client lets processes access DBFS using local filesystem APIs. However, it was designed mainly for convenience instead of performance. We introduced high-performance FUSE storage at location `file:/dbfs/ml` [for Azure in Databricks Runtime 5.3](https://docs.microsoft.com/en-us/azure/databricks/data/databricks-file-system#access-dbfs-using-high-performance-local-apis) and [for AWS in Databricks Runtime 5.4](https://docs.databricks.com/data/databricks-file-system.html#access-dbfs-using-high-performance-local-apis).  DBFS FUSE v2 expands the improved performance from `dbfs:/ml` to all DBFS locations including mounts. The feature is in private preview; to try it contact Databricks support.

## Secrets API in R notebooks

The Databricks Secrets API [[Azure](https://docs.microsoft.com/en-us/azure/databricks/dev-tools/api/latest/secrets)|[AWS](https://docs.databricks.com/dev-tools/api/latest/secrets.html)] lets you inject secrets into notebooks without hardcoding them. As of Databricks Runtime 5.5, this API is available in R notebooks in addition to existing support for Python and Scala notebooks. You can use the `dbutils.secrets.get` function to obtain secrets. Secrets are redacted before printing to a notebook cell.

## Plan to drop Python 2 support in Databricks Runtime 6.0

Python 2 is coming to the end of life in [2020](https://mail.python.org/pipermail/python-dev/2017-March/147655.html). Many popular projects have [announced](https://python3statement.org/) they will cease supporting Python 2 on or before 2020, including a recent [announcement](https://spark.apache.org/news/plan-for-dropping-python-2-support.html) for Spark 3.0. We have considered our customer base and plan to drop Python 2 support starting with Databricks Runtime 6.0, which is due to release later in 2019.

Databricks Runtime 6.0 and newer versions will support only Python 3. Databricks Runtime 4.x and 5.x will continue to support both Python 2 and 3. In addition, we plan to offer long-term support (LTS) for the last release of Databricks Runtime 5.x. You can continue to run Python 2 code in the LTS Databricks Runtime 5.x. We will soon announce which Databricks Runtime 5.x will be LTS.

## Enhancements to Databricks Runtime for Machine Learning

 

### Major package upgrades

With Databricks Runtime 5.5 for Machine Learning, we have made major package upgrades including:

- Added [MLflow 1.0](https://www.databricks.com/blog/2019/06/06/announcing-the-mlflow-1-0-release.html) Python package
- Tensorflow upgraded from 1.12.0 to 1.13.1
- PyTorch upgraded from 0.4.1 to 1.1.0
- scikit-learn upgraded from 0.19.1 to 0.20.3

### Single-node multi-GPU operation for HorovodRunner

We enabled HorovodRunner to utilize multi-GPU driver-only clusters. Previously, to use multiple GPUs, HorovodRunner users would have to spin up a driver and at least one worker. With this change, customers can now distribute training within a single node (i.e. a multi-GPU node) and thus use compute resources more efficiently. HorovodRunner is available only in Databricks Runtime for ML.

### Faster model inference pipelines with improved binary file data source and scalar iterator Pandas UDF - *public preview*

Machine learning tasks, especially in the image and video domain, often have to operate on a large number of files. In Databricks Runtime 5.4, we made available the binary file data source to help ETL arbitrary files such as images into Spark tables. In Databricks Runtime 5.5, we have added an option, `recursiveFileLookup`, to load files recursively from nested input directories. See binary file data source [[Azure](https://docs.microsoft.com/en-us/azure/databricks/data/data-sources/binary-file#binary-file)|[AWS](https://docs.databricks.com/data/data-sources/binary-file.html#binary-file)].

The binary file data source enable you to run model inference tasks in parallel from Spark tables using a scalar Pandas UDF. However, you might have to initialize the model for every record batch, which introduces overhead. In Databricks Runtime 5.5, we are backporting a new Pandas UDF type called “scalar iterator” from Apache Spark master. With it you can initialize the model only once and apply the model to many input batches, which can result in a 2-3x speedup for models like ResNet50. See Scalar Iterator UDFs [[Azure](https://docs.microsoft.com/en-us/azure/databricks/spark/latest/spark-sql/udf-python-pandas#scalar-iterator)|[AWS](https://docs.databricks.com/spark/latest/spark-sql/udf-python-pandas.html#scalar-iterator)].
