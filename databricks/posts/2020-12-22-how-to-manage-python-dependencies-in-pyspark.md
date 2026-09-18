# How to Manage Python Dependencies in PySpark

- Source: https://www.databricks.com/blog/2020/12/22/how-to-manage-python-dependencies-in-pyspark.html
- Published: 2020-12-22
- Authors: Hyukjin Kwon
- Categories: engineering, open-source
- Images: 0 total, 0 extracted as architecture

Controlling the environment of an application is often challenging in a distributed computing environment - it is difficult to ensure all nodes have the desired environment to execute, it may be tricky to know where the user’s code is actually running, and so on.

Apache Spark™ provides several standard ways to manage dependencies across the nodes in a cluster via script options such as `--jars`, `--packages`, and configurations such as `spark.jars.*` to make users seamlessly manage the dependencies in their clusters.

In contrast, PySpark users often ask how to do it with Python dependencies - there have been multiple issues filed such as [SPARK-13587](https://issues.apache.org/jira/browse/SPARK-13587), [SPARK-16367](https://issues.apache.org/jira/browse/SPARK-16367), [SPARK-20001](https://issues.apache.org/jira/browse/SPARK-20001) and [SPARK-25433](https://issues.apache.org/jira/browse/SPARK-25433). One simple example that illustrates the dependency management scenario is when users run pandas UDFs.

If they do not have required dependencies installed in all other nodes, it fails and complains that PyArrow and pandas have to be installed.

One straightforward method is to use script options such as `--py-files` or the `spark.submit.pyFiles`configuration, but this functionality cannot cover many cases, such as installing wheel files or when the Python libraries are dependent on C and C++ libraries such as pyarrow and NumPy.

This blog post introduces how to control Python dependencies in Apache Spark comprehensively. Most of the content will be also documented in the upcoming Apache Spark 3.1 as part of [Project Zen](https://issues.apache.org/jira/browse/SPARK-32082). Please refer to [An Update on Project Zen: Improving Apache Spark for Python Users](https://www.databricks.com/blog/2020/09/04/an-update-on-project-zen-improving-apache-spark-for-python-users.html) for more details.

## Using Conda

[Conda](https://docs.conda.io/en/latest/) is one of the most widely-used Python package management systems. PySpark users can directly use a Conda environment to ship their third-party Python packages by leveraging [conda-pack](https://conda.github.io/conda-pack/index.html) which is a command line tool creating relocatable Conda environments. It is supported in all types of clusters in the upcoming Apache Spark 3.1. In Apache Spark 3.0 or lower versions, it can be used only with YARN.

The example below creates a Conda environment to use on both the driver and executor and packs it into an archive file. This archive file captures the Conda environment for Python and stores both Python interpreter and all its relevant dependencies.

After that, you can ship it together with scripts or in the code by using the `--archives` option or `spark.archives` configuration (`spark.yarn.dist.archives` in YARN). It automatically unpacks the archive on executors.

In the case of a `spark-submit` script, you can use it as follows:

Note that `PYSPARK_DRIVER_PYTHON` above should not be set for cluster modes in YARN or Kubernetes.

For a `pyspark` shell:

If you’re on a regular Python shell or notebook, you can try it as shown below:

## Using Virtualenv

[Virtualenv](https://virtualenv.pypa.io/en/latest/) is a Python tool to create isolated Python environments. Since Python 3.3, a subset of its features has been integrated into Python as a standard library under the [venv](https://docs.python.org/3/library/venv.html) module. In the upcoming Apache Spark 3.1, PySpark users can use virtualenv to manage Python dependencies in their clusters by using [venv-pack](https://jcristharif.com/venv-pack/index.html) in a similar way as conda-pack. In the case of Apache Spark 3.0 and lower versions, it can be used only with YARN.

A virtual environment to use on both driver and executor can be created as demonstrated below. It packs the current virtual environment to an archive file, and it contains both Python interpreter and the dependencies. However, it requires all nodes in a cluster to have the same Python interpreter installed because venv-pack packs Python interpreter as a symbolic link.

You can directly pass/unpack the archive file and enable the environment on executors by leveraging the `--archives `option or `spark.archives` configuration (`spark.yarn.dist.archives` in YARN).

For `spark-submit`, you can use it by running the command as follows. Also, notice that `PYSPARK_DRIVER_PYTHON` has to be unset in Kubernetes or YARN cluster modes.

In the case of a `pyspark` shell:

For regular Python shells or notebooks:

## Using PEX

PySpark can also use [PEX](https://pex.readthedocs.io/en/latest/) to ship the Python packages together. PEX is a tool that creates a self-contained Python environment. This is similar to Conda or virtualenv, but a `.pex` file is executable by itself.

The following example creates a `.pex` file for the driver and executor to use. The file contains the Python dependencies specified with the `pex` command.

This file behaves similarly with a regular Python interpreter.

However, `.pex` file does not include a Python interpreter itself under the hood so all nodes in a cluster should have the same Python interpreter installed.

In order to transfer and use the `.pex` file in a cluster, you should ship it via the `spark.files` configuration (`spark.yarn.dist.files` in YARN) or `--files` option because they are regular files instead of directories or archive files.

For application submission, you run the commands as shown below. `PYSPARK_DRIVER_PYTHON` should not be set for cluster modes in YARN or Kubernetes.

For the interactive `pyspark` shell, the commands are almost the same:

For regular Python shells or notebooks:

## Conclusion

In Apache Spark, Conda, virtualenv and PEX can be leveraged to ship and manage Python dependencies.

- Conda: this is one of the most commonly used package management systems. In Apache Spark 3.0 and lower versions, Conda can be supported with YARN cluster only, and it works with all other cluster types in the upcoming Apache Spark 3.1.
- Virtualenv: users can do it without an extra installation because it is a built-in library in Python but it should have the same Python installed in all nodes whereas Conda does not require it. Virtualenv works only with YARN cluster in Apache Spark 3.0 and lower versions, and all other cluster types support it in the upcoming Apache Spark 3.1.
- PEX: it can be used with any type of cluster in any version of Apache Spark although it is arguably less widely used and requires to have the same Python installed in all nodes whereas Conda does not require it.

These package management systems can handle any Python packages that `--py-files` or `spark.submit.pyFiles` configuration cannot cover. Users can seamlessly ship not only pandas and PyArrow but also other dependencies to interact together when they work with PySpark.

In the case of Databricks notebooks, we not only provide an elegant mechanism by having a well-designed UI but also [allow users to directly use pip and Conda](https://www.databricks.com/blog/2020/06/17/simplify-python-environment-management-on-databricks-runtime-for-machine-learning-using-pip-and-conda.html) in order to address this Python dependency management. Try out these today for [free on Databricks](https://www.databricks.com/try-databricks).
